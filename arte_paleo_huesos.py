"""Huesos sueltos de los 30 animales (hasta 100 por animal).

El hueso k de un animal sale de su "kit": el grupo es k % 6 (craneo/dientes, cuello y columna, costillas, cola,
patas de adelante, patas de atras: igual que las 6 partes del esqueleto) y la variante es k // 6.
Cada familia (teropodo, saurisquio, marino, pez, volador, mamifero...) tiene sus piezas y cada animal anade
las suyas (cuernos, placas, maza, colmillos, dientes de megalodon, cresta...). Las piezas se dibujan una vez
(con sobremuestreo), se recortan y se guardan en cache.
"""

import math

import pygame

import arte_paleo_comun as C
from arte_paleo_comun import (Lienzo, spline, azar, HUESO, SOMBRA, HUESO_CLARO, HUESO_MEDIO, OSCURO)

TEROPODOS = ("velociraptor", "alosaurio", "carnotauro", "espinosaurio", "giganotosaurio", "tiranosaurio")
FAM = {}
for _i in TEROPODOS:
    FAM[_i] = "tero"
for _i in ("diplodoco", "braquiosaurio"):
    FAM[_i] = "sauro"
for _i in ("triceratops", "estegosaurio", "anquilosaurio", "parasaurolofo"):
    FAM[_i] = "herb"
for _i in ("plesiosaurio", "liopleurodon", "mosasaurio", "ictiosaurio"):
    FAM[_i] = "mar"
for _i in ("dunkleosteus", "megalodon"):
    FAM[_i] = "pez"
for _i in ("arqueopterix", "dimorfodonte", "ranforinco", "tapejara", "pteranodon", "quetzalcoatlus"):
    FAM[_i] = "aire"
for _i in ("smilodon", "gliptodonte", "megaloceros", "rinoceronte_lanudo", "megaterio", "mamut"):
    FAM[_i] = "mami"

