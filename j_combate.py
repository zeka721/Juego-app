"""Combate por turnos con gestos (Ninja Mundo).

Turno del jugador (menu de 3 botones grandes, se eligen con dwell/clic/golpe):
  ATACAR  -> haz un TAJO rapido. Dano segun la velocidad; si el tajo cruza al enemigo es critico.
  GOLPEAR -> un anillo se encoge: golpe/clic (o un tajo) justo cuando se junta con el circulo.
  CARGAR  -> agita (golpes/clics/tajos) para llenar la barra de energia. Con 3 de energia el
             tercer boton pasa a ser el SUPERATAQUE (gran dano y ademas cura un corazon).
Turno del enemigo: avisa por que carril va a caer su ataque (marcas rojas en el suelo) y hay
que esquivar moviendo el cursor a un carril libre (verde). Si no se hace nada en el menu
durante unos segundos, el enemigo se aburre y ataca igual.

Mejoras de la ruleta:
  potencia -> multiplica el dano de todos los ataques.
  alcance  -> agranda la zona de critico, las ventanas de Perfecto/Bien del anillo y las
              franjas neutras (seguras) entre carriles al esquivar.
  lento    -> todos los tiempos (avisos, anillo, ventanas) duran 1/0.8 veces mas.
  vida     -> un corazon extra.   puntos -> sumar() ya los duplica.
  tiempo   -> sin efecto (el combate no tiene limite de tiempo).

Estrellas: 0 si pierde, 1 si gana, 2 si gana perdiendo un solo corazon, 3 sin perder ninguno.
Puntos (ruleta) = dano total / 2.
"""

import math
import random

import pygame

import arte
from ajustes import ANCHO, ALTO
from nucleo import (MEJORAS, Boton, Minijuego, TextoFlotante, V2, aclarar, barra, corazon,
                    corazones, escribir, estrella, explosion, oscurecer)

W3 = ANCHO / 3                       # ancho de un carril
EX, EY = ANCHO / 2, 335              # centro del enemigo
SUELO_Y = 455                        # donde empieza el suelo
ZONA_Y, ZONA_H = 470, 235            # franja de esquiva
DANO_BASE = 22.0
ESPERA_MENU = 8.0                    # segundos sin elegir antes de que el enemigo ataque
ANILLO_R0, ANILLO_RT = 260.0, 78.0   # radio inicial del anillo y radio del circulo objetivo
VENTANA_TAJO = 2.5
VENTANA_CARGA = 3.0
FASES_JEFE = (1.0, 0.9, 0.75)        # factor del tiempo de aviso por fase del jefe


