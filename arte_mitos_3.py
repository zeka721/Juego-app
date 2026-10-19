"""Murales del mundo 3 (Egipto) de las Ruinas: Escarabajo, Bastet, Sobek, Anubis, Horus y Esfinge.
Dibujo procedural con el lienzo _L (alto/hondo). Sin archivos ni azar."""
import math

import arte_mitos_base as B

NOMBRES = ['Escarabajo', 'Bastet', 'Sobek', 'Anubis', 'Horus', 'Esfinge']

PI = math.pi


# ------------------------------------------------------------------ auxiliares
def _suave(pts, n=5):
    return B.curva(pts, n, True)


def _ojo_horus(L, x, y, s, sg=1, tono=0):
    """Ojo de Horus: almendra, iris, ceja y cola en espiral."""
    sup = [(x + sg * s * t / 5., y - .30 * s * (1 - (t / 5.) ** 2) - .04 * s) for t in range(-5, 6)]
    inf = [(x + sg * s * t / 5., y + .20 * s * (1 - (t / 5.) ** 2) - .04 * s) for t in range(5, -6, -1)]
    L.pol(sup + inf)
    L.alto(tono)
    L.circ(x + sg * .08 * s, y - .06 * s, .17 * s)
    L.hondo(2)
    L.circ(x + sg * .08 * s, y - .06 * s, .07 * s)
    L.alto(0)
    L.lin([(x - sg * 1.05 * s, y - .5 * s), (x - sg * .3 * s, y - .62 * s), (x + sg * .6 * s, y - .5 * s),
           (x + sg * 1.0 * s, y - .38 * s)], 2.6)
    L.lin([(x + sg * .55 * s, y + .14 * s), (x + sg * .5 * s, y + .45 * s), (x + sg * .3 * s, y + .62 * s),
           (x + sg * .12 * s, y + .55 * s), (x + sg * .15 * s, y + .42 * s)], 2.6)
    L.lin([(x - sg * .95 * s, y + .0 * s), (x - sg * 1.3 * s, y + .22 * s)], 2.6)
    L.alto(1)


def _loto(L, x, y, s):
    for a, l in ((-.55, .8), (.55, .8), (0, 1.0)):
        L.pol(B.hoja(x, y, -PI / 2 + a, l * s, .22 * s))
    L.alto(0)
    for a, l in ((-.3, .7), (.3, .7)):
        L.pol(B.hoja(x, y, -PI / 2 + a, l * s, .17 * s))
    L.alto(1)
    L.lin([(x, y), (x, y + .5 * s)], 2)
    L.hondo(2)


def _papiro(L, x, y, s, alto=1.0):
    """Papiro: tallo y sombrilla de rayos."""
    top = y - alto * s
    L.lin([(x, y), (x, top)], 3)
    L.alto(2)
    for j in range(9):
        a = -PI / 2 + (j - 4) * .3
        L.lin([(x, top), (x + .45 * s * math.cos(a), top + .45 * s * math.sin(a) * 1.0)], 2)
    L.alto(1)
    for j in range(5):
        a = -PI / 2 + (j - 2) * .45
        L.circ(x + .5 * s * math.cos(a), top + .5 * s * math.sin(a), .05 * s)
    L.alto(0)


def _ankh(L, x, y, s, tono=0):
    """Ankh con el aro arriba en (x, y) y altura total s."""
    L.elip(x, y + .17 * s, .15 * s, .2 * s, 3.2)
    L.alto(tono)
    L.lin([(x, y + .36 * s), (x, y + s)], 4.5)
    L.lin([(x - .24 * s, y + .5 * s), (x + .24 * s, y + .5 * s)], 4.5)
    L.alto(tono)
    L.lin([(x, y + .4 * s), (x, y + .95 * s)], 1.2)
    L.hondo(2)


