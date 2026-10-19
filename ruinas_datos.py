"""Datos de las Ruinas Antiguas: 5 mundos de criaturas mitologicas x 6 murales, el desbloqueo por mundos y el progreso.

Sin dibujo ni pygame: solo reglas. El mural i (0..29) es el mundo i // 6, fase i % 6. Las 6 fases de cada mundo usan las
mismas cuadriculas (6, 9, 12, 16, 20 y 24 piezas). Un mundo se abre al completar los 6 murales del anterior (como Fosiles).
Se guarda en perfil.extra["ruinas"]:
    {"hechas": [indices de mural completados], "mejor": {i: segundos}, "estrellas": {i: 1..3}}
(las claves de los diccionarios se normalizan a int al leer, porque JSON las vuelve texto).
"""

POR_MUNDO = 6
FASES = [(3, 2), (3, 3), (4, 3), (4, 4), (5, 4), (6, 4)]      # (columnas, filas): 6, 9, 12, 16, 20 y 24 piezas
AYUDA_FASE = [2, 2, 2, 1, 1, 0]       # 2 = mural fantasma tenue + brillo en pieza bien puesta, 1 = solo brillo, 0 = nada

MUNDOS = [
    dict(id="griego", nombre="Mundo Griego", corto="Griego", color=(60, 140, 190)),
    dict(id="nordico", nombre="Mundo Nórdico", corto="Nórdico", color=(110, 120, 205)),
    dict(id="egipcio", nombre="Mundo Egipcio", corto="Egipcio", color=(205, 150, 50)),
    dict(id="oriental", nombre="Mundo Oriental", corto="Oriental", color=(200, 80, 70)),
    dict(id="leyendas", nombre="Leyendas del Mundo", corto="Leyendas", color=(150, 100, 200)),
]
N_MUNDOS = len(MUNDOS)
RUINAS = FASES * N_MUNDOS
N_RUINAS = len(RUINAS)                # 30
AYUDA = AYUDA_FASE * N_MUNDOS

# Estrellas por tiempo: segundos por pieza
PAR_2 = 12.0
PAR_3 = 7.0


# ---------------------------------------------------------------- indices
def mundo_de(i):
    return i // POR_MUNDO


def fase_de(i):
    return i % POR_MUNDO


def indice(mundo, fase):
    return mundo * POR_MUNDO + fase


def indices_mundo(mundo):
    return list(range(mundo * POR_MUNDO, (mundo + 1) * POR_MUNDO))


# ---------------------------------------------------------------- estado guardado
def estado(perfil):
    e = perfil.extra.get("ruinas")
    if not isinstance(e, dict):
        e = {}
        perfil.extra["ruinas"] = e
    e.setdefault("hechas", [])
    for clave in ("mejor", "estrellas"):
        d = e.get(clave)
        if not isinstance(d, dict):
            d = {}
        e[clave] = {int(k): v for k, v in d.items()}
    e["hechas"] = [int(i) for i in e["hechas"]]
    return e


def hecha(perfil, i):
    return i in estado(perfil)["hechas"]


def estrellas(perfil, i):
    return int(estado(perfil)["estrellas"].get(i, 0))


def mejor_tiempo(perfil, i):
    return estado(perfil)["mejor"].get(i)


def total_hechas(perfil):
    return len(set(estado(perfil)["hechas"]))


def registrar(perfil, i, segundos, estrellas_n):
    """Anota un mural completado. Devuelve True si es la primera vez que se completa."""
    e = estado(perfil)
    primera = i not in e["hechas"]
    if primera:
        e["hechas"].append(i)
    m = e["mejor"].get(i)
    if m is None or segundos < m:
        e["mejor"][i] = round(float(segundos), 1)
    if estrellas_n > e["estrellas"].get(i, 0):
        e["estrellas"][i] = int(estrellas_n)
    return primera


def monedas_por(i, estrellas_n):
    """Monedas al completar el mural i: crecen con la fase y con el mundo."""
    return 10 * (fase_de(i) + 1 + 2 * mundo_de(i)) * estrellas_n


# ---------------------------------------------------------------- mundos y desbloqueo
def hechas_mundo(perfil, mundo):
    h = set(estado(perfil)["hechas"])
    return sum(1 for i in indices_mundo(mundo) if i in h)


def mundo_completo(perfil, mundo):
    """True si ya se completaron los 6 murales del mundo (la llave del siguiente)."""
    return hechas_mundo(perfil, mundo) >= POR_MUNDO


tiene_llave = mundo_completo


def _prueba(ajustes):
    if ajustes is None:
        import ajustes as ajustes_mod
        ajustes = ajustes_mod
    return bool(getattr(ajustes, "MODO_PRUEBA", False))


def mundo_desbloqueado(perfil, mundo, ajustes=None):
    """El mundo 0 esta abierto; cada mundo siguiente se abre al completar los 6 murales del anterior."""
    return mundo == 0 or mundo_completo(perfil, mundo - 1) or _prueba(ajustes)


def faltan(perfil, i):
    """Lista de textos con lo que falta para abrir el mural i (vacia si esta abierto)."""
    m = mundo_de(i)
    if mundo_desbloqueado(perfil, m, ajustes=_Sin):
        return []
    return [f"Completa el {MUNDOS[m - 1]['nombre']}"]


class _Sin:
    """Ajustes vacios: faltan() no mira MODO_PRUEBA."""
    MODO_PRUEBA = False


def abierta(perfil, i, ajustes=None):
    return mundo_desbloqueado(perfil, mundo_de(i), ajustes)


def datos_estado(perfil, ajustes=None):
    """Lista de 'bloqueada' / 'abierta' / 'hecha' para los 30 murales."""
    res = []
    for i in range(N_RUINAS):
        if hecha(perfil, i):
            res.append("hecha")
        elif abierta(perfil, i, ajustes):
            res.append("abierta")
        else:
            res.append("bloqueada")
    return res


def siguiente_abierta(perfil, ajustes=None):
    """Primer mural abierto aun sin hacer (o el primer mural hecho); None si todo esta cerrado."""
    est = datos_estado(perfil, ajustes)
    for i, s in enumerate(est):
        if s == "abierta":
            return i
    for i, s in enumerate(est):
        if s == "hecha":
            return i
    return None


def pares(i):
    """(par_2, par_3) en segundos para el mural i."""
    c, f = RUINAS[i]
    return PAR_2 * c * f, PAR_3 * c * f


# ---------------------------------------------------------------- mundo que se esta viendo en el menu
def elegir_mundo(perfil, mundo):
    """Recuerda el mundo que se estaba viendo (para volver a el al salir de un mural)."""
    if 0 <= mundo < N_MUNDOS:
        estado(perfil)["mundo"] = int(mundo)


def mundo_vista(perfil, ajustes=None):
    """Mundo que muestra el menu al abrirse: el ultimo elegido si sigue abierto; si no, el del siguiente mural por hacer."""
    m = estado(perfil).get("mundo")
    if isinstance(m, int) and 0 <= m < N_MUNDOS and mundo_desbloqueado(perfil, m, ajustes):
        return m
    i = siguiente_abierta(perfil, ajustes)
    return mundo_de(i) if i is not None else 0
