from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PreferenciaRequest(BaseModel):
    """
    Payload de entrada para solicitar recomendaciones personalizadas.
    Acepta tanto la nomenclatura en lenguaje natural como la de base de datos.
    """
    intereses: str = Field(
        default="",
        description="Palabras clave o intereses temáticos (ej. 'cataratas, selva, aventura')",
        examples=["cataratas naturaleza aventura"],
    )
    tiempo_en_horas: float = Field(
        default=8.0,
        gt=0.0,
        le=24.0,
        description="Tiempo disponible del turista en horas (0.1 a 24.0)",
        examples=[5.0],
    )
    presupuesto: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Presupuesto máximo referencial en soles (PEN). Null si no tiene límite.",
        examples=[50.0],
    )
    provincia: Optional[str] = Field(
        default="Todas",
        description="Provincia de interés ('SAN MARTIN', 'LAMAS', 'MOYOBAMBA', etc.) o 'Todas'",
        examples=["SAN MARTIN"],
    )
    compania: Optional[str] = Field(
        default="Todos",
        description="Tipo de compañía de viaje: 'Solo', 'Pareja', 'Amigos', 'Familia', 'Familia con niños', 'Adulto mayor', 'Todos'",
        examples=["Amigos"],
    )
    nivel_dificultad: Optional[str] = Field(
        default="Media",
        description="Nivel de dificultad física aceptado: 'Baja', 'Media', 'Alta'",
        examples=["Baja"],
    )
    requiere_accesibilidad: bool = Field(
        default=False,
        description="Indica si se requiere accesibilidad para personas con movilidad reducida",
    )
    top_n: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número de recomendaciones a devolver (por defecto 5)",
        examples=[5],
    )
    tipo_dispositivo: Optional[str] = Field(
        default="escritorio",
        description="Dispositivo desde el que se consulta: 'movil', 'tablet', 'escritorio'",
    )
    consentimiento_datos: bool = Field(
        default=False,
        description="Consentimiento para uso analítico anónimo",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "intereses": "cataratas naturaleza cascadas",
                    "tiempo_en_horas": 4.5,
                    "presupuesto": 35.0,
                    "provincia": "SAN MARTIN",
                    "compania": "Amigos",
                    "nivel_dificultad": "Baja",
                    "top_n": 5
                }
            ]
        }
    )

    @field_validator("provincia", mode="before")
    @classmethod
    def normalize_provincia(cls, v: Any) -> str:
        if v is None:
            return "Todas"
        val = str(v).strip()
        return val if val else "Todas"

    @field_validator("compania", mode="before")
    @classmethod
    def normalize_compania(cls, v: Any) -> str:
        if v is None:
            return "Todos"
        val = str(v).strip()
        return val if val else "Todos"

    @field_validator("nivel_dificultad", mode="before")
    @classmethod
    def normalize_dificultad(cls, v: Any) -> str:
        if v is None:
            return "Media"
        val = str(v).strip().capitalize()
        if val in ["Baja", "Media", "Alta"]:
            return val
        return "Media"


class RecomendacionItem(BaseModel):
    """
    Detalle de un atractivo recomendado dentro del Top-N.
    """
    id_recomendacion: int = Field(..., description="Identificador persistido de la recomendación")
    posicion: int = Field(..., ge=1, description="Posición en el ranking (1 al N)")
    id_atractivo: int = Field(..., description="ID del atractivo en la base de datos")
    codigo_recurso: str = Field(..., description="Código oficial MINCETUR (ej. REC-00001)")
    nombre_recurso: str = Field(..., description="Nombre oficial del atractivo turístico")
    categoria: str = Field(..., description="Categoría MINCETUR")
    tipo: str = Field(..., description="Tipo de recurso turístico")
    subtipo: str = Field(..., description="Subtipo de recurso turístico")
    provincia: str = Field(..., description="Provincia de ubicación")
    distrito: str = Field(..., description="Distrito de ubicación")
    latitud: float = Field(..., description="Latitud geográfica")
    longitud: float = Field(..., description="Longitud geográfica")
    duracion_estimada_horas: float = Field(..., description="Duración estimada de visita en horas")
    costo_referencial_pen: float = Field(..., description="Costo referencial de acceso en soles")
    nivel_dificultad: str = Field(..., description="Dificultad física del recorrido")
    publico_recomendado: str = Field(..., description="Público o compañía idónea")
    afinidad_pct: float = Field(..., description="Porcentaje de afinidad semántica (0 - 100%)")
    puntaje_afinidad: float = Field(..., description="Puntaje de afinidad normalizado (0.0000 - 1.0000)")
    cluster_id: int = Field(..., description="ID del cluster asignado por KMeans")
    cluster_label: str = Field(..., description="Etiqueta descriptiva del perfil de cluster")
    explicacion: str = Field(..., description="Justificación inteligible generada por el motor (XAI)")
    imagen_url: Optional[str] = Field(None, description="URL de la fotografía representativa")
    cumple_filtros: bool = Field(True, description="Indica si cumplió todos los filtros estrictos")

    model_config = ConfigDict(from_attributes=True)


