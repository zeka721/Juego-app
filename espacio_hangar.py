"""Hangar de Defensa Espacial, con dos secciones alineadas:

  - Nave nodriza (izquierda): los 4 componentes, cada uno con sus dos planetas. Un componente con las 6 piezas
    y los dos jefes vencidos se abre tocandolo: abre el rompecabezas para armarlo.
  - Sonda (derecha): 8 tarjetas con la imagen y el color de cada sonda. Tocar una la elige. Abajo se compran
    sus mejoras con mineral; las mejoras son de cada sonda.

HangarEspacio(app, volver)   volver() devuelve la escena a la que se regresa (el hub).
"""

import pygame

from ajustes import ANCHO, ALTO
from escena import Escena
from escena_items import BotonF, PAPEL, TINTA, TINTA_SUAVE, ajustado
from nucleo import escribir, fondo, panel
from espacio_rompecabezas import RompecabezasEspacio
import espacio_dataset as AD
import espacio_datos as D
from espacio_datos import PIEZAS_COMPONENTE

COLOR_COMPRA = (90, 190, 110)
COLOR_BLOQUEADA = (170, 175, 190)
COLOR_ABRIR = (90, 190, 110)
ORO = (255, 225, 140)
STATS = ("hp", "escudo", "arma")
BORDE_PAPEL = (90, 60, 30)

# paneles (ambos misma altura y mismo titulo, para que queden alineados)
PANEL_Y, PANEL_H = 110, 520
NAVE = (40, PANEL_Y, 560, PANEL_H)
SONDA = (640, PANEL_Y, 600, PANEL_H)
# fila de cada componente en la nave
FILA_Y0, FILA_H, FILA_SEP = 190, 80, 12
# tarjetas de sonda: 4 columnas x 2 filas
TARJ_W, TARJ_H, TARJ_SEP = 132, 120, 10
TARJ_Y0 = 160
TARJ_FILA_SEP = 10
# filas de mejora
MEJ_Y0, MEJ_H, MEJ_SEP = 494, 36, 8


