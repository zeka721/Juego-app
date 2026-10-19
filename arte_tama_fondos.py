"""Fondos de Tamagotchi: hogar (dia/noche) y arenas por tipo. Capa estatica en cache + capa dinamica ligera."""

import math

import pygame

try:
    from ajustes import ANCHO, ALTO
except Exception:  # pragma: no cover
    ANCHO, ALTO = 1280, 720

from arte_tama_base import CONTORNO
from arte_tama_fx import glow, suave, _rnd, _mix, _flash_pantalla
from nucleo import aclarar, oscurecer

_CACHE = {}


def _grad(s, rect, c0, c1, c_mid=None):
    r = pygame.Rect(rect)
    for i in range(r.h):
        f = i / max(1, r.h - 1)
        if c_mid is not None:
            col = _mix(c0, c_mid, f * 2) if f < 0.5 else _mix(c_mid, c1, (f - 0.5) * 2)
        else:
            col = _mix(c0, c1, f)
        pygame.draw.line(s, col, (r.x, r.y + i), (r.right - 1, r.y + i))


def _nube(s, x, y, sc, col=(255, 255, 255), sombra=None):
    sombra = sombra or oscurecer(col, 0.12)
    bolas = [(-1.5, 0.3, 0.7), (-0.7, -0.2, 0.95), (0.3, -0.4, 1.1), (1.2, -0.05, 0.9), (1.9, 0.3, 0.65), (0.2, 0.3, 0.9), (-0.6, 0.4, 0.7), (0.9, 0.4, 0.75)]
    for bx, by, br in bolas:
        pygame.draw.circle(s, sombra, (x + bx * sc * 30, y + by * sc * 30 + sc * 6), br * sc * 30)
    for bx, by, br in bolas:
        pygame.draw.circle(s, col, (x + bx * sc * 30, y + by * sc * 30), br * sc * 30)


_NUBES = {}


def _sprite_nube(sc, col, sombra=None, extra=0):
    key = (round(sc, 2), col, sombra, extra)
    r = _NUBES.get(key)
    if r is None:
        w, h = int(sc * 30 * 4.8), int(sc * 30 * 2.6)
        r = pygame.Surface((w, h), pygame.SRCALPHA)
        _nube(r, w * 0.38, h * 0.55, sc, col, sombra)
        _NUBES[key] = r
    return r


def _conv(s):
    try:
        return s.convert()
    except pygame.error:
        return s


def _montanas(s, y_base, alt, col, n, seed, nieve=None, ancho=ANCHO, pico=0.5):
    pts = [(-20, y_base)]
    x = -20
    k = 0
    while x < ancho + 80:
        w = 150 + 150 * _rnd(k, seed)
        h = alt * (0.45 + 0.55 * _rnd(k, seed + 3))
        pts.append((x + w * pico, y_base - h))
        x += w
        pts.append((x, y_base - h * 0.25 * _rnd(k, seed + 7)))
        k += 1
    pts.append((ancho + 40, y_base))
    pygame.draw.polygon(s, col, pts)
    if nieve:
        for i in range(1, len(pts) - 1, 2):
            px, py = pts[i]
            h = y_base - py
            if h > alt * 0.35:
                cap = [(px, py), (px + 36 * h / alt + 12, py + h * 0.28), (px + 14, py + h * 0.2), (px, py + h * 0.33), (px - 16, py + h * 0.22), (px - 36 * h / alt - 12, py + h * 0.28)]
                pygame.draw.polygon(s, nieve, cap)


