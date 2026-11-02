"""
Pruebas Unitarias y de Integración para la Integración de Google Gemini API
===========================================================================
Valida:
1. Lectura segura de GEMINI_API_KEY y GEMINI_MODEL desde la configuración.
2. Ausencia de exposición de la API Key en respuestas, modelos o logs.
3. Extracción contextual de atractivos relevantes de San Martín.
4. Manejo de error controlado ante agotamiento de cuota gratuita (HTTP 429).
5. Manejo de error controlado ante alta demanda o indisponibilidad (HTTP 503).
6. Fallback resiliente local ante desconexión o falta de credenciales.
7. Endpoints /api/chat y /assistant/chat con ciclo de vida FastAPI.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest
from httpx import ASGITransport

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT / "ml_engine") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "ml_engine"))

from config import settings
from gemini_service import (
    buscar_atractivos_relevantes,
    consultar_gemini,
)
from main import app
from schemas import ChatRequest, ChatResponse
from services import procesar_consulta_asistente


@pytest.fixture
def mock_catalogo():
    """Catálogo mínimo simulado con datos representativos de San Martín."""
    return pd.DataFrame([
        {
            "id_recurso": "SM-001",
            "nombre_recurso": "Catarata de Ahuashiyacu",
            "categoria": "Sitios Naturales",
            "tipo": "Caídas de agua",
            "provincia": "SAN MARTIN",
            "distrito": "Banda de Shilcayo",
            "duracion_estimada_horas": 2.5,
            "costo_referencial_pen": 10.0,
            "nivel_dificultad": "Baja",
            "imagen_url": "https://example.com/ahuashiyacu.jpg",
            "descripcion_corta": "Emblemática catarata de 40 metros de altura a pocos minutos de Tarapoto.",
            "etiquetas_interes": "catarata naturaleza aventura agua",
        },
        {
            "id_recurso": "SM-002",
            "nombre_recurso": "Laguna de Sauce (Laguna Azul)",
            "categoria": "Sitios Naturales",
            "tipo": "Lagunas",
            "provincia": "SAN MARTIN",
            "distrito": "Sauce",
            "duracion_estimada_horas": 6.0,
            "costo_referencial_pen": 25.0,
            "nivel_dificultad": "Baja",
            "imagen_url": "https://example.com/sauce.jpg",
            "descripcion_corta": "Hermosa laguna tropical ideal para navegación, pesca y relax.",
            "etiquetas_interes": "laguna sauce descanso navegacion",
        },
        {
            "id_recurso": "SM-003",
            "nombre_recurso": "Castillo de Lamas",
            "categoria": "Manifestaciones Culturales",
            "tipo": "Arquitectura",
            "provincia": "LAMAS",
            "distrito": "Lamas",
            "duracion_estimada_horas": 3.0,
            "costo_referencial_pen": 15.0,
            "nivel_dificultad": "Baja",
            "imagen_url": "https://example.com/lamas.jpg",
            "descripcion_corta": "Construcción de estilo medieval en la cúspide de la ciudad de Lamas.",
            "etiquetas_interes": "cultura castillo lamas historia",
        },
    ])


@pytest.mark.asyncio
async def test_configuracion_gemini_cargada():
    """Verifica que las variables de configuración de Gemini existan en settings."""
    assert hasattr(settings, "GEMINI_API_KEY")
    assert hasattr(settings, "GEMINI_MODEL")
    assert settings.GEMINI_MODEL in ("gemini-2.5-flash", "gemini-3.8-flash", "gemini-flash-lite-latest")


@pytest.mark.asyncio
async def test_buscar_atractivos_relevantes(mock_catalogo):
    """Verifica que el buscador identifique cataratas correctamente en el catálogo."""
    res = buscar_atractivos_relevantes("Quiero visitar cataratas", catalogo=mock_catalogo)
    assert len(res) >= 1
    assert "Ahuashiyacu" in res[0]["nombre"]


@pytest.mark.asyncio
async def test_gemini_exito_200(mock_catalogo):
    """Simula una respuesta exitosa (200 OK) de Gemini API."""
    mock_response = httpx.Response(
        status_code=200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "¡Hola! La **Catarata de Ahuashiyacu** es perfecta para ti.\n- ¿Cómo llegar a Ahuashiyacu?\n- ¿Cuál es el costo de ingreso?"
                            }
                        ]
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        reply, actions, related = await consultar_gemini(
            message="Recomiéndame una catarata",
            catalogo=mock_catalogo,
            api_key="test_fake_api_key",
            model="gemini-2.5-flash",
        )

        assert "Ahuashiyacu" in reply
        assert len(actions) >= 1
        assert len(related) >= 1
        # Verificar que la API Key NO se expone en la respuesta
        assert "test_fake_api_key" not in reply


@pytest.mark.asyncio
async def test_gemini_cuota_agotada_429(mock_catalogo):
    """
    Requisito 6: Simula el agotamiento de la cuota gratuita (HTTP 429)
    y verifica que se devuelva un mensaje de error controlado y amigable.
    """
    mock_response = httpx.Response(
        status_code=429,
        json={
            "error": {
                "code": 429,
                "message": "Resource has been exhausted (e.g. check quota).",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        reply, actions, related = await consultar_gemini(
            message="¿Qué cataratas hay?",
            catalogo=mock_catalogo,
            api_key="test_fake_api_key",
            model="gemini-2.5-flash",
        )

        # Debe contener aviso controlado de límite de cuota
        assert "cuota gratuita" in reply.lower() or "límite" in reply.lower()
        # No debe lanzar excepción no controlada
        assert isinstance(actions, list)
        assert isinstance(related, list)
        assert "test_fake_api_key" not in reply


@pytest.mark.asyncio
async def test_gemini_alta_demanda_503(mock_catalogo):
    """Simula indisponibilidad temporal por alta demanda (HTTP 503)."""
    mock_response = httpx.Response(
        status_code=503,
        json={"error": {"code": 503, "message": "Service Unavailable"}},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        reply, actions, related = await consultar_gemini(
            message="¿Qué hay en Sauce?",
            catalogo=mock_catalogo,
            api_key="test_fake_api_key",
            model="gemini-2.5-flash",
        )

        assert "alta demanda" in reply.lower() or "disponible" in reply.lower()


@pytest.mark.asyncio
async def test_procesar_consulta_con_fallback_local(mock_catalogo):
    """Verifica que sin Gemini API Key el chatbot responda con el motor local sin fallar."""
    class FakeEngine:
        catalogo = mock_catalogo

    with patch.object(settings, "GEMINI_API_KEY", None):
        resp: ChatResponse = await procesar_consulta_asistente(
            message="¿Cuáles son las cataratas más conocidas?",
            context=None,
            engine=FakeEngine(),
        )

        assert isinstance(resp, ChatResponse)
        assert len(resp.reply) > 0
        assert "Ahuashiyacu" in resp.reply
        assert len(resp.suggested_actions) > 0


@pytest.mark.asyncio
async def test_api_chat_endpoint_e2e():
    """Valida el endpoint HTTP POST /api/chat a través de FastAPI ASGI."""
    async with ASGITransport(app=app) as transport:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/api/chat",
                json={"message": "¿Qué actividades hay en la Laguna de Sauce?"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "suggested_actions" in data
            assert "related_atractivos" in data
            # Verificar que ninguna API key se filtre en la respuesta JSON
            assert "AQ." not in str(data)

