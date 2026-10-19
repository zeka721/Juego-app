"""Murales del mundo 5 de las Ruinas: LEYENDAS DEL MUNDO (Unicornio, Sirena, Grifo, Yeti, Fenix, Quetzalcoatl).
Relieves procedurales de arenisca para el lienzo _L de arte_ruinas. Sin aleatoriedad ni archivos externos."""
import math

import arte_mitos_base as B

NOMBRES = ['Unicornio', 'Sirena', 'Grifo', 'Yeti', 'Fénix', 'Quetzalcóatl']
PI = math.pi


# ------------------------------------------------------------------ utilidades
class _X:
    """Envoltorio del lienzo: dibujas en coordenadas de diseño y se escala/traslada (sx=-1 voltea en horizontal)."""

    def __init__(s, L, k=1.0, dx=0.0, dy=0.0, sx=1):
        s.L, s.k, s.dx, s.dy, s.sx = L, k, dx, dy, sx

    def _p(s, pts):
        return [(x * s.k * s.sx + s.dx, y * s.k + s.dy) for x, y in pts]

    def circ(s, x, y, r, w=0):
        s.L.circ(x * s.k * s.sx + s.dx, y * s.k + s.dy, r * s.k, w)

    def elip(s, x, y, rx, ry, w=0):
        s.L.elip(x * s.k * s.sx + s.dx, y * s.k + s.dy, rx * s.k, ry * s.k, w)

    def pol(s, pts, w=0):
        s.L.pol(s._p(pts), w)

    def lin(s, pts, w=2):
        s.L.lin(s._p(pts), w)

    def alto(s, t=1, f=1.0):
        s.L.alto(t, f)

    def hondo(s, t=1, f=1.0):
        s.L.hondo(t, f)


def _estr(x, y, r, k=.3, n=4, a0=-PI / 2):
    pts = []
    for j in range(2 * n):
        rr = r if j % 2 == 0 else r * k
        a = a0 + j * PI / n
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return pts


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _espiral(cx, cy, r0, r1, vueltas, a0=0.0, n=30):
    return [(cx + (r0 + (r1 - r0) * j / n) * math.cos(a0 + vueltas * 2 * PI * j / n),
             cy + (r0 + (r1 - r0) * j / n) * math.sin(a0 + vueltas * 2 * PI * j / n)) for j in range(n + 1)]


def _pir(w, h, ang=0.0, ox=0.0, oy=0.0):
    """Modulo de greca escalonada (piramide de tres escalones) con la base en (ox, oy) y la punta hacia 'arriba' girada ang."""
    p = [(-w / 2, 0), (-w / 2, -h / 3), (-w / 3, -h / 3), (-w / 3, -2 * h / 3), (-w / 6, -2 * h / 3), (-w / 6, -h),
         (w / 6, -h), (w / 6, -2 * h / 3), (w / 3, -2 * h / 3), (w / 3, -h / 3), (w / 2, -h / 3), (w / 2, 0)]
    return B.rotar(p, ang, ox, oy)


def _guarda(L, x0, x1, y, n, h=.11, t=1):
    """Fila de piramides escalonadas (greca) entre x0 y x1 con la base en y."""
    w = (x1 - x0) / n
    for j in range(n):
        L.pol(_pir(w * .92, h, 0, x0 + w * (j + .5), y))
    L.alto(t)
    for j in range(n):
        L.pol(_pir(w * .45, h * .55, 0, x0 + w * (j + .5), y - h * .1))
    L.hondo(2)


