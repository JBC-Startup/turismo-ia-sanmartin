-- =====================================================================
--  TurismoIA San Martín — Base de datos PostgreSQL (v1.0)
--  Recomendador de atractivos turísticos de la región San Martín
--  Fuente base: Inventario de Recursos Turísticos – GORE San Martín
--  Probado en PostgreSQL 16 (compatible con 13+)
--
--  Orden de ejecución:
--     1) 01_esquema_turismoia.sql   (este archivo: tablas, catálogos, vistas, funciones)
--     2) 02_datos_turismoia.sql     (carga de los 307 recursos del CSV revisado)
--
--  Crear la BD antes (desde psql):
--     CREATE DATABASE turismoia ENCODING 'UTF8' TEMPLATE template0;
--     \c turismoia
--
--  Convención: NULL = "No informado" (no se inventan datos).
--  En dificultad y accesibilidad se distingue "No informado" de "No aplica"
--  mediante sus tablas catálogo.
-- =====================================================================

SET client_encoding = 'UTF8';

DROP SCHEMA IF EXISTS turismo CASCADE;
CREATE SCHEMA turismo;
SET search_path TO turismo, public;

CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- búsqueda aproximada por nombre (RF-11)


-- =====================================================================
-- 1. UBICACIÓN (UBIGEO INEI)
-- =====================================================================
CREATE TABLE departamento (
    id_departamento  CHAR(2)      PRIMARY KEY,
    nombre           VARCHAR(60)  NOT NULL UNIQUE
);

CREATE TABLE provincia (
    id_provincia     CHAR(4)      PRIMARY KEY,                 -- dep + prov, ej. 2206
    id_departamento  CHAR(2)      NOT NULL REFERENCES departamento,
    codigo           CHAR(2)      NOT NULL,
    nombre           VARCHAR(80)  NOT NULL,
    UNIQUE (id_departamento, codigo),
    UNIQUE (id_departamento, nombre),
    CHECK  (id_provincia = id_departamento || codigo)
);

CREATE TABLE distrito (
    ubigeo           CHAR(6)      PRIMARY KEY,                 -- ej. 220601
    id_provincia     CHAR(4)      NOT NULL REFERENCES provincia,
    codigo           CHAR(2)      NOT NULL,
    nombre           VARCHAR(80)  NOT NULL,
    UNIQUE (id_provincia, codigo),
    UNIQUE (id_provincia, nombre),
    CHECK  (ubigeo = id_provincia || codigo)
);


-- =====================================================================
-- 2. CLASIFICACIÓN OFICIAL (MINCETUR: categoría > tipo > subtipo)
-- =====================================================================
CREATE TABLE categoria (
    id_categoria     CHAR(2)       PRIMARY KEY,
    nombre           VARCHAR(100)  NOT NULL UNIQUE
);

-- El código de tipo NO es único globalmente (ej. "14 OTROS" existe en dos categorías)
CREATE TABLE tipo (
    id_tipo          SMALLINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_categoria     CHAR(2)       NOT NULL REFERENCES categoria,
    codigo           CHAR(2)       NOT NULL,
    nombre           VARCHAR(100)  NOT NULL,
    UNIQUE (id_categoria, codigo)
);

CREATE TABLE subtipo (
    id_subtipo       SMALLINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_tipo          SMALLINT      NOT NULL REFERENCES tipo,
    codigo           CHAR(3)       NOT NULL,
    nombre           VARCHAR(100)  NOT NULL,
    UNIQUE (id_tipo, codigo)
);

CREATE TABLE estado_recurso (
    id_estado           CHAR(2)      PRIMARY KEY,
    nombre              VARCHAR(30)  NOT NULL UNIQUE,
    visible_en_ranking  BOOLEAN      NOT NULL DEFAULT TRUE,     -- OBSERVADO = FALSE (sección 7.4)
    descripcion         VARCHAR(200)
);


-- =====================================================================
-- 3. SEGURIDAD / ADMINISTRACIÓN (RF-10, RNF-07)
-- =====================================================================
CREATE TABLE rol (
    id_rol           SMALLINT     PRIMARY KEY,
    nombre           VARCHAR(40)  NOT NULL UNIQUE,
    descripcion      VARCHAR(200)
);

CREATE TABLE permiso (
    id_permiso       SMALLINT     PRIMARY KEY,
    codigo           VARCHAR(50)  NOT NULL UNIQUE,
    descripcion      VARCHAR(200)
);

CREATE TABLE rol_permiso (
    id_rol           SMALLINT     NOT NULL REFERENCES rol ON DELETE CASCADE,
    id_permiso       SMALLINT     NOT NULL REFERENCES permiso ON DELETE CASCADE,
    PRIMARY KEY (id_rol, id_permiso)
);