BASE = {
    "tero": [["craneo", "diente_serr", "mandibula", "craneo", "diente_serr", "diente_serr"],
             ["vertebra", "vertebra_alta", "vertebra", "atlas", "vertebra_alta", "sacro"],
             ["costilla", "costilla_corta", "costilla", "gastralia", "costilla_larga", "esternon"],
             ["vertebra_cola", "chevron", "vertebra_cola", "vertebra_cola_chica", "chevron", "vertebra_cola"],
             ["omoplato", "humero", "mano", "garra", "radio", "falange"],
             ["femur", "tibia", "pelvis", "pie", "garra_g", "metatarso"]],
    "sauro": [["craneo", "diente_clavija", "mandibula", "craneo", "diente_clavija", "diente_clavija"],
              ["vertebra_larga", "vertebra_alta", "vertebra_larga", "atlas", "vertebra_alta", "sacro"],
              ["costilla_larga", "costilla", "costilla_larga", "esternon", "costilla", "costilla_corta"],
              ["vertebra_cola", "chevron", "vertebra_cola", "vertebra_cola_chica", "chevron", "vertebra_cola_chica"],
              ["omoplato", "humero", "radio", "pie", "falange", "garra_roma"],
              ["femur", "tibia", "pelvis", "pie", "metatarso", "garra_roma"]],
    "herb": [["craneo", "molar", "mandibula", "craneo", "molar", "molar"],
             ["vertebra", "vertebra_alta", "vertebra", "atlas", "vertebra_alta", "sacro"],
             ["costilla", "costilla_corta", "costilla", "gastralia", "costilla_larga", "esternon"],
             ["vertebra_cola", "chevron", "vertebra_cola", "vertebra_cola_chica", "chevron", "vertebra_cola"],
             ["omoplato", "humero", "radio", "pie", "falange", "garra_roma"],
             ["femur", "tibia", "pelvis", "pie", "rotula", "metatarso"]],
    "mar": [["craneo", "diente_cono", "mandibula", "craneo", "diente_cono", "diente_cono"],
            ["vertebra_disco", "vertebra", "vertebra_larga", "vertebra_disco", "vertebra_alta", "vertebra_disco"],
            ["costilla", "costilla_larga", "gastralia", "costilla_corta", "esternon", "costilla"],
            ["vertebra_cola", "chevron", "vertebra_cola", "radios", "vertebra_cola_chica", "chevron"],
            ["aleta", "humero", "aleta_mosaico", "aleta", "falange", "radio"],
            ["aleta", "femur", "aleta_mosaico", "falange", "pelvis", "aleta"]],
    "pez": [["craneo", "placa_dunkle", "mandibula", "placa_dunkle", "craneo", "placa_dunkle"],
            ["vertebra_pez", "vertebra_pez", "radios", "vertebra_pez", "vertebra_pez", "radios"],
            ["costilla_fina", "placa_dunkle", "costilla_fina", "costilla_fina", "placa_dunkle", "costilla_fina"],
            ["vertebra_pez", "radios", "vertebra_pez", "radios", "vertebra_pez", "radios"],
            ["aleta_pect", "radios", "placa_dunkle", "aleta_pect", "radios", "aleta_pect"],
            ["aleta_pect", "radios", "placa_dunkle", "aleta_pect", "radios", "aleta_pect"]],
    "aire": [["craneo", "diente_cono", "mandibula", "craneo", "cresta", "diente_cono"],
             ["vertebra_larga", "vertebra", "atlas", "vertebra_larga", "sacro", "vertebra"],
             ["costilla_fina", "esternon_quilla", "costilla_fina", "gastralia", "costilla_fina", "esternon_quilla"],
             ["vertebra_cola_larga", "vertebra_cola_chica", "chevron", "vertebra_cola_larga", "vertebra_cola_chica", "vertebra_cola_larga"],
             ["ala_hueso", "humero_hueco", "falange_alar", "ala_hueso", "garra", "falange_alar"],
             ["femur_hueco", "tibia", "pie", "metatarso", "pelvis", "garra"]],
    "mami": [["craneo", "molar", "mandibula", "craneo", "molar", "diente_cono"],
             ["vertebra", "vertebra_alta", "atlas", "vertebra", "sacro", "vertebra_alta"],
             ["costilla", "costilla_larga", "esternon", "costilla_corta", "costilla", "gastralia"],
             ["vertebra_cola", "chevron", "vertebra_cola_chica", "vertebra_cola", "chevron", "vertebra_cola_chica"],
             ["omoplato", "humero", "radio", "mano", "garra", "falange"],
             ["femur", "tibia", "pelvis", "pie", "rotula", "metatarso"]],
}
# piezas propias de cada animal (se anaden al grupo indicado)
ESP = {
    "triceratops": {0: ["cuerno", "gola", "cuerno"], 2: ["placa_hex"]},
    "estegosaurio": {1: ["placa", "placa", "placa"], 3: ["pua", "pua"]},
    "anquilosaurio": {0: ["cuerno"], 1: ["osteoderma", "osteoderma"], 3: ["maza", "maza"]},
    "parasaurolofo": {0: ["cresta", "cresta"]},
    "espinosaurio": {1: ["vela_espina", "vela_espina", "vela_espina"], 0: ["diente_cono"]},
    "carnotauro": {0: ["cuerno"]},
    "alosaurio": {0: ["cuerno_chico"]},
    "megalodon": {0: ["diente_mega", "diente_mega", "diente_mega", "diente_mega"], 1: ["diente_mega"]},
    "dunkleosteus": {0: ["mandibula_filo", "mandibula_filo"]},
    "plesiosaurio": {1: ["vertebra_larga", "vertebra_larga"]},
    "ictiosaurio": {0: ["pico_largo"]},
    "mosasaurio": {0: ["diente_cono", "pico_largo"]},
    "tapejara": {0: ["cresta_vela"]},
    "pteranodon": {0: ["pico_largo", "cresta"]},
    "quetzalcoatlus": {0: ["pico_largo"], 1: ["vertebra_larga", "vertebra_larga"]},
    "ranforinco": {3: ["rombo_cola"]},
    "dimorfodonte": {3: ["rombo_cola"]},
    "arqueopterix": {4: ["pluma"], 3: ["pluma"]},
    "smilodon": {0: ["colmillo_sable", "colmillo_sable"]},
    "gliptodonte": {2: ["placa_hex", "caparazon", "placa_hex"], 3: ["anillo"]},
    "megaloceros": {0: ["asta", "asta", "asta"]},
    "rinoceronte_lanudo": {0: ["cuerno", "cuerno"]},
    "megaterio": {4: ["garra_g", "garra_g"], 5: ["garra_g"]},
    "mamut": {0: ["colmillo", "colmillo", "colmillo"]},
}
GROSOR = {"tero": 1.0, "sauro": 1.3, "herb": 1.15, "mar": 1.0, "pez": 0.9, "aire": 0.7, "mami": 1.15}
TAM = {"diente_serr": 58, "diente_cono": 58, "diente_clavija": 60, "molar": 54, "diente_mega": 78, "vertebra": 66,
       "vertebra_alta": 76, "vertebra_larga": 84, "vertebra_disco": 62, "vertebra_cola": 58, "vertebra_cola_chica": 46,
       "vertebra_cola_larga": 72, "vertebra_pez": 60, "chevron": 62, "atlas": 64, "sacro": 100, "garra": 66, "garra_g": 84,
       "garra_roma": 60, "falange": 56, "rotula": 50, "pie": 84, "mano": 84, "metatarso": 92, "radio": 94,
       "costilla": 96, "costilla_corta": 78, "costilla_larga": 108, "costilla_fina": 100, "esternon": 90, "gastralia": 84,
       "omoplato": 100, "humero": 100, "humero_hueco": 100, "femur": 108, "femur_hueco": 108, "tibia": 104,
       "pelvis": 100, "mandibula": 104, "mandibula_filo": 96, "craneo": 104, "cuerno": 100, "cuerno_chico": 62,
       "colmillo": 110, "colmillo_sable": 100, "asta": 108, "cresta": 104, "cresta_vela": 96, "gola": 100, "placa": 90,
       "placa_hex": 64, "placa_dunkle": 84, "osteoderma": 64, "pua": 96, "maza": 84, "aleta": 104, "aleta_mosaico": 90,
       "aleta_pect": 96, "radios": 100, "ala_hueso": 110, "falange_alar": 100, "esternon_quilla": 84, "vela_espina": 100,
       "pico_largo": 108, "rombo_cola": 84, "pluma": 96, "caparazon": 100, "anillo": 84}


def kit(ident):
    fam = FAM[ident]
    grupos = [list(g) for g in BASE[fam]]
    for g, extra in ESP.get(ident, {}).items():
        grupos[g] = grupos[g] + extra
    if fam == "aire" and ident in ("tapejara", "pteranodon", "quetzalcoatlus"):
        grupos[0] = [("pico_largo" if x == "diente_cono" else x) for x in grupos[0]]
    return grupos


# ====================================================================== formas
def _col(r):
    j = r.randint(-9, 9)
    h = tuple(max(0, min(255, c + j)) for c in HUESO)
    s = tuple(max(0, min(255, c + j)) for c in SOMBRA)
    return (h, s)


