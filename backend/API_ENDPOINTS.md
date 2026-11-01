# Contrato de APIs - TurismoIA San Martín Backend

Base URL local: `http://localhost:8000`  
Documentación interactiva Swagger: `http://localhost:8000/docs`

---

## Índice de Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de salud del backend, base de datos y modelo ML |
| `GET` | `/api/filtros` | Catálogos de provincias, compañías de viaje y dificultades |
| `GET` | `/api/atractivos` | Listado paginado y búsqueda de atractivos turísticos |
| `GET` | `/api/atractivos/{id_atractivo}` | Detalle completo de un atractivo por ID |
| `POST` | `/api/recomendar` | Generación de Top-5 recomendaciones con ML y filtros duros |
| `POST` | `/api/valorar` | Registro de valoración y feedback de una recomendación |
| `POST` | `/api/chat` | Asistente conversacional IA (Gemini + Catálogo San Martín) |
| `GET` | `/api/metricas` | Métricas operativas del prototipo y calidad de recomendación |

---

## 1. GET `/health`
Verifica conectividad con PostgreSQL y artefacto ML cargado en memoria RAM.

### Respuesta (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-10-31T23:50:00Z",
  "version": "1.0.0",
  "database": {
    "connected": true,
    "latency_ms": 3.2,
    "total_atractivos": 297,
    "schema": "turismo"
  },
  "model": {
    "loaded": true,
    "version": "1.0.0",
    "atractivos_en_catalogo": 297,
    "vector_dimension": 469,
    "clusters_activos": 4
  }
}
```

#### Ejemplo curl:
```bash
curl -X GET http://localhost:8000/health
```

---

## 2. GET `/api/filtros`
Devuelve las opciones disponibles para alimentar selectores y filtros en el cliente.

### Respuesta (200 OK):
```json
{
  "provincias": [
    { "id_provincia": "2201", "nombre": "Moyobamba" },
    { "id_provincia": "2202", "nombre": "Bellavista" },
    { "id_provincia": "2205", "nombre": "Lamas" },
    { "id_provincia": "2209", "nombre": "San Martín" }
  ],
  "companias": [
    { "id_compania": 1, "nombre": "Solo", "descripcion": "Viajero individual" },
    { "id_compania": 2, "nombre": "Pareja", "descripcion": "Viaje en pareja" },
    { "id_compania": 3, "nombre": "Amigos", "descripcion": "Grupo de amigos" },
    { "id_compania": 4, "nombre": "Familia", "descripcion": "Grupo familiar" }
  ],
  "dificultades": [
    { "id_dificultad": 1, "nombre": "Baja", "nivel_esfuerzo": 1 },
    { "id_dificultad": 2, "nombre": "Media", "nivel_esfuerzo": 2 },
    { "id_dificultad": 3, "nombre": "Alta", "nivel_esfuerzo": 3 }
  ]
}
```

#### Ejemplo curl:
```bash
curl -X GET http://localhost:8000/api/filtros
```

---

## 3. GET `/api/atractivos`
Consulta y filtra atractivos turísticos con paginación.

### Parámetros Query:
- `q` (opcional, string): Búsqueda por texto en nombre o descripción.
- `provincia` (opcional, string): Filtrar por provincia (`SAN MARTIN`, `LAMAS`, `MOYOBAMBA`, etc.).
- `categoria` (opcional, string): Filtrar por categoría MINCETUR.
- `limit` (opcional, int, default `20`): Cantidad por página (máx. 100).
- `offset` (opcional, int, default `0`): Desplazamiento de registros.

### Respuesta (200 OK):
```json
{
  "total": 297,
  "limit": 2,
  "offset": 0,
  "items": [
    {
      "id_atractivo": 10,
      "codigo_recurso": "REC-00010",
      "nombre": "CATARATAS DE AHUASHIYACU",
      "categoria": "SITIOS NATURALES",
      "tipo": "CAIDAS DE AGUA",
      "subtipo": "CATARATAS",
      "departamento": "SAN MARTIN",
      "provincia": "SAN MARTIN",
      "distrito": "LA BANDA DE SHILCAYO",
      "latitud": -6.4542,
      "longitud": -76.3051,
      "estado": "ACTIVO",
      "descripcion_corta": "Emblemática caída de agua de 40 metros rodeada de exuberante vegetación.",
      "duracion_horas": 1.5,
      "costo_min_pen": 10.0,
      "costo_max_pen": 10.0,
      "es_gratuito": false,
      "costo_texto": "S/ 10.00",
      "dificultad": "Baja",
      "accesibilidad": "Sendero habilitado",
      "horario": "08:00 - 17:00",
      "temporada": "Todo el año",
      "etiquetas": "naturaleza cascadas paisaje fotografia",
      "publico_recomendado": "Todos",
      "imagen_principal": "https://turismoia.pe/images/ahuashiyacu.jpg"
    }
  ]
}
```

#### Ejemplo curl:
```bash
curl -X GET "http://localhost:8000/api/atractivos?q=catarata&provincia=SAN%20MARTIN&limit=5"
```

---

## 4. GET `/api/atractivos/{id_atractivo}`
Obtiene el detalle completo de un recurso por su ID.

### Parámetro Path:
- `id_atractivo` (int, obligatorio): ID numérico del atractivo.

### Respuesta (200 OK):
```json
{
  "id_atractivo": 204,
  "codigo_recurso": "REC-00204",
  "nombre": "CASTILLO MEDIEVAL DE LAMAS",
  "categoria": "MANIFESTACIONES CULTURALES",
  "tipo": "ARQUITECTURA Y ESPACIOS URBANOS",
  "subtipo": "CASTILLOS",
  "provincia": "LAMAS",
  "distrito": "LAMAS",
  "latitud": -6.4228,
  "longitud": -76.5161,
  "duracion_horas": 1.0,
  "costo_min_pen": 15.0,
  "costo_max_pen": 15.0,
  "es_gratuito": false,
  "dificultad": "Baja"
}
```

#### Ejemplo curl:
```bash
curl -X GET http://localhost:8000/api/atractivos/204
```

---

## 5. POST `/api/recomendar`
Calcula el Top-N de atractivos recomendados usando el modelo de Machine Learning (similitud del coseno sobre 469 dimensiones y filtros duros).

### Request Body:
```json
{
  "intereses": "cataratas naturaleza aventura paisajes",
  "tiempo_en_horas": 4.5,
  "presupuesto": 35.0,
  "provincia": "San Martín",
  "compania": "Amigos",
  "nivel_dificultad": "Media",
  "requiere_accesibilidad": false,
  "top_n": 5
}
```

### Respuesta (200 OK):
```json
{
  "id_sesion": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "id_ejecucion": 1284920,
  "id_modelo": 1,
  "tiempo_respuesta_ms": 7,
  "total_candidatos": 24,
  "fallback_provincia": false,
  "recomendaciones": [
    {
      "id_recomendacion": 1,
      "posicion": 1,
      "id_atractivo": 10,
      "codigo_recurso": "REC-00010",
      "nombre_recurso": "CATARATAS DE AHUASHIYACU",
      "categoria": "SITIOS NATURALES",
      "tipo": "CAIDAS DE AGUA",
      "subtipo": "CATARATAS",
      "provincia": "SAN MARTIN",
      "distrito": "LA BANDA DE SHILCAYO",
      "duracion_estimada_horas": 1.5,
      "costo_referencial_pen": 10.0,
      "nivel_dificultad": "Baja",
      "publico_recomendado": "Todos",
      "afinidad_pct": 52.3,
      "puntaje_afinidad": 0.523,
      "cluster_id": 1,
      "cluster_label": "Patrimonio Cultural, Historia y Naturaleza",
      "explicacion": "Alineado a tus intereses en cataratas, naturaleza; tiempo de 1.5h y S/10.0; dificultad baja en San Martín.",
      "cumple_filtros": true
    }
  ]
}
```

#### Ejemplo curl:
```bash
curl -X POST http://localhost:8000/api/recomendar \
  -H "Content-Type: application/json" \
  -d '{
    "intereses": "cataratas naturaleza aventura",
    "tiempo_en_horas": 6.0,
    "presupuesto": 40.0,
    "provincia": "San Martín",
    "compania": "Amigos",
    "nivel_dificultad": "Media",
    "top_n": 3
  }'
