-- =====================================================================
-- Migración 001: Soporte de imágenes panorámicas 360° en atractivo_imagen
-- =====================================================================
BEGIN;

ALTER TABLE turismo.atractivo_imagen
    ADD COLUMN IF NOT EXISTS tipo VARCHAR(10) NOT NULL DEFAULT 'normal';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'atractivo_imagen_tipo_check'
          AND conrelid = 'turismo.atractivo_imagen'::regclass
    ) THEN
        ALTER TABLE turismo.atractivo_imagen
            ADD CONSTRAINT atractivo_imagen_tipo_check CHECK (tipo IN ('normal', '360'));
    END IF;
END $$;

DROP INDEX IF EXISTS turismo.ux_imagen_principal;
CREATE UNIQUE INDEX ux_imagen_principal
    ON turismo.atractivo_imagen (id_atractivo, tipo)
    WHERE es_principal;

CREATE OR REPLACE VIEW turismo.v_catalogo AS
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
          FROM turismo.atractivo_etiqueta ae JOIN turismo.etiqueta et USING (id_etiqueta)
         WHERE ae.id_atractivo = a.id_atractivo)            AS etiquetas,
       (SELECT string_agg(cv.nombre, ';' ORDER BY cv.id_compania)
          FROM turismo.atractivo_compania ac JOIN turismo.compania_viaje cv USING (id_compania)
         WHERE ac.id_atractivo = a.id_atractivo)            AS publico_recomendado,
       (SELECT im.url FROM turismo.atractivo_imagen im
         WHERE im.id_atractivo = a.id_atractivo AND im.es_principal AND im.tipo = 'normal') AS imagen_principal,
       e.requiere_validacion,
       e.fecha_verificacion,
       a.fecha_corte,
       a.activo,
       (SELECT im.url FROM turismo.atractivo_imagen im
         WHERE im.id_atractivo = a.id_atractivo AND im.es_principal AND im.tipo = '360') AS imagen_360,
       (SELECT coalesce(array_agg(im.url ORDER BY im.orden, im.id_imagen), ARRAY[]::text[])
          FROM turismo.atractivo_imagen im
         WHERE im.id_atractivo = a.id_atractivo AND NOT im.es_principal AND im.tipo = 'normal') AS imagenes_secundarias
FROM turismo.atractivo a
JOIN turismo.subtipo st        ON st.id_subtipo = a.id_subtipo
JOIN turismo.tipo t            ON t.id_tipo = st.id_tipo
JOIN turismo.categoria c       ON c.id_categoria = t.id_categoria
JOIN turismo.distrito d        ON d.ubigeo = a.ubigeo
JOIN turismo.provincia p       ON p.id_provincia = d.id_provincia
JOIN turismo.departamento dp   ON dp.id_departamento = p.id_departamento
JOIN turismo.estado_recurso er ON er.id_estado = a.id_estado
LEFT JOIN turismo.atributo_enriquecido e ON e.id_atractivo = a.id_atractivo
LEFT JOIN turismo.nivel_dificultad nd    ON nd.id_dificultad = e.id_dificultad
LEFT JOIN turismo.nivel_accesibilidad na ON na.id_accesibilidad = e.id_accesibilidad;

CREATE OR REPLACE VIEW turismo.v_catalogo_recomendable AS
SELECT * FROM turismo.v_catalogo WHERE visible_en_ranking AND activo;

COMMIT;
