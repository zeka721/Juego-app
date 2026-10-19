"""Ninja Mundo - juegos de movimiento con el mando ESP32.

Uso:   python main.py        (con el mando conectado por USB; cierra el Monitor Serial)
Teclas: H calibrar giro | T calibrar deslizamiento | M mando/raton | [ ] sensibilidad del corte
        G golpe manual | F1 diagnostico | F11 pantalla completa | ESC volver
Ajustes (puerto, sensibilidad, etc.): ajustes.py
"""

import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _carpeta_datos():
    return os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))


def registrar(texto):
    """Anota una linea en error.log (sirve para diagnosticar en el telefono)."""
    try:
        with open(os.path.join(_carpeta_datos(), "error.log"), "a", encoding="utf-8") as f:
            f.write(texto + "\n")
    except Exception:
        pass


def mostrar_error(texto, segundos=300):
    """Muestra un error en pantalla (en el telefono no se ve la consola) y lo guarda en error.log."""
    print(texto)
    try:
        with open(os.path.join(_carpeta_datos(), "error.log"), "w", encoding="utf-8") as f:
            f.write(texto)
    except Exception:
        pass
    try:
        import pygame
        pygame.init()
        pantalla = pygame.display.set_mode((1280, 720))
        fuente = pygame.font.Font(None, 28)
        pantalla.fill((40, 0, 0))
        lineas = []
        for linea in texto.splitlines():
            while len(linea) > 120:
                lineas.append(linea[:120])
                linea = linea[120:]
            lineas.append(linea)
        lineas = lineas[-30:]
        pantalla.blit(fuente.render("ERROR AL INICIAR - toca la pantalla para cerrar", True, (255, 230, 120)), (12, 12))
        for i, linea in enumerate(lineas):
            pantalla.blit(fuente.render(linea, True, (255, 220, 220)), (12, 50 + i * 22))
        pygame.display.flip()
        fin = time.time() + segundos
        while time.time() < fin:
            for ev in pygame.event.get():
                if ev.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    return
            time.sleep(0.05)
    except Exception:
        pass


try:
    import pygame

    from ajustes import ANCHO, ALTO, ES_ANDROID
    from aventura import Aplicacion
    from entrada import Entrada
    from nucleo import Fuentes, Sonidos, escribir
except Exception:
    mostrar_error("Fallo al cargar los modulos:\n\n" + traceback.format_exc())
    raise SystemExit(1)


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
                registrar(f"QUIT recibido en el cuadro {cuadros} (tiempo {time.time():.1f}) - evento del sistema")
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
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        mostrar_error("Error en el juego:\n\n" + traceback.format_exc())
        raise
