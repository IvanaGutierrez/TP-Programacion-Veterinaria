from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class FichaBase(BaseModel):
    telefono: str
    direccion: str


class FichaCreate(FichaBase):
    pass


class FichaRead(FichaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    duenio_id: int


class DuenioBase(BaseModel):
    nombre: str
    email: EmailStr


class DuenioCreate(DuenioBase):
    pass


class DuenioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None


class DuenioSimpleRead(DuenioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DuenioRead(DuenioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # En Duenio, la ficha se resuelve como un objeto (o null), nunca como una lista
    ficha: Optional[FichaRead] = None


class MascotaResumenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    especie: str
    duenio_id: int
