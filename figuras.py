"""Figuras coleccionables del Gachapon: catalogo, rangos, probabilidades, sorteo y dibujo.

    figuras.tirar(rng=random) -> id de figura       (funcion pura, sin tocar el perfil)
    figuras.contar_unicas(perfil) -> cuantas figuras distintas tiene
    figuras.dibujar_figura_coleccion(p, id, cx, cy, tam, ...)   figura sobre su base con aura e insignia

Todo el arte se dibuja con codigo; las figuras reutilizan las criaturas y peces de arte.py,
los dinosaurios de arte_dinos.py y personajes extra originales dibujados aqui.
"""

import colorsys
import math
import random

import pygame

import arte
import arte_dinos
from nucleo import aclarar, oscurecer

# ---------------------------------------------------------------- rangos
RANGOS = ["C", "B", "A", "S", "SS", "SSS"]
COLOR_RANGO = {
    "C": (176, 184, 200),       # plata
    "B": (70, 150, 245),        # azul
    "A": (70, 205, 110),        # verde
    "S": (255, 200, 45),        # dorado
    "SS": (235, 65, 205),       # magenta
    "SSS": (255, 120, 60),      # arcoiris (este es solo el color base)
}
NOMBRE_RANGO = {"C": "Común", "B": "Poco común", "A": "Rara", "S": "Súper rara",
                "SS": "Épica", "SSS": "¡Legendaria!"}

# porcentaje de cada rango en una tirada (suma 100)
PROBABILIDADES = {"C": 45.0, "B": 28.0, "A": 15.0, "S": 7.5, "SS": 3.5, "SSS": 1.0}

# Tiro garantizado (OPCIONAL, desactivado): si vale N, cada N-esima tirada sale al menos
# GARANTIZADO_RANGO_MINIMO. None = sin garantia.
TIRO_GARANTIZADO_CADA = None
GARANTIZADO_RANGO_MINIMO = "A"


def color_rango(rango, t=0.0):
    """Color del rango; el SSS cambia de tono con el tiempo (arcoiris)."""
    if rango == "SSS":
        return color_arcoiris(t * 0.6)
    return COLOR_RANGO[rango]


