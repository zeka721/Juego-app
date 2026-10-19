"""Iconos de tipo y de accion, caca simpatica y nubes de estado (todo cacheado y suavizado)."""

import math

import pygame

from arte_tama_base import CONTORNO
from nucleo import aclarar, oscurecer

SS = 4


class _L:
    """Lienzo en coordenadas unitarias (0..1)."""

    def __init__(self, n):
        self.n = n * SS
        self.s = pygame.Surface((self.n, self.n), pygame.SRCALPHA)

    def u(self, v):
        return v * self.n

    def w(self, v):
        return max(1, int(round(v * self.n)))

    def pts(self, P):
        return [(x * self.n, y * self.n) for x, y in P]

    def poly(self, fill, P, borde=CONTORNO, g=0.04):
        if fill is not None:
            pygame.draw.polygon(self.s, fill, self.pts(P))
        if borde:
            pygame.draw.polygon(self.s, borde, self.pts(P), self.w(g))
            for x, y in self.pts(P):
                pygame.draw.circle(self.s, borde, (x, y), self.w(g) / 2)

    def circ(self, fill, c, r, borde=CONTORNO, g=0.04):
        if fill is not None:
            pygame.draw.circle(self.s, fill, (c[0] * self.n, c[1] * self.n), r * self.n)
        if borde:
            pygame.draw.circle(self.s, borde, (c[0] * self.n, c[1] * self.n), r * self.n, self.w(g))

    def elip(self, fill, rect, borde=CONTORNO, g=0.04):
        r = pygame.Rect(rect[0] * self.n, rect[1] * self.n, rect[2] * self.n, rect[3] * self.n)
        if fill is not None:
            pygame.draw.ellipse(self.s, fill, r)
        if borde:
            pygame.draw.ellipse(self.s, borde, r, self.w(g))

    def rect(self, fill, rect, rad=0.05, borde=CONTORNO, g=0.04):
        r = pygame.Rect(rect[0] * self.n, rect[1] * self.n, rect[2] * self.n, rect[3] * self.n)
        if fill is not None:
            pygame.draw.rect(self.s, fill, r, border_radius=int(rad * self.n))
        if borde:
            pygame.draw.rect(self.s, borde, r, self.w(g), border_radius=int(rad * self.n))

    def linea(self, c, a, b, g=0.04):
        pygame.draw.line(self.s, c, (a[0] * self.n, a[1] * self.n), (b[0] * self.n, b[1] * self.n), self.w(g))
        for q in (a, b):
            pygame.draw.circle(self.s, c, (q[0] * self.n, q[1] * self.n), self.w(g) / 2)

    def lineas(self, c, P, g=0.04, cerrado=False):
        pygame.draw.lines(self.s, c, cerrado, self.pts(P), self.w(g))
        for x, y in self.pts(P):
            pygame.draw.circle(self.s, c, (x, y), self.w(g) / 2)

    def arco(self, c, rect, a0, a1, g=0.04):
        r = pygame.Rect(rect[0] * self.n, rect[1] * self.n, rect[2] * self.n, rect[3] * self.n)
        pygame.draw.arc(self.s, c, r, a0, a1, self.w(g))

    def fin(self, tam):
        return pygame.transform.smoothscale(self.s, (tam, tam))


def _curva(f, N=40):
    return [f(i / N) for i in range(N + 1)]


def _brillo_u(L, c, r, a=190):
    s = pygame.Surface((L.n, L.n), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (255, 255, 255, a), (c[0] * L.n - r * L.n, c[1] * L.n - r * L.n * 0.6, r * 2 * L.n, r * 1.2 * L.n))
    L.s.blit(s, (0, 0))


