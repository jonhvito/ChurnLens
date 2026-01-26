"""Data service for loading and caching pipeline results."""
from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd

from app import config
from app.core import pipeline, validation


class DataService:
    """Service to load data and run pipeline with simple caching."""
    
    def __init__(self):
        self._features: Optional[pd.DataFrame] = None
        self._as_of_date: Optional[pd.Timestamp] = None
    
    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load raw CSV datasets.
        
        Returns:
            Tuple of (customers, orders, payments) DataFrames
        
        Raises:
            FileNotFoundError: If CSV files don't exist
            ValueError: If validation fails
        """
        try:
            customers = pd.read_csv(
                config.PATH_CUSTOMERS,
                dtype={"customer_id": "string", "customer_unique_id": "string"}
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Customers file not found: {config.PATH_CUSTOMERS}")
        
        try:
            orders = pd.read_csv(
                config.PATH_ORDERS,
                dtype={"order_id": "string", "customer_id": "string", "order_status": "string"},
                parse_dates=["order_purchase_timestamp"]
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Orders file not found: {config.PATH_ORDERS}")
        
        try:
            payments = pd.read_csv(
                config.PATH_PAYMENTS,
                dtype={"order_id": "string", "payment_type": "string"}
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Payments file not found: {config.PATH_PAYMENTS}")
        
        # Validate schemas
        validation.validate_datasets(customers, orders, payments)
        
        return customers, orders, payments
    
    def get_features(self, force_refresh: bool = False) -> Tuple[pd.DataFrame, pd.Timestamp]:
        """
        Get customer features, running pipeline if needed.
        
        Args:
            force_refresh: If True, ignore cache and recompute
        
        Returns:
            Tuple of (features DataFrame, as_of_date)
        """
        if config.CACHE_ENABLED and not force_refresh and self._features is not None:
            return self._features, self._as_of_date
        
        # Load and process
        customers, orders, payments = self.load_raw_data()
        
        features, as_of_date = pipeline.run_pipeline(
            customers=customers,
            orders=orders,
            payments=payments,
            churn_threshold_days=config.CHURN_THRESHOLD_DAYS,
            valid_status=config.VALID_STATUS
        )
        
        # Cache
        if config.CACHE_ENABLED:
            self._features = features
            self._as_of_date = as_of_date
        
        return features, as_of_date
    
    def get_kpis(self) -> dict:
        """Get summary KPIs."""
        from app.core.schemas import features_to_kpis, features_to_dict
        
        features, as_of_date = self.get_features()
        kpis = features_to_kpis(features, as_of_date)
        return features_to_dict(kpis)
    
    def get_churn_by_rfm(self) -> list[dict]:
        """Get churn rate aggregated by RFM score."""
        features, _ = self.get_features()
        
        rfm_churn = (
            features.groupby("RFM_score", as_index=False)
            .agg(count=("customer_unique_id", "size"), churn_rate=("churn", "mean"))
        )
        rfm_churn["churn_rate"] = (rfm_churn["churn_rate"] * 100).round(2)
        
        return rfm_churn.to_dict(orient="records")
    
    def get_recency_histogram(self, bins: int = 20) -> dict:
        """
        Get recency distribution as histogram.
        
        Args:
            bins: Number of bins for histogram
        
        Returns:
            Dict with bin_edges and counts
        """
        features, _ = self.get_features()
        
        counts, bin_edges = pd.cut(
            features["recency_days"],
            bins=bins,
            retbins=True,
            duplicates="drop"
        )
        
        hist_data = counts.value_counts().sort_index()
        
        return {
            "bins": [f"{int(interval.left)}-{int(interval.right)}" for interval in hist_data.index],
            "counts": hist_data.values.tolist()
        }
    
    def get_risk_summary(self) -> list[dict]:
        """Get aggregation by risk segment."""
        features, _ = self.get_features()
        
        risk_summary = (
            features.groupby("risk_segment", as_index=False)
            .agg(
                count=("customer_unique_id", "size"),
                churn_rate=("churn", "mean"),
                monetary_sum=("monetary", "sum")
            )
        )
        risk_summary["churn_rate"] = (risk_summary["churn_rate"] * 100).round(2)
        risk_summary["monetary_sum"] = risk_summary["monetary_sum"].round(2)
        
        return risk_summary.to_dict(orient="records")
    
    def get_top_risk(self, n: int = 50) -> list[dict]:
        """
        Get top N customers by risk.
        
        Args:
            n: Number of customers to return
        
        Returns:
            List of customer dicts
        """
        features, _ = self.get_features()
        
        top_risk = (
            features.sort_values(["churn", "recency_days", "monetary"], ascending=[False, False, False])
            .head(n)
            [[
                "customer_unique_id", "churn", "risk_segment", "recency_days",
                "frequency", "monetary", "avg_ticket", "R_score", "F_score",
                "M_score", "RFM_score"
            ]]
        )
        
        return top_risk.to_dict(orient="records")
    
    def get_all_features(self) -> pd.DataFrame:
        """Get all customer features (for export)."""
        features, _ = self.get_features()
        return features


# Global service instance
data_service = DataService()
