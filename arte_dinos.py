"""Dinosaurios hechos con codigo: esqueletos, huesos sueltos y dinosaurios vivos (caricatura).

API publica (la usa aventura.py y j_fosiles.py):
    DINOS, ORDEN_DINOS, HUESOS_POR_DINO, NOMBRES_HUESOS
    dibujar_esqueleto(p, ident, x, y, escala, huesos, brillo)
    dibujar_hueso(p, ident, i, x, y, escala, angulo)
    dibujar_dino(p, ident, x, y, escala, t, silueta)
    tamano_hueso(ident, i)  -> (ancho, alto) de la pieza a escala 1

Todo comparte una sola "geometria" por dinosaurio (GEO): el esqueleto y el dinosaurio vivo
se construyen sobre los mismos puntos del cuello, lomo, cola, patas y craneo.
Las piezas del esqueleto se dibujan una vez a doble resolucion y se guardan en cache.
"""

import math

import pygame

from nucleo import aclarar, oscurecer

# id: (nombre, periodo, dieta, tamano, dato curioso, color principal)
DINOS = {
    "tiranosaurio": ("Tiranosaurio", "Vivió hace 68 millones de años.", "Comía carne.",
                     "Medía 12 metros de largo.",
                     "Tenía brazos chiquitos, pero dientes enormes.", (214, 98, 72)),
    "triceratops": ("Triceratops", "Vivió hace 68 millones de años.", "Comía plantas.",
                    "Medía 9 metros de largo.",
                    "Tenía tres cuernos y un escudo en la cabeza.", (96, 156, 214)),
    "estegosaurio": ("Estegosaurio", "Vivió hace 150 millones de años.", "Comía plantas.",
                     "Medía 9 metros de largo.",
                     "Tenía placas en el lomo y púas en la cola.", (112, 190, 104)),
    "braquiosaurio": ("Braquiosaurio", "Vivió hace 150 millones de años.",
                      "Comía hojas de árboles altos.", "Medía 22 metros de largo.",
                      "Su cuello larguísimo llegaba a las ramas más altas.", (240, 190, 84)),
    "velociraptor": ("Velociraptor", "Vivió hace 75 millones de años.", "Comía carne.",
                     "Medía 2 metros, como un perro grande.",
                     "Tenía plumas y corría muy rápido.", (150, 110, 205)),
    "anquilosaurio": ("Anquilosaurio", "Vivió hace 68 millones de años.", "Comía plantas.",
                      "Medía 8 metros de largo.",
                      "Tenía una armadura y una cola con maza.", (176, 134, 92)),
}
ORDEN_DINOS = ["tiranosaurio", "triceratops", "estegosaurio", "braquiosaurio",
               "velociraptor", "anquilosaurio"]
HUESOS_POR_DINO = 6
NOMBRES_HUESOS = ["Cráneo", "Cuello y columna", "Costillas", "Cola", "Patas de adelante",
                  "Patas de atrás"]

# ====================================================================== geometria
# Marco del esqueleto: x a la derecha (el dinosaurio mira a la derecha), y hacia abajo,
# origen en el centro de una caja de ~420x250. El suelo esta cerca de y = 108.
# craneo = (cx, cy, tipo, tamano, angulo)   cuello/lomo/cola = polilineas
# costillas = (n, x_inicio, x_fin, profundidad)   pelvis = (x, y, rx, ry)
# brazos / patas = lista de cadenas (cadera, rodilla, tobillo)   dedos = puntas respecto al tobillo
GEO = {
    "tiranosaurio": dict(
        craneo=(150, -70, "tira", 1.0, 0.0),
        cuello=[(108, -58), (88, -56), (70, -44), (55, -32)],
        lomo=[(55, -32), (25, -40), (-10, -42), (-40, -36), (-62, -28)],
        cola=[(-62, -28), (-110, -28), (-155, -15), (-190, 8), (-208, 32)],
        costillas=(6, 46, -16, 56), pelvis=(-55, -22, 26, 20),
        brazos=[[(62, -6), (76, 14), (88, 10)]], dedos_b=[(12, 8), (10, -2)],
        patas=[[(-55, -20), (-16, 34), (-60, 78)]], dedos_p=[(42, 30), (30, 34), (16, 36), (-12, 24)],
        desfase=(22, -3)),
    "triceratops": dict(
        craneo=(154, 24, "tri", 1.0, 0.0),
        cuello=[(100, 0), (82, -10), (62, -18)],
        lomo=[(62, -18), (20, -28), (-30, -28), (-68, -15)],
        cola=[(-68, -15), (-115, -5), (-160, 10), (-202, 38)],
        costillas=(6, 52, -46, 62), pelvis=(-62, -8, 24, 20),
        brazos=[[(55, 2), (70, 48), (62, 98)]], dedos_b=[(16, 10), (8, 12), (0, 12)],
        patas=[[(-60, 0), (-36, 44), (-62, 98)]], dedos_p=[(16, 10), (8, 12), (0, 12)],
        desfase=(18, -4)),
    "estegosaurio": dict(
        craneo=(168, 54, "esteg", 0.8, 0.12),
        cuello=[(146, 48), (126, 32), (106, 10), (88, -8)],
        lomo=[(88, -8), (50, -38), (10, -55), (-30, -62), (-62, -55)],
        cola=[(-62, -55), (-110, -35), (-160, -15), (-205, 0)],
        costillas=(6, 74, -30, 62), pelvis=(-55, -48, 26, 20),
        brazos=[[(78, 0), (86, 52), (98, 96)]], dedos_b=[(14, 10), (8, 12), (0, 12)],
        patas=[[(-55, -40), (-34, 24), (-52, 90)]], dedos_p=[(22, 14), (12, 18), (2, 18)],
        desfase=(18, -4)),
    "braquiosaurio": dict(
        craneo=(158, -112, "braq", 0.7, 0.12),
        cuello=[(138, -102), (126, -82), (113, -54), (98, -26), (80, -6)],
        lomo=[(80, -6), (40, -12), (0, -8), (-40, 2)],
        cola=[(-40, 2), (-100, 25), (-160, 50), (-205, 62)],
        costillas=(6, 70, -20, 54), pelvis=(-38, 6, 24, 20),
        brazos=[[(62, 10), (70, 58), (76, 102)]], dedos_b=[(16, 8), (8, 12), (0, 12)],
        patas=[[(-35, 12), (-32, 58), (-42, 100)]], dedos_p=[(16, 8), (8, 12), (0, 12)],
        desfase=(18, -4)),
    "velociraptor": dict(
        craneo=(158, -40, "vel", 0.78, 0.22),
        cuello=[(134, -38), (112, -42), (88, -30), (66, -18)],
        lomo=[(66, -18), (30, -26), (-15, -24), (-50, -17)],
        cola=[(-50, -17), (-100, -15), (-150, -8), (-205, 0)],
        costillas=(5, 56, -8, 42), pelvis=(-45, -12, 22, 16),
        brazos=[[(55, 0), (72, 28), (100, 20)]], dedos_b=[(16, 8), (14, -2)],
        patas=[[(-45, -8), (-12, 38), (-50, 76)]], dedos_p=[(34, 30), (22, 33), (10, 32)],
        desfase=(20, -3)),
    "anquilosaurio": dict(
        craneo=(158, 46, "anq", 0.85, 0.1),
        cuello=[(136, 40), (112, 24), (90, 10)],
        lomo=[(90, 10), (50, -10), (0, -14), (-40, -8), (-72, 6)],
        cola=[(-72, 6), (-115, 20), (-155, 32), (-182, 42)],
        costillas=(6, 80, -30, 58), pelvis=(-62, 12, 26, 20),
        brazos=[[(70, 28), (78, 68), (84, 102)]], dedos_b=[(14, 8), (8, 10), (0, 10)],
        patas=[[(-55, 25), (-48, 66), (-58, 100)]], dedos_p=[(14, 8), (8, 10), (0, 10)],
        desfase=(16, -4)),
}

