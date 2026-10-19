"""Platos terminados de la Cocina, dibujados con codigo (vista 3/4, colores alegres).

    dibujar_plato(p, receta_id_o_dict, x, y, tam=120, t=0.0)

`receta` puede ser el id (cocina_datos.POR_ID) o el dict de la receta (id, nombre, color, cont, ...). El tipo de
comida se deduce de las palabras del id y del nombre (tipo_de(receta)); si no encaja, se dibuja un plato generico
con el color de la receta segun su recipiente (`cont`: plato, vaso, cuenco, bandeja). Un dict puede traer la clave
opcional "tipo" para forzarlo. Tipos: jugos, panes, ensaladas, sopas, pastas, arroces, pescados, empanadas,
tartas, postres, panqueques, huevos, generico.  `t` solo anima el vapor.
Nunca lanza excepcion (receta desconocida = plato generico).
"""

import math
import unicodedata
import zlib
from random import Random

import pygame

from nucleo import aclarar, oscurecer
from cocina_herramientas import c, e, rr, poli, lin, brillo, INK

TIPOS = ("jugos", "panes", "ensaladas", "sopas", "pastas", "arroces", "pescados", "empanadas", "tartas", "postres",
         "panqueques", "huevos", "generico")

# palabras clave (el orden importa: el primer tipo que encaje gana)
_PALABRAS = (
    ("jugos", ("jugo", "licuado", "limonada", "smoothie", "naranjada", "refresco", "chicha", "batido", "zumo")),
    ("panqueques", ("panqueque", "panqueques", "crepe", "crepes", "waffle", "hotcake", "hotcakes", "tortita")),
    ("empanadas", ("empanada", "empanadas", "rollo", "rollos", "wrap", "taco", "tacos", "burrito", "enrollado",
                   "enrollados", "tamal", "rollito", "rollitos", "pastelito")),
    ("tartas", ("pizza", "pizzas", "tarta", "tartas", "quiche", "tartaleta", "calzone")),
    ("postres", ("galleta", "galletas", "torta", "tortas", "pastel", "pasteles", "keke", "queque", "cupcake", "cupcakes",
                 "muffin", "brownie", "flan", "helado", "postre", "budin", "gelatina", "mousse", "alfajor", "alfajores",
                 "dona", "donas", "bizcocho", "mazamorra", "turron", "dulce", "dulces", "cookie", "cookies")),
    ("pescados", ("pescado", "pescados", "langostino", "langostinos", "camaron", "camarones", "calamar", "calamares",
                  "ceviche", "cebiche", "sushi", "marisco", "mariscos", "salmon", "atun", "trucha", "pulpo", "pez",
                  "tiradito", "jalea", "chicharron")),
    ("huevos", ("huevo", "huevos", "tortilla", "omelette", "omelet", "revuelto", "revueltos")),
    ("ensaladas", ("ensalada", "ensaladas", "tabule", "cesar")),
    ("sopas", ("sopa", "sopas", "crema", "cremas", "caldo", "guiso", "chupe", "sancochado", "locro", "pure", "estofado",
               "aguadito", "menestrone", "gazpacho", "puchero")),
    ("pastas", ("pasta", "pastas", "fideo", "fideos", "espagueti", "espaguetis", "tallarin", "tallarines", "lasagna",
                "lasana", "ravioles", "raviol", "macarron", "macarrones", "canelones", "noquis", "spaghetti")),
    ("arroces", ("arroz", "risotto", "chaufa", "arroces", "pilaf", "paella")),
    ("panes", ("pan", "panes", "pancito", "tostada", "tostadas", "sandwich", "sandwiches", "bruschetta", "bruschettas",
               "bocadillo", "emparedado", "croissant", "bagel")),
)


