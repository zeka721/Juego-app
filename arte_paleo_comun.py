"""Piezas comunes del arte paleontologico: utilidades de geometria, caches y esqueletos por partes.

- Geometria y pinceles se reutilizan de arte_dinos (mismo estilo de caricatura).
- Los esqueletos se componen de 6 "partes" (craneo, cuello/columna, costillas, cola, patas/aletas/alas delanteras,
  patas/aletas traseras). Cada animal registra sus 6 funciones de dibujo; aqui se cachean, se escalan y se
  muestran poco a poco segun `frac`.
- Las animaciones son periodicas (PERIODO s) para poder guardar cuadros de los animales chicos en una cache.
"""

import collections
import math
import random

import pygame

import arte_dinos as AD
from nucleo import aclarar, oscurecer

spline = AD._spline
largo = AD._largo
en = AD._en
rot = AD._rot
elipse_pts = AD._elipse_pts
cadena = AD._cadena
Lienzo = AD._Lienzo
Pincel = AD._Pincel

HUESO, SOMBRA, CONTORNO, LUZ, OSCURO = AD.HUESO, AD.SOMBRA, AD.CONTORNO, AD.LUZ, AD.OSCURO
HUESO_LEJOS = AD.HUESO_LEJOS
HUESO_CLARO = (250, 244, 226)
HUESO_MEDIO = (232, 220, 190)
SS = AD.SS
CONTORNO_VIVO = AD.CONTORNO_VIVO
SIL_COLOR = AD.SIL_COLOR
OJO_OSC = (50, 30, 40)

PERIODO = 4.0                      # todas las animaciones se repiten cada PERIODO segundos
W = 2 * math.pi / PERIODO
NF = 24                            # cuadros guardados por animal chico
ESC_CACHE = 0.65                   # hasta esta escala se usan cuadros guardados
T_SIL = 0.6                        # instante en que se dibuja la silueta (pose bonita)


def parpadeo(t):
    ph = t % PERIODO
    return 3.62 < ph < 3.76


