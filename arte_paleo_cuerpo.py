"""Motor de animales "de columna" (marinos, peces y voladores): un cuerpo que sigue una curva (la columna) con
perfil de grosor, cabeza, aletas/alas poligonales animadas y esqueleto por partes.

Spec de un animal (dict):
  color, acento (color de aletas/alas), spine (puntos cabeza -> cola), perfil [(u, radio)], n (puntos de la curva),
  onda=(amplitud, frecuencia, fase por u, u0), cuello=(u_fin, amplitud)  movimiento de ondulacion y de cuello,
  cabeza=dict(tipo, z, ang, u) con HEADS[tipo] como en arte_paleo_tierra,
  aletas = lista de dict(u, lado "c"/"l", pos "abajo"/"arriba"/"fin", pts, ang, amp, fase, f, col, z, parte, nombre),
  vientre (factor), costillas=(u0, u1, n, prof), col_esq=(u0, u1), cola_esq=(u0, u1), extras=[...].
Marco de una aleta: a = hacia la cabeza, b = hacia afuera del cuerpo. El angulo gira desde +b hacia atras.
"""

import math

import pygame

import arte_paleo_comun as C
import arte_paleo_tierra as T
from arte_paleo_comun import (aclarar, oscurecer, spline, largo, en, rot, cadena, Pincel, HUESO, SOMBRA, OSCURO, W,
                              SIL_COLOR, HUESO_CLARO, HUESO_MEDIO)

FV = 0.92
CAJA = (620, 460)
SP = {}
_geo = {}


def registrar(ident, spec):
    SP[ident] = spec
    spec.setdefault("n", 80)
    spec.setdefault("onda", (8, 1, 5.0, 0.0))
    spec.setdefault("aletas", [])
    spec.setdefault("extras", [])
    spec.setdefault("acento", spec["color"])
    spec.setdefault("cuello", (0.0, 0.0))
    spec.setdefault("cabeza", dict(tipo=None, z=1.0, ang=0.0, u=0.0))
    spec["cabeza"].setdefault("u", 0.0)
    spec["cabeza"].setdefault("ang", 0.0)
    C.registrar_esqueleto(ident, _partes(ident), spec.get("caja_esq", (560, 400)))
    return spec


def _resamplear(pts, n):
    cad = spline(pts, 8)
    total = largo(cad)
    # tabla de longitudes acumuladas para no recalcular
    acum = [0.0]
    for i in range(1, len(cad)):
        acum.append(acum[-1] + math.dist(cad[i - 1], cad[i]))
    out = []
    j = 0
    for k in range(n):
        meta = total * k / (n - 1)
        while j < len(cad) - 2 and acum[j + 1] < meta:
            j += 1
        d = acum[j + 1] - acum[j] or 1.0
        f = max(0.0, min(1.0, (meta - acum[j]) / d))
        out.append((cad[j][0] + (cad[j + 1][0] - cad[j][0]) * f, cad[j][1] + (cad[j + 1][1] - cad[j][1]) * f))
    return out


def _radio(sp, u):
    pf = sp["perfil"]
    if u <= pf[0][0]:
        return pf[0][1]
    for i in range(1, len(pf)):
        if u <= pf[i][0]:
            u0, r0 = pf[i - 1]
            u1, r1 = pf[i]
            f = (u - u0) / ((u1 - u0) or 1.0)
            f = 0.5 - 0.5 * math.cos(math.pi * f)
            return r0 + (r1 - r0) * f
    return pf[-1][1]


def geo(ident):
    if ident not in _geo:
        sp = SP[ident]
        n = sp["n"]
        P = _resamplear(sp["spine"], n)
        us = [i / (n - 1) for i in range(n)]
        rs = [_radio(sp, u) for u in us]
        _geo[ident] = (P, us, rs)
    return _geo[ident]


def _sentido(P, i, k=2):
    a = P[max(0, i - k)]
    b = P[min(len(P) - 1, i + k)]
    dx, dy = a[0] - b[0], a[1] - b[1]                 # hacia la cabeza
    m = math.hypot(dx, dy) or 1.0
    return dx / m, dy / m


