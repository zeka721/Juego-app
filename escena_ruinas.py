"""Menu de las Ruinas Antiguas, con la forma del de Fosiles: 5 mundos de criaturas mitologicas a la izquierda y los 6 murales
del mundo elegido en el centro. Un mundo se abre al completar los 6 murales del anterior (la llave).

RuinasEscena(app)
    Se elige con el cursor (permanencia) o con clic. Al elegir un mural abierto se lanza el minijuego Ruinas con
    Partida y, al terminar, Resultado vuelve a este menu (en el mismo mundo).
"""

import pygame

import arte_ruinas as AR
import ruinas_datos as RD
from ajustes import ANCHO, ALTO
from escena import Escena
from escena_fosiles import centrado, dibujar_candado, dibujar_llave, tarjeta
from escena_items import BotonF, PAPEL, TINTA, TINTA_SUAVE, ajustado, moneda
from nucleo import DWELL_SEG, barra, estrella, panel

VERDE = (40, 130, 60)
ORO = (255, 225, 140)
GRIS = (150, 155, 170)
CLARO = (255, 240, 200)
CONTORNO = (40, 25, 10)

X_CENTRO = 290
W_TARJ, H_TARJ = 312, 240
SEP_X, SEP_Y = 15, 12
Y_TARJ = 134
ALTO_MINI = 146


