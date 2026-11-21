SET client_encoding = 'UTF8';
SET search_path TO turismo, public;
BEGIN;
-- =====================================================================
-- Imágenes normales (principales y secundarias) para atractivos 180 a 240
-- Cada INSERT tiene VALUES en la línea siguiente, comentado con ID, código y nombre.
-- =====================================================================
DELETE FROM turismo.atractivo_imagen WHERE id_atractivo BETWEEN 180 AND 240 AND tipo = 'normal' AND es_principal = FALSE;
-- [180] REC-00180 | AGUAS TERMALES DON GRIMALDO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (180, 'https://lh3.googleusercontent.com/grass-cs/AABkmLeFyuprJgPGxthmguBtZ7vDUOJh7M0j2O5wmyMffqfw5FykrbaRT9FmVtBqDz9vXbA_bFTBEFraYzCnK61ZZMZgp79BhoeOwfrLkeU7PDMubqiXovUbbOAmY4eUXlEVSFi8FxiQ=w1200-h800-k-no', 'Aguas Termales Don Grimaldo', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [181] REC-00181 | CENTRO ACADEMICO DE INVESTIGACION Y ECOTURISTICO - BIODIVERSIDAD DE LA UNSM
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (181, 'https://scontent-lim1-1.xx.fbcdn.net/v/t39.30808-6/499544668_999489565727174_9033561357362168632_n.jpg?stp=dst-jpg_tt6&cstp=mx2048x1543&ctp=s2048x1543&_nc_cat=102&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=127cfc&_nc_eui2=AeHLArIxYdxgT3vNTBWCMKfpt4B-mf2xZkC3gH6Z_bFmQHTcEjKM3JcjrAXUmEbf_mzFcF8C-En9BDcJf0-6shvl&_nc_ohc=55LMpOPukdwQ7kNvwF8r4pY&_nc_oc=Adqtajq55-GUGp099J40HRIzk48uvj9p42-GoD-TMXH4iVpTUkbLBshWJM38xtG3B6c&_nc_zt=23&_nc_ht=scontent-lim1-1.xx&_nc_gid=-93SArrPSQLSIyU10HMZpg&_nc_ss=7a2a8&oh=00_AQTImEBYuRpacGkJRKL6l5GydOzRBN_HjLG4lfwe3dACYw&oe=6B078EF4', 'Centro Academico De Investigacion Y Ecoturistico - Biodiversidad De La Unsm', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [182] REC-00182 | BANOS TERMALES MEDICINALES DE PAUCARYACU BANOS TERMALES DE PAUCARYACU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (182, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-k1DuHdySmCqiZ-cReKVTa6_S_GpDF41Hwaia2MHWn_7vduGoOC-E8u9PpsOJWGl7OocVN5d_lc1OtGcnGJChzA9dRYlzBTDzo-QgFoNxPx7ALzPulv2RdY70ajpGQt1afN9kc=w1200-h800-p-k-no', 'Banos Termales Medicinales De Paucaryacu Banos Termales De Paucaryacu', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [183] REC-00183 | FIESTA PATRONAL VIRGEN DE LAS MERCEDES
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (183, 'https://www.prelaturademoyobamba.com/wp-content/uploads/2024/09/merced-fiesta-3.jpeg', 'Fiesta Patronal Virgen De Las Mercedes', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [184] REC-00184 | FESTIVAL REGIONAL DE LA NARANJA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (184, 'https://cdn.www.gob.pe/uploads/document/file/6990547/1027879-30.jpg', 'Festival Regional De La Naranja', 'GORE San Martín', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [185] REC-00185 | RAPIDOS DE SAN JERONIMO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (185, 'https://www.turismoperuano.com/wp-content/uploads/img_62070f0e02ba2.jpg', 'Rapidos De San Jeronimo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (185, 'https://visitasanmartin.com/wp-content/uploads/2025/06/RAPIDOS-rotated.jpeg', 'Rapidos De San Jeronimo - Vista secundaria', NULL, 'normal', FALSE, 2);
-- [186] REC-00186 | BOSQUE SHIRINGAL
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (186, 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=390556', 'Bosque Shiringal', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [187] REC-00187 | MUSEO DEPARTAMENTAL SAN MARTIN
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (187, 'https://www.tur4all.com/images/153254', 'Museo Departamental San Martin', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (187, 'https://lh5.googleusercontent.com/p/AF1QipO5uswrAhgUktDJL2IAscDYR4j5HLNPMrsHA3lH=w1200-h800-k-no', 'Museo Departamental San Martin - Google Maps', 'Google Maps', 'normal', FALSE, 2);
-- [188] REC-00188 | CUEVA DEL OTORONGO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (188, 'https://cuevasdelperu.org/wp-content/gallery/travesia-del-rio-churos-fotos/p3010120.jpg', 'Cueva Del Otorongo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (188, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U9uVVnMNRembywxiVXcnk-XrhLwOTE9_STd-61Jkav-qiA7sAjcqA8BEFgFd9IoUfRFfWFK_ffwla8_luXXPD45QCn1na9wYD2XSzA7XwH7q54GgQVVoLCbeKC7Py2jqVOlWB7PmpCIOME7=w1200-h800-p-k-no', 'Cueva Del Otorongo - Google Maps', 'Google Maps', 'normal', FALSE, 2);
-- [189] REC-00189 | CUEVA DE LOS FRANCESES
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (189, 'https://www.turismoperuano.com/wp-content/uploads/cueva-de-los-franceses-san-martin.jpg', 'Cueva De Los Franceses', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [190] REC-00190 | CASCADA EL OSO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (190, 'https://www.turismoperuano.com/wp-content/uploads/cascada-oso-san-martin.jpg', 'Cascada El Oso', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [191] REC-00191 | CASCADAS DE MICAELA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (191, 'https://www.ytuqueplanes.com/imagenes/fotos/novedades/interna-Campana-selva-nota5-1.jpg', 'Cascadas De Micaela', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [192] REC-00192 | PLAZA DE ARMAS DE JUANJUI
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (192, 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Plaza_Juanjui.png', 'Plaza De Armas De Juanjui', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (192, 'https://lh3.googleusercontent.com/p/AF1QipMlxkdGcKwGxRGHS_TXIY-jGS645jUI7tu9axYq=w1200-h800-k-no', 'Plaza De Armas De Juanjui - Google Maps', 'Google Maps', 'normal', FALSE, 2);
-- [193] REC-00193 | MUSEO ARQUEOLOGICO DE SITIO GUAYAQUIL
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (193, 'https://i.ytimg.com/vi/aoboGIB5PI0/maxres2.jpg', 'Museo Arqueologico De Sitio Guayaquil', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [194] REC-00194 | CUEVA PALACIO DEL REY
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (194, 'https://scontent-lim1-1.xx.fbcdn.net/v/t39.99422-6/720696008_3688262171314379_6565245968815252036_n.png?stp=dst-jpg_tt6&cstp=mx1600x1200&ctp=s1600x1200&_nc_cat=100&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=127cfc&_nc_eui2=AeHCrZg4kPN9H10mitCr7AvEYbD4EAVOBd9hsPgQBU4F396SpoCH1sUxkXHsLJRd_cFKvF55jGK-QVXooRaSfUx1&_nc_ohc=ag0J5IVfGOkQ7kNvwGLK66J&_nc_oc=AdrCNY4eZ1TjZvU25VY2aQKE-dmTT6uAltwmUyEjsiR5TSyi_riYownV11Gd-fYPhdo&_nc_zt=14&_nc_ht=scontent-lim1-1.xx&_nc_gid=6-G1APhVkZOlTpWxJRZl-g&_nc_ss=7a2a8&oh=00_AQRsacpBrpuX5_pDon7zFV7L26j1UHSrRB3vcWM0Fp9F8w&oe=6B064E71', 'Cueva Palacio Del Rey', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;

-- [195] REC-00195 | CUEVA DEL TIGRE PERDIDO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (195, 'https://cuevasdelperu.org/wp-content/gallery/cueva-del-tigre-perdido-fotos/img_20180226_093535.jpg', 'Cueva Del Tigre Perdido', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [196] REC-00196 | CUEVA DE PALESTINA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (196, 'https://consultasenlinea.mincetur.gob.pe/fichaInventario//foto.aspx?cod=295788', 'Cueva De Palestina', 'MINCETUR', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (196, 'https://lh5.googleusercontent.com/p/AF1QipOdBf66yLbwUYunPhSX3gQfGJ0ANY0iSb7DSdyK=w1200-h800-k-no', 'Cueva De Palestina - Google Maps', 'Google Maps', 'normal', FALSE, 2);
-- [197] REC-00197 | CERRO MIRADOR
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (197, 'https://visitasanmartin.com/wp-content/uploads/2025/06/Cerro-Mirador-Andino-Amazonico-1-1.jpg', 'Cerro Mirador', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [198] REC-00198 | ANIVERSARIO DE FUNDACION ESPANOLA Y SEMANA TURISTICA DE RIOJA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (198, 'https://diarioviral.pe/uploads/333a19ef2a75_000993618W.jpg', 'Aniversario De Fundacion Espanola Y Semana Turistica De Rioja', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [199] REC-00199 | PINTURA RUPESTRE DE AUCAPATA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (199, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2024/04/21/001057566W.jpg', 'Pintura Rupestre De Aucapata', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [200] REC-00200 | PANDILLA MOYOBAMBINA Y LA UMSHA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (200, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2025/07/25/001190985W.jpg', 'Pandilla Moyobambina Y La Umsha', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [201] REC-00201 | RIO MAYO SECTOR JUAN ANTONIO - TAHUISHCO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (201, 'https://lh5.googleusercontent.com/p/AF1QipMSUBgH68lz1Etqgg5UHewVV8PbzkmRInmpE0e8=w1200-h800-k-no', 'Rio Mayo Sector Juan Antonio - Tahuishco', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [202] REC-00202 | MASCARAS RIOJANAS
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (202, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2024/02/13/001037994W.jpg', 'Mascaras Riojanas', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [203] REC-00203 | TEJIDOS DE PAJA DE RIOJA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (203, 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=538884', 'Tejidos De Paja De Rioja', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [204] REC-00204 | MIRADOR ALTOMIRA - SAPOSOA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (204, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-ggSlI-DDWxK4POFoNw_W1s-tiC11yK7k-AlPMbDfXQCJsTb7Pq3OO6l77eLxxBQzkzmAAIHvs24oUHtxCnCCexGmxUyrxHSUtamQ93YHDcVUq95zvzlOz-BOin9nPjyLtAUAt=w1200-h800-p-k-no', 'Mirador Altomira - Saposoa', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [205] REC-00205 | MIRADOR NATURAL DE CUNCHIHUILLO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (205, 'https://lh3.googleusercontent.com/gps-cs/AAjk-CNFt0kWI44C3HDBKkW7Nt0OPMryb22uKlJHWHz6LxquSp6UZxiNvvD4aAnSRoLX5W2PvSsE3yDKbr2ROM2Lb3RX3bkXK2yLXdBiCVPPZykMy3YLxsW86CVTkyYo6HvBICdx2DlOIA=s1600', 'Mirador Natural De Cunchihuillo', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [206] REC-00206 | CHU CHU CENTER
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (206, 'https://lh5.googleusercontent.com/p/AF1QipMtJfO516AhD7AKvuE5xExuf-UrMj41naJu3L2Q=w1200-h800-k-no', 'Chu Chu Center', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [207] REC-00207 | CAPILLA SANTO CRISTO DE BAGAZAN
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (207, 'https://scontent-lim1-1.xx.fbcdn.net/v/t39.30808-6/486156252_952796940380390_4003656054054320771_n.jpg?stp=dst-jpg_tt6&cstp=mx960x1280&ctp=s960x1280&_nc_cat=110&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeFPcWdvptc_qS_TJN5XxP4dolBtVlEuUyGiUG1WUS5TIfGw9oYSfyBziNnW1q0cCSrHq815HaSrZcD-yENJy9Cz&_nc_ohc=a_7w_ZT1hrkQ7kNvwHvan1m&_nc_oc=Adp8CHXXtOQshTDfVa8ALaGb7tkbnMgmqtQEcNvrPzMldgdmTBXdpkXh2zuhqiznm1o&_nc_zt=23&_nc_ht=scontent-lim1-1.xx&_nc_gid=2BFUs5VFf0QkpsakCIBoPQ&_nc_ss=7a2a8&oh=00_AQQNA8Md9UeQZ9e3HvaQU9AwFPjzmRU15co1Mlodv7TZMA&oe=6B064F5C', 'Capilla Santo Cristo De Bagazan', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [208] REC-00208 | VIVERO ORQUIDEAS AMAZONICAS
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (208, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-jAKFrOtFWpzkZjk1DeZ5MlNlDfyjhEtCiJ3m50MeHK3ZApq5q32FXQeEMnmv9-LXcD3H0OcjU6bWRJEqapfAuOZo6zM_3uB2GCOJtVf1Ab7qGEB3wxLTRZyAZ5bFrdB7Xfk9o=w1200-h800-p-k-no', 'Vivero Orquideas Amazonicas', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [209] REC-00209 | LAS PAMPAS DEL OLVIDO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (209, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U___R8F5srb4ld-_VyxLrybBzEBTWZ-ajUiNwMznArlW6GmcV2DCdedSyRiWbEM-Ia0H2hhgRSqaRPDWmxPty6BPoq-7noZ3B2WKJRiI9X5AszUj1441Qwhi4rDZxxgVn72Fcyx=w1200-h800-p-k-no', 'Las Pampas Del Olvido', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [210] REC-00210 | CENTRO DE CONSERVACION WAQANKI
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (210, 'https://www.turismoperuano.com/wp-content/uploads/centro-de-conservacion-waqanki-san-martin.jpg', 'Centro De Conservacion Waqanki', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [211] REC-00211 | ANIVERSARIO DE FUNDACION ESPANOLA DE MOYOBAMBA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (211, 'https://www.turismoperuano.com/wp-content/uploads/aniversario-de-fundacion-espanola-de-moyobamba-san-martin.jpg', 'Aniversario De Fundacion Espanola De Moyobamba', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [212] REC-00212 | FIESTA PATRONAL SANTIAGO APOSTOL Y SANTA ANA DE MOYOBAMBA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (212, 'https://www.prelaturademoyobamba.com/wp-content/uploads/2022/07/Fiestas-Patronales-1.jpg', 'Fiesta Patronal Santiago Apostol Y Santa Ana De Moyobamba', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [213] REC-00213 | CARNAVAL RIOJANO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (213, 'https://visitasanmartin.com/wp-content/uploads/2025/05/BRD9743-scaled.jpg', 'Carnaval Riojano', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [214] REC-00214 | CASTILLO MEDIEVAL DE LAMAS
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (214, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_aeXPUzcaXEcyWM2el3J_Oo4aBDjzkwnYypKPmyAoaMhbD2dQHLU8g1Y2yumkQp3vaZXKEr_w8stztSCYdLVGc3h6YZzS0SItugH-eNOiR9-Se_hmTLSTMQo72XoUE2U_RV5Zy=w1200-h800-p-k-no', 'Castillo Medieval De Lamas', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [215] REC-00215 | CASCADAS DE MARAYSILLO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (215, 'https://www.turismoperuano.com/wp-content/uploads/cascadas-de-maraysillo-san-martin.jpg', 'Cascadas De Maraysillo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [216] REC-00216 | COMUNIDAD NATIVA KECHWA EL WAYKU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (216, 'https://lh5.googleusercontent.com/p/AF1QipMIHOwEQL_nGQQeY9GHbulYLtpOAeFgmQvTXOBx=w1200-h800-k-no', 'Comunidad Nativa Kechwa El Wayku', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [217] REC-00217 | FABRICA DE CHOCOLATES ORQUIDEA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (217, 'https://consultasenlinea.mincetur.gob.pe/fichaInventario/foto.aspx?cod=624260', 'Fabrica De Chocolates Orquidea', 'MINCETUR', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (217, 'https://www.kuritours.com/wp-content/uploads/2023/09/fabrica-la-orquidea-tarapoto.jpg', 'Fabrica De Chocolates Orquidea - Tienda Tarapoto', NULL, 'normal', FALSE, 2);
-- [218] REC-00218 | AREA DE CONSERVACION MUNICIPAL DE MARONILLA Y CHORROBAMBA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (218, 'https://upload.wikimedia.org/wikipedia/commons/b/bd/Camino_a_la_Cordillera_Escalera%2C_Tarapoto%2C_Per%C3%BA.jpg', 'Area De Conservacion Municipal De Maronilla Y Chorrobamba', 'Wikimedia Commons', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (218, 'https://www.turismoperuano.com/wp-content/uploads/area-de-conservacion-municipal-de-maronilla-y-chorrobamba-san-martin.jpg', 'Area De Conservacion Municipal De Maronilla Y Chorrobamba - Referencia local', NULL, 'normal', FALSE, 2);
-- [219] REC-00219 | ECOPARQUE LA SONADA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (219, 'https://lh5.googleusercontent.com/p/AF1QipOdmZQ9chRrj30n01SclmM3Kso_hrC3tQqs9oeJ=w1200-h800-k-no', 'Ecoparque La Sonada', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [220] REC-00220 | LAGUNA LAGARTOCOCHA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (220, 'https://portal.andina.pe/EDPfotografia/Thumbnail/2015/02/01/000279936W.jpg', 'Laguna Lagartococha', 'Agencia Andina', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (220, 'https://www.turismoperuano.com/wp-content/uploads/laguna-lagartococha-san-martin.jpg', 'Laguna Lagartococha - Referencia local', NULL, 'normal', FALSE, 2);
-- [221] REC-00221 | CASCADA EL SALTO DE LA BRUJA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (221, 'https://visitasanmartin.com/wp-content/uploads/2025/06/DJI_0902-1-scaled.jpg', 'Cascada El Salto De La Bruja', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [222] REC-00222 | BANOS TERMALES DE SAN JOSE
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (222, 'https://visitasanmartin.com/wp-content/uploads/2025/06/WhatsApp-Image-2024-06-25-at-11.06.27-AM.jpeg', 'Banos Termales De San Jose', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [223] REC-00223 | LAGUNA ANDIVIELA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (223, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2024/10/16/001108613W.jpg', 'Laguna Andiviela', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [224] REC-00224 | MIRADOR NATURAL ALTO SHILCAYO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (224, 'https://visitasanmartin.com/wp-content/uploads/2025/06/05.jpg', 'Mirador Natural Alto Shilcayo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [225] REC-00225 | CASCADAS DE TAMUSHAL - ALTO SHILCAYO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (225, 'https://www.turismoperuano.com/wp-content/uploads/cascadas-del-tamushal-san-martin.jpg', 'Cascadas De Tamushal - Alto Shilcayo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [226] REC-00227 | CASCADA DE JULIAN PAMPA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (226, 'https://www.turismoperuano.com/wp-content/uploads/cascada-de-julian-pampa-san-martin.jpg', 'Cascada De Julian Pampa', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [227] REC-00228 | PARQUE SUCHICHE
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (227, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-Ey69bIcFZzuVE6TnGcXcWbXZ9u6RsLElSTlPuh6PfaEUt9zWArAjWqOyZ-aYqQYc7-ncJCK-BzGnYm0yOeeVum0GdLw2nl3kuGYfvo6uX0xVELQQecDYsumYJ6z8TppL7l1-v=w1200-h800-p-k-no', 'Parque Suchiche', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [228] REC-00229 | FESTIVAL DE LA ORQUIDEA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (228, 'https://www.turismoperuano.com/wp-content/uploads/festival-de-la-orquidea-san-martin.jpg', 'Festival De La Orquidea', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [229] REC-00230 | FIESTAS TRADICIONALES DE SAN JUAN SAN PEDRO Y SAN PABLO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (229, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2023/06/23/000969465W.jpg', 'Fiestas Tradicionales De San Juan San Pedro Y San Pablo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [230] REC-00231 | FIESTA DE CORPUS CHRISTI EN MOYOBAMBA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (230, 'https://www.prelaturademoyobamba.com/wp-content/uploads/2023/06/corpus-moy-1-Copy.jpg', 'Fiesta De Corpus Christi En Moyobamba', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [231] REC-00232 | SEMANA TURISTICA DE MOYOBAMBA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (231, 'https://lh3.googleusercontent.com/-JKkfruz0uew/ZJFokj5iSMI/AAAAAAABMok/uc7dI-EWD-MtjAnBC2dwDkbblX8prNz0ACNcBGAsYHQ/w1200-h630-p-k-no-nu/276840-xlix-semana-turistica-moyobamba-programacion-oficial-fiesta-san-juan-2023-20-30.jpg=w1200-h800-k-no', 'Semana Turistica De Moyobamba', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (231, 'https://www.ytuqueplanes.com/imagenes//fotos/festividades/400x400/Semana_turistica_moyobamba_400.webp', 'Semana Turistica De Moyobamba - Y Tu Que Planes', NULL, 'normal', FALSE, 2);
-- [232] REC-00233 | LAGUNA ONERCOCHA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (232, 'https://scontent-lim1-1.cdninstagram.com/v/t51.82787-15/730837341_18593694508063070_7893208826972234779_n.jpg?stp=dst-jpegr_e35_tt6&_nc_cat=111&_nc_map=urlgen_bucketless&ig_cache_key=MzkyOTY0MTgzMDAwMDQ5NTYwMA%3D%3D.3-ccb7-5&ccb=7-5&_nc_sid=58cdad&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0ueHBpZHMuMzAyNC5oZHIucmVndWxhcl9waG90by5DMyJ9&_nc_ohc=6mYFkO4fLCMQ7kNvwG2s0Qh&_nc_oc=AdqjphKGrJ6mXJX5bjFWgVJ6ctcLKBpt-nFHQT4Y2rY9hh_Z9ctSURCTTvmyoX1h2m8&_nc_zt=23&_nc_ht=scontent-lim1-1.cdninstagram.com&_nc_gid=vokkly4IQisJDGkdhxLgpw&_nc_ss=7ba8c&_nc_ct=RQosPBUIFQIlAgAAAA&oh=00_AQSLpno0_XtUp9SM690cF-6HhiiPKeJgplpPQ88VDECFUA&oe=6B063EAD', 'Laguna Onercocha', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [233] REC-00234 | CASCADA DE LEJIAYACU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (233, 'https://i0.wp.com/viajarparavivir.com/wp-content/uploads/2019/03/5.-CATARATAS-DE-LEJIAYACU-DISTRITO-DE-JEPELACIO.FOTO-DE-CRONWELL-MACOY-ZAPATA-VELA-%40macoyzv-.jpg?ssl=1', 'Cascada De Lejiayacu', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [234] REC-00235 | RESERVA ECOLOGICA TINGANA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (234, 'https://tarapoto.com/s/img/wp-content/uploads/2020/06/tingana-1536x882.jpg', 'Reserva Ecologica Tingana', 'Google Maps', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [235] REC-00236 | PARQUE NACIONAL CORDILLERA AZUL
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (235, 'https://www.cima.org.pe/files/images/parque-nacional-cordillera-azul/.1500x445/seccion-parque-nacional-cordillera-azul.jpg', 'Parque Nacional Cordillera Azul', 'CIMA', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (235, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2022/12/12/000918542W.jpg', 'Parque Nacional Cordillera Azul - Andina', NULL, 'normal', FALSE, 2);
-- [236] REC-00237 | PARQUE NACIONAL RIO ABISEO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (236, 'https://tarapoto.com/wp-content/uploads/2020/07/parque-nacional-rio-abiseo.jpg', 'Parque Nacional Rio Abiseo', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [237] REC-00238 | CUEVA DE CASCAYUNGA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (237, 'https://cuevasdelperu.org/wp-content/gallery/cueva-de-cascayunga-fotos/p2270274.jpg', 'Cueva De Cascayunga', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [238] REC-00239 | COMPLEJO ARQUEOLOGICO EL GRAN PAJATEN
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (238, 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2023/09/13/000994198W.jpg', 'Complejo Arqueologico El Gran Pajaten', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [239] REC-00240 | NACIENTE DEL RIO TIOYACU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (239, 'https://consultasenlinea.mincetur.gob.pe/fichaInventario//foto.aspx?cod=643551', 'Naciente Del Rio Tioyacu', 'MINCETUR', 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [240] REC-00241 | CASCADA DE LAHUARPIA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (240, 'https://moyobamba.com/wp-content/uploads/2021/08/huarpia4.jpg', 'Cascada De Lahuarpia', NULL, 'normal', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
COMMIT;
