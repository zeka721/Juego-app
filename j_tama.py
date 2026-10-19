"""Tamagotchi: BATALLA DE ENTRENAMIENTO por TURNOS con esquive en vivo (Ninja Mundo).

Tu mascota activa (tama_datos.estado(perfil)['activa']) pelea contra un rival de entrenamiento. El rival nunca esta
quieto: deambula suavemente en vertical (tambien en tu turno).

TU TURNO (menu con botones grandes; la mascota NO sigue al cursor):
  * ATAQUE: traza una forma PEQUENA del tipo de tu mascota (rombo, circulo, zigzag, ola, ocho, triangulo), delante de
    ella, siguiendo la luz con el cursor. UNA vuelta, ventana de ~5 s. Calidad 1.0 con la vuelta completa (1.1 si
    la terminas en menos de 2.5 s), parcial 0.6-0.9 y 0.5 si se acaba el tiempo (sin castigo). Al terminar sale un
    proyectil AUTO-APUNTADO en linea recta hacia la posicion actual del rival (900 px/s). El rival puede esquivarlo
    con probabilidad min(0.80, 0.50 + 0.05*(turno-1)) (turno = tu ataque basico n.o N de la batalla). +25 de energia.
  * ELEMENTAL (energia 100): forma GRANDE en el centro, 3 vueltas, ventana ~9 s, calidad 0.5-1.2. Siempre impacta.
  * ESCAPAR: sale sin premio ni castigo.
TURNO DEL RIVAL (esquive en vivo): solo ahora tu mascota SIGUE LA ALTURA DEL CURSOR (650 px/s suavizados; si el cursor
esta en la zona de botones se queda quieta). El rival apunta con una mira (0.8 s; sigue tu altura con 0.25 s de
retraso y se pone ROJA y FIJA los ultimos 0.2 s) y dispara un proyectil en LINEA RECTA al punto bloqueado. Etapas 2 y 3
disparan 2 veces (con ~1.2 s entre disparos), las etapas 0 y 1 una. Si te mueves despues del bloqueo, esquivas. Con la
energia llena usa su ELEMENTAL (carga 1.4 s con aviso; siempre impacta). +8 de energia al recibir un golpe.
Perder deja a la mascota mareada, nunca muere.

Atributos publicos utiles: fase ('intro', 'menu', 'trazo', 'proyectil', 'gesto', 'anim', 'turno_r', 'huida', 'fin'),
mia / rival (dicts con hp, hp_max, estamina, tipo, etapa...), botones, y_jugador, y_rival, banda_j / banda_r,
proy_jugador (dict o None), proys_r (lista) / proy_rival (el ultimo o None), r_estado ('libre', 'aviso', 'mira',
'vuelo', 'carga', 'anim', 'fin_turno'), mira_y, mira_bloqueada, tiros_total, tiro_r, esquivados, golpes_recibidos,
prob_reaccion_rival(), modo_gesto ('chico' | 'grande'), rect_gesto, tipo_gesto, puntos_ctrl, idx_ctrl, vueltas,
t_gesto, calidad, consejo, resultado, ganado, hp_frac.
"""

import math
import random

import pygame

import arte_tama
import tama_datos as td
from ajustes import ANCHO, ALTO
from nucleo import (Boton, Minijuego, TextoFlotante, V2, aclarar, barra, estrella, explosion,
                    oscurecer)

# --- disposicion de la pantalla ---
PX, RX = 230, 1050                           # x fijo de cada mascota
Y_PANELES = 150                              # debajo de las barras de vida
Y_BARRA = 590                                # arriba de la barra de botones
ESCALA_ET = (1.0, 1.0, 0.92, 0.82)           # tamano en batalla por etapa (para caber en la banda de juego)
DUR_CARGADO, DUR_FIN = 2.6, 3.0
ESTAMINA_RECIBIR = getattr(td, "ESTAMINA_RECIBIR", 8)   # energia que da recibir un golpe que impacta
PUNTOS_ESQUIVAR = 5
HP_AVISO_CURAR = 0.30                        # al terminar con menos vida: consejo 'Usa CURAR para recuperar vida'
T_CIERRE = 0.9                               # pausa corta de celebracion al llegar un HP a 0
# --- ataque basico: forma pequena delante de tu mascota ---
LADO_CHICO = 170                             # el cuadro de la forma es de LADO_CHICO x LADO_CHICO
DX_CHICO = 135                               # separacion desde el centro de tu mascota hasta el borde izquierdo
VENTANA_CHICO = 5.0                          # segundos para trazar la forma pequena
RADIO_CHICO = (42, 40, 38, 36)               # radio de acierto de cada punto de control por etapa
T_BONUS_CHICO = 2.5                          # si la terminas antes de esto, calidad 1.1
CAL_CHICO_MIN, CAL_CHICO_PARCIAL = 0.5, (0.6, 0.9)   # sin avance / parcial (0.6 a 0.9 segun el avance)
CAL_CHICO_LLENA, CAL_CHICO_RAPIDA = 1.0, 1.1
PROB_ESQUIVE_BASE, PROB_ESQUIVE_PASO, PROB_ESQUIVE_TOPE = 0.50, 0.05, 0.80   # esquive del rival a tu basico, por turno
V_PROY_JUGADOR = 900.0                       # px/s del proyectil auto-apuntado
DIST_REACCION, V_ESQUIVE_RIVAL = 350.0, 380.0
T_POST_PROY = 0.6                            # pausa tras resolverse tu proyectil, antes del turno del rival
# --- ataque elemental: forma grande ---
RECT_GESTO = pygame.Rect(430, 160, 420, 340)
VENTANA_GESTO = 9.0                          # segundos para dibujar el gesto grande
VUELTAS_LLENO = 3
VUELTAS_EXTRA = 5
QUIETO_CONSEJO = 3.0                         # cursor quieto en el gesto -> consejo 'Sigue la luz'
RADIO_PUNTO = (58, 54, 50, 46)               # radio de acierto en la forma grande por etapa (mas generoso al inicio)
GRACIA_LLENO = 1.5                           # tras 3 vueltas, si dejas de seguir, se lanza
# --- tu mascota en el turno del rival ---
VEL_JUGADOR = 650.0                          # px/s maximos al seguir el cursor
SUAVIZADO = 14.0                             # 1/s: cuanto se acerca al cursor
V_RECENTRAR = 320.0                          # px/s: vuelve al centro durante tu turno
# --- rival ---
V_VAGAR = (140.0, 180.0, 230.0, 280.0)       # velocidad al deambular por etapa del rival
T_VAGAR = (0.6, 1.4)                         # cada cuanto elige una altura nueva
T_AVISO = 1.2                                # aviso 'Le toca a ...'
T_MIRA, T_BLOQUEO, RETRASO_MIRA = 0.8, 0.2, 0.25
V_PROY_RIVAL = (520.0, 600.0, 680.0, 780.0)  # px/s por etapa del rival
TIROS_ETAPA = (1, 1, 2, 2)                   # disparos por turno segun la etapa del rival
INTERVALO_TIROS = 1.2                        # segundos entre disparos de un mismo turno
T_CARGA_ELEM = 1.4
T_FIN_TURNO = 0.6                            # pausa tras el ultimo proyectil del rival
R_HIT = 0.35                                 # radio del hitbox = R_HIT * alto visual

ESCALA_NOTAS = (440, 494, 523, 587, 659, 698, 784, 880)   # nota al acertar cada punto de la guia (se repite)
SONIDOS_USADOS = ("pop", "ok", "lanzar", "tick", "golpe", "bombo", "rugido", "premio", "fallo")

NOMBRE_GESTO = {"electrico": "Zigzag de rayo", "fuego": "Dibuja un círculo", "hielo": "Dibuja un rombo",
                "agua": "Dibuja una ola", "viento": "Dibuja un ocho", "tierra": "Dibuja una montaña"}
VERDE, AMARILLO, ROJO = (90, 205, 120), (245, 205, 70), (238, 100, 92)


def _mezcla(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def color_hp(frac):
    """Verde -> amarillo -> rojo suave segun la vida que queda."""
    if frac >= 0.5:
        return _mezcla(AMARILLO, VERDE, (frac - 0.5) / 0.5)
    return _mezcla(ROJO, AMARILLO, (frac - 0.2) / 0.3)


def _dist_segmento(pt, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / L2))
    return math.hypot(pt[0] - (ax + u * dx), pt[1] - (ay + u * dy))


# ---------------------------------------------------------------- cache de dibujo (rendimiento)
_TXT, _PAN, _GUIA, _VELO = {}, {}, {}, {}


