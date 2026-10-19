"""Datos de Defensa Espacial: planetas (mundos), fases, jefes, piezas, componentes de la nave nodriza y sondas.

Guardado en perfil.extra["espacio"]:
  mineral      int, mineral espacial que tienes
  piezas       {id_mundo: [fases con su pieza]}           (3 piezas por mundo)
  jefes        [mundos con el jefe vencido]
  componentes  [componentes instalados en la nave nodriza]  (6 piezas cada uno)
  sondas       {id_sonda: {"hp": n, "escudo": n, "arma": n}}   (cada sonda guarda las suyas)
  elegida      indice de la sonda con la que vuelas

Mundos: los 8 planetas en orden del Sol (1 Mercurio ... 8 Neptuno). Cada uno da 3 piezas (3 fases + jefe).
Componentes: cada uno sale de dos mundos seguidos. Sus piezas 1-3 vienen del primer mundo y 4-6 del segundo.

Reglas:
  - Mundo 1 abierto siempre.
  - Mundo par (2, 4, ...): se abre al vencer al jefe del mundo anterior.
  - Mundo impar (3, 5, ...): se abre al instalar el componente de la pareja anterior.
  - Fase f se abre al terminar la f-1. Cada fase es una partida aparte y da una pieza.
  - Sonda k (k = 1..7) se abre al vencer al jefe del mundo k; la basica (k = 0) siempre esta.
  - Componente c se arma cuando los mundos 2c-1 y 2c tienen sus 3 piezas y sus jefes vencidos.

Codigo de partida: mundo * 10 + fase; la fase JEFE es el jefe. Ej.: 11 = Mercurio fase 1, 14 = jefe de Mercurio.
"""

FASES = 3                    # piezas por mundo (una por fase)
JEFE = FASES + 1             # codigo de fase del jefe (4)
PIEZAS_COMPONENTE = 6        # 3 de cada uno de los dos mundos de la pareja
MINERAL_JEFE = 15            # mineral extra la primera vez que vences al jefe de un mundo, x numero de mundo

MUNDOS = [
    dict(id="mercurio", nombre="Mercurio", corto="1 · Mercurio", color=(170, 160, 150),
         fondo=((12, 10, 22), (44, 38, 56)), planeta=(176, 168, 160), rapidez=1.00,
         boss=(190, 180, 170), boss_hp=28),
    dict(id="venus", nombre="Venus", corto="2 · Venus", color=(230, 196, 120),
         fondo=((30, 20, 10), (90, 60, 30)), planeta=(236, 206, 140), rapidez=1.07,
         boss=(232, 186, 96), boss_hp=36),
    dict(id="tierra", nombre="Tierra", corto="3 · Tierra", color=(80, 150, 230),
         fondo=((4, 12, 40), (20, 60, 120)), planeta=(80, 150, 230), rapidez=1.14,
         boss=(90, 170, 240), boss_hp=44),
    dict(id="marte", nombre="Marte", corto="4 · Marte", color=(196, 92, 56),
         fondo=((12, 6, 30), (48, 18, 40)), planeta=(196, 92, 56), rapidez=1.21,
         boss=(214, 96, 60), boss_hp=52),
    dict(id="jupiter", nombre="Júpiter", corto="5 · Júpiter", color=(214, 164, 110),
         fondo=((10, 8, 30), (40, 30, 70)), planeta=(214, 164, 110), bandas=True, rapidez=1.28,
         boss=(226, 150, 84), boss_hp=60),
    dict(id="saturno", nombre="Saturno", corto="6 · Saturno", color=(200, 180, 120),
         fondo=((8, 10, 34), (26, 30, 62)), planeta=(226, 206, 146), anillos=True, rapidez=1.35,
         boss=(206, 186, 120), boss_hp=68),
    dict(id="urano", nombre="Urano", corto="7 · Urano", color=(120, 200, 215),
         fondo=((4, 14, 30), (14, 46, 66)), planeta=(150, 222, 230), rapidez=1.42,
         boss=(90, 210, 222), boss_hp=76),
    dict(id="neptuno", nombre="Neptuno", corto="8 · Neptuno", color=(90, 120, 230),
         fondo=((4, 6, 40), (16, 22, 92)), planeta=(70, 110, 236), rapidez=1.49,
         boss=(70, 100, 230), boss_hp=84),
]
N_MUNDOS = len(MUNDOS)

