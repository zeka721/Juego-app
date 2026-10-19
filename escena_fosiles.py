"""Escenas de Fosiles: la EXPEDICION (centro del juego) y el TALLER de herramientas.

ExpedicionEscena(app)       mundos, dinosaurios y su progreso, zona de excavacion (carrito), grado y EXCAVAR.
TallerEscena(app, volver)   crafteo de brocha, martillo, cincel y cincel pequeno (1 a 5 estrellas) y lista
                            de tus herramientas (durabilidad, equipar).

Todo se maneja con el cursor (Boton con permanencia), con textos grandes y sin castigos: si faltan
materiales o monedas solo se avisa con un mensaje amable. La logica vive en fosiles_datos.
"""

import math
import random

import pygame

import arte_paleo as arte
import catalogo
import fosiles_datos as fd
from ajustes import ANCHO, ALTO
from catalogo import dibujar_item
from escena import Escena
from escena_items import BotonF, TINTA, TINTA_SUAVE, PAPEL, MADERA, ajustado, moneda
from nucleo import (Boton, Particula, TextoFlotante, aclarar, barra, escribir, estrella, explosion,
                    fondo, oscurecer, panel)

ROJO = (200, 60, 50)
VERDE = (40, 130, 60)
ORO = (235, 170, 20)
GEMA_COL = (170, 110, 230)
COLOR_HERR = {"brocha": (214, 150, 70), "martillo": (206, 96, 84), "cincel": (84, 132, 208),
              "cincel_pequeno": (60, 170, 150)}
NOMBRE_CAPA = {"polvo": "Polvo", "barro": "Barro", "rocas": "Rocas", "cristales": "Cristales"}
ARTICULO = {"brocha": "una", "martillo": "un", "cincel": "un", "cincel_pequeno": "un"}
NOMBRE_MIN = {"brocha": "brocha", "martillo": "martillo", "cincel": "cincel",
              "cincel_pequeno": "cincel pequeño"}
EXPLICA_HERR = {
    "brocha": "La brocha limpia el polvo que cubre los huesos.",
    "martillo": "El martillo rompe las rocas con golpes suaves.",
    "cincel": "El cincel parte las rocas duras y los cristales.",
    "cincel_pequeno": "El cincel pequeño quita el barro con cuidado.",
}
ORDEN_MAT = ["madera", "cerda", "hierro", "acero", "cuarzo", "gema_fosil"]
POR_PAGINA_MIAS = 7


def corto_mundo(i):
    n = fd.MUNDOS[i]["nombre"]
    for pre in ("Mundo de los ", "Mundo de las ", "Mundo de la ", "Mundo de "):
        if n.startswith(pre):
            return n[len(pre):]
    return n


def _plural(n, uno, varios):
    return f"{n} {uno if n == 1 else varios}"


def _mmss(s):
    s = int(math.ceil(max(0.0, s)))
    return f"{s // 60}:{s % 60:02d}"


def _estrellas_txt(n):
    return f"{n} estrella" + ("" if n == 1 else "s")


# ---------------------------------------------------------------- dibujo de iconos y piezas
def dibujar_candado(p, x, y, s=24, color=(150, 155, 175)):
    x, y = int(x), int(y)
    osc = oscurecer(color, 0.5)
    pygame.draw.arc(p, osc, (x - int(s * 0.62), y - int(s * 1.25), int(s * 1.24), int(s * 1.5)), 0, math.pi, 7)
    pygame.draw.arc(p, (215, 218, 230), (x - int(s * 0.62), y - int(s * 1.25), int(s * 1.24), int(s * 1.5)),
                    0, math.pi, 3)
    r = pygame.Rect(x - s, y - int(s * 0.3), 2 * s, int(s * 1.5))
    pygame.draw.rect(p, osc, r.move(0, 3), border_radius=8)
    pygame.draw.rect(p, color, r, border_radius=8)
    pygame.draw.rect(p, osc, r, 3, border_radius=8)
    pygame.draw.circle(p, osc, (x, y + int(s * 0.3)), max(3, int(s * 0.22)))
    pygame.draw.rect(p, osc, (x - 2, y + int(s * 0.3), 5, int(s * 0.5)))


def dibujar_llave(p, x, y, s=24, color=(255, 205, 50)):
    x, y = int(x), int(y)
    osc = oscurecer(color, 0.5)
    cx = x - int(s * 0.55)
    pygame.draw.line(p, osc, (cx, y), (x + s, y), 9)
    pygame.draw.line(p, color, (cx, y), (x + s, y), 5)
    for dx in (int(s * 0.55), int(s * 0.95)):
        pygame.draw.line(p, osc, (x + dx, y), (x + dx, y + int(s * 0.5)), 8)
        pygame.draw.line(p, color, (x + dx, y), (x + dx, y + int(s * 0.5)), 4)
    pygame.draw.circle(p, osc, (cx, y), int(s * 0.5))
    pygame.draw.circle(p, color, (cx, y), int(s * 0.5) - 3)
    pygame.draw.circle(p, osc, (cx, y), int(s * 0.2))


def dibujar_gema(p, x, y, s=16, color=GEMA_COL):
    x, y = int(x), int(y)
    pts = [(x, y - s), (x + int(s * 0.85), y - int(s * 0.2)), (x, y + s), (x - int(s * 0.85), y - int(s * 0.2))]
    pygame.draw.polygon(p, color, pts)
    pygame.draw.polygon(p, oscurecer(color, 0.5), pts, 3)
    pygame.draw.polygon(p, aclarar(color, 0.6), [(x, y - s + 3), (x + int(s * 0.3), y - int(s * 0.2)),
                                                 (x - int(s * 0.3), y - int(s * 0.2))])


def estrellitas(p, x, y, n, maximo=None, r=7, sep=16, encendidas=None):
    """Fila de estrellas centrada en x. 'encendidas' (si se da) = cuantas se ven llenas."""
    maximo = n if maximo is None else maximo
    encendidas = n if encendidas is None else encendidas
    x0 = x - (maximo - 1) * sep / 2
    for i in range(maximo):
        if i < encendidas:
            estrella(p, x0 + i * sep, y, r)
        else:
            estrella(p, x0 + i * sep, y, r, color=(225, 215, 195), borde=(170, 155, 130))


def color_dur(f):
    return (90, 200, 120) if f > 0.5 else (240, 200, 60) if f > 0.25 else (240, 130, 60)


def centrado(p, fuente, texto, cx, y, ancho, color=TINTA, interlineado=None, maximo=4):
    """Texto centrado en varias lineas desde y. Devuelve la y siguiente."""
    interlineado = interlineado or fuente.get_linesize()
    lineas, actual = [], ""
    for palabra in str(texto).split():
        prueba = (actual + " " + palabra).strip()
        if fuente.size(prueba)[0] > ancho and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    for i, l in enumerate(lineas[:maximo]):
        ajustado(p, fuente, l, cx, y + i * interlineado + interlineado / 2, ancho, color)
    return y + min(len(lineas), maximo) * interlineado