class RecomendacionResponse(BaseModel):
    """
    Respuesta integral de recomendación generada y persistida.
    """
    id_sesion: UUID = Field(..., description="Identificador único de la sesión del usuario")
    id_ejecucion: int = Field(..., description="Identificador único de la ejecución de recomendación")
    id_modelo: int = Field(..., description="ID de la versión de modelo aplicada")
    tiempo_respuesta_ms: int = Field(..., description="Tiempo de respuesta total en milisegundos")
    total_candidatos: int = Field(..., description="Total de atractivos que cumplieron los filtros obligatorios")
    fallback_provincia: bool = Field(False, description="Indica si se aplicó relajación de provincia por ausencia de candidatos")
    recomendaciones: list[RecomendacionItem] = Field(..., description="Listado Top-N de atractivos recomendados")

    model_config = ConfigDict(from_attributes=True)


class ValoracionRequest(BaseModel):
    """
    Payload para registrar feedback y valoración del turista sobre una recomendación.
    """
    id_ejecucion: int = Field(
        ...,
        description="ID de la ejecución de recomendación que se evalúa",
        examples=[1],
    )
    utilidad: int = Field(
        ...,
        ge=1,
        le=5,
        description="Escala de utilidad de 1 a 5 estrellas",
        examples=[5],
    )
    comentario: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Comentario opcional del turista (máx. 500 caracteres)",
        examples=["Excelentes recomendaciones, Ahuashiyacu fue espectacular."],
    )
    id_recomendacion_elegida: Optional[int] = Field(
        default=None,
        description="ID de la recomendación (id_recomendacion) que el usuario decidió visitar",
        examples=[None],
    )
    eligio_alternativa: Optional[bool] = Field(
        default=None,
        description="Indica si eligió alguna de las opciones presentadas. Se infiere como True si envía id_recomendacion_elegida.",
        examples=[True],
    )
    explicacion_comprensible: bool = Field(
        default=True,
        description="Indica si las justificaciones proporcionadas fueron claras y comprensibles",
        examples=[True],
    )


class ValoracionResponse(BaseModel):
    """
    Respuesta tras la persistencia exitosa de la valoración.
    """
    id_valoracion: int = Field(..., description="ID de la valoración registrada")
    id_ejecucion: int = Field(..., description="ID de la ejecución evaluada")
    utilidad: int = Field(..., description="Calificación en estrellas (1-5)")
    eligio_alternativa: bool = Field(..., description="Indica si eligió alternativa")
    id_recomendacion_elegida: Optional[int] = Field(None, description="Recomendación elegida")
    explicacion_comprensible: bool = Field(..., description="Comprensibilidad de la explicación")
    comentario: Optional[str] = Field(None, description="Comentario almacenado")
    fecha: datetime = Field(..., description="Fecha y hora de registro")
    mensaje: str = Field("Valoración registrada exitosamente", description="Mensaje de confirmación")

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """
    Respuesta del endpoint /health para observabilidad y monitoreo continuo.
    """
    status: str = Field(..., description="Estado general del servicio: 'healthy' o 'unhealthy'", examples=["healthy"])
    timestamp: datetime = Field(..., description="Marca de tiempo actual del servidor")
    version: str = Field(..., description="Versión de la API", examples=["1.0.0"])
    database: dict[str, Any] = Field(..., description="Estado de conectividad y métricas de PostgreSQL")
    model: dict[str, Any] = Field(..., description="Estado del modelo en memoria RAM y dimensiones vectoriales")


class CatalogoOpcion(BaseModel):
    id: Any
    nombre: str
    descripcion: Optional[str] = None


class FiltrosResponse(BaseModel):
    """Opciones y catálogos disponibles para poblar formularios y selectores en frontend."""
    provincias: list[dict[str, str]] = Field(..., description="Provincias disponibles en San Martín")
    companias: list[dict[str, Any]] = Field(..., description="Compañías de viaje disponibles")
    dificultades: list[dict[str, Any]] = Field(..., description="Niveles de dificultad física")


class AtractivoDetalle(BaseModel):
    """Detalle completo de un atractivo turístico."""
    id_atractivo: int
    codigo_recurso: str
    nombre: str
    categoria: Optional[str] = None
    tipo: Optional[str] = None
    subtipo: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    latitud: float
    longitud: float
    estado: Optional[str] = None
    descripcion_corta: Optional[str] = None
    duracion_horas: Optional[float] = None
    costo_min_pen: Optional[float] = None
    costo_max_pen: Optional[float] = None
    es_gratuito: Optional[bool] = None
    costo_texto: Optional[str] = None
    dificultad: Optional[str] = None
    accesibilidad: Optional[str] = None
    horario: Optional[str] = None
    temporada: Optional[str] = None
    etiquetas: Optional[str] = None
    publico_recomendado: Optional[str] = None
    imagen_principal: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AtractivosListResponse(BaseModel):
    """Listado paginado de atractivos turísticos."""
    total: int
    limit: int
    offset: int
    items: list[AtractivoDetalle]


class MetricasPrototipoResponse(BaseModel):
    """Métricas operativas del prototipo y calidad de recomendación (RF-16)."""
    sesiones: int
    ejecuciones: int
    valoraciones: int
    utilidad_promedio: Optional[float] = None
    pct_eligio_alternativa: Optional[float] = None
    pct_explicacion_comprensible: Optional[float] = None
    tiempo_respuesta_ms_prom: Optional[float] = None
    pct_cumple_filtros: Optional[float] = None
    diversidad_categorias_prom: Optional[float] = None
    pct_cobertura_catalogo: Optional[float] = None

