from collections.abc import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings


def get_engine(database_url: str | None = None, echo: bool | None = None) -> AsyncEngine:
    """Crea y devuelve un motor asincrónico de SQLAlchemy."""
    url = database_url or settings.DATABASE_URL
    echo_mode = echo if echo is not None else settings.ECHO_SQL
    return create_async_engine(
        url,
        echo=echo_mode,
        future=True,
    )


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Crea la fábrica de sesiones asincrónicas.
    expire_on_commit=False es fundamental en contextos asincrónicos para evitar
    excepciones MissingGreenlet al acceder a atributos de objetos tras un commit (sección 4.5).
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia FastAPI inyectada con Depends(get_session).
    Obtiene la fábrica de sesiones desde app.state (inicializada en el lifespan)
    y entrega una sesión por petición HTTP.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
