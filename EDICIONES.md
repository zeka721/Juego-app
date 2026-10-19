# Ediciones a mano (3 archivos existentes)

## 1) arte_ruinas.py

(a) Al inicio, justo despues de los imports (`import pygame` / bloque numpy), pega:

    import arte_mitos

    N_MUNDOS = 5
    POR_MUNDO = 6
    N_RUINAS = N_MUNDOS * POR_MUNDO
    NOMBRES = list(arte_mitos.NOMBRES)
    _VARIANTE = [1, 5, 0, 4, 2]

    def _var(i):
        return _VARIANTE[(i // POR_MUNDO) % N_MUNDOS]

y borra las lineas antiguas `N_RUINAS = 6` y `NOMBRES = [...]`.

(b) Reemplaza la funcion `mural` completa por:

    def mural(i, w, h):
        key = (i, w, h)
        m = _cache_mural.get(key)
        if m is not None:
            return m
        i %= N_RUINAS
        v = _var(i)
        pal = _pal(v)
        sf = _arenisca(w, h, v, seed=1 + i)
        S = min(w, h)
        bw = max(6, int(S * .065))
        Lr = _L(sf, w / 2, h / 2, S / 2.0, pal)
        _relleno(Lr, w, h, v, bw)
        U = max(10.0, S / 2 - bw * .9)
        L = _L(sf, w / 2, h / 2, U, pal, max(0.3, S / 2 / 180.0))
        arte_mitos.MOTIVOS[i](L)
        _borde_mural(sf, w, h, v, bw, pal)
        _viñeta(sf, 60)
        _cache_mural[key] = sf
        return sf

(c) En `dibujar_fondo`, `dibujar_columnas` y `dibujar_marco`, la linea `i = i % N_RUINAS` pasa a:

    i = _var(i % N_RUINAS)

(d) En `_icono_base`, la linea `piedra = _arenisca(W, H, i, seed=3)` pasa a:

    piedra = _arenisca(W, H, _var(i), seed=3)

## 2) j_ruinas.py

(a) En `_completar`, la linea de monedas pasa a:

    self.monedas_ruina = RD.monedas_por(self.ruina, est)

(b) En el HUD, justo despues de `escribir(p, self.f.grande, nombre, ANCHO / 2, 38, ...)`, agrega:

    escribir(p, self.f.chica, f"{RD.MUNDOS[RD.mundo_de(self.ruina)]['nombre']}  ·  mural {RD.fase_de(self.ruina) + 1} de {RD.POR_MUNDO}",
             ANCHO / 2, 74, (230, 210, 160), contorno=(30, 20, 10))

## 3) Archivos nuevos o reemplazados completos
arte_mitos_base.py, arte_mitos.py, arte_mitos_1.py ... arte_mitos_5.py (nuevos),
ruinas_datos.py y escena_ruinas.py (reemplazan a los actuales),
test_ruinas.py (reemplaza pruebas/test_ruinas.py).
En pruebas/test_arte_ruinas.py cambia 6 por 30 (N_RUINAS, NOMBRES, range y el set de bytes).
