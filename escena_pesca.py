"""Escenas de Pesca por mundos: la EXPEDICION DE PESCA (hub) y el TALLER de cana, cuerda y anzuelo.

PescaEscena(app)         5 mundos (candado / llave / progreso), los 6 peces objetivo del mundo elegido
                         (silueta hasta pescarlos, ficha al tocarlos), equipo activo con estrellas y
                         durabilidad, aviso si el equipo no alcanza y el boton grande "A pescar".
TallerEscena(app, volver) crafteo de cana, cuerda y anzuelo (1 a 5 estrellas), compra de materiales basicos,
                         equipar y ver la durabilidad. El crafteo avanza solo con el cursor dentro del circulo
                         verde, igual que en el taller de Fosiles.

Todo se maneja con el cursor (Boton con permanencia), con textos grandes y sin castigos. La logica vive en
pesca_datos; el dibujo de peces, fondos y herramientas, en arte / arte_mar.
"""

import math
import random

import pygame

import arte
import arte_mar
import catalogo
import pesca_datos as pd
from ajustes import ANCHO, ALTO
from escena import Escena
from escena_fosiles import (_Base, tarjeta, centrado, estrellitas, color_dur, dibujar_candado, dibujar_llave,
                            _estrellas_txt, _plural, ROJO, VERDE, ORO)
from escena_items import BotonF, TINTA, TINTA_SUAVE, PAPEL, ajustado, moneda
from nucleo import (Boton, Particula, aclarar, barra, escribir, estrella, explosion, fondo, oscurecer, panel)

COLOR_HERR = {"cana": (200, 150, 70), "cuerda": (90, 170, 210), "anzuelo": (150, 150, 175)}
NOMBRE_MIN = {"cana": "caña", "cuerda": "cuerda", "anzuelo": "anzuelo"}
ARTICULO = {"cana": "una", "cuerda": "una", "anzuelo": "un"}
EXPLICA_HERR = {
    "cana": "La caña da fuerza para enrollar cuando el pez tira.",
    "cuerda": "La cuerda aguanta la tensión sin romperse.",
    "anzuelo": "El anzuelo se clava bien y el pez no se suelta.",
}
ORDEN_MAT = ["bambu", "hilo", "alambre", "alga", "escama", "perla", "marfil", "luz_abisal", "escama_dragon"]
POR_PAGINA_MIAS = 7
AZUL_MAR = (30, 90, 140)

# tamano y dato curioso de los 30 peces objetivo: id -> (tamano, dato)
FICHAS = {
    "sardina": ("15 a 25 cm", "Nada en grupos enormes que brillan como la plata."),
    "perca": ("20 a 40 cm", "Tiene rayas oscuras y una aleta con espinas."),
    "trucha": ("30 a 60 cm", "Le gustan los ríos de agua fría y limpia."),
    "carpa": ("40 a 80 cm", "Puede vivir más de 40 años."),
    "bagre": ("50 cm a 1 metro", "Usa sus bigotes para encontrar comida en el fondo."),
    "esturion": ("Hasta 2 metros", "Es un pez muy antiguo: ya existía con los dinosaurios."),
    "payaso": ("8 a 11 cm", "Vive entre los tentáculos de la anémona sin que lo piquen."),
    "globo": ("20 a 40 cm", "Se infla como un balón cuando se asusta."),
    "caballito": ("5 a 15 cm", "El papá lleva los huevitos en una bolsa."),
    "pezangel": ("15 a 30 cm", "Sus colores brillantes lo hacen reconocible en el arrecife."),
    "mantarraya": ("2 a 5 metros", "Parece que vuela bajo el agua moviendo sus aletas."),
    "tortuga": ("Hasta 1 metro", "Vuelve a la playa donde nació para poner sus huevos."),
    "atun": ("1 a 2 metros", "Nada muy rápido y casi nunca se detiene."),
    "bacalao": ("Hasta 1 metro", "Tiene un pequeño bigote debajo de la boca."),
    "beluga": ("4 a 5 metros", "Es la ballena blanca que silba y 'canta'."),
    "narval": ("4 a 5 metros", "Su largo colmillo es un diente retorcido."),
    "cachalote": ("Hasta 16 metros", "Se sumerge muy hondo y aguanta mucho sin respirar."),
    "orca": ("6 a 8 metros", "Es el delfín más grande y vive en familia."),
    "pezlinterna": ("Hasta 15 cm", "Tiene lucecitas en la panza para brillar en lo oscuro."),
    "pezvibora": ("Hasta 35 cm", "Sus dientes son tan largos que casi no le caben en la boca."),
    "pezhacha": ("3 a 6 cm", "Es plateado y tiene ojos grandes que miran hacia arriba."),
    "pezpescador": ("Hasta 1 metro", "Lleva un farolito en la frente para atraer a otros peces."),
    "anguila": ("1 a 2 metros", "Es larga como una serpiente y se esconde en las cuevas."),
    "pulpogigante": ("Hasta 5 metros", "Tiene tres corazones y brazos con muchas ventosas."),
    "celacanto": ("Hasta 2 metros", "Creían que ya no existía, ¡y apareció vivo en el mar!"),
    "megalodon": ("15 metros o más", "Fue el tiburón más grande que existió."),
    "serpiente": ("Hasta 20 metros", "Los marineros de antes contaban historias sobre ella."),
    "dragonmar": ("Hasta 12 metros", "Un dragón del mar que guarda tesoros en el fondo."),
    "kraken": ("Grande como un barco", "Cuentan que sus brazos podían abrazar un barco entero."),
    "leviatan": ("Más grande que una ballena", "Es el monstruo más antiguo de las leyendas del mar."),
}


NOMBRE_CORTO = {"hilo": "Hilo", "escama": "Escama", "perla": "Perla", "marfil": "Marfil",
                "luz_abisal": "Luz abisal", "escama_dragon": "Esc. dragón"}