# ------------------------------------------------------------------ acciones
def _ic_comer(L):
    # manzana
    L.linea(CONTORNO, (0.5, 0.26), (0.55, 0.1), 0.06)
    L.poly((90, 190, 80), [(0.55, 0.17), (0.7, 0.05), (0.84, 0.13), (0.7, 0.26), (0.58, 0.22)], g=0.035)
    cuerpo = [(0.5 + 0.40 * math.sin(a) * (1 - 0.1 * math.cos(a)), 0.58 - 0.34 * math.cos(a) * (1 if math.cos(a) < 0 else 0.9) + (0.05 if abs(a - math.pi * 2) < 0.25 or abs(a) < 0.25 else 0))
              for a in [i * math.pi * 2 / 48 for i in range(48)]]
    # forma con hendidura arriba
    cuerpo = []
    for i in range(60):
        a = i * math.pi * 2 / 60
        x = 0.5 + 0.40 * math.sin(a)
        y = 0.57 - 0.33 * math.cos(a)
        if math.cos(a) > 0.7:
            y += 0.06 * (math.cos(a) - 0.7) / 0.3
        if math.cos(a) < -0.5:
            x = 0.5 + 0.34 * math.sin(a)
        cuerpo.append((x, y))
    L.poly((235, 62, 66), cuerpo)
    L.poly(None, cuerpo, borde=None)
    # sombra y brillo
    L.arco((190, 35, 50), (0.14, 0.24, 0.72, 0.66), -0.9, 0.6, 0.06)
    _brillo_u(L, (0.32, 0.4), 0.09, 200)
    L.circ((255, 255, 255), (0.27, 0.56), 0.025, borde=None)
    # mordisco
    L.circ((0, 0, 0, 0), (0.9, 0.5), 0.0, borde=None)


def _ic_jugar(L):
    c = (0.5, 0.5)
    r = 0.4
    L.circ((255, 255, 255), c, r, borde=None)
    cols = [(240, 70, 80), (255, 205, 60), (70, 160, 240), (90, 200, 120)]
    cx, cy = c
    for i in range(4):
        a0 = i * math.pi / 2 - math.pi / 4 + 0.4
        P = [c] + [(cx + math.cos(a0 + j * 0.0245 * 64 / 10) * r, cy + math.sin(a0 + j * 0.0245 * 64 / 10) * r) for j in range(0, 11)]
        pygame.draw.polygon(L.s, cols[i], L.pts(P))
    # estrella blanca central
    L.circ((255, 255, 255), c, 0.12, borde=CONTORNO, g=0.025)
    L.circ(None, c, r, borde=CONTORNO, g=0.045)
    _brillo_u(L, (0.34, 0.3), 0.09, 190)


def _ic_limpiar(L):
    # esponja
    L.rect((255, 214, 70), (0.14, 0.38, 0.66, 0.42), rad=0.1)
    L.rect((120, 205, 130), (0.14, 0.58, 0.66, 0.22), rad=0.08)
    L.rect(None, (0.14, 0.38, 0.66, 0.42), rad=0.1)
    for x, y, r in [(0.3, 0.48, 0.035), (0.5, 0.45, 0.028), (0.66, 0.5, 0.034), (0.42, 0.52, 0.02), (0.58, 0.55, 0.02)]:
        L.circ((235, 170, 40), (x, y), r, borde=None)
    L.linea((255, 240, 160), (0.22, 0.42), (0.5, 0.42), 0.03)
    # burbujas
    for x, y, r in [(0.76, 0.26, 0.11), (0.58, 0.14, 0.07), (0.88, 0.5, 0.06), (0.3, 0.18, 0.05)]:
        L.circ((200, 235, 255), (x, y), r, borde=(70, 130, 200), g=0.025)
        L.circ((255, 255, 255), (x - r * 0.3, y - r * 0.3), r * 0.25, borde=None)


