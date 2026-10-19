"""Murales del mundo 2 de las Ruinas (NORDICO): Ratatosk, Cuervo Hugin, Sleipnir, Fenrir, Troll y Jormungandr.
Relieves de arenisca con runas y nudos. Solo dibujo procedural con la clase _L (sin archivos ni azar)."""
import math

import arte_mitos_base as B

NOMBRES = ['Ratatosk', 'Cuervo Hugin', 'Sleipnir', 'Fenrir', 'Troll', 'Jörmungandr']

PI = math.pi
_cos, _sin = math.cos, math.sin


def _rad(d):
    return d * PI / 180.0


# ------------------------------------------------------------------ runas (segmentos en caja x -.4..+.4, y -1..+1)
_RUNAS = [
    [[(-.4, -1), (-.4, 1)], [(-.4, -.3), (.4, -.9)], [(-.4, .2), (.4, -.4)]],          # fehu
    [[(-.4, 1), (-.4, -1), (.4, -.4), (.4, 1)]],                                          # uruz
    [[(-.4, -1), (-.4, 1)], [(-.4, -.5), (.4, 0), (-.4, .5)]],                            # thurisaz
    [[(-.4, -1), (-.4, 1)], [(-.4, -1), (.4, -.4)], [(-.4, -.3), (.4, .3)]],              # ansuz
    [[(-.4, -1), (-.4, 1)], [(-.4, -1), (.4, -.5), (-.4, 0), (.4, 1)]],                   # raido
    [[(.4, -.8), (-.3, 0), (.4, .8)]],                                                    # kenaz
    [[(-.4, -.9), (.4, .9)], [(.4, -.9), (-.4, .9)]],                                     # gebo
    [[(-.4, -1), (-.4, 1)], [(-.4, -1), (.4, -.5), (-.4, 0)]],                            # wunjo
    [[(-.4, -1), (-.4, 1)], [(.4, -1), (.4, 1)], [(-.4, -.4), (.4, .4)]],                 # hagalaz
    [[(0, -1), (0, 1)], [(-.4, -.3), (.4, .3)]],                                          # nauthiz
    [[(.4, -1), (-.4, -.3), (.4, .3), (-.4, 1)]],                                         # sowilo
    [[(0, -1), (0, 1)], [(-.4, -.4), (0, -1), (.4, -.4)]],                                # tiwaz
    [[(-.4, -1), (-.4, 1)], [(-.4, -1), (.3, -.5), (-.4, 0), (.3, .5), (-.4, 1)]],        # berkano
    [[(0, -1), (0, 1)], [(0, 0), (-.4, -.7)], [(0, 0), (.4, -.7)]],                       # algiz
    [[(0, -.9), (.4, 0), (0, .9), (-.4, 0), (0, -.9)]],                                   # inguz
    [[(-.4, -.9), (-.4, .9), (.4, -.9), (.4, .9), (-.4, -.9)]],                           # dagaz
    [[(-.2, -1), (-.2, 1)], [(-.2, -1), (.4, -.5)]],                                      # laguz
    [[(0, -1), (0, 1)], [(0, -1), (.4, -.5), (0, 0)]],                                    # perthro suave
]


def _runa(L, i, x, y, h, ang=0.0, w=2):
    """Dibuja la runa i (lineas) centrada en (x, y), de alto 2h, girada ang."""
    ca, sa = _cos(ang), _sin(ang)
    for seg in _RUNAS[i % len(_RUNAS)]:
        L.lin([(x + (px * ca - py * sa) * h, y + (px * sa + py * ca) * h) for px, py in seg], w)


def _copo(L, x, y, r, w=1.5):
    """Copo de nieve / estrella de seis puntas con lineas."""
    for k in range(3):
        a = k * PI / 3 + .3
        L.lin([(x - r * _cos(a), y - r * _sin(a)), (x + r * _cos(a), y + r * _sin(a))], w)


def _estrella(L, x, y, r):
    L.pol([(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28),
           (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)])


def _recta(x0, y0, x1, y1, n=40):
    return [(x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n) for j in range(n + 1)]


def _ojo(L, x, y, r, mx=0.0, my=0.0):
    """Ojo amable: blanco, pupila oscura y brillo."""
    L.circ(x, y, r)
    L.alto(0)
    L.circ(x + mx * r * .25, y + my * r * .25, r * .62)
    L.hondo(2)
    L.circ(x + mx * r * .25 - r * .18, y + my * r * .25 - r * .2, r * .2)
    L.alto(0)


