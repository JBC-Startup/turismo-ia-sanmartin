from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Any, Optional

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    PreferenciaRequest,
    RecomendacionItem,
    RecomendacionResponse,
    ValoracionRequest,
    ValoracionResponse,
)

logger = logging.getLogger(__name__)


class CatalogCache:
    """
    Caché en memoria de catálogos y metadatos de PostgreSQL para optimización extrema.
    Se carga una sola vez durante el lifespan del servidor.
    """

    def __init__(self) -> None:
        self.atractivo_map: dict[str, int] = {}       # codigo_recurso -> id_atractivo
        self.atractivo_name_map: dict[str, int] = {}  # nombre_upper -> id_atractivo
        self.provincia_map: dict[str, str] = {}       # nombre_upper -> id_provincia
        self.compania_map: dict[str, int] = {}        # nombre_lower -> id_compania
        self.dificultad_map: dict[str, int] = {}      # nombre_lower -> id_dificultad
        self.active_model_id: int = 1
        self.cluster_map: dict[int, int] = {}         # numero_cluster -> id_cluster

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
    Calcula cuántos atractivos satisfacen los filtros duros obligatorios.
    """
    tiempo_max = float(perfil.get("tiempo_disponible_horas", 8.0))
    presupuesto_val = perfil.get("presupuesto_max_pen")
    presupuesto_max = float(presupuesto_val) if presupuesto_val is not None else 9999.0
    provincia_in = str(perfil.get("provincia", "Todas")).strip()
    filtro_prov_activo = provincia_in.upper() not in ["TODAS", "TODOS", "CUALQUIERA", ""]

    mask_tiempo = catalogo["duracion_estimada_horas"] <= tiempo_max
    mask_costo = catalogo["costo_referencial_pen"] <= presupuesto_max
    mask_prov = (
        catalogo["provincia"].str.upper() == provincia_in.upper()
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
    db.add(sesion)
    await db.flush()

    # Si se seleccionó provincia específica, registrarla en sesion_provincia
    prov_key = preferencias.provincia.upper()
    if prov_key not in ["TODAS", "TODOS", "CUALQUIERA", ""]:
        id_prov = cache.provincia_map.get(prov_key)
        if id_prov:
            sesion_prov = SesionProvincia(
                id_sesion=sesion.id_sesion,
                id_provincia=id_prov,
            )
            db.add(sesion_prov)

    # 6. Persistir EjecucionRecomendacion
    ejecucion = EjecucionRecomendacion(
        id_sesion=sesion.id_sesion,
        id_modelo=cache.active_model_id,
        id_cluster=id_cluster_fk,
        total_candidatos=total_candidatos,
        tiempo_respuesta_ms=elapsed_ms,
        parametros_aplicados=preferencias.model_dump(),
    )
    db.add(ejecucion)
    await db.flush()

    # 7. Persistir Recomendaciones individuales (Top-N)
    items_response: list[RecomendacionItem] = []
    fallback_provincia_aplicado = False

    for r in recs:
        cod_recurso = r["id_recurso"]
        id_atractivo = cache.atractivo_map.get(cod_recurso)
        if not id_atractivo:
            id_atractivo = cache.atractivo_name_map.get(r["nombre_recurso"].upper(), 1)

        afinidad_norm = round(max(0.0, min(1.0, float(r["afinidad_pct"]) / 100.0)), 4)
        explicacion_truncada = str(r["justificacion"])[:400]
        cumple_filtros = not r.get("fallback_provincia", False)
        if r.get("fallback_provincia", False):
            fallback_provincia_aplicado = True

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

        items_response.append(
            RecomendacionItem(
                id_recomendacion=rec_db.id_recomendacion,
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

    await db.commit()

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
    """
    # 1. Validar existencia de la ejecución
    res_ejec = await db.execute(
        select(EjecucionRecomendacion).where(EjecucionRecomendacion.id_ejecucion == val_data.id_ejecucion)
    )
    ejecucion = res_ejec.scalar_one_or_none()
    if not ejecucion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La ejecución de recomendación con ID {val_data.id_ejecucion} no existe.",
        )

    # 2. Validar que la recomendación elegida pertenezca a la misma ejecución
    if val_data.id_recomendacion_elegida is not None:
        res_rec = await db.execute(
            select(Recomendacion).where(
                Recomendacion.id_recomendacion == val_data.id_recomendacion_elegida,
                Recomendacion.id_ejecucion == val_data.id_ejecucion,
            )
        )
        rec = res_rec.scalar_one_or_none()
        if not rec:
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

    # 3. Verificar si ya existe valoración previa para esta ejecución
    res_exist = await db.execute(
        select(Valoracion).where(Valoracion.id_ejecucion == val_data.id_ejecucion)
    )
    val_exist = res_exist.scalar_one_or_none()

    comentario_clean = val_data.comentario.strip()[:500] if val_data.comentario else None

    if val_exist:
        # Actualización idempotente
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

    # 4. Creación de nueva valoración
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