def _ic_dormir(L):
    # luna creciente + estrella + z
    P = []
    for i in range(41):
        a = -math.pi * 0.62 + i * math.pi * 1.24 / 40
        P.append((0.46 + math.cos(a) * 0.36, 0.52 + math.sin(a) * 0.36))
    for i in range(41):
        a = math.pi * 0.62 - i * math.pi * 1.24 / 40
        P.append((0.62 + math.cos(a) * 0.29, 0.5 + math.sin(a) * 0.30))
    # luna: circulo grande menos circulo
    s = pygame.Surface((L.n, L.n), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 214, 90), (0.45 * L.n, 0.55 * L.n), 0.36 * L.n)
    pygame.draw.circle(s, (0, 0, 0, 0), (0.62 * L.n, 0.45 * L.n), 0.3 * L.n)
    m = pygame.mask.from_surface(s)
    borde = m.outline()
    # contorno
    L.s.blit(s, (0, 0))
    # cubrimos con circulo transparente: dibujar contorno a mano
    if len(borde) > 2:
        pygame.draw.polygon(L.s, CONTORNO, borde, L.w(0.045))
    pygame.draw.circle(L.s, (255, 244, 170), (0.27 * L.n, 0.64 * L.n), 0.035 * L.n)
    pygame.draw.circle(L.s, (240, 190, 70), (0.2 * L.n, 0.46 * L.n), 0.03 * L.n)
    # estrella
    st = []
    for i in range(10):
        r = 0.1 if i % 2 == 0 else 0.045
        a = -math.pi / 2 + i * math.pi / 5
        st.append((0.78 + math.cos(a) * r, 0.24 + math.sin(a) * r))
    L.poly((255, 240, 130), st, g=0.03)
    # Z
    L.lineas(CONTORNO, [(0.7, 0.58), (0.86, 0.58), (0.7, 0.74), (0.86, 0.74)], 0.07)
    L.lineas((150, 175, 255), [(0.7, 0.58), (0.86, 0.58), (0.7, 0.74), (0.86, 0.74)], 0.035)


def _ic_curar(L):
    # corazon con cruz
    P = []
    for i in range(60):
        a = math.pi * 2 * i / 60
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        P.append((0.5 + x * 0.027, 0.47 + y * 0.027))
    L.poly((246, 82, 112), P, g=0.045)
    _brillo_u(L, (0.3, 0.3), 0.08, 190)
    cr = [(0.43, 0.28), (0.57, 0.28), (0.57, 0.42), (0.71, 0.42), (0.71, 0.56), (0.57, 0.56), (0.57, 0.7), (0.43, 0.7), (0.43, 0.56), (0.29, 0.56), (0.29, 0.42), (0.43, 0.42)]
    L.poly((255, 255, 255), cr, borde=(190, 45, 80), g=0.025)


def _ic_entrenar(L):
    # guante de boxeo
    cuerpo = [(0.22, 0.46), (0.2, 0.28), (0.34, 0.12), (0.58, 0.1), (0.78, 0.2), (0.84, 0.42), (0.8, 0.62), (0.68, 0.72), (0.62, 0.84), (0.34, 0.84), (0.3, 0.7), (0.22, 0.6)]
    L.poly((232, 58, 62), cuerpo, g=0.05)
    _brillo_u(L, (0.45, 0.24), 0.14, 160)
    # pulgar
    L.poly((246, 90, 90), [(0.2, 0.46), (0.22, 0.36), (0.36, 0.34), (0.42, 0.46), (0.34, 0.58), (0.22, 0.58)], g=0.035)
    L.linea((170, 36, 50), (0.5, 0.62), (0.74, 0.58), 0.03)
    # munequera
    L.rect((250, 245, 235), (0.3, 0.74, 0.34, 0.2), rad=0.04)
    L.linea((200, 190, 175), (0.36, 0.8), (0.58, 0.8), 0.025)
    L.linea((200, 190, 175), (0.36, 0.87), (0.58, 0.87), 0.025)


