"""Dibujos hechos con codigo: criaturas, peces y otros personajes (todos originales)."""

import math

import pygame

from nucleo import aclarar, oscurecer
import arte_mar

# id: (nombre, rareza 1-3, color, vientre, forma, orejas, cola, extra)
CRIATURAS = {
    "pelusin":  ("Pelusin", 1, (245, 160, 70), (255, 225, 170), "redondo", "punta", "rabo", None),
    "gotita":   ("Gotita", 1, (90, 170, 250), (190, 225, 255), "gota", "ninguna", "ninguna", "brillo"),
    "hojita":   ("Hojita", 1, (110, 200, 100), (210, 240, 180), "redondo", "hoja", "ninguna", None),
    "nubi":     ("Nubi", 1, (225, 238, 252), (255, 255, 255), "nube", "ninguna", "ninguna", "mejillas"),
    "chispin":  ("Chispin", 2, (80, 205, 195), (200, 245, 235), "redondo", "redonda", "rayo", None),
    "piedri":   ("Piedri", 2, (150, 155, 170), (200, 205, 215), "piedra", "cuernos", "ninguna", None),
    "burbujo":  ("Burbujo", 2, (225, 130, 220), (250, 205, 245), "redondo", "antenas", "ninguna", None),
    "llamita":  ("Llamita", 2, (240, 90, 60), (255, 190, 90), "gota", "llama", "ninguna", None),
    "pinchin":  ("Pinchin", 2, (170, 115, 70), (235, 205, 165), "huevo", "pinchos", "rabo", None),
    "lunita":   ("Lunita", 3, (70, 80, 170), (150, 160, 230), "redondo", "redonda", "ninguna", "luna"),
    "estrellin": ("Estrellin", 3, (255, 225, 110), (255, 250, 200), "estrella", "ninguna", "ninguna", "mejillas"),
    "dragonito": ("Dragonito", 3, (120, 200, 140), (225, 245, 190), "huevo", "cuernos", "rabo", "alas"),
}
ORDEN_CRIATURAS = list(CRIATURAS)

