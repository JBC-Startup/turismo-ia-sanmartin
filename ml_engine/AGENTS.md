# Contexto del Proyecto: TurismoIA San Martín (ML Engine)

## 1. Visión y Propósito
Sistema inteligente de recomendación turística para la región San Martín, Perú. Procesa el inventario oficial de 308 recursos turísticos del GORE San Martín enriquecido con variables operativas (duración, costo, dificultad, accesibilidad, etiquetas, ruta desde Tarapoto) para devolver un Top-5 personalizado según las restricciones y gustos del viajero.

## 2. Restricciones Arquitectónicas de IA
- NO entrenar redes neuronales ni modelos de Deep Learning (el dataset es de ~308 registros, causaría overfitting).
- NO delegar la lógica de selección a un prompt de LLM. El núcleo matemático debe ser Machine Learning clásico reproducible (Scikit-Learn).
- Enfoque obligatorio: Filtrado Basado en Contenido (Content-Based Filtering) mediante Similitud del Coseno + Clustering no supervisado con K-Means para perfilado de macro-experiencias.

## 3. Esquema exacto del Dataset Crudo (`data/raw/turismo_san_martin.xlsx`)
Columnas disponibles:
- Oficiales/Geográficas: `ID_RECURSO`, `NOMBRE_RECURSO`, `DEPARTAMENTO`, `PROVINCIA`, `DISTRITO`, `UBIGEO`, `CODIGO_CATEGORIA`, `CATEGORIA`, `CODIGO_TIPO`, `TIPO`, `CODIGO_SUBTIPO`, `SUBTIPO`, `LATITUD`, `LONGITUD`, `CODIGO_ESTADO`, `ESTADO`, `FECHA_CORTE`.
- Enriquecidas (Operativas y Semánticas): `duracion_estimada_horas`, `costo_referencial_pen`, `nivel_dificultad`, `accesibilidad_reducida`, `etiquetas_interes`, `publico_recomendado`, `descripcion_corta`, `horario_referencial`, `temporada_ideal`, `imagen_url`, `distancia_km_tarapoto`, `tiempo_viaje_horas_tarapoto`, `tiempo_total_tour_horas`, `ruta_acceso_desde_tarapoto`, `referencia_ubicacion`, `url_fuente`, `fecha_verificacion`.

## 4. Entorno de Ejecución
- SO: Linux (PEP 668 activo). Toda ejecución de Python o instalación de paquetes DEBE realizarse invocando el entorno virtual local (`./venv/bin/python` y `./venv/bin/pip`).