def tarjeta(p, r, borde, fondo_c=PAPEL, sombra=True, radio=18):
    r = pygame.Rect(r)
    if sombra:
        pygame.draw.rect(p, oscurecer(borde, 0.4), r.move(0, 4), border_radius=radio)
    pygame.draw.rect(p, fondo_c, r, border_radius=radio)
    pygame.draw.rect(p, borde, r, 4, border_radius=radio)


_f24 = {}


def fuente24():
    if "f" not in _f24:
        _f24["f"] = pygame.font.SysFont("arial", 23, bold=True)
    return _f24["f"]


class _Base(Escena):
    """Pieza comun: perfil, sonidos, mensajes, particulas."""

    def __init__(self, app):
        super().__init__(app)
        self.msg = ("", TINTA, 0.0)
        self.flotantes = []
        self.particulas = []

    @property
    def perfil(self):
        return self.app.ctx.perfil

    @property
    def snd(self):
        return self.app.ctx.sonidos

    def decir(self, texto, color=TINTA):
        self.msg = (texto, color, 4.5)

    def _efectos(self, dt):
        txt, col, t = self.msg
        if t > 0:
            self.msg = (txt, col, t - dt)
        self.flotantes = [f for f in self.flotantes if f.actualizar(dt)]
        self.particulas = [x for x in self.particulas if x.actualizar(dt)]

    def _celebrar(self, x, y, texto, color=(255, 215, 60)):
        self.flotantes.append(TextoFlotante(texto, x, y, color, vida=1.3, subida=70))
        explosion(self.particulas, x, y, color, n=16, vida=0.8)

    def _dibujar_efectos(self, p):
        for x in self.particulas:
            x.dibujar(p)
        for f in self.flotantes:
            f.dibujar(p, self.f.normal)

    def _barra_mensaje(self, p, x, ancho, defecto):
        txt, col, t = self.msg
        if t <= 0 or not txt:
            txt, col = defecto, TINTA_SUAVE
        panel(p, (x, ALTO - 78, ancho, 56), color=PAPEL, alfa=235, radio=18, borde=(90, 60, 30))
        ajustado(p, self.f.normal, txt, x + ancho / 2, ALTO - 50, ancho - 30, col)

    def _cabecera(self, p):
        pygame.draw.rect(p, MADERA, (0, 0, ANCHO, 94))
        for y in (31, 62):
            pygame.draw.line(p, oscurecer(MADERA, 0.25), (0, y), (ANCHO, y), 2)
        pygame.draw.rect(p, oscurecer(MADERA, 0.45), (0, 92, ANCHO, 5))