def color_arcoiris(h, s=0.75, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


# ---------------------------------------------------------------- catalogo
# id: (nombre, rango, tipo, arg, texto corto).  tipo: cri | pez | dino | jefe | extra
_DEF = [
    # --- C (10)
    ("pelusin", "Pelusín", "C", "cri", "pelusin", "Una bolita de pelo calentita que ronronea."),
    ("gotita", "Gotita", "C", "cri", "gotita", "Brilla como una gota de rocío al sol."),
    ("hojita", "Hojita", "C", "cri", "hojita", "Le encanta bailar con el viento del jardín."),
    ("nubi", "Nubi", "C", "cri", "nubi", "Flota tranquila y regala cosquillas de lluvia."),
    ("sardina", "Sardina", "C", "pez", "sardina", "Nada en grupo y nunca se pierde."),
    ("trucha", "Trucha", "C", "pez", "trucha", "Salta feliz por los ríos de montaña."),
    ("hongo", "Hongo Sonriente", "C", "extra", "hongo", "Un hongo risueño que sale después de la lluvia."),
    ("pelota", "Pelota Saltarina", "C", "extra", "pelota", "Rebota tan alto que casi toca las nubes."),
    ("helado", "Helado Mágico", "C", "extra", "helado", "Dos bolas de helado que jamás se derriten."),
    ("patito", "Patito de Goma", "C", "extra", "patito", "Hace cuac cuac en la hora del baño."),
    # --- B (9)
    ("chispin", "Chispín", "B", "cri", "chispin", "Suelta chispitas de alegría por la cola."),
    ("piedri", "Piedri", "B", "cri", "piedri", "Parece duro, pero es un cariñoso."),
    ("burbujo", "Burbujo", "B", "cri", "burbujo", "Hace burbujas de colores con cada risa."),
    ("payaso", "Pez Payaso", "B", "pez", "payaso", "Se esconde entre las anémonas para jugar."),
    ("globo", "Pez Globo", "B", "pez", "globo", "Se infla de risa cuando le hacen cosquillas."),
    ("atun", "Atún Veloz", "B", "pez", "atun", "Un gran nadador del mar azul."),
    ("velociraptor", "Velociraptor", "B", "dino", "velociraptor", None),
    ("cohete", "Cohete Chispa", "B", "extra", "cohete", "Despega con un fium hacia las estrellas."),
    ("robot", "Robot Amigo", "B", "extra", "robot", "Siempre tiene un abrazo de metal listo."),
    # --- A (7)
    ("llamita", "Llamita", "A", "cri", "llamita", "Una llamita traviesa que calienta los días fríos."),
    ("pinchin", "Pinchín", "A", "cri", "pinchin", "Sus púas son de mentiritas: es muy dulce."),
    ("pezluna", "Pez Luna", "A", "pez", "pezluna", "Brilla de noche como la luna llena."),
    ("dorado", "Pez Dorado", "A", "pez", "dorado", "Dicen que cumple un deseo si lo cuidas."),
    ("anquilosaurio", "Anquilosaurio", "A", "dino", "anquilosaurio", None),
    ("estegosaurio", "Estegosaurio", "A", "dino", "estegosaurio", None),
    ("drakito", "Drakito Rojo", "A", "extra", "drakito", "Un dragoncito que escupe chispas de colores."),
    # --- S (5)
    ("pulpo", "Pulpo Abrazos", "S", "pez", "pulpo", "Tiene ocho brazos para dar ocho abrazos."),
    ("triceratops", "Triceratops", "S", "dino", "triceratops", None),
    ("braquiosaurio", "Braquiosaurio", "S", "dino", "braquiosaurio", None),
    ("lunita", "Lunita", "S", "cri", "lunita", "Cuida los sueños mientras todos duermen."),
    ("estrellin", "Estrellín", "S", "cri", "estrellin", "Una estrella que bajó del cielo para jugar contigo."),
    # --- SS (3)
    ("dragonito", "Dragonito", "SS", "cri", "dragonito", "Un dragoncito volador con un corazón gigante."),
    ("tiranosaurio", "Tiranosaurio", "SS", "dino", "tiranosaurio", None),
    ("cofre", "Cofre del Tesoro", "SS", "extra", "cofre", "Guarda un tesoro de risas y monedas de oro."),
    # --- SSS (2)
    ("rey_grunon", "Rey Grunón", "SSS", "jefe", "rey", "¡El gran Rey Grunón, en versión de colección!"),
    ("cosmo", "Cosmo Anillos", "SSS", "extra", "cosmo", "Un planeta con anillos que canta canciones del espacio."),
]

FIGURAS = {}
ORDEN_FIGURAS = []
for _id, _nom, _rango, _tipo, _arg, _txt in _DEF:
    if _txt is None:                                  # dinosaurios: dato curioso del libro
        _txt = arte_dinos.DINOS[_arg][4]
    FIGURAS[_id] = {"id": _id, "nombre": _nom, "rango": _rango, "tipo": _tipo, "arg": _arg, "texto": _txt}
    ORDEN_FIGURAS.append(_id)
TOTAL = len(FIGURAS)
POR_RANGO = {r: [i for i in ORDEN_FIGURAS if FIGURAS[i]["rango"] == r] for r in RANGOS}


def nombre(ident):
    return FIGURAS[ident]["nombre"]


def rango_de(ident):
    return FIGURAS[ident]["rango"]


# ---------------------------------------------------------------- paginas de mundo del album y suerte
# El album tiene una pagina por mundo. Cada figura nueva llena su pagina; cuanto mas llenas estan las
# paginas, mejores son las probabilidades de sacar figuras de rango alto (suerte del album).
PAGINAS = [
    {"id": "criaturas", "nombre": "Criaturas", "color": (120, 200, 90), "tipos": ("cri",)},
    {"id": "oceano", "nombre": "Océano", "color": (70, 150, 245), "tipos": ("pez",)},
    {"id": "prehistoria", "nombre": "Prehistoria", "color": (220, 140, 60), "tipos": ("dino",)},
    {"id": "fantasia", "nombre": "Fantasía", "color": (200, 100, 230), "tipos": ("extra", "jefe")},
]
PUNTOS_PAGINA_COMPLETA = 0.25                 # bonus extra de suerte por cada pagina terminada
# cuanto crece el peso de cada rango por cada punto de suerte (C no crece: lo demas le quita terreno)
BONO_SUERTE = {"C": 0.0, "B": 0.10, "A": 0.20, "S": 0.35, "SS": 0.50, "SSS": 0.60}


def pagina_de(ident):
    """Indice de la pagina del album a la que pertenece la figura."""
    tipo = FIGURAS[ident]["tipo"]
    for k, pg in enumerate(PAGINAS):
        if tipo in pg["tipos"]:
            return k
    return 0


POR_PAGINA = [[i for i in ORDEN_FIGURAS if pagina_de(i) == k] for k in range(len(PAGINAS))]


def progreso_pagina(perfil, k):
    """(figuras distintas que tiene, total) de la pagina k."""
    ids = POR_PAGINA[k]
    return sum(1 for i in ids if perfil.figuras.get(i, 0) > 0), len(ids)


def pagina_completa(perfil, k):
    t, n = progreso_pagina(perfil, k)
    return t >= n


def suerte(perfil):
    """Puntos de suerte: suma de lo llena que esta cada pagina (0..4) + bonus por pagina completa."""
    total = 0.0
    for k in range(len(PAGINAS)):
        t, n = progreso_pagina(perfil, k)
        total += t / n
        if t >= n:
            total += PUNTOS_PAGINA_COMPLETA
    return total


def suerte_max():
    return len(PAGINAS) * (1.0 + PUNTOS_PAGINA_COMPLETA)


def probabilidades_efectivas(perfil=None):
    """Porcentaje de cada rango (suma 100) con la suerte del album del perfil; sin perfil son las base."""
    s = suerte(perfil) if perfil is not None else 0.0
    pesos = {r: PROBABILIDADES[r] * (1.0 + BONO_SUERTE[r] * s) for r in RANGOS}
    tot = sum(pesos.values())
    return {r: 100.0 * pesos[r] / tot for r in RANGOS}


def siguiente_meta(perfil):
    """Pagina incompleta a la que menos le falta: (indice, faltan) o None si el album esta completo."""
    mejor = None
    for k in range(len(PAGINAS)):
        t, n = progreso_pagina(perfil, k)
        if t < n and (mejor is None or n - t < mejor[1]):
            mejor = (k, n - t)
    return mejor


# ---------------------------------------------------------------- sorteo
def indice_rango(r):
    return RANGOS.index(r)


def sortear_rango(rng=random, minimo=None, probs=None):
    """Elige un rango segun 'probs' (por defecto PROBABILIDADES), opcionalmente al menos 'minimo'."""
    probs = probs or PROBABILIDADES
    validos = [r for r in RANGOS if minimo is None or indice_rango(r) >= indice_rango(minimo)]
    total = sum(probs[r] for r in validos)
    x = rng.random() * total
    acum = 0.0
    for r in validos:
        acum += probs[r]
        if x < acum:
            return r
    return validos[-1]


def tirar(rng=random, rango=None, minimo=None, probs=None):
    """Una tirada: elige el rango por probabilidad y luego una figura de ese rango al azar.
    'rango' fuerza un rango (pruebas); 'minimo' pide al menos ese rango (tiro garantizado);
    'probs' son las probabilidades a usar (por defecto las base; la escena pasa las del album)."""
    if rango is None:
        rango = sortear_rango(rng, minimo, probs)
    return rng.choice(POR_RANGO[rango])


def rango_garantizado(numero_tirada):
    """Rango minimo que debe salir en la tirada numero N (1, 2, 3...), o None."""
    n = TIRO_GARANTIZADO_CADA
    if n and numero_tirada % n == 0:
        return GARANTIZADO_RANGO_MINIMO
    return None


def contar_unicas(perfil):
    """Cuantas figuras distintas tiene el jugador."""
    return sum(1 for i in ORDEN_FIGURAS if perfil.figuras.get(i, 0) > 0)


def contar_unicas_rango(perfil, rango):
    return sum(1 for i in POR_RANGO[rango] if perfil.figuras.get(i, 0) > 0)


def cantidad(perfil, ident):
    return int(perfil.figuras.get(ident, 0))


# ---------------------------------------------------------------- personajes extra (originales)
def _oj(p, x, y, r):
    pygame.draw.circle(p, (255, 255, 255), (int(x), int(y)), int(r))
    pygame.draw.circle(p, (40, 30, 50), (int(x), int(y + r * 0.1)), int(r * 0.55))
    pygame.draw.circle(p, (255, 255, 255), (int(x + r * 0.15), int(y - r * 0.15)), max(1, int(r * 0.2)))


def _sonrisa(p, cx, cy, w, s):
    pygame.draw.arc(p, (60, 30, 50), pygame.Rect(cx - w / 2, cy - w * 0.3, w, w * 0.7),
                    math.pi * 1.1, math.pi * 1.9, max(2, int(3 * s)))


def _hongo(p, cx, cy, s):
    borde = (90, 40, 40)
    tallo = pygame.Rect(0, 0, 58 * s, 64 * s)
    tallo.center = (cx, cy + 28 * s)
    pygame.draw.rect(p, (250, 235, 205), tallo, border_radius=int(24 * s))
    pygame.draw.rect(p, (150, 110, 90), tallo, max(2, int(3 * s)), border_radius=int(24 * s))
    sombrero = pygame.Rect(0, 0, 130 * s, 86 * s)
    sombrero.center = (cx, cy - 14 * s)
    pygame.draw.ellipse(p, (230, 60, 70), sombrero)
    pygame.draw.ellipse(p, borde, sombrero, max(2, int(4 * s)))
    for dx, dy, r in ((-36, -22, 11), (0, -40, 13), (36, -22, 11), (-12, -6, 8), (22, -2, 8)):
        pygame.draw.circle(p, (255, 250, 245), (int(cx + dx * s), int(cy + dy * s)), int(r * s))
    for lado in (-1, 1):
        _oj(p, cx + lado * 13 * s, cy + 22 * s, 7 * s)
        pygame.draw.circle(p, (255, 150, 160), (int(cx + lado * 24 * s), int(cy + 36 * s)), int(5 * s))
    _sonrisa(p, cx, cy + 36 * s, 20 * s, s)


def _pelota(p, cx, cy, s):
    r = 52 * s
    cols = [(240, 70, 70), (255, 210, 60), (70, 170, 240), (90, 200, 110), (240, 120, 200), (255, 150, 50)]
    n = len(cols)
    for i, c in enumerate(cols):
        a0 = -math.pi / 2 + i * 2 * math.pi / n
        a1 = a0 + 2 * math.pi / n
        pts = [(cx, cy)] + [(cx + r * math.cos(a0 + (a1 - a0) * k / 8),
                             cy + r * math.sin(a0 + (a1 - a0) * k / 8)) for k in range(9)]
        pygame.draw.polygon(p, c, pts)
    pygame.draw.circle(p, (60, 40, 70), (int(cx), int(cy)), int(r), max(2, int(4 * s)))
    pygame.draw.circle(p, (255, 255, 255), (int(cx), int(cy)), int(11 * s))
    pygame.draw.ellipse(p, (255, 255, 255), pygame.Rect(cx - r * 0.62, cy - r * 0.7, r * 0.5, r * 0.28))


def _helado(p, cx, cy, s):
    borde = (110, 70, 40)
    cono = [(cx - 32 * s, cy + 2 * s), (cx + 32 * s, cy + 2 * s), (cx, cy + 66 * s)]
    pygame.draw.polygon(p, (235, 180, 100), cono)
    for k in (-1, 0, 1):
        pygame.draw.line(p, (200, 140, 70), (cx + k * 20 * s, cy + 4 * s), (cx + k * 5 * s, cy + 52 * s), max(1, int(2 * s)))
    pygame.draw.line(p, (200, 140, 70), (cx - 24 * s, cy + 22 * s), (cx + 24 * s, cy + 22 * s), max(1, int(2 * s)))
    pygame.draw.polygon(p, borde, cono, max(2, int(3 * s)))
    pygame.draw.circle(p, (150, 230, 205), (int(cx), int(cy - 6 * s)), int(36 * s))
    pygame.draw.circle(p, (110, 70, 80), (int(cx), int(cy - 6 * s)), int(36 * s), max(2, int(3 * s)))
    pygame.draw.circle(p, (255, 170, 205), (int(cx), int(cy - 38 * s)), int(32 * s))
    pygame.draw.circle(p, (110, 70, 80), (int(cx), int(cy - 38 * s)), int(32 * s), max(2, int(3 * s)))
    pygame.draw.circle(p, (225, 40, 60), (int(cx + 4 * s), int(cy - 72 * s)), int(9 * s))
    pygame.draw.line(p, (70, 120, 50), (cx + 4 * s, cy - 80 * s), (cx + 12 * s, cy - 92 * s), max(2, int(3 * s)))
    for lado in (-1, 1):
        _oj(p, cx + lado * 11 * s, cy - 40 * s, 6 * s)
    _sonrisa(p, cx, cy - 26 * s, 18 * s, s)


def _patito(p, cx, cy, s):
    borde = (150, 100, 20)
    amar = (255, 220, 70)
    cuerpo = pygame.Rect(0, 0, 118 * s, 78 * s)
    cuerpo.center = (cx - 6 * s, cy + 24 * s)
    pygame.draw.polygon(p, amar, [(cx - 62 * s, cy + 12 * s), (cx - 86 * s, cy - 4 * s), (cx - 56 * s, cy + 30 * s)])
    pygame.draw.ellipse(p, amar, cuerpo)
    pygame.draw.ellipse(p, borde, cuerpo, max(2, int(4 * s)))
    ala = pygame.Rect(0, 0, 54 * s, 36 * s)
    ala.center = (cx - 16 * s, cy + 28 * s)
    pygame.draw.ellipse(p, (255, 195, 40), ala)
    pygame.draw.ellipse(p, borde, ala, max(1, int(3 * s)))
    pygame.draw.circle(p, amar, (int(cx + 22 * s), int(cy - 22 * s)), int(36 * s))
    pygame.draw.circle(p, borde, (int(cx + 22 * s), int(cy - 22 * s)), int(36 * s), max(2, int(4 * s)))
    pico = [(cx + 48 * s, cy - 22 * s), (cx + 84 * s, cy - 14 * s), (cx + 48 * s, cy - 4 * s)]
    pygame.draw.polygon(p, (255, 140, 40), pico)
    pygame.draw.polygon(p, (170, 80, 20), pico, max(1, int(2 * s)))
    _oj(p, cx + 30 * s, cy - 34 * s, 7 * s)
    pygame.draw.circle(p, (255, 160, 150), (int(cx + 34 * s), int(cy - 12 * s)), int(6 * s))


def _robot(p, cx, cy, s):
    borde = (40, 55, 85)
    azul = (120, 170, 225)
    # antena
    pygame.draw.line(p, borde, (cx, cy - 58 * s), (cx, cy - 82 * s), max(2, int(4 * s)))
    pygame.draw.circle(p, (255, 90, 90), (int(cx), int(cy - 86 * s)), int(8 * s))
    # cuerpo y brazos
    cu = pygame.Rect(0, 0, 70 * s, 54 * s)
    cu.center = (cx, cy + 52 * s)
    for lado in (-1, 1):
        br = pygame.Rect(0, 0, 18 * s, 50 * s)
        br.center = (cx + lado * 48 * s, cy + 50 * s)
        pygame.draw.rect(p, (170, 190, 215), br, border_radius=int(8 * s))
        pygame.draw.rect(p, borde, br, max(2, int(3 * s)), border_radius=int(8 * s))
    pygame.draw.rect(p, azul, cu, border_radius=int(10 * s))
    pygame.draw.rect(p, borde, cu, max(2, int(4 * s)), border_radius=int(10 * s))
    pygame.draw.circle(p, (255, 220, 70), (int(cx), int(cy + 52 * s)), int(10 * s))
    pygame.draw.polygon(p, (230, 70, 90), [(cx, cy + 63 * s), (cx - 8 * s, cy + 54 * s), (cx, cy + 46 * s), (cx + 8 * s, cy + 54 * s)])
    # cabeza
    ca = pygame.Rect(0, 0, 104 * s, 82 * s)
    ca.center = (cx, cy - 14 * s)
    pygame.draw.rect(p, (190, 210, 235), ca, border_radius=int(18 * s))
    pygame.draw.rect(p, borde, ca, max(2, int(4 * s)), border_radius=int(18 * s))
    for lado in (-1, 1):
        o = pygame.Rect(0, 0, 28 * s, 28 * s)
        o.center = (cx + lado * 24 * s, cy - 22 * s)
        pygame.draw.rect(p, (60, 220, 240), o, border_radius=int(8 * s))
        pygame.draw.rect(p, borde, o, max(2, int(3 * s)), border_radius=int(8 * s))
        pygame.draw.circle(p, (255, 255, 255), (int(o.centerx + 4 * s), int(o.centery - 4 * s)), int(4 * s))
        pygame.draw.circle(p, (255, 150, 160), (int(cx + lado * 38 * s), int(cy + 2 * s)), int(6 * s))
    pygame.draw.arc(p, borde, pygame.Rect(cx - 20 * s, cy - 8 * s, 40 * s, 24 * s), math.pi * 1.1, math.pi * 1.9, max(2, int(4 * s)))


def _cohete(p, cx, cy, s):
    borde = (60, 40, 70)
    # llamas
    for dx, h, c in ((0, 52, (255, 150, 50)), (0, 32, (255, 235, 100))):
        pts = [(cx - 22 * s * (h / 52), cy + 54 * s), (cx + 22 * s * (h / 52), cy + 54 * s), (cx, cy + (54 + h) * s)]
        pygame.draw.polygon(p, c, pts)
    # aletas
    for lado in (-1, 1):
        pts = [(cx + lado * 30 * s, cy + 6 * s), (cx + lado * 66 * s, cy + 62 * s), (cx + lado * 30 * s, cy + 52 * s)]
        pygame.draw.polygon(p, (230, 60, 80), pts)
        pygame.draw.polygon(p, borde, pts, max(2, int(3 * s)))
    cu = pygame.Rect(0, 0, 76 * s, 150 * s)
    cu.center = (cx, cy - 8 * s)
    pygame.draw.ellipse(p, (245, 245, 255), cu)
    pygame.draw.rect(p, (235, 235, 248), (cx - 38 * s, cy + 6 * s, 76 * s, 56 * s))
    pygame.draw.polygon(p, (230, 60, 80), [(cx - 36 * s, cy - 40 * s), (cx + 36 * s, cy - 40 * s), (cx, cy - 86 * s)])
    pygame.draw.ellipse(p, borde, cu, max(2, int(4 * s)))
    pygame.draw.rect(p, (230, 60, 80), (cx - 38 * s, cy + 40 * s, 76 * s, 14 * s))
    pygame.draw.circle(p, (90, 190, 250), (int(cx), int(cy - 14 * s)), int(19 * s))
    pygame.draw.circle(p, borde, (int(cx), int(cy - 14 * s)), int(19 * s), max(2, int(4 * s)))
    pygame.draw.circle(p, (255, 255, 255), (int(cx - 6 * s), int(cy - 21 * s)), int(5 * s))


def _drakito(p, cx, cy, s):
    rojo, vientre = (225, 70, 60), (255, 205, 120)
    borde = oscurecer(rojo, 0.55)
    # cola y alas
    pts = [(cx + 36 * s, cy + 40 * s), (cx + 90 * s, cy + 52 * s), (cx + 110 * s, cy + 20 * s), (cx + 80 * s, cy + 30 * s), (cx + 50 * s, cy + 20 * s)]
    pygame.draw.polygon(p, rojo, pts)
    pygame.draw.polygon(p, borde, pts, max(2, int(3 * s)))
    pygame.draw.polygon(p, (255, 220, 70), [(cx + 100 * s, cy + 18 * s), (cx + 124 * s, cy + 6 * s), (cx + 114 * s, cy + 34 * s)])
    for lado in (-1, 1):
        pts = [(cx + lado * 30 * s, cy - 6 * s), (cx + lado * 92 * s, cy - 66 * s), (cx + lado * 70 * s, cy - 6 * s), (cx + lado * 84 * s, cy + 14 * s), (cx + lado * 40 * s, cy + 18 * s)]
        pygame.draw.polygon(p, (250, 140, 90), pts)
        pygame.draw.polygon(p, borde, pts, max(2, int(3 * s)))
    cu = pygame.Rect(0, 0, 100 * s, 106 * s)
    cu.center = (cx, cy + 14 * s)
    pygame.draw.ellipse(p, rojo, cu)
    pygame.draw.ellipse(p, borde, cu, max(2, int(4 * s)))
    pygame.draw.ellipse(p, vientre, pygame.Rect(cx - 28 * s, cy + 18 * s, 56 * s, 64 * s))
    for k in range(3):
        pygame.draw.line(p, (225, 160, 70), (cx - 20 * s, cy + 34 * s + k * 16 * s), (cx + 20 * s, cy + 34 * s + k * 16 * s), max(1, int(2 * s)))
    for lado in (-1, 1):
        pts = [(cx + lado * 26 * s, cy - 36 * s), (cx + lado * 44 * s, cy - 70 * s), (cx + lado * 14 * s, cy - 44 * s)]
        pygame.draw.polygon(p, (255, 240, 200), pts)
        pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
        _oj(p, cx + lado * 22 * s, cy - 6 * s, 11 * s)
        pygame.draw.circle(p, (255, 140, 130), (int(cx + lado * 38 * s), int(cy + 10 * s)), int(6 * s))
    pygame.draw.ellipse(p, (255, 170, 120), pygame.Rect(cx - 14 * s, cy + 2 * s, 28 * s, 20 * s))
    for lado in (-1, 1):
        pygame.draw.circle(p, borde, (int(cx + lado * 5 * s), int(cy + 10 * s)), max(1, int(2 * s)))
    pygame.draw.circle(p, (255, 240, 120), (int(cx), int(cy - 52 * s)), int(6 * s))


def _cofre(p, cx, cy, s):
    borde = (70, 40, 20)
    oro, madera = (255, 205, 60), (170, 105, 55)
    # brillo de monedas
    for dx, dy in ((-26, -78), (4, -92), (30, -76), (-8, -70)):
        pygame.draw.circle(p, oro, (int(cx + dx * s), int(cy + dy * s)), int(13 * s))
        pygame.draw.circle(p, (170, 110, 20), (int(cx + dx * s), int(cy + dy * s)), int(13 * s), max(1, int(2 * s)))
    pygame.draw.circle(p, (255, 90, 120), (int(cx + 46 * s), int(cy - 66 * s)), int(10 * s))
    pygame.draw.circle(p, (90, 220, 250), (int(cx - 46 * s), int(cy - 64 * s)), int(10 * s))
    cuerpo = pygame.Rect(0, 0, 130 * s, 70 * s)
    cuerpo.center = (cx, cy + 36 * s)
    pygame.draw.rect(p, madera, cuerpo, border_radius=int(10 * s))
    tapa = pygame.Rect(0, 0, 130 * s, 76 * s)
    tapa.midbottom = (cx, cy + 6 * s)
    pygame.draw.rect(p, (190, 120, 62), tapa, border_top_left_radius=int(48 * s), border_top_right_radius=int(48 * s))
    for dx in (-44, 44):
        pygame.draw.rect(p, oro, (cx + dx * s - 8 * s, tapa.top + 22 * s, 16 * s, 54 * s))
        pygame.draw.rect(p, oro, (cx + dx * s - 8 * s, cuerpo.top, 16 * s, 70 * s))
    pygame.draw.rect(p, oro, (cx - 65 * s, cy + 2 * s, 130 * s, 10 * s))
    pygame.draw.rect(p, borde, cuerpo, max(2, int(4 * s)), border_radius=int(10 * s))
    pygame.draw.rect(p, borde, tapa, max(2, int(4 * s)), border_top_left_radius=int(48 * s), border_top_right_radius=int(48 * s))
    pygame.draw.circle(p, oro, (int(cx), int(cy + 12 * s)), int(14 * s))
    pygame.draw.circle(p, borde, (int(cx), int(cy + 12 * s)), int(14 * s), max(2, int(3 * s)))
    pygame.draw.rect(p, borde, (cx - 3 * s, cy + 12 * s, 6 * s, 12 * s))


def _cosmo(p, cx, cy, s):
    inc = math.radians(-22)
    ci, si = math.cos(inc), math.sin(inc)

    def anillo(medio, rx, ry, grosor, color):
        pts = []
        rango = range(0, 21) if medio == "atras" else range(20, 41)
        for k in rango:
            a = k / 40 * 2 * math.pi
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((cx + x * ci - y * si, cy + x * si + y * ci))
        pygame.draw.lines(p, color, False, pts, max(2, int(grosor * s)))
    anillo("atras", 92 * s, 24 * s, 12, (255, 205, 90))
    anillo("atras", 92 * s, 24 * s, 4, (255, 240, 170))
    r = 48 * s
    pygame.draw.circle(p, (120, 90, 220), (int(cx), int(cy)), int(r))
    # bandas del planeta
    sup = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
    for k, c in enumerate(((170, 130, 250), (95, 70, 190), (200, 160, 255))):
        pygame.draw.rect(sup, c, (0, r * (0.35 + 0.42 * k) - r * 0.1, r * 2, r * 0.22))
    mask = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (int(r), int(r)), int(r))
    sup.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    p.blit(sup, (cx - r, cy - r))
    pygame.draw.circle(p, (50, 30, 100), (int(cx), int(cy)), int(r), max(2, int(4 * s)))
    pygame.draw.ellipse(p, (255, 255, 255), pygame.Rect(cx - r * 0.7, cy - r * 0.78, r * 0.5, r * 0.26))
    for lado in (-1, 1):
        _oj(p, cx + lado * 16 * s, cy - 4 * s, 9 * s)
        pygame.draw.circle(p, (255, 150, 190), (int(cx + lado * 28 * s), int(cy + 14 * s)), int(6 * s))
    _sonrisa(p, cx, cy + 10 * s, 22 * s, s)
    anillo("delante", 92 * s, 24 * s, 12, (255, 205, 90))
    anillo("delante", 92 * s, 24 * s, 4, (255, 240, 170))
    for dx, dy, rr in ((-92, -44, 9), (88, 48, 7), (70, -62, 6)):
        arte_estrella(p, cx + dx * s, cy + dy * s, rr * s)


