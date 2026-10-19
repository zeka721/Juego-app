"""Cocina v2: habilidades, reglas, ingredientes nuevos y recetas (solo datos y calculos, sin dibujar).

HABILIDADES   22 habilidades (cortar, pelar, rayar, extraer, exprimir, aplastar, presionar, moldear, enrollar,
              untar, espolvorear, decorar, combinar, girar, batir, cucharear, verter, mover_sarten, saltear,
              hornear, hervir, servir). `perfil.habilidades[id]` guarda la experiencia (XP): nivel 1..5.
RECETAS       30 recetas (cocina_recetas.py), una por NIVEL 1..30. Cada receta tiene estrellas (1..5, su
              complejidad), una lista de pasos (cada paso = una habilidad sobre un ingrediente), materiales que se
              gastan del inventario y requisitos de habilidad. Las `basica=True` usan "ingredientes de la casa".
FLUJO         preparar los ingredientes crudos (cortar, pelar, rayar, extraer...) -> montar/combinar (combinar,
              batir, girar, cucharear...) -> cocinar (mover_sarten, saltear, hornear, hervir) -> servir.
"""

import catalogo

# ----------------------------------------------------------------------------- habilidades
# id: nombre, descripcion corta, herramientas (cursor), fase habitual, color
HABILIDADES = {
    "cortar": dict(nombre="Cortar", desc="Con cuchillo o tijera, según lo que cortes", herr="cuchillo / tijera",
                   fase="preparar", color=(215, 222, 235)),
    "pelar": dict(nombre="Pelar", desc="Quitar la cáscara con el pelador", herr="pelador",
                  fase="preparar", color=(120, 200, 100)),
    "rayar": dict(nombre="Rallar", desc="Rallar queso, chocolate y más", herr="rallador",
                  fase="preparar", color=(250, 215, 90)),
    "extraer": dict(nombre="Extraer", desc="Quitar escamas o la cáscara de los langostinos", herr="cuchara / tijera",
                    fase="preparar", color=(110, 170, 220)),
    "exprimir": dict(nombre="Exprimir", desc="Sacar el jugo de los cítricos", herr="exprimidor",
                     fase="preparar", color=(245, 190, 40)),
    "aplastar": dict(nombre="Aplastar", desc="Lanzar y aplastar la masa", herr="manos",
                     fase="preparar", color=(240, 215, 160)),
    "presionar": dict(nombre="Presionar", desc="Con rodillo o con tenedor", herr="rodillo / tenedor",
                      fase="preparar", color=(200, 160, 110)),
    "moldear": dict(nombre="Moldear", desc="Dar forma con moldes o con las manos", herr="molde",
                    fase="preparar", color=(240, 130, 150)),
    "enrollar": dict(nombre="Enrollar", desc="Enrollar la base con su relleno", herr="manos",
                     fase="montar", color=(220, 160, 90)),
    "untar": dict(nombre="Untar", desc="Mantequilla, queso crema, mermelada...", herr="espátula",
                  fase="montar", color=(250, 225, 120)),
    "espolvorear": dict(nombre="Espolvorear", desc="Sal, harina, canela, azúcar...", herr="salero / cernidor",
                        fase="montar", color=(235, 235, 245)),
    "decorar": dict(nombre="Decorar", desc="Adornar con crema o chocolate", herr="manga pastelera",
                    fase="servir", color=(250, 160, 200)),
    "combinar": dict(nombre="Combinar", desc="Juntar varios ingredientes en un cuenco", herr="manos",
                     fase="montar", color=(150, 190, 240)),
    "girar": dict(nombre="Girar", desc="Revolver en círculos con la cuchara", herr="cuchara",
                  fase="montar", color=(190, 150, 230)),
    "batir": dict(nombre="Batir", desc="Batir huevos, cremas y masas", herr="batidor",
                  fase="montar", color=(255, 200, 120)),
    "cucharear": dict(nombre="Cucharear", desc="Pasar cucharadas de un cuenco a otro lugar", herr="cuchara",
                      fase="montar", color=(200, 190, 150)),
    "verter": dict(nombre="Verter", desc="Echar líquidos sin derramar", herr="jarra",
                   fase="montar", color=(130, 200, 230)),
    "mover_sarten": dict(nombre="Mover la sartén", desc="Repartir la mantequilla o la salsa", herr="sartén",
                         fase="cocinar", color=(120, 125, 140)),
    "saltear": dict(nombre="Saltear", desc="Hacer saltar la comida en la sartén", herr="sartén",
                    fase="cocinar", color=(240, 120, 60)),
    "hornear": dict(nombre="Hornear", desc="Sacar del horno en su punto", herr="horno",
                    fase="cocinar", color=(220, 110, 60)),
    "hervir": dict(nombre="Hervir", desc="Cuidar el fuego de la olla", herr="fuego",
                   fase="cocinar", color=(90, 170, 230)),
    "servir": dict(nombre="Servir", desc="Poner el plato bonito en la mesa", herr="plato",
                   fase="servir", color=(240, 190, 90)),
}
ORDEN_HAB = tuple(HABILIDADES)
FASES = ("preparar", "montar", "cocinar", "servir")
NOMBRE_FASE = {"preparar": "Preparar", "montar": "Mezclar y montar", "cocinar": "Cocinar", "servir": "Servir"}

