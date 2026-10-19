"""Gusano: juego minimo de PRUEBA para descartar si el problema es el telefono o la compilacion.

Se construye igual que Ninja Mundo (Buildozer + python-for-android + pygame 2.6.1), pero solo usa pygame:
sin numpy, sin fuentes del sistema, sin sonido, sin archivos propios. Un dedo mueve al gusano; come puntos y crece.
Cada paso del arranque se anota en error.log; si la app se cae, la proxima vez muestra ese registro en pantalla.
"""
import math
import os
import random
import sys
import time
import traceback

ES_ANDROID = hasattr(sys, "getandroidapilevel")
CARPETA = os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))
RUTA_LOG = os.path.join(CARPETA, "error.log")
T0 = time.time()
W, H = 1280, 720


def registrar(texto):
    linea = f"[{time.time() - T0:6.1f}s] {texto}"
    print("GUSANO " + linea, flush=True)
    try:
        with open(RUTA_LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def leer(ruta):
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


previo = leer(RUTA_LOG)
previo = previo if (previo.strip() and "FIN LIMPIO" not in previo) else ""
open(RUTA_LOG, "w").close()
try:
    import faulthandler
    _fh = open(os.path.join(CARPETA, "fatal.log"), "a")
    faulthandler.enable(file=_fh, all_threads=True)
except Exception as e:
    registrar(f"faulthandler: {e}")
registrar(f"PASO 0 inicio (android={ES_ANDROID}, python={sys.version.split()[0]}, carpeta={CARPETA})")

try:
    registrar("PASO 1 importando pygame")
    import pygame
    registrar(f"PASO 2 pygame {pygame.version.ver} SDL {'.'.join(map(str, pygame.get_sdl_version()))} importado")
except Exception:
    registrar("ERROR importando pygame:\n" + traceback.format_exc())
    raise


def texto(p, fuente, s, x, y, color=(255, 255, 255), centro=True):
    img = fuente.render(s, True, color)
    p.blit(img, img.get_rect(center=(x, y)) if centro else (x, y))


def mostrar_previo(pantalla, fuente, contenido):
    w, h = pantalla.get_size()
    lineas = contenido.strip().splitlines()[-18:]
    fin = time.time() + 600
    pygame.event.clear()
    while time.time() < fin:
        pantalla.fill((30, 30, 90))
        y = 20
        for ln in ["LA VEZ ANTERIOR SE CERRO. Quedo anotado:"] + lineas + ["", "Toca para continuar"]:
            pantalla.blit(fuente.render(ln[:110], True, (255, 240, 200)), (20, y))
            y += fuente.get_linesize()
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN, pygame.KEYDOWN, pygame.QUIT):
                return
        time.sleep(0.05)


def main():
    registrar("PASO 3 iniciando pantalla")
    pygame.display.init()
    pygame.font.init()
    pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if ES_ANDROID else pygame.display.set_mode((W, H))
    sw, sh = pantalla.get_size()
    registrar(f"PASO 4 pantalla {sw}x{sh}")
    pantalla.fill((20, 90, 60))
    pygame.display.flip()
    fuente = pygame.font.Font(None, max(20, sh // 28))
    grande = pygame.font.Font(None, max(40, sh // 10))
    registrar("PASO 5 fuentes listas")
    if previo:
        mostrar_previo(pantalla, fuente, previo)

    reloj = pygame.time.Clock()
    cabeza = [sw / 2, sh / 2]
    objetivo = list(cabeza)
    cuerpo = [tuple(cabeza)] * 10
    largo = 10
    puntos = 0
    comida = [random.randint(60, sw - 60), random.randint(120, sh - 60)]
    cuadros = 0
    toques = 0
    back = getattr(pygame, "K_AC_BACK", None)
    corriendo = True
    registrar("PASO 6 bucle principal")
    while corriendo:
        dt = min(reloj.tick(60) / 1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                registrar("QUIT recibido")
                corriendo = False
            elif ev.type == pygame.KEYDOWN and (ev.key == pygame.K_ESCAPE or (back is not None and ev.key == back)):
                registrar("tecla atras/escape")
                corriendo = False
            elif ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                if ev.type == pygame.MOUSEBUTTONDOWN or ev.buttons[0]:
                    objetivo = [ev.pos[0], ev.pos[1]]
                    toques += ev.type == pygame.MOUSEBUTTONDOWN
            elif ev.type == pygame.FINGERDOWN or ev.type == pygame.FINGERMOTION:
                objetivo = [ev.x * sw, ev.y * sh]

        dx, dy = objetivo[0] - cabeza[0], objetivo[1] - cabeza[1]
        d = math.hypot(dx, dy)
        if d > 4:
            v = min(d * 4, 420) * dt
            cabeza[0] += dx / d * v
            cabeza[1] += dy / d * v
        cuerpo.append((cabeza[0], cabeza[1]))
        cuerpo = cuerpo[-largo:]
        if math.hypot(cabeza[0] - comida[0], cabeza[1] - comida[1]) < 34:
            puntos += 1
            largo += 6
            comida = [random.randint(60, sw - 60), random.randint(120, sh - 60)]

        pantalla.fill((20, 90, 60))
        for i, (x, y) in enumerate(cuerpo):
            r = 10 + int(14 * i / max(1, len(cuerpo)))
            pygame.draw.circle(pantalla, (240, 210, 60) if i % 2 else (250, 150, 40), (int(x), int(y)), r)
        pygame.draw.circle(pantalla, (255, 60, 80), (int(comida[0]), int(comida[1])), 18)
        pygame.draw.circle(pantalla, (255, 255, 255), (int(cabeza[0] + 8), int(cabeza[1] - 6)), 5)
        texto(pantalla, grande, f"Puntos: {puntos}", sw // 2, 50)
        texto(pantalla, fuente, f"Python {sys.version.split()[0]}  pygame {pygame.version.ver}  cuadros {cuadros}  toques {toques}", sw // 2, sh - 24)
        pygame.display.flip()
        if cuadros == 0:
            registrar("PASO 7 primer cuadro dibujado")
        if cuadros == 180:
            registrar("PASO 8 180 cuadros (3 s) sin problemas")
        cuadros += 1
    registrar("FIN LIMPIO")
    pygame.quit()


try:
    main()
except Exception:
    registrar("ERROR en main:\n" + traceback.format_exc())
    raise
