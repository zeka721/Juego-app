"""Murales del mundo 4 de las Ruinas: ORIENTE (Japon y China). Tanuki, Kappa, Kitsune, Qilin, Fenghuang, Dragon Long."""
import math

import arte_mitos_base as B

NOMBRES = ['Tanuki', 'Kappa', 'Kitsune', 'Qilin', 'Fenghuang', 'Dragón Long']

PI = math.pi


# ------------------------------------------------------------------ ayudas
def _esp(x, y, r0, r1, vueltas, a0=0.0, sg=1, n=30):
    """Espiral desde el radio r0 (centro) hasta r1."""
    return [(x + (r0 + (r1 - r0) * t / n) * math.cos(a0 + sg * t / n * vueltas * 2 * PI),
             y + (r0 + (r1 - r0) * t / n) * math.sin(a0 + sg * t / n * vueltas * 2 * PI)) for t in range(n + 1)]


def _cinta(pts, w0, w1=None, n_fn=None):
    """Poligono de una cinta que sigue la poligonal pts; ancho (semiancho) de w0 a w1. Devuelve (poligono, normales)."""
    w1 = w0 if w1 is None else w1
    m = len(pts)
    izq, der, nor = [], [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(m - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        t = i / max(1, m - 1)
        w = (w0 + (w1 - w0) * t) if n_fn is None else n_fn(t)
        izq.append((x + nx * w, y + ny * w))
        der.append((x - nx * w, y - ny * w))
        nor.append((nx, ny, w))
    return izq + der[::-1], nor


def _nube(L, x, y, s=1.0, sg=1):
    """Nube oriental: bulto de circulos con espiral."""
    for dx, dy, r in ((0, 0, .1), (.11, .0, .08), (-.11, .01, .075), (.2, .035, .055), (-.2, .04, .05), (0, -.07, .08)):
        L.circ(x + sg * dx * s, y + dy * s, r * s)
    L.rect(x, y + .06 * s, .22 * s, .035 * s)
    L.alto(0, .9)
    L.lin(_esp(x + sg * .02 * s, y - .01 * s, .01 * s, .06 * s, 1.6, 0, sg, 14), 1.6)
    L.lin(B.arco(x - sg * .1 * s, y + .06 * s, .06 * s, .03 * s, 0, PI, 6), 1.3)
    L.lin(B.arco(x + sg * .1 * s, y + .06 * s, .06 * s, .03 * s, 0, PI, 6), 1.3)
    L.hondo(2)


def _flor(L, x, y, r, ang=0.0):
    """Flor de cerezo de 5 petalos."""
    for j in range(5):
        a = ang + j * 2 * PI / 5
        L.circ(x + r * .55 * math.cos(a), y + r * .55 * math.sin(a), r * .45)
    L.alto(0, .95)
    for j in range(5):
        a = ang + j * 2 * PI / 5
        L.lin([(x + r * .25 * math.cos(a), y + r * .25 * math.sin(a)), (x + r * .8 * math.cos(a), y + r * .8 * math.sin(a))], 1)
    L.hondo(2, .6)
    L.circ(x, y, r * .2)
    L.alto(2)


def _greca(x0, y0, x1, y1, h, n):
    """Greca oriental (meandro) a lo largo de un segmento: lista de puntos."""
    dx, dy = (x1 - x0) / n, (y1 - y0) / n
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts = []
    for j in range(n):
        bx, by = x0 + dx * j, y0 + dy * j
        for (u, v) in ((0, 0), (0, 1), (.7, 1), (.7, .3), (.35, .3), (.35, .65)):
            pts.append((bx + dx * u + nx * h * v, by + dy * u + ny * h * v))
    return pts


def _ojo_feliz(L, x, y, r, mira=0.0):
    L.circ(x, y, r)
    L.hondo(2)
    L.circ(x, y, r * .72)
    L.alto(0)
    L.circ(x + mira * r * .12, y + r * .05, r * .42)
    L.alto(2)
    L.circ(x + r * .12, y - r * .15, r * .14)
    L.alto(0)


def _ola(L, x, y, r):
    """Ola estilizada (seigaiha): arcos concentricos."""
    for k in range(3):
        L.lin(B.arco(x, y, r * (1 - k * .28), r * (1 - k * .28), PI, 2 * PI, 10), 1.5)
    L.hondo(2)


def _llama(x, y, ang, largo, ancho, curv=.9):
    """Lengua de fuego curvada que sale de (x, y) hacia ang."""
    ej = [(x + largo * t / 8 * math.cos(ang + curv * (t / 8) ** 1.5), y + largo * t / 8 * math.sin(ang + curv * (t / 8) ** 1.5))
          for t in range(9)]
    pol, _ = _cinta(ej, ancho, 0.0, lambda t: ancho * (1 - t) ** .75 * (.45 + .55 * min(1.0, t * 4)))
    return pol


def _pluma(x, y, ang, largo, ancho, curva=0.0):
    """Pluma larga curvada."""
    ej = [(largo * t / 8 * math.cos(ang + curva * (t / 8) ** 2), largo * t / 8 * math.sin(ang + curva * (t / 8) ** 2))
          for t in range(9)]
    ej = [(x + a, y + b) for a, b in ej]
    pol, _ = _cinta(ej, ancho, 0.0, lambda t: ancho * math.sin(PI * (.12 + .88 * t) ** .85) ** .8)
    return pol, ej


# ------------------------------------------------------------------ 0. Tanuki
def _m_tanuki(L):
    _nube(L, -.7, -.42, .85)
    _nube(L, .7, -.38, .85, -1)
    for (x, y, r, a) in ((-.74, .3, .09, 0), (.8, .12, .08, .5), (.52, -.74, .07, .3), (-.52, -.76, .06, .8), (-.68, .62, .06, 1), (.66, .66, .07, 0)):
        _flor(L, x, y, r, a)
    # cola rayada
    L.pol(B.elipse(.56, .6, .26, .13, -.7))
    L.alto(1)
    for k in range(4):
        L.lin(B.rotar([(0, -.11), (0, .11)], -.7, .42 + k * .09, .66 - k * .09), 3.5)
    L.hondo(2)
    # orejas
    for sg in (-1, 1):
        L.circ(sg * .3, -.66, .09)
        L.alto(2)
        L.circ(sg * .3, -.65, .045)
        L.alto(0)
    # cuerpo gordito
    L.elip(0, .3, .56, .57)
    L.alto(1)
    # brazos y patas oscuros
    for sg in (-1, 1):
        L.pol(B.elipse(sg * .5, .12, .09, .2, sg * .45))
        L.circ(sg * .42, .27, .08)
        L.elip(sg * .26, .83, .17, .09)
    L.alto(2)
    for sg in (-1, 1):
        for q in range(3):
            L.circ(sg * (.18 + q * .07), .85, .018)
    L.alto(0, .8)
    # barriga tambor
    L.circ(0, .36, .41)
    L.alto(0)
    L.circ(0, .36, .37, 3)
    L.circ(0, .36, .29, 2)
    L.hondo(2)
    for j in range(22):
        a = j * 2 * PI / 22
        L.circ(.39 * math.cos(a), .36 + .39 * math.sin(a), .017)
    L.alto(1)
    L.lin(_esp(0, .36, .01, .21, 2.5, 0, 1, 34), 3)
    L.hondo(2)
    for j in range(12):
        a = j * 2 * PI / 12 + .26
        L.lin(B.arco(.29 * math.cos(a), .36 + .29 * math.sin(a), .035, .035, a + PI * .5, a + PI * 1.5, 5), 1.2)
    L.hondo(2, .8)
    # cabeza ancha
    L.elip(0, -.4, .42, .31)
    L.alto(1)
    # antifaz oscuro inclinado
    for sg in (-1, 1):
        L.pol(B.elipse(sg * .19, -.43, .125, .08, sg * .6))
    L.alto(2)
    # ojos sonrientes
    for sg in (-1, 1):
        L.lin(B.arco(sg * .18, -.42, .06, .05, PI + .3, 2 * PI - .3, 7), 3)
    L.alto(0)
    # hocico
    L.elip(0, -.27, .17, .13)
    L.alto(0)
    L.pol(B.curva([(-.06, -.34), (0, -.36), (.06, -.34), (0, -.28)], 3, True))
    L.alto(2)
    L.lin([(0, -.29), (0, -.23)], 2)
    L.lin(B.arco(-.07, -.23, .07, .06, .1, PI * .6, 6), 2)
    L.lin(B.arco(.07, -.23, .07, .06, PI * .4, PI - .1, 6), 2)
    L.hondo(2)
    for sg in (-1, 1):
        L.circ(sg * .27, -.25, .04, 2)
    L.hondo(2, .6)
    # frente con marca
    L.lin([(-.06, -.62), (0, -.56), (.06, -.62)], 2)
    L.hondo(2, .7)
    # hoja sobre la cabeza
    ang = -PI / 2 + .4
    L.pol(B.hoja(0, -.68, ang, .3, .12))
    L.alto(0)
    L.lin(B.rotar([(.02, 0), (.28, 0)], ang, 0, -.68), 2)
    for q in range(4):
        L.lin(B.rotar([(.07 + q * .055, 0), (.11 + q * .055, .06)], ang, 0, -.68), 1.2)
        L.lin(B.rotar([(.07 + q * .055, 0), (.11 + q * .055, -.06)], ang, 0, -.68), 1.2)
    L.hondo(2)


# ------------------------------------------------------------------ 1. Kappa
def _m_kappa(L):
    # olas al fondo
    for k in range(3):
        L.lin(B.ondas(-.92, .62 + k * .13, .92, .62 + k * .13, .03, 5 + k, 40), 2.5)
    L.hondo(2, .9)
    for (x, y) in ((-.7, .78), (.0, .86), (.7, .78)):
        _ola(L, x, y + .05, .13)
    _flor(L, -.72, -.55, .09)
    _flor(L, .72, -.6, .08, .6)
    _nube(L, -.62, -.2, .65)
    # caparazon
    L.elip(0, .22, .68, .56)
    L.alto(2)
    L.elip(0, .22, .62, .5)
    L.alto(1)
    for r in range(3):
        for c in range(-3, 4):
            x = c * .2 + (.1 if r % 2 else 0)
            y = -.05 + r * .27 - 0
            if (x / .6) ** 2 + ((y - .22) / .46) ** 2 < 1:
                L.pol([(x + .1 * math.cos(PI / 3 * k), y + .11 * math.sin(PI / 3 * k)) for k in range(6)], 1.5)
    L.hondo(2)
    # torso
    L.elip(0, .36, .34, .4)
    L.alto(0)
    for q in range(4):
        L.lin(B.arco(0, .36 + q * .02, .14 + q * .06, .06, .3, PI - .3, 7), 1.5)
    L.hondo(2, .8)
    L.circ(0, .45, .035)
    L.hondo(2)
    # brazos
    for sg in (-1, 1):
        L.pol(B.elipse(sg * .4, .32, .09, .21, sg * -.45))
        L.circ(sg * .49, .5, .07)
    L.alto(1)
    # pies palmeados
    for sg in (-1, 1):
        L.pol([(sg * .1, .72), (sg * .4, .72), (sg * .45, .78), (sg * .35, .82), (sg * .25, .78), (sg * .18, .83), (sg * .1, .79)])
    L.alto(1)
    # pepino
    L.pol(B.elipse(.68, .38, .075, .3, .55))
    L.alto(0)
    for (x, y) in ((.6, .22), (.68, .3), (.74, .4), (.64, .42), (.8, .5), (.58, .32)):
        L.circ(x, y, .012)
    L.lin([(.6, .48), (.78, .26)], 1.5)
    L.hondo(2)
    L.lin([(.56, .17), (.5, .1)], 3)
    L.alto(2)
    # cabeza
    L.elip(0, -.28, .4, .34)
    L.alto(1)
    # flequillo de pelo alrededor del plato
    for j in range(9):
        x = -.24 + j * .06
        L.pol([(x - .035, -.5), (x, -.63 + abs(j - 4) * .012), (x + .035, -.5)])
    L.alto(2)
    # plato de agua
    L.elip(0, -.56, .27, .1)
    L.alto(0)
    L.elip(0, -.56, .22, .07)
    L.hondo(1)
    L.lin(B.ondas(-.15, -.56, .15, -.56, .015, 2, 14), 1.5)
    L.alto(0, .7)
    L.pol([(0, -.78), (.05, -.7), (0, -.66), (-.05, -.7)])
    L.alto(0)
    # ojos
    for sg in (-1, 1):
        _ojo_feliz(L, sg * .16, -.34, .1, sg * -.3)
    L.lin([(-.28, -.5), (-.08, -.46)], 2.5)
    L.lin([(.28, -.5), (.08, -.46)], 2.5)
    L.hondo(2)
    # pico
    L.elip(0, -.14, .18, .1)
    L.alto(0)
    L.lin(B.arco(0, -.17, .12, .06, .2, PI - .2, 8), 2)
    L.circ(-.05, -.2, .014)
    L.circ(.05, -.2, .014)
    L.hondo(2)
    for sg in (-1, 1):
        L.circ(sg * .27, -.18, .05, 2)
    L.hondo(2, .6)


# ------------------------------------------------------------------ 2. Kitsune
def _m_kitsune(L):
    # nueve colas en abanico (curvas, con la punta clara)
    bx, by = 0, .5
    for j in range(9):
        a = -PI + .1 + j * (PI - .2) / 8
        d = abs(j - 4)
        largo = 1.08 - d * .035
        cv = .0 if j == 4 else (.45 if j < 4 else -.45) * (d / 4) ** .7
        ej = [(bx + largo * t / 10 * math.cos(a + cv * (t / 10) ** 1.5), by + largo * t / 10 * math.sin(a + cv * (t / 10) ** 1.5)) for t in range(11)]
        pol, _ = _cinta(ej, .15, 0, lambda t: .17 * math.sin(PI * (.2 + .8 * t) ** .9) ** .7 + .01)
        L.pol(pol)
        L.alto(1 if j % 2 == 0 else 2)
        tip = ej[6:]
        pc, _ = _cinta(tip, .14, 0, lambda t: .15 * (1 - t) ** .5 + .005)
        L.pol(pc)
        L.alto(0)
        L.lin(ej[1:7], 1.5)
        x6, y6 = ej[6]
        L.lin([(x6 - .1, y6 - .03), (x6 - .04, y6 + .03), (x6, y6 - .03), (x6 + .04, y6 + .03), (x6 + .1, y6 - .03)], 1.5)
        for q in range(2, 6):
            x, y = ej[q]
            L.lin([(x - .035, y + .02), (x, y - .015), (x + .035, y + .02)], 1.2)
        L.hondo(2, .8)
    # orbes y llamitas
    for sg in (-1, 1):
        for (x, y, s) in ((.62, -.62, 1.0), (.84, -.3, .8)):
            L.pol(_llama(sg * x, y - .02, -PI / 2, .24 * s, .07 * s, -sg * .5))
            L.alto(0)
            L.circ(sg * x, y, .055 * s)
            L.alto(0)
            L.circ(sg * x, y, .028 * s)
            L.hondo(2)
    # cuerpo sentado
    L.pol(B.curva(B.simetrico([(.0, .12), (.2, .18), (.34, .45), (.37, .72), (.3, .88)]), 4, True))
    L.alto(1)
    L.elip(0, .55, .13, .3)
    L.alto(0)
    for q in range(4):
        L.lin([(-.07, .38 + q * .1), (0, .43 + q * .1), (.07, .38 + q * .1)], 1.5)
    L.hondo(2)
    for sg in (-1, 1):
        L.pol(B.elipse(sg * .22, .62, .07, .24, sg * .1))
        L.elip(sg * .24, .85, .1, .05)
    L.alto(2)
    # collar con cascabel
    L.lin(B.arco(0, .14, .27, .1, .25, PI - .25, 10), 4)
    L.alto(0)
    L.circ(0, .26, .045)
    L.alto(0)
    L.lin([(-.03, .26), (.03, .26)], 1.5)
    L.hondo(2)
    # orejas grandes
    for sg in (-1, 1):
        L.pol([(sg * .08, -.3), (sg * .22, -.78), (sg * .4, -.2)])
        L.alto(1)
        L.pol([(sg * .16, -.32), (sg * .23, -.62), (sg * .33, -.26)])
        L.alto(2)
        L.lin([(sg * .22, -.35), (sg * .24, -.55)], 1.5)
        L.hondo(1, .8)
    # cabeza con mechones de mejilla
    L.pol(B.simetrico([(0, -.32), (.2, -.28), (.34, -.14), (.52, .02), (.4, .03), (.47, .14), (.3, .14), (.14, .22)]) + [(0, .24)])
    L.alto(1)
    # hocico y mejillas claras
    L.pol(B.curva(B.simetrico([(0, -.06), (.14, -.02), (.34, .02), (.4, .04), (.3, .12), (.14, .2)]), 3, True))
    L.alto(0)
    # nariz y boca
    L.pol([(-.04, .0), (.04, .0), (0, .05)])
    L.alto(2)
    L.lin([(0, .05), (0, .1)], 1.8)
    L.lin(B.arco(-.06, .1, .06, .05, .1, PI * .6, 5), 1.8)
    L.lin(B.arco(.06, .1, .06, .05, PI * .4, PI - .1, 5), 1.8)
    L.hondo(2)
    # ojos rasgados
    for sg in (-1, 1):
        L.pol([(sg * .09, -.12), (sg * .2, -.19), (sg * .3, -.11), (sg * .2, -.08)])
        L.alto(0)
        L.circ(sg * .2, -.125, .028)
        L.hondo(2)
        # manchas rituales rojas
        L.lin([(sg * .34, -.1), (sg * .44, -.04)], 3)
        L.lin([(sg * .34, -.04), (sg * .44, .02)], 3)
        L.lin([(sg * .14, -.26), (sg * .22, -.2)], 3)
    L.hondo(2)
    L.circ(0, -.24, .035)
    L.lin([(0, -.31), (0, -.28)], 2)
    L.hondo(2)
    _flor(L, -.62, .82, .07)
    _flor(L, .62, .84, .07, .4)


# ------------------------------------------------------------------ 3. Qilin
def _pata_ciervo(L, x, y0, y1=.68, w=.075):
    L.pol([(x - w, y0), (x + w, y0), (x + w * .9, .42), (x + w * .55, y1), (x - w * .55, y1), (x - w * .6, .46)])
    L.circ(x, y0, w * 1.15)


def _m_qilin(L):
    _nube(L, -.5, .86, .75)
    _nube(L, .4, .88, .75, -1)
    _nube(L, -.72, -.66, .6)
    _flor(L, .8, .4, .06)
    _flor(L, -.86, .12, .06, .5)
    # cola de llamas
    for k in range(4):
        L.pol(_llama(-.58, .06 + k * .02, PI + .55 - k * .35, .45 - k * .03, .06, -.9))
    L.alto(2)
    # patas lejanas
    for x in (-.38, .16):
        _pata_ciervo(L, x, .2)
    L.alto(2)
    for x in (-.38, .16):
        L.pol([(x - .045, .68), (x + .045, .68), (x + .07, .76), (x - .07, .76)])
    L.alto(2)
    # cuerpo
    L.pol(B.curva([(-.62, -.02), (-.45, -.18), (-.1, -.2), (.2, -.14), (.36, -.04), (.34, .16), (.1, .3), (-.3, .32), (-.55, .22)], 5, True))
    L.alto(1)
    for x in (-.55, .3):
        _pata_ciervo(L, x, .12, .68, .085)
    L.alto(1)
    for x in (-.55, .3):
        L.pol([(x - .05, .68), (x + .05, .68), (x + .075, .76), (x - .075, .76)])
    L.alto(2)
    # escamas del cuerpo
    for fila in range(5):
        for col in range(10):
            x = -.55 + col * .088 + (.044 if fila % 2 else 0)
            y = -.12 + fila * .085
            if -.58 < x < .3 and y < .22 and not (x > .22 and y > .14) and not (x < -.5 and y < -.06):
                L.lin(B.arco(x, y, .04, .04, .15, PI - .15, 6), 1.3)
    L.hondo(2)
    for x in (-.55, .3):
        for q in range(3):
            L.lin([(x - .05, .34 + q * .1), (x, .38 + q * .1), (x + .05, .34 + q * .1)], 1.3)
    L.hondo(2, .8)
    # cuello
    L.pol([(.1, -.2), (.2, -.52), (.42, -.46), (.42, -.2), (.4, .08), (.28, .12)])
    L.alto(1)
    for q in range(4):
        for c in range(2):
            L.lin(B.arco(.26 + c * .09 + (q % 2) * .045, -.1 - q * .09, .04, .04, .15, PI - .15, 5), 1.2)
    L.hondo(2)
    # melena de llamas por cuello y lomo
    pos = [(.2, -.55), (.14, -.44), (.07, -.34), (-.02, -.26), (-.13, -.23), (-.24, -.21), (-.35, -.19), (-.46, -.15), (-.54, -.1)]
    for j, (x, y) in enumerate(pos):
        a = PI * 1.1 + j * .04 if j > 3 else -PI + .1 + j * .12
        L.pol(_llama(x, y, a - .15, .32 - (j % 3) * .03, .08, -1.0))
    L.alto(0)
    for j, (x, y) in enumerate(pos):
        a = PI * 1.1 + j * .04 if j > 3 else -PI + .1 + j * .12
        L.lin([(x + .03 * math.cos(a - .15), y + .03 * math.sin(a - .15)), (x + .13 * math.cos(a - .3), y + .13 * math.sin(a - .3))], 1.3)
    L.hondo(2)
    _cabeza_dragon(L, .28, -.52, 1.05, 1, .45, False)


# ------------------------------------------------------------------ 4. Fenghuang
def _pluma_redonda(x, y, ang, largo, ancho, curva=0.0):
    ej = [(x + largo * t / 8 * math.cos(ang + curva * (t / 8) ** 2), y + largo * t / 8 * math.sin(ang + curva * (t / 8) ** 2))
          for t in range(9)]

    def w(t):
        base = .55 + .45 * min(1.0, t * 5)
        if t < .5:
            return ancho * base
        return ancho * math.sqrt(max(0.0, 1 - ((t - .5) / .5) ** 2.5))
    pol, _ = _cinta(ej, ancho, 0.0, w)
    return pol, ej


def _m_fenghuang(L):
    # sol y aro
    L.circ(0, -.05, .93, 3)
    L.circ(0, -.05, .88, 2)
    L.hondo(2)
    for j in range(32):
        a = j * 2 * PI / 32
        L.circ(.905 * math.cos(a), -.05 + .905 * math.sin(a), .012)
    L.alto(0, .8)
    L.circ(0, -.2, .5)
    L.alto(0, .6)
    L.circ(0, -.2, .45, 2)
    for j in range(24):
        a = j * 2 * PI / 24
        L.lin([(.36 * math.cos(a), -.2 + .36 * math.sin(a)), (.44 * math.cos(a), -.2 + .44 * math.sin(a))], 1.2)
    L.hondo(2, .6)
    _nube(L, -.62, .74, .75)
    _nube(L, .62, .74, .75, -1)
    _nube(L, -.7, -.68, .55)
    _nube(L, .7, -.68, .55, -1)
    # cola larga: cintas con ojos de pluma
    colas = [
        [(0, .24), (.2, .42), (.46, .5), (.7, .42), (.78, .22)],
        [(0, .26), (.14, .5), (.34, .68), (.58, .74), (.74, .62)],
        [(0, .28), (.06, .52), (.2, .76), (.2, .96 - .12)],
    ]
    for k, pts in enumerate(colas):
        for sg in ((-1, 1) if k < 2 else (-1, 1)):
            ej = B.curva([(sg * x, y) for x, y in pts], 6)
            if k == 2:
                ej = B.curva([(sg * x * .6, y) for x, y in pts], 6)
            pol, _ = _cinta(ej, .075, .04, lambda t: .035 + .07 * math.sin(PI * min(1, t * 1.15)) ** .5)
            L.pol(pol)
            L.alto((2, 1, 2)[k])
            L.lin(ej[:-4], 1.5)
            for q in range(3, len(ej) - 5, 3):
                x, y = ej[q]
                L.lin([(x - .03, y - .03), (x, y + .01), (x + .03, y - .03)], 1.2)
            L.hondo(2, .8)
            x, y = ej[-1]
            L.circ(x, y, .07)
            L.alto(0)
            L.circ(x, y, .045)
            L.hondo(2)
            L.circ(x, y, .02)
            L.alto(1)
    # alas: tres capas de plumas redondeadas
    for sg in (-1, 1):
        def an(a):
            return a if sg > 0 else PI - a
        for q in range(7):
            p, _ = _pluma_redonda(sg * .12, -.12, an(-1.5 + q * .26), .86 - abs(q - 2) * .04, .085, sg * .35 * (q - 3) * .1)
            L.pol(p)
        L.alto(2)
        for q in range(6):
            p, _ = _pluma_redonda(sg * .12, -.1, an(-1.3 + q * .27), .6, .085)
            L.pol(p)
        L.alto(1)
        for q in range(5):
            p, _ = _pluma_redonda(sg * .12, -.07, an(-1.05 + q * .3), .36, .075)
            L.pol(p)
        L.alto(0)
        for q in range(6):
            a = an(-1.3 + q * .27)
            L.lin(B.rotar([(.12, 0), (.52, 0)], a, sg * .12, -.1), 1.3)
        for q in range(5):
            a = an(-1.05 + q * .3)
            for r in (.12, .22, .31):
                x, y = sg * .12 + r * math.cos(a), -.07 + r * math.sin(a)
                L.lin(B.arco(x, y, .035, .035, a - 1.3, a + 1.3, 4), 1.2)
        L.hondo(2, .85)
    # cuerpo
    L.elip(0, -.02, .19, .3)
    L.alto(1)
    L.elip(0, .0, .13, .25)
    L.alto(0)
    for q in range(5):
        L.lin([(-.1, -.12 + q * .09), (0, -.04 + q * .09), (.1, -.12 + q * .09)], 1.5)
    L.hondo(2)
    # cabeza y cuello
    L.pol([(-.08, -.32), (.08, -.32), (.1, -.22), (-.1, -.22)])
    L.alto(1)
    L.circ(0, -.43, .15)
    L.alto(1)
    # cresta de plumas curvas
    for sg in (-1, 1):
        for (a, l, c) in ((-PI / 2 + sg * .35, .28, sg * .8), (-PI / 2 + sg * .8, .22, sg * 1.0)):
            L.pol(_llama(sg * .07, -.54, a, l, .045, c))
    L.pol(_llama(0, -.56, -PI / 2, .34, .05, 0.01))
    L.alto(0)
    for sg in (-1, 1):
        L.pol([(sg * .03, -.45), (sg * .09, -.49), (sg * .13, -.44), (sg * .09, -.42)])
        L.alto(0)
        L.circ(sg * .09, -.455, .017)
        L.hondo(2)
        L.circ(sg * .105, -.37, .03, 2)
    L.hondo(2, .6)
    L.pol([(-.05, -.41), (.05, -.41), (0, -.29)])
    L.alto(2)
    L.lin([(0, -.4), (0, -.32)], 1.2)
    L.alto(0)
    for sg in (-1, 1):
        L.lin(B.ondas(sg * .12, -.36, sg * .24, -.14, .03, 1.2, 10), 2)
    L.alto(2)
    _flor(L, -.44, .5, .05)
    _flor(L, .44, .5, .05, .5)


# ------------------------------------------------------------------ 5. Dragon Long
def _cabeza_dragon(L, x, y, s, cuernos=2, bigote=1.0, melena=True):
    """Cabeza amable de dragon chino de perfil mirando a la derecha."""
    def T(p):
        return B.mover(B.escalar(p, s), x, y)

    def P(a, b):
        return (x + a * s, y + b * s)

    # melena de llamas
    if melena:
        for j in range(6):
            L.pol(T(_llama(-.1, -.08 + j * .035, PI * .9 + j * .13 - .1, .34, .05, -.9)))
        L.alto(2)
    # cuernos
    for k in range(cuernos):
        ej = B.curva([(.05 - k * .07, -.1), (-.02 - k * .1, -.3), (-.16 - k * .1, -.4), (-.3 - k * .08, -.36)], 5)
        pol, _ = _cinta(ej, .04, .004)
        L.pol(T(pol))
    L.alto(0)
    # craneo y hocico
    L.pol(T(B.curva([(-.18, -.02), (-.05, -.13), (.16, -.13), (.34, -.12), (.46, -.14), (.52, -.06), (.46, .02), (.28, .04), (.16, .12), (-.04, .14), (-.17, .08)], 4, True)))
    L.alto(1)
    # mandibula
    L.pol(T(B.curva([(.14, .05), (.32, .05), (.44, .04), (.42, .12), (.26, .16), (.1, .15)], 4, True)))
    L.alto(0)
    # nariz
    L.pol(T(B.elipse(.47, -.1, .07, .045, -.3)))
    L.alto(0)
    L.pol(T(B.elipse(.5, -.12, .016, .012)))
    L.hondo(2)
    # sonrisa
    L.lin(T(B.arco(.3, .02, .14, .05, .1, PI * .55, 6)), 1.6)
    L.hondo(2)
    # escamas del craneo
    for q in range(3):
        L.lin(T(B.arco(.0 + q * .09, -.02, .04, .04, .2, PI - .2, 5)), 1.2)
    L.hondo(2)
    # ceja, ojo
    L.lin(T([(.07, -.12), (.15, -.16), (.26, -.11)]), 2.4)
    L.alto(2)
    ex, ey = P(.16, -.05)
    _ojo_feliz(L, ex, ey, .085 * s, .6)
    # bigotes largos
    L.lin(T(B.ondas(.42, -.09, .42 + .4 * bigote, -.3, .045, 1.6, 20)), 2)
    L.lin(T(B.ondas(.4, -.04, .4 + .46 * bigote, -.08, .04, 1.8, 20)), 2)
    L.alto(0)
    # barba
    L.pol(T(B.curva([(.1, .13), (.16, .32), (.26, .13)], 3)))
    L.alto(2)
    L.pol(T([(.22, .13), (.3, .27), (.36, .12)]))
    L.alto(2)


def _m_dragon(L):
    _nube(L, -.64, -.66, .6)
    _nube(L, .7, .6, .75, -1)
    _nube(L, -.76, .62, .6)
    _flor(L, .82, -.2, .06)
    _flor(L, -.86, -.12, .06, .5)
    # cuerpo en espiral
    n = 70
    cam = []
    for i in range(n + 1):
        t = i / n
        a = -PI * (120 / 180) - t * PI * (332 / 180)
        r = .55 - .24 * t ** .9
        cam.append((r * math.cos(a), r * math.sin(a)))
    cam = [(.0, -.58), (-.12, -.56), (-.2, -.52)] + cam
    cam = B.curva(cam, 1)
    m = len(cam)
    pol, nor = _cinta(cam, .1, .02, lambda t: .105 - .085 * t ** .8)
    for i in range(3, m - 6, 3):
        x, y = cam[i]
        nx, ny, w = nor[i]
        sg = 1 if x * nx + y * ny > 0 else -1
        ang = math.atan2(ny * sg, nx * sg)
        L.pol(_llama(x + nx * sg * w * .7, y + ny * sg * w * .7, ang + .3, .12 + .05 * (1 - i / m), .03, .9))
    L.alto(2)
    # patas con garras
    for (idx, ln, sg) in ((24, .27, 1), (44, .25, -1), (62, .2, 1)):
        x, y = cam[idx]
        d = math.hypot(x, y) or 1
        ux, uy = x / d, y / d
        a = math.atan2(uy, ux)
        pata = [(x, y), (x + ux * ln * .5 - uy * .04 * sg, y + uy * ln * .5 + ux * .04 * sg), (x + ux * ln, y + uy * ln)]
        pp, _ = _cinta(B.curva(pata, 4), .035, .025)
        L.pol(pp)
        ex, ey = pata[-1]
        L.circ(ex, ey, .04)
        L.alto(1)
        for k in (-1, 0, 1):
            L.pol(B.rotar([(0, -.02), (.09, 0), (0, .02)], a + k * .55, ex, ey))
        L.alto(0)
    L.pol(pol)
    L.alto(1)
    # escamas en V
    for i in range(0, m - 1, 2):
        x, y = cam[i]
        nx, ny, w = nor[i]
        L.lin([(x + nx * w * .9, y + ny * w * .9), (x + nx * w * .1 - ny * w * .55, y + ny * w * .1 + nx * w * .55), (x - nx * w * .9, y - ny * w * .9)], 1.3)
    L.hondo(2)
    # puntos claros en el lomo
    for i in range(1, m - 1, 4):
        x, y = cam[i]
        nx, ny, w = nor[i]
        sg = 1 if x * nx + y * ny > 0 else -1
        L.circ(x + nx * sg * w * .6, y + ny * sg * w * .6, .014)
    L.alto(0)
    # penacho de la cola
    ex, ey = cam[-1]
    for k in range(3):
        L.pol(_llama(ex, ey, -.3 + k * .6 - 0.2, .2 - k * .02, .035, 1.0))
    L.alto(0)
    # perla con llamas
    for j in range(10):
        a = j * 2 * PI / 10
        L.pol(_llama(.15 * math.cos(a), .15 * math.sin(a), a + .5, .1, .025, .9))
    L.alto(2, .8)
    L.circ(0, 0, .19)
    L.alto(0)
    L.circ(0, 0, .155, 2)
    L.hondo(2)
    L.lin(_esp(0, 0, .01, .12, 2, 0, 1, 24), 2)
    L.hondo(2, .8)
    L.circ(-.07, -.07, .028)
    L.alto(0)
    _cabeza_dragon(L, .1, -.57, .82, 2, .9)


MOTIVOS = [_m_tanuki, _m_kappa, _m_kitsune, _m_qilin, _m_fenghuang, _m_dragon]
