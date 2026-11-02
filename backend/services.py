from __future__ import annotations

import asyncio
import logging
import re
import time
import unicodedata
from decimal import Decimal
from typing import Any, Optional

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import (
    Atractivo,
    ClusterPerfil,
    CompaniaViaje,
    EjecucionRecomendacion,
    ModeloVersion,
    NivelDificultad,
    Provincia,
    Recomendacion,
    SesionPreferencia,
    SesionProvincia,
    Valoracion,
)
from schemas import (
    ChatResponse,
    PreferenciaRequest,
    RecomendacionItem,
    RecomendacionResponse,
    ValoracionRequest,
    ValoracionResponse,
)

logger = logging.getLogger(__name__)

def normalizar_cadena(val: Any) -> str:
    """Elimina acentos y normaliza a mayúsculas sin espacios redundantes."""
    if val is None or pd.isna(val):
        return ""
    nfkd = unicodedata.normalize('NFKD', str(val))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip().upper()


def pide_recomendaciones_destinos(msg: str) -> bool:
    """
    Determina si el usuario está solicitando explícitamente recomendaciones,
    sugerencias o listas de lugares/destinos turísticos para visitar.
    """
    if not msg:
        return False
    nfkd = unicodedata.normalize('NFKD', msg.lower())
    t = ''.join([c for c in nfkd if not unicodedata.combining(c)])

    patterns = [
        r'recomiend',                                 # recomiéndame, recomendación, qué recomiendas, etc.
        r'sugier',                                   # sugiéreme, sugerencia, etc.
        r'itinerario',                               # itinerario de viaje
        r'que\s+(?:puedo\s+|se\s+puede\s+)?(?:hacer|visitar|conocer|ver)',  # qué hacer, qué puedo visitar
        r'que\s+(?:lugares|destinos|sitios|atractivos|cataratas|lagunas)',  # qué lugares, qué destinos
        r'donde\s+(?:puedo\s+)?ir',                  # dónde ir, dónde puedo ir
        r'mejores\s+(?:lugares|destinos|cataratas|lagunas|atractivos|sitios)', # mejores lugares
        r'(?:dame|muestrame|mostrame)\s+(?:opciones|lugares|destinos|rutas)',
        r'(?:lugares|destinos|sitios|atractivos)\s+(?:para|de|turisticos|bonitos|imperdibles)',
    ]
    return any(re.search(p, t) for p in patterns)

# Almacenamiento en memoria para modo autónomo (cuando PostgreSQL no está activo)
MEM_SESIONES: dict[str, dict[str, Any]] = {}
MEM_EJECUCIONES: dict[int, dict[str, Any]] = {}
MEM_VALORACIONES: dict[int, dict[str, Any]] = {}


