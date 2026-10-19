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
    """Pantalla logica de 1280x720.

    Telefono: pygame.SCALED deja que la GPU estire la imagen (sin reescalar cada cuadro por CPU, que era lo
    que hacia lento el juego). Si el sistema no acepta SCALED, se usa la via antigua por CPU (cpu=True).
    """

    def __init__(self):
        self.cpu = False
        self.puntero = (ANCHO / 2, ALTO / 2)
        if ES_ANDROID:
            try:
                self.pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.FULLSCREEN)
                self.lienzo = self.pantalla
                return
            except pygame.error:
                pass
            self.cpu = True
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.lienzo = pygame.Surface((ANCHO, ALTO)).convert()
            self._geom()
        else:
            try:
                self.pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.RESIZABLE)
            except pygame.error:
                self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
            self.lienzo = self.pantalla

    def _geom(self):
        w, h = pygame.display.get_surface().get_size()
        self.e = min(w / ANCHO, h / ALTO)
        self.tw, self.th = max(1, int(ANCHO * self.e)), max(1, int(ALTO * self.e))
        self.ox, self.oy = (w - self.tw) // 2, (h - self.th) // 2
        self._tam = (w, h)

    def a_logico(self, x, y):
        return (max(0.0, min(ANCHO, (x - self.ox) / self.e)), max(0.0, min(ALTO, (y - self.oy) / self.e)))

    def eventos(self):
        """Con SCALED, pygame ya da los toques en coordenadas logicas. Solo la via CPU necesita convertir."""
        crudos = pygame.event.get()
        if not self.cpu:
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
                if ev.type == pygame.FINGERDOWN and not hay_boton:
                    salida.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                     {"pos": (int(pos[0]), int(pos[1])), "button": 1}))
            else:
                salida.append(ev)
        return salida

    def presentar(self):
        if self.cpu:
            p = pygame.display.get_surface()
            if p.get_size() != self._tam:
                self._geom()
            p.fill((0, 0, 0))
            p.blit(pygame.transform.scale(self.lienzo, (self.tw, self.th)), (self.ox, self.oy))
        pygame.display.flip()


def precalentar_tama(ventana):
    """Genera antes de empezar los huevos y las 72 mascotas (la primera vez tardan y dan tirones).
    Se hace en la pantalla de carga, con barra de progreso, y queda en cache."""
    import arte_tama as AT
    lista = [("huevo", k) for k in range(18)] + [("mascota", (e, et)) for e in AT.ESPECIES for et in range(4)]
    S = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    t0 = time.time()
    for i, (tipo, dato) in enumerate(lista):
        if tipo == "huevo":
            AT.dibujar_huevo(S, dato, ANCHO // 2, ALTO // 2, 1.0, 0.0)
        else:
            AT.dibujar_mascota(S, dato[0], dato[1], ANCHO // 2, ALTO // 2, 1.0, 0.0)
        if i % 6 == 0 or i == len(lista) - 1:
            ventana.lienzo.fill((20, 60, 90))
            ancho_barra = 600
            frac = (i + 1) / len(lista)
            pygame.draw.rect(ventana.lienzo, (255, 255, 255), (ANCHO // 2 - 300, ALTO // 2 + 40, ancho_barra, 24), 3, 8)
            pygame.draw.rect(ventana.lienzo, (255, 200, 90), (ANCHO // 2 - 296, ALTO // 2 + 44, int((ancho_barra - 8) * frac), 16), border_radius=6)
            f = pygame.font.Font(None, 48)
            ventana.lienzo.blit(f.render("Preparando a tus mascotas...", True, (255, 255, 255)),
                                f.render("Preparando a tus mascotas...", True, (0, 0, 0)).get_rect(center=(ANCHO // 2, ALTO // 2 - 30)).topleft)
            ventana.presentar()
            pygame.event.pump()
    registrar(f"PASO precalentado tamagotchi: {len(lista)} dibujos en {time.time() - t0:.1f}s")


DIAG = ES_ANDROID or os.environ.get("NINJA_DIAG") == "1"   # contador en pantalla (para medir el telefono)


def _dibujar_diag(lienzo, fuentes, diag):
    txt = diag.get("txt", "midiendo...")
    f = pygame.font.Font(None, 30)
    img = f.render(txt, True, (255, 255, 255))
    fondo = pygame.Surface((img.get_width() + 12, img.get_height() + 6), pygame.SRCALPHA)
    fondo.fill((0, 0, 0, 170))
    lienzo.blit(fondo, (6, 6))
    lienzo.blit(img, (12, 9))


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
        time.sleep(0.12)
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
        if ES_ANDROID and ventana.cpu:
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
        if SOLO_TAMA:
            precalentar_tama(ventana)
            app = AppTama(entrada, sonidos, fuentes)
        elif JUEGO:
            app = AppSolo(entrada, sonidos, fuentes, JUEGO)
        else:
            app = Aplicacion(entrada, sonidos, fuentes)
        paso(ventana, "8 juego listo")

        back = getattr(pygame, "K_AC_BACK", None)
        mostrar_diag = False
        cuadros = 0
        diag = {"n": 0, "act": 0.0, "dib": 0.0, "flip": 0.0, "ini": time.perf_counter(), "t": 0.0, "fps": 0}
        while not app.salir:
            dt = min(reloj.tick(60) / 1000.0, 0.05)
            t_ini = time.perf_counter()
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
            t_act = time.perf_counter()
            lienzo = ventana.lienzo
            app.dibujar(lienzo)
            t_dib = time.perf_counter()
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
            if DIAG:
                _dibujar_diag(lienzo, fuentes, diag)
            ventana.presentar()
            t_fin = time.perf_counter()
            diag["n"] += 1
            diag["act"] += t_act - t_ini
            diag["dib"] += t_dib - t_act
            diag["flip"] += t_fin - t_dib
            if t_fin - diag["t"] >= 1.0 or diag["t"] == 0.0:
                if diag["t"]:
                    n = max(1, diag["n"])
                    diag["fps"] = round(diag["n"] / (t_fin - diag["t"]))
                    diag["txt"] = (f"{diag['fps']} fps | actualizar {diag['act']/n*1000:.1f} ms | "
                                   f"dibujar {diag['dib']/n*1000:.1f} ms | pantalla {diag['flip']/n*1000:.1f} ms")
                    registrar("DIAG " + diag["txt"])
                    diag["n"] = 0
                    diag["act"] = diag["dib"] = diag["flip"] = 0.0
                diag["t"] = t_fin
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
