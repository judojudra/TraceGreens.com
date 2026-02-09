"""Simple cookie-based admin authentication."""

from fastapi import Cookie, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings

COOKIE_NAME = "tg_admin"
COOKIE_VALUE = "authenticated"


def require_admin(tg_admin: str = Cookie(None)):
    """Dependency that checks for admin cookie. Redirects to login if missing."""
    if tg_admin != COOKIE_VALUE:
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})


def verify_password(password: str) -> bool:
    return password == settings.ADMIN_PASSWORD


def set_admin_cookie(response: RedirectResponse) -> RedirectResponse:
    response.set_cookie(COOKIE_NAME, COOKIE_VALUE, httponly=True, max_age=86400 * 7)
    return response


def clear_admin_cookie(response: RedirectResponse) -> RedirectResponse:
    response.delete_cookie(COOKIE_NAME)
    return response
