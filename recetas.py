"""Recetas y habilidades de la Cocina de Ninja Mundo (solo datos y reglas, sin dibujar).

HABILIDADES  picar, mezclar, sazonar, hornear, servir. `perfil.habilidades[id]` guarda la
             experiencia (XP); `nivel_habilidad(xp)` la convierte en nivel 1..5.
RECETAS      18 recetas: dificultad 1..5, habilidades minimas, materiales que se gastan del
             inventario y la lista de pasos. Las recetas con `basica=True` no piden
             habilidades ni materiales (usan "ingredientes de la casa"): siempre hay 4.
PLATOS       al importar este modulo se registra en el catalogo un objeto `plato_<id>` por receta,
             con un precio de tienda tal que venderlo (la mitad) deja ganancia sobre sus materiales.
"""

import catalogo

HABILIDADES = {
    "picar": dict(nombre="Picar", desc="Cortar con el cuchillo"),
    "mezclar": dict(nombre="Mezclar", desc="Revolver con la cuchara"),
    "sazonar": dict(nombre="Sazonar", desc="Poner sal y especias"),
    "hornear": dict(nombre="Hornear", desc="Cocinar en el horno a tiempo"),
    "servir": dict(nombre="Servir", desc="Poner el plato bonito"),
}
ORDEN_HAB = ("picar", "mezclar", "sazonar", "hornear", "servir")

# XP acumulada necesaria para llegar a cada nivel (nivel 1 = 0 XP)
NIVEL_XP = (0, 25, 70, 140, 240)
NIVEL_MAX = len(NIVEL_XP)


def nivel_habilidad(xp):
    """Nivel 1..5 segun la experiencia acumulada."""
    n = 1
    for i, lim in enumerate(NIVEL_XP):
        if xp >= lim:
            n = i + 1
    return n


def progreso_habilidad(xp):
    """(nivel, xp dentro del nivel, xp que mide el nivel, fraccion 0..1). En el nivel maximo la barra va llena."""
    n = nivel_habilidad(xp)
    if n >= NIVEL_MAX:
        return n, 0, 0, 1.0
    base, sig = NIVEL_XP[n - 1], NIVEL_XP[n]
    return n, int(xp - base), sig - base, max(0.0, min(1.0, (xp - base) / (sig - base)))


def niveles(perfil):
    """{habilidad: nivel} de todo el perfil."""
    return {h: nivel_habilidad(perfil.habilidades.get(h, 0)) for h in ORDEN_HAB}


def xp_paso(dif, frac):
    """XP que da un paso de una receta de dificultad `dif` hecho con exito `frac` (0..1)."""
    return int(round((10 + 4 * dif) * max(0.0, min(1.0, frac))))


def dar_xp(perfil, ganado):
    """Suma XP ({habilidad: xp}) al perfil y devuelve las subidas de nivel [(hab, nivel_nuevo)]."""
    subidas = []
    for h, xp in ganado.items():
        if xp <= 0:
            continue
        antes = nivel_habilidad(perfil.habilidades.get(h, 0))
        perfil.habilidades[h] = perfil.habilidades.get(h, 0) + int(xp)
        despues = nivel_habilidad(perfil.habilidades[h])
        if despues > antes:
            subidas.append((h, despues))
    return subidas


def _R(ident, nombre, dif, hab, mats, pasos, ing, rec, cont, plato, basica=False):
    return dict(id=ident, nombre=nombre, dif=dif, hab=hab, mats=mats, pasos=pasos, ing=ing, rec=rec,
                cont=cont, plato=plato, basica=basica)


P, M, S, H, V = "picar", "mezclar", "sazonar", "hornear", "servir"

