"""Utilidades de dibujo compartidas por todo el arte de Tamagotchi (ojos, boca, contorno, sombra, rebote)."""

import math

import pygame

from nucleo import aclarar, oscurecer

CONTORNO = (38, 32, 52)


def rebote(t, vel=2.0, amp=4.0, fase=0.0):
    """Desplazamiento vertical suave (idle)."""
    return math.sin(t * vel + fase) * amp


def respirar(t, vel=2.0, amp=0.03, fase=0.0):
    """Factor de escala (1 +- amp) para 'respirar'."""
    return 1.0 + math.sin(t * vel + fase) * amp


def parpadeando(t, periodo=3.4, dur=0.14, fase=0.0):
    return ((t + fase) % periodo) < dur


def sombra(p, cx, cy, ancho, alto=None, alfa=70):
    alto = alto or ancho * 0.22
    s = pygame.Surface((int(ancho), int(alto)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alfa), s.get_rect())
    p.blit(s, (cx - ancho / 2, cy - alto / 2))


def elipse_borde(p, color, rect, grosor=3, borde=None):
    borde = borde or oscurecer(color, 0.55)
    pygame.draw.ellipse(p, color, rect)
    pygame.draw.ellipse(p, borde, rect, grosor)


def brillo(p, x, y, r, alfa=170):
    s = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (255, 255, 255, alfa), (0, 0, int(r * 2), int(r * 1.4)))
    p.blit(s, (x - r, y - r))


def ojos(p, cx, cy, sep, r, estado="normal", t=0.0, color=(40, 30, 60), dir=1, fase=0.0):
    """Dos ojos centrados en (cx,cy), separados 'sep', radio 'r'. Estados: normal, feliz, triste, hambre, duerme, enfermo,
    come, ataca, golpeado, evoluciona."""
    xs = (cx - sep / 2, cx + sep / 2)
    r = max(2, r)
    for x in xs:
        x = int(x)
        y = int(cy)
        if estado == "duerme":
            pygame.draw.arc(p, CONTORNO, (x - r, y - r * 0.6, r * 2, r * 1.2), math.pi, 2 * math.pi, max(2, int(r * 0.3)))
        elif estado == "feliz" or estado == "evoluciona":
            pygame.draw.arc(p, CONTORNO, (x - r, y - r * 0.4, r * 2, r * 1.4), 0, math.pi, max(2, int(r * 0.35)))
        elif estado == "golpeado":
            d = int(r * 0.8)
            pygame.draw.line(p, CONTORNO, (x - d, y - d), (x + d, y + d), max(2, int(r * 0.35)))
            pygame.draw.line(p, CONTORNO, (x - d, y + d), (x + d, y - d), max(2, int(r * 0.35)))
        elif parpadeando(t, fase=fase):
            pygame.draw.line(p, CONTORNO, (x - r, y), (x + r, y), max(2, int(r * 0.3)))
        else:
            pygame.draw.ellipse(p, (255, 255, 255), (x - r, y - r * 1.1, r * 2, r * 2.2))
            pygame.draw.ellipse(p, CONTORNO, (x - r, y - r * 1.1, r * 2, r * 2.2), max(2, int(r * 0.22)))
            mx = dir * r * 0.18
            my = r * 0.15 if estado in ("triste", "hambre", "enfermo") else 0
            pygame.draw.circle(p, color, (int(x + mx), int(y + my)), int(r * 0.72))
            pygame.draw.circle(p, (255, 255, 255), (int(x + mx - r * 0.25), int(y + my - r * 0.3)), max(1, int(r * 0.26)))
            if estado == "ataca":
                pygame.draw.line(p, CONTORNO, (x - r, y - r * 1.4), (x + r, y - r * 0.9 if x > cx else y - r * 1.9), max(2, int(r * 0.35)))
            if estado == "triste":
                pygame.draw.line(p, CONTORNO, (x - r, y - r * 1.3), (x + r * 0.6, y - r * 1.6) if x < cx else (x - r * 0.6, y - r * 1.6), 2)


def boca(p, cx, cy, ancho, estado="normal", t=0.0):
    """Boca pequena y simpatica. Estados: normal, feliz, triste, hambre, duerme, enfermo, come, ataca, golpeado."""
    w = max(4, int(ancho))
    g = max(2, int(w * 0.14))
    if estado in ("feliz", "evoluciona"):
        pygame.draw.arc(p, CONTORNO, (cx - w / 2, cy - w * 0.25, w, w * 0.7), math.pi, 2 * math.pi, g)
    elif estado in ("triste", "enfermo"):
        pygame.draw.arc(p, CONTORNO, (cx - w / 2, cy, w, w * 0.6), 0, math.pi, g)
    elif estado in ("hambre", "come", "ataca", "golpeado"):
        ab = w * (0.35 + 0.25 * abs(math.sin(t * 8))) if estado == "come" else w * 0.45
        pygame.draw.ellipse(p, (150, 50, 70), (cx - w * 0.3, cy, w * 0.6, ab))
        pygame.draw.ellipse(p, CONTORNO, (cx - w * 0.3, cy, w * 0.6, ab), g)
    elif estado == "duerme":
        pygame.draw.line(p, CONTORNO, (cx - w * 0.2, cy + 2), (cx + w * 0.2, cy + 2), g)
    else:
        pygame.draw.arc(p, CONTORNO, (cx - w / 2, cy - w * 0.15, w, w * 0.5), math.pi, 2 * math.pi, g)


def mejillas(p, cx, cy, sep, r, color=(255, 150, 160)):
    s = pygame.Surface((int(r * 4), int(r * 2.4)), pygame.SRCALPHA)
    for x in (cx - sep / 2, cx + sep / 2):
        s.fill((0, 0, 0, 0))
        pygame.draw.ellipse(s, color + (110,), (0, 0, int(r * 2), int(r * 1.2)))
        p.blit(s, (x - r, cy - r * 0.6))


def silueta_de(superficie, color=(60, 62, 80)):
    """Convierte una superficie SRCALPHA en su silueta gris oscura."""
    m = pygame.mask.from_surface(superficie)
    return m.to_surface(setcolor=color + (255,), unsetcolor=(0, 0, 0, 0))
