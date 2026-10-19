"""Dibujos de la Cocina: platos terminados, ingredientes, iconos de herramientas y adornos del libro.

Todo es procedural. Los platos se dibujan con `plato_completo(p, tipo, cont, ing, cx, cy, r)`
(plato blanco + comida) o solo la comida con `comida(...)`.
"""

import math

import pygame

from nucleo import aclarar, oscurecer
import arte

PAPEL = (252, 244, 222)
PAPEL_SOMBRA = (232, 219, 188)
CUERO = (126, 78, 48)
CUERO_OSC = (84, 50, 30)


def _c(p, col, x, y, r, borde=None, w=2):
    pygame.draw.circle(p, col, (int(x), int(y)), max(1, int(r)))
    if borde:
        pygame.draw.circle(p, borde, (int(x), int(y)), max(1, int(r)), w)


def _e(p, col, x, y, w, h, borde=None, bw=2):
    r = pygame.Rect(int(x - w / 2), int(y - h / 2), max(2, int(w)), max(2, int(h)))
    pygame.draw.ellipse(p, col, r)
    if borde:
        pygame.draw.ellipse(p, borde, r, bw)


# ----------------------------------------------------------------------------- comida
def comida(p, tipo, cont, ing, cx, cy, r):
    """Dibuja solo la comida, centrada en (cx, cy), cabe en un circulo de radio r."""
    cx, cy = int(cx), int(cy)
    fn = _TIPOS.get(tipo, _sopa)
    fn(p, cont, ing, cx, cy, r)


def _sopa(p, c, ing, cx, cy, r):
    _c(p, oscurecer(c, 0.25), cx, cy, r * 0.78)
    _c(p, c, cx, cy, r * 0.72)
    for i in range(9):
        a = i * 0.85
        d = r * (0.18 + 0.4 * ((i * 37) % 10) / 10)
        _c(p, ing, cx + math.cos(a) * d, cy + math.sin(a) * d, r * 0.11, oscurecer(ing, 0.3), 1)
    _c(p, aclarar(c, 0.5), cx - r * 0.3, cy - r * 0.3, r * 0.07)


def _ensalada(p, c, ing, cx, cy, r):
    for i in range(10):
        a = i * 0.63
        col = (110, 200, 90) if i % 2 else (75, 165, 70)
        _e(p, col, cx + math.cos(a) * r * 0.42, cy + math.sin(a) * r * 0.42, r * 0.56, r * 0.4)
    _e(p, (130, 215, 100), cx, cy, r * 0.6, r * 0.44)
    for a in (0.4, 1.9, 3.3, 4.7, 5.6):
        _c(p, (225, 60, 60), cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.5, r * 0.13)
        _c(p, (255, 150, 150), cx + math.cos(a) * r * 0.5 - 3, cy + math.sin(a) * r * 0.5 - 3, r * 0.04)


def _pizza(p, c, ing, cx, cy, r):
    _c(p, (225, 170, 90), cx, cy, r * 0.92)
    _c(p, c, cx, cy, r * 0.8)
    _c(p, (250, 215, 90), cx, cy, r * 0.72)
    for a in range(4):
        ang = a * math.pi / 2 + 0.4
        pygame.draw.line(p, (225, 170, 90), (cx, cy), (cx + math.cos(ang) * r * 0.9, cy + math.sin(ang) * r * 0.9), 3)
    for a, d in ((0.2, 0.5), (1.5, 0.45), (2.7, 0.55), (4.0, 0.4), (5.2, 0.55), (0.9, 0.15)):
        _c(p, (200, 60, 50), cx + math.cos(a) * r * d, cy + math.sin(a) * r * d, r * 0.13, (150, 40, 35), 2)
    _c(p, (90, 170, 70), cx + r * 0.1, cy - r * 0.55, r * 0.06)
    _c(p, (90, 170, 70), cx - r * 0.5, cy + r * 0.2, r * 0.06)


def _tortilla(p, c, ing, cx, cy, r):
    _c(p, (205, 145, 55), cx, cy, r * 0.88)
    _c(p, c, cx, cy, r * 0.8)
    for a, d in ((0.3, 0.4), (1.7, 0.5), (3.0, 0.3), (4.4, 0.5), (5.5, 0.35)):
        _c(p, (235, 190, 80), cx + math.cos(a) * r * d, cy + math.sin(a) * r * d, r * 0.12)
    _c(p, (255, 245, 170), cx - r * 0.3, cy - r * 0.3, r * 0.08)


