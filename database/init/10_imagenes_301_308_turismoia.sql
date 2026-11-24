-- ============================================================================
-- 10_imagenes_301_308_turismoia.sql
-- Imágenes normales REC-00301 a REC-00308 (resuelto por codigo_recurso)
-- Fuente: database/TurismoIA_301_308.sql (8 registros)
-- Nota: Resuelve id_atractivo mediante codigo_recurso para evitar desfase por REC-00226 ausente.
-- ============================================================================
BEGIN;

INSERT INTO turismo.atractivo_imagen
    (id_atractivo, url, texto_alternativo, tipo, es_principal, orden)
SELECT
    a.id_atractivo,
    v.url,
    v.texto_alternativo,
    v.tipo,
    v.es_principal,
    v.orden
FROM (VALUES
    -- REC-00301 -> id_atractivo=300 (FESTIVAL DEL MIJANO)
    ('REC-00301', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSX2JqAJ2QtdsruKFpma4nYMupNE-c50Kt5dR7RkaWwS73z9Yoirbe-VVo&s=10', 'Festival del mijano — Picota', 'normal', TRUE, 1),
    -- REC-00302 -> id_atractivo=301 (PLAZA DE ARMAS DE PICOTA)
    ('REC-00302', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyBjbTc7IPvrP94B2aoMzq8yU5eLWWNkqevxH5uY15Ji30dJQecgwa-ZA&s=10', 'Plaza de armas de picota — Picota', 'normal', TRUE, 1),
    -- REC-00303 -> id_atractivo=302 (ANIVERSARIO DE FUNDACION POLITICA DE PICOTA)
    ('REC-00303', 'https://www.selvaexploraperu.com/img/14186/6.jpg', 'Aniversario de fundacion politica de picota — Picota', 'normal', TRUE, 1),
    -- REC-00304 -> id_atractivo=303 (EMBARCADERO TURISTICO DEL PUERTO CALLAO DE HUICUNGO)
    ('REC-00304', 'https://www.selvaexploraperu.com/img/14411/0.webp', 'Embarcadero turistico del puerto callao de huicungo — Huicungo', 'normal', TRUE, 1),
    -- REC-00305 -> id_atractivo=304 (PLAZA DE ARMAS DE MOYOBAMBA)
    ('REC-00305', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQtIjC1Bf9q3k3cLeF34vQXfokQDRT6giIovA8uk7rIP_1Kmzj1DRsPd24&s=10', 'Plaza de armas de moyobamba — Moyobamba', 'normal', TRUE, 1),
    -- REC-00306 -> id_atractivo=305 (CHACRA PASIKIWI)
    ('REC-00306', 'https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2a/25/b0/8b/ruta-agroecoturistica.jpg?w=900&h=500&s=1', 'Chacra pasikiwi — Chazuta', 'normal', TRUE, 1),
    -- REC-00307 -> id_atractivo=306 (RIO SAJINERO)
    ('REC-00307', 'https://i.ytimg.com/vi/FgiKSj4Tjdg/maxresdefault.jpg', 'Rio sajinero — Tocache', 'normal', TRUE, 1),
    -- REC-00308 -> id_atractivo=307 (MELIPONARIO DON MARIO)
    ('REC-00308', 'https://visitasanmartin.com/wp-content/uploads/2026/10/Meliponario-Don-Mario.webp', 'Meliponario don mario — Elias Soplin Vargas', 'normal', TRUE, 1)
) AS v(codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
JOIN turismo.atractivo a
  ON a.codigo_recurso = v.codigo_recurso
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO NOTHING;

COMMIT;