def nombre_mat(m):
    return NOMBRE_CORTO.get(m) or catalogo.nombre_item(m)


def corto_mundo(i):
    return pd.MUNDOS[i]["nombre"].replace("Mundo ", "")


def nombre_pez(sp):
    return arte.PECES[sp][0]


def donde_vive(sp):
    """Texto de los mundos donde vive y a que profundidad."""
    d = arte.PECES[sp]
    mundos = [pd.MUNDOS[m - 1]["nombre"] for m in d[9] if 1 <= m <= pd.NUM_MUNDOS]
    medio = (d[10][0] + d[10][1]) / 2
    nivel = "cerca de la superficie" if medio < 110 else "a media agua" if medio < 230 else "en lo hondo"
    return " y ".join(mundos) if len(mundos) <= 2 else ", ".join(mundos[:-1]) + " y " + mundos[-1], nivel


def escala_pez(sp):
    """Escala para que las especies enormes quepan en su tarjeta."""
    t = arte.PECES[sp][8]
    return 0.6 if t < 250 else 0.45 if t < 450 else 0.34


def icono_material(p, m, x, y, tam=40):
    """Icono de un material (dibujo de pesca si existe; si no, el del catalogo)."""
    fn = getattr(arte_mar, "dibujar_material_pesca", None)
    propios = getattr(arte_mar, "_MATERIALES_ICONO", {})
    if fn is not None and m in propios:
        try:
            fn(p, m, x, y, tam / 48.0)
            return
        except Exception:
            pass
    catalogo.dibujar_item(p, m, x, y, tam)


def herramienta(p, tipo, x, y, escala, est):
    arte_mar.dibujar_herramienta_pesca(p, tipo, x, y, escala, est)


_mini = {}


def miniatura_fondo(i, tam):
    """Fondo del mundo i (0..4) reducido a 'tam' (se guarda para no recalcular)."""
    clave = (i, tam)
    if clave not in _mini:
        try:
            bg = arte_mar.fondo_mundo(i + 1)[0]
        except Exception:
            bg = pygame.Surface((ANCHO, ALTO))
            bg.fill(pd.MUNDOS[i]["color"])
        _mini[clave] = pygame.transform.smoothscale(bg, tam)
    return _mini[clave]


def _pegar_redondeado(p, img, rect, radio):
    """Dibuja img (del tamano de rect) con las esquinas redondeadas."""
    r = pygame.Rect(rect)
    mask = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radio)
    s = img.copy().convert_alpha()
    s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    p.blit(s, r.topleft)


