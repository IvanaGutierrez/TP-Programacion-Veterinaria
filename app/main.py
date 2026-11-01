from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import get_engine, get_session_factory
from app.modules.duenios.router import router as duenios_router
from app.modules.health.router import router as health_router
from app.modules.laboratorio.router import router as laboratorio_router
from app.modules.mascotas.router import router as mascotas_router
from app.modules.practicas.router import router as practicas_router
from app.modules.turnos.router import router as turnos_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Ciclo de vida de la aplicación FastAPI (sección 1.9).
    Inicializa el motor asincrónico y la fábrica de sesiones al arrancar el servidor
    y los almacena en app.state para inyección de dependencias.
    Al apagar la aplicación, se cierra y libera el motor limpiamente.
    """
    # 1. Startup: Creación de engine y sessionmaker con expire_on_commit=False
    engine = get_engine(settings.DATABASE_URL, echo=settings.ECHO_SQL)
    session_factory = get_session_factory(engine)

    app.state.engine = engine
    app.state.session_factory = session_factory

    yield

    # 2. Shutdown: Cierre del motor asincrónico y liberación de conexiones en el pool
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Asincrónica para Veterinaria con FastAPI, SQLModel y PostgreSQL (UTN Programación III)",
    version="1.0.0",
    lifespan=lifespan,
)

# Registro de routers modulares
app.include_router(health_router)
app.include_router(duenios_router)
app.include_router(mascotas_router)
app.include_router(practicas_router)
app.include_router(turnos_router)
app.include_router(laboratorio_router)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Endpoint raíz con bienvenida y enlace a la documentación interactiva."""
    return {
        "mensaje": "Bienvenido a la API de Veterinaria (UTN Programación III)",
        "docs": "/docs",
        "salud": "/health/live",
    }
