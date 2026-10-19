"""Dibujos y piezas auxiliares de la excavacion de Fosiles (gemas, bichos, capas de terreno, botones).

Todo se pre-renderiza una vez (sprites) para que el juego vaya fluido.
"""

import math
import random

import pygame

import arte_paleo
import fosiles_datos as fd
from ajustes import DWELL_SEG
from nucleo import Boton, aclarar, barra, escribir, estrella, oscurecer, V2

CEL = 66                                       # lado de cada celda en px
COLS, FILAS = 12, 7
GX0, GY0 = 30, 140                             # esquina del bloque de tierra en pantalla
GW, GH = COLS * CEL, FILAS * CEL

NOMBRES_CAPA = {"polvo": "Polvo", "barro": "Barro", "rocas": "Rocas", "cristales": "Cristales"}
COLOR_CAPA = {"polvo": (232, 200, 140), "barro": (120, 84, 54), "rocas": (150, 150, 162),
              "cristales": (130, 220, 250)}
# herramientas de la barra, en el orden de las capas
HERRAMIENTAS = ("brocha", "cincel_pequeno", "martillo", "cincel")
COLOR_HERR = {"brocha": (214, 150, 70), "cincel_pequeno": (96, 176, 156), "martillo": (206, 96, 84),
              "cincel": (84, 132, 208)}
BARRA = pygame.Rect(24, 612, 828, 78)          # zona de la barra de herramientas


def celda_rect(c, r):
    return pygame.Rect(GX0 + c * CEL, GY0 + r * CEL, CEL, CEL)


def articulo(tipo):
    """(articulo, 'o'/'a') para frases: una brocha, un martillo."""
    return ("una", "a") if tipo == "brocha" else ("un", "o")


def texto_necesita(tipo, est):
    art, o = articulo(tipo)
    nombre = fd.NOMBRES_HERR[tipo].lower()
    estr = "estrella" if est == 1 else "estrellas"
    return f"Necesitas {art} {nombre} de {est} {estr}: ¡fabrícal{o} en el Taller!"


# ====================================================================== gemas, bichos y vuelos
_glows = {}


def _glow(r, color=(170, 130, 255)):
    clave = (r, color)
    if clave not in _glows:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for k in range(10, 0, -1):
            f = k / 10
            pygame.draw.circle(s, (*color, int(90 * (1 - f) ** 1.5)), (r, r), max(1, int(r * f)))
        _glows[clave] = s
    return _glows[clave]


def dibujar_gema(p, x, y, r, t=0.0, brillo=True):
    """Gema de polvo especial (cristal violeta con destellos)."""
    if brillo:
        g = _glow(int(r * 2.2))
        g.set_alpha(int(150 + 90 * math.sin(t * 4 + x * 0.05)))
        p.blit(g, g.get_rect(center=(int(x), int(y))))
    pts = [(x, y - r), (x + r * 0.82, y - r * 0.36), (x + r * 0.56, y + r * 0.82), (x, y + r),
           (x - r * 0.56, y + r * 0.82), (x - r * 0.82, y - r * 0.36)]
    pygame.draw.polygon(p, (126, 78, 220), pts)
    pygame.draw.polygon(p, (176, 132, 255), [pts[0], pts[1], (x, y + r * 0.1), (x - r * 0.0, y - r * 0.1), pts[5]])
    pygame.draw.polygon(p, (96, 56, 190), [(x, y + r * 0.1), pts[1], pts[2], pts[3]])
    pygame.draw.polygon(p, (210, 235, 255), [(x - r * 0.45, y - r * 0.3), (x - r * 0.12, y - r * 0.62),
                                             (x - r * 0.05, y - r * 0.2)])
    pygame.draw.polygon(p, (60, 30, 110), pts, max(2, int(r / 7)))
    k = 0.5 + 0.5 * math.sin(t * 5 + x)
    if k > 0.2:
        a = r * 0.7 * k
        cx, cy = x + r * 0.55, y - r * 0.55
        pygame.draw.line(p, (255, 255, 255), (cx - a, cy), (cx + a, cy), 2)
        pygame.draw.line(p, (255, 255, 255), (cx, cy - a), (cx, cy + a), 2)


