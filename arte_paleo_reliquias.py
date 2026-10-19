"""Las 30 reliquias de Fosiles: dibujos de ~70 px (con sobremuestreo y cache) y su informacion."""

import math

import pygame

import fosiles_datos as fd
from nucleo import aclarar, oscurecer

SIL = (86, 102, 138)
OUT = (74, 52, 44)
SS = 3
N = 100                          # lienzo logico de 100x100 unidades (el objeto mide ~70)
V2 = pygame.Vector2


def _el_pts(cx, cy, rx, ry, rot=0.0, n=24):
    ca, sa = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * i / n) * ca - ry * math.sin(2 * math.pi * i / n) * sa,
             cy + rx * math.cos(2 * math.pi * i / n) * sa + ry * math.sin(2 * math.pi * i / n) * ca) for i in range(n)]


class Pl:
    """Pincel con coordenadas logicas (origen en el centro) y una rotacion global opcional."""

    def __init__(self):
        self.s = pygame.Surface((N * SS, N * SS), pygame.SRCALPHA)
        self.c = N * SS / 2
        self.giro = 0.0
        self.cx = 0.0
        self.cy = 0.0

    def P(self, q):
        x, y = q
        if self.giro:
            ca, sa = math.cos(self.giro), math.sin(self.giro)
            x, y = x * ca - y * sa, x * sa + y * ca
        return (self.c + (x + self.cx) * SS, self.c + (y + self.cy) * SS)

    def poli(self, pts, col, borde=OUT, w=2.2, cerrado=True):
        P = [self.P(q) for q in pts]
        if len(P) >= 3:
            pygame.draw.polygon(self.s, col, P)
        if borde and w:
            ww = max(1, int(w * SS))
            pygame.draw.lines(self.s, borde, cerrado, P, ww)
            for x, y in P:
                pygame.draw.circle(self.s, borde, (x, y), ww // 2)

    def elipse(self, cx, cy, rx, ry, col, borde=OUT, w=2.2, rot=0.0):
        self.poli(_el_pts(cx, cy, rx, ry, rot), col, borde, w)

    def circ(self, cx, cy, r, col, borde=OUT, w=2.2):
        self.elipse(cx, cy, r, r, col, borde, w)

    def linea(self, pts, col, w=2.0):
        P = [self.P(q) for q in pts]
        ww = max(1, int(w * SS))
        if len(P) > 1:
            pygame.draw.lines(self.s, col, False, P, ww)
        for x, y in P:
            pygame.draw.circle(self.s, col, (x, y), ww // 2)

    def estrella4(self, cx, cy, r, col=(255, 255, 255)):
        pts = []
        for i in range(8):
            a = -math.pi / 2 + i * math.pi / 4
            rr = r if i % 2 == 0 else r * 0.28
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        self.poli(pts, col, None, 0)

    def cono(self, p0, ang, largo, base, curva, col, borde=OUT, w=2.2, punta=0.0, brillo=True, anillos=0):
        n = 16
        x, y = p0
        a = ang
        izq, der = [], []
        paso = largo / n
        centro = []
        for i in range(n + 1):
            s = i / n
            ww = base * (1 - s) ** 0.85 + punta
            nx, ny = -math.sin(a), math.cos(a)
            izq.append((x + nx * ww, y + ny * ww))
            der.append((x - nx * ww, y - ny * ww))
            centro.append((x, y, nx, ny, ww))
            x += math.cos(a) * paso
            y += math.sin(a) * paso
            a += curva / n
        self.poli(izq + der[::-1], col, borde, w)
        if brillo:
            self.linea([(cx_ - nx_ * ww_ * 0.5, cy_ - ny_ * ww_ * 0.5) for cx_, cy_, nx_, ny_, ww_ in centro[2:11]], (255, 255, 255), 2.4)
        if anillos:
            for k in range(1, anillos + 1):
                cx_, cy_, nx_, ny_, ww_ = centro[int(k / (anillos + 1) * n)]
                self.linea([(cx_ + nx_ * ww_, cy_ + ny_ * ww_), (cx_ - nx_ * ww_, cy_ - ny_ * ww_)], oscurecer(col, 0.25), 1.8)
        return (x, y), a


def _ruta(pts, n=10):
    out = []
    for i in range(len(pts) - 1):
        for k in range(n):
            u = k / n
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u))
    out.append(pts[-1])
    return out


