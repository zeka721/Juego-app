"""Murales del mundo 1 de las Ruinas (griego): Pegaso, Centauro, Minotauro, Cerbero, Hidra y Quimera.
Relieves de arenisca dibujados con el lienzo _L; solo math y formas propias (sin archivos ni azar)."""
import math

import arte_mitos_base as B

NOMBRES = ['Pegaso', 'Centauro', 'Minotauro', 'Cerbero', 'Hidra', 'Quimera']

PI = math.pi


# ---------------------------------------------------------------- ayudas comunes
def _trazo(pts, w0, w1=None, n=6):
    """Poligono de un trazo curvo que cambia de grosor de w0 a w1 (cuellos, patas, colas)."""
    w1 = w0 if w1 is None else w1
    p = B.curva(pts, n) if len(pts) > 2 else list(pts)
    m = len(p)
    izq, der = [], []
    for i, (x, y) in enumerate(p):
        a, b = p[max(0, i - 1)], p[min(m - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        w = (w0 + (w1 - w0) * i / max(1, m - 1)) / 2
        izq.append((x + nx * w, y + ny * w))
        der.append((x - nx * w, y - ny * w))
    return izq + der[::-1]


def _tp(pts, x, y, s=1.0, ang=0.0, fl=1):
    """Lleva puntos locales (con y volteable) a su sitio: escala s, giro ang y desplazamiento (x, y)."""
    ca, sa = math.cos(ang), math.sin(ang)
    return [(x + (px * ca - py * fl * sa) * s, y + (px * sa + py * fl * ca) * s) for px, py in pts]


def _p1(p, x, y, s=1.0, ang=0.0, fl=1):
    return _tp([p], x, y, s, ang, fl)[0]


def _ojo(L, x, y, r, dx=0.0, dy=0.0):
    L.circ(x, y, r)
    L.alto(0)
    L.circ(x + dx, y + dy, r * .58)
    L.hondo(2)
    L.circ(x + dx - r * .18, y + dy - r * .22, r * .2)
    L.alto(0)


def _espiral(L, x, y, r, vueltas=2.2, w=2, sg=1, n=36):
    pts = []
    for j in range(n + 1):
        t = j / n
        a = t * vueltas * 2 * PI
        pts.append((x + sg * r * (.15 + .85 * t) * math.cos(a), y + r * (.15 + .85 * t) * math.sin(a)))
    L.lin(pts, w)


def _plumas(L, ox, oy, a0, a1, n, largo, ancho, tono, nerv=True):
    """Abanico de plumas desde (ox, oy), angulos en grados."""
    angs = []
    for q in range(n):
        a = math.radians(a0 + (a1 - a0) * q / max(1, n - 1))
        lg = largo * (1 - .1 * abs(q - (n - 1) / 2) / n)
        angs.append((a, lg))
        L.pol(B.hoja(ox, oy, a, lg, ancho))
    L.alto(tono)
    if nerv:
        for a, lg in angs:
            L.lin([(ox + lg * .12 * math.cos(a), oy + lg * .12 * math.sin(a)), (ox + lg * .86 * math.cos(a), oy + lg * .86 * math.sin(a))], 1.5)
        L.hondo(2)


def _chevrones(L, pts, ancho, paso=3, w=1.5):
    """Escamas en media luna a lo largo de una linea central pts (ya suavizada)."""
    for i in range(1, len(pts) - 1, paso):
        a = math.atan2(pts[i + 1][1] - pts[i - 1][1], pts[i + 1][0] - pts[i - 1][0])
        x, y = pts[i]
        L.lin(B.arco(x - math.cos(a) * ancho * .2, y - math.sin(a) * ancho * .2, ancho * .45, ancho * .45, a - 1.1, a + 1.1, 5), w)


def _sonrisa(L, x, y, r, w=2, sg=1):
    L.lin(B.arco(x, y, r, r * .6, .25, PI - .25, 8), w)


def _greca_h(L, x0, x1, y, h, w=2, inv=1):
    """Greca griega (llave) horizontal de x0 a x1, con ganchos de alto h hacia inv (+1 abajo, -1 arriba)."""
    paso = h * 1.5
    n = max(1, int((x1 - x0) / paso))
    L.lin([(x0, y), (x0 + n * paso, y)], w)
    for k in range(n):
        a = x0 + k * paso
        pts = [(a, y), (a, y + inv * h), (a + h, y + inv * h), (a + h, y + inv * h * .3), (a + h * .45, y + inv * h * .3), (a + h * .45, y + inv * h * .65)]
        L.lin(pts, w)


def _greca_v(L, y0, y1, x, h, w=2, inv=1):
    paso = h * 1.5
    n = max(1, int((y1 - y0) / paso))
    L.lin([(x, y0), (x, y0 + n * paso)], w)
    for k in range(n):
        a = y0 + k * paso
        pts = [(x, a), (x + inv * h, a), (x + inv * h, a + h), (x + inv * h * .3, a + h), (x + inv * h * .3, a + h * .45), (x + inv * h * .65, a + h * .45)]
        L.lin(pts, w)


def _nubes_polvo(L, x, y, r):
    for dx, dy, q in ((-1, .3, .8), (0, 0, 1), (1.1, .2, .7)):
        L.circ(x + dx * r, y + dy * r, r * q * .6)


# ---------------------------------------------------------------- 0. Pegaso (alas abiertas, perfil)
def _m_pegaso(L):
    ox, oy = -.02, -.05
    # alas detras del caballo
    for n, lg, an, tono, a0, a1 in ((10, .86, .14, 2, -176, -52), (9, .66, .13, 1, -168, -60), (7, .44, .11, 0, -158, -70)):
        _plumas(L, ox, oy, a0, a1, n, lg, an, tono)
    # cola ondulada
    L.pol(_trazo([(-.38, .1), (-.6, .1), (-.74, .28), (-.62, .5), (-.7, .64)], .08, .24))
    L.alto(0)
    for dy in (-.06, .0, .06):
        L.lin(B.curva([(-.42, .12 + dy), (-.62, .12 + dy), (-.7 + dy, .3), (-.6 - dy, .5), (-.66, .6)], 6), 1.5)
    L.hondo(2)
    # cuerpo (un solo relieve: cuerpo, cuello, cabeza y patas)
    L.elip(-.05, .16, .42, .2)
    L.pol(_trazo([(.18, .14), (.32, -.08), (.45, -.3)], .42, .21))
    L.pol(B.elipse(.57, -.37, .22, .115, .75))
    L.pol(_trazo([(.25, .22), (.31, .48), (.29, .72)], .15, .09))
    L.pol(_trazo([(.12, .24), (.36, .4), (.33, .58)], .15, .09))
    L.pol(_trazo([(-.32, .24), (-.4, .5), (-.46, .74)], .17, .09))
    L.pol(_trazo([(-.2, .26), (-.1, .48), (-.2, .7)], .17, .09))
    L.alto(1)
    # pezunas y orejas
    for (x, y) in ((.29, .73), (.33, .59), (-.46, .75), (-.2, .71)):
        L.pol([(x - .06, y - .02), (x + .07, y - .02), (x + .08, y + .06), (x - .07, y + .06)])
    L.pol([(.44, -.46), (.45, -.66), (.54, -.5)])
    L.alto(2)
    # cubre-hombro del ala
    L.circ(ox, oy, .11)
    L.alto(0)
    for j in range(6):
        a = j * PI / 3
        L.lin([(ox + .03 * math.cos(a), oy + .03 * math.sin(a)), (ox + .09 * math.cos(a), oy + .09 * math.sin(a))], 1.5)
    L.hondo(2)
    # crin: mechones sobre el cuello
    for j in range(7):
        t = j / 6
        bx, by = .12 + .3 * t, -.06 - .4 * t
        L.pol(_trazo([(bx, by), (bx - .09, by - .05), (bx - .18, by + .01), (bx - .22, by + .12)], .1, .01))
    L.alto(0)
    for j in range(7):
        t = j / 6
        bx, by = .12 + .3 * t, -.06 - .4 * t
        L.lin(B.curva([(bx - .02, by), (bx - .09, by - .03), (bx - .16, by + .02)], 4), 1.5)
    L.hondo(2)
    # mechon sobre la frente
    L.pol(_trazo([(.46, -.48), (.52, -.55), (.62, -.5)], .07, .02))
    L.alto(0)
    # cara
    _ojo(L, .56, -.42, .045, .008, .004)
    L.circ(.7, -.27, .016)
    L.hondo(2)
    L.lin([(.64, -.22), (.58, -.26), (.54, -.3)], 1.5)
    L.hondo(2)
    # adornos del cuerpo: espiral en la anca, puntos en la barriga, medallon en el pecho
    _espiral(L, -.28, .1, .12, 2.0, 2)
    L.hondo(2)
    for j in range(8):
        L.circ(-.34 + j * .075, .3 - .02 * math.sin(j / 7 * PI), .014)
    L.hondo(2)
    for j in range(4):
        L.lin([(-.08 + j * .06, -.0), (-.04 + j * .06, .08)], 1.5)
    L.hondo(2)
    L.circ(.27, .06, .06)
    L.alto(0)
    L.circ(.27, .06, .025)
    L.hondo(2)
    # articulaciones de las patas
    for (x, y) in ((.3, .5), (.35, .42), (-.4, .5), (-.1, .48)):
        L.lin(B.arco(x, y, .05, .03, .2, PI - .2, 5), 1.5)
    L.hondo(2)
    # estrellitas alrededor
    for (x, y) in ((.72, -.6), (-.78, .55), (.68, .45)):
        L.pol([(x + (.07 if j % 2 == 0 else .025) * math.cos(j * PI / 4 - PI / 2), y + (.07 if j % 2 == 0 else .025) * math.sin(j * PI / 4 - PI / 2)) for j in range(8)])
    L.alto(0)


# ---------------------------------------------------------------- 1. Centauro (galopa, con arco)
def _m_centauro(L):
    # lineas de velocidad y polvo
    for j in range(4):
        L.lin([(-.95 + j * .02, -.05 + j * .13), (-.72, -.05 + j * .13)], 2)
    L.hondo(2)
    # cola
    L.pol(_trazo([(-.55, .08), (-.74, .0), (-.84, -.16), (-.8, -.32)], .05, .16))
    L.alto(0)
    for dd in (-.04, .04):
        L.lin(B.curva([(-.58, .08 + dd), (-.74, .0 + dd), (-.82 + dd, -.14), (-.78 + dd, -.28)], 5), 1.5)
    L.hondo(2)
    # cuerpo de caballo y patas al galope
    L.pol(B.elipse(-.2, .2, .42, .21, -.1))
    L.circ(.1, .16, .2)
    L.pol(_trazo([(.06, .3), (.2, .52), (.26, .72)], .18, .09))
    L.pol(_trazo([(.0, .3), (.22, .38), (.13, .56)], .17, .09))
    L.pol(_trazo([(-.5, .28), (-.58, .5), (-.68, .7)], .2, .09))
    L.pol(_trazo([(-.42, .3), (-.62, .38), (-.8, .3)], .19, .09))
    L.alto(1)
    for (x, y, a) in ((.27, .73, .0), (.12, .58, .2), (-.69, .71, .3), (-.81, .29, 2.9)):
        L.pol(_tp([(-.07, -.04), (.07, -.04), (.08, .05), (-.07, .05)], x, y, 1, a))
    L.alto(2)
    # polvo
    _nubes_polvo(L, -.55, .8, .06)
    L.alto(0, .7)
    # manta de silla con greca
    L.pol([(-.34, -.04), (-.06, -.02), (-.04, .3), (-.38, .32)])
    L.alto(0)
    _greca_h(L, -.34, -.08, .08, .07, 1.5)
    L.hondo(2)
    L.lin([(-.36, .24), (-.06, .24)], 2)
    L.hondo(2)
    for j in range(5):
        L.circ(-.33 + j * .06, .28, .012)
    L.hondo(2)
    # lunares y pelaje
    for (x, y) in ((-.52, .12), (-.48, .26), (-.14, .36), (-.58, .22)):
        L.circ(x, y, .03)
    L.hondo(2, .7)
    for j in range(4):
        L.lin([(-.5 + j * .05, .0), (-.46 + j * .05, .05)], 1.5)
    L.hondo(2)
    # aljaba a la espalda con flechas
    L.pol(B.rotar([(-.05, -.18), (.05, -.18), (.07, .2), (-.07, .2)], -.35, .0, -.28))
    L.alto(2)
    for j in range(3):
        a = -1.9 + j * .12
        L.lin([(-.05 + j * .03, -.4), (-.08 + j * .03 - .1 * j * .0, -.62)], 2)
    L.alto(0)
    for j in range(3):
        L.pol(B.hoja(-.09 + j * .035, -.7, -1.85 - j * .05, .07, .03))
    L.alto(1)
    # torso humano
    L.pol(_trazo([(.12, .2), (.18, -.02), (.22, -.24)], .34, .3))
    L.circ(.22, -.22, .16)
    L.alto(0)
    # cabeza y pelo
    L.circ(.26, -.46, .125)
    L.alto(0)
    L.pol([(.14, -.5), (.18, -.62), (.3, -.65), (.4, -.58), (.4, -.5), (.33, -.55), (.22, -.52)])
    L.pol(_trazo([(.16, -.52), (.08, -.46), (.06, -.34)], .08, .03))
    L.alto(2)
    _ojo(L, .31, -.47, .024, .005, .003)
    _sonrisa(L, .31, -.4, .05, 1.5)
    L.hondo(2)
    L.circ(.26, -.43, .02)
    L.hondo(1, .5)
    # banda cruzada y detalles del torso
    L.lin([(.05, -.23), (.34, .05)], 4)
    L.alto(2)
    L.lin([(.15, -.04), (.19, -.02)], 1.5)
    L.lin([(.24, -.12), (.28, -.1)], 1.5)
    L.hondo(2)
    L.lin(B.arco(.2, -.08, .1, .07, .3, PI - .3, 6), 1.5)
    L.hondo(2)
    # brazo con el arco
    L.pol(_trazo([(.28, -.24), (.45, -.2), (.62, -.3)], .09, .07))
    L.alto(0)
    L.pol(_trazo([(.14, -.22), (.1, -.05), (.1, .1)], .08, .06))
    L.alto(0)
    arco = B.arco(.38, -.3, .24, .44, -PI / 2, PI / 2, 14)
    L.lin(arco, 5)
    L.alto(2)
    L.lin([arco[0], arco[-1]], 1.5)
    L.alto(0)
    L.circ(.62, -.3, .045)
    L.alto(0)
    L.lin([(.6, -.3), (.64, -.3)], 1.5)
    L.hondo(2)
    # flecha lista
    L.lin([(.1, -.3), (.62, -.3)], 2)
    L.alto(2)
    L.pol([(.62, -.35), (.74, -.3), (.62, -.25)])
    L.alto(1)
    # crin del caballo
    for j in range(5):
        L.pol(_trazo([(.0 - j * .07, .05 + j * .02), (-.1 - j * .07, .0 + j * .02), (-.16 - j * .07, .08 + j * .02)], .07, .01))
    L.alto(0)
    # estrellas
    for (x, y) in ((.7, .62), (-.15, -.72)):
        L.pol([(x + (.06 if j % 2 == 0 else .02) * math.cos(j * PI / 4 - PI / 2), y + (.06 if j % 2 == 0 else .02) * math.sin(j * PI / 4 - PI / 2)) for j in range(8)])
    L.alto(0)


# ---------------------------------------------------------------- 2. Minotauro (frente, con laberinto)
def _m_minotauro(L):
    # laberinto: espiral cuadrada detras
    pts = []
    h, cx, cy = .74, 0.0, .02
    x0, y0, x1, y1 = cx - h, cy - h, cx + h, cy + h
    paso = .085
    while x1 - x0 > .1:
        pts += [(x0, y0), (x1, y0), (x1, y1), (x0 + paso, y1)]
        x0, y0, x1, y1 = x0 + paso, y0 + paso, x1 - paso, y1 - paso
        pts.append((x0 - paso, y1 + paso))
        pts.pop()
        pts.append((x0 - paso, y0))
        pts.pop()
        pts.append((x0 - paso, y0))
        pts.pop()
    L.lin(pts, 2.5)
    L.hondo(2)
    # cuerpo: torso
    L.pol(B.simetrico([(.05, -.2), (.3, -.18), (.43, -.06), (.36, .16), (.25, .32)]))
    L.alto(1)
    # brazos en la cintura
    for sg in (-1, 1):
        L.pol(_trazo([(sg * .4, -.1), (sg * .6, .1), (sg * .3, .27)], .15, .12))
    L.alto(1)
    for sg in (-1, 1):
        L.circ(sg * .3, .27, .06)
    L.alto(0)
    # falda con pliegues y greca
    L.pol([(-.27, .28), (.27, .28), (.36, .72), (-.36, .72)])
    L.alto(0)
    for j in range(7):
        x = -.3 + j * .1
        L.lin([(x * .8, .32), (x * 1.1 if abs(x) > .01 else x, .7)], 1.5)
    L.hondo(2)
    _greca_h(L, -.33, .33, .62, .05, 1.5, 1)
    L.hondo(2)
    # cinturon con hebilla
    L.rect(0, .28, .27, .04)
    L.alto(2)
    L.circ(0, .28, .06)
    L.alto(0)
    L.circ(0, .28, .025)
    L.hondo(2)
    # piernas y pezunas
    for sg in (-1, 1):
        L.pol(_trazo([(sg * .13, .7), (sg * .15, .85)], .17, .15))
    L.alto(1)
    for sg in (-1, 1):
        L.pol([(sg * .06, .83), (sg * .23, .83), (sg * .26, .92), (sg * .04, .92)])
    L.alto(2)
    # pecho: pectorales, ombligo, pelo
    L.lin(B.arco(-.15, -.02, .14, .09, .2, PI - .2, 8), 2)
    L.lin(B.arco(.15, -.02, .14, .09, .2, PI - .2, 8), 2)
    L.lin([(0, .08), (0, .16)], 2)
    L.circ(0, .2, .02)
    L.hondo(2)
    for sg in (-1, 1):
        L.lin([(sg * .38, .0), (sg * .5, .06)], 1.5)
        L.lin([(sg * .38, .06), (sg * .5, .12)], 1.5)
    L.hondo(2)
    # collar y brazaletes
    L.lin(B.arco(0, -.17, .26, .15, .1, PI - .1, 10), 3)
    L.alto(0)
    for j in range(7):
        a = .3 + j * (PI - .6) / 6
        L.circ(.26 * math.cos(a), -.17 + .15 * math.sin(a), .017)
    L.hondo(2)
    # cuernos
    for sg in (-1, 1):
        L.pol(_trazo([(sg * .13, -.48), (sg * .34, -.5), (sg * .48, -.62), (sg * .46, -.8)], .13, .02))
    L.alto(0)
    for sg in (-1, 1):
        L.lin(B.curva([(sg * .15, -.48), (sg * .34, -.49), (sg * .46, -.6)], 5), 1.5)
    L.hondo(2)
    # orejas
    for sg in (-1, 1):
        L.pol(_tp([(0, 0), (.1, -.07), (.22, -.04), (.28, .06), (.2, .1), (.08, .08)], sg * .17, -.34, 1, 0 if sg == 1 else PI, 1 if sg == 1 else -1))
    L.alto(1)
    for sg in (-1, 1):
        L.pol(_tp([(.07, .0), (.13, -.03), (.2, .0), (.15, .04)], sg * .17, -.34, 1, 0 if sg == 1 else PI, 1 if sg == 1 else -1))
    L.hondo(2)
    # cabeza de toro
    L.elip(0, -.36, .21, .24)
    L.alto(1)
    # mechon de pelo
    L.pol(_trazo([(-.1, -.58), (-.02, -.64), (.08, -.6), (.12, -.52)], .09, .03))
    L.alto(2)
    # hocico
    L.elip(0, -.25, .15, .12)
    L.alto(0)
    L.circ(-.065, -.23, .018)
    L.circ(.065, -.23, .018)
    L.hondo(2)
    # anillo en la nariz
    L.lin(B.arco(0, -.2, .04, .05, 0, PI, 8), 2)
    L.alto(0)
    # ojos amistosos y cejas
    for sg in (-1, 1):
        _ojo(L, sg * .09, -.4, .04, 0, .004)
        L.lin([(sg * .04, -.47), (sg * .1, -.5), (sg * .16, -.46)], 2)
    L.hondo(2)
    _sonrisa(L, 0, -.2, .08, 1.5)
    L.hondo(2)
    # lunares del hocico
    for (x, y) in ((-.1, -.3), (.1, -.3), (-.04, -.3), (.04, -.3)):
        L.circ(x, y, .008)
    L.hondo(2)
    # esquinas griegas
    for (x, y) in ((-.8, -.76), (.8, -.76)):
        L.rect(x, y, .07, .07, 2)
        L.rect(x, y, .03, .03)
    L.hondo(2)


# ---------------------------------------------------------------- 3. Cerbero (tres cabezas, de frente)
def _cabeza_perro(L, x, y, s, ang, expr):
    def T(pts):
        return _tp(pts, x, y, s, ang)

    def C(lx, ly):
        return _p1((lx, ly), x, y, s, ang)

    # orejas colgantes
    for sg in (-1, 1):
        L.pol(T([(sg * .65, -.75), (sg * 1.25, -.35), (sg * 1.2, .7), (sg * .8, .55), (sg * .7, -.1)]))
    L.alto(2)
    for sg in (-1, 1):
        L.pol(T([(sg * .75, -.5), (sg * 1.05, -.3), (sg * 1.02, .4), (sg * .85, .3)]))
    L.hondo(2, .6)
    # craneo y hocico
    L.pol(T(B.elipse(0, -.05, .88, .85, 0, 28)))
    L.alto(1)
    L.pol(T(B.elipse(0, .42, .52, .44, 0, 24)))
    L.alto(0)
    # mancha de la frente
    L.pol(T([(0, -.85), (.14, -.6), (0, -.42), (-.14, -.6)]))
    L.hondo(2)
    # nariz
    L.pol(T(B.elipse(0, .22, .22, .14, 0, 14)))
    L.alto(2)
    cx, cy = C(-.08, .17)
    L.circ(cx, cy, .007 * s / .2)
    L.alto(0)
    # ojos y cejas segun la expresion
    for sg in (-1, 1):
        ex, ey = C(sg * .38, -.2)
        r = .17 * s
        if expr == 0 and True:      # cerrados y felices
            L.lin(B.arco(ex, ey + .02 * s, r, r * .8, PI + .3, 2 * PI - .3, 7), 2.5)
            L.hondo(2)
        elif expr == 2 and sg == 1:  # guino
            L.lin([C(.2, -.2), C(.5, -.14)], 2.5)
            L.hondo(2)
        else:
            _ojo(L, ex, ey, r, 0, .01)
        bx0, by0 = C(sg * .18, -.45)
        bx1, by1 = C(sg * .6, -.5)
        L.lin([(bx0, by0), (bx1, by1)], 2)
        L.hondo(2)
    # boca
    if expr == 1:  # boca abierta con lengua
        L.pol(T([(-.36, .55), (.36, .55), (.28, .85), (0, .95), (-.28, .85)]))
        L.hondo(2)
        L.pol(T(B.elipse(0, .85, .17, .2, 0, 12)))
        L.alto(0)
        L.lin([C(0, .72), C(0, .98)], 1.5)
        L.hondo(2)
        L.pol(T([(-.2, .55), (-.1, .55), (-.15, .66)]))
        L.pol(T([(.1, .55), (.2, .55), (.15, .66)]))
        L.alto(0)
    else:
        L.lin(T([(0, .36), (0, .5)]), 2)
        L.lin(T(B.arco(-.17, .5, .17, .1, 0, PI * .85, 6)), 2)
        L.lin(T(B.arco(.17, .5, .17, .1, PI * .15, PI, 6)), 2)
        L.hondo(2)
        if expr == 2:
            L.pol(T(B.elipse(.34, .68, .1, .15, -.4, 12)))
            L.alto(2)
    # pecas
    for sg in (-1, 1):
        for q in range(3):
            fx, fy = C(sg * (.3 + q * .06), .12 + q * .03)
            L.circ(fx, fy, .006 * s / .2)
    L.hondo(2, .7)
    # collar con medallon
    L.pol(_trazo(T([(-.85, 1.0), (0, 1.22), (.85, 1.0)]), .17 * s, .17 * s))
    L.alto(2)
    for q in range(7):
        t = -.7 + q * .233
        px, py = C(t, 1.1 + .1 * (1 - t * t / .5 * .4) * 0)
        L.circ(px, py + .05 * s * (1 - (t / .85) ** 2), .028 * s)
    L.alto(0)
    mx, my = C(0, 1.25)
    L.circ(mx, my, .075 * s)
    L.alto(0)
    L.circ(mx, my, .03 * s)
    L.hondo(2)


def _m_cerbero(L):
    # cola con punta
    L.pol(_trazo([(.55, .55), (.78, .5), (.86, .3), (.76, .12)], .09, .15))
    L.alto(0)
    L.circ(.74, .1, .08)
    L.alto(1)
    # cuello de las cabezas laterales
    for sg in (-1, 1):
        L.pol(_trazo([(sg * .2, .25), (sg * .42, .05), (sg * .54, -.1)], .3, .3))
    L.pol(_trazo([(0, .25), (0, .0), (0, -.15)], .4, .38))
    L.alto(1)
    # ancas, pecho, patas delanteras
    for sg in (-1, 1):
        L.pol(B.elipse(sg * .46, .52, .21, .27, 0))
    L.elip(0, .38, .4, .38)
    for sg in (-1, 1):
        L.pol(_trazo([(sg * .17, .5), (sg * .18, .85)], .17, .15))
    L.alto(1)
    # patas y garras
    for sg in (-1, 1):
        L.pol(B.elipse(sg * .18, .88, .13, .06, 0, 12))
        L.pol(B.elipse(sg * .56, .83, .13, .06, 0, 12))
    L.alto(0)
    for sg in (-1, 1):
        for q in range(3):
            L.lin([(sg * .18 + (q - 1) * .06, .88), (sg * .18 + (q - 1) * .06, .94)], 1.5)
            L.lin([(sg * .56 + (q - 1) * .06, .83), (sg * .56 + (q - 1) * .06, .89)], 1.5)
    L.hondo(2)
    # pelaje del pecho
    L.pol([(-.3, .25), (0, .62), (.3, .25), (.2, .22), (0, .45), (-.2, .22)])
    L.alto(0)
    for fila in range(3):
        for q in range(4 - fila):
            x = (q - (3 - fila - 1) / 2) * .13
            y = .3 + fila * .12
            L.lin([(x - .05, y), (x, y + .07), (x + .05, y)], 1.5)
    L.hondo(2)
    for sg in (-1, 1):
        L.lin(B.curva([(sg * .5, .34), (sg * .44, .5), (sg * .5, .66)], 4), 1.5)
        for q in range(3):
            L.lin([(sg * (.4 + q * .06), .42), (sg * (.45 + q * .06), .48)], 1.5)
    L.hondo(2)
    # tres cabezas
    _cabeza_perro(L, -.55, -.24, .25, -.3, 0)
    _cabeza_perro(L, .55, -.24, .25, .3, 2)
    _cabeza_perro(L, 0, -.38, .31, 0, 1)
    # estrellas
    for (x, y) in ((-.8, .55), (.82, -.65), (-.82, -.72)):
        L.pol([(x + (.06 if j % 2 == 0 else .02) * math.cos(j * PI / 4 - PI / 2), y + (.06 if j % 2 == 0 else .02) * math.sin(j * PI / 4 - PI / 2)) for j in range(8)])
    L.alto(0)


# ---------------------------------------------------------------- 4. Hidra (cinco cuellos y estanque)
def _cabeza_serp(L, x, y, s, ang, fl, tipo):
    def T(pts):
        return _tp(pts, x, y, s, ang, fl)

    def C(lx, ly):
        return _p1((lx, ly), x, y, s, ang, fl)

    # adornos que van detras
    if tipo == 0:   # abanico de plumas
        for q in range(5):
            a = -2.5 + q * .35
            L.pol(T(B.hoja(-.2, -.1, a, 1.1, .2)))
        L.alto(2)
    elif tipo == 2:  # gola de cresta
        for q in range(7):
            a = PI * .55 + q * (PI * .9 / 6)
            L.pol(T(B.hoja(-.3, 0, a, 1.2, .16)))
        L.alto(0)
        for q in range(7):
            a = PI * .55 + q * (PI * .9 / 6)
            L.lin(T([(-.3 + .2 * math.cos(a), .2 * math.sin(a)), (-.3 + 1.0 * math.cos(a), 1.0 * math.sin(a))]), 1.5)
        L.hondo(2)
    elif tipo == 4:  # pinchos de lomo
        for q in range(4):
            L.pol(T([(-.9 + q * .35, -.6), (-.78 + q * .35, -1.1), (-.55 + q * .35, -.65)]))
        L.alto(2)
    # cabeza
    L.pol(T(B.elipse(0, 0, 1.25, .82, 0, 26)))
    L.alto(0)
    L.pol(T(B.elipse(.5, .12, .85, .5, 0, 22)))
    L.alto(1, .6)
    # adornos delanteros
    if tipo == 1:   # cuernitos
        for sg in (-.15, .45):
            L.pol(T([(sg - .12, -.7), (sg + .02, -1.35), (sg + .16, -.7)]))
        L.alto(2)
    elif tipo == 3:  # orejitas redondas y lunares
        L.circ(*C(-.4, -.75), .12 * s)
        L.alto(1)
        for (px, py) in ((-.6, .0), (-.9, .3), (-.3, .2)):
            L.circ(*C(px, py), .08 * s)
        L.hondo(2)
    elif tipo == 4:  # antena con bola
        L.lin(T([(.1, -.75), (.2, -1.1), (.5, -1.3)]), 2)
        L.alto(2)
        L.circ(*C(.5, -1.3), .1 * s)
        L.alto(0)
    elif tipo == 2:  # corona
        L.pol(T([(-.35, -.75), (-.35, -1.1), (-.15, -.9), (0, -1.2), (.15, -.9), (.35, -1.1), (.35, -.75)]))
        L.alto(0)
    # ojo, narinas, sonrisa, lengua
    ex, ey = C(.35, -.22)
    _ojo(L, ex, ey, .26 * s, .012, .006)
    L.circ(*C(1.1, -.12), .05 * s)
    L.hondo(2)
    L.lin(T(B.arco(.55, .1, .6, .35, .15, 1.2, 8)), 1.5)
    L.hondo(2)
    if tipo in (1, 4):
        L.lin(T([(1.2, .2), (1.55, .28), (1.8, .18)]), 2)
        L.lin(T([(1.55, .28), (1.85, .38)]), 2)
        L.hondo(2)
    # pecas / manchas del hocico
    for q in range(3):
        L.circ(*C(-.2 + q * .22, .38), .035 * s)
    L.hondo(2, .7)


def _m_hidra(L):
    # estanque
    L.pol(B.elipse(0, .68, .92, .27, 0, 32))
    L.alto(2, .55)
    for q in range(3):
        L.pol(B.elipse(0, .68, .86 - q * .2, .24 - q * .06, 0, 32), 2)
    L.hondo(2, .6)
    # cinco cuellos y sus cabezas (los de fuera primero)
    necks = [
        ([(-.26, .45), (-.5, .3), (-.56, .05), (-.5, -.15), (-.68, -.18)], (-.7, -.18), PI + .3, -1, 0, .17),
        ([(.26, .45), (.5, .3), (.56, .05), (.5, -.15), (.68, -.18)], (.7, -.18), -.3, 1, 4, .17),
        ([(-.13, .45), (-.3, .2), (-.16, -.1), (-.32, -.38), (-.4, -.58)], (-.42, -.6), PI + .6, -1, 1, .17),
        ([(.13, .45), (.3, .2), (.16, -.1), (.32, -.38), (.4, -.58)], (.42, -.6), -.6, 1, 3, .17),
        ([(0, .45), (.1, .2), (-.1, -.1), (-.12, -.45), (-.05, -.7)], (-.02, -.72), -.2, 1, 2, .21),
    ]
    for pts, _h, _a, _f, _t, _s in necks:
        sp = B.curva(pts, 6)
        L.pol(_trazo(pts, .2, .12))
        L.alto(1)
        L.pol(_trazo(pts, .09, .05))
        L.alto(0)
        _chevrones(L, sp, .17, 3, 1.5)
        L.hondo(2)
    for pts, (hx, hy), ang, fl, tipo, s in necks:
        _cabeza_serp(L, hx, hy, s, ang, fl, tipo)
    # cuerpo
    L.elip(0, .52, .36, .22)
    L.alto(1)
    L.elip(0, .55, .24, .13)
    L.alto(0)
    for j in range(3):
        L.lin(B.arco(-.15 + j * .15, .5, .09, .09, .3, PI - .3, 6), 1.5)
        L.lin(B.arco(-.075 + j * .15, .58, .09, .09, .3, PI - .3, 6), 1.5)
    L.hondo(2)
    # agua delante: la parte baja del estanque con olas
    top = [(-.92 + 1.84 * t / 30, .68 + .02 * math.sin(t / 30 * 6 * PI)) for t in range(31)]
    L.pol(top + B.arco(0, .68, .92, .27, 0, PI, 18)[::-1])
    L.alto(2, .7)
    for j, y in enumerate((.76, .84)):
        L.lin(B.ondas(-.6 + .1 * j, y, .6 - .1 * j, y, .02, 4 + j % 2), 2)
    L.hondo(2)
    for (x, y, r) in ((-.6, .55, .035), (.62, .54, .03), (.5, .4, .025), (-.5, .42, .02), (-.78, .66, .025)):
        L.circ(x, y, r, 2)
    L.alto(0)


# ---------------------------------------------------------------- 5. Quimera (leon, cabra y serpiente)
def _estrella(L, x, y, r):
    L.pol([(x + (r if j % 2 == 0 else r * .35) * math.cos(j * PI / 4 - PI / 2), y + (r if j % 2 == 0 else r * .35) * math.sin(j * PI / 4 - PI / 2)) for j in range(8)])


def _m_quimera(L):
    # cola de serpiente que sube por detras
    cola = [(-.5, .24), (-.74, .26), (-.84, .02), (-.74, -.22), (-.82, -.42)]
    L.pol(_trazo(cola, .1, .17))
    L.alto(1)
    sp = B.curva(cola, 6)
    _chevrones(L, sp, .12, 2, 1.5)
    L.hondo(2)
    L.pol(B.elipse(-.78, -.54, .17, .11, -.9, 16))
    L.alto(0)
    _ojo(L, -.76, -.58, .03, .004, .003)
    L.lin([(-.7, -.62), (-.66, -.72), (-.6, -.7)], 2)
    L.lin([(-.66, -.72), (-.62, -.78)], 2)
    L.hondo(2)
    for j in range(3):
        L.circ(-.84 + j * .04, -.46 + j * .0, .012)
    L.hondo(2)
    # cuerpo de leon y patas
    L.pol(B.elipse(-.1, .22, .5, .24, 0))
    for (a, b, c, w) in (((.24, .3), (.3, .55), (.27, .76), .2), ((.06, .34), (.02, .55), (.04, .76), .2),
                         ((-.34, .3), (-.42, .55), (-.4, .76), .22), ((-.5, .28), (-.6, .5), (-.6, .72), .2)):
        L.pol(_trazo([a, b, c], w, w * .75))
    L.alto(1)
    for (x, y) in ((.27, .77), (.04, .77), (-.4, .77), (-.6, .73)):
        L.pol(B.elipse(x, y, .12, .055, 0, 12))
    L.alto(0)
    for (x, y) in ((.27, .77), (.04, .77), (-.4, .77), (-.6, .73)):
        for q in range(3):
            L.lin([(x + (q - 1) * .05, y), (x + (q - 1) * .05, y + .06)], 1.5)
    L.hondo(2)
    # pelaje del lomo y de las patas
    for j in range(10):
        x = -.56 + j * .1
        L.lin(B.arco(x, .08 + .03 * math.sin(j * 1.3), .06, .06, .3, PI - .3, 5), 1.5)
        L.lin(B.arco(x + .05, .2, .06, .06, .3, PI - .3, 5), 1.5)
    for (x, y) in ((.3, .6), (.04, .6), (-.42, .6), (-.6, .55)):
        L.lin([(x - .03, y), (x, y + .05), (x + .03, y)], 1.5)
        L.lin([(x - .03, y + .08), (x, y + .13), (x + .03, y + .08)], 1.5)
    L.hondo(2)
    # banda griega del costado y espiral en la anca
    L.rect(-.1, .4, .32, .028)
    L.alto(0)
    for j in range(9):
        L.circ(-.38 + j * .075, .4, .01)
    L.hondo(2)
    _espiral(L, -.4, .18, .1, 2.0, 2)
    L.hondo(2)
    # cuello y cabeza de cabra que salen del lomo
    L.pol(_trazo([(-.12, .06), (-.14, -.1), (-.1, -.26)], .3, .22))
    L.alto(0)
    for j in range(3):
        y = .0 - j * .08
        L.lin([(-.22, y + .02), (-.15, y + .06), (-.08, y + .02)], 1.5)
    L.hondo(2)
    # cuernos largos hacia atras con anillos
    L.pol(_trazo([(-.06, -.5), (-.2, -.64), (-.38, -.64), (-.46, -.5)], .11, .02))
    L.alto(2)
    for t in (.3, .5, .7):
        x = -.06 + (-.46 + .06) * t
        L.lin([(x - .02, -.5 - .22 * math.sin(t * PI) - .0), (x + .02, -.58 - .16 * math.sin(t * PI))], 1.5)
    L.hondo(0)
    # orejas
    L.pol(B.elipse(-.2, -.4, .14, .045, .3))
    L.alto(1)
    # craneo, hocico
    L.pol(B.elipse(-.02, -.4, .18, .14, .3))
    L.alto(0)
    L.pol(B.elipse(.12, -.32, .15, .085, .6))
    L.alto(1)
    # barba
    L.pol([(.1, -.26), (.04, -.1), (.12, -.16), (.16, -.28)])
    L.alto(2)
    L.circ(.0, -.44, .04)
    L.alto(0)
    L.rect(.0, -.44, .009, .03)
    L.hondo(2)
    L.circ(.2, -.3, .014)
    L.hondo(2)
    _sonrisa(L, .13, -.25, .05, 1.5)
    L.hondo(2)
    L.lin([(-.08, -.52), (-.02, -.56), (.04, -.52)], 2)
    L.hondo(2)
    # cabeza de leon con melena grande
    cx, cy = .56, .04
    L.circ(cx, cy, .36)
    L.alto(2)
    for j in range(16):
        a = j * 2 * PI / 16
        L.pol(B.hoja(cx + .25 * math.cos(a), cy + .25 * math.sin(a), a, .18, .075))
    L.alto(1)
    for j in range(16):
        a = j * 2 * PI / 16 + .2
        L.lin([(cx + .2 * math.cos(a), cy + .2 * math.sin(a)), (cx + .33 * math.cos(a), cy + .33 * math.sin(a))], 1.5)
    L.hondo(2)
    L.circ(cx, cy, .23)
    L.alto(0)
    for sg in (-1, 1):
        L.circ(cx + sg * .16, cy - .2, .065)
    L.alto(1)
    L.circ(cx - .16, cy - .2, .03)
    L.circ(cx + .16, cy - .2, .03)
    L.hondo(2)
    L.elip(cx, cy + .09, .13, .1)
    L.alto(1)
    L.pol([(cx - .06, cy + .03), (cx + .06, cy + .03), (cx, cy + .1)])
    L.alto(2)
    L.lin([(cx, cy + .1), (cx, cy + .15)], 2)
    L.lin(B.arco(cx - .07, cy + .15, .07, .05, 0, PI * .9, 6), 2)
    L.lin(B.arco(cx + .07, cy + .15, .07, .05, PI * .1, PI, 6), 2)
    L.hondo(2)
    for sg in (-1, 1):
        _ojo(L, cx + sg * .1, cy - .07, .04, 0, .004)
        L.lin([(cx + sg * .04, cy - .15), (cx + sg * .11, cy - .19), (cx + sg * .17, cy - .14)], 2)
    L.hondo(2)
    for q in range(3):
        for sg in (-1, 1):
            L.circ(cx + sg * (.08 + q * .025), cy + .08 + q * .02, .007)
    L.hondo(2)
    # estrellas
    for (x, y) in ((.82, -.62), (-.82, .64)):
        _estrella(L, x, y, .06)
    L.alto(0)


MOTIVOS = [_m_pegaso, _m_centauro, _m_minotauro, _m_cerbero, _m_hidra, _m_quimera]
