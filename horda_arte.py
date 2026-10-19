"""Arte de la Horda Elemental: mapa, heroe, enemigos (mascotas del Tamagotchi), proyectiles por elemento,
zonas de ultimate y tarjetas de habilidades. Todo se cachea para que vaya fluido."""

import math
from collections import OrderedDict

import pygame

import arte_tama as AT
from escena_items import ajustado
import horda_datos as D
import horda_mapa as M
from nucleo import aclarar, barra, oscurecer

_SPR = {}
_ICON = {}


# ---------------------------------------------------------------- mapa
def _tile_pasto(p, x, y, h):
    p.fill((112 + h % 9, 186 + h % 7, 92 + h % 5), (x, y, M.TAM, M.TAM))
    if h % 5 == 0:
        pygame.draw.line(p, (96, 170, 80), (x + 8, y + 30), (x + 10, y + 24), 2)
        pygame.draw.line(p, (96, 170, 80), (x + 30, y + 28), (x + 32, y + 22), 2)


CH_MAPA = 8                  # casillas por bloque del mapa (solo se dibujan los bloques que se ven)
_BLOQUES_MAX = 80            # bloques guardados a la vez: memoria acotada


def _dibujar_casillas(surf, g, c0, r0, c1, r1, ox, oy):
    """Dibuja las casillas [c0,c1) x [r0,r1) en surf. (ox, oy) = posicion en el mundo de la esquina de surf."""
    T = M.TAM
    rango = [(cx, cy) for cy in range(r0, r1) for cx in range(c0, c1)
             if 0 <= cx < M.COLS and 0 <= cy < M.FILAS]
    for cx, cy in rango:                                        # pasto, agua, hojas
        x, y, h = cx * T - ox, cy * T - oy, (cx * 31 + cy * 17) % 11
        v = g[cy][cx]
        if v == M.AGUA:
            surf.fill((70, 150, 225), (x, y, T, T))
            pygame.draw.line(surf, (120, 190, 245), (x + 6 + h, y + 12), (x + 18 + h, y + 12), 2)
        elif v == M.HOJAS:
            _tile_pasto(surf, x, y, h)
            for k in range(4):
                pygame.draw.circle(surf, (70 + k * 6, 160 + k * 5, 70), (x + 10 + k * 8, y + 12 + (k % 2) * 14), 6)
        else:
            _tile_pasto(surf, x, y, h)
    for cx, cy in rango:                                        # orillas del agua
        if g[cy][cx] == M.AGUA:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < M.COLS and 0 <= ny < M.FILAS and g[ny][nx] != M.AGUA:
                    x, y = cx * T - ox, cy * T - oy
                    ancho = 4
                    rect = [(x, y, T, ancho), (x, y + T - ancho, T, ancho),
                            (x, y, ancho, T), (x + T - ancho, y, ancho, T)][
                        [(1, 0), (-1, 0), (0, 1), (0, -1)].index((dx, dy))]
                    surf.fill((235, 215, 150), rect)
    for cx, cy in rango:                                        # arboles y rocas (encima, con sombra)
        v = g[cy][cx]
        x, y = cx * T - ox + T / 2, cy * T - oy + T / 2
        if v == M.ARBOL:
            pygame.draw.ellipse(surf, (40, 90, 50, 120), (x - 16, y + 10, 34, 12))
            pygame.draw.rect(surf, (120, 80, 45), (x - 3, y, 6, 14))
            pygame.draw.circle(surf, (40, 130, 60), (int(x), int(y - 4)), 17)
            pygame.draw.circle(surf, (60, 160, 80), (int(x - 5), int(y - 9)), 9)
        elif v == M.ROCA:
            pygame.draw.ellipse(surf, (60, 60, 60), (x - 15, y + 8, 30, 10))
            pts = [(x - 16, y + 8), (x - 12, y - 10), (x + 2, y - 16), (x + 16, y - 6), (x + 14, y + 8)]
            pygame.draw.polygon(surf, (140, 140, 150), pts)
            pygame.draw.polygon(surf, (95, 95, 105), pts, 2)
            pygame.draw.line(surf, (190, 190, 200), (x - 6, y - 8), (x, y - 12), 2)


