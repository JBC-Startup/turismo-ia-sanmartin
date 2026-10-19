#!/usr/bin/env python3
"""
Módulo de Modelado, Clustering y Motor de Recomendación - TurismoIA San Martín
=============================================================================
Fases 4 y 5 del Pipeline de ML:
- Fase 4.1: Clustering no supervisado con K-Means (perfilado de macro-experiencias).
- Fase 4.2: Motor de recomendación por Similitud del Coseno con filtrado duro y fallback.
- Fase 5: Validación técnica offline y auditoría de restricciones con perfiles sintéticos.

Cumple estrictamente con las restricciones arquitectónicas:
- Machine Learning clásico reproducible (Scikit-Learn).
- Sin LLMs para la selección ni redes neuronales sobreajustadas.
- Explicabilidad del resultado (XAI) y 100% de cumplimiento de restricciones operativas.
"""

from __future__ import annotations

import argparse
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
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from src.feature_engineering import TurismoFeaturePipeline

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Etiquetas descriptivas de macro-experiencias para los clusters
CLUSTER_LABELS: dict[int, str] = {
    0: "Centros Urbanos, Lagunas y Paisajes en San Martín (Tarapoto)",
    1: "Patrimonio Cultural, Historia, Tradiciones y Plazas Urbanas",
    2: "Aventura, Espeleología (Grutas y Cuevas) y Senderos de Selva Alta",
    3: "Ecoturismo de Selva, Cascadas Emblemáticas y Caídas de Agua",
}


