"""Arte de la Granja: animales, cultivos, parcelas, estanques y escenarios (todo con codigo).

Convenciones: los animales y cultivos se dibujan con (x, y) en el SUELO (los pies / la base);
'esc' es la escala; 'mirando' = 1 derecha, -1 izquierda; 't' es el tiempo para animar.
"""

import math
import random

import pygame

from nucleo import aclarar, oscurecer

V2 = pygame.Vector2

CULTIVOS = ("zanahoria", "tomate", "lechuga", "papa", "maiz", "calabaza", "cebolla", "pimiento", "espinaca", "pepino")
# dias de riego que necesita cada cultivo para madurar
DIAS_CULTIVO = {"zanahoria": 2, "tomate": 3, "lechuga": 1, "papa": 2, "maiz": 3, "calabaza": 4,
                "cebolla": 2, "pimiento": 3, "espinaca": 1, "pepino": 2}
TIPOS_ANIMAL = ("gallina", "oveja", "vaca")
# alto aproximado de cada animal (para colocar la burbuja encima)
ALTO_ANIMAL = {"gallina": 82, "oveja": 96, "vaca": 132}

VERDE = (70, 170, 70)
VERDE_OSC = (40, 125, 55)


# =====================================================================
#  Utilidades
# =====================================================================

def _el(p, color, cx, cy, w, h, borde=None, grosor=2):
    r = pygame.Rect(0, 0, max(2, int(w)), max(2, int(h)))
    r.center = (int(cx), int(cy))
    pygame.draw.ellipse(p, color, r)
    if borde:
        pygame.draw.ellipse(p, borde, r, grosor)


def _circ(p, color, cx, cy, r, borde=None, grosor=2):
    pygame.draw.circle(p, color, (int(cx), int(cy)), max(1, int(r)))
    if borde:
        pygame.draw.circle(p, borde, (int(cx), int(cy)), max(1, int(r)), grosor)


def _hoja(p, x, y, ang, largo, ancho, color, borde=None):
    """Hoja en forma de lente que sale de (x, y) con el angulo dado (grados, 0 = derecha, -90 = arriba)."""
    a = math.radians(ang)
    d = V2(math.cos(a), math.sin(a))
    n = V2(-d.y, d.x)
    pts = []
    for lado in (1, -1):
        rango = range(0, 9) if lado == 1 else range(8, -1, -1)
        for k in rango:
            u = k / 8
            q = V2(x, y) + d * largo * u + n * lado * ancho * math.sin(math.pi * u)
            pts.append((q.x, q.y))
    pygame.draw.polygon(p, color, pts)
    if borde:
        pygame.draw.polygon(p, borde, pts, 1)


def _sombra(p, x, y, w, h):
    s = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (30, 50, 20, 70), s.get_rect())
    p.blit(s, (int(x - w / 2), int(y - h / 2)))


def _degradado(sup, rect, c1, c2):
    rect = pygame.Rect(rect)
    for yy in range(rect.height):
        f = yy / max(1, rect.height - 1)
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * f) for i in range(3))
        pygame.draw.line(sup, col, (rect.x, rect.y + yy), (rect.right - 1, rect.y + yy))


# =====================================================================
#  Iconos pequenos
# =====================================================================

def dibujar_gota(p, x, y, r, color=(70, 150, 235)):
    """Gota de agua centrada en (x, y)."""
    x, y = int(x), int(y)
    pygame.draw.circle(p, color, (x, y + int(r * 0.3)), int(r * 0.72))
    pygame.draw.polygon(p, color, [(x, y - int(r * 1.0)), (x - int(r * 0.66), y + int(r * 0.05)),
                                   (x + int(r * 0.66), y + int(r * 0.05))])
    pygame.draw.circle(p, aclarar(color, 0.65), (x - int(r * 0.25), y + int(r * 0.2)), max(2, int(r * 0.2)))


def dibujar_moneda(p, x, y, r=14):
    x, y = int(x), int(y)
    pygame.draw.circle(p, (200, 140, 20), (x, y), int(r))
    pygame.draw.circle(p, (255, 213, 70), (x, y), int(r - 2))
    pygame.draw.circle(p, (255, 236, 150), (x - int(r * 0.25), y - int(r * 0.25)), max(2, int(r * 0.3)))
    pygame.draw.circle(p, (200, 140, 20), (x, y), int(r * 0.6), 2)


