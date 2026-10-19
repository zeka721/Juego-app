"""Mapa de la Horda: terreno en cuadricula y reglas de fisica (sin dibujo).

Tipos de casilla:
  PASTO   se camina normal
  HOJAS   arbustos y hojas: se pisan normal
  AGUA    se entra, pero se anda mas lento
  ARBOL   bloquea (hay que bordearlo)
  ROCA    bloquea (hay que bordearla)
"""

import math
import random
from collections import deque

TAM = 40                      # pixeles por casilla
COLS, FILAS = 300, 220        # 12000 x 8800 px (el doble de ancho y de alto que antes)
AREA = COLS * FILAS / 16500   # factor de densidad: el terreno se escala para tener la misma densidad
ANCHO_MUNDO, ALTO_MUNDO = COLS * TAM, FILAS * TAM

PASTO, HOJAS, AGUA, ARBOL, ROCA = 0, 1, 2, 3, 4
BLOQUEADO = {ARBOL, ROCA}
VEL_AGUA = 0.5
VECINOS8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def generar(seed=7):
    """Cuadricula de COLS x FILAS. Siempre hay pasto alrededor del centro (donde aparece el heroe)."""
    rng = random.Random(seed)
    g = [[PASTO] * COLS for _ in range(FILAS)]
    for _ in range(int(30 * AREA)):                        # lagos
        cx, cy = rng.randint(4, COLS - 5), rng.randint(4, FILAS - 5)
        r = rng.uniform(2.5, 4.5)
        for y in range(max(0, int(cy - r - 1)), min(FILAS, int(cy + r + 2))):
            for x in range(max(0, int(cx - r - 1)), min(COLS, int(cx + r + 2))):
                if math.hypot(x - cx, (y - cy) * 1.1) <= r:
                    g[y][x] = AGUA
    for _ in range(int(40 * AREA)):                        # bosques (grupos de arboles)
        cx, cy = rng.randint(2, COLS - 3), rng.randint(2, FILAS - 3)
        for _ in range(rng.randint(12, 24)):
            x = int(rng.gauss(cx, 2.2))
            y = int(rng.gauss(cy, 2.0))
            if 0 <= x < COLS and 0 <= y < FILAS and g[y][x] == PASTO:
                g[y][x] = ARBOL
    for _ in range(int(165 * AREA)):                       # arboles sueltos
        x, y = rng.randrange(COLS), rng.randrange(FILAS)
        if g[y][x] == PASTO:
            g[y][x] = ARBOL
    for _ in range(int(185 * AREA)):                       # rocas
        x, y = rng.randrange(COLS), rng.randrange(FILAS)
        if g[y][x] == PASTO:
            g[y][x] = ROCA
    for y in range(FILAS):                                 # hojas y arbustos: zonas que se pisan
        for x in range(COLS):
            if g[y][x] == PASTO and rng.random() < 0.16:
                g[y][x] = HOJAS
    cx, cy = COLS // 2, FILAS // 2
    for y in range(cy - 6, cy + 7):                        # zona libre donde nace el heroe
        for x in range(cx - 6, cx + 7):
            if g[y][x] in (AGUA, ARBOL, ROCA):
                g[y][x] = PASTO
    return g


