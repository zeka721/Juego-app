"""Los 6 animales del Mundo de los Cielos: arqueopterix, dimorfodonte, ranforinco, tapejara, pteranodon, quetzalcoatlus.

Motor de arte_paleo_cuerpo. Las alas son aletas de membrana (poligonos) con el dedo alar dibujado encima; baten con
una animacion suave. Pose de perfil con las alas abiertas.
"""

import math

import arte_paleo_tierra as T
import arte_paleo_cuerpo as K

_g = T._g


def ala(L, C, escal=0.0):
    """Ala de pterosaurio. Marco: b = a lo largo del ala (hacia afuera), a = hacia la cabeza; la membrana va hacia atras."""
    pts = [(0, 0), (3, 0.28 * L), (6, 0.55 * L), (0, L)]            # borde de ataque (la punta es el indice 3)
    A, B = (-0.03 * L, 0.97 * L), (-C, 0.05 * L)
    nk = 3
    knots = []
    for j in range(nk + 1):
        s = j / nk
        knots.append((A[0] + (B[0] - A[0]) * s - 0.1 * L * math.sin(math.pi * s) * 0.6, A[1] + (B[1] - A[1]) * s))
    tr = []
    for j in range(nk):
        a0, a1 = knots[j], knots[j + 1]
        for f in (0.0, 0.25, 0.5, 0.75):
            bow = 0.07 * L * math.sin(math.pi * f)
            tr.append((a0[0] + (a1[0] - a0[0]) * f + bow, a0[1] + (a1[1] - a0[1]) * f + bow * 0.2))
    tr.append(knots[-1])
    tr.append((-C, 0.0))
    return pts + tr


def ala_detalle(L, C):
    return [([(0, 0), (2, 0.26 * L), (6, 0.55 * L)], 5.0), ([(6, 0.55 * L), (2, 0.8 * L), (0, L)], 3.6),
            ([(6, 0.55 * L), (-0.12 * L, 0.78 * L)], 1.6), ([(6, 0.55 * L), (-0.3 * L, 0.5 * L)], 1.6),
            ([(2, 0.26 * L), (-0.32 * L, 0.2 * L)], 1.6)]


def ala_plumas(L, C):
    """Ala de ave con plumas en el borde de atras (arqueopterix)."""
    pts = [(0, 0), (4, 0.3 * L), (6, 0.6 * L), (0, L)]
    n = 9
    for k in range(n):
        s = k / (n - 1)
        a = -C * (s ** 0.75) - 2
        b = L * 0.97 * (1 - s) ** 0.9 + 0.03 * L
        fa = -0.9
        pts.append((a - 5, b - 2))
        pts.append((a + 1, b - 9))
    pts.append((-C, 0))
    return pts


def pata(L, w=7):
    return [(-w * 0.5, 0), (w * 0.5, 0), (w * 0.4, 0.7 * L), (w * 1.9, 0.86 * L), (w * 1.9, L), (-w * 0.8, L), (-w * 0.5, 0.8 * L)]


def rombo(w, h):
    """Aleta en rombo al final de la cola (ranforinco, dimorfodonte)."""
    return [(2, 0), (-w * 0.5, h * 0.6), (-w, 0), (-w * 0.5, -h * 0.6)]


