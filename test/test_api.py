import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from reiniciar import reiniciar_base_de_datos


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Ejecuta reiniciar_base_de_datos y activa el ciclo de vida (lifespan) de FastAPI para la sesión de pruebas."""
    await reiniciar_base_de_datos()
    async with app.router.lifespan_context(app):
        yield


@pytest.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"estado": "vivo"}


@pytest.mark.asyncio
async def test_health_ready(client: AsyncClient):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"estado": "base de datos conectada"}


@pytest.mark.asyncio
async def test_c01_parametro_no_entero(client: AsyncClient):
    """C-01: Parámetro de ruta que no es entero -> 422 sin ejecutar el handler."""
    response = await client.get("/duenios/abc")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_c02_duplicados_email_y_practica(client: AsyncClient):
    """C-02: Email de dueño o nombre de práctica repetido -> 409 con mensaje propio."""
    # Email duplicado (Juan Pérez ya existe en seed data)
    resp_duenio = await client.post(
        "/duenios/",
        json={"nombre": "Juan Clónico", "email": "juan.perez@example.com"},
    )
    assert resp_duenio.status_code == 409
    assert "registrado" in resp_duenio.json()["detail"].lower()

    # Práctica duplicada ('Consulta general' ya existe en seed data)
    resp_practica = await client.post(
        "/practicas/",
        json={"nombre": "Consulta general", "precio": "20000.00"},
    )
    assert resp_practica.status_code == 409
    assert "ya existe" in resp_practica.json()["detail"].lower()


@pytest.mark.asyncio
async def test_c03_segunda_ficha_mismo_duenio(client: AsyncClient):
    """C-03: Segunda ficha para el mismo dueño -> 409."""
    # Dueño 1 ya tiene ficha creada en seed data
    response = await client.post(
        "/duenios/1/ficha",
        json={"telefono": "11-0000-0000", "direccion": "Otra calle 456"},
    )
    assert response.status_code == 409
    assert "ya posee una ficha" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_c04_integridad_referencial_y_todo_o_nada(client: AsyncClient):
    """C-04: Mascota con dueño inexistente (409) y turno con práctica inexistente (409, no guarda nada)."""
    # Mascota con dueño inexistente
    resp_mascota = await client.post(
        "/mascotas/",
        json={"nombre": "Ghost", "especie": "perro", "duenio_id": 99999},
    )
    assert resp_mascota.status_code == 409

    # Turno con práctica inexistente
    resp_turno = await client.post(
        "/turnos/",
        json={
            "mascota_id": 1,
            "fecha": "2026-11-20T10:00:00-03:00",
            "motivo": "Control con práctica fantasma",
            "practicas": [{"practica_id": 1}, {"practica_id": 99999}],
        },
    )
    assert resp_turno.status_code == 409


@pytest.mark.asyncio
async def test_c05_borrar_duenio_con_mascotas_y_borrar_turno(client: AsyncClient):
    """C-05: Borrar dueño con mascotas (409) y borrar turno (204, cascada)."""
    # Intento de borrar Dueño 1 (tiene mascotas Toby y Milo)
    resp_del_duenio = await client.delete("/duenios/1")
    assert resp_del_duenio.status_code == 409

    # Borrar Turno 1 (creado en seed)
    resp_del_turno = await client.delete("/turnos/1")
    assert resp_del_turno.status_code == 204

    # Comprobar que Turno 1 ya no existe
    resp_get_turno = await client.get("/turnos/1")
    assert resp_get_turno.status_code == 404


@pytest.mark.asyncio
async def test_c06_turno_valido_con_dos_practicas(client: AsyncClient):
    """C-06: Turno válido con dos prácticas (201 con precios copiados y total calculado)."""
    # Mascota 2 (Milo), prácticas 1 (15000.00) y 4 (8000.00) -> total 23000.00
    resp = await client.post(
        "/turnos/",
        json={
            "mascota_id": 2,
            "fecha": "2026-11-25T14:00:00-03:00",
            "motivo": "Chequeo y desparasitación",
            "practicas": [{"practica_id": 1}, {"practica_id": 4}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["total"] == "23000.00"
    assert len(data["practicas"]) == 2
    assert data["practicas"][0]["precio_unitario"] == "15000.00"
    assert data["practicas"][1]["precio_unitario"] == "8000.00"


@pytest.mark.asyncio
async def test_c07_detalle_turno_eager_loading(client: AsyncClient):
    """C-07: Detalle de turno con relaciones precargadas."""
    # Crear turno con 1 práctica
    resp1 = await client.post(
        "/turnos/",
        json={
            "mascota_id": 3,
            "fecha": "2026-11-26T10:00:00-03:00",
            "motivo": "Consulta sola",
            "practicas": [{"practica_id": 1}],
        },
    )
    assert resp1.status_code == 201
    turno1_id = resp1.json()["id"]

    # Consultar detalle
    detalle = await client.get(f"/turnos/{turno1_id}")
    assert detalle.status_code == 200
    assert detalle.json()["mascota"]["nombre"] == "Luna"
    assert len(detalle.json()["practicas"]) == 1


@pytest.mark.asyncio
async def test_c08_validacion_precio_positivo(client: AsyncClient):
    """C-08: Validación de precio > 0 en DTO (422)."""
    resp = await client.post(
        "/practicas/",
        json={"nombre": "Práctica Gratis", "precio": "0.00"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_c09_laboratorio_no_bloqueante(client: AsyncClient):
    """C-09: Consultas concurrentes al laboratorio no bloquean /health/live."""
    # Lanzamos 3 consultas de laboratorio en paralelo
    task1 = asyncio.create_task(client.get("/laboratorio/stock/antirrabica"))
    task2 = asyncio.create_task(client.get("/laboratorio/stock/sextuple"))
    task3 = asyncio.create_task(client.get("/laboratorio/stock/triplefelina"))

    # Pequeña pausa para asegurar que entraron al pool de hilos
    await asyncio.sleep(0.05)

    # GET /health/live debe responder inmediatamente
    t_start = asyncio.get_event_loop().time()
    resp_health = await client.get("/health/live")
    t_duration = asyncio.get_event_loop().time() - t_start

    assert resp_health.status_code == 200
    assert resp_health.json() == {"estado": "vivo"}
    # Comprobar que respondió en menos de 0.2 segundos (sin esperar al sleep(1) del laboratorio)
    assert t_duration < 0.2

    # Esperar finalización de las 3 tareas de laboratorio
    r1, r2, r3 = await asyncio.gather(task1, task2, task3)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_mascotas_paginacion(client: AsyncClient):
    """Paginación de mascotas con envoltorio { items, total, page, size, pages }."""
    # Página 1 válida
    resp = await client.get("/mascotas/?page=1&size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["pages"] >= 1

    # Página fuera de rango (422)
    resp_out = await client.get("/mascotas/?page=999&size=20")
    assert resp_out.status_code == 422


@pytest.mark.asyncio
async def test_duenio_patch_parcial(client: AsyncClient):
    """Modificación parcial con PATCH usando exclude_unset."""
    resp = await client.patch(
        "/duenios/2",
        json={"nombre": "María Gómez Actualizada"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "María Gómez Actualizada"
    # El email no debe haber cambiado
    assert data["email"] == "maria.gomez@example.com"
