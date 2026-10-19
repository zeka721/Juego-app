"""Pasos de cocina de MASAS Y MONTAJE (S2): aplastar, presionar, moldear, enrollar, untar, espolvorear, decorar.

Todos se juegan solo con el cursor (la herramienta ES el cursor) y siguen las reglas de cocina_base:
calidad minima 0.25, `dif` 0..10, `mods` (pot, alc, tiempo, lento) y el bot inerte termina al acabar el tiempo.

spec (claves que leen):
  aplastar     ing                       -> estilo Cookie Mama: la masa sube y se estrella; sigue la bolita guia (arriba/abajo).
  presionar    ing, herr="rodillo"|"tenedor"
               rodillo: vaiven izquierda-derecha extiende la masa; tenedor: tocar los puntitos para marcar la masa.
  moldear      ing, herr="molde"|"manos", forma="estrella|corazon|flor|circulo" (opcional; si falta se mezclan)
               molde: pasar el cortador por cada figura marcada y esperar un momento (o clic) para estampar;
               manos: tocar los puntos alrededor de la masa para redondearla.
  enrollar     ing, dir="der"|"izq" (opcional), relleno="<ing>" (color del relleno; por defecto segun ing)
               mover el cursor en una direccion por el carril: la base se enrolla.
  untar        ing (lo que se unta: mantequilla, queso_crema, mermelada, crema_cacao, salsa...), sobre (pan, base, panqueque...)
               cubrir la superficie con la espatula; zonas con chispitas hasta que quedan cubiertas.
  espolvorear  ing (sal, harina, canela, azucar, queso...), sobre; salero / cernidor (herr opcional "salero"|"cernidor").
  decorar      ing (sobre que se decora: galleta, base...), sobre, color=(r,g,b) opcional, patron="ondas|corazon|estrella|
               espiral|guirnalda|zigzag" opcional; seguir los puntos en orden con la manga pastelera.
"""

import math
import random

import pygame

import catalogo
from ajustes import ANCHO, ALTO
from nucleo import aclarar, escribir, oscurecer, panel, V2
from cocina_base import Paso, AREA, paso

CX, CY = ANCHO // 2, 390
MASA = (240, 214, 160)
PIEL = (255, 214, 170)

COLORES_ING = {
    "masa": MASA, "masa_plana": MASA, "base": (240, 212, 150), "galleta": (222, 172, 105), "pizza": (240, 205, 130),
    "panqueque": (236, 188, 105), "bizcocho": (240, 205, 130), "pan": (225, 175, 100), "pan_rebanado": (225, 175, 100),
    "mantequilla": (252, 228, 125), "queso_crema": (246, 242, 228), "queso": (250, 205, 80), "mermelada": (205, 45, 85),
    "crema_cacao": (115, 66, 42), "salsa": (212, 62, 42), "crema": (250, 250, 238), "miel": (240, 170, 30),
    "sal": (252, 252, 252), "harina": (250, 246, 234), "azucar": (255, 255, 255), "canela": (170, 98, 58),
    "glaseado": (252, 236, 244), "crema_batida": (252, 250, 244), "chocolate": (110, 64, 40), "relleno": (210, 70, 70),
    "carne": (190, 60, 60), "nueces": (150, 105, 60),
}

NOMBRES_ING = {
    "mantequilla": "la mantequilla", "queso_crema": "el queso crema", "mermelada": "la mermelada",
    "crema_cacao": "la crema de cacao", "salsa": "la salsa", "crema": "la crema", "miel": "la miel", "queso": "el queso",
    "sal": "la sal", "harina": "la harina", "azucar": "el azúcar", "canela": "la canela", "nueces": "las nueces",
    "chocolate": "el chocolate", "masa": "la masa", "base": "la base", "relleno": "el relleno",
}


def _color(ing, defecto=MASA):
    if ing in COLORES_ING:
        return COLORES_ING[ing]
    try:
        return tuple(catalogo.info(ing)["color"])
    except Exception:
        return defecto


def _nombre(ing, defecto="la masa"):
    return NOMBRES_ING.get(ing, defecto)


def _hash(txt):
    return sum(ord(c) * (i + 1) for i, c in enumerate(str(txt)))


def _fin(q):
    return "¡Perfecto!" if q >= 0.9 else "¡Muy bien!" if q >= 0.6 else "¡Así se practica!"


def _dwell(items, pos, radio, espera, dt, clic=False):
    """Mantener el cursor sobre un punto `espera` segundos lo marca (solo el mas cercano acumula; clic acelera).
    items: dicts con x, y, hecho, dwell. Devuelve los items que se acaban de completar."""
    cerca = None
    dmin = radio
    for it in items:
        if it["hecho"]:
            continue
        d = math.hypot(pos.x - it["x"], pos.y - it["y"])
        if d < dmin:
            cerca, dmin = it, d
    nuevos = []
    for it in items:
        if it["hecho"]:
            continue
        if it is cerca:
            it["dwell"] += dt * (4.0 if clic else 1.0)
            if it["dwell"] >= espera:
                it["hecho"] = True
                nuevos.append(it)
        else:
            it["dwell"] = max(0.0, it["dwell"] - dt * 2)
    return nuevos


# ----------------------------------------------------------------------------- arte (con arte externo opcional)
def _herr_ext(p, nombre, x, y, tam, ang=0.0):
    """Intenta cocina_herramientas.dibujar_herr; True si dibujo."""
    try:
        import cocina_herramientas as m
        f = getattr(m, "dibujar_herr", None)
        if f is None:
            return False
        f(p, nombre, x, y, tam, ang)
        return True
    except Exception:
        return False


def _ing_ext(p, ident, x, y, tam, estado="entero", t=0.0):
    try:
        import cocina_ingredientes as m
        f = getattr(m, "dibujar_ing", None)
        if f is None:
            return False
        f(p, ident, x, y, tam, estado, t)
        return True
    except Exception:
        return False


def _rot(pts, ang, ox, oy):
    c, s = math.cos(ang), math.sin(ang)
    return [(ox + x * c - y * s, oy + x * s + y * c) for x, y in pts]


def insignia(p, ing, x, y, t, estado="entero"):
    """Circulo con el ingrediente en la esquina (por si el nino olvida que esta haciendo)."""
    pygame.draw.circle(p, (255, 255, 255), (x, y), 52)
    pygame.draw.circle(p, (200, 150, 95), (x, y), 52, 4)
    if not ing:
        return
    if not _ing_ext(p, ing, x, y, 70, estado, t):
        c = _color(ing)
        pygame.draw.circle(p, c, (x, y), 30)
        pygame.draw.circle(p, oscurecer(c, 0.3), (x, y), 30, 3)
        pygame.draw.circle(p, aclarar(c, 0.5), (x - 9, y - 10), 8)


def blob(p, cx, cy, rx, ry, col=MASA):
    rx, ry = max(3, int(rx)), max(3, int(ry))
    r = pygame.Rect(0, 0, rx * 2, ry * 2)
    r.center = (int(cx), int(cy))
    pygame.draw.ellipse(p, oscurecer(col, 0.22), r.move(0, 6))
    pygame.draw.ellipse(p, col, r)
    h = pygame.Rect(0, 0, int(rx * 0.8), int(ry * 0.45))
    h.center = (int(cx - rx * 0.2), int(cy - ry * 0.45))
    pygame.draw.ellipse(p, aclarar(col, 0.4), h)
    pygame.draw.ellipse(p, oscurecer(col, 0.3), r, 3)


