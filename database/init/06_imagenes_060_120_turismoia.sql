-- ============================================================================
-- 06_imagenes_060_120_turismoia.sql
-- Imágenes normales REC-00060 a REC-00120 (y corrección REC-00020)
-- Actualizado desde actualizadas de 60 a 120.sql:
--   * 40 atractivos actualizados (40 principales + 26 secundarias = 66 filas).
--   * 12 atractivos pendientes de reemplazo conservan su enlace previo
--     (REC-00065, 00067, 00070, 00077, 00085, 00090, 00091, 00097, 00099,
--     00107, 00117, 00119).
-- Notas:
--   * En el catálogo verificado (02_datos_turismoia.sql), 'Cueva Cascada
--     Escondida' (Nueva Cajamarca, 220804) corresponde a REC-00020; el previo
--     mapeo erróneo sobre REC-00061 ('Cueva La Cascada', Tocache) se limpia.
--   * Enlaces de Google Drive normalizados a URL directa de imagen:
--     https://lh3.googleusercontent.com/d/<ID>=w1600
-- ============================================================================
BEGIN;
SET LOCAL standard_conforming_strings = on;

CREATE TEMP TABLE tmp_imagenes_060_120 (
    codigo_recurso    text     NOT NULL,
    url               text     NOT NULL,
    texto_alternativo text     NOT NULL,
    tipo              text     NOT NULL,
    es_principal      boolean  NOT NULL,
    orden             smallint NOT NULL
) ON COMMIT DROP;