# Componentes de la nave nodriza: cada uno sale de dos mundos seguidos (la pareja).
COMPONENTES = [
    dict(n=1, nombre="Propulsor 1", mundos=(1, 2), color=(120, 170, 230)),        # Mercurio + Venus
    dict(n=2, nombre="Propulsor 2", mundos=(3, 4), color=(210, 120, 90)),         # Tierra + Marte
    dict(n=3, nombre="Blindaje", mundos=(5, 6), color=(200, 160, 250)),           # Júpiter + Saturno
    dict(n=4, nombre="Módulo de salto hiperespacial", mundos=(7, 8), color=(90, 220, 200)),  # Urano + Neptuno
]
N_COMPONENTES = len(COMPONENTES)

# Tamano de la sonda en pixeles: la imagen y el area que recibe impactos (meteoritos, tiros enemigos, jefe).
SONDA_TAM = (285, 112)

# Sondas: una por planeta. La sonda k se gana al vencer al jefe del mundo k (la basica, k = 0, es la inicial).
# Las sondas 7 y 8 aun no tienen arma propia: por ahora disparan como la basica.
SONDAS = [
    dict(id="basica", nombre="Sonda básica", color=(120, 190, 255), arma=0,
         desc="Disparo simple. Golpe especial: abanico de 5 balas."),
    dict(id="doble", nombre="Sonda doble cañón", color=(120, 220, 120), arma=1,
         desc="Dos cañones a la vez. Golpe especial: cono de 8 balas."),
    dict(id="perforante", nombre="Sonda perforante", color=(200, 130, 255), arma=2,
         desc="Balas que atraviesan hasta 3 meteoritos. Golpe especial: 3 balas gruesas."),
    dict(id="laser", nombre="Sonda láser", color=(255, 90, 90), arma=3,
         desc="Rayo continuo que daña lo que toca. Golpe especial: rayo largo."),
    dict(id="explosivo", nombre="Sonda de misil explosivo", color=(255, 170, 60), arma=4,
         desc="Misiles rectos que explotan al chocar. Golpe especial: 3 misiles en abanico."),
    dict(id="teledirigido", nombre="Sonda de misil teledirigido", color=(90, 230, 200), arma=5,
         desc="Misiles guiados que buscan su objetivo. Golpe especial: 4 misiles."),
    dict(id="sonda7", nombre="Sonda 7", color=(230, 150, 220), arma=0,
         desc="Arma por diseñar. Por ahora dispara como la básica."),
    dict(id="sonda8", nombre="Sonda 8", color=(250, 240, 120), arma=0,
         desc="Arma por diseñar. Por ahora dispara como la básica."),
]
N_SONDAS = len(SONDAS)

COSTO_NIVEL = {1: 10, 2: 25, 3: 50, 4: 90, 5: 150}      # mineral para subir al nivel 1, 2, 3...
MAX_NIVEL = {"hp": 2, "escudo": 5, "arma": 5}
NOMBRE_STAT = {"hp": "Corazones", "escudo": "Escudo", "arma": "Arma"}
DESC_STAT = {"hp": "+1 corazón por nivel", "escudo": "Absorbe golpes antes del HP",
             "arma": "Más cadencia y daño"}


# ---------------------------------------------------------------- lectura y escritura
def datos(perfil):
    return perfil.extra.setdefault("espacio", {})


def mineral(perfil):
    return int(datos(perfil).get("mineral", 0))


def _lista(perfil, clave):
    return sorted(datos(perfil).get(clave, []))


def componentes(perfil):
    return _lista(perfil, "componentes")


def jefes(perfil):
    return _lista(perfil, "jefes")


def piezas(perfil, n):
    """Fases (1..FASES) cuya pieza ya tienes, del mundo n."""
    return sorted(datos(perfil).get("piezas", {}).get(MUNDOS[n - 1]["id"], []))


def componente_de(n):
    """Componente al que pertenece el mundo n (1 y 2 -> 1, 3 y 4 -> 2, ...)."""
    return (n + 1) // 2


def piezas_componente(perfil, c):
    """Piezas del componente c que ya tienes, numeradas 1..6 (3 del primer mundo y 3 del segundo)."""
    a, b = COMPONENTES[c - 1]["mundos"]
    return sorted([f for f in piezas(perfil, a)] + [f + FASES for f in piezas(perfil, b)])


def tiene_componente(perfil, c):
    return c in componentes(perfil)


def jefe_vencido(perfil, n):
    return n in jefes(perfil)