def dibujar_gusano(p, x, y, t, esc=1.0):
    for k in range(5):
        px = x - k * 9 * esc
        py = y + math.sin(t * 9 - k * 1.1) * 4 * esc
        pygame.draw.circle(p, (150, 70, 80), (int(px), int(py)), int((9 - k * 0.5) * esc) + 2)
        pygame.draw.circle(p, (246, 160, 170), (int(px), int(py)), int((9 - k * 0.5) * esc))
    pygame.draw.circle(p, (255, 255, 255), (int(x + 3 * esc), int(y - 3 * esc)), max(2, int(3 * esc)))
    pygame.draw.circle(p, (30, 20, 30), (int(x + 4 * esc), int(y - 3 * esc)), max(1, int(1.5 * esc)))


def dibujar_escarabajo(p, x, y, t, ang):
    """Escarabajo mirando hacia ang (si es 0 mira a la derecha)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def R(dx, dy):
        return (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    for k in range(3):
        mov = math.sin(t * 22 + k * 2) * 4
        for lado in (-1, 1):
            pygame.draw.line(p, (30, 22, 20), R(-6 + k * 7, lado * 6), R(-9 + k * 7 + mov, lado * 15), 3)
    for lado in (-1, 1):
        pygame.draw.line(p, (30, 22, 20), R(14, lado * 3), R(25, lado * 9 + math.sin(t * 9) * 2), 2)
    cuerpo = []
    for i in range(16):
        a = 2 * math.pi * i / 16
        cuerpo.append(R(2 + 19 * math.cos(a), 14 * math.sin(a)))
    pygame.draw.polygon(p, (22, 100, 84), cuerpo)
    pygame.draw.polygon(p, (16, 60, 50), cuerpo, 2)
    pygame.draw.circle(p, (80, 200, 160), R(-3, -5), 5)
    pygame.draw.circle(p, (30, 24, 22), R(18, 0), 8)
    pygame.draw.circle(p, (255, 255, 255), R(21, -3), 3)
    pygame.draw.line(p, (16, 60, 50), R(-16, 0), R(12, 0), 2)


class Bicho:
    def __init__(self, c, r, clase):
        self.c, self.r, self.clase = c, r, clase
        self.pos = V2(GX0 + c * CEL + CEL / 2, GY0 + r * CEL + CEL / 2)
        self.huyendo = False
        self.t = random.uniform(0, 5)
        a = random.choice((0.0, math.pi, math.pi / 2, -math.pi / 2, 0.6, 2.5))
        self.dir = V2(math.cos(a), math.sin(a))
        self.vida = 0.0

    def actualizar(self, dt):
        self.t += dt
        if self.huyendo:
            self.vida += dt
            self.pos += self.dir * (170 if self.clase == 0 else 80) * dt
        return not (self.huyendo and self.vida > 2.6)

    def dibujar(self, p):
        if self.clase == 0:
            dibujar_escarabajo(p, self.pos.x, self.pos.y, self.t,
                               math.atan2(self.dir.y, self.dir.x) if self.huyendo else 0.0)
        else:
            dibujar_gusano(p, self.pos.x, self.pos.y, self.t)


class Vuelo:
    """Pieza que vuela desde donde se hallo hasta el panel."""

    def __init__(self, dibujo, x0, y0, x1, y1, dur=0.95, al_llegar=None, esc=(1.0, 0.55)):
        self.dibujo, self.a, self.b = dibujo, V2(x0, y0), V2(x1, y1)
        self.dur, self.t, self.al_llegar, self.esc = dur, 0.0, al_llegar, esc

    def actualizar(self, dt):
        self.t += dt
        return self.t < self.dur

    def pos(self):
        u = min(1.0, self.t / self.dur)
        e = u * u * (3 - 2 * u)
        q = self.a.lerp(self.b, e)
        q.y -= 110 * math.sin(math.pi * e)
        return q, self.esc[0] + (self.esc[1] - self.esc[0]) * e


class TextoGrande:
    """Texto flotante que dura mas y se lee mejor (nombre del hueso hallado)."""

    def __init__(self, texto, x, y, color=(255, 255, 255)):
        self.texto, self.x, self.y, self.t, self.vida, self.color = texto, x, y, 0.0, 1.9, color

    def actualizar(self, dt):
        self.t += dt
        return self.t < self.vida

    def dibujar(self, pantalla, fuente):
        escribir(pantalla, fuente, self.texto, min(max(self.x, 150), 700), self.y - 20 * (self.t / self.vida),
                 color=self.color)


# ====================================================================== piezas escondidas
def sup_senuelo(w, h, semilla):
    """Piedra con forma de hueso (senuelo): mas gris y sin brillo."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    rnd = random.Random(semilla)
    cx, cy = w / 2, h / 2
    ang = rnd.choice((-0.5, 0.0, 0.4))
    largo = (w - 34) / 2 if w > CEL else 16
    ax, ay = cx - math.cos(ang) * largo, cy - math.sin(ang) * largo
    bx, by = cx + math.cos(ang) * largo, cy + math.sin(ang) * largo
    gris, claro, borde = (168, 164, 170), (196, 192, 198), (82, 78, 88)
    pygame.draw.line(s, borde, (ax, ay), (bx, by), 20)
    pygame.draw.line(s, gris, (ax, ay), (bx, by), 14)
    for qx, qy in ((ax, ay), (bx, by)):
        for dx, dy in ((-6, -6), (6, 6)):
            pygame.draw.circle(s, borde, (int(qx + dx), int(qy + dy)), 12)
        for dx, dy in ((-6, -6), (6, 6)):
            pygame.draw.circle(s, gris, (int(qx + dx), int(qy + dy)), 10)
    pygame.draw.line(s, claro, (ax, ay - 3), (bx, by - 3), 3)
    return s