def _pose(sp, ident, t):
    P, us, rs = geo(ident)
    A, f, k, u0 = sp["onda"]
    uc, B = sp["cuello"]
    Q = []
    for i, (x, y) in enumerate(P):
        u = us[i]
        dy = A * max(0.0, u - u0) ** 1.3 * math.sin(W * t * f - k * u)
        dx = 0.0
        if uc > 0 and u < uc:
            w = (1 - u / uc) ** 2
            dx = B * w * math.sin(W * t)
            dy += B * 0.7 * w * math.sin(W * t * 2 + 1.0)
        Q.append((x + dx, y + dy + 1.2 * math.sin(W * t * 2)))
    return Q


def _col(sp, sil):
    c = sp["color"]
    if sil:
        return dict(b=SIL_COLOR, c=SIL_COLOR, m=SIL_COLOR, o=SIL_COLOR, r=SIL_COLOR, n=SIL_COLOR, a=SIL_COLOR, k=SIL_COLOR, x=SIL_COLOR)
    m = sp.get("marfil", (250, 244, 222))
    return dict(b=c, c=aclarar(c, sp.get("claro", 0.42)), m=m, o=oscurecer(c, 0.3), r=(255, 160, 160),
                n=oscurecer(m, 0.25), a=sp["acento"], k=(120, 44, 60), x=sp.get("cresta", sp["acento"]))


def _aleta_pts(al, th):
    ca, sa = math.cos(th), math.sin(th)
    return [(a * ca - b * sa, a * sa + b * ca) for a, b in al["pts"]]


def _colocar_aleta(sp, ident, al, Q, t, lejos=False):
    P, us, rs = geo(ident)
    n = len(Q)
    i = int(round(al["u"] * (n - 1)))
    i = max(0, min(n - 1, i))
    hd = _sentido(Q, i)
    down = (-hd[1], hd[0])
    pos = al.get("pos", "abajo")
    sg = 1.0 if pos == "abajo" else -1.0
    nrm = (down[0] * sg, down[1] * sg)
    off = al.get("off", 0.85)
    r = rs[i]
    ox = Q[i][0] + nrm[0] * r * off
    oy = Q[i][1] + nrm[1] * r * off
    if pos == "fin":
        hd = _sentido(Q, n - 1, 3)
        down = (-hd[1], hd[0])
        nrm = (-down[0], -down[1])
        ox, oy = Q[-1]
    fase = al.get("fase", 0.0) + (1.2 if lejos else 0.0)
    th = al.get("ang", 0.0) + al.get("amp", 0.0) * math.sin(W * al.get("f", 1) * t + fase)
    loc = _aleta_pts(al, th)
    sc = al.get("esc", 1.0)
    pts = [(ox + (a * hd[0] + b * nrm[0]) * sc + (6 if lejos else 0), oy + (a * hd[1] + b * nrm[1]) * sc - (3 if lejos else 0))
           for a, b in loc]
    return pts, (ox, oy), hd, nrm


