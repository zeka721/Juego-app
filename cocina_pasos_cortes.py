"""Pasos de cocina de CORTE: cortar, pelar, rayar, extraer, exprimir (v2, ver CONTRATO_COCINA.md).

Todos se completan SOLO moviendo el cursor (la herramienta es el cursor). Sin castigo: si se acaba el tiempo el
paso termina con calidad = max(0.25, progreso). Claves de `spec` usadas: h, ing (ingrediente), herr (herramienta,
opcional: "cuchillo"/"tijera" en cortar), tazon (letra del cuenco donde queda el resultado: "A".."F").
  cortar    ing: pan, zanahoria... -> cuchillo; alga, fideos, pasta, langostino -> tijera (o spec["herr"]).
  pelar     ing: zanahoria, papa, pepino... (verdura que gira).
  rayar     ing: queso, chocolate, nueces (virutas a un cuenco).
  extraer   ing: pescado (descamar con cuchara) o langostino (4 secciones de cascara: cortar y tirar).
  exprimir  ing: naranja, limon... (cursor gira alrededor de la fruta).
"""

import math
import random

import pygame

from ajustes import ANCHO, ALTO
from nucleo import escribir, V2
from cocina_base import Paso, paso, AREA

CX = ANCHO // 2

# ----------------------------------------------------------------------------- datos de arte
COLORES = {
    "zanahoria": (242, 140, 40), "papa": (205, 165, 105), "tomate": (225, 60, 50), "lechuga": (120, 200, 90),
    "maiz": (245, 205, 60), "calabaza": (240, 150, 50), "cebolla": (205, 120, 165), "pimiento": (225, 55, 45),
    "espinaca": (60, 150, 75), "pepino": (85, 175, 90), "alga": (50, 120, 80), "fideos": (245, 215, 140),
    "pasta": (245, 215, 140), "langostino": (250, 140, 100), "pan": (225, 175, 100), "queso": (250, 205, 80),
    "chocolate": (110, 65, 40), "nueces": (150, 105, 60), "pescado": (110, 150, 185), "naranja": (250, 165, 40),
    "limon": (245, 225, 80), "manzana": (220, 70, 60), "carne": (190, 60, 60), "pollo": (240, 200, 160),
    "calamar": (235, 170, 185),
}
INTERIOR = {"zanahoria": (252, 190, 100), "papa": (245, 232, 170), "pepino": (200, 235, 160),
            "calabaza": (255, 205, 110), "cebolla": (250, 235, 235), "tomate": (245, 140, 120),
            "pimiento": (250, 200, 160), "manzana": (250, 240, 200)}
NOMBRES = {"zanahoria": "la zanahoria", "papa": "la papa", "tomate": "el tomate", "lechuga": "la lechuga",
           "maiz": "el maíz", "calabaza": "la calabaza", "cebolla": "la cebolla", "pimiento": "el pimiento",
           "espinaca": "la espinaca", "pepino": "el pepino", "alga": "el alga", "fideos": "los fideos",
           "pasta": "la pasta", "langostino": "el langostino", "pan": "el pan", "queso": "el queso",
           "chocolate": "el chocolate", "nueces": "las nueces", "pescado": "el pescado", "naranja": "la naranja",
           "limon": "el limón", "manzana": "la manzana", "carne": "la carne", "pollo": "el pollo",
           "calamar": "el calamar", "pasta_cocida": "la pasta"}
TIJERA = ("alga", "fideos", "pasta", "pasta_cocida", "langostino")


def col_ing(ing, defecto=(200, 200, 200)):
    c = COLORES.get(ing)
    if c:
        return c
    try:
        import catalogo
        return tuple(catalogo.info(ing)["color"])
    except Exception:
        return defecto


def nombre_ing(ing):
    if ing in NOMBRES:
        return NOMBRES[ing]
    try:
        import catalogo
        return "el " + catalogo.info(ing)["nombre"].lower()
    except Exception:
        return "el ingrediente"


def _mez(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _osc(c, f=0.3):
    return tuple(max(0, int(v * (1 - f))) for v in c)


def _cla(c, f=0.35):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c)


def _cursor_pos(ctrl):
    return V2(ctrl.pos)


# ----------------------------------------------------------------------------- herramientas (arte propio)
ESC_HERR = 1.5          # las herramientas se dibujan grandes (ninos)

def dibujar_herr(p, nombre, x, y, pres=0.0, abierto=0.0, ang=0.0, t=0.0):
    """Dibuja la herramienta con su punto de accion en (x, y). Primero intenta cocina_herramientas.dibujar_herr."""
    if nombre != "mano":
        try:
            import cocina_herramientas as ch
            tam = 150
            # herramientas de punta: la punta (abajo del cuadro) cae en el cursor; rallador/exprimidor: centro
            dy = 0 if nombre in ("rallador", "exprimidor") else -tam * 0.5 + 6
            ch.dibujar_herr(p, nombre, int(x), int(y + dy), tam, ang)
            return
        except Exception:
            pass
    s = pygame.Surface((220, 240), pygame.SRCALPHA)
    ox, oy = 110, 170                                   # punto de accion dentro de s
    f = _FUNC_HERR.get(nombre, _h_cuchara)
    f(s, ox, oy, pres, abierto, t)
    E = ESC_HERR
    s = pygame.transform.smoothscale(s, (int(220 * E), int(240 * E)))
    ox, oy = ox * E, oy * E
    if ang:
        s2 = pygame.transform.rotozoom(s, ang, 1.0)
        v = V2(ox - s.get_width() / 2, oy - s.get_height() / 2).rotate(-ang)
        p.blit(s2, s2.get_rect(center=(int(x - v.x), int(y - v.y))))
    else:
        p.blit(s, (int(x - ox), int(y - oy)))


def _sombra(s, ox, oy, rx=34, ry=9):
    sh = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 60), sh.get_rect())
    s.blit(sh, (ox - rx, oy - ry + 4))


def _h_cuchillo(s, ox, oy, pres, ab, t):
    """Cuchillo de chef: el filo esta abajo y el punto de accion es el centro del filo."""
    ang = -pres * 8
    pts = [(-52, 0), (46, 0), (50, -8), (46, -66), (-46, -70), (-50, -30)]
    pts = [(ox + x, oy + y) for x, y in pts]
    pygame.draw.polygon(s, (205, 212, 225), pts)
    pygame.draw.polygon(s, (110, 118, 135), pts, 3)
    pygame.draw.line(s, (245, 248, 255), (ox - 40, oy - 56), (ox + 38, oy - 56), 4)
    pygame.draw.rect(s, (130, 85, 50), (ox - 34, oy - 150, 66, 82), border_radius=14)
    pygame.draw.rect(s, (80, 50, 30), (ox - 34, oy - 150, 66, 82), 3, border_radius=14)
    for i in range(3):
        pygame.draw.circle(s, (230, 200, 120), (ox - 2, oy - 128 + i * 24), 5)


def _h_tijera(s, ox, oy, pres, ab, t):
    """Tijera: las puntas estan abajo (punto de accion). `ab` 0..1 = apertura."""
    a = 6 + ab * 22
    piv = (ox, oy - 62)
    for lado in (-1, 1):
        punta = (ox + lado * a, oy)
        pygame.draw.line(s, (110, 118, 135), piv, punta, 14)
        pygame.draw.line(s, (215, 222, 235), piv, punta, 9)
        mango = (ox - lado * 34, oy - 140)
        pygame.draw.line(s, (200, 60, 70), piv, mango, 11)
        pygame.draw.circle(s, (230, 80, 90), (mango[0] - lado * 8, mango[1] - 8), 22, 8)
    pygame.draw.circle(s, (70, 70, 90), piv, 7)


def _h_pelador(s, ox, oy, pres, ab, t):
    """Pelador: punto de accion en la hojita de abajo."""
    pygame.draw.rect(s, (130, 85, 50), (ox - 15, oy - 160, 30, 86), border_radius=12)
    pygame.draw.rect(s, (80, 50, 30), (ox - 15, oy - 160, 30, 86), 3, border_radius=12)
    pygame.draw.polygon(s, (190, 198, 212), [(ox - 15, oy - 82), (ox + 15, oy - 82), (ox + 40, oy - 30),
                                              (ox + 40, oy), (ox - 40, oy), (ox - 40, oy - 30)])
    pygame.draw.polygon(s, (100, 108, 125), [(ox - 15, oy - 82), (ox + 15, oy - 82), (ox + 40, oy - 30),
                                              (ox + 40, oy), (ox - 40, oy), (ox - 40, oy - 30)], 3)
    pygame.draw.rect(s, (60, 60, 80), (ox - 20, oy - 26, 40, 16), border_radius=6)
    pygame.draw.rect(s, (235, 240, 250), (ox - 24, oy - 6, 48, 6))


