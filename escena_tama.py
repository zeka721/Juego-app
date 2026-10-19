"""Hub del Tamagotchi de Ninja Mundo: elegir huevo, calentarlo, vivir con la mascota, evolucionar y graduar.

TamagotchiEscena(app, rng=None)

Todo se maneja con el cursor (Boton con permanencia) y clic opcional. La mascota nunca muere.
Modos (self.modo):
    huevos    18 huevos para elegir (los ya abiertos muestran la cascara y la mascota descubierta)
    eclosion  el huevo elegido se calienta frotandolo con el cursor; al abrirse se revela la especie
    hogar     vivir con la mascota: comer, jugar, limpiar, dormir, curar, entrenar (batalla), evolucionar
    cuaderno  coleccion de 18 especies x 4 etapas (escena_tama_libro)
    salon     mascotas graduadas (escena_tama_libro)
La logica vive en tama_datos; el dibujo, en arte_tama (y escena_tama_ui para la interfaz).
"""

import math
import random

import pygame

import arte_tama as AT
import catalogo
import tama_datos as TD
from ajustes import ANCHO, ALTO
from arte_tama_fx import glow, destello_estrella, dibujar_aura_evolucion
from escena import Escena
from escena_tama_ui import (overlay_mascota, escoba, marcas_mascota, dibujar_marca, curita, botiquin, icono_vida, colores_vida, BotonTama, Parts, barra_bonita, clamp, ease_out_back, escribir_parrafo, fuente, flash,
                            lineas_de, mezcla, moneda, pastilla, pelota, silueta_blanca, tarjeta, trofeo, velo, ajustar)
from nucleo import Boton, TextoFlotante, aclarar, corazon, escribir, estrella, oscurecer

V2 = pygame.Vector2

SUELO_Y = 592                       # donde apoya los pies la mascota en el hogar
ESC_HOGAR = (1.5, 1.35, 1.12, 0.98)  # escala por etapa en el hogar (grande pero claramente creciente)
ESC_EVO = 1.35
HUEVO_C = (640, 385)                # centro del huevo grande
VEL_FROTAR = 170.0                  # px/s de cursor dentro del huevo que cuentan como 1 s de calor
NIVEL_BAJO = 35                     # necesidad "baja" (parpadea)
CACAS_POS = [(262, 598), (1010, 600), (400, 612), (905, 612)]
TIEMPO_JUGAR = 20.0
DUR_CACA = 2.0                      # segundos por caca en la limpieza (barrida con escoba)
DUR_BANO = 3.0                      # segundos de ducha
CURA_PRIMERA = 0.5                  # curar: la primera marca aparece a los 0.5 s
CURA_HOVER = 0.5                    # curar: segundos con el cursor encima para poner la curita
CURA_AUTO = 6.0                     # curar: si no la toca, la curita se pone sola a los 6 s
CURA_MIN = 20.0                     # curar: la sesion dura al menos esto (con o sin cursor)
CURA_CIERRE = 1.3                   # curar: celebracion despues de la ultima curita
CURA_RADIO = 46                     # curar: radio (px) de toque de cada marca
LIMPIEZA_OK = 90                    # a partir de aqui, sin cacas, no hace falta limpiar
PANEL_COMER = pygame.Rect(130, 118, 1020, 496)

MENSAJE_TIPO = {
    "agua": "¡Le encanta chapotear y jugar con las olas!",
    "viento": "¡Es ligero como una pluma y vuela con la brisa!",
    "fuego": "¡Tiene un corazón calentito y muy valiente!",
    "hielo": "¡Es fresquito, suave y muy tierno!",
    "tierra": "¡Es fuerte, tranquilo y un gran amigo!",
    "electrico": "¡Está lleno de chispas de energía!",
}
MENSAJE_EVO = ["¡Ahora es más grande y más fuerte!", "¡Qué valiente se ve!", "¡Es increíble, qué poderoso!"]
NOMBRE_CAT = {"fruta": "Le encantan las frutas", "verdura": "Le encantan las verduras", "comida": "Le encantan los platos",
              "granja": "Le encantan los productos de granja", "pesca": "Le encanta el pescado"}

NECESIDADES = (
    ("hambre", "comer", (255, 200, 90), (245, 120, 40), "Hambre"),
    ("felicidad", "jugar", (255, 160, 200), (235, 80, 140), "Alegría"),
    ("energia", "dormir", (150, 215, 255), (70, 140, 245), "Energía"),
    ("limpieza", "limpiar", (130, 240, 230), (50, 185, 205), "Limpieza"),
    ("salud", "curar", (170, 240, 130), (70, 200, 90), "Salud"),
    ("hp", "vida", (160, 238, 125), (70, 200, 90), "Vida"),
)

_CALIENTE = False


def _calentar_arte():
    """Genera los fondos y efectos pesados una sola vez (si el arte lo ofrece)."""
    global _CALIENTE
    if _CALIENTE:
        return
    _CALIENTE = True
    f = getattr(AT, "precalentar", None)
    if f is not None:
        try:
            f()
        except Exception as e:                # el arte nunca debe romper la escena
            print("Tama: no se pudo precalentar el arte:", e)


def _sol(p, cx, cy, tam):
    r = tam * 0.28
    for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(p, (255, 240, 150), (cx + math.cos(a) * r * 1.5, cy + math.sin(a) * r * 1.5),
                         (cx + math.cos(a) * r * 2.2, cy + math.sin(a) * r * 2.2), max(3, int(tam * 0.07)))
    pygame.draw.circle(p, (200, 130, 20), (int(cx), int(cy + 2)), int(r * 1.25))
    pygame.draw.circle(p, (255, 215, 70), (int(cx), int(cy)), int(r * 1.25))
    pygame.draw.circle(p, (255, 245, 170), (int(cx - r * 0.35), int(cy - r * 0.35)), int(r * 0.4))


def _estrella_icono(p, cx, cy, tam):
    estrella(p, int(cx), int(cy), int(tam * 0.5), (255, 245, 150), (170, 110, 20))


class _AppVuelta:
    """Envuelve la app para que la Granja, al salir, vuelva al hogar de mascotas y no al menu."""

    def __init__(self, app, volver):
        self._app = app
        self._volver = volver

    def __getattr__(self, nombre):
        return getattr(self._app, nombre)

    def ir_menu(self):
        self._app.ir(self._volver())