def _suave(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


class Combate(Minijuego):
    id = "combate"
    titulo = "Combate"
    instruccion = "Elige tu acción y esquiva moviendo el cursor."
    gesto = "Tajo, golpe, agitar y mover el mando"
    duracion = None

    def __init__(self, ctx, nivel=1, jefe=False, criatura=None, companera=None):
        super().__init__(ctx, nivel)
        self.jefe = bool(jefe)
        self.companera = companera if companera in arte.CRIATURAS else None
        if self.jefe:
            self.titulo = "Rey Grunón"
            self.fondo_arriba, self.fondo_abajo = (85, 55, 140), (205, 120, 165)
            self.nombre = "Rey Grunón"
            self.ident = None
            self.vida_max = 450.0
        else:
            self.fondo_arriba, self.fondo_abajo = (125, 195, 255), (210, 238, 255)
            self.ident = criatura or self._elegir_criatura()
            self.nombre = arte.CRIATURAS[self.ident][0]
            self.vida_max = 140.0 + 8.0 * (self.nivel - 1)
        self.vida = self.vida_max
        self.vida_vis = self.vida_max
        self.vidas_max = 3 + self.mej.vidas_extra()
        self.vidas = self.vidas_max
        self.energia = 0.0
        self.dano_total = 0.0
        self._resto = 0.0
        self.fase_jefe = 1
        self.enojado = False
        self.potencia = self.mej.mult("potencia")
        self.alcance = self.mej.mult("alcance")
        self.margen_carril = max(24.0, 80.0 - 12.0 * (self.nivel - 1)) * self.alcance
        self.necesarios = 3 + (1 if self.nivel >= 3 else 0) + (1 if self.nivel >= 5 else 0)
        self.anillo_T = max(1.1, 1.9 - 0.12 * (self.nivel - 1))
        # estado
        self.fase = "intro"
        self.t_fase = 0.0
        self.botones, self.pistas = [], []
        self.t_afk = 0.0
        self.particulas, self.numeros = [], []
        self.temblor = self.retroceso = self.parpadeo = self.flash_rojo = self.inmune = 0.0
        self.dir_retro = 1
        self.hero_x = ANCHO / 2
        self.pos = V2(ANCHO / 2, ALTO / 2)
        self._cort_prev = False
        self.tj_activo = self.tj_bloq = False
        self.tj_vmax, self.tj_cruza, self.q_visible = 0.0, False, 0.0
        self.rastro = []
        self.hits, self.ult_pulso = 0, -1.0
        self.res_anillo = None
        self.super_hecho = False
        self.olas, self.ola_i, self.aviso_t = [[1]], 0, 1.8
        self.golpeado_ataque = False
        self.impacto_lanes = []
        self._pre_render()

    def calcular_metas(self):
        return (1, 2, 3)

    # ------------------------------------------------------------------ preparacion
    def _elegir_criatura(self):
        rarezas = {1: (1,), 2: (1, 2), 3: (2,), 4: (2, 3), 5: (3,)}[self.nivel]
        ids = [i for i, c in arte.CRIATURAS.items() if c[1] in rarezas]
        ids = [i for i in ids if i != self.companera] or ids
        nuevos = [i for i in ids if i not in self.ctx.perfil.criaturas]
        return random.choice(nuevos or ids)

    def _pre_render(self):
        """Dibuja una sola vez el escenario, las zonas de esquiva, la bola y el heroe."""
        suelo_a, suelo_b = ((118, 196, 120), (104, 183, 110)) if not self.jefe else ((96, 80, 126), (82, 68, 110))
        self.decor = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        colina = (150, 215, 140) if not self.jefe else (120, 90, 150)
        for cx, r in ((180, 190), (560, 240), (1000, 210), (1280, 170)):
            pygame.draw.ellipse(self.decor, colina, (cx - r, SUELO_Y - r * 0.38, 2 * r, r * 0.8))
        if not self.jefe:
            pygame.draw.circle(self.decor, (255, 240, 150), (1130, 130), 48)
            for cx, cy in ((250, 160), (860, 120)):
                for dx, dy, r in ((-40, 6, 30), (0, -8, 40), (42, 6, 30)):
                    pygame.draw.circle(self.decor, (255, 255, 255, 235), (cx + dx, cy + dy), r)
        for i in range(3):
            c = suelo_a if i % 2 == 0 else suelo_b
            pygame.draw.rect(self.decor, c, (i * W3, SUELO_Y, W3 + 1, ALTO - SUELO_Y))
        pygame.draw.line(self.decor, oscurecer(suelo_a, 0.3), (0, SUELO_Y), (ANCHO, SUELO_Y), 5)
        for i in (1, 2):
            for y in range(SUELO_Y + 14, ALTO, 34):
                pygame.draw.line(self.decor, (255, 255, 255, 150), (i * W3, y), (i * W3, y + 18), 4)
        self.decor = self.decor.convert_alpha()
        m = int(self.margen_carril)
        w = int(W3 - 2 * m)
        self.zonas = []
        for i in range(3):
            rojo = pygame.Surface((w, ZONA_H), pygame.SRCALPHA)
            pygame.draw.rect(rojo, (255, 50, 50, 170), rojo.get_rect(), border_radius=26)
            pygame.draw.rect(rojo, (255, 40, 40, 255), rojo.get_rect(), 6, border_radius=26)
            escribir(rojo, self.f.enorme, "!", w // 2, ZONA_H // 2, color=(255, 255, 255),
                     contorno=(200, 20, 20), grosor=4)
            verde = pygame.Surface((w, ZONA_H), pygame.SRCALPHA)
            pygame.draw.rect(verde, (90, 255, 130, 70), verde.get_rect(), border_radius=26)
            pygame.draw.rect(verde, (60, 220, 100, 220), verde.get_rect(), 5, border_radius=26)
            self.zonas.append((rojo.convert_alpha(), verde.convert_alpha()))
        col = (255, 150, 60) if self.jefe else arte.CRIATURAS[self.ident][2]
        self.bola = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(self.bola, oscurecer(col, 0.55), (55, 55), 50)
        pygame.draw.circle(self.bola, col, (55, 55), 44)
        pygame.draw.circle(self.bola, aclarar(col, 0.6), (38, 38), 12)
        for lado in (-1, 1):
            pygame.draw.line(self.bola, (40, 20, 40), (55 + lado * 6, 47), (55 + lado * 28, 36), 5)
            pygame.draw.circle(self.bola, (255, 255, 255), (55 + lado * 17, 56), 9)
            pygame.draw.circle(self.bola, (40, 20, 40), (55 + lado * 17, 58), 4)
        h = pygame.Surface((90, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(h, (45, 55, 120), (19, 52, 52, 62))
        pygame.draw.ellipse(h, (25, 30, 80), (19, 52, 52, 62), 3)
        pygame.draw.circle(h, (60, 70, 150), (45, 38), 28)
        pygame.draw.circle(h, (25, 30, 80), (45, 38), 28, 3)
        pygame.draw.rect(h, (255, 220, 180), (25, 30, 40, 16), border_radius=7)
        for dx in (-8, 8):
            pygame.draw.circle(h, (30, 20, 40), (45 + dx, 38), 3)
        pygame.draw.rect(h, (230, 60, 70), (17, 18, 56, 9), border_radius=4)
        pygame.draw.polygon(h, (230, 60, 70), [(70, 20), (88, 12), (82, 28)])
        pygame.draw.line(h, (210, 215, 230), (66, 86), (80, 54), 7)
        pygame.draw.line(h, (120, 80, 50), (64, 92), (67, 84), 7)
        self.heroe = h

    # ------------------------------------------------------------------ utilidades
    def _ir(self, fase, ctrl=None):
        self.fase = fase
        self.t_fase = 0.0
        if fase == "menu":
            self._crear_botones()
            self.t_afk = 0.0
            self.rastro = []
        if fase in ("atacar", "golpear", "cargar"):
            self.tj_activo = False
            self.tj_bloq = bool(ctrl and ctrl.cortando)
            self.tj_vmax, self.tj_cruza, self.q_visible = 0.0, False, 0.0
            self.hits, self.ult_pulso, self.res_anillo, self.rastro = 0, -1.0, None, []

    def _crear_botones(self):
        sup = self.energia >= 3.0 - 1e-6
        defs = [("ATACAR", (235, 90, 70), "Tajo"), ("GOLPEAR", (70, 140, 235), "Golpe"),
                ("¡SUPER!", (240, 160, 20), "Gran ataque") if sup else ("CARGAR", (70, 185, 100), "Agitar")]
        self.botones, self.pistas = [], []
        for i, (txt, col, pista) in enumerate(defs):
            rect = pygame.Rect(0, 0, 340, 110)
            rect.center = (220 + 420 * i, 620)
            self.botones.append(Boton(rect, txt, col, espera=0.7))
            self.pistas.append(pista)

    def _pulso(self, ctrl):
        """Golpe, clic o inicio de un tajo (sirve para quien no pueda sacudir el mando)."""
        return ctrl.golpe or ctrl.clic or (ctrl.cortando and not self._cort_prev)

    def _rect_enemigo(self):
        w, h = (330, 340) if self.jefe else (270, 250)
        r = pygame.Rect(0, 0, int(w * self.alcance), int(h * self.alcance))
        r.center = (EX, EY)
        return r

    def _cruza(self, p1, p2):
        r = self._rect_enemigo()
        return bool(r.clipline(p1.x, p1.y, p2.x, p2.y)) or r.collidepoint(p2.x, p2.y)

    def _num_fase_jefe(self):
        f = self.vida / self.vida_max
        return 1 if f > 0.66 else (2 if f > 0.33 else 3)

    def _color_enemigo(self):
        return (160, 100, 220) if self.jefe else arte.CRIATURAS[self.ident][2]

    def _dar_puntos(self, real):
        self._resto += real / 2.0
        n = int(self._resto)
        self._resto -= n
        if n:
            self.sumar(n)

    def _herir(self, dano, etiqueta=None, fuerte=False):
        real = min(dano, self.vida)
        self.vida -= real
        self.dano_total += real
        self._dar_puntos(real)
        self.retroceso = 0.7
        self.parpadeo = 0.7
        self.dir_retro = random.choice((-1, 1))
        self.temblor = max(self.temblor, 0.4 if fuerte else 0.2)
        self.numeros.append(TextoFlotante(f"-{int(round(dano))}", EX + random.uniform(-70, 70),
                                          EY - 90, (255, 235, 90), vida=1.2, subida=90))
        if etiqueta:
            self.flotantes.append(TextoFlotante(etiqueta, EX + 190, EY - 120, (255, 255, 255), vida=1.2))
        explosion(self.particulas, EX, EY, self._color_enemigo(), n=22 if fuerte else 14,
                  vel_min=120, vel_max=420, vida=0.8, gravedad=400, radio=7)
        explosion(self.particulas, EX, EY, (255, 240, 150), n=8, vel_min=100, vel_max=300, vida=0.6, radio=5)
        self.sonidos.reproducir("golpe")
        if self.vida <= 0.01:
            self.vida = 0.0
            self._victoria()

    def _pausa(self):
        self._ir("pausa")

    # ------------------------------------------------------------------ ciclo
    def paso(self, dt_real, ctrl):
        dt = dt_real * self.lento
        self.pos = V2(ctrl.pos)
        self.t_fase += dt
        self._efectos(dt)
        getattr(self, "_f_" + self.fase)(dt, dt_real, ctrl)
        self._cort_prev = bool(ctrl.cortando)

    def _efectos(self, dt):
        self.particulas = [p for p in self.particulas if p.actualizar(dt)]
        self.numeros = [n for n in self.numeros if n.actualizar(dt)]
        self.temblor = max(0.0, self.temblor - dt)
        self.retroceso = max(0.0, self.retroceso - dt)
        self.parpadeo = max(0.0, self.parpadeo - dt)
        self.flash_rojo = max(0.0, self.flash_rojo - dt)
        self.inmune = max(0.0, self.inmune - dt)
        self.vida_vis += (self.vida - self.vida_vis) * min(1.0, 6 * dt)
        if abs(self.vida_vis - self.vida) < 0.2:
            self.vida_vis = self.vida
        objetivo = max(70.0, min(ANCHO - 70.0, self.pos.x))
        self.hero_x += (objetivo - self.hero_x) * min(1.0, 18 * dt)

    # ------------------------------------------------------------------ fases del jugador
    def _f_intro(self, dt, dt_real, ctrl):
        if self.t_fase == dt:
            self.sonidos.reproducir("rugido" if self.jefe else "pop")
        if self.t_fase >= 1.7:
            self._ir("menu")

    def _f_menu(self, dt, dt_real, ctrl):
        elegido = None
        for i, b in enumerate(self.botones):
            if b.actualizar(dt_real, ctrl):
                elegido = i
        if any(b.encima for b in self.botones):
            self.t_afk = 0.0
        else:
            self.t_afk += dt
        if elegido is not None:
            self.sonidos.reproducir("click")
            if elegido == 0:
                self._ir("atacar", ctrl)
            elif elegido == 1:
                self._ir("golpear", ctrl)
            elif self.energia >= 3.0 - 1e-6:
                self.super_hecho = False
                self._ir("super", ctrl)
            else:
                self._ir("cargar", ctrl)
        elif self.t_afk >= ESPERA_MENU:
            self._turno_enemigo(afk=True)

    def _seguir_tajo(self, ctrl):
        """Sigue un tajo. Devuelve (vel_max, cruza) cuando termina, o None."""
        if ctrl.cortando:
            if self.t_fase < 0.2:
                self.tj_bloq = True
            if not self.tj_bloq:
                if not self.tj_activo:
                    self.tj_activo, self.tj_vmax, self.tj_cruza = True, 0.0, False
                self.tj_vmax = max(self.tj_vmax, ctrl.vel)
                self.q_visible = max(self.q_visible, self._calidad_tajo(self.tj_vmax))
                if self._cruza(ctrl.p1, ctrl.p2):
                    self.tj_cruza = True
                self.rastro.append(V2(ctrl.p2))
                self.rastro = self.rastro[-24:]
            return None
        self.tj_bloq = False
        if self.tj_activo:
            self.tj_activo = False
            return (self.tj_vmax, self.tj_cruza)
        return None

    @staticmethod
    def _calidad_tajo(vmax):
        return max(0.0, min(1.0, (vmax - 1000.0) / 3500.0))

    def _f_atacar(self, dt, dt_real, ctrl):
        res = self._seguir_tajo(ctrl)
        if res is None and self.t_fase >= VENTANA_TAJO:
            res = (self.tj_vmax, self.tj_cruza) if self.tj_activo else "nada"
            self.tj_activo = False
        if res is None:
            return
        if res == "nada":
            self.flotantes.append(TextoFlotante("¡Sin tajo!", EX, EY - 40, (255, 255, 255)))
            self.sonidos.reproducir("error")
            self._pausa()
            return
        vmax, cruza = res
        q = self._calidad_tajo(vmax)
        self.q_visible = q
        dano = DANO_BASE * (0.55 + 0.75 * q) * (1.5 if cruza else 1.0) * self.potencia
        self.sonidos.reproducir("corte")
        self._pausa()
        self._herir(dano, "¡CRÍTICO!" if cruza else ("¡Fuerte!" if q > 0.7 else None), fuerte=cruza)

    def _radio_anillo(self, t):
        return ANILLO_R0 - (ANILLO_R0 - ANILLO_RT) / self.anillo_T * t

    def _f_golpear(self, dt, dt_real, ctrl):
        if self.res_anillo is not None:
            return
        r = self._radio_anillo(self.t_fase)
        error = abs(r - ANILLO_RT)
        if self.t_fase > 0.35 and self._pulso(ctrl):
            if error <= 16 * self.alcance:
                txt, mult = "¡Perfecto!", 1.7
            elif error <= 42 * self.alcance:
                txt, mult = "¡Bien!", 1.0
            else:
                txt, mult = "¡Casi!", 0.4
        elif r <= 22:
            txt, mult = "¡Muy tarde!", 0.4
        else:
            return
        self.res_anillo = (max(r, 22.0), txt)
        self.q_visible = mult
        self._pausa()
        self._herir(DANO_BASE * mult * self.potencia, txt, fuerte=mult > 1.5)

    def _f_cargar(self, dt, dt_real, ctrl):
        if self.t_fase > 0.3 and self._pulso(ctrl) and self.t_fase - self.ult_pulso >= 0.12:
            self.hits += 1
            self.ult_pulso = self.t_fase
            self.sonidos.nota(330 + 60 * self.hits, 0.12)
            explosion(self.particulas, 640 + (self.hits - self.necesarios / 2) * 90, 600,
                      (255, 235, 90), n=6, vel_min=60, vel_max=220, vida=0.5, gravedad=100)
        if self.hits >= self.necesarios or self.t_fase >= VENTANA_CARGA:
            ganancia = min(1.0, self.hits / self.necesarios)
            antes = self.energia
            self.energia = min(3.0, self.energia + ganancia)
            if self.energia >= 3.0 - 1e-6 and antes < 3.0 - 1e-6:
                texto, snd = "¡SUPER listo!", "premio"
            elif ganancia >= 1.0:
                texto, snd = "¡Cargado!", "ok"
            elif ganancia > 0:
                texto, snd = "¡Casi! Agita más", "ok"
            else:
                texto, snd = "¡Agita el mando!", "error"
            self.flotantes.append(TextoFlotante(texto, EX, EY - 60, (255, 240, 120), vida=1.3))
            self.sonidos.reproducir(snd)
            self._pausa()

    def _f_super(self, dt, dt_real, ctrl):
        if not self.super_hecho and self.t_fase >= 0.8:
            self.super_hecho = True
            self.energia = 0.0
            if self.vidas < self.vidas_max:
                self.vidas += 1
                self.flotantes.append(TextoFlotante("¡+1 corazón!", 190, 150, (255, 130, 150), vida=1.5))
            self.sonidos.reproducir("premio")
            self._herir(DANO_BASE * 3.2 * self.potencia, "¡SUPER!", fuerte=True)
        if self.fase == "super" and self.t_fase >= 1.7:
            self._pausa()

    def _f_pausa(self, dt, dt_real, ctrl):
        if self.t_fase < 0.95:
            return
        if self.jefe:
            nueva = self._num_fase_jefe()
            if nueva > self.fase_jefe:
                self.fase_jefe = nueva
                self.enojado = True
                self.temblor = 0.9
                self.sonidos.reproducir("rugido")
                self._ir("rugido_fase")
                return
        self._turno_enemigo()

    def _f_rugido_fase(self, dt, dt_real, ctrl):
        if self.t_fase >= 1.5:
            self._turno_enemigo()

    # ------------------------------------------------------------------ turno del enemigo
    def _turno_enemigo(self, afk=False):
        self.rastro = []
        if not afk and not self.jefe and random.random() < {1: 0.25, 2: 0.1}.get(self.nivel, 0.0):
            self.flotantes.append(TextoFlotante("¡Tropezó!", EX, EY - 40, (255, 255, 255), vida=1.2))
            self._ir("tropiezo")
            return
        if self.jefe and self.fase_jefe >= 2 and random.random() < (0.15 if self.fase_jefe == 2 else 0.2):
            self.sonidos.reproducir("rugido")
            self.temblor = 0.7
            self._ir("rugido")
            return
        self.olas = self._generar_olas()
        self.ola_i = 0
        self.golpeado_ataque = False
        self.aviso_t = self._tiempo_aviso(True)
        self.sonidos.nota(500, 0.15)
        self._ir("aviso")

    def _f_tropiezo(self, dt, dt_real, ctrl):
        if self.t_fase >= 1.3:
            self._ir("menu")

    def _f_rugido(self, dt, dt_real, ctrl):
        if self.t_fase >= 1.3:
            self._ir("menu")

    def _tiempo_aviso(self, primera):
        base = max(0.9, 1.8 - 0.2 * (self.nivel - 1))
        if self.jefe:
            base *= FASES_JEFE[self.fase_jefe - 1]
        if not primera:
            base *= 0.85
        return max(0.8, base)

    def _generar_olas(self):
        carriles = (0, 1, 2)

        def uno(prev=None):
            return [random.choice([c for c in carriles if c != prev])]

        def dos():
            libre = random.choice(carriles)
            return [c for c in carriles if c != libre]

        a = uno()
        b = uno(a[0])
        c = uno(b[0])
        if self.jefe:
            if self.fase_jefe == 1:
                return [a]
            if self.fase_jefe == 2:
                return random.choice(([dos()], [a, b]))
            return random.choice(([dos()], [a, b, c], [dos(), c], [a, dos()]))
        if self.nivel == 4:
            return [a, b] if random.random() < 0.35 else [a]
        if self.nivel == 5:
            r = random.random()
            return [a, b] if r < 0.5 else ([dos()] if r < 0.65 else [a])
        return [a]

    def _en_peligro(self, x, lanes):
        m = self.margen_carril
        return any(i * W3 + m <= x <= (i + 1) * W3 - m for i in lanes)

    def _f_aviso(self, dt, dt_real, ctrl):
        if self.t_fase < self.aviso_t:
            return
        lanes = self.olas[self.ola_i]
        self.impacto_lanes = lanes
        self.temblor = max(self.temblor, 0.3)
        for i in lanes:
            explosion(self.particulas, i * W3 + W3 / 2, ZONA_Y + 110, self._color_enemigo(), n=14,
                      vel_min=100, vel_max=380, vida=0.7, gravedad=500, radio=7)
        self.sonidos.reproducir("golpe")
        if self._en_peligro(ctrl.pos.x, lanes) and not self.golpeado_ataque:
            self.golpeado_ataque = True
            self.vidas -= 1
            self.flash_rojo = 0.45
            self.inmune = 0.9
            self.flotantes.append(TextoFlotante("¡Ay!", self.hero_x, 560, (255, 120, 120), vida=1.1))
            self.sonidos.reproducir("fallo")
            if self.vidas <= 0:
                self._derrota()
                return
        elif not self._en_peligro(ctrl.pos.x, lanes):
            self.flotantes.append(TextoFlotante("¡Esquivado!", self.hero_x, 560, (190, 255, 190), vida=0.9))
            self.sonidos.reproducir("ok")
        self._ir("impacto")

    def _f_impacto(self, dt, dt_real, ctrl):
        if self.t_fase < 0.65:
            return
        self.ola_i += 1
        if self.ola_i < len(self.olas):
            self.aviso_t = self._tiempo_aviso(False)
            self._ir("aviso")
        else:
            self._ir("menu")

    # ------------------------------------------------------------------ final
    def _victoria(self):
        self.ganado = True
        if not self.jefe:
            self.recompensas.append(("criatura", self.ident))
        self.sonidos.reproducir("premio")
        self.temblor = 0.3
        self._ir("victoria")

    def _f_victoria(self, dt, dt_real, ctrl):
        if random.random() < 0.25:
            explosion(self.particulas, random.uniform(300, 980), random.uniform(120, 420),
                      random.choice(((255, 220, 90), (255, 130, 160), (130, 220, 255))),
                      n=8, vel_min=80, vel_max=300, vida=0.9, gravedad=300, radio=6)
        if self.t_fase >= 3.2:
            self.terminar("¡Ganaste!")

    def _derrota(self):
        self.ganado = False
        self.sonidos.reproducir("fin")
        self._ir("derrota")

    def _f_derrota(self, dt, dt_real, ctrl):
        if self.t_fase >= 2.4:
            self.terminar("¡Casi lo logras!")

    # ------------------------------------------------------------------ dibujo
    def _dib_enemigo(self, p):
        u = self.retroceso / 0.7
        s = math.sin(math.pi * (1 - u)) if self.retroceso > 0 else 0.0
        x = EX + self.dir_retro * 55 * s
        y = EY + math.sin(self.t * 2.6) * 6 - 25 * s
        esc = 1.0
        if self.fase == "intro":
            y -= 420 * (1 - _suave(self.t_fase / 0.9)) ** 2
        elif self.fase == "aviso":
            esc = 1.0 + 0.04 * math.sin(self.t * 16)
            x += math.sin(self.t * 40) * 4
        elif self.fase in ("rugido", "rugido_fase"):
            esc = 1.0 + 0.08 * abs(math.sin(self.t_fase * 9))
        elif self.fase == "tropiezo":
            x += 40 * math.sin(self.t_fase * 6) * (1 - self.t_fase / 1.4)
        if self.temblor > 0:
            x += random.uniform(-1, 1) * min(12.0, 40 * self.temblor)
            y += random.uniform(-1, 1) * min(12.0, 40 * self.temblor)
        # sombra
        ancho = (330 if self.jefe else 230) * (1 + (EY - y) / 500)
        pygame.draw.ellipse(p, (60, 100, 70) if not self.jefe else (50, 35, 70),
                            (EX - ancho / 2, SUELO_Y + 2, ancho, 30))
        golpeado = self.parpadeo > 0 and int(self.parpadeo * 16) % 2 == 0
        feliz = self.fase in ("victoria", "intro", "menu", "pausa") and not golpeado
        if self.fase == "victoria" and self.jefe:
            tmp = pygame.Surface((620, 560), pygame.SRCALPHA)
            arte.dibujar_jefe(tmp, 310, 300, 0.85, self.t, enojado=False, golpeado=False)
            v = _suave(self.t_fase / 1.8)
            tmp = pygame.transform.rotozoom(tmp, v * 540, max(0.05, 1 - v * 0.95))
            tmp.set_alpha(int(255 * (1 - v)))
            p.blit(tmp, tmp.get_rect(center=(x, y)))
            return
        if self.jefe:
            arte.dibujar_jefe(p, x, y, 0.85 * esc, self.t, enojado=self.enojado or self.fase == "aviso",
                              golpeado=golpeado)
        elif not (golpeado and int(self.parpadeo * 32) % 2):
            arte.dibujar_criatura(p, self.ident, x, y, 2.1 * esc, self.t, feliz=feliz)
        if self.fase == "victoria" and not self.jefe:
            for k in range(5):
                tt = (self.t_fase * 0.8 + k * 0.2) % 1.0
                corazon(p, EX - 160 + k * 80, EY - 110 - 140 * tt, 14 + 6 * (1 - tt))

    def _banner(self, p, texto, y=105, fuente=None, color=(255, 255, 255)):
        escribir(p, fuente or self.f.grande, texto, ANCHO / 2, y, color=color)

    def _dib_zonas(self, p):
        lanes = self.olas[self.ola_i]
        u = min(1.0, self.t_fase / self.aviso_t) if self.fase == "aviso" else 1.0
        pulso = 0.5 + 0.5 * math.sin(self.t * 14)
        x_hero = self.pos.x
        m = self.margen_carril
        for i in range(3):
            rojo, verde = self.zonas[i]
            x0 = i * W3 + m
            if i in lanes:
                a = int((200 + 55 * pulso) if self.fase == "aviso" else 140 * (1 - self.t_fase / 0.65))
                rojo.set_alpha(max(0, min(255, a)))
                p.blit(rojo, (x0, ZONA_Y))
                if self.fase == "aviso":
                    cx = i * W3 + W3 / 2
                    # bola que cae (acelera hasta tocar el suelo justo al acabar el aviso)
                    by = -90 + (ZONA_Y + 120 + 90) * u * u
                    p.blit(self.bola, self.bola.get_rect(center=(cx, by)))
                    if self._en_peligro(x_hero, lanes):
                        escribir(p, self.f.normal, "¡Muévete!", cx, ZONA_Y + 190)
            elif self.fase == "aviso":
                verde.set_alpha(int(150 + 90 * pulso))
                p.blit(verde, (x0, ZONA_Y))
                estrella(p, x0 + (W3 - 2 * m) / 2, ZONA_Y + 70, 34 + 6 * pulso)
        if self.fase == "impacto":
            v = self.t_fase / 0.65
            for i in self.impacto_lanes:
                cx = i * W3 + W3 / 2
                r = 50 + 190 * v
                pygame.draw.ellipse(p, (255, 235, 140), (cx - r, ZONA_Y + 120 - r * 0.28, 2 * r, r * 0.56),
                                    max(1, int(10 * (1 - v))))

    def _dib_heroe(self, p):
        if self.inmune > 0 and int(self.inmune * 14) % 2:
            return
        y = 668 + (6 * math.sin(self.t * 12) if self.fase == "aviso" else 0)
        pygame.draw.ellipse(p, (40, 70, 50), (self.hero_x - 40, 656, 80, 22))
        p.blit(self.heroe, self.heroe.get_rect(midbottom=(self.hero_x, y)))

    def _dib_companera(self, p):
        """La criatura amiga mira el combate desde la izquierda; salta al acertar y se encoge al recibir dano."""
        if self.companera is None or self.fase in ("victoria", "derrota"):
            return
        x, y, esc = 175, 350, 1.0
        y += math.sin(self.t * 3.0) * 5
        if self.retroceso > 0:
            y -= 38 * math.sin(math.pi * (1 - self.retroceso / 0.7))
        if self.flash_rojo > 0:
            esc = 0.9
            x += math.sin(self.t * 70) * 6
        if self.fase == "intro":
            esc *= _suave(self.t_fase / 0.6)
        if esc <= 0.02:
            return
        pygame.draw.ellipse(p, (40, 90, 50), (x - 55 * esc, 350 + 60, 110 * esc, 22))
        arte.dibujar_criatura(p, self.companera, x, y, esc, self.t, feliz=self.flash_rojo <= 0)
        escribir(p, self.f.chica, arte.CRIATURAS[self.companera][0], x, 450)

    def _dib_menu(self, p):
        self._banner(p, "Tu turno: elige", 482)
        barra(p, (500, 508, 280, 8), 1 - self.t_afk / ESPERA_MENU, color=(255, 255, 255),
              color_fondo=(100, 120, 150))
        for b, pista in zip(self.botones, self.pistas):
            escribir(p, self.f.normal, pista, b.rect.centerx, b.rect.top - 22)
            if b.texto.startswith("¡SUPER"):
                b.color = (240, 160, 20) if int(self.t * 4) % 2 else (255, 200, 60)
            b.dibujar(p, self.f.grande)

    def _dib_tajo(self, p):
        if len(self.rastro) > 1:
            pts = [(q.x, q.y) for q in self.rastro]
            pygame.draw.lines(p, (255, 220, 90), False, pts, 14)
            pygame.draw.lines(p, (255, 255, 255), False, pts, 6)
        if self.fase == "atacar" and not self.tj_activo and self.t_fase < VENTANA_TAJO:
            mov = 14 * math.sin(self.t * 8)
            for lado in (-1, 1):
                x = EX + lado * (300 + mov * lado)
                pygame.draw.polygon(p, (255, 255, 255), [(x + lado * 30, EY), (x - lado * 20, EY - 40), (x - lado * 20, EY + 40)])
            self._barra_texto(p, "Fuerza", self.q_visible, (255, 150, 60))
        if self.fase == "atacar":
            barra(p, (500, 690, 280, 9), 1 - self.t_fase / VENTANA_TAJO, color=(255, 255, 255), color_fondo=(100, 120, 150))

    def _barra_texto(self, p, texto, frac, color):
        escribir(p, self.f.normal, texto, ANCHO / 2, 575)
        barra(p, (390, 600, 500, 40), frac, color=color)

    def _dib_anillo(self, p):
        if self.res_anillo is not None:
            r, _ = self.res_anillo
        else:
            r = self._radio_anillo(self.t_fase)
        err = abs(r - ANILLO_RT)
        color = (255, 255, 255)
        if err <= 16 * self.alcance:
            color = (255, 215, 40)
        elif err <= 42 * self.alcance:
            color = (120, 235, 130)
        cir = pygame.Surface((2 * 90 + 8, 2 * 90 + 8), pygame.SRCALPHA)
        pygame.draw.circle(cir, (255, 255, 255, 70), (98, 98), int(ANILLO_RT))
        p.blit(cir, cir.get_rect(center=(EX, EY)))
        pygame.draw.circle(p, (255, 255, 255), (EX, EY), int(ANILLO_RT), 8)
        pygame.draw.circle(p, (60, 60, 90), (EX, EY), int(ANILLO_RT) + 6, 3)
        pygame.draw.circle(p, color, (EX, EY), int(max(6, r)), 12)
        if self.res_anillo is None:
            escribir(p, self.f.normal, "¡Golpe!", ANCHO / 2, 600)

    def _dib_carga(self, p):
        escribir(p, self.f.normal, f"{self.hits} / {self.necesarios}", ANCHO / 2, 575)
        barra(p, (340, 600, 600, 50), self.hits / self.necesarios, color=(255, 215, 60))
        barra(p, (500, 670, 280, 9), 1 - self.t_fase / VENTANA_CARGA, color=(255, 255, 255), color_fondo=(100, 120, 150))
        t = 1 + 0.12 * math.sin(self.t * 14)
        for k in range(self.hits):
            estrella(p, 460 + k * 90, 535, 26 * t)

    def _dib_super(self, p):
        for k in range(10):
            v = _suave((self.t_fase - 0.07 * k) / 0.6)
            if 0 < v < 1:
                ang = k * 0.63
                sx, sy = EX + math.cos(ang) * 700, EY + math.sin(ang) * 520
                estrella(p, sx + (EX - sx) * v, sy + (EY - sy) * v, 40 + 20 * v)
        if 0.8 <= self.t_fase < 1.0:
            f = pygame.Surface((ANCHO, ALTO))
            f.fill((255, 255, 220))
            f.set_alpha(int(220 * (1 - (self.t_fase - 0.8) / 0.2)))
            p.blit(f, (0, 0))

    def _dib_fin(self, p):
        if self.fase == "victoria":
            escribir(p, self.f.enorme, "¡Ganaste!", ANCHO / 2, 120, color=(255, 240, 120))
            texto = f"¡Venciste al {self.nombre}!" if self.jefe else f"¡{self.nombre} es tu amigo!"
            escribir(p, self.f.grande, texto, ANCHO / 2, 495)
            for i in range(3):
                lleno = i < self.estrellas()
                estrella(p, ANCHO / 2 + (i - 1) * 90, 590, 38 if lleno else 30,
                         (255, 210, 60) if lleno else (200, 205, 220),
                         (160, 110, 20) if lleno else (140, 145, 165))
        elif self.fase == "derrota":
            self._banner(p, "¡Casi! ¡Otra vez!", 120, self.f.enorme)

    def dibujar_juego(self, p):
        p.blit(self.decor, (0, 0))
        self._dib_enemigo(p)
        self._dib_companera(p)
        f = self.fase
        if f in ("aviso", "impacto"):
            self._dib_zonas(p)
            self._dib_heroe(p)
            if f == "aviso":
                txt = "¡Cuidado!" if (self.ola_i == 0 and self.t_fase < 0.6 * self.aviso_t and self.aviso_t >= 1.2) else "¡Esquiva!"
                self._banner(p, txt, 105, color=(255, 120, 110))
        elif f == "menu":
            self._dib_menu(p)
        elif f == "atacar":
            self._banner(p, "¡Haz un TAJO!")
            self._dib_tajo(p)
        elif f == "golpear":
            self._banner(p, "¡Golpea al juntarse!")
            self._dib_anillo(p)
        elif f == "cargar":
            self._banner(p, "¡Agita el mando!")
            self._dib_carga(p)
        elif f == "super":
            self._dib_super(p)
        elif f == "pausa":
            self._dib_tajo(p)
            if self.res_anillo is not None:
                self._dib_anillo(p)
        elif f == "intro":
            self._banner(p, f"¡{self.nombre} te reta!" if self.jefe else f"¡Un {self.nombre} salvaje!", 105)
        elif f == "rugido_fase":
            self._banner(p, "¡Grrr! ¡Se enoja!", 105, color=(255, 150, 120))
        elif f == "rugido":
            self._banner(p, "¡GRRR!", 105, color=(255, 150, 120))
        elif f == "tropiezo":
            self._banner(p, "¡Se tropezó!", 105)
        elif f in ("victoria", "derrota"):
            self._dib_fin(p)
        for q in self.particulas:
            q.dibujar(p)
        for n in self.numeros:
            n.dibujar(p, self.f.grande)
        # barra de vida del enemigo
        escribir(p, self.f.normal, self.nombre, ANCHO / 2, 18)
        frac = self.vida_vis / self.vida_max
        color = (90, 205, 110) if frac > 0.5 else ((250, 200, 60) if frac > 0.25 else (240, 80, 80))
        barra(p, (400, 38, 480, 28), frac, color=color)
        if self.jefe:
            for k in (1, 2):
                x = 400 + 480 * k / 3
                pygame.draw.line(p, (255, 255, 255), (x, 40), (x, 64), 3)
        if self.flash_rojo > 0:
            s = pygame.Surface((ANCHO, ALTO))
            s.fill((255, 40, 40))
            s.set_alpha(int(110 * self.flash_rojo / 0.45))
            p.blit(s, (0, 0))

    def dibujar_hud(self, p):
        escribir(p, self.f.grande, f"Puntos: {self.puntos}", 24, 34, ancla="izq")
        corazones(p, self.vidas, self.vidas_max, 42, 92, r=17, sep=44)
        escribir(p, self.f.chica, "Energía", 24, 128, ancla="izq")
        barra(p, (24, 142, 190, 20), self.energia / 3.0, color=(255, 215, 60))
        for k in (1, 2):
            pygame.draw.line(p, (255, 255, 255), (24 + 190 * k / 3, 144), (24 + 190 * k / 3, 160), 2)
        for i, nombre in enumerate(self.mej.activas):
            escribir(p, self.f.chica, MEJORAS[nombre][1], ANCHO - 20, 70 + i * 24,
                     color=(255, 235, 140), ancla="der")

    def estrellas(self):
        if self.ganado is not True:
            return 0
        perdidos = self.vidas_max - self.vidas
        return 3 if perdidos <= 0 else (2 if perdidos == 1 else 1)
