from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.mascotas.schemas import (
    MascotaConDuenioRead,
    MascotaCreate,
    MascotaRead,
    MascotasPaginadas,
)
from app.modules.mascotas.service import (
    crear_mascota,
    listar_mascotas,
    obtener_mascota_por_id,
)

router = APIRouter(prefix="/mascotas", tags=["Mascotas"])


@router.post("/", response_model=MascotaRead, status_code=status.HTTP_201_CREATED)
async def post_mascota(
    data: MascotaCreate,
    session: AsyncSession = Depends(get_session),
) -> MascotaRead:
    """Registra una nueva mascota vinculada a un dueño existente. Si el dueño no existe, responde 409."""
    mascota = await crear_mascota(session, data)
    return MascotaRead.model_validate(mascota)


@router.get("/", response_model=MascotasPaginadas, status_code=status.HTTP_200_OK)
async def get_mascotas(
    page: int = Query(1, ge=1, description="Número de página (>= 1)"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página (entre 1 y 100)"),
    session: AsyncSession = Depends(get_session),
) -> MascotasPaginadas:
    """
    Retorna el listado paginado de mascotas con envoltorio { items, total, page, size, pages }.
    Si page > pages, responde HTTP 422.
    """
    resultado = await listar_mascotas(session, page=page, size=size)
    return MascotasPaginadas(
        items=[MascotaConDuenioRead.model_validate(m) for m in resultado["items"]],
        total=resultado["total"],
        page=resultado["page"],
        size=resultado["size"],
        pages=resultado["pages"],
    )


@router.get("/{id}", response_model=MascotaConDuenioRead, status_code=status.HTTP_200_OK)
async def get_mascota(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> MascotaConDuenioRead:
    """Obtiene el detalle de una mascota con su dueño precargado (joinedload)."""
    mascota = await obtener_mascota_por_id(session, id)
    return MascotaConDuenioRead.model_validate(mascota)
