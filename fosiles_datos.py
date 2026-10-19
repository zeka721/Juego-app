"""Reglas y datos de Fosiles: mundos, dinosaurios, grados, zonas de excavacion, herramientas.

Solo logica (sin dibujo). Todo el estado se guarda en `perfil.extra["fosiles"]` (JSON) salvo
`perfil.polvo` (gemas para revivir), `perfil.dinos` (revividos) e `perfil.inventario` (materiales).

Resumen del diseno
- 5 mundos x 6 dinosaurios. El dinosaurio de la posicion 0..5 de cada mundo necesita 20, 36, 52, 68, 84 y 100 huesos.
- Cada zona de excavacion esconde como maximo 3 huesos (y gemas de polvo especial). Aparece sola entre 1 y 5 minutos
  (tiempo real) despues de terminar la anterior, y no se acumulan. Si no terminas una zona, se queda: al volver se excava
  de nuevo con capas nuevas pero solo lo que faltaba.
- Las gemas se reparten por dinosaurio de forma aleatoria pero garantizada: al encontrar el ultimo hueso de un dinosaurio
  ya se han entregado exactamente las gemas que cuesta revivirlo. Asi el total siempre cuadra.
- 20 grados de dificultad. Se desbloquean con la pericia (experiencia) que se gana al terminar zonas.
- Herramientas (brocha, martillo, cincel, cincel pequeno) de 1 a 5 estrellas, que se craftean con materiales y se gastan.
"""

import math
import random
import time

import catalogo

# ---------------------------------------------------------------- mundos y dinosaurios
# Cada mundo: 6 dinosaurios de menor a mayor (el sexto es el mas grande).
MUNDOS = [
    dict(id="depredadores", nombre="Mundo de los Depredadores", color=(200, 80, 60),
         dinos=["velociraptor", "alosaurio", "carnotauro", "espinosaurio", "giganotosaurio", "tiranosaurio"]),
    dict(id="mares", nombre="Mundo de los Mares", color=(60, 140, 210),
         dinos=["ictiosaurio", "dunkleosteus", "plesiosaurio", "liopleurodon", "mosasaurio", "megalodon"]),
    dict(id="cielos", nombre="Mundo de los Cielos", color=(120, 180, 240),
         dinos=["arqueopterix", "dimorfodonte", "ranforinco", "tapejara", "pteranodon", "quetzalcoatlus"]),
    dict(id="herbivoros", nombre="Mundo de los Herbívoros", color=(90, 170, 90),
         dinos=["parasaurolofo", "anquilosaurio", "estegosaurio", "triceratops", "diplodoco", "braquiosaurio"]),
    dict(id="hielo", nombre="Mundo de la Era de Hielo", color=(150, 200, 230),
         dinos=["smilodon", "gliptodonte", "megaloceros", "rinoceronte_lanudo", "megaterio", "mamut"]),
]
ORDEN_DINOS = [d for m in MUNDOS for d in m["dinos"]]
HUESOS_POS = [20, 36, 52, 68, 84, 100]      # huesos del dinosaurio segun su posicion en el mundo
GEMAS_POS = [4, 6, 8, 10, 12, 14]           # gemas (polvo especial) para revivirlo
MAX_HUESOS_ZONA = 4                          # maximo de huesos por zona
PESOS_HUESOS_ZONA = {1: 15, 2: 35, 3: 30, 4: 20}   # probabilidad (%) de 1, 2, 3 o 4 huesos
PESOS_HUESOS_ZONA = {k: w for k, w in PESOS_HUESOS_ZONA.items() if k <= MAX_HUESOS_ZONA}
PROMEDIO_HUESOS_ZONA = sum(k * w for k, w in PESOS_HUESOS_ZONA.items()) / sum(PESOS_HUESOS_ZONA.values())
ESPERA_MIN, ESPERA_MAX = 60.0, 300.0        # segundos reales entre zonas (1 a 5 minutos)


def mundo_de(dino):
    for i, m in enumerate(MUNDOS):
        if dino in m["dinos"]:
            return i
    raise KeyError(dino)


def posicion(dino):
    return MUNDOS[mundo_de(dino)]["dinos"].index(dino)


def huesos_total(dino):
    return HUESOS_POS[posicion(dino)]


def costo_revivir(dino):
    return GEMAS_POS[posicion(dino)]


