"""Base comun de los PASOS de cocina (cada habilidad es una mini-vista jugable).

Un paso trabaja sobre UN ingrediente (o una mezcla) y dura unos segundos. El orquestador (j_cocina.Cocina)
crea el paso con `crear_paso(ctx, spec, dif, mods)`, llama `paso.actualizar(dt, ctrl)` y `paso.dibujar(p)`
cada cuadro y, cuando `paso.terminado` es True, lee `paso.calidad` (0..1).

    from cocina_base import Paso, paso, AREA
    @paso("cortar")
    class Cortar(Paso):
        habilidad = "cortar"
        def iniciar(self): ...                     # crea el estado (usa self.spec, self.dif, self.mods)
        def tiempo_base(self): return 25.0
        def actualizar_paso(self, dt, ctrl): ...  # logica; llama self.avanzar(frac) y self.terminar(calidad)
        def dibujar_paso(self, p): ...             # dibuja DENTRO de AREA (el fondo ya esta pintado)

Reglas para TODOS los pasos (nino de 5 anos, mando-espada o raton):
  * Se puede completar SOLO moviendo el cursor (sin clic ni golpe); clic/golpe/tajo pueden ayudar pero no ser obligatorios.
  * Nunca hay castigo duro: si se acaba el tiempo el paso termina con calidad = max(0.25, progreso). Con el
    cursor quieto (bot inerte) el paso igual termina al acabarse el tiempo y no se cuelga.
  * El cursor ES la herramienta: dibujala siguiendo a ctrl.pos (cuchillo, tijera, pelador, rallador, cuchara...).
    El cursor global lo dibuja Entrada, no lo repitas; dibuja tu herramienta con un ligero desfase para que el
    punto de accion sea claro.
  * La dificultad `dif` (0..10) endurece: mas repeticiones, zonas mas pequenas, menos tiempo. dif=0 debe ser muy facil.
  * Las mejoras de la ruleta llegan en `self.mods`: pot (potencia: cada gesto cuenta mas), alc (alcance/zonas mas
    grandes), tiempo (multiplica el tiempo), lento (factor <=1 que baja velocidades de agujas/objetos).
"""

import math
import random

import pygame

from ajustes import ANCHO, ALTO
from nucleo import aclarar, barra, escribir, explosion, oscurecer, panel, V2, TextoFlotante, Particula

# zona donde dibuja cada paso (la cabecera de la receta ocupa los 100 px de arriba)
AREA = pygame.Rect(0, 100, ANCHO, ALTO - 100)

PASOS = {}          # habilidad -> clase

MIN_PASO = 0.0      # sin tiempo minimo forzado: la barra de abajo muestra el avance REAL de la tarea


def paso(habilidad):
    """Decorador: registra la clase de un paso para esa habilidad."""
    def reg(cls):
        cls.habilidad = habilidad
        PASOS[habilidad] = cls
        return cls
    return reg


class Mods:
    """Mejoras de la ruleta para los pasos."""

    def __init__(self, pot=1.0, alc=1.0, tiempo=1.0, lento=1.0):
        self.pot, self.alc, self.tiempo, self.lento = pot, alc, tiempo, lento


MODS_NORMALES = Mods()


class Paso:
    """Clase base de un paso de cocina. Sobrescribe iniciar / tiempo_base / actualizar_paso / dibujar_paso."""

    habilidad = ""
    titulo = ""                     # instruccion corta que muestra el orquestador ("¡Pela la zanahoria!")
    fondo_tipo = "mesada"           # mesada | fuego | horno (el fondo que pinta la base)

    def __init__(self, ctx, spec, dif=0.0, mods=None):
        self.ctx = ctx
        self.f = ctx.f
        self.sonidos = ctx.sonidos
        self.spec = dict(spec or {})
        self.ing = self.spec.get("ing")
        self.herr = self.spec.get("herr")
        self.dif = max(0.0, min(10.0, float(dif)))
        self.mods = mods or MODS_NORMALES
        self.t = 0.0
        self.prog = 0.0              # 0..1 (barra de avance)
        self.terminado = False
        self.calidad = 0.0
        self.mensaje = ""
        self.particulas = []
        self.flotantes = []
        self.t_cierre = 0.0          # pausa breve tras terminar (para ver el resultado antes de pasar al siguiente)
        self.iniciar()
        # ajusta tiempo_base() para que un buen jugador termine hacia los 30-40 s; el limite nunca baja de 45 s
        self.t_max = max(45.0, float(self.tiempo_base()) * max(0.5, self.mods.tiempo))
        self._pend = None

    # ---- a sobrescribir
    def iniciar(self):
        pass

    def tiempo_base(self):
        return 25.0

    def actualizar_paso(self, dt, ctrl):
        pass

    def dibujar_paso(self, p):
        pass

    # ---- servicios
    def avanzar(self, frac):
        self.prog = max(0.0, min(1.0, self.prog + frac))

    def terminar(self, calidad=None, mensaje=""):
        """Termina el paso. calidad 0..1 (por defecto: segun el progreso, minimo 0.25)."""
        if self.terminado:
            return
        if self.t < MIN_PASO:
            if self._pend is None:             # se cerrara cuando se cumplan los 30 s minimos
                self._pend = (calidad, mensaje)
            return
        if calidad is None:
            calidad = self.prog
        self.calidad = max(0.25, min(1.0, float(calidad)))
        self.mensaje = mensaje
        self.terminado = True

    @property
    def tiempo_restante(self):
        return max(0.0, self.t_max - self.t)

    def sumar_particulas(self, x, y, color, n=10):
        explosion(self.particulas, x, y, color, n=n, vida=0.6)

    def texto_flotante(self, texto, x, y, color=(255, 240, 120)):
        self.flotantes.append(TextoFlotante(texto, x, y, color))

    # ---- ciclo (no sobrescribir)
    def actualizar(self, dt, ctrl):
        self.t += dt
        self.particulas = [x for x in self.particulas if x.actualizar(dt)]
        self.flotantes = [x for x in self.flotantes if x.actualizar(dt)]
        if self.terminado:
            self.t_cierre += dt
            return
        self.actualizar_paso(dt, ctrl)
        if self._pend is not None and not self.terminado and self.t >= MIN_PASO:
            c, m = self._pend
            self.terminar(c, m)
        if not self.terminado and self.t >= self.t_max:
            self.terminar(self.prog, "¡Se acabó el tiempo, pero quedó bien!")

    def dibujar(self, p):
        fondo_cocina(p, self.fondo_tipo)
        self.dibujar_paso(p)
        for x in self.particulas:
            x.dibujar(p)
        for x in self.flotantes:
            x.dibujar(p, self.f.normal)
        self.dibujar_barras(p)

    def dibujar_barras(self, p):
        """Barra de avance (abajo) y de tiempo (fina, arriba del area)."""
        mostrado = self.prog
        barra(p, (340, ALTO - 34, 600, 20), mostrado, color=(255, 190, 60), color_fondo=(80, 55, 40),
              borde=(255, 255, 255))
        fr = self.tiempo_restante / max(0.1, self.t_max)
        barra(p, (340, AREA.y + 4, 600, 8), fr, color=(110, 200, 255) if fr > 0.25 else (255, 120, 90),
              color_fondo=(80, 55, 40), borde=(255, 255, 255))