def _claro(col):
    return (tuple(min(255, c + 12) for c in col[0]), col[1])


def poli(L, pts, col, **kw):
    L.poli(pts, hueso=col[0], sombra=col[1], **kw)


def cono_curvo(L, largo, base, curva, col, pto=(0, 0), ang0=0.0, anillos=0, punta=0.0):
    """Cono curvo (garra, colmillo, cuerno) desde pto; curva = giro total en radianes."""
    n = 14
    x, y = pto
    a = ang0
    c, d = [], []
    paso = largo / n
    for i in range(n + 1):
        s = i / n
        w = base * (1 - s) ** 0.85 + punta
        nx, ny = -math.sin(a), math.cos(a)
        c.append((x + nx * w, y + ny * w))
        d.append((x - nx * w, y - ny * w))
        x += math.cos(a) * paso
        y += math.sin(a) * paso
        a += curva / n
    poli(L, c + d[::-1], col)
    for k in range(anillos):
        s = (k + 1) / (anillos + 1)
        i = int(s * n)
        L.linea([c[i], d[i]], 2.0, (col[1], col[1]))
    return (x, y)


def f_vertebra(L, r, par, alto=1.0, ancho=1.0):
    col = par["col"]
    g = par["gr"]
    poli(L, [(-14 * ancho, 4), (-11 * ancho, -22 * alto), (0, -36 * alto), (11 * ancho, -22 * alto), (14 * ancho, 4)], col)
    L.elipse(-30 * ancho, -2, 11 * g, 7 * g, 0.3, hueso=col[0], sombra=col[1])
    L.elipse(30 * ancho, -2, 11 * g, 7 * g, -0.3, hueso=col[0], sombra=col[1])
    L.elipse(0, 14, 25 * g * ancho, 17 * g, 0.0, hueso=col[0], sombra=col[1])
    L.elipse(0, -8, 5, 7 * alto, hueso=OSCURO, sombra=(30, 24, 18), grosor=1.5)


def f_vertebra_alta(L, r, par):
    f_vertebra(L, r, par, alto=1.5)


def f_vertebra_larga(L, r, par):
    col = par["col"]
    g = par["gr"]
    poli(L, [(-24, -4), (-18, -26), (-4, -34), (14, -22), (26, -4)], col)
    L.elipse(0, 10, 44, 15 * g, 0.0, hueso=col[0], sombra=col[1])
    L.elipse(-40, 10, 9, 12 * g, hueso=col[0], sombra=col[1])
    L.elipse(40, 10, 9, 12 * g, hueso=col[0], sombra=col[1])
    for dx in (-20, 20):
        L.linea([(dx, 14), (dx + 6, 32)], 5 * g, col)


def f_vertebra_disco(L, r, par):
    col = par["col"]
    g = par["gr"]
    L.elipse(0, 0, 34 * g, 34 * g, hueso=col[0], sombra=col[1])
    L.elipse(0, 0, 24 * g, 24 * g, hueso=(col[1][0] + 18, col[1][1] + 18, col[1][2] + 18), sombra=col[1], grosor=1.6)
    L.elipse(0, 0, 11 * g, 11 * g, hueso=col[0], sombra=col[1], grosor=1.4)
    for k in range(8):
        a = k * math.pi / 4
        L.linea([(math.cos(a) * 13 * g, math.sin(a) * 13 * g), (math.cos(a) * 22 * g, math.sin(a) * 22 * g)], 1.4, (col[1], col[1]), )


def f_vertebra_pez(L, r, par):
    col = par["col"]
    L.elipse(0, 0, 32, 26, hueso=col[0], sombra=col[1])
    for k, rr in enumerate((22, 14, 7)):
        L.elipse(0, 0, rr, rr * 0.8, hueso=(col[1][0] + 10 * k, col[1][1] + 10 * k, col[1][2] + 10 * k) if k % 2 == 0 else col[0],
                 sombra=col[1], grosor=1.3)
    L.linea([(-34, 0), (-44, 0)], 6, col)


def f_atlas(L, r, par):
    col = par["col"]
    L.elipse(0, 0, 32, 26, hueso=col[0], sombra=col[1])
    L.elipse(0, -4, 14, 12, hueso=OSCURO, sombra=(30, 24, 18), grosor=1.5)
    L.elipse(0, 16, 8, 5, hueso=col[0], sombra=col[1], grosor=1.2)
    L.elipse(-26, -16, 8, 7, hueso=col[0], sombra=col[1])
    L.elipse(26, -16, 8, 7, hueso=col[0], sombra=col[1])


def f_sacro(L, r, par):
    col = par["col"]
    g = par["gr"]
    L.linea([(-48, 6), (48, 0)], 14 * g, col)
    for k in range(5):
        x = -42 + 21 * k
        poli(L, [(x - 6, 2), (x - 3, -22), (x + 3, -22), (x + 6, 0)], col)
        L.elipse(x, 8 - k * 1.2, 11, 12 * g, hueso=col[0], sombra=col[1], grosor=1.6)
    L.elipse(46, -2, 8, 14, hueso=col[0], sombra=col[1])