class HangarEspacio(Escena):
    def __init__(self, app, volver):
        super().__init__(app)
        self.volver_a = volver
        self.perfil = app.ctx.perfil
        self.k = D.sonda_elegida(self.perfil)
        self.botones_comp = []
        for i in range(D.N_COMPONENTES):
            x, y = NAVE[0] + 20, FILA_Y0 + i * (FILA_H + FILA_SEP)
            self.botones_comp.append(BotonF((x, y, NAVE[2] - 40, FILA_H), "", COLOR_ABRIR))
        self.botones_sonda = []
        for i in range(D.N_SONDAS):
            col, fil = i % 4, i // 4
            x = SONDA[0] + 20 + col * (TARJ_W + TARJ_SEP)
            y = TARJ_Y0 + fil * (TARJ_H + TARJ_FILA_SEP)
            self.botones_sonda.append(BotonF((x, y, TARJ_W, TARJ_H), "", D.SONDAS[i]["color"]))
        self.botones_mejora = {}
        for i, stat in enumerate(STATS):
            self.botones_mejora[stat] = BotonF((SONDA[0] + SONDA[2] - 170, MEJ_Y0 + i * (MEJ_H + MEJ_SEP), 150, MEJ_H),
                                               "", COLOR_COMPRA)
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))

    # ------------------------------------------------------------------ logica
    def _sonido(self, ok):
        self.app.ctx.sonidos.reproducir("ok" if ok else "error")

    def _abrir_rompecabezas(self, c):
        self.app.ctx.sonidos.reproducir("click")
        self.app.ir(RompecabezasEspacio(self.app, c, lambda: HangarEspacio(self.app, self.volver_a)))

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        if self.volver.actualizar(dt, ctrl):
            self.app.ir(self.volver_a())
            return
        for i, b in enumerate(self.botones_comp):
            b.activo = D.rompecabezas_abierto(self.perfil, i + 1)
            if b.actualizar(dt, ctrl):
                self._abrir_rompecabezas(i + 1)
                return
        for i, b in enumerate(self.botones_sonda):
            b.activo = D.sonda_desbloqueada(self.perfil, i)
            if b.actualizar(dt, ctrl):
                ok = D.elegir_sonda(self.perfil, i)
                if ok:
                    self.k = i
                self._sonido(ok)
        for stat in STATS:
            if self.botones_mejora[stat].actualizar(dt, ctrl):
                self._sonido(D.subir_mejora(self.perfil, self.k, stat))

    # ------------------------------------------------------------------ dibujo
    def _texto_compra(self, stat):
        c = D.costo_mejora(self.perfil, self.k, stat)
        return "Máximo" if c is None else f"Mejorar · {c}"

    def _dibujar_nave(self, p):
        per = self.perfil
        panel(p, NAVE, color=PAPEL, alfa=240, radio=22, borde=BORDE_PAPEL)
        ajustado(p, self.f.normal, "Nave nodriza", NAVE[0] + 24, 134, 300, TINTA, ancla="izq")
        ajustado(p, self.f.chica, f"Componentes instalados: {len(D.componentes(per))} de {D.N_COMPONENTES}",
                 NAVE[0] + 24, 166, 500, TINTA_SUAVE, ancla="izq")
        for i, comp in enumerate(D.COMPONENTES):
            c = i + 1
            b = self.botones_comp[i]
            a, z = comp["mundos"]
            abierto = D.mundo_abierto(per, a)
            instalado = D.tiene_componente(per, c)
            armable = D.rompecabezas_abierto(per, c)
            hechas = len(D.piezas_componente(per, c))
            if instalado:
                b.color, estado = (120, 170, 120), "Instalado"
            elif armable:
                b.color, estado = COLOR_ABRIR, "¡Toca para armar!"
            elif abierto:
                b.color, estado = (200, 180, 140), f"Piezas {hechas} de {PIEZAS_COMPONENTE}"
            else:
                b.color, estado = COLOR_BLOQUEADA, "Bloqueado"
            b.dibujar(p, self.f.normal)
            ajustado(p, self.f.normal, f"{c}. {comp['nombre']}", b.rect.x + 14, b.rect.y + 24, 330, (255, 255, 255),
                     ancla="izq", contorno=(40, 40, 60))
            ajustado(p, self.f.chica, f"{D.MUNDOS[a - 1]['nombre']} + {D.MUNDOS[z - 1]['nombre']} · {estado}",
                     b.rect.x + 14, b.rect.y + 52, 330, (255, 255, 255), ancla="izq", contorno=(40, 40, 60))
            if abierto and not instalado:
                tengo = set(D.piezas_componente(per, c))
                for j in range(PIEZAS_COMPONENTE):
                    cx = b.rect.right - 150 + j * 22
                    pygame.draw.circle(p, (255, 220, 90) if (j + 1) in tengo else (235, 235, 240),
                                       (cx, b.rect.centery), 8)
                    pygame.draw.circle(p, (60, 60, 80), (cx, b.rect.centery), 8, 2)
        ajustado(p, self.f.chica, "Cada componente instalado abre los siguientes planetas.",
                 NAVE[0] + 24, NAVE[1] + NAVE[3] - 30, 520, TINTA_SUAVE, ancla="izq")

    def _dibujar_tarjeta_sonda(self, p, i, b):
        sd = D.SONDAS[i]
        desbloqueada = D.sonda_desbloqueada(self.perfil, i)
        b.color = sd["color"] if desbloqueada else COLOR_BLOQUEADA
        b.dibujar(p, self.f.normal)
        if i == self.k:
            pygame.draw.rect(p, ORO, b.rect.inflate(10, 10), 5, border_radius=22)
        img = AD.sonda(i)
        if img is not None:
            img = pygame.transform.smoothscale(img, (120, 47))
            if not desbloqueada:
                img = img.copy()
                img.fill((90, 90, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
            p.blit(img, img.get_rect(center=(b.rect.centerx, b.rect.y + 46)))
        else:
            pygame.draw.circle(p, (255, 255, 255), (b.rect.centerx, b.rect.y + 46), 30, 3)
        ajustado(p, self.f.chica, sd["nombre"], b.rect.centerx, b.rect.bottom - 14, b.rect.w - 12, (255, 255, 255),
                 contorno=(40, 40, 60))
        if not desbloqueada:
            ajustado(p, self.f.chica, f"Vence a {D.MUNDOS[i - 1]['nombre']}", b.rect.centerx, b.rect.y + 14,
                     b.rect.w - 12, (255, 255, 255), contorno=(40, 40, 60))

    def _dibujar_sonda(self, p):
        perfil = self.perfil
        panel(p, SONDA, color=PAPEL, alfa=240, radio=22, borde=BORDE_PAPEL)
        ajustado(p, self.f.normal, "Sonda", SONDA[0] + 24, 134, 300, TINTA, ancla="izq")
        for i, b in enumerate(self.botones_sonda):
            self._dibujar_tarjeta_sonda(p, i, b)
        s = D.SONDAS[self.k]
        ajustado(p, self.f.chica, f"{s['nombre']}: {s['desc']}", SONDA[0] + 24, 426, 552, TINTA, ancla="izq")
        for i, sd in enumerate(D.SONDAS):
            if not D.sonda_desbloqueada(perfil, i):
                ajustado(p, self.f.chica, f"{sd['nombre']} se abre al vencer al jefe de {D.MUNDOS[i - 1]['nombre']}.",
                         SONDA[0] + 24, 446, 552, TINTA_SUAVE, ancla="izq")
                break
        if D.sonda_desbloqueada(perfil, self.k):
            ajustado(p, self.f.normal, f"Mejoras de {s['nombre']}", SONDA[0] + 24, 468, 552, TINTA, ancla="izq")
            m = D.mejoras_sonda(perfil, self.k)
            for i, stat in enumerate(STATS):
                y = MEJ_Y0 + i * (MEJ_H + MEJ_SEP)
                panel(p, (SONDA[0] + 20, y, SONDA[2] - 40, MEJ_H), color=(255, 255, 255), alfa=230, radio=12,
                      borde=(200, 190, 170))
                ajustado(p, self.f.chica, f"{D.NOMBRE_STAT[stat]}  ·  nivel {m[stat]}/{D.MAX_NIVEL[stat]}",
                         SONDA[0] + 34, y + MEJ_H // 2, 360, TINTA, ancla="izq")
                b = self.botones_mejora[stat]
                b.texto = self._texto_compra(stat)
                b.dibujar(p, self.f.normal)

    def dibujar(self, p):
        fondo(p, (10, 12, 40), (40, 40, 100))
        escribir(p, self.f.grande, "Hangar espacial", ANCHO / 2, 46, (255, 255, 255))
        escribir(p, self.f.normal, f"Mineral: {D.mineral(self.perfil)}", ANCHO - 30, 84, (180, 230, 255),
                 ancla="der")
        self._dibujar_nave(p)
        self._dibujar_sonda(p)
        self.volver.dibujar(p, self.f.normal)
