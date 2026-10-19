"""Animales de tierra de arte_paleo (teropodos, hadrosaurio, saurisquio de cuello largo y mamiferos de la era de hielo).

Misma idea que arte_dinos: una sola geometria (GEO) sirve para el animal vivo y para su esqueleto.
Los 6 dinosaurios originales (tiranosaurio, velociraptor, triceratops, estegosaurio, braquiosaurio, anquilosaurio)
se dibujan con arte_dinos; aqui estan los 12 nuevos de tierra.

Cabezas: lista de grupos (clave de color, primitivas, blando). Claves: b = color del cuerpo, c = mas claro,
m = marfil, o = oscuro. `blando` = tejido que no sale en el craneo (trompa, orejas).
Primitivas: ("p", pts) poligono, ("e", (cx, cy), rx, ry, rot), ("c", (cx, cy), r), ("k", pts, radios) cadena.
"""

import math

import pygame

import arte_paleo_comun as C
from arte_paleo_comun import (aclarar, oscurecer, spline, largo, en, rot, elipse_pts, cadena, Lienzo, Pincel, HUESO,
                              SOMBRA, OSCURO, W, SIL_COLOR, CONTORNO_VIVO, OJO_OSC, HUESO_CLARO, HUESO_MEDIO)

V = pygame
CAJA = (560, 440)
FV = 0.92
MARFIL = (250, 244, 222)


# ====================================================================== cabezas
def _g(clave, prims, blando=False):
    return (clave, prims, blando)


def _tri(a, b, c):
    return ("p", [a, b, c])