class PasoGenerico(Paso):
    """Respaldo si una habilidad aun no tiene clase: mueve el cursor por la zona brillante hasta llenar la barra."""

    titulo = "¡Sigue la luz!"

    def iniciar(self):
        self.zx, self.zy = ANCHO / 2, 400.0

    def tiempo_base(self):
        return 12.0

    def actualizar_paso(self, dt, ctrl):
        self.zx = ANCHO / 2 + 220 * math.sin(self.t * 0.9)
        self.zy = 400 + 80 * math.sin(self.t * 1.7)
        if math.hypot(ctrl.pos.x - self.zx, ctrl.pos.y - self.zy) < 110:
            self.avanzar(dt / 5.0)
        if self.prog >= 1.0:
            self.terminar(1.0)

    def dibujar_paso(self, p):
        pygame.draw.circle(p, (255, 230, 120), (int(self.zx), int(self.zy)), 100, 6)
        escribir(p, self.f.grande, self.habilidad, ANCHO / 2, 160, (90, 60, 40), contorno=None)


def crear_paso(ctx, spec, dif=0.0, mods=None):
    """Instancia el paso de la habilidad spec["h"] (o el generico si no esta registrada)."""
    cargar_pasos()
    cls = PASOS.get(spec.get("h"), PasoGenerico)
    p = cls(ctx, spec, dif, mods)
    return p


_cargado = []
MODULOS_PASOS = ("cocina_pasos_cortes", "cocina_pasos_masas", "cocina_pasos_fuego")


def cargar_pasos():
    """Importa los modulos que registran pasos (los que existan)."""
    if _cargado:
        return
    _cargado.append(True)
    import importlib
    for nombre in MODULOS_PASOS:
        try:
            importlib.import_module(nombre)
        except ModuleNotFoundError as e:
            if e.name != nombre:
                raise


# ----------------------------------------------------------------------------- fondos
_fondos = {}


def fondo_cocina(p, tipo="mesada"):
    """Pinta el fondo de la cocina (cacheado): mesada de madera, fuego (cocina con hornillas) u horno."""
    s = _fondos.get(tipo)
    if s is None:
        s = pygame.Surface((ANCHO, ALTO))
        if tipo == "fuego":
            s.fill((88, 92, 110))
            for x in range(0, ANCHO, 64):
                pygame.draw.line(s, (78, 82, 100), (x, 0), (x, ALTO), 2)
            pygame.draw.rect(s, (60, 62, 76), (0, 560, ANCHO, ALTO - 560))
            pygame.draw.rect(s, (110, 114, 134), (0, 556, ANCHO, 8))
        elif tipo == "horno":
            s.fill((120, 100, 90))
            for y in range(0, ALTO, 48):
                pygame.draw.line(s, (108, 90, 80), (0, y), (ANCHO, y), 2)
            pygame.draw.rect(s, (70, 56, 50), (0, 580, ANCHO, ALTO - 580))
        else:
            s.fill((255, 238, 205))
            for x in range(0, ANCHO, 80):
                pygame.draw.line(s, (240, 218, 175), (x, 0), (x, 580), 2)
            for y in range(0, 580, 80):
                pygame.draw.line(s, (240, 218, 175), (0, y), (ANCHO, y), 2)
            pygame.draw.rect(s, (205, 150, 95), (0, 580, ANCHO, ALTO - 580))
            pygame.draw.rect(s, (230, 180, 120), (0, 580, ANCHO, 14))
            pygame.draw.rect(s, (150, 100, 60), (0, 594, ANCHO, 5))
        _fondos[tipo] = s
    p.blit(s, (0, 0))
