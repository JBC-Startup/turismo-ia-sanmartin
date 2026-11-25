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
    assert settings.GEMINI_MODEL in ("gemini-2.5-flash", "gemini-3.8-flash", "gemini-flash-lite-latest", "gemini-3.5-flash-lite")


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
async def test_prompt_no_trata_imputaciones_como_datos(mock_catalogo):
    mock_response = httpx.Response(
        status_code=200,
        json={"candidates": [{"content": {"parts": [{"text": "No tengo ese dato confirmado."}]}}]},
        request=httpx.Request("POST", "https://example.test"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await consultar_gemini(
            message="¿Cuánto cuesta y cuánto dura la visita a la Catarata de Ahuashiyacu?",
            catalogo=mock_catalogo,
            api_key="fake-key",
            model="gemini-2.5-flash",
        )
    prompt = mock_post.call_args.kwargs["json"]["system_instruction"]["parts"][0]["text"]
    assert "Eres Loro FISI" in prompt
    assert "guía oficial" in prompt
    assert "Costo registrado: no disponible/confirmado" in prompt
    assert "Duración estimada registrada: no disponible/confirmado" in prompt
    assert "Costo aprox: S/ 0.00" not in prompt


@pytest.mark.asyncio
async def test_prompt_incluye_solo_datos_con_fuente_fecha_y_flag(mock_catalogo):
    catalog = mock_catalogo.copy()
    row = catalog["nombre_recurso"].str.contains("Ahuashiyacu", case=False)
    catalog.loc[row, "costo_referencial_pen"] = 12.5
    catalog.loc[row, "duracion_estimada_horas"] = 1.75
    for field in ("costo_referencial_pen", "duracion_estimada_horas"):
        catalog.loc[row, f"{field}_informado"] = True
    catalog.loc[row, "url_fuente"] = "https://example.test/ficha"
    catalog.loc[row, "fecha_verificacion"] = "2025-01-15"
    catalog.loc[row, "codigo_estado"] = 1
    catalog.loc[row, "estado"] = "PUBLICADO"
    response = httpx.Response(
        status_code=200,
        json={"candidates": [{"content": {"parts": [{"text": "Respuesta basada en la ficha."}]}}]},
        request=httpx.Request("POST", "https://example.test"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as mock_post:
        await consultar_gemini(
            message="Cuánto cuesta y cuánto dura la Catarata de Ahuashiyacu",
            catalogo=catalog,
            api_key="fake-key",
            model="gemini-2.5-flash",
        )
    prompt = mock_post.call_args.kwargs["json"]["system_instruction"]["parts"][0]["text"]
    assert "Costo registrado: 12.5 soles" in prompt
    assert "Duración estimada registrada: 1.75h" in prompt
    assert "https://example.test/ficha" in prompt
    assert "2025-01-15" in prompt


@pytest.mark.asyncio
async def test_metadata_gemini_autentico(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo
    mock_response = httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "Respuesta generada"}]}}]}, request=httpx.Request("POST", "https://example.test"))
    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await procesar_consulta_asistente("Consulta", engine=FakeEngine())
    assert result.source == "gemini"
    assert result.model == settings.GEMINI_MODEL
    assert result.fallback_reason is None


@pytest.mark.asyncio
async def test_metadata_fallback_por_cuota(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo
    response = httpx.Response(429, json={"error": {"code": 429}}, request=httpx.Request("POST", "https://example.test"))
    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response):
        result = await procesar_consulta_asistente("Consulta", engine=FakeEngine())
    assert result.source == "local" and result.model is None
    assert result.fallback_reason == "quota_exceeded"


@pytest.mark.asyncio
async def test_metadata_fallback_respuesta_vacia(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo
    response = httpx.Response(200, json={"candidates": []}, request=httpx.Request("POST", "https://example.test"))
    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response):
        result = await procesar_consulta_asistente("Consulta", engine=FakeEngine())
    assert result.source == "local" and result.model is None
    assert result.fallback_reason == "empty_response"


