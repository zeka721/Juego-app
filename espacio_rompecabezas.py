"""Rompecabezas de un componente de la nave nodriza en Defensa Espacial.

Paso 1, armar: toca una pieza de la bandeja y luego su hueco en el componente (3 x 2 = 6 piezas).
Las piezas 1-3 vienen del primer planeta de la pareja y las 4-6 del segundo.
Paso 2, instalar: el componente armado queda en la mano y sigue al cursor. Toca su hueco en la nave nodriza.

RompecabezasEspacio(app, c, volver)   c = numero de componente (1..4); volver() devuelve la escena a la que se regresa.
"""

import random

import pygame

from ajustes import ANCHO, ALTO
from escena import Escena
from escena_items import BotonF, PAPEL, TINTA, TINTA_SUAVE, ajustado
from nucleo import fondo, panel
import espacio_datos as D
import espacio_dataset as AD
from espacio_datos import PIEZAS_COMPONENTE

ORO = (255, 225, 140)
CLARO = (255, 240, 200)
CONTORNO = (20, 14, 40)
BORDE_PAPEL = (90, 60, 30)

# huecos del componente (fila mayor = filas, columnas de 3)
CELDA_W, CELDA_H, SEP = 150, 110, 10
ORIGEN_X, ORIGEN_Y = 60, 150
# bandeja de piezas
BANDEJA_Y = 520
PIEZA_W, PIEZA_H, PIEZA_SEP = 140, 96, 26
# slots de la nave nodriza (uno por componente)
SLOTS = {1: (800, 250), 2: (985, 240), 3: (1150, 300), 4: (900, 430)}
SLOT_W, SLOT_H = 130, 120
NAVE_RECT = (748, 190, 424, 238)           # donde se dibuja la nave (640 x 360 escalada)


def celda(f):
    """Rectangulo del hueco f (1..6) del componente."""
    col, fil = (f - 1) % 3, (f - 1) // 3
    return pygame.Rect(ORIGEN_X + col * (CELDA_W + SEP), ORIGEN_Y + fil * (CELDA_H + SEP), CELDA_W, CELDA_H)


def dibujar_pieza(p, n, f, rect, color, fuente):
    """Pieza f del componente n: imagen del dataset, o un cuadro de color con su numero."""
    img = AD.pieza(n, f)
    if img is not None:
        p.blit(pygame.transform.smoothscale(img, rect.size), rect)
        return
    pygame.draw.rect(p, color, rect, border_radius=12)
    pygame.draw.rect(p, (60, 40, 20), rect, 3, border_radius=12)
    ajustado(p, fuente, str(f), rect.centerx, rect.centery, rect.w - 20, (255, 255, 255), contorno=(40, 30, 20))


def mosaico(p, x, y, cw, ch, color, llenos):
    """Dibuja el componente de 3 x 2 en (x, y); 'llenos' son los huecos con pieza."""
    for f in range(1, PIEZAS_COMPONENTE + 1):
        col, fil = (f - 1) % 3, (f - 1) // 3
        r = pygame.Rect(x + col * (cw + 4), y + fil * (ch + 4), cw, ch)
        if f in llenos:
            pygame.draw.rect(p, color, r, border_radius=8)
            pygame.draw.rect(p, (60, 40, 20), r, 2, border_radius=8)
        else:
            pygame.draw.rect(p, (240, 236, 226), r, border_radius=8)
            pygame.draw.rect(p, (150, 140, 130), r, 2, border_radius=8)