class TamagotchiEscena(Escena):
    def __init__(self, app, rng=None):
        super().__init__(app)
        self.rng = rng or random.Random()
        _calentar_arte()
        self.parts = Parts(self.rng)
        self.flot = []
        self.aviso = ("", 0.0, (255, 255, 255))
        self.sub = None              # None | comer | anim | jugar | evo | graduar
        self.hatch = None
        self.evo = None
        self.anim = None
        self.jg = None
        self.libro = None
        self.ov = (None, 0.0)        # estado visual temporal (nombre, hasta t)
        self._aura_buf = None
        self.hv = [0.0] * TD.NUM_HUEVOS
        self.prev_pos = None
        self.rub = 0.0
        self.t_sin_frotar = 99.0
        self.px, self.ptarget, self.pespera, self.vdir, self.hop = 640.0, 640.0, 1.0, 1, 0.0
        self.caricia = 0.0
        self._t_tick = 0.0
        self._t_guardar = 0.0
        self._grieta_ant = 0
        TD.tick(self.perfil)
        self.st = TD.estado(self.perfil)
        self.m = self.st["activa"]
        self._dormia = bool(self.m and self.m["dormida"])
        self.vis = dict(hp=self.m["hp"] if self.m else 1.0, salud=float(self.m["salud"]) if self.m else 100.0)
        self.pulso_hasta = 0.0       # el boton CURAR pulsa hasta este instante (tras ENTRENAR bloqueado)
        self.modo = self._modo_base()
        self._construir_botones()
        if self.m is not None and TD.aviso_evolucion(self.perfil):
            self.avisar("¡Ya puede evolucionar!" if TD.puede_evolucionar(self.perfil) else "¡Llegó a su forma más poderosa!",
                        3.2, (255, 230, 120))

    # ------------------------------------------------------------ acceso
    @property
    def perfil(self):
        return self.app.ctx.perfil

    @property
    def sonidos(self):
        return self.app.ctx.sonidos

    def _modo_base(self):
        st = TD.estado(self.perfil)
        if st["activa"] is not None:
            return "hogar"
        return "eclosion" if st["huevo"] is not None else "huevos"

    def _guardar(self):
        self._t_guardar = 0.0
        self.perfil.guardar()

    def avisar(self, texto, seg=2.6, color=(255, 255, 255)):
        self.aviso = (texto, seg, color)

    def _sonido(self, nombre):
        self.sonidos.reproducir(nombre)

    # ------------------------------------------------------------ botones
    def _construir_botones(self):
        self.b_cuaderno = BotonTama((912, 10, 112, 88), "Cuaderno", (245, 165, 60), "cuaderno")
        self.b_salon = BotonTama((1032, 10, 112, 88), "Salón", (185, 120, 230), trofeo)
        self.b_volver = BotonTama((1152, 10, 112, 88), "Volver", (140, 150, 190), "volver")
        defs = (("comer", "COMER", (240, 150, 70)), ("jugar", "JUGAR", (235, 105, 160)),
                ("limpiar", "LIMPIAR", (65, 180, 215)), ("dormir", "DORMIR", (110, 110, 215)),
                ("curar", "CURAR", (80, 190, 115)), ("entrenar", "ENTRENAR", (225, 85, 80)))
        w, gap = 190, 14
        x0 = (ANCHO - (len(defs) * w + (len(defs) - 1) * gap)) // 2
        self.acc = {n: BotonTama((x0 + i * (w + gap), 626, w, 88), t, c, n) for i, (n, t, c) in enumerate(defs)}
        self.b_despertar = BotonTama((ANCHO // 2 - 200, 616, 400, 98), "Despertar", (255, 185, 60), _sol, False, 64, False, 42)
        self.b_evo = BotonTama((ANCHO - 340, 250, 310, 96), "¡Evolucionar!", (255, 185, 30), _estrella_icono, False, 56, True, 36)
        self.b_graduar = BotonTama((ANCHO - 340, 250, 310, 96), "Pasar al Salón", (245, 165, 30), trofeo, False, 56, True, 32)
        self.b_hogar = BotonTama((ANCHO // 2 - 220, 606, 440, 90), "¡Vamos al hogar!", (90, 190, 110), None, False, 40, False, 38)
        self.b_evo_ok = BotonTama((ANCHO // 2 - 200, 620, 400, 82), "¡Genial!", (90, 190, 110), None, False, 40, False, 40)
        self.b_c_cerrar = BotonTama((PANEL_COMER.x + 24, 556, 190, 56), "Cerrar", (150, 155, 185), None, False, 40, False, 28)
        self.b_c_granja = BotonTama((PANEL_COMER.right - 24 - 270, 556, 270, 56), "Ir a la granja", (100, 185, 90), None,
                                    False, 40, False, 28)
        self.b_c_prev = BotonTama((PANEL_COMER.centerx - 190, 556, 80, 56), "", (90, 150, 225), lambda p, x, y, t: self._fl(p, x, y, -1),
                                  False, 30)
        self.b_c_next = BotonTama((PANEL_COMER.centerx + 110, 556, 80, 56), "", (90, 150, 225), lambda p, x, y, t: self._fl(p, x, y, 1),
                                  False, 30)
        self.pr_grad = pygame.Rect(ANCHO // 2 - 410, 108, 820, 500)
        self.b_g_si = BotonTama((self.pr_grad.x + 40, self.pr_grad.bottom - 112, 340, 90), "Pasar al Salón", (245, 165, 30), trofeo,
                                False, 54, False, 30)
        self.b_g_no = BotonTama((self.pr_grad.right - 40 - 340, self.pr_grad.bottom - 112, 340, 90), "Seguir juntos", (90, 190, 110),
                                None, False, 40, False, 30)
        # huevos
        self.cards = []
        cw, ch, gx, gy = 176, 164, 14, 8
        x0 = (ANCHO - (6 * cw + 5 * gx)) // 2
        for k in range(TD.NUM_HUEVOS):
            col, fil = k % 6, k // 6
            self.cards.append(Boton((x0 + col * (cw + gx), 100 + fil * (ch + gy), cw, ch), "", (255, 200, 120)))
        self.cartas = []
        self.comer_pag = 0
        self.comer_npag = 1
        self.pr = pygame.Rect(PANEL_COMER)

    @staticmethod
    def _fl(p, x, y, lado):
        from escena_tama_ui import flecha
        flecha(p, x, y, 18, lado)

    def _reset_botones(self):
        """Evita pulsaciones fantasma al cambiar de pantalla: todos esperan un momento."""
        todos = [self.b_cuaderno, self.b_salon, self.b_volver, self.b_despertar, self.b_evo, self.b_graduar, self.b_hogar,
                 self.b_evo_ok, self.b_c_cerrar, self.b_c_granja, self.b_c_prev, self.b_c_next, self.b_g_si, self.b_g_no]
        todos += list(self.acc.values()) + self.cards
        for b in todos:
            b.espera = 0.5
            b.dwell = 0.0

    # ------------------------------------------------------------ ciclo
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        dt = min(dt, 0.1)
        self.parts.actualizar(dt)
        self.flot = [f for f in self.flot if f.actualizar(dt)]
        txt, seg, col = self.aviso
        self.aviso = (txt, max(0.0, seg - dt), col)
        self._refrescar(dt)
        if self.modo == "huevos":
            self._act_huevos(dt, ctrl)
        elif self.modo == "eclosion":
            self._act_eclosion(dt, ctrl)
        elif self.modo == "hogar":
            self._act_hogar(dt, ctrl)
        elif self.libro is not None:
            if self.libro.actualizar(dt, ctrl):
                self._cerrar_libro()

    def _refrescar(self, dt):
        """Paso del tiempo real de la mascota y cuadro actual del estado."""
        self._t_tick += dt
        if self._t_tick >= 0.5:
            self._t_tick = 0.0
            TD.tick(self.perfil)
        self.st = TD.estado(self.perfil)
        self.m = self.st["activa"]
        m = self.m
        if m is not None and self._dormia and not m["dormida"] and self.sub is None:
            self.avisar("¡Buenos días! Ya descansaron las energías", 2.6, (255, 235, 140))
            self._guardar()
        self._dormia = bool(m and m["dormida"])
        if m is not None:                       # las barras de Vida y Salud suben/bajan suave
            for clave, tope in (("hp", 1.0), ("salud", 100.0)):
                v, meta = self.vis[clave], float(m[clave])
                self.vis[clave] = meta if abs(meta - v) < tope * 0.002 else v + (meta - v) * min(1.0, dt * 4.0)
            self.acc["curar"].pulso = bool(not m["dormida"] and (m["hp"] < TD.HP_URGENTE or self.t < self.pulso_hasta))
        self._t_guardar += dt
        if self._t_guardar > 20:
            self._guardar()
        if self.modo == "hogar" and m is None:
            self.modo = self._modo_base()
            self.sub = None
        elif self.modo == "eclosion" and self.hatch is None and self.st["huevo"] is None:
            self.modo = self._modo_base()

    def tecla_esc(self):
        if self.libro is not None:
            self._cerrar_libro()
        elif self.hatch is not None or self.evo is not None or self.jg is not None:
            return
        elif self.sub == "anim" and self.anim is not None and self.anim["tipo"] == "curar":
            self._terminar_curar(False)
        elif self.sub in ("comer", "graduar"):
            self.sub = None
            self._reset_botones()
        elif self.sub is None:
            self._salir()

    def _salir(self):
        self._guardar()
        self._sonido("click")
        if getattr(self.app, "solo_tama", False):      # version del telefono: salir = cerrar la app
            self.app.salir = True
            return
        from aventura import Libre
        self.app.ir(Libre(self.app))

    def _abrir_libro(self, cual):
        from escena_tama_libro import LibroCuaderno, LibroSalon
        self._sonido("click")
        self.libro = (LibroCuaderno if cual == "cuaderno" else LibroSalon)(self)
        self.modo = cual
        self._reset_botones()

    def _cerrar_libro(self):
        self.libro = None
        self.modo = self._modo_base()
        self._reset_botones()

    def _act_top(self, dt, ctrl, activo=True):
        """Botones de arriba a la derecha. Devuelve True si cambio de pantalla."""
        for b in (self.b_cuaderno, self.b_salon, self.b_volver):
            b.activo = activo
        if self.b_cuaderno.actualizar(dt, ctrl):
            self._abrir_libro("cuaderno")
            return True
        if self.b_salon.actualizar(dt, ctrl):
            self._abrir_libro("salon")
            return True
        if self.b_volver.actualizar(dt, ctrl):
            self._salir()
            return True
        return False

    # ============================================================ HUEVOS
    def _act_huevos(self, dt, ctrl):
        if self._act_top(dt, ctrl):
            return
        ecl = set(self.st["eclosionados"])
        for k, b in enumerate(self.cards):
            b.activo = k not in ecl
            objetivo = 1.0 if (b.activo and b.rect.collidepoint(ctrl.pos.x, ctrl.pos.y)) else 0.0
            self.hv[k] += (objetivo - self.hv[k]) * min(1.0, dt * 8)
            if b.actualizar(dt, ctrl):
                if TD.elegir_huevo(self.perfil, k):
                    self._sonido("ok")
                    self._guardar()
                    self.modo = "eclosion"
                    self.hatch = None
                    self.rub = 0.0
                    self.prev_pos = None
                    self.t_sin_frotar = 99.0
                    self._grieta_ant = 0
                    self._reset_botones()
                return

    def _dibujar_huevos(self, p):
        AT.dibujar_fondo_hogar_velado(p, self.t, False, 125, (255, 245, 225))
        escribir(p, self.f.grande, "Elige un huevo", ANCHO / 2 - 150, 40, (255, 250, 235), contorno=(120, 70, 40), grosor=3)
        escribir(p, fuente(22), "¿Qué mascota habrá dentro? ¡Es un secreto!", ANCHO / 2 - 150, 80, (255, 240, 210),
                 contorno=(120, 70, 40))
        ecl = set(self.st["eclosionados"])
        desc = self.st["descubiertas"]
        for k, b in enumerate(self.cards):
            r = pygame.Rect(b.rect)
            hv = self.hv[k]
            r.y -= int(6 * hv)
            abierto = k in ecl
            borde = (255, 200, 70) if hv > 0.3 else (190, 140, 100)
            tarjeta(p, r, (255, 250, 240) if not abierto else (255, 244, 214), 240, 24, borde, 5 if hv > 0.3 else 3)
            cx = r.centerx
            if hv > 0.05:
                glow(p, cx, r.y + 78, 90 + 20 * hv, (255, 225, 140), int(110 * hv))
            if abierto:
                esp = self.st["huevos"][k]
                et = desc.get(esp, 0)
                h_ = AT.ALTO_ETAPA[et]
                AT.dibujar_mascota(p, esp, et, cx, r.y + 64, 72.0 / h_, self.t + k, "feliz", 1)
                self._cascara_abierta(p, k, cx, r.y + 90)
                nombre = TD.ESPECIES[esp]["formas"][et]
                escribir(p, ajustar(21, nombre, r.w - 30, 14), nombre, cx, r.bottom - 15, (90, 60, 40), contorno=None)
                AT.dibujar_icono_tipo(p, TD.ESPECIES[esp]["tipo"], r.x + 22, r.y + 22, 13)
            else:
                self._nido(p, cx, r.y + 128)
                AT.dibujar_huevo(p, k, cx, r.y + 74, 0.88, self.t + k * 0.7, 0, hv * 0.85, hv * 0.25)
            if b.dwell > 0:
                from ajustes import DWELL_SEG
                barra_bonita(p, (r.x + 22, r.bottom - 22, r.w - 44, 12), b.dwell / DWELL_SEG, (255, 215, 90), (255, 150, 40))
        self._dibujar_botones_top(p)

    @staticmethod
    def _nido(p, cx, cy):
        for i, (dx, dy, w, h, c) in enumerate(((0, 6, 138, 30, (150, 105, 60)), (0, 0, 126, 26, (190, 140, 80)),
                                               (0, -4, 108, 20, (225, 180, 105)))):
            pygame.draw.ellipse(p, c, (cx - w / 2 + dx, cy - h / 2 + dy, w, h))
            pygame.draw.ellipse(p, oscurecer(c, 0.4), (cx - w / 2 + dx, cy - h / 2 + dy, w, h), 2)

    @staticmethod
    def _cascara_abierta(p, k, cx, cy):
        """Cascara rota en el suelo: la base y las dos tapas recostadas."""
        try:
            from arte_tama_huevos import _pieza, CW, CH
            b = pygame.transform.smoothscale(_pieza(k, "base"), (int(CW * 0.64), int(CH * 0.64)))
            p.blit(b, b.get_rect(center=(cx, cy)))
        except Exception:
            pygame.draw.ellipse(p, (240, 230, 210), (cx - 30, cy - 10, 60, 30))

    # ============================================================ ECLOSION
    @staticmethod
    def _en_huevo(pos):
        dx = (pos[0] - HUEVO_C[0]) / 112.0
        dy = (pos[1] - HUEVO_C[1]) / 150.0
        return dx * dx + dy * dy <= 1.0

    def _act_eclosion(self, dt, ctrl):
        if self.hatch is not None:
            self._act_hatch(dt, ctrl)
            return
        if self._act_top(dt, ctrl):
            return
        pos = V2(ctrl.pos)
        d = 0.0
        if self.prev_pos is not None and self._en_huevo(pos) and self._en_huevo(self.prev_pos):
            d = pos.distance_to(self.prev_pos)
        self.prev_pos = pos
        efectivo = min(dt, d / VEL_FROTAR)
        self.rub += (min(1.0, d / max(dt, 1e-6) / VEL_FROTAR) - self.rub) * min(1.0, dt * 6)
        if efectivo > 0:
            self.t_sin_frotar = 0.0
            TD.calentar(self.perfil, efectivo * TD.CALOR_POR_SEGUNDO)
            if self.rng.random() < dt * 40 * self.rub:
                self.parts.calor(pos.x, pos.y)
        else:
            self.t_sin_frotar += dt
        calor = self.st["calor"]
        grieta = min(4, int(calor / 0.2))
        if grieta > self._grieta_ant:
            self._grieta_ant = grieta
            self._sonido("pop")
            for _ in range(8):
                self.parts.chispa(HUEVO_C[0], HUEVO_C[1] - 20, (255, 230, 140), 11, 160)
            self._guardar()
        if TD.calor_listo(self.perfil):
            self._empezar_hatch()

    def _empezar_hatch(self):
        k = self.st["huevo"]
        esp = TD.eclosionar(self.perfil)
        if esp is None:
            return
        self.hatch = dict(t=0.0, k=k, esp=esp)
        self.px, self.ptarget, self.pdir = 640.0, 640.0, 1
        self._sonido("premio")
        self._guardar()
        self.st = TD.estado(self.perfil)
        self.m = self.st["activa"]
        self._reset_botones()

    def _act_hatch(self, dt, ctrl):
        h = self.hatch
        h["t"] += dt
        t = h["t"]
        if 0.1 < t < 1.6 and self.rng.random() < dt * 50:
            self.parts.confeti(HUEVO_C[0], HUEVO_C[1] - 40)
        if 0.45 < t < 0.5:
            self._sonido("ok")
        if t > 2.3:
            self.b_hogar.activo = True
            if self.b_hogar.actualizar(dt, ctrl):
                self._sonido("ok")
                self.hatch = None
                self.modo = "hogar"
                self.sub = None
                self.px = 640.0
                self._reset_botones()
                self.avisar("¡Cuídalo mucho!", 2.6, (255, 235, 140))

    def _dibujar_eclosion(self, p):
        AT.dibujar_fondo_hogar_velado(p, self.t, False, 60, (90, 50, 20))
        if self.hatch is not None:
            self._dibujar_hatch(p)
            return
        k = self.st["huevo"]
        calor = self.st["calor"]
        cx, cy = HUEVO_C
        act = clamp(self.rub * 1.2)
        glow(p, cx, cy, 250 + 80 * calor, (255, 190, 90), int(35 + 150 * calor * (0.5 + 0.5 * act)))
        escribir(p, self.f.grande, "Calienta el huevo", ANCHO / 2 - 150, 40, (255, 250, 235), contorno=(120, 70, 40), grosor=3)
        self._nido(p, cx, cy + 150)
        grieta = min(4, int(calor / 0.2))
        mecer = clamp(act * 0.9 + calor * 0.25)
        AT.dibujar_huevo(p, k, cx, cy, 1.85, self.t, grieta, mecer, clamp(calor * 0.9 + act * 0.2))
        self.parts.dibujar(p)
        # indicacion de frotar: flechas circulares que giran cuando aun no se frota
        if self.t_sin_frotar > 1.2 and calor < 1:
            a = self.t * 2.4
            for i in range(2):
                a0 = a + i * math.pi
                rect = pygame.Rect(0, 0, 250, 160)
                rect.center = (cx, cy + 20)
                pygame.draw.arc(p, (255, 245, 200), rect, a0, a0 + 1.7, 7)
                ex, ey = cx + math.cos(a0 + 1.7) * 125, cy + 20 - math.sin(a0 + 1.7) * 80
                glow(p, ex, ey, 22, (255, 240, 170), 230)
            escribir(p, fuente(26), "¡Frótalo con el cursor para calentarlo!", ANCHO / 2 - 150, 84, (255, 240, 200),
                     contorno=(120, 70, 40))
        elif calor >= 0.8:
            escribir(p, fuente(28), "¡Ya casi sale!", ANCHO / 2 - 150, 84, (255, 240, 130), contorno=(140, 70, 20))
        else:
            escribir(p, fuente(26), "¡Sigue frotando, se está calentando!", ANCHO / 2 - 150, 84, (255, 240, 200),
                     contorno=(120, 70, 40))
        # barra de calor
        r = pygame.Rect(0, 0, 520, 40)
        r.center = (ANCHO // 2, 628)
        tarjeta(p, r.inflate(120, 24), (255, 245, 225), 190, 26, (190, 120, 70), 3)
        barra_bonita(p, r, calor, (255, 215, 80), (240, 70, 40), (95, 55, 45), (255, 245, 220),
                     titilar=0.5 + 0.5 * math.sin(self.t * 8) if act > 0.2 else 0.0)
        fx = r.x + 6 + (r.w - 12) * calor
        glow(p, fx, r.centery, 30, (255, 190, 90), int(120 + 90 * act))
        self._llama(p, r.x - 48, r.centery + 2, 46 + 4 * math.sin(self.t * 9))
        escribir(p, fuente(22), f"{int(calor * 100)}%", r.right + 54, r.centery, (255, 240, 200), contorno=(100, 50, 30))
        self._dibujar_botones_top(p)

    @staticmethod
    def _llama(p, cx, cy, tam):
        s = tam / 46.0
        pts = [(cx, cy - 22 * s), (cx + 13 * s, cy - 2 * s), (cx + 14 * s, cy + 10 * s), (cx, cy + 20 * s),
               (cx - 14 * s, cy + 10 * s), (cx - 12 * s, cy - 4 * s)]
        pygame.draw.polygon(p, (230, 70, 30), pts)
        pygame.draw.polygon(p, (150, 40, 20), pts, 3)
        pts2 = [(cx, cy - 6 * s), (cx + 7 * s, cy + 6 * s), (cx, cy + 15 * s), (cx - 7 * s, cy + 6 * s)]
        pygame.draw.polygon(p, (255, 215, 70), pts2)

    def _dibujar_hatch(self, p):
        h = self.hatch
        t = h["t"]
        esp = h["esp"]
        cx, cy = HUEVO_C
        m = self.m
        glow(p, cx, cy, 300, (255, 220, 140), int(120 * clamp(1.2 - t * 0.5)))
        self._nido(p, cx, cy + 150)
        if t < 1.8:
            AT.dibujar_cascaras(p, h["k"], cx, cy, clamp(t / 1.7), self.t)
        if t > 0.45:
            s = ease_out_back((t - 0.45) / 0.8)
            AT.dibujar_mascota(p, esp, 0, cx, cy + 15 - (1 - clamp((t - 0.45) / 0.8)) * 20, 1.9 * max(0.05, s),
                               self.t, "feliz", 1)
        self.parts.dibujar(p)
        info = TD.ESPECIES[esp]
        tipo = info["tipo"]
        col = AT.COLOR_TIPO[tipo]
        if t > 1.2:
            k = ease_out_back((t - 1.2) / 0.6)
            nombre = (m["nombre"] if m else info["formas"][0])
            escribir(p, fuente(int(60 * clamp(k, 0.3, 1.1))), f"¡Es {nombre}!", ANCHO / 2, 84 - (1 - clamp(k)) * 30,
                     (255, 250, 235), contorno=oscurecer(col, 0.6), grosor=4)
        if t > 1.7:
            txt = "Tipo " + AT.NOMBRE_TIPO[tipo]
            fn = fuente(30)
            r = pygame.Rect(0, 0, fn.size(txt)[0] + 104, 54)
            r.center = (ANCHO // 2, 158)
            tarjeta(p, r, aclarar(col, 0.55), 255, 27, oscurecer(col, 0.35), 3, False)
            AT.dibujar_icono_tipo(p, tipo, r.x + 36, r.centery, 24)
            escribir(p, fn, txt, r.x + 68, r.centery, (50, 40, 80), "izq", contorno=None)
        if t > 2.0:
            escribir_parrafo(p, fuente(30), MENSAJE_TIPO[tipo], ANCHO / 2, 548, 1000, (255, 250, 235), (100, 60, 30))
        if t > 2.3:
            self.b_hogar.dibujar(p, None, self.t)
        flash(p, (1 - t / 0.7) ** 2 if t < 0.7 else 0.0)

    # ============================================================ HOGAR
    def _estado_visual(self):
        m = self.m
        if self.ov[0] is not None and self.t < self.ov[1]:
            return self.ov[0]
        if m["dormida"]:
            return "duerme"
        if m["salud"] < 40:
            return "enfermo"
        if m["hambre"] < NIVEL_BAJO:
            return "hambre"
        if m["felicidad"] < NIVEL_BAJO or m["limpieza"] < 25 or m["cacas"] >= 2:
            return "triste"
        if m["felicidad"] >= 65:
            return "feliz"
        return "normal"

    def _alto_pet(self):
        e = self.m["etapa"]
        return AT.ALTO_ETAPA[e] * ESC_HOGAR[e]

    def _centro_pet(self):
        return self.px, SUELO_Y - self._alto_pet() / 2 - self.hop

    def _mover_mascota(self, dt, quieta, centro):
        m = self.m
        moviendo = False
        if quieta or centro:
            if centro and not quieta and abs(self.px - 640) > 2:
                paso = clamp(640 - self.px, -230 * dt, 230 * dt)
                self.px += paso
                if abs(paso) > 0.1:
                    self.vdir = 1 if paso > 0 else -1
                moviendo = True
        else:
            if self.pespera > 0:
                self.pespera -= dt
                if self.pespera <= 0:
                    self.ptarget = self.rng.uniform(500, 790)
            else:
                vel = 45.0 if m["salud"] >= 40 and m["hambre"] >= NIVEL_BAJO else 26.0
                paso = clamp(self.ptarget - self.px, -vel * dt, vel * dt)
                self.px += paso
                if abs(paso) > 0.01:
                    self.vdir = 1 if paso > 0 else -1
                    moviendo = True
                if abs(self.ptarget - self.px) < 1.0:
                    self.pespera = self.rng.uniform(1.5, 4.0)
        self.hop = abs(math.sin(self.t * 7)) * 5 if moviendo else self.hop * max(0.0, 1 - dt * 12)

    def _act_hogar(self, dt, ctrl):
        m = self.m
        libre = self.sub is None
        quieta = bool(m["dormida"])
        self._mover_mascota(dt, quieta, centro=self.sub in ("anim", "comer", "graduar"))
        if self.sub == "jugar":
            self._act_jugar(dt, ctrl)
            return
        if self.sub == "evo":
            self._act_evo(dt, ctrl)
            return
        if self.sub == "anim":
            self._act_anim(dt, ctrl)
            if self.anim is not None and self.anim["tipo"] == "curar":
                return                                  # la sesion de curar maneja sus propios botones
            self._act_top(dt, ctrl, False)
            return
        if self.sub == "comer":
            self._act_top(dt, ctrl, False)
            self._act_comer(dt, ctrl)
            return
        if self.sub == "graduar":
            self._act_top(dt, ctrl, False)
            self._act_graduar(dt, ctrl)
            return
        # ---- hogar libre
        if self._act_top(dt, ctrl, libre):
            return
        # caricias con el cursor (solo corazones, no cambian datos)
        cx, cy = self._centro_pet()
        h = self._alto_pet()
        if not m["dormida"] and abs(ctrl.pos.x - cx) < h * 0.45 and abs(ctrl.pos.y - cy) < h * 0.5:
            self.caricia += dt
            if self.caricia > 0.6:
                self.caricia = 0.0
                self.parts.corazon(cx, cy - h * 0.4)
                self._sonido("pop")
                self.ov = ("feliz", self.t + 1.4)
        else:
            self.caricia = max(0.0, self.caricia - dt)
        if self._nivel_polvo() > 0 and self.hop > 1.0 and self.rng.random() < dt * 5:
            self.parts.polvo(cx + self.rng.uniform(-30, 30), SUELO_Y - 6)
        if m["dormida"]:
            if self.rng.random() < dt * 0.7:
                self.parts.zzz(cx + h * 0.25, cy - h * 0.35)
            if self.b_despertar.actualizar(dt, ctrl):
                self._despertar()
            return
        for nombre, b in self.acc.items():
            b.activo = True
            if nombre == "entrenar":
                b.activo = True
            if b.actualizar(dt, ctrl):
                getattr(self, "_accion_" + nombre)()
                return
        if TD.puede_evolucionar(self.perfil):
            if self.b_evo.actualizar(dt, ctrl):
                self._iniciar_evo()
                return
        elif TD.puede_graduar(self.perfil):
            if self.b_graduar.actualizar(dt, ctrl):
                self.sub = "graduar"
                self._sonido("click")
                self._reset_botones()

    # ------------------------------------------------------------ acciones
    def _accion_comer(self):
        m = self.m
        if m["hambre"] >= 95:
            self.avisar("¡Tiene la pancita llena! No quiere más ahora", 2.8, (255, 235, 150))
            self.ov = ("feliz", self.t + 1.5)
            return
        self._sonido("click")
        self.sub = "comer"
        self.comer_pag = 0
        self._cartas_comida()
        self._reset_botones()

    def _cartas_comida(self):
        comidas = TD.comidas(self.perfil)
        self.comer_npag = max(1, (len(comidas) + 9) // 10)
        self.comer_pag = max(0, min(self.comer_pag, self.comer_npag - 1))
        lista = comidas[self.comer_pag * 10:(self.comer_pag + 1) * 10]
        self.cartas = []
        una_fila = 0 < len(lista) <= 5
        self.pr = pygame.Rect(130, 150, 1020, 420) if una_fila else pygame.Rect(PANEL_COMER)
        R = self.pr
        x0, y0 = R.x + 55, R.y + 114
        for i, (item, n) in enumerate(lista):
            col, fil = i % 5, i // 5
            self.cartas.append((item, n, Boton((x0 + col * 184, y0 + fil * 160, 170, 148), "", (255, 200, 120))))
        self.hay_comida = bool(comidas)
        yb = R.bottom - 58
        self.b_c_cerrar.rect.topleft = (R.x + 24, yb)
        self.b_c_granja.rect.topleft = (R.right - 24 - 270, yb)
        self.b_c_prev.rect.topleft = (R.centerx - 190, yb)
        self.b_c_next.rect.topleft = (R.centerx + 110, yb)

    def _act_comer(self, dt, ctrl):
        self.b_c_cerrar.activo = True
        if self.b_c_cerrar.actualizar(dt, ctrl):
            self.sub = None
            self._reset_botones()
            return
        self.b_c_granja.activo = True
        if self.b_c_granja.actualizar(dt, ctrl):
            self._ir_granja()
            return
        if self.comer_npag > 1:
            if self.b_c_prev.actualizar(dt, ctrl):
                self.comer_pag = (self.comer_pag - 1) % self.comer_npag
                self._cartas_comida()
                return
            if self.b_c_next.actualizar(dt, ctrl):
                self.comer_pag = (self.comer_pag + 1) % self.comer_npag
                self._cartas_comida()
                return
        for item, n, b in self.cartas:
            if b.actualizar(dt, ctrl):
                self._dar_comida(item)
                return

    def _dar_comida(self, item):
        res = TD.comer(self.perfil, item)
        if res is None:
            self.avisar("No pudo comer eso ahora", 2.4)
            self.sub = None
            return
        self._guardar()
        self.anim = dict(tipo="comer", item=item, res=res, t=0.0, dur=2.9, n_crumbs=0)
        self.sub = "anim"
        self._sonido("ok")
        self._reset_botones()

    def _ir_granja(self):
        if getattr(self.app, "solo_tama", False):
            self.avisar("La granja llega muy pronto.", 2.5, (255, 240, 180))
            return
        from escena_granja import GranjaEscena
        self._guardar()
        self._sonido("click")
        app = self.app
        self.app.ir(GranjaEscena(_AppVuelta(app, lambda: TamagotchiEscena(app))))

    def _accion_limpiar(self):
        m = self.m
        n = min(int(m["cacas"]), len(CACAS_POS))
        if m["cacas"] == 0 and m["limpieza"] >= LIMPIEZA_OK:
            self.avisar("¡Ya está limpiecito!", 2.6, (200, 245, 255))
            for _ in range(8):
                x, y = self._centro_pet()
                self.parts.chispa(x + self.rng.uniform(-60, 60), y + self.rng.uniform(-60, 60), (255, 255, 255), 12, 40)
            return
        # servicio completo: escoba para cada caca y despues ducha (los datos se aplican al terminar)
        self.anim = dict(tipo="limpiar", t=0.0, n=n, t_bano=n * DUR_CACA, dur=n * DUR_CACA + DUR_BANO,
                         nivel=self._nivel_polvo(), visitas=[], quitadas=[])
        self.sub = "anim"
        self._sonido("click")
        self._reset_botones()

    def _nivel_polvo(self):
        """0 = limpia; 1..4 = cada vez mas manchas de polvo segun baja la limpieza (visible bajo 65)."""
        l = self.m["limpieza"] if self.m is not None else 100
        return 0 if l >= 65 else 4 if l < 20 else 3 if l < 35 else 2 if l < 50 else 1

    def _accion_curar(self):
        ctx = TD.curar_inicio(self.perfil)
        if ctx is None:
            self.avisar("¡Estoy sanita!", 2.6, (200, 255, 210))
            self.ov = ("feliz", self.t + 1.5)
            x, y = self._centro_pet()
            for _ in range(5):
                self.parts.corazon(x + self.rng.uniform(-50, 50), y - self._alto_pet() * 0.4)
            return
        # sesion: aparece el botiquin y, una a una, las marcas que hay que curar con una curita
        self.anim = dict(tipo="curar", t=0.0, dur=9999.0, ctx=ctx, n=int(ctx["n"]), k=0, marcas=[], completo=False,
                         fin_t=0.0, t_real=0.0)
        self.sub = "anim"
        self._sonido("click")
        self._reset_botones()

    def _act_curar(self, a, dt, ctrl):
        """Sesion de curar (~22 s): las marcas aparecen una a una; tocarlas con el cursor 0.5 s pone la curita."""
        cx, cy = self._centro_pet()
        h = self._alto_pet()
        self.b_cuaderno.activo = self.b_salon.activo = False
        self.b_volver.activo = True
        a["t_real"] += dt
        if self.b_volver.actualizar(dt, ctrl):
            self._terminar_curar(False)
            return
        if not a["marcas"]:
            if abs(self.px - 640) > 2:                 # espera a que la mascota llegue al centro
                return
            e = self.m["etapa"]
            pts = marcas_mascota(self.m["especie"], e, ESC_HOGAR[e], self.vdir, a["n"])
            sep = (TD.CURAR_SEGUNDOS - CURA_AUTO + 1.0 - CURA_PRIMERA) / max(1, a["n"] - 1)
            a["marcas"] = [dict(dx=dx, dy=dy, tipo="moreton" if i % 2 == 0 else "raspon", est=0, hover=0.0, tc=0.0,
                                ap=CURA_PRIMERA + i * sep) for i, (dx, dy) in enumerate(pts)]
            self.avisar("¡Toca las marcas para ponerles una curita!", 3.6, (255, 235, 170))
        a["t"] += dt
        t, n = a["t"], a["n"]
        for mk in a["marcas"]:
            ap = mk["ap"]
            if mk["est"] == 0 and t >= ap:
                mk["est"] = 1
                self._sonido("pop")
                for _ in range(4):
                    self.parts.chispa(cx + mk["dx"], cy + mk["dy"], (255, 255, 255), 10, 50, 0.6)
            if mk["est"] == 1:
                edad = t - ap
                d = math.hypot(ctrl.pos.x - (cx + mk["dx"]), ctrl.pos.y - (cy + mk["dy"]))
                if edad >= 0.35 and d <= CURA_RADIO:
                    mk["hover"] = min(CURA_HOVER, mk["hover"] + dt)
                else:
                    mk["hover"] = max(0.0, mk["hover"] - dt * 2)
                if mk["hover"] >= CURA_HOVER or edad >= CURA_AUTO:
                    self._aplicar_curita(a, mk, cx + mk["dx"], cy + mk["dy"], h)
            elif mk["est"] == 2:
                mk["tc"] += dt
        if a["completo"] and t >= max(a["fin_t"] + CURA_CIERRE, CURA_MIN):
            self._terminar_curar(True)
            return
        pend = a["n"] - a["k"]
        if self.t >= self.ov[1] - 0.05:
            self.ov = ("enfermo" if pend >= a["n"] - 1 and a["ctx"]["hp0"] < 0.35 else "normal", self.t + 0.2)

    def _aplicar_curita(self, a, mk, x, y, h):
        mk["est"] = 2
        mk["tc"] = 0.0
        a["k"] += 1
        res = TD.curar_paso(self.perfil, a["ctx"], a["k"])
        self._sonido("pop")
        self.parts.corazon(x, y - 10)
        self.parts.corazon(x + 24, y - 30)
        for _ in range(4):
            self.parts.estrella(x, y, (255, 235, 170), 11)
        self.flot.append(TextoFlotante("Vida %d%%" % round(res["hp"] * 100), x, y - 46, (170, 255, 190), 1.1, 50))
        self.ov = ("feliz", self.t + 1.0)
        if a["k"] >= a["n"]:
            a["completo"] = True
            a["fin_t"] = a["t"]
            TD.curar_fin(self.perfil, a["ctx"])
            self._sonido("premio")
            cxp, cyp = self._centro_pet()
            self.parts.confeti(cxp, cyp - h * 0.3)
            for _ in range(6):
                self.parts.corazon(cxp + self.rng.uniform(-70, 70), cyp - h * 0.2)

    def _terminar_curar(self, completo):
        a = self.anim
        if a is None:
            return
        TD.curar_fin(self.perfil, a["ctx"])             # no hace nada si ya se cerro; da la recompensa si hubo curitas
        k = a["k"]
        self.anim = None
        self.sub = None
        self.ov = ("feliz", self.t + 1.8)
        self._reset_botones()
        if completo:
            self.avisar("¡Vida recuperada!", 3.0, (170, 255, 190))
        elif k > 0:
            self.avisar("¡Ya está mejor! Seguimos luego", 3.0, (200, 255, 210))
        else:
            self.avisar("Seguimos luego", 2.4, (255, 235, 170))
        self._guardar()

    def _accion_dormir(self):
        m = self.m
        if m["energia"] >= 95:
            self.avisar("Todavía no tiene sueño", 2.6, (255, 235, 150))
            return
        TD.dormir(self.perfil, True)
        self._guardar()
        self._sonido("click")
        self.avisar("¡Buenas noches! Duerme hasta recuperar su energía", 3.0, (200, 215, 255))
        self._reset_botones()

    def _despertar(self):
        TD.dormir(self.perfil, False)
        self._guardar()
        self._sonido("ok")
        self.avisar("¡Buenos días!", 2.4, (255, 235, 140))
        self.ov = ("feliz", self.t + 1.6)
        self._reset_botones()

    def _accion_entrenar(self):
        m = self.m
        if not TD.puede_entrenar(self.perfil):
            self.avisar("Estoy muy cansadita, ¡cúrame primero!", 3.4, (255, 220, 160))
            self.pulso_hasta = self.t + 4.0
            self.ov = ("enfermo", self.t + 1.6)
            return
        if m["energia"] < 15:
            self.avisar("Tiene mucho sueño para pelear. ¡Que descanse!", 3.0, (255, 220, 160))
            return
        if m["hambre"] < 15:
            self.avisar("Tiene mucha hambre. ¡Dale de comer primero!", 3.0, (255, 220, 160))
            return
        if getattr(self.app, "solo_tama", False):
            self.avisar("Las peleas llegan muy pronto.", 2.5, (255, 240, 180))
            return
        self._guardar()
        self._sonido("click")
        from aventura import Partida
        self.app.ir(Partida(self.app, "horda", 1))   # la pelea es Horda Elemental

    # ------------------------------------------------------------ animaciones de cuidado
    def _act_anim(self, dt, ctrl):
        a = self.anim
        if a["tipo"] == "curar":
            self._act_curar(a, dt, ctrl)
            return
        a["t"] += dt
        t = a["t"]
        cx, cy = self._centro_pet()
        h = self._alto_pet()
        tipo = a["tipo"]
        if tipo == "comer":
            if t >= 0.9 and a["n_crumbs"] < 14 and t < 2.0 and self.rng.random() < dt * 22:
                a["n_crumbs"] += 1
                self.parts.migaja(cx + self.vdir * 20, cy - h * 0.05)
            if t >= 0.9 and not a.get("mordio"):
                a["mordio"] = True
                self._sonido("pop")
                res = a["res"]
                self.flot.append(TextoFlotante("¡Ñam ñam!", cx, cy - h * 0.62, (255, 240, 150), 0.8, 50))
            if t >= 1.7 and not a.get("premio"):
                a["premio"] = True
                res = a["res"]
                self._sonido("moneda")
                for _ in range(5):
                    self.parts.corazon(cx, cy - h * 0.35)
                self.flot.append(TextoFlotante(f"Hambre +{res['hambre']}", cx - 190, cy - h * 0.2, (255, 200, 110), 1.6, 70))
                self.flot.append(TextoFlotante(f"Alegría +{res['felicidad']}", cx + 190, cy - h * 0.2, (255, 160, 205), 1.6, 70))
                if res["xp"]:
                    self.flot.append(TextoFlotante(f"XP +{res['xp']}", cx, cy - h * 0.72, (255, 240, 110), 1.6, 60))
                if res["favorita"]:
                    self.flot.append(TextoFlotante("¡Es su favorita!", cx, cy - h * 0.95, (255, 110, 150), 1.8, 50))
                    for _ in range(6):
                        self.parts.estrella(cx, cy - h * 0.3)
            if 0.9 <= t < 2.0:
                self.ov = ("come", self.t + 0.2)
            elif t >= 2.0:
                self.ov = ("feliz", self.t + 0.2)
        elif tipo == "limpiar":
            if t < a["t_bano"]:                      # 1) la escoba visita cada caca, en orden
                i = min(int(t // DUR_CACA), a["n"] - 1)
                ti = t - i * DUR_CACA
                x, y = CACAS_POS[i % len(CACAS_POS)]
                if i not in a["visitas"]:
                    a["visitas"].append(i)
                    self._sonido("lanzar")
                if 0.5 <= ti < 1.4 and self.rng.random() < dt * 34:
                    self.parts.polvo(x + self.rng.uniform(-30, 30), y + 6)
                if ti >= 1.0 and i not in a["quitadas"]:
                    a["quitadas"].append(i)
                    self._sonido("pop")
                    for _ in range(7):
                        self.parts.estrella(x, y - 12, (255, 235, 150), 11)
                self.ov = ("normal", self.t + 0.2)
            else:                                    # 2) ducha y espuma sobre la mascota
                tb = t - a["t_bano"]
                if not a.get("splash"):
                    a["splash"] = True
                    self._sonido("splash")
                if tb < 2.2 and self.rng.random() < dt * 24:
                    self.parts.burbuja(cx + self.rng.uniform(-h * 0.5, h * 0.5), cy + self.rng.uniform(-h * 0.2, h * 0.5))
                if tb >= 2.4 and not a.get("brillo"):
                    a["brillo"] = True
                    self._sonido("premio")
                    for _ in range(12):
                        self.parts.chispa(cx + self.rng.uniform(-h * 0.5, h * 0.5), cy + self.rng.uniform(-h * 0.5, h * 0.5),
                                          (255, 255, 255), 14, 70, 1.0)
                    for _ in range(5):
                        self.parts.estrella(cx + self.rng.uniform(-h * 0.4, h * 0.4), cy - h * 0.2, (255, 240, 170), 11)
                    self.flot.append(TextoFlotante("¡Limpio!", cx, cy - h * 0.7, (200, 245, 255), 1.6, 60))
                self.ov = ("feliz" if tb >= 2.4 else "normal", self.t + 0.2)
        if t >= a["dur"]:
            self.anim = None
            self.sub = None
            self.ov = ("feliz", self.t + 1.6)
            self._reset_botones()
            if TD.puede_evolucionar(self.perfil) and tipo == "comer":
                self.avisar("¡Ya puede evolucionar!", 3.0, (255, 230, 120))
            if tipo == "limpiar":
                TD.limpiar(self.perfil)               # una sola vez, al final del servicio
                self.avisar("¡Todo limpio y brillante!", 2.8, (200, 245, 255))
            self._guardar()

    # ------------------------------------------------------------ jugar
    def _accion_jugar(self):
        m = self.m
        if m["energia"] < 10:
            self.avisar("Tiene mucho sueño para jugar. ¡Que duerma un poco!", 3.0, (255, 220, 160))
            return
        self._sonido("click")
        self.jg = dict(t=TIEMPO_JUGAR, pts=0, bx=640.0, by=260.0, bvx=170.0, bvy=-60.0, ang=0.0, cd=0.0, cat=0.0,
                       px=self.px, fin=None, gan=0.0, hits=0, catches=0, pdir=self.vdir, salto=0.0)
        self.sub = "jugar"
        self._reset_botones()

    def _act_jugar(self, dt, ctrl):
        jg = self.jg
        self._act_top(dt, ctrl, False)
        h = self._alto_pet()
        if jg["fin"] is not None:
            jg["fin"] -= dt
            self.px = jg["px"]
            if jg["fin"] <= 0:
                self.jg = None
                self.sub = None
                self.ov = ("feliz", self.t + 1.4)
                self._reset_botones()
            return
        R = 34
        floor_y = SUELO_Y - R - 6
        jg["t"] -= dt
        jg["cd"] = max(0.0, jg["cd"] - dt)
        jg["cat"] = max(0.0, jg["cat"] - dt)
        jg["salto"] = max(0.0, jg["salto"] - dt)
        # fisica suave de la pelota
        jg["bvy"] += 430 * dt
        jg["bx"] += jg["bvx"] * dt
        jg["by"] += jg["bvy"] * dt
        jg["ang"] += jg["bvx"] * dt * 0.02
        if jg["bx"] < R + 20:
            jg["bx"], jg["bvx"] = R + 20, abs(jg["bvx"]) * 0.9
        elif jg["bx"] > ANCHO - R - 20:
            jg["bx"], jg["bvx"] = ANCHO - R - 20, -abs(jg["bvx"]) * 0.9
        if jg["by"] < 190:
            jg["by"], jg["bvy"] = 190, abs(jg["bvy"]) * 0.4
        dx = jg["bx"] - jg["px"]
        # la mascota persigue la pelota
        paso = clamp(dx, -310 * dt, 310 * dt)
        jg["px"] = clamp(jg["px"] + paso, 130, ANCHO - 130)
        if abs(paso) > 0.1:
            jg["pdir"] = 1 if paso > 0 else -1
        if jg["by"] >= floor_y:
            jg["by"] = floor_y
            if abs(dx) < 95 and jg["cat"] <= 0:         # la mascota la atrapa y la devuelve al aire
                jg["bvy"] = -640
                jg["bvx"] = self.rng.uniform(-260, 260)
                jg["pts"] += 3
                jg["catches"] += 1
                jg["cat"] = 0.7
                jg["salto"] = 0.5
                self.parts.corazon(jg["px"], SUELO_Y - h)
                self._sonido("pop")
                self.flot.append(TextoFlotante("+3", jg["px"], SUELO_Y - h - 10, (255, 200, 220), 1.0, 60))
            else:
                jg["bvy"] = -max(150.0, abs(jg["bvy"]) * 0.65)
                jg["bvx"] *= 0.92
        # el jugador la lanza pasando el cursor por encima
        pos = V2(ctrl.pos)
        bola = V2(jg["bx"], jg["by"])
        d = pos.distance_to(bola)
        if d < R + 18 and jg["cd"] <= 0:
            dirv = (bola - pos)
            dirv = dirv.normalize() if dirv.length() > 1 else V2(0, -1)
            mov = (V2(ctrl.p2) - V2(ctrl.p1)) / max(dt, 1e-3)
            if mov.length() > 600:
                mov.scale_to_length(600)
            jg["bvx"] = clamp(dirv.x * 300 + mov.x * 0.25, -480, 480)
            jg["bvy"] = min(-420.0, dirv.y * 300 + mov.y * 0.25 - 220)
            jg["cd"] = 0.4
            jg["pts"] += 5
            jg["hits"] += 1
            self._sonido("lanzar")
            self.flot.append(TextoFlotante("+5", bola.x, bola.y - 30, (255, 240, 120), 0.9, 60))
            for _ in range(5):
                self.parts.chispa(bola.x, bola.y, (255, 240, 150), 11, 170, 0.6)
        if jg["t"] <= 0:
            jg["t"] = 0.0
            gan = TD.jugar(self.perfil, jg["pts"])
            jg["gan"] = gan
            jg["fin"] = 2.8
            self._guardar()
            self._sonido("premio")
            for _ in range(30):
                self.parts.confeti(ANCHO / 2, 300)
            self.st = TD.estado(self.perfil)
            self.m = self.st["activa"]

    # ------------------------------------------------------------ evolucion
    def _iniciar_evo(self):
        m = self.m
        esp, e0, n0 = m["especie"], m["etapa"], m["nombre"]
        e1 = TD.evolucionar(self.perfil)
        if e1 is None:
            return
        self._guardar()
        self.st = TD.estado(self.perfil)
        self.m = self.st["activa"]
        self.evo = dict(t=0.0, esp=esp, e0=e0, e1=e1, n0=n0, n1=self.m["nombre"],
                        s0=silueta_blanca(esp, e0, ESC_EVO), s1=silueta_blanca(esp, e1, ESC_EVO), flash=False, snd=0)
        self.sub = "evo"
        self.ov = (None, 0.0)
        self._sonido("lanzar")
        self._reset_botones()

    EVO_T_REVELA = 3.78

    def _act_evo(self, dt, ctrl):
        e = self.evo
        e["t"] += dt
        t = e["t"]
        cx, cy = 640, 385
        if 0.5 < t < 3.6 and self.rng.random() < dt * 30:
            self.parts.chispa(cx + self.rng.uniform(-120, 120), cy + self.rng.uniform(-100, 140),
                              self.rng.choice([(255, 255, 255), (255, 225, 120), (255, 170, 220), (150, 225, 255)]), 12,
                              60, 1.0, -40)
        if int(t * 3) != e["snd"] and t < 3.6:
            e["snd"] = int(t * 3)
            self.sonidos.nota(330 + 55 * e["snd"], 0.18, 0.18)
        if t >= self.EVO_T_REVELA and not e["flash"]:
            e["flash"] = True
            self._sonido("premio")
            for _ in range(40):
                self.parts.confeti(cx, cy - 40)
            for _ in range(10):
                self.parts.estrella(cx, cy)
        if t > 5.2:
            if self.b_evo_ok.actualizar(dt, ctrl):
                self._sonido("ok")
                self.evo = None
                self.sub = None
                self.px = 640.0
                self.ov = ("feliz", self.t + 2.0)
                self._reset_botones()
                self._guardar()

    def _act_graduar(self, dt, ctrl):
        if self.b_g_si.actualizar(dt, ctrl):
            nombre = self.m["nombre"]
            if TD.graduar(self.perfil):
                self._guardar()
                self.sub = None
                self.st = TD.estado(self.perfil)
                self.m = None
                self._sonido("premio")
                self._abrir_libro("salon")
                self.libro.celebrar(nombre)
            else:
                self.sub = None
            return
        if self.b_g_no.actualizar(dt, ctrl):
            self.sub = None
            self._reset_botones()

    # ============================================================ DIBUJO DEL HOGAR
    def _dibujar_hogar(self, p):
        m = self.m
        noche = bool(m["dormida"])
        AT.dibujar_fondo_hogar(p, self.t, noche)
        if self.sub == "jugar":
            self._dibujar_juego(p)
        elif self.sub == "evo":
            self._dibujar_evo(p)
        else:
            self._dibujar_pet_normal(p)
        if self.sub != "evo":
            self._dibujar_panel_superior(p)
            self._dibujar_necesidades(p)
            self._dibujar_botones_top(p)
            self._dibujar_barra_acciones(p)
        self.parts.dibujar(p)
        for f in self.flot:
            f.dibujar(p, fuente(30))
        if self.sub == "comer":
            self._dibujar_panel_comer(p)
        elif self.sub == "graduar":
            self._dibujar_panel_graduar(p)
        elif self.sub == "evo":
            self._dibujar_texto_evo(p)
        elif self.sub is None and not noche:
            self._dibujar_botones_especiales(p)
        self._dibujar_aviso(p)

    def _dibujar_pet_normal(self, p):
        m = self.m
        a = self.anim
        n = min(m["cacas"], len(CACAS_POS)) if not (a and a["tipo"] == "limpiar") else a["n"]
        for i in range(n):
            x, y = CACAS_POS[i % len(CACAS_POS)]
            esc = 1.0
            if a and a["tipo"] == "limpiar":
                esc = clamp(1 - (a["t"] - i * DUR_CACA - 1.0) / 0.45)
                if esc <= 0:
                    continue
            AT.dibujar_caca(p, x, y, esc, self.t + i)
        cx, cy = self._centro_pet()
        estado = self._estado_visual()
        h = self._alto_pet()
        e = m["etapa"]
        if m["dormida"]:
            glow(p, cx, cy, h * 0.9, (120, 140, 255), 60)
        AT.dibujar_mascota(p, m["especie"], e, cx, cy, ESC_HOGAR[e], self.t, estado, self.vdir)
        nivel, fac = self._nivel_polvo(), 1.0
        if a is not None and a["tipo"] == "limpiar":
            nivel = a["nivel"]
            fac = 1.0 - clamp((a["t"] - a["t_bano"] - 0.2) / 1.6)       # el polvo se va con la ducha
        if nivel > 0 and fac > 0:
            s, (dx, dy) = overlay_mascota(m["especie"], e, ESC_HOGAR[e], self.vdir, "polvo", nivel)
            s.set_alpha(int(255 * fac))
            p.blit(s, (cx + dx, cy + dy))
        if a is not None:
            self._dibujar_anim(p, a, cx, cy, h)
        elif self.sub is None and not m["dormida"]:
            necesidad = TD.necesidad_baja(self.perfil)
            if necesidad:
                nx = min(cx + h * 0.55 + 20, ANCHO - 90)
                ny = max(236, cy - h * 0.5 - 30)
                AT.dibujar_nube_estado(p, nx, ny, necesidad, self.t)
        if m["dormida"]:
            velo(p, 55, (20, 20, 70))

    def _dibujar_anim(self, p, a, cx, cy, h):
        t = a["t"]
        tipo = a["tipo"]
        if tipo == "comer":
            if t < 0.9:
                f = clamp(t / 0.9)
                f = f * f * (3 - 2 * f)
                x = (cx + self.vdir * 170) * (1 - f) + (cx + self.vdir * 24) * f
                y = (cy - h * 0.2 - 250) * (1 - f) + (cy - h * 0.02) * f
                catalogo.dibujar_item(p, a["item"], x, y, int(110 - 40 * f))
                glow(p, x, y, 70, (255, 240, 170), 60)
        elif tipo == "limpiar":
            if t < a["t_bano"]:                      # escoba barriendo la caca actual
                i = min(int(t // DUR_CACA), a["n"] - 1)
                ti = t - i * DUR_CACA
                x0, y0 = CACAS_POS[i % len(CACAS_POS)]
                x_ini = CACAS_POS[(i - 1) % len(CACAS_POS)][0] if i > 0 else min(ANCHO - 70, x0 + 280)
                f = clamp(ti / 0.5)
                f = f * f * (3 - 2 * f)
                xb = x_ini + (x0 - x_ini) * f
                ang, alza = 0.0, 0.0
                if 0.5 <= ti < 1.5:
                    s = math.sin((ti - 0.5) * math.tau * 1.5)
                    xb = x0 + 42 * s
                    ang = 0.32 * s
                elif ti >= 1.5:
                    alza = 24 * clamp((ti - 1.5) / 0.5)
                escoba(p, xb, y0 + 14 - alza, ang)
                return
            t = t - a["t_bano"]
            # ducha sobre la mascota: cabezal arriba, chorritos y espuma
            top = cy - h * 0.62
            hx = cx
            if 0.3 <= t <= 2.5:
                fe = clamp((t - 0.3) / 1.2) * clamp((2.5 - t) / 0.7)
                sp_, (dx, dy) = overlay_mascota(self.m["especie"], self.m["etapa"], ESC_HOGAR[self.m["etapa"]], self.vdir, "espuma")
                sp_.set_alpha(int(255 * fe))
                p.blit(sp_, (cx + dx, cy + dy))
            if t < 2.7:
                f = clamp(t / 0.4) * clamp((2.7 - t) / 0.3)
                yb = top - 70 * (1 - clamp(t / 0.4))
                pygame.draw.rect(p, (150, 160, 185), (hx - 5, yb - 80, 10, 60), border_radius=4)
                pygame.draw.ellipse(p, (170, 180, 205), (hx - 46, yb - 30, 92, 30))
                pygame.draw.ellipse(p, (90, 100, 130), (hx - 46, yb - 30, 92, 30), 3)
                pygame.draw.ellipse(p, (230, 240, 255), (hx - 36, yb - 24, 40, 8))
                for i in range(18):
                    ph = (t * 2.2 + i * 0.37) % 1.0
                    xx = hx - 38 + (i * 4.4) % 76
                    y0 = yb
                    y1 = y0 + (cy + h * 0.45 - y0) * ph
                    s = pygame.Surface((6, 30), pygame.SRCALPHA)
                    pygame.draw.line(s, (150, 210, 255, int(220 * f)), (3, 0), (3, 26), 4)
                    p.blit(s, (xx, y1))
        elif tipo == "curar":
            self._dibujar_curar(p, a, cx, cy, h)

    def _dibujar_curar(self, p, a, cx, cy, h):
        t = a["t"]
        # botiquin con la fila de curitas puestas
        f = ease_out_back(clamp(t / 0.6)) if a["marcas"] else 0.0
        bx, by = 250, 440
        if f > 0.02:
            botiquin(p, bx, by, f, self.t)
            for i in range(a["n"]):
                sx, sy = bx - 70 + 14 + i * 28, by + 62
                pygame.draw.circle(p, (255, 255, 255), (sx, sy), 12)
                if i < a["k"]:
                    curita(p, sx, sy, -0.5, 0.3)
                else:
                    pygame.draw.circle(p, (150, 140, 175), (sx, sy), 12, 2)
        for mk in a["marcas"]:
            x, y = cx + mk["dx"], cy + mk["dy"]
            if mk["est"] == 1:
                ap = clamp((t - mk["ap"]) / 0.3)
                glow(p, x, y, 54, (255, 240, 200), int(70 * ap))
                dibujar_marca(p, x, y, mk["tipo"], self.t + x * 0.01, ease_out_back(ap))
                if mk["hover"] > 0:                      # anillo de permanencia
                    fr = clamp(mk["hover"] / CURA_HOVER)
                    r = pygame.Rect(0, 0, CURA_RADIO * 2 - 4, CURA_RADIO * 2 - 4)
                    r.center = (int(x), int(y))
                    pygame.draw.circle(p, (255, 255, 255), r.center, r.w // 2, 3)
                    pygame.draw.arc(p, (255, 205, 60), r, math.pi / 2, math.pi / 2 + math.tau * fr, 8)
            elif mk["est"] == 2 and mk["tc"] < 1.3:
                tc = mk["tc"]
                if tc < 0.25:
                    dibujar_marca(p, x, y, mk["tipo"], self.t, 1.0, int(255 * (1 - tc / 0.25)))
                glow(p, x, y, 62, (255, 235, 210), int(110 * clamp(1 - tc / 1.0)))
                tam = ease_out_back(clamp(tc / 0.3))
                curita(p, x, y, -0.5, 0.95 * tam, int(255 * clamp((1.3 - tc) / 0.3)))
        if a["completo"]:
            fe = clamp((t - a["fin_t"]) / CURA_CIERRE)
            glow(p, cx, cy, h * 0.8, (150, 255, 180), int(90 * math.sin(fe * math.pi)))

    def _dibujar_panel_superior(self, p):
        m = self.m
        info = TD.ESPECIES[m["especie"]]
        tipo = info["tipo"]
        col = AT.COLOR_TIPO[tipo]
        r = pygame.Rect(12, 8, 886, 94)
        tarjeta(p, r, (255, 250, 240), 225, 24, oscurecer(col, 0.3), 4)
        # icono de tipo
        pygame.draw.circle(p, aclarar(col, 0.55), (r.x + 48, r.y + 34), 28)
        pygame.draw.circle(p, oscurecer(col, 0.3), (r.x + 48, r.y + 34), 28, 3)
        AT.dibujar_icono_tipo(p, tipo, r.x + 48, r.y + 34, 22)
        nombre = m["nombre"]
        fn = ajustar(36, nombre, 330, 20)
        rn = escribir(p, fn, nombre, r.x + 90, r.y + 32, (60, 45, 90), "izq", contorno=None)
        etapa = TD.ETAPAS[m["etapa"]]
        px = rn.right + 14
        pastilla(p, fuente(20), etapa, px + fuente(20).size(etapa)[0] / 2 + 14, r.y + 32, aclarar(col, 0.5),
                 (60, 45, 90), oscurecer(col, 0.3), 14, 32)
        px2 = px + fuente(20).size(etapa)[0] + 40
        escribir(p, fuente(20), AT.NOMBRE_TIPO[tipo], px2, r.y + 32, oscurecer(col, 0.45), "izq", contorno=None)
        # xp
        necesaria = TD.xp_necesaria(m["etapa"])
        lleno = m["xp"] >= necesaria
        br = pygame.Rect(r.x + 90, r.y + 58, 420, 24)
        c0, c1 = ((255, 225, 90), (255, 160, 30)) if lleno else ((150, 200, 255), (90, 120, 240))
        barra_bonita(p, br, m["xp"] / max(1, necesaria), c0, c1, (200, 195, 220), (110, 90, 150),
                     titilar=(0.5 + 0.5 * math.sin(self.t * 6)) if lleno else 0.0)
        txt = "¡Listo!" if lleno and m["etapa"] < 3 else f"XP {m['xp']} / {necesaria}"
        escribir(p, fuente(16), txt, br.centerx, br.centery, (255, 255, 255), contorno=(60, 45, 110), grosor=1)
        # puntos de etapa
        for i in range(4):
            c = (r.x + 545 + i * 34, r.y + 70)
            hecho = i <= m["etapa"]
            pygame.draw.circle(p, (255, 205, 60) if hecho else (205, 200, 220), c, 11)
            pygame.draw.circle(p, (150, 100, 20) if hecho else (150, 145, 170), c, 11, 2)
            if i == m["etapa"]:
                pygame.draw.circle(p, (255, 255, 255), c, 15, 2)
        # monedas
        moneda(p, r.right - 130, r.y + 47, 17)
        escribir(p, fuente(32), str(self.perfil.monedas), r.right - 100, r.y + 47, (150, 100, 20), "izq", contorno=None)

    def _dibujar_necesidades(self, p):
        m = self.m
        n = len(NECESIDADES)
        gap = 6
        w = (ANCHO - 24 - (n - 1) * gap) // n
        x0 = (ANCHO - (n * w + (n - 1) * gap)) // 2
        for i, (clave, accion, c0, c1, nombre) in enumerate(NECESIDADES):
            es_vida = clave == "hp"
            v = self.vis["hp"] * 100.0 if es_vida else (self.vis["salud"] if clave == "salud" else m[clave])
            r = pygame.Rect(x0 + i * (w + gap), 110, w, 42)
            baja = v < (TD.HP_URGENTE * 100 if es_vida else NIVEL_BAJO) and not (clave == "energia" and m["dormida"])
            blink = 0.5 + 0.5 * math.sin(self.t * (4 if es_vida else 6)) if baja else 0.0
            borde = mezcla((130, 110, 160), (255, 90, 90), blink) if baja else (130, 110, 160)
            tarjeta(p, r, mezcla((255, 250, 240), (255, 215, 215), blink), 220, 21, borde, 3, False)
            ic_y = r.centery + (math.sin(self.t * 12) * 2 if baja else 0)
            if es_vida:
                icono_vida(p, r.x + 25, ic_y, 34)
                c0, c1 = colores_vida(v / 100.0)
            else:
                AT.dibujar_icono_accion(p, accion, r.x + 25, ic_y, 34, True)
            br = pygame.Rect(r.x + 50, r.centery - 10, w - 62, 20)
            if baja and not es_vida:
                c0, c1 = (255, 150, 120), (235, 60, 60)
            barra_bonita(p, br, v / 100.0, c0, c1, (200, 195, 220), (110, 90, 150), titilar=blink)
            escribir(p, fuente(14), nombre, br.centerx, br.centery, (255, 255, 255), contorno=(60, 45, 110), grosor=1)

    def _dibujar_botones_top(self, p):
        for b in (self.b_cuaderno, self.b_salon, self.b_volver):
            b.dibujar(p, None, self.t)

    def _dibujar_barra_acciones(self, p):
        m = self.m
        tarjeta(p, (14, 618, ANCHO - 28, 100), (255, 245, 225), 170, 26, (190, 140, 100), 3, False)
        if m["dormida"]:
            self.b_despertar.dibujar(p, None, self.t)
            escribir(p, fuente(24), "Zzz... está durmiendo", 250, 668, (255, 255, 255), contorno=(40, 50, 110))
            escribir(p, fuente(24), "Duerme hasta llenar la energía", ANCHO - 260, 668, (255, 255, 255), contorno=(40, 50, 110))
            return
        bloqueado = self.sub is not None
        for nombre, b in self.acc.items():
            b.activo = not bloqueado
            b.dibujar(p, None, self.t)

    def _dibujar_botones_especiales(self, p):
        if TD.puede_evolucionar(self.perfil):
            self.b_evo.dibujar(p, None, self.t)
        elif TD.puede_graduar(self.perfil):
            self.b_graduar.dibujar(p, None, self.t)

    def _dibujar_aviso(self, p):
        txt, seg, col = self.aviso
        if seg <= 0 or not txt:
            return
        a = clamp(seg / 0.4)
        fn = ajustar(28, txt, 1000, 18)
        r = pastilla(p, fn, txt, ANCHO / 2, 190 + (1 - a) * -10, (60, 45, 100), col, (255, 255, 255), 30, 52, int(235 * a))
        return r

    # ------------------------------------------------------------ panel de comida
    def _dibujar_panel_comer(self, p):
        velo(p, 110)
        m = self.m
        R = self.pr
        tarjeta(p, R, (255, 248, 235), 245, 30, (190, 130, 80), 5)
        escribir(p, self.f.grande, f"¿Qué quiere comer {m['nombre']}?", R.centerx, R.y + 40, (150, 90, 40), contorno=None)
        fav = TD.favorita(m["especie"])
        frase = NOMBRE_CAT.get(fav, "Le encanta " + fav)
        escribir(p, fuente(22), frase, R.centerx + 14, R.y + 82, (190, 70, 110), contorno=None)
        w = fuente(22).size(frase)[0]
        corazon(p, int(R.centerx + 14 - w / 2 - 20), R.y + 82, 12)
        if not self.cartas:
            self._dibujar_sin_comida(p)
        for item, n, b in self.cartas:
            r = b.rect
            es_fav = catalogo.info(item)["cat"] == fav
            hov = b.encima
            tarjeta(p, r, (255, 255, 255) if not hov else (255, 245, 215), 255, 20,
                    (240, 90, 140) if es_fav else ((255, 190, 60) if hov else (205, 175, 140)), 4 if (es_fav or hov) else 3,
                    False)
            catalogo.dibujar_item(p, item, r.centerx, r.y + 52, 76)
            nombre = catalogo.nombre_item(item)
            escribir(p, ajustar(20, nombre, r.w - 14, 13), nombre, r.centerx, r.y + 104, (90, 60, 40), contorno=None)
            escribir(p, fuente(24), f"x{n}", r.centerx, r.y + 130, (150, 100, 30), contorno=None)
            if es_fav:
                corazon(p, r.right - 22, r.y + 22, 14)
            if b.dwell > 0:
                from ajustes import DWELL_SEG
                barra_bonita(p, (r.x + 14, r.bottom - 16, r.w - 28, 10), b.dwell / DWELL_SEG, (255, 215, 90), (255, 150, 40))
        self.b_c_cerrar.dibujar(p, None, self.t)
        self.b_c_granja.dibujar(p, None, self.t)
        if self.comer_npag > 1:
            self.b_c_prev.dibujar(p, None, self.t)
            self.b_c_next.dibujar(p, None, self.t)
            escribir(p, fuente(22), f"{self.comer_pag + 1} / {self.comer_npag}", R.centerx, self.b_c_prev.rect.centery, (120, 80, 40),
                     contorno=None)

    def _dibujar_sin_comida(self, p):
        R = PANEL_COMER
        catalogo.dibujar_item(p, "manzana", R.centerx - 150, 330, 110)
        catalogo.dibujar_item(p, "zanahoria", R.centerx, 310, 110)
        catalogo.dibujar_item(p, "huevo", R.centerx + 150, 330, 110)
        escribir(p, self.f.grande, "¡Uy! No hay comida en la mochila", R.centerx, 420, (190, 90, 60), contorno=None)
        escribir_parrafo(p, fuente(26), "En la granja puedes cosechar frutas y verduras. ¡Vamos a buscarlas!", R.centerx, 475, 880,
                         (120, 80, 50), None)

    def _dibujar_panel_graduar(self, p):
        velo(p, 120)
        m = self.m
        r = self.pr_grad
        tarjeta(p, r, (255, 248, 230), 245, 30, (230, 170, 50), 6)
        escribir(p, ajustar(44, f"¡{m['nombre']} lo logró!", 760, 24), f"¡{m['nombre']} lo logró!", r.centerx, r.y + 48,
                 (170, 110, 20), contorno=None)
        escribir(p, fuente(24), "Llegó a su forma más poderosa", r.centerx, r.y + 88, (150, 100, 40), contorno=None)
        AT.dibujar_mascota(p, m["especie"], m["etapa"], r.centerx, r.y + 215, 0.62, self.t, "feliz", 1)
        escribir_parrafo(p, fuente(24), "¿Pasa al Salón de las Mascotas para elegir otro huevo, o seguimos juntos?",
                         r.centerx, r.y + 332, 760, (120, 80, 40), None, 28, 2)
        self.b_g_si.dibujar(p, None, self.t)
        self.b_g_no.dibujar(p, None, self.t)

    # ------------------------------------------------------------ juego de la pelota
    def _dibujar_juego(self, p):
        jg = self.jg
        m = self.m
        e = m["etapa"]
        h = self._alto_pet()
        floor_y = SUELO_Y - 40
        cy = SUELO_Y - h / 2 - (math.sin(jg["salto"] / 0.5 * math.pi) * 40 if jg["salto"] > 0 else 0)
        estado = "feliz" if jg["fin"] is not None or jg["salto"] > 0 else "normal"
        AT.dibujar_mascota(p, m["especie"], e, jg["px"], cy, ESC_HOGAR[e], self.t, estado, jg["pdir"])
        pelota(p, jg["bx"], jg["by"], 34, jg["ang"], SUELO_Y + 4)
        # HUD
        if jg["fin"] is None:
            tarjeta(p, (ANCHO // 2 - 250, 166, 500, 62), (255, 250, 240), 230, 22, (190, 120, 150), 4, False)
            barra_bonita(p, (ANCHO // 2 - 230, 176, 300, 22), jg["t"] / TIEMPO_JUGAR, (255, 215, 90), (255, 130, 60),
                         (200, 195, 220), (110, 90, 150))
            escribir(p, fuente(20), f"{int(jg['t']) + 1} s", ANCHO // 2 - 80, 187, (255, 255, 255), contorno=(110, 70, 30), grosor=1)
            escribir(p, fuente(30), f"Puntos: {jg['pts']}", ANCHO // 2 + 175, 187, (190, 70, 110), contorno=None)
            if jg["t"] > TIEMPO_JUGAR - 4 or jg["hits"] == 0 and jg["t"] > TIEMPO_JUGAR - 9:
                pastilla(p, fuente(26), "¡Pasa el cursor por la pelota para lanzarla!", ANCHO / 2, 258, (255, 255, 255),
                         (110, 70, 150), None, 26, 46, 235)
        else:
            r = pygame.Rect(0, 0, 640, 200)
            r.center = (ANCHO // 2, 300)
            tarjeta(p, r, (255, 248, 235), 245, 30, (230, 130, 170), 5)
            escribir(p, self.f.grande, "¡Qué divertido!", r.centerx, r.y + 46, (190, 70, 110), contorno=None)
            escribir(p, fuente(30), f"Puntos: {jg['pts']}", r.centerx, r.y + 102, (120, 80, 50), contorno=None)
            escribir(p, fuente(30), f"Alegría +{int(round(jg['gan']))}", r.centerx, r.y + 146, (235, 80, 140), contorno=None)

    # ------------------------------------------------------------ evolucion (dibujo)
    def _dibujar_evo(self, p):
        e = self.evo
        t = e["t"]
        cx, cy = 640, 385
        velo(p, clamp(t / 1.0) * 120, (20, 10, 50))
        if self._aura_buf is None:
            self._aura_buf = pygame.Surface((ANCHO, ALTO))
        self._aura_buf.fill((0, 0, 0))
        dibujar_aura_evolucion(self._aura_buf, cx, cy + 20, clamp(t / 4.2), self.t)
        p.blit(self._aura_buf, (0, 0), special_flags=pygame.BLEND_ADD)
        T = self.EVO_T_REVELA
        esp = e["esp"]
        if t < 1.9:                                         # la forma vieja se vuelve luz
            AT.dibujar_mascota(p, esp, e["e0"], cx, cy, ESC_EVO, self.t, "evoluciona", 1)
            a = clamp((t - 0.7) / 1.0)
            if a > 0:
                s = e["s0"]
                s.set_alpha(int(255 * a))
                p.blit(s, s.get_rect(center=(cx, cy)))
        elif t < T:                                         # silueta que cambia de forma
            f = clamp((t - 1.9) / (T - 1.9 - 0.3))
            f = f * f * (3 - 2 * f)
            pul = 1 + 0.05 * math.sin(t * 14)
            for s, a, k in ((e["s0"], 1 - f, 1.0), (e["s1"], f, 1.0)):
                s2 = pygame.transform.smoothscale(s, (int(s.get_width() * pul), int(s.get_height() * pul)))
                s2.set_alpha(int(255 * a))
                p.blit(s2, s2.get_rect(center=(cx, cy)))
        else:                                               # revelacion de la nueva forma
            AT.dibujar_mascota(p, esp, e["e1"], cx, cy, ESC_EVO, self.t, "feliz", 1)
            a = clamp(1 - (t - T) / 0.7)
            if a > 0:
                s = e["s1"]
                s.set_alpha(int(255 * a))
                p.blit(s, s.get_rect(center=(cx, cy)))
        self.parts.dibujar(p)
        if t >= T:
            flash(p, clamp(1 - (t - T) / 0.5) * 0.9)
        # el destello de la aura ocurre cerca de T: se suma un flash propio
        if T - 0.35 < t < T:
            flash(p, (t - (T - 0.35)) / 0.35)

    def _dibujar_texto_evo(self, p):
        e = self.evo
        t = e["t"]
        if t < self.EVO_T_REVELA + 0.5:
            if t < 3.0:
                escribir(p, fuente(44), "¡Está evolucionando!", ANCHO / 2, 70, (255, 250, 235), contorno=(110, 60, 140), grosor=4)
            return
        k = ease_out_back((t - self.EVO_T_REVELA - 0.5) / 0.7)
        info = TD.ESPECIES[e["esp"]]
        col = AT.COLOR_TIPO[info["tipo"]]
        escribir(p, fuente(int(46 * clamp(k, 0.3, 1.1))), f"¡{e['n0']} ahora es {e['n1']}!", ANCHO / 2, 70 - (1 - clamp(k)) * 30,
                 (255, 250, 235), contorno=oscurecer(col, 0.6), grosor=4)
        if t > 5.0:
            escribir(p, fuente(32), MENSAJE_EVO[max(0, min(2, e["e1"] - 1))], ANCHO / 2, 575, (255, 250, 235), contorno=(100, 60, 30))
            pastilla(p, fuente(26), TD.ETAPAS[e["e1"]], ANCHO / 2, 128, aclarar(col, 0.55), (60, 45, 90),
                     oscurecer(col, 0.35), 30, 46)
        if t > 5.2:
            self.b_evo_ok.dibujar(p, None, self.t)

    # ============================================================ DIBUJO
    def dibujar(self, p):
        if self.modo == "huevos":
            self._dibujar_huevos(p)
            self.parts.dibujar(p)
            self._dibujar_aviso(p)
        elif self.modo == "eclosion":
            self._dibujar_eclosion(p)
            if self.hatch is None:
                self._dibujar_aviso(p)
        elif self.modo == "hogar" and self.m is not None:
            self._dibujar_hogar(p)
        elif self.libro is not None:
            self.libro.dibujar(p)
            self.parts.dibujar(p)
            self._dibujar_aviso(p)