# Cabezas (coordenadas locales con el origen en el centro del craneo, ~100 unidades de ancho)
# cr = craneo, mand = mandibula, ojo = (x, y, rx, ry), boca = (frente, comisura),
# dientes = [(x0, x1, y, n, tamano)], cuernos = poligonos, gola = (cx, cy, rx, ry)
def _cab(**kw):
    return kw


CABEZAS = {
    "tira": _cab(
        cr=[(-46, -6), (-40, -26), (-12, -34), (10, -28), (30, -24), (50, -14), (54, -2), (48, 4),
            (-20, 8), (-44, 8)],
        mand=[(-40, 8), (-20, 8), (48, 4), (46, 14), (20, 24), (-14, 26), (-38, 22)],
        ojo=(-8, -14, 9, 11), nariz=(42, -12), boca=((50, 5), (-14, 8)),
        dientes=[(-14, 46, 5, 7, 10)], cuernos=[]),
    "tri": _cab(
        gola=(-34, -6, 42, 60),
        cr=[(-24, -22), (4, -24), (34, -10), (54, 4), (68, 18), (54, 28), (28, 26), (-8, 26),
            (-28, 12)],
        mand=[(-18, 24), (28, 26), (54, 28), (48, 36), (10, 38), (-16, 34)],
        ojo=(2, -6, 8, 9), nariz=(46, 2), boca=((58, 27), (4, 30)), dientes=[],
        cuernos=[[(-4, -16), (16, -22), (60, -56)], [(34, -2), (54, 2), (64, -26)]]),
    "esteg": _cab(
        cr=[(-30, -10), (-8, -16), (24, -10), (46, 2), (48, 10), (20, 13), (-10, 14), (-30, 8)],
        mand=[(-24, 12), (20, 13), (46, 10), (40, 19), (0, 21), (-22, 18)],
        ojo=(-6, -4, 6, 7), nariz=(36, -2), boca=((46, 11), (-8, 14)),
        dientes=[(8, 38, 12, 4, 5)], cuernos=[]),
    "braq": _cab(
        cr=[(-28, 2), (-20, -20), (-4, -30), (8, -20), (10, -10), (32, -8), (42, 2), (40, 12),
            (0, 16), (-28, 12)],
        mand=[(-24, 14), (0, 16), (40, 12), (34, 22), (0, 25), (-22, 22)],
        ojo=(-10, -2, 7, 8), nariz=(-2, -21), boca=((40, 13), (-6, 16)),
        dientes=[(18, 38, 13, 4, 6)], cuernos=[]),
    "vel": _cab(
        cr=[(-36, -8), (-30, -18), (-2, -18), (30, -12), (56, -6), (58, 0), (40, 4), (-34, 8)],
        mand=[(-32, 8), (40, 4), (54, 3), (44, 15), (-4, 15), (-30, 18)],
        ojo=(-14, -8, 9, 10), nariz=(46, -6), boca=((54, 3), (-20, 9)),
        dientes=[(-4, 52, 4, 8, 8)], cuernos=[]),
    "anq": _cab(
        cr=[(-40, -6), (-24, -20), (16, -18), (44, -4), (50, 8), (30, 16), (-30, 16)],
        mand=[(-28, 14), (30, 16), (46, 10), (40, 23), (-24, 23)],
        ojo=(-4, -4, 7, 8), nariz=(40, -2), boca=((48, 10), (-6, 17)), dientes=[],
        cuernos=[[(-38, -6), (-24, -20), (-62, -32)], [(-36, 10), (-24, 16), (-64, 28)],
                 [(10, -16), (28, -12), (22, -34)]]),
}

HUESO = (240, 230, 203)
SOMBRA = (196, 180, 146)
CONTORNO = (112, 94, 68)
LUZ = (255, 252, 238)
OSCURO = (62, 50, 38)
HUESO_LEJOS = ((214, 200, 168), (170, 152, 118))
SS = 2                                          # sobremuestreo de las piezas del esqueleto