def _h_rallador(s, ox, oy, pres, ab, t):
    """Rallador plano: punto de accion en el centro de la placa."""
    r = pygame.Rect(ox - 52, oy - 76, 104, 150)
    pygame.draw.rect(s, (190, 198, 212), r, border_radius=14)
    pygame.draw.rect(s, (100, 108, 125), r, 4, border_radius=14)
    for i in range(5):
        for j in range(7):
            pygame.draw.ellipse(s, (90, 98, 118), (r.x + 14 + i * 18 - (j % 2) * 8, r.y + 16 + j * 19, 11, 8))
    pygame.draw.rect(s, (200, 60, 70), (ox - 14, oy - 128, 28, 54), border_radius=10)
    pygame.draw.rect(s, (130, 30, 40), (ox - 14, oy - 128, 28, 54), 3, border_radius=10)


def _h_cuchara(s, ox, oy, pres, ab, t):
    """Cuchara con la que se raspa: la cabeza esta en el punto de accion."""
    pygame.draw.line(s, (130, 135, 150), (ox + 10, oy - 6), (ox + 60, oy - 120), 14)
    pygame.draw.line(s, (225, 230, 240), (ox + 10, oy - 6), (ox + 60, oy - 120), 9)
    pygame.draw.ellipse(s, (130, 135, 150), (ox - 36, oy - 22, 72, 44))
    pygame.draw.ellipse(s, (225, 230, 240), (ox - 31, oy - 18, 62, 36))
    pygame.draw.ellipse(s, (255, 255, 255), (ox - 20, oy - 12, 26, 12))


def _h_exprimidor(s, ox, oy, pres, ab, t):
    """Exprimidor (cono estriado visto desde arriba) con mango."""
    pygame.draw.line(s, (200, 60, 70), (ox, oy), (ox + 70, oy - 90), 18)
    pygame.draw.circle(s, (70, 150, 220), (ox, oy), 44)
    pygame.draw.circle(s, (30, 80, 140), (ox, oy), 44, 4)
    for k in range(10):
        a = k * math.tau / 10 + t * 0
        pygame.draw.line(s, (200, 230, 255), (ox, oy), (ox + 40 * math.cos(a), oy + 40 * math.sin(a)), 3)
    pygame.draw.circle(s, (230, 245, 255), (ox, oy), 12)


def _h_mano(s, ox, oy, pres, ab, t):
    """Manita (palma + dedos) para tirar; el punto de accion es el centro de la palma."""
    piel = (250, 205, 170)
    borde = (170, 110, 80)
    for k, a in enumerate((-70, -35, 0, 35)):
        r = math.radians(a - 90)
        e = (ox + 40 * math.cos(r), oy + 40 * math.sin(r))
        pygame.draw.line(s, borde, (ox, oy), e, 24)
        pygame.draw.line(s, piel, (ox, oy), e, 18)
    pygame.draw.circle(s, piel, (ox, oy), 36)
    pygame.draw.circle(s, borde, (ox, oy), 36, 3)
    pygame.draw.line(s, borde, (ox - 30, oy + 22), (ox - 44, oy + 6), 22)
    pygame.draw.line(s, piel, (ox - 30, oy + 22), (ox - 44, oy + 6), 16)


_FUNC_HERR = {"cuchillo": _h_cuchillo, "tijera": _h_tijera, "pelador": _h_pelador, "rallador": _h_rallador,
              "cuchara": _h_cuchara, "exprimidor": _h_exprimidor, "mano": _h_mano}