class CatalogCache:
    """
    Caché en memoria de catálogos y metadatos para optimización extrema.
    Puede sincronizarse con PostgreSQL o inicializarse autónomamente desde el catálogo serializado.
    """

    def __init__(self) -> None:
        self.atractivo_map: dict[str, int] = {}       # codigo_recurso -> id_atractivo
        self.atractivo_name_map: dict[str, int] = {}  # nombre_upper -> id_atractivo
        self.provincia_map: dict[str, str] = {}       # nombre_upper -> id_provincia
        self.compania_map: dict[str, int] = {}        # nombre_lower -> id_compania
        self.dificultad_map: dict[str, int] = {}      # nombre_lower -> id_dificultad
        self.active_model_id: int = 1
        self.cluster_map: dict[int, int] = {}         # numero_cluster -> id_cluster

    def load_from_catalogo(self, catalogo: pd.DataFrame, cluster_metadata: Optional[dict[int, dict[str, str]]] = None) -> None:
        """Inicializa catálogos directamente desde el DataFrame de atractivos en RAM."""
        for idx, row in catalogo.iterrows():
            aid = int(idx) + 1
            cod = str(row.get("id_recurso", f"REC-{aid:05d}"))
            nom = str(row.get("nombre_recurso", "")).upper()
            self.atractivo_map[cod] = aid
            self.atractivo_name_map[nom] = aid

            prov_norm = normalizar_cadena(row.get("provincia", ""))
            prov_raw = str(row.get("provincia", "")).upper()
            if prov_norm and prov_norm not in self.provincia_map:
                pid = f"22{len(self.provincia_map)+1:02d}"
                self.provincia_map[prov_norm] = pid
                self.provincia_map[prov_raw] = pid

        for cid, nom in enumerate(["Solo", "Pareja", "Amigos", "Familia", "Familia con niños", "Adulto mayor", "Todos"], start=1):
            self.compania_map[nom.lower()] = cid

        for did, nom in enumerate(["Baja", "Media", "Alta"], start=1):
            self.dificultad_map[nom.lower()] = did

        if cluster_metadata:
            for c_num in cluster_metadata:
                self.cluster_map[c_num] = c_num

        logger.info(
            "Caché inicializado desde catálogo en memoria: %d atractivos, %d provincias, %d compañías.",
            len(self.atractivo_map),
            len(self.provincia_map),
            len(self.compania_map),
        )

    async def load(self, db: AsyncSession, cluster_metadata: Optional[dict[int, dict[str, str]]] = None) -> None:
        """
        Carga y sincroniza catálogos desde la base de datos.
        """
        logger.info("Cargando caché de catálogos desde PostgreSQL (esquema turismo)...")

        # 1. Atractivos
        res_atr = await db.execute(select(Atractivo.id_atractivo, Atractivo.codigo_recurso, Atractivo.nombre))
        for aid, cod, nom in res_atr.all():
            self.atractivo_map[cod] = aid
            self.atractivo_name_map[nom.upper()] = aid

        # 2. Provincias
        res_prov = await db.execute(select(Provincia.id_provincia, Provincia.nombre))
        for pid, nom in res_prov.all():
            self.provincia_map[nom.upper()] = pid
            self.provincia_map[normalizar_cadena(nom)] = pid

        # 3. Compañía de viaje
        res_comp = await db.execute(select(CompaniaViaje.id_compania, CompaniaViaje.nombre))
        for cid, nom in res_comp.all():
            self.compania_map[nom.lower()] = cid

        # 4. Nivel de dificultad
        res_dif = await db.execute(select(NivelDificultad.id_dificultad, NivelDificultad.nombre))
        for did, nom in res_dif.all():
            self.dificultad_map[nom.lower()] = did

        # 5. Modelo Activo
        res_mod = await db.execute(select(ModeloVersion.id_modelo).where(ModeloVersion.activo.is_(True)).limit(1))
        mod_id = res_mod.scalar()
        if mod_id:
            self.active_model_id = mod_id
        else:
            self.active_model_id = 1

        # 6. Sincronización de Cluster Perfil
        res_clusters = await db.execute(
            select(ClusterPerfil.numero, ClusterPerfil.id_cluster).where(ClusterPerfil.id_modelo == self.active_model_id)
        )
        clusters_db = dict(res_clusters.all())

        if not clusters_db and cluster_metadata:
            logger.info("Poblando perfiles de clusters en 'turismo.cluster_perfil' para id_modelo=%d...", self.active_model_id)
            for c_num, c_info in cluster_metadata.items():
                label = str(c_info.get("label", f"Cluster {c_num}"))[:80]
                descr = str(c_info.get("descripcion", ""))[:300]
                cp = ClusterPerfil(
                    id_modelo=self.active_model_id,
                    numero=c_num,
                    nombre=label,
                    descripcion=descr,
                )
                db.add(cp)
            await db.commit()

            # Recargar mapa
            res_clusters = await db.execute(
                select(ClusterPerfil.numero, ClusterPerfil.id_cluster).where(ClusterPerfil.id_modelo == self.active_model_id)
            )
            clusters_db = dict(res_clusters.all())

        self.cluster_map = clusters_db

        logger.info(
            "Caché cargado con éxito: %d atractivos, %d provincias, %d compañías, %d clusters.",
            len(self.atractivo_map),
            len(self.provincia_map),
            len(self.compania_map),
            len(self.cluster_map),
        )


def count_candidates(catalogo: pd.DataFrame, perfil: dict[str, Any]) -> int:
    """
    Calcula cuántos atractivos satisfacen los filtros duros obligatorios con normalización de caracteres.
    """
    tiempo_max = float(perfil.get("tiempo_disponible_horas", 8.0))
    presupuesto_val = perfil.get("presupuesto_max_pen")
    presupuesto_max = float(presupuesto_val) if presupuesto_val is not None else 9999.0
    provincia_in = normalizar_cadena(perfil.get("provincia", "Todas"))
    filtro_prov_activo = provincia_in not in ["TODAS", "TODOS", "CUALQUIERA", ""]

    mask_tiempo = catalogo["duracion_estimada_horas"] <= tiempo_max
    mask_costo = catalogo["costo_referencial_pen"] <= presupuesto_max
    mask_prov = (
        catalogo["provincia"].apply(normalizar_cadena) == provincia_in
        if filtro_prov_activo
        else pd.Series(True, index=catalogo.index)
    )

    mask_filtros = mask_tiempo & mask_costo & mask_prov
    if mask_filtros.sum() == 0 and filtro_prov_activo:
        mask_filtros = mask_tiempo & mask_costo

    return int(mask_filtros.sum())