def _losa(d, col=(190, 176, 152), w=74, h=60):
    d.poli([(-w / 2 + 6, -h / 2), (w / 2 - 4, -h / 2 + 2), (w / 2, h / 2 - 6), (w / 2 - 8, h / 2), (-w / 2 + 2, h / 2 - 2),
            (-w / 2, -h / 2 + 8)], col)
    d.linea([(-w / 2 + 8, -h / 2 + 3), (w / 2 - 6, -h / 2 + 5)], aclarar(col, 0.4), 2.2)
    for (x, y) in ((-20, 18), (24, -16), (18, 22), (-28, -12)):
        d.circ(x, y, 1.6, oscurecer(col, 0.12), None, 0)


MARFIL = (250, 244, 226)
BRILLO = (255, 255, 255)


# ---------------------------------------------------------------- depredadores
def r_diente_gigante(d):
    d.giro = -0.22
    d.poli([(-13, 8), (-11, 36), (-3, 38), (0, 24), (3, 38), (11, 36), (13, 8)], (200, 170, 124))
    d.poli([(-17, 10), (-13, -12), (-3, -38), (9, -28), (15, -8), (17, 10)], (252, 248, 234))
    for k in range(5):
        y = -26 + 8 * k
        d.poli([(11 + k * 1.2, y), (16 + k * 1.1, y + 3), (12 + k * 1.1, y + 7)], (252, 248, 234), OUT, 1.4)
    d.linea([(-9, 6), (-4, -22)], BRILLO, 3)


def r_garra_curva(d):
    d.circ(-24, 24, 11, (200, 176, 140))
    p, a = d.cono((-26, 22), -0.5, 64, 13, 1.25, (226, 204, 168), anillos=2)
    d.circ(-24, 24, 5, (150, 124, 96), None, 0)


def r_huella_tres_dedos(d):
    _losa(d, (178, 166, 148))
    for ang, ln in ((-0.0, 28), (-0.75, 24), (0.75, 24)):
        x1, y1 = math.sin(ang) * ln, 10 - math.cos(ang) * ln
        nx, ny = math.cos(ang), math.sin(ang)
        d.poli([(-nx * 6, 10 - ny * 6), (nx * 6, 10 + ny * 6), (x1 + nx * 3, y1 + ny * 3), (x1 - nx * 3, y1 - ny * 3)], (116, 104, 90), (84, 72, 62), 1.6)
        d.poli([(x1 - nx * 3, y1 - ny * 3), (x1 + nx * 3, y1 + ny * 3), (x1 + math.sin(ang) * 6, y1 - math.cos(ang) * 6)], (84, 72, 62), None, 0)
    d.elipse(0, 12, 9, 7, (116, 104, 90), (84, 72, 62), 1.6)
    d.linea([(-6, 8), (-14, -4)], (146, 134, 118), 1.6)


def r_huevo_fosil(d):
    d.elipse(0, 32, 30, 7, (160, 150, 134))
    d.elipse(0, 2, 23, 30, (236, 218, 180))
    for (x, y, r) in ((-9, -10, 2.2), (8, -2, 2.6), (-6, 10, 2.0), (10, 14, 2.2), (0, 4, 1.8), (-14, 2, 1.6)):
        d.circ(x, y, r, (190, 160, 118), None, 0)
    d.linea([(-4, -28), (2, -18), (-5, -10), (4, -2), (-3, 8)], (92, 70, 52), 2.6)
    d.linea([(2, -18), (12, -14)], (92, 70, 52), 2.0)
    d.linea([(-12, -14), (-14, -4)], BRILLO, 3)


