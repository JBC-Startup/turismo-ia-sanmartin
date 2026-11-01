from __future__ import annotations

import logging
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


async def consultar_gemini(
    message: str,
    atractivos_relevantes: list[dict[str, Any]],
    contexto_activo: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """
    Invoca la API de Google Gemini para redactar una respuesta conversacional enriquecida,
    usando como base fidedigna los atractivos del catálogo oficial seleccionados por el modelo ML.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or not api_key.strip():
        return None

    # Sintetizar información verificada de los atractivos para contextualizar al modelo
    destinos_contexto = []
    for a in atractivos_relevantes[:5]:
        destinos_contexto.append(
            f"- **{a['nombre']}** ({a.get('provincia', 'San Martín')} · {a.get('distrito', '')}): "
            f"{a.get('descripcion', '')} "
            f"[Duración: {a.get('duracion_horas', 2.0)}h | "
            f"Costo: S/ {a.get('costo_pen', 0.0):.2f} | "
            f"Dificultad: {a.get('dificultad', 'Media')}]"
        )
    destinos_str = "\n".join(destinos_contexto) if destinos_contexto else "Catálogo general de atractivos de San Martín."

    contexto_pantalla = ""
    if contexto_activo and isinstance(contexto_activo, dict):
        c_nom = contexto_activo.get("name") or contexto_activo.get("nombre", "")
        c_prov = contexto_activo.get("province") or contexto_activo.get("provincia", "")
        c_desc = contexto_activo.get("description") or contexto_activo.get("descripcion", "")
        if c_nom:
            contexto_pantalla = (
                f"\n\n[Destino actualmente seleccionado en la pantalla del turista: {c_nom} ({c_prov}). "
                f"Descripción: {c_desc}]"
            )

    system_prompt = (
        "Eres el Asistente y Guía Turístico Inteligente oficial de la región San Martín, Perú (TurismoIA San Martín). "
        "Tu misión es orientar al turista con respuestas dinámicas, acogedoras, concisas y fidedignas en español.\n\n"
        "DIRECTRICES:\n"
        "1. Usa como fuente primaria la siguiente información verificada del catálogo oficial:\n"
        f"{destinos_str}{contexto_pantalla}\n\n"
        "2. Responde en 2 a 3 párrafos breves o viñetas concisas con formato Markdown legible (resalta destinos en negrita).\n"
        "3. Incluye datos prácticos reales (precios referenciales en soles, tiempos de visita, tipo de calzado, clima cálido/húmedo o recomendaciones de traslado desde Tarapoto, Moyobamba o Lamas).\n"
        "4. Si la consulta es amplia o sobre gastronomía/cultura, orienta con platos emblemáticos (juane, tacacho, patarashca, café y cacao orgánico) y sitios típicos.\n"
        "5. Sé directo, cálido y no inventes destinos fuera de San Martín."
    )

    candidate_models = [settings.GEMINI_MODEL, "gemini-3.1-flash-lite", "gemini-3.5-flash"]
    # Eliminar duplicados manteniendo orden
    candidate_models = list(dict.fromkeys(m for m in candidate_models if m))

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{system_prompt}\n\nPregunta del turista: {message}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 650,
        }
    }

    try:
        import httpx
        async with httpx.AsyncClient(timeout=8.0) as client:
            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key.strip()}"
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip()
                    else:
                        logger.warning("Gemini API (%s) respondió con código %d: %s", model_name, resp.status_code, resp.text[:180])
                except Exception as req_exc:
                    logger.debug("Error intentando modelo %s: %s", model_name, req_exc)
    except Exception as exc:
        logger.warning("Fallo al comunicarse con Gemini API: %s. Operando con fallback.", exc)

    return None


async def procesar_consulta_asistente(
    message: str,
    context: Optional[dict[str, Any]],
    engine: Any,
) -> ChatResponse:
    """
    Motor conversacional de TurismoIA San Martín:
    - Interpreta la intención del turista y busca atractivos reales mediante similitud semántica en el catálogo.
    - Si `GEMINI_API_KEY` está configurada en .env, genera una respuesta inteligente, dinámica y personalizada.
    - Si no está disponible, utiliza el motor de respuesta enriquecido en memoria.
    - Devuelve la respuesta, las acciones sugeridas y las tarjetas de destinos oficiales.
    """
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
    catalogo = getattr(engine, "catalogo", None) if engine else None

    # Contexto activo de la vista (ej. destino seleccionado en explorador)
    context_name = None
    if context and isinstance(context, dict):
        context_name = context.get("name") or context.get("nombre")

    related: list[dict[str, Any]] = []

    # 1. Búsqueda semántica y recuperación de atractivos relevantes del catálogo
    if catalogo is not None and not catalogo.empty:
        matches = pd.DataFrame()

        # Priorizar si coincide con el destino en pantalla
        if context_name:
            c_norm = normalizar_cadena(context_name)
            c_matches = catalogo[catalogo["nombre_recurso"].apply(normalizar_cadena).str.contains(c_norm, regex=False, na=False)]
            if not c_matches.empty:
                matches = pd.concat([matches, c_matches])

        # Búsqueda semántica usando el vectorizador del motor si está disponible
        pipeline = getattr(engine, "feature_pipeline", None)
        if pipeline and hasattr(pipeline, "tfidf") and hasattr(engine, "X_global"):
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                # Vectorizar texto de consulta
                q_vec = pipeline.tfidf.transform([msg_clean]) * 5.0
                # Extraer componente de texto de X_global
                n_text_cols = len(pipeline.tfidf.get_feature_names_out())
                X_text_corpus = engine.X_global[:, :n_text_cols]
                text_sims = cosine_similarity(q_vec, X_text_corpus).flatten()

                top_k_indices = text_sims.argsort()[::-1][:5]
                top_df = catalogo.iloc[top_k_indices]
                matches = pd.concat([matches, top_df]).drop_duplicates(subset=["id_recurso"])
            except Exception as exc:
                logger.debug("Búsqueda vectorial en chat falló, usando filtro léxico: %s", exc)

        # Fallback a búsqueda léxica si no hubo suficientes coincidencias
        if len(matches) < 3:
            term_candidates = [w for w in msg_lower.replace(",", " ").replace("?", "").split() if len(w) > 3]
            if term_candidates:
                pattern = "|".join([normalizar_cadena(t) for t in term_candidates])
                lexical_matches = catalogo[
                    catalogo["nombre_recurso"].apply(normalizar_cadena).str.contains(pattern, regex=True, na=False) |
                    catalogo["etiquetas_interes"].apply(normalizar_cadena).str.contains(pattern, regex=True, na=False) |
                    catalogo["subtipo"].apply(normalizar_cadena).str.contains(pattern, regex=True, na=False) |
                    catalogo["provincia"].apply(normalizar_cadena).str.contains(pattern, regex=True, na=False)
                ]
                matches = pd.concat([matches, lexical_matches]).drop_duplicates(subset=["id_recurso"])

        # Si aún no hay matches, tomar una selección representativa
        sample_rows = matches.head(3) if not matches.empty else catalogo.head(3)

        for _, row in sample_rows.iterrows():
            costo = float(row.get("costo_referencial_pen", 0.0))
            related.append({
                "id_recurso": str(row.get("id_recurso", "")),
                "nombre": str(row.get("nombre_recurso", "")),
                "provincia": str(row.get("provincia", "")),
                "distrito": str(row.get("distrito", "")),
                "duracion_horas": float(row.get("duracion_estimada_horas", 2.0)),
                "costo_pen": costo,
                "dificultad": str(row.get("nivel_dificultad", "Media")),
                "imagen_url": str(row.get("imagen_url", "")),
                "descripcion": str(row.get("descripcion_corta", ""))[:180] + ("..." if len(str(row.get("descripcion_corta", ""))) > 180 else ""),
            })

    # 2. Generación con Gemini AI si la clave está disponible
    gemini_reply = await consultar_gemini(
        message=msg_clean,
        atractivos_relevantes=related,
        contexto_activo=context,
    )

    # 3. Fallback dinámico si Gemini no está activo o no respondió
    if gemini_reply:
        reply = gemini_reply
    else:
        # Generador de respuesta dinámica contextual basado en el catálogo
        if context_name:
            c_prov = context.get('province') or context.get('provincia') or 'San Martín'
            reply = (
                f"📍 **{context_name}** es uno de los destinos emblemáticos de la provincia de **{c_prov}**. "
                f"Para visitarlo te recomiendo calzado adecuado con buen agarre, ropa ligera y repelente contra insectos. "
                f"Las primeras horas de la mañana son ideales para evitar las horas de mayor calor y disfrutar de la luz natural."
            )
        elif any(k in msg_lower for k in ["catarata", "cascada", "caida", "ahuashiyacu"]):
            reply = (
                "🌊 En la región San Martín destacan espectaculares caídas de agua como **Ahuashiyacu** "
                "(a solo 20 min de Tarapoto), **Pucayaquillo** en Shapaja (caminata refrescante en selva) y "
                "las cascadas de **Lamas** y **Moyobamba**. La mayoría cuenta con senderos accesibles y costos de ingreso entre S/ 5 y S/ 15."
            )
        elif any(k in msg_lower for k in ["laguna", "sauce", "azul", "lago"]):
            reply = (
                "⛵ La **Laguna de Sauce (Laguna Azul)** es la joya lacustre de San Martín, a 52 km de Tarapoto cruzando el río Huallaga en balsa cautiva. "
                "Ofrece navegación en bote, kayak, descanso en resorts ribereños y deliciosa gastronomía de pescados amazónicos."
            )
        elif any(k in msg_lower for k in ["lamas", "castillo", "wayku"]):
            reply = (
                "🏰 **Lamas**, la histórica 'Ciudad de los Tres Pisos', ofrece una mezcla única de naturaleza y herencia cultural. "
                "No te pierdas el **Castillo de Lamas**, el **Barrio Nativo Kechwa El Wayku**, y sus talleres de artesanía y chocolate artesanal."
            )
        elif any(k in msg_lower for k in ["moyobamba", "orquidea", "san mateo"]):
            reply = (
                "🌺 **Moyobamba**, la 'Ciudad de las Orquídeas', cautiva con sus orquidearios Waqanki, los relajantes "
                "**Baños Termales de San Mateo** y la navegación ecológica en la reserva Tingana por el río Mayo."
            )
        elif any(k in msg_lower for k in ["comida", "gastronomia", "comer", "juane", "cacao", "chocolate", "cafe"]):
            reply = (
                "🍲 ¡La gastronomía sanmartinense es un deleite amazónico! Disfruta del auténtico **Juane de gallina**, "
                "el **Tacacho con cecina y chorizo regional**, la **Patarashca** a la parrilla, y visita emprendimientos como "
                "**Misky Cacao** o la **Fábrica de Chocolates Orquídea**."
            )
        elif any(k in msg_lower for k in ["familia", "ninos", "accesib", "facil"]):
            reply = (
                "👨‍👩‍👧‍👦 Para viajes familiares o con ritmo pausado, te sugiero destinos con dificultad baja como "
                "las **Cataratas de Ahuashiyacu**, el paseo por la **Laguna de Sauce**, el **Castillo de Lamas** y los miradores urbanos de Tarapoto y Moyobamba."
            )
        else:
            n_destinos = len(related)
            destinos_mencionados = ", ".join([f"**{r['nombre']}** ({r['provincia']})" for r in related[:2]])
            reply = (
                f"🌿 ¡Hola! Soy tu **Guía Inteligente de San Martín**. Conozco los 297 atractivos oficiales de la región. "
                f"Para tu consulta te recomiendo explorar {destinos_mencionados}. "
                f"¿Deseas detalles sobre rutas de acceso, costos de entrada o las mejores temporadas para visitarlos?"
            )

    # Sugerencias contextuales y fluidas de preguntas de seguimiento
    actions: list[str] = []
    if related:
        primero = related[0]["nombre"]
        actions.append(f"¿Cómo llegar a {primero}?")
        actions.append(f"¿Cuál es el costo de ingreso a {primero}?")
        if len(related) > 1:
            segundo = related[1]["nombre"]
            actions.append(f"Cuéntame más sobre {segundo}")

    if len(actions) < 4:
        if any(k in msg_lower for k in ["catarata", "cascada", "agua"]):
            actions.extend(["¿Qué calzado se necesita para las cataratas?", "¿Cuáles son las más cercanas a Tarapoto?"])
        elif any(k in msg_lower for k in ["sauce", "laguna", "azul"]):
            actions.extend(["¿Cómo cruzar el río Huallaga en balsa?", "¿Qué actividades náuticas hay en Sauce?"])
        elif any(k in msg_lower for k in ["lamas", "castillo"]):
            actions.extend(["¿Cuánto cuesta la entrada al Castillo de Lamas?", "¿Dónde conocer artesanía en El Wayku?"])
        elif any(k in msg_lower for k in ["moyobamba", "orquidea"]):
            actions.extend(["¿Cuáles son los horarios de los Baños Termales?", "¿Dónde visitar los mejores orquidearios?"])
        else:
            actions.extend([
                "¿Cuáles son las cataratas más recomendadas?",
                "¿Qué platos típicos probar en San Martín?",
                "¿Qué atractivos son ideales para la familia?",
            ])

    actions = list(dict.fromkeys(actions))[:4]

    return ChatResponse(
        reply=reply,
        suggested_actions=actions,
        related_atractivos=related,
    )
