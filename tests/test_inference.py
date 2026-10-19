"""
Pruebas unitarias para src/inference.py
=======================================
Verifica:
1. Carga limpia y autónoma del artefacto serializado.
2. Estructura y tipos del payload devuelto por predict_top_n (JSON-ready para FastAPI).
3. Cumplimiento estricto de filtros duros (tiempo y presupuesto).
4. Activación de fallback con relajación de provincia si no hay candidatos.
5. Latencia de inferencia ultrarrápida (< 20 ms).
6. Función predict_top_n a nivel de módulo con patrón Singleton.
"""

import time
import unittest
from pathlib import Path

from src.inference import InferenceEngine, get_inference_engine, predict_top_n


class TestInferenceEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model_path = "models/modelo_recomendador_sanmartin.pkl"
        if not Path(cls.model_path).exists():
            raise unittest.SkipTest(f"Artefacto de producción {cls.model_path} no encontrado.")
        cls.engine = InferenceEngine(model_path=cls.model_path)

    def test_engine_initialization_and_metadata(self):
        self.assertEqual(self.engine.version, "1.0.0")
        self.assertEqual(len(self.engine.catalogo), 297)
        self.assertEqual(self.engine.X_global.shape, (297, 139))
        self.assertIn(0, self.engine.cluster_metadata)
        self.assertIn(3, self.engine.cluster_metadata)

    def test_predict_top_n_structure_and_keys(self):
        perfil = {
            "intereses": "cataratas naturaleza cascadas",
            "tiempo_disponible_horas": 4.0,
            "presupuesto_max_pen": 30.0,
            "nivel_dificultad": "Baja",
            "provincia": "SAN MARTIN",
            "publico": "Amigos",
        }
        recs = self.engine.predict_top_n(perfil, top_n=5)

        self.assertEqual(len(recs), 5)
        expected_keys = {
            "ranking",
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
            "afinidad_pct",
            "cluster_id",
            "cluster_label",
            "justificacion",
            "imagen_url",
            "fallback_provincia",
        }

        for rank, r in enumerate(recs, start=1):
            self.assertEqual(r["ranking"], rank)
            self.assertTrue(expected_keys.issubset(r.keys()))
            self.assertIsInstance(r["afinidad_pct"], float)
            self.assertIsInstance(r["duracion_estimada_horas"], float)
            self.assertIsInstance(r["costo_referencial_pen"], float)
            self.assertIsInstance(r["cluster_id"], int)
            self.assertTrue(len(r["justificacion"]) > 10)

    def test_predict_top_n_hard_filters_compliance(self):
        perfil = {
            "intereses": "aventura trekking",
            "tiempo_disponible_horas": 3.0,
            "presupuesto_max_pen": 10.0,
            "provincia": "SAN MARTIN",
        }
        recs = self.engine.predict_top_n(perfil, top_n=5)

        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertLessEqual(r["duracion_estimada_horas"], 3.0)
            self.assertLessEqual(r["costo_referencial_pen"], 10.0)
            self.assertEqual(r["provincia"].upper(), "SAN MARTIN")
            self.assertFalse(r["fallback_provincia"])

    def test_predict_top_n_fallback(self):
        # Filtros imposibles para una provincia específica
        perfil_imposible = {
            "intereses": "paseo",
            "tiempo_disponible_horas": 0.5,
            "presupuesto_max_pen": 0.0,
            "provincia": "EL DORADO",
        }
        recs = self.engine.predict_top_n(perfil_imposible, top_n=3)

        if len(recs) > 0:
            self.assertTrue(recs[0]["fallback_provincia"])
            for r in recs:
                self.assertLessEqual(r["duracion_estimada_horas"], 0.5)
                self.assertLessEqual(r["costo_referencial_pen"], 0.0)

    def test_inference_latency_under_20ms(self):
        perfil = {
            "intereses": "cultura tradicion cafe",
            "tiempo_disponible_horas": 6.0,
            "presupuesto_max_pen": 50.0,
            "provincia": "LAMAS",
        }
        # Warmup
        _ = self.engine.predict_top_n(perfil, top_n=5)

        times = []
        for _ in range(25):
            t0 = time.perf_counter()
            _ = self.engine.predict_top_n(perfil, top_n=5)
            times.append((time.perf_counter() - t0) * 1000)

        avg_latency = sum(times) / len(times)
        self.assertLess(avg_latency, 20.0, f"Latencia promedio {avg_latency:.2f}ms excede el límite de 20ms")

    def test_module_level_predict_top_n_singleton(self):
        perfil = {
            "intereses": "lagunas selva",
            "tiempo_disponible_horas": 5.0,
            "presupuesto_max_pen": 25.0,
            "provincia": "Todas",
        }
        recs1 = predict_top_n(perfil, top_n=3)
        recs2 = predict_top_n(perfil, top_n=3)

        self.assertEqual(len(recs1), 3)
        self.assertEqual(len(recs2), 3)
        self.assertEqual(recs1[0]["id_recurso"], recs2[0]["id_recurso"])

        # Verificar que el singleton sea el mismo
        engine1 = get_inference_engine()
        engine2 = get_inference_engine()
        self.assertIs(engine1, engine2)


if __name__ == "__main__":
    unittest.main()
