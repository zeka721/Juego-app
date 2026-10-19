"""Los 6 animales del Mundo de los Mares: ictiosaurio, dunkleosteus, plesiosaurio, liopleurodon, mosasaurio, megalodon.

Usan el motor de arte_paleo_cuerpo (columna con grosor + cabeza + aletas animadas).
"""

import math

import arte_paleo_tierra as T
import arte_paleo_cuerpo as K

_g = T._g


def paleta(L, w):
    """Aleta de remo (plesiosaurio, mosasaurio...) que apunta hacia afuera del cuerpo."""
    n = 8
    ancho = lambda s: w * (0.42 + 0.58 * math.sin(math.pi * min(1.0, s * 1.05) ** 0.75)) * (1 - 0.55 * s ** 3)
    izq = [(-ancho(k / n) * 0.8, L * k / n * 0.98) for k in range(n)]
    der = [(ancho(k / n) * 0.45, L * k / n * 0.98) for k in range(n, 0, -1)]
    pts = [(0.0, 0.0)] + [(-q[0], q[1]) for q in izq[1:]]
    pts = [(-ancho(k / n) * 0.85, L * (k / n) ** 0.95) for k in range(0, n + 1)]
    pts += [(ancho(k / n) * 0.5, L * (k / n) ** 0.95) for k in range(n, 0, -1)]
    pts[n] = (0.0, L)
    return pts


def dorsal(h, w):
    return [(w * 0.5, 0), (w * 0.15, h * 0.65), (-w * 0.5, h), (-w * 0.2, h * 0.45), (-w * 0.55, 0)]


def luna(h, w, sup=1.0, inf=0.8):
    """Aleta de cola en media luna (vertical)."""
    return [(3, 0.3 * h), (-0.45 * w, 0.8 * h * sup), (-w, h * sup), (-0.6 * w, 0.38 * h), (-0.38 * w, 0),
            (-0.55 * w, -0.35 * h * inf), (-0.95 * w, -0.85 * h * inf), (-0.45 * w, -0.65 * h * inf), (3, -0.3 * h)]


def pectoral(L):
    return [(16, 0), (-18, 0), (-30, 0.5 * L), (-14, L), (6, 0.45 * L)]


