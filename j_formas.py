"""Formas y colores: lleva cada ficha de la bandeja a su agujero."""

import math
import random

import pygame

from ajustes import ANCHO, ALTO
from j_agarre import Espera, anillo, confeti, puntos_forma, superficie_forma
from nucleo import (Minijuego, TextoFlotante, aclarar, escribir, explosion, oscurecer, panel, V2)

FORMAS = ["circulo", "cuadrado", "triangulo", "estrella", "corazon", "rombo"]
# forma: (articulo, nombre, es_femenino)
NOMBRES = {"circulo": ("el", "círculo", False), "cuadrado": ("el", "cuadrado", False),
           "triangulo": ("el", "triángulo", False), "estrella": ("la", "estrella", True),
           "corazon": ("el", "corazón", False), "rombo": ("el", "rombo", False)}
# color: (rgb, masculino, femenino)
COLORES = {"rojo": ((230, 60, 70), "rojo", "roja"), "azul": ((60, 120, 230), "azul", "azul"),
           "verde": ((70, 185, 85), "verde", "verde"), "amarillo": ((250, 205, 40), "amarillo", "amarilla"),
           "morado": ((160, 90, 210), "morado", "morada"), "naranja": ((250, 140, 35), "naranja", "naranja"),
           "celeste": ((90, 205, 240), "celeste", "celeste"), "rosa": ((250, 130, 190), "rosa", "rosa")}
BASICOS = ["rojo", "azul", "verde", "amarillo", "morado", "naranja"]
PARECIDOS = {"rojo": ["naranja", "rosa"], "naranja": ["rojo", "amarillo"], "azul": ["celeste", "morado"],
             "celeste": ["azul"], "morado": ["azul", "rosa"], "rosa": ["rojo", "morado"],
             "amarillo": ["naranja"], "verde": ["celeste"]}
EXTRAS = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2}
BANDEJA = pygame.Rect(60, 452, 1160, 245)
PANEL_HUECOS = pygame.Rect(60, 172, 1160, 232)
Y_HUECOS = 290
GRIS = (95, 105, 140)


class Hueco:
    def __init__(self, forma, color, x, y):
        self.forma, self.color, self.x, self.y = forma, color, x, y
        self.lleno = False
        self.tiembla = 0.0

    def acepta(self, ficha):
        return ficha.forma == self.forma and (self.color is None or ficha.color == self.color)


class Ficha:
    def __init__(self, forma, color, hx, hy):
        self.forma, self.color = forma, color
        self.home = V2(hx, hy)
        self.pos = V2(hx, hy)
        self.vel = V2(0, 0)
        self.estado = "bandeja"      # bandeja, agarrada, vuelve, encaja, puesta
        self.t = 0.0
        self.origen = V2(hx, hy)
        self.hueco = None
        self.escala = 1.0
        self.fase = random.uniform(0, 6.28)


