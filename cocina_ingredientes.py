"""Ingredientes de cocina en todos sus estados (dibujo procedural).

    dibujar_ing(p, ident, x, y, tam=64, estado="entero", t=0.0)
    dibujar_tazon(p, x, y, contenido=[(ident, estado), ...], tam=90)

`ident`: id de catalogo (se usa catalogo.dibujar_item para 'entero'), pseudo-ingrediente de cocina_datos.PSEUDO
o cualquier otro (se dibuja un circulo con la inicial; nunca lanza excepcion).
Estados: entero, pelado, cortado, rallado, picado, batido, masa, cocido, quemado (otros = entero).
`t` (segundos) anima vapor, burbujas y humo. Los dibujos se guardan en cache (ver LIMITE_CACHE).
"""

import math
import zlib
from random import Random

import pygame

import catalogo
from nucleo import aclarar, oscurecer
from cocina_herramientas import c, e, rr, poli, lin, brillo, INK

ESTADOS = ("entero", "pelado", "cortado", "rallado", "picado", "batido", "masa", "cocido", "quemado")
LIMITE_CACHE = 600

try:
    import cocina_datos as _datos
    PSEUDO = tuple(_datos.PSEUDO)
except Exception:                                                   # pragma: no cover
    PSEUDO = ()

PSEUDO_COL = {"masa": (240, 215, 165), "masa_plana": (242, 220, 172), "mezcla": (245, 225, 170),
              "batido": (255, 235, 150), "crema_batida": (255, 252, 245), "salsa": (225, 70, 50),
              "caldo": (240, 190, 80), "relleno": (200, 130, 80), "pure": (250, 230, 150), "bizcocho": (245, 205, 100),
              "base": (238, 205, 140), "pasta_cocida": (248, 218, 130), "arroz_cocido": (252, 250, 242),
              "glaseado": (255, 225, 235), "jugo": (250, 170, 40), "huevo_batido": (255, 225, 110),
              "pan_rebanado": (230, 180, 105), "tortilla": (240, 200, 90), "rollo": (225, 170, 100),
              "empanada": (225, 160, 80), "galleta": (220, 165, 95), "bolitas": (235, 200, 150),
              "panqueque": (235, 190, 105), "pizza": (235, 120, 60), "agua": (110, 190, 245)}

FLESH = {"manzana": (250, 240, 200), "naranja": (255, 195, 85), "limon": (250, 240, 150), "sandia": (240, 85, 95),
         "kiwi": (150, 210, 80), "tomate": (240, 95, 75), "cebolla": (250, 236, 245), "pepino": (195, 232, 150),
         "papa": (250, 236, 170), "zanahoria": (255, 175, 70), "calabaza": (255, 195, 65), "pimiento": (250, 105, 80),
         "maiz": (250, 225, 90), "huevo": (255, 252, 245), "pescado": (255, 225, 215), "langostino": (255, 215, 200),
         "calamar": (252, 238, 240), "lechuga": (170, 225, 120), "espinaca": (100, 185, 100)}


def _hash(ident):
    return zlib.crc32(str(ident).encode("utf-8", "ignore"))


def _mezcla(a, b, f):
    return tuple(int(a[i] * (1 - f) + b[i] * f) for i in range(3))


def _flesh(ident, col):
    return FLESH.get(ident) or aclarar(col, .5)


def _color(ident):
    if ident in catalogo.ITEMS:
        return catalogo.ITEMS[ident]["color"]
    return PSEUDO_COL.get(ident, (190, 190, 205))


def _forma(ident):
    return catalogo.ITEMS[ident]["forma"] if ident in catalogo.ITEMS else None


# ----------------------------------------------------------------------------- piezas basicas
def _mancha(s, cx, cy, rx, ry, col, rng, borde=True, n=9, hl=True):
    """Blob irregular (union de elipses) con contorno."""
    piezas = []
    for i in range(n):
        a = i / n * 2 * math.pi + rng.uniform(-.2, .2)
        d = rng.uniform(.45, .72)
        piezas.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, rx * rng.uniform(.38, .55),
                       ry * rng.uniform(.4, .58)))
    piezas.append((cx, cy, rx * .95, ry * .9))
    if borde:
        for px, py, w, h in piezas:
            pygame.draw.ellipse(s, oscurecer(col, .4), (int(px - w - 2), int(py - h - 2), int(w * 2 + 4), int(h * 2 + 4)))
    for px, py, w, h in piezas:
        pygame.draw.ellipse(s, col, (int(px - w), int(py - h), int(w * 2), int(h * 2)))
    if hl:
        e(s, aclarar(col, .5), cx - rx * .3, cy - ry * .35, rx * .5, ry * .3, False)
        brillo(s, cx - rx * .4, cy - ry * .4, max(1, rx * .07))


def _vapor(s, cx, cy, r, t, n=3, col=(255, 255, 255)):
    for i in range(n):
        ph = (t * .9 + i / n) % 1.0
        x0 = cx + (i - (n - 1) / 2) * r * .5
        pts = [(x0 + math.sin(ph * 6 + i + j * .9) * r * .1, cy - ph * r * .5 - j * r * .12) for j in range(5)]
        a = int(220 * (1 - ph))
        sup = pygame.Surface((s.get_width(), s.get_height()), pygame.SRCALPHA)
        pygame.draw.lines(sup, col + (a,), False, [(int(a1), int(b1)) for a1, b1 in pts], max(2, int(r * .09)))
        s.blit(sup, (0, 0))


def _humo(s, cx, cy, r, t, n=3):
    for i in range(n):
        ph = (t * .7 + i / n) % 1.0
        x0 = cx + (i - (n - 1) / 2) * r * .5 + math.sin(ph * 5 + i) * r * .15
        y0 = cy - ph * r * .8
        rad = r * (.12 + .18 * ph)
        sup = pygame.Surface((s.get_width(), s.get_height()), pygame.SRCALPHA)
        pygame.draw.circle(sup, (70, 66, 74, int(200 * (1 - ph))), (int(x0), int(y0)), max(2, int(rad)))
        s.blit(sup, (0, 0))


# ----------------------------------------------------------------------------- ingredientes propios (entero)
def _agua(s, cx, cy, r, t):
    col = (110, 190, 245)
    poli(s, col, [(cx, cy - r * .9), (cx + r * .55, cy + r * .25), (cx + r * .45, cy + r * .6), (cx, cy + r * .85),
                  (cx - r * .45, cy + r * .6), (cx - r * .55, cy + r * .25)])
    c(s, col, cx, cy + r * .3, r * .55, False)
    pygame.draw.circle(s, oscurecer(col, .4), (int(cx), int(cy + r * .3)), int(r * .55), 2)
    c(s, aclarar(col, .6), cx - r * .2, cy + r * .2, r * .13, False)


