import asyncio
from app.modules.laboratorio.cliente import consultar_stock


async def obtener_stock_vacuna(vacuna: str) -> int:
    """
    Delega la ejecución de la función sincrónica bloqueante 'consultar_stock'
    fuera del bucle de eventos principal (event loop) a un thread pool usando asyncio.to_thread.
    Esto garantiza que las llamadas concurrentes no congelen FastAPI ni retrasen GET /health/live.
    """
    return await asyncio.to_thread(consultar_stock, vacuna)
