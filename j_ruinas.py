"""Ruinas: rompecabezas de piedra al estilo de las Ruinas de Alph.

Se agarran las piezas sueltas con el cursor (posando el cursor 0.35 s o con clic) y se colocan en
la cuadricula del marco (quedandose quieto 0.45 s sobre una celda o con clic). No se giran, no hay
tiempo limite ni castigo. Al completar el mural se revela con un destello.

Uso: Ruinas(ctx, nivel=1, ruina=None)   nivel = indice de ruina + 1 (1..6).
El dibujo vive en arte_ruinas; los datos y el desbloqueo en ruinas_datos.
"""

import math
import random

import pygame

import arte_ruinas as AR
import ruinas_datos as RD
from ajustes import ANCHO, ALTO
from nucleo import Minijuego, V2, escribir, estrella, explosion, Particula

# ----- tiempos de la mecanica
AGARRAR_SEG = 0.35          # cursor quieto sobre una pieza para agarrarla
SOLTAR_SEG = 0.45           # cursor quieto sobre una celda (o fuera) para soltar
RADIO_QUIETO = 36.0         # px que puede temblar el cursor y aun contar como "quieto"
ARMAR_PX = 60.0             # tras agarrar, hay que mover el cursor esto antes de poder soltar quieto

# ----- geometria (pantalla 1280x720)
BORDE = 14                                  # grosor del marco, por fuera de la cuadricula
ZONA = pygame.Rect(108, 98, 1064, 558)      # zona jugable entre las columnas de glifos
TOP_INNER = 112                             # y de arriba de la cuadricula
HUECO = 10                                  # espacio entre piezas sueltas


def _slots_zona(s, zona):
    """Centros de huecos de tamano s dentro de zona (bloque centrado)."""
    nx = (zona.w + HUECO) // (s + HUECO)
    ny = (zona.h + HUECO) // (s + HUECO)
    if nx <= 0 or ny <= 0:
        return []
    ancho = nx * s + (nx - 1) * HUECO
    alto = ny * s + (ny - 1) * HUECO
    x0 = zona.x + (zona.w - ancho) / 2 + s / 2
    y0 = zona.y + (zona.h - alto) / 2 + s / 2
    return [(x0 + i * (s + HUECO), y0 + j * (s + HUECO)) for j in range(ny) for i in range(nx)]


