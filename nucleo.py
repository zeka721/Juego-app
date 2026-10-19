"""Base compartida de Ninja Mundo: control, interfaz, sonido, partida guardada y la
clase Minijuego de la que heredan todos los minijuegos.

Todo se dibuja con codigo (sin imagenes ni sonidos externos).
"""

import json
import math
import random
from array import array

import pygame

from ajustes import (ANCHO, ALTO, ARCHIVO_PARTIDA, DWELL_SEG, RULETA_CADA, USOS_MEJORA)
from catalogo import EQUIPO_INICIAL

V2 = pygame.Vector2


# =====================================================================
#  Control: lo que cada escena ve del mando (o del raton, o de una prueba)
# =====================================================================

class ControlBase:
    """Campos que usan las escenas (se actualizan una vez por cuadro):

    pos        Vector2  cursor en pantalla
    p1, p2     Vector2  inicio y fin del movimiento de este cuadro (para cortes)
    vel        float    velocidad del cursor en px/s
    cortando   bool     True mientras el movimiento es un tajo rapido
    clic       bool     True solo en el cuadro en que se pulso el boton / clic
    golpe      bool     True solo en el cuadro en que hubo un golpe/sacudida del mando
    inclinacion Vector2 desviacion del centro, de -1 a 1 en cada eje (x derecha, y abajo)
    """

    def __init__(self):
        self.pos = V2(ANCHO / 2, ALTO / 2)
        self.p1 = V2(self.pos)
        self.p2 = V2(self.pos)
        self.vel = 0.0
        self.cortando = False
        self.clic = False
        self.golpe = False

    @property
    def inclinacion(self):
        x = (self.pos.x - ANCHO / 2) / (ANCHO / 2)
        y = (self.pos.y - ALTO / 2) / (ALTO / 2)
        return V2(max(-1.0, min(1.0, x)), max(-1.0, min(1.0, y)))

    def centrar(self):
        self.pos.update(ANCHO / 2, ALTO / 2)
        self.p1 = V2(self.pos)
        self.p2 = V2(self.pos)


class ControlSim(ControlBase):
    """Control falso para pruebas automaticas sin mando ni pantalla."""

    def mover_a(self, x, y, dt=1 / 60, cortando=None, umbral_px=900.0):
        self.p1 = V2(self.pos)
        self.pos = V2(x, y)
        self.p2 = V2(self.pos)
        self.vel = self.p1.distance_to(self.p2) / dt if dt > 0 else 0.0
        self.cortando = (self.vel > umbral_px) if cortando is None else cortando

    def fin_cuadro(self):
        self.clic = False
        self.golpe = False
        self.cortando = False
        self.p1 = V2(self.pos)
        self.p2 = V2(self.pos)
        self.vel = 0.0


# =====================================================================
#  Utilidades de dibujo
# =====================================================================

def aclarar(color, f=0.45):
    return tuple(int(c + (255 - c) * f) for c in color)


def oscurecer(color, f=0.35):
    return tuple(int(c * (1 - f)) for c in color)


class Fuentes:
    def __init__(self):
        nombre = "arial"
        self.chica = pygame.font.SysFont(nombre, 20)
        self.normal = pygame.font.SysFont(nombre, 28, bold=True)
        self.grande = pygame.font.SysFont(nombre, 44, bold=True)
        self.enorme = pygame.font.SysFont(nombre, 76, bold=True)


_cache_gradientes = {}


def fondo(pantalla, arriba=(120, 190, 255), abajo=(215, 240, 255)):
    """Pinta un degradado vertical (se guarda para no recalcularlo cada cuadro)."""
    clave = (arriba, abajo, pantalla.get_size())
    sup = _cache_gradientes.get(clave)
    if sup is None:
        ancho, alto = pantalla.get_size()
        sup = pygame.Surface((ancho, alto))
        for y in range(alto):
            f = y / max(1, alto - 1)
            color = tuple(int(arriba[i] + (abajo[i] - arriba[i]) * f) for i in range(3))
            pygame.draw.line(sup, color, (0, y), (ancho, y))
        _cache_gradientes[clave] = sup
    pantalla.blit(sup, (0, 0))


