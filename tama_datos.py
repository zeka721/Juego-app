"""Datos y reglas del Tamagotchi de Ninja Mundo (logica pura: sin dibujo, sin pygame).

Todo el estado vive en perfil.extra["tama"] (JSON, claves str). Las funciones que usan azar reciben un
rng inyectable (random.Random) y el tiempo se puede inyectar con `ahora`, asi todo es deterministico en pruebas.
La mascota NUNCA muere: si se descuida se pone triste o enferma y se recupera cuidandola.
"""

import random
import time

try:                                    # registra los platos de cocina en el catalogo (si existen)
    import cocina_datos as _cocina_datos  # noqa: F401
except Exception:                       # pragma: no cover
    _cocina_datos = None
try:
    import recetas as _recetas          # noqa: F401
except Exception:                       # pragma: no cover
    _recetas = None

import catalogo

# =====================================================================
#  CONSTANTES DE BALANCE
# =====================================================================
# --- decaimiento (segundos reales por cada punto perdido) ---
SEG_HAMBRE = 50.0
SEG_FELICIDAD = 70.0
SEG_ENERGIA = 90.0
SEG_LIMPIEZA = 80.0
MULT_FELICIDAD_MAL = 2.5        # la felicidad baja mas rapido si hay hambre baja, cacas o poca salud
MULT_LIMPIEZA_CACA = 0.25       # +25% de suciedad por cada caca
MULT_HAMBRE_DORMIDA = 0.5       # dormida tiene menos hambre
SEG_ENERGIA_DORMIDA = 4.0       # segundos por punto de energia que sube al dormir
SEG_CACA = 300.0                # una caca cada 5 min despierta
MAX_CACAS = 4
SEG_SALUD_BAJA = 60.0           # salud baja 1 punto por minuto si hambre<10 o limpieza<15
SEG_SALUD_SUBE = 20.0           # y sube 1 punto cada 20 s si esta bien cuidada
SALUD_MIN = 10                  # la salud nunca baja de aqui
HAMBRE_CRITICA = 10
LIMPIEZA_CRITICA = 15
OFFLINE_UMBRAL = 120.0          # mas de 2 min sin tick = jugador ausente
OFFLINE_MAX_BAJA = 50           # ausente: ninguna necesidad baja mas de 50 puntos...
OFFLINE_MINIMO = 15             # ...ni por debajo de 15
OFFLINE_MAX_CACAS = 2
NECESIDAD_BAJA = 35             # por debajo de esto una necesidad se considera urgente
PASO_TICK = 10.0                # el tick largo (< umbral) se simula en pasos de 10 s

# --- evolucion ---
XP_ETAPA = (100, 300, 700, 1200)   # XP ACUMULADA para pasar de la etapa i a la siguiente (la 3 = graduacion)
CUIDADO_MIN = (5, 12, 25, 40)      # puntos de cuidado minimos para evolucionar / graduar (bajos a proposito)
XP_JUGAR_MAX = 5
XP_LIMPIAR = 2                     # poco
XP_CURAR = 1
CUIDADO_COMER = 3
CUIDADO_JUGAR = 1
CUIDADO_LIMPIAR = 2
CUIDADO_CURAR = 2
CUIDADO_DORMIR = 1

# --- comida ---
BONUS_FAVORITA = 1.5
HAMBRE_SIN_XP = 90                 # comer con hambre mayor a esto no da xp ni cuidado (evita abusar)

# --- eclosion ---
CALOR_POR_SEGUNDO = 1.0 / 50.0     # calor (0..1) por segundo de frotado efectivo: ~50 s de interaccion

# --- juego / cuidado ---
JUGAR_FELIC_POR_PUNTO = 0.5
JUGAR_FELIC_MAX = 25
JUGAR_ENERGIA = 5
JUGAR_HAMBRE = 3
LIMPIAR_SUBE = 50
LIMPIAR_FELIC = 5
CURAR_SUBE = 20
CURAR_FELIC = 3

# --- vida (HP) de batalla: persiste entre combates ---
HP_MIN_ENTRENAR = 0.20          # fraccion minima de vida para entrar a una batalla
HP_PISO_DERROTA = 0.15          # al perder la vida queda en 15 %, nunca 0
HP_REGEN_SEG = 30.0             # la vida sube 1 % cada 30 s (x3 si duerme)
HP_REGEN_DORMIDA = 3.0
HP_REGEN_OFFLINE_MAX = 0.25     # ausente: no se cura mas de 25 puntos
HP_URGENTE = 0.30               # por debajo de esto necesita curita
CURAR_SEGUNDOS = 22.0           # duracion de la sesion de curar
CURAR_PASOS = 6                 # curitas por sesion