async def generar_y_persistir_recomendaciones(
    db: AsyncSession,
    engine: Any,
    preferencias: PreferenciaRequest,
    cache: CatalogCache,
) -> RecomendacionResponse:
    """
    Orquesta la ejecución de inferencia con filtros duros y persiste:
    1. sesion_preferencia
    2. sesion_provincia (si aplica)
    3. ejecucion_recomendacion
    4. recomendacion (Top-N)
    """
    # 1. Preparar dict de perfil para InferenceEngine
    perfil_dict = {
        "intereses": preferencias.intereses,
        "tiempo_disponible_horas": preferencias.tiempo_en_horas,
        "presupuesto_max_pen": preferencias.presupuesto if preferencias.presupuesto is not None else 9999.0,
        "nivel_dificultad": preferencias.nivel_dificultad,
        "provincia": preferencias.provincia,
        "publico": preferencias.compania,
    }

    # 2. Ejecutar inferencia cronometrada en memoria RAM (<10ms)
    t0 = time.perf_counter()
    recs = engine.predict_top_n(perfil_dict, top_n=preferencias.top_n)
    elapsed_ms = max(1, int(round((time.perf_counter() - t0) * 1000)))

    # 3. Contabilizar candidatos válidos
    total_candidatos = count_candidates(engine.catalogo, perfil_dict)

    # 4. Determinar cluster del perfil de usuario
    id_cluster_fk: Optional[int] = None
    try:
        user_row = pd.DataFrame([{
            "categoria": "",
            "tipo": "",
            "subtipo": "",
            "etiquetas_interes": preferencias.intereses,
            "descripcion_corta": preferencias.intereses,
            "nivel_dificultad": preferencias.nivel_dificultad,
            "provincia": preferencias.provincia.upper() if preferencias.provincia.upper() not in ["TODAS", "TODOS", ""] else "DESCONOCIDA",
            "publico_recomendado": preferencias.compania,
            "duracion_estimada_horas": min(preferencias.tiempo_en_horas, 7.0),
            "costo_referencial_pen": min(preferencias.presupuesto or 40.0, 40.0),
        }])
        user_vec = engine.feature_pipeline.transform(user_row)
        user_cluster_num = int(engine.kmeans.predict(user_vec)[0])
        id_cluster_fk = cache.cluster_map.get(user_cluster_num)
    except Exception as exc:
        logger.warning("No se pudo predecir cluster para la sesión: %s", exc)

    # 5. Persistir SesionPreferencia
    compania_id = cache.compania_map.get(preferencias.compania.lower())
    dificultad_id = cache.dificultad_map.get(preferencias.nivel_dificultad.lower())

    import uuid
    id_sesion_gen = uuid.uuid4()
    id_ejecucion_gen = (int(time.time() * 1000) % 2000000000) + 1

    sesion = SesionPreferencia(
        tiempo_disponible_horas=Decimal(str(round(preferencias.tiempo_en_horas, 2))),
        presupuesto_max_pen=Decimal(str(round(preferencias.presupuesto, 2))) if preferencias.presupuesto is not None else None,
        id_compania=compania_id,
        id_dificultad_max=dificultad_id,
        requiere_accesibilidad=preferencias.requiere_accesibilidad,
        texto_libre=preferencias.intereses[:300] if preferencias.intereses else None,
        tipo_dispositivo=preferencias.tipo_dispositivo,
        consentimiento_datos=preferencias.consentimiento_datos,
    )
    sesion.id_sesion = id_sesion_gen

    db_persisted = False
    if db is not None:
        try:
            db.add(sesion)
            await db.flush()
            db_persisted = True
        except Exception as exc:
            logger.warning("Fallo al persistir sesión en PostgreSQL: %s. Operando en memoria.", exc)
            db_persisted = False

    # Si se seleccionó provincia específica, registrarla en sesion_provincia
    prov_norm = normalizar_cadena(preferencias.provincia)
    if prov_norm not in ["TODAS", "TODOS", "CUALQUIERA", ""]:
        id_prov = cache.provincia_map.get(prov_norm) or cache.provincia_map.get(preferencias.provincia.upper())
        if id_prov and db_persisted:
            try:
                sesion_prov = SesionProvincia(
                    id_sesion=sesion.id_sesion,
                    id_provincia=id_prov,
                )
                db.add(sesion_prov)
                await db.flush()
            except Exception as exc:
                logger.warning("No se pudo persistir sesion_provincia: %s", exc)

    # 6. Persistir EjecucionRecomendacion
    ejecucion = EjecucionRecomendacion(
        id_sesion=sesion.id_sesion,
        id_modelo=cache.active_model_id,
        id_cluster=id_cluster_fk,
        total_candidatos=total_candidatos,
        tiempo_respuesta_ms=elapsed_ms,
        parametros_aplicados=preferencias.model_dump(),
    )
    if not db_persisted:
        ejecucion.id_ejecucion = id_ejecucion_gen

    if db_persisted:
        try:
            db.add(ejecucion)
            await db.flush()
        except Exception as exc:
            logger.warning("Fallo al persistir ejecución en PostgreSQL: %s", exc)
            db_persisted = False
            ejecucion.id_ejecucion = id_ejecucion_gen

    # 7. Persistir Recomendaciones individuales (Top-N)
    items_response: list[RecomendacionItem] = []
    fallback_provincia_aplicado = False

    for idx, r in enumerate(recs):
        cod_recurso = r["id_recurso"]
        id_atractivo = cache.atractivo_map.get(cod_recurso)
        if not id_atractivo:
            id_atractivo = cache.atractivo_name_map.get(r["nombre_recurso"].upper(), idx + 1)

        afinidad_norm = round(max(0.0, min(1.0, float(r["afinidad_pct"]) / 100.0)), 4)
        explicacion_truncada = str(r["justificacion"])[:400]
        cumple_filtros = not r.get("fallback_provincia", False)
        if r.get("fallback_provincia", False):
            fallback_provincia_aplicado = True

        rec_id = idx + 1 + (ejecucion.id_ejecucion * 10)
        if db_persisted:
            try:
                rec_db = Recomendacion(
                    id_ejecucion=ejecucion.id_ejecucion,
                    id_atractivo=id_atractivo,
                    posicion=r["ranking"],
                    puntaje_afinidad=Decimal(str(afinidad_norm)),
                    cumple_filtros=cumple_filtros,
                    explicacion=explicacion_truncada,
                )
                db.add(rec_db)
                await db.flush()
                rec_id = rec_db.id_recomendacion
            except Exception as exc:
                logger.warning("No se pudo persistir recomendacion en DB: %s", exc)

        items_response.append(
            RecomendacionItem(
                id_recomendacion=rec_id,
                posicion=r["ranking"],
                id_atractivo=id_atractivo,
                codigo_recurso=cod_recurso,
                nombre_recurso=r["nombre_recurso"],
                categoria=r["categoria"],
                tipo=r["tipo"],
                subtipo=r["subtipo"],
                provincia=r["provincia"],
                distrito=r["distrito"],
                latitud=r["latitud"],
                longitud=r["longitud"],
                duracion_estimada_horas=r["duracion_estimada_horas"],
                costo_referencial_pen=r["costo_referencial_pen"],
                nivel_dificultad=r["nivel_dificultad"],
                publico_recomendado=r["publico_recomendado"],
                afinidad_pct=r["afinidad_pct"],
                puntaje_afinidad=afinidad_norm,
                cluster_id=r["cluster_id"],
                cluster_label=r["cluster_label"],
                explicacion=explicacion_truncada,
                imagen_url=r.get("imagen_url"),
                cumple_filtros=cumple_filtros,
            )
        )

    if db_persisted:
        try:
            await db.commit()
        except Exception as exc:
            logger.warning("Fallo en db.commit(): %s", exc)

    # Registrar en memoria para persistencia local y fallback de valoración
    MEM_SESIONES[str(sesion.id_sesion)] = {
        "id_sesion": sesion.id_sesion,
        "preferencias": preferencias.model_dump(),
    }
    MEM_EJECUCIONES[ejecucion.id_ejecucion] = {
        "id_ejecucion": ejecucion.id_ejecucion,
        "id_sesion": sesion.id_sesion,
        "recomendaciones": items_response,
        "tiempo_respuesta_ms": elapsed_ms,
        "cumple_filtros": not fallback_provincia_aplicado,
    }

    return RecomendacionResponse(
        id_sesion=sesion.id_sesion,
        id_ejecucion=ejecucion.id_ejecucion,
        id_modelo=cache.active_model_id,
        tiempo_respuesta_ms=elapsed_ms,
        total_candidatos=total_candidatos,
        fallback_provincia=fallback_provincia_aplicado,
        recomendaciones=items_response,
    )