def _pan(s, cx, cy, r, t):
    col = (225, 175, 100)
    e(s, oscurecer(col, .25), cx, cy + r * .25, r * 1.7, r * 1.05)
    rr(s, col, cx, cy + r * .0, r * 1.7, r * .9, r * .4)
    e(s, aclarar(col, .1), cx, cy - r * .3, r * 1.5, r * .75)
    pygame.draw.ellipse(s, oscurecer(col, .45), (int(cx - r * .75), int(cy - r * .68), int(r * 1.5), int(r * .75)), 2)
    for k in (-.4, 0, .4):
        lin(s, oscurecer(col, .3), (cx + k * r - r * .08, cy - r * .55), (cx + k * r + r * .1, cy - r * .1), 3)
    brillo(s, cx - r * .5, cy - r * .5, r * .06)


def _mantequilla(s, cx, cy, r, t):
    col = (250, 225, 120)
    poli(s, oscurecer(col, .15), [(cx - r * .7, cy - r * .1), (cx + r * .55, cy - r * .1), (cx + r * .55, cy + r * .6),
                                  (cx - r * .7, cy + r * .6)])
    poli(s, aclarar(col, .45), [(cx - r * .7, cy - r * .1), (cx - r * .4, cy - r * .5), (cx + r * .85, cy - r * .5),
                                (cx + r * .55, cy - r * .1)])
    poli(s, col, [(cx + r * .55, cy - r * .1), (cx + r * .85, cy - r * .5), (cx + r * .85, cy + r * .2),
                  (cx + r * .55, cy + r * .6)])
    rr(s, (250, 250, 255), cx - r * .08, cy + r * .25, r * .8, r * .32, r * .06, False)
    brillo(s, cx - r * .1, cy - r * .3, r * .06)


def _queso(s, cx, cy, r, t):
    col = (250, 205, 80)
    poli(s, col, [(cx - r * .85, cy + r * .45), (cx + r * .85, cy + r * .45), (cx + r * .85, cy + r * .0),
                  (cx - r * .85, cy + r * .45)], False)
    poli(s, aclarar(col, .3), [(cx - r * .85, cy + r * .45), (cx + r * .85, cy + r * .0), (cx + r * .6, cy - r * .35),
                               (cx - r * .5, cy - r * .1)])
    poli(s, col, [(cx - r * .85, cy + r * .45), (cx + r * .85, cy + r * .45), (cx + r * .85, cy + r * .0)])
    for dx, dy, rad in ((.3, .27, .1), (-.25, .3, .08), (.58, .22, .06)):
        c(s, oscurecer(col, .3), cx + dx * r, cy + dy * r, r * rad, False)
    c(s, oscurecer(col, .25), cx + r * .1, cy - r * .12, r * .08, False)
    brillo(s, cx - r * .25, cy - r * .03, r * .05)


def _carne(s, cx, cy, r, t):
    col = (200, 70, 70)
    _mancha(s, cx, cy, r * .85, r * .6, col, Random(5), n=7)
    for k in range(3):
        lin(s, (250, 215, 205), (cx - r * .4 + k * r * .3, cy - r * .1), (cx - r * .1 + k * r * .3, cy + r * .3), 3)
    c(s, (250, 230, 225), cx + r * .35, cy - r * .05, r * .13)


def _pollo(s, cx, cy, r, t):
    hueso = (250, 245, 230)
    lin(s, hueso, (cx + r * .2, cy + r * .1), (cx + r * .75, cy + r * .72), max(4, r * .2))
    c(s, hueso, cx + r * .72, cy + r * .78, r * .14)
    c(s, hueso, cx + r * .86, cy + r * .62, r * .14)
    _mancha(s, cx - r * .15, cy - r * .12, r * .7, r * .6, (232, 175, 110), Random(9), n=7)
    brillo(s, cx - r * .4, cy - r * .35, r * .06)


def _fideos(s, cx, cy, r, t):
    col = (245, 215, 140)
    for k in range(7):
        x0 = cx - r * .6 + k * r * .2
        lin(s, oscurecer(col, .25), (x0 - r * .08, cy - r * .7), (x0 + r * .05, cy + r * .75), 5)
        lin(s, col, (x0 - r * .08, cy - r * .7), (x0 + r * .05, cy + r * .75), 3)
    rr(s, (235, 90, 80), cx, cy + r * .0, r * 1.5, r * .22, r * .05)


def _nueces(s, cx, cy, r, t):
    for dx, dy in ((-.35, .15), (.35, .2), (0, -.3)):
        _nuez(s, cx + dx * r, cy + dy * r, r * .5)


def _nuez(s, x, y, rad):
    col = (170, 120, 70)
    c(s, col, x, y, rad)
    lin(s, oscurecer(col, .45), (x, y - rad), (x, y + rad), 2)
    for k in (-.35, .35):
        pygame.draw.arc(s, oscurecer(col, .45), pygame.Rect(int(x - rad * .6 + k * rad), int(y - rad * .6),
                                                           int(rad * 1.2), int(rad * 1.2)), 1.2, 5.0, 2)
    brillo(s, x - rad * .4, y - rad * .4, max(1, rad * .12))


_PROPIOS = {"agua": _agua, "pan": _pan, "mantequilla": _mantequilla, "queso": _queso, "carne": _carne,
            "pollo": _pollo, "fideos": _fideos, "nueces": _nueces}


# ----------------------------------------------------------------------------- pseudo-ingredientes (entero)
def _masa(s, cx, cy, r, t, col=None):
    col = col or (240, 215, 165)
    _mancha(s, cx, cy + r * .1, r * .85, r * .7, col, Random(3), n=8)


def _masa_plana(s, cx, cy, r, t):
    col = PSEUDO_COL["masa_plana"]
    e(s, oscurecer(col, .3), cx, cy + r * .12, r * 1.8, r * 1.05)
    e(s, col, cx, cy, r * 1.8, r * 1.05)
    e(s, aclarar(col, .3), cx - r * .1, cy - r * .08, r * 1.3, r * .65, False)
    for k in (-.4, 0, .4):
        lin(s, oscurecer(col, .2), (cx + k * r - r * .15, cy - r * .35), (cx + k * r + r * .15, cy + r * .3), 2)


