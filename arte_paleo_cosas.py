"""Herramientas de excavacion (4 tipos x 5 estrellas) y el carrito de mina."""

import math

import pygame

from nucleo import aclarar, oscurecer, estrella

BORDE = (50, 36, 30)

# estilos por estrellas: madera, metal (base, claro, oscuro), cuero, oro, gema
ESTILO = {
    1: dict(mad=(176, 118, 66), mad_o=(128, 82, 44), metal=(160, 164, 174), metal_l=(206, 210, 220), metal_d=(104, 110, 124),
            cuero=None, oro=None, gema=None, remaches=False, cerda=(226, 190, 124)),
    2: dict(mad=(158, 104, 58), mad_o=(112, 72, 40), metal=(174, 180, 192), metal_l=(224, 228, 238), metal_d=(110, 118, 134),
            cuero=(120, 74, 46), oro=None, gema=None, remaches=False, cerda=(232, 198, 134)),
    3: dict(mad=(124, 82, 54), mad_o=(86, 56, 38), metal=(118, 148, 196), metal_l=(188, 214, 246), metal_d=(66, 90, 140),
            cuero=(88, 58, 42), oro=None, gema=None, remaches=True, cerda=(240, 214, 150)),
    4: dict(mad=(98, 66, 48), mad_o=(66, 44, 34), metal=(186, 206, 234), metal_l=(244, 250, 255), metal_d=(104, 126, 170),
            cuero=(70, 46, 36), oro=(238, 192, 74), gema=None, remaches=True, cerda=(250, 232, 176)),
    5: dict(mad=(80, 52, 42), mad_o=(52, 34, 30), metal=(206, 226, 250), metal_l=(255, 255, 255), metal_d=(110, 140, 196),
            cuero=(58, 40, 36), oro=(252, 208, 84), gema=(104, 228, 238), remaches=True, cerda=(255, 240, 196)),
}


class _H:
    """Dibuja piezas en coordenadas locales (la punta en (0, 0), el mango hacia -y) rotadas `ang` grados."""

    def __init__(self, p, x, y, esc, ang):
        self.p, self.x, self.y, self.e = p, x, y, esc
        a = math.radians(ang)
        self.ca, self.sa = math.cos(a), math.sin(a)

    def q(self, u, v):
        return (self.x + (u * self.ca - v * self.sa) * self.e, self.y + (u * self.sa + v * self.ca) * self.e)

    def w(self, g):
        return max(1, int(g * self.e + 0.4))

    def poli(self, pts, col, borde=BORDE, g=2.0):
        P = [self.q(*a) for a in pts]
        pygame.draw.polygon(self.p, col, P)
        if borde:
            pygame.draw.polygon(self.p, borde, P, self.w(g))

    def lin(self, a, b, col, g=2.0):
        pygame.draw.line(self.p, col, self.q(*a), self.q(*b), self.w(g))

    def circ(self, c, r, col, borde=BORDE, g=1.6):
        P = self.q(*c)
        pygame.draw.circle(self.p, col, (int(P[0]), int(P[1])), max(1, int(r * self.e)))
        if borde:
            pygame.draw.circle(self.p, borde, (int(P[0]), int(P[1])), max(1, int(r * self.e)), self.w(g))

    def chispa(self, c, r, col=(255, 255, 255)):
        P = self.q(*c)
        pts = []
        for i in range(8):
            a = -math.pi / 2 + i * math.pi / 4
            rr = r * self.e if i % 2 == 0 else r * self.e * 0.28
            pts.append((P[0] + rr * math.cos(a), P[1] + rr * math.sin(a)))
        pygame.draw.polygon(self.p, col, pts)

    def barra(self, y0, y1, w0, w1, col, claro, oscuro, borde=BORDE):
        """Pieza cilindrica entre dos alturas con luz a la izquierda y sombra a la derecha."""
        self.poli([(-w0, y0), (w0, y0), (w1, y1), (-w1, y1)], col, borde)
        self.poli([(-w0 * 0.78, y0), (-w0 * 0.36, y0), (-w1 * 0.36, y1), (-w1 * 0.78, y1)], claro, None)
        self.poli([(w0 * 0.55, y0), (w0, y0), (w1, y1), (w1 * 0.55, y1)], oscuro, None)
        self.poli([(-w0, y0), (w0, y0), (w1, y1), (-w1, y1)], None, borde, 2.0) if False else None
        P = [self.q(-w0, y0), self.q(w0, y0), self.q(w1, y1), self.q(-w1, y1)]
        pygame.draw.polygon(self.p, borde, P, self.w(2.0))

    def banda(self, y, ancho, col, g=4.0):
        self.poli([(-ancho, y - g / 2), (ancho, y - g / 2), (ancho, y + g / 2), (-ancho, y + g / 2)], col, BORDE, 1.4)


