"""Shared rate limiter instance for the application."""
from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_id(request: Request) -> str:
    """Key function: use authenticated user_id or fall back to client IP."""
    user = getattr(request.state, "current_user", None)
    if user is not None:
        return str(user.id)
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_id)
