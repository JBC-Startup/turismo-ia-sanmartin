#!/usr/bin/env python3
"""
Módulo de Ingesta y Limpieza de Datos - TurismoIA San Martín
=============================================================
Responsable de procesar el inventario de recursos turísticos desde el formato
crudo de Excel (data/raw/turismo_san_martin.xlsx) y generar un dataset validado,
estandarizado y libre de valores nulos matemáticos (data/processed/dataset_limpio.csv).

Sigue los lineamientos de la Fase 2 del sistema de recomendación turística.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def normalize_column_name(col_name: str) -> str:
    """
    Normaliza el nombre de una columna:
    - Pasa a minúsculas.
    - Elimina tildes y diacríticos (ej. 'duración' -> 'duracion').
    - Reemplaza espacios y guiones por guiones bajos.
    - Elimina caracteres que no sean alfanuméricos ni guiones bajos.
    - Colapsa múltiples guiones bajos en uno solo y quita guiones en extremos.
    """
    col = str(col_name).strip()
    col = "".join(
        c for c in unicodedata.normalize("NFD", col)
        if unicodedata.category(c) != "Mn"
    )
    col = col.lower()
    col = re.sub(r"[\s\-]+", "_", col)
    col = re.sub(r"[^a-z0-9_]", "", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col


def normalize_column_names(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Estandariza los nombres de todas las columnas del DataFrame.
    Retorna el DataFrame con nuevas cabeceras y un diccionario de mapeo.
    """
    col_mapping = {col: normalize_column_name(col) for col in df.columns}
    df_normalized = df.rename(columns=col_mapping)
    return df_normalized, col_mapping