class RompecabezasEspacio(Escena):
    def __init__(self, app, n, volver):
        super().__init__(app)
        self.n = n
        self.comp = D.COMPONENTES[n - 1]
        self.mundo_a, self.mundo_b = (D.MUNDOS[m - 1] for m in self.comp["mundos"])
        self.volver_a = volver
        self.color = self.comp["color"]
        self.bandeja = list(range(1, PIEZAS_COMPONENTE + 1))
        random.shuffle(self.bandeja)
        self.colocadas = set()
        self.seleccion = None
        self.estado = "armar"            # armar -> mano -> listo
        self.mensaje = "Toca una pieza de abajo y luego su hueco."
        self.cursor = (ANCHO / 2, ALTO / 2)
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))

    def _pieza_rect(self, i):
        return pygame.Rect(120 + i * (PIEZA_W + PIEZA_SEP), BANDEJA_Y, PIEZA_W, PIEZA_H)

    def _salir(self):
        self.app.ctx.sonidos.reproducir("click")
        self.app.ir(self.volver_a())

    def tecla_esc(self):
        self._salir()

    # ------------------------------------------------------------ logica
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self.cursor = (ctrl.pos.x, ctrl.pos.y)
        if self.volver.actualizar(dt, ctrl):
            self._salir()
            return
        if self.estado == "armar":
            if ctrl.clic:
                self._armar_clic(ctrl.pos)
        elif self.estado == "mano":
            if ctrl.clic:
                self._instalar_clic(ctrl.pos)

    def _armar_clic(self, pos):
        for i, f in enumerate(list(self.bandeja)):
            if self._pieza_rect(i).collidepoint(pos.x, pos.y):
                self.seleccion = f
                self.app.ctx.sonidos.reproducir("click")
                return
        if self.seleccion is None:
            return
        for f in range(1, PIEZAS_COMPONENTE + 1):
            if f not in self.colocadas and celda(f).collidepoint(pos.x, pos.y):
                if f == self.seleccion:
                    self.colocadas.add(f)
                    self.bandeja.remove(f)
                    self.seleccion = None
                    self.app.ctx.sonidos.reproducir("ok")
                    if len(self.colocadas) == PIEZAS_COMPONENTE:
                        self.estado = "mano"
                        self.mensaje = f"¡{self.comp['nombre']} armado! Llévalo a su hueco en la nave nodriza."
                        self.app.ctx.sonidos.reproducir("premio")
                    else:
                        self.mensaje = f"¡Bien! Quedan {PIEZAS_COMPONENTE - len(self.colocadas)} piezas."
                else:
                    self.seleccion = None
                    self.app.ctx.sonidos.reproducir("error")
                    self.mensaje = "Esa pieza no va en ese hueco. Prueba otra vez."
                return

    def _instalar_clic(self, pos):
        for m, (cx, cy) in SLOTS.items():
            if pygame.Rect(cx - SLOT_W // 2, cy - SLOT_H // 2, SLOT_W, SLOT_H).collidepoint(pos.x, pos.y):
                if m != self.n:
                    self.app.ctx.sonidos.reproducir("error")
                    self.mensaje = f"Ese hueco es del {D.COMPONENTES[m - 1]['nombre']}."
                    return
                if D.instalar_componente(self.app.ctx.perfil, self.n):
                    self.estado = "listo"
                    self.app.ctx.sonidos.reproducir("premio")
                    self.mensaje = (f"¡{self.comp['nombre']} instalado! "
                                    f"La nave nodriza se mejora.")
                else:
                    self.app.ctx.sonidos.reproducir("error")
                    self.mensaje = "Este componente ya estaba instalado."
                return

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        fondo(p, *self.mundo_a["fondo"])
        ajustado(p, self.f.grande, f"Armar {self.comp['nombre']}", ANCHO / 2, 50, 900, CLARO,
                 contorno=CONTORNO)
        ajustado(p, self.f.chica, f"Piezas de {self.mundo_a['nombre']} y {self.mundo_b['nombre']}", ANCHO / 2, 84,
                 900, CLARO, contorno=CONTORNO)
        self._dibujar_componente_mesa(p)
        self._dibujar_bandeja(p)
        self._dibujar_nave(p)
        if self.estado == "mano":
            self._dibujar_en_mano(p)
        self.volver.dibujar(p, self.f.normal)
        ajustado(p, self.f.chica, self.mensaje, 735, ALTO - 40, 960, CLARO, contorno=CONTORNO)

    def _dibujar_componente_mesa(self, p):
        panel(p, (ORIGEN_X - 20, ORIGEN_Y - 20, 3 * CELDA_W + 2 * SEP + 40, 2 * CELDA_H + SEP + 40),
              color=PAPEL, alfa=240, radio=20, borde=BORDE_PAPEL)
        for f in range(1, PIEZAS_COMPONENTE + 1):
            r = celda(f)
            if f in self.colocadas:
                cuadro = pygame.Rect(0, 0, 110, 110)
                cuadro.center = r.center
                dibujar_pieza(p, self.n, f, cuadro, self.color, self.f.grande)
            else:
                pygame.draw.rect(p, (232, 226, 214), r, border_radius=12)
                pygame.draw.rect(p, (150, 140, 130), r, 2, border_radius=12)
                ajustado(p, self.f.normal, str(f), r.centerx, r.centery, r.w - 20, (170, 160, 150))

    def _dibujar_bandeja(self, p):
        if self.estado != "armar":
            return
        for i, f in enumerate(self.bandeja):
            r = self._pieza_rect(i)
            if self.seleccion == f:
                pygame.draw.rect(p, ORO, r.inflate(10, 10), 5, border_radius=18)
            cuadro = pygame.Rect(0, 0, 88, 88)
            cuadro.center = r.center
            dibujar_pieza(p, self.n, f, cuadro, self.color, self.f.grande)
        ajustado(p, self.f.chica, "Piezas por armar", 120, BANDEJA_Y - 14, 400, TINTA_SUAVE, ancla="izq")

    def _dibujar_nave(self, p):
        per = self.app.ctx.perfil
        panel(p, (720, 130, 500, 390), color=PAPEL, alfa=240, radio=22, borde=BORDE_PAPEL)
        # nave: imagen del dataset, o un casco provisional
        nave = AD.nave()
        if nave is not None:
            p.blit(pygame.transform.smoothscale(nave, NAVE_RECT[2:]), NAVE_RECT[:2])
        else:
            pygame.draw.ellipse(p, (120, 130, 150), (745, 200, 430, 300))
            pygame.draw.ellipse(p, (90, 100, 120), (745, 200, 430, 300), 4)
        ajustado(p, self.f.normal, "Nave nodriza", 970, 150, 400, TINTA)
        for m, (cx, cy) in SLOTS.items():
            r = pygame.Rect(cx - SLOT_W // 2, cy - SLOT_H // 2, SLOT_W, SLOT_H)
            color = D.COMPONENTES[m - 1]["color"]
            if D.tiene_componente(per, m):
                img = AD.componente(m)
                if img is not None:
                    spr = pygame.transform.smoothscale(img, (120, 80))
                    p.blit(spr, spr.get_rect(center=r.center))
                else:
                    mosaico(p, r.x + 1, r.centery - 30, 40, 28, color, set(range(1, PIEZAS_COMPONENTE + 1)))
            else:
                pygame.draw.rect(p, (60, 66, 84), r, border_radius=12)
                pygame.draw.rect(p, color, r, 3, border_radius=12)
                if self.estado == "mano" and m == self.n:
                    pygame.draw.rect(p, ORO, r.inflate(10, 10), 4, border_radius=16)
            ajustado(p, self.f.chica, D.COMPONENTES[m - 1]["nombre"], r.centerx, r.bottom + 14, r.w + 40, TINTA)

    def _dibujar_en_mano(self, p):
        """El componente armado sigue al cursor hasta que se instala."""
        x, y = self.cursor
        img = AD.componente(self.n)
        if img is not None:
            spr = pygame.transform.smoothscale(img, (180, 120))
            p.blit(spr, spr.get_rect(center=(int(x), int(y))))
            return
        cw, ch = 60, 40
        w = 3 * cw + 2 * 4
        h = 2 * ch + 4
        mosaico(p, int(x - w / 2), int(y - h / 2), cw, ch, self.color, set(range(1, PIEZAS_COMPONENTE + 1)))
