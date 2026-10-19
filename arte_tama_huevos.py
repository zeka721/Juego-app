"""Huevos de Tamagotchi: 18 disenos distintos (cacheados), grietas, balanceo y cascaras al eclosionar."""

import math

import pygame

from arte_tama_base import CONTORNO, sombra
from nucleo import aclarar, oscurecer

SS = 3                     # supersampling del cache
EW, EH = 112, 150          # tamano del huevo a escala 1
CW, CH = 132, 172          # lienzo (con margen)

# (fondo arriba, fondo abajo, acento 1, acento 2, patron)
DISENOS = [
    ((255, 240, 205), (255, 214, 170), (255, 120, 150), (255, 190, 90), "lunares"),
    ((150, 205, 255), (110, 160, 240), (255, 255, 255), (255, 235, 140), "ondas"),
    ((190, 245, 205), (120, 215, 170), (255, 225, 80), (255, 255, 255), "estrellas"),
    ((215, 190, 250), (170, 140, 235), (255, 255, 255), (255, 170, 220), "zigzag"),
    ((255, 190, 110), (250, 150, 70), (130, 78, 50), (255, 225, 170), "manchas"),
    ((255, 205, 225), (250, 165, 200), (255, 255, 255), (230, 70, 110), "corazones"),
    ((255, 235, 120), (255, 210, 70), (70, 150, 230), (255, 255, 255), "cuadricula"),
    ((120, 225, 220), (60, 185, 195), (200, 255, 245), (40, 130, 150), "escamas"),
    ((255, 130, 120), (235, 85, 95), (255, 235, 200), (255, 255, 255), "diagonales"),
    ((250, 250, 240), (225, 232, 225), (110, 190, 100), (60, 140, 80), "hojas"),
    ((110, 90, 190), (60, 50, 130), (255, 235, 120), (230, 230, 255), "luna_estrellas"),
    ((205, 245, 120), (140, 205, 70), (255, 255, 255), (70, 140, 50), "espirales"),
    ((50, 70, 150), (25, 35, 95), (255, 255, 255), (150, 190, 255), "galaxia"),
    ((255, 225, 140), (225, 175, 70), (255, 245, 200), (190, 120, 40), "rombos"),
    ((190, 205, 225), (150, 168, 200), (255, 255, 255), (110, 130, 175), "nubes"),
    ((255, 215, 235), (200, 230, 255), (255, 170, 190), (170, 215, 255), "arcoiris"),
    ((225, 190, 140), (190, 145, 95), (250, 235, 205), (120, 80, 50), "huellas"),
    ((130, 215, 200), (95, 180, 190), (255, 150, 140), (255, 240, 200), "flores"),
]

_cache_base = {}
_cache_grieta = {}
_cache_cascaras = {}


def _perfil(w, h, cx, cy, n=96):
    pts = []
    for i in range(n):
        u = math.pi * 2 * i / n
        x = (w / 2) * math.sin(u) * (1 - 0.15 * math.cos(u))
        y = -(h / 2) * math.cos(u)
        pts.append((cx + x, cy + y))
    return pts


def _lerp(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _estrella(s, cx, cy, r, color, rot=-math.pi / 2, pico=0.45):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * pico
        a = rot + i * math.pi / 5
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    pygame.draw.polygon(s, color, pts)


def _corazon(s, cx, cy, r, color):
    pts = []
    for i in range(40):
        a = math.pi * 2 * i / 40
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + x * r / 16, cy + y * r / 16 + r * 0.1))
    pygame.draw.polygon(s, color, pts)


def _flor(s, cx, cy, r, c1, c2):
    for i in range(5):
        a = i * math.pi * 2 / 5 - math.pi / 2
        pygame.draw.circle(s, c1, (cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62), r * 0.45)
    pygame.draw.circle(s, c2, (cx, cy), r * 0.38)


