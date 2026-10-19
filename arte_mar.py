"""Arte marino de Ninja Mundo: animales, barcos, iconos de pista, fondos (por zona y por mundo), herramientas y
materiales de pesca.

Todo se dibuja con codigo. Los animales se dibujan en un marco nominal (cabeza hacia +x, y hacia abajo)
y `dibujar_animal` los escala; cada forma conoce su largo nominal (FORMAS) y las "partes" que se
pueden dejar asomar en el juego de pesca (ventanas en el mismo marco nominal).
"""

import math
import random
import zlib

import pygame

from nucleo import aclarar, oscurecer, estrella

WY = 250                                     # y de la superficie del agua en el juego de pesca
ANCHO, ALTO = 1280, 720

GRADO_COLOR = {1: (90, 205, 100), 2: (245, 210, 60), 3: (245, 145, 45), 4: (235, 65, 65), 5: (165, 90, 225)}
GRADO_NOMBRE = {1: "Muy fácil", 2: "Fácil", 3: "Medio", 4: "Difícil", 5: "Muy difícil"}
SIL = (60, 62, 80)
SIL_B = (45, 45, 70)

# forma: (largo nominal en unidades, [(nombre de la parte, (cx, cy, ancho, alto)), ...])
FORMAS = {
    "oval":   (114, [("aleta", (2, -34, 46, 30)), ("cola", (-54, 0, 40, 52)), ("cuerpo", (8, 2, 46, 54))]),
    "larga":  (130, [("aleta", (2, -29, 46, 28)), ("cola", (-62, 0, 42, 52)), ("cuerpo", (10, 2, 48, 44))]),
    "globo":  (102, [("aleta", (0, -40, 52, 30)), ("cola", (-52, 0, 38, 46)), ("cuerpo", (6, 2, 48, 52))]),
    "luna":   (108, [("aleta", (-2, -46, 44, 30)), ("cola", (-46, 0, 34, 56)), ("cuerpo", (6, 4, 50, 56))]),
    "pulpo":  (96, [("cabeza", (0, -22, 64, 44)), ("brazos", (0, 40, 74, 40)), ("cuerpo", (0, 4, 56, 56))]),
    "caballito": (46, [("cabeza", (18, -38, 40, 36)), ("cola", (10, 30, 40, 40)), ("cuerpo", (0, -4, 40, 44))]),
    "raya":   (150, [("ala", (-8, -30, 62, 36)), ("cola", (-62, 4, 44, 36)), ("cuerpo", (6, 2, 54, 56))]),
    "espada": (146, [("aleta", (-4, -34, 46, 30)), ("espada", (60, -2, 44, 26)), ("cola", (-60, 0, 40, 52)), ("cuerpo", (8, 2, 46, 40))]),
    "lintera": (110, [("farol", (30, -48, 40, 36)), ("dientes", (36, 6, 38, 40)), ("cuerpo", (-8, 2, 50, 56))]),
    "anguila": (160, [("cola", (-60, 0, 44, 40)), ("cuerpo", (0, 0, 50, 36)), ("cabeza", (62, 0, 40, 36))]),
    "tiburon": (150, [("aleta", (0, -36, 46, 34)), ("cola", (-70, 0, 46, 60)), ("cuerpo", (10, 2, 52, 44))]),
    "ballena": (160, [("lomo", (4, -26, 56, 30)), ("cola", (-70, -10, 44, 62)), ("cuerpo", (14, 4, 56, 52))]),
    "pulpogig": (140, [("cabeza", (4, -34, 64, 44)), ("brazos", (-4, 36, 80, 42)), ("cuerpo", (0, 0, 58, 54))]),
    "medusa": (96, [("sombrero", (0, -22, 62, 34)), ("tentaculos", (0, 34, 62, 40)), ("cuerpo", (0, 6, 56, 54))]),
}


class _Pincel:
    """Dibuja en coordenadas nominales (cabeza hacia +x) con escala s y direccion m (+1/-1)."""

    def __init__(self, p, cx, cy, s, m, sil):
        self.p, self.cx, self.cy, self.s, self.m, self.sil = p, cx, cy, s, m, sil
        self.bd = SIL_B

    def X(self, x):
        return self.cx + self.m * x * self.s

    def Y(self, y):
        return self.cy + y * self.s

    def pt(self, x, y):
        return (self.X(x), self.Y(y))

    def c(self, color):
        return SIL if self.sil else color

    def borde(self, color):
        return SIL_B if self.sil else oscurecer(color, 0.55)

    def pol(self, pts, col, borde=True, w=3):
        q = [self.pt(a, b) for a, b in pts]
        pygame.draw.polygon(self.p, self.c(col), q)
        if borde:
            pygame.draw.polygon(self.p, self.borde(col), q, max(1, int(w * self.s)))

    def el(self, x, y, w, h, col, borde=True, w_b=3):
        r = pygame.Rect(0, 0, max(2, int(w * self.s)), max(2, int(h * self.s)))
        r.center = (int(self.X(x)), int(self.Y(y)))
        pygame.draw.ellipse(self.p, self.c(col), r)
        if borde:
            pygame.draw.ellipse(self.p, self.borde(col), r, max(1, int(w_b * self.s)))

    def circ(self, x, y, r, col, borde=True, w_b=3):
        rr = max(1, int(r * self.s))
        pygame.draw.circle(self.p, self.c(col), (int(self.X(x)), int(self.Y(y))), rr)
        if borde:
            pygame.draw.circle(self.p, self.borde(col), (int(self.X(x)), int(self.Y(y))), rr, max(1, int(w_b * self.s)))

    def lin(self, a, b, col, w=3):
        pygame.draw.line(self.p, self.c(col), self.pt(*a), self.pt(*b), max(1, int(w * self.s)))

    def lineas(self, pts, col, w=3):
        pygame.draw.lines(self.p, self.c(col), False, [self.pt(a, b) for a, b in pts], max(1, int(w * self.s)))

    def ojo(self, x, y, r=7):
        if self.sil:
            return
        self.circ(x, y, r, (255, 255, 255), borde=False)
        self.circ(x + 1.2, y + 0.8, r * 0.55, (40, 30, 50), borde=False)
        self.circ(x + 0.4, y - 1.6, r * 0.2, (255, 255, 255), borde=False)


