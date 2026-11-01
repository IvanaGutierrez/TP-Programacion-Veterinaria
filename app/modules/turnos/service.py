from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.modules.mascotas.models import Mascota
from app.modules.practicas.models import Practica
from app.modules.turnos.models import Turno, TurnoPractica
from app.modules.turnos.schemas import (
    MascotaSimpleRead,
    TurnoCreate,
    TurnoPracticaRead,
    TurnoRead,
)


def _mapear_turno_read(turno: Turno) -> TurnoRead:
    """Mapea una entidad Turno con relaciones precargadas a su DTO de salida."""
    practicas_dto = [
        TurnoPracticaRead(
            practica_id=tp.practica_id,
            nombre=tp.practica.nombre if tp.practica else "",
            precio_unitario=f"{tp.precio_unitario:.2f}",
        )
        for tp in turno.practicas
    ]
    return TurnoRead(
        id=turno.id,  # type: ignore[arg-type]
        fecha=turno.fecha,
        motivo=turno.motivo,
        total=f"{turno.total:.2f}",
        mascota=MascotaSimpleRead(
            id=turno.mascota.id,  # type: ignore[arg-type, union-attr]
            nombre=turno.mascota.nombre,  # type: ignore[union-attr]
            especie=turno.mascota.especie,  # type: ignore[union-attr]
        ),
        practicas=practicas_dto,
    )


async def obtener_turno_por_id(session: AsyncSession, turno_id: int) -> TurnoRead:
    """
    Obtiene el detalle de un turno con carga anticipada explícita:
    joinedload para la relación 'a uno' (mascota) y selectinload para la colección (practicas).
    Garantiza un número fijo de consultas (2 consultas) sin importar cuántas prácticas tenga (caso C-07).
    """
    query = (
        select(Turno)
        .where(Turno.id == turno_id)
        .options(
            joinedload(Turno.mascota),
            selectinload(Turno.practicas).joinedload(TurnoPractica.practica),
        )
    )
    result = await session.execute(query)
    turno = result.scalar_one_or_none()
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el turno con ID {turno_id}",
        )
    return _mapear_turno_read(turno)


async def crear_turno(session: AsyncSession, data: TurnoCreate) -> TurnoRead:
    """
    Alta atómica de un turno con sus prácticas asociadas (RN-05, RN-06, RN-07).
    - Valida existencia de la mascota y de todas las prácticas en catálogo.
    - Si algo falla, la transacción se aborta completamente (nada queda guardado, caso C-04).
    - Congela el precio_unitario vigente en turno_practica.
    - Calcula el total = sum(precio_unitario).
    - Si se repite una práctica, la PK compuesta (turno_id, practica_id) rechaza con 409.
    """
    # 1. Verificar existencia de la mascota
    mascota = await session.get(Mascota, data.mascota_id)
    if not mascota:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La mascota con ID {data.mascota_id} no existe",
        )

    # 2. Consultar prácticas vigentes en el catálogo
    requested_ids = [item.practica_id for item in data.practicas]
    query_practicas = select(Practica).where(Practica.id.in_(requested_ids))
    result_practicas = await session.execute(query_practicas)
    practicas_db = {p.id: p for p in result_practicas.scalars().all()}

    # Si alguna práctica solicitada no existe, se rechaza la operación completa
    for pid in requested_ids:
        if pid not in practicas_db:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La práctica con ID {pid} no existe en el catálogo",
            )

    # 3. Congelar precios y calcular total
    total = sum(practicas_db[item.practica_id].precio for item in data.practicas)

    # 4. Crear turno en la transacción
    turno = Turno(
        mascota_id=data.mascota_id,
        fecha=data.fecha,
        motivo=data.motivo,
        total=total,
    )
    session.add(turno)
    await session.flush()  # Genera el ID del turno dentro de la transacción activa

    # 5. Crear registros TurnoPractica asociados
    for item in data.practicas:
        practica_vigente = practicas_db[item.practica_id]
        tp = TurnoPractica(
            turno_id=turno.id,  # type: ignore[arg-type]
            practica_id=item.practica_id,
            precio_unitario=practica_vigente.precio,
        )
        session.add(tp)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        # RN-07: Práctica duplicada rechazada por la clave primaria compuesta (turno_id, practica_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Una misma práctica no puede aparecer dos veces en un turno",
        ) from exc

    # Retorna el turno con carga anticipada garantizada
    return await obtener_turno_por_id(session, turno.id)  # type: ignore[arg-type]


async def eliminar_turno(session: AsyncSession, turno_id: int) -> None:
    """
    RN-09: Al borrar un turno, PostgreSQL elimina en cascada sus prácticas asociadas
    mediante ON DELETE CASCADE en turno_practica.turno_id.
    La relación Turno.practicas tiene passive_deletes=True para que SQLAlchemy
    no emita consultas redundantes.
    """
    turno = await session.get(Turno, turno_id)
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el turno con ID {turno_id}",
        )
    await session.delete(turno)
    await session.commit()