class MapaVisto:
    """El mundo se dibuja por bloques: solo los que se ven, con memoria acotada (el mundo es muy grande
    para una sola imagen). Cada bloque tiene 1 casilla de margen para que los arboles no se corten."""

    def __init__(self, g):
        self.g = g
        self._bloques = OrderedDict()

    def _bloque(self, ic, jc):
        clave = (ic, jc)
        s = self._bloques.get(clave)
        if s is not None:
            self._bloques.move_to_end(clave)
            return s
        T, n = M.TAM, CH_MAPA + 2
        c0, r0 = ic * CH_MAPA - 1, jc * CH_MAPA - 1
        s = pygame.Surface((n * T, n * T))
        _dibujar_casillas(s, self.g, c0, r0, c0 + n, r0 + n, c0 * T, r0 * T)
        self._bloques[clave] = s
        if len(self._bloques) > _BLOQUES_MAX:
            self._bloques.popitem(last=False)
        return s

    def blit(self, p, cam_x, cam_y, ancho, alto):
        L = CH_MAPA * M.TAM
        ic0, ic1 = max(0, int(cam_x // L)), min((M.COLS - 1) // CH_MAPA, int((cam_x + ancho) // L))
        jc0, jc1 = max(0, int(cam_y // L)), min((M.FILAS - 1) // CH_MAPA, int((cam_y + alto) // L))
        for jc in range(jc0, jc1 + 1):
            for ic in range(ic0, ic1 + 1):
                p.blit(self._bloque(ic, jc), (ic * L - M.TAM - cam_x, jc * L - M.TAM - cam_y))


# ---------------------------------------------------------------- sprites de mascotas
def sprite_mascota(especie, etapa, alto, mirar=1):
    """Mascota del Tamagotchi recortada y escalada a 'alto' px. Cacheada."""
    clave = (especie, etapa, alto, mirar)
    s = _SPR.get(clave)
    if s is not None:
        return s
    lienzo = pygame.Surface((320, 320), pygame.SRCALPHA)
    AT.dibujar_mascota(lienzo, especie, etapa, 160, 170, 1.0, 0.0, "normal", mirar)
    caja = lienzo.get_bounding_rect()
    if caja.w == 0:
        caja = pygame.Rect(0, 0, 320, 320)
    recorte = lienzo.subsurface(caja).copy()
    f = alto / max(1, recorte.get_height())
    s = pygame.transform.smoothscale(recorte, (max(1, int(recorte.get_width() * f)), alto))
    _SPR[clave] = s
    return s


def sombra(p, x, y, r):
    s = pygame.Surface((int(r * 2.2), int(r * 0.9)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (20, 50, 20, 90), s.get_rect())
    p.blit(s, (x - s.get_width() / 2, y - s.get_height() / 2))


def dibujar_enemigo(p, especie, etapa, x, y, alto, t, estados):
    """Estados: 'aturdido', 'mojado', 'quemado', 'congelado', 'paralizado', 'empujado' (solo cambian el tinte)."""
    sombra(p, x, y + alto * 0.42, alto * 0.42)
    s = sprite_mascota(especie, etapa, alto)
    if estados:
        s = s.copy()
        if "congelado" in estados:
            s.fill((140, 210, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
            s.fill((60, 40, 0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        if "quemado" in estados:
            s.fill((120, 40, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        if "mojado" in estados:
            s.fill((0, 40, 110, 0), special_flags=pygame.BLEND_RGBA_ADD)
        if "paralizado" in estados and int(t * 20) % 2:
            s.fill((200, 180, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    desplaza = math.sin(t * 9 + x) * 2 if not (estados and ("congelado" in estados or "aturdido" in estados)) else 0
    p.blit(s, (x - s.get_width() / 2, y - alto / 2 + desplaza))
    if estados and ("aturdido" in estados or "paralizado" in estados):
        for k in range(3):
            a = t * 4 + k * 2.1
            pygame.draw.circle(p, (255, 240, 120), (int(x + math.cos(a) * 18), int(y - alto / 2 - 6 + math.sin(a) * 4)), 4)


def dibujar_jefe(p, especie, etapa, x, y, alto, t, rojo=False):
    sombra(p, x, y + alto * 0.42, alto * 0.42)
    s = sprite_mascota(especie, etapa, alto)
    p.blit(s, (x - s.get_width() / 2, y - alto / 2 + math.sin(t * 3) * 4))
    if rojo:
        halo = pygame.Surface((alto, alto), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 60, 60, 60), (alto // 2, alto // 2), alto // 2)
        p.blit(halo, (x - alto / 2, y - alto / 2))


# ---------------------------------------------------------------- heroe
def dibujar_heroe(p, x, y, tipo, t, invuln, mirar=1):
    col = D.COLOR_TIPO[tipo]
    if invuln > 0 and int(t * 16) % 2:
        return
    sombra(p, x, y + 18, 18)
    cuerpo = pygame.Surface((70, 70), pygame.SRCALPHA)
    pygame.draw.circle(cuerpo, (30, 25, 50), (35, 37), 22)
    pygame.draw.circle(cuerpo, col, (35, 35), 21)
    pygame.draw.circle(cuerpo, aclarar(col, 0.5), (28, 27), 6)
    ojo = (255, 255, 255)
    pygame.draw.circle(cuerpo, ojo, (35 + 6 * mirar - 4, 31), 5)
    pygame.draw.circle(cuerpo, ojo, (35 + 6 * mirar + 6, 31), 5)
    pygame.draw.circle(cuerpo, (30, 25, 50), (35 + 6 * mirar - 3, 32), 2)
    pygame.draw.circle(cuerpo, (30, 25, 50), (35 + 6 * mirar + 7, 32), 2)
    pygame.draw.arc(cuerpo, (30, 25, 50), pygame.Rect(26, 38, 18, 12), math.pi * 0.1, math.pi * 0.9, 3)
    if tipo == "hielo":                              # gorrito
        pygame.draw.polygon(cuerpo, (120, 200, 250), [(18, 22), (35, 2), (52, 22)])
    if tipo == "electrico":
        pygame.draw.polygon(cuerpo, (255, 240, 120), [(14, 18), (32, 0), (26, 14), (46, 4), (30, 26)])
    p.blit(cuerpo, (x - 35, y - 35 + math.sin(t * 8) * 1.5))


# ---------------------------------------------------------------- proyectiles
def _girar(puntos, ang, cx, cy):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + px * c - py * s, cy + px * s + py * c) for px, py in puntos]


def dibujar_proyectil(p, tipo, x, y, ang, r, t, intermedio=False):
    col = D.COLOR_TIPO[tipo]
    if intermedio:
        glow = pygame.Surface((int(r * 5), int(r * 5)), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, 60), (int(r * 2.5), int(r * 2.5)), int(r * 2.4))
        p.blit(glow, (x - r * 2.5, y - r * 2.5))
    if tipo == "electrico":                          # "zap": varias Z pequenas seguidas
        for k in range(3):
            off = (k - 1) * r * 1.1
            base = [(-r * 0.7, -r * 0.6), (r * 0.7, -r * 0.6), (-r * 0.7, r * 0.6), (r * 0.7, r * 0.6)]
            pts = _girar([(px + off, py) for px, py in base], ang, x, y)
            pygame.draw.lines(p, (255, 255, 255), False, pts, max(3, int(r * 0.3)))
            pygame.draw.lines(p, col, False, pts, max(2, int(r * 0.16)))
    elif tipo == "agua":                             # gotita
        pts = [(0, -r * 1.3), (r * 0.8, r * 0.3), (0, r * 0.9), (-r * 0.8, r * 0.3)]
        pts = _girar(pts, ang, x, y)
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, oscurecer(col, 0.5), pts, 2)
        pygame.draw.circle(p, (255, 255, 255), (int(x - r * 0.25), int(y + r * 0.1)), max(2, int(r * 0.2)))
    elif tipo == "viento":                           # medio tornado: arcos que se achican
        for k in range(3):
            w = r * (1.2 - k * 0.3)
            pygame.draw.arc(p, col, pygame.Rect(x - w, y - r * 0.9 + k * r * 0.6 - w * 0.2, w * 2, w * 0.9),
                            ang + 0.3, ang + math.pi - 0.3, max(2, int(r * 0.22)))
    elif tipo == "tierra":                           # roca
        pts = [(-r, -r * 0.4), (-r * 0.4, -r), (r * 0.7, -r * 0.8), (r, r * 0.2), (r * 0.3, r), (-r * 0.8, r * 0.6)]
        pts = _girar(pts, ang, x, y)
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, oscurecer(col, 0.5), pts, 2)
    elif tipo == "fuego":                            # bolita de fuego
        pygame.draw.circle(p, col, (int(x), int(y)), int(r))
        pygame.draw.circle(p, (255, 230, 120), (int(x - r * 0.2), int(y - r * 0.2)), max(2, int(r * 0.5)))
    elif tipo == "hielo":                            # caramo de hielo (punta hacia donde va)
        pts = [(r * 1.6, 0), (-r * 0.5, -r * 0.6), (-r * 0.9, 0), (-r * 0.5, r * 0.6)]
        pts = _girar(pts, ang, x, y)
        pygame.draw.polygon(p, col, pts)
        pygame.draw.polygon(p, (120, 200, 240), pts, 2)
    if intermedio:
        pygame.draw.circle(p, (255, 255, 255), (int(x), int(y)), max(2, int(r * 0.12)))


def dibujar_bala_enemiga(p, x, y, r, t):
    pygame.draw.circle(p, (60, 20, 60), (int(x), int(y)), int(r + 2))
    pygame.draw.circle(p, (200, 60, 200), (int(x), int(y)), int(r))
    pygame.draw.circle(p, (255, 200, 255), (int(x - r * 0.3), int(y - r * 0.3)), max(2, int(r * 0.3)))


# ---------------------------------------------------------------- zonas de ultimate y chispas
def dibujar_zona(p, z, t):
    """z: dict con tipo, x, y, r, fase ('aviso'|'impacto'|'activa'), u (0..1 avance de la fase)."""
    tipo, x, y, r = z["tipo"], z["x"], z["y"], z["r"]
    col = D.COLOR_TIPO[tipo]
    if z["fase"] == "aviso":
        k = z["u"]
        s = pygame.Surface((int(r * 2.2), int(r * 2.2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, int(40 + 90 * k)), (int(r * 1.1), int(r * 1.1)), int(r * (0.6 + 0.4 * k)))
        pygame.draw.circle(s, (*oscurecer(col, 0.3), 200), (int(r * 1.1), int(r * 1.1)), int(r), 3)
        p.blit(s, (x - r * 1.1, y - r * 1.1))
        if tipo == "tierra" or tipo == "hielo":        # sombra de lo que cae
            pygame.draw.circle(p, (60, 40, 20), (int(x), int(y)), int(r * (0.3 + 0.5 * k)), 2)
        return
    if tipo == "agua":                                 # ola: anillo que se expande
        for j in range(3):
            rr = r * min(1.0, z["u"] + j * 0.12)
            pygame.draw.circle(p, col, (int(x), int(y)), int(rr), max(3, int(14 * (1 - z["u"]))))
    elif tipo == "viento":                             # tornado: espiral que gira
        for j in range(14):
            a = t * 9 + j * 0.9
            rr = r * (0.3 + 0.7 * ((j * 37) % 14) / 14)
            pygame.draw.circle(p, (235, 255, 248), (int(x + math.cos(a) * rr), int(y + math.sin(a) * rr * 0.5)), 5)
    elif tipo == "tierra":                             # derrumbe: rocas que caen
        for j in range(5):
            a = j * 1.26 + 0.4
            pts = [(-7, -4), (-2, -9), (7, -5), (8, 4), (1, 8)]
            pts = [(x + math.cos(a) * r * 0.5 + px, y + math.sin(a) * r * 0.5 + py) for px, py in pts]
            pygame.draw.polygon(p, col, pts)
    elif tipo == "fuego":                              # explosion
        pygame.draw.circle(p, col, (int(x), int(y)), int(r * (0.5 + 0.5 * z["u"])))
        pygame.draw.circle(p, (255, 240, 150), (int(x), int(y)), int(r * 0.35 * (1 - z["u"]) + 6))
    elif tipo == "hielo":                              # iceberg: bloque de hielo
        pygame.draw.polygon(p, (230, 248, 255), [(x - r * 0.7, y + r * 0.2), (x - r * 0.2, y - r * 0.8),
                                                  (x + r * 0.6, y - r * 0.5), (x + r * 0.8, y + r * 0.4),
                                                  (x, y + r * 0.8)])
        pygame.draw.polygon(p, (120, 200, 240), [(x - r * 0.7, y + r * 0.2), (x - r * 0.2, y - r * 0.8),
                                                  (x + r * 0.6, y - r * 0.5), (x + r * 0.8, y + r * 0.4),
                                                  (x, y + r * 0.8)], 3)
    elif tipo == "electrico":                          # truenos
        for j in range(3):
            a = t * 5 + j * 2.0
            pts = [(x, y - 12)]
            for k in range(1, 5):
                pts.append((x + math.cos(a + k) * 9 * (-1) ** k, y - 12 + k * 14))
            pygame.draw.lines(p, (255, 255, 255), False, pts, 6)
            pygame.draw.lines(p, col, False, pts, 3)


def dibujar_chispa(p, x, y, col, u):
    """Destello de impacto (u 0..1)."""
    r = int(6 + 16 * u)
    pygame.draw.circle(p, col, (int(x), int(y)), r, max(1, int(4 * (1 - u)) + 1))


# ---------------------------------------------------------------- HUD
def corazon(p, x, y, lleno, tam=22):
    col = (240, 70, 110) if lleno else (80, 60, 90)
    pygame.draw.circle(p, col, (int(x - tam * 0.25), int(y - tam * 0.1)), int(tam * 0.3))
    pygame.draw.circle(p, col, (int(x + tam * 0.25), int(y - tam * 0.1)), int(tam * 0.3))
    pygame.draw.polygon(p, col, [(x - tam * 0.52, y - tam * 0.05), (x + tam * 0.52, y - tam * 0.05), (x, y + tam * 0.5)])


def icono_habilidad(tipo, cual, tam=56):
    """Icono cuadrado: 'basico' (proyectil), 'inter' (carga) o 'ulti' (area)."""
    clave = (tipo, cual, tam)
    s = _ICON.get(clave)
    if s is not None:
        return s
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    col = D.COLOR_TIPO[tipo]
    pygame.draw.rect(s, (30, 22, 50, 230), s.get_rect(), border_radius=12)
    pygame.draw.rect(s, col, s.get_rect(), 3, border_radius=12)
    c = tam // 2
    if cual == "basico":
        dibujar_proyectil(s, tipo, c, c, -0.8, tam * 0.2, 0.0)
    elif cual == "inter":
        dibujar_proyectil(s, tipo, c, c, -0.8, tam * 0.26, 0.0, intermedio=True)
    else:
        pygame.draw.circle(s, col, (c, c), tam // 3, 3)
        pygame.draw.circle(s, col, (c, c), tam // 6)
    _ICON[clave] = s
    return s


def tarjeta(p, rect, fuente, fuente_chica, titulo, cuerpo, color, ok, motivo="", icono=None, enfoque=False,
            dwell=0.0):
    """Carta de mejora con titulo, descripcion y, si no se puede elegir, el motivo. Apagada = bloqueada."""
    base = color if ok else (74, 70, 88)
    pygame.draw.rect(p, oscurecer(base, 0.5), rect.move(0, 7), border_radius=22)
    pygame.draw.rect(p, base, rect, border_radius=22)
    pygame.draw.rect(p, (255, 255, 255) if ok else (110, 106, 124), rect, 4, border_radius=22)
    if enfoque and ok:
        pygame.draw.rect(p, (255, 240, 120), rect.inflate(10, 10), 5, border_radius=26)
    y = rect.y + 30
    if icono is not None:
        p.blit(icono, icono.get_rect(center=(rect.centerx, rect.y + 58)))
        y = rect.y + 122
    ajustado(p, fuente, titulo, rect.centerx, y, rect.w - 28, (255, 255, 255) if ok else (190, 186, 205),
             contorno=(30, 20, 40))
    y = texto_centrado(p, fuente_chica, cuerpo, rect.centerx, y + 44, rect.w - 36,
                       (255, 255, 255) if ok else (170, 166, 185), lineas_max=3)
    if not ok and motivo:
        texto_centrado(p, fuente_chica, motivo, rect.centerx, rect.bottom - 78, rect.w - 36,
                       (255, 220, 140), lineas_max=3)
    if dwell > 0 and ok:
        barra(p, pygame.Rect(rect.x + 18, rect.bottom - 22, rect.w - 36, 10), min(1.0, dwell),
              color=(255, 230, 90), color_fondo=(60, 40, 80))
    return rect


def texto_centrado(p, fuente, texto, x, y, ancho, color, lineas_max=3, interlineado=None):
    palabras, linea, out = texto.split(), "", []
    for w in palabras:
        prueba = (linea + " " + w).strip()
        if fuente.size(prueba)[0] <= ancho or not linea:
            linea = prueba
        else:
            out.append(linea)
            linea = w
    if linea:
        out.append(linea)
    inter = interlineado or fuente.get_linesize()
    for i, ln in enumerate(out[:lineas_max]):
        ajustado(p, fuente, ln, x, y + i * inter, ancho, color, contorno=(30, 20, 40))
    return y + len(out[:lineas_max]) * inter
