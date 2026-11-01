"""
Script de inicialización y siembra de la base de datos (reiniciar.py).

Funcionalidades:
1. Verifica si la base de datos destino existe; si no existe, la crea automáticamente.
2. Registra todos los modelos de SQLModel.
3. Elimina todas las tablas existentes en PostgreSQL (drop_all).
4. Recrea todas las tablas con sus restricciones e índices (create_all).
5. Carga los datos iniciales mínimos requeridos por la cátedra:
   - 2 dueños, uno con ficha.
   - 3 mascotas.
   - 4 prácticas médicas.
   - 1 turno con dos prácticas asociadas.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from urllib.parse import urlparse, urlunparse

from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.database import get_engine, get_session_factory

# Importación obligatoria de todos los modelos para poblar SQLModel.metadata
from app.modules.duenios.models import Duenio, FichaDuenio  # noqa: F401
from app.modules.mascotas.models import Mascota  # noqa: F401
from app.modules.practicas.models import Practica  # noqa: F401
from app.modules.turnos.models import Turno, TurnoPractica  # noqa: F401


async def asegurar_base_de_datos(target_url: str) -> None:
    """
    Verifica si la base de datos destino existe conectando a la base por defecto ('postgres').
    Si no existe, emite 'CREATE DATABASE <nombre>' con autocommit.
    """
    parsed = urlparse(target_url)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        return

    # URL conectando a la base de mantenimiento 'postgres'
    postgres_url = urlunparse(parsed._replace(path="/postgres"))
    engine_admin = get_engine(postgres_url, echo=False)

    try:
        async with engine_admin.connect() as conn:
            # En SQLAlchemy 2.0 async, autocommit se logra con execution_options
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            exists = result.scalar() is not None
            if not exists:
                print(f"La base de datos '{db_name}' no existe. Creándola...")
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Base de datos '{db_name}' creada exitosamente.")
            else:
                print(f"Base de datos '{db_name}' existente.")
    except Exception as e:
        print(f"Nota: No se pudo verificar/crear la base automáticamente vía 'postgres' ({e}). Continuando con la conexión directa...")
    finally:
        await engine_admin.dispose()


async def reiniciar_base_de_datos() -> None:
    print("=" * 60)
    print("Iniciando reinicio de base de datos Veterinaria...")
    print(f"URL: {settings.DATABASE_URL}")
    print("=" * 60)

    # 0. Asegurar que la base de datos exista
    await asegurar_base_de_datos(settings.DATABASE_URL)

    engine = get_engine(settings.DATABASE_URL, echo=False)
    session_factory = get_session_factory(engine)

    # 1. Eliminación y recreación del esquema
    async with engine.begin() as conn:
        print("Eliminando tablas existentes (drop_all)...")
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("Creando tablas con restricciones e índices (create_all)...")
        await conn.run_sync(SQLModel.metadata.create_all)

    # 2. Carga de datos semilla (Seed Data)
    async with session_factory() as session:
        print("Insertando datos semilla...")

        # A. Dueños (2 dueños, uno con ficha)
        duenio1 = Duenio(
            nombre="Juan Pérez",
            email="juan.perez@example.com",
        )
        duenio2 = Duenio(
            nombre="María Gómez",
            email="maria.gomez@example.com",
        )
        session.add(duenio1)
        session.add(duenio2)
        await session.flush()  # Para obtener IDs de dueños

        # Ficha para Dueño 1
        ficha1 = FichaDuenio(
            duenio_id=duenio1.id,  # type: ignore[arg-type]
            telefono="11-4455-6677",
            direccion="Av. Corrientes 1234, CABA",
        )
        session.add(ficha1)

        # B. Mascotas (3 mascotas)
        mascota1 = Mascota(
            nombre="Toby",
            especie="perro",
            duenio_id=duenio1.id,  # type: ignore[arg-type]
        )
        mascota2 = Mascota(
            nombre="Milo",
            especie="gato",
            duenio_id=duenio1.id,  # type: ignore[arg-type]
        )
        mascota3 = Mascota(
            nombre="Luna",
            especie="perro",
            duenio_id=duenio2.id,  # type: ignore[arg-type]
        )
        session.add_all([mascota1, mascota2, mascota3])
        await session.flush()

        # C. Prácticas (4 prácticas con Decimal > 0)
        p1 = Practica(nombre="Consulta general", precio=Decimal("15000.00"))
        p2 = Practica(nombre="Vacuna séxtuple", precio=Decimal("18000.00"))
        p3 = Practica(nombre="Vacuna antirrábica", precio=Decimal("12000.00"))
        p4 = Practica(nombre="Desparasitación", precio=Decimal("8000.00"))
        session.add_all([p1, p2, p3, p4])
        await session.flush()

        # D. Turno (1 turno con 2 prácticas para Mascota 1)
        tz_bsas = timezone(timedelta(hours=-3))
        fecha_turno = datetime(2026, 11, 12, 10, 30, 0, tzinfo=tz_bsas)
        total_turno = p1.precio + p3.precio  # 15000.00 + 12000.00 = 27000.00

        turno1 = Turno(
            mascota_id=mascota1.id,  # type: ignore[arg-type]
            fecha=fecha_turno,
            motivo="Control y vacunación antirrábica",
            total=total_turno,
        )
        session.add(turno1)
        await session.flush()

        # Prácticas congeladas en el turno
        tp1 = TurnoPractica(
            turno_id=turno1.id,  # type: ignore[arg-type]
            practica_id=p1.id,  # type: ignore[arg-type]
            precio_unitario=p1.precio,
        )
        tp2 = TurnoPractica(
            turno_id=turno1.id,  # type: ignore[arg-type]
            practica_id=p3.id,  # type: ignore[arg-type]
            precio_unitario=p3.precio,
        )
        session.add_all([tp1, tp2])

        await session.commit()
        print("Datos semilla insertados exitosamente:")
        print(f"  - Dueños: 2 (ID 1: '{duenio1.nombre}' con ficha, ID 2: '{duenio2.nombre}')")
        print(f"  - Mascotas: 3 (ID 1: '{mascota1.nombre}', ID 2: '{mascota2.nombre}', ID 3: '{mascota3.nombre}')")
        print(f"  - Prácticas: 4 (IDs 1 a 4: Consulta, Séxtuple, Antirrábica, Desparasitación)")
        print(f"  - Turnos: 1 (ID 1: Mascota '{mascota1.nombre}', Total: ${turno1.total})")
        print("=" * 60)

    await engine.dispose()
    print("Reinicio completado con éxito.")


if __name__ == "__main__":
    asyncio.run(reiniciar_base_de_datos())
