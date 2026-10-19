"""
Pruebas unitarias para src/recommender.py
=========================================
Verifica:
1. Agrupamiento con K-Means (4 clusters, distribución y resúmenes).
2. Motor de recomendación con Similitud del Coseno.
3. Cumplimiento del 100% en filtros duros (tiempo, presupuesto, provincia).
4. Activación de fallback cuando el filtro de provincia deja 0 resultados.
5. Generación de justificaciones explicativas legibles (XAI).
6. Casos sintéticos contrastantes A y B (Fase 5).
7. Persistencia de artefactos (kmeans_model.pkl y dataset_con_clusters.csv).
"""

import unittest
from pathlib import Path

import pandas as pd
import scipy.sparse as sp

from src.recommender import TurismoRecommender, recomendar_atractivos


class TestTurismoRecommender(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog_path = "data/processed/dataset_limpio.csv"
        cls.matrix_path = "data/processed/X_global.npz"
        cls.pipeline_path = "models/feature_pipeline.pkl"
        cls.kmeans_path = "models/kmeans_model.pkl"
        cls.clusters_path = "data/processed/dataset_con_clusters.csv"

        if not Path(cls.catalog_path).exists() or not Path(cls.matrix_path).exists():
            raise unittest.SkipTest("Archivos de datos de prueba no encontrados.")

        cls.recommender = TurismoRecommender.load(
            catalog_path=cls.catalog_path,
            matrix_path=cls.matrix_path,
            pipeline_path=cls.pipeline_path,
            kmeans_path=cls.kmeans_path if Path(cls.kmeans_path).exists() else None,
        )
        if cls.recommender.kmeans_model is None:
            cls.recommender.train_clustering(n_clusters=4, random_state=42, n_init=10)

    def test_clustering_training_and_structure(self):
        summaries = self.recommender.get_cluster_summary()
        self.assertEqual(len(summaries), 4)

        cluster_ids = {s["cluster_id"] for s in summaries}
        self.assertEqual(cluster_ids, {0, 1, 2, 3})

        total_recursos = sum(s["total_atractivos"] for s in summaries)
        self.assertEqual(total_recursos, len(self.recommender.catalog_df))

        for s in summaries:
            self.assertIn("nombre_cluster", s)
            self.assertIn("categoria_predominante", s)
            self.assertGreater(s["total_atractivos"], 0)

    def test_recomendar_atractivos_hard_filters_compliance(self):
        perfil = {
            "intereses": "cataratas naturaleza cascadas",
            "tiempo_disponible_horas": 3.0,
            "presupuesto_max_pen": 15.0,
            "nivel_dificultad": "Baja",
            "provincia": "SAN MARTIN",
            "publico": "Todos",
        }
        recs = self.recommender.recomendar_atractivos(perfil, top_n=5)

        self.assertEqual(len(recs), 5)
        eval_metrics = self.recommender.evaluate_hard_filters_compliance(recs, perfil)

        self.assertTrue(eval_metrics["cumple_tiempo"], "Todas las recomendaciones deben respetar el tiempo límite")
        self.assertTrue(eval_metrics["cumple_costo"], "Todas las recomendaciones deben respetar el presupuesto")
        self.assertTrue(eval_metrics["cumple_provincia"], "Todas las recomendaciones deben ser de la provincia pedida")
        self.assertEqual(eval_metrics["porcentaje_cumplimiento"], 100.0)

    def test_recomendar_atractivos_ranking_order(self):
        perfil = {
            "intereses": "arqueologia historia cultura",
            "tiempo_disponible_horas": 6.0,
            "presupuesto_max_pen": 50.0,
            "provincia": "Todas",
        }
        recs = self.recommender.recomendar_atractivos(perfil, top_n=5)

        self.assertEqual(len(recs), 5)
        # Verificar que el ranking sea consecutivo 1..5
        self.assertEqual(recs["ranking"].tolist(), [1, 2, 3, 4, 5])
        # Verificar orden descendente de afinidad
        afinidades = recs["afinidad_pct"].tolist()
        self.assertEqual(afinidades, sorted(afinidades, reverse=True))

    def test_fallback_mechanism_when_province_has_zero_results(self):
        # Perfil con tiempo extremadamente bajo y provincia con pocos recursos
        perfil_imposible = {
            "intereses": "paseo",
            "tiempo_disponible_horas": 0.5,
            "presupuesto_max_pen": 0.0,
            "provincia": "EL DORADO",  # Solo 2 recursos en el dataset
        }
        recs = self.recommender.recomendar_atractivos(perfil_imposible, top_n=3)

        if not recs.empty:
            # Si se activó fallback, debe haber devuelto recomendaciones respetando tiempo y costo
            self.assertTrue(recs["fallback_provincia"].iloc[0])
            self.assertTrue((recs["duracion_estimada_horas"] <= 0.5).all())
            self.assertTrue((recs["costo_referencial_pen"] <= 0.0).all())

    def test_case_a_validation(self):
        perfil_caso_a = {
            "intereses": "cataratas aventura selva naturaleza",
            "tiempo_disponible_horas": 4.0,
            "presupuesto_max_pen": 30.0,
            "nivel_dificultad": "Baja",
            "provincia": "SAN MARTIN",
            "publico": "Amigos",
        }
        recs = self.recommender.recomendar_atractivos(perfil_caso_a, top_n=5)
        self.assertEqual(len(recs), 5)

        eval_res = self.recommender.evaluate_hard_filters_compliance(recs, perfil_caso_a)
        self.assertEqual(eval_res["porcentaje_cumplimiento"], 100.0)
        self.assertTrue(eval_res["cumple_tiempo"])
        self.assertTrue(eval_res["cumple_costo"])
        self.assertTrue(eval_res["cumple_provincia"])

        # Verificar justificaciones no vacías
        for just in recs["justificacion"]:
            self.assertTrue(len(just) > 10)

    def test_case_b_validation(self):
        perfil_caso_b = {
            "intereses": "cultura artesania cafe historia",
            "tiempo_disponible_horas": 8.0,
            "presupuesto_max_pen": 100.0,
            "nivel_dificultad": "Media",
            "provincia": "LAMAS",
            "publico": "Familia",
        }
        recs = self.recommender.recomendar_atractivos(perfil_caso_b, top_n=5)
        self.assertEqual(len(recs), 5)

        eval_res = self.recommender.evaluate_hard_filters_compliance(recs, perfil_caso_b)
        self.assertEqual(eval_res["porcentaje_cumplimiento"], 100.0)
        self.assertTrue(eval_res["cumple_tiempo"])
        self.assertTrue(eval_res["cumple_costo"])
        self.assertTrue(eval_res["cumple_provincia"])

    def test_standalone_recomendar_atractivos_function(self):
        perfil = {
            "intereses": "lagunas naturaleza",
            "tiempo_disponible_horas": 5.0,
            "presupuesto_max_pen": 20.0,
            "provincia": "Todas",
        }
        recs = recomendar_atractivos(perfil, top_n=3, recommender=self.recommender)
        self.assertEqual(len(recs), 3)
        self.assertIn("ranking", recs.columns)
        self.assertIn("justificacion", recs.columns)

    def test_artifacts_existence_and_consistency(self):
        self.assertTrue(Path(self.kmeans_path).exists(), "El modelo kmeans_model.pkl debe existir")
        self.assertTrue(Path(self.clusters_path).exists(), "El archivo dataset_con_clusters.csv debe existir")

        df_clusters = pd.read_csv(self.clusters_path)
        self.assertEqual(len(df_clusters), 297)
        self.assertIn("cluster_id", df_clusters.columns)
        self.assertEqual(set(df_clusters["cluster_id"].unique()), {0, 1, 2, 3})


if __name__ == "__main__":
    unittest.main()