# Peces y animales marinos (ya sin limite de especies: el Cuaderno los muestra por mundo).
# id: (nombre, grado 1-5, color, color2, forma, valor, fuerza, aguante, tamano (px en el juego),
#      mundos donde vive (1 normal, 2 submarino, 3 polar, 4 subnautica, 5 legendario), (profundidad min, max en px bajo la superficie),
#      puntos, evento, caracter)
# grado: 1 verde, 2 amarillo, 3 naranja, 4 rojo, 5 morado.  caracter: timido, curioso, cauto, agresivo.
# Objetivos de cada mundo (6): 1 sardina perca trucha carpa bagre esturion | 2 payaso globo caballito pezangel mantarraya tortuga |
# 3 atun bacalao beluga narval cachalote orca | 4 pezlinterna pezvibora pezhacha pezpescador anguila pulpogigante |
# 5 celacanto megalodon serpiente dragonmar kraken leviatan.  El resto son peces de fondo y de evento.
PECES = {
    # ---- mundo 1: normal (grados 1-2)
    "sardina":    ("Sardina", 1, (170, 190, 210), (225, 235, 245), "larga", 5, 1.0, 0.8, 74, (1, 2), (20, 150), 8, False, "timido"),
    "perca":      ("Perca", 1, (110, 160, 90), (240, 225, 160), "oval", 6, 1.1, 0.9, 92, (1,), (40, 190), 8, False, "curioso"),
    "trucha":     ("Trucha", 1, (150, 190, 130), (240, 190, 170), "oval", 7, 1.2, 1.0, 100, (1,), (30, 200), 10, False, "curioso"),
    "carpa":      ("Carpa", 1, (232, 150, 70), (250, 214, 150), "carpa", 9, 1.3, 1.1, 120, (1,), (40, 210), 12, False, "curioso"),
    "bagre":      ("Bagre", 2, (118, 104, 92), (205, 192, 170), "bagre", 14, 1.7, 1.3, 140, (1,), (90, 240), 16, False, "cauto"),
    "esturion":   ("Esturión", 2, (112, 128, 134), (218, 218, 206), "esturion", 20, 2.1, 1.6, 190, (1,), (120, 260), 22, False, "cauto"),
    "dorado":     ("Pez dorado", 2, (255, 200, 40), (255, 235, 140), "oval", 16, 2.2, 1.5, 100, (1, 2), (60, 230), 20, False, "cauto"),
    # ---- mundo 2: submarino (grados 2-3)
    "payaso":     ("Pez payaso", 2, (250, 140, 40), (255, 255, 255), "oval", 12, 1.8, 1.2, 76, (2,), (90, 230), 16, False, "curioso"),
    "globo":      ("Pez globo", 2, (240, 210, 90), (255, 245, 190), "globo", 12, 1.9, 1.4, 92, (2,), (50, 240), 16, False, "cauto"),
    "caballito":  ("Caballito de mar", 2, (250, 175, 60), (255, 230, 150), "caballito", 14, 1.6, 1.2, 74, (2,), (60, 220), 18, False, "timido"),
    "pezangel":   ("Pez ángel", 2, (246, 206, 70), (70, 120, 210), "pezangel", 18, 2.0, 1.5, 96, (2,), (60, 230), 22, False, "curioso"),
    "mantarraya": ("Mantarraya", 3, (80, 115, 175), (200, 215, 240), "raya", 28, 3.5, 2.2, 215, (2, 3), (130, 300), 32, False, "curioso"),
    "tortuga":    ("Tortuga marina", 3, (86, 156, 100), (226, 218, 156), "tortuga", 30, 3.2, 2.4, 170, (2,), (100, 260), 34, False, "curioso"),
    "pezluna":    ("Pez luna", 3, (190, 200, 235), (240, 245, 255), "luna", 25, 3.4, 2.2, 190, (2, 3), (130, 270), 30, False, "curioso"),
    # ---- mundo 3: polar (grados 3-4)
    "atun":       ("Atún", 3, (70, 110, 190), (200, 215, 240), "larga", 24, 3.2, 2.0, 170, (3,), (110, 240), 30, False, "cauto"),
    "bacalao":    ("Bacalao", 3, (124, 134, 100), (226, 226, 200), "bacalao", 26, 3.0, 1.9, 150, (3,), (100, 270), 30, False, "cauto"),
    "beluga":     ("Beluga", 3, (240, 240, 246), (255, 255, 255), "beluga", 40, 4.0, 2.5, 230, (3,), (110, 270), 42, False, "curioso"),
    "narval":     ("Narval", 4, (150, 166, 188), (236, 236, 242), "narval", 55, 5.2, 2.8, 290, (3,), (130, 290), 56, False, "curioso"),
    "cachalote":  ("Cachalote", 4, (108, 120, 142), (226, 216, 204), "cachalote", 62, 5.9, 3.2, 350, (3,), (150, 300), 64, False, "cauto"),
    "orca":       ("Orca", 4, (34, 40, 56), (250, 250, 252), "orca", 72, 6.3, 3.3, 300, (3,), (130, 290), 72, False, "agresivo"),
    "pezespada":  ("Pez espada", 4, (90, 125, 175), (225, 232, 245), "espada", 45, 6.0, 2.8, 260, (3, 4), (150, 290), 52, False, "agresivo"),
    "pulpo":      ("Pulpo", 4, (200, 100, 200), (240, 170, 240), "pulpo", 35, 5.0, 2.4, 150, (3, 4), (200, 340), 40, False, "cauto"),
    # ---- mundo 4: subnautica (grados 4-5)
    "pezlinterna": ("Pez linterna", 4, (90, 62, 125), (160, 115, 175), "lintera", 50, 4.8, 2.4, 150, (4,), (250, 360), 56, False, "cauto"),
    "pezvibora":  ("Pez víbora", 4, (46, 80, 116), (150, 196, 200), "pezvibora", 58, 5.2, 2.6, 180, (4,), (230, 360), 60, False, "agresivo"),
    "pezhacha":   ("Pez hacha", 4, (176, 188, 202), (240, 246, 252), "pezhacha", 52, 4.8, 2.4, 130, (4,), (220, 350), 54, False, "cauto"),
    "pezpescador": ("Pez pescador", 5, (96, 66, 56), (166, 124, 92), "pezpescador", 80, 7.0, 3.1, 200, (4,), (250, 370), 80, False, "cauto"),
    "anguila":    ("Anguila abisal", 5, (60, 150, 115), (205, 232, 185), "anguila", 70, 7.5, 3.0, 290, (4,), (280, 370), 72, False, "agresivo"),
    "pulpogigante": ("Pulpo gigante", 5, (205, 70, 95), (250, 165, 175), "pulpogig", 130, 8.6, 3.4, 400, (4,), (240, 360), 130, False, "cauto"),
    # ---- mundo 5: legendario (grado 5)
    "celacanto":  ("Celacanto", 5, (62, 98, 164), (176, 200, 232), "celacanto", 90, 8.0, 3.4, 260, (5,), (240, 360), 90, False, "cauto"),
    "megalodon":  ("Megalodón", 5, (92, 102, 128), (236, 238, 244), "megalodon", 160, 10.5, 4.2, 520, (5,), (200, 340), 150, False, "agresivo"),
    "serpiente":  ("Serpiente marina", 5, (42, 150, 130), (232, 226, 152), "serpiente", 150, 10.0, 4.0, 560, (5,), (180, 330), 140, False, "agresivo"),
    "dragonmar":  ("Dragón marino", 5, (52, 168, 176), (246, 232, 170), "dragonmar", 175, 11.0, 4.4, 540, (5,), (170, 330), 160, False, "curioso"),
    "kraken":     ("Kraken", 5, (126, 52, 150), (232, 156, 204), "kraken", 220, 12.0, 5.0, 600, (5,), (240, 350), 200, False, "agresivo"),
    "leviatan":   ("Leviatán", 5, (48, 62, 124), (244, 214, 124), "leviatan", 250, 12.0, 5.5, 700, (5,), (250, 350), 240, False, "agresivo"),
    # ---- animales marinos de evento (aparecen solo en eventos temporales)
    "medusa":     ("Medusa dorada", 4, (255, 205, 70), (255, 240, 160), "medusa", 80, 5.4, 2.4, 150, (1, 2, 3, 4), (70, 210), 80, True, "curioso"),
    "tiburon":    ("Tiburón", 5, (115, 135, 165), (235, 240, 250), "tiburon", 110, 8.0, 3.0, 330, (3, 4, 5), (140, 270), 95, True, "agresivo"),
    "ballena":    ("Ballena", 5, (70, 110, 190), (210, 225, 245), "ballena", 150, 9.0, 3.6, 460, (3, 4, 5), (110, 240), 140, True, "curioso"),
}
ORDEN_PECES = list(PECES)

