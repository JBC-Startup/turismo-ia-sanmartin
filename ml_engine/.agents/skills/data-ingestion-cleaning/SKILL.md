---
name: data-ingestion-cleaning
description: Reglas y contexto para la ingesta, auditoría, imputación y limpieza del dataset turístico de San Martín (Fase 2).
---

# Ingesta y Limpieza de Datos

## Objetivo del Skill
Transformar el archivo crudo `data/raw/turismo_san_martin.xlsx` en un dataset validado, consistente y libre de nulos matemáticos en `data/processed/dataset_limpio.csv`.

## Reglas de Negocio e Imputación
1. **Estandarización de cabeceras**: Todos los nombres de columnas deben normalizarse a minúsculas, sin espacios laterales ni caracteres especiales.
2. **Filtro de calidad administrativa**: Descartar cualquier registro cuyo `estado` sea "OBSERVADO" (insensible a mayúsculas/minúsculas).
3. **Imputación de campos semánticos** (`descripcion_corta`, `etiquetas_interes`, `categoria`, `tipo`, `subtipo`, `ruta_acceso_desde_tarapoto`, `referencia_ubicacion`):
   - Ninguno puede quedar como `NaN`. Reemplazar vacíos por cadenas vacías `""` y asegurar tipo string.
4. **Imputación de variables categóricas** (`provincia`, `nivel_dificultad`, `publico_recomendado`, `accesibilidad_reducida`):
   - Normalizar formato de texto (ej. `provincia` en mayúsculas).
   - Imputar faltantes con valores por defecto lógicos ("Media" para dificultad, "Todos" para público, "No" para accesibilidad).
5. **Imputación de variables numéricas** (`duracion_estimada_horas`, `costo_referencial_pen`, `distancia_km_tarapoto`, `tiempo_viaje_horas_tarapoto`, `tiempo_total_tour_horas`):
   - Forzar conversión numérica segura (`float`).
   - Imputar tiempos y distancias con la mediana estadística de su columna (o valor base razonable si no hay mediana) y costos faltantes con `0.0` (asumiendo acceso gratuito).
6. **Trazabilidad**: El script debe imprimir métricas claras en consola (registros leídos, registros descartados por estado, nulos corregidos y dimensiones finales).