# ---------------------------------------------------------------- reliquias (coleccion del cuaderno)
# id: (mundo, rareza 1..3). Los nombres y dibujos estan en arte_paleo.
RELIQUIAS = {
    # depredadores
    "diente_gigante": (0, 1), "garra_curva": (0, 1), "huella_tres_dedos": (0, 1),
    "huevo_fosil": (0, 2), "escama_dura": (0, 2), "colmillo_afilado": (0, 3),
    # mares
    "amonita": (1, 1), "trilobite": (1, 1), "concha_espiral": (1, 1),
    "diente_megalodon": (1, 2), "aleta_fosil": (1, 2), "perla_antigua": (1, 3),
    # cielos
    "pluma_fosil": (2, 1), "helecho_fosil": (2, 1), "hueso_hueco": (2, 1),
    "ala_membrana": (2, 2), "nido_antiguo": (2, 2), "ambar_insecto": (2, 3),
    # herbivoros
    "hoja_gigante": (3, 1), "diente_plano": (3, 1), "semilla_antigua": (3, 1),
    "cuerno_roto": (3, 2), "tronco_petrificado": (3, 2), "piedra_pulida": (3, 3),
    # hielo
    "colmillo_mamut": (4, 1), "mechon_lana": (4, 1), "cristal_hielo": (4, 1),
    "punta_de_piedra": (4, 2), "hueso_tallado": (4, 2), "ambar_gota": (4, 3),
}
ORDEN_RELIQUIAS = sorted(RELIQUIAS, key=lambda r: (RELIQUIAS[r][0], RELIQUIAS[r][1], r))

# ---------------------------------------------------------------- grados de dificultad (1..20)
GRADOS_MAX = 20
TIEMPO_BASE = 120.0
TIEMPO_POR_GRADO = 10.0
XP_POR_NIVEL = 40                            # pericia necesaria por cada grado nuevo

# capa -> herramientas que sirven para romperla (la primera es la ideal)
HERRAMIENTAS_CAPA = {
    "polvo": ("brocha",),
    "barro": ("cincel_pequeno",),
    "rocas": ("martillo", "cincel"),
    "cristales": ("cincel", "martillo"),
}


def tiempo_grado(g):
    """45 s en el grado 1 y 5 s mas por cada grado."""
    return TIEMPO_BASE + TIEMPO_POR_GRADO * (max(1, min(GRADOS_MAX, g)) - 1)


def capas_grado(g):
    """Capas que cubren la zona en ese grado.
    1-4 solo polvo; 5-9 polvo y barro; 10-14 polvo, barro y rocas; 15-20 ademas cristales."""
    if g < 5:
        return ("polvo",)
    if g < 10:
        return ("polvo", "barro")
    if g < 15:
        return ("polvo", "barro", "rocas")
    return ("polvo", "barro", "rocas", "cristales")


def estrellas_requeridas(g, capa):
    """Estrellas minimas de la herramienta para trabajar esa capa en ese grado."""
    if capa == "polvo":
        return 1
    if capa == "barro":
        return 1 if g < 7 else 2
    if capa == "rocas":
        return 2 if g < 13 else 3
    if capa == "cristales":
        return 3 if g <= 17 else (4 if g <= 19 else 5)
    return 1


def sensibilidad_grado(g):
    """Factor de la velocidad maxima permitida cerca de un hueso (menor = mas estricto).
    El grado 1 vale 1.0 y equivale a la sensibilidad que antes tenia el 'nivel 4' de Fosiles.
    Los umbrales de velocidad y de golpe de la excavacion se multiplican por este factor."""
    return 1.0 - 0.03 * (max(1, min(GRADOS_MAX, g)) - 1)


def xp_zona(g, huesos, limpio=True):
    """Pericia que da terminar una zona."""
    return int(round((8 + 2 * g) * (0.5 + 0.25 * huesos) * (1.0 if limpio else 0.8)))


