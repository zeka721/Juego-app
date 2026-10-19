"""Arte Tamagotchi: especies de FUEGO (dragon, lobo, fenix) y HIELO (pinguino, oso, ciervo), 4 etapas cada una.
DIBUJOS = {especie_id: fn(p, etapa, cx, cy, escala, t, estado, dir, silueta)}.
(cx, cy) = centro del cuerpo; alto aprox 120/165/215/270 px con escala 1. Los cuerpos se renderizan una vez (supersampling x2)
y se cachean por (especie, etapa, escala redondeada); la animacion usa transformaciones baratas + llamas/destellos por cuadro."""

import math

import pygame

import arte_tama_base as B
from nucleo import aclarar, oscurecer

ALTO_ETAPA = (120, 165, 215, 270)
SS = 2
CW, CH, TOP = 220, 112, 40          # lienzo en unidades (figura de ~100 u de alto, pies en y~106; TOP = margen superior)

PAL = {
    "fuego": ((120, 30, 30), (255, 86, 44), (255, 170, 52), (255, 238, 150)),
    "sol": ((140, 70, 10), (255, 150, 30), (255, 214, 70), (255, 252, 214)),
}


# ------------------------------------------------------------------ utilidades geometricas
def _smooth(pts, closed=False, n=6):
    P = list(pts)
    m = len(P)
    out = []
    for i in (range(m) if closed else range(m - 1)):
        p0 = P[(i - 1) % m] if (closed or i > 0) else P[0]
        p1 = P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[-1]
        for j in range(n):
            u = j / n
            u2 = u * u
            u3 = u2 * u
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3) for k in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


def _rot(x, y, ang):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return x * ca - y * sa, x * sa + y * ca


def _plantilla():
    def loc(sw):
        return [(-1, 0), (-.95, -.3), (-.5 + sw * .3, -.7), (sw, -1), (.5 + sw * .4, -.66), (.95, -.28), (1, 0), (.6, .6), (0, .95), (-.6, .6)]
    a, b = _smooth(loc(0), True, 3), _smooth(loc(1), True, 3)
    return [(p[0], p[1], q[0] - p[0]) for p, q in zip(a, b)]


_TPL = _plantilla()
_CAPAS = ((1.0, 1.0), (.68, .82), (.38, .66))


def _llama(s, x, y, r, h, t, ph, pal, ang=0.0, sw=None, borde=True):
    """Llama en pixeles sobre la superficie s. Base en (x,y), punta hacia arriba (rotada 'ang' grados horario)."""
    cols = PAL[pal]
    if sw is None:
        sw = math.sin(t * 7.0 + ph) * r * 0.5
        h = h * (1 + 0.12 * math.sin(t * 9.5 + ph * 2))
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    for i, (k, hk) in enumerate(_CAPAS):
        rr, hh, ss = r * k, h * hk, sw * k
        pts = []
        for ux, uy, wx in _TPL:
            lx = ux * rr + wx * ss
            ly = uy * (hh if uy < 0 else rr)
            pts.append((x + lx * ca - ly * sa, y + lx * sa + ly * ca))
        pygame.draw.polygon(s, cols[i + 1], pts)
        if i == 0 and borde:
            pygame.draw.polygon(s, cols[0], pts, max(1, int(r * 0.16)))


def _estrella(s, x, y, r, col=(255, 255, 255)):
    if r < 1:
        return
    pts = [(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22), (x, y + r),
           (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)]
    pygame.draw.polygon(s, col, pts)