def casilla(g, x, y):
    cx, cy = int(x // TAM), int(y // TAM)
    if 0 <= cx < COLS and 0 <= cy < FILAS:
        return g[cy][cx]
    return ARBOL                                           # fuera del mapa = bloqueado


def choca(g, x, y, r, borde=True):
    """True si un circulo de radio r en (x,y) toca una casilla bloqueada.
    Con borde=True tambien cuenta como choque salirse del mapa (heroe).
    Con borde=False el afuera del mapa se ignora (enemigos que entran desde fuera)."""
    x0, x1 = int((x - r) // TAM), int((x + r) // TAM)
    y0, y1 = int((y - r) // TAM), int((y + r) // TAM)
    for cy in range(y0, y1 + 1):
        for cx in range(x0, x1 + 1):
            if not (0 <= cx < COLS and 0 <= cy < FILAS):
                if borde:
                    return True
                continue
            if g[cy][cx] in BLOQUEADO:
                # distancia del centro al rectangulo de la casilla
                nx = min(max(x, cx * TAM), (cx + 1) * TAM)
                ny = min(max(y, cy * TAM), (cy + 1) * TAM)
                if (x - nx) ** 2 + (y - ny) ** 2 < r * r:
                    return True
    return False


def mover(g, x, y, dx, dy, r, borde=True):
    """Mueve el circulo y se desliza por las paredes (primero X, luego Y)."""
    nx = x + dx
    if not choca(g, nx, y, r, borde):
        x = nx
    ny = y + dy
    if not choca(g, x, ny, r, borde):
        y = ny
    return x, y


def velocidad_en(g, x, y):
    return VEL_AGUA if casilla(g, x, y) == AGUA else 1.0


def libre_cerca(g, x, y, r, rng, radio=260, intentos=30):
    """Un punto libre (no bloqueado) cerca de (x,y)."""
    for _ in range(intentos):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, radio)
        px, py = x + math.cos(a) * d, y + math.sin(a) * d
        if not choca(g, px, py, r):
            return px, py
    return x, y


# ------------------------------------------------------------ camino hacia el heroe
_cache_mascara = {"g": None, "m": None}


def _mascara_pegada(g):
    """Casillas libres pero pegadas a arbol o roca (y las propias bloqueadas).
    Por ahi no pasa el camino: deja un margen para que un enemigo grande quepa."""
    if _cache_mascara["g"] is g:
        return _cache_mascara["m"]
    m = [[False] * COLS for _ in range(FILAS)]
    for y in range(FILAS):
        for x in range(COLS):
            if g[y][x] in BLOQUEADO:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < FILAS and 0 <= xx < COLS:
                            m[yy][xx] = True
    _cache_mascara["g"], _cache_mascara["m"] = g, m
    return m


def campo_flujo_iter(g, hcx, hcy):
    """Igual que campo_flujo, pero cede el control cada tanto (generador): el mapa es grande
    y asi el calculo se reparte entre cuadros y no provoca tirones."""
    """Distancia en casillas desde la casilla del heroe hasta cada casilla transitable
    (-1 si no se llega). Los enemigos bajan por este campo hacia el heroe."""
    m = _mascara_pegada(g)
    dist = [[-1] * COLS for _ in range(FILAS)]
    if not (0 <= hcx < COLS and 0 <= hcy < FILAS):
        return dist
    # origen: la casilla libre (sin pegarse a arboles) mas cercana al heroe. Asi, si el
    # heroe se mete en un hueco estrecho, los enemigos llegan hasta la entrada del hueco.
    origen = (hcx, hcy)
    for radio in range(0, 6):
        hallado = False
        for dy in range(-radio, radio + 1):
            for dx in range(-radio, radio + 1):
                if max(abs(dx), abs(dy)) != radio:
                    continue
                x, y = hcx + dx, hcy + dy
                if 0 <= x < COLS and 0 <= y < FILAS and not m[y][x] and g[y][x] not in BLOQUEADO:
                    origen, hallado = (x, y), True
                    break
            if hallado:
                break
        if hallado:
            break
    dist[origen[1]][origen[0]] = 0
    cola = deque([origen])
    n = 0
    while cola:
        x, y = cola.popleft()
        d = dist[y][x] + 1
        for dx, dy in VECINOS8:
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < FILAS and dist[ny][nx] < 0 and not m[ny][nx]:
                dist[ny][nx] = d
                cola.append((nx, ny))
        n += 1
        if n % 2500 == 0:
            yield                       # cede el control: se sigue en el proximo cuadro
    return dist


def campo_flujo(g, hcx, hcy):
    """Calcula el campo de distancia de una vez."""
    it = campo_flujo_iter(g, hcx, hcy)
    while True:
        try:
            next(it)
        except StopIteration as fin:
            return fin.value
