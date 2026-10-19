"""Arte paleontologico de Fosiles (version final): 30 animales prehistoricos, esqueletos, huesos sueltos,
30 reliquias, herramientas de 1 a 5 estrellas y el carrito de la excavacion.

API (la usan j_fosiles, escena_fosiles y el cuaderno):
    DINOS[id] = (nombre, periodo, dieta, tamano, dato curioso, color)   ORDEN_DINOS   NOMBRES_HUESOS
    dibujar_dino(p, id, x, y, escala=1.0, t=0.0, silueta=False)
    dibujar_esqueleto(p, id, x, y, escala=1.0, frac=1.0, brillo=0.0)
    dibujar_hueso(p, id, k, x, y, escala=1.0, angulo=0.0)          (k = 0..99)
    dibujar_reliquia(p, id, x, y, escala=1.0, silueta=False)       RELIQUIAS_INFO[id] = (nombre, dato)
    dibujar_herramienta(p, tipo, x, y, escala=1.0, estrellas=0, ang=28.0)
    dibujar_carrito(p, x, y, escala=1.0, t=0.0, aviso=True)
Extras: tamano_hueso(id, k), nombre_pieza(id, k), estadisticas() (cuadros y superficies guardados).

Modulos: arte_paleo_tierra (teropodos, hadrosaurio, diplodoco y mamiferos), arte_paleo_mar, arte_paleo_aire
(motor arte_paleo_cuerpo), arte_paleo_viejos (los 6 de arte_dinos), arte_paleo_huesos, arte_paleo_reliquias,
arte_paleo_cosas (herramientas y carrito), arte_paleo_comun (caches y esqueletos por partes).
"""

import arte_dinos
import arte_paleo_aire as _aire
import arte_paleo_comun as _C
import arte_paleo_cosas as _cosas
import arte_paleo_cuerpo as _cuerpo
import arte_paleo_huesos as _huesos
import arte_paleo_mar as _mar
import arte_paleo_reliquias as _rel
import arte_paleo_tierra as _tierra
import arte_paleo_viejos as _viejos
import fosiles_datos as fd

ORDEN_DINOS = list(fd.ORDEN_DINOS)
NOMBRES_HUESOS = list(_C.NOMBRES_PARTES)
HUESOS_POR_DINO = 6

_MI = "Medía"
_VIV = "Vivió hace "
_ERA = "Vivió en la Era de Hielo, hace unos 20 000 años."

