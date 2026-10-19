"""Pasos de cocina "de mezcla y fuego" (S3): combinar, girar, batir, cucharear, verter, mover_sarten, saltear,
hornear, hervir y servir.  Todos se juegan SOLO moviendo el cursor (ver cocina_base).

Claves de `spec` que leen (todas opcionales, con valores por defecto):
  combinar    ings (lista de ids a arrastrar al cuenco; 2..8), ing
  girar       ings / ing (color de la mezcla), sobre
  batir       ing ("huevo", "crema", "huevo_batido"...), ings (color de la mezcla)
  cucharear   ing (lo que se pasa), sobre ("plato", "sarten", "bandeja", otro = cuenco) -> a donde va
  verter      ing (liquido: leche, agua, jugo, caldo, salsa, aceite...), sobre ("vaso", "olla"...)
  mover_sarten ing ("mantequilla", "salsa", "aceite"...)
  saltear     ing (la comida que salta), ings (mezcla de comida)
  hornear     ing (lo que se hornea: masa, bizcocho, galleta, pizza...)
  hervir      ing (lo que hierve: fideos, papa, caldo...), sobre.  Tres botones de fuego (ALTO/MEDIO/BAJO):
              la olla pide un nivel que cambia varias veces; basta posar el cursor sobre el boton.
  servir      ing / ings (comida principal, 1..3), adornos (lista opcional de adornos:
              hoja, tomatito, rodaja, flor, estrella).  Si ing/ings es bebida (id 'jugo*', leche, agua, te...):
              sin comida -> un vaso solo; con comida -> bandeja con plato y vaso al costado.
Tiempos: todos los pasos apuntan a ~30-40 s para un buen jugador; tiempo_base() = 52-58 s (t_max>=45 s).
Arte: usa cocina_ingredientes.dibujar_ing / cocina_herramientas.dibujar_herr si existen; si no, dibujo propio.
"""

import math
import random

import pygame

import catalogo
from ajustes import ANCHO, ALTO
from nucleo import aclarar, barra, escribir, oscurecer, V2
from cocina_base import Paso, paso, AREA

# ----------------------------------------------------------------------------- utilidades de arte
_COL = {
    "masa": (240, 215, 160), "masa_plana": (240, 215, 160), "mezcla": (245, 222, 165), "batido": (250, 225, 130),
    "crema_batida": (255, 252, 242), "salsa": (215, 70, 50), "caldo": (225, 175, 80), "relleno": (210, 140, 90),
    "pure": (245, 215, 120), "bizcocho": (245, 205, 120), "base": (235, 200, 140), "pasta_cocida": (248, 222, 150),
    "arroz_cocido": (250, 248, 235), "glaseado": (250, 240, 245), "jugo": (250, 180, 50),
    "huevo_batido": (250, 220, 110), "pan_rebanado": (235, 195, 125), "tortilla": (240, 205, 130),
    "rollo": (225, 175, 105), "empanada": (225, 170, 100), "galleta": (215, 160, 90), "bolitas": (220, 165, 100),
    "panqueque": (235, 190, 110), "pizza": (235, 170, 80), "huevo": (250, 240, 220), "leche": (252, 252, 248),
    "agua": (150, 210, 245), "aceite": (245, 215, 80), "harina": (250, 248, 240), "azucar": (255, 255, 255),
    "sal": (245, 245, 250), "mantequilla": (250, 225, 120), "crema": (250, 250, 238), "queso": (250, 205, 80),
}
_LIQUIDOS = ("leche", "agua", "aceite", "jugo", "caldo", "salsa", "crema", "miel", "huevo_batido", "batido")
_HOJA = (80, 170, 80)


def _col(ident):
    if ident in _COL:
        return _COL[ident]
    try:
        return tuple(catalogo.info(ident)["color"][:3])
    except Exception:
        return (200, 190, 170)


