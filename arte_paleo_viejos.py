"""Los 6 dinosaurios originales (arte_dinos) adaptados a la API nueva.

Se reutiliza su dibujo, pero con una copia de sus funciones de animacion cuyas frecuencias son multiplos de la
animacion comun (para que los cuadros guardados de los animales chicos se repitan sin saltos), y se registran
sus 6 partes de esqueleto en arte_paleo_comun (frac progresivo, brillo, cache).
"""

import inspect
import math
import re

import arte_dinos as AD
import arte_paleo_comun as C

IDS = tuple(AD.ORDEN_DINOS)
CAJA = (560, 440)

_ns = dict(AD.__dict__)
_ns["W"] = C.W
_ns["math"] = math


def _periodico(src):
    src = src.replace("t * 1.7", "t * W").replace("t * 0.9", "t * W * 0.5").replace("t * 1.2", "t * W")
    src = src.replace("t * 1.9", "t * W * 2").replace("t * 2.2", "t * W * 2").replace("t % 3.7", "t % 4.0")
    return src


for _f in (AD._mover, AD._pintar_dino):
    _src = _periodico(inspect.getsource(_f))
    exec(compile(_src, "<arte_dinos_periodico>", "exec"), _ns)

_pintar_dino = _ns["_pintar_dino"]
HUESOS = AD.HUESOS_POR_DINO


def dibujar(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    C.pintar_vivo(p, ident, x, y, escala, t, silueta,
                  lambda sup, cx, cy, e, tt, sil: _pintar_dino(sup, ident, cx, cy, e, tt, sil), CAJA)


for _id in IDS:
    C.registrar_esqueleto(_id, [lambda L, i=i, d=_id: AD._PARTES[i](L, d) for i in range(6)], (520, 360))