def _cinta(pts, ws, n=6):
    """Cinta de ancho variable alrededor de una curva suave. Devuelve (poligono, info) con info = [(x, y, tx, ty, w)]."""
    c = B.curva(pts, n)
    m = len(c)
    info, izq, der = [], [], []
    for i, (x, y) in enumerate(c):
        a, b = c[max(i - 1, 0)], c[min(i + 1, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1.0
        tx, ty = dx / l, dy / l
        t = i / (m - 1) * (len(ws) - 1)
        j = min(int(t), len(ws) - 2)
        f = t - j
        w = ws[j] * (1 - f) + ws[j + 1] * f
        info.append((x, y, tx, ty, w))
        izq.append((x - ty * w, y + tx * w))
        der.append((x + ty * w, y - tx * w))
    return izq + der[::-1], info


def _chev(L, info, paso, desde=1, f=.8, adel=.05, off=0.0, hasta=None):
    """Chevrones (plumas, pelo, escamas) cruzando una cinta."""
    for i in range(desde, (hasta or len(info)) - 1, paso):
        x, y, tx, ty, w = info[i]
        nx, ny = -ty, tx
        cx, cy = x + nx * off * w, y + ny * off * w
        L.lin([(cx + nx * w * f - tx * .03, cy + ny * w * f - ty * .03), (cx + tx * adel, cy + ty * adel),
               (cx - nx * w * f - tx * .03, cy - ny * w * f - ty * .03)], 1.5)


def _trenza(L, c, amp, ciclos, w=3, tono=1):
    """Trenza de dos hebras sobre una polilinea densa c."""
    m = len(c)
    A, Bs = [], []
    for i, (x, y) in enumerate(c):
        a, b = c[max(i - 1, 0)], c[min(i + 1, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / l, dx / l
        s = _sin(2 * PI * ciclos * i / (m - 1)) * amp
        A.append((x + nx * s, y + ny * s))
        Bs.append((x - nx * s, y - ny * s))
    L.lin(A, w)
    L.lin(Bs, w)
    L.alto(tono)
    d = max(2, int((m - 1) / (ciclos * 6)))
    for k in range(int(2 * ciclos) + 1):
        i0 = int(k / (2.0 * ciclos) * (m - 1))
        lo, hi = max(0, i0 - d), min(m - 1, i0 + d)
        if hi - lo < 2:
            continue
        L.lin((A if k % 2 == 0 else Bs)[lo:hi + 1], w)
        L.alto(tono if tono == 0 else 0)


def _pluma(L, x, y, ang, largo, ancho, tono, nervio=True):
    L.pol(B.hoja(x, y, ang, largo, ancho))
    L.alto(tono)
    if nervio:
        L.lin([(x + _cos(ang) * largo * .1, y + _sin(ang) * largo * .1),
               (x + _cos(ang) * largo * .88, y + _sin(ang) * largo * .88)], 1.5)
        L.hondo(2, .9)


def _musgo(L, x, y, r):
    for dx, dy, q in ((0, 0, 1), (-.8, .2, .75), (.8, .25, .75), (-.35, -.5, .7), (.4, -.45, .7)):
        L.circ(x + dx * r, y + dy * r, r * .5 * q)
    L.alto(0)
    for dx, dy in ((-.3, 0), (.35, .1), (0, -.35)):
        L.circ(x + dx * r, y + dy * r, r * .09)
    L.hondo(2)


# ================================================================== 0. Ratatosk
def _m_ratatosk(L):
    # runas y copos al fondo
    for k, (x, y) in enumerate(((.78, -.62), (.9, -.2), (.82, .2), (-.9, -.55), (-.5, .9), (.5, -.9))):
        _runa(L, k * 3 + 1, x, y, .075, 0, 2)
    L.hondo(2, .8)
    for (x, y, r) in ((.68, -.82, .06), (-.88, .0, .05), (.9, .62, .05), (-.15, .93, .05)):
        _copo(L, x, y, r)
    L.hondo(2, .8)
    # rama
    rama, inf = _cinta([(-1.0, .88), (-.45, .78), (.3, .70), (1.0, .52)], [.09, .1, .09, .06])
    L.pol(rama)
    L.alto(2)
    for i in range(3, len(inf) - 2, 4):
        x, y, tx, ty, w = inf[i]
        L.lin([(x, y - w * .6), (x + .02, y + w * .55)], 1.5)
    L.hondo(2)
    # hojas y bellotas en la rama
    for (x, y, a) in ((.62, .58, -80), (.7, .6, -30), (-.78, .78, -120), (-.7, .76, -160)):
        _pluma(L, x, y, _rad(a), .24, .075, 0)
    # cola enorme
    cola, ic = _cinta([(-.22, .52), (-.52, .42), (-.7, .1), (-.62, -.3), (-.38, -.62), (-.05, -.78), (.2, -.72), (.3, -.55)],
                      [.07, .13, .2, .22, .22, .19, .11, .05])
    L.pol(cola)
    L.alto(1)
    c2, _ = _cinta([(-.24, .5), (-.5, .4), (-.66, .1), (-.58, -.3), (-.36, -.6), (-.05, -.74), (.18, -.7)],
                   [.04, .08, .12, .13, .13, .1, .05])
    L.pol(c2)
    L.alto(0)
    _chev(L, ic, 3, 3, .85, .06)
    _chev(L, ic, 3, 4, .85, .06, hasta=len(ic) - 8)
    L.hondo(2, .9)
    # cuerpo
    L.pol(B.elipse(-.05, .22, .27, .38, .22, 28))
    L.alto(1)
    L.pol(B.elipse(.08, .26, .15, .27, .22, 24))
    L.alto(0)
    for q in range(5):
        y = .02 + q * .1
        L.lin([(.0 + q * .01, y), (.07 + q * .01, y + .04), (.14 + q * .01, y)], 1.5)
    L.hondo(2, .8)
    # pata trasera y pie
    L.elip(-.14, .4, .17, .14)
    L.alto(0)
    L.lin(B.arco(-.14, .4, .1, .08, _rad(200), _rad(340), 6), 1.5)
    L.hondo(2)
    L.elip(.08, .55, .2, .06)
    L.alto(1)
    for q in range(3):
        L.lin([(.17 + q * .04, .52), (.19 + q * .04, .58)], 1.5)
    L.hondo(2)
    # cabeza
    for (pts) in ([(.07, -.3), (.05, -.57), (.2, -.38)], [(.24, -.38), (.32, -.6), (.4, -.34)]):
        L.pol(pts)
    L.alto(1)
    L.lin([(.07, -.38), (.07, -.5)], 2)
    L.lin([(.3, -.43), (.33, -.54)], 2)
    L.hondo(2)
    L.elip(.22, -.2, .24, .21)
    L.alto(1)
    L.elip(.43, -.14, .12, .085)
    L.alto(0)
    L.circ(.53, -.17, .032)
    L.alto(2)
    L.lin([(.38, -.09), (.45, -.06), (.52, -.09)], 2)
    L.hondo(2)
    L.rect(.46, -.045, .016, .028)
    L.alto(0)
    _ojo(L, .3, -.27, .055, .6, .1)
    for q in range(3):
        L.lin([(.1 + q * .02, -.12 + q * .03), (.16 + q * .02, -.1 + q * .03)], 1.5)
    L.hondo(2)
    # bellota grande entre las manitas
    L.elip(.52, .2, .11, .15)
    L.alto(0)
    L.elip(.52, .07, .13, .08)
    L.alto(2)
    for q in range(-3, 4):
        L.lin([(.52 + q * .035, .0), (.52 + q * .028, .14)], 1.5)
    L.lin([(.4, .06), (.64, .06)], 1.5)
    L.lin([(.4, .1), (.64, .1)], 1.5)
    L.hondo(2)
    L.lin([(.52, -.01), (.55, -.1)], 3)
    L.alto(2)
    L.lin([(.2, 0), (.34, .06), (.4, .16)], 8)
    L.alto(1)
    L.circ(.4, .17, .045)
    L.circ(.65, .2, .045)
    L.alto(0)


# ================================================================== 1. Cuervo Hugin
def _ala(L, S, W, ang0, ang1, largo0, largo1, ancho, tono, tono_cob):
    """Ala de ave: plumas de vuelo que salen del brazo S->W (hacia atras) y banda de coberteras."""
    n = 9
    for q in range(n):
        t = .12 + .88 * q / (n - 1)
        bx, by = S[0] + (W[0] - S[0]) * t, S[1] + (W[1] - S[1]) * t
        a = _rad(ang0 + (ang1 - ang0) * q / (n - 1))
        lg = largo0 + (largo1 - largo0) * q / (n - 1)
        _pluma(L, bx, by, a, lg, ancho, tono)
    for q in range(7):
        t = .1 + .9 * q / 6
        bx, by = S[0] + (W[0] - S[0]) * t, S[1] + (W[1] - S[1]) * t
        a = _rad(ang0 + (ang1 - ang0) * q / 6 + 4)
        _pluma(L, bx, by, a, (largo0 + (largo1 - largo0) * q / 6) * .55, ancho * .9, tono_cob)
    poli, inf = _cinta([S, ((S[0] + W[0]) / 2 - .03, (S[1] + W[1]) / 2), W], [.07, .06, .04])
    L.pol(poli)
    L.alto(tono_cob)


def _m_hugin(L):
    # anillo de runas
    for a in B.radios(24, .1, .72, .13):
        L.lin(a, 1.5)
    L.hondo(2, .5)
    L.circ(0, 0, .95, 3)
    L.circ(0, 0, .72, 3)
    L.hondo(2)
    n = 16
    for j in range(n):
        th = 2 * PI * j / n
        _runa(L, j, .835 * _cos(th), .835 * _sin(th), .07, th + PI / 2, 2)
    L.hondo(2)
    for j in range(n):
        th = 2 * PI * (j + .5) / n
        L.circ(.835 * _cos(th), .835 * _sin(th), .014)
    L.alto(0)
    # ala lejana (arriba), tras la cabeza
    _ala(L, (.14, -.1), (.12, -.78), 185, 150, .55, .5, .06, 2, 1)
    # cola larga en cuna
    for a in (150, 160, 170, 180, 190):
        _pluma(L, -.4, .22, _rad(a), .55, .065, 2)
    # patas
    for sx in (-.04, .1):
        L.lin([(sx, .22), (sx + .01, .44)], 5)
        for a in (-.5, 0, .5):
            L.lin([(sx + .01, .44), (sx + .01 + .1 * _sin(a) + .06, .52 + abs(a) * .02)], 3)
    L.alto(2)
    # cuerpo esbelto
    L.pol(B.elipse(-.02, .06, .5, .17, -.38, 28))
    L.alto(1)
    for q in range(-4, 5):
        cx = q * .095
        pts = B.rotar([(cx - .03, -.1), (cx + .04, 0), (cx - .03, .1)], -.38, -.02, .06)
        L.lin(pts, 1.5)
    L.hondo(2, .9)
    # ala cercana
    _ala(L, (.04, -.04), (-.34, -.62), 178, 120, .62, .72, .085, 2, 1)
    for q in range(3):
        for col in range(5):
            x, y = -.2 + col * .06 + q * .03, -.1 - col * .09 + q * .07 + .05
            L.lin(B.arco(x, y, .035, .035, _rad(15), _rad(165), 6), 1.5)
    L.hondo(2, .9)
    # cabeza y pico
    L.pol([(.3, -.05), (.34, .07), (.4, -.05)])
    L.pol([(.36, -.06), (.42, .04), (.48, -.08)])
    L.alto(1)
    L.circ(.37, -.2, .15)
    L.alto(1)
    L.pol([(.46, -.33), (.78, -.19), (.72, -.13), (.46, -.07)])
    L.alto(2)
    L.lin([(.5, -.2), (.74, -.17)], 2)
    L.lin([(.55, -.28), (.57, -.24)], 2)
    L.hondo(2)
    _ojo(L, .4, -.24, .04, .5, 0)
    L.lin([(.34, -.3), (.42, -.31)], 2)
    L.lin([(.25, -.26), (.22, -.17)], 1.5)
    L.hondo(2)
    # runas sueltas
    _runa(L, 4, -.45, .52, .075, .1)
    _runa(L, 11, .4, .46, .075, -.1)
    L.hondo(2, .8)


# ================================================================== 2. Sleipnir
def _pata(L, pts, tono):
    poli, inf = _cinta(pts, [.075, .05, .036, .042], 5)
    L.pol(poli)
    L.alto(tono)
    x, y, tx, ty, w = inf[-1]
    L.pol([(x - .045, y - .02), (x + .05, y - .02), (x + .06, y + .035), (x - .055, y + .035)])
    L.alto(2)
    i = int(len(inf) * .8)
    x, y, tx, ty, w = inf[i]
    L.lin([(x - ty * w, y + tx * w), (x + ty * w, y - tx * w)], 2)
    L.hondo(2)


def _m_sleipnir(L):
    # nubes / viento y runas
    for k, (x, y) in enumerate(((-.8, -.62), (-.45, -.8), (.0, -.9), (.45, -.84))):
        _runa(L, k * 4 + 2, x, y, .06, 0)
    L.hondo(2, .8)
    for (y, x0, x1) in ((.78, -.8, .8), (.86, -.55, .55)):
        L.lin(B.ondas(x0, y, x1, y, .02, 7), 2)
    L.hondo(2, .8)
    # ocho patas: delanteras y traseras
    delanteras = [[(.3, .06), (.46, .24), (.64, .36), (.72, .56)],
                  [(.3, .06), (.42, .3), (.52, .46), (.52, .64)],
                  [(.3, .06), (.32, .3), (.24, .46), (.3, .64)],
                  [(.3, .06), (.22, .26), (.08, .42), (.08, .62)]]
    traseras = [[(-.38, .04), (-.22, .26), (-.1, .42), (-.12, .62)],
                [(-.38, .04), (-.4, .28), (-.3, .46), (-.34, .64)],
                [(-.38, .04), (-.52, .26), (-.52, .46), (-.6, .62)],
                [(-.38, .04), (-.62, .2), (-.72, .36), (-.82, .52)]]
    for q in (3, 1, 2, 0):
        _pata(L, delanteras[q], 2 if q % 2 else 1)
    for q in (3, 1, 2, 0):
        _pata(L, traseras[q], 2 if q % 2 else 1)
    # cola
    cola, ic = _cinta([(-.52, -.14), (-.7, -.22), (-.86, -.34), (-.94, -.18), (-.86, .0), (-.8, .12)], [.05, .09, .1, .08, .05, .02])
    L.pol(cola)
    L.alto(2)
    for k in (2, 3, 4):
        L.lin([(p[0], p[1]) for p in ic[k * 5:k * 5 + 5]], 1.5)
    L.hondo(1)
    # cuerpo, cuello y cabeza
    cuerpo = B.curva([(-.5, -.2), (-.3, -.3), (0, -.3), (.25, -.28), (.4, -.42), (.5, -.62), (.58, -.74), (.7, -.76), (.84, -.66),
                      (.92, -.54), (.9, -.46), (.8, -.48), (.68, -.5), (.56, -.44), (.46, -.3), (.4, -.1), (.34, .08),
                      (.1, .14), (-.2, .14), (-.4, .1), (-.52, -.02)], 5, True)
    # crin
    for q in range(8):
        t = q / 7
        x = .36 + t * .2
        y = -.4 - t * .36
        _pluma(L, x, y, _rad(200 + (1 - t) * 20 - t * 25), .22 - t * .03, .05, 2, False)
    L.pol(cuerpo)
    L.alto(0)
    # manta de silla con runas
    L.pol([(-.22, -.3), (.1, -.3), (.14, .0), (-.24, .02)])
    L.alto(1)
    L.lin([(-.2, -.26), (.08, -.26), (.11, -.03), (-.21, -.01), (-.2, -.26)], 1.5)
    L.hondo(2)
    for k in range(3):
        _runa(L, [0, 3, 8][k], -.14 + k * .09, -.14, .06)
    L.hondo(2)
    # trenza en la barriga
    _trenza(L, _recta(-.44, .045, .3, .07, 60), .03, 9, 3, 1)
    # espirales en anca y hombro
    for (cx, cy) in ((-.4, -.12), (.28, -.1)):
        L.lin([(cx + (.015 + .075 * t / 26) * _cos(t / 26 * 5 * PI), cy + (.015 + .075 * t / 26) * _sin(t / 26 * 5 * PI)) for t in range(27)], 2)
    L.hondo(2)
    # puntos decorativos en el cuello
    for k in range(5):
        L.circ(.45 + k * .02, -.32 - k * .1, .018)
    L.alto(1)
    # oreja, ojo, nariz, brida
    L.pol([(.56, -.72), (.55, -.9), (.65, -.75)])
    L.alto(2)
    _ojo(L, .72, -.63, .04, .5, 0)
    L.circ(.89, -.52, .014)
    L.lin([(.86, -.5), (.92, -.5)], 1.5)
    L.hondo(2)
    L.lin([(.6, -.72), (.72, -.52), (.82, -.5)], 2)
    L.lin([(.64, -.52), (.78, -.6)], 2)
    L.alto(2)
    L.circ(.72, -.52, .025)
    L.alto(0)


# ================================================================== 3. Fenrir
def _m_fenrir(L):
    # rayos y luna
    for a in B.radios(28, .6, .76, .1):
        L.lin(B.mover(a, .15, -.35), 2)
    L.hondo(2, .7)
    for (x, y, r) in ((-.8, -.6, .06), (-.55, -.85, .045), (.9, -.72, .05), (.85, -.15, .04), (-.88, -.1, .04)):
        _estrella(L, x, y, r)
    L.alto(0)
    L.circ(.15, -.35, .56)
    L.alto(0)
    L.circ(.15, -.35, .5, 2)
    L.hondo(2, .6)
    for (x, y, r) in ((.4, -.55, .09), (.35, -.25, .06), (.0, -.15, .1), (.2, -.62, .045), (.5, -.3, .04), (-.1, -.5, .05)):
        L.circ(x, y, r)
        L.circ(x, y, r * .55, 2)
    L.hondo(2, .6)
    # cola
    cola, ic = _cinta([(-.72, .72), (-.88, .6), (-.92, .38), (-.86, .22)], [.1, .13, .1, .03])
    L.pol(cola)
    L.alto(1)
    _chev(L, ic, 3, 2, .8, .05)
    L.hondo(2)
    # cuerpo
    cuerpo = B.curva([(-.16, -.36), (-.3, -.2), (-.5, 0), (-.68, .25), (-.78, .55), (-.72, .8), (-.2, .82), (.3, .82), (.4, .55),
                      (.34, .3), (.26, .1), (.22, -.1), (.18, -.3)], 5, True)
    L.pol(cuerpo)
    L.alto(1)
    # pelaje en mechones solapados
    for fila in range(6):
        for col in range(5):
            x = -.58 + col * .15 + (.075 if fila % 2 else 0)
            y = -.12 + fila * .12
            if fila < 2 and x < -.3 or x > .1 + fila * .01 and fila < 5 and x > .2:
                continue
            _pluma(L, x, y, _rad(98), .17, .05, 0, False)
    L.hondo(2, .7)
    # gola del pecho
    for q in range(9):
        t = q / 8
        x = .2 + t * .2
        y = -.18 + t * .72
        _pluma(L, x, y, _rad(78 + t * 20), .2, .055, 0, False)
    L.hondo(2, .6)
    # anca con espiral
    L.elip(-.5, .56, .26, .25)
    L.alto(0)
    L.lin([(-.5 + (.02 + .15 * t / 30) * _cos(t / 30 * 5 * PI), .56 + (.02 + .15 * t / 30) * _sin(t / 30 * 5 * PI)) for t in range(31)], 2)
    L.hondo(2)
    # patas
    L.pol([(.1, .3), (.36, .3), (.38, .82), (.1, .82)])
    L.alto(1)
    for q in range(4):
        L.lin([(.14, .38 + q * .1), (.2, .44 + q * .1), (.26, .38 + q * .1)], 1.5)
    L.hondo(2)
    L.elip(.27, .84, .17, .07)
    L.alto(0)
    L.elip(-.35, .85, .2, .07)
    L.alto(0)
    for q in range(3):
        L.lin([(.2 + q * .06, .81), (.21 + q * .06, .88)], 1.5)
        L.lin([(-.45 + q * .07, .82), (-.44 + q * .07, .9)], 1.5)
    L.hondo(2)
    # cabeza aullando
    ang = _rad(-42)
    ox, oy = -.1, -.36
    ES = 1.3

    def T(pts):
        return B.rotar(B.escalar(pts, ES), ang, ox, oy)
    L.pol(T([(.12, .06), (.46, .06), (.46, .2), (.1, .17)]))
    L.hondo(2, 1)
    L.pol(T([(.08, .08), (.3, .12), (.46, .2), (.44, .27), (.28, .26), (.1, .21), (.0, .16)]))
    L.alto(1)
    for (ore) in ([(-.08, -.17), (-.1, -.34), (.04, -.2)], [(-.2, -.1), (-.26, -.26), (-.12, -.18)]):
        L.pol(T(ore))
    L.alto(1)
    L.pol(T([(-.1, -.2), (-.1, -.3), (0, -.21)]))
    L.hondo(2, .8)
    L.pol(T([(-.2, -.1), (-.08, -.2), (.06, -.17), (.16, -.1), (.36, -.08), (.5, -.06), (.54, 0), (.5, .04), (.3, .05),
             (.12, .07), (.0, .16), (-.14, .22), (-.24, .1)]))
    L.alto(1)
    # mechones de la mejilla
    for q in range(4):
        L.pol(T([(-.2 + q * .06, .14 + q * .015), (-.1 + q * .06, .27), (-.12 + q * .06, .1)]))
    L.alto(0)
    L.circ(*T([(.52, -.01)])[0], .026)
    L.alto(2)
    for (x, y) in ((.2, .075), (.34, .06), (.44, .05)):
        L.pol(T([(x - .018, y), (x + .018, y), (x, y + .05)]))
    L.alto(0)
    ex, ey = T([(.1, -.06)])[0]
    _ojo(L, ex, ey, .045, .3, -.6)
    L.lin(T([(.02, -.1), (.1, -.13), (.17, -.1)]), 2)
    for q in range(3):
        L.lin(T([(.3 + q * .05, -.03), (.34 + q * .05, -.01)]), 1.5)
    L.hondo(2)
    # roca
    L.elip(0, .94, .85, .13)
    L.alto(2)
    for k in range(8):
        L.lin([(-.7 + k * .2, .94), (-.66 + k * .2, .9)], 1.5)
    L.hondo(2)


# ================================================================== 4. Troll
def _m_troll(L):
    # runas de fondo
    for k, (x, y) in enumerate(((-.85, -.55), (.85, -.55), (-.88, .0), (.88, .0))):
        _runa(L, k * 5 + 3, x, y, .08)
    L.hondo(2, .8)
    # piernas / pies
    for sx in (-1, 1):
        L.pol([(sx * .12, .62), (sx * .4, .62), (sx * .42, .82), (sx * .1, .82)])
    L.alto(2)
    for sx in (-1, 1):
        L.elip(sx * .27, .84, .22, .09)
    L.alto(1)
    for sx in (-1, 1):
        for q in range(3):
            L.lin([(sx * (.14 + q * .12), .8), (sx * (.15 + q * .12), .89)], 1.5)
    L.hondo(2)
    # torso
    torso = B.curva([(-.3, -.16), (-.5, -.12), (-.62, .05), (-.66, .32), (-.6, .55), (-.45, .72), (-.2, .78), (.2, .78),
                     (.45, .72), (.6, .55), (.66, .32), (.62, .05), (.5, -.12), (.3, -.16)], 5, True)
    L.pol(torso)
    L.alto(1)
    # pectorales y grietas
    L.lin(B.arco(-.22, .08, .22, .18, _rad(10), _rad(170), 8), 2)
    L.lin(B.arco(.22, .08, .22, .18, _rad(10), _rad(170), 8), 2)
    L.lin([(-.44, .22), (-.38, .3), (-.46, .38), (-.4, .44)], 1.5)
    L.lin([(.44, .2), (.5, .3), (.42, .36)], 1.5)
    for q in range(4):
        L.lin([(-.07 + q * .05, .3), (-.03 + q * .05, .38)], 1.5)
    L.hondo(2)
    # piedras incrustadas
    L.pol([(-.5, .0), (-.38, -.06), (-.3, .04), (-.36, .14), (-.48, .12)])
    L.pol([(.34, .26), (.46, .2), (.54, .3), (.46, .4), (.36, .36)])
    L.alto(2)
    L.lin([(-.38, -.06), (-.4, .06), (-.48, .12)], 1.5)
    L.lin([(.46, .2), (.45, .32), (.36, .36)], 1.5)
    L.hondo(2)
    # collar de piedras
    for k in range(7):
        a = _rad(25 + k * 21.7)
        L.circ(.4 * _cos(a), -.13 + .26 * _sin(a), .028)
    L.alto(2)
    L.pol([(0, .22), (.06, .3), (0, .4), (-.06, .3)])
    L.alto(0)
    # cinturon con hebilla rúnica y taparrabos
    L.pol([(-.4, .5), (.4, .5), (.3, .74), (0, .82), (-.3, .74)])
    L.alto(0)
    L.lin([(-.34, .55), (.34, .55), (.25, .72), (0, .78), (-.25, .72), (-.34, .55)], 1.5)
    for k in range(3):
        _runa(L, [5, 9, 13][k], -.14 + k * .14, .65, .05)
    L.hondo(2)
    L.rect(0, .5, .62, .06)
    L.alto(2)
    L.rect(0, .5, .09, .09)
    L.alto(0)
    _runa(L, 8, 0, .5, .055)
    L.hondo(2)
    # brazos
    for sx in (-1, 1):
        brazo, ib = _cinta([(sx * .56, -.04), (sx * .74, .22), (sx * .72, .46)], [.15, .19, .15])
        L.pol(brazo)
    L.alto(1)
    for sx in (-1, 1):
        for q in range(3):
            L.lin([(sx * (.58 + q * .05), .06 + q * .13), (sx * (.7 + q * .02), .1 + q * .13)], 1.5)
    L.hondo(2)
    for sx in (-1, 1):
        L.circ(sx * .72, .58, .15)
    L.alto(0)
    for sx in (-1, 1):
        for q in range(3):
            L.lin([(sx * (.66 + q * .06), .52), (sx * (.66 + q * .06), .6)], 1.5)
    L.hondo(2)
    # florecita en la mano
    L.lin([(.72, .5), (.74, .34)], 2)
    L.alto(1)
    for k in range(5):
        a = _rad(-90 + k * 72)
        L.circ(.74 + .04 * _cos(a), .3 + .04 * _sin(a), .028)
    L.alto(0)
    L.circ(.74, .3, .02)
    L.alto(2)
    # musgo en hombros
    _musgo(L, -.52, -.12, .11)
    _musgo(L, .54, -.1, .1)
    _musgo(L, -.38, .66, .07)
    # orejas
    for sx in (-1, 1):
        L.pol(B.curva([(sx * .26, -.44), (sx * .44, -.6), (sx * .66, -.74), (sx * .76, -.6), (sx * .68, -.4), (sx * .5, -.28),
                       (sx * .28, -.28)], 5, True))
    L.alto(1)
    for sx in (-1, 1):
        L.lin(B.curva([(sx * .34, -.44), (sx * .5, -.54), (sx * .64, -.6), (sx * .6, -.45), (sx * .48, -.37)], 4), 2)
        L.circ(sx * .7, -.58, .02)
    L.hondo(2)
    # pelo de musgo / hierba en la cabeza
    for k in range(7):
        _pluma(L, -.2 + k * .067, -.72, _rad(-90 + (k - 3) * 22), .2, .045, 0, False)
    L.hondo(2, .5)
    # cabeza
    L.elip(0, -.44, .35, .35)
    L.alto(1)
    L.circ(-.2, -.7, .025)
    L.circ(.25, -.66, .02)
    L.hondo(2)
    L.lin(B.arco(0, -.5, .26, .12, _rad(200), _rad(340), 8), 2)
    L.hondo(2)
    for sx in (-1, 1):
        L.pol([(sx * .06, -.58), (sx * .24, -.62), (sx * .26, -.54), (sx * .06, -.52)])
    L.alto(2)
    for sx in (-1, 1):
        _ojo(L, sx * .15, -.5, .055, -sx * .3, .2)
    # nariz enorme
    L.elip(0, -.36, .14, .17)
    L.alto(0)
    L.circ(-.075, -.28, .028)
    L.circ(.075, -.28, .028)
    L.hondo(2)
    L.circ(.06, -.4, .018)
    L.alto(2)
    # sonrisa y colmillos
    L.lin(B.arco(0, -.29, .24, .11, _rad(12), _rad(168), 10), 2.5)
    L.hondo(2)
    for sx in (-1, 1):
        L.pol([(sx * .15 - .03, -.17), (sx * .15 + .03, -.17), (sx * .15, -.27)])
    L.alto(0)
    for sx in (-1, 1):
        L.circ(sx * .24, -.34, .04, 2)
    L.hondo(2, .6)


# ================================================================== 5. Jormungandr
def _m_jormungandr(L):
    R = .58
    th0 = -1.0
    gap = .55
    tot = 2 * PI - gap
    N = 96

    def ang(s):
        return th0 + s * tot

    def ancho(s):
        if s < .2:
            return .02 + .115 * (s / .2) ** .8
        if s > .88:
            return .135 - .03 * (s - .88) / .12
        return .135 + .008 * _sin(s * 30)

    # olas alrededor
    L.circ(0, 0, .96, 3)
    L.hondo(2)
    for j in range(32):
        th = 2 * PI * j / 32
        cx, cy = .83 * _cos(th), .83 * _sin(th)
        L.lin(B.arco(cx, cy, .075, .075, th - PI / 2, th + PI / 2, 8), 2)
    L.hondo(2)
    for j in range(32):
        th = 2 * PI * j / 32
        L.circ(.83 * _cos(th), .83 * _sin(th), .017)
    L.alto(0)
    # globo central con runas
    L.circ(0, 0, .3)
    L.alto(0)
    L.circ(0, 0, .3, 2)
    L.elip(0, 0, .13, .3, 2)
    L.elip(0, 0, .3, .13, 2)
    L.lin([(-.3, 0), (.3, 0)], 2)
    L.lin([(0, -.3), (0, .3)], 2)
    L.hondo(2)
    L.circ(0, 0, .06)
    L.alto(1)
    for j in range(12):
        th = 2 * PI * j / 12
        _runa(L, j + 2, .385 * _cos(th), .385 * _sin(th), .04, th + PI / 2, 1.5)
    L.hondo(2)
    # cuerpo
    ext, inte = [], []
    for j in range(N + 1):
        s = j / N
        a = ang(s)
        w = ancho(s)
        ext.append(((R + w) * _cos(a), (R + w) * _sin(a)))
        inte.append(((R - w) * _cos(a), (R - w) * _sin(a)))
    L.pol(ext + inte[::-1])
    L.alto(1)
    # vientre claro
    v1, v2 = [], []
    for j in range(8, N + 1):
        s = j / N
        a = ang(s)
        w = ancho(s)
        v1.append(((R - w * .45) * _cos(a), (R - w * .45) * _sin(a)))
        v2.append(((R - w) * _cos(a), (R - w) * _sin(a)))
    L.pol(v1 + v2[::-1])
    L.alto(0)
    # escamas en chevrones y rombos del dorso
    M = 52
    for j in range(M):
        s = .07 + j * .92 / M
        a = ang(s)
        w = ancho(s)
        ct, st = _cos(a), _sin(a)
        tx, ty = -st, ct
        nx, ny = ct, st
        us = (-.1, .5) if j % 2 == 0 else (.2, -.4)
        for u in us:
            cx, cy = (R + u * w) * ct, (R + u * w) * st
            h = w * .38
            L.lin([(cx + nx * h - tx * .03, cy + ny * h - ty * .03), (cx + tx * .045, cy + ty * .045),
                   (cx - nx * h - tx * .03, cy - ny * h - ty * .03)], 1.5)
    L.hondo(2, .9)
    for j in range(8, M, 5):
        s = .07 + j * .92 / M
        a = ang(s)
        cx, cy = R * _cos(a), R * _sin(a)
        L.pol(B.rotar([(0, -.06), (.04, 0), (0, .06), (-.04, 0)], a + PI / 2, cx, cy))
    L.alto(0)
    # puas dorsales
    for j in range(12, M, 2):
        s = .07 + j * .92 / M
        a = ang(s)
        w = ancho(s)
        ct, st = _cos(a), _sin(a)
        tx, ty = -st, ct
        bx, by = (R + w) * ct, (R + w) * st
        L.pol([(bx - tx * .028, by - ty * .028), (bx + ct * .075 - tx * .045, by + st * .075 - ty * .045), (bx + tx * .028, by + ty * .028)])
    L.alto(0)
    # cabeza (muerde la punta de la cola)
    ah = ang(1.0)
    P = (R * _cos(ah), R * _sin(ah))
    tx, ty = -_sin(ah), _cos(ah)
    nx, ny = _cos(ah), _sin(ah)

    def H(pts):
        return [(P[0] + tx * x * 1.2 + nx * y * 1.2, P[1] + ty * x * 1.2 + ny * y * 1.2) for x, y in pts]
    L.pol(H([(-.1, .1), (-.2, .24), (-.04, .17)]))
    L.pol(H([(.0, .13), (-.08, .27), (.07, .17)]))
    L.alto(0)
    L.pol(H([(-.1, -.12), (.08, -.15), (.22, -.12), (.34, -.07), (.39, 0), (.34, .07), (.22, .13), (.08, .16), (-.1, .13)]))
    L.alto(1)
    L.lin(H([(.1, 0), (.38, 0)]), 2.5)
    L.hondo(2)
    for x in (.16, .25, .33):
        L.pol(H([(x - .018, -.008), (x + .018, -.008), (x, -.05)]))
        L.pol(H([(x - .018, .008), (x + .018, .008), (x, .05)]))
    L.alto(0)
    ex, ey = H([(.12, .075)])[0]
    _ojo(L, ex, ey, .04, nx * .5 + tx * .4, ny * .5 + ty * .4)
    L.lin(H([(.04, .125), (.12, .125), (.19, .1)]), 2)
    L.circ(*H([(.34, .035)])[0], .012)
    L.hondo(2)
    # bigotes
    L.lin(H([(.34, -.03), (.42, -.12), (.46, -.1)]), 1.5)
    L.hondo(2)


MOTIVOS = [_m_ratatosk, _m_hugin, _m_sleipnir, _m_fenrir, _m_troll, _m_jormungandr]