def _pintar(p, ident, x, y, escala, t, sil):
    sp = SP[ident]
    s = escala * FV
    pin = Pincel(p, x, y, s, sil)
    col = _col(sp, sil)
    Q = _pose(sp, ident, t)
    P, us, rs = geo(ident)
    n = len(Q)
    base = col["b"]
    aletas = sp["aletas"]

    def dibujar_aletas(z, lejos):
        for al in aletas:
            if al.get("z", 1) != z or (al.get("lado", "c") == "l") != lejos:
                continue
            pts, o, hd, nrm = _colocar_aleta(sp, ident, al, Q, t, lejos)
            c = col["o"] if lejos and not sil else col[al.get("col", "b")]
            if lejos and al.get("col", "b") == "a" and not sil:
                c = oscurecer(sp["acento"], 0.25)
            pin.grupo([("p", pts)], c, 3.0)
            if not sil and al.get("detalle"):
                th = al.get("ang", 0.0) + al.get("amp", 0.0) * math.sin(W * al.get("f", 1) * t + al.get("fase", 0.0) + (1.2 if lejos else 0.0))
                dc = oscurecer(sp["acento"] if al.get("col") == "a" else sp["color"], 0.38)
                if lejos:
                    dc = oscurecer(dc, 0.15)
                sc = al.get("esc", 1.0)
                for q, gr in al["detalle"]:
                    L = []
                    for a, b in q:
                        a2, b2 = _giro((a, b), th)
                        L.append((o[0] + (a2 * hd[0] + b2 * nrm[0]) * sc + (6 if lejos else 0),
                                  o[1] + (a2 * hd[1] + b2 * nrm[1]) * sc - (3 if lejos else 0)))
                    pin.linea(L, dc, gr)

    # ---- detras del cuerpo
    dibujar_aletas(0, True)
    dibujar_aletas(0, False)
    dibujar_aletas(1, True)
    # ---- cuerpo
    ic = int(sp.get("u_cuerpo", 0.0) * (n - 1))
    prims = [("c", Q[i], rs[i]) for i in range(ic, n)]
    pin.grupo(prims, base)
    if not sil:
        vf = sp.get("vientre", 0.0)
        if vf:
            vp = []
            for i in range(ic, n):
                hd = _sentido(Q, i)
                d = (-hd[1], hd[0])
                r = rs[i]
                vp.append(("c", (Q[i][0] + d[0] * r * (1 - vf), Q[i][1] + d[1] * r * (1 - vf)), r * vf))
            for pr in vp:
                pin.circ(pr[1], pr[2], col["c"])
        for ex in sp["extras"]:
            _extra(pin, p, sp, ident, ex, Q, rs, us, col, t)
    # ---- aletas cercanas
    dibujar_aletas(1, False)
    # ---- cabeza
    ch = sp["cabeza"]
    h = T.HEADS[ch["tipo"]]
    i0 = int(round(ch["u"] * (n - 1)))
    hd = _sentido(Q, i0, 3)
    ang = math.atan2(hd[1], hd[0]) + ch["ang"]
    z = ch["z"]
    cx, cy = Q[i0]
    for clave, pr, blando in h["grupos"]:
        if blando == "esq":
            continue
        pr2 = T._expandir([T._xf_prim(q, cx, cy, z, ang) for q in pr])
        pin.grupo(pr2, col[clave], 3.0 if clave not in ("m", "n") else 2.4)
    if sil:
        return
    C.cara(pin, p, h, cx, cy, z, ang, t, col)


def _giro(q, th):
    ca, sa = math.cos(th), math.sin(th)
    return (q[0] * ca - q[1] * sa, q[0] * sa + q[1] * ca)


def _extra(pin, p, sp, ident, ex, Q, rs, us, col, t):
    n = len(Q)
    if ex == "branquias":
        for u in (0.2, 0.235, 0.27, 0.305):
            i = int(u * (n - 1))
            hd = _sentido(Q, i)
            d = (-hd[1], hd[0])
            r = rs[i]
            a = (Q[i][0] - d[0] * r * 0.5, Q[i][1] - d[1] * r * 0.5)
            b = (Q[i][0] + d[0] * r * 0.3 - hd[0] * 4, Q[i][1] + d[1] * r * 0.3 - hd[1] * 4)
            m = ((a[0] + b[0]) / 2 + hd[0] * 5, (a[1] + b[1]) / 2 + hd[1] * 5)
            pin.linea([a, m, b], oscurecer(sp["color"], 0.35), 2.4)
    elif ex == "manchas":
        for (u, k, rr) in sp.get("manchas", []):
            i = int(u * (n - 1))
            hd = _sentido(Q, i)
            d = (-hd[1], hd[0])
            r = rs[i]
            pin.circ((Q[i][0] - d[0] * r * k, Q[i][1] - d[1] * r * k), rr, oscurecer(sp["color"], 0.25))
    elif ex == "rayas":
        for u in sp.get("rayas_u", ()):
            i = int(u * (n - 1))
            hd = _sentido(Q, i)
            d = (-hd[1], hd[0])
            r = rs[i]
            pin.linea([(Q[i][0] - d[0] * r * 0.92, Q[i][1] - d[1] * r * 0.92), (Q[i][0] - d[0] * r * 0.35, Q[i][1] - d[1] * r * 0.35)],
                      oscurecer(sp["color"], 0.25), 5)
    elif ex == "plumas_cola":
        # plumas a los lados de la cola (arqueopterix)
        for k in range(7):
            u = 0.6 + 0.058 * k
            i = int(u * (n - 1))
            hd = _sentido(Q, i)
            d = (-hd[1], hd[0])
            for sg in (-1, 1):
                ang = math.atan2(hd[1], hd[0]) + math.pi + sg * 0.55
                L = 30 - k * 1.4
                tip = (Q[i][0] + math.cos(ang) * L, Q[i][1] + math.sin(ang) * L)
                pin.grupo([("e", ((Q[i][0] + tip[0]) / 2, (Q[i][1] + tip[1]) / 2), L * 0.52, 4.0, ang)],
                          sp["acento"] if sg > 0 else oscurecer(sp["acento"], 0.2), 1.8)