# =====================================================================
#  HOGAR
# =====================================================================
def _hogar_estatico(noche):
    W, H = ANCHO, ALTO
    s = pygame.Surface((W, H))
    pared0, pared1 = ((255, 232, 196), (255, 214, 176))
    suelo0, suelo1 = ((214, 160, 100), (176, 120, 74))
    hy = 478
    _grad(s, (0, 0, W, hy), pared0, pared1)
    # papel pintado: franjas suaves y estrellitas
    for i in range(0, W, 80):
        pygame.draw.rect(s, _mix(pared0, (255, 245, 225), 0.5), (i, 0, 40, hy))
    for gy in range(40, hy - 30, 70):
        for gx in range(30 + (gy // 70 % 2) * 40, W, 80):
            if 120 < gx < 470 and 60 < gy < 330:
                continue
            pygame.draw.circle(s, _mix(pared1, (255, 190, 170), 0.55), (gx, gy), 5)
            pygame.draw.circle(s, _mix(pared1, (255, 190, 170), 0.55), (gx + 18, gy + 4), 3)
    # guirnalda de banderines
    pts = [(x, 28 + 26 * math.sin(math.pi * (x / W) * 2) ** 2 * 0 + 22 * math.sin(math.pi * x / W)) for x in range(0, W + 1, 8)]
    pygame.draw.lines(s, (150, 110, 80), False, pts, 3)
    cols = [(255, 120, 130), (255, 205, 90), (120, 205, 150), (110, 170, 245), (190, 140, 235)]
    for i, x in enumerate(range(60, W, 100)):
        y = 28 + 22 * math.sin(math.pi * x / W)
        pygame.draw.polygon(s, cols[i % 5], [(x - 17, y + 1), (x + 17, y + 1), (x, y + 38)])
        pygame.draw.polygon(s, oscurecer(cols[i % 5], 0.4), [(x - 17, y + 1), (x + 17, y + 1), (x, y + 38)], 2)
    # ventana
    wx, wy, ww, wh = 140, 96, 310, 250
    marco = (176, 120, 80)
    pygame.draw.rect(s, oscurecer(marco, 0.3), (wx - 18, wy - 18, ww + 36, wh + 36), border_radius=14)
    pygame.draw.rect(s, marco, (wx - 14, wy - 14, ww + 28, wh + 28), border_radius=12)
    cielo = pygame.Surface((ww, wh))
    if noche:
        _grad(cielo, (0, 0, ww, wh), (14, 18, 62), (58, 52, 120))
    else:
        _grad(cielo, (0, 0, ww, wh), (120, 200, 255), (215, 240, 255))
    # paisaje de jardin
    if noche:
        pygame.draw.ellipse(cielo, (24, 56, 70), (-80, wh - 90, 280, 160))
        pygame.draw.ellipse(cielo, (20, 48, 62), (120, wh - 70, 340, 160))
        pygame.draw.rect(cielo, (46, 34, 40), (214, wh - 120, 12, 70))
        for cx, cy, r in [(220, wh - 138, 36), (194, wh - 118, 28), (244, wh - 116, 28)]:
            pygame.draw.circle(cielo, (22, 66, 62), (cx, cy), r)
    else:
        pygame.draw.ellipse(cielo, (140, 210, 120), (-80, wh - 90, 280, 160))
        pygame.draw.ellipse(cielo, (110, 190, 100), (120, wh - 70, 340, 160))
        pygame.draw.rect(cielo, (140, 96, 64), (214, wh - 120, 12, 70))
        for cx, cy, r in [(220, wh - 138, 36), (194, wh - 118, 28), (244, wh - 116, 28)]:
            pygame.draw.circle(cielo, (86, 170, 90), (cx, cy), r)
        for cx, cy in [(212, wh - 150), (232, wh - 128), (196, wh - 118)]:
            pygame.draw.circle(cielo, (255, 100, 100), (cx, cy), 6)
        pygame.draw.circle(cielo, (255, 238, 140), (ww - 62, 60), 30)
        pygame.draw.circle(cielo, (255, 250, 200), (ww - 62, 60), 22)
    s.blit(cielo, (wx, wy))
    # cruces y alfeizar
    pygame.draw.rect(s, marco, (wx + ww // 2 - 6, wy, 12, wh))
    pygame.draw.rect(s, marco, (wx, wy + wh // 2 - 6, ww, 12))
    pygame.draw.rect(s, oscurecer(marco, 0.3), (wx - 14, wy - 14, ww + 28, wh + 28), 3, border_radius=12)
    pygame.draw.rect(s, aclarar(marco, 0.2), (wx - 28, wy + wh + 10, ww + 56, 20), border_radius=7)
    pygame.draw.rect(s, oscurecer(marco, 0.3), (wx - 28, wy + wh + 10, ww + 56, 20), 3, border_radius=7)
    # cortinas
    cc = (240, 130, 150) if not noche else (200, 100, 130)
    for sx in (-1, 1):
        x0 = wx - 30 if sx < 0 else wx + ww + 30
        P = [(x0, wy - 26), (x0 + sx * 56, wy - 26), (x0 + sx * 40, wy + wh * 0.55), (x0 + sx * 70, wy + wh + 14), (x0, wy + wh + 14)]
        pygame.draw.polygon(s, cc, P)
        for k in range(1, 4):
            pygame.draw.line(s, oscurecer(cc, 0.18), (x0 + sx * k * 14, wy - 24), (x0 + sx * (k * 14 + 8), wy + wh + 10), 3)
        pygame.draw.polygon(s, oscurecer(cc, 0.4), P, 3)
    pygame.draw.rect(s, (150, 100, 70), (wx - 70, wy - 38, ww + 140, 12), border_radius=6)
    for sx in (wx - 74, wx + ww + 62):
        pygame.draw.circle(s, (200, 140, 90), (sx + 8, wy - 32), 11)
    # estante a la derecha
    sx0, sy0 = 820, 210
    pygame.draw.rect(s, (160, 108, 70), (sx0, sy0 + 78, 360, 16), border_radius=5)
    pygame.draw.rect(s, (160, 108, 70), (sx0 + 20, sy0 + 190, 320, 16), border_radius=5)
    for (bx, bw, bh, c) in [(30, 24, 70, (230, 90, 100)), (56, 20, 62, (100, 170, 240)), (78, 26, 74, (250, 200, 80)), (106, 18, 58, (120, 200, 140))]:
        pygame.draw.rect(s, c, (sx0 + bx, sy0 + 78 - bh, bw, bh), border_radius=4)
        pygame.draw.rect(s, oscurecer(c, 0.4), (sx0 + bx, sy0 + 78 - bh, bw, bh), 2, border_radius=4)
    # planta
    pygame.draw.polygon(s, (214, 120, 90), [(sx0 + 250, sy0 + 78), (sx0 + 310, sy0 + 78), (sx0 + 300, sy0 + 34), (sx0 + 260, sy0 + 34)])
    for ang, L in [(-60, 56), (-20, 66), (20, 62), (60, 54), (-90, 70)]:
        a = math.radians(ang - 90)
        pygame.draw.ellipse(s, (96, 190, 100), (sx0 + 280 + math.cos(a) * L * 0.5 - 10, sy0 + 36 + math.sin(a) * L * 0.5 - 22, 20, 44))
    # cuadro en la pared
    pygame.draw.rect(s, (160, 108, 70), (sx0 + 36, sy0 - 80, 110, 84), border_radius=6)
    pygame.draw.rect(s, (255, 244, 220), (sx0 + 46, sy0 - 70, 90, 64))
    pygame.draw.circle(s, (255, 205, 90), (sx0 + 112, sy0 - 50), 11)
    pygame.draw.polygon(s, (110, 190, 120), [(sx0 + 46, sy0 - 6), (sx0 + 78, sy0 - 40), (sx0 + 100, sy0 - 20), (sx0 + 114, sy0 - 28), (sx0 + 136, sy0 - 6)])
    # reloj
    pygame.draw.circle(s, (160, 108, 70), (sx0 + 240, sy0 - 40), 40)
    pygame.draw.circle(s, (255, 248, 230), (sx0 + 240, sy0 - 40), 32)
    pygame.draw.line(s, CONTORNO, (sx0 + 240, sy0 - 40), (sx0 + 240, sy0 - 62), 3)
    pygame.draw.line(s, CONTORNO, (sx0 + 240, sy0 - 40), (sx0 + 256, sy0 - 34), 3)
    # zocalo y suelo
    pygame.draw.rect(s, (255, 248, 235), (0, hy - 8, W, 22))
    pygame.draw.line(s, (214, 190, 160), (0, hy + 14), (W, hy + 14), 3)
    _grad(s, (0, hy + 15, W, H - hy - 15), suelo0, suelo1)
    # tablas con perspectiva
    for k in range(0, 9):
        yy = hy + 15 + int((k / 9) ** 1.5 * (H - hy))
        pygame.draw.line(s, oscurecer(suelo0, 0.25), (0, yy), (W, yy), 2)
    for k in range(-12, 13):
        x_top = W / 2 + k * 120
        x_bot = W / 2 + k * 190
        pygame.draw.line(s, oscurecer(suelo0, 0.18), (x_top, hy + 15), (x_bot, H), 1)
    # alfombra
    cx, cy = 640, 612
    for (rx, ry, c) in [(430, 96, (150, 90, 110)), (410, 88, (238, 130, 150)), (360, 76, (255, 220, 160)), (330, 68, (130, 200, 220)), (270, 54, (255, 238, 200))]:
        pygame.draw.ellipse(s, c, (cx - rx, cy - ry, rx * 2, ry * 2))
    for i in range(28):
        a = i * math.pi * 2 / 28
        pygame.draw.circle(s, (255, 244, 220), (cx + math.cos(a) * 385, cy + math.sin(a) * 82), 5)
    # cesto de juguetes y maceta
    pygame.draw.polygon(s, (204, 140, 90), [(1090, 540), (1210, 540), (1196, 640), (1104, 640)])
    for yy in (562, 590, 616):
        pygame.draw.line(s, (166, 108, 66), (1096, yy), (1204, yy), 3)
    pygame.draw.rect(s, (230, 90, 100), (1110, 508, 38, 38), border_radius=6)
    pygame.draw.rect(s, (110, 170, 240), (1146, 518, 36, 30), border_radius=6)
    pygame.draw.circle(s, (250, 205, 80), (1180, 520), 20)
    pygame.draw.circle(s, oscurecer((250, 205, 80), 0.4), (1180, 520), 20, 3)
    pygame.draw.polygon(s, (214, 120, 90), [(60, 600), (130, 600), (120, 668), (70, 668)])
    for ang, L in [(-50, 84), (-15, 100), (20, 92), (55, 80), (-85, 108)]:
        a = math.radians(ang - 90)
        pygame.draw.ellipse(s, (96, 190, 100), (95 + math.cos(a) * L * 0.5 - 14, 596 + math.sin(a) * L * 0.5 - 30, 28, 60))
    # lampara de pie
    pygame.draw.rect(s, (130, 96, 70), (1236, 330, 8, 250))
    pygame.draw.ellipse(s, (130, 96, 70), (1210, 572, 60, 18))
    pygame.draw.polygon(s, (255, 210, 120), [(1214, 330), (1266, 330), (1252, 276), (1228, 276)])
    pygame.draw.polygon(s, oscurecer((255, 210, 120), 0.4), [(1214, 330), (1266, 330), (1252, 276), (1228, 276)], 3)
    s = _conv(s)
    if noche:
        # oscurece toda la habitacion con azul (luz calida se anade dinamicamente)
        s.fill((118, 122, 190), special_flags=pygame.BLEND_MULT)
        # vuelve a pintar el cielo de la ventana sin oscurecer demasiado
        # pared bajo la luz de la lampara
    return s


def _estrellas_ventana(p, t, noche, wx=140, wy=96, ww=310, wh=250):
    clip = p.get_clip()
    p.set_clip(pygame.Rect(wx, wy, ww, wh))
    if noche:
        for i in range(26):
            x = wx + 14 + _rnd(i, 1) * (ww - 28)
            y = wy + 10 + _rnd(i, 2) * (wh * 0.62)
            a = 0.35 + 0.65 * (math.sin(t * (1.2 + _rnd(i, 3) * 2) + i) * 0.5 + 0.5)
            r = 1.6 + 2.2 * _rnd(i, 4)
            glow(p, x, y, r * 3.4, (255, 245, 200), int(150 * a))
            pygame.draw.circle(p, (255, 255, 255), (x, y), max(1, int(r * 0.8)))
        # luna
        mx, my = wx + ww - 80, wy + 70
        glow(p, mx, my, 90, (170, 190, 255), 150)
        pygame.draw.circle(p, (255, 248, 215), (mx, my), 32)
        pygame.draw.circle(p, (80, 70, 110), (mx + 15, my - 8), 26)  # se sobrepone para hacer creciente
        pygame.draw.circle(p, (255, 248, 215), (mx - 2, my + 2), 29, 0)
        pygame.draw.circle(p, (58, 52, 120), (mx + 14, my - 6), 26)
    else:
        for i, (y, sc, v, col) in enumerate([(wy + 40, 0.9, 12, (255, 255, 255)), (wy + 100, 0.7, 8, (250, 252, 255)), (wy + 140, 1.1, 5, (255, 255, 255))]):
            x = wx + ((t * v + i * 140) % (ww + 200)) - 100
            spr = _sprite_nube(sc, col, (205, 225, 245))
            p.blit(spr, (x - spr.get_width() / 2, y - spr.get_height() / 2))
    p.set_clip(clip)


_motas = 22


def dibujar_fondo_hogar(p, t, noche=False):
    key = ("hogar", bool(noche))
    s = _CACHE.get(key)
    if s is None:
        s = _hogar_estatico(noche)
        _CACHE[key] = s
    p.blit(s, (0, 0))
    _estrellas_ventana(p, t, noche)
    # ventana: marco/cruz se repinta sobre el cielo dinamico (barras finas)
    wx, wy, ww, wh = 140, 96, 310, 250
    marco = (176, 120, 80)
    if noche:
        marco = _mix(marco, (60, 60, 90), 0.55)
    pygame.draw.rect(p, marco, (wx + ww // 2 - 6, wy, 12, wh))
    pygame.draw.rect(p, marco, (wx, wy + wh // 2 - 6, ww, 12))
    if noche:
        # luz de la lampara (parpadeo muy suave) y luz de luna en el suelo
        fl = 0.92 + 0.08 * math.sin(t * 2.3) + 0.03 * math.sin(t * 7.1)
        glow(p, 1240, 300, 330 * fl, (255, 190, 100), int(205 * fl))
        glow(p, 1240, 300, 140 * fl, (255, 225, 160), int(210 * fl))
        glow(p, 1240, 560, 150, (255, 190, 100), 80)
        pygame.draw.polygon(p, (130, 140, 255), [(0, 0)] * 0 + [(wx, wy + wh), (wx + ww, wy + wh), (wx + ww + 230, 700), (wx - 120, 700)], 0) if False else None
        glow(p, 360, 580, 280, (110, 130, 220), 60)
        for i in range(8):
            x = 700 + _rnd(i, 1) * 480 + math.sin(t * 0.7 + i) * 20
            y = 280 + _rnd(i, 2) * 260 + math.cos(t * 0.9 + i) * 16
            a = (math.sin(t * 2 + i * 2) + 1) / 2
            glow(p, x, y, 8, (255, 240, 150), int(200 * a))
    else:
        # rayo de sol de la ventana
        a = 0.5 + 0.5 * math.sin(t * 0.6)
        glow(p, 300, 560, 330, (255, 235, 170), int(60 + 20 * a))
        for i in range(_motas):
            x = 180 + _rnd(i, 1) * 420 + math.sin(t * 0.4 + i) * 18
            y = 360 + ((_rnd(i, 2) * 300 + t * 6 * (0.5 + _rnd(i, 3))) % 300)
            glow(p, x, y, 6, (255, 244, 200), int(130 * (0.5 + 0.5 * math.sin(t + i))))


# =====================================================================
#  ARENAS
# =====================================================================
def _suelo_sombras(s, y0, c0, c1):
    _grad(s, (0, y0, ANCHO, ALTO - y0), c0, c1)


def _arena_neutra():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 430), (186, 168, 232), (252, 230, 240))
    for i in range(26):
        x, y = _rnd(i, 1) * ANCHO, _rnd(i, 2) * 330
        pygame.draw.circle(s, (255, 255, 255), (x, y), 3 + 8 * _rnd(i, 3), 0)
    _montanas(s, 430, 120, (160, 144, 208), 8, 5)
    _montanas(s, 440, 80, (140, 126, 192), 8, 9)
    _suelo_sombras(s, 430, (236, 222, 205), (196, 176, 164))
    for k in range(1, 8):
        yy = 430 + int((k / 8) ** 1.6 * (ALTO - 430))
        pygame.draw.line(s, (214, 196, 182), (0, yy), (ANCHO, yy), 2)
    for k in range(-10, 11):
        pygame.draw.line(s, (214, 196, 182), (ANCHO / 2 + k * 100, 430), (ANCHO / 2 + k * 260, ALTO), 1)
    pygame.draw.ellipse(s, (206, 186, 174), (170, 520, 940, 150), 4)
    pygame.draw.ellipse(s, (222, 204, 190), (230, 540, 820, 110), 3)
    return _conv(s)


def _arena_agua():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 300), (96, 190, 255), (204, 240, 255))
    pygame.draw.circle(s, (255, 244, 190), (1010, 120), 70)
    pygame.draw.circle(s, (255, 252, 225), (1010, 120), 50)
    for x, y, sc in [(180, 90, 1.3), (520, 150, 0.9), (800, 70, 1.0)]:
        _nube(s, x, y, sc, (255, 255, 255), (214, 232, 250))
    # isla lejana
    pygame.draw.ellipse(s, (96, 150, 130), (260, 266, 360, 70))
    pygame.draw.polygon(s, (90, 140, 120), [(330, 290), (430, 236), (540, 292)])
    pygame.draw.rect(s, (150, 100, 70), (452, 244, 7, 40))
    for a in (-40, 0, 40, 80, 140):
        r = math.radians(a - 90)
        pygame.draw.line(s, (80, 170, 100), (456, 246), (456 + math.cos(r) * 32, 246 + math.sin(r) * 22 + 10), 5)
    # mar
    _grad(s, (0, 300, ANCHO, 140), (58, 170, 235), (28, 118, 205))
    pygame.draw.line(s, (200, 238, 255), (0, 300), (ANCHO, 300), 3)
    for k in range(10):
        y = 316 + k * 13
        for j in range(8):
            x = (j * 190 + k * 70) % ANCHO
            pygame.draw.line(s, (170, 225, 255), (x, y), (x + 40 + 10 * (k % 3), y), 2)
    # arena
    _grad(s, (0, 430, ANCHO, ALTO - 430), (246, 228, 176), (222, 190, 132))
    pygame.draw.polygon(s, (170, 150, 120), [(0, 430), (ANCHO, 430), (ANCHO, 446), (0, 446)])
    pygame.draw.rect(s, (200, 170, 125), (0, 436, ANCHO, 18))
    for i in range(40):
        x, y = _rnd(i, 1) * ANCHO, 470 + _rnd(i, 2) * 240
        pygame.draw.circle(s, (206, 176, 128), (x, y), 2 + _rnd(i, 3) * 3)
    for (x, y) in [(190, 620), (1060, 560), (840, 660), (360, 700)]:
        pygame.draw.ellipse(s, (255, 214, 220), (x - 20, y - 12, 40, 26))
        pygame.draw.ellipse(s, (210, 150, 160), (x - 20, y - 12, 40, 26), 3)
        for a in range(-2, 3):
            pygame.draw.line(s, (210, 150, 160), (x + a * 7, y - 11), (x + a * 6, y + 10), 2)
    # estrella de mar y roca
    st = []
    for i in range(10):
        r = 24 if i % 2 == 0 else 10
        a = -math.pi / 2 + i * math.pi / 5
        st.append((1130 + math.cos(a) * r, 680 + math.sin(a) * r))
    pygame.draw.polygon(s, (250, 140, 100), st)
    pygame.draw.polygon(s, (170, 80, 60), st, 3)
    pygame.draw.ellipse(s, (130, 130, 140), (60, 640, 120, 64))
    pygame.draw.ellipse(s, (160, 160, 170), (74, 646, 70, 30))
    pygame.draw.ellipse(s, (70, 70, 84), (60, 640, 120, 64), 4)
    return _conv(s)


def _arena_viento():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 470), (90, 178, 250), (226, 246, 255))
    # sol suave
    pygame.draw.circle(s, (255, 250, 220), (230, 130), 60)
    # islas flotantes lejanas
    for x, y, w in [(880, 200, 200), (330, 270, 150)]:
        pygame.draw.polygon(s, (130, 90, 70), [(x - w / 2, y), (x + w / 2, y), (x + w * 0.15, y + w * 0.35), (x - w * 0.1, y + w * 0.45)])
        pygame.draw.ellipse(s, (120, 200, 120), (x - w / 2, y - 24, w, 48))
        pygame.draw.circle(s, (80, 170, 100), (x - w * 0.1, y - 28), 22)
        pygame.draw.rect(s, (130, 90, 70), (x - w * 0.1 - 3, y - 12, 6, 14))
    # nubes del piso (capas)
    for k, (y0, col, sh) in enumerate([(470, (238, 248, 255), (196, 220, 244)), (520, (248, 252, 255), (206, 228, 248)), (590, (255, 255, 255), (214, 232, 250))]):
        for i in range(-1, 14):
            x = i * 110 + (k * 55) % 110
            r = 70 + 22 * _rnd(i, k)
            pygame.draw.circle(s, sh, (x, y0 + 12), r)
        pygame.draw.rect(s, sh, (0, y0 + 40, ANCHO, ALTO))
        for i in range(-1, 14):
            x = i * 110 + (k * 55) % 110
            r = 70 + 22 * _rnd(i, k)
            pygame.draw.circle(s, col, (x, y0), r)
        pygame.draw.rect(s, col, (0, y0 + 30, ANCHO, ALTO))
    _grad(s, (0, 600, ANCHO, ALTO - 600), (255, 255, 255), (222, 238, 252))
    return _conv(s)


def _arena_fuego():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 440), (58, 28, 70), (255, 150, 70), c_mid=(190, 70, 80))
    for i in range(34):
        pygame.draw.circle(s, (255, 230, 200), (_rnd(i, 1) * ANCHO, _rnd(i, 2) * 170), 1 + _rnd(i, 3) * 1.6)
    pygame.draw.circle(s, (255, 190, 100), (190, 330), 90)
    pygame.draw.circle(s, (255, 220, 150), (190, 330), 62)
    _montanas(s, 440, 150, (112, 52, 76), 6, 11)
    # volcan
    vx = 760
    pygame.draw.polygon(s, (92, 56, 66), [(vx - 380, 440), (vx - 70, 190), (vx + 70, 190), (vx + 380, 440)])
    pygame.draw.polygon(s, (120, 72, 82), [(vx - 380, 440), (vx - 70, 190), (vx - 20, 190), (vx - 110, 440)])
    pygame.draw.polygon(s, (70, 40, 54), [(vx + 70, 190), (vx + 380, 440), (vx + 140, 440)])
    pygame.draw.ellipse(s, (255, 140, 50), (vx - 82, 176, 164, 36))
    pygame.draw.ellipse(s, (255, 220, 110), (vx - 56, 182, 112, 22))
    pygame.draw.ellipse(s, (60, 34, 48), (vx - 82, 176, 164, 36), 4)
    for pts in [[(vx - 20, 204), (vx - 36, 270), (vx - 22, 330), (vx - 60, 440)], [(vx + 24, 204), (vx + 40, 280), (vx + 28, 350), (vx + 70, 440)], [(vx, 210), (vx + 6, 300), (vx - 6, 380), (vx + 6, 440)]]:
        pygame.draw.lines(s, (200, 70, 40), False, pts, 14)
        pygame.draw.lines(s, (255, 150, 50), False, pts, 8)
        pygame.draw.lines(s, (255, 230, 130), False, pts, 3)
    # suelo de basalto
    _grad(s, (0, 440, ANCHO, ALTO - 440), (84, 48, 56), (46, 28, 38))
    for k in range(1, 7):
        yy = 440 + int((k / 7) ** 1.6 * (ALTO - 440))
        pygame.draw.line(s, (62, 38, 48), (0, yy), (ANCHO, yy), 2)
    for gx, gy in [(160, 520), (520, 610), (980, 540), (1130, 680), (320, 690), (760, 660)]:
        pts = [(gx, gy)]
        for j in range(1, 7):
            pts.append((gx + j * 26 + (_rnd(j, gx) - 0.5) * 30, gy + (_rnd(j, gy) - 0.5) * 24))
        pygame.draw.lines(s, (200, 60, 30), False, pts, 8)
        pygame.draw.lines(s, (255, 150, 50), False, pts, 4)
        pygame.draw.lines(s, (255, 225, 120), False, pts, 1)
    return _conv(s)


def _arena_hielo():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 440), (140, 196, 240), (236, 248, 255))
    for i in range(30):
        pygame.draw.circle(s, (255, 255, 255), (_rnd(i, 1) * ANCHO, _rnd(i, 2) * 150), 1 + _rnd(i, 3) * 1.4)
    _montanas(s, 420, 250, (176, 204, 236), 6, 2, nieve=(244, 250, 255))
    _montanas(s, 450, 160, (140, 178, 222), 6, 7, nieve=(250, 253, 255))
    _grad(s, (0, 440, ANCHO, ALTO - 440), (248, 252, 255), (200, 224, 244))
    # lomas de nieve
    for i in range(-1, 9):
        x = i * 190
        pygame.draw.ellipse(s, (255, 255, 255), (x, 428, 260, 40))
    for k in range(1, 7):
        yy = 460 + int((k / 7) ** 1.6 * (ALTO - 460))
        pygame.draw.ellipse(s, (232, 244, 255), (-100 + k * 20, yy, ANCHO + 200 - k * 40, 22))
    # iglu
    ix, iy = 150, 480
    pygame.draw.ellipse(s, (190, 215, 240), (ix - 100, iy + 28, 200, 30))
    pygame.draw.circle(s, (232, 244, 255), (ix, iy + 30), 82)
    pygame.draw.rect(s, (248, 252, 255), (ix - 90, iy + 30, 180, 30))
    pygame.draw.circle(s, (160, 190, 224), (ix, iy + 30), 82, 4)
    pygame.draw.rect(s, (160, 190, 224), (ix - 92, iy + 56, 184, 4))
    for yy in range(iy + 60, iy + 116):
        pygame.draw.line(s, s.get_at((ix + 140, yy)), (ix - 100, yy), (ix + 100, yy))
    pygame.draw.ellipse(s, (206, 226, 246), (ix - 96, iy + 52, 192, 22))
    pygame.draw.ellipse(s, (160, 190, 224), (ix - 96, iy + 52, 192, 22), 3)
    for a in range(-3, 4):
        pygame.draw.arc(s, (190, 215, 240), (ix - 80, iy - 50, 160, 160), 0.3 + a * 0.3, 0.3 + a * 0.3 + 0.2, 2)
    pygame.draw.circle(s, (70, 100, 140), (ix, iy + 52), 24)
    pygame.draw.rect(s, (70, 100, 140), (ix - 24, iy + 52, 48, 16))
    # cristales y abeto nevado
    for x, y in [(1100, 520), (1180, 560), (980, 640)]:
        for dx, hh in [(-14, 34), (0, 52), (16, 38)]:
            pts = [(x + dx - 9, y), (x + dx, y - hh), (x + dx + 9, y)]
            pygame.draw.polygon(s, (170, 222, 255), pts)
            pygame.draw.polygon(s, (230, 248, 255), [pts[0], pts[1], (x + dx, y)])
            pygame.draw.polygon(s, (90, 140, 200), pts, 2)
    tx, ty = 1010, 470
    pygame.draw.rect(s, (130, 90, 70), (tx - 6, ty + 20, 12, 40))
    for k in range(3):
        w = 70 - k * 16
        pts = [(tx - w, ty + 30 - k * 36), (tx, ty - 40 - k * 36), (tx + w, ty + 30 - k * 36)]
        pygame.draw.polygon(s, (70, 150, 120), pts)
        pygame.draw.polygon(s, (250, 253, 255), [pts[0], pts[1], (tx - w * 0.3, ty - 8 - k * 36), (tx - w * 0.5, ty + 6 - k * 36), (tx - w * 0.9, ty + 16 - k * 36)][:3] + [(tx - w * 0.1, ty - 4 - k * 36)])
        pygame.draw.polygon(s, (40, 100, 84), pts, 3)
    return _conv(s)