def _frutas(p, c, ing, cx, cy, r):
    _c(p, (250, 235, 205), cx, cy, r * 0.82, (215, 190, 150), 3)
    cols = [(215, 50, 50), (245, 150, 40), (140, 205, 80), (250, 215, 70), (170, 90, 190), (215, 50, 50),
            (245, 150, 40), (140, 205, 80), (250, 215, 70)]
    for i, col in enumerate(cols):
        a = i * 2.4
        d = r * (0.12 + 0.5 * ((i * 5) % 9) / 9)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        rr = pygame.Rect(0, 0, int(r * 0.3), int(r * 0.3))
        rr.center = (int(x), int(y))
        pygame.draw.rect(p, col, rr, border_radius=int(r * 0.09))
        pygame.draw.rect(p, oscurecer(col, 0.35), rr, 2, border_radius=int(r * 0.09))
    _c(p, (255, 255, 255), cx - r * 0.1, cy - r * 0.05, r * 0.05)


def _jugo(p, c, ing, cx, cy, r):
    top, bot, h = r * 0.62, r * 0.42, r * 1.3
    y0 = cy - h * 0.5
    pygame.draw.line(p, (230, 90, 90), (cx + r * 0.1, y0 - r * 0.28), (cx + r * 0.32, y0 + h * 0.5), int(max(3, r * 0.08)))
    pts = [(cx - top, y0), (cx + top, y0), (cx + bot, y0 + h), (cx - bot, y0 + h)]
    pygame.draw.polygon(p, (225, 240, 252), pts)
    liq = [(cx - top * 0.93, y0 + h * 0.18), (cx + top * 0.93, y0 + h * 0.18), (cx + bot * 0.95, y0 + h * 0.97),
           (cx - bot * 0.95, y0 + h * 0.97)]
    pygame.draw.polygon(p, c, liq)
    pygame.draw.polygon(p, aclarar(c, 0.5), [(cx - top * 0.7, y0 + h * 0.3), (cx - top * 0.5, y0 + h * 0.3),
                                              (cx - bot * 0.45, y0 + h * 0.85), (cx - bot * 0.65, y0 + h * 0.85)])
    pygame.draw.polygon(p, (120, 130, 155), pts, 3)
    _c(p, (250, 170, 50), cx + top * 0.95, y0 + 2, r * 0.22, (200, 110, 20), 3)
    _c(p, (255, 215, 130), cx + top * 0.95, y0 + 2, r * 0.13)


def _tostada(p, c, ing, cx, cy, r):
    w = r * 1.4
    rr = pygame.Rect(0, 0, int(w), int(r * 1.3))
    rr.center = (cx, cy + int(r * 0.08))
    pygame.draw.rect(p, (185, 125, 60), rr, border_radius=int(r * 0.3))
    for dx in (-0.28, 0.28):
        _c(p, (185, 125, 60), cx + dx * r * 1.4, rr.top + 2, r * 0.36)
    inn = rr.inflate(-int(r * 0.2), -int(r * 0.2))
    pygame.draw.rect(p, (245, 215, 150), inn, border_radius=int(r * 0.22))
    pygame.draw.rect(p, c, inn.inflate(-int(r * 0.2), -int(r * 0.2)), border_radius=int(r * 0.18))
    pygame.draw.line(p, aclarar(c, 0.5), (inn.x + r * 0.25, inn.y + r * 0.28), (inn.x + r * 0.7, inn.y + r * 0.28), 4)
    pygame.draw.rect(p, (255, 240, 130), (cx + r * 0.1, cy - r * 0.15, r * 0.3, r * 0.22), border_radius=3)


def _panqueques(p, c, ing, cx, cy, r):
    for i in range(3):
        y = cy + r * 0.28 - i * r * 0.26
        _e(p, (190, 125, 55), cx, y + r * 0.1, r * 1.5, r * 0.5)
        _e(p, (235, 180, 90), cx, y, r * 1.5, r * 0.5, (190, 125, 55), 2)
    _e(p, c, cx, cy - r * 0.42, r * 1.1, r * 0.34)
    for dx in (-0.55, -0.15, 0.4):
        pygame.draw.rect(p, c, (cx + dx * r, cy - r * 0.42, r * 0.14, r * 0.5), border_radius=6)
    pygame.draw.rect(p, (255, 240, 130), (cx - r * 0.18, cy - r * 0.62, r * 0.36, r * 0.22), border_radius=4)
    pygame.draw.rect(p, (200, 160, 40), (cx - r * 0.18, cy - r * 0.62, r * 0.36, r * 0.22), 2, border_radius=4)