def dibujar_luna(p, x, y, r, color=(250, 235, 150)):
    s = pygame.Surface((int(r * 2.4), int(r * 2.4)), pygame.SRCALPHA)
    c = (s.get_width() // 2, s.get_height() // 2)
    pygame.draw.circle(s, color, c, int(r))
    pygame.draw.circle(s, (0, 0, 0, 0), (c[0] + int(r * 0.5), c[1] - int(r * 0.25)), int(r * 0.85))
    p.blit(s, (int(x - s.get_width() / 2), int(y - s.get_height() / 2)))


def dibujar_cubo(p, x, y, r=18):
    """Balde de pescador."""
    x, y = int(x), int(y)
    pts = [(x - r, y - int(r * 0.6)), (x + r, y - int(r * 0.6)), (x + int(r * 0.7), y + r), (x - int(r * 0.7), y + r)]
    pygame.draw.polygon(p, (200, 90, 70), pts)
    pygame.draw.polygon(p, (110, 40, 40), pts, 2)
    pygame.draw.arc(p, (90, 90, 100), (x - r, y - int(r * 1.5), 2 * r, int(r * 1.6)), 0, math.pi, 3)
    pygame.draw.line(p, (240, 140, 120), (x - int(r * 0.6), y - int(r * 0.3)), (x - int(r * 0.4), y + int(r * 0.6)), 3)


def dibujar_burbuja(p, x, y, r, t, frac=0.0, aviso=False):
    """Burbuja de ayuda con cola. Devuelve el centro (x, y) donde dibujar el icono."""
    y = y + math.sin(t * 3.2 + x * 0.02) * 3
    x, y = int(x), int(y)
    s = pygame.Surface((int(r * 2 + 12), int(r * 2 + 30)), pygame.SRCALPHA)
    cx, cy = s.get_width() // 2, int(r + 4)
    pygame.draw.polygon(s, (255, 255, 255, 235), [(cx - 8, cy + r - 4), (cx + 8, cy + r - 4), (cx, cy + r + 14)])
    pygame.draw.circle(s, (255, 255, 255, 235), (cx, cy), int(r))
    col = (255, 170, 40) if aviso else (60, 100, 170)
    pygame.draw.circle(s, col, (cx, cy), int(r), 3)
    p.blit(s, (x - cx, y - cy))
    if frac > 0:
        rect = pygame.Rect(0, 0, int(r * 2 + 8), int(r * 2 + 8))
        rect.center = (x, y)
        pygame.draw.arc(p, (255, 205, 40), rect, math.pi / 2, math.pi / 2 + 2 * math.pi * min(1.0, frac), 6)
    return x, y


def dibujar_regadera(p, x, y, t, regando=True):
    """Regadera con la que se riega (el centro queda en (x, y))."""
    s = pygame.Surface((120, 100), pygame.SRCALPHA)
    pygame.draw.rect(s, (80, 150, 215), (30, 38, 52, 40), border_radius=10)
    pygame.draw.rect(s, (40, 90, 150), (30, 38, 52, 40), 3, border_radius=10)
    pygame.draw.polygon(s, (80, 150, 215), [(30, 56), (30, 66), (8, 36), (8, 28)])
    pygame.draw.polygon(s, (40, 90, 150), [(30, 56), (30, 66), (8, 36), (8, 28)], 2)
    pygame.draw.ellipse(s, (60, 120, 185), (0, 18, 18, 16))
    pygame.draw.arc(s, (40, 90, 150), (62, 28, 36, 40), -1.2, 1.5, 5)
    pygame.draw.ellipse(s, (130, 190, 240), (38, 44, 20, 8))
    giro = pygame.transform.rotozoom(s, 18 if regando else 0, 1.0)
    p.blit(giro, giro.get_rect(center=(int(x), int(y))))
    # punta de la regadera (aprox.) para las gotas
    return V2(x - 44, y + 4)


def dibujar_brillo(p, x, y, r, t, fase=0.0):
    k = 0.6 + 0.4 * math.sin(t * 5 + fase)
    rr = r * k
    col = (255, 245, 170)
    pygame.draw.polygon(p, col, [(x, y - rr), (x + rr * 0.28, y - rr * 0.28), (x + rr, y), (x + rr * 0.28, y + rr * 0.28),
                                 (x, y + rr), (x - rr * 0.28, y + rr * 0.28), (x - rr, y), (x - rr * 0.28, y - rr * 0.28)])


# =====================================================================
#  Animales
# =====================================================================

def dibujar_gallina(p, x, y, esc=1.0, t=0.0, fase=0.0, mirando=1):
    s, m = esc, mirando
    resp = math.sin(t * 2.4 + fase)
    ph = (t * 0.5 + fase * 0.37) % 1.0
    pico = math.sin(ph / 0.35 * math.pi) ** 2 if ph < 0.35 else 0.0     # picotea de vez en cuando

    def X(dx):
        return x + m * dx * s

    def Y(dy):
        return y + dy * s

    _sombra(p, x, y, 62 * s, 12 * s)
    for dx in (-5, 9):                                                   # patas
        pygame.draw.line(p, (235, 150, 30), (X(dx), Y(-16)), (X(dx), Y(-2)), max(2, int(4 * s)))
        for g in (-6, 0, 6):
            pygame.draw.line(p, (235, 150, 30), (X(dx), Y(-2)), (X(dx + g * 0.9 + 4), Y(0)), max(2, int(3 * s)))
    for k, ang in enumerate((-60, -30, 0)):                              # cola
        a = math.radians(ang)
        pygame.draw.polygon(p, (230, 225, 215) if k != 1 else (205, 120, 60),
                            [(X(-22), Y(-36)), (X(-22 - 26 * math.cos(a)), Y(-36 + 30 * math.sin(a) - 22)),
                             (X(-14), Y(-52 + k * 6))])
    _el(p, (252, 250, 245), X(0), Y(-34 + resp * 0.8), 60 * s, (44 + resp * 2) * s, (205, 195, 180))
    _el(p, (235, 225, 205), X(-4), Y(-32), 30 * s, 22 * s, (205, 195, 180), 1)           # ala
    hx, hy = 24 + pico * 9, -53 + pico * 24
    _circ(p, (252, 250, 245), X(hx), Y(hy), 14 * s, (205, 195, 180))
    for k in range(3):                                                    # cresta
        _circ(p, (225, 50, 60), X(hx - 5 + k * 5), Y(hy - 15 + abs(k - 1) * 2), 5.5 * s)
    pygame.draw.polygon(p, (250, 175, 40), [(X(hx + 12), Y(hy - 3)), (X(hx + 25), Y(hy + 2)), (X(hx + 12), Y(hy + 6))])
    _circ(p, (225, 50, 60), X(hx + 9), Y(hy + 10), 4 * s)                 # barbilla
    if (t + fase) % 3.7 > 0.12:
        _circ(p, (30, 25, 40), X(hx + 4), Y(hy - 3), 2.6 * s)
        _circ(p, (255, 255, 255), X(hx + 3.4), Y(hy - 3.8), 0.9 * s)


def dibujar_vaca(p, x, y, esc=1.0, t=0.0, fase=0.0, mirando=1):
    s, m = esc, mirando
    resp = math.sin(t * 1.8 + fase)
    ph = (t * 0.22 + fase * 0.3) % 1.0
    pasta = math.sin(ph / 0.4 * math.pi) if ph < 0.4 else 0.0           # baja la cabeza a comer
    cola = math.sin(t * 2.6 + fase) * 7

    def X(dx):
        return x + m * dx * s

    def Y(dy):
        return y + dy * s

    blanco, mancha, rosa = (252, 250, 247), (60, 55, 62), (250, 175, 180)
    _sombra(p, x, y, 150 * s, 16 * s)
    for dx in (-44, 40):                                                  # patas del fondo
        pygame.draw.rect(p, (225, 222, 218), (X(dx) - 8 * s, Y(-48), 16 * s, 46 * s), border_radius=5)
        pygame.draw.rect(p, (60, 50, 50), (X(dx) - 8 * s, Y(-8), 16 * s, 8 * s), border_radius=3)
    pygame.draw.line(p, (60, 55, 62), (X(-62), Y(-86)), (X(-72 - cola), Y(-52)), max(3, int(5 * s)))   # cola
    _circ(p, (60, 55, 62), X(-72 - cola), Y(-48), 7 * s)
    _el(p, blanco, X(0), Y(-72 + resp * 0.8), 134 * s, (66 + resp * 2) * s, (190, 185, 180))
    _el(p, mancha, X(-28), Y(-82), 36 * s, 26 * s)
    _el(p, mancha, X(22), Y(-62), 30 * s, 24 * s)
    _el(p, rosa, X(-12), Y(-44), 28 * s, 14 * s, (210, 130, 140), 1)      # ubre
    for dx in (-28, 22):                                                  # patas del frente
        pygame.draw.rect(p, blanco, (X(dx) - 8 * s, Y(-50), 16 * s, 50 * s), border_radius=5)
        pygame.draw.rect(p, (190, 185, 180), (X(dx) - 8 * s, Y(-50), 16 * s, 50 * s), 2, border_radius=5)
        pygame.draw.rect(p, (60, 50, 50), (X(dx) - 8 * s, Y(-9), 16 * s, 9 * s), border_radius=3)
    hx, hy = 70 + pasta * 6, -82 + pasta * 34
    pygame.draw.polygon(p, (245, 235, 200), [(X(hx - 8), Y(hy - 20)), (X(hx - 14), Y(hy - 36)), (X(hx - 2), Y(hy - 22))])   # cuernos
    pygame.draw.polygon(p, (245, 235, 200), [(X(hx + 10), Y(hy - 20)), (X(hx + 16), Y(hy - 36)), (X(hx + 20), Y(hy - 18))])
    _el(p, blanco, X(hx - 14), Y(hy - 6), 20 * s, 12 * s, (190, 185, 180), 1)             # oreja
    _el(p, blanco, X(hx), Y(hy), 46 * s, 42 * s, (190, 185, 180))
    _el(p, mancha, X(hx - 8), Y(hy - 8), 18 * s, 16 * s)
    _el(p, rosa, X(hx + 12), Y(hy + 8), 28 * s, 22 * s, (210, 130, 140), 1)               # hocico
    _circ(p, (150, 80, 90), X(hx + 8), Y(hy + 8), 2.4 * s)
    _circ(p, (150, 80, 90), X(hx + 17), Y(hy + 8), 2.4 * s)
    if (t + fase) % 4.1 > 0.14:
        _circ(p, (30, 25, 40), X(hx + 6), Y(hy - 6), 3.2 * s)
        _circ(p, (255, 255, 255), X(hx + 5.2), Y(hy - 7), 1.1 * s)


def dibujar_oveja(p, x, y, esc=1.0, t=0.0, fase=0.0, mirando=1, esquilada=False):
    s, m = esc, mirando
    resp = math.sin(t * 2.0 + fase)
    ph = (t * 0.3 + fase * 0.5) % 1.0
    pasta = math.sin(ph / 0.4 * math.pi) if ph < 0.4 else 0.0

    def X(dx):
        return x + m * dx * s

    def Y(dy):
        return y + dy * s

    lana, borde = (250, 248, 240), (205, 200, 190)
    _sombra(p, x, y, 110 * s, 14 * s)
    for dx in (-24, -8, 14, 28):                                          # patas
        pygame.draw.rect(p, (70, 62, 65), (X(dx) - 4 * s, Y(-34), 8 * s, 34 * s), border_radius=3)
    cx, cy = X(0), Y(-56)
    r = 26 * s * (1 + resp * 0.02)
    puntos = [(-30, -4, 24), (-14, -20, 24), (8, -22, 24), (28, -8, 22), (30, 12, 20), (10, 18, 24),
              (-14, 16, 24), (-32, 10, 20), (0, 0, 28)]
    for dx, dy, rr in puntos:                                              # contorno de la lana
        _circ(p, borde, cx + m * dx * s, cy + dy * s, rr * s * (1 + resp * 0.02) + 2)
    for dx, dy, rr in puntos:
        _circ(p, lana, cx + m * dx * s, cy + dy * s, rr * s * (1 + resp * 0.02))
    hx, hy = 44 + pasta * 4, -52 + pasta * 22
    for lado in (-1, 1):                                                   # orejas
        _el(p, (90, 80, 82), X(hx - 6 + lado * 14), Y(hy - 6 + lado * 2), 20 * s, 10 * s, None)
    _el(p, (95, 85, 88), X(hx), Y(hy), 32 * s, 38 * s, (60, 52, 55))
    _circ(p, lana, X(hx - 2), Y(hy - 19), 11 * s, borde, 1)
    if (t + fase) % 3.3 > 0.12:
        _circ(p, (255, 255, 255), X(hx + 6), Y(hy - 4), 4 * s)
        _circ(p, (20, 20, 30), X(hx + 7), Y(hy - 4), 2 * s)
    pygame.draw.arc(p, (40, 30, 35), (int(X(hx + 6) - 5 * s), int(Y(hy + 6)), int(10 * s), int(8 * s)), 3.3, 6.1, 2)


def dibujar_animal(p, tipo, x, y, esc=1.0, t=0.0, fase=0.0, mirando=1):
    if tipo == "vaca":
        dibujar_vaca(p, x, y, esc, t, fase, mirando)
    elif tipo == "oveja":
        dibujar_oveja(p, x, y, esc, t, fase, mirando)
    else:
        dibujar_gallina(p, x, y, esc, t, fase, mirando)


# =====================================================================
#  Cultivos (4 etapas: 0 semilla, 1 brote, 2 planta, 3 lista para cosechar)
# =====================================================================

def _monticulo(p, x, y, w=46):
    _el(p, (92, 58, 35), x, y, w, w * 0.34)
    _el(p, (125, 82, 52), x - w * 0.1, y - w * 0.04, w * 0.55, w * 0.18)


def dibujar_cultivo(p, cultivo, etapa, x, y, esc=1.0, t=0.0):
    """Dibuja el cultivo con la base en (x, y). etapa 0..3."""
    etapa = max(0, min(3, int(etapa)))
    s = esc
    bal = math.sin(t * 1.6 + x * 0.03) * (1 + etapa)           # balanceo con el viento
    _monticulo(p, x, y, 50 * s)
    if etapa == 0:
        for dx in (-8, 4, 12):
            _el(p, (230, 205, 150), x + dx * s, y - 1 * s, 6 * s, 4 * s)
        pygame.draw.line(p, (130, 200, 90), (x, y - 3 * s), (x + 1, y - 9 * s), 2)
        return
    if cultivo == "zanahoria":
        n, largo = {1: (2, 18), 2: (5, 40), 3: (7, 52)}[etapa]
        if etapa == 3:
            _el(p, (245, 140, 30), x, y - 3 * s, 26 * s, 14 * s, (180, 90, 10))
            _el(p, (255, 190, 100), x - 5 * s, y - 5 * s, 8 * s, 4 * s)
        for k in range(n):
            ang = -90 + (k - (n - 1) / 2) * (110 / max(1, n)) + bal * 1.5
            _hoja(p, x, y - 4 * s, ang, largo * s, 4.5 * s, (80, 180, 75), VERDE_OSC)
    elif cultivo == "tomate":
        alto = {1: 24, 2: 56, 3: 74}[etapa] * s
        if etapa >= 2:
            pygame.draw.line(p, (150, 110, 60), (x + 12 * s, y), (x + 12 * s, y - alto - 8 * s), 4)
        pygame.draw.line(p, (60, 150, 60), (x, y), (x + bal * 0.5, y - alto), 4)
        for k in range(2 + etapa * 2):
            yy = y - alto * (0.25 + 0.75 * k / (2 + etapa * 2))
            lado = 1 if k % 2 else -1
            _hoja(p, x + bal * 0.4, yy, -90 + lado * (50 + 10 * (k % 3)) + bal, (16 + etapa * 6) * s, 6 * s, (85, 185, 80), VERDE_OSC)
        if etapa == 2:
            for k in range(2):
                _circ(p, (255, 225, 70), x - 10 * s + k * 20 * s + bal * 0.5, y - alto * (0.55 + 0.2 * k), 3.5 * s)
        if etapa == 3:
            for dx, dy in ((-13, 0.42), (13, 0.58), (-2, 0.8)):
                cx, cy = x + dx * s + bal * 0.4, y - alto * dy
                _circ(p, (225, 55, 45), cx, cy, 11 * s, (150, 25, 25))
                _circ(p, (255, 150, 140), cx - 3 * s, cy - 4 * s, 3 * s)
                _hoja(p, cx, cy - 9 * s, -90, 7 * s, 3 * s, (60, 160, 60))
    elif cultivo == "lechuga":
        n, largo = {1: (3, 14), 2: (5, 26), 3: (8, 36)}[etapa]
        for k in range(n):
            ang = -90 + (k - (n - 1) / 2) * (170 / n) + bal
            _hoja(p, x, y - 3 * s, ang, largo * s, (7 + etapa * 3) * s, (115, 205, 95), (50, 130, 55))
        if etapa == 3:
            for dx, dy, rr in ((0, -22, 16), (-11, -16, 13), (11, -16, 13)):
                _circ(p, (150, 225, 120), x + dx * s + bal * 0.3, y + dy * s, rr * s, (60, 140, 60))
            _circ(p, (190, 240, 150), x - 3 * s, y - 28 * s, 6 * s)
    elif cultivo == "papa":
        n, largo = {1: (2, 16), 2: (5, 30), 3: (7, 36)}[etapa]
        for k in range(n):
            ang = -90 + (k - (n - 1) / 2) * (130 / n) + bal
            _hoja(p, x, y - 3 * s, ang, largo * s, 7 * s, (45, 140, 65), (25, 90, 45))
        if etapa >= 2:
            for dx, dy in ((-9, -24), (8, -30), (0, -38)):
                _circ(p, (250, 250, 250), x + dx * s + bal * 0.5, y + dy * s * (1 if etapa == 3 else 0.7), 3.5 * s, (200, 180, 220), 1)
        if etapa == 3:
            for dx, dy, w in ((-12, -2, 18), (10, -1, 20), (0, 2, 16)):
                _el(p, (205, 165, 105), x + dx * s, y + dy * s, w * s, 12 * s, (150, 110, 60))
                _circ(p, (150, 110, 60), x + dx * s + 3, y + dy * s, 1.4 * s)
    elif cultivo == "maiz":
        alto = {1: 24, 2: 62, 3: 94}[etapa] * s
        pygame.draw.line(p, (110, 175, 70), (x, y), (x + bal * 0.4, y - alto), max(3, int(5 * s)))
        for k in range(1 + etapa * 2):
            yy = y - alto * (0.15 + 0.7 * k / (1 + etapa * 2))
            lado = 1 if k % 2 else -1
            _hoja(p, x + bal * 0.3, yy, -90 + lado * 62 + bal, (24 + etapa * 8) * s, 5 * s, (105, 185, 65), (50, 120, 45))
        if etapa == 3:
            for lado, dy in ((-1, 0.55), (1, 0.7)):
                cx, cy = x + lado * 11 * s + bal * 0.3, y - alto * dy
                _el(p, (250, 210, 60), cx, cy, 14 * s, 30 * s, (190, 140, 20))
                _hoja(p, cx, cy + 12 * s, -90 + lado * 18, 26 * s, 6 * s, (100, 180, 70), (50, 120, 45))
            for k in range(5):
                pygame.draw.line(p, (225, 190, 90), (x + bal * 0.4, y - alto), (x + (k - 2) * 7 * s + bal * 0.6, y - alto - 14 * s), 2)
    elif cultivo == "calabaza":
        n = {1: 2, 2: 4, 3: 5}[etapa]
        for k in range(n):
            lado = -1 if k % 2 else 1
            cx = x + lado * (8 + k * 8) * s
            cy = y - (4 + 5 * (k % 2)) * s - etapa * 4 * s
            pygame.draw.line(p, (60, 140, 60), (x, y - 3 * s), (cx, cy + 4 * s), 3)
            _el(p, (85, 175, 80), cx, cy - 6 * s * etapa * 0.5, (14 + etapa * 6) * s, (11 + etapa * 5) * s, VERDE_OSC)
        if etapa == 2:
            _circ(p, (255, 215, 60), x + 6 * s, y - 24 * s, 5 * s, (200, 140, 20))
        if etapa == 3:
            _el(p, (245, 150, 35), x - 4 * s, y - 14 * s, 54 * s, 40 * s, (180, 90, 10))
            for dx in (-14, -2, 10):
                pygame.draw.arc(p, (200, 105, 20), (int(x - 4 * s + dx * s - 6 * s), int(y - 33 * s), int(12 * s), int(38 * s)), 1.6, 4.7, 2)
            pygame.draw.line(p, (95, 130, 50), (x - 4 * s, y - 33 * s), (x - 1 * s, y - 42 * s), max(3, int(5 * s)))
            _el(p, (255, 200, 110), x - 14 * s, y - 20 * s, 12 * s, 8 * s)
    elif cultivo == "cebolla":
        n, largo = {1: (2, 16), 2: (5, 34), 3: (6, 44)}[etapa]
        if etapa == 3:
            for dx, ancho in ((-11, 20), (11, 20), (0, 24)):
                _el(p, (205, 120, 165), x + dx * s, y - 4 * s, ancho * s, 18 * s, (150, 70, 115))
            _el(p, (240, 190, 215), x - 3 * s, y - 8 * s, 8 * s, 5 * s)
        for k in range(n):
            ang = -90 + (k - (n - 1) / 2) * (80 / n) + bal * 1.5
            _hoja(p, x, y - 6 * s, ang, largo * s, 3.5 * s, (95, 185, 85), VERDE_OSC)
    elif cultivo == "pimiento":
        alto = {1: 22, 2: 50, 3: 62}[etapa] * s
        pygame.draw.line(p, (60, 150, 60), (x, y), (x + bal * 0.5, y - alto), 4)
        for k in range(2 + etapa * 2):
            yy = y - alto * (0.25 + 0.75 * k / (2 + etapa * 2))
            lado = 1 if k % 2 else -1
            _hoja(p, x + bal * 0.4, yy, -90 + lado * (55 + 8 * (k % 3)) + bal, (15 + etapa * 5) * s, 6 * s, (80, 175, 75), VERDE_OSC)
        if etapa == 2:
            for k in range(2):
                _circ(p, (255, 255, 250), x - 8 * s + k * 16 * s + bal * 0.5, y - alto * (0.5 + 0.2 * k), 3.5 * s, (200, 200, 190), 1)
        if etapa == 3:
            for dx, dy in ((-13, 0.45), (13, 0.6), (0, 0.85)):
                cx, cy = x + dx * s + bal * 0.4, y - alto * dy
                _el(p, (225, 55, 45), cx, cy + 5 * s, 17 * s, 24 * s, (150, 25, 25))
                _el(p, (255, 150, 140), cx - 3 * s, cy, 4 * s, 9 * s)
                _hoja(p, cx, cy - 6 * s, -90, 7 * s, 3 * s, (60, 160, 60))
    elif cultivo == "espinaca":
        n, largo = {1: (3, 14), 2: (6, 26), 3: (9, 34)}[etapa]
        for k in range(n):
            ang = -90 + (k - (n - 1) / 2) * (150 / n) + bal
            _hoja(p, x, y - 3 * s, ang, largo * s, (5 + etapa * 2) * s, (55, 150, 75), (25, 95, 50))
        if etapa == 3:
            for dx, dy in ((-9, -14), (9, -14), (0, -24)):
                _el(p, (70, 170, 85), x + dx * s + bal * 0.3, y + dy * s, 16 * s, 22 * s, (30, 105, 55))
            _el(p, (130, 210, 130), x - 2 * s, y - 28 * s, 5 * s, 9 * s)
    elif cultivo == "pepino":
        n = {1: 2, 2: 4, 3: 5}[etapa]
        for k in range(n):
            lado = -1 if k % 2 else 1
            cx = x + lado * (8 + k * 7) * s
            cy = y - (6 + 8 * (k % 2)) * s - etapa * 6 * s
            pygame.draw.line(p, (60, 140, 60), (x, y - 3 * s), (cx, cy + 4 * s), 3)
            _hoja(p, cx, cy, -90 + lado * 55 + bal, (10 + etapa * 5) * s, 6 * s, (85, 175, 80), VERDE_OSC)
        if etapa == 2:
            _circ(p, (255, 215, 60), x + 6 * s, y - 30 * s, 5 * s, (200, 140, 20))
        if etapa == 3:
            for dx, dy, w in ((-12, -4, 38), (10, -14, 34)):
                _el(p, (70, 160, 80), x + dx * s, y + dy * s, w * s, 15 * s, (35, 100, 50))
                _el(p, (150, 215, 140), x + dx * s - 5 * s, y + dy * s - 3 * s, w * 0.5 * s, 4 * s)
    else:
        _hoja(p, x, y, -90, 20 * s, 5 * s, VERDE)


# =====================================================================
#  Parcelas y estanques
# =====================================================================

def dibujar_parcela(p, rect, regada=False, t=0.0, resalte=False):
    rect = pygame.Rect(rect)
    suelo = (96, 62, 40) if regada else (140, 98, 62)
    pygame.draw.rect(p, oscurecer(suelo, 0.45), rect.move(0, 5), border_radius=16)
    pygame.draw.rect(p, suelo, rect, border_radius=16)
    for k in range(5):                                                    # surcos
        yy = rect.y + 22 + k * (rect.height - 40) / 4
        pygame.draw.line(p, oscurecer(suelo, 0.28), (rect.x + 14, yy), (rect.right - 14, yy), 4)
        pygame.draw.line(p, aclarar(suelo, 0.14), (rect.x + 14, yy + 4), (rect.right - 14, yy + 4), 2)
    if regada:
        for k in range(5):                                                # charquitos
            _el(p, (80, 110, 160), rect.x + 30 + k * (rect.width - 60) / 4, rect.y + 20 + (k * 37) % (rect.height - 40), 18, 7)
    pygame.draw.rect(p, (230, 215, 160) if resalte else (82, 52, 32), rect, 4, border_radius=16)


def _agua(w, h):
    clave = ("agua", w, h)
    if clave not in _cache:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        _degradado(s, (0, 0, w, h), (95, 200, 235), (30, 110, 190))
        m = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(m, (255, 255, 255, 255), (0, 0, w, h), border_radius=26)
        s.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        # reflejos del cielo (franjas diagonales translucidas)
        r = pygame.Surface((w, h), pygame.SRCALPHA)
        for k in range(4):
            x0 = k * w / 3.2 - 30
            pygame.draw.polygon(r, (255, 255, 255, 34), [(x0 + 50, 0), (x0 + 90, 0), (x0 + 30, h), (x0 - 10, h)])
        r.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(r, (0, 0))
        _cache[clave] = s
    return _cache[clave]


def dibujar_estanque(p, rect, t=0.0, resalte=False):
    """Estanque con borde de piedras, agua con reflejos y ondas. Devuelve el rect del agua."""
    rect = pygame.Rect(rect)
    borde = rect.inflate(26, 26)
    pygame.draw.rect(p, (110, 108, 105), borde.move(0, 5), border_radius=38)
    pygame.draw.rect(p, (165, 160, 152), borde, border_radius=36)
    rnd = random.Random(rect.x * 31 + rect.y)
    n = int((borde.width + borde.height) / 17)
    for k in range(n):                                                    # piedras alrededor
        u = k / n * 2 * (borde.width + borde.height)
        if u < borde.width:
            cx, cy = borde.x + u, borde.y + 7
        elif u < borde.width + borde.height:
            cx, cy = borde.right - 7, borde.y + (u - borde.width)
        elif u < 2 * borde.width + borde.height:
            cx, cy = borde.right - (u - borde.width - borde.height), borde.bottom - 7
        else:
            cx, cy = borde.x + 7, borde.bottom - (u - 2 * borde.width - borde.height)
        g = rnd.randint(150, 200)
        _el(p, (g, g - 4, g - 10), cx, cy, 20, 15, (95, 92, 88), 1)
    p.blit(_agua(rect.width, rect.height), rect.topleft)
    clip = p.get_clip()
    p.set_clip(rect.inflate(-8, -8))
    for k in range(3):                                                    # ondas que se expanden
        f = ((t * 0.33) + k / 3 + rect.x * 0.003) % 1.0
        r = 14 + f * 70
        cx = rect.x + rect.width * (0.25 + 0.25 * k)
        cy = rect.y + rect.height * (0.3 + 0.2 * ((k * 2) % 3))
        col = (200, 235, 250)
        rr = pygame.Rect(0, 0, int(r * 2), int(r * 0.8))
        rr.center = (int(cx), int(cy))
        pygame.draw.ellipse(p, col, rr, 2 if f < 0.7 else 1)
    for k in range(6):                                                    # destellos
        v = (t * 0.8 + k * 0.37 + rect.x) % 2.0
        if v < 0.5:
            gx = rect.x + 20 + (k * 53 + rect.x) % (rect.width - 40)
            gy = rect.y + 14 + (k * 71) % (rect.height - 28)
            pygame.draw.line(p, (235, 250, 255), (gx - 7, gy), (gx + 7, gy), 2)
    p.set_clip(clip)
    # nenufar
    lx, ly = rect.right - 34, rect.bottom - 26
    _el(p, (80, 175, 90), lx, ly, 42, 22, (40, 115, 55))
    pygame.draw.polygon(p, (60, 140, 220), [(lx, ly), (lx + 24, ly - 8), (lx + 24, ly + 3)])
    _circ(p, (255, 170, 200), lx - 3, ly - 3, 6, (200, 100, 140), 1)
    if resalte:
        pygame.draw.rect(p, (255, 240, 150), borde, 4, border_radius=36)
    return rect


# =====================================================================
#  Escenarios (se dibujan una vez y se guardan)
# =====================================================================

_cache = {}


def _colinas(sup, y0, color, amp, fase, alto_max):
    pts = [(0, alto_max)]
    for x in range(0, 1281, 20):
        pts.append((x, y0 + math.sin(x * 0.006 + fase) * amp + math.sin(x * 0.017 + fase * 2) * amp * 0.3))
    pts.append((1280, alto_max))
    pygame.draw.polygon(sup, color, pts)


def _cerca(sup, x0, x1, y, alto=44, color=(170, 120, 70)):
    pygame.draw.rect(sup, oscurecer(color, 0.3), (x0, y - alto * 0.55 + 3, x1 - x0, 9), border_radius=3)
    pygame.draw.rect(sup, color, (x0, y - alto * 0.55, x1 - x0, 9), border_radius=3)
    pygame.draw.rect(sup, oscurecer(color, 0.3), (x0, y - alto * 0.15 + 3, x1 - x0, 9), border_radius=3)
    pygame.draw.rect(sup, color, (x0, y - alto * 0.15, x1 - x0, 9), border_radius=3)
    x = x0
    while x <= x1:
        pygame.draw.rect(sup, oscurecer(color, 0.3), (x - 6 + 3, y - alto + 3, 14, alto + 4), border_radius=4)
        pygame.draw.rect(sup, aclarar(color, 0.1), (x - 6, y - alto, 14, alto + 4), border_radius=4)
        pygame.draw.line(sup, aclarar(color, 0.35), (x - 3, y - alto + 4), (x - 3, y - 4), 2)
        x += 70


def _arbol(sup, x, y, esc=1.0):
    pygame.draw.rect(sup, (110, 75, 45), (x - 11 * esc, y - 60 * esc, 22 * esc, 62 * esc), border_radius=6)
    for dx, dy, r in ((0, -100, 48), (-34, -76, 34), (34, -78, 36), (6, -128, 34)):
        _circ(sup, (75, 160, 80), x + dx * esc, y + dy * esc, r * esc, (45, 115, 60), 3)
    for dx, dy in ((-14, -110), (22, -92), (-30, -80)):
        _circ(sup, (225, 70, 60), x + dx * esc, y + dy * esc, 6 * esc)


def _flores(sup, rnd, n, caja, colores=((255, 120, 150), (255, 230, 90), (255, 255, 255), (170, 130, 255))):
    for _ in range(n):
        x = rnd.randint(caja[0], caja[2])
        y = rnd.randint(caja[1], caja[3])
        c = rnd.choice(colores)
        pygame.draw.line(sup, (60, 140, 60), (x, y), (x, y + 10), 2)
        for ang in range(0, 360, 72):
            pygame.draw.circle(sup, c, (int(x + 4 * math.cos(math.radians(ang))), int(y + 4 * math.sin(math.radians(ang)))), 3)
        pygame.draw.circle(sup, (255, 200, 40), (x, y), 2)


def _matas(sup, rnd, n, caja):
    for _ in range(n):
        x = rnd.randint(caja[0], caja[2])
        y = rnd.randint(caja[1], caja[3])
        for dx in (-4, 0, 4):
            pygame.draw.line(sup, (70, 150, 60), (x + dx, y), (x + dx * 2, y - 9), 2)


def _cielo(sup, alto, c1=(120, 190, 255), c2=(215, 240, 255)):
    _degradado(sup, (0, 0, 1280, alto), c1, c2)


def _sol(sup, x, y, r=54):
    for k, a in ((3, 28), (2, 50), (1, 80)):
        g = pygame.Surface((int(r * 2 * (1 + k * 0.5)),) * 2, pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 240, 150, a), (g.get_width() // 2,) * 2, g.get_width() // 2)
        sup.blit(g, (x - g.get_width() // 2, y - g.get_height() // 2))
    _circ(sup, (255, 225, 80), x, y, r, (255, 190, 40), 4)


def escenario(nombre):
    """Superficie 1280x720 con el fondo de 'granja', 'huerto' o 'pisci'."""
    if nombre in _cache:
        return _cache[nombre]
    sup = pygame.Surface((1280, 720))
    rnd = random.Random(sum(map(ord, nombre)) + 7)
    if nombre == "granja":
        _cielo(sup, 330)
        _sol(sup, 1130, 160)
        _colinas(sup, 250, (135, 200, 110), 22, 0.5, 400)
        _colinas(sup, 285, (110, 180, 90), 18, 2.2, 420)
        _degradado(sup, (0, 300, 1280, 420), (112, 182, 88), (92, 160, 72))
        _matas(sup, rnd, 90, (10, 310, 1270, 710))
        _flores(sup, rnd, 40, (10, 320, 1270, 700))
        # granero y silo
        pygame.draw.rect(sup, (170, 50, 45), (54, 150, 200, 150))
        pygame.draw.polygon(sup, (120, 35, 35), [(40, 154), (154, 78), (268, 154)])
        pygame.draw.polygon(sup, (190, 70, 60), [(54, 150), (154, 86), (254, 150)])
        pygame.draw.rect(sup, (250, 245, 235), (108, 200, 92, 100), 5)
        pygame.draw.line(sup, (250, 245, 235), (108, 200), (200, 300), 5)
        pygame.draw.line(sup, (250, 245, 235), (200, 200), (108, 300), 5)
        pygame.draw.circle(sup, (250, 230, 150), (154, 135), 14)
        pygame.draw.circle(sup, (250, 245, 235), (154, 135), 14, 3)
        pygame.draw.rect(sup, (200, 205, 215), (276, 140, 44, 160))
        pygame.draw.ellipse(sup, (170, 175, 190), (276, 124, 44, 34))
        pygame.draw.line(sup, (150, 155, 170), (276, 200), (320, 200), 3)
        pygame.draw.line(sup, (150, 155, 170), (276, 250), (320, 250), 3)
        _arbol(sup, 1210, 330, 1.0)
        # corral
        _el(sup, (205, 185, 120), 640, 480, 1130, 320, (170, 150, 90), 4)
        _el(sup, (215, 196, 132), 640, 470, 1000, 270)
        _cerca(sup, 70, 1210, 318, 52)
        _cerca(sup, 70, 1210, 628, 52)
        for yy in range(318, 630, 77):
            pygame.draw.rect(sup, (170, 120, 70), (64, yy - 36, 14, 80), border_radius=4)
            pygame.draw.rect(sup, (170, 120, 70), (1204, yy - 36, 14, 80), border_radius=4)
    elif nombre == "huerto":
        _cielo(sup, 260, (130, 200, 250), (225, 245, 255))
        _sol(sup, 1180, 130, 46)
        _colinas(sup, 190, (135, 200, 110), 18, 1.0, 300)
        _degradado(sup, (0, 220, 1280, 500), (118, 188, 92), (96, 164, 74))
        _matas(sup, rnd, 100, (10, 230, 1270, 710))
        _flores(sup, rnd, 30, (10, 240, 1270, 700))
        # el campo arado
        campo = pygame.Rect(262, 84, 920, 528)
        pygame.draw.rect(sup, (88, 58, 38), campo.move(0, 8), border_radius=24)
        pygame.draw.rect(sup, (126, 88, 56), campo, border_radius=24)
        for k in range(16):
            yy = campo.y + 14 + k * 33
            pygame.draw.line(sup, (108, 74, 46), (campo.x + 12, yy), (campo.right - 12, yy), 6)
        pygame.draw.rect(sup, (170, 120, 70), campo, 6, border_radius=24)
        _cerca(sup, 262, 1182, 616, 44)
        # espantapajaros
        sx, sy = 1226, 470
        pygame.draw.line(sup, (120, 85, 50), (sx, sy - 70), (sx, sy + 30), 7)
        pygame.draw.line(sup, (120, 85, 50), (sx - 42, sy - 40), (sx + 42, sy - 40), 7)
        pygame.draw.polygon(sup, (70, 120, 200), [(sx - 22, sy - 44), (sx + 22, sy - 44), (sx + 16, sy + 2), (sx - 16, sy + 2)])
        _circ(sup, (240, 210, 140), sx, sy - 70, 17, (180, 140, 80))
        pygame.draw.polygon(sup, (190, 150, 60), [(sx - 28, sy - 78), (sx + 28, sy - 78), (sx + 14, sy - 100), (sx - 14, sy - 100)])
        pygame.draw.line(sup, (190, 150, 60), (sx - 28, sy - 78), (sx + 28, sy - 78), 4)
        for dx in (-6, 6):
            _circ(sup, (40, 30, 40), sx + dx, sy - 72, 2)
        _arbol(sup, 140, 640, 0.8)
    else:                                                    # pisci
        _cielo(sup, 200, (140, 205, 245), (225, 245, 250))
        _colinas(sup, 150, (130, 195, 115), 16, 3.0, 260)
        _degradado(sup, (0, 170, 1280, 550), (112, 184, 96), (84, 150, 78))
        _matas(sup, rnd, 100, (10, 180, 1270, 710))
        _flores(sup, rnd, 28, (10, 190, 1270, 700))
        # juncos
        for jx in (292, 596, 902, 1206):
            for k in range(4):
                x = jx + k * 9 - 12
                h = 50 + (k * 17) % 28
                pygame.draw.line(sup, (80, 150, 60), (x, 560), (x + (k - 2) * 3, 560 - h), 3)
                if k % 2 == 0:
                    pygame.draw.line(sup, (120, 80, 50), (x + (k - 2) * 3, 560 - h), (x + (k - 2) * 3, 560 - h - 20), 6)
    _cache[nombre] = sup
    return sup


def nubes(p, t, alto=240):
    """Nubes que pasan despacio (dibujar justo despues del escenario)."""
    for i in range(5):
        x = (i * 290 + t * 12 * (1 + i % 3)) % (1280 + 240) - 120
        y = 96 + (i * 83) % (alto - 100)
        s = pygame.Surface((180, 80), pygame.SRCALPHA)
        for dx, dy, r in ((50, 46, 26), (86, 38, 32), (122, 48, 24), (84, 52, 26)):
            pygame.draw.circle(s, (255, 255, 255, 200), (dx, dy), r)
        p.blit(s, (x - 90, y - 40))
