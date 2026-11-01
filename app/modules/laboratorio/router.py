from fastapi import APIRouter, status
from app.modules.laboratorio.service import obtener_stock_vacuna

router = APIRouter(prefix="/laboratorio", tags=["Laboratorio"])


@router.get("/stock/{vacuna}", status_code=status.HTTP_200_OK)
async def get_stock_vacuna(vacuna: str) -> dict[str, str | int]:
    """
    Consulta de stock de vacunas con biblioteca externa sincrónica.
    Se ejecuta de forma asincrónica no bloqueante para el servidor.
    """
    stock = await obtener_stock_vacuna(vacuna)
    return {"vacuna": vacuna, "stock": stock}
