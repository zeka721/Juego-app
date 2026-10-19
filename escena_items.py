"""Escena ITEMS: la mochila, el equipo de pesca y la tienda (pantalla del menu principal).

Tres pestanas grandes:
    Objetos  inventario con cantidades, filtro por categoria, paginas y detalle.
    Equipo   las 5 ranuras de pesca (cana, cuerda, carrete, anzuelo, barco): equipar y comprar.
    Tienda   Comprar (semillas, despensa, granja y equipo) y Vender (tus objetos).
Todo se maneja con el cursor (Boton con permanencia). Sin castigos: si faltan monedas
solo se avisa con un mensaje amable.
"""

import math

import pygame

import catalogo
from ajustes import ANCHO, ALTO
from catalogo import (CATEGORIAS, EQUIPO, EQUIPO_SLOTS, dibujar_item, info, pieza,
                      precio_venta, stats_equipo)
from escena import Escena
from nucleo import (Boton, TextoFlotante, aclarar, escribir, explosion, fondo, oscurecer,
                    panel)

# ---------------------------------------------------------------- colores
TINTA = (80, 50, 28)              # texto oscuro sobre papel
TINTA_SUAVE = (130, 95, 60)
PAPEL = (255, 248, 228)
MADERA = (128, 84, 48)
MADERA_CLARA = (160, 112, 66)
COLOR_CAT = {"fruta": (230, 80, 70), "verdura": (90, 180, 90), "granja": (225, 170, 60),
             "pesca": (70, 150, 225), "despensa": (190, 140, 90), "semilla": (110, 190, 60),
             "comida": (240, 120, 60), "especial": (160, 110, 230), "otro": (150, 150, 170),
             "equipo": (50, 170, 170)}
COLOR_NIVEL = {1: (190, 150, 100), 2: (90, 180, 110), 3: (80, 140, 220), 4: (170, 110, 230),
               5: (255, 195, 40)}
POR_PAGINA = 12
COLUMNAS = 4
CAT_TIENDA = [("semilla", "Semillas"), ("fruta", "Frutas"), ("despensa", "Despensa"), ("granja", "Granja")]
EXPLICA = {
    "cana": "Fuerza: levanta peces más grandes.",
    "cuerda": "Aguanta más sin romperse.",
    "carrete": "Cuerda más larga: lanza más lejos y más hondo.",
    "anzuelo": "Clava mejor: el pez no se suelta.",
}
ZONAS = {1: "la orilla y el lago", 2: "el mar cercano", 3: "el mar abierto",
         4: "las aguas profundas"}
NOMBRE_RANURA = dict(EQUIPO_SLOTS)


def _nivel_max(ranura):
    return max(d["nivel"] for d in EQUIPO[ranura].values())


def _fmt(n):
    return f"{int(n):,}".replace(",", ".")


# ---------------------------------------------------------------- utilidades de dibujo
class BotonF(Boton):
    """Boton cuyo texto se encoge si no cabe."""

    def dibujar(self, pantalla, fuente):
        texto, self.texto = self.texto, ""
        super().dibujar(pantalla, fuente)
        self.texto = texto
        if texto:
            ajustado(pantalla, fuente, texto, self.rect.centerx, self.rect.centery - 2,
                     self.rect.width - 24, (255, 255, 255), contorno=(30, 30, 50))


def ajustado(p, fuente, texto, x, y, ancho, color, ancla="centro", contorno=None):
    """Escribe el texto y, si no cabe en 'ancho', lo encoge para que no se corte."""
    base = fuente.render(str(texto), True, color)
    w, h = base.get_size()
    if w > ancho:
        base = pygame.transform.smoothscale(base, (int(ancho), max(1, int(h * ancho / w))))
        w, h = base.get_size()
    px = {"centro": x - w / 2, "izq": x, "der": x - w}[ancla]
    py = y - h / 2
    if contorno:
        sombra = fuente.render(str(texto), True, contorno)
        if sombra.get_width() != w:
            sombra = pygame.transform.smoothscale(sombra, (w, h))
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                if dx or dy:
                    p.blit(sombra, (px + dx, py + dy))
    p.blit(base, (px, py))
    return pygame.Rect(px, py, w, h)


def parrafo(p, fuente, texto, x, y, ancho, color=TINTA, interlineado=None, maximo=6):
    """Texto en varias lineas. Devuelve la y siguiente."""
    interlineado = interlineado or fuente.get_linesize()
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if fuente.size(prueba)[0] > ancho and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    for i, l in enumerate(lineas[:maximo]):
        ajustado(p, fuente, l, x, y + i * interlineado, ancho, color, ancla="izq")
    return y + min(len(lineas), maximo) * interlineado


