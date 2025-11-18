from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl, model_validator # model_validator era usato in una versione precedente, lo importo per coerenza se serve
from typing import List, Optional

class AuthSettings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    TENANT_ID: str
    REDIRECT_URI: HttpUrl # Pydantic validerà che sia un URL valido
    SCOPE: List[str] = Field(default_factory=list) # Default a lista vuota
 
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256" # Assicurati che JWT_ALGORITHM sia nel .env o usa questo default
    FRONTEND_URL: HttpUrl = Field(default="http://localhost:3000")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Sostituito JWT_EXPIRATION_HOURS e impostato un default in minuti
    ADMIN_EMAIL_DOMAIN: Optional[str] = None # Dominio email per gli amministratori

    # Credenziali per l'admin di default (per setup iniziale)
    DEFAULT_ADMIN_USERNAME: Optional[str] = None # Caricato da .env
    DEFAULT_ADMIN_PASSWORD: Optional[str] = None # Caricato da .env (password in chiaro)
    DEFAULT_ADMIN_EMAIL: Optional[str] = "admin@example.com" # Aggiunto/Decommentato per coerenza

    AUTHORITY: Optional[str] = None # Verrà costruito dinamicamente

    # Il validatore per AUTHORITY è stato spostato qui per coerenza con la definizione della classe
    # Se usi Pydantic v1, @validator("AUTHORITY", pre=True, always=True)
    # Se usi Pydantic v2, @model_validator(mode='before') o @root_validator(pre=True)
    # Per Pydantic v2 con model_validator(mode='before')
    # @model_validator(mode='before')
    # def assemble_authority_v2_before(cls, values):
    #     if values.get("AUTHORITY") is None and values.get("TENANT_ID"):
    #         values["AUTHORITY"] = f"https://login.microsoftonline.com/{values.get('TENANT_ID')}"
    #     elif values.get("AUTHORITY") is None and not values.get("TENANT_ID"):
    #         raise ValueError("TENANT_ID must be set to assemble AUTHORITY if AUTHORITY is not provided")
    #     return values

    # Per Pydantic v1 con @validator
    @model_validator(mode='after') # Per Pydantic v2, o @root_validator per v1
    def assemble_authority(self) -> 'AuthSettings':
        if self.AUTHORITY is None: # Se non è già stato impostato da .env
            if self.TENANT_ID:
                self.AUTHORITY = f"https://login.microsoftonline.com/{self.TENANT_ID}"
            else:
                # Questo non dovrebbe accadere se TENANT_ID è obbligatorio e non fornito,
                # Pydantic solleverebbe un errore prima. Ma è una doppia sicurezza.
                raise ValueError("TENANT_ID must be set to assemble AUTHORITY if AUTHORITY is not explicitly set.")
        return self

    class Config:
        env_file = ".env" # Cerca .env nella directory di lavoro corrente
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = AuthSettings()