class RuinasEscena(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.vista = RD.mundo_vista(self.perfil)
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.b_mundos = [BotonF((24, 102 + m * 104, 246, 96), "", RD.MUNDOS[m]["color"]) for m in range(RD.N_MUNDOS)]
        self.cards = []
        for k in range(RD.POR_MUNDO):
            col, fil = k % 3, k // 3
            rect = (X_CENTRO + col * (W_TARJ + SEP_X), Y_TARJ + fil * (H_TARJ + SEP_Y), W_TARJ, H_TARJ)
            self.cards.append(BotonF(rect, "", (150, 120, 70)))
        self.hover = None
        self._minis = {}

    @property
    def perfil(self):
        return self.app.ctx.perfil

    # ------------------------------------------------------------ datos
    def estados(self):
        return RD.datos_estado(self.perfil)

    def abierta(self, i):
        return RD.abierta(self.perfil, i)

    def mundo_abierto(self, m):
        return RD.mundo_desbloqueado(self.perfil, m)

    # ------------------------------------------------------------ acciones
    def _elegir_mundo(self, m):
        self.vista = m
        self.app.ctx.sonidos.reproducir("click")
        if self.mundo_abierto(m):
            RD.elegir_mundo(self.perfil, m)
            self.perfil.guardar()

    def _jugar(self, i):
        from aventura import Partida          # import perezoso: aventura importa este modulo
        self.app.ctx.sonidos.reproducir("click")
        RD.elegir_mundo(self.perfil, RD.mundo_de(i))
        self.perfil.guardar()
        self.app.ir(Partida(self.app, "ruinas", i + 1))

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
        for m, b in enumerate(self.b_mundos):
            if b.actualizar(dt, ctrl):
                self._elegir_mundo(m)
        est = self.estados()
        self.hover = None
        for k, b in enumerate(self.cards):
            i = RD.indice(self.vista, k)
            b.activo = est[i] != "bloqueada"
            if b.activo and b.rect.collidepoint(ctrl.pos.x, ctrl.pos.y):
                self.hover = k
            if b.actualizar(dt, ctrl):
                self._jugar(i)
                return

    # ------------------------------------------------------------ miniaturas
    def _mini(self, i, modo):
        """Mural pequeno con la proporcion de su rompecabezas; 'oscuro' = aun sin descubrir (con las lineas de corte)."""
        clave = (i, modo)
        s = self._minis.get(clave)
        if s is None:
            c, f = RD.RUINAS[i]
            w = int(round(ALTO_MINI * c / f))
            s = AR.mural(i, w, ALTO_MINI).copy()
            if modo == "oscuro":
                s.fill((80, 76, 92), special_flags=pygame.BLEND_RGB_MULT)
                for cc in range(1, c):
                    x = int(cc * w / c)
                    pygame.draw.line(s, (200, 190, 170), (x, 0), (x, ALTO_MINI - 1), 1)
                for rr in range(1, f):
                    y = int(rr * ALTO_MINI / f)
                    pygame.draw.line(s, (200, 190, 170), (0, y), (w - 1, y), 1)
            self._minis[clave] = s
        return s

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        AR.dibujar_fondo(p, RD.indice(self.vista, 0), self.t)
        self._dibujar_cabecera(p)
        self._dibujar_mundos(p)
        self._dibujar_centro(p)
        self.volver.dibujar(p, self.f.normal)
        self._mensaje(p)

    def _dibujar_cabecera(self, p):
        per = self.perfil
        ajustado(p, self.f.grande, "Ruinas Antiguas", 150, 47, 250, CLARO, contorno=CONTORNO)
        panel(p, (290, 12, 440, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        n = RD.total_hechas(per)
        ajustado(p, self.f.normal, f"Murales descubiertos: {n} de {RD.N_RUINAS}", 308, 33, 400, TINTA, ancla="izq")
        barra(p, (306, 52, 408, 18), n / RD.N_RUINAS, color=(255, 190, 40))
        panel(p, (746, 12, 230, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        for k in range(3):
            estrella(p, 786 + k * 52, 47, 18, (255, 210, 60), (160, 110, 20))
        panel(p, (992, 12, 264, 70), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        moneda(p, 1024, 47, 17)
        ajustado(p, self.f.grande, f"{per.monedas:,}".replace(",", "."), 1050, 47, 190, TINTA, ancla="izq")

    def _dibujar_mundos(self, p):
        per = self.perfil
        for m, b in enumerate(self.b_mundos):
            abierto = self.mundo_abierto(m)
            b.color = RD.MUNDOS[m]["color"] if abierto else GRIS
            b.dibujar(p, self.f.normal)
            if m == self.vista:
                pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(12, 12), 5, border_radius=26)
            r = b.rect
            ajustado(p, self.f.normal, RD.MUNDOS[m]["corto"], r.x + 16, r.y + 32, r.width - 100, (255, 255, 255),
                     ancla="izq", contorno=(40, 40, 60))
            if abierto:
                ajustado(p, self.f.chica, f"Murales: {RD.hechas_mundo(per, m)} de {RD.POR_MUNDO}", r.x + 16, r.y + 62,
                         r.width - 100, (255, 255, 255), ancla="izq", contorno=(40, 40, 60))
            else:
                ajustado(p, self.f.chica, "Bloqueado", r.x + 16, r.y + 62, r.width - 100, (255, 255, 255),
                         ancla="izq", contorno=(40, 40, 60))
            ix, iy = r.right - 40, r.centery
            if not abierto:
                dibujar_candado(p, ix, iy + 4, 20)
            elif RD.mundo_completo(per, m):
                if m < RD.N_MUNDOS - 1:
                    dibujar_llave(p, ix - 6, iy, 18)
                else:
                    estrella(p, ix, iy, 16, (255, 220, 60), (160, 110, 20))

    def _dibujar_centro(self, p):
        per = self.perfil
        m = self.vista
        abierto = self.mundo_abierto(m)
        hechas = RD.hechas_mundo(per, m)
        titulo = RD.MUNDOS[m]["nombre"]
        if abierto:
            titulo += f"  ·  {hechas} de {RD.POR_MUNDO} descubiertos"
            if RD.mundo_completo(per, m):
                titulo = RD.MUNDOS[m]["nombre"] + ("  ·  ¡Llave conseguida!" if m < RD.N_MUNDOS - 1 else "  ·  ¡Completo!")
        ajustado(p, self.f.normal, titulo, X_CENTRO + 483, 117, 960, CLARO, contorno=CONTORNO)
        est = self.estados()
        for k, b in enumerate(self.cards):
            self._dibujar_card(p, k, b, est[RD.indice(m, k)])
        if not abierto:
            self._cartel_bloqueado(p, m)

    def _dibujar_card(self, p, k, b, estado):
        i = RD.indice(self.vista, k)
        r = b.rect
        c, f = RD.RUINAS[i]
        color = RD.MUNDOS[self.vista]["color"] if estado != "bloqueada" else GRIS
        tarjeta(p, r, color)
        if self.hover == k and estado != "bloqueada":
            pygame.draw.rect(p, ORO, r, 6, border_radius=18)
        ajustado(p, self.f.normal, AR.NOMBRES[i], r.centerx, r.y + 21, r.width - 20, TINTA)
        zona = pygame.Rect(r.x + 8, r.y + 38, r.width - 16, ALTO_MINI + 8)
        pygame.draw.rect(p, (40, 34, 28), zona, border_radius=10)
        mini = self._mini(i, "color" if estado == "hecha" else "oscuro")
        p.blit(mini, mini.get_rect(center=zona.center))
        if estado == "hecha":
            ganadas = RD.estrellas(self.perfil, i)
            for q in range(3):
                estrella(p, r.centerx - 30 + q * 30, r.y + 224, 11,
                         (255, 210, 60) if q < ganadas else (200, 190, 170),
                         (160, 110, 20) if q < ganadas else (150, 140, 120))
            ajustado(p, self.f.chica, f"¡Descubierto!  ·  {c * f} piedras", r.centerx, r.y + 204, r.width - 20, VERDE)
        elif estado == "abierta":
            ajustado(p, self.f.normal, f"{c * f} piedras", r.centerx, r.y + 204, r.width - 20, TINTA)
            ajustado(p, self.f.chica, "Aún sin descubrir", r.centerx, r.y + 226, r.width - 20, TINTA_SUAVE)
        else:
            ajustado(p, self.f.normal, f"{c * f} piedras", r.centerx, r.y + 204, r.width - 20, TINTA_SUAVE)
            ajustado(p, self.f.chica, "Bloqueado", r.centerx, r.y + 226, r.width - 20, TINTA_SUAVE)
        if b.dwell > 0:
            barra(p, (r.x + 16, r.bottom - 9, r.w - 32, 6), min(1.0, b.dwell / DWELL_SEG), color=(255, 230, 90))

    def _cartel_bloqueado(self, p, m):
        r = pygame.Rect(0, 0, 600, 240)
        r.center = (X_CENTRO + 483, 390)
        pygame.draw.rect(p, (50, 50, 70), r.move(0, 6), border_radius=26)
        panel(p, r, color=(250, 245, 235), alfa=250, radio=26, borde=(110, 115, 135))
        dibujar_candado(p, r.centerx, r.y + 62, 36)
        anterior = RD.MUNDOS[m - 1]["nombre"]
        centrado(p, self.f.normal, f"Descubre los 6 murales del {anterior} para conseguir la llave", r.centerx, r.y + 122,
                 r.width - 50, TINTA, interlineado=36, maximo=3)

    def _mensaje(self, p):
        if not self.mundo_abierto(self.vista):
            texto = "Todavía no tienes la llave de ese mundo."
        else:
            texto = "Elige un mural y arma las piedras. Termina los 6 de un mundo para abrir el siguiente."
        ajustado(p, self.f.chica, texto, 735, ALTO - 50, 960, CLARO, contorno=CONTORNO)
