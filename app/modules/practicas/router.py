from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.practicas.schemas import PracticaCreate, PracticaRead
from app.modules.practicas.service import crear_practica, listar_practicas

router = APIRouter(prefix="/practicas", tags=["Prácticas"])


@router.post("/", response_model=PracticaRead, status_code=status.HTTP_201_CREATED)
async def post_practica(
    data: PracticaCreate,
    session: AsyncSession = Depends(get_session),
) -> PracticaRead:
    """Crea una nueva práctica en el catálogo. Responde 409 si el nombre ya existe."""
    practica = await crear_practica(session, data)
    return PracticaRead.model_validate(practica)


@router.get("/", response_model=list[PracticaRead], status_code=status.HTTP_200_OK)
async def get_practicas(
    session: AsyncSession = Depends(get_session),
) -> list[PracticaRead]:
    """Retorna el catálogo completo de prácticas médicas."""
    practicas = await listar_practicas(session)
    return [PracticaRead.model_validate(p) for p in practicas]
