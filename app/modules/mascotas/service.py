import math
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.modules.mascotas.models import Mascota
from app.modules.mascotas.schemas import MascotaCreate


async def crear_mascota(session: AsyncSession, data: MascotaCreate) -> Mascota:
    """
    Alta de mascota. Se escribe directamente sin SELECT previo ("Look Before You Leap").
    Si duenio_id no existe, PostgreSQL lanza violación de FK que se atrapa como IntegrityError
    para devolver HTTP 409 (caso C-04).
    """
    mascota = Mascota(
        nombre=data.nombre,
        especie=data.especie,
        duenio_id=data.duenio_id,
    )
    session.add(mascota)
    try:
        await session.commit()
        await session.refresh(mascota)
        return mascota
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El dueño con ID {data.duenio_id} no existe",
        ) from exc


async def listar_mascotas(
    session: AsyncSession, page: int = 1, size: int = 20
) -> dict:
    """
    Listado paginado de mascotas con envoltorio { items, total, page, size, pages }.
    size va de 1 a 100 con default 20.
    Si page > pages, responde 422 (salvo page=1 cuando total=0).
    Carga anticipada con joinedload(Mascota.duenio) para evitar N+1 y MissingGreenlet.
    """
    # 1. Conteo total de registros
    count_query = select(func.count(Mascota.id))
    total_result = await session.execute(count_query)
    total: int = total_result.scalar_one()

    # 2. Cálculo de páginas totales
    pages = math.ceil(total / size) if total > 0 else 1

    # 3. Validación de rango de página
    if total > 0 and page > pages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Página {page} fuera de rango. Páginas disponibles: {pages}",
        )
    if total == 0 and page > 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Página {page} fuera de rango. No existen registros",
        )

    # 4. Consulta de registros con carga anticipada del dueño
    offset = (page - 1) * size
    query = (
        select(Mascota)
        .options(joinedload(Mascota.duenio))
        .order_by(Mascota.id)
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(query)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


async def obtener_mascota_por_id(session: AsyncSession, mascota_id: int) -> Mascota:
    """
    Obtiene una mascota con su dueño precargado vía joinedload.
    Si no existe, responde 404.
    """
    query = (
        select(Mascota)
        .where(Mascota.id == mascota_id)
        .options(joinedload(Mascota.duenio))
    )
    result = await session.execute(query)
    mascota = result.scalar_one_or_none()
    if not mascota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la mascota con ID {mascota_id}",
        )
    return mascota
