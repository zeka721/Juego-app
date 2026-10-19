"""Reglas y datos de la Pesca por mundos (como Fosiles): mundos, peces objetivo, herramientas con estrellas.

Solo logica (sin dibujo). Todo el estado vive en `perfil.extra["pesca"]` (JSON); los materiales son items
normales del inventario (`perfil.inventario`), registrados en `catalogo` (categoria "pesca") al importar.

Resumen del diseno
- 5 mundos con 6 peces objetivo cada uno (mas peces de fondo de grado parecido). Los indices de mundo son 0..4.
- Cada especie capturada queda registrada (con cuantas veces). El mundo siguiente se abre al registrar los 6
  peces objetivo del anterior (la llave) y se queda abierto para siempre.
- Herramientas cana / cuerda / anzuelo de 1 a 5 estrellas: se craftean con materiales, se desgastan en cada
  forcejeo y se rompen (hay que volver a craftear). El carrete y el barco ya no son piezas: el alcance, la
  profundidad y la estabilidad de la linea dependen del mundo.
- Regla de estrellas: el mundo i (0..4) pide cana, cuerda y anzuelo de al menos i+1 estrellas
  (mundo 1 = 1 estrella ... mundo 5 = 5 estrellas). Se puede pescar en un mundo mas bajo con equipo menor.
- Las especies nuevas (carpa, orca, kraken...) las agrega el arte; si faltan en `arte.PECES` se ignoran
  (la llave solo pide las que existen).
"""

import random

import arte
import catalogo

# ---------------------------------------------------------------- mundos
# objetivo: 6 ids (arte.PECES). fondo: ids de relleno de grado parecido. Los ids que aun no existan se filtran.
MUNDOS = [
    dict(id="normal", nombre="Mundo Normal", color=(90, 190, 120), grado_min=1, grado_max=2, estrellas_req=1,
         objetivo=["sardina", "perca", "trucha", "carpa", "bagre", "esturion"],
         fondo=["payaso", "caballito", "dorado"],
         aspera=0.15, alcance=520, prof=240, barco=1, fuerza=1.0),
    dict(id="submarino", nombre="Mundo Submarino", color=(70, 160, 225), grado_min=2, grado_max=3, estrellas_req=2,
         objetivo=["payaso", "globo", "caballito", "pezangel", "mantarraya", "tortuga"],
         fondo=["dorado", "pezluna", "trucha", "sardina", "medusa"],
         aspera=0.30, alcance=650, prof=275, barco=2, fuerza=0.8),
    dict(id="polar", nombre="Mundo Polar", color=(160, 210, 240), grado_min=3, grado_max=4, estrellas_req=3,
         objetivo=["atun", "bacalao", "beluga", "narval", "cachalote", "orca"],
         fondo=["pezluna", "pezespada", "pulpo", "dorado", "mantarraya", "ballena"],
         aspera=0.50, alcance=780, prof=310, barco=3, fuerza=0.8),
    dict(id="subnautica", nombre="Mundo Subnáutica", color=(120, 90, 210), grado_min=4, grado_max=5, estrellas_req=4,
         objetivo=["pezlinterna", "pezvibora", "pezhacha", "pezpescador", "anguila", "pulpogigante"],
         fondo=["pulpo", "pezespada", "mantarraya", "pezluna", "tiburon", "medusa"],
         aspera=0.65, alcance=910, prof=345, barco=4, fuerza=0.8),
    dict(id="legendario", nombre="Mundo Legendario", color=(230, 190, 70), grado_min=5, grado_max=5, estrellas_req=5,
         objetivo=["celacanto", "megalodon", "serpiente", "dragonmar", "kraken", "leviatan"],
         fondo=["anguila", "pulpogigante", "tiburon", "ballena", "pezespada", "pezpescador"],
         aspera=0.80, alcance=1040, prof=380, barco=4, fuerza=0.62),
]
NUM_MUNDOS = len(MUNDOS)
ORDEN_OBJETIVOS = [s for m in MUNDOS for s in m["objetivo"]]

