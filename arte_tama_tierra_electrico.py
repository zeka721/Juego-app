"""Mascotas Tamagotchi de los tipos TIERRA (armadillo, topo, escarabajo) y ELECTRICO (raton, gato, rana), 4 etapas c/u.

DIBUJOS = {especie_id: fn(p, etapa, cx, cy, escala, t, estado, dir, silueta)}.  (cx, cy) = centro del cuerpo.
Altura con escala 1: 120 / 165 / 215 / 270 px segun la etapa.

Tecnica: cada (especie, etapa, escala) se dibuja UNA vez a un Surface (supermuestreo x2 + smoothscale = bordes suaves) y se
cachea; el cuadro a cuadro solo mezcla partes cacheadas (cola, alas...) con rotaciones baratas, aplasta/estira el sprite
(respirar, saltar, atacar...) y dibuja ojos/boca/efectos con arte_tama_base.  Primer dibujo de una forma ~50-150 ms
(usar precalentar() al cargar); despues <1 ms.
"""

import math

import pygame

from nucleo import aclarar, oscurecer
import arte_tama_base as B

HPX = (120, 165, 215, 270)       # altura en px con escala 1 por etapa
CW, CH = 176, 150                # lienzo en "unidades de diseno" (100 unidades = altura de la criatura)
PIV = 48.0                       # y (unidades) de los pies: pivote de aplastar/inclinar
_CACHE = {}


# ----------------------------------------------------------------------------------------------- utilidades
def mez(a, b, f):
    return tuple(int(a[i] * (1 - f) + b[i] * f) for i in range(3))


def bor(c):
    return mez(oscurecer(c, 0.62), B.CONTORNO, 0.45)


def suave(pts, it=3):
    for _ in range(it):
        n = len(pts)
        nu = []
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            nu.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            nu.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = nu
    return pts


def suave_ab(pts, it=3):
    for _ in range(it):
        nu = [pts[0]]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            nu.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            nu.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        nu.append(pts[-1])
        pts = nu
    return pts


def girar(pts, ang, ox=0.0, oy=0.0):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return [(ox + (x - ox) * c - (y - oy) * s, oy + (x - ox) * s + (y - oy) * c) for x, y in pts]


def elp(cx, cy, rx, ry, ang=0.0, n=44):
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return girar(pts, ang, cx, cy) if ang else pts


def _hash(n):
    v = math.sin(n * 127.1 + 311.7) * 43758.5453
    return v - math.floor(v)