def mano(p, x, y, hacia=1, s=1.0):
    """Mano abierta con los dedos hacia `hacia` (+1 derecha, -1 izquierda)."""
    pygame.draw.ellipse(p, PIEL, (x - 28 * s, y - 34 * s, 56 * s, 68 * s))
    for i in range(4):
        fy = y - 27 * s + i * 18 * s
        pygame.draw.ellipse(p, PIEL, (x + hacia * 24 * s - 20 * s, fy - 8 * s, 40 * s, 17 * s))
        pygame.draw.ellipse(p, oscurecer(PIEL, 0.25), (x + hacia * 24 * s - 20 * s, fy - 8 * s, 40 * s, 17 * s), 2)
    pygame.draw.ellipse(p, PIEL, (x - 10 * s, y + 20 * s, 40 * s, 22 * s))
    pygame.draw.ellipse(p, oscurecer(PIEL, 0.25), (x - 28 * s, y - 34 * s, 56 * s, 68 * s), 2)


def pts_forma(nombre, cx, cy, r):
    if nombre == "estrella":
        return [(cx + (r if i % 2 == 0 else r * 0.47) * math.cos(-math.pi / 2 + i * math.pi / 5),
                 cy + (r if i % 2 == 0 else r * 0.47) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    if nombre == "corazon":
        res = []
        for i in range(40):
            t = i / 40 * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            res.append((cx + x * r / 17, cy + 1 + y * r / 17))
        return res
    if nombre == "flor":
        return [(cx + r * (0.76 + 0.24 * math.cos(5 * a)) * math.cos(a), cy + r * (0.76 + 0.24 * math.cos(5 * a)) * math.sin(a))
                for a in (i / 50 * 2 * math.pi for i in range(50))]
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (i / 32 * 2 * math.pi for i in range(32))]


FORMAS = ("estrella", "corazon", "flor", "circulo", "cuadrado")
NOMBRES_FORMA = {"estrella": "estrella", "corazon": "corazón", "flor": "flor", "circulo": "círculo", "cuadrado": "cuadrado"}


def pts_molde(nombre, cx, cy, r):
    """pts_forma + el cuadradito redondeado (moldes de la paleta)."""
    if nombre == "cuadrado":
        res = []
        for i in range(48):
            a = i / 48 * 2 * math.pi
            c, sn = math.cos(a), math.sin(a)
            k = r * 0.86
            res.append((cx + k * math.copysign(abs(c) ** 0.3, c), cy + k * math.copysign(abs(sn) ** 0.3, sn)))
        return res
    return pts_forma(nombre, cx, cy, r)


def superficie(nombre):
    """(surface RGBA, tipo) de la comida sobre la que se unta / espolvorea / decora. Cacheada."""
    if nombre in _SUP:
        return _SUP[nombre]
    if nombre in ("pan", "pan_rebanado", "bizcocho"):
        w, h = 560, 380
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        corteza = (186, 126, 66) if nombre != "bizcocho" else (205, 150, 80)
        pygame.draw.rect(s, corteza, (0, 0, w, h), border_radius=70)
        pygame.draw.rect(s, oscurecer(corteza, 0.2), (0, 0, w, h), 5, border_radius=70)
        pygame.draw.rect(s, (246, 218, 156), (24, 24, w - 48, h - 48), border_radius=50)
        rnd = random.Random(7)
        for _ in range(55):
            x, y = rnd.randint(50, w - 50), rnd.randint(50, h - 50)
            pygame.draw.circle(s, (232, 198, 134), (x, y), rnd.randint(3, 6))
        res = (s, "rect")
    else:
        R = 205
        s = pygame.Surface((2 * R, 2 * R), pygame.SRCALPHA)
        col = _color(nombre, MASA)
        if nombre not in COLORES_ING:
            col = MASA
        pygame.draw.circle(s, oscurecer(col, 0.15), (R, R), R)
        pygame.draw.circle(s, col, (R, R), R - 12)
        pygame.draw.circle(s, aclarar(col, 0.25), (R - 20, R - 24), R - 60)
        pygame.draw.circle(s, oscurecer(col, 0.3), (R, R), R, 5)
        rnd = random.Random(3)
        for _ in range(26):
            a, d = rnd.random() * 6.28, rnd.random() * (R - 50)
            x, y = R + d * math.cos(a), R + d * math.sin(a)
            if nombre == "galleta":
                pygame.draw.circle(s, (92, 56, 36), (int(x), int(y)), rnd.randint(7, 11))
            elif nombre == "panqueque":
                pygame.draw.circle(s, (205, 150, 75), (int(x), int(y)), rnd.randint(6, 12))
            else:
                pygame.draw.circle(s, oscurecer(col, 0.08), (int(x), int(y)), rnd.randint(3, 6))
        res = (s, "disc")
    mascara = pygame.mask.from_surface(res[0], 10).to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    _SUP[nombre] = (res[0], res[1], mascara)
    return _SUP[nombre]


_SUP = {}


# ----------------------------------------------------------------------------- base comun
class PasoMasa(Paso):
    pista = ""

    def _arte_comun(self, p):
        insignia(p, self.ing, 108, AREA.y + 100, self.t)
        if self.terminado:
            escribir(p, self.f.grande, self.mensaje or _fin(self.calidad), CX, AREA.y + 50, (255, 245, 150))
        elif self.pista:
            escribir(p, self.f.normal, self.pista, CX, AREA.y + 42, (255, 255, 255))

    def dibujar_paso(self, p):
        self.dibujar_escena(p)
        self._arte_comun(p)

    def dibujar_escena(self, p):
        pass


# ============================================================================= APLASTAR
@paso("aplastar")
class Aplastar(PasoMasa):
    """La masa sube y se estrella; sigue con el cursor la bolita guia arriba / abajo al ritmo."""

    pista = "Sube y baja la mano con la bolita amarilla"
    TRACK_X = 1140

    def iniciar(self):
        d = self.dif / 10
        self.titulo = "¡Aplasta la masa!"
        self.intro = 1.4
        self.periodo = (2.2 - 0.6 * d) / max(0.3, self.mods.lento)
        self.necesarios = 28 + round(12 * d)
        reach = (60 + 10 * d) / max(0.6, self.mods.alc)
        self.thr_arr = 360 - reach
        self.thr_aba = 360 + reach
        self.win = 0.2 * self.periodo * max(1.0, self.mods.alc)
        self.k = 1
        self.ok = False
        self.squash = 0.0
        self.aplastes = 0
        self.f_vis = 0.0

    def tiempo_base(self):
        return 55.0

    @property
    def tt(self):
        return self.t - self.intro

    def altura(self, tt=None):
        tt = self.tt if tt is None else tt
        if tt < 0:
            return 0.0
        ph = (tt / self.periodo) % 1.0
        return 1 - (2 * ph - 1) ** 2

    def guia_y(self):
        tt = self.tt
        if tt < 0:
            return 360.0 + 200
        return 360 + 200 * math.cos(2 * math.pi * tt / self.periodo)

    def actualizar_paso(self, dt, ctrl):
        self.squash = max(0.0, self.squash - dt * 4)
        self.f_vis += (self.prog - self.f_vis) * min(1.0, dt * 5)
        self.cy_mano = max(190.0, min(570.0, ctrl.pos.y))
        tt = self.tt
        while tt >= 0:
            tk = self.k * self.periodo / 2
            if tt >= tk - self.win and not self.ok:
                if (ctrl.pos.y < self.thr_arr) if self.k % 2 == 1 else (ctrl.pos.y > self.thr_aba):
                    self.ok = True
            if tt < tk:
                break
            if self.ok:
                self.avanzar(self.mods.pot / self.necesarios)
                if self.k % 2 == 0:
                    self.squash = 1.0
                    self.aplastes += 1
                    self.sumar_particulas(CX, 560, (255, 252, 240), 12)
                    self.texto_flotante("¡Plaf!", CX + random.randint(-120, 120), 470)
                else:
                    self.texto_flotante("¡Arriba!", CX + random.randint(-120, 120), 240, (200, 240, 255))
            self.k += 1
            self.ok = False
        if self.prog >= 0.999:
            self.terminar(1.0, "¡Masa lista!")

    def dibujar_escena(self, p):
        h = self.altura()
        f = self.f_vis
        rx = 85 + 150 * f
        ry = 82 - 40 * f
        sq = self.squash
        rx *= 1 + 0.28 * sq
        ry *= 1 - 0.28 * sq
        ybase = 574 - ry
        y = ybase - h * (ybase - 235)
        sh = 1 - 0.55 * h
        pygame.draw.ellipse(p, (170, 125, 80), (CX - rx * sh, 566, 2 * rx * sh, 22))
        blob(p, CX, y, rx, ry)
        rnd = random.Random(2)
        for _ in range(7):
            ox, oy = rnd.uniform(-.6, .6) * rx, rnd.uniform(-.5, .3) * ry
            pygame.draw.circle(p, (255, 252, 240), (int(CX + ox), int(y + oy)), 4)
        # manos: siguen al cursor (y)
        hy = getattr(self, "cy_mano", 480)
        mano(p, CX - rx - 55, hy, +1)
        mano(p, CX + rx + 55, hy, -1)
        # pista (carril de la bolita guia)
        x = self.TRACK_X
        pygame.draw.line(p, (205, 160, 110), (x, 170), (x, 570), 10)
        for yy, tx in ((self.thr_arr, "ARRIBA"), (self.thr_aba, "ABAJO")):
            pygame.draw.line(p, (255, 255, 255), (x - 40, yy), (x + 40, yy), 4)
        gy = max(170, min(570, self.guia_y()))
        near = abs(self.tt - self.k * self.periodo / 2) < self.win * 1.5 and self.tt >= -0.5
        pygame.draw.circle(p, (255, 220, 60), (x, int(gy)), 26 if near else 20)
        pygame.draw.circle(p, (255, 255, 255), (x, int(gy)), 26 if near else 20, 4)
        if self.tt >= 0 or int(self.t * 3) % 2 == 0:
            arriba = self.k % 2 == 1
            ax = x - 75
            if arriba:
                pts = [(ax, 150), (ax - 22, 190), (ax + 22, 190)]
            else:
                pts = [(ax, 600), (ax - 22, 560), (ax + 22, 560)]
            pygame.draw.polygon(p, (255, 160, 70), pts)
        pygame.draw.circle(p, (255, 255, 255), (x + 0, int(max(170, min(570, self.cy_mano if hasattr(self, "cy_mano") else 360)))), 9)
        pygame.draw.circle(p, (90, 60, 40), (x, int(max(170, min(570, getattr(self, "cy_mano", 360))))), 9, 3)


# ============================================================================= PRESIONAR
@paso("presionar")
class Presionar(PasoMasa):
    """Rodillo en vaiven (extiende la masa) o tenedor (marca puntitos)."""

    def iniciar(self):
        d = self.dif / 10
        self.d = d
        self.tenedor = self.herr in ("tenedor", "tenedor_pinchar")
        self.pistas = {True: "Pon el tenedor un momento sobre cada circulito", False: "Mueve el rodillo de lado a lado"}
        self.pista = self.pistas[self.tenedor]
        if self.tenedor:
            self.titulo = "¡Marca la masa con el tenedor!"
            n = 28 + round(d * 0.8)
            rr = (175, 120, 65)
            cnt = [round(n * r / sum(rr)) for r in rr]
            cnt[0] += n - sum(cnt)
            self.pts = []
            for k, (r, c) in enumerate(zip(rr, cnt)):
                self.pts += [(CX + r * math.cos(2 * math.pi * i / c + 0.3 * (k + 1)),
                              CY + r * math.sin(2 * math.pi * i / c + 0.3 * (k + 1))) for i in range(c)]
            self.items = [dict(x=x, y=y, hecho=False, dwell=0.0) for x, y in self.pts]
            self.hecho = [False] * len(self.pts)
            self.espera = 1.2
            sp = 2 * math.pi * rr[2] / cnt[2]
            self.radio = min(50 - 1.5 * d, max(26.0, 0.48 * sp)) * self.mods.alc
        else:
            self.titulo = "¡Extiende la masa con el rodillo!"
            self.necesarios = 50 + round(d)
            self.umbral = (130 + 6 * d) / max(0.6, self.mods.alc)
            self.lado = 0
            self.golpes = 0
            self.f_vis = 0.0
            self.banda = 190 * self.mods.alc

    def tiempo_base(self):
        return 55.0

    def actualizar_paso(self, dt, ctrl):
        pos = ctrl.pos
        if self.tenedor:
            for it in _dwell(self.items, pos, self.radio, self.espera / max(0.5, self.mods.pot), dt, ctrl.clic):
                self.hecho[self.items.index(it)] = True
                self.avanzar(1.0 / len(self.pts))
                self.sumar_particulas(it["x"], it["y"], (250, 235, 200), 5)
            if all(self.hecho) or self.prog >= 0.999:
                self.terminar(1.0, "¡Masa marcada!")
        else:
            self.f_vis += (self.prog - self.f_vis) * min(1.0, dt * 6)
            if abs(pos.y - CY) < self.banda:
                lado = 0
                if pos.x < CX - self.umbral:
                    lado = -1
                elif pos.x > CX + self.umbral:
                    lado = 1
                if lado:
                    if self.lado and lado != self.lado:
                        self.golpes += 1
                        self.avanzar(self.mods.pot / self.necesarios)
                        self.sumar_particulas(pos.x, CY + 100, (255, 252, 240), 6)
                    self.lado = lado
            if self.prog >= 0.999:
                self.terminar(1.0, "¡Masa extendida!")

    def dibujar_escena(self, p):
        pos = self._pos
        if self.tenedor:
            rect = pygame.Rect(0, 0, 470, 470)
            rect.center = (CX, CY)
            blob(p, CX, CY, 235, 235)
            ca, sa = math.cos(self.ANG_TEN), math.sin(self.ANG_TEN)
            for (x, y), h in zip(self.pts, self.hecho):
                if h:
                    for dx in self.DX_TEN:
                        mx, my = x + dx * ca, y + dx * sa
                        pygame.draw.circle(p, (178, 136, 88), (int(mx), int(my)), 5)
                        pygame.draw.circle(p, (255, 240, 205), (int(mx - 1), int(my - 2)), 2)
                else:
                    r = 15 + int(3 * math.sin(self.t * 5))
                    pygame.draw.circle(p, (255, 255, 255), (int(x), int(y)), r, 3)
                    dw = self.items[self.pts.index((x, y))]["dwell"]
                    if dw > 0:
                        fr = min(1.0, dw / self.espera)
                        pygame.draw.arc(p, (255, 170, 60), (x - 24, y - 24, 48, 48), math.pi / 2,
                                        math.pi / 2 + 2 * math.pi * fr, 6)
            self._tenedor(p, pos)          # arte propio: la PUNTA de los dientes cae exactamente en ctrl.pos
        else:
            f = self.f_vis
            w, h = 310 + 340 * f, 200 + 130 * f
            r = pygame.Rect(0, 0, int(w), int(h))
            r.center = (CX, CY)
            pygame.draw.rect(p, oscurecer(MASA, 0.22), r.move(0, 7), border_radius=70)
            pygame.draw.rect(p, MASA, r, border_radius=70)
            pygame.draw.rect(p, aclarar(MASA, 0.35), r.inflate(-40, -40), 4, border_radius=55)
            pygame.draw.rect(p, oscurecer(MASA, 0.3), r, 4, border_radius=70)
            # guia: flechas laterales
            a = 22 * math.sin(self.t * 4)
            y = CY
            for sx in (-1, 1):
                x = CX + sx * (self.umbral + 40) + sx * a * 0.3
                pygame.draw.polygon(p, (255, 160, 70), [(x + sx * 20, y), (x - sx * 10, y - 22), (x - sx * 10, y + 22)])
            if not _herr_ext(p, "rodillo", pos.x, pos.y, 200, 0.0):
                self._rodillo(p, pos)

    _pos = V2(CX, CY)

    def dibujar_paso(self, p):
        super().dibujar_paso(p)

    def actualizar(self, dt, ctrl):
        self._pos = V2(ctrl.pos)
        super().actualizar(dt, ctrl)

    @staticmethod
    def _rodillo(p, pos):
        x, y = int(pos.x), int(pos.y)
        for yy in (y - 150, y + 105):
            pygame.draw.rect(p, (160, 105, 60), (x - 13, yy, 26, 45), border_radius=12)
        pygame.draw.rect(p, (225, 178, 112), (x - 28, y - 110, 56, 220), border_radius=24)
        pygame.draw.rect(p, (252, 220, 160), (x - 18, y - 100, 14, 200), border_radius=7)
        pygame.draw.rect(p, (140, 90, 50), (x - 28, y - 110, 56, 220), 4, border_radius=24)

    ANG_TEN = 0.38                         # inclinacion (rad): el mango sube hacia la derecha
    DX_TEN = (-18, -6, 6, 18)              # posicion de cada diente respecto de la punta (a lo ancho)

    @classmethod
    def _tenedor(cls, p, pos):
        """Tenedor con la punta de los dientes EXACTAMENTE en pos; mango arriba a la derecha, inclinado."""
        a, ox, oy = cls.ANG_TEN, pos.x, pos.y
        gris, borde = (214, 219, 230), (120, 128, 148)

        def poli(pts, col, ancho=0, dx=0, dy=0):
            q = [(x + dx, y + dy) for x, y in _rot(pts, a, ox, oy)]
            pygame.draw.polygon(p, col, q, ancho)

        def elipse(cx, cy, rx, ry, n=28):
            return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]
        partes = []
        for dx in cls.DX_TEN:
            partes.append([(dx - 3.5, -62), (dx + 3.5, -62), (dx + 3.5, 0), (dx - 3.5, 0)])
        partes.append([(-24, -56), (24, -56), (24, -72), (9, -98), (-9, -98), (-24, -72)])
        partes.append([(-6, -96), (6, -96), (6, -150), (-6, -150)])
        partes.append(elipse(0, -198, 18, 52))
        for q in partes:                                    # sombra suave sobre la masa
            poli(q, (170, 128, 84), 0, 4, 3)
        for q in partes:
            poli(q, gris)
        for q in partes:
            poli(q, borde, 2)
        for dx in cls.DX_TEN:                               # puntita redondeada de cada diente
            c = _rot([(dx, -1)], a, ox, oy)[0]
            pygame.draw.circle(p, gris, (int(c[0]), int(c[1])), 4)
        pygame.draw.circle(p, (255, 90, 70), (int(ox), int(oy)), 4, 2)   # marca del punto de accion


