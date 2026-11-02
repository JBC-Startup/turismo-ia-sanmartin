from pathlib import Path
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import settings
from tts_service import generar_audio_elevenlabs


@pytest.mark.asyncio
async def test_tts_caching_and_synthesis():
    """Prueba que la síntesis de voz con ElevenLabs genere bytes y utilice caché."""
    texto = "Prueba de síntesis de voz en San Martín."
    mock_audio = b"ID3\x03\x00\x00\x00\x00\x00#simulated_mp3_stream"
    mock_response = httpx.Response(
        status_code=200,
        content=mock_audio,
        request=httpx.Request("POST", "https://api.elevenlabs.io/v1/text-to-speech/test"),
    )

    with patch.object(settings, "ELEVENLABS_API_KEY", "test_elevenlabs_key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # 1. Primera llamada (genera o recupera de caché)
            audio_1 = await generar_audio_elevenlabs(texto)
            assert isinstance(audio_1, bytes)
            assert len(audio_1) > 0

            # 2. Segunda llamada (debe ser instantánea desde la caché local sin re-invocar la API)
            audio_2 = await generar_audio_elevenlabs(texto)
            assert audio_1 == audio_2


@pytest.mark.asyncio
async def test_tts_empty_text_error():
    """Prueba que un texto vacío lance un error ValueError."""
    with pytest.raises(ValueError):
        await generar_audio_elevenlabs("   ")