def dibujar(p, ident, x, y, escala=1.0, t=0.0, silueta=False):
    C.pintar_vivo(p, ident, x, y, escala, t, silueta, lambda *a: _pintar(a[0], ident, *a[1:]), CAJA)


# ====================================================================== esqueleto
def _pts_cabeza(sp, ident):
    ch = sp["cabeza"]
    P, us, rs = geo(ident)
    n = len(P)
    i0 = int(round(ch["u"] * (n - 1)))
    hd = _sentido(P, i0, 3)
    return P[i0], math.atan2(hd[1], hd[0]) + ch["ang"], ch["z"]


def _esq_craneo(L, ident):
    sp = SP[ident]
    h = T.HEADS[sp["cabeza"]["tipo"]]
    (cx, cy), ang, z = _pts_cabeza(sp, ident)
    z = sp.get("z_esq", z)
    tonos = dict(b=HUESO, c=(244, 238, 216), m=HUESO_CLARO, o=HUESO_MEDIO, n=HUESO_MEDIO, a=HUESO, r=HUESO, k=OSCURO, x=HUESO_CLARO)
    for clave, prims, blando in h["grupos"]:
        if blando is True:
            continue
        for pr in prims:
            q = T._xf_prim(pr, cx, cy, z, ang)
            if q[0] == "k":
                L.linea(q[1], 2 * sum(q[2]) / len(q[2]), (tonos[clave], SOMBRA))
            elif q[0] == "p":
                L.poli(q[1], hueso=tonos[clave], sombra=SOMBRA if clave != "m" else (225, 215, 190))
            elif q[0] == "e":
                L.elipse(q[1][0], q[1][1], q[2], q[3], q[4], hueso=tonos[clave])
            else:
                L.elipse(q[1][0], q[1][1], q[2], q[2], hueso=tonos[clave])
    for x0, x1, yy, nn, tam in h.get("dientes", []):
        for i in range(nn):
            xx = x0 + (x1 - x0) * (i + 0.5) / nn
            w = (x1 - x0) / nn * 0.42
            L.poli(rot([(xx - w, yy - 1), (xx + w, yy - 1), (xx, yy + tam)], cx, cy, z, ang),
                   hueso=(255, 253, 244), sombra=(225, 215, 190), grosor=1.2)
    ox, oy, r0 = h["ojo"]
    px, py = rot([(ox, oy)], cx, cy, z, ang)[0]
    L.elipse(px, py, r0 * z * 1.05, r0 * z * 1.15, ang, hueso=OSCURO, sombra=(30, 24, 18), grosor=2.0)


def _tramo(sp, ident, u0, u1):
    P, us, rs = geo(ident)
    n = len(P)
    a, b = int(u0 * (n - 1)), int(u1 * (n - 1))
    return P[a:b + 1], rs[a:b + 1], us[a:b + 1]


