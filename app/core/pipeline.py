"""
Core pipeline functions for churn analysis.

Este módulo contém as funções puras (sem I/O) para processar dados de clientes
e realizar análise RFM (Recency, Frequency, Monetary) para predição de churn.

METODOLOGIA:
1. Limpeza de dados (remover nulos, duplicatas, valores inválidos)
2. Junção de datasets (orders + payments + customers)
3. Cálculo de features RFM por cliente
4. Classificação de churn (recency > threshold)
5. Pontuação RFM (quintis 1-5 para cada dimensão)
6. Segmentação de risco (8 níveis baseados em RFM)

All functions are pure: no I/O, no side effects, only DataFrame transformations.
"""
from __future__ import annotations

from typing import Tuple

import pandas as pd


def clean_orders(orders: pd.DataFrame, valid_status: set[str]) -> pd.DataFrame:
    """
    Clean orders dataset: remove nulls, duplicates, filter by status.
    
    Args:
        orders: Raw orders DataFrame
        valid_status: Set of valid order statuses (e.g., {"delivered"})
    
    Returns:
        Cleaned orders DataFrame
    """
    df = orders.dropna(subset=["order_id", "customer_id", "order_purchase_timestamp"])
    df = df.drop_duplicates(subset=["order_id"])
    df = df[df["order_status"].isin(valid_status)].copy()
    return df


def clean_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """
    Clean payments dataset: remove nulls, convert types, filter negatives.
    
    Args:
        payments: Raw payments DataFrame
    
    Returns:
        Cleaned payments DataFrame
    """
    df = payments.dropna(subset=["order_id", "payment_value"])
    df["payment_value"] = pd.to_numeric(df["payment_value"], errors="coerce")
    df = df.dropna(subset=["payment_value"])
    df = df[df["payment_value"] >= 0].copy()
    return df


def aggregate_payments_by_order(payments: pd.DataFrame) -> pd.DataFrame:
    """
    Sum payment values per order.
    
    Args:
        payments: Cleaned payments DataFrame
    
    Returns:
        DataFrame with order_id and total payment_value
    """
    return payments.groupby("order_id", as_index=False)["payment_value"].sum()


def join_datasets(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    payments_agg: pd.DataFrame
) -> pd.DataFrame:
    """
    Join orders with customer mapping and aggregated payments.
    
    Args:
        orders: Cleaned orders DataFrame
        customers: Customers DataFrame (customer_id, customer_unique_id)
        payments_agg: Aggregated payments by order
    
    Returns:
        Joined DataFrame with customer_unique_id and payment_value
    """
    cust_map = customers[["customer_id", "customer_unique_id"]].dropna()
    cust_map = cust_map.drop_duplicates(subset=["customer_id"])
    
    df = orders.merge(cust_map, on="customer_id", how="inner")
    df = df.merge(payments_agg, on="order_id", how="left")
    df["payment_value"] = df["payment_value"].fillna(0.0)
    
    return df


def compute_customer_features(
    orders: pd.DataFrame,
    as_of_date: pd.Timestamp
) -> pd.DataFrame:
    """
    Compute RFM features per customer.
    
    Args:
        orders: Joined orders DataFrame with customer_unique_id and payment_value
        as_of_date: Reference date for recency calculation
    
    Returns:
        DataFrame with customer features (frequency, monetary, recency, etc.)
    """
    g = orders.groupby("customer_unique_id", sort=False)
    
    features = pd.DataFrame({
        "customer_unique_id": g.size().index,
        "frequency": g.size().to_numpy(),
        "last_purchase": g["order_purchase_timestamp"].max().to_numpy(),
        "first_purchase": g["order_purchase_timestamp"].min().to_numpy(),
        "monetary": g["payment_value"].sum().to_numpy(),
    })
    
    features["last_purchase"] = pd.to_datetime(features["last_purchase"])
    features["first_purchase"] = pd.to_datetime(features["first_purchase"])
    
    features["recency_days"] = (as_of_date - features["last_purchase"]).dt.days.astype("int64")
    features["tenure_days"] = (as_of_date - features["first_purchase"]).dt.days.astype("int64")
    features["avg_ticket"] = features["monetary"] / features["frequency"]
    
    return features


