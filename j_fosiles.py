"""Fósiles: excava la zona del carrito, halla huesos, gemas y reliquias, y revive dinosaurios.

20 grados de dificultad (se desbloquean con la pericia). Cada partida usa la ZONA persistente de
fosiles_datos: el dinosaurio en turno, los huesos que faltan (máximo 3), las gemas y la reliquia.
Se esconde en el terreno exactamente eso, bajo las capas del grado:
  POLVO      (grados 1+)   brocha: se barre moviendo el cursor; con la brocha también se limpia el hueso
                           ya descubierto, muy despacito.
  BARRO      (grados 5+)   cincel pequeño: se raspa con un movimiento lento y controlado (de una pasada
                           real, no vale temblar), o con golpes puntuales.
  ROCAS      (grados 10+)  martillo (golpe fuerte, área mayor, puede agrietar huesos cercanos) o
                           cincel (golpe preciso y lento).
  CRISTALES  (grados 15+)  cincel o martillo, con las estrellas que pide el grado.
Nada se rompe por dejar el cursor quieto: hay que usar la herramienta correcta.
Las herramientas de 1 a 5 estrellas se gastan con el uso (durabilidad) y se fabrican en el Taller.

Los huesos tienen calidad 0..100: si la herramienta va muy rápido sobre un hueso descubierto, o un
golpe cae muy cerca, aparecen grietas (un semáforo avisa: "¡Despacito!"); si llega a 0 se rompe, se
pierde de esa partida y vuelve a aparecer en la zona. La calidad se guarda en
perfil.extra["fosiles"]["calidad"][dino][indice].
Cada hueso, gema o reliquia hallado se guarda al instante. Al terminar: si la zona quedó completa se
cierra (pericia y siguiente zona en 1 a 5 minutos); si no, la zona sigue ahí con capas nuevas.
Laboratorio: con un esqueleto completo y gemas suficientes se rocía el polvo moviendo el cursor hasta
que el dinosaurio revive.

Modo práctica (practica=True, lo usa la aventura): zona falsa, herramientas de prueba infinitas y nada
se guarda.
"""

import math
import random
from collections import deque

import pygame

import arte_paleo
import fosiles_datos as fd
from ajustes import ANCHO, ALTO
from j_fosiles_arte import (CEL, COLS, FILAS, GX0, GY0, GW, GH, BARRA, HERRAMIENTAS, COLOR_CAPA, NOMBRES_CAPA,
                            BotonHerr, Bicho, Bloque, articulo, TextoGrande, Vuelo, crear_cubierta, dibujar_gema, fuente,
                            escribir_c, preparar_pieza, sup_barro, sup_senuelo, texto_necesita)
from nucleo import (Minijuego, Particula, aclarar, barra, estrella, explosion, oscurecer, panel, V2)

PANEL = pygame.Rect(848, 226, 404, 404)
LAB_C = (640, 372)                             # centro del esqueleto en el laboratorio
LAB_ESC = 1.4
LAB_SEG = 5.5                                  # segundos de rociado continuo para llenar la barra
GRACIA = 0.8                                   # s sin dano por movimiento tras descubrir un hueso
TOL_LIMPIEZA = 70                              # px/cuadro maximos que cuentan al limpiar un hueso
NETO_MIN = 26.0                                # px de recorrido real en 0.3 s para que el cincel pequeno raspe
PX_BARRO = 300.0                               # px de raspado para limpiar una celda de barro (1 estrella)
GRADOS_MAX = fd.GRADOS_MAX
# las capas del terreno (nombre de la pila) y la capa de fosiles_datos que les corresponde
CAPA_DE = {"polvo": "polvo", "barro": "barro", "roca": "rocas", "cristal": "cristales"}
RADIO_BROCHA = (40.0, 48.0, 56.0, 64.0, 72.0)
RADIO_CINCELP = (20.0, 23.0, 26.0, 29.0, 32.0)
POT_MARTILLO = (1.0, 1.25, 1.5, 1.8, 2.2)
POT_CINCEL = (0.8, 1.0, 1.2, 1.5, 1.9)
# desgaste (puntos de durabilidad)
COSTO_CELDA_BROCHA = 0.7
COSTO_PX_LIMPIAR = 0.0035
COSTO_PX_RASPAR = 0.008
COSTO_GOLPE = {"martillo": 4.0, "cincel": 3.5, "cincel_pequeno": 2.0}
PISTA_CAPA = {"polvo": "El polvo se barre con la brocha",
              "barro": "El barro se raspa con el cincel pequeño",
              "roca": "Esa roca necesita el martillo o el cincel",
              "cristal": "Ese cristal necesita el cincel o el martillo"}


def parametros(grado):
    """Sensibilidad y densidad del terreno. El grado 1 vale lo que tenia el 'nivel 4' del juego anterior;
    de ahi sube de forma gradual hasta el grado 20 (los umbrales de velocidad se multiplican por
    fosiles_datos.sensibilidad_grado)."""
    g = max(1, min(GRADOS_MAX, int(grado)))
    u = (g - 1) / 19.0

    def L(a, b):
        return a + (b - a) * u
    return dict(
        umbral=580.0 * fd.sensibilidad_grado(g),        # px/s a partir de los que se danan los huesos
        k=L(1.3, 2.0),                                  # dano por segundo al pasarse del umbral
        piso=0,
        hp_roca=(int(round(L(2, 3))), int(round(L(3, 4)))),
        hp_cristal=(int(round(L(2, 3))), int(round(L(3, 5)))),
        sobre=L(0.5, 0.85),                             # probabilidad de que un tesoro este bajo una capa gruesa
        senuelos=int(round(L(1, 6))),
        bichos=int(round(L(2, 4))),
        cerca=L(38, 52),                                # px de un hueso en que un golpe de martillo lo agrieta
        dano_golpe=L(26, 42),
        limp=L(720, 920),                               # px de brocha para limpiar un hueso
        pm=L(1.8, 2.6),                                 # multiplicador de puntos
        gema_fosil=L(0.35, 0.6),
        n_barro=int(round(84 * (0.10 + 0.0107 * (g - 5)))) if g >= 5 else 0,
        n_rocas=int(round(5 + 0.8 * (g - 10))) if g >= 10 else 0,
        n_cristales=int(round(3 + 0.8 * (g - 15))) if g >= 15 else 0,
    )


def calidad_esqueleto(perfil, dino, indices=None):
    """Promedio de la calidad (0..100) de los huesos. Los huesos sin dato valen 100."""
    est = fd.estado(perfil)
    d = est.get("calidad", {}).get(dino, {})
    indices = list(range(fd.huesos_total(dino))) if indices is None else list(indices)
    if not indices:
        return 100
    tot = 0.0
    for i in indices:
        try:
            tot += float(d.get(str(i), 100))
        except (TypeError, ValueError):
            tot += 100.0
    return int(round(tot / len(indices)))


NOMBRES_PIEZA = {
    "craneo": "Cráneo", "mandibula": "Mandíbula", "vertebra": "Vértebra", "vertebra_cola": "Vértebra de la cola",
    "costilla": "Costilla", "diente": "Diente", "colmillo": "Colmillo", "molar": "Molar", "femur": "Fémur",
    "humero": "Húmero", "tibia": "Tibia", "radio": "Radio", "radios": "Radios", "falange": "Falange",
    "garra": "Garra", "pelvis": "Pelvis", "sacro": "Sacro", "omoplato": "Omóplato", "esternon": "Esternón",
    "placa": "Placa", "cresta": "Cresta", "cuerno": "Cuerno", "asta": "Asta", "aleta": "Aleta", "pie": "Pie",
    "mano": "Mano", "metatarso": "Metatarso", "rotula": "Rótula", "pua": "Púa", "gastralia": "Gastralia",
    "chevron": "Chevrón", "atlas": "Atlas", "gola": "Gola", "ala_hueso": "Hueso del ala", "pico": "Pico",
    "rombo": "Rombo de la cola", "vela": "Espina de la vela",
}


def _nombre_hueso(dino, i):
    """Nombre en espanol del hueso numero i (de la pieza que dibuja arte_paleo)."""
    try:
        clave = arte_paleo.nombre_pieza(dino, i)
    except Exception:
        clave = None
    if clave:
        if clave in NOMBRES_PIEZA:
            return NOMBRES_PIEZA[clave]
        partes = clave.split("_")
        for n in range(len(partes), 0, -1):
            if "_".join(partes[:n]) in NOMBRES_PIEZA:
                return NOMBRES_PIEZA["_".join(partes[:n])]
        return clave.replace("_", " ").capitalize()
    nombres = arte_paleo.NOMBRES_HUESOS
    return nombres[i % len(nombres)]


