"""Captura: apunta con el cursor y lanza la red a la criatura del prado."""

import math
import random
from collections import deque

import pygame

from ajustes import ANCHO, ALTO
from arte import CRIATURAS, dibujar_criatura
from j_combate import Combate
from nucleo import (Minijuego, TextoFlotante, aclarar, oscurecer, escribir, explosion,
                    estrella, V2)

ZONA = (120, 205, 1160, 555)          # donde puede andar la criatura (x0, y0, x1, y1)
ORIGEN = V2(ANCHO / 2, ALTO + 70)     # de aqui sale la bola
DUR_VUELO = 0.4
DUR_SALTO_ESCONDIDA = (1.0, 1.6)

# valores por nivel (indice nivel - 1)
NIVEL_COMBATE = 4                     # niveles 1-3: captura; 4: combate; 5: jefe final
COMPANERA_PRESTADA = "pelusin"        # criatura prestada si el jugador aun no tiene ninguna
VEL_BASE = (62, 92, 130, 175, 220)
ESCALA = (1.35, 1.25, 1.15, 1.05, 1.0)
PAUSA = ((0.8, 1.5), (0.5, 1.1), (0.3, 0.7), (0.1, 0.4), (0.0, 0.15))
PROB_ESCONDER = (0.0, 0.0, 0.25, 0.35, 0.45)
PROB_SPRINT = (0.0, 0.08, 0.2, 0.32, 0.45)
RADIO_BASE = (150, 136, 124, 114, 106)
PESOS_RAREZA = ((1.0, 0.0, 0.0), (0.8, 0.2, 0.0), (0.55, 0.38, 0.07),
                (0.38, 0.45, 0.17), (0.25, 0.45, 0.30))
FACTOR_RAREZA = {1: 1.0, 2: 0.9, 3: 0.8}
PUNTOS_RAREZA = {1: 10, 2: 20, 3: 40}
COLORES_CONFETI = [(255, 90, 90), (255, 210, 60), (90, 210, 120), (80, 170, 250),
                   (240, 120, 230), (255, 160, 60)]


def _ease_out(f):
    f = max(0.0, min(1.0, f))
    return 1 - (1 - f) ** 3


