"""Horda Elemental: sobrevive a oleadas de criaturas del Tamagotchi con el elemento que elijas.

Caminas con el puntero (o la espada) hacia donde apuntas, desde el centro de la pantalla. Disparas solo al
enemigo mas cercano. Al subir de nivel eliges una mejora entre tres tarjetas. A las 2000 derrotas aparece el
dragon: lanza ataques que se ven venir (anillo, rafaga y embestida). Esquivalos.
"""

import math
import random

import pygame

import arte_tama as AT
import horda_arte as A
import horda_datos as D
import horda_mapa as M
import tama_datos as TD
from ajustes import ANCHO, ALTO
from nucleo import Minijuego, barra, corazones, escribir, estrella, explosion

DWELL = 0.9                  # s con el puntero encima de una carta para elegirla
INTER_CD = 2.5               # s de carga del intermedio (se multiplica por la mejora "carga")
AVISO_ULT = 0.8              # s de aviso antes de que caiga el ultimate
VEL_EMPUJE = 260.0           # px/s con que huye un enemigo empujado
VEL_BOSS = 45.0              # px/s del dragon cuando se acerca
BOSS_VIDA = 150
BOSS_ALTO = 170
BOSS_R = 44
MAX_ENEMIGOS = 100          # depuracion: 100 enemigos. Al final subir a 2000
# radio con el que el heroe choca con arboles y rocas: igual que el enemigo mas chico.
# Asi el heroe no entra a huecos donde los enemigos no caben (y no queda a salvo ahi).
RADIO_CHOQUE_HEROE = 17
# corazones que recuperan 1 vida: muy de vez en cuando
PROB_CORAZON = 0.004         # al derrotar un enemigo comun
PROB_CORAZON_RARO = 0.25     # al derrotar uno de muchos disparos (vida >= 5)
MAX_CORAZONES = 3            # como mucho en el suelo a la vez
# tiradores: disparan balas LINEALES (no persiguen): se esquivan moviendose
VEL_TIRO = 230.0             # px/s
CADA_TIRO = 2.8              # s entre disparos (con un poco de variacion)
ALCANCE_TIRO = 950.0         # px: solo disparan si el heroe esta cerca
# dragon final: ataques con carga. Durante la carga queda quieto y marca la zona (se puede esquivar)
JEFE_CARGA = {"melee": 1.2, "meteoros": 1.3, "rayo": 1.4}
JEFE_DIST_ATAQUE = 520.0     # px: desde aqui empieza a atacar
JEFE_PAUSA = 2.2             # s de descanso entre ataques
VEL_EMBESTIDA = 520.0        # px/s
VEL_RAYO = 1400.0            # px/s con que avanza el rayo
LARGO_RAYO = 1300.0
ANCHO_RAYO = 56.0
OLA_INI = 3.0               # s antes de la primera horda
ESPECIES_HORDA = [e for e in AT.ESPECIES if e != "dragon"]
STUN = ("aturdido", "congelado", "paralizado")
EFECTO_DE = {"agua": "mojado", "viento": "empujado", "tierra": "aturdido",
             "fuego": "quemado", "hielo": "congelado", "electrico": "paralizado"}
CX, CY = ANCHO / 2, ALTO / 2
RAMA_ICONO = {"basico": "basico", "intermedio": "inter", "ultimate": "ulti"}