def arte_estrella(p, cx, cy, r, color=(255, 235, 120), borde=(170, 120, 20)):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pygame.draw.polygon(p, color, pts)
    pygame.draw.polygon(p, borde, pts, max(1, int(r / 7)))


_EXTRAS = {"hongo": _hongo, "pelota": _pelota, "helado": _helado, "patito": _patito, "robot": _robot,
           "cohete": _cohete, "drakito": _drakito, "cofre": _cofre, "cosmo": _cosmo}


# ---------------------------------------------------------------- arte en cache (recortado)
_ARTE = {}           # id -> Surface recortada (SRCALPHA), maximo 300x300
_ESC = {}            # (id, tam, silueta) -> Surface escalada
_FUENTES = {}


def fuente(tam):
    f = _FUENTES.get(tam)
    if f is None:
        f = _FUENTES[tam] = pygame.font.SysFont("arial", tam, bold=True)
    return f


def _pintar_figura(sup, ident, cx, cy):
    f = FIGURAS[ident]
    tipo, arg = f["tipo"], f["arg"]
    if tipo == "cri":
        arte.dibujar_criatura(sup, arg, cx, cy, 2.3, 1.0)
    elif tipo == "pez":
        arte.dibujar_pez(sup, arg, cx, cy, 2.0, 1, 0.0)
    elif tipo == "dino":
        arte_dinos.dibujar_dino(sup, arg, cx, cy, 1.0, 0.4)
    elif tipo == "jefe":
        arte.dibujar_jefe(sup, cx, cy, 0.75, 0.0)
    else:
        _EXTRAS[arg](sup, cx, cy, 2.6)


