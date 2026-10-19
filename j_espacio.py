"""Defensa Espacial: la sonda protege su camino de los meteoritos que vienen desde la derecha.

Cada partida es una fase (30 s de meteoritos, una pieza) o el jefe de un mundo. Los datos viven en espacio_datos.py.
Mundos: los 8 planetas en orden del Sol, de 1 Mercurio a 8 Neptuno.
"""

import math
import random

import pygame

from ajustes import ANCHO, ALTO, VIDAS
from espacio_datos import (COMPONENTES, FASES, JEFE, MUNDOS, N_MUNDOS, SONDAS, SONDA_TAM, componente_de, guardar_jefe,
                           guardar_pieza, marcar_aviso, rompecabezas_abierto,
                           mejoras_sonda, mineral, piezas, sonda_elegida, sumar_mineral)
from nucleo import (Minijuego, aclarar, barra, corazones, escribir, explosion, oscurecer, panel, V2)
import espacio_dataset as AD

# ---------------------------------------------------------------- arte
_BRILLOS = {}
_ROCAS = {}


def _brillo(radio, color):
    """Disco de luz suave (se pinta con suma de colores, asi brilla de verdad)."""
    radio = max(6, int(round(radio / 4.0)) * 4)
    clave = (radio, color)
    s = _BRILLOS.get(clave)
    if s is None:
        d = 2 * radio
        s = pygame.Surface((d, d))
        s.fill((0, 0, 0))
        paso = 1 if radio < 50 else 2
        for k in range(radio, 0, -paso):
            i = (1 - k / radio) ** 1.7
            pygame.draw.circle(s, tuple(int(c * i) for c in color), (radio, radio), k)
        _BRILLOS[clave] = s
    return s


def luz(pantalla, x, y, radio, color, k=1.0):
    k = max(0.0, min(1.0, k))
    q = int(k * 4 + 0.5) / 4.0
    if q <= 0:
        return
    col = tuple(int(c * q) for c in color)
    s = _brillo(radio, col)
    pantalla.blit(s, (int(x - s.get_width() / 2), int(y - s.get_height() / 2)),
                  special_flags=pygame.BLEND_RGB_ADD)


PALETA_ROCA = (((135, 104, 78), (92, 68, 52)), ((142, 140, 146), (98, 96, 106)),
               ((156, 114, 82), (108, 78, 58)), ((118, 108, 102), (80, 72, 70)))


