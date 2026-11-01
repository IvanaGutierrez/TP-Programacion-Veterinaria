from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.duenios.schemas import (
    DuenioCreate,
    DuenioRead,
    DuenioUpdate,
    FichaCreate,
    FichaRead,
    MascotaResumenRead,
)
from app.modules.duenios.service import (
    actualizar_duenio_parcial,
    crear_duenio,
    crear_ficha_duenio,
    eliminar_duenio,
    obtener_duenio_por_id,
    obtener_mascotas_de_duenio,
)

router = APIRouter(prefix="/duenios", tags=["Dueños"])


@router.post("/", response_model=DuenioRead, status_code=status.HTTP_201_CREATED)
async def post_duenio(
    data: DuenioCreate,
    session: AsyncSession = Depends(get_session),
) -> DuenioRead:
    """Registra un nuevo dueño. Responde 201 Created o 409 Conflict si el email ya existe."""
    duenio = await crear_duenio(session, data)
    return DuenioRead.model_validate(duenio)


@router.get("/{id}", response_model=DuenioRead, status_code=status.HTTP_200_OK)
async def get_duenio(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> DuenioRead:
    """Obtiene un dueño con su ficha precargada. Si id no es entero, FastAPI responde 422."""
    duenio = await obtener_duenio_por_id(session, id)
    return DuenioRead.model_validate(duenio)


@router.patch("/{id}", response_model=DuenioRead, status_code=status.HTTP_200_OK)
async def patch_duenio(
    id: int,
    data: DuenioUpdate,
    session: AsyncSession = Depends(get_session),
) -> DuenioRead:
    """Actualización parcial de dueño aplicando únicamente los campos enviados."""
    duenio = await actualizar_duenio_parcial(session, id, data)
    return DuenioRead.model_validate(duenio)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_duenio(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Elimina un dueño. Si tiene mascotas asociadas, responde 409 por restricción ON DELETE RESTRICT."""
    await eliminar_duenio(session, id)


@router.post(
    "/{id}/ficha", response_model=FichaRead, status_code=status.HTTP_201_CREATED
)
async def post_ficha_duenio(
    id: int,
    data: FichaCreate,
    session: AsyncSession = Depends(get_session),
) -> FichaRead:
    """Registra la ficha de contacto para un dueño. Un dueño solo puede tener una ficha (409 en duplicado)."""
    ficha = await crear_ficha_duenio(session, id, data)
    return FichaRead.model_validate(ficha)


@router.get(
    "/{id}/mascotas",
    response_model=list[MascotaResumenRead],
    status_code=status.HTTP_200_OK,
)
async def get_duenio_mascotas(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> list[MascotaResumenRead]:
    """Obtiene el listado de mascotas pertenecientes al dueño indicado."""
    mascotas = await obtener_mascotas_de_duenio(session, id)
    return [MascotaResumenRead.model_validate(m) for m in mascotas]