def _mezcla_d(s, cx, cy, r, t):
    col = PSEUDO_COL["mezcla"]
    rng = Random(12)
    _mancha(s, cx, cy + r * .05, r * .88, r * .68, col, rng, n=8)
    for i in range(10):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(.1, .6)
        cc = rng.choice([(235, 100, 80), (110, 190, 90), (250, 160, 60), (255, 250, 235)])
        c(s, cc, cx + math.cos(a) * r * .75 * d * 1.1, cy + math.sin(a) * r * .55 * d, r * .09, False)


def _espuma(s, cx, cy, r, t, col):
    rng = Random(21)
    claro = aclarar(col, .45)
    for i in range(14):
        a = i / 14 * 6.28 + .3
        d = .55 + .1 * (i % 3)
        x, y = cx + math.cos(a) * r * d, cy + math.sin(a) * r * d * .72
        c(s, claro, x, y, r * (.26 + .06 * (i % 2)), oscurecer(col, .3), 2)
    for i in range(6):
        a = i / 6 * 6.28
        c(s, aclarar(col, .5), cx + math.cos(a) * r * .28, cy + math.sin(a) * r * .22, r * .3, oscurecer(col, .3), 2)
    c(s, aclarar(col, .6), cx, cy, r * .33, oscurecer(col, .25), 2)
    pygame.draw.arc(s, oscurecer(col, .35), pygame.Rect(int(cx - r * .5), int(cy - r * .4), int(r), int(r * .8)),
                    t * 3 % 6.28, t * 3 % 6.28 + 3.5, 3)
    for i in range(4):
        ph = (t * .8 + i * .27) % 1
        c(s, (255, 255, 255), cx - r * .6 + i * r * .4, cy - r * .5 - ph * r * .35, r * (.06 + .04 * (1 - ph)), INK, 1)
    brillo(s, cx - r * .3, cy - r * .35, r * .07)


def _crema_batida(s, cx, cy, r, t):
    col = (255, 252, 245)
    bd = (200, 185, 175)
    for i, (w, dy) in enumerate(((1.7, .5), (1.35, .15), (.95, -.17), (.55, -.45))):
        e(s, col, cx, cy + dy * r, r * w, r * (.5 - i * .05), bd, 2)
    poli(s, col, [(cx - r * .12, cy - r * .55), (cx + r * .12, cy - r * .55), (cx + r * .02, cy - r * .88)], bd)
    for dx, dy in ((-.45, .45), (.3, .15), (-.1, -.15)):
        pygame.draw.arc(s, bd, pygame.Rect(int(cx + dx * r - r * .3), int(cy + dy * r - r * .08), int(r * .6), int(r * .22)), 3.4, 6.1, 2)
    brillo(s, cx - r * .55, cy + r * .35, r * .06)


def _salsa(s, cx, cy, r, t):
    col = PSEUDO_COL["salsa"]
    e(s, oscurecer(col, .3), cx, cy + r * .1, r * 1.75, r * 1.0)
    e(s, col, cx, cy, r * 1.7, r * .95)
    rng = Random(8)
    for i in range(7):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(.1, .6)
        c(s, aclarar(col, .25), cx + math.cos(a) * r * .8 * d, cy + math.sin(a) * r * .4 * d, r * .13, False)
    e(s, aclarar(col, .5), cx - r * .35, cy - r * .2, r * .5, r * .2, False)
    for dx, dy in ((.95, -.35), (-.95, .25)):
        c(s, col, cx + dx * r, cy + dy * r, r * .09)
    c(s, (110, 190, 90), cx + r * .35, cy + r * .05, r * .07, False)


def _caldo(s, cx, cy, r, t):
    col = PSEUDO_COL["caldo"]
    e(s, oscurecer(col, .35), cx, cy + r * .12, r * 1.75, r * 1.0)
    e(s, col, cx, cy, r * 1.7, r * .95)
    for dx, dy in ((-.35, -.05), (.25, .1), (.5, -.15), (-.1, .25)):
        c(s, aclarar(col, .5), cx + dx * r, cy + dy * r * .6, r * .1, oscurecer(col, .2), 1)
    e(s, aclarar(col, .5), cx - r * .4, cy - r * .22, r * .4, r * .15, False)
    _vapor(s, cx, cy - r * .2, r, t)


def _relleno(s, cx, cy, r, t):
    rng = Random(33)
    cols = [(200, 120, 70), (110, 185, 90), (250, 160, 60), (240, 90, 70), (235, 215, 150)]
    puntos = [(cx + rng.uniform(-.7, .7) * r, cy + rng.uniform(-.2, .6) * r * (1 - abs(0) )) for _ in range(26)]
    puntos.sort(key=lambda q: q[1])
    for i, (x, y) in enumerate(puntos):
        cc = cols[i % len(cols)]
        h = (y - cy + r * .2) / (r * .8)
        w = r * (.95 - .75 * (1 - min(1, max(0, h))))
        if abs(x - cx) > w:
            x = cx + (x - cx) * w / (abs(x - cx) + 1e-6) * .9
        rr(s, cc, x, y, r * .26, r * .22, r * .06)


def _pure(s, cx, cy, r, t):
    col = PSEUDO_COL["pure"]
    e(s, oscurecer(col, .3), cx, cy + r * .35, r * 1.7, r * .7)
    poli(s, col, [(cx - r * .85, cy + r * .35), (cx - r * .45, cy - r * .35), (cx, cy - r * .55), (cx + r * .45, cy - r * .35),
                  (cx + r * .85, cy + r * .35)], False)
    e(s, col, cx, cy + r * .35, r * 1.7, r * .7, False)
    e(s, col, cx, cy - r * .15, r * 1.0, r * .75, False)
    pygame.draw.ellipse(s, oscurecer(col, .4), (int(cx - r * .85), int(cy), int(r * 1.7), int(r * .7)), 2)
    for k in range(4):
        pygame.draw.arc(s, oscurecer(col, .22), pygame.Rect(int(cx - r * .55 + k * 4), int(cy - r * .55 + k * r * .18),
                                                           int(r * 1.1 - k * 8), int(r * .5)), .3, 2.9, 2)
    e(s, (255, 235, 130), cx, cy - r * .5, r * .3, r * .15)


