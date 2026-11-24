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
import math
import re
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
import unicodedata

from src.feature_engineering import TurismoFeaturePipeline

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def normalizar_texto(texto: Any) -> str:
    """Elimina tildes/acentos y normaliza a mayúsculas sin espacios extra."""
    if pd.isna(texto) or texto is None:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip().upper()


_PROVINCE_DISPLAY: dict[str, str] = {
    "BELLAVISTA": "Bellavista",
    "EL DORADO": "El Dorado",
    "HUALLAGA": "Huallaga",
    "LAMAS": "Lamas",
    "MARISCAL CACERES": "Mariscal Cáceres",
    "MOYOBAMBA": "Moyobamba",
    "PICOTA": "Picota",
    "RIOJA": "Rioja",
    "SAN MARTIN": "San Martín",
    "TOCACHE": "Tocache",
}

_LOWERCASE_CONNECTORS = {"de", "del", "la", "las", "el", "los", "y"}

_KEYWORD_PHRASES: dict[str, str] = {
    "catarata": "cataratas",
    "cataratas": "cataratas",
    "cascada": "cascadas",
    "cascadas": "cascadas",
    "laguna": "lagunas",
    "lagunas": "lagunas",
    "naturaleza": "naturaleza amazónica",
    "ecologico": "naturaleza amazónica",
    "ecologica": "naturaleza amazónica",
    "paisaje": "paisajes naturales",
    "paisajes": "paisajes naturales",
    "bosque": "bosques",
    "senderismo": "caminatas por senderos",
    "trekking": "caminatas de aventura",
    "aventura": "aventura al aire libre",
    "agua": "paisajes de agua",
    "aguas": "paisajes de agua",
    "termales": "aguas termales",
    "descanso": "descanso al aire libre",
    "poza": "pozas naturales",
    "pozas": "pozas naturales",
    "banos": "baños naturales",
    "rio": "ríos y riberas",
    "rios": "ríos y riberas",
    "comunidad": "cultura viva",
    "comunidades": "cultura viva",
    "nativas": "comunidades locales",
    "cultura": "cultura local",
    "cultural": "cultura local",
    "culturales": "cultura local",
    "historia": "historia regional",
    "historico": "historia regional",
    "historica": "historia regional",
    "tradicion": "tradiciones locales",
    "tradicional": "tradiciones locales",
    "tradicionales": "tradiciones locales",
    "templo": "patrimonio arquitectónico",
    "templos": "patrimonio arquitectónico",
    "artesania": "artesanía tradicional",
    "artesanias": "artesanía tradicional",
    "castillo": "arquitectura singular",
    "lamista": "herencia lamista",
    "gastronomia": "gastronomía regional",
    "cacao": "cacao amazónico",
    "chocolate": "chocolate artesanal",
    "cafe": "café de la región",
    "juane": "cocina tradicional",
    "cecina": "cocina tradicional",
    "mercados": "mercados locales",
    "sabores": "sabores amazónicos",
    "degustacion": "degustaciones locales",
    "mirador": "miradores panorámicos",
    "miradores": "miradores panorámicos",
}

# Traducir solo los rótulos administrativos; el resto conserva el tipo del catálogo.
_EXPERIENCE_LABELS: dict[str, str] = {
    "FIESTAS TRADICIONALES(HERRANZA CARNAVALES OTROS)": "fiestas y costumbres locales",
    "FIESTAS RELIGIOSAS- PATRONALES": "celebraciones patronales",
    "FIESTAS RELIGIOSAS-PATRONALES": "celebraciones patronales",
    "TEJIDOS(LANAS FIBRAS DE ANIMALES FIBRA VEGETAL. ETC)": "tejidos artesanales",
    "PETROGLIFOS (GRABADOS EN PIEDRA)": "petroglifos",
    "GALERIAS EXPOSITIVA": "galerías de arte y cultura",
    "LUGARES PINTORESCOS DE FLORA Y FAUNA": "flora y fauna local",
    "REALIZACIONES TECNICAS CIENTIFICAS Y ARTISTICAS CONTEMPORANEAS": "espacios productivos y culturales",
    "AGRICULTURA": "actividades del campo",
    "TEMPLO": "templos", "CAPILLA": "capillas", "PLAZA": "plazas", "CASTILLO": "castillos",
    "TRADICIONALES": "tradiciones locales",
}

