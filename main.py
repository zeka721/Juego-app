"""Ninja Mundo - juegos de movimiento con el mando ESP32.

PC:       python main.py          (menu completo; mando por USB o raton)
Telefono: arranca directo en el Tamagotchi, solo con toques (ver app_tama.py).
          Para probar la version del telefono en el PC:  NINJA_SOLO_TAMA=1 python main.py
Teclas (PC): H calibrar giro | T calibrar deslizamiento | M mando/raton | [ ] sensibilidad
             G golpe manual | F1 diagnostico | F11 pantalla completa | ESC volver
Ajustes (puerto, sensibilidad, etc.): ajustes.py

DIAGNOSTICO SIN CABLE: cada paso del arranque se anota en error.log (en la carpeta privada de la app).
Si la app se cae, al abrirla de nuevo muestra en pantalla lo que quedo anotado de la vez anterior.
"""

import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ES_ANDROID = hasattr(sys, "getandroidapilevel")


def _juego_solo():
    """'tama' o 'ruinas' si esta app es de un solo juego; '' = menu completo (PC)."""
    try:       # tools/armar.py escribe juego.txt dentro del APK
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "juego.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        pass
    if os.environ.get("NINJA_JUEGO"):
        return os.environ["NINJA_JUEGO"].strip()
    if os.environ.get("NINJA_SOLO_TAMA") == "1" or ES_ANDROID:
        return "tama"
    return ""


JUEGO = _juego_solo()
SOLO_TAMA = JUEGO == "tama"
PASOS_VISIBLES = ES_ANDROID          # diagnostico: muestra los pasos del arranque en pantalla


def _carpeta_datos():
    return os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))


RUTA_LOG = os.path.join(_carpeta_datos(), "error.log")
RUTA_FATAL = os.path.join(_carpeta_datos(), "fatal.log")
RUTA_PREVIO = os.path.join(_carpeta_datos(), "error_previo.log")
_T0 = time.time()


