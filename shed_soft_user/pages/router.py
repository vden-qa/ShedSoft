from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shed_soft_user.config import settings
from shed_soft_user.services.auth_dep import get_current_user, get_keycloak_client

router = APIRouter()

templates = Jinja2Templates(directory="shed_soft_user/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница с редиректом на защищенную или логин."""
    try:
        keycloak = await get_keycloak_client(request)
        token = request.cookies.get("access_token")
        user = await get_current_user(token=token, keycloak=keycloak)
        return RedirectResponse(url="/protected")
    except HTTPException:
        # Редирект на Keycloak для авторизации
        params = {
            "client_id": settings.CLIENT_ID_USER,
            "redirect_uri": settings.redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
        }
        login_url = f"{settings.auth_url}?{urlencode(params)}"
        return RedirectResponse(url=login_url)


@router.get("/protected", response_class=HTMLResponse)
async def protected_page(request: Request):
    """Защищенная страница, требующая авторизации."""
    try:
        keycloak = await get_keycloak_client(request)
        token = request.cookies.get("access_token")
        user = await get_current_user(token=token, keycloak=keycloak)
        return templates.TemplateResponse("index.html", {"request": request, "user": user})
    except HTTPException:
        # Редирект на главную, которая перенаправит на логин
        return RedirectResponse(url="/")