def rotar_pts(pts, ang, cx=0.0, cy=0.0):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def mover_pts(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def escalar_pts(pts, sx, sy=None):
    sy = sx if sy is None else sy
    return [(x * sx, y * sy) for x, y in pts]


def espejo_x(pts):
    return [(-x, y) for x, y in pts]


# ====================================================================== caches con tope de memoria
class LRU:
    def __init__(self, max_bytes):
        self.d = collections.OrderedDict()
        self.bytes = 0
        self.max = max_bytes

    def get(self, k):
        v = self.d.get(k)
        if v is not None:
            self.d.move_to_end(k)
        return v

    def put(self, k, sup, extra=None):
        v = (sup, extra)
        if k in self.d:
            self.bytes -= self._peso(self.d[k])
        self.d[k] = v
        self.d.move_to_end(k)
        self.bytes += self._peso(v)
        while self.bytes > self.max and len(self.d) > 1:
            _, viejo = self.d.popitem(last=False)
            self.bytes -= self._peso(viejo)
        return v

    @staticmethod
    def _peso(v):
        w, h = v[0].get_size()
        return w * h * 4


CACHE_VIVOS = LRU(80 * 1024 * 1024)
CACHE_SIL = LRU(40 * 1024 * 1024)
CACHE_ESQ = LRU(60 * 1024 * 1024)
ESTAD = collections.Counter()


# ====================================================================== animales vivos (cuadros y siluetas)
def _q(esc, paso=50):
    return max(1, round(esc * paso))


def pintar_vivo(p, ident, x, y, escala, t, sil, pintar, caja):
    """Dibuja un animal con la funcion `pintar(sup, cx, cy, escala, t, sil)`.
    Los chicos (escala <= ESC_CACHE) usan cuadros guardados; los grandes se dibujan en vivo."""
    cw, ch = caja
    if sil:
        q = _q(escala, 40)
        k = (ident, q)
        v = CACHE_SIL.get(k)
        if v is None:
            e = q / 40
            sup = pygame.Surface((int(cw * e), int(ch * e)), pygame.SRCALPHA)
            pintar(sup, sup.get_width() / 2, sup.get_height() / 2, e, T_SIL, True)
            v = CACHE_SIL.put(k, sup)
            ESTAD["sil_nuevas"] += 1
        s = v[0]
        p.blit(s, s.get_rect(center=(int(x), int(y))))
        return
    if escala > ESC_CACHE:
        pintar(p, x, y, escala, t, False)
        return
    q = _q(escala, 50)
    fr = int((t % PERIODO) / PERIODO * NF) % NF
    k = (ident, q, fr)
    v = CACHE_VIVOS.get(k)
    if v is None:
        e = q / 50
        sup = pygame.Surface((int(cw * e), int(ch * e)), pygame.SRCALPHA)
        pintar(sup, sup.get_width() / 2, sup.get_height() / 2, e, fr * PERIODO / NF, False)
        v = CACHE_VIVOS.put(k, sup)
        ESTAD["cuadros_nuevos"] += 1
    s = v[0]
    p.blit(s, s.get_rect(center=(int(x), int(y))))


# ====================================================================== esqueletos por partes
NOMBRES_PARTES = ["Cráneo", "Cuello y columna", "Costillas", "Cola", "Patas de adelante", "Patas de atrás"]
_REG = {}                      # ident -> dict(partes, caja, dirs)
_maestras = {}
_fantasmas = {}
_escaladas = {}
DIRS_BASE = ("L", "R", "L", "R", "T", "T")      # barrido de la parte que esta a medias


def registrar_esqueleto(ident, partes, caja=(520, 360), dirs=DIRS_BASE):
    _REG[ident] = dict(partes=partes, caja=caja, dirs=dirs)


def esqueleto_registrado(ident):
    return ident in _REG


def partes_de(ident):
    return _REG[ident]["partes"]


def maestra(ident, i):
    """(superficie recortada a SS veces, desplazamiento x, y de su esquina respecto al centro, en px SS)."""
    k = (ident, i)
    if k not in _maestras:
        w, h = _REG[ident]["caja"]
        L = Lienzo(w, h)
        _REG[ident]["partes"][i](L)
        r = L.s.get_bounding_rect()
        if r.w == 0:
            r = pygame.Rect(L.ox, L.oy, 2, 2)
        r.inflate_ip(4, 4)
        r = r.clip(L.s.get_rect())
        _maestras[k] = (L.s.subsurface(r).copy(), r.x - L.ox, r.y - L.oy)
    return _maestras[k]


def _fantasma(ident, i):
    k = (ident, i)
    if k not in _fantasmas:
        s, ox, oy = maestra(ident, i)
        mask = pygame.mask.from_surface(s, 40)
        g = mask.to_surface(setcolor=(236, 226, 200, 70), unsetcolor=(0, 0, 0, 0))
        for n, (x, y) in enumerate(mask.outline(3)):
            if n % 2 == 0:
                pygame.draw.circle(g, (255, 244, 214, 205), (x, y), 2)
        _fantasmas[k] = (g, ox, oy)
    return _fantasmas[k]


def _escalada(ident, i, fantasma, esc):
    q = _q(esc, 25)
    k = (ident, i, fantasma, q)
    if k not in _escaladas:
        s, ox, oy = (_fantasma if fantasma else maestra)(ident, i)
        f = q / 25 / SS
        w, h = max(1, int(s.get_width() * f)), max(1, int(s.get_height() * f))
        _escaladas[k] = (pygame.transform.smoothscale(s, (w, h)), ox * f, oy * f)
    return _escaladas[k]


def _parcial(s, f, d):
    """Parte visible (fraccion f) de la superficie s, barriendo en la direccion d."""
    w, h = s.get_size()
    if d == "L":
        r = pygame.Rect(0, 0, max(1, int(w * f)), h)
    elif d == "R":
        n = max(1, int(w * f))
        r = pygame.Rect(w - n, 0, n, h)
    elif d == "B":
        n = max(1, int(h * f))
        r = pygame.Rect(0, h - n, w, n)
    else:
        r = pygame.Rect(0, 0, w, max(1, int(h * f)))
    return r


_resplandor = {}


def _brillo_sup(w, h):
    k = (w, h)
    if k not in _resplandor:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for n in range(14, 0, -1):
            f = n / 14
            pygame.draw.ellipse(s, (120, 100, 255, int(150 * (1 - f) ** 1.3)),
                                pygame.Rect(w / 2 - w * f / 2, h / 2 - h * f / 2, w * f, h * f))
        _resplandor[k] = s
    return _resplandor[k]


def _componer(ident, esc, frac):
    reg = _REG[ident]
    cw, ch = reg["caja"]
    q = _q(esc, 25)
    e = q / 25
    sup = pygame.Surface((int(cw * e), int(ch * e)), pygame.SRCALPHA)
    ox0, oy0 = sup.get_width() / 2, sup.get_height() / 2
    n = frac * 6
    orden = (3, 5, 1, 2, 4, 0)                    # de atras hacia adelante
    for i in orden:
        f = max(0.0, min(1.0, n - i))
        if f < 1.0:
            s, ox, oy = _escalada(ident, i, True, e)
            sup.blit(s, (ox0 + ox, oy0 + oy))
        if f > 0.0:
            s, ox, oy = _escalada(ident, i, False, e)
            if f >= 1.0:
                sup.blit(s, (ox0 + ox, oy0 + oy))
            else:
                r = _parcial(s, f, reg["dirs"][i])
                sup.blit(s, (ox0 + ox + r.x, oy0 + oy + r.y), r)
    return sup


def dibujar_esqueleto(p, ident, x, y, escala=1.0, frac=1.0, brillo=0.0):
    """Esqueleto de perfil; frac = fraccion de huesos hallados (las partes aparecen en orden)."""
    frac = max(0.0, min(1.0, frac))
    fq = round(frac * 60) / 60
    k = (ident, _q(escala, 25), fq)
    v = CACHE_ESQ.get(k)
    if v is None:
        v = CACHE_ESQ.put(k, _componer(ident, escala, fq))
        ESTAD["esq_nuevos"] += 1
    sup = v[0]
    if brillo > 0:
        b = max(0.0, min(1.0, brillo))
        bq = round(b * 10)
        kb = (k, "b", bq)
        vb = CACHE_ESQ.get(kb)
        if vb is None:
            c = sup.copy()
            bb = bq / 10
            c.fill((int(70 * bb), int(55 * bb), int(170 * bb), 0), special_flags=pygame.BLEND_RGB_ADD)
            vb = CACHE_ESQ.put(kb, c)
        g = _brillo_sup(int(sup.get_width() * 1.08), int(sup.get_height() * 1.0))
        g.set_alpha(int(255 * b))
        p.blit(g, g.get_rect(center=(int(x), int(y))))
        sup = vb[0]
    p.blit(sup, sup.get_rect(center=(int(x), int(y))))


# ====================================================================== piezas de hueso para esqueletos
def poli_hueso(L, pts, claro=False, **kw):
    L.poli(pts, hueso=HUESO_CLARO if claro else HUESO, **kw)


def barra_hueso(L, a, b, g, col=(HUESO, SOMBRA), nudos=True):
    """Hueso largo con dos nudos en los extremos."""
    L.linea([a, b], g, col)
    if nudos:
        L.nudo(a, g * 0.8, col)
        L.nudo(b, g * 0.7, col)


def vertebras(L, pts, r0, r1, espina=0.0, costado=1.0, paso=9.0):
    """Vertebras (discos) a lo largo de una polilinea con radio interpolado; opcional espina hacia arriba."""
    cad = spline(pts, 6)
    total = largo(cad)
    n = max(2, int(total / paso))
    L.linea(cad, max(2.0, r1 * 0.9))
    for k in range(n + 1):
        u = k / n
        (x, y), (dx, dy) = en(cad, u)
        r = r0 + (r1 - r0) * u
        if espina > 0:
            nx, ny = dy * costado, -dx * costado
            if ny > 0:
                nx, ny = -nx, -ny
            h = espina * (0.7 + 0.5 * math.sin(math.pi * u))
            L.linea([(x, y), (x + nx * h, y + ny * h)], max(1.6, r * 0.55))
        L.elipse(x, y, r, r * 0.85, hueso=HUESO, sombra=SOMBRA, grosor=1.5)


def ojo_oscuro(L, x, y, rx, ry, rot_=0.0):
    L.elipse(x, y, rx, ry, rot_, hueso=OSCURO, sombra=(30, 24, 18), grosor=2.0)


def dientes_fila(L, p0, p1, n, tam, nx, ny, claro=True):
    """Dientes triangulares a lo largo de la recta p0-p1, apuntando hacia (nx, ny)."""
    for i in range(n):
        u = (i + 0.5) / n
        x = p0[0] + (p1[0] - p0[0]) * u
        y = p0[1] + (p1[1] - p0[1]) * u
        w = math.dist(p0, p1) / n * 0.42
        tx, ty = (p1[0] - p0[0]), (p1[1] - p0[1])
        m = math.hypot(tx, ty) or 1.0
        tx, ty = tx / m * w, ty / m * w
        L.poli([(x - tx, y - ty), (x + tx, y + ty), (x + nx * tam, y + ny * tam)],
               hueso=(255, 253, 244), sombra=(225, 215, 190), grosor=1.2)


def azar(*cosas):
    """Generador al azar estable (no cambia entre ejecuciones)."""
    return random.Random(sum((i + 3) * sum(ord(c) * (j + 1) for j, c in enumerate(str(x))) for i, x in enumerate(cosas)))


# ====================================================================== cara simpatica comun
def cara(pin, p, h, cx, cy, z, ang, t, col, boca_col=(84, 40, 48)):
    """Dientes chicos, sonrisa, mejilla, ojo grande con brillo y nariz de una cabeza `h` ya colocada en (cx, cy)."""
    for x0, x1, yy, n, tam in h.get("dientes", []):
        for i in range(n):
            xx = x0 + (x1 - x0) * (0.3 + 0.7 * (i + 0.5) / n)
            w = (x1 - x0) / n * 0.2
            pts = rot([(xx - w, yy - 1), (xx + w, yy - 1), (xx, yy + tam * 0.7)], cx, cy, z, ang)
            pygame.draw.polygon(p, (255, 255, 250), [pin.pt(q) for q in pts])
    (fx, fy), (kx, ky) = h["boca"]
    boca = [(fx - 2, fy), ((fx + kx) / 2, fy + 2), (kx + 4, ky + 1), (kx - 3, ky - 5)]
    pin.linea(rot(spline(boca, 5), cx, cy, z, ang), boca_col, 2.6)
    if h.get("mej"):
        mx, my = rot([h["mej"]], cx, cy, z, ang)[0]
        pin.circ((mx, my), 5.5 * z, (255, 160, 160))
    ox, oy, r0 = h["ojo"]
    ex, ey = rot([(ox, oy)], cx, cy, z, ang)[0]
    r = r0 * z * 1.05 + 2
    if parpadeo(t):
        pin.linea([(ex - r * 0.8, ey + 1), (ex + r * 0.8, ey + 1)], OJO_OSC, 3)
    else:
        pin.circ((ex, ey), r + 1.6, OJO_OSC)
        pin.circ((ex, ey), r, (255, 255, 255))
        pin.circ((ex + r * 0.22, ey + r * 0.12), r * 0.58, (40, 28, 46))
        pin.circ((ex + r * 0.34, ey - r * 0.12), r * 0.2, (255, 255, 255))
    if h.get("nariz"):
        nx, ny = rot([h["nariz"]], cx, cy, z, ang)[0]
        pin.circ((nx, ny), 2.6 * z, (70, 40, 46))
