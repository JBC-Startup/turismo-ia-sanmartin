---
name: feature-engineering-pipeline
description: Construcción del espacio vectorial multidimensional (TF-IDF, One-Hot Encoding y MinMaxScaler) para los recursos turísticos (Fase 3).
---

# Pipeline de Ingeniería de Características

## Objetivo del Skill
Tomar `data/processed/dataset_limpio.csv` y construir el pipeline de transformación que represente cada recurso turístico como un vector numérico en una matriz dispersa o densa unificada ($X_{global}$).

## Reglas de Ingeniería de Características
1. **Construcción del Corpus Semántico**:
   - Crear una columna unificada combinando `categoria`, `tipo`, `subtipo`, `etiquetas_interes` y `descripcion_corta`.
2. **Representación Textual (TF-IDF)**:
   - Aplicar vectorización TF-IDF eliminando stop words en español (preposiciones, artículos, conectores).
   - Limitar el vocabulario a las palabras más representativas para evitar ruido dimensional en un catálogo de ~300 filas.
3. **Codificación Categórica (One-Hot Encoding)**:
   - Codificar variables categóricas clave para el perfilado (`nivel_dificultad`, `provincia`, `publico_recomendado`, `accesibilidad_reducida`).
   - Configurar el codificador para ignorar categorías desconocidas durante la inferencia futura (`handle_unknown='ignore'`).
4. **Escalado Numérico (MinMaxScaler)**:
   - Normalizar en rango `[0, 1]` las variables continuas (`duracion_estimada_horas`, `costo_referencial_pen`, y opcionalmente `tiempo_total_tour_horas`) para que la magnitud en soles o kilómetros no domine sobre la similitud textual.
5. **Ensamblado Matricial**:
   - Concatenar horizontalmente las matrices de texto, categorías y números en una sola matriz de características ($X_{global}$), garantizando que el mismo flujo pueda transformar el input de un turista al mismo espacio dimensional.