# --- batalla ---
ESTAMINA_BASICO = 25
ESTAMINA_MAX = 100
XP_BATALLA = {"gana": 30, "pierde": 5, "escapa": 0}   # Horda: victoria completa = la gran recompensa, aun asi chica
XP_BATALLA_BONUS_HP = 10           # extra al ganar, proporcional al HP que queda
XP_DANO_DIV = 50                   # +1 xp por cada 50 de dano hecho...
XP_DANO_MAX = 10                   # ...hasta este tope (se alcanza hacia las 500 derrotas)
MONEDAS_BATALLA = {"gana": 25, "pierde": 5, "escapa": 0}
MONEDAS_BONUS_HP = 15
PROB_ITEM_GANA = 0.15
ITEM_GANA = "fragmento_estelar"
BATALLA_FELIC = {"gana": 10, "pierde": 0, "escapa": 0}
BATALLA_ENERGIA = 15
BATALLA_HAMBRE = 10
BATALLA_MIN_HAMBRE = 10            # la batalla no deja la mascota con menos que esto
BATALLA_MIN_ENERGIA = 10
HP_ETAPA = (60, 100, 150, 220)
ATAQUE_ETAPA = (10, 16, 24, 34)
MULT_VENTAJA = 1.5
MULT_DESVENTAJA = 0.67
MULT_CARGADO = 2.6
CALIDAD_MIN, CALIDAD_MAX = 0.5, 1.2

# =====================================================================
#  TIPOS Y ESPECIES
# =====================================================================
TIPOS = ["agua", "viento", "fuego", "hielo", "tierra", "electrico"]
NOMBRE_TIPO = {"agua": "Agua", "viento": "Viento", "fuego": "Fuego", "hielo": "Hielo",
               "tierra": "Tierra", "electrico": "Eléctrico"}
ETAPAS = ["Bebé", "Niño", "Adulto", "Ultimate"]

# cada tipo gana al siguiente: fuego > hielo > viento > tierra > electrico > agua > fuego
CICLO = ["fuego", "hielo", "viento", "tierra", "electrico", "agua"]

_DEF = [
    ("agua", "delfin", "delfin", ["Gotin", "Salpin", "Delfaron", "Delfonte"]),
    ("agua", "tortuga", "tortuga", ["Tortin", "Marin", "Caparazul", "Tortamarea"]),
    ("agua", "pulpo", "pulpo", ["Burbi", "Pulpin", "Octoparla", "Abisalo"]),
    ("viento", "mariposa", "mariposa", ["Alin", "Mariposin", "Brisaflor", "Alaciclon"]),
    ("viento", "ardilla", "ardilla voladora", ["Rafi", "Planin", "Ventarro", "Tornadero"]),
    ("viento", "buho", "buho", ["Plumin", "Buhito", "Nocturvento", "Buhotempestad"]),
    ("fuego", "dragon", "dragon", ["Brasin", "Dragulla", "Pirodraco", "Dracolava"]),
    ("fuego", "lobo", "lobo", ["Ascuito", "Cenizo", "Lobollama", "Lobo Solar"]),
    ("fuego", "fenix", "fenix", ["Cenicin", "Pollollama", "Ave Brasa", "Fenix Solar"]),
    ("hielo", "pinguino", "pinguino", ["Copito", "Pinguin", "Glacialpin", "Pinguirey"]),
    ("hielo", "oso", "oso polar", ["Nevadito", "Osnevado", "Glaciosso", "Osoboreal"]),
    ("hielo", "ciervo", "ciervo", ["Escarchin", "Cervatillo", "Ciervo Glacial", "Cervirey Cristal"]),
    ("tierra", "armadillo", "armadillo", ["Rocadillo", "Armadin", "Tierradillo", "Armadura Titan"]),
    ("tierra", "topo", "topo", ["Toposo", "Topin", "Excavon", "Topogigante"]),
    ("tierra", "escarabajo", "escarabajo", ["Terron", "Escarabin", "Cuernoroca", "Escarabeon"]),
    ("electrico", "raton", "raton", ["Voltin", "Ratonchispa", "Electrorrata", "Megavoltio"]),
    ("electrico", "gato", "gato/tigre", ["Zapin", "Gatochispa", "Truenotigre", "Tigre Relampago"]),
    ("electrico", "rana", "rana", ["Zumbi", "Ranazap", "Voltirrana", "Rey Trueno"]),
]
ESPECIES = {i: dict(id=i, tipo=t, animal=a, formas=list(f)) for t, i, a, f in _DEF}
ORDEN = [d[1] for d in _DEF]
NUM_HUEVOS = len(ORDEN)