RECETAS = [
    # ---- dificultad 1 (las 3 primeras son basicas)
    _R("ensalada_frutas", "Ensalada de frutas", 1, {}, {}, [P, M, V], ("redondo", (235, 70, 60)), "bol",
       (250, 190, 90), "frutas", True),
    _R("jugo", "Jugo de naranja", 1, {}, {}, [P, M, V], ("redondo", (245, 150, 30)), "bol",
       (250, 165, 40), "jugo", True),
    _R("pan_dulce", "Pan con mermelada", 1, {}, {}, [P, S, V], ("pan", (240, 205, 140)), "bol",
       (205, 60, 80), "tostada", True),
    _R("ensalada", "Ensalada fresca", 1, {}, {"lechuga": 1, "tomate": 1}, [P, M, S, V],
       ("hoja", (110, 200, 90)), "bol", (150, 215, 100), "ensalada"),
    # ---- dificultad 2
    _R("tortilla", "Tortilla de huevo", 2, {M: 2}, {"huevo": 2}, [P, M, H, V],
       ("largo", (235, 205, 140)), "bol", (250, 225, 90), "tortilla"),
    _R("sopa_zanahoria", "Sopa de zanahoria", 2, {P: 2}, {"zanahoria": 2}, [P, M, S, V],
       ("largo", (245, 140, 40)), "olla", (250, 150, 50), "sopa"),
    _R("panqueques", "Panqueques", 2, {M: 2}, {"harina": 1, "huevo": 1, "leche": 1}, [M, M, H, V],
       ("redondo", (240, 215, 150)), "bol", (150, 90, 40), "panqueques"),
    _R("arroz", "Arroz con verduras", 2, {S: 2}, {"arroz": 1, "zanahoria": 1}, [P, M, S, V],
       ("largo", (245, 140, 40)), "bol", (250, 250, 240), "arroz"),
    # ---- dificultad 3
    _R("pizza", "Pizza casera", 3, {P: 2, H: 2}, {"harina": 1, "tomate": 2}, [P, M, S, H, V],
       ("redondo", (250, 210, 80)), "bol", (225, 70, 55), "pizza"),
    _R("sopa_pescado", "Sopa de pescado", 3, {P: 2, S: 2}, {"pescado": 1, "zanahoria": 1}, [P, P, M, S, V],
       ("pez", (170, 190, 210)), "olla", (245, 170, 70), "sopa"),
    _R("galletas", "Galletas dulces", 3, {M: 3, H: 2}, {"harina": 1, "azucar": 1, "huevo": 1}, [M, M, S, H, V],
       ("redondo", (230, 175, 95)), "bol", (230, 175, 95), "galletas"),
    _R("tarta", "Tarta de manzana", 3, {P: 3, H: 2}, {"manzana": 2, "harina": 1, "azucar": 1}, [P, M, M, H, V],
       ("redondo", (205, 45, 45)), "bol", (210, 80, 60), "tarta"),
    # ---- dificultad 4
    _R("sushi", "Sushi de pescado", 4, {P: 3, V: 3}, {"arroz": 1, "pescado": 1, "alga": 1}, [P, P, M, S, V, V],
       ("pez", (170, 190, 210)), "bol", (250, 250, 245), "sushi"),
    _R("pastel_chocolate", "Pastel de chocolate", 4, {M: 3, H: 3},
       {"harina": 2, "huevo": 2, "chocolate": 1, "azucar": 1}, [P, M, M, S, H, V],
       ("largo", (110, 65, 40)), "bol", (110, 65, 40), "pastel"),
    _R("ceviche", "Ceviche fresco", 4, {P: 3, S: 3}, {"pescado": 2, "limon": 2, "sal": 1}, [P, P, M, S, S, V],
       ("pez", (170, 190, 210)), "bol", (225, 240, 235), "ceviche"),
    # ---- dificultad 5
    _R("paella", "Paella marinera", 5, {P: 3, S: 3, H: 3},
       {"arroz": 2, "pescado": 1, "huevas": 1, "tomate": 1, "aceite": 1}, [P, P, M, S, H, S, V],
       ("pez", (170, 190, 210)), "olla", (250, 205, 70), "paella"),
    _R("pastel_frutas", "Pastel de frutas", 5, {M: 4, H: 4, P: 3},
       {"harina": 2, "azucar": 2, "huevo": 2, "manzana": 1, "naranja": 1, "leche": 1}, [P, P, M, M, S, H, V],
       ("redondo", (245, 150, 30)), "bol", (250, 140, 150), "pastel_frutas"),
    _R("pescado_papas", "Pescado con papas", 5, {P: 4, S: 4, H: 3},
       {"pescado": 1, "papa": 2, "aceite": 1, "sal": 1, "limon": 1}, [P, P, M, S, H, H, V],
       ("pez", (170, 190, 210)), "olla", (235, 190, 70), "pescado_papas"),
]
POR_ID = {r["id"]: r for r in RECETAS}