def _norm(txt):
    t = unicodedata.normalize("NFKD", str(txt or "").lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t.replace("_", " ").replace("-", " ")


def _palabras(rec):
    return _norm("%s %s" % (rec.get("id", ""), rec.get("nombre", ""))).split()


def tipo_de(rec):
    """Tipo de comida de una receta (uno de TIPOS)."""
    try:
        if rec.get("tipo") in TIPOS:
            return rec["tipo"]
        if rec.get("cont") == "vaso":                      # todo lo que va en vaso es bebida: nunca sobre plato
            return "jugos"
        if "pastel" in _palabras(rec) and any(w in _palabras(rec) for w in ("pollo", "carne", "papa", "verduras", "atun")):
            return "tartas"                                # pastel salado, no postre
        pal = _palabras(rec)
        for tipo, claves in _PALABRAS:
            if any(w in claves for w in pal):
                return tipo
        if rec.get("cont") == "vaso":
            return "jugos"
    except Exception:
        pass
    return "generico"


def _tiene(rec, *claves):
    pal = _palabras(rec)
    txt = " ".join(pal)
    return any(k in pal or k in txt for k in claves)


# ----------------------------------------------------------------------------- recipientes
PLATO_K = .8          # el plato es apenas mas grande que la comida (la comida ocupa ~90% del plato)


def _plato(s, cx, cy, r, cont="plato"):
    """Plato (o bandeja) en 3/4; devuelve (fx, fy) = centro donde va la comida."""
    py = cy + r * .32
    r0 = r
    if cont == "bandeja_ancha":                    # bandeja grande: plato a la izquierda, vaso a la derecha
        rr(s, (150, 150, 165), cx, py + r * .1, r * 2.9, r * 1.35, r * .22, False)
        rr(s, (190, 195, 210), cx, py, r * 2.9, r * 1.35, r * .22, (120, 125, 145), 2)
        rr(s, (225, 230, 240), cx, py - r * .02, r * 2.65, r * 1.1, r * .16, False)
        for k in (-1, 1):
            rr(s, (150, 155, 175), cx + k * r * 1.45, py, r * .1, r * .35, 3, False)
        return cx, cy
    if cont == "bandeja":
        r = r * PLATO_K
        rr(s, (150, 150, 165), cx, py + r * .1, r * 1.98, r * 1.0, r * .18, False)
        rr(s, (190, 195, 210), cx, py, r * 1.98, r * 1.0, r * .18, (120, 125, 145), 2)
        rr(s, (225, 230, 240), cx, py - r * .02, r * 1.7, r * .8, r * .12, False)
        for k in (-1, 1):
            rr(s, (150, 155, 175), cx + k * r * 1.0, py, r * .1, r * .3, 3, False)
        return cx, cy + r0 * .2
    r = r * PLATO_K
    e(s, (165, 172, 195), cx, py + r * .08, r * 1.98, r * 1.06, False)
    e(s, (255, 255, 255), cx, py, r * 1.98, r * 1.06, (195, 202, 222), 2)
    e(s, (232, 238, 250), cx, py, r * 1.52, r * .8, False)
    e(s, (255, 255, 255), cx, py - r * .02, r * 1.4, r * .72, (214, 222, 240), 1)
    return cx, cy + r0 * .22


def _tazon_3q(s, cx, cy, r, body=(235, 225, 205), banda=(240, 130, 90), ancho=1.75, alto=.9):
    """Cuenco 3/4. Devuelve (yborde, ancho_boca, alto_boca) de la boca."""
    w = r * ancho
    yb = cy - r * .1
    boca_h = w * .34
    pts = [(cx - w / 2, yb)] + [(cx + math.cos(a) * w / 2, yb + math.sin(a) * r * alto) for a in [i * math.pi / 18 for i in range(19)]]
    poli(s, (170, 160, 150), [(a, b + 3) for a, b in pts], False)
    poli(s, body, pts)
    pygame.draw.arc(s, aclarar(body, .6), pygame.Rect(int(cx - w * .47), int(yb - r * .1), int(w * .94), int(r * alto * 1.7)), 3.6, 4.9, 3)
    ang = [i * math.pi / 18 for i in range(19)]
    sup = [(cx + math.cos(a) * w * .5 * .93, yb + r * .17 + math.sin(a) * r * alto * .62) for a in ang]
    pygame.draw.lines(s, banda, False, [(int(a), int(b)) for a, b in sup], max(4, int(r * .1)))
    e(s, body, cx, yb, w, boca_h, (170, 160, 150), 2)
    return yb, w, boca_h


# ----------------------------------------------------------------------------- jugos
def _jugo(s, cx, cy, r, col, rec, var, cont):
    cx, cy = cx, cy + r * .02
    lq = col
    cremoso = _tiene(rec, "licuado", "batido", "smoothie", "leche")
    top, bot, wt, wb = cy - r * .72, cy + r * .78, r * .62, r * .46
    sombra = (cx, bot + r * .06)
    e(s, (120, 130, 150), sombra[0], sombra[1] + r * .03, r * 1.15, r * .26, False)             # base / posavasos
    e(s, (236, 240, 248), sombra[0], sombra[1], r * 1.15, r * .26, (170, 180, 200), 2)
    e(s, (0, 0, 0, 50), sombra[0], sombra[1] - r * .02, r * .85, r * .17, False)
    # pajita atras
    lin(s, (240, 90, 120), (cx + r * .15, cy - r * .1), (cx + r * .42, top - r * .38), max(4, r * .1))
    lin(s, (255, 170, 190), (cx + r * .15, cy - r * .1), (cx + r * .42, top - r * .38), max(1, r * .03))
    cristal = (214, 238, 255)
    poli(s, cristal, [(cx - wt, top), (cx + wt, top), (cx + wb, bot), (cx - wb, bot)], (150, 190, 220), 2)
    nivel = top + r * .22
    fx = lambda y, sg: cx + sg * (wt + (wb - wt) * (y - top) / (bot - top))
    poli(s, lq, [(fx(nivel, -1) + 2, nivel), (fx(nivel, 1) - 2, nivel), (cx + wb - 2, bot - 2), (cx - wb + 2, bot - 2)], False)
    poli(s, oscurecer(lq, .15), [(cx + wb * .35, nivel), (fx(nivel, 1) - 2, nivel), (cx + wb - 2, bot - 2), (cx + wb * .35, bot - 2)], False)
    e(s, aclarar(lq, .45), cx, nivel, (fx(nivel, 1) - fx(nivel, -1)) - 4, r * .17, False)
    if cremoso:
        for k in range(5):
            c(s, (255, 252, 245), cx - r * .5 + k * r * .25, nivel - r * .03, r * .12, (235, 215, 215), 1)
    lin(s, (255, 255, 255), (cx - wt * .65, top + r * .2), (cx - wb * .6, bot - r * .22), max(3, r * .08))
    for dx, dy in ((.2, .1), (-.15, .35), (.3, .5)):                                       # gotitas
        c(s, (255, 255, 255), cx + dx * r, cy + dy * r, r * .035, False)
    # rodaja en el borde
    fruta = aclarar(lq, .1)
    if _tiene(rec, "limon", "limonada"):
        fruta = (240, 225, 90)
    if _tiene(rec, "fresa", "frutilla", "berry", "mora"):
        fruta = (230, 60, 80)
    cxr, cyr = cx - wt * .88, top + r * .02
    c(s, oscurecer(fruta, .15), cxr, cyr, r * .22)
    c(s, aclarar(fruta, .45), cxr, cyr, r * .17, False)
    for k in range(8):
        a = k * math.pi / 4
        lin(s, oscurecer(fruta, .1), (cxr, cyr), (cxr + math.cos(a) * r * .16, cyr + math.sin(a) * r * .16), 2)
    e(s, cristal, cx, top, wt * 2, r * .2, (150, 190, 220), 2)
    e(s, aclarar(lq, .5), cx, top + r * .02, wt * 1.7, r * .12, False)


# ----------------------------------------------------------------------------- panes y tostadas
def _rebanada(s, x, y, w, h, corteza, miga, ang=0.0):
    sup = pygame.Surface((int(w * 1.6), int(h * 1.6)), pygame.SRCALPHA)
    cx, cy = sup.get_width() / 2, sup.get_height() / 2
    pts = [(cx - w * .5, cy + h * .5), (cx - w * .5, cy - h * .15), (cx - w * .3, cy - h * .5), (cx + w * .3, cy - h * .5),
           (cx + w * .5, cy - h * .15), (cx + w * .5, cy + h * .5)]
    poli(sup, corteza, pts)
    pygame.draw.rect(sup, miga, (int(cx - w * .4), int(cy - h * .36), int(w * .8), int(h * .8)), border_radius=int(w * .15))
    for k in range(5):
        c(sup, oscurecer(miga, .08), cx - w * .25 + (k * 37 % 5) * w * .12, cy - h * .2 + (k * 53 % 5) * h * .14, max(1, w * .02), False)
    sup = pygame.transform.rotate(sup, ang)
    s.blit(sup, sup.get_rect(center=(int(x), int(y))))


def _pan(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    if _tiene(rec, "sandwich", "emparedado", "bocadillo"):
        # sandwich: dos triangulos apilados con capas
        for k, (dx, dy) in enumerate(((-.38, .12), (.35, -.02))):
            x, y = fx + dx * r, fy + dy * r
            poli(s, (205, 140, 75), [(x - r * .5, y + r * .38), (x + r * .5, y + r * .38), (x, y - r * .45)])
            capas = ((y + r * .12, (110, 190, 90)), (y + r * .02, (240, 90, 70)), (y - r * .08, (250, 215, 90)))
            for yy, cc in capas:
                rr(s, cc, x, yy, r * .74 - (y + r * .12 - yy) * 1.2, r * .09, 3, False)
            poli(s, (245, 215, 150), [(x - r * .4, y + r * .3), (x + r * .4, y + r * .3), (x, y - r * .33)], False)
            poli(s, (205, 140, 75), [(x - r * .5, y + r * .38), (x + r * .5, y + r * .38), (x + r * .44, y + r * .3), (x - r * .44, y + r * .3)], False)
        return
    mant = _tiene(rec, "mantequilla")
    mermelada = _tiene(rec, "mermelada", "dulce")
    untado = (200, 50, 85) if mermelada else (252, 228, 120)
    for dx, dy, ang in ((-.4, .05, 8), (.38, -.05, -6)):
        x, y = fx + dx * r, fy + dy * r
        _rebanada(s, x, y, r * .95, r * .95, (200, 130, 65), (246, 214, 150), ang)
        sup_h = r * .7
        e(s, untado, x, y - r * .02, sup_h, sup_h * .78, oscurecer(untado, .25), 1)
        e(s, aclarar(untado, .5), x - r * .12, y - r * .12, r * .22, r * .1, False)
        if mant and not mermelada:
            rr(s, (255, 240, 150), x + r * .08, y + r * .05, r * .3, r * .2, r * .05)
            rr(s, (255, 250, 200), x + r * .05, y + r * .0, r * .3, r * .08, r * .04, False)
    for k in range(14):                                                                   # azucar / migas
        a = k * 2.3
        c(s, (255, 255, 255), fx + math.cos(a) * r * (.3 + .5 * ((k * 7) % 5) / 5), fy + math.sin(a) * r * .22 + r * .02, max(1, r * .028), False)


# ----------------------------------------------------------------------------- ensaladas
def _ensalada(s, cx, cy, r, col, rec, var, cont):
    yb, w, bh = _tazon_3q(s, cx, cy + r * .12, r, (250, 250, 255), (110, 190, 100), 1.8, .85)
    e(s, (120, 175, 95), cx, yb, w * .93, bh * .88, False)
    rng = Random(var)
    verdes = [(95, 190, 85), (130, 215, 100), (70, 160, 70), (160, 225, 120)]
    for i in range(20):                                                                   # hojas
        a = i / 20 * 6.28
        d = rng.uniform(.2, .8)
        x = cx + math.cos(a) * w * .42 * d
        y = yb - r * .08 + math.sin(a) * r * .17 * d - (1 - d) * r * .4
        e(s, verdes[i % 4], x, y, r * rng.uniform(.5, .7), r * rng.uniform(.3, .4), oscurecer(verdes[i % 4], .3), 1)
    for i in range(7):                                                                    # tomates
        a = i * .9 + .3
        d = rng.uniform(.25, .8)
        x, y = cx + math.cos(a) * w * .38 * d, yb - r * .3 + math.sin(a) * r * .15 * d
        c(s, (230, 65, 55), x, y, r * .15)
        brillo(s, x - r * .05, y - r * .05, r * .035)
    for i in range(5):                                                                    # zanahoria
        a = i * 1.3 + 1
        x, y = cx + math.cos(a) * w * .3, yb - r * .38 + math.sin(a) * r * .1
        c(s, (250, 150, 40), x, y, r * .1)
        c(s, (255, 190, 90), x, y, r * .05, False)
    for i in range(4):                                                                    # pepino
        a = i * 1.7 + .2
        x, y = cx + math.cos(a) * w * .22, yb - r * .45 + math.sin(a) * r * .09
        c(s, (80, 165, 85), x, y, r * .11)
        c(s, (200, 235, 160), x, y, r * .08, False)
    # borde delantero del cuenco
    pygame.draw.arc(s, (170, 160, 150), pygame.Rect(int(cx - w / 2), int(yb - bh / 2), int(w), int(bh)), math.pi, 2 * math.pi, 2)
    pygame.draw.arc(s, (170, 160, 150), pygame.Rect(int(cx - w / 2), int(yb - bh / 2), int(w), int(bh)), 0, math.pi, 3)


# ----------------------------------------------------------------------------- sopas y cremas
def _sopa(s, cx, cy, r, col, rec, var, cont):
    crema = _tiene(rec, "crema", "pure")
    yb, w, bh = _tazon_3q(s, cx, cy + r * .12, r, (252, 246, 232), oscurecer(col, .05) if col else (240, 130, 90), 1.8, .85)
    liq = col
    e(s, oscurecer(liq, .2), cx, yb + 2, w * .9, bh * .85, False)
    e(s, liq, cx, yb + 2, w * .86, bh * .78, False)
    rng = Random(var)
    if crema:
        e(s, aclarar(liq, .25), cx - w * .05, yb, w * .55, bh * .5, False)
        pts = []
        for i in range(30):                                                               # espiral de crema
            a = i * .45
            d = 1 - i / 34
            pts.append((cx + math.cos(a) * w * .28 * d, yb + 2 + math.sin(a) * bh * .3 * d))
        pygame.draw.lines(s, (255, 252, 240), False, [(int(a), int(b)) for a, b in pts], max(3, int(r * .07)))
        for k in range(3):
            e(s, (90, 175, 80), cx + w * (.18 + k * .05), yb - bh * .08 + k * 3, r * .13, r * .06, False)
        for k in range(5):                                                                # crutones
            rr(s, (225, 170, 90), cx - w * .3 + k * w * .13, yb + bh * .22 - (k % 2) * 4, r * .14, r * .12, 3)
    else:
        for i in range(12):
            a = rng.uniform(0, 6.28)
            d = rng.uniform(.15, .78)
            x, y = cx + math.cos(a) * w * .4 * d, yb + 2 + math.sin(a) * bh * .36 * d
            k = i % 4
            if k == 0:
                c(s, (250, 150, 40), x, y, r * .1, (200, 110, 30), 1)
            elif k == 1:
                c(s, (110, 190, 80), x, y, r * .05, False)
            elif k == 2:
                rr(s, (245, 225, 150), x, y, r * .15, r * .13, 3, (210, 185, 110), 1)
            else:
                pygame.draw.arc(s, (250, 220, 130), pygame.Rect(int(x - r * .1), int(y - r * .05), int(r * .2), int(r * .1)), 0, 3.4, 3)
        e(s, aclarar(liq, .55), cx - w * .22, yb - bh * .15, w * .22, bh * .14, False)
    pygame.draw.ellipse(s, (170, 160, 150), pygame.Rect(int(cx - w / 2), int(yb - bh / 2), int(w), int(bh)), 3)
    # cuchara apoyada
    lin(s, (200, 205, 220), (cx + w * .52, yb + bh * .1), (cx + w * .8, yb - r * .5), max(3, int(r * .07)))
    e(s, (210, 215, 230), cx + w * .46, yb + bh * .15, r * .24, r * .14, (150, 155, 175), 1)


# ----------------------------------------------------------------------------- pastas
def _pasta(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    salsa = col
    if _tiene(rec, "lasagna", "lasana", "canelones"):
        x, y, w, h = fx, fy, r * 1.1, r * .5
        for i, cc in enumerate(((250, 215, 130), (225, 70, 55), (255, 245, 210), (250, 215, 130), (225, 70, 55), (250, 215, 130))):
            yy = y + r * .12 - i * h * .13
            poli(s, cc, [(x - w * .5, yy), (x + w * .5, yy), (x + w * .5 + r * .25, yy - r * .17), (x - w * .5 + r * .25, yy - r * .17)], False)
            rr(s, cc, x, yy + h * .06, w, h * .13, 2, False)
        poli(s, (250, 215, 130), [(x - w * .5, y - h * .45), (x + w * .5, y - h * .45), (x + w * .5 + r * .25, y - h * .62), (x - w * .5 + r * .25, y - h * .62)])
        poli(s, (250, 210, 90), [(x - w * .5 + r * .1, y - h * .47), (x + w * .5 + r * .1, y - h * .47), (x + w * .5 + r * .2, y - h * .6), (x - w * .5 + r * .3, y - h * .6)], False)
        for dx in (-.25, .1, .3):
            c(s, (225, 70, 55), x + dx * r + r * .1, y - h * .54, r * .06, False)
        e(s, (80, 170, 70), x + r * .2, y - h * .54, r * .1, r * .05, False)
        return
    if _tiene(rec, "ravioles", "raviol", "noquis"):
        for dx, dy in ((-.42, .0), (.0, .22), (.42, .0), (.0, -.2)):
            x, y = fx + dx * r, fy + dy * r
            rr(s, (250, 220, 140), x, y, r * .55, r * .4, r * .08, (205, 165, 95), 2)
            for k in range(5):
                c(s, (205, 165, 95), x - r * .22 + k * r * .11, y - r * .19, max(1, r * .02), False)
                c(s, (205, 165, 95), x - r * .22 + k * r * .11, y + r * .19, max(1, r * .02), False)
        e(s, salsa, fx, fy + r * .05, r * .55, r * .22, False)
        for k in range(5):
            c(s, (255, 250, 235), fx - r * .2 + k * r * .1, fy + r * .03, r * .03, False)
        e(s, (80, 170, 70), fx + r * .1, fy - r * .02, r * .2, r * .1, False)
        return
    amar = (248, 218, 130)
    rng = Random(var)
    e(s, oscurecer(amar, .3), fx, fy + r * .15, r * 1.3, r * .55, False)
    for i in range(16):                                                                   # nido de fideos
        a0 = rng.uniform(0, 6.28)
        pts = []
        for j in range(18):
            a = a0 + j * .42
            dd = .55 + .04 * j - .015 * j * j / 6
            pts.append((fx + math.cos(a) * r * .5 * dd * 1.25, fy + r * .05 + math.sin(a) * r * .5 * dd * .55 - j * r * .01))
        pygame.draw.lines(s, oscurecer(amar, .3), False, [(int(a), int(b)) for a, b in pts], 6)
        pygame.draw.lines(s, amar if i % 2 else aclarar(amar, .2), False, [(int(a), int(b)) for a, b in pts], 4)
    e(s, oscurecer(salsa, .25), fx, fy - r * .1, r * .78, r * .42, False)
    e(s, salsa, fx, fy - r * .12, r * .72, r * .36, False)
    for k in range(5):
        c(s, aclarar(salsa, .3), fx - r * .25 + k * r * .13, fy - r * .14 + (k % 2) * r * .05, r * .06, False)
    e(s, aclarar(salsa, .55), fx - r * .2, fy - r * .22, r * .22, r * .07, False)
    for k in range(7):                                                                    # queso rallado
        lin(s, (255, 240, 170), (fx - r * .3 + k * r * .09, fy - r * .08 - (k % 3) * 3), (fx - r * .22 + k * r * .09, fy - r * .02 - (k % 3) * 3), 2)
    for dx in (-.08, .1):
        e(s, (80, 175, 70), fx + dx * r, fy - r * .34, r * .12, r * .06, oscurecer((80, 175, 70), .3), 1)
    lin(s, (210, 215, 230), (fx + r * .75, fy + r * .22), (fx + r * 1.0, fy - r * .05), max(3, int(r * .06)))   # tenedor


# ----------------------------------------------------------------------------- arroces
def _arroz(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    base = tuple(int(v * .45 + 255 * .55) for v in col)
    rng = Random(var)
    frito = _tiene(rec, "chaufa", "paella", "frito", "pilaf")
    if frito:
        base = aclarar(col, .35)
    e(s, oscurecer(base, .3), fx, fy + r * .1, r * 1.35, r * .62, False)
    for i in range(110):
        a = rng.uniform(0, 6.28)
        d = math.sqrt(rng.uniform(0, 1))
        x = fx + math.cos(a) * d * r * .62
        y = fy + r * .02 + math.sin(a) * d * r * .3 - (1 - d * d) * r * .22
        pygame.draw.ellipse(s, oscurecer(base, .3), (int(x - 5), int(y - 3), 11, 7))
        pygame.draw.ellipse(s, base if i % 3 else aclarar(base, .3), (int(x - 4), int(y - 3), 9, 6))
    for i in range(16):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(.2, .9)
        x, y = fx + math.cos(a) * r * .55 * d, fy - r * .08 + math.sin(a) * r * .22 * d
        k = i % 4
        if k == 0:
            c(s, (95, 190, 80), x, y, r * .06, False)
        elif k == 1:
            rr(s, (250, 150, 40), x, y, r * .1, r * .1, 2, False)
        elif k == 2 and frito:
            rr(s, (230, 70, 60), x, y, r * .2, r * .06, 2, False)
        else:
            c(s, (250, 215, 80), x, y, r * .05, False)
    if frito:
        for dx, ang in ((-.35, 0), (.3, 1)):
            x, y = fx + dx * r, fy - r * .12
            for j in range(5):
                c(s, (250, 140, 100), x + math.cos(j * .6 + ang) * r * .13, y + math.sin(j * .6 + ang) * r * .13, r * (.075 - j * .008))
        e(s, (60, 150, 80), fx + r * .5, fy - r * .1, r * .15, r * .06, False)
    e(s, (255, 255, 255), fx - r * .2, fy - r * .22, r * .2, r * .06, False)


# ----------------------------------------------------------------------------- pescados y mariscos
def _camaron(s, x, y, r, col, flip=1):
    n = 7
    for j in range(n):
        a = -1.0 + j * .5
        px = x + flip * math.cos(a) * r * .5
        py = y + math.sin(a) * r * .5
        c(s, col, px, py, r * (.2 - j * .012))
        lin(s, oscurecer(col, .25), (px - r * .1, py - r * .08), (px + r * .1, py + r * .08), 2)
    ex = x + flip * math.cos(-1.0 + 6 * .5) * r * .5
    ey = y + math.sin(-1.0 + 6 * .5) * r * .5
    for k in (-1, 0, 1):
        e(s, aclarar(col, .1), ex + flip * r * .1, ey + k * r * .1, r * .18, r * .09, oscurecer(col, .3), 1)
    c(s, (30, 30, 40), x + flip * r * .42, y - r * .55, max(1, r * .035), False)
    lin(s, oscurecer(col, .2), (x + flip * r * .45, y - r * .6), (x + flip * r * .75, y - r * .9), 2)


def _pescado(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    pal = _tiene(rec, "langostino", "camaron")
    if pal:
        for dx, dy, fl in ((-.35, .02, 1), (.2, .0, -1), (0, .25, 1)):
            _camaron(s, fx + dx * r, fy + dy * r + r * .1, r * .68, (250, 150, 105), fl)
    elif _tiene(rec, "calamar", "jalea", "chicharron"):
        rng = Random(var)
        for i in range(8):
            a = i * 1.2
            x, y = fx + math.cos(a) * r * .5 * (.4 + (i % 3) * .25), fy + math.sin(a) * r * .22 * (.4 + (i % 3) * .25)
            c(s, (225, 160, 70), x, y, r * .22, (170, 110, 40))
            c(s, (255, 255, 255), x, y, r * .1, (200, 185, 170), 1)
            c(s, (240, 190, 100), x - r * .08, y - r * .08, r * .05, False)
    elif _tiene(rec, "ceviche", "cebiche", "tiradito"):
        rng = Random(var)
        for i in range(14):
            a = rng.uniform(0, 6.28)
            d = rng.uniform(.1, .9)
            x, y = fx + math.cos(a) * r * .55 * d, fy + math.sin(a) * r * .25 * d - (1 - d) * r * .1
            rr(s, (255, 248, 240), x, y, r * .2, r * .18, 3, (225, 205, 195), 1)
        for i in range(6):
            a = i * 1.3
            pygame.draw.arc(s, (210, 90, 150), pygame.Rect(int(fx + math.cos(a) * r * .35 - r * .1), int(fy + math.sin(a) * r * .14 - r * .1 - r * .1),
                                                          int(r * .24), int(r * .2)), 0.3, 3.0, 3)
        for i in range(5):
            c(s, (250, 205, 60), fx - r * .4 + i * r * .2, fy + r * .12, r * .05, False)
        c(s, (130, 205, 80), fx + r * .6, fy + r * .1, r * .09, (80, 150, 50))
        c(s, (180, 235, 120), fx + r * .6, fy + r * .1, r * .06, False)
    elif _tiene(rec, "sushi"):
        for dx, dy in ((-.45, .05), (.0, .2), (.45, .02)):
            x, y = fx + dx * r, fy + dy * r
            rr(s, (250, 250, 250), x, y, r * .4, r * .42, r * .1, (205, 205, 215), 1)
            e(s, (255, 255, 255), x, y - r * .2, r * .4, r * .18, (205, 205, 215), 1)
            rr(s, (35, 45, 40), x, y, r * .4, r * .12, 2, False)
            c(s, (250, 140, 90), x, y - r * .2, r * .07, False)
        e(s, (250, 140, 100), fx, fy - r * .22, r * .5, r * .2, (200, 90, 60), 1)
        rr(s, (255, 250, 245), fx, fy - r * .08, r * .5, r * .12, 3, (205, 200, 195), 1)
    else:
        # pescado entero a la plancha
        x, y = fx, fy - r * .02
        L = r * .75
        poli(s, oscurecer(col, .1), [(x + L * .8, y), (x + L * 1.25, y - r * .3), (x + L * 1.25, y + r * .3)])
        e(s, col, x, y, L * 2.0, r * .72, oscurecer(col, .35), 2)
        e(s, aclarar(col, .3), x - L * .1, y + r * .08, L * 1.4, r * .35, False)
        poli(s, oscurecer(col, .12), [(x - L * .2, y - r * .3), (x + L * .3, y - r * .3), (x + L * .1, y - r * .5)])
        for k in range(-2, 4):
            lin(s, oscurecer(col, .35), (x + k * L * .22 - r * .08, y - r * .22), (x + k * L * .22 + r * .08, y + r * .22), 3)
        c(s, (255, 255, 255), x - L * .72, y - r * .08, r * .1, INK, 1)
        c(s, (25, 25, 40), x - L * .72, y - r * .08, r * .05, False)
        pygame.draw.arc(s, oscurecer(col, .4), pygame.Rect(int(x - L * .95), int(y - r * .05), int(r * .3), int(r * .2)), 3.4, 5.5, 2)
    # limon y perejil
    lx, ly = fx + r * .66, fy + r * .27
    c(s, (240, 225, 90), lx, ly, r * .12, (200, 180, 40))
    c(s, (252, 245, 160), lx, ly, r * .09, False)
    for k in range(6):
        lin(s, (225, 205, 70), (lx, ly), (lx + math.cos(k * 1.05) * r * .08, ly + math.sin(k * 1.05) * r * .08), 1)
    e(s, (80, 170, 70), fx - r * .62, fy + r * .3, r * .11, r * .055, False)
    e(s, (100, 190, 80), fx - r * .54, fy + r * .33, r * .09, r * .05, False)


# ----------------------------------------------------------------------------- empanadas y rollos
def _empanada(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    rollo = _tiene(rec, "rollo", "rollos", "wrap", "taco", "tacos", "burrito", "enrollado", "enrollados", "rollito", "rollitos")
    dorado = col
    if rollo:
        for dx, dy, ang in ((-.1, .22, 12), (.0, -.05, 5)):
            x, y = fx + dx * r, fy + dy * r
            L, H = r * 1.25, r * .42
            rr(s, oscurecer(dorado, .3), x, y + 3, L, H, H * .5, False)
            rr(s, dorado, x, y, L, H, H * .5, oscurecer(dorado, .35), 2)
            lin(s, aclarar(dorado, .5), (x - L * .38, y - H * .22), (x + L * .3, y - H * .22), max(2, int(r * .05)))
            for k in range(3):
                lin(s, oscurecer(dorado, .3), (x - L * .2 + k * L * .22, y - H * .25), (x - L * .15 + k * L * .22, y + H * .3), 2)
        x, y = fx + r * .55, fy + r * .05                                                    # corte con relleno
        c(s, aclarar(dorado, .35), x, y, r * .32, oscurecer(dorado, .35))
        for i, cc in enumerate(((250, 235, 190), (235, 90, 75), (110, 190, 90))):
            pygame.draw.circle(s, cc, (int(x), int(y)), int(r * (.24 - i * .075)), max(2, int(r * .045)))
        c(s, (110, 190, 90), x, y, r * .04, False)
        return
    for dx, dy, esc in ((-.5, .12, .85), (.5, .12, .85), (0, -.1, 1.0)):
        x, y = fx + dx * r, fy + dy * r
        R = r * .55 * esc
        n = 20
        pts = [(x + math.cos(math.pi * (1 + i / n)) * R, y + R * .45 + math.sin(math.pi * (1 + i / n)) * R * .95) for i in range(n + 1)]
        poli(s, oscurecer(dorado, .4), [(x - R, y + R * .55)] + [(a, b + 3) for a, b in pts] + [(x + R, y + R * .55)], False)
        poli(s, dorado, [(x - R, y + R * .45)] + pts + [(x + R, y + R * .45)])
        poli(s, aclarar(dorado, .3), [(a, b + 4) for a, b in pts[3:-3]] + [(x + R * .62, y + R * .3), (x - R * .62, y + R * .3)], False)
        e(s, dorado, x, y + R * .45, R * 2, R * .3, oscurecer(dorado, .35), 2)
        for i in range(9):
            c(s, oscurecer(dorado, .35), x - R * .9 + i * R * .225, y + R * .45, max(1, R * .07), False)
        e(s, (255, 235, 170), x - R * .1, y - R * .2, R * .6, R * .2, False)
        c(s, oscurecer(dorado, .25), x + R * .35, y - R * .05, max(1, R * .06), False)


# ----------------------------------------------------------------------------- tartas y pizzas
def _tarta(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    if _tiene(rec, "pizza", "pizzas", "calzone"):
        w, h = r * 1.55, r * .78
        e(s, (190, 130, 60), fx, fy + r * .14, w, h, False)
        e(s, (230, 175, 95), fx, fy + r * .08, w, h, (180, 120, 55), 2)
        e(s, (220, 70, 50), fx, fy + r * .07, w * .84, h * .82, False)
        e(s, (252, 214, 95), fx, fy + r * .06, w * .8, h * .78, False)
        for a, d in ((.3, .5), (1.6, .42), (2.8, .55), (4.1, .4), (5.3, .5), (.9, .12)):
            x, y = fx + math.cos(a) * w * .3 * d * 1.6, fy + r * .06 + math.sin(a) * h * .3 * d * 1.6
            e(s, (205, 60, 50), x, y, r * .26, r * .17, (150, 40, 35), 1)
            c(s, (235, 110, 95), x - r * .05, y - r * .03, r * .03, False)
        for x, y in ((fx + w * .12, fy - r * .18), (fx - w * .28, fy + r * .15)):
            e(s, (80, 175, 70), x, y, r * .15, r * .08, False)
        # porcion cortada con hilos de queso
        for k in (-1, 1):
            a = -.6 + k * 0
        lin(s, (190, 130, 60), (fx, fy + r * .07), (fx + w * .5, fy + r * .07 - h * .12), 2)
        lin(s, (190, 130, 60), (fx, fy + r * .07), (fx + w * .42, fy + r * .07 + h * .3), 2)
        lin(s, (190, 130, 60), (fx, fy + r * .07), (fx - w * .5, fy + r * .07 + h * .02), 2)
        lin(s, (190, 130, 60), (fx, fy + r * .07), (fx - w * .2, fy + r * .07 - h * .46), 2)
        for k in range(3):
            lin(s, (255, 235, 140), (fx + w * .3 + k * 3, fy + r * .0 + k * 2), (fx + w * .32 + k * 4, fy + r * .22 + k * 3), 2)
        return
    # tarta con borde ondulado y rejilla
    w, h = r * 1.5, r * .76
    e(s, (150, 100, 55), fx, fy + r * .2, w, h, False)
    rr(s, (215, 160, 85), fx, fy + r * .12, w, r * .22, r * .1, False)
    e(s, (215, 160, 85), fx, fy + r * .02, w, h, (165, 110, 55), 2)
    for i in range(22):
        a = i / 22 * 6.28
        c(s, (235, 185, 105), fx + math.cos(a) * w * .5, fy + r * .02 + math.sin(a) * h * .5, r * .06, False)
    relleno = col
    e(s, relleno, fx, fy + r * .02, w * .82, h * .78, oscurecer(relleno, .3), 2)
    e(s, aclarar(relleno, .35), fx - w * .12, fy - r * .1, w * .35, h * .2, False)
    if _tiene(rec, "quiche"):
        for dx, dy in ((-.2, 0), (.2, .05), (0, -.1)):
            c(s, (95, 175, 80), fx + dx * w, fy + dy * h, r * .06, False)
    else:
        for k in range(-2, 3):                                                                # rejilla
            lin(s, (225, 170, 95), (fx + k * w * .17 - w * .15, fy - h * .38), (fx + k * w * .17 + w * .15, fy + h * .4), max(3, int(r * .07)))
            lin(s, (225, 170, 95), (fx + k * w * .17 + w * .15, fy - h * .38), (fx + k * w * .17 - w * .15, fy + h * .4), max(3, int(r * .07)))
        e(s, (165, 110, 55), fx, fy + r * .02, w * .84, h * .8, (165, 110, 55), 2) if False else None
        pygame.draw.ellipse(s, (165, 110, 55), pygame.Rect(int(fx - w * .41), int(fy + r * .02 - h * .39), int(w * .82), int(h * .78)), 2)
    c(s, (255, 255, 255), fx + w * .3, fy - r * .22, r * .05, False)


# ----------------------------------------------------------------------------- galletas, tortas y postres
def _estrella_pts(x, y, R, n=5, f=.45, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        rad = R if i % 2 == 0 else R * f
        a = rot + i * math.pi / n
        pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad * .8))
    return pts


def _postre(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    rng = Random(var)
    if _tiene(rec, "galleta", "galletas", "cookie", "cookies", "alfajor", "alfajores"):
        dorado = col
        spots = ((-.5, .12, "e"), (.5, .1, "c"), (-.1, -.08, "e"), (.15, .28, "c"))
        for dx, dy, forma in spots:
            x, y = fx + dx * r, fy + dy * r
            if forma == "e":
                pts = _estrella_pts(x, y, r * .45, 5, .5)
                poli(s, oscurecer(dorado, .35), [(a, b + 3) for a, b in pts], False)
                poli(s, dorado, pts, oscurecer(dorado, .35), 2)
                poli(s, aclarar(dorado, .25), _estrella_pts(x, y - 1, r * .3, 5, .5), False)
                c(s, (255, 235, 245), x, y, r * .06, (240, 150, 180), 1)
            else:
                e(s, oscurecer(dorado, .35), x, y + 3, r * .8, r * .5, False)
                e(s, dorado, x, y, r * .8, r * .5, oscurecer(dorado, .35), 2)
                e(s, aclarar(dorado, .25), x, y - 1, r * .55, r * .3, False)
                for k in range(5):
                    a = k * 1.3 + dx
                    c(s, (100, 60, 40), x + math.cos(a) * r * .22, y + math.sin(a) * r * .12, r * .045, False)
        for k in range(10):
            c(s, [(250, 120, 160), (110, 190, 240), (250, 220, 70)][k % 3], fx + rng.uniform(-.8, .8) * r, fy + rng.uniform(-.1, .45) * r, max(1, r * .025), False)
        return
    if _tiene(rec, "flan", "gelatina", "mousse", "mazamorra"):
        x, y = fx, fy + r * .05
        caramelo = (190, 100, 30)
        e(s, caramelo, x, y + r * .12, r * 1.3, r * .5, False)
        e(s, aclarar(caramelo, .2), x, y + r * .1, r * 1.2, r * .42, False)
        poli(s, (250, 215, 110), [(x - r * .5, y + r * .02), (x - r * .3, y - r * .4), (x + r * .3, y - r * .4), (x + r * .5, y + r * .02)], False)
        e(s, (250, 215, 110), x, y + r * .02, r * 1.0, r * .35, False)
        e(s, (255, 230, 140), x, y - r * .4, r * .6, r * .25, False)
        e(s, caramelo, x, y - r * .4, r * .5, r * .2, False)
        for k in (-.15, 0, .2):
            lin(s, caramelo, (x + k * r, y - r * .38), (x + k * r + r * .05, y - r * .05), max(2, int(r * .05)))
        e(s, (255, 245, 190), x - r * .25, y - r * .12, r * .1, r * .3, False)
        c(s, (230, 50, 70), x, y - r * .6, r * .09, (160, 30, 45))
        return
    if _tiene(rec, "helado"):
        x, y = fx, fy
        poli(s, (225, 170, 90), [(x - r * .3, y - r * .1), (x + r * .3, y - r * .1), (x, y + r * .5)])
        for k in range(-2, 3):
            lin(s, (180, 120, 50), (x + k * r * .12, y - r * .1), (x + k * r * .04, y + r * .35), 2)
        c(s, col, x, y - r * .3, r * .35, oscurecer(col, .3))
        c(s, (255, 220, 230), x, y - r * .72, r * .3, (225, 150, 170))
        brillo(s, x - r * .1, y - r * .8, r * .06)
        c(s, (230, 50, 70), x, y - r * 1.05, r * .07, (160, 30, 45))
        return
    if _tiene(rec, "cupcake", "cupcakes", "muffin", "queque"):
        x, y = fx, fy + r * .05
        poli(s, (240, 130, 150), [(x - r * .4, y - r * .1), (x + r * .4, y - r * .1), (x + r * .3, y + r * .4), (x - r * .3, y + r * .4)])
        for k in range(-2, 3):
            lin(s, (255, 190, 205), (x + k * r * .15, y - r * .08), (x + k * r * .11, y + r * .38), 2)
        for i, (w, dy) in enumerate(((.95, -.15), (.7, -.4), (.45, -.62))):
            e(s, col if i % 2 == 0 else aclarar(col, .25), x, y + dy * r, r * w, r * .3, oscurecer(col, .35), 2)
        c(s, (230, 50, 70), x, y - r * .85, r * .1, (160, 30, 45))
        return
    if _tiene(rec, "brownie", "turron"):
        for i in range(3):
            x, y = fx - r * .3 + i * r * .15, fy + r * .15 - i * r * .24
            rr(s, (110, 65, 40), x, y + r * .05, r * .75, r * .35, r * .06)
            poli(s, (140, 85, 55), [(x - r * .37, y - r * .12), (x + r * .37, y - r * .12), (x + r * .45, y - r * .28), (x - r * .29, y - r * .28)])
            for k in range(4):
                c(s, (190, 135, 95), x - r * .25 + k * r * .15, y + r * .05, r * .025, False)
        return
    # torta de capas
    x, y = fx, fy - r * .12
    esponja = (240, 200, 120)
    crema = (255, 245, 225)
    glas = col
    W = r * .66
    for i in range(2):
        yy = y + r * .22 - i * r * .38
        e(s, oscurecer(esponja, .25), x, yy + r * .26, W * 2, r * .52, False)
        rr(s, esponja, x, yy + r * .1, W * 2, r * .32, 2, False)
        e(s, esponja, x, yy + r * .26 - r * .0, W * 2, r * .52, oscurecer(esponja, .3), 1) if False else None
        rr(s, crema, x, yy - r * .06, W * 2, r * .1, 2, False)
    rr(s, esponja, x, y - r * .15, W * 2, r * .36, 2, False)
    e(s, glas, x, y - r * .5, W * 2, r * .5, oscurecer(glas, .3), 2)
    e(s, aclarar(glas, .3), x - W * .1, y - r * .53, W * 1.2, r * .3, False)
    for k in range(-3, 4):                                                                    # gotas de glaseado
        h = r * (.2 + .12 * ((k * 5) % 3))
        rr(s, glas, x + k * W * .27, y - r * .38 + h * .35, W * .2, h, W * .1, False)
    pygame.draw.arc(s, aclarar(glas, .5), pygame.Rect(int(x - W), int(y - r * .72), int(W * 2), int(r * .5)), 3.5, 5.4, 2)
    for k, ang in enumerate((.5, 2.1, 3.7, 5.2)):
        c(s, (250, 250, 250), x + math.cos(ang) * W * .55, y - r * .5 + math.sin(ang) * r * .13, r * .05, False)
    c(s, (230, 50, 70), x, y - r * .62, r * .12, (160, 30, 45))
    brillo(s, x - r * .03, y - r * .67, r * .035)


# ----------------------------------------------------------------------------- panqueques
def _panqueque(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    cobertura = (200, 50, 85)
    if _tiene(rec, "miel"):
        cobertura = (235, 160, 30)
    if _tiene(rec, "chocolate", "cacao"):
        cobertura = (110, 65, 40)
    dorado = col
    if _tiene(rec, "crepe", "crepes"):
        for dx, dy in ((-.35, .1), (.35, .0)):
            x, y = fx + dx * r, fy + dy * r
            poli(s, oscurecer(dorado, .3), [(x - r * .5, y + r * .32), (x + r * .5, y + r * .32), (x, y - r * .4)], False)
            poli(s, dorado, [(x - r * .46, y + r * .28), (x + r * .46, y + r * .28), (x, y - r * .36)], oscurecer(dorado, .35), 2)
            poli(s, aclarar(dorado, .3), [(x - r * .3, y + r * .22), (x, y + r * .22), (x - r * .05, y - r * .1)], False)
            lin(s, cobertura, (x - r * .25, y + r * .1), (x + r * .2, y - r * .05), max(3, int(r * .06)))
        for dx, dy in ((.0, .25), (.1, -.1)):
            c(s, (230, 55, 75), fx + dx * r, fy + dy * r, r * .07, (160, 30, 45))
        return
    for i in range(3):
        y = fy + r * .26 - i * r * .26
        w = r * (1.35 - i * .05)
        rr(s, oscurecer(dorado, .3), fx, y + r * .06, w, r * .26, r * .12, False)
        rr(s, aclarar(dorado, .1), fx, y + r * .02, w, r * .26, r * .12, oscurecer(dorado, .35), 2)
        rr(s, (205, 145, 70), fx, y - r * .06, w * .96, r * .06, r * .03, False)
    ytop = fy - r * .28
    e(s, (215, 155, 75), fx, ytop, r * 1.3, r * .5, oscurecer(dorado, .35), 2)
    e(s, cobertura, fx, ytop, r * .9, r * .34, False)
    e(s, aclarar(cobertura, .4), fx - r * .2, ytop - r * .06, r * .3, r * .08, False)
    for k in (-.4, -.05, .35):                                                                # goteo
        h = r * (.22 + .12 * abs(k))
        rr(s, cobertura, fx + k * r * 1.1, ytop + r * .22 + h * .3, r * .1, h, r * .05, False)
        c(s, cobertura, fx + k * r * 1.1, ytop + r * .22 + h * .8, r * .06, False)
    rr(s, (255, 240, 150), fx + r * .0, ytop - r * .05, r * .26, r * .16, r * .04, oscurecer((255, 240, 150), .25), 1)
    for dx in (-.35, .4):
        c(s, (230, 55, 75), fx + dx * r, ytop - r * .02, r * .065, (160, 30, 45))


# ----------------------------------------------------------------------------- huevos
def _huevo_frito(s, x, y, R):
    rng = Random(int(x * 7 + y * 3))
    for i in range(8):
        a = i / 8 * 6.28
        e(s, (255, 253, 248), x + math.cos(a) * R * .5, y + math.sin(a) * R * .35, R * rng.uniform(.8, 1.0), R * rng.uniform(.5, .65), (225, 215, 195), 1)
    e(s, (255, 253, 248), x, y, R * 1.3, R * .9, False)
    c(s, (250, 185, 35), x - R * .05, y - R * .05, R * .36, (215, 140, 20))
    brillo(s, x - R * .18, y - R * .18, R * .09)


def _huevos(s, cx, cy, r, col, rec, var, cont):
    fx, fy = _plato(s, cx, cy, r, cont)
    if _tiene(rec, "tortilla") and not _tiene(rec, "tortillas"):
        x, y = fx, fy + r * .05
        w = r * 1.5
        dorado = (240, 195, 80)
        e(s, (190, 135, 50), x, y + r * .2, w, r * .72, False)
        rr(s, (225, 170, 60), x, y + r * .0, w, r * .42, r * .08, False)
        e(s, (225, 170, 60), x, y + r * .2, w, r * .72, False)
        e(s, dorado, x, y - r * .1, w, r * .72, (190, 135, 50), 2)
        e(s, aclarar(dorado, .3), x - r * .1, y - r * .14, w * .65, r * .4, False)
        poli(s, (250, 232, 150), [(x, y - r * .1), (x + w * .5, y - r * .12), (x + w * .46, y + r * .2), (x + w * .22, y + r * .3)], False)   # cuña
        for k in range(4):
            c(s, (225, 195, 90), x + w * .12 + k * w * .09, y + r * .05 + (k % 2) * r * .06, r * .06, False)
        for k in range(3):
            c(s, (105, 175, 75), x - w * .25 + k * w * .12, y - r * .15 + (k % 2) * r * .05, r * .035, False)
        return
    if _tiene(rec, "omelette", "omelet"):
        x, y = fx, fy
        n = 20
        pts = [(x + math.cos(math.pi * (1 + i / n)) * r * .78, y + r * .22 + math.sin(math.pi * (1 + i / n)) * r * .55) for i in range(n + 1)]
        dorado = (250, 210, 80)
        poli(s, (205, 155, 50), [(x - r * .78, y + r * .3)] + [(a, b + 4) for a, b in pts] + [(x + r * .78, y + r * .3)], False)
        poli(s, dorado, [(x - r * .78, y + r * .22)] + pts + [(x + r * .78, y + r * .22)], (205, 155, 50), 2)
        e(s, dorado, x, y + r * .22, r * 1.56, r * .35, (205, 155, 50), 2)
        e(s, (255, 235, 150), x - r * .2, y - r * .08, r * .55, r * .14, False)
        for k, cc in enumerate(((95, 175, 80), (230, 70, 60), (95, 175, 80), (250, 150, 40))):
            c(s, cc, x - r * .4 + k * r * .22, y + r * .22, r * .06, False)
        for k in range(6):
            c(s, (80, 160, 70), x - r * .3 + k * r * .12, y - r * .02 + (k % 2) * r * .05, max(1, r * .025), False)
        return
    if _tiene(rec, "revuelto", "revueltos"):
        rng = Random(var)
        for i in range(14):
            a = rng.uniform(0, 6.28)
            d = rng.uniform(.1, .9)
            x, y = fx + math.cos(a) * r * .55 * d, fy + math.sin(a) * r * .22 * d - (1 - d) * r * .12
            e(s, (252, 220, 70), x, y, r * .3, r * .2, (215, 170, 30), 1)
            e(s, (255, 240, 140), x - r * .05, y - r * .04, r * .12, r * .06, False)
        for k in range(5):
            c(s, (90, 175, 70), fx - r * .3 + k * r * .15, fy - r * .1 + (k % 2) * r * .1, max(1, r * .03), False)
        return
    # huevos fritos con tostada
    _rebanada(s, fx + r * .4, fy + r * .05, r * .9, r * .85, (200, 130, 65), (246, 214, 150), -8)
    _huevo_frito(s, fx - r * .3, fy + r * .05, r * .62)
    _huevo_frito(s, fx + r * .3, fy - r * .08, r * .5)
    for k in range(6):
        c(s, (60, 50, 50), fx - r * .45 + k * r * .15, fy + r * .0 + (k % 2) * r * .1, max(1, r * .02), False)


# ----------------------------------------------------------------------------- generico (por recipiente)
def _generico(s, cx, cy, r, col, rec, var, cont):
    rng = Random(var)
    claro, osc = aclarar(col, .35), oscurecer(col, .3)
    if cont == "vaso":
        _jugo(s, cx, cy, r, col, rec, var, cont)
        return
    if cont == "cuenco":
        yb, w, bh = _tazon_3q(s, cx, cy + r * .12, r, (250, 250, 255), col, 1.8, .85)
        e(s, osc, cx, yb + 2, w * .9, bh * .85, False)
        e(s, col, cx, yb, w * .86, bh * .75, False)
        for i in range(12):
            a = rng.uniform(0, 6.28)
            d = rng.uniform(.1, .85)
            c(s, claro if i % 2 else osc, cx + math.cos(a) * w * .4 * d, yb + math.sin(a) * bh * .35 * d, r * .07, False)
        e(s, claro, cx - w * .2, yb - bh * .15, w * .25, bh * .15, False)
        pygame.draw.ellipse(s, (170, 160, 150), pygame.Rect(int(cx - w / 2), int(yb - bh / 2), int(w), int(bh)), 3)
        return
    fx, fy = _plato(s, cx, cy, r, cont)
    if cont == "bandeja":
        for dx, dy in ((-.5, .0), (0, .1), (.5, 0)):
            x, y = fx + dx * r, fy + dy * r
            rr(s, osc, x, y + 3, r * .6, r * .38, r * .12, False)
            rr(s, col, x, y, r * .6, r * .38, r * .12, osc, 2)
            rr(s, claro, x - r * .05, y - r * .06, r * .35, r * .1, r * .04, False)
        return
    e(s, osc, fx, fy + r * .1, r * 1.1, r * .55, False)
    for i in range(10):                                                                       # monticulo
        a = i / 10 * 6.28
        x, y = fx + math.cos(a) * r * .4, fy + r * .02 + math.sin(a) * r * .15
        c(s, col if i % 2 else claro, x, y, r * .22, osc, 1)
    c(s, col, fx, fy - r * .18, r * .38, osc, 2)
    e(s, claro, fx - r * .1, fy - r * .28, r * .25, r * .12, False)
    for dx, dy in ((-.35, .15), (.4, .0), (.1, .25)):
        e(s, (95, 180, 80), fx + dx * r, fy + dy * r, r * .2, r * .1, oscurecer((95, 180, 80), .3), 1)
    for k in range(4):
        c(s, (250, 215, 90), fx - r * .3 + k * r * .2, fy + r * .2, r * .04, False)


_DIBUJOS = {"jugos": _jugo, "panes": _pan, "ensaladas": _ensalada, "sopas": _sopa, "pastas": _pasta,
            "arroces": _arroz, "pescados": _pescado, "empanadas": _empanada, "tartas": _tarta,
            "postres": _postre, "panqueques": _panqueque, "huevos": _huevos, "generico": _generico}

# vapor: tipos calientes
_CALIENTES = ("sopas", "pastas", "arroces", "pescados", "empanadas", "tartas", "huevos", "panqueques", "generico")

# color propio de algunos tipos cuando la receta trae el color por omision (para que se reconozcan)
_cache = {}
LIMITE_CACHE = 120


def _receta(r):
    if isinstance(r, dict):
        return r
    try:
        import cocina_datos
        rec = cocina_datos.POR_ID.get(r)
        if rec is not None:
            return rec
    except Exception:
        pass
    return {"id": str(r), "nombre": str(r).replace("_", " ")}


def _vapor(p, x, y, r, t):
    for i in range(3):
        ph = (t * .6 + i / 3) % 1.0
        x0 = x + (i - 1) * r * .38
        pts = [(x0 + math.sin(ph * 6 + i + j) * r * .06, y - ph * r * .35 - j * r * .1) for j in range(4)]
        sup = pygame.Surface((int(r * 3), int(r * 3)), pygame.SRCALPHA)
        o = (x - r * 1.5, y - r * 1.5)
        pygame.draw.lines(sup, (255, 255, 255, int(200 * (1 - ph))), False, [(int(a - o[0]), int(b - o[1])) for a, b in pts], max(2, int(r * .06)))
        p.blit(sup, (int(o[0]), int(o[1])))


ESCALA = 1.2          # la comida se dibuja un poco mas grande para llenar el recuadro
ESCALA_VASO = 1.08


def _bebida_rec(b, rec):
    """Receta (dict) del vaso de una clave 'bebida' (id, nombre o dict)."""
    d = None
    try:
        d = dict(_receta(b)) if not isinstance(b, str) or b else None
    except Exception:
        d = None
    if not d:
        d = {"id": "jugo", "nombre": "jugo"}
    d["cont"] = "vaso"
    d["tipo"] = "jugos"
    if not d.get("color"):
        d["color"] = (250, 170, 40)
    return d


def _dibujar(rec, tam):
    S = int(tam * 1.6) + 4
    s = pygame.Surface((S, S), pygame.SRCALPHA)
    r = tam / 2
    col = tuple(rec.get("color") or (240, 190, 100))[:3]
    tipo = tipo_de(rec)
    var = zlib.crc32(str(rec.get("id", rec.get("nombre", ""))).encode("utf-8", "ignore"))
    if tipo == "jugos":                                    # bebida sola, sin plato
        _jugo(s, S / 2, S / 2 + r * .08, r * ESCALA_VASO, col, rec, var, "vaso")
        return s, tipo
    beb = rec.get("bebida")
    if beb:                                                # bandeja con plato + vaso al costado
        k = .7
        _plato(s, S / 2, S / 2 - r * .1, r * k, "bandeja_ancha")
        comida = pygame.Surface((S, S), pygame.SRCALPHA)
        cont = rec.get("cont", "plato")
        _DIBUJOS[tipo](comida, S / 2, S / 2, r * .78 * k, col, rec, var, "plato" if cont in ("vaso", "bandeja") else cont)
        s.blit(comida, (-int(r * .42 * k), int(r * .02)))
        vaso = pygame.Surface((S, S), pygame.SRCALPHA)
        br = _bebida_rec(beb, rec)
        _jugo(vaso, S / 2, S / 2, r * .62 * k, tuple(br["color"])[:3], br, 7, "vaso")
        s.blit(vaso, (int(r * .98 * k), int(r * .08)))
        return s, tipo
    _DIBUJOS[tipo](s, S / 2, S / 2 - r * .05, r * (1.02 if tipo == "postres" else ESCALA), col, rec, var, rec.get("cont", "plato"))
    return s, tipo


def dibujar_plato(p, receta, x, y, tam=120, t=0.0):
    """Dibuja el plato terminado de una receta (id o dict) centrado en (x, y), cabe en tam x tam aprox."""
    try:
        rec = _receta(receta)
        tam = max(16, int(tam))
        clave = (str(rec.get("id", rec.get("nombre", ""))), tuple(rec.get("color") or ()), rec.get("cont"), rec.get("tipo"), tam)
        hit = _cache.get(clave)
        if hit is None:
            if len(_cache) > LIMITE_CACHE:
                _cache.clear()
            hit = _cache[clave] = _dibujar(rec, tam)
        s, tipo = hit
        p.blit(s, s.get_rect(center=(int(x), int(y))))
        if t and tipo in _CALIENTES:
            _vapor(p, x, y - tam * .3, tam / 2, t)
    except Exception:
        try:
            pygame.draw.ellipse(p, (250, 250, 255), (int(x - tam / 2), int(y - tam / 4), int(tam), int(tam / 2)))
            pygame.draw.circle(p, (240, 190, 100), (int(x), int(y)), max(4, int(tam / 5)))
        except Exception:
            pass
