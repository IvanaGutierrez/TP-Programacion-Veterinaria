from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.turnos.models import TurnoPractica


class Practica(SQLModel, table=True):
    __tablename__ = "practica"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False, unique=True, index=True)
    precio: Decimal = Field(
        sa_column=Column(
            Numeric(10, 2),
            CheckConstraint("precio > 0", name="chk_practica_precio_positivo"),
            nullable=False,
        )
    )

    # Navegación hacia los turnos en los que figura la práctica
    turno_practicas: list["TurnoPractica"] = Relationship(back_populates="practica")