# ============================================================================= MOLDEAR
@paso("moldear")
class Moldear(PasoMasa):
    """Cortador sobre la masa estampando formas, o con las manos redondeando la masa."""

    def iniciar(self):
        d = self.dif / 10
        self.d = d
        self.molde = self.herr in ("molde", "cortador")
        self.pos = V2(CX, CY)
        if self.molde:
            self.titulo = "¡Corta formas en la masa!"
            self.pista = "Elige un molde del costado y llévalo a una figura igual"
            n = 13 + round(d * 0.3)
            cols = (n + 2) // 3
            self.hoja = pygame.Rect(290, 175, 730, 430)
            fijo = self.spec.get("forma")
            if fijo not in FORMAS:
                fijo = None
            rnd = random.Random(_hash(self.ing or "") + 11)
            if fijo:
                formas = [fijo] * n
                otras = [f for f in FORMAS if f != fijo]
                rnd.shuffle(otras)
                pal = [fijo] + otras[:2]
                rnd.shuffle(pal)
            else:
                pool = list(FORMAS)
                formas = []
                while len(formas) < n:                       # reparto parejo y mezclado
                    rnd.shuffle(pool)
                    formas += pool
                formas = formas[:n]
                pal = list(FORMAS)
            self.spots = []
            for i in range(n):
                row, col = i % 3, i // 3
                x = self.hoja.x + self.hoja.w * (col + 0.5) / cols
                y = self.hoja.y + self.hoja.h * (row + 0.5) / 3
                self.spots.append(dict(x=x, y=y, forma=formas[i], dwell=0.0, hecho=False, anim=0.0))
            # paleta de moldes (columna a la izquierda)
            self.pal_rect = pygame.Rect(30, 262, 220, 330)
            paso_y = (self.pal_rect.h - 20) / len(pal)
            self.paleta = [dict(forma=f, x=self.pal_rect.x + 44, y=self.pal_rect.y + 10 + paso_y * (k + 0.5), dwell=0.0)
                           for k, f in enumerate(pal)]
            self.R = min(54.0, 0.42 * self.hoja.w / cols)
            self.radio = min(68 - 2 * d, 0.5 * self.hoja.w / cols) * self.mods.alc
            self.radio_pal = 44.0 * self.mods.alc
            self.espera = 1.3 + 0.02 * d
            self.espera_pal = 0.5
            self.elegido = None            # forma del molde que sigue al cursor
            self.aviso_t = 0.0             # tiempo restante del aviso amable
            self.aviso = ""
            self.correcto = None           # molde correcto resaltado en la paleta
            self.aviso_pos = (CX, CY)
        else:
            self.titulo = "¡Dale forma con las manos!"
            self.pista = "Pon la mano un momento sobre cada circulito"
            n = 22 + round(0.5 * d)
            n2 = n * 8 // 22
            n1 = n - n2
            self.marc = [dict(x=CX + 215 * math.cos(2 * math.pi * i / n1 + 0.2), y=CY + 175 * math.sin(2 * math.pi * i / n1 + 0.2),
                              hecho=False, dwell=0.0) for i in range(n1)]
            self.marc += [dict(x=CX + 105 * math.cos(2 * math.pi * i / n2 + 0.6), y=CY + 80 * math.sin(2 * math.pi * i / n2 + 0.6),
                               hecho=False, dwell=0.0) for i in range(n2)]
            self.radio = min(52 - 1.5 * d, 38.0) * self.mods.alc
            self.espera = 1.45
            self.amp = 0.38

    def tiempo_base(self):
        return 55.0

    def actualizar_paso(self, dt, ctrl):
        self.pos = V2(ctrl.pos)
        if self.molde:
            pot = max(0.5, self.mods.pot)
            clic = ctrl.clic or ctrl.golpe
            for s_ in self.spots:
                s_["anim"] = max(0.0, s_["anim"] - dt * 3)
            self.aviso_t = max(0.0, self.aviso_t - dt)
            if self.aviso_t <= 0:
                self.correcto = None
            # elegir molde: posar el cursor sobre el de la paleta un instante (sin clic)
            cerca = None
            dmin = self.radio_pal
            for m in self.paleta:
                dd = math.hypot(ctrl.pos.x - m["x"], ctrl.pos.y - m["y"])
                if dd < dmin and m["forma"] != self.elegido:
                    cerca, dmin = m, dd
            for m in self.paleta:
                if m is cerca:
                    m["dwell"] += dt * (4.0 if clic else 1.0)
                    if m["dwell"] >= self.espera_pal:
                        m["dwell"] = 0.0
                        self.elegido = m["forma"]
                        self.aviso_t, self.correcto = 0.0, None
                        self.sumar_particulas(m["x"], m["y"], (255, 235, 150), 8)
                else:
                    m["dwell"] = max(0.0, m["dwell"] - dt * 2)
            # estampar: solo figuras de la MISMA forma que el molde elegido
            buenas = [s_ for s_ in self.spots if not s_["hecho"] and s_["forma"] == self.elegido]
            for s_ in self.spots:
                if not s_["hecho"] and s_ not in buenas:
                    s_["dwell"] = max(0.0, s_["dwell"] - dt * 2)
            for s_ in _dwell(buenas, ctrl.pos, self.radio, self.espera / pot, dt, clic):
                s_["anim"] = 1.0
                self.avanzar(1.0 / len(self.spots))
                self.sumar_particulas(s_["x"], s_["y"], (255, 235, 190), 10)
                self.texto_flotante("¡Clac!", s_["x"], s_["y"] - 70)
            # molde equivocado sobre una figura: no corta y avisa con amabilidad
            if self.elegido and not any(math.hypot(ctrl.pos.x - s_["x"], ctrl.pos.y - s_["y"]) < self.radio for s_ in buenas):
                mal = [s_ for s_ in self.spots if not s_["hecho"] and s_["forma"] != self.elegido
                       and math.hypot(ctrl.pos.x - s_["x"], ctrl.pos.y - s_["y"]) < self.radio]
                if mal:
                    s_ = min(mal, key=lambda q: math.hypot(ctrl.pos.x - q["x"], ctrl.pos.y - q["y"]))
                    self.aviso = "Prueba con el molde de %s" % NOMBRES_FORMA.get(s_["forma"], s_["forma"])
                    self.aviso_t = 2.5
                    self.correcto = s_["forma"]
                    self.aviso_pos = (s_["x"], s_["y"])
            if self.aviso_t > 0:
                self.pista = self.aviso
            elif self.elegido is None:
                self.pista = "Elige un molde del costado: quédate sobre él un momento"
            else:
                self.pista = "Lleva el molde a una figura igual y espera"
            if all(s_["hecho"] for s_ in self.spots) or self.prog >= 0.999:
                self.terminar(1.0, "¡Qué lindas formas!")
        else:
            for m in _dwell(self.marc, ctrl.pos, self.radio, self.espera / max(0.5, self.mods.pot), dt, ctrl.clic):
                self.avanzar(1.0 / len(self.marc))
                self.sumar_particulas(m["x"], m["y"], (255, 235, 190), 6)
            objetivo = 0.38 * (1 - self.prog) + 0.02
            self.amp += (objetivo - self.amp) * min(1.0, dt * 5)
            if all(m["hecho"] for m in self.marc) or self.prog >= 0.999:
                self.terminar(1.0, "¡Masa redonda!")

    def dibujar_escena(self, p):
        pos = self.pos
        if self.molde:
            h = self.hoja
            pygame.draw.rect(p, oscurecer(MASA, 0.22), h.move(0, 8), border_radius=36)
            pygame.draw.rect(p, MASA, h, border_radius=36)
            pygame.draw.rect(p, aclarar(MASA, 0.35), h.inflate(-30, -30), 3, border_radius=28)
            R = self.R
            for s_ in self.spots:
                if s_["hecho"]:
                    pygame.draw.polygon(p, (214, 176, 120), pts_molde(s_["forma"], s_["x"], s_["y"], R * 1.13))
                    q = pts_molde(s_["forma"], s_["x"], s_["y"] - 4 * s_["anim"], R)
                    pygame.draw.polygon(p, (250, 226, 172), q)
                    pygame.draw.polygon(p, (196, 150, 92), q, 4)
                    pygame.draw.polygon(p, (255, 244, 214), pts_molde(s_["forma"], s_["x"] - 8, s_["y"] - 8, R * 0.5))
                else:
                    q = pts_molde(s_["forma"], s_["x"], s_["y"], R)
                    igual = s_["forma"] == self.elegido
                    if igual:
                        pygame.draw.polygon(p, (255, 252, 236), q, 4)       # las figuras que le tocan a este molde
                    else:
                        pygame.draw.polygon(p, (205, 170, 118), q, 3)       # contorno tenue
                    if s_["dwell"] > 0:
                        fr = min(1.0, s_["dwell"] / self.espera)
                        pygame.draw.arc(p, (255, 170, 60), (s_["x"] - R - 14, s_["y"] - R - 14, 2 * R + 28, 2 * R + 28), math.pi / 2,
                                        math.pi / 2 + 2 * math.pi * fr, 8)
            # paleta de moldes
            pr = self.pal_rect
            pygame.draw.rect(p, (205, 150, 95), pr.move(0, 5), border_radius=26)
            pygame.draw.rect(p, (255, 247, 228), pr, border_radius=26)
            pygame.draw.rect(p, (150, 100, 60), pr, 4, border_radius=26)
            for m in self.paleta:
                es_el = m["forma"] == self.elegido
                es_ok = m["forma"] == self.correcto and self.aviso_t > 0
                rr = pygame.Rect(0, 0, 196, 58)
                rr.center = (pr.centerx, int(m["y"]))
                if es_el:
                    pygame.draw.rect(p, (255, 226, 120), rr, border_radius=18)
                    pygame.draw.rect(p, (255, 150, 40), rr, 4, border_radius=18)
                if es_ok:
                    gl = 3 + int(2 * (1 + math.sin(self.t * 9)))
                    pygame.draw.rect(p, (120, 220, 130), rr.inflate(8, 8), gl, border_radius=22)
                q = pts_molde(m["forma"], m["x"], m["y"], 22)
                pygame.draw.polygon(p, (205, 212, 225), q)
                pygame.draw.polygon(p, (110, 120, 142), q, 3)
                escribir(p, self.f.normal, NOMBRES_FORMA[m["forma"]], rr.x + 134, int(m["y"]), (90, 60, 40), contorno=None)
                if m["dwell"] > 0:
                    fr = min(1.0, m["dwell"] / self.espera_pal)
                    pygame.draw.arc(p, (255, 170, 60), (m["x"] - 31, m["y"] - 31, 62, 62), math.pi / 2,
                                    math.pi / 2 + 2 * math.pi * fr, 6)
            # aviso amable junto a la figura
            if self.aviso_t > 0 and not self.terminado:
                ax, ay = self.aviso_pos
                ay = ay + R + 30 if ay < 450 else ay - R - 30
                ax = max(520, min(ANCHO - 260, ax))
                bub = pygame.Rect(0, 0, 440, 44)
                bub.center = (int(ax), int(ay))
                pygame.draw.rect(p, (255, 250, 214), bub, border_radius=20)
                pygame.draw.rect(p, (240, 150, 60), bub, 3, border_radius=20)
                escribir(p, self.f.normal, self.aviso, bub.centerx, bub.centery, (110, 70, 40), contorno=None)
            # el molde elegido ES el cursor: su centro es el punto de accion
            if self.elegido:
                q = pts_molde(self.elegido, pos.x, pos.y, self.R)
                pygame.draw.polygon(p, (205, 212, 225), q, 8)
                pygame.draw.polygon(p, (120, 130, 150), q, 2)
                pygame.draw.circle(p, (255, 90, 70), (int(pos.x), int(pos.y)), 4, 2)
                pygame.draw.rect(p, (230, 90, 100), (pos.x - 45, pos.y - self.R - 26, 90, 18), border_radius=9)
                pygame.draw.rect(p, (230, 90, 100), (pos.x - 11, pos.y - self.R - 8, 22, 14))
        else:
            R = 128
            pts = []
            for i in range(60):
                a = i / 60 * 2 * math.pi
                n = 0.5 * math.sin(3 * a + 1) + 0.3 * math.sin(5 * a + 2) + 0.2 * math.sin(7 * a)
                r = R * (1 + self.amp * n)
                pts.append((CX + r * math.cos(a) * 1.15, CY + r * math.sin(a)))
            sombra = [(x, y + 8) for x, y in pts]
            pygame.draw.polygon(p, oscurecer(MASA, 0.22), sombra)
            pygame.draw.polygon(p, MASA, pts)
            pygame.draw.polygon(p, oscurecer(MASA, 0.3), pts, 4)
            pygame.draw.ellipse(p, aclarar(MASA, 0.4), (CX - 90, CY - 85, 110, 55))
            for m in self.marc:
                if m["hecho"]:
                    pygame.draw.circle(p, (120, 200, 110), (int(m["x"]), int(m["y"])), 20)
                    pygame.draw.circle(p, (255, 255, 255), (int(m["x"]), int(m["y"])), 20, 3)
                else:
                    r = 22 + int(3 * math.sin(self.t * 5))
                    pygame.draw.circle(p, (255, 160, 70), (int(m["x"]), int(m["y"])), r, 4)
                    if m["dwell"] > 0:
                        fr = min(1.0, m["dwell"] / self.espera)
                        pygame.draw.arc(p, (255, 255, 255), (m["x"] - 30, m["y"] - 30, 60, 60), math.pi / 2,
                                        math.pi / 2 + 2 * math.pi * fr, 6)
            mano(p, pos.x, pos.y, 1 if pos.x < CX else -1, 1.1)