```

---

## 6. POST `/api/valorar`
Registra la calificación de satisfacción del turista (1 a 5 estrellas) asociada a la ejecución de recomendación.

### Request Body:
```json
{
  "id_ejecucion": 1284920,
  "utilidad": 5,
  "comentario": "Excelente recomendación, Ahuashiyacu fue espectacular.",
  "id_recomendacion_elegida": 1,
  "eligio_alternativa": true,
  "explicacion_comprensible": true
}
```

### Respuesta (201 Created):
```json
{
  "id_valoracion": 15,
  "id_ejecucion": 1284920,
  "utilidad": 5,
  "eligio_alternativa": true,
  "id_recomendacion_elegida": 1,
  "explicacion_comprensible": true,
  "comentario": "Excelente recomendación, Ahuashiyacu fue espectacular.",
  "fecha": "2026-10-31T23:55:00Z",
  "mensaje": "Valoración registrada exitosamente"
}
```

#### Ejemplo curl:
```bash
curl -X POST http://localhost:8000/api/valorar \
  -H "Content-Type: application/json" \
  -d '{
    "id_ejecucion": 1284920,
    "utilidad": 5,
    "comentario": "Muy buen servicio",
    "id_recomendacion_elegida": 1,
    "eligio_alternativa": true,
    "explicacion_comprensible": true
  }'
