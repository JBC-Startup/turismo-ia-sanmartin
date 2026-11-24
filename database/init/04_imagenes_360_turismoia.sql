SET client_encoding = 'UTF8';
SET search_path TO turismo, public;
BEGIN;
-- =====================================================================
-- Imágenes panorámicas 360° principales (tipo = 360) para atractivos 180 a 240
-- Cada INSERT está en una sola línea, comentado con el ID, código y nombre del lugar.
-- =====================================================================
-- [180] REC-00180 | AGUAS TERMALES DON GRIMALDO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (180, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U8OKV4TNi0RjXRI-3-XiLQvLiPURqlxCe-7H5c0P22eU6fMLrtAvKJbCcEle8gk0pf4no2XiXv0OiSyMxCELPqufVMEml_vBycyCKSRwS0BmiEbm42KCP6456Ehwg8uI-7-DDvWdg=w4096-h2048-k-no', 'Vista 360° de Aguas Termales Don Grimaldo', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [182] REC-00182 | BANOS TERMALES MEDICINALES DE PAUCARYACU BANOS TERMALES DE PAUCARYACU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (182, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-k1DuHdySmCqiZ-cReKVTa6_S_GpDF41Hwaia2MHWn_7vduGoOC-E8u9PpsOJWGl7OocVN5d_lc1OtGcnGJChzA9dRYlzBTDzo-QgFoNxPx7ALzPulv2RdY70ajpGQt1afN9kc=w4096-h2048-k-no', 'Vista 360° de Banos Termales Medicinales De Paucaryacu Banos Termales De Paucaryacu', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [188] REC-00188 | CUEVA DEL OTORONGO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (188, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U9uVVnMNRembywxiVXcnk-XrhLwOTE9_STd-61Jkav-qiA7sAjcqA8BEFgFd9IoUfRFfWFK_ffwla8_luXXPD45QCn1na9wYD2XSzA7XwH7q54GgQVVoLCbeKC7Py2jqVOlWB7PmpCIOME7=w4096-h2048-k-no', 'Vista 360° de Cueva Del Otorongo', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [192] REC-00192 | PLAZA DE ARMAS DE JUANJUI
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (192, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_BcOjBqrD_MaeU8B0xTYMZ9T0647eCDOZBTpEhNzk31Ir6PSzrFCdFW30EHrJc4EJlT5gYTvwuh17mX2t6rrA7n1g4-993xfsoFYqHcU6rgOodjGfDb3Id2CrC2gPl0V5IgoIk=w4096-h2048-k-no', 'Vista 360° de Plaza De Armas De Juanjui', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [196] REC-00196 | CUEVA DE PALESTINA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (196, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U8xOGFkOTDTvJrDiphhOspYLYz99TyAOBrhkUpiLDdSpH2OEzJiImIL3kI1BIyjqEt3i-eHxA9NgYzs_7AMiVnoIeYrYMZRu8NC7fhfgtkAhauih9_Ty91uRaGkITgK1DFTXesh=w4096-h2048-k-no', 'Vista 360° de Cueva De Palestina', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [201] REC-00201 | RIO MAYO SECTOR JUAN ANTONIO - TAHUISHCO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (201, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_jwog8ESxnYdeAPzjimIXmivuQNidOn4mLnY6njS4xiJjevFfuWF5fGvE-124vzcVqSCCSWUcRmjJ8YEo3jT-Aowjq7rgHIzGnKdi-SlfXsjoo0jW37E46FoUV-QC4bfB29WzuKQ=w4096-h2048-k-no', 'Vista 360° de Rio Mayo Sector Juan Antonio - Tahuishco', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [204] REC-00204 | MIRADOR ALTOMIRA - SAPOSOA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (204, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-ggSlI-DDWxK4POFoNw_W1s-tiC11yK7k-AlPMbDfXQCJsTb7Pq3OO6l77eLxxBQzkzmAAIHvs24oUHtxCnCCexGmxUyrxHSUtamQ93YHDcVUq95zvzlOz-BOin9nPjyLtAUAt=w4096-h2048-k-no', 'Vista 360° de Mirador Altomira - Saposoa', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [206] REC-00206 | CHU CHU CENTER
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (206, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U98B_lfaIuTry3LMTxHCTV_xIbLz6GeLVG0t34f-Sr_6mGteMFp5X53AsGHyB4VzA_ASsBsQqqAob1ihH2Cmn89eQ9BJLTNNkJDR6H13oNDQh9DxP95rkEi1vFpf5IA8shWRdcb=w4096-h2048-k-no', 'Vista 360° de Chu Chu Center', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [208] REC-00208 | VIVERO ORQUIDEAS AMAZONICAS
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (208, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-jAKFrOtFWpzkZjk1DeZ5MlNlDfyjhEtCiJ3m50MeHK3ZApq5q32FXQeEMnmv9-LXcD3H0OcjU6bWRJEqapfAuOZo6zM_3uB2GCOJtVf1Ab7qGEB3wxLTRZyAZ5bFrdB7Xfk9o=w4096-h2048-k-no', 'Vista 360° de Vivero Orquideas Amazonicas', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [209] REC-00209 | LAS PAMPAS DEL OLVIDO
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (209, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U___R8F5srb4ld-_VyxLrybBzEBTWZ-ajUiNwMznArlW6GmcV2DCdedSyRiWbEM-Ia0H2hhgRSqaRPDWmxPty6BPoq-7noZ3B2WKJRiI9X5AszUj1441Qwhi4rDZxxgVn72Fcyx=w4096-h2048-k-no', 'Vista 360° de Las Pampas Del Olvido', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [214] REC-00214 | CASTILLO MEDIEVAL DE LAMAS
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (214, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_aeXPUzcaXEcyWM2el3J_Oo4aBDjzkwnYypKPmyAoaMhbD2dQHLU8g1Y2yumkQp3vaZXKEr_w8stztSCYdLVGc3h6YZzS0SItugH-eNOiR9-Se_hmTLSTMQo72XoUE2U_RV5Zy=w4096-h2048-k-no', 'Vista 360° de Castillo Medieval De Lamas', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [216] REC-00216 | COMUNIDAD NATIVA KECHWA EL WAYKU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (216, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U90rABHN4UCCaq34XE6Oje6Avk-PmJN-GLZZ10MX9xbTCxri74PtEui1pCvlBFDlWAWQX3n8vgq_HCufNH13K8dW-XFEsw8TVEmKyiNux9AOle2UxxsOEuZLs_IBZ1uVpRHVAg3kA=w4096-h2048-k-no', 'Vista 360° de Comunidad Nativa Kechwa El Wayku', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [227] REC-00228 | PARQUE SUCHICHE
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (227, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U-Ey69bIcFZzuVE6TnGcXcWbXZ9u6RsLElSTlPuh6PfaEUt9zWArAjWqOyZ-aYqQYc7-ncJCK-BzGnYm0yOeeVum0GdLw2nl3kuGYfvo6uX0xVELQQecDYsumYJ6z8TppL7l1-v=w4096-h2048-k-no', 'Vista 360° de Parque Suchiche', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [233] REC-00234 | CASCADA DE LEJIAYACU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (233, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_lSzhRlHWac-1B7PcC6w7H5_3vks43_jI2FVo7V0Q74k5z9Cumz_1NrzNLPmiovlOgjZ9UfPHF_4bYthH_LWdYEZRJWRW4XsvaYniO4sA3c7vHDAYrwSNgQXRKW08pqPv_jhM=w4096-h2048-k-no', 'Vista 360° de Cascada De Lejiayacu', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [234] REC-00235 | RESERVA ECOLOGICA TINGANA
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (234, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_H_osP4RT2q2ZMfH5R1XmJbev5DJq6zpsHyegD2Oewje8w6Lmv4_3GUy9GZd7D_h3O5JWTCiiUogfQmg2-5RKnMMUfD2EqIfKCwNRrF4sBKmm8P4nQdTdaL0ROJz3Mp12bptaW=w4096-h2048-k-no', 'Vista 360° de Reserva Ecologica Tingana', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
-- [239] REC-00240 | NACIENTE DEL RIO TIOYACU
INSERT INTO turismo.atractivo_imagen (id_atractivo, url, texto_alternativo, credito, tipo, es_principal, orden)
VALUES (239, 'https://lh3.googleusercontent.com/gpms-cs-s/AM4Q-U_CNuwI222gJZDBYjyDgEOCfFTvaSGeY1WXMHdRQ0quS_XpQRGt6CG0I3aPKq-HnGec8IYz53j20bmemK-QvJLGCimTzhW26CTiHceBFU_mCj7wYurXGAGkiVWeXstxNRlIaGcrGznBUXY=w4096-h2048-k-no', 'Vista 360° de Naciente Del Rio Tioyacu', 'Google Maps', '360', TRUE, 1) ON CONFLICT (id_atractivo, tipo) WHERE es_principal DO UPDATE SET url = EXCLUDED.url, texto_alternativo = EXCLUDED.texto_alternativo, credito = EXCLUDED.credito;
COMMIT;