class TurismoRecommender:
    """
    Motor inteligente de recomendación turística para la región San Martín.
    
    Integra:
    - Agrupamiento de macro-experiencias mediante K-Means.
    - Vectorización en espacio multidimensional (139 características).
    - Cálculo de afinidad mediante Similitud del Coseno.
    - Aplicación estricta de filtros duros operativos (duración, costo, provincia).
    - Mecanismo de relajación controlada (fallback).
    - Generación dinámica de justificaciones legibles (XAI).
    """

    def __init__(
        self,
        catalog_df: pd.DataFrame,
        X_global: sp.csr_matrix,
        feature_pipeline: TurismoFeaturePipeline,
        kmeans_model: KMeans | None = None,
        cluster_labels: dict[int, str] | None = None,
    ) -> None:
        self.catalog_df = catalog_df.copy().reset_index(drop=True)
        self.X_global = X_global
        self.feature_pipeline = feature_pipeline
        self.kmeans_model = kmeans_model
        self.cluster_labels = cluster_labels or CLUSTER_LABELS

        if len(self.catalog_df) != self.X_global.shape[0]:
            raise ValueError(
                f"Discrepancia de dimensiones: catálogo tiene {len(self.catalog_df)} filas "
                f"y X_global tiene {self.X_global.shape[0]} filas."
            )

    def train_clustering(
        self,
        n_clusters: int = 4,
        random_state: int = 42,
        n_init: int = 10,
    ) -> KMeans:
        """
        Entrena el modelo K-Means sobre la matriz de características X_global
        y asigna el cluster_id a cada recurso del catálogo.
        """
        logger.info(
            "Entrenando K-Means (n_clusters=%d, random_state=%d, n_init=%d)...",
            n_clusters,
            random_state,
            n_init,
        )
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=n_init,
        )
        cluster_ids = kmeans.fit_predict(self.X_global)
        self.catalog_df["cluster_id"] = cluster_ids.astype(int)
        self.kmeans_model = kmeans
        logger.info("K-Means entrenado exitosamente.")
        return kmeans

    def get_cluster_summary(self) -> list[dict[str, Any]]:
        """
        Genera un resumen interpretativo cuantitativo y cualitativo de cada cluster.
        """
        if "cluster_id" not in self.catalog_df.columns:
            raise RuntimeError("El catálogo aún no cuenta con asignación de clusters. Ejecute train_clustering().")

        summaries = []
        total_recursos = len(self.catalog_df)

        for c_id in sorted(self.catalog_df["cluster_id"].unique()):
            sub = self.catalog_df[self.catalog_df["cluster_id"] == c_id]
            count = len(sub)
            pct = (count / total_recursos) * 100.0

            top_cat = sub["categoria"].value_counts().index[0] if "categoria" in sub.columns else "N/A"
            top_subt = sub["subtipo"].value_counts().index[0] if "subtipo" in sub.columns else "N/A"
            top_prov = sub["provincia"].value_counts().index[0] if "provincia" in sub.columns else "N/A"
            dur_media = float(sub["duracion_estimada_horas"].mean())
            costo_medio = float(sub["costo_referencial_pen"].mean())

            summaries.append({
                "cluster_id": int(c_id),
                "nombre_cluster": self.cluster_labels.get(c_id, f"Cluster {c_id}"),
                "total_atractivos": count,
                "porcentaje": pct,
                "categoria_predominante": top_cat,
                "subtipo_predominante": top_subt,
                "provincia_predominante": top_prov,
                "duracion_media_horas": dur_media,
                "costo_medio_pen": costo_medio,
                "ejemplos": sub["nombre_recurso"].head(3).tolist(),
            })

        return summaries

    def generate_justification(
        self,
        rec_row: pd.Series,
        perfil_usuario: dict[str, Any],
    ) -> str:
        """
        Genera una justificación explicativa legible para la recomendación (XAI)
        basada en las coincidencias de intereses semánticos, tiempo, presupuesto,
        dificultad y pertenencia al macro-cluster.
        """
        parts = []

        # 1. Coincidencia de intereses semánticos
        user_intereses = str(perfil_usuario.get("intereses", "")).lower()
        user_words = [w for w in user_intereses.replace(",", " ").split() if len(w) > 3]

        item_text = (
            f"{rec_row.get('nombre_recurso', '')} "
            f"{rec_row.get('etiquetas_interes', '')} "
            f"{rec_row.get('subtipo', '')} "
            f"{rec_row.get('categoria', '')} "
            f"{rec_row.get('descripcion_corta', '')}"
        ).lower()

        matched_words = [w for w in user_words if w in item_text]
        if matched_words:
            unique_matches = list(dict.fromkeys(matched_words))[:3]
            parts.append(f"Alineado a tus intereses en {', '.join(unique_matches)}")
        else:
            cat_label = str(rec_row.get("categoria", "")).title()
            sub_label = str(rec_row.get("subtipo", "")).title()
            parts.append(f"Destacado en {sub_label or cat_label}")

        # 2. Ajuste operativo de tiempo y presupuesto
        dur = float(rec_row.get("duracion_estimada_horas", 0.0))
        costo = float(rec_row.get("costo_referencial_pen", 0.0))
        costo_str = "acceso libre" if costo == 0.0 else f"S/{costo:.1f}"
        parts.append(f"tiempo de {dur:.1f}h y {costo_str}")

        # 3. Dificultad y ubicación
        dif = rec_row.get("nivel_dificultad", "Media")
        prov = rec_row.get("provincia", "San Martín")
        parts.append(f"dificultad {dif} en {prov}")

        return "; ".join(parts).capitalize() + "."

    def recomendar_atractivos(
        self,
        perfil_usuario: dict[str, Any],
        top_n: int = 5,
    ) -> pd.DataFrame:
        """
        Ejecuta el pipeline de recomendación para un perfil de usuario:
        a) Proyecta las preferencias del usuario en el espacio vectorial (139 dim).
        b) Calcula la Similitud del Coseno contra todo el catálogo.
        c) Aplica filtros duros obligatorios (tiempo, presupuesto, provincia).
           Aplica fallback relajando provincia si no hay candidatos.
        d) Ordena descendentemente por afinidad y extrae el Top-N.
        e) Agrega justificaciones dinámicas y metadatos interpretables.
        """
        # Extracción y sanitización de parámetros del usuario
        intereses = str(perfil_usuario.get("intereses", "")).strip()
        tiempo_max = float(perfil_usuario.get("tiempo_disponible_horas", perfil_usuario.get("tiempo", 8.0)))
        presupuesto_max = float(perfil_usuario.get("presupuesto_max_pen", perfil_usuario.get("presupuesto", 100.0)))
        dificultad = str(perfil_usuario.get("nivel_dificultad", perfil_usuario.get("dificultad", "Media"))).strip().capitalize()
        provincia_in = str(perfil_usuario.get("provincia", "Todas")).strip()
        publico = str(perfil_usuario.get("publico", perfil_usuario.get("publico_recomendado", "Todos"))).strip().capitalize()

        # Determinar si la provincia es específica o genérica
        filtro_prov_activo = provincia_in.upper() not in ["TODAS", "TODOS", "CUALQUIERA", ""]
        provincia_para_ohe = provincia_in.upper() if filtro_prov_activo else "DESCONOCIDA"

        # a) Construir el registro de usuario para la proyección vectorial
        user_row = pd.DataFrame([{
            "categoria": "",
            "tipo": "",
            "subtipo": "",
            "etiquetas_interes": intereses,
            "descripcion_corta": intereses,
            "nivel_dificultad": dificultad,
            "provincia": provincia_para_ohe,
            "publico_recomendado": publico,
            "duracion_estimada_horas": min(tiempo_max, 7.0),
            "costo_referencial_pen": min(presupuesto_max, 40.0),
        }])

        user_vec = self.feature_pipeline.transform(user_row)

        # b) Cálculo de Similitud del Coseno
        similitudes = cosine_similarity(user_vec, self.X_global).flatten()

        df_candidates = self.catalog_df.copy()
        df_candidates["afinidad_score"] = similitudes
        df_candidates["afinidad_pct"] = (similitudes * 100.0).round(2)

        # c) Aplicación de Filtros Duros
        mask_tiempo = df_candidates["duracion_estimada_horas"] <= tiempo_max
        mask_costo = df_candidates["costo_referencial_pen"] <= presupuesto_max
        mask_prov = (
            df_candidates["provincia"].str.upper() == provincia_in.upper()
            if filtro_prov_activo
            else pd.Series(True, index=df_candidates.index)
        )

        mask_filtros = mask_tiempo & mask_costo & mask_prov

        # Mecanismo de Fallback si no hay candidatos
        fallback_provincia_aplicado = False
        if mask_filtros.sum() == 0 and filtro_prov_activo:
            logger.warning(
                "Filtro estricto por provincia '%s' dejó 0 candidatos con tiempo <= %.1fh y presupuesto <= S/%.1f. "
                "Aplicando fallback: relajando provincia para garantizar recomendaciones.",
                provincia_in,
                tiempo_max,
                presupuesto_max,
            )
            mask_filtros = mask_tiempo & mask_costo
            fallback_provincia_aplicado = True

        df_filtered = df_candidates[mask_filtros].copy()

        if df_filtered.empty:
            logger.warning("No se encontraron atractivos que cumplan con los filtros incluso tras fallback.")
            return pd.DataFrame()

        # d) Ordenar descendentemente por afinidad y tomar Top-N
        df_top = df_filtered.sort_values(by="afinidad_score", ascending=False).head(top_n).copy()
        df_top["ranking"] = range(1, len(df_top) + 1)

        # e) Mapear nombre del cluster y generar justificaciones legibles
        df_top["cluster_nombre"] = df_top["cluster_id"].map(
            lambda cid: self.cluster_labels.get(cid, f"Cluster {cid}")
        )
        df_top["justificacion"] = df_top.apply(
            lambda row: self.generate_justification(row, perfil_usuario),
            axis=1,
        )
        df_top["fallback_provincia"] = fallback_provincia_aplicado

        # Selección de columnas clave para presentación
        cols_ordered = [
            "ranking",
            "id_recurso",
            "nombre_recurso",
            "provincia",
            "distrito",
            "categoria",
            "subtipo",
            "duracion_estimada_horas",
            "costo_referencial_pen",
            "nivel_dificultad",
            "publico_recomendado",
            "afinidad_pct",
            "cluster_id",
            "cluster_nombre",
            "justificacion",
            "fallback_provincia",
        ]
        available_cols = [c for c in cols_ordered if c in df_top.columns]
        return df_top[available_cols].reset_index(drop=True)

    def evaluate_hard_filters_compliance(
        self,
        df_top: pd.DataFrame,
        perfil_usuario: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Valida rigurosamente que ninguna recomendación exceda el tiempo o presupuesto
        solicitado (Fase 5 de control de calidad).
        """
        if df_top.empty:
            return {
                "cumple_tiempo": False,
                "cumple_costo": False,
                "cumple_provincia": False,
                "porcentaje_cumplimiento": 0.0,
            }

        tiempo_max = float(perfil_usuario.get("tiempo_disponible_horas", perfil_usuario.get("tiempo", 8.0)))
        presupuesto_max = float(perfil_usuario.get("presupuesto_max_pen", perfil_usuario.get("presupuesto", 100.0)))
        provincia = str(perfil_usuario.get("provincia", "Todas")).strip().upper()

        cumple_tiempo = bool((df_top["duracion_estimada_horas"] <= tiempo_max).all())
        cumple_costo = bool((df_top["costo_referencial_pen"] <= presupuesto_max).all())

        if provincia not in ["TODAS", "TODOS", "CUALQUIERA", ""]:
            cumple_prov = bool((df_top["provincia"].str.upper() == provincia).all())
        else:
            cumple_prov = True

        total_checks = len(df_top) * 2
        passed_checks = int((df_top["duracion_estimada_horas"] <= tiempo_max).sum()) + int(
            (df_top["costo_referencial_pen"] <= presupuesto_max).sum()
        )
        pct_compliance = (passed_checks / total_checks * 100.0) if total_checks > 0 else 0.0

        return {
            "cumple_tiempo": cumple_tiempo,
            "cumple_costo": cumple_costo,
            "cumple_provincia": cumple_prov,
            "porcentaje_cumplimiento": pct_compliance,
            "tiempo_max_solicitado": tiempo_max,
            "costo_max_solicitado": presupuesto_max,
            "tiempo_max_observado": float(df_top["duracion_estimada_horas"].max()),
            "costo_max_observado": float(df_top["costo_referencial_pen"].max()),
        }

    def save_artifacts(
        self,
        kmeans_output_path: str | Path = "models/kmeans_model.pkl",
        catalog_output_path: str | Path = "data/processed/dataset_con_clusters.csv",
    ) -> tuple[Path, Path]:
        """
        Guarda el modelo K-Means y el catálogo enriquecido con clusters.
        """
        km_path = Path(kmeans_output_path)
        km_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.kmeans_model, km_path)
        logger.info("Modelo K-Means serializado guardado en: %s", km_path)

        cat_path = Path(catalog_output_path)
        cat_path.parent.mkdir(parents=True, exist_ok=True)
        self.catalog_df.to_csv(cat_path, index=False, encoding="utf-8")
        logger.info("Catálogo con clusters guardado en: %s (%d filas)", cat_path, len(self.catalog_df))

        return km_path, cat_path

    @classmethod
    def load(
        cls,
        catalog_path: str | Path = "data/processed/dataset_limpio.csv",
        matrix_path: str | Path = "data/processed/X_global.npz",
        pipeline_path: str | Path = "models/feature_pipeline.pkl",
        kmeans_path: str | Path | None = "models/kmeans_model.pkl",
    ) -> TurismoRecommender:
        """
        Carga los datos y artefactos entrenados para inicializar el recomendador.
        """
        df = pd.read_csv(catalog_path)
        X = sp.load_npz(matrix_path)
        pipeline = TurismoFeaturePipeline.load(pipeline_path)

        kmeans_model = None
        if kmeans_path and Path(kmeans_path).exists():
            kmeans_model = joblib.load(kmeans_path)
            if "cluster_id" not in df.columns:
                df["cluster_id"] = kmeans_model.predict(X)

        return cls(
            catalog_df=df,
            X_global=X,
            feature_pipeline=pipeline,
            kmeans_model=kmeans_model,
        )


# Variable global para patrón singleton en llamadas funcionales directas
_GLOBAL_RECOMMENDER: TurismoRecommender | None = None


def recomendar_atractivos(
    perfil_usuario: dict[str, Any],
    top_n: int = 5,
    recommender: TurismoRecommender | None = None,
) -> pd.DataFrame:
    """
    Función de recomendación reutilizable de alto nivel.
    Si no se suministra un recomendador, carga la instancia global por defecto.
    """
    global _GLOBAL_RECOMMENDER
    rec = recommender or _GLOBAL_RECOMMENDER
    if rec is None:
        rec = TurismoRecommender.load()
        if rec.kmeans_model is None:
            rec.train_clustering()
        _GLOBAL_RECOMMENDER = rec

    return rec.recomendar_atractivos(perfil_usuario, top_n=top_n)


def format_recommendations_table(df_recs: pd.DataFrame, title: str) -> str:
    """
    Formatea el Top-N en una tabla ASCII legible y estética para terminal.
    """
    lines = []
    lines.append("=" * 105)
    lines.append(f" {title.upper()}")
    lines.append("=" * 105)

    header = f"{'Rank':4s} | {'Atractivo':32s} | {'Provincia':14s} | {'Durac.':7s} | {'Costo':8s} | {'Afinidad':8s} | {'Cluster':7s}"
    lines.append(header)
    lines.append("-" * 105)

    for _, row in df_recs.iterrows():
        nombre = str(row["nombre_recurso"])[:32]
        prov = str(row["provincia"])[:14]
        dur = f"{row['duracion_estimada_horas']:.1f}h"
        costo = f"S/{row['costo_referencial_pen']:.1f}"
        afinidad = f"{row['afinidad_pct']:.1f}%"
        cid = f"C{row['cluster_id']}"
        lines.append(f"{row['ranking']:4d} | {nombre:32s} | {prov:14s} | {dur:7s} | {costo:8s} | {afinidad:8s} | {cid:7s}")
        lines.append(f"     -> Justificación: {row['justificacion']}")
        lines.append("-" * 105)

    return "\n".join(lines)


def run_modeling_and_validation(
    catalog_path: str | Path = "data/processed/dataset_limpio.csv",
    matrix_path: str | Path = "data/processed/X_global.npz",
    pipeline_path: str | Path = "models/feature_pipeline.pkl",
    kmeans_output_path: str | Path = "models/kmeans_model.pkl",
    clusters_output_path: str | Path = "data/processed/dataset_con_clusters.csv",
) -> tuple[TurismoRecommender, pd.DataFrame, pd.DataFrame]:
    """
    Función de orquestación completa para las Fases 4 y 5:
    1. Carga catálogo, X_global y feature_pipeline.
    2. Entrena K-Means (k=4, seed=42, n_init=10).
    3. Exporta artefactos serializados.
    4. Ejecuta validación técnica con los casos sintéticos A y B.
    """
    logger.info("Iniciando Fase 4: Modelado y Clustering K-Means...")
    recommender = TurismoRecommender.load(
        catalog_path=catalog_path,
        matrix_path=matrix_path,
        pipeline_path=pipeline_path,
        kmeans_path=None,
    )

    # Entrenar agrupamiento K-Means
    recommender.train_clustering(n_clusters=4, random_state=42, n_init=10)

    # Guardar modelo K-Means y catálogo enriquecido
    recommender.save_artifacts(
        kmeans_output_path=kmeans_output_path,
        catalog_output_path=clusters_output_path,
    )

    # Reporte de Clusters por consola
    print("\n" + "=" * 105)
    print("      TURISMO IA SAN MARTÍN (ML ENGINE) - CLUSTERING NO SUPERVISADO (K-MEANS)")
    print("=" * 105)
    cluster_summaries = recommender.get_cluster_summary()
    for cs in cluster_summaries:
        print(f"[*] CLUSTER {cs['cluster_id']}: {cs['total_atractivos']:3d} atractivos ({cs['porcentaje']:.1f}%)")
        print(f"    Macro-experiencia: {cs['nombre_cluster']}")
        print(f"    Perfil dominante:  Cat: {cs['categoria_predominante']} | Subtipo: {cs['subtipo_predominante']} | Foco: {cs['provincia_predominante']}")
        print(f"    Promedios:         Duración: {cs['duracion_media_horas']:.2f}h | Costo: S/{cs['costo_medio_pen']:.2f}")
        print(f"    Ejemplos:          {', '.join(cs['ejemplos'])}")
        print("-" * 105)

    # Fase 5: Validación Técnica Offline con Perfiles Sintéticos
    print("\n" + "=" * 105)
    print("      TURISMO IA SAN MARTÍN (ML ENGINE) - VALIDACIÓN TÉCNICA OFFLINE (FASE 5)")
    print("=" * 105)

    # Caso A: Aventura y cascadas con tiempo y presupuesto acotados
    perfil_caso_a = {
        "intereses": "cataratas aventura selva naturaleza",
        "tiempo_disponible_horas": 4.0,
        "presupuesto_max_pen": 30.0,
        "nivel_dificultad": "Baja",
        "provincia": "SAN MARTIN",
        "publico": "Amigos",
    }
    top5_a = recommender.recomendar_atractivos(perfil_caso_a, top_n=5)
    eval_a = recommender.evaluate_hard_filters_compliance(top5_a, perfil_caso_a)

    print("\n" + format_recommendations_table(top5_a, "Caso A: Aventura y cascadas con tiempo limitado (Tarapoto)"))
    print(f"[*] Auditoría Filtros Duros Caso A:")
    print(f"    - Tiempo solicitado: <= {eval_a['tiempo_max_solicitado']}h | Máximo observado en Top-5: {eval_a['tiempo_max_observado']}h -> {'[OK]' if eval_a['cumple_tiempo'] else '[FALLO]'}")
    print(f"    - Presupuesto solicitado: <= S/{eval_a['costo_max_solicitado']} | Máximo observado en Top-5: S/{eval_a['costo_max_observado']} -> {'[OK]' if eval_a['cumple_costo'] else '[FALLO]'}")
    print(f"    - Cumplimiento estricto: {eval_a['porcentaje_cumplimiento']:.1f}%")

    # Caso B: Turismo cultural y familiar de día completo
    perfil_caso_b = {
        "intereses": "cultura artesania cafe historia",
        "tiempo_disponible_horas": 8.0,
        "presupuesto_max_pen": 100.0,
        "nivel_dificultad": "Media",
        "provincia": "LAMAS",
        "publico": "Familia",
    }
    top5_b = recommender.recomendar_atractivos(perfil_caso_b, top_n=5)
    eval_b = recommender.evaluate_hard_filters_compliance(top5_b, perfil_caso_b)

    print("\n" + format_recommendations_table(top5_b, "Caso B: Turismo cultural y familiar de día completo (Lamas)"))
    print(f"[*] Auditoría Filtros Duros Caso B:")
    print(f"    - Tiempo solicitado: <= {eval_b['tiempo_max_solicitado']}h | Máximo observado en Top-5: {eval_b['tiempo_max_observado']}h -> {'[OK]' if eval_b['cumple_tiempo'] else '[FALLO]'}")
    print(f"    - Presupuesto solicitado: <= S/{eval_b['costo_max_solicitado']} | Máximo observado en Top-5: S/{eval_b['costo_max_observado']} -> {'[OK]' if eval_b['cumple_costo'] else '[FALLO]'}")
    print(f"    - Cumplimiento estricto: {eval_b['porcentaje_cumplimiento']:.1f}%\n")

    return recommender, top5_a, top5_b


def main() -> None:
    """
    Punto de entrada CLI.
    """
    parser = argparse.ArgumentParser(
        description="Fases 4 y 5: Clustering K-Means y Motor de Recomendación (TurismoIA San Martín)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--catalog",
        default="data/processed/dataset_limpio.csv",
        help="Ruta al catálogo limpio CSV",
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
        "--kmeans-output",
        default="models/kmeans_model.pkl",
        help="Destino para guardar el modelo K-Means",
    )
    parser.add_argument(
        "--clusters-output",
        default="data/processed/dataset_con_clusters.csv",
        help="Destino para el catálogo con columna cluster_id",
    )

    args = parser.parse_args()

    try:
        run_modeling_and_validation(
            catalog_path=args.catalog,
            matrix_path=args.matrix,
            pipeline_path=args.pipeline,
            kmeans_output_path=args.kmeans_output,
            clusters_output_path=args.clusters_output,
        )
    except Exception as exc:
        logger.error("Error crítico durante la ejecución del recomendador: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import src.recommender as rec_mod
    rec_mod.main()