def _bizcocho(s, cx, cy, r, t):
    col = PSEUDO_COL["bizcocho"]
    tope = (195, 120, 60)
    rr(s, col, cx, cy + r * .1, r * 1.7, r * .9, r * .18)
    rr(s, aclarar(col, .3), cx, cy + r * .12, r * 1.45, r * .65, r * .12, False)
    rng = Random(44)
    for _ in range(12):
        c(s, oscurecer(col, .2), cx + rng.uniform(-.65, .65) * r, cy + r * .12 + rng.uniform(-.25, .3) * r, r * .035, False)
    e(s, tope, cx, cy - r * .3, r * 1.7, r * .55)
    e(s, aclarar(tope, .2), cx, cy - r * .33, r * 1.4, r * .35, False)
    pygame.draw.ellipse(s, oscurecer(tope, .4), (int(cx - r * .85), int(cy - r * .58), int(r * 1.7), int(r * .55)), 2)


def _base_d(s, cx, cy, r, t):
    col = PSEUDO_COL["base"]
    e(s, oscurecer(col, .35), cx, cy + r * .12, r * 1.85, r * 1.1)
    e(s, aclarar(col, .1), cx, cy, r * 1.85, r * 1.1)
    e(s, col, cx, cy, r * 1.45, r * .82, oscurecer(col, .2), 2)
    e(s, aclarar(col, .35), cx - r * .15, cy - r * .08, r * 1.0, r * .45, False)


def _pasta_cocida(s, cx, cy, r, t):
    col = PSEUDO_COL["pasta_cocida"]
    rng = Random(55)
    for i in range(14):
        a0 = rng.uniform(0, 6.28)
        pts = []
        for j in range(14):
            a = a0 + j * .45
            d = .25 + j * .04 + rng.uniform(0, .05)
            pts.append((cx + math.cos(a) * r * d * 1.5, cy + math.sin(a) * r * d))
        pygame.draw.lines(s, oscurecer(col, .35), False, pts, 6)
        pygame.draw.lines(s, col, False, pts, 4)
    brillo(s, cx - r * .3, cy - r * .3, r * .05)


def _arroz_cocido(s, cx, cy, r, t):
    col = PSEUDO_COL["arroz_cocido"]
    rng = Random(66)
    e(s, (210, 205, 195), cx, cy + r * .4, r * 1.6, r * .5, False)
    for i in range(70):
        a = rng.uniform(0, 6.28)
        d = math.sqrt(rng.uniform(0, 1))
        x = cx + math.cos(a) * d * r * .8
        y = cy + r * .1 + math.sin(a) * d * r * .5 - (1 - d) * r * .3
        pygame.draw.ellipse(s, (215, 210, 200), (int(x - 5), int(y - 3), 11, 7))
        pygame.draw.ellipse(s, col, (int(x - 4), int(y - 3), 9, 6))


def _glaseado(s, cx, cy, r, t):
    col = PSEUDO_COL["glaseado"]
    e(s, oscurecer(col, .3), cx, cy + r * .1, r * 1.8, r * 1.0)
    e(s, col, cx, cy, r * 1.8, r * .95)
    e(s, aclarar(col, .5), cx - r * .3, cy - r * .2, r * .7, r * .25, False)
    poli(s, col, [(cx + r * .45, cy + r * .1), (cx + r * .6, cy + r * .1), (cx + r * .55, cy + r * .55)], False)
    c(s, col, cx + r * .52, cy + r * .6, r * .09, oscurecer(col, .3))
    for dx, dy in ((-.3, .1), (.1, .05), (.4, -.15)):
        c(s, (250, 100, 150), cx + dx * r, cy + dy * r, r * .04, False)


def _jugo(s, cx, cy, r, t, col=None):
    col = col or PSEUDO_COL["jugo"]
    poli(s, (215, 238, 255), [(cx - r * .55, cy - r * .7), (cx + r * .55, cy - r * .7), (cx + r * .42, cy + r * .85),
                              (cx - r * .42, cy + r * .85)])
    poli(s, col, [(cx - r * .52, cy - r * .25), (cx + r * .52, cy - r * .25), (cx + r * .41, cy + r * .83),
                  (cx - r * .41, cy + r * .83)], False)
    lin(s, aclarar(col, .5), (cx - r * .52, cy - r * .25), (cx + r * .52, cy - r * .25), 3)
    lin(s, (255, 255, 255), (cx - r * .38, cy - r * .55), (cx - r * .3, cy + r * .6), max(2, r * .07))
    lin(s, (240, 90, 120), (cx + r * .2, cy - r * .3), (cx + r * .45, cy - r * 1.0), max(3, r * .1))


def _pan_rebanado(s, cx, cy, r, t):
    col = (232, 180, 105)
    for k, dx in enumerate((-.4, 0, .4)):
        x = cx + dx * r
        y = cy + (k - 1) ** 2 * r * .08
        rr(s, (190, 120, 60), x, y, r * .75, r * 1.2, r * .25)
        rr(s, (250, 232, 185), x, y + r * .04, r * .56, r * .98, r * .18, False)
        c(s, (240, 215, 160), x - r * .1, y - r * .1, r * .04, False)
        c(s, (240, 215, 160), x + r * .1, y + r * .2, r * .04, False)


def _tortilla_d(s, cx, cy, r, t):
    col = PSEUDO_COL["tortilla"]
    e(s, oscurecer(col, .35), cx, cy + r * .12, r * 1.85, r * 1.1)
    e(s, col, cx, cy, r * 1.85, r * 1.05)
    for dx, dy in ((-.4, -.1), (.3, .1), (.55, -.2), (-.1, .22), (0, -.28)):
        e(s, (225, 160, 60), cx + dx * r, cy + dy * r, r * .3, r * .15, False)
    e(s, aclarar(col, .5), cx - r * .45, cy - r * .22, r * .5, r * .18, False)


def _rollo(s, cx, cy, r, t):
    col = PSEUDO_COL["rollo"]
    rr(s, col, cx - r * .12, cy + r * .1, r * 1.5, r * 1.1, r * .45)
    c(s, aclarar(col, .35), cx + r * .62, cy + r * .1, r * .55, oscurecer(col, .4))
    for i, rad in enumerate((.42, .29, .17)):
        pygame.draw.circle(s, (240, 100, 80) if i == 1 else (120, 190, 90) if i == 2 else (250, 235, 190),
                           (int(cx + r * .62), int(cy + r * .1)), int(r * rad), 3)
    c(s, (240, 100, 80), cx + r * .62, cy + r * .1, r * .07, False)
    lin(s, aclarar(col, .5), (cx - r * .7, cy - r * .2), (cx + r * .1, cy - r * .2), 3)


