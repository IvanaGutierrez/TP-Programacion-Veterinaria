from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.duenios.models import Duenio
    from app.modules.turnos.models import Turno


class Mascota(SQLModel, table=True):
    __tablename__ = "mascota"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False)
    especie: str = Field(nullable=False)
    duenio_id: int = Field(
        foreign_key="duenio.id",
        nullable=False,
        ondelete="RESTRICT",
        index=True,
    )

    # Navegación bidireccional
    duenio: Optional["Duenio"] = Relationship(back_populates="mascotas")
    turnos: list["Turno"] = Relationship(back_populates="mascota")