# ---------------------------------------------------------------- ajustes del juego
DURACION_BASE = 120.0           # s de partida en el mundo 1 (se suma POR_MUNDO por cada mundo)
DURACION_POR_MUNDO = 10.0
FORCEJEO_BASE = 20.0            # s que dura el forcejeo de un buen jugador: base + por grado + por mundo
FORCEJEO_POR_GRADO = 2.0
FORCEJEO_POR_MUNDO = 1.5
PESO_OBJETIVO = 3.0             # un objetivo sin registrar sale 3 veces mas
PESO_OBJETIVO_REG = 1.0
PESO_FONDO = 0.8
BONO_EVENTO = 40                # puntos extra por un animal de evento
BONO_NUEVO = 10                 # puntos extra por registrar una especie nueva
MAX_ESTRELLAS = 5
TIPOS_HERR = ("cana", "cuerda", "anzuelo")
NOMBRES_HERR = {"cana": "Caña", "cuerda": "Cuerda", "anzuelo": "Anzuelo"}
EFECTO_HERR = {"cana": "fuerza al enrollar", "cuerda": "aguanta la tensión", "anzuelo": "se clava y no suelta"}
# durabilidad por estrella (1 estrella ~3 forcejeos, 5 estrellas ~35)
DURABILIDAD = {1: 90, 2: 180, 3: 330, 4: 600, 5: 1000}

# ---------------------------------------------------------------- materiales
# id: (nombre, color, forma de catalogo.dibujar_item, precio de compra (0 = no se vende), descripcion)
MATERIALES = {
    "bambu": ("Bambú", (190, 200, 110), "alargado", 6, "Para la caña."),
    "hilo": ("Hilo de pesca", (235, 235, 245), "ovillo", 6, "Para la cuerda y las cañas."),
    "alambre": ("Alambre", (160, 165, 185), "frasco", 8, "Para los anzuelos."),
    "escama": ("Escama plateada", (185, 215, 235), "gota", 0, "La sueltan los peces al pescarlos."),
    "perla": ("Perla marina", (250, 235, 245), "huevo", 0, "Brilla en el mar."),
    "marfil": ("Marfil marino", (245, 235, 200), "alargado", 0, "Colmillos de animales de hielo."),
    "luz_abisal": ("Luz abisal", (120, 240, 230), "gema", 0, "Brillo de los peces de las profundidades."),
    "escama_dragon": ("Escama de dragón", (230, 190, 70), "gema", 0, "Muy rara. Se puede vender."),
}
# materiales que ya existen en el catalogo y tambien se usan (alga se compra en la tienda)
EXTRA_MATERIALES = ("alga",)
SE_COMPRAN = ("bambu", "hilo", "alambre", "alga")
PRECIO_ALGA = 5
for _id, (_n, _c, _forma, _precio, _desc) in MATERIALES.items():
    catalogo.registrar_item(_id, _n, "pesca", _c, _forma, _precio if _id in SE_COMPRAN else 0, _desc)

# materiales que salen al capturar, por mundo: (id, probabilidad)
DROPS = [
    [("escama", 0.55), ("alga", 0.30)],
    [("escama", 0.50), ("perla", 0.30), ("alga", 0.25)],
    [("escama", 0.40), ("perla", 0.30), ("marfil", 0.35)],
    [("perla", 0.30), ("marfil", 0.30), ("luz_abisal", 0.40)],
    [("luz_abisal", 0.35), ("marfil", 0.30), ("escama_dragon", 0.45), ("perla", 0.25)],
]

_BASE = {
    "cana": {"bambu": 2, "hilo": 1},
    "cuerda": {"hilo": 3},
    "anzuelo": {"alambre": 3},
}
_POR_ESTRELLA = {
    1: {},
    2: {"escama": 2},
    3: {"escama": 3, "perla": 1},
    4: {"perla": 2, "marfil": 2},
    5: {"marfil": 2, "luz_abisal": 3, "perla": 2},
}


def se_vende(ident):
    return ident in SE_COMPRAN


def precio(ident):
    if ident in MATERIALES:
        return MATERIALES[ident][3]
    return PRECIO_ALGA if ident == "alga" else 0


def receta_herramienta(tipo, est):
    """Materiales {id: cantidad} para craftear la herramienta (1 estrella = lo mas simple y barato)."""
    r = dict(_BASE[tipo])
    for k, v in _POR_ESTRELLA[est].items():
        r[k] = r.get(k, 0) + v
    return r


def segundos_crafteo(est):
    """Tiempo (interactivo) del crafteo: 3 s para 1 estrella, 13 s para 5."""
    return 3.0 + 2.5 * (est - 1)


# ---------------------------------------------------------------- estado guardado
def estado(perfil):
    """Diccionario de estado (se crea con valores iniciales la primera vez)."""
    e = perfil.extra.get("pesca")
    if not isinstance(e, dict) or e.get("version") != 1:
        e = {
            "version": 1,
            "capturas": {},          # especie -> veces capturada (el registro)
            "abiertos": [0],         # mundos abiertos (una vez abierto, siempre abierto)
            "mundo": 0,              # mundo elegido
            "herr": [],              # herramientas crafteadas
            "equipada": {},          # tipo -> id de la herramienta elegida
            "sig_id": 1,
            "lanzamientos": 0,
        }
        perfil.extra["pesca"] = e
        for t in TIPOS_HERR:         # equipo inicial gratis: una herramienta de 1 estrella de cada tipo
            _nueva_herramienta(e, t, 1)
    return e


