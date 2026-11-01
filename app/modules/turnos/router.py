from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.turnos.schemas import TurnoCreate, TurnoRead
from app.modules.turnos.service import (
    crear_turno,
    eliminar_turno,
    obtener_turno_por_id,
)

router = APIRouter(prefix="/turnos", tags=["Turnos"])


@router.post("/", response_model=TurnoRead, status_code=status.HTTP_201_CREATED)
async def post_turno(
    data: TurnoCreate,
    session: AsyncSession = Depends(get_session),
) -> TurnoRead:
    """
    Reserva un turno con sus prácticas asociadas.
    Copia los precios vigentes, congela el precio unitario y calcula el total automáticamente.
    """
    return await crear_turno(session, data)


@router.get("/{id}", response_model=TurnoRead, status_code=status.HTTP_200_OK)
async def get_turno(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> TurnoRead:
    """
    Obtiene el detalle de un turno con su mascota y sus prácticas asociadas.
    Resuelto con un número fijo de consultas (joinedload + selectinload) para evitar N+1.
    """
    return await obtener_turno_por_id(session, id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_turno(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Elimina un turno. La base de datos elimina en cascada las prácticas asociadas
    mediante ON DELETE CASCADE en turno_practica (con passive_deletes=True en el ORM).
    """
    await eliminar_turno(session, id)
