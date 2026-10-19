"""Ninja Mundo: menu principal, minijuegos sueltos, ruleta de mejoras, cuaderno, granja, items y gachapon.

La clase Aplicacion maneja las pantallas (escenas). Cada escena recibe el control
(cursor, clic, golpe...) y dibuja con codigo, igual que los minijuegos.
"""

import math
import random

import pygame

import arte
import arte_paleo
import fosiles_datos
import pesca_datos
from escena import Escena, fondo_fiesta
from ajustes import ANCHO, ALTO, MONEDAS_POR_PUNTO, RULETA_CADA, USOS_MEJORA
import catalogo
from nucleo import (Boton, Contexto, MEJORAS, Mejoras, Perfil, Sonidos, Fuentes, aclarar,
                    barra, escribir, estrella, explosion, fondo, oscurecer, panel)

from j_cocina import Cocina
from j_espacio import Espacio
from espacio_escena import EspacioEscena
from j_fosiles import Fosiles
from j_pesca import Pesca
from j_ruinas import Ruinas
from j_tama import Tamagotchi
from j_horda import Horda   # la pelea del Tamagotchi (boton ENTRENAR)
from escena_gachapon import GachaponEscena
from escena_granja import GranjaEscena
from escena_fosiles import ExpedicionEscena
from escena_pesca import PescaEscena
from escena_ruinas import RuinasEscena
from escena_tama import TamagotchiEscena
from escena_items import ItemsEscena

# id -> clase, en el orden en que aparecen en "Minijuegos"
JUEGOS = {c.id: c for c in (Pesca, Cocina, Tamagotchi, Ruinas, Fosiles, Espacio)}
# Partidas que lanza una pantalla (no aparecen en Libre): la pelea nueva del Tamagotchi
JUEGOS_TODOS = {**JUEGOS, "horda": Horda}

COLORES_JUEGO = {
    "pesca": (70, 150, 230), "cocina": (240, 160, 60),
    "tamagotchi": (235, 120, 170), "ruinas": (200, 150, 70), "fosiles": (190, 140, 80), "espacio": (80, 90, 190),
}


# ===================================================================== escenas

