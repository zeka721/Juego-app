"""Contar con el movimiento: cada golpe suma 1; al parar se revisa si el numero es el correcto."""

import math
import random

import pygame

from ajustes import ANCHO, ALTO
from nucleo import (Minijuego, NOTAS, TextoFlotante, aclarar, corazon, escribir, estrella,
                    explosion, panel)

ORDEN_NOTAS = ["do", "re", "mi", "fa", "sol", "la", "si"]
ESPERA_EVAL = 1.6          # segundos sin golpes para revisar el conteo
ESPERA_AYUDA = 10.0        # sin ningun golpe: se muestra el conteo como ayuda
TIPOS = ["estrella", "manzana", "corazon", "globo"]
ELOGIOS = ["¡Muy bien!", "¡Genial!", "¡Excelente!"]
RANGO = {1: (1, 3), 2: (1, 5), 3: (2, 6), 4: (3, 8), 5: (4, 10)}


def frecuencia(k):
    """Frecuencia de la k-esima nota (k desde 1): do re mi fa sol la si do2 re2 ..."""
    i = k - 1
    return NOTAS[ORDEN_NOTAS[i % 7]] * (2 ** (i // 7))


def _sprite(tipo, r):
    """Dibuja un objeto una sola vez en una superficie con transparencia."""
    d = 2 * r + 30
    c = d // 2
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    if tipo == "estrella":
        estrella(s, c, c, int(r * 1.15))
    elif tipo == "manzana":
        pygame.draw.circle(s, (215, 45, 45), (c, c + 3), r)
        pygame.draw.circle(s, (255, 150, 150), (c - r // 3, c - r // 3), max(3, r // 5))
        pygame.draw.line(s, (95, 65, 30), (c, c - r + 4), (c + 4, c - r - 10), 4)
        pygame.draw.ellipse(s, (70, 175, 70), (c + 4, c - r - 12, r // 2 + 4, r // 3))
    elif tipo == "corazon":
        corazon(s, c, c, int(r * 1.15))
    else:
        pygame.draw.line(s, (90, 90, 110), (c, c + r), (c - 5, c + r + 16), 3)
        pygame.draw.ellipse(s, (70, 150, 240), (c - r * 0.8, c - r, r * 1.6, r * 2))
        pygame.draw.ellipse(s, (190, 225, 255), (c - r * 0.45, c - r * 0.7, r * 0.4, r * 0.6))
    return s


class Contar(Minijuego):
    """Cuenta dando golpes (golpe del mando o clic) y espera 1.6 s para que se revise.

    Cada ronda muestra N objetos ("¿Cuántas ves?") o pide "Da N golpes" con el numero
    enorme. Correcto: +5 puntos y +1 por racha (hasta +5), celebracion, ronda nueva.
    Incorrecto: "¡Casi! Eran N" y los objetos se iluminan uno a uno con su nota; sin castigo.
    Sin ningun golpe en 10 s se muestra el conteo como ayuda.
    Nivel: N va de 1-3 (nivel 1) hasta 4-10 (nivel 5); mas ronda "Da N golpes".
    Mejoras: lento = animaciones mas lentas y mas tiempo para terminar de contar;
    alcance = objetos mas grandes; puntos = x2; tiempo = mas segundos; vida = el primer
    error no rompe la racha; potencia = sin efecto.
    """

    id = "contar"
    titulo = "Contar con el movimiento"
    instruccion = "Da tantos golpes como objetos veas."
    gesto = "Golpes con el mando"
    duracion = 60.0
    fondo_arriba = (255, 200, 140)
    fondo_abajo = (255, 245, 205)

    def __init__(self, ctx, nivel=1):
        super().__init__(ctx, nivel)
        self.escala_obj = min(1.25, self.mej.mult("alcance"))
        self.espera_eval = ESPERA_EVAL / self.lento
        self.fuente_gigante = pygame.font.SysFont("arial", 220, bold=True)
        self.sprites = {t: _sprite(t, 46) for t in TIPOS}
        self.escudo = self.mej.vidas_extra()
        self.racha = 0
        self.aciertos = 0
        self.ultimo_n = 0
        self.particulas = []
        self.estado = "contando"      # contando | acierto | revela
        self.golpes = 0
        self.pulso = 0.0
        self.t_golpe = 0.0            # tiempo desde el ultimo golpe
        self.t_inactivo = 0.0
        self.t_estado = 0.0
        self.msg, self.msg_t = "", 0.0
        self.revelados = 0
        self.t_revela = 0.0
        self._nueva_ronda()

    def calcular_metas(self):
        return (15, 30, 50)

    # --- rondas ---
    def _nueva_ronda(self):
        lo, hi = RANGO[self.nivel]
        n = random.randint(lo, hi)
        for _ in range(10):
            if n != self.ultimo_n:
                break
            n = random.randint(lo, hi)
        self.n = self.ultimo_n = n
        p_num = (0.0, 0.3, 0.4, 0.4, 0.45)[self.nivel - 1]
        self.variante = "numero" if random.random() < p_num else "objetos"
        self.tipo = random.choice(TIPOS)
        self.golpes = 0
        self.estado = "contando"
        self.t_golpe = 0.0
        self.t_inactivo = 0.0
        self.revelados = 0
        self._posiciones()

    def _posiciones(self):
        n = self.n
        if n <= 5:
            filas, y0, sep, rad = [n], 345, 150, 50
        else:
            filas, y0, sep, rad = [(n + 1) // 2, n // 2], 300, 135, 44
        self.rad = rad * self.escala_obj
        self.pos_obj = []
        for i, k in enumerate(filas):
            y = y0 + i * 125
            x0 = ANCHO / 2 - sep * (k - 1) / 2
            for j in range(k):
                self.pos_obj.append((x0 + j * sep, y))

    # --- ciclo ---
    def paso(self, dt, ctrl):
        dt_a = dt * self.lento
        self.pulso = max(0.0, self.pulso - dt * 3.5)
        self.msg_t = max(0.0, self.msg_t - dt)
        self.particulas = [q for q in self.particulas if q.actualizar(dt)]

        if self.estado == "contando":
            if ctrl.golpe or ctrl.clic:
                self.golpes = min(99, self.golpes + 1)
                self.pulso = 1.0
                self.t_golpe = 0.0
                self.t_inactivo = 0.0
                self.sonidos.nota(frecuencia(min(self.golpes, 14)), 0.3)
                x, y = ANCHO / 2, 585
                explosion(self.particulas, x, y, (255, 215, 90), n=6, vel_min=80, vel_max=240,
                          vida=0.5, gravedad=200, radio=5)
            elif self.golpes > 0:
                self.t_golpe += dt
                if self.t_golpe >= self.espera_eval:
                    self._evaluar()
            else:
                self.t_inactivo += dt
                if self.t_inactivo >= ESPERA_AYUDA:
                    self._empezar_revela("¡Mira! Eran ")
        elif self.estado == "acierto":
            self.t_estado -= dt
            if self.t_estado <= 0:
                if self.puntos >= self.metas[2]:
                    self.terminar("¡Bien hecho!")
                else:
                    self._nueva_ronda()
        else:                                           # revela
            self.t_revela -= dt_a
            if self.revelados < self.n and self.t_revela <= 0:
                self.revelados += 1
                self.golpes = self.revelados
                self.pulso = 1.0
                self.t_revela = 0.55
                self.sonidos.nota(frecuencia(self.revelados), 0.35)
                px, py = self.pos_obj[self.revelados - 1]
                explosion(self.particulas, px, py, (255, 240, 130), n=8, vel_min=60, vel_max=220,
                          vida=0.5, gravedad=150, radio=5)
            elif self.revelados >= self.n and self.t_revela <= -0.6:
                self._nueva_ronda()

    def _evaluar(self):
        if self.golpes == self.n:
            self.aciertos += 1
            self.racha += 1
            bonus = min(self.racha - 1, 5)
            self.sumar(5 + bonus, ANCHO / 2, 470, (255, 240, 120))
            self.sonidos.reproducir("premio")
            self.msg, self.msg_t = random.choice(ELOGIOS), 1.5
            for px, py in self.pos_obj:
                explosion(self.particulas, px, py, (255, 215, 90), n=10, vel_min=100,
                          vel_max=380, vida=0.8, gravedad=250, radio=6)
                explosion(self.particulas, px, py, (120, 220, 255), n=6, vel_min=100,
                          vel_max=300, vida=0.7, gravedad=250, radio=5)
            if self.racha >= 3:
                self.flotantes.append(TextoFlotante(f"¡Racha x{self.racha}!", ANCHO / 2, 530,
                                                    (255, 120, 60), vida=1.3))
            self.estado = "acierto"
            self.t_estado = 1.8
        else:
            if self.escudo > 0:
                self.escudo -= 1
            else:
                self.racha = 0
            self.sonidos.reproducir("error")
            self._empezar_revela("¡Casi! Eran ")

    def _empezar_revela(self, texto):
        self.msg, self.msg_t = f"{texto}{self.n}", 99.0
        self.estado = "revela"
        self.revelados = 0
        self.golpes = 0
        self.t_revela = 0.6

    # --- dibujo ---
    def _obj(self, pantalla, i, x, y):
        s = self.sprites[self.tipo]
        brillo = 0.0
        if self.estado == "revela" and i < self.revelados:
            brillo = 1.0 if i == self.revelados - 1 else 0.35
        k = self.escala_obj * (1.0 + 0.3 * brillo * (1 if i == self.revelados - 1 else 0.3))
        if self.estado == "acierto":
            k *= 1.0 + 0.1 * abs(math.sin(self.t * 8 + i))
            y -= 10 * abs(math.sin(self.t * 8 + i * 0.7))
        else:
            y += 5 * math.sin(self.t * 2.2 + i * 0.9)
        if brillo > 0:
            halo = pygame.Surface((220, 220), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 240, 120, int(150 * brillo)), (110, 110), 80)
            pantalla.blit(halo, halo.get_rect(center=(int(x), int(y))))
        s2 = pygame.transform.rotozoom(s, 0, k) if abs(k - 1.0) > 0.01 else s
        pantalla.blit(s2, s2.get_rect(center=(int(x), int(y))))

    def dibujar_juego(self, pantalla):
        # texto de la ronda
        if self.estado == "contando":
            if self.variante == "numero":
                pl = "golpe" if self.n == 1 else "golpes"
                escribir(pantalla, self.f.grande, f"Da {self.n} {pl}", ANCHO / 2, 140,
                         color=(255, 255, 255))
            else:
                escribir(pantalla, self.f.grande, "¿Cuántas ves?", ANCHO / 2, 140)
                escribir(pantalla, self.f.normal, "¡Da ese número de golpes!", ANCHO / 2, 190,
                         color=(255, 245, 190))
        # objetos (en la variante "numero" solo aparecen al celebrar o revelar)
        if self.variante == "objetos" or self.estado != "contando":
            for i, (x, y) in enumerate(self.pos_obj):
                self._obj(pantalla, i, x, y)
        else:
            # numero gigante en el centro
            txt = str(self.n)
            c = (ANCHO // 2, 345 + int(5 * math.sin(self.t * 3)))
            escribir(pantalla, self.fuente_gigante, txt, c[0], c[1], color=(255, 255, 255),
                     contorno=(60, 40, 120), grosor=5)
        # contador grande
        self._contador(pantalla)
        for q in self.particulas:
            q.dibujar(pantalla)
        # mensaje
        if self.msg_t > 0 and self.estado != "contando":
            color = (255, 235, 90) if self.estado == "acierto" else (255, 255, 255)
            fuente = self.f.enorme if self.estado == "acierto" else self.f.grande
            y = 140 if self.estado == "revela" else 150
            escribir(pantalla, fuente, self.msg, ANCHO / 2, y, color=color)

    def _contador(self, pantalla):
        cx, cy = ANCHO // 2, 595
        r = 78 + int(14 * self.pulso)
        if self.estado == "acierto":
            col, borde = (130, 225, 140), (30, 130, 60)
        elif self.estado == "revela":
            col, borde = (255, 215, 120), (200, 120, 20)
        else:
            col, borde = (255, 255, 255), (60, 80, 150)
        pygame.draw.circle(pantalla, (200, 150, 110), (cx + 4, cy + 7), r)
        pygame.draw.circle(pantalla, col, (cx, cy), r)
        pygame.draw.circle(pantalla, borde, (cx, cy), r, 6)
        txt = self.f.enorme.render(str(self.golpes), True, (45, 60, 140))
        k = 1.0 + 0.35 * self.pulso
        t2 = pygame.transform.rotozoom(txt, 0, k)
        pantalla.blit(t2, t2.get_rect(center=(cx, cy + 2)))
        if self.golpes == 0 and self.estado == "contando":
            escribir(pantalla, self.f.chica, "golpes", cx, cy + 52, color=(120, 130, 170),
                     contorno=None)
