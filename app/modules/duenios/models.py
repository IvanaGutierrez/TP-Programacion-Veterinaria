from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.mascotas.models import Mascota


class Duenio(SQLModel, table=True):
    __tablename__ = "duenio"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)

    # Relación 1 a 1 con FichaDuenio. uselist=False asegura que se resuelva como objeto y no como lista
    ficha: Optional["FichaDuenio"] = Relationship(
        back_populates="duenio",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "uselist": False,
        },
    )

    # Relación 1 a N con Mascota (agregación)
    mascotas: list["Mascota"] = Relationship(back_populates="duenio")


class FichaDuenio(SQLModel, table=True):
    __tablename__ = "ficha_duenio"

    id: Optional[int] = Field(default=None, primary_key=True)
    duenio_id: int = Field(
        foreign_key="duenio.id",
        unique=True,
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    telefono: str = Field(nullable=False)
    direccion: str = Field(nullable=False)

    # Navegación hacia el dueño
    duenio: Optional[Duenio] = Relationship(back_populates="ficha")