def _arroz(p, c, ing, cx, cy, r):
    _e(p, (240, 240, 235), cx, cy + r * 0.1, r * 1.5, r * 1.1, (200, 200, 195), 3)
    for i in range(24):
        a = i * 2.39
        d = r * 0.5 * math.sqrt((i + 1) / 24)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.7
        pygame.draw.ellipse(p, (255, 255, 250), (int(x - 5), int(y - 3), 11, 6))
    for k, (a, col) in enumerate(((0.4, (245, 140, 40)), (1.8, (245, 140, 40)), (3.1, (110, 190, 80)),
                                  (4.2, (245, 140, 40)), (5.2, (110, 190, 80)), (2.5, (110, 190, 80)))):
        _c(p, col, cx + math.cos(a) * r * 0.4, cy + math.sin(a) * r * 0.28, r * 0.09)


def _galletas(p, c, ing, cx, cy, r):
    for dx, dy, rr in ((-0.45, 0.15, 0.4), (0.4, 0.2, 0.4), (0.0, -0.3, 0.42)):
        x, y = cx + dx * r, cy + dy * r
        _c(p, (190, 130, 60), x, y + 3, r * rr, None)
        _c(p, (230, 175, 95), x, y, r * rr, (180, 120, 55), 2)
        for a in range(5):
            _c(p, (95, 55, 35), x + math.cos(a * 1.4 + dx) * r * rr * 0.5, y + math.sin(a * 1.4 + dx) * r * rr * 0.5,
               r * 0.05)


def _tarta(p, c, ing, cx, cy, r):
    _c(p, (200, 140, 65), cx, cy, r * 0.9)
    _c(p, (225, 170, 95), cx, cy, r * 0.84)
    _c(p, c, cx, cy, r * 0.68)
    for i in range(-3, 4):
        d = i * r * 0.2
        pygame.draw.line(p, (225, 170, 95), (cx + d - r * 0.6, cy - r * 0.6), (cx + d + r * 0.6, cy + r * 0.6), 5)
        pygame.draw.line(p, (225, 170, 95), (cx + d - r * 0.6, cy + r * 0.6), (cx + d + r * 0.6, cy - r * 0.6), 5)
    _c(p, (225, 170, 95), cx, cy, r * 0.9, None)
    pygame.draw.circle(p, (200, 140, 65), (cx, cy), int(r * 0.9), 5)
    _c(p, (250, 215, 130), cx, cy, r * 0.22, (200, 140, 65), 2)


def _sushi(p, c, ing, cx, cy, r):
    for dx, dy in ((-0.5, 0.25), (0.5, 0.25), (0.0, -0.4)):
        x, y = cx + dx * r, cy + dy * r
        _c(p, (45, 60, 55), x, y, r * 0.38)
        _c(p, (250, 250, 245), x, y, r * 0.31)
        _c(p, (245, 130, 100), x, y, r * 0.16, (210, 90, 70), 2)
        _c(p, (110, 180, 90), x + r * 0.07, y - r * 0.04, r * 0.05)
    pygame.draw.rect(p, (110, 175, 85), (cx + r * 0.62, cy - r * 0.6, r * 0.2, r * 0.2), border_radius=6)


def _pastel(p, c, ing, cx, cy, r):
    w = r * 1.5
    for i, col in enumerate((c, aclarar(c, 0.45), c)):
        pygame.draw.rect(p, col, (cx - w / 2, cy + r * 0.0 - i * r * 0.0 + r * (0.05 + 0.26 * i) - r * 0.2,
                                  w, r * 0.28), border_radius=5)
    pygame.draw.rect(p, oscurecer(c, 0.5), (cx - w / 2, cy - r * 0.2, w, r * 0.84), 3, border_radius=8)
    pygame.draw.rect(p, aclarar(c, 0.7), (cx - w / 2 - 4, cy - r * 0.42, w + 8, r * 0.3), border_radius=12)
    for dx in (-0.55, -0.2, 0.25, 0.6):
        pygame.draw.rect(p, aclarar(c, 0.7), (cx + dx * r - 6, cy - r * 0.3, 14, r * 0.28), border_radius=7)
    _c(p, (215, 40, 60), cx, cy - r * 0.52, r * 0.14, (140, 20, 35), 2)
    pygame.draw.line(p, (90, 140, 60), (cx, cy - r * 0.64), (cx + 8, cy - r * 0.84), 3)


