from pydantic import BaseModel, ConfigDict
from app.modules.duenios.schemas import DuenioSimpleRead


class MascotaBase(BaseModel):
    nombre: str
    especie: str


class MascotaCreate(MascotaBase):
    duenio_id: int


class MascotaRead(MascotaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    duenio_id: int


class MascotaConDuenioRead(MascotaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    duenio: DuenioSimpleRead


class MascotasPaginadas(BaseModel):
    items: list[MascotaConDuenioRead]
    total: int
    page: int
    size: int
    pages: int