@pytest.mark.asyncio
async def test_metadata_fallback_timeout(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo
    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ReadTimeout("timeout")):
        result = await procesar_consulta_asistente("Consulta", engine=FakeEngine())
    assert result.source == "local" and result.model is None
    assert result.fallback_reason == "timeout"


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

    with patch.object(settings, "GEMINI_API_KEY", None), patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        resp: ChatResponse = await procesar_consulta_asistente(
            message="¿Cuáles son las cataratas más conocidas?",
            context=None,
            engine=FakeEngine(),
        )

        assert isinstance(resp, ChatResponse)
        assert len(resp.reply) > 0
        assert "Ahuashiyacu" in resp.reply
        assert len(resp.suggested_actions) > 0
        assert resp.source == "local"
        assert resp.model is None
        assert resp.fallback_reason == "missing_api_key"


@pytest.mark.asyncio
async def test_saludo_charapa_y_presentacion_sin_consultar_gemini(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        greeting = await procesar_consulta_asistente("Buenas", engine=FakeEngine())
        identity = await procesar_consulta_asistente("¿Quién eres?", engine=FakeEngine())

    mock_post.assert_not_called()
    assert "pe" in greeting.reply.lower()
    assert "Loro FISI" not in greeting.reply
    assert len(greeting.reply) < 100
    assert "mascota virtual" in identity.reply
    assert "oficial" not in identity.reply.lower()
    assert greeting.source == identity.source == "local"
    assert greeting.fallback_reason is identity.fallback_reason is None


@pytest.mark.asyncio
async def test_hola_loro_responde_breve_y_sin_gemini(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        result = await procesar_consulta_asistente("Hola, loro", engine=FakeEngine())

    mock_post.assert_not_called()
    assert result.source == "local"
    assert "hola" in result.reply.lower()
    assert len(result.reply) < 100


@pytest.mark.asyncio
async def test_identidad_loro_fisi(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    result = await procesar_consulta_asistente("¿Quién eres?", engine=FakeEngine())
    assert "Loro FISI" in result.reply
    assert "mascota virtual" in result.reply


@pytest.mark.asyncio
async def test_recomendacion_generica_usa_catalogo(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    result = await procesar_consulta_asistente("Recomiéndame un lugar de San Martín", engine=FakeEngine())
    assert result.related_atractivos
    assert any(item["nombre"] in result.reply for item in result.related_atractivos)


@pytest.mark.asyncio
async def test_pregunta_por_atractivo_recomienda_solo_catalogo(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    with patch.object(settings, "GEMINI_API_KEY", None), patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        result = await procesar_consulta_asistente("¿Qué puedo visitar en Lamas?", engine=FakeEngine())

    assert "Castillo de Lamas" in result.reply
    assert "Ahuashiyacu" not in result.reply
    assert result.related_atractivos[0]["nombre"] == "Castillo de Lamas"


@pytest.mark.asyncio
async def test_precio_no_disponible_no_llama_a_gemini_ni_inventa(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        result = await procesar_consulta_asistente("¿Cuánto cuesta la Catarata de Ahuashiyacu?", engine=FakeEngine())

    mock_post.assert_not_called()
    assert result.source == "local"
    assert result.model is None
    assert result.fallback_reason == "unverified_data_unavailable"
    assert "no tengo un dato confirmado" in result.reply.lower()
    assert "S/" not in result.reply


def test_atractivo_mencionado_tiene_prioridad_sobre_categoria_general(mock_catalogo):
    result = buscar_atractivos_relevantes(
        "¿Cuánto cuesta visitar la Catarata de Ahuashiyacu?",
        catalogo=mock_catalogo,
    )
    assert result[0]["nombre"] == "Catarata de Ahuashiyacu"


@pytest.mark.asyncio
async def test_recomendacion_sin_coincidencias_no_consulta_conocimiento_general():
    class FakeEngine:
        catalogo = pd.DataFrame()

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        result = await procesar_consulta_asistente("Recomiéndame atractivos de una provincia desconocida", engine=FakeEngine())

    mock_post.assert_not_called()
    assert result.source == "local"
    assert result.fallback_reason == "unverified_data_unavailable"
    assert "no recibí registros" in result.reply.lower() or "revisaré" in result.reply.lower()


def test_duracion_faltante_no_se_completa_con_dos_horas(mock_catalogo):
    result = buscar_atractivos_relevantes("Catarata de Ahuashiyacu", catalogo=mock_catalogo)
    assert result[0]["duracion_horas"] is None
    assert result[0]["costo_pen"] is None


def test_cero_ambiguo_no_se_presenta_como_gratis(mock_catalogo):
    catalog = mock_catalogo.copy()
    row = catalog["nombre_recurso"].str.contains("Ahuashiyacu", case=False)
    catalog.loc[row, "costo_referencial_pen"] = 0.0
    catalog.loc[row, "costo_referencial_pen_informado"] = False
    catalog.loc[row, "costo_acceso_libre_informado"] = False
    catalog.loc[row, "url_fuente"] = "https://example.test/ficha"
    catalog.loc[row, "fecha_verificacion"] = "2025-01-15"
    catalog.loc[row, "estado"] = "PUBLICADO"
    result = buscar_atractivos_relevantes("Catarata de Ahuashiyacu", catalogo=catalog)
    assert result[0]["costo_pen"] is None
    assert result[0]["costo_es_acceso_libre"] is False


def _catalogo_con_datos_verificados(catalog):
    verified = catalog.copy()
    row = verified["nombre_recurso"].str.contains("Ahuashiyacu", case=False)
    verified.loc[row, "costo_referencial_pen"] = 12.5
    verified.loc[row, "duracion_estimada_horas"] = 1.75
    for field in ("costo_referencial_pen", "duracion_estimada_horas"):
        verified.loc[row, f"{field}_informado"] = True
    verified.loc[row, "url_fuente"] = "https://example.test/ficha"
    verified.loc[row, "fecha_verificacion"] = "2025-01-15"
    verified.loc[row, "codigo_estado"] = 1
    verified.loc[row, "estado"] = "PUBLICADO"
    return verified


def test_recomendacion_preserva_datos_con_evidencia(mock_catalogo):
    result = buscar_atractivos_relevantes(
        "Catarata de Ahuashiyacu",
        catalogo=_catalogo_con_datos_verificados(mock_catalogo),
    )
    assert result[0]["costo_pen"] == 12.5
    assert result[0]["duracion_horas"] == 1.75
    assert result[0]["fecha_verificacion"] == "2025-01-15"
    assert result[0]["url_fuente"] == "https://example.test/ficha"


@pytest.mark.asyncio
async def test_timeout_no_inventa_y_preserva_metadata_con_dato_fechado(mock_catalogo):
    class FakeEngine:
        catalogo = _catalogo_con_datos_verificados(mock_catalogo)

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ReadTimeout("timeout")):
        result = await procesar_consulta_asistente("¿Cuál es el precio de Ahuashiyacu?", engine=FakeEngine())

    assert result.source == "local"
    assert result.model is None
    assert result.fallback_reason == "timeout"
    assert "S/ 12.5" in result.reply
    assert "2025-01-15" in result.reply


@pytest.mark.asyncio
async def test_timeout_generico_fallback_mantiene_identidad_loro(mock_catalogo):
    class FakeEngine:
        catalogo = mock_catalogo

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"), patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ReadTimeout("timeout")):
        result = await procesar_consulta_asistente("Cuéntame algo de San Martín", engine=FakeEngine())

    assert result.source == "local"
    assert result.model is None
    assert result.fallback_reason == "timeout"
    assert "Loro FISI" in result.reply


@pytest.mark.asyncio
async def test_api_chat_endpoint_e2e():
    """Valida ambos contratos HTTP sin consumir API real."""
    with patch.object(settings, "GEMINI_API_KEY", None), patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        async with ASGITransport(app=app) as transport:
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                for path in ("/api/chat", "/assistant/chat"):
                    resp = await client.post(path, json={"message": "Hola"})
                    assert resp.status_code == 200
                    data = resp.json()
                    assert "reply" in data
                    assert "suggested_actions" in data
                    assert "related_atractivos" in data
                    assert data["source"] == "local"
                    assert data["model"] is None
                    assert data["fallback_reason"] is None
                    assert "AQ." not in str(data)