def _esq_columna(L, ident):
    sp = SP[ident]
    u0, u1 = sp.get("col_esq", (0.0, 0.7))
    pts, rs, us = _tramo(sp, ident, u0, u1)
    k = 4 if len(pts) > 6 else 1
    pts, rs = pts[::k], rs[::k]
    if pts[-1] != _tramo(sp, ident, u0, u1)[0][-1]:
        pts.append(_tramo(sp, ident, u0, u1)[0][-1])
        rs.append(_tramo(sp, ident, u0, u1)[1][-1])
    esp = sp.get("espina", 10.0)
    L.linea(pts, 5.0)
    for i, (x, y) in enumerate(pts):
        j = min(len(pts) - 1, i + 1)
        dx, dy = pts[max(0, i - 1)][0] - pts[j][0], pts[max(0, i - 1)][1] - pts[j][1]
        m = math.hypot(dx, dy) or 1.0
        hd = (dx / m, dy / m)
        up = (hd[1], -hd[0])
        if esp > 0:
            L.linea([(x, y), (x + up[0] * esp * (0.6 + 0.5 * min(1, rs[i] / 30)), y + up[1] * esp * (0.6 + 0.5 * min(1, rs[i] / 30)))], 2.6)
        rr = max(3.2, min(6.5, 2.5 + rs[i] * 0.10))
        L.elipse(x, y, rr, rr * 0.85, hueso=HUESO, sombra=SOMBRA, grosor=1.5)
    for ex in sp["extras"]:
        if ex == "gastralia":
            pass


def _esq_costillas(L, ident):
    sp = SP[ident]
    if not sp.get("costillas"):
        return
    u0, u1, nn, prof = sp["costillas"]
    P, us, rs = geo(ident)
    n = len(P)
    base = []
    for k in range(nn):
        u = u0 + (u1 - u0) * (k + 0.5) / nn
        i = int(u * (n - 1))
        hd = _sentido(P, i)
        d = (-hd[1], hd[0])
        r = rs[i] * prof
        x, y = P[i]
        arco = spline([(x + d[0] * 3, y + d[1] * 3), (x + d[0] * r * 0.55 + hd[0] * 5, y + d[1] * r * 0.55 + hd[1] * 5),
                       (x + d[0] * r * 0.9, y + d[1] * r * 0.9 - hd[0] * 0), (x + d[0] * r * 0.8 - hd[0] * 7, y + d[1] * r * 0.8 - hd[1] * 7)], 5)
        L.linea(arco, 4.4)
        base.append((x + d[0] * r * 0.8 - hd[0] * 7, y + d[1] * r * 0.8 - hd[1] * 7))
    if len(base) > 1 and not sp.get("sin_esternon"):
        L.linea(base, 2.6)


def _esq_cola(L, ident):
    sp = SP[ident]
    u0, u1 = sp.get("cola_esq", (0.7, 1.0))
    pts, rs, us = _tramo(sp, ident, u0, u1)
    pts, rs = pts[::3], rs[::3]
    L.linea(pts, 3.6)
    for i, (x, y) in enumerate(pts):
        j = min(len(pts) - 1, i + 1)
        dx, dy = pts[max(0, i - 1)][0] - pts[j][0], pts[max(0, i - 1)][1] - pts[j][1]
        m = math.hypot(dx, dy) or 1.0
        hd = (dx / m, dy / m)
        rr = max(2.4, min(5.5, 2.0 + rs[i] * 0.12))
        if i % 2 == 0:
            L.linea([(x, y), (x + hd[1] * rr * 1.6, y - hd[0] * rr * 1.6)], 2.2)
        L.elipse(x, y, rr, rr * 0.85, hueso=HUESO, sombra=SOMBRA, grosor=1.5)
    _esq_aletas(L, ident, 3)


def _radios(pts):
    """Puntas de los radios de una aleta: puntos repartidos por el borde lejano al origen."""
    d = [math.hypot(a, b) for a, b in pts]
    dm = max(d) or 1.0
    n = len(pts)
    lejos = [d[i] > 0.5 * dm for i in range(n)]
    if all(lejos) or not any(lejos):
        return [pts[i] for i in range(n)][:6]
    k0 = next(i for i in range(n) if not lejos[i])
    orden = [(k0 + i) % n for i in range(n)]
    cam = [pts[i] for i in orden if lejos[i]]
    if len(cam) < 2:
        return cam
    tot = largo(cam)
    m = 5 if tot > 40 else 3
    return [en(cam, k / (m - 1))[0] for k in range(m)]


