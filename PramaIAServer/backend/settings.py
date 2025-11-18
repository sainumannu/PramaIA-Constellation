# In un file settings.py
from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    TENANT_ID: str
    REDIRECT_URI: str
    SCOPE: list[str] = []
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    FRONTEND_URL: str = "http://localhost:3000"
    AUTHORITY: str | None = None # Può essere costruito dinamicamente

    # Per costruire AUTHORITY dinamicamente
    # from pydantic import model_validator
    # @model_validator(mode='after')
    # def assemble_authority(self) -> 'AuthSettings':
    #     if self.TENANT_ID:
    #         self.AUTHORITY = f"https://login.microsoftonline.com/{self.TENANT_ID}"
    #     return self

    class Config:
        env_file = ".env" # O specifica il percorso del tuo file .env
        env_file_encoding = 'utf-8'

settings = AuthSettings()

# Poi in auth_router.py:
# from .settings import settings
# CLIENT_ID = settings.CLIENT_ID
# ...e così via
