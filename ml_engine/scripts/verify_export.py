#!/usr/bin/env python3
"""
Script de Verificación y Auditoría de Producción - TurismoIA San Martín
======================================================================
Fase 6: Control de calidad del artefacto serializado 'models/modelo_recomendador_sanmartin.pkl'.

Audita:
1. Tamaño del archivo en disco (< 5 MB).
2. Tiempo de carga en memoria (< 300 ms).
3. Latencia de inferencia completa (< 20 ms).
4. Autonomía e integridad matemática y estructural del artefacto.
5. 100% de cumplimiento en filtros duros y calidad del payload JSON.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
import sklearn

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def audit_model_artifact(
    model_path: str | Path = "models/modelo_recomendador_sanmartin.pkl",
    n_iterations: int = 50,
) -> dict[str, Any]:
    """
    Ejecuta las pruebas de rendimiento, memoria y latencia sobre el artefacto serializado.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Artefacto de modelo no encontrado en: {path}")

    # 1. Auditoría de Tamaño en Disco
    size_bytes = path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_bytes / (1024 * 1024)
    size_ok = size_mb < 5.0

    # 2. Auditoría de Tiempo de Carga en Memoria
    t_start_load = time.perf_counter()
    bundle = joblib.load(path)
    t_load_ms = (time.perf_counter() - t_start_load) * 1000
    load_ok = t_load_ms < 300.0

    # 3. Verificación de Contenido Estructural
    required_keys = [
        "version",
        "feature_pipeline",
        "kmeans",
        "X_global",
        "catalogo",
        "cluster_metadata",
    ]
    missing_keys = [k for k in required_keys if k not in bundle]
    structure_ok = len(missing_keys) == 0

    n_recursos = len(bundle["catalogo"])
    n_features = bundle["X_global"].shape[1]
    n_clusters = bundle["kmeans"].n_clusters

    # 4. Auditoría de Latencia de Inferencia (InferenceEngine)
    from src.inference import InferenceEngine

    engine = InferenceEngine(model_path=path)

    test_profile = {
        "intereses": "cataratas aventura selva naturaleza",
        "tiempo_disponible_horas": 4.0,
        "presupuesto_max_pen": 30.0,
        "nivel_dificultad": "Baja",
        "provincia": "SAN MARTIN",
        "publico": "Amigos",
    }

    # Warm-up run
    _ = engine.predict_top_n(test_profile, top_n=5)

    latencies = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        _ = engine.predict_top_n(test_profile, top_n=5)
        latencies.append((time.perf_counter() - t0) * 1000)

    avg_latency = float(np.mean(latencies))
    min_latency = float(np.min(latencies))
    max_latency = float(np.max(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    latency_ok = avg_latency < 20.0

    # 5. Validación del Payload Resultante y Filtros Duros
    recs = engine.predict_top_n(test_profile, top_n=5)
    payload_ok = len(recs) == 5

    required_fields = [
        "ranking",
        "id_recurso",
        "nombre_recurso",
        "categoria",
        "provincia",
        "duracion_estimada_horas",
        "costo_referencial_pen",
        "nivel_dificultad",
        "afinidad_pct",
        "cluster_id",
        "cluster_label",
        "justificacion",
    ]
    fields_ok = all(all(f in r for f in required_fields) for r in recs)

    cumple_tiempo = all(r["duracion_estimada_horas"] <= 4.0 for r in recs)
    cumple_costo = all(r["costo_referencial_pen"] <= 30.0 for r in recs)
    cumple_prov = all(r["provincia"].upper() == "SAN MARTIN" for r in recs)
    filters_ok = cumple_tiempo and cumple_costo and cumple_prov

    all_passed = (
        size_ok
        and load_ok
        and structure_ok
        and latency_ok
        and payload_ok
        and fields_ok
        and filters_ok
    )

    return {
        "model_path": str(path),
        "version": bundle.get("version", "1.0.0"),
        "created_at": bundle.get("created_at", ""),
        "size_bytes": size_bytes,
        "size_kb": size_kb,
        "size_mb": size_mb,
        "size_ok": size_ok,
        "load_time_ms": t_load_ms,
        "load_ok": load_ok,
        "structure_ok": structure_ok,
        "missing_keys": missing_keys,
        "n_recursos": n_recursos,
        "n_features": n_features,
        "n_clusters": n_clusters,
        "n_iterations": n_iterations,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "p95_latency_ms": p95_latency,
        "latency_ok": latency_ok,
        "payload_ok": payload_ok,
        "fields_ok": fields_ok,
        "filters_ok": filters_ok,
        "all_passed": all_passed,
        "sample_top1": recs[0] if recs else None,
    }


def print_verification_report(metrics: dict[str, Any]) -> None:
    """
    Muestra en consola el informe de verificación y auditoría del modelo.
    """
    sep = "=" * 85
    subsep = "-" * 85

    print("\n" + sep)
    print("      TURISMO IA SAN MARTÍN (ML ENGINE) - AUDITORÍA Y VERIFICACIÓN DE EXPORTACIÓN")
    print(sep)
    print(f"[*] Artefacto evaluado:  {metrics['model_path']}")
    print(f"[*] Versión empaquetada: v{metrics['version']} ({metrics['created_at']})")
    print(subsep)

    print("1. AUDITORÍA DE TAMAÑO Y ALMACENAMIENTO:")
    status_size = "[PASS]" if metrics["size_ok"] else "[FAIL]"
    print(f"   - Tamaño en disco:     {metrics['size_kb']:.2f} KB ({metrics['size_mb']:.3f} MB)  {status_size} (Requisito: < 5.0 MB)")
    print(f"   - Total atractivos:    {metrics['n_recursos']} recursos turísticos")
    print(f"   - Dimensionalidad:     {metrics['n_features']} características vectoriales")
    print(f"   - Estructura bundle:   {'[PASS] Todos los campos presentes' if metrics['structure_ok'] else '[FAIL] Faltan: ' + str(metrics['missing_keys'])}")
    print(subsep)

    print("2. RENDIMIENTO DE CARGA EN MEMORIA (COLD/WARM LOAD):")
    status_load = "[PASS]" if metrics["load_ok"] else "[FAIL]"
    print(f"   - Tiempo de carga:     {metrics['load_time_ms']:.2f} ms  {status_load} (Requisito: < 300 ms)")
    print(subsep)

    print("3. LATENCIA DE INFERENCIA EN PRODUCCIÓN (100% AUTÓNOMO):")
    status_lat = "[PASS]" if metrics["latency_ok"] else "[FAIL]"
    print(f"   - Evaluado sobre:      {metrics['n_iterations']} inferencias consecutivas")
    print(f"   - Latencia promedio:   {metrics['avg_latency_ms']:.2f} ms  {status_lat} (Requisito: < 20.0 ms)")
    print(f"   - Rango observado:     [{metrics['min_latency_ms']:.2f} ms - {metrics['max_latency_ms']:.2f} ms]")
    print(f"   - Percentil 95 (P95):  {metrics['p95_latency_ms']:.2f} ms")
    print(subsep)

    print("4. CALIDAD Y FORMATO DEL PAYLOAD (FASTAPI READY):")
    status_filters = "[PASS] 100% cumplimiento" if metrics["filters_ok"] else "[FAIL] Violación de filtros"
    print(f"   - Estructura JSON:     {'[PASS] 5 registros con esquema completo' if metrics['payload_ok'] and metrics['fields_ok'] else '[FAIL]'}")
    print(f"   - Filtros duros:       {status_filters}")
    if metrics["sample_top1"]:
        s = metrics["sample_top1"]
        print(f"   - Recomendación #1:    {s['nombre_recurso']} ({s['provincia']}) | Afinidad: {s['afinidad_pct']}% | S/{s['costo_referencial_pen']}")
        print(f"     -> Justificación:    {s['justificacion']}")
    print(subsep)

    final_verdict = "APROBADO PARA PRODUCCIÓN (LISTO PARA FASTAPI)" if metrics["all_passed"] else "FALLÓ LA AUDITORÍA"
    print(f"[*] DICTAMEN FINAL:       {final_verdict}")
    print(sep + "\n")


def main() -> None:
    """
    Punto de entrada CLI.
    """
    parser = argparse.ArgumentParser(
        description="Fase 6: Verificación de Carga y Rendimiento del Artefacto de Inferencia",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-m",
        "--model",
        default="models/modelo_recomendador_sanmartin.pkl",
        help="Ruta al artefacto serializado de producción",
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=50,
        help="Número de iteraciones para la medición de latencia",
    )

    args = parser.parse_args()

    try:
        metrics = audit_model_artifact(model_path=args.model, n_iterations=args.iterations)
        print_verification_report(metrics)
        if not metrics["all_passed"]:
            sys.exit(1)
    except Exception as exc:
        logger.error("Error crítico durante la auditoría: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