_cache_caja = {}


def caja_dibujo(clave, dibujar):
    """Mide el rectangulo que ocupa un dibujo (se dibuja en el centro de un lienzo de 360x360)."""
    if clave not in _cache_caja:
        s = pygame.Surface((360, 360), pygame.SRCALPHA)
        dibujar(s, 180, 180, 1.0)
        r = s.get_bounding_rect()
        if r.w < 4 or r.h < 4:
            r = pygame.Rect(150, 160, 60, 40)
        _cache_caja[clave] = r
    return _cache_caja[clave]


def preparar_pieza(clave, dibujar, max_celdas=2):
    """Devuelve (cols, filas, escala, superficie) de una pieza (hueso o reliquia) que ocupa celdas enteras.
    `dibujar(s, x, y, esc)` pinta la pieza centrada en (x, y)."""
    caja = caja_dibujo(clave, dibujar)
    tope = max_celdas * CEL - 10
    esc = min(1.0, tope / max(caja.w, caja.h))
    w, h = caja.w * esc, caja.h * esc
    cols = 1 if w <= CEL - 6 else max_celdas
    filas = 1 if h <= CEL - 6 else max_celdas
    sup = pygame.Surface((cols * CEL, filas * CEL), pygame.SRCALPHA)
    dx = (caja.centerx - 180) * esc
    dy = (caja.centery - 180) * esc
    dibujar(sup, cols * CEL / 2 - dx, filas * CEL / 2 - dy, esc)
    return cols, filas, esc, sup


# ====================================================================== capas de terreno
_cub_base = []


def crear_cubierta():
    """Capa de polvo (arena suelta), una baldosa por celda. Se devuelve una copia."""
    if not _cub_base:
        s = pygame.Surface((GW, GH), pygame.SRCALPHA)
        rnd = random.Random(2)
        for c in range(COLS):
            for r in range(FILAS):
                v = rnd.randint(-9, 9)
                col = (226 + v, 194 + v, 136 + v)
                rect = pygame.Rect(c * CEL + 1, r * CEL + 1, CEL - 2, CEL - 2)
                pygame.draw.rect(s, (190 + v, 154 + v, 100 + v), rect.move(0, 2), border_radius=9)
                pygame.draw.rect(s, col, rect.inflate(0, -2).move(0, -1), border_radius=9)
                pygame.draw.line(s, (244, 222, 172), (rect.x + 8, rect.y + 3), (rect.right - 8, rect.y + 3), 2)
                for _ in range(7):
                    x, y = rnd.randint(rect.x + 6, rect.right - 6), rnd.randint(rect.y + 6, rect.bottom - 6)
                    pygame.draw.circle(s, (206 + v, 172 + v, 118 + v), (x, y), rnd.randint(1, 3))
        _cub_base.append(s)
    return _cub_base[0].copy()


_barros = []


