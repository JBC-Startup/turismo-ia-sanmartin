"""
Pruebas unitarias para src/feature_engineering.py
=================================================
Verifica:
1. Construcción consistente del corpus semántico textual.
2. Ajuste y transformación del espacio vectorial (TF-IDF, OHE, MinMaxScaler).
3. Dimensionalidad esperada y ensamblado horizontal en formato CSR.
4. Integridad matemática (sin NaNs, sin Infs, rango [0, 1] numérico).
5. Robustez en inferencia con categorías no vistas (handle_unknown='ignore').
6. Serialización y deserialización correcta del pipeline.
7. Ejecución end-to-end sobre dataset_limpio.csv y persistencia en .npz.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from src.feature_engineering import TurismoFeaturePipeline, run_feature_engineering


class TestFeatureEngineering(unittest.TestCase):

    def setUp(self):
        self.sample_df = pd.DataFrame({
            "categoria": ["SITIOS NATURALES", "MANIFESTACIONES CULTURALES", "SITIOS NATURALES"],
            "tipo": ["CAIDAS DE AGUA", "ARQUITECTURA", "LAGOS Y LAGUNAS"],
            "subtipo": ["CATARATAS", "TEMPLO", "LAGUNA"],
            "etiquetas_interes": ["naturaleza aventura", "cultura historia", "naturaleza paseo"],
            "descripcion_corta": [
                "Hermosa catarata en la selva con posa natural para bano",
                "Templo colonial historico en la plaza principal de la ciudad",
                "Laguna tranquila rodeada de vegetacion y senderos",
            ],
            "nivel_dificultad": ["Baja", "Media", "Alta"],
            "provincia": ["SAN MARTIN", "MOYOBAMBA", "RIOJA"],
            "publico_recomendado": ["Todos", "Amigos", "Familia"],
            "duracion_estimada_horas": [1.5, 3.0, 4.5],
            "costo_referencial_pen": [0.0, 15.0, 30.0],
        })

    def test_build_corpus(self):
        pipeline = TurismoFeaturePipeline(max_features=20)
        corpus = pipeline.build_corpus(self.sample_df)

        self.assertEqual(len(corpus), 3)
        self.assertIn("SITIOS NATURALES", corpus.iloc[0])
        self.assertIn("catarata", corpus.iloc[0])
        self.assertIn("TEMPLO", corpus.iloc[1])

    def test_fit_transform_shapes_and_types(self):
        max_feat = 10
        pipeline = TurismoFeaturePipeline(max_features=max_feat)
        X = pipeline.fit_transform(self.sample_df)

        self.assertTrue(sp.isspmatrix_csr(X), "La matriz resultante debe ser scipy.sparse.csr_matrix")

        # 3 filas
        self.assertEqual(X.shape[0], 3)

        # Total columnas = max_features (10) + ohe categories (3 dificultad + 3 provincia + 3 publico = 9) + 2 num = 21
        expected_cols = max_feat + (3 + 3 + 3) + 2
        self.assertEqual(X.shape[1], expected_cols)

    def test_numerical_scaling_bounds(self):
        pipeline = TurismoFeaturePipeline(max_features=10)
        pipeline.fit(self.sample_df)

        num_arr = pipeline._prepare_numerical_input(self.sample_df)
        scaled = pipeline.scaler.transform(num_arr)

        self.assertAlmostEqual(scaled[:, 0].min(), 0.0)
        self.assertAlmostEqual(scaled[:, 0].max(), 1.0)
        self.assertAlmostEqual(scaled[:, 1].min(), 0.0)
        self.assertAlmostEqual(scaled[:, 1].max(), 1.0)

    def test_no_nan_no_inf(self):
        pipeline = TurismoFeaturePipeline(max_features=15)
        X = pipeline.fit_transform(self.sample_df)

        self.assertFalse(np.isnan(X.data).any(), "La matriz no debe contener NaN")
        self.assertFalse(np.isinf(X.data).any(), "La matriz no debe contener Inf")

    def test_handle_unknown_categories_in_inference(self):
        pipeline = TurismoFeaturePipeline(max_features=10)
        pipeline.fit(self.sample_df)

        # Simular consulta de usuario con categoría y provincia desconocidas
        user_query = pd.DataFrame([{
            "categoria": "SITIOS NATURALES",
            "tipo": "CAIDAS DE AGUA",
            "subtipo": "CATARATAS",
            "etiquetas_interes": "aventura",
            "descripcion_corta": "catarata",
            "nivel_dificultad": "Extrema",       # Categoría desconocida
            "provincia": "LIMA",                 # Provincia no perteneciente a San Martín
            "publico_recomendado": "Solitarios", # Público desconocido
            "duracion_estimada_horas": 2.0,
            "costo_referencial_pen": 10.0,
        }])

        X_user = pipeline.transform(user_query)
        self.assertEqual(X_user.shape[0], 1)
        self.assertEqual(X_user.shape[1], len(pipeline.get_feature_names_out()))
        self.assertFalse(np.isnan(X_user.data).any())

    def test_save_and_load_pipeline(self):
        pipeline = TurismoFeaturePipeline(max_features=15)
        pipeline.fit(self.sample_df)
        X_orig = pipeline.transform(self.sample_df)

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            pipeline.save(tmp_path)
            loaded_pipeline = TurismoFeaturePipeline.load(tmp_path)
            X_loaded = loaded_pipeline.transform(self.sample_df)

            self.assertEqual(X_orig.shape, X_loaded.shape)
            diff = np.abs((X_orig - X_loaded).data)
            self.assertTrue(len(diff) == 0 or np.all(diff < 1e-7))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_end_to_end_real_data(self):
        clean_dataset = "data/processed/dataset_limpio.csv"
        if not Path(clean_dataset).exists():
            self.skipTest("Dataset limpio data/processed/dataset_limpio.csv no disponible")

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tmp_mat:
            tmp_mat_path = Path(tmp_mat.name)
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp_pip:
            tmp_pip_path = Path(tmp_pip.name)

        try:
            X_global, pipeline, metrics = run_feature_engineering(
                input_path=clean_dataset,
                output_matrix_path=tmp_mat_path,
                output_pipeline_path=tmp_pip_path,
                max_features=120,
            )

            # Validar 297 atractivos x 139 columnas
            self.assertEqual(X_global.shape, (297, 139))
            self.assertEqual(metrics["dimensiones_X_global"]["filas"], 297)
            self.assertEqual(metrics["dimensiones_X_global"]["columnas"], 139)
            self.assertFalse(metrics["tiene_nan"])
            self.assertFalse(metrics["tiene_inf"])

            # Validar lectura desde archivo NPZ guardado
            loaded_mat = sp.load_npz(tmp_mat_path)
            self.assertEqual(loaded_mat.shape, (297, 139))
            self.assertTrue(sp.isspmatrix_csr(loaded_mat))
        finally:
            if tmp_mat_path.exists():
                tmp_mat_path.unlink()
            if tmp_pip_path.exists():
                tmp_pip_path.unlink()


if __name__ == "__main__":
    unittest.main()