CREATE TABLE usuario_administrador (
    id_usuario       INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre           VARCHAR(120) NOT NULL,
    correo           VARCHAR(150) NOT NULL CHECK (correo ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    clave_hash       VARCHAR(255) NOT NULL,                     -- bcrypt/argon2 desde la API, nunca texto plano
    id_rol           SMALLINT     NOT NULL REFERENCES rol,
    estado           VARCHAR(10)  NOT NULL DEFAULT 'activo'
                     CHECK (estado IN ('activo','inactivo','bloqueado')),
    ultimo_acceso    TIMESTAMPTZ,
    fecha_creacion   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_usuario_correo ON usuario_administrador (lower(correo));


-- =====================================================================
-- 4. CATÁLOGOS DE ATRIBUTOS ENRIQUECIDOS
-- =====================================================================
CREATE TABLE nivel_dificultad (
    id_dificultad    SMALLINT     PRIMARY KEY,
    nombre           VARCHAR(20)  NOT NULL UNIQUE,
    nivel_esfuerzo   SMALLINT     CHECK (nivel_esfuerzo BETWEEN 1 AND 3)   -- NULL en "No informado"/"No aplica"
);

CREATE TABLE nivel_accesibilidad (
    id_accesibilidad         SMALLINT     PRIMARY KEY,
    nombre                   VARCHAR(20)  NOT NULL UNIQUE,
    apto_movilidad_reducida  BOOLEAN                                       -- NULL = se desconoce
);

CREATE TABLE compania_viaje (
    id_compania      SMALLINT     PRIMARY KEY,
    nombre           VARCHAR(30)  NOT NULL UNIQUE,
    descripcion      VARCHAR(150)
);

CREATE TABLE grupo_etiqueta (
    id_grupo         SMALLINT     PRIMARY KEY,
    nombre           VARCHAR(30)  NOT NULL UNIQUE
);

CREATE TABLE etiqueta (
    id_etiqueta      SMALLINT     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre           VARCHAR(40)  NOT NULL UNIQUE CHECK (nombre ~ '^[a-z_]+$'),
    id_grupo         SMALLINT     NOT NULL REFERENCES grupo_etiqueta,
    descripcion      VARCHAR(200),
    estado           VARCHAR(10)  NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','inactivo'))
);

CREATE TABLE fuente (
    id_fuente        INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre           VARCHAR(200) NOT NULL,
    entidad          VARCHAR(150) NOT NULL,
    tipo_fuente      VARCHAR(25)  NOT NULL
                     CHECK (tipo_fuente IN ('oficial','operador','verificacion_directa','estimacion_equipo','otro')),
    url              TEXT         CHECK (url ~* '^https?://'),
    licencia         VARCHAR(100),
    fecha_consulta   DATE,
    UNIQUE (nombre, entidad)
);


-- =====================================================================
-- 5. CATÁLOGO DE ATRACTIVOS
-- =====================================================================
-- 5.1 Datos oficiales (no se mezclan con los enriquecidos)
CREATE TABLE atractivo (
    id_atractivo         INTEGER       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_recurso       VARCHAR(12)   NOT NULL UNIQUE CHECK (codigo_recurso ~ '^REC-[0-9]{5}$'),
    nombre               VARCHAR(150)  NOT NULL,
    id_subtipo           SMALLINT      NOT NULL REFERENCES subtipo,      -- tipo y categoría se derivan
    ubigeo               CHAR(6)       NOT NULL REFERENCES distrito,     -- provincia y dpto. se derivan
    latitud              NUMERIC(12,9) NOT NULL CHECK (latitud  BETWEEN -18.40 AND  -0.03),  -- rango Perú
    longitud             NUMERIC(12,9) NOT NULL CHECK (longitud BETWEEN -81.40 AND -68.60),
    id_estado            CHAR(2)       NOT NULL REFERENCES estado_recurso,
    fecha_corte          DATE          NOT NULL,                          -- fecha de corte del dataset oficial
    activo               BOOLEAN       NOT NULL DEFAULT TRUE,
    fecha_creacion       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    fecha_actualizacion  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    UNIQUE (nombre, ubigeo)                                               -- duplicados nombre–distrito (7.4)
);
CREATE INDEX ix_atractivo_ubigeo   ON atractivo (ubigeo);
CREATE INDEX ix_atractivo_subtipo  ON atractivo (id_subtipo);
CREATE INDEX ix_atractivo_estado   ON atractivo (id_estado);
CREATE INDEX ix_atractivo_nombre_trgm ON atractivo USING gin (nombre gin_trgm_ops);
CREATE INDEX ix_atractivo_nombre_fts  ON atractivo USING gin (to_tsvector('spanish', nombre));

-- 5.2 Atributos enriquecidos (relación 1:1 con atractivo)
CREATE TABLE atributo_enriquecido (
    id_atractivo            INTEGER       PRIMARY KEY REFERENCES atractivo ON DELETE CASCADE,
    descripcion_corta       TEXT          CHECK (char_length(descripcion_corta) >= 20),
    duracion_horas          NUMERIC(4,2)  CHECK (duracion_horas > 0 AND duracion_horas <= 24),
    costo_min_pen           NUMERIC(8,2)  CHECK (costo_min_pen >= 0),
    costo_max_pen           NUMERIC(8,2)  CHECK (costo_max_pen >= 0),
    es_gratuito             BOOLEAN       GENERATED ALWAYS AS (costo_max_pen = 0) STORED,
    id_dificultad           SMALLINT      NOT NULL DEFAULT 1 REFERENCES nivel_dificultad,
    id_accesibilidad        SMALLINT      NOT NULL DEFAULT 1 REFERENCES nivel_accesibilidad,
    horario_texto           VARCHAR(150),
    hora_apertura           TIME,
    hora_cierre             TIME,
    temporada_texto         VARCHAR(150),
    todo_el_anio            BOOLEAN       NOT NULL DEFAULT FALSE,
    mes_inicio              SMALLINT      CHECK (mes_inicio BETWEEN 1 AND 12),
    mes_fin                 SMALLINT      CHECK (mes_fin    BETWEEN 1 AND 12),
    requiere_validacion     BOOLEAN       NOT NULL DEFAULT TRUE,
    fecha_verificacion      DATE,
    id_usuario_verificador  INTEGER       REFERENCES usuario_administrador ON DELETE SET NULL,
    fecha_actualizacion     TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CHECK (costo_max_pen IS NULL OR costo_min_pen IS NULL OR costo_max_pen >= costo_min_pen),
    CHECK ((hora_apertura IS NULL) = (hora_cierre IS NULL)),
    CHECK ((mes_inicio IS NULL) = (mes_fin IS NULL)),
    CHECK (NOT (todo_el_anio AND mes_inicio IS NOT NULL))
);
CREATE INDEX ix_enriq_duracion    ON atributo_enriquecido (duracion_horas);
CREATE INDEX ix_enriq_costo       ON atributo_enriquecido (costo_min_pen);
CREATE INDEX ix_enriq_descr_fts   ON atributo_enriquecido USING gin (to_tsvector('spanish', coalesce(descripcion_corta,'')));

-- 5.3 Etiquetas de interés (N:M) — base del vector de contenido / TF-IDF
CREATE TABLE atractivo_etiqueta (
    id_atractivo     INTEGER       NOT NULL REFERENCES atractivo ON DELETE CASCADE,
    id_etiqueta      SMALLINT      NOT NULL REFERENCES etiqueta,
    peso             NUMERIC(3,2)  NOT NULL DEFAULT 1.00 CHECK (peso > 0 AND peso <= 1),
    id_fuente        INTEGER       REFERENCES fuente ON DELETE SET NULL,
    PRIMARY KEY (id_atractivo, id_etiqueta)
);
CREATE INDEX ix_atr_etq_etiqueta ON atractivo_etiqueta (id_etiqueta);

-- 5.4 Público recomendado (N:M). "Todos" = apto para cualquier compañía.
CREATE TABLE atractivo_compania (
    id_atractivo     INTEGER       NOT NULL REFERENCES atractivo ON DELETE CASCADE,
    id_compania      SMALLINT      NOT NULL REFERENCES compania_viaje,
    PRIMARY KEY (id_atractivo, id_compania)
);

-- 5.5 Trazabilidad: fuente y fecha de verificación por campo (RF-13, RNF-04)
CREATE TABLE fuente_dato (
    id_fuente_dato          INTEGER       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_atractivo            INTEGER       NOT NULL REFERENCES atractivo ON DELETE CASCADE,
    id_fuente               INTEGER       NOT NULL REFERENCES fuente,
    campo                   VARCHAR(30)   NOT NULL CHECK (campo IN (
                                'catalogo_base','ubicacion','descripcion_corta','duracion_horas','costo',
                                'dificultad','accesibilidad','horario','temporada','etiquetas','publico','imagen')),
    url_especifica          TEXT          CHECK (url_especifica ~* '^https?://'),
    fecha_verificacion      DATE,
    id_usuario_responsable  INTEGER       REFERENCES usuario_administrador ON DELETE SET NULL,
    observacion             VARCHAR(300),
    UNIQUE (id_atractivo, campo, id_fuente)
);
CREATE INDEX ix_fuente_dato_atractivo ON fuente_dato (id_atractivo);

-- 5.6 Imágenes
CREATE TABLE atractivo_imagen (
    id_imagen          INTEGER       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_atractivo       INTEGER       NOT NULL REFERENCES atractivo ON DELETE CASCADE,
    url                TEXT          NOT NULL CHECK (url ~* '^https?://'),
    texto_alternativo  VARCHAR(200)  NOT NULL,                    -- accesibilidad (RNF-09)
    credito            VARCHAR(150),
    es_principal       BOOLEAN       NOT NULL DEFAULT FALSE,
    orden              SMALLINT      NOT NULL DEFAULT 1 CHECK (orden >= 1),
    id_fuente          INTEGER       REFERENCES fuente ON DELETE SET NULL
);
CREATE UNIQUE INDEX ux_imagen_principal ON atractivo_imagen (id_atractivo) WHERE es_principal;

-- 5.7 Auditoría de cambios (historial_actualizacion)
CREATE TABLE historial_actualizacion (
    id_historial     BIGINT        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabla            VARCHAR(60)   NOT NULL,
    registro_id      VARCHAR(40)   NOT NULL,
    operacion        CHAR(1)       NOT NULL CHECK (operacion IN ('I','U','D')),
    campo            VARCHAR(60),
    valor_anterior   TEXT,
    valor_nuevo      TEXT,
    motivo           VARCHAR(300),
    id_usuario       INTEGER       REFERENCES usuario_administrador ON DELETE SET NULL,
    fecha            TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX ix_historial_registro ON historial_actualizacion (tabla, registro_id);


-- =====================================================================
-- 6. MOTOR DE RECOMENDACIÓN (versionado para reproducibilidad, RNF-06/RNF-10)
-- =====================================================================
CREATE TABLE modelo_version (
    id_modelo           SMALLINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre              VARCHAR(80)   NOT NULL,
    version             VARCHAR(20)   NOT NULL,
    algoritmo           VARCHAR(20)   NOT NULL CHECK (algoritmo IN ('contenido_coseno','kmeans','hibrido')),
    peso_intereses      NUMERIC(4,3),
    peso_tiempo         NUMERIC(4,3),
    peso_ubicacion      NUMERIC(4,3),
    peso_presupuesto    NUMERIC(4,3),
    peso_accesibilidad  NUMERIC(4,3),
    parametros          JSONB         NOT NULL DEFAULT '{}'::jsonb,   -- TF-IDF, top_n, diversidad, k...
    version_dataset     VARCHAR(40)   NOT NULL,
    descripcion         VARCHAR(300),
    activo              BOOLEAN       NOT NULL DEFAULT FALSE,
    fecha_creacion      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    UNIQUE (nombre, version),
    CHECK (
        (peso_intereses IS NULL AND peso_tiempo IS NULL AND peso_ubicacion IS NULL
         AND peso_presupuesto IS NULL AND peso_accesibilidad IS NULL)
     OR (peso_intereses + peso_tiempo + peso_ubicacion + peso_presupuesto + peso_accesibilidad = 1.000)
    )
);
CREATE UNIQUE INDEX ux_modelo_activo ON modelo_version (algoritmo) WHERE activo;

CREATE TABLE cluster_perfil (
    id_cluster       SMALLINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_modelo        SMALLINT      NOT NULL REFERENCES modelo_version ON DELETE CASCADE,
    numero           SMALLINT      NOT NULL CHECK (numero >= 0),
    nombre           VARCHAR(80)   NOT NULL,
    descripcion      VARCHAR(300),
    centroide        JSONB,
    UNIQUE (id_modelo, numero)
);


-- =====================================================================
-- 7. SESIONES ANÓNIMAS DE PREFERENCIA (RF-03, RF-04, RNF-05)
--    Sin cuenta, sin datos personales, sin coordenadas exactas.
-- =====================================================================
CREATE TABLE sesion_preferencia (
    id_sesion                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),   -- id anónimo
    tiempo_disponible_horas  NUMERIC(4,2)  NOT NULL CHECK (tiempo_disponible_horas > 0 AND tiempo_disponible_horas <= 24),
    presupuesto_max_pen      NUMERIC(8,2)  CHECK (presupuesto_max_pen >= 0),        -- NULL = sin límite
    id_compania              SMALLINT      REFERENCES compania_viaje,
    id_dificultad_max        SMALLINT      REFERENCES nivel_dificultad,             -- nivel de esfuerzo aceptado
    requiere_accesibilidad   BOOLEAN       NOT NULL DEFAULT FALSE,
    ubigeo_referencia        CHAR(6)       REFERENCES distrito,                     -- punto de partida aproximado
    radio_km                 NUMERIC(6,1)  CHECK (radio_km > 0),
    texto_libre              VARCHAR(300),                                          -- palabras clave (TF-IDF)
    tipo_dispositivo         VARCHAR(10)   CHECK (tipo_dispositivo IN ('movil','tablet','escritorio')),
    consentimiento_datos     BOOLEAN       NOT NULL DEFAULT FALSE,
    fecha_creacion           TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CHECK (radio_km IS NULL OR ubigeo_referencia IS NOT NULL)
);
CREATE INDEX ix_sesion_fecha ON sesion_preferencia (fecha_creacion);

CREATE TABLE sesion_interes (
    id_sesion        UUID          NOT NULL REFERENCES sesion_preferencia ON DELETE CASCADE,
    id_etiqueta      SMALLINT      NOT NULL REFERENCES etiqueta,
    peso             NUMERIC(3,2)  NOT NULL DEFAULT 1.00 CHECK (peso > 0 AND peso <= 1),
    PRIMARY KEY (id_sesion, id_etiqueta)
);

CREATE TABLE sesion_categoria (
    id_sesion        UUID          NOT NULL REFERENCES sesion_preferencia ON DELETE CASCADE,
    id_categoria     CHAR(2)       NOT NULL REFERENCES categoria,
    PRIMARY KEY (id_sesion, id_categoria)
);

CREATE TABLE sesion_provincia (
    id_sesion        UUID          NOT NULL REFERENCES sesion_preferencia ON DELETE CASCADE,
    id_provincia     CHAR(4)       NOT NULL REFERENCES provincia,
    PRIMARY KEY (id_sesion, id_provincia)
);

CREATE TABLE sesion_distrito (
    id_sesion        UUID          NOT NULL REFERENCES sesion_preferencia ON DELETE CASCADE,
    ubigeo           CHAR(6)       NOT NULL REFERENCES distrito,
    PRIMARY KEY (id_sesion, ubigeo)
);


-- =====================================================================
-- 8. RESULTADOS Y VALORACIÓN (RF-05..RF-09, RF-14, RF-15)
--    Separados del catálogo para evaluar el sistema.
-- =====================================================================
CREATE TABLE ejecucion_recomendacion (
    id_ejecucion          BIGINT        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_sesion             UUID          NOT NULL REFERENCES sesion_preferencia ON DELETE CASCADE,
    id_modelo             SMALLINT      NOT NULL REFERENCES modelo_version,
    id_cluster            SMALLINT      REFERENCES cluster_perfil,
    total_candidatos      INTEGER       CHECK (total_candidatos >= 0),     -- tras filtros obligatorios
    tiempo_respuesta_ms   INTEGER       CHECK (tiempo_respuesta_ms >= 0),  -- meta < 3000 ms (RNF-01)
    parametros_aplicados  JSONB,
    fecha_generacion      TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX ix_ejecucion_sesion ON ejecucion_recomendacion (id_sesion);

CREATE TABLE recomendacion (
    id_recomendacion       BIGINT        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_ejecucion           BIGINT        NOT NULL REFERENCES ejecucion_recomendacion ON DELETE CASCADE,
    id_atractivo           INTEGER       NOT NULL REFERENCES atractivo,
    posicion               SMALLINT      NOT NULL CHECK (posicion >= 1),
    puntaje_afinidad       NUMERIC(5,4)  NOT NULL CHECK (puntaje_afinidad BETWEEN 0 AND 1),
    puntaje_intereses      NUMERIC(5,4)  CHECK (puntaje_intereses     BETWEEN 0 AND 1),
    puntaje_tiempo         NUMERIC(5,4)  CHECK (puntaje_tiempo        BETWEEN 0 AND 1),
    puntaje_ubicacion      NUMERIC(5,4)  CHECK (puntaje_ubicacion     BETWEEN 0 AND 1),
    puntaje_presupuesto    NUMERIC(5,4)  CHECK (puntaje_presupuesto   BETWEEN 0 AND 1),
    puntaje_accesibilidad  NUMERIC(5,4)  CHECK (puntaje_accesibilidad BETWEEN 0 AND 1),
    cumple_filtros         BOOLEAN       NOT NULL DEFAULT TRUE,
    explicacion            VARCHAR(400)  NOT NULL,
    UNIQUE (id_ejecucion, posicion),
    UNIQUE (id_ejecucion, id_atractivo),
    UNIQUE (id_recomendacion, id_ejecucion)          -- soporte para FK compuesta de valoracion
);
CREATE INDEX ix_recomendacion_atractivo ON recomendacion (id_atractivo);

-- Etiquetas que originaron la coincidencia (explicación, RF-07)
CREATE TABLE recomendacion_etiqueta (
    id_recomendacion BIGINT        NOT NULL REFERENCES recomendacion ON DELETE CASCADE,
    id_etiqueta      SMALLINT      NOT NULL REFERENCES etiqueta,
    PRIMARY KEY (id_recomendacion, id_etiqueta)
);

-- Una valoración por Top-N; la alternativa elegida debe pertenecer al mismo Top-N
CREATE TABLE valoracion (
    id_valoracion             BIGINT        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_ejecucion              BIGINT        NOT NULL UNIQUE REFERENCES ejecucion_recomendacion ON DELETE CASCADE,
    utilidad                  SMALLINT      NOT NULL CHECK (utilidad BETWEEN 1 AND 5),
    eligio_alternativa        BOOLEAN       NOT NULL,
    id_recomendacion_elegida  BIGINT,
    explicacion_comprensible  BOOLEAN       NOT NULL,
    comentario                VARCHAR(500),
    fecha                     TIMESTAMPTZ   NOT NULL DEFAULT now(),
    FOREIGN KEY (id_recomendacion_elegida, id_ejecucion)
        REFERENCES recomendacion (id_recomendacion, id_ejecucion),
    CHECK (id_recomendacion_elegida IS NULL OR eligio_alternativa)
);


-- =====================================================================
-- 9. FUNCIONES Y TRIGGERS
-- =====================================================================
-- 9.1 fecha_actualizacion automática
CREATE OR REPLACE FUNCTION fn_set_fecha_actualizacion() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.fecha_actualizacion := now();
    RETURN NEW;
END $$;

CREATE TRIGGER tg_atractivo_fecha  BEFORE UPDATE ON atractivo
    FOR EACH ROW EXECUTE FUNCTION fn_set_fecha_actualizacion();
CREATE TRIGGER tg_enriq_fecha      BEFORE UPDATE ON atributo_enriquecido
    FOR EACH ROW EXECUTE FUNCTION fn_set_fecha_actualizacion();

-- 9.2 Auditoría campo por campo.
--   La API debe ejecutar en cada transacción:  SET LOCAL turismoia.id_usuario = '<id>';
--   Para cargas masivas:                         SET LOCAL turismoia.auditar = 'off';
CREATE OR REPLACE FUNCTION fn_auditar() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_usuario  INTEGER := nullif(current_setting('turismoia.id_usuario', true), '')::INTEGER;
    v_motivo   TEXT    := nullif(current_setting('turismoia.motivo', true), '');
    v_pk       TEXT    := TG_ARGV[0];
    v_old      JSONB;
    v_new      JSONB;
    v_key      TEXT;
BEGIN
    IF coalesce(current_setting('turismoia.auditar', true), 'on') = 'off' THEN
        RETURN coalesce(NEW, OLD);
    END IF;

    IF TG_OP = 'INSERT' THEN
        v_new := to_jsonb(NEW);
        INSERT INTO historial_actualizacion (tabla, registro_id, operacion, campo, valor_nuevo, motivo, id_usuario)
        VALUES (TG_TABLE_NAME, v_new->>v_pk, 'I', NULL, v_new::text, v_motivo, v_usuario);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        v_old := to_jsonb(OLD);
        INSERT INTO historial_actualizacion (tabla, registro_id, operacion, campo, valor_anterior, motivo, id_usuario)
        VALUES (TG_TABLE_NAME, v_old->>v_pk, 'D', NULL, v_old::text, v_motivo, v_usuario);
        RETURN OLD;
    END IF;

    v_old := to_jsonb(OLD);
    v_new := to_jsonb(NEW);
    FOR v_key IN SELECT jsonb_object_keys(v_new) LOOP
        CONTINUE WHEN v_key IN ('fecha_actualizacion');
        IF v_old->v_key IS DISTINCT FROM v_new->v_key THEN
            INSERT INTO historial_actualizacion
                (tabla, registro_id, operacion, campo, valor_anterior, valor_nuevo, motivo, id_usuario)
            VALUES (TG_TABLE_NAME, v_new->>v_pk, 'U', v_key, v_old->>v_key, v_new->>v_key, v_motivo, v_usuario);
        END IF;
    END LOOP;
    RETURN NEW;
END $$;

CREATE TRIGGER tg_auditar_atractivo
    AFTER INSERT OR UPDATE OR DELETE ON atractivo
    FOR EACH ROW EXECUTE FUNCTION fn_auditar('id_atractivo');
CREATE TRIGGER tg_auditar_enriquecido
    AFTER INSERT OR UPDATE OR DELETE ON atributo_enriquecido
    FOR EACH ROW EXECUTE FUNCTION fn_auditar('id_atractivo');

-- 9.3 Distancia aproximada (km) entre dos puntos — fórmula de Haversine
CREATE OR REPLACE FUNCTION fn_distancia_km(lat1 NUMERIC, lon1 NUMERIC, lat2 NUMERIC, lon2 NUMERIC)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT round((6371 * 2 * asin(sqrt(
              power(sin(radians((lat2 - lat1)::float8) / 2), 2)
            + cos(radians(lat1::float8)) * cos(radians(lat2::float8))
            * power(sin(radians((lon2 - lon1)::float8) / 2), 2))))::numeric, 2)
$$;

-- 9.4 Filtros obligatorios del recomendador (paso 2 del flujo 9.2 / RF-12).
--     Devuelve los candidatos elegibles para una sesión; el motor IA calcula la afinidad después.
--     Datos "no informados" no se excluyen, pero se marcan para mostrar advertencia.
CREATE OR REPLACE FUNCTION fn_candidatos(p_id_sesion UUID)
RETURNS TABLE (
    id_atractivo       INTEGER,
    codigo_recurso     VARCHAR,
    nombre             VARCHAR,
    provincia          VARCHAR,
    distrito           VARCHAR,
    duracion_horas     NUMERIC,
    costo_min_pen      NUMERIC,
    dificultad         VARCHAR,
    distancia_km       NUMERIC,
    datos_incompletos  BOOLEAN
)
LANGUAGE sql STABLE AS $$
    WITH s AS (
        SELECT sp.*, nd.nivel_esfuerzo AS esfuerzo_max,
               ref.lat_ref, ref.lon_ref
        FROM sesion_preferencia sp
        LEFT JOIN nivel_dificultad nd ON nd.id_dificultad = sp.id_dificultad_max
        LEFT JOIN LATERAL (                              -- centroide aproximado del distrito de referencia
            SELECT avg(a2.latitud) AS lat_ref, avg(a2.longitud) AS lon_ref
            FROM atractivo a2 WHERE a2.ubigeo = sp.ubigeo_referencia
        ) ref ON TRUE
        WHERE sp.id_sesion = p_id_sesion
    )
    SELECT a.id_atractivo, a.codigo_recurso, a.nombre, p.nombre, d.nombre,
           e.duracion_horas, e.costo_min_pen, nd.nombre,
           CASE WHEN s.lat_ref IS NOT NULL
                THEN fn_distancia_km(s.lat_ref, s.lon_ref, a.latitud, a.longitud) END,
           (e.duracion_horas IS NULL OR e.costo_min_pen IS NULL OR nd.nivel_esfuerzo IS NULL)
    FROM s
    CROSS JOIN atractivo a
    JOIN estado_recurso er        ON er.id_estado = a.id_estado AND er.visible_en_ranking
    JOIN distrito d               ON d.ubigeo = a.ubigeo
    JOIN provincia p              ON p.id_provincia = d.id_provincia
    JOIN subtipo st               ON st.id_subtipo = a.id_subtipo
    JOIN tipo t                   ON t.id_tipo = st.id_tipo
    LEFT JOIN atributo_enriquecido e ON e.id_atractivo = a.id_atractivo
    LEFT JOIN nivel_dificultad nd    ON nd.id_dificultad = e.id_dificultad
    LEFT JOIN nivel_accesibilidad na ON na.id_accesibilidad = e.id_accesibilidad
    WHERE a.activo
      -- tiempo disponible
      AND (e.duracion_horas IS NULL OR e.duracion_horas <= s.tiempo_disponible_horas)
      -- presupuesto
      AND (s.presupuesto_max_pen IS NULL OR e.costo_min_pen IS NULL OR e.costo_min_pen <= s.presupuesto_max_pen)
      -- esfuerzo
      AND (s.esfuerzo_max IS NULL OR nd.nivel_esfuerzo IS NULL OR nd.nivel_esfuerzo <= s.esfuerzo_max)
      -- accesibilidad: si se requiere, solo atractivos confirmados como aptos
      AND (NOT s.requiere_accesibilidad OR na.apto_movilidad_reducida IS TRUE)
      -- zona: provincias / distritos elegidos (si no eligió ninguno, toda la región)
      AND (NOT EXISTS (SELECT 1 FROM sesion_provincia x WHERE x.id_sesion = s.id_sesion)
           OR p.id_provincia IN (SELECT x.id_provincia FROM sesion_provincia x WHERE x.id_sesion = s.id_sesion))
      AND (NOT EXISTS (SELECT 1 FROM sesion_distrito x WHERE x.id_sesion = s.id_sesion)
           OR a.ubigeo IN (SELECT x.ubigeo FROM sesion_distrito x WHERE x.id_sesion = s.id_sesion))
      -- categorías elegidas
      AND (NOT EXISTS (SELECT 1 FROM sesion_categoria x WHERE x.id_sesion = s.id_sesion)
           OR t.id_categoria IN (SELECT x.id_categoria FROM sesion_categoria x WHERE x.id_sesion = s.id_sesion))
      -- radio de distancia
      AND (s.radio_km IS NULL OR s.lat_ref IS NULL
           OR fn_distancia_km(s.lat_ref, s.lon_ref, a.latitud, a.longitud) <= s.radio_km)
      -- compañía: el atractivo es para "Todos", para esa compañía, o no tiene dato
      AND (s.id_compania IS NULL
           OR NOT EXISTS (SELECT 1 FROM atractivo_compania ac WHERE ac.id_atractivo = a.id_atractivo)
           OR EXISTS (SELECT 1 FROM atractivo_compania ac
                      JOIN compania_viaje cv ON cv.id_compania = ac.id_compania
                      WHERE ac.id_atractivo = a.id_atractivo
                        AND (ac.id_compania = s.id_compania OR cv.nombre = 'Todos')))
$$;


-- =====================================================================
-- 10. VISTAS
-- =====================================================================
-- 10.1 Catálogo completo desnormalizado (RF-01, RF-02, RF-08)
CREATE OR REPLACE VIEW v_catalogo AS
SELECT a.id_atractivo,
       a.codigo_recurso,
       a.nombre,
       c.id_categoria, c.nombre             AS categoria,
       t.id_tipo,      t.nombre             AS tipo,
       st.id_subtipo,  st.nombre            AS subtipo,
       dp.nombre                            AS departamento,
       p.id_provincia, p.nombre             AS provincia,
       a.ubigeo,       d.nombre             AS distrito,
       a.latitud, a.longitud,
       er.nombre                            AS estado,
       er.visible_en_ranking,
       e.descripcion_corta,
       e.duracion_horas,
       e.costo_min_pen, e.costo_max_pen, e.es_gratuito,
       CASE WHEN e.costo_max_pen IS NULL THEN 'No informado'
            WHEN e.costo_max_pen = 0     THEN 'Gratuito'
            WHEN e.costo_min_pen = e.costo_max_pen THEN 'S/ ' || to_char(e.costo_min_pen, 'FM9990.00')
            ELSE 'S/ ' || to_char(e.costo_min_pen, 'FM9990.00') || ' – ' || to_char(e.costo_max_pen, 'FM9990.00')
       END                                  AS costo_texto,
       nd.nombre                            AS dificultad,
       nd.nivel_esfuerzo,
       na.nombre                            AS accesibilidad,
       na.apto_movilidad_reducida,
       coalesce(e.horario_texto,  'No informado') AS horario,
       e.hora_apertura, e.hora_cierre,
       coalesce(e.temporada_texto,'No informado') AS temporada,
       e.todo_el_anio, e.mes_inicio, e.mes_fin,
       (SELECT string_agg(et.nombre, ';' ORDER BY et.nombre)
          FROM atractivo_etiqueta ae JOIN etiqueta et USING (id_etiqueta)
         WHERE ae.id_atractivo = a.id_atractivo)            AS etiquetas,
       (SELECT string_agg(cv.nombre, ';' ORDER BY cv.id_compania)
          FROM atractivo_compania ac JOIN compania_viaje cv USING (id_compania)
         WHERE ac.id_atractivo = a.id_atractivo)            AS publico_recomendado,
       (SELECT im.url FROM atractivo_imagen im
         WHERE im.id_atractivo = a.id_atractivo AND im.es_principal) AS imagen_principal,
       e.requiere_validacion,
       e.fecha_verificacion,
       a.fecha_corte,
       a.activo
FROM atractivo a
JOIN subtipo st        ON st.id_subtipo = a.id_subtipo
JOIN tipo t            ON t.id_tipo = st.id_tipo
JOIN categoria c       ON c.id_categoria = t.id_categoria
JOIN distrito d        ON d.ubigeo = a.ubigeo
JOIN provincia p       ON p.id_provincia = d.id_provincia
JOIN departamento dp   ON dp.id_departamento = p.id_departamento
JOIN estado_recurso er ON er.id_estado = a.id_estado
LEFT JOIN atributo_enriquecido e ON e.id_atractivo = a.id_atractivo
LEFT JOIN nivel_dificultad nd    ON nd.id_dificultad = e.id_dificultad
LEFT JOIN nivel_accesibilidad na ON na.id_accesibilidad = e.id_accesibilidad;

-- 10.2 Solo lo que puede entrar al ranking público (excluye OBSERVADO e inactivos)
CREATE OR REPLACE VIEW v_catalogo_recomendable AS
SELECT * FROM v_catalogo WHERE visible_en_ranking AND activo;

-- 10.3 Fuente y fecha de verificación por campo (RF-13)
CREATE OR REPLACE VIEW v_fuentes_atractivo AS
SELECT a.id_atractivo, a.codigo_recurso, a.nombre AS atractivo,
       fd.campo, f.nombre AS fuente, f.entidad, f.tipo_fuente,
       coalesce(fd.url_especifica, f.url) AS url,
       f.licencia, fd.fecha_verificacion, u.nombre AS responsable, fd.observacion
FROM fuente_dato fd
JOIN atractivo a ON a.id_atractivo = fd.id_atractivo
JOIN fuente f    ON f.id_fuente = fd.id_fuente
LEFT JOIN usuario_administrador u ON u.id_usuario = fd.id_usuario_responsable;

-- 10.4 Diversidad por Top-N (meta: ≥ 2 categorías/tipos distintos)
CREATE OR REPLACE VIEW v_diversidad_ejecucion AS
SELECT r.id_ejecucion,
       count(*)                          AS n_items,
       count(DISTINCT t.id_categoria)    AS categorias_distintas,
       count(DISTINCT t.id_tipo)         AS tipos_distintos,
       count(DISTINCT d.id_provincia)    AS provincias_distintas,
       bool_and(r.cumple_filtros)        AS cumple_filtros_todos,
       round(avg(r.puntaje_afinidad), 4) AS afinidad_promedio
FROM recomendacion r
JOIN atractivo a ON a.id_atractivo = r.id_atractivo
JOIN subtipo st  ON st.id_subtipo = a.id_subtipo
JOIN tipo t      ON t.id_tipo = st.id_tipo
JOIN distrito d  ON d.ubigeo = a.ubigeo
GROUP BY r.id_ejecucion;

-- 10.5 Resumen de métricas del prototipo (RF-16, sección 11)
CREATE OR REPLACE VIEW v_metricas_prototipo AS
SELECT
    (SELECT count(*) FROM sesion_preferencia)                                 AS sesiones,
    (SELECT count(*) FROM ejecucion_recomendacion)                            AS ejecuciones,
    (SELECT count(*) FROM valoracion)                                         AS valoraciones,
    (SELECT round(avg(utilidad), 2) FROM valoracion)                          AS utilidad_promedio,      -- meta ≥ 4
    (SELECT round(100.0 * avg(eligio_alternativa::int), 1) FROM valoracion)   AS pct_eligio_alternativa, -- meta ≥ 80 %
    (SELECT round(100.0 * avg(explicacion_comprensible::int), 1) FROM valoracion) AS pct_explicacion_comprensible,
    (SELECT round(avg(tiempo_respuesta_ms)) FROM ejecucion_recomendacion)     AS tiempo_respuesta_ms_prom, -- meta < 3000
    (SELECT round(100.0 * avg(cumple_filtros::int), 1) FROM recomendacion)   AS pct_cumple_filtros,     -- meta 100 %
    (SELECT round(avg(categorias_distintas), 2) FROM v_diversidad_ejecucion)  AS diversidad_categorias_prom, -- meta ≥ 2
    (SELECT round(100.0 * count(DISTINCT r.id_atractivo)
                 / nullif((SELECT count(*) FROM v_catalogo_recomendable), 0), 1)
       FROM recomendacion r)                                                  AS pct_cobertura_catalogo; -- meta ≥ 60 %

-- 10.6 Calidad de datos: cuántos atributos faltan por completar
CREATE OR REPLACE VIEW v_calidad_datos AS
SELECT count(*)                                                    AS total_atractivos,
       count(*) FILTER (WHERE e.descripcion_corta IS NULL)         AS sin_descripcion,
       count(*) FILTER (WHERE e.duracion_horas IS NULL)            AS sin_duracion,
       count(*) FILTER (WHERE e.costo_min_pen IS NULL)             AS sin_costo,
       count(*) FILTER (WHERE nd.nivel_esfuerzo IS NULL)           AS sin_dificultad,
       count(*) FILTER (WHERE na.apto_movilidad_reducida IS NULL)  AS sin_accesibilidad,
       count(*) FILTER (WHERE e.horario_texto IS NULL)             AS sin_horario,
       count(*) FILTER (WHERE e.temporada_texto IS NULL)           AS sin_temporada,
       count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM atractivo_etiqueta x WHERE x.id_atractivo = a.id_atractivo)) AS sin_etiquetas,
       count(*) FILTER (WHERE e.requiere_validacion)               AS pendientes_validacion
FROM atractivo a
LEFT JOIN atributo_enriquecido e ON e.id_atractivo = a.id_atractivo
LEFT JOIN nivel_dificultad nd    ON nd.id_dificultad = e.id_dificultad
LEFT JOIN nivel_accesibilidad na ON na.id_accesibilidad = e.id_accesibilidad;


-- =====================================================================
-- 11. DATOS SEMILLA DE CATÁLOGOS
-- =====================================================================
INSERT INTO estado_recurso (id_estado, nombre, visible_en_ranking, descripcion) VALUES
 ('01','PUBLICADO',  TRUE,  'Recurso publicado en el inventario oficial'),
 ('02','REGISTRADO', TRUE,  'Recurso registrado en el inventario oficial'),
 ('03','OBSERVADO',  FALSE, 'Recurso con observaciones; excluido del ranking público');

INSERT INTO nivel_dificultad (id_dificultad, nombre, nivel_esfuerzo) VALUES
 (1,'No informado',NULL), (2,'No aplica',NULL), (3,'Baja',1), (4,'Media',2), (5,'Alta',3);

INSERT INTO nivel_accesibilidad (id_accesibilidad, nombre, apto_movilidad_reducida) VALUES
 (1,'No informado',NULL), (2,'No aplica',NULL), (3,'Sí',TRUE), (4,'Parcial',TRUE), (5,'No',FALSE);

INSERT INTO compania_viaje (id_compania, nombre, descripcion) VALUES
 (1,'Todos','Apto para cualquier tipo de visitante'),
 (2,'Solo','Viaja solo'),
 (3,'Pareja','Viaja en pareja'),
 (4,'Amigos','Grupo de amigos'),
 (5,'Familia','Familia sin niños pequeños'),
 (6,'Familia con niños','Familia con niños'),
 (7,'Adulto mayor','Viaja con personas adultas mayores');

INSERT INTO grupo_etiqueta (id_grupo, nombre) VALUES
 (1,'naturaleza'), (2,'cultura'), (3,'gastronomia'), (4,'actividad'), (5,'turismo_rural');

INSERT INTO rol (id_rol, nombre, descripcion) VALUES
 (1,'administrador','Acceso total: usuarios, catálogo, modelos y métricas'),
 (2,'editor_contenido','Mantiene atributos, descripciones, etiquetas, imágenes y fuentes'),
 (3,'analista','Equipo del proyecto: consulta valoraciones y métricas');

INSERT INTO permiso (id_permiso, codigo, descripcion) VALUES
 (1,'catalogo.leer','Consultar catálogo y fuentes'),
 (2,'catalogo.editar','Crear/editar atractivos y atributos enriquecidos'),
 (3,'catalogo.eliminar','Desactivar o eliminar atractivos'),
 (4,'etiquetas.gestionar','Gestionar etiquetas'),
 (5,'metricas.ver','Ver valoraciones y métricas del prototipo'),
 (6,'modelos.gestionar','Registrar versiones y pesos del recomendador'),
 (7,'usuarios.gestionar','Gestionar usuarios administradores'),
 (8,'historial.ver','Consultar historial de cambios');

INSERT INTO rol_permiso (id_rol, id_permiso)
SELECT 1, id_permiso FROM permiso
UNION ALL SELECT 2, x FROM unnest(ARRAY[1,2,4,8]) x
UNION ALL SELECT 3, x FROM unnest(ARRAY[1,5,8]) x;

INSERT INTO fuente (nombre, entidad, tipo_fuente, url, licencia, fecha_consulta) VALUES
 ('Inventario de recursos turísticos de la región San Martín',
  'Gobierno Regional de San Martín - GORE San Martín', 'oficial',
  'https://www.datosabiertos.gob.pe/dataset/inventario-de-recursos-tur%C3%ADsticos-de-la-regi%C3%B3n-san-mart%C3%ADn-%E2%80%93-gore-san-mart%C3%ADn-grsm',
  'Open Data Commons Attribution License', DATE '2026-06-21'),
 ('Enriquecimiento TurismoIA – dataset revisión 307',
  'Equipo TurismoIA San Martín (UNSM)', 'estimacion_equipo', NULL, NULL, NULL);

INSERT INTO modelo_version (nombre, version, algoritmo,
    peso_intereses, peso_tiempo, peso_ubicacion, peso_presupuesto, peso_accesibilidad,
    parametros, version_dataset, descripcion, activo) VALUES
 ('baseline_contenido', '1.0', 'contenido_coseno', 0.450, 0.200, 0.150, 0.100, 0.100,
  '{"top_n":5,"vectorizacion":["one_hot","tfidf"],"similitud":"coseno","diversidad":{"max_misma_categoria":3,"max_mismo_tipo":2}}',
  'revision_307', 'Baseline de la sección 9.3: afinidad = 0.45·intereses + 0.20·tiempo + 0.15·ubicación + 0.10·presupuesto + 0.10·accesibilidad', TRUE),
 ('kmeans_perfiles', '0.1', 'kmeans', NULL, NULL, NULL, NULL, NULL,
  '{"k":4,"variables":["intereses","tiempo","presupuesto","esfuerzo"]}',
  'revision_307', 'Experimental: agrupamiento de perfiles frecuentes; no reemplaza los filtros', FALSE);