def _ceviche(p, c, ing, cx, cy, r):
    _c(p, (245, 248, 252), cx, cy, r * 0.84, (180, 190, 205), 3)
    _c(p, (225, 238, 240), cx, cy, r * 0.7)
    for i in range(9):
        a = i * 2.2
        d = r * (0.1 + 0.4 * ((i * 7) % 9) / 9)
        rr = pygame.Rect(0, 0, int(r * 0.26), int(r * 0.26))
        rr.center = (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d))
        pygame.draw.rect(p, (250, 245, 235) if i % 2 else (250, 205, 190), rr, border_radius=4)
    for a in (0.6, 3.0, 4.6):
        _c(p, (150, 90, 160), cx + math.cos(a) * r * 0.45, cy + math.sin(a) * r * 0.45, r * 0.07)
    _c(p, (170, 220, 90), cx + r * 0.45, cy - r * 0.45, r * 0.2, (90, 150, 40), 3)
    _c(p, (210, 240, 130), cx + r * 0.45, cy - r * 0.45, r * 0.1)


def _paella(p, c, ing, cx, cy, r):
    _c(p, (80, 84, 100), cx, cy, r * 0.95)
    _c(p, (60, 62, 78), cx, cy, r * 0.95, None)
    _c(p, (250, 205, 70), cx, cy, r * 0.8)
    for i in range(16):
        a = i * 2.1
        d = r * 0.68 * math.sqrt((i + 1) / 16)
        pygame.draw.ellipse(p, (255, 230, 120), (int(cx + math.cos(a) * d - 5), int(cy + math.sin(a) * d - 3), 11, 6))
    for a in (0.5, 2.2, 3.9, 5.3):
        _e(p, (245, 120, 80), cx + math.cos(a) * r * 0.45, cy + math.sin(a) * r * 0.45, r * 0.34, r * 0.2,
           (200, 70, 50), 2)
    for a in (1.2, 3.0, 4.6):
        pygame.draw.line(p, (215, 50, 40), (cx + math.cos(a) * r * 0.2, cy + math.sin(a) * r * 0.2),
                         (cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62), 6)
    for a in (0.1, 1.8, 2.9, 4.2, 5.7):
        _c(p, (90, 175, 80), cx + math.cos(a) * r * 0.3, cy + math.sin(a) * r * 0.55, r * 0.05)
    pygame.draw.circle(p, (45, 48, 62), (cx, cy), int(r * 0.95), 5)
    _c(p, (255, 235, 120), cx + r * 0.6, cy + r * 0.45, r * 0.15, (200, 170, 40), 2)


def _pescado_papas(p, c, ing, cx, cy, r):
    for i in range(6):
        x = cx + r * 0.1 + i * r * 0.12
        pygame.draw.line(p, (235, 190, 70), (x, cy + r * 0.55), (x + r * 0.1 * (i - 2) * 0.3, cy - r * 0.05 + (i % 2) * 10),
                         int(r * 0.12))
    _e(p, (220, 150, 55), cx - r * 0.2, cy - r * 0.1, r * 1.1, r * 0.55, (160, 100, 30), 3)
    pygame.draw.polygon(p, (220, 150, 55), [(cx + r * 0.3, cy - r * 0.1), (cx + r * 0.62, cy - r * 0.38),
                                            (cx + r * 0.62, cy + r * 0.18)])
    _c(p, (255, 255, 255), cx - r * 0.55, cy - r * 0.18, r * 0.07)
    _c(p, (30, 30, 50), cx - r * 0.55, cy - r * 0.18, r * 0.035)
    for dx in (-0.2, 0.05):
        pygame.draw.arc(p, (170, 105, 35), pygame.Rect(int(cx + dx * r - 14), int(cy - r * 0.32), 28, int(r * 0.45)), -1.2, 1.2, 3)
    _c(p, (250, 235, 90), cx - r * 0.5, cy + r * 0.45, r * 0.16, (200, 170, 30), 2)


