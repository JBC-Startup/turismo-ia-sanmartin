---
name: ml-clustering-and-ranking
description: Entrenamiento de K-Means, cálculo de Similitud del Coseno con filtros duros y validación con perfiles sintéticos (Fases 4 y 5).
---

# Clustering No Supervisado y Ranking de Recomendación

## Objetivo del Skill
Agrupar la oferta turística en clusters interpretables y construir el motor de recomendación que genera el Top-5 personalizado para un turista, validándolo con métricas de control offline.

## Reglas del Motor de Recomendación
1. **Clustering No Supervisado (K-Means)**:
   - Entrenar K-Means sobre la matriz de características ($k$ entre 3 y 5 grupos, con semilla fija `random_state=42` para reproducibilidad).
   - Asignar el `cluster_id` a cada recurso turístico y generar un resumen interpretable de qué tipo de atractivos cayeron en cada cluster.
2. **Regla de Filtrado Duro (Hard Filters)**:
   - Antes o inmediatamente después de puntuar, el motor DEBE filtrar estrictamente los recursos que violen las restricciones operativas del usuario:
     - `duracion_estimada_horas` (o `tiempo_total_tour_horas`) <= tiempo disponible del turista.
     - `costo_referencial_pen` <= presupuesto máximo del turista.
     - Si el turista especifica una provincia concreta (distinta de "Todas"/"Cualquiera"), filtrar por dicha provincia.
   - Incluir un mecanismo de relajación controlada (fallback) solo si el filtro duro deja 0 resultados, advirtiendo al usuario.
3. **Ranking por Similitud del Coseno**:
   - Proyectar las preferencias del usuario al espacio vectorial usando los transformadores entrenados.
   - Calcular la similitud del coseno contra los recursos candidatos y ordenar de mayor a menor score para extraer el Top-5.
4. **Validación Técnica Offline (Fase 5)**:
   - Probar el motor con al menos 2 perfiles sintéticos contrastantes (ej. "Mochilero de aventura con poco tiempo/presupuesto en Tarapoto" vs "Viaje familiar cultural de día completo en Lamas/Moyobamba").
   - Verificar cumplimiento del 100% en restricciones de tiempo/presupuesto y diversidad de categorías en el Top-5.