# ---------------------------------------------------------------- cabezas (coordenadas locales)
T.HEADS.update({
    "plesio": dict(
        grupos=[_g("c", [("p", [(-20, 10), (40, 9), (54, 7), (48, 15), (10, 20), (-18, 17)])]),
                _g("b", [("p", [(-24, 4), (-20, -14), (0, -22), (22, -16), (44, -8), (58, 0), (54, 7), (40, 9), (-20, 11)])])],
        ojo=(-2, -6, 8), nariz=(46, -4), boca=((54, 7), (-6, 11)), dientes=[(24, 54, 7, 6, 8)], mej=(-10, 8)),
    "lio": dict(
        grupos=[_g("c", [("p", [(-40, 10), (-20, 10), (86, 8), (90, 12), (80, 22), (30, 30), (-10, 30), (-38, 24)])]),
                _g("b", [("p", [(-44, -6), (-38, -24), (-10, -30), (24, -24), (60, -14), (84, -8), (90, 0), (86, 8),
                                (-20, 10), (-44, 10)])])],
        ojo=(-12, -12, 9), nariz=(80, -4), boca=((88, 8), (-14, 10)), dientes=[(10, 84, 8, 8, 9)], mej=(-4, 16)),
    "mosa": dict(
        grupos=[_g("c", [("p", [(-36, 8), (-20, 8), (92, 8), (100, 10), (90, 18), (40, 22), (-8, 22), (-32, 18)])]),
                _g("b", [("p", [(-40, -4), (-34, -18), (-6, -22), (30, -16), (72, -8), (98, -2), (102, 4), (92, 8),
                                (-20, 8), (-40, 8)])])],
        ojo=(-14, -8, 8), nariz=(94, -2), boca=((98, 8), (-14, 8)), dientes=[(16, 94, 8, 9, 8)], mej=(-6, 14)),
    "ictio": dict(
        grupos=[_g("c", [("p", [(-30, 8), (40, 8), (96, 4), (100, 6), (94, 10), (40, 14), (0, 22), (-28, 20)])]),
                _g("b", [("p", [(-40, 0), (-36, -22), (-10, -30), (20, -24), (40, -14), (76, -8), (100, -4), (104, 0),
                                (98, 4), (40, 8), (-10, 12), (-34, 10)])])],
        ojo=(-2, -8, 13), nariz=(98, -2), boca=((98, 5), (14, 12)), dientes=[(50, 96, 5, 7, 5)], mej=(-14, 8)),
    "megalodon": dict(
        grupos=[_g("b", [("p", [(0, 4), (-24, -12), (-64, -28), (-104, -26), (-116, -4), (-100, 10), (-50, 12)])], "esq"),
                _g("c", [("p", [(-6, 12), (-50, 16), (-96, 10), (-104, 24), (-84, 38), (-40, 40), (-10, 28)])], "esq"),
                _g("k", [("p", [(-4, 13), (-96, 15), (-88, 27), (-34, 30)])])],
        ojo=(-74, -12, 8), nariz=(-14, -2), boca=((-4, 13), (-98, 15)),
        dientes=[(-92, -10, 13, 9, 14), (-84, -14, 28, 7, -12)], mej=(-80, 14)),
    "dunkle": dict(
        grupos=[_g("k", [("p", [(-2, 8), (-114, 12), (-100, 34), (-40, 34)])]),
                _g("c", [("p", [(-4, 14), (-30, 44), (-80, 54), (-118, 36), (-110, 10), (-60, 14)])]),
                _g("b", [("p", [(0, -2), (-14, -30), (-50, -56), (-96, -62), (-128, -34), (-126, 12), (-70, 14), (-30, 8)])]),
                _g("c", [("p", [(-34, -34), (-70, -56), (-100, -54), (-92, -30), (-56, -26)])]),
                _g("c", [("p", [(-22, -14), (-62, -18), (-84, 2), (-34, 4)])]),
                _g("c", [("e", (-84, -30), 18, 18, 0)]),
                _g("m", [("p", [(-2, 4), (-20, 4), (-8, 32)]), ("p", [(-8, 26), (-24, 26), (-14, 2)])])],
        ojo=(-84, -30, 10), nariz=None, boca=((-2, 9), (-104, 12)), dientes=[], mej=None),
})

# ---------------------------------------------------------------- animales
K.registrar("plesiosaurio", dict(
    color=(80, 190, 196), acento=(50, 150, 176), claro=0.5, vientre=0.55,
    spine=[(190, -86), (164, -98), (136, -98), (112, -76), (96, -44), (70, -12), (30, 2), (-20, 8), (-70, 16),
           (-120, 30), (-168, 52), (-192, 68)],
    perfil=[(0, 7), (0.1, 7), (0.25, 10), (0.33, 20), (0.42, 40), (0.5, 46), (0.6, 42), (0.75, 24), (0.9, 10), (1, 3)],
    onda=(6, 1, 4.0, 0.55), cuello=(0.32, 7),
    cabeza=dict(tipo="plesio", z=1.45, ang=-0.12),
    aletas=[dict(u=0.43, lado="l", off=0.6, pos="abajo", pts=paleta(130, 34), ang=0.85, amp=0.45, fase=0.0, col="a", z=0, parte=4),
            dict(u=0.62, lado="l", off=0.6, pos="abajo", pts=paleta(116, 30), ang=0.95, amp=0.45, fase=1.6, col="a", z=0, parte=5),
            dict(u=0.43, lado="c", off=0.6, pos="abajo", pts=paleta(130, 34), ang=0.85, amp=0.45, fase=0.0, col="a", z=1, parte=4),
            dict(u=0.62, lado="c", off=0.6, pos="abajo", pts=paleta(116, 30), ang=0.95, amp=0.45, fase=1.6, col="a", z=1, parte=5)],
    extras=[], col_esq=(0.0, 0.62), cola_esq=(0.62, 1.0), costillas=(0.38, 0.6, 8, 0.9), espina=14))