def _pat(s, nombre, W, H, c1, c2, k):
    cx, cy = W / 2, H / 2
    u = SS  # unidad: 1 px del tamano base
    x0, x1 = cx - EW * u / 2, cx + EW * u / 2
    y0, y1 = cy - EH * u / 2, cy + EH * u / 2
    if nombre == "lunares":
        for i, (px, py, r) in enumerate([(-30, -40, 9), (10, -52, 7), (32, -22, 10), (-8, -14, 12), (-38, 10, 8), (22, 20, 9),
                                         (-14, 42, 10), (40, 44, 6), (-42, 46, 5), (4, 62, 6), (-26, -62, 4)]):
            pygame.draw.circle(s, c1 if i % 3 else c2, (cx + px * u, cy + py * u), r * u)
    elif nombre == "ondas":
        for j in range(7):
            yy = y0 + (18 + j * 20) * u
            pts = [(x0 + i * 4, yy + math.sin(i * 0.18 + j) * 6 * u) for i in range(int(EW * u / 4) + 3)]
            pygame.draw.lines(s, c1 if j % 2 == 0 else c2, False, pts, int(5 * u))
    elif nombre == "estrellas":
        for i, (px, py, r) in enumerate([(-25, -38, 11), (22, -48, 8), (30, -6, 12), (-8, 4, 9), (-34, 30, 8), (16, 40, 11), (-8, 62, 7),
                                         (42, 38, 6)]):
            _estrella(s, cx + px * u, cy + py * u, r * u, c1 if i % 2 == 0 else c2, rot=-math.pi / 2 + i * 0.3)
    elif nombre == "zigzag":
        for j in range(5):
            yy = y0 + (26 + j * 26) * u
            pts = [(x0 + (i * 14) * u, yy + (9 * u if i % 2 else -9 * u)) for i in range(11)]
            pygame.draw.lines(s, c1 if j % 2 == 0 else c2, False, pts, int(5 * u))
    elif nombre == "manchas":
        for px, py, rx, ry in [(-28, -32, 16, 11), (18, -48, 12, 9), (30, -4, 18, 13), (-24, 14, 14, 18), (14, 42, 20, 12), (-40, 52, 12, 9),
                               (-2, -12, 8, 6), (44, 40, 8, 10)]:
            pygame.draw.ellipse(s, c1, (cx + (px - rx) * u, cy + (py - ry) * u, rx * 2 * u, ry * 2 * u))
            pygame.draw.ellipse(s, c2, (cx + (px - rx * 0.5) * u, cy + (py - ry * 0.65) * u, rx * u * 0.5, ry * u * 0.5))
    elif nombre == "corazones":
        for i, (px, py, r) in enumerate([(-24, -40, 11), (20, -30, 9), (-4, -4, 14), (-34, 24, 9), (30, 22, 11), (0, 50, 10), (-36, 56, 5), (40, 56, 5)]):
            _corazon(s, cx + px * u, cy + py * u, r * u, c1 if i % 2 == 0 else c2)
    elif nombre == "cuadricula":
        for gx in range(-3, 4):
            pygame.draw.line(s, c1, (cx + gx * 20 * u, y0), (cx + gx * 20 * u, y1), int(4 * u))
        for gy in range(-4, 5):
            pygame.draw.line(s, c1, (x0, cy + gy * 20 * u), (x1, cy + gy * 20 * u), int(4 * u))
        for gx in range(-3, 4):
            for gy in range(-4, 5):
                if (gx + gy) % 2 == 0:
                    pygame.draw.circle(s, c2, (cx + (gx * 20 + 10) * u, cy + (gy * 20 + 10) * u), 3.5 * u)
    elif nombre == "escamas":
        for j in range(8):
            for i in range(-3, 5):
                px = cx + (i * 26 + (13 if j % 2 else 0) - 26) * u
                py = y0 + (14 + j * 18) * u
                pygame.draw.circle(s, c2, (px, py), 15 * u, int(3 * u))
                pygame.draw.circle(s, c1, (px, py - 4 * u), 6 * u, int(2 * u))
    elif nombre == "diagonales":
        for j in range(-8, 9):
            pts = [(cx + j * 22 * u - 100 * u, cy + 120 * u), (cx + j * 22 * u - 100 * u + 18 * u, cy + 120 * u),
                   (cx + j * 22 * u + 100 * u + 18 * u, cy - 120 * u), (cx + j * 22 * u + 100 * u, cy - 120 * u)]
            if j % 2 == 0:
                pygame.draw.polygon(s, c1, pts)
        for j in range(-8, 9, 2):
            pts = [(cx + j * 22 * u - 100 * u + 18 * u, cy + 120 * u), (cx + j * 22 * u - 100 * u + 24 * u, cy + 120 * u),
                   (cx + j * 22 * u + 100 * u + 24 * u, cy - 120 * u), (cx + j * 22 * u + 100 * u + 18 * u, cy - 120 * u)]
            pygame.draw.polygon(s, c2, pts)
    elif nombre == "hojas":
        pygame.draw.line(s, c2, (cx - 40 * u, cy + 50 * u), (cx + 20 * u, cy - 62 * u), int(3 * u))
        pygame.draw.line(s, c2, (cx + 42 * u, cy + 40 * u), (cx - 10 * u, cy - 40 * u), int(3 * u))
        for i in range(6):
            for sd, base, dx in ((0, (cx - 40 * u, cy + 50 * u), 60), (1, (cx + 42 * u, cy + 40 * u), -52)):
                f = (i + 1) / 7
                bx = base[0] + dx * f * u
                by = base[1] - (112 if sd == 0 else 80) * f * u
                for sg in (-1, 1):
                    ang = -math.pi / 2 + sg * 0.9
                    L = 17 * u
                    pts = [(bx, by), (bx + math.cos(ang - 0.35) * L * 0.6, by + math.sin(ang - 0.35) * L * 0.6),
                           (bx + math.cos(ang) * L, by + math.sin(ang) * L),
                           (bx + math.cos(ang + 0.35) * L * 0.6, by + math.sin(ang + 0.35) * L * 0.6)]
                    pygame.draw.polygon(s, c1 if (i + sd) % 2 == 0 else c2, pts)
    elif nombre == "luna_estrellas":
        pygame.draw.circle(s, c1, (cx - 6 * u, cy - 6 * u), 22 * u)
        pygame.draw.circle(s, (80, 68, 160), (cx + 4 * u, cy - 12 * u), 19 * u)
        for px, py, r in [(26, -42, 7), (36, 6, 6), (-30, -52, 5), (-36, 30, 7), (12, 44, 8), (40, 46, 4), (-8, 66, 5)]:
            _estrella(s, cx + px * u, cy + py * u, r * u, c2 if r % 2 else c1)
    elif nombre == "espirales":
        for px, py, r in [(-22, -34, 18), (24, -8, 20), (-20, 28, 17), (26, 50, 12), (-4, -64, 9)]:
            pts = []
            for i in range(60):
                a = i * 0.28
                rr = r * u * i / 60
                pts.append((cx + px * u + math.cos(a) * rr, cy + py * u + math.sin(a) * rr))
            pygame.draw.lines(s, c1, False, pts, int(4 * u))
        for px, py in [(34, -42), (-40, 0), (0, 4), (40, 24)]:
            pygame.draw.circle(s, c2, (cx + px * u, cy + py * u), 3.5 * u)
    elif nombre == "galaxia":
        pygame.draw.ellipse(s, (95, 70, 170), (cx - 46 * u, cy - 30 * u, 92 * u, 56 * u))
        pygame.draw.ellipse(s, (130, 95, 205), (cx - 30 * u, cy - 20 * u, 60 * u, 36 * u))
        pygame.draw.ellipse(s, (190, 150, 240), (cx - 14 * u, cy - 11 * u, 28 * u, 18 * u))
        for i in range(34):
            a = (math.sin(i * 12.9898 + k) * 43758.5453) % 1.0
            b = (math.sin(i * 78.233 + k) * 24634.6345) % 1.0
            pygame.draw.circle(s, c1 if i % 3 else c2, (x0 + a * EW * u, y0 + b * EH * u), (1.4 + (i % 3)) * u)
    elif nombre == "rombos":
        for gy in range(-5, 6):
            for gx in range(-4, 5):
                px = cx + (gx * 24 + (12 if gy % 2 else 0)) * u
                py = cy + gy * 15 * u
                pts = [(px, py - 14 * u), (px + 12 * u, py), (px, py + 14 * u), (px - 12 * u, py)]
                if (gx + gy) % 2 == 0:
                    pygame.draw.polygon(s, c1, pts)
                else:
                    pygame.draw.polygon(s, c2, pts, int(3 * u))
    elif nombre == "nubes":
        for px, py, r in [(-26, -44, 14), (24, -16, 17), (-20, 22, 15), (22, 54, 12)]:
            for dx, dy, rr in [(-0.9, 0.2, 0.7), (0, -0.3, 1.0), (0.9, 0.2, 0.75), (0, 0.4, 0.8)]:
                pygame.draw.circle(s, c1, (cx + (px + dx * r) * u, cy + (py + dy * r * 0.7) * u), rr * r * u * 0.8)
            pygame.draw.line(s, c2, (cx + (px - r) * u, cy + (py + r * 0.6) * u), (cx + (px + r) * u, cy + (py + r * 0.6) * u), int(3 * u))
    elif nombre == "arcoiris":
        cols = [(255, 140, 150), (255, 200, 120), (255, 245, 140), (150, 230, 160), (130, 205, 255), (190, 160, 250)]
        for i, c in enumerate(cols):
            pygame.draw.rect(s, c, (x0 - 4 * u, y0 + (10 + i * 22.5) * u, EW * u + 8 * u, 12 * u))
        for px, py, r in [(-30, -30, 5), (30, 10, 6), (-10, 54, 5), (36, -52, 4)]:
            _estrella(s, cx + px * u, cy + py * u, r * u * 1.6, (255, 255, 255))
    elif nombre == "huellas":
        for i, (px, py, r, rot) in enumerate([(-24, -40, 9, -0.3), (20, -18, 10, 0.4), (-22, 14, 10, -0.2), (24, 44, 9, 0.3), (-8, 62, 6, 0)]):
            X, Y = cx + px * u, cy + py * u
            pygame.draw.ellipse(s, c2, (X - r * u * 0.9, Y - r * u * 0.5, r * 1.8 * u, r * 1.5 * u))
            for q in range(4):
                a = rot - math.pi / 2 + (q - 1.5) * 0.55
                pygame.draw.circle(s, c2, (X + math.cos(a) * r * 1.25 * u, Y + math.sin(a) * r * 1.25 * u - r * 0.15 * u), r * 0.38 * u)
        for gx in range(-3, 4):
            for gy in range(-4, 5):
                if (gx + gy) % 2 == 0:
                    pygame.draw.rect(s, c1, (cx + gx * 20 * u - 5 * u, cy + gy * 20 * u - 5 * u, 10 * u, 10 * u), border_radius=int(2 * u))
    elif nombre == "flores":
        for i, (px, py, r) in enumerate([(-24, -38, 13), (22, -20, 11), (-8, 8, 14), (-34, 38, 10), (28, 46, 12), (4, -64, 7)]):
            _flor(s, cx + px * u, cy + py * u, r * u, c1 if i % 2 == 0 else c2, (255, 220, 90) if i % 2 == 0 else (255, 140, 130))
        for px, py in [(36, -50), (-40, -8), (40, 12), (-6, 40)]:
            pygame.draw.circle(s, (255, 255, 255), (cx + px * u, cy + py * u), 3 * u)


