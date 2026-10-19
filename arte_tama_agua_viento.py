"""Mascotas Tamagotchi de AGUA (delfin, tortuga, pulpo) y VIENTO (mariposa, ardilla, buho): 4 etapas cada una.

DIBUJOS = {especie_id: fn(p, etapa, cx, cy, escala, t, estado, dir, silueta)}.
(cx, cy) = centro del cuerpo. Altura con escala 1: 120 / 165 / 215 / 270 px segun la etapa.

Tecnica: cada dibujo se construye UNA vez en capas (superficies recortadas, supermuestreadas para suavizar bordes) y se guarda en cache
por (especie, etapa, escala redondeada). Cada cuadro solo recoloca/escala/rota capas pequenas (barato), pone ojos y boca en vivo
(arte_tama_base) y unos efectos sencillos segun el estado.
"""

import math

import pygame

import arte_tama_base as B
from nucleo import aclarar, oscurecer

ALTOS = (120, 165, 215, 270)
CONT = B.CONTORNO
_CACHE = {}
_MAX_CACHE = 48


# ----------------------------------------------------------------------------------------------------------------------
# Utilidades geometricas
# ----------------------------------------------------------------------------------------------------------------------
def _mez(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _spline(pts, cerrado=True, n=8):
    m = len(pts)
    out = []
    rango = range(m) if cerrado else range(m - 1)
    for i in rango:
        p1 = pts[i]
        p2 = pts[(i + 1) % m]
        p0 = pts[(i - 1) % m] if (cerrado or i > 0) else p1
        p3 = pts[(i + 2) % m] if (cerrado or i + 2 < m) else p2
        for j in range(n):
            u = j / n
            u2 = u * u
            u3 = u2 * u
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3) for k in (0, 1)))
    if not cerrado:
        out.append(tuple(pts[-1]))
    return out


def _esc(pts, o, f, fy=None):
    """Escala una lista de puntos respecto de o."""
    fy = f if fy is None else fy
    return [(o[0] + (x - o[0]) * f, o[1] + (y - o[1]) * fy) for x, y in pts]


def _esp(pts):
    """Espeja una lista de puntos en x."""
    return [(-x, y) for x, y in pts]


def _el_pts(cx, cy, rx, ry, ang=0.0, n=32):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for i in range(n):
        a = i / n * math.tau
        x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Lienzo: dibuja en unidades (100 unidades = altura nominal) sobre una superficie de trabajo y va guardando capas recortadas