def add_churn_label(features: pd.DataFrame, threshold_days: int) -> pd.DataFrame:
    """
    Add binary churn label based on recency threshold.
    
    Args:
        features: Customer features DataFrame
        threshold_days: Days threshold for churn (e.g., 270)
    
    Returns:
        Features DataFrame with churn column
    """
    df = features.copy()
    df["churn"] = (df["recency_days"] >= threshold_days).astype("int8")
    return df


def qcut_safe(s: pd.Series, q: int, labels: list) -> pd.Series:
    """
    Safely compute quantile bins using rank to handle duplicates.
    
    Args:
        s: Pandas Series to bin
        q: Number of quantiles
        labels: Labels for bins
    
    Returns:
        Binned Series
    """
    x = s.astype(float)
    r = x.rank(method="first")
    return pd.qcut(r, q=q, labels=labels)


def compute_rfm_scores(features: pd.DataFrame) -> pd.DataFrame:
    """
    Compute RFM scores (1-5) using quintiles.
    
    R: lower recency is better (5), higher is worse (1)
    F/M: higher is better (5)
    
    Args:
        features: Customer features DataFrame
    
    Returns:
        Features DataFrame with R_score, F_score, M_score, RFM_score, RFM_segment
    """
    df = features.copy()
    
    # R: lower recency = better (5)
    df["R_score"] = qcut_safe(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype("int8")
    # F/M: higher = better (5)
    df["F_score"] = qcut_safe(df["frequency"], q=5, labels=[1, 2, 3, 4, 5]).astype("int8")
    df["M_score"] = qcut_safe(df["monetary"], q=5, labels=[1, 2, 3, 4, 5]).astype("int8")
    
    # RFM Score: Média de R, F e M (resultado de 1.0 a 5.0, arredondado para 1 casa decimal)
    df["RFM_score"] = ((df["R_score"] + df["F_score"] + df["M_score"]) / 3.0).round(1)
    df["RFM_segment"] = (
        df["R_score"].astype(str) + "-"
        + df["F_score"].astype(str) + "-"
        + df["M_score"].astype(str)
    )
    
    return df


def compute_risk_segments(features: pd.DataFrame) -> pd.DataFrame:
    """
    Compute risk segments using business rules based on recency and value.
    
    Args:
        features: Customer features DataFrame with recency, frequency, monetary
    
    Returns:
        Features DataFrame with risk_segment column
    """
    df = features.copy()
    
    # Compute thresholds
    monetary_q80 = df["monetary"].quantile(0.80)
    frequency_q80 = df["frequency"].quantile(0.80)
    
    def risk_bucket(row) -> str:
        r = row["recency_days"]
        f = row["frequency"]
        m = row["monetary"]
        
        if r >= 450:
            return "Risco muito alto"
        if r >= 270:
            if (m >= monetary_q80) or (f >= frequency_q80):
                return "Churn (prioritário)"
            return "Churn"
        if r >= 180:
            if (m >= monetary_q80) or (f >= frequency_q80):
                return "Risco alto (prioritário)"
            return "Risco alto"
        if r >= 90:
            return "Risco médio"
        return "Risco baixo"
    
    df["risk_segment"] = df.apply(risk_bucket, axis=1)
    
    return df


def run_pipeline(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    payments: pd.DataFrame,
    churn_threshold_days: int,
    valid_status: set[str]
) -> Tuple[pd.DataFrame, pd.Timestamp]:
    """
    Execute the complete churn analysis pipeline.
    
    Args:
        customers: Raw customers DataFrame
        orders: Raw orders DataFrame
        payments: Raw payments DataFrame
        churn_threshold_days: Threshold for churn label
        valid_status: Valid order statuses to include
    
    Returns:
        Tuple of (features DataFrame, as_of_date)
    
    Raises:
        ValueError: If no valid data after filtering
    """
    # Clean
    orders_clean = clean_orders(orders, valid_status)
    payments_clean = clean_payments(payments)
    
    # Aggregate payments
    payments_agg = aggregate_payments_by_order(payments_clean)
    
    # Join datasets
    orders_joined = join_datasets(orders_clean, customers, payments_agg)
    
    # Compute as_of_date
    as_of_date = orders_joined["order_purchase_timestamp"].max()
    if pd.isna(as_of_date):
        raise ValueError("No valid order_purchase_timestamp after filtering")
    
    # Features
    features = compute_customer_features(orders_joined, as_of_date)
    features = add_churn_label(features, churn_threshold_days)
    features = compute_rfm_scores(features)
    features = compute_risk_segments(features)
    
    return features, as_of_date