K.registrar("liopleurodon", dict(
    color=(66, 128, 176), acento=(44, 98, 150), claro=0.45, vientre=0.5,
    spine=[(150, -8), (122, -6), (92, -2), (56, 4), (14, 10), (-30, 14), (-76, 20), (-118, 30), (-154, 42), (-178, 52)],
    perfil=[(0, 24), (0.1, 30), (0.22, 40), (0.4, 54), (0.55, 54), (0.7, 40), (0.85, 20), (1, 5)],
    onda=(7, 1, 4.0, 0.5), cuello=(0.0, 0.0),
    cabeza=dict(tipo="lio", z=1.2, ang=0.0),
    aletas=[dict(u=0.38, lado="l", off=0.6, pos="abajo", pts=paleta(140, 40), ang=0.8, amp=0.4, fase=0.0, col="a", z=0, parte=4),
            dict(u=0.6, lado="l", off=0.6, pos="abajo", pts=paleta(124, 34), ang=0.9, amp=0.4, fase=1.6, col="a", z=0, parte=5),
            dict(u=0.38, lado="c", off=0.6, pos="abajo", pts=paleta(140, 40), ang=0.8, amp=0.4, fase=0.0, col="a", z=1, parte=4),
            dict(u=0.6, lado="c", off=0.6, pos="abajo", pts=paleta(124, 34), ang=0.9, amp=0.4, fase=1.6, col="a", z=1, parte=5),
            dict(u=1.0, lado="c", pos="fin", pts=luna(30, 34, 1.0, 0.9), ang=0.0, amp=0.3, fase=0.5, col="a", z=0, parte=3)],
    extras=[], col_esq=(0.12, 0.7), cola_esq=(0.7, 1.0), costillas=(0.3, 0.62, 8, 0.9), espina=14))

K.registrar("mosasaurio", dict(
    color=(124, 172, 104), acento=(86, 136, 90), claro=0.5, vientre=0.5,
    spine=[(160, -20), (132, -14), (96, -8), (54, 0), (10, 6), (-40, 8), (-90, 4), (-136, -6), (-176, -20), (-206, -34)],
    perfil=[(0, 16), (0.12, 22), (0.3, 32), (0.5, 34), (0.7, 26), (0.85, 16), (0.93, 8), (1, 3)],
    onda=(12, 1, 6.0, 0.15), cuello=(0.0, 0.0),
    cabeza=dict(tipo="mosa", z=0.95, ang=0.0),
    aletas=[dict(u=0.3, lado="l", off=0.6, pos="abajo", pts=paleta(58, 28), ang=0.8, amp=0.4, fase=0.0, col="a", z=0, parte=4),
            dict(u=0.5, lado="l", off=0.6, pos="abajo", pts=paleta(52, 26), ang=0.9, amp=0.4, fase=1.6, col="a", z=0, parte=5),
            dict(u=0.3, lado="c", off=0.6, pos="abajo", pts=paleta(58, 28), ang=0.8, amp=0.4, fase=0.0, col="a", z=1, parte=4),
            dict(u=0.5, lado="c", off=0.6, pos="abajo", pts=paleta(52, 26), ang=0.9, amp=0.4, fase=1.6, col="a", z=1, parte=5),
            dict(u=1.0, lado="c", pos="fin", pts=luna(46, 54, 0.9, 1.0), ang=0.0, amp=0.3, fase=0.5, col="a", z=0, parte=3)],
    extras=["rayas"], rayas_u=(0.22, 0.32, 0.42, 0.52, 0.62, 0.72),
    col_esq=(0.05, 0.62), cola_esq=(0.62, 1.0), costillas=(0.12, 0.5, 10, 0.85), espina=10))

K.registrar("ictiosaurio", dict(
    color=(112, 146, 226), acento=(84, 112, 196), claro=0.55, vientre=0.5,
    spine=[(120, -4), (84, -8), (42, -10), (0, -8), (-46, 0), (-90, 12), (-128, 26), (-160, 36), (-190, 32)],
    perfil=[(0, 14), (0.1, 26), (0.25, 38), (0.42, 44), (0.58, 38), (0.74, 22), (0.9, 9), (1, 4)],
    onda=(9, 1, 5.0, 0.3), cuello=(0.0, 0.0),
    cabeza=dict(tipo="ictio", z=1.0, ang=0.0),
    aletas=[dict(u=0.5, lado="c", pos="arriba", pts=dorsal(48, 42), ang=0.0, amp=0.05, fase=0.0, col="a", z=0, parte=5),
            dict(u=0.34, lado="l", pos="abajo", pts=paleta(46, 18), ang=0.9, amp=0.35, fase=0.0, col="a", z=0, parte=4),
            dict(u=0.34, lado="c", pos="abajo", pts=paleta(46, 18), ang=0.9, amp=0.35, fase=0.0, col="a", z=1, parte=4),
            dict(u=0.64, lado="c", pos="abajo", pts=paleta(26, 12), ang=1.0, amp=0.3, fase=1.0, col="a", z=1, parte=5),
            dict(u=1.0, lado="c", pos="fin", pts=luna(48, 40, 1.0, 1.0), ang=0.0, amp=0.35, fase=0.5, col="a", z=0, parte=3)],
    extras=[], col_esq=(0.12, 0.7), cola_esq=(0.7, 1.0), costillas=(0.2, 0.55, 8, 0.85), espina=10))

