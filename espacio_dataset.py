"""Carga las imagenes de Defensa Espacial desde la carpeta dataset_defensa_espacial/ (junto a los .py).

Cada imagen se carga una sola vez (cache). Si el archivo no existe, las funciones devuelven None y el juego
dibuja su version provisional. Si el tamano no es el especificado, se escala al tamano correcto.

    sonda(k)            k = 0..7    -> sonda_{k+1}.png             (285 x 112)
    nave()                          -> nave_nodriza.png            (640 x 360)
    componente(c)       c = 1..4    -> componente_{c}.png          (384 x 256)
    pieza(c, p)         p = 1..6    -> componente_{c}_{p}.png      (128 x 128)
    planeta(id)         id = mercurio, venus, ... -> planeta_{id}.png o {id}.png (tamano propio de cada planeta)
    planeta_escalado(id, diametro)  la esfera del planeta mide 'diametro' px en el juego
"""

import os

import pygame

import espacio_datos as D

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_defensa_espacial")

TAM = {"sonda": D.SONDA_TAM, "nave": (640, 360), "componente": (384, 256), "pieza": (128, 128),
       "jefe": (384, 384), "evento": (512, 512)}

# planetas: diametro de la esfera dentro de su imagen (px), en proporcion al tamano real
ESFERA = {"mercurio": 40, "venus": 64, "tierra": 66, "marte": 48,
          "jupiter": 480, "saturno": 400, "urano": 176, "neptuno": 170}
PLANETAS = list(ESFERA)

_cache = {}


def ruta(nombre):
    """Ruta del PNG 'nombre'. Ignora mayusculas: Sonda_1.png y sonda_1.png son el mismo archivo."""
    exacta = os.path.join(RAIZ, nombre + ".png")
    if os.path.exists(exacta) or not os.path.isdir(RAIZ):
        return exacta
    minusculas = (nombre + ".png").lower()
    for archivo in os.listdir(RAIZ):
        if archivo.lower() == minusculas:
            return os.path.join(RAIZ, archivo)
    return exacta


def _cargar(nombre, tam):
    clave = (nombre, tam)
    if clave in _cache:
        return _cache[clave]
    img = None
    archivo = ruta(nombre)
    if os.path.exists(archivo):
        try:
            img = pygame.image.load(archivo).convert_alpha()
            if tam and img.get_size() != tam:
                img = pygame.transform.smoothscale(img, tam)
        except pygame.error:
            img = None
    _cache[clave] = img
    return img


def sonda(k):
    return _cargar(f"sonda_{k + 1}", TAM["sonda"])


def nave():
    return _cargar("nave_nodriza", TAM["nave"])


def componente(c):
    return _cargar(f"componente_{c}", TAM["componente"])


def pieza(c, p):
    return _cargar(f"componente_{c}_{p}", TAM["pieza"])


def _archivo_planeta(id_planeta):
    """Nombre (sin .png) del archivo del planeta: planeta_<id> o solo <id>, por ejemplo Mercurio.png."""
    for nombre in (f"planeta_{id_planeta}", id_planeta):
        if os.path.exists(ruta(nombre)):
            return nombre
    return f"planeta_{id_planeta}"


def planeta(id_planeta):
    return _cargar(_archivo_planeta(id_planeta), None)


def planeta_escalado(id_planeta, diametro):
    """Imagen del planeta con la esfera de 'diametro' px. None si no existe el archivo."""
    clave = ("planeta_escalado", id_planeta, diametro)
    if clave in _cache:
        return _cache[clave]
    img = planeta(id_planeta)
    out = None
    if img is not None:
        f = diametro / ESFERA[id_planeta]
        out = pygame.transform.smoothscale(img, (max(1, round(img.get_width() * f)),
                                                 max(1, round(img.get_height() * f))))
    _cache[clave] = out
    return out


def jefe(id_planeta):
    """Sprite del jefe de un planeta: jefe_<id>.png (384 x 384). None si no existe: se dibuja el jefe provisional."""
    return _cargar(f"jefe_{id_planeta}", TAM["jefe"])


def asteroide():
    """Asteroide de extincion (512 x 512). None si falta."""
    return _cargar("asteroide_extincion", TAM["evento"])


def agujero():
    """Agujero negro, jefe final (512 x 512). Sprite estatico: el centro es transparente, el negro es el fondo."""
    return _cargar("agujero_negro", TAM["evento"])


def faltantes():
    """Nombres de las imagenes que faltan en la carpeta (sondas, nave, componentes, piezas y planetas)."""
    esperadas = [f"sonda_{k}" for k in range(1, 9)] + ["nave_nodriza"]
    esperadas += [f"componente_{c}" for c in range(1, 5)]
    esperadas += [f"componente_{c}_{p}" for c in range(1, 5) for p in range(1, 7)]
    esperadas += [_archivo_planeta(p) for p in PLANETAS]
    return [e for e in esperadas if not os.path.exists(ruta(e))]


def limpiar_cache():
    _cache.clear()