# ---------------------------------------------------------------- apertura
def mundo_abierto(perfil, n):
    if n == 1:
        return True
    if n % 2 == 0:
        return jefe_vencido(perfil, n - 1)
    return tiene_componente(perfil, componente_de(n - 1))


def fase_abierta(perfil, n, f):
    if not mundo_abierto(perfil, n):
        return False
    return f == 1 or f - 1 in piezas(perfil, n)


def fase_hecha(perfil, n, f):
    return f in piezas(perfil, n)


def jefe_abierto(perfil, n):
    return mundo_abierto(perfil, n) and len(piezas(perfil, n)) == FASES


def rompecabezas_abierto(perfil, c):
    """El componente c se puede armar: sus dos mundos tienen las piezas y los jefes vencidos."""
    a, b = COMPONENTES[c - 1]["mundos"]
    listo = all(len(piezas(perfil, m)) == FASES and jefe_vencido(perfil, m) for m in (a, b))
    return listo and not tiene_componente(perfil, c)


def sonda_desbloqueada(perfil, k):
    return k == 0 or jefe_vencido(perfil, k)


def sonda_elegida(perfil):
    k = int(datos(perfil).get("elegida", 0))
    return k if 0 <= k < N_SONDAS and sonda_desbloqueada(perfil, k) else 0


def elegir_sonda(perfil, k):
    """Elige la sonda k si esta desbloqueada. Devuelve True si se pudo."""
    if not sonda_desbloqueada(perfil, k):
        return False
    datos(perfil)["elegida"] = k
    perfil.guardar()
    return True


# ---------------------------------------------------------------- acciones que guardan progreso
def guardar_pieza(perfil, n, f):
    """Guarda la pieza de la fase f del mundo n. Devuelve True si era nueva."""
    d = datos(perfil)
    tabla = d.setdefault("piezas", {})
    lista = tabla.setdefault(MUNDOS[n - 1]["id"], [])
    nueva = f not in lista
    if nueva:
        lista.append(f)
        lista.sort()
        perfil.guardar()
    return nueva


def guardar_jefe(perfil, n):
    """Marca el jefe del mundo n como vencido. Devuelve True la primera vez (y da el bono)."""
    d = datos(perfil)
    lista = d.setdefault("jefes", [])
    if n in lista:
        return False
    lista.append(n)
    lista.sort()
    d["mineral"] = mineral(perfil) + MINERAL_JEFE * n
    perfil.guardar()
    return True


def instalar_componente(perfil, c):
    """Instala el componente c en la nave nodriza. Devuelve True si se instalo ahora."""
    if not rompecabezas_abierto(perfil, c):
        return False
    d = datos(perfil)
    lista = d.setdefault("componentes", [])
    lista.append(c)
    lista.sort()
    perfil.guardar()
    return True


def marcar_aviso(perfil, n):
    """Pide que el hub avise que el jefe del mundo n ya esta disponible (se gasta al abrir el hub)."""
    datos(perfil)["aviso"] = n
    perfil.guardar()


def pop_aviso(perfil):
    """Devuelve el mundo con aviso pendiente (o None) y lo borra."""
    n = datos(perfil).pop("aviso", None)
    if n is not None:
        perfil.guardar()
    return n


def sumar_mineral(perfil, n):
    d = datos(perfil)
    d["mineral"] = mineral(perfil) + n


# ---------------------------------------------------------------- mejoras de la sonda
def mejoras_sonda(perfil, k):
    sondas = datos(perfil).setdefault("sondas", {})
    return sondas.setdefault(SONDAS[k]["id"], {"hp": 0, "escudo": 0, "arma": 0})


def costo_mejora(perfil, k, stat):
    """Mineral que cuesta subir una mejora de la sonda k. None si ya esta al maximo."""
    nivel = mejoras_sonda(perfil, k)[stat]
    if nivel >= MAX_NIVEL[stat]:
        return None
    return int(round(COSTO_NIVEL[nivel + 1] * (1 + 0.5 * k)))


def subir_mejora(perfil, k, stat):
    """Gasta mineral y sube una mejora. Devuelve True si se pudo."""
    if not sonda_desbloqueada(perfil, k):
        return False
    c = costo_mejora(perfil, k, stat)
    if c is None or mineral(perfil) < c:
        return False
    datos(perfil)["mineral"] = mineral(perfil) - c
    mejoras_sonda(perfil, k)[stat] += 1
    perfil.guardar()
    return True