# ----------------------------------------------------------------------------- peces clasicos
def _clasico(P, ident, col, col2, t, largo, alto, cola_grande=False):
    mov = math.sin(t * 9) * 8
    k = 1.25 if cola_grande else 1.0
    P.pol([(-largo + 6, 0), (-largo - 26 * k, -22 * k + mov), (-largo - 26 * k, 22 * k + mov)], col)
    P.pol([(-10, -alto + 4), (18, -alto + 4), (6, -alto - 18)], col)
    P.pol([(-6, alto - 4), (14, alto - 4), (0, alto + 12)], col)
    P.el(0, 0, largo * 2, alto * 2, col, borde=False)
    if not P.sil:
        if ident == "atun":
            P.el(0, alto * 0.18, largo * 1.9, alto * 1.15, col2, borde=False)
            for dx in (-40, -32, -24):                     # pinnulas amarillas
                P.pol([(dx, -alto + 2), (dx - 6, -alto - 8), (dx - 10, -alto + 4)], (250, 215, 70), w=2)
            P.lin((-largo + 8, -2), (largo * 0.7, -2), (150, 190, 250), 3)
        elif ident == "payaso":
            P.el(0, alto * 0.18, largo * 1.5, alto * 0.7, col2, borde=False)
            for dx in (-14, 14):
                P.pol([(dx - 5, -alto * 0.9), (dx + 5, -alto * 0.9), (dx + 5, alto * 0.9), (dx - 5, alto * 0.9)],
                      (255, 255, 255), borde=False)
        elif ident == "perca":
            P.el(0, alto * 0.2, largo * 1.6, alto * 0.8, col2, borde=False)
            for dx in (-24, -4, 16):
                P.lineas([(dx, -alto * 0.8), (dx + 3, 0), (dx, alto * 0.8)], oscurecer(col, 0.45), 6)
            P.pol([(-8, alto - 4), (16, alto - 4), (0, alto + 16)], (240, 120, 60))
        elif ident == "trucha":
            P.el(0, alto * 0.2, largo * 1.6, alto * 0.8, col2, borde=False)
            for (dx, dy) in ((-22, -10), (-6, -14), (10, -8), (-14, -2), (2, -4), (20, 0)):
                P.circ(dx, dy, 3.2, oscurecer(col, 0.5), borde=False)
        elif ident == "dorado":
            P.el(0, alto * 0.2, largo * 1.6, alto * 0.8, col2, borde=False)
            for dx in range(-28, 24, 12):
                for dy in (-12, 0, 12):
                    P.lineas([(dx, dy - 4), (dx + 5, dy), (dx, dy + 4)], aclarar(col, 0.4), 2)
        elif ident == "sardina":
            P.el(0, alto * 0.25, largo * 1.7, alto * 0.9, col2, borde=False)
            P.lin((-largo + 10, -3), (largo * 0.7, -3), (110, 150, 200), 4)
            for dx in (-10, 10, 28):
                P.circ(dx, -9, 2.4, (90, 120, 170), borde=False)
        elif ident in ("pezluna",):
            pass
        else:
            P.el(0, alto * 0.2, largo * 1.6, alto * 0.8, col2, borde=False)
    # borde del cuerpo
    r = pygame.Rect(0, 0, int(largo * 2 * P.s), int(alto * 2 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.ojo(largo * 0.58, -alto * 0.2, 7.5)
    if not P.sil:
        pygame.draw.arc(P.p, (60, 30, 50), pygame.Rect(min(P.X(largo * 0.55), P.X(largo * 0.95)), P.Y(2),
                                                      abs(P.X(largo * 0.95) - P.X(largo * 0.55)), 12 * P.s),
                        math.pi * 1.1, math.pi * 1.9, max(1, int(2 * P.s)))


def _globo(P, col, col2, t):
    largo = alto = 38
    mov = math.sin(t * 9) * 5
    P.pol([(-largo + 6, 0), (-largo - 22, -16 + mov), (-largo - 22, 16 + mov)], col)
    P.el(0, 0, largo * 2, alto * 2, col, borde=False)
    if not P.sil:
        P.el(0, 8, largo * 1.5, alto * 0.9, col2, borde=False)
        for dx in range(-26, 30, 13):
            P.pol([(dx - 5, -alto + 3), (dx, -alto - 11), (dx + 5, -alto + 3)], oscurecer(col, 0.45), w=2)
            P.pol([(dx - 5, alto - 3), (dx, alto + 9), (dx + 5, alto - 3)], oscurecer(col, 0.45), w=2)
        P.pol([(-4, 6), (14, 14 + math.sin(t * 12) * 3), (2, 20)], col)
    r = pygame.Rect(0, 0, int(largo * 2 * P.s), int(alto * 2 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.ojo(largo * 0.5, -alto * 0.22, 8)
    if not P.sil:
        P.circ(largo * 0.86, alto * 0.18, 4, (240, 150, 150), borde=False)


def _luna(P, col, col2, t):
    mov = math.sin(t * 7) * 4
    P.pol([(-34, -26), (-52, -30 + mov), (-52, 30 + mov), (-34, 26)], col)
    P.pol([(-18, -32), (6, -34), (-6, -62 + mov * 0.5)], col)
    P.pol([(-18, 32), (6, 34), (-6, 62 + mov * 0.5)], col)
    P.el(4, 0, 84, 76, col, borde=False)
    if not P.sil:
        P.el(8, 8, 62, 46, col2, borde=False)
        for dy in (-18, -6, 6):
            P.lineas([(-20, dy), (-6, dy + 3), (8, dy)], aclarar(col, 0.4), 2)
    r = pygame.Rect(0, 0, int(84 * P.s), int(76 * P.s))
    r.center = (int(P.X(4)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.ojo(26, -10, 7.5)
    if not P.sil:
        P.el(42, 8, 8, 10, (60, 30, 50), borde=False)


def _pulpo(P, col, col2, t):
    for i in range(-3, 4):
        pts = []
        for j in range(7):
            u = j / 6
            pts.append((i * 9 + math.sin(t * 5 + i + u * 4) * 6 * u, 8 + 40 * u))
        P.lineas(pts, col, 9 - 0)
        if not P.sil:
            P.lineas(pts, aclarar(col, 0.15), 6)
    P.el(0, -12, 74, 70, col)
    if not P.sil:
        P.el(-12, -26, 20, 14, aclarar(col, 0.35), borde=False)
        P.ojo(-15, -8, 9)
        P.ojo(15, -8, 9)
        pygame.draw.arc(P.p, (60, 30, 50), pygame.Rect(P.X(-8), P.Y(4), 16 * P.s, 10 * P.s),
                        math.pi * 1.1, math.pi * 1.9, max(1, int(2 * P.s)))


# ----------------------------------------------------------------------------- formas nuevas
def _caballito(P, col, col2, t):
    sway = math.sin(t * 4) * 2
    ruta = [(8, -26, 14), (0, -10, 17), (-3, 8, 16), (2, 24, 12), (12, 34, 9), (22, 32, 7), (24, 22, 5.5), (18, 18, 4)]
    P.pol([(-10, -12), (-24, -8 + sway), (-22, 6 + sway), (-8, 6)], aclarar(col, 0.25), w=2)
    for x, y, r in ruta:
        P.circ(x, y, r + 2.5, oscurecer(col, 0.55), borde=False)
    for x, y, r in ruta:
        P.circ(x, y, r, col, borde=False)
    P.el(10, -40, 30, 26, col)
    P.lin((20, -42), (42, -40), oscurecer(col, 0.35), 9)
    P.lin((20, -42), (42, -40), col, 6)
    if not P.sil:
        for i in range(4):
            P.lin((-6 + i * 1.5, -22 + i * 11), (10 + i * 0.5, -22 + i * 11), col2, 3)
        for dx in (-6, 6, 18):
            P.pol([(dx - 4, -50), (dx, -62), (dx + 4, -50)], aclarar(col, 0.3), w=2)
        P.ojo(16, -44, 5.5)
    return


def _raya(P, col, col2, t):
    f = math.sin(t * 3) * 5
    ala = [(50, 0), (24, -38 - f), (-8, -50 - f), (-34, -26 - f * 0.5), (-30, 0), (-34, 26 + f * 0.5),
           (-8, 50 + f), (24, 38 + f)]
    P.lineas([(-30, 0), (-62, 4 + math.sin(t * 4) * 5), (-86, 2 + math.sin(t * 4 + 1) * 8)], col, 6)
    P.pol(ala, col)
    if not P.sil:
        P.pol([(46, 0), (22, -22), (-14, -28), (-26, 0), (-14, 28), (22, 22)], col2, borde=False)
        for dx, dy in ((-6, -14), (-6, 14), (8, 0), (-18, 0)):
            P.circ(dx, dy, 3, oscurecer(col, 0.35), borde=False)
        P.ojo(34, -9, 5)
        P.ojo(34, 9, 5)
        P.lin((48, 0), (50, 0), (60, 30, 50), 3)


def _espada(P, col, col2, t):
    mov = math.sin(t * 9) * 7
    P.pol([(-44, 0), (-70, -20 + mov), (-62, 0), (-70, 20 + mov)], col)
    P.pol([(-8, -22), (14, -22), (2, -52), (-18, -22)], oscurecer(col, 0.1))
    P.pol([(-6, 18), (10, 20), (-8, 36)], col)
    P.el(0, 0, 100, 44, col, borde=False)
    if not P.sil:
        P.el(4, 8, 90, 26, col2, borde=False)
        P.lin((-36, -2), (34, -2), aclarar(col, 0.4), 3)
    P.pol([(46, -3), (46, 3), (86, 0)], (190, 200, 215) if not P.sil else SIL, w=2)
    r = pygame.Rect(0, 0, int(100 * P.s), int(44 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.ojo(34, -6, 6.5)


def _lintera(P, col, col2, t):
    brillo = 0.5 + 0.5 * math.sin(t * 3)
    mov = math.sin(t * 7) * 5
    P.pol([(-34, 0), (-56, -18 + mov), (-56, 18 + mov)], col)
    P.lineas([(6, -30), (14, -52), (30, -60), (42, -50)], oscurecer(col, 0.3), 4)
    P.el(0, 0, 84, 70, col, borde=False)
    if not P.sil:
        P.el(-10, 8, 54, 36, col2, borde=False)
    r = pygame.Rect(0, 0, int(84 * P.s), int(70 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    # boca con dientes
    P.pol([(40, -4), (14, 4), (24, 26), (46, 18)], (60, 20, 50) if not P.sil else SIL, w=2)
    if not P.sil:
        for i, (a, b) in enumerate(((38, -2), (32, 2), (26, 6), (20, 11))):
            P.pol([(a, b), (a + 4, b + 10), (a + 8, b)], (255, 255, 255), w=1)
        P.circ(42, -52, 11 + brillo * 3, (255, 245, 130), borde=False)
        P.circ(42, -52, 6, (255, 255, 220), borde=False)
    P.ojo(22, -14, 7)


def _anguila(P, col, col2, t):
    n = 16
    pts = []
    for i in range(n + 1):
        u = i / n
        x = 72 - 144 * u
        y = math.sin(u * 7 - t * 4) * (10 + 6 * u)
        pts.append((x, y, 9.5 - 5.5 * u))
    for x, y, r in pts:
        P.circ(x, y, r + 2.4, oscurecer(col, 0.55), borde=False)
    for x, y, r in pts:
        P.circ(x, y, r, col, borde=False)
    if not P.sil:
        for x, y, r in pts[1:-1:2]:
            P.circ(x, y + r * 0.35, r * 0.55, col2, borde=False)
        for i in range(1, n - 1, 2):
            x, y, r = pts[i]
            P.lin((x, y - r), (x - 4, y - r - 6), oscurecer(col, 0.2), 3)
    x, y, r = pts[0]
    P.ojo(x - 2, y - 3, 4.2)
    if not P.sil:
        P.lin((x + 6, y + 3), (x + 1, y + 4), (60, 30, 50), 2)


def _tiburon(P, col, col2, t):
    mov = math.sin(t * 6) * 8
    P.pol([(-52, 0), (-84, -34 + mov), (-72, -4 + mov * 0.4), (-82, 26 + mov)], col)
    P.pol([(-6, -24), (18, -24), (4, -58), (-14, -24)], col)
    P.pol([(4, 14), (26, 16), (6, 42)], col)
    P.el(0, 0, 130, 54, col, borde=False)
    if not P.sil:
        P.el(10, 10, 112, 30, col2, borde=False)
        for dx in (16, 22, 28):
            P.lin((dx, -6), (dx - 2, 8), oscurecer(col, 0.4), 2)
    r = pygame.Rect(0, 0, int(130 * P.s), int(54 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.ojo(44, -8, 5.5)
    if not P.sil:
        P.lineas([(66, 6), (48, 12), (30, 8)], (60, 20, 40), 3)
        for dx in (60, 54, 48, 42, 36):
            P.pol([(dx, 7), (dx - 3, 14), (dx - 6, 8)], (255, 255, 255), w=1)


def _ballena(P, col, col2, t):
    mov = math.sin(t * 3) * 7
    P.pol([(-54, -2), (-76, -20 + mov * 0.5), (-92, -44 + mov), (-72, -38 + mov), (-62, -26 + mov * 0.6),
           (-60, -14 + mov * 0.4), (-76, -2)], col)
    P.pol([(-54, 2), (-76, 8), (-92, -18 + mov), (-62, -2)], col, borde=False)
    P.el(0, 0, 138, 76, col, borde=False)
    if not P.sil:
        P.el(10, 16, 112, 40, col2, borde=False)
        for i in range(5):
            P.lin((-24 + i * 14, 6), (-26 + i * 14, 22), oscurecer(col2, 0.12), 2)
    r = pygame.Rect(0, 0, int(138 * P.s), int(76 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.pol([(8, 14), (34, 26), (14, 34)], col)
    P.ojo(48, -4, 5)
    if not P.sil:
        pygame.draw.arc(P.p, (60, 30, 50), pygame.Rect(min(P.X(40), P.X(72)), P.Y(8), abs(P.X(72) - P.X(40)), 14 * P.s),
                        math.pi * 1.15, math.pi * 1.85, max(1, int(2 * P.s)))
        # chorro de agua
        for i, dx in enumerate((-4, 0, 4)):
            P.lineas([(14, -36), (14 + dx, -46 - i * 2), (14 + dx * 2, -54)], (200, 235, 255), 3)


def _pulpogig(P, col, col2, t):
    for i in range(-4, 5):
        pts = []
        for j in range(8):
            u = j / 7
            pts.append((i * 8.5 + math.sin(t * 3 + i * 0.8 + u * 5) * 9 * u + i * 3 * u, 6 + 58 * u))
        P.lineas(pts, col, 10)
        if not P.sil:
            P.lineas(pts, aclarar(col, 0.12), 7)
            for x, y in pts[2::2]:
                P.circ(x, y + 2, 2.2, col2, borde=False)
    P.el(4, -22, 98, 82, col)
    if not P.sil:
        P.el(-10, -42, 30, 18, aclarar(col, 0.3), borde=False)
        for dx, dy in ((20, -50), (30, -38), (-26, -44)):
            P.circ(dx, dy, 3.5, col2, borde=False)
        P.ojo(-10, -14, 11)
        P.ojo(24, -14, 11)
        P.lin((-22, -30), (-2, -24), (50, 20, 60), 4)
        P.lin((36, -30), (16, -24), (50, 20, 60), 4)
        pygame.draw.arc(P.p, (60, 30, 50), pygame.Rect(P.X(0) - 9 * P.s, P.Y(6), 18 * P.s, 12 * P.s),
                        math.pi * 1.1, math.pi * 1.9, max(1, int(3 * P.s)))


def _medusa(P, col, col2, t):
    pulso = math.sin(t * 3) * 3
    for i in range(-3, 4):
        pts = []
        for j in range(9):
            u = j / 8
            pts.append((i * 10 + math.sin(t * 4 + i + u * 6) * 5 * u, 10 + 46 * u))
        P.lineas(pts, aclarar(col, 0.25), 3)
    for i in (-1.5, 0, 1.5):
        pts = []
        for j in range(7):
            u = j / 6
            pts.append((i * 14 + math.sin(t * 3 + i + u * 5) * 8 * u, 8 + 36 * u))
        P.lineas(pts, col2, 6)
    P.pol([(-46, 8), (-38, -22 - pulso), (-18, -40 - pulso), (0, -44 - pulso), (18, -40 - pulso),
           (38, -22 - pulso), (46, 8), (30, 14), (14, 8), (0, 14), (-14, 8), (-30, 14)], col)
    if not P.sil:
        P.el(0, -22, 54, 26, aclarar(col, 0.5), borde=False)
        for dx in (-26, -10, 10, 26):
            P.circ(dx, -6, 3, aclarar(col, 0.55), borde=False)
        P.ojo(-12, -16, 5)
        P.ojo(12, -16, 5)
        pygame.draw.arc(P.p, (90, 50, 20), pygame.Rect(P.X(-6), P.Y(-12), 12 * P.s, 8 * P.s),
                        math.pi * 1.1, math.pi * 1.9, max(1, int(2 * P.s)))


# ----------------------------------------------------------------------------- ayudas de forma (pesca v2)
def _g(u, k=1.4, e=0.6):
    return max(0.0, math.sin(math.pi * min(1.0, max(0.0, u)) ** k)) ** e


def _w(u, base=0.14, k=1.4, e=0.6):
    return base + (1 - base) * _g(u, k, e)


def _suave(pts, it=3):
    """Suaviza un poligono cerrado (Chaikin)."""
    for _ in range(it):
        n = len(pts)
        nuevo = []
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            nuevo.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            nuevo.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = nuevo
    return pts


def _contorno(P, pts, col, w=3):
    pygame.draw.polygon(P.p, P.borde(col), [P.pt(a, b) for a, b in pts], max(1, int(w * P.s)))


def _forma(P, pts, col, borde=True, w=3, it=3):
    q = _suave(pts, it)
    P.pol(q, col, borde, w)
    return q


def _perfil(x0, x1, top, bot, n=26):
    ts = [(x0 + (x1 - x0) * i / n, top(i / n)) for i in range(n + 1)]
    bs = [(x0 + (x1 - x0) * i / n, bot(i / n)) for i in range(n + 1)]
    return ts + bs[::-1]


def _cuerpo(P, x0, x1, top, bot, col, col2=None, vientre=0.5, n=26):
    """Cuerpo de pez por perfil: x0 = cola, x1 = hocico; top(u)/bot(u) dan y."""
    pts = _perfil(x0, x1, top, bot, n)
    P.pol(pts, col, borde=False)
    if col2 and not P.sil:
        bel = [(x0 + (x1 - x0) * i / n, top(i / n) + (bot(i / n) - top(i / n)) * vientre) for i in range(n + 1)]
        bb = [(x0 + (x1 - x0) * i / n, bot(i / n)) for i in range(n + 1)]
        P.pol(bel + bb[::-1], col2, borde=False)
    _contorno(P, pts, col)
    return pts


def _tubo(P, pts, col, col2=None):
    """Cadena de circulos (x, y, r) con borde: cuerpos de serpiente."""
    for x, y, r in pts:
        P.circ(x, y, r + 2.4, oscurecer(col, 0.55), borde=False)
    for x, y, r in pts:
        P.circ(x, y, r, col, borde=False)
    if col2 and not P.sil:
        for x, y, r in pts[1:-1]:
            P.circ(x, y + r * 0.42, r * 0.5, col2, borde=False)


def _escamas(P, x0, x1, top, bot, col, paso=9, margen=6, ini=0.12, fin=0.8):
    if P.sil:
        return
    x = x0 + (x1 - x0) * ini
    k = 0
    while x < x0 + (x1 - x0) * fin:
        u = (x - x0) / (x1 - x0)
        y = top(u) + margen + (paso * 0.5 if k % 2 else 0)
        while y < bot(u) - margen:
            P.lineas([(x + 2, y - 3.5), (x - 1, y), (x + 2, y + 3.5)], col, 1.6)
            y += paso
        x += paso * 0.9
        k += 1


def _dientes(P, xa, xb, y_a, y_b, n, alto, ancho=4.0, col=(255, 255, 255), abajo=True):
    """Fila de dientes triangulares entre (xa, y_a) y (xb, y_b)."""
    if P.sil:
        return
    for i in range(n):
        f = i / max(1, n - 1)
        x = xa + (xb - xa) * f
        y = y_a + (y_b - y_a) * f
        d = alto if abajo else -alto
        P.pol([(x - ancho / 2, y), (x + ancho / 2, y), (x, y + d)], col, w=1)


def _aleta_suave(P, pts, col, col2=None):
    q = _forma(P, pts, col, it=2)
    return q


# ----------------------------------------------------------------------------- mundo 1
def _carpa(P, col, col2, t):
    mov = math.sin(t * 8) * 6
    P.pol([(-44, 0), (-72, -26 + mov), (-61, 0), (-72, 26 + mov)], col)
    P.pol([(-34, -22), (-28, -40), (-4, -45), (20, -30), (20, -22)], oscurecer(col, 0.12))
    top = lambda u: -30 * _w(u)
    bot = lambda u: 27 * _w(u)
    _cuerpo(P, -50, 52, top, bot, col, col2, 0.58)
    P.pol([(-22, 24), (-10, 40), (0, 24)], col)
    P.pol([(14, 16), (0, 38), (26, 22)], aclarar(col, 0.12))
    _escamas(P, -50, 52, top, bot, aclarar(col, 0.38), 9)
    P.lineas([(34, -26), (30, 0), (34, 20)], oscurecer(col, 0.35), 3)          # opérculo
    P.lineas([(48, 8), (56, 20), (52, 30)], (240, 220, 150), 2.5)              # bigotes
    P.lineas([(46, 12), (50, 26), (44, 34)], (240, 220, 150), 2.5)
    P.ojo(40, -12, 6.5)
    if not P.sil:
        P.lineas([(52, 6), (47, 11)], (80, 40, 40), 2)


def _bagre(P, col, col2, t):
    mov = math.sin(t * 7) * 6
    P.pol([(-44, -4), (-66, -16 + mov), (-72, 0 + mov), (-66, 16 + mov), (-44, 6)], col)
    P.pol([(-20, -24), (-12, -46), (6, -24)], oscurecer(col, 0.1))             # dorsal con espina
    P.pol([(-46, -16), (-34, -26), (-26, -16)], oscurecer(col, 0.1), w=2)      # adiposa
    top = lambda u: -26 * _w(u, 0.16, 1.1, 0.7)
    bot = lambda u: 20 * _w(u, 0.16, 1.1, 0.7)
    _cuerpo(P, -50, 50, top, bot, col, col2, 0.6)
    if not P.sil:
        for dx, dy, r in ((-30, -10, 4), (-14, -4, 5), (4, -12, 4), (-4, 4, 3.5), (18, -6, 4), (-36, 4, 3)):
            P.circ(dx, dy, r, oscurecer(col, 0.35), borde=False)
    P.pol([(-6, 14), (16, 18), (4, 36)], col)
    # bigotes largos y ondulados
    for i, (y0, ln) in enumerate(((2, 46), (8, 52), (-4, 40), (12, 44))):
        pts = [(48 + j * ln / 6, y0 + 4 + j * 2.6 + math.sin(t * 4 + i + j * 0.9) * 3) for j in range(7)]
        P.lineas(pts, oscurecer(col, 0.45), 5.5)
        P.lineas(pts, aclarar(col, 0.15), 3)
    P.ojo(34, -14, 4.8)
    if not P.sil:
        P.lineas([(50, 4), (40, 8), (28, 4)], (50, 25, 30), 2.5)


def _esturion(P, col, col2, t):
    mov = math.sin(t * 6) * 6
    P.pol([(-62, 0), (-100, -38 + mov), (-86, -4), (-98, 20 + mov)], col)
    top = lambda u: -22 * _w(u, 0.16, 1.1, 0.8)
    bot = lambda u: 20 * _w(u, 0.16, 1.1, 0.8)
    _cuerpo(P, -68, 80, top, bot, col, col2, 0.6)
    P.pol([(-40, -16), (-56, -36), (-24, -17)], oscurecer(col, 0.1))
    P.pol([(22, 12), (6, 32), (36, 20)], aclarar(col, 0.1))
    P.pol([(-30, 17), (-44, 32), (-16, 20)], col)
    if not P.sil:
        # placas oseas en tres filas
        clara = aclarar(col, 0.42)
        for x in range(-52, 46, 12):
            u = (x + 68) / 148
            P.pol([(x - 5, top(u) + 4), (x, top(u) - 4), (x + 5, top(u) + 4)], clara, w=1.5)
            P.pol([(x - 5, -1), (x, -7), (x + 5, -1), (x, 5)], clara, w=1.5)
            P.pol([(x - 5, bot(u) - 3), (x, bot(u) + 3), (x + 5, bot(u) - 3)], clara, w=1.5)
        P.lineas([(64, 8), (50, 14), (40, 14)], (50, 30, 30), 2)
        for dx in (50, 44):
            P.lin((dx, 14), (dx - 2, 24), (235, 225, 190), 2.5)
    P.ojo(52, -6, 4.5)


# ----------------------------------------------------------------------------- mundo 2
def _pezangel(P, col, col2, t):
    mov = math.sin(t * 8) * 4
    P.pol([(-30, -2), (-50, -16 + mov), (-46, 0 + mov), (-50, 16 + mov)], col)
    _forma(P, [(14, -34), (4, -52), (-18, -66), (-36, -70 + mov * .5), (-30, -44), (-26, -26)], col2, it=2)
    _forma(P, [(14, 34), (4, 52), (-18, 66), (-36, 70 + mov * .5), (-30, 44), (-26, 26)], col2, it=2)
    P.el(0, 0, 76, 82, col)
    if not P.sil:
        for x in (-16, 2, 20):
            h = 41 * math.sqrt(max(0.0, 1 - (x / 38.0) ** 2))
            P.lin((x, -h + 3), (x, h - 3), col2, 6)
        P.el(2, 12, 40, 30, aclarar(col, 0.3), borde=False)
        P.pol([(2, 30), (10, 46), (14, 28)], col2, w=2)
    r = pygame.Rect(0, 0, int(76 * P.s), int(82 * P.s))
    r.center = (int(P.X(0)), int(P.Y(0)))
    pygame.draw.ellipse(P.p, P.borde(col), r, max(1, int(3 * P.s)))
    P.ojo(22, -8, 6.5)
    if not P.sil:
        P.lineas([(37, 6), (31, 8)], (80, 40, 40), 2.5)


def _tortuga(P, col, col2, t):
    f = math.sin(t * 3) * 14
    P.pol([(-44, 6), (-60, 12 + f * .2), (-46, 14)], col)                            # cola
    _forma(P, [(-30, 12), (-50, 24 - f * .3), (-54, 34 - f * .3), (-40, 30), (-22, 18)], col, it=2)       # aleta trasera
    _forma(P, [(40, -4), (50, -14), (62, -10), (68, 0), (60, 8), (48, 10), (40, 6)], col, it=2)   # cabeza
    P.pol([(34, -2), (40, -4), (42, 8), (34, 12)], col, borde=False)                # cuello
    P.el(0, 6, 96, 40, aclarar(col2, 0.1))                                           # plastron
    cas = (150, 108, 58) if not P.sil else SIL
    _forma(P, [(-46, 10), (-38, -12), (-14, -28), (14, -28), (38, -14), (46, 10)], cas)
    if not P.sil:
        for dx, dy, r in ((-22, -4, 10), (0, -14, 11), (22, -4, 10), (0, 4, 10), (-30, 8, 6), (30, 8, 6)):
            pts = [(dx + r * math.cos(math.pi / 3 * i), dy + r * 0.8 * math.sin(math.pi / 3 * i)) for i in range(6)]
            P.pol(pts, oscurecer(cas, 0.15), w=1.8)
        P.lineas([(-46, 12), (46, 12)], oscurecer(cas, 0.5), 3.5)
    _forma(P, [(24, 12), (36, 22), (22, 44 + f), (-6, 62 + f), (-12, 56 + f), (2, 34), (6, 14)], aclarar(col, 0.08), it=2)   # aleta delantera
    P.ojo(56, -6, 4.5)
    if not P.sil:
        P.lineas([(68, 2), (58, 5)], (60, 40, 30), 2.2)


# ----------------------------------------------------------------------------- mundo 3
def _bacalao(P, col, col2, t):
    mov = math.sin(t * 7) * 5
    P.pol([(-46, 0), (-70, -22 + mov), (-66, 0), (-70, 22 + mov)], col)
    top = lambda u: -26 * _w(u, 0.14, 1.5, 0.55)
    bot = lambda u: 24 * _w(u, 0.14, 1.5, 0.55)
    for x0, x1, h in ((-38, -18, 30), (-12, 10, 32), (14, 30, 26)):                  # tres dorsales
        P.pol([(x0, -20), ((x0 + x1) / 2 - 3, -20 - h * .55), (x1, -20)], oscurecer(col, 0.1), w=2)
    P.pol([(-34, 22), (-20, 40), (-8, 22)], oscurecer(col, 0.05), w=2)
    P.pol([(0, 22), (10, 38), (22, 22)], oscurecer(col, 0.05), w=2)
    _cuerpo(P, -52, 56, top, bot, col, col2, 0.6)
    if not P.sil:
        for dx, dy, r in ((-30, -12, 3.2), (-18, -6, 3.8), (-6, -14, 3.0), (6, -4, 3.5), (18, -12, 3.2), (-12, 4, 2.6), (26, -2, 2.8), (-36, -2, 2.6)):
            P.circ(dx, dy, r, oscurecer(col, 0.45), borde=False)
        P.lineas([(-46, -4), (-20, -9), (10, -6), (40, -2)], aclarar(col2, 0.2), 2.4)   # linea lateral
        P.lineas([(34, -20), (30, 0), (34, 18)], oscurecer(col, 0.3), 2.5)
        P.lin((52, 14), (48, 28), (235, 225, 170), 3)                                      # barbilla
        P.lineas([(56, 8), (44, 12), (38, 8)], (60, 35, 30), 2.2)
    P.ojo(42, -10, 6)


def _ballena_cola(P, x, mov, col):
    """Aleta caudal de ballena vista de lado: dos lobulos en media luna hacia atras."""
    _forma(P, [(x + 6, -3), (x - 8, -16 + mov * .4), (x - 26, -30 + mov), (x - 42, -34 + mov), (x - 36, -16 + mov * .6),
               (x - 20, -6)], col, it=2)
    _forma(P, [(x + 6, 3), (x - 8, 16 + mov * .4), (x - 26, 30 + mov), (x - 42, 34 + mov), (x - 36, 16 + mov * .6),
               (x - 20, 6)], col, it=2)


def _beluga(P, col, col2, t):
    mov = math.sin(t * 4) * 6
    _ballena_cola(P, -50, mov, col)
    bulto = lambda u: 11 * math.exp(-((u - 0.84) / 0.10) ** 2)
    top = lambda u: -30 * _w(u, 0.10, 1.25, 0.62) - bulto(u)
    bot = lambda u: 30 * _w(u, 0.10, 1.25, 0.62)
    _cuerpo(P, -56, 64, top, bot, col, None)
    if not P.sil:
        P.el(10, 6, 80, 26, aclarar(col, 0.0), borde=False)
        P.lineas([(-30, -10), (-10, -4), (14, -6)], oscurecer(col, 0.12), 2)
        P.lineas([(-24, 6), (-4, 12), (20, 8)], oscurecer(col, 0.1), 2)
    P.pol([(16, 20), (6, 44), (30, 30)], col)
    P.ojo(40, -2, 4.5)
    if not P.sil:
        P.lineas([(64, 8), (54, 14), (44, 12)], (120, 90, 100), 2.4)        # sonrisa
        P.circ(46, 10, 3, (255, 170, 170), borde=False)


def _narval(P, col, col2, t):
    mov = math.sin(t * 4) * 6
    # colmillo largo (detras)
    P.pol([(58, -8), (136, -26), (138, -24), (60, 0)], (250, 245, 225) if not P.sil else SIL, w=2.5)
    if not P.sil:
        for i in range(8):
            x = 66 + i * 9
            y = -8 - (x - 58) * 0.23
            P.lin((x - 3, y + 7), (x + 3, y - 1), (200, 190, 160), 2)
    _ballena_cola(P, -50, mov, col)
    top = lambda u: -28 * _w(u, 0.10, 1.25, 0.62)
    bot = lambda u: 28 * _w(u, 0.10, 1.25, 0.62)
    _cuerpo(P, -56, 62, top, bot, col, col2, 0.62)
    if not P.sil:
        for dx, dy, r in ((-30, -14, 4), (-14, -18, 5), (2, -12, 4), (-22, 0, 4.5), (-4, -2, 3.5), (14, -6, 3.5),
                          (26, -12, 3), (-40, -4, 3), (-8, 10, 3), (30, 0, 2.6)):
            P.circ(dx, dy, r, oscurecer(col, 0.38), borde=False)
    P.pol([(16, 18), (6, 40), (30, 28)], col)
    P.ojo(40, -4, 4.5)
    if not P.sil:
        P.lineas([(60, 6), (52, 10), (44, 8)], (70, 50, 70), 2.2)


def _cachalote(P, col, col2, t):
    mov = math.sin(t * 3) * 6
    _ballena_cola(P, -76, mov * 1.2, col)
    cuerpo = [(-78, 0), (-56, -12), (-24, -26), (6, -34), (44, -42), (86, -42), (100, -30), (102, 4), (94, 22),
              (60, 28), (26, 30), (-10, 26), (-46, 14)]
    _forma(P, cuerpo, col, it=3)
    if not P.sil:
        for i in range(6):                                           # arrugas
            x = -34 + i * 14
            P.lineas([(x, -6), (x + 5, 2), (x, 10)], oscurecer(col, 0.3), 2)
        P.pol([(-42, -20), (-34, -34), (-20, -24)], oscurecer(col, 0.06), w=2)         # joroba
        P.lineas([(92, -44), (96, -52), (90, -58)], (210, 240, 255), 3)               # soplo
        P.lineas([(86, -44), (84, -54), (76, -62)], (210, 240, 255), 3)
    # mandibula inferior pequena
    _forma(P, [(94, 14), (62, 22), (34, 30), (36, 38), (72, 38), (96, 28)], aclarar(col, 0.25), it=2)
    P.pol([(30, 24), (20, 48), (50, 34)], col)
    P.ojo(62, 8, 4.5)
    if not P.sil:
        P.lineas([(100, 14), (80, 18), (50, 22)], (70, 55, 60), 2.4)
        _dientes(P, 84, 56, 24, 28, 5, 6, 3.4, (250, 245, 225), abajo=False)


def _orca(P, col, col2, t):
    mov = math.sin(t * 5) * 6
    _ballena_cola(P, -62, mov, col)
    cuerpo = [(76, 4), (62, -10), (30, -24), (-2, -30), (-34, -24), (-64, -8), (-72, 2), (-64, 8), (-34, 16),
              (8, 28), (46, 24), (66, 14)]
    q = _forma(P, cuerpo, col, borde=False, it=3)
    if not P.sil:
        vientre = [(70, 8), (50, 10), (20, 6), (-14, 6), (-40, 8), (-60, 6), (-34, 16), (8, 28), (46, 26), (66, 16)]
        _forma(P, vientre, col2, borde=False, it=2)
        P.el(-14, -24, 40, 10, (150, 155, 165), borde=False)                      # parche gris
        P.el(30, -10, 22, 10, col2, borde=False)                                   # mancha del ojo
    _contorno(P, q, col)
    _forma(P, [(-6, -26), (4, -50), (14, -74), (22, -48), (22, -24)], col, it=2)    # dorsal alta
    _forma(P, [(28, 14), (14, 50), (34, 46), (44, 22)], col, it=2)                   # aleta grande
    P.ojo(40, -8, 4)
    if not P.sil:
        P.lineas([(72, 8), (56, 12), (46, 10)], (50, 40, 50), 2)


# ----------------------------------------------------------------------------- mundo 4
def _pezvibora(P, col, col2, t):
    mov = math.sin(t * 7) * 5
    P.pol([(-46, 0), (-72, -20 + mov), (-62, 0), (-72, 20 + mov)], col)
    top = lambda u: -16 * _w(u, 0.16, 1.3, 0.7)
    bot = lambda u: 14 * _w(u, 0.16, 1.3, 0.7)
    # rayo dorsal largo con luz
    P.lineas([(10, -14), (28, -44), (46, -50), (56, -40)], oscurecer(col, 0.05), 3)
    _cuerpo(P, -52, 52, top, bot, col, col2, 0.55)
    P.pol([(-26, 12), (-10, 28), (-2, 12)], col, w=2)
    P.pol([(-32, -14), (-20, -28), (-10, -14)], col, w=2)
    # mandibulas abiertas con colmillos
    _forma(P, [(50, -2), (78, 8), (74, 14), (50, 22), (30, 14)], (95, 30, 55) if not P.sil else SIL, it=2)
    P.lineas([(52, -4), (66, 0), (80, 8)], oscurecer(col, 0.4), 3)
    if not P.sil:
        for x, y, h in ((72, 6, 14), (62, 3, 16), (54, 0, 12)):                       # superiores
            P.pol([(x - 3, y), (x + 3, y), (x + 1, y + h)], (255, 255, 235), w=1)
        for x, y, h in ((70, 14, -16), (60, 17, -15), (50, 20, -12), (42, 17, -10)):  # inferiores
            P.pol([(x - 3, y), (x + 3, y), (x - 1, y + h)], (255, 255, 235), w=1)
        for x in range(-30, 40, 10):
            P.circ(x, 9, 2, (140, 255, 235), borde=False)
        P.circ(56, -41, 4.5 + math.sin(t * 4), (160, 255, 240), borde=False)
    P.ojo(30, -6, 5.5)


def _pezhacha(P, col, col2, t):
    mov = math.sin(t * 9) * 3
    P.pol([(-44, 0), (-62, -12 + mov), (-58, 0), (-62, 12 + mov)], col)
    cuerpo = [(-48, 0), (-30, -10), (0, -22), (26, -26), (42, -14), (44, 2), (34, 26), (14, 52), (-4, 42), (-26, 16)]
    _forma(P, cuerpo, col, it=2)
    if not P.sil:
        _forma(P, [(-30, 6), (0, 0), (30, 8), (36, 22), (14, 48), (-4, 40), (-24, 16)], col2, borde=False, it=2)
        P.lineas([(-40, -2), (0, -12), (34, -10)], (255, 255, 255), 3)
        for i in range(7):                                         # fotoforos en la quilla
            pass
        for fx, fy in ((34, 20), (30, 29), (25, 37), (19, 43), (12, 45), (5, 42), (-2, 36)):
            P.circ(fx, fy, 2.2, (170, 250, 255), borde=False)
    P.pol([(-18, -18), (-8, -42), (6, -22)], col, w=2)
    P.pol([(-22, 24), (-30, 40), (-10, 30)], col, w=2)
    # ojos grandes mirando arriba
    if not P.sil:
        P.circ(30, -14, 10, (255, 255, 255), borde=True, w_b=2)
        P.circ(31, -18, 5.5, (30, 25, 45), borde=False)
        P.circ(29, -20, 1.8, (255, 255, 255), borde=False)
        P.lineas([(44, 4), (36, 12), (30, 8)], (60, 40, 50), 2.4)
    else:
        P.circ(30, -14, 10, col, borde=False)


def _pezpescador(P, col, col2, t):
    mov = math.sin(t * 6) * 5
    luz = 0.5 + 0.5 * math.sin(t * 3)
    P.pol([(-40, 0), (-66, -16 + mov), (-62, 0), (-66, 16 + mov)], col)
    # senuelo
    P.lineas([(14, -34), (26, -58), (44, -68), (58, -56)], oscurecer(col, 0.2), 4)
    if not P.sil:
        P.circ(58, -56, 9 + luz * 3, (255, 235, 110), borde=False)
        P.circ(58, -56, 5, (255, 255, 230), borde=False)
    P.el(0, 0, 100, 88, col)
    if not P.sil:
        P.el(-4, 18, 78, 40, col2, borde=False)
        for dx, dy, r in ((-24, -22, 4), (-8, -28, 3), (-34, -6, 3.5), (-18, 4, 3), (6, -16, 3)):
            P.circ(dx, dy, r, oscurecer(col, 0.3), borde=False)
        P.pol([(-20, -40), (-10, -52), (-2, -38)], oscurecer(col, 0.1), w=2)
    # boca enorme con agujas
    _forma(P, [(46, -4), (50, 16), (32, 34), (4, 38), (-6, 28), (22, 22), (40, 10)], (80, 25, 45) if not P.sil else SIL, it=2)
    P.lineas([(46, -4), (36, 10), (20, 20), (-4, 28)], oscurecer(col, 0.45), 3)
    if not P.sil:
        for i in range(6):
            x, y = 42 - i * 8.5, 5 + i * 3.6
            P.pol([(x - 2.5, y), (x + 2.5, y), (x, y + 13 - i)], (255, 255, 235), w=1)
        for i in range(5):
            x, y = 48 - i * 9, 14 + i * 4.4
            P.pol([(x - 2.5, y), (x + 2.5, y), (x + 1, y - 12 + i)], (255, 255, 235), w=1)
    P.pol([(-8, 16), (-22, 34), (2, 28)], col, w=2)
    P.ojo(24, -14, 5)


# ----------------------------------------------------------------------------- mundo 5
def _celacanto(P, col, col2, t):
    mov = math.sin(t * 5) * 5
    P.pol([(-54, 0), (-78, -28 + mov), (-72, -8 + mov), (-88, 0 + mov * .5), (-72, 8 + mov), (-78, 28 + mov)], col)
    top = lambda u: -24 * _w(u, 0.2, 1.3, 0.6)
    bot = lambda u: 22 * _w(u, 0.2, 1.3, 0.6)
    P.pol([(-6, -20), (4, -42), (22, -20)], oscurecer(col, 0.1), w=2)
    P.pol([(-46, -18), (-40, -40), (-20, -22)], oscurecer(col, 0.05), w=2)
    _cuerpo(P, -58, 62, top, bot, col, col2, 0.62)
    # aletas lobuladas (con "pata")
    for (bx, by, ln) in ((14, 18, 1.0), (-16, 18, 0.95), (-36, 18, 0.7)):
        ex, ey = bx - 10 * ln, by + 16 * ln
        P.lin((bx, by), (ex, ey), oscurecer(col, 0.35), 12 * ln)
        P.lin((bx, by), (ex, ey), col, 8 * ln)
        _forma(P, [(ex - 7 * ln, ey - 2), (ex + 5 * ln, ey - 6), (ex + 9 * ln, ey + 8 * ln), (ex - 2 * ln, ey + 20 * ln),
                   (ex - 10 * ln, ey + 12 * ln)], aclarar(col, 0.1), it=2)
    P.pol([(-2, -22), (-12, -32), (-20, -22)], col, w=2)
    if not P.sil:
        for dx in range(-40, 44, 10):
            for dy in (-12, -3, 7):
                u = (dx + 58) / 120
                if top(u) + 5 < dy < bot(u) - 5:
                    P.circ(dx + (4 if dy == -3 else 0), dy, 1.8, (245, 248, 255), borde=False)
        P.lineas([(46, -18), (42, 0), (46, 14)], oscurecer(col, 0.3), 2.5)
        P.lineas([(62, 6), (50, 9), (42, 6)], (40, 30, 50), 2.2)
    P.ojo(46, -6, 5.5)


def _rot(pts, ang, ox, oy):
    c, s = math.cos(ang), math.sin(ang)
    return [(ox + x * c - y * s, oy + x * s + y * c) for x, y in pts]


def _megalodon(P, col, col2, t):
    mov = math.sin(t * 4) * 9
    P.pol([(-98, -2), (-142, -66 + mov), (-122, -10), (-136, 34 + mov), (-98, 6)], col)
    sup = [(104, 0), (96, -8), (70, -24), (30, -38), (-10, -43), (-50, -35), (-84, -18), (-104, -4), (-104, 5),
           (-84, 12), (-50, 22), (-10, 34), (30, 36), (44, 26), (70, 8)]
    q = _forma(P, sup, col, borde=False, it=2)
    if not P.sil:
        bel = [(-98, 3), (-60, 7), (-20, 13), (30, 12), (70, 8), (44, 26), (30, 36), (-10, 34), (-50, 22), (-84, 12)]
        _forma(P, bel, col2, borde=False, it=2)
    _contorno(P, q, col)
    P.pol([(-16, -40), (2, -96), (14, -70), (32, -38)], col)
    P.pol([(-66, -28), (-74, -50), (-52, -32)], col, w=2)
    P.pol([(34, 22), (12, 70), (30, 62), (62, 30)], col)
    P.pol([(-44, 20), (-56, 40), (-30, 24)], col, w=2)
    # boca abierta
    P.pol([(100, 2), (68, 8), (44, 26), (98, 26)], (110, 25, 45) if not P.sil else SIL, borde=False)
    _forma(P, [(44, 26), (30, 38), (42, 50), (82, 48), (102, 34), (100, 24)], col2 if not P.sil else col, it=1)
    if not P.sil:
        _dientes(P, 98, 52, 2, 14, 9, 13, 6.5)
        _dientes(P, 98, 52, 26, 29, 8, 11, 6, abajo=False)
        for x in (36, 42, 48, 54):
            P.lineas([(x, -16), (x - 4, -2), (x, 12)], oscurecer(col, 0.45), 2.5)
        P.lineas([(-30, -20), (-22, -10)], aclarar(col, 0.3), 2.5)
        P.lineas([(10, -26), (18, -16)], aclarar(col, 0.3), 2.5)
        P.lin((52, -22), (80, -14), oscurecer(col, 0.6), 4)
    P.ojo(70, -14, 5)


def _cabeza_serpiente(P, pts, ang, ox, oy, col, col2):
    q = _forma(P, [(x, y) for x, y in _rot(pts, ang, ox, oy)], col, it=2)
    return q


def _cadena(n, f):
    return [f(i / (n - 1)) for i in range(n)]


def _serpiente(P, col, col2, t):
    def nodo(u):
        return (104 - 214 * u, math.sin(u * 6.4 - t * 3.2) * (18 + 8 * u), 4.5 + 9.5 * (1 - u) ** 0.7)
    ns = _cadena(46, nodo)
    # aleta dorsal roja
    for i in range(2, 44, 2):
        x, y, r = ns[i]
        P.pol([(x + 5, y - r), (x - 1, y - r - 12 - 4 * math.sin(i)), (x - 6, y - r)], (215, 70, 70), w=2)
    x, y, r = ns[-1]
    P.pol([(x + 2, y), (x - 24, y - 16), (x - 18, y), (x - 24, y + 16)], col)
    _tubo(P, ns, col, col2)
    if not P.sil:
        for i in range(3, 44, 3):
            x, y, r = ns[i]
            P.lineas([(x + 2, y + r * 0.15), (x, y + r * 0.9)], aclarar(col2, 0.1), 2)
    hx, hy, hr = ns[0]
    a = math.atan2(ns[0][1] - ns[1][1], ns[0][0] - ns[1][0])
    head = [(-8, -14), (12, -17), (32, -12), (46, -5), (44, 5), (26, 11), (6, 15), (-8, 12)]
    # cresta en abanico
    if not P.sil:
        for k in range(5):
            aa = -2.4 + k * 0.5
            ex, ey = _rot([(26 * math.cos(aa), 26 * math.sin(aa))], a, hx, hy)[0]
            sx, sy = _rot([(-2 + 4 * math.cos(aa), 4 * math.sin(aa))], a, hx, hy)[0]
            P.pol([(sx, sy), (ex, ey), (sx + 3, sy + 3)], (215, 70, 70), w=2)
    _forma(P, _rot(head, a, hx, hy), col, it=2)
    if not P.sil:
        _forma(P, _rot([(-6, 4), (20, 6), (44, 4), (40, 8), (20, 13), (-4, 12)], a, hx, hy), col2, borde=False, it=1)
        ex, ey = _rot([(18, -6)], a, hx, hy)[0]
        P.ojo(ex, ey, 5)
        P.lineas(_rot([(46, 3), (30, 6), (14, 4)], a, hx, hy), (80, 30, 40), 2.2)
        lx, ly = _rot([(45, 4)], a, hx, hy)[0]
        l1 = _rot([(58 + math.sin(t * 10) * 3, 4)], a, hx, hy)[0]
        P.lineas([(lx, ly), l1, _rot([(66, 0)], a, hx, hy)[0]], (225, 60, 80), 2.2)
        P.lineas([l1, _rot([(66, 8)], a, hx, hy)[0]], (225, 60, 80), 2.2)


def _dragonmar(P, col, col2, t):
    oro = (250, 205, 80)
    def nodo(u):
        return (100 - 206 * u, math.sin(u * 5.6 - t * 2.6) * (24 + 6 * u), 4.0 + 10 * (1 - u) ** 0.65)
    ns = _cadena(54, nodo)
    # melena dorada
    for i in range(2, 34):
        x, y, r = ns[i]
        h = 18 - i * 0.28 + 4 * math.sin(t * 5 + i)
        P.pol([(x + 6, y - r), (x - 2, y - r - h), (x - 5, y - r)], (240, 110, 70) if i % 2 else oro, w=1.5)
    # cola con penacho
    x, y, r = ns[-1]
    P.pol([(x + 4, y), (x - 22, y - 20), (x - 12, y - 4), (x - 30, y), (x - 12, y + 6), (x - 24, y + 22)], oro, w=2)
    # patas con garras
    for i in (9, 17, 27, 33):
        x, y, r = ns[i]
        P.lineas([(x, y + r * 0.7), (x - 4, y + r + 8), (x + 2, y + r + 16)], oscurecer(col, 0.2), 6)
        P.lineas([(x, y + r * 0.7), (x - 4, y + r + 8), (x + 2, y + r + 16)], col, 3.5)
        for dx in (-5, 0, 5):
            P.lin((x + 2, y + r + 16), (x + 2 + dx, y + r + 22), (255, 245, 210), 2)
    _tubo(P, ns, col, col2)
    if not P.sil:
        for i in range(2, 50, 2):
            x, y, r = ns[i]
            P.lineas([(x + 3, y - r * 0.5), (x, y - r * 0.1), (x + 3, y + r * 0.3)], aclarar(col, 0.35), 1.6)
    hx, hy, hr = ns[0]
    a = math.atan2(ns[0][1] - ns[1][1], ns[0][0] - ns[1][0])
    if not P.sil:
        for lado in (-1, 1):                                      # bigotes largos
            pts = [(40 + k * 7, 2 * lado + lado * k * 1.6 + math.sin(t * 4 + k * .8 + lado) * 4) for k in range(9)]
            P.lineas(_rot(pts, a, hx, hy), oro, 2.4)
        # cuernos ramificados
        for base in ((8, -14), (-2, -14)):
            pts = _rot([base, (base[0] - 10, base[1] - 16), (base[0] - 20, base[1] - 20)], a, hx, hy)
            P.lineas(pts, oro, 3.5)
            P.lineas(_rot([(base[0] - 10, base[1] - 16), (base[0] - 8, base[1] - 28)], a, hx, hy), oro, 3)
    head = [(-8, -14), (14, -17), (34, -14), (50, -9), (56, -3), (50, 4), (28, 10), (6, 15), (-8, 12)]
    _forma(P, _rot(head, a, hx, hy), col, it=2)
    if not P.sil:
        _forma(P, _rot([(-6, 5), (24, 6), (52, 2), (46, 8), (24, 13), (-4, 12)], a, hx, hy), col2, borde=False, it=1)
        P.lineas(_rot([(48, 4), (30, 7), (12, 5)], a, hx, hy), (100, 40, 30), 2.2)
        pts = _rot([(50, 6), (50, 14), (44, 22)], a, hx, hy)               # barbita
        P.lineas(pts, oro, 3)
        ex, ey = _rot([(22, -6)], a, hx, hy)[0]
        P.ojo(ex, ey, 5.5)
        ox, oy = _rot([(56, -6)], a, hx, hy)[0]
        pygame.draw.circle(P.p, (210, 40, 40), (int(P.X(ox)), int(P.Y(oy))), max(2, int(2.5 * P.s)))
        px, py = _rot([(76, 0)], a, hx, hy)[0]                            # perla
        P.circ(px, py, 8, (200, 240, 255), w_b=2)
        P.circ(px - 2, py - 3, 2.5, (255, 255, 255), borde=False)


def _tentaculo(P, bx, by, fin_x, fin_y, onda, col, col2, r0, t, ph, ventosas=True, n=22):
    pts = []
    for j in range(n):
        u = j / (n - 1)
        x = bx + (fin_x - bx) * u + math.sin(t * 3 + ph + u * 5) * onda * u
        y = by + (fin_y - by) * u - math.sin(u * math.pi) * 0 + math.cos(t * 3 + ph + u * 4) * onda * 0.35 * u
        pts.append((x, y, r0 * (1 - u) ** 0.8 + 2.2))
    _tubo(P, pts, col)
    if ventosas and not P.sil:
        for x, y, r in pts[4:-2:2]:
            P.circ(x, y + r * 0.4, max(1.3, r * 0.32), col2, borde=False)
    return pts


def _kraken(P, col, col2, t):
    # brazos largos levantados
    for lado in (-1, 1):
        _tentaculo(P, lado * 34, 8, lado * 150, -96, 14, col, col2, 12, t, lado * 1.3, n=30)
    for i, bx in enumerate((-42, -26, -9, 9, 26, 42)):
        fx = bx * 2.0 + (i - 2.5) * 12
        _tentaculo(P, bx, 18, fx, 98 + (i % 2) * 14, 11, col, col2, 11, t, i * 0.9)
    # cuerpo (manto) puntiagudo
    manto = [(0, -112), (22, -90), (42, -52), (48, -14), (36, 14), (12, 24), (-12, 24), (-36, 14), (-48, -14), (-42, -52), (-22, -90)]
    _forma(P, manto, col, it=3)
    if not P.sil:
        _forma(P, [(0, -66), (24, -40), (30, -6), (14, 16), (-14, 16), (-30, -6), (-24, -40)], aclarar(col, 0.12), borde=False, it=3)
        for k in range(5):                                           # lomos
            P.lineas([(-30 + k * 15, -60 + abs(k - 2) * 8), (-26 + k * 14, -20)], oscurecer(col, 0.28), 2.5)
        for dx, h in ((-30, 16), (0, 26), (30, 16)):                  # pinchos
            P.pol([(dx - 7, -66 + abs(dx) * .5), (dx, -66 - h + abs(dx) * .5), (dx + 7, -66 + abs(dx) * .5)], col2, w=2)
        for lado in (-1, 1):
            cx = lado * 22
            P.circ(cx, -6, 13, (255, 235, 90), w_b=2.5)
            P.circ(cx + lado * 1, -5, 4.2, (60, 10, 20), borde=False)
            P.lin((cx - lado * 18, -26), (cx + lado * 12, -14), (40, 15, 40), 5)       # ceno
        P.pol([(-9, 14), (9, 14), (0, 28)], (40, 20, 30), w=2)                           # pico
    else:
        for lado in (-1, 1):
            P.circ(lado * 22, -6, 13, SIL, borde=False)


def _leviatan(P, col, col2, t):
    oro = (250, 205, 90)
    def nodo(u):
        return (118 - 250 * u, math.sin(u * 5.0 - t * 2.0 + 0.7) * (26 * (0.35 + 0.65 * u)) - 6, 5 + 20 * (1 - u) ** 0.55)
    ns = _cadena(60, nodo)
    # pinchos dorsales dorados
    for i in range(3, 56, 3):
        x, y, r = ns[i]
        h = 22 * (1 - i / 70)
        P.pol([(x + 7, y - r), (x - 2, y - r - h), (x - 9, y - r)], oro, w=2)
    x, y, r = ns[-1]
    mov = math.sin(t * 3) * 8
    P.pol([(x + 4, y), (x - 30, y - 34 + mov), (x - 22, y - 4), (x - 34, y + 30 + mov)], col)
    if not P.sil:
        P.lineas([(x - 6, y), (x - 30, y - 30 + mov)], oro, 2.4)
    # aleta lateral
    x, y, r = ns[9]
    P.pol([(x + 6, y + r * .6), (x - 8, y + r + 34), (x - 22, y + r + 20), (x - 28, y + r * .4)], col)
    _tubo(P, ns, col, col2)
    if not P.sil:
        for i in range(3, 56, 3):
            x, y, r = ns[i]
            P.lineas([(x + 3, y - r * 0.8), (x + 1, y), (x + 3, y + r * 0.8)], oscurecer(col, 0.3), 2.4)   # placas
    hx, hy, hr = ns[0]
    a = math.atan2(ns[0][1] - ns[1][1], ns[0][0] - ns[1][0])
    # cuernos
    if not P.sil:
        for k, (bx, by) in enumerate(((2, -22), (-12, -22))):
            P.pol(_rot([(bx + 6, by), (bx - 6, by), (bx - 26 - k * 6, by - 24 - k * 4), (bx - 10, by - 4)], a, hx, hy), oro, w=2)
    # mandibula inferior abierta
    ab = 0.38
    inf = _rot([(0, 4), (70, 4), (84, 6), (80, 12), (52, 26), (10, 30), (-6, 22)], ab, 0, 0)
    P.pol(_rot(inf, a, hx, hy), col, w=3)
    if not P.sil:
        interior = _rot([(2, 2), (84, 4), (60, 4), (8, 6)], ab * 0.5, 0, 0)
        _forma(P, _rot([(6, -2), (84, 6), (64, 30), (20, 26)], a, hx, hy), (110, 25, 45), borde=False, it=1)
        P.pol(_rot(inf, a, hx, hy), col, w=3)
        dd = _rot([(78, 6), (24, 6)], ab, 0, 0)
        for i in range(6):
            f = i / 5
            bx0 = dd[0][0] + (dd[1][0] - dd[0][0]) * f
            by0 = dd[0][1] + (dd[1][1] - dd[0][1]) * f
            P.pol(_rot([(bx0 - 3, by0), (bx0 + 3, by0), (bx0, by0 - 11)], a, hx, hy), (255, 250, 235), w=1)
    sup = [(-10, -24), (22, -26), (58, -18), (84, -8), (88, 0), (60, 2), (20, 2), (-10, 4)]
    _forma(P, _rot(sup, a, hx, hy), col, it=2)
    if not P.sil:
        for i in range(6):
            bx0 = 76 - i * 10
            P.pol(_rot([(bx0 - 3, 1), (bx0 + 3, 1), (bx0, 13)], a, hx, hy), (255, 250, 235), w=1)
        P.lineas(_rot([(86, -2), (50, -4), (20, -4)], a, hx, hy), oscurecer(col, 0.5), 2.4)
        ex, ey = _rot([(32, -12)], a, hx, hy)[0]
        P.circ(ex, ey, 8, oro, w_b=2.5)
        P.circ(ex + 1, ey, 3, (50, 10, 30), borde=False)
        pygame.draw.line(P.p, (50, 10, 30), (P.X(ex - 9), P.Y(ey - 8)), (P.X(ex + 8), P.Y(ey - 3)), max(2, int(3 * P.s)))
    else:
        pass


# ----------------------------------------------------------------------------- tabla de formas nuevas
_NUEVAS = {
    "carpa": _carpa, "bagre": _bagre, "esturion": _esturion, "pezangel": _pezangel, "tortuga": _tortuga,
    "bacalao": _bacalao, "beluga": _beluga, "narval": _narval, "cachalote": _cachalote, "orca": _orca,
    "pezvibora": _pezvibora, "pezhacha": _pezhacha, "pezpescador": _pezpescador, "celacanto": _celacanto,
    "megalodon": _megalodon, "serpiente": _serpiente, "dragonmar": _dragonmar, "kraken": _kraken,
    "leviatan": _leviatan,
}

FORMAS.update({
    "carpa": (130, [("aleta", (-6, -36, 50, 28)), ("cola", (-60, 0, 36, 56)), ("cuerpo", (0, 0, 70, 56))]),
    "bagre": (140, [("aleta", (-8, -36, 36, 30)), ("bigotes", (62, 14, 40, 40)), ("cola", (-62, 0, 36, 40)), ("cuerpo", (-2, 0, 80, 44))]),
    "esturion": (190, [("aleta", (-40, -26, 40, 26)), ("cola", (-82, -8, 44, 60)), ("cuerpo", (0, 0, 100, 40))]),
    "pezangel": (100, [("aleta", (-32, -56, 40, 50)), ("cola", (-42, 0, 24, 34)), ("cuerpo", (0, 0, 60, 70))]),
    "tortuga": (140, [("cabeza", (56, -2, 30, 24)), ("aleta", (14, 32, 30, 36)), ("caparazon", (0, -8, 80, 40)), ("cuerpo", (0, 4, 80, 40))]),
    "bacalao": (130, [("aleta", (-12, -34, 60, 24)), ("cola", (-60, 0, 34, 50)), ("cuerpo", (0, 0, 80, 48))]),
    "beluga": (150, [("lomo", (0, -30, 60, 20)), ("cola", (-62, -12, 40, 60)), ("cuerpo", (4, 0, 80, 58))]),
    "narval": (210, [("colmillo", (96, -20, 70, 22)), ("cola", (-62, -12, 40, 60)), ("cuerpo", (0, 0, 80, 54))]),
    "cachalote": (190, [("cabeza", (66, -6, 56, 56)), ("cola", (-90, -12, 40, 60)), ("cuerpo", (0, -4, 90, 54))]),
    "orca": (150, [("dorsal", (8, -52, 28, 50)), ("cola", (-70, -12, 40, 60)), ("cuerpo", (0, -4, 90, 50))]),
    "pezvibora": (130, [("rayo", (36, -42, 40, 26)), ("dientes", (60, 8, 40, 32)), ("cola", (-60, 0, 30, 40)), ("cuerpo", (-4, 0, 80, 30))]),
    "pezhacha": (100, [("aleta", (-8, -32, 30, 24)), ("quilla", (14, 36, 40, 36)), ("cuerpo", (-4, 10, 70, 60))]),
    "pezpescador": (130, [("senuelo", (50, -58, 36, 30)), ("boca", (26, 16, 50, 46)), ("cola", (-54, 0, 30, 36)), ("cuerpo", (0, 0, 80, 70))]),
    "celacanto": (150, [("aleta", (14, 28, 30, 40)), ("cola", (-76, 0, 36, 56)), ("cuerpo", (0, 0, 100, 44))]),
    "megalodon": (230, [("dorsal", (6, -66, 40, 54)), ("boca", (70, 20, 60, 50)), ("cola", (-122, -14, 46, 90)), ("cuerpo", (-4, 0, 140, 72))]),
    "serpiente": (230, [("cresta", (96, -14, 40, 40)), ("lomo", (20, -28, 80, 24)), ("cola", (-100, 0, 40, 40)), ("cuerpo", (0, 0, 200, 56))]),
    "dragonmar": (240, [("melena", (60, -26, 60, 44)), ("cabeza", (96, -4, 50, 40)), ("cola", (-100, 0, 44, 44)), ("cuerpo", (0, 0, 200, 64))]),
    "kraken": (230, [("cabeza", (0, -60, 90, 100)), ("brazos", (0, 66, 150, 70)), ("cuerpo", (0, -30, 96, 90))]),
    "leviatan": (270, [("cabeza", (96, 0, 70, 54)), ("lomo", (10, -34, 90, 26)), ("cola", (-124, 0, 50, 60)), ("cuerpo", (0, 0, 200, 70))]),
})


def dibujar_animal(p, ident, datos, cx, cy, escala=1.0, direccion=1, t=0.0, silueta=False):
    """Dibuja un animal marino. datos = (color, color2, forma). escala=1 -> unos 130 px de largo nominal."""
    color, color2, forma = datos
    P = _Pincel(p, cx, cy, escala, 1 if direccion >= 0 else -1, silueta)
    col, col2 = color, color2
    if forma == "oval":
        _clasico(P, ident, col, col2, t, 44, 28, cola_grande=(ident == "dorado"))
    elif forma == "larga":
        _clasico(P, ident, col, col2, t, 52, 22)
    elif forma == "globo":
        _globo(P, col, col2, t)
    elif forma == "luna":
        _luna(P, col, col2, t)
    elif forma == "pulpo":
        _pulpo(P, col, col2, t)
    elif forma == "caballito":
        _caballito(P, col, col2, t)
    elif forma == "raya":
        _raya(P, col, col2, t)
    elif forma == "espada":
        _espada(P, col, col2, t)
    elif forma == "lintera":
        _lintera(P, col, col2, t)
    elif forma == "anguila":
        _anguila(P, col, col2, t)
    elif forma == "tiburon":
        _tiburon(P, col, col2, t)
    elif forma == "ballena":
        _ballena(P, col, col2, t)
    elif forma == "pulpogig":
        _pulpogig(P, col, col2, t)
    elif forma == "medusa":
        _medusa(P, col, col2, t)
    elif forma in _NUEVAS:
        _NUEVAS[forma](P, col, col2, t)
    else:
        _clasico(P, ident, col, col2, t, 44, 28)


# ----------------------------------------------------------------------------- iconos de pista
def icono_pista(p, tipo, x, y, r=18, t=0.0):
    """tipo: 'facil' (pulgar verde), 'medio' (pulgar amarillo de lado), 'dificil' (cuidado rojo),
    'hondo' (flecha gris hacia abajo: esta muy profundo para tu cuerda)."""
    x, y = int(x), int(y)
    if tipo == "dificil":
        q = [(x, y - r - 2), (x + r + 4, y + r - 2), (x - r - 4, y + r - 2)]
        pygame.draw.polygon(p, (235, 60, 60), q)
        pygame.draw.polygon(p, (255, 255, 255), q, 3)
        pygame.draw.line(p, (255, 255, 255), (x, y - r * 0.45), (x, y + r * 0.2), max(3, r // 5))
        pygame.draw.circle(p, (255, 255, 255), (x, int(y + r * 0.62)), max(2, r // 7))
        return
    col = {"facil": (70, 190, 90), "medio": (240, 190, 40), "hondo": (130, 140, 165)}[tipo]
    pygame.draw.circle(p, col, (x, y), r)
    pygame.draw.circle(p, (255, 255, 255), (x, y), r, 3)
    if tipo == "hondo":
        pygame.draw.polygon(p, (255, 255, 255), [(x - r * 0.5, y - r * 0.1), (x + r * 0.5, y - r * 0.1), (x, y + r * 0.55)])
        pygame.draw.rect(p, (255, 255, 255), (x - r * 0.15, y - r * 0.6, r * 0.3, r * 0.55))
        return
    # mano en un lienzo pequeno para poder girarla
    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    c = r
    pygame.draw.rect(s, (255, 255, 255), (c - r * 0.52, c - r * 0.05, r * 0.7, r * 0.62), border_radius=max(2, r // 5))
    pygame.draw.rect(s, (255, 255, 255), (c - r * 0.2, c - r * 0.62, r * 0.28, r * 0.62), border_radius=max(2, r // 6))
    pygame.draw.rect(s, (255, 255, 255), (c + r * 0.14, c + 0.0, r * 0.3, r * 0.5), border_radius=max(2, r // 7))
    if tipo == "medio":
        s = pygame.transform.rotate(s, -90)
    p.blit(s, s.get_rect(center=(x, y)))


# ----------------------------------------------------------------------------- barcos
MANO_BARCO = {1: (46, -58), 2: (58, -62), 3: (64, -64), 4: (96, -104)}      # donde sostiene la cana (respecto a x, WY)
NOMBRE_BARCO = {1: "Bote de remos", 2: "Bote a motor", 3: "Lancha rápida", 4: "Barco pesquero"}


def _nino(s, x, y):
    """Nino ninja sentado: (x, y) = cintura."""
    pygame.draw.rect(s, (60, 90, 190), (x - 16, y - 34, 32, 40), border_radius=10)
    pygame.draw.circle(s, (255, 214, 175), (x, y - 50), 18)
    pygame.draw.circle(s, (60, 40, 40), (x, y - 50), 18, 3)
    pygame.draw.rect(s, (225, 55, 60), (x - 19, y - 60, 38, 9))
    pygame.draw.polygon(s, (225, 55, 60), [(x - 18, y - 56), (x - 34, y - 48), (x - 20, y - 50)])
    pygame.draw.circle(s, (40, 30, 50), (x + 7, y - 49), 3)
    pygame.draw.arc(s, (120, 50, 50), (x + 3, y - 46, 12, 9), math.pi * 1.1, math.pi * 1.9, 2)


_cache_barcos = {}


def dibujar_barco(p, nivel, x, wy, t=0.0, roll=0.0):
    """Dibuja el barco (nivel 1..4) con su linea de flotacion en wy, centrado en x. Devuelve la posicion de la mano.
    El dibujo y sus giros se guardan en cache (el balanceo se redondea a medio grado)."""
    nivel = max(1, min(4, int(nivel)))
    W, H = 440, 300
    cw = H - 70
    paso = int(round(roll * 2))
    clave = (nivel, paso)
    img = _cache_barcos.get(clave)
    if img is None:
        base = _cache_barcos.get((nivel, None))
        if base is None:
            base = _cache_barcos[(nivel, None)] = _barco_base(nivel, W, H)
        img = pygame.transform.rotozoom(base, paso / 2.0, 1.0) if paso else base
        _cache_barcos[clave] = img
    p.blit(img, img.get_rect(center=(int(x), int(wy - (cw - H // 2)))))
    mx, my = MANO_BARCO[nivel]
    return x + mx, wy + my


def _barco_base(nivel, W, H):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cw = W // 2, H - 70                         # cw: linea de flotacion dentro del lienzo
    if nivel == 1:
        casco = [(cx - 112, cw - 22), (cx + 112, cw - 22), (cx + 84, cw + 22), (cx - 84, cw + 22)]
        pygame.draw.polygon(s, (150, 98, 55), casco)
        pygame.draw.polygon(s, (90, 55, 30), casco, 4)
        pygame.draw.rect(s, (200, 145, 85), (cx - 118, cw - 30, 236, 12), border_radius=6)
        pygame.draw.rect(s, (120, 80, 45), (cx - 20, cw - 26, 8, 40))
        for dx in (-70, 0, 70):
            pygame.draw.line(s, (110, 70, 40), (cx + dx, cw - 20), (cx + dx - 8, cw + 18), 3)
        pygame.draw.line(s, (120, 80, 45), (cx - 40, cw - 28), (cx - 108, cw + 40), 8)
        pygame.draw.ellipse(s, (150, 98, 55), (cx - 128, cw + 28, 40, 18))
        _nino(s, cx + 6, cw - 20)
    elif nivel == 2:
        casco = [(cx - 130, cw - 28), (cx + 130, cw - 24), (cx + 96, cw + 22), (cx - 110, cw + 22)]
        pygame.draw.polygon(s, (245, 245, 250), casco)
        pygame.draw.polygon(s, (60, 100, 170), casco, 4)
        pygame.draw.rect(s, (60, 110, 200), (cx - 124, cw - 12, 224, 10))
        pygame.draw.rect(s, (60, 70, 85), (cx - 150, cw - 38, 30, 52), border_radius=8)
        pygame.draw.rect(s, (110, 120, 135), (cx - 144, cw + 12, 14, 30))
        pygame.draw.polygon(s, (120, 125, 140), [(cx - 146, cw + 38), (cx - 126, cw + 38), (cx - 134, cw + 50)])
        pygame.draw.rect(s, (230, 90, 70), (cx - 60, cw - 34, 52, 12), border_radius=5)
        _nino(s, cx + 12, cw - 22)
    elif nivel == 3:
        casco = [(cx - 140, cw - 20), (cx + 150, cw - 36), (cx + 100, cw + 22), (cx - 120, cw + 22)]
        pygame.draw.polygon(s, (225, 60, 60), casco)
        pygame.draw.polygon(s, (120, 25, 35), casco, 4)
        pygame.draw.polygon(s, (255, 255, 255), [(cx - 136, cw - 14), (cx + 140, cw - 28), (cx + 132, cw - 14), (cx - 132, cw)])
        pygame.draw.polygon(s, (170, 220, 245), [(cx - 10, cw - 22), (cx + 30, cw - 62), (cx + 48, cw - 62), (cx + 28, cw - 24)])
        pygame.draw.polygon(s, (255, 255, 255), [(cx - 10, cw - 22), (cx + 30, cw - 62), (cx + 48, cw - 62), (cx + 28, cw - 24)], 3)
        pygame.draw.rect(s, (60, 70, 85), (cx - 154, cw - 34, 22, 38), border_radius=6)
        pygame.draw.rect(s, (60, 60, 80), (cx - 108, cw - 36, 56, 16), border_radius=6)
        _nino(s, cx - 24, cw - 26)
    else:
        casco = [(cx - 190, cw - 34), (cx + 190, cw - 34), (cx + 150, cw + 30), (cx - 160, cw + 30)]
        pygame.draw.polygon(s, (50, 90, 160), casco)
        pygame.draw.polygon(s, (25, 45, 95), casco, 5)
        pygame.draw.rect(s, (225, 70, 60), (cx - 176, cw - 2, 332, 14))
        pygame.draw.rect(s, (245, 245, 250), (cx - 170, cw - 40, 340, 14), border_radius=4)
        pygame.draw.rect(s, (245, 245, 250), (cx - 120, cw - 92, 110, 58), border_radius=8)
        pygame.draw.rect(s, (60, 100, 170), (cx - 120, cw - 92, 110, 58), 4, border_radius=8)
        for dx in (-104, -72, -40):
            pygame.draw.rect(s, (170, 220, 245), (cx + dx, cw - 82, 22, 22), border_radius=4)
        pygame.draw.rect(s, (225, 70, 60), (cx - 96, cw - 114, 60, 24), border_radius=5)
        pygame.draw.line(s, (80, 80, 95), (cx - 66, cw - 114), (cx - 66, cw - 150), 5)
        pygame.draw.polygon(s, (255, 210, 60), [(cx - 64, cw - 150), (cx - 34, cw - 142), (cx - 64, cw - 134)])
        pygame.draw.line(s, (80, 80, 95), (cx + 60, cw - 40), (cx + 60, cw - 120), 6)
        pygame.draw.line(s, (80, 80, 95), (cx + 60, cw - 118), (cx + 150, cw - 60), 5)
        pygame.draw.line(s, (180, 180, 190), (cx + 150, cw - 60), (cx + 150, cw - 30), 2)
        _nino(s, cx + 6, cw - 40)
    return s


# ----------------------------------------------------------------------------- fondos
ZONAS_ARTE = {
    1: dict(cielo=((125, 200, 255), (225, 245, 255)), agua=((95, 205, 205), (28, 105, 125)), suelo=(205, 185, 125)),
    2: dict(cielo=((105, 190, 250), (205, 240, 255)), agua=((60, 205, 235), (18, 100, 175)), suelo=(235, 215, 160)),
    3: dict(cielo=((100, 165, 235), (255, 228, 190)), agua=((40, 150, 225), (8, 48, 130)), suelo=(150, 140, 125)),
    4: dict(cielo=((85, 110, 175), (205, 190, 220)), agua=((24, 90, 175), (5, 22, 70)), suelo=(70, 75, 95)),
    5: dict(cielo=((15, 20, 65), (85, 70, 135)), agua=((28, 40, 115), (4, 4, 24)), suelo=(40, 35, 60)),
}
_cache_fondos = {}


def _grad(s, rect, a, b):
    x, y, w, h = rect
    for i in range(int(h)):
        f = i / max(1, h - 1)
        pygame.draw.line(s, tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3)), (x, y + i), (x + w, y + i))


def _nube(s, x, y, w, color=(255, 255, 255)):
    for dx, dy, r in ((-0.3, 0.1, 0.3), (0, -0.1, 0.4), (0.3, 0.1, 0.3), (0.0, 0.18, 0.3)):
        pygame.draw.circle(s, color, (int(x + dx * w), int(y + dy * w)), int(r * w * 0.6))


def _alga(s, x, y, alto, color, rnd, grosor=9):
    pts = []
    fase = rnd.uniform(0, 6)
    for i in range(9):
        u = i / 8
        pts.append((x + math.sin(fase + u * 4.2) * 14 * u, y - alto * u))
    pygame.draw.lines(s, oscurecer(color, 0.4), False, pts, grosor + 4)
    pygame.draw.lines(s, color, False, pts, grosor)


def _coral(s, x, y, alto, color, rnd):
    pygame.draw.line(s, oscurecer(color, 0.3), (x, y), (x, y - alto), 12)
    for dx, h in ((-22, 0.7), (22, 0.6), (-8, 0.9), (10, 1.0)):
        pygame.draw.line(s, color, (x, y - alto * 0.3), (x + dx, y - alto * h), 9)
        pygame.draw.circle(s, aclarar(color, 0.35), (x + dx, int(y - alto * h)), 9)


def _roca(s, x, y, w, h, color):
    pts = [(x - w / 2, y), (x - w * 0.42, y - h * 0.65), (x - w * 0.1, y - h), (x + w * 0.3, y - h * 0.85),
           (x + w / 2, y - h * 0.3), (x + w * 0.5, y)]
    pygame.draw.polygon(s, color, pts)
    pygame.draw.polygon(s, oscurecer(color, 0.45), pts, 4)
    pygame.draw.line(s, aclarar(color, 0.25), (x - w * 0.2, y - h * 0.75), (x + w * 0.1, y - h * 0.9), 4)


def fondo_zona(zona):
    """(fondo, frente): fondo opaco del corte lateral y capa transparente que va delante de los peces."""
    zona = max(1, min(5, int(zona)))
    if zona in _cache_fondos:
        return _cache_fondos[zona]
    z = ZONAS_ARTE[zona]
    rnd = random.Random(zona * 31)
    bg = pygame.Surface((ANCHO, ALTO))
    fr = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _grad(bg, (0, 0, ANCHO, WY), *z["cielo"])
    _grad(bg, (0, WY, ANCHO, ALTO - WY), *z["agua"])
    # ---- cielo
    if zona == 5:
        for _ in range(110):
            pygame.draw.circle(bg, (255, 255, 235), (rnd.randint(0, ANCHO), rnd.randint(0, WY - 20)), rnd.choice((1, 1, 2)))
        pygame.draw.circle(bg, (235, 235, 255), (1010, 90), 44)
        pygame.draw.circle(bg, (15, 20, 65), (1030, 80), 40)
    else:
        sol = {1: (760, 120), 2: (1040, 110), 3: (880, 170), 4: (1000, 110)}[zona]
        col = {1: (255, 244, 170), 2: (255, 244, 170), 3: (255, 190, 110), 4: (230, 215, 200)}[zona]
        pygame.draw.circle(bg, aclarar(col, 0.3), sol, 62)
        pygame.draw.circle(bg, col, sol, 44)
        for cx, cy, w in ((560, 70, 150), (1130, 170, 130), (700, 140, 90)):
            _nube(bg, cx, cy, w, (255, 255, 255) if zona < 4 else (150, 150, 185))
    # ---- orilla / costa lejana (solo detras del agua)
    if zona == 1:
        pygame.draw.ellipse(bg, (110, 185, 120), (700, WY - 90, 800, 180))
        pygame.draw.ellipse(bg, (90, 165, 110), (900, WY - 130, 600, 230))
        for x, h in ((980, 80), (1060, 100), (1150, 70), (1220, 90)):
            pygame.draw.rect(bg, (95, 65, 40), (x - 4, WY - h * 0.45, 8, h * 0.45))
            pygame.draw.circle(bg, (60, 150, 80), (x, int(WY - h * 0.6)), int(h * 0.38))
    elif zona == 2:
        pygame.draw.ellipse(bg, (235, 215, 150), (760, WY - 36, 220, 70))
        pygame.draw.ellipse(bg, (110, 185, 110), (790, WY - 52, 150, 52))
        pygame.draw.rect(bg, (95, 65, 40), (860, WY - 86, 8, 40))
        pygame.draw.polygon(bg, (60, 150, 80), [(864, WY - 86), (830, WY - 70), (864, WY - 76), (900, WY - 70)])
    elif zona == 3:
        pygame.draw.polygon(bg, (120, 150, 190), [(1100, WY), (1160, WY - 60), (1220, WY)])
        pygame.draw.polygon(bg, (95, 125, 170), [(1170, WY), (1240, WY - 90), (1300, WY)])
    elif zona == 4:
        for x in range(0, ANCHO, 90):
            h = rnd.randint(14, 40)
            pygame.draw.polygon(bg, (60, 80, 125), [(x, WY), (x + 45, WY - h), (x + 90, WY)])
    else:
        pygame.draw.polygon(bg, (30, 25, 75), [(850, WY), (940, WY - 70), (1010, WY - 20), (1090, WY - 90), (1200, WY)])
    # ---- rayos de luz
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    if zona <= 4:
        a = {1: 38, 2: 36, 3: 28, 4: 14}[zona]
        for i in range(7):
            x0 = 60 + i * 190 + rnd.randint(-30, 30)
            pygame.draw.polygon(capa, (255, 255, 235, a), [(x0, WY), (x0 + 55, WY), (x0 + 205, ALTO), (x0 + 80, ALTO)])
    bg.blit(capa, (0, 0))
    # ---- superficie
    pygame.draw.rect(bg, aclarar(z["agua"][0], 0.45), (0, WY, ANCHO, 5))
    # ---- fondo marino
    base = z["suelo"]
    sy = 648
    pts = [(0, ALTO), (0, sy + 10)]
    for x in range(0, ANCHO + 40, 40):
        pts.append((x, sy + math.sin(x * 0.013 + zona) * 12 + math.sin(x * 0.04) * 4))
    pts.append((ANCHO, ALTO))
    pygame.draw.polygon(bg, base, pts)
    pygame.draw.lines(bg, aclarar(base, 0.25), False, pts[1:-1], 4)
    for _ in range(40):
        pygame.draw.circle(bg, oscurecer(base, 0.2 + rnd.random() * 0.15),
                           (rnd.randint(0, ANCHO), rnd.randint(sy + 20, ALTO - 4)), rnd.randint(2, 5))
    # siluetas lejanas (dan profundidad)
    sil = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for _ in range(6):
        x = rnd.randint(40, ANCHO - 40)
        _roca(sil, x, sy + 6, rnd.randint(110, 220), rnd.randint(60, 150), (*oscurecer(z["agua"][1], 0.2), 120))
    bg.blit(sil, (0, 0))
    # ---- decoracion del fondo (detras de los peces)
    if zona == 1:
        for x in range(30, ANCHO, 95):
            _alga(bg, x + rnd.randint(-20, 20), sy + 14, rnd.randint(50, 120), (70, 160, 90), rnd, 8)
        for x, y in ((220, WY + 3), (560, WY + 4), (1010, WY + 3)):                # nenufares
            pygame.draw.ellipse(bg, (70, 170, 85), (x - 38, y - 8, 76, 16))
            pygame.draw.ellipse(bg, (250, 170, 200), (x - 8, y - 14, 16, 12))
        for x in (440, 780, 1200):
            _roca(bg, x, sy + 22, 120, 56, (130, 125, 120))
    elif zona == 2:
        cols = [(240, 110, 130), (250, 160, 70), (170, 110, 220), (80, 200, 170)]
        for i, x in enumerate(range(80, ANCHO, 150)):
            _coral(bg, x + rnd.randint(-30, 30), sy + 16, rnd.randint(50, 110), cols[i % 4], rnd)
        for x in (330, 900):
            _roca(bg, x, sy + 24, 130, 60, (150, 140, 135))
    elif zona == 3:
        for x in range(50, ANCHO, 110):
            _alga(bg, x + rnd.randint(-25, 25), sy + 16, rnd.randint(110, 230), (45, 130, 90), rnd, 11)
        for x in (260, 760, 1130):
            _roca(bg, x, sy + 26, 190, 100, (110, 110, 125))
    elif zona == 4:
        for x in (150, 520, 940, 1200):
            _roca(bg, x, sy + 30, rnd.randint(200, 280), rnd.randint(110, 190), (60, 65, 90))
        for x in range(90, ANCHO, 210):
            for k in range(3):
                pygame.draw.line(bg, (190, 80, 110), (x + k * 12, sy + 12), (x + k * 12 + rnd.randint(-6, 6), sy - 34 - k * 8), 7)
                pygame.draw.circle(bg, (255, 130, 160), (x + k * 12, int(sy - 36 - k * 8)), 6)
    else:
        for x in (200, 640, 1040):
            _roca(bg, x, sy + 34, rnd.randint(220, 300), rnd.randint(120, 200), (45, 40, 70))
        glow = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        for x in range(80, ANCHO, 130):
            h = rnd.randint(40, 90)
            pygame.draw.line(bg, (60, 200, 190), (x, sy + 14), (x + rnd.randint(-10, 10), sy - h), 5)
            pygame.draw.circle(glow, (90, 255, 230, 70), (x, int(sy - h)), 22)
            pygame.draw.circle(bg, (150, 255, 235), (x, int(sy - h)), 8)
        pygame.draw.polygon(glow, (255, 150, 70, 50), [(560, sy), (610, sy - 220), (660, sy)])
        bg.blit(glow, (0, 0))
    # ---- capa de frente (algas y rocas en los bordes, delante de los peces)
    if zona == 1:
        for x in (20, 90, 1180, 1250):
            _alga(fr, x, ALTO + 6, rnd.randint(110, 190), (60, 150, 80), rnd, 12)
    elif zona == 2:
        for x, c in ((30, (240, 110, 130)), (1230, (250, 160, 70))):
            _coral(fr, x, ALTO + 8, 120, c, rnd)
    elif zona == 3:
        for x in (20, 70, 1210, 1260):
            _alga(fr, x, ALTO + 6, rnd.randint(170, 270), (40, 120, 85), rnd, 14)
    elif zona == 4:
        _roca(fr, 40, ALTO + 20, 220, 120, (45, 50, 75))
        _roca(fr, 1240, ALTO + 20, 240, 130, (45, 50, 75))
    else:
        _roca(fr, 30, ALTO + 20, 230, 140, (30, 28, 50))
        _roca(fr, 1250, ALTO + 20, 240, 140, (30, 28, 50))
        for x in (120, 1140):
            pygame.draw.line(fr, (60, 200, 190), (x, ALTO), (x + 6, ALTO - 90), 6)
            pygame.draw.circle(fr, (150, 255, 235), (x + 6, ALTO - 92), 8)
    _cache_fondos[zona] = (bg, fr)
    return bg, fr


# ----------------------------------------------------------------------------- fondos por mundo (pesca v2)
_cache_mundos = {}


def _brillo(s, x, y, r, col, a=60, pasos=6):
    """Resplandor suave: circulos concentricos translucidos (s debe ser SRCALPHA)."""
    for i in range(pasos):
        f = 1 - i / pasos
        pygame.draw.circle(s, (*col, int(a * (1 - f) ** 1.2 + 6)), (int(x), int(y)), int(r * f + 2))


def _particulas(s, rnd, n, col, rmax=3, y0=WY + 10, y1=ALTO - 10, a=120):
    for _ in range(n):
        pygame.draw.circle(s, (*col, rnd.randint(a // 2, a)), (rnd.randint(0, ANCHO), rnd.randint(y0, y1)), rnd.choice((1, 1, 2, rmax)))


def _rayos(bg, rnd, a, col=(255, 255, 235), n=7, ancho=55, pen=205):
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for i in range(n):
        x0 = 40 + i * (ANCHO // n) + rnd.randint(-30, 30)
        pygame.draw.polygon(capa, (*col, a), [(x0, WY), (x0 + ancho, WY), (x0 + pen, ALTO), (x0 + pen // 2 - 40, ALTO)])
    bg.blit(capa, (0, 0))


def _suelo(bg, rnd, base, sy=648, amp=12, semilla=0):
    pts = [(0, ALTO), (0, sy + 10)]
    for x in range(0, ANCHO + 40, 40):
        pts.append((x, sy + math.sin(x * 0.013 + semilla) * amp + math.sin(x * 0.04) * 4))
    pts.append((ANCHO, ALTO))
    pygame.draw.polygon(bg, base, pts)
    pygame.draw.lines(bg, aclarar(base, 0.25), False, pts[1:-1], 4)
    for _ in range(46):
        pygame.draw.circle(bg, oscurecer(base, 0.18 + rnd.random() * 0.15),
                           (rnd.randint(0, ANCHO), rnd.randint(sy + 20, ALTO - 4)), rnd.randint(2, 5))


def _columna(s, x, base, alto, ancho, color, rota=False, rnd=None):
    c2 = oscurecer(color, 0.4)
    top = base - alto
    pygame.draw.rect(s, color, (x - ancho // 2, top, ancho, alto))
    for k in range(1, 4):
        xx = x - ancho // 2 + ancho * k // 4
        pygame.draw.line(s, c2, (xx, top + 6), (xx, base), 2)
    pygame.draw.rect(s, c2, (x - ancho // 2, top, ancho, alto), 3)
    pygame.draw.rect(s, aclarar(color, 0.1), (x - ancho // 2 - 8, base - 12, ancho + 16, 14))
    pygame.draw.rect(s, c2, (x - ancho // 2 - 8, base - 12, ancho + 16, 14), 3)
    if rota:
        pts = [(x - ancho // 2, top + 2), (x - ancho * 0.25, top - 16), (x - ancho * 0.05, top + 6),
               (x + ancho * 0.2, top - 24), (x + ancho // 2, top)]
        pygame.draw.polygon(s, color, pts + [(x + ancho // 2, top + 6), (x - ancho // 2, top + 6)])
        pygame.draw.lines(s, c2, False, pts, 3)
    else:
        pygame.draw.rect(s, aclarar(color, 0.1), (x - ancho // 2 - 8, top - 12, ancho + 16, 14))
        pygame.draw.rect(s, c2, (x - ancho // 2 - 8, top - 12, ancho + 16, 14), 3)


def _runa(s, x, y, r, col):
    pygame.draw.circle(s, col, (int(x), int(y)), int(r), 3)
    pygame.draw.line(s, col, (x - r * 0.5, y + r * 0.4), (x, y - r * 0.6), 3)
    pygame.draw.line(s, col, (x, y - r * 0.6), (x + r * 0.5, y + r * 0.4), 3)
    pygame.draw.line(s, col, (x - r * 0.3, y), (x + r * 0.3, y), 3)


def _abanico(s, x, y, alto, color, rnd):
    for i in range(-5, 6):
        a = -math.pi / 2 + i * 0.2
        pygame.draw.line(s, color, (x, y), (x + math.cos(a) * alto * 0.8, y + math.sin(a) * alto), 5)
    pygame.draw.arc(s, aclarar(color, 0.3), (x - alto * 0.7, y - alto, alto * 1.4, alto * 1.1), 0.3, math.pi - 0.3, 5)
    pygame.draw.line(s, oscurecer(color, 0.3), (x, y), (x, y + 18), 9)


def _cerebro(s, x, y, r, color):
    pygame.draw.circle(s, oscurecer(color, 0.25), (x, y), r + 3)
    pygame.draw.circle(s, color, (x, y), r)
    for k in range(5):
        pygame.draw.arc(s, oscurecer(color, 0.3), (x - r + 4, y - r + 6 + k * r // 3, r * 2 - 8, r // 2), 0.2, math.pi - 0.2, 3)


def _tubos(s, x, y, alto, color, rnd):
    for dx, h in ((-14, 0.7), (0, 1.0), (14, 0.8)):
        hh = alto * h
        pygame.draw.rect(s, color, (x + dx - 8, y - hh, 16, hh), border_radius=7)
        pygame.draw.ellipse(s, oscurecer(color, 0.45), (x + dx - 8, y - hh - 4, 16, 10))
        pygame.draw.rect(s, oscurecer(color, 0.3), (x + dx - 8, y - hh, 16, hh), 3, border_radius=7)


def _anemona(s, x, y, r, color, t0=0.0):
    pygame.draw.ellipse(s, oscurecer(color, 0.4), (x - r * 0.7, y - r * 0.35, r * 1.4, r * 0.7))
    for i in range(-5, 6):
        a = i * 0.16
        ex, ey = x + math.sin(a) * r * 1.3 + i * 2, y - r * 1.2 + abs(i) * 2
        pygame.draw.line(s, color, (x + i * r * 0.1, y - 4), (ex, ey), 6)
        pygame.draw.circle(s, aclarar(color, 0.4), (int(ex), int(ey)), 5)


def _estrellamar(s, x, y, r, color):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    pygame.draw.polygon(s, color, pts)
    pygame.draw.polygon(s, oscurecer(color, 0.4), pts, 3)


def _pino(s, x, y, h, color):
    pygame.draw.rect(s, (90, 62, 40), (x - 3, y - h * 0.2, 6, h * 0.2))
    for k in range(3):
        w = h * (0.34 - k * 0.07)
        yy = y - h * 0.2 - k * h * 0.26
        pygame.draw.polygon(s, color, [(x - w, yy), (x + w, yy), (x, yy - h * 0.42)])


def _palmera(s, x, y, h):
    pygame.draw.lines(s, (110, 78, 48), False, [(x, y), (x + 8, y - h * 0.5), (x + 4, y - h)], 7)
    for a in (-2.7, -2.2, -1.2, -0.6, -0.1, 0.4):
        ex, ey = x + 4 + math.cos(a) * 52, y - h + math.sin(a) * 30 + 14
        pygame.draw.polygon(s, (50, 150, 80), [(x + 4, y - h), ((x + 4 + ex) / 2, (y - h + ey) / 2 - 12), (ex, ey), ((x + 4 + ex) / 2, (y - h + ey) / 2 + 6)])


def _medusa_fondo(s, x, y, r, col, rnd, t0=0):
    cam = pygame.Surface((int(r * 3), int(r * 5)), pygame.SRCALPHA)
    w = cam.get_width()
    pygame.draw.ellipse(cam, (*col, 90), (w * 0.5 - r, 4, r * 2, r * 1.5))
    pygame.draw.ellipse(cam, (*aclarar(col, 0.4), 140), (w * 0.5 - r * 0.6, 10, r * 1.2, r * 0.6))
    for i in range(-3, 4):
        pts = [(w * 0.5 + i * r * 0.25 + math.sin(i + k * 0.9) * 6, r * 1.2 + k * r * 0.4) for k in range(7)]
        pygame.draw.lines(cam, (*col, 110), False, pts, 3)
    s.blit(cam, (x - w // 2, y))


def _mundo1(bg, fr, rnd):
    _grad(bg, (0, 0, ANCHO, WY), (120, 198, 255), (228, 246, 255))
    glow = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _brillo(glow, 770, 112, 150, (255, 240, 170), 70)
    bg.blit(glow, (0, 0))
    pygame.draw.circle(bg, (255, 246, 175), (770, 112), 44)
    for cx, cy, w in ((520, 66, 160), (1140, 160, 130), (300, 150, 100), (980, 60, 90)):
        _nube(bg, cx, cy, w)
    for x, y in ((200, 70), (240, 92), (1000, 140)):                                  # pajaros
        pygame.draw.lines(bg, (70, 80, 100), False, [(x - 10, y - 4), (x - 4, y), (x, y - 3), (x + 4, y), (x + 10, y - 4)], 2)
    # orilla lejana con colinas, pinos y cabana
    pygame.draw.ellipse(bg, (126, 190, 130), (620, WY - 80, 800, 170))
    pygame.draw.ellipse(bg, (96, 168, 112), (880, WY - 128, 640, 230))
    for x, h in ((940, 90), (1000, 110), (1070, 80), (1140, 100), (1200, 84), (1250, 96)):
        _pino(bg, x, WY - 6, h, (48, 128, 84))
    pygame.draw.rect(bg, (170, 120, 80), (1030, WY - 40, 50, 34))
    pygame.draw.polygon(bg, (190, 70, 60), [(1022, WY - 40), (1055, WY - 66), (1088, WY - 40)])
    pygame.draw.rect(bg, (250, 235, 190), (1046, WY - 30, 12, 24))
    for x in range(660, 900, 22):                                                      # juncos
        pygame.draw.line(bg, (80, 150, 90), (x, WY), (x + rnd.randint(-4, 4), WY - rnd.randint(14, 34)), 3)
    _grad(bg, (0, WY, ANCHO, ALTO - WY), (100, 212, 205), (26, 100, 122))
    _rayos(bg, rnd, 36)
    pygame.draw.rect(bg, (190, 238, 238), (0, WY, ANCHO, 5))
    for _ in range(26):                                                                # destellos
        x = rnd.randint(0, ANCHO)
        pygame.draw.line(bg, (225, 250, 250), (x, WY + 12 + rnd.randint(0, 18)), (x + rnd.randint(14, 34), WY + 12 + rnd.randint(0, 18)), 2)
    sy = 648
    _suelo(bg, rnd, (206, 188, 128), sy, 12, 1)
    sil = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for _ in range(6):
        _roca(sil, rnd.randint(40, ANCHO - 40), sy + 6, rnd.randint(110, 220), rnd.randint(60, 140), (24, 80, 98, 110))
    bg.blit(sil, (0, 0))
    for x in range(30, ANCHO, 80):
        _alga(bg, x + rnd.randint(-20, 20), sy + 14, rnd.randint(50, 130), (68, 160, 92), rnd, 8)
    for x, y in ((220, WY + 3), (360, WY + 5), (560, WY + 4), (1010, WY + 3)):         # nenufares
        pygame.draw.ellipse(bg, (66, 168, 84), (x - 40, y - 8, 80, 16))
        pygame.draw.ellipse(bg, (250, 168, 200), (x - 8, y - 15, 16, 12))
        pygame.draw.line(bg, (60, 140, 80), (x, y + 6), (x + 3, y + 70), 3)
    for x in (440, 780, 1200):
        _roca(bg, x, sy + 22, 120, 56, (134, 128, 120))
    for x in (150, 700, 980):                                                          # conchas y piedras
        pygame.draw.ellipse(bg, (240, 220, 200), (x, sy + 38, 22, 14))
        pygame.draw.arc(bg, (200, 170, 150), (x, sy + 38, 22, 14), 0, math.pi, 2)
    for x in (20, 90, 1180, 1250):
        _alga(fr, x, ALTO + 6, rnd.randint(110, 190), (58, 150, 80), rnd, 12)
    for x in (60, 1210):
        for k in range(4):
            pygame.draw.line(fr, (80, 160, 90), (x + k * 14, ALTO), (x + k * 14 + rnd.randint(-10, 10), ALTO - rnd.randint(110, 170)), 6)
    _particulas(fr, rnd, 40, (255, 255, 255), 2, a=70)


def _mundo2(bg, fr, rnd):
    _grad(bg, (0, 0, ANCHO, WY), (84, 186, 252), (206, 242, 255))
    glow = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _brillo(glow, 1050, 100, 140, (255, 245, 180), 70)
    bg.blit(glow, (0, 0))
    pygame.draw.circle(bg, (255, 248, 185), (1050, 100), 42)
    for cx, cy, w in ((500, 80, 140), (200, 120, 110), (760, 50, 90)):
        _nube(bg, cx, cy, w)
    # isla tropical
    pygame.draw.ellipse(bg, (240, 220, 156), (700, WY - 34, 300, 80))
    pygame.draw.ellipse(bg, (110, 188, 112), (740, WY - 58, 200, 60))
    _palmera(bg, 800, WY - 22, 96)
    _palmera(bg, 880, WY - 24, 72)
    pygame.draw.ellipse(bg, (255, 120, 90), (840, WY - 18, 14, 10))
    _grad(bg, (0, WY, ANCHO, ALTO - WY), (64, 220, 236), (16, 96, 176))
    _rayos(bg, rnd, 44, (255, 255, 230), 8, 60, 215)
    pygame.draw.rect(bg, (200, 250, 250), (0, WY, ANCHO, 5))
    sy = 648
    _suelo(bg, rnd, (238, 218, 164), sy, 10, 2)
    sil = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for _ in range(5):
        _roca(sil, rnd.randint(40, ANCHO - 40), sy + 6, rnd.randint(110, 200), rnd.randint(60, 130), (20, 100, 150, 90))
    bg.blit(sil, (0, 0))
    cols = [(240, 106, 132), (252, 160, 70), (176, 112, 224), (80, 204, 172), (255, 210, 80)]
    for i, x in enumerate(range(70, ANCHO, 120)):
        c = cols[i % 5]
        k = i % 5
        xx = x + rnd.randint(-24, 24)
        if k == 0:
            _coral(bg, xx, sy + 16, rnd.randint(60, 120), c, rnd)
        elif k == 1:
            _abanico(bg, xx, sy + 14, rnd.randint(70, 110), (255, 130, 160), rnd)
        elif k == 2:
            _cerebro(bg, xx, sy - 8, rnd.randint(22, 34), (230, 190, 90))
        elif k == 3:
            _tubos(bg, xx, sy + 16, rnd.randint(70, 110), (170, 110, 225), rnd)
        else:
            _coral(bg, xx, sy + 16, rnd.randint(60, 100), c, rnd)
    for x in (330, 900):
        _roca(bg, x, sy + 24, 130, 60, (156, 146, 140))
    for x, y in ((280, sy + 40), (650, sy + 46), (1040, sy + 38)):
        _estrellamar(bg, x, y, 14, (252, 130, 90))
    _anemona(bg, 520, sy + 26, 26, (250, 120, 190))
    _anemona(bg, 1130, sy + 26, 22, (255, 190, 80))
    for x in range(40, ANCHO, 60):                                                    # pasto marino
        pygame.draw.line(bg, (60, 170, 110), (x, sy + 18), (x + rnd.randint(-8, 8), sy - rnd.randint(14, 36)), 3)
    for x, c in ((30, (240, 106, 132)), (1230, (252, 160, 70))):
        _coral(fr, x, ALTO + 8, 130, c, rnd)
    _abanico(fr, 110, ALTO + 6, 80, (255, 130, 160), rnd)
    _tubos(fr, 1150, ALTO + 10, 76, (170, 110, 225), rnd)
    for _ in range(18):                                                               # burbujas
        x, y = rnd.randint(0, ANCHO), rnd.randint(WY + 30, ALTO - 30)
        r = rnd.randint(3, 8)
        pygame.draw.circle(fr, (255, 255, 255, 70), (x, y), r, 2)
    _particulas(fr, rnd, 30, (255, 255, 255), 2, a=70)


def _mundo3(bg, fr, rnd):
    _grad(bg, (0, 0, ANCHO, WY), (14, 32, 86), (130, 200, 225))
    _grad(bg, (0, WY, ANCHO, ALTO - WY), (44, 150, 205), (6, 40, 112))
    for _ in range(90):
        pygame.draw.circle(bg, (255, 255, 245), (rnd.randint(0, ANCHO), rnd.randint(0, WY - 60)), rnd.choice((1, 1, 2)))
    # aurora boreal
    au = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for x in range(0, ANCHO, 4):
        base = 80 + math.sin(x * 0.006) * 36 + math.sin(x * 0.017 + 1) * 18
        h = 90 + math.sin(x * 0.011 + 2) * 40 + math.sin(x * 0.043) * 14
        for k in range(10):
            f = k / 9
            col = (int(70 + 120 * f), int(255 - 120 * f), int(140 + 90 * f))
            pygame.draw.line(au, (*col, int(80 * (1 - f) + 8)), (x, base + h * f - h * 0.2), (x, base + h * f - h * 0.2 + h / 9 + 1), 4)
    bg.blit(au, (0, 0))
    # montanas nevadas
    for pts, c in (([(-20, WY), (140, WY - 120), (260, WY - 40), (420, WY - 150), (600, WY)], (150, 180, 215)),
                   ([(300, WY), (520, WY - 90), (700, WY - 30), (860, WY)], (120, 156, 200))):
        pygame.draw.polygon(bg, c, pts)
    for px, py in ((140, WY - 120), (420, WY - 150)):
        pygame.draw.polygon(bg, (245, 250, 255), [(px, py), (px - 34, py + 44), (px - 10, py + 36), (px + 6, py + 52), (px + 34, py + 42)])
    # iceberg: parte visible + masa sumergida
    sub = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    pygame.draw.polygon(sub, (170, 225, 250, 70), [(850, WY), (1240, WY), (1210, WY + 130), (1110, WY + 240), (1010, WY + 200), (900, WY + 120)])
    pygame.draw.polygon(sub, (210, 240, 255, 60), [(900, WY), (1180, WY), (1130, WY + 110), (1010, WY + 160)])
    bg.blit(sub, (0, 0))
    pts = [(850, WY), (900, WY - 70), (950, WY - 56), (1010, WY - 140), (1060, WY - 96), (1120, WY - 120), (1180, WY - 50), (1240, WY)]
    pygame.draw.polygon(bg, (232, 246, 255), pts)
    pygame.draw.polygon(bg, (176, 212, 240), [(1010, WY - 140), (1060, WY - 96), (1040, WY), (990, WY)])
    pygame.draw.polygon(bg, (200, 228, 250), [(1120, WY - 120), (1180, WY - 50), (1240, WY), (1110, WY)])
    pygame.draw.lines(bg, (150, 190, 225), False, pts, 3)
    for x, w in ((330, 70), (520, 54), (640, 90), (180, 60)):                            # trozos de hielo
        pygame.draw.ellipse(bg, (236, 248, 255), (x, WY - 8, w, 18))
        pygame.draw.ellipse(bg, (150, 200, 235), (x, WY - 2, w, 12))
    pygame.draw.circle(bg, (255, 255, 255), (1210, 70), 0)
    _rayos(bg, rnd, 26, (220, 245, 255), 7, 50, 195)
    pygame.draw.rect(bg, (205, 238, 255), (0, WY, ANCHO, 5))
    sy = 648
    _suelo(bg, rnd, (150, 168, 188), sy, 12, 3)
    sil = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for _ in range(6):
        _roca(sil, rnd.randint(40, ANCHO - 40), sy + 6, rnd.randint(110, 220), rnd.randint(60, 150), (10, 50, 110, 120))
    bg.blit(sil, (0, 0))
    for x in range(50, ANCHO, 110):
        _alga(bg, x + rnd.randint(-25, 25), sy + 16, rnd.randint(110, 230), (46, 140, 104), rnd, 11)
    for x in (260, 760, 1130):
        _roca(bg, x, sy + 26, 190, 100, (120, 130, 150))
    for x in (140, 520, 980, 1220):                                                      # cristales de hielo
        for k, (dx, h) in enumerate(((-14, 40), (0, 62), (14, 44))):
            pygame.draw.polygon(bg, (200, 236, 255), [(x + dx - 9, sy + 20), (x + dx, sy + 20 - h), (x + dx + 9, sy + 20)])
            pygame.draw.polygon(bg, (240, 252, 255), [(x + dx - 3, sy + 20), (x + dx, sy + 20 - h), (x + dx + 3, sy + 20)])
    for x in (20, 70, 1210, 1260):
        _alga(fr, x, ALTO + 6, rnd.randint(170, 270), (40, 124, 92), rnd, 14)
    for x in (360, 900):
        pygame.draw.polygon(fr, (214, 242, 255, 230), [(x - 24, ALTO), (x, ALTO - 70), (x + 24, ALTO)])
    _particulas(fr, rnd, 50, (235, 250, 255), 2, a=90)


def _mundo4(bg, fr, rnd):
    _grad(bg, (0, 0, ANCHO, WY), (6, 10, 32), (30, 46, 86))
    _grad(bg, (0, WY, ANCHO, ALTO - WY), (6, 46, 76), (2, 6, 22))
    for _ in range(100):
        pygame.draw.circle(bg, (210, 225, 255), (rnd.randint(0, ANCHO), rnd.randint(0, WY - 30)), rnd.choice((1, 1, 2)))
    glow = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _brillo(glow, 980, 100, 150, (140, 200, 255), 70)
    bg.blit(glow, (0, 0))
    pygame.draw.circle(bg, (205, 225, 245), (980, 100), 38)
    pygame.draw.circle(bg, (150, 180, 210), (968, 92), 8)
    pygame.draw.circle(bg, (150, 180, 210), (992, 112), 6)
    for x in range(0, ANCHO, 80):                                                         # siluetas de la orilla
        h = rnd.randint(18, 56)
        pygame.draw.polygon(bg, (14, 22, 50), [(x, WY), (x + 40, WY - h), (x + 80, WY)])
    for x in (120, 360, 700, 1100):
        pygame.draw.circle(bg, (90, 230, 210), (x + rnd.randint(-10, 10), WY - 12), 3)
    cap = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for _ in range(5):                                                                    # luz tenue
        x0 = rnd.randint(100, 1100)
        pygame.draw.polygon(cap, (140, 230, 255, 12), [(x0, WY), (x0 + 40, WY), (x0 + 140, ALTO), (x0 + 30, ALTO)])
    bg.blit(cap, (0, 0))
    pygame.draw.rect(bg, (80, 130, 170), (0, WY, ANCHO, 4))
    sy = 648
    _suelo(bg, rnd, (22, 30, 52), sy, 14, 4)
    for x, w, h in ((150, 250, 170), (560, 300, 210), (980, 260, 180), (1230, 220, 150)):
        _roca(bg, x, sy + 30, w, h, (24, 34, 62))
    # arco de roca
    pygame.draw.arc(bg, (28, 40, 72), (330, sy - 190, 220, 360), 0, math.pi, 28)
    gl = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    # plantas luminosas
    paleta = [(60, 255, 220), (255, 90, 200), (110, 170, 255), (255, 220, 90)]
    for i, x in enumerate(range(60, ANCHO, 95)):
        c = paleta[i % 4]
        h = rnd.randint(60, 190)
        tipo = i % 3
        xx = x + rnd.randint(-20, 20)
        if tipo == 0:                                                                     # tubo con farol
            pts = [(xx + math.sin(k * 0.7 + i) * 10, sy + 14 - h * k / 8) for k in range(9)]
            pygame.draw.lines(bg, oscurecer(c, 0.55), False, pts, 8)
            pygame.draw.lines(bg, oscurecer(c, 0.3), False, pts, 4)
            _brillo(gl, pts[-1][0], pts[-1][1], 36, c, 90)
            pygame.draw.circle(bg, aclarar(c, 0.5), (int(pts[-1][0]), int(pts[-1][1])), 8)
        elif tipo == 1:                                                                   # hongo coral
            pygame.draw.line(bg, oscurecer(c, 0.55), (xx, sy + 14), (xx, sy - h * 0.6), 9)
            pygame.draw.ellipse(bg, oscurecer(c, 0.35), (xx - 34, sy - h * 0.6 - 18, 68, 34))
            for k in range(-2, 3):
                pygame.draw.circle(bg, c, (xx + k * 12, int(sy - h * 0.6 - 6)), 4)
                _brillo(gl, xx + k * 12, sy - h * 0.6 - 6, 14, c, 80, 4)
        else:                                                                             # ramas con puntos
            for dx in (-16, 0, 16):
                ex, ey = xx + dx * 1.6, sy - h * (0.7 + 0.1 * dx / 16)
                pygame.draw.line(bg, oscurecer(c, 0.5), (xx, sy + 14), (ex, ey), 5)
                _brillo(gl, ex, ey, 20, c, 90, 4)
                pygame.draw.circle(bg, aclarar(c, 0.5), (int(ex), int(ey)), 5)
    # medusas gigantes de fondo
    for x, y, r, c in ((260, 330, 40, (90, 200, 255)), (800, 400, 54, (255, 110, 210)), (1120, 310, 34, (110, 255, 210))):
        _medusa_fondo(bg, x, y, r, c, rnd)
        _brillo(gl, x, y + r * 0.7, r * 1.4, c, 40, 5)
    bg.blit(gl, (0, 0))
    for x in (40, 1240):
        _roca(fr, x, ALTO + 20, 230, 130, (14, 22, 44))
    gf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for x, c in ((130, (60, 255, 220)), (1150, (255, 90, 200))):
        pts = [(x + math.sin(k * 0.7) * 10, ALTO - 110 * k / 6) for k in range(7)]
        pygame.draw.lines(fr, oscurecer(c, 0.5), False, pts, 8)
        _brillo(gf, pts[-1][0], pts[-1][1], 40, c, 100)
        pygame.draw.circle(fr, aclarar(c, 0.5), (int(pts[-1][0]), int(pts[-1][1])), 8)
    fr.blit(gf, (0, 0))
    _particulas(fr, rnd, 70, (120, 255, 230), 3, a=140)


def _mundo5(bg, fr, rnd):
    _grad(bg, (0, 0, ANCHO, WY), (18, 10, 56), (110, 58, 130))
    _grad(bg, (0, WY, ANCHO, ALTO - WY), (42, 28, 118), (6, 2, 26))
    for _ in range(120):
        pygame.draw.circle(bg, (255, 245, 220), (rnd.randint(0, ANCHO), rnd.randint(0, WY - 20)), rnd.choice((1, 1, 2)))
    glow = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _brillo(glow, 300, 100, 190, (255, 220, 140), 70)
    bg.blit(glow, (0, 0))
    pygame.draw.circle(bg, (255, 232, 170), (300, 100), 52)
    pygame.draw.circle(bg, (232, 196, 130), (284, 90), 11)
    pygame.draw.circle(bg, (232, 196, 130), (318, 116), 8)
    for cx, cy, w in ((700, 80, 260), (1050, 130, 200), (140, 170, 180)):                # nubes de tormenta
        _nube(bg, cx, cy, w, (60, 40, 100))
    pygame.draw.polygon(bg, (255, 220, 120), [(1000, 0), (1014, 60), (1004, 62), (1022, 130), (990, 70), (1002, 68)])
    pygame.draw.polygon(bg, (24, 14, 60), [(850, WY), (940, WY - 60), (1010, WY - 20), (1090, WY - 80), (1200, WY)])
    # rayos dorados que bajan hasta las ruinas
    _rayos(bg, rnd, 30, (255, 215, 120), 6, 70, 220)
    cap = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    pygame.draw.polygon(cap, (255, 210, 110, 34), [(500, WY), (700, WY), (880, ALTO), (380, ALTO)])
    bg.blit(cap, (0, 0))
    pygame.draw.rect(bg, (160, 120, 200), (0, WY, ANCHO, 4))
    sy = 648
    _suelo(bg, rnd, (44, 34, 78), sy, 12, 5)
    # ruinas: escalinata, arco y columnas
    ruina = (86, 74, 124)
    for i in range(5):
        pygame.draw.rect(bg, aclarar(ruina, 0.04 * i), (470 - i * 22, sy + 8 - 16 * (i + 1) , 340 + i * 44, 16))
        pygame.draw.rect(bg, oscurecer(ruina, 0.4), (470 - i * 22, sy + 8 - 16 * (i + 1), 340 + i * 44, 16), 2)
    for x, h, rt in ((380, 230, False), (440, 160, True), (840, 250, False), (910, 120, True), (150, 200, True), (1100, 190, False)):
        _columna(bg, x, sy + 14, h, 40, ruina, rt)
    pygame.draw.rect(bg, aclarar(ruina, 0.06), (352, sy - 270, 520, 24))
    pygame.draw.rect(bg, oscurecer(ruina, 0.4), (352, sy - 270, 520, 24), 3)
    pygame.draw.polygon(bg, aclarar(ruina, 0.1), [(352, sy - 270), (612, sy - 330), (872, sy - 270)])
    pygame.draw.polygon(bg, oscurecer(ruina, 0.4), [(352, sy - 270), (612, sy - 330), (872, sy - 270)], 3)
    # portal con runas doradas
    gl = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _brillo(gl, 612, sy - 130, 120, (255, 200, 90), 70)
    pygame.draw.circle(bg, (255, 210, 110), (612, sy - 130), 62, 6)
    pygame.draw.circle(bg, (150, 100, 230), (612, sy - 130), 46, 3)
    for k in range(6):
        a = k * math.pi / 3
        _runa(bg, 612 + math.cos(a) * 54, sy - 130 + math.sin(a) * 54, 7, (255, 225, 140))
    for x in (230, 1010, 1190):                                                           # gemas luminosas en el suelo
        for k in range(3):
            c = (255, 205, 90) if k % 2 == 0 else (180, 110, 255)
            gx, gy = x + k * 22, sy + 24 - k % 2 * 10
            _brillo(gl, gx, gy, 26, c, 90, 4)
            pygame.draw.polygon(bg, aclarar(c, 0.3), [(gx, gy - 16), (gx + 8, gy), (gx, gy + 6), (gx - 8, gy)])
    # cadenas colgando
    for x in (700, 760):
        for k in range(10):
            pygame.draw.ellipse(bg, (110, 96, 140), (x - 5 + (k % 2) * 2, WY + 12 + k * 14, 10, 16), 3)
    bg.blit(gl, (0, 0))
    # niebla violeta
    nb = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for i in range(7):
        pygame.draw.ellipse(nb, (150, 90, 230, 22), (rnd.randint(-200, ANCHO - 200), rnd.randint(WY + 160, ALTO - 40), rnd.randint(500, 900), 70))
    bg.blit(nb, (0, 0))
    for x in (30, 1250):
        _columna(fr, x, ALTO + 6, 340, 70, (58, 46, 98), rota=(x < 600))
    gf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for x in (140, 1140):
        _brillo(gf, x, ALTO - 40, 40, (255, 205, 90), 100, 5)
        pygame.draw.polygon(fr, (255, 225, 140), [(x, ALTO - 62), (x + 10, ALTO - 40), (x, ALTO - 28), (x - 10, ALTO - 40)])
    fr.blit(gf, (0, 0))
    _particulas(fr, rnd, 60, (255, 215, 120), 3, a=150)
    _particulas(fr, rnd, 30, (190, 140, 255), 2, a=130)


_MUNDOS_FONDO = {1: _mundo1, 2: _mundo2, 3: _mundo3, 4: _mundo4, 5: _mundo5}


def fondo_mundo(mundo):
    """(fondo, frente) del mundo 1..5: 1 normal, 2 submarino, 3 polar, 4 subnautica, 5 legendario."""
    mundo = max(1, min(5, int(mundo)))
    if mundo in _cache_mundos:
        return _cache_mundos[mundo]
    rnd = random.Random(mundo * 101 + 7)
    bg = pygame.Surface((ANCHO, ALTO))
    fr = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _MUNDOS_FONDO[mundo](bg, fr, rnd)
    _cache_mundos[mundo] = (bg, fr)
    return bg, fr



# ----------------------------------------------------------------------------- herramientas de pesca (1 a 5 estrellas)
_BORDE_H = (50, 36, 30)


class _T:
    """Pincel de herramienta: coordenadas locales centradas en (x, y), escala e."""

    def __init__(self, p, x, y, e):
        self.p, self.x, self.y, self.e = p, x, y, e

    def q(self, u, v):
        return (self.x + u * self.e, self.y + v * self.e)

    def w(self, g):
        return max(1, int(g * self.e + 0.4))

    def poli(self, pts, col, borde=_BORDE_H, g=2.0):
        q = [self.q(*a) for a in pts]
        pygame.draw.polygon(self.p, col, q)
        if borde:
            pygame.draw.polygon(self.p, borde, q, self.w(g))

    def lin(self, a, b, col, g=3.0):
        pygame.draw.line(self.p, col, self.q(*a), self.q(*b), self.w(g))

    def lineas(self, pts, col, g=3.0):
        pygame.draw.lines(self.p, col, False, [self.q(*a) for a in pts], self.w(g))

    def circ(self, c, r, col, borde=_BORDE_H, g=2.0):
        qc = (int(self.q(*c)[0]), int(self.q(*c)[1]))
        pygame.draw.circle(self.p, col, qc, max(1, int(r * self.e)))
        if borde:
            pygame.draw.circle(self.p, borde, qc, max(1, int(r * self.e)), self.w(g))

    def el(self, c, ancho, alto, col, borde=_BORDE_H, g=2.0):
        r = pygame.Rect(0, 0, max(2, int(ancho * self.e)), max(2, int(alto * self.e)))
        r.center = (int(self.q(*c)[0]), int(self.q(*c)[1]))
        pygame.draw.ellipse(self.p, col, r)
        if borde:
            pygame.draw.ellipse(self.p, borde, r, self.w(g))

    def chispa(self, c, r, col=(255, 255, 255)):
        x, y = self.q(*c)
        r = r * self.e
        pygame.draw.polygon(self.p, col, [(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28),
                                           (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)])

    def tubo(self, a, b, col, g0, g1, borde=_BORDE_H, n=48):
        """Segmento ahusado de a a b (grosor g0 -> g1) con borde."""
        for paso, extra in ((borde, 1.8), (None, 0)):
            c = paso if paso else col
            if c is None:
                continue
            for i in range(n):
                f = i / (n - 1)
                u, v = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                g = g0 + (g1 - g0) * f + extra
                pygame.draw.circle(self.p, c, (int(self.q(u, v)[0]), int(self.q(u, v)[1])), max(1, int(g * self.e / 2 + 0.4)))


_EST_CANA = {
    1: dict(vara=(214, 178, 96), vara_o=(150, 112, 56), grip=(150, 98, 60), carrete=None, guia=(120, 110, 100), linea=(240, 240, 240), gema=None, oro=None),
    2: dict(vara=(150, 100, 60), vara_o=(100, 64, 38), grip=(110, 70, 46), carrete=((150, 156, 168), 8), guia=(190, 195, 205), linea=(240, 240, 240), gema=None, oro=None),
    3: dict(vara=(70, 176, 190), vara_o=(30, 96, 112), grip=(212, 170, 110), carrete=((190, 200, 220), 10), guia=(220, 228, 240), linea=(240, 250, 255), gema=None, oro=None),
    4: dict(vara=(54, 60, 78), vara_o=(26, 28, 40), grip=(60, 44, 40), carrete=((236, 196, 84), 11), guia=(240, 200, 90), linea=(220, 240, 255), gema=None, oro=(240, 196, 84)),
    5: dict(vara=(250, 236, 190), vara_o=(170, 130, 50), grip=(70, 40, 120), carrete=((255, 214, 90), 12), guia=(120, 240, 245), linea=(150, 250, 255), gema=(110, 235, 245), oro=(255, 214, 90)),
}


def _cana(h, est):
    st = _EST_CANA[est]
    a, b = (-34, 40), (38, -44)                                    # mango y punta
    # linea y señuelo
    if est >= 3:
        h.lineas([(38, -44), (46, -14), (42, 20)], st["linea"], 1.4)
    else:
        h.lineas([(38, -44), (44, -10), (40, 18)], st["linea"], 1.4)
    if est == 1:
        h.circ((40, 22), 4.5, (240, 70, 60))
        h.poli([(36, 22), (44, 22), (40, 28)], (255, 255, 255), g=1.2)
    elif est == 2:
        h.circ((40, 24), 4, (255, 210, 60))
    else:
        h.poli([(40, 20), (35, 28), (40, 25), (45, 28)], (230, 235, 245), g=1.2)
    # vara
    h.tubo(a, b, st["vara"], 8.5, 2.6, st["vara_o"])
    if est == 1:
        for f in (0.35, 0.55, 0.75):                               # nudos del bambu
            u, v = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            h.lin((u - 3, v - 2), (u + 3, v + 3), st["vara_o"], 2.2)
    if est >= 3:
        for f in (0.30, 0.52, 0.72, 0.9):                          # anillas guia
            u, v = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            h.circ((u + 3, v - 3), 2.4 - f * 0.8, st["guia"], st["vara_o"], 1.2)
    elif est == 2:
        for f in (0.45, 0.7, 0.92):
            u, v = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            h.circ((u + 2, v - 2), 1.8, st["guia"], st["vara_o"], 1.0)
    if st["oro"]:
        for f in (0.18, 0.46, 0.72):                               # anillos dorados
            u, v = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            h.lin((u - 3.5, v - 3), (u + 3.5, v + 3), st["oro"], 3.2)
    # empunadura
    ga, gb = (-34, 40), (-16, 16)
    h.tubo(ga, gb, st["grip"], 11, 9.5, _BORDE_H)
    if est == 1:
        for f in (0.2, 0.45, 0.7):
            h.lin((ga[0] + (gb[0] - ga[0]) * f - 4, ga[1] + (gb[1] - ga[1]) * f - 2), (ga[0] + (gb[0] - ga[0]) * f + 4, ga[1] + (gb[1] - ga[1]) * f + 3), (230, 210, 160), 1.8)
    if est >= 3:
        h.circ(ga, 6, st["oro"] or (210, 214, 224), g=1.6)
    # carrete
    if st["carrete"]:
        col, r = st["carrete"]
        cx, cy = -14, 22
        h.lin((-18, 16), (cx, cy + 4), _BORDE_H, 3.5)
        h.circ((cx, cy + 8), r, col)
        h.circ((cx, cy + 8), r * 0.55, oscurecer(col, 0.25), g=1.4)
        h.lin((cx, cy + 8), (cx + r * 0.95, cy + 8 - r * 0.6), _BORDE_H, 2.2)
        h.circ((cx + r * 0.95, cy + 8 - r * 0.6), 2.3, st["oro"] or (80, 80, 90), g=1.2)
        if est >= 4:
            h.circ((cx, cy + 8), r * 0.22, (255, 255, 255), g=1.0)
    if st["gema"]:
        h.poli([(-14, 14), (-9, 18), (-14, 24), (-19, 18)], st["gema"], (30, 100, 120), 1.4)
        h.poli([(38, -50), (42, -46), (38, -42), (34, -46)], st["gema"], (30, 100, 120), 1.2)
        h.chispa((-6, -22), 6, (255, 255, 255))
        h.chispa((24, -14), 4.5, (255, 250, 200))


_EST_CUERDA = {
    1: dict(c=(216, 188, 132), c_o=(150, 118, 70), n=2, trenza=False, extra=None),
    2: dict(c=(112, 204, 150), c_o=(52, 120, 84), n=3, trenza=False, extra="etiqueta"),
    3: dict(c=(84, 134, 226), c_o=(36, 66, 140), n=3, trenza=True, extra="etiqueta"),
    4: dict(c=(204, 214, 232), c_o=(100, 112, 140), n=4, trenza=True, extra="clip"),
    5: dict(c=(255, 214, 96), c_o=(160, 110, 30), n=4, trenza=True, extra="gema"),
}


def _cuerda(h, est):
    st = _EST_CUERDA[est]
    n = st["n"]
    # carrete de madera/metal detras
    base = (150, 104, 66) if est < 4 else ((120, 126, 146) if est == 4 else (250, 205, 90))
    h.el((0, 6), 78, 60, oscurecer(base, 0.1), g=2.4)
    h.el((0, -4), 78, 60, base, g=2.4)
    # vueltas del cordel (elipses concentricas)
    for i in range(n):
        rw, rh = 36 - i * 6.5, 25 - i * 4.5
        h.el((0, -4), rw * 2 - 4, rh * 2 - 4, st["c"], st["c_o"], 3.0)
        if st["trenza"]:
            for k in range(14):
                a = k * math.tau / 14
                u, v = math.cos(a) * (rw - 1), -4 + math.sin(a) * (rh - 1)
                h.lin((u - 2, v - 1.5), (u + 2, v + 1.5), st["c_o"], 1.6)
    h.el((0, -4), 24, 14, oscurecer(base, 0.35), g=2.0)                            # hueco central
    h.circ((0, -4), 3, (240, 235, 220), g=1.2)
    # punta suelta
    h.lineas([(30, 2), (42, 12), (38, 30), (46, 38)], st["c"], 3.4)
    h.lineas([(30, 2), (42, 12), (38, 30), (46, 38)], st["c_o"], 1.2)
    if st["extra"] == "etiqueta":
        h.poli([(-8, 20), (10, 20), (10, 34), (-8, 34)], (250, 245, 225), g=1.4)
        h.lin((-4, 25), (6, 25), st["c_o"], 1.6)
        h.lin((-4, 30), (3, 30), st["c_o"], 1.6)
    if st["extra"] == "clip":
        h.circ((46, 40), 4.2, (210, 214, 226), g=1.6)
        h.lin((46, 44), (46, 54), (210, 214, 226), 3)
        h.chispa((-30, -26), 5)
    if st["extra"] == "gema":
        h.poli([(46, 34), (51, 40), (46, 48), (41, 40)], (110, 235, 245), (30, 100, 120), 1.4)
        h.chispa((-30, -26), 6)
        h.chispa((30, -22), 4.5, (255, 250, 200))
        h.chispa((-4, 22), 4, (200, 255, 255))


_EST_ANZUELO = {
    1: dict(c=(150, 156, 166), c_o=(80, 86, 98), g=7.0, barba=False, extra=None),
    2: dict(c=(190, 198, 212), c_o=(96, 104, 122), g=7.5, barba=True, extra="ojo"),
    3: dict(c=(104, 160, 226), c_o=(40, 80, 150), g=8.0, barba=True, extra="lombriz"),
    4: dict(c=(246, 204, 90), c_o=(150, 100, 20), g=8.5, barba=True, extra="plumas"),
    5: dict(c=(140, 240, 250), c_o=(30, 110, 140), g=9.0, barba=True, extra="gema"),
}


def _anzuelo(h, est):
    st = _EST_ANZUELO[est]
    pts = [(0, -40), (0, 8)]
    cx, cy, r = 18, 8, 18
    for k in range(1, 15):
        a = math.pi - k * math.pi / 14 * 1.0
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append((36, -10))
    # linea que baja
    h.lineas([(0, -52), (0, -40)], (240, 240, 245), 1.8)
    for col, g in ((st["c_o"], st["g"] + 3.0), (st["c"], st["g"])):
        h.lineas(pts, col, g)
        for (u, v) in (pts[0], pts[-1]):
            pygame.draw.circle(h.p, col, (int(h.q(u, v)[0]), int(h.q(u, v)[1])), max(1, int(g * h.e / 2)))
    h.lineas(pts[:7], aclarar(st["c"], 0.5), max(1.2, st["g"] * 0.22))
    if st["barba"]:
        h.poli([(37, -11), (27, 0), (36, -3)], st["c"], st["c_o"], 1.5)
    # ojo (donde se ata la linea)
    h.circ((0, -44), 5.5, st["c"], st["c_o"], 2.0)
    h.circ((0, -44), 2.4, (60, 50, 60), None)
    h.lineas([(0, -49), (0, -56)], (240, 240, 245), 1.8)
    if st["extra"] == "lombriz":
        h.lineas([(14, 21), (22, 16), (26, 22), (34, 18), (38, 26)], (240, 140, 150), 5)
        h.lineas([(14, 21), (22, 16), (26, 22), (34, 18), (38, 26)], (255, 190, 195), 1.8)
    elif st["extra"] == "plumas":
        for dx, col in ((-9, (230, 70, 70)), (9, (80, 150, 240)), (0, (255, 230, 90))):
            h.poli([(0, -30), (dx * 1.8, -24), (dx * 1.3, -8), (0, -14)], col, _BORDE_H, 1.2)
        h.chispa((34, -30), 4.5, (255, 245, 190))
    elif st["extra"] == "gema":
        h.poli([(34, 16), (40, 22), (34, 30), (28, 22)], (110, 235, 245), (30, 100, 120), 1.4)
        h.chispa((-16, -22), 6)
        h.chispa((38, -14), 4.5, (255, 250, 200))
        h.chispa((6, 28), 4, (200, 255, 255))

_HERR_PESCA = {"cana": _cana, "cuerda": _cuerda, "anzuelo": _anzuelo}


def dibujar_herramienta_pesca(p, tipo, x, y, escala=1.0, estrellas=0):
    """Herramienta de pesca ('cana', 'cuerda' o 'anzuelo') centrada en (x, y), ~100*escala px de alto.
    El aspecto mejora con las estrellas (1 a 5); con estrellas > 0 dibuja esas estrellas debajo."""
    est = max(1, min(5, int(estrellas or 1)))
    h = _T(p, x, y, escala)
    _HERR_PESCA.get(tipo, _cana)(h, est)
    if estrellas > 0:
        n = min(5, int(estrellas))
        r = 9 * escala
        sep = 21 * escala
        cy = y + 62 * escala
        x0 = x - (n - 1) * sep / 2
        for i in range(n):
            estrella(p, int(x0 + i * sep), int(cy), max(3, int(r)), (255, 210, 60), (160, 110, 20))


# ----------------------------------------------------------------------------- materiales de pesca
def _color_hash(ident):
    h = zlib.crc32(ident.encode("utf-8"))
    hue = (h % 360)
    c = pygame.Color(0)
    c.hsva = (hue, 55 + (h >> 9) % 30, 90, 100)
    return (c.r, c.g, c.b), h


def _m_escama(h):
    for i, (u, v) in enumerate(((-9, 4), (9, 4), (0, -6))):
        h.el((u, v), 28, 26, (160, 205, 235), (60, 110, 160), 2.0)
        for k in (-6, 0, 6):
            h.lin((u + k * 0.3, v - 8), (u + k * 0.8, v + 8), (230, 245, 255), 1.2)
        h.lineas([(u - 8, v + 2), (u, v + 8), (u + 8, v + 2)], (90, 140, 190), 1.2)
    h.chispa((12, -14), 4)


def _m_perla(h):
    h.circ((0, 2), 15, (248, 244, 250), (150, 140, 170), 2.0)
    h.circ((0, 4), 11, (255, 226, 240), None)
    h.circ((-5, -4), 4.5, (255, 255, 255), None)
    h.chispa((12, -12), 4)


def _m_hielo(h):
    h.poli([(0, -22), (14, -8), (10, 16), (-4, 22), (-16, 6), (-12, -10)], (196, 232, 252), (70, 130, 190), 2.2)
    h.poli([(0, -22), (14, -8), (2, -2)], (236, 250, 255), None)
    h.poli([(-12, -10), (0, -22), (2, -2), (-16, 6)], (220, 242, 255), None)
    h.lin((2, -2), (-4, 22), (130, 190, 235), 1.6)
    h.lin((2, -2), (10, 16), (130, 190, 235), 1.6)
    h.chispa((12, -16), 4)


def _m_cristal(h):
    for u, v, w, hh, c in ((-10, 6, 9, 22, (160, 130, 240)), (10, 8, 8, 18, (120, 200, 250)), (0, 2, 11, 30, (200, 150, 250))):
        h.poli([(u - w, v + 14), (u - w * 0.7, v - hh * 0.5), (u, v - hh), (u + w * 0.7, v - hh * 0.5), (u + w, v + 14)], c, oscurecer(c, 0.5), 1.8)
        h.lin((u - w * 0.2, v - hh * 0.8), (u - w * 0.4, v + 10), aclarar(c, 0.5), 1.6)
    h.chispa((14, -16), 4)


def _m_tinta(h):
    h.poli([(0, -22), (12, 2), (14, 12), (6, 20), (-6, 20), (-14, 12), (-12, 2)], (60, 40, 110), (24, 14, 50), 2.2)
    h.el((-4, 8), 9, 14, (120, 90, 180), None)
    h.chispa((8, -4), 3, (200, 180, 255))


def _m_diente(h):
    h.poli([(-12, -18), (12, -18), (13, -6), (6, 14), (0, 22), (-6, 14), (-13, -6)], (250, 246, 228), (150, 130, 100), 2.2)
    h.lin((-4, -12), (-4, 8), (255, 255, 255), 2.2)
    h.lin((12, -18), (-12, -18), (200, 180, 140), 2.0)


def _m_alga(h):
    for k, (u, c) in enumerate(((-9, (60, 160, 90)), (0, (80, 190, 110)), (9, (50, 140, 100)))):
        pts = [(u + math.sin(i * 0.9 + k) * 5, 20 - i * 5.2) for i in range(8)]
        h.lineas(pts, oscurecer(c, 0.5), 8.5)
        h.lineas(pts, c, 5.5)
    h.chispa((13, -14), 3.5)


def _m_concha(h):
    h.poli([(-4, 18), (-20, 4), (-14, -12), (0, -18), (14, -12), (20, 4), (4, 18)], (250, 190, 200), (170, 100, 120), 2.2)
    for k in range(-3, 4):
        h.lin((0, 16), (k * 5.5, -14 + abs(k) * 2), (235, 150, 170), 1.6)
    h.poli([(-6, 18), (6, 18), (4, 24), (-4, 24)], (200, 120, 140), (130, 70, 90), 1.6)


def _m_hilo(h):
    h.el((0, 14), 40, 12, (150, 104, 66), (90, 60, 38), 2.0)
    h.poli([(-17, -12), (17, -12), (17, 14), (-17, 14)], (110, 190, 235), (50, 110, 160), 2.0)
    for k in range(6):
        h.lin((-17, -8 + k * 4), (17, -4 + k * 4), (220, 240, 255), 1.5)
    h.el((0, -12), 40, 12, (150, 104, 66), (90, 60, 38), 2.0)
    h.lineas([(17, -4), (26, 0), (24, 14)], (220, 240, 255), 2)


def _m_aleta(h):
    h.poli([(-16, 18), (-18, -4), (-8, -18), (4, -8), (14, -14), (18, 4), (10, 18)], (120, 190, 235), (50, 100, 160), 2.2)
    for k in range(-3, 4):
        h.lin((0, 18), (k * 5.5, -12 + abs(k) * 2), (200, 232, 252), 1.4)


def _m_coral(h):
    c = (240, 100, 110)
    for a, b in (((0, 20), (0, -18)), ((0, 4), (-14, -12)), ((0, 8), (14, -8)), ((-8, 10), (-18, 0)), ((6, -4), (12, -20))):
        h.lin(a, b, oscurecer(c, 0.45), 9)
    for a, b in (((0, 20), (0, -18)), ((0, 4), (-14, -12)), ((0, 8), (14, -8)), ((-8, 10), (-18, 0)), ((6, -4), (12, -20))):
        h.lin(a, b, c, 6)
        h.circ(b, 3.4, aclarar(c, 0.35), None)


def _m_ambar(h):
    pts = [(math.cos(a * math.pi / 3) * 17, math.sin(a * math.pi / 3) * 17) for a in range(6)]
    h.poli(pts, (250, 180, 60), (150, 90, 20), 2.2)
    h.poli([(-8, -6), (4, -12), (2, -2), (-8, 2)], (255, 225, 140), None)
    h.circ((6, 6), 2.2, (160, 100, 30), None)
    h.chispa((10, -12), 3.5)


def _m_espina(h):
    h.poli([(-6, 20), (6, 20), (2, -4), (0, -22), (-2, -4)], (240, 230, 210), (130, 110, 90), 2.0)
    h.lin((0, 18), (0, -16), (190, 170, 140), 1.4)
    h.poli([(-12, 20), (12, 20), (12, 24), (-12, 24)], (180, 150, 120), (110, 80, 60), 1.4)


def _m_pepita(h):
    h.poli([(-16, 12), (-12, -4), (0, -14), (14, -6), (18, 10), (4, 18)], (255, 214, 90), (160, 110, 20), 2.2)
    h.poli([(-6, -4), (2, -10), (8, -2), (-2, 4)], (255, 240, 170), None)
    h.chispa((12, -14), 4)


_MATERIALES_ICONO = {
    "escama": _m_escama, "perla": _m_perla, "hielo": _m_hielo, "cristal": _m_cristal, "tinta": _m_tinta,
    "diente": _m_diente, "alga": _m_alga, "concha": _m_concha, "hilo": _m_hilo, "aleta": _m_aleta,
    "coral": _m_coral, "ambar": _m_ambar, "espina": _m_espina, "pepita": _m_pepita, "oro": _m_pepita,
}


def dibujar_material_pesca(p, ident, x, y, escala=1.0):
    """Icono de un material de pesca (~48*escala px). Los ids conocidos tienen dibujo propio (escama, perla, hielo,
    cristal, tinta, diente, alga, concha, hilo, aleta, coral, ambar, espina, pepita); cualquier otro id recibe un
    dibujo generico (orbe, gema, esquirla o gota) con un color que sale del propio id."""
    h = _T(p, x, y, escala * 0.95)
    f = _MATERIALES_ICONO.get(ident)
    if f is None:
        for k, fn in _MATERIALES_ICONO.items():                    # ids compuestos: 'escama_dorada' -> escama
            if ident.startswith(k):
                f = fn
                break
    if f is not None:
        f(h)
        return
    col, hv = _color_hash(ident)
    borde = oscurecer(col, 0.55)
    forma = hv % 4
    if forma == 0:                                                 # orbe
        h.circ((0, 0), 15, col, borde, 2.2)
        h.circ((-5, -5), 4.5, aclarar(col, 0.6), None)
    elif forma == 1:                                               # gema
        h.poli([(-14, -4), (-6, -16), (6, -16), (14, -4), (0, 18)], col, borde, 2.2)
        h.lineas([(-14, -4), (14, -4)], aclarar(col, 0.4), 1.6)
        h.lin((-6, -16), (0, -4), aclarar(col, 0.4), 1.4)
        h.lin((6, -16), (0, -4), aclarar(col, 0.4), 1.4)
    elif forma == 2:                                               # esquirla
        h.poli([(-6, 20), (-14, 0), (-2, -20), (8, -6), (14, 12)], col, borde, 2.2)
        h.lin((-2, -16), (0, 10), aclarar(col, 0.5), 1.6)
    else:                                                          # gota
        h.poli([(0, -20), (12, 2), (14, 10), (6, 18), (-6, 18), (-14, 10), (-12, 2)], col, borde, 2.2)
        h.el((-4, 6), 8, 12, aclarar(col, 0.5), None)
    h.chispa((12, -14), 3.5)
