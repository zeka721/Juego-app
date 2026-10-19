"""Herramientas de cocina dibujadas con codigo (cursor de los pasos y adornos).

    dibujar_herr(p, nombre, x, y, tam=64, angulo=0.0)

Se dibuja centrada en (x, y) dentro de un cuadro de `tam` px. Posicion natural (angulo 0): la herramienta
esta vertical con el mango arriba y la punta de trabajo ABAJO (rodillo y tazon/plato/olla/jarra en su posicion
normal). `angulo` en grados, giro antihorario (como pygame.transform.rotate). Nunca lanza excepcion.

Nombres: cuchillo, tijera, pelador, rallador, rodillo, tenedor, cuchara, batidor, espatula, salero, cernidor,
molde (estrella | corazon | circulo: "molde", "molde_estrella", "molde_corazon", "molde_circulo"), exprimidor,
sarten, olla, manga, jarra, tazon, plato, guantes.

Tambien exporta pequenos ayudantes de dibujo (c, e, rr, poli, rotar_blit) que usan cocina_ingredientes y
cocina_platos.
"""

import math

import pygame

from nucleo import aclarar, oscurecer

# ----------------------------------------------------------------------------- ayudantes
INK = (70, 55, 60)          # contorno suave


def c(s, col, x, y, r, borde=True, w=2):
    pygame.draw.circle(s, col, (int(x), int(y)), max(1, int(r)))
    if borde:
        pygame.draw.circle(s, oscurecer(col, 0.4) if borde is True else borde, (int(x), int(y)), max(1, int(r)), w)


def e(s, col, x, y, w, h, borde=True, bw=2):
    r = pygame.Rect(int(x - w / 2), int(y - h / 2), max(2, int(w)), max(2, int(h)))
    pygame.draw.ellipse(s, col, r)
    if borde:
        pygame.draw.ellipse(s, oscurecer(col, 0.4) if borde is True else borde, r, bw)


def rr(s, col, x, y, w, h, rad=6, borde=True, bw=2):
    """Rectangulo redondeado centrado en (x, y)."""
    r = pygame.Rect(int(x - w / 2), int(y - h / 2), max(2, int(w)), max(2, int(h)))
    pygame.draw.rect(s, col, r, border_radius=max(0, int(rad)))
    if borde:
        pygame.draw.rect(s, oscurecer(col, 0.4) if borde is True else borde, r, bw, border_radius=max(0, int(rad)))


def poli(s, col, pts, borde=True, bw=2):
    pts = [(int(a), int(b)) for a, b in pts]
    pygame.draw.polygon(s, col, pts)
    if borde:
        pygame.draw.polygon(s, oscurecer(col, 0.4) if borde is True else borde, pts, bw)


def lin(s, col, a, b, w=2):
    pygame.draw.line(s, col, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), max(1, int(w)))


def brillo(s, x, y, r):
    pygame.draw.circle(s, (255, 255, 255), (int(x), int(y)), max(1, int(r)))


def rotar_blit(p, surf, x, y, angulo=0.0):
    if angulo:
        surf = pygame.transform.rotate(surf, angulo)
    p.blit(surf, surf.get_rect(center=(int(x), int(y))))


ACERO = (205, 212, 225)
ACERO_OSC = (140, 150, 170)
MADERA = (214, 160, 96)
ROJO = (235, 85, 80)
AZUL = (95, 160, 235)
VERDE = (110, 195, 100)
AMAR = (250, 205, 70)
ROSA = (245, 140, 175)


# ----------------------------------------------------------------------------- herramientas (centro 0,0 -> cx, cy)
def _cuchillo(s, cx, cy, r):
    poli(s, ACERO, [(cx - r * .18, cy - r * .1), (cx + r * .2, cy - r * .1), (cx + r * .2, cy + r * .55),
                    (cx - r * .02, cy + r * .95)], True)
    lin(s, (245, 248, 255), (cx - r * .08, cy - r * .02), (cx - r * .08, cy + r * .6), max(2, r * .07))
    rr(s, ROJO, cx, cy - r * .55, r * .3, r * .8, r * .12)
    c(s, (250, 235, 200), cx, cy - r * .45, r * .045, False)
    c(s, (250, 235, 200), cx, cy - r * .7, r * .045, False)
    rr(s, ACERO_OSC, cx, cy - r * .12, r * .38, r * .1, 3)