def registrar(texto):
    """Anota una linea y la fuerza a disco (sobrevive aunque la app se caiga de golpe)."""
    linea = f"[{time.time() - _T0:6.1f}s] {texto}"
    print(linea, flush=True)
    try:
        with open(RUTA_LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def _leer(ruta):
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def preparar_registro():
    """Devuelve el texto de la vez anterior si esa vez NO termino bien; luego empieza un registro nuevo."""
    previo = _leer(RUTA_LOG)
    fatal = _leer(RUTA_FATAL).strip()
    cayo = bool(previo.strip()) and "FIN LIMPIO" not in previo
    texto = ""
    if cayo or fatal:
        texto = previo.strip()
        if fatal:
            texto += "\n--- fatal.log ---\n" + fatal
        try:
            with open(RUTA_PREVIO, "w", encoding="utf-8") as f:
                f.write(texto)
        except Exception:
            pass
    for r in (RUTA_LOG, RUTA_FATAL):
        try:
            open(r, "w").close()
        except Exception:
            pass
    try:                      # si Python se cae por dentro (segfault), deja el rastro en fatal.log
        import faulthandler
        global _FH
        _FH = open(RUTA_FATAL, "w")
        faulthandler.enable(file=_FH, all_threads=True)
    except Exception as e:
        registrar(f"faulthandler no disponible: {e}")
    return texto


def _partir(texto, fuente, ancho_max):
    lineas = []
    for crudo in texto.splitlines():
        actual = ""
        for palabra in crudo.split(" "):
            prueba = (actual + " " + palabra).strip()
            if fuente.size(prueba)[0] > ancho_max and actual:
                lineas.append(actual)
                actual = palabra
            else:
                actual = prueba
        lineas.append(actual)
    return lineas


def pantalla_texto(titulo, texto, color_fondo=(120, 20, 20), segundos=600):
    """Muestra texto largo en pantalla hasta que se toque. Sirve para leer errores sin cable."""
    import pygame
    try:
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        pantalla = pygame.display.get_surface() or pygame.display.set_mode((1280, 720))
        w, h = pantalla.get_size()
        fuente = pygame.font.Font(None, max(18, h // 30))
        fuente_t = pygame.font.Font(None, max(26, h // 18))
        lineas = _partir(texto, fuente, w - 40)
        alto_linea = fuente.get_linesize()
        max_lineas = max(1, (h - 120) // alto_linea)
        lineas = lineas[-max_lineas:]
        fin = time.time() + segundos
        pygame.event.clear()
        while time.time() < fin:
            pantalla.fill(color_fondo)
            pantalla.blit(fuente_t.render(titulo, True, (255, 255, 255)), (20, 14))
            y = 70
            for ln in lineas:
                pantalla.blit(fuente.render(ln, True, (255, 240, 220)), (20, y))
                y += alto_linea
            pantalla.blit(fuente.render("Toca la pantalla para continuar", True, (255, 255, 120)), (20, h - alto_linea - 8))
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN, pygame.FINGERDOWN, pygame.QUIT):
                    return
            time.sleep(0.05)
    except Exception:
        pass


def mostrar_error(texto):
    registrar("ERROR:\n" + texto)
    pantalla_texto("Ninja Mundo: algo fallo (toma una foto de esta pantalla)", texto)


# ------------------------------------------------------------------ arranque
TEXTO_PREVIO = preparar_registro()
registrar(f"PASO 0 main.py iniciado (android={ES_ANDROID}, juego={JUEGO or 'menu'}, python={sys.version.split()[0]})")

try:
    registrar("PASO 1 importando pygame")
    import pygame
    registrar(f"pygame {pygame.version.ver} / SDL {'.'.join(map(str, pygame.get_sdl_version()))} importado")
    from ajustes import ANCHO, ALTO
    registrar("PASO 1b ajustes importado")
    from entrada import Entrada
    from nucleo import Fuentes, Sonidos, escribir
    if SOLO_TAMA:
        from app_tama import AppTama
    elif JUEGO:
        from app_solo import AppSolo
    else:
        from aventura import Aplicacion
    registrar("PASO 1c modulos del juego importados")
except Exception:
    mostrar_error("Fallo al cargar los modulos:\n\n" + traceback.format_exc())
    raise SystemExit(1)


class Ventana:
    """En el telefono se dibuja en un lienzo de 1280x720 y se estira a la pantalla, con barras si hace falta."""

    def __init__(self):
        if ES_ANDROID:
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.lienzo = pygame.Surface((ANCHO, ALTO)).convert()
        else:
            try:
                self.pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.RESIZABLE)
            except pygame.error:
                self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
            self.lienzo = self.pantalla
        self.puntero = (ANCHO / 2, ALTO / 2)
        self._geom()

    def _geom(self):
        w, h = pygame.display.get_surface().get_size()
        self.e = min(w / ANCHO, h / ALTO)
        self.tw, self.th = max(1, int(ANCHO * self.e)), max(1, int(ALTO * self.e))
        self.ox, self.oy = (w - self.tw) // 2, (h - self.th) // 2
        self._tam = (w, h)

    def a_logico(self, x, y):
        if not ES_ANDROID:
            return (x, y)
        return (max(0.0, min(ANCHO, (x - self.ox) / self.e)), max(0.0, min(ALTO, (y - self.oy) / self.e)))

    def eventos(self):
        """Eventos con la posicion ya en coordenadas del juego (y los dedos tratados como raton)."""
        crudos = pygame.event.get()
        if not ES_ANDROID:
            return crudos
        w, h = self._tam
        hay_boton = any(e.type == pygame.MOUSEBUTTONDOWN for e in crudos)
        salida = []
        for ev in crudos:
            if ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                pos = self.a_logico(*ev.pos)
                self.puntero = pos
                d = dict(ev.dict)
                d["pos"] = (int(pos[0]), int(pos[1]))
                salida.append(pygame.event.Event(ev.type, d))
            elif ev.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
                pos = self.a_logico(ev.x * w, ev.y * h)
                self.puntero = pos
                if ev.type == pygame.FINGERDOWN and not hay_boton:      # por si el sistema no hace el toque-raton
                    salida.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                     {"pos": (int(pos[0]), int(pos[1])), "button": 1}))
            else:
                salida.append(ev)
        return salida

    def presentar(self):
        if ES_ANDROID:
            p = pygame.display.get_surface()
            if p.get_size() != self._tam:
                self._geom()
            p.fill((0, 0, 0))
            p.blit(pygame.transform.scale(self.lienzo, (self.tw, self.th)), (self.ox, self.oy))
        pygame.display.flip()


def paso(ventana, texto):
    """Anota el paso y, si PASOS_VISIBLES, lo deja ver en pantalla un instante."""
    registrar("PASO " + texto)
    if not PASOS_VISIBLES or ventana is None:
        return
    try:
        ventana.lienzo.fill((10, 10, 40))
        f = pygame.font.Font(None, 48)
        ventana.lienzo.blit(f.render("Arranque: " + texto, True, (255, 255, 255)), (40, ALTO // 2 - 20))
        ventana.presentar()
        pygame.event.pump()
        time.sleep(0.4)
    except Exception:
        pass


def main(max_cuadros=None, cada_cuadro=None):
    ventana = None
    try:
        registrar("PASO 2 iniciando pantalla")
        pygame.display.init()
        pygame.font.init()
        if ES_ANDROID:            # SysFont("arial") no existe en Android: usar la letra incluida en pygame
            pygame.font.SysFont = lambda nombre=None, tam=20, bold=False, italic=False: pygame.font.Font(None, int(tam * 1.15))
        ventana = Ventana()
        pygame.display.set_caption("Ninja Mundo")
        pygame.mouse.set_visible(False)
        if ES_ANDROID:
            pygame.mouse.get_pos = lambda: (int(ventana.puntero[0]), int(ventana.puntero[1]))
        paso(ventana, "3 pantalla lista " + str(pygame.display.get_surface().get_size()))

        if TEXTO_PREVIO:
            pantalla_texto("La vez anterior la app se cerro. Esto quedo anotado:", TEXTO_PREVIO, (30, 30, 90))

        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
            pygame.mixer.init()
            paso(ventana, "4 sonido listo")
        except Exception as e:
            paso(ventana, f"4 sin sonido ({e})")

        reloj = pygame.time.Clock()
        entrada = Entrada()
        paso(ventana, "5 entrada lista")
        fuentes = Fuentes()
        paso(ventana, "6 fuentes listas")
        sonidos = Sonidos()
        paso(ventana, "7 sonidos listos")
        ventana.lienzo.fill((20, 60, 90))
        escribir(ventana.lienzo, fuentes.grande, "Preparando a tu mascota...", ANCHO / 2, ALTO / 2, (255, 255, 255))
        ventana.presentar()
        if SOLO_TAMA:
            app = AppTama(entrada, sonidos, fuentes)
        elif JUEGO:
            app = AppSolo(entrada, sonidos, fuentes, JUEGO)
        else:
            app = Aplicacion(entrada, sonidos, fuentes)
        paso(ventana, "8 juego listo")

        back = getattr(pygame, "K_AC_BACK", None)
        mostrar_diag = False
        cuadros = 0
        while not app.salir:
            dt = min(reloj.tick(60) / 1000.0, 0.05)
            eventos = ventana.eventos()
            for ev in eventos:
                if ev.type == pygame.QUIT:
                    registrar(f"QUIT recibido en el cuadro {cuadros}")
                    app.salir = True
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE or (back is not None and ev.key == back):
                        app.tecla_esc()
                    elif ev.key == pygame.K_F1 and not ES_ANDROID:
                        mostrar_diag = not mostrar_diag
                    elif ev.key == pygame.K_F11 and not ES_ANDROID:
                        pygame.display.toggle_fullscreen()
                elif ev.type == getattr(pygame, "APP_WILLENTERBACKGROUND", -1):
                    registrar("app pasa a segundo plano: guardando")
                    g = getattr(app, "guardar", None)
                    if g:
                        g()

            entrada.actualizar(dt, eventos)
            if not entrada.calibrando:           # el juego se pausa mientras se calibra
                app.actualizar(dt, entrada)
            lienzo = ventana.lienzo
            app.dibujar(lienzo)
            entrada.dibujar_cursor(lienzo)
            if not ES_ANDROID:
                entrada.dibujar_aviso_cal(lienzo, fuentes.normal)
                if mostrar_diag:
                    for i, texto in enumerate(entrada.lineas_diagnostico()):
                        escribir(lienzo, fuentes.chica, texto, 12, ALTO - 150 + i * 24, (255, 255, 255), ancla="izq")
                else:
                    estado = entrada.lineas_diagnostico()[0]
                    if entrada.mando is None or not entrada.mando.conectado or entrada.mando.lecturas == 0:
                        escribir(lienzo, fuentes.chica, estado[:120], 12, ALTO - 14, (255, 220, 160), ancla="izq")
            ventana.presentar()
            if cuadros == 0:
                registrar("PASO 9 primer cuadro del juego dibujado")
            elif cuadros == 120:
                registrar("PASO 10 120 cuadros sin problemas")

            cuadros += 1
            if cada_cuadro:
                cada_cuadro(cuadros, app, entrada, lienzo)
            if max_cuadros and cuadros >= max_cuadros:
                break
        g = getattr(app, "guardar", None)
        if g:
            g()
    except Exception:
        mostrar_error("Error en el juego:\n\n" + traceback.format_exc())
        raise SystemExit(1)
    registrar("FIN LIMPIO")
    pygame.quit()


if __name__ == "__main__":
    main()