def _empanada(s, cx, cy, r, t):
    col = PSEUDO_COL["empanada"]
    n = 22
    pts = [(cx + math.cos(math.pi * (1 + i / n)) * r * .88, cy + r * .4 + math.sin(math.pi * (1 + i / n)) * r * .95)
           for i in range(n + 1)]
    poli(s, oscurecer(col, .3), [(cx - r * .88, cy + r * .5)] + [(a, b + 3) for a, b in pts] + [(cx + r * .88, cy + r * .5)], False)
    poli(s, col, [(cx - r * .88, cy + r * .4)] + pts + [(cx + r * .88, cy + r * .4)])
    pygame.draw.polygon(s, aclarar(col, .3), [(int(a), int(b + 4)) for a, b in pts[3:-3]] +
                        [(int(cx + r * .6), int(cy + r * .2)), (int(cx - r * .6), int(cy + r * .2))])
    for i in range(0, 9):
        x = cx - r * .85 + i * r * .212
        c(s, oscurecer(col, .35), x, cy + r * .4, r * .06, False)
    e(s, aclarar(col, .5), cx - r * .1, cy - r * .1, r * .6, r * .2, False)


def _galleta(s, cx, cy, r, t):
    col = PSEUDO_COL["galleta"]
    e(s, oscurecer(col, .35), cx, cy + r * .1, r * 1.7, r * 1.55)
    c(s, col, cx, cy, r * .85)
    c(s, aclarar(col, .25), cx - r * .1, cy - r * .1, r * .6, False)
    for dx, dy in ((-.35, -.3), (.3, -.25), (0, .05), (-.3, .35), (.35, .3), (.55, .0)):
        c(s, (100, 60, 40), cx + dx * r, cy + dy * r, r * .11, False)
    brillo(s, cx - r * .5, cy - r * .5, r * .06)


def _bolitas(s, cx, cy, r, t):
    col = PSEUDO_COL["bolitas"]
    for dx, dy in ((-.45, .3), (.45, .3), (0, -.3)):
        c(s, col, cx + dx * r, cy + dy * r, r * .48)
        c(s, aclarar(col, .5), cx + dx * r - r * .16, cy + dy * r - r * .16, r * .12, False)


def _panqueque_d(s, cx, cy, r, t):
    col = PSEUDO_COL["panqueque"]
    e(s, oscurecer(col, .4), cx, cy + r * .25, r * 1.85, r * 1.05)
    e(s, aclarar(col, .1), cx, cy + r * .12, r * 1.85, r * 1.05)
    e(s, (210, 150, 70), cx, cy, r * 1.85, r * 1.0)
    e(s, (225, 170, 85), cx, cy, r * 1.5, r * .75, False)
    for dx, dy in ((-.3, -.1), (.3, .1), (.1, -.2)):
        c(s, (190, 125, 55), cx + dx * r, cy + dy * r * .8, r * .08, False)


def _pizza_d(s, cx, cy, r, t):
    col = PSEUDO_COL["pizza"]
    c(s, (225, 170, 90), cx, cy, r * .92)
    c(s, (250, 215, 90), cx, cy, r * .74)
    c(s, (240, 90, 60), cx, cy, r * .6, False)
    c(s, (252, 220, 100), cx, cy, r * .58, False)
    for a, d in ((.2, .35), (1.5, .3), (2.7, .4), (4.0, .3), (5.2, .4)):
        c(s, (200, 60, 50), cx + math.cos(a) * r * d, cy + math.sin(a) * r * d, r * .11, (150, 40, 35))


_PSEUDO_DIB = {"masa": _masa, "masa_plana": _masa_plana, "mezcla": _mezcla_d,
               "batido": lambda s, cx, cy, r, t: _espuma(s, cx, cy, r, t, PSEUDO_COL["batido"]),
               "crema_batida": _crema_batida, "salsa": _salsa, "caldo": _caldo, "relleno": _relleno, "pure": _pure,
               "bizcocho": _bizcocho, "base": _base_d, "pasta_cocida": _pasta_cocida, "arroz_cocido": _arroz_cocido,
               "glaseado": _glaseado, "jugo": _jugo,
               "huevo_batido": lambda s, cx, cy, r, t: _espuma(s, cx, cy, r, t, PSEUDO_COL["huevo_batido"]),
               "pan_rebanado": _pan_rebanado, "tortilla": _tortilla_d, "rollo": _rollo, "empanada": _empanada,
               "galleta": _galleta, "bolitas": _bolitas, "panqueque": _panqueque_d, "pizza": _pizza_d}


# ----------------------------------------------------------------------------- estados generales
def _rodaja(s, x, y, rad, col, fl, ident, ang=0.0):
    c(s, col, x, y, rad)
    if ident == "cebolla":
        for k, f in enumerate((.82, .6, .38, .16)):
            pygame.draw.circle(s, (230, 150, 195) if k % 2 == 0 else fl, (int(x), int(y)), max(1, int(rad * f)), 3 if k < 3 else 0)
        return
    c(s, fl, x, y, rad * .82, False)
    if ident in ("tomate", "pimiento"):
        for k in range(3):
            a = ang + k * 2.1
            e(s, aclarar(fl, .15), x + math.cos(a) * rad * .38, y + math.sin(a) * rad * .38, rad * .5, rad * .4, False)
            lin(s, col, (x, y), (x + math.cos(a + 1.05) * rad * .8, y + math.sin(a + 1.05) * rad * .8), 2)
    elif ident == "kiwi":
        c(s, (250, 245, 200), x, y, rad * .25, False)
        for k in range(10):
            a = ang + k * .63
            c(s, (50, 40, 30), x + math.cos(a) * rad * .48, y + math.sin(a) * rad * .48, max(1, rad * .05), False)
    elif ident == "pepino":
        c(s, aclarar(fl, .3), x, y, rad * .55, False)
        for k in range(6):
            a = ang + k * 1.05
            c(s, (235, 245, 200), x + math.cos(a) * rad * .3, y + math.sin(a) * rad * .3, max(1, rad * .06), False)
    elif ident in ("zanahoria", "papa", "calabaza", "manzana", "naranja", "limon"):
        c(s, aclarar(fl, .25), x, y, rad * .55, False)
        for k in range(8):
            a = ang + k * .785
            lin(s, oscurecer(fl, .12), (x + math.cos(a) * rad * .2, y + math.sin(a) * rad * .2),
                (x + math.cos(a) * rad * .7, y + math.sin(a) * rad * .7), 1)
    else:
        c(s, aclarar(fl, .25), x, y, rad * .5, False)
    brillo(s, x - rad * .4, y - rad * .4, max(1, rad * .08))