def _glifo(L, k, x, y, s):
    """Glifos sencillos de relleno (se acumulan; el que llama hace hondo)."""
    k %= 6
    if k == 0:   # agua
        L.lin([(x - s, y - .3 * s), (x - .5 * s, y - .6 * s), (x, y - .3 * s), (x + .5 * s, y - .6 * s), (x + s, y - .3 * s)], 1.6)
        L.lin([(x - s, y + .4 * s), (x - .5 * s, y + .1 * s), (x, y + .4 * s), (x + .5 * s, y + .1 * s + y), (x + s, y + .4 * s)], 1.6)
    elif k == 1:  # sol
        L.circ(x, y, s * .7, 1.6)
        L.circ(x, y, s * .15)
    elif k == 2:  # junco
        L.lin([(x, y + s), (x, y - .6 * s)], 1.6)
        L.lin([(x, y - .6 * s), (x - .5 * s, y - s)], 1.6)
        L.lin([(x, y - .6 * s), (x + .5 * s, y - s)], 1.6)
    elif k == 3:  # pan
        L.pol([(x - s, y + .5 * s), (x - .6 * s, y - .4 * s), (x + .6 * s, y - .4 * s), (x + s, y + .5 * s)], 1.6)
    elif k == 4:  # serpiente
        L.lin([(x - s, y + .4 * s), (x - .3 * s, y - .5 * s), (x + .3 * s, y + .5 * s), (x + s, y - .4 * s)], 1.6)
    else:        # ojo
        L.lin(B.arco(x, y + .3 * s, s, .8 * s, PI * 1.15, PI * 1.85, 8), 1.6)
        L.lin(B.arco(x, y - .3 * s, s, .8 * s, PI * .15, PI * .85, 8), 1.6)
        L.circ(x, y, .22 * s)