def _base(k):
    """Huevo k a escala 1 (superficie CWxCH), sin grietas."""
    k = int(k) % 18
    if k in _cache_base:
        return _cache_base[k]
    top, bot, c1, c2, pat = DISENOS[k]
    W, H = CW * SS, CH * SS
    cx, cy = W / 2, H / 2
    lienzo = pygame.Surface((W, H), pygame.SRCALPHA)
    # degradado vertical
    y_ini, y_fin = int(cy - EH * SS / 2), int(cy + EH * SS / 2)
    for y in range(y_ini, y_fin + 1):
        f = (y - y_ini) / max(1, y_fin - y_ini)
        pygame.draw.line(lienzo, _lerp(top, bot, f), (0, y), (W, y))
    _pat(lienzo, pat, W, H, c1, c2, k)
    # mascara de huevo
    pts = _perfil(EW * SS, EH * SS, cx, cy)
    mask = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), pts)
    lienzo.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # sombreado: oscurece borde inferior derecho, luz arriba izquierda
    sh = pygame.Surface((W, H), pygame.SRCALPHA)
    oscuro = oscurecer(bot, 0.6)
    pygame.draw.polygon(sh, oscuro + (95,), pts)
    luz = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.ellipse(luz, (0, 0, 0, 0), (0, 0, 1, 1))
    # recorta la zona iluminada restando una elipse desplazada
    hueco = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.ellipse(hueco, (255, 255, 255, 255), (cx - EW * SS * 0.60, cy - EH * SS * 0.60, EW * SS * 1.05, EH * SS * 1.05))
    hueco = pygame.transform.smoothscale(pygame.transform.smoothscale(hueco, (W // 8, H // 8)), (W, H))
    inv = pygame.Surface((W, H), pygame.SRCALPHA)
    inv.fill((255, 255, 255, 255))
    inv.blit(hueco, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    sh.blit(inv, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    sh.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    lienzo.blit(sh, (0, 0))
    # brillo
    br = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.ellipse(br, (255, 255, 255, 170), (cx - EW * SS * 0.30, cy - EH * SS * 0.36, EW * SS * 0.16, EH * SS * 0.2))
    pygame.draw.circle(br, (255, 255, 255, 190), (cx - EW * SS * 0.10, cy - EH * SS * 0.40), EW * SS * 0.028)
    br = pygame.transform.rotate(br, 0)
    lienzo.blit(br, (0, 0))
    pygame.draw.polygon(lienzo, CONTORNO, pts, int(3.2 * SS))
    s = pygame.transform.smoothscale(lienzo, (CW, CH))
    _cache_base[k] = s
    return s


def _siluet_mask(s):
    m = pygame.mask.from_surface(s, 40)
    return m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


def _ruta_grieta(grieta):
    """Polilineas (en coordenadas de lienzo CWxCH) de la grieta segun nivel 1..4."""
    cx, cy = CW / 2, CH / 2
    caminos = []
    if grieta >= 1:
        caminos.append([(cx + 8, cy - 70), (cx + 2, cy - 58), (cx + 12, cy - 48), (cx + 4, cy - 38)])
    if grieta >= 2:
        caminos.append([(cx + 4, cy - 38), (cx - 8, cy - 30), (cx - 2, cy - 20), (cx - 14, cy - 12), (cx - 8, cy - 2)])
        caminos.append([(cx + 12, cy - 48), (cx + 24, cy - 44), (cx + 30, cy - 34)])
    if grieta >= 3:
        caminos.append([(cx - 8, cy - 2), (cx - 24, cy + 6), (cx - 32, cy + 0), (cx - 46, cy + 8)])
        caminos.append([(cx - 2, cy - 20), (cx + 12, cy - 14), (cx + 20, cy - 22), (cx + 34, cy - 14)])
        caminos.append([(cx - 14, cy - 12), (cx - 30, cy - 22), (cx - 38, cy - 34)])
    if grieta >= 4:
        caminos.append([(cx - 46, cy + 8), (cx - 40, cy + 20), (cx - 28, cy + 14), (cx - 20, cy + 26), (cx - 6, cy + 18), (cx + 6, cy + 30),
                        (cx + 18, cy + 20), (cx + 30, cy + 30), (cx + 44, cy + 18)])
        caminos.append([(cx + 34, cy - 14), (cx + 40, cy - 2), (cx + 50, cy + 6), (cx + 44, cy + 18)])
        caminos.append([(cx - 8, cy - 2), (cx + 4, cy + 8), (cx + 0, cy + 18)])
    return caminos


def _huevo_grieta(k, grieta):
    key = (k, grieta)
    if key in _cache_grieta:
        return _cache_grieta[key]
    base = _base(k)
    if grieta <= 0:
        _cache_grieta[key] = base
        return base
    s = base.copy()
    W, H = CW * SS, CH * SS
    lin = pygame.Surface((W, H), pygame.SRCALPHA)
    caminos = _ruta_grieta(min(4, grieta))
    for c in caminos:
        pts = [(x * SS, y * SS) for x, y in c]
        pygame.draw.lines(lin, (255, 245, 190, 255) if grieta >= 4 else (255, 255, 255, 120), False, pts, int((6.5 if grieta >= 4 else 5.5) * SS))
    for c in caminos:
        pts = [(x * SS, y * SS) for x, y in c]
        pygame.draw.lines(lin, CONTORNO + (255,), False, pts, int(3.4 * SS))
        # chispitas de cascara en las puntas
        pygame.draw.lines(lin, (0, 0, 0, 0), False, pts, 0)
    lin = pygame.transform.smoothscale(lin, (CW, CH))
    lin.blit(_siluet_mask(base), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(lin, (0, 0))
    _cache_grieta[key] = s
    return s


def _aura(p, cx, cy, rx, ry, color, a):
    from arte_tama_fx import glow
    glow(p, cx, cy, max(rx, ry) * 1.25, color, a)


def dibujar_huevo(p, k, cx, cy, escala=1.0, t=0.0, grieta=0, mecer=0.0, brillo=0.0):
    k = int(k) % 18
    grieta = max(0, min(4, int(grieta)))
    mecer = max(0.0, min(1.0, mecer))
    spr = _huevo_grieta(k, grieta)
    # sombra en el suelo
    base_y = cy + EH * 0.5 * escala
    sombra(p, cx, base_y - 2 * escala, EW * 0.95 * escala, EW * 0.2 * escala, 70)
    if brillo > 0:
        _aura(p, cx, cy, EW * escala, EH * escala * 0.9, (255, 205, 110), int(255 * min(1.0, brillo) * 0.8))
    if grieta >= 4:
        from arte_tama_fx import glow
        glow(p, cx, cy + 4 * escala, EW * 0.95 * escala, (255, 230, 150), int(110 + 40 * math.sin(t * 9)))
    ang = 0.0
    desp = 0.0
    if mecer > 0:
        ang = math.sin(t * 7.5) * 9 * mecer * (1 + 0.25 * grieta / 4)
        desp = -abs(math.sin(t * 7.5)) * 3 * mecer * escala
    elif grieta == 0 and brillo <= 0:
        ang = 0.0
    w = int(CW * escala)
    h = int(CH * escala)
    if abs(ang) > 0.05:
        # girar alrededor de la base (centro-abajo del huevo)
        piv_y = EH * 0.5 - 6
        img = pygame.transform.rotozoom(spr, ang, escala)
        a = math.radians(ang)
        # centro del lienzo respecto al pivote
        vx, vy = 0.0, -(piv_y)  # vector pivote -> centro (px escala 1)
        rx = vx * math.cos(a) + vy * math.sin(a)
        ry = -vx * math.sin(a) + vy * math.cos(a)
        px, py = cx, cy + piv_y * escala
        p.blit(img, img.get_rect(center=(px + rx * escala, py + ry * escala + desp)))
    else:
        img = spr if abs(escala - 1.0) < 1e-3 else pygame.transform.smoothscale(spr, (max(2, w), max(2, h)))
        p.blit(img, img.get_rect(center=(cx, cy + desp)))


def _pieza(k, cual):
    """Piezas de cascara: 'base', 'izq', 'der', 'esq0'.. 'esq3' (cada una superficie CWxCH)."""
    key = (k, cual)
    if key in _cache_cascaras:
        return _cache_cascaras[key]
    egg = _base(k)
    sil = _siluet_mask(egg)
    cx, cy = CW / 2, CH / 2
    yc = cy + 2
    jag = []
    n = 9
    for i in range(n + 1):
        x = cx - 62 + i * 124 / n
        jag.append((x, yc + (-9 if i % 2 else 9) + (3 if i % 3 == 0 else 0)))
    big = 400
    W, H = CW * SS, CH * SS

    def poligono(pts):
        m = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(x * SS, y * SS) for x, y in pts])
        return pygame.transform.smoothscale(m, (CW, CH))

    top_poly = [(cx - big, cy - big)] + [(cx + big, cy - big), (cx + big, jag[-1][1])] + list(reversed(jag)) + [(cx - big, jag[0][1])]
    if cual == "base":
        poly = [(cx - big, cy + big), (cx + big, cy + big), (cx + big, jag[-1][1])] + list(reversed(jag)) + [(cx - big, jag[0][1])]
    elif cual == "izq":
        poly = [(cx, cy - big)] + [(cx - big, cy - big), (cx - big, jag[0][1])] + jag[: n // 2 + 1] + [(cx + 2, jag[n // 2][1] - 22), (cx - 5, cy - 40), (cx + 4, cy - 60)]
    elif cual == "der":
        poly = [(cx + 4, cy - 60), (cx - 5, cy - 40), (cx + 2, jag[n // 2][1] - 22)] + jag[n // 2:] + [(cx + big, jag[-1][1]), (cx + big, cy - big), (cx, cy - big)]
    else:
        i = int(cual[3:])
        # fragmentos: pedacitos triangulares del borde (se toman de la zona superior)
        pos = [(-30, -22), (24, -34), (-8, -52), (40, -8)][i]
        pts = [(cx + pos[0] - 14, cy + pos[1] + 8), (cx + pos[0] + 2, cy + pos[1] - 14), (cx + pos[0] + 16, cy + pos[1] + 6)]
        poly = pts
    m = poligono(poly)
    pieza = egg.copy()
    pieza.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if cual in ("base", "izq", "der"):
        W2, H2 = CW * SS, CH * SS
        lin = pygame.Surface((W2, H2), pygame.SRCALPHA)
        if cual == "base":
            interior = [(x, y - 7) for x, y in jag]
            pygame.draw.polygon(lin, (255, 246, 215, 255), [(x * SS, y * SS) for x, y in jag + list(reversed(interior))])
            pygame.draw.lines(lin, CONTORNO + (255,), False, [(x * SS, y * SS) for x, y in jag], int(3.4 * SS))
        else:
            pts = jag[: n // 2 + 1] if cual == "izq" else jag[n // 2:]
            pygame.draw.lines(lin, CONTORNO + (255,), False, [(x * SS, y * SS) for x, y in pts], int(3.4 * SS))
        lin = pygame.transform.smoothscale(lin, (CW, CH))
        lin.blit(sil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pieza.blit(lin, (0, 0))
        if cual == "base":
            pieza.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    else:
        pygame.draw.polygon(pieza, CONTORNO, [(x, y) for x, y in poly], 2)
        pieza.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    _cache_cascaras[key] = pieza
    return pieza


def dibujar_cascaras(p, k, cx, cy, f, t):
    """Cascaras saltando al eclosionar. f 0..1 (0 = recien abierto)."""
    from arte_tama_fx import glow, destello_estrella
    k = int(k) % 18
    f = max(0.0, min(1.0, f))
    g = 9.0
    # destello y brillo calido en los primeros instantes
    if f < 0.55:
        a = (1 - f / 0.55)
        glow(p, cx, cy, 170 * (0.6 + f), (255, 240, 180), int(230 * a))
        destello_estrella(p, cx, cy, 110 * (0.5 + f), (255, 250, 220), a, rot=t)
    off = (cx - CW / 2, cy - CH / 2)
    alfa = 255 if f < 0.7 else int(255 * (1 - (f - 0.7) / 0.3))
    # base se queda; se hunde un poquito y se desvanece al final
    base = _pieza(k, "base")
    b2 = base if alfa >= 255 else base.copy()
    if alfa < 255:
        b2.set_alpha(alfa)
    p.blit(b2, (off[0], off[1] + min(f * 6, 3)))
    sombra(p, cx, cy + EH * 0.5 - 2, EW * 0.95, EW * 0.2, int(70 * alfa / 255))
    # tapas
    for cual, vx, vy, vr in (("izq", -85, -260, -190), ("der", 95, -300, 210)):
        x = vx * f * 0.9
        y = vy * f - vy * 1.2 * f * f
        ang = vr * f
        img = pygame.transform.rotozoom(_pieza(k, cual), ang, 1.0)
        img.set_alpha(alfa)
        p.blit(img, img.get_rect(center=(cx + x, cy + y - 22 * f)))
    for i, (vx, vy, vr) in enumerate([(-150, -170, 400), (130, -140, -360), (-60, -250, 520), (170, -200, -300)]):
        x = vx * f
        y = vy * f - vy * 1.25 * f * f
        img = pygame.transform.rotozoom(_pieza(k, "esq%d" % i), vr * f, 1.0)
        img.set_alpha(alfa)
        p.blit(img, img.get_rect(center=(cx + x, cy + y)))
    # chispas
    for i in range(12):
        a = i * math.pi * 2 / 12 + 0.3
        d = 30 + f * (80 + (i % 3) * 25)
        al = max(0.0, 1 - f * 1.2)
        if al > 0:
            glow(p, cx + math.cos(a) * d, cy - 10 + math.sin(a) * d * 0.8 + f * f * 40, 9 + 5 * (i % 2), (255, 235, 150), int(220 * al))