```

---

## 7. POST `/api/chat` (alias `/assistant/chat`)
Diálogo con el Guía Inteligente. Utiliza **Google Gemini AI** (si `GEMINI_API_KEY` está configurada en `.env`) o el motor semántico de respaldo con los 297 atractivos oficiales.

### Request Body:
```json
{
  "message": "¿Cuáles son las mejores opciones culturales y gastronómicas en Lamas?",
  "context": {
    "name": "Castillo Medieval de Lamas",
    "province": "Lamas"
  },
  "session_id": "sesion-turista-123"
}
```

### Respuesta (200 OK):
```json
{
  "reply": "🏰 En **Lamas**, la 'Ciudad de los Tres Pisos', encontrarás una fascinante combinación de tradición e historia viva. Te recomiendo visitar el **Castillo Medieval de Lamas** con su arquitectura singular, el **Barrio Nativo Kechwa El Wayku** donde podrás adquirir artesanías tradicionales y admirar la arquitectura de tapial, y la **Chocolatería Pepitas de Cacao** para probar cacao nativo fino de aroma.",
  "suggested_actions": [
    "¿Cuáles son las cataratas más recomendadas?",
    "¿Qué visitar en un viaje familiar?",
    "¿Dónde conocer la ruta del cacao y café?",
    "¿Cómo llegar a la Laguna de Sauce?"
  ],
  "related_atractivos": [
    {
      "id_recurso": "REC-00204",
      "nombre": "CASTILLO MEDIEVAL DE LAMAS",
      "provincia": "LAMAS",
      "distrito": "LAMAS",
      "duracion_horas": 1.0,
      "costo_pen": 15.0,
      "dificultad": "Baja",
      "descripcion": "Singular fortaleza de estilo medieval erigida en la colina de Lamas..."
    },
    {
      "id_recurso": "REC-00206",
      "nombre": "COMUNIDAD NATIVA KECHWA EL WAYKU",
      "provincia": "LAMAS",
      "distrito": "LAMAS",
      "duracion_horas": 1.5,
      "costo_pen": 0.0,
      "dificultad": "Baja",
      "descripcion": "Comunidad ancestral depositaria del idioma kichwa y artesanía tradicional..."
    }
  ]
}
```

#### Ejemplo curl:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Qué cataratas puedo visitar cerca de Tarapoto?",
    "context": null
  }'
```

---

## 8. GET `/api/metricas`
Consulta métricas operativas del sistema (sesiones, ejecuciones, tiempo promedio de respuesta y cumplimiento de filtros).

### Respuesta (200 OK):
```json
{
  "sesiones": 42,
  "ejecuciones": 48,
  "valoraciones": 30,
  "utilidad_promedio": 4.8,
  "pct_eligio_alternativa": 93.3,
  "pct_explicacion_comprensible": 96.7,
  "tiempo_respuesta_ms_prom": 7.5,
  "pct_cumple_filtros": 100.0,
  "diversidad_categorias_prom": 3.2,
  "pct_cobertura_catalogo": 100.0
}
```

#### Ejemplo curl:
```bash
curl -X GET http://localhost:8000/api/metricas
```