def _mezclar(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _promedio(cols):
    if not cols:
        return (240, 220, 170)
    return tuple(int(sum(c[i] for c in cols) / len(cols)) for i in range(3))


def _tinte(c, estado):
    if estado in ("cocido", "dorado"):
        return _mezclar(c, (205, 140, 60), 0.55)
    if estado == "quemado":
        return _mezclar(c, (45, 32, 28), 0.85)
    if estado in ("batido", "espuma"):
        return aclarar(c, 0.55)
    if estado in ("masa", "crudo"):
        return _mezclar(c, (240, 215, 160), 0.6)
    if estado == "pelado":
        return aclarar(c, 0.25)
    return c


def _rot(pts, ang, ox, oy):
    c, s = math.cos(ang), math.sin(ang)
    return [(ox + x * c - y * s, oy + x * s + y * c) for x, y in pts]


def _elipse_pts(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _snd(ctx_sonidos, nombre):
    try:
        ctx_sonidos.reproducir(nombre)
    except Exception:
        pass


def dibujar_ing(p, ident, x, y, tam=64, estado="entero", t=0.0):
    """Ingrediente: arte de cocina_ingredientes si existe; si no, un dibujo propio sencillo."""
    try:
        import cocina_ingredientes
        cocina_ingredientes.dibujar_ing(p, ident, x, y, tam, estado, t)
        return
    except (ImportError, AttributeError, TypeError, KeyError, ValueError, IndexError):
        pass
    c = _tinte(_col(ident), estado)
    r = int(tam * 0.42)
    x, y = int(x), int(y)
    borde = oscurecer(c, 0.45)
    if ident == "huevo" and estado == "entero":
        pygame.draw.ellipse(p, c, (x - int(r * 0.8), y - r, int(r * 1.6), int(r * 2.0)))
        pygame.draw.ellipse(p, borde, (x - int(r * 0.8), y - r, int(r * 1.6), int(r * 2.0)), 3)
        pygame.draw.ellipse(p, (255, 255, 255), (x - int(r * 0.45), y - int(r * 0.7), int(r * 0.35), int(r * 0.6)))
    elif ident in _LIQUIDOS and estado == "entero":
        pygame.draw.rect(p, c, (x - int(r * 0.7), y - r, int(r * 1.4), int(r * 2.0)), border_radius=10)
        pygame.draw.rect(p, borde, (x - int(r * 0.7), y - r, int(r * 1.4), int(r * 2.0)), 3, border_radius=10)
        pygame.draw.rect(p, (200, 90, 80), (x - int(r * 0.45), y - r - 8, int(r * 0.9), 12), border_radius=4)
    else:
        pygame.draw.circle(p, c, (x, y), r)
        pygame.draw.circle(p, borde, (x, y), r, 3)
        pygame.draw.circle(p, aclarar(c, 0.6), (x - r // 3, y - r // 3), max(2, r // 4))
    if estado in ("cortado", "picado"):
        pygame.draw.line(p, borde, (x - r // 2, y), (x + r // 2, y), 2)


def dibujar_herr(p, nombre, x, y, tam=64, angulo=0.0, color=None):
    """Herramienta con la punta de accion en (x, y). angulo en radianes (positivo = sentido del reloj)."""
    if nombre in ("cuchara", "batidor", "espatula"):
        try:
            import cocina_herramientas
            if nombre in getattr(cocina_herramientas, "NOMBRES", ()):
                # el arte oficial se centra en (x, y) con la punta ABAJO y gira en grados antihorario:
                # lo colocamos para que la punta quede en (x, y)
                c, s_ = math.cos(angulo), math.sin(angulo)
                dx, dy = 0.0, -0.40 * tam
                cocina_herramientas.dibujar_herr(p, nombre, x + dx * c - dy * s_, y + dx * s_ + dy * c, tam,
                                                 -math.degrees(angulo))
                return
        except (ImportError, AttributeError, TypeError, ValueError):
            pass
    k = tam / 64.0
    if nombre == "cuchara":
        mango = _rot([(0, 0), (34 * k, -118 * k)], angulo, x, y)
        pygame.draw.line(p, (140, 100, 60), mango[0], mango[1], max(3, int(7 * k)))
        pts = _rot(_elipse_pts(0, 0, 22 * k, 28 * k), angulo, x, y)
        pygame.draw.polygon(p, (205, 205, 215), pts)
        pygame.draw.polygon(p, (110, 110, 130), pts, 3)
        pygame.draw.polygon(p, (235, 235, 245), _rot(_elipse_pts(-4 * k, -4 * k, 9 * k, 12 * k, 12), angulo, x, y))
    elif nombre == "batidor":
        mango = _rot([(0, -28 * k), (30 * k, -120 * k)], angulo, x, y)
        pygame.draw.line(p, (200, 70, 70), mango[0], mango[1], max(4, int(9 * k)))
        for rx in (21, 12, 4):
            pts = _rot(_elipse_pts(0, 6 * k, rx * k, 34 * k, 18), angulo, x, y)
            pygame.draw.polygon(p, (190, 195, 210), pts, 3)
        pygame.draw.line(p, (190, 195, 210), *_rot([(0, -28 * k), (0, 40 * k)], angulo, x, y), 3)
    elif nombre == "guante":
        pts = _rot([(-26, -10), (-26, -60), (-8, -64), (-6, -80), (6, -80), (8, -64), (26, -60), (26, -10),
                    (14, 14), (-14, 14)], angulo, x, y)
        pts = [(x + (px - x) * k, y + (py - y) * k) for px, py in pts]
        pygame.draw.polygon(p, (230, 90, 100), pts)
        pygame.draw.polygon(p, (140, 40, 55), pts, 3)
    elif nombre == "mano":
        pygame.draw.circle(p, (250, 205, 170), (int(x), int(y)), int(22 * k))
        pygame.draw.circle(p, (200, 150, 120), (int(x), int(y)), int(22 * k), 3)
    else:
        pygame.draw.line(p, (150, 110, 70), (x, y), (x + 30 * k, y - 100 * k), max(3, int(7 * k)))
        pygame.draw.circle(p, (210, 210, 220), (int(x), int(y)), int(16 * k))


def _jarra(p, x, y, tilt, color, k=1.0):
    """Jarra con el pico en (x, y); tilt 0..1 la inclina hacia la izquierda."""
    ang = -tilt * 1.1
    cuerpo = [(0, 0), (92, 0), (92, 112), (6, 112), (14, 40)]
    pts = [(a * k, b * k) for a, b in cuerpo]
    pico = _rot([(-14 * k, -4 * k), (0, 0), (10 * k, 10 * k), (-6 * k, 6 * k)], ang, x, y)
    cu = _rot(pts, ang, x, y)
    pygame.draw.polygon(p, (230, 245, 255), cu)
    # liquido (se ve sobre todo cuando esta derecha)
    nivel = 0.75 - 0.5 * tilt
    liq = _rot([(14 * k, 112 * k * (1 - nivel) + 8 * k), (92 * k, 112 * k * (1 - nivel) + 8 * k), (92 * k, 112 * k),
                (6 * k, 112 * k)], ang, x, y)
    pygame.draw.polygon(p, color, liq)
    pygame.draw.polygon(p, (90, 120, 160), cu, 4)
    pygame.draw.polygon(p, (230, 245, 255), pico)
    pygame.draw.polygon(p, (90, 120, 160), pico, 3)
    asa = _rot([(92 * k, 20 * k), (130 * k, 30 * k), (130 * k, 85 * k), (92 * k, 98 * k)], ang, x, y)
    pygame.draw.lines(p, (90, 120, 160), False, asa, 8)


def _cuenco_persp(p, cx, cy, rx, ry, color=(120, 165, 225), contenido=None, nivel=0.7):
    """Cuenco visto un poco de lado. contenido = color de lo que lleva (o None)."""
    cx, cy, rx, ry = int(cx), int(cy), int(rx), int(ry)
    prof = int(ry * 2.3)
    sombra = pygame.Surface((rx * 2 + 40, 60), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (60, 40, 20, 70), (20 + rx // 5, 10, int(rx * 1.6), 36))
    p.blit(sombra, (cx - rx - 20, cy + prof - 22))
    cuerpo = [(cx + rx * math.cos(a * math.pi / 24), cy + prof * math.sin(a * math.pi / 24)) for a in range(25)]
    pygame.draw.polygon(p, oscurecer(color, 0.22), cuerpo)
    clar = [(cx + rx * 0.93 * math.cos(a * math.pi / 24), cy + (prof - 8) * math.sin(a * math.pi / 24)) for a in range(25)]
    pygame.draw.polygon(p, oscurecer(color, 0.12), clar)
    pygame.draw.ellipse(p, aclarar(color, 0.55), (cx - rx - 4, cy - ry - 4, rx * 2 + 8, ry * 2 + 8))
    pygame.draw.ellipse(p, color, (cx - rx, cy - ry, rx * 2, ry * 2))
    ri = pygame.Rect(cx - rx + 12, cy - ry + 8, rx * 2 - 24, ry * 2 - 16)
    pygame.draw.ellipse(p, oscurecer(color, 0.2), ri)
    if contenido is not None:
        baja = int((1.0 - max(0.1, min(1.0, nivel))) * ri.h * 0.45)
        pygame.draw.ellipse(p, contenido, (ri.x + 6, ri.y + 4 + baja, ri.w - 12, ri.h - 8 - baja))
        pygame.draw.ellipse(p, aclarar(contenido, 0.35), (ri.x + 6, ri.y + 4 + baja, ri.w - 12, ri.h - 8 - baja), 3)


def _cenital(p, cx, cy, r, color=(110, 150, 210), contenido=None):
    """Cuenco visto desde arriba."""
    cx, cy, r = int(cx), int(cy), int(r)
    pygame.draw.circle(p, oscurecer(color, 0.5), (cx + 6, cy + 10), r + 14)
    pygame.draw.circle(p, color, (cx, cy), r + 14)
    pygame.draw.circle(p, aclarar(color, 0.6), (cx, cy), r + 14, 5)
    pygame.draw.circle(p, oscurecer(color, 0.2), (cx, cy), r + 2)
    if contenido is not None:
        pygame.draw.circle(p, contenido, (cx, cy), r - 8)


def _adorno(p, ident, x, y, tam=60):
    x, y, r = int(x), int(y), int(tam * 0.42)
    if str(ident).startswith("ad:"):
        _adorno_ing(p, str(ident)[3:], x, y, tam)
    elif ident == "hoja":
        pts = _elipse_pts(x, y, r * 0.55, r * 1.1, 14)
        pygame.draw.polygon(p, _HOJA, pts)
        pygame.draw.polygon(p, (40, 110, 50), pts, 3)
        pygame.draw.line(p, (40, 110, 50), (x, y - r), (x, y + r), 2)
    elif ident == "tomatito":
        pygame.draw.circle(p, (225, 55, 45), (x, y), r)
        pygame.draw.circle(p, (140, 25, 25), (x, y), r, 3)
        pygame.draw.circle(p, (255, 160, 150), (x - r // 3, y - r // 3), max(2, r // 4))
        pygame.draw.polygon(p, _HOJA, [(x, y - r + 2), (x - 8, y - r - 4), (x + 8, y - r - 4)])
    elif ident == "rodaja":
        pygame.draw.circle(p, (250, 215, 70), (x, y), r)
        pygame.draw.circle(p, (240, 245, 170), (x, y), int(r * 0.78))
        for i in range(6):
            a = i * math.pi / 3
            pygame.draw.line(p, (250, 215, 70), (x, y), (x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75), 2)
        pygame.draw.circle(p, (200, 160, 30), (x, y), r, 3)
    elif ident == "flor":
        for i in range(6):
            a = i * math.pi / 3
            pygame.draw.circle(p, (250, 140, 180), (int(x + math.cos(a) * r * 0.62), int(y + math.sin(a) * r * 0.62)),
                               int(r * 0.45))
        pygame.draw.circle(p, (255, 220, 70), (x, y), int(r * 0.4))
    else:
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        pygame.draw.polygon(p, (255, 215, 60), pts)
        pygame.draw.polygon(p, (200, 150, 20), pts, 3)


# adornos coherentes con la receta: ingrediente -> adorno pequeno. Los demas (harina, sal, azucar, aceite, agua,
# levadura, leche, mantequilla...) no dan adorno.
_ADORNO_SALADO = ("lechuga", "espinaca", "tomate", "limon", "pimiento", "pepino", "zanahoria", "cebolla", "queso",
                  "maiz", "calabaza", "alga", "langostino", "huevo")           # orden = preferencia (lo mas decorativo antes)
_ADORNO_DULCE = ("chocolate", "canela", "manzana", "nueces", "naranja", "limon")
_ES_DULCE = ("chocolate", "canela", "manzana", "crema_cacao", "mermelada")
_MAX_TIPOS_ADORNO = 3


def elegir_adornos(receta_ings, receta_id=None):
    """Hasta 3 ids de adorno ("ad:<ingrediente>") coherentes con los ingredientes de la receta; [] si ninguno encaja."""
    ings = set(str(i) for i in (receta_ings or []))
    if ings & set(_ES_DULCE):
        orden = _ADORNO_DULCE                                            # postres: solo adornos dulces
    else:
        orden = _ADORNO_SALADO
    elegidos = []
    for ing in orden:
        if ing not in ings:
            continue
        if ing == "huevo" and (ings & {"harina", "azucar", "levadura", "leche"} or not ings & {
                "lechuga", "espinaca", "arroz", "arroz_cocido", "alga", "pepino"}):
            continue                                                     # el huevo duro solo va en ensaladas/arroces/sushi
        elegidos.append("ad:" + ing)
        if len(elegidos) >= _MAX_TIPOS_ADORNO:
            break
    return elegidos


def _rodaja(p, x, y, r, borde, pulpa, interior=None, gajos=0, col_gajo=None):
    pygame.draw.circle(p, borde, (x, y), r)
    pygame.draw.circle(p, pulpa, (x, y), max(2, int(r * 0.78)))
    if interior is not None:
        pygame.draw.circle(p, interior, (x, y), max(2, int(r * 0.30)))
    for i in range(gajos):
        a = i * 2 * math.pi / gajos + 0.3
        pygame.draw.line(p, col_gajo or borde, (x, y), (x + math.cos(a) * r * 0.74, y + math.sin(a) * r * 0.74), 2)
    pygame.draw.circle(p, oscurecer(borde, 0.3), (x, y), r, 2)


def _tira(p, col, x, y, largo, ancho, ang, borde=None):
    pts = _rot([(-largo / 2, -ancho / 2), (largo / 2, -ancho / 2), (largo / 2, ancho / 2), (-largo / 2, ancho / 2)],
               ang, x, y)
    pygame.draw.polygon(p, col, pts)
    if borde:
        pygame.draw.polygon(p, borde, pts, 1)


def _adorno_ing(p, ing, x, y, tam):
    """Dibujo propio, pequeno y reconocible, de lo que da cada ingrediente como adorno."""
    r = max(5, int(tam * 0.42))
    if ing == "tomate":                                              # rodajita de tomate con semillitas
        _rodaja(p, x, y, r, (205, 45, 40), (240, 95, 80), None)
        for i in range(3):
            a = i * 2.094 + 0.5
            pygame.draw.circle(p, (255, 225, 140), (int(x + math.cos(a) * r * 0.42), int(y + math.sin(a) * r * 0.42)),
                               max(2, r // 5))
    elif ing in ("lechuga", "espinaca"):                             # hojita
        c = (95, 185, 85) if ing == "lechuga" else (50, 135, 60)
        pts = _elipse_pts(x, y, r * 0.55, r * 1.1, 14)
        pygame.draw.polygon(p, c, pts)
        pygame.draw.polygon(p, (35, 100, 45), pts, 2)
        pygame.draw.line(p, (35, 100, 45), (x, y - r), (x, y + r), 2)
    elif ing == "limon":
        _rodaja(p, x, y, r, (235, 205, 40), (250, 240, 150), (255, 250, 200), 8, (235, 215, 90))
    elif ing == "naranja":
        _rodaja(p, x, y, r, (240, 140, 25), (255, 190, 80), (255, 215, 130), 8, (240, 160, 50))
    elif ing == "zanahoria":
        _rodaja(p, x, y, int(r * 0.85), (235, 120, 25), (250, 160, 55), (255, 195, 110))
    elif ing == "pepino":
        _rodaja(p, x, y, int(r * 0.9), (60, 135, 60), (200, 235, 160), (225, 245, 195), 3, (160, 210, 130))
    elif ing == "manzana":                                           # rodajita con piel roja y corazoncito
        _rodaja(p, x, y, r, (205, 50, 55), (252, 242, 200))
        pygame.draw.ellipse(p, (150, 100, 60), (x - 2, y - 5, 4, 10))
    elif ing == "cebolla":                                           # aros
        for k, c in ((r, (205, 120, 170)), (int(r * 0.74), (250, 235, 245)), (int(r * 0.55), (205, 120, 170)),
                     (int(r * 0.36), (250, 235, 245))):
            pygame.draw.circle(p, c, (x, y), max(1, k), 0)
    elif ing == "pimiento":                                          # tiritas
        for i, ang in enumerate((-0.35, 0.0, 0.35)):
            _tira(p, (225, 60, 50) if i != 1 else (245, 190, 40), x + (i - 1) * r * 0.5, y, r * 1.8, r * 0.4,
                  math.pi / 2 + ang, (150, 30, 30))
    elif ing == "queso":                                             # virutas
        for ox, oy, ang in ((-0.45, -0.3, 0.4), (0.4, -0.35, -0.5), (0.0, 0.05, 1.2), (-0.4, 0.5, -0.2), (0.45, 0.45, 0.8)):
            _tira(p, (252, 210, 70), x + ox * r, y + oy * r, r * 0.9, r * 0.22, ang, (215, 160, 30))
    elif ing == "chocolate":                                         # virutas
        for ox, oy, ang in ((-0.45, -0.3, 0.5), (0.4, -0.3, -0.6), (0.0, 0.1, 1.0), (-0.35, 0.5, -0.3), (0.5, 0.45, 0.9)):
            _tira(p, (110, 65, 40), x + ox * r, y + oy * r, r * 0.8, r * 0.28, ang, (60, 33, 20))
    elif ing == "canela":                                            # ramita enrollada
        _tira(p, (150, 90, 50), x, y, r * 2.0, r * 0.5, -0.4, (95, 55, 30))
        pygame.draw.ellipse(p, (95, 55, 30), (int(x + r * 0.62), int(y - r * 0.95), int(r * 0.5), int(r * 0.5)))
        pygame.draw.line(p, (200, 140, 90), (x - r * 0.8, y + r * 0.35), (x + r * 0.6, y - r * 0.2), 2)
    elif ing == "nueces":                                            # nuez partida
        pygame.draw.circle(p, (195, 150, 95), (x, y), r)
        pygame.draw.circle(p, (120, 80, 45), (x, y), r, 2)
        pygame.draw.line(p, (120, 80, 45), (x, y - r), (x, y + r), 2)
        pygame.draw.arc(p, (120, 80, 45), (x - r // 2, y - r // 2, r, r), 0.5, 4.0, 2)
    elif ing == "maiz":                                              # granitos
        for ox, oy in ((-0.5, -0.4), (0.5, -0.5), (0.0, 0.0), (-0.45, 0.5), (0.5, 0.45)):
            pygame.draw.circle(p, (250, 205, 40), (int(x + ox * r), int(y + oy * r)), max(3, r // 3))
            pygame.draw.circle(p, (200, 150, 20), (int(x + ox * r), int(y + oy * r)), max(3, r // 3), 1)
    elif ing == "calabaza":                                          # cuadraditos
        for ox, oy in ((-0.45, -0.4), (0.45, -0.3), (-0.1, 0.45)):
            q = int(r * 0.75)
            pygame.draw.rect(p, (240, 140, 30), (int(x + ox * r - q / 2), int(y + oy * r - q / 2), q, q))
            pygame.draw.rect(p, (180, 90, 15), (int(x + ox * r - q / 2), int(y + oy * r - q / 2), q, q), 2)
    elif ing == "huevo":                                             # cunita de huevo duro
        pts = [(x - r, y + r * 0.6), (x + r, y + r * 0.6)] + [(x + r * math.cos(a), y + r * 0.6 - r * 1.5 * math.sin(a))
                                                                for a in [math.pi * i / 10 for i in range(0, 11)]][1:-1]
        pygame.draw.polygon(p, (252, 250, 240), pts)
        pygame.draw.polygon(p, (205, 200, 180), pts, 2)
        pygame.draw.circle(p, (250, 195, 40), (x, int(y + r * 0.1)), max(3, int(r * 0.42)))
    elif ing == "alga":                                              # tira de alga
        _tira(p, (25, 70, 50), x, y, r * 2.0, r * 0.6, -0.3, (10, 40, 30))
        pygame.draw.line(p, (60, 120, 90), (x - r * 0.8, y + r * 0.1), (x + r * 0.7, y - r * 0.4), 1)
    elif ing == "langostino":                                        # langostino entero pequeno
        for i in range(6):
            a = -0.2 + i * 0.55
            pygame.draw.circle(p, (245, 135, 90), (int(x - r * 0.7 + math.cos(a + 3.4) * r * 0.7 + i * r * 0.25),
                                                   int(y + math.sin(a + 3.4) * r * 0.55)), max(3, int(r * (0.42 - i * 0.03))))
        pygame.draw.polygon(p, (230, 100, 60), [(x + r * 0.9, y + r * 0.5), (x + r * 1.25, y + r * 0.9), (x + r * 0.7, y + r * 0.95)])
        pygame.draw.circle(p, (40, 30, 30), (int(x - r * 0.55), int(y - r * 0.35)), 2)
    else:
        pygame.draw.circle(p, (255, 215, 60), (x, y), r)


def _nombre_ing(ident):
    try:
        return catalogo.info(ident)["nombre"]
    except Exception:
        return str(ident)


# ----------------------------------------------------------------------------- base comun
class _PasoFuego(Paso):
    """Atajos comunes: self.d (0..1), self.pot, self.alc, self.lento, velocidad del cursor."""

    def _comunes(self):
        self.d = self.dif / 10.0
        self.pot = max(0.5, self.mods.pot)
        self.alc = max(0.6, self.mods.alc)
        self.lento = max(0.3, min(1.0, self.mods.lento))
        self.prev = None
        self.vel = 0.0
        self.pos = V2(ANCHO / 2, ALTO / 2)

    def _mover(self, dt, ctrl):
        """Actualiza self.pos y self.vel (px/s, medida propia) a partir del cursor."""
        pos = V2(ctrl.pos)
        if self.prev is None:
            self.vel = 0.0
        else:
            self.vel = pos.distance_to(self.prev) / max(1e-4, dt)
        self.prev = pos
        self.pos = pos
        return pos

    def pista(self, p, texto, y=AREA.y + 36):
        escribir(p, self.f.normal, texto, ANCHO / 2, y, (255, 255, 255))


# ----------------------------------------------------------------------------- arrastrar y soltar (combinar / servir)
_BEBIDAS = ("limonada", "refresco", "te", "cafe", "leche", "agua", "chocolate_caliente", "malteada", "smoothie")


def _es_bebida(ident):
    s = str(ident or "")
    return s.startswith("jugo") or s in _BEBIDAS


def _plato(p, cx, cy, R):
    """Plato visto desde arriba: borde exterior R y fondo hondo (radio 0.76 R)."""
    cx, cy, R = int(cx), int(cy), int(R)
    pygame.draw.circle(p, (110, 90, 70), (cx + 8, cy + 12), R + 4)
    pygame.draw.circle(p, (250, 250, 255), (cx, cy), R)
    pygame.draw.circle(p, (205, 215, 235), (cx, cy), R, 6)
    pygame.draw.circle(p, (236, 240, 252), (cx, cy), int(R * 0.76))
    pygame.draw.circle(p, (205, 215, 235), (cx, cy), int(R * 0.76), 3)


def _vaso(p, cx, cy, w, h, color=None, nivel=0.8):
    """Vaso de lado, centrado en (cx, cy). color = bebida (None = vacio)."""
    x0, top = cx - w / 2, cy - h / 2
    pts = [(x0, top), (x0 + w, top), (x0 + w - w * 0.14, top + h), (x0 + w * 0.14, top + h)]
    pygame.draw.polygon(p, (232, 245, 255), pts)
    if color is not None:
        ny = top + h * (1.0 - nivel)
        fx = w * 0.14 * (nivel)
        liq = [(x0 + w * 0.14 * (1 - nivel) + 3, ny), (x0 + w - w * 0.14 * (1 - nivel) - 3, ny),
               (x0 + w - w * 0.14 - 3, top + h - 3), (x0 + w * 0.14 + 3, top + h - 3)]
        pygame.draw.polygon(p, color, liq)
        pygame.draw.line(p, aclarar(color, 0.5), liq[0], liq[1], 4)
    pygame.draw.line(p, (255, 255, 255), (x0 + w * 0.2, top + 8), (x0 + w * 0.26, top + h * 0.7), 4)
    pygame.draw.polygon(p, (120, 150, 195), pts, 4)


class _Arrastrar(_PasoFuego):
    """Tomar cosas con el cursor (basta con tocarlas) y llevarlas a su sitio (hay que sostenerlas un instante)."""

    DW = 0.4

    def iniciar(self):
        self._comunes()
        self.items = []
        self.held = None
        self.dw = 0.0
        self.armar()
        self.n = max(1, sum(i.get("reps", 1) for i in self.items))

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def r_agarre(self):
        return (82 - 2.6 * self.dif) * self.alc

    def armar(self):
        pass

    def destino_ok(self, it, pos):
        return False

    def dw_item(self, it):
        return self.DW

    def colocar(self, it):
        it["hechos"] = it.get("hechos", 0) + 1
        self.held = None
        self.dw = 0.0
        if it["hechos"] >= it.get("reps", 1):
            it["puesto"] = True
            it["pos"] = V2(it["target"])
        else:
            it["pos"] = V2(it["home"])
        hechos = sum(i.get("hechos", 0) for i in self.items)
        self.prog = hechos / self.n
        self.sumar_particulas(it["target"][0], it["target"][1], it.get("color", (255, 235, 130)), 10)
        _snd(self.sonidos, "pop")
        if hechos >= self.n:
            fr = self.t / max(1.0, self.t_max)
            q = 1.0 if fr <= 0.8 else max(0.75, 1.0 - (fr - 0.8) * 0.6)
            self.terminar(q, "¡Qué bien!")

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        amp = 5 + 14 * self.d
        for k, it in enumerate(self.items):
            if it["puesto"]:
                continue
            if it is self.held:
                it["pos"] += (pos - it["pos"]) * min(1.0, 22 * dt)
            else:
                f = self.lento
                it["pos"] = V2(it["home"][0] + math.sin(self.t * 1.3 * f + k * 1.7) * amp,
                               it["home"][1] + math.cos(self.t * 1.7 * f + k) * amp * 0.7)
        if self.held is None:
            mejor, md = None, 1e9
            for it in self.items:
                if it["puesto"]:
                    continue
                d = it["pos"].distance_to(pos)
                if d < self.r_agarre() and d < md:
                    mejor, md = it, d
            if mejor is not None:
                self.held = mejor
                self.dw = 0.0
                _snd(self.sonidos, "click")
        elif self.destino_ok(self.held, pos):
            self.dw += dt
            if self.dw >= self.dw_item(self.held):
                self.colocar(self.held)
        else:
            self.dw = max(0.0, self.dw - 2 * dt)

    def dibujar_items(self, p):
        for it in self.items:
            if it["puesto"] or it is self.held:
                continue
            self.dibujar_item(p, it, it["pos"], 1.0)
        if self.held is not None:
            q = self.held["pos"]
            pygame.draw.ellipse(p, (120, 100, 80), (q.x - 34, q.y + 30, 68, 16))
            self.dibujar_item(p, self.held, V2(q.x, q.y - 10 + math.sin(self.t * 10) * 2), 1.15)
            if self.dw > 0:
                barra(p, (q.x - 40, q.y + 52, 80, 10), min(1.0, self.dw / max(0.05, self.dw_item(self.held))),
                      color=(255, 230, 90), color_fondo=(70, 60, 60), borde=(255, 255, 255))

    def dibujar_item(self, p, it, pos, esc):
        pass


@paso("combinar")
class Combinar(_Arrastrar):
    titulo = "¡Echa todo en el cuenco!"
    CUENCO = (640, 500)
    DW = 0.3

    def armar(self):
        ings = list(self.spec.get("ings") or [])
        if not ings:
            ings = [self.spec.get("ing") or "harina"]
        if len(ings) < 2:
            ings.append("huevo" if ings[0] != "huevo" else "harina")
        ings = ings[:8]
        n = len(ings)
        reps = max(2, int(math.ceil((22 + 0.1 * self.dif) / n / self.pot)))      # cuantas veces hay que traer cada uno
        for i, ident in enumerate(ings):
            th = math.pi * (0.12 + 0.76 * (i + 0.5 * (n == 1)) / max(1, n - 1)) if n > 1 else math.pi / 2
            home = (640 - 480 * math.cos(th), 470 - 270 * math.sin(th))
            a = 2 * math.pi * i / n + 0.4
            ro = 0 if n == 1 else 42
            tgt = (self.CUENCO[0] + math.cos(a) * ro * 1.3, self.CUENCO[1] + 6 + math.sin(a) * ro * 0.45)
            self.items.append(dict(id=ident, home=home, pos=V2(home), target=tgt, puesto=False, reps=reps, hechos=0,
                                   color=_col(ident)))

    def destino_ok(self, it, pos):
        c = V2(self.CUENCO)
        return abs(pos.x - c.x) < 150 * self.alc and abs(pos.y - c.y) < 90 * self.alc + 20

    def dibujar_item(self, p, it, pos, esc):
        dibujar_ing(p, it["id"], pos.x, pos.y, 92 * esc, "entero", self.t)
        if not it["puesto"] and it is not self.held:
            quedan = it["reps"] - it["hechos"]
            for k in range(min(quedan, 9)):
                pygame.draw.circle(p, (255, 240, 130), (int(pos.x + (k - (min(quedan, 9) - 1) / 2) * 12), int(pos.y + 58)), 4)

    def dibujar_paso(self, p):
        self.pista(p, "Toca cada ingrediente y llévalo al cuenco, ¡varias veces!")
        con = [i for i in self.items if i["hechos"] > 0]
        base = _promedio([i["color"] for i in con]) if con else None
        _cuenco_persp(p, self.CUENCO[0], self.CUENCO[1], 190, 70, (120, 165, 225),
                      contenido=None if base is None else aclarar(base, 0.1),
                      nivel=0.35 + 0.5 * self.prog)
        # los ingredientes NO se dibujan dentro del cuenco: solo el color de la mezcla
        if self.held is not None:
            pulso = 4 * math.sin(self.t * 8)
            pygame.draw.ellipse(p, (255, 240, 130), (self.CUENCO[0] - 200 - pulso, self.CUENCO[1] - 80 - pulso,
                                                      400 + 2 * pulso, 160 + 2 * pulso), 5)
        self.dibujar_items(p)
        dibujar_herr(p, "mano", self.pos.x, self.pos.y + 4, 40)


# ----------------------------------------------------------------------------- servir
@paso("servir")
class Servir(_Arrastrar):
    titulo = "¡Pon el plato bonito!"
    DW = 0.9
    PC = (640, 430)           # centro del plato (modo plato)
    REPS_LIMPIO = 9           # porciones totales cuando no hay adornos (para que dure parecido)

    def dw_item(self, it):
        return 1.6 if it["tipo"] in ("comida", "bebida") else 1.2

    def armar(self):
        mains = list(self.spec.get("ings") or [])
        if not mains:
            mains = [self.spec.get("ing") or "pizza"]
        bebs = [m for m in mains if _es_bebida(m)][:1]
        coms = [m for m in mains if not _es_bebida(m)][:3]
        self.modo = "plato" if not bebs else ("vaso" if not coms else "bandeja")
        # geometria segun el modo
        if self.modo == "plato":
            self.pc, self.pR = V2(640, 430), 210.0
        elif self.modo == "bandeja":
            self.pc, self.pR = V2(500, 440), 168.0
        else:
            self.pc, self.pR = V2(640, 430), 0.0
        self.vc = V2(640, 440) if self.modo == "vaso" else V2(900, 440)
        self.vw, self.vh = (170.0, 270.0) if self.modo == "vaso" else (104.0, 180.0)
        well = self.pR * 0.76 * 2                         # diametro del fondo del plato
        n = len(coms)
        for i, ident in enumerate(coms):
            home = (150, 240 + i * 125)
            if n == 1:
                tgt, dia = (self.pc.x, self.pc.y), 0.9 * well          # la comida ocupa ~90% del plato
            else:
                a = -math.pi / 2 + 2 * math.pi * i / n + 0.5
                rr = 0.27 * well if n == 2 else 0.24 * well
                tgt = (self.pc.x + math.cos(a) * rr, self.pc.y + math.sin(a) * rr * 0.9)
                dia = (0.58 if n == 2 else 0.5) * well
            self.items.append(dict(id=ident, home=home, pos=V2(home), target=tgt, puesto=False, tipo="comida",
                                   r=max(60.0, dia * 0.4), tam=dia * 0.95, color=_col(ident)))
        if bebs:
            home = (150, 240 + n * 125)
            self.items.append(dict(id=bebs[0], home=home, pos=V2(home), target=(self.vc.x, self.vc.y), puesto=False,
                                   tipo="bebida", r=max(70.0, self.vw * 0.7), tam=0, color=_col(bebs[0])))
        if self.spec.get("adornos"):
            tipos = list(self.spec["adornos"])                 # la receta lo pide explicitamente
        else:
            tipos = elegir_adornos(self.spec.get("receta_ings"), self.spec.get("receta_id"))
        self.adornos_tipos = list(tipos)
        if not tipos:
            # plato limpio: no hay adornos coherentes; la comida (y la bebida) se sirve en varias porciones
            nm = max(1, len(self.items))
            for it in self.items:
                it["reps"] = max(2, int(math.ceil(self.REPS_LIMPIO / nm)))
            return
        na = 8 + int(round(self.dif * 0.2))
        k = len(tipos)
        ador = []
        for j in range(na):                                    # tipos intercalados: cada uno en pocas piezas
            ador.append(tipos[j % k])
        for i, ident in enumerate(ador):
            home = (1090 + 95 * (i % 2), 215 + (i // 2) * 70)
            if self.modo == "vaso":
                pts = [(-118, -10), (118, -10), (-100, -105), (100, -105), (0, 150), (-125, 90), (125, 90),
                       (0, -135), (-60, 140), (60, 140)]
                tgt = (self.vc.x + pts[i % len(pts)][0], self.vc.y + pts[i % len(pts)][1])
            else:
                a = -2.4 + 2 * math.pi * i / len(ador)
                rad = self.pR * (0.66 if i % 2 == 0 else 0.58)
                tgt = (self.pc.x + math.cos(a) * rad, self.pc.y + math.sin(a) * rad * 0.95)
            self.items.append(dict(id=ident, home=home, pos=V2(home), target=tgt, puesto=False, tipo="adorno", r=38.0,
                                   tam=46.0, color=(255, 230, 120)))

    def destino_ok(self, it, pos):
        return V2(it["target"]).distance_to(pos) < (it["r"] + 14) * self.alc

    def dibujar_item(self, p, it, pos, esc):
        if it["tipo"] == "comida":
            tam = it["tam"] if it["puesto"] else 130 * esc
            dibujar_ing(p, it["id"], pos.x, pos.y, tam, "cocido", self.t)
        elif it["tipo"] == "bebida":
            if it["puesto"]:
                return                                      # el vaso lleno se dibuja en su sitio
            _vaso(p, pos.x, pos.y, 62 * esc, 108 * esc, it["color"], 0.8)
        else:
            _adorno(p, it["id"], pos.x, pos.y, it["tam"] * (1.0 if it["puesto"] else 1.25 * esc))

    def dibujar_paso(self, p):
        self.pista(p, "Pon la comida en el plato y los adornos en su lugar" if self.adornos_tipos else "Sirve la comida en el plato, ¡poco a poco!")
        if self.modo == "bandeja":
            pygame.draw.rect(p, (110, 90, 70), (146, 242, 1000, 410), border_radius=30)
            pygame.draw.rect(p, (170, 175, 190), (140, 232, 1000, 410), border_radius=30)
            pygame.draw.rect(p, (210, 215, 230), (140, 232, 1000, 410), 6, border_radius=30)
        if self.pR > 0:
            _plato(p, self.pc.x, self.pc.y, self.pR)
        beb = [i for i in self.items if i["tipo"] == "bebida"]
        if self.modo != "plato":
            llena = bool(beb) and (beb[0]["puesto"] or beb[0].get("hechos", 0) > 0)
            niv = 0.82 if not beb or beb[0]["puesto"] else 0.82 * beb[0].get("hechos", 0) / beb[0].get("reps", 1)
            _vaso(p, self.vc.x, self.vc.y, self.vw, self.vh, beb[0]["color"] if llena else None, max(0.15, niv))
        # anillos que muestran donde va cada cosa
        for it in self.items:
            if it["puesto"]:
                continue
            esq = it is self.held
            col = (255, 200, 60) if esq else (190, 195, 215)
            r = int(it["r"] * (1.0 + (0.08 * math.sin(self.t * 8) if esq else 0)))
            tx, ty = int(it["target"][0]), int(it["target"][1])
            for a in range(0, 360, 30):
                a0 = math.radians(a)
                pygame.draw.arc(p, col, (tx - r, ty - int(r * 0.8), r * 2, int(r * 1.6)), a0, a0 + 0.30, 4 if esq else 3)
        for it in self.items:                                         # porciones ya servidas (aun faltan mas)
            if not it["puesto"] and it.get("hechos", 0) > 0 and it["tipo"] == "comida":
                dibujar_ing(p, it["id"], it["target"][0], it["target"][1],
                            it["tam"] * (0.45 + 0.55 * it["hechos"] / it.get("reps", 1)), "cocido", self.t)
        for tipo in ("comida", "adorno"):
            for it in self.items:
                if it["puesto"] and it["tipo"] == tipo:
                    self.dibujar_item(p, it, V2(it["target"]), 1.0)
        self.dibujar_items(p)
        escribir(p, self.f.chica, "comida", 150, AREA.y + 100, (255, 255, 255))
        if self.adornos_tipos:
            escribir(p, self.f.chica, "adornos", 1140, AREA.y + 100, (255, 255, 255))
        dibujar_herr(p, "mano", self.pos.x, self.pos.y + 4, 40)


# ----------------------------------------------------------------------------- girar
@paso("girar")
class Girar(_PasoFuego):
    titulo = "¡Revuelve en círculos!"
    C = V2(640, 440)

    def iniciar(self):
        self._comunes()
        ings = list(self.spec.get("ings") or [])
        if not ings:
            ings = [self.spec.get("ing") or "mezcla"]
        self.cols = [_col(i) for i in ings][:4]
        if len(self.cols) == 1:
            self.cols = [self.cols[0], aclarar(self.cols[0], 0.25)]
        self.base = _promedio(self.cols)
        self.vueltas = (26.0 + 1.2 * self.dif) / self.pot
        self.ang_prev = None
        self.giro = 0.0           # radianes acumulados (para dibujar)
        self.rad = 0.0
        self.t_mov = 0.0
        self.t_bien = 0.0

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        d = pos - self.C
        rmax = 285 * (0.8 + 0.2 * self.alc)
        if 28 < d.length() < rmax:
            a = math.atan2(d.y, d.x)
            if self.ang_prev is not None:
                da = (a - self.ang_prev + math.pi) % (2 * math.pi) - math.pi
                if abs(da) <= max(0.45, 16 * dt):
                    self.giro += da
                    self.rad += abs(da) / (2 * math.pi)
                    self.t_mov += dt
                    if 70 < d.length() < 0.8 * rmax:
                        self.t_bien += dt
                    self.avanzar(abs(da) / (2 * math.pi) / self.vueltas)
            self.ang_prev = a
        else:
            self.ang_prev = None
        if self.prog >= 1.0:
            fr = self.t_bien / max(0.5, self.t_mov)
            self.terminar(0.72 + 0.28 * fr, "¡Bien mezclado!")

    def dibujar_paso(self, p):
        self.pista(p, "Mueve la cuchara dando vueltas al cuenco")
        cx, cy = int(self.C.x), int(self.C.y)
        mezcla = _mezclar(self.base, aclarar(self.base, 0.1), self.prog)
        _cenital(p, cx, cy, 215, (120, 165, 225), mezcla)
        # brazos de color que se mezclan
        n = len(self.cols)
        for k in range(n * 2):
            col = _mezclar(self.cols[k % n], mezcla, min(1.0, self.prog * 1.15))
            a0 = self.giro + k * math.pi / n
            pts = []
            for i in range(26):
                r = 18 + i * 7.0
                a = a0 + i * 0.11
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            pygame.draw.lines(p, col, False, pts, 22)
        pygame.draw.circle(p, oscurecer(mezcla, 0.15), (cx, cy), 205, 4)
        # flecha de ayuda al principio
        if self.prog < 0.12 and (self.t % 1.2) < 0.9:
            for i in range(10):
                a = self.t * 3 + i * 0.12
                pygame.draw.circle(p, (255, 255, 255), (int(cx + math.cos(a) * 130), int(cy + math.sin(a) * 130)), 5)
        dibujar_herr(p, "cuchara", self.pos.x, self.pos.y, 140, 0.0)


# ----------------------------------------------------------------------------- batir
@paso("batir")
class Batir(_PasoFuego):
    titulo = "¡Bate muy rápido!"
    C = V2(640, 450)

    def iniciar(self):
        self._comunes()
        ing = self.spec.get("ing") or "huevo"
        if ing in ("huevo", "huevo_batido", "batido"):
            self.c0 = (250, 205, 90)
        else:
            self.c0 = _col(ing)
        self.espuma = 0.0
        rnd = random.Random(7)
        self.burbujas = []
        for _ in range(110):
            a, r = rnd.uniform(0, 6.283), 185 * math.sqrt(rnd.random())
            self.burbujas.append((math.cos(a) * r, math.sin(a) * r, rnd.uniform(9, 22), rnd.random()))
        self.umbral = 150 + 8 * self.dif

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        dentro = pos.distance_to(self.C) < 250 * (0.85 + 0.15 * self.alc)
        s = min(self.vel, 2400.0)
        if dentro and s > self.umbral:
            self.espuma += dt * 0.0235 * min(1.6, s / (650 + 5 * self.dif)) * self.pot
        else:
            self.espuma -= dt * (0.02 + 0.01 * self.dif)
        self.espuma = max(0.0, min(1.0, self.espuma))
        self.prog = self.espuma
        if self.espuma >= 1.0:
            self.terminar(1.0 if self.t < 0.8 * self.t_max else 0.85, "¡Qué espuma!")

    def dibujar_paso(self, p):
        self.pista(p, "Mueve el batidor muy rápido de lado a lado")
        cx, cy = int(self.C.x), int(self.C.y)
        liq = _mezclar(self.c0, (255, 250, 235), self.espuma)
        _cenital(p, cx, cy, 215, (120, 165, 225), liq)
        n = int(len(self.burbujas) * min(1.0, self.espuma * 1.1))
        for i in range(n):
            bx, by, r, ph = self.burbujas[i]
            rr = int(r * (0.5 + 0.5 * min(1.0, self.espuma * 1.5)) * (1 + 0.08 * math.sin(self.t * 9 + ph * 7)))
            pygame.draw.circle(p, (255, 255, 252), (int(cx + bx), int(cy + by)), rr)
            pygame.draw.circle(p, (225, 230, 235), (int(cx + bx), int(cy + by)), rr, 2)
        mueve = self.vel > self.umbral
        ox = math.sin(self.t * 40) * 5 if mueve else 0
        dibujar_herr(p, "batidor", self.pos.x + ox, self.pos.y, 160, 0.0)


# ----------------------------------------------------------------------------- cucharear
@paso("cucharear")
class Cucharear(_PasoFuego):
    titulo = "¡Pasa las cucharadas!"
    ORIGEN = V2(310, 470)
    DESTINO = V2(970, 470)

    def iniciar(self):
        self._comunes()
        self.ing = self.spec.get("ing") or "mezcla"
        self.color = _col(self.ing)
        self.sobre = self.spec.get("sobre") or "plato"
        self.n_tot = int(math.ceil((18 + 0.5 * self.dif) / self.pot))
        self.hechas = 0
        self.carga = False
        self.derrames = 0
        self.enfria = 0.0
        self.ang = math.pi / 2          # cuchara tendida de lado, con la parte honda mirando a la izquierda (cuenco)

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        self.enfria = max(0.0, self.enfria - dt)
        # la cuchara va tendida de lado y su parte honda apunta hacia el destino final (cargada: el plato; vacia: el cuenco)
        meta = self.DESTINO if self.carga else self.ORIGEN
        dx, dy = meta.x - pos.x, meta.y - pos.y
        lado = 1.0 if dx >= 0 else -1.0
        th = max(-0.5, min(0.5, math.atan2(dy, max(40.0, abs(dx)))))
        ux, uy = lado * math.cos(th), math.sin(th)
        obj = math.atan2(-ux, uy)                 # (-sin a, cos a) = direccion de la punta
        self.ang += (obj - self.ang) * min(1.0, 9.0 * dt)
        if not self.carga:
            if pos.distance_to(self.ORIGEN) < 135 * self.alc and self.hechas < self.n_tot:
                self.carga = True
                self.sumar_particulas(pos.x, pos.y, self.color, 6)
                _snd(self.sonidos, "click")
        else:
            if self.vel > 1900 - 60 * self.dif and self.enfria <= 0:
                self.derrames += 1
                self.enfria = 0.6
                self.sumar_particulas(pos.x, pos.y + 20, self.color, 8)
                self.texto_flotante("¡Despacio!", pos.x, pos.y - 60)
            if pos.distance_to(self.DESTINO) < 135 * self.alc:
                self.carga = False
                self.hechas += 1
                self.prog = self.hechas / self.n_tot
                self.sumar_particulas(self.DESTINO.x, self.DESTINO.y, self.color, 10)
                _snd(self.sonidos, "pop")
                if self.hechas >= self.n_tot:
                    self.terminar(max(0.6, 1.0 - 0.05 * self.derrames), "¡Todo pasado!")

    def dibujar_paso(self, p):
        self.pista(p, "Saca una cucharada de la izquierda y llévala a la derecha")
        fr = self.hechas / self.n_tot
        _cuenco_persp(p, self.ORIGEN.x, self.ORIGEN.y, 170, 62, (120, 165, 225), self.color, 0.85 - 0.6 * fr)
        dx, dy = int(self.DESTINO.x), int(self.DESTINO.y)
        if self.sobre in ("sarten", "sartén"):
            pygame.draw.circle(p, (50, 52, 60), (dx, dy), 150)
            pygame.draw.circle(p, (90, 92, 105), (dx, dy), 150, 8)
            pygame.draw.rect(p, (70, 55, 45), (dx + 140, dy - 12, 130, 24), border_radius=10)
            pygame.draw.circle(p, (70, 72, 82), (dx, dy), 128)
        elif self.sobre == "bandeja":
            pygame.draw.rect(p, (150, 155, 170), (dx - 190, dy - 70, 380, 170), border_radius=16)
            pygame.draw.rect(p, (190, 195, 210), (dx - 190, dy - 70, 380, 170), 6, border_radius=16)
        else:
            pygame.draw.ellipse(p, (150, 120, 90), (dx - 180, dy - 50, 360, 140))
            pygame.draw.ellipse(p, (250, 250, 255), (dx - 180, dy - 70, 360, 140))
            pygame.draw.ellipse(p, (205, 215, 235), (dx - 180, dy - 70, 360, 140), 5)
        rnd = random.Random(3)
        for i in range(self.hechas):
            for _ in range(2):
                bx, by = dx + rnd.uniform(-85, 85), dy + rnd.uniform(-30, 30)
                pygame.draw.ellipse(p, self.color, (bx - 24, by - 12, 48, 26))
                pygame.draw.ellipse(p, aclarar(self.color, 0.4), (bx - 24, by - 12, 48, 26), 2)
        if self.carga is False and self.hechas < self.n_tot:
            pulso = 6 * math.sin(self.t * 7)
            pygame.draw.ellipse(p, (255, 240, 130), (self.ORIGEN.x - 185 - pulso, self.ORIGEN.y - 72 - pulso,
                                                      370 + 2 * pulso, 144 + 2 * pulso), 4)
        elif self.carga:
            pulso = 6 * math.sin(self.t * 7)
            pygame.draw.ellipse(p, (255, 240, 130), (dx - 190 - pulso, dy - 90 - pulso, 380 + 2 * pulso,
                                                      180 + 2 * pulso), 4)
        bal = self.ang + math.sin(self.t * 9) * min(0.12, self.vel / 9000.0)
        dibujar_herr(p, "cuchara", self.pos.x, self.pos.y, 140, bal)
        if self.carga:
            # comida en la parte honda (que mira hacia el destino)
            ux, uy = -math.sin(bal), math.cos(bal)
            bx, by = self.pos.x - ux * 24, self.pos.y - uy * 24 - 4
            pygame.draw.ellipse(p, self.color, (bx - 20, by - 13, 40, 26))
            pygame.draw.ellipse(p, aclarar(self.color, 0.4), (bx - 20, by - 13, 40, 26), 2)


# ----------------------------------------------------------------------------- verter
@paso("verter")
class Verter(_PasoFuego):
    titulo = "¡Vierte sin derramar!"
    VASO_Y = 440          # borde de arriba del vaso
    ALTO_VASO = 135

    def iniciar(self):
        self._comunes()
        self.ing = self.spec.get("ing") or "leche"
        self.color = _col(self.ing)
        if self.ing == "agua":
            self.color = (110, 190, 245)
        self.sobre = self.spec.get("sobre") or "vaso"
        self.gx0 = 860.0
        self.gx = self.gx0
        self.ancho = (150 - 6 * self.dif) * (0.85 + 0.15 * self.alc)
        self.obj = min(0.9, 0.62 + 0.025 * self.dif)
        self.nivel = 0.0
        self.derrame = 0.0
        self.charcos = []
        self.tilt = 0.0
        self.flujo = 0.0
        self.sobre_vaso = False

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        self.gx = self.gx0 + 90 * self.d * math.sin(self.t * 0.6 * self.lento)
        self.tilt = max(0.0, min(1.0, (pos.y - 170) / 220.0))
        self.flujo = max(0.0, self.tilt - 0.12) * 0.022 * (1 + 0.05 * self.dif) * self.pot ** 0.5
        self.sobre_vaso = abs(pos.x - self.gx) < self.ancho / 2 - 6 and pos.y < self.VASO_Y - 10
        if self.flujo > 0:
            if self.sobre_vaso:
                self.nivel += self.flujo * dt
            else:
                self.derrame += self.flujo * dt
                if random.random() < 0.5:
                    self.charcos.append([pos.x + random.uniform(-6, 6), random.uniform(585, 600), 0.0])
                    self.charcos = self.charcos[-40:]
        if self.nivel >= self.obj:
            self.prog = 1.0
            self.terminar(max(0.5, 1.0 - 1.2 * self.derrame), "¡Justo hasta la raya!")
        else:
            self.prog = self.nivel / self.obj

    def dibujar_paso(self, p):
        self.pista(p, "Baja el cursor para inclinar la jarra y llena el vaso hasta la raya")
        for c in self.charcos:
            c[2] = min(1.0, c[2] + 0.02)
            pygame.draw.ellipse(p, self.color, (c[0] - 20 * c[2], c[1] - 5 * c[2], 40 * c[2], 10 * c[2]))
        # vaso / olla
        w, x0 = self.ancho, self.gx
        top, h = self.VASO_Y, self.ALTO_VASO
        pts = [(x0 - w / 2, top), (x0 + w / 2, top), (x0 + w / 2 - 14, top + h), (x0 - w / 2 + 14, top + h)]
        pygame.draw.polygon(p, (235, 245, 255), pts)
        nivel_px = h * min(1.0, self.nivel)
        liq = [(x0 - w / 2 + 14 * (1 - nivel_px / h) + 2, top + h - nivel_px),
               (x0 + w / 2 - 14 * (1 - nivel_px / h) - 2, top + h - nivel_px),
               (x0 + w / 2 - 16, top + h - 2), (x0 - w / 2 + 16, top + h - 2)]
        if nivel_px > 1:
            pygame.draw.polygon(p, self.color, liq)
            pygame.draw.line(p, aclarar(self.color, 0.5), liq[0], liq[1], 4)
        pygame.draw.polygon(p, (130, 160, 200), pts, 5)
        ly = top + h - h * self.obj
        pygame.draw.line(p, (255, 90, 90), (x0 - w / 2 - 14, ly), (x0 + w / 2 + 14, ly), 4)
        for i in range(6):
            pygame.draw.line(p, (255, 90, 90), (x0 + w / 2 + 14 + i * 0, ly), (x0 + w / 2 + 14, ly), 4)
        escribir(p, self.f.chica, "hasta aquí", x0 + w / 2 + 70, ly, (255, 255, 255))
        # chorro
        if self.flujo > 0:
            fin = top + h - nivel_px if self.sobre_vaso else 600
            x = self.pos.x
            pygame.draw.line(p, self.color, (x, self.pos.y + 6), (x, fin), max(3, int(3 + 14 * self.flujo)))
            pygame.draw.line(p, aclarar(self.color, 0.5), (x - 1, self.pos.y + 6), (x - 1, fin), 2)
        _jarra(p, self.pos.x, self.pos.y, self.tilt, self.color, 1.0)
        # aviso
        if self.flujo > 0 and not self.sobre_vaso and (self.t % 0.8) < 0.5:
            escribir(p, self.f.normal, "¡Pon la jarra sobre el vaso!", ANCHO / 2, 600, (255, 230, 140))


# ----------------------------------------------------------------------------- mover_sarten
@paso("mover_sarten")
class MoverSarten(_PasoFuego):
    titulo = "¡Unta todo el fondo!"
    fondo_tipo = "fuego"
    C = V2(640, 410)
    R = 205
    CELDA = 12
    META = 0.90           # hay que untar MAS del 90% del fondo

    def iniciar(self):
        self._comunes()
        self.ing = self.spec.get("ing") or "mantequilla"
        self.color = _col(self.ing)
        if self.ing == "aceite":
            self.color = (245, 215, 90)
        self.r_blob = (21 - 0.5 * self.dif) * (0.85 + 0.15 * self.alc)      # un trocito muy pequeno
        self.bp = V2(0, 0)
        self.celdas = []
        lim = self.R * 0.9
        for gx in range(-self.R, self.R + 1, self.CELDA):
            for gy in range(-self.R, self.R + 1, self.CELDA):
                if math.hypot(gx, gy) < lim:
                    self.celdas.append((gx, gy))
        self.cub = [False] * len(self.celdas)
        self.n_cub = 0
        self.cobertura = 0.0
        self.capa = pygame.Surface((self.R * 2 + 40, self.R * 2 + 40), pygame.SRCALPHA)
        self.off = V2(0, 0)
        self.meta = self.META

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        v = pos - self.C
        self.off = V2(v.x * 0.12, v.y * 0.12)
        tgt = V2(v)
        lim = self.R * 0.86
        if tgt.length() > lim:
            tgt.scale_to_length(lim)
        self.bp += (tgt - self.bp) * min(1.0, 3.5 * self.lento * dt + 0.3 * dt)
        mid = self.R + 20
        pygame.draw.circle(self.capa, (*self.color, 235), (int(mid + self.bp.x), int(mid + self.bp.y)),
                           int(self.r_blob))
        rb = self.r_blob
        n = 0
        for i, (gx, gy) in enumerate(self.celdas):
            if not self.cub[i] and math.hypot(gx - self.bp.x, gy - self.bp.y) < rb:
                self.cub[i] = True
            n += self.cub[i]
        self.n_cub = n
        self.cobertura = n / len(self.celdas)
        self.prog = min(1.0, self.cobertura / self.meta)
        if self.cobertura > self.meta:
            self.terminar(1.0, "¡Todo el fondo untado!")

    def dibujar_paso(self, p):
        self.pista(p, "Lleva el trocito de mantequilla por toda la sartén, ¡hasta cubrir el fondo!")
        cx, cy = int(self.C.x + self.off.x), int(self.C.y + self.off.y)
        pygame.draw.circle(p, (30, 30, 36), (cx + 8, cy + 12), self.R + 28)
        pygame.draw.rect(p, (80, 60, 50), (cx + self.R + 10, cy - 18, 190, 36), border_radius=14)
        pygame.draw.circle(p, (90, 92, 105), (cx, cy), self.R + 24)
        pygame.draw.circle(p, (150, 152, 165), (cx, cy), self.R + 24, 6)
        pygame.draw.circle(p, (62, 64, 74), (cx, cy), self.R + 4)
        p.blit(self.capa, (cx - self.R - 20, cy - self.R - 20))
        # brillo y trocito
        pygame.draw.circle(p, aclarar(self.color, 0.5), (int(cx + self.bp.x - self.r_blob * 0.3),
                                                          int(cy + self.bp.y - self.r_blob * 0.3)), max(3, int(self.r_blob * 0.3)))
        if self.prog < 0.98:
            r = int(self.r_blob)
            pygame.draw.circle(p, (255, 255, 255), (int(cx + self.bp.x), int(cy + self.bp.y)), r, 2)
        for k in range(4):
            a = self.t * 1.7 + k * 1.6
            pygame.draw.circle(p, (235, 240, 250), (int(cx + math.cos(a) * 150), int(cy - 235 - (self.t * 40 + k * 20) % 60)),
                               6, 2)
        escribir(p, self.f.normal, "Untado: %d%%  (meta: más de %d%%)" % (int(self.cobertura * 100), int(self.meta * 100)),
                 ANCHO / 2, 650, (255, 255, 255))
        dibujar_herr(p, "mano", self.pos.x, self.pos.y + 4, 36)


# ----------------------------------------------------------------------------- saltear
class _Trozo:
    def __init__(self, x, y, ident, rnd):
        self.x, self.y, self.z, self.vz = x, y, 0.0, 0.0
        self.vx = self.vy = 0.0
        self.ident = ident
        self.tam = rnd.uniform(46, 62)
        self.fase = rnd.uniform(0, 6.28)
        self.espera = 0.0


@paso("saltear")
class Saltear(_PasoFuego):
    titulo = "¡Sacude la sartén!"
    fondo_tipo = "fuego"
    C = V2(640, 410)
    R = 215

    def iniciar(self):
        self._comunes()
        ings = list(self.spec.get("ings") or [])
        if not ings:
            ings = [self.spec.get("ing") or "cebolla"]
        rnd = random.Random(11)
        self.trozos = []
        for i in range(8):
            a, r = rnd.uniform(0, 6.283), 150 * math.sqrt(rnd.random())
            self.trozos.append(_Trozo(math.cos(a) * r, math.sin(a) * r, ings[i % len(ings)], rnd))
        self.necesarias = int(math.ceil((34 + 1.0 * self.dif) / self.pot))
        self.sacudidas = 0
        self.enfria = 0.0
        self.off = V2(0, 0)
        self.umbral = 400 + 30 * self.dif

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        v = pos - self.C
        self.off = V2(max(-40, min(40, v.x * 0.15)), max(-30, min(30, v.y * 0.15)))
        self.enfria = max(0.0, self.enfria - dt)
        if self.vel > self.umbral and self.enfria <= 0:
            self.enfria = 0.9
            self.sacudidas += 1
            self.prog = min(1.0, self.sacudidas / self.necesarias)
            altura = max(230.0, min(330.0, self.vel * 0.3))
            for t in self.trozos:
                t.vz = altura * random.uniform(0.75, 1.1)
                t.vx = random.uniform(-70, 70)
                t.vy = random.uniform(-40, 40)
            self.sumar_particulas(self.C.x + self.off.x, self.C.y + self.off.y, (255, 200, 90), 8)
            self.texto_flotante("¡Hop!", self.C.x + random.uniform(-80, 80), self.C.y - 120, (255, 240, 130))
            _snd(self.sonidos, "tick")
        for t in self.trozos:
            t.x += t.vx * dt
            t.y += t.vy * dt
            t.vx *= 0.97
            t.vy *= 0.97
            if t.z > 0 or t.vz > 0:
                t.z += t.vz * dt
                t.vz -= 1500 * dt
                if t.z <= 0:
                    t.z, t.vz = 0.0, 0.0
            d = math.hypot(t.x, t.y)
            if d > 160:
                t.x, t.y = t.x * 160 / d, t.y * 160 / d
        if self.sacudidas >= self.necesarias:
            self.terminar(1.0, "¡Bien salteado!")

    def dibujar_paso(self, p):
        self.pista(p, "Sacude el cursor rápido de lado a lado para que salte la comida")
        cx, cy = int(self.C.x + self.off.x), int(self.C.y + self.off.y)
        pygame.draw.circle(p, (30, 30, 36), (cx + 8, cy + 12), self.R + 24)
        pygame.draw.rect(p, (80, 60, 50), (cx - 28, cy + self.R + 10, 56, 120), border_radius=14)
        pygame.draw.circle(p, (90, 92, 105), (cx, cy), self.R + 20)
        pygame.draw.circle(p, (150, 152, 165), (cx, cy), self.R + 20, 6)
        pygame.draw.circle(p, (62, 64, 74), (cx, cy), self.R)
        estado = "cocido" if self.prog > 0.45 else "cortado"
        for t in sorted(self.trozos, key=lambda q: q.y):
            sx, sy = cx + t.x, cy + t.y
            sc = 1.0 + t.z / 400.0
            sh = max(8, int(t.tam * 0.8 / sc))
            pygame.draw.ellipse(p, (35, 36, 42), (sx - sh // 2, sy + t.tam * 0.18, sh, sh // 2))
            dibujar_ing(p, t.ident, sx, sy - t.z, t.tam * sc, estado, self.t)
        for k in range(5):
            a = self.t * 1.9 + k * 1.3
            pygame.draw.circle(p, (235, 240, 250), (int(cx + math.cos(a) * 150), int(cy - 250 - (self.t * 45 + k * 22) % 70)),
                               6, 2)
        dibujar_herr(p, "mano", self.pos.x, self.pos.y + 4, 36)


# ----------------------------------------------------------------------------- hornear
@paso("hornear")
class Hornear(_PasoFuego):
    titulo = "¡Saca del horno en su punto!"
    fondo_tipo = "horno"
    ZONA_C = 0.66
    MANIJA = pygame.Rect(360, 478, 560, 26)
    VENTANA = pygame.Rect(350, 200, 580, 250)
    DW = 0.5

    def iniciar(self):
        self._comunes()
        self.ing = self.spec.get("ing") or "masa"
        self.b = 0.0
        self.zona_hw = (0.17 - 0.010 * self.dif) * (0.8 + 0.2 * self.alc)
        self.dwell = 0.0
        self.sacado = False
        self.quemado = False

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        if not self.sacado:
            self.b = min(1.0, self.b + dt / 46.0 * self.lento)
        zona = self.MANIJA.inflate(120, 110)
        sobre = zona.collidepoint(pos.x, pos.y)
        if sobre:
            self.dwell += dt
        else:
            self.dwell = max(0.0, self.dwell - 2 * dt)
        self.prog = min(1.0, self.dwell / self.DW) * 0.9
        if (self.dwell >= self.DW or (sobre and (ctrl.clic or ctrl.golpe))):
            self.sacar()
        elif self.b >= 1.0:
            self.quemado = True
            self.prog = 0.0
            self.terminar(0.25, "¡Uy, se quemó un poquito!")

    def sacar(self):
        dist = abs(self.b - self.ZONA_C)
        if dist <= self.zona_hw:
            q = 1.0 - 0.25 * dist / self.zona_hw
        else:
            q = max(0.25, 0.75 - (dist - self.zona_hw) * 2.0)
        self.sacado = True
        self.prog = 1.0
        txt = "¡Perfecto!" if q >= 0.85 else ("¡Muy bien!" if q >= 0.6 else "¡Casi!")
        self.texto_flotante(txt, ANCHO / 2, 330, (255, 255, 255))
        self.sumar_particulas(ANCHO / 2, 400, (255, 220, 110), 14)
        _snd(self.sonidos, "ok" if q >= 0.6 else "click")
        self.terminar(q, txt)

    def estado(self):
        if self.b < 0.4:
            return "masa"
        if self.b < 0.86:
            return "cocido"
        return "quemado"

    def _comida(self, p, x, y, esc):
        """Bandeja con tres porciones; el color va de crudo a dorado a quemado."""
        b = self.b
        if b < 0.66:
            c = _mezclar((242, 222, 175), (214, 150, 62), b / 0.66)
        else:
            c = _mezclar((214, 150, 62), (40, 28, 24), min(1.0, (b - 0.66) / 0.34))
        pygame.draw.rect(p, (150, 152, 165), (x - 230 * esc, y + 36 * esc, 460 * esc, 22 * esc), border_radius=8)
        pygame.draw.rect(p, (95, 98, 112), (x - 230 * esc, y + 36 * esc, 460 * esc, 22 * esc), 3, border_radius=8)
        for dx in (-130, 0, 130):
            cx = x + dx * esc
            pygame.draw.ellipse(p, oscurecer(c, 0.3), (cx - 60 * esc, y - 20 * esc, 120 * esc, 70 * esc))
            pygame.draw.ellipse(p, c, (cx - 58 * esc, y - 40 * esc, 116 * esc, 72 * esc))
            pygame.draw.ellipse(p, aclarar(c, 0.35), (cx - 36 * esc, y - 32 * esc, 40 * esc, 22 * esc))
        if self.ing in ("masa", "mezcla", "bizcocho", "galleta", "pizza", "empanada", "pan_rebanado"):
            pass

    def dibujar_paso(self, p):
        self.pista(p, "Espera a que se dore y pon el cursor en la manija")
        v = self.VENTANA
        pygame.draw.rect(p, (60, 60, 72), v.inflate(70, 70).move(0, 40), border_radius=28)
        pygame.draw.rect(p, (140, 142, 158), v.inflate(70, 70).move(0, 40), 8, border_radius=28)
        fondo = (60 + int(120 * (1 - abs(0.5 - self.b))), 30, 20)
        pygame.draw.rect(p, (25, 20, 22), v, border_radius=18)
        pygame.draw.rect(p, _mezclar((70, 35, 20), (190, 80, 20), 0.5 + 0.5 * math.sin(self.t * 3)), v.inflate(-30, -30),
                         border_radius=14)
        if not self.sacado:
            self._comida(p, v.centerx, v.centery + 20, 1.0)
        else:
            pygame.draw.rect(p, (40, 28, 25), v.inflate(-30, -30), border_radius=14)
        pygame.draw.rect(p, (170, 175, 195), v, 8, border_radius=18)
        pygame.draw.rect(p, (90, 92, 105), self.MANIJA, border_radius=12)
        pygame.draw.rect(p, (200, 205, 220), self.MANIJA, 4, border_radius=12)
        escribir(p, self.f.chica, "manija", self.MANIJA.centerx, self.MANIJA.centery, (255, 255, 255))
        if self.dwell > 0:
            barra(p, (self.MANIJA.x + 60, self.MANIJA.bottom + 12, self.MANIJA.w - 120, 12),
                  self.dwell / self.DW, color=(255, 230, 90), color_fondo=(70, 60, 60), borde=(255, 255, 255))
        if self.sacado:
            self._comida(p, ANCHO / 2, 640, 0.8)
        # medidor de dorado (derecha)
        gx, gy, gh = 1090, 190, 330
        for i in range(gh):
            f = i / gh
            if f < 0.66:
                c = _mezclar((242, 222, 175), (214, 150, 62), f / 0.66)
            else:
                c = _mezclar((214, 150, 62), (40, 28, 24), (f - 0.66) / 0.34)
            pygame.draw.line(p, c, (gx, gy + i), (gx + 44, gy + i))
        z0 = gy + (self.ZONA_C - self.zona_hw) * gh
        z1 = gy + (self.ZONA_C + self.zona_hw) * gh
        pygame.draw.rect(p, (90, 220, 120), (gx - 8, z0, 60, z1 - z0), 5, border_radius=6)
        pygame.draw.rect(p, (255, 255, 255), (gx, gy, 44, gh), 3, border_radius=4)
        my = gy + self.b * gh
        pygame.draw.polygon(p, (255, 255, 255), [(gx - 6, my), (gx - 28, my - 12), (gx - 28, my + 12)])
        pygame.draw.polygon(p, (60, 60, 80), [(gx - 6, my), (gx - 28, my - 12), (gx - 28, my + 12)], 3)
        escribir(p, self.f.chica, "crudo", gx + 22, gy - 16, (255, 255, 255))
        escribir(p, self.f.chica, "dorado", gx - 70, (z0 + z1) / 2, (150, 255, 170))
        escribir(p, self.f.chica, "quemado", gx + 22, gy + gh + 18, (255, 255, 255))
        dibujar_herr(p, "guante", self.pos.x, self.pos.y + 6, 60)


# ----------------------------------------------------------------------------- hervir
def _llama(p, x, y, alto, t=0.0, k=0):
    """Llamita con la base en (x, y)."""
    alto = max(8.0, alto) * (0.9 + 0.12 * math.sin(t * 9 + k * 1.9))
    a = alto * 0.34
    pygame.draw.polygon(p, (255, 120, 40), [(x - a, y), (x - a * 0.7, y - alto * 0.45), (x - a * 0.2, y - alto * 0.55),
                                            (x + a * 0.1, y - alto), (x + a * 0.55, y - alto * 0.5), (x + a, y - alto * 0.3),
                                            (x + a, y)])
    pygame.draw.polygon(p, (255, 215, 80), [(x - a * 0.55, y), (x - a * 0.4, y - alto * 0.3), (x + a * 0.05, y - alto * 0.62),
                                            (x + a * 0.5, y - alto * 0.25), (x + a * 0.55, y)])
    pygame.draw.polygon(p, (255, 250, 200), [(x - a * 0.22, y), (x, y - alto * 0.3), (x + a * 0.25, y)])


@paso("hervir")
class Hervir(_PasoFuego):
    titulo = "¡Cuida el fuego!"
    fondo_tipo = "fuego"
    OLLA = V2(520, 420)
    NOMBRES = ("BAJO", "MEDIO", "ALTO")
    CALOR = (0.22, 0.58, 0.95)                    # que tan fuerte hierve la olla con cada fuego
    BOTONES = {2: pygame.Rect(900, 170, 310, 130), 1: pygame.Rect(900, 315, 310, 130), 0: pygame.Rect(900, 460, 310, 130)}
    HOVER = 0.25                                  # basta posar el cursor un instante sobre el boton

    def iniciar(self):
        self._comunes()
        self.ing = self.spec.get("ing") or "fideos"
        self.rnd = random.Random()
        self.fuego = 1                            # 0 BAJO, 1 MEDIO, 2 ALTO
        self.req = 1                              # nivel que pide la olla
        self.h = self.CALOR[1]
        self.hover_t = {0: 0.0, 1: 0.0, 2: 0.0}
        self.t_req = 4.0
        self.cambios = 0
        self.ok_t = 0.0
        self.mal_t = 0.0
        self.necesita = (26.0 + 0.5 * self.dif) / self.pot
        self.burbujas = []

    def tiempo_base(self):
        return 58.0 - 0.6 * self.dif

    def rect_boton(self, nivel):
        return self.BOTONES[nivel]

    def mensaje_fuego(self):
        """(texto, color, estado) estado: ok | falta | mucho."""
        n = self.NOMBRES[self.req]
        if self.fuego == self.req:
            return "¡Fuego perfecto! Sigue así", (70, 160, 90), "ok"
        if self.req > self.fuego:
            return "¡Falta fuego! Pon el fuego %s" % n, (215, 125, 40), "falta"
        return "¡Mucho fuego! Bájalo a %s" % n, (205, 70, 60), "mucho"

    def actualizar_paso(self, dt, ctrl):
        pos = self._mover(dt, ctrl)
        for nivel, r in self.BOTONES.items():
            if r.collidepoint(pos.x, pos.y):
                self.hover_t[nivel] += dt
                if self.hover_t[nivel] >= self.HOVER and self.fuego != nivel:
                    self.fuego = nivel
                    self.sumar_particulas(r.centerx, r.centery, (255, 190, 70), 12)
                    _snd(self.sonidos, "pop")
            else:
                self.hover_t[nivel] = 0.0
        # la olla cambia de pedido varias veces
        self.t_req -= dt
        if self.t_req <= 0:
            op = [n for n in (0, 1, 2) if n != self.req and n != self.fuego] or [n for n in (0, 1, 2) if n != self.req]
            self.req = self.rnd.choice(op)
            self.t_req = (7.5 - 0.35 * self.dif + self.rnd.uniform(0.0, 1.5)) * (2.0 - self.lento)
            self.cambios += 1
        if self.fuego == self.req:
            self.ok_t += dt
        else:
            self.mal_t += dt
        self.h += (self.CALOR[self.fuego] - self.h) * min(1.0, 1.2 * dt)
        self.prog = min(1.0, self.ok_t / self.necesita)
        if self.h > 0.12 and self.rnd.random() < 0.3 + 1.2 * self.h:
            self.burbujas.append([self.OLLA.x + self.rnd.uniform(-110, 110), self.OLLA.y - 20 + self.rnd.uniform(-10, 40),
                                  self.rnd.uniform(5, 16) * (0.6 + self.h), 0.0])
        for b in self.burbujas:
            b[3] += dt * (1.2 + 1.5 * self.h)
            b[1] -= dt * (30 + 60 * self.h)
        self.burbujas = [b for b in self.burbujas if b[3] < 1.0][-60:]
        if self.prog >= 1.0:
            self.terminar(self.necesita / (self.necesita + 0.6 * self.mal_t), "¡Hirvió justo bien!")

    def dibujar_boton(self, p, nivel):
        r = self.BOTONES[nivel]
        activo = self.fuego == nivel
        pide = self.req == nivel
        base = ((250, 200, 70), (245, 150, 50), (235, 80, 50))[nivel]
        col = base if activo else oscurecer(base, 0.45)
        pygame.draw.rect(p, (30, 30, 36), r.move(5, 7), border_radius=26)
        pygame.draw.rect(p, col, r, border_radius=26)
        borde = (255, 255, 255) if activo else (150, 150, 165)
        if pide and not activo:
            borde = (255, 240, 120) if (self.t % 0.7) < 0.4 else (255, 160, 60)
        pygame.draw.rect(p, borde, r, 8 if (activo or pide) else 4, border_radius=26)
        # llamitas: 1 (bajo), 2 (medio), 3 (alto)
        n = nivel + 1
        alto = (46, 66, 90)[nivel]
        x0 = r.x + 40 + (3 - n) * 22
        for k in range(n):
            _llama(p, x0 + k * 46, r.bottom - 26, alto * (1.0 if activo else 0.75), self.t * (1.0 if activo else 0.2), k)
        escribir(p, self.f.grande, self.NOMBRES[nivel], r.right - 88, r.centery - 8, (255, 255, 255) if activo else (235, 235, 240))
        if activo:
            escribir(p, self.f.chica, "encendido", r.right - 88, r.centery + 30, (255, 255, 255))
        elif self.hover_t[nivel] > 0:
            barra(p, (r.x + 24, r.bottom - 16, r.w - 48, 10), self.hover_t[nivel] / self.HOVER, color=(255, 240, 120),
                  color_fondo=(60, 55, 60), borde=(255, 255, 255))

    def dibujar_paso(self, p):
        self.pista(p, "Lleva el cursor al botón de fuego que pide la olla")
        ox, oy = int(self.OLLA.x), int(self.OLLA.y)
        h = self.h
        # llama bajo la olla (segun el fuego puesto)
        nfl = 3 + 2 * self.fuego
        sep = 240.0 / (nfl - 1)
        for k in range(nfl):
            _llama(p, ox - 120 + k * sep, oy + 152, 24 + 70 * h, self.t, k)
        pygame.draw.rect(p, (40, 42, 50), (ox - 150, oy + 145, 300, 14), border_radius=6)
        # olla
        pygame.draw.rect(p, (110, 115, 135), (ox - 165, oy - 120, 330, 255), border_radius=30)
        pygame.draw.rect(p, (150, 156, 178), (ox - 165, oy - 120, 330, 255), 6, border_radius=30)
        pygame.draw.rect(p, (70, 55, 50), (ox + 160, oy - 60, 110, 22), border_radius=10)
        pygame.draw.rect(p, (70, 55, 50), (ox - 270, oy - 60, 110, 22), border_radius=10)
        agua = _mezclar((120, 190, 235), (200, 235, 250), min(1.0, h * 1.2))
        pygame.draw.ellipse(p, (90, 100, 125), (ox - 165, oy - 150, 330, 70))
        pygame.draw.ellipse(p, agua, (ox - 152, oy - 142, 304, 54))
        # comida que hierve
        for k in range(3):
            fx = ox - 80 + k * 80 + math.sin(self.t * (1 + 2 * h) + k) * 12 * h
            fy = oy - 118 + math.cos(self.t * (1.4 + 2 * h) + k * 2) * 5 * h
            dibujar_ing(p, self.ing, fx, fy, 46, "entero", self.t)
        for b in self.burbujas:
            r = int(b[2] * (1 - 0.3 * b[3]))
            by = min(oy - 100, b[1])
            by = max(by, oy - 165)
            pygame.draw.circle(p, (235, 248, 255), (int(b[0]), int(oy - 120 + (by - oy + 120) * 0.2)), r, 3)
        txt, colm, est = self.mensaje_fuego()
        if est == "mucho":                                   # espuma que se desborda
            ex = min(1.0, 0.5 + 0.5 * (self.h - self.CALOR[self.req]) / 0.4)
            for k in range(8):
                pygame.draw.circle(p, (255, 255, 255), (ox - 150 + k * 43, int(oy - 110 + 30 * ex * math.sin(self.t * 5 + k))),
                                   int(14 + 22 * ex))
        for k in range(4):
            a = self.t * 1.3 + k * 1.7
            pygame.draw.circle(p, (235, 240, 250), (int(ox + math.sin(a) * 60 + (k - 2) * 50),
                                                    int(oy - 200 - (self.t * 35 + k * 25) % 60)), 8, 2)
        # cartel de lo que pide la olla
        pul = 3 * math.sin(self.t * 8) if est != "ok" else 0
        rc = pygame.Rect(ox - 300, 168, 600, 78)
        pygame.draw.rect(p, (30, 30, 36), rc.move(4, 6), border_radius=22)
        pygame.draw.rect(p, colm, rc.inflate(pul, pul), border_radius=22)
        pygame.draw.rect(p, (255, 255, 255), rc.inflate(pul, pul), 5, border_radius=22)
        escribir(p, self.f.normal, txt, rc.centerx + 22, rc.centery, (255, 255, 255))
        _llama(p, rc.x + 40, rc.bottom - 14, 30 + 16 * self.req, self.t, 0)
        # botones de fuego
        for nivel in (2, 1, 0):
            self.dibujar_boton(p, nivel)
        dibujar_herr(p, "mano", self.pos.x, self.pos.y + 4, 36)
