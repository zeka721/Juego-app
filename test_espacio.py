"""Pruebas de Defensa Espacial: 8 planetas, fases (una pieza por partida), jefes, componentes de 6 piezas,
sondas, mineral, hub, hangar, dataset y capturas."""
import os
import random
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from pruebas_util import crear_ctx, capturar, simular, AppFalsa, escena_simular, capturar_escena

import pygame
from ajustes import ALTO, ANCHO
from nucleo import ControlSim, V2
import j_espacio as E
import espacio_datos as D
from espacio_hangar import HangarEspacio
from espacio_escena import EspacioEscena
from espacio_rompecabezas import RompecabezasEspacio, celda, SLOTS

SHOTS = "/tmp/shots/"
os.makedirs(SHOTS, exist_ok=True)


def bot_bueno(juego, ctrl, t):
    """La sonda se pone a la altura del meteorito mas cercano que viene hacia ella."""
    ctrl.pos = V2(300, 360)
    cerca = None
    for m in juego.meteoros:
        if m["x"] > 260 and (cerca is None or m["x"] < cerca["x"]):
            cerca = m
    if cerca is not None:
        ctrl.pos = V2(300, min(max(cerca["y"], 130), ALTO - 50))
    if int(t) % 9 == 8 and abs(t - round(t)) < 1 / 120:
        ctrl.golpe = True


def bot_jefe(juego, ctrl, t):
    """Contra el jefe: la sonda sigue su altura para que los disparos den en el blanco."""
    if juego.modo == "boss" and juego.boss:
        ctrl.pos = V2(260, juego.boss["y"])
    else:
        bot_bueno(juego, ctrl, t)


def bot_inerte(juego, ctrl, t):
    ctrl.pos = V2(120, 130)


def clic_en(escena, ctrl, pos):
    """Un clic en 'pos' (un cuadro)."""
    ctrl.pos = V2(*pos)
    ctrl.clic = True
    escena.actualizar(1 / 60, ctrl)
    ctrl.fin_cuadro()


def pulsar(escena, ctrl, boton, segundos=1.2):
    """Espera la entrada del boton (dwell) y lo pulsa una vez."""
    cen = boton.rect.center
    hecho = []

    def bot(e, c, t):
        c.pos = V2(*cen)
        c.clic = t > 0.7 and not hecho
        if c.clic:
            hecho.append(t)

    escena_simular(escena, ctrl, bot, segundos=segundos)


def _meteoro(x, y, hp=1, vx=0.0):
    return dict(tipo="peq", x=float(x), y=float(y), vx=vx, vy=0.0, r=26.0, hp=hp, ang=0.0, giro=0.0, semilla=0)


def _dar_piezas(perfil, n):
    for f in range(1, D.FASES + 1):
        D.guardar_pieza(perfil, n, f)


def test_area_de_impacto_de_la_sonda():
    ctx = crear_ctx()
    j = E.Espacio(ctx, 11)
    j.sx, j.sy = 300.0, 360.0
    assert j._toca_sonda(300, 360, 1)                       # centro
    assert j._toca_sonda(300 + 142 + 5, 360, 10)            # borde derecho + radio: toca
    assert not j._toca_sonda(300 + 142 + 30, 360, 10)       # fuera del rectangulo
    assert j._toca_sonda(300, 360 + 56 + 5, 10)             # borde inferior + radio: toca
    assert not j._toca_sonda(300, 360 + 56 + 30, 10)
    print("area de impacto de la sonda ok")