def _escribir(p, fuente, texto, x, y, color=(255, 255, 255), ancla="centro", contorno=(30, 30, 50), grosor=2):
    """Igual que nucleo.escribir pero con el texto (y su contorno) ya compuesto en una superficie en cache."""
    texto = str(texto)
    key = (id(fuente), texto, color, contorno, grosor)
    ent = _TXT.get(key)
    if ent is None:
        if len(_TXT) > 600:
            _TXT.clear()
        base = fuente.render(texto, True, color)
        w, h = base.get_size()
        g = grosor if contorno else 0
        s = pygame.Surface((w + 2 * g, h + 2 * g), pygame.SRCALPHA)
        if contorno:
            sombra = fuente.render(texto, True, contorno)
            for dx in range(-g, g + 1):
                for dy in range(-g, g + 1):
                    if dx or dy:
                        s.blit(sombra, (g + dx, g + dy))
        s.blit(base, (g, g))
        ent = _TXT[key] = (s, w, h, g, fuente)
    s, w, h, g, _ = ent
    if ancla == "centro":
        px, py = x - w / 2, y - h / 2
    elif ancla == "izq":
        px, py = x, y - h / 2
    else:
        px, py = x - w, y - h / 2
    p.blit(s, (int(px) - g, int(py) - g))


def _panel(p, rect, color=(255, 255, 255), alfa=210, radio=22, borde=(40, 60, 110)):
    rect = pygame.Rect(rect)
    key = (rect.w, rect.h, color, alfa, radio, borde)
    s = _PAN.get(key)
    if s is None:
        if len(_PAN) > 80:
            _PAN.clear()
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alfa), s.get_rect(), border_radius=radio)
        pygame.draw.rect(s, (*borde, 255), s.get_rect(), 3, border_radius=radio)
        _PAN[key] = s
    p.blit(s, rect.topleft)


def _velo(tam, color, radio=0):
    key = (tam, color, radio)
    s = _VELO.get(key)
    if s is None:
        s = pygame.Surface(tam, pygame.SRCALPHA)
        pygame.draw.rect(s, color, s.get_rect(), border_radius=radio)
        _VELO[key] = s
    return s