def escribir(pantalla, fuente, texto, x, y, color=(255, 255, 255), ancla="centro",
             contorno=(30, 30, 50), grosor=2):
    """Texto con contorno para que se lea sobre cualquier fondo."""
    base = fuente.render(str(texto), True, color)
    ancho, alto = base.get_size()
    if ancla == "centro":
        px, py = x - ancho / 2, y - alto / 2
    elif ancla == "izq":
        px, py = x, y - alto / 2
    else:                                   # der
        px, py = x - ancho, y - alto / 2
    if contorno:
        sombra = fuente.render(str(texto), True, contorno)
        for dx in range(-grosor, grosor + 1):
            for dy in range(-grosor, grosor + 1):
                if dx or dy:
                    pantalla.blit(sombra, (px + dx, py + dy))
    pantalla.blit(base, (px, py))
    return pygame.Rect(px, py, ancho, alto)


def estrella(pantalla, cx, cy, r, color=(255, 210, 60), borde=(160, 110, 20), puntas=5):
    pts = []
    for i in range(puntas * 2):
        ang = -math.pi / 2 + i * math.pi / puntas
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    pygame.draw.polygon(pantalla, color, pts)
    if borde:
        pygame.draw.polygon(pantalla, borde, pts, max(1, int(r / 8)))


def corazon(pantalla, cx, cy, r, color=(235, 70, 90), borde=(130, 20, 40)):
    pts = []
    for i in range(40):
        t = i / 40 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 17, cy + y * r / 17))
    pygame.draw.polygon(pantalla, color, pts)
    if borde:
        pygame.draw.polygon(pantalla, borde, pts, max(1, int(r / 9)))


def corazones(pantalla, vidas, maximo, x, y, r=16, sep=40):
    for i in range(maximo):
        if i < vidas:
            corazon(pantalla, x + i * sep, y, r)
        else:
            corazon(pantalla, x + i * sep, y, r, color=(200, 200, 215), borde=(130, 130, 150))


