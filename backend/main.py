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
    registrar_feedback,
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

    # 2. Inicialización de caché de catálogos desde PostgreSQL
    try:
        catalog_cache = CatalogCache()
        async with AsyncSessionLocal() as session:
            await catalog_cache.load(session, cluster_metadata=engine.cluster_metadata)
        app.state.catalog_cache = catalog_cache
    except Exception as exc:
        logger.error("Error al cargar la caché de catálogos desde la BD: %s", exc)
        app.state.catalog_cache = CatalogCache()

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

    is_healthy = db_status.get("connected", False) and model_status.get("loaded", False)
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

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
    from sqlalchemy import text

    res_prov = await db.execute(text("SELECT id_provincia, nombre FROM turismo.provincia ORDER BY nombre"))
    provincias = [{"id_provincia": r[0], "nombre": r[1]} for r in res_prov.fetchall()]

    res_comp = await db.execute(text("SELECT id_compania, nombre, descripcion FROM turismo.compania_viaje ORDER BY id_compania"))
    companias = [{"id_compania": r[0], "nombre": r[1], "descripcion": r[2]} for r in res_comp.fetchall()]

    res_dif = await db.execute(text("SELECT id_dificultad, nombre, nivel_esfuerzo FROM turismo.nivel_dificultad ORDER BY id_dificultad"))
    dificultades = [{"id_dificultad": r[0], "nombre": r[1], "nivel_esfuerzo": r[2]} for r in res_dif.fetchall()]

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
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atractivo turístico con ID {id_atractivo} no encontrado.",
        )
    return AtractivoDetalle(**dict(row))


@app.get(
    "/api/metricas",
    response_model=MetricasPrototipoResponse,
    summary="Métricas de evaluación del prototipo y calidad de recomendación (RF-16)",
    tags=["Observabilidad"],
)
async def obtener_metricas_prototipo(db: AsyncSession = Depends(get_db)) -> MetricasPrototipoResponse:
    """Consulta la vista `turismo.v_metricas_prototipo` con los indicadores clave del sistema."""
    from sqlalchemy import text

    res = await db.execute(text("SELECT * FROM turismo.v_metricas_prototipo"))
    row = res.mappings().one_or_none()
    if not row:
        return MetricasPrototipoResponse(sesiones=0, ejecuciones=0, valoraciones=0)
    return MetricasPrototipoResponse(**dict(row))



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