def _fila_glifos(L, x0, x1, y, n, s, k0=0):
    for j in range(n):
        _glifo(L, k0 + j * 5 // 3 + j, x0 + (x1 - x0) * j / max(1, n - 1), y, s)


def _ojo_amable(L, x, y, r, sg=1):
    """Ojo redondo de criatura (anillo + pupila)."""
    L.circ(x, y, r)
    L.alto(0)
    L.circ(x, y, r, 1.6)
    L.hondo(2)
    L.circ(x + sg * r * .15, y, r * .5)
    L.alto(2)


def _collar(L, cx, cy, rx, ry, bandas=3, t0=.12, sgn=1):
    """Collar ancho (wesekh): bandas en media luna con cuentas. sgn=1 hacia abajo."""
    for b in range(bandas):
        r0 = 1 - b * t0
        r1 = 1 - (b + 1) * t0
        a = B.arco(cx, cy, rx * r0, ry * r0, 0, sgn * PI, 16)
        c = B.arco(cx, cy, rx * r1, ry * r1, sgn * PI, 0, 16)
        L.pol(a + c)
        L.alto(0 if b % 2 == 0 else 2)
    for b in range(bandas):
        rm = 1 - (b + .5) * t0
        n = 10 + b * 2
        for j in range(n):
            ang = sgn * PI * (j + .5) / n
            L.circ(cx + rx * rm * math.cos(ang), cy + ry * rm * math.sin(ang), .017)
        L.hondo(2)
    # gotas del borde
    n = 12
    for j in range(n):
        ang = sgn * PI * (j + .5) / n
        px, py = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        L.elip(px, py + sgn * .02, .025, .045)
    L.alto(1)


def _suelo(L, hw, y, esp=.05, glif=True):
    L.rect(0, y, hw, esp)
    L.alto(2)
    if glif:
        _fila_glifos(L, -hw + .08, hw - .08, y, 7, .026)
        L.hondo(0)


# ------------------------------------------------------------------ 0 Escarabajo
def _pata(L, pts, w=5):
    L.lin(pts, w)
    L.alto(2)
    # espinas
    for (x, y), (x2, y2) in zip(pts[:-1], pts[1:]):
        mx, my = (x + x2) / 2, (y + y2) / 2
        dx, dy = x2 - x, y2 - y
        d = math.hypot(dx, dy) or 1
        L.lin([(mx, my), (mx - dy / d * .05, my + dx / d * .05)], 1.5)
    L.alto(1)


def _m_escarabajo(L):
    # disco solar arriba
    cx, cy = 0, -.56
    for j in range(20):
        a = j * 2 * PI / 20
        L.pol(B.rotar([(.31, -.025), (.4, 0), (.31, .025)], a, cx, cy))
    L.alto(0)
    L.circ(cx, cy, .31)
    L.alto(0)
    L.circ(cx, cy, .26, 3)
    L.hondo(2)
    for j in range(16):
        a = j * 2 * PI / 16
        L.lin([(cx + .1 * math.cos(a), cy + .1 * math.sin(a)), (cx + .21 * math.cos(a), cy + .21 * math.sin(a))], 2)
    L.hondo(2)
    L.circ(cx, cy, .09)
    L.alto(2)
    L.circ(cx, cy, .04)
    L.alto(0)
    # alas abiertas
    for sg in (-1, 1):
        borde = [(sg * .2, .0), (sg * .45, -.12), (sg * .75, -.05), (sg * .9, .14), (sg * .88, .38),
                 (sg * .68, .58), (sg * .42, .68), (sg * .22, .55)]
        L.pol(B.curva([(x, y) for x, y in borde], 4, True))
        L.alto(1)
        raiz = (sg * .28, .22)
        for j in range(1, 8):
            bx, by = borde[j]
            L.lin([(raiz[0] + (bx - raiz[0]) * .3, raiz[1] + (by - raiz[1]) * .3), (raiz[0] + (bx - raiz[0]) * .88, raiz[1] + (by - raiz[1]) * .88)], 2.2)
        L.hondo(2)
        for j in range(1, 8):
            bx, by = borde[j]
            for q in (.5, .66, .8):
                L.circ(raiz[0] + (bx - raiz[0]) * q + sg * .01, raiz[1] + (by - raiz[1]) * q + .03, .014)
        L.alto(0)
    # patas
    for sg in (-1, 1):
        _pata(L, [(sg * .2, -.06), (sg * .38, -.22), (sg * .3, -.36)], 5)
        _pata(L, [(sg * .27, .28), (sg * .55, .24), (sg * .72, .46)], 6)
        _pata(L, [(sg * .22, .55), (sg * .42, .74), (sg * .5, .9)], 5)
    # cuerpo
    for sg in (-1, 1):
        mit = [(0, -.1), (sg * .12, -.08), (sg * .27, .08), (sg * .31, .35), (sg * .24, .6), (sg * .1, .78), (0, .82)]
        L.pol(mit)
    L.alto(0)
    L.lin([(0, -.05), (0, .82)], 2.5)
    for j in range(8):
        y = .12 + j * .085
        L.lin([(-.28 + abs(y - .38) * .1, y), (-.04, y + .045)], 1.5)
        L.lin([(.28 - abs(y - .38) * .1, y), (.04, y + .045)], 1.5)
    L.hondo(2)
    for j in range(5):
        for sg in (-1, 1):
            L.circ(sg * .16, .2 + j * .11, .018)
    L.alto(1)
    # protorax
    L.elip(0, -.02, .27, .13)
    L.alto(1)
    L.elip(0, -.02, .2, .08, 1.6)
    L.hondo(2)
    L.lin([(-.14, -.03), (0, .02), (.14, -.03)], 2)
    L.alto(0)
    # cabeza con dientes
    cab = [(-.2, -.16), (-.16, -.24), (-.1, -.2), (-.06, -.3), (0, -.23), (.06, -.3), (.1, -.2), (.16, -.24), (.2, -.16),
           (.19, -.08), (-.19, -.08)]
    L.pol(cab)
    L.alto(2)
    L.elip(0, -.14, .15, .05)
    L.alto(0)
    for sg in (-1, 1):
        L.circ(sg * .1, -.15, .035)
        L.hondo(2)
        L.lin([(sg * .06, -.28), (sg * .15, -.4), (sg * .24, -.38)], 2)
    L.alto(2)


# ------------------------------------------------------------------ 1 Bastet
def _m_bastet(L):
    # cola enroscada
    L.lin(B.curva([(.28, .8), (.55, .78), (.7, .55), (.62, .3), (.5, .22)], 6), 8)
    L.alto(2)
    for j in range(5):
        t = j / 4.
        L.circ(.36 + .3 * math.sin(t * 2.0) , .8 - .62 * t * t + .05, .015)
    L.hondo(0)
    # cuerpo
    cuerpo = [(-.2, -.26), (.2, -.26), (.31, .0), (.35, .4), (.32, .8), (-.32, .8), (-.35, .4), (-.31, .0)]
    L.pol(B.curva(cuerpo, 4, True))
    L.alto(1)
    for sg in (-1, 1):
        L.elip(sg * .31, .56, .13, .26)
    L.alto(0)
    # vestido plisado
    for j in range(-3, 4):
        L.lin([(j * .07, .22), (j * .08, .78)], 1.5)
    L.hondo(2)
    for j in range(-3, 4):
        L.circ(j * .07 + .035, .38, .014)
    L.alto(0)
    # patas delanteras
    for sg in (-1, 1):
        L.pol([(sg * .06, .3), (sg * .16, .3), (sg * .17, .74), (sg * .2, .8), (sg * .02, .8), (sg * .05, .74)])
    L.alto(0)
    L.lin([(-.1, .8), (-.1, .76)], 1.5)
    L.lin([(.1, .8), (.1, .76)], 1.5)
    L.lin([(0, .5), (0, .8)], 1.5)
    L.hondo(2)
    # cabeza
    for sg in (-1, 1):
        L.pol([(sg * .1, -.58), (sg * .22, -.93), (sg * .31, -.82), (sg * .31, -.52)])
    L.alto(1)
    for sg in (-1, 1):
        L.pol([(sg * .15, -.6), (sg * .22, -.82), (sg * .26, -.72), (sg * .25, -.58)])
    L.hondo(2)
    L.elip(0, -.5, .27, .24)
    L.alto(0)
    # franja y escarabajo de la frente
    L.lin(B.arco(0, -.5, .24, .21, PI * 1.15, PI * 1.85, 10), 2)
    L.hondo(2)
    L.elip(0, -.72, .05, .04)
    L.alto(2)
    # ojos almendrados con kohl
    for sg in (-1, 1):
        L.pol([(sg * .06, -.52), (sg * .13, -.58), (sg * .22, -.52), (sg * .13, -.47)])
        L.alto(2, .8)
        L.circ(sg * .13, -.525, .025)
        L.alto(0)
        L.lin([(sg * .21, -.52), (sg * .3, -.5)], 2.5)
        L.hondo(2)
        # mejillas
        for q in range(3):
            L.lin([(sg * .22, -.42 + q * .03), (sg * .3, -.4 + q * .045)], 1.3)
        L.hondo(2)
    L.elip(0, -.4, .09, .07)
    L.alto(1)
    L.pol([(-.04, -.43), (.04, -.43), (0, -.39)])
    L.alto(2)
    L.lin([(0, -.39), (0, -.35)], 1.5)
    L.lin(B.arco(-.045, -.35, .045, .03, 0, PI * .8, 6), 1.5)
    L.lin(B.arco(.045, -.35, .045, .03, PI * .2, PI, 6), 1.5)
    L.hondo(2)
    for sg in (-1, 1):
        for q in range(3):
            L.lin([(sg * .08, -.38 + q * .02), (sg * .34, -.43 + q * .06)], 1)
    L.hondo(2)
    # aretes
    for sg in (-1, 1):
        L.circ(sg * .29, -.34, .035, 2.5)
        L.elip(sg * .29, -.26, .02, .045)
    L.alto(0)
    # collar
    _collar(L, 0, -.24, .43, .5, 3, .16)
    # peto con ankh
    L.elip(0, .06, .13, .13)
    L.alto(1)
    _ankh(L, 0, -.03, .32, 0)
    # base
    _suelo(L, .44, .87, .045)


# ------------------------------------------------------------------ 2 Sobek
def _papiro2(L, x, yb, yt, r):
    """Papiro con sombrilla grande: tallo de yb a yt y rayos de radio r."""
    L.lin([(x, yb), (x, yt)], 3.5)
    L.alto(2)
    for j in range(11):
        a = -PI / 2 + (j - 5) * .27
        L.lin(B.curva([(x, yt), (x + r * .6 * math.sin(a + PI / 2 - PI / 2) * 1.0 + 0, yt - r * .6 * math.cos(a + PI / 2 - PI / 2) * .0),
                       (x + r * math.cos(a) * 1.0, yt + r * math.sin(a) * 1.0)], 3), 2)
    L.alto(1)
    for j in range(11):
        a = -PI / 2 + (j - 5) * .27
        L.circ(x + r * 1.05 * math.cos(a), yt + r * 1.05 * math.sin(a), .022)
    L.alto(0)
    for q in range(3):
        L.lin([(x - .022, yb - .08 - q * .12), (x + .022, yb - .06 - q * .12)], 1.3)
    L.hondo(2)


def _m_sobek(L):
    # papiros detras
    _papiro2(L, -.78, .58, -.3, .2)
    _papiro2(L, .62, .58, -.38, .22)
    _papiro2(L, .2, .58, -.3, .15)
    # cuerpo
    sup = [(-.9, .0), (-.8, -.1), (-.62, -.12), (-.52, -.2), (-.4, -.17), (-.25, -.1), (0, -.1), (.3, -.08), (.55, -.06),
           (.72, -.1), (.85, -.22), (.93, -.38)]
    inf = [(.95, -.38), (.9, -.1), (.78, .1), (.55, .18), (.3, .24), (0, .28), (-.25, .26), (-.42, .2), (-.6, .12), (-.8, .12),
           (-.9, .1)]
    L.pol(B.curva(sup + inf, 3, True))
    L.alto(1)
    # patas robustas
    for x in (-.3, .36):
        L.pol([(x - .1, .1), (x + .16, .1), (x + .2, .4), (x + .26, .5), (x + .04, .52), (x - .02, .44), (x - .1, .5), (x - .18, .48), (x - .12, .35)])
    L.alto(2)
    for x in (-.3, .36):
        for q in range(3):
            L.lin([(x - .13 + q * .08, .5), (x - .13 + q * .08, .43)], 1.2)
        L.lin(B.arco(x + .03, .22, .08, .06, PI * .1, PI * .9, 5), 1.3)
    L.hondo(0)
    # vientre
    L.pol(B.curva([(-.4, .17), (-.2, .16), (0, .19), (.3, .17), (.55, .13), (.78, .06), (.55, .18), (.3, .24), (0, .28), (-.25, .26), (-.42, .2)], 3, True))
    L.alto(0)
    for j in range(15):
        x = -.4 + j * .09
        L.lin([(x, .19), (x + .01, .27)], 1.2)
    L.hondo(2)
    # escudos del lomo
    for j in range(14):
        x = -.36 + j * .09
        y = -.1 + (.04 * max(0, (x - .5) / .4))
        L.pol([(x - .04, y + .01), (x, y - .07 - .01 * (j % 2)), (x + .04, y + .01)])
    L.alto(2)
    # escamas en filas
    for q in range(3):
        for j in range(11):
            x = -.34 + j * .09 + (q % 2) * .045
            L.lin(B.arco(x, -.0 + q * .075 + (.02 if x > .5 else 0), .045, .04, PI * .1, PI * .9, 5), 1.3)
    L.hondo(2)
    for j in range(6):
        x = .56 + j * .06
        L.lin([(x, -.03 - j * .035), (x + .015, .09 - j * .03)], 1.5)
    L.hondo(2)
    # cara
    L.circ(-.78, -.07, .02)
    L.hondo(2)
    L.lin(B.curva([(-.9, .07), (-.6, .06), (-.46, .06), (-.38, .0)], 5), 1.8)
    L.hondo(2)
    L.pol([(-.7, .075), (-.66, .075), (-.68, .13)])
    L.pol([(-.55, .065), (-.51, .065), (-.53, .11)])
    L.alto(0)
    L.circ(-.46, -.15, .05)
    L.alto(0)
    L.circ(-.46, -.15, .05, 1.5)
    L.hondo(2)
    L.circ(-.45, -.145, .022)
    L.alto(2)
    L.lin([(-.52, -.2), (-.4, -.22)], 2)
    L.hondo(2)
    # corona: base, disco solar y cuernos
    L.pol([(-.6, -.18), (-.4, -.18), (-.43, -.29), (-.57, -.29)])
    L.alto(2)
    L.lin(B.arco(-.5, -.43, .24, .22, PI * .95, PI * 1.5, 8), 5)
    L.lin(B.arco(-.5, -.43, .24, .22, PI * 1.5, PI * 2.05, 8), 5)
    L.alto(2)
    L.circ(-.5, -.43, .14)
    L.alto(0)
    L.circ(-.5, -.43, .1, 2)
    L.hondo(2)
    L.circ(-.5, -.43, .04)
    L.alto(2)
    # agua delante
    for j in range(4):
        y = .6 + j * .1
        pts = [(-.95 + 1.9 * t / 40., y + .035 * math.sin(t / 40. * 12 * PI + j * 1.5)) for t in range(41)]
        L.lin(pts, 3.2)
    L.alto(1, .9)
    for j in range(4):
        y = .65 + j * .1
        pts = [(-.95 + 1.9 * t / 40., y + .035 * math.sin(t / 40. * 12 * PI + j * 1.5 + 1.2)) for t in range(41)]
        L.lin(pts, 1.3)
    L.hondo(2)
    _loto(L, -.5, .66, .13)
    _loto(L, .1, .68, .11)
    _loto(L, .6, .66, .12)


# ------------------------------------------------------------------ 3 Anubis
def _m_anubis(L):
    # cola
    L.lin(B.curva([(.5, .78), (.72, .74), (.8, .55), (.78, .4)], 6), 8)
    L.alto(2)
    # cuerpo sentado
    torso = [(-.12, -.22), (.18, -.26), (.36, -.1), (.42, .2), (.5, .5), (.5, .84), (-.02, .84), (-.04, .5), (-.1, .2)]
    L.pol(B.curva(torso, 4, True))
    L.alto(1)
    L.elip(.34, .56, .22, .27)
    L.alto(0)
    # falda shendyt
    L.pol([(-.08, .3), (.34, .3), (.52, .5), (.54, .82), (-.02, .82)])
    L.alto(0)
    for j in range(7):
        L.lin([(.0 + j * .075, .33), (.0 + j * .08 + .0, .81)], 1.4)
    L.hondo(2)
    L.rect(.24, .31, .17, .03)
    L.alto(2)
    # pata trasera
    L.pol([(.26, .75), (.6, .75), (.62, .84), (.2, .84)])
    L.alto(2)
    # brazo sosteniendo el ankh
    L.lin([(.02, -.02), (-.2, .1), (-.5, .2)], 9)
    L.alto(1)
    L.lin([(-.2, .1), (-.5, .2)], 1.5)
    L.hondo(2)
    # patas delanteras sobre el suelo
    L.pol([(-.04, .35), (.12, .35), (.14, .8), (.2, .86), (-.14, .86), (-.08, .8)])
    L.alto(1)
    L.lin([(-.04, .86), (-.04, .8)], 1.4)
    L.lin([(.04, .86), (.04, .8)], 1.4)
    L.hondo(2)
    # ankh
    _ankh(L, -.64, -.12, .78, 0)
    L.circ(-.6, .2, .06)
    L.alto(1)
    # cabeza de chacal
    for dx, a, b in ((0, .0, -.95), (.14, .08, -.9)):
        L.pol([(dx - .02, -.62), (dx + a - .03, b), (dx + a + .12, -.6)])
        L.alto(2 if dx else 1)
    L.pol([(.03, -.84), (.04, -.67), (.1, -.67)])
    L.hondo(2)
    L.elip(.08, -.5, .2, .19)
    L.alto(1)
    hocico = [(-.08, -.64), (-.28, -.6), (-.5, -.46), (-.52, -.4), (-.5, -.35), (-.28, -.33), (-.05, -.3)]
    L.pol(hocico)
    L.alto(1)
    L.pol([(-.5, -.4), (-.3, -.38), (-.05, -.33), (-.28, -.3), (-.5, -.35)])
    L.alto(0)
    L.circ(-.5, -.45, .03)
    L.alto(2)
    L.lin(B.curva([(-.49, -.37), (-.3, -.35), (-.14, -.36), (-.08, -.41)], 4), 1.6)
    L.hondo(2)
    L.circ(-.19, -.51, .035)
    L.alto(0)
    L.circ(-.19, -.51, .035, 1.4)
    L.hondo(2)
    L.circ(-.185, -.5, .016)
    L.alto(2)
    L.lin([(-.13, -.5), (.0, -.46)], 2.4)
    L.hondo(2)
    # collar ancho
    _collar(L, .1, -.26, .36, .45, 3, .17)
    # tocado: banda de la frente
    L.lin([(-.05, -.64), (.15, -.66), (.26, -.56)], 2.5)
    L.hondo(2)
    _suelo(L, .72, .9, .04)


# ------------------------------------------------------------------ 4 Horus
def _pluma(x, y, ang, l, w):
    """Pluma larga de punta redonda que sale de (x, y) hacia ang."""
    base = [(0, -w * .55), (l * .55, -w), (l * .85, -w * .9), (l * .97, -w * .5), (l, 0), (l * .97, w * .5), (l * .85, w * .9),
            (l * .55, w), (0, w * .55)]
    return B.rotar(base, ang, x, y)


def _m_horus(L):
    filas = [(.1, .72, .085, 2, -2, 38, 10),
             (-.02, .84, .085, 1, -34, 14, 12),
             (-.14, .66, .08, 0, -52, -8, 11),
             (-.22, .4, .07, 1, -64, -20, 11)]
    for ry, largo, anc, tono, a0, a1, paso in filas:
        angs = list(range(a0, a1 + 1, paso))
        for sg in (-1, 1):
            for k, a in enumerate(angs):
                ang = math.radians(a)
                if sg < 0:
                    ang = PI - ang
                L.pol(_pluma(sg * .15, ry, ang, largo, anc))
                L.alto(tono if k % 2 == 0 else (0 if tono else 1))
                L.lin([(sg * .15 + .08 * math.cos(ang), ry + .08 * math.sin(ang)),
                       (sg * .15 + (largo - .05) * math.cos(ang), ry + (largo - .05) * math.sin(ang))], 1.3)
                L.hondo(2)
    # cola
    for a in (-.5, -.25, 0, .25, .5):
        L.pol(_pluma(0, .45, PI / 2 + a, .5, .07))
        L.alto(1)
        L.lin([(0, .5), (.45 * math.cos(PI / 2 + a), .45 + .45 * math.sin(PI / 2 + a))], 1.2)
        L.hondo(2)
    # cuerpo
    cuerpo = [(-.19, -.17), (.19, -.17), (.22, .15), (.14, .5), (-.14, .5), (-.22, .15)]
    L.pol(B.curva(cuerpo, 4, True))
    L.alto(0)
    for j in range(4):
        y = .24 + j * .07
        L.lin([(-.17, y - .04), (0, y + .04), (.17, y - .04)], 1.6)
    L.hondo(2)
    _ojo_horus(L, 0, .06, .13, 1, 0)
    # patas con anillos shen
    for sg in (-1, 1):
        L.pol([(sg * .1, .46), (sg * .2, .46), (sg * .19, .62), (sg * .26, .7), (sg * .1, .7)])
        L.alto(2)
        L.elip(sg * .31, .6, .05, .075)
        L.alto(0)
        L.lin([(sg * .27, .66), (sg * .35, .66)], 1.5)
        L.hondo(2)
    # cabeza
    L.elip(0, -.3, .15, .17)
    L.alto(0)
    L.elip(0, -.4, .12, .05)
    L.alto(1)
    L.pol([(-.05, -.27), (.05, -.27), (.045, -.15), (0, -.08), (-.02, -.14), (-.05, -.2)])
    L.alto(2)
    for sg in (-1, 1):
        L.circ(sg * .075, -.32, .04)
        L.alto(0)
        L.circ(sg * .075, -.32, .04, 1.4)
        L.hondo(2)
        L.circ(sg * .075, -.32, .017)
        L.alto(2)
        L.lin([(sg * .075, -.28), (sg * .09, -.2)], 2)
        L.lin([(sg * .12, -.34), (sg * .17, -.37)], 2)
        L.hondo(2)
    # disco solar con cobras
    for sg in (-1, 1):
        L.lin(B.curva([(sg * .13, -.58), (sg * .22, -.52), (sg * .19, -.44)], 4), 4)
    L.alto(1)
    L.circ(0, -.66, .15)
    L.alto(0)
    L.circ(0, -.66, .11, 2.2)
    L.hondo(2)
    L.circ(0, -.66, .05)
    L.alto(2)
    for sg in (-1, 1):
        L.circ(sg * .19, -.43, .03)
    L.alto(1)
    for sg in (-1, 1):
        _glifo(L, 1, sg * .86, .5, .045)
        _glifo(L, 2, sg * .66, .72, .045)
    L.hondo(2)
    _suelo(L, .4, .87, .04, False)


# ------------------------------------------------------------------ 5 Esfinge
def _m_esfinge(L):
    gy = .55   # suelo
    # sol
    sx, sy = .0, -.62
    for j in range(24):
        a = j * 2 * PI / 24
        r1 = .31 + .04 * (j % 2)
        L.lin([(sx + .26 * math.cos(a), sy + .26 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))], 2.5)
    L.alto(0)
    L.circ(sx, sy, .22)
    L.alto(0, .85)
    L.circ(sx, sy, .16, 2)
    L.hondo(2)
    L.circ(sx, sy, .06)
    L.alto(1)
    # piramides
    for (ax, ay, bx, ex) in ((.75, .05, .52, .98), (.46, -.35, .08, .84)):
        L.pol([(bx, gy), (ax, ay), (ax + (ax - bx), gy)])
        L.alto(1 if ay > -.2 else 0, .9)
        n = 6
        for q in range(1, n):
            y = ay + q * (gy - ay) / n
            t = (y - ay) / (gy - ay)
            L.lin([(ax - (ax - bx) * t, y), (ax + (ax - bx) * t, y)], 1.2)
        L.hondo(2, .8)
        L.lin([(ax, ay), (ax, gy)], 1.2)
        L.hondo(2, .6)
    # cuerpo de leon
    cuerpo = [(-.36, -.02), (-.1, -.01), (.15, -.0), (.38, .05), (.52, .2), (.58, .4), (.55, gy), (-.9, gy), (-.92, .42),
              (-.8, .36), (-.55, .36), (-.4, .2)]
    L.pol(B.curva(cuerpo, 4, True))
    L.alto(1)
    # anca
    L.elip(.3, .3, .24, .25)
    L.alto(0)
    for q in range(4):
        L.lin(B.arco(.3, .3, .06 + q * .045, .1 + q * .045, -PI * .6, PI * .5, 8), 1.3)
    L.hondo(2)
    # pata trasera
    L.pol([(.0, .45), (.3, .45), (.3, gy), (-.12, gy), (-.12, .5)])
    L.alto(0)
    for q in range(3):
        L.lin([(-.1 + q * .04, gy), (-.1 + q * .04, .5)], 1.3)
    L.hondo(2)
    # pata delantera
    L.pol([(-.6, .36), (-.2, .38), (-.18, gy), (-.9, gy), (-.92, .42), (-.8, .36)])
    L.alto(0)
    for q in range(4):
        L.lin([(-.9 + q * .05, gy), (-.9 + q * .05, .44)], 1.4)
    L.lin(B.curva([(-.6, .4), (-.35, .44), (-.2, .42)], 4), 1.4)
    L.hondo(2)
    # pelaje del lomo
    for q in range(8):
        L.lin([(-.28 + q * .075, .03 + q * .002), (-.25 + q * .075, .14)], 1.3)
    L.hondo(2)
    # cola
    L.lin(B.curva([(.55, .5), (.7, .48), (.76, .3), (.68, .15)], 5), 5)
    L.alto(2)
    L.circ(.67, .12, .045)
    L.alto(0)
    # nemes (parte de atras)
    L.pol(B.curva([(-.66, -.36), (-.55, -.52), (-.4, -.52), (-.26, -.4), (-.2, -.05), (-.22, .14), (-.38, .16), (-.4, .0), (-.46, -.1), (-.5, -.3)], 3, True))
    L.alto(1)
    for q in range(7):
        L.lin([(-.4 + q * .03, -.46 + abs(q - 3) * .02), (-.36 + q * .026, .12)], 1.2)
    L.hondo(2)
    for q in range(5):
        L.lin([(-.6 + q * .08, -.47 + abs(q - 2) * .0), (-.62 + q * .08, -.3)], 1.0)
    L.hondo(2)
    # cara de perfil (mira a la izquierda)
    cara = [(-.66, -.36), (-.7, -.28), (-.7, -.22), (-.78, -.12), (-.73, -.09), (-.74, -.04), (-.71, .0), (-.7, .06), (-.62, .1),
            (-.5, .04), (-.46, -.3)]
    L.pol(cara)
    L.alto(0)
    # banda del tocado en la frente
    L.lin([(-.66, -.36), (-.55, -.46), (-.42, -.46), (-.3, -.38)], 3)
    L.alto(2)
    # ojo almendrado, ceja, sonrisa
    L.pol([(-.69, -.23), (-.63, -.27), (-.57, -.23), (-.63, -.2)])
    L.alto(2)
    L.circ(-.63, -.235, .012)
    L.alto(0)
    L.lin([(-.71, -.3), (-.58, -.32)], 2.2)
    L.lin([(-.57, -.23), (-.52, -.2)], 1.8)
    L.lin([(-.72, -.03), (-.66, -.01), (-.62, -.03)], 1.4)
    L.hondo(2)
    # uraeus y barba
    L.circ(-.68, -.4, .035)
    L.alto(2)
    L.pol([(-.66, .09), (-.58, .09), (-.58, .26), (-.62, .29), (-.66, .26)])
    L.alto(2)
    # collar y solapa
    L.pol([(-.5, .08), (-.34, .06), (-.3, .4), (-.44, .42)])
    L.alto(1)
    for q in range(4):
        L.lin([(-.47 + q * .035, .1), (-.42 + q * .03, .38)], 1.2)
    L.hondo(2)
    _collar(L, -.38, .06, .28, .24, 2, .22)
    # base con glifos
    L.rect(0, .7, .62, .08)
    L.alto(2)
    _fila_glifos(L, -.5, .5, .7, 9, .033)
    L.hondo(0)


MOTIVOS = [_m_escarabajo, _m_bastet, _m_sobek, _m_anubis, _m_horus, _m_esfinge]