def sup_barro(i):
    """Baldosa de barro humedo (4 variantes)."""
    if not _barros:
        for k in range(4):
            rnd = random.Random(40 + k)
            s = pygame.Surface((CEL, CEL), pygame.SRCALPHA)
            r = pygame.Rect(1, 1, CEL - 2, CEL - 2)
            pygame.draw.rect(s, (64, 44, 30), r.move(0, 2), border_radius=14)
            pygame.draw.rect(s, (104, 72, 46), r, border_radius=14)
            pygame.draw.rect(s, (126, 90, 58), r.inflate(-12, -14).move(0, -3), border_radius=12)
            for _ in range(5):                                       # charcos brillantes
                x, y = rnd.randint(10, CEL - 18), rnd.randint(10, CEL - 14)
                pygame.draw.ellipse(s, (158, 118, 80), (x, y, rnd.randint(8, 16), rnd.randint(4, 7)))
                pygame.draw.ellipse(s, (196, 156, 112), (x + 2, y + 1, 5, 2))
            for _ in range(4):                                       # piedritas
                x, y = rnd.randint(8, CEL - 8), rnd.randint(8, CEL - 8)
                pygame.draw.circle(s, (80, 58, 40), (x, y), rnd.randint(2, 4))
            pygame.draw.rect(s, (50, 34, 24), r, 3, border_radius=14)
            _barros.append(s)
    return _barros[i % 4]


def _roca_pts(semilla, radio):
    rnd = random.Random(semilla)
    pts = []
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.15, 0.15)
        r = radio * rnd.uniform(0.82, 1.0)
        pts.append((r * math.cos(a), r * math.sin(a) * 0.86))
    return pts


class Bloque:
    """Roca o cristal que cubre una celda y aguanta varios golpes."""

    def __init__(self, c, r, tipo, hp, semilla):
        self.c, self.r, self.tipo = c, r, tipo
        self.hp = self.hpmax = float(hp)
        self.centro = V2(GX0 + c * CEL + CEL / 2, GY0 + r * CEL + CEL / 2)
        self.sacudida = 0.0
        self.semilla = semilla
        self.bloqueado = False                 # el jugador no tiene herramienta suficiente
        self.sup = self._crear_sup()
        self.sombra = None

    def distancia(self, pos):
        """Distancia del punto a la celda del bloque (0 si esta dentro)."""
        dx = max(abs(pos.x - self.centro.x) - CEL / 2, 0.0)
        dy = max(abs(pos.y - self.centro.y) - CEL / 2, 0.0)
        return math.hypot(dx, dy)

    def _crear_sup(self):
        s = pygame.Surface((CEL + 12, CEL + 12), pygame.SRCALPHA)
        cx = cy = (CEL + 12) / 2
        if self.tipo == "roca":
            radio = 27 if self.hpmax <= 1 else 29 if self.hpmax <= 2 else 31
            col = ((150, 150, 160), (128, 126, 142), (104, 100, 124))[min(2, int(self.hpmax) - 1)]
            pts = [(cx + a, cy + b) for a, b in _roca_pts(self.semilla, radio)]
            pygame.draw.polygon(s, (50, 44, 56), [(a, b + 5) for a, b in pts])
            pygame.draw.polygon(s, col, pts)
            pygame.draw.polygon(s, aclarar(col, 0.3),
                                [(cx + (a - cx) * 0.62 - 5, cy + (b - cy) * 0.6 - 6) for a, b in pts])
            pygame.draw.polygon(s, (50, 44, 56), pts, 3)
            pygame.draw.line(s, (90, 88, 104), (cx - 14, cy - 8), (cx - 4, cy + 4), 3)
        else:
            rnd = random.Random(self.semilla)
            base = rnd.choice(((110, 214, 250), (176, 136, 255), (255, 142, 206)))
            pygame.draw.ellipse(s, oscurecer(base, 0.55), (cx - 28, cy + 12, 56, 18))
            prismas = [(-16, 6, 15, 36, -0.22), (14, 8, 14, 30, 0.25), (0, 12, 19, 50, 0.0),
                       (-4, 10, 11, 26, 0.45)]
            for dx, dy, ancho, alto, ang in prismas:
                x0, y0 = cx + dx, cy + dy                       # base del prisma
                top = (x0 + math.sin(ang) * alto, y0 - math.cos(ang) * alto)
                izq, der = (x0 - ancho / 2, y0), (x0 + ancho / 2, y0)
                cuello = (top[0] - ancho * 0.32, top[1] + alto * 0.2), (top[0] + ancho * 0.32, top[1] + alto * 0.2)
                cara_izq = [izq, cuello[0], top, (x0, y0)]
                cara_der = [(x0, y0), top, cuello[1], der]
                pygame.draw.polygon(s, aclarar(base, 0.35), cara_izq)
                pygame.draw.polygon(s, oscurecer(base, 0.12), cara_der)
                pygame.draw.polygon(s, oscurecer(base, 0.5), [izq, cuello[0], top, cuello[1], der], 2)
                pygame.draw.line(s, (255, 255, 255), (x0 - ancho * 0.22, y0 - alto * 0.25),
                                 (top[0] - ancho * 0.28, top[1] + alto * 0.35), 2)
        return s

    def dibujar(self, p, t=0.0):
        cx, cy = self.centro
        if self.sacudida > 0:
            cx += math.sin(self.sacudida * 70) * 4 * self.sacudida / 0.25
        if self.tipo == "cristal":
            g = _glow(46, (150, 230, 255))
            g.set_alpha(int(120 + 80 * math.sin(t * 3 + self.c * 1.3 + self.r)))
            p.blit(g, g.get_rect(center=(int(cx), int(cy))))
        p.blit(self.sup, self.sup.get_rect(center=(int(cx), int(cy))))
        dano = 1.0 - max(0.0, self.hp) / self.hpmax
        if dano > 0.02:                                  # grietas segun el dano recibido
            col = (40, 34, 46) if self.tipo == "roca" else (255, 255, 255)
            pygame.draw.lines(p, col, False,
                              [(cx - 6, cy - 22), (cx + 2, cy - 8), (cx - 7, cy + 2), (cx + 6, cy + 14)], 3)
            if dano > 0.45:
                pygame.draw.lines(p, col, False, [(cx + 16, cy - 14), (cx + 8, cy - 2), (cx + 14, cy + 10)], 3)
        if self.tipo == "cristal":                       # destello que da vueltas
            k = 0.5 + 0.5 * math.sin(t * 5 + self.c * 2 + self.r * 3)
            if k > 0.4:
                a = 9 * k
                sx, sy = cx + 14, cy - 18
                pygame.draw.line(p, (255, 255, 255), (sx - a, sy), (sx + a, sy), 2)
                pygame.draw.line(p, (255, 255, 255), (sx, sy - a), (sx, sy + a), 2)
        n = int(math.ceil(self.hp - 0.01))               # puntos de dureza: cuantos golpes aguanta
        for k in range(min(n, 5)):
            px = int(cx - (min(n, 5) - 1) * 6 + k * 12)
            pygame.draw.circle(p, (255, 236, 150), (px, int(cy + 25)), 4)
            pygame.draw.circle(p, (50, 44, 56), (px, int(cy + 25)), 4, 1)
        if self.bloqueado:                               # candado: hace falta una herramienta mejor
            lx, ly = int(cx + 20), int(cy - 22)
            pygame.draw.circle(p, (60, 40, 40), (lx, ly), 13)
            pygame.draw.circle(p, (255, 200, 90), (lx, ly), 11)
            pygame.draw.rect(p, (110, 70, 30), (lx - 6, ly - 1, 12, 9), border_radius=2)
            pygame.draw.arc(p, (110, 70, 30), (lx - 5, ly - 9, 10, 12), 0, math.pi, 2)


