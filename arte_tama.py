"""Arte de Tamagotchi: despachador de mascotas + arte comun (huevos, efectos, guias, iconos, fondos).

Las funciones de dibujo estan centralizadas aqui para poder reemplazarlas luego por imagenes del usuario.
Mascotas por especie: arte_tama_agua_viento / arte_tama_fuego_hielo / arte_tama_tierra_electrico (DIBUJOS).
(cx, cy) de dibujar_mascota = CENTRO DEL CUERPO.
"""

import math

import pygame

from arte_tama_base import ojos, boca, sombra, silueta_de, rebote, respirar, CONTORNO
from arte_tama_fx import (COL, glow, destello_estrella, dibujar_ataque_basico, dibujar_impacto, dibujar_carga,
                          dibujar_ataque_cargado, dibujar_guia, puntos_guia, trazo_guia, dibujar_aura_evolucion)
from arte_tama_huevos import dibujar_huevo, dibujar_cascaras
from arte_tama_iconos import (dibujar_icono_tipo, dibujar_icono_accion, dibujar_caca, dibujar_nube_estado,
                              icono_accion, icono_tipo, COLOR_TIPO as _CT)
from arte_tama_fondos import dibujar_fondo_hogar, dibujar_fondo_hogar_velado, dibujar_fondo_arena, precalentar
from nucleo import aclarar, oscurecer

TIPOS = ["agua", "viento", "fuego", "hielo", "tierra", "electrico"]
ESPECIES = ["delfin", "tortuga", "pulpo", "mariposa", "ardilla", "buho", "dragon", "lobo", "fenix",
            "pinguino", "oso", "ciervo", "armadillo", "topo", "escarabajo", "raton", "gato", "rana"]
TIPO_DE = {e: TIPOS[i // 3] for i, e in enumerate(ESPECIES)}
COLOR_TIPO = dict(_CT)
NOMBRE_TIPO = {"agua": "Agua", "viento": "Viento", "fuego": "Fuego", "hielo": "Hielo", "tierra": "Tierra", "electrico": "Eléctrico"}
ACCIONES = ["comer", "jugar", "limpiar", "dormir", "curar", "entrenar", "cuaderno", "huevos", "volver"]
ALTO_ETAPA = (120, 165, 215, 270)

# ---------------------------------------------------------------- despacho de mascotas
DIBUJOS = {}
for _m in ("arte_tama_agua_viento", "arte_tama_fuego_hielo", "arte_tama_tierra_electrico"):
    try:
        _mod = __import__(_m)
        DIBUJOS.update(getattr(_mod, "DIBUJOS", {}))
    except Exception:  # falta el modulo o tiene un error: se usa el marcador provisional
        pass


def _provisional(p, especie, etapa, cx, cy, escala, t, estado, dir, silueta):
    tipo = TIPO_DE.get(especie, "agua")
    col = COLOR_TIPO[tipo]
    etapa = max(0, min(3, int(etapa)))
    h = ALTO_ETAPA[etapa] * escala
    w = h * 0.9
    bob = rebote(t, 2.2, 3 * escala)
    sq = respirar(t, 2.0, 0.03)
    w *= 2 - sq
    h *= sq
    sombra(p, cx, cy + h * 0.5, w * 0.9)
    s = pygame.Surface((int(w + 20), int(h + 20)), pygame.SRCALPHA)
    r = pygame.Rect(10, 10, int(w), int(h))
    pygame.draw.ellipse(s, col, r)
    pygame.draw.ellipse(s, aclarar(col, 0.45), (r.x + w * 0.15, r.y + h * 0.58, w * 0.7, h * 0.32))
    pygame.draw.ellipse(s, oscurecer(col, 0.5), r, max(2, int(4 * escala)))
    if silueta:
        s = silueta_de(s)
    else:
        for i in range(etapa):
            pygame.draw.circle(s, aclarar(col, 0.5), (int(r.centerx + (i - (etapa - 1) / 2) * w * 0.22), int(r.y + 2)), max(3, int(8 * escala)))
        ojos(s, r.centerx + dir * w * 0.1, r.y + h * 0.4, w * 0.36, max(3, w * 0.09), estado, t, dir=dir)
        boca(s, r.centerx + dir * w * 0.1, r.y + h * 0.58, w * 0.18, estado, t)
    if estado == "golpeado":
        cx += math.sin(t * 40) * 4 * escala
    p.blit(s, (cx - s.get_width() / 2, cy - s.get_height() / 2 + bob))
    if estado == "evoluciona":
        glow(p, cx, cy, h * 0.9, (255, 240, 180), 160)


def dibujar_mascota(p, especie, etapa, cx, cy, escala=1.0, t=0.0, estado="normal", dir=1, silueta=False):
    """Dibuja la mascota con (cx,cy) = centro del cuerpo. dir=1 mira a la derecha."""
    fn = DIBUJOS.get(especie)
    if fn is None:
        fn = _provisional
    fn(p, int(etapa), cx, cy, escala, t, estado, dir, silueta) if fn is not _provisional else fn(p, especie, etapa, cx, cy, escala, t, estado, dir, silueta)


__all__ = [
    "TIPOS", "ESPECIES", "TIPO_DE", "COLOR_TIPO", "NOMBRE_TIPO", "ACCIONES", "dibujar_mascota", "dibujar_huevo", "dibujar_cascaras",
    "dibujar_ataque_basico", "dibujar_impacto", "dibujar_carga", "dibujar_ataque_cargado", "dibujar_guia", "puntos_guia",
    "dibujar_icono_tipo", "dibujar_icono_accion", "dibujar_fondo_hogar", "dibujar_fondo_hogar_velado", "dibujar_fondo_arena", "dibujar_caca",
    "dibujar_nube_estado", "dibujar_aura_evolucion", "precalentar", "trazo_guia", "DIBUJOS",
]
