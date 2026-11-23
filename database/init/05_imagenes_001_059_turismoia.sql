-- ============================================================================
-- 05_imagenes_001_059_turismoia.sql
-- Imágenes normales REC-00001 a REC-00059 (omite placeholder REC-00057)
-- Fuente: database/imagenes_1_a_59_placeholders.sql (58 registros)
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
    -- REC-00001 -> id_atractivo=1 (TEMPLO VIRGEN DE LA MERCED)
    ('REC-00001', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSMuRqxpWs3qt6QibYw6ZYtKABDdw5ozMjcy8nzAfEG4Q&s=10', 'Templo virgen de la merced — Juanjui', 'normal', TRUE, 1),
    -- REC-00002 -> id_atractivo=2 (ALAMEDA TURISTICA DE JUANJUI)
    ('REC-00002', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTRNpLVxXBacMMJfFCKK9eoNLbo4cNGLItTdiZ9V1GXdA&s=10', 'Alameda turistica de juanjui — Juanjui', 'normal', TRUE, 1),
    -- REC-00003 -> id_atractivo=3 (GALERIA FOTOGRAFICA SO2 JORGE LEON LINARES)
    ('REC-00003', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPwMWdr-qQPEJD3p59k18NNS8krUPkWDt6pmqpDTqARIwtTm3IAC9X1gk&s=10', 'Galeria fotografica jorge leon linares — Huicungo', 'normal', TRUE, 1),
    -- REC-00004 -> id_atractivo=4 (RODALES DE MANCHINGA)
    ('REC-00004', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT0rzpo7NfL_hgWwUjBJm07H5A_uQKmwCZwRHe7XWBl3k6PI3XUsK3eXxZk&s=10', 'Rodales de manchinga — San Pablo', 'normal', TRUE, 1),
    -- REC-00005 -> id_atractivo=5 (BOULEVARD TURISTICO QUILLOSISA)
    ('REC-00005', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRS9OjW0x6gQL0K_S8-NsuWhOxcBRdT5zaFnxeOk-A92xyX5mPWZ2glwzQ&s=10', 'Boulevard turistico quillosisa — Rioja', 'normal', TRUE, 1),
    -- REC-00006 -> id_atractivo=6 (CASCADA LAGUNAS GEMELAS DE SACANCHE)
    ('REC-00006', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzC2qgPGVYQP1FXLjoL8cETrxdKf7b9feOeTs_WoLj3A&s=10', 'Cascada lagunas gemelas de sacanche — Sacanche', 'normal', TRUE, 1),
    -- REC-00007 -> id_atractivo=7 (COMUNIDAD SALUDABLE MIGUEL GRAU)
    ('REC-00007', 'https://tarapoto.com/wp-content/uploads/2020/06/crianza-de-plantas-1024x683.jpg', 'Comunidad saludable miguel grau — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00008 -> id_atractivo=8 (RIO AGUAS CLARAS)
    ('REC-00008', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFfOylbuHueRS4__qGKs4E73ryDnhk9IA_n0HlLU3NaDNoZu4PSw8oIPY&s=10', 'Rio aguas claras — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00009 -> id_atractivo=9 (SENDERO ROYAL SUNANGEL)
    ('REC-00009', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=443364', 'Sendero royal sunangel — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00010 -> id_atractivo=10 (CASCADAS DE PROGRESO - LA BANDA DE SHILCAYO)
    ('REC-00010', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSkNow41sb5-ndvS2dQXpIib79DKQZImCcvWMnBsAig_g&s=10', 'Cascadas de progreso — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00011 -> id_atractivo=11 (CASCADAS LAGRIMAS DE LA NOVIA)
    ('REC-00011', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTboCQwlQ0k5DwWxTy44ygeXZ0Jc8bGOJtOeuIFpIfqvLPnm6j2JIM-MnI&s=10', 'Cascadas lagrimas de la novia — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00012 -> id_atractivo=12 (EL AGUAJAL LAGUNA EL DOREO)
    ('REC-00012', 'https://d1vv3l16eo9v1l.cloudfront.net/turismo/11135/424136.jpg', 'El aguajal laguna el doreo — Habana', 'normal', TRUE, 1),
    -- REC-00013 -> id_atractivo=13 (CASCADA CHORROS CALIENTES)
    ('REC-00013', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzLwFm-jhSjBSxoI-3v2YYHWtleI_5ac_KCeeeFGNU0Q&s=10', 'Cascada chorros calientes — Soritor', 'normal', TRUE, 1),
    -- REC-00014 -> id_atractivo=14 (MIRADOR TURISTICO JUAN HUIDO)
    ('REC-00014', 'https://www.selvaexploraperu.com/img/11104/0.webp', 'Mirador turistico juan huido — Juanjui', 'normal', TRUE, 1),
    -- REC-00015 -> id_atractivo=15 (JARDIN ZOOBOTANICO AMAZONIA)
    ('REC-00015', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqLCakk-PFAkyOxM8uY9S1AZdv5X0EpksxoDRNWLA90vGFDkAIRYBTw5wz&s=10', 'Jardin zoobotanico amazonia — Moyobamba', 'normal', TRUE, 1),
    -- REC-00016 -> id_atractivo=16 (CASCADAS PUCAYACU)
    ('REC-00016', 'https://media-cdn.tripadvisor.com/media/photo-s/1d/da/97/35/cataratas-de-pucayacu.jpg', 'Cascadas pucayacu — Sauce', 'normal', TRUE, 1),
    -- REC-00017 -> id_atractivo=17 (CATARATA SHIHUI)
    ('REC-00017', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT0Sni3fYf_sCcvigwuOHGWebhpz5AiZhdtwgznylTC-w_r_62RHzDnooRP&s=10', 'Catarata shihui — Huicungo', 'normal', TRUE, 1),
    -- REC-00018 -> id_atractivo=18 (CERRO TAMBURCO)
    ('REC-00018', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRX0sKjKLvrGMpqkctQOfCb_rKef3cXctBpdQkhRrC8wCvnpXWio40fwo7L&s=10', 'Cerro tamburco — Rioja', 'normal', TRUE, 1),
    -- REC-00019 -> id_atractivo=19 (LLANTERIA BIRD´S)
    ('REC-00019', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSD-5vfCjjSQwP9zKSclsaTvlJACWYYdUBH4lndRnzPcQ&s=10', 'Llanteria birds — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00020 -> id_atractivo=20 (CUEVA CASCADA ESCONDIDA)
    ('REC-00020', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRB0MoeHK-hP2-U6WKE-NOapOAxwHV5ffpoZmkwgGIFUD4PiXKxv8FZPs8&s=10', 'Cueva cascada escondida — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00021 -> id_atractivo=21 (CASCADA URKUCHAKI)
    ('REC-00021', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTCYjfkKVf9XwmhR2-HxsPcFjeSM9bhzL4xy5nmPGcBIKQLS5_lbLrLjGGM&s=10', 'Cascada urkuchaki — Elias Soplin Vargas', 'normal', TRUE, 1),
    -- REC-00022 -> id_atractivo=22 (MIRADOR EL MONO Y LA GATA)
    ('REC-00022', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSVyC_K1rPobJZLGr3jWjc9n2LSFP7X6NPpZDGQRclQDtBsMVM92mqfa54&s=10', 'Mirador el mono y la gata — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00023 -> id_atractivo=23 (FUNDO ALTO NIEVA - RIOJA)
    ('REC-00023', 'https://turismo.munirioja.gob.pe/img/Recursos%20Turisticos/tur15/foto.png', 'Fundo alto nieva - rioja — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00024 -> id_atractivo=24 (RESERVA PRIVADA ACONABIKH)
    ('REC-00024', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMKmBCAYP8CV6UibX8m_mMlrVAAbJamggWw4xpTrpCjbjd83k8h74oBJw&s=10', 'Reserva privada aconabikh — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00025 -> id_atractivo=25 (CASCADA LLUVIA PERPETUA)
    ('REC-00025', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSKNZ6e3nzVE_uIs-VIexqbQh4K8Csx71-h5Xu4hHyv3yRpVAaPVGmPAFqO&s=10', 'Cascada lluvia perpetua — Soritor', 'normal', TRUE, 1),
    -- REC-00026 -> id_atractivo=26 (CASCADA PISCINA DE LOS REYES)
    ('REC-00026', 'https://visitasanmartin.com/wp-content/uploads/2025/06/DJI_0586-1024x682.jpg', 'Cascada piscina de los reyes — Soritor', 'normal', TRUE, 1),
    -- REC-00027 -> id_atractivo=27 (MIRADOR DEL RIO TIOYACU)
    ('REC-00027', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQuglGtkk25WQkJyGVPxCFqU4NPxHQV8p9sxOG7u-iFtLmed8u2plscadLi&s=10', 'Mirador del rio tioyacu — Elias Soplin Vargas', 'normal', TRUE, 1),
    -- REC-00028 -> id_atractivo=28 (BOSQUE DE LAS NUWAS)
    ('REC-00028', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT4jy3gZdAhjyYK3o_1xA_8W8i8YLcVwa2p_BdqiQbybBTzzp2HUPaL5pH1&s=10', 'Bosque de las nuwas — Awajun', 'normal', TRUE, 1),
    -- REC-00029 -> id_atractivo=29 (LA ENCANADA DE YORONGOS)
    ('REC-00029', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-0MuMRS3aiTtlYnNbgN8jpNcHHpSq2Q2OcwWYsZVTXYfbXrNCKFN-2zrq&s=10', 'La encanada de yorongos — Yorongos', 'normal', TRUE, 1),
    -- REC-00030 -> id_atractivo=30 (MELIPONARIO YANTALO)
    ('REC-00030', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQiRpJl7qslexPdGeimMHRere96CofdOkPTO9fN2wJ03hWgCAMVDWI9Sq1N&s=10', 'Meliponario yantalo — Yantalo', 'normal', TRUE, 1),
    -- REC-00031 -> id_atractivo=31 (SENDERO QUISCARRUMI)
    ('REC-00031', 'https://www.selvaexploraperu.com/img/12118/0.webp', 'Sendero quiscarrumi — Jepelacio', 'normal', TRUE, 1),
    -- REC-00032 -> id_atractivo=32 (RESERVA ARENA BLANCA - RIOJA)
    ('REC-00032', 'https://portal.andina.pe/EDPFotografia3/thumbnail/2021/09/07/000805526M.jpg', 'Reserva arena blanca - rioja — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00033 -> id_atractivo=33 (LAGUNA RICURICOCHA)
    ('REC-00033', 'https://d2j6dbq0eux0bg.cloudfront.net/images/76631593/4338085257.jpg', 'Laguna ricuricocha — Tarapoto', 'normal', TRUE, 1),
    -- REC-00034 -> id_atractivo=34 (CASCADA GALINDONA)
    ('REC-00034', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLVqKk4WzjTX_72eGsFlfPJkhxx3bVuCHoN8zvXTD2qJBAZlGkrcWFDuVL&s=10', 'Cascada galindona — Pinto Recodo', 'normal', TRUE, 1),
    -- REC-00035 -> id_atractivo=35 (PLAYA DE LAS MARIPOSAS)
    ('REC-00035', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5Wf6nPPjH8Wk0rfPKgNwaNAxo3rg_g0GvPOvSf0kWLlBd306MUzJWqbE&s=10', 'Playa de las mariposas — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00036 -> id_atractivo=36 (CATARATAS DEL GERA)
    ('REC-00036', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQATqKijucUzQevcP_k4AErDJv1bLtPpDa7Xzp3zXH4oKVhkb_r2BhQ0tfR&s=10', 'Cataratas del gera — Jepelacio', 'normal', TRUE, 1),
    -- REC-00037 -> id_atractivo=37 (CENTRO CULTURAL JOICY V. BARTRA)
    ('REC-00037', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS38fh_8WUR4sW71DvYSsTdCIpQmSmOSRvN2BVw45rS1g4mdWlc4P6oK-I&s=10', 'Centro cultural joicy v. bartra — Chazuta', 'normal', TRUE, 1),
    -- REC-00038 -> id_atractivo=38 (LAGUNA ATUNCOCHA)
    ('REC-00038', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRo2PGq6edOL_djZ68kHmR_WpfNGVPFw6RN1fd9sC-cR3jI7pGnbFbxX3iA&s=10', 'Laguna atuncocha — Papaplaya', 'normal', TRUE, 1),
    -- REC-00039 -> id_atractivo=39 (LAGUNA PAPACOCHA)
    ('REC-00039', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRZU8I_Zm4kWOCLwk0XxWBRsBq_NBdBthZbyFyyEShJyvER5-_sWkPkUzFT&s=10', 'Laguna papacocha — Papaplaya', 'normal', TRUE, 1),
    -- REC-00040 -> id_atractivo=40 (ZONA DE CONSERVACION Y RECUPERACION DE ECOSISTEMAS HUMEDAL DEL ALTO MAYO SECTOR LLOROS)
    ('REC-00040', 'https://www.selvaexploraperu.com/img/12777/0.jpg', 'Zona de conservacion y recuperacion de ecosistemas humedal del alto mayo sector lloros — Yuracyacu', 'normal', TRUE, 1),
    -- REC-00041 -> id_atractivo=41 (MARIPOSARIO MORPHO AZUL)
    ('REC-00041', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqRNf7msANzShQc60vfmV3n3c-nKZD_QXzsKNuQvUy6hz_zCzmkc6cJTNq&s=10', 'Mariposario morpho azul — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00042 -> id_atractivo=42 (CERAMICA DE CHAZUTA)
    ('REC-00042', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLlrmC8ekzuvGh_yyllcGiZs7RAQDM0VcJv5qUKc3QjGAfk25Zj8CwYLqh&s=10', 'Ceramica de chazuta — Chazuta', 'normal', TRUE, 1),
    -- REC-00043 -> id_atractivo=43 (MISKY CACAO)
    ('REC-00043', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS-OjSZ1s_y0fNK3LabctcjdO38U1LFyv8XsSVx2q4L4q6m64XmF9S3Q_Y&s=10', 'Misky cacao — Chazuta', 'normal', TRUE, 1),
    -- REC-00044 -> id_atractivo=44 (CASCADA VELO DE NOVIA)
    ('REC-00044', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSd2xu9NyLu1O4lC30JWzWiUNpHNc6LONzLXrfdj8HoDfEOnx6yQZZw5ZA&s=10', 'Cascada velo de novia — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00045 -> id_atractivo=45 (CASCADA DE CHIRAPILLO)
    ('REC-00045', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvxT-zqZhptB-HYKka6qSgZR5r5cz_0QAt8yyHloehqw&s=10', 'Cascada de chirapillo — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00046 -> id_atractivo=46 (CATARATA DE SISAYACU)
    ('REC-00046', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRdzjGfpab-kZzwV3LH_vzj9rOWYmQMX7vTktv3F004wXaE02ahRZ0SbgE&s=10', 'Catarata de sisayacu — Caynarachi', 'normal', TRUE, 1),
    -- REC-00047 -> id_atractivo=47 (CASCADA DE SABALOYACU 02)
    ('REC-00047', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRrntLtRsDsV4TAuNMstAe8dyA7navC2i_qTs4OWVfvOg&s=10', 'Cascada de sabaloyacu 02 — Caynarachi', 'normal', TRUE, 1),
    -- REC-00048 -> id_atractivo=48 (FIESTA TRADICIONAL DE SAN JUAN GRANDE Y SAN JUAN CHICO DE SORITOR)
    ('REC-00048', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYaAVRfClHn5QHm40syHzlNoOaWGFPnpR1nidp_ifeZGLbQOqS__R1M_l4&s=10', 'Fiesta tradicional de san juan grande y san juan chico — Soritor', 'normal', TRUE, 1),
    -- REC-00049 -> id_atractivo=49 (ANIVERSARIO DE FUNDACION POLITICA DE SORITOR)
    ('REC-00049', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSC5k8VP1QWW3cavYkSBSYQtQqVVq6FLyv1DIKTVFUNUOuuYtX7ZSPwpl8&s=10', 'Aniversario de fundacion politica — Soritor', 'normal', TRUE, 1),
    -- REC-00050 -> id_atractivo=50 (CONFITE DE MANI SORITORINO)
    ('REC-00050', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSyWofIYn5dvEoWpre8O2ViseMqEzNnUZqbTYTt5AyaE1heFH6OgCekZPia&s=10', 'Confite de mani soritorino — Soritor', 'normal', TRUE, 1),
    -- REC-00051 -> id_atractivo=51 (CASCADA DE SABALOYACU 01)
    ('REC-00051', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXLisyD-AYRAORNKFTfxipRtS7VFxfMCUrwgzzNAY9aypVDdOdx66itIo&s=10', 'Cascada de sabaloyacu 01 — Caynarachi', 'normal', TRUE, 1),
    -- REC-00052 -> id_atractivo=52 (MUSEO ETNOGRAFICO TOE)
    ('REC-00052', 'https://visitasanmartin.com/wp-content/uploads/2025/06/Museo-Toe.jpg', 'Museo etnografico toe — Rioja', 'normal', TRUE, 1),
    -- REC-00053 -> id_atractivo=53 (CENTRO CULTURAL WASICHAY)
    ('REC-00053', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmLQMUrGhU4izHsUH9rlbVdcJvIIe-YaH9IXXfqnc0LJsE1JltiHkJGhs&s=10', 'Centro cultural wasichay — Chazuta', 'normal', TRUE, 1),
    -- REC-00054 -> id_atractivo=54 (CASCADA AGUAS CALIENTES)
    ('REC-00054', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRI6rasZUTbriYVEVdTLgAh6lUj4i3bIv3qeYbSxu5_dxrX1BmP8heq1A_Y&s=10', 'Cascada aguas calientes — Soritor', 'normal', TRUE, 1),
    -- REC-00055 -> id_atractivo=55 (SENDERO EL CANTO DEL BOSQUE)
    ('REC-00055', 'https://visitasanmartin.com/wp-content/uploads/2025/06/420171364_695054039477563_2551336660000851398_n.jpg', 'Sendero el canto del bosque — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00056 -> id_atractivo=56 (MIRADOR TURISTICO DEL BOSQUE DE PROTECCION ALTO MAYO)
    ('REC-00056', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQiCMxOYRlvP2QFg2lGfiHSJcWcbtb8-1JRqvadJTX5TA&s=10', 'Mirador turistico del bosque de proteccion alto mayo — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00058 -> id_atractivo=58 (CENTRO DE PRODUCCION DE CACAO Y DERIVADOS DE NUEVA BAMBAMARCA)
    ('REC-00058', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS_Tifs0MwDqCqTK-3BSLPgdSYwQdpOI28AonLRPY3kYV5Nh3wevKeesK4u&s=10', 'Centro de produccion de cacao y derivados de nueva bambamarca — Tocache', 'normal', TRUE, 1),
    -- REC-00059 -> id_atractivo=59 (MALECON GERMAN ALIAGA)
    ('REC-00059', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTqDBGfsJbIlJSfig7FB-sn-oXFz9qM-8PL9pTp9PwjxolTn5bLBh49kMMu&s=10', 'Malecon german aliaga — Tocache', 'normal', TRUE, 1)
) AS v(codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
JOIN turismo.atractivo a
  ON a.codigo_recurso = v.codigo_recurso
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO NOTHING;

COMMIT;
