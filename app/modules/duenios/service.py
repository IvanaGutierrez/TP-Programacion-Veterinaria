from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.modules.duenios.models import Duenio, FichaDuenio
from app.modules.duenios.schemas import DuenioCreate, DuenioUpdate, FichaCreate
from app.modules.mascotas.models import Mascota


async def crear_duenio(session: AsyncSession, data: DuenioCreate) -> Duenio:
    """
    RN-01: Alta de dueño. No hace SELECT previo para chequear unicidad de email.
    Escribe directamente y atrapa IntegrityError para responder HTTP 409.
    """
    duenio = Duenio(nombre=data.nombre, email=str(data.email))
    session.add(duenio)
    try:
        await session.commit()
        await session.refresh(duenio)
        return duenio
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya se encuentra registrado",
        ) from exc


async def obtener_duenio_por_id(session: AsyncSession, duenio_id: int) -> Duenio:
    """
    Obtiene el dueño con su ficha precargada mediante joinedload (relación 1 a 1).
    Evita el problema N+1 y excepciones MissingGreenlet.
    """
    query = (
        select(Duenio)
        .where(Duenio.id == duenio_id)
        .options(joinedload(Duenio.ficha))
    )
    result = await session.execute(query)
    duenio = result.scalar_one_or_none()
    if not duenio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el dueño con ID {duenio_id}",
        )
    return duenio


async def actualizar_duenio_parcial(
    session: AsyncSession, duenio_id: int, data: DuenioUpdate
) -> Duenio:
    """
    PATCH del dueño: Aplica sólo los campos enviados con exclude_unset (sección 2.6).
    Atrapa IntegrityError en caso de conflicto de email (RN-01 -> 409).
    """
    duenio = await obtener_duenio_por_id(session, duenio_id)
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return duenio

    for key, value in update_data.items():
        if value is not None and key == "email":
            value = str(value)
        setattr(duenio, key, value)

    session.add(duenio)
    try:
        await session.commit()
        # Aseguramos que la ficha siga cargada en memoria tras commit
        return await obtener_duenio_por_id(session, duenio_id)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya se encuentra registrado por otro dueño",
        ) from exc


async def eliminar_duenio(session: AsyncSession, duenio_id: int) -> None:
    """
    RN-08: Borrar dueño con ON DELETE RESTRICT.
    Si el dueño tiene mascotas, la base de datos rechaza la eliminación con violación de FK.
    El service atrapa el IntegrityError, hace rollback y responde HTTP 409.
    """
    duenio = await obtener_duenio_por_id(session, duenio_id)
    try:
        await session.delete(duenio)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede borrar un dueño que tenga mascotas a su nombre",
        ) from exc


async def crear_ficha_duenio(
    session: AsyncSession, duenio_id: int, data: FichaCreate
) -> FichaDuenio:
    """
    RN-03: Un dueño tiene como máximo una ficha (UNIQUE en ficha_duenio.duenio_id).
    Verifica existencia de dueño (404) y delega unicidad en la base de datos (409).
    """
    # Verificamos existencia previa del dueño para devolver 404 si no existe
    await obtener_duenio_por_id(session, duenio_id)

    ficha = FichaDuenio(
        duenio_id=duenio_id,
        telefono=data.telefono,
        direccion=data.direccion,
    )
    session.add(ficha)
    try:
        await session.commit()
        await session.refresh(ficha)
        return ficha
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El dueño ya posee una ficha registrada",
        ) from exc


async def obtener_mascotas_de_duenio(
    session: AsyncSession, duenio_id: int
) -> list[Mascota]:
    """
    Obtiene las mascotas asociadas a un dueño. Si el dueño no existe, responde 404.
    """
    await obtener_duenio_por_id(session, duenio_id)
    query = select(Mascota).where(Mascota.duenio_id == duenio_id)
    result = await session.execute(query)
    return list(result.scalars().all())