def _tijera(s, cx, cy, r):
    for k, col in ((-1, AZUL), (1, ROSA)):
        poli(s, ACERO, [(cx + k * r * .02, cy - r * .1), (cx - k * r * .22, cy + r * .95), (cx - k * r * .06, cy + r * .95)])
    for k, col in ((-1, AZUL), (1, ROSA)):
        lin(s, oscurecer(col, .3), (cx, cy - r * .1), (cx + k * r * .22, cy - r * .5), max(3, r * .1))
        pygame.draw.circle(s, col, (int(cx + k * r * .3), int(cy - r * .68)), int(r * .27), max(3, int(r * .12)))
        pygame.draw.circle(s, oscurecer(col, .4), (int(cx + k * r * .3), int(cy - r * .68)), int(r * .27), 1)
    c(s, (255, 230, 120), cx, cy - r * .08, r * .09)


def _pelador(s, cx, cy, r):
    rr(s, VERDE, cx, cy - r * .35, r * .26, r * 1.0, r * .13)
    lin(s, aclarar(VERDE, .5), (cx - r * .06, cy - r * .7), (cx - r * .06, cy - r * .1), max(2, r * .05))
    poli(s, ACERO, [(cx - r * .3, cy + r * .2), (cx + r * .3, cy + r * .2), (cx + r * .28, cy + r * .95),
                    (cx + r * .1, cy + r * .95), (cx + r * .1, cy + r * .5), (cx - r * .1, cy + r * .5),
                    (cx - r * .1, cy + r * .95), (cx - r * .28, cy + r * .95)])
    rr(s, ACERO_OSC, cx, cy + r * .2, r * .62, r * .1, 3)
    lin(s, (245, 250, 255), (cx - r * .2, cy + r * .3), (cx - r * .2, cy + r * .85), max(2, r * .06))


def _rallador(s, cx, cy, r):
    rr(s, (240, 170, 60), cx, cy - r * .8, r * .8, r * .18, r * .08)            # asa
    poli(s, ACERO, [(cx - r * .3, cy - r * .7), (cx + r * .3, cy - r * .7), (cx + r * .6, cy + r * .95),
                    (cx - r * .6, cy + r * .95)])
    poli(s, ACERO_OSC, [(cx - r * .3, cy - r * .7), (cx + r * .3, cy - r * .7), (cx + r * .6, cy + r * .95),
                        (cx - r * .6, cy + r * .95)], True, 2)
    for i in range(4):
        for j in range(3):
            yy = cy - r * .35 + i * r * .33
            ww = r * (.3 + .3 * (yy - (cy - r * .7)) / (r * 1.65))
            xx = cx + (j - 1) * ww * .55
            e(s, (90, 100, 125), xx, yy, r * .18, r * .1, False)
            lin(s, (250, 252, 255), (xx - r * .08, yy - r * .06), (xx + r * .08, yy - r * .06), 1)


def _rodillo(s, cx, cy, r):
    lin(s, (190, 130, 70), (cx - r * .95, cy), (cx + r * .95, cy), max(4, r * .16))
    for k in (-1, 1):
        c(s, (230, 90, 80), cx + k * r * .93, cy, r * .13)
    rr(s, MADERA, cx, cy, r * 1.4, r * .6, r * .2)
    lin(s, aclarar(MADERA, .5), (cx - r * .6, cy - r * .15), (cx + r * .55, cy - r * .15), max(2, r * .07))
    for k in (-1, 1):
        lin(s, oscurecer(MADERA, .25), (cx + k * r * .5, cy - r * .27), (cx + k * r * .5, cy + r * .27), 2)


def _tenedor(s, cx, cy, r):
    rr(s, ACERO, cx, cy - r * .45, r * .2, r * .95, r * .09)
    poli(s, ACERO, [(cx - r * .38, cy - r * .02), (cx + r * .38, cy - r * .02), (cx + r * .3, cy + r * .2),
                    (cx + r * .08, cy + r * .28), (cx - r * .08, cy + r * .28), (cx - r * .3, cy + r * .2)])
    for k in (-3, -1, 1, 3):
        rr(s, ACERO, cx + k * r * .1, cy + r * .5, r * .1, r * .85, r * .04)
    lin(s, (250, 252, 255), (cx - r * .05, cy - r * .85), (cx - r * .05, cy - r * .1), max(2, r * .05))


