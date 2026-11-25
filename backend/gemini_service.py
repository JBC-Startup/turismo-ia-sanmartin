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
from dataclasses import dataclass
import math
import re
from typing import Any, Optional

import httpx
import pandas as pd

from config import settings

logger = logging.getLogger("turismoia.gemini")

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _valor_informado(row: pd.Series, field: str) -> bool:
    """True only when an explicit source-presence flag survived catalog export."""
    value = row.get(f"{field}_informado", False)
    if pd.isna(value):
        return False
    return value is True or str(value).strip().lower() in {"true", "1", "si", "sí"}


def _registro_con_fuente(row: pd.Series) -> bool:
    """Require a published record, source URL and dated verification metadata."""
    source_value = row.get("url_fuente", "")
    date_value = row.get("fecha_verificacion", "")
    state_value = row.get("estado", "")
    source = "" if pd.isna(source_value) else str(source_value).strip()
    verified_at = "" if pd.isna(date_value) else str(date_value).strip()
    state = "" if pd.isna(state_value) else str(state_value).strip().upper()
    try:
        published_code = int(row.get("codigo_estado", 0)) == 1
    except (TypeError, ValueError):
        published_code = False
    published_state = state == "PUBLICADO"
    valid_date = verified_at.lower() not in {"", "nan", "none", "null", "nat", "n/a", "<na>"}
    return bool(source.startswith(("https://", "http://")) and valid_date and (published_code or published_state))


def _valor_numerico_verificable(row: pd.Series, field: str) -> Optional[float]:
    if not _registro_con_fuente(row) or not _valor_informado(row, field):
        return None
    try:
        value = float(row.get(field))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def _texto_verificable(row: pd.Series, field: str) -> Optional[str]:
    if not _registro_con_fuente(row) or not _valor_informado(row, field):
        return None
    value = str(row.get(field, "")).strip()
    normalized = value.lower()
    if not value or normalized in {"nan", "none", "null", "n/a", "na", "<na>"}:
        return None
    if any(marker in normalized for marker in ("sin horario fijo publicado", "no aplica", "consultar calendario", "según programa", "segun programa")):
        return None
    return value