# ============================================================================= ENROLLAR
@paso("enrollar")
class Enrollar(PasoMasa):
    """Mover el cursor hacia un lado por el carril: la base se enrolla con su relleno."""

    LW, LH = 760, 360

    def iniciar(self):
        d = self.dif / 10
        self.d = d
        self.titulo = "¡Enrolla con cuidado!"
        self.dir = self.spec.get("dir") or ("der" if _hash(self.ing or "") % 2 == 0 else "izq")
        self.sg = 1 if self.dir == "der" else -1
        self.pista = "Lleva el cursor despacito hacia " + ("la derecha" if self.sg > 0 else "la izquierda") + " por el camino"
        self.lane = (160 - 9 * d) * self.mods.alc
        self.r = 0.0
        self.relleno = _color(self.spec.get("relleno") or self.ing, (210, 70, 70))
        if self.ing in ("masa", "base", "masa_plana", None):
            self.relleno = _color(self.spec.get("relleno"), (215, 70, 90))
        self.x0 = CX - self.LW / 2
        self.largo = self.LW - 40
        self.prev = None
        self.dentro = False

    def tiempo_base(self):
        return 55.0

    def actualizar_paso(self, dt, ctrl):
        pos = ctrl.pos
        self.dentro = abs(pos.y - CY) < self.lane
        if self.prev is not None and self.dentro:
            dx = (pos.x - self.prev) * self.sg
            if dx > 0:
                # avance lento: aunque se mueva rapido, enrollar entero lleva ~33 s como minimo
                g = min(dx / (self.largo * 0.85), dt / 33.0) * self.mods.pot
                self.r = min(1.0, self.r + g)
                self.prog = self.r
        self.prev = pos.x
        if self.r >= 0.999:
            self.terminar(1.0, "¡Rico rollito!")

    def dibujar_escena(self, p):
        W, H = self.LW, self.LH
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        r = self.r
        xr = 20 + r * self.largo * 0.96
        rw = 20 + 120 * math.sqrt(r) if r > 0 else 0
        top, bot = 40, H - 40
        h = bot - top
        # lamina plana restante
        if xr < W - 20:
            pygame.draw.rect(s, oscurecer(MASA, 0.22), (xr, top + 6, W - 20 - xr, h), border_radius=20)
            pygame.draw.rect(s, MASA, (xr, top, W - 20 - xr, h), border_radius=20)
            pygame.draw.rect(s, oscurecer(MASA, 0.3), (xr, top, W - 20 - xr, h), 3, border_radius=20)
            for i in range(5):
                x = xr + 30 + i * (W - 60 - xr) / 5
                for j in range(6):
                    y = top + 28 + j * (h - 56) / 5 + (14 if i % 2 else 0)
                    if x < W - 40:
                        pygame.draw.circle(s, self.relleno, (int(x), int(min(bot - 20, y))), 12)
                        pygame.draw.circle(s, aclarar(self.relleno, 0.5), (int(x - 3), int(min(bot - 20, y)) - 3), 4)
        # rollo (cilindro de eje vertical con tapas)
        if rw > 0:
            rx0 = xr - rw
            cuerpo = pygame.Rect(int(rx0), top, int(rw), h)
            pygame.draw.rect(s, oscurecer(MASA, 0.12), cuerpo)
            for i in range(1, 5):
                pygame.draw.line(s, aclarar(MASA, 0.3), (cuerpo.x + cuerpo.w * i / 5, top + 4), (cuerpo.x + cuerpo.w * i / 5, bot - 4), 3)
            for yy, tapa in ((top, True), (bot, False)):
                e = pygame.Rect(cuerpo.x, yy - 14, cuerpo.w, 28)
                pygame.draw.ellipse(s, MASA, e)
                pygame.draw.ellipse(s, oscurecer(MASA, 0.3), e, 3)
                if cuerpo.w > 24:
                    pygame.draw.ellipse(s, self.relleno, e.inflate(-cuerpo.w * 0.5, -12), 4)
            pygame.draw.line(s, oscurecer(MASA, 0.3), (cuerpo.x, top), (cuerpo.x, bot), 3)
            pygame.draw.line(s, oscurecer(MASA, 0.3), (cuerpo.right, top), (cuerpo.right, bot), 3)
        if self.sg < 0:
            s = pygame.transform.flip(s, True, False)
        p.blit(s, (CX - W // 2, CY - H // 2))
        # carril y flecha guia
        c = (120, 200, 110) if self.dentro else (255, 170, 80)
        pygame.draw.line(p, c, (CX - W // 2, CY - self.lane), (CX + W // 2, CY - self.lane), 3)
        pygame.draw.line(p, c, (CX - W // 2, CY + self.lane), (CX + W // 2, CY + self.lane), 3)
        a = 14 * math.sin(self.t * 5)
        x = CX + self.sg * (W // 2 + 60) + self.sg * a
        pygame.draw.polygon(p, (255, 160, 70), [(x + self.sg * 30, CY), (x - self.sg * 10, CY - 30), (x - self.sg * 10, CY + 30)])
        self._mano_pos(p)

    def _mano_pos(self, p):
        pass

    def dibujar_paso(self, p):
        self.dibujar_escena(p)
        self._arte_comun(p)
        mano(p, self.prev if self.prev is not None else CX, self._y, -self.sg, 1.1)

    _y = CY

    def actualizar(self, dt, ctrl):
        self._y = ctrl.pos.y
        super().actualizar(dt, ctrl)


# ============================================================================= UNTAR / ESPOLVOREAR
class _Cubrir(PasoMasa):
    """Cubrir una superficie moviendo el cursor (celdas con chispitas hasta que quedan cubiertas)."""

    CS = 36
    K_TC = 300.0    # TC = K_TC / celdas: asi cubrir toda la superficie lleva ~33 s a buen ritmo, sea grande o chica

    def iniciar(self):
        d = self.dif / 10
        self.d = d
        self.sobre = self.spec.get("sobre") or ("pan" if self.habilidad == "untar" else "base")
        self.surf, self.tipo, self.mascara = superficie(self.sobre)
        self.ox = CX - self.surf.get_width() // 2
        self.oy = CY - self.surf.get_height() // 2
        self.capa = pygame.Surface(self.surf.get_size(), pygame.SRCALPHA)
        self.comp = None
        self.suc = True
        m = pygame.mask.from_surface(self.surf, 10)
        w, h = self.surf.get_size()
        self.celdas = []
        for cy in range(self.CS // 2, h, self.CS):
            for cx in range(self.CS // 2, w, self.CS):
                if m.get_at((cx, cy)):
                    self.celdas.append([cx, cy, 0.0])
        self.prev = None
        self.color = _color(self.ing, (250, 240, 220))
        self.total = len(self.celdas)
        self.TC = self.K_TC / max(40, self.total)     # segundos que una celda necesita bajo la herramienta
        self.cur = V2(CX, CY)
        self.cubierto = 0.0
        self.iniciar_cub()

    def iniciar_cub(self):
        pass

    def tiempo_base(self):
        return 55.0

    def tocar(self, lx, ly, r, paso_nivel):
        r2 = r * r
        for c in self.celdas:
            if (c[0] - lx) ** 2 + (c[1] - ly) ** 2 <= r2 and c[2] < 1.0:
                c[2] = min(1.0, c[2] + paso_nivel)
                self.suc = True

    def muestras(self, a, b, r):
        d = a.distance_to(b)
        n = max(1, int(d / max(8.0, r * 0.5)))
        return [a.lerp(b, (i + 1) / n) for i in range(n)]

    def actualizar_paso(self, dt, ctrl):
        self.cur = V2(ctrl.pos)
        loc = V2(ctrl.pos.x - self.ox, ctrl.pos.y - self.oy)
        prev = self.prev if self.prev is not None else loc
        self.mover(dt, loc, prev)
        self.prev = loc
        self.cubierto = sum(min(1.0, c[2]) for c in self.celdas) / max(1, self.total)
        self.prog = min(1.0, self.cubierto / 0.95)
        if self.cubierto >= 0.95:
            self.terminar(1.0, self.msg_fin)

    msg_fin = "¡Bien cubierto!"

    def componer(self):
        if self.suc or self.comp is None:
            c = self.capa.copy()
            c.blit(self.mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.comp = c
            self.suc = False
        return self.comp

    def dibujar_escena(self, p):
        # sombra y comida
        s = self.surf
        sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        sombra.blit(self.mascara, (0, 0))
        sombra.fill((90, 60, 40, 70), special_flags=pygame.BLEND_RGBA_MULT)
        p.blit(sombra, (self.ox + 6, self.oy + 10))
        p.blit(s, (self.ox, self.oy))
        p.blit(self.componer(), (self.ox, self.oy))
        self.chispas(p)
        self.herramienta(p)

    def chispas(self, p):
        for cx, cy, lv in self.celdas:
            if lv < 0.5:
                k = 4 + int(2 * math.sin(self.t * 5 + cx * 0.1 + cy * 0.07))
                pygame.draw.circle(p, self.color_chispa, (self.ox + cx, self.oy + cy), k)
                pygame.draw.circle(p, (120, 90, 60), (self.ox + cx, self.oy + cy), k, 1)

    color_chispa = (255, 255, 255)


@paso("untar")
class Untar(_Cubrir):
    """Espatula repartiendo mantequilla / queso crema / mermelada / crema de cacao sobre pan o base."""

    msg_fin = "¡Qué rico se ve!"
    color_chispa = (255, 255, 255)

    def iniciar_cub(self):
        self.titulo = "¡Unta %s!" % _nombre(self.ing, "lo que sigue")
        self.pista = "Pasa la espátula por toda la superficie"
        self.radio = (74 - 2.5 * self.d) * self.mods.alc
        self.color_chispa = aclarar(self.color, 0.3) if sum(self.color) < 600 else (200, 160, 110)

    def mover(self, dt, loc, prev):
        r = self.radio * (1 + 0.15 * self.mods.pot - 0.15)
        pts = self.muestras(prev, loc, r)
        for q in pts:
            self.tocar(q.x, q.y, r, dt * self.mods.pot / self.TC / len(pts))
        # la capa se pinta segun cuanto se cubrio cada celda (se va espesando con cada pasada)
        c = self.color
        self.capa.fill((0, 0, 0, 0))
        cl = aclarar(c, 0.35)
        rc = int(self.CS * 0.78)
        for cx, cy, lv in self.celdas:
            if lv > 0.02:
                pygame.draw.circle(self.capa, (*c, int(255 * min(1.0, lv * 1.4))), (int(cx), int(cy)), rc)
        for cx, cy, lv in self.celdas:
            if lv >= 0.99:
                pygame.draw.circle(self.capa, (*cl, 255), (int(cx - 5), int(cy - 5)), 4)
        self.suc = True

    def herramienta(self, p):
        pos = self.cur
        if _herr_ext(p, "espatula", pos.x, pos.y, 170, 0.0):
            return
        ang = -math.radians(50)
        blade = _rot([(0, -6), (16, -24), (105, -24), (105, 24), (16, 24), (0, 6)], ang, pos.x, pos.y)
        pygame.draw.polygon(p, (212, 218, 230), blade)
        pygame.draw.polygon(p, (110, 120, 140), blade, 3)
        shaft = _rot([(105, -4), (140, -4), (140, 4), (105, 4)], ang, pos.x, pos.y)
        pygame.draw.polygon(p, (150, 156, 170), shaft)
        mango = _rot([(140, -11), (240, -11), (240, 11), (140, 11)], ang, pos.x, pos.y)
        pygame.draw.polygon(p, (225, 80, 80), mango)
        pygame.draw.polygon(p, (140, 40, 50), mango, 3)
        # untadito en la punta
        pygame.draw.circle(p, self.color, (int(pos.x), int(pos.y)), 9)


@paso("espolvorear")
class Espolvorear(_Cubrir):
    """Salero, cernidor de harina o canela: mover sobre la superficie cubriendola de granitos."""

    msg_fin = "¡Todo espolvoreado!"
    K_TC = 340.0
    color_chispa = (255, 255, 255)

    def iniciar_cub(self):
        ing = self.ing
        self.titulo = "¡Espolvorea %s!" % _nombre(ing, "por encima")
        self.pista = "Mueve el " + ("cernidor" if self.cernidor else "salero") + " sobre la comida"
        self.radio = (84 - 3 * self.d) * self.mods.alc
        self.granos = []
        rnd = random.Random(5)
        self.rnd = rnd
        self.color_chispa = (255, 255, 255)

    @property
    def cernidor(self):
        return self.herr == "cernidor" or (self.herr != "salero" and self.ing in ("harina", "azucar", "azucar_glas", "cacao"))

    def mover(self, dt, loc, prev):
        r = self.radio
        pts = self.muestras(prev, loc, r)
        ritmo = 1.0 + 0.5 * (self.mods.pot - 1)
        for q in pts:
            self.tocar(q.x, q.y, r, dt * ritmo / self.TC / len(pts))
        c = self.color
        w, h = self.capa.get_size()
        for _ in range(7):
            a = self.rnd.random() * math.tau
            d = self.rnd.random() ** 0.5 * r
            x, y = loc.x + d * math.cos(a), loc.y + d * math.sin(a)
            if 0 <= x < w and 0 <= y < h:
                tono = self.rnd.choice((c, aclarar(c, 0.3), oscurecer(c, 0.12)))
                pygame.draw.circle(self.capa, (*tono, 255), (int(x), int(y)), self.rnd.choice((2, 3, 3, 4)))
                self.suc = True
            if self.rnd.random() < 0.5 and len(self.granos) < 90:
                self.granos.append([self.cur.x + self.rnd.uniform(-20, 20), self.cur.y - 70, 0.0, self.cur.y + self.rnd.uniform(-r * 0.5, r * 0.5)])
        nuevos = []
        for g in self.granos:
            g[2] += 900 * dt
            g[1] += g[2] * dt
            if g[1] < g[3]:
                nuevos.append(g)
        self.granos = nuevos

    def herramienta(self, p):
        pos = self.cur
        for g in self.granos:
            pygame.draw.circle(p, self.color, (int(g[0]), int(g[1])), 3)
            pygame.draw.circle(p, (140, 110, 80), (int(g[0]), int(g[1])), 3, 1)
        if _herr_ext(p, "cernidor" if self.cernidor else "salero", pos.x, pos.y - 80, 130, 0.0):
            return
        x, y = int(pos.x), int(pos.y) - 80
        if self.cernidor:
            pygame.draw.polygon(p, (205, 210, 222), [(x - 62, y - 30), (x + 62, y - 30), (x + 38, y + 24), (x - 38, y + 24)])
            for i in range(-2, 3):
                pygame.draw.line(p, (150, 156, 175), (x + i * 18, y - 24), (x + i * 11, y + 20), 2)
            pygame.draw.polygon(p, (150, 156, 175), [(x - 62, y - 30), (x + 62, y - 30), (x + 38, y + 24), (x - 38, y + 24)], 3)
            pygame.draw.rect(p, (225, 80, 80), (x + 55, y - 50, 90, 16), border_radius=8)
            pygame.draw.polygon(p, (205, 210, 222), [(x + 58, y - 32), (x + 70, y - 32), (x + 50, y - 10)])
        else:
            pygame.draw.polygon(p, (235, 245, 252), [(x - 30, y - 70), (x + 30, y - 70), (x + 36, y + 14), (x - 36, y + 14)])
            pygame.draw.polygon(p, self.color if sum(self.color) < 740 else (245, 245, 250), [(x - 30, y - 30), (x + 30, y - 30), (x + 36, y + 14), (x - 36, y + 14)])
            pygame.draw.polygon(p, (120, 140, 170), [(x - 30, y - 70), (x + 30, y - 70), (x + 36, y + 14), (x - 36, y + 14)], 3)
            pygame.draw.rect(p, (210, 80, 80), (x - 38, y + 10, 76, 22), border_radius=8)
            for dx in (-18, 0, 18):
                pygame.draw.circle(p, (60, 40, 40), (x + dx, y + 21), 3)


# ============================================================================= DECORAR
PATRONES = ("ondas", "corazon", "estrella", "espiral", "guirnalda", "zigzag")


def _en_poli(verts, u, cerrado):
    n = len(verts)
    seg = n if cerrado else n - 1
    f = u * seg
    i = int(f) % n if cerrado else min(int(f), seg - 1)
    t = f - int(f) if not (not cerrado and int(f) >= seg) else 1.0
    a, b = verts[i], verts[(i + 1) % n]
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def punto_patron(nombre, u):
    """Punto unitario (-1..1) del patron en u (0..1)."""
    if nombre == "ondas":
        return (-1 + 2 * u, 0.4 * math.sin(2 * math.pi * 2 * u))
    if nombre == "corazon":
        t = 2 * math.pi * u
        return (math.sin(t) ** 3 * 1.0,
                -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16 - 0.1)
    if nombre == "estrella":
        v = [(math.cos(-math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45),
              math.sin(-math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45)) for i in range(10)]
        return _en_poli(v, u, True)
    if nombre == "espiral":
        r = 1 - 0.85 * u
        a = 2 * math.pi * 2.2 * u
        return (r * math.cos(a), r * math.sin(a))
    if nombre == "zigzag":
        v = [(-1 + 2 * i / 8, (-0.45 if i % 2 == 0 else 0.45)) for i in range(9)]
        return _en_poli(v, u, False)
    return (math.sin(2 * math.pi * u), -math.cos(2 * math.pi * u))     # guirnalda


@paso("decorar")
class Decorar(PasoMasa):
    """Manga pastelera: seguir los puntos en orden dibujando el adorno."""

    def iniciar(self):
        d = self.dif / 10
        self.d = d
        self.titulo = "¡Decora con la manga!"
        self.pista = "Lleva la punta de la manga al punto que brilla y espera"
        self.sobre = self.spec.get("sobre") or self.ing or "galleta"
        if self.sobre in ("pan", "pan_rebanado", "bizcocho"):
            self.sobre = "galleta"
        self.surf, _tipo, self.mascara = superficie(self.sobre)
        self.ox = CX - self.surf.get_width() // 2
        self.oy = CY - self.surf.get_height() // 2
        self.patron = self.spec.get("patron") or PATRONES[_hash(self.ing or self.sobre) % len(PATRONES)]
        n = 34 + round(d)
        cerrado = self.patron in ("corazon", "estrella", "guirnalda")
        S = 165
        self.pts = []
        for i in range(n):
            u = i / n if cerrado else i / (n - 1)
            x, y = punto_patron(self.patron, u)
            self.pts.append((CX + S * x, CY + S * y))
        sp = min(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(self.pts, self.pts[1:]))
        self.radio = max(24.0, min(54 - 2 * d, 0.62 * sp)) * self.mods.alc
        self.espera = 1.0
        self.dw = 0.0
        self.k = 0
        self.hits = 0
        self.crema = self.spec.get("color") or (_color(self.ing) if self.ing in ("crema", "crema_cacao", "chocolate", "mermelada", "glaseado")
                                                 else (255, 170, 205))
        if self.sobre in ("crema_cacao", "chocolate"):
            self.crema = (255, 170, 205)
        self.pos = V2(CX, CY)

    def tiempo_base(self):
        return 55.0

    def actualizar_paso(self, dt, ctrl):
        self.pos = V2(ctrl.pos)
        if self.k < len(self.pts):
            x, y = self.pts[self.k]
            # el punto de accion es la BOQUILLA: ctrl.pos es exactamente la punta de la manga
            if math.hypot(ctrl.pos.x - x, ctrl.pos.y - y) < self.radio:
                self.dw += dt * (4.0 if ctrl.clic else 1.0) * max(0.5, self.mods.pot)
                if self.dw >= self.espera:
                    self.dw = 0.0
                    self.k += 1
                    self.hits += 1
                    self.avanzar(1.0 / len(self.pts))
                    self.sumar_particulas(x, y, self.crema, 6)
            else:
                self.dw = max(0.0, self.dw - dt * 2)
        if self.k >= len(self.pts) or self.prog >= 0.999:
            self.terminar(1.0, "¡Qué bonito adorno!")

    def dibujar_escena(self, p):
        s = self.surf
        sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        sombra.blit(self.mascara, (0, 0))
        sombra.fill((90, 60, 40, 70), special_flags=pygame.BLEND_RGBA_MULT)
        p.blit(sombra, (self.ox + 6, self.oy + 10))
        p.blit(s, (self.ox, self.oy))
        c = self.crema
        for i, (x, y) in enumerate(self.pts):
            if i < self.k:
                if i > 0:
                    a = self.pts[i - 1]
                    pygame.draw.line(p, c, (int(a[0]), int(a[1])), (int(x), int(y)), 10)
                pygame.draw.circle(p, c, (int(x), int(y)), 11)
                pygame.draw.circle(p, aclarar(c, 0.55), (int(x - 3), int(y - 3)), 4)
                pygame.draw.circle(p, oscurecer(c, 0.3), (int(x), int(y)), 11, 2)
            elif i == self.k:
                r = int(self.radio * 0.55 + 4 * math.sin(self.t * 6))
                pygame.draw.circle(p, (255, 255, 255), (int(x), int(y)), r + 5, 4)
                pygame.draw.circle(p, (255, 160, 70), (int(x), int(y)), r, 5)
                fr = min(1.0, self.dw / self.espera)
                pygame.draw.circle(p, c, (int(x), int(y)), 4 + int(8 * fr))
                pygame.draw.circle(p, (255, 160, 70), (int(x), int(y)), 4 + int(8 * fr), 2)
            else:
                pygame.draw.circle(p, (255, 255, 255), (int(x), int(y)), 5)
                pygame.draw.circle(p, (150, 110, 80), (int(x), int(y)), 5, 2)
        # manga propia (no el arte externo, que se centra): la BOQUILLA cae exactamente en ctrl.pos
        pos = self.pos
        ang = -math.radians(62)
        bolsa = _rot([(34, -17), (34, 17), (210, 70), (230, 0), (210, -70)], ang, pos.x, pos.y)
        pygame.draw.polygon(p, (250, 248, 240), bolsa)
        pygame.draw.polygon(p, c, _rot([(34, -17), (34, 17), (120, 42), (120, -42)], ang, pos.x, pos.y))
        pygame.draw.polygon(p, (140, 130, 130), bolsa, 3)
        boq = _rot([(0, -3), (0, 3), (36, 17), (36, -17)], ang, pos.x, pos.y)
        pygame.draw.polygon(p, (245, 205, 90), boq)
        pygame.draw.polygon(p, (150, 110, 40), boq, 2)
        if self.k < len(self.pts) and self.dw > 0:
            pygame.draw.circle(p, c, (int(pos.x), int(pos.y)), 3 + int(7 * self.dw / self.espera))
        pygame.draw.circle(p, (255, 255, 255), (int(pos.x), int(pos.y)), 4)
        pygame.draw.circle(p, (150, 110, 40), (int(pos.x), int(pos.y)), 4, 1)
