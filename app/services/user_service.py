from chatbot.db import (
    create_user,
    delete_user,
    fetch_user_by_id,
    list_users,
    set_user_active,
    update_user_role,
)


def list_all_users() -> list[dict]:
    return list_users()


def create_staff_user(name: str, email: str, role: str) -> int:
    return create_user(name=name, email=email, role=role)


def change_user_role(user_id: int, role: str) -> bool:
    return update_user_role(user_id=user_id, role=role)


def set_user_status(user_id: int, is_active: bool) -> bool:
    return set_user_active(user_id=user_id, is_active=is_active)


def get_user(user_id: int) -> dict | None:
    return fetch_user_by_id(user_id)


def remove_user(user_id: int) -> bool:
    return delete_user(user_id)