# =====================================================================
#  EXPEDICION
# =====================================================================
class ExpedicionEscena(_Base):
    X_CENTRO = 284
    W_TARJ, H_TARJ = 186, 192
    X_ZONA, W_ZONA = 876, 380

    def __init__(self, app):
        super().__init__(app)
        per = self.perfil
        fd.tick(per)
        e = fd.estado(per)
        self.vista = e["mundo"] if fd.mundo_desbloqueado(per, e["mundo"]) else 0
        try:
            g = int(e.get("grado", 1))
        except (TypeError, ValueError):
            g = 1
        self.grado = max(1, min(fd.grado_max(per), g))
        self.hay_zona = e["zona"] is not None
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.b_taller = BotonF((self.X_ZONA, ALTO - 78, self.W_ZONA, 56), "Taller de herramientas", (60, 160, 190))
        self.b_mundos = [BotonF((24, 102 + i * 104, 246, 96), "", fd.MUNDOS[i]["color"])
                         for i in range(len(fd.MUNDOS))]
        zx = self.X_ZONA
        self.b_menos = BotonF((zx + 16, 318, 60, 56), "-", (70, 150, 230))
        self.b_mas = BotonF((zx + self.W_ZONA - 76, 318, 60, 56), "+", (70, 150, 230))
        self.b_excavar = BotonF((zx + 10, 558, self.W_ZONA - 20, 70), "EXCAVAR", (230, 120, 40))

    # ------------------------------------------------------------ datos
    def necesidades(self):
        """Por cada capa del grado elegido: (capa, herramienta ideal, estrellas, cumple, equipar_mejor)."""
        per = self.perfil
        res = []
        for capa in fd.capas_grado(self.grado):
            req = fd.estrellas_requeridas(self.grado, capa)
            tipos = fd.HERRAMIENTAS_CAPA[capa]
            ok = False
            mejor = None
            for t in tipos:
                a = fd.herramienta_activa(per, t)
                if a and a["est"] >= req:
                    ok = True
                for h in fd.herramientas(per, t):
                    if h["dur"] > 0 and h["est"] >= req and mejor is None:
                        mejor = t
            res.append((capa, tipos[0], req, ok, None if ok else mejor))
        return res

    def aviso_herramientas(self):
        """Texto amable si las herramientas no alcanzan para el grado elegido (o None)."""
        for capa, tipo, req, ok, mejor in self.necesidades():
            if ok:
                continue
            if mejor:
                return f"Equipa {ARTICULO[mejor]} {NOMBRE_MIN[mejor]} de {_estrellas_txt(req)} o más en el Taller"
            return (f"Te falta {ARTICULO[tipo]} {NOMBRE_MIN[tipo]} de {_estrellas_txt(req)}: ve al Taller")
        return None

    # ------------------------------------------------------------ acciones
    def _elegir_mundo(self, i):
        per = self.perfil
        self.vista = i
        self.snd.reproducir("click")
        if fd.mundo_desbloqueado(per, i):
            fd.elegir_mundo(per, i)
            per.guardar()
            self.decir(f"¡Ahora buscas fósiles en {fd.MUNDOS[i]['nombre']}!", VERDE)
        else:
            self.decir("Todavía no tienes la llave de ese mundo.", TINTA_SUAVE)

    def _cambiar_grado(self, d):
        per = self.perfil
        gmax = fd.grado_max(per)
        nuevo = max(1, min(gmax, self.grado + d))
        if nuevo != self.grado:
            self.grado = nuevo
            fd.estado(per)["grado"] = nuevo
            per.guardar()
            self.snd.reproducir("click")

    def _excavar(self):
        from aventura import Partida          # import perezoso: aventura importa este modulo
        per = self.perfil
        fd.estado(per)["grado"] = self.grado
        per.guardar()
        self.snd.reproducir("click")
        self.app.ir(Partida(self.app, "fosiles", self.grado))

    def _ir_taller(self):
        self.snd.reproducir("click")
        self.app.ir(TallerEscena(self.app))

    def _salir(self):
        from aventura import Libre
        self.snd.reproducir("click")
        self.app.ir(Libre(self.app))

    def tecla_esc(self):
        self._salir()

    # ------------------------------------------------------------ bucle
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self._efectos(dt)
        per = self.perfil
        lista = fd.zona_lista(per)
        if lista and not self.hay_zona:
            self.snd.reproducir("premio")
            self._celebrar(self.X_ZONA + self.W_ZONA / 2, 200, "¡Zona lista!")
            per.guardar()
        self.hay_zona = lista
        gmax = fd.grado_max(per)
        self.grado = max(1, min(gmax, self.grado))
        if self.volver.actualizar(dt, ctrl):
            self._salir()
            return
        if self.b_taller.actualizar(dt, ctrl):
            self._ir_taller()
            return
        for i, b in enumerate(self.b_mundos):
            if b.actualizar(dt, ctrl):
                self._elegir_mundo(i)
        if lista:
            self.b_menos.activo = self.grado > 1
            self.b_mas.activo = self.grado < gmax
            if self.b_menos.actualizar(dt, ctrl):
                self._cambiar_grado(-1)
            if self.b_mas.actualizar(dt, ctrl):
                self._cambiar_grado(1)
            if self.b_excavar.actualizar(dt, ctrl):
                self._excavar()

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        fondo(p, (240, 214, 164), (196, 154, 104))
        self._dibujar_cabecera(p)
        self._dibujar_mundos(p)
        self._dibujar_centro(p)
        self._dibujar_herramientas(p)
        self._dibujar_zona(p)
        self.volver.dibujar(p, self.f.normal)
        self.b_taller.dibujar(p, self.f.normal)
        self._barra_mensaje(p, 210, 650, self._defecto())
        self._dibujar_efectos(p)

    def _defecto(self):
        per = self.perfil
        if fd.zona_lista(per):
            return "¡El carrito te avisa! Elige el grado y pulsa EXCAVAR."
        return "Elige un mundo. Cuando el carrito aparezca, ¡a excavar!"

    def _dibujar_cabecera(self, p):
        self._cabecera(p)
        per = self.perfil
        escribir(p, self.f.grande, "Expedición", 150, 47, (255, 240, 200), contorno=(60, 40, 20))
        # pericia
        panel(p, (290, 12, 440, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        xp, por = fd.xp_para_siguiente(per)
        gmax = fd.grado_max(per)
        ajustado(p, self.f.normal, f"Pericia: grado {gmax}", 308, 33, 220, TINTA, ancla="izq")
        if gmax >= fd.GRADOS_MAX:
            ajustado(p, self.f.chica, "¡Máximo!", 712, 33, 100, TINTA_SUAVE, ancla="der")
            barra(p, (306, 52, 408, 18), 1.0, color=(255, 190, 40))
        else:
            ajustado(p, self.f.chica, f"{xp} / {por}", 712, 33, 100, TINTA_SUAVE,
                     ancla="der")
            barra(p, (306, 52, 408, 18), xp / por, color=(255, 190, 40))
        # gemas
        panel(p, (746, 12, 230, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        dibujar_gema(p, 782, 47, 20)
        ajustado(p, self.f.normal, f"Gemas: {per.polvo}", 812, 47, 150, TINTA, ancla="izq")
        # monedas
        panel(p, (992, 12, 264, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        moneda(p, 1024, 47, 17)
        ajustado(p, self.f.grande, f"{per.monedas:,}".replace(",", "."), 1050, 47, 190, TINTA, ancla="izq")

    # ---- columna de mundos
    def _dibujar_mundos(self, p):
        per = self.perfil
        activo = fd.estado(per)["mundo"]
        for i, b in enumerate(self.b_mundos):
            abierto = fd.mundo_desbloqueado(per, i)
            col = fd.MUNDOS[i]["color"] if abierto else (150, 155, 170)
            b.color = col
            b.dibujar(p, self.f.normal)
            if i == self.vista:
                pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(12, 12), 5, border_radius=26)
            r = b.rect
            ajustado(p, self.f.normal, corto_mundo(i), r.x + 16, r.y + 28, r.width - 100, (255, 255, 255),
                     ancla="izq", contorno=(40, 40, 60))
            if abierto:
                vivos = sum(1 for d in fd.MUNDOS[i]["dinos"] if d in per.dinos)
                ajustado(p, self.f.chica, f"Revividos: {vivos} de 6", r.x + 16, r.y + 56, r.width - 100,
                         (255, 255, 255), ancla="izq", contorno=(40, 40, 60))
                if i == activo:
                    ajustado(p, self.f.chica, "Buscando aquí", r.x + 16, r.y + 78, r.width - 100,
                             (255, 240, 160), ancla="izq", contorno=(40, 40, 60))
            else:
                ajustado(p, self.f.chica, "Bloqueado", r.x + 16, r.y + 56, r.width - 100, (255, 255, 255),
                         ancla="izq", contorno=(40, 40, 60))
            ix, iy = r.right - 40, r.centery
            if not abierto:
                dibujar_candado(p, ix, iy + 4, 20)
            elif fd.tiene_llave(per, i) and i < len(fd.MUNDOS) - 1:
                dibujar_llave(p, ix - 6, iy, 18)

    # ---- dinosaurios del mundo elegido
    def _dibujar_centro(self, p):
        per = self.perfil
        i = self.vista
        m = fd.MUNDOS[i]
        abierto = fd.mundo_desbloqueado(per, i)
        vivos = sum(1 for d in m["dinos"] if d in per.dinos)
        titulo = m["nombre"] + (f"  ·  {vivos} de 6 revividos" if abierto else "")
        if abierto and fd.tiene_llave(per, i) and i < len(fd.MUNDOS) - 1:
            titulo = m["nombre"] + "  ·  ¡Llave conseguida!"
        ajustado(p, self.f.normal, titulo, self.X_CENTRO + 288, 117, 576, (60, 40, 20))
        for k, dino in enumerate(m["dinos"]):
            col, fil = k % 3, k // 3
            r = pygame.Rect(self.X_CENTRO + col * (self.W_TARJ + 9), 134 + fil * (self.H_TARJ + 8),
                            self.W_TARJ, self.H_TARJ)
            self._tarjeta_dino(p, r, dino, k, abierto)
        if not abierto:
            self._cartel_bloqueado(p, i)

    def _tarjeta_dino(self, p, r, dino, k, abierto):
        per = self.perfil
        m = fd.MUNDOS[self.vista]
        h, tot = fd.progreso(per, dino)
        viv = dino in per.dinos
        completo = h >= tot
        gemas = fd.costo_revivir(dino)
        listo = completo and not viv and per.polvo >= gemas
        tarjeta(p, r, m["color"] if abierto else (150, 155, 170))
        nombre = arte.DINOS[dino][0]
        ajustado(p, self.f.normal, nombre, r.centerx, r.y + 19, r.width - 16, TINTA)
        zona = pygame.Rect(r.x + 5, r.y + 30, r.width - 10, 86)
        cx, cy = zona.centerx, zona.centery
        p.set_clip(zona)
        if not abierto or (h == 0 and not viv):
            arte.dibujar_dino(p, dino, cx, cy, 0.30, self.t, silueta=True)
        elif viv:
            arte.dibujar_dino(p, dino, cx, cy, 0.30, self.t)
        else:
            brillo = (0.35 + 0.25 * math.sin(self.t * 4)) if listo else 0.0
            arte.dibujar_esqueleto(p, dino, cx, cy, 0.30, frac=h / tot, brillo=brillo)
        p.set_clip(None)
        if viv:
            estrella(p, r.right - 20, r.y + 44, 11)
        # barra y estado
        barra(p, (r.x + 12, r.y + 122, r.width - 24, 16), 1.0 if viv else h / tot,
              color=(90, 200, 120) if completo or viv else (90, 170, 235))
        if not abierto:
            ajustado(p, self.f.normal, f"0 / {tot} huesos", r.centerx, r.y + 154, r.width - 16, TINTA_SUAVE)
            ajustado(p, self.f.chica, "Bloqueado", r.centerx, r.y + 175, r.width - 16, TINTA_SUAVE)
            return
        hh = tot if viv else h
        ajustado(p, self.f.normal, f"{hh} / {tot} huesos", r.centerx, r.y + 154, r.width - 16, TINTA)
        if viv:
            txt, c = "¡Revivido!", VERDE
        elif listo:
            txt, c = "¡Listo para revivir!", (200, 120, 0)
        elif completo:
            txt, c = f"Faltan {_plural(gemas - per.polvo, 'gema', 'gemas')}", (140, 70, 200)
        elif h == 0:
            txt, c = "Aún sin huesos", TINTA_SUAVE
        else:
            txt, c = f"Revivir: {_plural(gemas, 'gema', 'gemas')}", TINTA_SUAVE
        ajustado(p, self.f.normal if (viv or listo or completo) else self.f.chica, txt, r.centerx, r.y + 175,
                 r.width - 12, c)

    def _cartel_bloqueado(self, p, i):
        r = pygame.Rect(self.X_CENTRO + 40, 200, 496, 260)
        pygame.draw.rect(p, (50, 50, 70), r.move(0, 6), border_radius=26)
        panel(p, r, color=(250, 245, 235), alfa=250, radio=26, borde=(110, 115, 135))
        dibujar_candado(p, r.centerx, r.y + 70, 36)
        anterior = fd.MUNDOS[i - 1]["nombre"]
        centrado(p, self.f.normal, f"Revive los 6 de {anterior} para conseguir la llave", r.centerx, r.y + 130,
                 r.width - 50, TINTA, interlineado=36, maximo=3)

    # ---- resumen de herramientas
    def _dibujar_herramientas(self, p):
        per = self.perfil
        panel(p, (self.X_CENTRO, 532, 576, 100), color=PAPEL, alfa=235, radio=18, borde=(150, 110, 60))
        for k, tipo in enumerate(fd.TIPOS_HERR):
            x = self.X_CENTRO + k * 144
            h = fd.herramienta_activa(per, tipo)
            ajustado(p, self.f.chica, fd.NOMBRES_HERR[tipo], x + 72, 549, 130, TINTA)
            if h is None:
                ajustado(p, self.f.chica, "Sin herramienta", x + 72, 590, 130, ROJO)
                barra(p, (x + 10, 612, 124, 14), 0.0)
                continue
            arte.dibujar_herramienta(p, tipo, x + 34, 584, 0.5, 0)
            estrellitas(p, x + 100, 576, h["est"], 5, r=6, sep=14, encendidas=h["est"])
            f = h["dur"] / fd.DURABILIDAD[h["est"]]
            barra(p, (x + 10, 600, 124, 20), f, color=color_dur(f))
            ajustado(p, self.f.chica, f"{int(math.ceil(f * 100))}%", x + 72, 610, 60, (255, 255, 255),
                     contorno=(30, 30, 50))

    # ---- zona de excavacion
    def _dibujar_zona(self, p):
        per = self.perfil
        e = fd.estado(per)
        x0, w = self.X_ZONA, self.W_ZONA
        cx = x0 + w / 2
        r = pygame.Rect(x0, 102, w, 530)
        lista = e["zona"] is not None
        panel(p, r, color=(255, 244, 218) if lista else (232, 228, 222), alfa=245, radio=24,
              borde=(200, 120, 40) if lista else (140, 135, 130))
        if lista:
            self._zona_lista(p, e["zona"], x0, w, cx)
        else:
            self._zona_dormida(p, x0, w, cx)

    def _zona_lista(self, p, z, x0, w, cx):
        per = self.perfil
        ajustado(p, self.f.normal, "¡Zona de excavación lista!", cx, 128, w - 24, (190, 80, 20))
        arte.dibujar_carrito(p, x0 + 66, 232, 0.95, self.t, True)
        dino = z["dino"]
        tx = x0 + 128
        ajustado(p, self.f.chica, "Buscas a:", tx, 160, 220, TINTA_SUAVE, ancla="izq")
        ajustado(p, self.f.normal, arte.DINOS[dino][0], tx, 188, w - 138, TINTA, ancla="izq")
        partes = []
        if len(z["faltan"]):
            partes.append(_plural(len(z["faltan"]), "hueso", "huesos"))
        if z["gemas"] > 0:
            partes.append(_plural(z["gemas"], "gema", "gemas"))
        txt = "Faltan " + " y ".join(partes) if partes else "¡Casi terminada!"
        yy = 212
        for l in self._lineas(self.f.normal, txt, w - 140)[:2]:
            ajustado(p, self.f.normal, l, tx, yy + 16, w - 140, (140, 70, 20), ancla="izq")
            yy += 32
        if z.get("reliquia"):
            arte.dibujar_reliquia(p, z.get("reliquia"), x0 + 40, 296, 0.5, silueta=True)
            ajustado(p, self.f.normal, "¡Hay una reliquia misteriosa!", x0 + 76, 296, w - 90, (110, 70, 190),
                     ancla="izq")
        # grado
        b1, b2 = self.b_menos, self.b_mas
        b1.dibujar(p, self.f.grande)
        b2.dibujar(p, self.f.grande)
        ajustado(p, self.f.grande, f"Grado {self.grado}", cx, 340, 170, TINTA)
        gmax = fd.grado_max(per)
        ajustado(p, self.f.chica, f"Tu grado máximo: {gmax}", cx, 371, 200, TINTA_SUAVE)
        ajustado(p, self.f.normal, f"Tiempo {int(fd.tiempo_grado(self.grado))} s  ·  "
                 f"{_plural(len(fd.capas_grado(self.grado)), 'capa', 'capas')}", cx, 397, w - 24, TINTA)
        # herramientas necesarias
        nec = self.necesidades()
        cw = (w - 24) / max(1, len(nec))
        for k, (capa, tipo, req, ok, mejor) in enumerate(nec):
            xx = x0 + 12 + k * cw
            rr = pygame.Rect(int(xx + 2), 410, int(cw - 4), 74)
            pygame.draw.rect(p, (235, 255, 235) if ok else (255, 232, 228), rr, border_radius=12)
            pygame.draw.rect(p, (90, 190, 110) if ok else (230, 120, 100), rr, 3, border_radius=12)
            ajustado(p, self.f.chica, NOMBRE_CAPA[capa], rr.centerx, rr.y + 12, rr.width - 6, TINTA)
            arte.dibujar_herramienta(p, tipo, rr.x + rr.width * 0.28, rr.y + 46, 0.42, 0)
            ajustado(p, self.f.normal, f"{req}", rr.x + rr.width * 0.58, rr.y + 48, 30,
                     VERDE if ok else ROJO, ancla="izq")
            estrella(p, rr.x + rr.width * 0.58 + 26, rr.y + 48, 8)
        aviso = self.aviso_herramientas()
        if aviso:
            centrado(p, fuente24(), aviso, cx, 490, w - 30, ROJO, interlineado=27, maximo=2)
        else:
            ajustado(p, self.f.normal, "¡Tienes las herramientas!", cx, 515, w - 30, VERDE)
        self.b_excavar.dibujar(p, self.f.grande)

    @staticmethod
    def _lineas(fuente, texto, ancho):
        lineas, actual = [], ""
        for palabra in texto.split():
            prueba = (actual + " " + palabra).strip()
            if fuente.size(prueba)[0] > ancho and actual:
                lineas.append(actual)
                actual = palabra
            else:
                actual = prueba
        if actual:
            lineas.append(actual)
        return lineas

    def _zona_dormida(self, p, x0, w, cx):
        per = self.perfil
        seg = fd.segundos_para_zona(per)
        ajustado(p, self.f.normal, "Sin zona por ahora", cx, 128, w - 24, TINTA_SUAVE)
        arte.dibujar_carrito(p, cx, 225, 1.8, self.t, False)
        if seg is None:
            ajustado(p, self.f.grande, "¡Lo completaste todo!", cx, 335, w - 30, VERDE)
            centrado(p, self.f.normal, "Ya hallaste y reviviste todos los dinosaurios. ¡Eres un gran paleontólogo!",
                     cx, 372, w - 50, TINTA, interlineado=34, maximo=4)
            return
        ajustado(p, self.f.grande, f"Próxima zona en {_mmss(seg)}", cx, 335, w - 30, TINTA)
        centrado(p, self.f.normal, "El carrito está buscando un buen lugar para excavar.", cx, 368, w - 60,
                 TINTA_SUAVE, interlineado=34, maximo=3)
        dino = fd.siguiente_dino(per)
        if dino:
            ajustado(p, self.f.normal, f"Buscaremos: {arte.DINOS[dino][0]}", cx, 515, w - 30, (140, 70, 20))
        centrado(p, self.f.chica, "Mientras esperas, ¡craftea herramientas en el Taller!", cx, 548, w - 50,
                 TINTA_SUAVE, interlineado=24, maximo=2)


# =====================================================================
#  TALLER
# =====================================================================
class TallerEscena(_Base):
    X_DET, W_DET = 880, 376

    def __init__(self, app, volver=None):
        super().__init__(app)
        self.volver_a = volver
        self.tipo = fd.TIPOS_HERR[0]
        self.vista = "recetas"
        self.est = 1
        self.pagina = 0
        self.craft = None            # animacion en curso
        self.cartel = None           # "¡Nueva herramienta!"
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.tabs = {t: BotonF((24 + i * 192, 14, 184, 66), fd.NOMBRES_HERR[t], COLOR_HERR[t])
                     for i, t in enumerate(fd.TIPOS_HERR)}
        self.b_vista = BotonF((802, 14, 236, 66), "Mis herramientas", (150, 110, 200))
        self.b_filas = [Boton((24, 160 + i * 92, 842, 84), "", (200, 160, 100)) for i in range(5)]
        self.b_comprar = [BotonF((self.X_DET + self.W_DET - 142, 284 + i * 46 - 21, 130, 42), "Comprar", (235, 150, 60))
                          for i in range(5)]
        self.b_todo = BotonF((self.X_DET + 8, 494, self.W_DET - 16, 46), "Comprar lo que falta", (235, 150, 60))
        self.b_craftear = BotonF((self.X_DET + 8, 548, self.W_DET - 16, 78), "CRAFTEAR", (80, 180, 90))
        self.b_equipar = [BotonF((706, 160 + i * 66 + 6, 156, 48), "Equipar", (60, 160, 190))
                          for i in range(POR_PAGINA_MIAS)]
        self.b_ant = BotonF((210, ALTO - 78, 150, 56), "< Antes", (70, 150, 230))
        self.b_sig = BotonF((370, ALTO - 78, 150, 56), "Más >", (70, 150, 230))
        self.b_cancelar = BotonF((540, 566, 200, 48), "Cancelar", (150, 150, 170))
        self.b_genial = BotonF((520, 520, 240, 70), "¡Genial!", (80, 180, 90))

    # ------------------------------------------------------------ datos
    def mats(self):
        r = fd.receta_herramienta(self.tipo, self.est)
        return [(m, r[m]) for m in ORDEN_MAT if m in r]

    def faltan(self):
        per = self.perfil
        return [(m, n - per.cantidad(m)) for m, n in self.mats() if per.cantidad(m) < n]

    def costo_faltan(self):
        """(costo de lo que se puede comprar, hay algo que no se vende)."""
        costo, no_vende = 0, False
        for m, f in self.faltan():
            if fd.se_vende(m):
                costo += fd.MATERIALES[m][2] * f
            else:
                no_vende = True
        return costo, no_vende

    def lista_mias(self):
        per = self.perfil
        act = fd.herramienta_activa(per, self.tipo)
        hs = sorted(fd.herramientas(per, self.tipo), key=lambda h: (-(act is not None and h["id"] == act["id"]),
                                                                   -h["est"], -h["dur"], h["id"]))
        return hs, act

    def total_paginas(self):
        return max(1, math.ceil(len(self.lista_mias()[0]) / POR_PAGINA_MIAS))

    # ------------------------------------------------------------ acciones
    def _tab(self, tipo):
        if tipo != self.tipo:
            self.tipo = tipo
            self.pagina = 0
            self.snd.reproducir("click")

    def _cambiar_vista(self):
        self.vista = "mias" if self.vista == "recetas" else "recetas"
        self.pagina = 0
        self.snd.reproducir("click")

    def _elegir_est(self, est):
        if est != self.est:
            self.est = est
            self.snd.reproducir("click")

    def _comprar_uno(self, mat, n):
        per = self.perfil
        costo = fd.MATERIALES[mat][2] * n
        if per.monedas < costo:
            self.snd.reproducir("error")
            self.decir(f"Te faltan {costo - per.monedas} monedas. ¡Juega para ganar más!", ROJO)
            return False
        if fd.comprar_material(per, mat, n):
            per.guardar()
            self.snd.reproducir("moneda")
            self.decir(f"¡Compraste {n} de {catalogo.nombre_item(mat).lower()}!", VERDE)
            self._celebrar(self.X_DET + 190, 300, f"+{n}")
            return True
        return False

    def _comprar_todo(self):
        per = self.perfil
        costo, _ = self.costo_faltan()
        if costo <= 0:
            return
        if per.monedas < costo:
            self.snd.reproducir("error")
            self.decir(f"Te faltan {costo - per.monedas} monedas. ¡Juega para ganar más!", ROJO)
            return
        for m, f in self.faltan():
            if fd.se_vende(m):
                fd.comprar_material(per, m, f)
        per.guardar()
        self.snd.reproducir("moneda")
        self.decir("¡Compraste lo que faltaba!", VERDE)
        self._celebrar(self.X_DET + 190, 480, "¡Listo!")

    def _empezar_craft(self):
        per = self.perfil
        if not fd.puede_craftear(per, self.tipo, self.est):
            self.snd.reproducir("error")
            self.decir("Todavía faltan materiales. ¡Compra lo básico o busca acero y cuarzo excavando!", ROJO)
            return
        self.snd.reproducir("click")
        self.craft = dict(tipo=self.tipo, est=self.est, prog=0.0, t=0.0, golpe_t=0.0, dentro=False,
                          bonus=0.0, hits=0)
        self.cartel = None

    def zona_pos(self, t=None):
        """Centro de la zona brillante que hay que seguir (se mueve despacio sobre la pieza)."""
        t = self.craft["t"] if t is None and self.craft else (t or 0.0)
        return (640 + 200 * math.sin(0.9 * t), 330 + 55 * math.sin(1.7 * t + 1.0))

    R_ZONA = 100

    def _actualizar_craft(self, dt, ctrl):
        c = self.craft
        if self.b_cancelar.actualizar(dt, ctrl):
            self.craft = None
            self.snd.reproducir("click")
            self.decir("Cancelado: no gastaste nada.", TINTA_SUAVE)
            return
        c["t"] += dt
        zx, zy = self.zona_pos()
        d = math.hypot(ctrl.pos.x - zx, ctrl.pos.y - zy)
        dentro = d < self.R_ZONA
        c["dentro"] = dentro
        seg = fd.segundos_crafteo(c["est"])
        c["golpe_t"] = max(0.0, c["golpe_t"] - dt)
        trabajo = ctrl.vel > 120 or ctrl.golpe or ctrl.clic
        if dentro:
            c["prog"] += dt / seg
            if trabajo:
                if random.random() < min(1.0, dt * 22):
                    self.particulas.append(Particula(ctrl.pos.x, ctrl.pos.y, random.choice(
                        [(255, 210, 80), (255, 160, 50), (255, 245, 170)]), 90, 320, 0.55, 700, 4))
                if c["golpe_t"] <= 0:
                    c["golpe_t"] = 0.42
                    self.snd.reproducir("golpe")
        if (ctrl.golpe or ctrl.clic) and dentro:
            c["prog"] += 0.25 / seg
            explosion(self.particulas, ctrl.pos.x, ctrl.pos.y, (255, 220, 100), n=12, vida=0.6)
        marca = int(c["prog"] * c["est"] * 2)
        if marca > c["hits"]:
            c["hits"] = marca
            self.snd.reproducir("pop")
        if c["prog"] >= 1.0:
            self._terminar_craft()

    def _terminar_craft(self):
        per = self.perfil
        c, self.craft = self.craft, None
        tipo, est = c["tipo"], c["est"]
        act = fd.herramienta_activa(per, tipo)
        h = fd.craftear(per, tipo, est)
        if h is None:
            self.snd.reproducir("error")
            self.decir("Ay, faltaron materiales. ¡Prueba otra vez!", ROJO)
            return
        puesta = act is None or est >= act["est"]
        if puesta:
            fd.equipar(per, h["id"])
        per.guardar()
        self.snd.reproducir("ok")
        self.snd.reproducir("premio")
        self.cartel = dict(h=h, tipo=tipo, est=est, puesta=puesta, t=0.0)
        explosion(self.particulas, 640, 300, (255, 215, 60), n=40, vida=1.1)

    def _equipar(self, h):
        per = self.perfil
        if fd.equipar(per, h["id"]):
            per.guardar()
            self.snd.reproducir("ok")
            self.decir(f"¡Listo! Usas {NOMBRE_MIN[h['tipo']]} de {_estrellas_txt(h['est'])}.", VERDE)
        else:
            self.snd.reproducir("error")

    def _salir(self):
        self.snd.reproducir("click")
        v = self.volver_a
        if v is None:
            self.app.ir(ExpedicionEscena(self.app))
        elif isinstance(v, Escena):
            self.app.ir(v)
        elif callable(v):
            r = v()
            if isinstance(r, Escena):
                self.app.ir(r)
        else:
            self.app.ir(ExpedicionEscena(self.app))

    def tecla_esc(self):
        if self.craft:
            self.craft = None
        elif self.cartel:
            self.cartel = None
        else:
            self._salir()

    # ------------------------------------------------------------ bucle
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self._efectos(dt)
        if self.cartel:
            self.cartel["t"] += dt
            if self.b_genial.actualizar(dt, ctrl) or self.cartel["t"] > 8.0:
                self.cartel = None
                self.snd.reproducir("click")
            return
        if self.craft:
            self._actualizar_craft(dt, ctrl)
            return
        if self.volver.actualizar(dt, ctrl):
            self._salir()
            return
        for t, b in self.tabs.items():
            if b.actualizar(dt, ctrl):
                self._tab(t)
        if self.b_vista.actualizar(dt, ctrl):
            self._cambiar_vista()
        if self.vista == "recetas":
            self._actualizar_recetas(dt, ctrl)
        else:
            self._actualizar_mias(dt, ctrl)

    def _actualizar_recetas(self, dt, ctrl):
        per = self.perfil
        for i, b in enumerate(self.b_filas):
            if b.actualizar(dt, ctrl):
                self._elegir_est(i + 1)
        falt = dict(self.faltan())
        mats = self.mats()
        for i, b in enumerate(self.b_comprar):
            if i < len(mats) and mats[i][0] in falt and fd.se_vende(mats[i][0]):
                b.activo = True
                if b.actualizar(dt, ctrl):
                    self._comprar_uno(mats[i][0], falt[mats[i][0]])
            else:
                b.activo = False
        costo, _ = self.costo_faltan()
        self.b_todo.activo = costo > 0 and per.monedas >= costo
        if costo > 0 and self.b_todo.actualizar(dt, ctrl):
            self._comprar_todo()
        self.b_craftear.activo = fd.puede_craftear(per, self.tipo, self.est)
        if self.b_craftear.actualizar(dt, ctrl):
            self._empezar_craft()

    def _actualizar_mias(self, dt, ctrl):
        hs, act = self.lista_mias()
        total = self.total_paginas()
        self.pagina = max(0, min(self.pagina, total - 1))
        vis = hs[self.pagina * POR_PAGINA_MIAS:(self.pagina + 1) * POR_PAGINA_MIAS]
        for i, b in enumerate(self.b_equipar):
            if i < len(vis) and not (act and vis[i]["id"] == act["id"]):
                b.activo = True
                if b.actualizar(dt, ctrl):
                    self._equipar(vis[i])
            else:
                b.activo = False
        if total > 1:
            self.b_ant.activo = self.pagina > 0
            self.b_sig.activo = self.pagina < total - 1
            if self.b_ant.actualizar(dt, ctrl):
                self.pagina -= 1
                self.snd.reproducir("click")
            if self.b_sig.actualizar(dt, ctrl):
                self.pagina += 1
                self.snd.reproducir("click")

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        fondo(p, (206, 214, 226), (150, 160, 180))
        self._cabecera(p)
        for t, b in self.tabs.items():
            sel = t == self.tipo
            b.color = COLOR_HERR[t] if sel else (150, 140, 130)
            b.dibujar(p, self.f.normal)
            if sel:
                pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(10, 10), 5, border_radius=26)
        self.b_vista.texto = "Recetas" if self.vista == "mias" else "Mis herramientas"
        self.b_vista.dibujar(p, self.f.normal)
        panel(p, (1050, 14, 206, 66), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        moneda(p, 1080, 47, 17)
        ajustado(p, self.f.grande, f"{self.perfil.monedas:,}".replace(",", "."), 1106, 47, 140, TINTA, ancla="izq")
        self._barra_materiales(p)
        if self.vista == "recetas":
            self._dibujar_recetas(p)
            defecto = ("¡Tienes todo! Pulsa CRAFTEAR." if fd.puede_craftear(self.perfil, self.tipo, self.est)
                       else "Faltan materiales: cómpralos con monedas o búscalos excavando.")
        else:
            self._dibujar_mias(p)
            defecto = "La herramienta equipada es la que usas al excavar."
        self.volver.dibujar(p, self.f.normal)
        if self.vista == "mias" and self.total_paginas() > 1:
            self.b_ant.dibujar(p, self.f.normal)
            self.b_sig.dibujar(p, self.f.normal)
            self._barra_mensaje(p, 530, 400, defecto)
        else:
            self._barra_mensaje(p, 210, 650, defecto)
        self._dibujar_efectos(p)
        if self.craft:
            self._dibujar_craft(p)
        if self.cartel:
            self._dibujar_cartel(p)

    def _barra_materiales(self, p):
        per = self.perfil
        panel(p, (24, 102, 1232, 50), color=PAPEL, alfa=235, radio=16, borde=(110, 120, 140))
        w = 1232 / len(ORDEN_MAT)
        for k, m in enumerate(ORDEN_MAT):
            x = 24 + k * w
            dibujar_item(p, m, x + 32, 127, 34)
            ajustado(p, self.f.normal, f"{catalogo.nombre_item(m)}  {per.cantidad(m)}", x + 56, 127, w - 64, TINTA,
                     ancla="izq")

    # ---- recetas
    def _dibujar_recetas(self, p):
        per = self.perfil
        for i, b in enumerate(self.b_filas):
            est = i + 1
            r = b.rect
            sel = est == self.est
            r_mats = fd.receta_herramienta(self.tipo, est)
            puede = all(per.cantidad(m) >= n for m, n in r_mats.items())
            tarjeta(p, r, COLOR_HERR[self.tipo] if sel else (150, 140, 130),
                    aclarar(PAPEL, 0.4) if b.encima else PAPEL, radio=16)
            if sel:
                pygame.draw.rect(p, (255, 235, 120), r.inflate(8, 8), 4, border_radius=20)
            arte.dibujar_herramienta(p, self.tipo, r.x + 60, r.centery - 6, 0.62, est)
            ajustado(p, self.f.chica, _estrellas_txt(est), r.x + 60, r.bottom - 10, 100, TINTA_SUAVE)
            for k, m in enumerate(ORDEN_MAT):
                if m not in r_mats:
                    continue
                n = r_mats[m]
                idx = [mm for mm in ORDEN_MAT if mm in r_mats].index(m)
                x = r.x + 126 + idx * 122
                dibujar_item(p, m, x + 22, r.centery, 38)
                tengo = per.cantidad(m)
                ajustado(p, self.f.normal, f"{tengo} / {n}", x + 46, r.centery, 70, VERDE if tengo >= n else ROJO,
                         ancla="izq")
            if puede:
                ajustado(p, self.f.chica, "¡Listo!", r.right - 12, r.centery, 70, VERDE, ancla="der")
        self._dibujar_detalle(p)

    def _dibujar_detalle(self, p):
        per = self.perfil
        x, w = self.X_DET, self.W_DET
        panel(p, (x, 160, w, 472), color=PAPEL, alfa=245, radio=22, borde=(90, 100, 130))
        arte.dibujar_herramienta(p, self.tipo, x + 66, 206, 0.8, self.est)
        ajustado(p, self.f.normal, fd.NOMBRES_HERR[self.tipo], x + 130, 188, w - 140, TINTA, ancla="izq")
        ajustado(p, self.f.normal, _estrellas_txt(self.est), x + 130, 222, w - 140, (200, 140, 20), ancla="izq")
        ajustado(p, self.f.chica, "Materiales que necesitas:", x + 14, 244, w - 20, TINTA_SUAVE, ancla="izq")
        mats = self.mats()
        falt = dict(self.faltan())
        for i, (m, n) in enumerate(mats):
            cy = 284 + i * 46
            tengo = per.cantidad(m)
            dibujar_item(p, m, x + 30, cy, 36)
            ajustado(p, self.f.normal, f"{tengo} / {n}", x + 54, cy, 84, VERDE if tengo >= n else ROJO,
                     ancla="izq")
            ajustado(p, self.f.chica, catalogo.nombre_item(m), x + 142, cy, 92, TINTA, ancla="izq")
            if m in falt:
                if fd.se_vende(m):
                    precio = fd.MATERIALES[m][2] * falt[m]
                    b = self.b_comprar[i]
                    b.texto = f"Comprar {precio}"
                    b.color = (235, 150, 60) if per.monedas >= precio else (190, 160, 130)
                    b.dibujar(p, self.f.normal)
                else:
                    ajustado(p, self.f.chica, "Solo excavando", x + w - 14, cy, 130, TINTA_SUAVE, ancla="der")
        costo, no_vende = self.costo_faltan()
        if costo > 0:
            self.b_todo.texto = f"Comprar lo que falta: {costo}"
            self.b_todo.dibujar(p, self.f.normal)
        self.b_craftear.dibujar(p, self.f.grande)

    # ---- mis herramientas
    def _dibujar_mias(self, p):
        hs, act = self.lista_mias()
        total = self.total_paginas()
        self.pagina = max(0, min(self.pagina, total - 1))
        vis = hs[self.pagina * POR_PAGINA_MIAS:(self.pagina + 1) * POR_PAGINA_MIAS]
        if not hs:
            r = pygame.Rect(24, 160, 842, 150)
            panel(p, r, color=PAPEL, alfa=240, radio=22, borde=(110, 120, 140))
            ajustado(p, self.f.grande, f"No tienes {NOMBRE_MIN[self.tipo]}", r.centerx, r.y + 56, r.width - 40, TINTA)
            ajustado(p, self.f.normal, "¡Craftea uno en Recetas!", r.centerx, r.y + 106, r.width - 40, TINTA_SUAVE)
        for i, h in enumerate(vis):
            r = pygame.Rect(24, 160 + i * 66, 842, 60)
            puesta = act is not None and h["id"] == act["id"]
            tarjeta(p, r, (90, 190, 110) if puesta else (150, 140, 130), PAPEL, radio=14)
            arte.dibujar_herramienta(p, h["tipo"], r.x + 46, r.centery - 2, 0.5, 0)
            estrellitas(p, r.x + 170, r.centery, h["est"], 5, r=9, sep=21, encendidas=h["est"])
            f = h["dur"] / fd.DURABILIDAD[h["est"]]
            barra(p, (r.x + 300, r.centery - 13, 260, 26), f, color=color_dur(f))
            ajustado(p, self.f.normal, f"{int(math.ceil(f * 100))}%", r.x + 576, r.centery, 80, TINTA, ancla="izq")
            if puesta:
                ajustado(p, self.f.normal, "¡Equipada!", r.right - 90, r.centery, 150, VERDE)
            else:
                self.b_equipar[i].dibujar(p, self.f.normal)
        x, w = self.X_DET, self.W_DET
        panel(p, (x, 160, w, 472), color=PAPEL, alfa=245, radio=22, borde=(90, 100, 130))
        arte.dibujar_herramienta(p, self.tipo, x + w / 2, 240, 1.3, 0)
        ajustado(p, self.f.grande, fd.NOMBRES_HERR[self.tipo], x + w / 2, 330, w - 30, TINTA)
        yy = centrado(p, self.f.normal, EXPLICA_HERR[self.tipo], x + w / 2, 362, w - 40, TINTA_SUAVE,
                      interlineado=34, maximo=3)
        centrado(p, self.f.normal, "Si se gasta del todo, se rompe: ¡craftea otra!", x + w / 2, yy + 14, w - 40,
                 (140, 70, 20), interlineado=34, maximo=3)

    # ---- animacion de crafteo
    def _dibujar_craft(self, p):
        c = self.craft
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((20, 20, 40, 150))
        p.blit(velo, (0, 0))
        r = pygame.Rect(180, 96, 920, 528)
        panel(p, r, color=(60, 52, 60), alfa=250, radio=28, borde=(255, 220, 120))
        tipo, est = c["tipo"], c["est"]
        ajustado(p, self.f.grande, f"Crafteando: {fd.NOMBRES_HERR[tipo]}", 640, 134, 800, (255, 240, 200),
                 contorno=(30, 20, 20))
        estrellitas(p, 640, 176, est, est, r=14, sep=34, encendidas=min(est, int(c["prog"] * est + 0.001)))
        # calor y yunque
        calor = int(40 + 180 * c["prog"])
        glow = pygame.Surface((420, 300), pygame.SRCALPHA)
        for k in range(6, 0, -1):
            pygame.draw.ellipse(glow, (255, 140, 40, int(calor / 6)), (210 - 34 * k, 150 - 24 * k, 68 * k, 48 * k))
        p.blit(glow, (430, 175))
        pygame.draw.polygon(p, (70, 74, 90), [(430, 450), (850, 450), (800, 400), (480, 400)])
        pygame.draw.rect(p, (90, 94, 112), (470, 380, 340, 30), border_radius=8)
        pygame.draw.rect(p, (60, 62, 78), (590, 450, 100, 56))
        pygame.draw.rect(p, (60, 62, 78), (540, 500, 200, 18), border_radius=6)
        mov = c["dentro"]
        ang = 28 + (16 * math.sin(c["t"] * 16) if mov else 0)
        arte.dibujar_herramienta(p, tipo, 640, 330, 2.2, 0, ang)
        # zona brillante
        zx, zy = self.zona_pos()
        pulso = 0.5 + 0.5 * math.sin(c["t"] * 5)
        zs = pygame.Surface((2 * self.R_ZONA + 10, 2 * self.R_ZONA + 10), pygame.SRCALPHA)
        cc = self.R_ZONA + 5
        col = (120, 255, 150) if c["dentro"] else (255, 230, 90)
        pygame.draw.circle(zs, (*col, int(50 + 40 * pulso)), (cc, cc), self.R_ZONA)
        pygame.draw.circle(zs, (*col, 220), (cc, cc), self.R_ZONA, 6)
        pygame.draw.circle(zs, (*col, 220), (cc, cc), int(self.R_ZONA * (0.3 + 0.2 * pulso)), 4)
        p.blit(zs, (zx - cc, zy - cc))
        # textos y barra
        ajustado(p, self.f.normal, "¡Mueve el cursor sobre la luz!" if not c["dentro"] else "¡Muy bien, sigue así!",
                 640, 232, 760, (255, 240, 180) if not c["dentro"] else (160, 255, 170), contorno=(30, 20, 20))
        barra(p, (300, 526, 680, 30), c["prog"], color=(255, 170, 50), color_fondo=(40, 36, 44), borde=(255, 255, 255))
        ajustado(p, self.f.chica, f"{int(min(1.0, c['prog']) * 100)}%", 640, 541, 80, (255, 255, 255),
                 contorno=(30, 20, 20))
        self.b_cancelar.dibujar(p, self.f.normal)

    def _dibujar_cartel(self, p):
        k = self.cartel
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((20, 20, 40, 150))
        p.blit(velo, (0, 0))
        r = pygame.Rect(300, 100, 680, 520)
        panel(p, r, color=(255, 248, 226), alfa=252, radio=30, borde=(255, 190, 40))
        escala = 1.0 + 0.06 * math.sin(self.t * 6)
        for i in range(12):
            a = self.t * 0.8 + i * math.pi / 6
            pygame.draw.line(p, (255, 230, 140), (640 + 90 * math.cos(a), 300 + 90 * math.sin(a)),
                             (640 + 190 * math.cos(a), 300 + 190 * math.sin(a)), 5)
        ajustado(p, self.f.grande, "¡Nueva herramienta!", 640, 150, 620, (200, 110, 20))
        arte.dibujar_herramienta(p, k["tipo"], 640, 290, 2.4 * escala, 0)
        estrellitas(p, 640, 392, k["est"], k["est"], r=15, sep=36, encendidas=k["est"])
        ajustado(p, self.f.normal, f"{fd.NOMBRES_HERR[k['tipo']]} de {_estrellas_txt(k['est'])}", 640, 440, 620, TINTA)
        ajustado(p, self.f.normal, "¡Ya la estás usando!" if k["puesta"] else "Equípala en Mis herramientas.",
                 640, 478, 620, VERDE if k["puesta"] else TINTA_SUAVE)
        self.b_genial.dibujar(p, self.f.grande)
