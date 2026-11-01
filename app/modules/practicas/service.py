from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.modules.practicas.models import Practica
from app.modules.practicas.schemas import PracticaCreate


async def crear_practica(session: AsyncSession, data: PracticaCreate) -> Practica:
    """
    RN-02: El nombre de una práctica es único.
    Escribe directamente en base sin SELECT previo y atrapa IntegrityError para responder 409.
    """
    practica = Practica(nombre=data.nombre, precio=data.precio)
    session.add(practica)
    try:
        await session.commit()
        await session.refresh(practica)
        return practica
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una práctica con el nombre '{data.nombre}'",
        ) from exc


async def listar_practicas(session: AsyncSession) -> list[Practica]:
    """Obtiene el catálogo completo de prácticas médicas."""
    query = select(Practica).order_by(Practica.id)
    result = await session.execute(query)
    return list(result.scalars().all())
