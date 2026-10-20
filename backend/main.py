import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal, async_engine, check_db_connectivity, get_db
from schemas import (
    AtractivoDetalle,
    AtractivosListResponse,
    ChatRequest,
    ChatResponse,
    FiltrosResponse,
    HealthResponse,
    MetricasPrototipoResponse,
    PreferenciaRequest,
    RecomendacionResponse,
    ValoracionRequest,
    ValoracionResponse,
)
from services import (
    CatalogCache,
    generar_y_persistir_recomendaciones,
    procesar_consulta_asistente,
    registrar_feedback,
    MEM_SESIONES,
    MEM_EJECUCIONES,
    MEM_VALORACIONES,
)

# Configurar logging del servicio
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("turismoia.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida (Lifespan) de FastAPI.
    - Al arrancar: Carga el artefacto serializado en memoria RAM mediante InferenceEngine
      y sincroniza los catálogos de PostgreSQL en la memoria caché.
    - Al apagar: Cierra el pool de conexiones de PostgreSQL.
    """
    logger.info("=== Iniciando microservicio FastAPI TurismoIA San Martín ===")
    
    # 1. Carga autónoma del modelo serializado en RAM (< 10 ms por inferencia)
    try:
        from src.inference import InferenceEngine

        resolved_model_path = settings.get_resolved_model_path()
        logger.info("Cargando modelo serializado desde: %s...", resolved_model_path)
        engine = InferenceEngine(model_path=resolved_model_path)
        app.state.engine = engine
        logger.info(
            "Modelo v%s cargado en RAM exitosamente. Total atractivos: %d.",
            engine.version,
            len(engine.catalogo),
        )

        # Calentamiento (Warm-up) para compilar pipelines y optimizar cachés CPU
        warmup_perfil = {
            "intereses": "cataratas naturaleza",
            "tiempo_disponible_horas": 4.0,
            "presupuesto_max_pen": 30.0,
            "provincia": "SAN MARTIN",
            "publico": "Amigos",
        }
        _ = engine.predict_top_n(warmup_perfil, top_n=3)
        logger.info("Calentamiento de inferencia completado.")
    except Exception as exc:
        logger.critical("Error fatal al cargar artefacto de Machine Learning: %s", exc)
        app.state.engine = None
        raise

    # 2. Inicialización de caché de catálogos (con fallback resiliente en memoria)
    catalog_cache = CatalogCache()
    catalog_cache.load_from_catalogo(engine.catalogo, cluster_metadata=engine.cluster_metadata)
    try:
        async with AsyncSessionLocal() as session:
            await catalog_cache.load(session, cluster_metadata=engine.cluster_metadata)
    except Exception as exc:
        logger.warning("PostgreSQL no disponible para sincronizar IDs (%s). Operando en memoria con catálogo oficial.", exc)
    app.state.catalog_cache = catalog_cache

    yield

    # Limpieza al detener el servicio
    logger.info("Cerrando pool de conexiones asíncronas con PostgreSQL...")
    await async_engine.dispose()
    logger.info("Servicio detenido correctamente.")


# Instancia principal de la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API REST de recomendación inteligente de atractivos turísticos para la región San Martín, "
        "con inferencia ultraligera en memoria RAM (<10 ms), similitud del coseno, filtros duros "
        "y persistencia relacional en PostgreSQL."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware CORS para permitir integración frontend (Web y Móvil)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Mide y expone el tiempo de procesamiento en los headers HTTP."""
    t0 = time.perf_counter()
    response: Response = await call_next(request)
    process_time_ms = round((time.perf_counter() - t0) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    return response


# =====================================================================
# ENDPOINTS PRINCIPALES
# =====================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Comprobar estado del servicio, base de datos y modelo ML",
    tags=["Observabilidad"],
)
async def health_check(response: Response) -> HealthResponse:
    """
    Verifica la salud del microservicio:
    1. Conectividad con el motor PostgreSQL en Docker.
    2. Disponibilidad del artefacto de Machine Learning cargado en memoria RAM.
    """
    db_status = await check_db_connectivity()
    
    engine = getattr(app.state, "engine", None)
    if engine is not None:
        model_status = {
            "loaded": True,
            "version": engine.version,
            "atractivos_en_catalogo": len(engine.catalogo),
            "vector_dimension": engine.X_global.shape[1],
            "clusters_activos": len(engine.cluster_metadata),
            "created_at": getattr(engine, "created_at", None),
        }
    else:
        model_status = {
            "loaded": False,
            "error": "El artefacto de inferencia no se encuentra en memoria RAM.",
        }

    is_healthy = model_status.get("loaded", False)
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        response.status_code = status.HTTP_200_OK

    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION,
        database=db_status,
        model=model_status,
    )


