import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Prueba de la aplicacion completa sin pantalla ni mando."""
import os, random, sys, tempfile, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pruebas_util import crear_ctx, pantalla
import pygame
from ajustes import ANCHO, ALTO
from nucleo import ControlSim, Perfil, Sonidos, Fuentes, V2
import aventura as av
random.seed(5)

class FalsaEntrada(ControlSim):
    mando = None
    class espada: calibrada = True
    def centrar(self):
        super().centrar()

def nueva_app():
    p = pantalla()
    ent = FalsaEntrada()
    perfil = Perfil(os.path.join(tempfile.mkdtemp(), "p.json"))
    app = av.Aplicacion(ent, Sonidos(), Fuentes(), perfil)
    return app, ent

def frames(app, ent, n, dt=1/60):
    for _ in range(n):
        app.actualizar(dt, ent)
        app.dibujar(pantalla())
        ent.fin_cuadro()

def click(app, ent, x, y):
    ent.pos = V2(x, y)
    frames(app, ent, 50)       # pasa la espera inicial del boton
    ent.clic = True
    frames(app, ent, 1)

def shot(nombre):
    os.makedirs("/tmp/shots", exist_ok=True)
    pygame.image.save(pantalla(), f"/tmp/shots/app_{nombre}.png")

app, ent = nueva_app()
frames(app, ent, 30); shot("menu")
assert isinstance(app.escena, av.Menu)
# botones nuevos del menu: items, granja, gachapon
from escena_items import ItemsEscena
from escena_granja import GranjaEscena
from escena_gachapon import GachaponEscena
# botones del menu: MINIJUEGOS (izq. arriba), GRANJA, GACHAPON, ITEMS (izq. abajo) y sin AVENTURA
from escena_items import ItemsEscena
from escena_granja import GranjaEscena
from escena_gachapon import GachaponEscena
assert "aventura" not in app.escena.botones and not hasattr(av, "Mapa") and not hasattr(av, "NIVELES")
for cx, cy, clase in ((ANCHO // 2 - 195, 235 + 92 * 2 + 39, ItemsEscena), (ANCHO // 2 + 195, 235 + 39, GranjaEscena),
                      (ANCHO // 2 + 195, 235 + 92 + 39, GachaponEscena)):
    click(app, ent, cx, cy)
    assert isinstance(app.escena, clase), (clase, app.escena)
    frames(app, ent, 20)
    shot("menu_" + clase.__name__)
    app.ir_menu()
    frames(app, ent, 5)
click(app, ent, ANCHO // 2 - 195, 235 + 39)
assert isinstance(app.escena, av.Libre), app.escena
frames(app, ent, 20); shot("libre_menu")
# cocina: ficha de la segunda columna -> Intro -> JUGAR -> Partida
ficha_cocina = [b for i, b in app.escena.fichas if i == "cocina"][0]
click(app, ent, ficha_cocina.rect.centerx, ficha_cocina.rect.centery)
assert isinstance(app.escena, av.Intro), app.escena
frames(app, ent, 10); shot("intro")
click(app, ent, ANCHO // 2, 606)
assert isinstance(app.escena, av.Partida), app.escena
frames(app, ent, 30); shot("cuenta")
frames(app, ent, 200)
shot("partida")
mj = app.escena.mj
mj.puntos = 40
mj.recompensas.append(("criatura", "pelusin"))
mj.terminar("prueba")
frames(app, ent, 5)
assert isinstance(app.escena, av.Resultado), app.escena
frames(app, ent, 120); shot("resultado")
perfil = app.ctx.perfil
print("fichas:", perfil.fichas, "criaturas:", perfil.criaturas)
assert "pelusin" in perfil.criaturas
# ruleta
perfil.fichas = max(1, perfil.fichas)
click(app, ent, ANCHO - 185, 76)
assert isinstance(app.escena, av.RuletaEscena), app.escena
frames(app, ent, 60); shot("ruleta_gira")
ent.golpe = True; frames(app, ent, 1)
frames(app, ent, 60 * 12); 
shot("ruleta_fin")
assert app.escena.estado == "resultado", app.escena.estado
print("ruleta:", app.escena.texto, "| mejoras activas:", perfil.mejoras, "| fichas:", perfil.fichas)
click(app, ent, ANCHO // 2, 650)
assert isinstance(app.escena, av.Libre), app.escena      # la ruleta vuelve al menu del juego (cocina -> Libre)
# cada minijuego suelto, en niveles 1, 3 y 5, con un control erratico
for ident in av.JUEGOS:
    for nivel in (1, 3, 5):
        app.ir(av.Partida(app, ident, nivel))
        for k in range(120 + 200):
            if k % 15 == 0:
                ent.mover_a(random.uniform(0, ANCHO), random.uniform(0, ALTO))
            app.actualizar(1/60, ent); app.dibujar(pantalla()); ent.fin_cuadro()
# cuaderno y libre y final
perfil.criaturas = list(av.arte.CRIATURAS)[:7]; perfil.peces = list(av.arte.PECES)[:3]
app.ir(av.Cuaderno(app)); frames(app, ent, 20); shot("cuaderno")
click(app, ent, 485, 121); frames(app, ent, 5); shot("cuaderno_peces")
import fosiles_datos as fd
perfil.dinos = ["velociraptor", "tiranosaurio", "triceratops"]
fd.estado(perfil)["huesos"] = {"alosaurio": list(range(9)), "carnotauro": list(range(30))}
fd.estado(perfil)["reliquias"] = {"amonita": 1, "diente_gigante": 2, "pluma_fosil": 1}
perfil.polvo = 3
click(app, ent, 785, 121); frames(app, ent, 5); shot("cuaderno_dinos")
assert app.escena.tab == "dinos"
click(app, ent, 1055, 520); frames(app, ent, 5); shot("cuaderno_pagina")
assert app.escena.pagina == "tiranosaurio", app.escena.pagina
click(app, ent, ANCHO - 180, ALTO - 50); assert app.escena.pagina is None
click(app, ent, ANCHO / 2 + 295, 185); frames(app, ent, 5); shot("cuaderno_dinos_mares")
assert app.escena.mundo == 1
click(app, ent, 1090, 121); frames(app, ent, 5)
assert app.escena.tab == "reliquias"
click(app, ent, 120, 240); frames(app, ent, 5); shot("cuaderno_reliquias")
# resultado con pagina de dinosaurio nueva
from j_fosiles import Fosiles
mjd = Fosiles(app.ctx, 1)
mjd.recompensas.append(("dino", "braquiosaurio")); mjd.puntos = 30; mjd.dar("madera", 2); mjd.dar("hierro", 1); mjd.terminar("prueba")
app.ir(av.Resultado(app, mjd)); frames(app, ent, 120); shot("resultado_dino")
assert "braquiosaurio" in perfil.dinos
fd.estado(perfil)["proxima"] = 0
app.ir(av.Libre(app)); frames(app, ent, 20); shot("libre_carrito")
assert fd.zona_lista(perfil)
app.ir(av.Libre(app)); frames(app, ent, 20); shot("libre")
fichas_f = [b for i, b in app.escena.fichas if i == "fosiles"][0]
click(app, ent, fichas_f.rect.centerx, fichas_f.rect.centery)
import escena_fosiles
assert isinstance(app.escena, escena_fosiles.ExpedicionEscena), app.escena
frames(app, ent, 20); shot("expedicion")
app.ir(av.Libre(app))
print("APP OK")
