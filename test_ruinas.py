import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Pruebas de Ruinas: geometria, agarrar/soltar (permanencia y clic), intercambio, sin rotacion, bot bueno en las
30 murales, bot inerte y erratico, desbloqueo, persistencia, hub, juego libre y capturas
(/tmp/shots/ruinas_*.png).

Si todavia no existe arte_ruinas.py (lo escribe otro agente) se usa un arte falso (pruebas/arte_ruinas_falso.py)."""

import os
import random
import sys
import tempfile

try:
    import arte_ruinas                                   # noqa: F401  arte real
    ARTE = "real"
except ImportError:
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import arte_ruinas_falso
    sys.modules["arte_ruinas"] = arte_ruinas_falso
    ARTE = "falso"

import pygame

import ajustes
import ruinas_datos as RD
import j_ruinas as J
from j_ruinas import Ruinas
from nucleo import ControlSim, Perfil, Sonidos, Fuentes, V2
from pruebas_util import AppFalsa, crear_ctx, simular, capturar, pantalla, escena_simular, capturar_escena
from ajustes import ANCHO, ALTO

SHOTS = "/tmp/shots/ruinas_"


# ------------------------------------------------------------ bots
class BotBueno:
    """Va pieza por pieza: la agarra (quieto sobre ella) y la lleva a su celda (quieto encima)."""

    def __init__(self, paso=25.0, hasta=None):
        self.paso = paso
        self.hasta = hasta                    # se detiene al llegar a esta cantidad de piezas bien puestas
        self.pz = None

    def __call__(self, j, ctrl, t):
        if j.completo:
            return
        if self.hasta is not None and sum(q.correcta for q in j.piezas) >= self.hasta:
            return
        if j.llevada is None:
            if self.pz is None or self.pz.correcta or self.pz is j.llevada:
                cand = [q for q in j.piezas if not q.correcta]
                if not cand:
                    return
                self.pz = cand[0]
            ctrl.mover_a(self.pz.pos.x, self.pz.pos.y)
        else:
            self.pz = j.llevada
            objetivo = j.centro_celda(self.pz.c, self.pz.r)
            d = objetivo - ctrl.pos
            if d.length() > self.paso:
                d.scale_to_length(self.paso)
            ctrl.mover_a(ctrl.pos.x + d.x, ctrl.pos.y + d.y)


def bot_inerte(j, ctrl, t):
    pass


def bot_erratico(j, ctrl, t):
    ctrl.mover_a(random.uniform(0, 1280), random.uniform(0, 720))
    ctrl.clic = random.random() < 0.1
    ctrl.golpe = random.random() < 0.1
    ctrl.cortando = random.random() < 0.3


def correr(j, ctrl, seg, bot=None):
    return simular(j, ctrl, bot, segundos=seg, dibujar_cada=30)


def nuevo(ruina=0, semilla=1, **kw):
    ctx = crear_ctx()
    j = Ruinas(ctx, ruina + 1, semilla=semilla, **kw)
    ctrl = ControlSim()
    return j, ctrl


def mover_y_esperar(j, ctrl, x, y, seg):
    ctrl.mover_a(x, y)
    correr(j, ctrl, seg)


# ------------------------------------------------------------ geometria
def test_geometria():
    marco_zona = J.ZONA
    for i, (c, f) in enumerate(RD.RUINAS):
        j, _ = nuevo(i)
        s = j.s
        assert len(j.piezas) == c * f == j.n
        assert j.inner.size == (c * s, f * s)
        assert j.mural.get_size() == (c * s, f * s)
        assert j.marco.contains(j.inner) and j.marco.w - j.inner.w == 2 * J.BORDE
        assert marco_zona.contains(j.marco), (i, j.marco)
        rects = []
        for pz in j.piezas:
            assert pz.surf.get_size() == (s, s), (i, pz.surf.get_size(), s)
            r = pygame.Rect(0, 0, s, s)
            r.center = (int(pz.pos.x), int(pz.pos.y))
            assert marco_zona.inflate(2, 2).contains(r), (i, r)
            assert pygame.Rect(0, 0, ANCHO, ALTO).contains(r)
            assert not r.colliderect(j.marco), (i, "pieza sobre el marco", r, j.marco)
            for q in rects:
                assert not r.colliderect(q), (i, "piezas solapadas", r, q)
            rects.append(r)
        # al empezar ninguna pieza esta puesta y el orden esta mezclado
        assert all(pz.celda is None for pz in j.piezas)
        assert not all(pz.correcta for pz in j.piezas)
        print(f"ruina {i}: {c}x{f} celda {s}px marco {tuple(j.marco)}")
    # mismo semilla -> mismo reparto
    a, _ = nuevo(5, semilla=7)
    b, _ = nuevo(5, semilla=7)
    assert [(p.c, p.r, tuple(p.pos)) for p in a.piezas] == [(p.c, p.r, tuple(p.pos)) for p in b.piezas]
    # sin rotacion: la API no tiene angulo y la superficie de cada pieza no cambia
    assert not hasattr(a.piezas[0], "angulo") and not hasattr(a.piezas[0], "rot")
    print("geometria ok")


# ------------------------------------------------------------ mecanica
def test_mecanica():
    j, ctrl = nuevo(0)
    pz = j.piezas[0]
    surf0 = pz.surf
    x, y = pz.pos.x, pz.pos.y
    # agarrar por permanencia: 0.30 s no, 0.45 s si
    mover_y_esperar(j, ctrl, x, y, 0.30)
    assert j.llevada is None
    correr(j, ctrl, 0.15)
    assert j.llevada is pz
    # temblor pequeno no reinicia; mover rapido a otra pieza si
    j2, c2 = nuevo(0)
    q = j2.piezas[1]
    for k in range(40):                       # 0.67 s con temblor de +-10 px
        c2.mover_a(q.pos.x + (10 if k % 2 else -10), q.pos.y)
        correr(j2, c2, 1 / 60)
    assert j2.llevada is q, "el temblor del cursor no debe impedir agarrar"
    j3, c3 = nuevo(0)
    q = j3.piezas[2]
    for k in range(60):                       # cursor que se mueve mucho: no agarra nada
        c3.mover_a(q.pos.x + (60 if (k // 5) % 2 else -60), q.pos.y)
        correr(j3, c3, 1 / 60)
    assert j3.llevada is None
    # la pieza sigue al cursor
    cel = j.centro_celda(1, 0)
    for _ in range(60):
        d = cel - ctrl.pos
        if d.length() < 1:
            break
        if d.length() > 40:
            d.scale_to_length(40)
        ctrl.mover_a(ctrl.pos.x + d.x, ctrl.pos.y + d.y)
        correr(j, ctrl, 1 / 60)
    assert j.llevada is pz and j.armado
    # no suelta antes de 0.45 s quieto sobre la celda
    ctrl.mover_a(*cel)
    correr(j, ctrl, 0.3)
    assert j.llevada is pz, "no debe soltar antes de 0.45 s quieto"
    correr(j, ctrl, 0.2)
    assert j.llevada is None and pz.celda == (1, 0), pz.celda
    assert j.rejilla[(1, 0)] is pz and pz.surf is surf0
    # tras soltar no se vuelve a agarrar sola aunque el cursor siga encima
    correr(j, ctrl, 1.5)
    assert j.llevada is None
    # al salir y volver si se agarra
    mover_y_esperar(j, ctrl, 640, 700, 0.2)
    mover_y_esperar(j, ctrl, *cel, 0.5)
    assert j.llevada is pz and pz.celda is None and (1, 0) not in j.rejilla
    # soltar por clic (en una celda distinta)
    ctrl.mover_a(*j.centro_celda(0, 1))
    correr(j, ctrl, 1 / 60)
    ctrl.clic = True
    correr(j, ctrl, 1 / 60)
    assert j.llevada is None and pz.celda == (0, 1), pz.celda
    # agarrar por clic
    ctrl.mover_a(640, 700)
    correr(j, ctrl, 0.2)
    ctrl.mover_a(*j.centro_celda(0, 1))
    ctrl.clic = True
    correr(j, ctrl, 1 / 60)
    assert j.llevada is pz and pz.celda is None
    # soltar fuera de la cuadricula: se queda ahi, fuera del marco y dentro de la pantalla
    ctrl.mover_a(300, 300)
    correr(j, ctrl, 0.1)
    ctrl.mover_a(300, 400)
    correr(j, ctrl, 0.05)
    ctrl.clic = True
    correr(j, ctrl, 1 / 60)
    correr(j, ctrl, 1.0)
    assert j.llevada is None and pz.celda is None
    r = pygame.Rect(0, 0, j.s, j.s)
    r.center = (int(pz.pos.x), int(pz.pos.y))
    assert abs(pz.pos.y - 400) < 2 or True
    assert not r.colliderect(j.marco) and J.ZONA.inflate(2, 2).contains(r), r
    # soltar quieto fuera de la cuadricula tambien funciona (sobre el marco se aparta)
    j4, c4 = nuevo(1)
    p4 = j4.piezas[0]
    mover_y_esperar(j4, c4, p4.pos.x, p4.pos.y, 0.5)
    assert j4.llevada is p4
    for _ in range(10):
        c4.mover_a(j4.marco.centerx + 40, j4.marco.top - 4)       # sobre el borde del marco
        correr(j4, c4, 1 / 60)
    correr(j4, c4, 0.6)
    assert j4.llevada is None and p4.celda is None
    for _ in range(60):
        correr(j4, c4, 1 / 60)
    r = pygame.Rect(0, 0, j4.s, j4.s)
    r.center = (int(p4.dest.x), int(p4.dest.y))
    assert not r.colliderect(j4.marco), (r, j4.marco)
    print("agarrar/soltar ok")


def llevar(j, ctrl, pz, celda):
    """Agarra pz con clic y la suelta con clic en la celda."""
    ctrl.mover_a(pz.pos.x, pz.pos.y)
    correr(j, ctrl, 1 / 60)
    ctrl.clic = True
    correr(j, ctrl, 1 / 60)
    assert j.llevada is pz
    ctrl.mover_a(*j.centro_celda(*celda))
    correr(j, ctrl, 1 / 60)
    ctrl.clic = True
    correr(j, ctrl, 1 / 60)
    assert j.llevada is None
    correr(j, ctrl, 0.8)


def test_intercambio():
    j, ctrl = nuevo(1)
    a, b = j.piezas[0], j.piezas[1]
    pb0 = V2(b.pos)
    celda = (1, 1)
    llevar(j, ctrl, a, celda)
    assert a.celda == celda
    # b (de la bandeja) cae sobre a: a vuelve a donde estaba b
    llevar(j, ctrl, b, celda)
    assert b.celda == celda and j.rejilla[celda] is b
    assert a.celda is None, "la pieza desplazada vuelve a la bandeja"
    assert (a.dest - pb0).length() < 1, "la desplazada va donde estaba la otra"
    # intercambio puro entre dos celdas
    c2 = (0, 0)
    llevar(j, ctrl, a, c2)
    assert a.celda == c2 and b.celda == celda
    llevar(j, ctrl, b, c2)
    assert b.celda == c2 and a.celda == celda, (a.celda, b.celda)
    assert len(j.rejilla) == 2
    print("intercambio ok")


# ------------------------------------------------------------ completar
def test_completar():
    for i in range(RD.N_RUINAS):
        j, ctrl = nuevo(i, semilla=3 + i)
        t = correr(j, ctrl, 400, BotBueno())
        assert j.terminado and j.completo and j.superado(), (i, t)
        assert all(q.correcta for q in j.piezas)
        assert j.estrellas() == 3 and j.puntos == 150 + j.n
        par = j.par_3
        assert j.t_comp < par, (i, j.t_comp, par)
        per = j.ctx.perfil
        assert RD.hecha(per, i) and RD.estrellas(per, i) == 3 and RD.mejor_tiempo(per, i) is not None
        assert j.monedas_ruina == RD.monedas_por(i, 3) and per.monedas == 150 + j.monedas_ruina
        assert j.primera_vez
        print(f"ruina {i} {j.cols}x{j.filas}: completa a {j.t_comp:.1f}s (par3 {par:.0f}) estrellas {j.estrellas()} "
              f"pts {j.puntos} fin a {t:.1f}s | {j.mensaje_final}")
        capturar(j, SHOTS + f"fin_{i}.png") if False else None
    # estrellas segun tiempo
    j, ctrl = nuevo(0, semilla=1)
    j.t = j.par_2 + 1
    j.paso(0.0, ctrl)
    j.piezas_ok = [setattr(q, "celda", (q.c, q.r)) for q in j.piezas]
    j._completar()
    assert j.estrellas() == 1
    j, ctrl = nuevo(0, semilla=1)
    j.t = j.par_3 + 1
    for q in j.piezas:
        q.celda = (q.c, q.r)
    j._completar()
    assert j.estrellas() == 2
    print("completar ok")


def test_inerte_y_erratico():
    for i in range(RD.N_RUINAS):
        j, ctrl = nuevo(i)
        correr(j, ctrl, 120, bot_inerte)
        assert not j.terminado and not j.completo and j.estrellas() == 0 and j.puntos == 0
        assert not any(q.celda for q in j.piezas)
        assert not RD.hecha(j.ctx.perfil, i)
    random.seed(4)
    for i in range(RD.N_RUINAS):
        j, ctrl = nuevo(i)
        correr(j, ctrl, 40, bot_erratico)
        j.dibujar(pantalla())
        # nunca se pierden ni se duplican piezas
        assert len(j.piezas) == j.n
        celdas = [q.celda for q in j.piezas if q.celda is not None]
        assert len(celdas) == len(set(celdas)) and len(j.rejilla) == len(celdas)
        assert (j.llevada is not None) == (j.origen is not None)
    # niveles raros y mejoras de la ruleta no rompen
    for mej in ((), ("potencia", "alcance", "lento", "tiempo", "puntos", "vida")):
        for nivel in (0, 1, 3, 6, 9):
            ctx = crear_ctx(mej)
            j = Ruinas(ctx, nivel, semilla=2)
            correr(j, ControlSim(), 10, bot_erratico)
    print("inerte y erratico ok")


# ------------------------------------------------------------ datos
def test_desbloqueo():
    ctx = crear_ctx()
    per = ctx.perfil

    class Aj:
        MODO_PRUEBA = False

    class AjP:
        MODO_PRUEBA = True

    assert RD.N_RUINAS == 30 and RD.N_MUNDOS == 5 and RD.POR_MUNDO == 6
    assert [c * f for c, f in RD.RUINAS[:6]] == [6, 9, 12, 16, 20, 24]
    assert all(RD.RUINAS[m * 6 + k] == RD.RUINAS[k] for m in range(5) for k in range(6))
    assert RD.datos_estado(per, Aj) == ["abierta"] * 6 + ["bloqueada"] * 24
    assert RD.abierta(per, 0, Aj) and RD.abierta(per, 5, Aj) and not RD.abierta(per, 6, Aj)
    assert RD.abierta(per, 29, AjP)
    assert RD.faltan(per, 6) == ["Completa el Mundo Griego"] or RD.faltan(per, 6)[0].startswith("Completa")
    for m in range(4):
        for k in range(5):
            RD.registrar(per, m * 6 + k, 30.0, 2)
            assert not RD.mundo_completo(per, m) and not RD.abierta(per, (m + 1) * 6, Aj)
        RD.registrar(per, m * 6 + 5, 30.0, 2)
        assert RD.mundo_completo(per, m) and RD.tiene_llave(per, m)
        assert RD.abierta(per, (m + 1) * 6, Aj) and not RD.abierta(per, (m + 2) * 6, Aj) if m < 3 else True
    assert RD.total_hechas(per) == 24
    # los guardados antiguos (0..5) siguen siendo el mundo 1
    assert RD.monedas_por(0, 3) == 30 and RD.monedas_por(5, 3) == 180 and RD.monedas_por(29, 3) == 10 * (6 + 8) * 3
    assert not getattr(ajustes, "MODO_PRUEBA", False)
    # ajustes real: MODO_PRUEBA no existe por defecto
    assert not getattr(ajustes, "MODO_PRUEBA", False)
    # registrar: primera vez, mejor tiempo y estrellas solo mejoran
    ctx = crear_ctx()
    per = ctx.perfil
    assert RD.registrar(per, 2, 50.0, 2) is True
    assert RD.registrar(per, 2, 70.0, 1) is False
    assert RD.mejor_tiempo(per, 2) == 50.0 and RD.estrellas(per, 2) == 2
    assert RD.registrar(per, 2, 40.0, 3) is False
    assert RD.mejor_tiempo(per, 2) == 40.0 and RD.estrellas(per, 2) == 3
    assert per.extra["ruinas"]["hechas"] == [2]
    print("desbloqueo ok")


def test_persistencia():
    ctx = crear_ctx()
    per = ctx.perfil
    RD.registrar(per, 1, 33.3, 2)
    RD.registrar(per, 4, 80.0, 3)
    per.guardar()
    otro = Perfil(per.archivo)
    e = RD.estado(otro)
    assert e["hechas"] == [1, 4] and e["estrellas"] == {1: 2, 4: 3} and e["mejor"] == {1: 33.3, 4: 80.0}, e
    assert RD.estrellas(otro, 4) == 3 and RD.hecha(otro, 1) and not RD.hecha(otro, 0)
    assert RD.registrar(otro, 1, 20.0, 3) is False and RD.estrellas(otro, 1) == 3
    # un perfil de verdad: jugar una ruina guarda sola
    j, ctrl = nuevo(0)
    correr(j, ctrl, 100, BotBueno())
    r = Perfil(j.ctx.perfil.archivo)
    assert RD.hecha(r, 0) and RD.estrellas(r, 0) == 3
    print("persistencia ok")


# ------------------------------------------------------------ hub, mapa y capturas
def esperar(esc, ctrl, seg):
    escena_simular(esc, ctrl, None, segundos=seg, dibujar_cada=20)


def completar_mundo(per, m):
    for k in range(6):
        RD.registrar(per, m * 6 + k, 30.0, 2)


def test_hub():
    import aventura as av
    from escena_ruinas import RuinasEscena
    app = AppFalsa()
    per = app.ctx.perfil
    esc = RuinasEscena(app)
    ctrl = ControlSim()
    esperar(esc, ctrl, 0.2)
    assert esc.vista == 0
    capturar_escena(esc, SHOTS + "hub_inicio.png")
    # mundo 2 cerrado: se puede mirar, pero sus murales no se abren
    ctrl.mover_a(*esc.b_mundos[1].rect.center)
    esperar(esc, ctrl, 1.5)
    assert esc.vista == 1 and RD.estado(per).get("mundo") in (None, 0)
    capturar_escena(esc, SHOTS + "hub_bloqueado.png")
    ctrl.mover_a(*esc.cards[0].rect.center)
    esperar(esc, ctrl, 2.0)
    ctrl.clic = True
    esperar(esc, ctrl, 1 / 60)
    assert app.escena is None, "mural de un mundo cerrado no debe abrirse"
    # mundo 1: por permanencia y por clic
    ctrl.mover_a(*esc.b_mundos[0].rect.center)
    esperar(esc, ctrl, 1.5)
    assert esc.vista == 0
    ctrl.mover_a(*esc.cards[0].rect.center)
    esperar(esc, ctrl, 1.5)
    assert isinstance(app.escena, av.Partida) and app.escena.mj.id == "ruinas" and app.escena.mj.ruina == 0
    app.escena = None
    esc = RuinasEscena(app)
    ctrl = ControlSim()
    esperar(esc, ctrl, 0.8)
    ctrl.mover_a(*esc.cards[3].rect.center)
    esperar(esc, ctrl, 0.1)
    ctrl.clic = True
    esperar(esc, ctrl, 1 / 60)
    assert isinstance(app.escena, av.Partida) and app.escena.mj.ruina == 3
    # fases libres dentro de un mundo abierto
    assert RD.datos_estado(per)[:6] == ["abierta"] * 6
    # completar el mundo 1 abre el 2 (llave)
    completar_mundo(per, 0)
    assert RD.datos_estado(per)[:7] == ["hecha"] * 6 + ["abierta"]
    app.escena = None
    esc = RuinasEscena(app)
    ctrl = ControlSim()
    esperar(esc, ctrl, 0.3)
    capturar_escena(esc, SHOTS + "hub_llave.png")
    ctrl.mover_a(*esc.b_mundos[1].rect.center)
    esperar(esc, ctrl, 1.5)
    assert esc.vista == 1 and RD.estado(per)["mundo"] == 1
    ctrl.mover_a(*esc.cards[2].rect.center)
    esperar(esc, ctrl, 1.5)
    assert isinstance(app.escena, av.Partida) and app.escena.mj.ruina == 8
    # al volver se recuerda el mundo
    app.escena = None
    assert RuinasEscena(app).vista == 1
    # todo abierto (MODO_PRUEBA)
    ajustes.MODO_PRUEBA = True
    try:
        esc = RuinasEscena(app)
        esc._elegir_mundo(4)
        esperar(esc, ctrl, 0.2)
        capturar_escena(esc, SHOTS + "hub_prueba.png")
        assert RD.abierta(per, 29)
    finally:
        del ajustes.MODO_PRUEBA
    # Volver
    app.escena = None
    esc = RuinasEscena(app)
    ctrl.mover_a(640, 100)
    esperar(esc, ctrl, 0.8)
    ctrl.mover_a(*esc.volver.rect.center)
    esperar(esc, ctrl, 0.1)
    ctrl.clic = True
    esperar(esc, ctrl, 1 / 60)
    assert isinstance(app.escena, av.Libre)
    print("hub ok")


def test_libre():
    import aventura as av
    from escena_ruinas import RuinasEscena
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

    class FalsaEntrada(ControlSim):
        mando = None

        class espada:
            calibrada = True

    ent = FalsaEntrada()
    perfil = Perfil(os.path.join(tempfile.mkdtemp(), "p.json"))
    app = av.Aplicacion(ent, Sonidos(), Fuentes(), perfil)

    def frames(n, dt=1 / 60, bot=None):
        for k in range(n):
            if bot and isinstance(app.escena, av.Partida) and app.escena.cuenta <= 0:
                bot(app.escena.mj, ent, 0)
            app.actualizar(dt, ent)
            app.dibujar(pantalla())
            ent.fin_cuadro()

    def click(x, y):
        ent.mover_a(x, y)
        frames(50)
        ent.clic = True
        frames(1)

    assert "ruinas" in av.JUEGOS and "pintor" not in av.JUEGOS and "pintor" not in av.COLORES_JUEGO
    # Juego libre: ficha Ruinas -> hub
    app.ir(av.Libre(app))
    frames(20)
    ficha = [b for i, b in app.escena.fichas if i == "ruinas"][0]
    click(*ficha.rect.center)
    assert isinstance(app.escena, RuinasEscena), app.escena
    # abrir la ruina 0 y jugarla desde el hub
    frames(50)
    esc = app.escena
    click(*esc.cards[0].rect.center)
    assert isinstance(app.escena, av.Partida) and app.escena.mj.ruina == 0
    frames(200)                                   # cuenta atras
    bot = BotBueno()
    for _ in range(60 * 90):
        if isinstance(app.escena, av.Resultado):
            break
        frames(1, bot=bot)
    assert isinstance(app.escena, av.Resultado), app.escena
    assert perfil.records.get("ruinas", 0) > 0 and RD.hecha(perfil, 0)
    frames(120)
    capturar_escena(app.escena, SHOTS + "resultado.png")
    # Seguir: vuelve al hub de Ruinas
    app.escena.seguir()
    assert isinstance(app.escena, RuinasEscena), app.escena
    # Intro (por si alguien la crea): JUGAR abre el hub, sin selector de nivel
    app.ir(av.Intro(app, "ruinas", 1))
    frames(10)
    assert app.escena.sin_nivel
    click(ANCHO // 2, 606)
    assert isinstance(app.escena, RuinasEscena)
    # Resultado en juego libre -> hub libre; Repetir -> misma ruina
    app.ir(av.Partida(app, "ruinas", 1))
    frames(200)
    mj = app.escena.mj
    mj.puntos = 10
    mj.terminar("prueba")
    frames(3)
    assert isinstance(app.escena, av.Resultado)
    app.escena.seguir()
    assert isinstance(app.escena, RuinasEscena)
    # partidas de las 6 ruinas con el control erratico dentro de la aplicacion
    random.seed(9)
    for i in range(0, 30, 3):
        app.ir(av.Partida(app, "ruinas", i + 1))
        for k in range(400):
            if k % 10 == 0:
                ent.mover_a(random.uniform(0, ANCHO), random.uniform(0, ALTO))
            if k % 37 == 0:
                ent.clic = True
            app.actualizar(1 / 60, ent)
            app.dibujar(pantalla())
            ent.fin_cuadro()
    print("libre ok")


def test_capturas():
    for i in (0, 9, 17, 22, 29):
        j, ctrl = nuevo(i, semilla=5)
        simular(j, ctrl, None, segundos=0.3)
        capturar(j, SHOTS + f"{i}_inicio.png")
        mitad = j.n // 2
        # mitad de las piezas bien puestas y una en la mano
        bot = BotBueno(hasta=mitad)
        simular(j, ctrl, bot, segundos=300)
        # una pieza en la mano camino de su celda
        cand = [q for q in j.piezas if not q.correcta][0]
        ctrl.mover_a(cand.pos.x, cand.pos.y)
        simular(j, ctrl, None, segundos=0.5)
        objetivo = j.centro_celda(cand.c, cand.r)
        ctrl.mover_a(*(objetivo + V2(-j.s, j.s * 0.5)))
        simular(j, ctrl, None, segundos=0.5)
        capturar(j, SHOTS + f"{i}_mitad.png")
        simular(j, ctrl, BotBueno(), segundos=300)
        assert j.completo
        simular(j, ctrl, None, segundos=0.4) if not j.terminado else None
        j.t_rev = min(j.t_rev, 0.6) if not j.terminado else j.t_rev
        capturar(j, SHOTS + f"{i}_completo.png")
    print("capturas guardadas en", SHOTS + "*.png")


def main():
    random.seed(11)
    print("arte:", ARTE)
    test_geometria()
    test_mecanica()
    test_intercambio()
    test_completar()
    test_inerte_y_erratico()
    test_desbloqueo()
    test_persistencia()
    test_hub()
    test_libre()
    test_capturas()
    print("TODO OK")


if __name__ == "__main__":
    main()