# habilidades de la version anterior -> nueva (se migran las guardadas en perfil.habilidades)
MIGRACION_HAB = {"picar": "cortar", "mezclar": "girar", "sazonar": "espolvorear"}

# XP acumulada necesaria para llegar a cada nivel de habilidad (nivel 1 = 0 XP)
NIVEL_XP = (0, 25, 70, 140, 240)
NIVEL_MAX_HAB = len(NIVEL_XP)

# ----------------------------------------------------------------------------- niveles de receta
NIVELES = 30
# cantidad de pasos (habilidades aplicadas) de la receta de cada nivel 1..30
PASOS_NIVEL = {1: 4, 2: 4, 3: 5, 4: 5, 5: 6, 6: 6, 7: 7, 8: 8, 9: 8, 10: 9, 11: 9, 12: 10, 13: 11, 14: 11, 15: 12,
               16: 13, 17: 14, 18: 14, 19: 15, 20: 16, 21: 16, 22: 17, 23: 18, 24: 19, 25: 20, 26: 21, 27: 22,
               28: 23, 29: 24, 30: 25}


def estrellas_receta(nivel):
    """Complejidad de la receta en estrellas (1..5): niveles 1-6 = 1, 7-12 = 2, ..., 25-30 = 5."""
    return 1 + (max(1, min(NIVELES, nivel)) - 1) // 6


def dif_nivel(nivel):
    """Dificultad de los pasos 0..10 segun el nivel de la receta (los pasos la usan para endurecerse)."""
    return 10.0 * (max(1, min(NIVELES, nivel)) - 1) / (NIVELES - 1)


def nivel_hab_requerido(nivel):
    """Nivel minimo (1..4) que se pide en cada habilidad usada por una receta de ese nivel."""
    return 1 + (max(1, min(NIVELES, nivel)) - 1) // 8


# ----------------------------------------------------------------------------- ingredientes
# Ingredientes de la casa: las recetas `basica` los usan sin gastar nada del inventario.
CASA = ("agua", "sal", "azucar", "aceite", "harina", "huevo", "leche", "naranja", "manzana", "limon", "pan",
        "mermelada", "mantequilla")

# Ingredientes que NO son objetos del inventario: resultados de pasos anteriores (los dibuja cocina_ingredientes).
PSEUDO = ("masa", "masa_plana", "mezcla", "batido", "crema_batida", "salsa", "caldo", "relleno", "pure", "bizcocho",
          "base", "pasta_cocida", "arroz_cocido", "glaseado", "jugo", "huevo_batido", "pan_rebanado", "tortilla",
          "rollo", "empanada", "galleta", "bolitas", "panqueque", "pizza")