def test_datos_y_apertura():
    ctx = crear_ctx()
    perfil = ctx.perfil
    assert [m["nombre"] for m in D.MUNDOS] == ["Mercurio", "Venus", "Tierra", "Marte", "Júpiter", "Saturno",
                                               "Urano", "Neptuno"]
    assert len(D.COMPONENTES) == 4 and D.PIEZAS_COMPONENTE == 6
    assert [c["mundos"] for c in D.COMPONENTES] == [(1, 2), (3, 4), (5, 6), (7, 8)]
    assert [s["arma"] for s in D.SONDAS[:6]] == [0, 1, 2, 3, 4, 5] and len(D.SONDAS) == 8
    assert D.mundo_abierto(perfil, 1) and not D.mundo_abierto(perfil, 2)
    assert D.fase_abierta(perfil, 1, 1) and not D.fase_abierta(perfil, 1, 2)
    assert D.sonda_desbloqueada(perfil, 0) and not D.sonda_desbloqueada(perfil, 1)
    assert [D.componente_de(n) for n in range(1, 9)] == [1, 1, 2, 2, 3, 3, 4, 4]
    print("datos y apertura ok")


def test_fase_da_una_pieza_y_sale():
    random.seed(3)
    ctx = crear_ctx()
    j = E.Espacio(ctx, 11)
    assert j.mundo["nombre"] == "Mercurio" and j.fase == 1 and not j.jefe_modo
    ctrl = ControlSim()
    simular(j, ctrl, bot_bueno, segundos=90)
    print(f"fase 1: vidas={j.vidas} mineral={D.mineral(ctx.perfil)} derribados={j.derribados} msg={j.mensaje_final}")
    assert j.terminado and j.ganado is True, (j.terminado, j.ganado, j.vidas)
    assert D.piezas(ctx.perfil, 1) == [1], D.piezas(ctx.perfil, 1)
    assert "Pieza 1" in j.mensaje_final
    assert D.mineral(ctx.perfil) <= 25, "el mineral por fase no debe ser excesivo"
    print("fase da una pieza y sale ok")


def test_fases_suben_la_dificultad():
    ctx = crear_ctx()
    f1 = E.Espacio(ctx, 11)
    f3 = E.Espacio(ctx, 13)
    assert f3.calcular_metas()[0] > f1.calcular_metas()[0]
    assert f3._velocidad() > f1._velocidad()
    assert f3._ritmo() < f1._ritmo()
    print("dificultad sube por fase ok")


def test_jefe_mercurio_abre_venus():
    random.seed(5)
    ctx = crear_ctx()
    perfil = ctx.perfil
    _dar_piezas(perfil, 1)
    assert D.jefe_abierto(perfil, 1) and not D.mundo_abierto(perfil, 2)
    j = E.Espacio(ctx, 14)
    assert j.jefe_modo and j.boss is not None
    j.vidas = 99                       # prueba del jefe, no de la dificultad
    ctrl = ControlSim()
    simular(j, ctrl, bot_jefe, segundos=240)
    assert j.terminado and j.ganado is True, (j.terminado, j.ganado)
    assert D.jefe_vencido(perfil, 1) and D.mineral(perfil) >= D.MINERAL_JEFE
    assert D.mundo_abierto(perfil, 2) and not D.mundo_abierto(perfil, 3)
    assert D.sonda_desbloqueada(perfil, 1) and not D.sonda_desbloqueada(perfil, 2)
    assert "sonda 2" in j.mensaje_final, j.mensaje_final
    print("jefe de Mercurio abre Venus ok")


def test_componente_1_con_mercurio_y_venus():
    ctx = crear_ctx()
    perfil = ctx.perfil
    _dar_piezas(perfil, 1)
    D.guardar_jefe(perfil, 1)
    _dar_piezas(perfil, 2)
    D.guardar_jefe(perfil, 2)
    assert D.piezas_componente(perfil, 1) == [1, 2, 3, 4, 5, 6]
    assert D.rompecabezas_abierto(perfil, 1) and not D.rompecabezas_abierto(perfil, 2)
    assert D.instalar_componente(perfil, 1)
    assert D.componentes(perfil) == [1]
    assert D.mundo_abierto(perfil, 3) and not D.mundo_abierto(perfil, 4)
    assert not D.instalar_componente(perfil, 1)           # ya estaba instalado
    print("componente 1 con Mercurio y Venus ok")


