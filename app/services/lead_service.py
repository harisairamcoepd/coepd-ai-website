from chatbot.db import delete_lead, fetch_dashboard_leads, fetch_leads, save_lead, update_lead_status


def create_lead(payload: dict) -> int:
    return save_lead(payload)


def list_leads(
    date_prefix: str | None = None,
    source: str | None = None,
    search: str | None = None,
    interested_domain: str | None = None,
) -> list[dict]:
    return fetch_leads(date_prefix=date_prefix, source=source, search=search, interested_domain=interested_domain)


def remove_lead(lead_id: int) -> bool:
    return delete_lead(lead_id)


def set_lead_status(lead_id: int, working_status: str) -> bool:
    return update_lead_status(lead_id=lead_id, working_status=working_status)


def list_dashboard_leads() -> list[dict]:
    payload = fetch_dashboard_leads(page=1, page_size=100, search=None)
    return payload.get("items", [])


def list_dashboard_leads_paginated(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> dict:
    return fetch_dashboard_leads(page=page, page_size=page_size, search=search)