def _cinta(ctr, wf):
    """Poligono de cinta a lo largo de la poligonal ctr con semiancho wf(t). Devuelve (poligono, [(punto, tangente, normal)])."""
    n = len(ctr)
    izq, der, info = [], [], []
    for i, (x, y) in enumerate(ctr):
        a = ctr[max(0, i - 1)]
        b = ctr[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        d = math.hypot(tx, ty) or 1.0
        tx, ty = tx / d, ty / d
        nx, ny = -ty, tx
        w = wf(i / (n - 1))
        izq.append((x + nx * w, y + ny * w))
        der.append((x - nx * w, y - ny * w))
        info.append(((x, y), (tx, ty), (nx, ny)))
    return izq + der[::-1], info


def _ojo(X, x, y, r, mirada=0.0):
    """Ojo amable: blanco en relieve, pupila hundida y brillo."""
    X.circ(x, y, r)
    X.alto(0)
    X.circ(x + mirada * r * .3, y + r * .05, r * .62)
    X.hondo(2)
    X.circ(x + mirada * r * .3 - r * .2, y - r * .25, r * .2)
    X.alto(0)


def _copo(X, x, y, r, t=0):
    for j in range(3):
        a = j * PI / 3 + .2
        c, s = math.cos(a), math.sin(a)
        X.lin([(x - c * r, y - s * r), (x + c * r, y + s * r)], 2)
        for sg in (-1, 1):
            bx, by = x + sg * c * r * .6, y + sg * s * r * .6
            for sa in (-1, 1):
                a2 = a + sa * .8
                X.lin([(bx, by), (bx + sg * math.cos(a2) * r * .32, by + sg * math.sin(a2) * r * .32)], 1.5)
    X.alto(t)


def _brillo(X, x, y, r):
    X.pol(_estr(x, y, r, .22))
    X.alto(0)


def _pluma(X, x, y, ang, largo, ancho, nerv=True):
    """Pluma en poligono (con nervio central pendiente de hondo por el llamador via lista)."""
    return B.curva(B.hoja(x, y, ang, largo, ancho), 3, True)


def _abanico(X, x, y, angs, largos, ancho, tono, nervio=2):
    """Plumas en abanico: relieve del tono dado y nervios hundidos."""
    for a, l in zip(angs, largos):
        X.pol(_pluma(X, x, y, a, l, ancho))
    X.alto(tono)
    for a, l in zip(angs, largos):
        X.lin([(x + math.cos(a) * l * .15, y + math.sin(a) * l * .15), (x + math.cos(a) * l * .92, y + math.sin(a) * l * .92)], nervio)
    X.hondo(2)


def _pelaje(cx, cy, rx, ry, n, pico, ang=0.0, a0=0.0, a1=2 * PI):
    pts = []
    m = 2 * n
    for j in range(m):
        a = a0 + (a1 - a0) * j / m
        f = 1 + (pico if j % 2 else 0)
        x, y = rx * f * math.cos(a), ry * f * math.sin(a)
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    return pts


# ------------------------------------------------------------------ 0 Unicornio
def _m_unicornio(L):
    X = _X(L, .83, -.04, -.03)
    # cielo: estrellas y destellos
    for x, y, r in ((-.70, -.52, .11), (-.84, -.14, .07), (-.46, -.84, .07), (.24, -.88, .06), (.82, -.20, .07)):
        L.pol(_estr(x, y, r, .25))
    L.alto(0)
    for x, y in ((-.58, -.74), (-.82, -.34), (.06, -.78)):
        L.circ(x, y, .018)
    L.alto(1)
    # patas lejanas
    X.lin([(.28, .22), (.46, .42), (.40, .54)], 12)
    X.lin([(-.20, .28), (-.18, .56), (-.12, .70)], 10)
    X.alto(2)
    X.pol([(.34, .52), (.46, .52), (.48, .61), (.33, .61)])
    X.pol([(-.19, .68), (-.05, .68), (-.03, .77), (-.20, .77)])
    X.alto(2)
    # cola
    ct = [(-.52, -.08), (-.70, -.10), (-.88, .05), (-.94, .28), (-.86, .52), (-.94, .74)]
    cb = [(-.52, .10), (-.66, .14), (-.74, .28), (-.72, .48), (-.76, .64), (-.86, .78)]
    X.pol(B.curva(ct + cb[::-1], 3, True))
    X.alto(0)
    for s_ in (.33, .66):
        X.lin(B.curva([_lerp(ct[i], cb[i], s_) for i in range(6)], 4), 2)
    X.hondo(2)
    for x, y in ((-.84, .20), (-.80, .48)):
        X.pol(_estr(x, y, .06, .3))
    X.alto(1)
    # cuerpo
    cuerpo = [(.82, -.34), (.80, -.27), (.70, -.26), (.60, -.33), (.50, -.32), (.44, -.18), (.38, 0), (.32, .14), (.24, .28),
              (-.10, .30), (-.38, .28), (-.50, .16), (-.54, 0), (-.46, -.12), (-.30, -.14), (-.05, -.12), (.14, -.30),
              (.28, -.50), (.34, -.66), (.44, -.68), (.56, -.64), (.68, -.52), (.78, -.42)]
    X.pol(B.curva(cuerpo, 5, True))
    X.alto(0)
    # patas cercanas
    X.lin([(.26, .22), (.30, .46), (.30, .70)], 13)
    X.lin([(-.40, .15), (-.46, .44), (-.52, .70)], 14)
    X.alto(0)
    X.pol([(.22, .66), (.38, .66), (.40, .77), (.21, .77)])
    X.pol([(-.60, .66), (-.45, .66), (-.43, .77), (-.62, .77)])
    X.alto(2)
    # melena
    e1 = [(.34, -.68), (.28, -.50), (.14, -.30), (-.05, -.12)]
    e2 = [(.20, -.84), (.04, -.62), (-.12, -.40), (-.30, -.16)]
    X.pol(B.curva(e1 + e2[::-1], 5, True))
    X.alto(1)
    for s_ in (.35, .7):
        X.lin(B.curva([_lerp(e1[i], e2[i], s_) for i in range(4)], 5), 2)
    X.hondo(2)
    for x, y in ((.12, -.58), (-.06, -.36)):
        X.pol(_estr(x, y, .07, .3))
    X.alto(0)
    # cuerno espiral
    base = (.58, -.66)
    ang = -1.10
    L_ = .38
    X.pol(B.rotar([(0, -.07), (L_, 0), (0, .07)], ang, *base))
    X.alto(0)
    for j in range(1, 7):
        t = j / 7.5
        w = .07 * (1 - t)
        X.lin(B.rotar([(t * L_, -w), (t * L_ + .05, w)], ang, *base), 2)
    X.hondo(2)
    # oreja
    X.pol([(.40, -.66), (.38, -.84), (.50, -.70)])
    X.alto(0)
    X.pol([(.41, -.69), (.40, -.79), (.46, -.71)])
    X.hondo(2)
    # ojo, nariz, boca
    X.elip(.56, -.53, .055, .04)
    X.alto(0)
    X.circ(.57, -.53, .03)
    X.hondo(2)
    X.lin([(.50, -.58), (.56, -.60), (.62, -.57)], 2)
    X.hondo(2)
    X.circ(.77, -.34, .012)
    X.lin([(.76, -.28), (.70, -.28)], 2)
    X.hondo(2)
    X.circ(.58, -.40, .03, 2)
    X.alto(1)
    # adornos del cuerpo
    X.lin(_espiral(.12, .10, .02, .12, 2, 0, 30), 2)
    X.lin(_espiral(-.34, .08, .02, .15, 2, 2, 30), 2)
    X.hondo(2)
    for x, y in ((-.10, .16), (-.0, -.04), (-.18, -.04), (.20, .22), (-.20, .24)):
        X.pol(_estr(x, y, .05, .3))
    X.alto(0)
    for j in range(9):
        X.circ(-.38 + j * .09, .28 - .015 * math.sin(j), .014)
    X.hondo(2)
    X.lin(B.curva([(.36, 0), (.31, .06), (.35, .12), (.29, .18)], 3), 2)
    X.lin(B.curva([(.44, -.10), (.40, -.04)], 3), 2)
    X.hondo(2)
    # greca del suelo
    _guarda(L, -.46, .46, .82, 7, .09)


# ------------------------------------------------------------------ 1 Sirena
def _m_sirena(L):
    X = _X(L, 1.0, 0, -.01)
    # olas de fondo
    for y in (.74, .82, .89):
        h = math.sqrt(max(.01, .93 ** 2 - y * y))
        X.lin(B.ondas(-h, y, h, y, .022, 6, 40), 3)
    X.alto(1)
    # cabello trasero
    hl = [(-.14, -.80), (-.30, -.74), (-.44, -.52), (-.40, -.26), (-.54, -.04), (-.46, .16), (-.36, .06), (-.30, -.10), (-.22, -.30), (-.14, -.46)]
    hr = [(.14, -.80), (.30, -.74), (.44, -.56), (.46, -.30), (.58, -.08), (.52, .14), (.42, .02), (.36, -.14), (.24, -.32), (.14, -.46)]
    X.pol(B.curva(hl, 4, True))
    X.pol(B.curva(hr, 4, True))
    X.alto(2)
    for pts in ([(-.2, -.74), (-.34, -.5), (-.32, -.25), (-.42, -.05)], [(-.26, -.7), (-.4, -.45), (-.4, -.2), (-.46, .08)],
                [(.2, -.74), (.34, -.52), (.36, -.28), (.46, -.06)], [(.27, -.7), (.4, -.48), (.44, -.25), (.52, .06)]):
        X.lin(B.curva(pts, 4), 2)
    X.hondo(1)
    # cola
    ctr = B.curva([(0, -.03), (-.05, .15), (-.13, .32), (-.04, .47), (.18, .56), (.38, .52), (.50, .40)], 6)
    poli, info = _cinta(ctr, lambda t: .13 - .09 * t)
    X.pol(poli)
    X.alto(1)
    # escamas
    for i in range(3, len(info) - 1, 3):
        (px, py), (tx, ty), (nx, ny) = info[i]
        t = i / (len(info) - 1)
        w = .13 - .09 * t
        ang = math.atan2(ty, tx)
        m = 3 if w > .09 else 2
        for q in range(m):
            off = (q - (m - 1) / 2) * 2 * w / (m + .3)
            cx, cy = px + nx * off, py + ny * off
            X.lin(B.arco(cx, cy, w / (m + .3) * 1.1, w / (m + .3) * 1.1, ang - 1.1, ang + 1.1, 6), 2)
    X.hondo(2)
    # aleta
    (ex, ey), (tx, ty), _n = info[-1]
    ang = math.atan2(ty, tx)
    fin = [(0, 0), (.12, -.18), (.30, -.34), (.26, -.13), (.38, 0), (.26, .13), (.30, .34), (.12, .18)]
    X.pol(B.curva(B.rotar(fin, ang, ex, ey), 4, True))
    X.alto(0)
    for da in (-.7, -.35, 0, .35, .7):
        X.lin(B.rotar([(.06, 0), (.30 * math.cos(da * .5), .30 * math.sin(da * .5) * 1.4)], ang, ex, ey), 2)
    X.hondo(2)
    # torso
    tor = [(-.09, -.48), (.09, -.48), (.15, -.40), (.17, -.22), (.12, -.08), (.10, .0), (-.10, .0), (-.12, -.08), (-.17, -.22), (-.15, -.40)]
    X.pol(B.curva(tor, 4, True))
    X.alto(0)
    # brazos
    X.lin([(-.15, -.38), (-.30, -.24), (-.26, -.06)], 9)
    X.lin([(.15, -.38), (.34, -.46), (.40, -.62)], 9)
    X.alto(0)
    X.circ(-.26, -.04, .045)
    X.circ(.40, -.64, .045)
    X.alto(0)
    # varita estrella
    X.lin([(.40, -.64), (.46, -.78)], 3)
    X.alto(1)
    X.pol(_estr(.47, -.86, .10, .38))
    X.alto(0)
    # conchas del pecho
    for sg in (-1, 1):
        X.circ(sg * .065, -.30, .07)
        X.alto(1)
        for j in range(5):
            a = -PI / 2 + (j - 2) * .5
            X.lin([(sg * .065, -.26), (sg * .065 + .06 * math.cos(a), -.26 + .06 * math.sin(a))], 1.5)
        X.hondo(2)
    X.lin(B.curva([(-.1, -.14), (0, -.11), (.1, -.14)], 4), 2)
    for j in range(5):
        X.circ(-.08 + j * .04, -.12 + .014 * math.sin(j * 1.5), .012)
    X.hondo(2)
    # cabeza
    X.circ(0, -.62, .15)
    X.alto(0)
    X.pol(B.curva([(-.16, -.64), (-.12, -.74), (0, -.78), (.12, -.74), (.16, -.64), (.08, -.70), (-.02, -.70), (-.10, -.64)], 3, True))
    X.alto(2)
    # cara
    for sg in (-1, 1):
        X.elip(sg * .06, -.62, .028, .032)
        X.hondo(2)
        X.lin([(sg * .035, -.665), (sg * .06, -.68), (sg * .09, -.665)], 1.5)
        X.hondo(2)
        X.circ(sg * .09, -.55, .02)
        X.hondo(1, .6)
    X.lin(B.arco(0, -.57, .045, .03, .3, PI - .3, 6), 2)
    X.hondo(2)
    # corona de estrellitas
    X.pol(_estr(0, -.84, .07, .35))
    X.pol(_estr(-.12, -.81, .045, .35))
    X.pol(_estr(.12, -.81, .045, .35))
    X.alto(0)
    # estrella de mar, concha, burbujas
    X.pol(_estr(-.64, .30, .15, .45, 5))
    X.alto(1)
    for j in range(5):
        a = -PI / 2 + j * 2 * PI / 5
        X.lin([(-.64, .30), (-.64 + .12 * math.cos(a), .30 + .12 * math.sin(a))], 2)
    X.hondo(2)
    for j in range(5):
        a = -PI / 2 + j * 2 * PI / 5
        X.circ(-.64 + .075 * math.cos(a), .30 + .075 * math.sin(a), .012)
    X.alto(0)
    cx0, cy0 = -.58, .68
    X.pol([(cx0, cy0)] + B.arco(cx0, cy0, .17, .17, -PI + .2, -.2, 10))
    X.alto(0)
    for j in range(6):
        a = -PI + .2 + j * (PI - .4) / 5
        X.lin([(cx0, cy0), (cx0 + .16 * math.cos(a), cy0 + .16 * math.sin(a))], 1.5)
    X.hondo(2)
    for x, y, r in ((.72, -.36, .06), (.62, -.54, .04), (.80, -.18, .035), (-.70, -.46, .05), (-.60, -.62, .035), (.58, .08, .04)):
        X.circ(x, y, r, 2)
    X.alto(0)
    for x, y in ((.70, -.36), (-.71, -.47)):
        X.circ(x - .02, y - .02, .01)
    X.alto(0)
    for x, y, r in ((.78, .50, .06), (.28, -.9, .05), (-.78, -.1, .05)):
        X.pol(_estr(x, y, r, .3))
    X.alto(0)



# ------------------------------------------------------------------ 2 Grifo
def _garra(X, x, y, ang, r=.07, w=2):
    """Tres garras curvas que salen de (x, y) hacia el angulo ang."""
    for da in (-.5, 0, .5):
        a = ang + da
        X.lin(B.curva([(x, y), (x + r * .6 * math.cos(a), y + r * .6 * math.sin(a)),
                       (x + r * math.cos(a + .5), y + r * math.sin(a + .5))], 3), w)


def _m_grifo(L):
    X = _X(L, .96, -.10, .06, -1)    # mira a la izquierda
    # estrellas del cielo
    for x, y, r in ((.62, -.62, .09), (.82, -.28, .06), (-.30, -.88, .06), (.30, -.84, .05)):
        L.pol(_estr(x, y, r, .25))
    L.alto(0)
    # ala (detras): plumas largas y cobertoras
    bx, by = -.06, -.10
    angs = [math.radians(a) for a in range(-176, -92, 10)]
    largos = [.62 + .22 * math.sin((i + .5) / len(angs) * PI * .9) for i in range(len(angs))]
    _abanico(X, bx, by, angs, largos, .075, 2)
    angs2 = [math.radians(a) for a in range(-172, -90, 14)]
    _abanico(X, bx, by, angs2, [.40] * len(angs2), .075, 1)
    angs3 = [math.radians(a) for a in range(-168, -90, 16)]
    _abanico(X, bx, by, angs3, [.24] * len(angs3), .06, 0, 1.5)
    # cola de leon
    X.lin(B.curva([(-.52, .08), (-.72, .20), (-.86, .12), (-.84, -.04)], 5), 7)
    X.alto(1)
    X.pol(B.curva([(-.84, -.02), (-.94, -.06), (-.96, -.16), (-.88, -.26), (-.80, -.18), (-.76, -.08)], 3, True))
    X.alto(0)
    X.lin([(-.86, -.04), (-.88, -.18)], 2)
    X.lin([(-.82, -.04), (-.80, -.16)], 2)
    X.hondo(2)
    # patas traseras lejana
    X.lin([(-.16, .22), (-.10, .42), (-.20, .56)], 14)
    X.alto(2)
    X.elip(-.16, .60, .10, .05)
    X.alto(2)
    # cuerpo de leon
    cuerpo = [(-.55, -.02), (-.40, -.16), (-.10, -.17), (.16, -.14), (.32, -.04), (.36, .14), (.28, .34), (.0, .38), (-.32, .36), (-.54, .26), (-.62, .10)]
    X.pol(B.curva(cuerpo, 5, True))
    X.alto(1)
    # pelaje del lomo y vientre
    for i in range(7):
        x = -.44 + i * .1
        X.lin([(x, .30), (x + .03, .37), (x + .06, .30)], 2)
    X.alto(1)
    for j in range(4):
        for i in range(5):
            x = -.40 + i * .13 + (j % 2) * .06
            y = -.04 + j * .08
            X.lin([(x - .035, y), (x, y + .04), (x + .035, y)], 1.5)
    X.hondo(2)
    # anca
    X.circ(-.36, .14, .17, 2)
    X.hondo(2)
    X.lin(_espiral(-.36, .14, .02, .10, 2, 0, 24), 2)
    X.hondo(2)
    # pata trasera cercana
    X.lin([(-.40, .16), (-.30, .38), (-.42, .52)], 17)
    X.alto(0)
    X.elip(-.38, .59, .115, .055)
    X.alto(0)
    for x in (-.45, -.38, -.31):
        X.lin([(x, .55), (x - .01, .63)], 1.5)
    X.hondo(2)
    # cuello con plumas, pecho
    X.lin([(.16, -.02), (.34, -.20), (.44, -.38)], 31)
    X.alto(0)
    for j in range(4):
        for i in range(3):
            x = .20 + j * .07 + i * .02
            y = -.02 - j * .09 + i * .07
            X.lin(B.arco(x, y, .05, .05, 0.3, PI - .3, 5), 1.5)
    X.hondo(2)
    # patas delanteras de aguila
    X.lin([(.24, .08), (.46, .12), (.54, .26)], 14)
    X.alto(0)
    X.lin([(.52, .24), (.56, .30)], 2)
    X.hondo(2)
    _garra(X, .54, .28, .9, .1, 3)
    X.alto(2)
    X.lin([(.20, .20), (.22, .44), (.26, .60)], 15)
    X.alto(0)
    for dy in (.46, .52):
        X.lin(B.arco(.23, dy, .07, .035, .2, PI - .2, 5), 1.5)
    X.hondo(2)
    _garra(X, .27, .62, .4, .1, 3)
    X.alto(2)
    # cabeza de aguila
    X.circ(.46, -.46, .14)
    X.alto(0)
    X.pol(B.curva([(.54, -.56), (.70, -.52), (.76, -.40), (.68, -.38), (.62, -.46), (.54, -.42)], 3, True))
    X.alto(2)
    X.lin([(.56, -.48), (.70, -.46)], 1.5)
    X.hondo(1)
    for a, l in ((-2.6, .19), (-2.25, .20), (-2.95, .16)):
        X.pol(_pluma(X, .38, -.54, a, l, .045))
    X.alto(1)
    _ojo(X, .50, -.51, .05, .8)
    X.lin([(.43, -.58), (.50, -.59), (.57, -.56)], 2.5)
    X.hondo(2)
    X.circ(.34, -.42, .018)
    X.hondo(2)
    # suelo
    _guarda(L, -.5, .5, .88, 7, .09)


# ------------------------------------------------------------------ 3 Yeti
def _m_yeti(L):
    X = _X(L, .94, 0, -.03)
    # montanas con nieve detras
    for px, py, x0, x1 in ((-.50, -.58, -.86, -.04), (.46, -.46, -.02, .90)):
        X.pol([(x0, .46), (px, py), (x1, .46)])
    X.alto(2)
    for px, py, x0, x1 in ((-.50, -.58, -.86, -.04), (.46, -.46, -.02, .90)):
        h = .46 - py
        a = [(px - .0, py), (px - .14, py + .22), (px - .07, py + .18), (px - .03, py + .26), (px + .03, py + .19), (px + .09, py + .27), (px + .15, py + .22)]
        X.pol(a)
    X.alto(0)
    X.lin([(-.5, -.58), (-.40, -.2), (-.46, .1), (-.38, .4)], 2)
    X.lin([(.46, -.46), (.56, -.1), (.50, .2), (.60, .42)], 2)
    X.hondo(2)
    # copos y destellos
    for x, y, r in ((0, -.80, .08), (-.80, -.10, .07), (.80, -.12, .08), (.28, -.66, .06), (-.26, -.76, .05)):
        _copo(L, x, y, r, 0) if False else _copo(_X(L), x, y, r, 0)
    for x, y, r in ((.62, -.74, .05), (-.80, -.42, .05)):
        L.pol(_estr(x, y, r, .25))
    L.alto(0)
    # pies
    for sg in (-1, 1):
        X.pol(_pelaje(sg * .22, .70, .19, .09, 7, .08))
    X.alto(1)
    for sg in (-1, 1):
        for j in range(3):
            X.circ(sg * (.22 + (j - 1) * .08), .74, .035)
    X.alto(0)
    # cuerpo
    X.pol(_pelaje(0, .24, .46, .42, 14, .07))
    X.alto(1)
    X.elip(0, .30, .24, .30)
    X.alto(0, .7)
    # mechones de pelaje
    for j in range(5):
        for i in range(-3, 4):
            x = i * .10 + (j % 2) * .05
            y = .02 + j * .12
            if (x / .44) ** 2 + ((y - .24) / .40) ** 2 < .72 and not ((x / .24) ** 2 + ((y - .3) / .3) ** 2 < .8):
                X.lin([(x - .04, y), (x, y + .06), (x + .04, y)], 2)
    X.hondo(2)
    for j in range(4):
        for i in range(-2, 3):
            x = i * .09 + (j % 2) * .045
            y = .08 + j * .13
            if (x / .22) ** 2 + ((y - .3) / .27) ** 2 < .8:
                X.lin([(x - .03, y), (x, y + .05), (x + .03, y)], 1.5)
    X.hondo(1)
    # brazos
    for sg in (-1, 1):
        X.pol(_pelaje(sg * .53, .24, .11, .31, 10, .08, sg * -.2))
    X.alto(1)
    for sg in (-1, 1):
        for j in range(4):
            X.lin([(sg * (.47 + j * .02), .10 + j * .1), (sg * (.52 + j * .02), .15 + j * .1), (sg * (.57 + j * .02), .10 + j * .1)], 2)
    X.hondo(2)
    for sg in (-1, 1):
        X.circ(sg * .58, .56, .10)
    X.alto(0)
    for sg in (-1, 1):
        for j in range(3):
            X.circ(sg * (.58 + (j - 1) * .07), .64, .035)
    X.alto(0)
    # cabeza
    X.pol(_pelaje(0, -.30, .31, .27, 10, .09))
    X.alto(1)
    for sg in (-1, 1):
        X.circ(sg * .33, -.28, .07)
    X.alto(1)
    # cara
    X.pol(B.curva([(-.19, -.40), (-.10, -.46), (0, -.42), (.10, -.46), (.19, -.40), (.21, -.26), (.14, -.12), (0, -.08), (-.14, -.12), (-.21, -.26)], 3, True))
    X.alto(0)
    X.lin([(-.18, -.43), (-.10, -.46), (0, -.42), (.10, -.46), (.18, -.43)], 2)
    for sg in (-1, 1):
        _ojo(X, sg * .085, -.31, .05, 0)
        X.lin([(sg * .04, -.385), (sg * .085, -.40), (sg * .13, -.38)], 2.5)
        X.hondo(2)
    X.elip(0, -.22, .04, .028)
    X.hondo(2)
    X.lin(B.arco(0, -.19, .09, .06, .35, PI - .35, 8), 2.5)
    X.hondo(2)
    for sg in (-1, 1):
        X.pol([(sg * .035 - .018, -.135), (sg * .035 + .018, -.135), (sg * .035, -.105)])
    X.alto(0)
    for sg in (-1, 1):
        X.circ(sg * .16, -.20, .025)
    X.hondo(1, .6)
    # guarda de nieve
    _guarda(L, -.5, .5, .90, 8, .08)


# ------------------------------------------------------------------ 4 Fenix
def _llama(r0, r1, a, w, lean=.14):
    """Lengua de fuego que sale del radio r0 y acaba en punta en r1 inclinada hacia un lado."""
    d = r1 - r0
    izq = [(r0, -w), (r0 + .25 * d, -w * 1.15), (r0 + .55 * d, -w * .8), (r0 + .8 * d, -w * .1), (r1, lean)]
    der = [(r1, lean), (r0 + .85 * d, lean * .5 + .0), (r0 + .6 * d, w * .55), (r0 + .35 * d, w * 1.0), (r0, w)]
    return B.rotar(B.curva(izq, 4)[:-1] + B.curva(der, 4), a)


def _m_fenix(L):
    X = _X(L, .93, 0, 0)
    n = 12
    # anillo exterior de llamas (tres capas)
    for j in range(n):
        a = j * 2 * PI / n
        X.pol(_llama(.50, .97, a, .13, .17))
    X.alto(2)
    for j in range(n):
        a = j * 2 * PI / n + PI / n
        X.pol(_llama(.50, .84, a, .10, .13))
    X.alto(1)
    for j in range(n):
        a = j * 2 * PI / n
        X.pol(_llama(.52, .86, a + .01, .075, .1))
    X.alto(0)
    for j in range(n):
        a = j * 2 * PI / n
        X.lin(B.rotar(B.curva([(.60, -.01), (.70, .0), (.80, .04)], 3), a), 1.5)
        X.lin(B.rotar(B.curva([(.60, -.06), (.68, -.06), (.76, -.03)], 3), a + PI / n), 1.5)
    X.hondo(2)
    X.circ(0, 0, .52, 3)
    X.hondo(2)
    X.circ(0, 0, .48)
    X.alto(2, .5)
    for j in range(24):
        X.circ(.43 * math.cos(j * PI / 12), .43 * math.sin(j * PI / 12), .014)
    X.hondo(2)
    # cola de plumas largas
    angs = [PI / 2 + d for d in (-.62, -.32, 0, .32, .62)]
    largos = [.50, .56, .60, .56, .50]
    _abanico(X, 0, .24, angs, largos, .075, 1)
    for a, l in zip(angs, largos):
        X.circ(math.cos(a) * l * .9, .24 + math.sin(a) * l * .9, .035)
    X.alto(0)
    for a, l in zip(angs, largos):
        X.circ(math.cos(a) * l * .9, .24 + math.sin(a) * l * .9, .015)
    X.hondo(2)
    # alas hacia arriba
    for sg in (-1, 1):
        ang = [(-PI / 2 + sg * d) for d in (.30, .48, .66, .84, 1.02, 1.20, 1.38, 1.56)]
        lar = [.64, .72, .74, .72, .66, .60, .52, .44]
        for a, l in zip(ang, lar):
            X.pol(_pluma(X, sg * .12, -.12, a, l, .075))
        X.alto(1)
        for a, l in zip(ang, lar):
            X.lin([(sg * .12 + math.cos(a) * l * .12, -.12 + math.sin(a) * l * .12), (sg * .12 + math.cos(a) * l * .9, -.12 + math.sin(a) * l * .9)], 2)
        X.hondo(2)
        ang2 = [(-PI / 2 + sg * d) for d in (.40, .64, .88, 1.12, 1.36, 1.6)]
        for a in ang2:
            X.pol(_pluma(X, sg * .12, -.12, a, .30, .07))
        X.alto(0)
        for a in ang2:
            X.lin([(sg * .12 + math.cos(a) * .06, -.12 + math.sin(a) * .06), (sg * .12 + math.cos(a) * .26, -.12 + math.sin(a) * .26)], 1.5)
        X.hondo(2)
    # cuerpo
    mit = [(0, -.28), (.10, -.24), (.16, -.10), (.16, .08), (.11, .24), (.04, .34)]
    X.pol(B.curva(B.simetrico(mit), 4, True))
    X.alto(0)
    for j in range(5):
        for i in (-1, 0, 1):
            x = i * .075 + (j % 2) * .0
            y = -.16 + j * .09
            if abs(x) < .12 - abs(y - .06) * .1:
                X.lin(B.arco(x, y, .04, .04, .3, PI - .3, 5), 2)
    X.hondo(2)
    # cresta y cabeza
    for a, l in ((-PI / 2, .28), (-PI / 2 - .5, .24), (-PI / 2 + .5, .24), (-PI / 2 - .95, .17), (-PI / 2 + .95, .17)):
        X.pol(_pluma(X, 0, -.40, a, l, .045))
    X.alto(1)
    X.circ(0, -.36, .125)
    X.alto(0)
    X.pol([(-.045, -.32), (.045, -.32), (0, -.22)])
    X.alto(2)
    for sg in (-1, 1):
        _ojo(X, sg * .055, -.39, .036, 0)
    X.lin([(-.10, -.435), (-.05, -.45), (-.01, -.43)], 2)
    X.lin([(.10, -.435), (.05, -.45), (.01, -.43)], 2)
    X.hondo(2)
    # chispas
    for x, y, r in ((-.70, -.72, .06), (.72, -.74, .06), (0, -.92, .05), (-.88, .1, .045), (.88, .12, .045)):
        L.pol(_estr(x, y, r, .25))
    L.alto(0)


# ------------------------------------------------------------------ 5 Quetzalcoatl
def _m_quetzal(L):
    X = _X(L, 1.0, 0, 0.0)
    # anillo exterior de piramides escalonadas
    n = 22
    for j in range(n):
        a = j * 2 * PI / n
        X.pol(_pir(.15, .12, a + PI / 2, .80 * math.cos(a), .80 * math.sin(a)))
    X.alto(2)
    for j in range(n):
        a = j * 2 * PI / n
        X.pol(_pir(.07, .06, a + PI / 2, .82 * math.cos(a), .82 * math.sin(a)))
    X.hondo(1)
    X.circ(0, 0, .78, 2)
    X.hondo(2)
    # cuerpo en espiral: de la cola (centro) a la cabeza (arriba)
    N = 150
    ctr = []
    th0 = -PI / 2 - 4 * PI
    for i in range(N + 1):
        t = i / N
        th = th0 + 4 * PI * t
        r = .10 + .52 * t ** .9
        ctr.append((r * math.cos(th), r * math.sin(th)))
    poli, info = _cinta(ctr, lambda t: .04 + .075 * t)
    X.pol(poli)
    X.alto(1)
    # bandas: escamas y plumas alternadas
    for i in range(2, N - 4, 6):
        (px, py), (tx, ty), (nx, ny) = info[i]
        t = i / N
        w = .04 + .075 * t
        ang = math.atan2(ty, tx)
        if (i // 6) % 2 == 0:
            m = 3 if w > .06 else 2
            for q in range(m):
                off = (q - (m - 1) / 2) * 2 * w / m
                rr = w / m * 1.05
                X.lin(B.arco(px + nx * off, py + ny * off, rr, rr, ang - 1.2, ang + 1.2, 6), 2)
            X.hondo(2)
        else:
            for q in (-1, 1):
                X.pol(B.curva(B.hoja(px, py, ang + q * 2.4 + PI * 0, w * 1.6, w * .45), 2, True))
            X.alto(0)
    # vientre claro
    ctr2 = ctr[6:N - 6]
    X.lin(ctr2, 2)
    X.hondo(2)
    # rosetón de la cola
    X.circ(0, 0, .09)
    X.alto(0)
    X.circ(0, 0, .05, 2)
    X.circ(0, 0, .018)
    X.hondo(2)
    # cabeza (al final de la espiral, arriba, mirando a la derecha)
    (hx, hy), (tx, ty), (nx, ny) = info[-1]
    ang = math.atan2(ty, tx)
    cab = [(-.08, -.11), (.06, -.13), (.20, -.09), (.30, -.04), (.30, .03), (.20, .06), (.10, .10), (-.04, .12), (-.10, .0)]
    # plumas de la cresta (quetzal)
    for pl, wd in (([(.0, -.07), (-.10, -.17), (-.26, -.22), (-.44, -.16)], .06),
                   ([(.03, -.07), (-.04, -.20), (-.16, -.30), (-.32, -.30)], .055),
                   ([(.06, -.06), (.08, -.20), (.02, -.30), (-.10, -.36)], .05)):
        pts = B.rotar(B.curva(pl, 6), ang, hx, hy)
        pol, _i = _cinta(pts, lambda t, wd=wd: wd * math.sin(PI * min(1, t * 1.15 + .12)) + .006)
        X.pol(pol)
        X.alto(0)
        X.lin(pts[2:-3], 2)
        X.hondo(2)
        X.circ(pts[-1][0], pts[-1][1], .022)
        X.alto(1)
    X.pol(B.curva(B.rotar(B.escalar(cab, 1.25), ang, hx, hy), 3, True))
    X.alto(0)
    # hocico y detalles
    X.lin(B.rotar([(.12, .03), (.28, .01)], ang, hx, hy), 2)
    X.hondo(2)
    X.lin(B.rotar(B.arco(.24, .01, .07, .05, .2, 1.4, 5), ang, hx, hy), 2)
    X.hondo(2)
    ex, ey = B.rotar([(.10, -.045)], ang, hx, hy)[0]
    _ojo(X, ex, ey, .056, 0)
    X.lin(B.rotar([(.04, -.09), (.12, -.10), (.18, -.07)], ang, hx, hy), 2.5)
    X.hondo(2)
    for j in range(4):
        X.circ(*B.rotar([(-.02 + j * .035, .0)], ang, hx, hy)[0], .012)
    X.hondo(2)
    # destellos
    for x, y, r in ((-.78, -.3, .05), (.78, -.34, .05), (.0, .93, .045)):
        L.pol(_estr(x, y, r, .25))
    L.alto(0)


MOTIVOS = [_m_unicornio, _m_sirena, _m_grifo, _m_yeti, _m_fenix, _m_quetzal]