def test_jefe_patrones_y_aviso():
    random.seed(6)
    ctx = crear_ctx()
    j = E.Espacio(ctx, 14)
    j.boss["hp"] = 10 ** 6
    j.vidas = 99
    ctrl = ControlSim()
    vistos, avisos, disparos = set(), 0, 0
    t, dt = 0.0, 1 / 60
    while t < 40:
        ctrl.pos = V2(260, 140)
        j.actualizar(dt, ctrl)
        ctrl.fin_cuadro()
        b = j.boss
        if b and b["patron"]:
            vistos.add(b["patron"])
            if b["tel"] > 0:
                avisos += 1
        disparos = max(disparos, len(j.balas_enemigas))
        assert j.meteoros == [], "no hay meteoritos mientras esta el jefe"
        t += dt
    assert vistos == set(E.PATRONES), vistos
    assert avisos > 0 and disparos > 0
    print("patrones y aviso ok:", sorted(vistos))


def test_inerte_pierde_y_no_da_pieza():
    random.seed(4)
    ctx = crear_ctx()
    j = E.Espacio(ctx, 11)
    j.vidas = 1                        # una sola vida: un golpe basta
    ctrl = ControlSim()
    simular(j, ctrl, bot_inerte, segundos=200)
    assert j.terminado and j.ganado is False
    assert "sin energía" in j.mensaje_final, j.mensaje_final
    assert D.piezas(ctx.perfil, 1) == []
    print("inerte pierde ok")


def test_pierce_y_explosivo():
    ctx = crear_ctx()
    perfil = ctx.perfil
    D.datos(perfil)["jefes"] = [1, 2, 3, 4]               # desbloquea hasta la explosiva (k=4)
    D.elegir_sonda(perfil, 2)
    j = E.Espacio(ctx, 11)
    assert j.k == 2 and j.arma == 2
    ctrl = ControlSim()
    j.cadencia = 99                                       # sin disparos automaticos
    j.meteoros = [_meteoro(500, 360), _meteoro(600, 360), _meteoro(700, 360)]
    j.balas = [dict(x=480.0, y=360.0, vx=900.0, vy=0.0, ttl=1.3, pierce=3, ya=[])]
    ctrl.pos = V2(260, 360)                               # la sonda se queda donde esta
    for _ in range(40):
        j.paso(1 / 60, ctrl)
    assert j.derribados == 3, j.derribados                # una bala atraviesa los tres
    D.elegir_sonda(perfil, 4)
    j2 = E.Espacio(ctx, 11)
    assert j2.k == 4 and j2.arma == 4
    j2.cadencia = 99
    j2.meteoros = [_meteoro(600, 360), _meteoro(620, 390), _meteoro(640, 330)]
    j2.misiles = [dict(x=560.0, y=360.0, ang=0.0, ttl=3.0, dmg=2, guiado=False, aoe=True)]
    for _ in range(40):
        j2.paso(1 / 60, ctrl)
    assert j2.derribados >= 2, j2.derribados               # la explosion alcanza a varios
    print("perforante y explosivo ok")


def test_sondas_7_y_8_disparan_como_la_basica():
    ctx = crear_ctx()
    perfil = ctx.perfil
    D.datos(perfil)["jefes"] = [1, 2, 3, 4, 5, 6, 7]
    for k in (6, 7):
        assert D.elegir_sonda(perfil, k)
        j = E.Espacio(ctx, 11)
        assert j.k == k and j.arma == 0, (j.k, j.arma)
    print("sondas 7 y 8 disparan como la basica ok")


def test_sonda_bloqueada_no_se_elige():
    ctx = crear_ctx()
    perfil = ctx.perfil
    D.datos(perfil)["elegida"] = 5
    j = E.Espacio(ctx, 11)
    assert j.k == 0
    assert not D.elegir_sonda(perfil, 5)
    print("sonda bloqueada no se elige ok")


