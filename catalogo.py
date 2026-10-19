"""Catalogo comun de Ninja Mundo: objetos (items), equipo de pesca y sus iconos.

Cualquier modulo puede agregar objetos nuevos con registrar_item() (por ejemplo los
platos de recetas.py). Los ids van en minusculas, sin tildes ni espacios.
"""

import math

import pygame

V2 = pygame.Vector2

ITEMS = {}


def registrar_item(ident, nombre, cat, color, forma="bolsa", precio=0, desc=""):
    """precio = lo que cuesta comprarlo en la tienda (0 = no se vende en la tienda).
    Se puede vender a la mitad del precio (minimo 1 moneda)."""
    ITEMS[ident] = dict(nombre=nombre, cat=cat, color=color, forma=forma, precio=precio, desc=desc)


def info(ident):
    """Datos de un objeto (con valores por defecto si no esta registrado)."""
    d = ITEMS.get(ident)
    if d is None:
        d = dict(nombre=ident.replace("_", " ").capitalize(), cat="otro", color=(180, 180, 195),
                 forma="bolsa", precio=0, desc="")
    return d


def nombre_item(ident):
    return info(ident)["nombre"]


def precio_venta(ident):
    p = info(ident)["precio"]
    return max(1, p // 2) if p > 0 else 1


# categoria -> titulo, en el orden en que se muestran
CATEGORIAS = [("fruta", "Frutas"), ("verdura", "Verduras"), ("granja", "Granja"),
              ("pesca", "Pesca"), ("despensa", "Despensa"), ("semilla", "Semillas"),
              ("comida", "Platos"), ("especial", "Especiales")]

# ---- frutas (las da Ninja Frutas al cortarlas; los nombres coinciden con TIPOS_FRUTA)
registrar_item("manzana", "Manzana", "fruta", (205, 45, 45), "fruta", 6, "Roja y crujiente.")
registrar_item("naranja", "Naranja", "fruta", (245, 150, 30), "fruta", 6, "Llena de jugo.")
registrar_item("limon", "Limón", "fruta", (235, 215, 60), "fruta", 5, "Muy ácido.")
registrar_item("sandia", "Sandía", "fruta", (60, 160, 80), "fruta", 10, "Grande y fresca.")
registrar_item("kiwi", "Kiwi", "fruta", (140, 100, 55), "fruta", 7, "Verde por dentro.")

# ---- verduras (huerto)
registrar_item("zanahoria", "Zanahoria", "verdura", (245, 140, 30), "alargado", 6, "Buena para los ojos.")
registrar_item("tomate", "Tomate", "verdura", (225, 60, 50), "fruta", 6, "Rojo y jugoso.")
registrar_item("lechuga", "Lechuga", "verdura", (110, 200, 90), "hoja", 6, "Fresca para ensaladas.")
registrar_item("papa", "Papa", "verdura", (200, 160, 100), "fruta", 5, "Sirve para muchos platos.")
registrar_item("maiz", "Maíz", "verdura", (245, 205, 60), "mazorca", 7, "Dorado y dulce.")
registrar_item("calabaza", "Calabaza", "verdura", (240, 150, 40), "fruta", 9, "Grande y naranja.")

# ---- granja
registrar_item("huevo", "Huevo", "granja", (250, 240, 215), "huevo", 5, "De las gallinas.")
registrar_item("leche", "Leche", "granja", (245, 245, 250), "botella", 7, "De las vacas.")
registrar_item("lana", "Lana", "granja", (235, 235, 245), "ovillo", 8, "De las ovejas.")
registrar_item("alimento_animal", "Grano para animales", "granja", (215, 180, 90), "bolsa", 4,
               "Para alimentar a los animales de la granja.")
registrar_item("alimento_peces", "Comida de peces", "granja", (130, 190, 120), "bolsa", 4,
               "Para alimentar a los peces del estanque.")

# ---- pesca
registrar_item("pescado", "Pescado", "pesca", (110, 170, 220), "pez", 9, "Fresco, listo para cocinar.")
registrar_item("huevas", "Huevas", "pesca", (240, 130, 70), "gota", 12, "Huevitos de pez.")
registrar_item("alga", "Alga", "pesca", (60, 150, 100), "alga", 5, "Del fondo del mar.")

# ---- despensa (se compran en la tienda)
registrar_item("harina", "Harina", "despensa", (245, 240, 225), "bolsa", 5, "Para panes y pasteles.")
registrar_item("azucar", "Azúcar", "despensa", (255, 250, 250), "bolsa", 5, "Dulce.")
registrar_item("sal", "Sal", "despensa", (235, 235, 240), "frasco", 3, "Una pizca da sabor.")
registrar_item("aceite", "Aceite", "despensa", (240, 205, 70), "botella", 6, "Para freír.")
registrar_item("arroz", "Arroz", "despensa", (250, 248, 238), "bolsa", 5, "Blanco y suave.")
registrar_item("chocolate", "Chocolate", "despensa", (110, 65, 40), "caja", 10, "Delicioso.")

# ---- semillas
for _id, _n, _c in (("zanahoria", "Zanahoria", (245, 140, 30)), ("tomate", "Tomate", (225, 60, 50)),
                    ("lechuga", "Lechuga", (110, 200, 90)), ("papa", "Papa", (200, 160, 100)),
                    ("maiz", "Maíz", (245, 205, 60)), ("calabaza", "Calabaza", (240, 150, 40))):
    registrar_item("semilla_" + _id, "Semillas de " + _n.lower(), "semilla", _c, "semilla", 3,
                   "Se plantan en el huerto.")

# ---- especiales
registrar_item("fragmento_estelar", "Fragmento estelar", "especial", (140, 120, 255), "gema", 15,
               "Un trocito de meteorito brillante.")
registrar_item("gema_fosil", "Gema fósil", "especial", (170, 110, 230), "gema", 20,
               "Brilla como el polvo especial.")


# =====================================================================
#  Equipo de pesca
# =====================================================================
# Cinco ranuras. Cada pieza tiene un "nivel" (1..5) y un precio en monedas.
#   cana    -> fuerza para enrollar y grado maximo de pez que puede levantar
#   cuerda  -> resistencia: cuanta tension aguanta antes de romperse
#   carrete -> tamano de la cuerda: distancia maxima de lanzamiento y profundidad
#   anzuelo -> probabilidad de clavar el anzuelo y de que el pez no se suelte
#   barco   -> zonas a las que se puede llegar (1 orilla y lago, 2 mar cercano,
#              3 mar abierto, 4 aguas profundas) y estabilidad
EQUIPO_SLOTS = [("cana", "Caña"), ("cuerda", "Cuerda"), ("carrete", "Carrete"),
                ("anzuelo", "Anzuelo"), ("barco", "Barco")]

EQUIPO = {
    "cana": {
        "cana_bambu": dict(nombre="Caña de bambú", nivel=1, precio=0, desc="La primera caña."),
        "cana_fibra": dict(nombre="Caña de fibra", nivel=2, precio=150, desc="Flexible y ligera."),
        "cana_carbono": dict(nombre="Caña de carbono", nivel=3, precio=400, desc="Fuerte y precisa."),
        "cana_titanio": dict(nombre="Caña de titanio", nivel=4, precio=900, desc="Aguanta peces grandes."),
        "cana_legendaria": dict(nombre="Caña legendaria", nivel=5, precio=2000, desc="Para los mejores pescadores."),
    },
    "cuerda": {
        "cuerda_hilo": dict(nombre="Hilo común", nivel=1, precio=0, desc="Se rompe fácil."),
        "cuerda_trenzada": dict(nombre="Hilo trenzado", nivel=2, precio=100, desc="Más resistente."),
        "cuerda_nailon": dict(nombre="Cuerda de nailon", nivel=3, precio=300, desc="Buena tensión."),
        "cuerda_reforzada": dict(nombre="Cuerda reforzada", nivel=4, precio=700, desc="Muy resistente."),
        "cuerda_acero": dict(nombre="Cuerda de acero", nivel=5, precio=1500, desc="Casi no se rompe."),
    },
    "carrete": {
        "carrete_chico": dict(nombre="Carrete chico", nivel=1, precio=0, desc="Poca cuerda."),
        "carrete_mediano": dict(nombre="Carrete mediano", nivel=2, precio=200, desc="Más cuerda."),
        "carrete_grande": dict(nombre="Carrete grande", nivel=3, precio=500, desc="Lanza lejos."),
        "carrete_gigante": dict(nombre="Carrete gigante", nivel=4, precio=1200, desc="Llega al fondo."),
    },
    "anzuelo": {
        "anzuelo_comun": dict(nombre="Anzuelo común", nivel=1, precio=0, desc="A veces se suelta."),
        "anzuelo_afilado": dict(nombre="Anzuelo afilado", nivel=2, precio=100, desc="Se clava mejor."),
        "anzuelo_acero": dict(nombre="Anzuelo de acero", nivel=3, precio=300, desc="Firme."),
        "anzuelo_dentado": dict(nombre="Anzuelo dentado", nivel=4, precio=700, desc="Casi no suelta."),
        "anzuelo_dorado": dict(nombre="Anzuelo dorado", nivel=5, precio=1500, desc="El mejor."),
    },
    "barco": {
        "bote_remos": dict(nombre="Bote de remos", nivel=1, precio=0, desc="Orilla y lago."),
        "bote_motor": dict(nombre="Bote a motor", nivel=2, precio=500, desc="Llega al mar cercano."),
        "lancha": dict(nombre="Lancha rápida", nivel=3, precio=1500, desc="Mar abierto."),
        "pesquero": dict(nombre="Barco pesquero", nivel=4, precio=4000, desc="Aguas profundas."),
    },
}

EQUIPO_INICIAL = {"cana": "cana_bambu", "cuerda": "cuerda_hilo", "carrete": "carrete_chico",
                  "anzuelo": "anzuelo_comun", "barco": "bote_remos"}


def pieza(ident):
    """(ranura, datos) de una pieza de equipo, o None."""
    for ranura, piezas in EQUIPO.items():
        if ident in piezas:
            return ranura, piezas[ident]
    return None


def stats_equipo(equipo):
    """equipo = {ranura: id}. Devuelve {ranura: nivel 1..5} (usa la pieza inicial si falta)."""
    res = {}
    for ranura, _ in EQUIPO_SLOTS:
        ident = (equipo or {}).get(ranura) or EQUIPO_INICIAL[ranura]
        datos = EQUIPO[ranura].get(ident) or EQUIPO[ranura][EQUIPO_INICIAL[ranura]]
        res[ranura] = datos["nivel"]
    return res


def nombres_equipo(equipo):
    res = {}
    for ranura, _ in EQUIPO_SLOTS:
        ident = (equipo or {}).get(ranura) or EQUIPO_INICIAL[ranura]
        datos = EQUIPO[ranura].get(ident) or EQUIPO[ranura][EQUIPO_INICIAL[ranura]]
        res[ranura] = datos["nombre"]
    return res


# =====================================================================
#  Iconos de objetos (sencillos, procedurales)
# =====================================================================

def _osc(c, f=0.35):
    return tuple(int(v * (1 - f)) for v in c)


def _cla(c, f=0.45):
    return tuple(int(v + (255 - v) * f) for v in c)


def dibujar_item(p, ident, x, y, tam=48):
    """Dibuja el icono del objeto centrado en (x, y), dentro de un cuadro de 'tam' px."""
    d = info(ident)
    c, forma, r = d["color"], d["forma"], tam / 2
    x, y = int(x), int(y)
    borde = _osc(c)
    if forma == "fruta":
        pygame.draw.circle(p, c, (x, y + 2), int(r * 0.82))
        pygame.draw.circle(p, borde, (x, y + 2), int(r * 0.82), 2)
        pygame.draw.circle(p, _cla(c), (x - int(r * 0.3), y - int(r * 0.2)), max(2, int(r * 0.18)))
        pygame.draw.line(p, (95, 65, 30), (x, y - int(r * 0.75)), (x + 2, y - int(r * 1.0)), 3)
        pygame.draw.ellipse(p, (70, 170, 70), (x + 2, y - int(r * 1.0), int(r * 0.5), int(r * 0.28)))
    elif forma == "alargado":
        pts = [(x - int(r * 0.45), y - int(r * 0.7)), (x + int(r * 0.45), y - int(r * 0.7)), (x, y + int(r * 0.95))]
        pygame.draw.polygon(p, c, pts)
        pygame.draw.polygon(p, borde, pts, 2)
        for k in (-1, 1):
            pygame.draw.line(p, (70, 170, 70), (x, y - int(r * 0.7)), (x + k * int(r * 0.35), y - int(r * 1.0)), 4)
    elif forma == "hoja":
        for dx, dy in ((-0.4, 0.1), (0.4, 0.1), (0.0, -0.25), (0.0, 0.35)):
            pygame.draw.circle(p, c, (x + int(dx * r), y + int(dy * r)), int(r * 0.5))
            pygame.draw.circle(p, borde, (x + int(dx * r), y + int(dy * r)), int(r * 0.5), 2)
    elif forma == "mazorca":
        pygame.draw.ellipse(p, c, (x - int(r * 0.4), y - int(r * 0.9), int(r * 0.8), int(r * 1.8)))
        pygame.draw.ellipse(p, borde, (x - int(r * 0.4), y - int(r * 0.9), int(r * 0.8), int(r * 1.8)), 2)
        for k in range(3):
            pygame.draw.line(p, borde, (x - int(r * 0.3), y - int(r * 0.4) + k * int(r * 0.4)),
                             (x + int(r * 0.3), y - int(r * 0.4) + k * int(r * 0.4)), 2)
        pygame.draw.polygon(p, (80, 170, 80), [(x - int(r * 0.4), y + int(r * 0.9)), (x, y), (x - int(r * 0.9), y + int(r * 0.2))])
    elif forma == "huevo":
        pygame.draw.ellipse(p, c, (x - int(r * 0.6), y - int(r * 0.8), int(r * 1.2), int(r * 1.6)))
        pygame.draw.ellipse(p, borde, (x - int(r * 0.6), y - int(r * 0.8), int(r * 1.2), int(r * 1.6)), 2)
    elif forma == "botella":
        pygame.draw.rect(p, c, (x - int(r * 0.45), y - int(r * 0.35), int(r * 0.9), int(r * 1.3)), border_radius=6)
        pygame.draw.rect(p, c, (x - int(r * 0.2), y - int(r * 0.9), int(r * 0.4), int(r * 0.6)))
        pygame.draw.rect(p, borde, (x - int(r * 0.45), y - int(r * 0.35), int(r * 0.9), int(r * 1.3)), 2, border_radius=6)
        pygame.draw.rect(p, (200, 70, 70), (x - int(r * 0.25), y - int(r * 1.0), int(r * 0.5), int(r * 0.2)))
    elif forma == "ovillo":
        pygame.draw.circle(p, c, (x, y), int(r * 0.8))
        pygame.draw.circle(p, borde, (x, y), int(r * 0.8), 2)
        for k in range(3):
            pygame.draw.arc(p, borde, (x - int(r * 0.7), y - int(r * 0.7) + k * 6, int(r * 1.4), int(r * 1.0)), 0.2, 2.9, 2)
    elif forma == "pez":
        pygame.draw.ellipse(p, c, (x - int(r * 0.85), y - int(r * 0.45), int(r * 1.4), int(r * 0.9)))
        pygame.draw.polygon(p, c, [(x + int(r * 0.4), y), (x + int(r * 0.95), y - int(r * 0.5)), (x + int(r * 0.95), y + int(r * 0.5))])
        pygame.draw.circle(p, (255, 255, 255), (x - int(r * 0.45), y - int(r * 0.1)), max(2, int(r * 0.13)))
        pygame.draw.circle(p, (20, 20, 40), (x - int(r * 0.45), y - int(r * 0.1)), max(1, int(r * 0.06)))
    elif forma == "gota":
        for dx, dy in ((-0.35, 0.2), (0.3, 0.3), (0.0, -0.25), (0.45, -0.2), (-0.3, -0.35)):
            pygame.draw.circle(p, c, (x + int(dx * r), y + int(dy * r)), max(3, int(r * 0.3)))
            pygame.draw.circle(p, _cla(c), (x + int(dx * r) - 2, y + int(dy * r) - 2), max(1, int(r * 0.09)))
    elif forma == "alga":
        for k, dx in enumerate((-0.45, 0.0, 0.45)):
            pts = [(x + int(dx * r) + int(math.sin(j * 0.9 + k) * r * 0.2), y + int(r * 0.9) - j * int(r * 0.3)) for j in range(7)]
            pygame.draw.lines(p, c, False, pts, 5)
    elif forma == "frasco":
        pygame.draw.rect(p, _cla(c, 0.6), (x - int(r * 0.45), y - int(r * 0.5), int(r * 0.9), int(r * 1.4)), border_radius=7)
        pygame.draw.rect(p, c, (x - int(r * 0.4), y - int(r * 0.1), int(r * 0.8), int(r * 0.95)), border_radius=5)
        pygame.draw.rect(p, (120, 120, 140), (x - int(r * 0.5), y - int(r * 0.8), int(r * 1.0), int(r * 0.35)), border_radius=4)
    elif forma == "semilla":
        pygame.draw.rect(p, (225, 200, 150), (x - int(r * 0.6), y - int(r * 0.2), int(r * 1.2), int(r * 1.0)), border_radius=8)
        pygame.draw.rect(p, _osc((225, 200, 150)), (x - int(r * 0.6), y - int(r * 0.2), int(r * 1.2), int(r * 1.0)), 2, border_radius=8)
        pygame.draw.circle(p, c, (x, y + int(r * 0.3)), max(4, int(r * 0.25)))
        pygame.draw.line(p, (70, 160, 70), (x, y - int(r * 0.2)), (x, y - int(r * 0.7)), 3)
        pygame.draw.ellipse(p, (90, 190, 90), (x, y - int(r * 0.9), int(r * 0.5), int(r * 0.3)))
    elif forma == "gema":
        pts = [(x, y - int(r * 0.9)), (x + int(r * 0.7), y - int(r * 0.2)), (x + int(r * 0.4), y + int(r * 0.8)),
               (x - int(r * 0.4), y + int(r * 0.8)), (x - int(r * 0.7), y - int(r * 0.2))]
        pygame.draw.polygon(p, c, pts)
        pygame.draw.polygon(p, borde, pts, 2)
        pygame.draw.polygon(p, _cla(c, 0.6), [pts[0], pts[1], (x, y)], 0)
    elif forma == "plato":
        pygame.draw.ellipse(p, (245, 245, 250), (x - int(r * 0.95), y, int(r * 1.9), int(r * 0.8)))
        pygame.draw.ellipse(p, borde, (x - int(r * 0.95), y, int(r * 1.9), int(r * 0.8)), 2)
        pygame.draw.circle(p, c, (x, y + 2), int(r * 0.55))
        pygame.draw.circle(p, _cla(c), (x - int(r * 0.2), y - int(r * 0.15)), max(2, int(r * 0.15)))
    elif forma == "caja":
        pygame.draw.rect(p, c, (x - int(r * 0.7), y - int(r * 0.55), int(r * 1.4), int(r * 1.1)), border_radius=5)
        pygame.draw.rect(p, borde, (x - int(r * 0.7), y - int(r * 0.55), int(r * 1.4), int(r * 1.1)), 2, border_radius=5)
        pygame.draw.line(p, _cla(c, 0.5), (x - int(r * 0.7), y), (x + int(r * 0.7), y), 2)
    else:                                              # bolsa
        pygame.draw.rect(p, c, (x - int(r * 0.65), y - int(r * 0.45), int(r * 1.3), int(r * 1.3)), border_radius=10)
        pygame.draw.rect(p, borde, (x - int(r * 0.65), y - int(r * 0.45), int(r * 1.3), int(r * 1.3)), 2, border_radius=10)
        pygame.draw.polygon(p, borde, [(x - int(r * 0.35), y - int(r * 0.45)), (x + int(r * 0.35), y - int(r * 0.45)),
                                       (x + int(r * 0.2), y - int(r * 0.85)), (x - int(r * 0.2), y - int(r * 0.85))])
        pygame.draw.circle(p, _cla(c, 0.6), (x, y + int(r * 0.2)), max(3, int(r * 0.22)))