def filter_unsuitable_records(
    df: pd.DataFrame,
    excluded_statuses: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Filtro de calidad administrativa:
    - Excluye atractivos con estado 'OBSERVADO' (insensible a mayúsculas/minúsculas).
    - Excluye atractivos con código de estado 3 si estuviera presente.
    - Excluye registros que carezcan de identificador o nombre esencial.

    Retorna:
    - df_valid: Registros aptos para catálogo público.
    - df_excluded: Registros descartados con metadatos del motivo.
    - stats: Métricas cuantitativas del filtrado.
    """
    if excluded_statuses is None:
        excluded_statuses = ["OBSERVADO"]

    norm_excluded = {s.strip().upper() for s in excluded_statuses}

    # Máscara para estado observado
    if "estado" in df.columns:
        status_clean = df["estado"].astype(str).str.strip().str.upper()
        mask_observed = status_clean.isin(norm_excluded)
    else:
        mask_observed = pd.Series(False, index=df.index)

    # Máscara para código de estado (3 = OBSERVADO)
    if "codigo_estado" in df.columns:
        mask_code_observed = pd.to_numeric(df["codigo_estado"], errors="coerce") == 3
        mask_observed = mask_observed | mask_code_observed

    # Máscara para registros sin identificador o nombre
    mask_invalid_id = pd.Series(False, index=df.index)
    if "id_recurso" in df.columns:
        id_str = df["id_recurso"].astype(str).str.strip().str.lower()
        mask_invalid_id = id_str.isin(["", "nan", "none", "null"])

    mask_invalid_name = pd.Series(False, index=df.index)
    if "nombre_recurso" in df.columns:
        name_str = df["nombre_recurso"].astype(str).str.strip().str.lower()
        mask_invalid_name = name_str.isin(["", "nan", "none", "null"])

    mask_discard = mask_observed | mask_invalid_id | mask_invalid_name

    df_valid = df[~mask_discard].copy().reset_index(drop=True)
    df_excluded = df[mask_discard].copy().reset_index(drop=True)

    stats = {
        "total_inicial": len(df),
        "total_descartados": int(mask_discard.sum()),
        "descartados_observado": int(mask_observed.sum()),
        "descartados_id_invalido": int(mask_invalid_id.sum()),
        "descartados_nombre_invalido": int(mask_invalid_name.sum()),
        "total_validos": len(df_valid),
        "ids_descartados": df.loc[mask_discard, "id_recurso"].tolist() if "id_recurso" in df.columns else [],
    }

    return df_valid, df_excluded, stats


def clean_semantic_fields(
    df: pd.DataFrame,
    semantic_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """
    Imputación de campos semánticos y textuales:
    - descripcion_corta, etiquetas_interes, categoria, tipo, subtipo,
      ruta_acceso_desde_tarapoto, referencia_ubicacion, horario_referencial,
      temporada_ideal, imagen_url, url_fuente, etc.
    - Reemplaza valores nulos o cadenas pseudo-nulas por texto vacío ("").
    - Asegura tipo string limpio sin espacios extras.
    """
    df_out = df.copy()

    if semantic_columns is None:
        semantic_columns = [
            "descripcion_corta",
            "etiquetas_interes",
            "categoria",
            "tipo",
            "subtipo",
            "ruta_acceso_desde_tarapoto",
            "referencia_ubicacion",
            "horario_referencial",
            "temporada_ideal",
            "imagen_url",
            "url_fuente",
            "nombre_recurso",
        ]

    nulls_imputed: dict[str, int] = {}
    null_literals = {"nan", "none", "null", "n/a", "na", "<na>"}

    for col in semantic_columns:
        if col in df_out.columns:
            # Detección de nulos o cadenas vacías / pseudo-nulas
            series_raw = df_out[col]
            is_na = series_raw.isna()
            as_str = series_raw.astype(str).str.strip()
            is_null_str = as_str.str.lower().isin(null_literals) | (as_str == "")
            combined_mask = is_na | is_null_str

            count_imputed = int(combined_mask.sum())
            nulls_imputed[col] = count_imputed

            # Asignación limpia
            cleaned_series = as_str.copy()
            cleaned_series[combined_mask] = ""
            df_out[col] = cleaned_series.astype(str)

    return df_out, nulls_imputed


def clean_categorical_fields(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """
    Imputación y normalización de variables categóricas:
    - provincia: formato mayúsculas, imputar faltantes con categoría por defecto lógica ('SAN MARTIN').
    - distrito: formato mayúsculas, asegurar sin espacios laterales.
    - departamento: formato mayúsculas ('SAN MARTIN').
    - nivel_dificultad: estandarizado ('Baja', 'Media', 'Alta'). Imputar faltantes con 'Media'.
    - publico_recomendado: estandarizado ('Todos', 'Amigos', 'Pareja', 'Familia'). Imputar con 'Todos'.
    - accesibilidad_reducida: estandarizado ('Si', 'No', 'Parcial'). Imputar faltantes con 'No'.
    """
    df_out = df.copy()
    imputed_counts: dict[str, int] = {}

    # 1. Normalización de provincia
    if "provincia" in df_out.columns:
        prov_series = df_out["provincia"].astype(str).str.strip().str.upper()
        invalid_mask = prov_series.isna() | prov_series.isin(["", "NAN", "NONE", "NULL"])
        imputed_counts["provincia"] = int(invalid_mask.sum())
        prov_series[invalid_mask] = "SAN MARTIN"
        df_out["provincia"] = prov_series

    # 2. Normalización de distrito
    if "distrito" in df_out.columns:
        dist_series = df_out["distrito"].astype(str).str.strip().str.upper()
        invalid_mask = dist_series.isna() | dist_series.isin(["", "NAN", "NONE", "NULL"])
        imputed_counts["distrito"] = int(invalid_mask.sum())
        dist_series[invalid_mask] = ""
        df_out["distrito"] = dist_series

    # 3. Normalización de departamento
    if "departamento" in df_out.columns:
        dep_series = df_out["departamento"].astype(str).str.strip().str.upper()
        invalid_mask = dep_series.isna() | dep_series.isin(["", "NAN", "NONE", "NULL"])
        imputed_counts["departamento"] = int(invalid_mask.sum())
        dep_series[invalid_mask] = "SAN MARTIN"
        df_out["departamento"] = dep_series

    # 4. Normalización de nivel_dificultad
    if "nivel_dificultad" in df_out.columns:
        raw_dif = df_out["nivel_dificultad"].astype(str).str.strip().str.lower()
        mapping_dif = {
            "baja": "Baja",
            "bajo": "Baja",
            "facil": "Baja",
            "media": "Media",
            "medio": "Media",
            "moderada": "Media",
            "moderado": "Media",
            "alta": "Alta",
            "alto": "Alta",
            "dificil": "Alta",
            "exigente": "Alta",
        }
        std_dif = raw_dif.map(mapping_dif)
        invalid_mask = std_dif.isna()
        imputed_counts["nivel_dificultad"] = int(invalid_mask.sum())
        std_dif[invalid_mask] = "Media"
        df_out["nivel_dificultad"] = std_dif

    # 5. Normalización de publico_recomendado
    if "publico_recomendado" in df_out.columns:
        raw_pub = df_out["publico_recomendado"].astype(str).str.strip().str.lower()
        mapping_pub = {
            "todos": "Todos",
            "todo publico": "Todos",
            "general": "Todos",
            "amigos": "Amigos",
            "amigo": "Amigos",
            "pareja": "Pareja",
            "parejas": "Pareja",
            "familia": "Familia",
            "familias": "Familia",
            "familiar": "Familia",
            "familiares": "Familia",
        }
        std_pub = raw_pub.map(mapping_pub)
        invalid_mask = std_pub.isna()
        imputed_counts["publico_recomendado"] = int(invalid_mask.sum())
        std_pub[invalid_mask] = "Todos"
        df_out["publico_recomendado"] = std_pub

    # 6. Normalización de accesibilidad_reducida
    if "accesibilidad_reducida" in df_out.columns:
        raw_acc = df_out["accesibilidad_reducida"].astype(str).str.strip().str.lower()
        mapping_acc = {
            "si": "Si",
            "sí": "Si",
            "s": "Si",
            "yes": "Si",
            "parcial": "Parcial",
            "p": "Parcial",
            "no": "No",
            "n": "No",
        }
        std_acc = raw_acc.map(mapping_acc)
        invalid_mask = std_acc.isna()
        imputed_counts["accesibilidad_reducida"] = int(invalid_mask.sum())
        std_acc[invalid_mask] = "No"
        df_out["accesibilidad_reducida"] = std_acc

    return df_out, imputed_counts


def clean_numerical_fields(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Imputación y conversión segura de variables numéricas a float:
    - duracion_estimada_horas: float, nulos imputados con la mediana de la columna (fallback: 2.0).
    - costo_referencial_pen: float, nulos imputados con 0.0 (acceso gratuito).
    - distancia_km_tarapoto: float, nulos imputados con la mediana (fallback: 115.0).
    - tiempo_viaje_horas_tarapoto: float, nulos imputados con la mediana (fallback: 2.0).
    - tiempo_total_tour_horas: float, nulos imputados con la mediana (fallback: 5.6).
    - latitud, longitud: float seguro.
    """
    df_out = df.copy()
    stats: dict[str, Any] = {}

    # 1. duracion_estimada_horas
    if "duracion_estimada_horas" in df_out.columns:
        dur_raw = pd.to_numeric(df_out["duracion_estimada_horas"], errors="coerce")
        dur_median = dur_raw.median()
        if pd.isna(dur_median):
            dur_median = 2.0
        n_imputed = int(dur_raw.isna().sum())
        dur_clean = dur_raw.fillna(dur_median).astype(float)
        # Asegurar no negatividad
        dur_clean = dur_clean.clip(lower=0.1)
        df_out["duracion_estimada_horas"] = dur_clean
        stats["duracion_estimada_horas"] = {
            "nulos_imputados": n_imputed,
            "mediana_imputacion": float(dur_median),
            "min": float(dur_clean.min()),
            "max": float(dur_clean.max()),
        }

    # 2. costo_referencial_pen
    if "costo_referencial_pen" in df_out.columns:
        cost_raw = pd.to_numeric(df_out["costo_referencial_pen"], errors="coerce")
        n_imputed = int(cost_raw.isna().sum())
        cost_clean = cost_raw.fillna(0.0).astype(float)
        cost_clean = cost_clean.clip(lower=0.0)
        df_out["costo_referencial_pen"] = cost_clean
        stats["costo_referencial_pen"] = {
            "nulos_imputados": n_imputed,
            "valor_defecto": 0.0,
            "min": float(cost_clean.min()),
            "max": float(cost_clean.max()),
            "mediana": float(cost_clean.median()),
        }

    # 3. distancia_km_tarapoto
    if "distancia_km_tarapoto" in df_out.columns:
        dist_raw = pd.to_numeric(df_out["distancia_km_tarapoto"], errors="coerce")
        dist_median = dist_raw.median()
        if pd.isna(dist_median):
            dist_median = 115.0
        n_imputed = int(dist_raw.isna().sum())
        dist_clean = dist_raw.fillna(dist_median).astype(float).clip(lower=0.0)
        df_out["distancia_km_tarapoto"] = dist_clean
        stats["distancia_km_tarapoto"] = {
            "nulos_imputados": n_imputed,
            "mediana_imputacion": float(dist_median),
            "min": float(dist_clean.min()),
            "max": float(dist_clean.max()),
        }

    # 4. tiempo_viaje_horas_tarapoto
    if "tiempo_viaje_horas_tarapoto" in df_out.columns:
        viaje_raw = pd.to_numeric(df_out["tiempo_viaje_horas_tarapoto"], errors="coerce")
        viaje_median = viaje_raw.median()
        if pd.isna(viaje_median):
            viaje_median = 2.0
        n_imputed = int(viaje_raw.isna().sum())
        viaje_clean = viaje_raw.fillna(viaje_median).astype(float).clip(lower=0.0)
        df_out["tiempo_viaje_horas_tarapoto"] = viaje_clean
        stats["tiempo_viaje_horas_tarapoto"] = {
            "nulos_imputados": n_imputed,
            "mediana_imputacion": float(viaje_median),
            "min": float(viaje_clean.min()),
            "max": float(viaje_clean.max()),
        }

    # 5. tiempo_total_tour_horas
    if "tiempo_total_tour_horas" in df_out.columns:
        total_raw = pd.to_numeric(df_out["tiempo_total_tour_horas"], errors="coerce")
        total_median = total_raw.median()
        if pd.isna(total_median):
            total_median = 5.6
        n_imputed = int(total_raw.isna().sum())
        total_clean = total_raw.fillna(total_median).astype(float).clip(lower=0.1)
        df_out["tiempo_total_tour_horas"] = total_clean
        stats["tiempo_total_tour_horas"] = {
            "nulos_imputados": n_imputed,
            "mediana_imputacion": float(total_median),
            "min": float(total_clean.min()),
            "max": float(total_clean.max()),
        }

    # 6. Coordenadas geográficas
    for coord_col in ["latitud", "longitud"]:
        if coord_col in df_out.columns:
            c_raw = pd.to_numeric(df_out[coord_col], errors="coerce")
            df_out[coord_col] = c_raw.astype(float)

    return df_out, stats


def export_clean_dataset(df: pd.DataFrame, output_path: str | Path) -> Path:
    """
    Exporta el DataFrame procesado a un archivo CSV en codificación UTF-8 sin índice.
    Crea las carpetas contenedoras si no existen.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def run_ingestion_pipeline(
    raw_path: str | Path,
    output_path: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Ejecuta el pipeline integral de ingesta y limpieza:
    1. Carga del archivo Excel.
    2. Estandarización de nombres de columnas.
    3. Filtrado de registros administrativos ("OBSERVADO").
    4. Limpieza e imputación de campos semánticos.
    5. Normalización e imputación de variables categóricas.
    6. Conversión e imputación de variables numéricas.
    7. Exportación a CSV limpio (si se especifica output_path).

    Retorna el DataFrame limpio y un diccionario detallado de métricas.
    """
    raw_file = Path(raw_path)
    if not raw_file.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos crudos: {raw_file}")

    logger.info("Iniciando lectura de datos desde: %s", raw_file)
    df_raw = pd.read_excel(raw_file)
    total_inicial = len(df_raw)
    cols_iniciales = len(df_raw.columns)
    logger.info("Archivo cargado con éxito. Filas: %d, Columnas: %d", total_inicial, cols_iniciales)

    # 1. Normalización de cabeceras
    df_norm, col_map = normalize_column_names(df_raw)

    # 2. Filtrado administrativo
    df_filtered, df_excluded, filter_stats = filter_unsuitable_records(df_norm)
    logger.info(
        "Filtro administrativo completado. Válidos: %d, Descartados: %d",
        filter_stats["total_validos"],
        filter_stats["total_descartados"],
    )

    # 3. Limpieza de texto semántico
    df_clean_sem, sem_stats = clean_semantic_fields(df_filtered)

    # 4. Limpieza de variables categóricas
    df_clean_cat, cat_stats = clean_categorical_fields(df_clean_sem)

    # 5. Limpieza de variables numéricas
    df_final, num_stats = clean_numerical_fields(df_clean_cat)

    # Verificación final de nulos
    null_audit = df_final.isna().sum()
    total_nulls_remaining = int(null_audit.sum())

    # 6. Exportación opcional
    exported_file_path: Path | None = None
    file_size_bytes: int = 0
    if output_path is not None:
        exported_file_path = export_clean_dataset(df_final, output_path)
        file_size_bytes = exported_file_path.stat().st_size
        logger.info("Dataset limpio exportado a: %s (%.1f KB)", exported_file_path, file_size_bytes / 1024)

    metrics: dict[str, Any] = {
        "raw_path": str(raw_file),
        "output_path": str(exported_file_path) if exported_file_path else None,
        "total_inicial": total_inicial,
        "columnas_iniciales": cols_iniciales,
        "filtro_stats": filter_stats,
        "sem_imputaciones": sem_stats,
        "cat_imputaciones": cat_stats,
        "num_stats": num_stats,
        "dimensiones_finales": {"filas": len(df_final), "columnas": len(df_final.columns)},
        "nulos_remanentes": total_nulls_remaining,
        "tamano_bytes": file_size_bytes,
        "distribucion_dificultad": df_final["nivel_dificultad"].value_counts().to_dict()
        if "nivel_dificultad" in df_final.columns
        else {},
        "distribucion_publico": df_final["publico_recomendado"].value_counts().to_dict()
        if "publico_recomendado" in df_final.columns
        else {},
        "distribucion_accesibilidad": df_final["accesibilidad_reducida"].value_counts().to_dict()
        if "accesibilidad_reducida" in df_final.columns
        else {},
        "top_provincias": df_final["provincia"].value_counts().head(5).to_dict()
        if "provincia" in df_final.columns
        else {},
    }

    return df_final, metrics


def print_summary_report(metrics: dict[str, Any]) -> None:
    """
    Imprime un informe exhaustivo y formateado en la terminal.
    """
    sep = "=" * 80
    subsep = "-" * 80

    print("\n" + sep)
    print("       TURISMO IA SAN MARTÍN (ML ENGINE) - INGESTA Y LIMPIEZA DE DATOS")
    print(sep)
    print(f"[*] Origen:  {metrics['raw_path']}")
    if metrics["output_path"]:
        print(f"[*] Destino: {metrics['output_path']} ({metrics['tamano_bytes'] / 1024:.2f} KB)")
    print(subsep)

    print("1. BALANCE DE REGISTROS:")
    print(f"   - Total inicial leídos:          {metrics['total_inicial']:4d}")
    f_stats = metrics["filtro_stats"]
    print(f"   - Registros descartados:         {f_stats['total_descartados']:4d}")
    print(f"     * Motivo OBSERVADO:            {f_stats['descartados_observado']:4d}")
    if f_stats["ids_descartados"]:
        sample_ids = ", ".join(f_stats["ids_descartados"][:6])
        if len(f_stats["ids_descartados"]) > 6:
            sample_ids += f"... (+{len(f_stats['ids_descartados']) - 6} más)"
        print(f"     * IDs excluidos:               [{sample_ids}]")
    print(f"   - Registros limpios resultantes: {metrics['dimensiones_finales']['filas']:4d}")
    print(subsep)

    print("2. DIMENSIONES FINALES:")
    dims = metrics["dimensiones_finales"]
    print(f"   - Filas:    {dims['filas']}")
    print(f"   - Columnas: {dims['columnas']}")
    print(f"   - Valores nulos remanentes: {metrics['nulos_remanentes']}")
    print(subsep)

    print("3. RESUMEN DE VARIABLES CLAVE (DATASET LIMPIO):")
    # Numéricas
    num = metrics.get("num_stats", {})
    if "duracion_estimada_horas" in num:
        d = num["duracion_estimada_horas"]
        print(f"   - Duración estimada (horas):    Mediana: {d['mediana_imputacion']:.2f}h | Rango: [{d['min']:.1f}h - {d['max']:.1f}h]")
    if "costo_referencial_pen" in num:
        c = num["costo_referencial_pen"]
        print(f"   - Costo referencial (PEN):      Mediana: {c['mediana']:.2f} soles | Rango: [{c['min']:.2f} - {c['max']:.2f}] soles")
    if "distancia_km_tarapoto" in num:
        dk = num["distancia_km_tarapoto"]
        print(f"   - Distancia desde Tarapoto:     Mediana: {dk['mediana_imputacion']:.1f} km | Rango: [{dk['min']:.1f} - {dk['max']:.1f}] km")
    if "tiempo_total_tour_horas" in num:
        tt = num["tiempo_total_tour_horas"]
        print(f"   - Tiempo total tour (horas):    Mediana: {tt['mediana_imputacion']:.2f}h | Rango: [{tt['min']:.1f}h - {tt['max']:.1f}h]")

    # Categóricas
    print("   - Nivel de Dificultad:          " + ", ".join(f"{k}: {v}" for k, v in metrics["distribucion_dificultad"].items()))
    print("   - Accesibilidad Reducida:       " + ", ".join(f"{k}: {v}" for k, v in metrics["distribucion_accesibilidad"].items()))
    print("   - Público Recomendado:          " + ", ".join(f"{k}: {v}" for k, v in metrics["distribucion_publico"].items()))
    print("   - Top 5 Provincias:             " + ", ".join(f"{k} ({v})" for k, v in metrics["top_provincias"].items()))
    print(sep + "\n")


def main() -> None:
    """
    Punto de entrada de línea de comandos.
    """
    parser = argparse.ArgumentParser(
        description="Ingesta y limpieza de datos turísticos de San Martín (Fase 2)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        default="data/raw/turismo_san_martin.xlsx",
        help="Ruta al archivo crudo de Excel",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="data/processed/dataset_limpio.csv",
        help="Ruta de destino para el archivo CSV limpio",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Silencia la salida detallada en consola",
    )

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.WARNING)

    try:
        _, metrics = run_ingestion_pipeline(raw_path=args.input, output_path=args.output)
        if not args.quiet:
            print_summary_report(metrics)
    except Exception as exc:
        logger.error("Error crítico durante la ejecución del pipeline: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
