"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path


# Base paths
BASE_DIR = Path(__file__).parent.parent  # ChurnLens/
DATA_DIR = BASE_DIR / "data"

# Data file paths
PATH_CUSTOMERS = str(DATA_DIR / "olist_customers_dataset.csv")
PATH_ORDERS = str(DATA_DIR / "olist_orders_dataset.csv")
PATH_PAYMENTS = str(DATA_DIR / "olist_order_payments_dataset.csv")

# Analysis parameters
CHURN_THRESHOLD_DAYS = int(os.getenv("CHURN_THRESHOLD_DAYS", "270"))
VALID_STATUS = {"delivered"}  # Can be expanded if needed

# Flask config
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", "5000"))

# Cache control
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "yes")
