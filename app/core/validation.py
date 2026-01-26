"""Validation utilities for data integrity checks."""
from __future__ import annotations

import pandas as pd


def validate_customers_schema(df: pd.DataFrame) -> None:
    """
    Validate customers DataFrame has required columns.
    
    Args:
        df: Customers DataFrame
    
    Raises:
        ValueError: If required columns are missing
    """
    required = {"customer_id", "customer_unique_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in customers: {missing}")


def validate_orders_schema(df: pd.DataFrame) -> None:
    """
    Validate orders DataFrame has required columns.
    
    Args:
        df: Orders DataFrame
    
    Raises:
        ValueError: If required columns are missing
    """
    required = {"order_id", "customer_id", "order_status", "order_purchase_timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in orders: {missing}")


def validate_payments_schema(df: pd.DataFrame) -> None:
    """
    Validate payments DataFrame has required columns.
    
    Args:
        df: Payments DataFrame
    
    Raises:
        ValueError: If required columns are missing
    """
    required = {"order_id", "payment_value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in payments: {missing}")


def validate_datasets(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    payments: pd.DataFrame
) -> None:
    """
    Validate all datasets have required schemas and are not empty.
    
    Args:
        customers: Customers DataFrame
        orders: Orders DataFrame
        payments: Payments DataFrame
    
    Raises:
        ValueError: If validation fails
    """
    if customers.empty:
        raise ValueError("Customers dataset is empty")
    if orders.empty:
        raise ValueError("Orders dataset is empty")
    if payments.empty:
        raise ValueError("Payments dataset is empty")
    
    validate_customers_schema(customers)
    validate_orders_schema(orders)
    validate_payments_schema(payments)