def _cuchara(s, cx, cy, r):
    rr(s, MADERA, cx, cy - r * .35, r * .17, r * 1.1, r * .08)
    e(s, MADERA, cx, cy + r * .55, r * .62, r * .82)
    e(s, aclarar(MADERA, .35), cx - r * .03, cy + r * .58, r * .42, r * .6, False)
    lin(s, (255, 235, 200), (cx - r * .12, cy - r * .8), (cx - r * .12, cy - r * .1), max(2, r * .04))


def _batidor(s, cx, cy, r):
    rr(s, ROJO, cx, cy - r * .55, r * .26, r * .85, r * .12)
    lin(s, aclarar(ROJO, .5), (cx - r * .06, cy - r * .85), (cx - r * .06, cy - r * .3), max(2, r * .05))
    rr(s, ACERO_OSC, cx, cy - r * .1, r * .3, r * .1, 3)
    for k in (-.5, -.25, 0, .25, .5):
        pygame.draw.ellipse(s, ACERO, (int(cx - r * (.12 + abs(k) * .7)), int(cy - r * .05),
                                       int(r * (.24 + abs(k) * 1.4)), int(r * 1.0)), 2)
    pygame.draw.ellipse(s, ACERO_OSC, (int(cx - r * .55), int(cy - r * .05), int(r * 1.1), int(r * 1.0)), 2)
    lin(s, ACERO, (cx, cy - r * .05), (cx, cy + r * .95), 2)


def _espatula(s, cx, cy, r):
    rr(s, AZUL, cx, cy - r * .5, r * .22, r * .95, r * .1)
    lin(s, aclarar(AZUL, .5), (cx - r * .05, cy - r * .85), (cx - r * .05, cy - r * .2), max(2, r * .05))
    poli(s, (250, 200, 80), [(cx - r * .12, cy - r * .02), (cx + r * .12, cy - r * .02), (cx + r * .45, cy + r * .2),
                             (cx + r * .45, cy + r * .9), (cx - r * .45, cy + r * .9), (cx - r * .45, cy + r * .2)])
    for k in (-.25, 0, .25):
        lin(s, (210, 150, 40), (cx + k * r, cy + r * .4), (cx + k * r, cy + r * .75), 2)


def _salero(s, cx, cy, r):
    rr(s, (235, 245, 255), cx, cy + r * .2, r * .8, r * 1.1, r * .22)
    rr(s, (250, 252, 255), cx, cy + r * .35, r * .62, r * .7, r * .15, False)
    for k in (-.1, .05, .2):
        c(s, (245, 245, 245), cx + k * r * 1.2, cy + r * .45 + k * r * .3, r * .035, False)
    rr(s, ROJO, cx, cy - r * .5, r * .86, r * .5, r * .2)
    for k in (-.25, 0, .25):
        c(s, (250, 230, 230), cx + k * r, cy - r * .5, r * .06, False)
    lin(s, (255, 255, 255), (cx - r * .26, cy), (cx - r * .26, cy + r * .6), max(2, r * .06))
    for dx, dy in ((.1, .95), (-.2, .9), (.3, .85)):                        # granitos que caen
        c(s, (255, 255, 255), cx + dx * r, cy + dy * r, r * .05, INK, 1)


def _cernidor(s, cx, cy, r):
    rr(s, ROSA, cx, cy - r * .62, r * .22, r * .8, r * .1)
    pygame.draw.circle(s, (240, 245, 255), (int(cx), int(cy + r * .05)), int(r * .82))
    rect = pygame.Rect(int(cx - r * .82), int(cy - r * .77), int(r * 1.64), int(r * 1.64))
    pygame.draw.arc(s, ACERO_OSC, rect, math.pi, 2 * math.pi, 3)
    cuenco = pygame.Rect(int(cx - r * .8), int(cy - r * .1), int(r * 1.6), int(r * .9))
    pygame.draw.ellipse(s, (232, 238, 250), cuenco)
    for i in range(1, 6):
        xx = cx - r * .8 + i * r * .267
        lin(s, (190, 200, 220), (xx, cy - r * .02), (xx, cy + r * .78), 1)
    for i in range(1, 4):
        yy = cy + i * r * .2
        lin(s, (190, 200, 220), (cx - r * .72, yy), (cx + r * .72, yy), 1)
    pygame.draw.ellipse(s, ACERO_OSC, cuenco, 3)
    rr(s, ACERO_OSC, cx, cy - r * .1, r * 1.64, r * .1, 4, False)