def _gajo(s, x, y, rad, col, fl, ident):
    """Medio disco (sandia, naranja, manzana, limon)."""
    n = 14
    arco = [(x + math.cos(math.pi * i / n) * rad, y + math.sin(math.pi * i / n) * rad * .9) for i in range(n + 1)]
    poli(s, col, [(x - rad, y)] + arco[::-1] + [(x + rad, y)])
    arco2 = [(x + math.cos(math.pi * i / n) * rad * .84, y + math.sin(math.pi * i / n) * rad * .74) for i in range(n + 1)]
    pygame.draw.polygon(s, fl, [(int(a), int(b)) for a, b in [(x - rad * .84, y + 1)] + arco2[::-1] + [(x + rad * .84, y + 1)]])
    if ident == "sandia":
        for dx, dy in ((-.45, .25), (0, .4), (.45, .25), (-.2, .15), (.25, .15)):
            e(s, (40, 40, 40), x + dx * rad, y + dy * rad, rad * .09, rad * .15, False)
    else:
        for k in range(1, 5):
            a = math.pi * k / 5
            lin(s, aclarar(fl, .35), (x, y + 2), (x + math.cos(a) * rad * .8, y + math.sin(a) * rad * .66), 2)
    brillo(s, x - rad * .4, y + rad * .2, max(1, rad * .06))


def _cortado(s, cx, cy, r, ident, col, forma, t):
    fl = _flesh(ident, col)
    rng = Random(_hash(ident))
    if ident in ("sandia", "naranja", "limon", "manzana"):
        _gajo(s, cx - r * .42, cy - r * .2, r * .52, col, fl, ident)
        _gajo(s, cx + r * .42, cy - r * .2, r * .52, col, fl, ident)
        _rodaja(s, cx, cy + r * .45, r * .42, col, fl, ident)
    elif forma == "hoja":
        for i in range(9):
            x = cx + rng.uniform(-.7, .7) * r
            y = cy + rng.uniform(-.5, .5) * r
            a = rng.uniform(0, 3.14)
            w, h = r * rng.uniform(.5, .7), r * rng.uniform(.15, .22)
            sup = pygame.Surface((int(w * 2) + 6, int(w * 2) + 6), pygame.SRCALPHA)
            e(sup, col if i % 2 else aclarar(col, .2), sup.get_width() / 2, sup.get_height() / 2, w, h)
            lin(sup, oscurecer(col, .3), (sup.get_width() / 2 - w * .4, sup.get_height() / 2), (sup.get_width() / 2 + w * .4, sup.get_height() / 2), 1)
            sup = pygame.transform.rotate(sup, math.degrees(a))
            s.blit(sup, sup.get_rect(center=(int(x), int(y))))
    elif ident == "calamar":
        for i, (dx, dy) in enumerate(((-.45, -.1), (.1, .2), (.5, -.15), (-.05, -.45))):
            c(s, col, cx + dx * r, cy + dy * r, r * .38)
            c(s, (252, 240, 240), cx + dx * r, cy + dy * r, r * .2, oscurecer(col, .3), 2)
    elif forma in ("pez",) or ident in ("langostino", "carne", "pollo", "pescado"):
        for i, (dx, dy) in enumerate(((-.4, -.25), (.35, -.2), (0, .3))):
            rr(s, col if ident != "pescado" else (250, 200, 190), cx + dx * r, cy + dy * r, r * .65, r * .45, r * .15)
            rr(s, fl, cx + dx * r, cy + dy * r, r * .48, r * .3, r * .1, False)
            lin(s, oscurecer(fl, .12), (cx + dx * r - r * .15, cy + dy * r), (cx + dx * r + r * .15, cy + dy * r), 2)
    elif forma == "mazorca":
        for dx, dy in ((-.45, -.2), (.45, -.2), (0, .4)):
            c(s, (250, 215, 80), cx + dx * r, cy + dy * r, r * .42)
            for k in range(8):
                a = k * .785
                c(s, (230, 170, 30), cx + dx * r + math.cos(a) * r * .24, cy + dy * r + math.sin(a) * r * .24, r * .08, False)
            c(s, (250, 240, 170), cx + dx * r, cy + dy * r, r * .1, False)
    elif ident == "huevo":
        for k in (-1, 1):
            x = cx + k * r * .45
            e(s, (255, 252, 245), x, cy + r * .1, r * .8, r * 1.1)
            c(s, (250, 195, 50), x, cy + r * .15, r * .24)
            brillo(s, x - r * .08, cy + r * .08, r * .05)
    elif forma in ("caja", "bolsa", "frasco", "botella") or ident == "pan":
        dados = [(-.45, .2), (.35, .3), (-.1, -.3), (.5, -.2)]
        for dx, dy in dados:
            x, y, k = cx + dx * r, cy + dy * r, r * .36
            poli(s, aclarar(col, .3), [(x - k, y), (x, y - k * .6), (x + k * 1.3, y - k * .6), (x + k * .3, y)])
            poli(s, col, [(x - k, y), (x + k * .3, y), (x + k * .3, y + k * 1.0), (x - k, y + k * 1.0)])
            poli(s, oscurecer(col, .2), [(x + k * .3, y), (x + k * 1.3, y - k * .6), (x + k * 1.3, y + k * .4),
                                         (x + k * .3, y + k * 1.0)])
    elif ident == "cebolla":
        _rodaja(s, cx - r * .3, cy - r * .1, r * .55, col, fl, ident)
        _rodaja(s, cx + r * .4, cy + r * .25, r * .48, col, fl, ident)
        _rodaja(s, cx + r * .2, cy - r * .5, r * .4, col, fl, ident)
    else:
        for i, (dx, dy, k) in enumerate(((-.5, .15, .46), (.0, -.2, .46), (.5, .2, .46), (.05, .45, .4))):
            _rodaja(s, cx + dx * r, cy + dy * r, r * k, col, fl, ident, i)