def nivel_pericia(xp):
    return max(1, min(GRADOS_MAX, 1 + int(xp // XP_POR_NIVEL)))


# ---------------------------------------------------------------- herramientas
TIPOS_HERR = ("brocha", "martillo", "cincel", "cincel_pequeno")
NOMBRES_HERR = {"brocha": "Brocha", "martillo": "Martillo", "cincel": "Cincel",
                "cincel_pequeno": "Cincel pequeño"}
MAX_ESTRELLAS = 5
# puntos de durabilidad por estrella: la excavacion los gasta (un hueso agrietado, un golpe, cada segundo de pincel...).
# Pensado para que 1 estrella alcance ~1-2 zonas y 5 estrellas ~15.
DURABILIDAD = {1: 100, 2: 180, 3: 320, 4: 560, 5: 900}

# materiales de crafteo: id -> (nombre, color, precio en monedas)
MATERIALES = {
    "madera": ("Madera", (170, 120, 70), 6),
    "cerda": ("Cerdas", (225, 205, 160), 6),
    "hierro": ("Hierro", (150, 155, 165), 14),
    "acero": ("Acero", (110, 130, 170), 30),
    "cuarzo": ("Cuarzo", (200, 230, 245), 60),
}
# materiales que ademas se pueden hallar excavando, segun el grado minimo
DROPS_MATERIAL = {"madera": 1, "cerda": 1, "hierro": 3, "acero": 8, "cuarzo": 12}
# materiales que NO se compran: solo se consiguen excavando (en el cofre al terminar una zona)
NO_SE_VENDEN = ("acero", "cuarzo")


def se_vende(ident):
    return ident in MATERIALES and ident not in NO_SE_VENDEN

_BASE = {
    "brocha": {"madera": 1, "cerda": 2},
    "martillo": {"madera": 1, "hierro": 1},
    "cincel": {"hierro": 1, "madera": 1},
    "cincel_pequeno": {"hierro": 1, "madera": 1},
}
_POR_ESTRELLA = {
    1: {},
    2: {"hierro": 1},
    3: {"hierro": 2, "acero": 1},
    4: {"acero": 2, "cuarzo": 1},
    5: {"acero": 3, "cuarzo": 2, "gema_fosil": 1},
}


def receta_herramienta(tipo, est):
    """Materiales {id: cantidad} para craftear la herramienta (1 estrella = lo mas simple y barato)."""
    r = dict(_BASE[tipo])
    for k, v in _POR_ESTRELLA[est].items():
        r[k] = r.get(k, 0) + v
    return r


def segundos_crafteo(est):
    """Tiempo (interactivo) del crafteo: 3 s para 1 estrella, 13 s para 5."""
    return 3.0 + 2.5 * (est - 1)


for _id, (_nombre, _color, _precio) in MATERIALES.items():
    catalogo.registrar_item(_id, _nombre, "material", _color, "bolsa" if _id in ("cerda", "cuarzo") else "gema",
                            _precio, "Material para craftear herramientas de excavación.")
if ("material", "Materiales") not in catalogo.CATEGORIAS:
    catalogo.CATEGORIAS.append(("material", "Materiales"))


# ---------------------------------------------------------------- estado guardado
def estado(perfil):
    """Diccionario de estado (se crea con valores iniciales la primera vez)."""
    e = perfil.extra.get("fosiles")
    if not isinstance(e, dict) or e.get("version") != 2:
        e = {
            "version": 2,
            "huesos": {},            # dino -> [indices hallados]
            "xp": 0,
            "zona": None,            # zona de excavacion lista (ver generar_zona)
            "proxima": time.time(),  # cuando aparece la siguiente zona (la primera, enseguida)
            "gemas_dadas": {},       # dino -> gemas ya repartidas en zonas
            "mundo": 0,              # mundo donde se busca (el siguiente fosil sale de aqui)
            "herr": [],              # herramientas crafteadas
            "equipada": {},          # tipo -> id de la herramienta elegida
            "sig_id": 1,
            "reliquias": {},         # id -> cantidad
            "grado": 1,              # ultimo grado elegido
            "zonas_hechas": 0,
        }
        perfil.extra["fosiles"] = e
        for t in TIPOS_HERR:         # equipo inicial gratis: una herramienta de 1 estrella de cada tipo
            _nueva_herramienta(e, t, 1)
    return e


def _nueva_herramienta(e, tipo, est):
    h = {"id": e["sig_id"], "tipo": tipo, "est": est, "dur": DURABILIDAD[est]}
    e["sig_id"] += 1
    e["herr"].append(h)
    return h


# ---------------------------------------------------------------- progreso de dinosaurios y mundos
def huesos_de(perfil, dino):
    return list(estado(perfil)["huesos"].get(dino, []))


def progreso(perfil, dino):
    """(huesos hallados, huesos totales)."""
    return len(estado(perfil)["huesos"].get(dino, [])), huesos_total(dino)


def completo(perfil, dino):
    h, t = progreso(perfil, dino)
    return h >= t


def revivido(perfil, dino):
    return dino in perfil.dinos


def mundo_desbloqueado(perfil, i):
    """El mundo 0 esta abierto; cada mundo siguiente se abre al revivir los 6 dinosaurios del anterior (la llave)."""
    return i == 0 or all(d in perfil.dinos for d in MUNDOS[i - 1]["dinos"])


def tiene_llave(perfil, i):
    """True si ya revivieron los 6 dinosaurios del mundo i (llave para el siguiente)."""
    return all(d in perfil.dinos for d in MUNDOS[i]["dinos"])


def mundos_abiertos(perfil):
    return [i for i in range(len(MUNDOS)) if mundo_desbloqueado(perfil, i)]


def elegir_mundo(perfil, i):
    if mundo_desbloqueado(perfil, i):
        estado(perfil)["mundo"] = i


def siguiente_dino(perfil, mundo=None):
    """Dinosaurio al que pertenecen las proximas zonas: el primero sin completar del mundo activo
    (o de otro mundo abierto si ese ya esta completo). None si no queda ninguno."""
    e = estado(perfil)
    orden = [e["mundo"] if mundo is None else mundo] + [i for i in mundos_abiertos(perfil)]
    for i in orden:
        if not mundo_desbloqueado(perfil, i):
            continue
        for d in MUNDOS[i]["dinos"]:
            if not completo(perfil, d):
                return d
    return None


# ---------------------------------------------------------------- pericia y grados
def pericia(perfil):
    return estado(perfil)["xp"]


def grado_max(perfil):
    return nivel_pericia(estado(perfil)["xp"])


def sumar_pericia(perfil, xp):
    """Suma pericia. Devuelve el grado nuevo si se desbloqueo uno, o None."""
    e = estado(perfil)
    antes = nivel_pericia(e["xp"])
    e["xp"] += int(xp)
    despues = nivel_pericia(e["xp"])
    return despues if despues > antes else None


def xp_para_siguiente(perfil):
    """(xp actual en este grado, xp que pide cada grado)."""
    xp = estado(perfil)["xp"]
    return xp - (nivel_pericia(xp) - 1) * XP_POR_NIVEL, XP_POR_NIVEL


# ---------------------------------------------------------------- zonas de excavacion
def _espera():
    return random.uniform(ESPERA_MIN, ESPERA_MAX)


def generar_zona(perfil):
    """Crea la zona siguiente: hasta 3 huesos del dinosaurio en turno y las gemas que le tocan."""
    e = estado(perfil)
    dino = siguiente_dino(perfil)
    if dino is None:
        return None
    total = huesos_total(dino)
    hallados = set(e["huesos"].get(dino, []))
    faltan = [k for k in range(total) if k not in hallados]
    n = random.choices(list(PESOS_HUESOS_ZONA), weights=list(PESOS_HUESOS_ZONA.values()))[0]
    n = min(n, len(faltan), MAX_HUESOS_ZONA)
    elegidos = sorted(random.sample(faltan, n))
    restan_tras = len(faltan) - n
    costo = costo_revivir(dino)
    dadas = e["gemas_dadas"].get(dino, 0)
    necesarias = max(0, costo - dadas)
    if restan_tras == 0:
        gemas = necesarias                        # ultima zona del dinosaurio: se entrega todo lo que falte
    else:
        zonas_est = math.ceil(restan_tras / PROMEDIO_HUESOS_ZONA) + 1
        p = necesarias / zonas_est
        gemas = int(p) + (1 if random.random() < p - int(p) else 0)
        gemas = min(gemas, necesarias, 3)
    e["gemas_dadas"][dino] = dadas + gemas
    zona = {"dino": dino, "mundo": mundo_de(dino), "faltan": elegidos, "gemas": gemas, "reliquia": None,
            "intentos": 0, "n": n}
    e["zona"] = zona
    return zona


def tick(perfil, ahora=None):
    """Llamar a menudo (menu, expedicion): crea la zona cuando se cumple la espera. Devuelve la zona o None."""
    e = estado(perfil)
    ahora = time.time() if ahora is None else ahora
    if e["zona"] is None and ahora >= e["proxima"]:
        generar_zona(perfil)
    return e["zona"]


def zona_lista(perfil, ahora=None):
    """True si hay una zona de excavacion lista (es lo que muestra el carrito)."""
    return tick(perfil, ahora) is not None


def segundos_para_zona(perfil, ahora=None):
    """Segundos que faltan para la proxima zona (0 si ya hay una lista; None si no quedan fosiles)."""
    e = estado(perfil)
    ahora = time.time() if ahora is None else ahora
    if e["zona"] is not None:
        return 0.0
    if siguiente_dino(perfil) is None:
        return None
    return max(0.0, e["proxima"] - ahora)


def sorteo_reliquia(perfil, grado):
    """Al empezar a excavar una zona: devuelve una reliquia escondida (id) o None. Se guarda en la zona
    para que reiniciar la zona no cambie el resultado."""
    e = estado(perfil)
    z = e["zona"]
    if z is None:
        return None
    if z.get("reliquia") == "":
        return None
    if z.get("reliquia"):
        return z["reliquia"]
    if random.random() < min(0.45, 0.10 + 0.02 * grado):
        mundo = z["mundo"]
        ids = [r for r, (m, ra) in RELIQUIAS.items() if m == mundo]
        pesos = [4 - RELIQUIAS[r][1] for r in ids]     # las raras salen menos
        z["reliquia"] = random.choices(ids, weights=pesos)[0]
    else:
        z["reliquia"] = ""
    return z["reliquia"] or None


def registrar_hueso(perfil, dino, idx):
    """Guarda un hueso hallado en la zona. Devuelve True si era un hueso nuevo."""
    e = estado(perfil)
    lista = e["huesos"].setdefault(dino, [])
    nuevo = idx not in lista
    if nuevo:
        lista.append(idx)
        lista.sort()
    z = e["zona"]
    if z is not None and z["dino"] == dino and idx in z["faltan"]:
        z["faltan"].remove(idx)
    return nuevo


def registrar_gema(perfil):
    """Una gema de polvo especial hallada en la zona."""
    e = estado(perfil)
    z = e["zona"]
    if z is not None and z["gemas"] > 0:
        z["gemas"] -= 1
        perfil.polvo += 1
        return True
    return False


def registrar_reliquia(perfil, ident):
    """Guarda la reliquia hallada. Devuelve True si es la primera de ese tipo."""
    e = estado(perfil)
    z = e["zona"]
    if z is not None and z.get("reliquia") == ident:
        z["reliquia"] = ""                              # ya encontrada: no vuelve a salir al reiniciar
    nueva = ident not in e["reliquias"]
    e["reliquias"][ident] = e["reliquias"].get(ident, 0) + 1
    return nueva


def zona_pendiente(perfil):
    """Lo que falta por encontrar en la zona actual: (huesos, gemas, hay reliquia sin hallar) o None."""
    z = estado(perfil)["zona"]
    if z is None:
        return None
    return len(z["faltan"]), z["gemas"], bool(z.get("reliquia"))


def cerrar_zona_si_termino(perfil, grado, limpio=True):
    """Si la zona ya no tiene huesos ni gemas pendientes la cierra: da pericia y programa la siguiente
    (entre 1 y 5 minutos). Devuelve un dict con el resultado o None si sigue pendiente."""
    e = estado(perfil)
    z = e["zona"]
    if z is None or z["faltan"] or z["gemas"] > 0:
        return None
    xp = xp_zona(grado, max(1, z.get("n", 1)), limpio)
    desbloqueo = sumar_pericia(perfil, xp)
    e["zonas_hechas"] += 1
    e["zona"] = None
    e["proxima"] = time.time() + _espera()
    return {"xp": xp, "grado_nuevo": desbloqueo, "dino": z["dino"]}


def reiniciar_zona(perfil):
    """Se acabo el tiempo sin terminar: la zona se mantiene con lo que falta (capas nuevas)."""
    z = estado(perfil)["zona"]
    if z is not None:
        z["intentos"] += 1


# ---------------------------------------------------------------- revivir
def dino_para_revivir(perfil):
    """Primer dinosaurio con esqueleto completo, sin revivir y con gemas suficientes. None si no hay."""
    for d in ORDEN_DINOS:
        if completo(perfil, d) and d not in perfil.dinos and perfil.polvo >= costo_revivir(d):
            return d
    return None


def dino_completo_sin_gemas(perfil):
    """Primer esqueleto completo al que aun le faltan gemas: (dino, gemas que faltan) o None."""
    for d in ORDEN_DINOS:
        if completo(perfil, d) and d not in perfil.dinos and perfil.polvo < costo_revivir(d):
            return d, costo_revivir(d) - perfil.polvo
    return None


def gastar_polvo_revivir(perfil, dino):
    """Gasta las gemas para revivir. Devuelve True si pudo (el dino lo anade la pantalla de resultados)."""
    c = costo_revivir(dino)
    if perfil.polvo >= c:
        perfil.polvo -= c
        return True
    return False


# ---------------------------------------------------------------- herramientas: uso y crafteo
def herramientas(perfil, tipo=None):
    hs = estado(perfil)["herr"]
    return [h for h in hs if tipo is None or h["tipo"] == tipo]


def herramienta_activa(perfil, tipo):
    """La herramienta equipada de ese tipo; si no hay o se rompio, la de mas estrellas que quede. None si no hay."""
    e = estado(perfil)
    hs = [h for h in e["herr"] if h["tipo"] == tipo and h["dur"] > 0]
    if not hs:
        return None
    ide = e["equipada"].get(tipo)
    for h in hs:
        if h["id"] == ide:
            return h
    return max(hs, key=lambda h: (h["est"], h["dur"]))


def equipar(perfil, herr_id):
    e = estado(perfil)
    for h in e["herr"]:
        if h["id"] == herr_id and h["dur"] > 0:
            e["equipada"][h["tipo"]] = herr_id
            return True
    return False


def gastar_durabilidad(perfil, herr, puntos):
    """Gasta durabilidad de una herramienta. Si llega a 0 se rompe y desaparece. Devuelve True si se rompio."""
    herr["dur"] = max(0, herr["dur"] - puntos)
    if herr["dur"] <= 0:
        e = estado(perfil)
        e["herr"] = [h for h in e["herr"] if h["id"] != herr["id"]]
        if e["equipada"].get(herr["tipo"]) == herr["id"]:
            e["equipada"].pop(herr["tipo"], None)
        return True
    return False


def puede_craftear(perfil, tipo, est):
    return all(perfil.cantidad(k) >= v for k, v in receta_herramienta(tipo, est).items())


def craftear(perfil, tipo, est):
    """Gasta los materiales y crea la herramienta. Devuelve la herramienta o None si faltan materiales."""
    r = receta_herramienta(tipo, est)
    if not all(perfil.cantidad(k) >= v for k, v in r.items()):
        return None
    for k, v in r.items():
        perfil.quitar(k, v)
    return _nueva_herramienta(estado(perfil), tipo, est)


def comprar_material(perfil, ident, n=1):
    if not se_vende(ident):
        return False
    """Compra materiales con monedas. Devuelve True si pudo."""
    precio = MATERIALES[ident][2] * n
    if perfil.gastar(precio):
        perfil.dar(ident, n)
        return True
    return False


def sorteo_materiales(grado):
    """Materiales del cofre al terminar una zona: lista de (id, cantidad). Nunca viene vacio."""
    out = []
    posibles = [mid for mid, gmin in DROPS_MATERIAL.items() if grado >= gmin]
    for mid in posibles:
        if random.random() < (0.42 if mid in NO_SE_VENDEN else 0.35):
            out.append((mid, 1 + (1 if random.random() < 0.3 else 0)))
    if not out and posibles:
        mid = random.choice(posibles)
        out.append((mid, 1 + (1 if grado >= 8 else 0)))
    return out


def resumen(perfil):
    """Datos sueltos para pantallas: dict con grado maximo, zona lista, segundos de espera, mundo activo."""
    e = estado(perfil)
    return {
        "grado_max": grado_max(perfil), "zona": e["zona"], "lista": zona_lista(perfil),
        "espera": segundos_para_zona(perfil), "mundo": e["mundo"], "dino": siguiente_dino(perfil),
        "xp": e["xp"], "reliquias": len(e["reliquias"]),
    }
