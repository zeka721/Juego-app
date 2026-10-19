"""Version del telefono para un solo juego (por ahora: Ruinas). Usa el codigo de siempre, sin tocarlo:
arranca en la pantalla del juego y cualquier 'volver al menu' cierra la app."""

from aventura import Aplicacion


class AppSolo(Aplicacion):
    solo_tama = False

    def __init__(self, entrada, sonidos, fuentes, juego):
        super().__init__(entrada, sonidos, fuentes)
        self.juego = juego
        if juego == "ruinas":
            from escena_ruinas import RuinasEscena
            self.escena = RuinasEscena(self)
        else:
            raise ValueError("juego desconocido: " + juego)

    def ir(self, escena):
        if type(escena).__name__ in ("Libre", "Menu"):      # 'volver' lleva al menu: aqui significa salir
            self.salir = True
        else:
            self.escena = escena

    def ir_menu(self):
        self.salir = True

    def guardar(self):
        try:
            self.ctx.perfil.guardar()
        except Exception:
            pass