# id: (nombre, periodo, dieta, tamano, dato curioso)
_TEXTOS = {
    "alosaurio": ("Alosaurio", _VIV + "150 millones de años.", "Comía carne.", "Medía 9 metros de largo.",
                  "Tenía crestas sobre los ojos y brazos con tres garras."),
    "carnotauro": ("Carnotauro", _VIV + "70 millones de años.", "Comía carne.", "Medía 8 metros de largo.",
                   "Tenía dos cuernos sobre los ojos y brazos diminutos."),
    "espinosaurio": ("Espinosaurio", _VIV + "95 millones de años.", "Comía peces y carne.", "Medía 14 metros de largo.",
                     "Tenía una vela enorme en el lomo y pescaba en los ríos."),
    "giganotosaurio": ("Giganotosaurio", _VIV + "98 millones de años.", "Comía carne.", "Medía 12 metros de largo.",
                       "Vivió donde hoy está Argentina. ¡Su cabeza medía más de un metro y medio!"),
    "ictiosaurio": ("Ictiosaurio", _VIV + "190 millones de años.", "Comía peces y calamares.",
                    "Medía 2 metros, como un delfín.",
                    "No era dinosaurio. Respiraba aire y tenía ojos enormes."),
    "dunkleosteus": ("Dunkleosteus", _VIV + "370 millones de años.", "Comía otros peces.", "Medía unos 4 metros de largo.",
                     "Era un pez con la cabeza cubierta de placas de hueso. No tenía dientes, tenía filos."),
    "plesiosaurio": ("Plesiosaurio", _VIV + "195 millones de años.", "Comía peces.", "Medía 3 metros de largo.",
                     "Tenía el cuello larguísimo y nadaba con cuatro aletas."),
    "liopleurodon": ("Liopleurodon", _VIV + "160 millones de años.", "Comía peces y reptiles marinos.",
                     "Medía unos 6 metros de largo.",
                     "Tenía cuatro aletas fuertes y una boca enorme."),
    "mosasaurio": ("Mosasaurio", _VIV + "70 millones de años.", "Comía peces y reptiles marinos.",
                   "Medía unos 12 metros de largo.",
                   "No era dinosaurio. Era un lagarto marino gigante con la cola como un remo."),
    "megalodon": ("Megalodón", "Vivió hace entre 23 y 3 millones de años.", "Comía ballenas y peces grandes.",
                  "Medía unos 15 metros de largo.",
                  "No era dinosaurio. Era un tiburón gigante con dientes de hasta 18 centímetros."),
    "arqueopterix": ("Arqueopterix", _VIV + "150 millones de años.", "Comía insectos y animalitos.",
                     "Medía unos 50 centímetros.",
                     "Tenía plumas y alas, pero también dientes y una cola larga."),
    "dimorfodonte": ("Dimorfodonte", _VIV + "190 millones de años.", "Comía insectos y animalitos.",
                     "Sus alas abiertas medían 1,4 metros.",
                     "Su nombre significa dientes de dos formas: tenía dientes grandes y chicos."),
    "ranforinco": ("Ranforinco", _VIV + "150 millones de años.", "Comía peces.", "Sus alas abiertas medían casi 2 metros.",
                   "Su cola larga terminaba en una punta en forma de rombo."),
    "tapejara": ("Tapejara", _VIV + "110 millones de años.", "Quizás comía frutas y semillas.",
                 "Sus alas abiertas medían unos 3 metros.",
                 "Tenía una cresta enorme en la cabeza, como una vela."),
    "pteranodon": ("Pteranodon", _VIV + "80 millones de años.", "Comía peces.", "Sus alas abiertas medían unos 6 metros.",
                   "No era dinosaurio. No tenía dientes y tenía una cresta larga."),
    "quetzalcoatlus": ("Quetzalcoatlus", _VIV + "68 millones de años.", "Cazaba animalitos en la tierra.",
                       "Sus alas abiertas medían unos 10 metros.",
                       "Era tan alto como una jirafa. Su nombre viene de un dios azteca."),
    "parasaurolofo": ("Parasaurolofo", _VIV + "75 millones de años.", "Comía plantas.", "Medía 10 metros de largo.",
                      "Su cresta era hueca y quizás sonaba como una trompeta."),
    "diplodoco": ("Diplodoco", _VIV + "150 millones de años.", "Comía plantas.", "Medía unos 25 metros de largo.",
                  "Tenía el cuello larguísimo y una cola como un látigo."),
    "smilodon": ("Smilodon", _ERA, "Comía carne.", "Medía 2 metros de largo.",
                 "Tenía colmillos de hasta 28 centímetros. No era un tigre."),
    "gliptodonte": ("Gliptodonte", _ERA, "Comía plantas.", "Medía unos 3 metros de largo.",
                    "Era pariente de los armadillos y tenía un caparazón enorme."),
    "megaloceros": ("Megaloceros", _ERA, "Comía plantas.", "Medía 2 metros de alto.",
                    "Sus cuernos medían más de 3 metros de ancho."),
    "rinoceronte_lanudo": ("Rinoceronte lanudo", _ERA, "Comía hierbas.", "Medía unos 3 metros de largo.",
                           "Tenía pelo largo para el frío y un cuerno de casi un metro."),
    "megaterio": ("Megaterio", _ERA, "Comía hojas.", "Medía 6 metros de largo.",
                  "Era un perezoso gigante que se paraba en dos patas para comer."),
    "mamut": ("Mamut", _ERA, "Comía plantas.", "Medía 3 metros de alto.",
              "Tenía colmillos curvos enormes y pelo largo para el frío."),
}

DINOS = {}
for _d in fd.ORDEN_DINOS:
    if _d in arte_dinos.DINOS:
        DINOS[_d] = arte_dinos.DINOS[_d]
    else:
        _col = (_tierra.ESPEC[_d]["color"] if _d in _tierra.ESPEC else _cuerpo.SP[_d]["color"])
        DINOS[_d] = _TEXTOS[_d] + (_col,)

RELIQUIAS_INFO = _rel.RELIQUIAS_INFO
dibujar_reliquia = _rel.dibujar_reliquia
dibujar_herramienta = _cosas.dibujar_herramienta
dibujar_carrito = _cosas.dibujar_carrito
dibujar_esqueleto = _C.dibujar_esqueleto
dibujar_hueso = _huesos.dibujar_hueso
tamano_hueso = _huesos.tamano_hueso
nombre_pieza = _huesos.nombre_hueso

_DESPACHO = {}
for _d in _viejos.IDS:
    _DESPACHO[_d] = _viejos.dibujar
for _d in _tierra.IDS:
    _DESPACHO[_d] = _tierra.dibujar
for _d in _mar.IDS:
    _DESPACHO[_d] = _mar.dibujar
for _d in _aire.IDS:
    _DESPACHO[_d] = _aire.dibujar

assert set(_DESPACHO) == set(fd.ORDEN_DINOS), set(fd.ORDEN_DINOS) ^ set(_DESPACHO)


def dibujar_dino(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    """Animal vivo de caricatura, de perfil, ~380x260 px a escala 1 (respira, parpadea y mueve cola/aletas/alas).
    silueta=True: gris azulado plano (se guarda en cache)."""
    _DESPACHO[ident](p, ident, x, y, escala, t, silueta)


def estadisticas():
    """Cuadros y superficies guardados (para medir la cache)."""
    return dict(_C.ESTAD, vivos=len(_C.CACHE_VIVOS.d), vivos_mb=_C.CACHE_VIVOS.bytes / 1e6, siluetas=len(_C.CACHE_SIL.d),
                esqueletos=len(_C.CACHE_ESQ.d), esqueletos_mb=_C.CACHE_ESQ.bytes / 1e6)
