from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    ADMIN_ROLES: str = "supervisor,admin"
    ADMIN: str
    ADMIN_PASSWORD: str
    SECRET_KEY: str
    TELEGRAM_TOKEN : str



    class Config:
        env_file = ".env"

settings = Settings()