def arte_figura(ident):
    """Dibujo de la figura (sin base), recortado y ajustado a 300x300 como maximo."""
    s = _ARTE.get(ident)
    if s is None:
        lienzo = pygame.Surface((900, 700), pygame.SRCALPHA)
        _pintar_figura(lienzo, ident, 450, 350)
        r = lienzo.get_bounding_rect()
        recorte = lienzo.subsurface(r).copy()
        k = min(300 / recorte.get_width(), 300 / recorte.get_height(), 1.6)
        s = pygame.transform.smoothscale(recorte, (max(1, int(recorte.get_width() * k)),
                                                   max(1, int(recorte.get_height() * k))))
        _ARTE[ident] = s
    return s


def _silueta(s, color=(34, 26, 58)):
    return pygame.mask.from_surface(s, 40).to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))


def superficie(ident, tam, silueta=False):
    """Dibujo de la figura ajustado para caber en un cuadro tam x tam (con cache)."""
    tam = max(8, int(tam))
    clave = (ident, tam, silueta)
    s = _ESC.get(clave)
    if s is None:
        base = arte_figura(ident)
        k = tam / max(base.get_width(), base.get_height())
        s = pygame.transform.smoothscale(base, (max(1, int(base.get_width() * k)),
                                                max(1, int(base.get_height() * k))))
        if silueta:
            s = _silueta(s)
        _ESC[clave] = s
    return s