T.HEADS.update({
    "arq": dict(
        grupos=[_g("c", [("p", [(-14, 8), (30, 6), (40, 6), (34, 12), (4, 14)])]),
                _g("b", [("p", [(-20, 2), (-16, -14), (4, -20), (24, -14), (38, -4), (44, 2), (38, 6), (-14, 10)])])],
        ojo=(2, -6, 8), nariz=(36, -2), boca=((42, 5), (-2, 8)), dientes=[(18, 40, 5, 4, 6)], mej=(-8, 6)),
    "dimo": dict(
        grupos=[_g("c", [("p", [(-24, 12), (40, 12), (52, 10), (44, 22), (0, 26)])]),
                _g("b", [("p", [(-30, 0), (-26, -24), (-4, -34), (24, -30), (46, -18), (58, -4), (56, 6), (40, 12),
                                (-20, 14)])])],
        ojo=(4, -12, 11), nariz=(52, -4), boca=((56, 8), (0, 12)), dientes=[(6, 52, 12, 6, 9)], mej=(-8, 8)),
    "ranfo": dict(
        grupos=[_g("c", [("p", [(-20, 8), (80, 6), (86, 8), (78, 14), (40, 16), (0, 20)])]),
                _g("b", [("p", [(-26, 0), (-22, -16), (0, -22), (30, -18), (62, -10), (84, -4), (88, 2), (80, 6),
                                (-20, 10)])])],
        ojo=(-6, -8, 8), nariz=(80, -2), boca=((86, 6), (-8, 9)), dientes=[(16, 84, 7, 7, 9)], mej=(-14, 8)),
    "tape": dict(
        grupos=[_g("x", [("s", [(10, -14), (22, -52), (10, -88), (-26, -104), (-60, -86), (-74, -50), (-56, -18), (-30, -8)])]),
                _g("c", [("p", [(-24, 10), (50, 10), (62, 6), (56, 16), (20, 22)])]),
                _g("b", [("p", [(-26, 2), (-22, -12), (6, -18), (38, -14), (60, -6), (64, 0), (60, 6), (30, 10),
                                (-20, 12)])])],
        ojo=(-4, -6, 8), nariz=(56, -2), boca=((62, 6), (-6, 10)), dientes=[], mej=(-10, 8)),
    "ptera": dict(
        grupos=[_g("x", [("p", [(-10, -14), (-30, -30), (-80, -48), (-112, -46), (-70, -26), (-22, -2)])]),
                _g("c", [("p", [(-16, 8), (126, 5), (130, 8), (120, 12), (60, 14), (10, 18)])]),
                _g("b", [("p", [(-20, 0), (-16, -14), (10, -20), (50, -14), (94, -8), (130, -2), (134, 2), (126, 5),
                                (-18, 10)])])],
        ojo=(0, -7, 8), nariz=(120, -2), boca=((132, 5), (-6, 8)), dientes=[], mej=(-8, 8)),
    "quetzal": dict(
        grupos=[_g("x", [("p", [(-12, -12), (-8, -34), (14, -38), (18, -14)])]),
                _g("c", [("p", [(-10, 6), (146, 4), (150, 7), (140, 10), (70, 10), (10, 14)])]),
                _g("b", [("p", [(-16, 0), (-12, -12), (10, -16), (60, -12), (120, -6), (150, -2), (154, 2), (146, 4),
                                (-14, 8)])])],
        ojo=(0, -6, 7), nariz=(142, -2), boca=((152, 4), (-4, 8)), dientes=[], mej=(-8, 7)),
})


def _alas(L, C, u, col="a", amp=0.85, ang=-0.15, f=3, fase=0.0, esc=0.0, plumas=False, off=0.55):
    pts = ala_plumas(L, C) if plumas else ala(L, C, esc)
    det = ala_detalle(L, C)
    return [
        dict(u=u, lado="l", pos="arriba", off=off, pts=pts, ang=ang - 0.15, amp=amp * 0.9, fase=fase, f=f, col=col, z=0,
             parte=4, detalle=det, alas=dict(punta=3, L=L)),
        dict(u=u, lado="c", pos="arriba", off=off, pts=pts, ang=ang, amp=amp, fase=fase, f=f, col=col, z=1,
             parte=4, detalle=det, alas=dict(punta=3, L=L)),
    ]


def _patas(u, L=30):
    return [dict(u=u, lado="l", pos="abajo", off=0.8, pts=pata(L), ang=0.35, amp=0.1, fase=0.5, col="o", z=0, parte=5),
            dict(u=u, lado="c", pos="abajo", off=0.8, pts=pata(L), ang=0.15, amp=0.1, fase=0.0, col="b", z=1, parte=5)]


K.registrar("arqueopterix", dict(
    color=(92, 176, 124), acento=(244, 170, 64), claro=0.45, vientre=0.4,
    spine=[(94, -16), (70, -6), (40, 4), (0, 12), (-40, 16), (-90, 24), (-150, 36), (-210, 50)],
    perfil=[(0, 14), (0.15, 15), (0.3, 26), (0.42, 32), (0.5, 28), (0.6, 12), (0.8, 5), (1, 3)],
    onda=(7, 1, 4.0, 0.4),
    cabeza=dict(tipo="arq", z=1.55, ang=0.0),
    aletas=_alas(104, 60, 0.32, f=5, amp=0.7, ang=0.0, plumas=True) + _patas(0.42, 34),
    extras=["plumas_cola"], col_esq=(0.0, 0.62), cola_esq=(0.62, 1.0), costillas=(0.26, 0.5, 6, 0.9), espina=7, caja_esq=(620, 540)))

