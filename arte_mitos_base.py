"""Ayudas de dibujo para los murales mitologicos de las Ruinas.

Todas devuelven listas de puntos (x, y) en las unidades del lienzo _L: x hacia la derecha, y hacia abajo, y el motivo
entero cabe en un disco de radio 1 centrado en (0, 0). No dependen de pygame ni de arte_ruinas.
"""
import math


def arco(cx, cy, rx, ry, a0, a1, n=14):
    """Puntos de un arco de elipse desde el angulo a0 hasta a1 (radianes; 0 = derecha, pi/2 = abajo)."""
    return [(cx + rx * math.cos(a0 + (a1 - a0) * j / n), cy + ry * math.sin(a0 + (a1 - a0) * j / n))
            for j in range(n + 1)]


def elipse(cx, cy, rx, ry, ang=0.0, n=24):
    """Poligono de una elipse girada ang radianes (el lienzo no gira elipses por si solo)."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def rotar(pts, ang, ox=0.0, oy=0.0):
    """Gira los puntos ang radianes alrededor de (0, 0) y los traslada a (ox, oy)."""
    ca, sa = math.cos(ang), math.sin(ang)
    return [(ox + x * ca - y * sa, oy + x * sa + y * ca) for x, y in pts]


def mover(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def escalar(pts, sx, sy=None, ox=0.0, oy=0.0):
    """Escala respecto al punto (ox, oy)."""
    sy = sx if sy is None else sy
    return [(ox + (x - ox) * sx, oy + (y - oy) * sy) for x, y in pts]


def espejo(pts):
    """Refleja los puntos respecto al eje vertical (x -> -x) y los devuelve en orden inverso (poligonos validos)."""
    return [(-x, y) for x, y in reversed(pts)]


def simetrico(pts):
    """Contorno cerrado simetrico: los puntos de la mitad derecha (de arriba hacia abajo) mas su espejo."""
    return list(pts) + [(-x, y) for x, y in reversed(pts)]


def curva(pts, n=8, cerrada=False):
    """Suaviza una poligonal con una spline Catmull-Rom: n puntos nuevos entre cada par. Sirve para contornos organicos."""
    p = list(pts)
    if len(p) < 3:
        return p
    if cerrada:
        ext = [p[-1]] + p + [p[0], p[1]]
        tramos = len(p)
    else:
        ext = [p[0]] + p + [p[-1]]
        tramos = len(p) - 1
    out = []
    for i in range(tramos):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not cerrada:
        out.append(p[-1])
    return out


def ondas(x0, y0, x1, y1, amp, ciclos, n=28):
    """Linea ondulada de (x0, y0) a (x1, y1) con ciclos ondas de amplitud amp."""
    dx, dy = x1 - x0, y1 - y0
    largo = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / largo, dx / largo
    pts = []
    for j in range(n + 1):
        t = j / n
        d = amp * math.sin(t * ciclos * 2 * math.pi)
        pts.append((x0 + dx * t + nx * d, y0 + dy * t + ny * d))
    return pts


def hoja(x, y, ang, largo, ancho):
    """Poligono de hoja o pluma que sale de (x, y) apuntando al angulo ang."""
    base = [(0, 0), (largo * .25, -ancho * .8), (largo * .6, -ancho), (largo, 0), (largo * .6, ancho), (largo * .25, ancho * .8)]
    return rotar(base, ang, x, y)


def escamas(L, filas):
    """Atajo opcional: dibuja filas de escamas en media luna. filas = lista de (x, y, r). No llama a alto/hondo."""
    for x, y, r in filas:
        L.lin(arco(x, y, r, r, math.radians(20), math.radians(160), 8), 1.5)


def radios(n, r0, r1, a0=0.0):
    """n segmentos radiales [(x0,y0),(x1,y1)] entre los radios r0 y r1 (rayos, melenas, aureolas)."""
    return [[(r0 * math.cos(a0 + 2 * math.pi * j / n), r0 * math.sin(a0 + 2 * math.pi * j / n)),
             (r1 * math.cos(a0 + 2 * math.pi * j / n), r1 * math.sin(a0 + 2 * math.pi * j / n))] for j in range(n)]
