from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.mascotas.models import Mascota
    from app.modules.practicas.models import Practica


class TurnoPractica(SQLModel, table=True):
    __tablename__ = "turno_practica"

    # Clave primaria compuesta (turno_id, practica_id)
    # turno_id con ON DELETE CASCADE para que la base de datos gestione el borrado
    turno_id: int = Field(
        foreign_key="turno.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    # practica_id lleva índice explícito porque en una PK compuesta (turno_id, practica_id),
    # el índice B-tree de PostgreSQL solo indexa el prefijo izquierdo (turno_id)
    practica_id: int = Field(
        foreign_key="practica.id",
        primary_key=True,
        index=True,
    )
    # precio_unitario congelado al momento de reservar el turno
    precio_unitario: Decimal = Field(
        sa_column=Column(
            Numeric(10, 2),
            CheckConstraint("precio_unitario > 0", name="chk_turno_practica_precio_positivo"),
            nullable=False,
        )
    )

    # Navegación hacia turno y práctica
    turno: Optional["Turno"] = Relationship(back_populates="practicas")
    practica: Optional["Practica"] = Relationship(back_populates="turno_practicas")


class Turno(SQLModel, table=True):
    __tablename__ = "turno"

    id: Optional[int] = Field(default=None, primary_key=True)
    mascota_id: int = Field(
        foreign_key="mascota.id",
        nullable=False,
        index=True,
    )
    fecha: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    motivo: str = Field(nullable=False)
    total: Decimal = Field(
        sa_column=Column(
            Numeric(12, 2),
            CheckConstraint("total >= 0", name="chk_turno_total_no_negativo"),
            nullable=False,
        )
    )

    # Navegación bidireccional
    mascota: Optional["Mascota"] = Relationship(back_populates="turnos")
    # passive_deletes=True delega el borrado en cascada completamente a PostgreSQL (ON DELETE CASCADE)
    # evitando que el ORM intente emitir DELETEs o vaciar filas por su cuenta
    practicas: list[TurnoPractica] = Relationship(
        back_populates="turno",
        sa_relationship_kwargs={
            "passive_deletes": True,
            "cascade": "all, delete-orphan",
        },
    )
