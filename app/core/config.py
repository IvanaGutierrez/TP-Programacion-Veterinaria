import os
from dotenv import load_dotenv

# Carga variables de entorno desde el archivo .env priorizando los valores del proyecto
load_dotenv(override=True)


class Settings:
    PROJECT_NAME: str = "Veterinaria API - UTN Programación III"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/veterinaria_db",
    )
    # Permite activar el logging de sentencias SQL en consola para auditar consultas N+1 (caso C-07)
    ECHO_SQL: bool = os.getenv("ECHO_SQL", "False").lower() in ("true", "1", "yes")


settings = Settings()