# ----------------------------------------------------------------------------------------------------------------------
class Lienzo:
    def __init__(s, u, ss):
        s.u, s.ss = u, ss
        s.k = u * ss
        s.W, s.H = int(260 * s.k), int(210 * s.k)
        s.ox, s.oy = s.W / 2.0, s.H / 2.0
        s.work = pygame.Surface((s.W, s.H), pygame.SRCALPHA)
        s.capas = []
        s.anim = None
        s.cara_idx = None
        s.bw = max(2, int(round(2.1 * s.k)))

    # -- capas
    def capa(s, anim=None):
        s._cerrar()
        s.anim = anim

    def cara_aqui(s):
        s._cerrar()
        s.cara_idx = len(s.capas)

    def _cerrar(s):
        r = s.work.get_bounding_rect()
        if r.width > 0 and r.height > 0:
            sub = s.work.subsurface(r).copy()
            w = max(1, int(round(r.w / s.ss)))
            h = max(1, int(round(r.h / s.ss)))
            sub = pygame.transform.smoothscale(sub, (w, h))
            off = ((r.x - s.ox) / s.ss, (r.y - s.oy) / s.ss)
            pv = (0.0, 0.0)
            a = s.anim
            if a and "pv" in a:
                pv = (a["pv"][0] * s.u, a["pv"][1] * s.u)
            s.capas.append({"surf": sub, "off": off, "anim": a, "pv": pv, "var": {}})
        s.work.fill((0, 0, 0, 0))
        s.anim = None

    def fin(s):
        s._cerrar()
        if s.cara_idx is None:
            s.cara_idx = len(s.capas)
        return s.capas

    # -- primitivas (unidades)
    def _p(s, q):
        return (s.ox + q[0] * s.k, s.oy + q[1] * s.k)

    def _lin(s, pts_px, grosor=None, col=CONT, cerrado=True):
        g = grosor or s.bw
        pygame.draw.lines(s.work, col, cerrado, pts_px, g)
        r = max(1, g // 2)
        for q in pts_px[::2]:
            pygame.draw.circle(s.work, col, (int(q[0]), int(q[1])), r)

    def forma(s, pts, col, suave=True, luz=True, borde=True, n=7, bcol=None):
        if suave:
            pts = _spline(pts, True, n)
        P = [s._p(q) for q in pts]
        pygame.draw.polygon(s.work, oscurecer(col, 0.2) if luz else col, P)
        if luz:
            xs = [q[0] for q in P]
            ys = [q[1] for q in P]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            hw, hh = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
            for f, cm in ((0.9, 0.0), (0.72, 0.1), (0.5, 0.2)):
                sh = (1 - f)
                Q = [(cx + (x - cx) * f - sh * hw * 0.35, cy + (y - cy) * f - sh * hh * 0.45) for x, y in P]
                pygame.draw.polygon(s.work, aclarar(col, cm) if cm else col, Q)
        if borde:
            s._lin(P, col=bcol or CONT)

    def el(s, cx, cy, rx, ry, col, luz=True, borde=True, ang=0.0, bcol=None):
        if ang:
            return s.forma(_el_pts(cx, cy, rx, ry, ang), col, suave=False, luz=luz, borde=borde, bcol=bcol)
        X, Y = s._p((cx, cy))
        rxp, ryp = rx * s.k, ry * s.k
        r = pygame.Rect(0, 0, max(2, rxp * 2), max(2, ryp * 2))
        r.center = (X, Y)
        pygame.draw.ellipse(s.work, oscurecer(col, 0.2) if luz else col, r)
        if luz:
            for f, cm in ((0.92, 0.0), (0.76, 0.1), (0.55, 0.2), (0.32, 0.3)):
                sh = 1 - f
                q = pygame.Rect(0, 0, max(2, rxp * 2 * f), max(2, ryp * 2 * f))
                q.center = (X - sh * rxp * 0.42, Y - sh * ryp * 0.5)
                pygame.draw.ellipse(s.work, aclarar(col, cm) if cm else col, q)
        if borde:
            pygame.draw.ellipse(s.work, bcol or CONT, r, s.bw)

    def ma(s, cx, cy, rx, ry, col, alfa=100, ang=0.0):
        """Mancha translucida (aura, manchas de pelaje, brillos)."""
        X, Y = s._p((cx, cy))
        w, h = max(2, int(rx * 2 * s.k)), max(2, int(ry * 2 * s.k))
        t = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(t, tuple(col[:3]) + (int(alfa),), t.get_rect())
        if ang:
            t = pygame.transform.rotate(t, -math.degrees(ang))
        s.work.blit(t, t.get_rect(center=(X, Y)))

    def br(s, cx, cy, rx, ry, alfa=170, ang=0.0):
        s.ma(cx, cy, rx, ry, (255, 255, 255), alfa, ang)

    def tubo(s, ctrl, r0, r1, col, luz=True, n=14, borde=True):
        pts = _spline(ctrl, False, n)
        N = len(pts)
        rs = [(r0 + (r1 - r0) * i / max(1, N - 1)) for i in range(N)]
        if borde:
            for (x, y), r in zip(pts, rs):
                X, Y = s._p((x, y))
                pygame.draw.circle(s.work, CONT, (int(X), int(Y)), int(r * s.k + s.bw * 0.9))
        for (x, y), r in zip(pts, rs):
            X, Y = s._p((x, y))
            pygame.draw.circle(s.work, col, (int(X), int(Y)), max(1, int(r * s.k)))
        if luz:
            for (x, y), r in zip(pts, rs):
                X, Y = s._p((x - r * 0.22, y - r * 0.3))
                pygame.draw.circle(s.work, aclarar(col, 0.22), (int(X), int(Y)), max(1, int(r * s.k * 0.55)))
            for (x, y), r in zip(pts[::2], rs[::2]):
                X, Y = s._p((x - r * 0.3, y - r * 0.4))
                pygame.draw.circle(s.work, aclarar(col, 0.4), (int(X), int(Y)), max(1, int(r * s.k * 0.22)))

    def tr(s, ctrl, w, col, suave=True, borde=True):
        s.tubo(ctrl, w / 2, w / 2, col, luz=False, borde=borde)

    def linea(s, ctrl, w, col, suave=True):
        """Linea fina sin contorno (detalles del dibujo)."""
        pts = _spline(ctrl, False, 8) if suave else ctrl
        P = [s._p(q) for q in pts]
        pygame.draw.lines(s.work, col, False, P, max(1, int(w * s.k)))
        for q in P[::2]:
            pygame.draw.circle(s.work, col, (int(q[0]), int(q[1])), max(1, int(w * s.k / 2)))

    def ng(s, pts, col, suave=True, n=7):
        """Forma plana sin contorno ni luz (manchas del pelaje)."""
        if suave:
            pts = _spline(pts, True, n)
        pygame.draw.polygon(s.work, col, [s._p(q) for q in pts])

    def estrella(s, x, y, r, col, ang=0.0, borde=True):
        pts = []
        for i in range(8):
            rr = r if i % 2 == 0 else r * 0.38
            a = ang + i * math.pi / 4
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        s.forma(pts, col, suave=False, luz=False, borde=borde)


# ----------------------------------------------------------------------------------------------------------------------
# Cache de construccion
# ----------------------------------------------------------------------------------------------------------------------
def _obtener(esp, etapa, escala):
    ek = round(escala * 20) / 20.0
    clave = (esp, etapa, ek)
    ent = _CACHE.get(clave)
    if ent is not None:
        return ent
    if len(_CACHE) >= _MAX_CACHE:
        _CACHE.pop(next(iter(_CACHE)))
    alto = ALTOS[etapa] * ek
    u = alto / 100.0
    ss = 2.0 if u <= 1.75 else 1.5
    c = Lienzo(u, ss)
    cara = _CONSTRUCTORES[esp](c, etapa)
    capas = c.fin()
    top = min([cp["off"][1] for cp in capas] + [0])
    bottom = max([cp["off"][1] + cp["surf"].get_height() for cp in capas] + [0])
    ent = {"capas": capas, "cara": cara, "u": u, "alto": alto, "cara_idx": c.cara_idx, "top": top, "bottom": bottom,
           "pie": cara.get("pie", 50) * u}
    _CACHE[clave] = ent
    return ent


def precalentar(esp, etapa, escala=1.0):
    _obtener(esp, etapa, escala)


def _variante(capa, modo, flip):
    clave = (modo, flip)
    v = capa["var"].get(clave)
    if v is not None:
        return v
    sf = capa["surf"]
    if modo == "sil":
        sf = B.silueta_de(sf, (52, 54, 74))
    elif modo == "enf":
        sf = sf.copy()
        sf.fill((205, 238, 170), special_flags=pygame.BLEND_RGB_MULT)
    elif modo in ("bril1", "bril2"):
        sf = sf.copy()
        v_ = 70 if modo == "bril1" else 150
        sf.fill((v_, v_, v_, 0), special_flags=pygame.BLEND_RGB_ADD)
    ox, oy = capa["off"]
    if flip:
        sf = pygame.transform.flip(sf, True, False)
        ox = -(ox + capa["surf"].get_width())
    v = (sf, ox, oy)
    capa["var"][clave] = v
    return v


# ----------------------------------------------------------------------------------------------------------------------
# Pose segun el estado
# ----------------------------------------------------------------------------------------------------------------------
def _pose(estado, t, alto, dir):
    P = {"dx": 0.0, "dy": 0.0, "sx": 1.0, "sy": 1.0, "am": 1.0, "vm": 1.0, "caida": 0.0, "modo": "n", "flash": 0}
    resp = math.sin(t * 2.2)
    if estado == "feliz":
        a = abs(math.sin(t * 5.0))
        P["dy"] = -a * 0.085 * alto
        P["sy"] = 1.0 + 0.04 * a - 0.05 * (1 - a) * (1 if a < 0.25 else 0)
        P["sx"] = 2.0 - P["sy"] if False else 1.0 - (P["sy"] - 1.0) * 0.6
        P["am"], P["vm"] = 1.7, 1.7
    elif estado == "triste":
        P["dy"] = 0.025 * alto
        P["sy"] = 0.94 + 0.012 * math.sin(t * 1.4)
        P["sx"] = 1.04
        P["am"], P["vm"], P["caida"] = 0.3, 0.5, 1.0
    elif estado == "hambre":
        P["dx"] = math.sin(t * 17) * 0.006 * alto * (1 if math.sin(t * 1.3) > 0.2 else 0)
        P["sy"] = 0.96 + 0.025 * math.sin(t * 3.0)
        P["sx"] = 1.03 - 0.01 * math.sin(t * 3.0)
        P["dy"] = 0.012 * alto
        P["am"], P["vm"], P["caida"] = 0.5, 0.8, 0.55
    elif estado == "duerme":
        P["sy"] = 1.0 + 0.045 * math.sin(t * 1.3)
        P["sx"] = 1.0 - 0.02 * math.sin(t * 1.3)
        P["dy"] = 0.02 * alto
        P["am"], P["vm"], P["caida"] = 0.12, 0.4, 1.0
    elif estado == "enfermo":
        P["dx"] = math.sin(t * 28) * 0.007 * alto
        P["sy"] = 0.95 + 0.01 * math.sin(t * 2)
        P["sx"] = 1.03
        P["dy"] = 0.02 * alto
        P["am"], P["vm"], P["caida"] = 0.3, 0.6, 0.8
        P["modo"] = "enf"
    elif estado == "come":
        m = math.sin(t * 13)
        P["sy"] = 1.0 + 0.045 * m
        P["sx"] = 1.0 - 0.03 * m
        P["dy"] = -0.01 * alto * abs(m)
        P["am"], P["vm"] = 1.3, 1.5
    elif estado == "ataca":
        ph = math.sin(t * 6.0)
        P["dx"] = dir * max(0.0, ph) * 0.13 * alto
        P["sx"] = 1.0 + max(0.0, ph) * 0.07
        P["sy"] = 1.0 - max(0.0, ph) * 0.04
        P["dy"] = -0.01 * alto
        P["am"], P["vm"] = 1.8, 2.2
    elif estado == "golpeado":
        P["dx"] = -dir * 0.07 * alto + math.sin(t * 40) * 0.012 * alto
        P["sx"], P["sy"] = 0.96, 1.04
        P["dy"] = -0.02 * alto
        P["am"], P["vm"] = 0.5, 2.0
        if math.sin(t * 22) > 0:
            P["modo"], P["flash"] = "n", 150
    elif estado == "evoluciona":
        P["sx"] = P["sy"] = 1.0 + 0.05 * math.sin(t * 9)
        P["dy"] = -0.015 * alto
        P["am"], P["vm"] = 1.5, 2.0
        P["flash"] = int(60 + 90 * (0.5 + 0.5 * math.sin(t * 7)))
    else:
        P["dy"] = math.sin(t * 2.2) * 0.012 * alto
        P["sy"] = 1.0 + 0.022 * resp
        P["sx"] = 1.0 - 0.012 * resp
    return P


def _transformar_capa(capa, pose, t, flip, modo, u, pie, dx, dy):
    """Devuelve (superficie, x, y) relativos al centro del cuerpo, ya con la pose aplicada."""
    sf, ox, oy = _variante(capa, modo, flip)
    sx, sy = pose["sx"], pose["sy"]
    a = capa["anim"]
    pvx, pvy = capa["pv"]
    if flip:
        pvx = -pvx
    # escala global respecto de los pies
    if abs(sx - 1) > 0.002 or abs(sy - 1) > 0.002:
        w, h = sf.get_size()
        nw, nh = max(1, int(round(w * sx))), max(1, int(round(h * sy)))
        sf = pygame.transform.smoothscale(sf, (nw, nh))
        ox = ox * sx
        oy = pie + (oy - pie) * sy
        pvx, pvy = pvx * sx, pie + (pvy - pie) * sy
    x, y = ox, oy
    if a:
        tp = a["tipo"]
        ph = t * pose["vm"] * a.get("vel", 2.0) + a.get("fase", 0.0)
        if tp == "rot":
            ang = a.get("amp", 8) * math.sin(ph) * pose["am"] + a.get("cd", 0) * pose["caida"]
            if flip:
                ang = -ang
            if abs(ang) > 0.3:
                w, h = sf.get_size()
                icx, icy = x + w / 2, y + h / 2
                vx, vy = icx - pvx, icy - pvy
                r = math.radians(ang)
                c, s_ = math.cos(r), math.sin(r)
                nx, ny = pvx + vx * c + vy * s_, pvy - vx * s_ + vy * c
                sf = pygame.transform.rotate(sf, ang)
                x, y = nx - sf.get_width() / 2, ny - sf.get_height() / 2
        elif tp == "flap":
            f = 1.0 - a.get("amp", 0.4) * (0.5 + 0.5 * math.sin(ph)) * min(1.6, pose["am"])
            f *= 1.0 - a.get("cd", 0.0) * pose["caida"]
            f = max(0.12, f)
            w, h = sf.get_size()
            nw = max(1, int(w * f))
            sf = pygame.transform.smoothscale(sf, (nw, h))
            x = pvx + (x - pvx) * f
        elif tp == "flot":
            y += a.get("amp", 3) * u * math.sin(ph)
            x += a.get("ampx", 0) * u * math.cos(ph * 0.8)
    return sf, x + dx, y + dy


# ----------------------------------------------------------------------------------------------------------------------
# Efectos de estado (baratos, en vivo)
# ----------------------------------------------------------------------------------------------------------------------
def _estrella_px(p, x, y, r, col, ang=0.0):
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.4
        a = ang + i * math.pi / 4
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    pygame.draw.polygon(p, CONT, pts, max(1, int(r * 0.22)))
    pygame.draw.polygon(p, col, pts)


def _z(p, x, y, r, a):
    pts = [(x - r, y - r), (x + r, y - r), (x - r, y + r), (x + r, y + r)]
    pygame.draw.lines(p, CONT, False, pts, max(3, int(r * 0.7)))
    pygame.draw.lines(p, (235, 245, 255), False, pts, max(2, int(r * 0.38)))


def _efectos(p, estado, t, cx, cy, u, ent, fx, fy, dir, cara, pose):
    top = cy + ent["top"] + pose["dy"]
    if estado == "duerme":
        for i in range(3):
            ph = (t * 0.45 + i / 3.0) % 1.0
            _z(p, fx + dir * (22 + ph * 26) * u, top + 22 * u - ph * 36 * u, (3.5 + ph * 5) * u, ph)
    elif estado == "feliz":
        for i in range(4):
            a = t * 1.8 + i * math.tau / 4
            ph = (t * 1.5 + i * 0.25) % 1.0
            r = (3.5 + 3 * math.sin(ph * math.pi)) * u
            _estrella_px(p, cx + math.cos(a) * 50 * u, cy - 6 * u + math.sin(a) * 36 * u - 10 * u, r, (255, 230, 90), t * 3 + i)
    elif estado == "triste":
        ex = fx + cara["ojos"][2] / 2 * u * dir
        for i in range(2):
            ph = (t * 0.7 + i * 0.5) % 1.0
            y = fy + (6 + ph * 26) * u
            r = (2.4 + (1 - ph) * 1.4) * u
            pygame.draw.ellipse(p, (130, 200, 255), (ex - r, y - r * 1.3, r * 2, r * 2.6))
            pygame.draw.ellipse(p, CONT, (ex - r, y - r * 1.3, r * 2, r * 2.6), max(1, int(u)))
    elif estado == "hambre":
        # gotita de baba y lineas de "ruido de tripa"
        ph = (t * 0.8) % 1.0
        bx = fx + dir * cara["boca"][0] * u
        by = fy + (cara["boca"][1] + 10 + ph * 12) * u
        pygame.draw.ellipse(p, (170, 225, 255), (bx - 2 * u, by - 3 * u, 4 * u, 6 * u))
        for sgn in (-1, 1):
            for k in range(2):
                a = pygame.Rect(0, 0, 14 * u, 10 * u)
                a.center = (cx + sgn * (46 + k * 7) * u, cy + (14 + k * 7) * u + math.sin(t * 6 + k) * 1.5 * u)
                pygame.draw.arc(p, CONT, a, -0.9 if sgn > 0 else math.pi - 0.9 + 0.2, 0.9 if sgn > 0 else math.pi + 0.9, max(2, int(1.6 * u)))
    elif estado == "enfermo":
        for i in range(3):
            ph = (t * 0.6 + i / 3.0) % 1.0
            x = cx + math.sin(t * 2 + i * 2.1) * 30 * u
            y = top + 10 * u - ph * 14 * u
            r = (3 + 2 * i) * u * (1 - ph * 0.4)
            pygame.draw.circle(p, (150, 205, 120), (int(x), int(y)), int(r))
            pygame.draw.circle(p, CONT, (int(x), int(y)), int(r), max(1, int(u)))
        # gota de sudor
        ex = fx - dir * cara["ojos"][2] * 0.9 * u
        pygame.draw.ellipse(p, (170, 225, 255), (ex - 2.5 * u, fy - 20 * u - 4 * u, 5 * u, 9 * u))
        pygame.draw.ellipse(p, CONT, (ex - 2.5 * u, fy - 20 * u - 4 * u, 5 * u, 9 * u), max(1, int(u)))
    elif estado == "come":
        bx = fx + dir * cara["boca"][0] * u
        by = fy + cara["boca"][1] * u + 3 * u
        for i in range(4):
            ph = (t * 3.0 + i * 0.25) % 1.0
            a = -0.4 - i * 0.55 + (i % 2) * 0.3
            x = bx + dir * math.cos(a) * ph * 26 * u * (1 if i % 2 else -1) * 0.7
            y = by + math.sin(a) * ph * 22 * u + ph * ph * 30 * u
            pygame.draw.circle(p, (255, 205, 110), (int(x), int(y)), max(1, int(2.4 * u * (1 - ph * 0.5))))
    elif estado == "ataca":
        for i in range(3):
            y = cy + (-18 + i * 18) * u
            ph = (t * 6.0 + i) % math.tau
            L = (18 + 8 * math.sin(ph)) * u
            x0 = cx - dir * 52 * u
            pygame.draw.line(p, (255, 255, 255), (x0, y), (x0 - dir * L, y), max(2, int(2.5 * u)))
        _estrella_px(p, cx + dir * 62 * u, cy - 20 * u, (5 + 2 * math.sin(t * 12)) * u, (255, 240, 130), t * 4)
    elif estado == "golpeado":
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            _estrella_px(p, cx + math.cos(a) * 24 * u, top - 2 * u + math.sin(a) * 6 * u, 4.5 * u, (255, 232, 100), t * 2)
    elif estado == "evoluciona":
        for i in range(10):
            a = t * 1.3 + i * math.tau / 10
            L0, L1 = 56 * u, (82 + 14 * math.sin(t * 6 + i * 1.7)) * u
            pygame.draw.line(p, (255, 252, 210), (cx + math.cos(a) * L0, cy + math.sin(a) * L0),
                             (cx + math.cos(a) * L1, cy + math.sin(a) * L1), max(2, int(2.6 * u)))
        for i in range(4):
            a = -t * 2.1 + i * math.tau / 4
            _estrella_px(p, cx + math.cos(a) * 66 * u, cy + math.sin(a) * 52 * u, (3.5 + math.sin(t * 8 + i) * 1.5) * u, (255, 255, 160), t * 3)


# ----------------------------------------------------------------------------------------------------------------------
# Dibujo generico
# ----------------------------------------------------------------------------------------------------------------------
def _dibujar(esp, p, etapa, cx, cy, escala, t, estado, dir, silueta):
    etapa = max(0, min(3, int(etapa)))
    ent = _obtener(esp, etapa, escala)
    u, alto = ent["u"], ent["alto"]
    pose = _pose(estado, t, alto, 1 if dir >= 0 else -1)
    flip = dir < 0
    sg = -1 if flip else 1
    modo = "sil" if silueta else pose["modo"]
    if not silueta and pose["flash"]:
        modo = "bril2" if pose["flash"] > 120 else "bril1"
    pie = ent["pie"]
    dx, dy = pose["dx"], pose["dy"]
    ccx, ccy = cx, cy
    if not silueta:
        # sombra en el suelo
        sc = 1.0 - abs(dy) / (alto * 3.0)
        B.sombra(p, cx + dx, cy + pie + 3 * u, alto * 0.78 * sc, alto * 0.14 * sc, 70)
    cara = ent["cara"]
    ci = ent["cara_idx"]
    capas = ent["capas"]
    flash = pose["flash"]
    for i, capa in enumerate(capas):
        if i == ci and not silueta:
            _cara(p, ent, cara, cx, cy, u, t, estado, sg, pose, pie)
        sf, x, y = _transformar_capa(capa, pose, t, flip, modo, u, pie, dx, dy)
        p.blit(sf, (cx + x, cy + y))
    if ci >= len(capas) and not silueta:
        _cara(p, ent, cara, cx, cy, u, t, estado, sg, pose, pie)
    if not silueta and estado not in ("normal",):
        fx, fy = _pos_cara(cara, cx, cy, u, sg, pose, pie)
        _efectos(p, estado, t, cx + dx, cy + dy, u, ent, fx, fy, sg, cara, pose)


def _pos_cara(cara, cx, cy, u, sg, pose, pie):
    ox, oy = cara["ojos"][0] * u * sg, cara["ojos"][1] * u
    oy = pie + (oy - pie) * pose["sy"]
    return cx + ox * pose["sx"] + pose["dx"], cy + oy + pose["dy"]


def _cara(p, ent, cara, cx, cy, u, t, estado, sg, pose, pie):
    fx, fy = _pos_cara(cara, cx, cy, u, sg, pose, pie)
    ex, ey, sep, r = cara["ojos"]
    fase = cara.get("fase", 0.0)
    B.ojos(p, fx, fy, sep * u, max(3, r * u), estado, t, cara.get("ojo", (40, 30, 60)), sg, fase)
    mj = cara.get("mej")
    if mj and estado not in ("duerme",):
        B.mejillas(p, fx + (mj[0] - ex) * u * sg, fy + (mj[1] - ey) * u, mj[2] * u, mj[3] * u, mj[4])
    bc = cara.get("boca")
    if bc:
        bx = fx + (bc[0] - ex) * u * sg
        by = fy + (bc[1] - ey) * u
        if estado == "normal" and cara.get("sin_boca_normal"):
            return
        B.boca(p, bx, by, bc[2] * u, estado, t)


# ======================================================================================================================
# ESPECIES
# ======================================================================================================================
def _delfin(c, e):
    A, D, V, C = (66, 158, 238), (40, 106, 205), (232, 247, 255), (120, 230, 255)
    # aura (solo ultimate)
    if e == 3:
        c.capa({"tipo": "flot", "amp": 3, "vel": 1.6})
        c.ma(0, 4, 78, 62, C, 60)
        for (x, y, r) in ((-70, -30, 6), (74, -40, 5), (-60, 40, 4), (66, 30, 7), (0, -78, 5)):
            c.el(x, y, r, r, (200, 245, 255), luz=False)
            c.br(x - r * .3, y - r * .3, r * .4, r * .3, 220)
    # cola
    c.capa({"tipo": "rot", "pv": (-26, 16), "amp": 9, "vel": 3.2, "cd": -12})
    tx, ty = -52 - 2 * e, -4 - 2 * e
    c.tubo([(-22, 18), (-42, 24), (tx + 2, ty + 14), (tx, ty)], 11, 4.5, A)
    f = 0.8 + 0.14 * e
    fk = _esc([(0, 2), (12, -6), (24, -22), (8, -18), (0, -10), (-8, -18), (-24, -22), (-12, -6)], (0, 0), f)
    c.forma([(tx + x, ty + y) for x, y in fk], D)
    if e == 3:
        for sg in (-1, 1):
            c.ma(tx + sg * 22 * f, ty - 20 * f, 7, 5, C, 170)
    # aleta dorsal
    c.capa({"tipo": "rot", "pv": (-18, -22), "amp": 3, "vel": 2.0, "cd": 8})
    h = 3 + 3 * e
    c.forma([(-26, -16), (-34, -30 - h), (-10, -32 - h * .4), (0, -22)], D)
    # cuerpo
    c.capa()
    c.el(-8, 10, 40, 34, A)
    c.el(2, 20, 27, 20, V, borde=False)
    if e >= 2:
        for i, y in enumerate((8, 16, 24)):
            c.linea([(-38 + i * 3, y), (-24, y - 5), (-8, y + 2), (4 + i * 2, y - 2)], 1.4, D)
    if e >= 1:
        c.linea([(-30, 30), (-10, 38), (14, 36)], 1.8, A if False else (170, 215, 250))
    # cabeza y pico
    c.el(16, -10, 31, 28, A)
    c.forma([(36, -9), (58, -3), (63, 3), (57, 8), (36, 10)], A, n=6)
    c.forma([(36, 8), (55, 9), (51, 15), (36, 17)], V, n=6)
    c.br(8, -28, 10, 4, 150, -0.3)
    c.cara_aqui()
    # cresta (adulto+)
    if e >= 2:
        n = 2 if e == 2 else 3
        for i in range(n):
            x = 4 + i * 10 - (n - 1) * 5
            c.forma([(x, -34), (x - 4 - e, -48 - e * 3 + (i == 1) * -5), (x + 5 + e, -38 + (i == 1) * -3)], C if e == 3 else (150, 220, 255))
    if e == 3:
        c.el(16, -34, 4.2, 4.2, (255, 252, 240))
        c.br(15, -35, 1.6, 1.2, 230)
    # aleta pectoral
    c.capa({"tipo": "rot", "pv": (-2, 16), "amp": 13, "vel": 3.2, "fase": 1.2, "cd": 16})
    fl = 1 + 0.18 * e
    c.forma(_esc([(-6, 12), (14, 18), (26, 36), (12, 38), (-2, 28)], (-6, 12), fl), D)
    if e == 3:
        c.ma(20, 38, 6, 5, C, 160)
    return {"ojos": (18, -12, 21, 7.0 + 0.5 * (e == 0)), "boca": (46, 12, 12), "mej": (14, -2, 29, 5.5, (255, 140, 170)),
            "ojo": (30, 60, 130), "pie": 48}


def _tortuga(c, e):
    P, PD = (104, 204, 140), (70, 160, 110)
    CAR, CARL, HEX, VIE = (46, 142, 128), (74, 182, 160), (150, 222, 190), (252, 232, 170)
    if e == 3:
        c.capa({"tipo": "flot", "amp": 3, "vel": 1.5})
        c.ma(-4, 2, 82, 60, (130, 225, 255), 55)
        for (x, y, r) in ((-72, -20, 6), (76, -30, 5), (64, 40, 6), (-64, 36, 4)):
            c.el(x, y, r, r, (205, 245, 255), luz=False)
            c.br(x - r * .3, y - r * .3, r * .4, r * .3, 220)
    # patas traseras y cola
    c.capa({"tipo": "rot", "pv": (-30, 26), "amp": 6, "vel": 2.4, "fase": 1, "cd": 8})
    c.el(-32, 38, 13 + e, 10, PD)
    c.capa()
    c.forma([(-46, 18), (-62 - e * 3, 22), (-48, 28)], P)
    # caparazon
    br_, bh = 42 + 3 * e, 36 + 2 * e
    c.el(-6, 0, br_, bh, CAR)
    # borde inferior (vientre del caparazon)
    c.forma(_esc([(-44, 22), (-6, 38), (36, 22), (30, 30), (-6, 44), (-40, 30)], (-6, 22), 1.0), VIE if False else (236, 210, 140), n=6)
    c.el(-6, 0, br_, bh, CAR)
    # placas hexagonales
    hx = [(-6, -14, 11), (-26, -4, 9), (14, -4, 9), (-14, 14, 9), (6, 14, 9)] if e >= 1 else [(-6, -12, 10), (-24, 6, 8), (12, 6, 8)]
    for (x, y, r) in hx:
        pts = [(x + math.cos(math.pi / 6 + i * math.pi / 3) * r, y + math.sin(math.pi / 6 + i * math.pi / 3) * r * 0.88) for i in range(6)]
        c.forma(pts, HEX if e < 3 else (170, 240, 235), suave=False, borde=True, luz=True)
    c.br(-26, -26, 14, 5, 130, -0.4)
    if e >= 2:
        # coral y alga sobre el caparazon
        c.tr([(-24, -34), (-28, -46), (-22, -56)], 3, (255, 130, 140))
        c.tr([(-28, -46), (-36, -50)], 2.4, (255, 130, 140))
        c.tr([(-14, -36), (-10, -50), (-16, -62)], 3, (80, 200, 120))
        c.el(-34, -50, 3, 3, (255, 190, 195), luz=False)
    if e == 3:
        c.estrella(8, -50, 7, (255, 245, 170), 0.2)
        for (x, y) in ((-6, -2), (-26, -4), (14, -4)):
            c.br(x, y, 3.5, 2.2, 200)
        c.linea([(-40, 8), (-30, 2), (-20, 8), (-10, 2)], 1.6, (190, 245, 255))
    # cabeza y cuello
    c.el(32, 14, 11 + e, 11, P)
    c.el(38, 12, 22 + e, 20 + e, P)
    c.el(38, 24, 11, 6, (180, 235, 190), borde=False)
    c.br(32, 0, 8, 3, 130, -0.3)
    c.cara_aqui()
    # patas delanteras
    c.capa({"tipo": "rot", "pv": (10, 30), "amp": 8, "vel": 3.0, "cd": 12})
    c.el(14, 38, 14 + e, 11, P)
    c.el(14, 44, 7, 3, (190, 240, 200), borde=False)
    return {"ojos": (40, 8, 17, 6.2 + 0.3 * (e == 0)), "boca": (45, 24, 11), "mej": (38, 18, 26, 4.5, (255, 150, 170)),
            "ojo": (30, 70, 70), "pie": 48}


def _pulpo(c, e):
    P, PD, SU = (176, 118, 244), (130, 84, 214), (255, 214, 250)
    C = (110, 235, 255)
    if e >= 2:
        c.capa({"tipo": "flot", "amp": 2.5, "vel": 1.6})
        c.ma(0, -8, 74 if e == 3 else 62, 64 if e == 3 else 54, C, 48)
        if e == 3:
            for (x, y, r) in ((-68, -40, 7), (72, -30, 5), (-72, 30, 5), (66, 40, 8), (0, -80, 6)):
                c.el(x, y, r, r, (200, 245, 255), luz=False)
                c.br(x - r * .3, y - r * .3, r * .4, r * .3, 220)
    # tentaculos
    if e == 0:
        pos = [(-22, 26, -30, 46), (22, 26, 30, 46), (-8, 30, -10, 50), (8, 30, 10, 50)]
    elif e == 1:
        pos = [(-30, 22, -52, 40), (30, 22, 52, 40), (-16, 28, -26, 52), (16, 28, 26, 52), (0, 30, 0, 50)]
    else:
        pos = [(-34, 18, -60, 30), (34, 18, 60, 30), (-24, 26, -46, 50), (24, 26, 46, 50), (-10, 30, -20, 54), (10, 30, 20, 54),
               (-38, 10, -70, 14), (38, 10, 70, 14)]
    L = 1.0 + 0.12 * e
    for i, (x0, y0, x1, y1) in enumerate(pos):
        c.capa({"tipo": "rot", "pv": (x0, y0 - 6), "amp": 9 + (i % 3) * 2, "vel": 2.6 + (i % 3) * 0.4, "fase": i * 0.9, "cd": (6 if x0 > 0 else -6)})
        sg = 1 if x1 > 0 else -1
        mx, my = (x0 + (x1 - x0) * 0.55), (y0 + (y1 - y0) * 0.5)
        w0, w1 = 8.5 + e * .6, 3.6
        ctrl = [(x0, y0), (mx, my + 6), (x1 * L, y1 * L - 2), (x1 * L + sg * 6 * (1 + (e >= 2)), y1 * L - 10 - e * 3)]
        c.tubo(ctrl, w0, w1, P if i % 2 == 0 else (186, 132, 248))
        if e >= 1:
            for k in range(3 + e):
                f = 0.25 + k * (0.55 / (3 + e))
                q = _spline(ctrl, False, 6)
                x, y = q[int(f * (len(q) - 1))]
                c.el(x + sg * -0.5, y + 1.5, 1.7, 1.4, SU, luz=False, borde=False)
    # manto
    c.capa()
    c.el(0, -10, 38 + 2 * e, 38 + 2 * e, P)
    if e >= 1:
        for (x, y, r) in ((-18, -34, 4), (-6, -40, 3), (14, -36, 3.6), (24, -28, 2.6)):
            c.el(x, y, r, r * 0.9, SU if e < 3 else C, luz=False, borde=False)
    if e >= 2:
        c.ma(0, 10, 28, 16, SU, 110)
    c.br(-16, -36, 12, 5, 140, -0.5)
    if e == 3:
        for (x, y) in ((-26, -8), (26, -6), (-30, 8), (30, 10)):
            c.el(x, y, 3, 3, C, luz=False, borde=False)
            c.br(x - 1, y - 1, 1.2, 1, 230)
    c.cara_aqui()
    # accesorios frente
    if e == 2:
        # perla en la frente
        c.el(0, -44, 5, 5, (255, 250, 245))
        c.br(-1.2, -45.5, 1.8, 1.3, 240)
    if e == 3:
        # corona de concha
        c.forma([(-22, -42), (-18, -58), (-9, -48), (0, -66), (9, -48), (18, -58), (22, -42)], (255, 230, 150), suave=False)
        c.el(0, -66, 4.5, 4.5, (255, 250, 245))
        c.el(-18, -58, 3.4, 3.4, C)
        c.el(18, -58, 3.4, 3.4, C)
    return {"ojos": (0, -10, 34 - 2 * (e == 0), 11.5 if e == 0 else 10.5), "boca": (0, 8, 12), "mej": (0, 4, 56, 6, (255, 150, 190)),
            "ojo": (60, 40, 120), "pie": 50}


def _mariposa(c, e):
    A1, A2, A3 = (126, 206, 255), (176, 150, 255), (255, 175, 225)
    CR, BODY, HEAD = (255, 244, 214), (176, 140, 226), (255, 232, 220)
    ws = 0.7 + 0.2 * e
    # alas (simetricas, aleteo escalando en x)
    c.capa({"tipo": "flap", "pv": (0, 0), "amp": 0.34, "vel": 6.0, "cd": 0.5})
    if e == 3:
        c.ma(0, 0, 88, 66, (190, 235, 255), 55)
    for sg in (-1, 1):
        # ala trasera
        tail = 6 + 12 * (e >= 2) + 8 * (e == 3)
        pts = [(sg * 8, 6), (sg * 38 * ws, 8), (sg * 54 * ws, 28 + tail * .5), (sg * 40 * ws, 40 + tail), (sg * 24 * ws, 38), (sg * 10, 26)]
        c.forma(pts, A2 if e >= 1 else A1)
        # ala delantera
        pts = [(sg * 8, 0), (sg * 30 * ws, -22 * ws), (sg * 66 * ws, -44 * ws - 4 * e), (sg * 82 * ws, -26 * ws), (sg * 72 * ws, 4), (sg * 46 * ws, 14), (sg * 12, 12)]
        c.forma(pts, A1 if e < 2 else (110, 196, 255))
        # manchas
        c.el(sg * 58 * ws, -20 * ws, 9 * ws + e, 8 * ws + e, CR, luz=False, borde=False)
        c.el(sg * 58 * ws, -20 * ws, 4.4 * ws + e * .5, 4 * ws + e * .5, A3, luz=False, borde=False)
        if e >= 1:
            c.el(sg * 32 * ws, 24 * ws, 6 * ws, 5.5 * ws, CR, luz=False, borde=False)
            c.el(sg * 32 * ws, 24 * ws, 3 * ws, 2.8 * ws, A3, luz=False, borde=False)
        if e >= 2:
            c.linea([(sg * 14, 0), (sg * 40 * ws, -6), (sg * 70 * ws, -14)], 1.5, (235, 245, 255))
            c.linea([(sg * 14, 8), (sg * 34 * ws, 14), (sg * 54 * ws, 26)], 1.5, (235, 245, 255))
        if e == 3:
            c.linea([(sg * 20, -2), (sg * 40, -20), (sg * 60, -30), (sg * 74, -22), (sg * 66, -12)], 1.6, (255, 255, 255))
            c.estrella(sg * 70 * ws, 2, 5, (255, 250, 200), 0.3, borde=False)
            c.estrella(sg * 50 * ws, 36, 4, (255, 250, 200), 0.3, borde=False)
        c.br(sg * 50 * ws, -38 * ws, 14 * ws, 4, 150, sg * -0.5)
    # antenas
    for sg in (-1, 1):
        c.capa({"tipo": "rot", "pv": (sg * 8, -40), "amp": 8, "vel": 3.0, "fase": sg * 1.3, "cd": sg * 14})
        L = 1 + 0.25 * e
        c.tubo([(sg * 6, -40), (sg * 14 * L, -58 * L), (sg * 22 * L, -64 * L)], 2.2, 1.6, (120, 90, 170), luz=False)
        c.el(sg * 22 * L, -65 * L, 4 + e * .5, 4 + e * .5, A3 if e < 3 else (255, 240, 130))
    # cuerpo
    c.capa()
    c.el(0, 24, 16 + e, 24 + e, BODY)
    for i in range(3):
        c.linea([(-12 - e, 14 + i * 9), (0, 18 + i * 9), (12 + e, 14 + i * 9)], 1.8, aclarar(BODY, .35))
    # patitas
    c.tr([(-8, 44), (-12, 52)], 3, (120, 90, 170))
    c.tr([(8, 44), (12, 52)], 3, (120, 90, 170))
    # cabeza
    c.el(0, -14, 27 + e * 1.2, 26 + e * 1.2, HEAD)
    c.el(0, -2, 24, 18, (255, 226, 214), luz=False, borde=False)
    # pelo/pelusa del cuello
    c.el(0, 4, 18, 8, CR, luz=False, borde=False)
    c.cara_aqui()
    if e >= 2:
        # corona de flores
        n = 3 if e == 2 else 5
        for i in range(n):
            a = math.pi + (i + 0.5) / n * math.pi
            x, y = math.cos(a) * 25, -16 + math.sin(a) * 25
            col = A3 if i % 2 == 0 else (255, 240, 130)
            for k in range(5):
                aa = k * math.tau / 5
                c.el(x + math.cos(aa) * 3.4, y + math.sin(aa) * 3.4, 3, 3, col, luz=False)
            c.el(x, y, 2.4, 2.4, (255, 250, 200) if i % 2 == 0 else (255, 150, 120), luz=False)
    return {"ojos": (0, -14, 24, 8.5), "boca": (0, 2, 11), "mej": (0, -6, 42, 5.5, (255, 150, 180)), "ojo": (80, 50, 140), "pie": 52}


def _ardilla(c, e):
    PEL, PELD, VIE = (194, 150, 112), (150, 108, 80), (252, 236, 208)
    MEM, MEMD = (126, 214, 206), (88, 176, 176)
    NARIZ = (255, 150, 160)
    # cola frondosa (atras)
    c.capa({"tipo": "rot", "pv": (-24, 26), "amp": 9, "vel": 2.2, "cd": -10})
    L = 1 + 0.12 * e
    c.tubo([(-18, 32), (-46, 22 - 2 * e), (-58 * L, -12), (-46 * L, -40 - 4 * e)], 11 * L, 14 * L, PEL)
    c.el(-46 * L, -38 - 4 * e, 10 * L, 12 * L, VIE, luz=True, borde=False, ang=0.5)
    c.tubo([(-52, 8), (-56 * L, -8)], 4, 4, VIE if False else PELD, luz=False, borde=False)
    # membranas planeadoras
    if e >= 1:
        sx = 0.75 + 0.2 * e
        c.capa({"tipo": "rot", "pv": (22, 4), "amp": 6, "vel": 2.6, "fase": 1, "cd": 14})
        c.forma([(16, 2), (44 * sx, -6 * sx - 2), (70 * sx, 8), (64 * sx, 30), (50 * sx, 40), (40 * sx, 32), (26, 44), (20, 30)], MEM)
        c.linea([(24, 14), (56 * sx, 18)], 1.4, MEMD)
        c.linea([(26, 24), (50 * sx, 32)], 1.4, MEMD)
        if e >= 2:
            c.linea([(30, 4), (50 * sx, -2), (62 * sx, 10)], 1.5, (235, 255, 255))
        if e == 3:
            c.estrella(56 * sx, 10, 5, (255, 250, 200), 0.3, borde=False)
        c.capa({"tipo": "rot", "pv": (-22, 4), "amp": 6, "vel": 2.6, "fase": 2.6, "cd": -14})
        c.forma([(-16, 2), (-44 * sx, -6 * sx - 2), (-70 * sx, 8), (-64 * sx, 30), (-50 * sx, 40), (-40 * sx, 32), (-26, 44), (-20, 30)], MEM)
        c.linea([(-24, 14), (-56 * sx, 18)], 1.4, MEMD)
        c.linea([(-26, 24), (-50 * sx, 32)], 1.4, MEMD)
        if e >= 2:
            c.linea([(-30, 4), (-50 * sx, -2), (-62 * sx, 10)], 1.5, (235, 255, 255))
        if e == 3:
            c.estrella(-56 * sx, 10, 5, (255, 250, 200), 0.3, borde=False)
    # cuerpo
    c.capa()
    c.el(0, 20, 26 + e, 28 + e, PEL)
    c.el(0, 26, 17 + e, 20 + e, VIE, borde=False)
    # patas
    c.el(-13, 46, 9, 6, PELD)
    c.el(13, 46, 9, 6, PELD)
    if e == 0:
        c.el(-22, 18, 6, 9, PELD, ang=0.3)
        c.el(22, 18, 6, 9, PELD, ang=-0.3)
    # orejas
    for sg in (-1, 1):
        c.forma([(sg * 12, -34), (sg * 24, -58 - e * 2), (sg * 34, -34)], PEL, n=6)
        c.forma([(sg * 17, -38), (sg * 24, -52 - e * 2), (sg * 29, -38)], (255, 190, 190), n=6, luz=False, borde=False)
        if e >= 2:
            c.tubo([(sg * 24, -56 - e * 2), (sg * 24, -64 - e * 2)], 2, 1.2, (90, 60, 50), luz=False, borde=False)
    # cabeza
    c.el(0, -14, 31 + e, 28 + e, PEL)
    c.el(0, -2, 24, 17, VIE, luz=False, borde=False)
    if e >= 1:
        c.ma(0, -34 - e, 12, 4, PELD, 140)
    c.br(-12, -32, 10, 4, 140, -0.3)
    c.cara_aqui()
    # nariz y bigotes
    c.forma([(-4, -5), (4, -5), (0, 0)], NARIZ, suave=True, n=4, luz=False)
    for sg in (-1, 1):
        c.linea([(sg * 14, -3), (sg * 28, -6)], 0.9, PELD)
        c.linea([(sg * 14, 0), (sg * 28, 2)], 0.9, PELD)
    if e >= 2:
        # bufanda de hoja
        c.forma([(-26, 6), (0, 14), (26, 6), (22, 14), (0, 20), (-22, 14)], (110, 200, 120), n=5)
        c.forma([(8, 16), (14, 34), (22, 28)], (90, 180, 110), n=4)
    if e == 3:
        c.el(0, -48, 5, 5, (110, 235, 255))
        c.br(-1, -49.5, 2, 1.4, 240)
    return {"ojos": (0, -16, 26, 9.0), "boca": (0, 8, 10), "mej": (0, -6, 48, 6, (255, 140, 160)), "ojo": (70, 40, 30), "pie": 52,
            "sin_boca_normal": False}


def _buho(c, e):
    PL, PLD, VIE = (132, 150, 226), (96, 112, 196), (250, 240, 214)
    DISCO, PICO, PATA = (255, 249, 228), (255, 188, 72), (255, 168, 80)
    C = (130, 235, 255)
    if e == 3:
        c.capa({"tipo": "flot", "amp": 3, "vel": 1.5})
        c.ma(0, 0, 86, 66, (170, 205, 255), 60)
        for i, (x, y) in enumerate(((-74, -30), (78, -20), (-70, 34), (72, 42))):
            c.linea([(x - 8, y), (x, y - 5), (x + 8, y), (x + 3, y + 5)], 1.8, (225, 240, 255))
    # alas
    wl = 1 + 0.22 * e
    for sg in (-1, 1):
        c.capa({"tipo": "rot", "pv": (sg * 24, -2), "amp": 7, "vel": 2.5, "fase": sg * 0.8, "cd": sg * 10})
        pts = [(sg * 22, -4), (sg * 40 * wl, -2), (sg * 52 * wl, 20), (sg * 46 * wl, 46 + 6 * e), (sg * 34, 38), (sg * 22, 30)]
        c.forma(pts, PLD)
        for k in range(2 + (e >= 1) + (e >= 3)):
            xx = sg * (30 + k * 7 * wl)
            c.linea([(xx, 22 + k * 2), (xx + sg * 2, 33 + k)], 1.3, aclarar(PLD, .3))
        if e == 3:
            c.ma(sg * 44 * wl, 42 + 6 * e, 6, 5, C, 180)
    # cola
    c.capa()
    if e >= 1:
        c.forma([(-12, 38), (-14, 54 + 2 * e), (0, 50 + 2 * e), (14, 54 + 2 * e), (12, 38)], PLD, n=5)
    # cuerpo
    c.el(0, 14, 30 + 1.5 * e, 38 + 1.5 * e, PL)
    c.el(0, 22, 21 + e, 28 + e, VIE, borde=False)
    # plumitas del pecho (escamas)
    filas = 2 + e
    for r in range(filas):
        for k in range(3):
            x = (k - 1) * 11 + (r % 2) * 5 - 2.5
            y = 8 + r * 9
            c.linea([(x - 4, y), (x, y + 3.5), (x + 4, y)], 1.3, (205, 190, 160))
    # patas
    for sg in (-1, 1):
        for k in (-1, 0, 1):
            c.tr([(sg * 11, 50), (sg * 11 + k * 4, 54)], 2.6, PATA)
        c.el(sg * 11, 50, 4.5, 3, PATA, borde=False)
    # orejas / penachos
    for sg in (-1, 1):
        h = 6 + 5 * e if e >= 1 else 3
        c.forma([(sg * 14, -34), (sg * (24 + 3 * e), -40 - h), (sg * 30, -26)], PL, n=5)
        if e >= 2:
            c.forma([(sg * 19, -34), (sg * 24, -44 - h), (sg * 27, -30)], aclarar(PL, .35), n=5, luz=False, borde=False)
    # cabeza
    c.el(0, -14, 33 + e, 28 + e, PL)
    # disco facial
    c.el(-12, -14, 15, 15, DISCO, borde=False)
    c.el(12, -14, 15, 15, DISCO, borde=False)
    c.el(0, -8, 11, 10, DISCO, luz=False, borde=False)
    c.br(-14, -32, 10, 3.5, 130, -0.3)
    if e == 3:
        c.estrella(0, -40, 5, (150, 245, 255), 0.0, borde=False)
        c.ma(0, -40, 9, 8, C, 120)
    c.cara_aqui()
    # pico
    c.forma([(-5, -12), (5, -12), (0, -1)], PICO, n=4, luz=False)
    return {"ojos": (0, -16, 26, 10.5 if e == 0 else 10.0), "boca": (0, 2, 9), "mej": (0, -4, 52, 5.5, (255, 160, 170)), "ojo": (60, 40, 30), "pie": 56}


_CONSTRUCTORES = {"delfin": _delfin, "tortuga": _tortuga, "pulpo": _pulpo, "mariposa": _mariposa, "ardilla": _ardilla, "buho": _buho}


def _hacer(esp):
    def fn(p, etapa, cx, cy, escala=1.0, t=0.0, estado="normal", dir=1, silueta=False):
        _dibujar(esp, p, etapa, cx, cy, escala, t, estado, dir, silueta)
    fn.__name__ = "dibujar_" + esp
    return fn


DIBUJOS = {esp: _hacer(esp) for esp in _CONSTRUCTORES}