K.registrar("dimorfodonte", dict(
    color=(236, 138, 100), acento=(248, 190, 140), claro=0.45, vientre=0.4,
    spine=[(94, -30), (72, -22), (44, -8), (10, 4), (-30, 12), (-80, 16), (-140, 18), (-196, 20), (-240, 16)],
    perfil=[(0, 14), (0.12, 15), (0.25, 22), (0.4, 28), (0.5, 22), (0.62, 8), (0.8, 4), (1, 2.5)],
    onda=(6, 1, 4.0, 0.4),
    cabeza=dict(tipo="dimo", z=1.15, ang=0.0),
    aletas=_alas(136, 76, 0.36, f=3, amp=0.65, ang=0.3) + _patas(0.5, 30) +
           [dict(u=1.0, lado="c", pos="fin", pts=rombo(30, 22), ang=0.0, amp=0.15, fase=0.5, col="a", z=0, parte=3)],
    col_esq=(0.0, 0.6), cola_esq=(0.6, 1.0), costillas=(0.28, 0.52, 6, 0.9), espina=8, caja_esq=(620, 540)))

K.registrar("ranforinco", dict(
    color=(148, 126, 214), acento=(200, 172, 244), claro=0.45, vientre=0.4,
    spine=[(100, -26), (74, -16), (46, -4), (10, 6), (-30, 12), (-90, 16), (-160, 20), (-230, 22)],
    perfil=[(0, 12), (0.12, 13), (0.25, 20), (0.4, 26), (0.5, 18), (0.62, 7), (0.8, 3.5), (1, 2.2)],
    onda=(6, 1, 4.0, 0.4),
    cabeza=dict(tipo="ranfo", z=1.1, ang=0.0),
    aletas=_alas(176, 64, 0.38, f=3, amp=0.65, ang=0.3) + _patas(0.5, 28) +
           [dict(u=1.0, lado="c", pos="fin", pts=rombo(44, 30), ang=0.0, amp=0.15, fase=0.5, col="a", z=0, parte=3)],
    col_esq=(0.0, 0.6), cola_esq=(0.6, 1.0), costillas=(0.28, 0.52, 6, 0.9), espina=7, caja_esq=(620, 540)))

K.registrar("tapejara", dict(
    color=(96, 162, 214), acento=(150, 202, 236), cresta=(255, 122, 92), claro=0.45, vientre=0.4,
    spine=[(98, -24), (74, -12), (48, 0), (10, 8), (-30, 12), (-70, 14), (-104, 16)],
    perfil=[(0, 12), (0.15, 14), (0.3, 24), (0.45, 30), (0.6, 20), (0.8, 8), (1, 4)],
    onda=(5, 1, 4.0, 0.4),
    cabeza=dict(tipo="tape", z=1.1, ang=0.0),
    aletas=_alas(150, 86, 0.4, f=3, amp=0.65, ang=0.3) + _patas(0.5, 30),
    col_esq=(0.0, 0.72), cola_esq=(0.72, 1.0), costillas=(0.3, 0.58, 6, 0.9), espina=7, caja_esq=(620, 540)))

K.registrar("pteranodon", dict(
    color=(224, 166, 66), acento=(244, 214, 140), cresta=(232, 92, 70), claro=0.45, vientre=0.4,
    spine=[(104, -30), (80, -20), (50, -6), (12, 6), (-26, 12), (-58, 16), (-84, 20)],
    perfil=[(0, 12), (0.15, 14), (0.3, 24), (0.45, 30), (0.6, 19), (0.8, 7), (1, 3.5)],
    onda=(5, 1, 4.0, 0.4),
    cabeza=dict(tipo="ptera", z=1.0, ang=0.0),
    aletas=_alas(190, 84, 0.4, f=3, amp=0.65, ang=0.3) + _patas(0.52, 30),
    col_esq=(0.0, 0.72), cola_esq=(0.72, 1.0), costillas=(0.3, 0.58, 6, 0.9), espina=7, caja_esq=(620, 540)))

K.registrar("quetzalcoatlus", dict(
    color=(124, 164, 196), acento=(176, 206, 228), cresta=(236, 130, 112), claro=0.45, vientre=0.4,
    spine=[(128, -66), (100, -58), (70, -42), (40, -20), (6, 0), (-30, 12), (-64, 18), (-92, 22)],
    perfil=[(0, 10), (0.15, 10), (0.3, 13), (0.42, 24), (0.55, 30), (0.7, 20), (0.85, 9), (1, 4)],
    onda=(5, 1, 4.0, 0.5), cuello=(0.4, 5),
    cabeza=dict(tipo="quetzal", z=0.95, ang=0.0),
    aletas=_alas(212, 96, 0.52, f=2, amp=0.6, ang=0.3) + _patas(0.62, 34),
    col_esq=(0.0, 0.72), cola_esq=(0.72, 1.0), costillas=(0.45, 0.68, 6, 0.9), espina=7,
    caja_esq=(620, 540)))

IDS = ("arqueopterix", "dimorfodonte", "ranforinco", "tapejara", "pteranodon", "quetzalcoatlus")


def dibujar(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    K.dibujar(p, ident, x, y, escala, t, silueta)
