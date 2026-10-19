"""Pesca por mundos: apunta, lanza, espera, clava y forcejea con peces y animales marinos de evento.

El juego es un corte lateral: cielo y barco arriba, agua con profundidad y fondo marino abajo.
El mundo (pesca_datos.MUNDOS) decide los peces, el alcance, la profundidad y la estabilidad; la caña, la
cuerda y el anzuelo (1 a 5 estrellas, se gastan) cambian la fuerza, la tension que aguanta la linea y el clavado.
"""

import math
import random

import pygame

import arte
import arte_mar
import catalogo  # noqa: F401
import pesca_datos
import cocina_datos  # noqa: F401  (registra langostino y calamar)
from ajustes import ANCHO, ALTO
from arte_mar import WY, GRADO_COLOR
from nucleo import (Boton, Minijuego, TextoFlotante, aclarar, barra, estrella, explosion,
                    oscurecer, panel, V2)
from nucleo import escribir as _escribir_lento

_cache_texto = {}

# giro del cursor en circulos, en CUALQUIER lugar de la pantalla: horario enrolla, antihorario afloja
GIRO_VENTANA = 0.8       # s de historial del cursor (su centroide es el centro del giro)
GIRO_RECIENTE = 0.22     # s finales de ese historial con que se mide la velocidad (cambia de sentido rapido)
GIRO_MIN_HIST = 0.2      # s minimos de historial para medir
GIRO_R_MIN = 25.0        # px: radio de giro minimo (menos = temblor o quieto)
GIRO_R_MAX = 300.0       # px: radio de giro maximo (mas = casi una recta)
GIRO_UMBRAL = 1.6        # rad/s (suavizada) para enrollar (horario) o aflojar activo (antihorario)
GIRO_SUELTA = 1.2        # rad/s: por debajo de esto deja de contar el giro (histeresis, evita parpadeo)
GIRO_TOPE = 5.5          # rad/s: girar mas rapido que esto ya no enrolla mas fuerte
GIRO_CORR = 1.25         # correccion de la velocidad angular medida con arcos cortos
GIRO_EMA = 14.0          # 1/s: suavizado de la velocidad angular
GIRO_FLOJA_S = 5.5       # s de cuerda floja (k<0.12) antes de que se suelte el pez (era 3.6 con el control de mitades)
GIRO_AVISO_S = 0.55       # s de aviso "¡Afloja!" antes del tirón del pez (sin cambio; con más el aviso casi no se apaga con peces fuertes)
GUIA_X, GUIA_Y = 1105, 470   # centro del indicador circular de sentido (forcejeo y recoger)


def escribir(p, fuente, texto, x, y, color=(255, 255, 255), ancla="centro", contorno=(30, 30, 50), grosor=2):
    """Igual que nucleo.escribir pero guarda el texto ya compuesto (con contorno) para no gastar tiempo cada cuadro."""
    clave = (id(fuente), str(texto), color, contorno, grosor)
    sup = _cache_texto.get(clave)
    if sup is None:
        base = fuente.render(str(texto), True, color)
        w, h = base.get_size()
        g = grosor if contorno else 0
        sup = pygame.Surface((w + 2 * g, h + 2 * g), pygame.SRCALPHA)
        if contorno:
            sombra = fuente.render(str(texto), True, contorno)
            for dx in range(-g, g + 1):
                for dy in range(-g, g + 1):
                    if dx or dy:
                        sup.blit(sombra, (g + dx, g + dy))
        sup.blit(base, (g, g))
        if len(_cache_texto) > 600:
            _cache_texto.clear()
        _cache_texto[clave] = sup
    g = grosor if contorno else 0
    w, h = sup.get_size()
    w0, h0 = w - 2 * g, h - 2 * g
    if ancla == "centro":
        px, py = x - w0 / 2, y - h0 / 2
    elif ancla == "izq":
        px, py = x, y - h0 / 2
    else:
        px, py = x - w0, y - h0 / 2
    p.blit(sup, (px - g, py - g))
    return pygame.Rect(px, py, w0, h0)


BX = 190                                   # x del barco
MARGEN_X = 1250                            # el anzuelo no cae mas alla de aqui
SUELO = 648                                # y del fondo marino
PROF_MAX_PANTALLA = 392
NPEC = 9                                   # peces nadando a la vez
DWELL_LANZAR = 0.9
DWELL_CLAVAR = 0.55
PX_POR_METRO = 40.0
BONO_EVENTO = 40                           # puntos extra por un animal de evento

ZONAS = {i + 1: m["nombre"] for i, m in enumerate(pesca_datos.MUNDOS)}   # compatibilidad: nombre por mundo (1..5)
NOMBRE_PIEZA = pesca_datos.NOMBRES_HERR
EFECTO_PIEZA = pesca_datos.EFECTO_HERR
BTN_RECOGER = (1030, 128, 230, 64)         # boton visible "Recoger" (solo mientras la linea espera en el agua)
DWELL_RECOGER = 1.0
GRACIA_FIN = 70.0                          # s maximos que el forcejeo en curso sigue aunque se acabe el tiempo
FORC_E_ESCALA = 0.30                       # el pez se cansa mas despacio en un forcejeo largo
FORC_CAL = 2.4                            # calibracion: un buen jugador solo enrolla ~40 % del tiempo (tiene que aflojar)
FORC_PEND = 2.4                           # peces duros (peak alto) obligan a aflojar mas: se acelera el progreso para compensar
FORC_MIN_FRAC = 0.45                      # enrollando sin parar nunca se tarda menos de esta fraccion del tiempo objetivo
FORC_REF_E = 0.70                          # fuerza media del pez que se usa para calibrar la duracion


def parametros(perfil, mundo):
    """Efecto numerico del equipo y del mundo (ver pesca_datos.parametros)."""
    return pesca_datos.parametros(perfil, mundo)


def _fondo(mundo):
    """(fondo, frente) del mundo 0..4: arte_mar.fondo_mundo (recibe 1..5) si existe, si no fondo_zona."""
    fm = getattr(arte_mar, "fondo_mundo", None) or arte_mar.fondo_zona
    return fm(mundo + 1)


def clavado_prob(par, grado):
    return max(0.1, min(0.98, par["clavar"] - 0.06 * (grado - 1)))


def peso_pez(par, grado):
    """Factor por el que la caña no 'levanta bien' un pez de grado mayor que sus estrellas + 2."""
    return 0.55 ** max(0, grado - (par["cana"] + 2))


class BotonAccion(Boton):
    """Boton de la pesca: se pulsa con clic/golpe o dejando el cursor encima `dwell_seg` segundos."""

    def __init__(self, rect, texto, color, dwell_seg=DWELL_LANZAR, espera=0.35):
        super().__init__(rect, texto, color, espera)
        self.dwell_seg = dwell_seg

    def actualizar(self, dt, ctrl):
        self.espera = max(0.0, self.espera - dt)
        self.encima = self.activo and self.rect.collidepoint(ctrl.pos.x, ctrl.pos.y)
        if not self.encima or self.espera > 0:
            self.dwell = max(0.0, self.dwell - dt * 2)
            return False
        self.dwell += dt
        if ctrl.clic or ctrl.golpe or self.dwell >= self.dwell_seg:
            self.dwell = 0.0
            return True
        return False

    def dibujar(self, pantalla, fuente):
        color = aclarar(self.color, 0.25) if self.encima else self.color
        pygame.draw.rect(pantalla, oscurecer(color, 0.5), self.rect.move(0, 5), border_radius=20)
        pygame.draw.rect(pantalla, color, self.rect, border_radius=20)
        pygame.draw.rect(pantalla, (255, 255, 255), self.rect, 4, border_radius=20)
        escribir(pantalla, fuente, self.texto, self.rect.centerx, self.rect.centery - 2)
        if self.dwell > 0:
            r = pygame.Rect(self.rect.x + 14, self.rect.bottom - 15, self.rect.width - 28, 8)
            barra(pantalla, r, self.dwell / self.dwell_seg, color=(255, 230, 90),
                  color_fondo=(110, 120, 150), borde=(255, 255, 255))