def test_mejoras_y_no_transferibles():
    ctx = crear_ctx()
    perfil = ctx.perfil
    D.datos(perfil)["mineral"] = 500
    assert D.costo_mejora(perfil, 0, "arma") == 10
    assert not D.subir_mejora(perfil, 1, "arma")          # la doble esta bloqueada
    assert D.subir_mejora(perfil, 0, "arma")
    assert D.mineral(perfil) == 490
    assert D.mejoras_sonda(perfil, 0)["arma"] == 1
    assert D.costo_mejora(perfil, 0, "arma") == 25
    D.datos(perfil)["mineral"] = 10 ** 6
    for _ in range(8):
        D.subir_mejora(perfil, 0, "escudo")
    assert D.mejoras_sonda(perfil, 0)["escudo"] == D.MAX_NIVEL["escudo"]
    assert D.costo_mejora(perfil, 0, "escudo") is None
    D.datos(perfil)["jefes"] = [1]
    assert D.sonda_desbloqueada(perfil, 1)
    assert D.mejoras_sonda(perfil, 1)["escudo"] == 0      # cada sonda guarda las suyas
    assert D.costo_mejora(perfil, 1, "arma") == 15
    print("mejoras ok")


def test_hub_fases_y_jefe():
    app = AppFalsa()
    ctrl = ControlSim()
    esc = EspacioEscena(app)
    assert len(esc.b_mundos) == 8 and len(esc.cards) == 3
    pulsar(esc, ctrl, esc.cards[1])                       # fase 2 bloqueada: no pasa nada
    assert type(app.escena).__name__ != "Partida"
    pulsar(esc, ctrl, esc.cards[0])                       # fase 1 abierta
    assert type(app.escena).__name__ == "Partida" and app.escena.mj.nivel == 11, type(app.escena).__name__
    print("hub: fase abierta lanza la partida ok")


def test_hub_rompecabezas_completo():
    app = AppFalsa()
    perfil = app.ctx.perfil
    _dar_piezas(perfil, 1)
    D.guardar_jefe(perfil, 1)
    _dar_piezas(perfil, 2)
    D.guardar_jefe(perfil, 2)
    ctrl = ControlSim()
    esc = EspacioEscena(app)
    pulsar(esc, ctrl, esc.b_armar)
    rom = app.escena
    assert isinstance(rom, RompecabezasEspacio), type(rom).__name__
    assert rom.n == 1 and len(rom.bandeja) == 6
    # armar: cada pieza de la bandeja, a su hueco
    while rom.bandeja:
        f = rom.bandeja[0]
        clic_en(rom, ctrl, rom._pieza_rect(0).center)
        clic_en(rom, ctrl, celda(f).center)
    assert rom.estado == "mano", rom.estado
    # instalar: primero un hueco equivocado, luego el suyo
    clic_en(rom, ctrl, SLOTS[2])
    assert D.componentes(perfil) == []
    clic_en(rom, ctrl, SLOTS[1])
    assert D.componentes(perfil) == [1], D.componentes(perfil)
    assert rom.estado == "listo"
    assert D.mundo_abierto(perfil, 3)
    capturar_escena(esc, SHOTS + "espacio_hub.png")
    # otra vuelta: el componente en la mano, a punto de instalar
    perfil.guardar()
    rom2 = RompecabezasEspacio(app, 2, lambda: None)
    rom2.colocadas = set(range(1, D.PIEZAS_COMPONENTE + 1))
    rom2.bandeja = []
    rom2.estado = "mano"
    rom2.cursor = (SLOTS[2][0] - 40, SLOTS[2][1] + 40)
    capturar_escena(rom2, SHOTS + "espacio_rompecabezas_mano.png")
    print("rompecabezas completo ok")


def test_hangar_desde_hub():
    app = AppFalsa()
    ctrl = ControlSim()
    esc = EspacioEscena(app)
    pulsar(esc, ctrl, esc.hangar)
    assert isinstance(app.escena, HangarEspacio), type(app.escena).__name__
    print("hangar desde hub ok")


