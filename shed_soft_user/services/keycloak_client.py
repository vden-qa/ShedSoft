import httpx
from fastapi import HTTPException

from shed_soft_user.config import settings


class KeycloakClient:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._own_client = client is None
        self.client = client or httpx.AsyncClient()

    async def close(self):
        """Закрыть HTTP-клиент, если он был создан внутри класса"""
        if self._own_client and self.client:
            await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get_tokens(self, code: str) -> dict:
        """Обмен authorization code на токены"""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "client_id": settings.CLIENT_ID_USER,
            "client_secret": settings.CLIENT_SECRET_USER,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = await self.client.post(
                settings.token_url, data=data, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Token request failed: {e.response.text}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON response from Keycloak: {str(e)}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Token exchange failed: {str(e)}"
            )

    async def get_user_info(self, token: str) -> dict:
        """Получить информацию о пользователе по access_token"""
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await self.client.get(settings.userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Invalid access token: {e.response.text}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON response from Keycloak: {str(e)}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Keycloak request error: {str(e)}"
            )