def _descripcion_sin_datos_operativos(row: pd.Series) -> str:
    """Keep descriptive sentences while withholding uncited numeric/practical claims."""
    if not _registro_con_fuente(row):
        return ""
    raw = row.get("descripcion_corta", "")
    if pd.isna(raw):
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", str(raw).strip())
    operational = re.compile(
        r"\d|S/|\bsoles?\b|\bkm\b|kil[oó]metr|\bminut|\bhora|\bhorario|\bruta\b|\bdistancia|"
        r"\bprecio|\bcosto|\btarifa|\btransporte|\bdesde tarapoto|\btiempo de viaje",
        re.IGNORECASE,
    )
    safe = [sentence for sentence in sentences if sentence and not operational.search(sentence)]
    return " ".join(safe)[:200]


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

    context_matches = pd.DataFrame()

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
            context_matches = c_matches

    query_name_stopwords = {
        "quiero", "quisiera", "recomiendame", "recomiend", "visitar", "conocer", "destino", "destinos",
        "atractivo", "atractivos", "lugar", "lugares", "sitio", "sitios", "catarata", "cataratas",
        "cascada", "cascadas", "laguna", "lagunas", "costo", "precio", "cuesta", "horario", "ruta",
        "distancia", "duracion", "cuanto", "demora", "tiempo", "viaje", "como", "llegar", "entrada",
        "tarifa", "dame", "opciones", "mejores", "cerca", "visita",
    }
    name_tokens = [
        word for word in re.findall(r"\w+", msg_lower)
        if len(word) > 3 and word not in query_name_stopwords
    ]
    name_matches = pd.DataFrame()
    if name_tokens:
        name_pattern = "|".join(re.escape(word) for word in name_tokens[:5])
        name_matches = catalogo[catalogo["nombre_recurso"].str.contains(name_pattern, case=False, na=False)]

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

    query_matches = pd.DataFrame()
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
    matches = name_matches if not name_matches.empty else context_matches
    if matches.empty and not query_matches.empty:
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

    if matches.empty:
        return []

    sample_df = matches.head(limit)

    related: list[dict[str, Any]] = []
    for _, row in sample_df.iterrows():
        verified_record = _registro_con_fuente(row)
        related.append({
            "id_recurso": str(row.get("id_recurso", "")),
            "nombre": str(row.get("nombre_recurso", "")),
            "provincia": _texto_verificable(row, "provincia") or "",
            "distrito": _texto_verificable(row, "distrito") or "",
            "duracion_horas": _valor_numerico_verificable(row, "duracion_estimada_horas"),
            "costo_pen": _valor_numerico_verificable(row, "costo_referencial_pen"),
            "costo_es_acceso_libre": (
                _registro_con_fuente(row)
                and _valor_informado(row, "costo_acceso_libre")
            ),
            "distancia_km_tarapoto": _valor_numerico_verificable(row, "distancia_km_tarapoto"),
            "tiempo_viaje_horas_tarapoto": _valor_numerico_verificable(row, "tiempo_viaje_horas_tarapoto"),
            "tiempo_total_tour_horas": _valor_numerico_verificable(row, "tiempo_total_tour_horas"),
            "horario_referencial": _texto_verificable(row, "horario_referencial"),
            "ruta_acceso_desde_tarapoto": _texto_verificable(row, "ruta_acceso_desde_tarapoto"),
            "url_fuente": str(row.get("url_fuente", "")) if verified_record else None,
            "fecha_verificacion": str(row.get("fecha_verificacion", "")) if verified_record else None,
            "dificultad": _texto_verificable(row, "nivel_dificultad"),
            "imagen_url": str(row.get("imagen_url", "")),
            "descripcion": _descripcion_sin_datos_operativos(row),
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
        palabras_interes = ["recomiend", "atractiv", "lugar", "destino", "catarata", "laguna", "visitar", "conocer", "paseo", "tour", "hacer", "costo", "precio", "horario", "ruta", "distancia", "dura", "tiempo"]
        if not any(k in msg_lower for k in palabras_interes):
            return False
    return True


def campos_practicos_solicitados(message: str) -> list[str]:
    """Map a travel-data question to catalog fields that can prove its answer."""
    text = message.lower()
    requested: list[str] = []
    if any(term in text for term in ("precio", "costo", "cuánto cuesta", "cuanto cuesta", "cuánto sale", "cuanto sale", "cuánto vale", "cuanto vale", "tarifa", "entrada", "presupuesto")):
        requested.append("costo_pen")
    if any(term in text for term in ("horario", "a qué hora", "a que hora", "abre", "cierr", "hora de atención", "hora de atencion")):
        requested.append("horario_referencial")
    if any(term in text for term in ("ruta", "cómo llegar", "como llegar", "cómo llego", "como llego", "por dónde", "por donde", "camino", "carretera", "transporte")):
        requested.append("ruta_acceso_desde_tarapoto")
    if any(term in text for term in ("distancia", "cuántos km", "cuantos km", "kilómetro", "kilometro")):
        requested.append("distancia_km_tarapoto")
    if "tiempo de viaje" in text:
        requested.append("tiempo_viaje_horas_tarapoto")
    elif any(term in text for term in ("duración", "duracion", "cuánto demora", "cuanto demora", "cuánto tiempo", "cuanto tiempo", "cuántas horas", "cuantas horas")):
        requested.append("duracion_horas")
    return requested


def _construir_system_prompt(atractivos: list[dict[str, Any]], context: Optional[dict[str, Any] | str]) -> str:
    """Build Loro FISI's persona with catalog fields gated by explicit provenance."""
    prompt = (
        "Eres Loro FISI, la mascota virtual de TurismoIA San Martín: un loro tropical simpático, expresivo, curioso y conversador.\n"
        "PERSONALIDAD: juvenil, divertido y amigable. Habla como un amigo de la selva peruana, especialmente de San Martín, con español peruano cálido y expresiones regionales ocasionales y discretas. Puedes bromear suavemente, sin exagerar el acento ni la jerga.\n"
        "No te presentes como guía oficial, institución, persona real ni operador turístico; no afirmes experiencias personales. No repitas tu nombre en cada respuesta. Responde brevemente a los saludos y evita el tono formal o institucional. Redacta de forma natural para reproducción por voz.\n\n"
        "EVIDENCIA Y SEGURIDAD DE DATOS (prioridad máxima):\n"
        "- Recomienda únicamente atractivos que aparezcan en los registros entregados abajo. No selecciones otros por conocimiento general.\n"
        "- Los campos prácticos se incluyen únicamente si la fuente los registró antes de cualquier imputación, y el registro tiene estado PUBLICADO, URL de fuente y fecha de verificación. Un 0 numérico ambiguo no es dato confirmado ni prueba de acceso libre; solo se indica acceso libre si la fuente lo expresa explícitamente.\n"
        "- Los valores del catálogo son datos registrados en la fecha indicada; no afirmes que estén vigentes hoy ni que consultaste la fuente en vivo. Para precios y condiciones que pueden cambiar, aclara la fecha y recomienda confirmarlos con la fuente antes del viaje.\n"
        "- No calcules ni infieras precios, horarios, rutas, distancias, duración, transporte, disponibilidad ni cantidades a partir de otro campo, del contexto visual o de conocimiento general. No completes huecos con estimaciones.\n"
        "- Si el registro no incluye un dato solicitado, dilo claramente y con calidez: no tienes un dato confirmado en el catálogo. No inventes una respuesta para ser útil.\n"
        "- El contexto visual solo indica qué pantalla mira la persona; no es evidencia turística.\n"
        "ESTILO: contesta saludos de forma breve. En preguntas de viaje, responde primero a lo pedido en uno o dos párrafos concisos y naturales para voz. Mantén contexto de la conversación sin tratar afirmaciones previas tuyas como evidencia.\n"
        "Cierra con exactamente 3 preguntas sugeridas breves usando este formato:\n"
        "---SUGERENCIAS---\n"
        "- ¿Pregunta sugerida 1?\n"
        "- ¿Pregunta sugerida 2?\n"
        "- ¿Pregunta sugerida 3?\n"
    )

    context_name = None
    context_prov = "San Martín"
    if isinstance(context, dict):
        context_name = context.get("name") or context.get("nombre") or context.get("title") or context.get("destination") or context.get("atractivo")
        context_prov = context.get("province") or context.get("provincia") or "San Martín"
    elif isinstance(context, str) and context.strip():
        context_name = context.strip()

    if context_name:
        prompt += f"\nContexto visual, no evidencia: la persona está viendo '{context_name}' (provincia indicada: {context_prov}).\n"

    if atractivos:
        prompt += "\nRegistros de catálogo entregados para esta consulta. Usa solo los campos disponibles; null significa dato no confirmado:\n"
        for a in atractivos:
            prompt += f"- {a['nombre']} ({a['provincia']} - {a['distrito']}). Descripción registrada: {a['descripcion']}\n"
            values = (
                ("Duración estimada registrada", a.get("duracion_horas"), "h"),
                ("Distancia desde Tarapoto registrada", a.get("distancia_km_tarapoto"), " km"),
                ("Tiempo de viaje registrado", a.get("tiempo_viaje_horas_tarapoto"), " h"),
                ("Duración total de tour registrada", a.get("tiempo_total_tour_horas"), " h"),
            )
            for label, value, unit in values:
                prompt += f"  {label}: {value}{unit}.\n" if value is not None else f"  {label}: no disponible/confirmado.\n"
            if a.get("costo_es_acceso_libre"):
                prompt += "  Costo registrado: la ficha indica acceso libre.\n"
            elif a.get("costo_pen") is not None:
                prompt += f"  Costo registrado: {a['costo_pen']} soles.\n"
            else:
                prompt += "  Costo registrado: no disponible/confirmado.\n"
            for label, key in (("Horario referencial", "horario_referencial"), ("Ruta registrada", "ruta_acceso_desde_tarapoto")):
                value = a.get(key)
                prompt += f"  {label}: {value}.\n" if value else f"  {label}: no disponible/confirmado.\n"
            if a.get("fecha_verificacion") and a.get("url_fuente"):
                prompt += f"  Fuente de ficha: {a['url_fuente']}; fecha de verificación: {a['fecha_verificacion']}.\n"
            if a.get("dificultad"):
                prompt += f"  Dificultad registrada: {a['dificultad']}.\n"
    else:
        prompt += "\nNo se encontraron registros coincidentes en el catálogo para esta consulta. No inventes ni enumeres atractivos.\n"

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
            if stripped:
                sug = re.sub(r"^[-*0-9.]+\s*", "", stripped).strip()
                if 5 < len(sug) < 120 and (stripped.startswith(("- ", "* ")) or re.match(r"^\d+\.\s+", stripped) or sug.endswith("?")):
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


@dataclass
class ResultadoGeneracion:
    reply: str
    suggested_actions: list[str]
    related_atractivos: list[dict[str, Any]]
    source: str
    model: Optional[str] = None
    fallback_reason: Optional[str] = None


async def consultar_gemini_resultado(
    message: str,
    context: Optional[dict[str, Any] | str] = None,
    catalogo: Optional[pd.DataFrame] = None,
    session_id: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    history: Optional[list[dict[str, str]]] = None,
) -> ResultadoGeneracion:
    """
    Envía una consulta a Google Gemini API utilizando el nivel gratuito (Free Tier).

    Manejo de estados y errores:
    - 200 OK: Respuesta exitosa formateada.
    - 429: Cuota gratuita agotada (Resource Exhausted) -> Error controlado amigable.
    - 503: Servicio no disponible / Alta demanda temporal -> Error controlado.
    - 404: Modelo no disponible (ej. deprecado para usuarios nuevos) -> Notificación o fallback controlado.
    - Otros: Mensaje controlado sin filtrar datos confidenciales ni API keys.
    """
    key = api_key or getattr(settings, "effective_gemini_api_key", settings.GEMINI_API_KEY) or settings.GEMINI_API_KEY
    if not key or not key.strip() or key.startswith("tu_gemini_api_key"):
        raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")

    modelo_solicitado = model or settings.GEMINI_MODEL or "gemini-3.8-flash"
    timeout = timeout_seconds or getattr(settings, "GEMINI_TIMEOUT_SECONDS", 20.0)

    # 1. Recuperar atractivos relevantes del catálogo oficial
    atractivos_rel = buscar_atractivos_relevantes(message, context=context, catalogo=catalogo, limit=4)
    atractivos_salida = atractivos_rel if es_consulta_de_atractivos(message) else []
    system_instruction = _construir_system_prompt(atractivos_rel, context)

    default_actions = [
        "¿Qué atractivos aparecen en el catálogo?",
        "¿Qué provincia de San Martín te interesa?",
        "¿Qué tipo de experiencia estás buscando?",
    ]

    # 2. Construir historial de conversación interactiva
    contents: list[dict[str, Any]] = []

    if history:
        for turn in history[-6:]:
            role = "user" if turn.get("role") == "user" else "model"
            text_val = str(turn.get("content") or turn.get("text") or "").strip()
            if text_val:
                contents.append({
                    "role": role,
                    "parts": [{"text": text_val}],
                })
    else:
        historial_previo = obtener_historial_sesion(session_id, limit=6)
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
                            return ResultadoGeneracion(texto_limpio, actions, atractivos_salida, "gemini", current_model)

                    # Respuesta vacía de candidatos
                    reply_text = (
                        "🌴 He recibido tu consulta sobre San Martín, pero no se generó una respuesta detallada. "
                        "Por favor reformula tu pregunta o elige una de las opciones sugeridas."
                    )
                    return ResultadoGeneracion(reply_text, default_actions, atractivos_salida, "local", None, "empty_response")

                # Caso 2: Cuota agotada (HTTP 429 - Too Many Requests / Resource Exhausted)
                if response.status_code == 429:
                    logger.warning("Cuota gratuita de Gemini API superada (HTTP 429).")
                    reply_cuota = (
                        "⚠️ **Límite de cuota gratuita alcanzado temporalmente**\n\n"
                        "Se ha superado el límite de solicitudes por minuto permitido por el nivel gratuito (Free Tier) "
                        "de Google Gemini API. Por favor, espera unos momentos antes de realizar una nueva consulta.\n\n"
                        "Mientras tanto, puedes revisar los atractivos recomendados a continuación."
                    )
                    return ResultadoGeneracion(reply_cuota, [
                        "¿Cuáles son las cataratas más visitadas?",
                        "¿Cómo llegar a Sauce?",
                        "¿Dónde comer comida típica?",
                    ], atractivos_salida, "local", None, "quota_exceeded")

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
                    return ResultadoGeneracion(reply_auth, default_actions, atractivos_salida, "local", None, "authentication_error")

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
            return ResultadoGeneracion(reply_503, default_actions, atractivos_salida, "local", None, "service_unavailable")

        raise RuntimeError(f"Gemini API no devolvió una respuesta válida (código: {last_error_code}).")


async def consultar_gemini(
    message: str,
    context: Optional[dict[str, Any] | str] = None,
    catalogo: Optional[pd.DataFrame] = None,
    session_id: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    history: Optional[list[dict[str, str]]] = None,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """Wrapper retrocompatible; los consumidores nuevos usan el resultado con metadata."""
    result = await consultar_gemini_resultado(message, context, catalogo, session_id, api_key, model, timeout_seconds, history)
    return result.reply, result.suggested_actions, result.related_atractivos