def r_escama_dura(d):
    hexa = [(32 * math.cos(math.pi / 6 + k * math.pi / 3), 32 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    d.poli(hexa, (150, 168, 122))
    d.poli([(x * 0.7, y * 0.7) for x, y in hexa], (176, 192, 146), (96, 112, 76), 1.6)
    d.poli([(x * 0.4, y * 0.4) for x, y in hexa], (198, 210, 168), (96, 112, 76), 1.4)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        d.linea([(math.cos(a) * 12, math.sin(a) * 12), (math.cos(a) * 30, math.sin(a) * 30)], (96, 112, 76), 1.4)
    d.linea([(-12, -20), (6, -26)], BRILLO, 2.6)


def r_colmillo_afilado(d):
    d.cono((-24, 28), -0.7, 72, 14, 0.7, (254, 250, 238))
    d.estrella4(26, -30, 8, (255, 244, 170))
    d.estrella4(-26, -22, 5, (200, 240, 255))
    d.estrella4(30, 4, 4, (255, 255, 255))


# ---------------------------------------------------------------- mares
def r_amonita(d):
    n = 90
    centro = []
    for i in range(n + 1):
        th = i / n * 2.55 * 2 * math.pi
        r = 2.6 * math.exp(0.155 * th)
        centro.append((r * math.cos(th), r * math.sin(th), r, th))
    for x, y, r, th in centro:
        d.circ(x, y, 0.4 * r + 2.4, (216, 164, 88), (122, 82, 44), 1.4)
    for x, y, r, th in centro[::5][2:]:
        nx, ny = math.cos(th), math.sin(th)
        rr = 0.4 * r + 2.4
        d.linea([(x - nx * rr * 0.85, y - ny * rr * 0.85), (x + nx * rr * 0.85, y + ny * rr * 0.85)], (150, 104, 54), 1.6)
    d.circ(centro[0][0], centro[0][1], 3, (240, 204, 140), (122, 82, 44), 1.2)


def r_trilobite(d):
    d.elipse(0, 4, 20, 34, (150, 146, 124))
    d.poli([(-24, -12), (-20, -30), (0, -38), (20, -30), (24, -12), (12, -6), (-12, -6)], (172, 168, 142))
    d.poli([(-24, -12), (-34, -4), (-26, -4)], (172, 168, 142), OUT, 1.6)
    d.poli([(24, -12), (34, -4), (26, -4)], (172, 168, 142), OUT, 1.6)
    for k in range(6):
        y = -2 + k * 6.4
        w = 20 - k * 1.6
        d.poli([(-w, y), (w, y), (w - 1, y + 6), (-w + 1, y + 6)], (160, 156, 130) if k % 2 else (184, 180, 152), OUT, 1.4)
    d.poli([(-12, 36), (12, 36), (6, 42), (-6, 42)][:4], (172, 168, 142), OUT, 1.4)
    d.elipse(0, 30, 12, 8, (172, 168, 142), OUT, 1.6)
    d.linea([(0, -30), (0, 26)], (126, 122, 100), 2.0)
    d.circ(-11, -18, 3.4, (60, 56, 48), (40, 36, 30), 1)
    d.circ(11, -18, 3.4, (60, 56, 48), (40, 36, 30), 1)
    d.circ(-12, -19, 1.2, BRILLO, None, 0)
    d.circ(10, -19, 1.2, BRILLO, None, 0)


def r_concha_espiral(d):
    d.giro = 0.18
    for k in range(7):
        t = k / 6
        cy = -34 + t * 52
        r = 5 + t * 21
        d.elipse(0, cy, r, r * 0.62, (240, 216, 196) if k % 2 == 0 else (230, 196, 176), (140, 96, 76), 1.8)
        d.linea([(-r * 0.7, cy - r * 0.2), (r * 0.7, cy + r * 0.1)], (186, 140, 112), 1.4)
    d.elipse(0, 22, 21, 12, (250, 228, 218), (140, 96, 76), 1.8)
    d.elipse(0, 22, 12, 6.5, (176, 120, 108), (120, 80, 66), 1.2)
    d.linea([(-20, 12), (-8, 8)], BRILLO, 2.4)


def r_diente_megalodon(d):
    d.poli([(-32, 20), (-26, 40), (0, 30), (26, 40), (32, 20)], (190, 174, 144))
    izq, der = [], []
    for k in range(15):
        t = k / 14
        x = (34 * (1 - t) + 0 * t) * (1 + 0.1 * math.sin(math.pi * t))
        y = 24 * (1 - t) + (-40) * t
        z = 1.3 if k % 2 else 0.0
        izq.append((-x - z, y))
        der.append((x + z, y))
    d.poli(izq + der[::-1], (246, 242, 232))
    d.linea([(-20, 16), (-6, -22)], BRILLO, 3)


def r_aleta_fosil(d):
    _losa(d, (186, 172, 150))
    base = (-18, 18)
    pts = [base]
    for k in range(7):
        a = -2.6 + k * 0.34
        pts.append((base[0] + 44 * math.cos(a) * 1.0, base[1] + 44 * math.sin(a)))
    d.poli(pts, (150, 134, 112), (110, 94, 76), 1.8)
    for k in range(1, 8):
        d.linea([base, pts[k]], (116, 100, 82), 1.4)


def r_perla_antigua(d):
    pts = [(-34, 10), (-30, -8), (-18, -22), (0, -26), (18, -22), (30, -8), (34, 10), (22, 26), (0, 30), (-22, 26)]
    d.poli(pts, (206, 186, 200))
    for k in range(-3, 4):
        d.linea([(0, 28), (k * 9, -22 + abs(k) * 3)], (160, 134, 156), 1.6)
    d.poli([(-30, 12), (0, 6), (30, 12), (22, 24), (0, 28), (-22, 24)], (236, 224, 238), OUT, 1.8)
    d.circ(0, -2, 14, (240, 234, 252), (140, 120, 170), 2.0)
    d.circ(3, 2, 9, (222, 214, 244), None, 0)
    d.circ(-4, -8, 4.5, BRILLO, None, 0)
    d.estrella4(22, -22, 7, (255, 255, 255))
    d.estrella4(-28, -18, 4, (255, 240, 255))


# ---------------------------------------------------------------- cielos
def r_pluma_fosil(d):
    _losa(d, (206, 190, 160))
    d.giro = -0.5
    d.poli(_el_pts(0, 0, 11, 34, 0, 20), (150, 124, 98), (100, 78, 60), 1.4)
    for k in range(-5, 6):
        y = k * 5.6
        w = 11 * math.sqrt(max(0, 1 - (y / 34) ** 2))
        d.linea([(0, y), (-w, y - 5)], (100, 78, 60), 1.3)
        d.linea([(0, y), (w, y - 5)], (100, 78, 60), 1.3)
    d.linea([(0, -34), (0, 40)], (80, 62, 48), 2.2)


def r_helecho_fosil(d):
    _losa(d, (200, 184, 154))
    col = (120, 100, 74)
    st = [(-18, 26), (-8, 6), (6, -14), (22, -30)]
    d.linea(st, (96, 78, 58), 2.6)
    for k in range(9):
        u = k / 8
        x = -18 + (22 + 18) * u
        y = 26 + (-30 - 26) * u * (0.9 + 0.1 * u)
        L = 17 * (1 - 0.8 * u) + 3
        d.elipse(x - L * 0.55, y - L * 0.45, L * 0.55, 2.8, col, (96, 78, 58), 0.8, rot=-0.7)
        d.elipse(x + L * 0.55, y + L * 0.1, L * 0.55, 2.8, col, (96, 78, 58), 0.8, rot=0.45)


def r_hueso_hueco(d):
    d.giro = -0.5
    d.linea([(-34, 0), (34, 0)], (240, 232, 208), 11)
    d.linea([(-34, -2), (34, -2)], BRILLO, 2.4)
    d.linea([(-34, 4), (34, 4)], (214, 200, 168), 2.0)
    d.circ(-36, -6, 7, (240, 232, 208), OUT, 1.8)
    d.circ(-36, 6, 7, (240, 232, 208), OUT, 1.8)
    d.elipse(36, 0, 8, 10, (240, 232, 208), OUT, 2.0)
    d.elipse(37, 0, 4.4, 6.2, (86, 62, 50), (60, 40, 34), 1.2)


def r_ala_membrana(d):
    _losa(d, (176, 162, 138))
    d.poli([(-24, 22), (-10, -20), (24, -26), (30, -6), (18, 4), (10, 12), (0, 20)], (206, 186, 150), (120, 100, 74), 1.6)
    d.linea([(-24, 22), (-12, -6), (6, -24), (28, -30)], (240, 230, 206), 4.0)
    for q in ((-12, -6), (6, -24)):
        d.circ(q[0], q[1], 3, (240, 230, 206), OUT, 1.2)
    d.linea([(-12, -6), (22, 4)], (140, 116, 84), 1.4)
    d.linea([(6, -24), (16, 4)], (140, 116, 84), 1.4)


def r_nido_antiguo(d):
    for (x, y) in ((-12, -4), (10, -6), (0, 6)):
        d.elipse(x, y, 11, 14, (244, 232, 202), OUT, 1.8)
        d.linea([(x - 5, y - 6), (x - 3, y - 11)], BRILLO, 2.2)
    d.poli(_el_pts(0, 14, 36, 17, 0, 24), (150, 108, 68), (92, 62, 40), 2.0)
    for k in range(10):
        a = -2.6 + k * 0.5
        d.linea([(36 * math.cos(a), 14 + 17 * math.sin(a)), (24 * math.cos(a + 1.0), 14 + 10 * math.sin(a + 1.0))], (196, 150, 98), 1.8)
    d.linea([(-34, 12), (-10, 24), (14, 28), (34, 14)], (196, 150, 98), 2.4)
    d.linea([(-30, 20), (0, 30), (30, 22)], (110, 76, 46), 2.2)


def r_ambar_insecto(d):
    d.poli(_el_pts(0, 2, 34, 28, 0.2, 28), (250, 176, 40), (160, 90, 20), 2.4)
    d.poli(_el_pts(-3, -2, 26, 20, 0.2, 28), (255, 204, 76), None, 0)
    d.elipse(2, 4, 8, 4.6, (60, 42, 28), (40, 28, 18), 1.0, rot=0.3)
    d.circ(11, 1, 3.4, (60, 42, 28), (40, 28, 18), 1.0)
    d.elipse(-2, -6, 11, 4, (255, 244, 214), (150, 110, 60), 1.0, rot=-0.6)
    d.elipse(4, -8, 10, 3.6, (255, 244, 214), (150, 110, 60), 1.0, rot=-1.1)
    for dx in (-4, 1, 6):
        d.linea([(dx, 8), (dx - 3, 15)], (60, 42, 28), 1.4)
    d.linea([(-6, 6), (-16, 10)], (60, 42, 28), 1.2)
    d.estrella4(-22, -16, 7, (255, 250, 220))
    d.estrella4(24, -10, 4, (255, 255, 255))


# ---------------------------------------------------------------- herbivoros
def r_hoja_gigante(d):
    d.giro = 0.5
    d.linea([(0, 38), (0, 26)], (90, 100, 60), 3.4)
    pts = [(0, 28)]
    n = 10
    for k in range(n + 1):
        y = 24 - 56 * k / n
        w = 28 * math.sin(math.pi * (k / n) ** 0.8) + 2
        pts.append((w + (3 if k % 2 else 0), y))
    for k in range(n, -1, -1):
        y = 24 - 56 * k / n
        w = 28 * math.sin(math.pi * (k / n) ** 0.8) + 2
        pts.append((-w - (3 if k % 2 else 0), y))
    d.poli(pts, (140, 170, 100), (84, 106, 56), 2.0)
    d.linea([(0, 28), (0, -32)], (96, 124, 66), 2.4)
    for k in range(1, 8):
        y = 24 - k * 7
        w = 22 * math.sin(math.pi * (k / 8) ** 0.8)
        d.linea([(0, y), (w, y - 6)], (108, 138, 76), 1.4)
        d.linea([(0, y), (-w, y - 6)], (108, 138, 76), 1.4)


def r_diente_plano(d):
    for dx in (-13, 13):
        d.poli([(dx - 8, 12), (dx - 5, 42), (dx + 5, 42), (dx + 8, 12)], (186, 166, 130))
    d.poli([(-26, -12), (-20, -26), (20, -26), (26, -12), (28, 16), (-28, 16)], (248, 242, 224))
    for x in (-12, 0, 12):
        d.linea([(x, -22), (x - 2, 10)], (196, 182, 150), 2.6)
    d.linea([(-22, -18), (20, -18)], BRILLO, 3)


def r_semilla_antigua(d):
    d.giro = 0.3
    d.poli(_el_pts(0, 0, 25, 33, 0, 26), (180, 130, 84), (104, 70, 40), 2.2)
    for fila in range(6):
        for col in range(4):
            x = (col - 1.5) * 11 + (5.5 if fila % 2 else 0)
            y = -26 + fila * 10.5
            if (x / 24) ** 2 + (y / 32) ** 2 < 0.82:
                d.poli([(x, y - 6), (x + 5.6, y), (x, y + 6), (x - 5.6, y)], (206, 156, 100), (116, 78, 46), 1.2)
    d.linea([(0, -33), (3, -42)], (104, 70, 40), 3)
    d.linea([(-14, -16), (-8, -24)], BRILLO, 2.2)


def r_cuerno_roto(d):
    d.cono((-28, 24), -0.95, 84, 17, 0.95, (230, 218, 192), anillos=3)
    d.poli([(-42, 22), (-34, 12), (-31, 20), (-23, 10), (-18, 22), (-22, 36), (-40, 36)], (214, 200, 170))
    d.elipse(-30, 26, 8, 9, (150, 126, 96), OUT, 1.6)


def r_tronco_petrificado(d):
    d.elipse(0, 8, 34, 26, (110, 78, 52))
    d.elipse(0, 2, 34, 26, (120, 84, 56))
    cols = [(226, 188, 140), (200, 140, 110), (168, 200, 196), (240, 220, 170), (206, 156, 126), (156, 190, 190)]
    for k, c in enumerate(cols):
        f = 0.9 - k * 0.15
        d.elipse(0, 2, 34 * f, 26 * f, c, (110, 78, 52), 1.2)
    d.circ(0, 2, 3, (96, 66, 44), None, 0)
    d.linea([(0, 2), (26, -8)], (96, 66, 44), 1.4)
    d.linea([(0, 2), (-20, 16)], (96, 66, 44), 1.4)
    d.linea([(-22, -12), (-8, -20)], BRILLO, 2.4)


def r_piedra_pulida(d):
    d.poli(_el_pts(0, 2, 30, 24, 0.15, 26), (72, 168, 160), (30, 90, 90), 2.4)
    d.poli([(-26, 0), (-8, -18), (14, -18), (4, 0)], (118, 204, 194), None, 0)
    d.poli([(4, 0), (14, -18), (28, -4), (22, 12)], (60, 144, 150), None, 0)
    d.poli([(-26, 0), (4, 0), (22, 12), (-4, 24), (-18, 14)], (88, 182, 172), None, 0)
    d.linea([(-18, -10), (-6, -16)], BRILLO, 3)
    d.estrella4(22, -18, 8, (255, 255, 255))
    d.estrella4(-24, 14, 4, (210, 255, 250))


# ---------------------------------------------------------------- hielo
def r_colmillo_mamut(d):
    d.cono((-30, 26), -0.85, 84, 14, 1.75, (250, 240, 216), anillos=3)
    d.elipse(-30, 26, 8, 12, (214, 196, 160), OUT, 1.8, rot=0.7)


def r_mechon_lana(d):
    cols = [(176, 120, 76), (150, 98, 60), (198, 140, 90), (130, 84, 52), (184, 128, 82), (160, 106, 66), (204, 148, 96)]
    angs = (-0.95, -0.62, -0.3, 0.0, 0.3, 0.62, 0.95)
    hebras = []
    for k, ang in enumerate(angs):
        pts = []
        for s in range(0, 9):
            u = s / 8
            pts.append((math.sin(ang) * 50 * u + 5 * math.sin(u * 7 + k * 1.3) * u, 24 - math.cos(ang * 0.9) * 58 * u))
        hebras.append(pts)
    for pts in hebras:
        d.linea(pts, OUT, 8.6)
    for k, pts in enumerate(hebras):
        d.linea(pts, cols[k], 6.0)
    for k, pts in enumerate(hebras):
        d.linea(pts[1:6], aclarar(cols[k], 0.3), 1.6)
    d.poli([(-11, 18), (11, 18), (10, 28), (-10, 28)], (160, 56, 56), OUT, 1.8)
    d.linea([(-10, 22), (10, 22)], (210, 110, 100), 1.6)


def r_cristal_hielo(d):
    def prisma(cx, cy, w, h, ang, col, claro):
        d.giro = ang
        d.cx, d.cy = cx, cy
        d.poli([(-w, h * 0.5), (-w * 1.05, -h * 0.25), (0, -h * 0.62), (w * 1.05, -h * 0.25), (w, h * 0.5)], col, (60, 100, 150), 2.0)
        d.poli([(-w * 0.2, h * 0.5), (-w * 0.25, -h * 0.28), (0, -h * 0.6), (w * 0.3, -h * 0.28), (w * 0.2, h * 0.5)], claro, None, 0)
        d.linea([(-w * 0.2, h * 0.5), (-w * 0.25, -h * 0.28), (0, -h * 0.62)], (110, 160, 210), 1.4)
        d.linea([(-w * 0.7, h * 0.3), (-w * 0.78, -h * 0.2)], BRILLO, 2.2)
        d.giro = 0.0
        d.cx = d.cy = 0.0
    prisma(-20, 14, 9, 40, -0.4, (170, 214, 244), (210, 236, 252))
    prisma(21, 14, 9, 36, 0.45, (160, 206, 240), (204, 232, 250))
    prisma(0, 6, 13, 64, 0.0, (186, 226, 250), (226, 244, 254))
    d.estrella4(16, -30, 6, (255, 255, 255))
    d.estrella4(-26, -10, 4, (230, 250, 255))


def r_punta_de_piedra(d):
    d.giro = 0.1
    d.poli([(0, -40), (13, -22), (26, 8), (9, 6), (6, 32), (-6, 32), (-9, 6), (-26, 8), (-13, -22)], (176, 164, 146), (92, 80, 68), 2.2)
    d.poli([(0, -34), (10, -18), (20, 4), (8, 4), (0, -4)], (200, 190, 172), None, 0)
    d.linea([(0, -36), (0, 30)], (130, 118, 104), 1.6)
    for k in range(4):
        y = -22 + k * 11
        d.linea([(0, y), (-10 - k, y + 6)], (126, 114, 100), 1.4)
        d.linea([(0, y), (10 + k, y + 6)], (126, 114, 100), 1.4)
    d.linea([(-10, -18), (-2, -34)], BRILLO, 2.2)


def r_hueso_tallado(d):
    d.giro = -0.55
    d.linea([(-30, 0), (30, 0)], (242, 232, 206), 13)
    d.linea([(-30, -3), (30, -3)], BRILLO, 2.4)
    for sx in (-1, 1):
        d.circ(sx * 34, -7, 8, (242, 232, 206), OUT, 1.8)
        d.circ(sx * 34, 7, 8, (242, 232, 206), OUT, 1.8)
    d.linea([(-22, 3), (-14, -3), (-6, 3), (2, -3), (10, 3), (18, -3), (24, 3)], (110, 76, 52), 1.8)
    for x in (-22, -8, 6, 20):
        d.circ(x, -7.5, 1.4, (110, 76, 52), None, 0)
    d.circ(8, 6, 1.4, (110, 76, 52), None, 0)


def r_ambar_gota(d):
    pts = [(0, -40), (8, -24), (22, -6), (28, 10), (22, 26), (0, 34), (-22, 26), (-28, 10), (-22, -6), (-8, -24)]
    d.poli(pts, (250, 170, 40), (160, 92, 20), 2.4)
    d.poli([(0, -32), (6, -20), (17, -4), (21, 10), (13, 22), (-4, 26), (-18, 16), (-20, 4), (-12, -8)], (255, 206, 84), None, 0)
    d.elipse(0, 6, 5, 9, (90, 110, 44), (62, 76, 30), 1.2, rot=0.3)
    d.linea([(0, 14), (0, -3)], (62, 76, 30), 1.2)
    d.estrella4(-14, -14, 8, (255, 250, 220))
    d.estrella4(18, 20, 4, (255, 255, 255))
    d.linea([(-16, 8), (-14, -4)], BRILLO, 2.4)


DIBUJOS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith("r_") and callable(v)}

_BASE = {}
_ESC = {}
_SIL = {}


def _base(rid):
    if rid not in _BASE:
        d = Pl()
        DIBUJOS[rid](d)
        _BASE[rid] = d.s
    return _BASE[rid]


def _escalada(rid, esc, sil):
    q = max(1, round(esc * 30))
    k = (rid, q, sil)
    if k not in _ESC:
        s = _base(rid)
        if sil:
            m = pygame.mask.from_surface(s, 10)
            s = m.to_surface(setcolor=SIL + (255,), unsetcolor=(0, 0, 0, 0))
        w = max(2, int(N * q / 30))
        _ESC[k] = pygame.transform.smoothscale(s, (w, w))
    return _ESC[k]


def dibujar_reliquia(p, ident, x, y, escala=1.0, silueta=False):
    """La reliquia centrada en (x, y); mide unos 70 px a escala 1."""
    s = _escalada(ident, escala, bool(silueta))
    p.blit(s, s.get_rect(center=(int(x), int(y))))


RELIQUIAS_INFO = {
    "diente_gigante": ("Diente gigante", "Los cazadores tenían dientes con borde de sierra, como un cuchillo."),
    "garra_curva": ("Garra curva", "Las garras eran de queratina, igual que tus uñas."),
    "huella_tres_dedos": ("Huella de tres dedos", "Las huellas fósiles cuentan cómo caminaba un dinosaurio."),
    "huevo_fosil": ("Huevo fósil", "Los dinosaurios ponían huevos, como hacen las aves."),
    "escama_dura": ("Escama dura", "Algunos dinosaurios tenían placas de hueso en la piel, como un escudo."),
    "colmillo_afilado": ("Colmillo afilado", "Los dinosaurios cazadores cambiaban los dientes caídos por otros nuevos."),
    "amonita": ("Amonita", "Era un animal marino con concha en espiral, pariente de los calamares."),
    "trilobite": ("Trilobite", "Vivió en el mar mucho antes que los dinosaurios."),
    "concha_espiral": ("Concha espiral", "Es la casita de un caracol de mar de hace millones de años."),
    "diente_megalodon": ("Diente de megalodón", "Estos dientes de tiburón gigante medían hasta 18 centímetros."),
    "aleta_fosil": ("Aleta fósil", "La marca de una aleta quedó en el barro y el barro se hizo piedra."),
    "perla_antigua": ("Perla antigua", "Las perlas se forman dentro de una concha, capa tras capa."),
    "pluma_fosil": ("Pluma fósil", "Muchos dinosaurios tenían plumas. Las aves vienen de ellos."),
    "helecho_fosil": ("Helecho fósil", "Los helechos ya existían cuando vivían los dinosaurios."),
    "hueso_hueco": ("Hueso hueco", "Los pterosaurios tenían huesos huecos y livianos para volar."),
    "ala_membrana": ("Ala de pterosaurio", "Su ala era de piel estirada desde un dedo larguísimo."),
    "nido_antiguo": ("Nido antiguo", "Algunos dinosaurios cuidaban sus huevos en nidos."),
    "ambar_insecto": ("Ámbar con insecto", "El ámbar es resina de árbol endurecida y a veces guarda insectos."),
    "hoja_gigante": ("Hoja gigante", "Los dinosaurios herbívoros comían hojas, helechos y ramas."),
    "diente_plano": ("Diente plano", "Los dientes planos servían para moler plantas."),
    "semilla_antigua": ("Semilla antigua", "Las cícadas y los pinos ya daban semillas en esa época."),
    "cuerno_roto": ("Cuerno roto", "El Triceratops usaba sus tres cuernos para defenderse."),
    "tronco_petrificado": ("Tronco petrificado", "Con los años, los minerales convirtieron la madera en piedra."),
    "piedra_pulida": ("Piedra pulida", "Algunos dinosaurios tragaban piedras lisas para digerir las plantas."),
    "colmillo_mamut": ("Colmillo de mamut", "Los colmillos del mamut podían medir más de 3 metros."),
    "mechon_lana": ("Mechón de lana", "Los mamuts tenían pelo largo y lanudo para el frío."),
    "cristal_hielo": ("Cristal de hielo", "En la Era de Hielo, mucho hielo cubrió gran parte de la Tierra."),
    "punta_de_piedra": ("Punta de piedra", "Los primeros humanos tallaban piedra para hacer puntas de lanza."),
    "hueso_tallado": ("Hueso tallado", "Hace miles de años se hacían adornos y herramientas con huesos."),
    "ambar_gota": ("Ámbar", "El ámbar brilla como miel, pero es resina muy antigua."),
}

assert set(DIBUJOS) >= set(fd.RELIQUIAS), set(fd.RELIQUIAS) - set(DIBUJOS)
assert set(RELIQUIAS_INFO) == set(fd.RELIQUIAS)