def _esq_aletas(L, ident, parte):
    sp = SP[ident]
    P, us, rs = geo(ident)
    for lejos in (True, False):
        for al in sp["aletas"]:
            if al.get("parte", 5) != parte or (al.get("lado", "c") == "l") != lejos:
                continue
            if al.get("sin_hueso"):
                continue
            al2 = dict(al, off=0.1)
            pts, o, hd, nrm = _colocar_aleta(sp, ident, al2, P, 0.0, lejos)
            loc = [((q[0] - o[0]), (q[1] - o[1])) for q in pts]
            col = C.HUESO_LEJOS if lejos else (HUESO, SOMBRA)
            if al.get("alas"):
                _esq_ala(L, sp, al, o, loc, col, lejos)
                continue
            tips = _radios(loc)
            cx = sum(a for a, b in tips) / len(tips)
            cy = sum(b for a, b in tips) / len(tips)
            m = math.hypot(cx, cy) or 1.0
            k = al.get("humero", 0.3)
            hx, hy = (o[0] + cx * k * 0.9, o[1] + cy * k * 0.9)
            L.linea([o, (hx, hy)], 6.0, col)
            L.nudo(o, 5.0, col)
            L.nudo((hx, hy), 4.2, col)
            for a, b in tips:
                tx, ty = o[0] + a, o[1] + b
                segs = 4
                L.linea([(hx, hy), (tx, ty)], 2.8, col)
                for s_ in range(1, segs + 1):
                    u = s_ / segs
                    L.elipse(hx + (tx - hx) * u, hy + (ty - hy) * u, 3.0, 3.0, hueso=col[0], sombra=col[1], grosor=1.2)


def _esq_ala(L, sp, al, o, loc, col, lejos):
    """Esqueleto de un ala: brazo, muneca, dedo alar largo y tres deditos con garra."""
    ala = al["alas"]
    tp = loc[ala["punta"]]
    Lg = math.hypot(tp[0], tp[1])
    th = math.atan2(tp[1], tp[0])
    dx, dy = math.cos(th), math.sin(th)
    px, py = -dy, dx
    codo = (o[0] + dx * Lg * 0.28 + px * Lg * 0.04, o[1] + dy * Lg * 0.28 + py * Lg * 0.04)
    mun = (o[0] + dx * Lg * 0.45, o[1] + dy * Lg * 0.45)
    punta = (o[0] + dx * Lg * 1.0, o[1] + dy * Lg * 1.0)
    L.linea([o, codo, mun], 7.0, col)
    L.nudo(o, 5.5, col)
    L.nudo(codo, 4.8, col)
    L.nudo(mun, 4.6, col)
    L.linea([mun, punta], 5.0, col)
    for s_ in range(1, 6):
        u = s_ / 6
        L.elipse(mun[0] + (punta[0] - mun[0]) * u, mun[1] + (punta[1] - mun[1]) * u, 3.6, 3.6, hueso=col[0], sombra=col[1], grosor=1.2)
    for k, ang in enumerate((-0.5, -0.1, 0.35)):
        a = th + ang + 1.1 * (1 if not ala.get('inv') else -1)
        fx, fy = mun[0] + math.cos(a) * 24, mun[1] + math.sin(a) * 24
        L.linea([mun, (fx, fy)], 3.0, col)
        L.poli([(fx - 2, fy - 3), (fx + 9 * math.cos(a), fy + 9 * math.sin(a)), (fx + 3, fy + 4)], hueso=HUESO_CLARO, grosor=1.2)
    if ala.get("plumas"):
        for s_ in range(6):
            u = 0.3 + 0.7 * s_ / 5
            qx, qy = o[0] + dx * Lg * u, o[1] + dy * Lg * u
            L.linea([(qx, qy), (qx + px * 18, qy + py * 18)], 2.0, col)


def _partes(ident):
    return [lambda L, i=ident: _esq_craneo(L, i), lambda L, i=ident: _esq_columna(L, i),
            lambda L, i=ident: _esq_costillas(L, i), lambda L, i=ident: _esq_cola(L, i),
            lambda L, i=ident: _esq_aletas(L, i, 4), lambda L, i=ident: _esq_aletas(L, i, 5)]