# ====================================================================== el minijuego
class Fosiles(Minijuego):
    """Excavacion por grados (1..20) con brocha, cincel pequeño, martillo y cincel, y laboratorio.

    Mejoras de la ruleta: alcance = brocha y cincel pequeño más grandes y huesos algo más tolerantes;
    potencia = martillo y cincel pegan con más fuerza y en un área mayor; tiempo = más segundos;
    puntos = x2; lento = animaciones más calmadas y huesos algo más tolerantes; vida no se usa.
    """

    id = "fosiles"
    titulo = "Fósiles"
    instruccion = "¡Excava huesos de dinosaurio!"
    gesto = "Barre con la brocha, raspa el barro y golpea las rocas con cuidado"
    duracion = None
    NIVEL_MAX = GRADOS_MAX
    fondo_arriba = (255, 190, 120)
    fondo_abajo = (150, 96, 60)

    def __init__(self, ctx, nivel=1, practica=False):
        self.practica = bool(practica)
        self.perfil = ctx.perfil
        grado = 1 if self.practica else max(1, min(GRADOS_MAX, int(nivel)))
        self.reliquia_id = None
        if self.practica:
            self.zona = dict(dino="velociraptor", mundo=0, faltan=[3, 11], gemas=0, reliquia=None,
                             intentos=0, n=2)
        else:
            self.zona = fd.tick(self.perfil)
            if self.zona is not None:
                self.reliquia_id = fd.sorteo_reliquia(self.perfil, grado)
        super().__init__(ctx, grado)
        self.g = parametros(self.nivel)
        self.capas = fd.capas_grado(self.nivel)
        self.pot = self.mej.mult("potencia")
        self.alc = self.mej.mult("alcance")
        self.umbral = self.g["umbral"] * (1.0 + (self.alc - 1.0) * 0.7) / self.lento
        self.tiempo_exc_total = (45.0 if self.practica else fd.tiempo_grado(self.nivel)) * self.mej.mult("tiempo")
        self.tiempo_exc = self.tiempo_exc_total
        self.fase = "excavacion"
        self.t_fase = 0.0
        self.prev = V2(-500, -500)
        self.ultima_pos = None
        self.particulas = []
        self.vuelos = []
        self.bichos = []
        self.items = []
        self.bloques = {}
        self.barro = {}
        self.pila = {(c, r): ["polvo"] for c in range(COLS) for r in range(FILAS)}
        self.celdas_limpias = 0
        self.celdas_barro = 0
        self.t_pop = 0.0
        self.t_tick = 0.0
        self.t_fin = 0.0
        self.fin_motivo = ""
        self.hall_huesos = 0
        self.hall_gemas = 0
        self.hall_reliquias = 0
        self.hall_rotos = 0
        self.hall_senuelos = 0
        self.calidades = []
        self.dano_por = {}
        self.msg_zona = ""
        self.cierre = None
        self.botin_zona = []
        # herramientas
        self.herr = "brocha"
        self.anim_golpe = 0.0
        self.cd_cincel = 0.0
        self.vs = 0.0
        self.v_inst = 0.0
        self.ratio = 0.0
        self.sobre_hueso = False
        self.cerca_hueso = False
        self.sobre_barro = False
        self.pista = ""
        self.t_pista = 0.0
        self.hist = deque()
        self.acum = {}
        self._sucio = False                # durabilidad gastada sin guardar
        self._t_sucio = 0.0
        self.herr_prueba = {t: {"id": -1 - i, "tipo": t, "est": 1, "dur": 10 ** 6}
                            for i, t in enumerate(HERRAMIENTAS)}
        self.botones = [BotonHerr((30 + i * 206, 620, 198, 58), t) for i, t in enumerate(HERRAMIENTAS)]
        self.botones[0].elegido = True
        self.bloqueadas = {}              # capa -> (herramienta ideal, estrellas) que el jugador no puede usar
        self.avisos = []
        self.t_aviso = 0.0
        # laboratorio
        self.lab_id = None
        self.energia = 0.0
        self.t_rev = 0.0
        self.t_lab_total = 100.0
        self.sin_mover = 0.0
        self.cal_lab = 100
        self.bono_lab = 0
        self.bg_lab = None
        self.bg = self._crear_fondo()
        self.suelo = self._crear_suelo()
        self.cubierta = crear_cubierta()
        self._skel = None
        self._skel_n = -1
        if self.zona is None:
            self.fase = "sinzona"
            self.dino = None
            self.total_huesos = 0
            self.mostrar_n = 0
            self.terminar("No hay zona de excavación lista")
            return
        self.dino = self.zona["dino"]
        self.total_huesos = len(self.zona["faltan"]) if self.practica else fd.huesos_total(self.dino)
        self.mostrar_n = 0 if self.practica else len(fd.huesos_de(self.perfil, self.dino))
        self._preparar_terreno()
        self._revisar_herramientas()
        self._estado_botones()

    # ------------------------------------------------------------------ metas
    def calcular_metas(self):
        g = self.nivel
        pm = 1.8 + 0.8 * (g - 1) / 19.0
        z = getattr(self, "zona", None)
        n = len(z["faltan"]) if z else 2
        gemas = z["gemas"] if z else 0
        esperado = n * 22 * pm + gemas * 8 * pm + 14
        m1 = int(round(14 * pm))
        m3 = max(m1 + 12, int(round(0.88 * esperado)))
        m2 = int(round((m1 + m3) / 2.0))
        return (m1, max(m1 + 4, m2), m3)

    # ------------------------------------------------------------------ herramientas
    def _usable(self, tipo, capa=None):
        """Herramienta que se puede usar para ese tipo (y esa capa): la activa si tiene estrellas
        suficientes o, si no, la mejor que quede. None si no hay."""
        if self.practica:
            return self.herr_prueba[tipo]
        req = fd.estrellas_requeridas(self.nivel, capa) if capa else 1
        h = fd.herramienta_activa(self.perfil, tipo)
        if h is not None and h["est"] >= req:
            return h
        cand = [x for x in fd.herramientas(self.perfil, tipo) if x["dur"] > 0 and x["est"] >= req]
        return max(cand, key=lambda x: (x["est"], x["dur"])) if cand else None

    def _est(self, tipo):
        h = self._usable(tipo)
        return h["est"] if h else 1

    @property
    def radio(self):
        """Radio de la brocha (px)."""
        return RADIO_BROCHA[self._est("brocha") - 1] * self.alc

    def _radio_cincelp(self):
        return RADIO_CINCELP[self._est("cincel_pequeno") - 1] * self.alc

    def _tol_martillo(self):
        return 10.0 + 4.0 * (self._est("martillo") - 1) + 80.0 * (self.pot - 1.0)

    def _gastar(self, tipo, herr, puntos):
        """Gasta durabilidad (acumula las fracciones). Avisa si la herramienta se rompe."""
        if self.practica or herr is None or puntos <= 0:
            return
        self.acum[tipo] = self.acum.get(tipo, 0.0) + puntos
        enteros = int(self.acum[tipo])
        if enteros <= 0:
            return
        self.acum[tipo] -= enteros
        self._sucio = True
        est = herr["est"]
        if fd.gastar_durabilidad(self.perfil, herr, enteros):
            self.sonidos.reproducir("fallo")
            for b in self.botones:
                if b.tipo == tipo:
                    b.rota = 1.5
            otra = fd.herramienta_activa(self.perfil, tipo)
            nom = fd.NOMBRES_HERR[tipo].lower()
            art, o = articulo(tipo)
            estr = "estrella" if est == 1 else "estrellas"
            if otra is not None:
                estr2 = "estrella" if otra["est"] == 1 else "estrellas"
                self._decir(f"¡Se rompió tu {nom} de {est} {estr}! Sigues con otr{o} de {otra['est']} {estr2}", 4.0)
            else:
                self._decir(f"¡Se rompió tu {nom}! Ya no tienes: fabrica {art} nuev{o} en el Taller", 4.5)
            self.perfil.guardar()
            self._revisar_herramientas()

    def _revisar_herramientas(self):
        """Avisa de las capas que el jugador no puede trabajar con lo que tiene."""
        self.bloqueadas = {}
        for capa in self.capas:
            tipos = fd.HERRAMIENTAS_CAPA[capa]
            req = fd.estrellas_requeridas(self.nivel, capa)
            if not any(self._usable(t, capa) for t in tipos):
                self.bloqueadas[capa] = (tipos[0], req)
        self.avisos = [texto_necesita(t, e) for t, e in self.bloqueadas.values()]
        if self.avisos and self.t_aviso <= 0 and self.t < 1.0:
            self.t_aviso = 7.0
        for b in self.bloques.values():
            b.bloqueado = CAPA_DE[b.tipo] in self.bloqueadas

    def elegir_herramienta(self, clave):
        if clave not in HERRAMIENTAS:
            return
        if clave != self.herr:
            self.sonidos.reproducir("click")
        self.herr = clave
        for b in self.botones:
            b.elegido = (b.tipo == clave)

    def herramienta_sugerida(self):
        pend = [it for it in self.items if it["tipo"] in ("hueso", "gema", "reliquia") and not it["hecho"]]
        for it in pend:
            if it["tipo"] == "hueso" and self._expuesto(it):
                return "brocha"
        tapas = {self.pila[q][0] for it in pend for q in it["celdas"] if self.pila[q]}
        if "polvo" in tapas or not tapas:
            return "brocha"
        for tope, h in (("barro", "cincel_pequeno"), ("roca", "martillo"), ("cristal", "cincel")):
            if tope in tapas:
                return h
        return "brocha"

    def _estado_botones(self, dt=0.0):
        """Estrellas, durabilidad y avisos de cada boton de la barra."""
        sug = self.herramienta_sugerida() if self.nivel <= 12 else None
        for b in self.botones:
            h = self._usable(b.tipo)
            b.est = h["est"] if h else 0
            b.infinita = self.practica
            b.frac = (h["dur"] / fd.DURABILIDAD[h["est"]]) if (h and not self.practica) else 1.0
            b.rota = max(0.0, b.rota - dt)
            b.pulso = (b.tipo == sug)

    def _actualizar_botones(self, dt, ctrl):
        self._estado_botones(dt)
        for b in self.botones:
            if b.actualizar(dt, ctrl):
                self.elegir_herramienta(b.tipo)

    # ------------------------------------------------------------------ preparar el terreno
    def _preparar_terreno(self):
        g = self.g
        z = self.zona
        libres = {(c, r) for c in range(COLS) for r in range(FILAS)}

        def colocar(w, h):
            for _ in range(300):
                c = random.randint(0, COLS - w)
                r = random.randint(0, FILAS - h)
                celdas = [(c + i, r + j) for i in range(w) for j in range(h)]
                if all(q in libres for q in celdas):
                    for q in celdas:
                        libres.discard(q)
                    return celdas
            return None

        dino = self.dino
        tesoros = []
        faltan = list(z["faltan"])
        random.shuffle(faltan)
        for k in faltan:
            def dib(s, x, y, e, k=k):
                arte_paleo.dibujar_hueso(s, dino, k, x, y, e)
            cols, filas, esc, sup = preparar_pieza(("hueso", dino, k), dib)
            sup.fill((34, 34, 28, 0), special_flags=pygame.BLEND_RGB_ADD)      # huesos reales: un poco mas claros
            celdas = colocar(cols, filas)
            if celdas:
                tesoros.append(self._item("hueso", celdas, sup=sup, indice=k))
        if self.reliquia_id:
            rid = self.reliquia_id

            def dibr(s, x, y, e):
                arte_paleo.dibujar_reliquia(s, rid, x, y, e)
            cols, filas, esc, sup = preparar_pieza(("rel", rid), dibr)
            celdas = colocar(cols, filas)
            if celdas:
                tesoros.append(self._item("reliquia", celdas, sup=sup, ident=rid))
        for _ in range(int(z["gemas"])):
            celdas = colocar(1, 1)
            if celdas:
                tesoros.append(self._item("gema", celdas))
        self.items.extend(tesoros)
        for _ in range(g["senuelos"]):                          # piedras con forma de hueso
            celdas = colocar(random.choice((1, 2)), 1)
            if celdas:
                it = self._item("senuelo", celdas, semilla=random.randint(0, 9999))
                it["sup"] = sup_senuelo(it["rect"].w, it["rect"].h, it["semilla"])
                self._mascaras(it)
                self.items.append(it)
        for _ in range(g["bichos"]):
            celdas = colocar(1, 1)
            if celdas:
                b = Bicho(celdas[0][0], celdas[0][1], random.choice((0, 1)))
                self.items.append(self._item("bicho", celdas, bicho=b))
        # capas gruesas sobre algunos tesoros (solo con las capas que tiene el grado)
        profundas = [c for c in self.capas if c != "polvo"]
        if profundas:
            for it in tesoros:
                if random.random() < g["sobre"]:
                    capa = random.choice(profundas)
                    cels = list(it["celdas"])
                    for q in random.sample(cels, max(1, len(cels) // 2)):
                        self._poner_capa(q, capa)
        ocupadas = {q for it in self.items for q in it["celdas"]}
        # rocas y cristales sueltos (sin amontonarse), luego manchas de barro
        def hueco(q, usadas):
            return all(abs(q[0] - e[0]) + abs(q[1] - e[1]) >= 2 for e in usadas)
        duros = [q for q, b in self.bloques.items()]
        for capa, n in (("rocas", g["n_rocas"]), ("cristales", g["n_cristales"])):
            if capa not in self.capas:
                continue
            ya = sum(1 for b in self.bloques.values() if CAPA_DE[b.tipo] == capa)
            cand = [(c, r) for c in range(COLS) for r in range(FILAS) if (c, r) not in ocupadas
                    and (c, r) not in self.bloques]
            random.shuffle(cand)
            for q in cand:
                if ya >= n:
                    break
                if hueco(q, duros):
                    self._poner_capa(q, capa)
                    duros.append(q)
                    ya += 1
        if "barro" in self.capas:
            objetivo = g["n_barro"]
            intentos = 0
            while len(self.barro) < objetivo and intentos < 200:
                intentos += 1
                q = (random.randrange(COLS), random.randrange(FILAS))
                tam = random.randint(2, 4)
                for _ in range(tam):
                    if len(self.barro) >= objetivo:
                        break
                    if q not in self.bloques and q not in self.barro:
                        self._poner_capa(q, "barro")
                    dc, dr = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                    q = (min(COLS - 1, max(0, q[0] + dc)), min(FILAS - 1, max(0, q[1] + dr)))
        # lo que no lleva polvo encima queda sin la baldosa de arena
        for (c, r), pl in self.pila.items():
            if "polvo" not in pl:
                self.cubierta.fill((0, 0, 0, 0), (c * CEL, r * CEL, CEL, CEL))

    def _poner_capa(self, q, capa):
        """Pone una capa en la celda q (la pila va de arriba hacia abajo)."""
        c, r = q
        g = self.g
        if capa == "barro":
            if q in self.barro or q in self.bloques:
                return
            self.pila[q] = ["polvo", "barro"] if random.random() < 0.6 else ["barro"]
            self.barro[q] = 1.0
        elif capa == "rocas":
            hp = random.randint(*g["hp_roca"])
            self.bloques[q] = Bloque(c, r, "roca", hp, 100 + c * 7 + r * 13)
            self.pila[q] = ["roca"]
            if "barro" in self.capas and random.random() < 0.3:
                self.pila[q].append("barro")
                self.barro[q] = 1.0
        elif capa == "cristales":
            hp = random.randint(*g["hp_cristal"])
            self.bloques[q] = Bloque(c, r, "cristal", hp, 300 + c * 11 + r * 5)
            self.pila[q] = ["cristal"]
            if "barro" in self.capas and random.random() < 0.3:
                self.pila[q].append("barro")
                self.barro[q] = 1.0

    def _item(self, tipo, celdas, sup=None, **kw):
        cs = [c for c, _ in celdas]
        rs = [r for _, r in celdas]
        rect = pygame.Rect(GX0 + min(cs) * CEL, GY0 + min(rs) * CEL,
                           (max(cs) - min(cs) + 1) * CEL, (max(rs) - min(rs) + 1) * CEL)
        it = dict(tipo=tipo, celdas=celdas, rect=rect, hecho=False, sup=sup, cal=100.0, limp=0.0, visto=False,
                  gracia=0.0, crk={}, film=None, mask=None, perdido=False, mini=None, mini_sil=None, **kw)
        if tipo == "hueso":
            self._mascaras(it)
            it["mini"] = self._mini(sup)
        elif tipo == "reliquia":
            it["mini"] = self._mini(sup)
            sil = pygame.Surface(rect.size, pygame.SRCALPHA)
            arte_paleo.dibujar_reliquia(sil, kw["ident"], rect.w / 2, rect.h / 2, 1.0, True)
            it["mini_sil"] = self._mini(sil)
        return it

    @staticmethod
    def _mini(sup, lado=46):
        r = sup.get_bounding_rect()
        if r.w < 2 or r.h < 2:
            return pygame.Surface((lado, lado), pygame.SRCALPHA)
        rec = sup.subsurface(r).copy()
        f = min(lado / rec.get_width(), lado / rec.get_height(), 1.0)
        return pygame.transform.smoothscale(rec, (max(2, int(rec.get_width() * f)), max(2, int(rec.get_height() * f))))

    @staticmethod
    def _mascaras(it):
        m = pygame.mask.from_surface(it["sup"])
        it["mask"] = m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        it["film"] = m.to_surface(setcolor=(206, 168, 118, 255), unsetcolor=(0, 0, 0, 0))

    def _libre(self, c, r):
        return not self.pila[(c, r)]

    def _expuesto(self, it):
        """Todas las celdas del tesoro sin ninguna capa encima."""
        return all(not self.pila[q] for q in it["celdas"])

    @staticmethod
    def _dist_celda(pos, c, r):
        dx = max(abs(pos.x - (GX0 + c * CEL + CEL / 2)) - CEL / 2, 0.0)
        dy = max(abs(pos.y - (GY0 + r * CEL + CEL / 2)) - CEL / 2, 0.0)
        return math.hypot(dx, dy)

    def _celda_de(self, pos):
        c, r = int((pos.x - GX0) // CEL), int((pos.y - GY0) // CEL)
        return (c, r) if 0 <= c < COLS and 0 <= r < FILAS else None

    def _tope(self, q):
        pl = self.pila.get(q)
        return pl[0] if pl else None

    # ------------------------------------------------------------------ fondos
    def _crear_fondo(self):
        s = pygame.Surface((ANCHO, ALTO))
        horizonte = 175
        for y in range(ALTO):
            if y < horizonte:
                f = y / horizonte
                a, b = (255, 170, 108), (255, 232, 182)
            else:
                f = min(1.0, (y - horizonte) / (ALTO - horizonte))
                a, b = (176, 112, 66), (104, 62, 38)
            pygame.draw.line(s, tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)), (0, y), (ANCHO, y))
        pygame.draw.circle(s, (255, 214, 130), (610, 108), 58)
        pygame.draw.circle(s, (255, 240, 190), (610, 108), 42)
        rnd = random.Random(3)
        for (x0, ancho, alto, col) in ((60, 220, 70, (214, 140, 100)), (330, 160, 48, (222, 152, 108)),
                                       (760, 260, 84, (206, 130, 94)), (1050, 200, 56, (218, 146, 104))):
            pygame.draw.polygon(s, col, [(x0, horizonte + 4), (x0 + 20, horizonte - alto), (x0 + ancho * 0.3, horizonte - alto),
                                         (x0 + ancho * 0.4, horizonte - alto * 0.55), (x0 + ancho * 0.8, horizonte - alto * 0.5),
                                         (x0 + ancho, horizonte + 4)])
        for x in (800, 1130):                              # cactus
            pygame.draw.rect(s, (88, 140, 80), (x, horizonte - 52, 14, 60), border_radius=7)
            pygame.draw.rect(s, (88, 140, 80), (x - 16, horizonte - 34, 10, 22), border_radius=5)
            pygame.draw.rect(s, (88, 140, 80), (x - 16, horizonte - 18, 24, 8), border_radius=4)
            pygame.draw.rect(s, (88, 140, 80), (x + 20, horizonte - 42, 10, 26), border_radius=5)
            pygame.draw.rect(s, (88, 140, 80), (x + 8, horizonte - 22, 20, 8), border_radius=4)
        for k in range(14):                                # estratos de la tierra
            y = horizonte + 10 + k * 42 + rnd.randint(-6, 6)
            col = (150 - k * 5, 94 - k * 3, 56 - k * 2)
            pygame.draw.line(s, col, (0, y), (ANCHO, y + rnd.randint(-10, 10)), rnd.randint(3, 7))
        for _ in range(120):
            x, y = rnd.randint(0, ANCHO), rnd.randint(horizonte + 20, ALTO)
            pygame.draw.ellipse(s, (132, 82, 50), (x, y, rnd.randint(5, 14), rnd.randint(3, 7)))
        marco = pygame.Rect(GX0 - 12, GY0 - 12, GW + 24, GH + 24)      # marco de madera del bloque
        pygame.draw.rect(s, (62, 38, 22), marco.move(0, 6), border_radius=18)
        pygame.draw.rect(s, (134, 86, 48), marco, border_radius=18)
        pygame.draw.rect(s, (176, 120, 70), marco.inflate(-6, -6), 4, border_radius=16)
        banco = BARRA.inflate(8, 4)                                    # banco de herramientas
        pygame.draw.rect(s, (62, 38, 22), banco.move(0, 5), border_radius=20)
        pygame.draw.rect(s, (112, 72, 40), banco, border_radius=20)
        pygame.draw.rect(s, (160, 110, 64), banco.inflate(-6, -6), 3, border_radius=18)
        return s

    def _crear_fondo_lab(self):
        s = pygame.Surface((ANCHO, ALTO))
        for y in range(ALTO):
            f = y / ALTO
            a, b = (30, 26, 70), (92, 58, 130)
            pygame.draw.line(s, tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)), (0, y), (ANCHO, y))
        rnd = random.Random(8)
        for _ in range(70):
            x, y = rnd.randint(0, ANCHO), rnd.randint(0, 470)
            pygame.draw.circle(s, (210, 200, 255), (x, y), rnd.choice((1, 1, 2)))
        for x0, alto in ((70, 150), (130, 100), (1150, 140), (1090, 90), (1210, 70)):    # cristales
            pygame.draw.polygon(s, (130, 100, 220), [(x0 - 22, 590), (x0, 590 - alto), (x0 + 22, 590)])
            pygame.draw.polygon(s, (170, 140, 255), [(x0 - 22, 590), (x0, 590 - alto), (x0 - 2, 590)])
        pygame.draw.ellipse(s, (36, 28, 62), (190, 520, 900, 120))
        pygame.draw.ellipse(s, (96, 76, 138), (190, 506, 900, 120))
        pygame.draw.ellipse(s, (124, 100, 170), (210, 506, 860, 100), 5)
        return s

    def _crear_suelo(self):
        s = pygame.Surface((GW, GH))
        rnd = random.Random(5)
        s.fill((112, 74, 48))
        for k in range(10):
            y = int(k * GH / 9)
            col = [(124, 84, 54), (100, 66, 42), (136, 94, 60), (108, 70, 46)][k % 4]
            pts = [(x, y + int(8 * math.sin(x / 90 + k))) for x in range(0, GW + 40, 40)]
            pygame.draw.polygon(s, col, pts + [(GW, GH), (0, GH)])
        for _ in range(260):
            x, y = rnd.randint(0, GW), rnd.randint(0, GH)
            c = rnd.choice(((90, 58, 38), (138, 98, 66), (76, 50, 34)))
            pygame.draw.ellipse(s, c, (x, y, rnd.randint(4, 12), rnd.randint(3, 8)))
        return s

    # ------------------------------------------------------------------ logica
    def paso(self, dt, ctrl):
        if dt <= 0 or self.fase == "sinzona":
            return
        self.t_fase += dt
        self.t_pop = max(0.0, self.t_pop - dt)
        self.t_tick = max(0.0, self.t_tick - dt)
        self.t_pista = max(0.0, self.t_pista - dt)
        self.t_aviso = max(0.0, self.t_aviso - dt)
        self.anim_golpe = max(0.0, self.anim_golpe - dt)
        self.cd_cincel = max(0.0, self.cd_cincel - dt)
        if self.fase == "excavacion":
            self._paso_excavacion(dt, ctrl)
        elif self.fase == "laboratorio":
            self._paso_lab(dt, ctrl)
        else:
            self._paso_revivida(dt)
        self.particulas = [q for q in self.particulas if q.actualizar(dt)]
        self.prev = V2(ctrl.pos)

    def _decir(self, texto, seg=2.6):
        self.pista, self.t_pista = texto, seg

    def _paso_excavacion(self, dt, ctrl):
        pos = V2(ctrl.pos)
        for b in self.bloques.values():
            b.sacudida = max(0.0, b.sacudida - dt)
        for it in self.items:
            it["gracia"] = max(0.0, it["gracia"] - dt)
        if self.t_fin == 0.0:
            self.tiempo_exc -= dt
            ok_prev = self.prev.x > -400
            mov = self.prev.distance_to(pos) if ok_prev else 0.0
            v = max(float(ctrl.vel), mov / dt)
            self.v_inst = v
            self.vs += (v - self.vs) * min(1.0, dt / 0.18)       # velocidad suavizada: un tiron aislado no cuenta
            self.ratio = self.vs / self.umbral
            self.hist.append((self.t, V2(pos)))
            while self.hist and self.t - self.hist[0][0] > 0.3:
                self.hist.popleft()
            self._actualizar_botones(dt, ctrl)
            if self._sucio:
                self._t_sucio += dt
                if self._t_sucio > 6.0:                          # guarda el desgaste de vez en cuando
                    self._sucio, self._t_sucio = False, 0.0
                    self.perfil.guardar()
            if not BARRA.collidepoint(pos.x, pos.y):
                self._fragilidad(dt, pos)
                if self.herr == "brocha" and mov >= 1.0 and ok_prev:
                    self._barrer(self.prev, pos)
                    self._limpiar_hueso(self.prev, pos, mov, dt)
                elif self.herr == "cincel_pequeno" and mov >= 1.0 and ok_prev:
                    self._raspar(self.prev, pos, mov)
                if ctrl.golpe or ctrl.clic:
                    self._accion(pos)
            else:
                self.sobre_hueso = False
                self.cerca_hueso = False
                self.sobre_barro = False
            self._revisar_items()
            if self.tiempo_exc <= 0 or not self._pendientes():
                self.t_fin = 0.001
                self.fin_motivo = "tiempo" if self.tiempo_exc <= 0 else "todo"
                if self.fin_motivo == "todo":
                    self.sonidos.reproducir("ok")
        else:
            self.t_fin += dt
        self.bichos = [b for b in self.bichos if b.actualizar(dt * self.lento)]
        self.vuelos = [v for v in self.vuelos if self._avanzar_vuelo(v, dt)]
        if self.t_fin > 0 and not self.vuelos and self.t_fin > 1.3:
            self._fin_excavacion()

    def _avanzar_vuelo(self, v, dt):
        vivo = v.actualizar(dt)
        if not vivo and v.al_llegar:
            v.al_llegar()
        return vivo

    def _pendientes(self):
        return [it for it in self.items if it["tipo"] in ("hueso", "gema", "reliquia") and not it["hecho"]]

    # --- fragilidad: la suavidad del movimiento
    def _huesos_cerca(self, pos, alcance):
        """Huesos con alguna celda a la vista a menos de `alcance` px del punto."""
        res = []
        for it in self.items:
            if it["tipo"] != "hueso" or it["hecho"]:
                continue
            if any(self._libre(c, r) and self._dist_celda(pos, c, r) <= alcance for c, r in it["celdas"]):
                res.append(it)
        return res

    def _fragilidad(self, dt, pos):
        h = self.herr
        self.sobre_barro = False
        if h == "martillo":
            alc = max(self.g["cerca"], 34) + 24
            self.cerca_hueso = bool(self._huesos_cerca(pos, alc))
            self.sobre_hueso = False
            return
        self.cerca_hueso = False
        if self._usable(h) is None:
            self.sobre_hueso = False
            return
        alc = {"brocha": self.radio * 0.7, "cincel_pequeno": self._radio_cincelp() * 0.9, "cincel": 14.0}[h]
        sobres = self._huesos_cerca(pos, alc)
        self.sobre_hueso = bool(sobres)
        if h == "cincel_pequeno":
            q = self._celda_de(pos)
            self.sobre_barro = q is not None and self._tope(q) == "barro"
        if not sobres:
            return
        if self.ratio > 0.65:
            self._decir("¡Despacito! Los huesos son frágiles", 1.4)
        if self.ratio > 1.0 and h != "cincel":
            dano = 30.0 * self.g["k"] * min(3.0, self.ratio) * dt
            for it in sobres:
                if it["gracia"] <= 0:                       # recien descubierto: tiempo para reaccionar
                    self._dano_hueso(it, dano, "movimiento")

    def _dano_hueso(self, it, cantidad, causa="movimiento"):
        if it["hecho"] or it["perdido"]:
            return
        self.dano_por[causa] = self.dano_por.get(causa, 0.0) + cantidad
        antes = it["cal"]
        it["cal"] = antes - cantidad
        cx, cy = it["rect"].center
        if it["cal"] <= 0:
            it["cal"] = 0.0
            it["perdido"] = True
            it["hecho"] = True
            self.hall_rotos += 1
            self.sonidos.reproducir("fallo")
            self.flotantes.append(TextoGrande("¡Se rompió!", cx, cy - 40))
            explosion(self.particulas, cx, cy, (240, 230, 203), n=22, vel_min=80, vel_max=300, vida=0.9,
                      gravedad=800, radio=6)
            explosion(self.particulas, cx, cy, (196, 180, 146), n=10, vel_min=40, vel_max=200, vida=0.7,
                      gravedad=600, radio=4)
            self._decir("Se rompió, pero vuelve a aparecer en la zona", 3.5)
            return
        if int(antes / 15) != int(it["cal"] / 15):          # cruzo un escalon: nueva grieta
            self.sonidos.reproducir("error")
            explosion(self.particulas, cx, cy, (120, 90, 60), n=6, vel_min=30, vel_max=120, vida=0.4,
                      gravedad=300, radio=3)

    def _nivel_grietas(self, it):
        return 0 if it["cal"] >= 99.5 else min(6, int((100.0 - it["cal"]) / 15) + 1)

    # --- brocha: barrer el polvo
    def _barrer(self, a, b):
        h = self._usable("brocha", "polvo")
        if h is None:
            self._decir(texto_necesita("brocha", 1), 3.0)
            return
        d = a.distance_to(b)
        n = max(1, int(d / 18))
        nuevas = 0
        rad = self.radio + 8
        for k in range(n + 1):
            q = a.lerp(b, k / n)
            if not (GX0 - rad < q.x < GX0 + GW + rad and GY0 - rad < q.y < GY0 + GH + rad):
                continue
            c0 = max(0, int((q.x - GX0 - rad) // CEL))
            c1 = min(COLS - 1, int((q.x - GX0 + rad) // CEL))
            r0 = max(0, int((q.y - GY0 - rad) // CEL))
            r1 = min(FILAS - 1, int((q.y - GY0 + rad) // CEL))
            for c in range(c0, c1 + 1):
                for r in range(r0, r1 + 1):
                    if self.pila[(c, r)] and self.pila[(c, r)][0] == "polvo":
                        cx, cy = GX0 + c * CEL + CEL / 2, GY0 + r * CEL + CEL / 2
                        if math.hypot(cx - q.x, cy - q.y) <= rad:
                            self._limpiar(c, r)
                            nuevas += 1
        if nuevas:
            if self.t_pop <= 0 and random.random() < 0.5:
                self.sonidos.reproducir("pop")
                self.t_pop = 0.25
            self._gastar("brocha", h, COSTO_CELDA_BROCHA * nuevas)
        # un hueso a la vista pide pasar la brocha despacito
        if self._huesos_cerca(b, self.radio * 0.7) and self.ratio <= 0.65:
            self._decir("Pasa la brocha despacito sobre el hueso", 2.2)

    def _limpiar(self, c, r):
        self.pila[(c, r)].pop(0)
        self.cubierta.fill((0, 0, 0, 0), (c * CEL, r * CEL, CEL, CEL))
        self.celdas_limpias += 1
        if self.celdas_limpias % 4 == 0:
            self.sumar(1)
        x, y = GX0 + c * CEL + CEL / 2, GY0 + r * CEL + CEL / 2
        explosion(self.particulas, x, y, (232, 200, 140), n=5, vel_min=30, vel_max=140, vida=0.5,
                  gravedad=300, radio=4)

    # --- brocha sobre el hueso descubierto: limpiarlo despacito
    def _limpiar_hueso(self, a, b, mov, dt):
        h = self._usable("brocha", "polvo")
        if h is None:
            return
        rad = 22.0 * self.alc
        for it in self.items:
            if it["tipo"] not in ("hueso", "senuelo") or it["hecho"]:
                continue
            if not self._expuesto(it):
                continue
            zona = it["rect"].inflate(rad, rad)
            if not (zona.collidepoint(b.x, b.y) and zona.collidepoint(a.x, a.y)):
                continue
            if self.ratio > 1.0 or mov / dt > self.umbral * 1.15:  # muy rapido: no limpia (y dana)
                continue
            paso = min(mov, TOL_LIMPIEZA)
            it["limp"] = min(1.0, it["limp"] + paso / (self.g["limp"] / (1.0 + 0.12 * (h["est"] - 1))))
            self._gastar("brocha", h, COSTO_PX_LIMPIAR * paso)
            if self.t_tick <= 0:
                self.sonidos.reproducir("tick")
                self.t_tick = 0.14
                explosion(self.particulas, b.x, b.y, (226, 190, 130), n=3, vel_min=20, vel_max=80, vida=0.4,
                          gravedad=200, radio=3)
            if it["limp"] >= 1.0:
                it["hecho"] = True
                cx, cy = it["rect"].center
                if it["tipo"] == "hueso":
                    self._hallar_hueso(it, cx, cy)
                else:
                    self.hall_senuelos += 1
                    self.sonidos.reproducir("pop")
                    self._decir("¡Era solo una piedra con forma de hueso!", 2.8)
                    explosion(self.particulas, cx, cy, (168, 164, 170), n=10, vel_min=40, vel_max=160,
                              vida=0.6, gravedad=500, radio=5)
            return

    # --- cincel pequeno: raspar el barro con movimiento lento y controlado
    def _celdas_barro_cerca(self, p, rad):
        res = []
        for q in self.barro:
            if self._tope(q) == "barro" and self._dist_celda(p, q[0], q[1]) <= rad:
                res.append(q)
        return res

    def _raspar(self, a, b, mov):
        h = self._usable("cincel_pequeno", "barro")
        rad = self._radio_cincelp()
        d = a.distance_to(b)
        n = max(1, int(d / 12))
        cels = set()
        for k in range(n + 1):
            cels.update(self._celdas_barro_cerca(a.lerp(b, k / n), rad))
        if not cels:
            q = self._celda_de(b)
            if q is not None and self._tope(q) == "polvo" and self.barro:
                if self._tiene_barro_debajo(q):
                    self._decir("Primero quita el polvo con la brocha", 2.4)
            return
        if h is None:
            self._decir(texto_necesita("cincel_pequeno", fd.estrellas_requeridas(self.nivel, "barro")), 3.0)
            return
        if self.ratio > 0.95 or self.v_inst > self.umbral * 1.2:
            self._decir("¡Más despacio! Raspa con calma", 1.6)
            return
        ant = None
        for tt, pp in self.hist:
            ant = pp
            break
        neto = ant.distance_to(b) if ant is not None else 0.0
        if neto < NETO_MIN:
            return                                            # temblar en el sitio no raspa
        rate = mov / PX_BARRO * (1.0 + 0.25 * (h["est"] - 1))
        for q in cels:
            self._raspa_celda(q, rate)
        self._gastar("cincel_pequeno", h, COSTO_PX_RASPAR * mov)
        if self.t_tick <= 0:
            self.sonidos.reproducir("tick")
            self.t_tick = 0.12

    def _tiene_barro_debajo(self, q):
        return "barro" in self.pila.get(q, ())

    def _raspa_celda(self, q, cantidad):
        if q not in self.barro or self._tope(q) != "barro":
            return
        self.barro[q] -= cantidad
        x, y = GX0 + q[0] * CEL + CEL / 2, GY0 + q[1] * CEL + CEL / 2
        if random.random() < 0.25:
            explosion(self.particulas, x, y, (120, 84, 54), n=2, vel_min=20, vel_max=90, vida=0.4,
                      gravedad=300, radio=3)
        if self.barro[q] <= 0:
            self.barro.pop(q, None)
            self.pila[q].pop(0)
            self.celdas_barro += 1
            if self.celdas_barro % 2 == 0:
                self.sumar(1)
            explosion(self.particulas, x, y, (120, 84, 54), n=8, vel_min=40, vel_max=180, vida=0.6,
                      gravedad=500, radio=5)
            self.sonidos.reproducir("pop")

    # --- golpes: martillo, cincel y cincel pequeno puntual
    def _accion(self, pos):
        h = self.herr
        if h == "martillo":
            self._accion_martillo(pos)
        elif h == "cincel":
            self._accion_cincel(pos)
        elif h == "cincel_pequeno":
            self._accion_cincelp(pos)
        else:                                                  # brocha: un golpe no hace nada
            q = self._celda_de(pos)
            tope = self._tope(q) if q else None
            if tope and tope != "polvo":
                self._decir(PISTA_CAPA[tope], 2.6)

    def _bloques_cerca(self, pos, tol):
        return [b for b in self.bloques.values() if b.distancia(pos) <= tol and b.hp > 0.01]

    def _atacar(self, h, tipo, pos, tol, tabla, costo):
        """Golpea los bloques cerca del punto con la herramienta h. Devuelve cuantos recibieron dano."""
        golpeados = 0
        gasto_herr = None
        for b in self._bloques_cerca(pos, tol):
            capa = CAPA_DE[b.tipo]
            ht = self._usable(tipo, capa)
            if ht is None:
                ideal = fd.HERRAMIENTAS_CAPA[capa][0]
                self._decir(texto_necesita(ideal, fd.estrellas_requeridas(self.nivel, capa)), 3.2)
                b.sacudida = 0.12
                self.sonidos.reproducir("error")
                continue
            fuerza = tabla[ht["est"] - 1] * self.pot
            if tipo == "cincel" and b.tipo == "cristal":
                fuerza *= 1.25
            self._dano_bloque(b, fuerza)
            golpeados += 1
            gasto_herr = ht
        if gasto_herr is not None:
            self._gastar(tipo, gasto_herr, costo)
        return golpeados

    def _accion_martillo(self, pos):
        self.anim_golpe = 0.25
        if self._usable("martillo") is None:
            self._decir(texto_necesita("martillo", 1), 3.0)
            return
        self._golpe_cerca_hueso(pos)
        n = self._atacar("martillo", "martillo", pos, self._tol_martillo(), POT_MARTILLO, COSTO_GOLPE["martillo"])
        if not n:
            self.sonidos.reproducir("golpe")
            explosion(self.particulas, pos.x, pos.y, (220, 190, 140), n=4, vel_min=20, vel_max=90,
                      vida=0.3, gravedad=200, radio=3)
            q = self._celda_de(pos)
            tope = self._tope(q) if q else None
            if tope in ("polvo", "barro"):
                self._decir(PISTA_CAPA[tope], 2.4)

    def _accion_cincel(self, pos):
        self.anim_golpe = 0.2
        if self._usable("cincel") is None:
            self._decir(texto_necesita("cincel", 1), 3.0)
            return
        if self.cd_cincel > 0:
            return                                             # el cincel es mas lento
        self.cd_cincel = 0.45
        for it in self._huesos_cerca(pos, 18.0):               # golpe preciso, pero con el cursor agitado se pasa
            if self.ratio > 1.2:
                self._dano_hueso(it, 12.0 * self.g["k"] + 4, "cincel")
                self._decir("¡Más suave con el cincel!", 2.2)
        n = self._atacar("cincel", "cincel", pos, 8.0, POT_CINCEL, COSTO_GOLPE["cincel"])
        if not n:
            self.sonidos.nota(900, 0.05, 0.18)
            q = self._celda_de(pos)
            tope = self._tope(q) if q else None
            if tope in ("polvo", "barro"):
                self._decir(PISTA_CAPA[tope], 2.4)

    def _accion_cincelp(self, pos):
        self.anim_golpe = 0.15
        h = self._usable("cincel_pequeno", "barro")
        rad = self._radio_cincelp()
        cels = self._celdas_barro_cerca(pos, rad)
        if not cels:
            q = self._celda_de(pos)
            tope = self._tope(q) if q else None
            if tope and tope != "barro":
                self._decir(PISTA_CAPA[tope] if tope != "polvo" else "Primero quita el polvo con la brocha", 2.4)
            return
        if h is None:
            self._decir(texto_necesita("cincel_pequeno", fd.estrellas_requeridas(self.nivel, "barro")), 3.0)
            return
        for it in self._huesos_cerca(pos, 18.0):
            if self.ratio > 1.2:
                self._dano_hueso(it, 12.0 * self.g["k"] + 4, "cincel")
                self._decir("¡Más suave con el cincel!", 2.2)
        q = min(cels, key=lambda c: self._dist_celda(pos, c[0], c[1]))
        self._raspa_celda(q, 0.5 * (1.0 + 0.15 * (h["est"] - 1)))
        self.sonidos.nota(1300, 0.06, 0.22)
        self._gastar("cincel_pequeno", h, COSTO_GOLPE["cincel_pequeno"])

    def _golpe_cerca_hueso(self, pos):
        cerca = self.g["cerca"]
        for it in self._huesos_cerca(pos, max(cerca, 34)):
            d = min(self._dist_celda(pos, c, r) for c, r in it["celdas"] if self._libre(c, r))
            if cerca > 0 and d <= cerca:                      # mas dano cuanto mas cerca cae el golpe
                self._dano_hueso(it, self.g["dano_golpe"] * (1.0 - d / cerca) + 2.0, "martillo")
                self._decir("¡Ese golpe cayó muy cerca del hueso!", 2.4)
            else:
                self._decir("¡Cuidado, hay un hueso cerca!", 2.0)

    def _dano_bloque(self, b, fuerza):
        b.hp -= fuerza
        b.sacudida = 0.25
        col = (150, 150, 160) if b.tipo == "roca" else (150, 230, 255)
        self.sonidos.reproducir("golpe")
        if b.tipo == "cristal":
            self.sonidos.nota(1500 + 100 * random.randint(0, 3), 0.08, 0.2)
        if b.hp > 0.01:
            explosion(self.particulas, b.centro.x, b.centro.y, col, n=6, vel_min=60, vel_max=200, vida=0.5,
                      gravedad=700, radio=5)
            return
        q = (b.c, b.r)
        self.bloques.pop(q, None)
        self.pila[q].pop(0)
        self.sumar(round((2 if b.tipo == "roca" else 5) * self.g["pm"]), b.centro.x, b.centro.y - 20, (220, 220, 235))
        explosion(self.particulas, b.centro.x, b.centro.y, col, n=14, vel_min=80, vel_max=280, vida=0.7,
                  gravedad=800, radio=6)
        explosion(self.particulas, b.centro.x, b.centro.y, (232, 200, 140), n=8, vel_min=30, vel_max=160,
                  vida=0.6, gravedad=300, radio=4)

    # --- hallazgos
    def _revisar_items(self):
        for it in self.items:
            if it["tipo"] == "bicho":
                if it["hecho"]:
                    continue
                b = it["bicho"]
                if not b.huyendo and self._libre(b.c, b.r):
                    b.huyendo = True
                    self.bichos.append(b)
                    it["hecho"] = True
                continue
            if it["hecho"]:
                continue
            if it["tipo"] in ("hueso", "senuelo"):
                if not it["visto"] and any(self._libre(c, r) for c, r in it["celdas"]):
                    it["visto"] = True
                    it["gracia"] = GRACIA                    # primer vistazo: sin dano un momento
                if it["tipo"] == "hueso" and not it.get("avisado") and self._expuesto(it):
                    it["avisado"] = True
                    self._decir("¡Hueso a la vista! Pasa la brocha despacito", 3.2)
                    self.sonidos.reproducir("pop")
                continue
            if not self._expuesto(it):
                continue
            it["hecho"] = True
            cx, cy = it["rect"].center
            if it["tipo"] == "gema":
                self._hallar_gema(cx, cy)
            else:
                self._hallar_reliquia(it, cx, cy)

    def _hallar_hueso(self, it, cx, cy):
        i = it["indice"]
        cal = int(round(it["cal"]))
        if not self.practica:
            fd.registrar_hueso(self.perfil, self.dino, i)
            est = fd.estado(self.perfil)
            est.setdefault("calidad", {}).setdefault(self.dino, {})[str(i)] = cal
            self.perfil.guardar()
        self.hall_huesos += 1
        self.calidades.append(cal)
        self.sumar(round(self.g["pm"] * (12 + 10 * cal / 100.0)), cx, cy - 30, (255, 240, 150))
        self.sonidos.reproducir("premio")
        self.flotantes.append(TextoGrande(_nombre_hueso(self.dino, i), cx, cy - 66))
        self.flotantes.append(TextoGrande(f"Calidad {cal}%", cx, cy - 96))
        explosion(self.particulas, cx, cy, (255, 240, 190), n=16, vel_min=90, vel_max=300, vida=0.8, gravedad=300)

        def llegada():
            self.mostrar_n += 1
            explosion(self.particulas, PANEL.centerx, PANEL.y + 110, (255, 240, 190), n=14, vel_min=60,
                      vel_max=220, vida=0.7, gravedad=200)
            self.sonidos.reproducir("ok")
        self.vuelos.append(Vuelo(it["sup"], cx, cy, PANEL.centerx, PANEL.y + 110, 0.95, llegada, (1.0, 0.6)))

    def _hallar_gema(self, cx, cy):
        if not self.practica:
            fd.registrar_gema(self.perfil)
            self.perfil.guardar()
        self.hall_gemas += 1
        self.sumar(round(8 * self.g["pm"]), cx, cy - 30, (200, 170, 255))
        self.sonidos.reproducir("moneda")
        explosion(self.particulas, cx, cy, (190, 150, 255), n=14, vel_min=80, vel_max=260, vida=0.7, gravedad=200)
        self.vuelos.append(Vuelo(None, cx, cy, PANEL.x + 40, PANEL.y + 304, 0.8, None, (26, 14)))
        if not self.practica and random.random() < self.g["gema_fosil"] * 0.5:      # botin extra en grados altos
            self.dar("gema_fosil", 1)
            self.flotantes.append(TextoGrande("¡Gema fósil!", cx, cy - 70))

    def _hallar_reliquia(self, it, cx, cy):
        self.hall_reliquias += 1
        nueva = True
        if not self.practica:
            nueva = fd.registrar_reliquia(self.perfil, it["ident"])
            self.perfil.guardar()
        nombre = arte_paleo.RELIQUIAS_INFO.get(it["ident"], (it["ident"], ""))[0]
        self.sumar(round(15 * self.g["pm"]), cx, cy - 30, (255, 240, 150))
        self.sonidos.reproducir("premio")
        self.flotantes.append(TextoGrande("¡Reliquia nueva!" if nueva else "¡Reliquia!", cx, cy - 66))
        self.flotantes.append(TextoGrande(nombre, cx, cy - 96))
        explosion(self.particulas, cx, cy, (255, 240, 190), n=16, vel_min=90, vel_max=260, vida=0.8, gravedad=300)
        self.vuelos.append(Vuelo(it["sup"], cx, cy, PANEL.x + 360, PANEL.y + 250, 0.95, None, (1.0, 0.45)))

    # --- fin de la excavacion
    def _fin_excavacion(self):
        partes = []
        if self.hall_huesos:
            partes.append(f"{self.hall_huesos} hueso" + ("s" if self.hall_huesos > 1 else ""))
        if self.hall_gemas:
            partes.append(f"{self.hall_gemas} gema" + ("s" if self.hall_gemas > 1 else ""))
        if self.hall_reliquias:
            partes.append(f"{self.hall_reliquias} reliquia" + ("s" if self.hall_reliquias > 1 else ""))
        msg = ("Hallaste " + " y ".join(partes) + ".") if partes else "Esta vez no hallaste nada. ¡Sigue intentando!"
        if self.calidades:
            msg += f" Calidad {int(round(sum(self.calidades) / len(self.calidades)))}%."
        if self.practica:
            self.msg_zona = msg + " ¡Ya sabes excavar!"
            self.terminar(self.msg_zona)
            return
        limpio = self.hall_rotos == 0 and (not self.calidades or sum(self.calidades) / len(self.calidades) >= 60)
        self.cierre = fd.cerrar_zona_si_termino(self.perfil, self.nivel, limpio)
        if self.cierre:
            msg += f" ¡Pericia +{self.cierre['xp']}!"
            if self.cierre["grado_nuevo"]:
                msg += f" ¡Grado {self.cierre['grado_nuevo']} desbloqueado!"
            self.botin_zona = fd.sorteo_materiales(self.nivel)
            for mid, n in self.botin_zona:
                self.dar(mid, n)
            if self.botin_zona:
                nombres = ", ".join(fd.MATERIALES[m][0] + (f" x{n}" if n > 1 else "") for m, n in self.botin_zona)
                msg += f" Botín: {nombres}."
            if self.reliquia_id and not self.hall_reliquias:
                msg += " Una reliquia se quedó bajo tierra."
        else:
            fd.reiniciar_zona(self.perfil)
            if self.hall_rotos:
                msg += (" Se rompió 1 hueso." if self.hall_rotos == 1 else f" Se rompieron {self.hall_rotos} huesos.")
            msg += " La zona sigue ahí: vuelve cuando el carrito te avise."
        listo = fd.dino_completo_sin_gemas(self.perfil)
        if listo and fd.dino_para_revivir(self.perfil) is None:
            d, falta = listo
            nombre = arte_paleo.DINOS[d][0]
            msg += f" ¡El {nombre} está completo! Te faltan {falta} gema" + ("s" if falta != 1 else "") + " para revivirlo."
        self._sucio = False
        self.perfil.guardar()
        self.msg_zona = msg
        rev = fd.dino_para_revivir(self.perfil)
        if rev:
            self._iniciar_lab(rev)
            return
        self.terminar(msg)

    # --- laboratorio
    def _iniciar_lab(self, ident):
        self.fase = "laboratorio"
        self.lab_id = ident
        self.t_fase = 0.0
        self.energia = 0.0
        self.sin_mover = 0.0
        self.cal_lab = calidad_esqueleto(self.perfil, ident)
        self.bg_lab = self._crear_fondo_lab()
        self.particulas.clear()
        self.flotantes.clear()
        self.vuelos.clear()
        self.sonidos.reproducir("ok")

    def _zona_lab(self):
        r = pygame.Rect(0, 0, 420 * LAB_ESC, 250 * LAB_ESC)
        r.center = LAB_C
        return r.inflate(60, 60)

    def _paso_lab(self, dt, ctrl):
        pos = V2(ctrl.pos)
        mov = self.prev.distance_to(pos) / dt if self.prev.x > -400 else 0.0
        dentro = self._zona_lab().collidepoint(pos.x, pos.y)
        if dentro and mov > 40:
            ritmo = min(1.0, mov / 450.0)
            self.energia = min(1.0, self.energia + ritmo * dt * self.pot / LAB_SEG)
            self.sin_mover = 0.0
            n = int(2 + 8 * ritmo)
            for _ in range(n):
                q = Particula(pos.x + random.uniform(-14, 14), pos.y + random.uniform(-6, 10),
                              random.choice(((160, 120, 255), (120, 200, 255), (255, 255, 255), (220, 150, 255))),
                              vel_min=20, vel_max=140, vida=random.uniform(0.6, 1.2), gravedad=120, radio=4)
                q.vy -= 40
                self.particulas.append(q)
            if random.random() < 0.1:
                self.sonidos.reproducir("tick")
        else:
            self.sin_mover += dt
        if self.energia >= 1.0:
            self._revivir()
        elif self.t_fase > self.t_lab_total:
            self.terminar("Se acabó el tiempo en el laboratorio. ¡Tus gemas siguen guardadas! " + self.msg_zona)

    def _revivir(self):
        ident = self.lab_id
        if not fd.gastar_polvo_revivir(self.perfil, ident):
            self.terminar("Aún faltan gemas para revivirlo. " + self.msg_zona)
            return
        self.fase = "revivida"
        self.t_rev = 0.0
        self.sonidos.reproducir("rugido")
        self.perfil.guardar()
        self.cal_lab = calidad_esqueleto(self.perfil, ident)
        self.sumar(40, LAB_C[0], LAB_C[1] - 160, (200, 170, 255))
        self.bono_lab = self.sumar(round(30 * self.cal_lab / 100.0 * self.g["pm"]), LAB_C[0] + 150,
                                   LAB_C[1] - 120, (255, 240, 150))
        if self.cal_lab >= 95 and self.nivel >= 3:
            self.dar("gema_fosil", 1)
        self.recompensas.append(("dino", ident))
        for _ in range(3):
            explosion(self.particulas, LAB_C[0] + random.uniform(-120, 120), LAB_C[1] + random.uniform(-80, 60),
                      random.choice(((200, 170, 255), (255, 255, 255), (140, 210, 255))),
                      n=18, vel_min=120, vel_max=420, vida=1.2, gravedad=200, radio=6)

    def _paso_revivida(self, dt):
        self.t_rev += dt
        if 1.0 < self.t_rev < 3.0 and random.random() < 0.25:
            explosion(self.particulas, random.uniform(300, 980), random.uniform(120, 420),
                      random.choice(((255, 220, 90), (255, 140, 200), (120, 220, 255), (170, 255, 150))),
                      n=10, vel_min=80, vel_max=300, vida=0.9, gravedad=400, radio=5)
        if self.t_rev > 4.4:
            nombre = arte_paleo.DINOS[self.lab_id][0]
            self.terminar(f"¡Revivió el {nombre}! Calidad {self.cal_lab}%. Nueva página en tu libro. " + self.msg_zona)

    # ------------------------------------------------------------------ dibujo
    def _medidor(self, p, x, y, ancho, alto=16, dim=False):
        """Semaforo de suavidad: verde (suave), amarillo (con cuidado), rojo (muy rapido)."""
        r = pygame.Rect(int(x), int(y), int(ancho), alto)
        zonas = ((0.0, 0.65, (70, 190, 100)), (0.65, 1.0, (235, 190, 50)), (1.0, 1.5, (226, 70, 70)))
        for a, b, col in zonas:
            if dim:
                col = tuple(int(c * 0.55 + 70) for c in col)
            z = pygame.Rect(r.x + int(r.w * a / 1.5), r.y, int(r.w * (b - a) / 1.5) + 1, r.h)
            pygame.draw.rect(p, col, z, border_radius=alto // 2 if a == 0.0 or b == 1.5 else 0)
        pygame.draw.rect(p, (40, 28, 24), r, 3, border_radius=alto // 2)
        k = min(1.5, max(0.0, self.ratio)) / 1.5
        mx = r.x + r.w * k
        pygame.draw.polygon(p, (255, 255, 255), [(mx, r.y - 2), (mx - 7, r.y - 11), (mx + 7, r.y - 11)])
        pygame.draw.polygon(p, (40, 28, 24), [(mx, r.y - 2), (mx - 7, r.y - 11), (mx + 7, r.y - 11)], 2)
        pygame.draw.line(p, (255, 255, 255), (mx, r.y), (mx, r.bottom), 3)

    def _texto_suavidad(self):
        if self.herr == "martillo":
            return ("¡Golpea lejos del hueso!", (255, 220, 120)) if self.cerca_hueso else ("Golpea con fuerza", (230, 230, 240))
        if self.ratio > 1.0:
            return "¡Despacito!", (255, 120, 110)
        if self.ratio > 0.65:
            return "Con cuidado", (255, 225, 110)
        return "Muy suave", (150, 235, 160)

    def dibujar(self, pantalla):
        """Como Minijuego.dibujar pero sin el degradado de fondo (cada fase pinta el suyo entero)."""
        self.dibujar_juego(pantalla)
        self.dibujar_hud(pantalla)
        for x in self.flotantes:
            x.dibujar(pantalla, self.f.normal)

    def dibujar_hud(self, p):
        super().dibujar_hud(p)
        if self.fase == "excavacion":
            titulo = "Práctica" if self.practica else f"Grado {self.nivel}"
            escribir_c(p, self.f.grande, titulo, 590, 34)
            f = max(0.0, self.tiempo_exc / self.tiempo_exc_total)
            barra(p, (ANCHO - 330, 22, 300, 26), f, color=(255, 190, 60) if self.tiempo_exc > 8 else (240, 80, 80))
            escribir_c(p, self.f.chica, f"{int(max(0, self.tiempo_exc)) + 1} s", ANCHO - 180, 35)
            escribir_c(p, self.f.chica, "Suavidad", 860, 152, ancla="izq")
            txt, col = self._texto_suavidad()
            escribir_c(p, self.f.normal, txt, 1240, 160, color=col, ancla="der")
            self._medidor(p, 860, 176, 250, 18, dim=self.herr == "martillo")

    def dibujar_juego(self, p):
        if self.fase == "sinzona":
            self._dibujar_sin_zona(p)
            return
        if self.fase == "excavacion":
            self._dibujar_excavacion(p)
        else:
            self._dibujar_lab(p)
        for q in self.particulas:
            q.dibujar(p)

    def _dibujar_sin_zona(self, p):
        p.blit(self.bg, (0, 0))
        panel(p, (300, 200, 680, 300), color=(58, 42, 34), alfa=235, borde=(214, 160, 96))
        arte_paleo.dibujar_carrito(p, 640, 320, 1.6, self.t, aviso=False)
        escribir_c(p, self.f.normal, "No hay zona de excavación lista", 640, 440)

    def _dibujar_item_hueso(self, p, it):
        sup = it["sup"]
        pos = sup.get_rect(center=it["rect"].center)
        p.blit(sup, pos)
        film = it["film"]
        alfa = int(205 * (1.0 - it["limp"]))
        if alfa > 4:
            film.set_alpha(alfa)
            p.blit(film, pos)
        niv = self._nivel_grietas(it) if it["tipo"] == "hueso" else 0
        if niv:
            p.blit(self._grietas(it, niv), pos)
        r = it["rect"]
        if it["tipo"] == "hueso" and self._expuesto(it):
            if it["cal"] < 99.5:                                   # integridad del hueso
                col = (90, 210, 110) if it["cal"] > 66 else (250, 200, 50) if it["cal"] > 33 else (236, 72, 72)
                barra(p, (r.x + 6, r.bottom - 12, r.w - 12, 10), it["cal"] / 100.0, color=col,
                      color_fondo=(60, 40, 30), borde=(255, 255, 255))
            if 0 < it["limp"] < 1:
                barra(p, (r.x + 6, r.y + 2, r.w - 12, 10), it["limp"], color=(120, 190, 255),
                      color_fondo=(60, 40, 30), borde=(255, 255, 255))
        elif it["tipo"] == "senuelo" and self._expuesto(it) and 0 < it["limp"] < 1:
            barra(p, (r.x + 6, r.y + 2, r.w - 12, 10), it["limp"], color=(120, 190, 255),
                  color_fondo=(60, 40, 30), borde=(255, 255, 255))

    def _grietas(self, it, nivel):
        if nivel in it["crk"]:
            return it["crk"][nivel]
        w, h = it["sup"].get_size()
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        rnd = random.Random(it["celdas"][0][0] * 31 + it["celdas"][0][1] * 7 + 5)
        for _ in range(nivel):
            x, y = rnd.uniform(0.2, 0.8) * w, rnd.uniform(0.25, 0.75) * h
            ang = rnd.uniform(0, 2 * math.pi)
            pts = [(x, y)]
            for _k in range(6):
                ang += rnd.uniform(-0.9, 0.9)
                x += math.cos(ang) * rnd.uniform(8, 17)
                y += math.sin(ang) * rnd.uniform(8, 17)
                pts.append((x, y))
            pygame.draw.lines(s, (40, 18, 12, 255), False, pts, 5)
            pygame.draw.lines(s, (150, 40, 30, 255), False, pts, 2)
        s.blit(it["mask"], (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        it["crk"][nivel] = s
        return s

    def _dibujar_excavacion(self, p):
        p.blit(self.bg, (0, 0))
        p.blit(self.suelo, (GX0, GY0))
        t = self.t
        for it in self.items:                                   # tesoros bajo las capas
            if it["tipo"] == "bicho":
                if not it["hecho"]:
                    it["bicho"].dibujar(p)
                continue
            if it["hecho"]:
                continue
            if it["tipo"] == "gema":
                cx, cy = it["rect"].center
                dibujar_gema(p, cx, cy, 24, t)
            elif it["tipo"] in ("hueso", "senuelo"):
                self._dibujar_item_hueso(p, it)
            else:
                sup = it["sup"]
                p.blit(sup, sup.get_rect(center=it["rect"].center))
        for q, grosor in self.barro.items():                    # barro (se adelgaza al rasparlo)
            sp = sup_barro(q[0] * 3 + q[1])
            if grosor < 0.99:
                sp = sp.copy()
                sp.set_alpha(int(70 + 185 * max(0.0, grosor)))
            p.blit(sp, (GX0 + q[0] * CEL, GY0 + q[1] * CEL))
        p.blit(self.cubierta, (GX0, GY0))
        for b in self.bloques.values():
            b.dibujar(p, t)
        if "barro" in self.bloqueadas:
            for q in self.barro:
                if self._tope(q) == "barro":
                    self._candado(p, GX0 + q[0] * CEL + CEL - 16, GY0 + q[1] * CEL + 16)
        for b in self.bichos:
            b.dibujar(p)
        for v in self.vuelos:
            q, esc = v.pos()
            if v.dibujo is None:
                dibujar_gema(p, q.x, q.y, esc, t)
            else:
                img = pygame.transform.rotozoom(v.dibujo, v.t * 120, esc)
                p.blit(img, img.get_rect(center=(int(q.x), int(q.y))))
        self._dibujar_aviso_huesos(p)
        self._dibujar_cursor(p)
        self._dibujar_panel(p)
        for b in self.botones:
            b.dibujar(p, self.f.normal, t)
        if self.t_fin > 0:
            txt = "¡Encontraste todo!" if self.fin_motivo == "todo" else "¡Se acabó el tiempo!"
            escribir_c(p, self.f.grande, txt, GX0 + GW / 2, GY0 + GH / 2, color=(255, 240, 150))
        else:
            if self.t_aviso > 0 and self.avisos:
                self._dibujar_aviso_herr(p)
            if self.t_pista > 0 and self.pista:
                escribir_c(p, self.f.normal, self.pista, 640, 704, color=(255, 240, 150))
            else:
                escribir_c(p, self.f.normal, self._consejo(), 640, 704)

    @staticmethod
    def _candado(p, lx, ly):
        pygame.draw.circle(p, (60, 40, 40), (lx, ly), 12)
        pygame.draw.circle(p, (255, 200, 90), (lx, ly), 10)
        pygame.draw.rect(p, (110, 70, 30), (lx - 5, ly - 1, 10, 8), border_radius=2)
        pygame.draw.arc(p, (110, 70, 30), (lx - 4, ly - 8, 8, 10), 0, math.pi, 2)

    def _dibujar_aviso_herr(self, p):
        n = len(self.avisos)
        h = 20 + 34 * n
        r = pygame.Rect(GX0 + 50, GY0 + GH - h - 30, GW - 100, h)
        panel(p, r, color=(60, 40, 30), alfa=225, borde=(255, 200, 90), radio=18)
        for i, txt in enumerate(self.avisos):
            escribir_c(p, fuente(24), txt, r.centerx, r.y + 27 + i * 34, color=(255, 236, 160))

    def _consejo(self):
        return {"brocha": "Brocha: mueve el cursor para barrer el polvo",
                "cincel_pequeno": "Cincel pequeño: raspa el barro despacito, sin temblar",
                "martillo": "Martillo: da un golpe sobre una roca",
                "cincel": "Cincel: golpes precisos y lentos sobre rocas y cristales"}[self.herr]

    def _dibujar_aviso_huesos(self, p):
        """Con el martillo cerca de un hueso descubierto, se marca la zona peligrosa."""
        if self.herr != "martillo" or not self.cerca_hueso or self.t_fin > 0:
            return
        k = 0.5 + 0.5 * math.sin(self.t * 9)
        for it in self.items:
            if it["tipo"] == "hueso" and not it["hecho"] and any(self._libre(c, r) for c, r in it["celdas"]):
                pygame.draw.rect(p, (255, int(90 + 70 * k), 70), it["rect"].inflate(8, 8), 4, border_radius=12)

    def _dibujar_cursor(self, p):
        q = self.ultima_pos
        if q is None or self.t_fin > 0:
            return
        x, y = int(q.x), int(q.y)
        if BARRA.collidepoint(x, y):
            return
        h = self.herr
        ht = self._usable(h)
        est = ht["est"] if ht else 1
        if h == "brocha":
            pygame.draw.circle(p, (255, 255, 255), (x, y), int(self.radio), 3)
            pygame.draw.circle(p, (80, 50, 30), (x, y), int(self.radio) + 3, 1)
            arte_paleo.dibujar_herramienta(p, "brocha", x, y, 0.9, 0, 28)
        elif h == "cincel_pequeno":
            rr = int(self._radio_cincelp())
            pygame.draw.circle(p, (255, 255, 255), (x, y), rr, 3)
            pygame.draw.circle(p, (80, 50, 30), (x, y), rr + 3, 1)
            k = self.anim_golpe / 0.15
            arte_paleo.dibujar_herramienta(p, "cincel_pequeno", x, y - 5 * k, 0.9, 0, 24)
        elif h == "martillo":
            k = self.anim_golpe / 0.25
            pygame.draw.circle(p, (255, 255, 255), (x, y), int(max(14, self._tol_martillo())), 2)
            arte_paleo.dibujar_herramienta(p, "martillo", x, y, 0.95, 0, 38 - 95 * k)
        else:
            pygame.draw.circle(p, (255, 255, 255), (x, y), 12, 2)
            pygame.draw.line(p, (255, 255, 255), (x - 18, y), (x - 8, y), 2)
            pygame.draw.line(p, (255, 255, 255), (x + 8, y), (x + 18, y), 2)
            arte_paleo.dibujar_herramienta(p, "cincel", x + 2 * (self.anim_golpe > 0), y - 6 * (self.anim_golpe / 0.2),
                                           0.95, 0, 22)
        if ht is None:                                           # sin herramienta de este tipo
            pygame.draw.line(p, (230, 60, 60), (x - 14, y - 14), (x + 14, y + 14), 5)
            pygame.draw.line(p, (230, 60, 60), (x + 14, y - 14), (x - 14, y + 14), 5)
        if h in ("brocha", "cincel_pequeno", "cincel"):          # semaforo de suavidad junto al cursor
            ref = self.radio if h == "brocha" else (self._radio_cincelp() if h == "cincel_pequeno" else 30)
            mx = min(max(x - 44, 8), ANCHO - 96)
            my = y + ref + 18
            if my + 12 > BARRA.top - 6:                                # no tapar con la barra de herramientas
                my = y - ref - 70
            activo = self.sobre_hueso or self.sobre_barro
            self._medidor(p, mx, my, 88, 12, dim=not activo)
            if activo and self.ratio > 0.65:
                txt, col = self._texto_suavidad()
                escribir_c(p, self.f.chica, txt, mx + 44, my + 28, color=col)

    # --- panel lateral
    def _sup_esqueleto(self, n):
        if self._skel is None or self._skel_n != n:
            s = pygame.Surface((380, 150), pygame.SRCALPHA)
            frac = n / max(1, self.total_huesos)
            arte_paleo.dibujar_esqueleto(s, self.dino, 190, 78, 0.56, min(1.0, frac), 0.0)
            self._skel, self._skel_n = s, n
        return self._skel

    def _dibujar_panel(self, p):
        panel(p, PANEL, color=(58, 42, 34), alfa=232, borde=(214, 160, 96))
        cx = PANEL.centerx
        nombre = arte_paleo.DINOS[self.dino][0]
        escribir_c(p, self.f.normal, nombre, cx, PANEL.y + 24)
        sk = self._sup_esqueleto(self.mostrar_n)
        p.blit(sk, sk.get_rect(center=(cx, PANEL.y + 108)))
        if self.practica:
            txt = f"Práctica: {self.hall_huesos} de {len(self.zona['faltan'])} huesos"
        else:
            txt = f"Huesos hallados: {self.mostrar_n} de {self.total_huesos}"
        escribir_c(p, fuente(24), txt, cx, PANEL.y + 188, grosor=2)
        # lo que falta en esta zona
        escribir_c(p, fuente(18), "Falta en esta zona", PANEL.x + 16, PANEL.y + 212, ancla="izq", grosor=1,
                 color=(236, 214, 180))
        x = PANEL.x + 40
        for it in self.items:
            if it["tipo"] not in ("hueso", "gema", "reliquia"):
                continue
            y = PANEL.y + 252
            hecho = it["hecho"] and not it["perdido"]
            if it["tipo"] == "gema":
                dibujar_gema(p, x, y, 15, self.t, brillo=not hecho)
                if hecho:
                    self._marca(p, x, y, (110, 230, 130))
            else:
                img = it["mini"] if (it["tipo"] == "hueso" or hecho) else it["mini_sil"]
                if it["perdido"] or hecho:
                    img = img.copy()
                    img.set_alpha(110 if hecho else 70)
                p.blit(img, img.get_rect(center=(x, y)))
                if hecho:
                    self._marca(p, x, y, (110, 230, 130))
                elif it["perdido"]:
                    self._marca(p, x, y, (240, 90, 90), x_roja=True)
            x += 56
        # gemas para revivir
        y = PANEL.y + 296
        dibujar_gema(p, PANEL.x + 34, y, 16, self.t)
        costo = fd.costo_revivir(self.dino) if not self.practica else 4
        escribir_c(p, fuente(22), f"Gemas {self.perfil.polvo} de {costo}", PANEL.x + 62, y - 2, ancla="izq", grosor=2,
                 color=(220, 200, 255))
        for i in range(min(costo, 14)):
            lleno = i < self.perfil.polvo
            px, py = PANEL.x + 232 + i * 11, y - 2
            pygame.draw.circle(p, (150, 110, 240) if lleno else (96, 84, 110), (px, py), 5)
            pygame.draw.circle(p, (255, 255, 255) if lleno else (140, 128, 150), (px, py), 5, 1)
        # grado y capas
        escribir_c(p, fuente(22), "Práctica" if self.practica else f"Grado {self.nivel} de {GRADOS_MAX}",
                 PANEL.x + 16, PANEL.y + 336, ancla="izq", grosor=2)
        x = PANEL.x + 16
        y = PANEL.y + 372
        for capa in self.capas:
            col = COLOR_CAPA[capa]
            bloqueada = capa in self.bloqueadas
            req = fd.estrellas_requeridas(self.nivel, capa)
            nombre = NOMBRES_CAPA[capa]
            f = fuente(16)
            extra = 22 if (req > 1 or bloqueada) else 0
            w = f.size(nombre)[0] + 16 + extra
            r = pygame.Rect(x, y - 15, w, 30)
            pygame.draw.rect(p, oscurecer(col, 0.35), r, border_radius=10)
            pygame.draw.rect(p, (240, 80, 80) if bloqueada else aclarar(col, 0.3), r, 3, border_radius=10)
            escribir_c(p, f, nombre, r.x + 8, y, ancla="izq", grosor=1)
            if extra:
                estrella(p, r.right - 20, y, 6, (255, 214, 70), (150, 100, 20))
                escribir_c(p, fuente(14), str(req), r.right - 8, y + 1, ancla="der", grosor=1)
            x += w + 6

    @staticmethod
    def _marca(p, x, y, color, x_roja=False):
        if x_roja:
            pygame.draw.line(p, color, (x - 12, y - 12), (x + 12, y + 12), 4)
            pygame.draw.line(p, color, (x + 12, y - 12), (x - 12, y + 12), 4)
        else:
            pygame.draw.lines(p, color, False, [(x - 10, y), (x - 3, y + 8), (x + 12, y - 9)], 5)

    # --- laboratorio
    def _dibujar_lab(self, p):
        p.blit(self.bg_lab, (0, 0))
        t = self.t
        ident = self.lab_id
        nombre = arte_paleo.DINOS[ident][0]
        cx, cy = LAB_C
        if self.fase == "laboratorio":
            arte_paleo.dibujar_esqueleto(p, ident, cx, cy, LAB_ESC, 1.0, self.energia)
            escribir_c(p, self.f.grande, f"¡Revive al {nombre}!", 640, 34 + 4 * math.sin(t * 3))
            escribir_c(p, self.f.normal, "Mueve el cursor sobre el esqueleto para rociar el polvo especial", 640, 84)
            escribir_c(p, self.f.normal, f"Calidad del esqueleto: {self.cal_lab}%", 640, 124,
                     color=self._color_calidad(self.cal_lab))
            barra(p, (340, 650, 600, 34), self.energia, color=(170, 120, 255), color_fondo=(50, 40, 90),
                  borde=(255, 255, 255))
            escribir_c(p, self.f.normal, "Polvo mágico", 640, 636, ancla="centro")
            if self.sin_mover > 2.5 and self.energia < 1:
                dx = math.sin(t * 4) * 90
                escribir_c(p, self.f.grande, "¡Muévelo de lado a lado!", 640 + dx * 0.2, 610, color=(255, 240, 150))
        else:
            tr = self.t_rev
            if tr < 0.8:
                arte_paleo.dibujar_esqueleto(p, ident, cx, cy, LAB_ESC, 1.0, 1.0)
            else:
                subir = max(0.0, 1.0 - (tr - 0.8) / 0.9)
                esc = 1.25 * (0.9 + 0.1 * min(1.0, (tr - 0.8) / 0.5))
                arte_paleo.dibujar_dino(p, ident, cx, cy + 20 + 60 * subir * subir, esc, t)
            if 0.5 < tr:
                a = max(0.0, 1.0 - abs(tr - 0.8) / 0.9)
                if a > 0:
                    vel = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                    vel.fill((255, 255, 255, int(255 * a)))
                    p.blit(vel, (0, 0))
            if tr > 1.0:
                escribir_c(p, self.f.grande, f"¡Revivió el {nombre}!", 640, 84, color=(255, 240, 150))
                escribir_c(p, self.f.normal, f"Calidad del esqueleto: {self.cal_lab}%   Bono +{self.bono_lab}", 640, 128,
                         color=self._color_calidad(self.cal_lab))
            if tr > 1.6:
                escribir_c(p, self.f.grande, "Nueva página en tu libro", 640, 640, color=(200, 255, 220))
        dibujar_gema(p, 60, 140, 22, t)                          # gemas disponibles
        escribir_c(p, self.f.normal, f"{self.perfil.polvo}", 96, 140, ancla="izq", color=(220, 200, 255))

    @staticmethod
    def _color_calidad(cal):
        return (150, 235, 160) if cal >= 70 else (255, 225, 110) if cal >= 40 else (255, 130, 120)

    def actualizar(self, dt, ctrl):
        self.ultima_pos = V2(ctrl.pos)
        super().actualizar(dt, ctrl)
