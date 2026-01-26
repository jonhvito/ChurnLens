"""Tests for core pipeline functions."""
from __future__ import annotations

import pandas as pd
import pytest

from app.core import pipeline


def test_churn_label_threshold():
    """Test that churn label is correctly applied based on threshold."""
    # Create sample data
    features = pd.DataFrame({
        "customer_unique_id": ["c1", "c2", "c3", "c4"],
        "recency_days": [100, 269, 270, 500],
        "frequency": [1, 2, 3, 4],
        "monetary": [100.0, 200.0, 300.0, 400.0]
    })
    
    # Apply churn label with threshold of 270
    result = pipeline.add_churn_label(features, threshold_days=270)
    
    # Assertions
    assert result.loc[0, "churn"] == 0  # 100 < 270
    assert result.loc[1, "churn"] == 0  # 269 < 270
    assert result.loc[2, "churn"] == 1  # 270 >= 270
    assert result.loc[3, "churn"] == 1  # 500 >= 270


def test_rfm_score_range():
    """Test that RFM scores are in valid range 1-5."""
    # Create sample data with varied values
    features = pd.DataFrame({
        "customer_unique_id": [f"c{i}" for i in range(100)],
        "recency_days": list(range(1, 101)),
        "frequency": list(range(1, 101)),
        "monetary": [float(i * 10) for i in range(1, 101)]
    })
    
    # Compute RFM scores
    result = pipeline.compute_rfm_scores(features)
    
    # Check ranges
    assert result["R_score"].min() >= 1
    assert result["R_score"].max() <= 5
    assert result["F_score"].min() >= 1
    assert result["F_score"].max() <= 5
    assert result["M_score"].min() >= 1
    assert result["M_score"].max() <= 5
    
    # RFM_score should be sum of R, F, M (range 3-15)
    assert result["RFM_score"].min() >= 3
    assert result["RFM_score"].max() <= 15


def test_no_negative_monetary():
    """Test that cleaned payments don't contain negative values."""
    # Create sample data with negative value
    payments = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4"],
        "payment_value": [100.0, -50.0, 200.0, 0.0]
    })
    
    # Clean payments
    result = pipeline.clean_payments(payments)
    
    # Should only have positive and zero values
    assert len(result) == 3  # Negative value removed
    assert (result["payment_value"] >= 0).all()


def test_clean_orders_removes_invalid():
    """Test that order cleaning removes invalid rows."""
    # Create sample data with null and duplicate
    orders = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o2", "o4"],
        "customer_id": ["c1", "c2", None, "c2", "c4"],
        "order_status": ["delivered", "delivered", "delivered", "delivered", "canceled"],
        "order_purchase_timestamp": pd.to_datetime(["2018-01-01", "2018-01-02", "2018-01-03", "2018-01-02", "2018-01-04"])
    })
    
    # Clean with valid_status={"delivered"}
    result = pipeline.clean_orders(orders, valid_status={"delivered"})
    
    # Should remove: null customer_id, duplicate order_id, non-delivered status
    assert len(result) == 2  # Only o1 and o2 (first occurrence)
    assert result["order_status"].isin({"delivered"}).all()
    assert result["customer_id"].notna().all()


def test_aggregate_payments_sums_correctly():
    """Test that payment aggregation sums values per order."""
    payments = pd.DataFrame({
        "order_id": ["o1", "o1", "o2", "o3"],
        "payment_value": [50.0, 50.0, 100.0, 200.0]
    })
    
    result = pipeline.aggregate_payments_by_order(payments)
    
    assert len(result) == 3
    assert result[result["order_id"] == "o1"]["payment_value"].iloc[0] == 100.0
    assert result[result["order_id"] == "o2"]["payment_value"].iloc[0] == 100.0
    assert result[result["order_id"] == "o3"]["payment_value"].iloc[0] == 200.0


def test_qcut_safe_handles_duplicates():
    """Test that qcut_safe handles series with many duplicates."""
    # Series with many duplicate values
    s = pd.Series([1, 1, 1, 1, 2, 2, 2, 3, 3, 4])
    
    # Should not raise error
    result = pipeline.qcut_safe(s, q=3, labels=[1, 2, 3])
    
    assert len(result) == len(s)
    assert result.isin([1, 2, 3]).all()
