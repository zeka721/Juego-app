import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Pruebas de Cocina v2 (libro de 30 recetas, ficha, habilidades, pasos con cuencos, XP, materiales, mejoras).

Un bot de juego completo navega el libro y juega cada paso con el bot "bueno" de las pruebas de pasos.
Capturas en /tmp/shots/cocina_*.png."""

import os
import sys
import time

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pruebas_util import crear_ctx, pantalla, capturar
from nucleo import ControlSim
import catalogo
import cocina_datos as cd
import j_cocina as jc
from j_cocina import Cocina
import test_pasos_cortes as tc
import test_pasos_masas as tm
import test_pasos_fuego as tf

SH = "/tmp/shots/cocina_"
DT = 1 / 60
CORTES = ("cortar", "pelar", "rayar", "extraer", "exprimir")
MASAS = ("aplastar", "presionar", "moldear", "enrollar", "untar", "espolvorear", "decorar")


# ----------------------------------------------------------------------------- utilidades
def subir_hab(perfil, nivel):
    for h in cd.ORDEN_HAB:
        perfil.habilidades[h] = cd.NIVEL_XP[nivel - 1]


def dar_todo(perfil, n=5):
    for r in cd.RECETAS:
        for m in r["mats"]:
            perfil.dar(m, n)


def ctx_completo(mejoras=()):
    ctx = crear_ctx(mejoras)
    subir_hab(ctx.perfil, 5)
    dar_todo(ctx.perfil, 5)
    return ctx


def bot_de_paso(cur):
    """Devuelve f(ctrl, t) que juega bien (solo cursor) el paso `cur`."""
    h = cur.habilidad
    if h in CORTES:
        return tc.bot_para(cur)
    if h in MASAS:
        return lambda ctrl, t: tm.bot_bueno(cur, ctrl, t)
    b = tf.BOTS[h]()
    return lambda ctrl, t: b(cur, ctrl, t)


class Bot:
    """Navega el libro, abre la ficha, cocina y juega los pasos. solo_cursor: nunca clic/golpe (dwell)."""

    def __init__(self, objetivo=None, solo_cursor=False, inerte=False):
        self.objetivo = objetivo
        self.solo_cursor = solo_cursor
        self.inerte = inerte
        self.cur = None
        self.f = None
        self.vio_habilidades = False

    def _ir(self, ctrl, boton):
        r = getattr(boton, "rect", boton)
        ctrl.mover_a(r.centerx, r.centery, cortando=False)
        if not self.solo_cursor:
            ctrl.clic = True

    def __call__(self, j, ctrl, t):
        if j.fase == "libro":
            self._libro(j, ctrl)
        elif j.fase == "paso":
            self._paso(j, ctrl)

    def _libro(self, j, ctrl):
        if j.giro:
            return
        if j.vista == "ficha":
            self._ir(ctrl, j.b_cocinar if j.b_cocinar.activo else j.b_volver)
            return
        if j.vista == "habilidades":
            self._ir(ctrl, j.b_cerrar)
            return
        obj = self.objetivo or j.recom
        idx = [r["id"] for r in cd.RECETAS].index(obj)
        d = idx // jc.POR_DOBLE
        if d > j.doble:
            self._ir(ctrl, j.b_sig)
        elif d < j.doble:
            self._ir(ctrl, j.b_ant)
        else:
            self._ir(ctrl, j.cartas[idx % jc.POR_DOBLE])

    def _paso(self, j, ctrl):
        if self.inerte or j.espera > 0:
            return
        if j.cur is not self.cur:
            self.cur = j.cur
            self.f = bot_de_paso(j.cur)
            ctrl.centrar()
        if not j.cur.terminado:
            self.f(ctrl, j.cur.t)


def jugar(j, bot, max_seg=1500.0, dibujar_cada=120, capturas=None):
    """Corre el juego hasta que termina. capturas: lista de (condicion(j), ruta)."""
    p = pantalla()
    ctrl = ControlSim()
    ctrl.centrar()
    t = 0.0
    n = 0
    capturas = list(capturas or [])
    while not j.terminado and t < max_seg:
        bot(j, ctrl, t)
        j.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        for c in list(capturas):
            if c[0](j):
                j.dibujar(p)
                os.makedirs(os.path.dirname(c[1]), exist_ok=True)
                pygame.image.save(p, c[1])
                capturas.remove(c)
        if n % dibujar_cada == 0:
            j.dibujar(p)
        t += DT
        n += 1
    assert j.terminado, "la cocina no termino en %d s (fase %s, paso %d)" % (max_seg, j.fase, j.i)
    return t


def entregar(ctx, j):
    """Lo que hace aventura.Resultado con el botin."""
    for item, n in j.botin.items():
        ctx.perfil.dar(item, n)


def suma_xp(perfil):
    return sum(perfil.habilidades.values())


# ----------------------------------------------------------------------------- pruebas
def test_datos():
    assert cd.validar() == [], cd.validar()
    assert Cocina.NIVEL_MAX == 30
    assert Cocina.duracion is None
    assert Cocina.etiquetas_nivel[1] and Cocina.etiquetas_nivel[30]
    assert len(cd.RECETAS) == 30
    print("datos ok")


def test_perfil_nuevo():
    ctx = crear_ctx()
    j = Cocina(ctx, nivel=30)
    # perfil nuevo: solo se puede cocinar una basica, aunque el nivel de juego sea 30
    rec = cd.POR_ID[j.recom]
    assert rec["basica"] and cd.jugable(ctx.perfil, rec), rec["id"]
    assert j.fase == "libro" and j.vista == "libro"
    assert len(j.metas) == 3
    # abrir ficha de una receta bloqueada: no se puede cocinar
    dura = cd.RECETAS[-1]
    j.abrir_ficha(dura["id"])
    assert j.vista == "ficha" and not j.b_cocinar.activo
    assert j._empezar(dura) is False and j.fase == "libro"
    assert cd.motivo_bloqueo(ctx.perfil, dura)
    # receta con materiales que faltan
    r3 = cd.POR_NIVEL[3]
    assert not cd.jugable(ctx.perfil, r3) and j._empezar(r3) is False
    p = pantalla()
    j.dibujar(p)
    # navega el libro entero (todas las hojas y fichas dibujan)
    for d in range(jc.n_dobles()):
        j.doble = d
        j._cache_hojas = {}
        j._colocar_cartas()
        j.vista = "libro"
        j.dibujar(p)
    for r in cd.RECETAS:
        j.abrir_ficha(r["id"])
        j.dibujar(p)
    j.abrir_habilidades()
    j.dibujar(p)
    print("perfil nuevo ok")


def test_migracion():
    ctx = crear_ctx()
    ctx.perfil.habilidades = {"picar": 30, "mezclar": 80, "sazonar": 10}
    j = Cocina(ctx, nivel=1)
    h = ctx.perfil.habilidades
    assert "picar" not in h and "mezclar" not in h and "sazonar" not in h, h
    assert h["cortar"] == 30 and h["girar"] == 80 and h["espolvorear"] == 10, h
    assert cd.nivel_habilidad(h["girar"]) == 3
    j.abrir_habilidades()
    j.dibujar(pantalla())
    print("migracion ok")


def test_receta_nivel(nivel, capturas=None):
    ctx = ctx_completo()
    perfil = ctx.perfil
    j = Cocina(ctx, nivel=nivel)
    r = cd.POR_NIVEL[nivel]
    assert j.recom == r["id"], (j.recom, r["id"])
    mats0 = {m: perfil.cantidad(m) for m in r["mats"]}
    xp0 = suma_xp(perfil)
    t = jugar(j, Bot(), capturas=capturas)
    assert j.fase == "entrega"
    assert len(j.calid) == len(r["pasos"]), (len(j.calid), len(r["pasos"]))
    assert j.estrellas() >= 2, (r["id"], j.puntos, j.metas)
    assert min(j.calid) >= 0.25 and sum(j.calid) / len(j.calid) > 0.7
    assert 0 < j.puntos <= cd.puntos_maximos(r), (j.puntos, cd.puntos_maximos(r))
    assert suma_xp(perfil) > xp0
    pid = cd.plato_id(r)
    assert j.botin.get(pid, 0) >= 1, j.botin
    entregar(ctx, j)
    assert perfil.cantidad(pid) >= 1
    assert perfil.recetas_hechas.get(r["id"]) == 1
    if not r["basica"]:
        for m, n in r["mats"].items():
            assert perfil.cantidad(m) == mats0[m] - n, (m, perfil.cantidad(m), mats0[m], n)
    assert perfil.extra["cocina"].get("pendiente") == {}
    # cuencos: todos los usados tienen o tuvieron contenido
    assert set(j.letras) == {s["tazon"] for s in r["pasos"] if s.get("tazon")}
    print("receta nivel %2d %-20s pasos=%2d puntos=%3d/%3d estrellas=%d  %.0f s" % (
        nivel, r["id"], len(r["pasos"]), j.puntos, cd.puntos_maximos(r), j.estrellas(), t))
    return j


def test_barrido_30():
    t0 = time.time()
    for r in cd.RECETAS:
        ctx = ctx_completo()
        perfil = ctx.perfil
        subir_hab(perfil, 4)                  # basta el nivel requerido (4 en el nivel 25+)
        j = Cocina(ctx, nivel=r["nivel"])
        assert j.recom == r["id"], (j.recom, r["id"])
        xp0 = suma_xp(perfil)
        mats0 = {m: perfil.cantidad(m) for m in r["mats"]}
        jugar(j, Bot(objetivo=r["id"]))
        assert j.estrellas() >= 1 and j.superado(), r["id"]
        assert suma_xp(perfil) > xp0, r["id"]
        if not r["basica"]:
            for m, n in r["mats"].items():
                assert perfil.cantidad(m) == mats0[m] - n, (r["id"], m)
        entregar(ctx, j)
        assert perfil.cantidad(cd.plato_id(r)) >= 1, r["id"]
    print("barrido de las 30 recetas ok (%.0f s)" % (time.time() - t0))


def test_solo_cursor():
    """Nada exige clic: libro, ficha y pasos con solo mover el cursor (dwell)."""
    ctx = ctx_completo()
    j = Cocina(ctx, nivel=5)
    jugar(j, Bot(solo_cursor=True))
    assert j.estrellas() >= 1
    print("solo cursor ok")


def test_inerte_y_devolucion():
    """Un bot que no hace nada termina, sin estrellas, y los materiales vuelven."""
    ctx = ctx_completo()
    perfil = ctx.perfil
    r = cd.POR_NIVEL[3]
    inv0 = dict(perfil.inventario)
    j = Cocina(ctx, nivel=3)
    t = jugar(j, Bot(inerte=True), max_seg=1200)
    assert j.fase == "entrega" and j.estrellas() == 0 and not j.superado()
    assert not j.botin
    assert perfil.inventario == inv0, "los materiales deben volver sin estrellas"
    assert j.resumen["devueltos"]
    assert all(q >= 0.25 for q in j.calid)
    print("inerte ok (%.0f s simulados)" % t)


def test_cancelar():
    ctx = ctx_completo()
    perfil = ctx.perfil
    r = cd.POR_NIVEL[6]
    inv0 = dict(perfil.inventario)
    j = Cocina(ctx, nivel=6)
    bot = Bot()
    ctrl = ControlSim()
    ctrl.centrar()
    for _ in range(60 * 200):
        bot(j, ctrl, 0)
        j.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        if j.fase == "paso" and j.i >= 2:
            break
    assert j.fase == "paso" and j.i >= 2
    assert perfil.cantidad("papa") == inv0["papa"] - r["mats"]["papa"]
    assert perfil.extra["cocina"]["pendiente"]
    j.cancelar()
    assert j.terminado
    assert perfil.inventario == inv0
    # cerrar el juego sin cancelar: el siguiente Cocina devuelve lo pendiente
    j2 = Cocina(ctx, nivel=6)
    jugar_hasta_cocinar(j2)
    perdido = dict(perfil.inventario)
    j3 = Cocina(ctx, nivel=6)                     # se abre de nuevo sin cancelar el anterior
    assert perfil.cantidad("papa") == inv0["papa"], (perdido, inv0)
    print("cancelar ok")


def jugar_hasta_cocinar(j):
    bot = Bot()
    ctrl = ControlSim()
    ctrl.centrar()
    for _ in range(60 * 60):
        bot(j, ctrl, 0)
        j.actualizar(DT, ctrl)
        ctrl.fin_cuadro()
        if j.fase == "paso":
            return
    raise AssertionError("no empezo a cocinar")


def test_mejoras():
    ctx = ctx_completo(("potencia", "alcance", "lento", "tiempo", "puntos", "vida"))
    j = Cocina(ctx, nivel=5)
    m = j._mods()
    assert m.pot == 1.5 and m.alc == 1.3 and m.lento == 0.8 and abs(m.tiempo - 1.25 * 1.3) < 1e-9, vars(m)
    jugar(j, Bot())
    assert j.estrellas() >= 2
    r = cd.POR_NIVEL[5]
    assert j.puntos > cd.puntos_maximos(r), "puntos x2"          # con "puntos" se puede pasar el maximo normal
    assert j.cur.mods is j.mods and j.cur.t_max > 0
    print("mejoras ok")


def test_subida_de_nivel():
    ctx = crear_ctx()
    ctx.perfil.habilidades = {"cortar": 24, "exprimir": 24, "verter": 24, "servir": 24}   # a 1 XP del nivel 2
    j = Cocina(ctx, nivel=1)
    jugar(j, Bot())
    assert j.subidas, "debio subir de nivel alguna habilidad"
    assert j.resumen["subidas"] == j.subidas
    j.dibujar(pantalla())
    print("subida de nivel ok", j.subidas)


def test_capturas():
    """Libro, ficha, habilidades, un paso con cuencos y resultado."""
    os.makedirs("/tmp/shots", exist_ok=True)
    p = pantalla()
    ctx = ctx_completo()
    ctx.perfil.habilidades.update({"cortar": 90, "pelar": 30, "batir": 200, "hornear": 10})
    j = Cocina(ctx, nivel=10)
    j.dibujar(p)
    pygame.image.save(p, SH + "libro.png")
    # libro con perfil nuevo (bloqueos y faltantes)
    j0 = Cocina(crear_ctx(), nivel=1)
    j0.doble = 1
    j0._cache_hojas = {}
    j0._colocar_cartas()
    j0.dibujar(p)
    pygame.image.save(p, SH + "libro_nuevo.png")
    j.abrir_ficha(cd.POR_NIVEL[20]["id"])
    j.dibujar(p)
    pygame.image.save(p, SH + "ficha20.png")
    j.abrir_ficha(cd.POR_NIVEL[3]["id"])
    j.dibujar(p)
    pygame.image.save(p, SH + "ficha3.png")
    j.abrir_ficha(cd.POR_NIVEL[30]["id"])
    j.dibujar(p)
    pygame.image.save(p, SH + "ficha30.png")
    j.abrir_habilidades()
    j.dibujar(p)
    pygame.image.save(p, SH + "habilidades.png")
    # un paso con cuencos (galletas) y su resultado
    ctx2 = ctx_completo()
    j2 = Cocina(ctx2, nivel=10)
    caps = [(lambda g: g.fase == "paso" and g.i == 4 and g.cur.t > 1.5, SH + "paso_cuencos.png"),
            (lambda g: g.fase == "paso" and g.i == 5 and g.cerrado and g.cur.t_cierre > 0.3, SH + "paso_resultado.png"),
            (lambda g: g.fase == "entrega" and g.t_ent > 2.0, SH + "resultado.png")]
    jugar(j2, Bot(), capturas=caps)
    # entrega con subida de nivel
    ctx3 = crear_ctx()
    ctx3.perfil.habilidades = {"cortar": 24, "exprimir": 24, "verter": 24, "servir": 24}
    j3 = Cocina(ctx3, nivel=1)
    jugar(j3, Bot(), capturas=[(lambda g: g.fase == "entrega" and g.t_ent > 2.0, SH + "resultado_sube.png")])
    # un paso largo (receta 30) a mitad con muchos cuencos
    ctx4 = ctx_completo()
    j4 = Cocina(ctx4, nivel=30)
    jugar(j4, Bot(), capturas=[(lambda g: g.fase == "paso" and g.i == 14 and g.cur.t > 2.0, SH + "paso30.png")])
    for n in ("libro", "ficha20", "habilidades", "paso_cuencos", "paso_resultado", "resultado", "paso30"):
        assert os.path.exists(SH + n + ".png"), n
    print("capturas ok")


def test_resultado():
    """El Resultado de aventura.py recibe la clase igual que los demas minijuegos."""
    import aventura as av
    assert av.JUEGOS["cocina"] is Cocina
    ctx = ctx_completo()
    j = Cocina(ctx, nivel=1)
    jugar(j, Bot())

    class App:
        pass
    app = App()
    app.ctx = ctx
    app.entrada = ControlSim()
    res = av.Resultado(app, j)
    assert ctx.perfil.cantidad(cd.plato_id(cd.POR_NIVEL[1])) >= 1
    assert res.superado and res.estrellas >= 1
    res.dibujar(pantalla())
    print("resultado ok")


def main():
    pantalla()
    test_datos()
    test_perfil_nuevo()
    test_migracion()
    for n in (1, 5, 10, 20, 30):
        test_receta_nivel(n)
    test_solo_cursor()
    test_inerte_y_devolucion()
    test_cancelar()
    test_mejoras()
    test_subida_de_nivel()
    test_barrido_30()
    test_capturas()
    test_resultado()
    print("TODO OK")


if __name__ == "__main__":
    main()
