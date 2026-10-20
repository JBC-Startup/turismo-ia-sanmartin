#!/usr/bin/env python3
"""
Test de Integración End-to-End para la API REST de TurismoIA San Martín
======================================================================
Valida contra la base de datos PostgreSQL real corriendo en Docker:
1. GET /health: Conectividad con PostgreSQL y modelo cargado en memoria RAM.
2. POST /api/recomendar: Generación del Top-5 con similitud del coseno y filtros duros.
3. Validación en base de datos de las inserciones en:
   - turismo.sesion_preferencia
   - turismo.ejecucion_recomendacion
   - turismo.recomendacion
4. POST /api/valorar: Registro de feedback (1-5 estrellas) y verificación de persistencia
   en la tabla turismo.valoracion.
5. Casos borde: validación de estrellas (1-5), ejecución inexistente, y activación de fallback.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Activar modo testing para aislamiento de conexiones por loop
os.environ["TESTING"] = "1"

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import text

# Configurar sys.path para importar módulos locales de backend
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT / "ml_engine") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "ml_engine"))

from database import AsyncSessionLocal
from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    """Fixture para cliente HTTP asíncrono con el ciclo de vida (Lifespan) activo."""
    async with app.router.lifespan_context(app):
        async with ASGITransport(app=app) as transport:
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                yield ac


@pytest.mark.asyncio
async def test_health_check_endpoint(client: httpx.AsyncClient):
    """Valida el endpoint GET /health."""
    response = await client.get("/health")
    assert response.status_code == 200, f"Error en /health: {response.text}"
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["database"]["total_atractivos"] >= 297
    assert data["model"]["loaded"] is True
    assert data["model"]["atractivos_en_catalogo"] >= 297
    assert data["model"]["vector_dimension"] == 139


@pytest.mark.asyncio
async def test_recomendar_y_persistencia_en_postgresql(client: httpx.AsyncClient):
    """
    Valida POST /api/recomendar y comprueba directamente en PostgreSQL en Docker:
    - Inserción de la sesión en turismo.sesion_preferencia.
    - Inserción de la ejecución en turismo.ejecucion_recomendacion.
    - Inserción de las 5 alternativas en turismo.recomendacion.
    """
    payload = {
        "intereses": "cataratas naturaleza cascadas",
        "tiempo_en_horas": 4.0,
        "presupuesto": 30.0,
        "provincia": "SAN MARTIN",
        "compania": "Amigos",
        "nivel_dificultad": "Baja",
        "top_n": 5,
        "tipo_dispositivo": "movil",
        "consentimiento_datos": True,
    }

    resp = await client.post("/api/recomendar", json=payload)
    assert resp.status_code == 200, f"Error en /api/recomendar: {resp.text}"
    data = resp.json()

    # 1. Validar estructura de respuesta HTTP
    id_sesion_str = data["id_sesion"]
    id_ejecucion = data["id_ejecucion"]
    recs = data["recomendaciones"]

    assert id_sesion_str, "id_sesion no debe estar vacío"
    assert id_ejecucion > 0, "id_ejecucion debe ser un entero positivo"
    assert len(recs) == 5, f"Se esperaban 5 recomendaciones, se obtuvieron {len(recs)}"
    assert data["total_candidatos"] > 0
    assert data["tiempo_respuesta_ms"] < 250, "La inferencia y persistencia debe ser veloz"

    # 2. Validar filtros duros en cada recomendación
    for r in recs:
        assert r["duracion_estimada_horas"] <= 4.0, f"Duración excedida: {r['duracion_estimada_horas']}"
        assert r["costo_referencial_pen"] <= 30.0, f"Costo excedido: {r['costo_referencial_pen']}"
        assert r["provincia"].upper() == "SAN MARTIN"
        assert 0.0 <= r["afinidad_pct"] <= 100.0
        assert 0.0 <= r["puntaje_afinidad"] <= 1.0
        assert len(r["explicacion"]) > 10
        assert r["id_recomendacion"] > 0
        assert r["id_atractivo"] > 0

    # 3. Validación directa contra la base de datos PostgreSQL de Docker
    async with AsyncSessionLocal() as db:
        # Validar sesion_preferencia
        res_sesion = await db.execute(
            text("SELECT tiempo_disponible_horas, presupuesto_max_pen, texto_libre FROM turismo.sesion_preferencia WHERE id_sesion = :sid"),
            {"sid": id_sesion_str},
        )
        row_sesion = res_sesion.fetchone()
        assert row_sesion is not None, f"Sesión {id_sesion_str} no encontrada en PostgreSQL"
        assert float(row_sesion[0]) == 4.0
        assert float(row_sesion[1]) == 30.0
        assert "cataratas" in row_sesion[2]

        # Validar sesion_provincia
        res_sp = await db.execute(
            text("SELECT id_provincia FROM turismo.sesion_provincia WHERE id_sesion = :sid"),
            {"sid": id_sesion_str},
        )
        row_sp = res_sp.fetchone()
        assert row_sp is not None, "Provincia de sesión no registrada"
        assert row_sp[0] == "2209"  # Ubigeo de SAN MARTIN

        # Validar ejecucion_recomendacion
        res_ejec = await db.execute(
            text("SELECT id_sesion, id_modelo, total_candidatos FROM turismo.ejecucion_recomendacion WHERE id_ejecucion = :eid"),
            {"eid": id_ejecucion},
        )
        row_ejec = res_ejec.fetchone()
        assert row_ejec is not None, f"Ejecución {id_ejecucion} no encontrada en PostgreSQL"
        assert str(row_ejec[0]) == id_sesion_str
        assert row_ejec[1] == 1  # Modelo activo

        # Validar las 5 recomendaciones persistidas
        res_recs = await db.execute(
            text("SELECT posicion, id_atractivo, puntaje_afinidad, cumple_filtros FROM turismo.recomendacion WHERE id_ejecucion = :eid ORDER BY posicion ASC"),
            {"eid": id_ejecucion},
        )
        db_recs = res_recs.fetchall()
        assert len(db_recs) == 5, f"Esperadas 5 recomendaciones en BD, encontradas: {len(db_recs)}"
        for idx, dbr in enumerate(db_recs, start=1):
            assert dbr[0] == idx  # Posición 1..5
            assert dbr[1] > 0     # id_atractivo
            assert 0.0 <= float(dbr[2]) <= 1.0  # puntaje_afinidad
            assert dbr[3] is True # cumple_filtros


@pytest.mark.asyncio
async def test_valoracion_y_persistencia(client: httpx.AsyncClient):
    """
    Valida POST /api/valorar vinculada a una ejecución real y comprueba
    su persistencia en turismo.valoracion.
    """
    # 1. Crear recomendación previa
    req_rec = {
        "intereses": "cultura arqueologia historia",
        "tiempo_en_horas": 6.0,
        "presupuesto": 50.0,
        "provincia": "LAMAS",
        "compania": "Familia",
        "nivel_dificultad": "Baja",
    }
    rec_resp = await client.post("/api/recomendar", json=req_rec)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    id_ejecucion = rec_data["id_ejecucion"]
    primera_rec = rec_data["recomendaciones"][0]["id_recomendacion"]

    # 2. Registrar valoración de 5 estrellas
    val_payload = {
        "id_ejecucion": id_ejecucion,
        "utilidad": 5,
        "comentario": "Recomendaciones impecables para viajar en familia a Lamas.",
        "id_recomendacion_elegida": primera_rec,
        "eligio_alternativa": True,
        "explicacion_comprensible": True,
    }
    val_resp = await client.post("/api/valorar", json=val_payload)
    assert val_resp.status_code == 201, f"Error en /api/valorar: {val_resp.text}"
    val_data = val_resp.json()

    assert val_data["id_valoracion"] > 0
    assert val_data["id_ejecucion"] == id_ejecucion
    assert val_data["utilidad"] == 5
    assert val_data["eligio_alternativa"] is True
    assert val_data["id_recomendacion_elegida"] == primera_rec

    # 3. Validar directamente en PostgreSQL
    async with AsyncSessionLocal() as db:
        res_val = await db.execute(
            text("SELECT utilidad, eligio_alternativa, id_recomendacion_elegida, comentario FROM turismo.valoracion WHERE id_ejecucion = :eid"),
            {"eid": id_ejecucion},
        )
        row_val = res_val.fetchone()
        assert row_val is not None, f"Valoración de ejecución {id_ejecucion} no encontrada en PostgreSQL"
        assert row_val[0] == 5
        assert row_val[1] is True
        assert row_val[2] == primera_rec
        assert "familia a Lamas" in row_val[3]


@pytest.mark.asyncio
async def test_filtros_y_catalogos(client: httpx.AsyncClient):
    """Valida GET /api/filtros."""
    resp = await client.get("/api/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["provincias"]) == 10
    assert len(data["companias"]) >= 7
    assert len(data["dificultades"]) >= 5


@pytest.mark.asyncio
async def test_atractivos_listado_y_detalle(client: httpx.AsyncClient):
    """Valida GET /api/atractivos y GET /api/atractivos/{id}."""
    resp = await client.get("/api/atractivos?limit=5&provincia=SAN%20MARTIN")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 5
    primer_id = data["items"][0]["id_atractivo"]

    # Detalle individual
    resp_det = await client.get(f"/api/atractivos/{primer_id}")
    assert resp_det.status_code == 200
    det = resp_det.json()
    assert det["id_atractivo"] == primer_id
    assert det["nombre"] != ""


@pytest.mark.asyncio
async def test_metricas_prototipo(client: httpx.AsyncClient):
    """Valida GET /api/metricas."""
    resp = await client.get("/api/metricas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sesiones"] >= 0
    assert data["ejecuciones"] >= 0


@pytest.mark.asyncio
async def test_validacion_errores_y_casos_borde(client: httpx.AsyncClient):
    """Valida controles de entrada, errores HTTP y fallback."""
    # 1. Utilidad fuera de rango (6 estrellas debe fallar con 422)
    resp_inv = await client.post("/api/valorar", json={"id_ejecucion": 1, "utilidad": 6})
    assert resp_inv.status_code == 422

    # 2. Utilidad menor a 1 (0 estrellas debe fallar con 422)
    resp_zero = await client.post("/api/valorar", json={"id_ejecucion": 1, "utilidad": 0})
    assert resp_zero.status_code == 422

    # 3. Valoración de ejecución inexistente (debe devolver 404)
    resp_404 = await client.post("/api/valorar", json={"id_ejecucion": 99999999, "utilidad": 4})
    assert resp_404.status_code == 404

    # 4. Atractivo inexistente (debe devolver 404)
    resp_atr_404 = await client.get("/api/atractivos/9999999")
    assert resp_atr_404.status_code == 404

    # 5. Fallback con provincia muy restrictiva y presupuesto nulo
    resp_fb = await client.post(
        "/api/recomendar",
        json={
            "intereses": "paseo",
            "tiempo_en_horas": 0.5,
            "presupuesto": 0.0,
            "provincia": "EL DORADO",
        },
    )
    assert resp_fb.status_code == 200
    fb_data = resp_fb.json()
    if len(fb_data["recomendaciones"]) > 0:
        assert fb_data["fallback_provincia"] is True


async def _run_all_standalone():
    """Ejecutor standalone cuando se invoca como script directo."""
    print("\n=== EJECUTANDO TEST DE INTEGRACIÓN BACKEND TURISMOIA SAN MARTÍN ===")
    async with app.router.lifespan_context(app):
        async with ASGITransport(app=app) as transport:
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                await test_health_check_endpoint(client)
                print("✔ [1/7] GET /health validado con éxito.")

                await test_filtros_y_catalogos(client)
                print("✔ [2/7] GET /api/filtros validado con éxito.")

                await test_atractivos_listado_y_detalle(client)
                print("✔ [3/7] GET /api/atractivos y GET /api/atractivos/{id} validados con éxito.")

                await test_recomendar_y_persistencia_en_postgresql(client)
                print("✔ [4/7] POST /api/recomendar y persistencia en DB PostgreSQL validados con éxito.")

                await test_valoracion_y_persistencia(client)
                print("✔ [5/7] POST /api/valorar y persistencia en DB PostgreSQL validados con éxito.")

                await test_metricas_prototipo(client)
                print("✔ [6/7] GET /api/metricas validado con éxito.")

                await test_validacion_errores_y_casos_borde(client)
                print("✔ [7/7] Casos borde, errores 404/422 y fallbacks comprobados con éxito.")

    print("\nTODAS LAS PRUEBAS DE INTEGRACIÓN PASARON SATISFACTORIAMENTE (100% OK).\n")


if __name__ == "__main__":
    asyncio.run(_run_all_standalone())
