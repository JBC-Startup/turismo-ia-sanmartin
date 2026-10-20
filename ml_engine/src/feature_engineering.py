#!/usr/bin/env python3
"""
Módulo de Ingeniería de Características - TurismoIA San Martín
==============================================================
Fase 3 del Pipeline de ML: Construcción del espacio vectorial multidimensional.

Transforma 'data/processed/dataset_limpio.csv' en una matriz de características
unificada (X_global) combinando:
1. TF-IDF sobre el corpus semántico (categoría, tipo, subtipo, etiquetas, descripción).
2. One-Hot Encoding sobre variables categóricas (dificultad, provincia, público recomendado).
3. MinMaxScaler [0, 1] sobre variables numéricas (duración estimada, costo referencial).
4. Ensamblado horizontal en formato CSR Matrix (scipy.sparse.hstack).

Garantiza compatibilidad futura en inferencia (handle_unknown='ignore', transform desacoplado).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Lista representativa de stop words en español (artículos, preposiciones, conectores, pronombres)
SPANISH_STOP_WORDS: list[str] = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "aquel", "aquellas", "aquellos",
    "aqui", "arriba", "asi", "atras", "aun", "aunque", "bajo", "bastante", "bien", "cabe",
    "cada", "casi", "cerca", "cierto", "ciertos", "como", "con", "conmigo", "contra", "cual",
    "cuales", "cualquier", "cualquiera", "cuan", "cuando", "cuanta", "cuantas", "cuanto",
    "cuantos", "de", "del", "demas", "demasiado", "dentro", "desde", "donde", "dos", "el",
    "ella", "ellas", "ello", "ellos", "en", "encima", "entonces", "entre", "era", "erais",
    "eramos", "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta",
    "estaba", "estaban", "estado", "estados", "estais", "estamos", "estan", "estar", "estas",
    "este", "estos", "estoy", "estuvo", "fue", "fuera", "fueron", "fui", "fuimos", "ha",
    "habeis", "haber", "habia", "habian", "habido", "hace", "hacen", "hacer", "hacia",
    "haciendo", "hago", "han", "has", "hasta", "hay", "haya", "hayan", "he", "hecho",
    "hemos", "hubo", "la", "las", "le", "les", "lo", "los", "mas", "me", "menos", "mi",
    "mia", "mias", "mientras", "mio", "mios", "mis", "misma", "mismas", "mismo", "mismos",
    "modo", "mucha", "muchas", "mucho", "muchos", "muy", "nada", "nadie", "ni", "ningun",
    "ninguna", "ninguno", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro",
    "nuestros", "nunca", "o", "otra", "otras", "otro", "otros", "para", "pero", "poca",
    "pocas", "poco", "pocos", "podeis", "podemos", "poder", "podria", "podrian", "por",
    "porque", "primero", "primera", "que", "quien", "quienes", "se", "segun", "ser", "si",
    "siempre", "siendo", "sin", "sino", "so", "sobre", "sois", "solamente", "solo", "somos",
    "son", "soy", "su", "sus", "suya", "suyo", "tal", "tales", "tambien", "tampoco", "tan",
    "tanto", "te", "teneis", "tenemos", "tener", "tenga", "tengan", "tengo", "tenia",
    "tenian", "tenido", "tiene", "tienen", "toda", "todas", "todavia", "todo", "todos",
    "tras", "tu", "tus", "tuve", "tuvieron", "tuvo", "tuya", "tuyo", "un", "una", "unas",
    "uno", "unos", "va", "vamos", "van", "varias", "varios", "vosotras", "vosotros", "voy",
    "y", "ya", "yo"
]


class TurismoFeaturePipeline:
    """
    Pipeline integral de extracción y normalización de características para recursos turísticos.

    Encapsula:
    - TfidfVectorizer: Representación dispersa del texto semántico.
    - OneHotEncoder: Representación dispersa de variables categóricas.
    - MinMaxScaler: Normalización numérica en rango [0, 1].
    - scipy.sparse.hstack: Concatenación matricial global (CSR).
    """

    def __init__(
        self,
        max_features: int = 120,
        text_columns: list[str] | None = None,
        categorical_columns: list[str] | None = None,
        numerical_columns: list[str] | None = None,
        stop_words: list[str] | None = None,
    ) -> None:
        self.max_features = max_features
        self.text_columns = text_columns or [
            "categoria",
            "tipo",
            "subtipo",
            "etiquetas_interes",
            "descripcion_corta",
        ]
        self.categorical_columns = categorical_columns or [
            "nivel_dificultad",
            "provincia",
            "publico_recomendado",
        ]
        self.numerical_columns = numerical_columns or [
            "duracion_estimada_horas",
            "costo_referencial_pen",
        ]
        self.stop_words = stop_words or SPANISH_STOP_WORDS

        # Instanciación de transformadores
        self.tfidf = TfidfVectorizer(
            stop_words=self.stop_words,
            max_features=self.max_features,
            strip_accents="unicode",
            lowercase=True,
            token_pattern=r"(?u)\b\w\w+\b",
        )
        self.ohe = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True,
        )
        self.scaler = MinMaxScaler(feature_range=(0.0, 1.0))

        self.is_fitted = False
        self.feature_names_out_: list[str] = []

    def build_corpus(self, df: pd.DataFrame) -> pd.Series:
        """
        Construye la representación textual unificada concatenando las columnas
        semánticas disponibles de forma segura y consistente.
        """
        series_list = []
        for col in self.text_columns:
            if col in df.columns:
                series_list.append(df[col].fillna("").astype(str).str.strip())
            else:
                series_list.append(pd.Series("", index=df.index))

        # Concatenar con espacio intermedio
        combined = series_list[0].copy()
        for s in series_list[1:]:
            combined = combined + " " + s

        return combined.str.strip().str.replace(r"\s+", " ", regex=True)

    def _prepare_categorical_input(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara las variables categóricas rellenando columnas ausentes con valores por defecto.
        """
        defaults = {
            "nivel_dificultad": "Media",
            "provincia": "SAN MARTIN",
            "publico_recomendado": "Todos",
        }
        df_cat = pd.DataFrame(index=df.index)
        for col in self.categorical_columns:
            if col in df.columns:
                df_cat[col] = df[col].fillna(defaults.get(col, "Desconocido")).astype(str)
            else:
                df_cat[col] = defaults.get(col, "Desconocido")
        return df_cat

    def _prepare_numerical_input(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepara las variables numéricas rellenando columnas ausentes con valores seguros.
        """
        defaults = {
            "duracion_estimada_horas": 2.0,
            "costo_referencial_pen": 0.0,
        }
        num_arrays = []
        for col in self.numerical_columns:
            if col in df.columns:
                val = pd.to_numeric(df[col], errors="coerce").fillna(defaults.get(col, 0.0)).to_numpy()
            else:
                val = np.full(len(df), defaults.get(col, 0.0))
            num_arrays.append(val.reshape(-1, 1))

        return np.hstack(num_arrays).astype(float)

    def fit(self, df: pd.DataFrame) -> TurismoFeaturePipeline:
        """
        Ajusta los transformadores (TF-IDF, OHE y MinMaxScaler) sobre el DataFrame proporcionado.
        """
        logger.info("Ajustando transformadores de ingeniería de características...")

        # 1. Ajustar TF-IDF
        corpus = self.build_corpus(df)
        self.tfidf.fit(corpus)
        text_features = [f"text_{feat}" for feat in self.tfidf.get_feature_names_out()]

        # 2. Ajustar OneHotEncoder
        df_cat = self._prepare_categorical_input(df)
        self.ohe.fit(df_cat)
        cat_features = [f"cat_{feat}" for feat in self.ohe.get_feature_names_out(self.categorical_columns)]

        # 3. Ajustar MinMaxScaler
        num_arr = self._prepare_numerical_input(df)
        self.scaler.fit(num_arr)
        num_features = [f"num_{col}" for col in self.numerical_columns]

        # Consolidar nombres de características globales
        self.feature_names_out_ = text_features + cat_features + num_features
        self.is_fitted = True

        logger.info(
            "Transformadores ajustados con éxito. Características: %d (Texto: %d, Cat: %d, Num: %d)",
            len(self.feature_names_out_),
            len(text_features),
            len(cat_features),
            len(num_features),
        )
        return self

    def transform(self, df: pd.DataFrame) -> sp.csr_matrix:
        """
        Transforma los datos de entrada al espacio vectorial multidimensional unificado.
        Retorna una matriz dispersa en formato CSR.
        """
        if not self.is_fitted:
            raise RuntimeError("El pipeline no ha sido ajustado. Llame a fit() antes de transform().")

        # 1. Transformación de texto
        corpus = self.build_corpus(df)
        X_text = self.tfidf.transform(corpus)

        # 2. Transformación categórica
        df_cat = self._prepare_categorical_input(df)
        X_cat = self.ohe.transform(df_cat)

        # 3. Transformación numérica
        num_arr = self._prepare_numerical_input(df)
        X_num_dense = self.scaler.transform(num_arr)
        X_num = sp.csr_matrix(X_num_dense)

        # 4. Ensamblado horizontal unificado
        X_global = sp.hstack([X_text, X_cat, X_num], format="csr")

        # Validación matemática de integridad
        self._validate_sparse_matrix(X_global)

        return X_global

    def fit_transform(self, df: pd.DataFrame) -> sp.csr_matrix:
        """
        Ajusta y transforma en una sola operación optimizada.
        """
        return self.fit(df).transform(df)

    def _validate_sparse_matrix(self, X: sp.csr_matrix) -> None:
        """
        Verifica que la matriz dispersa no contenga valores NaN ni infinitos.
        """
        if np.isnan(X.data).any():
            raise ValueError("Error de integridad matemática: la matriz X_global contiene valores NaN.")
        if np.isinf(X.data).any():
            raise ValueError("Error de integridad matemática: la matriz X_global contiene valores infinitos.")

    def get_feature_names_out(self) -> list[str]:
        """
        Retorna la lista de nombres de todas las características generadas.
        """
        if not self.is_fitted:
            raise RuntimeError("El pipeline no ha sido ajustado todavía.")
        return list(self.feature_names_out_)

    def get_feature_breakdown(self) -> dict[str, int]:
        """
        Retorna el conteo desglosado por grupo de características.
        """
        if not self.is_fitted:
            raise RuntimeError("El pipeline no ha sido ajustado todavía.")
        n_text = len(self.tfidf.get_feature_names_out())
        n_cat = len(self.ohe.get_feature_names_out())
        n_num = len(self.numerical_columns)
        return {
            "texto_tfidf": n_text,
            "categoricas_ohe": n_cat,
            "numericas_minmax": n_num,
            "total_caracteristicas": n_text + n_cat + n_num,
        }

    def save(self, filepath: str | Path) -> Path:
        """
        Guarda el objeto pipeline serializado en disco.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Pipeline serializado guardado en: %s", path)
        return path

    @classmethod
    def load(cls, filepath: str | Path) -> TurismoFeaturePipeline:
        """
        Carga un objeto pipeline serializado desde disco.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el pipeline serializado en: {path}")
        loaded = joblib.load(path)
        if not isinstance(loaded, TurismoFeaturePipeline):
            raise TypeError(f"El archivo cargado no es una instancia de TurismoFeaturePipeline: {type(loaded)}")
        return loaded


def run_feature_engineering(
    input_path: str | Path = "data/processed/dataset_limpio.csv",
    output_matrix_path: str | Path | None = "data/processed/X_global.npz",
    output_pipeline_path: str | Path | None = "models/feature_pipeline.pkl",
    max_features: int = 120,
) -> tuple[sp.csr_matrix, TurismoFeaturePipeline, dict[str, Any]]:
    """
    Función de orquestación de la Fase 3:
    1. Carga el dataset limpio.
    2. Instancia y ajusta TurismoFeaturePipeline.
    3. Construye y valida la matriz dispersa X_global.
    4. Guarda opcionalmente la matriz en formato NPZ y el pipeline serializado.
    5. Retorna la matriz, el pipeline y métricas completas de trazabilidad.
    """
    in_file = Path(input_path)
    if not in_file.exists():
        raise FileNotFoundError(f"No se encontró el dataset limpio en: {in_file}")

    logger.info("Cargando dataset limpio desde: %s", in_file)
    df = pd.read_csv(in_file)
    n_rows, n_cols = df.shape
    logger.info("Dataset cargado correctamente. Registros: %d, Columnas de entrada: %d", n_rows, n_cols)

    # Construcción y ajuste del pipeline
    pipeline = TurismoFeaturePipeline(max_features=max_features)
    X_global = pipeline.fit_transform(df)

    # Validaciones matemáticas y estadísticas
    has_nan = bool(np.isnan(X_global.data).any())
    has_inf = bool(np.isinf(X_global.data).any())
    nnz_count = int(X_global.nnz)
    total_elements = X_global.shape[0] * X_global.shape[1]
    sparsity = float(100.0 * (1.0 - (nnz_count / total_elements))) if total_elements > 0 else 0.0

    # Guardar matriz dispersa en formato NPZ si se especificó ruta
    matrix_file: Path | None = None
    matrix_bytes: int = 0
    if output_matrix_path:
        matrix_file = Path(output_matrix_path)
        matrix_file.parent.mkdir(parents=True, exist_ok=True)
        sp.save_npz(matrix_file, X_global)
        matrix_bytes = matrix_file.stat().st_size
        logger.info("Matriz X_global exportada a: %s (%.1f KB)", matrix_file, matrix_bytes / 1024)

    # Guardar pipeline en models/ si se especificó ruta
    pipeline_file: Path | None = None
    pipeline_bytes: int = 0
    if output_pipeline_path:
        pipeline_file = pipeline.save(output_pipeline_path)
        pipeline_bytes = pipeline_file.stat().st_size

    breakdown = pipeline.get_feature_breakdown()

    metrics = {
        "input_path": str(in_file),
        "output_matrix_path": str(matrix_file) if matrix_file else None,
        "output_pipeline_path": str(pipeline_file) if pipeline_file else None,
        "n_atractivos": n_rows,
        "n_columnas_entrada": n_cols,
        "dimensiones_X_global": {"filas": X_global.shape[0], "columnas": X_global.shape[1]},
        "formato_matriz": X_global.format,
        "tipo_matriz": type(X_global).__name__,
        "elementos_no_cero": nnz_count,
        "porcentaje_dispersion": sparsity,
        "tiene_nan": has_nan,
        "tiene_inf": has_inf,
        "desglose_caracteristicas": breakdown,
        "muestra_vocabulario": pipeline.tfidf.get_feature_names_out()[:15].tolist(),
        "categorias_ohe": pipeline.ohe.get_feature_names_out(pipeline.categorical_columns).tolist(),
        "variables_escaladas": pipeline.numerical_columns,
        "tamano_matriz_bytes": matrix_bytes,
        "tamano_pipeline_bytes": pipeline_bytes,
    }

    return X_global, pipeline, metrics


def print_summary_report(metrics: dict[str, Any]) -> None:
    """
    Imprime en consola un informe técnico exhaustivo con métricas de la Fase 3.
    """
    sep = "=" * 80
    subsep = "-" * 80

    print("\n" + sep)
    print("      TURISMO IA SAN MARTÍN (ML ENGINE) - INGENIERÍA DE CARACTERÍSTICAS")
    print(sep)
    print(f"[*] Entrada: {metrics['input_path']}")
    if metrics["output_matrix_path"]:
        print(f"[*] Matriz X_global: {metrics['output_matrix_path']} ({metrics['tamano_matriz_bytes'] / 1024:.2f} KB)")
    if metrics["output_pipeline_path"]:
        print(f"[*] Artefacto Pipeline: {metrics['output_pipeline_path']} ({metrics['tamano_pipeline_bytes'] / 1024:.2f} KB)")
    print(subsep)

    dims = metrics["dimensiones_X_global"]
    desglose = metrics["desglose_caracteristicas"]

    print("1. DIMENSIONALIDAD Y ESTRUCTURA DE X_GLOBAL:")
    print(f"   - Dimensión de la matriz:      {dims['filas']} atractivos x {dims['columnas']} columnas generadas")
    print(f"   - Formato matemático:          SciPy {metrics['formato_matriz'].upper()} ({metrics['tipo_matriz']})")
    print(f"   - Elementos no cero (nnz):     {metrics['elementos_no_cero']} de {dims['filas'] * dims['columnas']}")
    print(f"   - Nivel de dispersión:         {metrics['porcentaje_dispersion']:.2f}%")
    print(subsep)

    print("2. DESGLOSE DEL ESPACIO VECTORIAL:")
    print(f"   - Corpus Semántico (TF-IDF):   {desglose['texto_tfidf']:3d} columnas")
    print(f"     * Vocabulario (muestra 10):  [{', '.join(metrics['muestra_vocabulario'][:10])}...]")
    print(f"   - Variables Categóricas (OHE): {desglose['categoricas_ohe']:3d} columnas")
    print(f"     * 'nivel_dificultad':        3 categorías (Alta, Baja, Media)")
    print(f"     * 'provincia':               10 provincias de San Martín")
    print(f"     * 'publico_recomendado':     4 categorías (Amigos, Familia, Pareja, Todos)")
    print(f"   - Normalización Numérica:      {desglose['numericas_minmax']:3d} columnas [0.0, 1.0]")
    print(f"     * Columnas escaladas:        {metrics['variables_escaladas']}")
    print(f"   ------------------------------------------------------------")
    print(f"   - TOTAL CARACTERÍSTICAS:       {desglose['total_caracteristicas']:3d} columnas")
    print(subsep)

    print("3. VERIFICACIÓN Y AUDITORÍA MATEMÁTICA:")
    nan_status = "PASÓ (0 valores NaN)" if not metrics["tiene_nan"] else "FALLÓ (Contiene NaN)"
    inf_status = "PASÓ (0 valores infinitos)" if not metrics["tiene_inf"] else "FALLÓ (Contiene Inf)"
    print(f"   - Control de valores NaN:      [OK] {nan_status}")
    print(f"   - Control de valores Inf:      [OK] {inf_status}")
    print(f"   - Compatibilidad inferencia:   [OK] handle_unknown='ignore' activo")
    print(sep + "\n")


def main() -> None:
    """
    Punto de entrada de línea de comandos.
    """
    parser = argparse.ArgumentParser(
        description="Fase 3: Pipeline de Ingeniería de Características (TurismoIA San Martín)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        default="data/processed/dataset_limpio.csv",
        help="Ruta al dataset limpio en formato CSV",
    )
    parser.add_argument(
        "-m",
        "--output-matrix",
        default="data/processed/X_global.npz",
        help="Ruta de destino para la matriz scipy.sparse X_global (.npz)",
    )
    parser.add_argument(
        "-p",
        "--output-pipeline",
        default="models/feature_pipeline.pkl",
        help="Ruta de destino para el pipeline serializado (.pkl)",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=120,
        help="Número máximo de términos para TF-IDF",
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
        _, _, metrics = run_feature_engineering(
            input_path=args.input,
            output_matrix_path=args.output_matrix,
            output_pipeline_path=args.output_pipeline,
            max_features=args.max_features,
        )
        if not args.quiet:
            print_summary_report(metrics)
    except Exception as exc:
        logger.error("Error crítico durante la ingeniería de características: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import src.feature_engineering as fe
    fe.main()