# ----------------------------------------------------------------------------------------------- lienzo
class Lienzo:
    """Superficie de dibujo en unidades de diseno (origen = centro del lienzo)."""

    def __init__(self, k, raiz=None):
        self.k0 = k
        self.ss = 2 if k <= 3.0 else 1
        self.k = k * self.ss
        self.s = pygame.Surface((int(CW * self.k), int(CH * self.k)), pygame.SRCALPHA)
        self.raiz = raiz or self
        self.lista = []
        self.cara = None

    def P(self, x, y):
        return ((x + CW / 2) * self.k, (y + CH / 2) * self.k)

    def PP(self, pts):
        return [self.P(x, y) for x, y in pts]

    def forma(self, pts, col, gr=2.3, luz=True, brillo=False, borde=None, sombra=0.30):
        P = self.PP(pts)
        if luz:
            pygame.draw.polygon(self.s, mez(col, (20, 10, 40), sombra), P)
            xs = [q[0] for q in P]
            ys = [q[1] for q in P]
            mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            Q = [(mx + (x - mx) * 0.9 - w * 0.03, my + (y - my) * 0.9 - h * 0.045) for x, y in P]
            pygame.draw.polygon(self.s, col, Q)
            if brillo:
                pygame.draw.ellipse(self.s, aclarar(col, 0.42), (mx - w * 0.30, my - h * 0.36, w * 0.28, h * 0.15))
        else:
            pygame.draw.polygon(self.s, col, P)
        if gr > 0:
            b = borde or bor(col)
            lw = max(2, int(gr * self.k))
            pygame.draw.polygon(self.s, b, P, lw)
            if len(P) > 6:
                for q in P:
                    pygame.draw.circle(self.s, b, q, lw // 2)

    def el(self, cx, cy, rx, ry, col, ang=0.0, gr=2.3, luz=True, brillo=True, borde=None):
        self.forma(elp(cx, cy, rx, ry, ang), col, gr, luz, brillo, borde)

    def pl(self, pts, col, sua=0, gr=2.3, luz=True, brillo=False, borde=None):
        if sua:
            pts = suave(pts, sua)
        self.forma(pts, col, gr, luz, brillo, borde)

    def tubo(self, pts, w0, w1, col, gr=2.2, it=3, luz=True):
        path = suave_ab(pts, it) if it else list(pts)
        n = len(path)
        pasos = []
        for i in range(n - 1):
            a, b = path[i], path[i + 1]
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            m = max(1, int(d / 1.2))
            for j in range(m):
                f = (i + j / m) / (n - 1)
                pasos.append((a[0] + (b[0] - a[0]) * j / m, a[1] + (b[1] - a[1]) * j / m, (w0 + (w1 - w0) * f) / 2))
        f = 1.0
        pasos.append((path[-1][0], path[-1][1], w1 / 2))
        b = bor(col)
        for x, y, r in pasos:
            pygame.draw.circle(self.s, b, self.P(x, y), max(2, int((r + gr) * self.k)))
        sh = mez(col, (20, 10, 40), 0.28)
        for x, y, r in pasos:
            pygame.draw.circle(self.s, sh if luz else col, self.P(x, y), max(1, int(r * self.k)))
        if luz:
            for x, y, r in pasos:
                pygame.draw.circle(self.s, col, self.P(x - r * 0.12, y - r * 0.18), max(1, int(r * 0.82 * self.k)))
            for x, y, r in pasos[::3]:
                pygame.draw.circle(self.s, aclarar(col, 0.4), self.P(x - r * 0.35, y - r * 0.45), max(1, int(r * 0.22 * self.k)))

    def lin(self, pts, w, col, sua=0):
        if sua:
            pts = suave_ab(pts, sua)
        P = self.PP(pts)
        lw = max(1, int(w * self.k))
        if len(P) > 1:
            pygame.draw.lines(self.s, col, False, P, lw)
        for q in (P[0], P[-1]) if lw < 4 else P:
            pygame.draw.circle(self.s, col, q, max(1, lw // 2))

    def punto(self, x, y, r, col):
        pygame.draw.circle(self.s, col, self.P(x, y), max(1, int(r * self.k)))

    def parte(self, piv, amp, vel, fase=0.0, atras=True):
        h = Lienzo(self.k0, self.raiz)
        self.raiz.lista.append(dict(L=h, piv=piv, amp=amp, vel=vel, fase=fase, atras=atras))
        return h

    def cerrar(self):
        W, H = int(CW * self.k0), int(CH * self.k0)

        def red(s):
            return pygame.transform.smoothscale(s, (W, H)) if self.ss > 1 else s

        partes = []
        for d in self.lista:
            sf = red(d["L"].s)
            r = sf.get_bounding_rect(1)
            if r.w < 1 or r.h < 1:
                continue
            partes.append(dict(surf=sf.subsurface(r).copy(), pos=r.topleft,
                               piv=((d["piv"][0] + CW / 2) * self.k0, (d["piv"][1] + CH / 2) * self.k0),
                               amp=d["amp"], vel=d["vel"], fase=d["fase"], atras=d["atras"]))
        return dict(cuerpo=red(self.s), partes=partes, cara=self.cara, W=W, H=H, k=self.k0)


# ----------------------------------------------------------------------------------------------- formas utiles
def rayo(L, x, y, s, col, ang=0.0, gr=2.0, luz=False):
    pts = [(0.12, -1.0), (-0.55, 0.12), (-0.1, 0.12), (-0.3, 1.0), (0.55, -0.28), (0.08, -0.28), (0.45, -1.0)]
    pts = [(x + a * s, y + b * s) for a, b in pts]
    if ang:
        pts = girar(pts, ang, x, y)
    L.forma(pts, col, gr, luz)


def cristal(L, x, y, w, h, col, ang=0.0, gr=2.0):
    loc = [(0, -h), (w * 0.5, -h * 0.68), (w * 0.5, 0), (-w * 0.5, 0), (-w * 0.5, -h * 0.68)]
    pts = girar([(x + a, y + b) for a, b in loc], ang, x, y)
    L.forma(pts, col, gr, luz=False)
    fac = girar([(x + a, y + b) for a, b in
                 [(0, -h + 2.2), (-w * 0.5 + 1.3, -h * 0.68 + 0.6), (-w * 0.5 + 1.3, -1.5), (-w * 0.12, -1.5)]], ang, x, y)
    L.forma(fac, aclarar(col, 0.45), 0, luz=False)
    der = girar([(x + a, y + b) for a, b in [(0, -h + 2.2), (w * 0.5 - 1.3, -h * 0.68 + 0.6), (w * 0.5 - 1.3, -1.5), (w * 0.12, -1.5)]], ang, x, y)
    L.forma(der, mez(col, (30, 10, 50), 0.22), 0, luz=False)


def sol(L, cx, cy, Ro, Ri, n, col, ang0=0.0, gr=2.0, luz=True):
    pts = []
    for i in range(n * 2):
        r = Ro if i % 2 == 0 else Ri
        a = math.radians(ang0) + math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    L.forma(pts, col, gr, luz)


def garras(L, x, y, n, tam, ang0, abre, col):
    """n garras partiendo de (x,y), centro apuntando a ang0 (grados, 0 = abajo)."""
    for i in range(n):
        a = ang0 + (i - (n - 1) / 2) * abre
        loc = [(-tam * 0.32, 0), (0, tam), (tam * 0.32, 0)]
        pts = girar([(x + u, y + v) for u, v in loc], -a, x, y)
        L.forma(pts, col, 1.5, luz=False)


# ----------------------------------------------------------------------------------------------- ARMADILLO
def _armadillo(L, e):
    tan = (206, 146, 98)
    cre = (250, 228, 194)
    crs = (232, 196, 154)
    ros = (244, 170, 164)
    gris = (152, 152, 168)
    amb = (255, 198, 72)
    osc = mez(tan, (70, 30, 10), 0.42)
    rx = (46, 46, 47, 50)[e]
    ry = (44, 43, 40, 37)[e]
    c0 = (2, 3, 7, 10)[e]
    # cola
    cp = L.parte((rx - 12, c0 + 28), 9, 2.3, 0.6, True)
    cp.tubo([(rx - 12, c0 + 30), (rx + 6, c0 + 33), (rx + 20, c0 + 23), (rx + 23, c0 + 9)], (7, 8, 10, 12)[e], 3, tan)
    if e >= 2:
        for a in range(0, 360, 72):
            pts = girar([(rx + 23 - 3, c0 + 5), (rx + 23, c0 + 5 - 9 - e), (rx + 23 + 3, c0 + 5)], a + 20, rx + 23, c0 + 5)
            cp.forma(pts, gris, 1.4, luz=False)
        cp.el(rx + 23, c0 + 5, 5 + e, 5 + e, gris)
    # pies traseros
    for s in (-1, 1):
        L.el(s * 21, c0 + ry - 2, 12, 7, crs)
    # orejas
    for s in (-1, 1):
        if e == 0:
            L.el(s * 31, c0 - ry * 0.78, 9, 10.5, tan, ang=s * 25)
            L.el(s * 31, c0 - ry * 0.78 + 1, 5, 6.5, ros, ang=s * 25, gr=0, luz=False)
        else:
            h = (14, 17, 20)[e - 1]
            L.pl([(s * 20, c0 - ry * 0.92), (s * 37, c0 - ry - h), (s * 46, c0 - ry * 0.5)], tan, 2)
            L.pl([(s * 26, c0 - ry * 0.8), (s * 37, c0 - ry - h + 7), (s * 41, c0 - ry * 0.58)], ros, 2, gr=0, luz=False)
    if e >= 2:
        L.el(0, c0 - 3, rx + 3 * (e - 1), ry - 1, osc)
    # cuerpo y cara
    L.el(0, c0, rx, ry, cre)
    th = math.asin(10.0 / ry)
    xe = rx * math.cos(th)
    pts = []
    a0, a1 = math.pi - th, 2 * math.pi + th
    for i in range(23):
        a = a0 + (a1 - a0) * i / 22
        pts.append((rx * math.cos(a), c0 + ry * math.sin(a)))
    for i in range(13):
        x = xe - 2 * xe * i / 12
        pts.append((x, c0 - 12 + 22 * (x / xe) ** 2))
    L.pl(pts, tan, 0, luz=True)
    # bandas del caparazon
    nb = (2, 3, 4, 4)[e]
    for j in range(1, nb + 1):
        run = []
        runs = []
        for i in range(0, 25):
            x = -xe + 2 * xe * i / 24
            y = c0 - 12 + 22 * (x / xe) ** 2 - 10.5 * j
            u = (y - c0) / ry
            ok = u > -0.93 and abs(x) <= rx * math.sqrt(max(0.0, 1 - u * u)) * 0.93
            if ok:
                run.append((x, y))
            elif len(run) > 2:
                runs.append(run)
                run = []
            else:
                run = []
        if len(run) > 2:
            runs.append(run)
        for r in runs:
            L.lin([(x, y + 1.4) for x, y in r], 1.6, aclarar(tan, 0.30))
            L.lin(r, 2.0, osc)
    # nariz
    L.el(0, c0 + 13, 8.5 + e * 1.3, 6.0, (248, 206, 184), gr=1.8, brillo=False)
    L.el(0, c0 + 9.5, 3.4 + e * 0.3, 2.4, (140, 78, 84), gr=0, luz=False)
    # patas delanteras
    for s in (-1, 1):
        px, py = s * (rx - 9), c0 + 25
        if e >= 1:
            garras(L, px + s * 1, py + 4, 3 + (e >= 3), 5 + e * 1.8, s * 20, 28, (252, 242, 218))
        L.el(px, py, 7 + e * 1.8, 6.5 + e * 1.4, crs)
    # extras de evolucion
    if e >= 2:
        for j in range(1, nb):
            for x in (-26, -13, 0, 13, 26):
                y = c0 - 12 + 22 * (x / xe) ** 2 - 10.5 * j + 5
                u = (y - c0) / ry
                if u > -0.9 and abs(x) < rx * math.sqrt(max(0.0, 1 - u * u)) * 0.85:
                    L.el(x, y, 3.0 + e * 0.35, 2.6 + e * 0.3, gris, gr=1.4, brillo=False)
        L.forma([(0, c0 - 28), (6.5, c0 - 21), (0, c0 - 13), (-6.5, c0 - 21)], amb, 1.8, luz=False)
        L.forma([(0, c0 - 26), (-3, c0 - 21), (0, c0 - 20)], aclarar(amb, .6), 0, luz=False)
    if e >= 3:
        cristal(L, 0, c0 - ry + 7, 15, 30, amb)
        cristal(L, -15, c0 - ry + 8, 11, 21, amb, ang=-24)
        cristal(L, 15, c0 - ry + 8, 11, 21, amb, ang=24)
    L.cara = dict(ojos=(0, c0 + 3, 26, 6.6 + e * 0.3), boca=(0, c0 + 23, 11), mej=(0, c0 + 14, 40, 4.5, (255, 150, 150)))


# ----------------------------------------------------------------------------------------------- TOPO
def _topo(L, e):
    fur = (134, 102, 132)
    bel = (200, 170, 186)
    ros = (246, 156, 180)
    gar = (252, 234, 178)
    amb = (255, 196, 70)
    gris = (150, 150, 168)
    rx = (44, 45, 47, 50)[e]
    ry = (40, 40, 40, 38)[e]
    c0 = (6, 6, 7, 9)[e]
    if e >= 3:
        for s in (-1, 1):
            cristal(L, s * 34, c0 - 14, 12, 26, amb, ang=s * 38)
            cristal(L, s * 44, c0 - 2, 9, 18, aclarar(amb, .25), ang=s * 62)
    for s in (-1, 1):
        L.el(s * 19, c0 + ry - 2, 11, 7, mez(fur, (0, 0, 0), .15))
        L.el(s * 28, c0 - ry * 0.80, 8.5, 8, fur, ang=s * 20)
        L.el(s * 28, c0 - ry * 0.80 + 0.5, 4.8, 4.5, ros, gr=0, luz=False)
    L.el(0, c0, rx, ry, fur)
    L.el(0, c0 + 16, rx * 0.56, ry * 0.50, bel, gr=1.4, brillo=False)
    if e == 1:
        for dx, h in ((-8, 8), (0, 12), (8, 8)):
            L.pl([(dx - 4, c0 - ry + 3), (dx, c0 - ry - h), (dx + 4, c0 - ry + 3)], mez(fur, (0, 0, 0), .25), 1, gr=1.8, luz=False)
    # hocico y nariz
    L.el(0, c0 + 13, 16 + e, 10.5, bel, gr=2.0, brillo=False)
    L.el(0, c0 + 6.5, 7 + e * 0.5, 5, ros)
    L.punto(-2.2, c0 + 5, 1.5, aclarar(ros, .6))
    if e >= 1:
        for s in (-1, 1):
            for dy in (-2, 2):
                L.lin([(s * 12, c0 + 12 + dy), (s * (24 + e * 1.5), c0 + 10 + dy * 2.4)], 1.0, bor(fur))
    # manos excavadoras
    for s in (-1, 1):
        rxp, ryp = 9 + e * 2.6, 8 + e * 2.0
        px, py = s * (rx - 8), c0 + 24
        n = 3 + (e >= 2) + (e >= 3)
        garras(L, px + s * 2, py + ryp * 0.2, n, 8 + e * 4.2, s * 20, 30, gar)
        L.el(px, py, rxp, ryp, ros, ang=s * -10)
    # casco de minero
    if e >= 2:
        hy = c0 - ry + 12
        L.pl(elp(0, hy, 34, 26)[: 23] + [(34, hy), (-34, hy)][:0], amb, 0)
        L.pl([(x, y) for x, y in elp(0, hy, 33, 27, n=40) if y <= hy + 1] , amb, 0, luz=True, brillo=True)
        L.el(0, hy + 1.5, 38, 6.5, mez(amb, (180, 90, 20), .35))
        L.lin([(0, hy - 26), (0, hy - 8)], 3, mez(amb, (180, 90, 20), .4))
        L.el(0, hy - 6, 9, 8.5, gris, gr=1.8)
        L.el(0, hy - 6, 5.8, 5.4, (255, 250, 200), gr=0, luz=False)
    if e >= 3:
        cristal(L, 0, c0 - ry - 6, 11, 22, (255, 226, 120), ang=0)
        cristal(L, -13, c0 - ry - 3, 8, 15, (255, 226, 120), ang=-25)
        cristal(L, 13, c0 - ry - 3, 8, 15, (255, 226, 120), ang=25)
    L.cara = dict(ojos=(0, c0 - 5, 27, 6.0 + e * 0.2), boca=(0, c0 + 24, 12), mej=(0, c0 + 8, 44, 4.5, (255, 140, 160)))


# ----------------------------------------------------------------------------------------------- ESCARABAJO
def _escarabajo(L, e):
    ver = (92, 158, 96)
    cab = (74, 132, 88)
    amb = (246, 178, 64)
    pata = (52, 108, 76)
    ala = (226, 238, 250)
    sc = (12, 12, 12, 14)[e]
    shrx = (42, 43, 45, 47)[e]
    shry = (38, 37, 36, 35)[e]
    hc = (-12, -9, -5, -2)[e]
    hrx = (34, 32, 31, 30)[e]
    hry = (30, 28, 27, 26)[e]
    # alas
    if e >= 2:
        for s in (-1, 1):
            w = L.parte((s * 22, -6), s * -(4 + e * 2), 3.0 + e * 0.4, 0.0 if s > 0 else 1.2, True)
            big = 16 + (e - 2) * 12
            w.pl([(s * 22, -4), (s * (42 + big * 0.5), -22 - big * 0.35), (s * (58 + big), -12 - big * 0.4),
                  (s * (60 + big), 12), (s * 40, 24)], ala, 3)
            w.lin([(s * 28, 0), (s * (50 + big * .6), -8)], 1.2, (170, 190, 215))
            w.lin([(s * 30, 8), (s * (52 + big * .6), 6)], 1.2, (170, 190, 215))
    # patas
    ys = (24, 36) if e == 0 else (16, 28, 40)
    for s in (-1, 1):
        for y in ys:
            L.tubo([(s * 36, sc + y), (s * 47, sc + y + 2), (s * 50, sc + y + 9)], 8, 6, pata, it=2)
    # caparazon
    L.el(0, sc, shrx, shry, ver)
    L.lin([(0, sc - 12), (0, sc + shry - 2)], 2.2, mez(ver, (0, 20, 10), .55))
    L.el(-21, sc - 6, 6, 15, aclarar(ver, .38), ang=14, gr=0, luz=False)
    if e >= 1:
        for s in (-1, 1):
            for (x, y, r) in ((s * 24, sc + 6, 4.5), (s * 15, sc + 20, 4), (s * 30, sc + 22, 3.4)):
                L.el(x, y, r, r * 0.92, mez(ver, (10, 50, 40), .38), gr=0, luz=False)
    if e >= 2:
        for s in (-1, 1):
            pts = [(s * (shrx - 6) * math.cos(a), sc + (shry - 6) * math.sin(a)) for a in [math.radians(x) for x in range(15, 100, 10)]]
            L.lin(pts, 2.4, amb)
        L.forma([(0, sc + 17), (6, sc + 24), (0, sc + 31), (-6, sc + 24)], amb, 1.8, luz=False)
    if e >= 3:
        for s in (-1, 1):
            cristal(L, s * 30, sc - 14, 10, 18, (110, 220, 240), ang=s * 30)
            for ang in range(20, 90, 25):
                L.punto(s * (shrx - 5) * math.cos(math.radians(ang)), sc + (shry - 5) * math.sin(math.radians(ang)), 2.2, aclarar(amb, .5))
    # cabeza
    L.el(0, hc, hrx, hry, cab)
    L.el(-12, hc - 14, 8, 3.2, aclarar(cab, .35), gr=0, luz=False, ang=-15)
    # antenas
    if e >= 1:
        for s in (-1, 1):
            L.tubo([(s * 14, hc - hry + 4), (s * 20, hc - hry - 8), (s * 28, hc - hry - 12)], 3.2, 2.2, pata, it=2, luz=False)
            L.el(s * 29, hc - hry - 13, 3.8 + e * .4, 3.8 + e * .4, amb, gr=1.6)
    # cuerno
    top = hc - hry + 3
    if e == 0:
        L.pl([(-5, top + 3), (0, top - 11), (5, top + 3)], amb, 2)
    elif e == 1:
        L.tubo([(0, top + 3), (-1, top - 8), (7, top - 15)], 9, 3, amb, it=3)
    elif e == 2:
        L.tubo([(0, top + 3), (0, top - 12), (0, top - 22)], 11, 6, amb, it=2)
        L.tubo([(0, top - 17), (-9, top - 25), (-12, top - 31)], 6.5, 3, amb, it=2)
        L.tubo([(0, top - 17), (9, top - 25), (12, top - 31)], 6.5, 3, amb, it=2)
    else:
        L.tubo([(0, top + 3), (-2, top - 14), (4, top - 28), (3, top - 38)], 14, 6, amb, it=3)
        L.tubo([(4, top - 30), (-6, top - 38), (-10, top - 46)], 7, 2.6, amb, it=2)
        L.tubo([(4, top - 30), (14, top - 38), (17, top - 46)], 7, 2.6, amb, it=2)
        L.tubo([(-5, top + 5), (-16, top + 4), (-20, top - 4)], 6, 3, amb, it=2)
        L.tubo([(5, top + 5), (16, top + 4), (20, top - 4)], 6, 3, amb, it=2)
    if e >= 2:
        for s in (-1, 1):
            L.tubo([(s * 9, hc + hry - 4), (s * 14, hc + hry + 4), (s * 8, hc + hry + 9)], 5, 2.5, amb, it=2, luz=False)
    L.cara = dict(ojos=(0, hc + 1, 22, 6.6), boca=(0, hc + 14, 9), mej=(0, hc + 8, 34, 4, (255, 170, 120)))


# ----------------------------------------------------------------------------------------------- RATON
def _raton(L, e):
    am = (120, 188, 255)
    bel = (240, 250, 255)
    osc = (82, 140, 224)
    ama = (255, 222, 80)
    azul = (255, 222, 80)
    roj = (255, 222, 80)
    ros = (255, 176, 200)
    hy = (-10, -11, -13, -14)[e]       # centro de la cabeza
    by = (18, 19, 21, 22)[e]           # centro del cuerpo
    # cola de raton: larga y fina con rayo en la punta
    cp = L.parte((24, 44), 8, 2.6, 0.0, True)
    cp.tubo([(24, 44), (42, 50), (58, 42), (56, 28), (62, 18 - e * 3)][: 3 + min(e, 2)], 4.5 + e, 2.2, mez(am, (255, 255, 255), .0), it=3)
    rayo(cp, 61, 12 - e * 3, 6 + e * 2.5, ama, ang=12, gr=1.8)
    # aura de pelo erizado atras de la cabeza
    if e >= 3:
        sol(L, 0, hy + 6, 52, 38, 11, (226, 242, 255), ang0=8)
    # orejas
    for sg in (-1, 1):
        ec = (sg * (25 + e), hy - 27 - e * 0.5)
        ry = 13 + e * 1.4
        L.el(ec[0], ec[1], 11 + e * 0.8, ry, am, ang=sg * 20)
        L.el(ec[0] + sg * 0.5, ec[1] + 2, 6 + e * .4, ry * 0.62, ros, ang=sg * 20, gr=0, luz=False)
        tip = girar([(ec[0], ec[1] - ry * 0.52)], sg * 20, ec[0], ec[1])[0]
        L.el(tip[0], tip[1], 6.2 + e * .5, 5.0 + e * 0.4, osc if e < 2 else (70, 110, 230), ang=sg * 20, gr=0, luz=False)
    # pies, cuerpo
    for sg in (-1, 1):
        L.el(sg * 16, 46, 11, 6.5, osc)
    L.el(0, by, 29 + e * 0.8, 29 + e * 0.5, am)
    L.el(0, by + 5, 18 + e * 0.6, 21 + e * 0.5, bel, gr=1.4, brillo=False)
    if e >= 2:
        rayo(L, 0, by + 4, 9, azul, gr=1.6)
    # brazos
    for sg in (-1, 1):
        L.el(sg * (31 + e * 0.6), by - 2, 6 + e * 0.5, 9 + e * 0.8, am, ang=sg * -22)
        if e >= 2:
            L.el(sg * (32 + e * .8), by + 4, 6.5, 3.2, azul, ang=sg * -22, gr=1.2, luz=False)
    # cabeza
    L.el(0, hy, 38 + e * 0.5, 31 + e * 0.5, am)
    if e >= 2:
        for sg in (-1, 1):
            L.pl([(sg * 33, hy - 2), (sg * (50 + e), hy - 5), (sg * 41, hy + 5), (sg * (52 + e), hy + 10), (sg * 34, hy + 13)], am, 0, gr=2.0)
    if e >= 1:
        L.pl([(-6, hy - 28), (-3, hy - 40), (0, hy - 31), (4, hy - 43), (7, hy - 28)], am, 1, gr=1.8)
    if e >= 3:
        rayo(L, 0, hy - 44, 11, azul, gr=1.8)
    # mejillas electricas y nariz
    for sg in (-1, 1):
        L.el(sg * 27, hy + 8, 6.6 + e * 0.4, 6.2 + e * 0.4, roj, gr=1.6, brillo=False)
        L.punto(sg * 25, hy + 6, 1.8, aclarar(roj, .6))
        if e >= 1:
            rayo(L, sg * 27, hy + 8, 3.2 + e * .5, (60, 110, 230), gr=0, luz=False)
    L.el(0, hy + 5, 3.2, 2.5, (230, 110, 150), gr=1.2, luz=False)
    if e >= 3:
        for sg in (-1, 1):
            L.el(sg * 38, by + 14, 8, 8, am)
        L.el(0, by + 13, 10, 10, (255, 240, 150), gr=2.0)
        L.el(0, by + 13, 6, 6, (255, 255, 255), gr=0, luz=False)
    L.cara = dict(ojos=(0, hy - 2, 30, 7.4), boca=(0, hy + 13, 10), mej=None)


# ----------------------------------------------------------------------------------------------- GATO
def _gato(L, e):
    vio = (126, 110, 232)
    vio2 = (74, 58, 170)
    cre = (240, 232, 255)
    amar = (255, 228, 84)
    ros = (255, 170, 200)
    hy = (-10, -10, -9, -9)[e]
    by = (22, 22, 24, 25)[e]
    # cola
    cp = L.parte((26, 40), 7, 2.2, 0.0, True)
    cp.tubo([(26, 42), (46, 44), (58, 30), (54, 12 - e * 2)], 9 + e, 6, vio, it=3)
    rayo(cp, 54, 6 - e * 2, 5 + e * 2.6, amar, ang=15, gr=1.8)
    if e >= 3:
        sol(L, 0, hy + 2, 55, 40, 12, vio2, ang0=5)
        sol(L, 0, hy + 2, 49, 38, 12, (190, 175, 255), ang0=20)
    # orejas
    for s in (-1, 1):
        h = 20 + e * 3
        L.pl([(s * 14, hy - 26), (s * 33, hy - 29 - h), (s * 41, hy - 12)], vio, 2)
        L.pl([(s * 20, hy - 24), (s * 32, hy - 24 - h * 0.62), (s * 36, hy - 15)], ros, 2, gr=0, luz=False)
        if e >= 2:
            L.lin([(s * 32, hy - 29 - h), (s * 35, hy - 36 - h)], 2.6, vio2)
    # cuerpo y patas
    for s in (-1, 1):
        L.el(s * 16, 46, 11, 6.5, cre)
    L.el(0, by, 29 + e * 1.2, 27 + e * 0.8, vio)
    L.el(0, by + 6, 15, 18 + e, cre, gr=1.4, brillo=False)
    if e >= 1:
        for s in (-1, 1):
            for dy in (-6, 3, 12):
                L.lin([(s * (28 + e), by + dy), (s * (21 + e), by + dy + 2.5)], 2.6, vio2)
    if e >= 2:
        for s in (-1, 1):
            rayo(L, s * 20, by - 2, 8, amar, ang=s * 14, gr=1.4)
    for s in (-1, 1):
        L.el(s * (24 + e), by + 20, 8 + e * 0.6, 6, cre if e < 2 else vio, ang=s * 0)
    # cabeza
    L.el(0, hy, 39 + e, 32 + e * 0.5, vio)
    if e >= 2:
        for s in (-1, 1):
            L.pl([(s * 36, hy - 8), (s * 54, hy - 4), (s * 43, hy + 5), (s * 56, hy + 12), (s * 40, hy + 16), (s * 47, hy + 26), (s * 32, hy + 22)], cre, 0, gr=2.0)
    # marcas de la frente
    if e == 0:
        for dx in (-5, 0, 5):
            L.lin([(dx, hy - 30), (dx, hy - 22)], 2.6, vio2)
    else:
        for dx in (-12, 12):
            L.lin([(dx, hy - 30), (dx * 0.8, hy - 20)], 2.8, vio2)
        rayo(L, 0, hy - 24, 6 + e * 1.8, amar, gr=1.6)
    # hocico
    L.el(0, hy + 9, 17, 11, cre, gr=1.6, brillo=False)
    L.forma([(-3.5, hy + 3), (3.5, hy + 3), (0, hy + 7.5)], (240, 120, 150), 1.4, luz=False)
    for s in (-1, 1):
        n = 2 if e < 2 else 3
        for i in range(n):
            L.lin([(s * 14, hy + 8 + i * 2.5), (s * (30 + e * 3), hy + 4 + i * 5.5)], 1.0, vio2)
    L.cara = dict(ojos=(0, hy - 5, 31, 7.4), boca=(0, hy + 14.5, 9), mej=(0, hy + 7, 52, 4.2, (255, 150, 200)))


# ----------------------------------------------------------------------------------------------- RANA
def _rana(L, e):
    pie = (74, 212, 172)
    osc = (34, 150, 126)
    bel = (250, 242, 178)
    azul = (70, 140, 255)
    amar = (255, 226, 84)
    yo = (0, 0, 2, 6)[e]
    by = 12 + yo
    ey = -24 + yo
    if e >= 3:
        nube = (186, 204, 238)
        for (x, y, rx_, ry_) in ((-46, -14, 16, 12), (-34, -26, 18, 14), (-16, -30, 18, 14), (4, -33, 17, 13), (22, -30, 18, 14), (40, -22, 17, 13), (48, -8, 14, 11)):
            L.el(x, y + 8, rx_, ry_, nube, gr=2.0)
    # patas traseras
    for s in (-1, 1):
        r = 15 + e * 1.4
        L.el(s * 37, 33 + yo + e * 0.5, r, r * 0.76, pie, ang=s * -20)
        for i in range(3):
            L.el(s * (46 + i * 2.5 + e * .8), 44 + yo + e * 0.4 + (i - 1) * 3.4, 5.5, 3.8, pie, ang=s * (10 + i * 12), gr=1.8)
    # cuerpo
    L.el(0, by, 44 + e * 1.0, 36 + e * 0.4, pie)
    L.el(0, by + 11, 27 + e, 21 + e, bel, gr=1.4, brillo=False)
    # manchas
    for (x, y, r) in ((-24, by - 4, 4.4), (26, by - 8, 5), (-34, by + 8, 3.2), (14, by - 18, 3.6))[: 2 + e]:
        L.el(x, y, r, r * 0.85, osc, gr=0, luz=False)
    # bultos de ojos
    for s in (-1, 1):
        L.el(s * 21, ey, 15 + e * 0.6, 14 + e * 0.4, pie)
    # papo vocal
    if e >= 1:
        sac = (255, 230, 120) if e < 2 else azul
        L.el(0, by + 4 + e * 0.5, 8 + e * 1.8, 5 + e * 1.1, sac, gr=1.8)
    # comisuras y brazos
    for s in (-1, 1):
        L.lin([(s * 12, by - 17 + e), (s * 22, by - 18 + e), (s * 29, by - 24 + e)], 1.8, bor(pie), sua=2)
        L.el(s * 22, 41 + yo, 7, 7.5, pie, ang=s * 14)
        for i in range(3):
            L.el(s * 22 + (i - 1) * 4.5, 47 + yo, 2.5, 2.2, pie, gr=1.3, luz=False)
    if e >= 1:
        for s in (-1, 1):
            rayo(L, s * 33, by - 6, 4.8 + e * 1.4, amar, gr=1.2, ang=s * 10)
    if e >= 2:
        for s in (-1, 1):
            L.tubo([(s * 8, ey - 10), (s * 15, ey - 23), (s * 12, ey - 31)], 4, 2.5, pie, it=2, luz=False)
            L.el(s * 12, ey - 32, 3.6, 3.6, (255, 240, 120), gr=1.5)
    if e >= 3:
        rayo(L, 0, ey - 28, 15, amar, gr=2.0)
        rayo(L, -19, ey - 22, 10, amar, ang=-24, gr=1.8)
        rayo(L, 19, ey - 22, 10, amar, ang=24, gr=1.8)
        L.el(0, by + 12, 12, 8, (150, 220, 255), gr=0, luz=False)
    L.cara = dict(ojos=(0, ey + 1, 42, 7.2 + e * 0.2), boca=(0, by - 13, 12), mej=(0, by - 6, 62, 4, (255, 160, 120)))


_CONSTRUCTORES = {"armadillo": _armadillo, "topo": _topo, "escarabajo": _escarabajo,
                  "raton": _raton, "gato": _gato, "rana": _rana}

# ----------------------------------------------------------------------------------------------- estilo por especie
# tipo, color de chispas/aura, radios del efecto (unidades), parpadeo
_ESTILO = {
    "armadillo": dict(tipo="tierra", col=(255, 200, 90), rx=52, ry=42, fase=0.0),
    "topo": dict(tipo="tierra", col=(255, 200, 90), rx=54, ry=42, fase=0.7),
    "escarabajo": dict(tipo="tierra", col=(150, 235, 120), rx=56, ry=44, fase=1.3),
    "raton": dict(tipo="electrico", col=(255, 232, 90), rx=52, ry=44, fase=0.4),
    "gato": dict(tipo="electrico", col=(255, 232, 90), rx=54, ry=44, fase=1.0),
    "rana": dict(tipo="electrico", col=(140, 235, 255), rx=56, ry=42, fase=1.7),
}


# ----------------------------------------------------------------------------------------------- entrada de cache
_ALTO = {}


def _alto_unidades(esp, etapa):
    """Altura real (unidades de diseno) de la forma, para normalizar a HPX (los adornos suman altura)."""
    v = _ALTO.get((esp, etapa))
    if v is None:
        k = 0.7
        L = Lienzo(k)
        _CONSTRUCTORES[esp](L, etapa)
        e = L.cerrar()
        r = e["cuerpo"].get_bounding_rect(40)
        for d in e["partes"]:
            r = r.union(pygame.Rect(d["pos"], d["surf"].get_size()))
        v = r.h / k
        _ALTO[(esp, etapa)] = v
    return v


def _entrada(esp, etapa, k):
    key = (esp, etapa, round(k, 2))
    e = _CACHE.get(key)
    if e is None:
        kf = round(k * 100.0 / _alto_unidades(esp, etapa), 3)
        L = Lienzo(kf)
        _CONSTRUCTORES[esp](L, etapa)
        e = L.cerrar()
        e["scr"] = pygame.Surface((e["W"], e["H"]), pygame.SRCALPHA)
        e["sil"] = None
        e["glow"] = None
        _CACHE[key] = e
    return e


def _blit_parte(scr, d, ang):
    sf = d["surf"]
    if abs(ang) < 0.3:
        scr.blit(sf, d["pos"])
        return
    rot = pygame.transform.rotate(sf, ang)
    cxp = d["pos"][0] + sf.get_width() / 2 - d["piv"][0]
    cyp = d["pos"][1] + sf.get_height() / 2 - d["piv"][1]
    a = math.radians(ang)
    vx = cxp * math.cos(a) + cyp * math.sin(a)
    vy = -cxp * math.sin(a) + cyp * math.cos(a)
    scr.blit(rot, rot.get_rect(center=(d["piv"][0] + vx, d["piv"][1] + vy)))


def _componer(e, t, mult):
    scr = e["scr"]
    scr.fill((0, 0, 0, 0))
    for d in e["partes"]:
        _blit_parte(scr, d, d["amp"] * mult[0] * math.sin(t * d["vel"] * mult[1] + d["fase"]))
    scr.blit(e["cuerpo"], (0, 0))
    return scr


def _silueta(e):
    if e["sil"] is None:
        tmp = pygame.Surface((e["W"], e["H"]), pygame.SRCALPHA)
        for d in e["partes"]:
            if d["atras"]:
                tmp.blit(d["surf"], d["pos"])
        tmp.blit(e["cuerpo"], (0, 0))
        e["sil"] = B.silueta_de(tmp)
    return e["sil"]


def _glow(e, col, k, fuerza):
    if e["glow"] is None:
        r = int(78 * k)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        n = 22
        for i in range(n):
            f = i / n
            pygame.draw.circle(s, col + (int(150 * f ** 2.2),), (r, r), int(r * (1 - f)))
        e["glow"] = s
    return e["glow"]


# ----------------------------------------------------------------------------------------------- posturas por estado
def _postura(estado, t, etapa):
    r = math.sin(t * 2.2)
    d = dict(sx=1 - 0.013 * r, sy=1 + 0.024 * r, ang=math.sin(t * 1.1) * 0.8, dx=0.0, dy=0.0, flash=0, tint=None,
             cola=(1.0, 1.0), alto=0.0)
    if estado == "feliz":
        h = abs(math.sin(t * 4.6))
        d.update(dy=-14 * h, sy=1 + 0.06 * h - (0.07 if h < 0.12 else 0), sx=1 - 0.03 * h + (0.06 if h < 0.12 else 0),
                 ang=math.sin(t * 4.6) * 3.0, cola=(2.0, 1.8), alto=h)
    elif estado == "triste":
        d.update(sy=0.92 + 0.012 * r, sx=1.04, dy=2.5, ang=math.sin(t * 1.3) * 1.6 + 2.0, cola=(0.2, 0.6))
    elif estado == "hambre":
        d.update(sx=1 + 0.02 * math.sin(t * 6.0), sy=0.96 + 0.03 * math.sin(t * 3.0), ang=math.sin(t * 2.4) * 3.0, dy=1.5, cola=(0.5, 0.8))
    elif estado == "duerme":
        d.update(sy=0.93 + 0.035 * math.sin(t * 1.4), sx=1.04 - 0.02 * math.sin(t * 1.4), dy=3.0, ang=3.5, cola=(0.1, 0.4))
    elif estado == "enfermo":
        d.update(dx=math.sin(t * 31.0) * 0.9, sy=0.95 + 0.01 * r, sx=1.02, ang=math.sin(t * 1.6) * 2.4 - 2.0, tint=(176, 232, 160), cola=(0.2, 0.5), dy=1.5)
    elif estado == "come":
        c = math.sin(t * 9.0)
        d.update(sy=1 - 0.045 * abs(c), sx=1 + 0.03 * abs(c), dy=abs(c) * 1.2, ang=c * 1.8, cola=(1.4, 1.5))
    elif estado == "ataca":
        c = math.sin(t * 9.0)
        d.update(dx=9 + 6 * c, sx=1.06, sy=0.97, ang=-8 - 3 * c, cola=(2.2, 2.0))
    elif estado == "golpeado":
        d.update(dx=math.sin(t * 38.0) * 3.0 - 4.0, sy=1.04, sx=0.96, ang=7.0 + math.sin(t * 38.0) * 2.0, flash=70 if int(t * 12) % 2 == 0 else 0,
                 cola=(0.2, 0.3))
    elif estado == "evoluciona":
        h = 0.5 + 0.5 * math.sin(t * 7.0)
        d.update(sx=1.0 + 0.05 * h, sy=1.0 + 0.05 * h, flash=int(25 + 105 * h), cola=(1.0, 2.0))
    return d


# ----------------------------------------------------------------------------------------------- efectos
def _estrella(p, x, y, r, col, rot=0.0):
    pts = []
    for i in range(8):
        a = rot + math.pi * i / 4
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    pygame.draw.polygon(p, col, pts)


def _corazon(p, x, y, r, col):
    pygame.draw.circle(p, col, (int(x - r * 0.5), int(y - r * 0.3)), int(r * 0.58))
    pygame.draw.circle(p, col, (int(x + r * 0.5), int(y - r * 0.3)), int(r * 0.58))
    pygame.draw.polygon(p, col, [(x - r * 1.04, y - r * 0.05), (x + r * 1.04, y - r * 0.05), (x, y + r * 1.0)])


def _z(p, x, y, r, t_):
    pts = [(x - r, y - r), (x + r, y - r), (x - r, y + r), (x + r, y + r)]
    pygame.draw.lines(p, B.CONTORNO, False, pts, max(3, int(r * 0.7)))
    pygame.draw.lines(p, (225, 235, 255), False, pts, max(2, int(r * 0.4)))


def _chispas(p, cx, cy, k, t, n, col, rx, ry, largo, sem):
    for i in range(n):
        v = t * 1.7 + i / n + sem
        ph = v % 1.0
        if ph > 0.42:
            continue
        idx = int(v)
        h1, h2 = _hash(idx * 7 + i * 13 + sem * 50), _hash(idx * 3 + i * 5.1 + 9)
        a = h1 * 6.2832
        x0 = cx + math.cos(a) * rx * k * (0.8 + 0.3 * h2)
        y0 = cy + math.sin(a) * ry * k * (0.8 + 0.3 * h2)
        dx, dy = math.cos(a), math.sin(a)
        pts = [(x0, y0)]
        for j in range(1, 5):
            off = (h2 * 3 + j * 1.7) % 2 - 1
            pts.append((x0 + (dx * j * largo * 0.35 - dy * off * largo * 0.4) * k, y0 + (dy * j * largo * 0.35 + dx * off * largo * 0.4) * k))
        w = max(1, int(k * 1.8 * (1 - ph / 0.42) + 1))
        pygame.draw.lines(p, B.CONTORNO, False, pts, w + 2)
        pygame.draw.lines(p, col, False, pts, w + 1)
        pygame.draw.lines(p, (255, 255, 255), False, pts, max(1, w - 1))


def _guijarros(p, cx, cy, k, t, n, rx, ry, col):
    for i in range(n):
        a = t * 0.9 + i * 2 * math.pi / n
        x = cx + math.cos(a) * rx * k
        y = cy + (math.sin(a) * 0.3 * ry - 6) * k - (i % 2) * 10 * k
        r = (4.0 + (i % 3) * 1.6) * k
        pts = [(x + r * math.cos(j * 1.2566 + i), y + r * 0.8 * math.sin(j * 1.2566 + i)) for j in range(5)]
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, B.CONTORNO, pts, max(1, int(k * 1.2)))
        pygame.draw.circle(p, aclarar(col, .5), (int(x - r * 0.3), int(y - r * 0.3)), max(1, int(r * 0.25)))


def _polvo(p, cx, cy, k, t, n, col):
    for i in range(n):
        ph = (t * 0.8 + i / n) % 1.0
        x = cx + (math.sin(i * 12.3) * 40) * k
        y = cy - ph * 26 * k
        r = int((3 + 5 * ph) * k)
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col + (int(120 * (1 - ph)),), (r + 1, r + 1), r)
        p.blit(s, (x - r, y - r))


# ----------------------------------------------------------------------------------------------- dibujo principal
def _dibujar(esp, p, etapa, cx, cy, escala, t, estado, dir, silueta):
    etapa = max(0, min(3, int(etapa)))
    est = _ESTILO[esp]
    k = HPX[etapa] / 100.0 * escala
    e = _entrada(esp, etapa, k)
    k = e["k"]
    dr = 1 if dir >= 0 else -1
    st = _postura(estado, t, etapa)
    sx, sy, ang, dx, dy = st["sx"], st["sy"], st["ang"], st["dx"], st["dy"]

    # aura (adulto / ultimate)
    if etapa >= 2 and not silueta:
        g = _glow(e, est["col"], k, 1.0)
        pul = 0.55 + 0.25 * math.sin(t * 2.4)
        g.set_alpha(int(255 * pul * (0.55 if etapa == 2 else 1.0)))
        sc = 0.8 if etapa == 2 else 1.0
        gg = g if sc == 1.0 else pygame.transform.scale(g, (int(g.get_width() * sc), int(g.get_height() * sc)))
        p.blit(gg, gg.get_rect(center=(cx + dx * k * dr, cy + (PIV - 46 + dy) * k)))

    # sombra
    B.sombra(p, cx + dx * k * dr * 0.5, cy + (PIV + 1) * k, (66 + etapa * 8) * k * (1 - 0.25 * st["alto"]), alfa=80 - int(30 * st["alto"]))

    # sprite
    if silueta:
        spr = _silueta(e)
    else:
        spr = _componer(e, t, st["cola"])
        if st["tint"]:
            spr.fill(st["tint"] + (0,), special_flags=pygame.BLEND_RGB_MULT)
        if estado == "duerme":
            spr.fill((205, 205, 238, 0), special_flags=pygame.BLEND_RGB_MULT)
        if st["flash"]:
            f = st["flash"]
            spr.fill((f, f, f, 0) if estado == "evoluciona" else (f, f // 3, f // 3, 0), special_flags=pygame.BLEND_RGB_ADD)
    w, h = e["W"], e["H"]
    nw, nh = max(2, int(w * sx)), max(2, int(h * sy))
    if (nw, nh) != (w, h):
        spr = pygame.transform.scale(spr, (nw, nh))
    pvx, pvy = w / 2 * sx, (CH / 2 + PIV) * k * sy
    vx, vy = nw / 2 - pvx, nh / 2 - pvy
    if abs(ang) > 0.35:
        spr = pygame.transform.rotate(spr, ang)
        a = math.radians(ang)
        vx, vy = vx * math.cos(a) + vy * math.sin(a), -vx * math.sin(a) + vy * math.cos(a)
    if dr < 0:
        spr = pygame.transform.flip(spr, True, False)
    ox = dx * k + vx
    ox *= dr
    oy = (PIV + dy) * k + vy
    p.blit(spr, spr.get_rect(center=(int(cx + ox), int(cy + oy))))
    if silueta:
        return

    # transformacion local -> pantalla (para cara y efectos)
    ca = math.cos(math.radians(ang))
    sa = math.sin(math.radians(ang))

    def T(x, y):
        x1 = x * sx
        y1 = (y - PIV) * sy
        rx_ = x1 * ca + y1 * sa
        ry_ = -x1 * sa + y1 * ca
        return cx + (rx_ + dx) * k * dr, cy + (PIV + ry_ + dy) * k

    c = e["cara"]
    ex, ey, sep, er = c["ojos"]
    if estado == "triste":
        ey += 1.8
    elif estado == "duerme":
        ey += 1.0
    X, Y = T(ex, ey)
    ks = k * (sx + sy) / 2
    B.ojos(p, X, Y, sep * ks, er * ks, estado, t, dir=dr, fase=est["fase"])
    bx, by, bw = c["boca"]
    X2, Y2 = T(bx, by)
    B.boca(p, X2, Y2, bw * ks, estado, t)
    mj = c.get("mej")
    if mj is not None:
        mx, my, ms, mr, mc = mj
        X3, Y3 = T(mx, my)
        B.mejillas(p, X3, Y3, ms * ks, mr * ks * (1.25 if estado in ("feliz", "evoluciona") else 1.0), mc)
    elif estado in ("feliz", "evoluciona"):
        X3, Y3 = T(ex, ey + er * 1.9)
        B.mejillas(p, X3, Y3, sep * 1.15 * ks, er * 0.8 * ks, (255, 150, 160))

    # efectos del tipo
    cc = T(0, -4)
    tope = T(0, -48)
    if est["tipo"] == "electrico":
        n = (0, 2, 3, 5)[etapa] + (3 if estado in ("ataca", "evoluciona", "feliz") else 0) - (2 if estado in ("duerme", "triste") else 0)
        if estado == "enfermo":
            n = 1
        if n > 0:
            _chispas(p, cc[0], cc[1], k, t, n, est["col"], est["rx"], est["ry"], 8 + etapa * 2.5, est["fase"])
    else:
        if etapa >= 2:
            _guijarros(p, cc[0], cc[1], k, t, 3 if etapa == 2 else 5, est["rx"] + 8, est["ry"], (170, 150, 130) if esp != "escarabajo" else (150, 170, 120))
        if estado in ("ataca", "evoluciona", "feliz") or etapa >= 1:
            _polvo(p, cx, cy + (PIV - 2) * k, k, t, 2 + (2 if estado in ("ataca", "evoluciona") else etapa), (190, 160, 120))

    # iconos de estado
    hx, hy = T(ex, ey - 34)
    if estado == "duerme":
        for i in range(3):
            ph = (t * 0.5 + i / 3) % 1.0
            _z(p, hx + (22 + ph * 22) * k * dr, hy + 4 * k - ph * 30 * k, (4 + ph * 6) * k, 0)
    elif estado == "triste":
        for s in (-1, 1):
            ph = (t * 0.9 + (0 if s < 0 else 0.5)) % 1.0
            xx, yy = X + s * sep / 2 * ks, Y + er * ks * 1.3 + ph * 20 * ks
            pygame.draw.ellipse(p, (120, 190, 255), (xx - 2.5 * k, yy - 3.5 * k, 5 * k, 7 * k))
    elif estado == "enfermo":
        xx, yy = X + 28 * ks * dr, Y - 10 * ks + math.sin(t * 3) * 2 * ks
        pygame.draw.ellipse(p, (150, 220, 255), (xx - 3 * k, yy - 5 * k, 6 * k, 9 * k))
        pygame.draw.ellipse(p, B.CONTORNO, (xx - 3 * k, yy - 5 * k, 6 * k, 9 * k), max(1, int(k * 0.9)))
        for i in range(3):
            ph = (t * 0.7 + i / 3) % 1.0
            pygame.draw.circle(p, (150, 215, 120), (int(hx - 20 * k + i * 20 * k), int(hy + 14 * k - ph * 20 * k)), max(2, int((2 + 3 * (1 - ph)) * k)))
    elif estado == "feliz":
        for i in range(2):
            ph = (t * 0.9 + i * 0.5) % 1.0
            _corazon(p, hx + (-22 + i * 44) * k * 0.9, hy + 10 * k - ph * 30 * k, (4 + 3 * ph) * k, (255, 110, 150))
    elif estado == "hambre":
        pygame.draw.ellipse(p, (170, 225, 255), (X2 + bw * ks * 0.18, Y2 + bw * ks * 0.5 + abs(math.sin(t * 3)) * 6 * k, 4 * k, 7 * k))
        for i in range(2):
            a0 = math.sin(t * 8 + i) * 3 * k
            pygame.draw.arc(p, (255, 255, 255), (cx - 62 * k + a0, cy + 8 * k + i * 12 * k, 14 * k, 10 * k), 1.3, 4.5, max(2, int(k * 1.5)))
            pygame.draw.arc(p, (255, 255, 255), (cx + 48 * k - a0, cy + 8 * k + i * 12 * k, 14 * k, 10 * k), 4.7, 7.9, max(2, int(k * 1.5)))
    elif estado == "come":
        for i in range(4):
            ph = (t * 3.0 + i * 0.25) % 1.0
            ang2 = -1.2 + i * 0.8
            pygame.draw.circle(p, (255, 220, 150), (int(X2 + math.cos(ang2) * ph * 30 * k * dr), int(Y2 - math.sin(ang2 + 0.3) * ph * 18 * k + ph * ph * 20 * k)), max(1, int((2.4 - ph) * k)))
    elif estado == "ataca":
        for i in range(3):
            yy = cy + (-20 + i * 22) * k
            xx = cx - (50 + i * 6) * k * dr
            pygame.draw.line(p, (255, 255, 255), (xx, yy), (xx - 24 * k * dr, yy), max(2, int(2.4 * k)))
    elif estado == "golpeado":
        for i in range(3):
            a = t * 5 + i * 2.094
            _estrella(p, hx + math.cos(a) * 26 * k, hy + 14 * k + math.sin(a) * 6 * k, 5 * k, (255, 230, 90), a)
    elif estado == "evoluciona":
        for i in range(7):
            a = t * 2.0 + i * 0.9
            rr = (46 + 14 * math.sin(t * 3 + i)) * k
            _estrella(p, cc[0] + math.cos(a) * rr, cc[1] + math.sin(a) * rr * 0.9, (3 + 3 * abs(math.sin(t * 4 + i))) * k, (255, 255, 230), a)


def _fabrica(esp):
    def fn(p, etapa, cx, cy, escala=1.0, t=0.0, estado="normal", dir=1, silueta=False):
        _dibujar(esp, p, etapa, cx, cy, escala, t, estado, dir, silueta)
    fn.__name__ = "dibujar_" + esp
    return fn


DIBUJOS = {esp: _fabrica(esp) for esp in _CONSTRUCTORES}


def precalentar(escala=1.0):
    """Construye las 24 formas en cache (llamar al cargar la escena para evitar un tirón al primer dibujo)."""
    for esp in _CONSTRUCTORES:
        for et in range(4):
            _entrada(esp, et, HPX[et] / 100.0 * escala)
