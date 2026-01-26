"""Data schemas and structured outputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class KPIs:
    """Key performance indicators summary."""
    as_of_date: str
    total_customers: int
    churn_rate: float
    total_revenue: float
    churned_customers: int
    active_customers: int


@dataclass
class RFMChurnData:
    """RFM score aggregation with churn rate."""
    rfm_score: int
    count: int
    churn_rate: float


@dataclass
class RiskSegmentData:
    """Risk segment aggregation."""
    risk_segment: str
    count: int
    churn_rate: float
    monetary_sum: float


@dataclass
class TopRiskCustomer:
    """Top risk customer data."""
    customer_unique_id: str
    churn: int
    risk_segment: str
    recency_days: int
    frequency: int
    monetary: float
    avg_ticket: float
    R_score: int
    F_score: int
    M_score: int
    RFM_score: int


def features_to_kpis(features, as_of_date) -> KPIs:
    """Convert features DataFrame to KPIs dataclass."""
    return KPIs(
        as_of_date=as_of_date.strftime("%Y-%m-%d"),
        total_customers=len(features),
        churn_rate=float(features["churn"].mean() * 100),
        total_revenue=float(features["monetary"].sum()),
        churned_customers=int(features["churn"].sum()),
        active_customers=int((1 - features["churn"]).sum())
    )


def features_to_dict(kpis: KPIs) -> Dict[str, Any]:
    """Convert KPIs to dictionary for JSON serialization."""
    return {
        "as_of_date": kpis.as_of_date,
        "total_customers": kpis.total_customers,
        "churn_rate": round(kpis.churn_rate, 2),
        "total_revenue": round(kpis.total_revenue, 2),
        "churned_customers": kpis.churned_customers,
        "active_customers": kpis.active_customers
    }