def moneda(p, x, y, r=12):
    pygame.draw.circle(p, (200, 140, 20), (int(x), int(y)), r)
    pygame.draw.circle(p, (255, 215, 60), (int(x), int(y)), r - 2)
    pygame.draw.circle(p, (255, 240, 150), (int(x - r * 0.25), int(y - r * 0.25)), max(2, r // 4))


def barras_nivel(p, x, y, nivel, maximo, w=22, h=14, sep=4):
    """Barritas de nivel: las llenas con el color del nivel."""
    for i in range(maximo):
        r = pygame.Rect(x + i * (w + sep), y, w, h)
        if i < nivel:
            pygame.draw.rect(p, COLOR_NIVEL.get(nivel, (90, 180, 110)), r, border_radius=5)
            pygame.draw.rect(p, oscurecer(COLOR_NIVEL.get(nivel, (90, 180, 110)), 0.45), r, 2,
                             border_radius=5)
        else:
            pygame.draw.rect(p, (225, 215, 195), r, border_radius=5)
            pygame.draw.rect(p, (180, 165, 140), r, 2, border_radius=5)


def dibujar_pieza(p, ranura, nivel, x, y, tam=56):
    """Icono sencillo de una pieza de pesca (el color cambia con el nivel)."""
    c = COLOR_NIVEL.get(nivel, (190, 150, 100))
    osc = oscurecer(c, 0.5)
    r = tam / 2
    x, y = int(x), int(y)
    if ranura == "cana":
        a = (x - int(r * 0.8), y + int(r * 0.85))
        b = (x + int(r * 0.7), y - int(r * 0.8))
        pygame.draw.line(p, osc, a, b, 8)
        pygame.draw.line(p, c, a, b, 4)
        pygame.draw.line(p, (60, 60, 70), b, (x + int(r * 0.8), y + int(r * 0.2)), 2)
        pygame.draw.circle(p, (230, 80, 80), (x + int(r * 0.8), y + int(r * 0.25)), 4)
        pygame.draw.circle(p, (110, 70, 40), (x - int(r * 0.6), y + int(r * 0.65)), 7)
    elif ranura == "cuerda":
        for k in range(4):
            pygame.draw.ellipse(p, c, (x - int(r * 0.8) + k * 3, y - int(r * 0.6) + k * 4,
                                       int(r * 1.6) - k * 6, int(r * 1.2) - k * 8), 4)
        pygame.draw.line(p, osc, (x + int(r * 0.5), y + int(r * 0.4)), (x + int(r * 0.95), y + int(r * 0.9)), 4)
    elif ranura == "carrete":
        pygame.draw.circle(p, osc, (x, y), int(r * 0.85))
        pygame.draw.circle(p, c, (x, y), int(r * 0.85) - 3)
        pygame.draw.circle(p, osc, (x, y), int(r * 0.5), 3)
        pygame.draw.circle(p, (245, 240, 225), (x, y), int(r * 0.2))
        pygame.draw.line(p, (110, 80, 50), (x + int(r * 0.2), y - int(r * 0.2)), (x + int(r * 0.95), y - int(r * 0.8)), 5)
        pygame.draw.circle(p, (110, 80, 50), (x + int(r * 0.95), y - int(r * 0.8)), 6)
    elif ranura == "anzuelo":
        pygame.draw.line(p, (90, 90, 100), (x, y - int(r * 0.95)), (x, y + int(r * 0.2)), 5)
        pygame.draw.arc(p, c, (x - int(r * 0.7), y - int(r * 0.2), int(r * 1.4), int(r * 1.2)),
                        math.pi, 2 * math.pi + 0.7, 6)
        pygame.draw.arc(p, osc, (x - int(r * 0.7), y - int(r * 0.2), int(r * 1.4), int(r * 1.2)),
                        math.pi, 2 * math.pi + 0.7, 2)
        pygame.draw.polygon(p, c, [(x - int(r * 0.7), y + int(r * 0.4)), (x - int(r * 0.4), y + int(r * 0.15)),
                                   (x - int(r * 0.35), y + int(r * 0.5))])
        pygame.draw.circle(p, (90, 90, 100), (x, y - int(r * 0.95)), 5, 2)
    else:                                              # barco
        casco = [(x - int(r * 0.95), y + int(r * 0.1)), (x + int(r * 0.95), y + int(r * 0.1)),
                 (x + int(r * 0.6), y + int(r * 0.7)), (x - int(r * 0.6), y + int(r * 0.7))]
        pygame.draw.polygon(p, c, casco)
        pygame.draw.polygon(p, osc, casco, 3)
        pygame.draw.line(p, (110, 80, 50), (x, y + int(r * 0.1)), (x, y - int(r * 0.9)), 4)
        vela = [(x + 3, y - int(r * 0.85)), (x + int(r * (0.35 + 0.12 * nivel)), y - int(r * 0.1)),
                (x + 3, y - int(r * 0.1))]
        pygame.draw.polygon(p, (250, 250, 255), vela)
        pygame.draw.polygon(p, (150, 150, 170), vela, 2)
        pygame.draw.arc(p, (80, 150, 230), (x - int(r * 0.95), y + int(r * 0.5), int(r * 1.9), int(r * 0.6)),
                        math.pi, 2 * math.pi, 3)


def dibujar_objeto(p, ent, x, y, tam):
    if ent["kind"] == "equipo":
        dibujar_pieza(p, ent["ranura"], ent["nivel"], x, y, tam)
    else:
        dibujar_item(p, ent["id"], x, y, tam)


# =====================================================================
class ItemsEscena(Escena):
    X_GRID = 250
    ANCHO_TARJ = 158
    SEP = 8

    def __init__(self, app):
        super().__init__(app)
        try:                                   # registra los platos "plato_*" si el modulo existe
            import recetas  # noqa: F401
        except Exception:
            pass
        self.tab = "objetos"
        self.modo = "comprar"
        self.ranura = "cana"
        self.filtro = {"objetos": None, "comprar": None, "vender": None}
        self.pagina = {"objetos": 0, "comprar": 0, "vender": 0}
        self.sel = {"objetos": None, "comprar": None, "vender": None}
        self.cant = 1
        self.confirmar = False
        self.oferta = None                     # pieza recien comprada, para equiparla
        self.msg = ("", TINTA, 0.0)
        self.flotantes = []
        self.particulas = []
        self.volver = BotonF((24, ALTO - 78, 170, 56), "Volver", (150, 150, 170))
        self.tabs = {
            "objetos": BotonF((24, 14, 290, 66), "Objetos", (235, 150, 60)),
            "tienda": BotonF((324, 14, 290, 66), "Tienda", (110, 180, 80)),
        }
        self.acciones = []
        self.construir()

    # ------------------------------------------------------------ atajos
    @property
    def perfil(self):
        return self.app.ctx.perfil

    @property
    def snd(self):
        return self.app.ctx.sonidos

    def contexto(self):
        if self.tab == "objetos":
            return "objetos"
        if self.tab == "tienda":
            return self.modo
        return None

    def decir(self, texto, color=TINTA):
        self.msg = (texto, color, 4.0)

    # ------------------------------------------------------------ datos
    def todas(self, k):
        """Entradas de la lista (sin filtrar) para 'objetos', 'vender' o 'comprar'."""
        per = self.perfil
        orden = {c: i for i, (c, _) in enumerate(CATEGORIAS)}
        res = []
        if k in ("objetos", "vender"):
            for ident, n in per.inventario.items():
                if int(n) > 0:
                    d = info(ident)
                    res.append(dict(id=ident, kind="item", cat=d["cat"], cant=int(n),
                                    nombre=d["nombre"], precio=d["precio"]))
            res.sort(key=lambda e: (orden.get(e["cat"], 99), e["nombre"]))
        else:
            for ident, d in catalogo.ITEMS.items():
                if d["precio"] > 0 and d["cat"] in ("semilla", "fruta", "despensa", "granja"):
                    res.append(dict(id=ident, kind="item", cat=d["cat"], cant=per.cantidad(ident),
                                    nombre=d["nombre"], precio=d["precio"]))
            res.sort(key=lambda e: (orden.get(e["cat"], 99), e["nombre"]))
            # el equipo de pesca ya no se vende aqui: se craftea en el taller de la Expedicion de pesca
        return res

    def categorias_de(self, k):
        if k == "comprar":
            return [(None, "Todo")] + CAT_TIENDA
        cats = [(None, "Todo")] + list(CATEGORIAS)
        if any(e["cat"] not in dict(CATEGORIAS) for e in self.todas(k)):
            cats.append(("otro", "Otros"))
        return cats

    @staticmethod
    def _en_cat(ent, cat):
        if cat is None:
            return True
        if cat == "otro":
            return ent["cat"] not in dict(CATEGORIAS)
        return ent["cat"] == cat

    def visibles(self, k):
        return [e for e in self.todas(k) if self._en_cat(e, self.filtro[k])]

    def seleccionada(self, k):
        for e in self.todas(k):
            if e["id"] == self.sel[k]:
                return e
        return None

    # ------------------------------------------------------------ construccion de botones
    def construir(self):
        """Crea los botones de la pantalla actual (se llama al cambiar algo importante)."""
        self.acciones = []
        self.tarjetas = []
        k = self.contexto()
        if k:
            self._construir_lista(k)
        else:
            self._construir_equipo()
        self.b_equipar_ya = None
        if self.oferta and self.tab == "tienda":
            self.b_equipar_ya = BotonF((1000, ALTO - 78, 256, 56), "Equiparla ya", (60, 160, 190))
            self.acciones.append((self.b_equipar_ya, self._equipar_oferta))

    def _construir_lista(self, k):
        add = self.acciones.append
        ya = 102
        if self.tab == "tienda":
            self.b_modo = {
                "comprar": BotonF((self.X_GRID, 102, 200, 52), "Comprar", (110, 180, 80)),
                "vender": BotonF((self.X_GRID + 210, 102, 200, 52), "Vender", (230, 130, 60)),
            }
            for m, b in self.b_modo.items():
                add((b, lambda m=m: self._cambiar_modo(m)))
            ya = 166
        self.y_grid = ya
        # columna de categorias
        self.b_cats = []
        x, y = 24, 102
        for cat, nombre in self.categorias_de(k):
            b = BotonF((x, y, 212, 48), "", COLOR_CAT.get(cat, (200, 160, 80)) if cat else (200, 150, 70))
            self.b_cats.append((cat, nombre, b))
            add((b, lambda c=cat: self._cambiar_filtro(c)))
            y += 53
        # paginas y tarjetas
        lista = self.visibles(k)
        total = max(1, math.ceil(len(lista) / POR_PAGINA))
        self.pagina[k] = max(0, min(self.pagina[k], total - 1))
        pag = self.pagina[k]
        self.total_pag = total
        h_t = 128 if self.tab == "objetos" else 124
        self.h_tarj = h_t
        self.ents_pag = lista[pag * POR_PAGINA:(pag + 1) * POR_PAGINA]
        for i, ent in enumerate(self.ents_pag):
            col, fil = i % COLUMNAS, i // COLUMNAS
            r = (self.X_GRID + col * (self.ANCHO_TARJ + self.SEP), ya + fil * (h_t + 6),
                 self.ANCHO_TARJ, h_t)
            b = Boton(r, "", COLOR_CAT.get(ent["cat"], (150, 150, 170)))
            self.tarjetas.append((ent, b))
            add((b, lambda e=ent: self._elegir(e)))
        yp = ya + 3 * (h_t + 6) + 4
        self.y_pag = yp
        self.b_ant = BotonF((self.X_GRID, yp, 210, 52), "< Anterior", (70, 150, 230))
        self.b_sig = BotonF((self.X_GRID + 446, yp, 210, 52), "Siguiente >", (70, 150, 230))
        self.b_ant.activo = pag > 0
        self.b_sig.activo = pag < total - 1
        add((self.b_ant, lambda: self._pasar(-1)))
        add((self.b_sig, lambda: self._pasar(1)))
        # panel de detalle (comprar / vender)
        self.b_menos = self.b_mas = self.b_accion = self.b_todo = self.b_si = self.b_no = None
        sel = self.seleccionada(k)
        if self.tab == "tienda" and sel is not None:
            if k == "comprar":
                if sel["kind"] == "item":
                    self.b_menos = BotonF((946, 400, 72, 64), "-", (70, 150, 230))
                    self.b_mas = BotonF((1164, 400, 72, 64), "+", (70, 150, 230))
                    add((self.b_menos, lambda: self._cant(-1)))
                    add((self.b_mas, lambda: self._cant(1)))
                self.b_accion = BotonF((946, 508, 290, 78), "Comprar", (110, 180, 80))
                add((self.b_accion, self._comprar))
            else:
                if self.confirmar:
                    self.b_si = BotonF((946, 420, 290, 68), "Sí, vender todo", (230, 130, 60))
                    self.b_no = BotonF((946, 504, 290, 68), "No, mejor no", (150, 150, 170))
                    add((self.b_si, self._vender_todo))
                    add((self.b_no, self._cancelar_confirmar))
                else:
                    self.b_accion = BotonF((946, 420, 290, 68), "Vender 1", (110, 180, 80))
                    self.b_todo = BotonF((946, 504, 290, 68), "Vender todo", (230, 130, 60))
                    self.b_todo.activo = sel["cant"] > 1
                    add((self.b_accion, self._vender_uno))
                    add((self.b_todo, self._pedir_confirmar))

    def _construir_equipo(self):
        add = self.acciones.append
        self.b_ranuras = []
        for i, (r, _) in enumerate(EQUIPO_SLOTS):
            b = BotonF((24, 102 + i * 98, 276, 90), "", (200, 150, 70))
            self.b_ranuras.append((r, b))
            add((b, lambda r=r: self._elegir_ranura(r)))
        per = self.perfil
        self.b_piezas = []
        piezas = sorted(EQUIPO[self.ranura].items(), key=lambda kv: kv[1]["nivel"])
        for i, (ident, d) in enumerate(piezas):
            y = 102 + i * 100
            propia = ident in per.equipo_propio or d["precio"] <= 0
            puesta = per.equipo.get(self.ranura) == ident
            if puesta:
                b = None
            elif propia:
                b = BotonF((730, y + 18, 170, 58), "Equipar", (60, 160, 190))
                add((b, lambda i=ident: self._equipar(i)))
            else:
                b = BotonF((730, y + 18, 170, 58), f"Comprar {_fmt(d['precio'])}", (235, 150, 60))
                add((b, lambda i=ident: self._comprar_pieza(i)))
            self.b_piezas.append((ident, d, propia, puesta, b, pygame.Rect(316, y, 596, 92)))

    # ------------------------------------------------------------ acciones
    def _cambiar_tab(self, tab):
        if tab == self.tab:
            return
        self.tab = tab
        self.confirmar = False
        self.oferta = None
        self.snd.reproducir("click")
        self.construir()

    def _cambiar_modo(self, m):
        if m == self.modo:
            return
        self.modo = m
        self.confirmar = False
        self.cant = 1
        self.snd.reproducir("click")
        self.construir()

    def _cambiar_filtro(self, cat):
        k = self.contexto()
        if cat != self.filtro[k]:
            self.filtro[k] = cat
            self.pagina[k] = 0
            self.snd.reproducir("click")
            self.construir()

    def _pasar(self, d):
        k = self.contexto()
        self.pagina[k] += d
        self.snd.reproducir("click")
        self.construir()

    def _elegir(self, ent):
        k = self.contexto()
        self.sel[k] = ent["id"]
        self.cant = 1
        self.confirmar = False
        self.snd.reproducir("click")
        self.construir()

    def _cant(self, d):
        self.cant = max(1, min(10, self.cant + d))
        self.snd.reproducir("click")

    def _elegir_ranura(self, r):
        if r != self.ranura:
            self.ranura = r
            self.snd.reproducir("click")
            self.construir()

    def _celebrar(self, x, y, texto, color=(255, 215, 60)):
        self.flotantes.append(TextoFlotante(texto, x, y, color, vida=1.3, subida=70))
        explosion(self.particulas, x, y, color, n=16, vida=0.8)

    def _comprar(self):
        sel = self.seleccionada("comprar")
        if sel is None:
            return
        per = self.perfil
        if sel["kind"] == "equipo":
            self._comprar_pieza(sel["id"])
            return
        n = self.cant
        costo = sel["precio"] * n
        if not per.gastar(costo):
            falta = costo - per.monedas
            self.snd.reproducir("error")
            self.decir(f"Te faltan {_fmt(falta)} monedas. ¡Juega para ganar más!", (170, 60, 40))
            return
        per.dar(sel["id"], n)
        per.guardar()
        self.snd.reproducir("moneda")
        self.decir(f"¡Compraste {n} {sel['nombre']}!", (40, 130, 60))
        self._celebrar(1090, 380, f"+{n}")
        self.cant = 1
        self.oferta = None
        self.construir()

    def _comprar_pieza(self, ident):
        per = self.perfil
        datos = pieza(ident)
        if datos is None:
            return
        ranura, d = datos
        if ident in per.equipo_propio:
            return
        if not per.gastar(d["precio"]):
            falta = d["precio"] - per.monedas
            self.snd.reproducir("error")
            self.decir(f"Te faltan {_fmt(falta)} monedas. ¡Juega para ganar más!", (170, 60, 40))
            return
        per.equipo_propio.append(ident)
        per.guardar()
        self.snd.reproducir("moneda")
        self._celebrar(1090 if self.tab == "tienda" else 820, 400, "¡Nuevo!")
        if self.tab == "tienda":
            self.oferta = ident
            self.decir(f"¡Compraste {d['nombre']}! ¿La equipamos?", (40, 130, 60))
        else:
            self.decir(f"¡Compraste {d['nombre']}! Ahora toca Equipar.", (40, 130, 60))
        self.construir()

    def _equipar(self, ident):
        per = self.perfil
        datos = pieza(ident)
        if datos is None:
            return
        ranura, d = datos
        if ident not in per.equipo_propio:
            if d["precio"] > 0:
                self.snd.reproducir("error")
                self.decir("Primero hay que comprarla.", (170, 60, 40))
                return
            per.equipo_propio.append(ident)          # las piezas gratis siempre son tuyas
        per.equipo[ranura] = ident
        per.guardar()
        self.snd.reproducir("ok")
        self.decir(f"¡Listo! Ahora usas: {d['nombre']}", (40, 130, 60))
        self.construir()

    def _equipar_oferta(self):
        ident, self.oferta = self.oferta, None
        if ident:
            self._equipar(ident)

    def _vender(self, ident, n):
        per = self.perfil
        n = min(n, per.cantidad(ident))
        if n <= 0:
            return
        ganancia = precio_venta(ident) * n
        if not per.quitar(ident, n):
            return
        per.ganar(ganancia)
        per.guardar()
        self.snd.reproducir("moneda")
        self.decir(f"Vendiste {n} {info(ident)['nombre']}: +{_fmt(ganancia)} monedas", (40, 130, 60))
        self._celebrar(1090, 400, f"+{_fmt(ganancia)}")
        self.confirmar = False
        self.construir()

    def _vender_uno(self):
        sel = self.seleccionada("vender")
        if sel:
            self._vender(sel["id"], 1)

    def _pedir_confirmar(self):
        self.confirmar = True
        self.snd.reproducir("click")
        self.construir()

    def _cancelar_confirmar(self):
        self.confirmar = False
        self.snd.reproducir("click")
        self.construir()

    def _vender_todo(self):
        sel = self.seleccionada("vender")
        if sel:
            self._vender(sel["id"], sel["cant"])

    # ------------------------------------------------------------ bucle
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        txt, col, t = self.msg
        if t > 0:
            self.msg = (txt, col, t - dt)
        self.flotantes = [f for f in self.flotantes if f.actualizar(dt)]
        self.particulas = [x for x in self.particulas if x.actualizar(dt)]
        if self.volver.actualizar(dt, ctrl):
            self.snd.reproducir("click")
            self.app.ir_menu()
            return
        for nombre, b in self.tabs.items():
            if b.actualizar(dt, ctrl):
                self._cambiar_tab(nombre)
                return
        # los botones de la pantalla; si uno se pulsa, la pantalla se reconstruye
        pulsado = None
        for b, fn in list(self.acciones):
            if b.actualizar(dt, ctrl) and pulsado is None:
                pulsado = fn
        if pulsado:
            pulsado()

    def tecla_esc(self):
        self.app.ir_menu()

    # ------------------------------------------------------------ dibujo
    def dibujar(self, p):
        fondo(p, (255, 226, 170), (238, 186, 120))
        self._dibujar_cabecera(p)
        k = self.contexto()
        if k:
            self._dibujar_lista(p, k)
        else:
            self._dibujar_equipo(p)
        self._dibujar_pie(p)
        for x in self.particulas:
            x.dibujar(p)
        for f in self.flotantes:
            f.dibujar(p, self.f.normal)

    def _dibujar_cabecera(self, p):
        pygame.draw.rect(p, MADERA, (0, 0, ANCHO, 94))
        for y in (31, 62):
            pygame.draw.line(p, oscurecer(MADERA, 0.25), (0, y), (ANCHO, y), 2)
        pygame.draw.rect(p, oscurecer(MADERA, 0.45), (0, 92, ANCHO, 5))
        for nombre, b in self.tabs.items():
            sel = nombre == self.tab
            b.color = {"objetos": (235, 150, 60), "equipo": (60, 160, 190),
                       "tienda": (110, 180, 80)}[nombre] if sel else (175, 140, 105)
            b.dibujar(p, self.f.grande)
            if sel:
                pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(10, 10), 5, border_radius=26)
        panel(p, (944, 14, 312, 66), color=PAPEL, alfa=255, radio=20, borde=(90, 60, 30))
        moneda(p, 975, 47, 17)
        ajustado(p, self.f.grande, _fmt(self.perfil.monedas), 1000, 47, 240, TINTA, ancla="izq")

    def _dibujar_pie(self, p):
        self.volver.dibujar(p, self.f.normal)
        txt, col, t = self.msg
        if t <= 0 or not txt:
            txt, col = {"objetos": "Toca un objeto para ver sus datos.",
                        "equipo": "Elige una ranura y equipa lo mejor que tengas.",
                        "tienda": "Compra con tus monedas o vende lo que te sobra."}[self.tab], TINTA_SUAVE
        ancho = 770 if not self.oferta or self.tab != "tienda" else 770
        panel(p, (210, ALTO - 78, ancho, 56), color=PAPEL, alfa=235, radio=18, borde=(90, 60, 30))
        ajustado(p, self.f.normal, txt, 210 + ancho / 2, ALTO - 50, ancho - 30, col)
        if self.b_equipar_ya:
            self.b_equipar_ya.dibujar(p, self.f.normal)

    # ---- pestanas Objetos y Tienda
    def _dibujar_lista(self, p, k):
        # columna de categorias
        todas = self.todas(k)
        for cat, nombre, b in self.b_cats:
            n = sum(1 for e in todas if self._en_cat(e, cat))
            if k == "comprar" and cat is None:
                n = len(todas)
            sel = self.filtro[k] == cat
            b.dibujar(p, self.f.normal)
            if sel:
                pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(8, 8), 5, border_radius=24)
            ajustado(p, self.f.normal, nombre, b.rect.x + 18, b.rect.centery - 2, 118, (255, 255, 255),
                     ancla="izq", contorno=(60, 40, 20))
            bx = b.rect.right - 34
            pygame.draw.circle(p, PAPEL, (bx, b.rect.centery), 22)
            pygame.draw.circle(p, (90, 60, 30), (bx, b.rect.centery), 22, 2)
            ajustado(p, self.f.chica if n > 99 else self.f.normal, str(n) if n < 1000 else "999+",
                     bx, b.rect.centery, 38, TINTA)
        # botones de modo (tienda)
        if self.tab == "tienda":
            for m, b in self.b_modo.items():
                b.color = ((110, 180, 80) if m == "comprar" else (230, 130, 60)) if m == self.modo \
                    else (175, 140, 105)
                b.dibujar(p, self.f.normal)
                if m == self.modo:
                    pygame.draw.rect(p, (255, 235, 120), b.rect.inflate(8, 8), 5, border_radius=24)
        # tarjetas
        sel_id = self.sel[k]
        if not self.tarjetas:
            r = pygame.Rect(self.X_GRID, self.y_grid, 656, 3 * (self.h_tarj + 6) - 6)
            panel(p, r, color=PAPEL, alfa=235, radio=22, borde=(150, 110, 60))
            cat = dict(self.categorias_de(k)).get(self.filtro[k], "")
            if k == "comprar":
                aviso, sub = "Ya tienes todo lo de esta sección.", "¡Qué buen equipo!"
            else:
                aviso = "Todavía no tienes nada aquí"
                sub = "Juega y cocina para llenar tu mochila." if self.filtro[k] is None else \
                    f"Nada de {cat.lower()} por ahora."
            ajustado(p, self.f.grande, aviso, r.centerx, r.centery - 24, r.width - 40, TINTA)
            ajustado(p, self.f.normal, sub, r.centerx, r.centery + 28, r.width - 40, TINTA_SUAVE)
        for ent, b in self.tarjetas:
            self._tarjeta(p, k, ent, b, ent["id"] == sel_id)
        # paginas
        self.b_ant.dibujar(p, self.f.normal)
        self.b_sig.dibujar(p, self.f.normal)
        pag = self.pagina[k]
        panel(p, (self.X_GRID + 220, self.y_pag, 216, 52), color=PAPEL, alfa=235, radio=16,
              borde=(150, 110, 60))
        ajustado(p, self.f.normal, f"Página {pag + 1} de {self.total_pag}", self.X_GRID + 328,
                 self.y_pag + 26, 200, TINTA)
        # franja de datos (solo Objetos)
        if self.tab == "objetos":
            inv = self.perfil.inventario
            total = sum(int(v) for v in inv.values())
            tipos = sum(1 for v in inv.values() if int(v) > 0)
            r = pygame.Rect(self.X_GRID, self.y_pag + 62, 656, 48)
            panel(p, r, color=(255, 240, 200), alfa=240, radio=16, borde=(150, 110, 60))
            ajustado(p, self.f.normal,
                     f"Polvo especial: {_fmt(self.perfil.polvo)}      Tipos: {tipos}      "
                     f"Total: {_fmt(total)}", r.centerx, r.centery, r.width - 24, TINTA)
        # panel derecho
        self._dibujar_detalle(p, k)

    def _tarjeta(self, p, k, ent, b, elegida):
        r = b.rect
        borde = COLOR_CAT.get(ent["cat"], (150, 150, 170))
        pygame.draw.rect(p, oscurecer(borde, 0.4), r.move(0, 4), border_radius=18)
        pygame.draw.rect(p, aclarar(PAPEL, 0.4) if b.encima else PAPEL, r, border_radius=18)
        pygame.draw.rect(p, borde, r, 6, border_radius=18)
        if elegida:
            pygame.draw.rect(p, (255, 220, 60), r.inflate(8, 8), 5, border_radius=22)
        dibujar_objeto(p, ent, r.centerx, r.y + 38, 58)
        ajustado(p, self.f.chica, ent["nombre"], r.centerx, r.y + 78, r.width - 14, TINTA)
        if k == "objetos":
            ajustado(p, self.f.normal, f"x{_fmt(ent['cant'])}", r.centerx, r.bottom - 22, r.width - 16,
                     (150, 70, 20))
        elif k == "vender":
            ajustado(p, self.f.chica, f"x{_fmt(ent['cant'])}", r.x + 12, r.bottom - 20, 62,
                     (150, 70, 20), ancla="izq")
            moneda(p, r.right - 64, r.bottom - 20, 10)
            ajustado(p, self.f.normal, _fmt(precio_venta(ent["id"])), r.right - 48, r.bottom - 20, 44,
                     TINTA, ancla="izq")
        else:
            moneda(p, r.centerx - 28, r.bottom - 22, 11)
            ajustado(p, self.f.normal, _fmt(ent["precio"]), r.centerx - 12, r.bottom - 22,
                     r.width // 2 - 8, TINTA, ancla="izq")
        if b.dwell > 0:
            from ajustes import DWELL_SEG
            barra_r = pygame.Rect(r.x + 14, r.bottom - 12, r.width - 28, 7)
            pygame.draw.rect(p, (230, 215, 190), barra_r, border_radius=4)
            pygame.draw.rect(p, (255, 200, 40), (barra_r.x, barra_r.y,
                                                 max(7, barra_r.width * min(1, b.dwell / DWELL_SEG)),
                                                 barra_r.height), border_radius=4)

    def _dibujar_detalle(self, p, k):
        r = pygame.Rect(926, 102, 330, 524)
        panel(p, r, color=PAPEL, alfa=240, radio=24, borde=(150, 110, 60))
        sel = self.seleccionada(k)
        if sel is None:
            ajustado(p, self.f.normal, "Toca un objeto", r.centerx, r.centery - 20, r.width - 30, TINTA_SUAVE)
            ajustado(p, self.f.normal, "para verlo aquí", r.centerx, r.centery + 18, r.width - 30, TINTA_SUAVE)
            return
        cx = r.centerx
        color = COLOR_CAT.get(sel["cat"], (150, 150, 170))
        pygame.draw.circle(p, aclarar(color, 0.7), (cx, 168), 62)
        pygame.draw.circle(p, color, (cx, 168), 62, 5)
        dibujar_objeto(p, sel, cx, 168, 100)
        ajustado(p, self.f.grande, sel["nombre"], cx, 252, r.width - 24, TINTA)
        if sel["kind"] == "equipo":
            cat_txt = f"{NOMBRE_RANURA[sel['ranura']]} · nivel {sel['nivel']}"
            desc = sel["desc"]
        else:
            cat_txt = dict(CATEGORIAS).get(sel["cat"], "Otros")
            desc = info(sel["id"])["desc"]
        chip = pygame.Rect(0, 0, min(r.width - 40, self.f.chica.size(cat_txt)[0] + 30), 30)
        chip.center = (cx, 288)
        pygame.draw.rect(p, color, chip, border_radius=15)
        ajustado(p, self.f.chica, cat_txt, cx, 288, chip.width - 12, (255, 255, 255))
        parrafo(p, self.f.chica, desc or " ", r.x + 20, 322, r.width - 40, TINTA, 24, 3)
        if k == "objetos":
            ajustado(p, self.f.normal, f"Tienes: {_fmt(sel['cant'])}", cx, 428, r.width - 30, (150, 70, 20))
            moneda(p, r.x + 46, 480, 14)
            ajustado(p, self.f.normal, f"Vale {_fmt(precio_venta(sel['id']))} cada uno", r.x + 70, 480,
                     r.width - 90, TINTA, ancla="izq")
            ajustado(p, self.f.chica, "Véndelo en la Tienda.", cx, 530, r.width - 30, TINTA_SUAVE)
        elif k == "comprar":
            self._detalle_comprar(p, r, sel)
        else:
            self._detalle_vender(p, r, sel)

    def _detalle_comprar(self, p, r, sel):
        cx = r.centerx
        if sel["kind"] == "item":
            ajustado(p, self.f.chica, f"Tienes: {_fmt(sel['cant'])}", cx, 374, r.width - 30, TINTA_SUAVE)
            self.b_menos.dibujar(p, self.f.grande)
            self.b_mas.dibujar(p, self.f.grande)
            ajustado(p, self.f.grande, str(self.cant), cx, 432, 100, TINTA)
            n = self.cant
        else:
            ajustado(p, self.f.normal, "Una sola pieza", cx, 432, r.width - 30, TINTA_SUAVE)
            n = 1
        total = sel["precio"] * n
        moneda(p, cx - 70, 490, 14)
        ajustado(p, self.f.normal, f"Total: {_fmt(total)}", cx - 48, 490, 170, TINTA, ancla="izq")
        alcanza = self.perfil.monedas >= total
        self.b_accion.color = (110, 180, 80) if alcanza else (170, 150, 120)
        self.b_accion.dibujar(p, self.f.grande)
        if not alcanza:
            ajustado(p, self.f.chica, f"Te faltan {_fmt(total - self.perfil.monedas)} monedas",
                     cx, 608, r.width - 20, (170, 60, 40))

    def _detalle_vender(self, p, r, sel):
        cx = r.centerx
        ajustado(p, self.f.normal, f"Tienes: {_fmt(sel['cant'])}", cx, 372, r.width - 30, (150, 70, 20))
        pu = precio_venta(sel["id"])
        if self.confirmar:
            ajustado(p, self.f.normal, f"¿Vender {_fmt(sel['cant'])} por {_fmt(pu * sel['cant'])}?",
                     cx, 400, r.width - 24, TINTA)
            self.b_si.dibujar(p, self.f.normal)
            self.b_no.dibujar(p, self.f.normal)
        else:
            moneda(p, r.x + 40, 404, 12)
            ajustado(p, self.f.normal, f"Cada uno: {_fmt(pu)} monedas", r.x + 62, 400, r.width - 80,
                     TINTA, ancla="izq")
            self.b_accion.texto = f"Vender 1  (+{_fmt(pu)})"
            self.b_todo.texto = f"Vender todo  (+{_fmt(pu * sel['cant'])})"
            self.b_accion.dibujar(p, self.f.normal)
            self.b_todo.dibujar(p, self.f.normal)
            if sel["cant"] <= 1:
                ajustado(p, self.f.chica, "Solo tienes uno.", cx, 594, r.width - 20, TINTA_SUAVE)

    # ---- pestana Equipo
    def _dibujar_equipo(self, p):
        per = self.perfil
        stats = stats_equipo(per.equipo)
        # ranuras
        for r_id, b in self.b_ranuras:
            sel = r_id == self.ranura
            nivel = stats[r_id]
            rect = b.rect
            pygame.draw.rect(p, oscurecer(MADERA_CLARA, 0.4), rect.move(0, 5), border_radius=20)
            pygame.draw.rect(p, aclarar(PAPEL, 0.4) if b.encima else PAPEL, rect, border_radius=20)
            pygame.draw.rect(p, (60, 160, 190) if sel else (170, 130, 80), rect, 6 if sel else 4,
                             border_radius=20)
            if sel:
                pygame.draw.rect(p, (255, 220, 60), rect.inflate(8, 8), 4, border_radius=24)
            dibujar_pieza(p, r_id, nivel, rect.x + 48, rect.centery - 2, 58)
            ajustado(p, self.f.normal, NOMBRE_RANURA[r_id], rect.x + 92, rect.y + 24, 170, TINTA, ancla="izq")
            pid = per.equipo.get(r_id) or catalogo.EQUIPO_INICIAL[r_id]
            nombre = EQUIPO[r_id].get(pid, {"nombre": "?"})["nombre"]
            ajustado(p, self.f.chica, nombre, rect.x + 92, rect.y + 52, 172, TINTA_SUAVE, ancla="izq")
            maxn = _nivel_max(r_id)
            barras_nivel(p, rect.x + 92, rect.y + 64, nivel, maxn, w=max(10, 120 // maxn - 4), h=14)
            if b.dwell > 0:
                self._dwell(p, b, rect)
        # piezas de la ranura elegida
        for ident, d, propia, puesta, b, rect in self.b_piezas:
            pygame.draw.rect(p, oscurecer(MADERA_CLARA, 0.4), rect.move(0, 5), border_radius=20)
            pygame.draw.rect(p, PAPEL if (propia or puesta) else (238, 228, 205), rect, border_radius=20)
            pygame.draw.rect(p, (90, 190, 100) if puesta else (170, 130, 80), rect, 6 if puesta else 4,
                             border_radius=20)
            dibujar_pieza(p, self.ranura, d["nivel"], rect.x + 52, rect.centery - 2, 62)
            if not (propia or puesta):
                cand = pygame.Surface((26, 30), pygame.SRCALPHA)
                pygame.draw.rect(cand, (120, 120, 140), (0, 12, 26, 18), border_radius=4)
                pygame.draw.arc(cand, (120, 120, 140), (5, 0, 16, 22), 0, math.pi, 4)
                p.blit(cand, (rect.x + 78, rect.y + 56))
            ajustado(p, self.f.normal, d["nombre"], rect.x + 102, rect.y + 22, 290, TINTA, ancla="izq")
            barras_nivel(p, rect.x + 102, rect.y + 42, d["nivel"], _nivel_max(self.ranura), w=26, h=14)
            ajustado(p, self.f.chica, d["desc"], rect.x + 102, rect.y + 72, 290, TINTA_SUAVE, ancla="izq")
            if puesta:
                ajustado(p, self.f.normal, "EQUIPADA", rect.right - 100, rect.centery, 170, (40, 140, 60))
            elif b is not None:
                b.dibujar(p, self.f.normal)
        # poder de pesca
        r = pygame.Rect(926, 102, 330, 524)
        panel(p, r, color=PAPEL, alfa=240, radio=24, borde=(150, 110, 60))
        ajustado(p, self.f.grande, "Poder de pesca", r.centerx, 134, r.width - 50, TINTA)
        for i, (r_id, nom) in enumerate(EQUIPO_SLOTS):
            y = 172 + i * 89
            nivel = stats[r_id]
            maxn = _nivel_max(r_id)
            ajustado(p, self.f.normal, nom, r.x + 18, y + 12, 100, TINTA, ancla="izq")
            barras_nivel(p, r.x + 126, y + 5, nivel, maxn, w=max(12, 170 // maxn - 4), h=15)
            if r_id == "barco":
                texto = f"Llegas a {ZONAS.get(nivel, ZONAS[4])}."
            else:
                texto = EXPLICA[r_id]
            parrafo(p, self.f.chica, texto, r.x + 18, y + 40, r.width - 36, TINTA_SUAVE, 22, 2)

    def _dwell(self, p, b, rect):
        from ajustes import DWELL_SEG
        barra_r = pygame.Rect(rect.x + 18, rect.bottom - 14, rect.width - 36, 7)
        pygame.draw.rect(p, (230, 215, 190), barra_r, border_radius=4)
        pygame.draw.rect(p, (255, 200, 40), (barra_r.x, barra_r.y,
                                             max(7, barra_r.width * min(1, b.dwell / DWELL_SEG)),
                                             barra_r.height), border_radius=4)
