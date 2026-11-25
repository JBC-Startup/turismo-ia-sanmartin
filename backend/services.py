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


from gemini_service import (
    buscar_atractivos_relevantes,
    campos_practicos_solicitados,
    consultar_gemini_resultado,
    es_consulta_de_atractivos,
)


def _respuesta_local_fallback(
    message: str,
    context: Optional[dict[str, Any] | str],
    catalogo: Optional[pd.DataFrame],
    fallback_reason: Optional[str] = None,
) -> ChatResponse:
    """Fallback conversacional que usa solo registros coincidentes y campos respaldados."""
    msg_lower = message.lower().strip()
    related = buscar_atractivos_relevantes(message, context=context, catalogo=catalogo, limit=4) if es_consulta_de_atractivos(message) else []
    actions = [
        "¿Qué atractivos aparecen en el catálogo?",
        "¿Qué provincia de San Martín te interesa?",
        "¿Qué tipo de experiencia estás buscando?",
    ]

    def result(reply: str) -> ChatResponse:
        return ChatResponse(
            reply=reply,
            suggested_actions=actions,
            related_atractivos=related,
            source="local",
            model=None,
            fallback_reason=fallback_reason,
        )

    if any(term in msg_lower for term in ("quién eres", "quien eres", "cómo te llamas", "como te llamas", "qué eres", "que eres", "quién es mono fisi", "quien es mono fisi", "quién es loro fisi", "quien es loro fisi")):
        return result("¡Soy Loro FISI, la mascota virtual de TurismoIA San Martín! ¿Qué lugar te da curiosidad?")

    if msg_lower in ("hola", "hola loro", "hola loro fisi", "buenas", "buenos días", "buenos dias", "buenas tardes", "buenas noches", "hey") or any(term in msg_lower for term in ("cómo estás", "como estas", "qué tal", "que tal", "todo bien")):
        return result("¡Hola! Qué gusto leerte, pe. ¿Qué te gustaría explorar hoy?")

    requested_fields = campos_practicos_solicitados(message)
    if requested_fields:
        labels = {
            "costo_pen": ("costo", "S/ {}"),
            "horario_referencial": ("horario", "{}"),
            "ruta_acceso_desde_tarapoto": ("ruta", "{}"),
            "distancia_km_tarapoto": ("distancia desde Tarapoto", "{} km"),
            "duracion_horas": ("duración estimada", "{} h"),
            "tiempo_viaje_horas_tarapoto": ("tiempo de viaje desde Tarapoto", "{} h"),
        }
        fields = requested_fields
        if "duracion_horas" in fields and "tiempo de viaje" in msg_lower:
            fields = [field for field in fields if field != "duracion_horas"] + ["tiempo_viaje_horas_tarapoto"]
        facts: list[str] = []
        missing: list[str] = []
        for field in fields:
            label, formatter = labels[field]
            values = [item for item in related if item.get(field) is not None and item.get("fecha_verificacion") and item.get("url_fuente")]
            if values:
                item = values[0]
                if field == "costo_pen" and item.get("costo_es_acceso_libre"):
                    value_text = "acceso libre"
                else:
                    value_text = formatter.format(item[field])
                facts.append(f"{item['nombre']}: la ficha registra {value_text} (verificada el {item['fecha_verificacion']}; puede haber cambiado).")
            else:
                missing.append(label)
        if facts and not missing:
            reply = "Según la ficha disponible, " + " ".join(facts) + " Te recomiendo confirmar las condiciones actuales con la fuente antes de salir."
        elif facts:
            reply = "Según la ficha disponible, " + " ".join(facts) + f" No tengo un dato confirmado de {', '.join(missing)} en el catálogo."
        else:
            reply = f"Ahorita no tengo un dato confirmado de {', '.join(missing or [labels[field][0] for field in fields])} para ese atractivo. Prefiero no darte una cifra o indicación al tanteo."
        return result(reply)

    if related:
        names = [
            f"{item['nombre']} ({item['provincia']})" if item.get("provincia") else item["nombre"]
            for item in related if item.get("nombre")
        ]
        if names:
            return result("¡Ya! En los registros disponibles aparecen " + ", ".join(names[:4]) + ". ¿Cuál te gustaría explorar primero?")

    return result("¡Aquí está Loro FISI, listo para explorar San Martín contigo! Dime qué destino, provincia o actividad tienes en mente y revisaré qué aparece en el catálogo.")


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

    normalized_message = message.strip().lower().rstrip(".!¿?¡ ")
    identity_question = any(term in normalized_message for term in (
        "quién eres", "quien eres", "cómo te llamas", "como te llamas", "qué eres", "que eres",
        "quién es mono fisi", "quien es mono fisi", "quién es loro fisi", "quien es loro fisi",
    ))
    simple_greeting = normalized_message in {
        "hola", "buenas", "buenos días", "buenos dias", "buenas tardes", "buenas noches", "hey",
        "cómo estás", "como estas", "qué tal", "que tal", "todo bien", "hola loro", "hola loro fisi",
    }
    if identity_question or simple_greeting:
        return _respuesta_local_fallback(message=message, context=context, catalogo=catalogo)

    practical_fields = campos_practicos_solicitados(message)
    if practical_fields:
        matches = buscar_atractivos_relevantes(message, context=context, catalogo=catalogo, limit=4)
        fields = practical_fields
        if "duracion_horas" in fields and "tiempo de viaje" in message.lower():
            fields = [field for field in fields if field != "duracion_horas"] + ["tiempo_viaje_horas_tarapoto"]
        if any(not any(item.get(field) is not None for item in matches) for field in fields):
            return _respuesta_local_fallback(
                message=message,
                context=context,
                catalogo=catalogo,
                fallback_reason="unverified_data_unavailable",
            )

    if pide_recomendaciones_destinos(message) and not buscar_atractivos_relevantes(
        message,
        context=context,
        catalogo=catalogo,
        limit=4,
    ):
        return _respuesta_local_fallback(
            message=message,
            context=context,
            catalogo=catalogo,
            fallback_reason="unverified_data_unavailable",
        )

    # Enviar absolutamente cada mensaje a Gemini API para su análisis generativo en tiempo real
    gemini_key = getattr(settings, "effective_gemini_api_key", None) or getattr(settings, "GEMINI_API_KEY", None)
    if gemini_key and gemini_key.strip() and not gemini_key.startswith("tu_gemini_api_key"):
        try:
            result = await consultar_gemini_resultado(
                message=message,
                context=context,
                catalogo=catalogo,
                session_id=session_id,
                history=history,
            )
            return ChatResponse(
                reply=result.reply,
                suggested_actions=result.suggested_actions,
                related_atractivos=result.related_atractivos,
                source=result.source,
                model=result.model,
                fallback_reason=result.fallback_reason,
            )
        except Exception as exc:
            reason = "timeout" if isinstance(exc, TimeoutError) else "gemini_error"
            logger.warning("Fallo al consultar Gemini API (%s), utilizando contingencia local.", exc)
            return _respuesta_local_fallback(message=message, context=context, catalogo=catalogo, fallback_reason=reason)

    # Si no hay API Key configurada, usar contingencia local
    return _respuesta_local_fallback(message=message, context=context, catalogo=catalogo, fallback_reason="missing_api_key")