def _ic_cuaderno(L):
    # libro abierto
    L.poly((120, 82, 190), [(0.04, 0.3), (0.5, 0.22), (0.96, 0.3), (0.96, 0.86), (0.5, 0.8), (0.04, 0.86)], g=0.045)
    L.poly((255, 250, 238), [(0.09, 0.27), (0.5, 0.2), (0.5, 0.74), (0.09, 0.8)], g=0.03)
    L.poly((250, 244, 226), [(0.5, 0.2), (0.91, 0.27), (0.91, 0.8), (0.5, 0.74)], g=0.03)
    for i in range(4):
        y = 0.34 + i * 0.09
        L.linea((150, 170, 210), (0.15, y + 0.01), (0.44, y - 0.01), 0.025)
        if i < 3:
            L.linea((150, 170, 210), (0.56, y - 0.01), (0.85, y + 0.01), 0.025)
    L.poly((255, 110, 120), [(0.7, 0.2), (0.8, 0.22), (0.8, 0.38), (0.75, 0.33), (0.7, 0.36)], g=0.025)
    # estrellita
    st = []
    for i in range(10):
        r = 0.07 if i % 2 == 0 else 0.03
        a = -math.pi / 2 + i * math.pi / 5
        st.append((0.78 + math.cos(a) * r, 0.58 + math.sin(a) * r))
    L.poly((255, 215, 80), st, g=0.02)


def _ic_huevos(L):
    P = []
    for i in range(64):
        a = math.pi * 2 * i / 64
        P.append((0.5 + 0.31 * math.sin(a) * (1 - 0.15 * math.cos(a)), 0.52 - 0.4 * math.cos(a)))
    L.poly((255, 238, 200), P, g=0.045)
    # manchas
    s = pygame.Surface((L.n, L.n), pygame.SRCALPHA)
    for x, y, r, c in [(0.4, 0.34, 0.07, (255, 130, 150)), (0.62, 0.45, 0.06, (255, 190, 90)), (0.44, 0.6, 0.075, (130, 190, 255)), (0.62, 0.72, 0.05, (255, 130, 150)), (0.34, 0.5, 0.035, (255, 190, 90))]:
        pygame.draw.circle(s, c, (x * L.n, y * L.n), r * L.n)
    m = pygame.Surface((L.n, L.n), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), L.pts(P))
    s.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    L.s.blit(s, (0, 0))
    _brillo_u(L, (0.38, 0.24), 0.07, 200)
    L.poly(None, P, g=0.045)
    # destellitos
    for x, y in [(0.84, 0.22), (0.14, 0.7)]:
        L.poly((255, 240, 140), [(x, y - 0.09), (x + 0.025, y - 0.025), (x + 0.09, y), (x + 0.025, y + 0.025), (x, y + 0.09), (x - 0.025, y + 0.025), (x - 0.09, y), (x - 0.025, y - 0.025)], borde=(220, 170, 60), g=0.015)


def _ic_volver(L):
    L.circ((255, 196, 80), (0.5, 0.5), 0.42, g=0.045)
    _brillo_u(L, (0.38, 0.26), 0.14, 130)
    P = [(0.2, 0.5), (0.46, 0.26), (0.46, 0.4), (0.78, 0.4), (0.78, 0.6), (0.46, 0.6), (0.46, 0.74)]
    L.poly((255, 255, 255), P, borde=CONTORNO, g=0.04)


_ACC = {"comer": _ic_comer, "jugar": _ic_jugar, "limpiar": _ic_limpiar, "dormir": _ic_dormir, "curar": _ic_curar,
        "entrenar": _ic_entrenar, "cuaderno": _ic_cuaderno, "huevos": _ic_huevos, "volver": _ic_volver}
_cache_acc = {}


def _grisear(s):
    g = s.copy()
    arr = pygame.surfarray.pixels3d(g)
    gris = (arr[:, :, 0] * 0.3 + arr[:, :, 1] * 0.59 + arr[:, :, 2] * 0.11) * 0.8 + 40
    for i in range(3):
        arr[:, :, i] = gris.astype("uint8")
    del arr
    g.set_alpha(190)
    return g


def icono_accion(accion, tam, activo=True):
    tam = max(8, int(tam))
    key = (accion, tam, bool(activo))
    s = _cache_acc.get(key)
    if s is None:
        fn = _ACC.get(accion)
        if fn is None:
            fn = _ic_huevos
        L = _L(tam)
        fn(L)
        s = L.fin(tam)
        # sombrita suave debajo
        if not activo:
            s = _grisear(s)
        _cache_acc[key] = s
    return s


