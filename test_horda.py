import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Pruebas de Horda Elemental: reglas de habilidades, terreno, seleccion de elemento, movimiento con el puntero,
subida de nivel con tarjetas, jefe (patrones y victoria), muerte, bot completo, rendimiento y capturas
(shots/horda_*.png)."""

import math
import random
import time

import horda_datos as D
import horda_mapa as M
from ajustes import ANCHO, ALTO
from nucleo import ControlSim
from pruebas_util import crear_ctx, capturar
import j_horda as J
from j_horda import Horda

SHOTS = "shots/horda_"
CX, CY = ANCHO / 2, ALTO / 2


def _juego(seed=None):
    return Horda(crear_ctx(), 1, semilla=seed)


def _paso(j, ctrl, segundos, dt=1 / 60):
    n = int(segundos / dt)
    for _ in range(n):
        if j.terminado:
            break
        j.actualizar(dt, ctrl)
        ctrl.fin_cuadro()


def _bot(j, ctrl, t, tipo_idx=0):
    """Elige elemento, sube de nivel con la primera tarjeta valida y camina hacia el enemigo mas cercano."""
    if j.fase == "elegir":
        ctrl.mover_a(*j._rects_tipos()[tipo_idx].center)
        ctrl.clic = True
        return
    if j.fase == "subida":
        for i, c in enumerate(j.cartas):
            if c["ok"]:
                ctrl.mover_a(*j._rects_cartas()[i].center)
                ctrl.clic = True
                return
        return
    ctrl.mover_a(CX, CY)
    if not j.enemigos:
        return
    e = min(j.enemigos, key=lambda q: math.hypot(q["x"] - j.hx, q["y"] - j.hy))
    dx, dy = e["x"] - j.hx, e["y"] - j.hy
    d = max(1.0, math.hypot(dx, dy))
    if d < 150:                                        # demasiado cerca: se aleja (kiting)
        ctrl.mover_a(CX - dx / d * 240, CY - dy / d * 240)
    elif d > 300:                                      # lejos: se acerca hasta distancia de tiro
        ctrl.mover_a(CX + dx / d * 240, CY + dy / d * 240)


# ------------------------------------------------------------ reglas
def test_reglas():
    h = D.Habilidades("agua")
    assert h.puntos_disponibles(0) == 0
    assert D.nivel_de(19) == 0 and D.nivel_de(20) == 1 and D.nivel_de(1900) == 10
    ok = [t for t in h.opciones(random.Random(1))]
    assert [t["rama"] for t in ok] == ["basico", "intermedio", "ultimate"]
    assert ok[1]["ok"] is False and ok[2]["ok"] is False          # bloqueados al inicio
    # gastar los 10 puntos: 4 basico, 1+3 intermedio, 1+1 ultimate
    rng = random.Random(3)
    gastados = 0
    while not h.completo():
        for t in h.opciones(rng):
            if t["ok"] and t["id"] is not None:
                if h.aplicar(t):
                    gastados += 1
                    break
        else:
            raise AssertionError("ninguna tarjeta valida con puntos disponibles")
    assert gastados == 10, gastados
    assert h.n_basico() == 4 and h.inter_desbloqueado and len(h.inter) == 3
    assert h.ult_desbloqueado and h.ult is not None
    s = h.stats()
    assert s["inter_on"] and s["ult_on"] and s["pen"] >= 1
    assert D.puntos_partida(D.DERROTAS_JEFE, True) == D.DERROTAS_JEFE * 10 + 500
    print("  reglas OK")


def test_mapa():
    g = M.generar(seed=7)
    assert M.casilla(g, M.ANCHO_MUNDO / 2, M.ALTO_MUNDO / 2) not in M.BLOQUEADO
    assert M.casilla(g, -5, 10) == M.ARBOL                         # fuera del mapa = bloqueado
    agua = None
    for cy in range(M.FILAS):
        for cx in range(M.COLS):
            if g[cy][cx] == M.AGUA:
                agua = (cx * M.TAM + M.TAM / 2, cy * M.TAM + M.TAM / 2)
                break
        if agua:
            break
    assert agua is not None
    assert M.velocidad_en(g, *agua) == M.VEL_AGUA
    # el heroe no atraviesa arboles ni rocas
    for cy in range(M.FILAS):
        for cx in range(M.COLS):
            if g[cy][cx] in M.BLOQUEADO:
                assert M.choca(g, cx * M.TAM + M.TAM / 2, cy * M.TAM + M.TAM / 2, 14)
                break
        else:
            continue
        break
    rng = random.Random(2)
    x, y = M.libre_cerca(g, M.ANCHO_MUNDO / 2, M.ALTO_MUNDO / 2, 14, rng)
    assert not M.choca(g, x, y, 14)
    nx, ny = M.mover(g, x, y, 500, 0, 14)
    assert not M.choca(g, nx, ny, 14)
    print("  mapa OK")


def test_seleccion_y_movimiento():
    j = _juego(1)
    ctrl = ControlSim()
    assert j.fase == "elegir"
    ctrl.mover_a(*j._rects_tipos()[0].center)
    ctrl.clic = True
    j.actualizar(1 / 60, ctrl)
    assert j.fase == "jugar" and j.tipo == D.TIPOS[0]
    ctrl.fin_cuadro()
    # puntero a la derecha: el heroe avanza en X; a la izquierda, retrocede
    x0 = j.hx
    ctrl.mover_a(CX + 300, CY)
    _paso(j, ctrl, 1.0)
    assert j.hx > x0 + 100, (x0, j.hx)
    x1 = j.hx
    ctrl.mover_a(CX - 300, CY)
    _paso(j, ctrl, 1.0)
    assert j.hx < x1 - 100
    # zona muerta: el puntero cerca del centro no mueve
    ctrl.mover_a(CX + 20, CY)
    x2 = j.hx
    _paso(j, ctrl, 0.5)
    assert abs(j.hx - x2) < 1e-6
    print("  seleccion y movimiento OK")


def test_subida_de_nivel():
    j = _juego(2)
    ctrl = ControlSim()
    ctrl.mover_a(*j._rects_tipos()[1].center)
    ctrl.clic = True
    _paso(j, ctrl, 0.05)
    ctrl.fin_cuadro()
    assert j.tipo == "viento"
    j.derrotas = 20                                   # primer nivel de mejoras
    _paso(j, ctrl, 1 / 60)
    assert j.fase == "subida" and len(j.cartas) == 3, j.fase
    # clic en una carta bloqueada: no cambia nada y avisa
    bloqueada = next(i for i, c in enumerate(j.cartas) if not c["ok"]) if any(not c["ok"] for c in j.cartas) else None
    if bloqueada is not None:
        ctrl.mover_a(*j._rects_cartas()[bloqueada].center)
        ctrl.clic = True
        _paso(j, ctrl, 1 / 60)
        ctrl.fin_cuadro()
        assert j.fase == "subida" and j.hab.puntos_gastados == 0
    # clic en una valida: gasta el punto y vuelve a jugar
    i = next(i for i, c in enumerate(j.cartas) if c["ok"])
    ctrl.mover_a(*j._rects_cartas()[i].center)
    ctrl.clic = True
    _paso(j, ctrl, 1 / 60)
    ctrl.fin_cuadro()
    assert j.hab.puntos_gastados == 1 and j.fase == "jugar", (j.hab.puntos_gastados, j.fase)
    print("  subida de nivel OK")


def test_jefe_y_victoria():
    """Progresion normal (el bot elige mejoras) hasta el dragon. Probamos varias partidas por si cae."""
    gano = None
    usados = set()
    for semilla in range(3, 11):
        j = _juego(semilla)
        ctrl = ControlSim()
        t = 0.0
        while t < 2400 and not j.terminado:
            if j.boss is not None and j.boss["pat"]:
                usados.add(j.boss["pat"])
            _bot(j, ctrl, t)
            j.actualizar(1 / 60, ctrl)
            ctrl.fin_cuadro()
            t += 1 / 60
        if j.ganado is True:
            assert j.superado() and j.puntos >= D.PUNTOS_JEFE
            gano = (semilla, round(t))
            break
    assert gano is not None, "ninguna partida de prueba derroto al dragon"
    assert len(usados) >= 2, usados
    # victoria forzada: el jefe muere -> ganado True
    j = _juego(20)
    ctrl = ControlSim()
    j.tipo, j.hab = "agua", D.Habilidades("agua")
    j.st, j.fase = j.hab.stats(), "jugar"
    j.derrotas = D.DERROTAS_JEFE
    j.boss_visto = True
    j.boss = j._nuevo_enemigo("dragon", 3, j.hx + 200, j.hy, jefe=True)
    j.enemigos.append(j.boss)
    j.boss["vida"] = 0
    _paso(j, ctrl, 1 / 60)
    assert j.terminado and j.ganado is True and j.superado()
    print(f"  jefe OK: semilla/segundos {gano} derrotaron al dragon (patrones vistos: {sorted(usados)})")


def _listo(j, tipo="agua"):
    """Deja el juego ya en marcha (elemento elegido) sin pasar por la pantalla de seleccion."""
    j.tipo, j.hab = tipo, D.Habilidades(tipo)
    j.st, j.fase = j.hab.stats(), "jugar"


def test_hordas_y_vida():
    """Las criaturas llegan en hordas (muchas a la vez) y la vida depende del progreso."""
    assert all(D.vida_enemigo(0, random.Random(s)) == 1 for s in range(300))
    assert any(D.vida_enemigo(1000, random.Random(s)) > 1 for s in range(300))
    assert D.intervalo_ola(0) == 7.0 and D.intervalo_ola(2000) == 4.0
    assert D.tamano_ola(0) == 8 and D.tamano_ola(2000) == 40
    j = _juego(11)
    _listo(j)
    ctrl = ControlSim()
    j.enemigos = []
    j.ola_t = 0.0
    _paso(j, ctrl, 1 / 60)
    assert len(j.enemigos) == D.tamano_ola(0), len(j.enemigos)
    for e in j.enemigos:
        # nacen FUERA del mapa (nunca en el centro de la pantalla)
        assert not (0 <= e["x"] <= M.ANCHO_MUNDO and 0 <= e["y"] <= M.ALTO_MUNDO), (e["x"], e["y"])
    e = j._nuevo_enemigo("pulpo", 1, j.hx + 200, j.hy)
    e["vida"] = e["vmax"] = 3
    j.enemigos = [e]
    j._herir(e, 1)
    assert e["vida"] == 2                              # una criatura de 3 golpes no cae de uno solo
    print("  hordas y vida OK")


def test_pelea_del_tamagotchi():
    """Al terminar la pelea se guarda la vida de la mascota y se da la recompensa (como la batalla de antes)."""
    j = _juego(12)
    _listo(j)
    ctrl = ControlSim()
    j.vidas = 0
    _paso(j, ctrl, 1 / 60)
    assert j.terminado and j.final == "pierde" and j.ganado is False
    assert j.resultado["estado"] == "pierde" and j.hp_guardada is not None
    assert j.estrellas() == 0 and not j.superado()
    j2 = _juego(13)
    _listo(j2)
    j2.terminar("salida")
    assert j2.final == "escapa" and j2.terminado and j2.resultado["estado"] == "escapa"
    j3 = _juego(14)
    _listo(j3)
    j3.derrotas = D.DERROTAS_JEFE
    j3.boss_visto = True
    j3.boss = j3._nuevo_enemigo("dragon", 3, j3.hx + 200, j3.hy, jefe=True)
    j3.enemigos.append(j3.boss)
    j3.boss["vida"] = 0
    _paso(j3, ctrl, 1 / 60)
    assert j3.terminado and j3.final == "gana" and j3.ganado is True and j3.superado()
    print("  pelea del Tamagotchi OK")


def test_muerte():
    """Rodeado de enemigos que no mueren: el heroe pierde sus 5 corazones y la partida termina sin estrellas."""
    j = _juego(4)
    ctrl = ControlSim()
    j.tipo, j.hab = "tierra", D.Habilidades("tierra")
    j.st, j.fase = j.hab.stats(), "jugar"
    for k in range(8):
        a = k * math.pi / 4
        e = j._nuevo_enemigo("pulpo", 1, j.hx + math.cos(a) * 30, j.hy + math.sin(a) * 30)
        e["vida"] = e["vmax"] = 10 ** 6
        j.enemigos.append(e)
    _paso(j, ctrl, 60.0)
    assert j.terminado and j.ganado is False and j.estrellas() == 0 and not j.superado()
    assert j.vidas <= 0 and j.mensaje_final
    print(f"  muerte OK: cayo y termino con mensaje '{j.mensaje_final}'")


def test_bot_completo_y_rendimiento():
    j = _juego(5)
    ctrl = ControlSim()
    cuadros = 0
    vistos_subida = 0
    t = 0.0
    while t < 240 and not j.terminado:
        if j.fase == "subida":
            vistos_subida += 1
        _bot(j, ctrl, t, tipo_idx=5)
        j.actualizar(1 / 60, ctrl)
        ctrl.fin_cuadro()
        if cuadros % 30 == 0:
            j.dibujar(J.pantalla() if hasattr(J, "pantalla") else __import__("pruebas_util").pantalla())
        cuadros += 1
        t += 1 / 60
    print(f"  bot: {cuadros} cuadros, derrotas {j.derrotas}, puntos {j.puntos}, subidas vistas {vistos_subida}, "
          f"fin: {j.mensaje_final or 'en curso'}")
    assert j.derrotas > 5 and vistos_subida > 0
    # rendimiento (con dibujo cada cuadro)
    p = __import__("pruebas_util").pantalla()
    j2 = _juego(6)
    j2.tipo = "electrico"
    j2.hab = D.Habilidades("electrico")
    for q in ("basico", "dano", "pen", "tam"):
        j2.hab.basico.add(q)
    j2.hab.inter_desbloqueado = True
    j2.hab.inter.update(["dano_i", "carga", "efecto"])
    j2.hab.ult_desbloqueado = True
    j2.hab.ult = "frec"
    j2.st = j2.hab.stats()
    j2.derrotas = 600
    j2.boss_visto = True
    c2 = ControlSim()
    c2.mover_a(CX + 200, CY + 100)
    rng = random.Random(9)
    for k in range(40):                                # 40 criaturas vivas (no mueren: mide la carga real)
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(200, 650)
        x, y = M.libre_cerca(j2.g, j2.hx + math.cos(a) * d, j2.hy + math.sin(a) * d, 14, rng, radio=60)
        e = j2._nuevo_enemigo(J.ESPECIES_HORDA[k % len(J.ESPECIES_HORDA)], 2, x, y)
        e["vida"] = e["vmax"] = 10 ** 6
        j2.enemigos.append(e)
    ms = []
    for k in range(600):
        j2.ola_t = 99.0                             # sin nuevas criaturas durante la medicion
        a = time.perf_counter()
        j2.actualizar(1 / 60, c2)
        c2.fin_cuadro()
        if k % 2 == 0:
            j2.dibujar(p)
        ms.append((time.perf_counter() - a) * 1000)
        if j2.terminado:
            break
    medio = sum(ms) / len(ms)
    print(f"  rendimiento: {medio:.1f} ms por cuadro (media), max {max(ms):.1f} ms, enemigos {len(j2.enemigos)}")
    assert medio < 25, medio


def test_capturas():
    j = _juego(7)
    ctrl = ControlSim()
    capturar(j, SHOTS + "elegir.png")
    ctrl.mover_a(*j._rects_tipos()[0].center)
    ctrl.clic = True
    _paso(j, ctrl, 1 / 60)
    ctrl.fin_cuadro()
    # partida a media marcha: mejoras elegidas, criaturas alrededor (sin tarjetas abiertas)
    j.derrotas = 1000
    j.boss_visto = True
    j.hab.basico.update(["cadencia", "dano", "tam"])
    j.hab.inter_desbloqueado = True
    j.hab.inter.update(["carga", "dano_i"])
    j.hab.ult_desbloqueado = True
    j.hab.puntos_gastados = 7                          # 130 derrotas = nivel 8: 3 basico + 3 inter + 2 ultimate
    j.st = j.hab.stats()
    rng = random.Random(5)
    for k in range(14):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(160, 430)
        x, y = M.libre_cerca(j.g, j.hx + math.cos(a) * d, j.hy + math.sin(a) * d, 14, rng, radio=60)
        e = j._nuevo_enemigo(J.ESPECIES_HORDA[k % len(J.ESPECIES_HORDA)], 2, x, y)
        e["vida"] = e["vmax"] = 4
        if k % 5 == 0:
            e["est"]["paralizado"] = 2.0
        j.enemigos.append(e)
    j.proys.append(dict(tipo="agua", x=j.hx + 90, y=j.hy - 40, ang=0.0, vx=600, vy=0, r=12, dano=2, pen=1,
                        ttl=1, efecto=None, dur=2.0, inter=False, tocados=set()))
    j.cd_ult = 0.2
    _paso(j, ctrl, 0.4)
    ctrl.fin_cuadro()
    capturar(j, SHOTS + "jugar.png")
    j.derrotas = 20
    j.cartas = j.hab.opciones(random.Random(4))
    j.fase = "subida"
    capturar(j, SHOTS + "subida.png")
    b = _juego(8)
    b.tipo = "fuego"
    b.hab = D.Habilidades("fuego")
    b.st = b.hab.stats()
    b.fase = "jugar"
    b.boss_visto = True
    b.derrotas = D.DERROTAS_JEFE
    b.boss = b._nuevo_enemigo("dragon", 3, b.hx + 250, b.hy - 120, jefe=True)
    b.enemigos.append(b.boss)
    b.boss["pat"], b.boss["tel"], b.boss["dash_dir"] = "embestida", 0.5, (1.0, 0.0)
    b.zonas.append(dict(tipo="fuego", x=b.hx - 120, y=b.hy + 60, r=150, fase="aviso", t=0.4, u=0.5,
                        dano=2, efecto="quemado", dur=2.0))
    capturar(b, SHOTS + "jefe.png")
    print("  capturas en shots/horda_*.png")


def main():
    print("Horda Elemental")
    test_reglas()
    test_mapa()
    test_seleccion_y_movimiento()
    test_subida_de_nivel()
    test_jefe_y_victoria()
    test_hordas_y_vida()
    test_pelea_del_tamagotchi()
    test_muerte()
    test_bot_completo_y_rendimiento()
    test_capturas()
    print("TODO OK")


if __name__ == "__main__":
    main()
