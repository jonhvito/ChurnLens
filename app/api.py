"""API routes for JSON data."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, make_response
import io

from app.services.data_service import data_service


api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/summary")
def summary():
    """Get KPIs summary."""
    try:
        kpis = data_service.get_kpis()
        return jsonify(kpis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/churn_by_rfm")
def churn_by_rfm():
    """Get churn rate by RFM score."""
    try:
        data = data_service.get_churn_by_rfm()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/recency_hist")
def recency_hist():
    """Get recency histogram data."""
    try:
        data = data_service.get_recency_histogram(bins=20)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/risk_summary")
def risk_summary():
    """Get risk segment summary."""
    try:
        data = data_service.get_risk_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/top_risk")
def top_risk():
    """Get top 50 risk customers."""
    try:
        data = data_service.get_top_risk(n=50)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Export endpoints
export = Blueprint("export", __name__, url_prefix="/export")


@export.route("/customers.csv")
def export_customers():
    """Export all customer features as CSV."""
    try:
        features = data_service.get_all_features()
        
        # Convert to CSV
        output = io.StringIO()
        features.to_csv(output, index=False)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=customers_features.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@export.route("/top_risk.csv")
def export_top_risk():
    """Export top 50 risk customers as CSV."""
    try:
        import pandas as pd
        
        top_risk_data = data_service.get_top_risk(n=50)
        df = pd.DataFrame(top_risk_data)
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=top_risk.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