def dibujar_icono_accion(p, accion, cx, cy, tam, activo=True):
    s = icono_accion(accion, tam, activo)
    p.blit(s, s.get_rect(center=(int(cx), int(cy))))


# ------------------------------------------------------------------ tipos
COLOR_TIPO = {"agua": (70, 160, 255), "viento": (120, 215, 190), "fuego": (255, 120, 50),
              "hielo": (140, 215, 250), "tierra": (172, 124, 74), "electrico": (255, 210, 50)}


def _sim_agua(L):
    P = []
    for i in range(48):
        a = math.pi * 2 * i / 48
        P.append((0.5 + 0.2 * math.cos(a), 0.62 + 0.2 * math.sin(a)))
    P += [(0.5, 0.2)]
    gota = [(0.5, 0.17), (0.66, 0.42), (0.72, 0.58), (0.66, 0.74), (0.5, 0.82), (0.34, 0.74), (0.28, 0.58), (0.34, 0.42)]
    pts = []
    for i in range(48):
        a = math.pi * 2 * i / 48
        x = 0.5 + 0.24 * math.cos(a)
        y = 0.62 + 0.22 * math.sin(a)
        if math.sin(a) < 0:
            k = (-math.sin(a))
            x = 0.5 + 0.24 * math.cos(a) * (1 - k ** 3 * 0.9)
            y = 0.62 + 0.22 * math.sin(a) - 0.12 * k ** 2
        pts.append((x, y))
    L.poly((255, 255, 255), pts, borde=(40, 90, 170), g=0.04)
    L.circ((190, 225, 255), (0.43, 0.68), 0.05, borde=None)


def _sim_viento(L):
    c = (255, 255, 255)
    b = (50, 110, 100)
    L.arco(b, (0.12, 0.28, 0.64, 0.3), math.pi * 0.0, math.pi * 1.0, 0.0)
    for P in ([(0.14, 0.36), (0.55, 0.36)], [(0.2, 0.52), (0.7, 0.52)], [(0.14, 0.68), (0.46, 0.68)]):
        pass
    # tres remolinos
    L.lineas(b, _curva(lambda u: (0.16 + 0.54 * u, 0.36 - 0.0 * u)), 0.12)
    L.arco(b, (0.5, 0.24, 0.28, 0.24), -math.pi / 2, math.pi * 0.9, 0.12)
    L.lineas(b, _curva(lambda u: (0.16 + 0.5 * u, 0.55)), 0.12)
    L.arco(b, (0.54, 0.43, 0.24, 0.24), -math.pi / 2, math.pi * 0.9, 0.12)
    L.lineas(b, _curva(lambda u: (0.24 + 0.32 * u, 0.74)), 0.12)
    L.arco(b, (0.5, 0.62, 0.2, 0.24), -math.pi / 2, math.pi * 0.9, 0.12)
    L.lineas(c, _curva(lambda u: (0.16 + 0.54 * u, 0.36)), 0.055)
    L.arco(c, (0.5, 0.24, 0.28, 0.24), -math.pi / 2, math.pi * 0.9, 0.055)
    L.lineas(c, _curva(lambda u: (0.16 + 0.5 * u, 0.55)), 0.055)
    L.arco(c, (0.54, 0.43, 0.24, 0.24), -math.pi / 2, math.pi * 0.9, 0.055)
    L.lineas(c, _curva(lambda u: (0.24 + 0.32 * u, 0.74)), 0.055)
    L.arco(c, (0.5, 0.62, 0.2, 0.24), -math.pi / 2, math.pi * 0.9, 0.055)


def _sim_fuego(L):
    ext = [(0.5, 0.1), (0.62, 0.3), (0.76, 0.48), (0.78, 0.66), (0.66, 0.84), (0.5, 0.9), (0.34, 0.84), (0.22, 0.66), (0.26, 0.5), (0.36, 0.38), (0.38, 0.5), (0.44, 0.34)]
    L.poly((255, 255, 255), ext, borde=(150, 40, 20), g=0.04)
    L.poly((255, 226, 120), [(0.5, 0.46), (0.6, 0.62), (0.58, 0.78), (0.5, 0.84), (0.42, 0.78), (0.4, 0.62)], borde=None)