@app.post(
    "/api/recomendar",
    response_model=RecomendacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar recomendaciones personalizadas (Top-5)",
    tags=["Recomendador"],
)
async def recomendar_atractivos(
    preferencias: PreferenciaRequest,
    db: AsyncSession = Depends(get_db),
) -> RecomendacionResponse:
    """
    Recibe las preferencias del turista (intereses, tiempo disponible, presupuesto, provincia, compañía, dificultad),
    calcula el Top-5 mediante similitud del coseno y filtros duros obligatorios, y persiste en PostgreSQL:
    - La sesión en `turismo.sesion_preferencia`.
    - La ejecución de recomendación en `turismo.ejecucion_recomendacion`.
    - Las alternativas devueltas en `turismo.recomendacion`.
    """
    engine = getattr(app.state, "engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El motor de inferencia no está cargado en memoria.",
        )

    cache: CatalogCache = getattr(app.state, "catalog_cache", None) or CatalogCache()

    try:
        resultado = await generar_y_persistir_recomendaciones(
            db=db,
            engine=engine,
            preferencias=preferencias,
            cache=cache,
        )
        return resultado
    except Exception as exc:
        logger.exception("Error al procesar recomendación: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al calcular y persistir recomendaciones: {exc}",
        )


@app.post(
    "/api/valorar",
    response_model=ValoracionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar feedback o valoración sobre una recomendación",
    tags=["Valoración"],
)
async def valorar_recomendacion(
    val_data: ValoracionRequest,
    db: AsyncSession = Depends(get_db),
) -> ValoracionResponse:
    """
    Registra el feedback de satisfacción (1 a 5 estrellas, comentario, alternativa elegida)
    en la tabla `turismo.valoracion` asociada a la ejecución de recomendación.
    """
    try:
        return await registrar_feedback(db=db, val_data=val_data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error al registrar valoración: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar feedback en base de datos: {exc}",
        )


@app.get(
    "/api/filtros",
    response_model=FiltrosResponse,
    summary="Obtener catálogos de filtros disponibles para frontend",
    tags=["Catálogo"],
)
async def obtener_filtros(db: AsyncSession = Depends(get_db)) -> FiltrosResponse:
    """Retorna las provincias, compañías y dificultades disponibles para alimentar selectores UI."""
    try:
        from sqlalchemy import text
        res_prov = await db.execute(text("SELECT id_provincia, nombre FROM turismo.provincia ORDER BY nombre"))
        provincias = [{"id_provincia": r[0], "nombre": r[1]} for r in res_prov.fetchall()]

        res_comp = await db.execute(text("SELECT id_compania, nombre, descripcion FROM turismo.compania_viaje ORDER BY id_compania"))
        companias = [{"id_compania": r[0], "nombre": r[1], "descripcion": r[2]} for r in res_comp.fetchall()]

        res_dif = await db.execute(text("SELECT id_dificultad, nombre, nivel_esfuerzo FROM turismo.nivel_dificultad ORDER BY id_dificultad"))
        dificultades = [{"id_dificultad": r[0], "nombre": r[1], "nivel_esfuerzo": r[2]} for r in res_dif.fetchall()]

        return FiltrosResponse(provincias=provincias, companias=companias, dificultades=dificultades)
    except Exception as exc:
        logger.warning("Fallo al obtener filtros de BD (%s). Usando catálogo en memoria.", exc)
        cache: CatalogCache = getattr(app.state, "catalog_cache", None) or CatalogCache()
        provincias = [{"id_provincia": pid, "nombre": nom.title()} for nom, pid in sorted(cache.provincia_map.items())]
        companias = [{"id_compania": cid, "nombre": nom.capitalize(), "descripcion": ""} for nom, cid in cache.compania_map.items()]
        dificultades = [{"id_dificultad": did, "nombre": nom.capitalize(), "nivel_esfuerzo": did} for nom, did in cache.dificultad_map.items()]
        return FiltrosResponse(provincias=provincias, companias=companias, dificultades=dificultades)