def dibujar_arte(p, ident, cx, cy, tam, silueta=False, ancho_rel=1.0, color_sil=None):
    """Dibuja solo el arte centrado. ancho_rel < 1 lo estrecha (simula un giro); negativo lo voltea."""
    s = superficie(ident, tam, silueta)
    if color_sil is not None and silueta:
        s = _silueta(s, color_sil)
    if abs(ancho_rel - 1.0) > 0.001:
        w = max(2, int(s.get_width() * abs(ancho_rel)))
        s = pygame.transform.scale(s, (w, s.get_height()))
        if ancho_rel < 0:
            s = pygame.transform.flip(s, True, False)
    p.blit(s, s.get_rect(center=(int(cx), int(cy))))
    return s


# ---------------------------------------------------------------- aura, base e insignia
_GLOWS = {}


def resplandor(color, radio, fuerza=1.0):
    """Superficie con un brillo circular suave (SRCALPHA) del color dado."""
    clave = (color, int(radio), round(fuerza, 2))
    g = _GLOWS.get(clave)
    if g is None:
        radio = int(radio)
        g = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pasos = 28
        for i in range(pasos, 0, -1):
            f = i / pasos
            alfa = int(255 * fuerza * (1 - f) ** 1.6 * 0.5)
            pygame.draw.circle(g, (*color, min(255, alfa)), (radio, radio), int(radio * f))
        _GLOWS[clave] = g
    return g