def _nueva_herramienta(e, tipo, est):
    h = {"id": e["sig_id"], "tipo": tipo, "est": est, "dur": DURABILIDAD[est]}
    e["sig_id"] += 1
    e["herr"].append(h)
    return h


# ---------------------------------------------------------------- peces, registro y mundos
def objetivos(i):
    """Los peces objetivo del mundo i que existen en arte.PECES (los 6 cuando el arte esta completo)."""
    return [s for s in MUNDOS[i]["objetivo"] if s in arte.PECES]


def fondo(i):
    return [s for s in MUNDOS[i]["fondo"] if s in arte.PECES and s not in MUNDOS[i]["objetivo"]]


def mundo_de(sp):
    """Mundo donde es objetivo la especie (None si es solo de fondo)."""
    for i, m in enumerate(MUNDOS):
        if sp in m["objetivo"]:
            return i
    return None


def veces(perfil, sp):
    return int(estado(perfil)["capturas"].get(sp, 0))


def registrado(perfil, sp):
    return veces(perfil, sp) > 0


def especies_registradas(perfil):
    return [s for s in arte.PECES if registrado(perfil, s)]


def progreso(perfil, i):
    """(objetivos registrados, objetivos del mundo) contando solo los que existen."""
    obj = objetivos(i)
    return sum(1 for s in obj if registrado(perfil, s)), len(obj)


def objetivos_pendientes(perfil, i):
    return [s for s in objetivos(i) if not registrado(perfil, s)]


def mundo_completo(perfil, i):
    obj = objetivos(i)
    return bool(obj) and all(registrado(perfil, s) for s in obj)


def tiene_llave(perfil, i):
    """True si ya registraron los peces objetivo del mundo i (la llave del mundo i+1)."""
    return mundo_completo(perfil, i)


def _sincronizar(perfil):
    """Anota los mundos cuya llave ya se tiene. Devuelve los recien abiertos."""
    e = estado(perfil)
    nuevos = []
    for i in range(1, NUM_MUNDOS):
        if i not in e["abiertos"] and tiene_llave(perfil, i - 1) and (i - 1) in e["abiertos"]:
            e["abiertos"].append(i)
            nuevos.append(i)
    e["abiertos"].sort()
    return nuevos


def mundo_abierto(perfil, i):
    _sincronizar(perfil)
    return 0 <= i < NUM_MUNDOS and i in estado(perfil)["abiertos"]


def mundos_abiertos(perfil):
    _sincronizar(perfil)
    return list(estado(perfil)["abiertos"])


def mundo_actual(perfil):
    """Mundo elegido (siempre abierto)."""
    e = estado(perfil)
    _sincronizar(perfil)
    if e["mundo"] not in e["abiertos"]:
        e["mundo"] = 0
    return e["mundo"]


def elegir_mundo(perfil, i):
    """Elige el mundo donde se pesca. Devuelve True si estaba abierto."""
    if mundo_abierto(perfil, i):
        estado(perfil)["mundo"] = i
        return True
    return False


def registrar_captura(perfil, sp):
    """Registra la captura. Devuelve la lista de eventos: ("nuevo", sp) si era una especie nueva,
    ("completo", i) si con ella se tienen los objetivos del mundo i, ("mundo", j) si se abrio el mundo j."""
    e = estado(perfil)
    ev = []
    nuevo = sp not in e["capturas"]
    e["capturas"][sp] = int(e["capturas"].get(sp, 0)) + 1
    if nuevo:
        ev.append(("nuevo", sp))
        i = mundo_de(sp)
        if i is not None and mundo_completo(perfil, i):
            ev.append(("completo", i))
    for j in _sincronizar(perfil):
        ev.append(("mundo", j))
    return ev


# ---------------------------------------------------------------- reglas de estrellas por mundo
def estrellas_requeridas(i, tipo=None):
    """Estrellas minimas de cana, cuerda y anzuelo para pescar en el mundo i (0..4): i + 1."""
    return int(MUNDOS[i]["estrellas_req"])


def estrellas_equipo(perfil):
    """{tipo: estrellas de la herramienta que se usaria}."""
    return {t: (herramienta_activa(perfil, t) or {"est": 0})["est"] for t in TIPOS_HERR}


def equipo_cumple(perfil, i):
    req = estrellas_requeridas(i)
    return all(v >= req for v in estrellas_equipo(perfil).values())


