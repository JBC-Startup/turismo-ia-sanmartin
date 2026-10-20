"""
Pruebas unitarias para src/data_ingestion.py
============================================
Verifica:
1. Normalización de cabeceras.
2. Filtrado administrativo de estados inválidos.
3. Imputación y limpieza de campos semánticos y categóricos.
4. Conversión e imputación de variables numéricas.
5. Ejecución end-to-end y consistencia del archivo procesado.
"""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data_ingestion import (
    clean_categorical_fields,
    clean_numerical_fields,
    clean_semantic_fields,
    export_clean_dataset,
    filter_unsuitable_records,
    normalize_column_name,
    normalize_column_names,
    run_ingestion_pipeline,
)


class TestDataIngestion(unittest.TestCase):

    def test_normalize_column_name(self):
        cases = {
            "ID_RECURSO": "id_recurso",
            "NOMBRE RECURSO": "nombre_recurso",
            "  duración_estimada_horas  ": "duracion_estimada_horas",
            "Costo-Referencial (PEN)": "costo_referencial_pen",
            "ETIQUETAS__INTERÉS": "etiquetas_interes",
            "UBIGEO": "ubigeo",
        }
        for original, expected in cases.items():
            normalized = normalize_column_name(original)
            self.assertEqual(normalized, expected, f"Fallo al normalizar '{original}': obtenido '{normalized}' != '{expected}'")

    def test_filter_unsuitable_records(self):
        sample_data = pd.DataFrame({
            "id_recurso": ["REC-1", "REC-2", "REC-3", "REC-4"],
            "nombre_recurso": ["Atractivo 1", "Atractivo 2", "Atractivo 3", "Atractivo 4"],
            "estado": ["PUBLICADO", "observado", "REGISTRADO", "  OBSERVADO  "],
            "codigo_estado": [1, 3, 2, 3],
        })
        df_valid, df_excluded, stats = filter_unsuitable_records(sample_data)

        self.assertEqual(len(df_valid), 2)
        self.assertEqual(len(df_excluded), 2)
        self.assertEqual(stats["total_descartados"], 2)
        self.assertEqual(df_valid["id_recurso"].tolist(), ["REC-1", "REC-3"])
        self.assertEqual(df_excluded["id_recurso"].tolist(), ["REC-2", "REC-4"])

    def test_clean_semantic_fields(self):
        sample_data = pd.DataFrame({
            "descripcion_corta": ["Hermosa catarata", None, "   ", "nan"],
            "etiquetas_interes": ["naturaleza aventura", "NULL", "cultura", None],
        })
        df_clean, stats = clean_semantic_fields(sample_data)

        self.assertEqual(df_clean.loc[0, "descripcion_corta"], "Hermosa catarata")
        self.assertEqual(df_clean.loc[1, "descripcion_corta"], "")
        self.assertEqual(df_clean.loc[2, "descripcion_corta"], "")
        self.assertEqual(df_clean.loc[3, "descripcion_corta"], "")

        self.assertEqual(df_clean.loc[1, "etiquetas_interes"], "")
        self.assertEqual(df_clean.loc[3, "etiquetas_interes"], "")

    def test_clean_categorical_fields(self):
        sample_data = pd.DataFrame({
            "provincia": ["  san martin  ", "moyobamba", None, "RIOJA"],
            "nivel_dificultad": ["baja", "MODERADA", "invalido", None],
            "publico_recomendado": ["amigos", "familiares", "DESCONOCIDO", None],
            "accesibilidad_reducida": ["sí", "parcial", "no", None],
        })
        df_clean, stats = clean_categorical_fields(sample_data)

        # Provincia en mayúsculas
        self.assertEqual(df_clean.loc[0, "provincia"], "SAN MARTIN")
        self.assertEqual(df_clean.loc[1, "provincia"], "MOYOBAMBA")
        self.assertEqual(df_clean.loc[2, "provincia"], "SAN MARTIN")  # Default

        # Nivel de dificultad estandarizado
        self.assertEqual(df_clean.loc[0, "nivel_dificultad"], "Baja")
        self.assertEqual(df_clean.loc[1, "nivel_dificultad"], "Media")
        self.assertEqual(df_clean.loc[2, "nivel_dificultad"], "Media")  # Default
        self.assertEqual(df_clean.loc[3, "nivel_dificultad"], "Media")  # Default

        # Público recomendado
        self.assertEqual(df_clean.loc[0, "publico_recomendado"], "Amigos")
        self.assertEqual(df_clean.loc[1, "publico_recomendado"], "Familia")
        self.assertEqual(df_clean.loc[2, "publico_recomendado"], "Todos")  # Default
        self.assertEqual(df_clean.loc[3, "publico_recomendado"], "Todos")  # Default

        # Accesibilidad reducida
        self.assertEqual(df_clean.loc[0, "accesibilidad_reducida"], "Si")
        self.assertEqual(df_clean.loc[1, "accesibilidad_reducida"], "Parcial")
        self.assertEqual(df_clean.loc[2, "accesibilidad_reducida"], "No")
        self.assertEqual(df_clean.loc[3, "accesibilidad_reducida"], "No")  # Default

    def test_clean_numerical_fields(self):
        sample_data = pd.DataFrame({
            "duracion_estimada_horas": [1.0, 2.0, 3.0, None, "no_num"],
            "costo_referencial_pen": [10.0, None, 20.0, "gratis", 0.0],
            "distancia_km_tarapoto": [50.0, 100.0, None, 150.0, 200.0],
        })
        df_clean, stats = clean_numerical_fields(sample_data)

        # Duración estimada: mediana de [1.0, 2.0, 3.0] es 2.0
        self.assertEqual(df_clean.loc[3, "duracion_estimada_horas"], 2.0)
        self.assertEqual(df_clean.loc[4, "duracion_estimada_horas"], 2.0)
        self.assertEqual(df_clean["duracion_estimada_horas"].dtype, float)

        # Costo referencial: nulos y no numéricos son 0.0
        self.assertEqual(df_clean.loc[1, "costo_referencial_pen"], 0.0)
        self.assertEqual(df_clean.loc[3, "costo_referencial_pen"], 0.0)
        self.assertEqual(df_clean["costo_referencial_pen"].dtype, float)

        # Distancia: mediana de [50, 100, 150, 200] es 125.0
        self.assertEqual(df_clean.loc[2, "distancia_km_tarapoto"], 125.0)

    def test_end_to_end_pipeline_with_real_data(self):
        raw_path = "data/raw/turismo_san_martin.xlsx"
        if not Path(raw_path).exists():
            self.skipTest("Archivo crudo no disponible para prueba de integración")

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            df_clean, metrics = run_ingestion_pipeline(raw_path, tmp_path)

            self.assertEqual(metrics["total_inicial"], 307)
            self.assertEqual(metrics["filtro_stats"]["total_descartados"], 10)
            self.assertEqual(len(df_clean), 297)
            self.assertEqual(metrics["nulos_remanentes"], 0)
            self.assertTrue(tmp_path.exists())
            self.assertGreater(tmp_path.stat().st_size, 100000)

            # Verificar tipos en archivo exportado
            df_reloaded = pd.read_csv(tmp_path)
            self.assertEqual(len(df_reloaded), 297)
            self.assertEqual(df_reloaded.isnull().sum().sum(), 0)
            self.assertIn("costo_referencial_pen", df_reloaded.columns)
            self.assertIn("duracion_estimada_horas", df_reloaded.columns)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