# Objetos nuevos (se registran en el catalogo al importar este modulo).
# id: (nombre, categoria, color, forma de icono, precio de tienda, descripcion, fuente)
#   fuente: huerto | pesca | tienda (despensa). Los de huerto necesitan sus semillas; los de pesca salen pescando.
NUEVOS_ITEMS = {
    "cebolla": ("Cebolla", "verdura", (205, 120, 165), "fruta", 6, "Hace llorar, pero da sabor.", "huerto"),
    "pimiento": ("Pimiento", "verdura", (225, 55, 45), "fruta", 7, "Rojo y dulce.", "huerto"),
    "espinaca": ("Espinaca", "verdura", (60, 150, 75), "hoja", 6, "Hojas verdes y fuertes.", "huerto"),
    "pepino": ("Pepino", "verdura", (85, 175, 90), "alargado", 6, "Fresco y crujiente.", "huerto"),
    "langostino": ("Langostino", "pesca", (250, 140, 100), "gota", 14, "Tiene una cáscara que se quita.", "pesca"),
    "calamar": ("Calamar", "pesca", (235, 170, 185), "pez", 12, "Suave y rosado.", "pesca"),
    "mantequilla": ("Mantequilla", "despensa", (250, 225, 120), "caja", 8, "Para untar y hornear.", "tienda"),
    "queso": ("Queso", "despensa", (250, 205, 80), "caja", 12, "Se puede rallar.", "tienda"),
    "crema": ("Crema", "despensa", (250, 250, 238), "frasco", 9, "Se bate para hacer nata.", "tienda"),
    "levadura": ("Levadura", "despensa", (225, 195, 140), "bolsa", 5, "Hace crecer la masa.", "tienda"),
    "canela": ("Canela", "despensa", (170, 100, 60), "alargado", 7, "Huele riquísimo.", "tienda"),
    "miel": ("Miel", "despensa", (240, 170, 30), "frasco", 9, "Dulce y dorada.", "tienda"),
    "mermelada": ("Mermelada", "despensa", (200, 50, 85), "frasco", 8, "De frutas.", "tienda"),
    "fideos": ("Fideos", "despensa", (245, 215, 140), "bolsa", 6, "Para la pasta.", "tienda"),
    "pan": ("Pan", "despensa", (225, 175, 100), "bolsa", 5, "Recién horneado.", "tienda"),
    "carne": ("Carne", "despensa", (190, 60, 60), "caja", 16, "Para guisos y rellenos.", "tienda"),
    "pollo": ("Pollo", "despensa", (240, 200, 160), "caja", 15, "Tierno y rico.", "tienda"),
    "nueces": ("Nueces", "despensa", (150, 105, 60), "fruta", 11, "Crujientes.", "tienda"),
    "crema_cacao": ("Crema de cacao", "despensa", (120, 70, 45), "frasco", 11, "Para untar.", "tienda"),
}
# semillas de los cultivos nuevos (el huerto las usa igual que las demas)
CULTIVOS_NUEVOS = ("cebolla", "pimiento", "espinaca", "pepino")


def _registrar_items():
    for ident, (nombre, cat, color, forma, precio, desc, _fuente) in NUEVOS_ITEMS.items():
        catalogo.registrar_item(ident, nombre, cat, color, forma, precio, desc)
    for c in CULTIVOS_NUEVOS:
        nombre, _cat, color = NUEVOS_ITEMS[c][0], NUEVOS_ITEMS[c][1], NUEVOS_ITEMS[c][2]
        catalogo.registrar_item("semilla_" + c, "Semillas de " + nombre.lower(), "semilla", color, "semilla", 3,
                                "Se plantan en el huerto.")


_registrar_items()


def fuente_de(ident):
    """De donde sale un ingrediente: 'huerto', 'granja', 'pesca', 'tienda' o 'casa'."""
    if ident in NUEVOS_ITEMS:
        return NUEVOS_ITEMS[ident][6]
    if ident in ("huevo", "leche"):
        return "granja"
    if ident in ("zanahoria", "tomate", "lechuga", "papa", "maiz", "calabaza"):
        return "huerto"
    if ident in ("pescado", "huevas", "alga"):
        return "pesca"
    if ident in ("manzana", "naranja", "limon", "sandia", "kiwi"):
        return "frutas"
    if ident in ("harina", "azucar", "sal", "aceite", "arroz", "chocolate"):
        return "tienda"
    return "casa"


