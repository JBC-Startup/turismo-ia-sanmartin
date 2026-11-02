"""
Módulo de Integración con Google Gemini API (Free Tier)
=======================================================
Proporciona el motor conversacional inteligente para el Chatbot Guía Turístico
de la Región San Martín, Perú.

Seguridad y Buenas Prácticas:
- La API Key se lee exclusivamente desde la variable de entorno GEMINI_API_KEY.
- La API Key se envía en headers HTTP ('x-goog-api-key'), nunca en la URL.
- No se expone la API Key en logs, respuestas de error ni frontend.
- Manejo explícito y controlado de agotamiento de cuota gratuita (HTTP 429).
- Fallback automático y resiliente ante indisponibilidad de red o alta demanda (HTTP 503).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

import httpx
import pandas as pd

from config import settings

logger = logging.getLogger("turismoia.gemini")

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def buscar_atractivos_relevantes(
    query: str,
    context: Optional[dict[str, Any] | str] = None,
    catalogo: Optional[pd.DataFrame] = None,
    limit: int = 4,
) -> list[dict[str, Any]]:
    """
    Extrae los atractivos turísticos más relevantes del catálogo de San Martín
    según la consulta del usuario y el contexto visual activo.
    """
    if catalogo is None or catalogo.empty:
        return []

    msg_lower = query.lower().strip()
    context_name = None
    if isinstance(context, dict):
        context_name = (
            context.get("name")
            or context.get("nombre")
            or context.get("title")
            or context.get("destination")
            or context.get("atractivo")
        )
    elif isinstance(context, str):
        context_name = context

    matches = pd.DataFrame()

    # 1. Coincidencia por contexto activo (ej. "Laguna de Sauce")
    if context_name:
        c_clean = str(context_name).strip().upper()
        # Buscar coincidencias por nombre o por palabras clave del destino activo (ej. "SAUCE")
        words_context = [w for w in re.findall(r"\w+", c_clean) if len(w) > 3]
        pattern_context = "|".join(words_context) if words_context else c_clean
        c_matches = catalogo[
            catalogo["nombre_recurso"].str.contains(pattern_context, case=False, na=False)
            | catalogo["distrito"].str.contains(pattern_context, case=False, na=False)
        ]
        if not c_matches.empty:
            matches = c_matches

    # 2. Coincidencia por términos clave de la consulta
    terms: list[str] = []
    term_map = {
        ("catarata", "cascada", "caida", "ahuashiyacu", "huacamaillo", "carpishuyacu", "torre", "pucayaquillo"): ["CATARATA", "CASCADA", "CAIDAS DE AGUA"],
        ("laguna", "sauce", "azul", "lago", "ricuricocha"): ["LAGUNA", "LAGO", "SAUCE"],
        ("cueva", "gruta", "palestina", "huacharos"): ["CUEVA", "GRUTA", "PALESTINA"],
        ("cultura", "museo", "templo", "castillo", "wayku", "kichwa", "artesania"): ["CULTURAL", "CASTILLO", "MUSEO", "WAYKU"],
        ("tarapoto", "san martin", "morales", "banda"): ["TARAPOTO", "SAN MARTIN"],
        ("lamas", "chazuta"): ["LAMAS", "CHAZUTA"],
        ("moyobamba", "orquidea", "orquideas", "banos termales", "san mateo"): ["MOYOBAMBA", "ORQUIDEAS", "SAN MATEO"],
        ("rioja", "naciente", "tio yacu", "tío yacu", "yacu"): ["RIOJA", "TIO YACU", "NACIENTE"],
        ("comida", "gastronomia", "comer", "juane", "tacacho", "cecina"): ["GASTRONOMIA", "TRADICIONAL"],
        ("tocache", "bellavista", "mariscal", "picota"): ["TOCACHE", "BELLAVISTA", "PICOTA"],
    }

    for keywords, patterns in term_map.items():
        if any(k in msg_lower for k in keywords):
            terms.extend(patterns)

    if terms:
        pattern = "|".join(terms)
        query_matches = catalogo[
            catalogo["nombre_recurso"].str.contains(pattern, case=False, na=False)
            | catalogo["categoria"].str.contains(pattern, case=False, na=False)
            | catalogo["tipo"].str.contains(pattern, case=False, na=False)
            | catalogo["etiquetas_interes"].str.contains(pattern, case=False, na=False)
            | catalogo["provincia"].str.contains(pattern, case=False, na=False)
            | catalogo["distrito"].str.contains(pattern, case=False, na=False)
        ]
        if not query_matches.empty:
            matches = query_matches

    # 3. Si aún no hay coincidencias directas, buscar palabras significativas del mensaje (> 3 letras)
    if matches.empty:
        words = [w for w in re.findall(r"\w+", msg_lower) if len(w) > 3 and w not in ("hola", "buenos", "dias", "tardes", "noches", "quiero", "saber")]
        if words:
            pattern = "|".join(words[:3])
            try:
                matches = catalogo[
                    catalogo["nombre_recurso"].str.contains(pattern, case=False, na=False)
                    | catalogo["etiquetas_interes"].str.contains(pattern, case=False, na=False)
                ]
            except Exception:
                matches = pd.DataFrame()

    # 4. Fallback de selección estelar: Si no hubo coincidencia (ej. "Hola"),
    # mostrar las joyas turísticas más icónicas de San Martín en vez de los primeros registros al azar
    if matches.empty:
        iconos = ["AHUASHIYACU", "SAUCE", "CASTILLO DE LAMAS", "TIO YACU", "SAN MATEO"]
        pattern_iconos = "|".join(iconos)
        sample_df = catalogo[catalogo["nombre_recurso"].str.contains(pattern_iconos, case=False, na=False)].head(limit)
        if sample_df.empty:
            sample_df = catalogo.head(limit)
    else:
        sample_df = matches.head(limit)

    related: list[dict[str, Any]] = []
    for _, row in sample_df.iterrows():
        related.append({
            "id_recurso": str(row.get("id_recurso", "")),
            "nombre": str(row.get("nombre_recurso", "")),
            "provincia": str(row.get("provincia", "")),
            "distrito": str(row.get("distrito", "")),
            "duracion_horas": float(row.get("duracion_estimada_horas", 2.0)),
            "costo_pen": float(row.get("costo_referencial_pen", 0.0)),
            "dificultad": str(row.get("nivel_dificultad", "Media")),
            "imagen_url": str(row.get("imagen_url", "")),
            "descripcion": str(row.get("descripcion_corta", ""))[:200] + "...",
        })

    return related


# Cliente HTTP persistente para reutilización de conexiones TLS (baja latencia)
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None


def _get_http_client(timeout: float = 12.0) -> httpx.AsyncClient:
    """Retorna un cliente HTTP persistente con keep-alive para respuestas ultra-rápidas."""
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None or _HTTP_CLIENT.is_closed:
        _HTTP_CLIENT = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=3.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
    return _HTTP_CLIENT


# Historial conversacional en memoria indexado por session_id
HISTORIAL_SESIONES: dict[str, list[dict[str, str]]] = {}


def obtener_historial_sesion(session_id: Optional[str], limit: int = 6) -> list[dict[str, str]]:
    """Obtiene los últimos turnos de diálogo de la sesión."""
    if not session_id or session_id not in HISTORIAL_SESIONES:
        return []
    return HISTORIAL_SESIONES[session_id][-limit:]


def registrar_en_historial(session_id: Optional[str], user_text: str, bot_text: str) -> None:
    """Registra el intercambio en la memoria de la sesión."""
    if not session_id:
        return
    if session_id not in HISTORIAL_SESIONES:
        HISTORIAL_SESIONES[session_id] = []
    HISTORIAL_SESIONES[session_id].append({"role": "user", "text": user_text})
    HISTORIAL_SESIONES[session_id].append({"role": "model", "text": bot_text})
    if len(HISTORIAL_SESIONES[session_id]) > 12:
        HISTORIAL_SESIONES[session_id] = HISTORIAL_SESIONES[session_id][-12:]


def es_consulta_de_atractivos(message: str) -> bool:
    """
    Determina si la consulta amerita adjuntar tarjetas de atractivos recomendados.
    Evita inundar el chat con tarjetas cuando el usuario solo saluda o se presenta.
    """
    msg_lower = message.lower().strip()
    saludos_o_presentacion = [
        "hola", "buenos dias", "buenos días", "buenas tardes", "buenas noches",
        "que tal", "qué tal", "como estas", "cómo estás", "como te va", "cómo te va",
        "mi nombre", "me llamo", "soy ", "gracias", "chau", "adios", "adiós"
    ]
    if any(msg_lower.startswith(w) for w in saludos_o_presentacion):
        palabras_interes = ["recomiend", "atractiv", "lugar", "destino", "catarata", "laguna", "visitar", "conocer", "paseo", "tour", "hacer", "costo", "precio"]
        if not any(k in msg_lower for k in palabras_interes):
            return False
    return True


def _construir_system_prompt(atractivos: list[dict[str, Any]], context: Optional[dict[str, Any] | str]) -> str:
    """Construye las instrucciones de personalidad y razonamiento para el LLM."""
    prompt = (
        "Eres el Asistente Guía Turístico Inteligente oficial de la Región San Martín, Perú.\n"
        "Tu misión es razonar dinámicamente cada interacción, ofreciendo recomendaciones auténticas, útiles y personalizadas.\n\n"
        "DIRECTRICES OBLIGATORIAS:\n"
        "1. RESPUESTA DIRECTA Y PRECISA: Analiza y responde exactamente a lo que el turista pregunta. "
        "Si te dice su nombre o saluda, responde amablemente llamándolo por su nombre de forma concisa. "
        "Si pregunta un costo, ruta, horario o recomendación, da primero ese dato concreto sin rodeos.\n"
        "2. CONCISO Y ÁGIL: 1 a 2 párrafos bien estructurados con Markdown. Evita párrafos largos o listas infinitas a menos que se te soliciten.\n"
        "3. LENGUAJE NATURAL Y CÁLIDO: Conversa como un guía local experto y amigable de la selva peruana (no como un bot rígido).\n"
        "4. MEMORIA E ITERACIÓN: Mantén el contexto de los mensajes anteriores en la conversación.\n"
        "5. SECCIÓN DE PREGUNTAS SUGERIDAS (OBLIGATORIO AL FINAL):\n"
        "Al final de tu respuesta, añade SIEMPRE una sección con exactamente 3 preguntas sugeridas breves y dinámicas con este formato exacto:\n"
        "---SUGERENCIAS---\n"
        "- ¿Pregunta sugerida 1?\n"
        "- ¿Pregunta sugerida 2?\n"
        "- ¿Pregunta sugerida 3?\n\n"
        "Base de Conocimiento de la Región San Martín:\n"
        "- Provincias clave: San Martín (Tarapoto), Lamas, Moyobamba (Ciudad de las Orquídeas), Rioja, Mariscal Cáceres, Tocache, etc.\n"
        "- Atractivos ícono: Catarata de Ahuashiyacu, Laguna Azul (Sauce), Castillo de Lamas, Baños Termales de San Mateo, Naciente de Tío Yacu, Cueva de Palestina.\n"
        "- Gastronomía: Juane de gallina, Tacacho con cecina y chorizo, Patarashca, café y cacao amazónico.\n"
        "- Datos prácticos: Moneda Soles (PEN), clima cálido tropical, uso de repelente ecológico y ropa ligera.\n"
    )

    context_name = None
    context_prov = "San Martín"
    if isinstance(context, dict):
        context_name = context.get("name") or context.get("nombre") or context.get("title")
        context_prov = context.get("province") or context.get("provincia") or "San Martín"
    elif isinstance(context, str) and context.strip():
        context_name = context.strip()

    if context_name:
        prompt += f"\nContexto visual de la pantalla: El turista está explorando '{context_name}' (Provincia: {context_prov}).\n"

    if atractivos:
        prompt += "\nAtractivos oficiales de San Martín verificados para enriquecer tu respuesta si es relevante:\n"
        for a in atractivos:
            prompt += (
                f"- {a['nombre']} ({a['provincia']} - {a['distrito']}, "
                f"Duración: {a['duracion_horas']}h, Costo aprox: S/ {a['costo_pen']:.2f}, "
                f"Dificultad: {a['dificultad']}): {a['descripcion']}\n"
            )

    return prompt


def _extraer_suggested_actions(gemini_text: str, default_actions: list[str]) -> tuple[str, list[str]]:
    """
    Separa el texto de la respuesta principal y las preguntas sugeridas dinámicas.
    Retorna (texto_limpio, lista_de_sugerencias).
    """
    actions: list[str] = []
    texto_limpio = gemini_text

    # Si contiene el delimitador ---SUGERENCIAS---
    if "---SUGERENCIAS---" in gemini_text:
        partes = gemini_text.split("---SUGERENCIAS---", 1)
        texto_limpio = partes[0].strip()
        lineas_sug = partes[1].strip().splitlines()
        for line in lineas_sug:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "1. ", "2. ", "3. ")):
                sug = re.sub(r"^[-*0-9.]+\s*", "", stripped).strip()
                if 5 < len(sug) < 120:
                    actions.append(sug)
    else:
        # Fallback de extracción de viñetas interrogativas al final
        lines = gemini_text.splitlines()
        clean_lines = []
        found_suggestions = False
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("- ") or stripped.startswith("* ") or re.match(r"^\d+\.\s+", stripped)) and stripped.endswith("?"):
                found_suggestions = True
                sug = re.sub(r"^[-*0-9.]+\s*", "", stripped).strip()
                if 5 < len(sug) < 120:
                    actions.append(sug)
            elif not found_suggestions:
                clean_lines.append(line)
        if actions:
            texto_limpio = "\n".join(clean_lines).strip()

    if not actions:
        actions = default_actions[:3]
    return texto_limpio, actions[:3]


async def consultar_gemini(
    message: str,
    context: Optional[dict[str, Any] | str] = None,
    catalogo: Optional[pd.DataFrame] = None,
    session_id: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """
    Envía una consulta a Google Gemini API utilizando el nivel gratuito (Free Tier).

    Manejo de estados y errores:
    - 200 OK: Respuesta exitosa formateada.
    - 429: Cuota gratuita agotada (Resource Exhausted) -> Error controlado amigable.
    - 503: Servicio no disponible / Alta demanda temporal -> Error controlado.
    - 404: Modelo no disponible (ej. deprecado para usuarios nuevos) -> Notificación o fallback controlado.
    - Otros: Mensaje controlado sin filtrar datos confidenciales ni API keys.
    """
    key = api_key or settings.GEMINI_API_KEY
    if not key or key.strip() == "" or key.startswith("tu_gemini_api_key"):
        raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")

    modelo_solicitado = model or settings.GEMINI_MODEL or "gemini-3.8-flash"
    timeout = timeout_seconds or getattr(settings, "GEMINI_TIMEOUT_SECONDS", 20.0)

    # 1. Recuperar atractivos relevantes del catálogo oficial
    atractivos_rel = buscar_atractivos_relevantes(message, context=context, catalogo=catalogo, limit=4)
    atractivos_salida = atractivos_rel if es_consulta_de_atractivos(message) else []
    system_instruction = _construir_system_prompt(atractivos_rel, context)

    default_actions = [
        "¿Cuáles son las mejores cataratas cerca de Tarapoto?",
        "¿Qué actividades puedo hacer en la Laguna de Sauce?",
        "¿Qué opciones culturales y artesanales hay en Lamas?",
        "¿Dónde degustar la mejor gastronomía típica de la región?",
    ]

    # 2. Construir historial de conversación interactiva
    historial_previo = obtener_historial_sesion(session_id, limit=6)
    contents: list[dict[str, Any]] = []

    for turn in historial_previo:
        contents.append({
            "role": turn["role"],
            "parts": [{"text": turn["text"]}],
        })

    contents.append({
        "role": "user",
        "parts": [{"text": message}],
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 380,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key,  # Enviado en header HTTP por seguridad
    }

    # Lista priorizada de modelos rápidos para asegurar respuesta continua en Free Tier
    modelos_a_probar = [modelo_solicitado]
    for alt in ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-flash-latest"]:
        if alt not in modelos_a_probar:
            modelos_a_probar.append(alt)

    async with httpx.AsyncClient(timeout=timeout) as client:
        last_error_code = None
        last_error_message = ""

        for current_model in modelos_a_probar:
            current_url = f"{GEMINI_API_BASE_URL}/{current_model}:generateContent"
            try:
                response = await client.post(current_url, headers=headers, json=payload)

                # Fallback de compatibilidad si el modelo no soporta system_instruction (HTTP 400)
                if response.status_code == 400 and "system_instruction" in payload:
                    fallback_contents = list(contents)
                    fallback_contents[-1] = {
                        "role": "user",
                        "parts": [{"text": f"{system_instruction}\n\nMensaje del turista: {message}"}],
                    }
                    fallback_payload = {
                        "contents": fallback_contents,
                        "generationConfig": payload["generationConfig"],
                    }
                    response = await client.post(current_url, headers=headers, json=fallback_payload)

                # Caso 1: Éxito (200 OK)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if "text" in p]
                        reply_text = "\n".join(text_parts).strip()
                        if reply_text:
                            texto_limpio, actions = _extraer_suggested_actions(reply_text, default_actions)
                            registrar_en_historial(session_id, message, texto_limpio)
                            return texto_limpio, actions, atractivos_salida

                    # Respuesta vacía de candidatos
                    reply_text = (
                        "🌴 He recibido tu consulta sobre San Martín, pero no se generó una respuesta detallada. "
                        "Por favor reformula tu pregunta o elige una de las opciones sugeridas."
                    )
                    return reply_text, default_actions, atractivos_salida

                # Caso 2: Cuota agotada (HTTP 429 - Too Many Requests / Resource Exhausted)
                if response.status_code == 429:
                    logger.warning("Cuota gratuita de Gemini API superada (HTTP 429).")
                    reply_cuota = (
                        "⚠️ **Límite de cuota gratuita alcanzado temporalmente**\n\n"
                        "Se ha superado el límite de solicitudes por minuto permitido por el nivel gratuito (Free Tier) "
                        "de Google Gemini API. Por favor, espera unos momentos antes de realizar una nueva consulta.\n\n"
                        "Mientras tanto, puedes revisar los atractivos recomendados a continuación."
                    )
                    return reply_cuota, [
                        "¿Cuáles son las cataratas más visitadas?",
                        "¿Cómo llegar a Sauce?",
                        "¿Dónde comer comida típica?",
                    ], atractivos_salida

                # Caso 3: Alta demanda o indisponibilidad temporal (HTTP 503) -> Probar siguiente modelo
                if response.status_code == 503:
                    logger.warning("Modelo %s con alta demanda (HTTP 503), probando modelo alternativo...", current_model)
                    last_error_code = 503
                    continue

                # Caso 4: Modelo no disponible (HTTP 404) -> Probar siguiente modelo
                if response.status_code == 404:
                    err_json = response.json().get("error", {})
                    err_msg = err_json.get("message", "")
                    logger.info("Modelo %s no disponible (404), probando alternativa rápida...", current_model)
                    last_error_code = 404
                    last_error_message = err_msg
                    continue

                # Caso 5: Error de autenticación (HTTP 401 / 403)
                if response.status_code in (401, 403):
                    logger.error("Error de autenticación con Gemini API: código %d.", response.status_code)
                    reply_auth = (
                        "🔒 **Error de configuración de Gemini API**\n\n"
                        "La API Key de Gemini configurada no es válida o no tiene permisos para el nivel gratuito. "
                        "Verifica la variable GEMINI_API_KEY en tu archivo `.env`."
                    )
                    return reply_auth, default_actions, atractivos_salida

                # Otros códigos HTTP no previstos
                logger.error("Gemini API respondió con código inesperado %d", response.status_code)
                last_error_code = response.status_code

            except httpx.TimeoutException:
                logger.warning("Timeout al conectar con Gemini API tras %.1f segundos.", timeout)
                raise TimeoutError("Tiempo de espera agotado al conectar con Gemini API")

            except Exception as exc:
                logger.warning("Fallo al conectar con Gemini API (%s).", exc)
                raise

        # Si llegó aquí sin respuesta 200 ni 429:
        if last_error_code == 503:
            reply_503 = (
                "⏳ **Servicio con alta demanda temporal**\n\n"
                "Los servidores de Gemini están experimentando alta demanda en este momento. "
                "Por favor, intenta de nuevo en unos instantes.\n\n"
                "Mientras tanto, puedes revisar los siguientes atractivos recomendados:"
            )
            return reply_503, default_actions, atractivos_salida

        raise RuntimeError(f"Gemini API no devolvió una respuesta válida (código: {last_error_code}).")


async def transcribir_audio_gemini(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Transcribe audio de voz a texto en español utilizando Google Gemini API multimodal.
    Universalmente compatible con grabaciones directas del navegador (.webm, .wav, .ogg, .mp3).
    """
    import base64

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY no está configurada en el backend.")

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    clean_mime = mime_type.split(";")[0].strip() if mime_type else "audio/webm"

    url = f"{GEMINI_API_BASE_URL}/gemini-flash-lite-latest:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Transcribe fielmente lo que se dice en este audio en español. "
                            "Devuelve única y exclusivamente el texto transcrito en texto plano. "
                            "No agregues comillas, ni explicaciones, ni formato Markdown. "
                            "Si el audio es inaudible o contiene solo ruido de fondo, responde exactamente: VACIO"
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": clean_mime,
                            "data": audio_b64,
                        }
                    },
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.warning("Gemini multimodal audio (%d): %s", response.status_code, response.text[:200])
            return ""

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""

        transcribed = parts[0].get("text", "").strip()
        if transcribed.upper() == "VACIO" or transcribed.upper() == "VACÍO":
            return ""

        return transcribed.strip('"\'')