def f_vertebra_cola(L, r, par, k=1.0):
    col = par["col"]
    g = par["gr"]
    L.elipse(0, 8, 18 * k * g, 13 * k * g, hueso=col[0], sombra=col[1])
    poli(L, [(-8 * k, 0), (-4 * k, -24 * k), (4 * k, -24 * k), (8 * k, 0)], col)
    L.elipse(-24 * k, 4, 7 * k, 5 * k, 0.4, hueso=col[0], sombra=col[1])
    L.elipse(24 * k, 4, 7 * k, 5 * k, -0.4, hueso=col[0], sombra=col[1])
    L.elipse(0, -6, 3, 4, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def f_vertebra_cola_chica(L, r, par):
    f_vertebra_cola(L, r, par, 0.75)


def f_vertebra_cola_larga(L, r, par):
    col = par["col"]
    L.elipse(0, 4, 46, 8, hueso=col[0], sombra=col[1])
    L.elipse(-44, 4, 7, 8, hueso=col[0], sombra=col[1])
    L.elipse(44, 4, 7, 8, hueso=col[0], sombra=col[1])
    L.linea([(-20, 0), (-20, -14)], 3, col)
    L.linea([(20, 0), (20, -14)], 3, col)


def f_chevron(L, r, par):
    col = par["col"]
    g = par["gr"]
    L.linea([(-18, -28), (0, 30), (18, -28)], 8 * g, col)
    L.elipse(0, -28, 24, 7, hueso=col[0], sombra=col[1], grosor=1.5)
    L.elipse(0, -28, 6, 3, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def f_costilla(L, r, par, k=1.0, g0=6.0):
    col = par["col"]
    g = par["gr"]
    pts = spline([(-52 * k, 26), (-40 * k, -6), (-5 * k, -28), (34 * k, -22), (52 * k, 4)], 6)
    L.linea(pts, g0 * g, col)
    L.nudo((-52 * k, 26), g0 * 1.2 * g, col)
    L.elipse(-46 * k, 20, 7, 5, 0.7, hueso=col[0], sombra=col[1], grosor=1.4)


def f_costilla_corta(L, r, par):
    f_costilla(L, r, par, 0.75, 5.6)


def f_costilla_larga(L, r, par):
    f_costilla(L, r, par, 1.1, 6.5)


def f_costilla_fina(L, r, par):
    f_costilla(L, r, par, 1.0, 3.6)


def f_esternon(L, r, par):
    col = par["col"]
    poli(L, [(-46, 0), (-26, -14), (4, -8), (36, -12), (50, 0), (36, 12), (4, 8), (-26, 14)], col)
    L.linea([(-34, 0), (40, 0)], 1.6, (col[1], col[1]))
    for x in (-18, 6, 28):
        L.elipse(x, 0, 4, 3, hueso=col[1], sombra=col[1], grosor=1.0)


def f_esternon_quilla(L, r, par):
    col = par["col"]
    poli(L, [(-46, 10), (-30, -18), (10, -26), (46, -4), (40, 12), (0, 16)], col)
    L.linea([(-34, 12), (36, 12)], 4, col)
    L.linea([(-26, -14), (6, 12)], 1.6, (col[1], col[1]))


def f_gastralia(L, r, par):
    col = par["col"]
    for k in range(4):
        x = -40 + 26 * k
        L.linea([(x - 14, -22), (x, 4), (x + 14, -22)], 3.2, col)


def f_omoplato(L, r, par):
    col = par["col"]
    poli(L, [(-54, -4), (-30, -14), (24, -14), (50, -6), (56, 4), (44, 12), (-24, 12), (-54, 6)], col)
    L.elipse(46, 0, 14, 17, hueso=col[0], sombra=col[1])
    L.elipse(48, 1, 6, 8, hueso=OSCURO, sombra=OSCURO, grosor=1.0)
    L.linea([(-44, 0), (30, -3)], 1.8, (col[1], col[1]))


def hueso_largo(L, ln, g, col, curv=0.0, ext=1.0, tilt=0.0):
    pts = spline([(-ln / 2, 0), (0, curv), (ln / 2, tilt)], 6)
    L.linea(pts, g, col)
    for sx in (-1, 1):
        cx = sx * ln / 2
        cy = tilt if sx > 0 else 0
        L.nudo((cx, cy - g * 0.5 * ext), g * 0.95 * ext, col)
        L.nudo((cx, cy + g * 0.5 * ext), g * 0.85 * ext, col)


def f_femur(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 98, 11 * g, col, curv=r.uniform(-6, 6))
    L.nudo((-42, -17 * g), 9.5 * g, col)
    L.elipse(-34, -9 * g, 5, 8, hueso=col[0], sombra=col[1], grosor=1.2)


def f_femur_hueco(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 100, 9 * g, col, curv=r.uniform(-4, 4))
    L.elipse(46, 0, 3, 3, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def f_tibia(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 100, 8 * g, col, curv=r.uniform(-5, 5), ext=1.2)
    L.linea([(-40, -14), (-10, -6)], 4 * g, col)


def f_humero(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 84, 10 * g, col, curv=r.uniform(-4, 4), ext=1.1)
    poli(L, [(-30, -8), (-6, -22 * g), (8, -10)], col)


def f_humero_hueco(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 92, 9 * g, col, curv=2)
    L.elipse(-46, 0, 9, 14, hueso=col[0], sombra=col[1])
    L.elipse(-46, 0, 3.5, 7, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def f_radio(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 90, 6.5 * g, col, curv=r.uniform(-4, 4))


def f_metatarso(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 84, 7 * g, col, curv=1.0, ext=1.1)


def f_falange(L, r, par):
    col = par["col"]
    g = par["gr"]
    L.linea([(-22, 0), (22, 0)], 11 * g, col)
    for sx in (-1, 1):
        L.nudo((sx * 24, -6 * g), 7.5 * g, col)
        L.nudo((sx * 24, 6 * g), 7.5 * g, col)
    L.elipse(0, 0, 16, 5, hueso=col[1], sombra=col[1], grosor=0.5)


def f_falange_alar(L, r, par):
    col = par["col"]
    g = par["gr"]
    hueso_largo(L, 96, 5.5 * g, col, curv=0.0, ext=0.9)
    for x in (-24, 6, 30):
        L.nudo((x, 0), 3.6 * g, col)


def f_ala_hueso(L, r, par):
    col = par["col"]
    g = par["gr"]
    pts = spline([(-52, 6), (0, 0), (54, -8)], 6)
    L.linea(pts, 6.5 * g, col)
    L.nudo((-52, 6), 6.5 * g, col)
    L.nudo((54, -8), 4.5 * g, col)
    for x in (-18, 18):
        L.nudo((x, -2 if x < 0 else -4), 4.4 * g, col)
    L.linea([(-52, 6), (-40, 20)], 4 * g, col)
    poli(L, [(-40, 18), (-34, 28), (-46, 26)], _claro(col), grosor=1.2)


def f_garra(L, r, par, k=1.0):
    col = par["col"]
    cono_curvo(L, 62 * k, 13 * par["gr"] * k, r.uniform(0.9, 1.4), col, pto=(-30 * k, 16 * k), ang0=-0.6, anillos=2)
    L.elipse(-34 * k, 20 * k, 16 * k * par["gr"], 13 * k * par["gr"], hueso=col[0], sombra=col[1])
    L.elipse(-34 * k, 20 * k, 6 * k, 5 * k, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def f_garra_g(L, r, par):
    f_garra(L, r, par, 1.25)


def f_garra_roma(L, r, par):
    col = par["col"]
    poli(L, [(-24, -14), (14, -20), (32, -6), (32, 10), (14, 20), (-24, 14)], col)
    L.linea([(0, -10), (22, 0)], 1.8, (col[1], col[1]))
    L.linea([(0, 10), (22, 2)], 1.8, (col[1], col[1]))


def f_mano(L, r, par):
    col = par["col"]
    g = par["gr"]
    L.nudo((-34, 0), 11 * g, col)
    for k, (dx, dy) in enumerate(((46, -22), (52, -2), (46, 18))):
        L.linea([(-30, 0), (dx - 12, dy)], 6.5 * g, col)
        cono_curvo(L, 22, 6.5, 0.9, _claro(col), pto=(dx - 12, dy), ang0=math.atan2(dy, dx + 30) * 0.8, anillos=0)


def f_pie(L, r, par):
    col = par["col"]
    g = par["gr"]
    L.elipse(-26, 0, 20 * g, 17 * g, hueso=col[0], sombra=col[1])
    for dx, dy in ((46, -22), (52, 0), (46, 22)):
        L.linea([(-18, dy * 0.3), (dx - 14, dy)], 8 * g, col)
        poli(L, [(dx - 14, dy - 5), (dx + 6, dy + 1), (dx - 14, dy + 6)], _claro(col), grosor=1.3)


def f_rotula(L, r, par):
    col = par["col"]
    L.elipse(0, 0, 25, 20, 0.3, hueso=col[0], sombra=col[1])
    L.elipse(-3, -3, 12, 8, 0.3, hueso=_claro(col)[0], sombra=_claro(col)[1], grosor=1.2)


def f_pelvis(L, r, par):
    col = par["col"]
    poli(L, [(-52, -6), (-40, -28), (-6, -34), (30, -26), (50, -4), (36, 14), (12, 10), (6, 40), (-10, 44), (-16, 12), (-40, 12)], col)
    L.elipse(18, 2, 11, 11, hueso=OSCURO, sombra=OSCURO, grosor=1.4)
    L.linea([(-38, -14), (0, -22)], 1.6, (col[1], col[1]))


def f_diente_serr(L, r, par):
    col = par["col"]
    cr = (255, 252, 240), (222, 212, 186)
    poli(L, [(-17, 18), (-12, 44), (12, 44), (17, 18)], (col[1], col[1]))
    poli(L, [(-17, 20), (-9, -20), (4, -50), (12, -30), (17, 20)], cr)
    for k in range(5):
        y = -32 + k * 11
        poli(L, [(10 + k * 1.4, y), (16 + k * 1.2, y + 3), (11 + k * 1.2, y + 7)], cr, grosor=0.8)
    L.linea([(-4, 14), (0, -28)], 2.2, ((255, 255, 250), (255, 255, 250)))


def f_diente_cono(L, r, par):
    col = par["col"]
    cr = (255, 252, 240), (222, 212, 186)
    poli(L, [(-12, 14), (-10, 40), (10, 40), (12, 14)], (col[1], col[1]))
    poli(L, [(-13, 16), (-6, -22), (4, -46), (12, -20), (13, 16)], cr)
    L.linea([(-3, 10), (1, -30)], 2.0, ((255, 255, 250), (255, 255, 250)))


def f_diente_clavija(L, r, par):
    col = par["col"]
    cr = (255, 252, 240), (222, 212, 186)
    L.linea([(0, 38), (0, -10)], 15, (col[1], col[1]))
    poli(L, [(-11, 12), (-12, -18), (-4, -34), (4, -34), (12, -18), (11, 12)], cr)
    L.linea([(-4, 8), (-4, -22)], 2.0, ((255, 255, 250), (255, 255, 250)))


def f_molar(L, r, par):
    col = par["col"]
    cr = (252, 246, 228), (214, 202, 172)
    for dx in (-14, 14):
        poli(L, [(dx - 8, 12), (dx - 5, 42), (dx + 5, 42), (dx + 8, 12)], (col[1], col[1]))
    poli(L, [(-24, -12), (-18, -22), (18, -22), (24, -12), (26, 14), (-26, 14)], cr)
    for x in (-10, 0, 10):
        L.linea([(x, -18), (x - 2, 10)], 2.4, ((190, 176, 146), (190, 176, 146)))
    L.linea([(-20, -14), (20, -14)], 2.0, ((255, 255, 250), (255, 255, 250)))


def f_diente_mega(L, r, par):
    cr = (252, 246, 228), (214, 202, 172)
    poli(L, [(-34, 26), (-24, 48), (24, 48), (34, 26)], ((196, 180, 150), (160, 144, 114)))
    poli(L, [(-36, 30), (-18, -8), (0, -52), (18, -8), (36, 30)], cr)
    for k in range(7):
        y = 22 - k * 9
        xx = 34 - k * 2.6
        poli(L, [(xx, y), (xx + 3, y - 4), (xx - 1, y - 7)], cr, grosor=0.7)
        poli(L, [(-xx, y), (-xx - 3, y - 4), (-xx + 1, y - 7)], cr, grosor=0.7)
    L.linea([(-16, 22), (-2, -34)], 3.0, ((255, 255, 250), (255, 255, 250)))
    L.linea([(-30, 30), (30, 30)], 3, ((196, 180, 150), (160, 144, 114)))


def f_mandibula(L, r, par):
    col = par["col"]
    fam = par["fam"]
    L.linea(spline([(-56, 14), (-40, 4), (0, 10), (40, 12), (62, 6)], 6), 11 * par["gr"], col)
    poli(L, [(-58, 20), (-52, -18), (-34, -14), (-34, 10)], col)
    L.elipse(-40, 0, 5, 7, hueso=OSCURO, sombra=OSCURO, grosor=1.0)
    if fam in ("tero", "mar", "aire", "mami"):
        n = 8 if fam != "mami" else 5
        for k in range(n):
            x = -22 + 11 * k
            if fam == "mami":
                poli(L, [(x - 6, 6), (x - 4, -6), (x + 4, -6), (x + 6, 6)], (255, 252, 240), grosor=1.0)
            else:
                poli(L, [(x - 4, 7), (x + 4, 7), (x + 1, -6)], ((255, 252, 240), (222, 212, 186)), grosor=1.0)


def f_mandibula_filo(L, r, par):
    col = par["col"]
    poli(L, [(-50, 16), (-44, -8), (10, -22), (54, -6), (40, 14), (-10, 24)], col)
    poli(L, [(36, 8), (56, -28), (62, 6)], ((255, 252, 240), (222, 212, 186)))
    L.linea([(-34, 8), (28, -8)], 2.0, (col[1], col[1]))


def f_pico_largo(L, r, par):
    col = par["col"]
    L.linea(spline([(-56, 6), (0, 2), (58, 0)], 6), 9 * par["gr"] + 4, col)
    poli(L, [(-58, -14), (-40, -20), (-30, 4), (-52, 20), (-60, 8)], col)
    L.elipse(-44, -4, 7, 7, hueso=OSCURO, sombra=OSCURO, grosor=1.0)
    L.linea([(-20, 3), (50, 0)], 1.6, (col[1], col[1]))


def f_cuerno(L, r, par):
    col = par["col"]
    cono_curvo(L, 100, 17 * par["gr"], r.uniform(-0.4, 0.4), _claro(col), pto=(-50, 0), ang0=-0.05, anillos=3)
    L.elipse(-52, 0, 14, 22, hueso=col[0], sombra=col[1])


def f_cuerno_chico(L, r, par):
    col = par["col"]
    cono_curvo(L, 50, 14, 0.0, _claro(col), pto=(-24, 8), ang0=-0.9, anillos=2)
    L.elipse(-26, 10, 14, 10, hueso=col[0], sombra=col[1])


def f_colmillo(L, r, par):
    cono_curvo(L, 124, 12, 1.9, ((252, 246, 228), (214, 202, 172)), pto=(-52, 34), ang0=-0.4, anillos=0)


def f_colmillo_sable(L, r, par):
    cono_curvo(L, 98, 11, 0.5, ((255, 252, 240), (222, 212, 186)), pto=(-24, -46), ang0=1.28, anillos=0)
    L.elipse(-26, -48, 13, 9, hueso=par["col"][0], sombra=par["col"][1])


def f_asta(L, r, par):
    col = par["col"]
    L.linea(spline([(-46, 36), (-34, 6), (-12, -24)], 6), 9, col)
    for pts in (((-30, 4), (-52, -22), (-70, -30)), ((-20, -8), (-26, -40), (-34, -58)), ((-12, -24), (2, -52), (24, -62)),
                ((-12, -24), (20, -30), (44, -26)), ((-26, 20), (0, 8), (24, 12))):
        L.linea(spline(list(pts), 5), 6, col)
    poli(L, [(-10, -20), (14, -50), (30, -26), (10, -4)], _claro(col), grosor=1.4)
    L.elipse(-46, 38, 12, 8, hueso=col[0], sombra=col[1])


def f_cresta(L, r, par):
    col = par["col"]
    L.linea(spline([(-50, 24), (-30, -22), (14, -30), (52, -4)], 6), 17, col)
    L.linea(spline([(-48, 22), (-28, -20), (12, -28), (48, -4)], 6), 5, (_claro(col)[0], _claro(col)[0]))
    L.elipse(52, -4, 7, 7, hueso=OSCURO, sombra=OSCURO, grosor=1.2)


def f_cresta_vela(L, r, par):
    col = par["col"]
    poli(L, [(-46, 36), (-52, -4), (-30, -40), (10, -48), (44, -26), (46, 6), (30, 36)], col)
    for k in range(5):
        L.linea([(-24 + 14 * k, 34), (-30 + 16 * k, -30 + abs(k - 2) * 8)], 1.6, (col[1], col[1]))


def f_gola(L, r, par):
    col = par["col"]
    pts = []
    for i in range(30):
        a = 2 * math.pi * i / 30
        rr = 1 + 0.07 * math.sin(a * 11)
        pts.append((50 * rr * math.cos(a), 40 * rr * math.sin(a)))
    poli(L, pts, col)
    L.elipse(-18, -4, 11, 15, hueso=OSCURO, sombra=OSCURO, grosor=1.4)
    L.elipse(18, -4, 11, 15, hueso=OSCURO, sombra=OSCURO, grosor=1.4)
    for i in range(8):
        a = math.pi * 1.1 + i * 0.28
        L.elipse(44 * math.cos(a), 34 * math.sin(a), 4, 4, hueso=_claro(col)[0], sombra=col[1], grosor=1.0)


def f_placa(L, r, par):
    col = par["col"]
    poli(L, [(-24, 38), (-30, 0), (-12, -34), (4, -52), (16, -30), (30, 0), (24, 38)], col)
    for dx in (-10, 0, 10):
        L.linea([(dx, 32), (dx * 0.6, -26 + abs(dx))], 1.8, (col[1], col[1]))
    L.elipse(0, 36, 22, 7, hueso=col[0], sombra=col[1], grosor=1.4)


def f_vela_espina(L, r, par):
    col = par["col"]
    L.linea([(0, 46), (4, -50)], 7, col)
    L.elipse(0, 46, 14, 10, hueso=col[0], sombra=col[1])
    L.linea([(-2, 30), (-14, 10)], 3, col)
    L.linea([(2, 30), (16, 10)], 3, col)


def f_pua(L, r, par):
    col = par["col"]
    cono_curvo(L, 92, 16, 0.5, _claro(col), pto=(-46, 10), ang0=-0.25, anillos=2)
    L.elipse(-48, 12, 16, 12, hueso=col[0], sombra=col[1])


def f_osteoderma(L, r, par):
    col = par["col"]
    L.elipse(0, 8, 32, 24, hueso=col[0], sombra=col[1])
    poli(L, [(-14, 6), (0, -34), (14, 6)], _claro(col))
    L.elipse(0, 10, 22, 14, hueso=_claro(col)[0], sombra=col[1], grosor=1.2)


def f_placa_hex(L, r, par):
    col = par["col"]
    hexa = [(36 * math.cos(math.pi / 6 + k * math.pi / 3), 36 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    poli(L, hexa, col)
    poli(L, [(x * 0.62, y * 0.62) for x, y in hexa], _claro(col), grosor=1.4)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        L.linea([(math.cos(a) * 23, math.sin(a) * 23), (math.cos(a) * 36, math.sin(a) * 36)], 1.2, (col[1], col[1]))
    L.elipse(0, 0, 7, 7, hueso=col[0], sombra=col[1], grosor=1.2)


def f_caparazon(L, r, par):
    col = par["col"]
    pts = [(-46, 22), (-40, -8), (-14, -30), (22, -32), (46, -10), (50, 22)]
    poli(L, pts, col)
    for cx, cy in ((-24, -4), (2, -14), (28, -2), (-8, 12), (18, 14)):
        hexa = [(cx + 13 * math.cos(math.pi / 6 + k * math.pi / 3), cy + 13 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
        poli(L, hexa, _claro(col), grosor=1.4)


def f_anillo(L, r, par):
    col = par["col"]
    L.elipse(0, 0, 22, 40, hueso=col[0], sombra=col[1])
    L.elipse(0, 0, 11, 28, hueso=OSCURO, sombra=(30, 24, 18), grosor=1.6)
    for k in range(5):
        a = -1.2 + 0.6 * k
        L.elipse(-24 * math.cos(a) * 0.9, 34 * math.sin(a) * 0.9, 5, 5, hueso=_claro(col)[0], sombra=col[1], grosor=1.0)


def f_maza(L, r, par):
    col = par["col"]
    L.elipse(0, 0, 42, 32, 0.1, hueso=col[0], sombra=col[1])
    for dx, dy in ((-24, -14), (2, -22), (26, -8), (-26, 10), (2, 14), (-6, -2), (26, 14)):
        L.elipse(dx, dy, 8, 8, hueso=_claro(col)[0], sombra=col[1], grosor=1.4)


def f_aleta(L, r, par):
    col = par["col"]
    L.linea([(-48, 0), (-26, 0)], 10, col)
    L.nudo((-48, 0), 8, col)
    filas = [(-18, 3, 11), (2, 4, 10), (20, 4, 9), (36, 3, 8), (50, 2, 6)]
    for fx, n, rr in filas:
        for k in range(n):
            dy = (k - (n - 1) / 2) * (rr * 1.9)
            L.elipse(fx + abs(dy) * 0.15, dy, rr * 0.95, rr * 0.7, hueso=col[0], sombra=col[1], grosor=1.3)


def f_aleta_mosaico(L, r, par):
    col = par["col"]
    for i in range(4):
        for j in range(5):
            x = -40 + i * 26 + (j % 2) * 4
            y = -40 + j * 20
            L.elipse(x, y, 11, 8, hueso=col[0], sombra=col[1], grosor=1.3)


def f_aleta_pect(L, r, par):
    col = par["col"]
    L.linea([(-44, 10), (-20, 4)], 9, col)
    L.nudo((-44, 10), 7, col)
    for k, ang in enumerate((-0.5, -0.25, 0.0, 0.25, 0.5)):
        x2, y2 = -20 + 70 * math.cos(ang), 4 + 70 * math.sin(ang)
        L.linea([(-20, 4), (x2, y2)], 4.6, col)
        for u in (0.4, 0.7, 1.0):
            L.nudo((-20 + (x2 + 20) * u, 4 + (y2 - 4) * u), 3.4, col)


def f_radios(L, r, par):
    col = par["col"]
    L.elipse(-46, 0, 8, 8, hueso=col[0], sombra=col[1])
    for k in range(7):
        ang = -0.9 + k * 0.3
        x2, y2 = -46 + 100 * math.cos(ang), 100 * math.sin(ang)
        L.linea([(-46, 0), (x2, y2)], 3.4, col)
        for u in (0.5, 0.8):
            L.nudo((-46 + (x2 + 46) * u, y2 * u), 2.4, col)


def f_placa_dunkle(L, r, par):
    col = par["col"]
    poli(L, [(-46, 16), (-40, -18), (-6, -38), (36, -30), (52, 0), (30, 26), (-14, 30)], col)
    for k in range(4):
        L.linea(spline([(-36 + k * 6, 18 - k * 4), (-8 + k * 8, -4 - k * 4), (30, -22 + k * 8)], 5), 1.8, (col[1], col[1]))
    L.elipse(30, -6, 5, 5, hueso=_claro(col)[0], sombra=col[1], grosor=1.0)
    L.elipse(-24, 10, 5, 5, hueso=_claro(col)[0], sombra=col[1], grosor=1.0)


def f_rombo_cola(L, r, par):
    col = par["col"]
    L.linea([(-56, 0), (-10, 0)], 5, col)
    poli(L, [(-12, 0), (22, -24), (56, 0), (22, 24)], _claro(col))
    L.linea([(-10, 0), (56, 0)], 2.0, (col[1], col[1]))


def f_pluma(L, r, par):
    col = par["col"]
    L.linea([(-54, 18), (50, -14)], 4.0, col)
    pts = [(-46, 14)]
    for k in range(10):
        x = -40 + k * 9
        y = 14 - k * 3.1
        L.linea([(x, y), (x + 10, y + 24 - k * 0.5)], 2.6, (_claro(col)[0], col[1]))
        L.linea([(x, y), (x + 8, y - 16 + k * 0.6)], 2.0, (_claro(col)[0], col[1]))


FORMAS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith("f_") and callable(v)}


# ====================================================================== piezas listas
_cache = {}
_esc = {}


def _nombre(ident, k):
    grupos = kit(ident)
    g = k % 6
    lista = grupos[g]
    return lista[(k // 6) % len(lista)]


def _fabricar(ident, k):
    nombre = _nombre(ident, k)
    r = azar(ident, k, nombre)
    fam = FAM[ident]
    if nombre == "craneo":
        s = C.maestra(ident, 0)[0].copy()
    else:
        par = dict(col=_col(r), gr=GROSOR[fam] * r.uniform(0.92, 1.1), fam=fam)
        L = Lienzo(150, 150)
        FORMAS[nombre](L, r, par)
        rect = L.s.get_bounding_rect()
        rect.inflate_ip(6, 6)
        rect = rect.clip(L.s.get_rect())
        s = L.s.subsurface(rect).copy()
    mayor = max(s.get_width(), s.get_height()) / C.SS
    tam = TAM.get(nombre, 90) * r.uniform(0.92, 1.08)
    if nombre == "craneo":
        tam = 108
    f = tam / mayor / C.SS
    w, h = max(2, int(s.get_width() * f)), max(2, int(s.get_height() * f))
    s = pygame.transform.smoothscale(s, (w, h))
    giro = r.uniform(-0.45, 0.45) if nombre not in ("craneo",) else r.uniform(-0.1, 0.1)
    if r.random() < 0.5 and nombre not in ("craneo", "mandibula", "pico_largo", "aleta"):
        s = pygame.transform.flip(s, True, False)
    if abs(giro) > 0.02:
        s = pygame.transform.rotozoom(s, math.degrees(giro), 1.0)
    return s


def pieza(ident, k):
    clave = (ident, k)
    if clave not in _cache:
        _cache[clave] = _fabricar(ident, k)
    return _cache[clave]


def nombre_hueso(ident, k):
    return _nombre(ident, k)


def tamano_hueso(ident, k):
    s = pieza(ident, k)
    return s.get_size()


def dibujar_hueso(p, ident, k, x, y, escala=1.0, angulo=0.0):
    """El hueso numero k (0..99) suelto, centrado en (x, y)."""
    s = pieza(ident, k)
    if angulo == 0.0:
        q = max(1, round(escala * 20))
        ck = (ident, k, q)
        img = _esc.get(ck)
        if img is None:
            if q == 20:
                img = s
            else:
                img = pygame.transform.smoothscale(s, (max(1, int(s.get_width() * q / 20)), max(1, int(s.get_height() * q / 20))))
            if len(_esc) > 600:
                _esc.clear()
            _esc[ck] = img
    else:
        img = pygame.transform.rotozoom(s, -math.degrees(angulo), escala)
    p.blit(img, img.get_rect(center=(int(x), int(y))))