EVENTO_TEXTO = {
    "medusa": "¡Evento: apareció una medusa dorada!",
    "tiburon": "¡Evento: llegó un tiburón!",
    "ballena": "¡Evento: llegó una ballena!",
}



def _ojos(p, cx, cy, sep, r, t=0.0, feliz=True, color=(255, 255, 255)):
    parpadeo = (t % 3.2) < 0.12
    for lado in (-1, 1):
        x = cx + lado * sep
        if parpadeo:
            pygame.draw.line(p, (40, 30, 50), (x - r * 0.8, cy), (x + r * 0.8, cy), max(2, int(r / 3)))
            continue
        pygame.draw.circle(p, color, (int(x), int(cy)), int(r))
        pygame.draw.circle(p, (40, 30, 50), (int(x + lado * r * 0.1), int(cy + r * 0.1)), int(r * 0.55))
        pygame.draw.circle(p, (255, 255, 255), (int(x + r * 0.05), int(cy - r * 0.15)), max(1, int(r * 0.2)))


def dibujar_criatura(p, ident, cx, cy, escala=1.0, t=0.0, silueta=False, feliz=True):
    """Dibuja una criatura centrada en (cx, cy). Mide unos 120*escala px de ancho."""
    nombre, rareza, color, vientre, forma, orejas, cola, extra = CRIATURAS[ident]
    s = escala
    sil = (60, 62, 80)
    col = sil if silueta else color
    vie = sil if silueta else vientre
    borde = (45, 45, 70) if silueta else oscurecer(color, 0.55)
    ancho, alto = 120 * s, 110 * s
    rect = pygame.Rect(0, 0, ancho, alto)
    rect.center = (cx, cy)

    # cola (detras)
    if cola == "rabo":
        pygame.draw.circle(p, col, (int(cx + 62 * s), int(cy + 8 * s)), int(17 * s))
        pygame.draw.circle(p, borde, (int(cx + 62 * s), int(cy + 8 * s)), int(17 * s), max(1, int(3 * s)))
    elif cola == "rayo":
        pts = [(cx + 50 * s, cy), (cx + 85 * s, cy - 22 * s), (cx + 72 * s, cy - 2 * s),
               (cx + 100 * s, cy - 8 * s), (cx + 62 * s, cy + 30 * s), (cx + 74 * s, cy + 6 * s)]
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    if extra == "alas" and not silueta:
        for lado in (-1, 1):
            pts = [(cx + lado * 40 * s, cy - 10 * s), (cx + lado * 95 * s, cy - 50 * s),
                   (cx + lado * 80 * s, cy + 5 * s)]
            pygame.draw.polygon(p, aclarar(color, 0.2), pts)
            pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    elif extra == "alas":
        for lado in (-1, 1):
            pts = [(cx + lado * 40 * s, cy - 10 * s), (cx + lado * 95 * s, cy - 50 * s),
                   (cx + lado * 80 * s, cy + 5 * s)]
            pygame.draw.polygon(p, sil, pts)

    # orejas / adornos (detras de la cabeza)
    top = cy - alto / 2
    if orejas == "punta":
        for lado in (-1, 1):
            pts = [(cx + lado * 18 * s, top + 8 * s), (cx + lado * 50 * s, top + 8 * s),
                   (cx + lado * 40 * s, top - 28 * s)]
            pygame.draw.polygon(p, col, pts)
            pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    elif orejas == "redonda":
        for lado in (-1, 1):
            pygame.draw.circle(p, col, (int(cx + lado * 40 * s), int(top + 6 * s)), int(20 * s))
            pygame.draw.circle(p, borde, (int(cx + lado * 40 * s), int(top + 6 * s)), int(20 * s), max(1, int(3 * s)))
    elif orejas == "hoja":
        for lado in (-1, 1):
            pts = [(cx + lado * 6 * s, top + 8 * s), (cx + lado * 52 * s, top - 30 * s),
                   (cx + lado * 40 * s, top + 14 * s)]
            pygame.draw.polygon(p, (60, 170, 80) if not silueta else sil, pts)
            pygame.draw.polygon(p, (30, 100, 50) if not silueta else sil, pts, max(1, int(3 * s)))
    elif orejas == "cuernos":
        for lado in (-1, 1):
            pts = [(cx + lado * 22 * s, top + 10 * s), (cx + lado * 40 * s, top + 8 * s),
                   (cx + lado * 34 * s, top - 22 * s)]
            pygame.draw.polygon(p, (245, 235, 200) if not silueta else sil, pts)
            pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    elif orejas == "antenas":
        for lado in (-1, 1):
            pygame.draw.line(p, borde, (cx + lado * 20 * s, top + 8 * s),
                             (cx + lado * 38 * s, top - 28 * s), max(2, int(4 * s)))
            pygame.draw.circle(p, (255, 230, 90) if not silueta else sil,
                               (int(cx + lado * 38 * s), int(top - 30 * s)), int(10 * s))
    elif orejas == "llama":
        pts = [(cx - 22 * s, top + 14 * s), (cx - 14 * s, top - 22 * s), (cx, top - 4 * s),
               (cx + 12 * s, top - 34 * s), (cx + 24 * s, top + 14 * s)]
        pygame.draw.polygon(p, (255, 200, 60) if not silueta else sil, pts)
        pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    elif orejas == "pinchos":
        for i in range(-2, 3):
            pts = [(cx + i * 22 * s - 10 * s, top + 12 * s), (cx + i * 22 * s + 10 * s, top + 12 * s),
                   (cx + i * 22 * s, top - 22 * s)]
            pygame.draw.polygon(p, oscurecer(color, 0.25) if not silueta else sil, pts)

    # cuerpo
    if forma == "gota":
        pygame.draw.circle(p, col, (int(cx), int(cy + 10 * s)), int(52 * s))
        pts = [(cx - 40 * s, cy - 8 * s), (cx + 40 * s, cy - 8 * s), (cx, cy - 62 * s)]
        pygame.draw.polygon(p, col, pts)
        pygame.draw.circle(p, borde, (int(cx), int(cy + 10 * s)), int(52 * s), max(1, int(3 * s)))
    elif forma == "nube":
        for dx, dy, r in ((-34, 8, 30), (0, -6, 40), (34, 8, 30), (-10, 22, 30), (20, 22, 30)):
            pygame.draw.circle(p, borde, (int(cx + dx * s), int(cy + dy * s)), int((r + 3) * s))
        for dx, dy, r in ((-34, 8, 30), (0, -6, 40), (34, 8, 30), (-10, 22, 30), (20, 22, 30)):
            pygame.draw.circle(p, col, (int(cx + dx * s), int(cy + dy * s)), int(r * s))
    elif forma == "piedra":
        pts = [(cx - 55 * s, cy + 30 * s), (cx - 45 * s, cy - 25 * s), (cx - 10 * s, cy - 50 * s),
               (cx + 30 * s, cy - 42 * s), (cx + 58 * s, cy - 5 * s), (cx + 50 * s, cy + 38 * s)]
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    elif forma == "estrella":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = (62 if i % 2 == 0 else 34) * s
            pts.append((cx + rr * math.cos(ang), cy + 4 * s + rr * math.sin(ang)))
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, borde, pts, max(1, int(3 * s)))
    elif forma == "huevo":
        pygame.draw.ellipse(p, col, pygame.Rect(cx - 46 * s, cy - 56 * s, 92 * s, 112 * s))
        pygame.draw.ellipse(p, borde, pygame.Rect(cx - 46 * s, cy - 56 * s, 92 * s, 112 * s), max(1, int(3 * s)))
    else:                                           # redondo
        pygame.draw.ellipse(p, col, rect)
        pygame.draw.ellipse(p, borde, rect, max(1, int(3 * s)))

    # vientre
    if forma not in ("nube", "estrella"):
        pygame.draw.ellipse(p, vie, pygame.Rect(cx - 28 * s, cy + 4 * s, 56 * s, 38 * s))

    if silueta:
        return
    # extras
    if extra == "luna":
        pygame.draw.circle(p, (255, 240, 150), (int(cx), int(cy - 30 * s)), int(11 * s))
        pygame.draw.circle(p, color, (int(cx + 5 * s), int(cy - 33 * s)), int(10 * s))
    if extra == "mejillas" or forma == "nube":
        for lado in (-1, 1):
            pygame.draw.circle(p, (255, 150, 160), (int(cx + lado * 34 * s), int(cy + 8 * s)), int(8 * s))
    if extra == "brillo":
        pygame.draw.circle(p, (255, 255, 255), (int(cx - 22 * s), int(cy - 2 * s)), int(8 * s))

    # cara
    _ojos(p, cx, cy - 8 * s, 20 * s, 10 * s, t, feliz)
    if feliz:
        pygame.draw.arc(p, (60, 30, 50), pygame.Rect(cx - 13 * s, cy - 2 * s, 26 * s, 20 * s),
                        math.pi * 1.1, math.pi * 1.9, max(2, int(3 * s)))
    else:
        pygame.draw.circle(p, (60, 30, 50), (int(cx), int(cy + 14 * s)), int(6 * s))