# =====================================================================
#  HUB: EXPEDICION DE PESCA
# =====================================================================
class PescaEscena(_Base):
    X_PECES, W_TARJ, H_TARJ = 24, 282, 142
    X_EQ, W_EQ = 900, 356

    def __init__(self, app):
        super().__init__(app)
        per = self.perfil
        self.vista = pd.mundo_actual(per)
        self.ficha = None                    # especie cuya ficha se ve
        self.t_ficha = 0.0
        self.b_mundos = [Boton((24 + i * 248, 102, 238, 108), "", pd.MUNDOS[i]["color"])
                         for i in range(pd.NUM_MUNDOS)]
        self.b_peces = [Boton((self.X_PECES + (k % 3) * (self.W_TARJ + 8), 250 + (k // 3) * (self.H_TARJ + 8),
                               self.W_TARJ, self.H_TARJ), "", (200, 170, 110)) for k in range(6)]
        self.volver = BotonF((24, 632, 170, 72), "Volver", (150, 150, 170))
        self.b_taller = BotonF((210, 632, 250, 72), "Taller", (60, 160, 190))
        self.b_pescar = BotonF((480, 632, 776, 72), "¡A pescar!", (60, 170, 90))
        self.b_cerrar = BotonF((520, 528, 240, 66), "¡Listo!", (80, 180, 90))

    # ------------------------------------------------------------ datos
    def abierto(self, i=None):
        return pd.mundo_abierto(self.perfil, self.vista if i is None else i)

    def objetivos(self):
        return pd.objetivos(self.vista)

    def estado_pesca(self):
        """(ok, motivo) de pescar en el mundo que se mira."""
        return pd.puede_pescar(self.perfil, self.vista)

    def aviso(self):
        """Texto claro si no se puede pescar en el mundo visto; None si se puede."""
        per = self.perfil
        ok, motivo = self.estado_pesca()
        if ok:
            return None
        i = self.vista
        if motivo == "cerrado":
            return f"Para abrir este mundo, pesca los 6 peces de {pd.MUNDOS[i - 1]['nombre']}."
        falta = pd.faltan_estrellas(per, i)
        req = pd.estrellas_requeridas(i)
        nombres = [NOMBRE_MIN[t] for t in pd.TIPOS_HERR if t in falta]
        lista = nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
        return (f"Este mundo pide caña, cuerda y anzuelo de {_estrellas_txt(req)}. "
                f"Te falta: {lista}. ¡Craftea en el Taller!")

    def texto_defecto(self):
        av = self.aviso()
        if av:
            return av, ROJO
        i = self.vista
        pend = pd.objetivos_pendientes(self.perfil, i)
        if pend:
            return f"¡Listo para pescar! Aún faltan {_plural(len(pend), 'pez', 'peces')} por registrar.", TINTA
        return "¡Registraste todos los peces de este mundo! Sigue pescando para ganar premios.", VERDE

    # ------------------------------------------------------------ acciones
    def _elegir_mundo(self, i):
        per = self.perfil
        self.vista = i
        self.snd.reproducir("click")
        if pd.elegir_mundo(per, i):
            per.guardar()
            self.decir(f"¡Ahora pescas en {pd.MUNDOS[i]['nombre']}!", VERDE)
        else:
            self.decir("Todavía no tienes la llave de ese mundo.", TINTA_SUAVE)

    def _abrir_ficha(self, sp):
        self.ficha = sp
        self.t_ficha = 0.0
        self.snd.reproducir("click")

    def _cerrar_ficha(self):
        self.ficha = None
        self.snd.reproducir("click")
        for b in self.b_peces:
            b.espera = 0.5
            b.dwell = 0.0

    def _pescar(self):
        from aventura import Partida          # import perezoso: aventura importa este modulo
        ok, _ = self.estado_pesca()
        if not ok:
            self.snd.reproducir("error")
            return
        pd.elegir_mundo(self.perfil, self.vista)
        self.perfil.guardar()
        self.snd.reproducir("click")
        self.app.ir(Partida(self.app, "pesca", 1))

    def _ir_taller(self):
        self.snd.reproducir("click")
        self.app.ir(TallerEscena(self.app))

    def _salir(self):
        from aventura import Libre
        self.snd.reproducir("click")
        self.app.ir(Libre(self.app))

    def tecla_esc(self):
        if self.ficha:
            self._cerrar_ficha()
        else:
            self._salir()

    # ------------------------------------------------------------ bucle
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self._efectos(dt)
        if self.ficha:
            self.t_ficha += dt
            if self.b_cerrar.actualizar(dt, ctrl) or self.t_ficha > 20.0:
                self._cerrar_ficha()
            return
        if self.volver.actualizar(dt, ctrl):
            self._salir()
            return
        if self.b_taller.actualizar(dt, ctrl):
            self._ir_taller()
            return
        ok, _ = self.estado_pesca()
        self.b_pescar.activo = ok
        if self.b_pescar.actualizar(dt, ctrl):
            self._pescar()
            return
        for i, b in enumerate(self.b_mundos):
            if b.actualizar(dt, ctrl):
                self._elegir_mundo(i)
        obj = self.objetivos()
        abierto = self.abierto()
        for k, b in enumerate(self.b_peces):
            b.activo = abierto and k < len(obj)
            if b.actualizar(dt, ctrl):
                self._abrir_ficha(obj[k])
                return

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        fondo(p, (176, 220, 238), (92, 160, 196))
        self._dibujar_cabecera(p)
        self._dibujar_mundos(p)
        self._dibujar_peces(p)
        self._dibujar_equipo(p)
        txt, col = self.texto_defecto()
        self._barra_mensaje(p, 24, 1232, txt, col)
        self.volver.dibujar(p, self.f.normal)
        self.b_taller.dibujar(p, self.f.normal)
        self._dibujar_pescar(p)
        self._dibujar_efectos(p)
        if self.ficha:
            self._dibujar_ficha(p)

    def _barra_mensaje(self, p, x, ancho, defecto, color_def=TINTA_SUAVE):
        txt, col, t = self.msg
        if t <= 0 or not txt or color_def == ROJO:      # el aviso de equipo o mundo cerrado siempre se ve
            txt, col = defecto, color_def
        panel(p, (x, 556, ancho, 66), color=PAPEL, alfa=240, radio=18, borde=(60, 100, 130))
        f = self.f.normal if self.f.normal.size(txt)[0] < ancho - 40 else self.f.chica
        if f is self.f.chica and self.f.chica.size(txt)[0] > ancho - 40:
            centrado(p, self.f.chica, txt, x + ancho / 2, 566, ancho - 40, col, interlineado=24, maximo=2)
        else:
            ajustado(p, f, txt, x + ancho / 2, 589, ancho - 40, col)

    def _dibujar_pescar(self, p):
        ok, motivo = self.estado_pesca()
        self.b_pescar.texto = "¡A pescar!" if ok else ("Mundo cerrado" if motivo == "cerrado" else "Faltan estrellas")
        self.b_pescar.dibujar(p, self.f.grande)
        if ok:
            pulso = 3 + 2 * math.sin(self.t * 4)
            pygame.draw.rect(p, (255, 240, 130), self.b_pescar.rect.inflate(10 + pulso, 10 + pulso), 4,
                             border_radius=28)
            herramienta(p, "anzuelo", self.b_pescar.rect.x + 64, self.b_pescar.rect.centery, 0.5, 0)
            herramienta(p, "cana", self.b_pescar.rect.right - 64, self.b_pescar.rect.centery, 0.5, 0)

    def _dibujar_cabecera(self, p):
        self._cabecera(p)
        per = self.perfil
        escribir(p, self.f.grande, "Expedición de pesca", 24, 47, (255, 240, 200), ancla="izq",
                 contorno=(60, 40, 20))
        panel(p, (610, 12, 330, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        ajustado(p, self.f.normal, f"Peces registrados: {len(pd.especies_registradas(per))}", 775, 47, 300, TINTA)
        panel(p, (992, 12, 264, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        moneda(p, 1024, 47, 17)
        ajustado(p, self.f.grande, f"{per.monedas:,}".replace(",", "."), 1050, 47, 190, TINTA, ancla="izq")

    # ---- fila de mundos
    def _dibujar_mundos(self, p):
        per = self.perfil
        activo = pd.mundo_actual(per)
        for i, b in enumerate(self.b_mundos):
            abierto = pd.mundo_abierto(per, i)
            r = b.rect
            col = pd.MUNDOS[i]["color"] if abierto else (150, 155, 170)
            b.color = col
            sombra = r.move(0, 6)
            pygame.draw.rect(p, oscurecer(col, 0.5), sombra, border_radius=22)
            _pegar_redondeado(p, miniatura_fondo(i, r.size), r, 22)
            if not abierto:
                velo = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(velo, (60, 64, 80, 170), velo.get_rect(), border_radius=22)
                p.blit(velo, r.topleft)
            elif b.encima:
                velo = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(velo, (255, 255, 255, 50), velo.get_rect(), border_radius=22)
                p.blit(velo, r.topleft)
            pygame.draw.rect(p, (255, 255, 255), r, 4, border_radius=22)
            if i == self.vista:
                pygame.draw.rect(p, (255, 235, 120), r.inflate(12, 12), 5, border_radius=26)
            # franja de texto
            franja = pygame.Surface((r.width - 8, 62), pygame.SRCALPHA)
            pygame.draw.rect(franja, (20, 30, 50, 150), franja.get_rect(), border_radius=14)
            p.blit(franja, (r.x + 4, r.bottom - 66))
            ajustado(p, self.f.normal, corto_mundo(i), r.x + 12, r.y + 24, r.width - 80, (255, 255, 255),
                     ancla="izq", contorno=(30, 40, 60))
            h, tot = pd.progreso(per, i)
            if abierto:
                ajustado(p, self.f.chica, f"{h} / {tot} peces", r.x + 12, r.bottom - 48, r.width - 100,
                         (255, 255, 255), ancla="izq")
                barra(p, (r.x + 12, r.bottom - 30, r.width - 100, 12), h / max(1, tot),
                      color=(90, 210, 130) if h >= tot else (90, 170, 235))
                if i == activo:
                    ajustado(p, self.f.chica, "Pescando aquí", r.right - 12, r.y + 54, 110, (255, 240, 160),
                             ancla="der", contorno=(30, 40, 60))
            else:
                ajustado(p, self.f.chica, "Bloqueado", r.x + 12, r.bottom - 48, r.width - 100, (255, 255, 255),
                         ancla="izq")
                ajustado(p, self.f.chica, f"0 / {tot} peces", r.x + 12, r.bottom - 26, r.width - 100,
                         (220, 225, 235), ancla="izq")
            # estrellas que pide
            ajustado(p, self.f.chica, f"{pd.estrellas_requeridas(i)}", r.right - 34, r.y + 24, 20, (255, 255, 255),
                     ancla="der", contorno=(30, 40, 60))
            estrella(p, r.right - 20, r.y + 24, 10)
            ix, iy = r.right - 40, r.bottom - 36
            if not abierto:
                dibujar_candado(p, ix, iy + 4, 18)
            elif pd.tiene_llave(per, i) and i < pd.NUM_MUNDOS - 1:
                dibujar_llave(p, ix - 6, iy, 16)
            if b.dwell > 0:
                barra(p, (r.x + 14, r.bottom - 12, r.width - 28, 7), min(1.0, b.dwell / 1.2),
                      color=(255, 230, 90), color_fondo=(110, 120, 150), borde=(255, 255, 255))

    # ---- peces objetivo del mundo elegido
    def _dibujar_peces(self, p):
        per = self.perfil
        i = self.vista
        m = pd.MUNDOS[i]
        abierto = self.abierto()
        area = pygame.Rect(24, 218, 862, 330)
        img = miniatura_fondo(i, area.size)
        _pegar_redondeado(p, img, area, 22)
        velo = pygame.Surface(area.size, pygame.SRCALPHA)
        pygame.draw.rect(velo, (255, 250, 235, 190), velo.get_rect(), border_radius=22)
        p.blit(velo, area.topleft)
        pygame.draw.rect(p, oscurecer(m["color"], 0.6), area, 4, border_radius=22)
        h, tot = pd.progreso(per, i)
        titulo = m["nombre"] + (f"  ·  {h} de {tot} peces" if abierto else "")
        if abierto and pd.tiene_llave(per, i) and i < pd.NUM_MUNDOS - 1:
            titulo = m["nombre"] + "  ·  ¡Llave conseguida!"
        ajustado(p, self.f.normal, titulo, area.centerx, 235, 800, TINTA)
        obj = self.objetivos()
        for k, b in enumerate(self.b_peces):
            if k < len(obj):
                self._tarjeta_pez(p, b, obj[k], abierto)
        if not abierto:
            self._cartel_bloqueado(p, area)

    def _tarjeta_pez(self, p, b, sp, abierto):
        per = self.perfil
        r = b.rect
        n = pd.veces(per, sp)
        reg = n > 0 and abierto
        tarjeta(p, r, pd.MUNDOS[self.vista]["color"] if abierto else (150, 155, 170),
                aclarar(PAPEL, 0.4) if b.encima else PAPEL, radio=16)
        zona = pygame.Rect(r.x + 5, r.y + 5, r.width - 10, 84)
        p.set_clip(zona)
        arte.dibujar_pez(p, sp, zona.centerx, zona.centery + 2, escala_pez(sp), 1, self.t, silueta=not reg)
        p.set_clip(None)
        if reg:
            estrella(p, r.right - 20, r.y + 20, 11)
            ajustado(p, self.f.normal, nombre_pez(sp), r.centerx, r.y + 104, r.width - 16, TINTA)
            ajustado(p, self.f.chica, f"Pescado {_plural(n, 'vez', 'veces')}", r.centerx, r.y + 128,
                     r.width - 16, VERDE)
        else:
            ajustado(p, self.f.normal, "???", r.centerx, r.y + 104, r.width - 16, TINTA_SUAVE)
            ajustado(p, self.f.chica, "¡Aún sin pescar!" if abierto else "Bloqueado", r.centerx, r.y + 128,
                     r.width - 16, TINTA_SUAVE)
        if b.dwell > 0:
            barra(p, (r.x + 14, r.bottom - 10, r.width - 28, 7), min(1.0, b.dwell / 1.2),
                  color=(255, 230, 90), color_fondo=(110, 120, 150), borde=(255, 255, 255))

    def _cartel_bloqueado(self, p, area):
        i = self.vista
        r = pygame.Rect(0, 0, 500, 230)
        r.center = area.center
        r.y += 12
        pygame.draw.rect(p, (50, 50, 70), r.move(0, 6), border_radius=26)
        panel(p, r, color=(250, 245, 235), alfa=250, radio=26, borde=(110, 115, 135))
        dibujar_candado(p, r.centerx, r.y + 64, 34)
        centrado(p, self.f.normal, f"Pesca los 6 peces de {pd.MUNDOS[i - 1]['nombre']} para conseguir la llave",
                 r.centerx, r.y + 122, r.width - 50, TINTA, interlineado=36, maximo=3)

    # ---- equipo
    def _dibujar_equipo(self, p):
        per = self.perfil
        i = self.vista
        req = pd.estrellas_requeridas(i)
        x0, w = self.X_EQ, self.W_EQ
        panel(p, (x0, 218, w, 330), color=PAPEL, alfa=245, radio=22, borde=(60, 100, 130))
        ajustado(p, self.f.normal, "Tu equipo", x0 + w / 2, 236, w - 20, TINTA)
        for k, tipo in enumerate(pd.TIPOS_HERR):
            r = pygame.Rect(x0 + 10, 252 + k * 84, w - 20, 78)
            h = pd.herramienta_activa(per, tipo)
            corto = h is None or h["est"] < req
            tarjeta(p, r, ROJO if corto else (90, 190, 110), (255, 255, 255), sombra=False, radio=14)
            ajustado(p, self.f.normal, pd.NOMBRES_HERR[tipo], r.x + 78, r.y + 15, 150, TINTA, ancla="izq")
            if h is None:
                ajustado(p, self.f.chica, "Sin herramienta", r.x + 78, r.y + 48, 160, ROJO, ancla="izq")
                continue
            herramienta(p, tipo, r.x + 38, r.y + 38, 0.5, 0)
            estrellitas(p, r.right - 80, r.y + 15, h["est"], 5, r=7, sep=15, encendidas=h["est"])
            f = h["dur"] / pd.DURABILIDAD[h["est"]]
            barra(p, (r.x + 78, r.y + 34, r.width - 94, 18), f, color=color_dur(f))
            ajustado(p, self.f.chica, f"{int(math.ceil(f * 100))}%", r.x + 78 + (r.width - 94) / 2, r.y + 43, 60,
                     (255, 255, 255), contorno=(30, 30, 50))
            if corto:
                ajustado(p, self.f.chica, f"¡Pide {_estrellas_txt(req)}!", r.x + 78, r.y + 63, r.width - 94, ROJO,
                         ancla="izq")
        ajustado(p, self.f.chica, f"Este mundo pide {_estrellas_txt(req)} en todo", x0 + w / 2, 535, w - 20,
                 TINTA_SUAVE)

    # ---- ficha del pez
    def _dibujar_ficha(self, p):
        sp = self.ficha
        per = self.perfil
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((10, 30, 50, 160))
        p.blit(velo, (0, 0))
        r = pygame.Rect(200, 84, 880, 520)
        panel(p, r, color=(255, 248, 226), alfa=252, radio=30, borde=(60, 120, 170))
        reg = pd.registrado(per, sp)
        d = arte.PECES[sp]
        # el pez, grande, sobre su mar
        vista = pygame.Rect(r.x + 24, r.y + 24, 380, 300)
        _pegar_redondeado(p, miniatura_fondo(self.vista, vista.size), vista, 22)
        pygame.draw.rect(p, (60, 120, 170), vista, 4, border_radius=22)
        p.set_clip(vista)
        arte.dibujar_pez(p, sp, vista.centerx, vista.centery, 2.4 * escala_pez(sp), 1, self.t,
                         silueta=not reg)
        p.set_clip(None)
        tam, dato = FICHAS.get(sp, ("", ""))
        x = r.x + 430
        w = r.right - x - 24
        if reg:
            ajustado(p, self.f.grande, nombre_pez(sp), x + w / 2, r.y + 52, w, (30, 90, 140))
            estrellitas(p, x + w / 2, r.y + 100, d[1], 5, r=11, sep=28, encendidas=d[1])
            ajustado(p, self.f.chica, f"Pescado {_plural(pd.veces(per, sp), 'vez', 'veces')}", x + w / 2, r.y + 130,
                     w, VERDE)
        else:
            ajustado(p, self.f.grande, "Pez misterioso", x + w / 2, r.y + 52, w, TINTA_SUAVE)
            ajustado(p, self.f.normal, "¡Aún no lo has pescado!", x + w / 2, r.y + 108, w, (200, 120, 0))
        mundos, nivel = donde_vive(sp)
        y = r.y + 160
        if reg:
            ajustado(p, self.f.chica, "Dato curioso", x, y, w, (30, 90, 140), ancla="izq")
            y = centrado(p, self.f.normal, dato, x + w / 2, y + 10, w, TINTA, interlineado=32, maximo=3)
            y += 8
            ajustado(p, self.f.chica, "Tamaño", x, y + 8, w, (30, 90, 140), ancla="izq")
            ajustado(p, self.f.normal, tam, x + w / 2, y + 38, w, TINTA)
            y += 62
        ajustado(p, self.f.chica, "Dónde vive", x, y + 8, w, (30, 90, 140), ancla="izq")
        centrado(p, self.f.normal, f"{mundos}, {nivel}", x + w / 2, y + 20, w, TINTA, interlineado=32, maximo=3)
        if not reg:
            centrado(p, self.f.normal, "¡Pesca uno para ver su ficha completa!", x + w / 2, r.y + 300, w,
                     TINTA_SUAVE, interlineado=32, maximo=2)
        self.b_cerrar.dibujar(p, self.f.grande)


# =====================================================================
#  TALLER
# =====================================================================
class TallerEscena(_Base):
    X_DET, W_DET = 880, 376
    R_ZONA = 100

    def __init__(self, app, volver=None):
        super().__init__(app)
        self.volver_a = volver
        self.tipo = pd.TIPOS_HERR[0]
        self.vista = "recetas"
        self.est = 1
        self.pagina = 0
        self.craft = None            # animacion en curso
        self.cartel = None           # "Nueva herramienta"
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.tabs = {t: BotonF((24 + i * 192, 14, 184, 66), pd.NOMBRES_HERR[t], COLOR_HERR[t])
                     for i, t in enumerate(pd.TIPOS_HERR)}
        self.b_vista = BotonF((802, 14, 236, 66), "Mis herramientas", (150, 110, 200))
        self.b_filas = [Boton((24, 168 + i * 90, 842, 82), "", (200, 160, 100)) for i in range(5)]
        self.b_comprar = [BotonF((self.X_DET + self.W_DET - 142, 296 + i * 46 - 21, 130, 42), "Comprar",
                                 (235, 150, 60)) for i in range(5)]
        self.b_todo = BotonF((self.X_DET + 8, 506, self.W_DET - 16, 46), "Comprar lo que falta", (235, 150, 60))
        self.b_craftear = BotonF((self.X_DET + 8, 558, self.W_DET - 16, 70), "CRAFTEAR", (80, 180, 90))
        self.b_equipar = [BotonF((706, 168 + i * 66 + 6, 156, 48), "Equipar", (60, 160, 190))
                          for i in range(POR_PAGINA_MIAS)]
        self.b_ant = BotonF((210, ALTO - 78, 150, 56), "< Antes", (70, 150, 230))
        self.b_sig = BotonF((370, ALTO - 78, 150, 56), "Más >", (70, 150, 230))
        self.b_cancelar = BotonF((540, 566, 200, 48), "Cancelar", (150, 150, 170))
        self.b_genial = BotonF((520, 520, 240, 70), "¡Genial!", (80, 180, 90))

    # ------------------------------------------------------------ datos
    def mats(self):
        r = pd.receta_herramienta(self.tipo, self.est)
        return [(m, r[m]) for m in ORDEN_MAT if m in r]

    def faltan(self):
        per = self.perfil
        return [(m, n - per.cantidad(m)) for m, n in self.mats() if per.cantidad(m) < n]

    def costo_faltan(self):
        """(costo de lo que se puede comprar, hay algo que no se vende)."""
        costo, no_vende = 0, False
        for m, f in self.faltan():
            if pd.se_vende(m):
                costo += pd.precio(m) * f
            else:
                no_vende = True
        return costo, no_vende

    def lista_mias(self):
        per = self.perfil
        act = pd.herramienta_activa(per, self.tipo)
        hs = sorted(pd.herramientas(per, self.tipo),
                    key=lambda h: (-(act is not None and h["id"] == act["id"]), -h["est"], -h["dur"], h["id"]))
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
        costo = pd.precio(mat) * n
        if per.monedas < costo:
            self.snd.reproducir("error")
            self.decir(f"Te faltan {costo - per.monedas} monedas. ¡Juega para ganar más!", ROJO)
            return False
        if pd.comprar_material(per, mat, n):
            per.guardar()
            self.snd.reproducir("moneda")
            self.decir(f"¡Compraste {n} de {catalogo.nombre_item(mat).lower()}!", VERDE)
            self._celebrar(self.X_DET + 190, 312, f"+{n}")
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
            if pd.se_vende(m):
                pd.comprar_material(per, m, f)
        per.guardar()
        self.snd.reproducir("moneda")
        self.decir("¡Compraste lo que faltaba!", VERDE)
        self._celebrar(self.X_DET + 190, 490, "¡Listo!")

    def _empezar_craft(self):
        per = self.perfil
        if not pd.puede_craftear(per, self.tipo, self.est):
            self.snd.reproducir("error")
            self.decir("Todavía faltan materiales. ¡Compra lo básico o consigue el resto pescando!", ROJO)
            return
        self.snd.reproducir("click")
        self.craft = dict(tipo=self.tipo, est=self.est, prog=0.0, t=0.0, golpe_t=0.0, dentro=False, hits=0)
        self.cartel = None

    def zona_pos(self, t=None):
        """Centro de la zona brillante que hay que seguir (se mueve despacio)."""
        t = self.craft["t"] if t is None and self.craft else (t or 0.0)
        return (640 + 200 * math.sin(0.9 * t), 330 + 55 * math.sin(1.7 * t + 1.0))

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
        seg = pd.segundos_crafteo(c["est"])
        c["golpe_t"] = max(0.0, c["golpe_t"] - dt)
        trabajo = ctrl.vel > 120 or ctrl.golpe or ctrl.clic
        if dentro:                                   # la barra solo avanza dentro del circulo verde
            c["prog"] += dt / seg
            if trabajo:
                if random.random() < min(1.0, dt * 22):
                    self.particulas.append(Particula(ctrl.pos.x, ctrl.pos.y, random.choice(
                        [(120, 220, 255), (190, 240, 255), (255, 255, 255)]), 90, 320, 0.55, 700, 4))
                if c["golpe_t"] <= 0:
                    c["golpe_t"] = 0.42
                    self.snd.reproducir("golpe")
        if (ctrl.golpe or ctrl.clic) and dentro:
            c["prog"] += 0.25 / seg
            explosion(self.particulas, ctrl.pos.x, ctrl.pos.y, (150, 230, 255), n=12, vida=0.6)
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
        act = pd.herramienta_activa(per, tipo)
        h = pd.craftear(per, tipo, est)
        if h is None:
            self.snd.reproducir("error")
            self.decir("Ay, faltaron materiales. ¡Prueba otra vez!", ROJO)
            return
        puesta = act is None or est >= act["est"]
        if puesta:
            pd.equipar(per, h["id"])
        per.guardar()
        self.snd.reproducir("ok")
        self.snd.reproducir("premio")
        self.cartel = dict(h=h, tipo=tipo, est=est, puesta=puesta, t=0.0)
        explosion(self.particulas, 640, 300, (255, 215, 60), n=40, vida=1.1)

    def _equipar(self, h):
        per = self.perfil
        if pd.equipar(per, h["id"]):
            per.guardar()
            self.snd.reproducir("ok")
            self.decir(f"¡Listo! Usas {NOMBRE_MIN[h['tipo']]} de {_estrellas_txt(h['est'])}.", VERDE)
        else:
            self.snd.reproducir("error")

    def _salir(self):
        self.snd.reproducir("click")
        v = self.volver_a
        if v is None:
            self.app.ir(PescaEscena(self.app))
        elif isinstance(v, Escena):
            self.app.ir(v)
        elif callable(v):
            r = v()
            if isinstance(r, Escena):
                self.app.ir(r)
        else:
            self.app.ir(PescaEscena(self.app))

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
            if i < len(mats) and mats[i][0] in falt and pd.se_vende(mats[i][0]):
                b.activo = True
                if b.actualizar(dt, ctrl):
                    self._comprar_uno(mats[i][0], falt[mats[i][0]])
            else:
                b.activo = False
        costo, _ = self.costo_faltan()
        self.b_todo.activo = costo > 0 and per.monedas >= costo
        if costo > 0 and self.b_todo.actualizar(dt, ctrl):
            self._comprar_todo()
        self.b_craftear.activo = pd.puede_craftear(per, self.tipo, self.est)
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
        fondo(p, (190, 226, 240), (110, 160, 190))
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
            defecto = ("¡Tienes todo! Pulsa CRAFTEAR." if pd.puede_craftear(self.perfil, self.tipo, self.est)
                       else "Faltan materiales: cómpralos con monedas o consíguelos pescando.")
        else:
            self._dibujar_mias(p)
            defecto = "La herramienta equipada es la que usas al pescar."
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
        panel(p, (24, 102, 1232, 58), color=PAPEL, alfa=235, radio=16, borde=(110, 120, 140))
        w = 1232 / len(ORDEN_MAT)
        for k, m in enumerate(ORDEN_MAT):
            x = 24 + k * w
            icono_material(p, m, x + 24, 131, 34)
            ajustado(p, self.f.chica, nombre_mat(m), x + 46, 118, w - 50, TINTA_SUAVE, ancla="izq")
            ajustado(p, self.f.normal, f"{per.cantidad(m)}", x + 46, 142, w - 50, TINTA, ancla="izq")

    # ---- recetas
    def _dibujar_recetas(self, p):
        per = self.perfil
        for i, b in enumerate(self.b_filas):
            est = i + 1
            r = b.rect
            sel = est == self.est
            r_mats = pd.receta_herramienta(self.tipo, est)
            puede = all(per.cantidad(m) >= n for m, n in r_mats.items())
            tarjeta(p, r, COLOR_HERR[self.tipo] if sel else (150, 140, 130),
                    aclarar(PAPEL, 0.4) if b.encima else PAPEL, radio=16)
            if sel:
                pygame.draw.rect(p, (255, 235, 120), r.inflate(8, 8), 4, border_radius=20)
            herramienta(p, self.tipo, r.x + 54, r.centery - 8, 0.52, 0)
            estrellitas(p, r.x + 54, r.bottom - 12, est, 5, r=6, sep=13, encendidas=est)
            presentes = [m for m in ORDEN_MAT if m in r_mats]
            for idx, m in enumerate(presentes):
                n = r_mats[m]
                x = r.x + 126 + idx * 122
                icono_material(p, m, x + 22, r.centery, 38)
                tengo = per.cantidad(m)
                ajustado(p, self.f.normal, f"{tengo} / {n}", x + 46, r.centery, 70, VERDE if tengo >= n else ROJO,
                         ancla="izq")
            if puede:
                ajustado(p, self.f.chica, "¡Listo!", r.right - 12, r.y + 14, 70, VERDE, ancla="der")
        self._dibujar_detalle(p)

    def _dibujar_detalle(self, p):
        per = self.perfil
        x, w = self.X_DET, self.W_DET
        panel(p, (x, 168, w, 466), color=PAPEL, alfa=245, radio=22, borde=(90, 100, 130))
        herramienta(p, self.tipo, x + 56, 214, 0.62, 0)
        ajustado(p, self.f.normal, pd.NOMBRES_HERR[self.tipo], x + 112, 196, w - 124, TINTA, ancla="izq")
        ajustado(p, self.f.normal, _estrellas_txt(self.est), x + 112, 230, w - 124, (200, 140, 20), ancla="izq")
        ajustado(p, self.f.chica, "Materiales que necesitas:", x + 14, 258, w - 20, TINTA_SUAVE, ancla="izq")
        mats = self.mats()
        falt = dict(self.faltan())
        for i, (m, n) in enumerate(mats):
            cy = 296 + i * 46
            tengo = per.cantidad(m)
            icono_material(p, m, x + 30, cy, 36)
            ajustado(p, self.f.normal, f"{tengo} / {n}", x + 54, cy, 84, VERDE if tengo >= n else ROJO,
                     ancla="izq")
            vende = m in falt and pd.se_vende(m)
            ajustado(p, self.f.chica, nombre_mat(m), x + 142, cy - (8 if m in falt and not vende else 0),
                     90 if vende else 150, TINTA, ancla="izq")
            if m in falt:
                if vende:
                    precio = pd.precio(m) * falt[m]
                    b = self.b_comprar[i]
                    b.texto = f"Comprar {precio}"
                    b.color = (235, 150, 60) if per.monedas >= precio else (190, 160, 130)
                    b.dibujar(p, self.f.normal)
                else:
                    ajustado(p, self.f.chica, "Solo pescando", x + 142, cy + 11, 150, (60, 120, 170), ancla="izq")
        costo, _ = self.costo_faltan()
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
            r = pygame.Rect(24, 168, 842, 150)
            panel(p, r, color=PAPEL, alfa=240, radio=22, borde=(110, 120, 140))
            ajustado(p, self.f.grande, f"No tienes {NOMBRE_MIN[self.tipo]}", r.centerx, r.y + 56, r.width - 40, TINTA)
            ajustado(p, self.f.normal, "¡Craftea una en Recetas!", r.centerx, r.y + 106, r.width - 40, TINTA_SUAVE)
        for i, h in enumerate(vis):
            r = pygame.Rect(24, 168 + i * 66, 842, 60)
            puesta = act is not None and h["id"] == act["id"]
            tarjeta(p, r, (90, 190, 110) if puesta else (150, 140, 130), PAPEL, radio=14)
            herramienta(p, h["tipo"], r.x + 46, r.centery, 0.4, 0)
            estrellitas(p, r.x + 170, r.centery, h["est"], 5, r=9, sep=21, encendidas=h["est"])
            f = h["dur"] / pd.DURABILIDAD[h["est"]]
            barra(p, (r.x + 300, r.centery - 13, 260, 26), f, color=color_dur(f))
            ajustado(p, self.f.normal, f"{int(math.ceil(f * 100))}%", r.x + 576, r.centery, 80, TINTA, ancla="izq")
            if puesta:
                ajustado(p, self.f.normal, "¡Equipada!", r.right - 90, r.centery, 150, VERDE)
            else:
                self.b_equipar[i].dibujar(p, self.f.normal)
        x, w = self.X_DET, self.W_DET
        panel(p, (x, 168, w, 466), color=PAPEL, alfa=245, radio=22, borde=(90, 100, 130))
        herramienta(p, self.tipo, x + w / 2, 250, 1.1, 0)
        ajustado(p, self.f.grande, pd.NOMBRES_HERR[self.tipo], x + w / 2, 340, w - 30, TINTA)
        yy = centrado(p, self.f.normal, EXPLICA_HERR[self.tipo], x + w / 2, 372, w - 40, TINTA_SUAVE,
                      interlineado=34, maximo=3)
        centrado(p, self.f.normal, "Si se gasta del todo, se rompe: ¡craftea otra!", x + w / 2, yy + 14, w - 40,
                 (140, 70, 20), interlineado=34, maximo=3)

    # ---- animacion de crafteo
    def _dibujar_craft(self, p):
        c = self.craft
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((10, 30, 50, 150))
        p.blit(velo, (0, 0))
        r = pygame.Rect(180, 96, 920, 528)
        panel(p, r, color=(36, 70, 96), alfa=250, radio=28, borde=(255, 220, 120))
        tipo, est = c["tipo"], c["est"]
        ajustado(p, self.f.grande, f"Crafteando: {pd.NOMBRES_HERR[tipo]}", 640, 134, 800, (255, 240, 200),
                 contorno=(20, 30, 50))
        estrellitas(p, 640, 176, est, est, r=14, sep=34, encendidas=min(est, int(c["prog"] * est + 0.001)))
        # mesa de trabajo con luz que crece
        brillo = int(40 + 180 * c["prog"])
        glow = pygame.Surface((420, 300), pygame.SRCALPHA)
        for k in range(6, 0, -1):
            pygame.draw.ellipse(glow, (130, 220, 255, int(brillo / 6)), (210 - 34 * k, 150 - 24 * k, 68 * k, 48 * k))
        p.blit(glow, (430, 175))
        pygame.draw.rect(p, (150, 104, 60), (440, 430, 400, 34), border_radius=10)
        pygame.draw.rect(p, (110, 74, 40), (440, 456, 400, 10), border_radius=4)
        for px in (470, 790):
            pygame.draw.rect(p, (110, 74, 40), (px, 460, 22, 60))
        mov = c["dentro"]
        dy = 5 * math.sin(c["t"] * 14) if mov else 0
        herramienta(p, tipo, 640, 320 + dy, 2.0, 0)
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
        ajustado(p, self.f.normal, "¡Mueve el cursor sobre la luz!" if not c["dentro"] else "¡Muy bien, sigue así!",
                 640, 232, 760, (255, 240, 180) if not c["dentro"] else (160, 255, 170), contorno=(20, 30, 50))
        barra(p, (300, 526, 680, 30), c["prog"], color=(255, 170, 50), color_fondo=(30, 40, 60),
              borde=(255, 255, 255))
        ajustado(p, self.f.chica, f"{int(min(1.0, c['prog']) * 100)}%", 640, 541, 80, (255, 255, 255),
                 contorno=(20, 30, 50))
        self.b_cancelar.dibujar(p, self.f.normal)

    def _dibujar_cartel(self, p):
        k = self.cartel
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((10, 30, 50, 150))
        p.blit(velo, (0, 0))
        r = pygame.Rect(300, 100, 680, 520)
        panel(p, r, color=(255, 248, 226), alfa=252, radio=30, borde=(255, 190, 40))
        escala = 1.0 + 0.06 * math.sin(self.t * 6)
        for i in range(12):
            a = self.t * 0.8 + i * math.pi / 6
            pygame.draw.line(p, (255, 230, 140), (640 + 90 * math.cos(a), 300 + 90 * math.sin(a)),
                             (640 + 190 * math.cos(a), 300 + 190 * math.sin(a)), 5)
        ajustado(p, self.f.grande, "¡Nueva herramienta!", 640, 150, 620, (200, 110, 20))
        herramienta(p, k["tipo"], 640, 290, 2.0 * escala, 0)
        estrellitas(p, 640, 392, k["est"], k["est"], r=15, sep=36, encendidas=k["est"])
        ajustado(p, self.f.normal, f"{pd.NOMBRES_HERR[k['tipo']]} de {_estrellas_txt(k['est'])}", 640, 440, 620, TINTA)
        ajustado(p, self.f.normal, "¡Ya la estás usando!" if k["puesta"] else "Equípala en Mis herramientas.",
                 640, 478, 620, VERDE if k["puesta"] else TINTA_SUAVE)
        self.b_genial.dibujar(p, self.f.grande)