def _crear_bola(r):
    """Bola-red naranja con malla blanca (superficie de lado 2r+8)."""
    d = 2 * r + 8
    c = d // 2
    sup = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(sup, (70, 40, 90), (c, c), r + 3)
    pygame.draw.circle(sup, (255, 165, 50), (c, c), r)
    red = pygame.Surface((d, d), pygame.SRCALPHA)
    for k in range(-3, 4):
        o = k * r / 3
        pygame.draw.line(red, (255, 240, 200), (c - r, c + o - r / 2), (c + r, c + o + r / 2), 2)
        pygame.draw.line(red, (255, 240, 200), (c - r, c + o + r / 2), (c + r, c + o - r / 2), 2)
    mascara = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (c, c), r - 1)
    red.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    sup.blit(red, (0, 0))
    pygame.draw.circle(sup, (255, 255, 255), (c - r // 3, c - r // 3), max(2, r // 6))
    pygame.draw.circle(sup, (70, 40, 90), (c, c), r + 1, 3)
    return sup


def _gris(sup):
    g = sup.copy()
    g.fill((150, 150, 165, 255), special_flags=pygame.BLEND_RGBA_MIN)
    return g


def _crear_arbusto():
    sup = pygame.Surface((250, 160), pygame.SRCALPHA)
    blobs = [(60, 100, 50), (125, 78, 64), (190, 100, 50), (95, 114, 48), (160, 114, 48)]
    for x, y, r in blobs:
        pygame.draw.circle(sup, (35, 105, 55), (x, y), r + 4)
    for x, y, r in blobs:
        pygame.draw.circle(sup, (70, 175, 85), (x, y), r)
    for x, y, r in blobs:
        pygame.draw.circle(sup, (110, 210, 110), (x - r // 3, y - r // 3), r // 3)
    rnd = random.Random(5)
    for _ in range(9):
        x, y = rnd.randint(40, 210), rnd.randint(70, 135)
        pygame.draw.circle(sup, (235, 60, 80), (x, y), 6)
        pygame.draw.circle(sup, (255, 190, 200), (x - 2, y - 2), 2)
    return sup


def _crear_fondo():
    f = pygame.Surface((ANCHO, ALTO))
    for y in range(ALTO):
        k = y / ALTO
        pygame.draw.line(f, (int(110 + 90 * k), int(190 + 45 * k), 255), (0, y), (ANCHO, y))
    pygame.draw.circle(f, (255, 235, 120), (1130, 120), 60)
    pygame.draw.circle(f, (255, 250, 190), (1130, 120), 44)
    for x, y, e in ((220, 150, 1.0), (620, 120, 0.8), (880, 190, 0.7)):
        for dx, dy, r in ((-40, 6, 28), (0, -8, 36), (40, 6, 28), (0, 14, 28)):
            pygame.draw.circle(f, (255, 255, 255), (int(x + dx * e), int(y + dy * e)), int(r * e))
    pygame.draw.ellipse(f, (120, 205, 120), (-200, 250, 900, 260))
    pygame.draw.ellipse(f, (100, 195, 110), (500, 230, 1000, 300))
    pygame.draw.rect(f, (95, 190, 100), (0, 330, ANCHO, ALTO - 330))
    for y in range(330, ALTO, 6):
        k = (y - 330) / (ALTO - 330)
        pygame.draw.line(f, (int(100 - 25 * k), int(195 - 35 * k), int(100 - 20 * k)),
                         (0, y), (ANCHO, y), 6)
    rnd = random.Random(11)
    for _ in range(46):
        x, y = rnd.randint(10, ANCHO - 10), rnd.randint(360, ALTO - 20)
        c = rnd.choice(((255, 240, 120), (255, 255, 255), (255, 150, 190), (190, 160, 255)))
        for a in range(0, 360, 72):
            pygame.draw.circle(f, c, (int(x + 6 * math.cos(math.radians(a))),
                                      int(y + 6 * math.sin(math.radians(a)))), 4)
        pygame.draw.circle(f, (255, 190, 60), (x, y), 3)
    return f


class Arbusto:
    def __init__(self, cx, cy, sup):
        self.cx, self.cy, self.sup = cx, cy, sup
        self.base = cy + sup.get_height() / 2
        self.temblor = 0.0

    def dibujar(self, pantalla):
        dx = math.sin(self.temblor * 60) * 4 * min(1.0, self.temblor * 3) if self.temblor > 0 else 0
        pantalla.blit(self.sup, self.sup.get_rect(center=(self.cx + dx, self.cy)))


class Captura(Minijuego):
    """Captura de criaturas (niveles 1-3), combate por turnos (nivel 4) y jefe final (nivel 5).

    Niveles 1-3: apunta con el cursor (reticula) y lanza la bola con GOLPE, clic o tajo rapido.
    Nivel 4: combate por turnos contra una criatura salvaje con una criatura capturada como companera.
    Nivel 5: combate contra el Rey Grunon. Ambos delegan en `self.interno` (un Combate) y Captura
    refleja hacia fuera puntos, terminado, ganado, recompensas, etc.

    Mejoras de la ruleta:
      alcance  -> agranda los anillos de la reticula (zona donde se atrapa) / zona de critico en combate
      potencia -> sube la probabilidad de atrapar / multiplica el dano en combate
      lento    -> la criatura se mueve y se esconde mas despacio / combate mas pausado
      vida     -> una bola extra por criatura / un corazon extra en combate
      puntos   -> puntos x2 (lo aplica sumar())
      tiempo   -> mas segundos (solo captura; el combate no tiene limite)
    """

    id = "captura"
    titulo = "Captura"
    instruccion = "Apunta con el mando y da un golpe para lanzar la bola. ¡Atrapa criaturas!"
    gesto = "Apunta y da un golpe"
    duracion = 60.0
    fondo_arriba = (120, 200, 255)
    fondo_abajo = (200, 235, 255)
    etiquetas_nivel = {1: "Captura fácil", 2: "Captura", 3: "Captura difícil",
                       4: "Combate", 5: "Jefe: Rey Gruñón"}
    # nivel -> (instruccion, gesto); si falta el nivel se usan instruccion y gesto de la clase
    instrucciones_nivel = {
        4: ("Combate con tu criatura amiga: elige tu acción y esquiva moviendo el cursor.",
            "Tajo, golpe, agitar y esquivar"),
        5: ("¡El Rey Gruñón te reta! Elige tu acción y esquiva sus ataques.",
            "Tajo, golpe, agitar y esquivar"),
    }

    def __init__(self, ctx, nivel=1):
        super().__init__(ctx, nivel)
        self.interno = None
        ins = self.instrucciones_nivel.get(self.nivel)
        if ins:
            self.instruccion, self.gesto = ins
        if self.nivel >= NIVEL_COMBATE:
            self._iniciar_combate()
            return
        self.etiqueta = self.etiquetas_nivel[self.nivel]
        n = self.nivel - 1
        self.alc = self.mej.mult("alcance")
        self.pot = self.mej.mult("potencia")
        self.bolas_max = 3 + self.mej.vidas_extra()
        self.escala = ESCALA[n]
        self.bg = _crear_fondo()
        sup_arb = _crear_arbusto()
        self.arbustos = [Arbusto(x, y, sup_arb) for x, y in ((200, 440), (1075, 425),
                                                             (470, 525), (810, 510))]
        self.sup_bola = _crear_bola(40)
        self.bola_hud = _crear_bola(20)
        self.bola_hud_gris = _gris(self.bola_hud)
        self.sombra = pygame.Surface((150, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(self.sombra, (30, 80, 40, 90), self.sombra.get_rect())
        self.pos = V2(ANCHO / 2, ALTO / 2)
        self.hist = deque()
        self.tajo_prev = False
        self.particulas, self.rebotes = [], []
        self.capturas = 0
        self.prev_id = None
        self._nueva()

    # ------------------------------------------------------------------
    #  Niveles 4 y 5: combate delegado
    # ------------------------------------------------------------------
    def _elegir_companera(self):
        """La criatura capturada mas rara (la mas reciente si empatan); si no hay, una prestada."""
        mias = [c for c in self.ctx.perfil.criaturas if c in CRIATURAS]
        if not mias:
            return COMPANERA_PRESTADA
        return max(enumerate(mias), key=lambda ic: (CRIATURAS[ic[1]][1], ic[0]))[1]

    def _iniciar_combate(self):
        self.companera = self._elegir_companera()
        jefe = self.nivel >= 5
        self.interno = Combate(self.ctx, 5 if jefe else 3, jefe=jefe, companera=self.companera)
        self.fondo_arriba = self.interno.fondo_arriba
        self.fondo_abajo = self.interno.fondo_abajo
        self.etiqueta = self.etiquetas_nivel[self.nivel]
        self.tiempo = self.tiempo_total = None
        self._sincronizar()

    def _sincronizar(self):
        i = self.interno
        self.puntos = i.puntos
        self.terminado = i.terminado
        self.ganado = i.ganado
        self.mensaje_final = i.mensaje_final
        self.recompensas = i.recompensas
        self.botin = i.botin
        self.metas = i.metas
        self.flotantes = i.flotantes
        self.t = i.t

    def actualizar(self, dt, ctrl):
        if self.interno is None:
            return super().actualizar(dt, ctrl)
        self.interno.actualizar(dt, ctrl)
        self._sincronizar()

    def dibujar(self, pantalla):
        if self.interno is None:
            return super().dibujar(pantalla)
        self.interno.dibujar(pantalla)

    def estrellas(self):
        if self.interno is not None:
            return self.interno.estrellas()
        return super().estrellas()

    def superado(self):
        if self.interno is not None:
            return self.interno.superado()
        return super().superado()

    # ------------------------------------------------------------------
    def calcular_metas(self):
        n = self.nivel
        if n >= NIVEL_COMBATE:
            return (1, 2, 3)
        return (10, 25 + 4 * n, 50 + 8 * n)

    # --- criatura ---
    def _nueva(self):
        n = self.nivel - 1
        rar = 1 if self.capturas < 2 else random.choices((1, 2, 3), PESOS_RAREZA[n])[0]
        ids = [k for k, v in CRIATURAS.items() if v[1] == rar and k != self.prev_id]
        self.cid = random.choice(ids)
        self.prev_id = self.cid
        self.rareza = rar
        self.cp = V2(random.uniform(ZONA[0] + 80, ZONA[2] - 80), random.uniform(ZONA[1] + 40, ZONA[3] - 60))
        self.cv = V2(0, 0)
        self.modo, self.arb = "vaga", None
        self.pausa, self.th, self.oculta, self.salto = 0.6, 0.0, 0.0, 0.0
        self.meta, self.vel_actual = V2(self.cp), VEL_BASE[n]
        self.estado, self.te = "aparece", 0.0
        self.bolas, self.fallos = self.bolas_max, 0
        self.bola, self.cool = None, 0.0
        explosion(self.particulas, self.cp.x, self.cp.y, (255, 255, 255), n=12, vel_min=60,
                  vel_max=240, vida=0.6, gravedad=0, radio=7)
        self.sonidos.reproducir("pop")

    def _elegir_meta(self, esconder=True):
        n = self.nivel - 1
        if esconder and random.random() < PROB_ESCONDER[n]:
            self.arb = random.choice(self.arbustos)
            self.meta = V2(self.arb.cx, self.arb.cy + 8)
            self.modo, self.vel_actual = "va_arbusto", VEL_BASE[n] * 1.3
            return
        for _ in range(8):
            ang = random.uniform(0, 2 * math.pi)
            d = random.uniform(160, 420)
            m = self.cp + V2(math.cos(ang), math.sin(ang)) * d
            if ZONA[0] <= m.x <= ZONA[2] and ZONA[1] <= m.y <= ZONA[3]:
                break
        else:
            m = V2(random.uniform(ZONA[0], ZONA[2]), random.uniform(ZONA[1], ZONA[3]))
        self.meta, self.modo = m, "vaga"
        self.vel_actual = VEL_BASE[n] * random.uniform(0.7, 1.15)
        if random.random() < PROB_SPRINT[n]:
            self.vel_actual *= 1.9

    def _mover(self, dt):
        n = self.nivel - 1
        desired = V2(0, 0)
        if self.modo == "escondida":
            self.th -= dt
            if self.th <= 0:
                self.arb.temblor = 0.4
                self.salto = 0.4
                self.sonidos.reproducir("pop")
                self.pausa = 0.0
                self._elegir_meta(esconder=False)
        elif self.pausa > 0:
            self.pausa -= dt
            if self.pausa <= 0:
                self._elegir_meta()
        else:
            d = self.meta - self.cp
            dist = d.length()
            if dist < 22:
                if self.modo == "va_arbusto":
                    self.modo = "escondida"
                    self.th = random.uniform(*DUR_SALTO_ESCONDIDA)
                    self.arb.temblor = 0.4
                else:
                    self.pausa = random.uniform(*PAUSA[n])
                    if self.pausa < 0.03:
                        self._elegir_meta()
            else:
                freno = 0.45 if (self.bola is not None and self.nivel <= 2) else 1.0
                desired = d / dist * self.vel_actual * freno
        self.cv += (desired - self.cv) * min(1.0, (3.0 + self.nivel) * dt)
        self.cp += self.cv * dt
        if self.modo != "va_arbusto" and self.modo != "escondida":
            if self.cp.x < ZONA[0] or self.cp.x > ZONA[2]:
                self.cp.x = max(ZONA[0], min(ZONA[2], self.cp.x))
                self.cv.x = -self.cv.x
                self.meta.x = ANCHO - self.meta.x
            if self.cp.y < ZONA[1] or self.cp.y > ZONA[3]:
                self.cp.y = max(ZONA[1], min(ZONA[3], self.cp.y))
                self.cv.y = -self.cv.y
                self.meta.y = ZONA[1] + ZONA[3] - self.meta.y
        hacia = 1.0 if self.modo == "escondida" else 0.0
        self.oculta += (hacia - self.oculta) * min(1.0, 9 * dt)
        self.salto = max(0.0, self.salto - dt)

    # --- puntería ---
    def _facil(self):
        return self.capturas < 2

    def radios(self):
        """(radio exterior, radio de acierto seguro) de la reticula."""
        r = RADIO_BASE[self.nivel - 1] * self.alc * (1 + 0.12 * self.fallos)
        if self._facil():
            r *= 1.35
        return r, 0.55 * r

    def probabilidad(self, d):
        r, rf = self.radios()
        if d <= rf:
            p = 1.0
        elif d <= r:
            p = 1.0 - 0.8 * (d - rf) / (r - rf)
        else:
            return 0.0
        p *= 1.0 if self._facil() else FACTOR_RAREZA[self.rareza]
        return max(0.0, min(1.0, 1 - (1 - p) / self.pot))

    def _pos_atras(self, seg):
        objetivo = self.t - seg
        res = self.pos
        for t, p in self.hist:
            res = p
            if t >= objetivo:
                break
        return V2(res)

    def _lanzar(self, ctrl):
        tajo = ctrl.cortando and not self.tajo_prev
        self.tajo_prev = ctrl.cortando
        if not (ctrl.golpe or ctrl.clic or tajo):
            return
        if (self.estado != "busca" or self.bola is not None or self.bolas <= 0
                or self.cool > 0):
            return
        atras = 0.0 if (ctrl.clic and not ctrl.golpe) else (0.1 if ctrl.golpe else 0.18)
        fin = self._pos_atras(atras)
        self.bolas -= 1
        self.bola = {"fin": fin, "t": 0.0}
        self.sonidos.reproducir("lanzar")

    def _bola_pos(self):
        b = self.bola
        f = b["t"] / DUR_VUELO
        p = ORIGEN.lerp(b["fin"], 0.5 * _ease_out(f) + 0.5 * f)
        p.y -= 110 * math.sin(math.pi * f)
        return p, 1.0 - 0.45 * f

    def _resolver(self):
        fin = self.bola["fin"]
        self.bola = None
        self.cool = 0.25
        d = fin.distance_to(self.cp)
        r, _ = self.radios()
        if self.oculta > 0.5:
            texto = "¡Se escondió!"
        elif d <= r and random.random() < self.probabilidad(d):
            self.estado, self.te = "atrapando", 0.0
            self.bola_ini = fin
            self.bola_fin = V2(self.cp)
            self.capturas += 1
            self.ganados = self.sumar(PUNTOS_RAREZA[self.rareza])
            self.recompensas.append(("criatura", self.cid))
            self.nuevo = self.cid not in self.ctx.perfil.criaturas
            self.fase_tic = -1
            return
        else:
            texto = "¡Casi!" if d <= r * 1.5 else "¡Uy!"
        self.fallos += 1
        self.salto = 0.35
        self.sonidos.reproducir("fallo")
        self.flotantes.append(TextoFlotante(texto, self.cp.x, self.cp.y - 90, (255, 255, 255)))
        self.rebotes.append({"p": V2(fin), "v": V2(random.uniform(-140, 140), -320), "t": 0.0})
        if self.bolas <= 0:
            self.estado, self.te = "huye", 0.0
            self.flotantes.append(TextoFlotante("¡Se escapó!", self.cp.x, self.cp.y - 140,
                                                (255, 220, 120), vida=1.2))
            self.dir_huida = 1 if self.cp.x > ANCHO / 2 else -1

    # --- ciclo ---
    def paso(self, dt, ctrl):
        dj = dt * self.lento
        self.pos = V2(ctrl.pos)
        self.hist.append((self.t, V2(ctrl.pos)))
        while self.hist and self.hist[0][0] < self.t - 0.6:
            self.hist.popleft()
        self.cool = max(0.0, self.cool - dt)
        for a in self.arbustos:
            a.temblor = max(0.0, a.temblor - dt)
        self.te += dt
        self._lanzar(ctrl)

        if self.estado == "aparece":
            self._mover(dj * 0.3)
            if self.te >= 0.5:
                self.estado = "busca"
        elif self.estado == "busca":
            self._mover(dj)
        elif self.estado == "huye":
            self.cp.x += self.dir_huida * 800 * dt
            self.cp.y -= 80 * dt
            if self.te > 0.9:
                self._nueva()
        elif self.estado == "atrapando":
            self._paso_captura()
        elif self.estado == "espera":
            if self.te > 0.25:
                self._nueva()

        if self.bola is not None:
            self.bola["t"] += dt
            if self.bola["t"] >= DUR_VUELO:
                self._resolver()
        for r in self.rebotes:
            r["t"] += dt
            r["v"].y += 1000 * dt
            r["p"] += r["v"] * dt
        self.rebotes = [r for r in self.rebotes if r["t"] < 0.8]
        self.particulas = [p for p in self.particulas if p.actualizar(dt)]

    def _paso_captura(self):
        te = self.te
        if te < 0.35:
            return
        fase = int((te - 0.35) / 0.4)
        if fase < 3:
            if fase != self.fase_tic:
                self.fase_tic = fase
                self.sonidos.nota((330, 392, 440)[fase], 0.18)
        elif self.fase_tic < 3:
            self.fase_tic = 3
            self.sonidos.reproducir("premio")
            b = self.bola_fin
            for _ in range(5):
                explosion(self.particulas, b.x, b.y, random.choice(COLORES_CONFETI), n=8,
                          vel_min=150, vel_max=520, vida=1.3, gravedad=450, radio=7)
            self.flotantes.append(TextoFlotante("¡Atrapado!", b.x, b.y - 170, (255, 235, 90), vida=1.6, subida=50))
            self.flotantes.append(TextoFlotante(f"+{self.ganados}", b.x + 200, b.y - 50, (255, 255, 255)))
            if self.nuevo:
                self.flotantes.append(TextoFlotante("¡Nuevo!", b.x - 200, b.y - 50, (255, 140, 230), vida=1.6))
        elif te > 2.3:
            self.estado, self.te = "espera", 0.0

    # ------------------------------------------------------------------
    #  Dibujo
    # ------------------------------------------------------------------
    def _dibujar_criatura(self, p):
        s = self.escala
        h = self.oculta
        cx, cy = self.cp.x, self.cp.y
        if self.estado == "aparece":
            s *= _ease_out(self.te / 0.5)
        if self.estado == "huye":
            cy += math.sin(self.te * 30) * 6
        else:
            cy += math.sin(self.t * 4) * 4
        if self.salto > 0:
            cy -= math.sin(math.pi * (1 - self.salto / 0.4)) * 36
        s *= 1 - 0.25 * h
        cy += 18 * h
        if s <= 0.02:
            return
        if h < 0.5:
            p.blit(self.sombra, self.sombra.get_rect(center=(cx, self.cp.y + 66 * s)))
        feliz = self.fallos == 0
        dibujar_criatura(p, self.cid, cx, cy, s, self.t, feliz=feliz)

    def _dibujar_bola_grande(self, p, pos, esc, ang=0.0):
        rot = pygame.transform.rotozoom(self.sup_bola, ang, esc)
        p.blit(rot, rot.get_rect(center=(int(pos.x), int(pos.y))))

    def dibujar_juego(self, p):
        p.blit(self.bg, (0, 0))
        atras = [a for a in self.arbustos if a.base < self.cp.y + 60 * self.escala]
        delante = [a for a in self.arbustos if a not in atras]
        escondida = self.modo == "escondida" or (self.modo == "va_arbusto" and self.oculta > 0.1)
        if escondida and self.arb in atras:
            atras.remove(self.arb)
            delante.append(self.arb)
        for a in atras:
            a.dibujar(p)
        en_mundo = self.estado in ("aparece", "busca", "huye")
        if en_mundo:
            self._dibujar_criatura(p)
        for a in delante:
            a.dibujar(p)
        if self.oculta > 0.5 and self.arb is not None:
            escribir(p, self.f.grande, "?", self.arb.cx, self.arb.cy - 100 + math.sin(self.t * 6) * 6,
                     color=(255, 235, 90))
        if self.estado == "atrapando":
            self._dibujar_captura(p)
        if self.bola is not None:
            pos, esc = self._bola_pos()
            self._dibujar_bola_grande(p, pos, esc, self.bola["t"] * 500)
        for r in self.rebotes:
            esc = 0.55 * max(0.2, 1 - r["t"] / 0.8)
            self._dibujar_bola_grande(p, r["p"], esc, r["t"] * 400)
        for q in self.particulas:
            q.dibujar(p)
        if self.estado in ("busca", "aparece"):
            self._dibujar_reticula(p)
        self._dibujar_hud(p)

    def _dibujar_captura(self, p):
        te = self.te
        ini, fin = self.bola_ini, self.bola_fin
        if te < 0.35:
            f = te / 0.35
            pos = ini.lerp(fin, _ease_out(f))
            s = self.escala * (1 - f)
            if s > 0.03:
                dibujar_criatura(p, self.cid, fin.x, fin.y, s, self.t)
            self._dibujar_bola_grande(p, pos, 1.1)
            return
        fase = (te - 0.35) / 0.4
        if fase < 3:
            sac = math.sin(fase * 2 * math.pi) * 18 * (1 - (fase % 1) * 0.3)
            pos = V2(fin.x, fin.y + 20 - 8 * abs(math.sin(fase * math.pi * 2)))
            self._dibujar_bola_grande(p, pos, 1.1, sac)
            return
        k = (te - 0.35 - 1.2) / 0.75
        rebote = abs(math.sin(k * 3 * math.pi)) * 22
        a = _ease_out(k * 2)
        dibujar_criatura(p, self.cid, fin.x, fin.y - 40 - rebote, self.escala * (0.4 + 0.7 * a), self.t)
        self._dibujar_bola_grande(p, V2(fin.x, fin.y + 80), 0.7, 0)
        for i in range(5):
            ang = self.t * 2 + i * 2 * math.pi / 5
            estrella(p, fin.x + 120 * math.cos(ang), fin.y - 40 + 70 * math.sin(ang), 16)

    def _dibujar_reticula(self, p):
        r, rf = self.radios()
        x, y = self.pos.x, self.pos.y
        listo = self.bola is None and self.cool <= 0 and self.bolas > 0
        dentro = (self.oculta < 0.5 and self.pos.distance_to(self.cp) <= rf)
        if not listo:
            col = (200, 205, 215)
        elif dentro:
            col = (255, 235, 80)
        else:
            col = (255, 255, 255)
        borde = (40, 50, 90)
        pulso = 1 + 0.03 * math.sin(self.t * 8)
        pygame.draw.circle(p, borde, (int(x), int(y)), int(rf * pulso) + 3, 8)
        pygame.draw.circle(p, col, (int(x), int(y)), int(rf * pulso), 4)
        for i in range(0, 24, 2):
            a0, a1 = i * math.pi / 12 + self.t * 0.5, (i + 1) * math.pi / 12 + self.t * 0.5
            pygame.draw.line(p, col, (x + r * math.cos(a0), y + r * math.sin(a0)),
                             (x + r * math.cos(a1), y + r * math.sin(a1)), 3)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pygame.draw.line(p, borde, (x + dx * (rf - 14), y + dy * (rf - 14)), (x + dx * (rf + 12), y + dy * (rf + 12)), 8)
            pygame.draw.line(p, col, (x + dx * (rf - 12), y + dy * (rf - 12)), (x + dx * (rf + 10), y + dy * (rf + 10)), 4)

    def _dibujar_hud(self, p):
        nombre, rareza = CRIATURAS[self.cid][0], self.rareza
        escribir(p, self.f.normal, nombre, ANCHO / 2, 34)
        for i in range(rareza):
            estrella(p, ANCHO / 2 + (i - (rareza - 1) / 2) * 32, 72, 13)
        for i in range(self.bolas_max):
            x = ANCHO / 2 + (i - (self.bolas_max - 1) / 2) * 56
            sup = self.bola_hud if i < self.bolas else self.bola_hud_gris
            p.blit(sup, sup.get_rect(center=(x, 676)))
        if self.capturas == 0 and self.t < 14 and int(self.t * 2) % 2 == 0:
            escribir(p, self.f.normal, "¡Apunta y da un golpe!", ANCHO / 2, 622)
