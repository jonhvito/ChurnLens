from __future__ import annotations

import numpy as np
import pandas as pd

# ====== CONFIG ======
PATH_CUSTOMERS = "./data/olist_customers_dataset.csv"
PATH_ORDERS    = "./data/olist_orders_dataset.csv"
PATH_PAYMENTS  = "./data/olist_order_payments_dataset.csv"

CHURN_THRESHOLD_DAYS = 270
VALID_STATUS = {"delivered"}  # ajuste se quiser incluir outros

# ====== LOAD ======
customers = pd.read_csv(PATH_CUSTOMERS, dtype={"customer_id": "string", "customer_unique_id": "string"})
orders = pd.read_csv(
    PATH_ORDERS,
    dtype={"order_id": "string", "customer_id": "string", "order_status": "string"},
    parse_dates=["order_purchase_timestamp"],
)
payments = pd.read_csv(
    PATH_PAYMENTS,
    dtype={"order_id": "string", "payment_type": "string"},
)

# ====== CLEAN ======
orders = orders.dropna(subset=["order_id", "customer_id", "order_purchase_timestamp"])
orders = orders.drop_duplicates(subset=["order_id"])
orders = orders[orders["order_status"].isin(VALID_STATUS)].copy()

payments = payments.dropna(subset=["order_id", "payment_value"])
payments["payment_value"] = pd.to_numeric(payments["payment_value"], errors="coerce")
payments = payments.dropna(subset=["payment_value"])
payments = payments[payments["payment_value"] >= 0].copy()

pay_per_order = payments.groupby("order_id", as_index=False)["payment_value"].sum()

cust_map = customers[["customer_id", "customer_unique_id"]].dropna().drop_duplicates(subset=["customer_id"])
orders = orders.merge(cust_map, on="customer_id", how="inner")
orders = orders.merge(pay_per_order, on="order_id", how="left")
orders["payment_value"] = orders["payment_value"].fillna(0.0)

# ====== as_of_date ======
as_of_date = orders["order_purchase_timestamp"].max()
if pd.isna(as_of_date):
    raise ValueError("Sem order_purchase_timestamp válido após filtros.")

# ====== FEATURES POR CLIENTE ======
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

# ====== CHURN LABEL ======
features["churn"] = (features["recency_days"] >= CHURN_THRESHOLD_DAYS).astype("int8")

# ====== RFM SCORE (quintis) ======
def _qcut_safe(s: pd.Series, q: int, labels):
    # qcut pode falhar com muitos valores repetidos; usa rank para destravar.
    x = s.astype(float)
    r = x.rank(method="first")
    return pd.qcut(r, q=q, labels=labels)

# R: menor recency = melhor (5); maior recency = pior (1)
features["R_score"] = _qcut_safe(features["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype("int8")
# F/M: maior = melhor (5)
features["F_score"] = _qcut_safe(features["frequency"], q=5, labels=[1, 2, 3, 4, 5]).astype("int8")
features["M_score"] = _qcut_safe(features["monetary"], q=5, labels=[1, 2, 3, 4, 5]).astype("int8")

features["RFM_score"] = (features["R_score"] + features["F_score"] + features["M_score"]).astype("int16")
features["RFM_segment"] = (
    features["R_score"].astype(str) + "-"
    + features["F_score"].astype(str) + "-"
    + features["M_score"].astype(str)
)

# ====== SEGMENTAÇÃO DE RISCO (regras simples) ======
def _risk_bucket(row) -> str:
    # alta inatividade domina; depois usa valor/frequência para prioridade
    r = row["recency_days"]
    f = row["frequency"]
    m = row["monetary"]

    if r >= 450:
        return "Risco muito alto"
    if r >= 270:
        # churn por regra; prioriza quem tem valor/frequência maiores
        if (m >= row["monetary_q80"]) or (f >= row["frequency_q80"]):
            return "Churn (prioritário)"
        return "Churn"
    if r >= 180:
        if (m >= row["monetary_q80"]) or (f >= row["frequency_q80"]):
            return "Risco alto (prioritário)"
        return "Risco alto"
    if r >= 90:
        return "Risco médio"
    return "Risco baixo"

features["monetary_q80"] = features["monetary"].quantile(0.80)
features["frequency_q80"] = features["frequency"].quantile(0.80)
features["risk_segment"] = features.apply(_risk_bucket, axis=1)
features = features.drop(columns=["monetary_q80", "frequency_q80"])

# ====== SUMÁRIOS ÚTEIS ======
churn_rate = float(features["churn"].mean() * 100)

rfm_churn = (
    features.groupby("RFM_score", as_index=False)
    .agg(n=("customer_unique_id", "size"), churn_rate=("churn", "mean"))
)
rfm_churn["churn_rate"] = (rfm_churn["churn_rate"] * 100).round(2)

risk_summary = (
    features.groupby("risk_segment", as_index=False)
    .agg(n=("customer_unique_id", "size"),
         churn_rate=("churn", "mean"),
         monetary_sum=("monetary", "sum"))
)
risk_summary["churn_rate"] = (risk_summary["churn_rate"] * 100).round(2)
risk_summary["monetary_sum"] = risk_summary["monetary_sum"].round(2)

top_risk = (
    features.sort_values(["churn", "recency_days", "monetary"], ascending=[False, False, False])
    .head(50)
    [["customer_unique_id", "churn", "risk_segment", "recency_days", "frequency", "monetary", "avg_ticket", "R_score", "F_score", "M_score", "RFM_score"]]
)

print(f"as_of_date: {as_of_date.date()}")
print(f"clientes: {len(features)}")
print(f"churn_rate(%): {churn_rate:.2f}")

print("\n== Resumo por risk_segment ==")
print(risk_summary.sort_values(["churn_rate", "n"], ascending=[False, False]).to_string(index=False))

print("\n== Resumo por RFM_score (top 15 por churn_rate, com suporte) ==")
print(rfm_churn.sort_values(["churn_rate", "n"], ascending=[False, False]).head(15).to_string(index=False))

print("\n== Top 10 clientes (risco) ==")
print(top_risk.head(10).to_string(index=False))

#Como apresentar corretamente

#No texto/UI:

#Churn → variável alvo (definição)

#Risk segment → regra de priorização após churn

#Exemplo de explicação curta:

#“Os segmentos de risco são regras operacionais baseadas em recency e valor, não clusters aprendidos. Por isso, churn_rate alto nos segmentos ‘Churn’ é esperado.”