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
    "paisaje": "paisajes naturales",
    "paisajes": "paisajes naturales",
    "bosque": "bosques",
    "senderismo": "caminatas por senderos",
    "trekking": "caminatas de aventura",
    "aventura": "aventura al aire libre",
    "aguas": "aguas termales",
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
    "historia": "historia regional",
    "tradicion": "tradiciones locales",
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
    "amazonicos": "sabores amazónicos",
    "degustacion": "degustaciones locales",
    "mirador": "miradores panorámicos",
    "miradores": "miradores panorámicos",
}

_SUBTIPO_DISPLAY: dict[str, str] = {
    "AGRICULTURA": "actividades agrícolas y del campo",
    "AGUAS TERMALES": "aguas termales",
    "ALAMEDAS": "paseos y alamedas",
    "ALFARERIA Y CERAMICA": "alfarería y cerámica tradicional",
    "AREAS DE CONSERVACION PRIVADA": "áreas de conservación natural",
    "BOSQUES": "bosques amazónicos",
    "BOSQUES DE PROTECCION": "bosques protegidos",
    "BULEVARES": "recorridos urbanos",
    "CAMINO PINTORESCO": "rutas escénicas",
    "CANONES": "cañones naturales",
    "CAPILLA": "patrimonio histórico y religioso",
    "CASCADAS": "cascadas naturales",
    "CASTILLO": "arquitectura emblemática",
    "CATARATAS": "cataratas",
    "CEMENTERIOS": "patrimonio histórico",
    "CENTROS DE RESCATE O CONSERVACION": "conservación de fauna y flora",
    "CENTROS PRODUCTIVOS": "experiencias productivas locales",
    "CERROS": "cerros y rutas panorámicas",
    "CUEVAS": "cuevas y cavernas",
    "DULCES TIPICOS": "dulces y sabores típicos",
    "FABRICAS": "talleres y producción artesanal",
    "FESTIVALES": "festivales regionales",
    "FIESTAS RELIGIOSAS- PATRONALES": "celebraciones tradicionales",
    "FIESTAS RELIGIOSAS-PATRONALES": "celebraciones tradicionales",
    "FIESTAS TRADICIONALES(HERRANZA CARNAVALES OTROS)": "fiestas y costumbres locales",
    "GALERIAS EXPOSITIVA": "galerías de arte y cultura",
    "GRUTAS": "grutas naturales",
    "HUMEDALES": "humedales y biodiversidad",
    "ISLAS": "islas y paisajes fluviales",
    "JARDINES BOTANICOS Y VIVEROS": "jardines botánicos y orquídeas",
    "LAGOS": "lagos y espejos de agua",
    "LAGUNAS": "lagunas naturales",
    "LUGARES PINTORESCOS DE FLORA Y FAUNA": "observación de flora y fauna",
    "MANANTIALES": "manantiales de agua clara",
    "MARIPOSARIOS": "mariposarios y fauna local",
    "MIRADORES": "miradores panorámicos",
    "MIRADORES NATURALES": "miradores naturales",
    "MITOS": "relatos y tradiciones amazónicas",
    "MUSEOS": "museos y memoria local",
    "MUSICA Y DANZAS": "música y danzas tradicionales",
    "OJOS DE AGUA": "ojos de agua naturales",
    "PAMPAS": "paisajes abiertos",
    "PARQUES": "parques y áreas verdes",
    "PARQUES NACIONALES": "parques nacionales y reservas",
    "PETROGLIFOS (GRABADOS EN PIEDRA)": "petroglifos y arte rupestre",
    "PINTURA RUPESTRE": "arte rupestre",
    "PINTURAS": "arte y pintura regional",
    "PLAZA": "plazas tradicionales",
    "PLAZAS": "plazas tradicionales",
    "PLAZUELAS": "plazuelas históricas",
    "PONGOS": "pongos y cañones fluviales",
    "PUENTES": "puentes y arquitectura local",
    "PUERTOS": "embarcaderos y vida fluvial",
    "QUEBRADAS": "quebradas de agua fresca",
    "RAPIDOS": "rápidos y aventura fluvial",
    "RIOS": "ríos amazónicos",
    "SALAS DE EXHIBICION": "salas culturales y exhibiciones",
    "SANTUARIOS": "santuarios y reservas",
    "TEJIDOS(LANAS FIBRAS DE ANIMALES FIBRA VEGETAL. ETC)": "tejidos y textilería artesanal",
    "TEMPLO": "templos históricos",
    "TEMPLOS": "templos históricos",
    "TRADICIONALES": "costumbres y sabores tradicionales",
    "ZONAS RESERVADAS": "zonas naturales protegidas",
}