def faltan_estrellas(perfil, i):
    """{tipo: estrellas minimas} de lo que no alcanza para el mundo i (vacio si cumple)."""
    req = estrellas_requeridas(i)
    return {t: req for t, v in estrellas_equipo(perfil).items() if v < req}


def puede_pescar(perfil, i):
    """(ok, motivo): mundo abierto y equipo con estrellas suficientes. motivo = "" | "cerrado" | "equipo"."""
    if not mundo_abierto(perfil, i):
        return False, "cerrado"
    if not equipo_cumple(perfil, i):
        return False, "equipo"
    return True, ""


def mundo_jugable_max(perfil):
    """El mundo mas alto abierto en el que el equipo cumple (como minimo el 0)."""
    mejor = 0
    for i in mundos_abiertos(perfil):
        if equipo_cumple(perfil, i):
            mejor = max(mejor, i)
    return mejor


def mundo_para_jugar(perfil, pedido=None):
    """Mundo en el que se jugara: el pedido (o el actual) si se puede; si no, el mas alto que se pueda
    por debajo. Devuelve (mundo, limitado)."""
    i = mundo_actual(perfil) if pedido is None else max(0, min(NUM_MUNDOS - 1, int(pedido)))
    j = i
    while j > 0 and not puede_pescar(perfil, j)[0]:
        j -= 1
    return j, j < i


# ---------------------------------------------------------------- pool de peces de un mundo
def pool(perfil, i, evento=False):
    """(ids, pesos) de las especies de un mundo. evento=False: peces normales; True: animales de evento.
    Los objetivos sin registrar pesan mas; el fondo y los registrados, menos."""
    m = MUNDOS[i]
    ids, pesos = [], []
    obj = objetivos(i)
    for s in obj + fondo(i):
        d = arte.PECES[s]
        if bool(d[12]) != bool(evento):
            continue
        if s in obj:
            w = PESO_OBJETIVO_REG if registrado(perfil, s) else PESO_OBJETIVO
        else:
            w = PESO_FONDO
        if not (m["grado_min"] <= d[1] <= m["grado_max"]):
            w *= 0.6                      # grado fuera de la banda del mundo: sale menos
        ids.append(s)
        pesos.append(w)
    return ids, pesos


def hay_objetivo_evento_pendiente(perfil, i):
    """True si algun objetivo sin registrar de este mundo es un animal de evento (sale en un evento)."""
    return any(bool(arte.PECES[s][12]) for s in objetivos_pendientes(perfil, i))


# ---------------------------------------------------------------- herramientas: uso y crafteo
def herramientas(perfil, tipo=None):
    return [h for h in estado(perfil)["herr"] if tipo is None or h["tipo"] == tipo]


def asegurar_basicas(perfil):
    """Si se rompio la ultima herramienta de un tipo, regala una de 1 estrella (nunca se queda sin poder pescar)."""
    e = estado(perfil)
    for t in TIPOS_HERR:
        if not any(h["tipo"] == t and h["dur"] > 0 for h in e["herr"]):
            _nueva_herramienta(e, t, 1)


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
    """Gasta durabilidad. Si llega a 0 se rompe y desaparece. Devuelve True si se rompio."""
    herr["dur"] = max(0, herr["dur"] - puntos)
    if herr["dur"] <= 0:
        e = estado(perfil)
        e["herr"] = [h for h in e["herr"] if h["id"] != herr["id"]]
        if e["equipada"].get(herr["tipo"]) == herr["id"]:
            e["equipada"].pop(herr["tipo"], None)
        return True
    return False


def desgaste_forcejeo(grado, resultado, tension=0.0):
    """Puntos de durabilidad que gasta un forcejeo: {tipo: puntos}. resultado: "captura", "suelta" o "rota".
    Los peces de mas grado gastan mas; si la linea se rompe la cuerda sufre un golpe extra."""
    f = 1.0 if resultado == "captura" else 0.6
    gastos = {"cana": (8 + 4 * grado) * f,
              "cuerda": (6 + 3 * grado) * f + (18 if resultado == "rota" else 0),
              "anzuelo": (5 + 2.5 * grado) * f}
    return {t: max(1, int(round(v * (1.0 + 0.4 * max(0.0, min(1.0, tension)))))) for t, v in gastos.items()}