def test_hangar_abre_rompecabezas_desde_la_nave():
    app = AppFalsa()
    perfil = app.ctx.perfil
    _dar_piezas(perfil, 1)
    D.guardar_jefe(perfil, 1)
    _dar_piezas(perfil, 2)
    D.guardar_jefe(perfil, 2)
    ctrl = ControlSim()
    esc = HangarEspacio(app, lambda: "hub")
    pulsar(esc, ctrl, esc.botones_comp[1])               # Tierra + Marte: aun bloqueado
    assert not isinstance(app.escena, RompecabezasEspacio)
    pulsar(esc, ctrl, esc.botones_comp[0])               # Mercurio + Venus: listo para armar
    assert isinstance(app.escena, RompecabezasEspacio), type(app.escena).__name__
    print("hangar abre rompecabezas ok")


def test_capturas():
    random.seed(9)
    ctx = crear_ctx()
    j = E.Espacio(ctx, 13)
    ctrl = ControlSim()
    simular(j, ctrl, bot_bueno, segundos=35)
    capturar(j, SHOTS + "espacio_fase_juego.png")
    jb = E.Espacio(ctx, 14)
    jb.boss["patron"] = "anillo"
    jb.boss["tel"] = 0.5
    jb.boss["tel0"] = 1.0
    capturar(jb, SHOTS + "espacio_boss.png")
    capturar_escena(HangarEspacio(AppFalsa(), lambda: None), SHOTS + "espacio_hangar.png")
    print("capturas en", SHOTS)


def test_aviso_del_jefe_tras_ultima_fase():
    ctx = crear_ctx()
    perfil = ctx.perfil
    D.guardar_pieza(perfil, 1, 1)
    D.guardar_pieza(perfil, 1, 2)
    j = E.Espacio(ctx, 13)                # fase 3 de Mercurio
    ctrl = ControlSim()
    simular(j, ctrl, bot_bueno, segundos=90)
    assert D.piezas(perfil, 1) == [1, 2, 3]
    assert D.jefe_abierto(perfil, 1)
    app = AppFalsa()
    app.ctx = ctx
    esc = EspacioEscena(app)
    assert esc.aviso == 1 and esc.vista == 0
    assert D.pop_aviso(perfil) is None                    # el hub ya lo consumio
    print("aviso del jefe tras la ultima fase ok")


def test_dibujo_de_los_ocho_planetas_y_jefes():
    ctx = crear_ctx()
    p = pygame.Surface((ANCHO, ALTO))
    for n in range(1, D.N_MUNDOS + 1):
        for f in (1, D.JEFE):
            E.Espacio(ctx, n * 10 + f).dibujar_juego(p)
    print("dibujo de los 8 planetas y jefes ok")


def test_capturas_hangar_y_hub():
    app = AppFalsa()
    perfil = app.ctx.perfil
    _dar_piezas(perfil, 1)
    D.guardar_jefe(perfil, 1)
    _dar_piezas(perfil, 2)
    D.guardar_jefe(perfil, 2)
    D.datos(perfil)["mineral"] = 320
    D.datos(perfil)["componentes"] = [1]
    capturar_escena(HangarEspacio(app, lambda: None), SHOTS + "espacio_hangar.png")
    D.datos(perfil)["aviso"] = 1
    capturar_escena(EspacioEscena(app), SHOTS + "espacio_hub_aviso.png")
    print("capturas hangar y hub ok")


