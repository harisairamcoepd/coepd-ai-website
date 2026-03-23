"""Analytics helpers for API consumers."""

from .db import fetch_dashboard_stats, fetch_monthly_lead_growth


def get_analytics() -> dict:
    stats = fetch_dashboard_stats()
    monthly = fetch_monthly_lead_growth()
    return {
        "total_leads": stats["total_leads"],
        "today_leads": stats["today_leads"],
        "dates": monthly["dates"],
        "counts": monthly["counts"],
    }