def _arena_tierra():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 440), (255, 190, 120), (255, 238, 196), c_mid=(255, 214, 160))
    pygame.draw.circle(s, (255, 244, 210), (860, 170), 86)
    pygame.draw.circle(s, (255, 252, 232), (860, 170), 60)

    def mesa(x, w, h, col, y0=440):
        pts = [(x, y0), (x + w * 0.08, y0 - h), (x + w * 0.9, y0 - h), (x + w, y0)]
        pygame.draw.polygon(s, col, pts)
        for k in range(1, 5):
            yy = y0 - h + k * h / 5
            pygame.draw.line(s, oscurecer(col, 0.18), (x + w * (0.08 - 0.08 * k / 5 * 0), yy), (x + w * 0.92, yy), 3)
    mesa(-60, 360, 150, (196, 120, 84))
    mesa(300, 240, 100, (210, 140, 98))
    mesa(870, 420, 190, (178, 100, 72))
    mesa(1130, 260, 120, (200, 126, 90))
    _grad(s, (0, 440, ANCHO, ALTO - 440), (226, 182, 122), (186, 136, 88))
    for k in range(1, 7):
        yy = 450 + int((k / 7) ** 1.6 * (ALTO - 450))
        pygame.draw.ellipse(s, (206, 160, 106), (-100 + k * 30, yy, ANCHO + 200 - k * 60, 18))
    # cactus
    for cx, cy, sc in [(180, 520, 1.0), (1110, 560, 1.2), (560, 470, 0.6)]:
        col, bor = (104, 170, 96), (50, 100, 60)
        pygame.draw.rect(s, col, (cx - 15 * sc, cy - 110 * sc, 30 * sc, 120 * sc), border_radius=int(14 * sc))
        pygame.draw.rect(s, col, (cx - 52 * sc, cy - 80 * sc, 22 * sc, 56 * sc), border_radius=int(11 * sc))
        pygame.draw.rect(s, col, (cx - 52 * sc, cy - 46 * sc, 50 * sc, 22 * sc), border_radius=int(11 * sc))
        pygame.draw.rect(s, col, (cx + 28 * sc, cy - 94 * sc, 22 * sc, 56 * sc), border_radius=int(11 * sc))
        pygame.draw.rect(s, col, (cx + 2 * sc, cy - 60 * sc, 48 * sc, 22 * sc), border_radius=int(11 * sc))
        pygame.draw.rect(s, bor, (cx - 15 * sc, cy - 110 * sc, 30 * sc, 120 * sc), 3, border_radius=int(14 * sc))
        pygame.draw.line(s, (150, 210, 130), (cx - 5 * sc, cy - 100 * sc), (cx - 5 * sc, cy - 10 * sc), 3)
        pygame.draw.circle(s, (255, 130, 160), (cx, cy - 112 * sc), 7 * sc)
    # rocas
    for x, y, r in [(420, 640, 46), (720, 690, 36), (950, 520, 30), (60, 660, 54)]:
        pygame.draw.ellipse(s, (150, 106, 76), (x - r, y - r * 0.6, r * 2, r * 1.2))
        pygame.draw.ellipse(s, (184, 138, 100), (x - r * 0.8, y - r * 0.5, r * 1.2, r * 0.6))
        pygame.draw.ellipse(s, (88, 58, 44), (x - r, y - r * 0.6, r * 2, r * 1.2), 4)
    return _conv(s)