INSERT INTO tmp_imagenes_060_120
    (codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
VALUES
    -- REC-00060 · PARQUE RECREACIONAL POZO GRANDE
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=12755
    ('REC-00060', 'https://lh3.googleusercontent.com/d/1N4upRuCg3CLWriB339v0rjb0xLvqIhO3=w1600', 'Parque recreacional pozo grande — Soritor', 'normal', TRUE, 1),
    ('REC-00060', 'https://lh3.googleusercontent.com/d/1QUfTsmsjDwdWlhcFmtQQ3VLdRy7p1Pfj=w1600', 'Parque recreacional pozo grande — Soritor', 'normal', FALSE, 2),
    -- REC-00061 · CUEVA CASCADA ESCONDIDA
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=12478
    -- La Cueva Cascada Escondida de Nueva Cajamarca figura en el catálogo como REC-00020.
    ('REC-00020', 'https://lh3.googleusercontent.com/d/1DdZk7YtQzLeq0cOqjO8Mu0VZwv5hh-lE=w1600', 'Cueva cascada escondida — Nueva Cajamarca', 'normal', TRUE, 1),
    ('REC-00020', 'https://lh3.googleusercontent.com/d/1lZg3FkXGgAxzN4qy4Z__Yw6y2HK6cd2R=w1600', 'Cueva cascada escondida — Nueva Cajamarca', 'normal', FALSE, 2),
    -- REC-00062 · MANANTIAL DE SANTA CRUZ
    -- Fuente consultada https://www.google.com/maps/place/VILLA+MANANTIAL+-+Recreo+tur%C3%ADstico+de+Santa+Cruz,+Nuevo+Progreso+-+Tocache/@-8.5618037,-76.2810219,17z/data=!3m1!4b1!4m6!3m5!1s0x91a58d8ad22fa509:0xc7a2e31c9e5ce87b!8m2!3d-8.5618037!4d-76.2810219!16s%2Fg%2F11rg4v5svn
    ('REC-00062', 'https://lh3.googleusercontent.com/d/1CHEWU_BxGikNzZ6VXf7WHfDLmq6SlRzA=w1600', 'Manantial de santa cruz — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00063 · EL MIRADOR DEL HUALLAGA
    -- Fuente consultada https://www.youtube.com/watch?v=T-GkGpHL5TQ
    ('REC-00063', 'https://lh3.googleusercontent.com/d/10jvQsU4LXi7J9-pBjsrAhX2gWMyR_SV3=w1600', 'El mirador del huallaga — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00064 · CATARATA EL ENCANTO DE LA SANTA
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=3966
    ('REC-00064', 'https://lh3.googleusercontent.com/d/1BR8Xk4NRoyv2GVK4GiZfa_7k5y8yzi25=w1600', 'Catarata el encanto de la santa — Nuevo Progreso', 'normal', TRUE, 1),
    ('REC-00064', 'https://lh3.googleusercontent.com/d/1NJd9BdERFhD0bgGqbOGHVSEsJPqZQt0P=w1600', 'Catarata el encanto de la santa — Nuevo Progreso', 'normal', FALSE, 2),
    -- REC-00065 (CASCADAS LAS GEMELAS 2) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00065', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRaWs0TGPpUPfHKzhd9f9boKGVEZEJC3GbFM_DdjYUcJ1NlSvtv3BbLqIAV&s=10', 'Cascadas las gemelas 2 — Tocache', 'normal', TRUE, 1),
    -- REC-00067 (CASCADA MARIA DE LOS PERFILES) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00067', 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcROp6dp-v3dbHLedupYXDJnK0xgHhVBZ1BDL5dX6i07iNYFquBg', 'Cascada maria de los perfiles — Tocache', 'normal', TRUE, 1),
    -- REC-00070 (MIRADOR EL ATARDECER) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00070', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRgegYNLQM3LiNjEid1OOMdKOenOUnN7Wa9VbhIULMOZAwQW2vBCVQpqlU&s=10', 'Mirador el atardecer — Tocache', 'normal', TRUE, 1),
    -- REC-00071 · CASA DEL ARTESANO DE RIOJA
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=12758
    ('REC-00071', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589851', 'Casa del artesano de rioja — Rioja', 'normal', TRUE, 1),
    ('REC-00071', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589886', 'Casa del artesano de rioja — Rioja', 'normal', FALSE, 2),
    -- REC-00072 · CUEVA MISTERIOSA
    -- Fuente consultada https://visitasanmartin.com/sitio/cueva-misteriosa/
    ('REC-00072', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=298872', 'Cueva misteriosa — Tocache', 'normal', TRUE, 1),
    ('REC-00072', 'https://visitasanmartin.com/wp-content/uploads/2025/06/CUEVA-MISTERIOSA.webp', 'Cueva misteriosa — Tocache', 'normal', FALSE, 2),
    -- REC-00073 · CUEVA MILAGROSA
    -- Fuente consultada https://visitasanmartin.com/sitio/cueva-milagrosa/
    ('REC-00073', 'https://lh3.googleusercontent.com/d/10jvQsU4LXi7J9-pBjsrAhX2gWMyR_SV3=w1600', 'Cueva milagrosa — Tocache', 'normal', TRUE, 1),
    -- REC-00074 · MIRADOR NATURAL DEL GALLINAZO
    -- Fuente consultada https://www.turismoperuano.com/mirador-natural-del-gallinazo-san-martin
    ('REC-00074', 'https://lh3.googleusercontent.com/d/1MKV603d-sIKov9fmIpPqBz-XtOV0DdtR=w1600', 'Mirador natural del gallinazo — Alberto Leveau', 'normal', TRUE, 1),
    -- REC-00075 · CASCADA TAYTAYACU
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=9144
    ('REC-00075', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=456461', 'Cascada taytayacu — Tarapoto', 'normal', TRUE, 1),
    ('REC-00075', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=456408', 'Cascada taytayacu — Tarapoto', 'normal', FALSE, 2),
    -- REC-00076 · CASCADAS ALTO CANUTO
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=12988
    ('REC-00076', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=547971', 'Cascadas alto canuto — Pólvora', 'normal', TRUE, 1),
    ('REC-00076', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=547869', 'Cascadas alto canuto — Pólvora', 'normal', FALSE, 2),
    -- REC-00077 (CASCADAS CHILIA) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00077', 'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQbyyHVi9UI_-RENzd6FRJIUKq5E-zXYOw44VXM8hu9KxWh5vEp', 'Cascadas chilia — Pólvora', 'normal', TRUE, 1),
    -- REC-00078 · CANON PULCACHI
    -- Fuente consultada https://www.youtube.com/watch?v=vTCNfuQd9d4
    ('REC-00078', 'https://lh3.googleusercontent.com/d/1l6ssRLxZNSl-9FRtr65bf6NhdfzIajWF=w1600', 'Canon pulcachi — Pólvora', 'normal', TRUE, 1),
    ('REC-00078', 'https://lh3.googleusercontent.com/d/171tDHYEheZFeyQOVtAMVY3536avNCrul=w1600', 'Canon pulcachi — Pólvora', 'normal', FALSE, 2),
    -- REC-00079 · CASCADAS LAS BRISAS DEL PARAISO
    -- Fuente consultada https://www.youtube.com/watch?v=jfAyUeuz15g
    ('REC-00079', 'https://lh3.googleusercontent.com/d/1_18oko8bOdX9db-U73eGzQOAOJFYSJl9=w1600', 'Cascadas las brisas del paraiso — Pólvora', 'normal', TRUE, 1),
    ('REC-00079', 'https://lh3.googleusercontent.com/d/17685v0SuKWeTS37CXM_2BOLs-cTGvdi2=w1600', 'Cascadas las brisas del paraiso — Pólvora', 'normal', FALSE, 2),
    -- REC-00081 · CASCADA DE TALLIQUIHUI
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=11465
    ('REC-00081', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=454604', 'Cascada de talliquihui — Santa Rosa', 'normal', TRUE, 1),
    ('REC-00081', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=454655', 'Cascada de talliquihui — Santa Rosa', 'normal', FALSE, 2),
    -- REC-00082 · CATARATA DE HUAJA
    -- Fuente consultada https://www.turismoperuano.com/catarata-de-huaja-san-martin
    ('REC-00082', 'https://www.turismoperuano.com/wp-content/uploads/catarata-de-huaja-san-martin.jpg', 'Catarata de huaja — San José de Sisa', 'normal', TRUE, 1),
    -- REC-00083 · AREA DE CONSERVACION PRIVADA TAMBO ILUSION
    -- Fuente consultada https://www.conservamospornaturaleza.org/area/tambo-ilusion-2/
    ('REC-00083', 'https://www.conservamospornaturaleza.org/img/2013/03/IMG_5133.jpg', 'Area de conservacion privada tambo ilusion — La Banda de Shilcayo', 'normal', TRUE, 1),
    ('REC-00083', 'https://www.conservamospornaturaleza.org/img/2013/03/IMG_5437.jpg', 'Area de conservacion privada tambo ilusion — La Banda de Shilcayo', 'normal', FALSE, 2),
    -- REC-00084 · CASCADAS DE CARPISHUYACU
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=8706
    ('REC-00084', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=431710', 'Cascadas de carpishuyacu — La Banda de Shilcayo', 'normal', TRUE, 1),
    ('REC-00084', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=431765', 'Cascadas de carpishuyacu — La Banda de Shilcayo', 'normal', FALSE, 2),
    -- REC-00085 (CANON DE SOLEDAD) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00085', 'https://lens.usercontent.google.com/image?vsrid=CLy_3I7hjOmwpwEQARgBIhDLbDYCT-Z__PYAm3gMW36NMoEBIgJjZygGQnMKLmxmZS1kdW1teTpjZjAzOGMxZC04ODUxLTQ3YmEtOTNiOS0wODM1N2RmNGU3NjUSQQo_L2Jucy9jZy9ib3JnL2NnL2Jucy9sZW5zLWZyb250ZW5kLWFwaS9wcm9kLmxlbnMtZnJvbnRlbmQtYXBpLzMzWgQKAmNnOKiqurHhmZgDUABqCWltYWdlL3BuZw', 'Canon de soledad — Huicungo', 'normal', TRUE, 1),
    -- REC-00086 · MANANTIAL EL FONDERO
    -- Fuente consultada https://www.turismoperuano.com/manantial-el-fondero-san-martin
    ('REC-00086', 'https://www.turismoperuano.com/wp-content/uploads/manantial-el-fondero-san-martin.jpg', 'Manantial el fondero — Tarapoto', 'normal', TRUE, 1),
    -- REC-00087 · MANANTIAL EL ACHUAL
    -- Fuente consultada https://www.turismoperuano.com/manantial-el-achual-san-martin
    ('REC-00087', 'https://www.turismoperuano.com/wp-content/uploads/manantial-el-achual-san-martin.jpg', 'Manantial el achual — Tarapoto', 'normal', TRUE, 1),
    -- REC-00088 · RIO UQUIHUA SECTOR EL CHORRO - QUILLOSISA
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=8100
    ('REC-00088', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=539626', 'Rio uquihua sector el chorro - quillosisa — Rioja', 'normal', TRUE, 1),
    ('REC-00088', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=539586', 'Rio uquihua sector el chorro - quillosisa — Rioja', 'normal', FALSE, 2),
    -- REC-00089 · RESERVA ECOLOGICA SANTA ELENA
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=8099
    ('REC-00089', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=573912', 'Reserva ecologica santa elena — Posic', 'normal', TRUE, 1),
    ('REC-00089', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=298954', 'Reserva ecologica santa elena — Posic', 'normal', FALSE, 2),
    -- REC-00090 (COMPLEJO ARQUEOLOGICO GUAYAQUIL) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00090', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRn5O9tx-NWYZ8Yc347tnKeK7hazvHKFJAaPNV-UpWYwrCJvRKRHxDJXwiI&s=10', 'Complejo arqueologico guayaquil — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00091 (CASCADA TRES MARIAS) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00091', 'https://i0.wp.com/portaldeturismo.pe/wp-content/uploads/2025/06/1182043-whatsapp-image-2025-06-04-at-5-46-30-pm-1.jpeg?fit=900%2C835&ssl=1', 'Cascada tres marias — La Banda de Shilcayo', 'normal', TRUE, 1),
    -- REC-00092 · PAUCARPATA SANTUARIO DE AVES
    -- Fuente consultada https://andina.pe/agencia/noticia-san-martin-conoce-mirador-paucarpata-atractivo-turistico-del-alto-mayo-1047261.aspx
    ('REC-00092', 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2025/10/05/001212233W.webp', 'Paucarpata santuario de aves — Moyobamba', 'normal', TRUE, 1),
    ('REC-00092', 'https://portal.andina.pe/EDPFotografia3/thumbnail/2025/10/05/001212224M.webp', 'Paucarpata santuario de aves — Moyobamba', 'normal', FALSE, 2),
    -- REC-00093 · PUERTO NICANOR VELASQUEZ DE TOCACHE
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=13163
    ('REC-00093', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=558963', 'Puerto nicanor velasquez de tocache — Tocache', 'normal', TRUE, 1),
    ('REC-00093', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=558975', 'Puerto nicanor velasquez de tocache — Tocache', 'normal', FALSE, 2),
    -- REC-00094 · FINCA AGROPARK
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=13474
    ('REC-00094', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589427', 'Finca agropark — Juanjuí', 'normal', TRUE, 1),
    ('REC-00094', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589425', 'Finca agropark — Juanjuí', 'normal', FALSE, 2),
    -- REC-00095 · LAGUNA DE LOS ENCANTOS
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=13659
    ('REC-00095', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=608647', 'Laguna de los encantos — Campanilla', 'normal', TRUE, 1),
    ('REC-00095', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=608613', 'Laguna de los encantos — Campanilla', 'normal', FALSE, 2),
    -- REC-00096 · CASCADA DE SHUCSHUYACU
    -- Fuente consultada https://www.turismoperuano.com/cascada-de-shucshuyacu-san-martin
    ('REC-00096', 'https://www.turismoperuano.com/wp-content/uploads/img_62070d88a6522.jpg', 'Cascada de shucshuyacu — Caynarachi', 'normal', TRUE, 1),
    -- REC-00097 (ZONA DE CONSERVACION Y RECUPERACION DE ECOSISTEMAS EL QUINILLAL) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00097', 'https://amazonica.pe/archivos/2022/09/02.jpg', 'Zona de conservacion y recuperacion de ecosistemas el quinillal — Picota', 'normal', TRUE, 1),
    -- REC-00099 (MIRADOR DE CHICHA ALTA) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00099', 'https://lens.usercontent.google.com/image?vsrid=CPnGobzN_4ejoAEQARgBIhCPR3kHyV-s0SW-K4k0rElzMoEBIgJjZigKQnMKLmxmZS1kdW1teTpjMzBjZDU2ZS04ZjZiLTRmMTYtYjdkNC1iNmY3YjBkMTIwYjUSQQo_L2Jucy9jZi9ib3JnL2NmL2Jucy9sZW5zLWZyb250ZW5kLWFwaS9wcm9kLmxlbnMtZnJvbnRlbmQtYXBpLzQzWgQKAmNmONDti7vjmZgDUABqCWltYWdlL3BuZw', 'Mirador de chicha alta — Pucacaca', 'normal', TRUE, 1),
    -- REC-00100 · PUEBLO PUMAWASI
    -- Fuente consultada https://selvaparaiso.blogspot.com/2016/07/playa-de-la-sirena-pumahuasi-picota.html
    ('REC-00100', 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEg6Bl7RWd0M2Eefp1Ly3p-0hdoHL1kDk_c2g1cmiAU-TFwMSG40YYlzSA11sXm_hjdPALviEMMyDyW_CQJcESq8M98G97HIZxBwWW6jYNeIeDYh4X5aS_eDak7TPcLO8H5xOgHwVLuYnXI/s1600/IMG_1622.JPG', 'Pueblo pumawasi — Picota', 'normal', TRUE, 1),
    ('REC-00100', 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgwzio5f3eJ6LawI7tTTL9BrchZfP0R2dYnFtCAO1_EHVkaPZ4-dke35iyohogF68_-a9uj9wCeXEecue23mEjFEz7R2YYpiymSO6ZGRxs29Rh-Dq-5NNLRLa5TKSHEtH4h5ekP8nYyEFU/s1600/IMG_1619.JPG', 'Pueblo pumawasi — Picota', 'normal', FALSE, 2),
    -- REC-00101 · CENTRO URKU
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=12111
    ('REC-00101', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=487684', 'Centro urku — Tarapoto', 'normal', TRUE, 1),
    ('REC-00101', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=488519', 'Centro urku — Tarapoto', 'normal', FALSE, 2),
    -- REC-00102 · BOSQUE OJOS DE AGUA
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=5342
    ('REC-00102', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=493077', 'Bosque ojos de agua — Pucacaca', 'normal', TRUE, 1),
    ('REC-00102', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=493033', 'Bosque ojos de agua — Pucacaca', 'normal', FALSE, 2),
    -- REC-00103 · MIRADOR PUCACACA
    -- Fuente consultada https://www.turismoperuano.com/mirador-pucacaca-san-martin
    ('REC-00103', 'https://lh3.googleusercontent.com/d/1sen9pMKEvqT3E9YP9zQ9n-RdRbJXRyYJ=w1600', 'Mirador pucacaca — Pucacaca', 'normal', TRUE, 1),
    -- REC-00104 · LA SANTISIMA CRUZ DE LOS MOTILONES DE LAMAS
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=5321
    ('REC-00104', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=483984', 'La santisima cruz de los motilones de lamas — Lamas', 'normal', TRUE, 1),
    ('REC-00104', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=483985', 'La santisima cruz de los motilones de lamas — Lamas', 'normal', FALSE, 2),
    -- REC-00105 · CATARATAS DE PUCAYAQUILLO
    -- Fuente consultada https://visitasanmartin.com/sitio/cataratas-de-pucayaquillo/
    ('REC-00105', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=576260', 'Cataratas de pucayaquillo — Shapaja', 'normal', TRUE, 1),
    ('REC-00105', 'https://visitasanmartin.com/wp-content/uploads/2025/06/image00006-scaled.jpeg', 'Cataratas de pucayaquillo — Shapaja', 'normal', FALSE, 2),
    -- REC-00106 · FIESTA RELIGIOSA SANTA ROSA RAYMI
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=5313
    ('REC-00106', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=483983', 'Fiesta religiosa santa rosa raymi — Lamas', 'normal', TRUE, 1),
    ('REC-00106', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=483952', 'Fiesta religiosa santa rosa raymi — Lamas', 'normal', FALSE, 2),
    -- REC-00107 (CASCADA DE LAS VELAS) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00107', 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcR4MauRq67NSFLMB3bENcxL56ztr4FfizqR-vcM4y7rmv9ZcDV-', 'Cascada de las velas — Yorongos', 'normal', TRUE, 1),
    -- REC-00108 · CASCADA DE YANAYACU
    -- Fuente consultada https://www.chullostravelperu.com/blog/cascada-de-yanayacu
    ('REC-00108', 'https://www.chullostravelperu.com/blog/wp-content/uploads/2023/05/yanayacu-catarata.jpg', 'Cascada de yanayacu — Moyobamba', 'normal', TRUE, 1),
    -- REC-00111 · MIRADOR PINTO RECODO
    -- Fuente consultada https://www.turismoperuano.com/mirador-pinto-recodo-san-martin
    ('REC-00111', 'https://www.turismoperuano.com/wp-content/uploads/mirador-pinto-recodo-san-martin.jpg', 'Mirador pinto recodo — Pinto Recodo', 'normal', TRUE, 1),
    -- REC-00112 · FIESTA PATRONAL VIRGEN DE LA NATIVIDAD DE TABALOSOS
    -- Fuente consultada https://prelaturademoyobamba.com/santuario-virgen-de-la-natividad-celebra-sus-fiestas-patronales-2026/
    ('REC-00112', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=645962', 'Fiesta patronal virgen de la natividad de tabalosos — Tabalosos', 'normal', TRUE, 1),
    ('REC-00112', 'https://i0.wp.com/prelaturademoyobamba.com/wp-content/uploads/2026/09/Reina-de-la-Prelatura-de-Moyobamba-29-1024x768.webp?resize=960%2C960', 'Fiesta patronal virgen de la natividad de tabalosos — Tabalosos', 'normal', FALSE, 2),
    -- REC-00113 · SANTUARIO DE LA VIRGEN DE LA NATIVIDAD DE TABALOSOS
    -- Fuente consultada https://portal.andina.pe/EDPFotografia3/thumbnail/2023/08/03/000982062W.jpg
    ('REC-00113', 'https://portal.andina.pe/EDPFotografia3/thumbnail/2023/08/03/000982062W.jpg', 'Santuario de la virgen de la natividad de tabalosos — Tabalosos', 'normal', TRUE, 1),
    -- REC-00115 · CASCADA EL PONGUITO DE CHUMBAQUIHUI
    -- Fuente consultada https://www.youtube.com/watch?v=rD9nuMXlpqc
    ('REC-00115', 'https://lh3.googleusercontent.com/d/1yUXFXci2suO_oxTy0bLrXYdgivc_C6Ln=w1600', 'Cascada el ponguito de chumbaquihui — Pinto Recodo', 'normal', TRUE, 1),
    -- REC-00116 · CENTRO ARTESANAL WASKA WASKA WARMI WASI
    -- Fuente consultada https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=4339
    ('REC-00116', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=591450', 'Centro artesanal waska waska warmi wasi — Lamas', 'normal', TRUE, 1),
    ('REC-00116', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=591449', 'Centro artesanal waska waska warmi wasi — Lamas', 'normal', FALSE, 2),
    -- REC-00117 (FIESTA PATRONAL SANTO PATRON SANTIAGO) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00117', 'https://portal.andina.pe/EDPFotografia3/thumbnail/2023/06/19/000968109M.jpg', 'Fiesta patronal santo patron santiago — Zapatero', 'normal', TRUE, 1),
    -- REC-00118 · CASCADAS DE TOAZAPA
    -- Fuente consultada https://radiotropical.pe/wp-content/uploads/2022/02/5f753291-f031-4f74-8c0d-5c9c101ef5fb.jpg
    ('REC-00118', 'https://lh3.googleusercontent.com/d/1yUXFXci2suO_oxTy0bLrXYdgivc_C6Ln=w1600', 'Cascadas de toazapa — Barranquita', 'normal', TRUE, 1),
    -- REC-00119 (CASCADAS DE YANAYACU) · Pendiente de reemplazo (se conserva enlace previo)
    ('REC-00119', 'https://s1.wklcdn.com/image_344/10332643/99480197/64776040Master.jpg', 'Cascadas de yanayacu — Barranquita', 'normal', TRUE, 1);

-- 1) Limpiar el enlace previo mal asignado a REC-00061 (pertenecía a REC-00020 Nueva Cajamarca)
DELETE FROM turismo.atractivo_imagen i
USING turismo.atractivo a
WHERE i.id_atractivo = a.id_atractivo
  AND a.codigo_recurso = 'REC-00061'
  AND i.tipo = 'normal'
  AND i.url = 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=496631';

-- 2) Insertar o actualizar imágenes principales (ux_imagen_principal: (id_atractivo, tipo) WHERE es_principal)
INSERT INTO turismo.atractivo_imagen
    (id_atractivo, url, texto_alternativo, tipo, es_principal, orden)
SELECT
    a.id_atractivo,
    t.url,
    t.texto_alternativo,
    t.tipo,
    t.es_principal,
    t.orden
FROM tmp_imagenes_060_120 t
JOIN turismo.atractivo a
  ON a.codigo_recurso = t.codigo_recurso
 AND (
     t.codigo_recurso <> 'REC-00020'
     OR (upper(a.nombre) = 'CUEVA CASCADA ESCONDIDA' AND a.ubigeo = '220804')
 )
WHERE t.es_principal = TRUE
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO UPDATE SET
    url = EXCLUDED.url,
    texto_alternativo = EXCLUDED.texto_alternativo,
    orden = EXCLUDED.orden;

-- 3) Actualizar imágenes secundarias existentes en ese orden (sin crear duplicados al re-ejecutar)
UPDATE turismo.atractivo_imagen i
SET url = t.url,
    texto_alternativo = t.texto_alternativo
FROM tmp_imagenes_060_120 t
JOIN turismo.atractivo a
  ON a.codigo_recurso = t.codigo_recurso
 AND (
     t.codigo_recurso <> 'REC-00020'
     OR (upper(a.nombre) = 'CUEVA CASCADA ESCONDIDA' AND a.ubigeo = '220804')
 )
WHERE t.es_principal = FALSE
  AND i.id_atractivo = a.id_atractivo
  AND i.tipo = t.tipo
  AND i.es_principal = FALSE
  AND i.orden = t.orden;

-- 4) Insertar nuevas imágenes secundarias de forma idempotente
INSERT INTO turismo.atractivo_imagen
    (id_atractivo, url, texto_alternativo, tipo, es_principal, orden)
SELECT
    a.id_atractivo,
    t.url,
    t.texto_alternativo,
    t.tipo,
    t.es_principal,
    t.orden
FROM tmp_imagenes_060_120 t
JOIN turismo.atractivo a
  ON a.codigo_recurso = t.codigo_recurso
 AND (
     t.codigo_recurso <> 'REC-00020'
     OR (upper(a.nombre) = 'CUEVA CASCADA ESCONDIDA' AND a.ubigeo = '220804')
 )
WHERE t.es_principal = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM turismo.atractivo_imagen i
      WHERE i.id_atractivo = a.id_atractivo
        AND i.tipo = t.tipo
        AND i.es_principal = FALSE
        AND (i.orden = t.orden OR i.url = t.url)
  );

COMMIT;