def ANTLER(bx, by, ang, k):
    """Cornamenta palmeada enorme: una palma con puas gruesas en abanico (coordenadas de la cabeza)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def r(q):
        return (bx + (q[0] - bx) * ca - (q[1] - by) * sa, by + (q[0] - bx) * sa + (q[1] - by) * ca)
    pr = []
    pc = (bx - 4, by - 30)
    pr.append(("k", [r((bx, by)), r((bx - 4, by - 14)), r(pc)], [8, 8, 9]))
    pr.append(("e", r(pc), 26 * k, 17 * k, ang - 0.2))
    for a, l in ((-1.2, 62), (-0.7, 82), (-0.2, 90), (0.3, 82), (0.8, 64), (1.25, 42)):
        a2 = a + ang
        base = r(pc)
        mid = (base[0] + l * 0.55 * math.sin(a2), base[1] - l * 0.55 * math.cos(a2))
        tip = (base[0] + l * math.sin(a2 + 0.12), base[1] - l * math.cos(a2 + 0.12))
        pr.append(("k", [base, mid, tip], [9 * k, 7 * k, 2.4]))
    return pr


HEADS = {
    "allo": dict(
        grupos=[_g("m", [_tri((-20, -24), (-10, -40), (2, -24)), _tri((2, -26), (12, -38), (20, -24))]),
                _g("b", [("p", [(-40, 8), (-20, 8), (50, 4), (48, 14), (20, 24), (-14, 26), (-38, 22)])]),
                _g("b", [("p", [(-46, -4), (-40, -24), (-14, -32), (10, -28), (32, -22), (54, -12), (58, -2), (50, 4),
                                (-20, 8), (-44, 8)])])],
        ojo=(-10, -12, 9), nariz=(46, -10), boca=((52, 3), (-14, 8)), dientes=[(-14, 48, 4, 7, 10)], mej=(-4, 14)),
    "carno": dict(
        grupos=[_g("m", [_tri((-22, -28), (-14, -58), (-2, -28)), _tri((4, -30), (18, -54), (24, -28))]),
                _g("b", [("p", [(-40, 10), (-20, 10), (40, 10), (40, 22), (14, 30), (-14, 30), (-38, 24)])]),
                _g("b", [("p", [(-44, -8), (-38, -28), (-12, -34), (14, -30), (36, -20), (50, -6), (50, 6), (40, 10),
                                (-20, 10), (-44, 10)])])],
        ojo=(-10, -12, 9), nariz=(42, -8), boca=((48, 8), (-14, 10)), dientes=[(-8, 44, 8, 6, 9)], mej=(-2, 18)),
    "espino": dict(
        grupos=[_g("o", [_tri((-8, -22), (6, -36), (30, -20))]),
                _g("b", [("p", [(-30, 8), (-20, 8), (70, 6), (80, 6), (74, 15), (30, 21), (-10, 23), (-28, 19)])]),
                _g("b", [("p", [(-36, -6), (-30, -22), (-10, -26), (14, -20), (44, -14), (72, -9), (84, -4), (84, 4),
                                (74, 7), (-20, 8), (-36, 8)])]),
                _g("c", [("e", (82, -4), 8, 8, 0)])],
        ojo=(-14, -10, 8), nariz=(80, -8), boca=((82, 6), (-10, 9)), dientes=[(30, 76, 7, 7, 7)], mej=(-8, 14)),
    "giga": dict(
        grupos=[_g("m", [_tri((-8, -28), (2, -40), (14, -26))]),
                _g("b", [("p", [(-42, 8), (-20, 8), (60, 4), (64, 14), (36, 24), (-12, 26), (-40, 22)])]),
                _g("b", [("p", [(-48, -6), (-42, -26), (-12, -34), (16, -30), (42, -22), (64, -12), (68, -2), (60, 5),
                                (-20, 8), (-46, 8)])])],
        ojo=(-12, -14, 9), nariz=(58, -10), boca=((62, 4), (-14, 8)), dientes=[(-14, 58, 5, 8, 9)], mej=(-6, 14)),
    "para": dict(
        grupos=[_g("b", [("k", [(14, -24), (-6, -44), (-44, -58), (-84, -54), (-106, -38)], [9, 9, 8, 7, 6])]),
                _g("c", [("k", [(10, -27), (-8, -43), (-44, -55), (-82, -52)], [3, 3, 2.5, 2])]),
                _g("b", [("p", [(-30, 8), (-24, 4), (30, 12), (56, 14), (66, 8), (68, 0), (62, -8), (40, -16), (0, -24),
                                (-24, -18), (-32, -4)])]),
                _g("c", [("p", [(-24, 6), (30, 14), (56, 16), (60, 24), (28, 26), (-18, 24)])])],
        ojo=(0, -8, 9), nariz=(50, -6), boca=((64, 10), (-10, 12)), dientes=[], mej=(-8, 12), ojo_ref="para"),
    "diplo": dict(
        grupos=[_g("b", [("p", [(-24, 4), (-20, -14), (-2, -22), (20, -20), (38, -12), (56, -4), (62, 4), (56, 12),
                                (20, 14), (-10, 16), (-24, 12)])]),
                _g("c", [("p", [(18, 6), (58, 6), (54, 12), (20, 14)])])],
        ojo=(-6, -8, 7), nariz=(54, -2), boca=((60, 7), (-4, 14)), dientes=[(30, 56, 5, 4, 5)], mej=(-8, 10)),
    "smilo": dict(
        grupos=[_g("b", [_tri((-26, -24), (-30, -48), (-8, -32)), _tri((-6, -30), (4, -48), (14, -28))]),
                _g("m", [_tri((24, 4), (37, 4), (31, 58)), _tri((12, 6), (22, 6), (18, 44))]),
                _g("b", [("p", [(-36, 6), (-20, 18), (10, 22), (34, 20), (44, 12), (40, 4), (-20, 4)])]),
                _g("b", [("p", [(-38, 2), (-34, -22), (-10, -34), (16, -30), (36, -16), (46, -2), (44, 8), (30, 14),
                                (-20, 16), (-38, 12)])]),
                _g("c", [("e", (34, 6), 12, 9, 0)])],
        ojo=(-2, -10, 9), nariz=(46, -4), boca=((38, 10), (4, 14)), dientes=[], mej=(-14, 8)),
    "glipto": dict(
        grupos=[_g("b", [("e", (6, 4), 38, 28, 0.1)]),
                _g("b", [("e", (38, 12), 22, 17, 0.25)]),
                _g("m", [("e", (0, -12), 16, 7, 0.2)])],
        ojo=(10, -4, 8), nariz=(54, 8), boca=((54, 16), (22, 18)), dientes=[], mej=(0, 14)),
    "megal": dict(
        grupos=[_g("n", ANTLER(10, -22, 0.55, 0.95)),
                _g("m", ANTLER(-10, -24, -0.1, 1.0)),
                _g("b", [("e", (-34, -26), 11, 22, 0.5)], True),
                _g("b", [("p", [(-30, -10), (-24, -24), (0, -26), (26, -18), (52, -8), (64, 2), (60, 12), (32, 16),
                                (-6, 18), (-28, 12)])]),
                _g("c", [("e", (34, 8), 24, 7, 0.1)])],
        ojo=(-6, -10, 7), nariz=(58, 2), boca=((62, 10), (8, 15)), dientes=[], mej=(-10, 10)),
    "rino": dict(
        grupos=[_g("m", [("p", [(40, -10), (68, -10), (74, -34), (86, -66), (70, -52), (54, -32)])]),
                _g("m", [("p", [(12, -18), (30, -18), (30, -36), (20, -30)])]),
                _g("b", [_tri((-30, -22), (-34, -46), (-12, -26))]),
                _g("b", [("p", [(-36, -12), (-28, -26), (0, -28), (32, -18), (56, -6), (68, 6), (62, 20), (34, 26),
                                (0, 26), (-30, 20)])]),
                _g("c", [("e", (48, 14), 18, 8, 0)])],
        ojo=(10, -8, 8), nariz=(62, 2), boca=((64, 18), (14, 22)), dientes=[], mej=(0, 14)),
    "megat": dict(
        grupos=[_g("o", [_tri((-22, -22), (-26, -42), (-6, -28))]),
                _g("b", [("p", [(-36, 4), (-32, -20), (-10, -32), (16, -30), (36, -16), (50, -2), (52, 10), (38, 22),
                                (0, 26), (-28, 20)])]),
                _g("c", [("e", (32, 6), 22, 15, 0.1)])],
        ojo=(8, -10, 9), nariz=(50, 0), boca=((46, 16), (12, 20)), dientes=[], mej=(-8, 12)),
    "mamut": dict(
        grupos=[_g("m", [("k", [(22, 20), (56, 52), (96, 40), (110, 6), (98, -26)], [9, 8, 6, 4, 2]),
                         ("k", [(30, 14), (62, 44), (92, 32), (100, 6)], [6, 5, 3.5, 2])]),
                _g("b", [("k", [(26, -6), (44, 14), (52, 44), (50, 74), (38, 96), (22, 98)], [19, 16, 14, 13, 12, 10])], True),
                _g("c", [("e", (-18, 4), 24, 34, 0.15)], True),
                _g("b", [("p", [(-44, 6), (-40, -30), (-14, -52), (16, -52), (38, -30), (44, -6), (36, 22), (6, 34),
                                (-28, 28)])]),
                _g("b", [("e", (6, -52), 22, 10, 0.0)], True)],
        ojo=(26, -4, 8), nariz=None, boca=((40, 26), (22, 36)), dientes=[], mej=(14, 24)),
}


# ====================================================================== especificaciones de los animales
def _ges(**kw):
    return kw


ESPEC = {
    "alosaurio": dict(
        color=(238, 150, 58), zoom=1.0,
        geo=dict(craneo=(148, -66, "allo", 1.0, 0.08),
                 cuello=[(106, -56), (86, -50), (68, -38), (54, -28)],
                 lomo=[(54, -28), (24, -36), (-10, -38), (-40, -32), (-62, -24)],
                 cola=[(-62, -24), (-110, -26), (-155, -14), (-195, 6), (-215, 30)],
                 costillas=(6, 44, -16, 52), pelvis=(-55, -20, 26, 19),
                 brazos=[[(60, -4), (78, 14), (98, 8)]], dedos_b=[(14, 8), (12, -2), (8, 12)],
                 patas=[[(-55, -18), (-16, 32), (-58, 76)]], dedos_p=[(42, 30), (30, 34), (16, 36), (-12, 24)],
                 desfase=(22, -3)),
        vivo=dict(torso=(78, 42, 0), cuello=(18, 30), cola=(30, 3), pata=(25, 16, 10), brazo=(11, 8, 6), cabeza=1.25,
                  manchas_pelo=True),
        extras=[]),
    "carnotauro": dict(
        color=(206, 76, 104), zoom=1.0,
        geo=dict(craneo=(148, -62, "carno", 1.0, 0.1),
                 cuello=[(108, -52), (88, -50), (70, -40), (56, -30)],
                 lomo=[(56, -30), (24, -42), (-12, -42), (-42, -34), (-64, -26)],
                 cola=[(-64, -26), (-112, -28), (-156, -16), (-194, 4), (-212, 28)],
                 costillas=(6, 46, -18, 58), pelvis=(-56, -22, 28, 22),
                 brazos=[[(64, -2), (72, 10), (78, 8)]], dedos_b=[(8, 4), (6, 8)],
                 patas=[[(-56, -20), (-14, 34), (-58, 78)]], dedos_p=[(42, 30), (30, 34), (16, 36), (-12, 24)],
                 desfase=(22, -3)),
        vivo=dict(torso=(84, 48, 0), cuello=(26, 38), cola=(34, 3), pata=(29, 18, 11), brazo=(5, 4, 3), cabeza=1.3,
                  rayas=True, rayas_col=0.26),
        extras=[]),
    "espinosaurio": dict(
        color=(48, 168, 172), zoom=1.0,
        geo=dict(craneo=(158, -48, "espino", 0.95, 0.1),
                 cuello=[(116, -46), (96, -48), (76, -40), (58, -30)],
                 lomo=[(58, -30), (26, -36), (-10, -34), (-40, -26), (-60, -18)],
                 cola=[(-60, -18), (-110, -14), (-155, -4), (-196, 14), (-220, 36)],
                 costillas=(6, 46, -16, 50), pelvis=(-52, -14, 26, 18),
                 brazos=[[(60, 0), (84, 16), (108, 8)]], dedos_b=[(16, 8), (14, -2), (10, 12)],
                 patas=[[(-52, -12), (-18, 30), (-56, 76)]], dedos_p=[(40, 30), (28, 34), (14, 36), (-12, 24)],
                 desfase=(22, -3)),
        vivo=dict(torso=(76, 38, 0), cuello=(18, 28), cola=(30, 4), pata=(24, 16, 10), brazo=(11, 8, 6), cabeza=1.3,
                  rayas=True, rayas_col=0.2),
        extras=["vela"]),
    "giganotosaurio": dict(
        color=(104, 126, 206), zoom=1.0,
        geo=dict(craneo=(154, -70, "giga", 1.0, 0.06),
                 cuello=[(110, -58), (90, -54), (70, -42), (54, -30)],
                 lomo=[(54, -30), (24, -40), (-12, -42), (-42, -36), (-64, -28)],
                 cola=[(-64, -28), (-112, -28), (-158, -14), (-198, 8), (-218, 34)],
                 costillas=(6, 46, -16, 56), pelvis=(-55, -22, 27, 20),
                 brazos=[[(62, -6), (76, 12), (90, 8)]], dedos_b=[(12, 8), (10, -2), (6, 10)],
                 patas=[[(-55, -20), (-16, 34), (-60, 78)]], dedos_p=[(42, 30), (30, 34), (16, 36), (-12, 24)],
                 desfase=(22, -3)),
        vivo=dict(torso=(80, 44, 0), cuello=(21, 33), cola=(32, 3), pata=(27, 17, 11), brazo=(7, 5, 4), cabeza=1.35,
                  rayas=True, rayas_col=0.22),
        extras=[]),
    "parasaurolofo": dict(
        color=(236, 120, 134), zoom=1.0,
        geo=dict(craneo=(142, -54, "para", 0.95, 0.12),
                 cuello=[(108, -46), (88, -40), (70, -30), (54, -20)],
                 lomo=[(54, -20), (22, -30), (-14, -34), (-46, -34), (-64, -28)],
                 cola=[(-64, -28), (-112, -20), (-158, -6), (-204, 14), (-226, 28)],
                 costillas=(6, 44, -22, 54), pelvis=(-56, -28, 26, 20),
                 brazos=[[(52, -4), (66, 36), (68, 84)]], dedos_b=[(14, 8), (6, 10), (-2, 10)],
                 patas=[[(-54, -26), (-20, 28), (-56, 78)]], dedos_p=[(30, 24), (20, 28), (10, 30)],
                 desfase=(18, -3)),
        vivo=dict(torso=(80, 44, 0), cuello=(17, 27), cola=(29, 3), pata=(25, 17, 12), brazo=(13, 10, 8), cabeza=1.5,
                  manchas_col=True),
        extras=["rayas_lomo"]),
    "diplodoco": dict(
        color=(160, 144, 214), zoom=1.0,
        geo=dict(craneo=(190, -50, "diplo", 0.62, 0.1),
                 cuello=[(172, -54), (150, -60), (128, -52), (108, -36), (88, -16)],
                 lomo=[(88, -16), (50, -16), (8, -12), (-30, -6)],
                 cola=[(-30, -6), (-92, 2), (-150, 4), (-196, 14), (-238, 38)],
                 costillas=(6, 70, -14, 50), pelvis=(-30, -2, 22, 18),
                 brazos=[[(60, 8), (64, 56), (66, 100)]], dedos_b=[(14, 8), (6, 12), (-2, 12)],
                 patas=[[(-30, 8), (-32, 56), (-40, 100)]], dedos_p=[(14, 8), (6, 12), (-2, 12)],
                 desfase=(16, -4)),
        vivo=dict(torso=(66, 36, 0), cuello=(10, 22), cola=(20, 2), pata=(19, 14, 12), brazo=(17, 13, 11), cabeza=1.75,
                  lunares=True),
        extras=[]),
    "smilodon": dict(
        color=(222, 168, 92), zoom=1.28,
        geo=dict(craneo=(112, -30, "smilo", 1.0, 0.12),
                 cuello=[(92, -28), (76, -26), (60, -22)],
                 lomo=[(60, -26), (28, -26), (-8, -18), (-44, -8)],
                 cola=[(-44, -8), (-66, 0), (-82, 18), (-86, 36)],
                 costillas=(6, 48, -28, 40), pelvis=(-40, -4, 20, 18),
                 brazos=[[(50, 2), (56, 48), (58, 90)]], dedos_b=[(14, 8), (6, 10), (-2, 10)],
                 patas=[[(-38, 4), (-18, 48), (-40, 90)]], dedos_p=[(14, 8), (6, 10), (-2, 10)],
                 desfase=(16, -3)),
        vivo=dict(torso=(60, 32, 0), cuello=(24, 30), cola=(11, 7), pata=(22, 16, 12), brazo=(22, 16, 12), cabeza=1.3,
                  manchas_pelo=True),
        extras=[]),
    "gliptodonte": dict(
        color=(150, 142, 112), zoom=1.12,
        geo=dict(craneo=(122, 28, "glipto", 1.0, 0.18),
                 cuello=[(110, 18), (94, 6), (76, -4)],
                 lomo=[(76, -4), (36, -20), (-10, -22), (-52, -10), (-76, 8)],
                 cola=[(-76, 8), (-112, 22), (-148, 38), (-176, 52)],
                 costillas=(7, 60, -44, 56), pelvis=(-60, 4, 26, 22),
                 brazos=[[(50, 22), (58, 62), (62, 100)]], dedos_b=[(14, 8), (6, 10), (-2, 10)],
                 patas=[[(-54, 22), (-50, 62), (-58, 100)]], dedos_p=[(14, 8), (6, 10), (-2, 10)],
                 desfase=(16, -4)),
        vivo=dict(torso=(86, 46, 0), cuello=(24, 30), cola=(23, 17), pata=(26, 21, 17), brazo=(24, 20, 16), cabeza=1.0),
        extras=["caparazon"]),
    "megaloceros": dict(
        color=(176, 124, 84), zoom=1.05, marfil=(222, 192, 144),
        geo=dict(craneo=(138, -74, "megal", 0.82, 0.14),
                 cuello=[(124, -66), (108, -52), (90, -38), (72, -26)],
                 lomo=[(72, -26), (30, -30), (-14, -28), (-52, -22)],
                 cola=[(-52, -22), (-64, -26), (-74, -18)],
                 costillas=(6, 56, -30, 44), pelvis=(-44, -14, 22, 18),
                 brazos=[[(56, -8), (62, 50), (66, 104)]], dedos_b=[(8, 8), (0, 9)],
                 patas=[[(-44, -8), (-28, 46), (-52, 104)]], dedos_p=[(8, 8), (0, 9)],
                 desfase=(16, -3)),
        vivo=dict(torso=(60, 30, 0), cuello=(14, 22), cola=(8, 4), pata=(14, 9, 6), brazo=(13, 9, 6), cabeza=1.1,
                  claro_vientre=True),
        extras=[]),
    "rinoceronte_lanudo": dict(
        color=(150, 108, 88), zoom=1.1, marfil=(226, 212, 184),
        geo=dict(craneo=(136, 12, "rino", 1.0, 0.2),
                 cuello=[(112, 4), (96, -8), (78, -14)],
                 lomo=[(78, -14), (40, -36), (-6, -30), (-50, -22)],
                 cola=[(-50, -22), (-70, -14), (-82, 4)],
                 costillas=(6, 56, -26, 48), pelvis=(-44, -6, 24, 20),
                 brazos=[[(60, 8), (64, 52), (66, 96)]], dedos_b=[(14, 8), (6, 10), (-2, 10)],
                 patas=[[(-44, 6), (-40, 52), (-48, 96)]], dedos_p=[(14, 8), (6, 10), (-2, 10)],
                 desfase=(16, -3)),
        vivo=dict(torso=(76, 44, 0), cuello=(30, 36), cola=(9, 5), pata=(25, 20, 16), brazo=(25, 20, 16), cabeza=1.2),
        extras=["pelo"], pelo=(112, 76, 62)),
    "megaterio": dict(
        color=(138, 112, 150), zoom=0.96,
        geo=dict(craneo=(78, -118, "megat", 1.0, 0.12),
                 cuello=[(68, -108), (56, -92), (44, -76)],
                 lomo=[(44, -76), (26, -50), (2, -24), (-22, -4)],
                 cola=[(-22, -4), (-62, 14), (-104, 42), (-136, 66)],
                 costillas=(6, 40, -4, 46), pelvis=(-24, 0, 26, 24),
                 brazos=[[(42, -64), (80, -56), (106, -74)]], dedos_b=[(14, 10), (10, 14), (4, 16)],
                 patas=[[(-22, 2), (-6, 50), (-28, 98)]], dedos_p=[(34, 8), (22, 12), (10, 12)],
                 desfase=(14, -3)),
        vivo=dict(torso=(52, 56, 0), cuello=(34, 36), cola=(30, 12), pata=(30, 24, 19), brazo=(19, 15, 12), cabeza=1.2,
                  garras=True),
        extras=["pelo"], pelo=(100, 80, 112)),
    "mamut": dict(
        color=(140, 98, 82), zoom=1.1,
        geo=dict(craneo=(118, -30, "mamut", 1.0, 0.0),
                 cuello=[(100, -28), (84, -34), (68, -34)],
                 lomo=[(68, -38), (36, -62), (-4, -58), (-40, -38), (-62, -18)],
                 cola=[(-62, -18), (-76, -6), (-84, 14)],
                 costillas=(7, 56, -34, 58), pelvis=(-48, -8, 24, 22),
                 brazos=[[(50, 6), (54, 54), (58, 100)]], dedos_b=[(10, 8), (2, 10)],
                 patas=[[(-46, 6), (-44, 54), (-50, 100)]], dedos_p=[(10, 8), (2, 10)],
                 desfase=(16, -3)),
        vivo=dict(torso=(78, 52, 0), cuello=(34, 40), cola=(9, 5), pata=(27, 24, 21), brazo=(27, 24, 21), cabeza=1.1),
        extras=["pelo"], pelo=(104, 70, 60)),
}
IDS = tuple(ESPEC)


def _zoom_geo(g, z):
    if z == 1.0:
        return g
    r = {}
    for k, v in g.items():
        if k == "craneo":
            r[k] = (v[0] * z, v[1] * z, v[2], v[3] * z, v[4])
        elif k == "costillas":
            n, a, b, pr = v
            r[k] = (n, a * z, b * z, pr * z)
        elif k == "pelvis":
            r[k] = tuple(c * z for c in v)
        elif k == "desfase":
            r[k] = (v[0] * z, v[1] * z)
        elif k in ("brazos", "patas"):
            r[k] = [[(a * z, b * z) for a, b in cad] for cad in v]
        elif k in ("dedos_b", "dedos_p"):
            r[k] = [(a * z, b * z) for a, b in v]
        else:
            r[k] = [(a * z, b * z) for a, b in v]
    return r


for _id, _sp in ESPEC.items():
    _z = _sp["zoom"]
    _sp["geo"] = _zoom_geo(_sp["geo"], _z)
    _v = _sp["vivo"]
    for _k in ("torso", "cuello", "cola", "pata", "brazo"):
        _v[_k] = tuple(c * _z for c in _v[_k])
    _v["cabeza"] = _v["cabeza"]            # ya incluye la escala de GEO (craneo[3])
    _sp["geo"]["_zoom"] = _z


# ====================================================================== utilidades de cabeza
def _cerrada(pts, n=6):
    """Curva cerrada suave por los puntos."""
    m = len(pts)
    q = [pts[(i - 1) % m] for i in range(m + 3)]
    q = [pts[(i - 1) % m] for i in range(m + 3)]
    out = []
    for i in range(1, m + 1):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    return out


def _xf_prim(pr, cx, cy, z, ang):
    k = pr[0]
    if k == "p":
        return ("p", rot(pr[1], cx, cy, z, ang))
    if k == "s":
        return ("p", rot(_cerrada(pr[1]), cx, cy, z, ang))
    if k == "e":
        c = rot([pr[1]], cx, cy, z, ang)[0]
        return ("e", c, pr[2] * z, pr[3] * z, (pr[4] if len(pr) > 4 else 0.0) + ang)
    if k == "c":
        c = rot([pr[1]], cx, cy, z, ang)[0]
        return ("c", c, pr[2] * z)
    # cadena
    pts = rot(spline(pr[1], 5), cx, cy, z, ang)
    rad = [r * z for r in pr[2]]
    return ("k", pts, rad)


def _expandir(prims):
    out = []
    for pr in prims:
        if pr[0] == "k":
            out += cadena(pr[1], list(pr[2]))
        else:
            out.append(pr)
    return out


def _cabeza_grupos(ident, t, cx, cy, z, ang):
    """Grupos de la cabeza ya transformados (para el animal vivo)."""
    sp = ESPEC[ident]
    h = HEADS[sp["geo"]["craneo"][2]]
    out = []
    for clave, prims, blando in h["grupos"]:
        if blando == "esq":
            continue
        out.append((clave, _expandir([_xf_prim(pr, cx, cy, z, ang) for pr in prims]), blando))
    return out


def _colores(sp, sil):
    c = sp["color"]
    if sil:
        return dict(b=SIL_COLOR, c=SIL_COLOR, m=SIL_COLOR, o=SIL_COLOR, r=SIL_COLOR, n=SIL_COLOR)
    m = sp.get("marfil", MARFIL)
    return dict(b=c, c=aclarar(c, 0.42), m=m, o=oscurecer(c, 0.3), r=(255, 160, 160), n=oscurecer(m, 0.25))


def _flecos(cx, cy, rx, ry, a0, a1, n, tam, fase=0.0):
    """Triangulos de pelo alrededor de una elipse entre los angulos a0 y a1 (radianes, 0 = derecha, y hacia abajo)."""
    out = []
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        da = (a1 - a0) / n * 0.55
        r = 1.0
        b1 = (cx + rx * r * math.cos(a - da), cy + ry * r * math.sin(a - da))
        b2 = (cx + rx * r * math.cos(a + da), cy + ry * r * math.sin(a + da))
        l = tam * (0.8 + 0.4 * math.sin(i * 2.3 + fase))
        nx, ny = math.cos(a) * ry, math.sin(a) * rx
        m = math.hypot(nx, ny) or 1.0
        pt = (cx + rx * math.cos(a) + nx / m * l, cy + ry * math.sin(a) + ny / m * l)
        out.append(("p", [b1, pt, b2]))
    return out


# ====================================================================== animal vivo
def _mover(sp, t):
    g = sp["geo"]
    cd = spline(g["cola"], 5)
    total = largo(cd) or 1.0
    acum = 0.0
    nueva = []
    z = g["_zoom"]
    for k, (x, y) in enumerate(cd):
        if k:
            acum += math.dist(cd[k - 1], cd[k])
        u = acum / total
        nueva.append((x - 3 * z * u * math.sin(W * t - u * 2.0) * 0.3,
                      y + 13 * z * u * u * math.sin(W * t - u * 2.6) + 3 * z * u * math.sin(W * t * 0.5)))
    cu = spline(g["cuello"], 5)
    nlen = len(cu)
    nc = []
    amp = (3.5 if len(g["cuello"]) < 5 else 6.5) * z
    for k, (x, y) in enumerate(cu):
        w = 1 - k / max(1, nlen - 1)
        nc.append((x + amp * w * w * math.sin(W * t), y + amp * 0.6 * w * math.sin(W * t * 2 + 1)))
    dcab = (nc[0][0] - cu[0][0], nc[0][1] - cu[0][1])
    return nueva, nc, dcab


def _pintar(p, ident, x, y, escala, t, sil):
    sp = ESPEC[ident]
    g, v = sp["geo"], sp["vivo"]
    ext = sp["extras"]
    s = escala * FV
    pin = Pincel(p, x, y, s, sil)
    col = _colores(sp, sil)
    base, claro, oscuro, marfil = col["b"], col["c"], col["o"], col["m"]
    color = sp["color"]
    resp = 1 + 0.03 * math.sin(2 * W * t)
    cola, cuello, dcab = _mover(sp, t)
    rxT, ryT, _ = v["torso"]
    ryT *= resp
    lomo = spline(g["lomo"], 6)
    bajo = [(a, b + ryT * 0.82) for a, b in lomo]
    dx, dy = g["desfase"]
    z0 = g["_zoom"]

    # ---- cosas que van detras del cuerpo
    if "vela" in ext:
        pts = spline(g["cuello"][-2:] + g["lomo"][:4], 6)
        vela = []
        top = []
        for k in range(15):
            u = 0.04 + 0.9 * k / 14
            (px, py), _n = en(pts, u)
            h = (22 + 52 * math.sin(math.pi * (0.1 + 0.8 * u))) * z0
            top.append((px, py - h))
        poly = [(pts[0][0], pts[0][1] + 8)] + top + [(en(pts, 0.96)[0][0], en(pts, 0.96)[0][1] + 8)]
        pin.grupo([("p", poly)], SIL_COLOR if sil else (255, 150, 62), 3.4)
        if not sil:
            for k in range(0, 15, 1):
                u = 0.04 + 0.9 * k / 14
                (px, py), _n = en(pts, u)
                pin.linea([(px, py + 6), top[k]], (214, 96, 40), 2.2)
            pin.linea(top, (255, 214, 140), 3.0)
    if "rayas_lomo" in ext and False:
        pass

    # ---- patas lejanas
    def patas(lejos):
        grupo = []
        for clave, rad, dedos in (("patas", v["pata"], g["dedos_p"]), ("brazos", v["brazo"], g["dedos_b"])):
            for cad in g[clave]:
                c = [(a + (dx if lejos else 0), b + (dy if lejos else 0)) for a, b in cad]
                curva = spline(c, 6)
                grupo += cadena(curva, list(rad))
                tob = c[2]
                for d in dedos[:3]:
                    pt = (tob[0] + d[0] * 0.8, tob[1] + d[1] * 0.8)
                    grupo += cadena([tob, pt], [rad[2] * 0.95, rad[2] * 0.75])
        return grupo
    pin.grupo(patas(True), oscuro)

    # ---- cola y cuerpo
    cola_prims = cadena(cola, [v["cola"][0], v["cola"][0] * 0.55, v["cola"][1]])
    pin.grupo(cola_prims, base)
    if "caparazon" in ext:                      # anillos de la cola con maza
        fin = cola[-1]
        anillos = []
        for u in (0.18, 0.34, 0.5, 0.66):
            (qx, qy), (tx, ty) = en(cola, u)
            r = (v["cola"][0] * (1 - u * 0.45)) * 1.05
            anillos.append(("e", (qx, qy), r * 0.42, r * 1.05, math.atan2(ty, tx)))
        pin.grupo(anillos, SIL_COLOR if sil else (170, 160, 126), 2.2)
        mz = [("e", (fin[0] + 4, fin[1] + 2), 17 * z0, 15 * z0, 0.2)]
        pin.grupo(mz, SIL_COLOR if sil else (176, 166, 132), 2.6)
        pin.grupo([_tri_((fin[0] - 6 * z0, fin[1] - 10 * z0), (fin[0] - 2 * z0, fin[1] - 28 * z0), (fin[0] + 6 * z0, fin[1] - 12 * z0)),
                   _tri_((fin[0] + 8 * z0, fin[1] - 6 * z0), (fin[0] + 26 * z0, fin[1] - 14 * z0), (fin[0] + 18 * z0, fin[1] + 6 * z0)),
                   _tri_((fin[0] + 4 * z0, fin[1] + 12 * z0), (fin[0] + 18 * z0, fin[1] + 26 * z0), (fin[0] - 6 * z0, fin[1] + 14 * z0))],
                  marfil, 2.2)

    cuerpo = cadena(bajo, [ryT * 0.78, ryT * 0.95, ryT * 0.9, ryT * 0.72])
    cuerpo += cadena(cuello, [v["cuello"][0], v["cuello"][1]])
    cuerpo += cadena([(a, b + ryT * 0.2) for a, b in g["cuello"][-2:]] + [bajo[0]], [v["cuello"][1] * 0.9, ryT * 0.8])
    cx0 = (g["lomo"][0][0] + g["lomo"][-1][0]) / 2
    cy0 = bajo[len(bajo) // 2][1] + ryT * 0.12
    cuerpo.append(("e", (cx0, cy0), rxT, ryT * 0.98))
    pin.grupo(cuerpo, base)
    if not sil:
        if not v.get("claro_vientre") is False:
            vientre = cadena([(a, b + ryT * 0.6) for a, b in lomo[3:-3]], [ryT * 0.34])
            vientre.append(("e", (cx0, cy0 + ryT * 0.38), rxT * 0.62, ryT * 0.4))
            for pr in vientre:
                if pr[0] == "c":
                    pin.circ(pr[1], pr[2], claro)
                else:
                    pygame.draw.polygon(p, claro, elipse_pts(*pin.pt(pr[1]), pr[2] * pin.s, pr[3] * pin.s))
        if v.get("rayas"):
            rc = oscurecer(color, v.get("rayas_col", 0.2))
            for k in range(6):
                (qx, qy), _n = en(lomo, 0.12 + 0.16 * k)
                pin.linea([(qx, qy + 4), (qx + 3, qy + ryT * 0.62)], rc, 5 * z0)
            for k in range(5):
                (qx, qy), _n = en(cola, 0.08 + 0.13 * k)
                pin.linea([(qx, qy - cola_prims[0][2] * 0.1 * (1 - 0.1 * k)),
                           (qx + 2, qy + cola_prims[0][2] * 0.36 * (1 - 0.15 * k))], rc, 4 * z0)
        if v.get("lunares"):
            for a, b, r in ((-40, 0.2, 8), (-14, 0.5, 10), (14, 0.2, 7), (40, 0.45, 8), (-62, 0.5, 6), (0, 0.8, 6)):
                pin.circ((cx0 + a * z0, cy0 - ryT * 0.4 + ryT * b * 1.1), r * z0, oscuro)
            for u, r in ((0.55, 5), (0.66, 4), (0.78, 4)):
                (qx, qy), _n = en(g["cuello"][::-1], u)
                pin.circ((qx, qy), r * z0, oscuro)
        if v.get("manchas_pelo"):
            for a, b, r in ((-30, 0.1, 7), (-6, 0.3, 9), (20, 0.1, 7), (40, 0.4, 6), (-48, 0.5, 6), (6, 0.7, 6)):
                pin.circ((cx0 + a * z0, cy0 - ryT * 0.55 + ryT * b * 1.2), r * z0, oscurecer(color, 0.28))
            for k in range(4):
                (qx, qy), _n = en(cola, 0.15 + 0.2 * k)
                pin.linea([(qx, qy - 5), (qx, qy + 5)], oscurecer(color, 0.3), 4 * z0)
        if v.get("manchas_col"):
            for k in range(7):
                (qx, qy), _n = en(lomo, 0.1 + 0.12 * k)
                pin.linea([(qx, qy + 3), (qx + 2, qy + ryT * 0.5)], oscurecer(color, 0.2), 6 * z0)

    if "caparazon" in ext:
        _caparazon_vivo(pin, p, g, v, cx0, cy0, rxT, ryT, sil, marfil, z0)
    if "pelo" in ext:
        pc = SIL_COLOR if sil else sp["pelo"]
        fl = _flecos(cx0, cy0 - ryT * 0.05, rxT * 0.97, ryT * 1.0, 0.1, math.pi - 0.1, 14, 15 * z0, ident.__len__())
        fl += _flecos(cx0, cy0 - ryT * 0.05, rxT * 0.97, ryT * 1.0, math.pi + 0.35, 2 * math.pi - 0.35, 12, 10 * z0, 1.0)
        # faldon de pelo largo en el vientre
        pin.grupo(fl, pc, 2.2)
        if not sil:
            tup = []
            for k in range(7):
                (qx, qy), _n = en(cola, 0.1 + 0.12 * k)
                tup.append(("p", [(qx - 4, qy), (qx + 3, qy + 12 + (k % 2) * 5), (qx + 8, qy)]))
            pin.grupo(tup, pc, 1.8)

    # ---- patas cercanas
    pin.grupo(patas(False), base)
    if not sil:
        for clave, dedos in (("patas", g["dedos_p"]), ("brazos", g["dedos_b"])):
            for cad in g[clave]:
                tob = cad[2]
                for d in dedos[:3]:
                    pin.circ((tob[0] + d[0] * 0.8 + 2, tob[1] + d[1] * 0.8), 3.4 * z0, (252, 248, 230))
        if v.get("garras"):
            for cad in g["brazos"]:
                tob = cad[2]
                for k, d in enumerate(g["dedos_b"][:3]):
                    ax, ay = tob[0] + d[0] * 0.8 + 6, tob[1] + d[1] * 0.8 + 4 * k
                    pin.grupo([("p", [(ax - 4, ay - 7), (ax + 32, ay - 2 + 8 * k), (ax + 4, ay + 9)])], MARFIL, 2.2)

    # ---- cabeza
    cx, cy, tipo, zh, ang = g["craneo"]
    h = HEADS[tipo]
    cx, cy = cx + dcab[0], cy + dcab[1] + math.sin(2 * W * t) * 0.8 * z0
    z = v["cabeza"] * z0
    if tipo == "mamut":                              # la trompa se balancea
        h = _anima_trompa(h, t)
    gr = []
    for clave, prims, blando in h["grupos"]:
        if blando == "esq":
            continue
        gr.append((clave, _expandir([_xf_prim(pr, cx, cy, z, ang) for pr in prims])))
    # orden: grupos detras primero
    for clave, prims in gr:
        pin.grupo(prims, col[clave], 3.0 if clave != "m" else 2.4)
    if sil:
        return
    _cara(pin, p, h, cx, cy, z, ang, t, col, ident, sp)


def _tri_(a, b, c):
    return ("p", [a, b, c])


def _anima_trompa(h, t):
    h2 = dict(h)
    gr = []
    sw = math.sin(W * t)
    for clave, prims, blando in h["grupos"]:
        if clave == "b" and blando:
            pts = [(26, -6), (44, 14), (52 + 3 * sw, 44), (50 + 7 * sw, 74), (38 + 12 * sw, 96), (22 + 14 * sw, 98 + 3 * sw)]
            prims = [("k", pts, [19, 16, 14, 13, 12, 10])]
        if clave == "m":
            nuevo = []
            for pr in prims:
                nuevo.append(pr)
            prims = nuevo
        gr.append((clave, prims, blando))
    h2["grupos"] = gr
    return h2


def _caparazon_vivo(pin, p, g, v, cx0, cy0, rxT, ryT, sil, marfil, z0):
    cx, cy = cx0 - 4 * z0, cy0 - ryT * 0.2
    rx, ry = rxT * 1.2, ryT * 1.6
    pts = []
    for i in range(41):
        a = math.pi + math.pi * i / 40
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a) * 0.95 + ry * 0.0))
    pts.append((cx + rx, cy + ry * 0.12))
    pts.append((cx - rx, cy + ry * 0.12))
    pin.grupo([("p", pts)], SIL_COLOR if sil else (176, 166, 128), 3.6)
    if sil:
        return
    # losetas hexagonales
    azulejos = []
    paso = 25 * z0
    fila = 0
    yv = cy - ry * 0.88
    while yv < cy + ry * 0.05:
        xv = cx - rx + (paso * 0.5 if fila % 2 else 0)
        while xv < cx + rx:
            nx_, ny_ = (xv - cx) / (rx * 0.98), (yv - cy) / (ry * 0.9)
            if nx_ * nx_ + ny_ * ny_ < 0.8:
                hexa = [(xv + 11.5 * z0 * math.cos(math.pi / 6 + k * math.pi / 3), yv + 11.5 * z0 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
                azulejos.append(hexa)
            xv += paso
        yv += paso * 0.86
        fila += 1
    for hexa in azulejos:
        P = [pin.pt(q) for q in hexa]
        pygame.draw.polygon(p, (206, 196, 154), P)
        pygame.draw.lines(p, (120, 108, 76), True, P, max(1, int(2 * pin.s)))
    # borde frontal
    pin.linea([pts[40 - 0], pts[0]][:1] + pts[:41], (120, 108, 76), 0.0001) if False else None


def _cara(pin, p, h, cx, cy, z, ang, t, col, ident, sp):
    # dientes
    for x0, x1, yy, n, tam in h["dientes"]:
        carn = ident in ("alosaurio", "carnotauro", "espinosaurio", "giganotosaurio")
        n2 = n if not carn else min(n, 5)
        for i in range(n2):
            xx = x0 + (x1 - x0) * (0.3 + 0.7 * (i + 0.5) / n2)
            w = (x1 - x0) / n2 * 0.2
            pts = rot([(xx - w, yy - 1), (xx + w, yy - 1), (xx, yy + tam * 0.7)], cx, cy, z, ang)
            pygame.draw.polygon(p, (255, 255, 250), [pin.pt(q) for q in pts])
    (fx, fy), (kx, ky) = h["boca"]
    boca = [(fx - 2, fy), ((fx + kx) / 2, fy + 2), (kx + 4, ky + 1), (kx - 3, ky - 5)]
    pin.linea(rot(spline(boca, 5), cx, cy, z, ang), (84, 40, 48), 2.6)
    mx, my = rot([(h["mej"][0], h["mej"][1])], cx, cy, z, ang)[0]
    pin.circ((mx, my), 5.5 * z, (255, 160, 160))
    ox, oy, r0 = h["ojo"]
    ex, ey = rot([(ox, oy)], cx, cy, z, ang)[0]
    r = r0 * z * 1.05 + 2
    if C.parpadeo(t):
        pin.linea([(ex - r * 0.8, ey + 1), (ex + r * 0.8, ey + 1)], (50, 30, 40), 3)
    else:
        pin.circ((ex, ey), r + 1.6, OJO_OSC)
        pin.circ((ex, ey), r, (255, 255, 255))
        pin.circ((ex + r * 0.22, ey + r * 0.12), r * 0.58, (40, 28, 46))
        pin.circ((ex + r * 0.34, ey - r * 0.12), r * 0.2, (255, 255, 255))
    if h["nariz"]:
        nx, ny = rot([h["nariz"]], cx, cy, z, ang)[0]
        pin.circ((nx, ny), 2.6 * z, (70, 40, 46))


def dibujar(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    C.pintar_vivo(p, ident, x, y, escala, t, silueta, lambda *a: _pintar(a[0], ident, *a[1:]), CAJA)


# ====================================================================== esqueleto
def _bone_grupos(ident, blandos=False):
    sp = ESPEC[ident]
    g = sp["geo"]
    cx, cy, tipo, z, ang = g["craneo"]
    h = HEADS[tipo]
    return h, cx, cy, z, ang


def _parte_craneo(L, ident):
    sp = ESPEC[ident]
    h, cx, cy, z, ang = _bone_grupos(ident)
    tonos = dict(b=HUESO, c=(244, 238, 216), m=HUESO_CLARO, o=HUESO_MEDIO, n=HUESO_MEDIO)
    for clave, prims, blando in h["grupos"]:
        if blando is True:
            continue
        for pr in prims:
            q = _xf_prim(pr, cx, cy, z, ang)
            if q[0] == "k":
                L.linea(q[1], 2 * sum(q[2]) / len(q[2]), (tonos[clave], SOMBRA))
            elif q[0] == "p":
                L.poli(q[1], hueso=tonos[clave], sombra=SOMBRA if clave != "m" else (225, 215, 190))
            elif q[0] == "e":
                L.elipse(q[1][0], q[1][1], q[2], q[3], q[4], hueso=tonos[clave])
            else:
                L.elipse(q[1][0], q[1][1], q[2], q[2], hueso=tonos[clave])
    for x0, x1, yy, n, tam in h["dientes"]:
        for i in range(n):
            xx = x0 + (x1 - x0) * (i + 0.5) / n
            w = (x1 - x0) / n * 0.42
            L.poli(rot([(xx - w, yy - 1), (xx + w, yy - 1), (xx, yy + tam)], cx, cy, z, ang),
                   hueso=(255, 253, 244), sombra=(225, 215, 190), grosor=1.2)
    ox, oy, r0 = h["ojo"]
    px, py = rot([(ox, oy)], cx, cy, z, ang)[0]
    L.elipse(px, py, r0 * z * 1.05, r0 * z * 1.15, ang, hueso=OSCURO, sombra=(30, 24, 18), grosor=2.0)
    if h["nariz"]:
        nx, ny = rot([h["nariz"]], cx, cy, z, ang)[0]
        L.elipse(nx, ny, 3.2 * z, 2.6 * z, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def _parte_columna(L, ident):
    sp = ESPEC[ident]
    g = sp["geo"]
    z0 = g["_zoom"]
    cad = spline(g["cuello"] + g["lomo"][1:], 6)
    L.linea(cad, 6.0 * z0)
    total = largo(cad)
    n = int(total / (9 * z0))
    for k in range(n + 1):
        (x, y), (dx, dy) = en(cad, k / max(1, n))
        nx, ny = dy, -dx
        if ny > 0:
            nx, ny = -nx, -ny
        h = (9 + 4 * math.sin(math.pi * k / max(1, n))) * z0
        if "vela" in sp["extras"]:
            h = (10 + 56 * math.sin(math.pi * k / max(1, n))) * z0 if 0.1 < k / max(1, n) < 0.72 else h
        L.linea([(x, y), (x + nx * h, y + ny * h)], 3.0 * z0 if "vela" not in sp["extras"] else 2.6 * z0)
        L.elipse(x, y, 4.2 * z0, 4.2 * z0, hueso=HUESO, sombra=SOMBRA, grosor=1.5)
    px, py, rx, ry = g["pelvis"]
    L.elipse(px, py, rx, ry, rot=-0.3, hueso=(232, 220, 190))
    L.elipse(px + 3, py - 2, rx * 0.3, ry * 0.38, rot=-0.3, hueso=(250, 244, 226), grosor=1.4)
    if ident == "parasaurolofo":
        lom = spline(g["lomo"], 6)
        for k in range(9):
            (x, y), _n = en(lom, 0.04 + 0.9 * k / 8)
            L.linea([(x, y), (x, y - 16)], 3.0)


def _parte_costillas(L, ident):
    sp = ESPEC[ident]
    g = sp["geo"]
    z0 = g["_zoom"]
    n, xa, xb, prof = g["costillas"]
    base = spline(g["lomo"], 6)
    puntas = []
    if "caparazon" in sp["extras"]:
        cx, cy = (g["lomo"][0][0] + g["lomo"][-1][0]) / 2 - 4, base[len(base) // 2][1] + 8
        rx, ry = g["costillas"][1] - g["costillas"][2], 74
        rx = rx * 0.6 + 30
        pts = [(cx + rx * math.cos(math.pi + math.pi * i / 24), cy + ry * 0.9 * math.sin(math.pi + math.pi * i / 24) + 20) for i in range(25)]
        L.linea(pts, 5.0)
        for ring in (0.72, 0.46):
            L.linea([(cx + (px - cx) * ring, cy + 20 + (py - cy - 20) * ring) for px, py in pts], 4.0)
        for i in range(1, 24, 2):
            px, py = pts[i]
            L.linea([(px, py), (cx + (px - cx) * 0.3, cy + 20 + (py - cy - 20) * 0.3)], 3.0)
        for i in range(2, 23, 2):
            px, py = pts[i]
            L.elipse(px, py, 6, 6, hueso=HUESO_CLARO, grosor=1.4)
        return
    for i in range(n):
        u = (i + 0.5) / n
        x = xa + (xb - xa) * u
        y = min(base, key=lambda q: abs(q[0] - x))[1]
        d = prof * (0.55 + 0.45 * math.sin(math.pi * (0.12 + 0.8 * u)))
        costilla = spline([(x, y + 4), (x + 8 * z0, y + d * 0.45), (x + 2 * z0, y + d * 0.85), (x - 6 * z0, y + d)], 5)
        L.linea(costilla, 5.0 * z0)
        puntas.append((x - 6 * z0, y + d))
    L.linea(puntas, 3.0 * z0)


def _parte_cola(L, ident):
    sp = ESPEC[ident]
    g = sp["geo"]
    z0 = g["_zoom"]
    cad = spline(g["cola"], 6)
    n = 17 if len(g["cola"]) > 4 else 11
    pts = [en(cad, k / n)[0] for k in range(n + 1)]
    L.linea(pts, 4.0 * z0)
    for k, (x, y) in enumerate(pts):
        r = (7.5 * (1 - k / (n + 1)) + 2.2) * z0
        L.elipse(x, y, r, r * 0.85, hueso=HUESO, sombra=SOMBRA, grosor=1.6)
        if k % 2 == 0 and k > 1:
            _, (dx, dy) = en(cad, k / n)
            nx, ny = -dy, dx
            if ny < 0:
                nx, ny = -nx, -ny
            L.linea([(x, y), (x + nx * r * 1.4, y + ny * r * 1.4)], 2.4)
    if "caparazon" in sp["extras"]:
        fin = pts[-1]
        L.elipse(fin[0] + 4, fin[1] + 2, 20, 17, rot=0.2, hueso=HUESO_MEDIO)
        for a, b in ((-8, -10), (8, -8), (12, 8), (-6, 8)):
            L.elipse(fin[0] + a, fin[1] + b, 5, 5, hueso=HUESO_CLARO, grosor=1.4)


def _pie(L, tobillo, dedos, g, col, garra=False):
    for d in dedos:
        punta = (tobillo[0] + d[0], tobillo[1] + d[1])
        L.linea([tobillo, punta], g, col)
        L.poli([(punta[0] - 1, punta[1] - 3), (punta[0] + 7, punta[1] + 1), (punta[0] - 1, punta[1] + 4)],
               hueso=(250, 244, 226), grosor=1.3)


def _extremidades(L, ident, clave, dedos_clave, grosores):
    sp = ESPEC[ident]
    g = sp["geo"]
    dx, dy = g["desfase"]
    for lejos in (True, False):
        col = C.HUESO_LEJOS if lejos else (HUESO, SOMBRA)
        for cad in g[clave]:
            c = [(x + (dx if lejos else 0), y + (dy if lejos else 0)) for x, y in cad]
            curva = spline(c, 6)
            L.linea(curva[:len(curva) // 2 + 1], grosores[0], col)
            L.linea(curva[len(curva) // 2:], grosores[1], col)
            L.nudo(c[0], grosores[0] * 0.8, col)
            L.nudo(c[1], grosores[0] * 0.72, col)
            _pie(L, c[2], g[dedos_clave], grosores[1] * 0.8, col)
            L.nudo(c[2], grosores[1] * 0.75, col)
            if ident == "megaterio" and clave == "brazos":
                for k, d in enumerate(g["dedos_b"][:3]):
                    ax, ay = c[2][0] + d[0] + 4, c[2][1] + d[1] + 4 * k
                    L.poli([(ax - 2, ay - 4), (ax + 24, ay + 10 + 6 * k), (ax + 4, ay + 6)], hueso=(250, 244, 226), grosor=1.4)


def _parte_brazos(L, ident):
    sp = ESPEC[ident]
    z0 = sp["geo"]["_zoom"]
    peq = sp["vivo"]["brazo"][0] < 12 * z0 and ident in ("alosaurio", "carnotauro", "espinosaurio", "giganotosaurio")
    gb = (4.0, 3.2) if ident in ("carnotauro", "giganotosaurio") else ((5.5, 4.4) if peq else (9.5 * z0, 7.5 * z0))
    if ident == "megaterio":
        gb = (7.5, 6.0)
    _extremidades(L, ident, "brazos", "dedos_b", gb)
    sx, sy = sp["geo"]["brazos"][0][0]
    if gb[0] > 6:
        L.elipse(sx - 4, sy - 2, 11 * z0, 16 * z0, rot=0.3, hueso=(232, 220, 190))


def _parte_patas(L, ident):
    z0 = ESPEC[ident]["geo"]["_zoom"]
    carn = ident in ("alosaurio", "carnotauro", "espinosaurio", "giganotosaurio")
    _extremidades(L, ident, "patas", "dedos_p", (10.5, 7.0) if carn else (9.5 * z0, 7.5 * z0))


def partes(ident):
    return [lambda L, i=ident, f=f: f(L, i) for f in
            (_parte_craneo, _parte_columna, _parte_costillas, _parte_cola, _parte_brazos, _parte_patas)]


for _id in ESPEC:
    C.registrar_esqueleto(_id, partes(_id), (580, 400) if _id == "diplodoco" else (520, 380))