# ====================================================================== barra de herramientas
_fuentes = {}
_textos = {}


def escribir_c(p, fnt, texto, x, y, color=(255, 255, 255), ancla="centro", contorno=(30, 30, 50), grosor=2):
    """Como nucleo.escribir pero guarda el texto ya dibujado (con su contorno): mucho mas rapido."""
    clave = (id(fnt), texto, color, contorno, grosor)
    sup = _textos.get(clave)
    if sup is None:
        if len(_textos) > 600:
            _textos.clear()
        base = fnt.render(str(texto), True, color)
        w, h = base.get_size()
        sup = pygame.Surface((w + 2 * grosor, h + 2 * grosor), pygame.SRCALPHA)
        if contorno:
            sombra = fnt.render(str(texto), True, contorno)
            for dx in range(-grosor, grosor + 1):
                for dy in range(-grosor, grosor + 1):
                    if dx or dy:
                        sup.blit(sombra, (grosor + dx, grosor + dy))
        sup.blit(base, (grosor, grosor))
        _textos[clave] = sup
    w, h = sup.get_size()
    if ancla == "centro":
        px, py = x - w / 2, y - h / 2
    elif ancla == "izq":
        px, py = x - grosor, y - h / 2
    else:
        px, py = x - w + grosor, y - h / 2
    p.blit(sup, (px, py))
    return pygame.Rect(px, py, w, h)


def fuente(n, negrita=True):
    clave = (n, negrita)
    if clave not in _fuentes:
        _fuentes[clave] = pygame.font.SysFont("arial", n, bold=negrita)
    return _fuentes[clave]


_iconos = {}