# ----------------------------------------------------------------------------- recetas
def _cargar_recetas():
    from cocina_recetas import RECETAS as crudas
    res = []
    for r in crudas:
        r = dict(r)
        r.setdefault("basica", False)
        r.setdefault("mats", {})
        r.setdefault("desc", "")
        r.setdefault("color", (240, 190, 100))
        r.setdefault("cont", "plato")
        r["estrellas"] = estrellas_receta(r["nivel"])
        r["dif"] = r["estrellas"]                      # compatibilidad con el codigo viejo
        r["hab"] = {}                                   # {habilidad: nivel minimo}
        for s in r["pasos"]:
            if r["nivel"] > 8:
                r["hab"][s["h"]] = nivel_hab_requerido(r["nivel"])
        res.append(r)
    res.sort(key=lambda r: r["nivel"])
    return res


RECETAS = _cargar_recetas()
POR_ID = {r["id"]: r for r in RECETAS}
POR_NIVEL = {r["nivel"]: r for r in RECETAS}


def plato_id(receta):
    return "plato_" + receta["id"]


def _costo_materiales(r):
    return sum(catalogo.info(m)["precio"] * n for m, n in r["mats"].items())


def _registrar_platos():
    for r in RECETAS:
        # vender = mitad del precio: siempre mas que lo que cuestan sus materiales en la tienda
        r["precio"] = 2 * _costo_materiales(r) + 8 + 5 * r["nivel"]
        catalogo.registrar_item(plato_id(r), r["nombre"], "comida", r["color"], "plato", r["precio"],
                                "Receta de nivel %d." % r["nivel"])


_registrar_platos()


# ----------------------------------------------------------------------------- experiencia de habilidades
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
    if n >= NIVEL_MAX_HAB:
        return n, 0, 0, 1.0
    base, sig = NIVEL_XP[n - 1], NIVEL_XP[n]
    return n, int(xp - base), sig - base, max(0.0, min(1.0, (xp - base) / (sig - base)))


def migrar_habilidades(perfil):
    """Pasa la XP de las habilidades de la version anterior (picar, mezclar, sazonar) a las nuevas. Idempotente."""
    h = perfil.habilidades
    cambiado = False
    for viejo, nuevo in MIGRACION_HAB.items():
        if viejo in h:
            h[nuevo] = h.get(nuevo, 0) + int(h.pop(viejo))
            cambiado = True
    return cambiado


def niveles(perfil):
    """{habilidad: nivel 1..5} de todo el perfil."""
    migrar_habilidades(perfil)
    return {h: nivel_habilidad(perfil.habilidades.get(h, 0)) for h in ORDEN_HAB}


def xp_paso(estrellas, calidad):
    """XP que da un paso de una receta de `estrellas` hecho con calidad 0..1."""
    return int(round((8 + 4 * estrellas) * max(0.0, min(1.0, calidad))))


def dar_xp(perfil, ganado):
    """Suma XP ({habilidad: xp}) al perfil y devuelve las subidas de nivel [(hab, nivel_nuevo)]."""
    migrar_habilidades(perfil)
    subidas = []
    for h, xp in ganado.items():
        if xp <= 0 or h not in HABILIDADES:
            continue
        antes = nivel_habilidad(perfil.habilidades.get(h, 0))
        perfil.habilidades[h] = perfil.habilidades.get(h, 0) + int(xp)
        despues = nivel_habilidad(perfil.habilidades[h])
        if despues > antes:
            subidas.append((h, despues))
    return subidas


# ----------------------------------------------------------------------------- reglas de receta
def habilidades_de(r):
    """Habilidades distintas que usa la receta, en orden de aparicion."""
    vistas = []
    for s in r["pasos"]:
        if s["h"] not in vistas:
            vistas.append(s["h"])
    return vistas


def habilidades_faltantes(perfil, r):
    """[(habilidad, nivel pedido)] que aun no se alcanzan."""
    niv = niveles(perfil)
    return [(h, n) for h, n in r["hab"].items() if niv.get(h, 1) < n]


def materiales_faltantes(perfil, r):
    """{material: cuantos faltan}. Las recetas basicas nunca piden nada."""
    if r["basica"]:
        return {}
    return {m: n - perfil.cantidad(m) for m, n in r["mats"].items() if perfil.cantidad(m) < n}


def desbloqueada(perfil, r):
    from ajustes import MODO_PRUEBA
    return MODO_PRUEBA or not habilidades_faltantes(perfil, r)


def jugable(perfil, r):
    from ajustes import MODO_PRUEBA
    if MODO_PRUEBA:
        return True
    return desbloqueada(perfil, r) and not materiales_faltantes(perfil, r)