def _png_de_prueba(ruta, tam, color):
    superficie = pygame.Surface(tam, pygame.SRCALPHA)
    superficie.fill((0, 0, 0, 0))
    pygame.draw.circle(superficie, color, (tam[0] // 2, tam[1] // 2), min(tam) // 3)
    pygame.image.save(superficie, ruta)


def test_dataset_carga_y_escala():
    import tempfile
    import espacio_dataset as AD
    crear_ctx()                                              # abre la ventana (hace falta para convert_alpha)
    carpeta = tempfile.mkdtemp()
    AD.limpiar_cache()
    AD_RAIZ = AD.RAIZ
    AD.RAIZ = carpeta
    try:
        _png_de_prueba(os.path.join(carpeta, "sonda_1.png"), (256, 256), (120, 190, 255))
        _png_de_prueba(os.path.join(carpeta, "sonda_2.png"), (100, 100), (120, 220, 120))   # tamano mal: se escala
        _png_de_prueba(os.path.join(carpeta, "componente_3_1.png"), (128, 128), (200, 200, 0))
        _png_de_prueba(os.path.join(carpeta, "planeta_jupiter.png"), (512, 512), (214, 164, 110))
        assert AD.sonda(0) is not None and AD.sonda(0).get_size() == (285, 112)
        assert AD.sonda(1).get_size() == (285, 112)
        assert AD.pieza(3, 1) is not None and AD.pieza(3, 1).get_size() == (128, 128)
        assert AD.sonda(7) is None and AD.nave() is None          # no existen: None, sin error
        assert AD.planeta_escalado("jupiter", 150).get_size() == (160, 160)
        assert AD.planeta_escalado("venus", 40) is None
        faltan = AD.faltantes()
        assert "sonda_1" not in faltan and "componente_3_1" not in faltan and "nave_nodriza" in faltan
        assert "planeta_jupiter" not in faltan and "planeta_marte" in faltan
        # 8 sondas, nave, 4 componentes, 24 piezas, 8 planetas = 45; hay 4 hechas
        assert len(faltan) == 45 - 4, len(faltan)
    finally:
        AD.RAIZ = AD_RAIZ
        AD.limpiar_cache()
    print("dataset carga y escala ok")


def test_capturas_hangar_con_dataset_de_prueba():
    import tempfile
    import espacio_dataset as AD
    crear_ctx()
    carpeta = tempfile.mkdtemp()
    AD.limpiar_cache()
    AD_RAIZ = AD.RAIZ
    AD.RAIZ = carpeta
    try:
        for k in range(8):
            _png_de_prueba(os.path.join(carpeta, f"sonda_{k + 1}.png"), (256, 256), D.SONDAS[k]["color"])
        _png_de_prueba(os.path.join(carpeta, "nave_nodriza.png"), (640, 360), (150, 160, 180))
        for c in range(1, 5):
            _png_de_prueba(os.path.join(carpeta, f"componente_{c}.png"), (384, 256), (200, 200, 80))
            for pz in range(1, 7):
                _png_de_prueba(os.path.join(carpeta, f"componente_{c}_{pz}.png"), (128, 128), (200, 120, 60))
        for m in D.MUNDOS:
            _png_de_prueba(os.path.join(carpeta, f"planeta_{m['id']}.png"), (256, 256), m["planeta"])
        AD.limpiar_cache()
        app = AppFalsa()
        perfil = app.ctx.perfil
        D.datos(perfil)["mineral"] = 320
        D.datos(perfil)["componentes"] = [1, 2]
        _dar_piezas(perfil, 5)
        _dar_piezas(perfil, 6)
        D.datos(perfil)["jefes"] = [1, 2, 3, 4, 5, 6]
        capturar_escena(HangarEspacio(app, lambda: None), SHOTS + "espacio_hangar_dataset.png")
        r = RompecabezasEspacio(app, 3, lambda: None)
        r.colocadas = {1, 2, 3}
        r.bandeja = [4, 5, 6]
        capturar_escena(r, SHOTS + "espacio_rompecabezas_dataset.png")
    finally:
        AD.RAIZ = AD_RAIZ
        AD.limpiar_cache()
    print("capturas con dataset de prueba ok")


def test_asteroide_se_debilita_con_disparos_y_meteoritos():
    random.seed(5)
    ctx = crear_ctx()
    j = E.Espacio(ctx, E.NIVEL_ASTEROIDE)
    assert j.modo == "evento" and not j.jefe_modo and j.evento_tipo == "asteroide"
    hp0 = j.boss["hp"]
    # un disparo que cae en el cuerpo le baja la vida
    j.boss["x"], j.boss["y"] = 600.0, 360.0
    j.cadencia = 99
    j.balas = [dict(x=520.0, y=360.0, vx=900.0, vy=0.0, ttl=1.3, pierce=1, ya=[])]
    ctrl = ControlSim()
    ctrl.pos = V2(260, 360)
    j.paso(1 / 60, ctrl)
    assert j.boss["hp"] == hp0 - j.dmg, (j.boss["hp"], hp0)
    # un meteorito destruido tambien le baja 1
    j._destruir(_meteoro(700, 200))
    assert j.boss["hp"] == hp0 - j.dmg - 1
    print("asteroide se debilita ok")


def test_asteroide_suelta_pedazos_al_agrietarse():
    random.seed(6)
    ctx = crear_ctx()
    j = E.Espacio(ctx, E.NIVEL_ASTEROIDE)
    j.meteoros = []
    j.boss["hp"] = j.boss["hpmax"] * 0.7               # perdio un 30 %: primera grieta
    j._actualizar_evento(1 / 60)
    assert j.boss["etapa"] == 1 and len(j.meteoros) == E.PEDAZOS_POR_GRIETA, (j.boss["etapa"], len(j.meteoros))
    assert all(m["vx"] < 0 for m in j.meteoros)        # los pedazos van hacia la sonda
    j.boss["hp"] = j.boss["hpmax"] * 0.2               # sigue perdiendo: dos grietas mas
    j._actualizar_evento(1 / 60)
    assert j.boss["etapa"] == 3 and len(j.meteoros) == 3 * E.PEDAZOS_POR_GRIETA
    print("asteroide suelta pedazos ok")


def test_asteroide_llega_a_la_sonda_y_pierde_la_fase():
    random.seed(7)
    ctx = crear_ctx()
    j = E.Espacio(ctx, E.NIVEL_ASTEROIDE)
    j.meteoros = []
    j.boss["x"] = 300.0                                # ya esta encima de la sonda
    ctrl = ControlSim()
    ctrl.pos = V2(260, 360)
    j.paso(1 / 60, ctrl)
    assert j.terminado and j.ganado is False, (j.terminado, j.ganado)
    assert "llegó a la sonda" in j.mensaje_final, j.mensaje_final
    assert D.piezas(ctx.perfil, 8) == []               # perder no da pieza
    print("asteroide llega y se pierde ok")


def test_asteroide_se_destruye_y_gana():
    random.seed(8)
    ctx = crear_ctx()
    j = E.Espacio(ctx, E.NIVEL_ASTEROIDE)
    j.meteoros = []
    j.boss["hp"] = 0.0
    ctrl = ControlSim()
    ctrl.pos = V2(260, 360)
    j.paso(1 / 60, ctrl)
    assert j.terminado and j.ganado is True, (j.terminado, j.ganado)
    assert "destruido" in j.mensaje_final, j.mensaje_final
    print("asteroide destruido gana ok")


def test_evento_genera_meteoritos_normales():
    random.seed(9)
    ctx = crear_ctx()
    j = E.Espacio(ctx, E.NIVEL_ASTEROIDE)
    ctrl = ControlSim()
    ctrl.pos = V2(260, 360)
    for _ in range(240):                               # cuatro segundos, lejos del asteroide
        j.paso(1 / 60, ctrl)
    assert j.meteoros or j.derribados > 0
    assert not j.terminado
    print("evento genera meteoritos ok")


def test_agujero_tiene_fondo_negro():
    ctx = crear_ctx()
    p = pygame.Surface((ANCHO, ALTO))
    j = E.Espacio(ctx, E.NIVEL_AGUJERO)
    j.dibujar_juego(p)
    assert tuple(p.get_at((20, 300)))[:3] == (0, 0, 0)
    assert tuple(p.get_at((ANCHO - 20, 600)))[:3] == (0, 0, 0)
    a = E.Espacio(ctx, E.NIVEL_ASTEROIDE)
    q = pygame.Surface((ANCHO, ALTO))
    a.dibujar_juego(q)
    assert tuple(q.get_at((20, 300)))[:3] != (0, 0, 0)  # el asteroide conserva el fondo del mundo
    print("agujero negro fondo ok")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print(f"\n{len(tests)} pruebas de Defensa Espacial pasadas")


if __name__ == "__main__":
    main()
