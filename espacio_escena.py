"""Menu de Defensa Espacial, con la forma del de Ruinas: 8 planetas a la izquierda y, en el centro, las 3 fases
del planeta elegido. Cada fase es una partida aparte que da una pieza. Abajo estan el jefe y el armado del
componente (cada componente sale de dos planetas seguidos).

EspacioEscena(app)
    Al elegir una fase abierta se lanza Partida con el codigo mundo*10 + fase. Al terminar, Resultado vuelve aqui.
"""

import pygame

from ajustes import ANCHO, ALTO
from escena import Escena
from escena_fosiles import dibujar_candado, dibujar_llave, tarjeta
from escena_items import BotonF, PAPEL, TINTA, TINTA_SUAVE, ajustado
from nucleo import DWELL_SEG, barra, estrella, fondo, panel
import espacio_datos as D
from espacio_datos import FASES, componente_de

VERDE = (40, 130, 60)
ORO = (255, 225, 140)
GRIS = (150, 155, 170)
CLARO = (255, 240, 200)
CONTORNO = (20, 14, 40)
BORDE_PAPEL = (90, 60, 30)

X_CENTRO = 290
W_TARJ, H_TARJ = 300, 170
SEP_X, SEP_Y = 15, 12
Y_TARJ = 134


class EspacioEscena(Escena):
    def __init__(self, app):
        super().__init__(app)
        # si acabas de terminar la fase 6, el hub abre en ese mundo y avisa que el jefe te espera
        self.aviso = D.pop_aviso(app.ctx.perfil)
        self.vista = self.aviso - 1 if self.aviso else self._mundo_inicial()
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.hangar = BotonF((ANCHO - 214, ALTO - 78, 190, 56), "Hangar", (90, 130, 220))
        self.b_mundos = [BotonF((24, 102 + m * 66, 246, 58), "", D.MUNDOS[m]["color"]) for m in range(D.N_MUNDOS)]
        self.cards = []
        for f in range(FASES):
            col, fil = f % 3, f // 3
            rect = (X_CENTRO + col * (W_TARJ + SEP_X), Y_TARJ + fil * (H_TARJ + SEP_Y), W_TARJ, H_TARJ)
            self.cards.append(BotonF(rect, "", (150, 120, 70)))
        self.b_jefe = BotonF((X_CENTRO, 508, 470, 76), "", (200, 80, 80))
        self.b_armar = BotonF((X_CENTRO + 485, 508, 470, 76), "", (90, 190, 110))

    @property
    def perfil(self):
        return self.app.ctx.perfil

    def _mundo_inicial(self):
        """Empieza en el mundo mas avanzado que este abierto."""
        abiertos = [n for n in range(1, D.N_MUNDOS + 1) if D.mundo_abierto(self.app.ctx.perfil, n)]
        return abiertos[-1] - 1 if abiertos else 0

    # ------------------------------------------------------------ acciones
    def _elegir_mundo(self, m):
        self.app.ctx.sonidos.reproducir("click")
        self.vista = m

    def _jugar(self, f):
        from aventura import Partida          # import perezoso: aventura importa este modulo
        self.app.ctx.sonidos.reproducir("click")
        self.app.ir(Partida(self.app, "espacio", (self.vista + 1) * 10 + f))

    def _jugar_jefe(self):
        from aventura import Partida
        self.app.ctx.sonidos.reproducir("click")
        self.app.ir(Partida(self.app, "espacio", (self.vista + 1) * 10 + D.JEFE))

    def _armar(self):
        from espacio_rompecabezas import RompecabezasEspacio
        self.app.ctx.sonidos.reproducir("click")
        c = componente_de(self.vista + 1)
        self.app.ir(RompecabezasEspacio(self.app, c, lambda: EspacioEscena(self.app)))

    def _ir_hangar(self):
        from espacio_hangar import HangarEspacio
        self.app.ctx.sonidos.reproducir("click")
        self.app.ir(HangarEspacio(self.app, lambda: EspacioEscena(self.app)))

    def _salir(self):
        from aventura import Libre
        self.app.ctx.sonidos.reproducir("click")
        self.app.ir(Libre(self.app))

    def tecla_esc(self):
        self._salir()

    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        if self.volver.actualizar(dt, ctrl):
            self._salir()
            return
        if self.hangar.actualizar(dt, ctrl):
            self._ir_hangar()
            return
        for m, b in enumerate(self.b_mundos):
            if b.actualizar(dt, ctrl):
                self._elegir_mundo(m)
        m = self.vista
        for f, b in enumerate(self.cards):
            b.activo = D.fase_abierta(self.perfil, m + 1, f + 1)
            if b.actualizar(dt, ctrl):
                self._jugar(f + 1)
                return
        self.b_jefe.activo = D.jefe_abierto(self.perfil, m + 1) and not D.jefe_vencido(self.perfil, m + 1)
        if self.b_jefe.actualizar(dt, ctrl):
            self._jugar_jefe()
            return
        self.b_armar.activo = D.rompecabezas_abierto(self.perfil, componente_de(m + 1))
        if self.b_armar.actualizar(dt, ctrl):
            self._armar()

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        fondo(p, *D.MUNDOS[self.vista]["fondo"])
        self._dibujar_cabecera(p)
        self._dibujar_mundos(p)
        self._dibujar_centro(p)
        self.volver.dibujar(p, self.f.normal)
        self.hangar.dibujar(p, self.f.normal)
        self._mensaje(p)

    def _dibujar_cabecera(self, p):
        per = self.perfil
        ajustado(p, self.f.grande, "Defensa Espacial", 150, 47, 250, CLARO, contorno=CONTORNO)
        panel(p, (290, 12, 440, 70), color=PAPEL, alfa=255, radio=20, borde=BORDE_PAPEL)
        n = sum(len(D.piezas(per, m)) for m in range(1, D.N_MUNDOS + 1))
        ajustado(p, self.f.normal, f"Piezas conseguidas: {n} de {D.N_MUNDOS * FASES}", 308, 33, 400, TINTA,
                 ancla="izq")
        barra(p, (306, 52, 408, 18), n / (D.N_MUNDOS * FASES), color=(255, 190, 40))
        panel(p, (746, 12, 230, 70), color=PAPEL, alfa=255, radio=20, borde=BORDE_PAPEL)
        ajustado(p, self.f.normal, f"Nave: {len(D.componentes(per))}/{D.N_COMPONENTES}", 762, 47, 200, TINTA,
                 ancla="izq")
        panel(p, (992, 12, 264, 70), color=PAPEL, alfa=255, radio=20, borde=BORDE_PAPEL)
        pygame.draw.circle(p, (120, 200, 255), (1024, 47), 17)
        pygame.draw.circle(p, (200, 235, 255), (1024, 47), 17, 3)
        ajustado(p, self.f.grande, str(D.mineral(per)), 1050, 47, 190, TINTA, ancla="izq")

    def _dibujar_mundos(self, p):
        per = self.perfil
        for m, b in enumerate(self.b_mundos):
            abierto = D.mundo_abierto(per, m + 1)
            b.color = D.MUNDOS[m]["color"] if abierto else GRIS
            b.dibujar(p, self.f.normal)
            if m == self.vista:
                pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(12, 12), 5, border_radius=26)
            r = b.rect
            ajustado(p, self.f.normal, D.MUNDOS[m]["corto"], r.x + 16, r.y + 20, r.width - 100, (255, 255, 255),
                     ancla="izq", contorno=(40, 40, 60))
            c = componente_de(m + 1)
            if not abierto:
                texto = "Bloqueado"
            elif D.tiene_componente(per, c):
                texto = "Componente instalado"
            else:
                texto = f"Piezas: {len(D.piezas(per, m + 1))} de {FASES}"
            ajustado(p, self.f.chica, texto, r.x + 16, r.y + 42, r.width - 100, (255, 255, 255), ancla="izq",
                     contorno=(40, 40, 60))
            ix, iy = r.right - 40, r.centery
            if not abierto:
                dibujar_candado(p, ix, iy + 4, 20)
            elif D.tiene_componente(per, c):
                estrella(p, ix, iy, 16, (255, 220, 60), (160, 110, 20))
            elif D.rompecabezas_abierto(per, c):
                dibujar_llave(p, ix - 6, iy, 18)

    def _dibujar_centro(self, p):
        per = self.perfil
        m = self.vista + 1
        abierto = D.mundo_abierto(per, m)
        titulo = D.MUNDOS[self.vista]["nombre"]
        if not abierto:
            titulo += "  ·  Bloqueado"
        elif D.tiene_componente(per, componente_de(m)):
            titulo += "  ·  ¡Componente instalado!"
        ajustado(p, self.f.normal, titulo, X_CENTRO + 485, 117, 960, CLARO, contorno=CONTORNO)
        for f, b in enumerate(self.cards):
            self._dibujar_fase(p, f + 1, b, m)
        self._dibujar_jefe(p, m)
        self._dibujar_armar(p, m)

    def _dibujar_fase(self, p, f, b, m):
        per = self.perfil
        r = b.rect
        abierta = D.fase_abierta(per, m, f)
        hecha = D.fase_hecha(per, m, f)
        color = D.MUNDOS[self.vista]["color"] if abierta else GRIS
        tarjeta(p, r, color)
        if b.encima and b.activo:
            pygame.draw.rect(p, ORO, r, 6, border_radius=18)
        ajustado(p, self.f.normal, f"Fase {f}", r.centerx, r.y + 24, r.width - 20, TINTA)
        # pieza: la que se consigue en esta fase
        tile = pygame.Rect(0, 0, 90, 60)
        tile.center = (r.centerx, r.y + 84)
        pygame.draw.rect(p, D.MUNDOS[self.vista]["color"] if hecha else (200, 195, 190), tile, border_radius=10)
        pygame.draw.rect(p, (60, 40, 20), tile, 3, border_radius=10)
        ajustado(p, self.f.normal, str(f), tile.centerx, tile.centery, 60, (255, 255, 255), contorno=(40, 30, 20))
        if hecha:
            ajustado(p, self.f.chica, "¡Pieza conseguida!", r.centerx, r.y + 134, r.width - 20, VERDE)
            ajustado(p, self.f.chica, "Toca para repetir", r.centerx, r.y + 154, r.width - 20, TINTA_SUAVE)
        elif abierta:
            ajustado(p, self.f.chica, "Disponible", r.centerx, r.y + 134, r.width - 20, TINTA)
        else:
            dibujar_candado(p, r.centerx, r.y + 128, 18)
            ajustado(p, self.f.chica, "Bloqueada", r.centerx, r.y + 154, r.width - 20, TINTA_SUAVE)
        if b.dwell > 0:
            barra(p, (r.x + 16, r.bottom - 9, r.w - 32, 6), min(1.0, b.dwell / DWELL_SEG), color=(255, 230, 90))

    def _dibujar_jefe(self, p, m):
        per = self.perfil
        b = self.b_jefe
        vencido = D.jefe_vencido(per, m)
        abierto = D.jefe_abierto(per, m)
        b.color = (200, 80, 80) if abierto and not vencido else GRIS if not abierto else (120, 170, 120)
        if self.aviso == m:
            pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(14, 14), 6, border_radius=26)
        b.dibujar(p, self.f.normal)
        if vencido:
            texto = f"Jefe de {D.MUNDOS[self.vista]['nombre']} · vencido (toca para repetir)"
        elif abierto:
            texto = f"¡Enfrentar al jefe de {D.MUNDOS[self.vista]['nombre']}!"
        else:
            texto = f"Jefe: consigue las {FASES} piezas"
        ajustado(p, self.f.chica, texto, b.rect.centerx, b.rect.centery, b.rect.width - 30, (255, 255, 255),
                 contorno=(60, 30, 30))

    def _dibujar_armar(self, p, m):
        per = self.perfil
        b = self.b_armar
        c = componente_de(m)
        nombre = D.COMPONENTES[c - 1]["nombre"]
        if D.tiene_componente(per, c):
            b.color = (120, 170, 120)
            texto = f"{nombre} instalado en la nave"
        elif D.rompecabezas_abierto(per, c):
            b.color = (90, 190, 110)
            texto = f"Armar {nombre} y ponerlo en la nave"
        else:
            b.color = GRIS
            texto = f"Armar {nombre}: vence a los dos jefes"
        b.dibujar(p, self.f.normal)
        ajustado(p, self.f.chica, texto, b.rect.centerx, b.rect.centery, b.rect.width - 30, (255, 255, 255),
                 contorno=(30, 60, 30))

    def _mensaje(self, p):
        per = self.perfil
        m = self.vista + 1
        if self.aviso == m:
            texto = f"¡Pieza {FASES} conseguida! Ya puedes enfrentar al jefe de {D.MUNDOS[self.vista]['nombre']}."
            panel(p, (290, 592, 950, 44), color=(255, 240, 200), alfa=240, radio=16, borde=(200, 150, 60))
            ajustado(p, self.f.normal, texto, 765, 614, 920, TINTA)
            return
        if not D.mundo_abierto(per, m):
            if m % 2 == 0:
                texto = f"Vence al jefe de {D.MUNDOS[m - 2]['nombre']} para abrir este planeta."
            else:
                c = componente_de(m - 1)
                texto = f"Arma y pon en la nave el {D.COMPONENTES[c - 1]['nombre']} para abrir este planeta."
        else:
            texto = (f"Cada fase es una partida: consigue su pieza y vuelve aquí. "
                     f"Con las {FASES} piezas, vence al jefe y arma el componente.")
        ajustado(p, self.f.chica, texto, 630, ALTO - 44, 800, CLARO, contorno=CONTORNO)
