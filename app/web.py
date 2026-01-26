"""Web routes for rendering templates."""
from __future__ import annotations

from flask import Blueprint, render_template

from app.services.data_service import data_service


web = Blueprint("web", __name__)


@web.route("/")
def dashboard():
    """Render main dashboard page."""
    try:
        kpis = data_service.get_kpis()
        return render_template("dashboard.html", kpis=kpis)
    except Exception as e:
        return render_template("error.html", error=str(e)), 500


@web.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}, 200
