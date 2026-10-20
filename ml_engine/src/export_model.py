#!/usr/bin/env python3
"""
Módulo de Empaquetado y Exportación Final - TurismoIA San Martín
===============================================================
Fase 6 del Pipeline de ML: Serialización del artefacto autónomo de inferencia.

Construye 'models/modelo_recomendador_sanmartin.pkl' conteniendo en una sola
estructura todos los elementos necesarios para producción y API (FastAPI):
- Pipeline de características ajustado (TF-IDF, OneHotEncoder, MinMaxScaler).
- Modelo K-Means entrenado con centroides y metadatos de clusters.
- Matriz precalculada X_global (SciPy CSR).
- Catálogo enriquecido con clusters y metadatos clave para frontend.
- Versión semántica y timestamp de generación.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
import scipy.sparse as sp
from sklearn.cluster import KMeans

from src.feature_engineering import TurismoFeaturePipeline

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Metadatos de negocio de los clusters
CLUSTER_METADATA: dict[int, dict[str, str]] = {
    0: {
        "label": "Centros Urbanos, Lagunas y Paisajes en San Martín (Tarapoto)",
        "descripcion": (
            "Atractivos en el corredor central de Tarapoto y alrededores: lagunas, miradores "
            "panorámicos, centros culturales y paseos urbanos."
        ),
    },
    1: {
        "label": "Patrimonio Cultural, Historia, Tradiciones y Plazas Urbanas",
        "descripcion": (
            "Rutas de identidad amazónica, centros históricos, iglesias coloniales, talleres "
            "artesanales, ferias y festividades patronales (Moyobamba, Rioja y Lamas)."
        ),
    },
    2: {
        "label": "Aventura, Espeleología (Grutas y Cuevas) y Senderos de Selva Alta",
        "descripcion": (
            "Excursiones de mayor duración y exigencia física: cavidades naturales, cavernas, "
            "grutas subterráneas y cerros para senderismo activo."
        ),
    },
    3: {
        "label": "Ecoturismo de Selva, Cascadas Emblemáticas y Caídas de Agua",
        "descripcion": (
            "Circuitos de naturaleza y caídas de agua emblemáticas en Tocache, Lamas y Rioja, "
            "ideales para fotografía, baño natural y observación de biodiversidad."
        ),
    },
}

# Columnas seleccionadas para el catálogo de producción
CATALOGO_COLUMNS = [
    "id_recurso",
    "nombre_recurso",
    "categoria",
    "tipo",
    "subtipo",
    "provincia",
    "distrito",
    "latitud",
    "longitud",
    "duracion_estimada_horas",
    "costo_referencial_pen",
    "nivel_dificultad",
    "publico_recomendado",
    "cluster_id",
    "descripcion_corta",
    "imagen_url",
    "etiquetas_interes",
    "horario_referencial",
    "temporada_ideal",
    "ruta_acceso_desde_tarapoto",
    "referencia_ubicacion",
    "url_fuente",
]


def export_production_model(
    catalog_path: str | Path = "data/processed/dataset_con_clusters.csv",
    matrix_path: str | Path = "data/processed/X_global.npz",
    pipeline_path: str | Path = "models/feature_pipeline.pkl",
    kmeans_path: str | Path = "models/kmeans_model.pkl",
    output_path: str | Path = "models/modelo_recomendador_sanmartin.pkl",
    version: str = "1.0.0",
) -> tuple[Path, dict[str, Any]]:
    """
    Empaqueta todos los artefactos en un único archivo serializado autónomo.
    """
    logger.info("Iniciando empaquetado del artefacto de producción v%s...", version)

    cat_file = Path(catalog_path)
    mat_file = Path(matrix_path)
    pip_file = Path(pipeline_path)
    km_file = Path(kmeans_path)
    out_file = Path(output_path)

    # Validar existencias
    for p in [cat_file, mat_file, pip_file, km_file]:
        if not p.exists():
            raise FileNotFoundError(f"Archivo requerido no encontrado: {p}")

    # 1. Cargar componentes
    logger.info("Cargando componentes entrenados...")
    df_raw = pd.read_csv(cat_file)
    X_global = sp.load_npz(mat_file)
    pipeline = TurismoFeaturePipeline.load(pip_file)
    kmeans: KMeans = joblib.load(km_file)

    # 2. Filtrar y preparar catálogo de producción
    available_cols = [c for c in CATALOGO_COLUMNS if c in df_raw.columns]
    catalogo_prod = df_raw[available_cols].copy().reset_index(drop=True)

    # Asegurar tipos adecuados
    catalogo_prod["cluster_id"] = catalogo_prod["cluster_id"].astype(int)
    catalogo_prod["duracion_estimada_horas"] = catalogo_prod["duracion_estimada_horas"].astype(float)
    catalogo_prod["costo_referencial_pen"] = catalogo_prod["costo_referencial_pen"].astype(float)

    # 3. Construir paquete integral
    timestamp_now = datetime.now(timezone.utc).isoformat()
    bundle = {
        "version": version,
        "created_at": timestamp_now,
        "feature_pipeline": pipeline,
        "tfidf": pipeline.tfidf,
        "ohe": pipeline.ohe,
        "scaler": pipeline.scaler,
        "kmeans": kmeans,
        "X_global": X_global,
        "catalogo": catalogo_prod,
        "cluster_metadata": CLUSTER_METADATA,
        "metadata": {
            "n_recursos": len(catalogo_prod),
            "n_features": X_global.shape[1],
            "n_clusters": kmeans.n_clusters,
            "provincias": sorted(catalogo_prod["provincia"].unique().tolist()),
            "format": "SciPy CSR + Scikit-Learn Pipeline",
        },
    }

    # 4. Guardar archivo serializado
    out_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out_file)
    file_size_bytes = out_file.stat().st_size

    logger.info(
        "Artefacto serializado exportado con éxito a: %s (%.2f KB / %.2f MB)",
        out_file,
        file_size_bytes / 1024,
        file_size_bytes / (1024 * 1024),
    )

    metrics = {
        "output_path": str(out_file),
        "version": version,
        "created_at": timestamp_now,
        "tamano_bytes": file_size_bytes,
        "tamano_kb": file_size_bytes / 1024,
        "tamano_mb": file_size_bytes / (1024 * 1024),
        "n_recursos": len(catalogo_prod),
        "n_features": X_global.shape[1],
        "n_clusters": kmeans.n_clusters,
    }

    return out_file, metrics


def main() -> None:
    """
    Punto de entrada CLI para la exportación.
    """
    parser = argparse.ArgumentParser(
        description="Fase 6: Exportador del Modelo Serializado de Inferencia (TurismoIA San Martín)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--catalog",
        default="data/processed/dataset_con_clusters.csv",
        help="Ruta al catálogo con clusters",
    )
    parser.add_argument(
        "-m",
        "--matrix",
        default="data/processed/X_global.npz",
        help="Ruta a la matriz SciPy CSR X_global",
    )
    parser.add_argument(
        "-p",
        "--pipeline",
        default="models/feature_pipeline.pkl",
        help="Ruta al pipeline serializado",
    )
    parser.add_argument(
        "-k",
        "--kmeans",
        default="models/kmeans_model.pkl",
        help="Ruta al modelo K-Means serializado",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="models/modelo_recomendador_sanmartin.pkl",
        help="Ruta destino para el artefacto único de inferencia",
    )
    parser.add_argument(
        "-v",
        "--version",
        default="1.0.0",
        help="Versión semántica del artefacto",
    )

    args = parser.parse_args()

    try:
        out_path, metrics = export_production_model(
            catalog_path=args.catalog,
            matrix_path=args.matrix,
            pipeline_path=args.pipeline,
            kmeans_path=args.kmeans,
            output_path=args.output,
            version=args.version,
        )
        print("\n" + "=" * 80)
        print("   TURISMO IA SAN MARTÍN (ML ENGINE) - ARTEFACTO DE PRODUCCIÓN EXPORTADO")
        print("=" * 80)
        print(f"[*] Archivo destino:   {metrics['output_path']}")
        print(f"[*] Versión modelo:    v{metrics['version']}")
        print(f"[*] Fecha generación:  {metrics['created_at']}")
        print(f"[*] Tamaño en disco:   {metrics['tamano_kb']:.2f} KB ({metrics['tamano_mb']:.3f} MB) -> [OK < 5 MB]")
        print(f"[*] Recursos en base:  {metrics['n_recursos']} atractivos turísticos")
        print(f"[*] Dimensión matriz:  {metrics['n_features']} características multidimensionales")
        print(f"[*] Macro-Clusters:    {metrics['n_clusters']} grupos K-Means (C0 a C3)")
        print("=" * 80 + "\n")
    except Exception as exc:
        logger.error("Error durante la exportación del artefacto: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import src.export_model as exp_mod
    exp_mod.main()