def _pastel_frutas(p, c, ing, cx, cy, r):
    w = r * 1.5
    pygame.draw.rect(p, (240, 205, 140), (cx - w / 2, cy - r * 0.15, w, r * 0.8), border_radius=8)
    pygame.draw.rect(p, (200, 150, 80), (cx - w / 2, cy - r * 0.15, w, r * 0.8), 3, border_radius=8)
    pygame.draw.rect(p, (250, 140, 150), (cx - w / 2 - 4, cy - r * 0.4, w + 8, r * 0.32), border_radius=12)
    for dx in (-0.55, -0.15, 0.3, 0.62):
        pygame.draw.rect(p, (250, 140, 150), (cx + dx * r - 6, cy - r * 0.3, 14, r * 0.28), border_radius=7)
    for dx, col in ((-0.5, (215, 40, 60)), (-0.17, (245, 150, 40)), (0.17, (140, 205, 80)), (0.5, (215, 40, 60))):
        _c(p, col, cx + dx * r, cy - r * 0.52, r * 0.14, oscurecer(col, 0.4), 2)
    _c(p, (170, 90, 190), cx, cy - r * 0.68, r * 0.12, (110, 50, 130), 2)


_TIPOS = {"sopa": _sopa, "ensalada": _ensalada, "pizza": _pizza, "tortilla": _tortilla, "frutas": _frutas,
          "jugo": _jugo, "tostada": _tostada, "panqueques": _panqueques, "arroz": _arroz, "galletas": _galletas,
          "tarta": _tarta, "sushi": _sushi, "pastel": _pastel, "ceviche": _ceviche, "paella": _paella,
          "pescado_papas": _pescado_papas, "pastel_frutas": _pastel_frutas}


def plato_completo(p, tipo, cont, ing, cx, cy, r):
    """Plato blanco con la comida encima. r = radio del plato."""
    cx, cy = int(cx), int(cy)
    pygame.draw.circle(p, (150, 156, 175), (cx, cy + max(2, int(r * 0.04))), int(r))
    pygame.draw.circle(p, (185, 190, 205), (cx, cy), int(r))
    pygame.draw.circle(p, (255, 255, 255), (cx, cy), int(r - 4))
    pygame.draw.circle(p, (232, 238, 248), (cx, cy), int(r * 0.86))
    if tipo in ("paella",):
        comida(p, tipo, cont, ing, cx, cy, r * 0.84)
    else:
        comida(p, tipo, cont, ing, cx, cy, r * 0.8)


def plato_vacio(p, cx, cy, r):
    cx, cy = int(cx), int(cy)
    pygame.draw.circle(p, (185, 190, 205), (cx, cy), int(r))
    pygame.draw.circle(p, (255, 255, 255), (cx, cy), int(r - 4))
    pygame.draw.circle(p, (232, 238, 248), (cx, cy), int(r * 0.86))


# ----------------------------------------------------------------------------- ingredientes (se cortan al picar)
def ingrediente(forma, col):
    """Superficie 260x170 con el ingrediente entero."""
    s = pygame.Surface((260, 170), pygame.SRCALPHA)
    borde = oscurecer(col, 0.5)
    if forma == "pez":
        arte.dibujar_pez(s, "sardina", 150, 88, 1.5, mirando=1)
    elif forma == "hoja":
        for dx, dy, w, h in ((-50, 10, 130, 90), (50, 10, 130, 90), (0, -22, 150, 100), (0, 24, 160, 90)):
            r = pygame.Rect(0, 0, w, h)
            r.center = (130 + dx, 85 + dy)
            pygame.draw.ellipse(s, col, r)
            pygame.draw.ellipse(s, borde, r, 3)
        pygame.draw.line(s, aclarar(col, 0.5), (60, 100), (200, 70), 5)
    elif forma == "redondo":
        pygame.draw.circle(s, col, (130, 85), 72)
        pygame.draw.circle(s, borde, (130, 85), 72, 4)
        for dx, dy in ((-25, -20), (30, 10), (-10, 35), (35, -35)):
            pygame.draw.circle(s, oscurecer(col, 0.2), (130 + dx, 85 + dy), 9)
        pygame.draw.circle(s, aclarar(col, 0.5), (100, 55), 11)
    elif forma == "pan":
        r = pygame.Rect(22, 40, 216, 96)
        pygame.draw.rect(s, (190, 130, 65), r, border_radius=44)
        pygame.draw.rect(s, (240, 205, 140), r.inflate(-16, -16), border_radius=36)
        for x in range(70, 210, 44):
            pygame.draw.line(s, (200, 150, 80), (x, 58), (x - 10, 80), 5)
        pygame.draw.rect(s, (130, 85, 40), r, 4, border_radius=44)
    else:
        r = pygame.Rect(18, 45, 224, 80)
        pygame.draw.rect(s, col, r, border_radius=38)
        for x in range(50, 230, 30):
            pygame.draw.line(s, oscurecer(col, 0.2), (x, 52), (x - 6, 118), 4)
        pygame.draw.rect(s, borde, r, 4, border_radius=38)
    return s


