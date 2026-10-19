import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Pruebas del Gachapon: catalogo, probabilidades, repetidas, costo, x10, bots y capturas."""

import json
import math
import random

import pygame

import ajustes
import figuras
from pruebas_util import AppFalsa, escena_simular, capturar_escena, pantalla
from escena_gachapon import GachaponEscena, MANIVELA, FASES_ANIM, DUR, VUELTAS, GX, GY, GR

SHOTS = "/tmp/shots"
DT = 1 / 60


def nueva(monedas=5000, **kw):
    app = AppFalsa()
    app.ctx.perfil.monedas = monedas
    esc = GachaponEscena(app)
    esc.rng = random.Random(kw.pop("semilla", 7))
    for k, v in kw.items():
        setattr(esc, k, v)
    # pasa la espera inicial de los botones
    escena_simular(esc, app.entrada, None, 0.7)
    return app, esc


def paso(esc, ctrl, n=1):
    for _ in range(n):
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()


def avanzar_hasta(esc, ctrl, cond, maximo=40.0, hook=None):
    t = 0.0
    while t < maximo and not cond():
        if hook:
            hook(t)
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        if int(t / DT) % 20 == 0:
            esc.dibujar(pantalla())
        t += DT
    assert cond(), f"no se llego a la condicion (fase={esc.fase})"
    return t


def foto(esc, nombre):
    if esc.fase == "figura":                               # figura de frente (no de canto)
        k = 2 * math.pi / 1.8
        esc.t = math.ceil(esc.t / k) * k
    capturar_escena(esc, f"{SHOTS}/gachapon_{nombre}.png")


# ------------------------------------------------------------------ catalogo
def test_catalogo():
    assert figuras.TOTAL == 36 == len(figuras.ORDEN_FIGURAS) == len(set(figuras.ORDEN_FIGURAS))
    esperado = {"C": 10, "B": 9, "A": 7, "S": 5, "SS": 3, "SSS": 2}
    assert {r: len(v) for r, v in figuras.POR_RANGO.items()} == esperado
    assert figuras.RANGOS == ["C", "B", "A", "S", "SS", "SSS"]
    assert abs(sum(figuras.PROBABILIDADES.values()) - 100.0) < 1e-9
    assert set(figuras.PROBABILIDADES) == set(figuras.RANGOS)
    pantalla()
    for ident, d in figuras.FIGURAS.items():
        assert d["nombre"] and d["texto"], ident
        s = figuras.arte_figura(ident)
        assert s.get_width() > 20 and s.get_height() > 20, ident
        assert figuras.rango_de(ident) in figuras.RANGOS
    assert figuras.TIRO_GARANTIZADO_CADA is None          # desactivado por defecto
    print("catalogo ok")


def test_sorteo_estadistico():
    rng = random.Random(12345)
    n = 20000
    por_rango = {r: 0 for r in figuras.RANGOS}
    por_figura = {i: 0 for i in figuras.ORDEN_FIGURAS}
    for _ in range(n):
        i = figuras.tirar(rng)
        por_figura[i] += 1
        por_rango[figuras.rango_de(i)] += 1
    for r in figuras.RANGOS:
        esp = figuras.PROBABILIDADES[r] / 100.0
        obs = por_rango[r] / n
        sigma = math.sqrt(esp * (1 - esp) / n)
        assert abs(obs - esp) < 5 * sigma + 0.002, (r, obs, esp)
    assert all(v > 0 for v in por_figura.values()), "alguna figura nunca sale"
    # dentro de cada rango las figuras son equiprobables
    for r in figuras.RANGOS:
        lista = figuras.POR_RANGO[r]
        medio = por_rango[r] / len(lista)
        for i in lista:
            assert abs(por_figura[i] - medio) < 6 * math.sqrt(medio) + 5, (i, por_figura[i], medio)
    print("frecuencias", {r: round(100 * por_rango[r] / n, 2) for r in figuras.RANGOS})
    # rango forzado y minimo
    rng = random.Random(1)
    for r in figuras.RANGOS:
        assert all(figuras.rango_de(figuras.tirar(rng, rango=r)) == r for _ in range(50))
    for _ in range(300):
        assert figuras.indice_rango(figuras.rango_de(figuras.tirar(rng, minimo="S"))) >= 3
    # sembrado reproducible
    a = [figuras.tirar(random.Random(5)) for _ in range(1)]
    b = [figuras.tirar(random.Random(5)) for _ in range(1)]
    assert a == b
    # tiro garantizado (opcional) funciona cuando se activa
    figuras.TIRO_GARANTIZADO_CADA = 5
    try:
        assert figuras.rango_garantizado(5) == figuras.GARANTIZADO_RANGO_MINIMO
        assert figuras.rango_garantizado(4) is None
    finally:
        figuras.TIRO_GARANTIZADO_CADA = None
    print("sorteo ok")


def test_repetidas_y_contador():
    rng = random.Random(3)
    vistos = {}
    for _ in range(300):
        i = figuras.tirar(rng)
        vistos[i] = vistos.get(i, 0) + 1
    assert any(v > 1 for v in vistos.values()), "deberian salir repetidas"

    class P:
        figuras = {"pelusin": 3, "robot": 1, "gotita": 0}
    assert figuras.contar_unicas(P) == 2
    assert figuras.contar_unicas_rango(P, "C") == 1
    print("repetidas ok")


# ------------------------------------------------------------------ escena
def test_tirada_costo_repetida_guardado():
    app, esc = nueva(monedas=1000, forzar_rango="SSS")
    perfil = app.ctx.perfil
    costo = ajustes.GACHA_COSTO
    assert esc.pedir_tirada(1)
    assert perfil.monedas == 1000 - costo
    ident = esc.res["id"]
    assert perfil.figuras[ident] == 1 and esc.res["nueva"] is True
    with open(perfil.archivo) as f:                       # se guardo en disco
        datos = json.load(f)
    assert datos["figuras"][ident] == 1 and datos["monedas"] == 1000 - costo
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "figura")
    foto(esc, "figura_nueva")
    # segunda y tercera tirada del mismo rango (solo hay 2 figuras SSS): hay repetida seguro
    esc._volver_inicio()
    esc._rearmar()
    paso(esc, app.entrada, 40)
    repetida = None
    for _ in range(4):
        assert esc.pedir_tirada(1)
        if not esc.res["nueva"]:
            repetida = dict(esc.res)
            break
        avanzar_hasta(esc, app.entrada, lambda: esc.fase == "figura")
        esc._volver_inicio()
    assert repetida is not None and repetida["cant"] >= 2
    assert perfil.figuras[repetida["id"]] == repetida["cant"]
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "figura")
    paso(esc, app.entrada, 90)
    foto(esc, "figura_repetida")
    assert sum(perfil.figuras.values()) == perfil.extra["gachapon"]["tiradas"]
    print("tirada/costo/repetida ok")


def test_sin_monedas():
    app, esc = nueva(monedas=ajustes.GACHA_COSTO - 1)
    perfil = app.ctx.perfil
    assert not esc.pedir_tirada(1)
    assert perfil.monedas == ajustes.GACHA_COSTO - 1 and not perfil.figuras
    assert esc.fase == "inicio" and esc.aviso_t > 0
    paso(esc, app.entrada, 3)
    assert not esc.b_tirar.activo and not esc.b_x10.activo
    assert esc.faltan(1) == 1
    # bot que pulsa el boton: no pasa nada
    ctrl = app.entrada
    ctrl.mover_a(*esc.b_tirar.rect.center)
    for _ in range(100):
        ctrl.clic = True
        paso(esc, ctrl)
    assert esc.fase == "inicio" and not perfil.figuras
    # bot que gira la manivela sin monedas: tampoco
    for k in range(240):
        a = k * 0.2
        ctrl.mover_a(MANIVELA[0] + 70 * math.cos(a), MANIVELA[1] + 70 * math.sin(a))
        paso(esc, ctrl)
    assert esc.fase == "inicio" and not perfil.figuras
    foto(esc, "sin_monedas")
    # con monedas justas para x1 pero no x10
    perfil.monedas = ajustes.GACHA_COSTO * 5
    assert not esc.pedir_tirada(10) and perfil.monedas == ajustes.GACHA_COSTO * 5
    print("sin monedas ok")


def test_x10():
    app, esc = nueva(monedas=ajustes.GACHA_COSTO * 10 + 7, forzar_rango=["C", "C", "C", "B", "C", "A", "C", "C", "S", "C"])
    perfil = app.ctx.perfil
    assert esc.pedir_tirada(10)
    assert perfil.monedas == 7
    assert len(esc.lote) == 10 and sum(perfil.figuras.values()) == 10
    assert esc.res["rango"] == "S"                       # se abre la mejor
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "lluvia", 10)
    paso(esc, app.entrada, 120)
    foto(esc, "x10_lluvia")
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "figura", 30)
    # a resumen con la mano
    ctrl = app.entrada
    ctrl.mover_a(*esc.b_resumen.rect.center)
    avanzar_hasta(esc, ctrl, lambda: esc.fase == "resumen", 5, hook=lambda t: setattr(ctrl, "clic", t > 1.0))
    paso(esc, ctrl, 70)
    foto(esc, "x10_resumen")
    assert not esc.b_otra.activo                        # no alcanza para otro x10
    ctrl.mover_a(*esc.b_seguir.rect.center)
    avanzar_hasta(esc, ctrl, lambda: esc.fase == "inicio", 5, hook=lambda t: setattr(ctrl, "clic", True))
    # sin x10 por falta de monedas
    assert not esc.pedir_tirada(10)
    print("x10 ok")


def bot_solo_cursor(esc, ctrl, t):
    """Solo mueve el cursor: gira la manivela en circulos; luego busca el boton Seguir con permanencia."""
    f = esc.fase
    if f == "inicio":
        a = t * 7.0
        ctrl.mover_a(MANIVELA[0] + 80 * math.cos(a), MANIVELA[1] + 80 * math.sin(a))
    elif f == "figura":
        b = esc.b_seguir if esc.modo == 1 else esc.b_resumen
        ctrl.mover_a(*b.rect.center)
    elif f == "resumen":
        ctrl.mover_a(*esc.b_seguir.rect.center)
    else:
        ctrl.mover_a(300, 300)


def test_bot_solo_cursor():
    app, esc = nueva(monedas=ajustes.GACHA_COSTO * 3 + 5)
    ctrl = app.entrada
    perfil = app.ctx.perfil
    esc.forzar_rango = ["B", "A", "C"]
    t = 0.0
    visto = set()
    # tres tiradas completas solo con el cursor (manivela + permanencia)
    while t < 120 and sum(perfil.figuras.values()) < 3 or esc.fase != "inicio":
        bot_solo_cursor(esc, ctrl, t)
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        visto.add(esc.fase)
        if int(t / DT) % 30 == 0:
            esc.dibujar(pantalla())
        t += DT
        if t > 200:
            break
    assert sum(perfil.figuras.values()) == 3, (perfil.figuras, esc.fase)
    assert perfil.monedas == 5
    assert {"caer", "rueda", "suspenso", "destello", "silueta", "rango", "figura"} <= visto, visto   # giro a mano: sin "agitar"
    print("bot solo cursor ok", round(t, 1), "s")


def test_bot_golpe_y_saltar():
    app, esc = nueva(monedas=1000, forzar_rango="A")
    ctrl = app.entrada
    ctrl.mover_a(640, 300)
    paso(esc, ctrl, 2)
    ctrl.golpe = True
    paso(esc, ctrl)
    assert esc.fase != "inicio", "un golpe sobre la maquina debe tirar"
    # saltar antes de 1 s no hace nada
    paso(esc, ctrl, 20)
    ctrl.golpe = True
    paso(esc, ctrl)
    assert esc.fase in FASES_ANIM
    paso(esc, ctrl, 60)
    ctrl.golpe = True
    paso(esc, ctrl)
    assert esc.fase == "figura", esc.fase
    # el golpe sobre el boton Seguir vuelve al inicio
    paso(esc, ctrl, 60)
    ctrl.mover_a(*esc.b_seguir.rect.center)
    ctrl.golpe = True
    paso(esc, ctrl)
    assert esc.fase == "inicio"
    # tecla ESC en inicio vuelve al menu
    esc.tecla_esc()
    assert app.volvio_al_menu
    print("bot golpe/saltar ok")


def test_bot_inerte():
    app, esc = nueva(monedas=1000)
    ctrl = app.entrada
    ctrl.mover_a(5, 5)
    escena_simular(esc, ctrl, None, 20)
    assert esc.fase == "inicio" and app.ctx.perfil.monedas == 1000 and not app.ctx.perfil.figuras
    # inerte durante una animacion: llega sola a la figura y espera
    esc.pedir_tirada(1)
    escena_simular(esc, ctrl, None, 25)
    assert esc.fase == "figura"
    assert sum(app.ctx.perfil.figuras.values()) == 1
    print("bot inerte ok")


def test_bot_erratico():
    rnd = random.Random(99)
    app, esc = nueva(monedas=1800)
    ctrl = app.entrada
    perfil = app.ctx.perfil
    gastadas = 0
    for n in range(60 * 150):
        if rnd.random() < 0.05:
            ctrl.mover_a(rnd.uniform(0, 1280), rnd.uniform(0, 720))
        if rnd.random() < 0.02:
            ctrl.clic = True
        if rnd.random() < 0.01:
            ctrl.golpe = True
        if rnd.random() < 0.001:
            esc.tecla_esc()
            app.volvio_al_menu = False
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        if n % 10 == 0:
            esc.dibujar(pantalla())
        assert perfil.monedas >= 0
        assert all(v > 0 for v in perfil.figuras.values())
    assert sum(perfil.figuras.values()) == perfil.extra.get("gachapon", {}).get("tiradas", 0)
    assert perfil.monedas + sum(perfil.figuras.values()) * ajustes.GACHA_COSTO == 1800
    print("bot erratico ok, figuras", sum(perfil.figuras.values()))


def test_rangos_forzados_y_capturas():
    for r in figuras.RANGOS:
        app, esc = nueva(monedas=2000, forzar_rango=r, engano=0.0)
        ctrl = app.entrada
        assert esc.pedir_tirada(1)
        assert esc.res["rango"] == r
        if r == "C":
            foto(esc, "agitar")
        avanzar_hasta(esc, ctrl, lambda: esc.fase == "caer")
        if r == "C":
            paso(esc, ctrl, 25)
            foto(esc, "caida")
            avanzar_hasta(esc, ctrl, lambda: esc.fase == "rueda")
            paso(esc, ctrl, 40)
            foto(esc, "rueda")
        avanzar_hasta(esc, ctrl, lambda: esc.fase == "suspenso")
        paso(esc, ctrl, 40)
        if r in ("C", "SSS"):
            foto(esc, f"suspenso_{r}")
        avanzar_hasta(esc, ctrl, lambda: esc.fase == "destello")
        paso(esc, ctrl, 22)
        foto(esc, f"destello_{r}")
        avanzar_hasta(esc, ctrl, lambda: esc.fase == "silueta")
        paso(esc, ctrl, 45)
        if r in ("C", "SSS"):
            foto(esc, f"silueta_{r}")
        avanzar_hasta(esc, ctrl, lambda: esc.fase == "rango")
        paso(esc, ctrl, 18)
        foto(esc, f"rango_{r}")
        avanzar_hasta(esc, ctrl, lambda: esc.fase == "figura")
        paso(esc, ctrl, 100)
        foto(esc, f"figura_{r}")
        assert figuras.cantidad(app.ctx.perfil, esc.res["id"]) == 1
    print("rangos forzados ok")


def test_engano_decorativo():
    app, esc = nueva(monedas=3000, engano=1.0, forzar_rango="C")
    assert esc.pedir_tirada(1)
    assert esc.res["aparente"] != "C" and esc.res["rango"] == "C"
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "suspenso")
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "destello")
    assert esc.cap_rango_ap == "C"                        # cambia al abrirse
    print("engano ok")


def test_coleccion():
    # vacia
    app, esc = nueva(monedas=0)
    esc.abrir_coleccion()
    paso(esc, app.entrada, 30)
    foto(esc, "coleccion_vacia")
    assert esc.paginas() == 3
    # llena
    app, esc = nueva(monedas=0)
    for i, ident in enumerate(figuras.ORDEN_FIGURAS):
        app.ctx.perfil.figuras[ident] = 1 + (i % 4 == 0) * 2
    assert figuras.contar_unicas(app.ctx.perfil) == 36
    esc.abrir_coleccion()
    paso(esc, app.entrada, 30)
    foto(esc, "coleccion_llena")
    # parcial con filtro y pagina por cursor
    app, esc = nueva(monedas=0)
    rng = random.Random(4)
    for _ in range(30):
        i = figuras.tirar(rng)
        app.ctx.perfil.figuras[i] = app.ctx.perfil.figuras.get(i, 0) + 1
    ctrl = app.entrada
    esc.abrir_coleccion()
    paso(esc, ctrl, 40)
    ctrl.mover_a(*esc.b_sig.rect.center)
    ctrl.clic = True
    paso(esc, ctrl)
    assert esc.pagina == 1
    paso(esc, ctrl, 5)
    foto(esc, "coleccion_pag2")
    ctrl.mover_a(*esc.b_filtros[4].rect.center)           # pestana Fantasia (pagina de mundo)
    ctrl.clic = True
    paso(esc, ctrl)
    assert esc.filtro == "fantasia" and esc.pagina == 0 and len(esc.lista_coleccion()) == 10
    esc.poner_filtro("S")                                  # tambien se puede filtrar por rango
    assert len(esc.lista_coleccion()) == 5
    esc.poner_filtro("fantasia")
    paso(esc, ctrl, 10)
    foto(esc, "coleccion_pagina_fantasia")
    # detalle de una figura que tengo y de una que no
    tengo = next(i for i in figuras.ORDEN_FIGURAS if app.ctx.perfil.figuras.get(i, 0) > 0)
    falta = next(i for i in figuras.ORDEN_FIGURAS if app.ctx.perfil.figuras.get(i, 0) == 0)
    for ident, nombre in ((tengo, "detalle_tengo"), (falta, "detalle_falta")):
        esc.poner_filtro(None)
        esc.abrir_detalle(ident)
        paso(esc, ctrl, 40)
        foto(esc, nombre)
        esc.detalle = None
    # cursor sobre una tarjeta con permanencia abre el detalle
    esc.poner_filtro(None)
    esc._rearmar()
    paso(esc, ctrl, 40)
    ctrl.mover_a(*esc.b_tarjetas[2].rect.center)
    for _ in range(int(ajustes.DWELL_SEG * 60) + 20):
        paso(esc, ctrl)
        if esc.detalle is not None:
            break
    assert esc.detalle == figuras.ORDEN_FIGURAS[2]
    ctrl.mover_a(*esc.b_cerrar.rect.center)
    paso(esc, ctrl, 40)
    ctrl.clic = True
    paso(esc, ctrl)
    assert esc.detalle is None
    # volver a la maquina y al menu
    esc.tecla_esc()
    assert esc.fase == "inicio"
    ctrl.mover_a(*esc.b_volver.rect.center)
    paso(esc, ctrl, 40)
    ctrl.clic = True
    paso(esc, ctrl)
    assert app.volvio_al_menu
    print("coleccion ok")


def test_maquina_reposo():
    app, esc = nueva(monedas=350)
    paso(esc, app.entrada, 30)
    foto(esc, "maquina_reposo")
    print("reposo ok")



# ------------------------------------------------------------------ suerte del album
class _P:
    def __init__(self, ids=()):
        self.figuras = {i: 1 for i in ids}


def test_paginas_y_suerte():
    assert [len(x) for x in figuras.POR_PAGINA] == [12, 8, 6, 10] and sum(len(x) for x in figuras.POR_PAGINA) == 36
    assert sorted(i for x in figuras.POR_PAGINA for i in x) == sorted(figuras.ORDEN_FIGURAS)
    vacio = figuras.probabilidades_efectivas(_P())
    assert vacio == figuras.PROBABILIDADES and figuras.suerte(_P()) == 0.0
    # llenar paginas sube la suerte, siempre mejora los rangos altos y la suma sigue siendo 100
    previo = vacio
    for k in range(len(figuras.PAGINAS)):
        ids = [i for j in range(k + 1) for i in figuras.POR_PAGINA[j]]
        ef = figuras.probabilidades_efectivas(_P(ids))
        assert abs(sum(ef.values()) - 100) < 1e-9
        for r in ("A", "S", "SS", "SSS"):
            assert ef[r] > previo[r], (k, r)
        assert ef["C"] < previo["C"]
        previo = ef
    lleno = figuras.probabilidades_efectivas(_P(figuras.ORDEN_FIGURAS))
    assert lleno["SSS"] > 2.0 * figuras.PROBABILIDADES["SSS"] and lleno["C"] < 35
    assert figuras.suerte(_P(figuras.ORDEN_FIGURAS)) == figuras.suerte_max()
    # una pagina a medias da menos que completa (con bonus)
    mitad = _P(figuras.POR_PAGINA[0][:6])
    assert 0.4 < figuras.suerte(mitad) < 0.6
    assert figuras.suerte(_P(figuras.POR_PAGINA[0])) == 1.25
    assert figuras.siguiente_meta(_P(figuras.POR_PAGINA[0])) == (2, 6)   # Prehistoria es la mas corta
    assert figuras.siguiente_meta(_P(figuras.ORDEN_FIGURAS)) is None
    # el sorteo usa las probabilidades efectivas (frecuencias)
    rng = random.Random(77)
    n = 30000
    cuenta = {r: 0 for r in figuras.RANGOS}
    for _ in range(n):
        cuenta[figuras.rango_de(figuras.tirar(rng, probs=lleno))] += 1
    for r in figuras.RANGOS:
        esp = lleno[r] / 100
        assert abs(cuenta[r] / n - esp) < 5 * math.sqrt(esp * (1 - esp) / n) + 0.002, (r, cuenta[r] / n, esp)
    print("paginas y suerte ok", {r: round(v, 1) for r, v in lleno.items()})


def test_suerte_en_la_escena():
    app, esc = nueva(monedas=5000)
    perfil = app.ctx.perfil
    antes = esc.probabilidades()
    for i in figuras.POR_PAGINA[1][:-1]:                     # Oceano a falta de una
        perfil.figuras[i] = 1
    medio = esc.probabilidades()
    assert medio["SSS"] > antes["SSS"]
    falta = figuras.POR_PAGINA[1][-1]
    # forzamos un rango que contenga la figura que falta: se completa la pagina
    esc.rng = random.Random(1)
    esc.forzar_rango = figuras.rango_de(falta)
    n = 0
    while not figuras.pagina_completa(perfil, 1) and n < 60:
        esc.pedir_tirada(1)
        esc._volver_inicio()
        n += 1
    assert figuras.pagina_completa(perfil, 1)
    # la tirada que la completo lo anuncia
    perfil.figuras.pop(falta)
    esc.forzar_rango = figuras.rango_de(falta)
    esc.rng = random.Random(3)
    esc.rng.choice = lambda lista, _f=falta: _f if _f in lista else lista[0]    # sale justo la que falta
    assert esc.pedir_tirada(1)
    assert esc.res["id"] == falta and esc.paginas_nuevas == [1], esc.paginas_nuevas
    assert esc.suerte_despues > esc.suerte_antes
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "figura")
    paso(esc, app.entrada, 80)
    foto(esc, "figura_pagina_completa")
    print("suerte en la escena ok")


# ------------------------------------------------------------------ manivela, vueltas y fisica
def girar(esc, ctrl, w, seg, radio=80, a0=0.0):
    """Mueve el cursor en circulos a w rad/s durante seg segundos (se detiene si empieza la tirada)."""
    for k in range(int(seg * 60)):
        a = a0 + k / 60 * w
        ctrl.mover_a(MANIVELA[0] + radio * math.cos(a), MANIVELA[1] + radio * math.sin(a))
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        if esc.fase != "inicio":
            return k
    return None


def test_diez_vueltas():
    assert VUELTAS == 10
    app, esc = nueva(monedas=1000, forzar_rango="B")
    ctrl = app.entrada
    perfil = app.ctx.perfil
    # 9 vueltas y media: todavia no cae nada
    w = 6.0
    k = 0
    while esc.giro < 2 * math.pi * 9.5:
        a = k / 60 * w
        ctrl.mover_a(MANIVELA[0] + 80 * math.cos(a), MANIVELA[1] + 80 * math.sin(a))
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        k += 1
        assert k < 60 * 30
        assert esc.fase == "inicio" and not perfil.figuras
    assert perfil.monedas == 1000
    foto(esc, "vueltas_9")
    # sigue girando: a la vuelta 10 suelta la capsula, sin pasar por la animacion de agitar
    k2 = girar(esc, ctrl, w, 3, a0=k / 60 * w)
    assert k2 is not None and esc.fase == "caer" and esc.manual, esc.fase
    assert perfil.monedas == 1000 - ajustes.GACHA_COSTO and sum(perfil.figuras.values()) == 1
    # tiempo minimo realista: a 6 rad/s, 10 vueltas llevan cerca de 10 s
    assert 9.0 < (k + k2) / 60 < 13.0, (k + k2) / 60
    avanzar_hasta(esc, ctrl, lambda: esc.fase == "figura")
    esc._volver_inicio()
    assert esc.giro == 0.0
    # la tirada con boton gira sola las 10 vueltas completas
    app, esc = nueva(monedas=1000, forzar_rango="C")
    assert esc.pedir_tirada(1) and not esc.manual and esc.fase == "agitar"
    a0 = esc.ang_man
    avanzar_hasta(esc, app.entrada, lambda: esc.fase == "caer")
    assert abs((esc.ang_man - a0) - 2 * math.pi * VUELTAS) < 0.05, (esc.ang_man - a0) / (2 * math.pi)
    print("diez vueltas ok")


def test_fuerza_e_inercia():
    # 1) el mango tiene masa: aunque el cursor salte, el mango tarda y tiene velocidad maxima
    app, esc = nueva(monedas=1000)
    ctrl = app.entrada
    for k in range(60):                                    # cursor saltando de lado a lado a 60 Hz
        a = k * 2.0
        ctrl.mover_a(MANIVELA[0] + 90 * math.cos(a), MANIVELA[1] + 90 * math.sin(a))
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        assert abs(esc.vel_man) <= 17.0 + 1e-6
    assert esc.giro < 2 * math.pi * 3, "un cursor que salta no puede regalar vueltas"
    # 2) inercia: al soltar, sigue girando un rato y se frena sola
    app, esc = nueva(monedas=1000)
    ctrl = app.entrada
    girar(esc, ctrl, 9.0, 2.0)
    v0 = esc.vel_man
    assert abs(v0) > 6.0, v0
    ctrl.mover_a(40, 40)                                   # cursor fuera de la manivela
    paso(esc, ctrl, 15)
    assert 0.2 * abs(v0) < abs(esc.vel_man) < abs(v0), (v0, esc.vel_man)
    g1 = esc.giro
    paso(esc, ctrl, 15)
    assert esc.giro > g1, "sigue girando por inercia"
    paso(esc, ctrl, 60 * 6)
    assert abs(esc.vel_man) < 0.2
    # 3) la paleta va engranada a la manivela
    girar(esc, ctrl, 9.0, 1.0)
    assert abs(esc.pal_vel - 0.75 * esc.vel_man) < 1e-6
    # 4) giro hacia el otro lado tambien cuenta
    app, esc = nueva(monedas=1000)
    ctrl = app.entrada
    girar(esc, ctrl, -6.0, 3.0)
    assert esc.giro > 2 * math.pi * 1.5 and esc.vel_man < 0
    print("fuerza e inercia ok")


def test_fisica_capsulas():
    # en reposo las capsulas se asientan: sin temblor y abajo del globo; nada se mueve "solo"
    app, esc = nueva(monedas=500)
    ctrl = app.entrada
    ctrl.mover_a(40, 40)
    paso(esc, ctrl, 120)
    v = [math.hypot(c.vx, c.vy) for c in esc.caps]
    assert sum(v) / len(v) < 25 and max(v) < 80, (sum(v) / len(v), max(v))
    assert all(abs(c.vang) < 2 for c in esc.caps)
    assert sum(c.y for c in esc.caps) / len(esc.caps) > GY + 20, "las capsulas caen al fondo"
    y_antes = [c.y for c in esc.caps]
    paso(esc, ctrl, 180)
    mov = max(abs(a - c.y) for a, c in zip(y_antes, esc.caps))
    assert mov < 3, f"movimiento espontaneo {mov}"
    # al girar la manivela se agitan: sube la energia y suben las capsulas; al soltar, se calman
    media_y_reposo = sum(c.y for c in esc.caps) / len(esc.caps)
    vmax, media_y_min = 0.0, 1e9
    for k in range(60 * 3):
        a = k / 60 * 8
        ctrl.mover_a(MANIVELA[0] + 80 * math.cos(a), MANIVELA[1] + 80 * math.sin(a))
        esc.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        if esc.fase != "inicio":
            break
        vmax = max(vmax, max(math.hypot(c.vx, c.vy) for c in esc.caps))
        media_y_min = min(media_y_min, sum(c.y for c in esc.caps) / len(esc.caps))
        assert all(math.hypot(c.x - GX, c.y - GY) <= GR for c in esc.caps), "una capsula salio del globo"
    assert vmax > 300 and media_y_min < media_y_reposo - 15, (vmax, media_y_min, media_y_reposo)
    foto(esc, "fisica_agitando")
    ctrl.mover_a(40, 40)
    paso(esc, ctrl, 60 * 8)
    v = [math.hypot(c.vx, c.vy) for c in esc.caps]
    assert sum(v) / len(v) < 25, "tras soltar se calman"
    # mas rapido => mas energia (la fuerza del jugador se nota)
    energias = []
    for w in (3.0, 9.0):
        app2, esc2 = nueva(monedas=500)
        c2 = app2.entrada
        c2.mover_a(40, 40)
        paso(esc2, c2, 120)
        acum = 0.0
        for k in range(60 * 2):
            a = k / 60 * w
            c2.mover_a(MANIVELA[0] + 80 * math.cos(a), MANIVELA[1] + 80 * math.sin(a))
            esc2.actualizar(DT, c2)
            c2.fin_cuadro()
            acum += sum(c.vx * c.vx + c.vy * c.vy for c in esc2.caps)
        energias.append(acum)
    assert energias[1] > 1.5 * energias[0], energias
    # rendimiento de la simulacion
    import time
    t0 = time.time()
    for _ in range(300):
        esc._sim_caps(DT)
    ms = (time.time() - t0) / 300 * 1000
    assert ms < 6.0, f"simulacion lenta: {ms:.2f} ms/cuadro"
    print(f"fisica capsulas ok ({ms:.2f} ms/cuadro)")


def test_ui_album_en_inicio():
    app, esc = nueva(monedas=700)
    perfil = app.ctx.perfil
    for i in figuras.POR_PAGINA[2] + figuras.POR_PAGINA[1][:3]:
        perfil.figuras[i] = 1
    paso(esc, app.entrada, 20)
    foto(esc, "inicio_album")
    esc.pedir_tirada(1)
    paso(esc, app.entrada, 150)
    foto(esc, "giro_automatico")
    print("ui album ok")



# ------------------------------------------------------------------ pulido para presentacion
def test_garantia_x10():
    base = dict(figuras.PROBABILIDADES)
    figuras.PROBABILIDADES.update({"C": 98.0, "B": 1.5, "A": 0.3, "S": 0.1, "SS": 0.05, "SSS": 0.05})
    try:
        for semilla in range(40):
            app, esc = nueva(monedas=2000, semilla=semilla)
            assert esc.pedir_tirada(10)
            rangos = [x["rango"] for x in esc.lote]
            assert any(figuras.indice_rango(r) >= figuras.indice_rango("A") for r in rangos), (semilla, rangos)
        # sin garantia, con estas probabilidades casi nunca sale una A o mejor
        sin = 0
        for semilla in range(40):
            app, esc = nueva(monedas=2000, semilla=semilla)
            esc.garantia_x10 = False
            esc.pedir_tirada(10)
            sin += any(figuras.indice_rango(x["rango"]) >= 2 for x in esc.lote)
        assert sin < 8, sin
        # una tirada x1 no tiene garantia
        app, esc = nueva(monedas=2000, semilla=5)
        esc.pedir_tirada(1)
    finally:
        figuras.PROBABILIDADES.update(base)
    # una tirada forzada manda sobre la garantia (pruebas)
    app, esc = nueva(monedas=2000, forzar_rango=["C"] * 10)
    esc.pedir_tirada(10)
    assert [x["rango"] for x in esc.lote] == ["C"] * 10
    print("garantia x10 ok")


def test_monedas_vuelan_y_contador():
    app, esc = nueva(monedas=1000)
    ctrl = app.entrada
    assert abs(esc.monedas_vis - 1000) < 1e-6
    esc.pedir_tirada(1)
    assert esc.vuelos and app.ctx.perfil.monedas == 900
    paso(esc, ctrl, 3)
    assert 900 < esc.monedas_vis < 1000, esc.monedas_vis          # el contador baja suave, no de golpe
    foto(esc, "moneda_vuela")
    paso(esc, ctrl, 90)
    assert not esc.vuelos and abs(esc.monedas_vis - 900) < 1.0
    # x10 lanza varias monedas
    app, esc = nueva(monedas=2000)
    esc.pedir_tirada(10)
    assert len(esc.vuelos) == 6
    print("monedas y contador ok")


def test_transiciones_y_arte():
    app, esc = nueva(monedas=500)
    ctrl = app.entrada
    esc.abrir_coleccion()
    assert esc.fade > 0.4
    paso(esc, ctrl, 40)
    assert esc.fade == 0.0
    esc._volver_inicio()
    assert esc.fade > 0.4
    # sprites de capsula y esferas: cacheados y con el tamano esperado
    import escena_gachapon as G
    a = G._esfera(25)
    assert a is G._esfera(25) and a.get_width() == 25 * 2 + 4
    base = G._cuerpo_capsula((200, 60, 60), 25)
    assert base is G._cuerpo_capsula((200, 60, 60), 25)
    scr = pantalla()
    for r in (23, 26, 34, 105):
        G.dibujar_capsula(scr, 300, 300, r, (80, 160, 240), 1.2)
    # el texto cacheado ocupa lo mismo que el original
    from nucleo import escribir as esc_orig
    r1 = G.escribir(scr, esc.f.normal, "Prueba", 400, 300)
    r2 = esc_orig(scr, esc.f.normal, "Prueba", 400, 300)
    assert r1.size == r2.size and r1.topleft == r2.topleft
    print("transiciones y arte ok")


if __name__ == "__main__":
    os_shots = SHOTS
    _os.makedirs(os_shots, exist_ok=True)
    test_catalogo()
    test_sorteo_estadistico()
    test_repetidas_y_contador()
    test_maquina_reposo()
    test_tirada_costo_repetida_guardado()
    test_sin_monedas()
    test_x10()
    test_bot_solo_cursor()
    test_bot_golpe_y_saltar()
    test_bot_inerte()
    test_bot_erratico()
    test_engano_decorativo()
    test_rangos_forzados_y_capturas()
    test_coleccion()
    test_paginas_y_suerte()
    test_suerte_en_la_escena()
    test_diez_vueltas()
    test_fuerza_e_inercia()
    test_fisica_capsulas()
    test_ui_album_en_inicio()
    test_garantia_x10()
    test_monedas_vuelan_y_contador()
    test_transiciones_y_arte()
    print("TODO OK")