def aplicar_desgaste(perfil, grado, resultado, tension=0.0):
    """Gasta las herramientas activas tras un forcejeo. Devuelve la lista de herramientas rotas (dicts con tipo y est)."""
    rotas = []
    for t, pts in desgaste_forcejeo(grado, resultado, tension).items():
        h = herramienta_activa(perfil, t)
        if h is not None:
            est = h["est"]
            if gastar_durabilidad(perfil, h, pts):
                rotas.append({"tipo": t, "est": est})
    if rotas:
        asegurar_basicas(perfil)
    return rotas


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
    """Compra materiales basicos con monedas. Devuelve True si pudo."""
    if not se_vende(ident):
        return False
    if perfil.gastar(precio(ident) * n):
        perfil.dar(ident, n)
        return True
    return False


def sorteo_materiales(mundo, grado=1, evento=False):
    """Materiales que suelta una captura: lista de (id, cantidad). Nunca viene vacia."""
    out = []
    tabla = DROPS[max(0, min(NUM_MUNDOS - 1, mundo))]
    bono = 0.04 * max(0, grado - 1) + (0.15 if evento else 0.0)
    for mid, p in tabla:
        if random.random() < min(0.95, p + bono):
            out.append((mid, 1 + (1 if (grado >= 4 or evento) and random.random() < 0.4 else 0)))
    if not out:
        mid = random.choices([m for m, _ in tabla], weights=[p for _, p in tabla])[0]
        out.append((mid, 1))
    return out


# ---------------------------------------------------------------- parametros del equipo (reemplaza stats_equipo)
def parametros(perfil, mundo):
    """Efecto numerico del equipo activo y del mundo. Llaves: alcance, prof (px), C (tension que aguanta la
    cuerda), P (fuerza de enrollado), clavar, agarre, estab (0..1 agitacion de la linea), barco (1..4, dibujo),
    cana/cuerda/anzuelo (estrellas), fuerza (factor de la fuerza de los peces en este mundo; los peces de
    los mundos altos tiran menos de lo que dice su ficha para que el equipo de ese mundo alcance), mundo,
    herr (herramientas activas)."""
    asegurar_basicas(perfil)
    m = MUNDOS[mundo]
    hs = {t: herramienta_activa(perfil, t) for t in TIPOS_HERR}
    cana, cuerda, anzuelo = (hs[t]["est"] for t in TIPOS_HERR)
    return {
        "alcance": m["alcance"], "prof": m["prof"], "estab": m["aspera"], "barco": m["barco"],
        "C": 3.2 + 1.7 * (cuerda - 1),
        "P": 1.8 + 1.0 * (cana - 1),
        "fuerza": m["fuerza"],
        "clavar": 0.80 + 0.04 * (anzuelo - 1),
        "agarre": 1.0 - 0.17 * (anzuelo - 1),
        "cana": cana, "cuerda": cuerda, "anzuelo": anzuelo, "mundo": mundo, "herr": hs,
    }


# ---------------------------------------------------------------- tiempos, puntos y metas
def fuerza_pez(sp, mundo):
    """Fuerza efectiva de un pez en un mundo (la ficha de arte x el factor del mundo)."""
    return arte.PECES[sp][6] * MUNDOS[mundo]["fuerza"]


def duracion_partida(mundo):
    return DURACION_BASE + DURACION_POR_MUNDO * (mundo + 1)


def tiempo_forcejeo(grado, mundo):
    """Segundos objetivo del forcejeo de un buen jugador (25 s en lo mas facil, ~40 s en lo mas dificil)."""
    return FORCEJEO_BASE + FORCEJEO_POR_GRADO * grado + FORCEJEO_POR_MUNDO * mundo


def puntos_captura(sp, nuevo=False):
    d = arte.PECES[sp]
    return d[11] + (BONO_EVENTO if d[12] else 0) + (BONO_NUEVO if nuevo else 0)


def metas_mundo(i):
    """Puntos para 1, 2 y 3 estrellas de la partida: 1 pez, 2 peces y 3.5 peces de puntos medios del mundo."""
    ids = [s for s in objetivos(i) + fondo(i) if not arte.PECES[s][12]] or ["sardina"]
    prom = sum(arte.PECES[s][11] for s in ids if s in arte.PECES) / max(1, len(ids))
    return (max(5, int(prom * 0.8)), max(10, int(prom * 2.0)), max(20, int(prom * 3.6)))


def resumen(perfil):
    """Datos sueltos para pantallas."""
    i = mundo_actual(perfil)
    return {
        "mundo": i, "abiertos": mundos_abiertos(perfil), "progreso": progreso(perfil, i),
        "pendientes": objetivos_pendientes(perfil, i), "equipo": estrellas_equipo(perfil),
        "requeridas": estrellas_requeridas(i), "jugable": puede_pescar(perfil, i)[0],
        "especies": len(especies_registradas(perfil)),
    }