K.registrar("megalodon", dict(
    color=(122, 146, 170), acento=(96, 118, 146), claro=0.7, vientre=0.55,
    spine=[(214, 8), (166, 2), (108, -4), (48, -6), (-12, -2), (-72, 6), (-124, 14), (-166, 22), (-194, 28)],
    perfil=[(0, 4), (0.05, 18), (0.15, 36), (0.3, 52), (0.42, 58), (0.58, 50), (0.75, 30), (0.9, 15), (1, 7)],
    onda=(8, 1, 5.0, 0.2), cuello=(0.0, 0.0),
    cabeza=dict(tipo="megalodon", z=1.0, ang=0.0),
    aletas=[dict(u=0.4, lado="c", pos="arriba", pts=dorsal(78, 66), ang=0.0, amp=0.04, fase=0.0, col="a", z=0, parte=5),
            dict(u=0.3, lado="l", pos="abajo", pts=pectoral(84), ang=0.55, amp=0.3, fase=0.0, col="a", z=0, parte=4),
            dict(u=0.3, lado="c", pos="abajo", pts=pectoral(84), ang=0.55, amp=0.3, fase=0.0, col="a", z=1, parte=4),
            dict(u=0.64, lado="c", pos="abajo", pts=pectoral(34), ang=0.6, amp=0.25, fase=1.0, col="a", z=1, parte=5),
            dict(u=1.0, lado="c", pos="fin", pts=luna(78, 64, 1.0, 0.8), ang=0.0, amp=0.3, fase=0.5, col="a", z=0, parte=3)],
    extras=["branquias"], col_esq=(0.1, 0.72), cola_esq=(0.72, 1.0), costillas=(0.22, 0.5, 6, 0.7), espina=8,
    z_esq=1.0))

K.registrar("dunkleosteus", dict(
    color=(214, 142, 92), acento=(242, 206, 150), claro=0.5, vientre=0.4,
    spine=[(124, 0), (84, 2), (42, 6), (-8, 12), (-58, 20), (-108, 28), (-148, 32), (-176, 28)],
    perfil=[(0, 6), (0.04, 34), (0.12, 54), (0.26, 50), (0.4, 40), (0.6, 26), (0.8, 13), (1, 4)], u_cuerpo=0.2,
    onda=(7, 1, 5.0, 0.3), cuello=(0.0, 0.0),
    cabeza=dict(tipo="dunkle", z=1.0, ang=0.0),
    aletas=[dict(u=0.42, lado="c", pos="arriba", pts=dorsal(38, 40), ang=0.0, amp=0.05, fase=0.0, col="a", z=0, parte=5),
            dict(u=0.3, lado="l", pos="abajo", pts=pectoral(42), ang=0.7, amp=0.3, fase=0.0, col="a", z=0, parte=4),
            dict(u=0.3, lado="c", pos="abajo", pts=pectoral(42), ang=0.7, amp=0.3, fase=0.0, col="a", z=1, parte=4),
            dict(u=0.62, lado="c", pos="abajo", pts=pectoral(24), ang=0.7, amp=0.25, fase=1.0, col="a", z=1, parte=5),
            dict(u=1.0, lado="c", pos="fin", pts=luna(44, 42, 1.0, 0.55), ang=0.0, amp=0.3, fase=0.5, col="a", z=0, parte=3)],
    extras=[], col_esq=(0.14, 0.72), cola_esq=(0.72, 1.0), costillas=(0.2, 0.42, 5, 0.6), espina=8))

IDS = ("plesiosaurio", "liopleurodon", "mosasaurio", "ictiosaurio", "megalodon", "dunkleosteus")


def dibujar(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    K.dibujar(p, ident, x, y, escala, t, silueta)