# categoria de comida favorita por especie (rota entre estas)
_FAV_CATS = ["fruta", "verdura", "comida", "granja", "pesca"]
FAVORITAS = {e: _FAV_CATS[(i * 2 + i // 5) % len(_FAV_CATS)] for i, e in enumerate(ORDEN)}

NECESIDADES = ("hambre", "felicidad", "energia", "limpieza", "salud")


# =====================================================================
#  ESTADO
# =====================================================================
def _ahora(ahora):
    return time.time() if ahora is None else float(ahora)


def _clamp(v, a=0.0, b=100.0):
    return max(a, min(b, v))


def _num(v, d):
    try:
        return float(v) if not isinstance(v, bool) else d
    except (TypeError, ValueError):
        return d


def _mascota_nueva(especie, ahora, etapa=0):
    return dict(especie=especie, etapa=etapa, xp=0, hambre=70.0, felicidad=80.0, energia=90.0, limpieza=100.0,
                salud=100.0, hp=1.0, cacas=0, dormida=False, ultimo=ahora, cuidado=0, batallas=0, victorias=0,
                nombre=ESPECIES[especie]["formas"][etapa], t_caca=0.0)


def _normalizar_mascota(m, ahora):
    if not isinstance(m, dict) or m.get("especie") not in ESPECIES:
        return None
    d = _mascota_nueva(m["especie"], ahora)
    d["etapa"] = int(_clamp(_num(m.get("etapa"), 0), 0, 3))
    d["nombre"] = m.get("nombre") if isinstance(m.get("nombre"), str) and m.get("nombre") else \
        ESPECIES[d["especie"]]["formas"][d["etapa"]]
    d["xp"] = int(max(0, _num(m.get("xp"), 0)))
    for k in NECESIDADES:
        d[k] = _clamp(_num(m.get(k), d[k]))
    d["salud"] = max(SALUD_MIN, d["salud"])
    d["hp"] = _clamp(_num(m.get("hp"), 1.0), 0.0, 1.0)
    d["cacas"] = int(_clamp(_num(m.get("cacas"), 0), 0, MAX_CACAS))
    d["dormida"] = bool(m.get("dormida", False))
    d["ultimo"] = _num(m.get("ultimo"), ahora)
    d["t_caca"] = max(0.0, _num(m.get("t_caca"), 0.0))
    for k in ("cuidado", "batallas", "victorias"):
        d[k] = int(max(0, _num(m.get(k), 0)))
    m.clear()                      # se normaliza EN SITIO: quien guarde una referencia a la mascota la sigue viendo viva
    m.update(d)
    return m


def estado(perfil, rng=None):
    """Estado normalizado (dict vivo guardado en perfil.extra['tama']). Crea/repara lo que falte.
    El mapeo huevo->especie se baraja UNA sola vez (con rng si se da) y queda guardado."""
    ex = perfil.extra
    st = ex.get("tama")
    if not isinstance(st, dict):
        st = {}
    huevos = st.get("huevos")
    if not (isinstance(huevos, list) and sorted(huevos) == sorted(ORDEN)):
        huevos = list(ORDEN)
        (rng or random.Random()).shuffle(huevos)
    st["huevos"] = [str(h) for h in huevos]
    h = st.get("huevo")
    st["huevo"] = int(h) if isinstance(h, int) and not isinstance(h, bool) and 0 <= h < NUM_HUEVOS else None
    st["calor"] = _clamp(_num(st.get("calor"), 0.0), 0.0, 1.0)
    ecl = st.get("eclosionados")
    st["eclosionados"] = sorted({int(k) for k in ecl if isinstance(k, int) and 0 <= k < NUM_HUEVOS}) \
        if isinstance(ecl, list) else []
    st["activa"] = _normalizar_mascota(st.get("activa"), _ahora(None))
    desc = st.get("descubiertas")
    st["descubiertas"] = {e: int(_clamp(_num(v, 0), 0, 3)) for e, v in desc.items() if e in ESPECIES} \
        if isinstance(desc, dict) else {}
    salon = st.get("salon")
    st["salon"] = [dict(especie=s["especie"], etapa=int(_clamp(_num(s.get("etapa"), 3), 0, 3)),
                        nombre=str(s.get("nombre", ""))) for s in salon
                   if isinstance(s, dict) and s.get("especie") in ESPECIES] if isinstance(salon, list) else []
    ex["tama"] = st
    return st


def especie_de_huevo(perfil, k):
    return estado(perfil)["huevos"][k]


# =====================================================================
#  ECLOSION
# =====================================================================
def elegir_huevo(perfil, k):
    st = estado(perfil)
    if st["activa"] is not None or st["huevo"] is not None:
        return False
    if not isinstance(k, int) or isinstance(k, bool) or not 0 <= k < NUM_HUEVOS or k in st["eclosionados"]:
        return False
    st["huevo"] = k
    st["calor"] = 0.0
    return True


def calentar(perfil, cantidad):
    """Suma progreso (0..1) de eclosion. Usar cantidad = segundos_frotando * CALOR_POR_SEGUNDO."""
    st = estado(perfil)
    if st["huevo"] is None:
        return st["calor"]
    st["calor"] = _clamp(st["calor"] + max(0.0, float(cantidad)), 0.0, 1.0)
    return st["calor"]


def calor_listo(perfil):
    st = estado(perfil)
    return st["huevo"] is not None and st["calor"] >= 1.0


def eclosionar(perfil, ahora=None):
    """Abre el huevo elegido (si el calor esta completo). Devuelve la especie o None."""
    st = estado(perfil)
    if not calor_listo(perfil):
        return None
    k = st["huevo"]
    esp = st["huevos"][k]
    st["eclosionados"] = sorted(set(st["eclosionados"]) | {k})
    st["huevo"] = None
    st["calor"] = 0.0
    st["activa"] = _mascota_nueva(esp, _ahora(ahora))
    st["descubiertas"][esp] = max(st["descubiertas"].get(esp, 0), 0)
    return esp


# =====================================================================
#  PASO DEL TIEMPO
# =====================================================================
def _paso(m, dt, rng):
    """Un paso corto de tiempo real (jugador presente)."""
    if m["dormida"]:
        m["energia"] = _clamp(m["energia"] + dt / SEG_ENERGIA_DORMIDA)
        if m["energia"] >= 100:
            m["dormida"] = False
        m["hambre"] = _clamp(m["hambre"] - dt / (SEG_HAMBRE / MULT_HAMBRE_DORMIDA))
    else:
        m["hambre"] = _clamp(m["hambre"] - dt / SEG_HAMBRE)
        m["energia"] = _clamp(m["energia"] - dt / SEG_ENERGIA)
        m["t_caca"] += dt
        while m["t_caca"] >= SEG_CACA:
            m["t_caca"] -= SEG_CACA
            m["cacas"] = min(MAX_CACAS, m["cacas"] + 1)
    m["limpieza"] = _clamp(m["limpieza"] - dt / SEG_LIMPIEZA * (1 + MULT_LIMPIEZA_CACA * m["cacas"]))
    m["hp"] = min(1.0, m["hp"] + dt / HP_REGEN_SEG / 100.0 * (HP_REGEN_DORMIDA if m["dormida"] else 1.0))
    mal = m["hambre"] < 30 or m["cacas"] > 0 or m["salud"] < 40
    if not m["dormida"]:
        m["felicidad"] = _clamp(m["felicidad"] - dt / SEG_FELICIDAD * (MULT_FELICIDAD_MAL if mal else 1.0))
    if m["hambre"] < HAMBRE_CRITICA or m["limpieza"] < LIMPIEZA_CRITICA:
        m["salud"] = max(SALUD_MIN, m["salud"] - dt / SEG_SALUD_BAJA)
    elif m["hambre"] >= 30 and m["limpieza"] >= 30:
        m["salud"] = _clamp(m["salud"] + dt / SEG_SALUD_SUBE)


def _ausente(m, dt):
    """El jugador no estuvo: bajadas limitadas (max -50, nunca por debajo de 15), salud intacta."""
    def baja(v, seg):
        if v <= OFFLINE_MINIMO:
            return v
        return max(OFFLINE_MINIMO, v - min(OFFLINE_MAX_BAJA, dt / seg))
    dormida = m["dormida"]
    if m["dormida"]:
        m["energia"] = _clamp(m["energia"] + dt / SEG_ENERGIA_DORMIDA)
        if m["energia"] >= 100:
            m["dormida"] = False
        m["hambre"] = baja(m["hambre"], SEG_HAMBRE / MULT_HAMBRE_DORMIDA)
    else:
        m["hambre"] = baja(m["hambre"], SEG_HAMBRE)
        m["energia"] = baja(m["energia"], SEG_ENERGIA)
        m["felicidad"] = baja(m["felicidad"], SEG_FELICIDAD)
        m["cacas"] = min(MAX_CACAS, m["cacas"] + min(OFFLINE_MAX_CACAS, int(dt // SEG_CACA)))
    m["limpieza"] = baja(m["limpieza"], SEG_LIMPIEZA)
    sube = dt / HP_REGEN_SEG / 100.0 * (HP_REGEN_DORMIDA if dormida else 1.0)
    m["hp"] = min(1.0, m["hp"] + min(HP_REGEN_OFFLINE_MAX, sube))


def tick(perfil, ahora=None, rng=None):
    """Aplica el paso del tiempo real desde el ultimo tick. Nunca mata: salud >= SALUD_MIN."""
    st = estado(perfil)
    m = st["activa"]
    ahora = _ahora(ahora)
    if m is None:
        return st
    dt = ahora - m["ultimo"]
    m["ultimo"] = ahora
    if dt <= 0:
        return st
    if dt > OFFLINE_UMBRAL:
        _ausente(m, dt)
    else:
        n = int(dt // PASO_TICK)
        for _ in range(n):
            _paso(m, PASO_TICK, rng)
        resto = dt - n * PASO_TICK
        if resto > 0:
            _paso(m, resto, rng)
    return st


def enferma(perfil):
    m = estado(perfil)["activa"]
    return m is not None and (m["salud"] < 40 or m["hp"] < HP_URGENTE)


def necesidad_baja(perfil):
    """Nombre de la necesidad mas urgente (hambre, sueno, diversion, limpieza, salud) o None."""
    m = estado(perfil)["activa"]
    if m is None or m["dormida"]:
        return None
    cand = {"hambre": m["hambre"], "sueno": m["energia"], "diversion": m["felicidad"],
            "limpieza": min(m["limpieza"], 25 if m["cacas"] >= 2 else 100),
            "salud": min(m["salud"], 20.0 if m["hp"] < HP_URGENTE else 100.0)}
    nombre, v = min(cand.items(), key=lambda kv: kv[1])
    return nombre if v < NECESIDAD_BAJA else None


# =====================================================================
#  COMIDA
# =====================================================================
# categoria -> (hambre, felicidad, xp); None = no es comida
VALOR_CATEGORIA = {"fruta": (12, 6, 4), "verdura": (12, 4, 4), "comida": (45, 15, 14)}
# por item: ajustes finos (los ingredientes crudos como harina, azucar, sal, aceite, arroz, carne... no son comida)
VALOR_ITEM = {
    "huevo": (15, 3, 3), "leche": (18, 6, 3), "pescado": (18, 4, 3), "huevas": (10, 3, 2), "alga": (8, 1, 1),
    "pan": (22, 4, 3), "queso": (14, 4, 3), "miel": (10, 10, 3), "mermelada": (10, 8, 3),
    "chocolate": (10, 14, 3), "crema_cacao": (10, 12, 3), "nueces": (10, 4, 3),
    "alimento_animal": None, "alimento_peces": None, "lana": None,
}


def valor_comida(item):
    """dict(hambre, felicidad, xp) o None si no es comida. Funciona aunque el item no este registrado."""
    if item in VALOR_ITEM:
        v = VALOR_ITEM[item]
        return None if v is None else dict(hambre=v[0], felicidad=v[1], xp=v[2])
    inf = catalogo.info(item)
    cat = inf.get("cat")
    if cat == "comida" or (cat == "otro" and str(item).startswith("plato_")):
        precio = int(inf.get("precio", 0) or 0)       # platos mas caros (mas elaborados) alimentan algo mas
        return dict(hambre=45 + min(25, precio // 6), felicidad=15 + min(10, precio // 15),
                    xp=14 + min(8, precio // 15))
    v = VALOR_CATEGORIA.get(cat)
    return None if v is None else dict(hambre=v[0], felicidad=v[1], xp=v[2])


def comidas(perfil):
    """[(item_id, cantidad)] del inventario que son comida, ordenados por categoria y nombre."""
    orden = {c: i for i, (c, _t) in enumerate(catalogo.CATEGORIAS)}
    res = [(k, int(n)) for k, n in perfil.inventario.items() if n > 0 and valor_comida(k) is not None]
    res.sort(key=lambda kn: (orden.get(catalogo.info(kn[0])["cat"], 99), kn[0]))
    return res


def favorita(especie):
    """Categoria de comida preferida (bonus x1.5): fruta, verdura, comida, granja o pesca."""
    return FAVORITAS.get(especie, "fruta")


def comer(perfil, item):
    """Da de comer 1 unidad. None si no hay mascota despierta, no es comida o no hay en el inventario."""
    st = estado(perfil)
    m = st["activa"]
    v = valor_comida(item)
    if m is None or m["dormida"] or v is None or perfil.cantidad(item) < 1:
        return None
    perfil.quitar(item, 1)
    fav = catalogo.info(item)["cat"] == favorita(m["especie"])
    k = BONUS_FAVORITA if fav else 1.0
    antes = m["hambre"]
    h = int(round(v["hambre"] * k))
    f = int(round(v["felicidad"] * k))
    xp = int(round(v["xp"] * k)) if antes <= HAMBRE_SIN_XP else 0
    m["hambre"] = _clamp(m["hambre"] + h)
    m["felicidad"] = _clamp(m["felicidad"] + f)
    if xp:
        m["cuidado"] += CUIDADO_COMER
        dar_xp(perfil, xp)
    return dict(item=item, hambre=h, felicidad=f, xp=xp, favorita=fav, evoluciona=puede_evolucionar(perfil))


# =====================================================================
#  CUIDADOS
# =====================================================================
def jugar(perfil, puntos):
    """Suma felicidad segun los puntos del minijuego. Devuelve la felicidad ganada."""
    m = estado(perfil)["activa"]
    if m is None or m["dormida"]:
        return 0
    g = min(JUGAR_FELIC_MAX, max(0.0, puntos) * JUGAR_FELIC_POR_PUNTO)
    antes = m["felicidad"]
    m["felicidad"] = _clamp(antes + g)
    m["energia"] = max(0.0, m["energia"] - JUGAR_ENERGIA)
    m["hambre"] = max(5.0, m["hambre"] - JUGAR_HAMBRE)
    m["cuidado"] += CUIDADO_JUGAR
    dar_xp(perfil, min(XP_JUGAR_MAX, int(puntos // 10)))
    return m["felicidad"] - antes


def limpiar(perfil):
    """Quita las cacas y sube la limpieza. False si no hacia falta."""
    m = estado(perfil)["activa"]
    if m is None or (m["cacas"] == 0 and m["limpieza"] >= 95):
        return False
    m["cacas"] = 0
    m["limpieza"] = _clamp(m["limpieza"] + LIMPIAR_SUBE)
    m["felicidad"] = _clamp(m["felicidad"] + LIMPIAR_FELIC)
    m["cuidado"] += CUIDADO_LIMPIAR
    dar_xp(perfil, XP_LIMPIAR)
    return True


def dormir(perfil, on):
    """Acuesta o despierta. Devuelve el estado final (dormida)."""
    m = estado(perfil)["activa"]
    if m is None:
        return False
    on = bool(on)
    if on and not m["dormida"]:
        m["cuidado"] += CUIDADO_DORMIR
    m["dormida"] = on
    return m["dormida"]


def curar(perfil):
    """Gratis. Sube la salud (el cuidado es repetirlo). False si ya estaba sana."""
    m = estado(perfil)["activa"]
    if m is None or (m["salud"] >= 100 and m["hp"] >= 1.0):
        return False
    m["salud"] = _clamp(m["salud"] + CURAR_SUBE)
    m["hp"] = 1.0
    m["felicidad"] = _clamp(m["felicidad"] + CURAR_FELIC)
    m["cuidado"] += CUIDADO_CURAR
    dar_xp(perfil, XP_CURAR)
    return True


def hp_frac(perfil):
    m = estado(perfil)["activa"]
    return m["hp"] if m else 1.0


def guardar_hp(perfil, frac, piso=0.0):
    """Guarda la vida de batalla (fraccion 0..1, con piso). Devuelve el valor guardado."""
    m = estado(perfil)["activa"]
    v = max(_clamp(float(frac), 0.0, 1.0), _clamp(float(piso), 0.0, 1.0))
    if m is not None:
        m["hp"] = v
    return v


def puede_entrenar(perfil):
    m = estado(perfil)["activa"]
    return m is not None and m["hp"] >= HP_MIN_ENTRENAR


def necesita_curar(perfil):
    m = estado(perfil)["activa"]
    return m is not None and (m["hp"] < 1.0 or m["salud"] < 100)


def curar_inicio(perfil):
    """Empieza una sesion de curar. dict(hp0, salud0, n) o None si no hace falta."""
    if not necesita_curar(perfil):
        return None
    m = estado(perfil)["activa"]
    return dict(hp0=m["hp"], salud0=m["salud"], n=CURAR_PASOS, k=0, fin=False)


def curar_paso(perfil, ctx, k):
    """Aplica la curita k (1..n). Nunca baja lo ya recuperado. Devuelve dict(hp, salud)."""
    m = estado(perfil)["activa"]
    n = max(1, int(ctx.get("n", CURAR_PASOS)))
    k = int(_clamp(k, 0, n))
    if m is None:
        return dict(hp=1.0, salud=100.0)
    f = k / n
    hp = ctx["hp0"] + (1.0 - ctx["hp0"]) * f
    salud = min(100.0, ctx["salud0"] + max((100.0 - ctx["salud0"]) * f, CURAR_SUBE * f))
    m["hp"] = max(m["hp"], min(1.0, hp))
    m["salud"] = max(m["salud"], salud)
    ctx["k"] = max(ctx.get("k", 0), k)
    return dict(hp=m["hp"], salud=m["salud"])


def curar_fin(perfil, ctx):
    """Cierra la sesion: da UNA sola vez felicidad, cuidado y xp (si hubo al menos una curita).
    Deja hp/salud en 100 solo si se completaron todos los pasos. True si dio las recompensas."""
    m = estado(perfil)["activa"]
    if m is None or ctx.get("fin") or ctx.get("k", 0) < 1:
        return False
    ctx["fin"] = True
    if ctx["k"] >= int(ctx.get("n", CURAR_PASOS)):
        m["hp"] = 1.0
        m["salud"] = 100.0
    m["felicidad"] = _clamp(m["felicidad"] + CURAR_FELIC)
    m["cuidado"] += CUIDADO_CURAR
    dar_xp(perfil, XP_CURAR)
    return True


# =====================================================================
#  EVOLUCION
# =====================================================================
def xp_necesaria(etapa):
    """XP acumulada que hay que tener en esta etapa para pasar a la siguiente (en la 3: para graduarse)."""
    return XP_ETAPA[int(_clamp(etapa, 0, 3))]


def dar_xp(perfil, n):
    """Suma xp (tope = la necesaria de la etapa actual). Devuelve la xp ganada de verdad."""
    m = estado(perfil)["activa"]
    if m is None or n <= 0:
        return 0
    antes = m["xp"]
    m["xp"] = min(xp_necesaria(m["etapa"]), antes + int(n))
    return m["xp"] - antes


def puede_evolucionar(perfil):
    m = estado(perfil)["activa"]
    return (m is not None and m["etapa"] < 3 and m["xp"] >= xp_necesaria(m["etapa"])
            and m["cuidado"] >= CUIDADO_MIN[m["etapa"]])


def evolucionar(perfil):
    """Pasa a la siguiente etapa y la deja descansada. Devuelve la nueva etapa o None."""
    st = estado(perfil)
    if not puede_evolucionar(perfil):
        return None
    m = st["activa"]
    viejo = ESPECIES[m["especie"]]["formas"][m["etapa"]]
    m["etapa"] += 1
    if m["nombre"] == viejo:                      # si el nino le puso nombre propio se conserva
        m["nombre"] = ESPECIES[m["especie"]]["formas"][m["etapa"]]
    for k in ("hambre", "felicidad", "energia", "limpieza"):
        m[k] = max(m[k], 70.0)
    m["salud"] = 100.0
    m["dormida"] = False
    st["descubiertas"][m["especie"]] = max(st["descubiertas"].get(m["especie"], 0), m["etapa"])
    return m["etapa"]


def puede_graduar(perfil):
    m = estado(perfil)["activa"]
    return (m is not None and m["etapa"] == 3 and m["xp"] >= xp_necesaria(3)
            and m["cuidado"] >= CUIDADO_MIN[3])


def graduar(perfil):
    """Ultimate con xp lleno: pasa al salon y se libera para elegir otro huevo. Devuelve True/False."""
    st = estado(perfil)
    if not puede_graduar(perfil):
        return False
    m = st["activa"]
    st["salon"].append(dict(especie=m["especie"], etapa=m["etapa"], nombre=m["nombre"]))
    st["activa"] = None
    st["huevo"] = None
    st["calor"] = 0.0
    if len(st["eclosionados"]) >= NUM_HUEVOS:     # si ya abrio los 18, vuelven a estar disponibles
        st["eclosionados"] = []
    return True


def aviso_evolucion(perfil):
    """Hay una evolucion o graduacion pendiente (para el aviso del hub)."""
    return puede_evolucionar(perfil) or puede_graduar(perfil)


# =====================================================================
#  BATALLA
# =====================================================================
def stats(especie, etapa):
    """dict(hp, ataque, estamina_max). Ligera variacion por especie (+-5%) segun su posicion."""
    etapa = int(_clamp(etapa, 0, 3))
    idx = ORDEN.index(especie) if especie in ORDEN else 0
    var = ((idx * 7) % 11 - 5) / 100.0            # -0.05 .. +0.05
    return dict(hp=int(round(HP_ETAPA[etapa] * (1 - var))), ataque=int(round(ATAQUE_ETAPA[etapa] * (1 + var))),
                estamina_max=ESTAMINA_MAX)


def ventaja(tipo_atacante, tipo_defensor):
    if tipo_atacante not in CICLO or tipo_defensor not in CICLO:
        return 1.0
    i = CICLO.index(tipo_atacante)
    if CICLO[(i + 1) % len(CICLO)] == tipo_defensor:
        return MULT_VENTAJA
    if CICLO[(i - 1) % len(CICLO)] == tipo_defensor:
        return MULT_DESVENTAJA
    return 1.0


def dano(ataque_stats, etapa, tipo_a, tipo_d, cargado=False, calidad=1.0, rng=None):
    """Dano entero (>=1). ataque_stats = dict de stats() o el numero de ataque. Basico: ataque*0.9..1.1
    (1.0 si no hay rng); cargado: ataque*2.6*calidad(0.5..1.2). Multiplica por la ventaja de tipo."""
    ataque = ataque_stats["ataque"] if isinstance(ataque_stats, dict) else float(ataque_stats)
    if cargado:
        base = ataque * MULT_CARGADO * _clamp(calidad, CALIDAD_MIN, CALIDAD_MAX)
    else:
        base = ataque * (rng.uniform(0.9, 1.1) if rng is not None else 1.0)
    return max(1, int(round(base * ventaja(tipo_a, tipo_d))))


def enemigo(perfil, rng=None):
    """Rival de etapa igual o +-1 a la de la mascota y tipo al azar."""
    rng = rng or random.Random()
    m = estado(perfil)["activa"]
    base = m["etapa"] if m else 0
    etapa = int(_clamp(base + rng.choice((-1, 0, 1)), 0, 3))
    tipo = rng.choice(TIPOS)
    esp = rng.choice([e for e in ORDEN if ESPECIES[e]["tipo"] == tipo])
    s = stats(esp, etapa)
    return dict(especie=esp, etapa=etapa, tipo=tipo, hp=s["hp"], ataque=s["ataque"],
                nombre=ESPECIES[esp]["formas"][etapa])


def recompensa_batalla(perfil, resultado, dano_hecho, hp_restante_frac, rng=None):
    """Calcula Y APLICA xp, monedas e items. Devuelve dict(xp, monedas, items)."""
    rng = rng or random.Random()
    if resultado not in XP_BATALLA:
        resultado = "escapa"
    frac = _clamp(float(hp_restante_frac), 0.0, 1.0)
    xp = XP_BATALLA[resultado] + min(XP_DANO_MAX, int(max(0, dano_hecho) // XP_DANO_DIV))
    monedas = MONEDAS_BATALLA[resultado]
    items = {}
    if resultado == "gana":
        xp += int(round(XP_BATALLA_BONUS_HP * frac))
        monedas += int(round(MONEDAS_BONUS_HP * frac))
        if rng.random() < PROB_ITEM_GANA:
            items[ITEM_GANA] = 1
    m = estado(perfil)["activa"]
    if m is not None:
        m["batallas"] += 1
        if resultado == "gana":
            m["victorias"] += 1
        m["felicidad"] = _clamp(m["felicidad"] + BATALLA_FELIC[resultado])
        if resultado != "escapa":
            m["energia"] = max(min(m["energia"], BATALLA_MIN_ENERGIA), m["energia"] - BATALLA_ENERGIA)
            m["hambre"] = max(min(m["hambre"], BATALLA_MIN_HAMBRE), m["hambre"] - BATALLA_HAMBRE)
        dar_xp(perfil, xp)
    if monedas:
        perfil.ganar(monedas)
    for k, n in items.items():
        perfil.dar(k, n)
    return dict(xp=xp, monedas=monedas, items=items)
