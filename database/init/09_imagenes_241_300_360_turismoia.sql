-- ============================================================================
-- 09_imagenes_241_300_360_turismoia.sql
-- Panoramas 360° REC-00257 a REC-00296 (resuelto por codigo_recurso)
-- Fuente: database/TurismoIA_241_300_360.sql (12 registros)
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
    -- REC-00257 -> id_atractivo=256 (EMBARCADERO TURISTICO DE TAHUISHCO)
    ('REC-00257', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U9Di1Guh3ug0mbXMflnrIprfqEGBSPvVBqpgoDGzIE4krnAoZddO91DWqSEq02S5QHbk_Av2ZYa80MGqNMe80qGFQkNfwLMap24nklYTHn7bFZnsX6otxslolhF7bOCPvkrPOdU=w4096-h2048-k-no', 'Vista 360° Embarcadero Turistico De Tahuishco. Vista desde la plataforma techada del embarcadero, con río y entorno.', '360', TRUE, 1),
    -- REC-00261 -> id_atractivo=260 (AGUAS TERMALES Y SULFUROSAS DE JEPELACIO)
    ('REC-00261', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_U5Q71Q1-Jp5erCl3ZXEDpBJAS40envaF9vCoTgo0tFAnXvxma0AkD9HgJBeGHSH0uVZYQHM2GxceZRvWb0sDGgJIe66GdynNffmnCUrc6dJGHNsWVufzsYVcUMqEz90ZNjgBldw=w4096-h2048-k-no', 'Vista 360° Aguas Termales Y Sulfurosas De Jepelacio. Vista aérea del complejo de aguas sulfurosas y su entorno natural; no es una toma a nivel de las pozas.', '360', TRUE, 1),
    -- REC-00268 -> id_atractivo=267 (MIRADOR PUNTA DE TAHUISHCO)
    ('REC-00268', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-o2n4NV3uQsDENWZC9riSKJ_OM_IOsWjQZXsJnWL2qvzoSIauFU7J6X34pHQlG7nqfjUptU2H5VR8fej2c_jYwUKiA-_YjzsRTLYgm6HKEvS18ADHza-8m7xk-vHwb2iF4JyEG=w4096-h2048-k-no', 'Vista 360° Mirador Punta De Tahuishco. Escalinata y plataforma del mirador; no ofrece una vista despejada de todo el valle.', '360', TRUE, 1),
    -- REC-00269 -> id_atractivo=268 (MIRADOR PUNTA DE SAN JUAN)
    ('REC-00269', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-XIt0MS9r6pwyI8IBZCKdCVRM0uoiaQ1AeEo_FN8OU-ZlT9A6EzRtYcYx5tOPbTbnKD0PEddaxmwtK2_xKn5ucJ-sWhkguZCIfx68BGQywN35ccBBUCQWp3uvlHKK0jW_dAjk=w4096-h2048-k-no', 'Vista 360° Mirador Punta De San Juan. Escalinatas y jardines del mirador Punta de San Juan.', '360', TRUE, 1),
    -- REC-00274 -> id_atractivo=273 (AGUAS TERMALES SAN MATEO)
    ('REC-00274', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_g6-9Kp2MNMnbpFv8RglbGQhEfQLpCahJ2Iv1ILo4XxrlLyLDJP6E3ddNgskqeS1Fd4nTK8E81p5JqQUQ9g4jCSwjTJw1QaXh_tdoLclHC1tddFt4A86WwFt_mK16kR5fKu5Bb9JFRvlJ_=w4096-h2048-k-no', 'Vista 360° Aguas Termales San Mateo. Vista aérea del entorno de San Mateo; instalaciones en la parte inferior de la esfera.', '360', TRUE, 1),
    -- REC-00275 -> id_atractivo=274 (MORRO DE CALZADA)
    ('REC-00275', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_hPyrAQJBEMu9nc-6WI0WY1Zt1ccc07xkn4yqxxPUfj2B2r5YZaQR8tRth4uEqv4TVbx7fwGrvSCBkaKzpjW10MwIdFC1rBltO2HqaPrcTu3Re1ihB6cNucEikuiA1fO7F1Gye=w4096-h2048-k-no', 'Vista 360° Morro De Calzada. Cumbre y paisaje circundante desde el Morro de Calzada.', '360', TRUE, 1),
    -- REC-00276 -> id_atractivo=275 (CATARATAS DE AHUASHIYACU)
    ('REC-00276', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U8arAQosQSv_iTwx273DOMKOd_MZ8OeYS2OSF-1TMi2rb_zSRXp0fn_Vs2gl-Dy-wCDdyvrRPeh7oBUP7Tk8IYzXfXC7QmLk0ayuTa2Ktsji8VTUvXPSCHb0LnSJdczhoGcWTGuCg=w4096-h2048-k-no', 'Vista 360° Cataratas De Ahuashiyacu. Catarata, cauce, vegetación y zona de visitantes de Ahuashiyacu.', '360', TRUE, 1),
    -- REC-00285 -> id_atractivo=284 (PLAZA DE ARMAS DE RIOJA)
    ('REC-00285', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_9u4y3IcnziOwPfEZnHYl-OqrND-g6xxTKw0sukWindS-7VXGywXgGYWjnnuDkirEVnsf_6NnFx87eHKJ978M5W19szOr36aPerCcruA-hctEEXszQqDRygvMH6MuQtgqa0lzqG9jgBKNy=w4096-h2048-k-no', 'Vista 360° Plaza De Armas De Rioja. Vista de la plaza, fuente y jardines; puede reflejar una configuración anterior de la plaza.', '360', TRUE, 1),
    -- REC-00288 -> id_atractivo=287 (PUENTE COCOCHO)
    ('REC-00288', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U9l4to_xkm2EwQXpX9t7K0D6vd2AxMP5GPLjiC-KpS7F9LR5HrTZd3sBz8Z9W-XY7OuDHwqRfelUGbfotwaNimaZ7hnx8dT9AHDheuJo0kzwlxLtcJddHkmc_YYC3lmL7ERnk-OAw=w4096-h2048-k-no', 'Vista 360° Puente Cococho. Acceso y estructura del puente peatonal Cococho.', '360', TRUE, 1),
    -- REC-00290 -> id_atractivo=289 (PLAZUELA SAN MARTIN - MOYOBAMBA)
    ('REC-00290', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U87MaB4CEWJy-uS-g_2TLJ2HAkx2HqtW711uqdJpTcCYxLaAyBB5ZJNtSArqqIo79hsU86UVyU8OytT8K8-S5ZZ5Wjyp0t7sfspu236jSkydl8m58PDPxpX_XsKF13v0T9Hsw=w4096-h2048-k-no', 'Vista 360° Plazuela San Martin - Moyobamba. Vista nocturna de la plazuela y su iglesia.', '360', TRUE, 1),
    -- REC-00291 -> id_atractivo=290 (PLAZUELA BOLOGNESI)
    ('REC-00291', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-1thHdBjiSU_KjA1abbkC3IHGn5is0J10yh3goEwYjJW0UJ5mTt2LXdzgL-6RH6FGvCqejuiG6IiSvkQjC8S-8U1NdD7Fw9MK1FSndjwVLVOmZKXu_U71zYsjjDdJYk0AH_dCk=w4096-h2048-k-no', 'Vista 360° Plazuela Bolognesi. Vista general de la plazuela, árboles y calles que la rodean.', '360', TRUE, 1),
    -- REC-00296 -> id_atractivo=295 (PUEBLO DE LAMAS)
    ('REC-00296', 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-V_o6ANbl2Tn5C9q4SRsAGvMpXk9nsPTsRl-rxGUOLpmENfRClfwFpZGfHzmpyyuryopMtDRabXX3GfSgvId6SPzKDuRkzHQmEwCkPNEESJL-4HcSllHMTuvg0oquDnukKJlng0g=w4096-h2048-k-no', 'Vista 360° Pueblo De Lamas. Plaza central de Lamas y edificios circundantes.', '360', TRUE, 1)
) AS v(codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
JOIN turismo.atractivo a
  ON a.codigo_recurso = v.codigo_recurso
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO NOTHING;

COMMIT;