def moneda(p, x, y, r=14):
    pygame.draw.circle(p, (190, 130, 20), (x, y + 2), r)
    pygame.draw.circle(p, (255, 205, 60), (x, y), r)
    pygame.draw.circle(p, (255, 235, 140), (x, y), max(2, int(r * 0.68)), max(2, r // 6))
    pygame.draw.circle(p, (255, 245, 190), (x - r // 3, y - r // 3), max(2, r // 5))


class Menu(Escena):
    def __init__(self, app):
        super().__init__(app)
        izq, der = ANCHO // 2 - 375, ANCHO // 2 + 15
        ys = [235 + 92 * i for i in range(4)]
        self.botones = {
            "libre": Boton((izq, ys[0], 360, 78), "MINIJUEGOS", (70, 150, 230)),
            "cuaderno": Boton((izq, ys[1], 360, 78), "CUADERNO", (240, 160, 60)),
            "items": Boton((izq, ys[2], 360, 78), "ITEMS", (120, 130, 200)),
            "granja": Boton((der, ys[0], 360, 78), "GRANJA", (110, 180, 90)),
            "gacha": Boton((der, ys[1], 360, 78), "GACHAPÓN", (230, 90, 120)),
            "ruleta": Boton((der, ys[2], 360, 78), "RULETA", (200, 90, 200)),
            "salir": Boton((ANCHO - 190, ALTO - 78, 160, 56), "Salir", (150, 150, 170)),
        }

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        perfil = self.app.ctx.perfil
        self.botones["ruleta"].activo = perfil.fichas > 0
        for nombre, b in self.botones.items():
            if b.actualizar(dt, ctrl):
                self.app.ctx.sonidos.reproducir("click")
                if nombre == "libre":
                    self.app.ir(Libre(self.app))
                elif nombre == "cuaderno":
                    self.app.ir(Cuaderno(self.app))
                elif nombre == "items":
                    self.app.ir(ItemsEscena(self.app))
                elif nombre == "granja":
                    self.app.ir(GranjaEscena(self.app))
                elif nombre == "gacha":
                    self.app.ir(GachaponEscena(self.app))
                elif nombre == "ruleta":
                    self.app.ir(RuletaEscena(self.app, Menu))
                elif nombre == "salir":
                    self.app.salir = True

    def dibujar(self, p):
        fondo_fiesta(p, self.t)
        # criaturas bailando a los lados
        ids = arte.ORDEN_CRIATURAS
        for i in range(3):
            dy = 8 * math.sin(self.t * 3 + i)
            arte.dibujar_criatura(p, ids[(i * 4) % len(ids)], 110, 280 + i * 130 + dy, 0.85, self.t)
            arte.dibujar_criatura(p, ids[(i * 4 + 2) % len(ids)], ANCHO - 110, 270 + i * 130 - dy, 0.85, self.t)
        escribir(p, self.f.enorme, "NINJA MUNDO", ANCHO / 2, 110 + 6 * math.sin(self.t * 2.5),
                 (255, 230, 90), contorno=(120, 60, 20), grosor=4)
        escribir(p, self.f.normal, "¡Juegos de movimiento con tu mando!", ANCHO / 2, 188, (255, 255, 255))
        for b in self.botones.values():
            b.dibujar(p, self.f.grande if b.rect.width > 300 else self.f.normal)
        perfil = self.app.ctx.perfil
        # monedas
        moneda(p, ANCHO - 150, 36, 18)
        escribir(p, self.f.grande, str(perfil.monedas), ANCHO - 122, 36, (255, 235, 130), ancla="izq")
        # progreso de la ruleta, debajo del boton RULETA
        rx, ry = ANCHO // 2 + 15, 235 + 92 * 3
        if perfil.fichas > 0:
            escribir(p, self.f.normal, f"¡{perfil.fichas} giro(s) de ruleta!", rx + 180, ry + 36,
                     (255, 240, 120))
        else:
            falta = RULETA_CADA - perfil.puntos_pend
            barra(p, (rx + 20, ry + 8, 320, 22), perfil.puntos_pend / RULETA_CADA, color=(255, 200, 70))
            escribir(p, self.f.chica, f"{falta} puntos para la ruleta", rx + 180, ry + 52)
        activas = list(self.app.ctx.mejoras.activas.items())
        for i, (nombre, usos) in enumerate(activas):
            escribir(p, self.f.chica, f"{MEJORAS[nombre][1]} ({usos})", 24, 24 + i * 26,
                     (255, 240, 140), ancla="izq")
        if self.app.entrada.mando and not self.app.entrada.espada.calibrada:
            escribir(p, self.f.normal, "Primero calibra el mando: pulsa la tecla H", ANCHO / 2, ALTO - 30,
                     (255, 190, 90))


class Libre(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.volver = Boton((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.fichas = []
        ids = list(JUEGOS)
        for i, ident in enumerate(ids):
            # 6 juegos en 3 columnas x 2 filas, centrados en la ventana
            col, fil = i % 3, i // 3
            w, h, sep = 300, 200, 40
            x0 = (ANCHO - (3 * w + 2 * sep)) // 2
            rect = (x0 + col * (w + sep), 150 + fil * (h + sep), w, h)
            self.fichas.append((ident, Boton(rect, "", COLORES_JUEGO[ident])))

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        if self.volver.actualizar(dt, ctrl):
            self.app.ir(Menu(self.app))
            return
        for ident, b in self.fichas:
            if b.actualizar(dt, ctrl):
                self.app.ctx.sonidos.reproducir("click")
                if ident == "fosiles":
                    self.app.ir(ExpedicionEscena(self.app))
                elif ident == "pesca":
                    self.app.ir(PescaEscena(self.app))
                elif ident == "ruinas":
                    self.app.ir(RuinasEscena(self.app))
                elif ident == "espacio":
                    self.app.ir(EspacioEscena(self.app))
                elif ident == "tamagotchi":
                    self.app.ir(TamagotchiEscena(self.app))
                else:
                    self.app.ir(Intro(self.app, ident, 1))
                return

    def tecla_esc(self):
        self.app.ir(Menu(self.app))

    def dibujar(self, p):
        fondo_fiesta(p, self.t)
        escribir(p, self.f.grande, "Elige un minijuego", ANCHO / 2, 60, (255, 255, 255))
        for ident, b in self.fichas:
            clase = JUEGOS[ident]
            b.dibujar(p, self.f.normal)
            # reemplazamos el texto del boton por titulo + record
            pygame.draw.rect(p, COLORES_JUEGO[ident] if not b.encima else aclarar(COLORES_JUEGO[ident], 0.25),
                             b.rect.inflate(-10, -10), border_radius=18)
            fuente = self.f.normal if self.f.normal.size(clase.titulo)[0] <= b.rect.width - 24 else self.f.chica
            escribir(p, fuente, clase.titulo, b.rect.centerx, b.rect.centery - 14,
                     (255, 255, 255), contorno=oscurecer(COLORES_JUEGO[ident], 0.6))
            rec = self.app.ctx.perfil.records.get(ident, 0)
            escribir(p, self.f.chica, f"Récord: {rec}", b.rect.centerx, b.rect.centery + 28, (255, 255, 255),
                     contorno=oscurecer(COLORES_JUEGO[ident], 0.6))
            if b.dwell > 0:
                barra(p, (b.rect.x + 14, b.rect.bottom - 18, b.rect.width - 28, 8), b.dwell, color=(255, 230, 90))
            if ident == "fosiles":
                fosiles_datos.tick(self.app.ctx.perfil)
                if fosiles_datos.zona_lista(self.app.ctx.perfil):
                    arte_paleo.dibujar_carrito(p, b.rect.right - 38, b.rect.y + 30, 0.42, self.t, aviso=True)
                    escribir(p, self.f.chica, "¡Zona lista!", b.rect.x + 16, b.rect.y + 24, (255, 255, 255),
                             ancla="izq", contorno=(150, 60, 30))
        self.volver.dibujar(p, self.f.normal)


class Intro(Escena):
    """Pantalla antes de jugar: explica el gesto y deja elegir el nivel (en juego libre)."""

    def __init__(self, app, juego, nivel):
        super().__init__(app)
        self.juego, self.nivel = juego, nivel
        self.clase = JUEGOS_TODOS[juego]
        self.jugar = Boton((ANCHO / 2 - 190, 560, 380, 92), "¡JUGAR!", (90, 190, 110))
        self.volver = Boton((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.menos = Boton((ANCHO / 2 - 300, 455, 70, 64), "-", (70, 150, 230))
        self.mas = Boton((ANCHO / 2 + 230, 455, 70, 64), "+", (70, 150, 230))
        self.sin_nivel = (juego in ("cocina", "ruinas", "tamagotchi"))   # el recetario ya muestra el nivel

    def _textos(self):
        """(instruccion, gesto) segun el nivel (algunos juegos cambian el texto por nivel)."""
        ins = getattr(self.clase, "instrucciones_nivel", {}).get(self.nivel)
        return ins if ins else (self.clase.instruccion, self.clase.gesto)

    def _etiqueta_nivel(self):
        et = getattr(self.clase, "etiquetas_nivel", {}).get(self.nivel)
        return f"Nivel {self.nivel}: {et}" if et else f"Nivel {self.nivel}"

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        if self.volver.actualizar(dt, ctrl):
            self.tecla_esc()
            return
        if not self.sin_nivel:
            if self.menos.actualizar(dt, ctrl):
                self.nivel = max(1, self.nivel - 1)
            if self.mas.actualizar(dt, ctrl):
                self.nivel = min(self.clase.NIVEL_MAX, self.nivel + 1)
        if self.jugar.actualizar(dt, ctrl):
            self.app.ctx.sonidos.reproducir("ok")
            if self.juego == "ruinas":              # Ruinas se elige en su hub
                self.app.ir(RuinasEscena(self.app))
                return
            self.app.ir(Partida(self.app, self.juego, self.nivel))

    def tecla_esc(self):
        self.app.ir(Libre(self.app))

    def dibujar(self, p):
        color = COLORES_JUEGO[self.juego]
        fondo(p, aclarar(color, 0.35), aclarar(color, 0.8))
        panel(p, (ANCHO / 2 - 480, 60, 960, 380), alfa=225)
        escribir(p, self.f.grande, self.clase.titulo, ANCHO / 2, 160, (40, 60, 110), contorno=None)
        # texto de instruccion en varias lineas
        instruccion, gesto = self._textos()
        palabras = instruccion.split()
        lineas, actual = [], ""
        for w in palabras:
            if self.f.normal.size(actual + " " + w)[0] > 860 and actual:
                lineas.append(actual)
                actual = w
            else:
                actual = (actual + " " + w).strip()
        lineas.append(actual)
        for i, l in enumerate(lineas):
            escribir(p, self.f.normal, l, ANCHO / 2, 235 + i * 40, (50, 60, 90), contorno=None)
        y = 235 + len(lineas) * 40 + 30
        panel(p, (ANCHO / 2 - 400, y, 800, 70), color=aclarar(color, 0.7), alfa=255, radio=18)
        escribir(p, self.f.normal, "Gesto: " + gesto, ANCHO / 2, y + 35, (40, 60, 110), contorno=None)
        if not self.sin_nivel:
            escribir(p, self.f.normal, self._etiqueta_nivel(), ANCHO / 2, 487, (255, 255, 255))
            self.menos.dibujar(p, self.f.grande)
            self.mas.dibujar(p, self.f.grande)
        self.jugar.dibujar(p, self.f.grande)
        self.volver.dibujar(p, self.f.normal)


class Partida(Escena):
    """Cuenta atras y luego el minijuego."""

    def __init__(self, app, juego, nivel):
        super().__init__(app)
        self.juego_id, self.nivel = juego, nivel
        self.mj = JUEGOS_TODOS[juego](app.ctx, nivel)
        self.cuenta = 3.0
        self.t_ya = 0.0
        app.entrada.centrar()
        self.ultimo = 4

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        if self.cuenta > 0:
            self.cuenta -= dt
            n = int(math.ceil(self.cuenta))
            if n != self.ultimo and n > 0:
                self.app.ctx.sonidos.reproducir("tick")
            self.ultimo = n
            if self.cuenta <= 0:
                self.app.ctx.sonidos.reproducir("premio")
                ctrl.centrar()
            return
        self.t_ya += dt
        self.mj.actualizar(dt, ctrl)
        if self.mj.terminado:
            self.app.ctx.sonidos.reproducir("fin" if not self.mj.superado() else "premio")
            self.app.ir(Resultado(self.app, self.mj))

    def tecla_esc(self):
        cancelar = getattr(self.mj, "cancelar", None)
        if cancelar and not self.mj.terminado:
            cancelar()                       # Cocina devuelve los materiales si se sale a medias
        self.app.ir(Resultado.volver_a(self.app, self.juego_id))

    def dibujar(self, p):
        self.mj.dibujar(p)
        if self.cuenta > 0:
            sombra = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            sombra.fill((20, 30, 60, 120))
            p.blit(sombra, (0, 0))
            n = int(math.ceil(self.cuenta))
            escribir(p, self.f.enorme, str(n), ANCHO / 2, ALTO / 2 - 20, (255, 235, 120), contorno=(120, 60, 20), grosor=5)
            escribir(p, self.f.normal, self.mj.gesto, ANCHO / 2, ALTO / 2 + 70, (255, 255, 255))
        elif self.t_ya < 0.7:
            escribir(p, self.f.enorme, "¡YA!", ANCHO / 2, ALTO / 2 - 20, (130, 240, 150), contorno=(20, 90, 40), grosor=5)


class Resultado(Escena):
    def __init__(self, app, mj):
        super().__init__(app)
        self.mj = mj
        perfil = app.ctx.perfil
        self.estrellas = mj.estrellas()
        self.superado = mj.superado()
        self.nuevas = []
        self.fichas_nuevas = 0
        self.record_nuevo = False
        self.record_nuevo = perfil.record(mj.id, mj.puntos)
        self.fichas_nuevas = perfil.sumar_puntos(mj.puntos)
        self.monedas_ganadas = int(round(mj.puntos * MONEDAS_POR_PUNTO)) + 5 * self.estrellas
        perfil.ganar(self.monedas_ganadas)
        self.botin = dict(mj.botin)
        self.avisos_pesca = self._avisos_pesca(mj)
        self.cofre = (mj.id == "fosiles" and bool(self.botin))     # el botin de Fosiles sale de un cofre
        self.t_cofre = 0.0
        self.cofre_abierto = False
        for item, n in self.botin.items():
            perfil.dar(item, n)
        perfil.dia += 1
        for tipo, ident in mj.recompensas:
            if perfil.agregar(tipo, ident):
                self.nuevas.append((tipo, ident))
        app.ctx.mejoras.gastar_uso()
        perfil.guardar()
        self.mostradas = 0
        self.t_estrella = 0.0
        self.botones = {
            "seguir": Boton((ANCHO / 2 - 330, 600, 300, 78), "Seguir", (90, 190, 110)),
            "repetir": Boton((ANCHO / 2 + 30, 600, 300, 78), "Repetir", (70, 150, 230)),
        }
        self.ruleta = Boton((ANCHO - 330, 40, 290, 72), "¡RULETA!", (200, 90, 200))
        self.particulas = []
        if self.superado:
            for _ in range(5):
                explosion(self.particulas, random.uniform(300, 980), random.uniform(120, 300),
                          random.choice([(255, 210, 60), (240, 90, 120), (90, 200, 240), (120, 220, 130)]),
                          n=12, vel_min=100, vel_max=380, vida=1.2, gravedad=400, radio=6)

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self.particulas = [x for x in self.particulas if x.actualizar(dt)]
        self.t_estrella += dt
        if self.cofre:
            self.t_cofre += dt
            if not self.cofre_abierto and self.t_cofre > 1.8:
                self.cofre_abierto = True
                self.app.ctx.sonidos.reproducir("premio")
        if self.mostradas < self.estrellas and self.t_estrella > 0.6:
            self.mostradas += 1
            self.t_estrella = 0.0
            self.app.ctx.sonidos.reproducir("moneda")
        if self.botones["seguir"].actualizar(dt, ctrl):
            self.seguir()
        elif self.botones["repetir"].actualizar(dt, ctrl):
            if self.mj.id == "fosiles":
                self.app.ir(ExpedicionEscena(self.app))
            elif self.mj.id == "pesca":
                self.app.ir(PescaEscena(self.app))
            else:
                self.app.ir(Partida(self.app, self.mj.id, self.mj.nivel))
        elif self.app.ctx.perfil.fichas > 0 and self.ruleta.actualizar(dt, ctrl):
            self.app.ir(RuletaEscena(self.app, lambda app: Resultado.volver_a(app, self.mj.id)))

    @staticmethod
    def _avisos_pesca(mj):
        """Frases cortas de la partida de pesca: peces nuevos, mundos abiertos y herramientas rotas."""
        if mj.id != "pesca":
            return []
        res = []
        for ev in getattr(mj, "eventos_reg", []):
            if ev[0] == "nuevo" and ev[1] in arte.PECES:
                res.append((f"¡Pez nuevo: {arte.PECES[ev[1]][0]}!", (40, 130, 70)))
            elif ev[0] == "mundo":
                res.append((f"¡Se abrió el {pesca_datos.MUNDOS[ev[1]]['nombre']}!", (200, 90, 40)))
        for r in getattr(mj, "herr_rotas", []):
            res.append((f"Se rompió tu {pesca_datos.NOMBRES_HERR[r['tipo']].lower()} de {r['est']} "
                        f"estrella{'s' if r['est'] != 1 else ''}", (170, 70, 60)))
        return res[:3]

    @staticmethod
    def volver_a(app, juego=None):
        """A que menu volver despues de un minijuego (cada uno vuelve a su propio menu)."""
        if juego == "fosiles":
            return ExpedicionEscena(app)
        if juego == "ruinas":
            return RuinasEscena(app)
        if juego == "espacio":
            return EspacioEscena(app)
        if juego in ("tamagotchi", "horda"):
            return TamagotchiEscena(app)
        return PescaEscena(app) if juego == "pesca" else Libre(app)

    def seguir(self):
        self.app.ir(self.volver_a(self.app, self.mj.id))

    def tecla_esc(self):
        self.seguir()

    def _dibujar_cofre(self, p, cx, cy, ab):
        """Cofre de madera que se abre (ab = 0 cerrado .. 1 abierto)."""
        w, h = 90, 46
        if ab > 0:
            brillo = pygame.Surface((220, 160), pygame.SRCALPHA)
            pygame.draw.circle(brillo, (255, 235, 140, int(90 * ab)), (110, 80), int(30 + 46 * ab))
            p.blit(brillo, (cx - 110, cy - 55))
        base = pygame.Rect(cx - w // 2, cy, w, h)
        pygame.draw.rect(p, (95, 55, 25), base, border_radius=8)
        pygame.draw.rect(p, (150, 92, 45), base.inflate(-8, -8), border_radius=6)
        pygame.draw.rect(p, (240, 200, 70), (cx - 7, cy + 2, 14, h - 6), border_radius=3)
        alto = 30
        if ab <= 0.05:
            tapa = pygame.Rect(cx - w // 2, cy - alto + 6, w, alto)
            pygame.draw.rect(p, (95, 55, 25), tapa, border_radius=12)
            pygame.draw.rect(p, (170, 108, 52), tapa.inflate(-8, -8), border_radius=9)
            pygame.draw.rect(p, (240, 200, 70), (cx - 7, tapa.y, 14, alto), border_radius=3)
            pygame.draw.circle(p, (255, 225, 110), (cx, cy + 6), 7)
        else:
            alza = int(34 * ab)
            pts = [(cx - w // 2 + 4, cy + 2), (cx + w // 2 - 4, cy + 2),
                   (cx + w // 2 - 14, cy - alza), (cx - w // 2 + 14, cy - alza)]
            pygame.draw.polygon(p, (95, 55, 25), pts)
            pygame.draw.polygon(p, (170, 108, 52), [(cx - w // 2 + 12, cy - 2), (cx + w // 2 - 12, cy - 2),
                                                   (cx + w // 2 - 20, cy - alza + 6), (cx - w // 2 + 20, cy - alza + 6)])
            pygame.draw.polygon(p, (60, 35, 18), pts, 3)

    def dibujar(self, p):
        color = COLORES_JUEGO.get(self.mj.id, (90, 150, 230))
        fondo(p, aclarar(color, 0.35), aclarar(color, 0.85))
        panel(p, (ANCHO / 2 - 430, 40, 860, 540), alfa=230)
        titulo = "¡Lo lograste!" if self.superado else "¡Casi! Inténtalo otra vez"
        escribir(p, self.f.grande, titulo, ANCHO / 2, 100, (40, 60, 110) if self.superado else (150, 80, 60),
                 contorno=None)
        if self.mj.mensaje_final:
            escribir(p, self.f.chica, self.mj.mensaje_final, ANCHO / 2, 145, (90, 100, 130), contorno=None)
        for k in range(3):
            lleno = k < self.mostradas
            rad = 52 if lleno else 44
            estrella(p, ANCHO / 2 - 130 + k * 130, 230, rad,
                     (255, 210, 60) if lleno else (205, 210, 225),
                     (160, 110, 20) if lleno else (150, 155, 175))
        escribir(p, self.f.grande, f"{self.mj.puntos} puntos", ANCHO / 2, 312, (40, 60, 110), contorno=None)
        moneda(p, int(ANCHO / 2 - 78), 358, 15)
        escribir(p, self.f.normal, f"+{self.monedas_ganadas} monedas", ANCHO / 2 - 54, 358, (170, 110, 20),
                 ancla="izq", contorno=None)
        if self.record_nuevo:
            escribir(p, self.f.chica, "¡Nuevo récord!", ANCHO / 2 + 175, 312, (230, 120, 40), ancla="izq",
                     contorno=None)
        for k, (txt, col) in enumerate(self.avisos_pesca):
            escribir(p, self.f.chica, txt, 232, 330 + 26 * k, col, ancla="izq", contorno=None)
        botin = list(self.botin.items())
        if botin and self.cofre:
            ab = max(0.0, min(1.0, (self.t_cofre - 1.8) / 0.5))
            self._dibujar_cofre(p, ANCHO / 2 - 200, 415, ab)
            for k, (item, cant) in enumerate(botin[:5]):
                pop = max(0.0, min(1.0, (self.t_cofre - 2.1 - k * 0.18) / 0.3))
                if pop > 0:
                    x = ANCHO / 2 - 80 + k * 76
                    catalogo.dibujar_item(p, item, int(x), int(448 - 24 * pop), max(8, int(56 * pop)))
                    escribir(p, self.f.normal, f"x{cant}", x + 30, 478, (90, 70, 40), ancla="der", contorno=None)
            if ab <= 0:
                escribir(p, self.f.chica, "¡Cofre del tesoro!", ANCHO / 2 + 40, 440, (150, 100, 40), contorno=None)
        elif botin:
            n = min(len(botin), 6)
            x0 = ANCHO / 2 - 62 * (n - 1) / 2
            for k, (item, cant) in enumerate(botin[:n]):
                catalogo.dibujar_item(p, item, int(x0 + k * 62), 410, 40)
                escribir(p, self.f.chica, f"x{cant}", x0 + k * 62 + 22, 428, (90, 70, 40), ancla="der",
                         contorno=None)
        y = 458
        for tipo, ident in self.nuevas[:3]:
            x = ANCHO / 2 - 200 * (len(self.nuevas[:3]) - 1) / 2 + 200 * self.nuevas.index((tipo, ident))
            if tipo == "criatura":
                arte.dibujar_criatura(p, ident, x, y + 30, 0.6, self.t)
                nombre = arte.CRIATURAS[ident][0]
            elif tipo == "dino":
                arte_paleo.dibujar_dino(p, ident, x, y + 28, 0.42, self.t)
                nombre = arte_paleo.DINOS[ident][0]
            else:
                arte.dibujar_pez(p, ident, x, y + 30, 0.9, 1, self.t)
                nombre = arte.PECES[ident][0]
            texto_nuevo = f"¡Página de {nombre}!" if tipo == "dino" else f"¡{nombre} nuevo!"
            escribir(p, self.f.chica, texto_nuevo, x, y + 90, (200, 90, 40), contorno=None)
        if self.app.ctx.perfil.fichas > 0:
            self.ruleta.dibujar(p, self.f.normal)
        elif self.fichas_nuevas:
            pass
        for x in self.particulas:
            x.dibujar(p)
        for b in self.botones.values():
            b.dibujar(p, self.f.grande)


class RuletaEscena(Escena):
    SEGS = ["tiempo", "potencia", "alcance", "lento", "puntos", "vida", "moneda", "sorpresa"]
    COLORES = [(240, 170, 60), (230, 80, 80), (80, 170, 240), (110, 200, 130),
               (240, 210, 70), (240, 120, 180), (160, 130, 230), (90, 210, 200)]
    ETIQ = {"tiempo": "+Tiempo", "potencia": "Fuerza", "alcance": "Alcance", "lento": "Lento",
            "puntos": "Puntos x2", "vida": "+Vida", "moneda": "+30", "sorpresa": "¡Sorpresa!"}

    def __init__(self, app, volver):
        super().__init__(app)
        self.volver_a = volver
        self.ang = random.uniform(0, 360)
        self.vel = 560.0
        self.estado = "girando"
        self.resultado = None
        self.texto = ""
        self.boton = Boton((ANCHO / 2 - 160, 648, 320, 62), "¡PARAR!", (230, 90, 90))
        self.salir = Boton((ANCHO / 2 - 160, 648, 320, 62), "Seguir", (90, 190, 110))
        self.particulas = []
        self.t_giro = 0.0
        self.tick_ang = 0.0

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self.particulas = [x for x in self.particulas if x.actualizar(dt)]
        if self.estado == "girando":
            self.t_giro += dt
            self.ang = (self.ang + self.vel * dt) % 360
            self._tick()
            if self.boton.actualizar(dt, ctrl) or ctrl.golpe or self.t_giro > 7:
                self.estado = "frenando"
        elif self.estado == "frenando":
            self.vel *= math.exp(-1.1 * dt)
            self.ang = (self.ang + self.vel * dt) % 360
            self._tick()
            if self.vel < 6:
                self._resolver()
        else:
            if self.salir.actualizar(dt, ctrl):
                self.app.ir(self.volver_a(self.app))

    def _tick(self):
        paso = int(self.ang // 45)
        if paso != self.tick_ang:
            self.tick_ang = paso
            self.app.ctx.sonidos.reproducir("tick")

    def _resolver(self):
        idx = int(((-self.ang) % 360) // 45)
        nombre = self.SEGS[idx]
        perfil = self.app.ctx.perfil
        perfil.fichas = max(0, perfil.fichas - 1)
        if nombre == "moneda":
            perfil.ganar(30)
            self.texto = "¡30 monedas!"
        elif nombre == "sorpresa":
            elegido = random.choice([m for m in MEJORAS])
            perfil.mejoras[elegido] = USOS_MEJORA + 2
            self.texto = f"¡Sorpresa! {MEJORAS[elegido][1]}  (dura {USOS_MEJORA + 2} juegos)"
        else:
            self.app.ctx.mejoras.agregar(nombre)
            self.texto = f"{MEJORAS[nombre][1]}  (dura {USOS_MEJORA} juegos)"
        self.resultado = nombre
        self.estado = "resultado"
        perfil.guardar()
        self.app.ctx.sonidos.reproducir("premio")
        for _ in range(6):
            explosion(self.particulas, ANCHO / 2 + random.uniform(-250, 250), 328,
                      random.choice([(255, 210, 60), (240, 90, 120), (90, 200, 240), (120, 220, 130)]),
                      n=12, vel_min=100, vel_max=420, vida=1.2, gravedad=400, radio=6)

    def tecla_esc(self):
        self.app.ir(self.volver_a(self.app))

    def dibujar(self, p):
        fondo(p, (90, 60, 170), (210, 150, 235))
        escribir(p, self.f.grande, "¡Ruleta de mejoras!", ANCHO / 2, 38, (255, 235, 120), contorno=(80, 40, 120))
        cx, cy, r = ANCHO // 2, 328, 222
        pygame.draw.circle(p, (60, 30, 110), (cx, cy + 8), r + 18)
        for i, nombre in enumerate(self.SEGS):
            a0 = math.radians(i * 45 + self.ang)
            a1 = math.radians((i + 1) * 45 + self.ang)
            pts = [(cx, cy)]
            for k in range(13):
                a = a0 + (a1 - a0) * k / 12
                pts.append((cx + r * math.sin(a), cy - r * math.cos(a)))
            pygame.draw.polygon(p, self.COLORES[i], pts)
            pygame.draw.polygon(p, (255, 255, 255), pts, 4)
            am = (a0 + a1) / 2
            escribir(p, self.f.chica, self.ETIQ[nombre], cx + r * 0.66 * math.sin(am), cy - r * 0.66 * math.cos(am),
                     (255, 255, 255), contorno=oscurecer(self.COLORES[i], 0.6))
        pygame.draw.circle(p, (255, 255, 255), (cx, cy), 36)
        pygame.draw.circle(p, (255, 210, 60), (cx, cy), 28)
        pygame.draw.polygon(p, (255, 255, 255), [(cx - 26, cy - r - 30), (cx + 26, cy - r - 30), (cx, cy - r + 16)])
        pygame.draw.polygon(p, (230, 60, 80), [(cx - 18, cy - r - 24), (cx + 18, cy - r - 24), (cx, cy - r + 6)])
        if self.estado == "resultado":
            panel(p, (ANCHO / 2 - 420, 578, 840, 58), alfa=240)
            escribir(p, self.f.normal, self.texto, ANCHO / 2, 607, (80, 40, 140), contorno=None)
            for x in self.particulas:
                x.dibujar(p)
            self.salir.dibujar(p, self.f.grande)
        else:
            escribir(p, self.f.chica, "Da un golpe o pulsa PARAR", ANCHO / 2, 610, (255, 255, 255))
            self.boton.dibujar(p, self.f.grande)


class Cuaderno(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.volver = Boton((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.tab = "criaturas"
        self.b_cri = Boton((40, 90, 290, 62), "Criaturas", (90, 190, 110))
        self.b_pez = Boton((340, 90, 290, 62), "Peces", (70, 150, 230))
        self.b_din = Boton((640, 90, 290, 62), "Dinos", (190, 140, 80))
        self.b_rel = Boton((940, 90, 300, 62), "Reliquias", (160, 120, 200))
        self.pagina = None             # id de dinosaurio abierto (pagina grande)
        self.mundo = fosiles_datos.estado(app.ctx.perfil).get("mundo", 0)
        self.mundo_p = pesca_datos.mundo_actual(app.ctx.perfil)     # mundo de pesca que muestra la pestana Peces
        self.m_ant = Boton((ANCHO / 2 - 330, 160, 70, 50), "<", (190, 140, 80))
        self.m_sig = Boton((ANCHO / 2 + 260, 160, 70, 50), ">", (190, 140, 80))
        self.tarjetas = []
        for i in range(6):
            col, fil = i % 3, i // 3
            self.tarjetas.append(Boton((40 + col * 410, 220 + fil * 205, 390, 190), "", (190, 140, 80)))
        self.cerrar = Boton((ANCHO - 330, ALTO - 78, 300, 56), "Cerrar página", (150, 150, 170))
        self.pos = (0, 0)

    def _dinos_mundo(self):
        return fosiles_datos.MUNDOS[self.mundo]["dinos"]

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        perfil = self.app.ctx.perfil
        self.pos = tuple(ctrl.pos)
        if self.pagina is not None:
            if self.cerrar.actualizar(dt, ctrl):
                self.pagina = None
            return
        if self.volver.actualizar(dt, ctrl):
            self.app.ir(Menu(self.app))
            return
        if self.b_cri.actualizar(dt, ctrl):
            self.tab = "criaturas"
        if self.b_pez.actualizar(dt, ctrl):
            self.tab = "peces"
        if self.b_din.actualizar(dt, ctrl):
            self.tab = "dinos"
        if self.b_rel.actualizar(dt, ctrl):
            self.tab = "reliquias"
        if self.tab == "peces":
            if self.m_ant.actualizar(dt, ctrl):
                self.mundo_p = (self.mundo_p - 1) % pesca_datos.NUM_MUNDOS
            if self.m_sig.actualizar(dt, ctrl):
                self.mundo_p = (self.mundo_p + 1) % pesca_datos.NUM_MUNDOS
        if self.tab == "dinos":
            if self.m_ant.actualizar(dt, ctrl):
                self.mundo = (self.mundo - 1) % len(fosiles_datos.MUNDOS)
            if self.m_sig.actualizar(dt, ctrl):
                self.mundo = (self.mundo + 1) % len(fosiles_datos.MUNDOS)
            for ident, b in zip(self._dinos_mundo(), self.tarjetas):
                b.activo = ident in perfil.dinos
                if b.actualizar(dt, ctrl):
                    self.app.ctx.sonidos.reproducir("click")
                    self.pagina = ident

    def tecla_esc(self):
        if self.pagina is not None:
            self.pagina = None
        else:
            self.app.ir(Menu(self.app))

    def _dibujar_pagina(self, p):
        ident = self.pagina
        nombre, periodo, dieta, tamano, dato, color = arte_paleo.DINOS[ident]
        panel(p, (60, 80, ANCHO - 120, 500), alfa=240, radio=26)
        escribir(p, self.f.enorme, nombre, ANCHO / 2, 140, (110, 70, 30), contorno=(255, 245, 220))
        arte_paleo.dibujar_dino(p, ident, 380, 400, 0.85, self.t)
        datos = [("Época", periodo), ("Comida", dieta), ("Tamaño", tamano)]
        for i, (k, v) in enumerate(datos):
            y = 230 + i * 70
            panel(p, (700, y - 28, 480, 60), color=(255, 245, 220), alfa=255, radio=14)
            escribir(p, self.f.chica, k, 720, y - 12, (150, 100, 50), ancla="izq", contorno=None)
            escribir(p, self.f.normal, v, 720, y + 14, (60, 50, 40), ancla="izq", contorno=None)
        panel(p, (700, 440, 480, 110), color=(255, 240, 190), alfa=255, radio=14)
        palabras, lineas, actual = dato.split(), [], ""
        for w in palabras:
            if self.f.chica.size(actual + " " + w)[0] > 440 and actual:
                lineas.append(actual)
                actual = w
            else:
                actual = (actual + " " + w).strip()
        lineas.append(actual)
        for i, l in enumerate(lineas[:3]):
            escribir(p, self.f.chica, l, 720, 468 + i * 30, (80, 60, 40), ancla="izq", contorno=None)
        self.cerrar.dibujar(p, self.f.normal)

    def _dibujar_peces(self, p, perfil):
        """Peces por mundo: arriba los 6 objetivo (llave del siguiente mundo), abajo los de fondo."""
        i = self.mundo_p
        m = pesca_datos.MUNDOS[i]
        reg, tot = pesca_datos.progreso(perfil, i)
        escribir(p, self.f.normal, f"{m['nombre']}  ({reg}/{tot})", ANCHO / 2, 185, (110, 70, 30), contorno=(255, 245, 220))
        self.m_ant.dibujar(p, self.f.normal)
        self.m_sig.dibujar(p, self.f.normal)
        filas = ((pesca_datos.objetivos(i), 320, "Peces objetivo"), (pesca_datos.fondo(i)[:6], 510, "Otros peces de este mundo"))
        for ids, cy, titulo in filas:
            escribir(p, self.f.chica, titulo, 40, cy - 98, (120, 80, 40), ancla="izq", contorno=None)
            for k, ident in enumerate(ids):
                cx = 130 + k * 204
                tiene = pesca_datos.registrado(perfil, ident) or ident in perfil.peces
                panel(p, (cx - 94, cy - 76, 188, 150), alfa=235, radio=16)
                arte.dibujar_pez(p, ident, cx, cy - 10, 0.6, 1, self.t, silueta=not tiene)
                nombre = arte.PECES[ident][0] if tiene else "???"
                escribir(p, self.f.chica, nombre, cx, cy + 54, (80, 60, 40), contorno=None)

    def _dibujar_dinos(self, p, perfil):
        m = fosiles_datos.MUNDOS[self.mundo]
        revividos = sum(1 for d in m["dinos"] if d in perfil.dinos)
        abierto = fosiles_datos.mundo_desbloqueado(perfil, self.mundo)
        escribir(p, self.f.normal, f"{m['nombre']}  ({revividos}/6)", ANCHO / 2, 185, m["color"], contorno=(255, 245, 220))
        self.m_ant.dibujar(p, self.f.normal)
        self.m_sig.dibujar(p, self.f.normal)
        for ident, b in zip(m["dinos"], self.tarjetas):
            r = b.rect
            revivido = ident in perfil.dinos
            panel(p, (r.x, r.y, r.width, r.height), alfa=235, radio=16)
            hall, tot = fosiles_datos.progreso(perfil, ident)
            cx, cy = r.centerx, r.centery - 14
            if revivido:
                arte_paleo.dibujar_dino(p, ident, cx, cy, 0.4, self.t)
                texto = arte_paleo.DINOS[ident][0]
            elif hall:
                arte_paleo.dibujar_esqueleto(p, ident, cx, cy, 0.36, frac=hall / tot)
                texto = f"Huesos {hall}/{tot}"
            else:
                arte_paleo.dibujar_dino(p, ident, cx, cy, 0.4, self.t, silueta=True)
                texto = "???" if not abierto else f"Huesos 0/{tot}"
            escribir(p, self.f.chica, texto, r.centerx, r.bottom - 24, (80, 60, 40), contorno=None)
            if revivido and b.dwell > 0:
                barra(p, (r.x + 14, r.bottom - 12, r.width - 28, 8), b.dwell, color=(255, 230, 90))
        if not abierto:
            escribir(p, self.f.chica, "Revive los 6 del mundo anterior para abrir este mundo", ANCHO / 2, ALTO - 50,
                     (150, 80, 60), contorno=None)
        else:
            escribir(p, self.f.chica, f"Gemas: {perfil.polvo}", ANCHO / 2, ALTO - 50, (110, 70, 130), contorno=None)

    def _dibujar_reliquias(self, p, perfil):
        cuenta = fosiles_datos.estado(perfil)["reliquias"]
        tengo = sum(1 for r in fosiles_datos.ORDEN_RELIQUIAS if cuenta.get(r, 0) > 0)
        elegida = None
        for i, ident in enumerate(fosiles_datos.ORDEN_RELIQUIAS):
            col, fil = i % 6, i // 6
            x, y = 30 + col * 204, 200 + fil * 84
            r = pygame.Rect(x, y, 196, 78)
            n = cuenta.get(ident, 0)
            panel(p, (r.x, r.y, r.width, r.height), alfa=235, radio=14)
            arte_paleo.dibujar_reliquia(p, ident, r.x + 42, r.centery, 0.8, silueta=(n <= 0))
            nombre = arte_paleo.RELIQUIAS_INFO[ident][0] if n > 0 else "???"
            fuente = self.f.chica
            partes = nombre.split()
            if len(partes) > 1 and fuente.size(nombre)[0] > 118:
                escribir(p, fuente, partes[0], r.x + 82, r.centery - 12, (80, 60, 40), ancla="izq", contorno=None)
                escribir(p, fuente, " ".join(partes[1:]), r.x + 82, r.centery + 12, (80, 60, 40), ancla="izq", contorno=None)
            else:
                escribir(p, fuente, nombre, r.x + 82, r.centery, (80, 60, 40), ancla="izq", contorno=None)
            if n > 1:
                escribir(p, fuente, f"x{n}", r.right - 12, r.y + 16, (150, 100, 50), ancla="der", contorno=None)
            if n > 0 and r.collidepoint(self.pos):
                elegida = ident
        if elegida is not None:
            nombre, dato = arte_paleo.RELIQUIAS_INFO[elegida]
            escribir(p, self.f.chica, f"{nombre}: {dato}", ANCHO / 2, 180, (110, 70, 30), contorno=None)
        else:
            escribir(p, self.f.chica, f"Reliquias encontradas: {tengo}/{len(fosiles_datos.ORDEN_RELIQUIAS)}  (toca una para leer)",
                     ANCHO / 2, 180, (110, 70, 130), contorno=None)

    def dibujar(self, p):
        fondo(p, (250, 235, 200), (235, 210, 160))
        perfil = self.app.ctx.perfil
        escribir(p, self.f.grande, "Mi cuaderno", ANCHO / 2, 40, (110, 70, 30), contorno=(255, 245, 220))
        if self.pagina is not None:
            self._dibujar_pagina(p)
            return
        est = fosiles_datos.estado(perfil)
        self.b_cri.texto = f"Criaturas {len(perfil.criaturas)}/{len(arte.CRIATURAS)}"
        self.b_pez.texto = f"Peces {len(set(perfil.peces) | set(pesca_datos.especies_registradas(perfil)))}/{len(arte.PECES)}"
        self.b_din.texto = f"Dinos {len(perfil.dinos)}/{len(fosiles_datos.ORDEN_DINOS)}"
        self.b_rel.texto = f"Reliquias {sum(1 for v in est['reliquias'].values() if v > 0)}/{len(fosiles_datos.RELIQUIAS)}"
        for b in (self.b_cri, self.b_pez, self.b_din, self.b_rel):
            b.dibujar(p, self.f.normal)
        if self.tab == "criaturas":
            for i, ident in enumerate(arte.ORDEN_CRIATURAS):
                col, fil = i % 6, i // 6
                cx, cy = 130 + col * 204, 270 + fil * 200
                tiene = ident in perfil.criaturas
                panel(p, (cx - 92, cy - 90, 184, 180), alfa=235, radio=16)
                arte.dibujar_criatura(p, ident, cx, cy - 14, 0.9, self.t, silueta=not tiene)
                nombre = arte.CRIATURAS[ident][0] if tiene else "???"
                escribir(p, self.f.chica, nombre, cx, cy + 66, (80, 60, 40), contorno=None)
                if tiene:
                    for k in range(arte.CRIATURAS[ident][1]):
                        estrella(p, cx - 14 * (arte.CRIATURAS[ident][1] - 1) + 28 * k - 0, cy - 74, 8)
        elif self.tab == "peces":
            self._dibujar_peces(p, perfil)
        elif self.tab == "dinos":
            self._dibujar_dinos(p, perfil)
        else:
            self._dibujar_reliquias(p, perfil)
        self.volver.dibujar(p, self.f.normal)


# ===================================================================== aplicacion

class Aplicacion:
    def __init__(self, entrada, sonidos=None, fuentes=None, perfil=None):
        self.entrada = entrada
        self.ctx = Contexto(sonidos or Sonidos(), fuentes or Fuentes(),
                            perfil or Perfil(), None)
        self.ctx.mejoras = Mejoras(self.ctx.perfil)
        self.salir = False
        self.escena = Menu(self)

    def ir(self, escena):
        self.escena = escena

    def ir_menu(self):
        self.escena = Menu(self)

    def tecla_esc(self):
        self.escena.tecla_esc()

    def actualizar(self, dt, ctrl):
        self.escena.actualizar(dt, ctrl)

    def dibujar(self, pantalla):
        self.escena.dibujar(pantalla)
