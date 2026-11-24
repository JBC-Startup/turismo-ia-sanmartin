-- ============================================================================
-- 08_imagenes_241_300_turismoia.sql
-- Imágenes normales REC-00241 a REC-00300 (resuelto por codigo_recurso)
-- Fuente: database/TurismoIA_241_300.sql (49 registros)
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
    -- REC-00241 -> id_atractivo=240 (CASCADA DE LAHUARPIA)
    ('REC-00241', 'https://www.turismoperuano.com/wp-content/uploads/cascada-de-lahuarpia-san-martin.jpg', 'Cascada de lahuarpia — Jepelacio', 'normal', TRUE, 1),
    -- REC-00242 -> id_atractivo=241 (MANANTIAL DE SACANCHE)
    ('REC-00242', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=293084', 'Manantial de sacanche — Sacanche', 'normal', TRUE, 1),
    -- REC-00245 -> id_atractivo=244 (CASCADA DE SHIMA)
    ('REC-00245', 'https://3.bp.blogspot.com/-SdWl3uFIaLc/WDHstshQEKI/AAAAAAAAkkM/NOKKCRhpPFkOn_ihSxs8M5IN--tGJWYoQCLcB/s1600/DSC04199%2B%25282%2529.JPG', 'Cascada de shima — Saposoa', 'normal', TRUE, 1),
    -- REC-00247 -> id_atractivo=246 (CASCADA DE PAIMA)
    ('REC-00247', 'https://2.bp.blogspot.com/-lgaOjF8Updw/V9C1gbRXAgI/AAAAAAAAj_0/q8mdlZLgd-o0TQW_Em4ngX-5GnmMiDIZwCLcB/s1600/paima%2B6.jpg', 'Cascada de paima — Saposoa', 'normal', TRUE, 1),
    -- REC-00248 -> id_atractivo=247 (QUEBRADA OROS)
    ('REC-00248', 'https://1.bp.blogspot.com/-ofgWPq8Tvbc/Xv0d4Msi3eI/AAAAAAAAAeA/o7_Ty7edWiM-nnfP4xV4UGFM6LaWNMqzwCK4BGAsYHg/s800/quebrada%2BDE%2BORO.jpg', 'Quebrada oros — Huicungo', 'normal', TRUE, 1),
    -- REC-00249 -> id_atractivo=248 (CENTRO DE INTERPRETACION DEL PARQUE NACIONAL RIO ABISEO)
    ('REC-00249', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=525236', 'Centro de interpretacion del parque nacional rio abiseo — Huicungo', 'normal', TRUE, 1),
    -- REC-00250 -> id_atractivo=249 (QUEBRADA CHURO - PARTE BAJA)
    ('REC-00250', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=391105', 'Quebrada churo - parte baja — Huicungo', 'normal', TRUE, 1),
    -- REC-00251 -> id_atractivo=250 (CASCADA TIMON)
    ('REC-00251', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=293106', 'Cascada timon — Huicungo', 'normal', TRUE, 1),
    -- REC-00253 -> id_atractivo=252 (PETROGLIFOS DE PANGUANA)
    ('REC-00253', 'https://www.turismoperuano.com/wp-content/uploads/petroglifos-de-panguana-san-martin-scaled.jpg', 'Petroglifos de panguana — Pachiza', 'normal', TRUE, 1),
    -- REC-00254 -> id_atractivo=253 (PETROGLIFOS DE CUNCHIHUILLO)
    ('REC-00254', 'https://www.turismoperuano.com/wp-content/uploads/petroglifos-de-cunchihuillo-san-martin.jpg', 'Petroglifos de cunchihuillo — Juanjui', 'normal', TRUE, 1),
    -- REC-00255 -> id_atractivo=254 (CATARATA EL BREO)
    ('REC-00255', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=315786', 'Catarata el breo — Huicungo', 'normal', TRUE, 1),
    -- REC-00256 -> id_atractivo=255 (CASCADA DE PACCHA)
    ('REC-00256', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=502662', 'Cascada de paccha — Jepelacio', 'normal', TRUE, 1),
    -- REC-00257 -> id_atractivo=256 (EMBARCADERO TURISTICO DE TAHUISHCO)
    ('REC-00257', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=295248', 'Embarcadero turistico de tahuishco — Moyobamba', 'normal', TRUE, 1),
    -- REC-00258 -> id_atractivo=257 (MIRADOR TURISTICO DE LAMAS)
    ('REC-00258', 'https://lh5.googleusercontent.com/p/AF1QipMC512GnnLrYygJoGYDEJIAhdR5xBTKwKL9t7ga=w1080-k-no', 'Vista del paisaje desde el Mirador Turístico de Lamas', 'normal', TRUE, 1),
    -- REC-00259 -> id_atractivo=258 (AGUAS TERMALES Y SULFOROSOS DE CHAZUTAYACU)
    ('REC-00259', 'https://www.turismoperuano.com/wp-content/uploads/banos-termales-y-sulfurosos-de-chazutayacu-san-martin.jpg', 'Aguas termales y sulforosos de chazutayacu — Chazuta', 'normal', TRUE, 1),
    -- REC-00260 -> id_atractivo=259 (TABACALERA DEL ORIENTE)
    ('REC-00260', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=653793', 'Tabacalera del oriente — Tarapoto', 'normal', TRUE, 1),
    -- REC-00261 -> id_atractivo=260 (AGUAS TERMALES Y SULFUROSAS DE JEPELACIO)
    ('REC-00261', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=430186', 'Aguas termales y sulfurosas de jepelacio — Jepelacio', 'normal', TRUE, 1),
    -- REC-00262 -> id_atractivo=261 (CUEVA DE LOS HUACHAROS)
    ('REC-00262', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=295926', 'Cueva de los huacharos — Soritor', 'normal', TRUE, 1),
    -- REC-00263 -> id_atractivo=262 (CASCADA DE MAMONAQUIHUA)
    ('REC-00263', 'https://www.turismoperuano.com/wp-content/uploads/img_62070d6218c83.jpg', 'Cascada de mamonaquihua — Cuñumbuqui', 'normal', TRUE, 1),
    -- REC-00264 -> id_atractivo=263 (CATARATA DE HUACAMAILLO)
    ('REC-00264', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=456510', 'Catarata de huacamaillo — San Antonio', 'normal', TRUE, 1),
    -- REC-00265 -> id_atractivo=264 (CASCADA DE ASNACYACU)
    ('REC-00265', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=394012', 'Cascada de asnacyacu — Moyobamba', 'normal', TRUE, 1),
    -- REC-00266 -> id_atractivo=265 (LAGUNA VENECIA)
    ('REC-00266', 'https://www.turismoperuano.com/wp-content/uploads/laguna-venecia-san-martin-scaled.jpg', 'Laguna venecia — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00267 -> id_atractivo=266 (MIRADOR PUNTA DE FACHIN)
    ('REC-00267', 'https://blog.casa-andina.com/wp-content/uploads/2025/05/mirador-moyobamba.jpg', 'Vista del valle del Alto Mayo desde el Mirador Punta de Fachín, Moyobamba', 'normal', TRUE, 1),
    -- REC-00268 -> id_atractivo=267 (MIRADOR PUNTA DE TAHUISHCO)
    ('REC-00268', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=484771', 'Mirador punta de tahuishco — Moyobamba', 'normal', TRUE, 1),
    -- REC-00269 -> id_atractivo=268 (MIRADOR PUNTA DE SAN JUAN)
    ('REC-00269', 'https://www.turismoperuano.com/wp-content/uploads/mirador-punta-de-san-juan-san-martin.jpg', 'Mirador punta de san juan — Moyobamba', 'normal', TRUE, 1),
    -- REC-00270 -> id_atractivo=269 (PETROGLIFOS DE POLISH)
    ('REC-00270', 'https://www.turismoperuano.com/wp-content/uploads/petroglifos-de-polish-san-martin.jpg', 'Petroglifos de polish — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00271 -> id_atractivo=270 (CUEVA DEL DIAMANTE)
    ('REC-00271', 'https://cuevasdelperu.org/wp-content/gallery/cueva-del-diamante-fotos/p1010236.jpg', 'Cueva del diamante — Pardo Miguel', 'normal', TRUE, 1),
    -- REC-00272 -> id_atractivo=271 (MIRADOR PUNTA DE DONE)
    ('REC-00272', 'https://www.turismoperuano.com/wp-content/uploads/mirador-punta-de-done-san-martin.jpg', 'Mirador punta de done — Moyobamba', 'normal', TRUE, 1),
    -- REC-00274 -> id_atractivo=273 (AGUAS TERMALES SAN MATEO)
    ('REC-00274', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=385200', 'Aguas termales san mateo — Moyobamba', 'normal', TRUE, 1),
    -- REC-00275 -> id_atractivo=274 (MORRO DE CALZADA)
    ('REC-00275', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=463477', 'Morro de calzada — Calzada', 'normal', TRUE, 1),
    -- REC-00276 -> id_atractivo=275 (CATARATAS DE AHUASHIYACU)
    ('REC-00276', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=584692', 'Cataratas de ahuashiyacu — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00277 -> id_atractivo=276 (CATARATA DE CHAPAWANKI)
    ('REC-00277', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=517240', 'Catarata de chapawanki — Lamas', 'normal', TRUE, 1),
    -- REC-00278 -> id_atractivo=277 (CASCADA DE TUNUNTUNUMBA)
    ('REC-00278', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=602424', 'Cascada de tununtunumba — Chazuta', 'normal', TRUE, 1),
    -- REC-00279 -> id_atractivo=278 (LAGO LINDO)
    ('REC-00279', 'https://www.turismoperuano.com/wp-content/uploads/lago-lindo-san-martin.jpg', 'Lago lindo — Sauce', 'normal', TRUE, 1),
    -- REC-00280 -> id_atractivo=279 (LAGO SAUCE (LAGUNA AZUL))
    ('REC-00280', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=653953', 'Lago sauce (laguna azul) — Sauce', 'normal', TRUE, 1),
    -- REC-00281 -> id_atractivo=280 (AGUAS SULFUROSAS DE OROMINA)
    ('REC-00281', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=480154', 'Aguas sulfurosas de oromina — Moyobamba', 'normal', TRUE, 1),
    -- REC-00283 -> id_atractivo=282 (CASCADA LA VICTORIA)
    ('REC-00283', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=589960', 'Cascada la victoria — Shunte', 'normal', TRUE, 1),
    -- REC-00285 -> id_atractivo=284 (PLAZA DE ARMAS DE RIOJA)
    ('REC-00285', 'https://turismo.munirioja.gob.pe/img/Recursos%20Turisticos/tur26/plaza_1.jpg', 'Plaza de armas de rioja — Rioja', 'normal', TRUE, 1),
    -- REC-00286 -> id_atractivo=285 (PLAZA DE LA CULTURA DE NUEVA CAJAMARCA)
    ('REC-00286', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=622166', 'Plaza de la cultura de nueva cajamarca — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00287 -> id_atractivo=286 (CENTRO CULTURAL MOYOBAMBA (CUMO))
    ('REC-00287', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=617073', 'Centro cultural moyobamba (cumo) — Moyobamba', 'normal', TRUE, 1),
    -- REC-00288 -> id_atractivo=287 (PUENTE COCOCHO)
    ('REC-00288', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=622833', 'Puente cococho — Moyobamba', 'normal', TRUE, 1),
    -- REC-00289 -> id_atractivo=288 (PLAZUELA LIBERTAD - MOYOBAMBA)
    ('REC-00289', 'https://upload.wikimedia.org/wikipedia/commons/c/c4/Plazuela_Libertad_en_Moyobamba.JPG', 'Plazuela libertad - moyobamba — Moyobamba', 'normal', TRUE, 1),
    -- REC-00294 -> id_atractivo=293 (CHOCOLATERIA VALLE DE RIOJA)
    ('REC-00294', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=632657', 'Chocolateria valle de rioja — Rioja', 'normal', TRUE, 1),
    -- REC-00295 -> id_atractivo=294 (TALLER ARTESANAL LLUTAKUNA WASI)
    ('REC-00295', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=626107', 'Taller artesanal llutakuna wasi — Lamas', 'normal', TRUE, 1),
    -- REC-00296 -> id_atractivo=295 (PUEBLO DE LAMAS)
    ('REC-00296', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=652452', 'Vista aérea del pueblo de Lamas', 'normal', TRUE, 1),
    -- REC-00297 -> id_atractivo=296 (MARINERA LAMISTA)
    ('REC-00297', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=644002', 'Marinera lamista — Lamas', 'normal', TRUE, 1),
    -- REC-00298 -> id_atractivo=297 (FIESTA PATRONAL VIRGEN DE LOS REMEDIOS)
    ('REC-00298', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=627797', 'Fiesta patronal virgen de los remedios — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00299 -> id_atractivo=298 (FESTIVAL DEL JUANE AMAZONICO SABOR BANDINO)
    ('REC-00299', 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=627803', 'Festival del juane amazonico sabor bandino — La Banda De Shilcayo', 'normal', TRUE, 1),
    -- REC-00300 -> id_atractivo=299 (FIESTA PATRONAL VIRGEN DEL PERPETUO SOCORRO)
    ('REC-00300', 'https://i1.wp.com/www.prelaturademoyobamba.com/wp-content/uploads/2024/10/picota-patrona-12-1024x771.jpg?resize=1542%2C1542', 'Celebración en la parroquia Virgen del Perpetuo Socorro de Picota, octubre de 2024', 'normal', TRUE, 1)
) AS v(codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
JOIN turismo.atractivo a
  ON a.codigo_recurso = v.codigo_recurso
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO NOTHING;

COMMIT;
