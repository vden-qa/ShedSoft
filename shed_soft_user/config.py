import os

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Settings(BaseSettings):

    # Переменные из блока shed_soft_user (.env.example)
    BASE_URL_USER: str
    KEYCLOAK_BASE_URL_USER: str
    REALM_USER: str
    CLIENT_ID_USER: str
    CLIENT_SECRET_USER: str
    DB_HOST_USER: str
    DB_PORT_USER: int
    DB_NAME_USER: str
    DB_USER: str
    DB_PASS: str
    POOL_SIZE_USER: int
    MAX_OVERFLOW_USER: int
    ENVIRONMENT: str = "development"


    # Вычисляемые URL
    @property
    def token_url(self) -> str:
        return f"{self.KEYCLOAK_BASE_URL_USER}/realms/{self.REALM_USER}/protocol/openid-connect/token"

    @property
    def auth_url(self) -> str:
        return (
            f"{self.KEYCLOAK_BASE_URL_USER}/realms/{self.REALM_USER}/protocol/openid-connect/auth"
        )

    @property
    def logout_url(self) -> str:
        return f"{self.KEYCLOAK_BASE_URL_USER}/realms/{self.REALM_USER}/protocol/openid-connect/logout"

    @property
    def userinfo_url(self) -> str:
        return f"{self.KEYCLOAK_BASE_URL_USER}/realms/{self.REALM_USER}/protocol/openid-connect/userinfo"

    @property
    def redirect_uri(self) -> str:
        return f"{self.BASE_URL_USER}/api/login/callback"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    model_config = SettingsConfigDict(
        env_file=f"{BASE_DIR}/.env",
        extra="ignore"
    )


settings = Settings()  # type: ignore