def _monton(s, cx, cy, r, base, rng, n, kind):
    """Montoncito de tiras (rallado) o cubitos (picado)."""
    e(s, oscurecer(base, .5), cx, cy + r * .58, r * 1.7, r * .38, False)
    piezas = []
    for i in range(n):
        a = rng.uniform(0, 6.28)
        d = math.sqrt(rng.uniform(0, 1))
        x = cx + math.cos(a) * d * r * .78
        y = cy + r * .5 - (1 - d * d) * r * .9 + math.sin(a) * d * r * .12
        piezas.append((y, x))
    piezas.sort()
    for y, x in piezas:
        f = rng.uniform(-.18, .22)
        cc = aclarar(base, f) if f > 0 else oscurecer(base, -f)
        if kind == "rallado":
            a = rng.uniform(-1.2, 1.2)
            dx, dy = math.cos(a) * r * .13, math.sin(a) * r * .13
            pygame.draw.line(s, oscurecer(cc, .25), (int(x - dx), int(y - dy)), (int(x + dx), int(y + dy)), 4)
            pygame.draw.line(s, cc, (int(x - dx), int(y - dy)), (int(x + dx), int(y + dy)), 2)
        else:
            k = max(3, int(r * rng.uniform(.1, .15)))
            pygame.draw.rect(s, oscurecer(cc, .3), (int(x - k - 1), int(y - k - 1), k * 2 + 2, k * 2 + 2), border_radius=2)
            pygame.draw.rect(s, cc, (int(x - k), int(y - k), k * 2, k * 2), border_radius=2)


def _frito_huevo(s, cx, cy, r, quemado=False):
    bl = (255, 253, 248) if not quemado else (95, 65, 40)
    rng = Random(7)
    _mancha(s, cx, cy, r * .9, r * .72, bl, rng, borde=True, n=8, hl=not quemado)
    c(s, (250, 190, 40) if not quemado else (40, 30, 25), cx - r * .05, cy - r * .02, r * .32)
    if not quemado:
        brillo(s, cx - r * .15, cy - r * .12, r * .08)


def _pelado(s, cx, cy, r, ident, col, tam, t):
    fl = _flesh(ident, col)
    d = catalogo.ITEMS.get(ident)
    if d is not None and d["cat"] not in ("fruta", "verdura", "pesca", "granja"):
        _entero(s, cx, cy, r, ident, col, tam, t)       # nada que pelar
        return
    if d is not None and ident != "huevo":
        viejo = d["color"]
        d["color"] = fl
        try:
            catalogo.dibujar_item(s, ident, cx, cy, tam)
        finally:
            d["color"] = viejo
        e(s, aclarar(fl, .5), cx - r * .25, cy - r * .2, r * .2, r * .12, False)
    elif ident == "huevo":
        e(s, (255, 253, 248), cx, cy, r * 1.2, r * 1.6, (225, 215, 195), 2)
        e(s, (255, 255, 255), cx - r * .2, cy - r * .3, r * .25, r * .4, False)
    else:
        _entero(s, cx, cy, r, ident, col, tam, t)
        return
    # cascara enroscada al lado
    sk = oscurecer(col, 0.0)
    pts = [(cx + r * .72 + math.cos(i * .8) * r * (.06 + .018 * i), cy + r * .55 + i * r * .04 + math.sin(i * .8) * r * (.05 + .01 * i))
           for i in range(10)]
    pygame.draw.lines(s, oscurecer(sk, .3), False, [(int(a), int(b)) for a, b in pts], 5)
    pygame.draw.lines(s, sk, False, [(int(a), int(b)) for a, b in pts], 3)


def _entero(s, cx, cy, r, ident, col, tam, t):
    if ident in _PROPIOS:
        _PROPIOS[ident](s, cx, cy, r, t)
    elif ident in _PSEUDO_DIB:
        _PSEUDO_DIB[ident](s, cx, cy, r, t)
    elif ident in catalogo.ITEMS:
        catalogo.dibujar_item(s, ident, cx, cy, tam)
    else:
        _desconocido(s, cx, cy, r, ident)


