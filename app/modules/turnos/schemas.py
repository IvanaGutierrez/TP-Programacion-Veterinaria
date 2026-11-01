from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TurnoPracticaItemCreate(BaseModel):
    practica_id: int


class TurnoCreate(BaseModel):
    mascota_id: int
    fecha: datetime
    motivo: str
    # RN-05: El turno se reserva con sus prácticas y debe tener al menos una (422 si la lista está vacía)
    # Ni los precios ni el total viajan en el DTO de alta
    practicas: list[TurnoPracticaItemCreate] = Field(
        ..., min_length=1, description="Lista de prácticas solicitadas (mínimo una)"
    )


class MascotaSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    especie: str


class TurnoPracticaRead(BaseModel):
    practica_id: int
    nombre: str
    precio_unitario: str

    model_config = ConfigDict(from_attributes=True)


class TurnoRead(BaseModel):
    id: int
    fecha: datetime
    motivo: str
    total: str
    mascota: MascotaSimpleRead
    practicas: list[TurnoPracticaRead]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("fecha")
    def serialize_fecha(self, v: datetime) -> str:
        """Formatea la fecha en formato ISO 8601 UTC terminado en Z según la convención del TP."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        v_utc = v.astimezone(timezone.utc)
        return v_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