def _guia_cache(tipo, rect, idx):
    """Guia de la forma (sin la luz que viaja) ya dibujada para el punto de control idx. Devuelve (sup, ox, oy, dens)."""
    key = (tipo, rect.x, rect.y, rect.w, rect.h, idx)
    ent = _GUIA.get(key)
    if ent is not None:
        return ent
    if len(_GUIA) > 160:
        _GUIA.clear()
    col = arte_tama.COLOR_TIPO[tipo]
    dens = arte_tama.trazo_guia(tipo, rect)
    ctrl = arte_tama.puntos_guia(tipo, rect)
    m = 40
    surf = pygame.Surface((rect.w + 2 * m, rect.h + 2 * m), pygame.SRCALPHA)
    ox, oy = rect.x - m, rect.y - m
    D = [(x - ox, y - oy) for x, y in dens]
    C = [(x - ox, y - oy) for x, y in ctrl]
    ancho = 10
    prog = idx / len(ctrl)

    def trazo(pts, w, color):
        if len(pts) < 2:
            return
        pygame.draw.lines(surf, color, False, pts, w)
        for q in pts[::2] + [pts[-1]]:
            pygame.draw.circle(surf, color, (int(q[0]), int(q[1])), w // 2)

    trazo(D, ancho + 12, col + (34,))
    trazo(D, ancho, aclarar(col, 0.25) + (92,))
    trazo(D, 2, (255, 255, 255, 120))
    if prog > 0:
        Dp = D[:max(2, int(len(D) * prog))]
        trazo(Dp, ancho + 14, col + (95,))
        trazo(Dp, ancho + 2, aclarar(col, 0.35) + (255,))
        trazo(Dp, 3, (255, 255, 255, 255))
    for i, c in enumerate(C):
        vis = (i + 0.5) / len(C) <= prog + 1e-6 and prog > 0
        r = ancho * (0.55 if vis else 0.38)
        pygame.draw.circle(surf, (255, 255, 255, 235 if vis else 120), (int(c[0]), int(c[1])), int(r) + 2)
        pygame.draw.circle(surf, (aclarar(col, 0.2) if vis else col) + (255 if vis else 140,),
                           (int(c[0]), int(c[1])), int(r))
    for fr in (0.14, 0.38, 0.62, 0.86):
        i = int(fr * (len(D) - 1))
        a, b = D[max(0, i - 3)], D[min(len(D) - 1, i + 3)]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        hecho = prog > 0 and fr <= prog
        s = ancho * 1.25
        tri = [(D[i][0] + math.cos(ang) * s, D[i][1] + math.sin(ang) * s),
               (D[i][0] + math.cos(ang + 2.5) * s, D[i][1] + math.sin(ang + 2.5) * s),
               (D[i][0] + math.cos(ang - 2.5) * s, D[i][1] + math.sin(ang - 2.5) * s)]
        pygame.draw.polygon(surf, (255, 255, 255, 255 if hecho else 190), tri)
        pygame.draw.polygon(surf, oscurecer(col, 0.45) + (255,), tri, 2)
    ent = _GUIA[key] = (surf, ox, oy, dens)
    return ent


class _BotonBatalla(Boton):
    """Boton grande con titulo y subtitulo; el elemental muestra el icono del tipo."""

    def __init__(self, rect, titulo, sub, color, tipo=None):
        super().__init__(rect, titulo, color)
        self.titulo, self.sub, self.tipo = titulo, sub, tipo
        self.t = 0.0

    def dibujar(self, p, fuente, fnormal=None, fchica=None, t=0.0):
        r = self.rect
        col = aclarar(self.color, 0.22) if self.encima else self.color
        if not self.activo:
            col = (176, 180, 194)
        pygame.draw.rect(p, oscurecer(col, 0.5), r.move(0, 6), border_radius=24)
        pygame.draw.rect(p, col, r, border_radius=24)
        pygame.draw.rect(p, aclarar(col, 0.3), (r.x + 8, r.y + 6, r.w - 16, r.h * 0.36), border_radius=18)
        borde = (255, 255, 255)
        if self.tipo and self.activo:
            pulso = 0.5 + 0.5 * math.sin(t * 6)
            borde = _mezcla((255, 255, 255), (255, 225, 90), pulso)
        pygame.draw.rect(p, borde, r, 5, border_radius=24)
        tx = r.centerx
        if self.tipo and self.activo:
            arte_tama.dibujar_icono_tipo(p, self.tipo, r.x + 56, r.centery - 6, 30)
            tx = r.centerx + 36
        txt_col = (255, 255, 255) if self.activo else (110, 114, 130)
        con = (30, 30, 50) if self.activo else (225, 228, 238)
        _escribir(p, fuente, self.titulo, tx, r.centery - 16, txt_col, contorno=con)
        _escribir(p, fchica, self.sub, tx, r.centery + 24, txt_col if self.activo else (80, 84, 100),
                  contorno=con if self.activo else None, grosor=1)
        if self.dwell > 0:
            from ajustes import DWELL_SEG
            fr = min(1.0, self.dwell / DWELL_SEG)
            rr = pygame.Rect(r.x + 18, r.bottom - 15, r.w - 36, 8)
            barra(p, rr, fr, color=(255, 230, 90), color_fondo=(110, 120, 150), borde=(255, 255, 255))


class Tamagotchi(Minijuego):
    id = "tamagotchi"
    titulo = "Tamagotchi"
    instruccion = "Sigue la forma para atacar y esquiva moviendo el cursor."
    gesto = "Sigue la forma y mueve el cursor arriba y abajo"
    duracion = None
    NIVEL_MAX = 1

    def __init__(self, ctx, nivel=1, rng=None):
        super().__init__(ctx, nivel)
        self.rng = rng or random.Random()
        perfil = ctx.perfil
        activa = td.estado(perfil)["activa"]
        self.prestada = activa is None
        if self.prestada:                       # mascota de prueba: no se guarda nada
            activa = dict(especie="dragon", etapa=1, nombre=td.ESPECIES["dragon"]["formas"][1])
        self.mascota = activa
        esp, et = activa["especie"], int(activa["etapa"])
        st = td.stats(esp, et)
        self.mia = dict(especie=esp, etapa=et, tipo=td.ESPECIES[esp]["tipo"], nombre=activa.get("nombre") or
                        td.ESPECIES[esp]["formas"][et], hp=float(st["hp"]), hp_max=float(st["hp"]),
                        ataque=st["ataque"], stats=st, estamina=0, hp_vis=float(st["hp"]))
        en = self._enemigo_de_prueba(et) if self.prestada else td.enemigo(perfil, self.rng)
        self.rival = dict(especie=en["especie"], etapa=en["etapa"], tipo=en["tipo"], nombre=en["nombre"],
                          hp=float(en["hp"]), hp_max=float(en["hp"]), ataque=en["ataque"], estamina=0,
                          stats=td.stats(en["especie"], en["etapa"]), hp_vis=float(en["hp"]))
        if not self.prestada:                    # la vida con la que quedaste en la ultima batalla
            f0 = max(0.01, min(1.0, float(td.hp_frac(perfil))))
            self.mia["hp"] = self.mia["hp_vis"] = f0 * self.mia["hp_max"]
        self.hp_inicial = self.mia["hp"] / self.mia["hp_max"]
        self.hp_guardado = False                 # la vida se guarda UNA sola vez
        self.hp_guardada = None
        self.ataques_basicos = 0
        self.dano_hecho = 0
        self.hp_frac = 1.0
        self.resultado = None
        self.recompensado = False
        self.fase = "intro"
        self.t_fase = 0.0
        self.anim = None
        self.msg = ""
        self.t_msg = 0.0
        self.consejo = None
        self.particulas = []
        self.fx = []                             # impactos en el campo
        self.flot_chicos = []
        self.temblor = 0.0
        self.flash = 0.0
        self.pos = V2(ANCHO / 2, ALTO / 2)
        self._lienzo = pygame.Surface((ANCHO, ALTO))
        self._blanco = None
        # gesto (forma pequena del ataque basico o grande del elemental)
        self.modo_gesto = "chico"
        self.tipo_gesto = self.mia["tipo"]
        self.rect_gesto = pygame.Rect(0, 0, LADO_CHICO, LADO_CHICO)
        self.puntos_ctrl = []
        self.idx_ctrl = 0
        self.vueltas = 0
        self.t_gesto = 0.0
        self.t_quieto = 0.0
        self.t_lleno = 0.0
        self.rastro = []
        self._prev = V2(self.pos)
        self.radio = RADIO_PUNTO[max(0, min(3, et))]
        self.calidad = 1.0
        self.poca_vida = False
        self.final = None                       # 'gana' | 'pierde' | 'escapa'
        self.t_huida = 0.0
        # campo de juego
        self.escala_j = ESCALA_ET[max(0, min(3, et))]
        self.escala_r = ESCALA_ET[max(0, min(3, self.rival["etapa"]))]
        self.alto_j = arte_tama.ALTO_ETAPA[max(0, min(3, et))] * self.escala_j
        self.alto_r = arte_tama.ALTO_ETAPA[max(0, min(3, self.rival["etapa"]))] * self.escala_r
        self.banda_j = (Y_PANELES + self.alto_j / 2 + 4, Y_BARRA - self.alto_j / 2 - 4)
        self.banda_r = (Y_PANELES + self.alto_r / 2 + 4, Y_BARRA - self.alto_r / 2 - 4)
        self.y_jugador = (self.banda_j[0] + self.banda_j[1]) / 2
        self.y_rival = (self.banda_r[0] + self.banda_r[1]) / 2
        self.t_mundo = 0.0
        self.hist_y = [(0.0, self.y_jugador)]
        # tu ataque
        self.proy_jugador = None
        self.t_post = 0.0
        self.ventana = VENTANA_CHICO
        self.vueltas_obj = 1
        self.t_ataca_j = self.t_golp_j = self.t_ataca_r = self.t_golp_r = 0.0
        # rival
        self.forzar_reaccion = None              # para pruebas: True/False fuerza la reaccion al esquivar
        self.r_target = self.y_rival
        self.r_t_cambio = self.rng.uniform(*T_VAGAR)
        self.r_pausa = 0.0
        self.r_esq = None                        # movimiento rapido de esquive
        self.r_estado = "libre"
        self.r_t = 0.0
        self.tiros_total = 1
        self.tiro_r = 0
        self.mira_y = self.y_jugador
        self.mira_bloqueada = False
        self.proys_r = []
        self.cierre = None
        self.t_cierre = 0.0
        self.esquivados = 0
        self.golpes_recibidos = 0
        self.ayuda = self._ayuda_pendiente()
        # botones: barra inferior (solo en tu turno)
        y, h = 598, 102
        self.botones = {
            "ataque": _BotonBatalla((40, y, 380, h), "ATAQUE", "Dibuja la forma", (235, 130, 70)),
            "elemental": _BotonBatalla((450, y, 400, h), "ELEMENTAL", "Carga tu energía",
                                       arte_tama.COLOR_TIPO[self.mia["tipo"]], tipo=self.mia["tipo"]),
            "escapar": _BotonBatalla((910, y + 14, 300, h - 28), "ESCAPAR", "Salir sin premio", (90, 140, 215)),
        }
        pre = getattr(arte_tama, "precalentar", None)
        if pre:
            try:
                pre()
            except Exception as e:                       # el arte nunca debe romper el juego
                print("precalentar:", e)
        self._precalentar_sonidos()
        self._precalentar_dibujo()
        self.fondo_arriba = self.fondo_abajo = (60, 60, 90)
        self._msg("¡Batalla de entrenamiento!", 1.4)

    def _precalentar_dibujo(self):
        """Un cuadro de prueba fuera de pantalla: llena las caches del fondo, las mascotas, los paneles y los textos
        para que el primer cuadro real no se note."""
        try:
            self._dibujar_escena(self._lienzo)
            self._hud(self._lienzo)
            self.botones["elemental"].activo = True
            self.botones["elemental"].dibujar(self._lienzo, self.f.grande, self.f.normal, self.f.chica, 0.0)
            self.botones["elemental"].activo = False
            rc = self._rect_chico()
            for i in range(len(arte_tama.puntos_guia(self.tipo_gesto, rc))):
                _guia_cache(self.tipo_gesto, rc, i)
        except Exception as e:
            print("precalentar dibujo:", e)

    def _precalentar_sonidos(self):
        """Los sonidos se sintetizan la primera vez que suenan (2 a 20 ms cada uno): se preparan aqui, en la carga,
        para que no haya tirones en pleno combate. Sin audio no hace nada."""
        s = self.sonidos
        try:
            if not getattr(s, "ok", False):
                return
            cache = s._cache
            for nombre in SONIDOS_USADOS:
                if nombre not in cache:
                    cache[nombre] = s._crear(nombre)
            for f in ESCALA_NOTAS:
                clave = ("nota", round(f), round(0.12, 2))
                if clave not in cache:
                    cache[clave] = s._tono(f, f, 0.12, 0.2, "seno", 1.2)
        except Exception as e:                                # el sonido nunca debe romper el juego
            print("precalentar sonidos:", e)

    def _enemigo_de_prueba(self, etapa):
        tipo = self.rng.choice(td.TIPOS)
        esp = self.rng.choice([e for e in td.ORDEN if td.ESPECIES[e]["tipo"] == tipo])
        s = td.stats(esp, etapa)
        return dict(especie=esp, etapa=etapa, tipo=tipo, hp=s["hp"], ataque=s["ataque"],
                    nombre=td.ESPECIES[esp]["formas"][etapa])

    def calcular_metas(self):
        return (1, 2, 3)

    def estrellas(self):
        if self.ganado is not True:
            return 0
        f = self.hp_frac
        return 3 if f >= 0.8 else 2 if f >= 0.5 else 1

    # ---------------------------------------------------------------- utilidades
    def _msg(self, texto, dur=1.2):
        self.msg, self.t_msg = texto, dur

    def _ir(self, fase):
        self.fase, self.t_fase = fase, 0.0

    def _ventaja_msg(self, tipo_a, tipo_d):
        v = td.ventaja(tipo_a, tipo_d)
        return "¡Muy eficaz!" if v > 1 else "No fue muy eficaz" if v < 1 else ""

    def _ayuda_pendiente(self):
        try:
            return not self.ctx.perfil.extra.get("tama_ayuda_hibrido", False)
        except Exception:
            return False

    def _ayuda_vista(self):
        self.ayuda = False
        try:
            self.ctx.perfil.extra["tama_ayuda_hibrido"] = True
        except Exception:
            pass

    def radio_hit_j(self):
        return R_HIT * self.alto_j

    def radio_hit_r(self):
        return R_HIT * self.alto_r

    @staticmethod
    def prob_esquive_turno(turno):
        """Probabilidad de que el rival esquive tu ataque basico numero 'turno' (1, 2, ...): 50% subiendo 5% por turno
        hasta 80%."""
        return min(PROB_ESQUIVE_TOPE, PROB_ESQUIVE_BASE + PROB_ESQUIVE_PASO * (max(1, int(turno)) - 1))

    def prob_reaccion_rival(self, turno=None):
        """Probabilidad de esquive del turno actual: el del ataque en vuelo, o el del proximo si no hay ninguno."""
        if turno is None:
            turno = self.ataques_basicos if self.proy_jugador else self.ataques_basicos + 1
        return self.prob_esquive_turno(turno)

    def _recibe_estamina(self, e):
        e["estamina"] = min(100, e["estamina"] + ESTAMINA_RECIBIR)

    def _y_jugador_en(self, t):
        """Altura de tu mascota en el instante t del mundo (para la mira con retraso)."""
        h = self.hist_y
        for i in range(len(h) - 1, -1, -1):
            if h[i][0] <= t:
                return h[i][1]
        return h[0][1]

    # ---------------------------------------------------------------- golpes y animaciones
    def _golpear(self, quien, dano, vent, x, y, grande=False):
        """Aplica un impacto de 'quien' (j/r) sobre el otro: dano, energia, textos, efectos."""
        defe = self.rival if quien == "j" else self.mia
        atac = self.mia if quien == "j" else self.rival
        dx = RX if quien == "j" else PX
        dy = self.y_rival if quien == "j" else self.y_jugador
        defe["hp"] = max(0.0, defe["hp"] - dano)
        self._recibe_estamina(defe)
        ty = max(235.0, dy - self.alto_j * 0.5 - 30)             # nunca detras de los paneles de vida
        self.flotantes.append(TextoFlotante(f"-{dano}", dx, ty,
                                            (255, 240, 120) if quien == "j" else (255, 130, 120), vida=1.2))
        frase = vent or ("¡Le diste!" if quien == "j" else "")
        if frase:
            self.flotantes.append(TextoFlotante(frase, dx, ty - 60, (255, 255, 255), vida=1.4, subida=30))
        col = arte_tama.COLOR_TIPO[atac["tipo"]]
        explosion(self.particulas, x, y, col, n=26 if grande else 12, vel_min=80, vel_max=420 if grande else 280,
                  vida=0.9, gravedad=380, radio=7 if grande else 5)
        self.fx.append(dict(tipo=atac["tipo"], etapa=atac["etapa"], x=x, y=y, t=0.0, dur=0.55))
        self.temblor = (7 + 5 * atac["etapa"]) if grande else 3.5
        if grande:
            self.flash = 0.8
        self.sonidos.reproducir("bombo" if grande else "golpe")
        if quien == "j":
            self.dano_hecho += dano
            self.t_golp_r = 0.4
        else:
            self.golpes_recibidos += 1
            self.t_golp_j = 0.4
        self._recalc_puntos()

    def _recalc_puntos(self):
        self.puntos = self.dano_hecho // 2 + PUNTOS_ESQUIVAR * self.esquivados

    def _nueva_anim(self, quien, dano, vent):
        atac, defe = (self.mia, self.rival) if quien == "j" else (self.rival, self.mia)
        return dict(quien=quien, kind="cargado", t=0.0, dur=DUR_CARGADO, t_imp=0.42 * DUR_CARGADO, dano=dano,
                    aplicado=False, vent=vent, atac=atac, defe=defe)

    def _lanzar_cargado(self):
        self.calidad = self._calidad()
        m = self.mia
        d = td.dano(m["stats"], m["etapa"], m["tipo"], self.rival["tipo"], cargado=True, calidad=self.calidad)
        self.anim = self._nueva_anim("j", d, self._ventaja_msg(m["tipo"], self.rival["tipo"]))
        self.consejo = None
        self._ir("anim")
        self.t_ataca_j = 1.0
        self.sonidos.reproducir("lanzar")
        self._msg("¡No se puede esquivar!", 1.8)

    def _lanzar_cargado_rival(self):
        r = self.rival
        r["estamina"] = 0
        cal = self.rng.uniform(0.7, 1.0)
        d = td.dano(r["stats"], r["etapa"], r["tipo"], self.mia["tipo"], cargado=True, calidad=cal)
        self.anim = self._nueva_anim("r", d, self._ventaja_msg(r["tipo"], self.mia["tipo"]))
        self.r_estado = "anim"
        self._ir("anim")
        self.t_ataca_r = 1.0
        self.sonidos.reproducir("lanzar")

    def _paso_anim(self, dt):
        a = self.anim
        a["t"] += dt
        if not a["aplicado"] and a["t"] >= a["t_imp"]:
            a["aplicado"] = True
            x = RX if a["quien"] == "j" else PX
            y = self.y_rival if a["quien"] == "j" else self.y_jugador
            self._golpear(a["quien"], a["dano"], a["vent"], x, y, grande=True)
        if a["t"] >= a["dur"]:
            quien = a["quien"]
            self.anim = None
            if self.cierre is not None:
                return
            if quien == "r":
                self.r_estado = "fin_turno"
                self.r_t = 0.0
                self._ir("turno_r")
            else:
                self._ir_turno_r()

    # ---------------------------------------------------------------- tu ataque basico
    def _origen_j(self):
        return V2(PX + 80, self.y_jugador)

    def _rect_chico(self):
        """Cuadro de la forma pequena: justo delante (a la derecha) de tu mascota, sin salirse de la zona de juego."""
        cy = max(Y_PANELES + 15 + LADO_CHICO / 2, min(548 - LADO_CHICO / 2, self.y_jugador))
        return pygame.Rect(int(PX + DX_CHICO), int(cy - LADO_CHICO / 2), LADO_CHICO, LADO_CHICO)

    def _iniciar_trazo(self):
        """ATAQUE: forma pequena del tipo de tu mascota, delante de ella."""
        self.modo_gesto = "chico"
        self.rect_gesto = self._rect_chico()
        self.radio = RADIO_CHICO[max(0, min(3, self.mia["etapa"]))]
        self.ventana = VENTANA_CHICO
        self.vueltas_obj = 1
        self._empezar_gesto("trazo")
        self._msg("¡Sigue la luz!", 1.2)

    def _iniciar_gesto(self):
        """ELEMENTAL: forma grande en el centro, 3 vueltas."""
        self.mia["estamina"] = 0
        self.modo_gesto = "grande"
        self.rect_gesto = RECT_GESTO.copy()
        self.radio = RADIO_PUNTO[max(0, min(3, self.mia["etapa"]))]
        self.ventana = VENTANA_GESTO
        self.vueltas_obj = VUELTAS_LLENO
        self._empezar_gesto("gesto")
        self._msg("¡Sigue la luz!", 1.5)

    def _empezar_gesto(self, fase):
        self.puntos_ctrl = arte_tama.puntos_guia(self.tipo_gesto, self.rect_gesto)
        self.idx_ctrl = 0
        self.vueltas = 0
        self.t_gesto = 0.0
        self.t_quieto = 0.0
        self.t_lleno = 0.0
        self.rastro = []
        self.consejo = None
        self._prev = V2(self.pos)
        self._ir(fase)
        self.sonidos.reproducir("pop")

    def _disparar_jugador(self):
        """Fin de la forma pequena: proyectil recto y AUTO-APUNTADO a la posicion actual del rival. +25 de energia."""
        m = self.mia
        self.calidad = self._calidad()
        o = self._origen_j()
        objetivo = V2(RX, self.y_rival)
        d = objetivo - o
        d = d / d.length()
        dano = td.dano(m["stats"], m["etapa"], m["tipo"], self.rival["tipo"], rng=self.rng)
        dano = max(1, int(round(dano * self.calidad)))
        self.ataques_basicos += 1
        prob = self.prob_esquive_turno(self.ataques_basicos)
        sortea = self.forzar_reaccion if self.forzar_reaccion is not None else self.rng.random() < prob
        self.proy_jugador = dict(prob_esquive=prob, esquiva=bool(sortea), turno=self.ataques_basicos, x=o.x, y=o.y, ux=d.x, uy=d.y, t=0.0, reaccion_vista=False, reaccionado=False,
                                 golpeo=False, dano=dano, calidad=self.calidad, objetivo_y=self.y_rival)
        m["estamina"] = min(100, m["estamina"] + td.ESTAMINA_BASICO)
        self.t_ataca_j = 0.5
        self.consejo = None
        self.msg, self.t_msg = "", 0.0
        if self.ayuda:
            self._ayuda_vista()
        self._ir("proyectil")
        self.t_post = 0.0
        self.sonidos.reproducir("lanzar")

    def _paso_proy_jugador(self, dt):
        p = self.proy_jugador
        x0, y0 = p["x"], p["y"]
        p["t"] += dt
        p["x"] += p["ux"] * V_PROY_JUGADOR * dt
        p["y"] += p["uy"] * V_PROY_JUGADOR * dt
        # el rival intenta esquivar cuando el proyectil se acerca
        if not p["reaccion_vista"] and RX - p["x"] < DIST_REACCION and p["x"] < RX:
            p["reaccion_vista"] = True
            self._rival_reacciona(p)
        # impacto contra el hitbox del rival
        if _dist_segmento((RX, self.y_rival), (x0, y0), (p["x"], p["y"])) <= self.radio_hit_r() + 6:
            p["golpeo"] = True
            self._golpear("j", p["dano"], self._ventaja_msg(self.mia["tipo"], self.rival["tipo"]), RX,
                          self.y_rival)
            self.proy_jugador = None
            return
        if p["x"] > ANCHO + 60 or p["y"] < -60 or p["y"] > ALTO + 60 or p["x"] < -60:
            txt = "¡Esquivó!" if p["reaccionado"] else "¡Fallaste!"
            self.flot_chicos.append(TextoFlotante(txt, min(ANCHO - 120, RX), max(210, min(560, p["y"])),
                                                  (255, 255, 255), vida=1.0, subida=30))
            self.proy_jugador = None

    def _rival_reacciona(self, p):
        """Con probabilidad prob_reaccion_rival se mueve rapido fuera de la linea, si le da tiempo."""
        ry = self.y_rival
        if p["ux"] <= 1e-6:
            return False
        yl = p["y"] + (RX - p["x"]) * p["uy"] / p["ux"]      # altura de la linea al llegar a la x del rival
        perp = abs(ry - yl) * p["ux"]
        necesario = self.radio_hit_r() + 12 - perp
        if necesario <= 0:
            return False                                      # no le iba a dar: no hace falta
        if not p.get("esquiva"):                                  # se sortea una vez por ataque, al salir el proyectil
            return False
        t_disp = (RX - p["x"]) / (V_PROY_JUGADOR * p["ux"])
        lado0 = 1 if ry >= yl else -1
        lo, hi = self.banda_r
        for lado in (lado0, -lado0):
            destino = max(lo, min(hi, ry + lado * (necesario + 20)))
            lograr = abs(destino - ry)
            sale = abs(destino - yl) * p["ux"] >= self.radio_hit_r() + 8
            if sale and lograr <= V_ESQUIVE_RIVAL * t_disp * 0.95:
                self.r_esq = dict(target=destino)
                p["reaccionado"] = True
                return True
        return False

    # ---------------------------------------------------------------- rival
    def _rival_vaga(self):
        f = self.fase
        if f in ("menu", "trazo", "gesto"):
            return True
        return f == "turno_r" and self.r_estado in ("aviso", "vuelo", "fin_turno")

    def _mover_rival(self, dt):
        et = max(0, min(3, self.rival["etapa"]))
        if self.r_esq is not None:
            d = self.r_esq["target"] - self.y_rival
            paso = V_ESQUIVE_RIVAL * dt
            if abs(d) <= paso:
                self.y_rival = self.r_esq["target"]
                self.r_esq = None
            else:
                self.y_rival += math.copysign(paso, d)
        elif self._rival_vaga():
            self._vagar(dt, V_VAGAR[et])

    def _vagar(self, dt, vel):
        if self.r_pausa > 0:
            self.r_pausa -= dt
        else:
            d = self.r_target - self.y_rival
            v = vel * min(1.0, 0.25 + abs(d) / 70.0)
            paso = v * dt
            self.y_rival = self.r_target if abs(d) <= paso else self.y_rival + math.copysign(paso, d)
        self.r_t_cambio -= dt
        if self.r_t_cambio <= 0:
            lo, hi = self.banda_r
            for _ in range(8):
                nuevo = self.rng.uniform(lo, hi)
                if abs(nuevo - self.y_rival) >= 50:
                    break
            self.r_target = nuevo
            self.r_t_cambio = self.rng.uniform(*T_VAGAR)
            if self.rng.random() < 0.3:
                self.r_pausa = self.rng.uniform(0.1, 0.35)

    @property
    def proy_rival(self):
        return self.proys_r[-1] if self.proys_r else None

    def _ir_turno_r(self):
        """Empieza el turno del rival: aviso, y tu mascota pasa a seguir el cursor."""
        et = max(0, min(3, self.rival["etapa"]))
        self.tiros_total = TIROS_ETAPA[et]
        self.tiro_r = 0
        self.proys_r = []
        self.r_estado = "aviso"
        self.r_t = 0.0
        self.mira_bloqueada = False
        self.consejo = None
        self._ir("turno_r")
        self.sonidos.reproducir("pop")

    def _ir_menu(self):
        self.r_estado = "libre"
        self._ir("menu")
        for b in self.botones.values():
            b.espera, b.dwell = 0.8, 0.0
        self._msg("Tu turno", 1.2)

    def _empezar_mira(self):
        self.r_estado = "mira"
        self.r_t = 0.0
        self.mira_bloqueada = False
        self.mira_y = self._y_jugador_en(self.t_mundo - RETRASO_MIRA)

    def _paso_turno_r(self, dt):
        r = self.rival
        st = self.r_estado
        if st == "aviso":
            self.r_t += dt
            if self.r_t >= T_AVISO:
                self.r_t = 0.0
                if r["estamina"] >= 100:
                    self.r_estado = "carga"
                    self._msg("¡Ataque elemental!", 1.4)
                    self.sonidos.reproducir("rugido")
                else:
                    self._empezar_mira()
        elif st == "mira":
            self.r_t += dt
            if self.r_t < T_MIRA - T_BLOQUEO:
                self.mira_y = self._y_jugador_en(self.t_mundo - RETRASO_MIRA)
            elif not self.mira_bloqueada:
                self.mira_bloqueada = True
                self.sonidos.reproducir("tick")
            if self.r_t >= T_MIRA:
                self._disparar_rival()
        elif st == "carga":
            self.r_t += dt
            if self.r_t >= T_CARGA_ELEM:
                self._lanzar_cargado_rival()
        elif st == "vuelo":
            self.r_t += dt                                   # tiempo desde el ultimo disparo
            if self.tiro_r < self.tiros_total:
                if self.r_t >= INTERVALO_TIROS - T_MIRA:
                    self._empezar_mira()
            elif not self.proys_r:
                self.r_estado = "fin_turno"
                self.r_t = 0.0
        elif st == "fin_turno":
            self.r_t += dt
            if self.r_t >= T_FIN_TURNO:
                self._ir_menu()

    def _disparar_rival(self):
        r = self.rival
        et = max(0, min(3, r["etapa"]))
        r["estamina"] = min(100, r["estamina"] + td.ESTAMINA_BASICO)
        o = V2(RX - 70, self.y_rival)
        objetivo = V2(PX, self.mira_y)
        d = objetivo - o
        d = d / d.length()
        self.proys_r.append(dict(x=o.x, y=o.y, x0=o.x, y0=o.y, ux=d.x, uy=d.y, v=V_PROY_RIVAL[et], t=0.0,
                                 golpeo=False, dano=td.dano(r["stats"], r["etapa"], r["tipo"], self.mia["tipo"],
                                                            rng=self.rng)))
        self.tiro_r += 1
        self.r_estado = "vuelo"
        self.r_t = 0.0
        self.mira_bloqueada = False
        self.t_ataca_r = 0.35
        self.sonidos.reproducir("lanzar")

    def _paso_proys_rival(self, dt):
        vivos = []
        for p in self.proys_r:
            x0, y0 = p["x"], p["y"]
            p["t"] += dt
            p["x"] += p["ux"] * p["v"] * dt
            p["y"] += p["uy"] * p["v"] * dt
            if _dist_segmento((PX, self.y_jugador), (x0, y0), (p["x"], p["y"])) <= self.radio_hit_j() + 6:
                self._golpear("r", p["dano"], self._ventaja_msg(self.rival["tipo"], self.mia["tipo"]), PX,
                              self.y_jugador)
                continue
            if p["x"] < -60 or p["y"] < -60 or p["y"] > ALTO + 60 or p["x"] > ANCHO + 80:
                self.esquivados += 1
                self._recalc_puntos()
                self.flotantes.append(TextoFlotante("¡Esquivaste!", PX, max(215.0, self.y_jugador - self.alto_j * 0.5 - 40),
                                                    (255, 255, 255), vida=1.4, subida=30))
                self.sonidos.reproducir("pop")
                continue
            vivos.append(p)
        self.proys_r = vivos

    # ---------------------------------------------------------------- mundo
    def _mover_jugador(self, dt):
        lo, hi = self.banda_j
        if self.fase == "turno_r":
            y = self.pos.y
            if Y_PANELES <= y < Y_BARRA:                     # sobre los botones se queda donde estaba
                obj = max(lo, min(hi, y))
                d = obj - self.y_jugador
                paso = min(VEL_JUGADOR * dt, abs(d) * (1.0 - math.exp(-SUAVIZADO * dt)))
                self.y_jugador += math.copysign(paso, d)
        elif self.fase == "menu":                            # vuelve suavemente al centro
            d = (lo + hi) / 2 - self.y_jugador
            self.y_jugador += math.copysign(min(V_RECENTRAR * dt, abs(d)), d)
        self.hist_y.append((self.t_mundo, self.y_jugador))
        while len(self.hist_y) > 2 and self.t_mundo - self.hist_y[1][0] > 1.0:
            self.hist_y.pop(0)

    def _timers(self, dt):
        for k in ("t_ataca_j", "t_golp_j", "t_ataca_r", "t_golp_r"):
            setattr(self, k, max(0.0, getattr(self, k) - dt))

    def calidad_actual(self):
        return self._calidad()

    def progreso_gesto(self):
        """Vueltas completas + fraccion de la vuelta en curso."""
        return self.vueltas + self.idx_ctrl / max(1, len(self.puntos_ctrl))

    def _calidad(self):
        if self.modo_gesto == "chico":
            if self.vueltas >= 1:
                return CAL_CHICO_RAPIDA if self.t_gesto < T_BONUS_CHICO else CAL_CHICO_LLENA
            if self.idx_ctrl <= 0:
                return CAL_CHICO_MIN
            lo, hi = CAL_CHICO_PARCIAL
            return lo + (hi - lo) * self.idx_ctrl / len(self.puntos_ctrl)
        if self.vueltas >= VUELTAS_LLENO:
            extra = min(VUELTAS_EXTRA, self.vueltas - VUELTAS_LLENO)
            return 0.8 + 0.4 * extra / VUELTAS_EXTRA
        return 0.5 + 0.3 * min(1.0, self.progreso_gesto() / VUELTAS_LLENO)

    def _paso_gesto(self, dt, ctrl):
        pos = V2(ctrl.pos)
        chico = self.modo_gesto == "chico"
        self.t_gesto += dt
        if pos.distance_to(self._prev) < 1.0:
            self.t_quieto += dt
        else:
            self.t_quieto = 0.0
        self.consejo = "Sigue la luz" if self.t_quieto > QUIETO_CONSEJO else None
        if not self.rastro or pos.distance_to(V2(self.rastro[-1][:2])) > 4:
            self.rastro.append((pos.x, pos.y, self.t_gesto))
        self.rastro = [q for q in self.rastro if self.t_gesto - q[2] < 0.8][-40:]
        # puntos de control en orden: se acierta si el cursor (o su recorrido de este cuadro) pasa cerca
        objetivo = self.puntos_ctrl[self.idx_ctrl]
        if _dist_segmento(objetivo, self._prev, pos) < self.radio:
            self.idx_ctrl += 1
            self.t_lleno = 0.0
            self.sonidos.nota(ESCALA_NOTAS[self.idx_ctrl % len(ESCALA_NOTAS)], 0.12, 0.2)
            if self.idx_ctrl >= len(self.puntos_ctrl):
                self.idx_ctrl = 0
                self.vueltas += 1
                self.sonidos.reproducir("ok")
                if not chico and self.vueltas == VUELTAS_LLENO:
                    self._msg("¡Energía llena! Sigue para más poder", 1.6)
                    self.flash = 0.35
        self._prev = pos
        if chico:
            if self.vueltas >= 1 or self.t_gesto >= self.ventana:
                self._disparar_jugador()
            return
        lleno = self.vueltas >= VUELTAS_LLENO
        if lleno:
            self.t_lleno += dt
        if (self.vueltas >= VUELTAS_LLENO + VUELTAS_EXTRA or self.t_gesto >= self.ventana
                or (lleno and self.t_lleno >= GRACIA_LLENO)):
            self._lanzar_cargado()

    # ---------------------------------------------------------------- final
    def _guardar_vida(self, res):
        """Guarda la vida de tu mascota UNA sola vez: al perder queda en HP_PISO_DERROTA (15%); si no, la que tengas."""
        if self.prestada or self.hp_guardado:
            return
        self.hp_guardado = True
        frac = max(0.0, self.mia["hp"] / self.mia["hp_max"])
        piso = td.HP_PISO_DERROTA if res == "pierde" else 0.01
        self.hp_guardada = td.guardar_hp(self.ctx.perfil, frac, piso=piso)

    def terminar(self, mensaje=""):
        if not self.terminado and not self.hp_guardado and self.final is None:
            self._guardar_vida("escapa")                        # salida por cualquier otro camino: conserva la vida
        super().terminar(mensaje)

    def _finalizar(self, res):
        self.final = res
        self.hp_frac = max(0.0, self.mia["hp"] / self.mia["hp_max"])
        self._guardar_vida(res)
        self.ganado = True if res == "gana" else False if res == "pierde" else None
        if res == "escapa":
            self.puntos = 0
        info = dict(xp=0, monedas=0, items={})
        if not self.prestada and not self.recompensado:
            self.recompensado = True
            perfil = self.ctx.perfil
            info = td.recompensa_batalla(perfil, res, self.dano_hecho, self.hp_frac, rng=self.rng)
            for item, n in info.get("items", {}).items():
                perfil.quitar(item, n)           # recompensa_batalla ya los metio: Resultado los entrega (una sola vez)
                self.dar(item, n)
        self.resultado = dict(estado=res, xp=int(info.get("xp", 0)), monedas=int(info.get("monedas", 0)),
                              items=dict(info.get("items", {})), dano_hecho=int(self.dano_hecho),
                              hp_frac=round(self.hp_frac, 3), hp_guardado=self.hp_guardada, esquivados=self.esquivados,
                              golpes_recibidos=self.golpes_recibidos)
        if res == "gana":
            txt = "¡Ganaste! Muy bien"
        elif res == "pierde":
            txt = "¡Buen intento! Descansa y usa CURAR"
        else:
            txt = "¡Huyeron a salvo!"
        self.poca_vida = res != "pierde" and self.hp_frac < HP_AVISO_CURAR
        if self.poca_vida:
            txt += ".  Usa CURAR para recuperar vida"
        self.mensaje_final = txt
        self.msg, self.t_msg = "", 0.0
        self.proy_jugador = None
        self.proys_r = []
        self._ir("fin")
        if res == "gana":
            self.sonidos.reproducir("premio")
            for _ in range(5):
                explosion(self.particulas, random.uniform(300, 980), random.uniform(120, 300),
                          random.choice([(255, 210, 60), (240, 90, 120), (90, 200, 240), (120, 220, 130)]),
                          n=12, vel_min=100, vel_max=380, vida=1.2, gravedad=400, radio=6)

    # ---------------------------------------------------------------- ciclo
    def paso(self, dt, ctrl):
        self.pos = V2(ctrl.pos)
        self.t_fase += dt
        self.t_msg = max(0.0, self.t_msg - dt)
        self.temblor = max(0.0, self.temblor - dt * 14)
        self.flash = max(0.0, self.flash - dt * 1.6)
        self.particulas = [q for q in self.particulas if q.actualizar(dt)]
        for q in self.fx:
            q["t"] += dt
        self.fx = [q for q in self.fx if q["t"] < q["dur"]]
        self.flot_chicos = [q for q in self.flot_chicos if q.actualizar(dt)]
        k = 1.0 - math.exp(-6.0 * dt)
        for nombre in ("mia", "rival"):
            e = getattr(self, nombre)
            e["hp_vis"] += (e["hp"] - e["hp_vis"]) * k
        f = self.fase
        if f == "intro":
            if self.t_fase > 1.4:
                self._ir_menu()
        elif f == "huida":
            self.t_huida += dt
            if self.t_fase > 1.8:
                self._finalizar("escapa")
        elif f == "fin":
            if self.t_fase > DUR_FIN:
                self.terminar(self.mensaje_final)
        else:
            self._paso_batalla(dt, ctrl)

    def _paso_batalla(self, dt, ctrl):
        self.t_mundo += dt
        self._timers(dt)
        if self.cierre is not None:                          # un HP llego a 0: pausa de celebracion
            if self.anim:
                self._paso_anim(dt)
            else:
                self.t_cierre -= dt
                if self.t_cierre <= 0:
                    self._finalizar(self.cierre)
            return
        self._mover_jugador(dt)
        self._mover_rival(dt)
        f = self.fase
        if f == "menu":
            self._paso_menu(dt, ctrl)
        elif f in ("trazo", "gesto"):
            self._paso_gesto(dt, ctrl)
        elif f == "proyectil":
            if self.proy_jugador:
                self._paso_proy_jugador(dt)
            else:
                self.t_post += dt
                if self.t_post >= T_POST_PROY and self.cierre is None and self.rival["hp"] > 0:
                    self._ir_turno_r()
        elif f == "anim":
            self._paso_anim(dt)
        elif f == "turno_r":
            self._paso_turno_r(dt)
        if self.proys_r and self.cierre is None:
            self._paso_proys_rival(dt)
        if self.cierre is None and (self.rival["hp"] <= 0 or self.mia["hp"] <= 0):
            self.cierre = "gana" if self.rival["hp"] <= 0 else "pierde"
            self.t_cierre = T_CIERRE
            self.proy_jugador = None
            self.proys_r = []

    def _paso_menu(self, dt, ctrl):
        self.botones["ataque"].sub = "Dibuja la forma"
        self.botones["elemental"].activo = self.mia["estamina"] >= 100
        self.botones["elemental"].sub = "Forma grande" if self.botones["elemental"].activo else "Carga tu energía"
        pulsado = None
        for k, b in self.botones.items():
            if b.actualizar(dt, ctrl):
                pulsado = k
        if pulsado == "escapar":
            self.t_huida = 0.0
            self.proy_jugador = None
            self.proys_r = []
            self._ir("huida")
            self._msg("¡Corre!", 1.6)
            self.sonidos.reproducir("fallo")
        elif pulsado == "elemental":
            self._iniciar_gesto()
        elif pulsado == "ataque":
            self._iniciar_trazo()

    # ---------------------------------------------------------------- dibujo
    def _pose(self, quien):
        yo = quien == "j"
        if self.fase == "fin":
            if self.final == "gana":
                return "feliz" if yo else "triste"
            if self.final == "pierde":
                return "triste" if yo else "feliz"
            return "normal"
        if self.cierre:
            if self.cierre == "gana":
                return "feliz" if yo else "triste"
            return "triste" if yo else "feliz"
        a = self.anim
        if a:
            if a["quien"] == quien:
                return "ataca" if a["t"] < 0.5 * a["dur"] else "normal"
            if a["aplicado"] and a["t"] < a["t_imp"] + 0.4:
                return "golpeado"
        if yo:
            if self.t_golp_j > 0:
                return "golpeado"
            if self.t_ataca_j > 0 or (self.fase == "gesto" and self.vueltas >= VUELTAS_LLENO) or \
                    (self.fase == "trazo" and self.idx_ctrl > 0):
                return "ataca"
        else:
            if self.t_golp_r > 0:
                return "golpeado"
            if self.t_ataca_r > 0 or self.r_estado in ("mira", "carga"):
                return "ataca"
        return "normal"

    def _estela(self, p, x, y, ux, uy, tipo, largo=170):
        col = aclarar(arte_tama.COLOR_TIPO[tipo], 0.35)
        for k in range(1, 9):
            f = 1 - k / 9
            arte_tama.glow(p, x - ux * largo * k / 8, y - uy * largo * k / 8, 5 + 12 * f, col, int(120 * f))

    def _dibujar_proyectil(self, p, at, x, y, ux, uy):
        self._estela(p, x, y, ux, uy, at["tipo"])
        arte_tama.dibujar_ataque_basico(p, at["tipo"], at["etapa"], x - ux * 260, y - uy * 260, x, y, 1.0, self.t)

    def _dibujar_mira(self, p):
        o = V2(RX - 70, self.y_rival)
        fin = V2(PX, self.mira_y)
        bloq = self.mira_bloqueada
        col = (255, 55, 45) if bloq else (255, 200, 60)
        d = fin - o
        L = d.length()
        u = d / L if L else V2(-1, 0)
        paso, seg = 34, 20
        n = int(L // paso)
        w = 8 if bloq else 5
        for i in range(n + 1):
            a = o + u * (i * paso)
            b = o + u * min(L, i * paso + (paso if bloq else seg))
            pygame.draw.line(p, (40, 20, 20), a, b, w + 4)
            pygame.draw.line(p, col, a, b, w)
        pul = 1 + 0.08 * math.sin(self.t * (18 if bloq else 8))
        r = int((self.radio_hit_j() + 34) * pul)
        pygame.draw.circle(p, (40, 20, 20), fin, r + 2, 11)
        pygame.draw.circle(p, col, fin, r, 7)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a = (fin.x + dx * (r - 14), fin.y + dy * (r - 14))
            b = (fin.x + dx * (r + 26), fin.y + dy * (r + 26))
            pygame.draw.line(p, (40, 20, 20), a, b, 11)
            pygame.draw.line(p, col, a, b, 7)
        if bloq:
            arte_tama.glow(p, fin.x, fin.y, r + 20, (255, 60, 50), 90)

    def _dibujar_escena(self, p):
        t = self.t
        arte_tama.dibujar_fondo_arena(p, self.rival["tipo"], t)
        m, r = self.mia, self.rival
        mx = PX
        if self.fase == "huida":
            u = max(0.0, self.t_huida - 0.3)
            mx -= u * u * 260
        rx = RX
        if self.fase == "intro":
            u = max(0.0, 1 - self.t_fase / 0.6)
            mx -= 420 * u * u
            rx += 420 * u * u
        my, ry = self.y_jugador, self.y_rival
        if self.fase == "gesto":
            fc = min(1.0, self.progreso_gesto() / VUELTAS_LLENO)
            arte_tama.dibujar_carga(p, m["tipo"], m["etapa"], mx, my, fc, t)
        if self.r_estado == "carga" and self.fase == "turno_r":
            arte_tama.dibujar_carga(p, r["tipo"], r["etapa"], rx, ry, min(1.0, self.r_t / T_CARGA_ELEM), t)
        if not (self.fase == "huida" and self.t_huida > 1.2):
            arte_tama.dibujar_mascota(p, m["especie"], m["etapa"], mx, my, self.escala_j, t, self._pose("j"), 1)
        arte_tama.dibujar_mascota(p, r["especie"], r["etapa"], rx, ry, self.escala_r, t + 1.3, self._pose("r"), -1)
        if self.r_estado == "mira" and self.fase == "turno_r":
            self._dibujar_mira(p)
        pj = self.proy_jugador
        if pj:
            self._dibujar_proyectil(p, m, pj["x"], pj["y"], pj["ux"], pj["uy"])
        for pr in self.proys_r:
            self._dibujar_proyectil(p, r, pr["x"], pr["y"], pr["ux"], pr["uy"])
        for q in self.fx:
            arte_tama.dibujar_impacto(p, q["tipo"], q["etapa"], q["x"], q["y"], q["t"] / q["dur"], t)
        a = self.anim
        if a:
            f = a["t"] / a["dur"]
            at = a["atac"]
            ax, ay = (mx, my) if a["quien"] == "j" else (rx, ry)
            dx, dy = (rx, ry) if a["quien"] == "j" else (mx, my)
            sentido = 1 if a["quien"] == "j" else -1
            arte_tama.dibujar_ataque_cargado(p, at["tipo"], at["etapa"], ax + sentido * 90, ay - 10, dx, dy, f, t)
            if f >= 0.42:
                arte_tama.dibujar_impacto(p, at["tipo"], at["etapa"], dx, dy, min(1.0, (f - 0.42) / 0.5), t)
        if self.fase == "gesto":
            p.blit(_velo((ANCHO, ALTO), (15, 20, 50, 70)), (0, 0))
            self._dibujar_gesto(p)
        elif self.fase == "trazo":
            self._dibujar_gesto(p)
        for q in self.particulas:
            q.dibujar(p)

    def _dibujar_gesto(self, p):
        t = self.t
        rc = self.rect_gesto
        col = arte_tama.COLOR_TIPO[self.tipo_gesto]
        # velo suave para que la guia se vea bien
        grande = rc.inflate(60, 50)
        p.blit(_velo(grande.size, (10, 15, 40, 42), 40), grande.topleft)
        surf, ox, oy, dens = _guia_cache(self.tipo_gesto, rc, self.idx_ctrl)
        p.blit(surf, (ox, oy))
        s0 = dens[0]
        pygame.draw.circle(p, (255, 255, 255), (int(s0[0]), int(s0[1])), int(12.5 * (1 + 0.15 * math.sin(t * 5))), 3)
        # luz viajera: muestra el sentido (antes del primer punto) o marca hasta donde llevas
        prog = self.idx_ctrl / len(self.puntos_ctrl)
        if prog <= 0:
            i = int(((t * 0.32) % 1.0) * (len(dens) - 1))
            arte_tama.glow(p, dens[i][0], dens[i][1], 26, aclarar(col, 0.4), 230)
            arte_tama.glow(p, dens[i][0], dens[i][1], 10, (255, 255, 255), 255)
        else:
            i = max(0, min(len(dens) - 1, int(prog * (len(dens) - 1))))
            arte_tama.glow(p, dens[i][0], dens[i][1], 30, aclarar(col, 0.4), 240)
            arte_tama.glow(p, dens[i][0], dens[i][1], 11, (255, 255, 255), 255)
        # siguiente punto: anillo que late
        ox2, oy2 = self.puntos_ctrl[self.idx_ctrl]
        rr = 24 + 5 * math.sin(t * 8)
        pygame.draw.circle(p, (255, 255, 255), (int(ox2), int(oy2)), int(rr), 4)
        # estela del cursor
        for (x, y, tt) in self.rastro:
            k = 1 - (self.t_gesto - tt) / 0.8
            if k > 0:
                pygame.draw.circle(p, aclarar(col, 0.5), (int(x), int(y)), max(2, int(11 * k)))
        pygame.draw.circle(p, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), 14)
        pygame.draw.circle(p, col, (int(self.pos.x), int(self.pos.y)), 14, 4)

    def _panel_mascota(self, p, e, x, lado):
        f = self.f
        w, h, y = 420, 130, 14
        _panel(p, (x, y, w, h), (255, 255, 255), alfa=215, radio=20)
        col = arte_tama.COLOR_TIPO[e["tipo"]]
        pygame.draw.circle(p, oscurecer(col, 0.35), (x + 40, y + 36), 25)
        arte_tama.dibujar_icono_tipo(p, e["tipo"], x + 40, y + 36, 22)
        _escribir(p, f.normal, e["nombre"], x + 76, y + 26, (40, 50, 90), "izq", contorno=None)
        _escribir(p, f.chica, f"{td.ETAPAS[e['etapa']]}  ·  {arte_tama.NOMBRE_TIPO[e['tipo']]}", x + 76, y + 52,
                  (90, 100, 140), "izq", contorno=None)
        frac = e["hp_vis"] / e["hp_max"]
        rect = pygame.Rect(x + 16, y + 68, w - 32, 26)
        barra(p, rect, frac, color=color_hp(frac), color_fondo=(70, 76, 100))
        if frac > 0.05:
            pygame.draw.rect(p, aclarar(color_hp(frac), 0.55), (rect.x + 10, rect.y + 4, int((rect.w - 20) * frac), 4),
                             border_radius=2)
        _escribir(p, f.chica, f"Vida  {int(math.ceil(e['hp']))}/{int(e['hp_max'])}", rect.centerx, rect.centery,
                  (255, 255, 255), grosor=1)
        er = pygame.Rect(x + 16, y + 99, w - 32, 22)
        llena = e["estamina"] >= 100
        if llena:
            pulso = 0.5 + 0.5 * math.sin(self.t * 7)
            halo = _velo((er.w + 12, er.h + 12), (255, 215, 80, 255), 14)
            halo.set_alpha(int(70 + 80 * pulso))
            p.blit(halo, (er.x - 6, er.y - 6))
            barra(p, er, 1.0, color=_mezcla((255, 200, 60), (255, 240, 150), pulso), color_fondo=(70, 76, 100))
            _escribir(p, f.chica, "¡ENERGÍA LLENA!", er.centerx, er.centery, (255, 255, 255), grosor=1)
        else:
            barra(p, er, e["estamina"] / 100, color=(80, 165, 245), color_fondo=(70, 76, 100))
            _escribir(p, f.chica, "Energía", er.centerx, er.centery, (255, 255, 255), grosor=1)

    def _banner(self, p, texto, y=96, col=(40, 50, 90), ancho=None):
        fuente = self.f.normal
        w = ancho or max(300, fuente.size(texto)[0] + 60)
        _panel(p, (ANCHO / 2 - w / 2, y, w, 58), (255, 255, 255), alfa=230, radio=26)
        _escribir(p, fuente, texto, ANCHO / 2, y + 29, col, contorno=None)

    def _hud(self, p):
        f = self.f
        self._panel_mascota(p, self.mia, 16, 0)
        self._panel_mascota(p, self.rival, ANCHO - 436, 1)
        if self.msg and self.t_msg > 0 and self.fase != "fin":
            self._banner(p, self.msg, 18)
        fase = self.fase
        if fase == "menu":
            for k, b in self.botones.items():
                b.dibujar(p, f.grande, f.normal, f.chica, self.t)
            if self.ayuda and self.t_fase < 16:
                _panel(p, (ANCHO / 2 - 250, 200, 500, 250), (255, 255, 255), alfa=225, radio=26)
                for i, linea in enumerate(("En tu turno sigue la forma", "con el cursor.",
                                           "Cuando ataque tu rival,", "mueve el cursor arriba o abajo",
                                           "para esquivar.")):
                    _escribir(p, f.normal, linea, ANCHO / 2, 235 + i * 44, (40, 50, 90), contorno=None)
        elif fase == "turno_r":
            if self.r_estado == "aviso":
                _escribir(p, f.grande, f"Le toca a {self.rival['nombre']}", ANCHO / 2, 250, (255, 240, 120),
                          contorno=(60, 30, 20), grosor=4)
            if self.r_estado in ("aviso", "mira", "vuelo", "fin_turno"):
                self._banner(p, "Mueve el cursor arriba o abajo para esquivar", 606)
            if self.r_estado == "carga":
                _escribir(p, f.grande, "¡Ataque elemental!", ANCHO / 2, 250, (255, 235, 90),
                          contorno=(150, 20, 20), grosor=4)
                self._banner(p, "¡Prepárate!", 606, ancho=320)
        elif fase == "huida":
            self._banner(p, "¡Corre!", 600, ancho=260)
        elif fase == "intro":
            self._banner(p, f"{self.mia['nombre']}  contra  {self.rival['nombre']}", 600, ancho=620)
        elif fase in ("trazo", "gesto"):
            self._hud_gesto(p)
        elif fase == "fin":
            self._hud_fin(p)

    def _hud_gesto(self, p):
        f = self.f
        _panel(p, (260, 560, 760, 140), (255, 255, 255), alfa=225, radio=26)
        col = arte_tama.COLOR_TIPO[self.tipo_gesto]
        rem = max(0.0, 1 - self.t_gesto / self.ventana)
        barra(p, (300, 668, 680, 18), rem, color=(255, 190, 60) if rem > 0.25 else (240, 110, 90),
              color_fondo=(190, 195, 215))
        if self.modo_gesto == "chico":
            _escribir(p, f.normal, self.consejo or NOMBRE_GESTO[self.tipo_gesto], ANCHO / 2, 590, (40, 50, 90),
                      contorno=None)
            barra(p, (300, 622, 680, 22), self.progreso_gesto(), color=col, color_fondo=(190, 195, 215))
            return
        lleno = self.vueltas >= VUELTAS_LLENO
        txt = ("¡Energía llena! Sigue para más poder" if lleno
               else f"Sigue la luz  ·  vuelta {self.vueltas + 1} de {VUELTAS_LLENO}")
        _escribir(p, f.normal, txt, ANCHO / 2, 590, (40, 50, 90), contorno=None)
        for i in range(VUELTAS_LLENO):
            hecho = i < self.vueltas
            estrella(p, ANCHO / 2 - 60 + i * 60, 633, 20, (255, 210, 60) if hecho else (205, 210, 225),
                     (160, 110, 20) if hecho else (150, 155, 175))
        if self.consejo:
            self._banner(p, self.consejo, 506, ancho=300)

    def _hud_fin(self, p):
        f = self.f
        r = self.resultado
        res = self.final
        _panel(p, (ANCHO / 2 - 380, 535, 760, 170), (255, 255, 255), alfa=238, radio=30)
        if res == "gana":
            _escribir(p, f.grande, "¡GANASTE!", ANCHO / 2, 574, (255, 205, 60), contorno=(150, 90, 20), grosor=3)
            n = self.estrellas()
            for i in range(3):
                estrella(p, ANCHO / 2 - 300 + i * 56, 640, 24, (255, 210, 60) if i < n else (205, 210, 225),
                         (160, 110, 20) if i < n else (150, 155, 175))
            _escribir(p, f.normal, f"+{r['xp']} XP    +{r['monedas']} monedas", ANCHO / 2 + 90, 636, (40, 50, 90),
                      contorno=None)
            if r["items"]:
                _escribir(p, f.chica, "¡Encontraste un Fragmento estelar!", ANCHO / 2, 670 if self.poca_vida else 682,
                          (110, 80, 200), contorno=None)
            if self.poca_vida:
                _escribir(p, f.chica, "Usa CURAR para recuperar vida", ANCHO / 2, 692, (60, 120, 80), contorno=None)
        elif res == "pierde":
            _escribir(p, f.grande, "¡Buen intento!", ANCHO / 2, 574, (90, 120, 200), contorno=(30, 40, 90), grosor=3)
            _escribir(p, f.normal, "Descansa y usa CURAR", ANCHO / 2, 628, (40, 50, 90), contorno=None)
            _escribir(p, f.chica, f"+{r['xp']} XP por entrenar", ANCHO / 2, 676, (70, 110, 70), contorno=None)
        else:
            _escribir(p, f.grande, "¡Huyeron a salvo!", ANCHO / 2, 574, (90, 140, 215), contorno=(30, 40, 90), grosor=3)
            _escribir(p, f.normal, "Sin premio y sin castigo", ANCHO / 2, 628 if self.poca_vida else 636, (40, 50, 90),
                      contorno=None)
            if self.poca_vida:
                _escribir(p, f.chica, "Usa CURAR para recuperar vida", ANCHO / 2, 676, (60, 120, 80), contorno=None)

    def dibujar(self, p):
        if self.temblor > 0.2:
            lienzo = self._lienzo
            self._dibujar_escena(lienzo)
            ox = math.sin(self.t * 71) * self.temblor
            oy = math.cos(self.t * 59) * self.temblor * 0.7
            ox, oy = int(ox), int(oy)
            p.blit(lienzo, (ox, oy))
            if ox > 0:                                       # solo las franjas que quedan al descubierto
                p.blit(lienzo, (0, 0), (0, 0, ox, ALTO))
            elif ox < 0:
                p.blit(lienzo, (ANCHO + ox, 0), (ANCHO + ox, 0, -ox, ALTO))
            if oy > 0:
                p.blit(lienzo, (0, 0), (0, 0, ANCHO, oy))
            elif oy < 0:
                p.blit(lienzo, (0, ALTO + oy), (0, ALTO + oy, ANCHO, -oy))
        else:
            self._dibujar_escena(p)
        for q in self.flotantes:
            q.dibujar(p, self.f.grande)
        for q in self.flot_chicos:
            q.dibujar(p, self.f.normal)
        self._hud(p)
        if self.flash > 0:
            if self._blanco is None:
                self._blanco = pygame.Surface((ANCHO, ALTO))
                self._blanco.fill((255, 255, 255))
            self._blanco.set_alpha(int(255 * min(1.0, self.flash)))
            p.blit(self._blanco, (0, 0))

    def dibujar_juego(self, pantalla):
        self.dibujar(pantalla)

    def dibujar_hud(self, pantalla):
        pass