def _desconocido(s, cx, cy, r, ident):
    h = _hash(ident)
    col = ((h & 0xff) // 2 + 120, ((h >> 8) & 0xff) // 2 + 120, ((h >> 16) & 0xff) // 2 + 120)
    c(s, col, cx, cy, r * .82)
    letra = (str(ident or "?")[:1] or "?").upper()
    try:
        if not pygame.font.get_init():
            pygame.font.init()
        f = pygame.font.Font(None, max(8, int(r * 1.3)))
        im = f.render(letra, True, (255, 255, 255))
        sh = f.render(letra, True, oscurecer(col, .55))
        s.blit(sh, sh.get_rect(center=(int(cx + 1), int(cy + 2))))
        s.blit(im, im.get_rect(center=(int(cx), int(cy))))
    except Exception:
        pass


def _solido_tipo(ident, forma):
    return forma in ("bolsa", "frasco", "botella", "semilla", "gema") and ident not in _PROPIOS


def _dibujar(ident, estado, tam, t):
    S = int(tam * 1.6) + 4
    s = pygame.Surface((S, S), pygame.SRCALPHA)
    cx = cy = S / 2
    r = tam / 2
    col = _color(ident)
    forma = _forma(ident)
    es_pseudo = ident in _PSEUDO_DIB
    rng = Random(_hash(ident) + 17)
    if estado == "pelado":
        _pelado(s, cx, cy, r, ident, col, tam, t)
    elif estado == "cortado":
        if es_pseudo:
            _entero(s, cx, cy, r, ident, col, tam, t)
            for k in (-.35, 0, .35):
                lin(s, (255, 255, 255), (cx + k * r - r * .15, cy - r * .7), (cx + k * r + r * .15, cy + r * .7), 3)
                lin(s, INK, (cx + k * r - r * .15 + 3, cy - r * .7), (cx + k * r + r * .15 + 3, cy + r * .7), 1)
        else:
            _cortado(s, cx, cy, r, ident, col, forma, t)
    elif estado in ("rallado", "picado"):
        base = _flesh(ident, col) if not es_pseudo else col
        if ident == "queso":
            base = (252, 215, 90)
        if ident == "chocolate":
            base = (120, 72, 45)
        if ident in ("lechuga", "espinaca", "alga"):
            base = col
        _monton(s, cx, cy, r, base, rng, 70 if estado == "rallado" else 60, estado)
    elif estado == "batido":
        base = _flesh(ident, col) if ident == "huevo" else col
        if ident == "huevo":
            base = (255, 225, 110)
        _espuma(s, cx, cy, r, t, _mezcla(base, (255, 245, 210), .25))
    elif estado == "masa":
        neutro = _mezcla(col, PSEUDO_COL["masa"], .78)
        _masa(s, cx, cy, r, t, neutro)
        if ident not in ("harina", "masa") and not es_pseudo:
            for i in range(7):
                a = rng.uniform(0, 6.28)
                d = rng.uniform(.1, .6)
                c(s, oscurecer(col, .1), cx + math.cos(a) * r * .7 * d, cy + r * .1 + math.sin(a) * r * .5 * d, r * .05, False)
    elif estado == "cocido":
        if ident == "huevo":
            _frito_huevo(s, cx, cy, r)
        elif _solido_tipo(ident, forma):
            _mancha(s, cx, cy + r * .1, r * .85, r * .65, _mezcla(col, (225, 175, 95), .45), rng, n=8)
        else:
            _entero(s, cx, cy, r, ident, col, tam, t)
            s.fill((22, 48, 74), special_flags=pygame.BLEND_RGB_SUB)
            s.fill((20, 14, 0), special_flags=pygame.BLEND_RGB_ADD)
            if ident in ("pescado", "carne", "pollo", "calamar", "langostino"):
                for k in (-.4, 0, .4):
                    lin(s, (110, 60, 30), (cx + k * r - r * .2, cy - r * .25), (cx + k * r + r * .2, cy + r * .35), 3)
        e(s, aclarar((240, 190, 80), .6), cx - r * .35, cy - r * .55, r * .22, r * .1, False)
        _vapor(s, cx, cy - r * .35, r, t)
    elif estado == "quemado":
        if ident == "huevo":
            _frito_huevo(s, cx, cy, r, True)
        elif _solido_tipo(ident, forma) or es_pseudo and ident in ("jugo", "salsa", "caldo"):
            _mancha(s, cx, cy + r * .1, r * .85, r * .65, (55, 45, 42), rng, n=8, hl=False)
        else:
            _entero(s, cx, cy, r, ident, col, tam, t)
            s.fill((110, 120, 125), special_flags=pygame.BLEND_RGB_SUB)
        for i in range(6):
            a = rng.uniform(0, 6.28)
            d = rng.uniform(.1, .7)
            c(s, (20, 18, 20), cx + math.cos(a) * r * .65 * d, cy + math.sin(a) * r * .5 * d, r * rng.uniform(.05, .1), False)
        _humo(s, cx, cy - r * .3, r, t)
    else:
        _entero(s, cx, cy, r, ident, col, tam, t)
    return s


_ANIMADOS = ("batido", "cocido", "quemado")
_cache = {}


def _surf(ident, estado, tam, t):
    animado = estado in _ANIMADOS or ident in ("caldo", "batido", "crema_batida", "huevo_batido")
    k = (ident, estado, tam, int(t * 8) % 16 if animado else 0)
    s = _cache.get(k)
    if s is None:
        if len(_cache) > LIMITE_CACHE:
            _cache.clear()
        s = _cache[k] = _dibujar(ident, estado, tam, t)
    return s


def dibujar_ing(p, ident, x, y, tam=64, estado="entero", t=0.0):
    """Dibuja un ingrediente (id de catalogo o pseudo) en el estado indicado, centrado en (x, y)."""
    try:
        tam = max(6, int(tam))
        ident = str(ident) if ident is not None else "?"
        estado = estado if estado in ESTADOS else "entero"
        s = _surf(ident, estado, tam, float(t or 0.0))
        p.blit(s, s.get_rect(center=(int(x), int(y))))
    except Exception:
        try:
            pygame.draw.circle(p, (200, 200, 215), (int(x), int(y)), max(3, int(tam / 3)))
        except Exception:
            pass


# ----------------------------------------------------------------------------- tazon con contenido
def dibujar_tazon(p, x, y, contenido=(), tam=90):
    """Cuenco visto de lado con lo que lleva dentro: contenido = [(ident, estado), ...] (maximo 6 visibles)."""
    try:
        tam = max(20, int(tam))
        R = tam / 2
        S = int(tam * 2)
        s = pygame.Surface((S, S), pygame.SRCALPHA)
        cx, cy = S / 2, S / 2 + R * .05
        borde = (235, 240, 250)
        e(s, (150, 120, 95), cx, cy - R * .05, R * 1.9, R * .55)
        e(s, (190, 160, 130), cx, cy - R * .02, R * 1.65, R * .42, False)
        items = list(contenido or [])[:6]
        n = len(items)
        for i, it in enumerate(items):
            try:
                ident, est = it
            except Exception:
                ident, est = it, "entero"
            ps = R * (1.05 if n <= 2 else .9 if n <= 4 else .8)
            if n == 1:
                px, py = cx, cy - R * .3
            else:
                f = i / (n - 1) - .5
                px = cx + f * R * 1.1
                py = cy - R * (.3 + .1 * ((i % 2) * 2 - 1) * (1 if n > 2 else 0.2))
            su = _surf(str(ident), est if est in ESTADOS else "entero", int(ps), 0.0)
            s.blit(su, su.get_rect(center=(int(px), int(py))))
        pts = [(cx - R * .95, cy - R * .02)] + [(cx + math.cos(a) * R * .95, cy - R * .02 + math.sin(a) * R * .88)
                                                 for a in [i * math.pi / 16 for i in range(17)]]
        poli(s, (130, 195, 235), pts)
        pygame.draw.arc(s, (240, 248, 255), pygame.Rect(int(cx - R * .88), int(cy - R * .2), int(R * 1.76), int(R * 1.0)), 3.5, 5.0, 3)
        lin(s, (252, 246, 205), (cx - R * .8, cy + R * .3), (cx + R * .8, cy + R * .3), max(3, R * .1))
        for k in (-.55, -.18, .18, .55):
            c(s, (255, 225, 120), cx + k * R * 1.2, cy + R * .3, R * .045, False)
        pygame.draw.arc(s, borde, pygame.Rect(int(cx - R * .95), int(cy - R * .3), int(R * 1.9), int(R * .56)), math.pi, 2 * math.pi, 3)
        pygame.draw.arc(s, (190, 200, 220), pygame.Rect(int(cx - R * .95), int(cy - R * .3), int(R * 1.9), int(R * .56)), math.pi, 2 * math.pi, 1)
        lin(s, borde, (cx - R * .95, cy - R * .02), (cx - R * .95 + 1, cy - R * .02), 3)
        p.blit(s, s.get_rect(center=(int(x), int(y))))
    except Exception:
        try:
            pygame.draw.circle(p, (130, 195, 235), (int(x), int(y)), max(5, int(tam / 3)))
        except Exception:
            pass
