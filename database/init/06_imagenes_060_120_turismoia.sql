-- ============================================================================
-- 06_imagenes_060_120_turismoia.sql
-- Imágenes normales REC-00060 a REC-00120
-- Fuente: database/TurismoIA_060_120.sql (52 registros)
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
    -- REC-00060 -> id_atractivo=60 (PARQUE RECREACIONAL POZO GRANDE)
    ('REC-00060', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=523434', 'Parque recreacional pozo grande — Soritor', 'normal', TRUE, 1),
    -- REC-00061 -> id_atractivo=61 (CUEVA LA CASCADA)
    ('REC-00061', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=496631', 'Cueva cascada escondida — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00062 -> id_atractivo=62 (MANANTIAL DE SANTA CRUZ)
    ('REC-00062', 'https://lh3.googleusercontent.com/grass-cs/AABkmLerCp3y8hrKL-TF9yVe1XvfyFWiMc-9MOpW9V_lnbINGSmVVoNrreirSn2d-lGDZYE__2wcKewHZxrme8enP8CvkxE6MVaaycRFgCl_6TNPtDSUjFyPKv9xSvcqmks8Iaq7DYG2=s0', 'Manantial de santa cruz — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00063 -> id_atractivo=63 (EL MIRADOR DEL HUALLAGA)
    ('REC-00063', 'https://i.ytimg.com/vi/T-GkGpHL5TQ/maxresdefault.jpg', 'El mirador del huallaga — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00064 -> id_atractivo=64 (CATARATA EL ENCANTO DE LA SANTA)
    ('REC-00064', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589992', 'Catarata el encanto de la santa — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00065 -> id_atractivo=65 (CASCADAS LAS GEMELAS 2)
    ('REC-00065', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRaWs0TGPpUPfHKzhd9f9boKGVEZEJC3GbFM_DdjYUcJ1NlSvtv3BbLqIAV&s=10', 'Cascadas las gemelas 2 — Tocache', 'normal', TRUE, 1),
    -- REC-00067 -> id_atractivo=67 (CASCADA MARIA DE LOS PERFILES)
    ('REC-00067', 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcROp6dp-v3dbHLedupYXDJnK0xgHhVBZ1BDL5dX6i07iNYFquBg', 'Cascada maria de los perfiles — Tocache', 'normal', TRUE, 1),
    -- REC-00070 -> id_atractivo=70 (MIRADOR EL ATARDECER)
    ('REC-00070', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRgegYNLQM3LiNjEid1OOMdKOenOUnN7Wa9VbhIULMOZAwQW2vBCVQpqlU&s=10', 'Mirador el atardecer — Tocache', 'normal', TRUE, 1),
    -- REC-00071 -> id_atractivo=71 (CASA DEL ARTESANO DE RIOJA)
    ('REC-00071', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589851', 'Casa del artesano de rioja — Rioja', 'normal', TRUE, 1),
    -- REC-00072 -> id_atractivo=72 (CUEVA MISTERIOSA)
    ('REC-00072', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=298872', 'Cueva misteriosa — Tocache', 'normal', TRUE, 1),
    -- REC-00073 -> id_atractivo=73 (CUEVA MILAGROSA)
    ('REC-00073', 'https://visitasanmartin.com/wp-content/uploads/2025/06/CUEVA-MILAGROSA-1.webp', 'Cueva milagrosa — Tocache', 'normal', TRUE, 1),
    -- REC-00074 -> id_atractivo=74 (MIRADOR NATURAL DEL GALLINAZO)
    ('REC-00074', 'https://www.turismoperuano.com/wp-content/uploads/mirador-natural-del-gallinazo-san-martin.jpg', 'Mirador natural del gallinazo — Alberto Leveau', 'normal', TRUE, 1),
    -- REC-00075 -> id_atractivo=75 (CASCADA TAYTAYACU)
    ('REC-00075', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=456461', 'Cascada taytayacu — Tarapoto', 'normal', TRUE, 1),
    -- REC-00076 -> id_atractivo=76 (CASCADAS ALTO CANUTO)
    ('REC-00076', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=547971', 'Cascadas alto canuto — Pólvora', 'normal', TRUE, 1),
    -- REC-00077 -> id_atractivo=77 (CASCADAS CHILIA)
    ('REC-00077', 'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQbyyHVi9UI_-RENzd6FRJIUKq5E-zXYOw44VXM8hu9KxWh5vEp', 'Cascadas chilia — Pólvora', 'normal', TRUE, 1),
    -- REC-00078 -> id_atractivo=78 (CANON PULCACHI)
    ('REC-00078', 'https://i.ytimg.com/vi/vTCNfuQd9d4/maxresdefault.jpg', 'Canon pulcachi — Pólvora', 'normal', TRUE, 1),
    -- REC-00079 -> id_atractivo=79 (CASCADAS LAS BRISAS DEL PARAISO)
    ('REC-00079', 'https://i.ytimg.com/vi/jfAyUeuz15g/maxresdefault.jpg', 'Cascadas las brisas del paraiso — Pólvora', 'normal', TRUE, 1),
    -- REC-00081 -> id_atractivo=81 (CASCADA DE TALLIQUIHUI)
    ('REC-00081', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=454604', 'Cascada de talliquihui — Santa Rosa', 'normal', TRUE, 1),
    -- REC-00082 -> id_atractivo=82 (CATARATA DE HUAJA)
    ('REC-00082', 'https://www.turismoperuano.com/wp-content/uploads/catarata-de-huaja-san-martin.jpg', 'Catarata de huaja — San José de Sisa', 'normal', TRUE, 1),
    -- REC-00083 -> id_atractivo=83 (AREA DE CONSERVACION PRIVADA TAMBO ILUSION)
    ('REC-00083', 'https://www.conservamospornaturaleza.org/img/2013/03/IMG_5133.jpg', 'Area de conservacion privada tambo ilusion — La Banda de Shilcayo', 'normal', TRUE, 1),
    -- REC-00084 -> id_atractivo=84 (CASCADAS DE CARPISHUYACU)
    ('REC-00084', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=431710', 'Cascadas de carpishuyacu — La Banda de Shilcayo', 'normal', TRUE, 1),
    -- REC-00085 -> id_atractivo=85 (CANON DE SOLEDAD)
    ('REC-00085', 'https://lens.usercontent.google.com/image?vsrid=CLy_3I7hjOmwpwEQARgBIhDLbDYCT-Z__PYAm3gMW36NMoEBIgJjZygGQnMKLmxmZS1kdW1teTpjZjAzOGMxZC04ODUxLTQ3YmEtOTNiOS0wODM1N2RmNGU3NjUSQQo_L2Jucy9jZy9ib3JnL2NnL2Jucy9sZW5zLWZyb250ZW5kLWFwaS9wcm9kLmxlbnMtZnJvbnRlbmQtYXBpLzMzWgQKAmNnOKiqurHhmZgDUABqCWltYWdlL3BuZw', 'Canon de soledad — Huicungo', 'normal', TRUE, 1),
    -- REC-00086 -> id_atractivo=86 (MANANTIAL EL FONDERO)
    ('REC-00086', 'https://www.turismoperuano.com/wp-content/uploads/manantial-el-fondero-san-martin.jpg', 'Manantial el fondero — Tarapoto', 'normal', TRUE, 1),
    -- REC-00087 -> id_atractivo=87 (MANANTIAL EL ACHUAL)
    ('REC-00087', 'https://www.turismoperuano.com/wp-content/uploads/manantial-el-achual-san-martin.jpg', 'Manantial el achual — Tarapoto', 'normal', TRUE, 1),
    -- REC-00088 -> id_atractivo=88 (RIO UQUIHUA SECTOR EL CHORRO - QUILLOSISA)
    ('REC-00088', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=539626', 'Rio uquihua sector el chorro - quillosisa — Rioja', 'normal', TRUE, 1),
    -- REC-00089 -> id_atractivo=89 (RESERVA ECOLOGICA SANTA ELENA)
    ('REC-00089', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=573912', 'Reserva ecologica santa elena — Posic', 'normal', TRUE, 1),
    -- REC-00090 -> id_atractivo=90 (COMPLEJO ARQUEOLOGICO GUAYAQUIL)
    ('REC-00090', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRn5O9tx-NWYZ8Yc347tnKeK7hazvHKFJAaPNV-UpWYwrCJvRKRHxDJXwiI&s=10', 'Complejo arqueologico guayaquil — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00091 -> id_atractivo=91 (CASCADA TRES MARIAS)
    ('REC-00091', 'https://i0.wp.com/portaldeturismo.pe/wp-content/uploads/2025/06/1182043-whatsapp-image-2025-06-04-at-5-46-30-pm-1.jpeg?fit=900%2C835&ssl=1', 'Cascada tres marias — La Banda de Shilcayo', 'normal', TRUE, 1),
    -- REC-00092 -> id_atractivo=92 (PAUCARPATA SANTUARIO DE AVES)
    ('REC-00092', 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2025/10/05/001212233W.webp', 'Paucarpata santuario de aves — Moyobamba', 'normal', TRUE, 1),
    -- REC-00093 -> id_atractivo=93 (PUERTO NICANOR VELASQUEZ DE TOCACHE)
    ('REC-00093', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=558963', 'Puerto nicanor velasquez de tocache — Tocache', 'normal', TRUE, 1),
    -- REC-00094 -> id_atractivo=94 (FINCA AGROPARK)
    ('REC-00094', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589427', 'Finca agropark — Juanjuí', 'normal', TRUE, 1),
    -- REC-00095 -> id_atractivo=95 (LAGUNA DE LOS ENCANTOS)
    ('REC-00095', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=608647', 'Laguna de los encantos — Campanilla', 'normal', TRUE, 1),
    -- REC-00096 -> id_atractivo=96 (CASCADA DE SHUCSHUYACU)
    ('REC-00096', 'https://www.turismoperuano.com/wp-content/uploads/img_62070d88a6522.jpg', 'Cascada de shucshuyacu — Caynarachi', 'normal', TRUE, 1),
    -- REC-00097 -> id_atractivo=97 (ZONA DE CONSERVACION Y RECUPERACION DE ECOSISTEMAS EL QUINILLAL)
    ('REC-00097', 'https://amazonica.pe/archivos/2022/09/02.jpg', 'Zona de conservacion y recuperacion de ecosistemas el quinillal — Picota', 'normal', TRUE, 1),
    -- REC-00099 -> id_atractivo=99 (MIRADOR DE CHICHA ALTA)
    ('REC-00099', 'https://lens.usercontent.google.com/image?vsrid=CPnGobzN_4ejoAEQARgBIhCPR3kHyV-s0SW-K4k0rElzMoEBIgJjZigKQnMKLmxmZS1kdW1teTpjMzBjZDU2ZS04ZjZiLTRmMTYtYjdkNC1iNmY3YjBkMTIwYjUSQQo_L2Jucy9jZi9ib3JnL2NmL2Jucy9sZW5zLWZyb250ZW5kLWFwaS9wcm9kLmxlbnMtZnJvbnRlbmQtYXBpLzQzWgQKAmNmONDti7vjmZgDUABqCWltYWdlL3BuZw', 'Mirador de chicha alta — Pucacaca', 'normal', TRUE, 1),
    -- REC-00100 -> id_atractivo=100 (PUEBLO PUMAWASI)
    ('REC-00100', 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEg6Bl7RWd0M2Eefp1Ly3p-0hdoHL1kDk_c2g1cmiAU-TFwMSG40YYlzSA11sXm_hjdPALviEMMyDyW_CQJcESq8M98G97HIZxBwWW6jYNeIeDYh4X5aS_eDak7TPcLO8H5xOgHwVLuYnXI/s1600/IMG_1622.JPG', 'Pueblo pumawasi — Picota', 'normal', TRUE, 1),
    -- REC-00101 -> id_atractivo=101 (CENTRO URKU)
    ('REC-00101', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=487684', 'Centro urku — Tarapoto', 'normal', TRUE, 1),
    -- REC-00102 -> id_atractivo=102 (BOSQUE OJOS DE AGUA)
    ('REC-00102', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=493077', 'Bosque ojos de agua — Pucacaca', 'normal', TRUE, 1),
    -- REC-00103 -> id_atractivo=103 (MIRADOR PUCACACA)
    ('REC-00103', 'https://www.turismoperuano.com/wp-content/uploads/Mirador-Pucacaca.webp', 'Mirador pucacaca — Pucacaca', 'normal', TRUE, 1),
    -- REC-00104 -> id_atractivo=104 (LA SANTISIMA CRUZ DE LOS MOTILONES DE LAMAS)
    ('REC-00104', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=483984', 'La santisima cruz de los motilones de lamas — Lamas', 'normal', TRUE, 1),
    -- REC-00105 -> id_atractivo=105 (CATARATAS DE PUCAYAQUILLO)
    ('REC-00105', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=576260', 'Cataratas de pucayaquillo — Shapaja', 'normal', TRUE, 1),
    -- REC-00106 -> id_atractivo=106 (FIESTA RELIGIOSA SANTA ROSA RAYMI)
    ('REC-00106', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=483983', 'Fiesta religiosa santa rosa raymi — Lamas', 'normal', TRUE, 1),
    -- REC-00107 -> id_atractivo=107 (CASCADA DE LAS VELAS)
    ('REC-00107', 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcR4MauRq67NSFLMB3bENcxL56ztr4FfizqR-vcM4y7rmv9ZcDV-', 'Cascada de las velas — Yorongos', 'normal', TRUE, 1),
    -- REC-00108 -> id_atractivo=108 (CASCADA DE YANAYACU)
    ('REC-00108', 'https://www.chullostravelperu.com/blog/wp-content/uploads/2023/05/yanayacu-catarata.jpg', 'Cascada de yanayacu — Moyobamba', 'normal', TRUE, 1),
    -- REC-00111 -> id_atractivo=111 (MIRADOR PINTO RECODO)
    ('REC-00111', 'https://www.turismoperuano.com/wp-content/uploads/mirador-pinto-recodo-san-martin.jpg', 'Mirador pinto recodo — Pinto Recodo', 'normal', TRUE, 1),
    -- REC-00112 -> id_atractivo=112 (FIESTA PATRONAL VIRGEN DE LA NATIVIDAD DE TABALOSOS)
    ('REC-00112', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=645962', 'Fiesta patronal virgen de la natividad de tabalosos — Tabalosos', 'normal', TRUE, 1),
    -- REC-00113 -> id_atractivo=113 (SANTUARIO DE LA VIRGEN DE LA NATIVIDAD DE TABALOSOS)
    ('REC-00113', 'https://portal.andina.pe/EDPFotografia3/thumbnail/2023/08/03/000982062W.jpg', 'Santuario de la virgen de la natividad de tabalosos — Tabalosos', 'normal', TRUE, 1),
    -- REC-00115 -> id_atractivo=115 (CASCADA EL PONGUITO DE CHUMBAQUIHUI)
    ('REC-00115', 'https://i.ytimg.com/vi/rD9nuMXlpqc/maxresdefault.jpg', 'Cascada el ponguito de chumbaquihui — Pinto Recodo', 'normal', TRUE, 1),
    -- REC-00116 -> id_atractivo=116 (CENTRO ARTESANAL WASKA WASKA WARMI WASI)
    ('REC-00116', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=591450', 'Centro artesanal waska waska warmi wasi — Lamas', 'normal', TRUE, 1),
    -- REC-00117 -> id_atractivo=117 (FIESTA PATRONAL SANTO PATRON SANTIAGO)
    ('REC-00117', 'https://portal.andina.pe/EDPFotografia3/thumbnail/2023/06/19/000968109M.jpg', 'Fiesta patronal santo patron santiago — Zapatero', 'normal', TRUE, 1),
    -- REC-00118 -> id_atractivo=118 (CASCADAS DE TOAZAPA)
    ('REC-00118', 'https://radiotropical.pe/wp-content/uploads/2022/02/5f753291-f031-4f74-8c0d-5c9c101ef5fb.jpg', 'Cascadas de toazapa — Barranquita', 'normal', TRUE, 1),
    -- REC-00119 -> id_atractivo=119 (CASCADAS DE YANAYACU)
    ('REC-00119', 'https://s1.wklcdn.com/image_344/10332643/99480197/64776040Master.jpg', 'Cascadas de yanayacu — Barranquita', 'normal', TRUE, 1)
) AS v(codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
JOIN turismo.atractivo a
  ON a.codigo_recurso = v.codigo_recurso
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO NOTHING;

COMMIT;