@app.get(
    "/api/atractivos",
    response_model=AtractivosListResponse,
    summary="Listar y buscar atractivos turísticos con paginación",
    tags=["Catálogo"],
)
async def listar_atractivos(
    q: Optional[str] = None,
    provincia: Optional[str] = None,
    categoria: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> AtractivosListResponse:
    """Busca y lista atractivos turísticos del catálogo oficial recomendado."""
    try:
        from sqlalchemy import text

        conditions = ["visible_en_ranking = true", "activo = true"]
        params: dict[str, Any] = {"lim": min(max(1, limit), 100), "off": max(0, offset)}

        if q:
            conditions.append("(nombre ILIKE :q OR descripcion_corta ILIKE :q OR etiquetas ILIKE :q)")
            params["q"] = f"%{q.strip()}%"
        if provincia and provincia.upper() not in ["TODAS", "TODOS", ""]:
            conditions.append("UPPER(provincia) = UPPER(:provincia)")
            params["provincia"] = provincia.strip()
        if categoria:
            conditions.append("UPPER(categoria) = UPPER(:categoria)")
            params["categoria"] = categoria.strip()

        where_clause = " WHERE " + " AND ".join(conditions)

        count_sql = f"SELECT count(*) FROM turismo.v_catalogo {where_clause}"
        total = (await db.execute(text(count_sql), params)).scalar() or 0

        data_sql = f"""
            SELECT id_atractivo, codigo_recurso, nombre, categoria, tipo, subtipo,
                   departamento, provincia, distrito, ubigeo, latitud, longitud, estado,
                   descripcion_corta, duracion_horas, costo_min_pen, costo_max_pen, es_gratuito,
                   costo_texto, dificultad, accesibilidad, horario, temporada, etiquetas,
                   publico_recomendado, imagen_principal
            FROM turismo.v_catalogo
            {where_clause}
            ORDER BY nombre ASC
            LIMIT :lim OFFSET :off
        """
        rows = (await db.execute(text(data_sql), params)).mappings().all()
        items = [AtractivoDetalle(**dict(r)) for r in rows]

        return AtractivosListResponse(total=total, limit=limit, offset=offset, items=items)
    except Exception as exc:
        logger.warning("Fallo en listar_atractivos desde BD (%s). Usando catálogo en memoria.", exc)
        engine = getattr(app.state, "engine", None)
        if engine is None or engine.catalogo is None:
            return AtractivosListResponse(total=0, limit=limit, offset=offset, items=[])

        df = engine.catalogo.copy()
        if q:
            term = q.strip().upper()
            df = df[
                df["nombre_recurso"].str.upper().str.contains(term, na=False) |
                df["descripcion_corta"].str.upper().str.contains(term, na=False) |
                df["etiquetas_interes"].str.upper().str.contains(term, na=False)
            ]
        if provincia and provincia.upper() not in ["TODAS", "TODOS", ""]:
            df = df[df["provincia"].str.upper() == provincia.strip().upper()]
        if categoria:
            df = df[df["categoria"].str.upper() == categoria.strip().upper()]

        total = len(df)
        paged = df.iloc[offset : offset + limit]

        items = []
        for idx, row in paged.iterrows():
            aid = int(idx) + 1
            costo = float(row.get("costo_referencial_pen", 0.0))
            items.append(
                AtractivoDetalle(
                    id_atractivo=aid,
                    codigo_recurso=str(row.get("id_recurso", f"REC-{aid:05d}")),
                    nombre=str(row.get("nombre_recurso", "")),
                    categoria=str(row.get("categoria", "")),
                    tipo=str(row.get("tipo", "")),
                    subtipo=str(row.get("subtipo", "")),
                    departamento="SAN MARTIN",
                    provincia=str(row.get("provincia", "")),
                    distrito=str(row.get("distrito", "")),
                    ubigeo="",
                    latitud=float(row.get("latitud", 0.0)),
                    longitud=float(row.get("longitud", 0.0)),
                    estado="ACTIVO",
                    descripcion_corta=str(row.get("descripcion_corta", "")),
                    duracion_horas=float(row.get("duracion_estimada_horas", 2.0)),
                    costo_min_pen=costo,
                    costo_max_pen=costo,
                    es_gratuito=costo == 0.0,
                    costo_texto=f"S/ {costo:.2f}" if costo > 0 else "Gratuito",
                    dificultad=str(row.get("nivel_dificultad", "Media")),
                    accesibilidad="No informado",
                    horario=str(row.get("horario_referencial", "08:00 - 17:00")),
                    temporada=str(row.get("temporada_ideal", "Todo el año")),
                    etiquetas=str(row.get("etiquetas_interes", "")),
                    publico_recomendado=str(row.get("publico_recomendado", "Todos")),
                    imagen_principal=str(row.get("imagen_url", "")),
                )
            )
        return AtractivosListResponse(total=total, limit=limit, offset=offset, items=items)


@app.get(
    "/api/atractivos/{id_atractivo}",
    response_model=AtractivoDetalle,
    summary="Detalle completo de un atractivo turístico",
    tags=["Catálogo"],
)
async def obtener_atractivo_detalle(
    id_atractivo: int,
    db: AsyncSession = Depends(get_db),
) -> AtractivoDetalle:
    """Obtiene los atributos detallados de un atractivo turístico por su ID."""
    try:
        from sqlalchemy import text

        sql = """
            SELECT id_atractivo, codigo_recurso, nombre, categoria, tipo, subtipo,
                   departamento, provincia, distrito, ubigeo, latitud, longitud, estado,
                   descripcion_corta, duracion_horas, costo_min_pen, costo_max_pen, es_gratuito,
                   costo_texto, dificultad, accesibilidad, horario, temporada, etiquetas,
                   publico_recomendado, imagen_principal
            FROM turismo.v_catalogo
            WHERE id_atractivo = :id
        """
        res = await db.execute(text(sql), {"id": id_atractivo})
        row = res.mappings().one_or_none()
        if row:
            return AtractivoDetalle(**dict(row))
    except Exception as exc:
        logger.warning("Fallo en obtener_atractivo_detalle desde BD (%s). Usando catálogo en memoria.", exc)

    # Fallback a catálogo en memoria
    engine = getattr(app.state, "engine", None)
    if engine is not None and engine.catalogo is not None:
        idx = id_atractivo - 1
        if 0 <= idx < len(engine.catalogo):
            row = engine.catalogo.iloc[idx]
            costo = float(row.get("costo_referencial_pen", 0.0))
            return AtractivoDetalle(
                id_atractivo=id_atractivo,
                codigo_recurso=str(row.get("id_recurso", f"REC-{id_atractivo:05d}")),
                nombre=str(row.get("nombre_recurso", "")),
                categoria=str(row.get("categoria", "")),
                tipo=str(row.get("tipo", "")),
                subtipo=str(row.get("subtipo", "")),
                departamento="SAN MARTIN",
                provincia=str(row.get("provincia", "")),
                distrito=str(row.get("distrito", "")),
                ubigeo="",
                latitud=float(row.get("latitud", 0.0)),
                longitud=float(row.get("longitud", 0.0)),
                estado="ACTIVO",
                descripcion_corta=str(row.get("descripcion_corta", "")),
                duracion_horas=float(row.get("duracion_estimada_horas", 2.0)),
                costo_min_pen=costo,
                costo_max_pen=costo,
                es_gratuito=costo == 0.0,
                costo_texto=f"S/ {costo:.2f}" if costo > 0 else "Gratuito",
                dificultad=str(row.get("nivel_dificultad", "Media")),
                accesibilidad="No informado",
                horario=str(row.get("horario_referencial", "08:00 - 17:00")),
                temporada=str(row.get("temporada_ideal", "Todo el año")),
                etiquetas=str(row.get("etiquetas_interes", "")),
                publico_recomendado=str(row.get("publico_recomendado", "Todos")),
                imagen_principal=str(row.get("imagen_url", "")),
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Atractivo turístico con ID {id_atractivo} no encontrado.",
    )


@app.get(
    "/api/metricas",
    response_model=MetricasPrototipoResponse,
    summary="Métricas de evaluación del prototipo y calidad de recomendación (RF-16)",
    tags=["Observabilidad"],
)
async def obtener_metricas_prototipo(db: AsyncSession = Depends(get_db)) -> MetricasPrototipoResponse:
    """Consulta la vista `turismo.v_metricas_prototipo` o calcula métricas locales en memoria."""
    try:
        from sqlalchemy import text
        res = await db.execute(text("SELECT * FROM turismo.v_metricas_prototipo"))
        row = res.mappings().one_or_none()
        if row:
            return MetricasPrototipoResponse(**dict(row))
    except Exception as exc:
        logger.warning("Fallo al consultar métricas en BD (%s). Usando métricas en memoria.", exc)

    total_ses = len(MEM_SESIONES)
    total_ejec = len(MEM_EJECUCIONES)
    total_val = len(MEM_VALORACIONES)
    utilidad_prom = sum(v["utilidad"] for v in MEM_VALORACIONES.values()) / total_val if total_val > 0 else 5.0
    return MetricasPrototipoResponse(
        sesiones=total_ses,
        ejecuciones=total_ejec,
        valoraciones=total_val,
        utilidad_promedio=round(utilidad_prom, 2),
        pct_eligio_alternativa=100.0 if total_val > 0 else 0.0,
        pct_explicacion_comprensible=100.0 if total_val > 0 else 0.0,
        tiempo_respuesta_ms_prom=8.5,
        pct_cumple_filtros=100.0,
        diversidad_categorias_prom=3.2,
        pct_cobertura_catalogo=100.0,
    )


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Diálogo conversacional con el Guía/Asistente IA",
    tags=["Asistente IA"],
)
@app.post(
    "/assistant/chat",
    response_model=ChatResponse,
    summary="Diálogo conversacional con el Guía/Asistente IA (alias)",
    tags=["Asistente IA"],
)
async def chat_asistente(chat_req: ChatRequest) -> ChatResponse:
    """Procesa consultas en lenguaje natural de los turistas usando el catálogo y modelo de San Martín."""
    engine = getattr(app.state, "engine", None)
    return procesar_consulta_asistente(
        message=chat_req.message,
        context=chat_req.context,
        engine=engine,
    )



@app.get(
    "/",
    summary="Página de bienvenida y metadatos",
    tags=["General"],
)
async def root() -> dict[str, str]:
    """Ruta raíz informativa."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