def _sim_hielo(L):
    c = (255, 255, 255)
    b = (40, 90, 150)
    cen = (0.5, 0.5)
    for i in range(6):
        a = i * math.pi / 3 - math.pi / 2
        e = (0.5 + math.cos(a) * 0.3, 0.5 + math.sin(a) * 0.3)
        L.linea(b, cen, e, 0.12)
    for i in range(6):
        a = i * math.pi / 3 - math.pi / 2
        e = (0.5 + math.cos(a) * 0.3, 0.5 + math.sin(a) * 0.3)
        m = (0.5 + math.cos(a) * 0.19, 0.5 + math.sin(a) * 0.19)
        for s in (-1, 1):
            q = (m[0] + math.cos(a + s * 0.9) * 0.11, m[1] + math.sin(a + s * 0.9) * 0.11)
            L.linea(b, m, q, 0.1)
    for i in range(6):
        a = i * math.pi / 3 - math.pi / 2
        e = (0.5 + math.cos(a) * 0.3, 0.5 + math.sin(a) * 0.3)
        L.linea(c, cen, e, 0.06)
        m = (0.5 + math.cos(a) * 0.19, 0.5 + math.sin(a) * 0.19)
        for s in (-1, 1):
            q = (m[0] + math.cos(a + s * 0.9) * 0.11, m[1] + math.sin(a + s * 0.9) * 0.11)
            L.linea(c, m, q, 0.05)


def _sim_tierra(L):
    L.poly((255, 255, 255), [(0.1, 0.8), (0.36, 0.28), (0.5, 0.48), (0.64, 0.18), (0.92, 0.8)], borde=(80, 52, 30), g=0.045)
    L.poly((205, 170, 120), [(0.64, 0.18), (0.78, 0.46), (0.7, 0.42), (0.66, 0.5), (0.58, 0.42), (0.5, 0.48), (0.56, 0.36)], borde=None)
    L.poly((225, 232, 245), [(0.64, 0.18), (0.72, 0.32), (0.66, 0.3), (0.62, 0.36), (0.57, 0.3), (0.56, 0.32)], borde=None)


def _sim_electrico(L):
    P = [(0.58, 0.08), (0.24, 0.54), (0.46, 0.54), (0.38, 0.92), (0.78, 0.4), (0.54, 0.4), (0.7, 0.08)]
    L.poly((255, 255, 255), P, borde=(130, 90, 10), g=0.045)
    L.poly((255, 235, 140), [(0.58, 0.14), (0.34, 0.5), (0.5, 0.5), (0.46, 0.7), (0.66, 0.42), (0.48, 0.42), (0.6, 0.14)], borde=None)


_SIM = {"agua": _sim_agua, "viento": _sim_viento, "fuego": _sim_fuego, "hielo": _sim_hielo, "tierra": _sim_tierra, "electrico": _sim_electrico}
_cache_tipo = {}


