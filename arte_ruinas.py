"""Arte procedural de las Ruinas Antiguas (agente ARTE): murales de arenisca tallada, fondo, columnas de glifos,
marco, rejilla, iconos y piezas. Solo dibujo; sin logica y sin archivos externos. Todo lo costoso se cachea."""
import math
import random
import pygame

try:
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None

import arte_mitos

N_MUNDOS = 5
POR_MUNDO = 6
N_RUINAS = N_MUNDOS * POR_MUNDO          # 30 murales: mundo = i // 6, fase = i % 6
NOMBRES = list(arte_mitos.NOMBRES)       # nombre de la criatura de cada mural
_VARIANTE = [1, 5, 0, 4, 2]              # ambiente (colores, glifos) de cada mundo: de las 6 variantes originales


def _var(i):
    """Variante de ambiente (0..5) de la ruina i."""
    return _VARIANTE[(i // POR_MUNDO) % N_MUNDOS]

# ---------------------------------------------------------------- colores
_TONOS = [  # (cuerpo, luz, sombra): claro, medio, oscuro
    ((228, 188, 108), (255, 238, 176), (122, 80, 32)),
    ((206, 160, 84), (242, 210, 138), (104, 66, 26)),
    ((172, 126, 60), (216, 174, 100), (80, 48, 20)),
]
_TINTE = [(1.0, 1.0, 1.0), (0.95, 1.0, 0.98), (1.02, 0.94, 0.94), (0.97, 1.02, 0.92), (1.03, 0.92, 0.86), (0.94, 0.96, 1.06)]
_FONDOS = [(46, 28, 16), (14, 36, 46), (38, 26, 50), (18, 40, 26), (50, 22, 22), (22, 24, 56)]


def _mez(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def _tin(c, i):
    f = _TINTE[i % 6]
    return (min(255, int(c[0] * f[0])), min(255, int(c[1] * f[1])), min(255, int(c[2] * f[2])))


def _pal(i):
    return [tuple(_tin(c, i) for c in t) for t in _TONOS]


# ---------------------------------------------------------------- lienzo de relieve
class _L:
    """Acumula formas (coordenadas en unidades U alrededor de cx,cy) y las talla con luces y sombras."""

    def __init__(s, surf, cx, cy, U, pal, k=None):
        s.s, s.cx, s.cy, s.U, s.pal = surf, cx, cy, U, pal
        s.k = k if k else max(0.3, U / 180.0)
        s.ops = []

    def X(s, x):
        return s.cx + x * s.U

    def Y(s, y):
        return s.cy + y * s.U

    def circ(s, x, y, r, w=0):
        s.ops.append(("c", x, y, r, w))

    def elip(s, x, y, rx, ry, w=0):
        s.ops.append(("e", x, y, rx, ry, w))

    def pol(s, pts, w=0):
        s.ops.append(("p", list(pts), w))

    def lin(s, pts, w=2):
        s.ops.append(("l", list(pts), w))

    def rect(s, x, y, hw, hh, w=0):
        s.ops.append(("r", x, y, hw, hh, w))

    def _wp(s, w):
        return 0 if w == 0 else max(1, int(round(w * s.k)))

    def _draw(s, col, dx, dy):
        sf, U = s.s, s.U
        for op in s.ops:
            t = op[0]
            if t == "c":
                _, x, y, r, w = op
                pygame.draw.circle(sf, col, (round(s.X(x) + dx), round(s.Y(y) + dy)), max(1, round(r * U)), s._wp(w))
            elif t == "e":
                _, x, y, rx, ry, w = op
                rc = pygame.Rect(round(s.X(x - rx) + dx), round(s.Y(y - ry) + dy), max(2, round(2 * rx * U)), max(2, round(2 * ry * U)))
                pygame.draw.ellipse(sf, col, rc, s._wp(w))
            elif t == "p":
                pts = [(s.X(a) + dx, s.Y(b) + dy) for a, b in op[1]]
                if len(pts) >= 3:
                    pygame.draw.polygon(sf, col, pts, s._wp(op[2]))
            elif t == "l":
                pts = [(s.X(a) + dx, s.Y(b) + dy) for a, b in op[1]]
                wp = s._wp(op[2])
                if len(pts) >= 2:
                    pygame.draw.lines(sf, col, False, pts, wp)
                    if wp >= 3:
                        for q in pts:
                            pygame.draw.circle(sf, col, (round(q[0]), round(q[1])), wp // 2)
            elif t == "r":
                _, x, y, hw, hh, w = op
                rc = pygame.Rect(round(s.X(x - hw) + dx), round(s.Y(y - hh) + dy), max(2, round(2 * hw * U)), max(2, round(2 * hh * U)))
                pygame.draw.rect(sf, col, rc, s._wp(w))

    def alto(s, tono=1, f=1.0):
        c, l, sh = s.pal[tono]
        d = max(1, round(s.k * 1.5))
        e = max(1, round(s.k * 0.8))
        if f < 1.0:
            base = s.pal[1][0]
            c, l, sh = _mez(base, c, f), _mez(base, l, f), _mez(base, sh, f)
        s._draw(sh, d, d)
        s._draw(l, -e, -e)
        s._draw(c, 0, 0)
        s.ops = []

    def hondo(s, tono=1, f=1.0):
        c, l, sh = s.pal[tono]
        e = max(1, round(s.k * 0.8))
        hu = _mez(c, sh, 0.55 * f)
        sh2 = _mez(c, sh, f)
        l2 = _mez(c, l, f)
        s._draw(l2, e, e)
        s._draw(sh2, -e, -e)
        s._draw(hu, 0, 0)
        s.ops = []


def _arco(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * j / n), cy + ry * math.sin(a0 + (a1 - a0) * j / n)) for j in range(n + 1)]


def _rotar(pts, ang, ox=0.0, oy=0.0):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(ox + x * ca - y * sa, oy + x * sa + y * ca) for x, y in pts]


def _hoja_pts(x, y, ang, largo, ancho):
    base = [(0, 0), (largo * .25, -ancho * .8), (largo * .6, -ancho), (largo, 0), (largo * .6, ancho), (largo * .25, ancho * .8)]
    return _rotar(base, ang, x, y)


# ---------------------------------------------------------------- glifos propios (16 clases)
def _glifo(L, kind, x, y, r):
    wg = max(1.0, r * L.U * 0.17) / L.k

    def g(a, b):
        return (x + a * r, y + b * r)

    kind %= 16
    if kind == 0:  # espiral
        n = 40
        L.lin([g((.12 + .88 * j / n) * math.cos(j / n * 4.4 * math.pi), (.12 + .88 * j / n) * math.sin(j / n * 4.4 * math.pi)) for j in range(n + 1)], wg)
    elif kind == 1:  # ojo
        top = [g(-1 + 2 * j / 10, -.6 * (1 - (-1 + 2 * j / 10) ** 2)) for j in range(11)]
        bot = [g(1 - 2 * j / 10, .6 * (1 - (1 - 2 * j / 10) ** 2)) for j in range(11)]
        L.pol(top + bot, wg)
        L.circ(x, y, r * .32, 0)
    elif kind == 2:  # olas
        for oy in (-.6, 0, .6):
            L.lin([g(-1 + 2 * j / 12, oy + .22 * math.sin(j / 12 * 4 * math.pi)) for j in range(13)], wg)
    elif kind == 3:  # sol
        L.circ(x, y, r * .38, wg)
        for j in range(8):
            a = j * math.pi / 4
            L.lin([g(.6 * math.cos(a), .6 * math.sin(a)), g(1.0 * math.cos(a), 1.0 * math.sin(a))], wg)
    elif kind == 4:  # pata
        L.elip(x, y + r * .3, r * .55, r * .45, 0)
        for a, b in ((-.75, -.15), (-.28, -.7), (.28, -.7), (.75, -.15)):
            L.circ(x + a * r, y + b * r, r * .22, 0)
    elif kind == 5:  # hoja
        L.pol(_hoja_pts(x - r, y, 0, 2 * r, r * .5), wg)
        L.lin([g(-1, 0), g(.8, 0)], wg)
        L.lin([g(-.2, 0), g(.3, -.35)], wg)
        L.lin([g(-.2, 0), g(.3, .35)], wg)
    elif kind == 6:  # cuadrado escalonado
        L.rect(x, y, r, r, wg)
        L.rect(x, y, r * .62, r * .62, wg)
        L.rect(x, y, r * .26, r * .26, 0)
    elif kind == 7:  # cruz con puntos
        L.lin([g(-.7, 0), g(.7, 0)], wg)
        L.lin([g(0, -.7), g(0, .7)], wg)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            L.circ(x + a * r * .88, y + b * r * .88, r * .16, 0)
    elif kind == 8:  # rombo
        L.pol([g(0, -1), g(1, 0), g(0, 1), g(-1, 0)], wg)
        L.pol([g(0, -.5), g(.5, 0), g(0, .5), g(-.5, 0)], wg)
        L.circ(x, y, r * .14, 0)
    elif kind == 9:  # luna
        a = _arco(0, 0, 1, 1, math.radians(50), math.radians(310), 14)
        b = _arco(.45, 0, .78, .78, math.radians(300), math.radians(60), 14)
        L.pol([g(p, q) for p, q in a + b], wg)
    elif kind == 10:  # serpiente zigzag
        L.lin([g(-1 + 2 * j / 6, (-.5 if j % 2 else .5)) for j in range(7)], wg)
        L.circ(x + r * 1.0, y + r * .5, r * .2, 0)
    elif kind == 11:  # montanas
        L.pol([g(-1, .8), g(-.4, -.5), g(.2, .8)], wg)
        L.pol([g(-.1, .8), g(.45, -.1), g(1, .8)], wg)
        L.circ(x + r * .55, y - r * .6, r * .2, 0)
    elif kind == 12:  # estrella de cuatro puntas
        L.pol([g((1 if j % 2 == 0 else .3) * math.cos(j * math.pi / 4 - math.pi / 2), (1 if j % 2 == 0 else .3) * math.sin(j * math.pi / 4 - math.pi / 2)) for j in range(8)], wg)
        L.circ(x, y, r * .12, 0)
    elif kind == 13:  # circulo con cruz
        L.circ(x, y, r, wg)
        L.lin([g(-1, 0), g(1, 0)], wg)
        L.lin([g(0, -1), g(0, 1)], wg)
        for a, b in ((.5, .5), (-.5, .5), (.5, -.5), (-.5, -.5)):
            L.circ(x + a * r, y + b * r, r * .12, 0)
    elif kind == 14:  # pez
        L.elip(x - r * .15, y, r * .75, r * .42, wg)
        L.pol([g(.5, 0), g(1, -.5), g(1, .5)], wg)
        L.circ(x - r * .5, y - r * .08, r * .1, 0)
    else:  # cuadrado con ojo
        L.rect(x, y, r, r, wg)
        L.circ(x, y, r * .5, wg)
        L.circ(x, y, r * .15, 0)


_KINDS = [  # glifos preferidos por ruina (para rellenos)
    [3, 0, 8, 12, 4, 9], [2, 14, 0, 1, 10, 13], [11, 1, 12, 10, 3, 7], [5, 7, 0, 4, 15, 2], [6, 15, 13, 8, 0, 10], [1, 12, 13, 9, 3, 11],
]

# ---------------------------------------------------------------- piedra base
_cache_mural = {}
_cache_misc = {}


def _arenisca(w, h, i, seed=1):
    s = pygame.Surface((w, h))
    pal = _pal(i)
    c = _mez(pal[1][0], pal[2][0], .35)
    c2 = _mez(pal[1][0], pal[2][0], .75)
    for y in range(0, h, 2):
        pygame.draw.rect(s, _mez(c, c2, y / max(1, h)), (0, y, w, 2))
    rnd = random.Random(seed * 131 + i)
    if _np is not None:
        rs = _np.random.RandomState(seed * 7 + i)
        # manchas suaves
        gw, gh = max(2, w // 40), max(2, h // 40)
        s.fill((32, 32, 32), special_flags=pygame.BLEND_RGB_SUB)
        ms = pygame.Surface((gw, gh))
        a = (rs.rand(gw, gh) * 44).astype(_np.uint8)
        pygame.surfarray.blit_array(ms, _np.stack([a, a, a], axis=2))
        ms = pygame.transform.smoothscale(ms, (w, h))
        s.blit(ms, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        # grano fino
        g = pygame.Surface((max(1, w // 2), max(1, h // 2)))
        n = (rs.rand(max(1, w // 2), max(1, h // 2)) * 22).astype(_np.uint8)
        pygame.surfarray.blit_array(g, _np.stack([n, n, n], axis=2))
        g = pygame.transform.scale(g, (w, h))
        s.blit(g, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    else:
        for _ in range(w * h // 30):
            x, y = rnd.randrange(w), rnd.randrange(h)
            v = rnd.randint(-14, 14)
            q = s.get_at((x, y))
            s.set_at((x, y), (max(0, min(255, q[0] + v)), max(0, min(255, q[1] + v)), max(0, min(255, q[2] + v))))
    # vetas y grietas finas
    cl = pal[2][2]
    for _ in range(max(2, w * h // 14000)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        pts = [(x, y)]
        for _j in range(rnd.randint(3, 6)):
            x += rnd.randint(-12, 12)
            y += rnd.randint(4, 14) * rnd.choice((1, 1, -1))
            pts.append((x, y))
        pygame.draw.lines(s, _mez(c, cl, .3), False, pts, 1)
    return s


def _viñeta(s, fuerza=70):
    w, h = s.get_size()
    key = ("vig", w, h, fuerza)
    v = _cache_misc.get(key)
    if v is None:
        v = pygame.Surface((w, h))
        v.fill((255, 255, 255))
        steps = 10
        for j in range(steps):
            a = 255 - int(fuerza * (1 - j / steps) ** 2)
            ins = j * max(1, min(w, h) // 40)
            if ins * 2 >= min(w, h):
                break
            pygame.draw.rect(v, (a, a, a), (ins, ins, w - 2 * ins, h - 2 * ins), max(1, min(w, h) // 40))
        _cache_misc[key] = v
    s.blit(v, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


# ---------------------------------------------------------------- motivos
def _relleno(L, w, h, i, bw):
    """Detalle repartido por toda la superficie: glifos tenues en cuadricula con jitter."""
    rnd = random.Random(500 + i)
    S = min(w, h)
    g = max(16, S / 8.5)
    kinds = _KINDS[i]
    ny, nx = int(h / g) + 1, int(w / g) + 1
    for a in range(nx):
        for b in range(ny):
            x = (a + .5) * g + rnd.uniform(-g * .12, g * .12)
            y = (b + .5) * g + rnd.uniform(-g * .12, g * .12)
            if x < bw * 1.2 or y < bw * 1.2 or x > w - bw * 1.2 or y > h - bw * 1.2:
                continue
            _glifo(L, kinds[(a * 7 + b * 13 + a * b * 3 + (a // 2) * 5) % len(kinds)], (x - L.cx) / L.U, (y - L.cy) / L.U, g * .22 / L.U)
            L.hondo(1, .8)


def _m_sol(L):
    n = 24
    for j in range(n):
        a = j * 2 * math.pi / n
        if j % 2 == 0:
            L.pol(_rotar([(.48, -.07), (.86, 0), (.48, .07)], a), 0)
        else:
            pts = [(.5 + .3 * t / 10, .045 * math.sin(t / 10 * 3 * math.pi)) for t in range(11)]
            L.lin(_rotar(pts, a), 5)
    L.alto(0)
    for j in range(n):
        if j % 2 == 0:
            a = j * 2 * math.pi / n
            L.lin(_rotar([(.52, 0), (.80, 0)], a), 1.5)
    L.hondo(2)
    for j in range(48):
        a = j * 2 * math.pi / 48 + .03
        L.circ(.9 * math.cos(a), .9 * math.sin(a), .018)
    L.alto(1)
    L.circ(0, 0, .46)
    L.alto(0)
    L.circ(0, 0, .42, 3)
    L.hondo(2)
    for j in range(28):
        a = j * 2 * math.pi / 28
        L.circ(.37 * math.cos(a), .37 * math.sin(a), .022)
    L.alto(2)
    L.circ(0, 0, .31)
    L.alto(0)
    # rostro
    for sg in (-1, 1):
        L.pol([(sg * .06, -.04), (sg * .13, -.1), (sg * .21, -.04), (sg * .13, .0)], 0)
        L.circ(sg * .13, -.05, .03)
        L.hondo(2)
        L.lin([(sg * .05, -.15), (sg * .13, -.18), (sg * .22, -.14)], 3)
        L.alto(1)
        L.circ(sg * .22, .1, .06, 2)
        L.circ(sg * .22, .1, .02)
    L.hondo(2)
    L.lin([(0, -.07), (0, .06), (-.03, .09), (.03, .09)], 2)
    L.hondo(2)
    L.lin(_arco(0, .08, .15, .09, .15, math.pi - .15), 2)
    for j in range(5):
        L.lin([(-.12 + j * .06, .17), (-.12 + j * .06, .21)], 1.5)
    L.hondo(2)
    L.lin([(-.12, -.22), (-.06, -.26), (0, -.22), (.06, -.26), (.12, -.22)], 1.5)
    L.alto(1)


def _m_pez(L):
    # olas de fondo en toda la superficie
    for j, y in enumerate([-1.0 + .19 * q for q in range(11)]):
        pts = [(-1.5 + 3 * t / 40, y + .035 * math.sin(t / 40 * 14 * math.pi + j)) for t in range(41)]
        L.lin(pts, 2.5)
    L.hondo(2, .8)
    # remolinos tipo ola
    for (x, y) in ((-.82, -.74), (.8, .72), (-.8, .78), (.82, -.74)):
        n = 30
        L.lin([(x + (.03 + .1 * t / n) * math.cos(t / n * 5 * math.pi), y + (.03 + .1 * t / n) * math.sin(t / n * 5 * math.pi)) for t in range(n + 1)], 3)
    L.alto(1)
    # peces pequenos
    for (x, y, sg) in ((-.72, -.58, 1), (.7, .6, -1), (.66, -.66, -1), (-.7, .64, 1)):
        L.elip(x, y, .12, .06)
        L.pol([(x + sg * .1, y), (x + sg * .2, y - .06), (x + sg * .2, y + .06)])
        L.alto(2)
        L.circ(x - sg * .06, y - .01, .012)
        L.hondo(2)
    # pez grande (mira a la izquierda)
    top, bot = [], []
    for j in range(25):
        s = j / 24
        hh = .36 * math.sin(math.pi * (.05 + .9 * s)) ** .8 * (1 - .25 * s)
        x = -.72 + s * 1.15
        top.append((x, -hh * .95))
        bot.append((x, hh * 1.05))
    body = top + bot[::-1]
    # aletas
    L.pol([(-.25, -.3), (-.05, -.62), (.12, -.55), (.2, -.28)])
    L.pol([(-.1, .3), (.02, .55), (.18, .42), (.2, .26)])
    L.pol([(.4, -.02), (.9, -.38), (.78, -.02), (.9, .38)])
    L.alto(2)
    L.pol(body)
    L.alto(0)
    # escamas
    for fila in range(5):
        for col in range(9):
            x = -.4 + col * .105 + (.052 if fila % 2 else 0)
            y = -.2 + fila * .1
            hh = .36 * math.sin(math.pi * (.05 + .9 * (x + .72) / 1.15)) ** .8
            if abs(y) < hh * .85 and x < .35:
                L.lin(_arco(x, y, .05, .05, 0.1, math.pi - .1, 6), 1.5)
    L.hondo(2)
    # aletas con rayas
    for q in range(5):
        a = -.2 + q * .05
        L.lin([(.45, 0), (.86 - q * .0, -.34 + q * .14)], 1.5)
    for q in range(5):
        L.lin([(-.2 + q * .08, -.3 - q * .01), (-.05 + q * .045, -.58 + q * .05)], 1.5)
    L.hondo(2)
    # branquia, boca y ojo
    L.lin(_arco(-.3, 0, .09, .27, -math.pi / 2 + .2, math.pi / 2 - .2), 3)
    L.lin([(-.7, .05), (-.6, .08)], 3)
    L.hondo(2)
    L.circ(-.56, -.1, .075)
    L.alto(1)
    L.circ(-.56, -.1, .05)
    L.alto(2)
    L.circ(-.56, -.1, .022)
    L.alto(0)
    # burbujas
    for (x, y, r) in ((-.86, -.2, .035), (-.8, -.34, .025), (-.9, -.46, .02), (.2, -.78, .03), (.3, -.9, .02)):
        L.circ(x, y, r, 2)
    L.alto(0)


def _m_ave(L):
    # fondo: rayos de sol tras el ave
    for j in range(11):
        a = -math.pi / 2 + (j - 5) * .24
        L.pol([(.0, -.1), (1.05 * math.cos(a) - .03, -.1 + 1.05 * math.sin(a)), (1.05 * math.cos(a) + .03, -.1 + 1.05 * math.sin(a))])
    L.alto(2, .45)
    # cola
    for q, a in enumerate((72, 86, 100, 114, 58)):
        L.pol(_rotar([(0, 0), (.1, -.07), (.5, -.08), (.58, 0), (.5, .08), (.1, .07)], math.radians(a), 0, .35))
    L.alto(1)
    for q, a in enumerate((72, 86, 100, 114, 58)):
        L.lin(_rotar([(.08, 0), (.5, 0)], math.radians(a), 0, .35), 1.5)
    L.hondo(2)
    # alas
    for sg in (-1, 1):
        for capa, (n, largo, ancho, tono, a0, a1) in enumerate(((7, .98, .095, 2, -78, 14), (7, .66, .085, 1, -70, 20), (6, .38, .075, 0, -60, 30))):
            for q in range(n):
                a = math.radians(a0 + (a1 - a0) * q / (n - 1))
                lg = largo * (1 - .1 * abs(q - n / 2) / n)
                ang = a if sg == 1 else math.pi - a
                pts = _rotar([(0, 0), (lg * .2, -ancho * .8), (lg * .7, -ancho), (lg, 0), (lg * .7, ancho), (lg * .2, ancho * .8)], ang, sg * .14, -.22)
                L.pol(pts)
                L.alto(tono)
                nerv = _rotar([(lg * .1, 0), (lg * .85, 0)], ang, sg * .14, -.22)
                L.lin(nerv, 1.5)
                L.hondo(2, .9)
    # cuerpo
    L.elip(0, .02, .17, .4)
    L.alto(0)
    for q in range(7):
        y = -.25 + q * .1
        L.lin([(-.12, y - .04), (0, y + .04), (.12, y - .04)], 2)
    L.hondo(2)
    # patas
    for sg in (-1, 1):
        L.lin([(sg * .08, .38), (sg * .13, .56)], 5)
        for a in (-.5, 0, .5):
            L.lin([(sg * .13, .56), (sg * .13 + .1 * math.sin(a) + sg * a * .1, .67)], 3)
    L.alto(2)
    # cabeza y cresta
    for a in (-.6, 0, .6):
        L.pol(_rotar([(0, 0), (.04, -.05), (.2, 0), (.04, .05)], -math.pi / 2 + a, 0, -.5))
    L.alto(2)
    L.circ(0, -.5, .14)
    L.alto(0)
    L.pol([(-.07, -.46), (.07, -.46), (.0, -.3), (-.02, -.28), (-.02, -.33)])
    L.alto(2)
    for sg in (-1, 1):
        L.circ(sg * .07, -.54, .035)
        L.alto(1)
        L.circ(sg * .07, -.54, .015)
        L.hondo(2)
    L.lin([(-.07, -.62), (0, -.58), (.07, -.62)], 2)
    L.hondo(2)
    # estrellas/glifos en los lados
    for (x, y) in ((-.82, -.7), (.82, -.7), (-.88, .1), (.88, .1), (-.8, .75), (.8, .75)):
        _glifo(L, 3 if y < 0 else 12, x, y, .1)
    L.alto(1)


def _m_arbol(L):
    rnd = random.Random(33)
    # suelo y raices
    L.lin([(-1.4, .78), (1.4, .78)], 4)
    for q in range(40):
        x = -1.3 + q * .0675
        L.lin([(x, .78), (x + rnd.uniform(-.03, .03), .78 - rnd.uniform(.04, .1))], 1.5)
    L.alto(2)
    for sg in (-1, 1):
        for q, (dx, dy) in enumerate(((.25, .08), (.5, .0), (.75, -.02))):
            L.lin([(sg * .06, .62), (sg * dx * .6, .74), (sg * dx, .84 + dy)], 8 - q * 2)
    L.alto(2)
    # tronco
    L.pol([(-.15, .78), (-.1, .3), (-.07, -.1), (.07, -.1), (.1, .3), (.15, .78)])
    L.alto(1)
    for q in range(5):
        x = -.06 + q * .03
        L.lin([(x, .72), (x * .8, .4), (x * .6, .0), (x * .5, -.08)], 1.5)
    L.hondo(2)
    # ramas
    def rama(x, y, ang, largo, ancho, prof):
        x2, y2 = x + largo * math.cos(ang), y + largo * math.sin(ang)
        L.lin([(x, y), (x2, y2)], ancho)
        if prof > 0:
            rama(x2, y2, ang - rnd.uniform(.35, .6), largo * .72, ancho * .7, prof - 1)
            rama(x2, y2, ang + rnd.uniform(.35, .6), largo * .72, ancho * .7, prof - 1)
    rama(0, -.08, -math.pi / 2, .2, 7, 3)
    L.alto(2)
    # hojas de copa
    hojas = []
    for q in range(80):
        a = rnd.uniform(0, 2 * math.pi)
        rr = math.sqrt(rnd.random())
        x, y = rr * .8 * math.cos(a), -.38 + rr * .55 * math.sin(a)
        hojas.append((y, x, rnd.uniform(0, 2 * math.pi)))
    hojas.sort()
    for q, (y, x, a) in enumerate(hojas):
        L.pol(_hoja_pts(x, y, a, .2, .055))
        L.alto(q % 3)
        L.lin(_rotar([(.01, 0), (.18, 0)], a, x, y), 1.2)
        L.hondo(2, .9)
    # frutos
    for q in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(.2, .8)
        x, y = rr * .6 * math.cos(a), -.42 + rr * .4 * math.sin(a)
        L.circ(x, y, .04)
        L.alto(0)
        L.circ(x, y, .015)
        L.hondo(2)
    # hojas sueltas en las esquinas
    for q, (x, y, a) in enumerate(((-.8, -.75, .7), (.8, -.75, 2.3), (-.82, .1, -.5), (.84, .05, 3.6), (-.7, .55, .2), (.7, .55, 2.9))):
        L.pol(_hoja_pts(x, y, a, .22, .07))
        L.alto(1)
        L.lin(_rotar([(.01, 0), (.2, 0)], a, x, y), 1.5)
        L.hondo(2)


def _m_mascara(L):
    # greca de fondo en los lados
    for sg in (-1, 1):
        for q in range(8):
            y = -.85 + q * .24
            x = sg * 1.0
            L.lin([(x + sg * .1, y), (x - sg * .1, y), (x - sg * .1, y + .1), (x + sg * .02, y + .1), (x + sg * .02, y + .02)], 2.5)
    L.hondo(2, .8)
    # corona escalonada
    L.pol([(-.62, -.5), (-.62, -.62), (-.46, -.62), (-.46, -.74), (-.28, -.74), (-.28, -.86), (.28, -.86), (.28, -.74), (.46, -.74), (.46, -.62), (.62, -.62), (.62, -.5)])
    L.alto(2)
    for q in range(5):
        L.circ(-.36 + q * .18, -.67, .035)
    L.hondo(0)
    L.lin([(-.5, -.56), (-.4, -.6), (-.3, -.56), (-.2, -.6), (-.1, -.56), (0, -.6), (.1, -.56), (.2, -.6), (.3, -.56), (.4, -.6), (.5, -.56)], 1.5)
    L.hondo(2)
    # orejeras
    for sg in (-1, 1):
        L.circ(sg * .66, -.08, .13)
        L.alto(2)
        L.circ(sg * .66, -.08, .085)
        L.alto(0)
        L.circ(sg * .66, -.08, .03)
        L.hondo(2)
        L.lin([(sg * .66, .05), (sg * .66, .3)], 4)
        L.alto(1)
        L.pol([(sg * .66, .3), (sg * .6, .4), (sg * .66, .5), (sg * .72, .4)])
        L.alto(0)
    # cara
    L.pol([(-.52, -.5), (.52, -.5), (.52, .3), (.4, .58), (.2, .72), (-.2, .72), (-.4, .58), (-.52, .3)])
    L.alto(0)
    # frente
    _glifo(L, 3, 0, -.38, .09)
    L.hondo(2)
    # cejas y ojos
    for sg in (-1, 1):
        L.pol([(sg * .08, -.3), (sg * .46, -.3), (sg * .46, -.2), (sg * .36, -.2), (sg * .36, -.24), (sg * .08, -.24)])
        L.alto(2)
        L.rect(sg * .26, -.08, .15, .12)
        L.hondo(2)
        L.rect(sg * .26, -.08, .1, .08)
        L.alto(1)
        L.circ(sg * .26, -.08, .045)
        L.hondo(2)
        # mejilla con espiral
        _glifo(L, 0, sg * .37, .27, .11)
        L.hondo(2)
    # nariz
    L.pol([(-.07, -.1), (.07, -.1), (.1, .2), (.16, .24), (.16, .3), (-.16, .3), (-.16, .24), (-.1, .2)])
    L.alto(2)
    L.circ(-.08, .26, .018)
    L.circ(.08, .26, .018)
    L.hondo(2)
    # boca con dientes
    L.rect(0, .5, .26, .09)
    L.hondo(2)
    for q in range(8):
        L.rect(-.21 + q * .06, .5, .024, .06)
    L.alto(0)
    L.lin([(-.3, .4), (.3, .4)], 2)
    L.hondo(2)
    # barba de barras
    for q in range(5):
        L.lin([(-.12 + q * .06, .62), (-.12 + q * .06, .72)], 1.5)
    L.hondo(2)
    # marcas en las esquinas
    for (x, y, k) in ((-.85, -.8, 6), (.85, -.8, 6), (-.85, .8, 8), (.85, .8, 8)):
        _glifo(L, k, x, y, .1)
    L.hondo(1)


def _m_ojo(L):
    # estrella grande de 16 puntas y estrella de 8
    L.pol([((.9 if j % 2 == 0 else .58) * math.cos(j * math.pi / 16), (.9 if j % 2 == 0 else .58) * math.sin(j * math.pi / 16)) for j in range(32)])
    L.alto(2)
    L.pol([((.76 if j % 2 == 0 else .42) * math.cos(j * math.pi / 8 + .2), (.76 if j % 2 == 0 else .42) * math.sin(j * math.pi / 8 + .2)) for j in range(16)])
    L.alto(1)
    L.circ(0, 0, .5, 3)
    L.hondo(2)
    for j in range(32):
        a = j * math.pi / 16
        L.circ(.52 * math.cos(a), .52 * math.sin(a), .014)
    L.alto(0)
    # ojo almendrado
    ar = _arco(0, .26, .62, .56, -math.pi + .55, -.55, 18)
    ab = _arco(0, -.26, .62, .56, .55, math.pi - .55, 18)
    ojo = ar + ab
    L.pol(ojo)
    L.alto(0)
    L.pol(ojo, 3)
    L.hondo(2)
    # pestanas
    for j in range(9):
        x = -.45 + j * .1125
        yt = .26 - .56 * math.sqrt(max(0, 1 - (x / .62) ** 2))
        L.lin([(x * 1.0, yt - .02), (x * 1.12, yt - .15)], 3)
        yb = -.26 + .56 * math.sqrt(max(0, 1 - (x / .62) ** 2))
        L.lin([(x, yb + .02), (x * 1.1, yb + .12)], 3)
    L.alto(2)
    L.circ(0, 0, .27)
    L.alto(1)
    for rr in (.22, .17):
        L.circ(0, 0, rr, 2)
    L.hondo(2)
    for j in range(16):
        a = j * math.pi / 8
        L.lin([(.12 * math.cos(a), .12 * math.sin(a)), (.22 * math.cos(a), .22 * math.sin(a))], 1.5)
    L.hondo(2)
    L.circ(0, 0, .095)
    L.alto(2)
    L.circ(-.035, -.035, .03)
    L.alto(0)
    # ceja y lagrima
    L.lin(_arco(0, .45, .72, .42, -math.pi + .5, -.5, 18), 4)
    L.alto(1)
    L.pol([(.0, .62), (-.05, .72), (0, .8), (.05, .72)])
    L.alto(1)
    # estrellas en las esquinas
    for (x, y) in ((-.85, -.75), (.85, -.75), (-.85, .75), (.85, .75)):
        L.pol([((.12 if j % 2 == 0 else .05) * math.cos(j * math.pi / 5 - math.pi / 2) + x, (.12 if j % 2 == 0 else .05) * math.sin(j * math.pi / 5 - math.pi / 2) + y) for j in range(10)])
    L.alto(0)
    for (x, y) in ((-1.1, 0), (1.1, 0)):
        _glifo(L, 1, x, y, .12)
    L.alto(1)


_MOTIVOS = [_m_sol, _m_pez, _m_ave, _m_arbol, _m_mascara, _m_ojo]


def _borde_mural(sf, w, h, i, bw, pal):
    k = max(0.3, min(w, h) / 360.0)
    L = _L(sf, 0, 0, 1.0, pal, k)
    # contorno exterior e interior de la franja
    L.rect(w / 2, h / 2, w / 2 - 1.5, h / 2 - 1.5, 2.5)
    L.alto(0)
    L.rect(w / 2, h / 2, w / 2 - bw, h / 2 - bw, 2.5)
    L.alto(1)
    kind = [3, 14, 8, 5, 6, 12][i]
    r = bw * .3
    step = bw * 1.35
    nx = max(2, int((w - 2 * bw) / step))
    for q in range(nx):
        x = bw + (q + .5) * (w - 2 * bw) / nx
        _glifo(L, kind, x, bw * .5 + 1, r)
        _glifo(L, kind, x, h - bw * .5 - 1, r)
    ny = max(2, int((h - 2 * bw) / step))
    for q in range(ny):
        y = bw + (q + .5) * (h - 2 * bw) / ny
        _glifo(L, kind, bw * .5 + 1, y, r)
        _glifo(L, kind, w - bw * .5 - 1, y, r)
    L.hondo(2)
    for (x, y) in ((bw / 2, bw / 2), (w - bw / 2, bw / 2), (bw / 2, h - bw / 2), (w - bw / 2, h - bw / 2)):
        _glifo(L, 13, x, y, r * 1.05)
    L.hondo(2)


def mural(i, w, h):
    key = (i, w, h)
    m = _cache_mural.get(key)
    if m is not None:
        return m
    i %= N_RUINAS
    v = _var(i)
    pal = _pal(v)
    sf = _arenisca(w, h, v, seed=1 + i)
    S = min(w, h)
    bw = max(6, int(S * .065))
    Lr = _L(sf, w / 2, h / 2, S / 2.0, pal)
    _relleno(Lr, w, h, v, bw)
    U = max(10.0, S / 2 - bw * .9)
    L = _L(sf, w / 2, h / 2, U, pal, max(0.3, S / 2 / 180.0))
    arte_mitos.MOTIVOS[i](L)
    _borde_mural(sf, w, h, v, bw, pal)
    _viñeta(sf, 60)
    _cache_mural[key] = sf
    return sf


# ---------------------------------------------------------------- piezas
def pieza(mural_surf, cols, filas, c, r):
    W, H = mural_surf.get_size()
    pw, ph = W // cols, H // filas
    s = pygame.Surface((pw, ph))
    s.blit(mural_surf, (0, 0), (c * pw, r * ph, pw, ph))
    b = max(2, min(pw, ph) // 22)
    luz, sombra = (255, 236, 176), (70, 42, 16)
    # sombra abajo-derecha, luz arriba-izquierda (biselado)
    for j in range(b):
        t = 1 - j / b
        cl = _mez(s.get_at((min(pw - 1, j + 2), min(ph - 1, j + 2)))[:3], luz, .75 * t)
        pygame.draw.line(s, cl, (j, j), (pw - 1 - j, j))
        pygame.draw.line(s, cl, (j, j), (j, ph - 1 - j))
        cs = _mez(s.get_at((max(0, pw - 3 - j), max(0, ph - 3 - j)))[:3], sombra, .8 * t)
        pygame.draw.line(s, cs, (j, ph - 1 - j), (pw - 1 - j, ph - 1 - j))
        pygame.draw.line(s, cs, (pw - 1 - j, j), (pw - 1 - j, ph - 1 - j))
    pygame.draw.rect(s, (60, 36, 14), (0, 0, pw, ph), 1)
    return s


# ---------------------------------------------------------------- fondo
def _fondo_base(i):
    key = ("fondo", i)
    s = _cache_misc.get(key)
    if s is not None:
        return s
    W, H = 1280, 720
    base = _FONDOS[i % 6]
    s = pygame.Surface((W, H))
    s.fill(base)
    rnd = random.Random(900 + i)
    bh, bwid = 48, 112
    for fila in range(H // bh + 1):
        off = (fila % 2) * bwid // 2 - bwid // 2
        for col in range(W // bwid + 2):
            x, y = col * bwid + off, fila * bh
            v = rnd.randint(-7, 7)
            c = (max(0, base[0] + v), max(0, base[1] + v), max(0, base[2] + v))
            rc = pygame.Rect(x + 2, y + 2, bwid - 4, bh - 4)
            pygame.draw.rect(s, c, rc)
            pygame.draw.line(s, _mez(c, (255, 255, 255), .08), rc.topleft, (rc.right - 1, rc.top))
            pygame.draw.line(s, _mez(c, (0, 0, 0), .35), (rc.left, rc.bottom - 1), (rc.right - 1, rc.bottom - 1))
            for _ in range(2):
                pygame.draw.circle(s, _mez(c, (0, 0, 0), .2), (rc.x + rnd.randrange(rc.w), rc.y + rnd.randrange(rc.h)), rnd.randint(1, 3))
    # glifos muy tenues tallados en el muro
    pal = _pal(i)
    L = _L(s, 0, 0, 1.0, pal, 1.0)
    for q in range(26):
        x, y = rnd.randrange(130, 1150), rnd.randrange(30, 700)
        _glifo(L, rnd.choice(_KINDS[i]), x, y, rnd.randint(10, 18))
    L.pal = [(_mez(base, (90, 80, 70), .25),) * 3] * 3
    L.hondo(1, .3)
    # vineta
    v = pygame.Surface((W, H))
    v.fill((255, 255, 255))
    for j in range(14):
        a = 255 - int(150 * (1 - j / 14) ** 2)
        pygame.draw.rect(v, (a, a, a), (j * 24, j * 14, W - j * 48, H - j * 28), 26)
    s.blit(v, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    try:
        s = s.convert()
    except pygame.error:
        pass
    _cache_misc[key] = s
    return s


def _motas(i):
    key = ("motas", i)
    d = _cache_misc.get(key)
    if d is None:
        rnd = random.Random(70 + i)
        mo = pygame.Surface((8, 8), pygame.SRCALPHA)
        c = _mez(_TONOS[0][1], (255, 255, 255), .2)
        pygame.draw.circle(mo, (*c, 40), (4, 4), 4)
        pygame.draw.circle(mo, (*c, 110), (4, 4), 2)
        d = (mo, [(rnd.random(), rnd.random(), rnd.uniform(6, 20), rnd.uniform(3, 10), rnd.uniform(0, 6.28)) for _ in range(26)])
        _cache_misc[key] = d
    return d


def dibujar_fondo(p, i, t):
    i = _var(i % N_RUINAS)
    p.blit(_fondo_base(i), (0, 0))
    mo, lista = _motas(i)
    for (x, y, vx, vy, ph) in lista:
        px = (x * 1280 + t * vx + 14 * math.sin(t * .6 + ph)) % 1280
        py = (y * 720 - t * vy * .5 + 8 * math.cos(t * .5 + ph)) % 720
        p.blit(mo, (px, py))


# ---------------------------------------------------------------- columnas
_COL_X = (14, 1184)
_COL_W, _COL_Y0, _COL_Y1 = 82, 90, 660


def _col_strip(i):
    key = ("col", i)
    s = _cache_misc.get(key)
    if s is not None:
        return s
    w, h = _COL_W, _COL_Y1 - _COL_Y0
    pal = _pal(i)
    s = _arenisca(w, h, i, seed=5)
    L = _L(s, 0, 0, 1.0, pal, 1.0)
    # marco de la franja
    L.rect(w / 2, h / 2, w / 2 - 1.5, h / 2 - 1.5, 2.5)
    L.alto(0)
    L.rect(w / 2, h / 2, w / 2 - 6, h / 2 - 6, 1.5)
    L.hondo(2)
    L.lin([(w / 2, 8), (w / 2, h - 8)], 1.5)
    L.hondo(2, .7)
    rnd = random.Random(300 + i)
    orden = list(range(16))
    rnd.shuffle(orden)
    fil = 14
    ph = (h - 16) / fil
    for fila in range(fil):
        for col in range(2):
            kind = orden[(fila * 2 + col + fila // 3) % 16]
            _glifo(L, kind, 8 + (col + .5) * (w - 16) / 2, 8 + (fila + .5) * ph, 11.5)
    L.hondo(2)
    _viñeta(s, 40)
    try:
        s = s.convert()
    except pygame.error:
        pass
    _cache_misc[key] = s
    return s


def _brillo_col():
    s = _cache_misc.get("brillocol")
    if s is None:
        s = pygame.Surface((_COL_W, 140))
        for y in range(140):
            a = math.sin(math.pi * y / 140) ** 2
            v = int(70 * a)
            pygame.draw.line(s, (v, int(v * .85), int(v * .5)), (0, y), (_COL_W, y))
        _cache_misc["brillocol"] = s
    return s


def dibujar_columnas(p, i, t):
    i = _var(i % N_RUINAS)
    strip = _col_strip(i)
    br = _brillo_col()
    for xi, x in enumerate(_COL_X):
        p.blit(strip, (x, _COL_Y0))
        y0 = ((t * 90 + xi * 200) % (570 + 140)) - 140  # sube y baja suave: recorre la columna
        a, b = max(0, -int(y0)), min(140, 570 - int(y0))
        if b > a:
            p.blit(br, (x, _COL_Y0 + int(y0) + a), (0, a, _COL_W, b - a), special_flags=pygame.BLEND_RGB_ADD)


# ---------------------------------------------------------------- marco
def _marco_tiras(i, w, h):
    key = ("marco", i, w, h)
    d = _cache_misc.get(key)
    if d is not None:
        return d
    B = 14
    W, H = w + 2 * B, h + 2 * B
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    pal = _pal(i)
    base = _arenisca(W, H, i, seed=9)
    s.blit(base, (0, 0))
    k = 1.0
    L = _L(s, 0, 0, 1.0, pal, k)
    L.rect(W / 2, H / 2, W / 2 - 1.5, H / 2 - 1.5, 2.5)
    L.alto(0)
    L.rect(W / 2, H / 2, w / 2 + 1.5, h / 2 + 1.5, 2.5)
    L.hondo(2)
    # puntos tallados a lo largo
    for q in range(int(W / 28)):
        x = 20 + q * (W - 40) / max(1, int(W / 28) - 1)
        L.circ(x, 7, 2.2)
        L.circ(x, H - 7, 2.2)
    for q in range(int(H / 28)):
        y = 20 + q * (H - 40) / max(1, int(H / 28) - 1)
        L.circ(7, y, 2.2)
        L.circ(W - 7, y, 2.2)
    L.hondo(2)
    for (x, y) in ((7, 7), (W - 7, 7), (7, H - 7), (W - 7, H - 7)):
        L.circ(x, y, 4.5)
    L.alto(0)
    # interior transparente
    pygame.draw.rect(s, (0, 0, 0, 0), (B, B, w, h))
    rects = [(0, 0, W, B), (0, H - B, W, B), (0, B, B, h), (W - B, B, B, h)]
    tiras = []
    for (x, y, a, b) in rects:
        t = s.subsurface((x, y, a, b)).copy()
        try:
            t = t.convert()
        except pygame.error:
            pass
        tiras.append(((x - B, y - B), t))
    # brillo (4 niveles)
    glows = []
    for nivel in range(1, 7):
        gl = []
        for (pos, t) in tiras:
            g = pygame.Surface(t.get_size())
            v = nivel * 14
            g.fill((v, int(v * .8), int(v * .35)))
            gl.append(g)
        glows.append(gl)
    d = (tiras, glows)
    _cache_misc[key] = d
    return d


def dibujar_marco(p, rect, i, completo=False, t=0):
    i = _var(i % N_RUINAS)
    rect = pygame.Rect(rect)
    tiras, glows = _marco_tiras(i, rect.w, rect.h)
    for (pos, tira) in tiras:
        p.blit(tira, (rect.x + pos[0], rect.y + pos[1]))
    if completo:
        nivel = int(3 + 2.9 * math.sin(t * 4))
        nivel = max(0, min(5, nivel))
        for (pos, _), g in zip(tiras, glows[nivel]):
            p.blit(g, (rect.x + pos[0], rect.y + pos[1]), special_flags=pygame.BLEND_RGB_ADD)
        for q in range(8):
            a = t * .9 + q * math.pi / 4
            per = 2 * (rect.w + rect.h)
            d = ((a / (2 * math.pi)) * per * 1.0 + q * per / 8) % per
            if d < rect.w:
                x, y = rect.x + d, rect.y - 7
            elif d < rect.w + rect.h:
                x, y = rect.right + 7, rect.y + d - rect.w
            elif d < 2 * rect.w + rect.h:
                x, y = rect.right - (d - rect.w - rect.h), rect.bottom + 7
            else:
                x, y = rect.x - 7, rect.bottom - (d - 2 * rect.w - rect.h)
            r = 3 + int(2 * math.sin(t * 6 + q))
            pygame.draw.circle(p, (255, 240, 170), (int(x), int(y)), r)
            pygame.draw.line(p, (255, 250, 210), (x - r - 3, y), (x + r + 3, y))
            pygame.draw.line(p, (255, 250, 210), (x, y - r - 3), (x, y + r + 3))


# ---------------------------------------------------------------- rejilla y celda
def dibujar_rejilla(p, rect, cols, filas, pista=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(p, (22, 18, 16), rect)
    pygame.draw.rect(p, (14, 11, 10), rect, 3)
    if pista is not None:
        if pista.get_size() != rect.size:
            pista = pygame.transform.smoothscale(pista, rect.size)
        pista = pista.copy()
        pista.set_alpha(58)
        p.blit(pista, rect.topleft)
    cw, ch = rect.w / cols, rect.h / filas
    for c in range(1, cols):
        x = rect.x + int(c * cw)
        pygame.draw.line(p, (64, 52, 34), (x, rect.y), (x, rect.bottom - 1))
    for r in range(1, filas):
        y = rect.y + int(r * ch)
        pygame.draw.line(p, (64, 52, 34), (rect.x, y), (rect.right - 1, y))


def dibujar_celda_ok(p, rect, t):
    rect = pygame.Rect(rect)
    a = 0.5 + 0.5 * math.sin(t * 5)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((255, 220, 120, int(30 + 40 * a)))
    p.blit(s, rect.topleft)
    pygame.draw.rect(p, (255, 232, 150), rect, 2)
    pygame.draw.rect(p, (255, 245, 200), rect.inflate(-6, -6), 1)
    cx, cy = rect.center
    r = int(min(rect.w, rect.h) * (0.12 + 0.06 * a))
    pygame.draw.line(p, (255, 250, 210), (cx - r, cy), (cx + r, cy))
    pygame.draw.line(p, (255, 250, 210), (cx, cy - r), (cx, cy + r))


# ---------------------------------------------------------------- iconos
def _candado(sf, cx, cy, u):
    cx, cy, u = int(cx), int(cy), float(u)
    w = max(3, int(u * .26))
    # arco del asa
    pygame.draw.circle(sf, (40, 40, 48), (cx, int(cy - u * .35)), int(u * .62), w + 2)
    pygame.draw.circle(sf, (176, 178, 188), (cx, int(cy - u * .35)), int(u * .62), w)
    rc = pygame.Rect(0, 0, int(u * 1.7), int(u * 1.3))
    rc.center = (cx, int(cy + u * .35))
    pygame.draw.rect(sf, (24, 24, 30), rc.move(2, 3), border_radius=int(u * .22))
    pygame.draw.rect(sf, (170, 172, 182), rc, border_radius=int(u * .22))
    pygame.draw.rect(sf, (232, 234, 242), rc, 2, border_radius=int(u * .22))
    pygame.draw.circle(sf, (40, 40, 48), (cx, int(cy + u * .22)), max(2, int(u * .2)))
    pygame.draw.line(sf, (40, 40, 48), (cx, int(cy + u * .3)), (cx, int(cy + u * .65)), max(2, int(u * .16)))


def _icono_base(i, estado, escala):
    key = ("ico", i, estado, round(escala * 20))
    d = _cache_misc.get(key)
    if d is not None:
        return d
    W, H = int(116 * escala), int(136 * escala)
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    gris = estado == "bloqueada"

    def arco_poly(x0, y0, x1, y1, n=18):
        r = (x1 - x0) / 2
        pts = [(x0, y1), (x0, y0 + r)]
        pts += [(x0 + r + r * math.cos(math.pi + math.pi * j / n), y0 + r + r * math.sin(math.pi + math.pi * j / n)) for j in range(n + 1)]
        pts += [(x1, y0 + r), (x1, y1)]
        return pts

    m = max(2, int(3 * escala))
    ext = arco_poly(m, m, W - m, H - m)
    piedra = _arenisca(W, H, _var(i), seed=3)
    if gris:
        piedra = pygame.transform.grayscale(piedra)
        piedra.fill((235, 235, 242), special_flags=pygame.BLEND_RGB_MULT)
    cap = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(cap, (255, 255, 255, 255), ext)
    mk = piedra.convert_alpha()
    mk.blit(cap, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.polygon(s, (30, 20, 10, 130), [(x + 3 * escala, y + 3 * escala) for x, y in ext])
    s.blit(mk, (0, 0))
    luz = (110, 110, 118) if gris else (255, 236, 176)
    som = (40, 40, 46) if gris else (82, 50, 20)
    pygame.draw.lines(s, som, False, ext[len(ext) // 2:], max(2, int(2.5 * escala)))
    pygame.draw.lines(s, luz, False, ext[:len(ext) // 2 + 1], max(2, int(2 * escala)))
    # hueco con mural
    b = int(13 * escala)
    iw, ih = W - 2 * b, H - 2 * b
    mu = mural(i, iw, ih)
    if gris:
        mu = pygame.transform.grayscale(mu)
        mu.fill((170, 170, 182), special_flags=pygame.BLEND_RGB_MULT)
    cap2 = pygame.Surface((iw, ih), pygame.SRCALPHA)
    interior = arco_poly(0, 0, iw, ih)
    pygame.draw.polygon(cap2, (255, 255, 255, 255), interior)
    tmp = mu.convert_alpha()
    tmp.blit(cap2, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.polygon(s, (20, 14, 10), [(x + b, y + b) for x, y in interior])
    s.blit(tmp, (b, b))
    pi_ = [(x + b, y + b) for x, y in interior]
    pygame.draw.lines(s, som, False, pi_[:len(pi_) // 2 + 1], max(2, int(2.5 * escala)))
    pygame.draw.lines(s, luz, False, pi_[len(pi_) // 2:], max(1, int(1.5 * escala)))
    if gris:
        veil = pygame.Surface((iw, ih), pygame.SRCALPHA)
        pygame.draw.polygon(veil, (10, 10, 16, 60), interior)
        s.blit(veil, (b, b))
        _candado(s, W / 2, H * .5, 21 * escala)
    elif estado == "hecha":
        cx, cy, r = int(W - 20 * escala), int(H - 22 * escala), int(14 * escala)
        pygame.draw.circle(s, (90, 56, 16), (cx + 1, cy + 2), r)
        pygame.draw.circle(s, (255, 214, 90), (cx, cy), r)
        pygame.draw.circle(s, (255, 244, 190), (cx, cy), r, max(2, int(2 * escala)))
        pygame.draw.lines(s, (110, 70, 14), False, [(cx - r * .5, cy), (cx - r * .1, cy + r * .45), (cx + r * .55, cy - r * .4)], max(2, int(3 * escala)))
    halo = None
    if estado != "bloqueada":
        halo = pygame.Surface((int(W * 1.5), int(H * 1.4)), pygame.SRCALPHA)
        for q in range(8):
            a = int(14 * (1 - q / 8))
            pygame.draw.ellipse(halo, (255, 220, 120, a + 4), pygame.Rect(0, 0, halo.get_width(), halo.get_height()).inflate(-q * 14, -q * 14))
    d = (s, halo)
    _cache_misc[key] = d
    return d


def icono_ruina(p, i, cx, cy, escala, estado, t=0):
    i %= N_RUINAS
    s, halo = _icono_base(i, estado, escala)
    W, H = s.get_size()
    if halo is not None:
        a = 0.55 + 0.45 * math.sin(t * 3) if estado == "hecha" else 0.25 + 0.2 * math.sin(t * 2.2)
        halo.set_alpha(int(255 * a))
        p.blit(halo, halo.get_rect(center=(cx, cy)))
    p.blit(s, (cx - W // 2, cy - H // 2))
    if estado == "hecha":
        for q in range(3):
            a = t * 1.3 + q * 2.1
            ph = (a % 2.0) / 2.0
            x = cx + (q - 1) * W * .3 + math.sin(a * 3) * 4
            y = cy - H * .15 - ph * H * .4
            r = max(1, int((1 - ph) * 4 * escala))
            pygame.draw.circle(p, (255, 240, 170), (int(x), int(y)), r)