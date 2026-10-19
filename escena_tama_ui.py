"""Piezas de interfaz de la escena Tamagotchi: botones con icono, barras bonitas, particulas y efectos.

Solo dibujo y utilidades (sin logica de juego). Las usa escena_tama.py.
"""

import math
import random

import pygame

import arte_tama as AT
from ajustes import ANCHO, ALTO
from arte_tama_fx import glow, destello_estrella
from nucleo import Boton, aclarar, oscurecer, escribir, corazon, estrella

V2 = pygame.Vector2

_fuentes = {}


def fuente(tam, negrita=True):
    k = (int(tam), bool(negrita))
    f = _fuentes.get(k)
    if f is None:
        f = pygame.font.SysFont("arial", int(tam), bold=negrita)
        _fuentes[k] = f
    return f


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def mezcla(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def ease_out_back(f):
    f = clamp(f)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (f - 1) ** 3 + c1 * (f - 1) ** 2


# ---------------------------------------------------------------- texto
def ajustar(fuente_base_tam, texto, ancho, minimo=14, negrita=True):
    """Fuente mas grande (hasta fuente_base_tam) con la que 'texto' cabe en 'ancho'."""
    tam = fuente_base_tam
    while tam > minimo and fuente(tam, negrita).size(texto)[0] > ancho:
        tam -= 1
    return fuente(tam, negrita)


def lineas_de(fnt, texto, ancho):
    palabras = str(texto).split()
    lineas, actual = [], ""
    for w in palabras:
        prueba = (actual + " " + w).strip()
        if fnt.size(prueba)[0] > ancho and actual:
            lineas.append(actual)
            actual = w
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas


def escribir_parrafo(p, fnt, texto, cx, y, ancho, color=(255, 255, 255), contorno=(30, 30, 50), inter=None,
                     grosor=2, max_lineas=6):
    inter = inter or fnt.get_linesize() + 2
    ls = lineas_de(fnt, texto, ancho)[:max_lineas]
    for i, l in enumerate(ls):
        escribir(p, fnt, l, cx, y + i * inter, color, contorno=contorno, grosor=grosor)
    return len(ls) * inter


def pastilla(p, fnt, texto, cx, cy, fondo=(255, 255, 255), color=(60, 50, 90), borde=None, pad=22, alto=44, alfa=235):
    ancho = fnt.size(texto)[0] + pad * 2
    r = pygame.Rect(0, 0, ancho, alto)
    r.center = (int(cx), int(cy))
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(s, fondo + (alfa,), s.get_rect(), border_radius=alto // 2)
    pygame.draw.rect(s, (borde or oscurecer(fondo, 0.45)) + (255,), s.get_rect(), 3, border_radius=alto // 2)
    p.blit(s, r.topleft)
    escribir(p, fnt, texto, r.centerx, r.centery, color, contorno=None)
    return r


# ---------------------------------------------------------------- formas sueltas
def moneda(p, x, y, r=14):
    pygame.draw.circle(p, (190, 130, 20), (x, y + 2), r)
    pygame.draw.circle(p, (255, 205, 60), (x, y), r)
    pygame.draw.circle(p, (255, 235, 140), (x, y), max(2, int(r * 0.68)), max(2, r // 6))
    pygame.draw.circle(p, (255, 245, 190), (x - r // 3, y - r // 3), max(2, r // 5))


def trofeo(p, cx, cy, tam):
    """Copa dorada (icono del Salon)."""
    s = tam / 64.0
    oro, borde, claro = (255, 205, 60), (150, 100, 20), (255, 240, 160)

    def P(x, y):
        return (cx + x * s, cy + y * s)
    for lado in (-1, 1):                       # asas
        pygame.draw.arc(p, borde, (cx + (lado * 24 - 12) * s, cy - 24 * s, 24 * s, 28 * s),
                        (-math.pi / 2 if lado > 0 else math.pi / 2), (math.pi / 2 if lado > 0 else 3 * math.pi / 2),
                        max(3, int(5 * s)))
    copa = [P(-22, -26), P(22, -26), P(18, -2), P(8, 10), P(-8, 10), P(-18, -2)]
    pygame.draw.polygon(p, oro, copa)
    pygame.draw.polygon(p, borde, copa, max(2, int(3 * s)))
    pygame.draw.polygon(p, claro, [P(-15, -22), P(-8, -22), P(-6, -4), P(-12, -4)])
    pygame.draw.rect(p, oro, (cx - 5 * s, cy + 9 * s, 10 * s, 12 * s))
    pygame.draw.rect(p, borde, (cx - 5 * s, cy + 9 * s, 10 * s, 12 * s), max(2, int(2 * s)))
    pygame.draw.rect(p, oro, (cx - 16 * s, cy + 20 * s, 32 * s, 8 * s), border_radius=int(3 * s))
    pygame.draw.rect(p, borde, (cx - 16 * s, cy + 20 * s, 32 * s, 8 * s), max(2, int(2 * s)), border_radius=int(3 * s))
    estrella(p, int(cx), int(cy - 12 * s), max(4, int(8 * s)), (255, 250, 220), (200, 150, 40))


def flecha(p, cx, cy, tam, lado=1, color=(255, 255, 255), borde=(60, 60, 90)):
    pts = [(cx - lado * tam * 0.5, cy - tam * 0.7), (cx + lado * tam * 0.6, cy), (cx - lado * tam * 0.5, cy + tam * 0.7)]
    pygame.draw.polygon(p, color, pts)
    pygame.draw.polygon(p, borde, pts, 3)


# ---------------------------------------------------------------- barras
_grad_cache = {}


def _grad(w, h, c0, c1):
    k = (w, h, c0, c1)
    s = _grad_cache.get(k)
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):
            pygame.draw.line(s, mezcla(c0, c1, x / max(1, w - 1)), (x, 0), (x, h))
        _grad_cache[k] = s
    return s


def barra_bonita(p, rect, frac, c0, c1, fondo=(52, 56, 88), borde=(255, 255, 255), titilar=0.0):
    """Barra redondeada con degradado y brillo. titilar 0..1 aclara el relleno (aviso suave)."""
    rect = pygame.Rect(rect)
    h = rect.h
    rad = h // 2
    pygame.draw.rect(p, (20, 22, 45), rect.move(0, 3), border_radius=rad)
    pygame.draw.rect(p, fondo, rect, border_radius=rad)
    frac = clamp(frac)
    ancho_total = rect.w - 4
    fh = h - 4
    fw = int(ancho_total * frac)
    if fw > 0:
        fw = max(fw, fh)
        tmp = pygame.Surface((fw, fh), pygame.SRCALPHA)
        tmp.blit(_grad(ancho_total, fh, c0, c1), (0, 0), area=(0, 0, fw, fh))
        pygame.draw.rect(tmp, (255, 255, 255, 80), (fh // 3, 2, max(2, fw - fh * 2 // 3), max(2, fh // 4)),
                         border_radius=fh // 8)
        if titilar > 0:
            tmp.fill((int(90 * titilar),) * 3 + (0,), special_flags=pygame.BLEND_RGB_ADD)
        m = pygame.Surface((fw, fh), pygame.SRCALPHA)
        pygame.draw.rect(m, (255, 255, 255, 255), m.get_rect(), border_radius=fh // 2)
        tmp.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        p.blit(tmp, (rect.x + 2, rect.y + 2))
    pygame.draw.rect(p, borde, rect, 2, border_radius=rad)


def tarjeta(p, rect, color=(255, 255, 255), alfa=225, radio=24, borde=(110, 90, 140), grosor=3, sombra=True):
    rect = pygame.Rect(rect)
    if sombra:
        s = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 10, 40, 70), (6, 8, rect.w, rect.h), border_radius=radio)
        p.blit(s, (rect.x - 6, rect.y - 2))
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, color + (alfa,), s.get_rect(), border_radius=radio)
    pygame.draw.rect(s, borde + (255,), s.get_rect(), grosor, border_radius=radio)
    p.blit(s, rect.topleft)


def velo(p, alfa=120, color=(20, 15, 40)):
    s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    s.fill(color + (int(alfa),))
    p.blit(s, (0, 0))


def flash(p, a, color=(255, 250, 225)):
    if a <= 0.01:
        return
    s = pygame.Surface((ANCHO, ALTO))
    s.fill(color)
    s.set_alpha(int(255 * min(1.0, a)))
    p.blit(s, (0, 0))


# ---------------------------------------------------------------- boton con icono
class BotonTama(Boton):
    """Boton grande con icono (nombre de accion de arte_tama o funcion f(p, cx, cy, tam)) y etiqueta.
    El progreso de permanencia se ve como un relleno que sube dentro del boton."""

    def __init__(self, rect, texto, color, icono=None, vertical=True, tam_icono=52, pulso=False, tam_texto=22):
        super().__init__(rect, texto, color)
        self.icono = icono
        self.vertical = vertical
        self.tam_icono = tam_icono
        self.pulso = pulso
        self.tam_texto = tam_texto
        self.visible = True

    def _icono(self, p, cx, cy):
        if self.icono is None:
            return
        if callable(self.icono):
            self.icono(p, cx, cy, self.tam_icono)
        else:
            AT.dibujar_icono_accion(p, self.icono, cx, cy, self.tam_icono, self.activo)

    def dibujar(self, p, fuente_ignorada=None, t=0.0):
        r = pygame.Rect(self.rect)
        base = self.color if self.activo else (150, 155, 172)
        if self.encima:
            base = aclarar(base, 0.2)
        if self.pulso and self.activo:
            k = 1 + 0.045 * math.sin(t * 5.5)
            r = r.inflate(int(r.w * (k - 1)), int(r.h * (k - 1)))
            glow(p, r.centerx, r.centery, r.w * 0.75, (255, 215, 90), int(95 + 50 * math.sin(t * 5.5)))
        rad = 22
        pygame.draw.rect(p, oscurecer(base, 0.55), r.move(0, 6), border_radius=rad)
        pygame.draw.rect(p, base, r, border_radius=rad)
        # brillo superior
        brillo = pygame.Surface((r.w - 16, r.h // 2 - 6), pygame.SRCALPHA)
        pygame.draw.rect(brillo, (255, 255, 255, 60), brillo.get_rect(), border_radius=rad - 6)
        p.blit(brillo, (r.x + 8, r.y + 6))
        # progreso de permanencia
        if self.dwell > 0:
            from ajustes import DWELL_SEG
            f = clamp(self.dwell / DWELL_SEG)
            alto = int(r.h * f)
            if alto > 2:
                s = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 255, 255, 120), s.get_rect(), border_radius=rad)
                p.blit(s, (r.x, r.y + r.h - alto), area=(0, r.h - alto, r.w, alto))
        borde = (255, 226, 110) if (self.pulso and self.activo) else (255, 255, 255)
        pygame.draw.rect(p, borde, r, 4, border_radius=rad)
        cont = oscurecer(base, 0.62)
        if self.vertical:
            self._icono(p, r.centerx, r.y + int(r.h * 0.38))
            fnt = ajustar(self.tam_texto, self.texto, r.w - 14, 14)
            escribir(p, fnt, self.texto, r.centerx, r.y + int(r.h * 0.82), (255, 255, 255), contorno=cont)
        else:
            pad = 14
            if self.icono is not None:
                self._icono(p, r.x + pad + self.tam_icono // 2, r.centery)
                x0 = r.x + pad * 2 + self.tam_icono
            else:
                x0 = r.x + pad
            fnt = ajustar(self.tam_texto, self.texto, r.right - pad - x0, 14)
            escribir(p, fnt, self.texto, (x0 + r.right - pad) / 2, r.centery, (255, 255, 255), contorno=cont)


# ---------------------------------------------------------------- particulas
_burbujas = {}


def _burbuja(r):
    r = max(3, int(r))
    s = _burbujas.get(r)
    if s is None:
        s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        c = (r + 2, r + 2)
        pygame.draw.circle(s, (190, 230, 255, 70), c, r)
        pygame.draw.circle(s, (255, 255, 255, 220), c, r, max(1, r // 6))
        pygame.draw.circle(s, (255, 255, 255, 230), (c[0] - r // 3, c[1] - r // 3), max(1, r // 4))
        _burbujas[r] = s
    return s


class Parts:
    """Particulas decorativas de la escena (corazones, chispas, burbujas, zzz, migajas, calor)."""

    def __init__(self, rng=None):
        self.l = []
        self.rng = rng or random.Random()

    def _add(self, kind, x, y, vx, vy, vida, tam, col=(255, 255, 255), g=0.0, **kw):
        d = dict(k=kind, x=x, y=y, vx=vx, vy=vy, vida=vida, t=0.0, tam=tam, col=col, g=g)
        d.update(kw)
        self.l.append(d)
        if len(self.l) > 400:
            del self.l[:50]

    def corazon(self, x, y, tam=16):
        r = self.rng
        self._add("corazon", x + r.uniform(-14, 14), y, r.uniform(-25, 25), r.uniform(-90, -60), 1.6, tam,
                  col=r.choice([(235, 70, 100), (255, 120, 150), (255, 90, 120)]))

    def chispa(self, x, y, col=(255, 235, 150), tam=10, vel=90, vida=0.9, g=0.0):
        r = self.rng
        a = r.uniform(0, math.tau)
        v = r.uniform(vel * 0.3, vel)
        self._add("chispa", x, y, math.cos(a) * v, math.sin(a) * v, vida * r.uniform(0.7, 1.2), tam, col=col, g=g)

    def calor(self, x, y):
        r = self.rng
        self._add("chispa", x + r.uniform(-12, 12), y + r.uniform(-8, 8), r.uniform(-20, 20), r.uniform(-120, -50),
                  r.uniform(0.7, 1.3), r.uniform(7, 14), col=r.choice([(255, 190, 80), (255, 150, 60), (255, 230, 130)]))

    def burbuja(self, x, y, r_=None):
        r = self.rng
        self._add("burbuja", x, y, r.uniform(-30, 30), r.uniform(-90, -30), r.uniform(1.0, 1.9), r_ or r.uniform(6, 20),
                  ola=r.uniform(0, 6))

    def zzz(self, x, y):
        self._add("zzz", x, y, 14, -34, 2.6, 30, col=(210, 225, 255), ola=self.rng.uniform(0, 6))

    def migaja(self, x, y, col=(235, 190, 110)):
        r = self.rng
        self._add("migaja", x, y, r.uniform(-90, 90), r.uniform(-170, -70), 0.8, r.uniform(3, 6), col=col, g=520)

    def estrella(self, x, y, col=(255, 225, 90), tam=14):
        r = self.rng
        a = r.uniform(0, math.tau)
        v = r.uniform(60, 240)
        self._add("estrella", x, y, math.cos(a) * v, math.sin(a) * v - 80, r.uniform(0.9, 1.5), tam, col=col, g=260)

    def confeti(self, x, y):
        r = self.rng
        a = r.uniform(-math.pi, 0)
        v = r.uniform(150, 420)
        col = r.choice([(255, 210, 60), (240, 90, 120), (90, 200, 240), (120, 220, 130), (200, 130, 240)])
        self._add("confeti", x, y, math.cos(a) * v, math.sin(a) * v, r.uniform(1.4, 2.4), r.uniform(5, 9), col=col, g=420,
                  rot=r.uniform(0, 6))

    def polvo(self, x, y):
        r = self.rng
        self._add("polvo", x, y, r.uniform(-30, 30), r.uniform(-45, -10), 0.9, r.uniform(9, 17))

    def cruz(self, x, y, col=(120, 230, 140)):
        r = self.rng
        self._add("cruz", x + r.uniform(-60, 60), y + r.uniform(-20, 20), r.uniform(-15, 15), r.uniform(-80, -40), 1.5,
                  r.uniform(9, 15), col=col)

    def actualizar(self, dt):
        vivas = []
        for d in self.l:
            d["t"] += dt
            if d["t"] >= d["vida"]:
                continue
            d["vy"] += d["g"] * dt
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            vivas.append(d)
        self.l = vivas

    def dibujar(self, p):
        for d in self.l:
            f = d["t"] / d["vida"]
            x, y, tam = d["x"], d["y"], d["tam"]
            k = d["k"]
            if k == "corazon":
                esc = clamp((1 - f) * 3) * clamp(f * 8 + 0.4)
                corazon(p, int(x + math.sin(d["t"] * 5) * 5), int(y), max(2, int(tam * esc)))
            elif k == "chispa":
                glow(p, x, y, tam * (1.2 - f * 0.6), d["col"], int(230 * (1 - f)))
            elif k == "burbuja":
                s = _burbuja(tam)
                s.set_alpha(int(255 * clamp((1 - f) * 2.5)))
                p.blit(s, s.get_rect(center=(int(x + math.sin(d["t"] * 4 + d["ola"]) * 8), int(y))))
            elif k == "zzz":
                fnt = fuente(int(tam * (0.7 + f * 0.7)))
                escribir(p, fnt, "Z", x + math.sin(d["t"] * 3 + d["ola"]) * 10, y, d["col"], contorno=(40, 50, 110),
                         grosor=2)
            elif k == "migaja":
                pygame.draw.circle(p, d["col"], (int(x), int(y)), max(1, int(tam * (1 - f))))
            elif k == "estrella":
                estrella(p, int(x), int(y), max(3, int(tam * (1 - f * 0.6))), d["col"], oscurecer(d["col"], 0.5))
            elif k == "confeti":
                w = max(2, int(tam))
                s = pygame.Surface((w, w * 2), pygame.SRCALPHA)
                s.fill(d["col"] + (255,))
                s = pygame.transform.rotate(s, d["rot"] * 60 + d["t"] * 300)
                s.set_alpha(int(255 * clamp((1 - f) * 3)))
                p.blit(s, s.get_rect(center=(int(x), int(y))))
            elif k == "polvo":
                rr = int(tam * (0.6 + f * 1.1))
                s = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (165, 140, 110, int(150 * (1 - f))), (rr + 1, rr + 1), rr)
                pygame.draw.circle(s, (205, 185, 155, int(110 * (1 - f))), (rr, rr), max(1, rr // 2))
                p.blit(s, (int(x - rr), int(y - rr)))
            elif k == "cruz":
                a = int(255 * clamp((1 - f) * 2.5))
                c = d["col"]
                w = max(3, int(tam))
                s = pygame.Surface((w * 3, w * 3), pygame.SRCALPHA)
                pygame.draw.rect(s, c + (a,), (w, 0, w, w * 3), border_radius=w // 3)
                pygame.draw.rect(s, c + (a,), (0, w, w * 3, w), border_radius=w // 3)
                p.blit(s, s.get_rect(center=(int(x), int(y))))


# ---------------------------------------------------------------- siluetas
def silueta_blanca(especie, etapa, escala=1.0, lado=700):
    """Silueta blanca de una mascota (para la cinematica de evolucion). Centrada en la superficie."""
    s = pygame.Surface((lado, lado), pygame.SRCALPHA)
    AT.dibujar_mascota(s, especie, etapa, lado / 2, lado / 2, escala, 0.0, "normal", 1, False)
    m = pygame.mask.from_surface(s, 60)
    return m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


_mask_cache = {}
_over_cache = {}
MARGEN = 34


def _mascara(esp, et, esc, dir):
    """Mascara del cuerpo de la mascota (cacheada): (mascara, rect_en_lienzo, lienzo)."""
    k = (esp, int(et), round(esc, 2), int(dir))
    r = _mask_cache.get(k)
    if r is None:
        if len(_mask_cache) > 40:
            _mask_cache.clear()
            _over_cache.clear()
        lado = 640
        s = pygame.Surface((lado, lado), pygame.SRCALPHA)
        AT.dibujar_mascota(s, esp, et, lado / 2, lado / 2, esc, 0.5, "normal", dir)
        m = pygame.mask.from_surface(s, 150)
        rect = s.get_bounding_rect(min_alpha=150)
        if rect.w < 8 or rect.h < 8:
            rect = pygame.Rect(lado // 2 - 30, lado // 2 - 30, 60, 60)
        r = (m, rect, lado)
        _mask_cache[k] = r
    return r


def overlay_mascota(esp, et, esc, dir, tipo, nivel=1):
    """Manchas de polvo ('polvo', nivel 1..4) o espuma ('espuma') ajustadas al cuerpo.
    Devuelve (superficie, (dx, dy)): blit en (cx + dx, cy + dy), con (cx, cy) = centro del cuerpo."""
    k = (esp, int(et), round(esc, 2), int(dir), tipo, int(nivel))
    r = _over_cache.get(k)
    if r is not None:
        return r
    m, rect, lado = _mascara(esp, et, esc, dir)
    import zlib
    rng = random.Random(zlib.crc32(("%s%d%s%d" % (esp, et, tipo, nivel)).encode()))
    M = MARGEN
    surf = pygame.Surface((rect.w + 2 * M, rect.h + 2 * M), pygame.SRCALPHA)

    def dentro(x, y, d=5):
        for ox, oy in ((0, 0), (d, 0), (-d, 0), (0, d), (0, -d)):
            xx, yy = int(x + ox), int(y + oy)
            if not (0 <= xx < lado and 0 <= yy < lado) or not m.get_at((xx, yy)):
                return False
        return True
    n = (5 * nivel + 3) if tipo == "polvo" else 46
    puestos, intentos = 0, 0
    while puestos < n and intentos < 900:
        intentos += 1
        x = rng.uniform(rect.x, rect.right)
        y = rng.uniform(rect.y, rect.bottom)
        if not dentro(x, y):
            continue
        puestos += 1
        lx, ly = x - rect.x + M, y - rect.y + M
        if tipo == "polvo":
            rad = rng.uniform(4, 10)
            col = rng.choice([(120, 92, 66), (140, 118, 92), (96, 80, 66)])
            pygame.draw.circle(surf, col + (118,), (lx, ly), rad)
            pygame.draw.circle(surf, (190, 165, 135, 90), (lx - rad * 0.3, ly - rad * 0.3), max(1, rad * 0.4))
            for _ in range(2):
                pygame.draw.circle(surf, col + (95,), (lx + rng.uniform(-14, 14), ly + rng.uniform(-14, 14)), rng.uniform(1.5, 3))
        else:
            rad = rng.uniform(11, 24)
            pygame.draw.circle(surf, (205, 228, 255, 255), (lx, ly), rad + 2)
            pygame.draw.circle(surf, (255, 255, 255, 255), (lx, ly), rad)
            pygame.draw.circle(surf, (225, 240, 255, 255), (lx + rad * 0.25, ly + rad * 0.3), rad * 0.55)
            pygame.draw.circle(surf, (255, 255, 255, 255), (lx - rad * 0.35, ly - rad * 0.35), max(2, rad * 0.25))
    if tipo == "polvo":                    # el polvo se recorta al cuerpo; la espuma sobresale un poco
        mk = m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        recorte = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        recorte.blit(mk, (M, M), area=rect)
        surf.blit(recorte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    r = (surf, (rect.x - lado / 2 - M, rect.y - lado / 2 - M))
    _over_cache[k] = r
    return r


def escoba(p, x, y, ang, tam=1.0):
    """Escoba con mango y cerdas. (x, y) = punta de las cerdas (centro), ang en radianes (0 = vertical)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(px, py):
        return (x + (px * ca - py * sa) * tam, y + (px * sa + py * ca) * tam)
    mango = [P(-5, -36), P(5, -36), P(4, -205), P(-4, -205)]
    pygame.draw.polygon(p, (176, 122, 66), mango)
    pygame.draw.polygon(p, (98, 62, 32), mango, 3)
    pygame.draw.line(p, (222, 176, 118), P(-1, -50), P(-1, -195), max(2, int(3 * tam)))
    pygame.draw.circle(p, (176, 122, 66), P(0, -208), int(7 * tam))
    pygame.draw.circle(p, (98, 62, 32), P(0, -208), int(7 * tam), 3)
    banda = [P(-19, -54), P(19, -54), P(21, -34), P(-21, -34)]
    pygame.draw.polygon(p, (225, 85, 85), banda)
    pygame.draw.polygon(p, (140, 40, 50), banda, 3)
    cerdas = [P(-19, -34), P(19, -34), P(38, 2), P(-38, 2)]
    pygame.draw.polygon(p, (238, 198, 96), cerdas)
    for k in range(-3, 4):
        pygame.draw.line(p, (196, 150, 62), P(k * 5.5, -33), P(k * 11, 0), max(2, int(2 * tam)))
    pygame.draw.polygon(p, (132, 92, 40), cerdas, 3)


_sil_cache = {}


def silueta_especie(especie, etapa, escala, lado=420, color=(70, 72, 96)):
    """Silueta oscura de una mascota al MISMO tamano que el dibujo real (para el '???' del cuaderno)."""
    k = (especie, int(etapa), round(escala, 3), color)
    s = _sil_cache.get(k)
    if s is None:
        tmp = pygame.Surface((lado, lado), pygame.SRCALPHA)
        AT.dibujar_mascota(tmp, especie, etapa, lado / 2, lado / 2, escala, 0.0, "normal", 1, False)
        m = pygame.mask.from_surface(tmp, 190)      # umbral alto: sin burbujas ni chispas sueltas
        s = m.to_surface(setcolor=color + (255,), unsetcolor=(0, 0, 0, 0))
        _sil_cache[k] = s
    return s


def pelota(p, x, y, r, ang, sombra_y=None):
    """Pelota de playa que rueda."""
    if sombra_y is not None:
        k = clamp(1 - (sombra_y - y) / 520.0, 0.25, 1.0)
        s = pygame.Surface((int(r * 2.4 * k) + 2, int(r * 0.6 * k) + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 70), s.get_rect())
        p.blit(s, s.get_rect(center=(int(x), int(sombra_y))))
    d = int(r * 2)
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    c = (r, r)
    cols = [(255, 90, 100), (255, 215, 80), (90, 190, 255), (255, 255, 255), (120, 220, 130), (255, 150, 60)]
    for i, col in enumerate(cols):
        a0 = ang + i * math.tau / 6
        pts = [c] + [(r + math.cos(a0 + j * math.tau / 36) * r * 1.2, r + math.sin(a0 + j * math.tau / 36) * r * 1.2)
                     for j in range(7)]
        pygame.draw.polygon(s, col + (255,), pts)
    m = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(m, (255, 255, 255, 255), c, r)
    s.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.circle(s, (60, 50, 90, 255), c, r, 3)
    pygame.draw.circle(s, (255, 255, 255, 255), c, max(3, r // 6))
    pygame.draw.circle(s, (255, 255, 255, 190), (int(r * 0.62), int(r * 0.58)), max(3, int(r * 0.2)))
    p.blit(s, s.get_rect(center=(int(x), int(y))))


# ---------------------------------------------------------------- curar: marcas, curitas, botiquin, icono de vida
_marcas_cache = {}


def marcas_mascota(esp, et, esc, dir, n=6, sep=62):
    """n puntos (dx, dy) sobre el cuerpo de la mascota, bien separados, relativos al centro del cuerpo.
    Deterministas por especie/etapa (cacheados)."""
    k = (esp, int(et), round(esc, 2), int(dir), int(n))
    r = _marcas_cache.get(k)
    if r is not None:
        return r
    m, rect, lado = _mascara(esp, et, esc, dir)
    import zlib
    rng = random.Random(zlib.crc32(("marcas%s%d%d" % (esp, et, n)).encode()))

    def dentro(x, y, d=14):
        for ox, oy in ((0, 0), (d, 0), (-d, 0), (0, d), (0, -d)):
            xx, yy = int(x + ox), int(y + oy)
            if not (0 <= xx < lado and 0 <= yy < lado) or not m.get_at((xx, yy)):
                return False
        return True
    cand = []
    for _ in range(1400):
        x = rng.uniform(rect.x, rect.right)
        y = rng.uniform(rect.y + rect.h * 0.18, rect.bottom - rect.h * 0.05)
        if dentro(x, y):
            cand.append((x, y))
    if len(cand) < n:
        cand += [(rect.centerx + rng.uniform(-30, 30), rect.centery + rng.uniform(-30, 30)) for _ in range(n)]
    elegidos = [cand[0]]
    while len(elegidos) < n:       # punto mas lejano de los ya elegidos (reparto parejo)
        mejor = max(cand, key=lambda c: min((c[0] - e[0]) ** 2 + (c[1] - e[1]) ** 2 for e in elegidos))
        elegidos.append(mejor)
    rng.shuffle(elegidos)
    r = [(x - lado / 2, y - lado / 2) for x, y in elegidos]
    if len(_marcas_cache) > 80:
        _marcas_cache.clear()
    _marcas_cache[k] = r
    return r


_marca_sup = {}


def _marca_surf(tipo):
    s = _marca_sup.get(tipo)
    if s is None:
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        c = (40, 40)
        if tipo == "moreton":
            pygame.draw.ellipse(s, (96, 70, 150, 235), (11, 16, 58, 48))
            pygame.draw.ellipse(s, (140, 104, 205, 235), (17, 20, 42, 32))
            pygame.draw.ellipse(s, (255, 255, 255, 120), (22, 24, 16, 9))
            pygame.draw.ellipse(s, (60, 40, 100, 255), (11, 16, 58, 48), 3)
            for dx, dy in ((-6, -2), (6, 3)):                   # cara llorosa tierna: dos puntitos
                pygame.draw.circle(s, (60, 40, 100, 255), (c[0] + dx, c[1] + dy), 2)
        else:                                                    # raspon: parche rosado con aranazos suaves
            pygame.draw.ellipse(s, (255, 196, 190, 240), (12, 16, 56, 48))
            pygame.draw.ellipse(s, (255, 222, 214, 240), (20, 22, 34, 22))
            for k in range(3):
                x = 26 + k * 13
                pygame.draw.line(s, (214, 96, 104, 255), (x + 5, 24), (x - 5, 56), 3)
            pygame.draw.circle(s, (214, 96, 104, 255), (56, 30), 2)
            pygame.draw.circle(s, (214, 96, 104, 255), (22, 52), 2)
            pygame.draw.ellipse(s, (205, 105, 112, 255), (12, 16, 56, 48), 3)
        _marca_sup[tipo] = s
    return s


def dibujar_marca(p, x, y, tipo, t, esc=1.0, alfa=255):
    """Marca cartoon (moreton o raspon) que late suave para llamar la atencion. Centro en (x, y)."""
    pulso = 1 + 0.07 * math.sin(t * 5)
    s = _marca_surf(tipo)
    k = 1.15 * esc * pulso
    if abs(k - 1) > 0.01:
        s = pygame.transform.smoothscale(s, (max(2, int(80 * k)), max(2, int(80 * k))))
    else:
        s = s.copy()
    if alfa < 255:
        s.set_alpha(alfa)
    p.blit(s, s.get_rect(center=(int(x), int(y))))


def curita(p, x, y, ang=0.0, tam=1.0, alfa=255):
    """Curita (tirita) rojiza suave con almohadilla blanca. Centro en (x, y), ang en radianes."""
    w, h = 78, 32
    s = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    r = pygame.Rect(2, 2, w, h)
    pygame.draw.rect(s, (255, 168, 160, 255), r, border_radius=14)
    pygame.draw.rect(s, (255, 205, 200, 255), r.inflate(-6, -18).move(0, -5), border_radius=7)
    pad = pygame.Rect(0, 0, 30, h - 4)
    pad.center = r.center
    pygame.draw.rect(s, (255, 244, 238, 255), pad, border_radius=7)
    for dx in (-3, 3):
        for dy in (-7, 0, 7):
            pygame.draw.circle(s, (240, 190, 185, 255), (pad.centerx + dx, pad.centery + dy), 1)
    for dx in (-28, 28):
        for dy in (-6, 6):
            pygame.draw.circle(s, (255, 130, 135, 255), (r.centerx + dx, r.centery + dy), 2)
    pygame.draw.rect(s, (205, 95, 105, 255), r, 3, border_radius=14)
    s = pygame.transform.rotozoom(s, -math.degrees(ang), tam)
    if alfa < 255:
        s.set_alpha(alfa)
    p.blit(s, s.get_rect(center=(int(x), int(y))))


def botiquin(p, x, y, tam=1.0, t=0.0):
    """Botiquin pequeno: maletin blanco con cruz roja y asa. Centro en (x, y)."""
    y = y + math.sin(t * 2.5) * 4
    w, h = int(104 * tam), int(78 * tam)
    r = pygame.Rect(0, 0, w, h)
    r.center = (int(x), int(y))
    asa = pygame.Rect(0, 0, int(40 * tam), int(26 * tam))
    asa.midbottom = (r.centerx, r.y + 4)
    pygame.draw.rect(p, (150, 150, 175), asa, 5, border_radius=10)
    pygame.draw.rect(p, (180, 175, 205), r.move(0, 5), border_radius=int(16 * tam))
    pygame.draw.rect(p, (255, 255, 255), r, border_radius=int(16 * tam))
    pygame.draw.rect(p, (235, 238, 250), (r.x + 6, r.y + 6, r.w - 12, int(r.h * 0.3)), border_radius=int(10 * tam))
    pygame.draw.rect(p, (110, 95, 140), r, 4, border_radius=int(16 * tam))
    cx, cy, a, b = r.centerx, r.centery + int(4 * tam), int(26 * tam), int(8 * tam)
    pygame.draw.rect(p, (240, 85, 95), (cx - a // 2 - 1, cy - b - 1, a + 2, 2 * b + 2), border_radius=4)
    pygame.draw.rect(p, (240, 85, 95), (cx - b - 1, cy - a // 2 - 1, 2 * b + 2, a + 2), border_radius=4)
    pygame.draw.rect(p, (255, 255, 255), (cx - 3, cy - a // 2 + 3, 6, a - 6), border_radius=2)
    pygame.draw.rect(p, (255, 255, 255), (cx - a // 2 + 3, cy - 3, a - 6, 6), border_radius=2)


def icono_vida(p, cx, cy, tam):
    """Escudo con corazon (icono de la barra de Vida)."""
    s = tam / 34.0

    def P(x, y):
        return (cx + x * s, cy + y * s)
    esc = [P(-15, -15), P(0, -19), P(15, -15), P(14, 4), P(0, 18), P(-14, 4)]
    pygame.draw.polygon(p, (120, 160, 235), esc)
    pygame.draw.polygon(p, (60, 80, 150), esc, max(2, int(2 * s)))
    pygame.draw.circle(p, (255, 110, 140), P(-4.5, -3), 5.5 * s)
    pygame.draw.circle(p, (255, 110, 140), P(4.5, -3), 5.5 * s)
    pygame.draw.polygon(p, (255, 110, 140), [P(-9.6, 0.5), P(9.6, 0.5), P(0, 11)])
    pygame.draw.circle(p, (255, 255, 255), P(-6, -5), 1.8 * s)


def colores_vida(f):
    """Verde -> amarillo -> rojo suave segun la fraccion de vida (c0, c1)."""
    verde = ((160, 238, 125), (70, 200, 90))
    amar = ((255, 232, 120), (240, 180, 45))
    rojo = ((255, 160, 135), (235, 90, 90))
    if f >= 0.6:
        a, b, k = verde, verde, 0.0
    elif f >= 0.3:
        a, b, k = amar, verde, (f - 0.3) / 0.3
    else:
        a, b, k = rojo, amar, f / 0.3 * 0.3
    return mezcla(a[0], b[0], k), mezcla(a[1], b[1], k)
