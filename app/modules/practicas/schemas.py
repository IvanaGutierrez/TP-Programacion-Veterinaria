from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PracticaBase(BaseModel):
    nombre: str
    precio: Decimal = Field(..., gt=0, description="Precio mayor a cero")


class PracticaCreate(PracticaBase):
    pass


class PracticaRead(PracticaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
