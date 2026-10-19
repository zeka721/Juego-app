"""Base comun de las escenas (pantallas) de Ninja Mundo.

Una escena recibe 'app' (Aplicacion) con:
    app.ctx        Contexto: ctx.sonidos, ctx.f (fuentes), ctx.perfil, ctx.mejoras
    app.entrada    la entrada real (mando/raton)
    app.ir(escena) cambia de escena
    app.ir_menu()  vuelve al menu principal
Cada cuadro se llama actualizar(dt, ctrl) y dibujar(pantalla). ESC llama tecla_esc().
"""

import pygame

from ajustes import ANCHO
from nucleo import fondo


class Escena:
    def __init__(self, app):
        self.app = app
        self.t = 0.0

    @property
    def f(self):
        return self.app.ctx.f

    def actualizar(self, dt, ctrl):
        self.t += dt

    def dibujar(self, p):
        pass

    def tecla_esc(self):
        pass


def fondo_fiesta(p, t):
    """Cielo con nubes que pasan."""
    fondo(p, (110, 180, 250), (200, 235, 255))
    for i in range(6):
        x = (i * 260 + t * 18 * (1 + i % 3)) % (ANCHO + 200) - 100
        y = 80 + (i * 97) % 220
        for dx, dy, r in ((0, 0, 34), (36, 10, 28), (-34, 12, 26)):
            pygame.draw.circle(p, (255, 255, 255), (int(x + dx), int(y + dy)), r)