_CATEGORIA_DISPLAY: dict[str, str] = {
    "SITIOS NATURALES": "entornos naturales",
    "MANIFESTACIONES CULTURALES": "expresiones culturales",
    "FOLCLORE": "tradiciones y folclore local",
    "REALIZACIONES TECNICAS CIENTIFICAS Y ARTISTICAS CONTEMPORANEAS": "espacios productivos y creativos",
    "ACONTECIMIENTOS PROGRAMADOS": "encuentros y festividades locales",
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
    sub_norm = normalizar_texto(rec_row.get("subtipo", ""))
    if sub_norm and sub_norm != "OTROS" and sub_norm in _SUBTIPO_DISPLAY:
        return _SUBTIPO_DISPLAY[sub_norm]
    cat_norm = normalizar_texto(rec_row.get("categoria", ""))
    if cat_norm in _CATEGORIA_DISPLAY:
        return _CATEGORIA_DISPLAY[cat_norm]
    return "experiencias locales en la región"


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
        Genera una explicación dinámica de negocio (XAI) legible y cercana para el viajero.
        """
        _ = cluster_label  # Reservado para compatibilidad de firma
        intereses_raw = str(perfil_dict.get("intereses", ""))
        user_tokens = [
            normalizar_texto(w).lower()
            for w in intereses_raw.replace(",", " ").split()
            if len(w.strip()) > 2
        ]

        item_text_norm = normalizar_texto(
            f"{rec_row.get('nombre_recurso', '')} "
            f"{rec_row.get('etiquetas_interes', '')} "
            f"{rec_row.get('subtipo', '')} "
            f"{rec_row.get('tipo', '')} "
            f"{rec_row.get('categoria', '')} "
            f"{rec_row.get('descripcion_corta', '')}"
        ).lower()

        matched_phrases: list[str] = []
        for token in user_tokens:
            if token in item_text_norm:
                phrase = _KEYWORD_PHRASES.get(token)
                if phrase and phrase not in matched_phrases:
                    matched_phrases.append(phrase)
            if len(matched_phrases) >= 2:
                break

        experience_phrase = _resolve_experience_phrase(rec_row)
        province_name = _format_province(rec_row.get("provincia", "San Martín"))

        if matched_phrases:
            interests_text = _join_spanish_list(matched_phrases)
            if any(p in experience_phrase or experience_phrase in p for p in matched_phrases):
                first_sentence = f"Encaja con tu interés en {interests_text} con una parada auténtica en {province_name}."
            else:
                first_sentence = f"Encaja con tu interés en {interests_text} gracias a su propuesta de {experience_phrase}."
        else:
            first_sentence = f"Destaca por su propuesta de {experience_phrase} en {province_name} y se adapta bien a tu recorrido."

        dur = float(rec_row.get("duracion_estimada_horas", 0.0) or 0.0)
        if dur <= 1.0:
            duration_phrase = "una visita breve"
        elif dur <= 3.0:
            duration_phrase = "un recorrido de unas horas"
        elif dur <= 6.0:
            duration_phrase = "una salida de medio día"
        else:
            duration_phrase = "una jornada amplia"

        dif_norm = normalizar_texto(rec_row.get("nivel_dificultad", "Media")).lower()
        if dif_norm == "baja":
            pace_phrase = "de ritmo tranquilo y acceso cómodo"
        elif dif_norm == "alta":
            pace_phrase = "con caminatas de mayor exigencia"
        else:
            pace_phrase = "de esfuerzo moderado"

        costo = float(rec_row.get("costo_referencial_pen", 0.0) or 0.0)
        presupuesto_max = float(
            perfil_dict.get("presupuesto_max_pen", perfil_dict.get("presupuesto", 100.0)) or 100.0
        )

        publico_raw = normalizar_texto(
            perfil_dict.get("publico", perfil_dict.get("publico_recomendado", "Todos"))
        ).lower()
        row_publico = normalizar_texto(rec_row.get("publico_recomendado", "Todos")).lower()
        effective_publico = publico_raw if publico_raw not in ("", "todos") else row_publico

        publico_map = {
            "familia": "ideal para compartir en familia",
            "pareja": "ideal para disfrutar en pareja",
            "amigos": "genial para ir con amigos",
            "solo": "ideal para recorrer por tu cuenta",
        }
        publico_phrase = publico_map.get(effective_publico, "")

        details: list[str] = []
        if costo == 0.0:
            details.append("con ingreso libre")
        elif presupuesto_max <= 25.0:
            details.append("con tarifa accesible")
        if publico_phrase:
            details.append(publico_phrase)

        if details:
            second_sentence = f"Ofrece {duration_phrase} {pace_phrase}, {', '.join(details)}."
        else:
            second_sentence = f"Ofrece {duration_phrase} {pace_phrase} para disfrutar sin apuros."

        justification = f"{first_sentence} {second_sentence}".strip()
        if len(justification) > 340:
            justification = first_sentence
        return justification[0].upper() + justification[1:]

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
        provincia_raw = str(perfil_dict.get("provincia", "Todas")).strip()
        provincia_in = normalizar_texto(provincia_raw)
        publico = str(perfil_dict.get("publico", perfil_dict.get("publico_recomendado", "Todos"))).strip().capitalize()

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
