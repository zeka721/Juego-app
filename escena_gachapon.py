"""Gachapon: una gran maquina de capsulas para ganar figuras coleccionables (rangos C a SSS).

Pantalla del menu principal (no es un minijuego). Se maneja solo con el cursor:
  - gira la manivela moviendo el cursor en circulos sobre ella: hay que darle VUELTAS (10) vueltas
    completas para que caiga la capsula. La manivela tiene inercia y fuerza (sigue al cursor con
    retraso, se frena sola) y mueve de verdad la paleta que revuelve las capsulas del globo, o
  - pulsa "Tirar x1" / "Tirar x10" (clic, golpe del mando o dejar el cursor encima 1 s): la maquina
    gira sola las 10 vueltas.
Suerte del album: el album tiene una pagina por mundo (Criaturas, Oceano, Prehistoria, Fantasia).
Cuanto mas llenas estan, mejores son las probabilidades de los rangos altos (figuras.suerte).
Cada tirada cuesta ajustes.GACHA_COSTO monedas. Puede salir repetido; cada figura se cuenta en
perfil.figuras[id]. "Mi coleccion" muestra todas las figuras (las que faltan, en silueta).

Para pruebas: self.rng (generador), self.forzar_rango (un rango o lista de rangos que se usan en
las siguientes tiradas), self.engano (probabilidad del color enganoso de la capsula),
self.pedir_tirada(n), self.saltar().
"""

import math
import random

import pygame

import ajustes
import figuras
from escena import Escena
from figuras import RANGOS, color_rango, color_arcoiris
from escena_items import ajustado
from nucleo import Boton, aclarar, barra, oscurecer, panel

V2 = pygame.Vector2
ANCHO, ALTO = ajustes.ANCHO, ajustes.ALTO

_TXT = {}


def escribir(p, fuente, texto, x, y, color=(255, 255, 255), ancla="centro", contorno=(30, 30, 50), grosor=2):
    """Texto con contorno (como nucleo.escribir) pero compuesto una sola vez y guardado: dibujarlo cuesta un blit."""
    clave = (id(fuente), str(texto), tuple(color), tuple(contorno) if contorno else None, grosor)
    c = _TXT.get(clave)
    if c is None:
        base = fuente.render(str(texto), True, color)
        w, h = base.get_size()
        if contorno:
            sombra = fuente.render(str(texto), True, contorno)
            sup = pygame.Surface((w + 2 * grosor, h + 2 * grosor), pygame.SRCALPHA)
            for dx in range(-grosor, grosor + 1):
                for dy in range(-grosor, grosor + 1):
                    if dx or dy:
                        sup.blit(sombra, (grosor + dx, grosor + dy))
            sup.blit(base, (grosor, grosor))
            off = grosor
        else:
            sup, off = base, 0
        if len(_TXT) > 900:
            _TXT.clear()
        c = _TXT[clave] = (sup, off, w, h)
    sup, off, w, h = c
    px = x - w / 2 if ancla == "centro" else (x if ancla == "izq" else x - w)
    py = y - h / 2
    p.blit(sup, (px - off, py - off))
    return pygame.Rect(px, py, w, h)

# ---------------------------------------------------------------- geometria de la maquina
GX, GY, GR = 640, 262, 165                      # globo de cristal (centro y radio)
MANIVELA = (566, 548)                           # centro de la manivela
MANIVELA_R = 56
RANURA = pygame.Rect(650, 566, 120, 72)         # salida de la capsula
TUBO = pygame.Rect(682, 462, 56, 88)            # ventanita del tubo
CAP_X = 710                                     # x por donde cae la capsula
AREA_MAQUINA = pygame.Rect(440, 60, 400, 640)
RANURA_MONEDA = (767, 502)                       # donde entran las monedas (placa a la derecha del tubo)

VUELTAS = 10                                    # vueltas de manivela para soltar una capsula
# manivela con fisica: el mango persigue al cursor como un muelle amortiguado (fuerza limitada)
MAN_K = 240.0                                   # rigidez del muelle cursor -> mango (rad/s^2 por rad)
MAN_C = 24.0                                    # amortiguacion
MAN_VMAX = 17.0                                 # velocidad maxima del mango (rad/s)
MAN_ROZ = 1.5                                   # rozamiento del mango al soltarlo (1/s)
ENGRANAJE = 0.75                                # la paleta del globo gira ENGRANAJE x lo que gira el mango
N_CAPS = 20                                     # capsulas dentro del globo
PALETA_L = GR - 16                              # largo de los brazos de la paleta
PALETA_ANCHO = 6                                # semiancho de un brazo
COLORES_CAP = [(240, 70, 70), (255, 150, 50), (255, 215, 60), (90, 200, 100),
               (70, 200, 220), (80, 130, 240), (170, 100, 230), (250, 120, 190)]

SEC1 = ["agitar", "caer", "rueda", "suspenso", "destello", "silueta", "rango"]
SEC10 = ["agitar", "lluvia", "rueda", "suspenso", "destello", "silueta", "rango"]
SEC1_MANUAL = SEC1[1:]                          # el jugador ya giro la manivela: empieza en "caer"
DUR = {"agitar": 4.0, "caer": 1.0, "lluvia": 2.4, "rueda": 0.9, "suspenso": 1.8,
       "destello": 1.3, "silueta": 1.2, "rango": 1.5}
FASES_ANIM = set(DUR)
SALTAR_DESDE = 1.0                              # segundos antes de poder saltar la animacion

# efectos de la apertura segun el rango
FX = {
    "C": dict(rayos=8, anillos=1, brillos=16, sacude=0.0, flash=0.5, espiral=False, rayos_t=0.8),
    "B": dict(rayos=10, anillos=2, brillos=26, sacude=0.0, flash=0.6, espiral=False, rayos_t=1.0),
    "A": dict(rayos=12, anillos=2, brillos=34, sacude=0.0, flash=0.7, espiral=True, rayos_t=1.2),
    "S": dict(rayos=16, anillos=3, brillos=50, sacude=3.0, flash=0.85, espiral=False, rayos_t=1.5),
    "SS": dict(rayos=20, anillos=3, brillos=76, sacude=7.0, flash=0.95, espiral=True, rayos_t=2.0),
    "SSS": dict(rayos=28, anillos=4, brillos=120, sacude=14.0, flash=1.0, espiral=True, rayos_t=2.6),
}
FANFARRIA = {
    "C": [392],
    "B": [440, 554],
    "A": [523, 659, 784],
    "S": [523, 659, 784, 1047],
    "SS": [523, 659, 784, 1047, 1319],
    "SSS": [392, 523, 659, 784, 1047, 1319, 1568],
}


# ---------------------------------------------------------------- ayudas
def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = max(0.0, min(1.0, x))
    return x * x


def ease_out_back(x, k=1.9):
    x = max(0.0, min(1.0, x))
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def monedas_txt(n):
    return f"{n} moneda" if n == 1 else f"{n} monedas"