# ----------------------------------------------------------------------------- arte comun
def cuenco(p, x, y, w, letra=None, color=None, nivel=0.0, pila=None, front_only=False):
    """Cuenco visto de frente con borde en (x, y)=centro del borde superior. `pila`: lista de (dx, dy, color)."""
    h = int(w * 0.46)
    r = pygame.Rect(0, 0, w, h * 2)
    r.midtop = (x, y - h)
    pygame.draw.ellipse(p, (60, 40, 30), (x - w // 2 + 6, y + h - 12, w - 12, 22))      # sombra
    base = pygame.Rect(x - w // 2, y - h // 2 + 2, w, h * 2 - 10)
    if not front_only:
        pygame.draw.ellipse(p, (240, 240, 250), (x - w // 2, y - h // 2, w, h))         # interior (aro)
        inter = (x - w // 2 + 6, y - h // 2 + 5, w - 12, h - 10)
        pygame.draw.ellipse(p, (210, 215, 232), inter)
    if pila:
        for dx, dy, c in pila:
            pygame.draw.circle(p, c, (int(x + dx), int(y + dy)), 5)
    # cuerpo del cuenco
    cuerpo = [(x - w // 2, y), (x + w // 2, y), (x + w // 2 - 28, y + h), (x - w // 2 + 28, y + h)]
    pygame.draw.polygon(p, (250, 250, 255), cuerpo)
    pygame.draw.ellipse(p, (250, 250, 255), (x - w // 2 + 28, y + h - 14, w - 56, 28))
    pygame.draw.polygon(p, (110, 130, 190), cuerpo, 3)
    pygame.draw.arc(p, (110, 130, 190), (x - w // 2 + 28, y + h - 14, w - 56, 28), math.pi, math.tau, 3)
    if pila:
        for dx, dy, c in pila:       # lo que sobresale por delante del borde
            if dy > 6:
                pygame.draw.circle(p, c, (int(x + dx), int(y + dy * 0.2)), 5)
    if not front_only:
        pygame.draw.ellipse(p, (110, 130, 190), (x - w // 2, y - h // 2, w, h), 3)
    if letra:
        pygame.draw.circle(p, (255, 200, 70), (x, y + h // 2 + 4), 17)
        pygame.draw.circle(p, (150, 100, 20), (x, y + h // 2 + 4), 17, 3)
        escribir(p, pygame.font.SysFont(None, 28, bold=True), letra, x, y + h // 2 + 4, (90, 55, 10), contorno=None)


def cuenco_chico(p, spec, listo=0.0, ing=None, estado="cortado"):
    """Cuencito de destino abajo a la derecha, con su letra y, si hay avance, el ingrediente preparado."""
    letra = spec.get("tazon")
    if listo > 0 and ing:
        try:
            import cocina_ingredientes as ci
            ci.dibujar_ing(p, ing, 1120, 560, 70 + 16 * min(1.0, listo), estado)
        except Exception:
            c = col_ing(ing)
            for i in range(int(8 * listo)):
                pygame.draw.circle(p, c, (1120 + (i % 4) * 22 - 33, 570 - (i // 4) * 8), 9)
                pygame.draw.circle(p, _osc(c, .3), (1120 + (i % 4) * 22 - 33, 570 - (i // 4) * 8), 9, 2)
    cuenco(p, 1120, 585, 150, letra, front_only=True)


def sombra_suave(p, rect, alfa=70):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alfa), s.get_rect())
    p.blit(s, (rect[0], rect[1]))


def tabla(p, rect):
    r = pygame.Rect(rect)
    sombra_suave(p, (r.x + 8, r.bottom - 14, r.w - 16, 36))
    pygame.draw.rect(p, (200, 150, 90), r, border_radius=26)
    pygame.draw.rect(p, (150, 100, 55), r, 5, border_radius=26)
    for i in range(1, 4):
        yy = r.y + i * r.h // 4
        pygame.draw.line(p, (185, 135, 78), (r.x + 22, yy), (r.right - 22, yy), 2)
    pygame.draw.circle(p, (150, 100, 55), (r.right - 40, r.y + 30), 11, 4)


def guia_texto(p, f, texto, y=148):
    escribir(p, f.normal, texto, CX, y, (255, 255, 255), contorno=(110, 70, 40))


# ----------------------------------------------------------------------------- sprites (cortar)
# (ancho, alto) NATURAL de lo que se corta sobre la tabla cuadrada: nunca se estira para llenar la tabla.
# Redondos: ancho == alto (circulo). Alargados: se ponen en horizontal con su proporcion real.
FORMAS = {
    "zanahoria": (340, 110), "pepino": (340, 100), "maiz": (300, 100), "pan": (340, 115), "alga": (340, 110),
    "fideos": (300, 100), "pasta": (300, 100), "pasta_cocida": (300, 100), "langostino": (320, 120),
    "pescado": (340, 140), "papa": (320, 230), "limon": (310, 220), "carne": (300, 180), "pollo": (290, 190),
    "queso": (300, 170),
}
FORMA_REDONDA = (290, 290)          # tomate, naranja, manzana, cebolla, pimiento, calabaza, lechuga...


def forma_ing(ing):
    return FORMAS.get(ing, FORMA_REDONDA)


def sprite_largo(ing, W=None, H=None):
    if W is None:
        W, H = forma_ing(ing)
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    c = col_ing(ing)
    oc = _osc(c, 0.35)
    if ing == "zanahoria":
        pts = [(0, H * 0.18), (W * 0.8, H * 0.40), (W, H * 0.5), (W * 0.8, H * 0.60), (0, H * 0.82)]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, oc, pts, 4)
        for i in range(6):
            x = 40 + i * W * 0.12
            yy = H * (0.3 + i * 0.02)
            pygame.draw.line(s, _osc(c, .18), (x, yy), (x + 14, yy), 3)
    elif ing in ("pepino", "maiz"):
        r = pygame.Rect(0, int(H * .1), W, int(H * .8))
        pygame.draw.rect(s, c, r, border_radius=int(H * .38))
        pygame.draw.rect(s, _cla(c, .25), (30, int(H * .18), W - 60, int(H * .16)), border_radius=10)
        pygame.draw.rect(s, oc, r, 4, border_radius=int(H * .38))
        rnd = random.Random(3)
        for _ in range(26):
            x, y = rnd.randint(30, W - 30), rnd.randint(int(H * .3), int(H * .8) - 12)
            if ing == "pepino":
                pygame.draw.circle(s, _osc(c, .25), (x, y), 3)
            else:
                pygame.draw.ellipse(s, (255, 235, 130), (x, y, 14, 14))
    elif ing == "pan":
        pygame.draw.rect(s, (205, 150, 80), (0, int(H * .22), W, int(H * .68)), border_radius=int(H * .3))
        pygame.draw.rect(s, (235, 190, 110), (8, int(H * .12), W - 16, int(H * .6)), border_radius=int(H * .3))
        for i in range(5):
            x = W * (0.14 + i * 0.18)
            pygame.draw.line(s, (180, 120, 60), (x, H * .26), (x + 36, H * .5), 7)
        pygame.draw.rect(s, (150, 100, 50), (0, int(H * .12), W, int(H * .78)), 4, border_radius=int(H * .3))
    elif ing == "alga":
        pts_a, pts_b = [], []
        for i in range(0, W + 1, 12):
            y = H * 0.5 + math.sin(i / 38.0) * H * 0.14
            pts_a.append((i, y - H * 0.24))
            pts_b.append((i, y + H * 0.24))
        pygame.draw.polygon(s, c, pts_a + pts_b[::-1])
        pygame.draw.polygon(s, _osc(c, .4), pts_a + pts_b[::-1], 4)
        for i in range(30, W - 20, 54):
            y = H * 0.5 + math.sin(i / 38.0) * H * 0.14
            pygame.draw.line(s, _cla(c, .3), (i, y - 22), (i + 8, y + 22), 3)
    elif ing in ("fideos", "pasta", "pasta_cocida"):
        for k in range(7):
            y0 = H * (0.2 + 0.6 * k / 6)
            pts = [(i, y0 + math.sin(i / 30.0 + k) * 4) for i in range(8, W - 8, 10)]
            pygame.draw.lines(s, _osc(c, .2), False, pts, 14)
            pygame.draw.lines(s, _cla(c, .15), False, pts, 9)
    elif ing == "langostino":
        pts = [(W * 0.08 + i * W * 0.84 / 24, H * 0.62 - math.sin(i / 24 * math.pi) * H * 0.3) for i in range(25)]
        pygame.draw.lines(s, oc, False, pts, int(H * 0.46))
        pygame.draw.lines(s, c, False, pts, int(H * 0.38))
        for i in range(2, 24, 3):
            x, y = pts[i]
            pygame.draw.line(s, oc, (x, y - H * 0.18), (x, y + H * 0.18), 4)
        pygame.draw.circle(s, (30, 30, 40), (int(pts[-1][0]), int(pts[-1][1] - 6)), 7)
    elif ing == "pescado":
        azul = (110, 150, 185)
        pygame.draw.polygon(s, _osc(azul, .1), [(W * .24, H * .5), (0, H * .06), (W * .07, H * .5), (0, H * .94)])
        pygame.draw.polygon(s, _osc(azul, .4), [(W * .24, H * .5), (0, H * .06), (W * .07, H * .5), (0, H * .94)], 3)
        pygame.draw.polygon(s, _osc(azul, .1), [(W * .46, H * .2), (W * .6, 0), (W * .74, H * .2)])
        pygame.draw.polygon(s, _osc(azul, .1), [(W * .5, H * .8), (W * .6, H), (W * .7, H * .8)])
        body = pygame.Rect(int(W * .2), int(H * .12), int(W * .79), int(H * .76))
        pygame.draw.ellipse(s, azul, body)
        pygame.draw.ellipse(s, _cla(azul, .35), (body.x + body.w * .12, body.y + body.h * .62, body.w * .6, body.h * .22))
        pygame.draw.ellipse(s, _osc(azul, .4), body, 4)
        for i in range(5):
            x = body.x + 40 + i * 42
            pygame.draw.arc(s, _osc(azul, .3), (x, body.y + 24, 34, 34), 1.5, 4.6, 2)
            pygame.draw.arc(s, _osc(azul, .3), (x - 18, body.y + 52, 34, 34), 1.5, 4.6, 2)
        pygame.draw.circle(s, (255, 255, 255), (int(W * .9), int(H * .42)), 9)
        pygame.draw.circle(s, (30, 30, 50), (int(W * .91), int(H * .42)), 5)
    elif ing in ("carne", "pollo", "queso"):
        r = pygame.Rect(4, 4, W - 8, H - 8)
        pygame.draw.rect(s, c, r, border_radius=int(H * .3))
        pygame.draw.rect(s, _cla(c, .3), (r.x + 18, r.y + 12, r.w * .5, 12), border_radius=6)
        pygame.draw.rect(s, oc, r, 4, border_radius=int(H * .3))
        if ing == "queso":
            rnd = random.Random(9)
            for _ in range(6):
                pygame.draw.circle(s, _osc(c, .22), (rnd.randint(30, W - 30), rnd.randint(30, H - 30)), rnd.randint(7, 12))
    else:                                                    # redondos: circulo (o oval natural: papa, limon)
        r = pygame.Rect(4, 4, W - 8, H - 8)
        pygame.draw.ellipse(s, c, r)
        pygame.draw.ellipse(s, _cla(c, .3), (int(W * .16), int(H * .16), int(W * .34), int(H * .16)))
        pygame.draw.ellipse(s, oc, r, 4)
        if ing == "cebolla":
            for k in range(1, 4):
                pygame.draw.ellipse(s, _osc(c, .12), r.inflate(-k * W * 0.2, -k * H * 0.2), 2)
        elif ing in ("tomate", "pimiento"):
            pygame.draw.circle(s, (70, 150, 70), (W // 2, int(H * 0.1)), int(H * 0.07))
        elif ing in ("naranja", "manzana", "limon"):
            rnd = random.Random(11)
            for _ in range(22):
                a, d = rnd.uniform(0, math.tau), rnd.uniform(0.2, 0.85)
                pygame.draw.circle(s, _osc(c, .15), (int(W / 2 + math.cos(a) * d * W / 2),
                                                     int(H / 2 + math.sin(a) * d * H / 2)), 2)
            pygame.draw.circle(s, (80, 150, 70), (W // 2, int(H * 0.08)), int(H * 0.04))
        elif ing == "papa":
            rnd = random.Random(2)
            for _ in range(10):
                pygame.draw.circle(s, _osc(c, .25), (rnd.randint(int(W * .2), int(W * .8)),
                                                     rnd.randint(int(H * .25), int(H * .8))), 4)
    return s


# =============================================================================================== CORTAR
@paso("cortar")
class Cortar(Paso):
    """Tabla CUADRADA. Pasa el cuchillo (o la tijera) de arriba a abajo por cada linea de corte; se repite en
    varias piezas (rondas). Lo que se corta conserva su proporcion natural (redondo = circulo, largo = horizontal)."""

    RONDAS = 5
    TAB = 420
    PAUSA = 0.7

    def iniciar(self):
        self.ing = self.ing or "zanahoria"
        self.herr_n = self.herr if self.herr in ("cuchillo", "tijera") else (
            "tijera" if self.ing in TIJERA else "cuchillo")
        self.titulo = "¡Corta %s!" % nombre_ing(self.ing)
        self.n = 5 + int(round(self.dif * 0.2))                    # 5..7 cortes por pieza
        self.R = self.RONDAS + (1 if self.dif < 4 else 0)       # 5-6 piezas
        self.ronda = 0
        self.W, self.H = forma_ing(self.ing)
        self.tab = pygame.Rect(0, 0, self.TAB, self.TAB)           # tabla cuadrada
        self.tab.center = (CX, 402)
        self.cy = self.tab.centery
        self.x0 = CX - self.W // 2
        self.sp = self.W / (self.n + 1.0)
        self.gx = [self.x0 + self.sp * (i + 1) for i in range(self.n)]
        self.zona = min(0.5 * self.sp, 0.46 * self.sp * self.mods.alc)   # mitad del ancho de cada linea
        self.hh = max(45.0, self.H * 0.4)
        self.hecho = [False] * self.n
        self.arm = {}
        self.err = []
        self.sprite = sprite_largo(self.ing, self.W, self.H)
        self.cpos = V2(CX, 250)
        self.pres = 0.0
        self.pausa = 0.0
        self.fin = False

    def tiempo_base(self):
        return 58.0 - 0.5 * self.dif

    def _nueva_ronda(self):
        self.hecho = [False] * self.n
        self.arm = {}

    def actualizar_paso(self, dt, ctrl):
        pos = _cursor_pos(ctrl)
        self.cpos = pos
        self.pres = max(0.0, self.pres - dt * 4)
        if self.fin:
            return
        if self.pausa > 0:
            self.pausa -= dt
            if self.pausa <= 0:
                self._nueva_ronda()
            return
        for i, gx in enumerate(self.gx):
            if self.hecho[i]:
                continue
            if abs(pos.x - gx) > self.zona:
                self.arm.pop(i, None)
                continue
            lado = -1 if pos.y < self.cy - self.hh else (1 if pos.y > self.cy + self.hh else 0)
            if lado == 0:
                continue
            if i not in self.arm:
                self.arm[i] = lado
            elif self.arm[i] != lado:
                self.hecho[i] = True
                self.err.append(abs(pos.x - gx) / max(1.0, self.zona))
                self.pres = 1.0
                self.sonidos.reproducir("corte")
                self.sumar_particulas(gx, self.cy, _cla(col_ing(self.ing), .3), 8)
        self.prog = (self.ronda + sum(self.hecho) / float(self.n)) / self.R
        if all(self.hecho):
            self.ronda += 1
            if self.ronda >= self.R:
                self.fin = True
                self.prog = 1.0
                self.terminar(None, "¡Qué cortes tan parejos!")
            else:
                self.pausa = self.PAUSA
                self.texto_flotante("¡Otra pieza!", CX, self.tab.y - 4)

    def terminar(self, calidad=None, mensaje=""):
        if calidad is None:
            calidad = 1.0 - 0.2 * (sum(self.err) / max(1, len(self.err)))
        super().terminar(calidad, mensaje)

    def _trozos(self, p, ox=0, oy=0):
        """Dibuja la pieza cortada en trozos (separados un poco) con su proporcion natural."""
        bordes = [self.x0] + self.gx + [self.x0 + self.W]
        total = sum(self.hecho)
        gap = min(15.0, 60.0 / self.n)
        top = self.cy - self.H // 2
        for j in range(self.n + 1):
            izq = sum(1 for i in range(j) if self.hecho[i])
            off = izq * gap - total * gap / 2
            w = int(bordes[j + 1] - bordes[j])
            area = pygame.Rect(int(bordes[j] - self.x0), 0, w, self.H)
            sombra_suave(p, (bordes[j] + off + 4 + ox, top + self.H - 16 + oy, w - 8, 22), 28)
            p.blit(self.sprite, (bordes[j] + off + ox, top + oy), area)
            for xx, hecho in ((bordes[j], j > 0 and self.hecho[j - 1]), (bordes[j + 1], j < self.n and self.hecho[j])):
                if hecho:
                    xe = (bordes[j] if xx == bordes[j] else bordes[j + 1]) + off + ox
                    pygame.draw.line(p, (255, 250, 235), (xe, top + 8 + oy), (xe, top + self.H - 8 + oy), 3)

    def dibujar_paso(self, p):
        f = self.f
        tabla(p, self.tab)
        if self.pausa > 0:                                   # los trozos viajan al cuenco
            e = 1.0 - self.pausa / self.PAUSA
            tmp = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            self._trozos(tmp)
            sc = 1.0 - 0.6 * e
            tmp.set_alpha(int(255 * (1 - e * e)))
            r = tmp.get_rect()
            cx0, cy0 = CX, self.cy
            tx, ty = 1120, 560
            nx, ny = cx0 + (tx - cx0) * e, cy0 + (ty - cy0) * e
            sub = tmp.subsurface(pygame.Rect(CX - 260, self.cy - 170, 520, 340))
            sub = pygame.transform.rotozoom(sub, 0, sc)
            p.blit(sub, sub.get_rect(center=(int(nx), int(ny))))
        else:
            self._trozos(p)
        top = self.tab.y
        if not self.fin and self.pausa <= 0:
            for i, gx in enumerate(self.gx):
                if self.hecho[i]:
                    continue
                pul = 0.5 + 0.5 * math.sin(self.t * 5 + i)
                c = (255, int(90 + 60 * pul), int(90 + 40 * pul))
                for yy in range(top + 12, self.tab.bottom - 22, 22):
                    pygame.draw.line(p, c, (gx, yy), (gx, yy + 11), 4)
                pygame.draw.polygon(p, c, [(gx - 12, top - 26), (gx + 12, top - 26), (gx, top - 6)])
        guia_texto(p, f, "Pasa %s de arriba a abajo por cada línea" % ("la tijera" if self.herr_n == "tijera"
                                                                         else "el cuchillo"), y=136)
        escribir(p, f.chica, "Pieza %d de %d" % (min(self.ronda + 1, self.R), self.R), self.tab.x - 90, self.tab.y + 20,
                 (255, 255, 255), contorno=(110, 70, 40))
        cuenco_chico(p, self.spec, self.prog, self.ing, "cortado")
        px, py = self.cpos.x, self.cpos.y + 10
        ab = (0.5 + 0.5 * math.sin(self.t * 12)) if self.herr_n == "tijera" and self.pres > 0 else \
            (0.6 if self.herr_n == "tijera" else 0)
        dibujar_herr(p, self.herr_n, px, py + 6 * self.pres, pres=self.pres, abierto=ab, t=self.t)



# =============================================================================================== PELAR
ALTO_PELAR = {"zanahoria": 330, "pepino": 330}
ALTO_PELAR_REDONDO = 260


def _perfil(ing, u):
    """Radio (px) del ingrediente a lo largo de su altura (u 0..1). Proporciones reales (sin estirar):
    zanahoria y pepino largos y finos; papa oval (mas ancha que alta); el resto, esfera (circulo)."""
    if ing == "zanahoria":
        return 56 * (1 - 0.86 * u ** 0.95) + 4
    if ing == "pepino":
        e = max(0.0, abs(2 * u - 1) - 0.86) / 0.14
        return 46 * math.sqrt(max(0.0, 1 - e * e)) + 3
    base = ALTO_PELAR_REDONDO / 2.0 * (1.15 if ing == "papa" else 1.0)
    return base * max(0.0, 1 - (2 * u - 1) ** 2) ** 0.5 + 3


@paso("pelar")
class Pelar(Paso):
    """La verdura gira. Sube y baja el pelador sobre ella: cada franja de cascara que pasa se pela."""

    FILA = 6
    LENTOS = {"zanahoria": 15.7, "pepino": 15.0, "papa": 7.2}               # cada franja necesita varias pasadas (avance natural, no instantaneo)

    def iniciar(self):
        self.ing = self.ing or "zanahoria"
        self.titulo = "¡Pela %s!" % nombre_ing(self.ing)
        self.S = 10 + int(round(self.dif * 0.8))                  # franjas alrededor
        self.alto = ALTO_PELAR.get(self.ing, ALTO_PELAR_REDONDO)
        self.top = 400 - self.alto // 2 if self.ing not in ("zanahoria", "pepino") else 232
        self.cx, self.cy = CX, self.top + self.alto // 2
        self.rot = 0.0
        self.pelado = [0.0] * self.S
        self.tol = (52 - 1.2 * self.dif) * self.mods.alc
        self.w = (0.8 + 0.06 * self.dif) * self.mods.lento
        rm = max(20.0, _perfil(self.ing, 0.5))
        # tiempo en que cada franja pasa frente al pelador: depende de lo ancha que sea la verdura
        self.lento = self.LENTOS.get(self.ing, 7.2)
        self.rmax = max(_perfil(self.ing, 0.0), _perfil(self.ing, 0.5), _perfil(self.ing, 0.2))
        self.prev = None
        self.cpos = V2(CX, 250)
        self.tiras = []
        self.acum = 0.0
        self.cascara = col_ing(self.ing)
        self.carne = INTERIOR.get(self.ing, _cla(self.cascara, .65))

    def tiempo_base(self):
        return 58.0 - 0.5 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = _cursor_pos(ctrl)
        self.cpos = pos
        self.rot += self.w * dt
        if self.prev is not None:
            dy = abs(pos.y - self.prev.y)
            if dy > 0.5 and self.top - 30 < pos.y < self.top + self.alto + 30 and abs(pos.x - self.cx) < self.rmax + 40:
                u = max(0.0, min(1.0, (pos.y - self.top) / self.alto))
                r = _perfil(self.ing, u)
                paso_a = dy / (self.alto * 2.0 * self.lento) * self.mods.pot
                gana = 0.0
                for k in range(self.S):
                    th = self.rot + k * math.tau / self.S + math.tau / self.S / 2
                    if math.cos(th) < 0.15 or self.pelado[k] >= 1.0:
                        continue
                    if abs(self.cx + r * math.sin(th) - pos.x) < self.tol:
                        nuevo = min(1.0, self.pelado[k] + paso_a)
                        gana += nuevo - self.pelado[k]
                        self.pelado[k] = nuevo
                if gana > 0:
                    self.acum += gana
                    while self.acum > 0.08:
                        self.acum -= 0.08
                        self._tira(pos)
                    self.prog = sum(self.pelado) / self.S
        self.prev = V2(pos)
        for t in self.tiras:
            if t["y"] < 628:
                t["vy"] += 700 * dt
                t["x"] += t["vx"] * dt
                t["y"] += t["vy"] * dt
                t["a"] += t["va"] * dt
            else:
                t["y"] = 628
        if self.prog >= 0.985:
            self.terminar(1.0, "¡Pelada y lista!")

    def _tira(self, pos):
        self.tiras.append(dict(x=pos.x + random.uniform(20, 50), y=pos.y, vx=random.uniform(30, 140), vy=-160,
                               a=random.uniform(0, 360), va=random.uniform(-200, 200), l=random.randint(26, 46)))
        if len(self.tiras) > 28:
            self.tiras.pop(0)
        if len(self.tiras) % 3 == 0:
            self.sonidos.reproducir("tick")

    def _dib_tira(self, p, t):
        s = pygame.Surface((80, 50), pygame.SRCALPHA)
        n = 9
        pts = [(8 + i * (t["l"] / (n - 1.0)), 25 + math.sin(i * 0.8) * 7) for i in range(n)]
        for q in pts:
            pygame.draw.circle(s, _osc(self.cascara, .3), (int(q[0]), int(q[1])), 6)
        for q in pts:
            pygame.draw.circle(s, self.cascara, (int(q[0]), int(q[1])), 4)
        s = pygame.transform.rotate(s, t["a"])
        p.blit(s, s.get_rect(center=(int(t["x"]), int(t["y"]))))

    def dibujar_paso(self, p):
        f = self.f
        # tabla de abajo con cascaras
        for t in self.tiras:
            self._dib_tira(p, t)
        # franja de sombra bajo la verdura
        sombra_suave(p, (self.cx - 130, self.top + self.alto - 14, 260, 36), 55)
        S = self.S
        paso_th = math.tau / S
        for y in range(0, self.alto, self.FILA):
            u = (y + self.FILA / 2) / self.alto
            r = _perfil(self.ing, u)
            yy = self.top + y
            for k in range(S):
                th = self.rot + k * paso_th
                th2 = th + paso_th
                mid = th + paso_th / 2
                prof = math.cos(mid)
                if prof <= 0:
                    continue
                x1 = r * math.sin(th)
                x2 = r * math.sin(th2)
                a, b = (x1, x2) if x1 < x2 else (x2, x1)
                pel = u < self.pelado[k]
                base = self.carne if pel else self.cascara
                luz = 0.45 + 0.55 * prof
                col = tuple(int(min(255, v * (0.55 + 0.45 * luz) + (20 if pel else 0))) for v in base)
                pygame.draw.rect(p, col, (int(self.cx + a), yy, int(b - a) + 2, self.FILA + 1))
        # contorno
        izq = [(self.cx - _perfil(self.ing, (y + 1) / self.alto), self.top + y) for y in range(0, self.alto, 6)]
        der = [(self.cx + _perfil(self.ing, (y + 1) / self.alto), self.top + y) for y in range(0, self.alto, 6)]
        pygame.draw.lines(p, _osc(self.cascara, .5), False, izq, 4)
        pygame.draw.lines(p, _osc(self.cascara, .5), False, der, 4)
        pygame.draw.line(p, _osc(self.cascara, .5), izq[0], der[0], 4)
        if self.ing == "zanahoria":
            for dx, h in ((-18, 50), (0, 66), (18, 46)):
                pygame.draw.line(p, (70, 160, 70), (self.cx + dx * 0.4, self.top + 4), (self.cx + dx, self.top - h), 10)
                pygame.draw.circle(p, (90, 190, 80), (self.cx + dx, self.top - h), 9)
        guia_texto(p, f, "Sube y baja el pelador sobre la verdura que gira")
        cuenco_chico(p, self.spec, self.prog, self.ing, "pelado")
        dibujar_herr(p, "pelador", self.cpos.x, self.cpos.y, pres=0, t=self.t)


# =============================================================================================== RAYAR
def dibujar_bloque(p, ing, rect, falta):
    """Bloque de comida a rallar. `falta` = fraccion que queda (1 -> entero)."""
    r = pygame.Rect(rect)
    c = col_ing(ing)
    if ing == "nueces":
        rnd = random.Random(5)
        n = max(1, int(round(8 * falta)))
        for i in range(n):
            x = r.x + 30 + (i % 4) * 56 + rnd.randint(-8, 8)
            y = r.bottom - 30 - (i // 4) * 40 + rnd.randint(-6, 6)
            pygame.draw.ellipse(p, c, (x - 28, y - 22, 56, 44))
            pygame.draw.ellipse(p, _osc(c, .35), (x - 28, y - 22, 56, 44), 3)
            pygame.draw.line(p, _osc(c, .35), (x, y - 20), (x, y + 20), 3)
            pygame.draw.arc(p, _cla(c, .3), (x - 16, y - 14, 20, 16), 1.6, 3.2, 3)
        return
    h = max(14, int(r.h * (0.25 + 0.75 * falta)))
    b = pygame.Rect(r.x, r.bottom - h, r.w, h)
    if ing == "chocolate":
        pygame.draw.rect(p, c, b, border_radius=10)
        for i in range(0, b.w, 46):
            pygame.draw.line(p, _osc(c, .35), (b.x + i, b.y + 4), (b.x + i, b.bottom - 4), 3)
        for j in range(0, b.h, 40):
            pygame.draw.line(p, _osc(c, .35), (b.x + 4, b.y + j), (b.right - 4, b.y + j), 3)
        pygame.draw.rect(p, _cla(c, .25), (b.x + 6, b.y + 6, b.w - 12, 8), border_radius=4)
        pygame.draw.rect(p, _osc(c, .5), b, 4, border_radius=10)
        pygame.draw.rect(p, (200, 200, 215), (b.x, b.bottom - h // 3, b.w, h // 3), border_radius=6)
    else:                                                    # queso (bloque con agujeros)
        pygame.draw.rect(p, c, b, border_radius=12)
        pygame.draw.rect(p, _cla(c, .35), (b.x + 6, b.y + 6, b.w - 12, 10), border_radius=5)
        rnd = random.Random(9)
        for _ in range(6):
            x, y = rnd.randint(b.x + 20, b.right - 20), rnd.randint(b.y + 20, max(b.y + 21, b.bottom - 14))
            pygame.draw.circle(p, _osc(c, .22), (x, y), rnd.randint(7, 13))
        pygame.draw.rect(p, _osc(c, .45), b, 4, border_radius=12)


@paso("rayar")
class Rayar(Paso):
    """Sube y baja el rallador sobre el bloque: las virutas caen al cuenco hasta llenarlo."""

    def iniciar(self):
        self.ing = self.ing or "queso"
        self.titulo = "¡Ralla %s!" % nombre_ing(self.ing)
        self.bw, self.bh = 250, 160
        self.by = 385                                # base del bloque
        self.bx = CX
        self.necesita = 9500.0 * (1 + 0.03 * self.dif)
        self.hecho = 0.0
        self.prev = None
        self.cpos = V2(CX, 250)
        self.virutas = []
        self.pila = []
        self.acum = 0.0
        self.sway = 0.0
        self.color = _cla(col_ing(self.ing), .2) if self.ing != "nueces" else (190, 140, 85)

    def tiempo_base(self):
        return 58.0 - 0.5 * self.dif

    def _rect(self):
        return pygame.Rect(int(self.bx - self.bw / 2), self.by - self.bh, self.bw, self.bh)

    def actualizar_paso(self, dt, ctrl):
        pos = _cursor_pos(ctrl)
        self.cpos = pos
        self.bx = CX + self.sway
        self.sway = 150 * (self.dif / 10.0) * math.sin(self.t * 0.8 * self.mods.lento)
        zona = self._rect().inflate(80 * self.mods.alc, 80 * self.mods.alc)
        zona.top -= 40
        if self.prev is not None and zona.collidepoint(pos.x, pos.y):
            dy = abs(pos.y - self.prev.y)
            if dy > 0.5:
                gana = dy * self.mods.pot
                self.hecho += gana
                self.acum += gana
                self.prog = min(1.0, self.hecho / self.necesita)
                while self.acum > 34:
                    self.acum -= 34
                    self.virutas.append(dict(x=pos.x + random.uniform(-40, 40), y=pos.y + 30, vx=random.uniform(-20, 20),
                                             vy=random.uniform(20, 120), c=self.color))
                    if len(self.virutas) % 4 == 0:
                        self.sonidos.reproducir("tick")
        self.prev = V2(pos)
        nv = []
        rnd = random
        for v in self.virutas:
            v["vy"] += 900 * dt
            v["vx"] += (CX - v["x"]) * 2.0 * dt
            v["vx"] *= 0.99
            v["x"] += v["vx"] * dt
            v["y"] += v["vy"] * dt
            if v["y"] >= 508 and abs(v["x"] - CX) < 140:
                if len(self.pila) < 130:
                    self.pila.append((rnd.uniform(-95, 95) * (0.6 + 0.4 * rnd.random()), rnd.uniform(-2, 6),
                                      _mez(v["c"], (255, 255, 255), rnd.uniform(0, 0.25))))
                continue
            if v["y"] < 760:
                nv.append(v)
        self.virutas = nv
        if self.prog >= 1.0:
            self.terminar(1.0, "¡Un montón de virutas!")

    def dibujar_paso(self, p):
        f = self.f
        r = self._rect()
        pygame.draw.ellipse(p, (230, 195, 140), (r.x - 40, self.by - 14, r.w + 80, 40))
        sombra_suave(p, (r.x, self.by - 10, r.w, 30), 60)
        dibujar_bloque(p, self.ing, r, 1.0 - 0.75 * self.prog)
        # cuenco con la pila de virutas
        cuenco(p, CX, 525, 300, self.spec.get("tazon"), pila=None)
        for dx, dy, c in self.pila:
            pygame.draw.circle(p, c, (int(CX + dx * 0.85), int(522 + dy - 6 * (1 - abs(dx) / 100.0))), 6)
        for v in self.virutas:
            pygame.draw.ellipse(p, v["c"], (int(v["x"]) - 6, int(v["y"]) - 3, 13, 7))
        guia_texto(p, f, "Sube y baja el rallador sobre %s" % nombre_ing(self.ing))
        dibujar_herr(p, "rallador", self.cpos.x, self.cpos.y + 8, t=self.t)


# =============================================================================================== EXTRAER
def _pez_cuerpo(p, cx, cy, rx, ry, limpio):
    """Pescado de lado: cola a la izquierda, cabeza a la derecha."""
    azul = (105, 150, 190)
    # cola
    pygame.draw.polygon(p, _osc(azul, .1), [(cx - rx + 20, cy), (cx - rx - 110, cy - 90), (cx - rx - 80, cy),
                                           (cx - rx - 110, cy + 90)])
    pygame.draw.polygon(p, _osc(azul, .4), [(cx - rx + 20, cy), (cx - rx - 110, cy - 90), (cx - rx - 80, cy),
                                           (cx - rx - 110, cy + 90)], 4)
    # aletas
    pygame.draw.polygon(p, _osc(azul, .1), [(cx - 70, cy - ry + 8), (cx + 30, cy - ry - 62), (cx + 90, cy - ry + 6)])
    pygame.draw.polygon(p, _osc(azul, .1), [(cx - 40, cy + ry - 8), (cx + 20, cy + ry + 48), (cx + 70, cy + ry - 8)])
    pygame.draw.ellipse(p, (240, 205, 195), (cx - rx, cy - ry, rx * 2, ry * 2))          # carne (limpia)
    pygame.draw.ellipse(p, (215, 175, 170), (cx - rx, cy - ry, rx * 2, ry * 2), 4)
    return azul


@paso("extraer")
class Extraer(Paso):
    """Pescado: raspa con la cuchara de la cola a la cabeza y quita las escamas.
    Langostino: corta cada una de las 4 secciones de la cascara con la tijera y tira de ella con la mano."""

    def iniciar(self):
        self.ing = self.ing or "pescado"
        self.cpos = V2(CX, 250)
        self.prev = None
        self.langostino = self.ing == "langostino"
        if self.langostino:
            self.titulo = "¡Quita la cáscara del langostino!"
            self._ini_langostino()
        else:
            self.titulo = "¡Quita las escamas de%s!" % (" " + nombre_ing(self.ing).replace("el ", "l ", 1)
                                                         if nombre_ing(self.ing).startswith("el ") else
                                                         " " + nombre_ing(self.ing))
            self.titulo = "¡Quita las escamas del pescado!" if self.ing == "pescado" else self.titulo
            self._ini_pescado()

    def tiempo_base(self):
        return 58.0 - 0.5 * self.dif

    # ------------------------------------------------------------------ pescado
    def _ini_pescado(self):
        self.pcx, self.pcy, self.prx, self.pry = 700, 410, 215, 92
        d = 36 - 0.9 * self.dif
        self.d = d
        self.escamas = []
        y = self.pcy - self.pry + 12
        fila = 0
        while y < self.pcy + self.pry - 8:
            x = self.pcx - self.prx + 14 + (d / 2 if fila % 2 else 0)
            while x < self.pcx + self.prx - 70:
                dx = (x - self.pcx) / (self.prx - 12)
                dy = (y - self.pcy) / (self.pry - 10)
                if dx * dx + dy * dy < 1:
                    self.escamas.append([x, y, True, random.uniform(0.85, 1.1)])
                x += d
            y += d * 0.78
            fila += 1
        self.radio = (36 - 0.4 * self.dif) * self.mods.alc
        self.golpes = 6 + int(round(self.dif * 0.1))              # pasadas que aguanta cada escama
        for e in self.escamas:
            e.extend([0, -9.0])                                   # [4]=pasadas recibidas, [5]=ultima vez
        self.filas = []                                           # alturas utiles de pasada (para guiar/bot)
        yy = self.pcy - self.pry + 16
        while yy < self.pcy + self.pry - 10:
            self.filas.append(yy)
            yy += self.radio * 1.3

    def _act_pescado(self, dt, ctrl):
        pos = self.cpos
        if self.prev is not None:
            dx = pos.x - self.prev.x
            if dx > 0.5 and abs(pos.y - self.pcy) < self.pry + 50 and abs(pos.x - self.pcx) < self.prx + 70:
                n = 0
                for e in self.escamas:
                    if e[2] and self.t - e[5] > 0.5 and math.hypot(e[0] - pos.x, e[1] - pos.y) < self.radio:
                        e[5] = self.t
                        e[4] += 1
                        n += 1
                        if e[4] >= self.golpes:
                            e[2] = False
                            self.sumar_particulas(e[0], e[1], (205, 225, 245), 2)
                if n:
                    self.prog = sum(min(1.0, e[4] / float(self.golpes)) for e in self.escamas) / len(self.escamas)
                    self.sonidos.reproducir("tick")
        if self.prog >= 0.99 or all(not e[2] for e in self.escamas):
            self.terminar(1.0, "¡Pescado limpito!")

    def _dib_pescado(self, p):
        cx, cy, rx, ry = self.pcx, self.pcy, self.prx, self.pry
        sombra_suave(p, (cx - rx - 60, cy + ry + 30, rx * 2 + 120, 40), 55)
        azul = _pez_cuerpo(p, cx, cy, rx, ry, False)
        for e in self.escamas:
            if e[2]:
                c = _mez(azul, (225, 238, 250), 0.25 * (e[3] - 0.85) / 0.25 + 0.1 + 0.4 * e[4] / float(self.golpes))
                rr = int(self.d * 0.62 * e[3] * (1 - 0.45 * e[4] / float(self.golpes)))
                pygame.draw.circle(p, c, (int(e[0]), int(e[1])), rr)
                pygame.draw.arc(p, _osc(azul, .35), (int(e[0]) - rr, int(e[1]) - rr, rr * 2, rr * 2), 2.2, 4.1, 2)
                pygame.draw.circle(p, _osc(azul, .3), (int(e[0]), int(e[1])), rr, 1)
        # cabeza
        pygame.draw.arc(p, (170, 110, 110), (cx + rx - 110, cy - ry, 60, ry * 2), -1.2, 1.2, 5)
        pygame.draw.circle(p, (255, 255, 255), (cx + rx - 40, cy - 18), 14)
        pygame.draw.circle(p, (30, 30, 50), (cx + rx - 36, cy - 18), 8)
        pygame.draw.arc(p, (170, 90, 90), (cx + rx - 60, cy + 12, 50, 30), 3.6, 5.6, 4)
        # flecha cola -> cabeza
        y = cy + ry + 90
        pygame.draw.line(p, (255, 255, 255), (cx - rx + 20, y), (cx + rx - 60, y), 6)
        pygame.draw.polygon(p, (255, 255, 255), [(cx + rx - 40, y), (cx + rx - 76, y - 18), (cx + rx - 76, y + 18)])
        escribir(p, self.f.chica, "cola", cx - rx + 10, y + 24, (255, 255, 255), contorno=(110, 70, 40))
        escribir(p, self.f.chica, "cabeza", cx + rx - 60, y + 24, (255, 255, 255), contorno=(110, 70, 40))
        guia_texto(p, self.f, "Raspa con la cuchara de la cola a la cabeza")
        dibujar_herr(p, "cuchara", self.cpos.x, self.cpos.y + 8, t=self.t)

    # ------------------------------------------------------------------ langostino
    def _ini_langostino(self):
        self.sx = [400, 495, 590, 685, 780, 875]
        self.sy = [432, 410, 394, 388, 396, 414]
        self.NS = len(self.sx)
        self.lado = 0                                   # 0 = un lado, 1 = se da la vuelta y se hace el otro
        self.pausa = 0.0
        self.zona = min(46.0, (44 - 2.0 * self.dif) * self.mods.alc)
        self.cortada = [False] * self.NS
        self.sacada = [False] * self.NS
        self.arm = {}
        self.dwell = 0.0
        self.agarre = None
        self.ancla = V2()
        self.vuelos = []
        self.errs = []
        self.sec_h = 84
        self.mano = False

    def _act_langostino(self, dt, ctrl):
        pos = self.cpos
        if self.pausa > 0:
            self.pausa -= dt
            return
        # 1) cortar con tijera
        for k in range(self.NS):
            if self.cortada[k]:
                continue
            gx, gy = self.sx[k], self.sy[k]
            if abs(pos.x - gx) > self.zona:
                self.arm.pop(k, None)
                continue
            hh = self.sec_h * 0.55
            lado = -1 if pos.y < gy - hh else (1 if pos.y > gy + hh else 0)
            if lado == 0:
                continue
            if k not in self.arm:
                self.arm[k] = lado
            elif self.arm[k] != lado:
                self.cortada[k] = True
                self.errs.append(abs(pos.x - gx) / self.zona)
                self.sonidos.reproducir("corte")
                self.sumar_particulas(gx, gy, (250, 170, 130), 8)
        # 2) agarrar y tirar
        self.mano = False
        if self.agarre is None:
            cerca = None
            for k in range(self.NS):
                if self.cortada[k] and not self.sacada[k]:
                    if math.hypot(pos.x - self.sx[k], pos.y - self.sy[k]) < 70 * self.mods.alc:
                        cerca = k
                        break
            if cerca is not None:
                self.mano = True
                self.dwell += dt
                if self.dwell >= 0.12:
                    self.agarre = cerca
                    self.ancla = V2(pos)
                    self.sonidos.reproducir("click")
            else:
                self.dwell = 0.0
        else:
            self.mano = True
            if pos.distance_to(self.ancla) > 150:
                k = self.agarre
                self.sacada[k] = True
                self.agarre = None
                self.dwell = 0.0
                d = (pos - self.ancla)
                d = d.normalize() if d.length() > 0 else V2(0, -1)
                self.vuelos.append(dict(k=k, x=self.sx[k] + d.x * 70, y=self.sy[k] + d.y * 70, vx=d.x * 200,
                                        vy=d.y * 200 - 60, t=0.0))
                self.sonidos.reproducir("pop")
                self.sumar_particulas(self.sx[k], self.sy[k], (250, 150, 110), 10)
        self.prog = (self.lado + sum((0.35 if self.cortada[k] else 0) + (0.65 if self.sacada[k] else 0)
                                     for k in range(self.NS)) / self.NS) / 2.0
        for v in self.vuelos:
            v["t"] += dt
            v["vy"] += 500 * dt
            v["x"] += v["vx"] * dt
            v["y"] += v["vy"] * dt
        self.vuelos = [v for v in self.vuelos if v["t"] < 0.6]
        if all(self.sacada):
            if self.lado == 0:
                self.lado = 1
                self.cortada = [False] * self.NS
                self.sacada = [False] * self.NS
                self.arm = {}
                self.agarre = None
                self.dwell = 0.0
                self.pausa = 1.0
                self.texto_flotante("¡Ahora el otro lado!", CX, 300)
            else:
                prec = 1.0 - 0.2 * (sum(self.errs) / max(1, len(self.errs)))
                self.terminar(prec, "¡Langostino pelado!")

    def _seccion(self, p, x, y, cascara, w=104, h=150, borde=True):
        c = (250, 140, 100)
        r = pygame.Rect(0, 0, w, h)
        r.center = (int(x), int(y))
        if cascara:
            pygame.draw.ellipse(p, c, r)
            pygame.draw.ellipse(p, _cla(c, .35), (r.x + 18, r.y + 12, w * 0.5, h * 0.2))
            for i in range(1, 4):
                pygame.draw.arc(p, _osc(c, .25), r.inflate(-i * 22, 0), 1.7, 4.6, 3)
            if borde:
                pygame.draw.ellipse(p, _osc(c, .4), r, 4)
        else:
            pass

    def _dib_langostino(self, p):
        f = self.f
        sombra_suave(p, (320, 500, 760, 50), 55)
        # cola (abanico) a la izquierda
        for da in (-1, 0, 1):
            pygame.draw.ellipse(p, (240, 120, 85), (262 + da * 6, 450 + da * 30 - 26, 120, 52))
            pygame.draw.ellipse(p, (170, 70, 50), (262 + da * 6, 450 + da * 30 - 26, 120, 52), 3)
        # patitas y cabeza (derecha)
        for i in range(6):
            pygame.draw.line(p, (230, 110, 80), (420 + i * 90, 470 - (i % 2) * 8), (400 + i * 90, 525), 7)
        pygame.draw.ellipse(p, (245, 130, 92), (935, 360, 140, 110))
        pygame.draw.ellipse(p, (170, 70, 50), (935, 360, 140, 110), 4)
        pygame.draw.circle(p, (255, 255, 255), (1035, 395), 13)
        pygame.draw.circle(p, (30, 30, 50), (1039, 395), 7)
        pygame.draw.line(p, (230, 110, 80), (1065, 385), (1145, 335), 5)
        pygame.draw.line(p, (230, 110, 80), (1065, 395), (1155, 385), 5)
        # carne continua debajo de la cascara
        pts = [(self.sx[0] - 60, self.sy[0] + 8)] + [(self.sx[k], self.sy[k]) for k in range(self.NS)] + [(955, 418)]
        pygame.draw.lines(p, (225, 150, 140), False, pts, 96)
        pygame.draw.lines(p, (255, 205, 190), False, pts, 86)
        pygame.draw.lines(p, (255, 232, 222), False, [(x, y - 20) for x, y in pts], 18)
        # secciones de cascara
        for k in range(self.NS):
            x, y = self.sx[k], self.sy[k]
            dx = dy = 0
            if self.agarre == k:
                d = self.cpos - self.ancla
                dl = min(d.length(), 150)
                if d.length() > 0:
                    d = d.normalize() * dl * 0.7
                dx, dy = d.x, d.y
            if not self.sacada[k]:
                self._seccion(p, x + dx, y + dy, True)
            if not self.cortada[k]:
                pul = 0.5 + 0.5 * math.sin(self.t * 5 + k)
                c = (255, int(255 - 100 * pul), int(255 - 140 * pul))
                for yy in range(int(y - 112), int(y + 112), 22):
                    pygame.draw.line(p, c, (x, yy), (x, yy + 11), 4)
            elif not self.sacada[k]:
                pygame.draw.line(p, (110, 40, 30), (x, y - self.sec_h), (x, y + self.sec_h), 4)
                if self.agarre is None:
                    b = 6 * math.sin(self.t * 6)
                    pygame.draw.circle(p, (255, 255, 255), (int(x), int(y + b)), 20, 4)
                    pygame.draw.polygon(p, (255, 255, 255), [(x - 14, y - 52 + b), (x + 14, y - 52 + b), (x, y - 34 + b)])
        for v in self.vuelos:
            al = max(0, 1 - v["t"] / 0.6)
            s = pygame.Surface((130, 170), pygame.SRCALPHA)
            self._seccion(s, 65, 85, True)
            s.set_alpha(int(255 * al))
            p.blit(s, (v["x"] - 65, v["y"] - 85))
        sig = "Pasa la tijera por la línea, luego toca la sección y tira"
        if all(self.cortada) and not all(self.sacada):
            sig = "Toca la sección y tira de ella con la mano"
        guia_texto(p, f, sig)
        if self.mano:
            dibujar_herr(p, "mano", self.cpos.x, self.cpos.y, t=self.t)
        else:
            dibujar_herr(p, "tijera", self.cpos.x, self.cpos.y + 10,
                         abierto=0.5 + 0.5 * math.sin(self.t * 9), t=self.t)

    # ------------------------------------------------------------------ comun
    def actualizar_paso(self, dt, ctrl):
        pos = _cursor_pos(ctrl)
        self.cpos = pos
        if self.langostino:
            self._act_langostino(dt, ctrl)
        else:
            self._act_pescado(dt, ctrl)
        self.prev = V2(pos)

    def dibujar_paso(self, p):
        if self.langostino:
            self._dib_langostino(p)
        else:
            self._dib_pescado(p)
        cuenco_chico(p, self.spec, self.prog, self.ing, "pelado")


# =============================================================================================== EXPRIMIR
@paso("exprimir")
class Exprimir(Paso):
    """Gira el exprimidor alrededor de la fruta, presionando: el jugo cae al vaso."""

    def iniciar(self):
        self.ing = self.ing or "naranja"
        self.titulo = "¡Exprime %s!" % nombre_ing(self.ing)
        self.fx, self.fy = CX, 335
        self.R = 4                                  # mitades de fruta (se exprime cada una)
        self.ronda = 0
        self.pr = 0.0                               # avance de la mitad actual 0..1
        self.pausa = 0.0
        self.vueltas = 6.0 + 0.3 * self.dif         # vueltas por mitad
        self.r_min, self.r_max = 30.0, 205.0 * self.mods.alc
        self.ang_prev = None
        self.cpos = V2(CX, 250)
        self.gotas = []
        self.acum = 0.0
        self.giro = 0.0
        self.color = col_ing(self.ing, (250, 165, 40))
        self.jugo = _cla(self.color, .1) if self.ing != "limon" else (235, 240, 150)

    def tiempo_base(self):
        return 58.0 - 0.5 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = _cursor_pos(ctrl)
        self.cpos = pos
        d = pos - V2(self.fx, self.fy)
        dist = d.length()
        if self.pausa > 0:
            self.pausa -= dt
            self.ang_prev = None
            self._gotas(dt)
            return
        if self.r_min < dist < self.r_max:
            a = math.atan2(d.y, d.x)
            if self.ang_prev is not None:
                da = (a - self.ang_prev + math.pi) % math.tau - math.pi
                if abs(da) < 1.5:
                    gana = abs(da) / math.tau / self.vueltas * self.mods.pot
                    self.pr = min(1.0, self.pr + gana)
                    self.prog = (self.ronda + self.pr) / self.R
                    self.giro += da
                    self.acum += gana
                    while self.acum > 0.012:
                        self.acum -= 0.012
                        self.gotas.append(dict(x=self.fx + random.uniform(-55, 55), y=self.fy + 60 + random.uniform(0, 30),
                                               vx=random.uniform(-15, 15), vy=random.uniform(0, 80)))
                    if int(self.prog * 40) % 4 == 0:
                        self.sonidos.reproducir("tick")
            self.ang_prev = a
        else:
            self.ang_prev = None
        self._gotas(dt)
        if self.pr >= 1.0:
            self.ronda += 1
            self.pr = 0.0
            if self.ronda >= self.R:
                self.prog = 1.0
                self.terminar(1.0, "¡Qué rico jugo!")
            else:
                self.pausa = 0.8
                self.texto_flotante("¡Otra mitad!", self.fx, self.fy - 150)

    def _nivel(self):
        """Nivel del jugo en el vaso 0..1 (llega como maximo al 78% aunque haya muchas mitades)."""
        return 0.06 + 0.72 * max(0.0, min(1.0, self.prog))

    def _superficie(self):
        return 600 + 140 // 2 - 10 - (140 - 14) * self._nivel()

    def _gotas(self, dt):
        nv = []
        for g in self.gotas:
            g["vy"] += 900 * dt
            g["vx"] += (CX - g["x"]) * 3.0 * dt
            g["x"] += g["vx"] * dt
            g["y"] += g["vy"] * dt
            # la gota cae dentro del vaso y se pierde al tocar el jugo (no se sale del vaso)
            if g["y"] < max(540.0, self._superficie()):
                nv.append(g)
        self.gotas = nv

    def _fruta(self, p, x, y, R):
        c = self.color
        pygame.draw.circle(p, _osc(c, .2), (x, y), R + 10)
        pygame.draw.circle(p, _cla(c, .55), (x, y), R + 3)
        pygame.draw.circle(p, c, (x, y), R - 5)
        n = 9
        for k in range(n):
            a0 = k * math.tau / n + 0.05
            a1 = (k + 1) * math.tau / n - 0.05
            pts = [(x + 8 * math.cos((a0 + a1) / 2), y + 8 * math.sin((a0 + a1) / 2))]
            for i in range(7):
                a = a0 + (a1 - a0) * i / 6
                pts.append((x + (R - 14) * math.cos(a), y + (R - 14) * math.sin(a)))
            pygame.draw.polygon(p, _mez(c, (255, 255, 200), 0.18 + 0.4 * self.pr), pts)
        pygame.draw.circle(p, (255, 250, 230), (x, y), 9)

    def dibujar_paso(self, p):
        f = self.f
        # platito
        pygame.draw.ellipse(p, (225, 230, 245), (self.fx - 150, self.fy - 140, 300, 300))
        pygame.draw.ellipse(p, (110, 130, 190), (self.fx - 150, self.fy - 140, 300, 300), 4)
        if self.pausa > 0 or self.ronda >= self.R:
            R = int(70 * (1 - 0.0))
            if self.pausa > 0:
                R = int(70 + 30 * max(0.0, 1.0 - self.pausa / 0.8))      # aparece la siguiente mitad
        else:
            R = int(100 * (1 - 0.3 * self.pr))
        self._fruta(p, self.fx, self.fy + int(6 * self.pr), R)
        escribir(p, f.chica, "Mitad %d de %d" % (min(self.ronda + 1, self.R), self.R), self.fx - 260, self.fy - 110,
                 (255, 255, 255), contorno=(110, 70, 40))
        # guia circular
        rg = 128
        for i in range(24):
            a = i * math.tau / 24 + self.t * 1.2
            if i % 2 == 0:
                pygame.draw.circle(p, (255, 255, 255), (int(self.fx + rg * math.cos(a)), int(self.fy + rg * math.sin(a))), 5)
        ax = self.t * 1.2 + 0.2
        pygame.draw.polygon(p, (255, 255, 255), [(self.fx + rg * math.cos(ax) + 16 * math.cos(ax + 1.57),
                                                  self.fy + rg * math.sin(ax) + 16 * math.sin(ax + 1.57)),
                                                 (self.fx + rg * math.cos(ax) - 16 * math.cos(ax + 1.57),
                                                  self.fy + rg * math.sin(ax) - 16 * math.sin(ax + 1.57)),
                                                 (self.fx + (rg + 0) * math.cos(ax + 0.3), self.fy + rg * math.sin(ax + 0.3))])
        # vaso
        gx, gy, gw, gh = CX, 600, 180, 140
        sombra_suave(p, (gx - 90, gy + 20, 180, 30), 60)
        vaso = [(gx - gw // 2, gy - gh // 2), (gx + gw // 2, gy - gh // 2), (gx + gw // 2 - 22, gy + gh // 2 - 10),
                (gx - gw // 2 + 22, gy + gh // 2 - 10)]
        nivel = self._nivel()
        hl = int((gh - 14) * nivel)
        yj = gy + gh // 2 - 10 - hl
        f_ = lambda yy: (gx - gw // 2 + 22 * (yy - (gy - gh // 2)) / (gh - 10)) + 0  # borde izquierdo en altura yy
        pygame.draw.polygon(p, (235, 245, 255), vaso)
        j = [(f_(yj) + 3, yj), (gx * 2 - f_(yj) - 3, yj), (gx + gw // 2 - 24, gy + gh // 2 - 12),
             (gx - gw // 2 + 24, gy + gh // 2 - 12)]
        pygame.draw.polygon(p, self.jugo, j)
        pygame.draw.line(p, _cla(self.jugo, .5), (j[0][0] + 4, yj + 3), (j[1][0] - 4, yj + 3), 3)
        pygame.draw.polygon(p, (150, 175, 215), vaso, 4)
        pygame.draw.line(p, (255, 255, 255), (gx - gw // 2 + 14, gy - gh // 2 + 14), (gx - gw // 2 + 26, gy + gh // 2 - 30), 4)
        for g in self.gotas:
            pygame.draw.ellipse(p, self.jugo, (int(g["x"]) - 5, int(g["y"]) - 8, 10, 16))
            pygame.draw.ellipse(p, _osc(self.jugo, .25), (int(g["x"]) - 5, int(g["y"]) - 8, 10, 16), 2)
        guia_texto(p, f, "Gira el exprimidor alrededor de la fruta")
        pres = 1.0
        dibujar_herr(p, "exprimidor", self.cpos.x, self.cpos.y + 4, pres=pres, t=self.t)
        cuenco_chico(p, self.spec, self.prog, "jugo", "entero")
