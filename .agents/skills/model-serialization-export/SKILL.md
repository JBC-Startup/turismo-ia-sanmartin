---
name: model-serialization-export
description: Empaquetado de artefactos entrenados (.pkl) e interfaz limpia de inferencia lista para producción/API (Fase 6).
---

# Serialización de Modelos y Exportación para Inferencia

## Objetivo del Skill
Serializar todos los objetos matemáticos entrenados y el catálogo procesado en un único artefacto portable (`models/modelo_recomendador_sanmartin.pkl`) y exponer una interfaz limpia de inferencia.

## Reglas de Empaquetado e Inferencia
1. **Estructura del Artefacto Serializado**:
   - El archivo `.pkl` debe contener un diccionario estructurado con:
     - Vectorizador de texto ajustado (`tfidf`).
     - Codificador categórico ajustado (`ohe`).
     - Escalador numérico ajustado (`scaler`).
     - Modelo `kmeans` entrenado.
     - Matriz precalculada `X_global`.
     - DataFrame del catálogo limpio con metadatos clave (`id_recurso`, `nombre_recurso`, `provincia`, `distrito`, `categoria`, `duracion_estimada_horas`, `costo_referencial_pen`, `nivel_dificultad`, `cluster_id`, `descripcion_corta`, `imagen_url`).
2. **Desacoplamiento Entrenamiento vs. Inferencia**:
   - El módulo de inferencia debe cargar el `.pkl` en memoria una sola vez y responder consultas en milisegundos sin re-entrenar nada.
3. **Explicabilidad del Resultado (XAI)**:
   - Cada recomendación del Top-5 debe devolver: ranking (1 al 5), datos del atractivo, porcentaje de afinidad (`0% a 100%`), `cluster_id` y una justificación legible generada a partir de la coincidencia de tiempo, costo, dificultad e intereses.
