import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ubicación base del proyecto
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
ML_ENGINE_DIR = PROJECT_ROOT / "ml_engine"

# Asegurar que ml_engine esté en sys.path para deserializar TurismoFeaturePipeline y módulos src
if str(ML_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ML_ENGINE_DIR))


class Settings(BaseSettings):
    """
    Configuración global del servicio Backend FastAPI - TurismoIA San Martín.
    Carga variables desde el archivo .env o variables de entorno del sistema.
    """
    # Base de Datos PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:admin123@localhost:5434/turismoia"
    DB_SCHEMA: str = "turismo"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True

    # Modelo Recomendador de Machine Learning
    MODEL_PATH: str = "../ml_engine/models/modelo_recomendador_sanmartin.pkl"

    # API Metadata
    PROJECT_NAME: str = "TurismoIA San Martín API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = False

    # Configuración de Pydantic v2 Settings
    model_config = SettingsConfigDict(
        env_file=(
            BACKEND_DIR / ".env",
            PROJECT_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_resolved_model_path(self) -> Path:
        """
        Resuelve la ruta absoluta del modelo serializado probando varias ubicaciones relativas.
        """
        candidate_paths = [
            Path(self.MODEL_PATH),
            BACKEND_DIR / self.MODEL_PATH,
            PROJECT_ROOT / "ml_engine" / "models" / "modelo_recomendador_sanmartin.pkl",
            ML_ENGINE_DIR / "models" / "modelo_recomendador_sanmartin.pkl",
        ]
        for p in candidate_paths:
            resolved = p.resolve()
            if resolved.exists() and resolved.is_file():
                return resolved

        raise FileNotFoundError(
            f"No se pudo encontrar el artefacto del modelo en ninguna de las rutas: "
            f"{[str(p.resolve()) for p in candidate_paths]}"
        )


settings = Settings()
