import os

class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "nexus")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "nexus123")
    DB_NAME: str = os.getenv("DB_NAME", "nexus_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nexus-secret-key-2024-super-secure-do-not-share")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:5432/{self.DB_NAME}"

settings = Settings()