async def registrar_feedback(
    db: AsyncSession,
    val_data: ValoracionRequest,
) -> ValoracionResponse:
    """
    Registra el feedback de un turista en 'turismo.valoracion' vinculado a la ejecución.
    Si la base de datos no está disponible, almacena la valoración en memoria.
    """
    from datetime import datetime, timezone

    # 1. Validar existencia de la ejecución
    ejecucion_db = None
    ejecucion_mem = MEM_EJECUCIONES.get(val_data.id_ejecucion)

    if db is not None:
        try:
            res_ejec = await db.execute(
                select(EjecucionRecomendacion).where(EjecucionRecomendacion.id_ejecucion == val_data.id_ejecucion)
            )
            ejecucion_db = res_ejec.scalar_one_or_none()
        except Exception as exc:
            logger.warning("Fallo al consultar ejecución en PostgreSQL: %s", exc)

    if not ejecucion_db and not ejecucion_mem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La ejecución de recomendación con ID {val_data.id_ejecucion} no existe.",
        )

    # 2. Validar que la recomendación elegida pertenezca a la misma ejecución
    if val_data.id_recomendacion_elegida is not None:
        rec_valida = False
        if ejecucion_db:
            try:
                res_rec = await db.execute(
                    select(Recomendacion).where(
                        Recomendacion.id_recomendacion == val_data.id_recomendacion_elegida,
                        Recomendacion.id_ejecucion == val_data.id_ejecucion,
                    )
                )
                if res_rec.scalar_one_or_none():
                    rec_valida = True
            except Exception:
                pass
        if not rec_valida and ejecucion_mem:
            recs_in_mem = ejecucion_mem.get("recomendaciones", [])
            if any(r.id_recomendacion == val_data.id_recomendacion_elegida for r in recs_in_mem):
                rec_valida = True

        if not rec_valida:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"La recomendación con ID {val_data.id_recomendacion_elegida} no pertenece "
                    f"a la ejecución {val_data.id_ejecucion}."
                ),
            )
        eligio = True
    else:
        eligio = bool(val_data.eligio_alternativa)

    comentario_clean = val_data.comentario.strip()[:500] if val_data.comentario else None
    ahora = datetime.now(timezone.utc)

    # Si hay conexión a BD, intentar persistir en PostgreSQL
    if ejecucion_db and db is not None:
        try:
            res_exist = await db.execute(
                select(Valoracion).where(Valoracion.id_ejecucion == val_data.id_ejecucion)
            )
            val_exist = res_exist.scalar_one_or_none()

            if val_exist:
                val_exist.utilidad = val_data.utilidad
                val_exist.eligio_alternativa = eligio
                val_exist.id_recomendacion_elegida = val_data.id_recomendacion_elegida
                val_exist.explicacion_comprensible = val_data.explicacion_comprensible
                val_exist.comentario = comentario_clean
                await db.commit()
                await db.refresh(val_exist)

                return ValoracionResponse(
                    id_valoracion=val_exist.id_valoracion,
                    id_ejecucion=val_exist.id_ejecucion,
                    utilidad=val_exist.utilidad,
                    eligio_alternativa=val_exist.eligio_alternativa,
                    id_recomendacion_elegida=val_exist.id_recomendacion_elegida,
                    explicacion_comprensible=val_exist.explicacion_comprensible,
                    comentario=val_exist.comentario,
                    fecha=val_exist.fecha,
                    mensaje="Valoración actualizada exitosamente",
                )

            nueva_val = Valoracion(
                id_ejecucion=val_data.id_ejecucion,
                utilidad=val_data.utilidad,
                eligio_alternativa=eligio,
                id_recomendacion_elegida=val_data.id_recomendacion_elegida,
                explicacion_comprensible=val_data.explicacion_comprensible,
                comentario=comentario_clean,
            )
            db.add(nueva_val)
            await db.commit()
            await db.refresh(nueva_val)

            return ValoracionResponse(
                id_valoracion=nueva_val.id_valoracion,
                id_ejecucion=nueva_val.id_ejecucion,
                utilidad=nueva_val.utilidad,
                eligio_alternativa=nueva_val.eligio_alternativa,
                id_recomendacion_elegida=nueva_val.id_recomendacion_elegida,
                explicacion_comprensible=nueva_val.explicacion_comprensible,
                comentario=nueva_val.comentario,
                fecha=nueva_val.fecha,
                mensaje="Valoración registrada exitosamente",
            )
        except Exception as exc:
            logger.warning("Fallo en persistencia de feedback en PostgreSQL (%s). Guardando en memoria.", exc)

    # Persistencia en memoria
    val_id = MEM_VALORACIONES.get(val_data.id_ejecucion, {}).get("id_valoracion", len(MEM_VALORACIONES) + 1)
    record = {
        "id_valoracion": val_id,
        "id_ejecucion": val_data.id_ejecucion,
        "utilidad": val_data.utilidad,
        "eligio_alternativa": eligio,
        "id_recomendacion_elegida": val_data.id_recomendacion_elegida,
        "explicacion_comprensible": val_data.explicacion_comprensible,
        "comentario": comentario_clean,
        "fecha": ahora,
    }
    MEM_VALORACIONES[val_data.id_ejecucion] = record

    return ValoracionResponse(
        id_valoracion=val_id,
        id_ejecucion=val_data.id_ejecucion,
        utilidad=val_data.utilidad,
        eligio_alternativa=eligio,
        id_recomendacion_elegida=val_data.id_recomendacion_elegida,
        explicacion_comprensible=val_data.explicacion_comprensible,
        comentario=comentario_clean,
        fecha=ahora,
        mensaje="Valoración registrada exitosamente en memoria",
    )


