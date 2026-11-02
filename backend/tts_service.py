import hashlib
import logging
from pathlib import Path
from typing import Optional

import httpx

try:
    from config import settings
except ImportError:
    from backend.config import settings

logger = logging.getLogger("turismoia.tts")

# Directorio de caché local para optimizar peticiones y proteger la cuota de ElevenLabs
TTS_CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "tts"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def generar_audio_elevenlabs(texto: str, voice_id: Optional[str] = None) -> bytes:
    """
    Sintetiza texto en audio MP3 de alta fidelidad humana utilizando la API de ElevenLabs.
    
    Implementa caché en disco basado en SHA-256 para:
    1. Reducir latencia a < 5ms en frases frecuentes (bienvenidas, destinos).
    2. Proteger la cuota de caracteres de ElevenLabs.
    3. Asegurar alta disponibilidad.
    """
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY no está configurada en el backend.")

    effective_voice_id = voice_id or settings.ELEVENLABS_VOICE_ID or "TX3LPaxmHKxFdv7VOQHJ"
    model_id = settings.ELEVENLABS_MODEL_ID or "eleven_multilingual_v2"

    # Limpiar y normalizar el texto para el caché
    clean_text = texto.strip()
    if not clean_text:
        raise ValueError("El texto para la síntesis de voz no puede estar vacío.")

    # Generar hash único para caché
    cache_key = hashlib.sha256(f"{effective_voice_id}:{model_id}:{clean_text}".encode("utf-8")).hexdigest()
    cache_file = TTS_CACHE_DIR / f"{cache_key}.mp3"

    if cache_file.exists() and cache_file.stat().st_size > 0:
        logger.info("Retornando audio TTS desde caché local (%s - %d bytes)", cache_key[:8], cache_file.stat().st_size)
        return cache_file.read_bytes()

    # Petición a ElevenLabs
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{effective_voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": clean_text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.15,
            "use_speaker_boost": True,
        },
    }

    logger.info("Llamando a ElevenLabs TTS (Voice: %s, Caracteres: %d)...", effective_voice_id, len(clean_text))

    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_msg = f"Error ElevenLabs API ({response.status_code}): {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        audio_bytes = response.content
        if not audio_bytes:
            raise RuntimeError("ElevenLabs retornó una respuesta de audio vacía.")

        # Guardar en caché para futuras reproducciones
        try:
            cache_file.write_bytes(audio_bytes)
            logger.info("Audio TTS guardado en caché local (%s - %d bytes)", cache_key[:8], len(audio_bytes))
        except Exception as cache_err:
            logger.warning("No se pudo escribir en la caché TTS: %s", cache_err)

        return audio_bytes