def _arena_electrico():
    s = pygame.Surface((ANCHO, ALTO))
    _grad(s, (0, 0, ANCHO, 440), (22, 22, 52), (96, 80, 140))
    for k in range(3):
        for i in range(-1, 10):
            x = i * 160 + k * 60
            y = 60 + k * 70 + 22 * math.sin(i * 1.7 + k)
            r = 80 + 30 * _rnd(i, k)
            col = [(46, 44, 82), (62, 58, 104), (82, 76, 126)][k]
            pygame.draw.circle(s, col, (x, y), r)
        pygame.draw.rect(s, [(46, 44, 82), (62, 58, 104), (82, 76, 126)][k], (0, 0, ANCHO, 40 + k * 70))
    _montanas(s, 460, 120, (40, 34, 74), 6, 13)
    _grad(s, (0, 440, ANCHO, ALTO - 440), (54, 44, 88), (30, 26, 56))
    for k in range(1, 7):
        yy = 450 + int((k / 7) ** 1.6 * (ALTO - 450))
        pygame.draw.line(s, (68, 58, 108), (0, yy), (ANCHO, yy), 2)
    for x, y, rx, ry in [(220, 560, 110, 20), (700, 640, 150, 26), (1060, 520, 90, 16), (480, 700, 100, 16)]:
        pygame.draw.ellipse(s, (88, 100, 160), (x - rx, y - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(s, (130, 150, 210), (x - rx * 0.8, y - ry * 0.6, rx * 1.2, ry * 0.7))
        pygame.draw.ellipse(s, (30, 26, 56), (x - rx, y - ry, rx * 2, ry * 2), 3)
    # torres de pararrayos
    for x in (130, 1150):
        pygame.draw.polygon(s, (30, 28, 50), [(x - 18, 560), (x - 4, 360), (x + 4, 360), (x + 18, 560)])
        pygame.draw.line(s, (30, 28, 50), (x, 360), (x, 320), 4)
        pygame.draw.circle(s, (255, 226, 80), (x, 316), 8)
        pygame.draw.circle(s, (130, 100, 20), (x, 316), 8, 2)
    return _conv(s)


_ARENAS = {None: _arena_neutra, "agua": _arena_agua, "viento": _arena_viento, "fuego": _arena_fuego,
           "hielo": _arena_hielo, "tierra": _arena_tierra, "electrico": _arena_electrico}


def _dinamico(p, tipo, t):
    if tipo == "agua":
        for k in range(4):
            y = 318 + k * 28
            pts = [(x, y + math.sin(x * 0.02 + t * (1.2 + 0.2 * k) + k) * 3) for x in range(0, ANCHO + 20, 20)]
            pygame.draw.lines(p, (210, 240, 255), False, pts, 2)
        # espuma en la orilla
        pts = [(x, 438 + math.sin(x * 0.012 + t * 1.4) * 5 + math.sin(t * 0.8) * 4) for x in range(0, ANCHO + 20, 16)]
        pygame.draw.lines(p, (255, 255, 255), False, pts, 6)
        pts2 = [(x, y + 8) for x, y in pts]
        pygame.draw.lines(p, (214, 240, 255), False, pts2, 3)
        for i in range(10):
            x = _rnd(i, 1) * ANCHO
            y = 305 + _rnd(i, 2) * 110
            a = (math.sin(t * 2 + i * 3) + 1) / 2
            glow(p, x, y, 9, (255, 255, 255), int(180 * a))
    elif tipo == "viento":
        for i in range(6):
            sp = 18 + 10 * i
            x = ((t * sp + i * 270) % (ANCHO + 400)) - 200
            y = 70 + i * 62 + math.sin(t * 0.7 + i) * 8
            spr = _sprite_nube(0.8 + 0.18 * (i % 3), (255, 255, 255), (206, 228, 248))
            p.blit(spr, (x - spr.get_width() / 2, y - spr.get_height() / 2))
        for i in range(8):
            x = ((t * (140 + 30 * i) + i * 190) % (ANCHO + 200)) - 100
            y = 120 + _rnd(i, 4) * 330
            pygame.draw.line(p, (255, 255, 255), (x, y), (x + 70 + 20 * (i % 3), y), 2)
        for i in range(5):
            x = ((t * 80 + i * 300) % (ANCHO + 100)) - 50
            y = 250 + i * 40 + math.sin(t * 2 + i) * 18
            a = t * 3 + i
            pygame.draw.polygon(p, (110, 190, 90), [(x + math.cos(a) * 8, y + math.sin(a) * 4), (x + math.cos(a + 1.6) * 4, y + math.sin(a + 1.6) * 8), (x - math.cos(a) * 8, y - math.sin(a) * 4), (x + math.cos(a - 1.6) * 4, y + math.sin(a - 1.6) * 8)])
    elif tipo == "fuego":
        vx = 760
        pul = 0.75 + 0.25 * math.sin(t * 2.2) + 0.08 * math.sin(t * 7)
        glow(p, vx, 190, 210 * pul, (255, 120, 40), int(230 * pul))
        glow(p, vx, 190, 70, (255, 230, 150), 255)
        for i in range(8):
            ph = (t * 0.2 + i / 8) % 1.0
            x = vx + 20 + math.sin(ph * 6 + i) * 30 + ph * 150
            y = 180 - ph * 170
            suave(p, x, y, 30 + 46 * ph, (96, 60, 70) if ph > 0.2 else (190, 100, 70), int(150 * (1 - ph)))
        for i in range(26):
            ph = (t * (0.18 + 0.1 * _rnd(i, 2)) + _rnd(i, 1)) % 1.0
            x = _rnd(i, 3) * ANCHO + math.sin(t * 2 + i) * 16
            y = 700 - ph * 600
            glow(p, x, y, 6 + 3 * _rnd(i, 4), (255, 150, 60), int(210 * (1 - ph)))
        for gx, gy in [(160, 520), (520, 610), (980, 540)]:
            glow(p, gx + 80, gy, 90, (255, 100, 40), int(55 + 25 * math.sin(t * 2 + gx)))
    elif tipo == "hielo":
        for i in range(3):
            pts_top, pts_bot = [], []
            for x in range(0, ANCHO + 30, 30):
                y = 90 + i * 24 + math.sin(x * 0.006 + t * 0.5 + i) * 40 + math.sin(x * 0.015 - t * 0.8) * 12
                glow(p, x, y, 90, [(60, 255, 190), (90, 190, 255), (180, 120, 255)][i], 38)
        for i in range(60):
            ph = (t * (0.07 + 0.06 * _rnd(i, 2)) + _rnd(i, 1)) % 1.0
            x = (_rnd(i, 3) * ANCHO + math.sin(t * 0.9 + i) * 22 + ph * 90) % ANCHO
            y = ph * 740 - 20
            r = 1.5 + 2 * _rnd(i, 4)
            pygame.draw.circle(p, (255, 255, 255), (x, y), max(1, int(r)))
        for i in range(12):
            x = _rnd(i, 7) * ANCHO
            y = 470 + _rnd(i, 8) * 240
            a = (math.sin(t * 2.4 + i * 2.1) + 1) / 2
            glow(p, x, y, 9, (220, 245, 255), int(200 * a))
    elif tipo == "tierra":
        for i in range(24):
            ph = (t * (0.05 + 0.06 * _rnd(i, 2)) + _rnd(i, 1)) % 1.0
            x = (ph * (ANCHO + 200) - 100)
            y = 450 + _rnd(i, 3) * 250 + math.sin(t * 1.5 + i) * 8
            suave(p, x, y, 16 + 22 * _rnd(i, 4), (226, 190, 140), int(54 * (1 - abs(ph - 0.5) * 1.4)))
        for i in range(10):
            x = _rnd(i, 7) * ANCHO
            y = 300 + _rnd(i, 8) * 400
            a = (math.sin(t + i * 2.3) + 1) / 2
            glow(p, x, y, 6, (255, 235, 180), int(110 * a))
    elif tipo == "electrico":
        ciclo = 4.2
        n = int(t // ciclo)
        ph = t - n * ciclo
        x = 140 + _rnd(n, 5) * (ANCHO - 280)
        if ph < 0.35:
            fl = (1.0 - ph / 0.35)
            if (int(ph * 24) % 3) != 1:
                pts = [(x, 40)]
                for j in range(1, 11):
                    pts.append((x + (_rnd(j, n) - 0.5) * 70, 40 + j * 40))
                pygame.draw.lines(p, (200, 190, 255), False, pts, 8)
                pygame.draw.lines(p, (255, 255, 255), False, pts, 3)
                glow(p, x, 300, 260, (170, 150, 255), int(120 * fl))
            _flash_pantalla(p, 0.28 * fl, (150, 140, 230))
        for i in range(70):
            sp = 520 + 160 * _rnd(i, 2)
            xx = (_rnd(i, 1) * (ANCHO + 200) - t * 90) % (ANCHO + 200) - 100
            yy = (_rnd(i, 3) * 800 + t * sp) % 800 - 40
            pygame.draw.line(p, (170, 180, 230), (xx, yy), (xx - 8, yy + 22), 1)
        for i in range(6):
            a = (math.sin(t * 3 + i * 2.7) + 1) / 2
            gx = 200 + i * 190
            if a > 0.8:
                glow(p, gx, 600 + (i % 2) * 40, 30, (255, 235, 90), int(220 * (a - 0.8) * 5))
    else:
        for i in range(10):
            x = _rnd(i, 1) * ANCHO
            y = 40 + ((_rnd(i, 2) * 400 + t * 10) % 400)
            a = (math.sin(t * 1.4 + i) + 1) / 2
            glow(p, x, y, 8, (255, 255, 255), int(120 * a))


def dibujar_fondo_arena(p, tipo, t):
    if tipo not in _ARENAS:
        tipo = None
    s = _CACHE.get(("arena", tipo))
    if s is None:
        s = _ARENAS[tipo]()
        _CACHE[("arena", tipo)] = s
    p.blit(s, (0, 0))
    _dinamico(p, tipo, t)


def precalentar():
    """Genera todos los fondos en cache (opcional, para evitar el tiron en el primer cuadro)."""
    for n in (False, True):
        _CACHE.setdefault(("hogar", n), _hogar_estatico(n))
    for k, fn in _ARENAS.items():
        _CACHE.setdefault(("arena", k), fn())
    # calienta las texturas de brillo de los efectos
    import arte_tama_fx as fx
    c = pygame.Surface((ANCHO, ALTO))
    for tipo in fx.COL:
        for et in range(4):
            for i in range(24):
                f = i / 23
                fx.dibujar_ataque_cargado(c, tipo, et, 300, 450, 900, 450, f, f * 2)
                fx.dibujar_ataque_basico(c, tipo, et, 300, 450, 900, 450, f, f * 2)
                fx.dibujar_impacto(c, tipo, et, 900, 450, f, f * 2)
                fx.dibujar_carga(c, tipo, et, 300, 450, f, f * 2)
    fx.dibujar_aura_evolucion(c, 600, 400, 0.5, 0.0)
