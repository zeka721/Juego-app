"""Version del telefono: arranca directo en el Tamagotchi (sin menu ni los otros juegos)."""

from nucleo import Contexto, Mejoras, Perfil


class AppTama:
    solo_tama = True

    def __init__(self, entrada, sonidos, fuentes, perfil=None):
        self.entrada = entrada
        self.ctx = Contexto(sonidos, fuentes, perfil or Perfil(), None)
        self.ctx.mejoras = Mejoras(self.ctx.perfil)
        self.salir = False
        from escena_tama import TamagotchiEscena
        self._clase = TamagotchiEscena
        self.escena = TamagotchiEscena(self)

    def ir(self, escena):
        self.escena = escena

    def ir_menu(self):
        self.escena = self._clase(self)

    def tecla_esc(self):
        self.escena.tecla_esc()

    def actualizar(self, dt, ctrl):
        self.escena.actualizar(dt, ctrl)

    def dibujar(self, pantalla):
        self.escena.dibujar(pantalla)

    def guardar(self):
        g = getattr(self.escena, "_guardar", None)
        if g:
            g()
