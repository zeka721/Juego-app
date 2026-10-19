"""Ninja Mundo - juegos de movimiento con el mando ESP32.

Uso:   python main.py        (con el mando conectado por USB; cierra el Monitor Serial)
Teclas: H calibrar giro | T calibrar deslizamiento | M mando/raton | [ ] sensibilidad del corte
        G golpe manual | F1 diagnostico | F11 pantalla completa | ESC volver
Ajustes (puerto, sensibilidad, etc.): ajustes.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from ajustes import ANCHO, ALTO, ES_ANDROID
from aventura import Aplicacion
from entrada import Entrada
from nucleo import Fuentes, Sonidos, escribir


def main(max_cuadros=None, cada_cuadro=None):
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    try:
        pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.RESIZABLE)
    except pygame.error:
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ninja Mundo")
    pygame.mouse.set_visible(False)
    reloj = pygame.time.Clock()

    entrada = Entrada()
    fuentes = Fuentes()
    app = Aplicacion(entrada, Sonidos(), fuentes)
    mostrar_diag = False
    cuadros = 0

    while not app.salir:
        dt = min(reloj.tick(60) / 1000.0, 0.05)
        eventos = pygame.event.get()
        for ev in eventos:
            if ev.type == pygame.QUIT:
                app.salir = True
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    app.tecla_esc()
                elif ev.key == pygame.K_F1:
                    mostrar_diag = not mostrar_diag
                elif ev.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

        entrada.actualizar(dt, eventos)
        if not entrada.calibrando:           # el juego se pausa mientras se calibra
            app.actualizar(dt, entrada)
        app.dibujar(pantalla)
        entrada.dibujar_cursor(pantalla)

        if entrada.calibrando or True:
            entrada.dibujar_aviso_cal(pantalla, fuentes.normal)
        if mostrar_diag:
            for i, texto in enumerate(entrada.lineas_diagnostico()):
                escribir(pantalla, fuentes.chica, texto, 12, ALTO - 150 + i * 24, (255, 255, 255), ancla="izq")
        else:
            estado = entrada.lineas_diagnostico()[0]
            if not ES_ANDROID and (entrada.mando is None or not entrada.mando.conectado or entrada.mando.lecturas == 0):
                escribir(pantalla, fuentes.chica, estado[:120], 12, ALTO - 14, (255, 220, 160), ancla="izq")
        pygame.display.flip()

        cuadros += 1
        if cada_cuadro:
            cada_cuadro(cuadros, app, entrada, pantalla)
        if max_cuadros and cuadros >= max_cuadros:
            break

    pygame.quit()


if __name__ == "__main__":
    main()