class Pez:
    """Un pez (o animal de evento) nadando en el corte lateral."""

    def __init__(self, sp, x, y, d, vel, parte, hambre, evento=False):
        self.sp = sp
        self.dat = arte.PECES[sp]
        self.grado = self.dat[1]
        self.x, self.y0, self.y = float(x), float(y), float(y)
        self.dir = d
        self.vel = vel
        self.parte = parte                   # (nombre de la parte visible, ventana nominal) o 'sombra'
        self.hambre = hambre
        self.evento = evento
        self.estado = "nada"                 # nada, acerca, mordisquea, muerde, huye
        self.t_est = 0.0
        self.fase = random.uniform(0, 6.28)
        self.largo = self.dat[8]
        self.escala = self.largo / arte_mar.FORMAS[self.dat[4]][0]
        self.carac = self.dat[13]

    @property
    def profundidad(self):
        return self.y - WY

    @property
    def visible(self):
        return 10 <= self.x <= ANCHO - 10


class Pesca(Minijuego):
    """Apunta con el cursor (o con un gesto de lanzamiento), lanza, espera, clava y enrolla.

    Fases: apuntar, vuelo, esperar, mordida, forcejeo, captura/pausa (no hay fase "preparar").
    La linea lanzada se QUEDA en el agua hasta que pique un pez: mover el cursor NO la recoge. Para cancelar
    el lanzamiento hay un boton visible "Recoger" (clic, golpe o dejar el cursor encima ~1 s).
    Control del forcejeo, en CUALQUIER lugar de la pantalla (cursor o espada): ENROLLAR = hacer circulos
    hacia adelante (sentido de las agujas del reloj); AFLOJAR = circulos al reves. Quieto, de vaiven o muy
    lento tambien afloja (sin soltar al pez enseguida). Se mide con el historial de ~0.8 s del cursor.
    El forcejeo es largo (un buen jugador tarda ~25-40 s segun el grado del pez y el mundo).

    Mejoras: potencia = enrollas con mas fuerza; alcance = la zona de mordida y la ventana de
    clavar son mas generosas; lento = los peces nadan mas despacio; vida = si la linea se rompe
    se reintenta una vez; puntos = cada pez vale el doble; tiempo = mas segundos de pesca.
    """

    id = "pesca"
    titulo = "Pesca"
    instruccion = "¡Apunta, lanza la caña y atrapa peces!"
    gesto = "Cursor para apuntar, golpe para lanzar; círculos hacia adelante enrollan, al revés aflojan"
    duracion = 130.0
    fondo_arriba = (120, 195, 255)
    fondo_abajo = (30, 100, 170)

    def __init__(self, ctx, nivel=1, mundo=None):
        self.perfil = ctx.perfil
        self.mundo, self.limitado = pesca_datos.mundo_para_jugar(self.perfil, mundo)
        self.mundo_def = pesca_datos.MUNDOS[self.mundo]
        self.duracion = pesca_datos.duracion_partida(self.mundo)
        super().__init__(ctx, self.mundo + 1)        # `nivel` se ignora: manda el mundo
        self.par = parametros(self.perfil, self.mundo)
        self.pot = self.mej.mult("potencia")
        self.alc = self.mej.mult("alcance")
        self.vidas = self.mej.vidas_extra()
        self.zona = self.mundo + 1                    # compatibilidad: 1..5
        self.estab = self.par["estab"]
        self.barco = self.par["barco"]
        # constantes derivadas
        self.mano = V2(arte_mar.MANO_BARCO[self.barco]) + V2(BX, WY)
        self.punta = self.mano + V2(150, -70)
        self.alcance = self.par["alcance"]
        self.x_min = self.punta.x + 70
        self.x_max = min(MARGEN_X, self.punta.x + self.alcance)
        self.prof = self.par["prof"]
        self.radio_mordida = 105 * self.alc
        self.ventana = (1.7 + 0.05 * (5 - self.zona)) * self.alc / self.lento
        self.vel_mundo = self.lento
        self.bg, self.frente = _fondo(self.mundo)
        self.tiras_frente = [pygame.Rect(0, 340, 330, ALTO - 340), pygame.Rect(ANCHO - 330, 340, 330, ALTO - 340)]
        # estado de juego
        self.fase = "apuntar"
        self.t_fase = 0.0
        self.t_jug = 0.0
        self.modo_gesto = False
        self.mira_x = min(self.x_max, self.punta.x + 260)
        self.mira_lejos = False
        self.rastro = []                          # [(t, x, y)] para el gesto
        self.v_gesto = V2(0, 0)
        self.hx, self.hy = self.punta.x, self.punta.y
        self.hook0 = V2(self.hx, self.hy)
        self.lx = self.mira_x
        self.pez = None                           # pez enganchado / mordiendo
        self.dist = 1.0
        self.k = 0.0
        self.e = 1.0
        self.aviso = False
        self.pulso = 0.0
        self.t_aviso = 0.0
        self.t_pulso = 2.0
        self.sin_prog = 0.0
        self.floja = 0.0
        self.vida_usada = False
        self.msg = ""
        self.msg_t = 0.0
        self.msg_color = (255, 255, 255)
        self.banner = None
        self.banner_t = 0.0
        self.evento = None
        self.eventos_hechos = 0
        self.t_evento = random.uniform(14, 28)
        self.gracia = GRACIA_FIN
        self.particulas = []
        self.peces = []
        self.vistos = set()
        self.nuevo = False
        self.capturados = 0
        self.capturas = []
        self.picadas = 0
        self.rotas = 0
        self.soltados = 0
        self.reintentos = 0
        self.ultimo_lanzamiento = None
        self.cache_mascara = {}
        self.boton = None
        self.b_modo = None
        self.b_recoger = None
        self.msgs_pesca = []                      # mensajes en cola (registro nuevo, mundo abierto, herramienta rota)
        self.eventos_reg = []                     # eventos de pesca_datos.registrar_captura de esta partida
        self.herr_rotas = []
        self.tope_f = 0.1
        self.escala_f = 0.05                      # escala de duracion del forcejeo (se calcula al clavar)
        self.recogiendo = False
        self.enrolla = True
        self.ruido = 0.0
        self._ang_prev = None                     # angulo del cursor respecto al carrete (None = fuera de zona)
        self.w_giro = 0.0                         # velocidad angular suavizada (rad/s, + = horario en pantalla)
        self.giro_on = False                      # gira hacia adelante (horario): enrolla
        self.giro_atras = False                   # gira al reves (antihorario): afloja activo
        self.giro_f = 0.0                         # 0..1: que tan rapido gira hacia adelante (sobre el umbral)
        self.hist_cur = []                        # [(t, x, y)] historial del cursor para medir el giro
        self.t_giro = 0.0
        self.ang_perilla = 0.0                    # perilla del indicador: gira como el jugador
        self._ola = None
        self._poblar()
        self._boton_fase()

    # ------------------------------------------------------------------ metas y datos
    def calcular_metas(self):
        return pesca_datos.metas_mundo(self.mundo)

    @property
    def zona_nombre(self):
        return self.mundo_def["nombre"]

    @property
    def aviso_equipo(self):
        if self.limitado:
            return f"Tu equipo llega hasta el {self.zona_nombre}"
        return ""

    def evaluar(self, pez):
        """'facil' (pulgar verde), 'medio' (amarillo), 'dificil' (cuidado rojo) o 'hondo' (tu cuerda no llega)."""
        if pez.profundidad > self.prof + 70:
            return "hondo"
        g = pez.grado
        peak = (pez.dat[6] * self.par["fuerza"] * 1.4 + 0.4 * self.par["P"] * self.pot) / self.par["C"]
        if g <= self.par["cana"] and peak <= 1.0:
            return "facil"
        if g <= self.par["cana"] + 1 and peak <= 1.6:
            return "medio"
        return "dificil"

    def prediccion_gesto(self, v):
        """Donde caera el anzuelo con un gesto de velocidad v (px/s): (x, distancia, fuerte)."""
        d = 0.20 * max(v.x, 0.4 * v.length())
        dist = max(90.0, min(self.x_max - self.punta.x, d))
        return self.punta.x + dist, dist, d > self.x_max - self.punta.x

    # ------------------------------------------------------------------ peces
    def _pool(self, evento=False):
        """(ids, pesos) del mundo: objetivos sin registrar pesan mas; fondo y registrados, menos."""
        ids, pesos = pesca_datos.pool(self.perfil, self.mundo, evento)
        for n, k in enumerate(ids):
            d = arte.PECES[k]
            if d[1] <= self.par["cana"] + 1:
                pesos[n] = max(pesos[n], 0.45)    # siempre quedan peces que tu caña maneja
            if d[10][0] > self.prof + 70:
                pesos[n] *= 0.35
        if evento and pesca_datos.hay_objetivo_evento_pendiente(self.perfil, self.mundo):
            for n, k in enumerate(ids):
                if k in pesca_datos.objetivos_pendientes(self.perfil, self.mundo):
                    pesos[n] *= 4.0
        return ids, pesos

    def _crear_pez(self, sp, x=None, evento=False):
        d = arte.PECES[sp]
        evento = evento or d[12]
        if x is None:
            if evento:
                x = random.choice((-120 - d[8] * 0.3, ANCHO + 120 + d[8] * 0.3))
            else:
                x = random.choice((-60, ANCHO + 60))
        direccion = 1 if x < ANCHO / 2 else -1
        dmin, dmax = d[10]
        dmax = min(dmax, PROF_MAX_PANTALLA)
        prof = random.uniform(dmin, max(dmin + 1, dmax))
        vel = random.uniform(34, 70) * (1.0 - 0.3 * min(1.0, d[8] / 450))
        if evento:
            vel = random.uniform(48, 62)
        nombres = arte_mar.FORMAS[d[4]][1]
        if random.random() < 0.16:
            parte = "sombra"
        else:
            parte = random.choice(nombres)
        hambre = evento or random.random() < 0.9
        return Pez(sp, x, WY + prof, direccion, vel, parte, hambre, evento)

    def _nuevo_pez(self, x=None):
        ids, pesos = self._pool(False)
        if not ids:
            ids = [k for k, d in arte.PECES.items() if not d[12]]
            pesos = [1.0] * len(ids)
        sp = random.choices(ids, pesos)[0]
        return self._crear_pez(sp, x)

    def _poblar(self):
        self.peces = []
        for _ in range(NPEC):
            self.peces.append(self._nuevo_pez(min(ANCHO + 40, max(-40, random.gauss(700, 380)))))

    def forzar_evento(self, sp=None):
        """Lanza un evento ahora (para pruebas y para el propio juego)."""
        ids, pesos = self._pool(True)
        if not ids:
            return None
        if sp is None:
            sp = random.choices(ids, pesos)[0]
        pez = self._crear_pez(sp, evento=True)
        self.peces.append(pez)
        self.evento = pez
        self.eventos_hechos += 1
        self.banner = arte.EVENTO_TEXTO.get(sp, "¡Evento!")
        self.banner_t = 4.0
        self.sonidos.reproducir("rugido")
        return pez

    def _mundo(self, dt):
        dtl = dt * self.vel_mundo
        buscando = self.fase == "esperar"
        hook = V2(self.hx, self.hy)
        for f in list(self.peces):
            f.t_est += dt
            if f.estado == "nada":
                f.x += f.dir * f.vel * dtl
                f.y = f.y0 + math.sin(self.t * 0.9 + f.fase) * 7
                if buscando and f.hambre and (f.y - hook.y) ** 2 + (f.x - hook.x) ** 2 < (self._radio(f)) ** 2 \
                        and self.hy > WY + 18:
                    if random.random() < 1.7 * dt:
                        f.estado = "acerca"
                        f.t_est = 0.0
                        f.dir = 1 if hook.x > f.x else -1
            elif f.estado == "acerca":
                if not buscando:
                    f.estado = "nada"
                    continue
                v = V2(hook.x - f.x, hook.y - f.y)
                dd = v.length()
                if dd > self._radio(f) * 1.5:
                    f.estado = "nada"
                    continue
                vel = {"timido": 150, "curioso": 120, "cauto": 85, "agresivo": 190}[f.carac] * dtl
                if dd > 1:
                    v.scale_to_length(min(dd, vel))
                f.x += v.x
                f.y += v.y
                f.y0 = f.y
                if abs(v.x) > 0.5:
                    f.dir = 1 if v.x > 0 else -1
                if dd < 24 + f.largo * 0.08:
                    f.estado = "mordisquea"
                    f.t_est = 0.0
                    rango = {"timido": (0.35, 0.7), "curioso": (0.5, 1.0), "cauto": (0.9, 1.6), "agresivo": (0.2, 0.5)}[f.carac]
                    f.espera = random.uniform(*rango) / self.alc
            elif f.estado == "mordisquea":
                if not buscando:
                    f.estado = "nada"
                    continue
                if f.t_est >= f.espera:
                    if f.carac == "cauto" and not f.evento and random.random() < 0.25:
                        f.estado = "huye"
                        f.hambre = False
                        f.dir = -f.dir
                    else:
                        f.estado = "muerde"
                        self._mordida(f)
            elif f.estado == "huye":
                f.x += f.dir * 230 * dtl
            if f.evento or f.estado == "huye":
                if f.x < -380 - f.largo or f.x > ANCHO + 380 + f.largo:
                    self.peces.remove(f)
                    if f is self.evento:
                        self.evento = None
                    if not f.evento:
                        self.peces.append(self._nuevo_pez())
            elif f.estado == "nada":
                if f.x < -60 and f.dir < 0:
                    f.dir = 1
                elif f.x > ANCHO + 60 and f.dir > 0:
                    f.dir = -1

    def _radio(self, f):
        r = self.radio_mordida
        if f.carac == "agresivo":
            r *= 1.2
        elif f.carac == "cauto":
            r *= 0.85
        if f.evento:
            r *= 1.25
        return r + f.largo * 0.1

    # ------------------------------------------------------------------ botones por fase
    def _boton_fase(self):
        f = self.fase
        self.boton = None
        self.b_modo = None
        self.b_recoger = None
        if f == "apuntar":
            self.boton = BotonAccion((500, 14, 280, 78), "¡LANZAR!", (70, 160, 230), DWELL_LANZAR, 0.35)
            self.b_modo = BotonAccion((322, 20, 168, 50), "Modo: Gesto" if self.modo_gesto else "Modo: Apuntar",
                                      (120, 110, 200), 0.9, 0.5)
        elif f == "mordida":
            self.boton = BotonAccion((500, 14, 280, 78), "¡CLAVAR!", (235, 90, 70), DWELL_CLAVAR, 0.0)
        elif f == "esperar":
            self.b_recoger = BotonAccion(BTN_RECOGER, "Recoger", (225, 130, 50), DWELL_RECOGER, 0.6)

    def _giro(self, dt, pos):
        """Mide el giro del cursor en cualquier lugar. Devuelve True si gira hacia adelante (enrolla).

        Centro = centroide del historial; velocidad angular w = suma(r x dp) / suma(|r|^2 dt) (+ = horario en
        pantalla, y hacia abajo); el radio se estima como rapidez/|w| y debe estar entre GIRO_R_MIN y GIRO_R_MAX."""
        self.t_giro += dt
        h = self.hist_cur
        h.append((self.t_giro, pos.x, pos.y))
        while len(h) > 1 and self.t_giro - h[0][0] > GIRO_VENTANA:
            h.pop(0)
        w_i = 0.0
        if len(h) > 2 and h[-1][0] - h[0][0] >= GIRO_MIN_HIST:
            n = len(h)
            cx = sum(q[1] for q in h) / n
            cy = sum(q[2] for q in h) / n
            num = den = cam = tm = 0.0
            for i in range(1, n):
                t0, x0, y0 = h[i - 1]
                t1, x1, y1 = h[i]
                if self.t_giro - t1 > GIRO_RECIENTE:
                    continue
                rx, ry = x1 - cx, y1 - cy
                dx, dy = x1 - x0, y1 - y0
                num += rx * dy - ry * dx
                den += (rx * rx + ry * ry) * (t1 - t0)
                cam += math.hypot(dx, dy)
                tm += t1 - t0
            if den > 1e-6 and tm > 1e-6:
                w = GIRO_CORR * num / den              # GIRO_CORR: medir solo los ultimos 0.22 s da w ~20% baja
                r_eff = (cam / tm) / max(1e-6, abs(w))
                if GIRO_R_MIN <= r_eff <= GIRO_R_MAX:
                    w_i = max(-12.0, min(12.0, w))
        self.w_giro += (w_i - self.w_giro) * min(1.0, GIRO_EMA * dt)
        w = self.w_giro
        self.giro_on = w > GIRO_UMBRAL or (self.giro_on and w > GIRO_SUELTA)
        self.giro_atras = w < -GIRO_UMBRAL or (self.giro_atras and w < -GIRO_SUELTA)
        self.giro_f = max(0.0, min(1.0, (w - GIRO_UMBRAL) / (GIRO_TOPE - GIRO_UMBRAL))) if self.giro_on else 0.0
        self.ang_perilla += max(-9.0, min(9.0, w)) * dt
        return self.giro_on

    def _giro_reset(self):
        self.hist_cur = []
        self.t_giro = 0.0
        self.w_giro = 0.0
        self.giro_on = False
        self.giro_atras = False
        self.giro_f = 0.0

    def _ir(self, fase):
        self.fase = fase
        self.t_fase = 0.0
        if fase in ("esperar", "forcejeo"):
            self._giro_reset()
        self._boton_fase()

    def _mensaje(self, texto, color=(255, 255, 255), seg=1.6):
        self.msg, self.msg_t, self.msg_color = texto, seg, color

    def _sobre_ui(self, pos):
        for b in (self.boton, self.b_modo, self.b_recoger):
            if b and b.rect.inflate(10, 10).collidepoint(pos.x, pos.y):
                return True
        return False

    # ------------------------------------------------------------------ logica por fase
    def paso(self, dt, ctrl):
        self.t_fase += dt
        self.msg_t = max(0.0, self.msg_t - dt)
        self.banner_t = max(0.0, self.banner_t - dt)
        self.particulas = [q for q in self.particulas if q.actualizar(dt)]
        self.rastro.append((self.t, ctrl.pos.x, ctrl.pos.y))
        while self.rastro and self.t - self.rastro[0][0] > 0.35:
            self.rastro.pop(0)
        f = self.fase
        self.t_jug += dt
        if f in ("forcejeo", "mordida", "captura") and self.tiempo < 1.0 and self.gracia > 0:
            self.tiempo += dt                      # termina el pez que tienes entre manos
            self.gracia -= dt
        pend_ev = pesca_datos.hay_objetivo_evento_pendiente(self.perfil, self.mundo)
        max_ev = 2 + (1 if pend_ev else 0)
        if self.evento is None and self.eventos_hechos < max_ev and self.mundo >= 1 \
                and self.t_jug >= self.t_evento and self.tiempo > 15 and f in ("apuntar", "esperar"):
            self.forzar_evento()
            self.t_evento = self.t_jug + random.uniform(35, 55)
        self._mundo(dt)
        getattr(self, "_f_" + f)(dt, ctrl)

    def _velocidad_gesto(self):
        """Velocidad maxima (vector, px/s) del cursor en los ultimos 0.25 s: la 'fuerza' del gesto."""
        r = self.rastro
        mejor = V2(0, 0)
        for i in range(len(r) - 2):
            t0, x0, y0 = r[i]
            t1, x1, y1 = r[i + 2]
            dtv = t1 - t0
            if dtv > 1e-4:
                v = V2((x1 - x0) / dtv, (y1 - y0) / dtv)
                if v.length() > mejor.length():
                    mejor = v
        return mejor

    def _f_apuntar(self, dt, ctrl):
        pos = ctrl.pos
        if self.b_modo.actualizar(dt, ctrl):
            self.modo_gesto = not self.modo_gesto
            self.b_modo.texto = "Modo: Gesto" if self.modo_gesto else "Modo: Apuntar"
            self.sonidos.reproducir("click")
        pulsado = self.boton.actualizar(dt, ctrl)
        sobre_ui = self._sobre_ui(pos)
        tajo = ctrl.cortando and not sobre_ui
        if self.modo_gesto:
            v = self._velocidad_gesto()
            if v.length() > 250:
                self.v_gesto = v
            x, dist, fuerte = self.prediccion_gesto(self.v_gesto if self.v_gesto.length() > 0 else V2(1500, 0))
            self.mira_x, self.mira_lejos = x, fuerte
            if tajo and ctrl.vel > 0:
                vf = V2(ctrl.p2 - ctrl.p1) / max(dt, 1e-3)
                if vf.length() > 0:
                    self.mira_x, _, self.mira_lejos = self.prediccion_gesto(vf)
        elif not ctrl.cortando and not sobre_ui:
            self.mira_lejos = pos.x > self.x_max + 6
            self.mira_x = max(self.x_min, min(self.x_max, pos.x))
        if self.t_fase < 0.35:
            return
        lanzar = pulsado or ((ctrl.golpe or ctrl.clic) and not self.b_modo.rect.collidepoint(pos.x, pos.y)) or tajo
        if lanzar:
            self._lanzar(ctrl)

    def _lanzar(self, ctrl):
        self.lx = self.mira_x
        self.ultimo_lanzamiento = self.lx
        self.hx, self.hy = self.punta.x, self.punta.y
        self._ir("vuelo")
        self.sonidos.reproducir("lanzar")

    def _f_vuelo(self, dt, ctrl):
        u = min(1.0, self.t_fase / 0.7)
        self.hx = self.punta.x + (self.lx - self.punta.x) * u
        self.hy = self.punta.y + (WY - self.punta.y) * u - self._altura_arco() * 4 * u * (1 - u)
        if u >= 1.0:
            self.hx, self.hy = self.lx, WY
            self.sonidos.reproducir("splash")
            explosion(self.particulas, self.lx, WY, (215, 240, 255), n=14, vel_min=60, vel_max=260,
                      vida=0.55, gravedad=700, radio=4)
            self._ir("esperar")

    def _altura_arco(self, lx=None):
        lx = self.lx if lx is None else lx
        return 40 + 0.12 * (lx - self.punta.x)

    def _f_esperar(self, dt, ctrl):
        """La linea se queda donde cayo hasta que pique un pez. Solo el boton Recoger la cancela."""
        pos = ctrl.pos
        if self.fase != "esperar":                 # un pez pico en este mismo cuadro (_mundo)
            return
        if self.recogiendo:
            v = V2(self.punta.x - self.hx, self.punta.y - self.hy)
            if v.length() < 50:
                self.recogiendo = False
                self._mensaje("¡Otra vez!", seg=0.8)
                self.sonidos.reproducir("pop")
                self._ir("apuntar")
                return
            v.scale_to_length(min(v.length(), 560 * dt))
            self.hx += v.x
            self.hy += v.y
            return
        if self.b_recoger.actualizar(dt, ctrl):
            self.recogiendo = True
            self.sonidos.reproducir("click")
            return
        # el anzuelo solo se mece un poco con el cursor, sin alejarse de donde cayo
        tx = max(self.x_min - 40, min(self.x_max, self.lx + max(-80, min(80, (pos.x - self.lx) * 0.3))))
        ty = max(WY + 25, min(WY + self.prof, pos.y))
        self.hx += max(-140 * dt, min(140 * dt, tx - self.hx))
        self.hy += max(-190 * dt, min(130 * dt, ty - self.hy))

    def _mordida(self, f):
        self.pez = f
        self.picadas += 1
        self._ir("mordida")
        self.sonidos.reproducir("splash")
        self.sonidos.nota(880, 0.2)

    def _f_mordida(self, dt, ctrl):
        f = self.pez
        self.hx = f.x + math.sin(self.t * 38) * 3
        self.hy = f.y + 4
        pulsado = self.boton.actualizar(dt, ctrl)
        if self.t_fase > 0.06 and (pulsado or ctrl.golpe or ctrl.clic or ctrl.cortando):
            self._clavar()
        elif self.t_fase >= self.ventana:
            f.estado = "huye"
            f.hambre = False
            f.dir = 1 if random.random() < 0.5 else -1
            self.pez = None
            self.sonidos.reproducir("fallo")
            self._mensaje("¡Se fue! Prueba otra vez", seg=1.2)
            self._ir("esperar")

    def _clavar(self):
        f = self.pez
        if random.random() < clavado_prob(self.par, f.grado):
            self._iniciar_forcejeo()
        else:
            f.estado = "huye"
            f.hambre = False
            self.pez = None
            self.soltados += 1
            self.sonidos.reproducir("fallo")
            self._mensaje("¡Se soltó! No pasa nada", (255, 235, 200), seg=1.3)
            self._ir("esperar")

    def _iniciar_forcejeo(self):
        f = self.pez
        if f in self.peces:
            self.peces.remove(f)
        if f is self.evento:
            self.evento = None
        if not f.evento:
            self.peces.append(self._nuevo_pez())
        self.hook0 = V2(f.x, f.y)
        self.dist, self.k, self.e = 1.0, 0.25, 1.0
        self.aviso, self.pulso, self.t_aviso = False, 0.0, 0.0
        self.t_pulso = random.uniform(1.4, 2.6)
        self.sin_prog = self.floja = 0.0
        self.vida_usada = False
        self.tension_max = 0.0
        self.msgs_pesca = []
        # duracion del forcejeo: la velocidad de progreso se calibra para que un buen jugador tarde
        # pesca_datos.tiempo_forcejeo(grado, mundo) segundos (con el pez a ~70 % de su fuerza)
        d = f.dat
        par = self.par
        P = par["P"] * self.pot
        vref = max(0.05, 0.26 * (P * peso_pez(par, d[1]) - 0.45 * d[6] * par["fuerza"] * (0.45 + 0.55 * FORC_REF_E)))
        self.t_obj = pesca_datos.tiempo_forcejeo(d[1], self.mundo)
        fz = d[6] * par["fuerza"]
        peak = (fz * 1.4 + 0.4 * P) / par["C"]                 # los peces duros obligan a aflojar mas: tardan mas
        impulso = 1.0 + FORC_PEND * max(0.0, peak - 0.75)
        self.escala_f = FORC_CAL * impulso / (vref * self.t_obj)
        self.tope_f = impulso / (FORC_MIN_FRAC * self.t_obj)
        self.t_forc = 0.0
        self.sonidos.reproducir("ok")
        self._ir("forcejeo")

    def _f_forcejeo(self, dt, ctrl):
        f = self.pez
        d = f.dat
        par = self.par
        dtl = dt * self.lento
        # tirones del pez (avisan antes)
        self.t_pulso -= dtl
        if self.t_pulso < 0:
            self.t_pulso = random.uniform(2.0, 3.6) / (1.0 + 0.04 * d[1])
            self.t_aviso = GIRO_AVISO_S
        ta = self.t_aviso
        if ta > 0:
            self.t_aviso = max(0.0, ta - dtl)
            if self.t_aviso == 0.0:
                self.pulso = 0.9
        elif self.pulso > 0:
            self.pulso = max(0.0, self.pulso - dtl)
        self.aviso = self.t_aviso > 0 or self.pulso > 0         # el pez va a tirar fuerte (o esta tirando)
        env = math.sin(math.pi * self.pulso / 0.9) if self.pulso > 0 else 0.0
        f_eff = d[6] * par["fuerza"] * (0.45 + 0.55 * self.e) * (1 + 0.4 * env)
        self.t_forc += dt
        enrolla = self._giro(dt, ctrl.pos)         # circulos horarios = enrolla; al reves, quieto o vaiven = afloja
        atras = self.giro_atras                    # gira al reves a proposito: afloja un poco mas rapido
        P = par["P"] * self.pot * (0.9 + 0.25 * self.giro_f)
        C = par["C"]
        if enrolla:
            targ = (f_eff + 0.4 * P) / C
        else:
            targ = (0.08 if atras else 0.12) * f_eff / C
        self.k += (targ - self.k) * min(1.0, (4.2 if atras and not enrolla else 3.0) * dt)
        ruido = 0.12 * self.estab * (math.sin(self.t * 7.0) + 0.6 * math.sin(self.t * 12.3 + 1.0))
        self.ruido = ruido
        kn = self.k + ruido
        self.tension_max = max(self.tension_max, self.k)
        # progreso
        if enrolla:
            v = 0.26 * (P * peso_pez(par, d[1]) - 0.45 * f_eff)
            v = max(-0.10, v)
            if env > 0:
                v *= 1.0 - 1.4 * env              # enrollar cuando el pez tira: el pez gana linea (hay que aflojar)
            self.dist -= min(v * self.escala_f, self.tope_f) * dt
            self.sin_prog = self.sin_prog + dt if v <= 0.005 else 0.0
            self.e = max(0.2, self.e - (0.09 + 0.14 * self.k) / math.sqrt(d[7]) * dtl * FORC_E_ESCALA)
        else:
            self.dist += 0.03 * (0.5 + d[6] * par["fuerza"] / 6) * self.escala_f * dt
            self.e = min(1.0, self.e + (0.03 if atras else 0.02) * dt)
            self.sin_prog = max(0.0, self.sin_prog - dt)
        self.dist = min(1.2, self.dist)
        if self.k < 0.12 and not enrolla:
            self.floja += dt * (0.4 if atras else 1.0)       # aflojar a proposito casi no cuenta como cuerda floja
        elif self.k > 0.2:
            self.floja = max(0.0, self.floja - dt)
        self.enrolla = enrolla
        # final
        if self.dist <= 0.0:
            self._capturar()
        elif kn >= 1.0:
            if self.vidas and not self.vida_usada:
                self.vida_usada = True
                self.reintentos += 1
                self.k = 0.3
                self._mensaje("¡Intento extra! La línea se arregló", (170, 240, 190), 1.6)
                self.sonidos.reproducir("pop")
            else:
                self.rotas += 1
                self.sonidos.reproducir("fallo")
                self.flotantes.append(TextoFlotante("¡Plaf!", self.hook0.x, self.hook0.y - 20, (255, 140, 120)))
                self._desgaste("rota")
                self._perder("¡Se rompió la línea! No pasa nada")
        else:
            h = (0.002 * d[1] * d[1] * (4.0 / self.t_obj) + 0.10 * max(0.0, self.k - 0.78)) * par["agarre"]
            if self.sin_prog > 7.0:
                self._soltar("El pez era muy fuerte y se soltó")
            elif self.floja > GIRO_FLOJA_S * (0.8 + 0.1 * par["anzuelo"]):
                self._soltar("¡La cuerda estaba floja y se soltó!")
            elif random.random() < h * dt:
                self._soltar("¡Se soltó del anzuelo!")

    def _soltar(self, texto):
        self.soltados += 1
        self.sonidos.reproducir("fallo")
        self._desgaste("suelta")
        self._perder(texto)

    def _desgaste(self, resultado):
        """Gasta la caña, la cuerda y el anzuelo con el forcejeo que acaba de terminar y recalcula el equipo."""
        rotas = pesca_datos.aplicar_desgaste(self.perfil, self.pez.grado, resultado, self.tension_max)
        for r in rotas:
            self.herr_rotas.append(r)
            self.msgs_pesca.append(f"¡Se rompió tu {pesca_datos.NOMBRES_HERR[r['tipo']].lower()} de {r['est']} "
                                   f"{'estrella' if r['est'] == 1 else 'estrellas'}!")
        self.par = parametros(self.perfil, self.mundo)

    def _perder(self, texto):
        self.pez = None
        self._mensaje(texto, (255, 190, 160), 1.6)
        self.hx, self.hy = self.punta.x, self.punta.y
        self._ir("pausa")

    def _capturar(self):
        f = self.pez
        d = f.dat
        self.capturados += 1
        self.capturas.append(f.sp)
        self.msgs_pesca = []
        eventos = pesca_datos.registrar_captura(self.perfil, f.sp)
        self.eventos_reg += eventos
        reg_nuevo = any(e[0] == "nuevo" for e in eventos)
        ptos = pesca_datos.puntos_captura(f.sp, reg_nuevo)
        self.sumar(ptos, 640, 330, (255, 235, 110))
        pv = self.perfil.peces_vivos
        pv[f.sp] = int(pv.get(f.sp, 0)) + 1
        self.nuevo = reg_nuevo or (f.sp not in self.perfil.peces and f.sp not in self.vistos)
        if f.sp not in self.vistos:
            self.vistos.add(f.sp)
            self.recompensas.append(("pez", f.sp))
        for e in eventos:
            if e[0] == "completo":
                self.msgs_pesca.append(f"¡Completaste el {pesca_datos.MUNDOS[e[1]]['nombre']}!")
            elif e[0] == "mundo":
                self.msgs_pesca.append(f"¡Se abrió el {pesca_datos.MUNDOS[e[1]]['nombre']}!")
        self._desgaste("captura")
        for mid, n in pesca_datos.sorteo_materiales(self.mundo, d[1], bool(d[12])):
            self.dar(mid, n)
        if d[1] >= 3 and (d[12] or random.random() < 0.55):
            self.dar("huevas", 2 if d[12] else 1)
        # mariscos para la cocina: langostino desde la zona 1, calamar desde la zona 2 (modestos)
        if random.random() < 0.10 + 0.04 * min(self.zona, 4):
            self.dar("langostino")
        if self.zona >= 2 and random.random() < 0.06 + 0.03 * min(self.zona, 5):
            self.dar("calamar")
        self.perfil.guardar()
        self.sonidos.reproducir("premio")
        explosion(self.particulas, self.punta.x + 40, WY + 60, (200, 235, 255), n=20, vel_min=100, vel_max=400,
                  vida=0.8, gravedad=700)
        self.hx, self.hy = self.punta.x, self.punta.y
        self._ir("captura")

    def _f_captura(self, dt, ctrl):
        if self.t_fase >= 1.7 + 1.0 * min(2, len(self.msgs_pesca)):
            self.pez = None
            self._ir("apuntar")

    def _f_pausa(self, dt, ctrl):
        if self.t_fase >= 1.4 + 0.9 * min(2, len(self.msgs_pesca)):
            self._ir("apuntar")

    # ------------------------------------------------------------------ dibujo: peces con parte visible
    def _mascara(self, w, h):
        m = self.cache_mascara.get((w, h))
        if m is None:
            m = pygame.Surface((w, h), pygame.SRCALPHA)
            m.fill((255, 255, 255, 0))
            pygame.draw.ellipse(m, (255, 255, 255, 255), (0, 0, w, h))
            self.cache_mascara[(w, h)] = m
        return m

    def ventana_parte(self, f):
        """(cx, cy, ancho, alto) en pantalla de la parte del pez que asoma."""
        if f.parte == "sombra":
            nom, r = [p for p in arte_mar.FORMAS[f.dat[4]][1] if p[0] == "cuerpo"][0]
        else:
            nom, r = f.parte
        cx, cy, w, h = r
        s = f.escala
        bx = f.x + f.dir * cx * s
        by = f.y + cy * s
        ww = max(70, min(170, w * s))
        hh = max(60, min(122, h * s))
        return bx, by, ww, hh

    def _dibujar_parte(self, p, f):
        bx, by, ww, hh = self.ventana_parte(f)
        ww, hh = int(ww), int(hh)
        if bx + ww / 2 < 0 or bx - ww / 2 > ANCHO:
            return
        tmp = pygame.Surface((ww, hh), pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, (225, 245, 255, 70), (0, 0, ww, hh))
        sil = f.parte == "sombra"
        arte.dibujar_pez(tmp, f.sp, f.x - (bx - ww / 2), f.y - (by - hh / 2), f.escala, f.dir,
                         self.t + f.fase, silueta=sil)
        tmp.blit(self._mascara(ww, hh), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        ev = self.evaluar(f)
        if ev == "hondo":
            tmp.set_alpha(150)
        p.blit(tmp, (bx - ww / 2, by - hh / 2))
        col = GRADO_COLOR[f.grado]
        r = pygame.Rect(0, 0, ww, hh)
        r.center = (int(bx), int(by))
        pygame.draw.ellipse(p, (255, 255, 255), r.inflate(4, 4), 2)
        pygame.draw.ellipse(p, col, r, 5)
        if f.estado in ("mordisquea", "muerde"):
            pygame.draw.ellipse(p, (255, 255, 255), r.inflate(14, 14), 3)
        arte_mar.icono_pista(p, ev, bx, by - hh / 2 - 12, 15)
        if f.evento:
            estrella(p, bx + ww / 2 - 4, by - hh / 2 + 4, 13, (255, 235, 110), (150, 90, 20))

    def _dibujar_completo(self, p, f, x, y, esc=None, t=None):
        arte.dibujar_pez(p, f.sp, x, y, f.escala if esc is None else esc, f.dir,
                         self.t if t is None else t)

    # ------------------------------------------------------------------ dibujo general
    def dibujar_juego(self, p):
        p.blit(self.bg, (0, 0))
        fase = self.fase
        self._burbujas(p)
        if fase not in ("forcejeo", "captura"):
            for f in sorted(self.peces, key=lambda z: -z.largo):
                self._dibujar_parte(p, f)
        for r in self.tiras_frente:
            p.blit(self.frente, r.topleft, r)
        roll = math.sin(self.t * 1.3) * (1.5 + 4.0 * self.estab)
        bob = math.sin(self.t * 1.7) * (1.0 + 1.5 * self.estab)
        arte_mar.dibujar_barco(p, self.barco, BX, WY + 2 + bob, self.t, roll)
        self._olas(p)
        tip = self._dibujar_cana(p)
        if fase == "apuntar":
            self._dibujar_mira(p, tip)
        elif fase in ("vuelo", "esperar", "mordida"):
            self._dibujar_linea(p, tip)
        elif fase == "forcejeo":
            self._dibujar_forcejeo(p, tip)
        elif fase == "captura":
            self._dibujar_captura(p, tip)
        for q in self.particulas:
            q.dibujar(p)
        self._dibujar_ui(p)

    def _burbujas(self, p):
        for i in range(9):
            x = (i * 151 + 60) % ANCHO
            y = ALTO - ((self.t * (22 + 6 * i) + i * 83) % (ALTO - WY))
            pygame.draw.circle(p, (200, 235, 250), (int(x + math.sin(self.t + i) * 8), int(y)), 3 + i % 3, 1)

    def _olas(self, p):
        pts = [(x, WY + math.sin(x * 0.03 + self.t * 2.2) * 3) for x in range(0, ANCHO + 20, 20)]
        pygame.draw.lines(p, (235, 250, 255), False, pts, 3)
        if self._ola is None:
            self._ola = pygame.Surface((520, 20), pygame.SRCALPHA)
            self._ola.fill((*self.bg.get_at((60, WY + 30))[:3], 120))
        p.blit(self._ola, (0, WY + 5))

    def _dibujar_cana(self, p):
        k = self.k if self.fase == "forcejeo" else 0.0
        base = self.mano
        tip = V2(self.punta) + V2(-26 * k, 22 * k)
        ctrl_pt = (base + tip) / 2 + V2(6, -34 - 26 * k)
        pts = []
        for i in range(14):
            u = i / 13
            pts.append(((1 - u) ** 2 * base.x + 2 * u * (1 - u) * ctrl_pt.x + u * u * tip.x,
                        (1 - u) ** 2 * base.y + 2 * u * (1 - u) * ctrl_pt.y + u * u * tip.y))
        pygame.draw.lines(p, (80, 55, 30), False, pts, 8)
        pygame.draw.lines(p, (160, 115, 65), False, pts, 4)
        pygame.draw.circle(p, (60, 60, 75), (int(base.x + 8), int(base.y + 10)), 11)
        pygame.draw.circle(p, (225, 70, 70), (int(base.x + 8), int(base.y + 10)), 7)
        return tip

    def _linea_aire(self, p, a, b, color=(255, 255, 255), sag=18, w=2):
        pts = []
        for i in range(17):
            u = i / 16
            pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + sag * 4 * u * (1 - u)))
        pygame.draw.lines(p, color, False, pts, w)

    def _anzuelo(self, p, x, y, brillo=False):
        x, y = int(x), int(y)
        if brillo:
            pygame.draw.circle(p, (255, 240, 130), (x, y + 6), 22, 3)
        pygame.draw.arc(p, (230, 235, 245), (x - 9, y - 2, 18, 22), math.pi * 1.0, math.pi * 2.05, 4)
        pygame.draw.line(p, (230, 235, 245), (x + 9, y + 8), (x + 9, y - 2), 3)
        pygame.draw.line(p, (230, 235, 245), (x - 9, y + 9), (x - 13, y + 4), 3)
        pygame.draw.circle(p, (240, 110, 120), (x - 3, y + 15), 4)

    def _dibujar_linea(self, p, tip):
        hx, hy = self.hx, self.hy
        if self.fase == "vuelo":
            self._linea_aire(p, tip, (hx, hy), sag=10)
        elif hy <= WY:
            self._linea_aire(p, tip, (hx, hy), sag=10)
        else:
            self._linea_aire(p, tip, (hx, WY), sag=22)
            pygame.draw.line(p, (255, 255, 255), (hx, WY), (hx, hy), 2)
        self._anzuelo(p, hx, hy, self.fase == "mordida")
        if self.fase == "esperar" and self.hy > WY:
            for i in range(2):
                u = ((self.t * 0.7) + i * 0.5) % 1.0
                rect = pygame.Rect(0, 0, 20 + u * 60, 6 + u * 14)
                rect.center = (int(hx), WY + 3)
                pygame.draw.ellipse(p, (225, 245, 255), rect, 2)

    def _pos_pez_forcejeo(self):
        q = V2(self.punta.x + 40, WY + 80)
        u = max(0.0, min(1.2, self.dist))
        pos = q + (self.hook0 - q) * u
        sac = 1.0 + 3.0 * self.k
        pos += V2(math.sin(self.t * 21) * 5 * sac, math.cos(self.t * 17) * 4 * sac)
        return pos

    def _dibujar_forcejeo(self, p, tip):
        f = self.pez
        pos = self._pos_pez_forcejeo()
        kk = max(0.0, min(1.0, self.k))
        color = (255, int(255 - 175 * kk), int(255 - 205 * kk))
        self._linea_aire(p, tip, (pos.x, WY), color, sag=8 * (1 - kk), w=3)
        pygame.draw.line(p, color, (pos.x, WY), (pos.x, pos.y - 4), 3)
        f.dir = -1 if pos.x > self.punta.x else 1
        esc = f.escala
        arte.dibujar_pez(p, f.sp, pos.x, pos.y, esc, f.dir, self.t * (1 + self.k))
        pygame.draw.circle(p, GRADO_COLOR[f.grado], (int(pos.x), int(pos.y)), int(max(50, f.largo * 0.5)), 4)
        if self.aviso and int(self.t * 10) % 2 == 0:
            escribir(p, self.f.grande, "¡Tira fuerte!", pos.x, pos.y - f.largo * 0.45 - 30, color=(255, 120, 100))

    def _dibujar_captura(self, p, tip):
        f = self.pez
        if f is None:
            return
        tf = self.t_fase
        u = min(1.0, tf / 0.9)
        q = V2(self.punta.x + 40, WY + 80)
        x = q.x + (640 - q.x) * u
        y = q.y + (390 - q.y) * u - 250 * 4 * u * (1 - u)
        esc = f.escala * min(2.0, 330 / f.largo) * (0.5 + 0.5 * u)
        bal = 0 if u < 1 else math.sin(tf * 6) * 0.05
        arte.dibujar_pez(p, f.sp, x, y, esc * (1 + bal), 1, self.t)
        if u >= 1:
            nom = f.dat[0]
            escribir(p, self.f.grande, f"¡{nom}!", 640, 160)
            n = f.grado
            for i in range(n):
                estrella(p, 640 + (i - (n - 1) / 2) * 46, 600, 19, GRADO_COLOR[n], oscurecer(GRADO_COLOR[n], 0.5))
            if self.nuevo:
                escribir(p, self.f.normal, "¡Pez nuevo en tu registro!", 640, 640, color=(255, 235, 110))
            if f.evento:
                escribir(p, self.f.normal, "¡Capturaste un animal de evento!", 640, 210, color=(220, 190, 255))
            for i, txt in enumerate(self.msgs_pesca[:3]):
                escribir(p, self.f.normal, txt, 640, 250 + 34 * i, color=(255, 235, 140))

    def _dibujar_mira(self, p, tip):
        dist = self.mira_x - self.punta.x
        col = (255, 90, 80) if self.mira_lejos else (255, 255, 255)
        # trayectoria prevista
        h = self._altura_arco(self.mira_x)
        for i in range(2, 22):
            u = i / 22
            x = self.punta.x + (self.mira_x - self.punta.x) * u
            y = self.punta.y + (WY - self.punta.y) * u - h * 4 * u * (1 - u)
            pygame.draw.circle(p, col, (int(x), int(y)), 4 if i % 2 else 3)
        # limite de la cuerda en el agua
        yp = WY + self.prof
        for x in range(0, ANCHO, 36):
            pygame.draw.line(p, (255, 255, 255), (x, yp), (x + 18, yp), 2)
        escribir(p, self.f.chica, "Hasta aquí llega tu cuerda", 1260, yp - 12, ancla="der", contorno=(20, 60, 100))
        # marca de caida
        pul = 1 + 0.08 * math.sin(self.t * 6)
        r = pygame.Rect(0, 0, int(88 * pul), int(26 * pul))
        r.center = (int(self.mira_x), WY + 4)
        pygame.draw.ellipse(p, col, r, 4)
        pygame.draw.ellipse(p, (255, 235, 110) if not self.mira_lejos else (255, 150, 140), r.inflate(-30, -12), 3)
        for i in range(0, 10):
            pygame.draw.line(p, (255, 255, 255), (self.mira_x, WY + 18 + i * 12), (self.mira_x, WY + 24 + i * 12), 2)
        txt = f"{dist / PX_POR_METRO:.0f} m"
        if self.mira_lejos:
            txt += "  ¡Muy lejos!"
        escribir(p, self.f.normal, txt, self.mira_x + 14, WY + 40, color=col, ancla="izq")
        # maximo alcance
        xm = self.x_max
        pygame.draw.line(p, (255, 230, 120), (xm, WY - 14), (xm, WY + 14), 4)
        escribir(p, self.f.chica, "máx", xm, WY - 26, color=(255, 230, 120))

    # ------------------------------------------------------------------ interfaz
    def _pips(self, p, x, y, n, maximo, w=26, h=16, gap=5, borde=2):
        for i in range(maximo):
            r = pygame.Rect(x + i * (w + gap), y - h // 2, w, h)
            if i < n:
                pygame.draw.rect(p, (110 + 28 * i, 215 - 18 * i, 110), r, border_radius=max(3, h // 3))
            else:
                pygame.draw.rect(p, (150, 160, 190), r, border_radius=max(3, h // 3))
            pygame.draw.rect(p, (60, 70, 110), r, borde, border_radius=max(3, h // 3))

    def _dibujar_equipo_mini(self, p):
        panel(p, (8, ALTO - 50, 590, 42), (255, 255, 255), 215, 14)
        x = 22
        for ranura in pesca_datos.TIPOS_HERR:
            escribir(p, self.f.chica, NOMBRE_PIEZA[ranura], x, ALTO - 29, (40, 50, 90), "izq", contorno=None)
            self._pips(p, x + 80, ALTO - 29, self.par[ranura], 5, 14, 14, 3, 1)
            x += 192
        escribir(p, self.f.chica, self.zona_nombre, 24, 120, ancla="izq", color=(255, 255, 255))
        if self.limitado:
            escribir(p, self.f.chica, self.aviso_equipo, 24, 144, ancla="izq", color=(255, 215, 120))

    def _dibujar_leyenda(self, p):
        panel(p, (918, ALTO - 50, 354, 42), (255, 255, 255), 215, 14)
        escribir(p, self.f.chica, "Dificultad", 930, ALTO - 29, (40, 50, 90), "izq", contorno=None)
        for g in range(1, 6):
            cx = 1042 + (g - 1) * 46
            pygame.draw.circle(p, GRADO_COLOR[g], (cx, ALTO - 29), 15)
            pygame.draw.circle(p, (255, 255, 255), (cx, ALTO - 29), 15, 2)
            escribir(p, self.f.chica, str(g), cx, ALTO - 30, contorno=(40, 40, 60), grosor=1)

    def _dibujar_ui(self, p):
        f = self.fase
        normal, grande = self.f.normal, self.f.grande
        self._dibujar_equipo_mini(p)
        self._dibujar_leyenda(p)
        if self.boton:
            self.boton.dibujar(p, grande)
        if self.b_modo:
            self.b_modo.dibujar(p, self.f.chica)
        if self.b_recoger and not self.recogiendo:
            self.b_recoger.dibujar(p, normal)
        if f == "apuntar":
            if self.modo_gesto:
                escribir(p, grande, "¡Haz un tajo para lanzar!", 640, 178)
                escribir(p, normal, "La fuerza del gesto decide hasta dónde llega", 640, 222)
            else:
                escribir(p, grande, "¡Apunta y lanza!", 640, 178)
                escribir(p, normal, "Mueve el cursor: la marca es donde cae el anzuelo", 640, 222)
            if self.capturados:
                escribir(p, normal, f"Peces: {self.capturados}", 24, ALTO - 66, ancla="izq")
        elif f == "esperar":
            puntos = "." * (1 + int(self.t * 2) % 3)
            if self.recogiendo:
                escribir(p, grande, "Recogiendo...", 640, 178)
            else:
                escribir(p, grande, "Espera" + puntos, 640, 178)
                escribir(p, normal, "La línea se queda hasta que pique un pez", 640, 222)
        elif f == "mordida":
            sac = math.sin(self.t * 30) * 4
            escribir(p, self.f.enorme, "¡Pica!", 640 + sac, 172, color=(255, 235, 90), contorno=(180, 40, 40), grosor=4)
            barra(p, (500, 100, 280, 16), 1 - self.t_fase / self.ventana, color=(255, 190, 60))
        elif f == "forcejeo":
            self._dibujar_tension(p)
        elif f == "pausa":
            escribir(p, grande, self.msg, 640, 178, color=self.msg_color)
            for i, txt in enumerate(self.msgs_pesca[:2]):
                escribir(p, normal, txt, 640, 228 + 34 * i, color=(255, 220, 150))
        if self.msg_t > 0 and f in ("apuntar", "esperar", "mordida"):
            escribir(p, normal, self.msg, 640, 252 + 24, color=self.msg_color)
        if self.banner_t > 0:
            w = 760
            panel(p, (640 - w / 2, 290, w, 66), (120, 60, 200), 225, 22, (255, 255, 255))
            escribir(p, grande, self.banner, 640, 323, color=(255, 240, 150))
        elif self.evento is not None:
            if int(self.t * 2) % 2 == 0:
                escribir(p, self.f.chica, "¡Evento en el agua!", 24, 144, ancla="izq", color=(230, 200, 255))

    def _dibujar_tension(self, p):
        f = self.pez
        normal, grande = self.f.normal, self.f.grande
        # barras de arriba: cercania del pez y su fuerza
        barra(p, (460, 14, 320, 26), 1 - self.dist, color=(90, 215, 120))
        escribir(p, self.f.chica, "El pez se acerca", 792, 28, ancla="izq")
        barra(p, (460, 48, 320, 16), self.e, color=(255, 190, 60))
        escribir(p, self.f.chica, "Fuerza del pez", 792, 57, ancla="izq")
        # tension de la linea (vertical, a la derecha)
        tr = pygame.Rect(1226, 270, 34, 340)
        pygame.draw.rect(p, (255, 255, 255), tr.inflate(8, 8), border_radius=17)
        pygame.draw.rect(p, (60, 65, 90), tr, border_radius=15)
        kk = max(0.0, min(1.0, self.k))
        alto = int(tr.h * kk)
        if alto > 2:
            col = (int(90 + 165 * kk), int(215 - 140 * kk), 90)
            pygame.draw.rect(p, col, (tr.x, tr.bottom - alto, tr.w, alto), border_radius=15)
        y_peligro = tr.bottom - int(tr.h * 0.78)
        pygame.draw.line(p, (255, 90, 80), (tr.x - 6, y_peligro), (tr.right + 6, y_peligro), 4)
        escribir(p, self.f.chica, "Cuerda", tr.centerx - 4, tr.y - 18)
        escribir(p, self.f.chica, "¡Peligro!", tr.centerx - 10, y_peligro - 14, ancla="centro", color=(255, 140, 130))
        # mensaje grande (siempre visible, sin parpadeos que cansen)
        if self.k > 0.78 or self.aviso:
            pul = 0.5 + 0.5 * math.sin(self.t * 12)
            col = (255, int(110 + 60 * pul), int(90 + 50 * pul))
            escribir(p, self.f.enorme, "¡Afloja!", 640, 172, color=col, contorno=(120, 20, 30), grosor=4)
            escribir(p, normal, "Gira al revés", 640, 228, color=(255, 200, 180))
            self._dibujar_guia_giro(p, -1, "¡Afloja! Gira al revés")
        elif not self.enrolla:
            escribir(p, self.f.enorme, "¡Enrolla!", 640, 172, color=(120, 235, 140), contorno=(20, 90, 40), grosor=4)
            escribir(p, normal, "Haz círculos así", 640, 228, color=(190, 250, 200))
            self._dibujar_guia_giro(p, 1, "¡Enrolla! Gira así")
        else:
            escribir(p, grande, "¡Enrolla!", 640, 172, color=(150, 245, 160))
            self._dibujar_guia_giro(p, 1, "¡Enrolla! Gira así")

    def _dibujar_guia_giro(self, p, sentido, texto):
        """Indicador fijo (a la derecha): anillo con flechas animadas en el sentido pedido (+1 horario verde =
        enrolla, -1 antihorario rojo = afloja). La perilla del centro gira como el jugador; la palomita dice si va bien."""
        cx, cy, R = GUIA_X, GUIA_Y, 52
        if sentido > 0:
            col, col2, bien = (90, 235, 120), (200, 255, 210), self.giro_on
        else:
            col, col2, bien = (255, 120, 100), (255, 205, 190), not self.giro_on      # quieto tambien afloja
        panel(p, (cx - 112, cy - R - 20, 224, 2 * R + 76), (20, 40, 70), 120, 18, col)
        n = 26
        for i in range(n):
            a = 2 * math.pi * i / n
            pygame.draw.circle(p, col, (int(cx + R * math.cos(a)), int(cy + R * math.sin(a))), 4 if i % 2 else 3)
        base = self.t * 2.6 * sentido          # en pantalla (y hacia abajo) el angulo creciente es horario
        for i in range(3):
            a = base + i * 2 * math.pi / 3
            for k in range(1, 7):              # estela detras de la punta
                b = a - sentido * k * 0.1
                pygame.draw.circle(p, col2, (int(cx + R * math.cos(b)), int(cy + R * math.sin(b))), max(2, 7 - k))
            tx, ty = -math.sin(a) * sentido, math.cos(a) * sentido
            nx, ny = math.cos(a), math.sin(a)
            tip = (cx + R * nx + 17 * tx, cy + R * ny + 17 * ty)
            l1 = (cx + R * nx - 8 * tx + 11 * nx, cy + R * ny - 8 * ty + 11 * ny)
            l2 = (cx + R * nx - 8 * tx - 11 * nx, cy + R * ny - 8 * ty - 11 * ny)
            pygame.draw.polygon(p, col2, [tip, l1, l2])
            pygame.draw.polygon(p, (50, 50, 80), [tip, l1, l2], 2)
        # perilla: gira igual que tu cursor
        kx, ky = cx + 26 * math.cos(self.ang_perilla), cy + 26 * math.sin(self.ang_perilla)
        pygame.draw.line(p, (60, 60, 75), (cx, cy), (kx, ky), 5)
        pygame.draw.circle(p, col if bien else (200, 200, 210), (int(kx), int(ky)), 10)
        pygame.draw.circle(p, (60, 60, 75), (int(kx), int(ky)), 10, 3)
        pygame.draw.circle(p, (60, 60, 75), (cx, cy), 6)
        # palomita: giras bien
        if bien:
            pygame.draw.circle(p, (90, 220, 120), (cx + R + 6, cy - R + 4), 17)
            pygame.draw.lines(p, (255, 255, 255), False, [(cx + R - 3, cy - R + 5), (cx + R + 3, cy - R + 12),
                                                          (cx + R + 15, cy - R - 4)], 5)
        escribir(p, self.f.chica, texto, cx, cy + R + 34, color=col2)

    def _flecha(self, p, x, y, sentido, color):
        off = math.sin(self.t * 8) * 8
        y = y + off * sentido * -1
        pts = [(x, y - 36 * sentido), (x - 34, y), (x + 34, y)]
        pygame.draw.polygon(p, color, pts)
        pygame.draw.polygon(p, (255, 255, 255), pts, 4)