from gemini_service import consultar_gemini, buscar_atractivos_relevantes, es_consulta_de_atractivos


def _respuesta_local_fallback(
    message: str,
    context: Optional[dict[str, Any] | str],
    catalogo: Optional[pd.DataFrame],
) -> ChatResponse:
    """Respuesta heurística instantánea, cálida y de alta calidad para el turista."""
    msg_lower = message.lower().strip()
    related = buscar_atractivos_relevantes(message, context=context, catalogo=catalogo, limit=4) if es_consulta_de_atractivos(message) else []

    context_name = None
    context_prov = "San Martín"
    if isinstance(context, dict):
        context_name = (
            context.get("name")
            or context.get("nombre")
            or context.get("title")
            or context.get("destination")
            or context.get("atractivo")
        )
        context_prov = context.get("province") or context.get("provincia") or "San Martín"
    elif isinstance(context, str) and context.strip():
        context_name = context.strip()

    c_clean = str(context_name).strip() if context_name else None

    # Acciones por defecto
    if c_clean:
        actions = [
            f"¿Qué actividades hacer en {c_clean}?",
            f"¿Cómo llegar a {c_clean}?",
            f"¿Cuál es el costo y horario en {c_clean}?",
            "¿Qué otros atractivos hay cerca?",
        ]
    else:
        actions = [
            "¿Cuáles son las mejores cataratas cerca de Tarapoto?",
            "¿Qué actividades puedo hacer en la Laguna de Sauce?",
            "¿Qué opciones culturales y artesanales hay en Lamas?",
            "¿Dónde degustar la mejor gastronomía típica de la región?",
        ]

    # 1. Detección de presentación personal / nombre del turista
    match_nombre = re.search(r"(?:mi\s+nombre\s+es|me\s+llamo|soy)\s+([A-Za-zÀ-ÿ]+)", msg_lower)
    if match_nombre:
        nombre_turista = match_nombre.group(1).capitalize()
        if c_clean:
            reply = (
                f"¡Mucho gusto, {nombre_turista}! Qué alegría saludarte y tenerte por aquí 😊.\n\n"
                f"Veo que te encuentras explorando **{c_clean}** ({context_prov}), uno de los destinos más hermosos de la región. "
                f"Dime, {nombre_turista}, ¿qué planes tienes en mente para hoy? ¿Te gustaría saber qué actividades acuáticas hacer, "
                f"cómo llegar a los mejores rincones o dónde probar la comida típica?"
            )
        else:
            reply = (
                f"¡Bienvenido a San Martín, {nombre_turista}! Es un verdadero placer saludarte 😊.\n\n"
                f"Estoy aquí para guiarte por las 10 provincias de la región. Cuéntame, {nombre_turista}, "
                f"¿qué tipo de experiencia buscas: cataratas refrescantes, lagunas relajantes, aventura o gastronomía?"
            )
        return ChatResponse(reply=reply, suggested_actions=actions, related_atractivos=related)

    # 2. Saludos de cortesía ("cómo estás", "qué tal", "cómo te va") -> Prioridad absoluta
    if any(k in msg_lower for k in ["como estas", "cómo estás", "que tal", "qué tal", "como te va", "cómo te va", "todo bien"]):
        if c_clean:
            reply = (
                f"😊 ¡Hola! Muy bien, muchas gracias por preguntar. ¡Qué gusto saludarte!\n\n"
                f"Veo que estás explorando **{c_clean}** 🌴. ¿En qué te puedo orientar hoy? "
                f"¿Te gustaría saber qué actividades hacer, cómo llegar desde Tarapoto o sus costos y mejores horarios?"
            )
        else:
            reply = (
                "😊 ¡Hola! Muy bien, muchas gracias por preguntar. ¡Qué gusto saludarte!\n\n"
                "¿En qué puedo ayudarte hoy a planear tu viaje por San Martín? "
                "Cuéntame si buscas cataratas cristalinas, lagunas tranquilas, lugares culturales o dónde comer rico."
            )
        return ChatResponse(reply=reply, suggested_actions=actions, related_atractivos=related)

    # 3. Saludo simple ("hola", "buenas", "buenos días")
    if msg_lower in ("hola", "buenas", "buenos dias", "buenos días", "buenas tardes", "buenas noches", "hey"):
        if c_clean:
            reply = (
                f"👋 ¡Hola! Qué alegría saludarte. Estás explorando **{c_clean}**, uno de los destinos más hermosos de {context_prov}.\n\n"
                f"¿En qué te puedo colaborar hoy? ¿Deseas conocer qué actividades hacer, cómo llegar o recomendaciones para tu visita?"
            )
        else:
            reply = (
                "👋 ¡Hola! Bienvenido a tu **Guía Inteligente de la Región San Martín**.\n\n"
                "Conozco los 297 atractivos oficiales de la región: caídas de agua, lagunas, naturaleza, cultura y gastronomía. "
                "¿Qué tipo de experiencia estás buscando hoy?"
            )
        return ChatResponse(reply=reply, suggested_actions=actions, related_atractivos=related)

    # 4. Paseos en bote / actividades acuáticas
    if any(k in msg_lower for k in ["bote", "lancha", "paseo", "navegar", "kayak", "acuatic"]):
        destino = c_clean or "la Laguna de Sauce"
        reply = (
            f"🚤 **Paseos en bote y actividades acuáticas en {destino}**:\n\n"
            f"- **Paseos en bote tradicional:** El alquiler de un bote privado para grupos o familias suele rondar entre **S/ 80 y S/ 120**, "
            f"con un recorrido de 1h 30min a 2h haciendo paradas escénicas. En botes colectivos, el costo es de **S/ 15 a S/ 25** por persona.\n"
            f"- **Deportes de aventura:** También puedes alquilar kayaks, motos acuáticas o hacer canopy cruzando sobre el agua.\n\n"
            "¿Deseas saber cuál es el mejor horario para embarcarte?"
        )
        return ChatResponse(reply=reply, suggested_actions=actions, related_atractivos=related)

    # 5. Consultas sobre cómo llegar / ruta
    if any(k in msg_lower for k in ["cómo llegar", "como llegar", "ruta", "transporte", "viaje", "distancia", "llegar"]):
        destino = c_clean or "este destino"
        reply = (
            f"🚗 **Cómo llegar a {destino}**:\n\n"
            f"Desde la ciudad de Tarapoto, puedes tomar transporte colectivo, taxi o tour guiado. "
            f"Para destinos como Sauce, el trayecto incluye cruzar el río Huallaga en balsa cautiva (unos 50 km, aprox. 1h 30min). "
            f"Para cataratas cercanas como Ahuashiyacu, está a tan solo 20 minutos por la carretera a Yurimaguas. "
            "Te sugiero salir temprano por la mañana para aprovechar el día y llevar repelente y protector solar."
        )
        return ChatResponse(reply=reply, suggested_actions=actions, related_atractivos=related)

    # 6. Consultas sobre costos / precios / tarifas
    if any(k in msg_lower for k in ["costo", "precio", "cuánto", "cuanto", "entrada", "tarifa", "presupuesto"]):
        destino = c_clean or "los atractivos de San Martín"
        reply = (
            f"🎟️ **Costos referenciales para {destino}**:\n\n"
            f"El acceso a atractivos naturales en la región suele tener tarifas de ingreso muy accesibles, "
            f"generalmente entre **S/ 5.00 y S/ 15.00** por persona. "
            f"Las actividades adicionales (paseos en bote, canopy o deportes de aventura) oscilan entre **S/ 20 y S/ 40**."
        )
        return ChatResponse(reply=reply, suggested_actions=actions, related_atractivos=related)

    # 5. Consultas temáticas generales
    if any(k in msg_lower for k in ["catarata", "cascada", "caida"]):
        reply = (
            "🌊 **Cataratas imperdibles en San Martín**:\n\n"
            "- **Catarata de Ahuashiyacu**: A solo 20 min de Tarapoto, caída de 40 metros ideal para un chapuzón refrescante.\n"
            "- **Catarata de Huacamaillo**: En San Antonio de Cumbaza, perfecta para caminatas y naturaleza.\n"
            "- **Cataratas de Carpishuyacu**: Con pozas termales naturales y senderos en selva virgen.\n\n"
            "¿Te gustaría conocer cómo llegar a alguna de ellas o sus costos de entrada?"
        )
    elif any(k in msg_lower for k in ["laguna", "sauce", "azul"]):
        reply = (
            "⛵ **Laguna Azul (Sauce)**:\n\n"
            "Ubicada a 52 km de Tarapoto, es el principal destino de relax y deportes acuáticos de San Martín. "
            "El viaje incluye cruzar el río Huallaga en balsa cautiva. En la laguna puedes realizar navegación en lancha, "
            "kayak, canopy, motos acuáticas y degustar trucha fresca o cecina ribereña."
        )
    elif any(k in msg_lower for k in ["lamas", "castillo"]):
        reply = (
            "🏰 **Lamas, la Ciudad de los Tres Pisos**:\n\n"
            "A solo 25 min de Tarapoto, visita obligada es el **Castillo de Lamas**, el tradicional "
            "**Barrio Nativo Wayku** (con artesanías, danzas y tradiciones de la etnia Kichwa) y "
            "los deliciosos cafés y chocolates artesanales de la zona."
        )
    elif any(k in msg_lower for k in ["moyobamba", "orquidea", "termales"]):
        reply = (
            "🌺 **Moyobamba, Ciudad de las Orquídeas**:\n\n"
            "Disfruta de sus famosos orquidearios, relájate en los **Baños Termales de San Mateo** y "
            "explora la reserva ecológica Tingana navegando entre ríos y aguajales vírgenes."
        )
    elif any(k in msg_lower for k in ["comida", "gastronomia", "platos", "comer", "juane"]):
        reply = (
            "🍲 **Gastronomía de la Selva Sanmartinense**:\n\n"
            "Prueba el tradicional **Juane de gallina**, el sabroso **Tacacho con cecina y chorizo regional**, "
            "la **Patarashca** envuelta en hoja de bijao, y acompáñalos con refrescos naturales de camu camu o cocona."
        )
    elif c_clean:
        reply = (
            f"🌴 Estás explorando **{c_clean}** en {context_prov}.\n\n"
            f"Es un lugar excelente para disfrutar de los encantos de la selva. "
            f"A continuación te presento los atractivos y experiencias más recomendadas para tu visita:"
        )
    else:
        reply = (
            "🌿 ¡Hola! Conozco los 297 atractivos oficiales de la región San Martín, sus distancias, costos y dificultades. "
            "¿Qué tipo de viaje tienes en mente: cataratas, lagunas, aventura o gastronomía?"
        )

    return ChatResponse(
        reply=reply,
        suggested_actions=actions,
        related_atractivos=related,
    )


