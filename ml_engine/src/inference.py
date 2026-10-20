#!/usr/bin/env python3
"""
Módulo de Inferencia Ultraligero para Producción - TurismoIA San Martín
======================================================================
Fase 6: Interfaz limpia de inferencia lista para producción y microservicios (FastAPI).

Características clave:
- Carga exclusivamente el artefacto serializado 'models/modelo_recomendador_sanmartin.pkl'.
- Inferencia ultrarrápida (< 10 ms por consulta).
- Desacoplamiento total: no re-entrena ni requiere archivos crudos.
- Filtros duros obligatorios con relajación controlada (fallback).
- Salida estandarizada lista para serialización JSON.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.feature_engineering import TurismoFeaturePipeline

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    Motor autónomo de inferencia para el sistema de recomendación turística.
    Carga el artefacto serializado en memoria una sola vez y resuelve consultas en milisegundos.
    """

    def __init__(
        self,
        model_path: str | Path = "models/modelo_recomendador_sanmartin.pkl",
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"No se encontró el artefacto serializado de producción en: {self.model_path}. "
                "Ejecute previamente 'src/export_model.py'."
            )

        logger.info("Cargando artefacto de producción desde: %s...", self.model_path)
        bundle = joblib.load(self.model_path)

        # Desempaquetado del artefacto
        self.version = bundle.get("version", "1.0.0")
        self.created_at = bundle.get("created_at", "")
        self.feature_pipeline: TurismoFeaturePipeline = bundle["feature_pipeline"]
        self.kmeans = bundle["kmeans"]
        self.X_global = bundle["X_global"]
        self.catalogo: pd.DataFrame = bundle["catalogo"].copy().reset_index(drop=True)
        self.cluster_metadata: dict[int, dict[str, str]] = bundle.get("cluster_metadata", {})

        logger.info(
            "Artefacto v%s cargado con éxito. Catálogo: %d atractivos, Espacio vectorial: %d dimensiones.",
            self.version,
            len(self.catalogo),
            self.X_global.shape[1],
        )

    def _generate_justification(
        self,
        rec_row: pd.Series,
        perfil_dict: dict[str, Any],
        cluster_label: str,
    ) -> str:
        """
        Genera una explicación dinámica de negocio (XAI) legible y fundamentada.
        """
        parts = []

        # 1. Coincidencia semántica con intereses del turista
        intereses = str(perfil_dict.get("intereses", "")).lower()
        user_words = [w for w in intereses.replace(",", " ").split() if len(w) > 3]

        item_text = (
            f"{rec_row.get('nombre_recurso', '')} "
            f"{rec_row.get('etiquetas_interes', '')} "
            f"{rec_row.get('subtipo', '')} "
            f"{rec_row.get('categoria', '')} "
            f"{rec_row.get('descripcion_corta', '')}"
        ).lower()

        matched = [w for w in user_words if w in item_text]
        if matched:
            unique_matches = list(dict.fromkeys(matched))[:3]
            parts.append(f"Alineado a tus intereses en {', '.join(unique_matches)}")
        else:
            sub = str(rec_row.get("subtipo", "")).title()
            cat = str(rec_row.get("categoria", "")).title()
            parts.append(f"Destacado en {sub or cat}")

        # 2. Respeto a restricciones operativas
        dur = float(rec_row.get("duracion_estimada_horas", 0.0))
        costo = float(rec_row.get("costo_referencial_pen", 0.0))
        costo_label = "acceso libre" if costo == 0.0 else f"S/{costo:.1f}"
        parts.append(f"tiempo de {dur:.1f}h y {costo_label}")

        # 3. Dificultad y territorio
        dif = rec_row.get("nivel_dificultad", "Media")
        prov = rec_row.get("provincia", "San Martín")
        parts.append(f"dificultad {dif} en {prov}")

        return "; ".join(parts).capitalize() + "."

    def predict_top_n(
        self,
        perfil_dict: dict[str, Any],
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Realiza la recomendación personalizada devolviendo una lista de diccionarios
        lista para serializarse a JSON en FastAPI.

        Parámetros en perfil_dict:
        - intereses (str): Palabras clave o búsqueda temática.
        - tiempo_disponible_horas / tiempo (float): Tiempo máximo en horas.
        - presupuesto_max_pen / presupuesto (float): Presupuesto máximo en soles.
        - nivel_dificultad / dificultad (str): 'Baja', 'Media', 'Alta'.
        - provincia (str): 'Todas' o provincia específica ('SAN MARTIN', 'LAMAS', etc.).
        - publico / publico_recomendado (str): 'Familia', 'Amigos', 'Pareja', 'Todos'.
        """
        # 1. Sanitización de entradas del perfil
        intereses = str(perfil_dict.get("intereses", "")).strip()
        tiempo_max = float(perfil_dict.get("tiempo_disponible_horas", perfil_dict.get("tiempo", 8.0)))
        presupuesto_max = float(perfil_dict.get("presupuesto_max_pen", perfil_dict.get("presupuesto", 100.0)))
        dificultad = str(perfil_dict.get("nivel_dificultad", perfil_dict.get("dificultad", "Media"))).strip().capitalize()
        provincia_in = str(perfil_dict.get("provincia", "Todas")).strip()
        publico = str(perfil_dict.get("publico", perfil_dict.get("publico_recomendado", "Todos"))).strip().capitalize()

        filtro_prov_activo = provincia_in.upper() not in ["TODAS", "TODOS", "CUALQUIERA", ""]
        provincia_ohe = provincia_in.upper() if filtro_prov_activo else "DESCONOCIDA"

        # 2. Vectorización ultrarrápida del perfil
        user_row = pd.DataFrame([{
            "categoria": "",
            "tipo": "",
            "subtipo": "",
            "etiquetas_interes": intereses,
            "descripcion_corta": intereses,
            "nivel_dificultad": dificultad,
            "provincia": provincia_ohe,
            "publico_recomendado": publico,
            "duracion_estimada_horas": min(tiempo_max, 7.0),
            "costo_referencial_pen": min(presupuesto_max, 40.0),
        }])

        user_vec = self.feature_pipeline.transform(user_row)

        # 3. Similitud del Coseno
        sims = cosine_similarity(user_vec, self.X_global).flatten()

        # 4. Filtros duros obligatorios
        mask_tiempo = self.catalogo["duracion_estimada_horas"] <= tiempo_max
        mask_costo = self.catalogo["costo_referencial_pen"] <= presupuesto_max
        mask_prov = (
            self.catalogo["provincia"].str.upper() == provincia_in.upper()
            if filtro_prov_activo
            else pd.Series(True, index=self.catalogo.index)
        )

        mask_filtros = mask_tiempo & mask_costo & mask_prov
        fallback_aplicado = False

        if mask_filtros.sum() == 0 and filtro_prov_activo:
            logger.warning(
                "Filtro duro estricto por provincia '%s' dejó 0 candidatos. Activando fallback.",
                provincia_in,
            )
            mask_filtros = mask_tiempo & mask_costo
            fallback_aplicado = True

        indices_validos = self.catalogo[mask_filtros].index.to_numpy()

        if len(indices_validos) == 0:
            logger.warning("No se encontraron candidatos que cumplan los filtros.")
            return []

        # 5. Ordenamiento y extracción del Top-N
        scores_validos = sims[indices_validos]
        top_sub_idx = np.argsort(scores_validos)[::-1][:top_n]
        best_indices = indices_validos[top_sub_idx]

        # 6. Construcción del resultado serializable
        results = []
        for rank, idx in enumerate(best_indices, start=1):
            row = self.catalogo.iloc[idx]
            cid = int(row["cluster_id"])
            c_meta = self.cluster_metadata.get(cid, {})
            c_label = c_meta.get("label", f"Cluster {cid}")
            justificacion = self._generate_justification(row, perfil_dict, c_label)

            results.append({
                "ranking": rank,
                "id_recurso": str(row.get("id_recurso", "")),
                "nombre_recurso": str(row.get("nombre_recurso", "")),
                "categoria": str(row.get("categoria", "")),
                "tipo": str(row.get("tipo", "")),
                "subtipo": str(row.get("subtipo", "")),
                "provincia": str(row.get("provincia", "")),
                "distrito": str(row.get("distrito", "")),
                "latitud": float(row.get("latitud", 0.0)),
                "longitud": float(row.get("longitud", 0.0)),
                "duracion_estimada_horas": float(row.get("duracion_estimada_horas", 0.0)),
                "costo_referencial_pen": float(row.get("costo_referencial_pen", 0.0)),
                "nivel_dificultad": str(row.get("nivel_dificultad", "")),
                "publico_recomendado": str(row.get("publico_recomendado", "")),
                "afinidad_pct": round(float(sims[idx] * 100.0), 2),
                "cluster_id": cid,
                "cluster_label": c_label,
                "justificacion": justificacion,
                "imagen_url": str(row.get("imagen_url", "")),
                "fallback_provincia": fallback_aplicado,
            })

        return results


# Patrón Singleton para microservicios y APIs
_ENGINE_INSTANCE: InferenceEngine | None = None


def get_inference_engine(
    model_path: str | Path = "models/modelo_recomendador_sanmartin.pkl",
) -> InferenceEngine:
    """
    Retorna la instancia global del motor de inferencia (Singleton).
    Evita recargar el archivo .pkl en memoria en cada llamada HTTP.
    """
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = InferenceEngine(model_path=model_path)
    return _ENGINE_INSTANCE


def predict_top_n(
    perfil_dict: dict[str, Any],
    top_n: int = 5,
    model_path: str | Path = "models/modelo_recomendador_sanmartin.pkl",
) -> list[dict[str, Any]]:
    """
    Función de acceso directo a inferencia lista para endpoints de FastAPI.
    """
    engine = get_inference_engine(model_path=model_path)
    return engine.predict_top_n(perfil_dict=perfil_dict, top_n=top_n)


if __name__ == "__main__":
    # Prueba rápida de humo
    test_perfil = {
        "intereses": "cataratas selva naturaleza",
        "tiempo_disponible_horas": 4.0,
        "presupuesto_max_pen": 30.0,
        "nivel_dificultad": "Baja",
        "provincia": "SAN MARTIN",
        "publico": "Amigos",
    }
    recs = predict_top_n(test_perfil, top_n=3)
    print("\n--- PRUEBA DE HUMO INFERENCE ENGINE ---")
    for r in recs:
        print(f"[{r['ranking']}] {r['nombre_recurso']} ({r['provincia']}) - S/{r['costo_referencial_pen']} | {r['afinidad_pct']}% | {r['cluster_label']}")
        print(f"    Justificación: {r['justificacion']}")
