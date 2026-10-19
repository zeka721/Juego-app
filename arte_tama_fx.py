"""Efectos de Tamagotchi: brillos aditivos, ataques por tipo y etapa, guias de gesto y aura de evolucion."""

import math

import pygame

from arte_tama_base import CONTORNO
from nucleo import aclarar, oscurecer

COL = {
    "agua": (70, 160, 255), "viento": (150, 228, 205), "fuego": (255, 130, 40),
    "hielo": (165, 228, 255), "tierra": (176, 128, 74), "electrico": (255, 226, 60),
}
INT = (0.62, 0.88, 1.18, 1.6)


def _I(etapa):
    return INT[max(0, min(3, int(etapa)))]


def _E(etapa):
    return max(0, min(3, int(etapa)))


def _ease(f):
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


def _rnd(i, k=0):
    v = math.sin(i * 127.1 + k * 311.7 + 0.37) * 43758.5453
    return v - math.floor(v)


def _lerp(a, b, f):
    return a + (b - a) * f


def _mix(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


# ---------------------------------------------------------------- brillos (cache)
_GL = {}
_GL_BYTES = [0]
_SF = {}


_MASTER = []


def _master():
    if not _MASTER:
        # Sin numpy (en Android no esta): discos concentricos, de afuera hacia adentro
        n = 256
        s = pygame.Surface((n, n))
        s.fill((0, 0, 0))
        mitad = n // 2
        for r in range(mitad, 0, -1):
            v = int(max(0.0, 1.0 - (r - 0.5) / mitad) ** 2.2 * 255)
            pygame.draw.circle(s, (v, v, v), (mitad, mitad), r)
        _MASTER.append(s)
    return _MASTER[0]


def _tex_glow(color, rq, aq):
    key = (color, rq, aq)
    s = _GL.get(key)
    if s is None:
        if _GL_BYTES[0] > 160e6:
            _GL.clear()
            _GL_BYTES[0] = 0
        n = rq * 2
        s = pygame.transform.smoothscale(_master(), (n, n))
        k = aq / 16.0
        s.fill((int(color[0] * k), int(color[1] * k), int(color[2] * k)), special_flags=pygame.BLEND_RGB_MULT)
        _GL[key] = s
        _GL_BYTES[0] += n * n * 4
    return s


def glow(p, x, y, r, color, alfa=255):
    """Brillo radial aditivo (BLEND_ADD)."""
    if r < 2 or alfa <= 4:
        return
    r = min(r, 420)
    rq = int(r) // 4 * 4 if r < 60 else (int(r) // 8 * 8 if r < 140 else int(r) // 32 * 32)
    rq = max(4, rq)
    aq = max(1, min(16, int(alfa / 16 + 0.5)))
    color = (int(color[0]) // 24 * 24 + 12, int(color[1]) // 24 * 24 + 12, int(color[2]) // 24 * 24 + 12)
    s = _tex_glow(color, rq, aq)
    p.blit(s, (int(x - rq), int(y - rq)), special_flags=pygame.BLEND_ADD)


def suave(p, x, y, r, color, alfa=200):
    """Circulo suave con transparencia normal (humo, polvo, espuma)."""
    if r < 2 or alfa <= 3:
        return
    r = min(r, 300)
    rq = max(8, int(r) // 8 * 8)
    color = (int(color[0]) // 16 * 16 + 8, int(color[1]) // 16 * 16 + 8, int(color[2]) // 16 * 16 + 8)
    key = ("s", color, rq)
    s = _SF.get(key)
    if s is None:
        if len(_SF) > 400:
            _SF.clear()
        s = pygame.Surface((rq * 2, rq * 2), pygame.SRCALPHA)
        for i in range(8, 0, -1):
            rr = rq * i / 8
            a = int(255 * min(1.0, (1.0 - (i - 1) / 8.0) * 1.15))
            pygame.draw.circle(s, color + (a if i < 8 else 120,), (rq, rq), int(rr))
        # versiones por capas: centro opaco, borde suave
        s2 = pygame.Surface((rq * 2, rq * 2), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            rr = rq * i / 10
            pygame.draw.circle(s2, color + (int(255 * (1 - i / 10) ** 0.6) if i > 1 else 255,), (rq, rq), max(1, int(rr)))
        s = s2
        _SF[key] = s
    s.set_alpha(int(max(0, min(255, alfa))))
    p.blit(s, (int(x - rq), int(y - rq)))


def destello_estrella(p, x, y, r, color, a=1.0, rot=0.0):
    """Estrella de 4 puntas brillante."""
    a = max(0.0, min(1.0, a))
    if a < 0.05 or r < 3:
        return
    glow(p, x, y, r * 0.9, color, int(200 * a))
    r = r * (0.35 + 0.65 * a)
    for k in range(2):
        ang = rot * 0.6 + k * math.pi / 2
        c, sn = math.cos(ang), math.sin(ang)
        w = max(1.5, r * 0.07)
        pts = [(x + c * r, y + sn * r), (x - sn * w, y + c * w), (x - c * r, y - sn * r), (x + sn * w, y - c * w)]
        pygame.draw.polygon(p, aclarar(color, 0.7), pts)
    glow(p, x, y, r * 0.35, (255, 255, 255), int(255 * a))


def _flash_pantalla(p, v, color=(255, 255, 255)):
    v = max(0.0, min(1.0, v))
    if v <= 0.01:
        return
    p.fill((int(color[0] * v), int(color[1] * v), int(color[2] * v)), special_flags=pygame.BLEND_ADD)


def _oscurecer_pantalla(p, v):
    v = int(max(0, min(120, v)))
    if v > 1:
        p.fill((v, v, v), special_flags=pygame.BLEND_SUB)


def _rot(pts, ang, cx, cy):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def _roca(p, x, y, r, rot=0.0, seed=0, color=(150, 108, 66), alfa=None):
    n = 8
    pts = []
    for i in range(n):
        a = math.pi * 2 * i / n
        rr = r * (0.78 + 0.32 * _rnd(i, seed))
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    P = _rot(pts, rot, x, y)
    pygame.draw.polygon(p, oscurecer(color, 0.18), P)
    # faceta clara arriba-izquierda
    cara = _rot([pts[5], pts[6], pts[7], pts[0], (0, 0)], rot, x, y)
    pygame.draw.polygon(p, aclarar(color, 0.28), cara)
    cara2 = _rot([pts[1], pts[2], pts[3], (0, 0)], rot, x, y)
    pygame.draw.polygon(p, oscurecer(color, 0.38), cara2)
    pygame.draw.polygon(p, CONTORNO, P, max(2, int(r * 0.12)))


def _cristal(p, x, y, w, h, rot=0.0, color=(165, 228, 255), brillo=1.0):
    """Cristal de hielo (rombo alargado con facetas); (x,y) = centro, punta arriba cuando rot=0."""
    top = (0, -h / 2)
    bot = (0, h / 2)
    izq = (-w / 2, -h * 0.1)
    der = (w / 2, -h * 0.1)
    cen = (0, h * 0.05)
    P = _rot([top, der, bot, izq], rot, x, y)
    pygame.draw.polygon(p, _mix(color, (255, 255, 255), 0.1 * brillo), P)
    pygame.draw.polygon(p, aclarar(color, 0.65), _rot([top, izq, cen], rot, x, y))
    pygame.draw.polygon(p, aclarar(color, 0.3), _rot([top, cen, der], rot, x, y))
    pygame.draw.polygon(p, oscurecer(color, 0.28), _rot([izq, cen, bot], rot, x, y))
    pygame.draw.polygon(p, oscurecer(color, 0.12), _rot([cen, der, bot], rot, x, y))
    pygame.draw.polygon(p, (40, 70, 130), P, max(2, int(w * 0.07)))


def _parte(p, tipo, x, y, s, rot=0.0, a=1.0, seed=0):
    """Particula pequena con forma de tipo."""
    if a <= 0.02 or s < 1:
        return
    c = COL[tipo]
    if tipo == "electrico":
        glow(p, x, y, s * 2.2, c, int(210 * a))
        for k in range(2):
            ang = rot + k * math.pi / 2
            dx, dy = math.cos(ang) * s * 1.2, math.sin(ang) * s * 1.2
            pygame.draw.line(p, _mix((0, 0, 0), (255, 245, 170), a), (x - dx, y - dy), (x + dx, y + dy), max(1, int(s * 0.3)))
    elif tipo == "fuego":
        glow(p, x, y, s * 2.4, (255, 110, 30), int(220 * a))
        glow(p, x, y, s * 1.1, (255, 230, 120), int(255 * a))
    elif tipo == "hielo":
        glow(p, x, y, s * 2.0, (120, 200, 255), int(120 * a))
        P = _rot([(0, -s * 1.2), (s * 0.7, 0), (0, s * 1.2), (-s * 0.7, 0)], rot, x, y)
        pygame.draw.polygon(p, _mix((60, 90, 150), (235, 250, 255), a), P)
        pygame.draw.polygon(p, (255, 255, 255), P, 1)
    elif tipo == "agua":
        pygame.draw.circle(p, _mix((20, 50, 110), (90, 170, 255), a), (x, y), s)
        pygame.draw.circle(p, (225, 245, 255), (x - s * 0.3, y - s * 0.3), max(1, s * 0.35))
    elif tipo == "viento":
        glow(p, x, y, s * 2.0, (150, 230, 210), int(110 * a))
        pts = []
        for i in range(8):
            f = i / 7
            pts.append((x + math.cos(rot + f * 2.0) * s * 2.2 * (f - 0.5), y + math.sin(rot + f * 2.0) * s * 1.2 * (f - 0.5) + math.sin(f * 6 + rot) * s * 0.4))
        pygame.draw.lines(p, _mix((20, 40, 40), (235, 255, 250), a), False, pts, max(1, int(s * 0.4)))
    else:
        pts = [(math.cos(i * 1.3) * s * (0.7 + 0.4 * _rnd(i, seed)), math.sin(i * 1.3) * s * (0.7 + 0.4 * _rnd(i, seed))) for i in range(5)]
        pygame.draw.polygon(p, _mix((30, 20, 10), (170, 125, 78), a), _rot(pts, rot, x, y))


# =====================================================================
# ATAQUE BASICO
# =====================================================================
def _zigzag(a, b, n, amp, seed):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts = [(ax, ay)]
    for i in range(1, n):
        f = i / n
        o = (_rnd(i, seed) - 0.5) * 2 * amp
        pts.append((ax + dx * f + nx * o, ay + dy * f + ny * o))
    pts.append((bx, by))
    return pts


def _rayo(p, pts, ancho, col=(255, 226, 60), halo=True):
    if halo:
        for i in range(0, len(pts), 3):
            glow(p, pts[i][0], pts[i][1], ancho * 3.2, col, 70)
    pygame.draw.lines(p, _mix(col, (0, 0, 0), 0.25), False, pts, int(ancho * 1.9))
    pygame.draw.lines(p, aclarar(col, 0.55), False, pts, max(2, int(ancho * 1.1)))
    pygame.draw.lines(p, (255, 255, 255), False, pts, max(1, int(ancho * 0.45)))


def dibujar_ataque_basico(p, tipo, etapa, x0, y0, x1, y1, f, t):
    if tipo not in COL:
        return
    I = _I(etapa)
    f = max(0.0, min(1.0, f))
    e = _ease(f) * 0.85 + f * 0.15
    x = _lerp(x0, x1, e)
    y = _lerp(y0, y1, e) - math.sin(math.pi * e) * 28
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    ang = math.atan2(uy, ux)
    r = 13 * I
    seed = int(t * 24)
    if tipo == "electrico":
        back = (x - ux * 85 * I, y - uy * 85 * I)
        pts = _zigzag(back, (x, y), 7, 11 * I, seed)
        _rayo(p, pts, 2.6 * I)
        glow(p, x, y, r * 2.6, (255, 230, 80), 230)
        glow(p, x, y, r * 1.2, (255, 255, 255), 255)
        for i in range(int(3 + 2 * etapa)):
            a = _rnd(i, seed) * 6.28
            d = r * (1.3 + _rnd(i, 5))
            _parte(p, "electrico", x + math.cos(a) * d, y + math.sin(a) * d, 3 + I, a, 1)
    elif tipo == "fuego":
        for j in range(14, 0, -1):
            ff = max(0.0, e - j * 0.018)
            px = _lerp(x0, x1, ff)
            py = _lerp(y0, y1, ff) - math.sin(math.pi * ff) * 28 + math.sin(t * 12 + j) * 4
            k = 1 - j / 15
            glow(p, px, py, r * (0.8 + 1.5 * k), (255, 90 + int(60 * k), 20), int(120 * k))
        glow(p, x, y, r * 2.6, (255, 100, 25), 190)
        suave(p, x, y, r * 1.05, (255, 150, 40), 255)
        suave(p, x, y, r * 0.7, (255, 215, 90), 255)
        glow(p, x, y, r * 0.8, (255, 255, 220), 255)
    elif tipo == "hielo":
        for j in range(8, 0, -1):
            ff = max(0.0, e - j * 0.025)
            px = _lerp(x0, x1, ff)
            py = _lerp(y0, y1, ff) - math.sin(math.pi * ff) * 28
            _parte(p, "hielo", px + math.sin(j * 3 + t * 5) * 6, py + math.cos(j * 2 + t * 5) * 6, 3 + 3 * (1 - j / 9) * I, j + t * 3, 1 - j / 9)
        glow(p, x, y, r * 2.4, (130, 205, 255), 150)
        _cristal(p, x, y, r * 1.1, r * 2.8, ang + math.pi / 2 + math.sin(t * 8) * 0.12)
    elif tipo == "agua":
        for j in range(7, 0, -1):
            ff = max(0.0, e - j * 0.03)
            px = _lerp(x0, x1, ff)
            py = _lerp(y0, y1, ff) - math.sin(math.pi * ff) * 28 + math.sin(j * 2.1 + t * 6) * 5
            suave(p, px, py, r * 0.55 * (1 - j / 9), (150, 205, 255), 190)
        glow(p, x, y, r * 2.0, (60, 140, 255), 110)
        # gota: circulo + cola
        cola = [(-r * 1.9, 0), (-r * 0.2, -r * 0.82), (-r * 0.2, r * 0.82)]
        pygame.draw.polygon(p, (60, 140, 245), _rot(cola, ang, x, y))
        pygame.draw.circle(p, (60, 140, 245), (x, y), r)
        pygame.draw.circle(p, (35, 80, 170), (x, y), r, max(2, int(r * 0.16)))
        pygame.draw.circle(p, (200, 235, 255), (x - r * 0.28, y - r * 0.32), r * 0.3)
    elif tipo == "viento":
        for j in range(1, 6):
            ff = max(0.0, e - j * 0.035)
            px = _lerp(x0, x1, ff)
            py = _lerp(y0, y1, ff) - math.sin(math.pi * ff) * 28 + (j - 3) * 6 * I
            pygame.draw.line(p, _mix((20, 60, 55), (225, 255, 245), 1 - j / 6), (px, py), (px - ux * 30 * I, py - uy * 30 * I), max(1, int(4 - j * 0.5)))
        glow(p, x, y, r * 2.2, (140, 235, 215), 110)
        # medialuna
        Rm = r * 1.9
        pts = []
        for i in range(13):
            a = ang - 1.05 + 2.1 * i / 12
            pts.append((x + math.cos(a) * Rm - ux * Rm * 0.55, y + math.sin(a) * Rm - uy * Rm * 0.55))
        for i in range(12, -1, -1):
            a = ang - 0.9 + 1.8 * i / 12
            pts.append((x + math.cos(a) * Rm * 0.74 - ux * Rm * 0.2, y + math.sin(a) * Rm * 0.74 - uy * Rm * 0.2))
        pygame.draw.polygon(p, (220, 255, 245), pts)
        pygame.draw.polygon(p, (70, 160, 150), pts, 2)
    else:
        for j in range(9, 0, -1):
            ff = max(0.0, e - j * 0.03)
            px = _lerp(x0, x1, ff)
            py = _lerp(y0, y1, ff) - math.sin(math.pi * ff) * 28
            suave(p, px, py + 6, r * (0.35 + 0.5 * (1 - j / 10)), (190, 160, 115), int(150 * (1 - j / 10)))
        _roca(p, x, y, r * 1.15, t * 9, 3)


# =====================================================================
# IMPACTO
# =====================================================================
def dibujar_impacto(p, tipo, etapa, x, y, f, t):
    if tipo not in COL:
        return
    I = _I(etapa)
    f = max(0.0, min(1.0, f))
    c = COL[tipo]
    a = 1 - f
    # destello central
    if f < 0.45:
        glow(p, x, y, (40 + 90 * f) * I, aclarar(c, 0.4), int(255 * (1 - f / 0.45)))
        destello_estrella(p, x, y, (36 + 50 * f) * I, (255, 255, 255), 1 - f / 0.45, rot=f * 3)
    # anillo
    rr = (18 + 78 * _ease(f)) * I
    if a * 7 * I > 1.2:
        pygame.draw.circle(p, aclarar(c, 0.55), (x, y), int(rr), max(1, int(7 * a * I)))
    seed = int(t * 20)
    n = int(7 + 3 * etapa)
    if tipo == "electrico":
        for i in range(n):
            ang = i * math.pi * 2 / n + _rnd(i, 1) * 0.5
            Lr = (30 + 60 * _ease(min(1, f * 1.6))) * I
            pts = _zigzag((x, y), (x + math.cos(ang) * Lr, y + math.sin(ang) * Lr), 4, 8 * I, seed + i)
            if a > 0.1:
                _rayo(p, pts, 1.6 * I * a + 0.5, halo=False)
        for i in range(5):
            _parte(p, "electrico", x + (_rnd(i, seed) - 0.5) * 120 * I * f, y + (_rnd(i, 2) - 0.5) * 100 * I * f, 3 + 3 * a, i + t * 4, a)
    elif tipo == "fuego":
        for i in range(n + 3):
            ang = i * math.pi * 2 / (n + 3) + _rnd(i, 3)
            d = (20 + 80 * _ease(f)) * I * (0.5 + _rnd(i, 4) * 0.6)
            px, py = x + math.cos(ang) * d, y + math.sin(ang) * d - f * 22
            col = _mix((255, 220, 100), (140, 40, 20), f)
            suave(p, px, py, (22 - 10 * f) * I * (0.6 + _rnd(i, 5)), col, int(230 * a))
            _parte(p, "fuego", px + math.cos(ang) * 14, py + math.sin(ang) * 14, 3 * I, 0, a)
    elif tipo == "hielo":
        for i in range(n):
            ang = i * math.pi * 2 / n + 0.2
            d = (16 + 80 * _ease(f)) * I
            _cristal(p, x + math.cos(ang) * d, y + math.sin(ang) * d, 9 * I, 24 * I * (0.6 + 0.4 * a), ang + math.pi / 2 + f * 2)
        for i in range(8):
            _parte(p, "hielo", x + math.cos(i * 0.8 + 1) * 70 * I * f, y + math.sin(i * 0.8 + 1) * 70 * I * f, 3, i + t * 3, a)
    elif tipo == "agua":
        for i in range(n + 3):
            ang = -math.pi * (0.1 + 0.8 * i / (n + 2))
            v = (110 + 70 * _rnd(i, 7)) * I
            tt = f * 1.0
            px = x + math.cos(ang) * v * tt * 0.9
            py = y + math.sin(ang) * v * tt + 260 * tt * tt * (0.6 + 0.4 * I / 1.6)
            if a > 0.05:
                _parte(p, "agua", px, py, (4 + 2 * I) * (0.6 + 0.4 * a), 0, 1)
        pygame.draw.ellipse(p, aclarar(c, 0.4 + 0.3 * f), (x - rr * 1.25, y + 10 - rr * 0.3, rr * 2.5, rr * 0.6), max(1, int(5 * a)))
    elif tipo == "viento":
        for k in range(3):
            r2 = (14 + (60 + 28 * k) * _ease(f)) * I
            ang0 = t * 5 + k * 2.1
            rect = pygame.Rect(x - r2, y - r2 * 0.7, r2 * 2, r2 * 1.4)
            pygame.draw.arc(p, _mix((10, 40, 36), (225, 255, 245), a), rect, ang0, ang0 + 2.4, max(1, int(5 * a)))
        for i in range(5):
            ang = i * 1.3 + t * 3
            _parte(p, "viento", x + math.cos(ang) * 60 * I * f, y + math.sin(ang) * 40 * I * f, 3 + I, ang, a)
    else:
        for i in range(n):
            ang = -math.pi * (0.05 + 0.9 * i / (n - 1)) if n > 1 else -1.5
            v = (90 + 80 * _rnd(i, 7)) * I
            px = x + math.cos(ang) * v * f
            py = y + math.sin(ang) * v * f + 230 * f * f
            _roca(p, px, py, (5 + 4 * _rnd(i, 2)) * I, f * 9 + i, i)
        for i in range(5):
            suave(p, x + (i - 2) * 26 * I * f, y + 14 - 10 * f, (16 + 26 * f) * I, (200, 175, 135), int(150 * a))


# =====================================================================
# CARGA
# =====================================================================
def dibujar_carga(p, tipo, etapa, cx, cy, f, t):
    if tipo not in COL:
        return
    I = _I(etapa)
    f = max(0.0, min(1.0, f))
    c = COL[tipo]
    R = (80 + 30 * etapa) * 1.0
    # anillo en el suelo
    rg = R * (0.6 + 0.5 * f)
    pygame.draw.ellipse(p, _mix((0, 0, 0), c, 0.25 + 0.5 * f), (cx - rg, cy + 55 - rg * 0.22, rg * 2, rg * 0.44), 3)
    n = int(9 + 4 * etapa)
    for i in range(n):
        ph = (t * (0.9 + 0.1 * (i % 3)) + i / n) % 1.0
        ang = i * 2.39996 + ph * 3.0 * (1 if i % 2 else -1)
        d = R * (1 - ph)
        px = cx + math.cos(ang) * d
        py = cy + math.sin(ang) * d * 0.8 - 8
        a = min(1.0, ph * 4) * (0.35 + 0.65 * f)
        _parte(p, tipo, px, py, (3 + 3 * I) * (0.5 + 0.5 * (1 - ph)), ang + t * 3, a, i)
    r0 = (10 + 52 * f) * I
    glow(p, cx, cy - 6, r0 * 2.3, c, int(40 + 150 * f))
    glow(p, cx, cy - 6, r0 * 1.0, aclarar(c, 0.6), int(60 + 195 * f * f))
    if f > 0.85:
        k = (f - 0.85) / 0.15
        glow(p, cx, cy - 6, r0 * 3.2, (255, 255, 255), int(120 * k))
        destello_estrella(p, cx, cy - 6, r0 * 2.2, aclarar(c, 0.6), k, t * 2)
    # chisporroteo del tipo
    if tipo == "electrico" and f > 0.2:
        seed = int(t * 18)
        for i in range(3):
            ang = _rnd(i, seed) * 6.28
            pts = _zigzag((cx, cy - 6), (cx + math.cos(ang) * R * 0.8 * f, cy - 6 + math.sin(ang) * R * 0.7 * f), 5, 8, seed * 3 + i)
            _rayo(p, pts, 1.2, halo=False)


# =====================================================================
# ATAQUE CARGADO
# =====================================================================
def _cargado_electrico(p, etapa, x0, y0, x1, y1, f, t):
    I = _I(etapa)
    n = (1, 2, 3, 5)[_E(etapa)]
    W, H = p.get_size()
    seed = int(t * 22)
    # oscurece el cielo antes del rayo y destello
    if f < 0.28:
        _oscurecer_pantalla(p, 85 * _ease(f / 0.28))
        for i in range(8):
            ang = _rnd(i, seed) * 6.28
            pts = _zigzag((x0, y0), (x0 + math.cos(ang) * 70 * I * f * 3, y0 + math.sin(ang) * 60 * I * f * 3), 5, 8, seed + i)
            _rayo(p, pts, 1.4, halo=False)
        glow(p, x0, y0, 60 * I * (0.5 + f * 3), (255, 235, 90), 210)
    elif f < 0.9:
        k = (f - 0.28) / 0.62
        _oscurecer_pantalla(p, 85 * (1 - k))
        flick = (int(t * 30) % 3) != 2 or k < 0.35
        if flick:
            for b in range(n):
                off = (b - (n - 1) / 2) * 70 * (0.7 + 0.3 * I)
                tx = x1 + off
                ty = y1 + abs(off) * 0.12
                pts = _zigzag((tx + (_rnd(b, seed) - 0.5) * 50, -30), (tx, ty), 12 + 4 * etapa, 34 * (0.8 + 0.4 * I), seed * 7 + b)
                _rayo(p, pts, 4.2 * I * (1 - 0.5 * k), halo=True)
                # ramificaciones
                for br in range(2 + etapa):
                    j = 3 + br * 3
                    if j < len(pts) - 1:
                        ex = pts[j][0] + (_rnd(br, seed + b) - 0.5) * 220 * I
                        ey = pts[j][1] + 80 + 70 * _rnd(br, b)
                        pr = _zigzag(pts[j], (ex, ey), 5, 14, seed + br * 5 + b)
                        _rayo(p, pr, 1.6 * I, halo=False)
            # rayo de lanzador a blanco, fino
            pts = _zigzag((x0, y0), (x1, y1), 12, 24, seed + 99)
            _rayo(p, pts, 1.8 * I, halo=True)
            glow(p, x1, y1, 120 * I, (255, 235, 100), 220)
            glow(p, x1, y1, 50 * I, (255, 255, 255), 255)
            for i in range(10 + 4 * etapa):
                ang = _rnd(i, seed) * 6.28
                d = (30 + 120 * _rnd(i, 3)) * I * k
                _parte(p, "electrico", x1 + math.cos(ang) * d, y1 + 14 + math.sin(ang) * d * 0.4 - 30 * k, 3 + 2 * I, ang, 1 - k * 0.7)
        # destello de pantalla al inicio del golpe
        _flash_pantalla(p, max(0.0, 0.8 - (f - 0.28) * 7) * (0.35 + 0.1 * etapa), (235, 235, 255))
    else:
        k = (f - 0.9) / 0.1
        for i in range(6):
            _parte(p, "electrico", x1 + (_rnd(i, 4) - 0.5) * 160 * I, y1 + (_rnd(i, 5) - 0.5) * 70, 3 * (1 - k) + 1, i + t * 5, 1 - k)


def _bola_fuego(p, x, y, r, t, dirx=1.0, diry=0.0):
    glow(p, x, y, r * 3.4, (255, 80, 20), 150)
    glow(p, x, y, r * 2.2, (255, 140, 30), 200)
    # lenguas de fuego hacia atras
    n = 9
    for i in range(n):
        ang = math.atan2(-diry, -dirx) + (i - (n - 1) / 2) * 0.30 + math.sin(t * 9 + i * 1.7) * 0.18
        L = r * (1.35 + 0.5 * _rnd(i, 2) + 0.2 * math.sin(t * 11 + i))
        base = [(math.cos(ang + math.pi / 2) * r * 0.55, math.sin(ang + math.pi / 2) * r * 0.55),
                (math.cos(ang) * L, math.sin(ang) * L),
                (math.cos(ang - math.pi / 2) * r * 0.55, math.sin(ang - math.pi / 2) * r * 0.55)]
        pygame.draw.polygon(p, (240, 80, 30), [(x + a, y + b) for a, b in base])
        inner = [(a * 0.6, b * 0.6) for a, b in base]
        pygame.draw.polygon(p, (255, 165, 50), [(x + a, y + b) for a, b in inner])
    suave(p, x, y, r * 1.08, (230, 70, 25), 255)
    suave(p, x, y, r * 0.88, (255, 140, 40), 255)
    suave(p, x, y, r * 0.6, (255, 215, 90), 255)
    glow(p, x, y, r * 0.85, (255, 255, 230), 255)


def _cargado_fuego(p, etapa, x0, y0, x1, y1, f, t):
    I = _I(etapa)
    Rm = (30, 44, 60, 80)[_E(etapa)]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    if f < 0.35:
        k = _ease(f / 0.35)
        r = 8 + (Rm - 8) * k
        _bola_fuego(p, x0 + ux * 50, y0 - 36 * k + uy * 50, r, t, ux, uy)
        for i in range(12):
            ph = (t * 1.3 + i / 12) % 1
            ang = i * 2.4
            d = (90 * (1 - ph)) * (0.4 + k)
            _parte(p, "fuego", x0 + ux * 50 + math.cos(ang) * d, y0 - 36 * k + uy * 50 + math.sin(ang) * d, 3 + 2 * I, 0, k * (1 - ph) * 1.4)
    elif f < 0.72:
        k = (f - 0.35) / 0.37
        e = _ease(k)
        sx, sy = x0 + ux * 50, y0 - 36 + uy * 50
        x = _lerp(sx, x1, e)
        y = _lerp(sy, y1, e) - math.sin(math.pi * e) * 50
        for j in range(18, 0, -1):
            ee = max(0.0, e - j * 0.014)
            px = _lerp(sx, x1, ee)
            py = _lerp(sy, y1, ee) - math.sin(math.pi * ee) * 50
            kk = 1 - j / 19
            suave(p, px + math.sin(t * 10 + j) * 4, py + math.cos(t * 9 + j) * 4, Rm * (0.3 + 0.7 * kk), _mix((200, 50, 20), (255, 170, 50), kk), int(190 * kk))
        _bola_fuego(p, x, y, Rm * (1 + 0.1 * math.sin(t * 20)), t, ux, uy)
    else:
        k = (f - 0.72) / 0.28
        Re = (110, 150, 200, 270)[_E(etapa)]
        if k < 0.35:
            _flash_pantalla(p, (1 - k / 0.35) * min(1.0, 0.5 + 0.18 * etapa), (255, 220, 160))
        e = _ease(k)
        glow(p, x1, y1, Re * (0.8 + 0.6 * e), (255, 110, 30), int(230 * (1 - k)))
        for i in range(int(16 + 8 * etapa)):
            ang = i * 2.39996
            dd = Re * (0.2 + 0.8 * _rnd(i, 3)) * e
            px, py = x1 + math.cos(ang) * dd, y1 + math.sin(ang) * dd * 0.8 - 30 * e
            col = _mix((255, 230, 120), (120, 30, 20), min(1.0, k * 1.2))
            suave(p, px, py, (26 + 22 * I) * (1 - 0.6 * k) * (0.6 + 0.6 * _rnd(i, 4)), col, int(235 * (1 - k * 0.9)))
        for ring in range(2):
            rr = Re * (0.3 + 0.9 * _ease(min(1.0, k * (1.1 + 0.3 * ring))))
            if k < 0.9:
                pygame.draw.circle(p, (255, 215, 130), (x1, y1), int(rr), max(1, int(10 * (1 - k))))
        for i in range(int(14 + 8 * etapa)):
            ang = _rnd(i, 8) * 6.28
            v = (160 + 140 * _rnd(i, 9)) * I
            px = x1 + math.cos(ang) * v * k * 0.9
            py = y1 + math.sin(ang) * v * k * 0.6 + 200 * k * k - 60 * k
            _parte(p, "fuego", px, py, 3 + 2 * I, 0, 1 - k)
        if etapa >= 2:
            destello_estrella(p, x1, y1, Re * 0.9 * (1 - k * 0.5), (255, 245, 210), 1 - k, k * 3)


def _cargado_hielo(p, etapa, x0, y0, x1, y1, f, t):
    I = _I(etapa)
    nC = (8, 12, 17, 24)[_E(etapa)]
    W, H = p.get_size()
    sx = 150 + 50 * etapa
    # tinte frio
    _flash_pantalla(p, 0.05 + 0.02 * etapa if 0.05 < f < 0.9 else 0.0, (30, 70, 120))
    # circulo de escarcha
    if f > 0.2:
        k = _ease((f - 0.2) / 0.5)
        rx = (90 + 50 * etapa) * k
        pygame.draw.ellipse(p, (205, 240, 255), (x1 - rx, y1 + 42 - rx * 0.25, rx * 2, rx * 0.5))
        pygame.draw.ellipse(p, (130, 200, 245), (x1 - rx, y1 + 42 - rx * 0.25, rx * 2, rx * 0.5), 3)
        for i in range(6):
            a = i * math.pi / 3
            pygame.draw.line(p, (255, 255, 255), (x1, y1 + 42), (x1 + math.cos(a) * rx * 0.9, y1 + 42 + math.sin(a) * rx * 0.22), 2)
    # cristales cayendo / clavados
    for i in range(nC):
        t0 = 0.04 + 0.5 * i / nC
        dur = 0.2
        xi = x1 + (_rnd(i, 1) - 0.5) * 2 * sx
        yl = y1 + 36 + (_rnd(i, 2) - 0.2) * 34
        size = (30 + 22 * _rnd(i, 3)) * (0.8 + 0.4 * I)
        if f < t0:
            continue
        k = (f - t0) / dur
        if k < 1:
            yi = _lerp(-60, yl - size * 0.35, k * k)
            glow(p, xi, yi - 30, size * 1.4, (130, 205, 255), 60)
            for j in range(1, 4):
                glow(p, xi, yi - j * 22, size * 0.5, (190, 235, 255), 55)
            _cristal(p, xi, yi, size * 0.42, size, math.pi + (_rnd(i, 4) - 0.5) * 0.3)
        else:
            gk = min(1.0, (f - t0 - dur) / 0.08)
            fade = 1.0 if f < 0.85 else max(0.0, 1 - (f - 0.85) / 0.15)
            hh = size * (0.55 + 0.45 * fade)
            if fade > 0.05:
                _cristal(p, xi, yl - hh * 0.5, size * 0.4 * (0.6 + 0.4 * fade), hh * 1.0, (_rnd(i, 4) - 0.5) * 0.5)
            if gk < 1:
                for j in range(6):
                    a = j * 1.05 + i
                    _parte(p, "hielo", xi + math.cos(a) * 30 * gk, yl - 10 - abs(math.sin(a)) * 40 * gk + 30 * gk * gk, 3, a, 1 - gk)
    # congelacion del blanco
    if f > 0.45:
        k = _ease((f - 0.45) / 0.3)
        fade = 1.0 if f < 0.9 else max(0.0, 1 - (f - 0.9) / 0.1)
        hw, hh = 62 + 14 * etapa, 100 + 24 * etapa
        pts = [(x1, y1 - hh * 0.6), (x1 + hw * 0.75, y1 - hh * 0.2), (x1 + hw * 0.65, y1 + 35), (x1 - hw * 0.65, y1 + 35), (x1 - hw * 0.75, y1 - hh * 0.2)]
        glow(p, x1, y1 - 20, hh * 0.9, (150, 215, 255), int(100 * k * fade))
        # contorno de bloque de hielo (translucido: solo lineas y destellos)
        if fade > 0.05:
            if k > 0.15:
                col = (225, 247, 255)
                gw = max(2, int(5 * k * fade))
                pygame.draw.polygon(p, (70, 130, 200), pts, gw + 3)
                pygame.draw.polygon(p, col, pts, gw)
                pygame.draw.lines(p, col, False, [pts[0], (x1, y1 - 10), pts[2]], 2)
                pygame.draw.lines(p, col, False, [pts[1], (x1, y1 - 10), pts[3]], 2)
            destello_estrella(p, x1 - hw * 0.3, y1 - hh * 0.35, 28 + 6 * etapa, (255, 255, 255), k * fade, t * 2)
            destello_estrella(p, x1 + hw * 0.35, y1 - hh * 0.05, 20 + 5 * etapa, (200, 240, 255), k * fade, -t * 2)
    for i in range(int(8 + 6 * etapa)):
        ph = (t * 0.6 + _rnd(i, 7)) % 1
        _parte(p, "hielo", x1 + (_rnd(i, 5) - 0.5) * sx * 2.2, y1 - ph * 200 + 40, 2.5 + I, i + t * 2, min(1, f * 4) * (1 - ph))


def _onda_geom(xf, base, H, Lw, s, t, ext):
    """Devuelve (cuerpo, arco_exterior, hueco) de una ola con labio rizado."""
    R = max(8.0, H * 0.5 * ext)
    yc = base - R * 1.12
    xc = -R * 0.35
    rel = []
    n = 14
    for i in range(n + 1):
        u = i / n
        sm = u * u * (3 - 2 * u)
        wob = math.sin(u * 7 - t * 6) * 1.5
        rel.append((-Lw + (xc - R + Lw) * u, base - (yc - (-R * 0.0) - 0) * 0 - (base - yc) * sm + wob))
    outer = []
    m = 18
    for i in range(m + 1):
        th = math.pi + (math.pi + 0.95) * i / m
        rr = R * (1 - 0.2 * i / m)
        outer.append((xc + math.cos(th) * rr, yc + math.sin(th) * rr))
    inner = []
    for i in range(m + 1):
        th = math.pi * 2 + 0.75 - (math.pi + 0.35) * i / m
        rr = R * 0.5 * (1 + 0.15 * i / m)
        inner.append((xc + R * 0.08 + math.cos(th) * rr, yc + R * 0.14 + math.sin(th) * rr))
    fin = [(xc + R * 0.05, base)]
    body = rel + outer[1:] + inner + fin + [(-Lw, base)]
    tr = lambda P: [(xf + s * x, y) for x, y in P]
    return tr(body), tr(outer), tr(inner)


def _cargado_agua(p, etapa, x0, y0, x1, y1, f, t):
    I = _I(etapa)
    Hm = (70, 110, 150, 205)[_E(etapa)]
    s = 1 if x1 >= x0 else -1
    base = y1 + 48
    Lw = Hm * 2.6
    if f < 0.72:
        k = f / 0.72
        e = _ease(k)
        ext = 0.3 + 0.7 * min(1.0, k * 2.0)
        xf = _lerp(x0 + s * 30, x1 + s * 20, e)
    else:
        k2 = (f - 0.72) / 0.28
        ext = max(0.0, 1 - k2 * 1.1)
        xf = x1 + s * 20 + s * 30 * k2
    poly, outer, inner = _onda_geom(xf, base, Hm, Lw, s, t, ext)
    pygame.draw.polygon(p, (28, 84, 180), [(x - s * 16, y + 7) for x, y in poly])
    pygame.draw.polygon(p, (52, 138, 245), poly)
    # franja clara bajo la cresta y tonos de profundidad
    n_r = 15
    pygame.draw.lines(p, (110, 192, 255), False, [(x, y + 10) for x, y in poly[:n_r]], 10)
    pygame.draw.lines(p, (140, 210, 255), False, outer, 9)
    pygame.draw.polygon(p, (22, 66, 150), poly, 4)
    # franjas de agua
    for k in range(3):
        yy = base - 10 - k * Hm * 0.16 * ext
        x_a = xf - s * Lw * (0.85 - 0.2 * k)
        x_b = xf - s * Lw * (0.35 - 0.05 * k)
        pygame.draw.line(p, (150, 215, 255), (x_a, yy), (x_b, yy), 3)
    # espuma en cresta y labio
    for i in range(0, len(outer), 2):
        x, y = outer[i]
        r = (4 + 5 * (i / len(outer))) * (0.7 + 0.5 * I) * (0.65 + 0.35 * math.sin(t * 8 + i))
        pygame.draw.circle(p, (242, 252, 255), (x, y + 1), max(2, r))
        pygame.draw.circle(p, (150, 200, 240), (x, y + 1), max(2, r), 1)
    for i in range(0, 14, 3):
        x, y = poly[i]
        pygame.draw.circle(p, (235, 250, 255), (x, y + 2), 3 + I)
    for i in range(int(5 + 4 * etapa)):
        ph = (t * 1.2 + _rnd(i, 3)) % 1
        px = xf - s * Lw * 0.2 * ph + s * 10
        py = base - Hm * ext * (0.6 + 0.6 * ph) - 10
        _parte(p, "agua", px + s * ph * 60, py + 40 * ph * ph * 3 - 30 * ph, 3 + I, 0, 1 - ph * 0.6)
    # salpicadura en el blanco
    if f > 0.62:
        k = (f - 0.62) / 0.38
        glow(p, x1, y1, 140 * I * (1 - k * 0.5), (110, 190, 255), int(150 * (1 - k)))
        for i in range(int(12 + 8 * etapa)):
            ang = -math.pi * (0.1 + 0.8 * _rnd(i, 1))
            v = (160 + 140 * _rnd(i, 2)) * (0.6 + 0.5 * I)
            px = x1 + math.cos(ang) * v * k
            py = y1 + 20 + math.sin(ang) * v * k + 330 * k * k
            _parte(p, "agua", px, py, (4 + 3 * I) * (1 - 0.5 * k), 0, 1)
        for ring in range(2):
            rr = (60 + 130 * I * 0.8) * _ease(min(1.0, k * (1.0 + 0.3 * ring)))
            pygame.draw.ellipse(p, _mix((20, 60, 130), (225, 245, 255), 1 - k), (x1 - rr, y1 + 40 - rr * 0.22, rr * 2, rr * 0.44), max(1, int(6 * (1 - k))))


def _cargado_viento(p, etapa, x0, y0, x1, y1, f, t):
    I = _I(etapa)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    ang = math.atan2(uy, ux)
    # cuchillas de aire
    nb = (3, 4, 6, 8)[_E(etapa)]
    for b in range(nb):
        t0 = 0.05 + 0.4 * b / nb
        k = (f - t0) / 0.42
        if k < 0 or k > 1.05:
            continue
        e = _ease(min(1.0, k))
        yoff = ((b % 4) - 1.5) * 34 * I
        x = _lerp(x0 + ux * 40, x1, e)
        y = _lerp(y0 + uy * 40, y1, e) + yoff * (1 - e * 0.6) - math.sin(math.pi * e) * 30
        Rm = (28 + 14 * etapa) * (0.8 + 0.4 * _rnd(b, 1))
        a_vis = 1.0 if k < 0.9 else max(0.0, 1 - (k - 0.9) / 0.15)
        for j in range(1, 7):
            glow(p, x - ux * j * 12, y - uy * j * 12, Rm * 0.5, (150, 235, 215), int(80 * (1 - j / 7) * a_vis))
        pts = []
        for i in range(15):
            a = ang - 1.1 + 2.2 * i / 14
            pts.append((x + math.cos(a) * Rm - ux * Rm * 0.6, y + math.sin(a) * Rm - uy * Rm * 0.6))
        for i in range(14, -1, -1):
            a = ang - 0.95 + 1.9 * i / 14
            pts.append((x + math.cos(a) * Rm * 0.72 - ux * Rm * 0.15, y + math.sin(a) * Rm * 0.72 - uy * Rm * 0.15))
        if a_vis > 0.05:
            pygame.draw.polygon(p, _mix((60, 120, 120), (230, 255, 248), a_vis), pts)
            pygame.draw.polygon(p, (60, 150, 145), pts, 2)
    # tornado en el blanco
    if f > 0.25:
        k = _ease(min(1.0, (f - 0.25) / 0.3))
        fade = 1.0 if f < 0.88 else max(0.0, 1 - (f - 0.88) / 0.12)
        Ht = (190, 250, 320, 410)[_E(etapa)] * k
        Rt = (44, 62, 84, 112)[_E(etapa)]
        xb, yb = x1, y1 + 44
        bw = int(Rt * 2.6)
        bh = int(Ht + 90)
        if bh > 20:
            surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            cxs, ybs = bw / 2, bh - 24
            nl = 22
            sway = math.sin(t * 3) * 6
            left, right = [], []
            for i in range(nl + 1):
                h = Ht * i / nl
                rr = 8 + (Rt - 8) * (i / nl) ** 1.25
                xc = cxs + sway * (i / nl)
                left.append((xc - rr, ybs - h))
                right.append((xc + rr, ybs - h))
            pygame.draw.polygon(surf, (170, 232, 224, int(150 * fade)), left + list(reversed(right)))
            for i in range(nl + 1):
                h = Ht * i / nl
                rr = 8 + (Rt - 8) * (i / nl) ** 1.25
                xc = cxs + sway * (i / nl)
                a0 = t * 7 * (1 + 0.4 * (i % 2)) + i * 0.9
                rect = pygame.Rect(xc - rr, ybs - h - rr * 0.16, rr * 2, rr * 0.32 + 4)
                col = (245, 255, 252, int(235 * fade)) if i % 2 == 0 else (150, 220, 205, int(215 * fade))
                pygame.draw.arc(surf, col, rect, a0, a0 + 3.3, 5)
            # contorno suave del embudo
            pygame.draw.lines(surf, (90, 170, 160, int(150 * fade)), False, left, 3)
            pygame.draw.lines(surf, (90, 170, 160, int(150 * fade)), False, right, 3)
            p.blit(surf, (xb - cxs, yb - ybs))
        glow(p, xb, yb, Rt * 1.5, (150, 235, 215), int(110 * fade * k))
        for i in range(int(8 + 5 * etapa)):
            ph = (t * 0.55 + i / (8 + 5 * etapa)) % 1
            h = Ht * ph
            rr = 8 + (Rt * 1.15 - 8) * ph ** 1.25
            a = t * 5.5 + i * 2.1
            px = xb + math.cos(a) * rr
            py = yb - h + math.sin(a) * rr * 0.16
            if math.sin(a) > -0.2 or True:
                if i % 3 == 0:
                    pygame.draw.polygon(p, (110, 190, 90), _rot([(-6, 0), (0, -4), (6, 0), (0, 4)], a, px, py))
                else:
                    pygame.draw.circle(p, (245, 255, 250), (px, py), 2 + I)


def _cargado_tierra(p, etapa, x0, y0, x1, y1, f, t):
    I = _I(etapa)
    s = 1 if x1 >= x0 else -1
    gy = y1 + 42
    # grieta en el suelo desde el lanzador hasta el blanco
    if f < 0.9:
        k = _ease(min(1.0, f / 0.3))
        pts = []
        xs, xe = x0 + s * 40, _lerp(x0 + s * 40, x1, k)
        n = 14
        for i in range(n + 1):
            xx = _lerp(xs, xe, i / n)
            pts.append((xx, gy + 6 + (_rnd(i, 1) - 0.5) * 12))
        if len(pts) > 1:
            pygame.draw.lines(p, (50, 32, 24), False, pts, 6)
            pygame.draw.lines(p, (255, 170, 80), False, pts, 2)
    # columnas de roca que emergen
    nS = (3, 5, 7, 9)[_E(etapa)]
    for i in range(nS):
        t0 = 0.1 + 0.4 * i / nS
        k = (f - t0) / 0.2
        if k < 0:
            continue
        fade = 1.0 if f < 0.84 else max(0.0, 1 - (f - 0.84) / 0.16)
        e = 1 - (1 - min(1.0, k)) ** 3
        xi = _lerp(x0 + s * 80, x1 - s * 20, (i + 0.5) / nS) + (_rnd(i, 2) - 0.5) * 24
        yi = gy + (i % 2) * 8
        hh = (46 + 36 * _rnd(i, 3) + 14 * etapa * (i / nS + 0.3)) * e * fade
        ww = (30 + 14 * etapa) * (0.8 + 0.5 * _rnd(i, 4))
        if hh > 4:
            col = (150, 108, 66)
            pts = [(xi - ww * 0.6, yi), (xi - ww * 0.5, yi - hh * 0.55), (xi - ww * 0.18, yi - hh), (xi + ww * 0.25, yi - hh * 0.8), (xi + ww * 0.55, yi - hh * 0.45), (xi + ww * 0.6, yi)]
            pygame.draw.polygon(p, oscurecer(col, 0.2), pts)
            pygame.draw.polygon(p, aclarar(col, 0.22), [pts[0], pts[1], pts[2], (xi, yi - hh * 0.4), (xi - ww * 0.15, yi)])
            pygame.draw.polygon(p, oscurecer(col, 0.42), [pts[3], pts[4], pts[5], (xi + ww * 0.1, yi)])
            for q in (0.3, 0.6):
                pygame.draw.line(p, oscurecer(col, 0.45), (xi - ww * (0.55 - 0.3 * q), yi - hh * q), (xi + ww * (0.5 - 0.3 * q), yi - hh * q + 4), 2)
            pygame.draw.polygon(p, CONTORNO, pts, 3)
            if k < 1:
                for j in range(3):
                    suave(p, xi + (j - 1) * ww * 0.6, yi, ww * 0.5 * (0.5 + k), (200, 175, 135), int(150 * (1 - k)))
    # roca lanzada
    if 0.38 < f < 0.8:
        k = (f - 0.38) / 0.42
        e = _ease(k)
        sx, sy = x0 + s * 30, y0 - 20
        x = _lerp(sx, x1, e)
        y = _lerp(sy, y1, e) - math.sin(math.pi * e) * (130 + 40 * etapa)
        r = (22, 30, 40, 54)[_E(etapa)]
        for j in range(8, 0, -1):
            ee = max(0.0, e - j * 0.03)
            px = _lerp(sx, x1, ee)
            py = _lerp(sy, y1, ee) - math.sin(math.pi * ee) * (130 + 40 * etapa)
            suave(p, px, py, r * (0.3 + 0.4 * (1 - j / 9)), (190, 160, 115), int(130 * (1 - j / 9)))
        _roca(p, x, y, r, t * 7, 5)
        if etapa >= 2:
            _roca(p, x - s * 55, y + 30, r * 0.55, t * 9, 8)
            _roca(p, x - s * 85, y + 10, r * 0.4, t * 11, 9)
    # impacto de la roca
    if f > 0.78:
        k = (f - 0.78) / 0.22
        if k < 0.3:
            _flash_pantalla(p, (1 - k / 0.3) * (0.25 + 0.1 * etapa), (255, 225, 170))
        rr = (50 + 120 * I) * _ease(k)
        pygame.draw.ellipse(p, _mix((60, 40, 30), (205, 180, 140), 1 - k), (x1 - rr, gy - rr * 0.2, rr * 2, rr * 0.4), max(1, int(8 * (1 - k))))
        for i in range(int(8 + 3 * etapa)):
            ang = -math.pi * (0.05 + 0.9 * _rnd(i, 3))
            v = (120 + 120 * _rnd(i, 4)) * I
            px = x1 + math.cos(ang) * v * k
            py = gy + math.sin(ang) * v * k + 320 * k * k
            _roca(p, px, py, (6 + 5 * _rnd(i, 5)) * I, k * 8 + i, i)
        for i in range(6):
            suave(p, x1 + (i - 2.5) * 34 * I * k, gy - 20 * k, (22 + 30 * k) * I, (200, 175, 135), int(160 * (1 - k)))


_CARGADOS = {"electrico": _cargado_electrico, "fuego": _cargado_fuego, "hielo": _cargado_hielo,
             "agua": _cargado_agua, "viento": _cargado_viento, "tierra": _cargado_tierra}


def dibujar_ataque_cargado(p, tipo, etapa, x0, y0, x1, y1, f, t):
    """Ataque grande del elemento; la sacudida de pantalla la hace la escena (usa f para decidir)."""
    fn = _CARGADOS.get(tipo)
    if fn is None:
        return
    fn(p, _E(etapa), x0, y0, x1, y1, max(0.0, min(1.0, f)), t)


# =====================================================================
# GUIAS DE GESTO
# =====================================================================
CERRADAS = {"fuego": True, "hielo": True, "viento": True, "tierra": True, "electrico": False, "agua": False}
_NUM = {"electrico": 16, "fuego": 16, "hielo": 16, "agua": 18, "viento": 20, "tierra": 15}


def _forma_unitaria(tipo):
    """Polilinea densa en coordenadas unitarias (0..1), un 'cerrar' implicito si es cerrada."""
    if tipo == "electrico":
        return [(0.5, 0.0), (0.16, 0.2), (0.84, 0.4), (0.16, 0.6), (0.84, 0.8), (0.5, 1.0)], False
    if tipo == "fuego":
        pts = [(0.5 + 0.5 * math.cos(-math.pi / 2 + 2 * math.pi * i / 120), 0.5 + 0.5 * math.sin(-math.pi / 2 + 2 * math.pi * i / 120)) for i in range(121)]
        return pts, True
    if tipo == "hielo":
        return [(0.5, 0.0), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5), (0.5, 0.0)], True
    if tipo == "agua":
        return [(i / 120, 0.5 + 0.36 * math.sin(2 * math.pi * 2 * i / 120)) for i in range(121)], False
    if tipo == "viento":
        pts = []
        for i in range(161):
            a = 2 * math.pi * i / 160
            d = 1 + math.sin(a) ** 2
            pts.append((0.5 + 0.5 * math.cos(a) / d * 1.0, 0.5 - 0.5 * (math.sin(a) * math.cos(a) / d) / 0.3536 * 0.62))
        return pts, True
    if tipo == "tierra":
        return [(0.0, 1.0), (0.5, 0.0), (1.0, 1.0), (0.0, 1.0)], True
    raise KeyError(tipo)


def _resample(pts, n, cerrada):
    acum = [0.0]
    for i in range(1, len(pts)):
        acum.append(acum[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    total = acum[-1]
    out = []
    cuenta = n if cerrada else n
    for k in range(cuenta):
        d = total * k / (n if cerrada else (n - 1))
        j = 1
        while j < len(acum) - 1 and acum[j] < d:
            j += 1
        seg = acum[j] - acum[j - 1] or 1.0
        u = (d - acum[j - 1]) / seg
        out.append((pts[j - 1][0] + (pts[j][0] - pts[j - 1][0]) * u, pts[j - 1][1] + (pts[j][1] - pts[j - 1][1]) * u))
    return out


def _mapear(pts, rect, tipo):
    rect = pygame.Rect(rect)
    pad = 0.08
    w, h = rect.w * (1 - 2 * pad), rect.h * (1 - 2 * pad)
    ox, oy = rect.x + rect.w * pad, rect.y + rect.h * pad
    if tipo == "fuego":
        d = min(w, h)
        ox += (w - d) / 2
        oy += (h - d) / 2
        w = h = d
    return [(ox + x * w, oy + y * h) for x, y in pts]


_cache_trazo = {}


def trazo_guia(tipo, rect, n=240):
    """Polilinea densa de la guia (para dibujar)."""
    key = (tipo, tuple(pygame.Rect(rect)), n)
    r = _cache_trazo.get(key)
    if r is None:
        u, cerr = _forma_unitaria(tipo)
        dens = _resample(u, n, cerr)
        if cerr:
            dens.append(dens[0])
        r = _mapear(dens, rect, tipo)
        if len(_cache_trazo) > 60:
            _cache_trazo.clear()
        _cache_trazo[key] = r
    return r


def puntos_guia(tipo, rect):
    """Puntos de control ordenados (~uniformes) de UNA vuelta del gesto."""
    u, cerr = _forma_unitaria(tipo)
    return _mapear(_resample(u, _NUM[tipo], cerr), rect, tipo)


def dibujar_guia(p, tipo, rect, progreso=None, t=0.0, ancho=10):
    if tipo not in COL:
        return
    rect = pygame.Rect(rect)
    col = COL[tipo]
    dens = trazo_guia(tipo, rect)
    ctrl = puntos_guia(tipo, rect)
    m = 40
    surf = pygame.Surface((rect.w + 2 * m, rect.h + 2 * m), pygame.SRCALPHA)
    ox, oy = rect.x - m, rect.y - m
    D = [(x - ox, y - oy) for x, y in dens]
    C = [(x - ox, y - oy) for x, y in ctrl]
    ancho = max(3, int(ancho))

    def trazo(pts, w, color):
        if len(pts) < 2:
            return
        pygame.draw.lines(surf, color, False, pts, w)
        for q in pts[::2] + [pts[-1]]:
            pygame.draw.circle(surf, color, (int(q[0]), int(q[1])), w // 2)

    trazo(D, ancho + 12, col + (34,))
    trazo(D, ancho, aclarar(col, 0.25) + (92,))
    trazo(D, max(2, ancho // 4), (255, 255, 255, 120))
    prog = None if progreso is None else max(0.0, min(1.0, progreso))
    if prog is not None and prog > 0:
        nn = max(2, int(len(D) * prog))
        Dp = D[:nn]
        trazo(Dp, ancho + 14, col + (95,))
        trazo(Dp, ancho + 2, aclarar(col, 0.35) + (255,))
        trazo(Dp, max(2, ancho // 3), (255, 255, 255, 255))
    # puntos de control
    for i, c in enumerate(C):
        vis = prog is not None and (i + 0.5) / len(C) <= prog + 1e-6
        r = ancho * (0.55 if vis else 0.38)
        pygame.draw.circle(surf, (255, 255, 255, 235 if vis else 120), (int(c[0]), int(c[1])), int(r) + 2)
        pygame.draw.circle(surf, (aclarar(col, 0.2) if vis else col) + (255 if vis else 140,), (int(c[0]), int(c[1])), int(r))
    # flechas de sentido
    for fr in (0.14, 0.38, 0.62, 0.86):
        i = int(fr * (len(D) - 1))
        a, b = D[max(0, i - 3)], D[min(len(D) - 1, i + 3)]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        hecho = prog is not None and fr <= prog
        s = ancho * 1.25
        tri = [(D[i][0] + math.cos(ang) * s, D[i][1] + math.sin(ang) * s),
               (D[i][0] + math.cos(ang + 2.5) * s, D[i][1] + math.sin(ang + 2.5) * s),
               (D[i][0] + math.cos(ang - 2.5) * s, D[i][1] + math.sin(ang - 2.5) * s)]
        pygame.draw.polygon(surf, (255, 255, 255, 255 if hecho else 190), tri)
        pygame.draw.polygon(surf, oscurecer(col, 0.45) + (255,), tri, 2)
    # punto de partida
    s0 = D[0]
    pul = 1 + 0.15 * math.sin(t * 5)
    pygame.draw.circle(surf, (255, 255, 255, 230), (int(s0[0]), int(s0[1])), int(ancho * 1.25 * pul), 3)
    p.blit(surf, (ox, oy))
    # luz viajera que muestra el sentido
    fr = (t * 0.32) % 1.0 if (prog is None or prog < 1) else 1.0
    if prog is None or prog <= 0.0:
        i = int(fr * (len(dens) - 1))
        glow(p, dens[i][0], dens[i][1], ancho * 2.6, aclarar(col, 0.4), 230)
        glow(p, dens[i][0], dens[i][1], ancho * 1.0, (255, 255, 255), 255)
    elif prog < 1:
        i = max(0, min(len(dens) - 1, int(prog * (len(dens) - 1))))
        glow(p, dens[i][0], dens[i][1], ancho * 3.0, aclarar(col, 0.4), 240)
        glow(p, dens[i][0], dens[i][1], ancho * 1.1, (255, 255, 255), 255)


# =====================================================================
# EVOLUCION
# =====================================================================
def dibujar_aura_evolucion(p, cx, cy, f, t):
    f = max(0.0, min(1.0, f))
    # columna de luz
    glow(p, cx, cy - 20, 210 * (0.5 + 0.5 * math.sin(min(1, f * 1.2) * math.pi)) + 40, (255, 235, 170), int(150 * min(1, f * 3)))
    for k in range(3):
        rr = (30 + 190 * ((f * 1.3 + k / 3.0) % 1.0))
        a = 1 - ((f * 1.3 + k / 3.0) % 1.0)
        pygame.draw.ellipse(p, _mix((0, 0, 0), (255, 240, 190), a * 0.9), (cx - rr, cy + 48 - rr * 0.22, rr * 2, rr * 0.44), max(1, int(5 * a)))
    n = 34
    cols = [(255, 255, 255), (255, 225, 120), (255, 170, 220), (150, 225, 255)]
    for i in range(n):
        ph = (f * 1.6 + i / n) % 1.0
        ang = i * 0.55 + ph * 9
        rr = 130 * (1 - ph) ** 0.8 + 18
        px = cx + math.cos(ang) * rr
        py = cy + 40 - ph * 170 + math.sin(ang) * rr * 0.25
        a = min(1.0, ph * 5) * (1 - ph * 0.5)
        glow(p, px, py, 10 + 8 * (1 - ph), cols[i % 4], int(235 * a))
        glow(p, px, py, 4, (255, 255, 255), int(255 * a))
    for i in range(4):
        destello_estrella(p, cx + math.cos(t * 1.7 + i * 1.6) * 80, cy - 20 + math.sin(t * 1.3 + i * 1.6) * 90, 18 + 8 * math.sin(t * 4 + i), (255, 245, 200), 0.7, t * 2 + i)
    if f > 0.8:
        k = (f - 0.8) / 0.2
        _flash_pantalla(p, math.sin(k * math.pi) * 0.75, (255, 245, 215))
        destello_estrella(p, cx, cy - 20, 300 * math.sin(k * math.pi), (255, 250, 230), 1.0, t * 3)