# ====================================================================== utilidades
def _spline(pts, n=8):
    """Curva suave (Catmull-Rom) que pasa por los puntos."""
    if len(pts) < 3:
        return list(pts)
    q = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u +
                                    (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def _largo(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def _en(pts, u):
    """Punto y direccion (unitaria) a la fraccion u del largo de la polilinea."""
    total = _largo(pts)
    meta = max(0.0, min(1.0, u)) * total
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if meta <= d or i == len(pts) - 2:
            f = 0 if d == 0 else min(1.0, meta / d)
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
            dx, dy = (pts[i + 1][0] - pts[i][0]), (pts[i + 1][1] - pts[i][1])
            n = math.hypot(dx, dy) or 1.0
            return (x, y), (dx / n, dy / n)
        meta -= d
    return pts[-1], (1.0, 0.0)


def _rot(pts, cx, cy, z, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + z * (x * ca - y * sa), cy + z * (x * sa + y * ca)) for x, y in pts]


def _elipse_pts(cx, cy, rx, ry, n=22, rot=0.0):
    ca, sa = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


# ====================================================================== lienzo de huesos
class _Lienzo:
    """Superficie transparente (con sobremuestreo) en coordenadas del esqueleto."""

    def __init__(self, w=520, h=360):
        self.s = pygame.Surface((w * SS, h * SS), pygame.SRCALPHA)
        self.ox, self.oy = w * SS / 2, h * SS / 2

    def pt(self, q):
        return (self.ox + q[0] * SS, self.oy + q[1] * SS)

    def linea(self, pts, g, col=(HUESO, SOMBRA)):
        P = [self.pt(q) for q in pts]
        hueso, sombra = col
        pasos = (
            (CONTORNO, g + 3.2, 0.0, 0.0),
            (sombra, g, 0.0, 0.0),
            (hueso, g * 0.74, 0.0, -g * 0.12),
            (LUZ, max(1.0, g * 0.24), 0.0, -g * 0.26),
        )
        for c, w, dx, dy in pasos:
            w = max(1, int(w * SS))
            Q = [(x + dx * SS, y + dy * SS) for x, y in P]
            if len(Q) > 1:
                pygame.draw.lines(self.s, c, False, Q, w)
            for x, y in Q:
                pygame.draw.circle(self.s, c, (int(x), int(y)), max(1, w // 2))

    def poli(self, pts, hueso=HUESO, sombra=SOMBRA, borde=CONTORNO, grosor=2.2):
        P = [self.pt(q) for q in pts]
        cx = sum(x for x, _ in P) / len(P)
        cy = sum(y for _, y in P) / len(P)
        pygame.draw.polygon(self.s, sombra, P)
        interior = [(cx + (x - cx) * 0.86, cy + (y - cy) * 0.86 - 1.5 * SS) for x, y in P]
        pygame.draw.polygon(self.s, hueso, interior)
        pygame.draw.lines(self.s, borde, True, P, max(1, int(grosor * SS)))
        for x, y in P:
            pygame.draw.circle(self.s, borde, (int(x), int(y)), max(1, int(grosor * SS / 2)))

    def elipse(self, cx, cy, rx, ry, rot=0.0, **kw):
        self.poli(_elipse_pts(cx, cy, rx, ry, 20, rot), **kw)

    def nudo(self, q, r, col=(HUESO, SOMBRA)):
        self.elipse(q[0], q[1], r, r, hueso=col[0], sombra=col[1], grosor=1.8)


# ====================================================================== partes del esqueleto
def _cabeza_pts(ident, k):
    cx, cy, tipo, z, ang = GEO[ident]["craneo"]
    return [_rot(poly, cx, cy, z, ang) for poly in k], (cx, cy, tipo, z, ang)


def _parte_craneo(L, ident):
    g = GEO[ident]
    cx, cy, tipo, z, ang = g["craneo"]
    c = CABEZAS[tipo]
    if "gola" in c:
        gx, gy, rx, ry = c["gola"]
        pts = []
        for i in range(64):
            a = 2 * math.pi * i / 64
            r = 1 + 0.055 * math.sin(a * 11)
            pts.append((gx + rx * r * math.cos(a), gy + ry * r * math.sin(a)))
        L.poli(_rot(pts, cx, cy, z, ang))
        for dy in (-26, 16):
            L.elipse(*_rot([(gx - 6, gy + dy)], cx, cy, z, ang)[0], 12 * z, 17 * z, ang,
                     hueso=OSCURO, sombra=(30, 24, 18), grosor=1.5)
    for h in c["cuernos"]:
        L.poli(_rot(h, cx, cy, z, ang), hueso=(250, 244, 226))
    L.poli(_rot(c["mand"], cx, cy, z, ang), hueso=(228, 216, 186))
    L.poli(_rot(c["cr"], cx, cy, z, ang))
    for x0, x1, y, n, tam in c["dientes"]:
        for i in range(n):
            x = x0 + (x1 - x0) * (i + 0.5) / n
            w = (x1 - x0) / n * 0.42
            L.poli(_rot([(x - w, y - 1), (x + w, y - 1), (x, y + tam)], cx, cy, z, ang),
                   hueso=(255, 253, 244), sombra=(225, 215, 190), grosor=1.2)
    ox, oy, rx, ry = c["ojo"]
    p0 = _rot([(ox, oy)], cx, cy, z, ang)[0]
    L.elipse(p0[0], p0[1], rx * z, ry * z, ang, hueso=OSCURO, sombra=(30, 24, 18), grosor=2.0)
    nx, ny = _rot([c["nariz"]], cx, cy, z, ang)[0]
    L.elipse(nx, ny, 3.2 * z, 2.6 * z, hueso=OSCURO, sombra=OSCURO, grosor=1.0)


def _parte_columna(L, ident):
    g = GEO[ident]
    cadena = _spline(g["cuello"] + g["lomo"][1:], 6)
    L.linea(cadena, 6.0)
    # vertebras con sus espinas
    total = _largo(cadena)
    n = int(total / 9)
    for k in range(n + 1):
        (x, y), (dx, dy) = _en(cadena, k / max(1, n))
        nx, ny = dy, -dx                           # normal hacia arriba
        if ny > 0:
            nx, ny = -nx, -ny
        largo = 9 + 4 * math.sin(math.pi * k / max(1, n))
        L.linea([(x, y), (x + nx * largo, y + ny * largo)], 3.0)
        L.elipse(x, y, 4.2, 4.2, hueso=HUESO, sombra=SOMBRA, grosor=1.5)
    px, py, rx, ry = g["pelvis"]
    L.elipse(px, py, rx, ry, rot=-0.3, hueso=(232, 220, 190))
    L.elipse(px + 3, py - 2, rx * 0.3, ry * 0.38, rot=-0.3, hueso=(250, 244, 226), grosor=1.4)
    if ident == "estegosaurio":
        lom = _spline(g["lomo"], 6)
        for k in range(9):
            u = 0.04 + 0.9 * k / 8
            (x, y), (dx, dy) = _en(lom, u)
            h = 14 + 30 * math.sin(math.pi * (0.1 + 0.85 * u))
            L.poli([(x - 12, y - 6), (x - 9, y - h * 0.65), (x - 1, y - h), (x + 8, y - h * 0.65),
                    (x + 11, y - 6)], hueso=(244, 236, 214))
    if ident == "anquilosaurio":
        lom = _spline(g["lomo"], 6)
        for k in range(8):
            (x, y), _ = _en(lom, 0.06 + 0.88 * k / 7)
            L.elipse(x, y - 11, 8, 6.5, hueso=(236, 226, 198))
            L.poli([(x - 5, y - 15), (x - 12, y - 28), (x + 2, y - 17)], hueso=(250, 244, 226))


def _parte_costillas(L, ident):
    g = GEO[ident]
    n, xa, xb, prof = g["costillas"]
    cad = _spline(g["cuello"][-2:] + g["lomo"][1:], 6)
    base = _spline(g["lomo"], 6)
    puntas = []
    for i in range(n):
        u = (i + 0.5) / n
        x = xa + (xb - xa) * u
        # y del lomo en esa x
        y = min(base, key=lambda q: abs(q[0] - x))[1]
        d = prof * (0.55 + 0.45 * math.sin(math.pi * (0.12 + 0.8 * u)))
        costilla = _spline([(x, y + 4), (x + 8, y + d * 0.45), (x + 2, y + d * 0.85), (x - 6, y + d)], 5)
        L.linea(costilla, 5.0)
        puntas.append((x - 6, y + d))
    L.linea(puntas, 3.0)                           # esternon


def _parte_cola(L, ident):
    g = GEO[ident]
    cad = _spline(g["cola"], 6)
    n = 17
    pts = [_en(cad, k / n)[0] for k in range(n + 1)]
    L.linea(pts, 4.0)
    for k, (x, y) in enumerate(pts):
        r = 7.5 * (1 - k / (n + 1)) + 2.2
        L.elipse(x, y, r, r * 0.85, hueso=HUESO, sombra=SOMBRA, grosor=1.6)
        if k % 2 == 0 and k > 1:
            _, (dx, dy) = _en(cad, k / n)
            nx, ny = -dy, dx
            if ny < 0:
                nx, ny = -nx, -ny
            L.linea([(x, y), (x + nx * r * 1.4, y + ny * r * 1.4)], 2.4)
    fin, (dx, dy) = _en(cad, 1.0)
    if ident == "estegosaurio":                    # cuatro puas
        for k, (a, b) in enumerate(((-14, -42), (-34, -36), (-14, 40), (-34, 34))):
            u = 0.74 + 0.1 * (k % 2)
            (x, y), _ = _en(cad, u)
            L.poli([(x - 8, y), (x + 8, y), (x + a, y + b)], hueso=(250, 244, 226))
    if ident == "anquilosaurio":                   # maza
        mx, my = fin[0] - 14, fin[1] + 1
        L.elipse(mx, my, 30, 22, rot=0.15, hueso=(232, 220, 190))
        for dx2, dy2 in ((-14, -14), (6, -18), (22, -4), (-18, 6), (4, 12), (-4, -2)):
            L.elipse(mx + dx2, my + dy2, 5, 5, hueso=(250, 244, 226), grosor=1.5)


def _pie(L, tobillo, dedos, g, col, garra=None):
    for d in dedos:
        punta = (tobillo[0] + d[0], tobillo[1] + d[1])
        L.linea([tobillo, punta], g, col)
        L.poli([(punta[0] - 1, punta[1] - 3), (punta[0] + 7, punta[1] + 1), (punta[0] - 1, punta[1] + 4)],
               hueso=(250, 244, 226), grosor=1.3)
    if garra:
        L.poli(garra, hueso=(250, 244, 226), grosor=1.5)


def _extremidades(L, ident, clave, dedos_clave, grosores):
    g = GEO[ident]
    dx, dy = g["desfase"]
    for lejos in (True, False):
        col = HUESO_LEJOS if lejos else (HUESO, SOMBRA)
        for cad in g[clave]:
            c = [(x + (dx if lejos else 0), y + (dy if lejos else 0)) for x, y in cad]
            curva = _spline(c, 6)
            L.linea(curva[:len(curva) // 2 + 1], grosores[0], col)
            L.linea(curva[len(curva) // 2:], grosores[1], col)
            L.nudo(c[0], grosores[0] * 0.8, col)
            L.nudo(c[1], grosores[0] * 0.72, col)
            garra = None
            if ident == "velociraptor" and clave == "patas":
                t = c[2]
                garra = [(t[0] + 18, t[1] - 4), (t[0] + 34, t[1] - 22), (t[0] + 28, t[1] + 4)]
            _pie(L, c[2], g[dedos_clave], grosores[1] * 0.8, col, garra)
            L.nudo(c[2], grosores[1] * 0.75, col)


def _parte_brazos(L, ident):
    peq = ident in ("tiranosaurio", "velociraptor")
    _extremidades(L, ident, "brazos", "dedos_b", (4.0, 3.2) if peq else (9.5, 7.5))
    sx, sy = GEO[ident]["brazos"][0][0]
    if not peq:
        L.elipse(sx - 4, sy - 2, 11, 16, rot=0.3, hueso=(232, 220, 190))


def _parte_patas(L, ident):
    if ident in ("tiranosaurio", "velociraptor"):
        _extremidades(L, ident, "patas", "dedos_p", (10.5, 7.0))
    else:
        _extremidades(L, ident, "patas", "dedos_p", (9.5, 7.5))


_PARTES = [_parte_craneo, _parte_columna, _parte_costillas, _parte_cola, _parte_brazos, _parte_patas]
_ORDEN_PINTADO = [3, 5, 1, 2, 4, 0]

_maestras = {}
_fantasmas = {}
_escaladas = {}


def _maestra(ident, i):
    """(superficie recortada, desplazamiento x, y de su esquina respecto al centro, en px SS)."""
    clave = (ident, i)
    if clave not in _maestras:
        L = _Lienzo()
        _PARTES[i](L, ident)
        r = L.s.get_bounding_rect()
        r.inflate_ip(4, 4)
        r = r.clip(L.s.get_rect())
        _maestras[clave] = (L.s.subsurface(r).copy(), r.x - L.ox, r.y - L.oy)
    return _maestras[clave]


def _fantasma(ident, i):
    clave = (ident, i)
    if clave not in _fantasmas:
        s, ox, oy = _maestra(ident, i)
        mask = pygame.mask.from_surface(s, 40)
        g = mask.to_surface(setcolor=(236, 226, 200, 78), unsetcolor=(0, 0, 0, 0))
        for k, (x, y) in enumerate(mask.outline(3)):
            if k % 2 == 0:
                pygame.draw.circle(g, (255, 244, 214, 215), (x, y), 2)
        _fantasmas[clave] = (g, ox, oy)
    return _fantasmas[clave]


def _escalada(ident, i, fantasma, esc):
    q = round(esc * 25) / 25
    clave = (ident, i, fantasma, q)
    if clave not in _escaladas:
        s, ox, oy = (_fantasma if fantasma else _maestra)(ident, i)
        f = q / SS
        w, h = max(1, int(s.get_width() * f)), max(1, int(s.get_height() * f))
        _escaladas[clave] = (pygame.transform.smoothscale(s, (w, h)), ox * f, oy * f)
    return _escaladas[clave]


_resplandor = {}


def _brillo_sup(w, h):
    clave = (w, h)
    if clave not in _resplandor:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for k in range(14, 0, -1):
            f = k / 14
            pygame.draw.ellipse(s, (120, 100, 255, int(150 * (1 - f) ** 1.3)),
                                pygame.Rect(w / 2 - w * f / 2, h / 2 - h * f / 2, w * f, h * f))
        _resplandor[clave] = s
    return _resplandor[clave]


def dibujar_esqueleto(p, ident, x, y, escala=1.0, huesos=None, brillo=0.0):
    """Esqueleto de perfil centrado en (x, y), unos 420x250 px a escala 1."""
    hs = set(range(HUESOS_POR_DINO)) if huesos is None else set(huesos)
    destino = p
    ox0, oy0 = x, y
    if brillo > 0:
        W, H = int(520 * escala), int(340 * escala)
        destino = pygame.Surface((W, H), pygame.SRCALPHA)
        ox0, oy0 = W / 2, H / 2
    for i in _ORDEN_PINTADO:
        s, ox, oy = _escalada(ident, i, i not in hs, escala)
        destino.blit(s, (ox0 + ox, oy0 + oy))
    if brillo > 0:
        b = max(0.0, min(1.0, brillo))
        destino.fill((int(70 * b), int(55 * b), int(170 * b), 0), special_flags=pygame.BLEND_RGB_ADD)
        g = _brillo_sup(int(560 * escala), int(360 * escala))
        g.set_alpha(int(255 * b))
        p.blit(g, g.get_rect(center=(int(x), int(y))))
        p.blit(destino, destino.get_rect(center=(int(x), int(y))))


def tamano_hueso(ident, i):
    """(ancho, alto) en px de la pieza i dibujada con dibujar_hueso a escala 1."""
    s = _maestra(ident, i)[0]
    k = _k_hueso(s)
    return s.get_width() * k / SS, s.get_height() * k / SS


def _k_hueso(s):
    mayor = max(s.get_width(), s.get_height()) / SS
    return max(0.3, min(1.3, 112.0 / mayor)) * SS / SS


_piezas = {}


def dibujar_hueso(p, ident, i, x, y, escala=1.0, angulo=0.0):
    """La pieza i suelta, centrada en (x, y), de hasta ~120 px a escala 1."""
    s = _maestra(ident, i)[0]
    k = _k_hueso(s) * escala
    q = round(k * 25) / 25
    clave = (ident, i, q)
    if clave not in _piezas:
        w, h = max(1, int(s.get_width() * q / SS)), max(1, int(s.get_height() * q / SS))
        _piezas[clave] = pygame.transform.smoothscale(s, (w, h))
    img = _piezas[clave]
    if angulo:
        img = pygame.transform.rotozoom(img, -math.degrees(angulo), 1.0)
    p.blit(img, img.get_rect(center=(int(x), int(y))))


# ====================================================================== dinosaurio vivo
# torso = (rx, ry, bajar), cuello/cola = (radio inicial, radio final), pata/brazo = radios,
# cabeza = tamano de la cabeza viva
VIVO = {
    "tiranosaurio": dict(torso=(80, 46, 0), cuello=(22, 34), cola=(33, 3), pata=(27, 17, 11),
                         brazo=(8, 6, 5), cabeza=1.3, rayas=True),
    "triceratops": dict(torso=(84, 46, 0), cuello=(30, 36), cola=(26, 3), pata=(22, 17, 14),
                        brazo=(21, 16, 13), cabeza=1.1),
    "estegosaurio": dict(torso=(80, 44, 0), cuello=(13, 25), cola=(26, 4), pata=(21, 16, 12),
                         brazo=(16, 13, 11), cabeza=1.75),
    "braquiosaurio": dict(torso=(72, 38, 0), cuello=(12, 25), cola=(22, 3), pata=(20, 15, 13),
                          brazo=(18, 14, 12), cabeza=1.9, manchas=True),
    "velociraptor": dict(torso=(62, 30, 0), cuello=(11, 20), cola=(18, 2), pata=(19, 11, 7),
                         brazo=(6, 4, 3), cabeza=1.5, rayas=True),
    "anquilosaurio": dict(torso=(88, 40, 0), cuello=(20, 30), cola=(21, 6), pata=(23, 18, 15),
                          brazo=(19, 16, 14), cabeza=1.45),
}
FV = 0.92                                        # escala del dinosaurio vivo respecto a GEO
CONTORNO_VIVO = (52, 36, 44)
SIL_COLOR = (86, 102, 138)


def _cadena(pts, radios, paso=None):
    """Circulos a lo largo de una polilinea con radio interpolado. radios = lista de radios."""
    total = _largo(pts) or 1.0
    out = []
    d = 0.0
    n = len(radios) - 1
    while d <= total:
        u = d / total
        (x, y), _ = _en(pts, u)
        f = u * n
        k = min(n - 1, int(f)) if n > 0 else 0
        r = radios[k] + (radios[min(n, k + 1)] - radios[k]) * (f - k) if n > 0 else radios[0]
        out.append(("c", (x, y), r))
        d += paso or max(1.4, r * 0.35)
    return out


class _Pincel:
    def __init__(self, p, ox, oy, s, sil):
        self.p, self.ox, self.oy, self.s, self.sil = p, ox, oy, s, sil

    def pt(self, q):
        return (self.ox + q[0] * self.s, self.oy + q[1] * self.s)

    def grupo(self, prims, relleno, grosor=3.4):
        """Dibuja primero el contorno de todo el grupo y luego el relleno (efecto pegatina)."""
        if self.sil:
            contorno, relleno = relleno, relleno
            grosor = 0.8
        else:
            contorno = CONTORNO_VIVO
        for fase in (0, 1):
            col = contorno if fase == 0 else relleno
            ex = grosor if fase == 0 else 0.0
            for pr in prims:
                if pr[0] == "c":
                    cx, cy = self.pt(pr[1])
                    pygame.draw.circle(self.p, col, (int(cx), int(cy)), max(1, int((pr[2] + ex) * self.s)))
                elif pr[0] == "e":
                    cx, cy = self.pt(pr[1])
                    pts = _elipse_pts(cx, cy, (pr[2] + ex) * self.s, (pr[3] + ex) * self.s, 22, pr[4] if len(pr) > 4 else 0)
                    pygame.draw.polygon(self.p, col, pts)
                else:
                    pts = [self.pt(q) for q in pr[1]]
                    pygame.draw.polygon(self.p, col, pts)
                    if ex:
                        pygame.draw.lines(self.p, col, True, pts, max(1, int(ex * 2 * self.s)))
                        for q in pts:
                            pygame.draw.circle(self.p, col, (int(q[0]), int(q[1])), max(1, int(ex * self.s)))

    def linea(self, pts, col, g):
        P = [self.pt(q) for q in pts]
        pygame.draw.lines(self.p, col, False, P, max(1, int(g * self.s)))
        for x, y in P:
            pygame.draw.circle(self.p, col, (int(x), int(y)), max(1, int(g * self.s / 2)))

    def circ(self, q, r, col):
        x, y = self.pt(q)
        pygame.draw.circle(self.p, col, (int(x), int(y)), max(1, int(r * self.s)))


def _mover(ident, t):
    """Puntos animados (cuello, cola) y desplazamientos de la cabeza y el torso."""
    g = GEO[ident]
    cola = g["cola"]
    cd = _spline(cola, 5)
    total = _largo(cd) or 1.0
    acum = 0.0
    nueva = []
    for k, (x, y) in enumerate(cd):
        if k:
            acum += math.dist(cd[k - 1], cd[k])
        u = acum / total
        nueva.append((x - 4 * u * math.sin(t * 1.7 - u * 2.0) * 0.3,
                      y + 15 * u * u * math.sin(t * 1.7 - u * 2.6) + 4 * u * math.sin(t * 0.9)))
    cu = _spline(g["cuello"], 5)
    nlen = len(cu)
    nc = []
    amp = 3.5 if ident != "braquiosaurio" else 6.5
    for k, (x, y) in enumerate(cu):
        w = 1 - k / max(1, nlen - 1)              # 1 en la cabeza, 0 en el hombro
        nc.append((x + amp * w * w * math.sin(t * 1.2), y + amp * 0.6 * w * math.sin(t * 1.9 + 1)))
    dcab = (nc[0][0] - cu[0][0], nc[0][1] - cu[0][1])
    return nueva, nc, dcab


def _pintar_dino(p, ident, x, y, escala, t, sil):
    g = GEO[ident]
    v = VIVO[ident]
    color = DINOS[ident][5]
    s = escala * FV
    pin = _Pincel(p, x, y, s, sil)
    base = SIL_COLOR if sil else color
    claro = SIL_COLOR if sil else aclarar(color, 0.42)
    oscuro = SIL_COLOR if sil else oscurecer(color, 0.22)
    marfil = SIL_COLOR if sil else (250, 244, 222)
    resp = 1 + 0.03 * math.sin(t * 2.2)
    cola, cuello, dcab = _mover(ident, t)
    rxT, ryT, _ = v["torso"]
    ryT *= resp
    lomo = _spline(g["lomo"], 6)
    bajo = [(a, b + ryT * 0.82) for a, b in lomo]
    dx, dy = g["desfase"]
    blob = lambda r: [r[0], r[1], r[2]]

    # ---- extras que van detras del cuerpo (placas, frente de triceratops)
    if ident == "estegosaurio" and True:
        placas = []
        pts = _spline(g["cuello"][-2:] + g["lomo"] + g["cola"][1:3], 6)
        for k in range(10):
            u = 0.05 + 0.92 * k / 9
            (px, py), _ = _en(pts, u)
            h = 20 + 34 * math.sin(math.pi * (0.12 + 0.8 * u))
            placas.append(("p", [(px - 15, py + 10), (px - 12, py - h * 0.6), (px - 2, py - h),
                                 (px + 10, py - h * 0.6), (px + 15, py + 10)]))
        pin.grupo(placas, SIL_COLOR if sil else (242, 150, 62))
    if ident == "triceratops":
        gx, gy, rx, ry = CABEZAS["tri"]["gola"]
        cx, cy, _, z, ang = g["craneo"]
        z = v["cabeza"]
        cx, cy = cx + dcab[0], cy + dcab[1]
        pts = []
        for i in range(60):
            a = 2 * math.pi * i / 60
            r = 1 + 0.06 * math.sin(a * 11)
            pts.append((gx + rx * r * math.cos(a), gy + ry * r * math.sin(a)))
        pin.grupo([("p", _rot(pts, cx, cy, z, ang))], SIL_COLOR if sil else aclarar(color, 0.12), 4.0)
        if not sil:
            for i in range(11):
                a = math.pi * 0.78 + i * 0.27
                q = _rot([(gx + rx * 0.92 * math.cos(a), gy + ry * 0.92 * math.sin(a))], cx, cy, z, ang)[0]
                pin.circ(q, 5.2, (255, 214, 120))
            for dyv in (-24, 16):
                q = _rot([(gx - 6, gy + dyv)], cx, cy, z, ang)[0]
                pin.circ(q, 11 * z, oscurecer(color, 0.28))

    # ---- patas lejanas (mas oscuras)
    def patas(lejos):
        grupo = []
        for clave, rad, dedos in (("patas", v["pata"], g["dedos_p"]), ("brazos", v["brazo"], g["dedos_b"])):
            for cad in g[clave]:
                c = [(a + (dx if lejos else 0), b + (dy if lejos else 0)) for a, b in cad]
                curva = _spline(c, 6)
                grupo += _cadena(curva, list(rad))
                tob = c[2]
                for d in dedos[:3]:
                    pt = (tob[0] + d[0] * 0.8, tob[1] + d[1] * 0.8)
                    grupo += _cadena([tob, pt], [rad[2] * 0.95, rad[2] * 0.75])
        return grupo
    pin.grupo(patas(True), oscuro)

    # ---- cola y cuerpo
    cola_prims = _cadena(cola, [v["cola"][0], v["cola"][0] * 0.55, v["cola"][1]])
    if ident == "anquilosaurio":
        fin = cola[-1]
        pin.grupo([("c", (fin[0] + 4, fin[1] - 1), 3)], base)
    pin.grupo(cola_prims, base)
    if ident == "anquilosaurio":
        fin = cola[-1]
        club = [("e", (fin[0] - 8, fin[1]), 30, 22, 0.1)]
        pin.grupo(club, SIL_COLOR if sil else (150, 118, 86))
        if not sil:
            for a, b in ((-10, -12), (6, -16), (20, -4), (-16, 6), (4, 10), (-2, -2)):
                pin.circ((fin[0] - 8 + a, fin[1] + b), 5, (214, 190, 150))
        pin.grupo([("p", [(fin[0] - 20, fin[1] - 18), (fin[0] - 14, fin[1] - 36), (fin[0] - 4, fin[1] - 20)]),
                   ("p", [(fin[0] + 4, fin[1] - 18), (fin[0] + 14, fin[1] - 34), (fin[0] + 18, fin[1] - 14)])],
                  marfil, 2.4)
    if ident == "estegosaurio":
        puas = []
        for k, (u, ang) in enumerate(((0.68, -1.7), (0.86, -2.3), (0.68, 1.5), (0.86, 2.3))):
            (px, py), _ = _en(cola, u)
            nx, ny = -math.sin(ang), math.cos(ang)
            puas.append(("p", [(px - nx * 8, py - ny * 8), (px + nx * 8, py + ny * 8),
                               (px + 42 * math.cos(ang), py + 42 * math.sin(ang))]))
        pin.grupo(puas, marfil, 2.4)

    cuerpo = _cadena(bajo, [ryT * 0.78, ryT * 0.95, ryT * 0.9, ryT * 0.72])
    cuerpo += _cadena(cuello, [v["cuello"][0], v["cuello"][1]])
    cuerpo += _cadena([(a, b + ryT * 0.2) for a, b in g["cuello"][-2:]] + [bajo[0]], [v["cuello"][1] * 0.9, ryT * 0.8])
    cx0 = (g["lomo"][0][0] + g["lomo"][-1][0]) / 2
    cuerpo.append(("e", (cx0, bajo[len(bajo) // 2][1] + ryT * 0.12), rxT, ryT * 0.98))
    pin.grupo(cuerpo, base)
    if not sil:
        vientre = _cadena([(a, b + ryT * 0.6) for a, b in lomo[3:-3]], [ryT * 0.34])
        vientre.append(("e", (cx0, bajo[len(bajo) // 2][1] + ryT * 0.5), rxT * 0.62, ryT * 0.4))
        for pr in vientre:
            if pr[0] == "c":
                pin.circ(pr[1], pr[2], claro)
            else:
                pts = _elipse_pts(*pin.pt(pr[1]), pr[2] * pin.s, pr[3] * pin.s)
                pygame.draw.polygon(p, claro, pts)
        if v.get("rayas"):
            for k in range(6):
                (qx, qy), (ddx, ddy) = _en(lomo, 0.12 + 0.16 * k)
                pin.linea([(qx, qy + 4), (qx + 3, qy + ryT * 0.62)], oscurecer(color, 0.2), 5)
            for k in range(5):
                (qx, qy), _ = _en(cola, 0.08 + 0.13 * k)
                pin.linea([(qx, qy - cola_prims[0][2] * 0.1 * (1 - 0.1 * k)),
                           (qx + 2, qy + cola_prims[0][2] * 0.36 * (1 - 0.15 * k))],
                          oscurecer(color, 0.2), 4)
        if v.get("manchas"):
            for a, b, r in ((-50, 0.2, 9), (-22, 0.45, 12), (10, 0.15, 8), (36, 0.4, 10), (58, 0.1, 7),
                            (-5, 0.65, 7), (-72, 0.4, 6)):
                pin.circ((cx0 + a, bajo[len(bajo) // 2][1] - ryT * 0.4 + ryT * b * 1.4), r, oscuro)
            for u, r in ((0.5, 5), (0.6, 4), (0.75, 4)):
                (qx, qy), _ = _en(g["cuello"][::-1], u)
                pin.circ((qx, qy), r, oscuro)
    if ident == "anquilosaurio":
        bultos = []
        for k in range(8):
            (qx, qy), _ = _en(lomo, 0.04 + 0.92 * k / 7)
            bultos.append(("e", (qx, qy + 3), 11, 8))
        pin.grupo(bultos, SIL_COLOR if sil else (196, 164, 118), 2.4)
        puas = []
        for k in range(0, 8, 2):
            (qx, qy), _ = _en(lomo, 0.04 + 0.92 * k / 7)
            puas.append(("p", [(qx - 6, qy - 3), (qx + 6, qy - 3), (qx + 2, qy - 24)]))
        pin.grupo(puas, marfil, 2.2)

    # ---- patas cercanas
    pin.grupo(patas(False), base)
    if not sil:
        for clave, dedos in (("patas", g["dedos_p"]), ("brazos", g["dedos_b"])):
            for cad in g[clave]:
                tob = cad[2]
                carn = ident in ("tiranosaurio", "velociraptor")
                for d in dedos[:3]:
                    pin.circ((tob[0] + d[0] * 0.8 + 2, tob[1] + d[1] * 0.8), 3.6, (252, 248, 230))
                if carn and clave == "patas":
                    pass

    # ---- cabeza
    cx, cy, tipo, _, ang = g["craneo"]
    z = v["cabeza"]
    cx, cy = cx + dcab[0], cy + dcab[1] + math.sin(t * 2.2) * 0.8
    c = CABEZAS[tipo]
    if ident == "tiranosaurio" or ident == "velociraptor":
        pass
    cuernos = [("p", _rot(h, cx, cy, z, ang)) for h in c["cuernos"]]
    if cuernos:
        pin.grupo(cuernos, marfil, 2.6)
    cab = [("p", _rot(c["mand"], cx, cy, z, ang)), ("p", _rot(c["cr"], cx, cy, z, ang))]
    pin.grupo(cab, base, 3.4)
    if sil:
        return
    # dientes simpaticos
    for x0, x1, yy, n, tam in c["dientes"]:
        if ident in ("tiranosaurio", "velociraptor"):
            n2 = 4
            for i in range(n2):
                xx = x0 + (x1 - x0) * (0.38 + 0.6 * (i + 0.5) / n2)
                w = (x1 - x0) / n2 * 0.18
                pts = _rot([(xx - w, yy - 1), (xx + w, yy - 1), (xx, yy + tam * 0.7)], cx, cy, z, ang)
                pygame.draw.polygon(p, (255, 255, 250), [pin.pt(q) for q in pts])
    # boca sonriente
    (fx, fy), (kx, ky) = c["boca"]
    boca = [(fx - 2, fy), ((fx + kx) / 2, fy + 2), (kx + 4, ky + 1), (kx - 3, ky - 5)]
    pin.linea(_rot(_spline(boca, 5), cx, cy, z, ang), (84, 40, 48), 2.6)
    # mejilla
    mx, my = _rot([(kx + 10, ky + 6)], cx, cy, z, ang)[0]
    pin.circ((mx, my), 5.5 * z, (255, 160, 160) if tipo != "vel" else (255, 170, 190))
    # ojo grande
    ox, oy, rx, ry = c["ojo"]
    ex, ey = _rot([(ox, oy)], cx, cy, z, ang)[0]
    r = max(rx, ry) * z * 1.05 + 2
    if (t % 3.7) < 0.14:
        pin.linea([(ex - r * 0.8, ey + 1), (ex + r * 0.8, ey + 1)], (50, 30, 40), 3)
    else:
        pin.circ((ex, ey), r + 1.6, (50, 30, 40))
        pin.circ((ex, ey), r, (255, 255, 255))
        pin.circ((ex + r * 0.22, ey + r * 0.12), r * 0.58, (40, 28, 46))
        pin.circ((ex + r * 0.34, ey - r * 0.12), r * 0.2, (255, 255, 255))
    nx, ny = _rot([c["nariz"]], cx, cy, z, ang)[0]
    pin.circ((nx, ny), 2.6 * z, (70, 40, 46))


_cache_sil = {}


def dibujar_dino(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    """El dinosaurio vivo (caricatura) de perfil, unos 380x260 px a escala 1."""
    if not silueta:
        _pintar_dino(p, ident, x, y, escala, t, False)
        return
    clave = (ident, round(escala * 20) / 20)
    if clave not in _cache_sil:
        W, H = int(520 * clave[1]), int(380 * clave[1])
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        _pintar_dino(s, ident, W / 2, H / 2, clave[1], 0.0, True)
        _cache_sil[clave] = s
    s = _cache_sil[clave]
    p.blit(s, s.get_rect(center=(int(x), int(y))))