def _mango(h, est, y0, y1, w0, w1):
    st = ESTILO[est]
    h.barra(y0, y1, w0, w1, st["mad"], aclarar(st["mad"], 0.22), st["mad_o"])
    n = 3 if est >= 2 else 0
    if st["cuero"]:
        if est >= 3:
            largo = y0 - y1
            for k in range(int(largo / 7)):
                yy = y0 - 4 - k * 7
                ww = w0 + (w1 - w0) * ((y0 - yy) / largo)
                h.lin((-ww, yy), (ww, yy - 5), st["cuero"], 3.0)
        else:
            for yy in (y0 - (y0 - y1) * 0.32, y0 - (y0 - y1) * 0.5):
                ww = w0 + (w1 - w0) * ((y0 - yy) / (y0 - y1))
                h.banda(yy, ww + 0.6, st["cuero"], 4.0)
    if st["oro"]:
        h.banda(y0 - 1.5, w0 + 1.4, st["oro"], 4.5)
        h.banda(y1 + 1.5, w1 + 1.4, st["oro"], 4.5)


def _remate(h, est, y, w):
    """Tapa del extremo del mango."""
    st = ESTILO[est]
    col = st["oro"] if st["oro"] else st["metal"]
    h.poli([(-w, y), (w, y), (w - 2, y - 7), (-w + 2, y - 7)], col, BORDE, 2.0)
    h.lin((-w + 2, y - 1.5), (w - 3, y - 1.5), aclarar(col, 0.5), 1.8)
    if st["gema"]:
        h.circ((0, y - 11), 6.5, st["gema"], (30, 90, 110), 1.8)
        h.circ((-2, y - 13), 2.2, (255, 255, 255), None)
        h.chispa((9, y - 20), 6)
    elif est == 1:
        pass


def _cabeza_metal(h, est, pts, base=None):
    st = ESTILO[est]
    h.poli(pts, base or st["metal"])


def herr_brocha(h, est):
    st = ESTILO[est]
    h.poli([(-15, 0), (15, 0), (12, -28), (-12, -28)], st["cerda"], (130, 90, 50))
    for u in (-9, -4.5, 0, 4.5, 9):
        h.lin((u, -2), (u * 0.82, -26), oscurecer(st["cerda"], 0.2), 1.8)
    if est >= 3:
        h.poli([(-15, 0), (15, 0), (13, -6), (-13, -6)], aclarar(st["cerda"], 0.3), None)
    h.barra(-28, -43, 12, 10.5, st["metal"], st["metal_l"], st["metal_d"])
    if st["remaches"]:
        h.circ((-5, -35.5), 1.4, st["metal_l"], None)
        h.circ((5, -35.5), 1.4, st["metal_d"], None)
    if st["oro"]:
        h.banda(-31, 12.6, st["oro"], 3.4)
        h.banda(-40, 11, st["oro"], 3.4)
    _mango(h, est, -43, -90, 5.4, 3.8)
    _remate(h, est, -90, 4.6)