def _forma_molde(tipo, cx, cy, r):
    if tipo == "corazon":
        pts = []
        for i in range(48):
            a = i / 48 * 2 * math.pi
            px = 16 * math.sin(a) ** 3
            py = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
            pts.append((cx + px / 17 * r * .85, cy - py / 17 * r * .85))
        return pts
    if tipo == "circulo":
        return [(cx + math.cos(i / 40 * 2 * math.pi) * r * .8, cy + math.sin(i / 40 * 2 * math.pi) * r * .8)
                for i in range(40)]
    pts = []                                                                  # estrella
    for i in range(10):
        rad = r * (.95 if i % 2 == 0 else .42)
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    return pts


def _molde(tipo):
    def f(s, cx, cy, r):
        cy2 = cy + r * .22
        pts = _forma_molde(tipo, cx, cy2, r * .85)
        poli(s, (245, 150, 70) if tipo == "estrella" else ((245, 110, 150) if tipo == "corazon" else (110, 190, 235)),
             pts, True, 2)
        interior = _forma_molde(tipo, cx, cy2, r * .85 * .72)
        pygame.draw.polygon(s, (255, 236, 200), [(int(a), int(b)) for a, b in interior])
        pygame.draw.polygon(s, (205, 150, 100), [(int(a), int(b)) for a, b in interior], 2)
        rr(s, ACERO, cx, cy - r * .88, r * .5, r * .22, r * .1)
        lin(s, ACERO_OSC, (cx, cy - r * .78), (cx, cy2 - r * .5), max(2, r * .06))
    return f


def _exprimidor(s, cx, cy, r):
    poli(s, (255, 250, 245), [(cx - r * .95, cy + r * .45), (cx + r * .95, cy + r * .45), (cx + r * .8, cy + r * .9),
                              (cx - r * .8, cy + r * .9)])
    e(s, (250, 235, 150), cx, cy + r * .45, r * 1.9, r * .5)
    poli(s, (245, 200, 80), [(cx - r * .55, cy + r * .45), (cx + r * .55, cy + r * .45), (cx + r * .25, cy - r * .2),
                             (cx - r * .25, cy - r * .2)])
    for k in (-.3, -.1, .1, .3):
        lin(s, (210, 150, 40), (cx + k * r * .6, cy + r * .4), (cx + k * r * .25, cy - r * .1), 2)
    c(s, (255, 225, 110), cx, cy - r * .3, r * .3)
    c(s, (255, 245, 190), cx - r * .08, cy - r * .36, r * .1, False)
    e(s, (255, 250, 245), cx, cy + r * .5, r * 1.9, r * .3, True)
    for dx in (-.55, .55):                                                    # medio limon
        pass


def _sarten(s, cx, cy, r):
    rr(s, (150, 100, 65), cx, cy + r * .72, r * .26, r * .6, r * .1)
    lin(s, (205, 150, 100), (cx - r * .06, cy + r * .5), (cx - r * .06, cy + r * .95), 2)
    c(s, (80, 85, 100), cx, cy - r * .22, r * .72)
    c(s, (55, 58, 72), cx, cy - r * .22, r * .6, False)
    pygame.draw.arc(s, (150, 155, 175), pygame.Rect(int(cx - r * .55), int(cy - r * .77), int(r * 1.1), int(r * 1.1)),
                    2.4, 3.6, 3)
    c(s, (255, 235, 120), cx + r * .08, cy - r * .22, r * .22, False)
    c(s, (255, 255, 210), cx + r * .08, cy - r * .22, r * .1, False)
    c(s, (180, 190, 205), cx, cy + r * .5 - r * .05, r * .06, False)