def dibujar_base(p, cx, cy, ancho, rango, t=0.0):
    """Base redonda de figura de coleccion; cy es el centro de su cara superior."""
    col = color_rango(rango, t)
    rx = ancho / 2
    ry = rx * 0.27
    h = max(6, ancho * 0.09)
    pygame.draw.ellipse(p, (20, 12, 40), pygame.Rect(cx - rx * 1.04, cy - ry * 1.04 + h * 0.5, rx * 2.08, ry * 2.08))
    pygame.draw.ellipse(p, oscurecer(col, 0.55), pygame.Rect(cx - rx, cy - ry + h, rx * 2, ry * 2))
    pygame.draw.rect(p, oscurecer(col, 0.55), (cx - rx, cy, rx * 2, h))
    pygame.draw.ellipse(p, oscurecer(col, 0.3), pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2))
    pygame.draw.ellipse(p, col, pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2), max(2, int(ancho * 0.02)))
    pygame.draw.ellipse(p, aclarar(col, 0.35), pygame.Rect(cx - rx * 0.86, cy - ry * 0.86, rx * 1.72, ry * 1.72))
    pygame.draw.ellipse(p, aclarar(col, 0.65), pygame.Rect(cx - rx * 0.6, cy - ry * 0.6, rx * 1.2, ry * 1.2), max(1, int(ancho * 0.012)))