def calcular_layout(cols, filas):
    """Devuelve (s, interior, marco_exterior, huecos): el tamano de celda mas grande con sitio para
    todas las piezas a los costados y debajo del marco."""
    n = cols * filas
    for s in range(150, 39, -2):
        inner = pygame.Rect(0, 0, cols * s, filas * s)
        inner.midtop = (ANCHO // 2, TOP_INNER)
        outer = inner.inflate(2 * BORDE, 2 * BORDE)
        if outer.bottom > ZONA.bottom or outer.left < ZONA.left or outer.right > ZONA.right:
            continue
        izq = pygame.Rect(ZONA.left, ZONA.top, outer.left - HUECO - ZONA.left, outer.bottom - ZONA.top)
        der = pygame.Rect(outer.right + HUECO, ZONA.top, ZONA.right - outer.right - HUECO, outer.bottom - ZONA.top)
        aba = pygame.Rect(ZONA.left, outer.bottom + HUECO, ZONA.w, ZONA.bottom - outer.bottom - HUECO)
        slots_aba = _slots_zona(s, aba)
        slots = _slots_zona(s, izq) + _slots_zona(s, der) + slots_aba
        if len(slots) >= n + 2 and slots_aba:
            return s, inner, outer, slots
    raise ValueError("no cabe la cuadricula")


class Pieza:
    def __init__(self, c, r, surf, pos):
        self.c, self.r = c, r          # celda correcta
        self.surf = surf
        self.pos = V2(pos)             # centro dibujado
        self.dest = V2(pos)            # hacia donde se mueve
        self.celda = None              # (c, r) donde esta puesta, o None si esta suelta

    @property
    def correcta(self):
        return self.celda == (self.c, self.r)


class Reposo:
    """Mide cuanto tiempo el cursor lleva quieto sobre lo mismo (con tolerancia de temblor)."""

    def __init__(self):
        self.reiniciar(None, V2())

    def reiniciar(self, clave, pos):
        self.clave, self.ancla, self.t = clave, V2(pos), 0.0

    def paso(self, dt, pos, clave):
        if clave is None:
            self.reiniciar(None, pos)
        elif clave != self.clave or self.ancla.distance_to(pos) > RADIO_QUIETO:
            self.reiniciar(clave, pos)
        else:
            self.t += dt
        return self.t


def _anillo(p, centro, radio, frac, color=(255, 225, 110)):
    if frac <= 0:
        return
    r = pygame.Rect(0, 0, radio * 2, radio * 2)
    r.center = (int(centro[0]), int(centro[1]))
    pygame.draw.circle(p, (20, 14, 8), r.center, radio, 7)
    pygame.draw.arc(p, color, r, math.pi / 2, math.pi / 2 + 2 * math.pi * min(1.0, frac), 7)


class Ruinas(Minijuego):
    id = "ruinas"
    titulo = "Ruinas"
    instruccion = ("Las piedras del mural se cayeron. Quédate quieto sobre una piedra para agarrarla "
                   "y llévala a su lugar. ¡Descubre el dibujo escondido!")
    gesto = "Quédate quieto para agarrar y soltar"
    duracion = None
    NIVEL_MAX = RD.N_RUINAS
    etiquetas_nivel = {i + 1: AR.NOMBRES[i] for i in range(RD.N_RUINAS)}
    fondo_arriba = (30, 24, 20)
    fondo_abajo = (12, 10, 8)

    def __init__(self, ctx, nivel=1, ruina=None, semilla=None):
        super().__init__(ctx, nivel)
        self.ruina = max(0, min(RD.N_RUINAS - 1, (self.nivel - 1) if ruina is None else int(ruina)))
        self.cols, self.filas = RD.RUINAS[self.ruina]
        self.n = self.cols * self.filas
        self.ayuda = RD.AYUDA[self.ruina]
        self.par_2, self.par_3 = RD.pares(self.ruina)
        rng = random.Random(semilla if semilla is not None else random.random())
        self.s, self.inner, self.marco, huecos = calcular_layout(self.cols, self.filas)
        self.mural = AR.mural(self.ruina, self.cols * self.s, self.filas * self.s)
        self.pista = None
        if self.ayuda >= 2:
            self.pista = self.mural.copy()
            self.pista.set_alpha(70)
        # piezas: orden aleatorio en huecos aleatorios
        self.piezas = []
        celdas = [(c, r) for r in range(self.filas) for c in range(self.cols)]
        rng.shuffle(celdas)
        rng.shuffle(huecos)
        for (c, r), hueco in zip(celdas, huecos):
            self.piezas.append(Pieza(c, r, AR.pieza(self.mural, self.cols, self.filas, c, r), hueco))
        self.rejilla = {}                  # (c, r) -> Pieza puesta
        self.llevada = None
        self.origen = None                 # ("celda", (c, r)) o ("libre", V2) de la pieza llevada
        self.armado = False
        self.punto_agarre = V2()
        self.bloq = None                   # pieza que no se puede re-agarrar hasta que el cursor salga
        self.reposo = Reposo()
        self.cursor = V2(ANCHO / 2, ALTO / 2)
        self.celda_obj = None              # celda bajo el cursor mientras se lleva una pieza
        self.completo = False
        self.t_comp = None
        self.t_rev = 0.0
        self.estrellas_n = 0
        self.monedas_ruina = 0
        self.primera_vez = False
        self.particulas = []
        self.aviso_ok = 0.0

    # ------------------------------------------------------------ geometria
    def metas_par(self):
        return self.par_2, self.par_3

    def calcular_metas(self):
        n = RD.RUINAS[max(0, min(RD.N_RUINAS - 1, self.nivel - 1))]
        n = n[0] * n[1]
        return (n + 50, n + 100, n + 150)

    def rect_celda(self, c, r):
        return pygame.Rect(self.inner.x + c * self.s, self.inner.y + r * self.s, self.s, self.s)

    def centro_celda(self, c, r):
        return V2(self.rect_celda(c, r).center)

    def celda_en(self, pos):
        if not self.inner.collidepoint(pos.x, pos.y):
            return None
        return (int((pos.x - self.inner.x) // self.s), int((pos.y - self.inner.y) // self.s))

    def pieza_en(self, pos):
        """Pieza bajo el cursor (la de arriba), sin contar la llevada."""
        for pz in reversed(self.piezas):
            if pz is self.llevada:
                continue
            if abs(pos.x - pz.dest.x) <= self.s / 2 and abs(pos.y - pz.dest.y) <= self.s / 2:
                return pz
        return None

    def _sacar_del_marco(self, pos):
        """Una posicion libre dentro de la zona jugable y fuera del marco."""
        h = self.s / 2
        x = min(max(pos.x, ZONA.left + h), ZONA.right - h)
        y = min(max(pos.y, ZONA.top + h), ZONA.bottom - h)
        m = self.marco
        if abs(x - m.centerx) < m.w / 2 + h and abs(y - m.centery) < m.h / 2 + h:
            opciones = [(abs(x - (m.left - h)), (m.left - h, y)), (abs(x - (m.right + h)), (m.right + h, y)),
                        (abs(y - (m.bottom + h)), (x, m.bottom + h)), (abs(y - (m.top - h)), (x, m.top - h))]
            opciones = [(d, q) for d, q in opciones
                        if ZONA.left + h <= q[0] <= ZONA.right - h and ZONA.top + h <= q[1] <= ZONA.bottom - h]
            if opciones:
                x, y = min(opciones, key=lambda o: o[0])[1]
        return V2(x, y)

    # ------------------------------------------------------------ acciones
    def agarrar(self, pz, ctrl):
        if pz.celda is not None:
            self.rejilla.pop(pz.celda, None)
            self.origen = ("celda", pz.celda)
        else:
            self.origen = ("libre", V2(pz.pos))
        pz.celda = None
        self.piezas.remove(pz)
        self.piezas.append(pz)             # se dibuja arriba
        self.llevada = pz
        self.armado = False
        self.punto_agarre = V2(ctrl.pos)
        self.reposo.reiniciar(None, ctrl.pos)
        self.sonidos.reproducir("pop")

    def _poner_en(self, pz, celda):
        pz.celda = celda
        pz.dest = self.centro_celda(*celda)
        self.rejilla[celda] = pz

    def _poner_libre(self, pz, pos):
        pz.celda = None
        pz.dest = self._sacar_del_marco(pos)

    def soltar(self, ctrl):
        pz = self.llevada
        if pz is None:
            return
        celda = self.celda_en(ctrl.pos)
        tipo, ref = self.origen
        if celda is not None:
            otra = self.rejilla.pop(celda, None)
            if otra is not None:                    # intercambio: la otra va donde estaba esta
                if tipo == "celda":
                    self._poner_en(otra, ref)
                else:
                    self._poner_libre(otra, ref)
            self._poner_en(pz, celda)
            self.sonidos.reproducir("ok" if pz.correcta else "click")
            if pz.correcta and self.ayuda >= 1:
                self.aviso_ok = 0.5
                explosion(self.particulas, pz.dest.x, pz.dest.y, (255, 220, 110), n=8, vida=0.6,
                          gravedad=0, vel_min=40, vel_max=160, radio=4)
        else:
            self._poner_libre(pz, ctrl.pos)
            self.sonidos.reproducir("click")
        self.llevada = None
        self.origen = None
        self.bloq = pz
        self.reposo.reiniciar(None, ctrl.pos)
        if all(q.correcta for q in self.piezas):
            self._completar()

    def _completar(self):
        self.completo = True
        self.t_comp = self.t
        est = 1 + (self.t < self.par_2) + (self.t < self.par_3)
        self.estrellas_n = est
        self.puntos = est * 50 + self.n
        self.monedas_ruina = RD.monedas_por(self.ruina, est)
        perfil = self.ctx.perfil
        self.primera_vez = RD.registrar(perfil, self.ruina, self.t, est)
        perfil.ganar(self.monedas_ruina)
        perfil.guardar()
        self.sonidos.reproducir("premio")
        for _ in range(6):
            explosion(self.particulas, random.uniform(300, 980), random.uniform(160, 520),
                      random.choice([(255, 220, 110), (255, 250, 200), (230, 170, 70)]),
                      n=14, vida=1.3, gravedad=120, vel_min=60, vel_max=300, radio=6)

    def estrellas(self):
        return self.estrellas_n if self.completo else 0

    def superado(self):
        return self.completo

    # ------------------------------------------------------------ paso
    def paso(self, dt, ctrl):
        self.cursor = V2(ctrl.pos)
        self.aviso_ok = max(0.0, self.aviso_ok - dt)
        self.particulas = [x for x in self.particulas if x.actualizar(dt)]
        # las piezas se deslizan hacia su destino
        k = min(1.0, 14 * dt)
        for pz in self.piezas:
            if pz is self.llevada:
                pz.dest = V2(ctrl.pos)
                k_p = min(1.0, 22 * dt)
                pz.pos += (pz.dest - pz.pos) * k_p
            else:
                pz.pos += (pz.dest - pz.pos) * k
        if self.completo:
            self.t_rev += dt
            if self.t_rev > 3.2:
                self.terminar(f"¡Mural completo! +{self.monedas_ruina} monedas de las ruinas")
            return
        if self.llevada is not None:
            self._paso_llevando(dt, ctrl)
        else:
            self._paso_libre(dt, ctrl)

    def _paso_libre(self, dt, ctrl):
        pz = self.pieza_en(ctrl.pos)
        if self.bloq is not None:
            if pz is self.bloq:
                pz = None
            else:
                self.bloq = None
        if pz is not None and ctrl.clic:
            self.agarrar(pz, ctrl)
            return
        quieto = self.reposo.paso(dt, ctrl.pos, id(pz) if pz is not None else None)
        if pz is not None and quieto >= AGARRAR_SEG:
            self.agarrar(pz, ctrl)

    def _paso_llevando(self, dt, ctrl):
        if not self.armado and ctrl.pos.distance_to(self.punto_agarre) > ARMAR_PX:
            self.armado = True
            self.reposo.reiniciar(None, ctrl.pos)
        celda = self.celda_en(ctrl.pos)
        self.celda_obj = celda
        if ctrl.clic:
            self.soltar(ctrl)
            return
        if not self.armado:
            return
        quieto = self.reposo.paso(dt, ctrl.pos, celda if celda is not None else "fuera")
        if quieto >= SOLTAR_SEG:
            self.soltar(ctrl)

    # ------------------------------------------------------------ dibujo
    def dibujar(self, pantalla):
        self.dibujar_juego(pantalla)
        self.dibujar_hud(pantalla)

    def _progreso_agarre(self):
        if self.llevada is None and self.reposo.clave is not None:
            return self.reposo.t / AGARRAR_SEG
        return 0.0

    def dibujar_juego(self, p):
        i, t = self.ruina, self.t
        AR.dibujar_fondo(p, i, t)
        AR.dibujar_columnas(p, i, t)
        revelar = 0.0
        if self.completo:
            revelar = min(1.0, self.t_rev / 1.2)
        AR.dibujar_marco(p, self.inner, i, completo=self.completo, t=t)
        AR.dibujar_rejilla(p, self.inner, self.cols, self.filas, pista=self.pista)
        # piezas puestas, sueltas y al final la llevada
        for pz in self.piezas:
            if pz is self.llevada:
                continue
            if pz.celda is not None and revelar >= 1.0:
                continue
            p.blit(pz.surf, pz.surf.get_rect(center=(int(pz.pos.x), int(pz.pos.y))))
            if pz.correcta and self.ayuda >= 1 and not self.completo:
                if (pz.dest - pz.pos).length() < 3:
                    AR.dibujar_celda_ok(p, self.rect_celda(pz.c, pz.r), t)
        if self.completo:
            m = self.mural.copy()
            m.set_alpha(int(255 * revelar))
            p.blit(m, self.inner.topleft)
            flash = max(0.0, 1.0 - self.t_rev / 0.9)
            if flash > 0:
                f = pygame.Surface(self.inner.size, pygame.SRCALPHA)
                f.fill((255, 245, 200, int(190 * flash)))
                p.blit(f, self.inner.topleft)
        # ayudas de agarre / soltar
        if self.llevada is None and not self.completo:
            pz = self.pieza_en(self.cursor)
            if pz is not None and pz is not self.bloq:
                pygame.draw.rect(p, (255, 225, 120), pygame.Rect(0, 0, self.s, self.s).move(
                    pz.pos.x - self.s / 2, pz.pos.y - self.s / 2), 3, border_radius=4)
                _anillo(p, pz.pos, int(self.s * 0.42), self._progreso_agarre())
        elif self.llevada is not None:
            celda = self.celda_obj
            if celda is not None:
                r = self.rect_celda(*celda)
                resalte = pygame.Surface(r.size, pygame.SRCALPHA)
                resalte.fill((255, 235, 150, 60))
                p.blit(resalte, r.topleft)
                pygame.draw.rect(p, (255, 225, 120), r, 3)
            pz = self.llevada
            sombra = pygame.Surface((self.s, self.s), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 90))
            p.blit(sombra, sombra.get_rect(center=(int(pz.pos.x) + 8, int(pz.pos.y) + 10)))
            p.blit(pz.surf, pz.surf.get_rect(center=(int(pz.pos.x), int(pz.pos.y))))
            pygame.draw.rect(p, (255, 235, 150), pz.surf.get_rect(center=(int(pz.pos.x), int(pz.pos.y))), 3,
                             border_radius=4)
            if self.armado:
                _anillo(p, self.cursor, int(self.s * 0.42), self.reposo.t / SOLTAR_SEG)
        for x in self.particulas:
            x.dibujar(p)

    def dibujar_hud(self, p):
        nombre = AR.NOMBRES[self.ruina]
        escribir(p, self.f.grande, nombre, ANCHO / 2, 38, (255, 225, 140), contorno=(40, 25, 10))
        escribir(p, self.f.chica,
                 f"{RD.MUNDOS[RD.mundo_de(self.ruina)]['nombre']}  ·  mural {RD.fase_de(self.ruina) + 1} de {RD.POR_MUNDO}",
                 ANCHO / 2, 74, (230, 210, 160), contorno=(30, 20, 10))
        puestas = sum(1 for q in self.piezas if q.correcta)
        escribir(p, self.f.normal, f"Piedras en su lugar: {puestas} de {self.n}", 24, 30, (255, 240, 200),
                 ancla="izq", contorno=(40, 25, 10))
        # estrellas que se ganarian ahora (bajan despacio con el tiempo, sin avisos ni prisa)
        if self.completo:
            ganadas = self.estrellas_n
        else:
            ganadas = 1 + (self.t < self.par_2) + (self.t < self.par_3)
        for k in range(3):
            lleno = k < ganadas
            estrella(p, ANCHO - 140 + k * 44, 38, 17, (255, 210, 60) if lleno else (110, 100, 90),
                     (160, 110, 20) if lleno else (70, 62, 55))
        if not self.completo:
            escribir(p, self.f.chica, "Quédate quieto sobre una piedra para agarrarla", ANCHO / 2, ALTO - 24,
                     (230, 210, 160), contorno=(30, 20, 10))
        else:
            escribir(p, self.f.normal, "¡Qué bonito mural!", ANCHO / 2, ALTO - 28, (255, 240, 170),
                     contorno=(60, 35, 10))