class Lienzo:
    def __init__(self, u, out):
        self.u = u
        self.f = u * SS
        self.s = pygame.Surface((int(CW * self.f), int((CH + TOP) * self.f)), pygame.SRCALPHA)
        self.lw = max(2.6 * SS, 1.25 * self.f)
        self.out = out

    def P(self, x, y):
        return ((x + CW / 2) * self.f, (y + TOP) * self.f)

    def _ep(self, x, y, rx, ry, ang=0.0, n=44):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        o = []
        for i in range(n):
            th = 2 * math.pi * i / n
            ex, ey = rx * math.cos(th), ry * math.sin(th)
            o.append(self.P(x + ex * ca - ey * sa, y + ex * sa + ey * ca))
        return o

    def ell(self, x, y, rx, ry, col, ang=0.0, sh=True, hl=True, ow=1.0):
        lw = self.lw * ow / self.f
        pygame.draw.polygon(self.s, self.out, self._ep(x, y, rx + lw / 2, ry + lw / 2, ang))
        if sh:
            pygame.draw.polygon(self.s, oscurecer(col, .26), self._ep(x, y, rx, ry, ang))
            pygame.draw.polygon(self.s, col, self._ep(x - rx * .05, y - ry * .09, rx * .95, ry * .9, ang))
            pygame.draw.polygon(self.s, aclarar(col, .13), self._ep(x - rx * .16, y - ry * .36, rx * .56, ry * .36, ang))
        else:
            pygame.draw.polygon(self.s, col, self._ep(x, y, rx, ry, ang))
        if hl:
            pygame.draw.polygon(self.s, aclarar(col, .72), self._ep(x - rx * .42, y - ry * .55, rx * .15, ry * .085, ang - 28, 20))

    def poly(self, pts, col, sh=True, ow=1.0, sm=False):
        if sm:
            pts = _smooth(pts, True, 5)
        P = [self.P(*q) for q in pts]
        lw = max(2, int(self.lw * ow))
        cx = sum(q[0] for q in pts) / len(pts)
        cy = sum(q[1] for q in pts) / len(pts)
        if sh:
            pygame.draw.polygon(self.s, oscurecer(col, .22), P)
            ins = [self.P(cx + (q[0] - cx) * .8 - 1.2, cy + (q[1] - cy) * .8 - 1.5) for q in pts]
            pygame.draw.polygon(self.s, col, ins)
        else:
            pygame.draw.polygon(self.s, col, P)
        pygame.draw.polygon(self.s, self.out, P, lw)
        if not sm:
            for q in P:
                pygame.draw.circle(self.s, self.out, q, lw // 2)

    def line(self, a, b, col, w=1.5):
        pygame.draw.line(self.s, col, self.P(*a), self.P(*b), max(1, int(w * self.f)))

    def tube(self, pts, r0, r1, col, bulge=0.0, hl=True):
        sp = _smooth(pts, False, 9)
        n = len(sp)
        rs = [r0 + (r1 - r0) * i / (n - 1) + bulge * math.sin(math.pi * i / (n - 1)) for i in range(n)]
        lw = self.lw / self.f
        for q, r in zip(sp, rs):
            pygame.draw.circle(self.s, self.out, self.P(*q), (r + lw / 2) * self.f)
        for q, r in zip(sp, rs):
            pygame.draw.circle(self.s, oscurecer(col, .2), self.P(*q), r * self.f)
        for q, r in zip(sp, rs):
            pygame.draw.circle(self.s, col, self.P(q[0] - r * .08, q[1] - r * .14), r * .86 * self.f)
        if hl:
            for q, r in zip(sp[::2], rs[::2]):
                pygame.draw.circle(self.s, aclarar(col, .16), self.P(q[0] - r * .2, q[1] - r * .38), r * .38 * self.f)

    def cone(self, x, y, tx, ty, wd, col, curve=0.0, sh=True):
        dx, dy = tx - x, ty - y
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        L, R = [], []
        for i in range(7):
            s = i / 6
            bend = curve * math.sin(math.pi * s)
            w = wd / 2 * (1 - s)
            L.append((x + dx * s + nx * (w + bend), y + dy * s + ny * (w + bend)))
            R.append((x + dx * s + nx * (-w + bend), y + dy * s + ny * (-w + bend)))
        self.poly(L + R[::-1][1:], col, sh=sh)

    def llama(self, x, y, r, h, pal="fuego", ang=0.0, sw=0.0):
        _llama(self.s, *self.P(x, y), r * self.f, h * self.f, 0, 0, pal, ang, sw=sw * self.f)

    def shard(self, x, y, w, h, ang, col, glow=True):
        """Cristal de hielo con base en (x,y) apuntando hacia 'arriba' rotado ang grados (horario)."""
        base = [(-w, 0), (-w * .85, -h * .55), (0, -h), (w * .85, -h * .55), (w, 0)]
        tr = lambda q: (x + _rot(q[0], q[1], ang)[0], y + _rot(q[0], q[1], ang)[1])
        izq = [tr(q) for q in [(-w, 0), (-w * .85, -h * .55), (0, -h), (0, 0)]]
        der = [tr(q) for q in [(0, 0), (0, -h), (w * .85, -h * .55), (w, 0)]]
        full = [tr(q) for q in base]
        pygame.draw.polygon(self.s, self.out, [self.P(*q) for q in full], int(self.lw * 1.7))
        pygame.draw.polygon(self.s, aclarar(col, .5), [self.P(*q) for q in izq])
        pygame.draw.polygon(self.s, col, [self.P(*q) for q in der])
        pygame.draw.polygon(self.s, self.out, [self.P(*q) for q in full], max(2, int(self.lw * .8)))
        self.line(tr((-w * .35, -h * .15)), tr((-w * .35, -h * .6)), (255, 255, 255), .9)
        self.line(tr((0, 0)), tr((0, -h)), oscurecer(col, .25), .5)

    def feather(self, x, y, ln, w, ang, col, col2=None):
        """Pluma: elipse alargada con base en (x,y) apuntando hacia arriba, rotada ang (horario)."""
        mx, my = _rot(0, -ln / 2, ang)
        self.ell(x + mx, y + my, w, ln / 2, col, ang, hl=False)
        if col2:
            ex, ey = _rot(0, -ln * .72, ang)
            self.ell(x + ex, y + ey, w * .6, ln * .24, col2, ang, sh=False, hl=False, ow=0.0001)


_AURAS = {}


def _aura(r, col):
    k = (int(r), col)
    s = _AURAS.get(k)
    if s is None:
        r = max(4, int(r))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(12, 0, -1):
            pygame.draw.circle(s, col + (int(5 + (12 - i) * 2.3),), (r, r), int(r * i / 12))
        _AURAS[k] = s
    return s


# ------------------------------------------------------------------ DRAGON
def _dragon(c, e):
    R, R2, CR, HORN, OR = (224, 70, 66), (246, 118, 72), (255, 230, 170), (255, 238, 178), (255, 170, 64)
    c.out = (98, 30, 46)
    cyh, rxh, ryh = (50, 45, 40, 35)[e], (33, 33, 32, 31)[e], (30, 29, 28, 27)[e]
    cyb, rxb, ryb = (86, 84, 81, 79)[e], (26, 29, 31, 33)[e], (20, 23, 26, 28)[e]
    fl, sp = [], []
    tl = (0, 6, 12, 18)[e]
    pts = [(rxb - 8, cyb + 8), (rxb + 12 + tl * .5, cyb + 14), (rxb + 22 + tl, cyb + 4 - e * 2), (rxb + 26 + tl * 1.4, cyb - 10 - e * 4)]
    c.tube(pts, 7 + e * .8, 2.5, R)
    if e >= 2:
        for i in range(1, 4):
            q = _smooth(pts, False, 9)[i * 8]
            c.cone(q[0] - 2, q[1] - 5, q[0] - 1, q[1] - 12 - e, 6, HORN, sh=False)
    fl.append((pts[-1][0], pts[-1][1] - 2, (4, 5.5, 7, 9)[e], (9, 12, 17, 22)[e], "fuego", 0.0, 10))
    if e >= 1:
        w, h = (0, 24, 38, 54)[e], (0, 24, 36, 48)[e]
        for sd in (-1, 1):
            x0, y0 = sd * (rxb - 6), cyb - 16
            loc = [(0, 0), (.22 * w, -.7 * h), (.7 * w, -h), (.62 * w, -.55 * h), (w, -.45 * h), (.7 * w, -.2 * h), (.82 * w, .1 * h), (.4 * w, .02 * h)]
            c.poly([(x0 + sd * a, y0 + b) for a, b in loc], OR if e < 3 else (255, 150, 60))
            c.line((x0, y0), (x0 + sd * .7 * w, y0 - h), R, 1.6)
            c.line((x0, y0 + 1), (x0 + sd * w, y0 - .45 * h), oscurecer(OR, .25), 1.0)
            if e == 3:
                fl.append((x0 + sd * .7 * w, y0 - h + 2, 4.5, 14, "fuego", 1.3 * sd, 8 * sd))
                fl.append((x0 + sd * w, y0 - .45 * h + 2, 3.8, 11, "fuego", 2.1 * sd, 18 * sd))
    for sd in (-1, 1):
        c.ell(sd * rxb * .5, 101, 11 + e * .6, 6.5, R, hl=False)
        for k in (-1, 0, 1):
            c.ell(sd * rxb * .5 + k * 4.4, 105.5, 2.2, 2, HORN, sh=False, hl=False, ow=.6)
    c.ell(0, cyb, rxb, ryb, R)
    c.ell(0, cyb + 3, rxb * .62, ryb * .82, CR, hl=False, ow=.55)
    if e >= 2:
        for i in range(3):
            y = cyb - ryb * .28 + i * ryb * .38
            c.line((-rxb * .45, y), (rxb * .45, y), oscurecer(CR, .25), .9)
    for sd in (-1, 1):
        c.ell(sd * (rxb - 1), cyb - 4, 6.5, 9, R, ang=sd * 14, hl=False)
        if e >= 1:
            for k in (-1, 0, 1):
                c.ell(sd * (rxb + 1.5) + k * 2.6 + sd * 1, cyb + 5, 1.7, 2.2, HORN, sh=False, hl=False, ow=.6)
    if e == 3:
        for sd in (-1, 1):
            c.ell(sd * (rxb - 4), cyb - 13, 7.5, 3.5, (255, 206, 80), ang=sd * -30, hl=False)
    # cuernos y cresta (detras de la cabeza)
    hl_ = (4, 8, 13, 19)[e]
    for sd in (-1, 1):
        c.cone(sd * rxh * .42, cyh - ryh * .8, sd * (rxh * .62 + e * 3), cyh - ryh - hl_, 11 + e * 1.5, HORN, curve=sd * 3)
    if e >= 2:
        for i, dx in enumerate((-9, 0, 9)):
            c.cone(dx, cyh - ryh * .96, dx * 1.3, cyh - ryh - 8 - (3 if dx == 0 else 0), 8, OR, sh=False)
    c.ell(0, cyh, rxh, ryh, R)
    if e >= 1:
        c.ell(0, cyh + ryh * .38, rxh * .56, ryh * .42, R2, hl=False, ow=.6)
        for sd in (-1, 1):
            c.ell(sd * 5.5, cyh + ryh * .28, 1.6, 1.2, oscurecer(R, .55), sh=False, hl=False, ow=.01)
    else:
        for sd in (-1, 1):
            c.ell(sd * 4, cyh + ryh * .3, 1.4, 1.1, oscurecer(R, .55), sh=False, hl=False, ow=.01)
    if e >= 2:
        for sd in (-1, 1):
            c.cone(sd * (rxh - 3), cyh + 5, sd * (rxh + 7), cyh + 1, 8, HORN, sh=False)
    if e == 3:
        for sd in (-1, 1):
            fl.append((sd * (rxh - 1), cyh - ryh * .5, 4.5, 15, "fuego", 0.7 * sd, 24 * sd))
        fl.append((0, cyh - ryh - 5, 4.5, 14, "sol", 0.2, 0))
    ey = cyh + ryh * .02
    return dict(eye=(0, ey, rxh * .95, 7.4 + e * .1), mouth=(0, cyh + ryh * (.62 if e else .52), 11), cheek=(0, ey + 10, rxh * 1.15, 4.2),
                ecol=(70, 40, 30), flames=fl, sparks=sp, head=(0, cyh - ryh - hl_), aura=(0, 60, 82, (255, 170, 80)) if e == 3 else None)


# ------------------------------------------------------------------ LOBO
def _lobo(c, e):
    F, F2, CR, EM, DK = (112, 92, 116), (150, 128, 152), (255, 234, 204), (255, 140, 50), (74, 60, 84)
    c.out = (44, 28, 54)
    cyh, rxh, ryh = (52, 47, 42, 37)[e], (33, 34, 34, 34)[e], (29, 28, 28, 27)[e]
    cyb, rxb, ryb = (86, 84, 80, 78)[e], (25, 28, 30, 32)[e], (20, 23, 27, 29)[e]
    fl, sp = [], []
    if e == 3:
        c.ell(0, cyh - 2, 49, 49, (255, 206, 80), sh=False, hl=False)
        c.ell(0, cyh - 2, 42, 42, (255, 240, 170), sh=False, hl=False, ow=.5)
        for i in range(12):
            a = math.radians(i * 30 + 15)
            c.cone(math.cos(a) * 46, cyh - 2 + math.sin(a) * 46, math.cos(a) * 62, cyh - 2 + math.sin(a) * 62, 9, (255, 206, 80), sh=False)
    # cola
    tp = [(rxb - 6, cyb + 6), (rxb + 14, cyb + 2), (rxb + 20 + e * 2, cyb - 14 - e * 3), (rxb + 14 + e * 3, cyb - 28 - e * 6)]
    c.tube(tp, 8 + e, 5 + e * .6, F, bulge=4 + e)
    c.tube(tp[1:], 5 + e * .6, 3 + e * .4, CR, hl=False) if False else None
    fl.append((tp[-1][0] + 1, tp[-1][1] - 3, (5, 6.5, 8, 11)[e], (11, 15, 21, 28)[e], "fuego", .5, 8))
    # patas y cuerpo
    c.ell(0, cyb, rxb, ryb, F)
    if e >= 1:
        for sd in (-1, 1):
            c.ell(sd * rxb * .78, cyb + 10, rxb * .38, ryb * .55, F2, hl=False)
    c.ell(0, cyb - 1, rxb * .55, ryb * .85, CR, hl=False, ow=.5)
    for sd in (-1, 1):
        c.ell(sd * rxb * .42, 101, 10.5 + e * .5, 6.8, F2, hl=False)
        for k in (-1, 1):
            c.line((sd * rxb * .42 + k * 2.6, 102.5), (sd * rxb * .42 + k * 2.6, 106), DK, .9)
        if e >= 2:
            c.ell(sd * rxb * .42, 104.5, 4.5, 2, EM, sh=False, hl=False, ow=.01)
    # melena de llamas (e>=2)
    if e >= 2:
        n = 5 if e == 2 else 7
        for i in range(n):
            a = math.pi * (1.1 + .8 * i / (n - 1))
            x, y = math.cos(a) * (rxh + 1), cyh + 6 + math.sin(a) * (ryh * .35) + ryh * .5 - 6
            c.poly([(x * .75, cyh + ryh * .65), (x * 1.18, y + 4 + e), (x * 1.0, y - 8 - e * 2), (x * .6, y + 2)], EM if i % 2 else (255, 190, 60), sh=False, ow=.7)
        if e == 3:
            for sd in (-1, 1):
                fl.append((sd * (rxh + 3), cyh + 8, 4.5, 13, "fuego", sd * .8, 40 * sd))
    if e == 3:
        c.ell(0, cyh + ryh + 1, 24, 6, (255, 206, 80), hl=False)
        c.ell(0, cyh + ryh + 4, 4.5, 4.5, (255, 90, 60), hl=False)
    # orejas
    eh = (14, 19, 23, 26)[e]
    for sd in (-1, 1):
        c.poly([(sd * (rxh * .28), cyh - ryh * .8), (sd * rxh * .98, cyh - ryh * .5), (sd * (rxh * .8 + e), cyh - ryh - eh)], F)
        c.poly([(sd * (rxh * .42), cyh - ryh * .75), (sd * rxh * .85, cyh - ryh * .52), (sd * (rxh * .76 + e), cyh - ryh - eh * .55)], (255, 170, 140), sh=False, ow=.01)
        if e >= 1:
            fl.append((sd * (rxh * .8 + e), cyh - ryh - eh + 3, (0, 3, 3.6, 4.4)[e], (0, 9, 12, 15)[e], "fuego", sd * .9, 6 * sd))
    c.ell(0, cyh, rxh, ryh, F)
    if e >= 1:
        for sd in (-1, 1):
            c.poly([(sd * (rxh - 3), cyh + 2), (sd * (rxh + 8), cyh + 11), (sd * (rxh - 5), cyh + ryh * .6)], F2, sh=False, ow=.7)
    c.ell(0, cyh + ryh * .4, rxh * .5, ryh * .4, CR, hl=False, ow=.6)
    c.ell(0, cyh + ryh * .22, 5.2, 3.6, DK, sh=False, hl=False, ow=.01)
    c.ell(-1.6, cyh + ryh * .17, 1.5, .9, (190, 180, 210), sh=False, hl=False, ow=.01)
    if e >= 1:
        # marca de brasa en la frente
        c.poly([(0, cyh - ryh * .86), (4, cyh - ryh * .5), (0, cyh - ryh * .22), (-4, cyh - ryh * .5)], EM, sh=False, ow=.6)
    if e == 3:
        c.poly([(0, cyh - ryh * .9), (4.5, cyh - ryh * .5), (0, cyh - ryh * .1), (-4.5, cyh - ryh * .5)], (255, 214, 70), sh=False, ow=.6)
    ey = cyh - 1
    return dict(eye=(0, ey, rxh * .86, 7.2), mouth=(0, cyh + ryh * .62, 9), cheek=(0, ey + 12, rxh * 1.12, 4.0), ecol=(226, 120, 28),
                flames=fl, sparks=sp, head=(0, cyh - ryh - eh), aura=(0, 56, 80, (255, 180, 90)) if e == 3 else None)


# ------------------------------------------------------------------ FENIX
def _fenix(c, e):
    G, O, RJ, CR, PICO = (255, 192, 58), (255, 130, 44), (226, 62, 52), (255, 238, 176), (255, 150, 40)
    c.out = (122, 42, 30)
    cyh, rxh, ryh = (54, 48, 43, 36)[e], (34, 33, 32, 30)[e], (31, 29, 28, 26)[e]
    cyb, rxb, ryb = (84, 82, 79, 77)[e], (30, 31, 31, 31)[e], (24, 26, 28, 29)[e]
    fl, sp = [], []
    # plumas de cola abanicadas detras
    if e >= 1:
        angs = {1: (-34, 0, 34), 2: (-58, -30, 0, 30, 58), 3: (-74, -50, -25, 0, 25, 50, 74)}[e]
        ln = (0, 24, 34, 44)[e]
        for i, a in enumerate(angs):
            col = (RJ, O, G)[min(2, abs(i - len(angs) // 2))] if e >= 2 else (O, G, O)[i]
            c.feather(0, cyb - 8, ln * (1 - abs(a) / 260), 5.2 + e, a, col, aclarar(col, .3))
            ex, ey2 = _rot(0, -ln * (1 - abs(a) / 260), a)
            if e >= 2 and abs(a) >= 48:
                fl.append((ex, cyb - 8 + ey2 + 2, 3.8 + e * .6, 9 + e * 2.5, "fuego", i * 1.1, a * .6))
    # alas
    for sd in (-1, 1):
        if e == 0:
            c.ell(sd * (rxb - 1), cyb - 2, 6, 9, O, ang=sd * 20, hl=False)
        elif e == 1:
            for k in range(3):
                c.feather(sd * (rxb - 6), cyb - 10, 26 - k * 3, 5, sd * (62 + k * 18), (O, RJ, RJ)[k] if k else O, None)
            c.ell(sd * (rxb - 2), cyb - 2, 8, 13, O, ang=sd * 14)
        else:
            n = 4 if e == 2 else 6
            ln = (0, 0, 32, 44)[e]
            for k in range(n):
                a = sd * (64 + k * (70 if e == 2 else 84) / n)
                col = RJ if k % 2 == 0 else O
                c.feather(sd * (rxb - 8), cyb - 12, ln - k * (2 if e == 2 else 1.5), 5 + e * .6, a, col, aclarar(col, .35))
                if e == 3 and k in (2, 5):
                    ex, ey2 = _rot(0, -(ln - k * 1.5), a)
                    fl.append((sd * (rxb - 8) + ex, cyb - 12 + ey2 + 1, 3.6, 10, "fuego", k + sd, a * .7))
            c.ell(sd * (rxb - 3), cyb - 4, 8.5, 14, O, ang=sd * 12)
    # patas
    for sd in (-1, 1):
        c.line((sd * 9, 99), (sd * 9, 104), PICO, 2.4)
        for k in (-1, 0, 1):
            c.line((sd * 9, 104), (sd * 9 + k * 5 + sd * 1, 106), PICO, 1.7)
    c.ell(0, cyb, rxb, ryb, G)
    c.ell(0, cyb + 4, rxb * .66, ryb * .8, CR, hl=False, ow=.5)
    if e >= 2:
        for i in range(3):
            c.line((-9 + i * 9, cyb + 2), (-9 + i * 9, cyb + 11), aclarar(O, .35), 1.2)
    if e == 3:
        c.ell(0, cyb + 3, 9, 9, (255, 214, 70), hl=False)
        c.ell(0, cyb + 3, 5, 5, (255, 100, 60), hl=False, ow=.5)
    # cresta
    n = (1, 3, 3, 5)[e]
    for i in range(n):
        o = i - (n - 1) / 2
        L = (9, 12, 15, 17)[e] * (1 - abs(o) * .18)
        c.cone(o * 6, cyh - ryh + 3, o * 9.5, cyh - ryh - L, 9 if e < 3 else 10, (RJ if i % 2 == 0 else O), curve=o * 2.5)
    fl.append((0, cyh - ryh - (9, 12, 15, 17)[e] + 2, (3, 4, 5, 6)[e], (7, 11, 15, 19)[e], "fuego", 0.4, 0))
    if e == 3:
        for sd in (-1, 1):
            fl.append((sd * 11, cyh - ryh - 10, 3.6, 11, "fuego", sd, 22 * sd))
        c.ell(0, cyh - ryh + 2, 14, 4, (255, 206, 80), hl=False)
    c.ell(0, cyh, rxh, ryh, G)
    c.ell(0, cyh + ryh * .3, rxh * .72, ryh * .58, CR, hl=False, ow=.01, sh=False)
    if e >= 2:
        for sd in (-1, 1):
            c.feather(sd * (rxh - 4), cyh + 4, 12, 3.4, sd * (150 - e * 10), O, None)
    by = cyh + ryh * .3
    bw = 6.2 + e * .4
    c.ell(0, by + 1, bw, 4.6, PICO, hl=False, ow=.8)
    c.line((-bw * .7, by + 1.4), (bw * .7, by + 1.4), oscurecer(PICO, .45), .5)
    ey = cyh - 1
    return dict(eye=(0, ey, rxh * .9, 7.0), pico=(0, by + 1, bw), cheek=(0, ey + 10, rxh * 1.12, 4.0), ecol=(60, 36, 30),
                flames=fl, sparks=sp, head=(0, cyh - ryh - (9, 12, 15, 19)[e]),
                aura=(0, 55, 85, (255, 190, 90)) if e == 3 else None)


# ------------------------------------------------------------------ PINGUINO
def _pinguino(c, e):
    NV, NV2, BL, ICE, PICO, ORA = (50, 84, 152), (78, 118, 190), (240, 251, 255), (156, 224, 255), (255, 176, 52), (255, 150, 40)
    c.out = (22, 36, 80)
    cyh, rx, ry = (52, 48, 43, 37)[e], (34, 35, 35, 35)[e], (31, 30, 30, 29)[e]
    cyb, rxb, ryb = (82, 80, 78, 76)[e], (31, 33, 34, 35)[e], (24, 27, 28, 30)[e]
    sp = []
    if e == 3:  # capa de cristales detras
        for i, a in enumerate((-86, -64, -42, 42, 64, 86)):
            c.shard(0, cyb - 2, 7, 50 - abs(a) * .1, a, ICE if i % 2 else aclarar(ICE, .2))
            ex, ey2 = _rot(0, -(50 - abs(a) * .1), a)
            sp.append((ex, cyb - 2 + ey2, 4.5, i * 1.3))
    if e >= 2:
        c.shard(-rxb + 3, cyb - 14, 6, 18, -50, ICE)
        c.shard(rxb - 3, cyb - 14, 6, 18, 50, ICE)
        sp.append((-rxb - 10, cyb - 26, 3.5, .5))
        sp.append((rxb + 10, cyb - 26, 3.5, 1.7))
    # aletas
    for sd in (-1, 1):
        L = (7, 11, 13, 15)[e]
        c.ell(sd * (rxb + 1), cyb - 2 + e, L * .55, L * 1.5, NV2, ang=sd * 22, hl=False)
    for sd in (-1, 1):
        c.ell(sd * 14, 103, 11.5, 5.2, ORA, hl=False)
    c.ell(0, cyb, rxb, ryb, NV)
    c.ell(0, cyb + 5, rxb * .74, ryb * .84, BL, hl=False, ow=.5)
    if e >= 2:
        c.shard(0, cyb + 14, 4.5, 13, 180, aclarar(ICE, .1), glow=False) if False else None
        c.poly([(0, cyb - 6), (5, cyb + 4), (0, cyb + 15), (-5, cyb + 4)], ICE, ow=.7)
        sp.append((0, cyb + 4, 3.5, 2.2))
    # copete / corona
    n = (0, 3, 5, 5)[e]
    for i in range(n):
        o = i - (n - 1) / 2
        L = ((12 - abs(o) * 2.4) if e == 1 else (15 - abs(o) * 2.6) + (4 if e == 3 else 0))
        c.shard(o * 6.4, cyh - ry + 5, 4.2 if e < 3 else 5, L, o * 17, ICE if e < 3 else aclarar(ICE, .15))
        if e >= 2 and i in (0, 4):
            sp.append((o * 6.4 + o * 5, cyh - ry - L + 4, 3.2, i))
    if e == 0:
        c.cone(0, cyh - ry + 3, 2, cyh - ry - 9, 6, NV, curve=2)
    c.ell(0, cyh, rx, ry, NV)
    # cara blanca
    c.ell(0, cyh + ry * .26, rx * .86, ry * .66, BL, hl=False, ow=.01, sh=False)
    if e == 3:
        for sd in (-1, 1):
            c.ell(sd * (rx - 6), cyh + 2, 5.5, 3.2, (255, 222, 120), ang=sd * -30, hl=False, ow=.7)
    if e >= 1:
        for sd in (-1, 1):
            c.ell(sd * (rx * .92), cyh - ry * .12, 5, 3, ICE, ang=sd * 30, hl=False, ow=.5) if False else None
    by = cyh + ry * .26
    c.ell(0, by + 3, 6.4 + e * .3, 4.2, PICO, hl=False, ow=.8)
    c.line((-4.2, by + 3.4), (4.2, by + 3.4), oscurecer(PICO, .45), .5)
    ey = cyh - 3
    return dict(eye=(0, ey, rx * .72, 6.8), pico=(0, by + 3, 6.4), cheek=(0, ey + 10, rx * .95, 4.0), ecol=(40, 40, 70),
                flames=[], sparks=sp, head=(0, cyh - ry - (6, 14, 18, 22)[e]),
                aura=(0, 56, 84, (150, 215, 255)) if e == 3 else None)


# ------------------------------------------------------------------ OSO POLAR
def _oso(c, e):
    W, W2, SH, ICE, NZ = (244, 249, 255), (226, 238, 252), (176, 202, 238), (150, 220, 255), (56, 66, 110)
    c.out = (52, 70, 130)
    cyh, rxh, ryh = (52, 47, 42, 37)[e], (34, 35, 36, 36)[e], (30, 29, 29, 28)[e]
    cyb, rxb, ryb = (86, 84, 81, 79)[e], (27, 30, 33, 35)[e], (21, 24, 27, 29)[e]
    sp = []
    if e == 3:
        # aurora detras (cinta ondulada)
        au = pygame.Surface(c.s.get_size(), pygame.SRCALPHA)
        for i, col in enumerate(((120, 255, 200), (110, 210, 255), (190, 150, 255))):
            pts = []
            for kk in range(25):
                a = math.pi * (1.02 + 0.96 * kk / 24)
                rad = 60 - i * 7 + 3 * math.sin(kk * .9 + i)
                pts.append(c.P(math.cos(a) * rad, 84 + math.sin(a) * (rad * .9)))
            pygame.draw.lines(au, col + (170,), False, pts, int(8 * c.f))
        c.s.blit(au, (0, 0))
        for i, a in enumerate((-84, -62, 62, 84)):
            c.shard(0, cyb - 4, 6, 40, a, ICE)
        sp.append((-52, 50, 4.2, .4))
        sp.append((52, 50, 4.2, 1.9))
    # piernas
    for sd in (-1, 1):
        c.ell(sd * rxb * .5, 100, 12.5 + e * .5, 7.6, W, hl=False)
        c.ell(sd * rxb * .5, 103, 5, 2.7, SH, sh=False, hl=False, ow=.01)
    # cuerpo
    c.ell(0, cyb, rxb, ryb, W)
    c.ell(0, cyb + 4, rxb * .6, ryb * .7, W2, sh=False, hl=False, ow=.01)
    # cola
    c.ell(rxb - 3, cyb + 12, 6, 5.5, W, hl=False)
    # brazos
    for sd in (-1, 1):
        c.ell(sd * (rxb + 1), cyb + 1, 7.5 + e * .5, 12 + e, W, ang=sd * 18, hl=False)
    # hombreras / cristales
    if e >= 2:
        for sd in (-1, 1):
            c.shard(sd * (rxb - 3), cyb - ryb * .6, 6 + (e - 2) * 2, 16 + (e - 2) * 6, sd * 40, ICE)
            c.shard(sd * (rxb - 12), cyb - ryb * .85, 4.5, 12 + (e - 2) * 4, sd * 14, aclarar(ICE, .2))
            sp.append((sd * (rxb + 8), cyb - ryb - 6 - (e - 2) * 4, 3.4, sd))
        c.poly([(0, cyb - 2), (5, cyb + 8), (0, cyb + 17), (-5, cyb + 8)], ICE, ow=.7)
    # bufanda (e>=1)
    if e >= 1:
        sc = (130, 190, 240)
        c.ell(0, cyh + ryh * .85, rxh * .72 + e * 2, 8, sc, hl=False)
        for k in range(-3, 4):
            c.line((k * 7, cyh + ryh * .85 - 6), (k * 7, cyh + ryh * .85 + 6), aclarar(sc, .5), .9) if e == 1 else None
        if e == 1:
            c.poly([(rxh * .35, cyh + ryh * .9), (rxh * .62, cyh + ryh * .8), (rxh * .74, cyh + ryh + 11), (rxh * .42, cyh + ryh + 9)], sc, ow=.8)
    # orejas
    for sd in (-1, 1):
        c.ell(sd * rxh * .7, cyh - ryh * .72, 10 + e * .4, 10 + e * .4, W)
        c.ell(sd * rxh * .7, cyh - ryh * .68, 5.6, 5.6, (190, 214, 250), sh=False, hl=False, ow=.01)
    if e == 3:
        for i, o in enumerate((-2, -1, 0, 1, 2)):
            c.shard(o * 8, cyh - ryh + 5, 5, 20 - abs(o) * 4, o * 16, ICE if i % 2 else aclarar(ICE, .2))
        sp.append((-16, cyh - ryh - 14, 3.4, 1.1))
        sp.append((17, cyh - ryh - 10, 3.0, 2.6))
    elif e == 2:
        c.shard(0, cyh - ryh + 5, 4.5, 14, 0, ICE)
        sp.append((0, cyh - ryh - 12, 3.2, .9))
    elif e == 1:
        c.shard(0, cyh - ryh + 5, 3.6, 9, 0, ICE)
    c.ell(0, cyh, rxh, ryh, W)
    c.ell(0, cyh + ryh * .38, rxh * .5, ryh * .4, (255, 255, 255), sh=False, hl=False, ow=.6)
    c.ell(0, cyh + ryh * .2, 6, 4.2, NZ, sh=False, hl=False, ow=.01)
    c.ell(-1.8, cyh + ryh * .13, 1.8, 1, (160, 170, 210), sh=False, hl=False, ow=.01)
    ey = cyh - 2
    return dict(eye=(0, ey, rxh * .84, 6.8), mouth=(0, cyh + ryh * .64, 9), cheek=(0, ey + 11, rxh * 1.1, 4.0), ecol=(40, 50, 100),
                flames=[], sparks=sp, head=(0, cyh - ryh - (4, 10, 14, 20)[e]),
                aura=(0, 56, 84, (150, 215, 255)) if e == 3 else None)


# ------------------------------------------------------------------ CIERVO
def _ciervo(c, e):
    F, CR, SPT, HOOF, ICE = (176, 206, 242), (238, 247, 255), (255, 255, 255), (74, 96, 160), (150, 222, 255)
    c.out = (48, 64, 128)
    cyh, rxh, ryh = (52, 47, 43, 40)[e], (29, 29, 29, 29)[e], (27, 26, 26, 26)[e]
    cyb, rxb, ryb = (84, 82, 78, 76)[e], (28, 30, 32, 34)[e], (19, 21, 24, 26)[e]
    sp = []
    if e == 3:
        for a in (-86, -66, 66, 86):
            c.shard(0, cyb - 6, 5.5, 36, a, aclarar(ICE, .15))
    # cola
    c.ell(rxb - 2, cyb - 2, 6, 5, CR, ang=-30, hl=False)
    # patas
    for sd in (-1, 1):
        c.ell(sd * rxb * .7, 94, 6.6, 12, F, hl=False)
        c.ell(sd * rxb * .7, 104, 7, 3.6, HOOF, hl=False, ow=.6)
        c.ell(sd * rxb * .28, 96, 6.6, 11, F, hl=False)
        c.ell(sd * rxb * .28, 104, 7, 3.6, HOOF, hl=False, ow=.6)
    c.ell(0, cyb, rxb, ryb, F)
    c.ell(0, cyb + 5, rxb * .62, ryb * .62, CR, sh=False, hl=False, ow=.01)
    if e <= 2:
        for (x, y) in ((-14, -9), (-5, -12), (6, -10), (15, -6), (-16, 0), (11, 2)) if e < 2 else ((-12, -10), (0, -12), (12, -9)):
            c.ell(x, cyb + y, 2.4, 2.1, SPT, sh=False, hl=False, ow=.01)
    # mechon del cuello
    if e >= 2:
        c.poly([(-12, cyh + 14), (-17, cyh + 28 + e), (-6, cyh + 24), (0, cyh + 34 + e), (6, cyh + 24), (17, cyh + 28 + e), (12, cyh + 14)], CR, sm=False, ow=.8)
    if e == 3:
        for sd in (-1, 1):
            c.shard(sd * 17, cyh + 22, 4.5, 14, sd * 70, ICE)
        c.shard(0, cyh + 28, 5, 16, 180, aclarar(ICE, .1))
        sp.append((0, cyh + 30, 3.4, .8))
    # astas
    def asta(sd):
        k = e
        base = (sd * rxh * .38, cyh - ryh * .75)
        Ls = (0, 12, 17, 22)[k]
        if k == 0:
            c.cone(base[0], base[1] + 3, sd * (rxh * .5), cyh - ryh - 7, 7, aclarar(ICE, .3), curve=sd)
            return
        pts = [base, (sd * (rxh * .5 + 2), cyh - ryh - Ls * .35), (sd * (rxh * .5 + Ls * .25), cyh - ryh - Ls * .8), (sd * (rxh * .45 + Ls * .1), cyh - ryh - Ls)]
        c.tube(pts, 3.4 + k * .4, 1.6, ICE if k < 3 else aclarar(ICE, .1), hl=False)
        tines = ((0.5, 36),) if k == 1 else (((.4, 46), (.75, 40)) if k == 2 else ((.3, 50), (.55, 44), (.8, 38)))
        for fr, ang in tines:
            q = _smooth(pts, False, 9)[int(fr * 27)]
            tx, ty = _rot(0, -(7 + k * 3), sd * ang)
            c.tube([q, (q[0] + tx * .5 + sd * 1, q[1] + ty * .5), (q[0] + tx + sd * 2, q[1] + ty)], 2.4 + k * .2, 1.2, ICE, hl=False)
        if k >= 2:
            c.shard(pts[-1][0], pts[-1][1] + 1, 3.6 + (k - 2) * 1.2, 11 + (k - 2) * 6, sd * 14, aclarar(ICE, .2))
            sp.append((pts[-1][0], pts[-1][1] - 11 - (k - 2) * 6, 3.4, sd + k))
    for sd in (-1, 1):
        asta(sd)
    # orejas
    for sd in (-1, 1):
        c.ell(sd * (rxh + 2), cyh - ryh * .35, 6.4, 12.5, F, ang=sd * 62, hl=False)
        c.ell(sd * (rxh + 2), cyh - ryh * .33, 3.3, 8, (206, 224, 250), ang=sd * 62, sh=False, hl=False, ow=.01)
    c.ell(0, cyh, rxh, ryh, F)
    c.ell(0, cyh + ryh * .42, rxh * .56, ryh * .46, CR, hl=False, ow=.6)
    c.ell(0, cyh + ryh * .28, 4.6, 3.2, HOOF, sh=False, hl=False, ow=.01)
    if e >= 2:
        c.poly([(0, cyh - ryh * .8), (3.2, cyh - ryh * .5), (0, cyh - ryh * .2), (-3.2, cyh - ryh * .5)], ICE if e == 2 else (200, 244, 255), sh=False, ow=.6)
        sp.append((0, cyh - ryh * .5, 3 + e - 2, 1.4))
    elif e == 1:
        for (x, y) in ((-10, -14), (8, -16), (0, -10)):
            c.ell(x, cyh + y, 2, 1.8, SPT, sh=False, hl=False, ow=.01)
    ey = cyh - 1
    return dict(eye=(0, ey, rxh * .86, 6.9), mouth=(0, cyh + ryh * .68, 8), cheek=(0, ey + 11, rxh * 1.1, 4.0), ecol=(60, 70, 130),
                flames=[], sparks=sp, head=(0, cyh - ryh - (8, 18, 27, 36)[e]),
                aura=(0, 56, 84, (150, 215, 255)) if e == 3 else None)


_DIB = {"dragon": _dragon, "lobo": _lobo, "fenix": _fenix, "pinguino": _pinguino, "oso": _oso, "ciervo": _ciervo}


# ------------------------------------------------------------------ cache y render
_CACHE = {}


def _construir(esp, e, esc_r, silueta):
    u = ALTO_ETAPA[e] * esc_r / 100.0
    c = Lienzo(u, B.CONTORNO)
    info = _DIB[esp](c, e)
    r = c.s.get_bounding_rect(1)
    k = ALTO_ETAPA[e] * esc_r / r.h
    w2, h2 = max(8, int(round(r.w * k))), max(8, int(round(ALTO_ETAPA[e] * esc_r)))
    img = pygame.transform.smoothscale(c.s.subsurface(r), (w2, h2))
    if silueta:
        img = B.silueta_de(img)
    return img, ((CW / 2 * c.f - r.x) * k, h2), info, c.f * k, r.bottom / c.f - TOP


def _obtener(esp, e, esc_r, silueta):
    k = (esp, e, esc_r, silueta)
    r = _CACHE.get(k)
    if r is None:
        if len(_CACHE) > 160:
            _CACHE.clear()
        r = _CACHE[k] = _construir(esp, e, esc_r, silueta)
    return r


_ROT = {}


def _rotada(esp, e, esc_r, sil, dr, qa, img, anc):
    """Imagen (volteada segun dir) rotada qa/2 grados (antihorario) alrededor de los pies; cacheada."""
    k = (esp, e, esc_r, sil, dr, qa)
    r = _ROT.get(k)
    if r is None:
        if len(_ROT) > 220:
            _ROT.clear()
        w, h = img.get_size()
        ax = anc[0]
        if dr < 0:
            img = pygame.transform.flip(img, True, False)
            ax = w - ax
        if qa:
            a = math.radians(qa / 2.0)
            img2 = pygame.transform.rotozoom(img, qa / 2.0, 1.0)
            vx, vy = ax - w / 2, anc[1] - h / 2
            r = (img2, (img2.get_width() / 2 + vx * math.cos(a) + vy * math.sin(a),
                        img2.get_height() / 2 - vx * math.sin(a) + vy * math.cos(a)))
        else:
            r = (img, (ax, anc[1]))
        _ROT[k] = r
    return r


def _pose(estado, t, dr, Hs):
    s = math.sin
    sx = sy = 1.0
    dx = dy = ang = 0.0
    tint = None
    if estado == "feliz":
        hop = abs(s(t * 5.5))
        dy = -hop * 0.09 * Hs
        sy = 1 + 0.06 * hop - 0.07 * (1 - hop) ** 4
        sx = 2 - sy if sy < 1 else 1 - 0.03 * hop
        ang = s(t * 5.5) * 3.5
    elif estado == "triste":
        sy, sx = 0.93 + 0.012 * s(t * 1.5), 1.03
        ang = 1.8 * s(t * 0.8)
    elif estado == "hambre":
        ang = 4.0 * s(t * 3.1)
        sy = 0.97 + 0.025 * s(t * 6)
        sx = 1.01
    elif estado == "duerme":
        ph = s(t * 1.2)
        sy, sx = 0.94 + 0.035 * ph, 1.03 - 0.02 * ph
        ang = 4.5 * dr
    elif estado == "enfermo":
        dx = s(t * 31) * 0.007 * Hs
        sy, sx = 0.95, 1.02
        ang = 2.5 * s(t * 2)
        tint = ("mult", (176, 232, 150))
    elif estado == "come":
        sy = 1 + 0.05 * s(t * 8)
        sx = 1 - 0.03 * s(t * 8)
        dy = -abs(s(t * 8)) * 0.012 * Hs
    elif estado == "ataca":
        l = max(0.0, s(t * 6))
        dx = dr * l * 0.17 * Hs
        ang = -dr * 10 * l
        sx, sy = 1 + 0.05 * l, 1 - 0.03 * l
    elif estado == "golpeado":
        dx = s(t * 38) * 0.035 * Hs
        ang = dr * (8 + 3 * s(t * 20))
        sy, sx = 0.96, 1.03
        tint = ("add", (90 + int(50 * s(t * 14)), 0, 0))
    elif estado == "evoluciona":
        pu = s(t * 9)
        sy, sx = 1 + 0.06 * pu, 1 - 0.03 * pu
        a = int(120 + 110 * (0.5 + 0.5 * pu))
        tint = ("add", (a, a, a))
    else:
        ph = s(t * 2.2)
        sy, sx = 1 + 0.028 * ph, 1 - 0.02 * ph
        dy = -0.01 * Hs * (ph + 1) / 2
    return sx, sy, dx, dy, ang, tint


def _extras(p, estado, t, hx, hy, q, dr, info):
    """Iconos de estado (screen px). (hx,hy) = punto sobre la cabeza, q = px por unidad."""
    if estado == "duerme":
        for i in range(3):
            ph = (t * 0.55 + i / 3) % 1
            x, y, r = hx + dr * (14 + ph * 30) * q, hy - 4 * q - ph * 46 * q, (4 + ph * 6) * q
            z = [(x - r, y - r), (x + r, y - r), (x - r, y + r), (x + r, y + r)]
            pygame.draw.lines(p, B.CONTORNO, False, z, max(3, int(r * .75)))
            pygame.draw.lines(p, (225, 238, 255), False, z, max(2, int(r * .4)))
    elif estado == "triste":
        for k in (-1, 1):
            ph = (t * 0.9 + (0.5 if k > 0 else 0)) % 1
            ex, ey = info["_ojos_px"]
            x, y = ex + k * info["_sep_px"] * 0.5, ey + (info["_r_px"] * 1.3 + ph * 18 * q)
            pygame.draw.ellipse(p, (130, 205, 255), (x - 2.5 * q, y - 3.5 * q, 5 * q, 7 * q))
            pygame.draw.ellipse(p, (255, 255, 255), (x - 1.2 * q, y - 2.4 * q, 1.6 * q, 2.6 * q))
    elif estado == "enfermo":
        x, y = hx + dr * 22 * q, hy + 14 * q + (t * 14 % 8) * q * .5
        pygame.draw.ellipse(p, B.CONTORNO, (x - 4.5 * q, y - 6 * q, 9 * q, 12 * q))
        pygame.draw.ellipse(p, (150, 215, 255), (x - 3.2 * q, y - 4.6 * q, 6.4 * q, 9.4 * q))
        for i in range(2):  # bichitos de fiebre
            a = t * 2 + i * 3.14
            pygame.draw.circle(p, (150, 200, 120), (int(hx + math.cos(a) * 30 * q), int(hy - 6 * q + math.sin(a) * 6 * q)), max(2, int(2.6 * q)))
    elif estado == "golpeado":
        for i in range(3):
            a = t * 5 + i * 2.1
            _estrella(p, hx + math.cos(a) * 26 * q, hy - 2 * q + math.sin(a) * 7 * q, 5 * q, (255, 230, 90))
    elif estado == "feliz":
        for i in range(2):
            ph = (t * 1.3 + i * .5) % 1
            x, y, r = hx + (-1 if i else 1) * (18 + ph * 10) * q, hy - ph * 30 * q, 5 * q * (1 - ph * .4)
            pygame.draw.circle(p, (255, 140, 170), (int(x - r * .5), int(y)), int(r * .6))
            pygame.draw.circle(p, (255, 140, 170), (int(x + r * .5), int(y)), int(r * .6))
            pygame.draw.polygon(p, (255, 140, 170), [(x - r * 1.05, y + r * .2), (x + r * 1.05, y + r * .2), (x, y + r * 1.4)])
    elif estado == "evoluciona":
        for i in range(5):
            a = t * 3 + i * 1.26
            _estrella(p, hx + math.cos(a) * 40 * q, hy + 40 * q + math.sin(a * 1.3) * 40 * q, (3 + 2 * math.sin(t * 8 + i)) * q, (255, 255, 220))
    elif estado == "ataca":
        for i in range(3):
            y = hy + (30 + i * 16) * q
            x = hx - dr * 40 * q
            pygame.draw.line(p, (255, 255, 255), (x, y), (x - dr * 22 * q, y), max(2, int(2 * q)))
    elif estado == "come":
        for i in range(3):
            ph = (t * 3 + i / 3) % 1
            pygame.draw.circle(p, (255, 210, 120), (int(hx + dr * (20 + ph * 14) * q), int(hy + (50 + ph * 26) * q)), max(1, int(2.2 * q * (1 - ph))))
    elif estado == "hambre":
        for i in range(2):
            ph = (t * 1.5 + i * .5) % 1
            x, y = hx + (-1 if i else 1) * 24 * q, hy + 30 * q - ph * 12 * q
            pygame.draw.lines(p, B.CONTORNO, False, [(x - 5 * q, y), (x, y - 4 * q), (x + 5 * q, y)], max(2, int(2 * q)))


def dibujar(esp, p, etapa, cx, cy, escala=1.0, t=0.0, estado="normal", dir=1, silueta=False):
    e = max(0, min(3, int(etapa)))
    escala = max(0.05, float(escala))
    esc_r = max(0.05, round(escala * 20) / 20)
    img, anc, info, q0, foot = _obtener(esp, e, esc_r, bool(silueta))
    dr = -1 if dir < 0 else 1
    ratio = escala / esc_r
    Hs = ALTO_ETAPA[e] * escala
    sx, sy, dx, dy, ang, tint = _pose(estado, t, dr, Hs)
    Sx, Sy = sx * ratio, sy * ratio
    qa = int(round(ang * 2))                      # angulo cuantizado a 0.5 grados (rotaciones cacheadas)
    ang = qa / 2.0
    img, anc = _rotada(esp, e, esc_r, bool(silueta), dr, qa, img, anc)
    w0, h0 = img.get_size()
    if abs(Sx - 1) > 0.003 or abs(Sy - 1) > 0.003:
        img = pygame.transform.smoothscale(img, (max(2, int(w0 * Sx)), max(2, int(h0 * Sy))))
        anc = (anc[0] * Sx, anc[1] * Sy)
    if tint and not silueta:
        img = img.copy()
        if tint[0] == "mult":
            img.fill(tint[1] + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            img.fill(tint[1], special_flags=pygame.BLEND_RGB_ADD)
    ax, ay = cx + dx, cy + Hs / 2 + dy
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    q = q0 * (Sx + Sy) / 2

    def tr(x, y):
        lx, ly = x * q0 * dr, (y - foot) * q0
        return ax + (lx * ca + ly * sa) * Sx, ay + (-lx * sa + ly * ca) * Sy

    if not silueta and info.get("aura") and estado != "duerme":
        axx, ayy, rr, col = info["aura"]
        sc = _aura(rr * q0 * ratio, col)
        sc.set_alpha(int(190 + 65 * math.sin(t * 2.4)))
        gx, gy = tr(axx, ayy)
        p.blit(sc, (gx - sc.get_width() / 2, gy - sc.get_height() / 2))
    p.blit(img, (ax - anc[0], ay - anc[1]))
    if silueta:
        return
    # llamas animadas (detras de la cara, delante del cuerpo)
    for (x, y, r, h, pal, ph, fa) in info["flames"]:
        fx, fy = tr(x, y)
        _llama(p, fx, fy, r * q, h * q * (0.8 if estado == "duerme" else 1.0), t, ph, pal, fa * dr + ang)
    for (x, y, r, ph) in info["sparks"]:
        k = max(0.0, math.sin(t * 3.2 + ph * 2.1))
        if k > 0.15:
            fx, fy = tr(x, y)
            _estrella(p, fx, fy, r * q * (0.4 + 1.1 * k), (255, 255, 255))
    # cara
    ex, ey, sep, er = info["eye"]
    X, Y = tr(ex + dr * 1.5 * 0, ey)
    sep_px, r_px = sep * q, max(2, er * q)
    info["_ojos_px"], info["_sep_px"], info["_r_px"] = (X, Y), sep_px, r_px
    if estado not in ("golpeado", "duerme") and info.get("cheek") and not silueta:
        mx, my, msep, mr = info["cheek"]
        MX, MY = tr(mx, my)
        B.mejillas(p, MX, MY, msep * q, mr * q, (255, 150, 160) if estado != "enfermo" else (170, 210, 150))
    B.ojos(p, X, Y, sep_px, r_px, estado, t, info["ecol"], dr, fase=hash(esp) % 7 * 0.37)
    if info.get("mouth"):
        bx, by, bw = info["mouth"]
        BX, BY = tr(bx, by)
        B.boca(p, BX, BY, bw * q, estado, t)
    elif info.get("pico"):
        bx, by, bw = info["pico"]
        BX, BY = tr(bx, by)
        w = bw * q
        if estado in ("hambre", "come", "ataca", "golpeado"):
            ab = w * (0.4 + 0.5 * abs(math.sin(t * 8))) if estado == "come" else w * 0.7
            pygame.draw.ellipse(p, (150, 50, 70), (BX - w * .55, BY - ab * .3, w * 1.1, ab))
            pygame.draw.ellipse(p, B.CONTORNO, (BX - w * .55, BY - ab * .3, w * 1.1, ab), max(2, int(w * .14)))
        elif estado in ("feliz", "evoluciona"):
            pygame.draw.arc(p, B.CONTORNO, (BX - w * .5, BY + w * .15, w, w * .6), math.pi, 2 * math.pi, max(2, int(w * .16)))
        elif estado in ("triste", "enfermo"):
            pygame.draw.arc(p, B.CONTORNO, (BX - w * .5, BY + w * .45, w, w * .6), 0, math.pi, max(2, int(w * .16)))
    hx, hy = tr(*info["head"])
    _extras(p, estado, t, hx, hy, q, dr, info)


def _mk(esp):
    def fn(p, etapa, cx, cy, escala=1.0, t=0.0, estado="normal", dir=1, silueta=False):
        dibujar(esp, p, etapa, cx, cy, escala, t, estado, dir, silueta)
    fn.__name__ = "dibujar_" + esp
    return fn


DIBUJOS = {esp: _mk(esp) for esp in _DIB}