def _olla(s, cx, cy, r):
    for k in (-1, 1):
        pygame.draw.circle(s, (130, 120, 130), (int(cx + k * r * .88), int(cy)), int(r * .18), max(3, int(r * .09)))
    rr(s, (110, 175, 235), cx, cy + r * .1, r * 1.5, r * 1.15, r * .2)
    rr(s, aclarar((110, 175, 235), .4), cx - r * .35, cy + r * .1, r * .18, r * .85, r * .08, False)
    rr(s, (245, 245, 250), cx, cy - r * .08, r * 1.5, r * .12, 3, False)
    e(s, (150, 150, 165), cx, cy - r * .5, r * 1.6, r * .3)
    poli(s, (170, 175, 190), [(cx - r * .75, cy - r * .5), (cx + r * .75, cy - r * .5), (cx + r * .55, cy - r * .75),
                              (cx - r * .55, cy - r * .75)])
    c(s, (240, 90, 80), cx, cy - r * .85, r * .12)


def _manga(s, cx, cy, r):
    poli(s, (250, 250, 255), [(cx - r * .45, cy - r * .85), (cx + r * .45, cy - r * .85), (cx + r * .14, cy + r * .6),
                              (cx - r * .14, cy + r * .6)])
    poli(s, (250, 170, 205), [(cx - r * .3, cy - r * .1), (cx + r * .3, cy - r * .1), (cx + r * .14, cy + r * .6),
                              (cx - r * .14, cy + r * .6)], False)
    for i in range(3):                                                        # punta de estrella
        yy = cy + r * (.66 + .1 * i)
        ww = r * (.2 - .035 * i)
        e(s, (250, 170, 205), cx, yy, ww * 2, r * .14)
    lin(s, (255, 255, 255), (cx - r * .3, cy - r * .7), (cx - r * .12, cy + r * .3), max(2, r * .05))
    poli(s, (230, 235, 245), [(cx - r * .45, cy - r * .85), (cx + r * .45, cy - r * .85), (cx + r * .3, cy - r * .98),
                              (cx - r * .3, cy - r * .98)])


def _jarra(s, cx, cy, r):
    pygame.draw.arc(s, (150, 190, 230), pygame.Rect(int(cx + r * .3), int(cy - r * .2), int(r * .7), int(r * .85)),
                    -math.pi / 2, math.pi / 2, max(4, int(r * .13)))
    poli(s, (205, 235, 255), [(cx - r * .55, cy - r * .55), (cx + r * .5, cy - r * .55), (cx + r * .45, cy + r * .85),
                              (cx - r * .5, cy + r * .85)])
    poli(s, (250, 170, 60), [(cx - r * .54, cy - r * .05), (cx + r * .49, cy - r * .05), (cx + r * .45, cy + r * .85),
                             (cx - r * .5, cy + r * .85)], False)
    lin(s, (255, 220, 140), (cx - r * .54, cy - r * .05), (cx + r * .49, cy - r * .05), 3)
    poli(s, (205, 235, 255), [(cx - r * .55, cy - r * .55), (cx - r * .8, cy - r * .5), (cx - r * .5, cy - r * .35)], True)
    lin(s, (255, 255, 255), (cx - r * .38, cy - r * .35), (cx - r * .35, cy + r * .65), max(2, r * .07))


def _tazon_h(s, cx, cy, r):
    e(s, (235, 240, 250), cx, cy - r * .1, r * 1.8, r * .5)
    e(s, (190, 150, 110), cx, cy - r * .06, r * 1.55, r * .36, False)
    poli(s, (130, 195, 235), [(cx - r * .9, cy - r * .1)] +
         [(cx + math.cos(a) * r * .9, cy - r * .1 + math.sin(a) * r * .95) for a in [i * math.pi / 14 for i in range(15)]], True)
    pygame.draw.arc(s, (240, 245, 255), pygame.Rect(int(cx - r * .9), int(cy - r * .35), int(r * 1.8), int(r * 1.0)), 3.5, 5.0, 3)
    lin(s, (250, 245, 200), (cx - r * .75, cy + r * .2), (cx + r * .75, cy + r * .2), max(3, r * .1))
    for k in (-.5, 0, .5):
        c(s, (255, 235, 130), cx + k * r, cy + r * .2, r * .05, False)
    e(s, (235, 240, 250), cx, cy - r * .1, r * 1.8, r * .5, True)
    e(s, (190, 150, 110), cx, cy - r * .06, r * 1.55, r * .36, False)
    e(s, (210, 170, 125), cx, cy - r * .03, r * 1.2, r * .22, False)


