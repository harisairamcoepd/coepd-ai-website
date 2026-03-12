from chatbot.db import fetch_dashboard_stats, fetch_monthly_lead_growth


def build_analytics_response() -> dict:
    stats = fetch_dashboard_stats()
    monthly = fetch_monthly_lead_growth()

    dates = monthly.get("dates", [])
    counts = monthly.get("counts", [])

    if not isinstance(dates, list):
        dates = []
    if not isinstance(counts, list):
        counts = []

    if len(counts) != len(dates):
        counts = (counts + [0] * len(dates))[: len(dates)]

    return {
        "total_leads": int(stats.get("total_leads", 0) or 0),
        "today_leads": int(stats.get("today_leads", 0) or 0),
        "week_leads": int(stats.get("week_leads", 0) or 0),
        "month_leads": int(stats.get("month_leads", 0) or 0),
        "chatbot_leads": int(stats.get("chatbot_leads", 0) or 0),
        "website_leads": int(stats.get("website_leads", 0) or 0),
        "dates": dates,
        "counts": counts,
    }