def barra(pantalla, rect, frac, color=(90, 200, 120), color_fondo=(60, 65, 90), borde=(20, 20, 40)):
    rect = pygame.Rect(rect)
    frac = max(0.0, min(1.0, frac))
    pygame.draw.rect(pantalla, color_fondo, rect, border_radius=rect.height // 2)
    if frac > 0:
        pygame.draw.rect(pantalla, color,
                         (rect.x, rect.y, max(rect.height, rect.width * frac), rect.height),
                         border_radius=rect.height // 2)
    pygame.draw.rect(pantalla, borde, rect, 2, border_radius=rect.height // 2)


def dibujar_rotado(pantalla, superficie, x, y, angulo):
    rotada = pygame.transform.rotozoom(superficie, angulo, 1.0)
    pantalla.blit(rotada, rotada.get_rect(center=(int(x), int(y))))


def panel(pantalla, rect, color=(255, 255, 255), alfa=210, radio=22, borde=(40, 60, 110)):
    rect = pygame.Rect(rect)
    sup = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(sup, (*color, alfa), sup.get_rect(), border_radius=radio)
    pygame.draw.rect(sup, (*borde, 255), sup.get_rect(), 3, border_radius=radio)
    pantalla.blit(sup, rect.topleft)


class Boton:
    """Boton grande para el mando: se pulsa con el boton fisico / clic, o dejando el
    cursor encima DWELL_SEG segundos (se ve como un anillo que se llena)."""

    def __init__(self, rect, texto, color=(70, 160, 230), espera=0.6):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.color = color
        self.dwell = 0.0
        self.espera = espera          # ignora entradas justo al aparecer
        self.encima = False
        self.activo = True

    def actualizar(self, dt, ctrl):
        self.espera = max(0.0, self.espera - dt)
        self.encima = self.activo and self.rect.collidepoint(ctrl.pos.x, ctrl.pos.y)
        if not self.encima or self.espera > 0:
            self.dwell = max(0.0, self.dwell - dt * 2)
            return False
        self.dwell += dt
        if ctrl.clic or ctrl.golpe or self.dwell >= DWELL_SEG:
            self.dwell = 0.0
            return True
        return False

    def dibujar(self, pantalla, fuente):
        color = aclarar(self.color, 0.25) if self.encima else self.color
        if not self.activo:
            color = (170, 175, 190)
        sombra = self.rect.move(0, 6)
        pygame.draw.rect(pantalla, oscurecer(color, 0.5), sombra, border_radius=22)
        pygame.draw.rect(pantalla, color, self.rect, border_radius=22)
        pygame.draw.rect(pantalla, (255, 255, 255), self.rect, 4, border_radius=22)
        escribir(pantalla, fuente, self.texto, self.rect.centerx, self.rect.centery)
        if self.dwell > 0:
            frac = min(1.0, self.dwell / DWELL_SEG)
            r = pygame.Rect(self.rect.x + 14, self.rect.bottom - 16, self.rect.width - 28, 8)
            barra(pantalla, r, frac, color=(255, 230, 90), color_fondo=(110, 120, 150),
                  borde=(255, 255, 255))


class TextoFlotante:
    def __init__(self, texto, x, y, color=(255, 255, 255), vida=1.0, subida=60):
        self.texto, self.x, self.y, self.color = texto, x, y, color
        self.t = 0.0
        self.vida = vida
        self.subida = subida

    def actualizar(self, dt):
        self.t += dt
        return self.t < self.vida

    def dibujar(self, pantalla, fuente):
        f = self.t / self.vida
        y = self.y - self.subida * f
        escribir(pantalla, fuente, self.texto, self.x, y, self.color)


class Particula:
    def __init__(self, x, y, color, vel_min=80, vel_max=320, vida=0.7, gravedad=500, radio=5):
        ang = random.uniform(0, 2 * math.pi)
        vel = random.uniform(vel_min, vel_max)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(ang) * vel, math.sin(ang) * vel
        self.color, self.vida, self.t = color, vida, 0.0
        self.gravedad = gravedad
        self.radio = radio

    def actualizar(self, dt):
        self.t += dt
        self.vy += self.gravedad * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.t < self.vida

    def dibujar(self, pantalla):
        r = max(1, int(self.radio * (1 - self.t / self.vida)))
        pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), r)


def explosion(lista, x, y, color, n=14, **kw):
    for _ in range(n):
        lista.append(Particula(x, y, color, **kw))


# =====================================================================
#  Sonido sintetizado
# =====================================================================

class Sonidos:
    """Sonidos y notas sinteticos. Si no hay audio, todo sigue funcionando en silencio."""

    def __init__(self):
        self.ok = False
        self._cache = {}
        try:
            frecuencia, formato, canales = pygame.mixer.get_init()
            if formato != -16:
                raise RuntimeError("formato de audio no soportado")
            self.frec, self.canales = frecuencia, canales
            self.ok = True
        except Exception as e:
            print("Sin sonido:", e)
        self.silencio = False

    # --- generacion ---
    def _sonido(self, muestras):
        datos = array("h")
        for v in muestras:
            v = int(max(-1.0, min(1.0, v)) * 32767)
            datos.extend([v] * self.canales)
        return pygame.mixer.Sound(buffer=datos.tobytes())

    def _tono(self, f0, f1, dur, vol=0.3, forma="seno", caida=1.0):
        total = int(self.frec * dur)
        fase, out = 0.0, []
        for i in range(total):
            t = i / total
            fase += 2 * math.pi * (f0 + (f1 - f0) * t) / self.frec
            if forma == "cuadrada":
                onda = 1.0 if math.sin(fase) >= 0 else -1.0
                onda *= 0.6
            elif forma == "ruido":
                onda = random.uniform(-1, 1)
            else:
                onda = math.sin(fase)
            env = (1 - t) ** caida
            out.append(vol * env * onda)
        return self._sonido(out)

    def _crear(self, nombre):
        s = self
        tabla = {
            "corte": lambda: s._tono(950, 350, 0.12, 0.3),
            "fallo": lambda: s._tono(220, 120, 0.25, 0.3),
            "fin": lambda: s._tono(330, 90, 0.7, 0.3),
            "ok": lambda: s._tono(600, 900, 0.18, 0.28),
            "error": lambda: s._tono(200, 150, 0.22, 0.28, "cuadrada"),
            "click": lambda: s._tono(700, 500, 0.06, 0.25),
            "pop": lambda: s._tono(500, 1200, 0.09, 0.3),
            "moneda": lambda: s._tono(1000, 1500, 0.15, 0.25, "cuadrada"),
            "splash": lambda: s._tono(400, 80, 0.3, 0.3, "ruido", 2.0),
            "lanzar": lambda: s._tono(300, 900, 0.2, 0.25),
            "premio": lambda: s._tono(500, 1500, 0.5, 0.3),
            "tick": lambda: s._tono(1200, 1200, 0.03, 0.2, "cuadrada"),
            "bombo": lambda: s._tono(150, 45, 0.28, 0.6, "seno", 1.5),
            "caja": lambda: s._tono(250, 180, 0.16, 0.45, "ruido", 2.0),
            "platillo": lambda: s._tono(900, 900, 0.4, 0.22, "ruido", 2.5),
            "golpe": lambda: s._tono(180, 60, 0.15, 0.5, "seno", 1.5),
            "rugido": lambda: s._tono(140, 60, 0.5, 0.4, "cuadrada", 1.0),
        }
        return tabla[nombre]()

    def reproducir(self, nombre):
        if not self.ok or self.silencio:
            return
        try:
            snd = self._cache.get(nombre)
            if snd is None:
                snd = self._cache[nombre] = self._crear(nombre)
            snd.play()
        except Exception as e:                         # el sonido nunca debe romper el juego
            print("Error de sonido:", e)
            self.ok = False

    def nota(self, frecuencia, dur=0.3, vol=0.3):
        """Una nota musical (frecuencia en Hz)."""
        if not self.ok or self.silencio:
            return
        clave = ("nota", round(frecuencia), round(dur, 2))
        try:
            snd = self._cache.get(clave)
            if snd is None:
                snd = self._cache[clave] = self._tono(frecuencia, frecuencia, dur, vol, "seno", 1.2)
            snd.play()
        except Exception as e:
            print("Error de sonido:", e)
            self.ok = False


NOTAS = {"do": 261.63, "re": 293.66, "mi": 329.63, "fa": 349.23, "sol": 392.0,
         "la": 440.0, "si": 493.88, "do2": 523.25}


# =====================================================================
#  Partida guardada y mejoras
# =====================================================================

class Perfil:
    """Progreso del jugador (se guarda en partida.json)."""

    CAMPOS = ("estrellas", "puntos_totales", "puntos_pend", "fichas", "criaturas", "peces",
              "records", "mejoras", "jefe_vencido", "huesos", "polvo", "dinos",
              "monedas", "inventario", "equipo", "equipo_propio", "habilidades",
              "recetas_hechas", "figuras", "granja", "peces_vivos", "dia", "extra")

    def __init__(self, archivo=ARCHIVO_PARTIDA):
        self.archivo = archivo
        self.estrellas = {}            # id de nivel -> 0..3
        self.puntos_totales = 0
        self.puntos_pend = 0           # puntos hacia el proximo giro de ruleta
        self.fichas = 0                # giros de ruleta disponibles
        self.criaturas = []            # ids capturados
        self.peces = []                # especies de peces capturadas (coleccion del cuaderno)
        self.records = {}
        self.mejoras = {}              # nombre -> usos restantes
        self.jefe_vencido = False
        self.huesos = {}               # id de dinosaurio -> lista de indices de huesos hallados
        self.polvo = 0                 # polvo especial (para revivir esqueletos)
        self.dinos = []                # ids de dinosaurios revividos (paginas del libro)
        self.monedas = 150             # dinero del juego (tienda, gachapon)
        self.inventario = {"semilla_zanahoria": 3, "semilla_tomate": 3,
                           "alimento_animal": 6, "alimento_peces": 6}   # id de objeto -> cantidad
        self.equipo = dict(EQUIPO_INICIAL)         # pieza de pesca elegida en cada ranura
        self.equipo_propio = list(EQUIPO_INICIAL.values())   # ids de equipo que ya tienes
        self.habilidades = {}          # habilidad de cocina -> puntos de experiencia
        self.recetas_hechas = {}       # id de receta -> veces cocinada
        self.figuras = {}              # id de figura del gachapon -> cantidad (puede repetirse)
        self.granja = {}               # estado de la granja, el huerto y los estanques
        self.peces_vivos = {}          # especie -> cantidad de peces vivos capturados (balde)
        self.dia = 0                   # dias de juego (sube 1 por cada minijuego terminado)
        self.extra = {}                # espacio libre para datos de cada modulo
        self.cargar()

    def cargar(self):
        try:
            with open(self.archivo) as f:
                d = json.load(f)
            for k in self.CAMPOS:
                if k in d:
                    setattr(self, k, d[k])
        except Exception:
            pass

    def guardar(self):
        try:
            with open(self.archivo, "w") as f:
                json.dump({k: getattr(self, k) for k in self.CAMPOS}, f)
        except OSError as e:
            print("No se pudo guardar la partida:", e)

    # --- objetos y dinero ---
    def cantidad(self, item):
        return int(self.inventario.get(item, 0))

    def dar(self, item, n=1):
        if n <= 0:
            return
        self.inventario[item] = self.cantidad(item) + int(n)

    def quitar(self, item, n=1):
        """Quita n objetos. Devuelve False (sin quitar nada) si no hay suficientes."""
        if self.cantidad(item) < n:
            return False
        nuevo = self.cantidad(item) - int(n)
        if nuevo > 0:
            self.inventario[item] = nuevo
        else:
            self.inventario.pop(item, None)
        return True

    def tiene(self, requisitos):
        """requisitos = {item: cantidad}. True si hay de todo."""
        return all(self.cantidad(k) >= v for k, v in requisitos.items())

    def ganar(self, n):
        self.monedas = max(0, self.monedas + int(n))

    def gastar(self, n):
        """Gasta monedas. Devuelve False (sin gastar) si no alcanzan."""
        if self.monedas < n:
            return False
        self.monedas -= int(n)
        return True

    def sumar_puntos(self, n):
        """Suma puntos y devuelve cuantos giros de ruleta se ganaron."""
        self.puntos_totales += n
        self.puntos_pend += n
        nuevos = self.puntos_pend // RULETA_CADA
        self.puntos_pend -= nuevos * RULETA_CADA
        self.fichas += nuevos
        return nuevos

    def mejor_estrellas(self, nivel_id, n):
        if n > self.estrellas.get(nivel_id, 0):
            self.estrellas[nivel_id] = n

    def record(self, juego, puntos):
        if puntos > self.records.get(juego, 0):
            self.records[juego] = puntos
            return True
        return False

    def agregar(self, tipo, ident):
        """Agrega a la coleccion. Devuelve True si es nuevo."""
        lista = {"criatura": self.criaturas, "dino": self.dinos}.get(tipo, self.peces)
        if ident not in lista:
            lista.append(ident)
            return True
        return False


# nombre: (valor, descripcion corta, descripcion larga)
MEJORAS = {
    "tiempo": (1.25, "+25% tiempo", "Mas tiempo para jugar"),
    "potencia": (1.5, "Potencia x1.5", "Mas fuerza: carrete, golpes y dano al jefe"),
    "alcance": (1.3, "Alcance x1.3", "Todo es mas facil de alcanzar y cortar"),
    "lento": (0.8, "Todo mas lento", "El juego va 20% mas despacio"),
    "puntos": (2.0, "Puntos x2", "Cada acierto vale el doble"),
    "vida": (1, "+1 vida", "Un intento extra"),
}


class Mejoras:
    """Potenciadores que da la ruleta. Cada uno dura USOS_MEJORA minijuegos.

    Los minijuegos solo consultan mult('potencia'), mult('alcance'), mult('lento'),
    mult('tiempo'), mult('puntos') y vidas_extra()."""

    def __init__(self, perfil):
        self.perfil = perfil

    @property
    def activas(self):
        return self.perfil.mejoras

    def agregar(self, nombre):
        self.perfil.mejoras[nombre] = USOS_MEJORA

    def mult(self, nombre):
        return MEJORAS[nombre][0] if nombre in self.perfil.mejoras and nombre != "vida" else 1.0

    def vidas_extra(self):
        return 1 if "vida" in self.perfil.mejoras else 0

    def gastar_uso(self):
        for k in list(self.perfil.mejoras):
            self.perfil.mejoras[k] -= 1
            if self.perfil.mejoras[k] <= 0:
                del self.perfil.mejoras[k]


class Contexto:
    """Lo que reciben los minijuegos: sonidos, fuentes, partida y mejoras."""

    def __init__(self, sonidos, fuentes, perfil, mejoras):
        self.sonidos = sonidos
        self.f = fuentes
        self.perfil = perfil
        self.mejoras = mejoras


# =====================================================================
#  Clase base de los minijuegos
# =====================================================================

class Minijuego:
    """Para crear un minijuego: hereda de esta clase y define

        id, titulo, instruccion, duracion (segundos; None = sin limite)
        calcular_metas()     -> (puntos para 1, 2 y 3 estrellas)
        paso(dt, ctrl)       -> logica de un cuadro
        dibujar_juego(p)     -> dibuja la escena (el HUD lo pone la clase base)

    y llama a self.sumar(n) para dar puntos y self.terminar(mensaje) para acabar.
    El nivel (1..5) sube la dificultad. Las mejoras de la ruleta se consultan con
    self.mej.mult("potencia") etc.
    """

    id = "base"
    NIVEL_MAX = 5                      # Fosiles lo sube a 20 (grados de dificultad)
    titulo = "Minijuego"
    instruccion = ""
    duracion = 45.0
    gesto = "Mueve el mando"          # texto corto para la pantalla de instrucciones
    fondo_arriba = (120, 190, 255)
    fondo_abajo = (215, 240, 255)

    def __init__(self, ctx, nivel=1):
        self.ctx = ctx
        self.f = ctx.f
        self.sonidos = ctx.sonidos
        self.mej = ctx.mejoras
        self.nivel = max(1, min(self.NIVEL_MAX, int(nivel)))
        self.puntos = 0
        self.terminado = False
        self.ganado = None             # True/False si el juego decide (combate); None = por estrellas
        self.t = 0.0
        self.mensaje_final = ""
        self.recompensas = []          # [("criatura", "pelusin"), ("pez", "trucha"), ("dino", "...")]
        self.botin = {}                # objetos ganados: {"manzana": 3, "pescado": 1} (ver dar())
        self.flotantes = []
        self.metas = self.calcular_metas()
        if self.duracion:
            self.tiempo_total = self.duracion * self.mej.mult("tiempo")
            self.tiempo = self.tiempo_total
        else:
            self.tiempo_total = self.tiempo = None

    # --- a sobrescribir ---
    def calcular_metas(self):
        return (30, 60, 100)

    def paso(self, dt, ctrl):
        pass

    def dibujar_juego(self, pantalla):
        pass

    # --- servicios para los minijuegos ---
    def sumar(self, n, x=None, y=None, color=(255, 240, 120)):
        n = int(round(n * self.mej.mult("puntos")))
        self.puntos = max(0, self.puntos + n)
        if x is not None:
            texto = f"+{n}" if n >= 0 else str(n)
            self.flotantes.append(TextoFlotante(texto, x, y, color))
        return n

    def dar(self, item, n=1):
        """Gana objetos que la pantalla de resultados guardara en el inventario."""
        self.botin[item] = self.botin.get(item, 0) + int(n)

    def terminar(self, mensaje=""):
        if not self.terminado:
            self.terminado = True
            self.mensaje_final = mensaje

    def estrellas(self):
        if self.ganado is False:
            return 0
        return sum(1 for m in self.metas if self.puntos >= m)

    def superado(self):
        if self.ganado is not None:
            return self.ganado
        return self.estrellas() >= 1

    @property
    def lento(self):
        """Factor de velocidad del juego (0.8 si la ruleta dio 'todo mas lento')."""
        return self.mej.mult("lento")

    # --- ciclo (no sobrescribir) ---
    def actualizar(self, dt, ctrl):
        self.t += dt
        self.flotantes = [x for x in self.flotantes if x.actualizar(dt)]
        if self.terminado:
            return
        if self.tiempo is not None:
            self.tiempo -= dt
            if self.tiempo <= 0:
                self.tiempo = 0
                self.paso(dt, ctrl)
                self.terminar("Se acabo el tiempo")
                return
        self.paso(dt, ctrl)

    def dibujar(self, pantalla):
        fondo(pantalla, self.fondo_arriba, self.fondo_abajo)
        self.dibujar_juego(pantalla)
        self.dibujar_hud(pantalla)
        for x in self.flotantes:
            x.dibujar(pantalla, self.f.normal)

    def dibujar_hud(self, pantalla):
        escribir(pantalla, self.f.grande, f"Puntos: {self.puntos}", 24, 34, ancla="izq")
        # estrellas ganadas hasta ahora
        for i, meta in enumerate(self.metas):
            lleno = self.puntos >= meta
            estrella(pantalla, 40 + i * 44, 84, 17,
                     (255, 210, 60) if lleno else (200, 205, 220),
                     (160, 110, 20) if lleno else (140, 145, 165))
        if self.tiempo is not None:
            barra(pantalla, (ANCHO - 330, 22, 300, 26), self.tiempo / self.tiempo_total,
                  color=(255, 190, 60) if self.tiempo > 8 else (240, 80, 80))
            escribir(pantalla, self.f.chica, f"{int(self.tiempo) + 1} s", ANCHO - 180, 35)
        activas = list(self.mej.activas)
        for i, nombre in enumerate(activas):
            escribir(pantalla, self.f.chica, MEJORAS[nombre][1], ANCHO - 20, 70 + i * 24,
                     color=(255, 235, 140), ancla="der")
