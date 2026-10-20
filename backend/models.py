import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# =====================================================================
# 1. CATÁLOGOS REFERENCIALES
# =====================================================================

class CompaniaViaje(Base):
    __tablename__ = "compania_viaje"
    __table_args__ = {"schema": "turismo"}

    id_compania: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)


class NivelDificultad(Base):
    __tablename__ = "nivel_dificultad"
    __table_args__ = {"schema": "turismo"}

    id_dificultad: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nivel_esfuerzo: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)


class Provincia(Base):
    __tablename__ = "provincia"
    __table_args__ = {"schema": "turismo"}

    id_provincia: Mapped[str] = mapped_column(String(4), primary_key=True)
    id_departamento: Mapped[str] = mapped_column(String(2), nullable=False)
    codigo: Mapped[str] = mapped_column(String(2), nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class Distrito(Base):
    __tablename__ = "distrito"
    __table_args__ = {"schema": "turismo"}

    ubigeo: Mapped[str] = mapped_column(String(6), primary_key=True)
    id_provincia: Mapped[str] = mapped_column(String(4), ForeignKey("turismo.provincia.id_provincia"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(2), nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class Atractivo(Base):
    __tablename__ = "atractivo"
    __table_args__ = {"schema": "turismo"}

    id_atractivo: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    codigo_recurso: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    id_subtipo: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ubigeo: Mapped[str] = mapped_column(String(6), ForeignKey("turismo.distrito.ubigeo"), nullable=False)
    latitud: Mapped[Decimal] = mapped_column(Numeric(12, 9), nullable=False)
    longitud: Mapped[Decimal] = mapped_column(Numeric(12, 9), nullable=False)
    id_estado: Mapped[str] = mapped_column(String(2), nullable=False)
    fecha_corte: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModeloVersion(Base):
    __tablename__ = "modelo_version"
    __table_args__ = {"schema": "turismo"}

    id_modelo: Mapped[int] = mapped_column(SmallInteger, Identity(), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    algoritmo: Mapped[str] = mapped_column(String(20), nullable=False)
    peso_intereses: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    peso_tiempo: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    peso_ubicacion: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    peso_presupuesto: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    peso_accesibilidad: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    parametros: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    version_dataset: Mapped[str] = mapped_column(String(40), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClusterPerfil(Base):
    __tablename__ = "cluster_perfil"
    __table_args__ = {"schema": "turismo"}

    id_cluster: Mapped[int] = mapped_column(SmallInteger, Identity(), primary_key=True)
    id_modelo: Mapped[int] = mapped_column(SmallInteger, ForeignKey("turismo.modelo_version.id_modelo", ondelete="CASCADE"), nullable=False)
    numero: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    centroide: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)


# =====================================================================
# 2. TABLAS OPERATIVAS DEL MOTOR DE RECOMENDACIÓN
# =====================================================================

class SesionPreferencia(Base):
    __tablename__ = "sesion_preferencia"
    __table_args__ = {"schema": "turismo"}

    id_sesion: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tiempo_disponible_horas: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    presupuesto_max_pen: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    id_compania: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey("turismo.compania_viaje.id_compania"), nullable=True)
    id_dificultad_max: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey("turismo.nivel_dificultad.id_dificultad"), nullable=True)
    requiere_accesibilidad: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ubigeo_referencia: Mapped[Optional[str]] = mapped_column(String(6), ForeignKey("turismo.distrito.ubigeo"), nullable=True)
    radio_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)
    texto_libre: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    tipo_dispositivo: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    consentimiento_datos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    ejecuciones: Mapped[list["EjecucionRecomendacion"]] = relationship("EjecucionRecomendacion", back_populates="sesion", cascade="all, delete-orphan")
    provincias: Mapped[list["SesionProvincia"]] = relationship("SesionProvincia", back_populates="sesion", cascade="all, delete-orphan")


class SesionProvincia(Base):
    __tablename__ = "sesion_provincia"
    __table_args__ = {"schema": "turismo"}

    id_sesion: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("turismo.sesion_preferencia.id_sesion", ondelete="CASCADE"), primary_key=True)
    id_provincia: Mapped[str] = mapped_column(String(4), ForeignKey("turismo.provincia.id_provincia"), primary_key=True)

    sesion: Mapped["SesionPreferencia"] = relationship("SesionPreferencia", back_populates="provincias")


class EjecucionRecomendacion(Base):
    __tablename__ = "ejecucion_recomendacion"
    __table_args__ = {"schema": "turismo"}

    id_ejecucion: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    id_sesion: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("turismo.sesion_preferencia.id_sesion", ondelete="CASCADE"), nullable=False)
    id_modelo: Mapped[int] = mapped_column(SmallInteger, ForeignKey("turismo.modelo_version.id_modelo"), nullable=False)
    id_cluster: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey("turismo.cluster_perfil.id_cluster"), nullable=True)
    total_candidatos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tiempo_respuesta_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parametros_aplicados: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    sesion: Mapped["SesionPreferencia"] = relationship("SesionPreferencia", back_populates="ejecuciones")
    recomendaciones: Mapped[list["Recomendacion"]] = relationship("Recomendacion", back_populates="ejecucion", cascade="all, delete-orphan")
    valoracion: Mapped[Optional["Valoracion"]] = relationship("Valoracion", back_populates="ejecucion", uselist=False, cascade="all, delete-orphan")


class Recomendacion(Base):
    __tablename__ = "recomendacion"
    __table_args__ = {"schema": "turismo"}

    id_recomendacion: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    id_ejecucion: Mapped[int] = mapped_column(BigInteger, ForeignKey("turismo.ejecucion_recomendacion.id_ejecucion", ondelete="CASCADE"), nullable=False)
    id_atractivo: Mapped[int] = mapped_column(Integer, ForeignKey("turismo.atractivo.id_atractivo"), nullable=False)
    posicion: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    puntaje_afinidad: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    puntaje_intereses: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    puntaje_tiempo: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    puntaje_ubicacion: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    puntaje_presupuesto: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    puntaje_accesibilidad: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    cumple_filtros: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    explicacion: Mapped[str] = mapped_column(String(400), nullable=False)

    # Relaciones
    ejecucion: Mapped["EjecucionRecomendacion"] = relationship("EjecucionRecomendacion", back_populates="recomendaciones")
    atractivo: Mapped["Atractivo"] = relationship("Atractivo")


class Valoracion(Base):
    __tablename__ = "valoracion"
    __table_args__ = {"schema": "turismo"}

    id_valoracion: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    id_ejecucion: Mapped[int] = mapped_column(BigInteger, ForeignKey("turismo.ejecucion_recomendacion.id_ejecucion", ondelete="CASCADE"), unique=True, nullable=False)
    utilidad: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    eligio_alternativa: Mapped[bool] = mapped_column(Boolean, nullable=False)
    id_recomendacion_elegida: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    explicacion_comprensible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ejecucion: Mapped["EjecucionRecomendacion"] = relationship("EjecucionRecomendacion", back_populates="valoracion")