def motivo_bloqueo(perfil, r):
    """Frase corta de por que no se puede cocinar, o None si se puede."""
    hf = habilidades_faltantes(perfil, r)
    if hf:
        if len(hf) == 1:
            return "Necesitas %s nivel %d" % (HABILIDADES[hf[0][0]]["nombre"], hf[0][1])
        return "Necesitas más práctica en %d habilidades" % len(hf)
    mf = materiales_faltantes(perfil, r)
    if mf:
        nombres = [catalogo.nombre_item(m) for m in mf]
        return "Te falta: " + nombres[0] + (" y %d más" % (len(nombres) - 1) if len(nombres) > 1 else "")
    return None


def puntos_por_paso(r):
    """Puntos de un paso perfecto."""
    return 3 + 2 * r["estrellas"]


def puntos_bono(r):
    return 4 + 6 * r["estrellas"]


def puntos_maximos(r):
    return len(r["pasos"]) * puntos_por_paso(r) + puntos_bono(r)


def metas_receta(r):
    """Puntos para 1, 2 y 3 estrellas de resultado: 30%, 60% y 85% del maximo."""
    m = puntos_maximos(r)
    return (max(3, int(round(m * 0.30))), int(round(m * 0.60)), int(round(m * 0.85)))


def recomendada(perfil, nivel):
    """Id de la receta que se destaca para el `nivel` de juego (la de ese nivel si se puede cocinar; si no, la
    jugable mas cercana por debajo; si no hay, la primera desbloqueada)."""
    nivel = max(1, min(NIVELES, nivel))
    jug = [r for r in RECETAS if jugable(perfil, r)]
    if not jug:
        jug = [r for r in RECETAS if desbloqueada(perfil, r)] or RECETAS[:1]
    debajo = [r for r in jug if r["nivel"] <= nivel]
    r = max(debajo, key=lambda x: x["nivel"]) if debajo else min(jug, key=lambda x: x["nivel"])
    return r["id"]


# ----------------------------------------------------------------------------- validacion (para pruebas)
def validar():
    """Devuelve la lista de problemas de las recetas (vacia si todo esta bien)."""
    malos = []
    ids = set()
    if len(RECETAS) < 30:
        malos.append("hay %d recetas (se piden 30)" % len(RECETAS))
    usadas = set()
    for r in RECETAS:
        n = r["nivel"]
        if r["id"] in ids:
            malos.append("id repetido " + r["id"])
        ids.add(r["id"])
        esperado = PASOS_NIVEL.get(n)
        if esperado is not None and abs(len(r["pasos"]) - esperado) > 1:
            malos.append("%s (nivel %d): %d pasos, se esperaban ~%d" % (r["id"], n, len(r["pasos"]), esperado))
        if n >= 20 and len(r["pasos"]) < 15:
            malos.append("%s: nivel %d con menos de 15 pasos" % (r["id"], n))
        for m in r["mats"]:
            if m not in catalogo.ITEMS:
                malos.append("%s: material desconocido %s" % (r["id"], m))
        for i, s in enumerate(r["pasos"]):
            if s.get("h") not in HABILIDADES:
                malos.append("%s paso %d: habilidad desconocida %s" % (r["id"], i, s.get("h")))
                continue
            usadas.add(s["h"])
            for clave in ("ing", "sobre"):
                v = s.get(clave)
                if v and v not in catalogo.ITEMS and v not in PSEUDO and v not in CASA:
                    malos.append("%s paso %d: %s '%s' no es un objeto ni un ingrediente conocido" % (r["id"], i, clave, v))
            for v in s.get("ings", ()):
                if v not in catalogo.ITEMS and v not in PSEUDO and v not in CASA:
                    malos.append("%s paso %d: ings '%s' desconocido" % (r["id"], i, v))
        if not r["basica"]:
            for s in r["pasos"]:
                v = s.get("ing")
                if v and v in catalogo.ITEMS and v not in r["mats"] and v not in CASA:
                    malos.append("%s: el paso usa %s pero no esta en los materiales" % (r["id"], v))
    faltan = [h for h in HABILIDADES if h not in usadas]
    if faltan:
        malos.append("habilidades que ninguna receta usa: " + ", ".join(faltan))
    return malos