def herr_martillo(h, est):
    st = ESTILO[est]
    _mango(h, est, -26, -90, 5.4, 4.2)
    _remate(h, est, -90, 5.0)
    h.poli([(-27, 0), (27, 0), (27, -29), (-27, -29)], st["metal"])
    h.poli([(-24, -2), (24, -2), (24, -12), (-24, -12)], st["metal_l"], None)
    h.poli([(-27, -22), (27, -22), (27, -29), (-27, -29)], st["metal_d"], None)
    h.poli([(-27, 0), (-21, 0), (-21, -29), (-27, -29)], st["metal_d"], BORDE, 1.6)
    h.poli([(21, 0), (27, 0), (27, -29), (21, -29)], st["metal_d"], BORDE, 1.6)
    pts = [h.q(-27, 0), h.q(27, 0), h.q(27, -29), h.q(-27, -29)]
    pygame.draw.polygon(h.p, BORDE, pts, h.w(2.2))
    if st["remaches"]:
        for u in (-15, 15):
            h.circ((u, -14), 2.0, st["metal_l"], BORDE, 1.0)
    if st["oro"]:
        h.banda(-4, 27.5, st["oro"], 3.4)
        h.banda(-25, 27.5, st["oro"], 3.4)
    if st["gema"]:
        h.poli([(0, -21), (7, -14.5), (0, -8), (-7, -14.5)], st["gema"], (30, 90, 110), 1.8)
        h.lin((-3, -16), (0, -19), (255, 255, 255), 1.6)
        h.chispa((20, -34), 6)
    h.barra(-29, -33, 6.4, 5.8, st["metal"], st["metal_l"], st["metal_d"])


def herr_cincel(h, est):
    st = ESTILO[est]
    h.poli([(0, 0), (-9, -30), (9, -30)], st["metal_l"] if est >= 3 else aclarar(st["metal"], 0.2))
    h.poli([(0, 0), (9, -30), (3, -30)], st["metal_d"], None)
    h.barra(-30, -60, 9.4, 8.6, st["metal"], st["metal_l"], st["metal_d"])
    if est >= 3:
        h.lin((-1, -34), (-1, -57), st["metal_d"], 1.6)
    if st["oro"]:
        h.banda(-60, 11.5, st["oro"], 5.0)
    else:
        h.banda(-60, 11.5, st["metal_d"], 5.0)
    _mango(h, est, -62, -92, 7.8, 7.2)
    h.poli([(-11, -92), (11, -92), (9, -101), (-9, -101)], st["oro"] if st["oro"] else st["metal"], BORDE, 2.0)
    h.lin((-8, -94), (8, -94), aclarar(st["oro"] or st["metal"], 0.5), 1.8)
    if st["gema"]:
        h.circ((0, -80), 3.6, st["gema"], (30, 90, 110), 1.4)
        h.chispa((12, -108), 6)


def herr_cincel_pequeno(h, est):
    st = ESTILO[est]
    h.poli([(0, 0), (-4.6, -24), (4.6, -24)], st["metal_l"] if est >= 3 else aclarar(st["metal"], 0.2))
    h.poli([(0, 0), (4.6, -24), (1.5, -24)], st["metal_d"], None)
    h.barra(-24, -46, 5.2, 5.0, st["metal"], st["metal_l"], st["metal_d"])
    if st["oro"]:
        h.banda(-46, 7.4, st["oro"], 4.0)
    else:
        h.banda(-46, 7.4, st["metal_d"], 4.0)
    _mango(h, est, -47, -76, 6.6, 6.2)
    h.circ((0, -78), 6.4, st["oro"] if st["oro"] else st["metal"], BORDE, 1.8)
    h.circ((-2, -80), 1.8, (255, 255, 255), None)
    if st["gema"]:
        h.circ((0, -62), 3.0, st["gema"], (30, 90, 110), 1.4)
        h.chispa((10, -88), 5)


_TOOLS = {"brocha": herr_brocha, "martillo": herr_martillo, "cincel": herr_cincel, "cincel_pequeno": herr_cincel_pequeno}