def roca(radio, semilla):
    clave = (radio, semilla)
    s = _ROCAS.get(clave)
    if s is not None:
        return s
    rnd = random.Random(semilla * 977 + radio)
    base, sombra = PALETA_ROCA[semilla % 4]
    d = 2 * radio + 16
    c = d / 2
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    n = 13
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.1, 0.1)
        rr = radio * rnd.uniform(0.8, 1.0)
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    pygame.draw.polygon(s, sombra, pts)
    luzp = [(c + (x - c) * 0.88 - radio * 0.07, c + (y - c) * 0.88 - radio * 0.07) for x, y in pts]
    pygame.draw.polygon(s, base, luzp)
    claro = [(c + (x - c) * 0.5 - radio * 0.2, c + (y - c) * 0.5 - radio * 0.2) for x, y in pts]
    pygame.draw.polygon(s, aclarar(base, 0.22), claro)
    for _ in range(3 + radio // 14):
        a = rnd.uniform(0, 2 * math.pi)
        dist = rnd.uniform(0.0, 0.62) * radio
        cr = max(3, int(radio * rnd.uniform(0.09, 0.2)))
        cx, cy = c + dist * math.cos(a), c + dist * math.sin(a)
        pygame.draw.circle(s, oscurecer(base, 0.38), (int(cx), int(cy)), cr)
        pygame.draw.circle(s, aclarar(base, 0.15), (int(cx - cr * 0.25), int(cy - cr * 0.25)),
                           max(1, int(cr * 0.62)))
    pygame.draw.polygon(s, (52, 38, 34), pts, 3)
    _ROCAS[clave] = s
    return s


def crear_fondo():
    f = pygame.Surface((ANCHO, ALTO))
    for y in range(ALTO):
        k = y / ALTO
        pygame.draw.line(f, (int(6 + 18 * k), int(6 + 10 * k), int(26 + 26 * k)), (0, y), (ANCHO, y))
    for x, y, r, col in ((300, 200, 330, (46, 18, 78)), (980, 330, 380, (14, 40, 84)),
                         (700, 80, 280, (40, 14, 60)), (140, 480, 260, (12, 34, 70))):
        s = _brillo(r, col)
        f.blit(s, (x - r, y - r), special_flags=pygame.BLEND_RGB_ADD)
    return f


# ---------------------------------------------------------------- constantes del juego
DUR_FASE = 30.0              # segundos de meteoritos en cada fase
PIEZA_SEG = 2.8              # cartel de la pieza antes de volver al hub
CADENCIA = 0.38              # segundos entre disparos automaticos (sin mejora de arma)
RAFAGA_CD = 5.0              # recarga del golpe especial
VEL_BALA = 900.0
INVULN = 1.0                 # segundos sin recibir golpe tras un choque
LASER_DUR = 0.6              # rayo automatico de la sonda laser
LASER_LARGO = 1.2            # rayo del golpe especial
MISIL_VEL = 460.0
MISIL_GIRO = 3.2             # radianes por segundo que puede girar un misil guiado
RADIO_EXPLOSION = 70         # area del misil explosivo
PATRONES = ("abanico", "anillo", "rafaga")
TEL = {"abanico": 0.8, "anillo": 0.9, "rafaga": 0.5}     # aviso antes de cada patron

# eventos de extincion (despues del jefe de Neptuno): no son jefes, son una amenaza que avanza despacio
NIVEL_ASTEROIDE = N_MUNDOS * 10 + 5     # asteroide de extincion
NIVEL_AGUJERO = N_MUNDOS * 10 + 6       # agujero negro: jefe final
EVENTO_NIVEL = {NIVEL_ASTEROIDE: "asteroide", NIVEL_AGUJERO: "agujero"}
# vida: cada disparo que le cae baja lo que hace la sonda; cada meteorito (o pedazo) que destruyes baja 1
EVENTO = {
    "asteroide": dict(hp=80, r=190.0, vel=16.0, x0=ANCHO + 300.0),
    "agujero": dict(hp=120, r=200.0, vel=20.0, x0=ANCHO + 300.0),
}
PEDAZOS_POR_GRIETA = 3
GRIETAS = (((-120, -60), (-40, -10), (-60, 40), (20, 80)),        # cada grieta es una linea sobre el cuerpo
           ((60, -120), (30, -40), (90, 0), (70, 70)),
           ((-30, 90), (40, 40), (120, 110)))

# tipo: radio, golpes, puntos, velocidad relativa y probabilidad de soltar 1 mineral
TIPOS = {
    "peq": dict(r=26, hp=1, pts=2, vel=1.0, gota=0.2),
    "med": dict(r=40, hp=2, pts=4, vel=0.8, gota=0.5),
    "gra": dict(r=58, hp=3, pts=6, vel=0.6, gota=1.0),
}


class Espacio(Minijuego):
    """Una fase o un jefe de Defensa Espacial. El nivel es el codigo mundo*10 + fase (la fase JEFE es el jefe).

    La sonda sigue el cursor y dispara sola; el golpe del mando activa su golpe especial.
    Fase: 30 s de meteoritos. Al despejarla se gana una pieza y se vuelve al hub.
    Jefe: patrones de disparo sin meteoritos. Vencerlo abre el rompecabezas del mundo.
    """

    id = "espacio"
    titulo = "Defensa Espacial"
    instruccion = ("La sonda sigue tu mando y dispara sola. Destruye o esquiva los meteoritos. "
                   "Cada fase te da una pieza de la nave nodriza.")
    gesto = "Mueve la sonda; sacude para el golpe especial"
    duracion = None
    NIVEL_MAX = NIVEL_AGUJERO          # incluye los eventos de extincion (asteroide y agujero negro)

    def __init__(self, ctx, nivel=11):
        super().__init__(ctx, nivel)
        perfil = ctx.perfil
        n, f = divmod(self.nivel, 10)
        self.evento_tipo = EVENTO_NIVEL.get(self.nivel)
        if self.evento_tipo:
            n, f = N_MUNDOS, 1                  # los eventos se juegan sobre Neptuno
        elif not (1 <= n <= N_MUNDOS and 1 <= f <= JEFE):
            n, f = 1, 1
        self.n = n
        self.fase = f
        self.jefe_modo = (f == JEFE) and not self.evento_tipo
        self.mundo = MUNDOS[n - 1]
        self.fondo_arriba, self.fondo_abajo = self.mundo["fondo"]
        self.metas = self.calcular_metas()
        self.k = sonda_elegida(perfil)
        self.sonda = SONDAS[self.k]
        self.arma = self.sonda["arma"]      # que arma dispara (la sonda 7 y 8 aun usan la basica)
        self.m = mejoras_sonda(perfil, self.k)
        self.vidas_max = VIDAS + self.mej.vidas_extra() + self.m["hp"]
        self.vidas = self.vidas_max
        self.escudo_max = self.m["escudo"]
        self.escudo = self.escudo_max
        self.dmg = 1 + self.m["arma"] // 2
        self.cad = CADENCIA * (0.88 ** self.m["arma"])
        self.cad_misil = 0.9 * (0.88 ** self.m["arma"])
        self.cad_laser = 1.6 * (0.88 ** self.m["arma"])
        self.sx, self.sy = 260.0, ALTO / 2
        self.pos = V2(self.sx, self.sy)
        self.modo = "evento" if self.evento_tipo else ("boss" if self.jefe_modo else "fase")
        self.t_fase = 0.0
        self.fase_cerrada = False
        self.t_spawn = 1.0
        self.t_pieza = 0.0           # >0 mientras se ve el cartel final
        self.cart = ""
        self.pieza_nueva = False
        self.cadencia = 0.0
        self.rafaga_cd = 0.0
        self.invuln = 0.0
        self.laser_cd = 1.0
        self.laser_t = 0.0
        self.laser_tick = 0.0
        self.balas = []              # x, y, vx, vy, ttl, pierce, ya
        self.misiles = []            # x, y, ang, ttl, dmg, guiado, aoe
        self.balas_enemigas = []
        self.meteoros = []           # tipo, x, y, vx, vy, r, hp, ang, giro, semilla
        self.particulas = []
        if self.evento_tipo:
            self.boss = self._nuevo_evento()
        else:
            self.boss = self._nuevo_boss() if self.jefe_modo else None
        self.derribados = 0
        self.bg = crear_fondo()
        for tipo in TIPOS:
            for s in range(4):
                roca(TIPOS[tipo]["r"], s)
        rnd = random.Random(7)
        self.estrellas_fondo = []    # [x, y, velocidad, radio, color]
        for _ in range(120):
            self.estrellas_fondo.append([rnd.uniform(0, ANCHO), rnd.uniform(0, ALTO),
                                         rnd.choice((25.0, 60.0, 120.0)), rnd.uniform(0.8, 2.2),
                                         rnd.choice(((255, 255, 255), (200, 220, 255), (255, 240, 200)))])

    # ------------------------------------------------------------------ metas y dificultad
    def calcular_metas(self):
        # la base llama a esto antes de decodificar el nivel: se decodifica aqui tambien
        n, f = divmod(self.nivel, 10)
        n = min(max(n, 1), N_MUNDOS)
        jefe = (f == JEFE)
        if f not in range(1, JEFE + 1):         # los eventos (85, 86) se miden como una fase
            f = 1
        mundo = 1 + 0.3 * (n - 1)
        if jefe:
            base = (100, 220, 380)
        else:
            base = (30, 80, 150)
            mundo *= 1 + 0.25 * (max(f, 1) - 1)     # cada fase pide un poco mas
        return tuple(int(x * mundo) for x in base)

    def _velocidad(self):
        extra = 0 if self.jefe_modo else 8 * (self.fase - 1)
        return (95 + extra) * self.mundo["rapidez"] * self.lento

    def _ritmo(self):
        return max(0.6, 1.4 - 0.12 * (self.fase - 1))

    def _tipo_al_azar(self):
        r = random.random()
        p_gra = 0.03 * (self.fase - 1)
        p_med = 0.25 + 0.03 * (self.fase - 1)
        if r < p_gra:
            return "gra"
        if r < p_gra + p_med:
            return "med"
        return "peq"

    def _spawn(self):
        tipo = self._tipo_al_azar()
        info = TIPOS[tipo]
        r = info["r"]
        self.meteoros.append(dict(tipo=tipo, x=ANCHO + r + 10.0, y=random.uniform(130, ALTO - 60),
                                  vx=-self._velocidad() * info["vel"], vy=random.uniform(-18, 18),
                                  r=float(r), hp=info["hp"], ang=random.uniform(0, 360),
                                  giro=random.uniform(-50, 50), semilla=random.randrange(4)))

    def _destruir(self, m):
        info = TIPOS[m["tipo"]]
        self.sumar(info["pts"], m["x"], m["y"] - m["r"], (255, 240, 120))
        if random.random() < info["gota"]:
            sumar_mineral(self.ctx.perfil, 1)
        self.derribados += 1
        if self.modo == "evento":
            self._golpe_evento(1)                 # cada meteorito o pedazo destruido debilita el evento
        self._estallar(m["x"], m["y"], (255, 170, 70), n=12 if m["tipo"] == "peq" else 18)

    def _estallar(self, x, y, color, n=16):
        explosion(self.particulas, x, y, color, n=n, vel_min=90, vel_max=340, vida=0.7,
                  gravedad=260, radio=5)

    # ------------------------------------------------------------------ armas de la sonda
    def _bala(self, ang=0.0, dy=0.0, pierce=1):
        self.balas.append(dict(x=self.sx + 34, y=self.sy + dy, vx=VEL_BALA * math.cos(ang),
                               vy=VEL_BALA * math.sin(ang), ttl=1.3, pierce=pierce, ya=[]))

    def _misil(self, ang=0.0, guiado=True, aoe=False):
        self.misiles.append(dict(x=self.sx + 30, y=self.sy, ang=ang, ttl=3.0,
                                 dmg=2 + self.m["arma"] // 2, guiado=guiado, aoe=aoe))

    def _disparos(self, dt, ctrl):
        self.cadencia -= dt
        self.laser_cd -= dt
        self.laser_tick -= dt
        if self.cadencia <= 0:
            if self.arma == 0:
                self._bala()
                self.cadencia = self.cad
            elif self.arma == 1:
                self._bala(dy=-14)
                self._bala(dy=14)
                self.cadencia = self.cad
            elif self.arma == 2:
                self._bala(pierce=3)
                self.cadencia = self.cad
            elif self.arma == 4:
                self._misil(guiado=False, aoe=True)
                self.cadencia = self.cad_misil
            elif self.arma == 5:
                self._misil(guiado=True)
                self.cadencia = self.cad_misil
            else:
                self.cadencia = self.cad
        if ctrl.golpe and self.rafaga_cd <= 0:
            self.rafaga_cd = RAFAGA_CD
            self.sonidos.reproducir("ok")
            if self.arma == 0:
                for a in (-0.22, -0.11, 0.0, 0.11, 0.22):
                    self._bala(ang=a)
            elif self.arma == 1:
                for i in range(8):
                    self._bala(ang=-0.35 + i * 0.1)
            elif self.arma == 2:
                for a in (-0.1, 0.0, 0.1):
                    self._bala(ang=a, pierce=5)
            elif self.arma == 3:
                self.laser_t = LASER_LARGO
            elif self.arma == 4:
                for a in (-0.2, 0.0, 0.2):
                    self._misil(ang=a, guiado=False, aoe=True)
            else:
                for a in (-0.3, -0.1, 0.1, 0.3):
                    self._misil(ang=a, guiado=True)
        if self.arma == 3:
            if self.laser_cd <= 0 and self.laser_t <= 0:
                self.laser_t = LASER_DUR
                self.laser_cd = self.cad_laser
                self.laser_tick = 0.0
            if self.laser_t > 0:
                self.laser_t -= dt
                if self.laser_tick <= 0:
                    self.laser_tick = 0.1
                    self._dano_laser()

    def _dano_laser(self):
        d = self.dmg
        for m in self.meteoros:
            if m["x"] > self.sx and abs(m["y"] - self.sy) < m["r"] + 9:
                m["hp"] -= d
        b = self.boss
        if b and self._hay_jefe() and b["x"] > self.sx and abs(b["y"] - self.sy) < b["r"] + 9:
            b["hp"] -= d
            b["flash"] = 0.1

    def _objetivo(self, x, y):
        """Lo mas cercano que un misil guiado puede perseguir: un meteorito o el jefe."""
        mejor, dmin = None, 1e18
        for m in self.meteoros:
            if m["hp"] > 0 and m["x"] > x - 30:
                d = (m["x"] - x) ** 2 + (m["y"] - y) ** 2
                if d < dmin:
                    dmin, mejor = d, (m["x"], m["y"])
        b = self.boss
        if b and self._hay_jefe() and b["hp"] > 0:
            d = (b["x"] - x) ** 2 + (b["y"] - y) ** 2
            if d < dmin:
                mejor = (b["x"], b["y"])
        return mejor

    def _golpe_area(self, x, y, dmg):
        """Explosion del misil: dania a todo lo que este dentro del radio."""
        for m in self.meteoros:
            if m["hp"] > 0 and (m["x"] - x) ** 2 + (m["y"] - y) ** 2 < (RADIO_EXPLOSION + m["r"]) ** 2:
                m["hp"] -= dmg
        b = self.boss
        if b and self._hay_jefe() and (b["x"] - x) ** 2 + (b["y"] - y) ** 2 < (RADIO_EXPLOSION + b["r"]) ** 2:
            b["hp"] -= dmg
            b["flash"] = 0.15
        self._estallar(x, y, (255, 150, 60), n=26)

    def _mover_misiles(self, dt):
        vivos = []
        for mi in self.misiles:
            if mi["guiado"]:
                obj = self._objetivo(mi["x"], mi["y"])
                if obj is not None:
                    des = math.atan2(obj[1] - mi["y"], obj[0] - mi["x"])
                    diff = (des - mi["ang"] + math.pi) % (2 * math.pi) - math.pi
                    mi["ang"] += max(-MISIL_GIRO * dt, min(MISIL_GIRO * dt, diff))
            mi["x"] += math.cos(mi["ang"]) * MISIL_VEL * dt
            mi["y"] += math.sin(mi["ang"]) * MISIL_VEL * dt
            mi["ttl"] -= dt
            hit = False
            for m in self.meteoros:
                if m["hp"] > 0 and (mi["x"] - m["x"]) ** 2 + (mi["y"] - m["y"]) ** 2 < (m["r"] + 6) ** 2:
                    hit = True
                    break
            b = self.boss
            if not hit and b and self._hay_jefe() and (mi["x"] - b["x"]) ** 2 + (mi["y"] - b["y"]) ** 2 < (b["r"] + 6) ** 2:
                hit = True
            if hit:
                if mi["aoe"]:
                    self._golpe_area(mi["x"], mi["y"], mi["dmg"])
                else:
                    for m in self.meteoros:
                        if m["hp"] > 0 and (mi["x"] - m["x"]) ** 2 + (mi["y"] - m["y"]) ** 2 < (m["r"] + 6) ** 2:
                            m["hp"] -= mi["dmg"]
                            break
                    else:
                        b["hp"] -= mi["dmg"]
                        b["flash"] = 0.15
                    self._estallar(mi["x"], mi["y"], (255, 160, 60), n=10)
            elif mi["ttl"] > 0 and -40 <= mi["x"] <= ANCHO + 40 and -40 <= mi["y"] <= ALTO + 40:
                vivos.append(mi)
        self.misiles = vivos

    def _hay_jefe(self):
        """Hay un cuerpo grande que recibe disparos: un jefe o un evento de extincion."""
        return self.boss is not None and self.modo in ("boss", "evento")

    # ------------------------------------------------------------------ jefe
    def _nuevo_boss(self):
        return dict(x=ANCHO - 230.0, y=ALTO / 2, r=70.0, hp=float(self.mundo["boss_hp"]),
                    hpmax=float(self.mundo["boss_hp"]), t=0.0, flash=0.0, patron=None, tel=0.0,
                    tel0=1.0, pausa=2.0, orden=0, disparos=0, t_disp=0.0)

    # ------------------------------------------------------------------ eventos de extincion
    def _nuevo_evento(self):
        spec = EVENTO[self.evento_tipo]
        return dict(x=spec["x0"], y=ALTO / 2, r=spec["r"], vel=spec["vel"], tipo=self.evento_tipo,
                    hp=float(spec["hp"]), hpmax=float(spec["hp"]), t=0.0, flash=0.0, etapa=0)

    def _actualizar_evento(self, dt):
        e = self.boss
        e["t"] += dt
        e["flash"] = max(0.0, e["flash"] - dt)
        e["x"] -= e["vel"] * dt                                  # avanza despacio, pero no se detiene
        e["y"] = ALTO / 2 + math.sin(e["t"] * 0.35) * ALTO * 0.12
        # cada cuarto de vida perdido se abre una grieta y suelta pedazos hacia la sonda
        perdido = 1 - max(0.0, e["hp"]) / e["hpmax"]
        etapa = min(len(GRIETAS), int(perdido * (len(GRIETAS) + 1)))
        while e["etapa"] < etapa:
            e["etapa"] += 1
            self._soltar_pedazos(e)

    def _soltar_pedazos(self, e):
        for _ in range(PEDAZOS_POR_GRIETA):
            r = TIPOS["med"]["r"]
            self.meteoros.append(dict(tipo="med", x=e["x"] - e["r"] * 0.8,
                                      y=e["y"] + random.uniform(-e["r"] * 0.5, e["r"] * 0.5),
                                      vx=-random.uniform(140.0, 200.0), vy=random.uniform(-70.0, 70.0),
                                      r=float(r), hp=TIPOS["med"]["hp"], ang=random.uniform(0, 360),
                                      giro=random.uniform(-60, 60), semilla=random.randrange(4)))

    def _golpe_evento(self, d):
        """Un meteorito (o pedazo) destruido o un disparo que cae en el asteroide le baja la vida."""
        self.boss["hp"] -= d
        self.boss["flash"] = 0.12

    def _fin_evento_ganado(self):
        self.ganado = True
        self.sumar(150, ANCHO / 2, 200, (255, 220, 120))
        self.sonidos.reproducir("premio")
        if self.evento_tipo == "asteroide":
            msg = "¡Asteroide de extinción destruido!"
        else:
            msg = "¡Agujero negro vencido! Has llegado al final del viaje."
        self.terminar(msg)

    def _fin_evento_perdido(self):
        self.ganado = False
        name = "asteroide" if self.evento_tipo == "asteroide" else "agujero negro"
        self.terminar(f"El {name} llegó a la sonda. ¡Inténtalo otra vez!")

    def _angulo_a_sonda(self, x, y):
        return math.atan2(self.sy - y, self.sx - x)

    def _tiro_jefe(self, ang, x, y, vel=None):
        vel = vel or (230 + 26 * (self.n - 1))
        self.balas_enemigas.append(dict(x=x, y=y, vx=math.cos(ang) * vel, vy=math.sin(ang) * vel, ttl=7.0))

    def _fuego_abanico(self, b):
        aim = self._angulo_a_sonda(b["x"], b["y"])
        for i in range(7):
            self._tiro_jefe(aim + (i - 3) * 0.14, b["x"], b["y"])

    def _fuego_anillo(self, b):
        off = random.uniform(0, 2 * math.pi)
        hueco = random.randrange(14)
        for i in range(14):
            if i in (hueco, (hueco + 1) % 14):
                continue                      # dos huecos para poder pasar
            self._tiro_jefe(off + i * 2 * math.pi / 14, b["x"], b["y"], vel=200 + 20 * (self.n - 1))

    def _actualizar_boss(self, dt):
        b = self.boss
        b["t"] += dt
        b["flash"] = max(0.0, b["flash"] - dt)
        b["y"] = ALTO / 2 + math.sin(b["t"] * 0.7) * ALTO * 0.26
        b["x"] = ANCHO - 230 + math.sin(b["t"] * 0.4) * 30
        if b["patron"] is None:
            b["pausa"] -= dt
            if b["pausa"] <= 0:
                nombre = PATRONES[b["orden"] % len(PATRONES)]
                b["orden"] += 1
                b["patron"] = nombre
                b["tel"] = b["tel0"] = TEL[nombre]
                b["disparos"] = 0
                b["t_disp"] = 0.0
            return
        if b["tel"] > 0:                      # el jefe carga el patron: se ve venir
            b["tel"] -= dt
            return
        p = b["patron"]
        if p == "abanico":
            self._fuego_abanico(b)
            self._fin_patron()
        elif p == "anillo":
            self._fuego_anillo(b)
            self._fin_patron()
        else:                                 # rafaga: 3 tiros apuntados seguidos
            b["t_disp"] -= dt
            if b["t_disp"] <= 0:
                self._tiro_jefe(self._angulo_a_sonda(b["x"], b["y"]), b["x"], b["y"])
                b["disparos"] += 1
                b["t_disp"] = 0.32
                if b["disparos"] >= 3:
                    self._fin_patron()

    def _fin_patron(self):
        self.boss["patron"] = None
        self.boss["pausa"] = 1.8

    # ------------------------------------------------------------------ fin de la fase o del jefe
    def _pieza_ganada(self):
        self.pieza_nueva = guardar_pieza(self.ctx.perfil, self.n, self.fase)
        if self.pieza_nueva and self.fase == FASES:
            marcar_aviso(self.ctx.perfil, self.n)       # el hub avisa que el jefe ya esta disponible
        self.sonidos.reproducir("premio")
        if not self.pieza_nueva:
            self.cart = f"Ya tenías la pieza {self.fase} de {FASES}."
        elif len(piezas(self.ctx.perfil, self.n)) == FASES:
            self.cart = f"¡Pieza {self.fase} de {FASES}! Ya tienes todas. Vence al jefe para armar el componente."
        else:
            self.cart = f"¡Pieza {self.fase} de {FASES} conseguida!"
        self.t_pieza = PIEZA_SEG

    def _fin_con_mensaje(self):
        self.ganado = True
        self.terminar(self.cart)

    def _toca_sonda(self, x, y, r):
        """Un circulo de radio r en (x, y) toca el area de la sonda: un rectangulo de SONDA_TAM centrado en ella."""
        media_w, media_h = SONDA_TAM[0] / 2, SONDA_TAM[1] / 2
        cx = min(max(x, self.sx - media_w), self.sx + media_w)
        cy = min(max(y, self.sy - media_h), self.sy + media_h)
        return (x - cx) ** 2 + (y - cy) ** 2 < r * r

    def _golpe_sonda(self, x, y):
        self._estallar(x, y, (200, 200, 220), n=12)
        if self.invuln > 0:
            return
        if self.escudo > 0:
            self.escudo -= 1
            self.invuln = 0.3
            self.sonidos.reproducir("tick")
        else:
            self.vidas -= 1
            self.invuln = INVULN
            self.sonidos.reproducir("error")
        if self.vidas <= 0:
            self._perder()

    def _perder(self):
        self.ganado = False
        self.terminar("La sonda se quedó sin energía. ¡Inténtalo otra vez!")

    def _mundo_vencido(self):
        nuevo = guardar_jefe(self.ctx.perfil, self.n)
        self.ganado = True
        self.sumar(60 * self.n, ANCHO / 2, 200, (255, 220, 120))
        self.sonidos.reproducir("premio")
        if nuevo:
            msg = f"¡Jefe de {self.mundo['nombre']} vencido!"
            if self.n < len(SONDAS):
                msg += f" Se abre la sonda {self.n + 1}."
            c = componente_de(self.n)
            if rompecabezas_abierto(self.ctx.perfil, c):
                msg += f" Ya puedes armar el {COMPONENTES[c - 1]['nombre']} en el rompecabezas."
        else:
            msg = f"¡Jefe de {self.mundo['nombre']} vencido otra vez!"
        self.terminar(msg)

    # ------------------------------------------------------------------ ciclo
    def paso(self, dt, ctrl):
        tx = min(max(ctrl.pos.x, 60.0), ANCHO - 60.0)
        ty = min(max(ctrl.pos.y, 120.0), ALTO - 40.0)
        k = min(1.0, dt * 9.0)
        self.sx += (tx - self.sx) * k
        self.sy += (ty - self.sy) * k
        self.pos = V2(self.sx, self.sy)
        self.invuln = max(0.0, self.invuln - dt)
        self.rafaga_cd = max(0.0, self.rafaga_cd - dt)
        self._disparos(dt, ctrl)
        if self.t_pieza > 0:
            self.t_pieza -= dt
            if self.t_pieza <= 0:
                self._fin_con_mensaje()
                return
        elif self.modo in ("fase", "evento") and not self.fase_cerrada:
            self.t_fase += dt
            self.t_spawn -= dt
            if self.t_spawn <= 0:
                self._spawn()
                self.t_spawn = self._ritmo() * random.uniform(0.8, 1.2)
            if self.modo == "fase" and self.t_fase >= DUR_FASE:
                self.fase_cerrada = True
        self._mover(dt)
        if self.terminado:
            return
        if self.modo == "fase" and self.fase_cerrada and not self.meteoros and self.t_pieza <= 0:
            self._pieza_ganada()

    def _mover(self, dt):
        for s in self.estrellas_fondo:
            s[0] -= s[2] * dt
            if s[0] < -4:
                s[0] += ANCHO + 8
                s[1] = random.uniform(0, ALTO)
        if self.boss and self.modo == "boss":
            self._actualizar_boss(dt)
        elif self.boss and self.modo == "evento":
            self._actualizar_evento(dt)
        # disparos de la sonda
        for b in self.balas:
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            b["ttl"] -= dt
        self.balas = [b for b in self.balas if b["ttl"] > 0 and b["x"] < ANCHO + 20 and -20 <= b["y"] <= ALTO + 20]
        self._mover_misiles(dt)
        # tiros del jefe
        for e in self.balas_enemigas:
            e["x"] += e["vx"] * dt
            e["y"] += e["vy"] * dt
            e["ttl"] -= dt
        self.balas_enemigas = [e for e in self.balas_enemigas
                               if e["ttl"] > 0 and -40 <= e["x"] <= ANCHO + 40 and -40 <= e["y"] <= ALTO + 40]
        # meteoritos
        for m in self.meteoros:
            m["x"] += m["vx"] * dt
            m["y"] += m["vy"] * dt
            m["ang"] += m["giro"] * dt
            if m["y"] < 110 or m["y"] > ALTO - 30:
                m["vy"] = -m["vy"]
        # balas de la sonda contra meteoritos (algunas los atraviesan) y jefe
        b_jefe = self.boss if self._hay_jefe() else None
        for b in self.balas:
            for m in self.meteoros:
                if m["hp"] <= 0 or id(m) in b["ya"]:
                    continue
                if (b["x"] - m["x"]) ** 2 + (b["y"] - m["y"]) ** 2 < (m["r"] + 5) ** 2:
                    m["hp"] -= self.dmg
                    b["ya"].append(id(m))
                    b["pierce"] -= 1
                    if b["pierce"] <= 0:
                        b["ttl"] = 0
                        break
            if b["ttl"] > 0 and b_jefe and (b["x"] - b_jefe["x"]) ** 2 + (b["y"] - b_jefe["y"]) ** 2 < (b_jefe["r"] + 6) ** 2:
                b_jefe["hp"] -= self.dmg
                b_jefe["flash"] = 0.15
                b["ttl"] = 0
        self.balas = [b for b in self.balas if b["ttl"] > 0]
        muertos = [m for m in self.meteoros if m["hp"] <= 0]
        self.meteoros = [m for m in self.meteoros if m["hp"] > 0]
        for m in muertos:
            self._destruir(m)
        if b_jefe and b_jefe["hp"] <= 0:
            if self.modo == "evento":
                self._fin_evento_ganado()
            else:
                self._mundo_vencido()
            return
        # choques con la sonda: meteoritos, tiros del jefe y el propio jefe
        for m in list(self.meteoros):
            if self._toca_sonda(m["x"], m["y"], m["r"]):
                self.meteoros = [q for q in self.meteoros if q is not m]
                self._golpe_sonda(m["x"], m["y"])
                if self.terminado:
                    return
        for e in list(self.balas_enemigas):
            if self._toca_sonda(e["x"], e["y"], 10):
                self.balas_enemigas = [q for q in self.balas_enemigas if q is not e]
                self._golpe_sonda(e["x"], e["y"])
                if self.terminado:
                    return
        if b_jefe and self._toca_sonda(b_jefe["x"], b_jefe["y"], b_jefe["r"] * 0.7):
            if self.modo == "evento":
                self._fin_evento_perdido()        # el asteroide o el agujero llegan a la sonda: se pierde la fase
                return
            self._golpe_sonda(self.sx, self.sy)
            if self.terminado:
                return
        self.meteoros = [m for m in self.meteoros if m["x"] > -m["r"] - 20]
        self.particulas = [q for q in self.particulas if q.actualizar(dt)]

    # ------------------------------------------------------------------ dibujo
    def dibujar_juego(self, p):
        negro = self.modo == "evento" and self.evento_tipo == "agujero"
        if negro:
            p.fill((0, 0, 0))                     # escenario final: el fondo es el espacio negro del agujero
        else:
            p.blit(self.bg, (0, 0))
            for s in self.estrellas_fondo:
                pygame.draw.circle(p, s[4], (int(s[0]), int(s[1])), max(1, int(s[3])))
            self._dibujar_planeta(p)
        for m in self.meteoros:
            spr = roca(TIPOS[m["tipo"]]["r"], m["semilla"])
            rot = pygame.transform.rotozoom(spr, m["ang"], 1.0)
            p.blit(rot, rot.get_rect(center=(int(m["x"]), int(m["y"]))))
        if self.boss and self.modo == "evento":
            self._dibujar_evento(p)
        elif self.boss and self.modo == "boss":
            self._dibujar_boss(p)
        for e in self.balas_enemigas:
            luz(p, e["x"], e["y"], 14, (255, 100, 60), 0.9)
            pygame.draw.circle(p, (255, 150, 90), (int(e["x"]), int(e["y"])), 8)
        for b in self.balas:
            ang = math.atan2(b["vy"], b["vx"])
            x2, y2 = b["x"] - math.cos(ang) * 18, b["y"] - math.sin(ang) * 18
            grosor = 7 if b["pierce"] > 1 else 4
            pygame.draw.line(p, (255, 240, 150), (b["x"], b["y"]), (x2, y2), grosor)
            luz(p, b["x"], b["y"], 12, (255, 230, 120), 0.8)
        for mi in self.misiles:
            col = (255, 150, 60) if mi["aoe"] else (120, 255, 180)
            luz(p, mi["x"], mi["y"], 12, col, 0.9)
            pygame.draw.circle(p, (255, 230, 200), (int(mi["x"]), int(mi["y"])), 4)
        if self.arma == 3 and self.laser_t > 0:
            pygame.draw.line(p, (255, 80, 80), (self.sx + 40, self.sy), (ANCHO, self.sy), 12)
            pygame.draw.line(p, (255, 240, 240), (self.sx + 40, self.sy), (ANCHO, self.sy), 3)
        for q in self.particulas:
            q.dibujar(p)
        self._dibujar_sonda(p)
        self._dibujar_interfaz_espacio(p)

    def _dibujar_planeta(self, p):
        cx, cy = 1120, 150
        # tamano relativo al de Jupiter (150 px), con minimo de 40 px para que los pequenos se vean
        diam = max(40, round(150 * AD.ESFERA[self.mundo["id"]] / 480))
        r = diam // 2
        col = self.mundo["planeta"]
        luz(p, cx, cy, r + 100, col, 0.45)
        img = AD.planeta_escalado(self.mundo["id"], diam)
        if img is not None:                              # imagen del dataset (si existe)
            p.blit(img, img.get_rect(center=(cx, cy)))
            return
        if self.mundo.get("anillos"):
            pygame.draw.ellipse(p, (150, 135, 100), (cx - int(r * 1.2), cy - r // 2, int(r * 2.4), r), 6)
        pygame.draw.circle(p, col, (cx, cy), r)
        if self.mundo.get("bandas"):
            for f in (-0.57, -0.29, 0.0, 0.29, 0.57):
                dy = int(r * f)
                hw = int((r * r - dy * dy) ** 0.5) - 2
                pygame.draw.line(p, oscurecer(col, 0.8), (cx - hw, cy + dy), (cx + hw, cy + dy), 4)
        else:
            pygame.draw.circle(p, oscurecer(col, 0.82), (cx - int(r * 0.28), cy + int(r * 0.2)), max(2, int(r * 0.26)))
            pygame.draw.circle(p, oscurecer(col, 0.85), (cx + int(r * 0.36), cy - int(r * 0.3)), max(2, int(r * 0.17)))
        if self.mundo.get("anillos"):
            pygame.draw.arc(p, (170, 155, 118), pygame.Rect(cx - int(r * 1.2), cy - r // 2, int(r * 2.4), r),
                            math.pi, 2 * math.pi, 6)

    def _dibujar_boss(self, p):
        b = self.boss
        col = self.mundo["boss"]
        x, y, r = int(b["x"]), int(b["y"]), b["r"]
        if b["patron"] and b["tel"] > 0:
            self._dibujar_telegrafo(p, b)
        luz(p, x, y, 130, col, 0.55 + 0.45 * b["flash"])
        img = AD.jefe(self.mundo["id"])
        if img is not None:                       # sprite del jefe (jefe_<planeta>.png)
            p.blit(img, img.get_rect(center=(x, y)))
        else:                                     # provisional: esfera con pinchos y ojos
            for i in range(8):
                a = b["t"] * 0.6 + i * math.pi / 4
                tip = (x + math.cos(a) * (r + 26), y + math.sin(a) * (r + 26))
                base1 = (x + math.cos(a + 0.2) * (r - 6), y + math.sin(a + 0.2) * (r - 6))
                base2 = (x + math.cos(a - 0.2) * (r - 6), y + math.sin(a - 0.2) * (r - 6))
                pygame.draw.polygon(p, oscurecer(col, 0.6), [tip, base1, base2])
            pygame.draw.circle(p, oscurecer(col, 0.55), (x, y + 6), int(r))
            pygame.draw.circle(p, col, (x, y), int(r))
            ang = self._angulo_a_sonda(b["x"], b["y"])
            for ex in (x - 24, x + 22):
                pygame.draw.circle(p, (250, 250, 240), (ex, y - 14), 16)
                pygame.draw.circle(p, (30, 20, 30), (int(ex + math.cos(ang) * 6), int(y - 14 + math.sin(ang) * 6)), 7)
            pygame.draw.arc(p, (60, 20, 20), pygame.Rect(x - 26, y + 12, 52, 30), math.pi, 2 * math.pi, 4)
        grietas = int((b["hpmax"] - max(0.0, b["hp"])) / b["hpmax"] * 6)
        for i in range(grietas):
            pygame.draw.line(p, (255, 120, 60), (x - 40 + i * 14, y - 50), (x - 30 + i * 14, y - 10), 3)

    def _dibujar_evento(self, p):
        e = self.boss
        x, y = int(e["x"]), int(e["y"])
        if e["tipo"] == "agujero":
            # sin halo de luz: el fondo tiene que quedar negro. El sprite gira y late
            img = AD.agujero()
            if img is not None:
                img = pygame.transform.rotozoom(img, e["t"] * 20.0, 1 + 0.03 * math.sin(e["t"] * 2.0))
        else:
            img = AD.asteroide()
            if img is not None:
                img = pygame.transform.rotozoom(img, math.sin(e["t"] * 0.3) * 4.0, 1.0)
        if img is not None:
            p.blit(img, img.get_rect(center=(x, y)))
        elif e["tipo"] == "agujero":              # provisional: centro negro con anillo
            pygame.draw.circle(p, (255, 140, 60), (x, y), int(e["r"]), 10)
            pygame.draw.circle(p, (0, 0, 0), (x, y), int(e["r"] * 0.8))
        else:                                     # provisional: roca gigante
            pygame.draw.circle(p, (120, 110, 104), (x, y), int(e["r"]))
            pygame.draw.circle(p, (80, 72, 70), (x, y), int(e["r"]), 6)
        if e["flash"] > 0:
            luz(p, x, y, int(e["r"]), (255, 255, 255), e["flash"] * 3)
        if e["tipo"] == "asteroide":
            for g in GRIETAS[:e["etapa"]]:
                pts = [(x + dx, y + dy) for dx, dy in g]
                pygame.draw.lines(p, (40, 20, 10), False, pts, 7)
                pygame.draw.lines(p, (255, 130, 60), False, pts, 3)

    def _dibujar_telegrafo(self, p, b):
        f = 1 - b["tel"] / max(0.01, b["tel0"])
        x, y = b["x"], b["y"]
        if b["patron"] == "abanico":
            aim = self._angulo_a_sonda(x, y)
            for da in (-0.42, 0.0, 0.42):
                a = aim + da
                pygame.draw.line(p, (255, 220, 120), (x, y), (x + math.cos(a) * 700, y + math.sin(a) * 700), 3)
        elif b["patron"] == "anillo":
            pygame.draw.circle(p, (255, 180, 120), (int(x), int(y)), int(b["r"] + f * 260), 3)
        else:
            pygame.draw.circle(p, (255, 120, 120), (int(self.sx), int(self.sy)), int(60 - 40 * f), 3)

    def _dibujar_sonda(self, p):
        x, y = self.sx, self.sy
        if self.invuln > 0 and int(self.t * 12) % 2:
            return                                     # parpadea tras un golpe
        img = AD.sonda(self.k)
        if img is not None:                            # imagen del dataset (285 x 112)
            p.blit(img, img.get_rect(center=(int(x), int(y))))
            if self.escudo > 0:
                area = pygame.Rect(0, 0, SONDA_TAM[0] + 12, SONDA_TAM[1] + 12)
                area.center = (int(x), int(y))
                luz(p, x, y, 170, (90, 180, 255), 0.4)
                pygame.draw.rect(p, (120, 200, 255), area, 3, border_radius=28)
            return
        flama = 14 + 6 * math.sin(self.t * 40)
        luz(p, x - 26, y, 40, (255, 160, 60), 0.8)
        pygame.draw.polygon(p, (255, 190, 80), [(x - 26, y - 7), (x - 26 - flama, y), (x - 26, y + 7)])
        ala = 40 if self.arma in (1, 4, 5) else 30
        pygame.draw.polygon(p, (70, 90, 140), [(x - 4, y - 6), (x - 22, y - ala), (x - 30, y - ala + 4), (x - 16, y - 2)])
        pygame.draw.polygon(p, (70, 90, 140), [(x - 4, y + 6), (x - 22, y + ala), (x - 30, y + ala - 4), (x - 16, y + 2)])
        nariz = 44 if self.arma in (2, 3) else 34
        cuerpo = [(x + nariz, y), (x - 18, y - 14), (x - 26, y - 6), (x - 26, y + 6), (x - 18, y + 14)]
        pygame.draw.polygon(p, (200, 210, 225), cuerpo)
        pygame.draw.polygon(p, (120, 130, 150), cuerpo, 2)
        pygame.draw.circle(p, (120, 220, 255), (int(x + 8), int(y)), 9)
        pygame.draw.circle(p, (230, 250, 255), (int(x + 5), int(y - 3)), 3)
        if self.arma == 1:
            pygame.draw.line(p, (60, 60, 80), (x + 20, y - 12), (x + 46, y - 12), 4)
            pygame.draw.line(p, (60, 60, 80), (x + 20, y + 12), (x + 46, y + 12), 4)
        elif self.arma == 2:
            pygame.draw.line(p, (90, 220, 255), (x + 20, y), (x + 50, y), 7)
        elif self.arma == 3:
            pygame.draw.circle(p, (255, 80, 80), (int(x + 40), int(y)), 5)
            if self.laser_cd < 0.5 and self.laser_t <= 0:
                luz(p, x + 40, y, 22, (255, 60, 60), 0.9)
        elif self.arma in (4, 5):
            for dy in (-22, 12):
                pygame.draw.rect(p, (90, 96, 110), (x - 14, y + dy, 26, 10), border_radius=3)
                pygame.draw.circle(p, (255, 150, 60) if self.arma == 4 else (120, 255, 180),
                                   (int(x + 12), int(y + dy + 5)), 4)
        if self.escudo > 0:
            luz(p, x, y, 46, (90, 180, 255), 0.5)
            pygame.draw.circle(p, (120, 200, 255), (int(x), int(y)), 40, 3)

    def _dibujar_interfaz_espacio(self, p):
        if self.modo == "evento":
            titulo = "Asteroide de extinción" if self.evento_tipo == "asteroide" else "Agujero negro"
            escribir(p, self.f.grande, titulo, ANCHO / 2, 34, (255, 235, 150))
            b = self.boss
            if b:
                barra(p, (ANCHO / 2 - 260, 66, 520, 14), max(0.0, b["hp"] / b["hpmax"]), color=(240, 80, 80))
        elif self.jefe_modo:
            escribir(p, self.f.grande, f"¡Jefe de {self.mundo['nombre']}!", ANCHO / 2, 34, (255, 235, 150))
            b = self.boss
            if b:
                barra(p, (ANCHO / 2 - 260, 66, 520, 14), max(0.0, b["hp"] / b["hpmax"]), color=(240, 80, 80))
        else:
            escribir(p, self.f.grande, f"{self.mundo['nombre']} · fase {self.fase} de {FASES}", ANCHO / 2, 34,
                     (255, 255, 255))
        corazones(p, self.vidas, self.vidas_max, 30, ALTO - 42, r=16, sep=40)
        for i in range(self.escudo_max):
            col = (120, 200, 255) if i < self.escudo else (60, 70, 90)
            pygame.draw.circle(p, col, (34 + i * 22, ALTO - 80), 8)
            pygame.draw.circle(p, (200, 230, 255), (34 + i * 22, ALTO - 80), 8, 2)
        escribir(p, self.f.chica, self.sonda["nombre"], 30, ALTO - 104, (200, 220, 255), ancla="izq")
        listo = self.rafaga_cd <= 0
        escribir(p, self.f.chica, "Golpe especial listo" if listo else "Golpe especial", ANCHO - 330, ALTO - 94,
                 (255, 240, 170), ancla="izq")
        barra(p, (ANCHO - 330, ALTO - 74, 220, 16), 1 - self.rafaga_cd / RAFAGA_CD, color=(255, 210, 70))
        escribir(p, self.f.normal, f"Mineral: {mineral(self.ctx.perfil)}", ANCHO - 24, ALTO - 42,
                 (180, 230, 255), ancla="der")
        escribir(p, self.f.chica, f"Piezas de {self.mundo['nombre']}: {len(piezas(self.ctx.perfil, self.n))}/{FASES}",
                 ANCHO - 24, ALTO - 16, (220, 220, 240), ancla="der")
        if self.t_pieza > 0:
            panel(p, (ANCHO / 2 - 330, 300, 660, 80), alfa=225)
            escribir(p, self.f.grande, self.cart, ANCHO / 2, 340, (40, 60, 110), contorno=None)
