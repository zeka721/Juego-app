"""Ayudas para probar minijuegos sin pantalla ni mando (SDL en modo 'dummy').

    from pruebas_util import crear_ctx, simular, capturar
    ctx = crear_ctx()
    juego = MiJuego(ctx, nivel=2)
    ctrl = ControlSim()
    def bot(juego, ctrl, t):          # se llama cada cuadro ANTES de actualizar
        ctrl.mover_a(640 + 200 * math.sin(t), 360)   # mueve el cursor (cortando automatico por velocidad)
        # ctrl.cortando = True       # fuerza un tajo
        # ctrl.clic = True           # pulsa el boton
        # ctrl.golpe = True          # da un golpe con el mando
    simular(juego, ctrl, bot, segundos=30)
    capturar(juego, "/tmp/shots/mi_juego.png")
"""

import os
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from ajustes import ANCHO, ALTO
from nucleo import Contexto, ControlSim, Fuentes, Mejoras, Perfil, Sonidos

_pantalla = None


def pantalla():
    global _pantalla
    if _pantalla is None:
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        _pantalla = pygame.display.set_mode((ANCHO, ALTO))
    return _pantalla


def crear_ctx(mejoras=()):
    """Contexto de prueba con una partida temporal (no toca partida.json)."""
    pantalla()
    perfil = Perfil(os.path.join(tempfile.mkdtemp(), "partida_prueba.json"))
    mej = Mejoras(perfil)
    for m in mejoras:
        mej.agregar(m)
    return Contexto(Sonidos(), Fuentes(), perfil, mej)


def simular(juego, ctrl, bot=None, segundos=30.0, dt=1 / 60, dibujar_cada=30):
    """Corre el minijuego cuadro a cuadro. Devuelve los segundos simulados."""
    p = pantalla()
    t = 0.0
    n = 0
    while t < segundos and not juego.terminado:
        if bot:
            bot(juego, ctrl, t)
        juego.actualizar(dt, ctrl)
        ctrl.fin_cuadro()
        if n % dibujar_cada == 0:
            juego.dibujar(p)             # asegura que dibujar() no falla durante el juego
        t += dt
        n += 1
    return t


def capturar(juego, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    p = pantalla()
    juego.dibujar(p)
    pygame.image.save(p, ruta)
