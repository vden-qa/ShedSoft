import jwt
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from shed_soft_user.services.keycloak_client import KeycloakClient


class UserInfo(BaseModel):
    """Модель информации о пользователе из Keycloak"""
    sub: str  # User ID
    email: str | None = None
    preferred_username: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email_verified: bool | None = None
    realm_name: str | None = None


# ✅ Получаем KeycloakClient из app.state
async def get_keycloak_client(request: Request) -> KeycloakClient:
    return request.app.state.keycloak_client


# ✅ Получаем токен из cookie (None, если нет)
async def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("access_token")


# ✅ Получаем пользователя по токену (возвращаем dict для совместимости)
async def get_current_user(
    token: str = Depends(get_token_from_cookie),
    keycloak: KeycloakClient = Depends(get_keycloak_client),
) -> dict:
    if not token:
        # Возвращаем стандартную ошибку — редиректим позже в роутере
        raise HTTPException(status_code=401, detail="Unauthorized: No access token")

    try:
        # Декодируем токен без проверки подписи для извлечения realm_name
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        
        # Извлекаем realm name из iss: "http://localhost:8080/realms/my-realm"
        issuer = decoded_token.get("iss", "")
        realm_name = issuer.split("/realms/")[-1] if "/realms/" in issuer else ""
        
        user_info = await keycloak.get_user_info(token)
        
        # Проверяем наличие обязательного поля sub (user_id)
        if not user_info.get("sub"):
            raise HTTPException(
                status_code=401,
                detail="Invalid user info: missing 'sub' field"
            )
        
        # Добавляем realm_name в user_info
        user_info["realm_name"] = realm_name
        
        # Возвращаем dict напрямую для совместимости с существующим кодом
        return user_info
    except HTTPException:
        # Пробрасываем HTTPException как есть, сохраняя оригинальный статус-код
        raise
    except Exception as e:
        # Обрабатываем неожиданные ошибки (сетевые, парсинг и т.д.)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user info: {type(e).__name__}"
        ) from e