def icono_herramienta(tipo, est):
    """Icono recortado y ajustado a una caja de 54x54."""
    clave = (tipo, est)
    if clave not in _iconos:
        s = pygame.Surface((300, 300), pygame.SRCALPHA)
        arte_paleo.dibujar_herramienta(s, tipo, 150, 190, 0.8, est, 40.0)
        r = s.get_bounding_rect()
        if r.w < 2 or r.h < 2:
            _iconos[clave] = pygame.Surface((2, 2), pygame.SRCALPHA)
        else:
            rec = s.subsurface(r).copy()
            f = min(54 / rec.get_width(), 54 / rec.get_height())
            _iconos[clave] = pygame.transform.smoothscale(
                rec, (max(2, int(rec.get_width() * f)), max(2, int(rec.get_height() * f))))
    return _iconos[clave]


class BotonHerr(Boton):
    """Boton de la barra de herramientas: icono, estrellas, durabilidad y marca de rota/faltante."""

    def __init__(self, rect, tipo):
        super().__init__(rect, fd.NOMBRES_HERR[tipo], COLOR_HERR[tipo])
        self.tipo = tipo
        self.clave = tipo
        self.elegido = False
        self.pulso = False
        self.est = 0               # estrellas de la herramienta activa (0 = no hay)
        self.frac = 0.0            # durabilidad restante 0..1
        self.infinita = False
        self.rota = 0.0            # parpadeo rojo tras romperse
        self.bloqueo = ""          # capas que esta herramienta no puede trabajar (aviso breve)

    def dibujar(self, p, fnt, t=0.0):
        falta = self.est <= 0
        color = aclarar(self.color, 0.28) if (self.encima or self.elegido) else self.color
        if falta:
            color = (150, 146, 156)
        pygame.draw.rect(p, oscurecer(color, 0.5), self.rect.move(0, 6), border_radius=18)
        pygame.draw.rect(p, color, self.rect, border_radius=18)
        if self.rota > 0:
            k = 0.5 + 0.5 * math.sin(t * 16)
            pygame.draw.rect(p, (255, int(60 + 60 * k), 60), self.rect.inflate(6, 6), 5, border_radius=20)
        pygame.draw.rect(p, (255, 236, 110) if self.elegido else (255, 255, 255), self.rect,
                         7 if self.elegido else 3, border_radius=18)
        if self.pulso and not self.elegido and not falta:
            k = 0.5 + 0.5 * math.sin(t * 7)
            pygame.draw.rect(p, (255, 240, 120), self.rect.inflate(10 + 8 * k, 10 + 8 * k), 4, border_radius=22)
        ic = icono_herramienta(self.tipo, max(1, self.est))
        if falta:
            ic = ic.copy()
            ic.set_alpha(110)
        p.blit(ic, ic.get_rect(center=(self.rect.x + 36, self.rect.centery - 1)))
        x0 = self.rect.x + 68
        tam = 19
        while tam > 13 and fuente(tam).size(self.texto)[0] > self.rect.right - x0 - 8:
            tam -= 1
        escribir_c(p, fuente(tam), self.texto, x0, self.rect.y + 14, ancla="izq", grosor=2)
        if falta:
            escribir_c(p, fuente(17), "Sin herramienta", x0, self.rect.y + 33, ancla="izq", color=(255, 214, 205),
                     grosor=1)
            pygame.draw.line(p, (230, 60, 60), (self.rect.x + 14, self.rect.y + 12), (self.rect.x + 58, self.rect.bottom - 12), 6)
            pygame.draw.line(p, (230, 60, 60), (self.rect.x + 58, self.rect.y + 12), (self.rect.x + 14, self.rect.bottom - 12), 6)
        else:
            for i in range(5):
                lleno = i < self.est
                estrella(p, x0 + 7 + i * 16, self.rect.y + 33, 7,
                         (255, 214, 70) if lleno else (170, 170, 186),
                         (150, 100, 20) if lleno else (110, 110, 130))
            col = (90, 210, 110) if self.frac > 0.5 else (250, 200, 50) if self.frac > 0.2 else (236, 72, 72)
            if self.infinita:
                col = (110, 190, 255)
            barra(p, (x0, self.rect.y + 44, 122, 8), 1.0 if self.infinita else self.frac, color=col,
                  color_fondo=(50, 40, 40), borde=(255, 255, 255))
        if self.dwell > 0:
            frac = min(1.0, self.dwell / DWELL_SEG)
            r = pygame.Rect(self.rect.x + 14, self.rect.bottom - 8, self.rect.width - 28, 6)
            barra(p, r, frac, color=(255, 230, 90), color_fondo=(110, 120, 150), borde=(255, 255, 255))