# ----------------------------------------------------------------------------- iconos
def icono(nombre, tam=64):
    """Icono de herramienta/habilidad: picar, mezclar, sazonar, hornear, servir."""
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    k = tam / 64
    if nombre == "picar":
        pts = [(10 * k, 50 * k), (14 * k, 22 * k), (44 * k, 10 * k), (38 * k, 38 * k)]
        pygame.draw.polygon(s, (215, 222, 235), pts)
        pygame.draw.polygon(s, (90, 100, 125), pts, 3)
        pygame.draw.line(s, (130, 85, 50), (38 * k, 40 * k), (56 * k, 56 * k), int(9 * k))
    elif nombre == "mezclar":
        pygame.draw.line(s, (130, 85, 50), (32 * k, 30 * k), (48 * k, 58 * k), int(7 * k))
        pygame.draw.ellipse(s, (170, 120, 70), (16 * k, 6 * k, 34 * k, 30 * k))
        pygame.draw.ellipse(s, (90, 60, 35), (16 * k, 6 * k, 34 * k, 30 * k), 3)
    elif nombre == "sazonar":
        pygame.draw.rect(s, (245, 248, 255), (16 * k, 18 * k, 32 * k, 40 * k), border_radius=int(8 * k))
        pygame.draw.rect(s, (90, 100, 125), (16 * k, 18 * k, 32 * k, 40 * k), 3, border_radius=int(8 * k))
        pygame.draw.rect(s, (80, 150, 230), (18 * k, 6 * k, 28 * k, 14 * k), border_radius=int(6 * k))
        for x in (26, 32, 38):
            pygame.draw.circle(s, (60, 80, 120), (int(x * k), int(12 * k)), max(1, int(2 * k)))
    elif nombre == "hornear":
        pygame.draw.rect(s, (200, 70, 60), (6 * k, 10 * k, 52 * k, 46 * k), border_radius=int(8 * k))
        pygame.draw.rect(s, (110, 30, 30), (6 * k, 10 * k, 52 * k, 46 * k), 3, border_radius=int(8 * k))
        pygame.draw.rect(s, (60, 45, 50), (13 * k, 24 * k, 38 * k, 26 * k), border_radius=int(5 * k))
        pygame.draw.polygon(s, (255, 190, 50), [(32 * k, 28 * k), (40 * k, 46 * k), (24 * k, 46 * k)])
        pygame.draw.polygon(s, (255, 235, 130), [(32 * k, 36 * k), (36 * k, 46 * k), (28 * k, 46 * k)])
        for x in (16, 26):
            pygame.draw.circle(s, (250, 220, 120), (int(x * k), int(17 * k)), max(2, int(3 * k)))
    else:                                           # servir
        pygame.draw.circle(s, (245, 248, 255), (int(32 * k), int(32 * k)), int(26 * k))
        pygame.draw.circle(s, (90, 100, 125), (int(32 * k), int(32 * k)), int(26 * k), 3)
        pygame.draw.circle(s, (210, 220, 240), (int(32 * k), int(32 * k)), int(16 * k), 3)
    return s


def candado(p, x, y, tam=30):
    """Candado centrado en (x, y)."""
    x, y = int(x), int(y)
    w = tam * 0.7
    pygame.draw.arc(p, (110, 115, 135), (x - w * 0.35, y - tam * 0.62, w * 0.7, w * 0.9), 0, math.pi, max(3, int(tam * 0.12)))
    pygame.draw.rect(p, (150, 155, 175), (x - w / 2, y - tam * 0.12, w, tam * 0.62), border_radius=6)
    pygame.draw.rect(p, (90, 95, 115), (x - w / 2, y - tam * 0.12, w, tam * 0.62), 2, border_radius=6)
    pygame.draw.circle(p, (90, 95, 115), (x, y + int(tam * 0.14)), max(2, int(tam * 0.08)))


def casita(p, x, y, tam=28):
    """Icono de 'ingredientes de la casa'."""
    x, y = int(x), int(y)
    h = tam / 2
    pygame.draw.polygon(p, (210, 80, 70), [(x - h, y), (x, y - h), (x + h, y)])
    pygame.draw.rect(p, (250, 225, 170), (x - h * 0.72, y, h * 1.44, h * 0.95))
    pygame.draw.rect(p, (130, 85, 50), (x - h * 0.2, y + h * 0.3, h * 0.4, h * 0.65))
    pygame.draw.rect(p, (150, 100, 60), (x - h * 0.72, y, h * 1.44, h * 0.95), 2)