def icono_tipo(tipo, r):
    r = max(6, int(r))
    key = (tipo, r)
    s = _cache_tipo.get(key)
    if s is None:
        tam = r * 2
        L = _L(tam)
        c = COLOR_TIPO.get(tipo, (150, 150, 160))
        L.circ(oscurecer(c, 0.22), (0.5, 0.5), 0.47, borde=None)
        # disco con degradado ligero (dos tonos)
        L.circ(c, (0.5, 0.48), 0.43, borde=None)
        L.circ(aclarar(c, 0.28), (0.5, 0.4), 0.3, borde=None)
        L.circ(c, (0.5, 0.52), 0.28, borde=None)
        L.circ(None, (0.5, 0.5), 0.47, borde=CONTORNO, g=0.045)
        _brillo_u(L, (0.34, 0.2), 0.12, 140)
        # simbolo: se dibuja en un sublienzo mas pequeno
        sub = _L(tam)
        fn = _SIM.get(tipo)
        if fn:
            fn(sub)
        simb = pygame.transform.smoothscale(sub.s, (int(sub.n * 0.64), int(sub.n * 0.64)))
        L.s.blit(simb, ((L.n - simb.get_width()) // 2, (L.n - simb.get_height()) // 2 + int(L.n * 0.01)))
        s = L.fin(tam)
        _cache_tipo[key] = s
    return s


def dibujar_icono_tipo(p, tipo, cx, cy, r):
    s = icono_tipo(tipo, r)
    p.blit(s, s.get_rect(center=(int(cx), int(cy))))


# ------------------------------------------------------------------ caca
_cache_caca = {}


def _caca_sprite(tam):
    s = _cache_caca.get(tam)
    if s is not None:
        return s
    L = _L(tam)
    marron = (150, 98, 56)
    # tres capas
    L.elip(oscurecer(marron, 0.15), (0.1, 0.62, 0.8, 0.32), g=0.045)
    L.elip(marron, (0.18, 0.42, 0.64, 0.3), g=0.045)
    L.elip(aclarar(marron, 0.08), (0.28, 0.24, 0.44, 0.26), g=0.045)
    # puntita
    L.poly(aclarar(marron, 0.08), [(0.42, 0.3), (0.5, 0.06), (0.62, 0.3)], g=0.045)
    L.poly(None, [(0.42, 0.3), (0.5, 0.06), (0.62, 0.3)], borde=None)
    # volver a rellenar uniones
    L.elip(aclarar(marron, 0.08), (0.3, 0.27, 0.4, 0.2), borde=None)
    L.arco(CONTORNO, (0.28, 0.24, 0.44, 0.26), math.pi * 0.0, math.pi * 1.0, 0.045)
    # brillo
    L.arco((200, 150, 100), (0.22, 0.46, 0.5, 0.22), math.pi * 0.62, math.pi * 0.98, 0.04)
    L.arco((200, 150, 100), (0.16, 0.66, 0.66, 0.24), math.pi * 0.72, math.pi * 0.98, 0.04)
    # carita
    L.circ((255, 255, 255), (0.4, 0.58), 0.065, g=0.025)
    L.circ((255, 255, 255), (0.62, 0.58), 0.065, g=0.025)
    L.circ(CONTORNO, (0.41, 0.59), 0.03, borde=None)
    L.circ(CONTORNO, (0.63, 0.59), 0.03, borde=None)
    L.arco(CONTORNO, (0.42, 0.62, 0.18, 0.16), math.pi * 1.05, math.pi * 1.95, 0.035)
    L.circ((255, 150, 160), (0.3, 0.7), 0.04, borde=None)
    L.circ((255, 150, 160), (0.72, 0.7), 0.04, borde=None)
    s = L.fin(tam)
    _cache_caca[tam] = s
    return s


def dibujar_caca(p, x, y, s=1.0, t=0.0):
    """(x,y) = centro del pie (base) de la caca."""
    tam = max(16, int(70 * s))
    spr = _caca_sprite(tam)
    bob = abs(math.sin(t * 3.0)) * 3 * s
    squash = 1 + math.sin(t * 6) * 0.03
    img = spr
    if abs(squash - 1) > 0.005:
        img = pygame.transform.smoothscale(spr, (int(tam * (2 - squash)), int(tam * squash)))
    rect = img.get_rect(midbottom=(int(x), int(y - bob + 2 * s)))
    from arte_tama_base import sombra
    sombra(p, x, y + 2 * s, tam * 0.85, tam * 0.2, 60)
    p.blit(img, rect)
    # moscas y brillo
    for i in range(2):
        a = t * (2.4 + i * 0.7) + i * 3
        fx = x + math.cos(a) * tam * 0.55
        fy = y - tam * (0.85 + 0.12 * math.sin(a * 1.7)) - bob
        pygame.draw.circle(p, CONTORNO, (int(fx), int(fy)), max(2, int(3 * s)))
        ala = max(2, int(3 * s))
        pygame.draw.ellipse(p, (230, 240, 255), (fx - ala, fy - ala * 1.6, ala, ala * 1.4))
        pygame.draw.ellipse(p, (230, 240, 255), (fx, fy - ala * 1.6, ala, ala * 1.4))
    from arte_tama_fx import destello_estrella
    k = (math.sin(t * 3.3) + 1) / 2
    destello_estrella(p, x + tam * 0.3, y - tam * 0.8 - bob, 9 * s + 4 * k * s, (255, 245, 190), k, 0)


# ------------------------------------------------------------------ nubes de estado
_NUBE_ICONO = {"hambre": "comer", "sueno": "dormir", "sueño": "dormir", "diversion": "jugar", "diversión": "jugar",
               "aburrido": "jugar", "limpieza": "limpiar", "suciedad": "limpiar", "salud": "curar", "enfermo": "curar",
               "energia": "dormir", "felicidad": "jugar"}
_cache_nube = {}


def _nube_base(w, h):
    key = (w, h)
    s = _cache_nube.get(key)
    if s is not None:
        return s
    n = SS
    S = pygame.Surface((w * n, h * n), pygame.SRCALPHA)
    cx, cy = w * n / 2, h * n * 0.5
    bolas = [(-0.30, 0.10, 0.28), (-0.10, -0.12, 0.34), (0.16, -0.08, 0.32), (0.34, 0.12, 0.26), (0.0, 0.16, 0.30), (-0.2, 0.2, 0.22), (0.2, 0.2, 0.22)]
    for g, col in ((int(5 * n), CONTORNO), (0, (255, 255, 255))):
        for bx, by, br in bolas:
            pygame.draw.circle(S, col, (cx + bx * w * n * 0.72, cy + by * h * n * 0.8), br * h * n * 0.78 + g)
    # sombreado inferior suave
    for bx, by, br in bolas[4:]:
        pass
    pygame.draw.ellipse(S, (222, 232, 248), (cx - w * n * 0.3, cy + h * n * 0.2, w * n * 0.6, h * n * 0.12))
    for bx, by, br in bolas:
        pygame.draw.circle(S, (255, 255, 255), (cx + bx * w * n * 0.72, cy + by * h * n * 0.8 - 2 * n), br * h * n * 0.78 - 3 * n)
    s = pygame.transform.smoothscale(S, (w, h))
    _cache_nube[key] = s
    return s


def dibujar_nube_estado(p, x, y, estado, t):
    """Burbuja de pensamiento; (x,y) = centro de la nube principal."""
    w, h = 110, 84
    bob = math.sin(t * 2.2) * 4
    k = 1 + math.sin(t * 3.1) * 0.02
    yy = y + bob
    # bolitas que conectan hacia abajo-izquierda
    for i, (dx, dy, r) in enumerate([(-34, 52, 7), (-46, 70, 4.5)]):
        yb = yy + dy + math.sin(t * 2.2 + i) * 1.5
        pygame.draw.circle(p, CONTORNO, (x + dx, yb), r + 3)
        pygame.draw.circle(p, (255, 255, 255), (x + dx, yb), r)
    base = _nube_base(w, h)
    if abs(k - 1) > 0.002:
        base = pygame.transform.smoothscale(base, (int(w * k), int(h * k)))
    p.blit(base, base.get_rect(center=(int(x), int(yy))))
    acc = _NUBE_ICONO.get(estado, "huevos")
    ic = icono_accion(acc, 46, True)
    esc = 1 + math.sin(t * 5) * 0.06
    if abs(esc - 1) > 0.01:
        ic = pygame.transform.smoothscale(ic, (int(46 * esc), int(46 * esc)))
    p.blit(ic, ic.get_rect(center=(int(x), int(yy - 2))))
    # signo de exclamacion suave de urgencia (pequenos destellos)
    a = (math.sin(t * 4) + 1) / 2
    for dx, dy in ((38, -26), (-40, -24)):
        r = 3 + 2 * a
        pygame.draw.circle(p, (255, 230, 120), (x + dx, yy + dy), r)