def dibujar_insignia(p, x, y, rango, alto=30, t=0.0):
    """Insignia con la letra del rango, centrada en (x, y)."""
    f = fuente(max(10, int(alto * 0.78)))
    letras = f.render(rango, True, (255, 255, 255))
    w = max(alto, letras.get_width() + alto * 0.55)
    r = pygame.Rect(0, 0, w, alto)
    r.center = (int(x), int(y))
    col = color_rango(rango, t)
    pygame.draw.rect(p, (30, 20, 50), r.inflate(6, 6), border_radius=alto // 2 + 3)
    if rango == "SSS":
        n = 12
        for i in range(n):
            tira = pygame.Rect(r.x + r.w * i / n, r.y, r.w / n + 1, r.h)
            pygame.draw.rect(p, color_arcoiris(i / n + t * 0.5), tira)
        pygame.draw.rect(p, (255, 255, 255), r, 3, border_radius=alto // 2)
        # esquinas redondeadas: se repinta el borde
    else:
        pygame.draw.rect(p, col, r, border_radius=alto // 2)
        pygame.draw.rect(p, aclarar(col, 0.7), r, 3, border_radius=alto // 2)
    sombra = f.render(rango, True, oscurecer(col, 0.7))
    p.blit(sombra, sombra.get_rect(center=(r.centerx + 1, r.centery + 2)))
    p.blit(letras, letras.get_rect(center=r.center))
    return r


def dibujar_figura_coleccion(p, ident, cx, cy, tam, t=0.0, cantidad=None, silueta=False,
                             aura=True, ancho_rel=1.0, insignia=True, rango=None):
    """Figura de coleccion completa: aura del color del rango, base redonda, el dibujo y la
    insignia con la letra. (cx, cy) es el centro del conjunto; tam es el tamano del dibujo.
    Con silueta=True se ve oscura (todavia no la tienes)."""
    rango = rango or rango_de(ident)
    col = color_rango(rango, t)
    if aura:
        g = resplandor(col if not silueta else (110, 110, 140), tam * 0.95, 0.9 if not silueta else 0.35)
        p.blit(g, g.get_rect(center=(int(cx), int(cy))))
    base_y = cy + tam * 0.42
    dibujar_base(p, cx, base_y, tam * 1.02, rango if not silueta else "C", t)
    s = superficie(ident, tam * 0.96, silueta)
    w = s.get_width()
    if abs(ancho_rel - 1.0) > 0.001:
        w = max(2, int(w * abs(ancho_rel)))
        s = pygame.transform.scale(s, (w, s.get_height()))
        if ancho_rel < 0:
            s = pygame.transform.flip(s, True, False)
    p.blit(s, s.get_rect(midbottom=(int(cx), int(base_y + tam * 0.02))))
    if silueta:
        return
    if rango in ("S", "SS", "SSS"):                       # destellos que giran alrededor
        n = {"S": 2, "SS": 3, "SSS": 5}[rango]
        for i in range(n):
            a = t * 1.6 + i * 2 * math.pi / n
            x = cx + math.cos(a) * tam * 0.55
            y = cy - tam * 0.05 + math.sin(a) * tam * 0.32
            r = tam * 0.05 * (0.6 + 0.4 * math.sin(t * 6 + i))
            arte_estrella(p, x, y, max(2, r), (255, 255, 230), color_rango(rango, t + i * 0.2))
    if insignia:
        dibujar_insignia(p, cx - tam * 0.5, cy - tam * 0.4, rango, max(22, int(tam * 0.2)), t)
    if cantidad is not None and cantidad > 1:
        f = fuente(max(12, int(tam * 0.17)))
        txt = f.render(f"x{cantidad}", True, (255, 255, 255))
        r = txt.get_rect(center=(int(cx + tam * 0.48), int(cy - tam * 0.4))).inflate(14, 8)
        pygame.draw.rect(p, (40, 30, 70), r, border_radius=r.h // 2)
        pygame.draw.rect(p, (255, 255, 255), r, 2, border_radius=r.h // 2)
        p.blit(txt, txt.get_rect(center=r.center))