def dibujar_jefe(p, cx, cy, escala=1.0, t=0.0, enojado=False, golpeado=False):
    """El Rey Grunon: jefe final (original)."""
    s = escala
    color = (130, 80, 190) if not golpeado else (230, 120, 130)
    borde = oscurecer(color, 0.55)
    # alas
    for lado in (-1, 1):
        pts = [(cx + lado * 100 * s, cy - 20 * s), (cx + lado * 220 * s, cy - 110 * s + math.sin(t * 4) * 12 * s),
               (cx + lado * 190 * s, cy + 40 * s)]
        pygame.draw.polygon(p, (90, 50, 150), pts)
        pygame.draw.polygon(p, borde, pts, max(2, int(4 * s)))
    # cuerpo
    cuerpo = pygame.Rect(0, 0, 250 * s, 230 * s)
    cuerpo.center = (cx, cy)
    pygame.draw.ellipse(p, color, cuerpo)
    pygame.draw.ellipse(p, borde, cuerpo, max(2, int(5 * s)))
    pygame.draw.ellipse(p, aclarar(color, 0.5), pygame.Rect(cx - 70 * s, cy + 10 * s, 140 * s, 90 * s))
    # cuernos
    for lado in (-1, 1):
        pts = [(cx + lado * 60 * s, cy - 95 * s), (cx + lado * 100 * s, cy - 80 * s),
               (cx + lado * 96 * s, cy - 165 * s)]
        pygame.draw.polygon(p, (250, 240, 200), pts)
        pygame.draw.polygon(p, borde, pts, max(2, int(4 * s)))
    # corona
    base = cy - 112 * s
    pts = [(cx - 55 * s, base), (cx - 55 * s, base - 40 * s), (cx - 28 * s, base - 18 * s),
           (cx, base - 52 * s), (cx + 28 * s, base - 18 * s), (cx + 55 * s, base - 40 * s), (cx + 55 * s, base)]
    pygame.draw.polygon(p, (255, 210, 60), pts)
    pygame.draw.polygon(p, (150, 100, 20), pts, max(2, int(4 * s)))
    for dx in (-30, 0, 30):
        pygame.draw.circle(p, (235, 60, 80), (int(cx + dx * s), int(base - 8 * s)), int(6 * s))
    # cara
    ojo_y = cy - 30 * s
    for lado in (-1, 1):
        x = cx + lado * 45 * s
        pygame.draw.circle(p, (255, 255, 255), (int(x), int(ojo_y)), int(24 * s))
        pygame.draw.circle(p, (40, 20, 50), (int(x), int(ojo_y + 3 * s)), int(12 * s))
        ceja = [(x - lado * 24 * s, ojo_y - 34 * s), (x + lado * 24 * s, ojo_y - (14 if enojado else 30) * s)]
        pygame.draw.line(p, (40, 20, 50), ceja[0], ceja[1], max(3, int(7 * s)))
    boca = pygame.Rect(cx - 50 * s, cy + 14 * s, 100 * s, 60 * s)
    pygame.draw.ellipse(p, (70, 20, 50), boca)
    for dx in (-30, -10, 10, 30):
        pygame.draw.polygon(p, (255, 255, 255), [(cx + dx * s - 8 * s, cy + 22 * s),
                                                  (cx + dx * s + 8 * s, cy + 22 * s), (cx + dx * s, cy + 40 * s)])


def dibujar_pez(p, ident, cx, cy, escala=1.0, direccion=1, t=0.0, silueta=False, mirando=None):
    """Pez o animal marino mirando a la derecha (direccion=1) o a la izquierda (-1).

    A escala 1 todos caben en unos 150 x 100 px (la Pesca los amplia con su tamano real).
    `mirando` es el nombre antiguo de `direccion`."""
    if mirando is not None:
        direccion = mirando
    d = PECES[ident]
    arte_mar.dibujar_animal(p, ident, (d[2], d[3], d[4]), cx, cy, escala, direccion, t, silueta)