def envolver(texto, fuente, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if fuente.size(prueba)[0] <= ancho or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def col_cap(rango, t=0.0):
    """Color de una capsula del rango dado."""
    if rango == "SSS":
        return color_arcoiris(t * 0.8, 0.7, 1.0)
    return figuras.COLOR_RANGO[rango]


def dibujar_media_capsula(p, x, y, r, color, ang=0.0, arriba=True, brillo=True):
    n = 20
    pts = []
    for k in range(n + 1):
        a = (math.pi if arriba else 0.0) + k * math.pi / n
        px, py = r * math.cos(a), r * math.sin(a)
        c, s = math.cos(ang), math.sin(ang)
        pts.append((x + px * c - py * s, y + px * s + py * c))
    pygame.draw.polygon(p, color, pts)
    pygame.draw.polygon(p, oscurecer(color, 0.55), pts, max(2, int(r / 14)))
    if arriba and brillo:
        c, s = math.cos(ang), math.sin(ang)
        hx, hy = -0.45 * r, -0.5 * r
        pygame.draw.circle(p, (255, 255, 255), (int(x + hx * c - hy * s), int(y + hx * s + hy * c)), max(2, int(r * 0.17)))
        hx, hy = -0.2 * r, -0.72 * r
        pygame.draw.circle(p, (255, 255, 255), (int(x + hx * c - hy * s), int(y + hx * s + hy * c)), max(1, int(r * 0.07)))


_ESFERA = {}


def _esfera(r):
    """Sombreado fijo de una esfera (la luz viene de arriba a la izquierda): sombra abajo-derecha, brillo
    arriba-izquierda y un reborde de luz. Se pinta encima de la capsula, que gira por debajo. Cacheado."""
    r = max(3, int(round(r)))
    sp = _ESFERA.get(r)
    if sp is None:
        d = r * 2 + 4
        c0 = d // 2
        sp = pygame.Surface((d, d), pygame.SRCALPHA)
        n = max(18, min(70, r // 2 + 10))
        for i in range(n):                                   # sombra: discos que se achican hacia la luz
            f = i / n
            rad = r * (1.0 - 0.62 * f)
            ox, oy = -0.30 * r * f, -0.34 * r * f
            pygame.draw.circle(sp, (20, 10, 50, int(112 * (1 - f) ** 1.5)), (int(c0 + ox), int(c0 + oy)), max(1, int(rad)))
        hl = pygame.Surface((d, d), pygame.SRCALPHA)
        m = max(12, min(50, r // 3 + 8))
        for i in range(m):                                   # brillo suave
            f = i / m
            pygame.draw.circle(hl, (255, 255, 255, int(32 + 150 * f * f)), (int(c0 - 0.36 * r), int(c0 - 0.40 * r)),
                               max(1, int(r * (0.42 - 0.34 * f))))
        sp.blit(hl, (0, 0))
        pygame.draw.circle(sp, (255, 255, 255, 215), (int(c0 - 0.43 * r), int(c0 - 0.47 * r)), max(1, int(r * 0.12)))
        pygame.draw.arc(sp, (255, 255, 255, 120), pygame.Rect(c0 - r + 2, c0 - r + 2, 2 * r - 4, 2 * r - 4),
                        math.radians(100), math.radians(168), max(1, int(r / 14)))      # reborde de luz
        pygame.draw.circle(sp, (30, 15, 60, 190), (c0, c0), r, max(1, int(r / 16)))     # contorno
        _ESFERA[r] = sp
    return sp


_BASE_CAP = {}


def _cuerpo_capsula(color, r):
    """Capsula sin girar (cacheada para tamanos pequenos); se rota al dibujarla."""
    clave = (color, r)
    sp = _BASE_CAP.get(clave)
    if sp is None:
        if len(_BASE_CAP) > 600:
            _BASE_CAP.clear()
        d = r * 2 + 6
        sp = pygame.Surface((d, d), pygame.SRCALPHA)
        c0 = d // 2
        dibujar_media_capsula(sp, c0, c0, r, (236, 240, 250), 0.0, arriba=False, brillo=False)
        dibujar_media_capsula(sp, c0, c0, r, color, 0.0, arriba=True, brillo=False)
        pygame.draw.line(sp, oscurecer(color, 0.5), (c0 - r, c0), (c0 + r, c0), max(2, int(r / 9)))
        _BASE_CAP[clave] = sp
    return sp


def dibujar_capsula(p, x, y, r, color, ang=0.0):
    """Capsula de juguete: mitad de color arriba, mitad clara abajo, con volumen."""
    if r <= 36 and abs(r - round(r)) < 1e-6:
        base = _cuerpo_capsula(tuple(color), int(round(r)))
        rot = pygame.transform.rotozoom(base, -math.degrees(ang), 1.0)
        p.blit(rot, (int(x - rot.get_width() / 2), int(y - rot.get_height() / 2)))
    else:
        dibujar_media_capsula(p, x, y, r, (236, 240, 250), ang, arriba=False, brillo=False)
        dibujar_media_capsula(p, x, y, r, color, ang, arriba=True, brillo=False)
        c, s = math.cos(ang), math.sin(ang)
        pygame.draw.line(p, oscurecer(color, 0.5), (x - r * c, y - r * s), (x + r * c, y + r * s), max(2, int(r / 9)))
    sp = _esfera(r)
    p.blit(sp, (int(x - sp.get_width() / 2), int(y - sp.get_height() / 2)))


_CAPAS = {}


def capa_efectos(p, dibujar, esc=0.5):
    """Dibuja efectos translucidos en una capa de menor resolucion y la pone encima suavizada.
    dibujar(sup, k) pinta en 'sup' (coordenadas de pantalla * k, k = esc)."""
    W, H = p.get_size()
    w, h = int(W * esc), int(H * esc)
    capa = _CAPAS.get((w, h))
    if capa is None:
        capa = _CAPAS[(w, h)] = pygame.Surface((w, h), pygame.SRCALPHA)
    capa.fill((0, 0, 0, 0))
    dibujar(capa, esc)
    p.blit(pygame.transform.smoothscale(capa, (W, H)), (0, 0))


def rayos(sup, k, cx, cy, n, rot, colores, alfa=90, largo=1100, ancho=0.5):
    for i in range(n):
        a0 = rot + i * 2 * math.pi / n
        a1 = a0 + 2 * math.pi / n * ancho
        col = colores(i)
        pts = [(cx * k, cy * k), ((cx + math.cos(a0) * largo) * k, (cy + math.sin(a0) * largo) * k),
               ((cx + math.cos(a1) * largo) * k, (cy + math.sin(a1) * largo) * k)]
        pygame.draw.polygon(sup, (*col, alfa), pts)


def brillo_suave(sup, k, cx, cy, radio, color, alfa=140, pasos=20):
    for j in range(pasos, 0, -1):
        f = j / pasos
        pygame.draw.circle(sup, (*color, int(alfa * (1 - f) ** 1.3 + 8)), (int(cx * k), int(cy * k)), max(1, int(radio * f * k)))


class Brillo:
    """Particula decorativa: estrella, circulo o confeti."""

    def __init__(self, x, y, vx, vy, vida, color, tipo="estrella", r=8, grav=300.0, vang=None):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vida, self.t = vida, 0.0
        self.color, self.tipo, self.r, self.grav = color, tipo, r, grav
        self.ang = random.uniform(0, 6.28)
        self.vang = vang if vang is not None else random.uniform(-6, 6)

    def actualizar(self, dt):
        self.t += dt
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.ang += self.vang * dt
        return self.t < self.vida and self.y < ALTO + 60

    def dibujar(self, p):
        f = self.t / self.vida
        esc = 1.0 if f < 0.7 else max(0.05, (1 - f) / 0.3)
        r = max(1.5, self.r * esc)
        if self.tipo == "estrella":
            figuras.arte_estrella(p, self.x, self.y, r, self.color, oscurecer(self.color, 0.5))
        elif self.tipo == "conf":
            c, s = math.cos(self.ang), math.sin(self.ang)
            w, h = r * 1.1, r * 0.55 * abs(math.cos(self.ang * 0.7)) + 1
            pts = [(self.x + dx * c - dy * s, self.y + dx * s + dy * c) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
            pygame.draw.polygon(p, self.color, pts)
        else:
            pygame.draw.circle(p, self.color, (int(self.x), int(self.y)), int(r))


class Cap:
    """Capsula dentro del globo."""

    def __init__(self, i):
        self.r = random.choice((23, 24, 25))
        a = random.uniform(0, 6.28)
        d = random.uniform(0, GR * 0.6)
        self.x, self.y = GX + math.cos(a) * d, GY + math.sin(a) * d * 0.7 + 30
        self.vx = self.vy = 0.0
        self.color = COLORES_CAP[i % len(COLORES_CAP)]
        self.ang = random.uniform(0, 6.28)
        self.vang = random.uniform(-2, 2)


# =====================================================================
class GachaponEscena(Escena):
    def __init__(self, app):
        super().__init__(app)
        f = self.f
        self.rng = random
        self.forzar_rango = None        # str o lista de rangos para las siguientes tiradas
        self.engano = 0.4               # probabilidad del color enganoso de la capsula
        self.fase = "inicio"            # inicio | coleccion | (fases de animacion) | figura | resumen
        self.tf = 0.0                   # tiempo dentro de la fase
        self.t_anim = 0.0
        self.seq = SEC1
        self.idx = 0
        self.modo = 1                   # 1 o 10 (cantidad de la tirada actual)
        self.res = None                 # resultado de la figura que se muestra
        self.lote = []                  # resultados de la tirada (1 o 10)
        self.ultimo = None              # id de la ultima figura destacada
        self.shake = 0.0
        self.flash = 0.0
        self.brillos = []
        self.agenda = []
        self.aviso = ""
        self.aviso_t = 0.0
        self.giro = 0.0                 # radianes que lleva girada la manivela en esta tirada
        self.ang_man = 0.0              # angulo del mango
        self.vel_man = 0.0              # velocidad del mango (rad/s)
        self.pal_ang = 0.0              # angulo de la paleta del globo
        self.pal_vel = 0.0              # su velocidad (rad/s), engranada con la manivela
        self.auto0 = 0.0                # angulo del mango al empezar el giro automatico
        self.manual = False             # la tirada actual salio de girar la manivela a mano
        self.paginas_nuevas = []        # paginas del album que esta tirada acaba de completar
        self.suerte_antes = 0.0
        self.suerte_despues = 0.0
        self.error_t = 0.0              # enfriamiento del sonido de "no hay monedas"
        self.luz = 0.0                  # fase de las luces de la marquesina (corren mas rapido con la manivela)
        self.fade = 0.8                 # velo negro que se desvanece al cambiar de pantalla
        self.monedas_vis = float(app.ctx.perfil.monedas)    # contador que sube/baja suave
        self.vuelos = []                # monedas que vuelan del contador a la ranura
        self.garantia_x10 = True        # el x10 asegura al menos una figura Rara (A) o mejor
        self.caps = [Cap(i) for i in range(N_CAPS)]
        self.cap_color_ap = (200, 200, 200)
        self.cap_pos = V2(CAP_X, 400)
        self.cap_r = 26
        self.cap_ang = 0.0
        self.cap_ini = V2(CAP_X, 600)
        self.cap_rango_ap = "C"
        self.cap_cambiada = False
        self.rayos_ang = 0.0
        self.tick_t = 0.0
        self.rayos_elec = []
        self.rayos_elec_t = 0.0
        self.lluvia = []                # capsulas de la tirada x10
        self.rayo_ang = 0.0
        self._sil_cache = {}
        self._letras = {}
        self._estrellas = [(random.uniform(0, ANCHO), random.uniform(0, ALTO), random.uniform(0.4, 1.0),
                            random.uniform(0, 6.28)) for _ in range(46)]
        # coleccion
        self.filtro = None
        self.pagina = 0
        self.detalle = None
        self.por_pagina = 12
        # botones
        self.b_tirar = Boton((930, 110, 320, 84), "", (230, 80, 120))
        self.b_x10 = Boton((930, 206, 320, 70), "", (150, 90, 230))
        self.b_coleccion = Boton((30, 100, 300, 84), "Mi colección", (240, 160, 60))
        self.b_volver = Boton((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.b_saltar = Boton((1070, ALTO - 78, 190, 56), "Saltar", (120, 120, 160), espera=0.2)
        self.b_seguir = Boton((330, 628, 270, 70), "Seguir", (90, 190, 110))
        self.b_otra = Boton((640, 628, 320, 70), "", (230, 80, 120))
        self.b_resumen = Boton((330, 628, 270, 70), "Ver resumen", (90, 190, 110))
        self.b_filtros = [Boton((50 + i * 242, 92, 232, 52), "", (110, 110, 140)) for i in range(1 + len(figuras.PAGINAS))]
        self.b_ant = Boton((330, ALTO - 78, 190, 56), "Anterior", (90, 150, 230))
        self.b_sig = Boton((760, ALTO - 78, 190, 56), "Siguiente", (90, 150, 230))
        self.b_maquina = Boton((24, ALTO - 78, 170, 56), "Máquina", (150, 150, 170))
        self.b_cerrar = Boton((540, 548, 200, 62), "Cerrar", (90, 190, 110))
        self.b_tarjetas = [Boton(self._rect_tarjeta(i), "") for i in range(self.por_pagina)]
        self._preparar_estaticos()
        self._rearmar()
        for _ in range(240):
            self._sim_caps(1 / 60)

    # ------------------------------------------------------------ datos
    @property
    def perfil(self):
        return self.app.ctx.perfil

    @property
    def sn(self):
        return self.app.ctx.sonidos

    @staticmethod
    def costo(n=1):
        return int(ajustes.GACHA_COSTO) * n

    def faltan(self, n=1):
        return max(0, self.costo(n) - self.perfil.monedas)

    def _rearmar(self):
        for b in (self.b_tirar, self.b_x10, self.b_coleccion, self.b_volver, self.b_seguir, self.b_otra,
                  self.b_resumen, self.b_ant, self.b_sig, self.b_maquina, self.b_cerrar,
                  *self.b_filtros, *self.b_tarjetas):
            b.espera = 0.5
            b.dwell = 0.0

    # ------------------------------------------------------------ tirada
    def _siguiente_forzado(self):
        fr = self.forzar_rango
        if isinstance(fr, (list, tuple)):
            if fr:
                lista = list(fr)
                v = lista.pop(0)
                self.forzar_rango = lista
                return v
            return None
        return fr

    def _aparente(self, rango):
        if self.rng.random() < self.engano:
            otros = [r for r in RANGOS if r != rango]
            return self.rng.choice(otros)
        return rango

    def probabilidades(self):
        """Probabilidades de cada rango con la suerte actual del album."""
        return figuras.probabilidades_efectivas(self.perfil)

    def pedir_tirada(self, n=1, manual=False):
        """Empieza una tirada (x1 o x10). Devuelve False si no hay monedas o ya hay una en marcha.
        manual=True: el jugador ya dio las VUELTAS con la manivela (no hay giro automatico)."""
        if self.fase != "inicio":
            return False
        perfil = self.perfil
        if perfil.monedas < self.costo(n):
            self.aviso_t = 2.5
            self.sn.reproducir("error")
            return False
        if not perfil.gastar(self.costo(n)):
            return False
        self.sn.reproducir("moneda")
        for k in range(1 if n == 1 else 6):            # monedas que vuelan a la ranura
            self.vuelos.append({"t": -0.09 * k, "p0": V2(964, 52), "p1": V2(*RANURA_MONEDA)})
        info = perfil.extra.setdefault("gachapon", {})
        lote = []
        probs = self.probabilidades()               # fijas durante toda la tirada (x10 incluida)
        completas = [figuras.pagina_completa(perfil, k) for k in range(len(figuras.PAGINAS))]
        self.suerte_antes = figuras.suerte(perfil)
        for k in range(n):
            info["tiradas"] = int(info.get("tiradas", 0)) + 1
            forzado = self._siguiente_forzado()
            minimo = figuras.rango_garantizado(info["tiradas"])
            if (n == 10 and k == n - 1 and self.garantia_x10 and forzado is None and minimo is None
                    and all(figuras.indice_rango(x["rango"]) < figuras.indice_rango("A") for x in lote)):
                minimo = "A"                          # la tirada x10 asegura una Rara o mejor
            ident = figuras.tirar(self.rng, rango=forzado, minimo=minimo, probs=probs)
            antes = perfil.figuras.get(ident, 0)
            perfil.figuras[ident] = antes + 1
            rango = figuras.rango_de(ident)
            lote.append({"id": ident, "rango": rango, "nueva": antes == 0, "cant": antes + 1,
                         "aparente": self._aparente(rango)})
        perfil.guardar()
        self.paginas_nuevas = [k for k in range(len(figuras.PAGINAS))
                               if not completas[k] and figuras.pagina_completa(perfil, k)]
        self.suerte_despues = figuras.suerte(perfil)
        self.lote = lote
        self.modo = n
        self.manual = bool(manual) and n == 1
        mejor = max(range(len(lote)), key=lambda i: (figuras.indice_rango(lote[i]["rango"]), lote[i]["nueva"], -i))
        self.res = lote[mejor]
        self.ultimo = self.res["id"]
        self.cap_rango_ap = self.res["aparente"]
        self.seq = (SEC1_MANUAL if self.manual else SEC1) if n == 1 else SEC10
        self.idx = -1
        self.t_anim = 0.0
        self.giro = 0.0
        self.aviso = ""
        self.rayos_elec = []
        self.brillos = []
        self.agenda = []
        self.shake = self.flash = 0.0
        self._siguiente_fase()
        return True

    def _siguiente_fase(self):
        self.idx += 1
        if self.idx >= len(self.seq):
            self._mostrar_figura()
            return
        self.fase = self.seq[self.idx]
        self.tf = 0.0
        self._entrar_fase()

    def _entrar_fase(self):
        f = self.fase
        res = self.res
        if f == "agitar":
            self.auto0 = self.ang_man          # la maquina gira sola las VUELTAS vueltas
            self.giro = 0.0
            self._vueltas_dadas = 0
        elif f == "caer":
            self.cap_pos = V2(CAP_X, 388)
            self.cap_r = 26
            self.cap_color_ap = col_cap(self.cap_rango_ap)
            self.sn.reproducir("pop")
        elif f == "lluvia":
            self.lluvia = [{"i": i, "r": r, "pos": V2(CAP_X, 600), "lanzada": False}
                           for i, r in enumerate(self.lote)]
            self.cap_cambiada = False
        elif f == "rueda":
            if self.modo == 1:
                self.cap_ini = V2(CAP_X, 604)
            else:
                k = self.lote.index(self.res)
                self.cap_ini = V2(self._destino_lluvia(k))
            self.cap_pos = V2(self.cap_ini)
            self.cap_r = 26 if self.modo == 1 else 34
            self.cap_color_ap = col_cap(self.cap_rango_ap)
            self.cap_cambiada = False
            self.sn.reproducir("lanzar")
        elif f == "suspenso":
            self.cap_pos = V2(640, 340)
            self.cap_r = 105
            self.cap_cambiada = (self.cap_rango_ap == res["rango"])
            self.cap_color_ap = col_cap(self.cap_rango_ap)
            self.tick_t = 0.0
        elif f == "destello":
            self._reventar()
        elif f == "silueta":
            self.sn.reproducir("rugido" if res["rango"] in ("SS", "SSS") else "pop")
        elif f == "rango":
            self._golpe_rango()

    def _destino_lluvia(self, k):
        n = max(1, len(self.lote))
        return (ANCHO / 2 + (k - (n - 1) / 2) * 106, 452)

    def _reventar(self):
        """Abre la capsula: destello y particulas segun el rango."""
        r = self.res["rango"]
        fx = FX[r]
        self.flash = fx["flash"]
        self.shake = max(self.shake, fx["sacude"] * 0.6)
        self.rayo_ang = 0.0
        for i in range(fx["brillos"]):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(160, 620 if r in ("SS", "SSS") else 480)
            col = color_arcoiris(random.random()) if r == "SSS" else (
                aclarar(figuras.COLOR_RANGO[r], random.uniform(0, 0.6)))
            self.brillos.append(Brillo(640 + math.cos(a) * 30, 340 + math.sin(a) * 30, math.cos(a) * v,
                                       math.sin(a) * v, random.uniform(0.7, 1.4), col,
                                       "estrella" if i % 2 == 0 else "circ", random.uniform(5, 13), 260))
        if r in ("S", "SS", "SSS"):
            self.sn.reproducir("premio")
            self.sn.reproducir("platillo")
        elif r in ("A", "B"):
            self.sn.reproducir("premio")
        else:
            self.sn.reproducir("pop")

    def _golpe_rango(self):
        """La letra del rango golpea la pantalla."""
        r = self.res["rango"]
        fx = FX[r]
        self.agenda = []
        for k, frec in enumerate(FANFARRIA[r]):
            self.agenda.append([0.25 + k * 0.11, "nota", frec])
        self.agenda.append([0.22, "snd", "golpe"])
        if r in ("S", "SS", "SSS"):
            self.agenda.append([0.22, "snd", "bombo"])
        if r in ("SS", "SSS"):
            self.agenda.append([0.25, "snd", "platillo"])
        if r == "SSS":
            self.agenda.append([0.3, "snd", "rugido"])
            self.agenda.append([0.9, "snd", "rugido"])
        self._shake_pendiente = fx["sacude"] * 1.8

    def _mostrar_figura(self):
        self.fase = "figura"
        self.tf = 0.0
        self.vel_man = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.brillos = [x for x in self.brillos if x.tipo == "conf"]
        self.b_seguir.espera = self.b_otra.espera = self.b_resumen.espera = 0.8
        self.b_seguir.dwell = self.b_otra.dwell = self.b_resumen.dwell = 0.0
        r = self.res["rango"]
        n = {"C": 12, "B": 20, "A": 30, "S": 50, "SS": 80, "SSS": 140}[r]
        for _ in range(n):
            self._confeti(arriba=False)
        self.sn.reproducir("premio")

    def saltar(self):
        """Salta la animacion (solo despues de SALTAR_DESDE segundos)."""
        if self.fase in FASES_ANIM and self.t_anim >= SALTAR_DESDE:
            self.agenda = []
            self._mostrar_figura()
            return True
        return False

    def _confeti(self, arriba=True):
        r = self.res["rango"] if self.res else "C"
        if r == "SSS":
            col = color_arcoiris(random.random())
        else:
            col = random.choice([figuras.COLOR_RANGO[r], aclarar(figuras.COLOR_RANGO[r], 0.5), (255, 255, 255),
                                 random.choice(COLORES_CAP)])
        x = random.uniform(0, ANCHO)
        y = random.uniform(-40, -5) if arriba else random.uniform(150, 420)
        vx = random.uniform(-60, 60) if arriba else random.uniform(-350, 350)
        vy = random.uniform(40, 160) if arriba else random.uniform(-520, -120)
        self.brillos.append(Brillo(x, y, vx, vy, random.uniform(2.0, 3.6), col,
                                   random.choice(("conf", "conf", "estrella")), random.uniform(6, 11), 220))

    # ------------------------------------------------------------ estaticos
    def _preparar_estaticos(self):
        f = self.f
        # cabina
        cab = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        pygame.draw.ellipse(cab, (30, 10, 60, 130), pygame.Rect(430, 650, 420, 64))
        for x in (500, 740):
            pygame.draw.rect(cab, (60, 30, 80), (x, 670, 60, 34), border_radius=10)
        cuerpo = pygame.Rect(470, 415, 340, 265)
        pygame.draw.rect(cab, (120, 25, 50), cuerpo.move(0, 8), border_radius=34)
        pygame.draw.rect(cab, (232, 62, 92), cuerpo, border_radius=34)
        self._degradado(cab, cuerpo, 34, (255, 255, 255, 34), (60, 0, 30, 105))
        pygame.draw.rect(cab, (255, 130, 150), (cuerpo.x + 14, cuerpo.y + 12, cuerpo.w - 28, 14), border_radius=7)
        pygame.draw.rect(cab, (255, 255, 255), cuerpo, 5, border_radius=34)
        pygame.draw.rect(cab, (255, 200, 60), (456, 402, 368, 30), border_radius=12)
        pygame.draw.rect(cab, (255, 245, 170), (462, 406, 356, 10), border_radius=5)
        pygame.draw.rect(cab, (150, 100, 20), (456, 402, 368, 30), 4, border_radius=12)
        panelf = pygame.Rect(488, 452, 304, 214)
        pygame.draw.rect(cab, (255, 236, 215), panelf, border_radius=24)
        pygame.draw.rect(cab, (150, 40, 70), panelf, 4, border_radius=24)
        # dial de la manivela
        pygame.draw.circle(cab, (110, 60, 80), (MANIVELA[0], MANIVELA[1] + 4), MANIVELA_R + 10)
        pygame.draw.circle(cab, (255, 255, 255), MANIVELA, MANIVELA_R + 8)
        pygame.draw.circle(cab, (190, 195, 215), MANIVELA, MANIVELA_R)
        pygame.draw.circle(cab, (230, 232, 245), MANIVELA, MANIVELA_R - 10)
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.circle(cab, (120, 125, 150), (int(MANIVELA[0] + math.cos(a) * (MANIVELA_R - 6)),
                                                      int(MANIVELA[1] + math.sin(a) * (MANIVELA_R - 6))), 3)
        # tubo y ranura
        pygame.draw.rect(cab, (70, 40, 90), TUBO.inflate(10, 10), border_radius=14)
        pygame.draw.rect(cab, (28, 20, 50), TUBO, border_radius=10)
        pygame.draw.rect(cab, (70, 40, 90), (CAP_X - 12, TUBO.bottom, 24, RANURA.top - TUBO.bottom + 4))
        pygame.draw.rect(cab, (70, 40, 90), RANURA.inflate(14, 14), border_radius=20)
        pygame.draw.rect(cab, (25, 12, 40), RANURA, border_radius=16)
        pygame.draw.rect(cab, (60, 40, 80), (RANURA.x + 8, RANURA.y + 6, RANURA.w - 16, 8), border_radius=4)
        # placa de monedas (a la derecha del tubo): ranura vertical y precio
        placa = pygame.Rect(0, 0, 48, 112)
        placa.center = (RANURA_MONEDA[0], RANURA_MONEDA[1] + 6)
        pygame.draw.rect(cab, (100, 60, 85), placa.move(0, 3), border_radius=12)
        pygame.draw.rect(cab, (70, 74, 100), placa, border_radius=12)
        self._degradado(cab, placa, 12, (255, 255, 255, 90), (0, 0, 20, 90))
        pygame.draw.rect(cab, (190, 196, 220), placa, 3, border_radius=12)
        ranura = pygame.Rect(0, 0, 8, 46)
        ranura.center = (placa.centerx, placa.y + 52)
        pygame.draw.rect(cab, (10, 5, 20), ranura, border_radius=4)
        pygame.draw.rect(cab, (255, 215, 90), ranura.inflate(6, 6), 2, border_radius=6)
        pygame.draw.circle(cab, (255, 205, 50), (placa.centerx, placa.y + 18), 11)
        pygame.draw.circle(cab, (255, 240, 150), (placa.centerx, placa.y + 18), 7, 2)
        escribir(cab, f.chica, f"{int(ajustes.GACHA_COSTO)}", placa.centerx, placa.bottom - 15, (255, 235, 150), contorno=None)
        # tornillos del panel
        for tx, ty in ((498, 462), (782, 462), (498, 656), (782, 656)):
            pygame.draw.circle(cab, (200, 130, 150), (tx, ty), 5)
            pygame.draw.circle(cab, (120, 50, 80), (tx, ty), 5, 1)
            pygame.draw.line(cab, (120, 50, 80), (tx - 3, ty - 1), (tx + 3, ty + 1), 1)
        escribir(cab, f.chica, "GIRA AQUÍ", MANIVELA[0], 632, (150, 40, 70), contorno=None)
        escribir(cab, f.chica, "PREMIO", RANURA.centerx, 650, (150, 40, 70), contorno=None)
        self._cab = cab
        # interior y cristal del globo
        d = GR * 2 + 40
        inte = pygame.Surface((d, d), pygame.SRCALPHA)
        for i in range(30, 0, -1):
            fr = i / 30
            c = (int(lerp(255, 160, fr)), int(lerp(255, 205, fr)), 255, 215)
            pygame.draw.circle(inte, c, (d // 2, d // 2), int((GR - 4) * fr))
        self._interior = inte
        cr = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(cr, (210, 238, 255, 38), (d // 2, d // 2), GR)
        pygame.draw.circle(cr, (255, 255, 255, 210), (d // 2, d // 2), GR, 7)
        pygame.draw.circle(cr, (120, 170, 255, 120), (d // 2, d // 2), GR - 7, 3)
        pygame.draw.arc(cr, (255, 255, 255, 200), pygame.Rect(d // 2 - GR + 22, d // 2 - GR + 22, GR * 2 - 44, GR * 2 - 44),
                        math.radians(112), math.radians(168), 12)
        pygame.draw.ellipse(cr, (255, 255, 255, 150), pygame.Rect(d // 2 - GR * 0.62, d // 2 - GR * 0.74, GR * 0.34, GR * 0.17))
        pygame.draw.circle(cr, (255, 255, 255, 120), (int(d // 2 + GR * 0.55), int(d // 2 + GR * 0.5)), 8)
        self._cristal = cr
        # tapa y cartel
        tapa = pygame.Surface((ANCHO, 130), pygame.SRCALPHA)
        pygame.draw.rect(tapa, (150, 30, 60), (GX - 98, 78, 196, 40), border_radius=16)
        pygame.draw.rect(tapa, (232, 62, 92), (GX - 98, 74, 196, 36), border_radius=16)
        pygame.draw.rect(tapa, (255, 255, 255), (GX - 98, 74, 196, 36), 4, border_radius=16)
        pygame.draw.rect(tapa, (255, 200, 60), (GX - 40, 66, 80, 14), border_radius=7)
        self._tapa = tapa

    @staticmethod
    def _degradado(dest, rect, radio, arriba, abajo):
        """Superpone un degradado vertical (con alfa) recortado a un rectangulo redondeado."""
        g = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.h):
            f = y / max(1, rect.h - 1)
            g.fill(tuple(int(arriba[i] + (abajo[i] - arriba[i]) * f) for i in range(4)), (0, y, rect.w, 1))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radio)
        g.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        dest.blit(g, rect.topleft)

    # ------------------------------------------------------------ simulacion de capsulas del globo
    def _sim_caps(self, dt, pasos=4):
        """Fisica del globo: gravedad, choques con la pared y entre capsulas, y la paleta engranada a la
        manivela. Nada se mueve solo: las capsulas solo se agitan si la paleta (la manivela) las empuja."""
        h = dt / pasos
        for _ in range(pasos):
            self._paso_caps(h)

    def _paso_caps(self, h):
        caps = self.caps
        pal_vel = self.pal_vel
        self.pal_ang += pal_vel * h
        brazos = []
        for k in range(3):
            a = self.pal_ang + k * 2 * math.pi / 3
            brazos.append((math.cos(a), math.sin(a)))
        for c in caps:
            c.vy += 1000 * h
            c.x += c.vx * h
            c.y += c.vy * h
            c.ang += c.vang * h
            c.vx *= 0.9995
            c.vy *= 0.9995
            c.vang *= 0.995
            v2 = c.vx * c.vx + c.vy * c.vy
            if v2 < 45 * 45:                        # casi quieta: se asienta (evita el temblor de reposo)
                c.vx *= 0.93
                c.vy *= 0.97
                c.vang *= 0.85
            if v2 > 2600 * 2600:
                f = 2600 / math.sqrt(v2)
                c.vx *= f
                c.vy *= f
            # paleta: tres brazos desde el centro del globo
            rx, ry = c.x - GX, c.y - GY
            for ux, uy in brazos:
                t = max(0.0, min(PALETA_L, rx * ux + ry * uy))
                qx, qy = ux * t, uy * t
                vx, vy = rx - qx, ry - qy
                dn = math.hypot(vx, vy)
                lim = c.r + PALETA_ANCHO
                if dn < lim:
                    if dn < 1e-3:
                        nx, ny = -uy, ux
                    else:
                        nx, ny = vx / dn, vy / dn
                    c.x += nx * (lim - dn)
                    c.y += ny * (lim - dn)
                    rx, ry = c.x - GX, c.y - GY
                    avx, avy = -pal_vel * qy, pal_vel * qx          # velocidad del punto del brazo
                    rel = (c.vx - avx) * nx + (c.vy - avy) * ny
                    if rel < 0:
                        c.vx -= (1.25) * rel * nx
                        c.vy -= (1.25) * rel * ny
                        # el brazo arrastra un poco de lado (rozamiento): da efecto de rodar
                        tx, ty = -ny, nx
                        rt = (c.vx - avx) * tx + (c.vy - avy) * ty
                        c.vx -= 0.12 * rt * tx
                        c.vy -= 0.12 * rt * ty
                        c.vang += -rt / c.r * 0.12
            # pared del globo
            dx, dy = c.x - GX, c.y - GY
            d = math.hypot(dx, dy) or 1.0
            lim = GR - 12 - c.r
            if d > lim:
                nx, ny = dx / d, dy / d
                c.x, c.y = GX + nx * lim, GY + ny * lim
                vn = c.vx * nx + c.vy * ny
                if vn > 0:
                    c.vx -= 1.3 * vn * nx
                    c.vy -= 1.3 * vn * ny
                tx, ty = -ny, nx
                vt = c.vx * tx + c.vy * ty
                c.vang += (vt / c.r - c.vang) * 0.15            # rueda por la pared
                c.vx -= 0.02 * vt * tx
                c.vy -= 0.02 * vt * ty
        for i in range(len(caps)):
            a = caps[i]
            for j in range(i + 1, len(caps)):
                b = caps[j]
                dx, dy = b.x - a.x, b.y - a.y
                m = a.r + b.r - 2
                if abs(dx) > m or abs(dy) > m:
                    continue
                d2 = dx * dx + dy * dy
                if d2 < m * m and d2 > 0.01:
                    d = math.sqrt(d2)
                    push = (m - d) * 0.5
                    nx, ny = dx / d, dy / d
                    a.x -= nx * push
                    a.y -= ny * push
                    b.x += nx * push
                    b.y += ny * push
                    rel = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                    if rel < 0:
                        j_ = 0.65 * rel                      # choque casi inelastico (e = 0.3)
                        a.vx += nx * j_
                        a.vy += ny * j_
                        b.vx -= nx * j_
                        b.vy -= ny * j_
                        tx, ty = -ny, nx
                        rt = (b.vx - a.vx) * tx + (b.vy - a.vy) * ty
                        a.vang += rt / a.r * 0.05
                        b.vang += rt / b.r * 0.05

    # ------------------------------------------------------------ actualizar
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self.tf += dt
        self.rayos_ang += dt * 0.25
        self.aviso_t = max(0.0, self.aviso_t - dt)
        self.error_t = max(0.0, self.error_t - dt)
        self.fade = max(0.0, self.fade - dt * 2.6)
        self.luz += dt * (3.0 + 0.9 * abs(self.vel_man))
        dif = self.perfil.monedas - self.monedas_vis
        self.monedas_vis = float(self.perfil.monedas) if abs(dif) < 0.6 else self.monedas_vis + dif * min(1.0, 7.0 * dt)
        for v in self.vuelos:
            v["t"] += dt
            if v["t"] >= 0.62 and not v.get("sono"):
                v["sono"] = True
                self.sn.reproducir("tick")
        self.vuelos = [v for v in self.vuelos if v["t"] < 0.62]
        self.flash = max(0.0, self.flash - dt * 1.6)
        self.shake = max(0.0, self.shake - dt * 14.0)
        self.brillos = [b for b in self.brillos if b.actualizar(dt)]
        if self.fase not in ("inicio", "agitar"):               # el mango sigue girando por inercia
            self.vel_man *= math.exp(-MAN_ROZ * 0.8 * dt)
            self.ang_man += self.vel_man * dt
        self._actualizar_agenda(dt)
        f = self.fase
        if f == "inicio":
            self._upd_inicio(dt, ctrl)
        elif f in FASES_ANIM:
            self._upd_anim(dt, ctrl)
        elif f == "figura":
            self._upd_figura(dt, ctrl)
        elif f == "resumen":
            self._upd_resumen(dt, ctrl)
        elif f == "coleccion":
            self._upd_coleccion(dt, ctrl)
        self.pal_vel = ENGRANAJE * self.vel_man                  # la paleta va engranada al mango
        self._sim_caps(dt)

    def _actualizar_agenda(self, dt):
        for a in list(self.agenda):
            a[0] -= dt
            if a[0] <= 0:
                self.agenda.remove(a)
                if a[1] == "nota":
                    self.sn.nota(a[2], 0.28)
                else:
                    self.sn.reproducir(a[2])
                    if a[2] == "golpe":
                        self.shake = max(self.shake, getattr(self, "_shake_pendiente", 0.0))

    # --- inicio
    def _upd_inicio(self, dt, ctrl):
        self.b_tirar.activo = self.perfil.monedas >= self.costo(1)
        self.b_x10.activo = self.perfil.monedas >= self.costo(10)
        pulsado = False
        if self.b_tirar.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            pulsado = True
            self.pedir_tirada(1)
        elif self.b_x10.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            pulsado = True
            self.pedir_tirada(10)
        elif self.b_coleccion.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self.abrir_coleccion()
            return
        elif self.b_volver.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self.app.ir_menu()
            return
        sobre_boton = any(b.encima for b in (self.b_tirar, self.b_x10, self.b_coleccion, self.b_volver))
        if (not pulsado and self.fase == "inicio" and ctrl.golpe and not sobre_boton
                and AREA_MAQUINA.collidepoint(ctrl.pos.x, ctrl.pos.y)):
            self.pedir_tirada(1)
        if self.fase == "inicio":
            self._upd_manivela(dt, ctrl)

    def _sonar_vueltas(self, antes, despues):
        """Tic a cada cuarto de vuelta y nota que sube a cada vuelta completa."""
        if int(despues * 2 / math.pi) != int(antes * 2 / math.pi):
            self.sn.reproducir("tick")
        va, vd = int(antes / (2 * math.pi)), int(despues / (2 * math.pi))
        if vd != va and vd < VUELTAS:
            self.sn.nota(300 + 38 * vd, 0.16)

    def _upd_manivela(self, dt, ctrl):
        """El mango persigue al cursor como un muelle amortiguado: tiene masa, la fuerza esta limitada y,
        al soltarlo, sigue girando y se frena solo. Solo cuentan las vueltas que de verdad da el mango."""
        c = V2(MANIVELA)
        d = ctrl.pos - c
        r = d.length()
        puede = self.perfil.monedas >= self.costo(1)
        agarra = 26 <= r <= 175
        if agarra:
            a = math.atan2(d.y, d.x)
            err = (a - self.ang_man + math.pi) % (2 * math.pi) - math.pi
            err = max(-1.2, min(1.2, err))
            if puede:
                self.vel_man += (MAN_K * err - MAN_C * self.vel_man) * dt
            else:                                               # sin monedas el mango esta trabado
                self.vel_man = 0.0
                if abs(err) > 0.5 and self.error_t <= 0:
                    self.error_t = 1.2
                    self.aviso_t = 2.5
                    self.sn.reproducir("error")
        else:
            self.vel_man *= math.exp(-MAN_ROZ * dt)
        self.vel_man = max(-MAN_VMAX, min(MAN_VMAX, self.vel_man))
        da = self.vel_man * dt
        self.ang_man += da
        if puede:
            antes = self.giro
            self.giro += abs(da)
            self._sonar_vueltas(antes, self.giro)
            # un poco de rozamiento extra: si el jugador deja la manivela mucho rato, el contador vuelve atras
            if not agarra and abs(self.vel_man) < 0.4:
                self.giro = max(0.0, self.giro - 0.08 * dt * 2 * math.pi)
        else:
            self.giro = 0.0
        if self.giro >= 2 * math.pi * VUELTAS and puede:
            self.giro = 2 * math.pi * VUELTAS
            self.pedir_tirada(1, manual=True)

    # --- animacion
    def _upd_anim(self, dt, ctrl):
        self.t_anim += dt
        f = self.fase
        u = self.tf / DUR[f]
        if f == "agitar":
            # giro automatico: arranca, mantiene y frena (trapecio), con las VUELTAS vueltas completas
            ac, cr = 0.22, 0.78                                  # fin de la aceleracion / inicio del frenado
            vmax = 1.0 / (1.0 - 0.5 * ac - 0.5 * (1 - cr))
            if u < ac:
                e = vmax * u * u / (2 * ac)
            elif u < cr:
                e = vmax * (ac / 2 + (u - ac))
            else:
                w = 1 - u
                e = 1 - vmax * w * w / (2 * (1 - cr))
            e = max(0.0, min(1.0, e))
            nuevo = self.auto0 + 2 * math.pi * VUELTAS * e
            self.vel_man = (nuevo - self.ang_man) / max(dt, 1e-3)
            self.ang_man = nuevo
            antes = self.giro
            self.giro = 2 * math.pi * VUELTAS * e
            self._sonar_vueltas(antes, self.giro)
        elif f == "caer":
            if u > 0.82 and not getattr(self, "_aterrizo", False):
                self._aterrizo = True
                self.sn.reproducir("caja")
        elif f == "lluvia":
            for ent in self.lluvia:
                if not ent["lanzada"] and self.tf >= ent["i"] * 0.15:
                    ent["lanzada"] = True
                    ent["t0"] = self.tf
                    self.sn.nota(330 + ent["i"] * 45, 0.12)
        elif f == "suspenso":
            self.tick_t -= dt
            intervalo = lerp(0.34, 0.1, u)
            if self.tick_t <= 0:
                self.tick_t = intervalo
                self.sn.nota(260 + 420 * u, 0.08)
            if u >= 0.6 and not self.cap_cambiada:
                self.cap_cambiada = True
                self.cap_rango_ap = self.res["rango"]
                self.cap_color_ap = col_cap(self.res["rango"], self.t)
                self.flash = 0.45
                self.sn.reproducir("pop")
        elif f in ("destello", "rango"):
            self._upd_electrico(dt)
        if f == "rango":
            if self.res["rango"] == "SSS" and self.tf > 0.3:
                self.shake = max(self.shake, 4.0 + 6.0 * math.sin(self.tf * 18) ** 2)
        if f in ("rango",) and self.res["rango"] in ("SS", "SSS") and random.random() < 0.5:
            a = random.uniform(0, 6.28)
            self.brillos.append(Brillo(640 + math.cos(a) * 120, 260 + math.sin(a) * 90, math.cos(a) * 200,
                                       math.sin(a) * 200 - 60, 0.9, color_arcoiris(random.random()) if
                                       self.res["rango"] == "SSS" else color_rango("SS"), "estrella", 9, 120))
        # saltar o avanzar
        if self.t_anim >= SALTAR_DESDE:
            self.b_saltar.activo = True
            if self.b_saltar.actualizar(dt, ctrl) or ctrl.golpe or ctrl.clic:
                self.saltar()
                return
        if self.tf >= DUR[f]:
            self._aterrizo = False
            self._siguiente_fase()

    def _upd_electrico(self, dt):
        if self.res["rango"] != "SSS":
            return
        self.rayos_elec_t -= dt
        if self.rayos_elec_t <= 0:
            self.rayos_elec_t = 0.07
            self.rayos_elec = []
            for _ in range(5):
                a = random.uniform(0, 2 * math.pi)
                pts = [(640, 340)]
                x, y = 640.0, 340.0
                for k in range(9):
                    a2 = a + random.uniform(-0.45, 0.45)
                    x += math.cos(a2) * random.uniform(55, 90)
                    y += math.sin(a2) * random.uniform(55, 90)
                    pts.append((x, y))
                self.rayos_elec.append(pts)

    def _upd_figura(self, dt, ctrl):
        r = self.res["rango"]
        tasa = {"C": 5, "B": 8, "A": 12, "S": 20, "SS": 30, "SSS": 50}[r]
        if random.random() < tasa * dt:
            self._confeti(True)
        if self.modo == 10:
            otra = self.b_resumen
        else:
            otra = self.b_seguir
        self.b_otra.texto = f"Otra vez ({self.costo(1)})" if self.modo == 1 else f"Otra vez x10 ({self.costo(10)})"
        self.b_otra.activo = self.perfil.monedas >= self.costo(self.modo)
        if otra.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            if self.modo == 10:
                self._ir_resumen()
            else:
                self._volver_inicio()
        elif self.modo == 1 and self.b_otra.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self._volver_inicio()
            self.pedir_tirada(1)

    def _ir_resumen(self):
        self.fase = "resumen"
        self.fade = 0.6
        self.tf = 0.0
        self.b_seguir.espera = self.b_otra.espera = 0.8
        self.b_seguir.dwell = self.b_otra.dwell = 0.0

    def _upd_resumen(self, dt, ctrl):
        self.b_otra.texto = f"Otra vez x10 ({self.costo(10)})"
        self.b_otra.activo = self.perfil.monedas >= self.costo(10)
        if self.b_seguir.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self._volver_inicio()
        elif self.b_otra.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self._volver_inicio()
            self.pedir_tirada(10)

    def _volver_inicio(self):
        self.fase = "inicio"
        self.fade = 0.55
        self.tf = 0.0
        self.brillos = []
        self.giro = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self._rearmar()

    # --- coleccion
    def abrir_coleccion(self):
        self.fase = "coleccion"
        self.fade = 0.55
        self.tf = 0.0
        self.detalle = None
        self.pagina = 0
        self._rearmar()

    def lista_coleccion(self):
        """Figuras de la pestana elegida: todas, una pagina de mundo (por id) o un rango (por letra)."""
        f = self.filtro
        if f is None:
            return list(figuras.ORDEN_FIGURAS)
        if f in figuras.POR_RANGO:
            return list(figuras.POR_RANGO[f])
        for k, pg in enumerate(figuras.PAGINAS):
            if pg["id"] == f:
                return list(figuras.POR_PAGINA[k])
        return list(figuras.ORDEN_FIGURAS)

    def paginas(self):
        return max(1, math.ceil(len(self.lista_coleccion()) / self.por_pagina))

    def _rect_tarjeta(self, i):
        col, fila = i % 6, i // 6
        return pygame.Rect(50 + col * 198, 162 + fila * 240, 190, 232)

    def poner_filtro(self, rango):
        self.filtro = rango
        self.pagina = 0

    def _upd_coleccion(self, dt, ctrl):
        if self.detalle is not None:
            if self.b_cerrar.actualizar(dt, ctrl):
                self.sn.reproducir("click")
                self.detalle = None
                self._rearmar()
            return
        for i, b in enumerate(self.b_filtros):
            if b.actualizar(dt, ctrl):
                self.sn.reproducir("click")
                self.poner_filtro(None if i == 0 else figuras.PAGINAS[i - 1]["id"])
        self.b_ant.activo = self.pagina > 0
        self.b_sig.activo = self.pagina < self.paginas() - 1
        if self.b_ant.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self.pagina -= 1
        elif self.b_sig.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self.pagina += 1
        elif self.b_maquina.actualizar(dt, ctrl):
            self.sn.reproducir("click")
            self._volver_inicio()
            return
        lista = self.lista_coleccion()
        ini = self.pagina * self.por_pagina
        for i, b in enumerate(self.b_tarjetas):
            b.activo = ini + i < len(lista)
            if b.actualizar(dt, ctrl):
                self.sn.reproducir("pop")
                self.abrir_detalle(lista[ini + i])

    def abrir_detalle(self, ident):
        self.detalle = ident
        self.tf = 0.0
        self.b_cerrar.espera = 0.5
        self.b_cerrar.dwell = 0.0
        for b in self.b_tarjetas:
            b.dwell = 0.0

    def tecla_esc(self):
        f = self.fase
        if f == "inicio":
            self.app.ir_menu()
        elif f == "coleccion":
            if self.detalle is not None:
                self.detalle = None
            else:
                self._volver_inicio()
        elif f in FASES_ANIM:
            if not self.saltar():
                pass
        else:
            self._volver_inicio()

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        f = self.fase
        if f == "inicio":
            self._dib_maquina(p)
            self._dib_ui_inicio(p)
        elif f == "coleccion":
            self._dib_coleccion(p)
        elif f in FASES_ANIM:
            self._dib_anim(p)
        elif f == "figura":
            self._dib_figura(p)
        elif f == "resumen":
            self._dib_resumen(p)
        if self.flash > 0.01:
            vel = pygame.Surface((ANCHO, ALTO))
            vel.fill((255, 255, 255))
            vel.set_alpha(int(255 * min(1.0, self.flash)))
            p.blit(vel, (0, 0))
        if self.fade > 0.01:
            velo = pygame.Surface((ANCHO, ALTO))
            velo.fill((12, 6, 28))
            velo.set_alpha(int(255 * min(1.0, self.fade)))
            p.blit(velo, (0, 0))
        if self.shake > 0.3:
            copia = p.copy()
            dx = random.uniform(-self.shake, self.shake)
            dy = random.uniform(-self.shake, self.shake)
            p.fill((10, 5, 25))
            p.blit(copia, (dx, dy))

    # --- fondos
    def _fondo_fiesta(self, p, oscuro=0.0):
        arriba, abajo = (70, 40, 160), (255, 135, 165)
        if oscuro:
            arriba = tuple(int(c * (1 - oscuro)) for c in arriba)
            abajo = tuple(int(c * (1 - oscuro)) for c in abajo)
        from nucleo import fondo
        fondo(p, arriba, abajo)
        capa_efectos(p, lambda s, k: rayos(s, k, GX, 330, 18, self.rayos_ang * 0.6,
                                           lambda i: (255, 230, 150) if i % 2 else (255, 170, 210), 26,
                                           1300, 0.5), 0.34)
        for (x, y, v, ph) in self._estrellas:
            yy = (y + self.t * 14 * v) % ALTO
            r = 3 + 3 * v * (0.6 + 0.4 * math.sin(self.t * 3 + ph))
            figuras.arte_estrella(p, x, yy, r, (255, 250, 200), (255, 220, 120))

    # --- maquina
    def _dib_maquina(self, p):
        self._fondo_fiesta(p)
        p.blit(self._cab, (0, 0))
        # interior, capsulas y cristal
        p.blit(self._interior, (GX - GR - 20, GY - GR - 20))
        for c in self.caps:
            dibujar_capsula(p, c.x, c.y, c.r, c.color, c.ang)
        self._dib_paleta(p)
        p.blit(self._cristal, (GX - GR - 20, GY - GR - 20))
        # tapa y cartel
        p.blit(self._tapa, (0, GY - GR - 112 + 4 - 4))
        self._dib_cartel_maquina(p)
        # luces alrededor del globo
        n = 18
        for i in range(n):
            a = i * 2 * math.pi / n - math.pi / 2
            x, y = GX + math.cos(a) * (GR + 18), GY + math.sin(a) * (GR + 18)
            if y > GY + GR * 0.6:
                continue
            on = (i + int(self.luz)) % 3 == 0
            col = (255, 240, 120) if on else (255, 150, 90)
            pygame.draw.circle(p, (90, 40, 60), (int(x), int(y)), 9)
            pygame.draw.circle(p, col, (int(x), int(y)), 7)
            if on:
                g = figuras.resplandor((255, 230, 120), 20, 0.8)
                p.blit(g, g.get_rect(center=(int(x), int(y))))
        # agujero de salida del globo
        pygame.draw.ellipse(p, (40, 20, 60), pygame.Rect(CAP_X - 22, GY + 140, 44, 24))
        self._dib_manivela(p)
        if self.fase == "caer":
            self._dib_capsula_cayendo(p)
        self._dib_vuelos(p)

    def _dib_vuelos(self, p):
        """Monedas que vuelan del contador a la ranura (giran como monedas de verdad)."""
        for v in self.vuelos:
            if v["t"] < 0:
                continue
            u = min(1.0, v["t"] / 0.62)
            e = ease_in(u) * 0.6 + u * 0.4
            pos = v["p0"].lerp(v["p1"], e)
            pos.y -= math.sin(u * math.pi) * 110
            ancho = max(3, int(19 * abs(math.cos(u * 9))))
            r = int(19 - 6 * u)
            g = figuras.resplandor((255, 215, 80), 30, 0.7)
            p.blit(g, g.get_rect(center=(int(pos.x), int(pos.y))))
            pygame.draw.ellipse(p, (150, 100, 20), pygame.Rect(pos.x - ancho, pos.y - r + 2, ancho * 2, r * 2))
            pygame.draw.ellipse(p, (255, 205, 50), pygame.Rect(pos.x - ancho, pos.y - r, ancho * 2, r * 2))
            if ancho > 8:
                pygame.draw.ellipse(p, (255, 240, 150), pygame.Rect(pos.x - ancho * 0.6, pos.y - r * 0.6, ancho * 1.2, r * 1.2), 2)

    def _dib_cartel_maquina(self, p):
        r = pygame.Rect(0, 0, 300, 62)
        r.center = (GX, 40)
        pygame.draw.rect(p, (90, 20, 70), r.move(0, 6), border_radius=20)
        pygame.draw.rect(p, (255, 205, 60), r, border_radius=20)
        pygame.draw.rect(p, (255, 245, 180), r.inflate(-14, -34).move(0, -12), border_radius=8)
        pygame.draw.rect(p, (255, 255, 255), r, 4, border_radius=20)
        escribir(p, self.f.grande, "GACHAPÓN", r.centerx, r.centery, (255, 255, 255), contorno=(150, 40, 90), grosor=3)
        for lado in (-1, 1):
            figuras.arte_estrella(p, r.centerx + lado * 168, r.centery + 2, 14 + 3 * math.sin(self.t * 5 + lado),
                                  (255, 240, 120), (170, 110, 20))

    def _dib_paleta(self, p):
        """Paleta de tres brazos del globo: gira engranada con la manivela y es lo que mueve las capsulas."""
        d = PALETA_L * 2 + 30
        capa = getattr(self, "_capa_paleta", None)
        if capa is None:
            capa = self._capa_paleta = pygame.Surface((d, d), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 0))
        c0 = d // 2
        for k in range(3):
            a = self.pal_ang + k * 2 * math.pi / 3
            ux, uy = math.cos(a), math.sin(a)
            x1, y1 = c0 + ux * PALETA_L, c0 + uy * PALETA_L
            pygame.draw.line(capa, (60, 50, 100, 120), (c0 + 2, c0 + 3), (x1 + 2, y1 + 3), PALETA_ANCHO * 2 + 2)
            pygame.draw.line(capa, (150, 156, 190, 205), (c0, c0), (x1, y1), PALETA_ANCHO * 2)
            pygame.draw.line(capa, (235, 240, 255, 230), (c0 - uy * 2, c0 + ux * 2), (x1 - uy * 2, y1 + ux * 2), 3)
            pygame.draw.circle(capa, (150, 156, 190, 230), (int(x1), int(y1)), PALETA_ANCHO + 1)
        p.blit(capa, (GX - c0, GY - c0))
        pygame.draw.circle(p, (60, 50, 90), (GX, GY + 2), 17)
        pygame.draw.circle(p, (255, 205, 60), (GX, GY), 14)
        pygame.draw.circle(p, (255, 245, 170), (GX - 4, GY - 4), 5)

    def _dib_manivela(self, p):
        cx, cy = MANIVELA
        puede = self.perfil.monedas >= self.costo(1)
        vuelta = (self.giro % (2 * math.pi)) if self.giro < 2 * math.pi * VUELTAS else 2 * math.pi
        # progreso de la vuelta actual (en sentido horario desde arriba)
        if vuelta > 0.04 and puede:
            R = MANIVELA_R + 16
            pts = [(cx + math.cos(-math.pi / 2 + vuelta * k / 40) * R, cy + math.sin(-math.pi / 2 + vuelta * k / 40) * R)
                   for k in range(41)]
            pygame.draw.lines(p, (255, 215, 60), False, pts, 9)
        ang = self.ang_man
        largo = 40
        vel = self.vel_man
        # estela de movimiento cuando gira rapido
        if abs(vel) > 5:
            for k in (3, 2, 1):
                aa = ang - vel * 0.012 * k
                gx, gy = cx + math.cos(aa) * largo, cy + math.sin(aa) * largo
                s = pygame.Surface((44, 44), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 215, 60, 38 + 22 * (4 - k)), (22, 22), 15)
                p.blit(s, (gx - 22, gy - 22))
        kx, ky = cx + math.cos(ang) * largo, cy + math.sin(ang) * largo
        col_brazo = (230, 90, 120) if puede else (170, 170, 185)
        pygame.draw.line(p, (60, 30, 60), (cx, cy + 3), (kx, ky + 3), 16)
        pygame.draw.line(p, col_brazo, (cx, cy), (kx, ky), 13)
        pygame.draw.circle(p, (60, 30, 60), (int(kx), int(ky + 2)), 17)
        pygame.draw.circle(p, (255, 215, 60) if puede else (190, 190, 200), (int(kx), int(ky)), 15)
        pygame.draw.circle(p, (255, 255, 255), (int(kx - 4), int(ky - 5)), 4)
        pygame.draw.circle(p, (60, 30, 60), (cx, cy), 13)
        pygame.draw.circle(p, (220, 225, 240), (cx, cy), 9)
        # pista para el nino: bolita que da vueltas
        if self.fase == "inicio" and puede and self.giro < 0.5:
            a = self.t * 3.0
            for k in range(6, 0, -1):
                aa = a - k * 0.2
                pygame.draw.circle(p, (255, 240, 160), (int(cx + math.cos(aa) * 84), int(cy + math.sin(aa) * 84)),
                                   max(2, 8 - k))
            px, py = cx + math.cos(a) * 84, cy + math.sin(a) * 84
            flecha = [(0, 0), (0, 26), (7, 20), (12, 31), (17, 29), (12, 18), (21, 18)]
            pts = [(px + fx, py + fy) for fx, fy in flecha]
            pygame.draw.polygon(p, (255, 255, 255), pts)
            pygame.draw.polygon(p, (60, 30, 80), pts, 2)

    def _dib_capsula_cayendo(self, p):
        x, y = self.cap_pos.x, self.cap_pos.y
        for clip in (pygame.Rect(600, 80, 220, 345), TUBO, RANURA.inflate(60, 60)):
            p.set_clip(clip)
            dibujar_capsula(p, x, y, self.cap_r, self.cap_color_ap, self.cap_ang)
            p.set_clip(None)
        # brillo del cristal del tubo
        g = pygame.Surface(TUBO.size, pygame.SRCALPHA)
        pygame.draw.rect(g, (255, 255, 255, 60), (6, 4, 12, TUBO.h - 8), border_radius=6)
        p.blit(g, TUBO.topleft)

    # --- HUD e interfaz de inicio
    def _hud_monedas(self, p):
        panel(p, (930, 20, 320, 64), (255, 255, 255), 235, 20, (150, 60, 100))
        pygame.draw.circle(p, (150, 100, 20), (964, 54), 20)
        pygame.draw.circle(p, (255, 205, 50), (964, 52), 19)
        pygame.draw.circle(p, (255, 240, 150), (964, 52), 12, 3)
        escribir(p, self.f.grande, f"{int(round(self.monedas_vis))}", 1000, 52, (120, 60, 20), ancla="izq", contorno=None)
        escribir(p, self.f.chica, "monedas", 1235, 56, (130, 80, 100), ancla="der", contorno=None)

    def _dib_album(self, p):
        """Suerte del album: una barra por pagina de mundo; cuanto mas llenas, mejores las probabilidades."""
        f = self.f
        perfil = self.perfil
        panel(p, (30, 196, 300, 236), (255, 255, 255), 232, 20, (150, 60, 100))
        escribir(p, f.normal, "Suerte del álbum", 180, 218, (120, 50, 130), contorno=None)
        base = sum(figuras.PROBABILIDADES[r] for r in ("S", "SS", "SSS"))
        efe = self.probabilidades()
        alto = sum(efe[r] for r in ("S", "SS", "SSS"))
        escribir(p, f.chica, f"Rangos altos: {base:.0f}%  >  {alto:.0f}%", 180, 244, (30, 140, 70) if alto > base + 0.05 else (110, 80, 120),
                 contorno=None)
        for k, pg in enumerate(figuras.PAGINAS):
            y = 272 + k * 34
            tengo, tot = figuras.progreso_pagina(perfil, k)
            completa = tengo >= tot
            escribir(p, f.chica, pg["nombre"], 46, y, (80, 50, 90), ancla="izq", contorno=None)
            barra(p, (150, y - 9, 120, 18), tengo / tot, color=pg["color"], color_fondo=(205, 195, 220), borde=(120, 80, 130))
            if completa:
                figuras.arte_estrella(p, 296, y, 12, (255, 225, 80), (170, 120, 20))
            else:
                escribir(p, f.chica, f"{tengo}/{tot}", 316, y, (80, 50, 90), ancla="der", contorno=None)
        meta = figuras.siguiente_meta(perfil)
        if meta is None:
            texto = "¡Álbum completo! Suerte al máximo."
        else:
            k, falta = meta
            texto = f"{'Falta' if falta == 1 else 'Faltan'} {falta} para llenar {figuras.PAGINAS[k]['nombre']}."
        for i, ln in enumerate(envolver(texto, f.chica, 270)):
            escribir(p, f.chica, ln, 180, 408 - (len(envolver(texto, f.chica, 270)) - 1) * 9 + i * 18, (120, 50, 130), contorno=None)

    def _dib_vueltas(self, p):
        """Contador de vueltas de la manivela (10 puntitos) y la pista de que hacer."""
        f = self.f
        puede = self.perfil.monedas >= self.costo(1)
        panel(p, (30, 444, 300, 182), (255, 255, 255), 232, 20, (150, 60, 100))
        completas = min(VUELTAS, int(self.giro / (2 * math.pi)))
        escribir(p, f.normal, "Vueltas", 110, 468, (120, 50, 130), contorno=None)
        escribir(p, f.grande, f"{completas} / {VUELTAS}", 250, 470, (150, 40, 90) if puede else (150, 150, 165), contorno=None)
        parcial = (self.giro % (2 * math.pi)) / (2 * math.pi) if completas < VUELTAS else 0.0
        for k in range(VUELTAS):
            x, y = 62 + k * 26.2, 514
            pygame.draw.circle(p, (205, 195, 220), (int(x), y), 10)
            if k < completas:
                pygame.draw.circle(p, (255, 200, 40), (int(x), y), 10)
                pygame.draw.circle(p, (255, 240, 150), (int(x - 2), y - 3), 3)
            elif k == completas and parcial > 0.02:
                pygame.draw.circle(p, (255, 215, 90), (int(x), y), max(2, int(10 * parcial)))
            pygame.draw.circle(p, (120, 80, 130), (int(x), y), 10, 2)
        if not puede:
            lineas = ["¡Juega para ganar", "más monedas!"]
        elif completas >= VUELTAS - 1 and self.giro > 0:
            lineas = ["¡Última vuelta!"]
        elif self.giro > 0.5:
            lineas = ["¡Sigue girando!"]
        else:
            lineas = ["Gira la manivela", "con el cursor", "o pulsa Tirar x1"]
        n = len(lineas)
        for i, ln in enumerate(lineas):
            escribir(p, f.normal if i < 2 else f.chica, ln, 180, 556 + i * 28 - (n - 1) * 6, (120, 50, 130), contorno=None)

    def _dib_ui_inicio(self, p):
        f = self.f
        perfil = self.perfil
        # contador de figuras
        panel(p, (30, 20, 300, 64), (255, 255, 255), 235, 20, (150, 60, 100))
        u = figuras.contar_unicas(perfil)
        escribir(p, f.normal, f"Figuras {u}/{figuras.TOTAL}", 180, 52, (120, 50, 130), contorno=None)
        self._hud_monedas(p)
        self.b_coleccion.dibujar(p, f.normal)
        # botones de tirada
        self.b_tirar.texto = f"Tirar x1  ({self.costo(1)})"
        self.b_x10.texto = f"Tirar x10  ({self.costo(10)})"
        self.b_tirar.dibujar(p, f.normal)
        self.b_x10.dibujar(p, f.normal)
        # aviso
        falta1, falta10 = self.faltan(1), self.faltan(10)
        msg = ""
        if falta1:
            msg = f"Te falta{'n' if falta1 != 1 else ''} {monedas_txt(falta1)}; juega para ganar más."
        elif falta10 and self.b_x10.encima:
            msg = f"Para x10 te faltan {monedas_txt(falta10)}."
        if msg:
            lineas = envolver(msg, f.normal, 300)
            col = (255, 235, 120) if self.aviso_t <= 0 else (255, 255, 255)
            panel(p, (930, 292, 320, 24 + 30 * len(lineas)), (80, 30, 90), 215, 16, (255, 255, 255))
            for i, ln in enumerate(lineas):
                escribir(p, f.normal, ln, 1090, 312 + i * 30, col)
        else:
            ajustado(p, f.chica, f"Cada tirada cuesta {self.costo(1)} monedas.", 1090, 300, 316, (255, 255, 255))
            if self.garantia_x10:
                ajustado(p, f.chica, "El x10 asegura una Rara (A) o mejor.", 1090, 324, 316, (255, 235, 130))
        # tabla de probabilidades (con la suerte del album)
        panel(p, (930, 400, 320, 250), (255, 255, 255), 225, 20, (150, 60, 100))
        escribir(p, f.normal, "¿Qué puede salir?", 1090, 424, (120, 50, 130), contorno=None)
        efect = self.probabilidades()
        for i, r in enumerate(RANGOS):
            y = 458 + i * 31
            figuras.dibujar_insignia(p, 984, y, r, 26, self.t)
            txt = figuras.NOMBRE_RANGO[r]
            escribir(p, f.chica, txt, 1030, y, (80, 50, 90), ancla="izq", contorno=None)
            pr = efect[r]
            sube = pr > figuras.PROBABILIDADES[r] + 0.05
            col = (30, 140, 70) if sube else (80, 50, 90)
            escribir(p, f.chica, f"{pr:.1f}%".replace(".0%", "%"), 1224, y, col, ancla="der", contorno=None)
            if sube:
                pygame.draw.polygon(p, (40, 170, 90), [(1236, y + 5), (1244, y + 5), (1240, y - 5)])
        self._dib_album(p)
        self._dib_vueltas(p)
        if perfil.monedas >= self.costo(1) and self.fase == "inicio":
            pygame.draw.polygon(p, (255, 235, 120), [(350, 538 + 4 * math.sin(self.t * 5)), (420, 548), (350, 580 - 4 * math.sin(self.t * 5))])
        self.b_volver.dibujar(p, f.normal)
        if self.fase == "inicio":
            # barra de ultimo premio
            pass

    # --- animacion
    def _dib_anim(self, p):
        f = self.fase
        u = min(1.0, self.tf / DUR[f])
        res = self.res
        r = res["rango"]
        if f in ("agitar", "caer", "lluvia", "rueda"):
            self._dib_maquina_anim(p, f, u)
        else:
            self._dib_fondo_oscuro(p, col_cap(self.cap_rango_ap, self.t) if f == "suspenso" else color_rango(r, self.t))
            if f == "suspenso":
                self._dib_suspenso(p, u)
            elif f == "destello":
                self._dib_destello(p, u)
            elif f == "silueta":
                self._dib_silueta(p, u)
            elif f == "rango":
                self._dib_rango(p, u)
        if self.t_anim >= SALTAR_DESDE:
            self.b_saltar.dibujar(p, self.f.normal)
        self._hud_monedas(p)

    def _dib_maquina_anim(self, p, f, u):
        self._dib_maquina(p)
        if f == "lluvia" or f == "rueda":
            vel = pygame.Surface((ANCHO, ALTO))
            vel.fill((15, 5, 35))
            a = 130 if f == "lluvia" else int(lerp(130, 215, ease_out(u))) if self.modo == 10 else int(215 * ease_out(u))
            vel.set_alpha(a)
            p.blit(vel, (0, 0))
        if f == "caer":
            y = lerp(388, 604, ease_in(min(1.0, u / 0.86)))
            if u > 0.86:
                rebote = abs(math.sin((u - 0.86) / 0.14 * math.pi)) * 8
                y = 604 - rebote
            self.cap_pos = V2(CAP_X, y)
            self.cap_ang = u * 9
        elif f == "agitar":
            self._dib_vueltas(p)                 # la maquina cuenta sus 10 vueltas
        elif f == "lluvia":
            self._dib_lluvia(p, u)
        elif f == "rueda":
            e = ease_out(u)
            destino = V2(640, 340)
            self.cap_pos = self.cap_ini.lerp(destino, e)
            self.cap_r = lerp(26 if self.modo == 1 else 34, 105, ease_out_back(u, 0.9))
            self.cap_ang = (1 - e) * -6
            g = figuras.resplandor(self.cap_color_ap, 220, 0.8)
            p.blit(g, g.get_rect(center=(int(self.cap_pos.x), int(self.cap_pos.y))))
            dibujar_capsula(p, self.cap_pos.x, self.cap_pos.y, self.cap_r, self.cap_color_ap, self.cap_ang)

    def _dib_lluvia(self, p, u):
        for ent in self.lluvia:
            if not ent["lanzada"]:
                continue
            lu = min(1.0, (self.tf - ent["t0"]) / 0.55)
            dest = V2(self._destino_lluvia(ent["i"]))
            ini = V2(CAP_X, 604)
            pos = ini.lerp(dest, ease_out(lu))
            pos.y -= math.sin(lu * math.pi) * 170
            col = col_cap(ent["r"]["aparente"], self.t)
            es_mejor = ent["r"] is self.res
            g = figuras.resplandor(col, 60, 0.9)
            p.blit(g, g.get_rect(center=(int(pos.x), int(pos.y))))
            dibujar_capsula(p, pos.x, pos.y, 34, col, lu * 7)
        if self.tf > 1.9:
            escribir(p, self.f.grande, "¡Se abre la mejor!", 640, 150, (255, 235, 120))
        else:
            escribir(p, self.f.grande, "¡10 cápsulas!", 640, 150, (255, 255, 255))

    def _dib_fondo_oscuro(self, p, color):
        p.fill((16, 8, 36))
        capa_efectos(p, lambda s, k: (brillo_suave(s, k, 640, 340, 520, color, 150),
                                      rayos(s, k, 640, 340, 14, self.rayos_ang * 1.5,
                                            lambda i: color, 38, 1300, 0.4)))

    def _dib_suspenso(self, p, u):
        x, y = 640, 340
        amp = 0.12 + 0.5 * u
        ang = math.sin(self.tf * (9 + 12 * u)) * amp
        pulso = 1 + 0.04 * math.sin(self.tf * 14) + 0.1 * u
        r = self.cap_r * pulso
        dx = math.sin(self.tf * 31) * 5 * u
        col = self.cap_color_ap
        g = figuras.resplandor(col, 230 + int(40 * u), 0.9)
        p.blit(g, g.get_rect(center=(x, y)))
        dibujar_capsula(p, x + dx, y, r, col, ang)
        # grieta de luz en la union
        if u > 0.7:
            k = (u - 0.7) / 0.3
            c, s = math.cos(ang), math.sin(ang)
            pygame.draw.line(p, (255, 255, 255), (x + dx - r * c * 0.9, y - r * s * 0.9), (x + dx + r * c * 0.9, y + r * s * 0.9),
                             int(3 + 8 * k))
        escribir(p, self.f.grande, "¿Qué habrá dentro?", 640, 110 + 3 * math.sin(self.tf * 8), (255, 255, 255))

    def _dib_destello(self, p, u):
        r = self.res["rango"]
        fx = FX[r]
        cx, cy = 640, 340
        # mitades de la capsula que salen volando
        if u < 0.55:
            e = u / 0.55
            col = col_cap(r, self.t)
            dibujar_media_capsula(p, cx - e * 330, cy - e * 300 + e * e * 420, 105, col, -e * 5, True)
            dibujar_media_capsula(p, cx + e * 330, cy + e * 160 + e * e * 520, 105, (236, 240, 250), e * 5, False)
        arco = r == "SSS"

        def efectos(s, k):
            colr = (lambda i: color_arcoiris(i / fx["rayos"] + self.t * 0.5)) if arco else \
                (lambda i: aclarar(figuras.COLOR_RANGO[r], 0.35 if i % 2 else 0.0))
            colbase = color_arcoiris(self.t * 0.6) if arco else figuras.COLOR_RANGO[r]
            brillo_suave(s, k, cx, cy, 120 + 560 * ease_out(u), colbase, int(210 * (1 - 0.5 * u)))
            rot = self.tf * fx["rayos_t"]
            rayos(s, k, cx, cy, fx["rayos"], rot, colr, int(150 * min(1, u * 4) * (1 - 0.25 * u)), 1300,
                  0.55 if r in ("C", "B") else 0.45)
            for j in range(fx["anillos"]):
                uu = u * 1.4 - j * 0.18
                if 0 < uu < 1:
                    pygame.draw.circle(s, (*colbase, int(230 * (1 - uu))), (int(cx * k), int(cy * k)),
                                       max(2, int(uu * 760 * k)), max(2, int(26 * (1 - uu) * k)))
            if fx["espiral"]:
                for j in range(36):
                    a = j * 0.5 + self.tf * 7
                    rad = (30 + j * 11) * (0.3 + u)
                    c = color_arcoiris(j / 36 + self.t) if arco else aclarar(colbase, 0.3)
                    pygame.draw.circle(s, (*c, 200), (int((cx + math.cos(a) * rad) * k), int((cy + math.sin(a) * rad) * k)),
                                       max(2, int(9 * k)))
        capa_efectos(p, efectos)
        if arco:
            for pts in self.rayos_elec:
                pygame.draw.lines(p, (255, 255, 255), False, pts, 6)
                pygame.draw.lines(p, color_arcoiris(self.t * 3), False, pts, 2)
        for b in self.brillos:
            b.dibujar(p)

    def _sil(self, ident, tam, color):
        clave = (ident, tam, color)
        s = self._sil_cache.get(clave)
        if s is None:
            s = figuras._silueta(figuras.superficie(ident, tam), color)
            self._sil_cache[clave] = s
        return s

    def _dib_silueta(self, p, u):
        r = self.res["rango"]
        ident = self.res["id"]
        col = color_rango(r, self.t)
        escala = lerp(0.12, 1.0, ease_out_back(u, 1.3))
        tam = 330
        fuerte = FX[r]["rayos_t"]
        capa_efectos(p, lambda s, k: rayos(s, k, 640, 340, FX[r]["rayos"], self.tf * fuerte, lambda i: col, 70, 1300, 0.4))
        g = figuras.resplandor(col, 260, 0.7)
        p.blit(g, g.get_rect(center=(640, 340)))
        halo = self._sil(ident, tam, col)
        base = self._sil(ident, tam, (22, 14, 44))
        w, h = int(base.get_width() * escala), int(base.get_height() * escala)
        if w > 4 and h > 4:
            hs = pygame.transform.scale(halo, (w + 18, h + 18))
            p.blit(hs, hs.get_rect(center=(640, 340)))
            bs = pygame.transform.scale(base, (w, h))
            p.blit(bs, bs.get_rect(center=(640, 340)))
        if int(self.tf * 5) % 2 == 0:
            escribir(p, self.f.enorme, "¿Quién será?", 640, 640, (255, 255, 255))
        else:
            escribir(p, self.f.enorme, "¿Quién será?", 640, 640, (255, 235, 120))
        for b in self.brillos:
            b.dibujar(p)

    def _sup_letras(self, rango):
        s = self._letras.get(rango)
        if s is not None:
            return s
        fnt = figuras.fuente(270)
        if rango == "SSS":
            cols = [(255, 205, 50), (255, 90, 200), (90, 225, 255)]
        elif rango == "SS":
            cols = [(255, 120, 230), (255, 80, 200)]
        else:
            cols = [figuras.COLOR_RANGO[rango]]
        halo = (255, 255, 255) if rango == "SSS" else aclarar(figuras.COLOR_RANGO[rango], 0.2)
        partes = [fnt.render(ch, True, cols[i % len(cols)]) for i, ch in enumerate(rango)]
        ancho = sum(x.get_width() for x in partes) - 18 * (len(rango) - 1)
        alto = partes[0].get_height()
        pad = 40
        sup = pygame.Surface((ancho + pad * 2, alto + pad * 2), pygame.SRCALPHA)
        x = pad
        pos = []
        for i, ch in enumerate(rango):
            pos.append(x)
            x += partes[i].get_width() - 18
        for radio, color in ((20, halo), (10, (40, 20, 70))):
            for i, ch in enumerate(rango):
                sombra = fnt.render(ch, True, color)
                for k in range(20):
                    a = k * 2 * math.pi / 20
                    sup.blit(sombra, (pos[i] + math.cos(a) * radio, pad + math.sin(a) * radio))
        for i, ch in enumerate(rango):
            sup.blit(partes[i], (pos[i], pad))
            brillo = fnt.render(ch, True, (255, 255, 255))
            brillo.set_alpha(70)
            sup.blit(brillo, (pos[i] - 3, pad - 4))
        self._letras[rango] = sup
        return sup

    def _dib_rango(self, p, u):
        r = self.res["rango"]
        ident = self.res["id"]
        col = color_rango(r, self.t)
        capa_efectos(p, lambda s, k: rayos(s, k, 640, 250, FX[r]["rayos"], self.tf * FX[r]["rayos_t"],
                                           (lambda i: color_arcoiris(i / 28 + self.t * 0.5)) if r == "SSS" else (lambda i: col),
                                           75, 1300, 0.4))
        g = figuras.resplandor(col, 300, 0.7)
        p.blit(g, g.get_rect(center=(640, 260)))
        # silueta que baja y se achica
        e = ease_out(self.tf / 0.35)
        tam = lerp(330, 210, e)
        cy = lerp(340, 540, e)
        sil = self._sil(ident, 330, (22, 14, 44))
        k = tam / 330
        s2 = pygame.transform.smoothscale(sil, (max(2, int(sil.get_width() * k)), max(2, int(sil.get_height() * k))))
        p.blit(s2, s2.get_rect(center=(640, cy)))
        # letra del rango
        sup = self._sup_letras(r)
        gu = self.tf / 0.22
        if gu < 1.0:
            esc = lerp(3.4, 1.0, ease_in(gu))
        else:
            esc = 1.0 + 0.04 * math.sin((self.tf - 0.22) * 9) * max(0.0, 1 - (self.tf - 0.22) / 0.8)
        alto_obj = 250
        k = esc * alto_obj / sup.get_height()
        if k > 0:
            s3 = pygame.transform.smoothscale(sup, (int(sup.get_width() * k), int(sup.get_height() * k)))
            p.blit(s3, s3.get_rect(center=(640, 235)))
        if self.tf > 0.35:
            esc2 = ease_out_back((self.tf - 0.35) / 0.35)
            txt = figuras.NOMBRE_RANGO[r]
            fnt = self.f.enorme
            sup_t = fnt.render(txt, True, (255, 255, 255))
            sombra = fnt.render(txt, True, (40, 20, 70))
            w, h = sup_t.get_size()
            base = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
            for dx in range(-5, 6, 5):
                for dy in range(-5, 6, 5):
                    base.blit(sombra, (6 + dx, 6 + dy))
            base.blit(sup_t, (6, 6))
            k2 = max(0.05, esc2)
            base = pygame.transform.smoothscale(base, (max(2, int(base.get_width() * k2)), max(2, int(base.get_height() * k2))))
            p.blit(base, base.get_rect(center=(640, 408)))
        for b in self.brillos:
            b.dibujar(p)
        if r == "SSS":
            for pts in self.rayos_elec:
                pygame.draw.lines(p, (255, 255, 255), False, pts, 5)

    # --- figura final
    def _fondo_figura(self, p):
        r = self.res["rango"]
        col = color_rango(r, self.t)
        p.fill((20, 10, 44))
        arco = r == "SSS"
        capa_efectos(p, lambda s, k: (brillo_suave(s, k, 640, 300, 560, col, 150),
                                      rayos(s, k, 640, 300, 16 if r != "C" else 10, self.t * 0.35,
                                            (lambda i: color_arcoiris(i / 16 + self.t * 0.3)) if arco else (lambda i: col),
                                            55, 1300, 0.45)))

    def _cartel(self, p, texto, x, y, color, ang):
        fnt = self.f.grande
        t = fnt.render(texto, True, (255, 255, 255))
        sup = pygame.Surface((t.get_width() + 70, 84), pygame.SRCALPHA)
        r = sup.get_rect()
        pygame.draw.rect(sup, oscurecer(color, 0.55), r.move(0, 5), border_radius=22)
        pygame.draw.rect(sup, color, r.inflate(0, -5), border_radius=22)
        pygame.draw.rect(sup, (255, 255, 255), r.inflate(0, -5), 4, border_radius=22)
        sombra = fnt.render(texto, True, oscurecer(color, 0.6))
        sup.blit(sombra, sombra.get_rect(center=(r.centerx + 2, r.centery - 2 + 3)))
        sup.blit(t, t.get_rect(center=(r.centerx, r.centery - 2)))
        k = 1 + 0.06 * math.sin(self.t * 6)
        rot = pygame.transform.rotozoom(sup, ang + 3 * math.sin(self.t * 3), k)
        p.blit(rot, rot.get_rect(center=(int(x), int(y))))

    def _dib_figura(self, p):
        self._fondo_figura(p)
        res = self.res
        r = res["rango"]
        ident = res["id"]
        fig = figuras.FIGURAS[ident]
        e = ease_out_back(self.tf / 0.6, 1.4)
        tam = 300 * max(0.05, e)
        giro = math.cos(self.t * 1.8)
        giro = math.copysign(max(0.3, abs(giro)), giro)
        figuras.dibujar_figura_coleccion(p, ident, 640, 300 - (1 - min(1, e)) * 60, tam, self.t,
                                         ancho_rel=giro, insignia=False)
        for b in self.brillos:
            b.dibujar(p)
        # insignia grande del rango, rango y nombre
        figuras.dibujar_insignia(p, 380, 190, r, 78, self.t)
        escribir(p, self.f.normal, figuras.NOMBRE_RANGO[r], 380, 252, (255, 255, 255))
        escribir(p, self.f.grande, "¡Conseguiste una figura!", 640, 42, (255, 240, 130), contorno=(90, 30, 100))
        self._aviso_paginas(p, 104)
        if self.tf > 0.4:
            escribir(p, self.f.enorme, fig["nombre"], 640, 502, (255, 255, 255), contorno=(60, 20, 90), grosor=3)
            escribir(p, self.f.normal, fig["texto"], 640, 565, (255, 245, 210))
        if self.tf > 0.5:
            if res["nueva"]:
                self._cartel(p, "¡NUEVA!", 930, 215, (255, 170, 30), -10)
            else:
                self._cartel(p, f"¡Repetida! x{res['cant']}", 930, 215, (80, 140, 245), -10)
                escribir(p, self.f.chica, f"Ya tienes {res['cant']} de esta figura", 930, 268, (255, 255, 255))
        self._dib_progreso_album(p)
        if self.modo == 10:
            self.b_resumen.dibujar(p, self.f.normal)
        else:
            self.b_seguir.dibujar(p, self.f.normal)
        self.b_otra.texto = f"Otra vez ({self.costo(1)})" if self.modo == 1 else ""
        if self.modo == 1:
            self.b_otra.dibujar(p, self.f.normal)
            if not self.b_otra.activo:
                escribir(p, self.f.chica, f"Te falta{'n' if self.faltan(1) != 1 else ''} {monedas_txt(self.faltan(1))}; juega para ganar más.", 800, 612, (255, 235, 120))
        self._hud_monedas(p)

    def _dib_progreso_album(self, p):
        """Mini panel con el avance del album y de la pagina de la figura (para querer seguir jugando)."""
        perfil = self.perfil
        f = self.f
        u = figuras.contar_unicas(perfil)
        k = figuras.pagina_de(self.res["id"])
        pg = figuras.PAGINAS[k]
        tengo, tot = figuras.progreso_pagina(perfil, k)
        panel(p, (24, 574, 286, 114), (28, 16, 60), 215, 18, (255, 255, 255))
        escribir(p, f.chica, f"Álbum  {u}/{figuras.TOTAL}", 44, 596, (255, 255, 255), ancla="izq", contorno=None)
        barra(p, (44, 610, 246, 14), u / figuras.TOTAL, color=(255, 200, 60), color_fondo=(70, 55, 110), borde=(255, 255, 255))
        escribir(p, f.chica, f"{pg['nombre']}  {tengo}/{tot}", 44, 644, pg["color"], ancla="izq", contorno=None)
        barra(p, (44, 658, 246, 14), tengo / tot, color=pg["color"], color_fondo=(70, 55, 110), borde=(255, 255, 255))
        if tengo >= tot:
            figuras.arte_estrella(p, 284, 644, 11, (255, 225, 80), (170, 120, 20))

    def _aviso_paginas(self, p, y):
        """Cartel '¡Pagina X completa!' con el aumento de suerte (si la tirada completo alguna pagina)."""
        if not self.paginas_nuevas or self.tf < 0.9:
            return
        nombres = " y ".join(figuras.PAGINAS[k]["nombre"] for k in self.paginas_nuevas)
        base = sum(figuras.probabilidades_efectivas(None)[r] for r in ("S", "SS", "SSS"))
        ef = self.probabilidades()
        alto = sum(ef[r] for r in ("S", "SS", "SSS"))
        txt1 = f"¡Página {nombres} completa!" if len(self.paginas_nuevas) == 1 else f"¡Páginas {nombres} completas!"
        txt2 = f"Suerte del álbum: rangos altos {base:.0f}% > {alto:.0f}%"
        k = 1 + 0.03 * math.sin(self.t * 6)
        w = 620
        r = pygame.Rect(0, 0, int(w * k), 64)
        r.center = (640, y)
        col = figuras.PAGINAS[self.paginas_nuevas[0]]["color"]
        pygame.draw.rect(p, oscurecer(col, 0.5), r.move(0, 5), border_radius=20)
        pygame.draw.rect(p, col, r, border_radius=20)
        pygame.draw.rect(p, (255, 255, 255), r, 4, border_radius=20)
        escribir(p, self.f.normal, txt1, r.centerx, r.y + 23, (255, 255, 255), contorno=oscurecer(col, 0.6))
        escribir(p, self.f.chica, txt2, r.centerx, r.y + 48, (255, 255, 255), contorno=oscurecer(col, 0.6))
        figuras.arte_estrella(p, r.x + 26, r.centery, 15, (255, 240, 120), (170, 110, 20))
        figuras.arte_estrella(p, r.right - 26, r.centery, 15, (255, 240, 120), (170, 110, 20))

    # --- tarjetas, resumen y coleccion
    def _tarjeta(self, p, rect, ident, cant, tag=None, destacada=False, dwell=0.0):
        tengo = cant > 0
        rango = figuras.rango_de(ident)
        col = color_rango(rango, self.t) if tengo else (120, 120, 150)
        fondo_c = (44, 30, 86) if tengo else (36, 28, 62)
        panel(p, rect, fondo_c, 235, 22, col)
        if destacada:
            pygame.draw.rect(p, (255, 235, 120), rect.inflate(8, 8), 5, border_radius=26)
        cx = rect.centerx
        tam = min(rect.w - 60, 118)
        figuras.dibujar_figura_coleccion(p, ident, cx, rect.y + rect.h * 0.40, tam, self.t,
                                         cantidad=cant if tengo else None, silueta=not tengo)
        if tengo:
            escribir(p, self.f.chica, figuras.nombre(ident), cx, rect.bottom - 44 if tag else rect.bottom - 26,
                     (255, 255, 255), contorno=(20, 10, 40))
        else:
            escribir(p, self.f.normal, "???", cx, rect.bottom - 28, (190, 190, 215), contorno=(20, 10, 40))
        if tag:
            escribir(p, self.f.chica, tag[0], cx, rect.bottom - 20, tag[1], contorno=(20, 10, 40))
        if dwell > 0:
            barra(p, (rect.x + 16, rect.bottom - 10, rect.w - 32, 6), min(1.0, dwell / ajustes.DWELL_SEG),
                  color=(255, 230, 90), color_fondo=(100, 100, 130), borde=(255, 255, 255))

    def _fondo_menu(self, p):
        from nucleo import fondo
        fondo(p, (50, 28, 110), (140, 60, 150))
        for (x, y, v, ph) in self._estrellas:
            yy = (y + self.t * 10 * v) % ALTO
            figuras.arte_estrella(p, x, yy, 2 + 2.5 * v * (0.6 + 0.4 * math.sin(self.t * 3 + ph)), (255, 250, 200), (255, 220, 120))

    def _dib_resumen(self, p):
        self._fondo_menu(p)
        f = self.f
        escribir(p, f.grande, "¡Tus 10 figuras!", 640, 40, (255, 240, 130), contorno=(90, 30, 100))
        mejor = self.res
        for i, r in enumerate(self.lote):
            col, fila = i % 5, i // 5
            rect = pygame.Rect(78 + col * 228, 84 + fila * 238, 212, 226)
            tag = ("¡NUEVA!", (255, 210, 70)) if r["nueva"] else (f"Repetida x{r['cant']}", (150, 215, 255))
            self._tarjeta(p, rect, r["id"], r["cant"], tag, destacada=(r is mejor))
        nuevas = sum(1 for r in self.lote if r["nueva"])
        escribir(p, f.normal, f"Nuevas: {nuevas}     Repetidas: {len(self.lote) - nuevas}", 640, 572, (255, 255, 255))
        self._aviso_paginas(p, 596)
        self.b_seguir.dibujar(p, f.normal)
        self.b_otra.dibujar(p, f.normal)
        self._hud_monedas(p)
        if not self.b_otra.activo:
            escribir(p, f.chica, f"Te faltan {monedas_txt(self.faltan(10))} para otro x10.", 800, 606, (255, 235, 120))

    def _dib_coleccion(self, p):
        self._fondo_menu(p)
        f = self.f
        perfil = self.perfil
        u = figuras.contar_unicas(perfil)
        escribir(p, f.grande, "Mi colección", 50, 40, (255, 240, 130), ancla="izq", contorno=(90, 30, 100))
        escribir(p, f.grande, f"Figuras {u}/{figuras.TOTAL}", 1230, 40, (255, 255, 255), ancla="der", contorno=(90, 30, 100))
        barra(p, (460, 30, 300, 22), u / figuras.TOTAL, color=(255, 200, 60))
        # pestanas: Todas + una pagina por mundo
        for i, b in enumerate(self.b_filtros):
            if i == 0:
                txt, col, clave = f"Todas {u}/{figuras.TOTAL}", (150, 110, 230), None
                hecha = u >= figuras.TOTAL
            else:
                k = i - 1
                pg = figuras.PAGINAS[k]
                tengo, tot = figuras.progreso_pagina(perfil, k)
                txt, col, clave = f"{pg['nombre']} {tengo}/{tot}", pg["color"], pg["id"]
                hecha = tengo >= tot
            b.color = col
            self._boton_filtro(p, b, txt, col, clave == self.filtro)
            if hecha:
                figuras.arte_estrella(p, b.rect.right - 16, b.rect.y + 4, 13, (255, 235, 90), (170, 110, 20))
        efe = self.probabilidades()
        base = sum(figuras.PROBABILIDADES[r] for r in ("S", "SS", "SSS"))
        alto = sum(efe[r] for r in ("S", "SS", "SSS"))
        escribir(p, f.chica, f"Cada página que llenas sube tu suerte: rangos altos {base:.0f}% > {alto:.0f}%", 640, 74,
                 (255, 245, 200), contorno=(90, 30, 100))
        lista = self.lista_coleccion()
        ini = self.pagina * self.por_pagina
        for i, b in enumerate(self.b_tarjetas):
            if ini + i >= len(lista):
                continue
            ident = lista[ini + i]
            self._tarjeta(p, b.rect, ident, figuras.cantidad(perfil, ident), dwell=b.dwell if self.detalle is None else 0.0)
        escribir(p, f.chica, f"Página {self.pagina + 1}/{self.paginas()}", 640, ALTO - 50, (255, 255, 255))
        self.b_ant.dibujar(p, f.normal)
        self.b_sig.dibujar(p, f.normal)
        self.b_maquina.dibujar(p, f.normal)
        if self.detalle is not None:
            self._dib_detalle(p)

    def _boton_filtro(self, p, b, txt, col, sel):
        r = b.rect
        c = aclarar(col, 0.25) if b.encima else col
        pygame.draw.rect(p, oscurecer(c, 0.5), r.move(0, 5), border_radius=18)
        pygame.draw.rect(p, c, r, border_radius=18)
        pygame.draw.rect(p, (255, 255, 255), r, 6 if sel else 3, border_radius=18)
        if sel:
            pygame.draw.polygon(p, (255, 255, 255), [(r.centerx - 10, r.bottom + 12), (r.centerx + 10, r.bottom + 12), (r.centerx, r.bottom + 2)])
        escribir(p, self.f.normal if len(txt) < 9 else self.f.chica, txt, r.centerx, r.centery,
                 (255, 255, 255), contorno=oscurecer(col, 0.6))
        if b.dwell > 0:
            barra(p, (r.x + 10, r.bottom - 12, r.w - 20, 6), min(1.0, b.dwell / ajustes.DWELL_SEG),
                  color=(255, 230, 90), color_fondo=(110, 120, 150), borde=(255, 255, 255))

    def _dib_detalle(self, p):
        vel = pygame.Surface((ANCHO, ALTO))
        vel.fill((10, 5, 30))
        vel.set_alpha(190)
        p.blit(vel, (0, 0))
        ident = self.detalle
        cant = figuras.cantidad(self.perfil, ident)
        tengo = cant > 0
        fig = figuras.FIGURAS[ident]
        r = fig["rango"]
        col = color_rango(r, self.t) if tengo else (140, 140, 170)
        panel(p, (230, 80, 820, 546), (44, 30, 86), 250, 28, col)
        giro = math.cos(self.t * 1.8)
        giro = math.copysign(max(0.3, abs(giro)), giro)
        figuras.dibujar_figura_coleccion(p, ident, 480, 300, 300, self.t, silueta=not tengo, ancho_rel=giro if tengo else 1.0,
                                         insignia=False)
        if tengo:
            figuras.dibujar_insignia(p, 330, 160, r, 60, self.t)
            escribir(p, self.f.grande, fig["nombre"], 860, 150, (255, 255, 255), contorno=(20, 10, 40))
            escribir(p, self.f.normal, f"Rango {r}  -  {figuras.NOMBRE_RANGO[r]}", 860, 205, col, contorno=(20, 10, 40))
            escribir(p, self.f.normal, f"Tienes: x{cant}", 860, 250, (255, 235, 120), contorno=(20, 10, 40))
            for i, ln in enumerate(envolver(fig["texto"], self.f.normal, 330)):
                escribir(p, self.f.normal, ln, 860, 310 + i * 34, (255, 255, 255), contorno=(20, 10, 40))
        else:
            escribir(p, self.f.enorme, "???", 860, 170, (200, 200, 225), contorno=(20, 10, 40))
            escribir(p, self.f.normal, "¡Todavía no la tienes!", 860, 250, (255, 235, 120), contorno=(20, 10, 40))
            for i, ln in enumerate(envolver("Sigue tirando en el Gachapon para encontrarla.", self.f.normal, 330)):
                escribir(p, self.f.normal, ln, 860, 310 + i * 34, (255, 255, 255), contorno=(20, 10, 40))
        self.b_cerrar.dibujar(p, self.f.normal)
