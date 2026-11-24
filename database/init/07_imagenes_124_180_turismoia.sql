-- ============================================================================
-- 07_imagenes_124_180_turismoia.sql
-- Imágenes normales REC-00124 a REC-00180
-- Fuente: database/TurismoIA_124_180.sql (56 registros)
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
    -- REC-00124 -> id_atractivo=124 (AGUAS TERMALES EL DORADO)
    ('REC-00124', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTvaCffy9q2kaJoitW1rCsluWyxhRhpCKZyOp4m693QyVuo2uNfXCNeHhO&s=10', 'Aguas termales el dorado — Moyobamba', 'normal', TRUE, 1),
    -- REC-00125 -> id_atractivo=125 (CASCADA LA COLCA)
    ('REC-00125', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRXhWmLGggnrthyYIeXdFWdOJifXfXlRdNp3pQE4GaoYOk7-Hp3TxytJRQ&s=10', 'Cascada la colca — Nueva Cajamarca', 'normal', TRUE, 1),
    -- REC-00126 -> id_atractivo=126 (NACIENTE DEL RIO NEGRO)
    ('REC-00126', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT5y_OTxLzZyd2uzKhPUpeKRu_DEDnYzOI-TbPLwhI8NyUcQDfFGO5CHe8&s=10', 'Naciente del rio negro — Elias Soplin Vargas', 'normal', TRUE, 1),
    -- REC-00127 -> id_atractivo=127 (SITIO ARQUEOLOGICO DE OCHANACHE)
    ('REC-00127', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR0UejxvTkls-Ku2xHrT39mNVhfcqqWkWT29dD9m5CEc5MUDz0ccC3NkH8&s=10', 'Sitio arqueologico de ochanache — Huicungo', 'normal', TRUE, 1),
    -- REC-00128 -> id_atractivo=128 (LAGUNA DE MASHUYACU)
    ('REC-00128', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRSMOY613b0a-jD0d4dSS1C7yHzp3_a9bgA0tU0zfvVHCjS19yeI10Wt0&s=10', 'Laguna de mashuyacu — Rioja', 'normal', TRUE, 1),
    -- REC-00129 -> id_atractivo=129 (MUSEO ETNO ARQUEOLOGICO DE PACHIZA)
    ('REC-00129', 'https://upload.wikimedia.org/wikipedia/commons/9/90/Museo_arqueologico_y_etnohistorico_de_pachiza.jpg?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original', 'Museo etno arqueologico de pachiza — Pachiza', 'normal', TRUE, 1),
    -- REC-00130 -> id_atractivo=130 (CATARATA MAQUISAPA)
    ('REC-00130', 'https://d1vv3l16eo9v1l.cloudfront.net/turismo/11120/390758.jpg', 'Catarata maquisapa — Huicungo', 'normal', TRUE, 1),
    -- REC-00132 -> id_atractivo=132 (CASCADA DE CAJANAHUI)
    ('REC-00132', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTI6r9yOXG3Cdg-OnOqZHa102hHN1WB9vA6dNP_yRKqpUaoyGvO0B1YePTq&s=10', 'Cascada de cajanahui — Huicungo', 'normal', TRUE, 1),
    -- REC-00133 -> id_atractivo=133 (CASCADA VICKY)
    ('REC-00133', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRIgYWJyHhls6ht0v8uQzhysK1DNYtB_rSzITIKx9PVkPElyktS7ovJ7Ff0&s=10', 'Cascada vicky — Huicungo', 'normal', TRUE, 1),
    -- REC-00134 -> id_atractivo=134 (MIRADOR FUNDO VAINILLA)
    ('REC-00134', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSdrOLFTY9WaeC9L3E9l1qD4nvKvYfKm_LFp_ylD6IjXTXXCz4TB9pP11s-&s=10', 'Mirador fundo vainilla — Huicungo', 'normal', TRUE, 1),
    -- REC-00135 -> id_atractivo=135 (CASCADA DE SHITARIYACU)
    ('REC-00135', 'https://www.turismoperuano.com/wp-content/uploads/cascada-de-shitariyacu-san-martin.jpg', 'Cascada de shitariyacu — Pachiza', 'normal', TRUE, 1),
    -- REC-00136 -> id_atractivo=136 (RAPIDOS DE OJOCOCHA)
    ('REC-00136', 'https://aprobocelbreo.wordpress.com/wp-content/uploads/2014/08/cropped-b0iii-1.jpg', 'Rapidos de ojococha — Huicungo', 'normal', TRUE, 1),
    -- REC-00137 -> id_atractivo=137 (RIO HUAYABAMBA)
    ('REC-00137', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAOcK8_qL8HMqlHw00vjUHLoEeXufoCC7wLK0MMtyh2Hl2hozXjzolNTXJ&s=10', 'Rio huayabamba — Huicungo', 'normal', TRUE, 1),
    -- REC-00138 -> id_atractivo=138 (COMPLEJO ARQUEOLOGICO LA GRAN SAPOSOA)
    ('REC-00138', 'https://www.pueblosoriginarios.com/sur/amazonia/chachapoya/imagenes/saposoa2.jpg', 'Complejo arqueologico la gran saposoa — Saposoa', 'normal', TRUE, 1),
    -- REC-00139 -> id_atractivo=139 (CUEVA DE ARMANAYACU)
    ('REC-00139', 'https://www.deperu.com/imagenes/afp/2016/4762ff7df781a5461fe740d722d34e42a803788c.jpg', 'Cueva de armanayacu — Saposoa', 'normal', TRUE, 1),
    -- REC-00140 -> id_atractivo=140 (AGUAS TERMALES DE SHIMA)
    ('REC-00140', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT-rgmy1rkgPJUoq-IRfUJ_sHLSVy4zAkIHjgDUFpjtW0v_mPbBfrcRFJc&s=10', 'Aguas termales de shima — Saposoa', 'normal', TRUE, 1),
    -- REC-00141 -> id_atractivo=141 (CASCADA DE NUEVO SAN ANDRES)
    ('REC-00141', 'https://www.chullostravelperu.com/blog/wp-content/uploads/2023/05/Cascada-de-Nuevo-San-Andres.jpg', 'Cascada de nuevo san andres — Saposoa', 'normal', TRUE, 1),
    -- REC-00142 -> id_atractivo=142 (CASCADA DE SHITARI)
    ('REC-00142', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTDbp2bEcH_VW7CeBPvTOeTaSFBw6kGvEF_iwxDYRJ-k04ZSJdC7afwDNnM&s=10', 'Cascada de shitari — Alto Saposoa', 'normal', TRUE, 1),
    -- REC-00143 -> id_atractivo=143 (CIUDADELA MAMAJ)
    ('REC-00143', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQfLwoNmoXaS8B9POuz2MWVF3QPrh_j4u373Sf8yDnJcWBkcF3dm7HAVk4S&s=10', 'Ciudadela mamaj — Shunte', 'normal', TRUE, 1),
    -- REC-00144 -> id_atractivo=144 (PETROGLIFO DE MONTECRISTO)
    ('REC-00144', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6eQKzf8Olo_qDxCeLxUpe2J_AJrABsY9OIgcb4QYlC9VKFsoQs3x_TZY&s=10', 'Petroglifo de montecristo — Shunte', 'normal', TRUE, 1),
    -- REC-00145 -> id_atractivo=145 (FIESTA PATRONAL DE SANTA ROSA)
    ('REC-00145', 'https://portal.andina.pe/EDPfotografia3/Thumbnail/2024/08/23/001093909W.webp', 'Fiesta patronal de santa rosa — Bellavista', 'normal', TRUE, 1),
    -- REC-00146 -> id_atractivo=146 (PETROGLIFOS DE MISHQUIYACU)
    ('REC-00146', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQBRpdJsWFrG8lKq5RrIMMA7G_JhQdaRbugiXrPBVxfPvywSY3Y_WS3w_4&s=10', 'Petroglifos de mishquiyacu — Bellavista', 'normal', TRUE, 1),
    -- REC-00147 -> id_atractivo=147 (CUEVA BOCA DEL TIGRE)
    ('REC-00147', 'https://cuevasdelperu.org/wp-content/gallery/cueva-del-tigre-perdido-fotos/img_20180226_093535.jpg', 'Cueva boca del tigre — Bellavista', 'normal', TRUE, 1),
    -- REC-00148 -> id_atractivo=148 (CAVERNA CATAHUA)
    ('REC-00148', 'https://www.deperu.com/imagenes/afp/2016/4762ff7df781a5461fe740d722d34e42a803788c.jpg', 'Caverna catahua — Bellavista', 'normal', TRUE, 1),
    -- REC-00149 -> id_atractivo=149 (CASCADA BOCA DEL SAPO)
    ('REC-00149', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSt3SYTjDChMAPYwAyMUXR_5uNRSTQmTv3OEr3BN_mMTXtwTPch4bBnbvIj&s=10', 'Cascada boca del sapo — San Pablo', 'normal', TRUE, 1),
    -- REC-00150 -> id_atractivo=150 (CASCADA DE SANANGOYACU)
    ('REC-00150', 'https://i.pinimg.com/736x/69/61/0d/69610d98f75feab922024dd092db8ad8.jpg', 'Cascada de sanangoyacu — San Pablo', 'normal', TRUE, 1),
    -- REC-00151 -> id_atractivo=151 (CASCADA DE PICUROYACU)
    ('REC-00151', 'https://leitoinntarapoto.com/media/tour/cascadas-de-pishurayacu-hgwwurnzvlkb-1.jpg', 'Cascada de picuroyacu — San Pablo', 'normal', TRUE, 1),
    -- REC-00152 -> id_atractivo=152 (CASCADA DE CHURILLO)
    ('REC-00152', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQqpLDgtfmD5ZtKjpTERvwUC2NQSDkUCr_rkXqNOaC-LpBklYR27E-TEp4&s=10', 'Cascada de churillo — Bellavista', 'normal', TRUE, 1),
    -- REC-00153 -> id_atractivo=153 (RIO HUALLAGA)
    ('REC-00153', 'https://upload.wikimedia.org/wikipedia/commons/9/99/Rio_huallaga%2C_Tarapoto%2C_San_Mart%C3%ADn%2C_Per%C3%BA.jpg?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original', 'Rio huallaga — Bellavista', 'normal', TRUE, 1),
    -- REC-00154 -> id_atractivo=154 (LAGUNA DE CHAUPICOCHA)
    ('REC-00154', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQrZnjWzg1eIesSzkuWLJL3NgtaE1j7qlx_JYyc6QFGx9bdEBkETA8sFEM&s=10', 'Laguna de chaupicocha — San Pablo', 'normal', TRUE, 1),
    -- REC-00155 -> id_atractivo=155 (LAGUNA DE SITULLICOCHA)
    ('REC-00155', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSQCJEyXfy2WmiZQkNzjEbUY7OSzanDkfEgsQyCjxv1aR68tn3TvsHIFP-X&s=10', 'Laguna de situllicocha — San Pablo', 'normal', TRUE, 1),
    -- REC-00156 -> id_atractivo=156 (LAGUNA DE SANGAMACOCHA.)
    ('REC-00156', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQrZnjWzg1eIesSzkuWLJL3NgtaE1j7qlx_JYyc6QFGx9bdEBkETA8sFEM&s=10', 'Laguna de sangamacocha — San Pablo', 'normal', TRUE, 1),
    -- REC-00157 -> id_atractivo=157 (CERRO SANGAPILLA)
    ('REC-00157', 'https://www.deperu.com/imagenes/afp/2014/5eb361ffe6f9148bb1e42c8d7fa7bc402f04dcc4.jpg', 'Cerro sangapilla — Bellavista', 'normal', TRUE, 1),
    -- REC-00158 -> id_atractivo=158 (MIRADOR ATUSPARIA)
    ('REC-00158', 'https://www.deperu.com/imagenes/afp/2014/5eb361ffe6f9148bb1e42c8d7fa7bc402f04dcc4.jpg', 'Mirador atusparia — Tocache', 'normal', TRUE, 1),
    -- REC-00159 -> id_atractivo=159 (CASCADA CHIAMPOY)
    ('REC-00159', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQYKdZindSdCBibZ9MUmRpL2xe8VEmbtD9O-Aw14HGWcs4fvCjcWNwY5fdP&s=10', 'Cascada chiampoy — Shunte', 'normal', TRUE, 1),
    -- REC-00160 -> id_atractivo=160 (CASCADA SALTO DEL MONO)
    ('REC-00160', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRch4Yza0pKjMhwdMrTvEjwhr76A4ApiE2eUiYUpOccR00WlgDdczvEHkY&s=10', 'Cascada salto del mono — Shunte', 'normal', TRUE, 1),
    -- REC-00161 -> id_atractivo=161 (CASCADA ZANCUDO)
    ('REC-00161', 'https://upload.wikimedia.org/wikipedia/commons/a/a8/CATARATA_SALTO_DEL_COTOMONO.jpg?utm_source=es.wikipedia.org&utm_campaign=index&utm_content=original', 'Cascada zancudo — Shunte', 'normal', TRUE, 1),
    -- REC-00162 -> id_atractivo=162 (CASCADA SAN JUAN DE ISHANGA)
    ('REC-00162', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMl7xiRgaMN6dNmxViPjKrdoZCK9b7QGxnaRV4ia1PJ0IsagYkGPl7Lkk&s=10', 'Cascada san juan de ishanga — Tocache', 'normal', TRUE, 1),
    -- REC-00163 -> id_atractivo=163 (CATARATA VELO DE PLATA)
    ('REC-00163', 'https://www.rumbosdelperu.com/wp-content/uploads/2020/10/c479703d-899a-41c9-bb36-cb5cdc91b138.jpg', 'Catarata velo de plata — Uchiza', 'normal', TRUE, 1),
    -- REC-00164 -> id_atractivo=164 (CASCADA LA NINFA)
    ('REC-00164', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTe3vwER990496sKbyRe5QYUa2HI2FyfnBLRhbYioVc5LM1ebAR8lBUIQhu&s=10', 'Cascada la ninfa — Tocache', 'normal', TRUE, 1),
    -- REC-00165 -> id_atractivo=165 (CASCADA TIESTO)
    ('REC-00165', 'https://pangoaturismo.wordpress.com/wp-content/uploads/2013/01/cascada-la-ninfa-_0011.jpg', 'Cascada tiesto — Tocache', 'normal', TRUE, 1),
    -- REC-00166 -> id_atractivo=166 (CASCADA SANTA CRUZ)
    ('REC-00166', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTIIEoORsK-QO3EeznfIgJ--A40RxN-Dhv6lPuyrXQwyZlnSLpeIhqfoQc&s=10', 'Cascada santa cruz — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00167 -> id_atractivo=167 (LAGUNA MADRE MIA)
    ('REC-00167', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRlA2mH7FoTyFIPlhCEz9xjy5zGDcKy6ZilqKhNZcAlogeK00Hz4WsAWH8&s=10', 'Laguna madre mia — Nuevo Progreso', 'normal', TRUE, 1),
    -- REC-00168 -> id_atractivo=168 (LAGUNA HUAYRANGA)
    ('REC-00168', 'https://dynamic-media-cdn.tripadvisor.com/media/photo-o/18/f6/76/ce/photo0jpg.jpg?w=1200&h=1200&s=1', 'Laguna huayranga — Tocache', 'normal', TRUE, 1),
    -- REC-00169 -> id_atractivo=169 (CATARATA DE SUNIPICAUSANI O TOROYACU)
    ('REC-00169', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXpD6gSS6vu31amNy2kHJzi8AMD_t9Pd59BS2ydqs9QST1j8Y8oiuUQyk&s=10', 'Catarata de sunipicausani o toroyacu — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00170 -> id_atractivo=170 (ATUNRUMI MAYOR)
    ('REC-00170', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTgT6VY5ywgVYHwTeIFpcRgYAcYoJDb5JmkyPhSS-o1Oq_9snArcmg6BMW3&s=10', 'Atunrumi mayor — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00171 -> id_atractivo=171 (ATUNRUMI CHICO DE YURACTIO)
    ('REC-00171', 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgM0yjijWKBO5aakBpxfiA_eMSAVrj_EZXnTQiTQdGhaKA0-0FkniSnH7CYEq-b4EQFSqyIeCFHeHjGyU07mpdQ_dnEMuYJEKgT4c10NuBurXRJiAI-g5NVwXiwRB3GMyXB4Dsafop4IHM/s1600/1174561_559108537482924_2043836147_n.jpg', 'Atunrumi chico de yuractio — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00172 -> id_atractivo=172 (CHOCOLATERIA PEPITAS DE CACAO)
    ('REC-00172', 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgM0yjijWKBO5aakBpxfiA_eMSAVrj_EZXnTQiTQdGhaKA0-0FkniSnH7CYEq-b4EQFSqyIeCFHeHjGyU07mpdQ_dnEMuYJEKgT4c10NuBurXRJiAI-g5NVwXiwRB3GMyXB4Dsafop4IHM/s1600/1174561_559108537482924_2043836147_n.jpg', 'Chocolateria pepitas de cacao — Lamas', 'normal', TRUE, 1),
    -- REC-00173 -> id_atractivo=173 (LA LAGUNA SECA)
    ('REC-00173', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRupWCQheR9n06Sj-DFkDNW5GS9pi-pQ5JrsJYOr9f8IXWVLyqSZAkVV1nb&s=10', 'La laguna seca — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00174 -> id_atractivo=174 (LA ISLA DEL AMOR Y JULIAN POZO)
    ('REC-00174', 'https://tarapoto.com/wp-content/uploads/2020/06/monzona.jpg', 'La isla del amor y julian pozo — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00175 -> id_atractivo=175 (CASCADA DE MISHQUIYACU)
    ('REC-00175', 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEi-rpB69ckSL4bI-btOrvupBRK4ATus9XFanhlMZMaLz1I3FMZQ7HkpgRY0sETcVVI0f99hGXcjQits8LweTNk2u5FV2FoeQNYD3fvH6mhemDYCQ0ZU3qfCB2lWw_aE6fDre3pMzy_JRqg/s1600/4481_94457675939_4688306_n.jpg', 'Cascada de mishquiyacu — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00176 -> id_atractivo=176 (POZA LA MONZONA)
    ('REC-00176', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRBoXHlfi2tUjrsCoqjL3OqGQiz67hgvMky-tboK-X3RPL3zVi6YjC_350&s=10', 'Poza la monzona — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00177 -> id_atractivo=177 (LA PAMPA)
    ('REC-00177', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR0FbYENHwpH-na4uPI0kmpOCZxdH5tMmhLMYBuYFp4DVf-drRzFFFd83k&s=10', 'La pampa — San Roque De Cumbaza', 'normal', TRUE, 1),
    -- REC-00178 -> id_atractivo=178 (URNAS FUNERARIAS DE CHAZUTA)
    ('REC-00178', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTS20dLm2S9djP-gbBcc_gHC44_yyzFHN4uO52e-XPB04KCGHKCa5fdO8Sp&s=10', 'Urnas funerarias de chazuta — Chazuta', 'normal', TRUE, 1),
    -- REC-00179 -> id_atractivo=179 (MINAS DE SAL DE PILLUANA)
    ('REC-00179', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMbZbsqL5bwb4ZaeplE3vqI4l_4Uiaep4bet5DfbqGMCG86nki1lyYsic_&s=10', 'Minas de sal de pilluana — Pilluana', 'normal', TRUE, 1),
    -- REC-00180 -> id_atractivo=180 (AGUAS TERMALES DON GRIMALDO)
    ('REC-00180', 'https://dynamic-media-cdn.tripadvisor.com/media/photo-o/08/14/03/22/termales-don-grimaldo.jpg?w=900&h=-1&s=1', 'Aguas termales don grimaldo — Sauce', 'normal', TRUE, 1)
) AS v(codigo_recurso, url, texto_alternativo, tipo, es_principal, orden)
JOIN turismo.atractivo a
  ON a.codigo_recurso = v.codigo_recurso
ON CONFLICT (id_atractivo, tipo) WHERE es_principal
DO NOTHING;

COMMIT;
