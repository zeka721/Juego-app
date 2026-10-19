import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Pruebas de TamagotchiEscena (hub del Tamagotchi): huevos, eclosion, hogar, cuidados, evolucion, cuaderno y salon."""

import json
import math
import random
import tempfile
import time
import types

try:
    import j_tama  # noqa: F401
except ImportError:                       # el agente de la batalla aun no la entrego: stub minimo
    from nucleo import Minijuego
    _m = types.ModuleType("j_tama")

    class Tamagotchi(Minijuego):
        id = "tamagotchi"
        titulo = "Tamagotchi"
        NIVEL_MAX = 1
        duracion = None
    _m.Tamagotchi = Tamagotchi
    _sys.modules["j_tama"] = _m

import pygame

import arte_tama as AT
import catalogo
import tama_datos as TD
from ajustes import ANCHO, ALTO
from nucleo import ControlSim, Perfil
from pruebas_util import AppFalsa, escena_simular, capturar_escena, pantalla
import escena_tama as ET
from escena_tama import TamagotchiEscena

SHOTS = "/tmp/shots/tama_escena_"
COMIDA = {"manzana": 3, "zanahoria": 2, "huevo": 2, "pan": 1}


# =====================================================================  ayudas
def nueva(inv=None, app=None, rng=None):
    app = app or AppFalsa()
    per = app.ctx.perfil
    if inv is not None:
        for k in list(per.inventario):
            if TD.valor_comida(k) is not None:
                per.inventario.pop(k)
        per.inventario.update(inv)
    esc = TamagotchiEscena(app, rng=rng or random.Random(7))
    return app, esc, ControlSim()


def avanzar(esc, ctrl, seg=0.7, dibujar_cada=10):
    escena_simular(esc, ctrl, None, segundos=seg, dibujar_cada=dibujar_cada)


def pulsar(esc, ctrl, rect, seg=1.75):
    """Pulsa por permanencia (dwell) un rectangulo y aparta el cursor."""
    ctrl.mover_a(*pygame.Rect(rect).center)
    avanzar(esc, ctrl, seg)
    ctrl.mover_a(640, 560)
    avanzar(esc, ctrl, 0.1)


def pulsar_clic(esc, ctrl, rect):
    ctrl.mover_a(*pygame.Rect(rect).center)
    avanzar(esc, ctrl, 0.7)
    ctrl.clic = True
    escena_simular(esc, ctrl, None, segundos=1 / 60, dibujar_cada=1)
    ctrl.mover_a(640, 560)
    avanzar(esc, ctrl, 0.1)


def frotar(esc, ctrl, seg, radio=70, vel=330.0):
    """Mueve el cursor en circulos dentro del huevo (velocidad en px/s)."""
    w = vel / radio
    cx, cy = ET.HUEVO_C

    def bot(e, c, t):
        c.mover_a(cx + radio * math.cos(w * t), cy + radio * 0.9 * math.sin(w * t))
    escena_simular(esc, ctrl, bot, segundos=seg, dibujar_cada=60)


def mascota(per, especie="dragon", etapa=0, **kw):
    """Deja una mascota activa directamente en el estado (para no frotar 50 s cada vez)."""
    st = TD.estado(per)
    m = TD._mascota_nueva(especie, time.time(), etapa)
    m.update(kw)
    st["activa"] = m
    st["huevo"] = None
    st["descubiertas"][especie] = max(st["descubiertas"].get(especie, 0), etapa)
    return TD.estado(per)["activa"]


def hogar(especie="dragon", etapa=1, inv=COMIDA, **kw):
    app = AppFalsa()
    per = app.ctx.perfil
    mascota(per, especie, etapa, **kw)
    app, esc, ctrl = nueva(inv, app=app)
    assert esc.modo == "hogar"
    avanzar(esc, ctrl, 0.8)
    return app, esc, ctrl


def estado_de(app):
    return TD.estado(app.ctx.perfil)


def nombre_escena(app):
    return type(app.escena).__name__


# =====================================================================  pruebas
def prueba_huevos_y_eleccion():
    app, esc, ctrl = nueva()
    assert esc.modo == "huevos" and len(esc.cards) == 18
    ctrl.mover_a(esc.cards[4].rect.centerx, esc.cards[4].rect.centery)
    avanzar(esc, ctrl, 0.3)
    assert esc.hv[4] > 0.3 and esc.hv[0] < 0.05          # el huevo bajo el cursor se mece
    capturar_escena(esc, SHOTS + "huevos.png")
    # elegir por permanencia
    pulsar(esc, ctrl, esc.cards[4].rect)
    st = estado_de(app)
    assert st["huevo"] == 4 and esc.modo == "eclosion", (st["huevo"], esc.modo)
    # nada del contenido se revela en la pantalla de huevos: con el estado vacio no se muestran nombres
    esp = st["huevos"][4]
    assert esp in TD.ESPECIES


def prueba_huevos_abiertos():
    app = AppFalsa()
    per = app.ctx.perfil
    st = TD.estado(per)
    for k in (0, 5, 11):
        st["eclosionados"].append(k)
        sp = st["huevos"][k]
        st["descubiertas"][sp] = 2
    app, esc, ctrl = nueva(app=app)
    assert esc.modo == "huevos"
    avanzar(esc, ctrl, 0.4)
    assert not esc.cards[5].activo and esc.cards[6].activo
    ctrl.mover_a(esc.cards[5].rect.centerx, esc.cards[5].rect.centery)
    avanzar(esc, ctrl, 1.6)                              # un huevo abierto no se puede elegir
    assert TD.estado(per)["huevo"] is None
    capturar_escena(esc, SHOTS + "huevos_abiertos.png")


def prueba_eclosion_completa():
    app, esc, ctrl = nueva()
    per = app.ctx.perfil
    pulsar(esc, ctrl, esc.cards[7].rect)
    assert esc.modo == "eclosion"
    esp_esperada = estado_de(app)["huevos"][7]
    avanzar(esc, ctrl, 0.3)
    capturar_escena(esc, SHOTS + "eclosion_0.png")
    # sin frotar no hay calor
    avanzar(esc, ctrl, 2.0)
    assert estado_de(app)["calor"] == 0.0
    # frotar fuera del huevo tampoco
    def fuera(e, c, t):
        c.mover_a(200 + 300 * math.sin(t * 6), 300)
    escena_simular(esc, ctrl, fuera, segundos=3, dibujar_cada=60)
    assert estado_de(app)["calor"] == 0.0
    # frotar dentro: ~50 s para llegar al 100 %
    fotos = {0.25: 1, 0.45: 2, 0.65: 3, 0.9: 4}
    t0 = 0.0
    c0 = 0.0
    while esc.hatch is None and t0 < 70:
        frotar(esc, ctrl, 0.25)
        t0 += 0.25
        calor = estado_de(app)["calor"]
        for umbral, n in list(fotos.items()):
            if calor >= umbral and esc.hatch is None:
                capturar_escena(esc, SHOTS + "eclosion_%d.png" % n)
                fotos.pop(umbral)
    assert 40 <= t0 <= 62, t0                               # ~50 s de frotado efectivo
    assert esc.hatch is not None and esc.hatch["esp"] == esp_esperada
    st = estado_de(app)
    assert st["activa"] is not None and st["activa"]["especie"] == esp_esperada and st["huevo"] is None
    assert 7 in st["eclosionados"] and st["descubiertas"][esp_esperada] == 0
    # cascaras saltando y revelacion
    while esc.hatch["t"] < 0.5:
        avanzar(esc, ctrl, 0.05, 1)
    capturar_escena(esc, SHOTS + "eclosion_cascaras.png")
    while esc.hatch["t"] < 0.95:
        avanzar(esc, ctrl, 0.05, 1)
    capturar_escena(esc, SHOTS + "eclosion_cascaras2.png")
    avanzar(esc, ctrl, 2.0)
    capturar_escena(esc, SHOTS + "revelacion.png")
    assert esc.b_hogar.activo
    pulsar(esc, ctrl, esc.b_hogar.rect)
    assert esc.modo == "hogar" and esc.hatch is None
    avanzar(esc, ctrl, 0.5)
    # se guardo en disco
    with open(per.archivo) as f:
        d = json.load(f)
    assert d["extra"]["tama"]["activa"]["especie"] == esp_esperada


def prueba_frotar_rapido_no_hace_trampa():
    """Sacudir el cursor a velocidades locas no acelera mas que frotar a ritmo normal."""
    app, esc, ctrl = nueva()
    TD.elegir_huevo(app.ctx.perfil, 3)
    esc.modo = "eclosion"

    def loco(e, c, t):
        c.mover_a(640 + (100 if int(t * 60) % 2 else -100), 385)
    escena_simular(esc, ctrl, loco, segundos=10, dibujar_cada=60)
    assert estado_de(app)["calor"] <= 10 * TD.CALOR_POR_SEGUNDO + 1e-6


def prueba_hogar_basico():
    app, esc, ctrl = hogar("dragon", 1)
    capturar_escena(esc, SHOTS + "hogar.png")
    m = estado_de(app)["activa"]
    # la mascota pasea y mira segun la direccion
    xs = set()
    for _ in range(40):
        avanzar(esc, ctrl, 0.5, 30)
        xs.add(round(esc.px))
    assert max(xs) - min(xs) > 20
    assert esc.m is m or esc.m["especie"] == m["especie"]
    # hambre baja: nube de estado y estado visual
    m["hambre"] = 18
    avanzar(esc, ctrl, 0.5)
    assert esc._estado_visual() == "hambre" and TD.necesidad_baja(app.ctx.perfil) == "hambre"
    capturar_escena(esc, SHOTS + "hogar_hambre.png")
    m["hambre"] = 80
    m["salud"] = 30
    avanzar(esc, ctrl, 0.3)
    assert esc._estado_visual() == "enfermo"
    capturar_escena(esc, SHOTS + "hogar_enfermo.png")
    m["salud"] = 100
    m["cacas"] = 3
    avanzar(esc, ctrl, 0.3)
    capturar_escena(esc, SHOTS + "hogar_cacas.png")


def prueba_comer():
    app, esc, ctrl = hogar("dragon", 1)
    per = app.ctx.perfil
    m = estado_de(app)["activa"]
    m["hambre"] = 30
    h0, f0 = m["hambre"], m["felicidad"]
    pulsar(esc, ctrl, esc.acc["comer"].rect)
    assert esc.sub == "comer" and len(esc.cartas) == 4, (esc.sub, esc.cartas)
    avanzar(esc, ctrl, 0.8)
    capturar_escena(esc, SHOTS + "comer.png")
    items = [c[0] for c in esc.cartas]
    assert "manzana" in items and "pan" in items
    # alimento de animales o semillas no aparecen
    assert "alimento_animal" not in items and not any(i.startswith("semilla") for i in items)
    n0 = per.cantidad("manzana")
    carta = [c for c in esc.cartas if c[0] == "manzana"][0]
    pulsar(esc, ctrl, carta[2].rect)
    assert esc.sub == "anim" and esc.anim["tipo"] == "comer"
    assert per.cantidad("manzana") == n0 - 1
    avanzar(esc, ctrl, 1.3)
    capturar_escena(esc, SHOTS + "comer_anim.png")
    avanzar(esc, ctrl, 2.5)
    assert esc.sub is None and esc.anim is None
    m = estado_de(app)["activa"]
    assert m["hambre"] > h0 and m["felicidad"] >= f0 and m["xp"] > 0
    # no se puede comer estando llena
    m["hambre"] = 99
    pulsar(esc, ctrl, esc.acc["comer"].rect)
    assert esc.sub is None and esc.aviso[1] > 0


def prueba_comer_favorita_marcada():
    app, esc, ctrl = hogar("delfin", 0, inv={"manzana": 2, "zanahoria": 2, "pan": 1, "huevo": 1, "pescado": 1})
    m = estado_de(app)["activa"]
    m["hambre"] = 40
    fav = TD.favorita("delfin")
    esc._accion_comer()
    avanzar(esc, ctrl, 0.8)
    favs = [c[0] for c in esc.cartas if catalogo.info(c[0])["cat"] == fav]
    assert favs, fav                                         # hay al menos una carta favorita marcada
    capturar_escena(esc, SHOTS + "comer_fav.png")


def prueba_sin_comida_y_granja():
    app, esc, ctrl = hogar("gato", 1, inv={})
    m = estado_de(app)["activa"]
    m["hambre"] = 20
    pulsar(esc, ctrl, esc.acc["comer"].rect)
    assert esc.sub == "comer" and esc.cartas == []
    avanzar(esc, ctrl, 0.8)
    capturar_escena(esc, SHOTS + "comer_vacio.png")
    assert app.ctx.perfil.cantidad("manzana") == 0
    pulsar(esc, ctrl, esc.b_c_granja.rect)
    assert nombre_escena(app) == "GranjaEscena", nombre_escena(app)
    gr = app.escena
    avanzar(gr, ctrl, 0.1)
    gr.tecla_esc()                                           # salir de la granja vuelve al hogar de mascotas
    assert nombre_escena(app) == "TamagotchiEscena" and app.escena.modo == "hogar"
    # cerrar el panel
    esc.sub = "comer"
    esc._cartas_comida()
    pulsar(esc, ctrl, esc.b_c_cerrar.rect)
    assert esc.sub is None


def prueba_comer_paginas():
    inv = {k: 2 for k in ("manzana", "naranja", "limon", "sandia", "kiwi", "zanahoria", "tomate", "lechuga", "papa",
                          "maiz", "calabaza", "huevo")}
    app, esc, ctrl = hogar("oso", 1, inv=inv)
    estado_de(app)["activa"]["hambre"] = 40
    esc._accion_comer()
    assert esc.comer_npag == 2 and len(esc.cartas) == 10
    avanzar(esc, ctrl, 0.7)
    pulsar(esc, ctrl, esc.b_c_next.rect)
    assert esc.comer_pag == 1 and len(esc.cartas) == 2
    capturar_escena(esc, SHOTS + "comer_pag2.png")


def prueba_jugar():
    app, esc, ctrl = hogar("conejo" if False else "raton", 1)
    per = app.ctx.perfil
    m = estado_de(app)["activa"]
    m["felicidad"] = 30
    f0 = m["felicidad"]
    pulsar(esc, ctrl, esc.acc["jugar"].rect)
    assert esc.sub == "jugar" and esc.jg is not None
    avanzar(esc, ctrl, 1.0)

    def bot(e, c, t):
        if e.jg is not None and e.jg["fin"] is None:
            c.mover_a(e.jg["bx"] + 4, e.jg["by"] - 6)      # pasa el cursor por encima de la pelota
        else:
            c.mover_a(640, 600)
    t = 0.0
    tomada = False
    while esc.jg is not None and t < 40:
        escena_simular(esc, ctrl, bot, segundos=1.0, dibujar_cada=30)
        t += 1.0
        if not tomada and esc.jg is not None and esc.jg["t"] < 12:
            capturar_escena(esc, SHOTS + "jugar.png")
            tomada = True
        if esc.jg is not None and esc.jg["fin"] is not None and not hasattr(esc, "_foto_fin"):
            esc._foto_fin = True
            capturar_escena(esc, SHOTS + "jugar_fin.png")
    assert tomada and esc.jg is None and esc.sub is None
    m = estado_de(app)["activa"]
    assert m["felicidad"] > f0 + 5 and m["cuidado"] >= 1
    # jugando sin hacer nada se obtienen pocos puntos pero no pasa nada malo
    pulsar(esc, ctrl, esc.acc["jugar"].rect)
    escena_simular(esc, ctrl, lambda e, c, t: c.mover_a(10, 650), segundos=25, dibujar_cada=60)
    assert esc.jg is None or esc.jg["fin"] is not None


def _hasta(esc, ctrl, cond, limite=20.0, paso=0.05):
    t = 0.0
    while not cond() and t < limite:
        avanzar(esc, ctrl, paso, 1000)
        t += paso
    assert cond(), "no se cumplio la condicion"


def prueba_limpiar_con_cacas_escoba_y_ducha():
    app, esc, ctrl = hogar("topo", 1)
    m = estado_de(app)["activa"]
    m["cacas"] = 2
    m["limpieza"] = 30
    pantalla()
    capturar_escena(esc, "/tmp/shots/tama_limpiar_sucio.png")
    pulsar(esc, ctrl, esc.acc["limpiar"].rect)
    a = esc.anim
    assert esc.sub == "anim" and a["tipo"] == "limpiar" and a["n"] == 2
    # los datos NO cambian hasta el final (limpiar se llama una sola vez)
    m = estado_de(app)["activa"]
    assert m["cacas"] == 2 and m["limpieza"] < 40
    llamadas = []
    original = TD.limpiar
    TD.limpiar = lambda perfil: (llamadas.append(1), original(perfil))[1]
    try:
        # escoba en la caca 1
        _hasta(esc, ctrl, lambda: 0 in a["visitas"])
        assert a["visitas"] == [0]
        _hasta(esc, ctrl, lambda: a["t"] > 1.0 and a["t"] % 2.0 > 0.8 or a["t"] > 2.0)
        while a["t"] % 2.0 < 0.9 and a["t"] < 2.0:
            avanzar(esc, ctrl, 0.05, 1000)
        capturar_escena(esc, "/tmp/shots/tama_limpiar_escoba1.png")
        _hasta(esc, ctrl, lambda: 1 in a["visitas"])
        assert a["visitas"] == [0, 1] and a["quitadas"][:1] == [0]
        while a["t"] < 3.0:
            avanzar(esc, ctrl, 0.05, 1000)
        capturar_escena(esc, "/tmp/shots/tama_limpiar_escoba2.png")
        _hasta(esc, ctrl, lambda: a["t"] >= a["t_bano"] + 1.0)
        assert a["quitadas"] == [0, 1]
        capturar_escena(esc, "/tmp/shots/tama_limpiar_ducha.png")
        # el cursor se mueve durante la secuencia sin romper ni cortar nada
        escena_simular(esc, ctrl, lambda e, c, t: c.mover_a(100 + 900 * abs(math.sin(t * 3)), 200 + 400 * abs(math.cos(t * 2))),
                       segundos=0.3, dibujar_cada=5)
        assert esc.sub == "anim"
        _hasta(esc, ctrl, lambda: a["t"] >= a["t_bano"] + 2.6)
        capturar_escena(esc, "/tmp/shots/tama_limpiar_limpio.png")
        assert len(llamadas) == 0
        _hasta(esc, ctrl, lambda: esc.sub is None)
    finally:
        TD.limpiar = original
    assert len(llamadas) == 1
    m = estado_de(app)["activa"]
    assert m["cacas"] == 0 and m["limpieza"] >= 75
    assert a["dur"] <= 2 * 3.0 + 3.0 + 1e-6
    assert esc.aviso[1] > 0


def prueba_limpiar_sin_cacas_solo_ducha():
    app, esc, ctrl = hogar("topo", 1)
    m = estado_de(app)["activa"]
    m.update(cacas=0, limpieza=40)
    pulsar(esc, ctrl, esc.acc["limpiar"].rect)
    a = esc.anim
    assert a["n"] == 0 and a["t_bano"] == 0 and abs(a["dur"] - 3.0) < 1e-6
    avanzar(esc, ctrl, 1.0, 5)
    assert a["visitas"] == [] and not a["quitadas"]
    _hasta(esc, ctrl, lambda: esc.sub is None)
    m = estado_de(app)["activa"]
    assert m["limpieza"] >= 85 and m["cacas"] == 0


def prueba_limpiar_ya_limpio():
    app, esc, ctrl = hogar("topo", 1)
    m = estado_de(app)["activa"]
    m.update(cacas=0, limpieza=95)
    pulsar(esc, ctrl, esc.acc["limpiar"].rect)
    assert esc.sub is None and esc.anim is None and esc.aviso[1] > 0 and "limpiecito" in esc.aviso[0]
    assert estado_de(app)["activa"]["limpieza"] > 94.5
    # limpieza justo bajo 90 si hace el bano
    m["limpieza"] = 89
    pulsar(esc, ctrl, esc.acc["limpiar"].rect)
    assert esc.sub == "anim" and esc.anim["n"] == 0


def prueba_polvo_segun_limpieza():
    app, esc, ctrl = hogar("oso", 2)
    p = pantalla()
    m = estado_de(app)["activa"]
    cx, cy = 640, ET.SUELO_Y - esc._alto_pet() / 2

    def foto(limpieza):
        m["limpieza"] = limpieza
        m["cacas"] = 0
        esc.px, esc.hop, esc.vdir = 640.0, 0.0, 1
        esc.ptarget = 640.0
        esc.pespera = 99
        esc.ov = ("normal", esc.t + 99)
        esc.parts.l = []
        esc.dibujar(p)
        r = pygame.Rect(int(cx - 160), int(cy - 150), 320, 300)
        return p.subsurface(r).copy()
    limpio = foto(100)
    assert esc._nivel_polvo() == 0
    niveles = {}
    for l in (60, 45, 30, 10):
        img = foto(l)
        niveles[l] = (esc._nivel_polvo(), _diferencia(limpio, img))
    assert [niveles[l][0] for l in (60, 45, 30, 10)] == [1, 2, 3, 4]
    d = [niveles[l][1] for l in (60, 45, 30, 10)]
    assert d[0] > 0 and d == sorted(d), d                     # mas manchas mientras mas baja
    assert _diferencia(limpio, foto(70)) == 0 and _diferencia(limpio, foto(65)) == 0   # sin polvo con limpieza alta
    # estable: dos cuadros seguidos iguales (no parpadea)
    a1, a2 = foto(20), foto(20)
    assert _diferencia(a1, a2) == 0
    # el polvo cabe dentro del cuerpo: el dibujo base no se altera (la mascota sigue igual fuera de las manchas)
    capturar_escena(esc, SHOTS + "polvo.png")


def _diferencia(a, b):
    n = 0
    w, h = a.get_size()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if a.get_at((x, y)) != b.get_at((x, y)):
                n += 1
    return n


def prueba_polvo_barrido_y_costo():
    p = pantalla()
    for esp in TD.ORDEN:
        for et in range(4):
            app = AppFalsa()
            mascota(app.ctx.perfil, esp, et, limpieza=12.0, cacas=2)
            app, esc, ctrl = nueva(inv=COMIDA, app=app)
            assert esc._nivel_polvo() == 4
            escena_simular(esc, ctrl, None, 0.2, dibujar_cada=3)
            for vd in (1, -1):
                esc.vdir = vd
                esc.dibujar(p)
            # secuencia completa de limpieza (solo para una etapa por especie, es larga)
            if et == TD.ORDEN.index(esp) % 4:
                esc._accion_limpiar()
                assert esc.sub == "anim"
                while esc.anim is not None:
                    escena_simular(esc, ctrl, None, 0.4, dibujar_cada=4)
                assert estado_de(app)["activa"]["cacas"] == 0
    # costo: el primer cuadro arma las manchas; los siguientes usan cache
    app = AppFalsa()
    mascota(app.ctx.perfil, "dragon", 3, limpieza=10.0)
    app, esc, ctrl = nueva(inv=COMIDA, app=app)
    esc.dibujar(p)
    t0 = time.time()
    for _ in range(60):
        esc.actualizar(1 / 60, ctrl)
        esc.dibujar(p)
    con = (time.time() - t0) / 60
    estado_de(app)["activa"]["limpieza"] = 100
    t0 = time.time()
    for _ in range(60):
        esc.actualizar(1 / 60, ctrl)
        esc.dibujar(p)
    sin = (time.time() - t0) / 60
    print("  con polvo %.1f ms, sin polvo %.1f ms por cuadro" % (con * 1000, sin * 1000))
    assert con < 0.05 and con - sin < 0.008


def prueba_dormir_y_despertar():
    app, esc, ctrl = hogar("buho", 1)
    m = estado_de(app)["activa"]
    m["energia"] = 40
    pulsar(esc, ctrl, esc.acc["dormir"].rect)
    m = estado_de(app)["activa"]
    assert m["dormida"] is True
    avanzar(esc, ctrl, 0.8)
    capturar_escena(esc, SHOTS + "hogar_noche.png")
    assert esc._estado_visual() == "duerme"
    # duerme y recupera energia con el paso del tiempo
    t0 = time.time()
    TD.tick(app.ctx.perfil, t0 + 60)
    assert estado_de(app)["activa"]["energia"] > 40
    # despertar con el boton grande
    pulsar(esc, ctrl, esc.b_despertar.rect)
    assert estado_de(app)["activa"]["dormida"] is False
    avanzar(esc, ctrl, 0.5)
    assert esc._estado_visual() != "duerme"
    # no quiere dormir si no tiene sueno
    estado_de(app)["activa"]["energia"] = 100
    pulsar(esc, ctrl, esc.acc["dormir"].rect)
    assert estado_de(app)["activa"]["dormida"] is False
    # se despierta sola al llegar a 100 de energia
    m = estado_de(app)["activa"]
    m["energia"] = 99
    TD.dormir(app.ctx.perfil, True)
    TD.tick(app.ctx.perfil, time.time() + 30)
    esc._t_tick = 1.0
    avanzar(esc, ctrl, 0.7)
    assert estado_de(app)["activa"]["dormida"] is False


def _bot_curitas(e, c, t):
    """Cursor que va tocando la primera marca visible (y espera lejos si no hay)."""
    a = e.anim
    if a is None or not a["marcas"]:
        return
    cx, cy = e._centro_pet()
    for mk in a["marcas"]:
        if mk["est"] == 1:
            c.mover_a(cx + mk["dx"], cy + mk["dy"])
            return
    c.mover_a(100, 330)


def _bot_lejos(e, c, t):
    c.mover_a(100, 330)


def _iniciar_curar(esc, ctrl):
    """Pulsa CURAR por permanencia y deja el cursor lejos de la mascota."""
    pulsar(esc, ctrl, esc.acc["curar"].rect)
    ctrl.mover_a(100, 330)
    escena_simular(esc, ctrl, _bot_lejos, 0.05, dibujar_cada=1000)
    assert esc.sub == "anim" and esc.anim["tipo"] == "curar", "no empezo la sesion de curar"
    return esc.anim


def _correr(esc, ctrl, bot, cond, limite=40.0, paso=0.05):
    t = 0.0
    while not cond() and t < limite:
        escena_simular(esc, ctrl, bot, paso, dibujar_cada=1000)
        t += paso
    assert cond(), "no se cumplio la condicion en %.0f s" % limite


def _contar_fin():
    """Envuelve TD.curar_fin y cuenta cuantas veces dio recompensa de verdad."""
    cuenta = {"n": 0}
    orig = TD.curar_fin

    def f(perfil, ctx):
        r = orig(perfil, ctx)
        cuenta["n"] += 1 if r else 0
        return r
    TD.curar_fin = f
    return cuenta, lambda: setattr(TD, "curar_fin", orig)


def prueba_curar_sesion_con_cursor():
    app, esc, ctrl = hogar("rana", 1, hp=0.25, salud=40)
    m = estado_de(app)["activa"]
    cu0, fe0, xp0 = m["cuidado"], m["felicidad"], m["xp"]
    assert TD.necesita_curar(app.ctx.perfil)
    capturar_escena(esc, "/tmp/shots/tama_hogar_vida.png")
    cuenta, restaurar = _contar_fin()
    try:
        a = _iniciar_curar(esc, ctrl)
        assert a["n"] == TD.CURAR_PASOS == 6 and a["k"] == 0
        m = estado_de(app)["activa"]
        assert 0.25 <= m["hp"] < 0.28 and 40 <= m["salud"] < 44, "al empezar no se cura (solo regeneracion natural)"
        # los otros botones estan bloqueados durante la sesion
        pulsar(esc, ctrl, esc.acc["comer"].rect)
        assert app.escena is None and esc.sub == "anim"
        pulsar(esc, ctrl, esc.b_cuaderno.rect)
        assert esc.libro is None and esc.sub == "anim"
        ctrl.mover_a(100, 330)
        # marcas de a una (cursor lejos)
        _correr(esc, ctrl, _bot_lejos, lambda: a["t"] >= 5.0 and sum(1 for k in a["marcas"] if k["est"] == 1) >= 2)
        vis = [k for k in a["marcas"] if k["est"] >= 1]
        assert len(vis) == 2 and len(a["marcas"]) == 6 and a["k"] == 0
        capturar_escena(esc, "/tmp/shots/tama_curar_marcas.png")
        # tocar una: curita, la marca desaparece y la vida sube suave
        _correr(esc, ctrl, _bot_curitas, lambda: a["k"] >= 1, 6.0)
        assert a["k"] == 1
        m = estado_de(app)["activa"]
        assert m["hp"] > 0.25 and m["hp"] < 1.0
        escena_simular(esc, ctrl, _bot_lejos, 0.3, dibujar_cada=1000)
        capturar_escena(esc, "/tmp/shots/tama_curar_curita.png")
        assert esc.vis["hp"] < estado_de(app)["activa"]["hp"] + 1e-6
        _correr(esc, ctrl, _bot_curitas, lambda: a["k"] >= 3, 12.0)
        escena_simular(esc, ctrl, _bot_curitas, 0.6, dibujar_cada=1000)
        capturar_escena(esc, "/tmp/shots/tama_curar_progreso.png")
        hp3 = estado_de(app)["activa"]["hp"]
        assert 0.26 < hp3 < 1.0 and cuenta["n"] == 0
        _correr(esc, ctrl, _bot_curitas, lambda: a["completo"], 20.0)
        assert a["k"] == 6 and cuenta["n"] == 1
        m = estado_de(app)["activa"]
        assert m["hp"] == 1.0 and m["salud"] == 100.0
        escena_simular(esc, ctrl, _bot_lejos, 0.5, dibujar_cada=1000)
        capturar_escena(esc, "/tmp/shots/tama_curar_fin.png")
        _correr(esc, ctrl, _bot_lejos, lambda: esc.anim is None, 10.0)
        dur = a["t_real"]
    finally:
        restaurar()
    assert 20.0 <= dur <= 25.0, dur
    assert esc.sub is None and "Vida recuperada" in esc.aviso[0]
    assert cuenta["n"] == 1, "curar_fin debe dar la recompensa una sola vez"
    m = estado_de(app)["activa"]
    assert m["cuidado"] == cu0 + TD.CUIDADO_CURAR and m["felicidad"] >= fe0
    assert m["xp"] >= xp0
    assert TD.puede_entrenar(app.ctx.perfil) and not TD.necesita_curar(app.ctx.perfil)
    # las barras llegan a los valores finales
    avanzar(esc, ctrl, 1.5)
    assert abs(esc.vis["hp"] - 1.0) < 0.01 and abs(esc.vis["salud"] - 100) < 1


def prueba_curar_sesion_pasiva():
    """Sin tocar nada: las curitas se ponen solas y dura entre 20 y 25 s."""
    app, esc, ctrl = hogar("topo", 2, hp=0.2, salud=30)
    cuenta, restaurar = _contar_fin()
    try:
        a = _iniciar_curar(esc, ctrl)
        _correr(esc, ctrl, _bot_lejos, lambda: esc.anim is None, 40.0)
        dur = a["t_real"]
    finally:
        restaurar()
    assert 20.0 <= dur <= 25.0, dur
    assert a["k"] == 6 and cuenta["n"] == 1
    m = estado_de(app)["activa"]
    assert m["hp"] == 1.0 and m["salud"] == 100.0 and esc.sub is None
    # nunca se queda trabado: ninguna marca espera mas de CURA_AUTO + margen
    assert all(k["est"] >= 2 for k in a["marcas"])


def prueba_curar_cancelar_a_la_mitad():
    for como in ("volver", "esc"):
        app, esc, ctrl = hogar("conejo" if "conejo" in TD.ORDEN else "rana", 1, hp=0.25, salud=40)
        m = estado_de(app)["activa"]
        cu0 = m["cuidado"]
        cuenta, restaurar = _contar_fin()
        try:
            a = _iniciar_curar(esc, ctrl)
            _correr(esc, ctrl, _bot_curitas, lambda: a["k"] >= 3, 20.0)
            if como == "volver":
                pulsar(esc, ctrl, esc.b_volver.rect)
            else:
                esc.tecla_esc()
        finally:
            restaurar()
        assert app.escena is None, "cancelar no debe salir del hogar"
        assert esc.sub is None and esc.anim is None
        m = estado_de(app)["activa"]
        assert 0.25 < m["hp"] < 1.0 and m["salud"] < 100, "conserva lo ya curado, sin curacion completa"
        assert cuenta["n"] == 1 and m["cuidado"] == cu0 + TD.CUIDADO_CURAR
        hp = m["hp"]
        avanzar(esc, ctrl, 1.0)
        assert estado_de(app)["activa"]["hp"] >= hp - 1e-9
        # cancelar sin curitas: sin recompensa
    app, esc, ctrl = hogar("rana", 1, hp=0.25, salud=40)
    m = estado_de(app)["activa"]
    cu0 = m["cuidado"]
    a = _iniciar_curar(esc, ctrl)
    esc.tecla_esc()
    assert esc.sub is None and estado_de(app)["activa"]["cuidado"] == cu0 and estado_de(app)["activa"]["hp"] < 0.28


def prueba_curar_sana_no_hace_nada():
    app, esc, ctrl = hogar("rana", 1, hp=1.0, salud=100)
    assert not TD.necesita_curar(app.ctx.perfil)
    m = estado_de(app)["activa"]
    antes = (m["hp"], m["salud"], m["cuidado"], m["xp"])
    pulsar(esc, ctrl, esc.acc["curar"].rect)
    assert esc.sub is None and esc.anim is None and "sanita" in esc.aviso[0] and esc.aviso[1] > 0
    m = estado_de(app)["activa"]
    assert antes == (m["hp"], m["salud"], m["cuidado"], m["xp"])


def prueba_entrenar_bloqueado_con_poca_vida():
    app, esc, ctrl = hogar("dragon", 2, hp=0.19)
    assert not TD.puede_entrenar(app.ctx.perfil)
    pulsar(esc, ctrl, esc.acc["entrenar"].rect)
    assert app.escena is None, "con vida 0.19 no debe empezar la batalla"
    assert "cúrame" in esc.aviso[0] and esc.aviso[1] > 0
    assert esc.acc["curar"].pulso and esc.pulso_hasta > esc.t
    capturar_escena(esc, "/tmp/shots/tama_entrenar_bloqueado.png")
    app, esc, ctrl = hogar("dragon", 2, hp=0.2)
    assert TD.puede_entrenar(app.ctx.perfil)
    pulsar(esc, ctrl, esc.acc["entrenar"].rect)
    assert nombre_escena(app) == "Partida"
    # al volver de una batalla con poca vida: hogar con nube de salud y CURAR pulsando
    app, esc, ctrl = hogar("dragon", 2, hp=0.15, salud=60)
    avanzar(esc, ctrl, 0.5)
    assert esc.acc["curar"].pulso and TD.necesidad_baja(app.ctx.perfil) == "salud"
    capturar_escena(esc, "/tmp/shots/tama_hogar_vida_baja.png")
    estado_de(app)["activa"]["hp"] = 0.6
    avanzar(esc, ctrl, 0.3)
    assert not esc.acc["curar"].pulso


def prueba_barra_vida_refleja_hp():
    from escena_tama_ui import colores_vida
    app, esc, ctrl = hogar("rana", 1)
    p = pantalla()
    for hp in (1.0, 0.75, 0.45, 0.28, 0.1):
        estado_de(app)["activa"]["hp"] = hp
        avanzar(esc, ctrl, 1.6)
        assert abs(esc.vis["hp"] - hp) < 0.02, (hp, esc.vis["hp"])
        esc.dibujar(p)
    assert len({colores_vida(v)[1] for v in (1.0, 0.45, 0.1)}) == 3
    g = colores_vida(1.0)[1]
    r = colores_vida(0.1)[1]
    assert g[1] > g[0] and r[0] > r[1], "verde arriba, rojo abajo"
    # las 6 tarjetas caben en pantalla sin cortarse
    n = len(ET.NECESIDADES)
    assert n == 6 and ET.NECESIDADES[-1][0] == "hp"
    gap = 6
    w = (ANCHO - 24 - (n - 1) * gap) // n
    x0 = (ANCHO - (n * w + (n - 1) * gap)) // 2
    assert x0 >= 8 and x0 + n * w + (n - 1) * gap <= ANCHO - 8 and w >= 190
    # parpadeo suave bajo 30 %: el cuadro cambia con el tiempo
    estado_de(app)["activa"]["hp"] = 0.1
    avanzar(esc, ctrl, 1.0)
    esc.t = 0.0
    esc.dibujar(p)
    a1 = pygame.image.tobytes(p.subsurface((x0 + 5 * (w + gap), 108, w, 46)), "RGB")
    esc.t = 0.26
    esc.dibujar(p)
    a2 = pygame.image.tobytes(p.subsurface((x0 + 5 * (w + gap), 108, w, 46)), "RGB")
    assert a1 != a2
    assert TD.HP_URGENTE == 0.30


def prueba_curar_barrido_18_especies():
    from escena_tama_ui import marcas_mascota
    p = pantalla()
    peor = 0.0
    for esp in TD.ORDEN:
        for et in range(4):
            app = AppFalsa()
            mascota(app.ctx.perfil, esp, et, hp=0.3, salud=50, limpieza=40)
            app, esc, ctrl = nueva(inv=COMIDA, app=app)
            escena_simular(esc, ctrl, None, 0.2, dibujar_cada=1000)
            esc._accion_curar()
            a = esc.anim
            assert a is not None and a["tipo"] == "curar"
            _correr(esc, ctrl, _bot_lejos, lambda: bool(a["marcas"]), 3.0)
            pts = marcas_mascota(esp, et, ET.ESC_HOGAR[et], esc.vdir, 6)
            assert len(pts) == 6
            for i in range(6):
                for j in range(i + 1, 6):
                    assert math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) >= 30, (esp, et, i, j)
            cx, cy = esc._centro_pet()
            for dx, dy in pts:
                assert 0 <= cx + dx <= ANCHO and 60 <= cy + dy <= ALTO
            for mk in a["marcas"]:
                mk["est"] = 1
            for vd in (1, -1):
                esc.vdir = vd
                t0 = time.time()
                esc.dibujar(p)
                peor = max(peor, time.time() - t0)
            esc._aplicar_curita(a, a["marcas"][0], cx, cy, esc._alto_pet())
            esc.dibujar(p)
            esc._terminar_curar(False)
    print("  curar con 6 marcas: peor cuadro %.1f ms" % (peor * 1000))
    assert peor < 0.12


def prueba_curar_costo_dibujo():
    app, esc, ctrl = hogar("dragon", 3, hp=0.3, salud=40)
    a = _iniciar_curar(esc, ctrl)
    _correr(esc, ctrl, _bot_lejos, lambda: sum(1 for k in a["marcas"] if k["est"] == 1) >= 2, 10.0)
    p = pantalla()
    esc.dibujar(p)
    t0 = time.time()
    for _ in range(60):
        esc.actualizar(1 / 60, ctrl)
        esc.dibujar(p)
    dt = (time.time() - t0) / 60
    print("  sesion de curar: %.1f ms por cuadro" % (dt * 1000))
    assert dt < 0.03


def prueba_evolucion():
    app, esc, ctrl = hogar("fenix", 0)
    per = app.ctx.perfil
    m = estado_de(app)["activa"]
    avanzar(esc, ctrl, 0.5)
    assert not TD.puede_evolucionar(per)
    m["xp"] = TD.xp_necesaria(0)
    m["cuidado"] = TD.CUIDADO_MIN[0]
    avanzar(esc, ctrl, 0.6)
    assert TD.puede_evolucionar(per)
    capturar_escena(esc, SHOTS + "evolucion_boton.png")
    pulsar(esc, ctrl, esc.b_evo.rect)
    assert esc.sub == "evo" and esc.evo is not None
    assert estado_de(app)["activa"]["etapa"] == 1
    e = esc.evo
    for t_obj, nombre in ((1.5, "a"), (2.9, "b"), (4.1, "c"), (5.0, "d")):
        while esc.evo is not None and esc.evo["t"] < t_obj:
            avanzar(esc, ctrl, 0.1, 5)
        capturar_escena(esc, SHOTS + "evolucion_%s.png" % nombre)
    avanzar(esc, ctrl, 1.3)
    capturar_escena(esc, SHOTS + "evolucion.png")
    assert esc.b_evo_ok.activo
    pulsar(esc, ctrl, esc.b_evo_ok.rect)
    assert esc.sub is None and esc.evo is None
    m = estado_de(app)["activa"]
    assert m["etapa"] == 1 and m["nombre"] == TD.ESPECIES["fenix"]["formas"][1]
    assert estado_de(app)["descubiertas"]["fenix"] == 1
    avanzar(esc, ctrl, 0.5)
    capturar_escena(esc, SHOTS + "hogar_evolucionado.png")


def prueba_evolucion_dando_xp_con_comida():
    app, esc, ctrl = hogar("lobo", 0, inv={"pan": 5, "manzana": 5})
    m = estado_de(app)["activa"]
    m["hambre"] = 20
    m["xp"] = TD.xp_necesaria(0) - 2
    m["cuidado"] = 10
    esc._accion_comer()
    avanzar(esc, ctrl, 0.8)
    carta = [c for c in esc.cartas if c[0] == "pan"][0]
    pulsar(esc, ctrl, carta[2].rect)
    avanzar(esc, ctrl, 3.5)
    assert TD.puede_evolucionar(app.ctx.perfil)
    assert esc.sub is None


def prueba_graduar():
    app, esc, ctrl = hogar("pinguino", 3)
    per = app.ctx.perfil
    m = estado_de(app)["activa"]
    m["xp"] = TD.xp_necesaria(3)
    m["cuidado"] = TD.CUIDADO_MIN[3]
    avanzar(esc, ctrl, 0.6)
    assert TD.puede_graduar(per) and not TD.puede_evolucionar(per)
    capturar_escena(esc, SHOTS + "graduar_boton.png")
    # el jugador puede elegir seguir con ella
    pulsar(esc, ctrl, esc.b_graduar.rect)
    assert esc.sub == "graduar"
    avanzar(esc, ctrl, 0.8)
    capturar_escena(esc, SHOTS + "graduar.png")
    pulsar(esc, ctrl, esc.b_g_no.rect)
    assert esc.sub is None and estado_de(app)["activa"] is not None and not estado_de(app)["salon"]
    # y luego pasar al salon
    pulsar(esc, ctrl, esc.b_graduar.rect)
    pulsar(esc, ctrl, esc.b_g_si.rect)
    st = estado_de(app)
    assert st["activa"] is None and len(st["salon"]) == 1 and st["salon"][0]["especie"] == "pinguino"
    assert esc.modo == "salon"
    avanzar(esc, ctrl, 0.8)
    capturar_escena(esc, SHOTS + "salon.png")
    pulsar(esc, ctrl, esc.libro.b_volver.rect)
    assert esc.modo == "huevos" and esc.libro is None
    avanzar(esc, ctrl, 0.4)
    # se puede elegir otro huevo
    pulsar(esc, ctrl, esc.cards[1].rect)
    assert esc.modo == "eclosion" and estado_de(app)["huevo"] == 1


def prueba_salon_vacio_y_paginas():
    app, esc, ctrl = nueva()
    pulsar(esc, ctrl, esc.b_salon.rect)
    assert esc.modo == "salon"
    avanzar(esc, ctrl, 0.5)
    capturar_escena(esc, SHOTS + "salon_vacio.png")
    esc.tecla_esc()
    assert esc.modo == "huevos"
    st = estado_de(app)
    for i, sp in enumerate(TD.ORDEN[:11]):
        st["salon"].append(dict(especie=sp, etapa=3, nombre=TD.ESPECIES[sp]["formas"][3]))
    esc._abrir_libro("salon")
    assert esc.libro._paginas() == 2
    avanzar(esc, ctrl, 0.5)
    capturar_escena(esc, SHOTS + "salon_lleno.png")
    pulsar(esc, ctrl, esc.libro.b_next.rect)
    assert esc.libro.pag == 1
    avanzar(esc, ctrl, 0.3)
    capturar_escena(esc, SHOTS + "salon_pag2.png")


def prueba_cuaderno():
    app = AppFalsa()
    per = app.ctx.perfil
    st = TD.estado(per)
    st["descubiertas"].update({"dragon": 3, "delfin": 1, "tortuga": 0, "lobo": 2, "gato": 0})
    mascota(per, "delfin", 1)
    app, esc, ctrl = nueva(app=app)
    avanzar(esc, ctrl, 0.5)
    pulsar(esc, ctrl, esc.b_cuaderno.rect)
    assert esc.modo == "cuaderno" and esc.libro is not None
    avanzar(esc, ctrl, 0.5)
    capturar_escena(esc, SHOTS + "cuaderno.png")           # pagina de Agua (la de su mascota)
    assert esc.libro.pag == 0
    for i, tab in enumerate(esc.libro.tabs):
        pulsar(esc, ctrl, tab.rect)
        assert esc.libro.pag == i
        avanzar(esc, ctrl, 0.2)
        if i == 2:
            capturar_escena(esc, SHOTS + "cuaderno_fuego.png")
    assert esc.libro._total() == 2 + 1 + 4 + 3 + 1
    pulsar(esc, ctrl, esc.libro.b_volver.rect)
    assert esc.modo == "hogar" and esc.libro is None


def prueba_barrido_18_especies():
    """Nada se rompe con ninguna de las 18 especies en las 4 etapas, en el hogar y en las animaciones."""
    p = pantalla()
    for esp in TD.ORDEN:
        for et in range(4):
            app = AppFalsa()
            per = app.ctx.perfil
            m = mascota(per, esp, et, hambre=20 if et % 2 else 80)
            app, esc, ctrl = nueva(inv=COMIDA, app=app)
            escena_simular(esc, ctrl, None, 0.3, dibujar_cada=5)
            for estado_v in ("normal", "feliz", "triste", "hambre", "duerme", "enfermo", "come"):
                esc.ov = (estado_v, esc.t + 5)
                esc.dibujar(p)
        # cada huevo -> eclosion -> revelacion de esa especie
    for k in range(18):
        app, esc, ctrl = nueva()
        assert TD.elegir_huevo(app.ctx.perfil, k)
        esc.modo = "eclosion"
        for grieta in (0.05, 0.3, 0.5, 0.7, 0.95):
            estado_de(app)["calor"] = grieta
            esc.dibujar(p)
        estado_de(app)["calor"] = 0.999
        TD.calentar(app.ctx.perfil, 0.01)
        escena_simular(esc, ctrl, None, 0.1)
        assert esc.hatch is not None
        for t in (0.2, 0.8, 1.5, 2.5):
            esc.hatch["t"] = t
            esc.dibujar(p)
    # cuaderno con todo descubierto y con nada, cada pagina
    for completo in (False, True):
        app = AppFalsa()
        if completo:
            TD.estado(app.ctx.perfil)["descubiertas"].update({e: 3 for e in TD.ORDEN})
        app, esc, ctrl = nueva(app=app)
        esc._abrir_libro("cuaderno")
        for i in range(6):
            esc.libro.pag = i
            esc.dibujar(p)
            if completo and i in (0, 5):
                capturar_escena(esc, SHOTS + "cuaderno_completo_%d.png" % i)


def prueba_evolucion_todas():
    """La cinematica corre completa para las 18 especies (cada una en una etapa distinta)."""
    for i, esp in enumerate(TD.ORDEN):
        et = i % 3
        app = AppFalsa()
        per = app.ctx.perfil
        mascota(per, esp, et, xp=TD.xp_necesaria(et), cuidado=TD.CUIDADO_MIN[et])
        app, esc, ctrl = nueva(inv=COMIDA, app=app)
        avanzar(esc, ctrl, 0.2, 30)
        esc._iniciar_evo()
        assert esc.sub == "evo"
        while esc.evo is not None and esc.evo["t"] < 6.0:
            escena_simular(esc, ctrl, None, 0.5, dibujar_cada=15)
        assert estado_de(app)["activa"]["etapa"] == et + 1


def prueba_tick_no_mata():
    app, esc, ctrl = hogar("armadillo", 2)
    per = app.ctx.perfil
    m = estado_de(app)["activa"]
    m.update(hambre=0.0, felicidad=0.0, energia=0.0, limpieza=0.0, salud=10.0)
    TD.tick(per, time.time() + 36000)
    TD.tick(per, time.time() + 36000 * 2)
    avanzar(esc, ctrl, 3.0, 20)
    m = estado_de(app)["activa"]
    assert m is not None and m["salud"] >= TD.SALUD_MIN
    assert esc.modo == "hogar"
    capturar_escena(esc, SHOTS + "hogar_descuidado.png")
    for estado_v in ("triste", "enfermo", "hambre"):
        esc.ov = (estado_v, esc.t + 5)
        esc.dibujar(pantalla())


def prueba_abrir_con_ausencia_larga():
    """Reabrir la escena tras mucho tiempo: la mascota sigue viva y se puede cuidar."""
    app = AppFalsa()
    per = app.ctx.perfil
    m = mascota(per, "escarabajo", 1)
    m["ultimo"] = time.time() - 3 * 24 * 3600
    app, esc, ctrl = nueva(app=app)
    m = estado_de(app)["activa"]
    assert m["hambre"] >= TD.OFFLINE_MINIMO and m["salud"] >= TD.SALUD_MIN
    avanzar(esc, ctrl, 0.5)


def prueba_persistencia():
    app = AppFalsa()
    per = app.ctx.perfil
    esc = TamagotchiEscena(app)
    ctrl = ControlSim()
    pulsar(esc, ctrl, esc.cards[9].rect)
    assert estado_de(app)["huevo"] == 9
    TD.calentar(per, 0.5)
    esc._guardar()
    # recrear la escena: sigue en la eclosion con el mismo calor
    esc2 = TamagotchiEscena(app)
    assert esc2.modo == "eclosion" and abs(estado_de(app)["calor"] - 0.5) < 1e-6
    # desde el disco, con otro Perfil
    per2 = Perfil(per.archivo)
    assert TD.estado(per2)["huevo"] == 9 and abs(TD.estado(per2)["calor"] - 0.5) < 1e-6
    # eclosiona, cuida y recrea
    frotar(esc2, ControlSim(), 28)
    assert estado_de(app)["activa"] is not None
    sp = estado_de(app)["activa"]["especie"]
    esc3 = TamagotchiEscena(app)
    assert esc3.modo == "hogar" and esc3.m["especie"] == sp
    TD.comer(per, "manzana") if per.cantidad("manzana") else None
    per.dar("manzana", 2)
    esc3._guardar()
    per3 = Perfil(per.archivo)
    assert TD.estado(per3)["activa"]["especie"] == sp and per3.cantidad("manzana") >= 2


def prueba_volver_y_navegacion():
    # juego libre: Volver -> Libre
    app, esc, ctrl = nueva()
    pulsar(esc, ctrl, esc.b_volver.rect)
    assert nombre_escena(app) == "Libre", nombre_escena(app)
    # ESC dentro del hogar vuelve; ESC en un panel solo lo cierra
    app, esc, ctrl = hogar("oso", 1)
    estado_de(app)["activa"]["hambre"] = 30
    esc._accion_comer()
    esc.tecla_esc()
    assert esc.sub is None and nombre_escena(app) != "Libre"
    esc.tecla_esc()
    assert nombre_escena(app) == "Libre"


def prueba_entrenar_lanza_batalla():
    """ENTRENAR lanza la pelea nueva (Horda Elemental); no aparece como minijuego suelto."""
    import aventura
    assert "horda" in aventura.JUEGOS_TODOS and "horda" not in aventura.JUEGOS
    app, esc, ctrl = hogar("dragon", 2)
    pulsar(esc, ctrl, esc.acc["entrenar"].rect)
    assert nombre_escena(app) == "Partida" and app.escena.juego_id == "horda"
    # al terminar la pelea se vuelve a la pantalla del Tamagotchi
    r = aventura.Resultado.volver_a(app, "horda")
    assert isinstance(r, TamagotchiEscena)
    # muy cansada: aviso amable y no lanza
    app, esc, ctrl = hogar("dragon", 2)
    estado_de(app)["activa"]["energia"] = 5
    pulsar(esc, ctrl, esc.acc["entrenar"].rect)
    assert app.escena is None and esc.aviso[1] > 0


def _app_con_mascota(especie, etapa):
    app = AppFalsa()
    mascota(app.ctx.perfil, especie, etapa)
    return app


def prueba_clic_y_mando():
    """Tambien funciona con clic (boton fisico) ademas de la permanencia."""
    app, esc, ctrl = hogar("dragon", 1)
    estado_de(app)["activa"]["hambre"] = 40
    pulsar_clic(esc, ctrl, esc.acc["comer"].rect)
    assert esc.sub == "comer"
    pulsar_clic(esc, ctrl, esc.b_c_cerrar.rect)
    assert esc.sub is None


def prueba_sin_perfil_roto():
    """Estado corrupto o ausente: la escena abre sin romperse."""
    app = AppFalsa()
    app.ctx.perfil.extra["tama"] = {"huevos": "basura", "activa": {"especie": "nada"}, "calor": "x"}
    esc = TamagotchiEscena(app)
    avanzar(esc, ControlSim(), 0.5)
    assert esc.modo == "huevos"
    app.ctx.perfil.extra = {}
    esc = TamagotchiEscena(app)
    avanzar(esc, ControlSim(), 0.5)


def prueba_rendimiento():
    app, esc, ctrl = hogar("dragon", 3)
    p = pantalla()
    t0 = time.time()
    for _ in range(60):
        esc.actualizar(1 / 60, ctrl)
        esc.dibujar(p)
    dt = (time.time() - t0) / 60
    print("  hogar: %.1f ms por cuadro" % (dt * 1000))
    assert dt < 0.1


PRUEBAS = [v for k, v in sorted(globals().items(), key=lambda kv: kv[1].__code__.co_firstlineno if callable(kv[1]) and hasattr(kv[1], "__code__") else 0)
           if k.startswith("prueba_")]

if __name__ == "__main__":
    pantalla()
    for f in PRUEBAS:
        t0 = time.time()
        f()
        print("OK  %-44s %.1fs" % (f.__name__, time.time() - t0))
    print("TODO OK")
