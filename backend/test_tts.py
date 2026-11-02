import pytest
from tts_service import generar_audio_elevenlabs


@pytest.mark.asyncio
async def test_tts_caching_and_synthesis():
    """Prueba que la síntesis de voz con ElevenLabs genere bytes y utilice caché."""
    texto = "Prueba de síntesis de voz en San Martín."
    # 1. Primera llamada (genera o recupera de caché)
    audio_1 = await generar_audio_elevenlabs(texto)
    assert isinstance(audio_1, bytes)
    assert len(audio_1) > 0

    # 2. Segunda llamada (debe ser instantánea desde la caché local)
    audio_2 = await generar_audio_elevenlabs(texto)
    assert audio_1 == audio_2


@pytest.mark.asyncio
async def test_tts_empty_text_error():
    """Prueba que un texto vacío lance un error ValueError."""
    with pytest.raises(ValueError):
        await generar_audio_elevenlabs("   ")