class Horda(Minijuego):
    id = "horda"
    titulo = "Horda Elemental"
    instruccion = ("Elige tu elemento. Camina con el puntero y dispara solo al mas cercano. "
                   "Sube de nivel para mejorar tus ataques y llega a 2000 derrotas para enfrentar al dragon.")
    gesto = "Mueve el puntero para caminar"
    duracion = None
    NIVEL_MAX = 1
    fondo_arriba = (120, 200, 150)
    fondo_abajo = (200, 235, 190)

    def calcular_metas(self):
        return (5000, 12000, 20500)

    def __init__(self, ctx, nivel=1, semilla=None):
        super().__init__(ctx, nivel)
        self.rng = random.Random(semilla)
        self.fase = "elegir"          # elegir -> jugar <-> subida
        self.tipo = None
        self.hab = None
        self.st = None
        self.g = M.generar(seed=self.rng.randint(1, 99999))
        self.mapa = A.MapaVisto(self.g)
        self.hx, self.hy = M.ANCHO_MUNDO / 2, M.ALTO_MUNDO / 2
        self.mirar = 1
        # la vida de la mascota decide cuantos corazones empiezas (como en la batalla del Tamagotchi)
        self.vidas = max(1, round(D.VIDA * TD.hp_frac(ctx.perfil)))
        self.final = None
        self.dano_hecho = 0
        self.hp_guardada = None
        self.hp_frac = 1.0
        self.invuln = 0.0
        self.derrotas = 0
        self.enemigos = []
        self.flujo, self.flujo_t = None, 0.0   # campo de distancia hacia el heroe (se recalcula)
        self._calc = None                      # calculo del campo en curso (se reparte entre cuadros)
        self.corazones = []                    # corazones en el suelo: dict(x, y)
        self.solo_jefe = False                 # al aparecer el dragon, solo quedan el y el heroe
        self.amenazas = []                     # ataques del dragon: circulos y rayos con carga
        self.proys = []
        self.balas = []
        self.zonas = []
        self.parts = []
        self.cartas = []
        self.ola_t = OLA_INI
        self.boss_visto = False
        self.boss = None
        self.cd_basico = self.cd_inter = self.cd_ult = 0.0
        self.dwell_i = None
        self.dwell = 0.0
        self.aviso = ""
        self.aviso_t = 0.0
        self.cam = (0.0, 0.0)
        self._camara()

    # ------------------------------------------------------------ utilidades
    def _s(self, x, y):
        """Mundo -> pantalla."""
        return x - self.cam[0], y - self.cam[1]

    def _avisar(self, texto, dur=1.8):
        self.aviso, self.aviso_t = texto, dur

    def _limitar(self, x, y):
        return min(max(x, 40.0), M.ANCHO_MUNDO - 40.0), min(max(y, 40.0), M.ALTO_MUNDO - 40.0)

    def _punto_alrededor(self, dist):
        a = self.rng.uniform(0, 2 * math.pi)
        return self._limitar(self.hx + math.cos(a) * dist, self.hy + math.sin(a) * dist)

    def _dist_borde(self, a):
        """Distancia desde el heroe hasta el borde del mapa en la direccion a."""
        dx, dy = math.cos(a), math.sin(a)
        t = 1e9
        if dx > 1e-6:
            t = min(t, (M.ANCHO_MUNDO - self.hx) / dx)
        elif dx < -1e-6:
            t = min(t, -self.hx / dx)
        if dy > 1e-6:
            t = min(t, (M.ALTO_MUNDO - self.hy) / dy)
        elif dy < -1e-6:
            t = min(t, -self.hy / dy)
        return t

    def _punto_fuera(self, a):
        """Punto FUERA del mapa, en la direccion a desde el heroe. Ahi nacen los enemigos
        (nunca en el centro de la pantalla) y caminan hacia el heroe."""
        dx, dy = math.cos(a), math.sin(a)
        t = self._dist_borde(a) + 40 + self.rng.uniform(0, 80)
        return self.hx + dx * t, self.hy + dy * t

    def _camara(self):
        self.cam = (min(max(self.hx - CX, 0), M.ANCHO_MUNDO - ANCHO),
                    min(max(self.hy - CY, 0), M.ALTO_MUNDO - ALTO))

    def _explosion(self, x, y, color, n):
        sx, sy = self._s(x, y)
        explosion(self.parts, sx, sy, color, n=n)

    def _etapa(self):
        return 1 + min(2, self.derrotas // 80)

    def _nuevo_enemigo(self, especie, etapa, x, y, jefe=False):
        alto = BOSS_ALTO if jefe else 46 + 10 * etapa
        vida = BOSS_VIDA if jefe else D.vida_enemigo(self.derrotas, self.rng)
        return dict(especie=especie, etapa=etapa, x=x, y=y, alto=alto,
                    r=BOSS_R if jefe else alto * 0.3, vida=vida, vmax=vida,
                    est={}, quem=0.0, jefe=jefe,
                    pat=None, pat_t=2.5, tel=0.0, dash=0.0, dash_dir=(1.0, 0.0))

    def _herir(self, e, dano):
        self.dano_hecho += max(0, min(dano, e["vida"]))
        e["vida"] -= dano

    def _efecto(self, e, nombre, dur):
        e["est"][nombre] = max(e["est"].get(nombre, 0.0), dur)

    def _golpe_heroe(self):
        self.vidas -= 1
        self.invuln = D.INVULN
        self.sonidos.reproducir("golpe")
        self._explosion(self.hx, self.hy, (255, 90, 110), 10)

    def _proyectil(self, ang, r, dano, pen, vel, ttl, efecto, inter):
        self.proys.append(dict(tipo=self.tipo, x=self.hx, y=self.hy, ang=ang,
                               vx=math.cos(ang) * vel, vy=math.sin(ang) * vel,
                               r=r, dano=dano, pen=pen, ttl=ttl, efecto=efecto,
                               dur=self.st["efecto"], inter=inter, tocados=set()))

    def _objetivo(self):
        mejor, md = None, D.ALCANCE
        for e in self.enemigos:
            d = math.hypot(e["x"] - self.hx, e["y"] - self.hy)
            if d <= md:
                mejor, md = e, d
        return mejor

    def _rects_tipos(self):
        return [pygame.Rect(int(CX + (i % 3 - 1) * 340 - 150), 190 + (i // 3) * 250, 300, 220) for i in range(6)]

    def _rects_cartas(self):
        return [pygame.Rect(int(CX + (i - 1) * 370 - 160), 250, 320, 320) for i in range(3)]

    def _pulsada(self, rects, dt, ctrl):
        """Indice de la carta elegida (clic o puntero quieto DWELL s encima), o None."""
        idx = None
        for i, r in enumerate(rects):
            if r.collidepoint(ctrl.pos.x, ctrl.pos.y):
                idx = i
                break
        if idx is None:
            self.dwell_i, self.dwell = None, 0.0
            return None
        if idx != self.dwell_i:
            self.dwell_i, self.dwell = idx, 0.0
        self.dwell += dt
        if ctrl.clic or self.dwell >= DWELL:
            self.dwell_i, self.dwell = None, 0.0
            return idx
        return None

    # ------------------------------------------------------------ ciclo
    def terminar(self, mensaje=""):
        if self.final is None and not self.terminado:
            # salida sin acabar la pelea: se guarda la vida y se da la recompensa de huida
            self._finalizar("escapa", "¡Huyeron a salvo!")
            return
        if not self.terminado:
            ext = self.ctx.perfil.extra
            ext["horda_mejor"] = max(ext.get("horda_mejor", 0), self.derrotas)
        super().terminar(mensaje)

    def _finalizar(self, res, mensaje):
        """Fin de la pelea: guarda la vida de la mascota y da la recompensa del Tamagotchi (una sola vez)."""
        self.final = res
        self.hp_frac = max(0.0, self.vidas / D.VIDA)
        piso = TD.HP_PISO_DERROTA if res == "pierde" else 0.01
        self.hp_guardada = TD.guardar_hp(self.ctx.perfil, self.hp_frac, piso=piso)
        self.ganado = res == "gana"
        info = TD.recompensa_batalla(self.ctx.perfil, res, self.dano_hecho, self.hp_frac, rng=self.rng)
        for item, n in info.get("items", {}).items():
            self.ctx.perfil.quitar(item, n)
            self.dar(item, n)
        self.resultado = dict(estado=res, xp=int(info.get("xp", 0)), monedas=int(info.get("monedas", 0)),
                              items=dict(info.get("items", {})), dano_hecho=int(self.dano_hecho),
                              hp_frac=round(self.hp_frac, 3), hp_guardado=self.hp_guardada)
        self.terminar(mensaje)

    def paso(self, dt, ctrl):
        if self.aviso_t > 0:
            self.aviso_t -= dt
        if self.fase == "elegir":
            i = self._pulsada(self._rects_tipos(), dt, ctrl)
            if i is not None:
                self.tipo = D.TIPOS[i]
                self.hab = D.Habilidades(self.tipo)
                self.st = self.hab.stats()
                self.fase = "jugar"
                self._avisar("¡Que empiece la horda!", 2.0)
            return
        if self.fase == "subida":
            self._paso_subida(dt, ctrl)
            return
        self._paso_jugar(dt, ctrl)

    def _paso_subida(self, dt, ctrl):
        i = self._pulsada(self._rects_cartas(), dt, ctrl)
        if i is None:
            return
        carta = self.cartas[i]
        if not carta["ok"]:
            self._avisar(carta["motivo"] or "Esa mejora todavia no esta disponible", 1.8)
            return
        self.hab.aplicar(carta)
        self.st = self.hab.stats()
        self._avisar(f"¡{carta['nombre']}!", 1.4)
        self._cerrar_subida()

    def _cerrar_subida(self):
        if self.hab.puntos_disponibles(self.derrotas) > 0 and not self.hab.completo():
            self.cartas = self.hab.opciones(self.rng)
        else:
            self.cartas = []
            self.fase = "jugar"

    def _paso_jugar(self, dt, ctrl):
        self.invuln = max(0.0, self.invuln - dt)
        self._mover_heroe(dt, ctrl)
        self._camara()
        self._disparar(dt)
        self._spawn(dt)
        self._actualizar_enemigos(dt)
        self._actualizar_jefe(dt)
        self._actualizar_amenazas(dt)
        self._actualizar_proyectiles(dt)
        self._actualizar_zonas(dt)
        self._actualizar_balas(dt)
        self._recoger()
        self._muertes()
        self.parts = [q for q in self.parts if q.actualizar(dt)]
        if self.terminado:
            return
        if self.vidas <= 0:
            self._finalizar("pierde", "La horda te ha superado")
            return
        if self.hab.puntos_disponibles(self.derrotas) > 0 and not self.hab.completo():
            self.cartas = self.hab.opciones(self.rng)
            self.fase = "subida"
            self.dwell_i, self.dwell = None, 0.0

    # ------------------------------------------------------------ heroe
    def _mover_heroe(self, dt, ctrl):
        dx, dy = ctrl.pos.x - CX, ctrl.pos.y - CY
        d = math.hypot(dx, dy)
        if d <= D.ZONA_MUERTA:
            return
        self.mirar = 1 if dx >= 0 else -1
        f = min(1.0, (d - D.ZONA_MUERTA) / 160.0)
        k = D.VEL_HEROE * f * M.velocidad_en(self.g, self.hx, self.hy) * dt / d
        self.hx, self.hy = M.mover(self.g, self.hx, self.hy, dx * k, dy * k, RADIO_CHOQUE_HEROE)

    def _disparar(self, dt):
        st = self.st
        self.cd_basico -= dt
        self.cd_inter -= dt
        self.cd_ult -= dt
        if not st["inter_on"]:
            self.cd_inter = INTER_CD
        if not st["ult_on"]:
            self.cd_ult = self.rng.uniform(*st["ult_intervalo"])
        obj = self._objetivo()
        if obj is not None:
            ang = math.atan2(obj["y"] - self.hy, obj["x"] - self.hx)
            if self.cd_basico <= 0:
                self.cd_basico = st["cadencia"]
                self._proyectil(ang, st["radio"], st["dano"], st["pen"], D.VEL_PROY, D.DUR_PROY, None, False)
                self.sonidos.reproducir("lanzar")
            if st["inter_on"] and self.cd_inter <= 0:
                self.cd_inter = INTER_CD * st["carga"]
                self._proyectil(ang, st["radio_i"], st["dano_i"], 1, D.VEL_INTER, D.DUR_INTER,
                                EFECTO_DE[self.tipo], True)
                self.sonidos.reproducir("lanzar")
        if st["ult_on"] and self.cd_ult <= 0:
            self.cd_ult = self.rng.uniform(*st["ult_intervalo"])
            x, y = self._punto_ultimate()
            r = D.ULT_RADIO[D.TIPOS.index(self.tipo)] * st["radio_u"]
            self.zonas.append(dict(tipo=self.tipo, x=x, y=y, r=r, fase="aviso", t=0.0, u=0.0,
                                   dano=st["dano_u"], efecto=EFECTO_DE[self.tipo], dur=st["efecto"]))

    def _punto_ultimate(self):
        cerca = [e for e in self.enemigos if math.hypot(e["x"] - self.hx, e["y"] - self.hy) < 420]
        if cerca:
            e = self.rng.choice(cerca)
            return e["x"], e["y"]
        a = self.rng.uniform(0, 2 * math.pi)
        d = self.rng.uniform(120, 260)
        return self._limitar(self.hx + math.cos(a) * d, self.hy + math.sin(a) * d)

    # ------------------------------------------------------------ enemigos
    def _spawn(self, dt):
        if D.jefe_aparece(self.derrotas, self.boss_visto):
            # evento final: solo el dragon y el heroe en todo el mapa
            self.boss_visto = True
            self.solo_jefe = True
            self.enemigos = []
            a = self.rng.uniform(0, 2 * math.pi)
            x, y = self._limitar(self.hx + math.cos(a) * 900, self.hy + math.sin(a) * 900)
            x, y = M.libre_cerca(self.g, x, y, BOSS_R, self.rng, radio=200)
            self.boss = self._nuevo_enemigo("dragon", 3, x, y, jefe=True)
            self.enemigos.append(self.boss)
            self._avisar("¡Aparece el dragón!", 2.6)
        if self.solo_jefe:
            return
        self.ola_t -= dt
        if self.ola_t > 0:
            return
        self.ola_t = D.intervalo_ola(self.derrotas) * (1.5 if self.boss else 1.0)
        self._horda()

    def _horda(self):
        """Una horda: muchas criaturas a la vez, llegando todas desde el mismo lado."""
        # de 8 lados al azar, usa el mas cercano al heroe: las hordas nacen un poco mas cerca
        lado = min((self.rng.uniform(0, 2 * math.pi) for _ in range(8)), key=self._dist_borde)
        for _ in range(D.tamano_ola(self.derrotas)):
            if len(self.enemigos) >= MAX_ENEMIGOS:
                break
            x, y = self._punto_fuera(lado + self.rng.uniform(-0.6, 0.6))
            self.enemigos.append(self._nuevo_enemigo(self.rng.choice(ESPECIES_HORDA), self._etapa(), x, y))
        self._avisar("¡Horda!", 0.8)

    def _actualizar_enemigos(self, dt):
        g = self.g
        if self._calc is None and (self.flujo_t <= 0 or self.flujo is None):
            self._calc = M.campo_flujo_iter(g, int(self.hx // M.TAM), int(self.hy // M.TAM))
            self.flujo_t = 0.4
        if self._calc is not None:
            try:
                for _ in range(3):              # un trozo del calculo por cuadro
                    next(self._calc)
            except StopIteration as fin:
                self.flujo, self._calc = fin.value, None
        self.flujo_t -= dt
        self._asignar_tiradores()
        for e in self.enemigos:
            est = e["est"]
            for k in list(est):
                est[k] -= dt
                if est[k] <= 0:
                    del est[k]
            if "quemado" in est:
                e["quem"] += dt
                if e["quem"] >= 1.0:
                    e["quem"] -= 1.0
                    self._herir(e, 1)
            if self.invuln <= 0 and math.hypot(self.hx - e["x"], self.hy - e["y"]) < D.RADIO_HEROE + e["r"]:
                self._golpe_heroe()
            if e["jefe"]:
                continue
            if any(k in est for k in STUN):
                continue
            if e.get("tira"):                      # tirador: bala lineal hacia donde esta el heroe ahora
                e["tiro"] -= dt
                if e["tiro"] <= 0:
                    e["tiro"] = CADA_TIRO * self.rng.uniform(0.9, 1.2)
                    ddx, ddy = self.hx - e["x"], self.hy - e["y"]
                    dd = math.hypot(ddx, ddy)
                    if 0 < dd <= ALCANCE_TIRO:
                        self.balas.append(dict(x=e["x"], y=e["y"], vx=ddx / dd * VEL_TIRO,
                                               vy=ddy / dd * VEL_TIRO, r=7, ttl=4.0))
            dx, dy = self.hx - e["x"], self.hy - e["y"]
            d = math.hypot(dx, dy)
            if d <= 1:
                continue
            if "empujado" in est:
                sentido, velo = -1.0, VEL_EMPUJE
            else:
                sentido = 1.0
                velo = D.vel_enemigo(self.derrotas) * (0.5 if "mojado" in est else 1.0)
            paso = velo * M.velocidad_en(g, e["x"], e["y"]) * dt
            if sentido > 0:
                e["x"], e["y"] = self._seguir(e["x"], e["y"], paso, e["r"])
            else:
                v = paso * sentido / d
                e["x"], e["y"] = M.mover(g, e["x"], e["y"], dx * v, dy * v, e["r"], borde=False)

    def _seguir(self, x, y, paso, r):
        """Un paso hacia el heroe por el camino del mapa (campo de distancia).
        Todo movimiento pasa por M.mover: nunca atraviesa arboles ni rocas."""
        g, TAM = self.g, M.TAM
        dentro = 0 <= x < M.ANCHO_MUNDO and 0 <= y < M.ALTO_MUNDO
        if dentro and M.choca(g, x, y, r, False):
            # quedo pegado a un arbol (caso raro): se saca con el menor desplazamiento posible
            x, y = M.libre_cerca(g, x, y, r, self.rng, radio=60)
        if not dentro or self.flujo is None:
            # fuera del mapa: va hacia la entrada libre mas cercana del borde, sin atravesar nada
            ex, ey = self._entrada(x, y)
            ang = math.atan2(ey - y, ex - x)
            x2, y2 = M.mover(g, x, y, math.cos(ang) * paso, math.sin(ang) * paso, r, borde=False)
            if math.hypot(x2 - x, y2 - y) < paso * 0.2:
                return self._escapar(x, y, ang, paso, r)
            return x2, y2
        cx, cy = int(x // TAM), int(y // TAM)
        f = self.flujo
        if f[cy][cx] == 0:                       # ya esta en la casilla del heroe: va directo
            return self._rodear(x, y, paso, r)
        if f[cy][cx] < 0:
            # casilla pegada a un arbol: sube al camino por la vecina libre mas cercana
            cand = [(f[cy + dy][cx + dx], cx + dx, cy + dy) for dx, dy in M.VECINOS8
                    if 0 <= cx + dx < M.COLS and 0 <= cy + dy < M.FILAS and f[cy + dy][cx + dx] >= 0]
            if not cand:
                return self._rodear(x, y, paso, r)
            _, nx, ny = min(cand)
        else:
            mejor, bd = None, f[cy][cx]
            for dx, dy in M.VECINOS8:
                nx_, ny_ = cx + dx, cy + dy
                if 0 <= nx_ < M.COLS and 0 <= ny_ < M.FILAS and 0 <= f[ny_][nx_] < bd:
                    bd, mejor = f[ny_][nx_], (nx_, ny_)
            if mejor is None:
                return self._rodear(x, y, paso, r)
            nx, ny = mejor
        ang = math.atan2((ny + 0.5) * TAM - y, (nx + 0.5) * TAM - x)
        x2, y2 = M.mover(g, x, y, math.cos(ang) * paso, math.sin(ang) * paso, r, borde=False)
        if math.hypot(x2 - x, y2 - y) < paso * 0.2:
            return self._escapar(x, y, ang, paso, r)
        return x2, y2

    def _entrada(self, x, y):
        """Centro de la casilla libre del borde (alcanzable desde el heroe) mas cercana a (x,y)."""
        TAM, f = M.TAM, self.flujo
        if f is None:
            return M.ANCHO_MUNDO / 2, M.ALTO_MUNDO / 2
        cx = min(max(int(x // TAM), 0), M.COLS - 1)
        cy = min(max(int(y // TAM), 0), M.FILAS - 1)
        mejor, bd = None, None
        for k in range(-12, 13):
            for bx, by in ((0, cy + k), (M.COLS - 1, cy + k), (cx + k, 0), (cx + k, M.FILAS - 1)):
                if 0 <= bx < M.COLS and 0 <= by < M.FILAS and f[by][bx] >= 0:
                    dd = (bx - cx) ** 2 + (by - cy) ** 2
                    if bd is None or dd < bd:
                        bd, mejor = dd, (bx, by)
        if mejor is None:                        # no hay entrada alcanzable: va al centro del mapa
            return M.ANCHO_MUNDO / 2, M.ALTO_MUNDO / 2
        return (mejor[0] + 0.5) * TAM, (mejor[1] + 0.5) * TAM

    def _escapar(self, x, y, ang, paso, r):
        """Enemigo encajado en la esquina de un arbol: prueba otras direcciones con fisica
        y toma la que lo mueve y deja en el camino mas cercano."""
        g, TAM, f = self.g, M.TAM, self.flujo
        mejor, clave = (x, y), None
        for giro in (0.5, -0.5, 1.0, -1.0, 1.6, -1.6, 2.3, -2.3, math.pi):
            a = ang + giro
            nx, ny = M.mover(g, x, y, math.cos(a) * paso, math.sin(a) * paso, r, borde=False)
            mv = math.hypot(nx - x, ny - y)
            if mv < paso * 0.3:
                continue
            cx, cy = int(nx // TAM), int(ny // TAM)
            fn = f[cy][cx] if (0 <= nx < M.ANCHO_MUNDO and 0 <= ny < M.ALTO_MUNDO and f[cy][cx] >= 0) else 10 ** 6
            if clave is None or (fn, -mv) < clave:
                clave, mejor = (fn, -mv), (nx, ny)
        return mejor

    def _rodear(self, x, y, paso, r):
        """Va hacia el heroe; si un arbol o roca bloquea, prueba direcciones desviadas
        y toma la que mas acerca al enemigo. Asi no queda clavado detras de obstaculos."""
        base = math.atan2(self.hy - y, self.hx - x)
        mejor, mejor_d = (x, y), math.hypot(self.hx - x, self.hy - y)
        for giro in (0.0, 0.5, -0.5, 1.0, -1.0, 1.6, -1.6, 2.3, -2.3):
            a = base + giro
            nx, ny = M.mover(self.g, x, y, math.cos(a) * paso, math.sin(a) * paso, r, borde=False)
            if math.hypot(nx - x, ny - y) < paso * 0.3:
                continue
            falta = math.hypot(self.hx - nx, self.hy - ny)
            if falta < mejor_d:
                mejor, mejor_d = (nx, ny), falta
            if giro == 0.0 and falta < math.hypot(self.hx - x, self.hy - y):
                # el paso directo funciona: no hace falta buscar mas
                return mejor
        return mejor

    def _actualizar_jefe(self, dt):
        b = self.boss
        if b is None or b["vida"] <= 0 or any(k in b["est"] for k in STUN):
            return
        if b["dash"] > 0:                          # embestida hacia la zona marcada
            b["dash"] -= dt
            ux, uy = b["dash_dir"]
            b["x"], b["y"] = M.mover(self.g, b["x"], b["y"], ux * VEL_EMBESTIDA * dt, uy * VEL_EMBESTIDA * dt,
                                     b["r"], borde=False)
            return
        if b["pat"] is None:                       # camina por el mapa hacia el heroe
            d = math.hypot(self.hx - b["x"], self.hy - b["y"])
            if d > JEFE_DIST_ATAQUE:
                b["x"], b["y"] = self._seguir(b["x"], b["y"], VEL_BOSS * dt, b["r"])
            b["pat_t"] -= dt
            if b["pat_t"] <= 0 and d <= JEFE_DIST_ATAQUE:
                self._atacar_jefe(b, self.rng.choice(["melee", "meteoros", "rayo"]))
            return
        b["tel"] -= dt                             # carga: quieto, marcando la zona
        if b["tel"] > 0:
            return
        if b["pat"] == "melee" and not b["embistio"]:
            b["embistio"] = True
            dx, dy = b["obj"][0] - b["x"], b["obj"][1] - b["y"]
            d = max(1.0, math.hypot(dx, dy))
            b["dash_dir"] = (dx / d, dy / d)
            b["dash"] = 0.5
            return
        if not any(a["jefe"] for a in self.amenazas) and b["dash"] <= 0:
            b["pat"], b["pat_t"], b["embistio"] = None, JEFE_PAUSA, False

    def _atacar_jefe(self, b, tipo):
        """Empieza un ataque: marca las zonas ahora (el heroe tiene el tiempo de carga para esquivar)."""
        b["pat"], b["tel"], b["embistio"] = tipo, JEFE_CARGA[tipo], False
        carga = JEFE_CARGA[tipo]
        hx, hy = self.hx, self.hy
        if tipo == "melee":                        # se acerca y embiste la zona pequena marcada
            b["obj"] = (hx, hy)
            self.amenazas.append(dict(kind="circulo", x=hx, y=hy, r=60.0, carga=carga, golpe=carga + 0.5,
                                      dur=0.35, t=0.0, hecho=False, jefe=True))
        elif tipo == "meteoros":                   # cae desde el cielo sobre varias zonas
            for _ in range(5):
                a = self.rng.uniform(0, 2 * math.pi)
                d = self.rng.uniform(0, 260)
                x, y = self._limitar(hx + math.cos(a) * d, hy + math.sin(a) * d)
                self.amenazas.append(dict(kind="circulo", x=x, y=y, r=70.0, carga=carga, golpe=carga,
                                          dur=0.35, t=0.0, hecho=False, jefe=True))
        else:                                      # rayo en abanico: 5 haces estrechos y largos
            base = math.atan2(hy - b["y"], hx - b["x"])
            for off in (-0.6, -0.3, 0.0, 0.3, 0.6):
                self.amenazas.append(dict(kind="rayo", x=b["x"], y=b["y"], ang=base + off, largo=LARGO_RAYO,
                                          ancho=ANCHO_RAYO, carga=carga, dur=0.8, t=0.0, hecho=False, jefe=True))
        self._avisar("¡Cuidado!", 1.0)

    def _actualizar_amenazas(self, dt):
        """Zonas marcadas del dragon: hacen dano cuando llega su momento (si el heroe sigue ahi)."""
        vivas = []
        for a in self.amenazas:
            a["t"] += dt
            if a["kind"] == "circulo":
                if not a["hecho"] and a["t"] >= a["golpe"]:
                    a["hecho"] = True
                    self._explosion(a["x"], a["y"], (255, 110, 60), 16)
                    if self.invuln <= 0 and math.hypot(self.hx - a["x"], self.hy - a["y"]) <= a["r"] + D.RADIO_HEROE:
                        self._golpe_heroe()
                if a["t"] < a["golpe"] + a["dur"]:
                    vivas.append(a)
            else:
                if not a["hecho"] and a["t"] >= a["carga"] and self.invuln <= 0:
                    L = min(a["largo"], (a["t"] - a["carga"]) * VEL_RAYO)
                    ca, sa = math.cos(a["ang"]), math.sin(a["ang"])
                    rx, ry = self.hx - a["x"], self.hy - a["y"]
                    s, perp = rx * ca + ry * sa, -rx * sa + ry * ca
                    if 0 <= s <= L and abs(perp) <= a["ancho"] / 2 + D.RADIO_HEROE:
                        a["hecho"] = True
                        self._golpe_heroe()
                if a["t"] < a["carga"] + a["dur"]:
                    vivas.append(a)
        self.amenazas = vivas

    def _asignar_tiradores(self):
        """Mantiene la cantidad de tiradores que toca segun el progreso (solo entre los de 3+ disparos)."""
        cuota = 0 if self.solo_jefe else D.tiradores_max(self.derrotas)
        vivos = sum(1 for e in self.enemigos if e.get("tira"))
        if vivos >= cuota:
            return
        candidatos = [e for e in self.enemigos if not e["jefe"] and not e.get("tira")
                      and e["vmax"] >= D.VIDA_TIRADOR]
        for e in self.rng.sample(candidatos, min(cuota - vivos, len(candidatos))):
            e["tira"] = True
            e["tiro"] = self.rng.uniform(1.0, CADA_TIRO)

    def _dibujar_amenazas(self, p):
        for a in self.amenazas:
            if a["kind"] == "circulo":
                sx, sy = self._s(a["x"], a["y"])
                if a["t"] < a["golpe"]:            # aviso: el anillo se achica hasta el golpe
                    pygame.draw.circle(p, (255, 80, 60), (int(sx), int(sy)), int(a["r"]), 4)
                    rin = int(a["r"] * max(0.1, 1 - a["t"] / a["golpe"]))
                    pygame.draw.circle(p, (255, 200, 90), (int(sx), int(sy)), rin, 2)
                else:
                    pygame.draw.circle(p, (255, 120, 60), (int(sx), int(sy)), int(a["r"]))
                continue
            ox, oy = self._s(a["x"], a["y"])
            ca, sa = math.cos(a["ang"]), math.sin(a["ang"])
            L = a["largo"] if a["t"] < a["carga"] else min(a["largo"], (a["t"] - a["carga"]) * VEL_RAYO)
            nx, ny = -sa * a["ancho"] / 2, ca * a["ancho"] / 2
            ex, ey = ca * L, sa * L
            pts = [(ox + nx, oy + ny), (ox - nx, oy - ny), (ox + ex - nx, oy + ey - ny), (ox + ex + nx, oy + ey + ny)]
            if a["t"] < a["carga"]:
                pygame.draw.polygon(p, (255, 80, 60), pts, 3)
            else:
                pygame.draw.polygon(p, (255, 140, 60), pts)

    def _actualizar_proyectiles(self, dt):
        vivos = []
        for p in self.proys:
            p["ttl"] -= dt
            if p["ttl"] <= 0:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if M.casilla(self.g, p["x"], p["y"]) in M.BLOQUEADO:
                self._explosion(p["x"], p["y"], D.COLOR_TIPO[p["tipo"]], 4)
                continue
            acabado = False
            for e in self.enemigos:
                if id(e) in p["tocados"]:
                    continue
                if math.hypot(e["x"] - p["x"], e["y"] - p["y"]) <= p["r"] + e["r"]:
                    p["tocados"].add(id(e))
                    self._herir(e, p["dano"])
                    if p["efecto"]:
                        self._efecto(e, p["efecto"], p["dur"])
                    self._explosion(p["x"], p["y"], D.COLOR_TIPO[p["tipo"]], 12 if p["inter"] else 5)
                    p["pen"] -= 1
                    if p["pen"] <= 0:
                        acabado = True
                        break
            if not acabado:
                vivos.append(p)
        self.proys = vivos

    def _actualizar_zonas(self, dt):
        vivas = []
        for z in self.zonas:
            z["t"] += dt
            if z["fase"] == "aviso":
                z["u"] = min(1.0, z["t"] / AVISO_ULT)
                if z["t"] >= AVISO_ULT:
                    self._impacto(z)
                    z["fase"], z["t"] = "activa", 0.0
                vivas.append(z)
            else:
                z["u"] = min(1.0, z["t"] / 0.5)
                if z["t"] < 0.5:
                    vivas.append(z)
        self.zonas = vivas

    def _impacto(self, z):
        for e in self.enemigos:
            if math.hypot(e["x"] - z["x"], e["y"] - z["y"]) <= z["r"] + e["r"]:
                self._herir(e, z["dano"])
                self._efecto(e, z["efecto"], z["dur"])
        self._explosion(z["x"], z["y"], D.COLOR_TIPO[z["tipo"]], 18)

    def _actualizar_balas(self, dt):
        vivas = []
        for b in self.balas:
            b["ttl"] -= dt
            if b["ttl"] <= 0:
                continue
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            if M.casilla(self.g, b["x"], b["y"]) in M.BLOQUEADO:
                continue
            if self.invuln <= 0 and math.hypot(self.hx - b["x"], self.hy - b["y"]) < D.RADIO_HEROE + b["r"]:
                self._golpe_heroe()
                continue
            vivas.append(b)
        self.balas = vivas

    def _soltar_corazon(self, e):
        """Al derrotar un enemigo a veces cae un corazon: casi siempre de los de muchos disparos."""
        prob = PROB_CORAZON_RARO if e["vmax"] >= 5 else PROB_CORAZON
        if len(self.corazones) < MAX_CORAZONES and self.rng.random() < prob:
            x, y = self._limitar(e["x"], e["y"])
            self.corazones.append({"x": x, "y": y})

    def _recoger(self):
        """Si el heroe pasa por encima de un corazon, recupera 1 vida."""
        for c in list(self.corazones):
            if math.hypot(self.hx - c["x"], self.hy - c["y"]) < RADIO_CHOQUE_HEROE + 14:
                self.corazones.remove(c)
                self.vidas = min(D.VIDA, self.vidas + 1)
                self._explosion(c["x"], c["y"], (240, 70, 110), 10)
                self._avisar("¡+1 corazón!", 1.2)

    def _muertes(self):
        vivos = []
        for e in self.enemigos:
            if e["vida"] > 0:
                vivos.append(e)
                continue
            if e["jefe"]:
                self.boss = None
                self._explosion(e["x"], e["y"], (255, 240, 150), 60)
                self.sumar(D.PUNTOS_JEFE, *self._s(e["x"], e["y"]))
                self._finalizar("gana", "¡Venciste al dragón!")
            else:
                self.derrotas += 1
                self._soltar_corazon(e)
                self._explosion(e["x"], e["y"], (255, 240, 150), 14)
                self.sumar(D.PUNTOS_DERROTA, *self._s(e["x"], e["y"]))
        self.enemigos = vivos

    # ------------------------------------------------------------ dibujo
    def dibujar_juego(self, p):
        if self.fase == "elegir":
            self._dibujar_elegir(p)
            return
        self._dibujar_mundo(p)
        if self.fase == "subida":
            self._dibujar_subida(p)

    def _dibujar_mundo(self, p):
        cx, cy = int(self.cam[0]), int(self.cam[1])
        self.mapa.blit(p, cx, cy, ANCHO, ALTO)
        for z in self.zonas:
            zz = dict(z)
            zz["x"], zz["y"] = self._s(z["x"], z["y"])
            A.dibujar_zona(p, zz, self.t)
        for c in self.corazones:
            sx, sy = self._s(c["x"], c["y"])
            A.corazon(p, sx, sy + math.sin(self.t * 4) * 2, True, tam=26)
        for e in sorted(self.enemigos, key=lambda q: q["y"]):
            sx, sy = self._s(e["x"], e["y"])
            if e["jefe"]:
                A.dibujar_jefe(p, "dragon", 3, sx, sy, BOSS_ALTO, self.t, rojo=e["tel"] > 0)
            else:
                A.dibujar_enemigo(p, e["especie"], e["etapa"], sx, sy, e["alto"], self.t, set(e["est"]))
            if e.get("tira") and e["tiro"] < 0.5:  # tirador a punto de disparar: aviso en rojo
                pygame.draw.circle(p, (255, 80, 80), (int(sx), int(sy)), int(e["alto"] / 2 + 8), 3)
            if e["vida"] < e["vmax"] and not e["jefe"]:
                barra(p, pygame.Rect(int(sx - 22), int(sy - e["alto"] / 2 - 10), 44, 6),
                      max(0.0, e["vida"] / e["vmax"]), color=(120, 230, 120))
        self._dibujar_telegrafos(p)
        for b in self.balas:
            sx, sy = self._s(b["x"], b["y"])
            A.dibujar_bala_enemiga(p, sx, sy, b["r"], self.t)
        hx, hy = self._s(self.hx, self.hy)
        A.dibujar_heroe(p, hx, hy, self.tipo, self.t, self.invuln, self.mirar)
        for pr in self.proys:
            sx, sy = self._s(pr["x"], pr["y"])
            A.dibujar_proyectil(p, pr["tipo"], sx, sy, pr["ang"], pr["r"], self.t, pr["inter"])
        for q in self.parts:
            q.dibujar(p)

    def _dibujar_telegrafos(self, p):
        self._dibujar_amenazas(p)

    def _dibujar_elegir(self, p):
        escribir(p, self.f.enorme, "Elige tu elemento", CX, 90)
        escribir(p, self.f.chica, "Apunta a una carta y espera un momento, o haz clic", CX, 152)
        for i, (r, tipo) in enumerate(zip(self._rects_tipos(), D.TIPOS)):
            resaltada = self.dwell_i == i
            A.tarjeta(p, r, self.f.normal, self.f.chica, D.NOMBRE_TIPO[tipo],
                      f"Disparo de {D.NOMBRE_TIPO[tipo].lower()}. Luego: {D.INTERMEDIO[tipo][0]} y {D.ULTIMATE[tipo]}.",
                      _carta_color(tipo), True, icono=A.icono_habilidad(tipo, "basico", 70),
                      enfoque=resaltada, dwell=self.dwell if resaltada else 0.0)

    def _dibujar_subida(self, p):
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((10, 8, 24, 170))
        p.blit(velo, (0, 0))
        escribir(p, self.f.enorme, "¡Subes de nivel!", CX, 110)
        escribir(p, self.f.chica, "Elige una mejora", CX, 165)
        if self.aviso_t > 0:
            escribir(p, self.f.normal, self.aviso, CX, 205, color=(255, 240, 150))
        for i, (r, c) in enumerate(zip(self._rects_cartas(), self.cartas)):
            resaltada = self.dwell_i == i
            A.tarjeta(p, r, self.f.normal, self.f.chica, c["nombre"], c["desc"], _carta_color(self.tipo), c["ok"],
                      c["motivo"], icono=A.icono_habilidad(self.tipo, RAMA_ICONO[c["rama"]], 64),
                      enfoque=resaltada, dwell=self.dwell if resaltada else 0.0)

    def dibujar_hud(self, p):
        if self.fase == "elegir":
            return
        f = self.f
        escribir(p, f.grande, f"Puntos: {self.puntos}", 24, 34, ancla="izq")
        for i, meta in enumerate(self.metas):
            lleno = self.puntos >= meta
            estrella(p, 40 + i * 44, 84, 17,
                     (255, 210, 60) if lleno else (200, 205, 220),
                     (160, 110, 20) if lleno else (140, 145, 165))
        escribir(p, f.grande, f"Derrotas: {self.derrotas}/{D.DERROTAS_JEFE}", ANCHO - 24, 34, ancla="der")
        corazones(p, self.vidas, D.VIDA, 40, ALTO - 40, r=14, sep=36)
        self._barra_nivel(p)
        self._habilidades(p)
        if self.boss is not None and self.boss["vida"] > 0:
            barra(p, pygame.Rect(CX - 300, 70, 600, 18), max(0.0, self.boss["vida"] / self.boss["vmax"]),
                  color=(230, 80, 90))
            escribir(p, f.chica, "DRAGÓN", CX, 79)
        if self.aviso_t > 0 and self.fase == "jugar":
            escribir(p, f.enorme, self.aviso, CX, 200, color=(255, 240, 150))

    def _barra_nivel(self, p):
        nivel = D.nivel_de(self.derrotas)
        prev = D.UMBRALES[nivel - 1] if nivel > 0 else 0
        if nivel < len(D.UMBRALES):
            prox = D.UMBRALES[nivel]
            texto = f"Mejoras {nivel}/{len(D.UMBRALES)} · próxima en {prox - self.derrotas} derrotas"
        else:
            prox = D.DERROTAS_JEFE
            texto = "¡Último tramo hacia el dragón!"
        barra(p, pygame.Rect(CX - 220, ALTO - 44, 440, 22), (self.derrotas - prev) / max(1, prox - prev),
              color=(120, 220, 255))
        escribir(p, self.f.chica, texto, CX, ALTO - 58)

    def _habilidades(self, p):
        st, h = self.st, self.hab
        iconos = [("basico", True, self.cd_basico / st["cadencia"], len(h.basico))]
        if st["inter_on"]:
            iconos.append(("inter", True, max(0.0, self.cd_inter) / (INTER_CD * st["carga"]), len(h.inter)))
        if st["ult_on"]:
            iconos.append(("ulti", True, max(0.0, self.cd_ult) / max(0.1, st["ult_intervalo"][1]),
                           1 if h.ult else 0))
        for i, (cual, _, frac, n) in enumerate(iconos):
            x = ANCHO - 90 - i * 84
            y = ALTO - 100
            p.blit(A.icono_habilidad(self.tipo, cual, 64), (x, y))
            if frac > 0:
                velo = pygame.Surface((64, int(64 * min(1.0, frac))), pygame.SRCALPHA)
                velo.fill((0, 0, 0, 140))
                p.blit(velo, (x, y))
            escribir(p, self.f.chica, f"x{n}", x + 32, y + 78)


CARTA = {"agua": (38, 92, 150), "viento": (58, 128, 112), "fuego": (150, 62, 24),
         "hielo": (62, 118, 168), "tierra": (96, 66, 38), "electrico": (140, 110, 22)}


def _carta_color(tipo):
    """Fondo de las cartas: un tono oscuro de cada elemento para que el texto blanco se lea."""
    return CARTA[tipo]