def plato_id(receta):
    return "plato_" + receta["id"]


def _costo_materiales(r):
    return sum(catalogo.info(m)["precio"] * n for m, n in r["mats"].items())


def _registrar_platos():
    for r in RECETAS:
        # vender = mitad del precio: siempre mas que lo que cuestan sus materiales en la tienda
        r["precio"] = 2 * _costo_materiales(r) + 6 + 4 * r["dif"]
        catalogo.registrar_item(plato_id(r), r["nombre"], "comida", r["cont"], "plato", r["precio"],
                                "Receta de dificultad %d." % r["dif"])


_registrar_platos()


# ----------------------------------------------------------------------------- reglas
def habilidades_faltantes(perfil, r):
    """[(habilidad, nivel pedido)] que aun no se alcanzan, en orden de habilidades."""
    niv = niveles(perfil)
    return [(h, n) for h in ORDEN_HAB for hh, n in r["hab"].items() if hh == h and niv[h] < n]


def materiales_faltantes(perfil, r):
    """{material: cuantos faltan}. Las recetas basicas nunca piden nada."""
    if r["basica"]:
        return {}
    return {m: n - perfil.cantidad(m) for m, n in r["mats"].items() if perfil.cantidad(m) < n}


def desbloqueada(perfil, r):
    """True si se cumplen los prerrequisitos de habilidad (no mira los materiales)."""
    return not habilidades_faltantes(perfil, r)


def jugable(perfil, r):
    return desbloqueada(perfil, r) and not materiales_faltantes(perfil, r)


def motivo_bloqueo(perfil, r):
    """Frase corta de por que no se puede cocinar, o None si se puede."""
    hf = habilidades_faltantes(perfil, r)
    if hf:
        if len(hf) == 1:
            return "Necesitas %s nivel %d" % (HABILIDADES[hf[0][0]]["nombre"], hf[0][1])
        return "Necesitas " + ", ".join("%s %d" % (HABILIDADES[h]["nombre"], n) for h, n in hf)
    mf = materiales_faltantes(perfil, r)
    if mf:
        nombres = [catalogo.nombre_item(m) for m in mf]
        return "Te falta: " + nombres[0] + (" y %d más" % (len(nombres) - 1) if len(nombres) > 1 else "")
    return None


def puntos_por_paso(r, nivel):
    """Puntos de un paso perfecto: mas dificultad de la receta y mas nivel de juego = mas puntos."""
    return (3 + r["dif"]) * (1 + 0.12 * (nivel - 1))


def puntos_bono(r, nivel):
    return (2 + 2 * r["dif"]) * (1 + 0.12 * (nivel - 1))


def puntos_maximos(r, nivel):
    return len(r["pasos"]) * puntos_por_paso(r, nivel) + puntos_bono(r, nivel)


def metas_receta(r, nivel):
    """Puntos para 1, 2 y 3 estrellas: 30%, 60% y 85% del maximo."""
    m = puntos_maximos(r, nivel)
    return (max(3, int(round(m * 0.30))), int(round(m * 0.60)), int(round(m * 0.85)))


def recomendadas(perfil, nivel):
    """Ids de las recetas jugables que mas se acercan a la dificultad `nivel` sin pasarse
    (si no hay, las mas faciles). Se destacan con "Para ti" en el libro."""
    jug = [r for r in RECETAS if jugable(perfil, r)]
    if not jug:
        jug = [r for r in RECETAS if desbloqueada(perfil, r)]
    if not jug:
        return []
    debajo = [r for r in jug if r["dif"] <= nivel]
    objetivo = max(r["dif"] for r in debajo) if debajo else min(r["dif"] for r in jug)
    return [r["id"] for r in jug if r["dif"] == objetivo]
