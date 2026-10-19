"""Cuaderno de mascotas (coleccion 18 especies x 4 etapas) y Salon de las mascotas graduadas.

Son "vistas" que usa TamagotchiEscena (no son escenas por si solas):
    vista.actualizar(dt, ctrl) -> True cuando se pide volver
    vista.dibujar(pantalla)
"""

import math

import pygame

import arte_tama as AT
import tama_datos as TD
from ajustes import ANCHO, ALTO
from arte_tama_fx import glow
from escena_tama_ui import (BotonTama, ajustar, escribir_parrafo, flecha, fuente, tarjeta, trofeo, velo, pastilla,
                            silueta_especie)
from nucleo import aclarar, escribir, oscurecer

ESC_CUADERNO = 0.45
CAJA_W, CAJA_H = 196, 112          # espacio maximo de cada mascota en su casilla
_ajustes = {}


def _ajuste(sp, e, esc=ESC_CUADERNO, cw=CAJA_W, ch=CAJA_H):
    """(factor, bajo, desvio_x): reduce las formas muy anchas o altas para que quepan en su casilla."""
    k = (sp, e, round(esc, 3), cw, ch)
    r = _ajustes.get(k)
    if r is None:
        lado = 560
        s = pygame.Surface((lado, lado), pygame.SRCALPHA)
        AT.dibujar_mascota(s, sp, e, lado / 2, lado / 2, esc, 0.0, "feliz", 1)
        bb = s.get_bounding_rect(min_alpha=190)
        if bb.w < 4 or bb.h < 4:
            bb = pygame.Rect(lado // 2 - 20, lado // 2 - 20, 40, 40)
        f = min(1.0, cw / bb.w, ch / bb.h)
        r = (f, bb.bottom - lado / 2, bb.centerx - lado / 2)
        _ajustes[k] = r
    return r
PAPEL = (253, 246, 228)


def _icono_tipo(tipo):
    return lambda p, x, y, t: AT.dibujar_icono_tipo(p, tipo, x, y, t * 0.5)


class LibroCuaderno:
    def __init__(self, esc):
        self.e = esc
        m = esc.m
        self.pag = TD.TIPOS.index(TD.ESPECIES[m["especie"]]["tipo"]) if m is not None else 0
        self.tabs = []
        for i, tipo in enumerate(TD.TIPOS):
            col = AT.COLOR_TIPO[tipo]
            self.tabs.append(BotonTama((20, 84 + i * 82, 134, 76), AT.NOMBRE_TIPO[tipo], col, _icono_tipo(tipo),
                                       True, 56, False, 18))
        self.b_volver = BotonTama((20, 584, 134, 66), "Volver", (140, 150, 190), "volver", False, 38, False, 22)
        self.t = 0.0

    def actualizar(self, dt, ctrl):
        self.t += dt
        for i, b in enumerate(self.tabs):
            if b.actualizar(dt, ctrl) and i != self.pag:
                self.pag = i
                self.e._sonido("click")
        if self.b_volver.actualizar(dt, ctrl):
            self.e._sonido("click")
            return True
        return False

    def _total(self):
        desc = self.e.st["descubiertas"]
        return sum(int(v) + 1 for v in desc.values())

    def dibujar(self, p):
        esc = self.e
        AT.dibujar_fondo_hogar(p, esc.t, False)
        velo(p, 110, (60, 40, 30))
        escribir(p, esc.f.grande, "Cuaderno de Mascotas", 166, 42, (255, 250, 235), "izq", contorno=(110, 60, 30), grosor=3)
        escribir(p, fuente(26), f"Descubiertas: {self._total()} de {len(TD.ORDEN) * 4}", ANCHO - 30, 44, (255, 235, 150),
                 "der", contorno=(110, 60, 30))
        tipo = TD.TIPOS[self.pag]
        col = AT.COLOR_TIPO[tipo]
        hoja = pygame.Rect(166, 80, 1096, 566)
        tarjeta(p, hoja, PAPEL, 255, 26, oscurecer(col, 0.35), 6)
        # espiral del cuaderno
        for i in range(9):
            y = hoja.y + 46 + i * 60
            pygame.draw.circle(p, (120, 100, 90), (hoja.x + 6, y), 9)
            pygame.draw.circle(p, (225, 215, 200), (hoja.x + 6, y), 5)
        desc = esc.st["descubiertas"]
        especies = [e for e in TD.ORDEN if TD.ESPECIES[e]["tipo"] == tipo]
        for fila, sp in enumerate(especies):
            y0 = hoja.y + 14 + fila * 182
            et_max = desc.get(sp, -1)
            # columna izquierda: icono de tipo y nombre del animal
            pygame.draw.circle(p, aclarar(col, 0.55), (238, y0 + 62), 40)
            pygame.draw.circle(p, oscurecer(col, 0.3), (238, y0 + 62), 40, 4)
            AT.dibujar_icono_tipo(p, tipo, 238, y0 + 62, 30)
            animal = TD.ESPECIES[sp]["animal"].capitalize() if et_max >= 0 else "???"
            escribir(p, ajustar(22, animal, 112, 14), animal, 238, y0 + 128, (100, 70, 50), contorno=None)
            for e in range(4):
                x = 306 + e * 238
                r = pygame.Rect(x, y0, 226, 170)
                conocido = e <= et_max
                tarjeta(p, r, aclarar(col, 0.82) if conocido else (232, 228, 222), 255, 20,
                        col if conocido else (175, 170, 165), 3, False)
                escribir(p, fuente(17), TD.ETAPAS[e], r.x + 14, r.y + 18, oscurecer(col, 0.35) if conocido else (150, 145, 140),
                         "izq", contorno=None)
                f, bajo, dx = _ajuste(sp, e)
                cy = r.y + 134 - bajo * f
                cxm = r.centerx - dx * f
                if conocido:
                    AT.dibujar_mascota(p, sp, e, cxm, cy, ESC_CUADERNO * f, self.t + fila + e, "feliz", 1)
                else:
                    s = silueta_especie(sp, e, ESC_CUADERNO * f)
                    p.blit(s, s.get_rect(center=(int(cxm), int(cy))))
                if conocido:
                    nombre = TD.ESPECIES[sp]["formas"][e]
                    escribir(p, ajustar(22, nombre, r.w - 20, 14), nombre, r.centerx, r.bottom - 15, (90, 60, 40), contorno=None)
                else:
                    escribir(p, fuente(24), "???", r.centerx, r.bottom - 15, (150, 145, 140), contorno=None)
                if e < 3:
                    flecha(p, r.right + 6, r.centery, 7, 1, oscurecer(col, 0.2) if e < et_max else (190, 185, 180), (255, 255, 255))
        for i, b in enumerate(self.tabs):
            if i == self.pag:
                original = pygame.Rect(b.rect)
                b.rect = pygame.Rect(original.x, original.y - 3, original.w + 16, original.h + 6)
                b.dibujar(p, None, self.t)
                pygame.draw.rect(p, (255, 225, 90), b.rect.inflate(2, 2), 4, border_radius=24)
                b.rect = original
            else:
                b.dibujar(p, None, self.t)
        self.b_volver.dibujar(p, None, self.t)


class LibroSalon:
    POR_PAGINA = 8

    def __init__(self, esc):
        self.e = esc
        self.pag = 0
        self.t = 0.0
        self.b_volver = BotonTama((ANCHO // 2 - 110, 628, 220, 76), "Volver", (140, 150, 190), "volver", False, 40, False, 28)
        self.b_prev = BotonTama((ANCHO // 2 - 330, 628, 100, 76), "", (90, 150, 225), lambda p, x, y, t: flecha(p, x, y, 22, -1),
                                False, 30)
        self.b_next = BotonTama((ANCHO // 2 + 230, 628, 100, 76), "", (90, 150, 225), lambda p, x, y, t: flecha(p, x, y, 22, 1),
                                False, 30)
        self.banner = ""
        self.t_banner = 0.0

    def celebrar(self, nombre):
        self.banner = f"¡{nombre} ya está en el Salón!"
        self.t_banner = 5.0
        for _ in range(60):
            self.e.parts.confeti(ANCHO / 2, 330)

    def _paginas(self):
        n = len(self.e.st["salon"])
        return max(1, (n + self.POR_PAGINA - 1) // self.POR_PAGINA)

    def actualizar(self, dt, ctrl):
        self.t += dt
        self.t_banner = max(0.0, self.t_banner - dt)
        n = self._paginas()
        if n > 1:
            if self.b_prev.actualizar(dt, ctrl):
                self.pag = (self.pag - 1) % n
                self.e._sonido("click")
            if self.b_next.actualizar(dt, ctrl):
                self.pag = (self.pag + 1) % n
                self.e._sonido("click")
        if self.b_volver.actualizar(dt, ctrl):
            self.e._sonido("click")
            return True
        return False

    def dibujar(self, p):
        esc = self.e
        AT.dibujar_fondo_hogar(p, esc.t, True)
        velo(p, 90, (50, 20, 90))
        for i in range(14):
            a = (math.sin(self.t * 1.6 + i * 1.9) + 1) / 2
            glow(p, 90 + (i * 197) % 1100, 120 + (i * 83) % 480, 16, (255, 235, 150), int(150 * a))
        trofeo(p, ANCHO // 2 - 300, 40, 62)
        trofeo(p, ANCHO // 2 + 300, 40, 62)
        escribir(p, esc.f.grande, "Salón de las Mascotas", ANCHO / 2, 38, (255, 235, 150), contorno=(90, 50, 20), grosor=3)
        salon = esc.st["salon"]
        if not salon:
            r = pygame.Rect(0, 0, 760, 300)
            r.center = (ANCHO // 2, 340)
            tarjeta(p, r, (255, 248, 235), 240, 30, (200, 150, 60), 5)
            trofeo(p, r.centerx, r.y + 90, 120)
            escribir(p, fuente(34), "Aquí aparecerán tus mascotas campeonas", r.centerx, r.y + 190, (150, 100, 40), contorno=None)
            escribir_parrafo(p, fuente(24), "Cuando una mascota llegue a la forma Ultimate, ¡podrá pasar al Salón!", r.centerx,
                             r.y + 238, 680, (130, 100, 70), None)
        else:
            pagina = salon[self.pag * self.POR_PAGINA:(self.pag + 1) * self.POR_PAGINA]
            cw, ch, g = 270, 236, 16
            x0 = (ANCHO - (4 * cw + 3 * g)) // 2
            for i, s in enumerate(pagina):
                col_i, fil = i % 4, i // 4
                r = pygame.Rect(x0 + col_i * (cw + g), 116 + fil * (ch + g), cw, ch)
                tipo = TD.ESPECIES[s["especie"]]["tipo"]
                col = AT.COLOR_TIPO[tipo]
                tarjeta(p, r, aclarar(col, 0.8), 245, 24, (230, 175, 50), 5)
                glow(p, r.centerx, r.y + 100, 100, aclarar(col, 0.4), 70)
                pygame.draw.ellipse(p, (230, 215, 190), (r.centerx - 80, r.y + 148, 160, 28))
                pygame.draw.ellipse(p, (170, 140, 100), (r.centerx - 80, r.y + 148, 160, 28), 3)
                e = s["etapa"]
                esc_m = 120.0 / AT.ALTO_ETAPA[e]
                f, bajo, dx = _ajuste(s["especie"], e, esc_m, 226, 124)
                AT.dibujar_mascota(p, s["especie"], e, r.centerx - dx * f, r.y + 160 - bajo * f, esc_m * f, self.t + i, "feliz", 1)
                AT.dibujar_icono_tipo(p, tipo, r.x + 26, r.y + 26, 15)
                trofeo(p, r.right - 28, r.y + 30, 34)
                escribir(p, ajustar(28, s["nombre"], r.w - 24, 16), s["nombre"], r.centerx, r.bottom - 26, (100, 60, 30),
                         contorno=None)
            n = self._paginas()
            if n > 1:
                self.b_prev.dibujar(p, None, self.t)
                self.b_next.dibujar(p, None, self.t)
                escribir(p, fuente(24), f"Página {self.pag + 1} de {n}", ANCHO - 150, 668, (255, 240, 200), contorno=(60, 30, 80))
        self.b_volver.dibujar(p, None, self.t)
        if self.t_banner > 0:
            pastilla(p, fuente(32), self.banner, ANCHO / 2, 90, (255, 245, 210), (150, 90, 20), (230, 175, 50), 34, 42)