def dibujar_herramienta(p, tipo, x, y, escala=1.0, estrellas=0, ang=28.0):
    """Herramienta con la punta de trabajo en (x, y) y el mango hacia arriba a la derecha.
    Con estrellas > 0 dibuja esas estrellas debajo; el aspecto mejora con las estrellas."""
    est = max(1, min(5, estrellas or 1))
    h = _H(p, x, y, escala, ang)
    _TOOLS[tipo](h, est)
    if estrellas > 0:
        n = min(5, estrellas)
        r = 9 * escala
        sep = 21 * escala
        cy = y + 26 * escala
        x0 = x - (n - 1) * sep / 2
        for i in range(n):
            estrella(p, int(x0 + i * sep), int(cy), max(3, int(r)), (255, 210, 60), (160, 110, 20))


# ====================================================================== carrito de mina
_fuente = {}


def _z(p, x, y, s, col, g):
    pygame.draw.lines(p, col, False, [(x, y), (x + s, y), (x, y + s), (x + s, y + s)], g)


def dibujar_carrito(p, x, y, escala=1.0, t=0.0, aviso=True):
    """Carrito de mina con un huesito y un pico. aviso=True rebota y lleva un globo rojo con "!" que parpadea;
    aviso=False es el carrito dormido (gris) con "zzz"."""
    e = escala
    if aviso:
        rebote = abs(math.sin(t * 5.0)) * 8 * e
        sx, sy = 1.0 + 0.03 * (1 - abs(math.sin(t * 5.0))), 1.0
    else:
        rebote = 0.0
        sx = sy = 1.0
    y = y - rebote
    madera = (158, 104, 60) if aviso else (132, 128, 134)
    madera_o = oscurecer(madera, 0.28)
    madera_l = aclarar(madera, 0.2)
    metal = (96, 100, 114) if aviso else (110, 112, 122)
    borde = (50, 36, 30) if aviso else (58, 56, 66)

    def P(u, v):
        return (x + u * e * sx, y + v * e * sy)

    # lo que lleva: huesito y pico
    hueso = (246, 238, 214) if aviso else (200, 198, 196)
    hb = ((-40, -14), (-12, -44))
    pygame.draw.line(p, borde, P(*hb[0]), P(*hb[1]), max(2, int(11 * e)))
    pygame.draw.line(p, hueso, P(*hb[0]), P(*hb[1]), max(1, int(7.5 * e)))
    for (u, v), d in (((hb[1][0], hb[1][1]), (1, -1)), ((hb[1][0], hb[1][1]), (-1, 1))):
        pass
    for (u, v) in ((hb[1][0] + 4, hb[1][1] - 4), (hb[1][0] - 5, hb[1][1] - 1)):
        c = P(u, v)
        pygame.draw.circle(p, borde, (int(c[0]), int(c[1])), max(2, int(6.4 * e)))
        pygame.draw.circle(p, hueso, (int(c[0]), int(c[1])), max(1, int(4.8 * e)))
    # pico
    mango = (172, 120, 70) if aviso else (124, 118, 120)
    pygame.draw.line(p, borde, P(10, -8), P(38, -56), max(2, int(8 * e)))
    pygame.draw.line(p, mango, P(10, -8), P(38, -56), max(1, int(5 * e)))
    cab = [P(20, -62), P(38, -66), P(56, -54), P(60, -46), P(46, -54), P(36, -54), P(22, -52)]
    pygame.draw.polygon(p, metal, cab)
    pygame.draw.polygon(p, borde, cab, max(1, int(2 * e)))
    pygame.draw.line(p, aclarar(metal, 0.5), P(26, -60), P(44, -60), max(1, int(2 * e)))
    # piedritas
    for (u, v, r, c) in ((-22, -12, 6, (170, 150, 120)), (-4, -14, 5, (130, 118, 100)), (18, -13, 5.5, (184, 164, 132))):
        c2 = P(u, v)
        col = c if aviso else (150, 148, 150)
        pygame.draw.circle(p, borde, (int(c2[0]), int(c2[1])), max(2, int((r + 1.5) * e)))
        pygame.draw.circle(p, col, (int(c2[0]), int(c2[1])), max(1, int(r * e)))
    # cuerpo
    cuerpo = [P(-50, -14), P(50, -14), P(42, 30), P(-42, 30)]
    pygame.draw.polygon(p, madera, cuerpo)
    pygame.draw.polygon(p, madera_o, [P(30, -14), P(50, -14), P(42, 30), P(24, 30)])
    pygame.draw.polygon(p, madera_l, [P(-50, -14), P(-34, -14), P(-30, 30), P(-42, 30)])
    for v in (4, 18):
        pygame.draw.line(p, madera_o, P(-48 + (v + 14) * 0.18, v), P(48 - (v + 14) * 0.18, v), max(1, int(2 * e)))
    pygame.draw.polygon(p, borde, cuerpo, max(1, int(2.6 * e)))
    # borde de metal arriba
    aro = [P(-54, -20), P(54, -20), P(52, -10), P(-52, -10)]
    pygame.draw.polygon(p, metal, aro)
    pygame.draw.polygon(p, borde, aro, max(1, int(2.2 * e)))
    pygame.draw.line(p, aclarar(metal, 0.45), P(-48, -17), P(48, -17), max(1, int(2 * e)))
    for u in (-40, -20, 0, 20, 40):
        c = P(u, -15)
        pygame.draw.circle(p, aclarar(metal, 0.3), (int(c[0]), int(c[1])), max(1, int(1.8 * e)))
    # ruedas
    giro = t * 6.0 if aviso else 0.0
    for u in (-26, 26):
        c = P(u, 32)
        r = max(3, int(11 * e))
        pygame.draw.circle(p, borde, (int(c[0]), int(c[1])), r + max(1, int(2 * e)))
        pygame.draw.circle(p, (70, 74, 86) if aviso else (84, 86, 96), (int(c[0]), int(c[1])), r)
        for k in range(4):
            a = giro + k * math.pi / 2
            pygame.draw.line(p, aclarar(metal, 0.4), c, (c[0] + math.cos(a) * r * 0.85, c[1] + math.sin(a) * r * 0.85), max(1, int(2 * e)))
        pygame.draw.circle(p, aclarar(metal, 0.5), (int(c[0]), int(c[1])), max(2, int(3.4 * e)))
    # riel
    pygame.draw.line(p, (90, 80, 70) if aviso else (110, 108, 110), P(-60, 44), P(60, 44), max(2, int(4 * e)))
    if aviso:
        # globo rojo con "!" que parpadea
        k = 0.5 + 0.5 * math.sin(t * 8.0)
        r = 15 * e * (1.0 + 0.08 * k)
        cx, cy = x + 2 * e, y - 84 * e
        col = (232, 56, 60) if k > 0.35 else (255, 110, 100)
        pygame.draw.polygon(p, (255, 255, 255), [(cx - 8 * e, cy + r - 3 * e), (cx + 8 * e, cy + r - 3 * e), (cx, cy + r + 13 * e)])
        pygame.draw.circle(p, (255, 255, 255), (int(cx), int(cy)), int(r + 3 * e))
        pygame.draw.circle(p, col, (int(cx), int(cy)), int(r))
        pygame.draw.polygon(p, col, [(cx - 6 * e, cy + r - 3 * e), (cx + 6 * e, cy + r - 3 * e), (cx, cy + r + 9 * e)])
        w = max(2, int(4.2 * e))
        pygame.draw.rect(p, (255, 255, 255), (int(cx - w / 2), int(cy - 9 * e), w, int(11 * e)), border_radius=max(1, w // 2))
        pygame.draw.circle(p, (255, 255, 255), (int(cx), int(cy + 7 * e)), max(2, int(2.6 * e)))
    else:
        for i in range(3):
            fase = (t * 0.5 + i * 0.34) % 1.0
            s = (7 + 3 * i) * e
            a = int(255 * math.sin(math.pi * fase))
            cxz = x + (36 + 9 * i) * e + 3 * math.sin(t + i) * e
            cyz = y - (34 + 14 * i) * e - 10 * fase * e
            sup = pygame.Surface((int(s * 2) + 8, int(s * 2) + 8), pygame.SRCALPHA)
            g = max(2, int(2.8 * e))
            _z(sup, 4, 4, s, (70, 90, 150, a), g + 2)
            _z(sup, 4, 4, s, (200, 216, 255, a), g)
            p.blit(sup, (cxz - 4, cyz - 4))