async def procesar_consulta_asistente(
    message: str,
    context: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
    engine: Any = None,
    history: Optional[list[dict[str, str]]] = None,
) -> ChatResponse:
    """
    Motor conversacional de TurismoIA San Martín:
    - Analiza cada mensaje del turista mediante Google Gemini API en tiempo real.
    - Respuestas generadas de forma dinámica, iterativa y personalizada por la IA.
    - Fallback heurístico solo si Gemini experimenta agotamiento de cuota o indisponibilidad de red.
    """
    catalogo = getattr(engine, "catalogo", None) if engine else None

    # Enviar absolutamente cada mensaje a Gemini API para su análisis generativo en tiempo real
    gemini_key = getattr(settings, "effective_gemini_api_key", None) or getattr(settings, "GEMINI_API_KEY", None)
    if gemini_key and gemini_key.strip() and not gemini_key.startswith("tu_gemini_api_key"):
        try:
            reply_text, actions, related = await consultar_gemini(
                message=message,
                context=context,
                catalogo=catalogo,
                session_id=session_id,
                history=history,
            )
            return ChatResponse(
                reply=reply_text,
                suggested_actions=actions,
                related_atractivos=related,
            )
        except Exception as exc:
            logger.warning("Fallo al consultar Gemini API (%s), utilizando contingencia local.", exc)
            return _respuesta_local_fallback(message=message, context=context, catalogo=catalogo)

    # Si no hay API Key configurada, usar contingencia local
    return _respuesta_local_fallback(message=message, context=context, catalogo=catalogo)

