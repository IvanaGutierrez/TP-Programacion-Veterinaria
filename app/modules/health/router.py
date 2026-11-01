from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def health_live() -> dict[str, str]:
    """
    Comprobación de vida (Liveness probe).
    Indica que el proceso del servidor está vivo y respondiendo.
    No toca la base de datos bajo ninguna circunstancia.
    """
    return {"estado": "vivo"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def health_ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Comprobación de preparación (Readiness probe).
    Verifica que la conexión a la base de datos PostgreSQL esté operativa
    mediante la ejecución de 'SELECT 1'.
    Responde 503 Service Unavailable si la base de datos no contesta.
    """
    try:
        await session.execute(text("SELECT 1"))
        return {"estado": "base de datos conectada"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="base de datos no disponible",
        ) from exc
