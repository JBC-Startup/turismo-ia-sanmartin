# =====================================================================
# Dockerfile para TurismoIA San Martín - Backend API & Inferencia ML
# =====================================================================
FROM python:3.12-slim

# Metadatos del contenedor
LABEL maintainer="TurismoIA San Martín Team"
LABEL description="API REST de Recomendación Turística Inteligente con FastAPI y PostgreSQL"

# Variables de entorno de Python y rutas de módulos
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/ml_engine:/app/backend"

WORKDIR /app

# Instalar dependencias del sistema mínimas requeridas (curl para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copiar artefactos y código del motor de machine learning
COPY ml_engine/src/ /app/ml_engine/src/
COPY ml_engine/models/ /app/ml_engine/models/

# Copiar código fuente del backend
COPY backend/ /app/backend/

# Directorio de trabajo en backend para resolución de módulos de uvicorn
WORKDIR /app/backend

# Exponer el puerto HTTP de la API REST
EXPOSE 8000

# Healthcheck de contenedor Docker
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio con servidor Uvicorn en producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