def _plato_h(s, cx, cy, r):
    e(s, (190, 196, 215), cx, cy + r * .12, r * 1.95, r * 1.35)
    e(s, (255, 255, 255), cx, cy + r * .06, r * 1.95, r * 1.35)
    e(s, (225, 235, 250), cx, cy + r * .06, r * 1.45, r * .98, False)
    e(s, (255, 255, 255), cx, cy + r * .06, r * 1.15, r * .78, (205, 215, 235), 2)
    for k in range(8):
        a = k * math.pi / 4
        c(s, (250, 170, 90), cx + math.cos(a) * r * .8, cy + r * .06 + math.sin(a) * r * .54, r * .045, False)
    brillo(s, cx - r * .5, cy - r * .3, r * .05)


def _guantes(s, cx, cy, r):
    for k, col in ((-1, (240, 100, 110)), (1, (110, 190, 235))):
        gx = cx + k * r * .42
        rr(s, col, gx, cy + r * .0, r * .66, r * 1.35, r * .22)
        e(s, col, gx + k * r * .26, cy - r * .02, r * .28, r * .42)
        rr(s, aclarar(col, .45), gx, cy - r * .6, r * .7, r * .3, r * .1)
        rr(s, oscurecer(col, .15), gx, cy + r * .3, r * .5, r * .3, r * .1, False)
        for j in range(3):
            c(s, (255, 255, 255), gx - r * .14 + j * r * .14, cy - r * .1 + (j % 2) * r * .1, r * .04, False)
        pygame.draw.arc(s, (255, 255, 255), pygame.Rect(int(gx - r * .5), int(cy + r * .35), int(r * 1.0), int(r * .3)),
                        math.pi, 2 * math.pi, 2)
        c(s, (250, 235, 150), gx, cy - r * .86, r * .07, INK, 1)


_HERR = {"cuchillo": _cuchillo, "tijera": _tijera, "pelador": _pelador, "rallador": _rallador, "rodillo": _rodillo,
         "tenedor": _tenedor, "cuchara": _cuchara, "batidor": _batidor, "espatula": _espatula, "salero": _salero,
         "cernidor": _cernidor, "molde": _molde("estrella"), "molde_estrella": _molde("estrella"),
         "molde_corazon": _molde("corazon"), "molde_circulo": _molde("circulo"), "exprimidor": _exprimidor,
         "sarten": _sarten, "olla": _olla, "manga": _manga, "jarra": _jarra, "tazon": _tazon_h, "plato": _plato_h,
         "guantes": _guantes}
NOMBRES = ("cuchillo", "tijera", "pelador", "rallador", "rodillo", "tenedor", "cuchara", "batidor", "espatula",
           "salero", "cernidor", "molde", "exprimidor", "sarten", "olla", "manga", "jarra", "tazon", "plato", "guantes")
_ALIAS = {"espátula": "espatula", "sartén": "sarten", "tazón": "tazon", "cuenco": "tazon", "rayador": "rallador",
          "pastelera": "manga", "manga_pastelera": "manga", "molde_estrellas": "molde_estrella",
          "molde_corazones": "molde_corazon", "corazon": "molde_corazon", "estrella": "molde_estrella",
          "circulo": "molde_circulo", "cortador": "molde", "cortador_estrella": "molde_estrella",
          "cortador_corazon": "molde_corazon", "cortador_circulo": "molde_circulo"}

_cache = {}


def dibujar_herr(p, nombre, x, y, tam=64, angulo=0.0):
    """Dibuja la herramienta `nombre` centrada en (x, y), cabe en un cuadro de tam x tam (angulo en grados)."""
    try:
        n = str(nombre or "").lower().strip().replace(" ", "_")
        n = _ALIAS.get(n, n)
        fn = _HERR.get(n)
        tam = max(4, int(tam))
        S = int(tam * 1.5) + 4
        s = pygame.Surface((S, S), pygame.SRCALPHA)
        r = tam / 2
        if fn is None:
            pygame.draw.circle(s, (200, 200, 215), (S // 2, S // 2), int(r * .8))
            pygame.draw.circle(s, INK, (S // 2, S // 2), int(r * .8), 2)
        else:
            fn(s, S / 2, S / 2, r)
        rotar_blit(p, s, x, y, angulo)
    except Exception:
        try:
            pygame.draw.circle(p, (200, 200, 215), (int(x), int(y)), max(3, int(tam / 3)))
        except Exception:
            pass