class Formas(Minijuego):
    """Formas y colores: agarra una ficha de la bandeja y sueltala en su agujero.

    Mando: clic, golpe o dejar el cursor ~0.6 s sobre una ficha la agarra (sigue al
    cursor); clic, golpe o espera sobre un agujero la suelta: si coincide encaja y suena
    "ok"; si no, rebota suave a la bandeja (sin castigo). Soltar en la bandeja (espera o
    clic) la devuelve. Nivel 1: forma (agujeros grises); desde el 2 el agujero tiene color y
    hay que acertar forma Y color; los niveles altos agregan fichas parecidas (mismo
    color o forma) y 4 agujeros.
    Puntos: 5 por acierto + 1 por cada acierto seguido (racha, hasta +4) + 5 por ronda.

    Mejoras: potencia = agarrar y soltar con menos espera (espera / potencia);
    alcance = zonas de agarre y de agujero x1.3; lento = animaciones y rebotes mas lentos;
    tiempo = mas segundos (base); puntos = x2 (base);
    vida = un escudo: el primer error de la partida no corta la racha.
    """

    id = "formas"
    titulo = "Formas y colores"
    instruccion = "Lleva cada ficha a su agujero. ¡Fíjate en la forma y el color!"
    gesto = "Cursor sobre la ficha y luego sobre el agujero"
    duracion = 60.0
    fondo_arriba = (255, 225, 150)
    fondo_abajo = (255, 245, 215)

    def __init__(self, ctx, nivel=1):
        super().__init__(ctx, nivel)
        self.espera = Espera(0.6 / self.mej.mult("potencia"))
        self.alcance = self.mej.mult("alcance")
        self.escudo = self.mej.vidas_extra() > 0
        self.pos = V2(ANCHO / 2, ALTO / 2)
        self.racha = 0
        self.aciertos = 0
        self.particulas = []
        self.agarrada = None
        self.pausa = 0.0
        self.entra = 0.0
        self.cache = {}
        self.huecos, self.fichas = [], []
        self.sombra = None
        self._nueva_ronda()

    def calcular_metas(self):
        return (15, 35, 60)

    # ------------------------------------------------------------ rondas
    def _elegir(self):
        """Devuelve (lista de (forma, color) de los agujeros, lista de extras)."""
        n = 3 if self.nivel <= 2 else 4
        nivel = self.nivel
        formas = random.sample(FORMAS, n if nivel <= 2 else 3)
        if nivel >= 3:
            formas.append(random.choice(formas))
        paleta = BASICOS if nivel <= 3 else list(COLORES)
        colores = random.sample(paleta, n)
        if nivel >= 5:                               # un par de colores parecidos
            a = random.choice(list(PARECIDOS))
            b = random.choice([c for c in PARECIDOS[a]])
            colores[0], colores[1] = a, b
            resto = [c for c in paleta if c not in (a, b)]
            colores[2:] = random.sample(resto, n - 2)
        combos = list(zip(formas, colores))
        if len(set(combos)) < n:                     # repetidos: se vuelve a sortear
            return self._elegir()
        extras = []
        for _ in range(EXTRAS[nivel]):
            for _ in range(60):
                forma, color = random.choice(combos)
                if nivel == 2:
                    color = random.choice([c for c in paleta if c not in colores])
                elif nivel >= 4 and random.random() < 0.6:
                    color = random.choice(PARECIDOS[color])
                else:
                    color = random.choice(colores)
                if (forma, color) not in combos and (forma, color) not in extras:
                    extras.append((forma, color))
                    break
        return combos, extras

    def _nueva_ronda(self):
        combos, extras = self._elegir()
        n = len(combos)
        self.R = 66 if n == 3 else 56
        paso = (PANEL_HUECOS.width - 120) / n
        self.huecos = []
        for i, (forma, color) in enumerate(combos):
            x = PANEL_HUECOS.x + 60 + (i + 0.5) * paso
            self.huecos.append(Hueco(forma, color if self.nivel >= 2 else None, x, Y_HUECOS))
        if self.nivel == 1:                          # colores sueltos: solo cuenta la forma
            colores = random.sample(list(COLORES), n)
            fichas = [(f, colores[i]) for i, (f, _) in enumerate(combos)]
        else:
            fichas = list(combos) + extras
        random.shuffle(fichas)
        m = len(fichas)
        pasoy = (BANDEJA.width - 100) / m
        self.fichas = [Ficha(f, c, BANDEJA.x + 50 + (i + 0.5) * pasoy, BANDEJA.centery + 8)
                       for i, (f, c) in enumerate(fichas)]
        self.agarrada = None
        self.pausa = 0.0
        self.entra = 0.0
        self.sombra = pygame.Surface((int(self.R * 1.9), int(self.R * 0.5)), pygame.SRCALPHA)
        pygame.draw.ellipse(self.sombra, (80, 50, 20, 55), self.sombra.get_rect())
        self.espera.bloquear(None)

    def _surf_ficha(self, forma, color):
        k = ("f", forma, color, self.R)
        if k not in self.cache:
            rgb = COLORES[color][0]
            self.cache[k] = superficie_forma(forma, self.R, rgb, oscurecer(rgb, 0.5), brillo=True)
        return self.cache[k]

    def _surf_hueco(self, forma, color):
        k = ("h", forma, color, self.R)
        if k not in self.cache:
            if color is None:
                self.cache[k] = superficie_forma(forma, self.R, (60, 66, 100), (40, 44, 75), interior=GRIS)
            else:
                rgb = COLORES[color][0]
                self.cache[k] = superficie_forma(forma, self.R, aclarar(rgb, 0.35), rgb,
                                                 interior=aclarar(rgb, 0.72), grosor=7)
        return self.cache[k]

    def _guia_hueco(self):
        for h in self.huecos:
            if not h.lleno:
                return h
        return None

    def _frase(self, h):
        art, nombre, fem = NOMBRES[h.forma]
        texto = f"Busca {art} {nombre}"
        if h.color is not None:
            texto += " " + COLORES[h.color][2 if fem else 1]
        return texto

    # ------------------------------------------------------------ busqueda
    def ficha_en(self, p):
        mejor, dmin = None, self.R * 1.2 * self.alcance
        for f in self.fichas:
            if f.estado == "bandeja":
                d = f.pos.distance_to(p)
                if d <= dmin:
                    mejor, dmin = f, d
        return mejor

    def hueco_en(self, p):
        mejor, dmin = None, self.R * 1.5 * self.alcance
        for i, h in enumerate(self.huecos):
            if not h.lleno:
                d = math.hypot(h.x - p.x, h.y - p.y)
                if d <= dmin:
                    mejor, dmin = i, d
        return mejor

    # ------------------------------------------------------------ acciones
    def _soltar_en(self, ficha, h):
        if h.acepta(ficha):
            h.lleno = True
            ficha.estado, ficha.t, ficha.hueco, ficha.origen = "encaja", 0.0, h, V2(ficha.pos)
            self.agarrada = None
            self.racha += 1
            self.aciertos += 1
            ptos = self.sumar(5 + min(self.racha - 1, 4), h.x, h.y - self.R - 10, (255, 255, 120))
            self.sonidos.reproducir("ok")
            explosion(self.particulas, h.x, h.y, COLORES[ficha.color][0], n=14, vel_min=100,
                      vel_max=300, gravedad=300)
            if self.racha >= 3:
                self.flotantes.append(TextoFlotante(f"¡Racha x{self.racha}!", h.x, h.y + self.R + 20,
                                                    (255, 120, 60), vida=1.1))
            if all(x.lleno for x in self.huecos):
                self.pausa = 1.5
                self.sumar(5, ANCHO / 2 + 260, 200, (255, 240, 120))
                self.sonidos.reproducir("premio")
                confeti(self.particulas, ANCHO, 45)
        else:
            h.tiembla = 0.5
            ficha.estado = "vuelve"
            self.agarrada = None
            self.sonidos.reproducir("error")
            self.flotantes.append(TextoFlotante("¡Casi! Prueba otra", h.x, h.y - self.R - 10,
                                                (255, 140, 40), vida=1.2))
            if self.escudo:
                self.escudo = False
                self.flotantes.append(TextoFlotante("¡Escudo!", h.x, h.y + self.R + 20, (90, 180, 255)))
            else:
                self.racha = 0

    def _accion(self, clave):
        tipo = clave[0]
        if tipo == "tomar":
            self.agarrada = clave[1]
            clave[1].estado = "agarrada"
            self.sonidos.reproducir("pop")
            self.espera.bloquear(("bandeja",))
        elif tipo == "soltar":
            self._soltar_en(self.agarrada, self.huecos[clave[1]])
        else:                                        # devolver a la bandeja
            self.agarrada.estado = "vuelve"
            self.agarrada = None
            self.sonidos.reproducir("click")

    # ------------------------------------------------------------ cuadro
    def paso(self, dt, ctrl):
        da = dt * self.lento
        self.pos = V2(ctrl.pos)
        self.particulas = [p for p in self.particulas if p.actualizar(dt)]
        self.entra += da
        for h in self.huecos:
            h.tiembla = max(0.0, h.tiembla - dt)
        self._animar(da, ctrl)
        if self.tiempo <= 0 and not self.terminado:
            self.terminar("¡Bien hecho!")
            return
        if self.pausa > 0:
            self.pausa -= dt
            if self.pausa <= 0:
                self._nueva_ronda()
            return
        ag = self.agarrada
        if ag is None:
            f = self.ficha_en(ctrl.pos)
            clave = ("tomar", f) if f else None
        else:
            i = self.hueco_en(ctrl.pos)
            if i is not None:
                clave = ("soltar", i)
            elif BANDEJA.collidepoint(ctrl.pos.x, ctrl.pos.y):
                clave = ("bandeja",)
            else:
                clave = None
        if self.espera.actualizar(dt, clave, ctrl.clic or ctrl.golpe):
            self._accion(clave)
        elif ctrl.clic and ag is not None and clave is None:          # clic al vacio: devuelve
            self._accion(("bandeja",))

    def _animar(self, da, ctrl):
        for f in self.fichas:
            if f.estado == "agarrada":
                f.pos += (V2(self.pos) - f.pos) * min(1.0, 20 * da)
                f.escala += (1.12 - f.escala) * min(1.0, 12 * da)
            elif f.estado == "vuelve":
                f.escala += (1.0 - f.escala) * min(1.0, 12 * da)
                a = (f.home - f.pos) * 200 - f.vel * 13
                f.vel += a * da
                f.pos += f.vel * da
                if f.pos.distance_to(f.home) < 2 and f.vel.length() < 25:
                    f.pos, f.vel, f.estado = V2(f.home), V2(0, 0), "bandeja"
            elif f.estado == "encaja":
                f.t += da
                u = min(1.0, f.t / 0.35)
                e = 1 - (1 - u) ** 3
                f.pos = f.origen + (V2(f.hueco.x, f.hueco.y) - f.origen) * e
                f.escala = 1.0 + 0.2 * math.sin(math.pi * u)
                if u >= 1.0:
                    f.estado, f.escala = "puesta", 1.0
            elif f.estado == "bandeja":
                f.escala += (1.0 - f.escala) * min(1.0, 12 * da)

    # ------------------------------------------------------------ dibujo
    def _blit(self, p, sup, x, y, escala=1.0):
        if abs(escala - 1.0) > 0.01:
            sup = pygame.transform.smoothscale(sup, (max(2, int(sup.get_width() * escala)),
                                                     max(2, int(sup.get_height() * escala))))
        p.blit(sup, sup.get_rect(center=(int(x), int(y))))

    def dibujar_juego(self, p):
        panel(p, PANEL_HUECOS, (255, 255, 255), 190, 26)
        pygame.draw.rect(p, (205, 150, 90), BANDEJA, border_radius=30)
        pygame.draw.rect(p, (150, 100, 55), BANDEJA, 6, border_radius=30)
        pygame.draw.rect(p, (225, 175, 115), BANDEJA.inflate(-30, -30), border_radius=24)
        entra = min(1.0, self.entra * 3.0)
        guia = self._guia_hueco()
        ag = self.agarrada
        sobre = self.hueco_en(self.pos) if ag is not None else None
        for i, h in enumerate(self.huecos):
            esc = 1.0 if h.lleno else max(0.05, entra)
            dx = math.sin(h.tiembla * 40) * 7 * (h.tiembla / 0.5)
            if not h.lleno and self.nivel <= 2 and h is guia and ag is None:
                pulso = 8 + 6 * math.sin(self.t * 6)
                pygame.draw.polygon(p, (255, 215, 50), puntos_forma(h.forma, h.x + dx, h.y, self.R + pulso), 6)
            self._blit(p, self._surf_hueco(h.forma, h.color), h.x + dx, h.y, esc)
            if sobre == i:
                pygame.draw.polygon(p, (255, 255, 255), puntos_forma(h.forma, h.x, h.y, self.R + 12), 6)
        sobre_f = self.ficha_en(self.pos) if ag is None else None
        for f in self.fichas:
            if f.estado in ("bandeja", "vuelve"):
                esc = entra if f.estado == "bandeja" else 1.0
                bob = math.sin(self.t * 2.2 + f.fase) * 3 if f.estado == "bandeja" else 0
                p.blit(self.sombra, self.sombra.get_rect(center=(int(f.pos.x), int(f.pos.y + self.R * 0.95))))
                sc = esc * (1.1 if f is sobre_f else 1.0)
                if f is sobre_f:
                    pygame.draw.polygon(p, (255, 240, 90), puntos_forma(f.forma, f.pos.x, f.pos.y + bob, self.R + 10), 6)
                self._blit(p, self._surf_ficha(f.forma, f.color), f.pos.x, f.pos.y + bob, max(0.05, sc))
            elif f.estado in ("encaja", "puesta"):
                self._blit(p, self._surf_ficha(f.forma, f.color), f.pos.x, f.pos.y, f.escala)
        if ag is not None:
            p.blit(self.sombra, self.sombra.get_rect(center=(int(ag.pos.x + 8), int(ag.pos.y + self.R * 1.1))))
            self._blit(p, self._surf_ficha(ag.forma, ag.color), ag.pos.x, ag.pos.y, ag.escala)
        # texto guia
        if self.pausa > 0:
            escribir(p, self.f.grande, "¡Muy bien!", ANCHO / 2, 128, color=(255, 235, 90), grosor=3)
        elif guia is not None:
            if ag is None:
                texto = self._frase(guia)
            else:
                texto = "¡Ahora ponla en su hueco!" if NOMBRES[ag.forma][2] else "¡Ahora ponlo en su hueco!"
            escribir(p, self.f.grande, texto, ANCHO / 2, 128, color=(255, 255, 255), grosor=3)
        if self.racha >= 2:
            escribir(p, self.f.normal, f"Racha: {self.racha}", 90, 200, color=(255, 190, 80), ancla="izq")
        for q in self.particulas:
            q.dibujar(p)
        anillo(p, self.pos.x, self.pos.y, self.espera.frac)