_ACCENTED_WORDS: dict[str, str] = {
    "alfareria": "alfarería", "areas": "áreas", "botanicos": "botánicos",
    "canones": "cañones", "ceramica": "cerámica", "conservacion": "conservación",
    "exhibicion": "exhibición", "galerias": "galerías", "musica": "música",
    "proteccion": "protección", "rapidos": "rápidos", "rios": "ríos", "tipicos": "típicos",
}


def _format_province(raw_province: Any) -> str:
    norm = normalizar_texto(raw_province)
    if not norm:
        return "San Martín"
    if norm in _PROVINCE_DISPLAY:
        return _PROVINCE_DISPLAY[norm]
    words = norm.lower().split()
    return " ".join(
        w if idx > 0 and w in _LOWERCASE_CONNECTORS else w.capitalize()
        for idx, w in enumerate(words)
    )


def _join_spanish_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} y {items[1]}"
    return f"{', '.join(items[:-1])} y {items[-1]}"


def _resolve_experience_phrase(rec_row: pd.Series) -> str:
    for field in ("subtipo", "categoria"):
        raw = rec_row.get(field)
        norm = normalizar_texto(raw)
        if not norm or norm == "OTROS":
            continue
        if norm in _EXPERIENCE_LABELS:
            return _EXPERIENCE_LABELS[norm]
        return re.sub(
            r"[^\s-]+",
            lambda match: _ACCENTED_WORDS.get(normalizar_texto(match[0]).lower(), match[0]),
            str(raw).strip().lower(),
        )
    return "lugares de la región"


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
        self._lats = pd.to_numeric(self.catalogo.get("latitud"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
        self._lngs = pd.to_numeric(self.catalogo.get("longitud"), errors="coerce").fillna(0.0).to_numpy(dtype=float)

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
        Genera una explicación dinámica de negocio (XAI) legible y cercana para el viajero.
        """
        _ = cluster_label  # Reservado para compatibilidad de firma
        intereses_raw = str(perfil_dict.get("intereses") or "")
        user_tokens = [
            tok
            for tok in re.findall(r"[a-z0-9]+", normalizar_texto(intereses_raw).lower())
            if len(tok) > 2
        ]

        item_text_norm = normalizar_texto(
            f"{rec_row.get('nombre_recurso', '')} "
            f"{rec_row.get('etiquetas_interes', '')} "
            f"{rec_row.get('subtipo', '')} "
            f"{rec_row.get('tipo', '')} "
            f"{rec_row.get('categoria', '')} "
            f"{rec_row.get('descripcion_corta', '')}"
        ).lower()
        item_tokens = set(re.findall(r"[a-z0-9]+", item_text_norm))

        matched_phrases: list[str] = []
        for token in user_tokens:
            if token in item_tokens:
                phrase = _KEYWORD_PHRASES.get(token)
                if phrase and phrase not in matched_phrases:
                    matched_phrases.append(phrase)
            if len(matched_phrases) >= 2:
                break

        experience_phrase = _resolve_experience_phrase(rec_row)
        province_name = _format_province(rec_row.get("provincia", "San Martín"))

        # Mencionar un interés solo si aparece en los datos de este lugar.
        theme = experience_phrase
        if matched_phrases and experience_phrase == "lugares de la región":
            theme = _join_spanish_list(matched_phrases)

        raw_budget = perfil_dict.get("presupuesto_max_pen")
        if raw_budget is None:
            raw_budget = perfil_dict.get("presupuesto")
        cost = rec_row.get("costo_referencial_pen")
        fits_budget = (
            raw_budget is not None and str(raw_budget).strip() != ""
            and cost is not None and not pd.isna(cost)
            and float(cost) <= float(raw_budget)
        )
        raw_time = perfil_dict.get("tiempo_disponible_horas")
        if raw_time is None:
            raw_time = perfil_dict.get("tiempo")
        duration = rec_row.get("duracion_estimada_horas")
        fits_time = (
            raw_time is not None and str(raw_time).strip() != ""
            and duration is not None and not pd.isna(duration)
            and 0 < float(duration) <= float(raw_time)
        )

        # Variación estable por lugar, sin aleatoriedad ni cambios en el ranking.
        variation = sum(ord(char) for char in str(rec_row.get("nombre_recurso", ""))) % 3
        fit = ""
        if fits_budget and (variation != 1 or not fits_time):
            fit = " sin salir de tu presupuesto de entrada"
        elif fits_time:
            fit = " dentro del tiempo que tienes para la visita"

        description_raw = rec_row.get("descripcion_corta")
        description = "" if pd.isna(description_raw) else str(description_raw or "").strip()
        if description and not re.search(r"provisional|requiere validaci[oó]n|figura en la base", description, re.I):
            name = normalizar_texto(rec_row.get("nombre_recurso", ""))
            detail = next((
                sentence for sentence in re.split(r"\.\s+", description)
                if normalizar_texto(sentence).rstrip(".") != name
            ), "")
            if detail and len(detail) <= 240:
                suffix = (
                    "; la visita se ajusta a tu presupuesto de entrada" if "presupuesto" in fit
                    else "; su duración se ajusta al tiempo que tienes" if fit else ""
                )
                return f"{detail.rstrip('.!?')}{suffix}."

        openings = (
            f"Puedes conocer {theme} en {province_name}",
            f"En {province_name}, una opción para conocer {theme}",
            f"Una opción en {province_name} para conocer {theme}",
        )
        return f"{openings[variation]}{fit}."

    def _haversine_km(self, idx_a: int, idx_b: int) -> float:
        lat1, lon1 = self._lats[idx_a], self._lngs[idx_a]
        lat2, lon2 = self._lats[idx_b], self._lngs[idx_b]
        if (lat1 == 0.0 and lon1 == 0.0) or (lat2 == 0.0 and lon2 == 0.0):
            return 9999.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2.0) ** 2)
        )
        return 2.0 * 6371.0 * math.asin(min(1.0, math.sqrt(a)))

    def _select_coherent_top_n(
        self,
        ordered_indices: np.ndarray,
        top_n: int,
        tiempo_max: float,
    ) -> np.ndarray:
        """Mantiene cercanía geográfica entre paradas cuando el tiempo disponible es corto."""
        if len(ordered_indices) <= 1 or tiempo_max > 9.0:
            return ordered_indices[:top_n]

        strict_km = 38.0 if tiempo_max <= 4.5 else 78.0
        relaxed_km = 65.0 if tiempo_max <= 4.5 else 120.0

        anchor_idx = int(ordered_indices[0])
        selected: list[int] = [anchor_idx]
        selected_set = {anchor_idx}

        # Priorizar candidatos top dentro del radio estricto, luego radio ampliado y finalmente resto
        for max_km in (strict_km, relaxed_km, float("inf")):
            if len(selected) >= top_n:
                break
            for candidate in ordered_indices[1:]:
                c_idx = int(candidate)
                if c_idx in selected_set:
                    continue
                if max_km == float("inf") or self._haversine_km(anchor_idx, c_idx) <= max_km:
                    selected.append(c_idx)
                    selected_set.add(c_idx)
                    if len(selected) >= top_n:
                        break

        # Ordenar paradas restantes por vecino más cercano para evitar zig-zags en la ruta
        if len(selected) > 2:
            routed = [selected[0]]
            remaining = selected[1:]
            while remaining:
                last = routed[-1]
                nearest_pos = min(range(len(remaining)), key=lambda i: self._haversine_km(last, remaining[i]))
                routed.append(remaining.pop(nearest_pos))
            selected = routed

        return np.array(selected, dtype=ordered_indices.dtype)

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
        intereses = str(perfil_dict.get("intereses") or "").strip()
        raw_tiempo = perfil_dict.get("tiempo_disponible_horas")
        if raw_tiempo is None:
            raw_tiempo = perfil_dict.get("tiempo")
        tiempo_max = (
            float(raw_tiempo)
            if raw_tiempo is not None and str(raw_tiempo).strip() != ""
            else 4.0
        )

        raw_presupuesto = perfil_dict.get("presupuesto_max_pen")
        if raw_presupuesto is None:
            raw_presupuesto = perfil_dict.get("presupuesto")
        presupuesto_max = (
            float(raw_presupuesto)
            if raw_presupuesto is not None and str(raw_presupuesto).strip() != ""
            else 9999.0
        )

        raw_dificultad = perfil_dict.get("nivel_dificultad")
        if raw_dificultad is None:
            raw_dificultad = perfil_dict.get("dificultad")
        dificultad = str(raw_dificultad or "Todos").strip().capitalize()

        provincia_raw = str(perfil_dict.get("provincia") or "Todas").strip()
        provincia_in = normalizar_texto(provincia_raw)

        raw_publico = perfil_dict.get("publico")
        if raw_publico is None:
            raw_publico = perfil_dict.get("publico_recomendado")
        publico = str(raw_publico or "Todos").strip().capitalize()

        filtro_prov_activo = provincia_in not in ["TODAS", "TODOS", "CUALQUIERA", ""]
        provincia_ohe = provincia_in if filtro_prov_activo else "DESCONOCIDA"

        # Inferencia de pistas temáticas para enriquecer vectorización semántica
        intereses_lower = normalizar_texto(intereses).lower()
        categoria_hint = ""
        if any(w in intereses_lower for w in ["catarata", "cascada", "laguna", "bosque", "naturaleza", "paisaje", "senderismo"]):
            categoria_hint = "SITIOS NATURALES"
        elif any(w in intereses_lower for w in ["cultura", "historia", "tradicion", "artesania", "templo", "museo", "castillo", "comunidad", "nativas"]):
            categoria_hint = "MANIFESTACIONES CULTURALES"
        elif any(w in intereses_lower for w in ["gastronomia", "cacao", "chocolate", "cafe", "sabores", "comida", "degustacion", "juane"]):
            categoria_hint = "REALIZACIONES TECNICAS CIENTIFICAS Y ARTISTICAS CONTEMPORANEAS FOLCLORE"

        # Público recomendado: la mayoría del catálogo está clasificado como "Todos", por lo que es apto para cualquier grupo
        publico_ohe = "Todos" if publico in ["Todos", "Amigos", ""] else publico

        # 2. Vectorización ultrarrápida del perfil
        user_row = pd.DataFrame([{
            "categoria": categoria_hint,
            "tipo": "",
            "subtipo": "",
            "etiquetas_interes": intereses,
            "descripcion_corta": f"{categoria_hint} {intereses}".strip(),
            "nivel_dificultad": dificultad,
            "provincia": provincia_ohe,
            "publico_recomendado": publico_ohe,
            "duracion_estimada_horas": min(tiempo_max, 7.0),
            "costo_referencial_pen": min(presupuesto_max, 40.0),
        }])

        user_vec = self.feature_pipeline.transform(user_row)

        # 3. Similitud del Coseno
        sims = cosine_similarity(user_vec, self.X_global).flatten()

        # 4. Filtros duros obligatorios con normalización de caracteres
        mask_tiempo = self.catalogo["duracion_estimada_horas"] <= tiempo_max
        mask_costo = self.catalogo["costo_referencial_pen"] <= presupuesto_max
        mask_prov = (
            self.catalogo["provincia"].apply(normalizar_texto) == provincia_in
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

        # 5. Ordenamiento y extracción del Top-N con coherencia geográfica para salidas cortas
        scores_validos = sims[indices_validos]
        sorted_order = np.argsort(scores_validos)[::-1]
        ordered_indices = indices_validos[sorted_order]
        best_indices = self._select_coherent_top_n(
            ordered_indices=ordered_indices,
            top_n=top_n,
            tiempo_max=tiempo_max,
        )

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
