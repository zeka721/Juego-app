"""Escena GRANJA: Mi granja (animales), Mi huerto (cultivos) y Mi piscicultivo (estanques).

No es un minijuego: es una pantalla que se abre desde el menu principal.
Todo se maneja con el cursor (permanencia, clic o golpe; regar y cosechar tambien con un tajo).

El tiempo avanza por DIAS DE JUEGO (perfil.dia). El estado vive en perfil.granja:
    {"ultimo_dia": n,
     "huerto":    {"parcelas": [None | {"c": cultivo, "dias": n, "regada": bool}, ...]},   # 6..12
     "animales":  [{"t": "gallina"|"oveja"|"vaca", "falta": dias para producir, "listo": productos}, ...],
     "estanques": [{"peces": {especie: n}, "alim": bool, "huevas": n, "alga": n}, ...]}      # 1..3
Los peces vivos recien capturados estan en perfil.peces_vivos (el "balde").
"""

import math
import random

import pygame

import arte
import arte_granja as ag
import catalogo
import cocina_datos  # noqa: F401  (registra cebolla, pimiento, espinaca, pepino y sus semillas)
from ajustes import ANCHO, ALTO
from escena import Escena
from nucleo import Boton, TextoFlotante, aclarar, barra, escribir, explosion, oscurecer, panel

V2 = pygame.Vector2

# ---------------- reglas de la granja ----------------
PARCELAS_INICIO = 6
PARCELAS_MAX = 12
PRECIO_PARCELA = {7: 60, 8: 80, 9: 100, 10: 120, 11: 140, 12: 160}
PROB_SEMILLA_EXTRA = 0.35

ANIMALES = {   # tipo: (nombre, precio, maximo, dias para producir, producto)
    "gallina": ("Gallina", 60, 4, 1, "huevo"),
    "oveja": ("Oveja", 120, 3, 3, "lana"),
    "vaca": ("Vaca", 200, 3, 2, "leche"),
}
ESCALA_ANIMAL = {"gallina": 1.2, "oveja": 1.1, "vaca": 1.0}
MAX_ANIMALES = sum(v[2] for v in ANIMALES.values())
MAX_PRODUCTOS = 3          # productos que se acumulan esperando en cada animal

ESTANQUES_MAX = 3
PRECIO_ESTANQUE = {2: 150, 3: 300}
CAPACIDAD_ESTANQUE = 6
MAX_HUEVAS = 3
MAX_ALGA = 2
PROB_ALGA = 0.2

NOMBRES_CULTIVO = {"zanahoria": "Zanahoria", "tomate": "Tomate", "lechuga": "Lechuga",
                   "papa": "Papa", "maiz": "Maíz", "calabaza": "Calabaza", "cebolla": "Cebolla",
                   "pimiento": "Pimiento", "espinaca": "Espinaca", "pepino": "Pepino"}

SECCIONES = ("granja", "huerto", "pisci")
NOMBRE_SECCION = {"granja": "Mi granja", "huerto": "Mi huerto", "pisci": "Mi piscicultivo"}

DWELL_ACCION = 0.6         # segundos con el cursor encima para actuar sin clic


# =====================================================================
#  Datos de peces (la estructura de arte.PECES puede variar)
# =====================================================================

def info_pez(ident):
    """(nombre, rareza) de una especie de arte.PECES."""
    e = arte.PECES.get(ident)
    if isinstance(e, dict):
        return e.get("nombre", ident), int(e.get("rareza", 1))
    if isinstance(e, (tuple, list)) and e:
        rareza = e[1] if len(e) > 1 and isinstance(e[1], int) else 1
        return str(e[0]), rareza
    return str(ident).capitalize(), 1


def pos_pez(rect, idx, t):
    """Posicion y direccion del pez numero idx nadando dentro de rect."""
    ph = idx * 1.73 + 0.4
    sp = 0.28 + 0.06 * (idx % 4)
    x = rect.centerx + (rect.width / 2 - 46) * math.sin(t * sp + ph)
    y = rect.centery + (rect.height / 2 - 46) * math.sin(t * sp * 0.8 + ph * 1.3)
    mirando = 1 if math.cos(t * sp + ph) >= 0 else -1
    return x, y, mirando


# =====================================================================
#  Boton con icono (para comprar, dar comida, dormir)
# =====================================================================

class BotonIcono(Boton):
    def __init__(self, rect, titulo, color, icono=None, sub="", precio=None):
        super().__init__(rect, "", color)
        self.titulo = titulo
        self.base = color
        self.icono = icono          # funcion (pantalla, x, y)
        self.sub = sub
        self.precio = precio        # None = sin precio
        self.gris = False
        self.compacto = False       # titulo arriba y precio debajo, centrados

    def dibujar(self, p, f):
        self.color = (150, 156, 172) if self.gris else self.base
        super().dibujar(p, f.normal)
        r = self.rect
        if self.compacto:
            escribir(p, f.normal, self.titulo, r.centerx, r.centery - 22)
            if self.precio is not None:
                ag.dibujar_moneda(p, r.centerx - 30, r.centery + 22, 14)
                escribir(p, f.normal, self.precio, r.centerx - 10, r.centery + 22, ancla="izq")
            return
        x0 = r.x + 20
        if self.icono:
            self.icono(p, r.x + 34, r.centery - 2)
            x0 = r.x + 62
        yt = r.centery - (11 if self.sub else 0)
        escribir(p, f.normal, self.titulo, x0, yt, ancla="izq")
        if self.sub:
            escribir(p, f.chica, self.sub, x0, r.centery + 15, ancla="izq", grosor=1)
        if self.precio is not None:
            ag.dibujar_moneda(p, r.right - 72, r.centery - (2 if not self.sub else 8), 12)
            escribir(p, f.normal, self.precio, r.right - 55, r.centery - (2 if not self.sub else 8), ancla="izq")


def _icono_item(ident, tam=40):
    return lambda p, x, y: catalogo.dibujar_item(p, ident, x, y, tam)


# =====================================================================
#  La escena
# =====================================================================

class GranjaEscena(Escena):
    def __init__(self, app, rng=None, seccion="granja"):
        super().__init__(app)
        self.perfil = app.ctx.perfil
        self.sonidos = app.ctx.sonidos
        self.rng = rng or random.Random()
        self.seccion = seccion if seccion in SECCIONES else "granja"
        self.espera = 0.5                    # ignora el cursor un momento al abrir la escena
        self.dw = {}                         # tiempo de permanencia por zona
        self.cool = {}
        self.tocado = set()
        self.textos = []
        self.parts = []
        self.aviso = ("", 0.0)
        self.banner = ("", 0.0)
        self.noche = 0.0
        self.regando = 0.0
        self.mano = V2(ANCHO / 2, ALTO / 2)
        self.sel = "zanahoria"
        self.mano_riega = None
        self._normalizar()
        self._elegir_semilla()

        f = self.f
        self.tabs = []
        for i, (sec, x, w) in enumerate((("granja", 16, 200), ("huerto", 224, 200), ("pisci", 432, 280))):
            self.tabs.append((sec, Boton((x, 8, w, 60), NOMBRE_SECCION[sec], (90, 120, 175))))
        self.b_volver = Boton((16, 642, 190, 64), "Volver", (230, 120, 90))
        self.b_dormir = BotonIcono((1012, 642, 252, 64), "Dormir", (90, 90, 190),
                                   lambda p, x, y: ag.dibujar_luna(p, x, y, 15), "pasar un día")
        self.b_animal = {}
        for i, tipo in enumerate(("gallina", "oveja", "vaca")):
            nom, precio, mx, _, prod = ANIMALES[tipo]
            self.b_animal[tipo] = BotonIcono((222 + i * 262, 642, 250, 64), nom, (80, 160, 90),
                                             self._icono_animal(tipo), "", precio)
        self.b_parcela = BotonIcono((0, 0, 200, 150), "Parcela", (120, 160, 80), None, "", 0)
        self.b_parcela.compacto = True
        self.b_comida = [BotonIcono((0, 0, 270, 56), "Dar comida", (80, 160, 110),
                                    _icono_item("alimento_peces", 38), "") for _ in range(ESTANQUES_MAX)]
        self.b_estanque = [BotonIcono((0, 0, 270, 110), "Estanque", (70, 150, 205), None, "", 0)
                           for _ in range(ESTANQUES_MAX)]
        for b in self.b_estanque:
            b.compacto = True

        self._sincronizar(inicio=True)

    # ------------------------------------------------------------ estado
    @property
    def g(self):
        return self.perfil.granja

    def _icono_animal(self, tipo):
        def f(p, x, y):
            ag.dibujar_animal(p, tipo, x, y + 22, 0.32 if tipo == "vaca" else 0.42, 0, 0, 1)
        return f

    def _normalizar(self):
        """Deja perfil.granja y perfil.peces_vivos completos y validos (acepta partidas vacias)."""
        p = self.perfil
        if not isinstance(p.granja, dict):
            p.granja = {}
        g = p.granja
        # --- huerto
        h = g.get("huerto")
        if not isinstance(h, dict):
            h = g["huerto"] = {}
        par = h.get("parcelas")
        if not isinstance(par, list):
            par = []
        par = par[:PARCELAS_MAX]
        while len(par) < PARCELAS_INICIO:
            par.append(None)
        for i, c in enumerate(par):
            if isinstance(c, dict) and c.get("c") in ag.DIAS_CULTIVO:
                dias = c.get("dias", 0)
                c["dias"] = max(0, min(int(dias), ag.DIAS_CULTIVO[c["c"]])) if isinstance(dias, (int, float)) else 0
                c["regada"] = bool(c.get("regada", False))
            else:
                par[i] = None
        h["parcelas"] = par
        # --- animales
        an = g.get("animales")
        lista = []
        if isinstance(an, list):
            for a in an:
                if isinstance(a, dict) and a.get("t") in ANIMALES:
                    falta = a.get("falta", 0)
                    listo = a.get("listo", 0)
                    lista.append({"t": a["t"],
                                  "falta": max(0, int(falta)) if isinstance(falta, (int, float)) else 0,
                                  "listo": max(0, min(MAX_PRODUCTOS, int(listo))) if isinstance(listo, (int, float)) else 0})
        if not lista:
            lista = [{"t": "gallina", "falta": 0, "listo": 0}]       # empiezas con una gallina
        g["animales"] = lista[:MAX_ANIMALES]
        # --- estanques
        es = g.get("estanques")
        lista = []
        if isinstance(es, list):
            for e in es[:ESTANQUES_MAX]:
                if not isinstance(e, dict):
                    continue
                peces = {}
                if isinstance(e.get("peces"), dict):
                    for k, v in e["peces"].items():
                        if isinstance(v, (int, float)) and int(v) > 0:
                            peces[str(k)] = int(v)
                lista.append({"peces": peces, "alim": bool(e.get("alim", False)),
                              "huevas": max(0, min(MAX_HUEVAS, int(e.get("huevas", 0) or 0))),
                              "alga": max(0, min(MAX_ALGA, int(e.get("alga", 0) or 0)))})
        if not lista:
            lista = [{"peces": {}, "alim": False, "huevas": 0, "alga": 0}]
        g["estanques"] = lista
        # --- balde
        if not isinstance(p.peces_vivos, dict):
            p.peces_vivos = {}
        for k in list(p.peces_vivos):
            v = p.peces_vivos[k]
            if not isinstance(v, (int, float)) or int(v) <= 0:
                del p.peces_vivos[k]
            else:
                p.peces_vivos[k] = int(v)
        if not isinstance(g.get("ultimo_dia"), int) or isinstance(g.get("ultimo_dia"), bool):
            g["ultimo_dia"] = self.dia

    @property
    def dia(self):
        try:
            return max(0, int(self.perfil.dia))
        except (TypeError, ValueError):
            return 0

    @property
    def parcelas(self):
        return self.g["huerto"]["parcelas"]

    @property
    def animales(self):
        return self.g["animales"]

    @property
    def estanques(self):
        return self.g["estanques"]

    def _guardar(self):
        self.perfil.guardar()

    # ------------------------------------------------------------ el tiempo
    def _sincronizar(self, inicio=False):
        """Simula los dias de juego que pasaron desde la ultima vez (sin tiempo real)."""
        g = self.g
        dia = self.dia
        ultimo = g.get("ultimo_dia")
        if not isinstance(ultimo, int):
            ultimo = dia
        ultimo = min(ultimo, dia)
        n = min(dia - ultimo, 400)
        for _ in range(n):
            self.pasar_dia()
        if g.get("ultimo_dia") != dia:
            g["ultimo_dia"] = dia
            self._guardar()
        if n > 0:
            self.banner = ("¡Día %d!" % dia if n == 1 else "¡Pasaron %d días!" % n, 2.4)
            self.sonidos.nota(660, 0.25)
            return n
        return 0

    def pasar_dia(self):
        """Un dia de juego: crecen los cultivos regados, los animales alimentados producen, los
        estanques alimentados dan huevas. Usa self.rng (inyectable)."""
        for c in self.parcelas:
            if c:
                if c["regada"] and c["dias"] < ag.DIAS_CULTIVO[c["c"]]:
                    c["dias"] += 1
                c["regada"] = False
        for a in self.animales:
            if a["falta"] > 0:
                a["falta"] -= 1
                if a["falta"] == 0:
                    a["listo"] = min(MAX_PRODUCTOS, a["listo"] + 1)
        for e in self.estanques:
            if e["alim"]:
                total = sum(e["peces"].values())
                if total > 0:
                    prob = min(0.8, 0.12 * total + 0.08 * (len(e["peces"]) - 1))
                    if self.rng.random() < prob:
                        e["huevas"] = min(MAX_HUEVAS, e["huevas"] + 1)
                    if self.rng.random() < PROB_ALGA:
                        e["alga"] = min(MAX_ALGA, e["alga"] + 1)
            e["alim"] = False

    def dormir(self):
        """Sube el dia de juego en 1 (la granja avanza sola en el siguiente cuadro)."""
        self.perfil.dia = self.dia + 1
        self.noche = 1.7
        self.sonidos.nota(330, 0.3)
        self._guardar()
        return True

    # ------------------------------------------------------------ acciones: avisos
    def _aviso(self, texto, seg=2.4):
        self.aviso = (texto, seg)

    def _texto(self, texto, x, y, color=(255, 255, 255)):
        self.textos.append(TextoFlotante(texto, x, y, color, 1.2, 70))

    def _sonido(self, nombre):
        self.sonidos.reproducir(nombre)

    # ------------------------------------------------------------ acciones: huerto
    def semillas_total(self):
        return sum(self.perfil.cantidad("semilla_" + c) for c in ag.CULTIVOS)

    def _elegir_semilla(self):
        if self.perfil.cantidad("semilla_" + self.sel) > 0:
            return
        for c in ag.CULTIVOS:
            if self.perfil.cantidad("semilla_" + c) > 0:
                self.sel = c
                return

    def etapa(self, c):
        """Etapa visual 0..3 de una parcela plantada."""
        if not c:
            return 0
        T = ag.DIAS_CULTIVO[c["c"]]
        if c["dias"] >= T:
            return 3
        return min(2, int(c["dias"] * 3 / T))

    def lista_cosecha(self, i):
        c = self.parcelas[i]
        return bool(c) and c["dias"] >= ag.DIAS_CULTIVO[c["c"]]

    def plantar(self, i, cultivo=None):
        cultivo = cultivo or self.sel
        if not (0 <= i < len(self.parcelas)) or self.parcelas[i] is not None or cultivo not in ag.DIAS_CULTIVO:
            return False
        if not self.perfil.quitar("semilla_" + cultivo, 1):
            self._aviso("No tienes semillas de %s" % NOMBRES_CULTIVO[cultivo].lower())
            self._sonido("error")
            return False
        self.parcelas[i] = {"c": cultivo, "dias": 0, "regada": False}
        self._elegir_semilla()
        self._guardar()
        self._sonido("pop")
        r = self.rect_parcela(i)
        explosion(self.parts, r.centerx, r.centery + 10, (140, 98, 62), 10, vel_max=180, vida=0.5, radio=4)
        return True

    def regar(self, i):
        c = self.parcelas[i] if 0 <= i < len(self.parcelas) else None
        if not c or c["regada"] or self.lista_cosecha(i):
            return False
        c["regada"] = True
        self._guardar()
        self._sonido("splash")
        r = self.rect_parcela(i)
        explosion(self.parts, r.centerx, r.centery, (90, 160, 235), 14, vel_max=200, vida=0.6, radio=4, gravedad=300)
        return True

    def cosechar(self, i):
        if not (0 <= i < len(self.parcelas)) or not self.lista_cosecha(i):
            return False
        c = self.parcelas[i]
        n = self.rng.randint(2, 3)
        self.perfil.dar(c["c"], n)
        r = self.rect_parcela(i)
        self._texto("+%d %s" % (n, NOMBRES_CULTIVO[c["c"]]), r.centerx, r.y + 30, (255, 240, 120))
        if self.rng.random() < PROB_SEMILLA_EXTRA:
            self.perfil.dar("semilla_" + c["c"], 1)
            self._texto("+1 semilla", r.centerx, r.y + 62, (180, 255, 160))
        self.parcelas[i] = None
        self._elegir_semilla()
        self._guardar()
        self._sonido("premio")
        explosion(self.parts, r.centerx, r.centery, (255, 220, 80), 16, vel_max=300, vida=0.7)
        return True

    def precio_parcela(self):
        n = len(self.parcelas)
        return PRECIO_PARCELA.get(n + 1) if n < PARCELAS_MAX else None

    def comprar_parcela(self):
        precio = self.precio_parcela()
        if precio is None:
            self._aviso("Ya tienes todas las parcelas")
            return False
        if not self.perfil.gastar(precio):
            self._aviso("Te faltan monedas")
            self._sonido("error")
            return False
        self.parcelas.append(None)
        self._guardar()
        self._sonido("moneda")
        self._aviso("¡Nueva parcela!")
        return True

    # ------------------------------------------------------------ acciones: animales
    def contar_animales(self, tipo):
        return sum(1 for a in self.animales if a["t"] == tipo)

    def comprar_animal(self, tipo):
        nom, precio, mx, _, _ = ANIMALES[tipo]
        if self.contar_animales(tipo) >= mx or len(self.animales) >= MAX_ANIMALES:
            self._aviso("Ya tienes todas las %s" % (nom.lower() + "s"))
            return False
        if not self.perfil.gastar(precio):
            self._aviso("Te faltan monedas")
            self._sonido("error")
            return False
        self.animales.append({"t": tipo, "falta": 0, "listo": 0})
        self._guardar()
        self._sonido("moneda")
        self._aviso("¡Nueva %s!" % nom.lower() if tipo != "gallina" else "¡Nueva gallina!")
        return True

    def alimentar_animal(self, i):
        if not (0 <= i < len(self.animales)):
            return False
        a = self.animales[i]
        if a["falta"] > 0:
            return False
        if not self.perfil.quitar("alimento_animal", 1):
            self._aviso("No tienes grano para animales")
            self._sonido("error")
            return False
        a["falta"] = ANIMALES[a["t"]][3]
        self._guardar()
        self._sonido("pop")
        x, y, _ = self.pos_animal(i)
        explosion(self.parts, x, y - 30, (230, 195, 90), 8, vel_max=150, vida=0.5, radio=4)
        self._texto("¡Ñam!", x, y - 80, (255, 230, 150))
        return True

    def recoger_animal(self, i):
        if not (0 <= i < len(self.animales)):
            return False
        a = self.animales[i]
        if a["listo"] <= 0:
            return False
        prod = ANIMALES[a["t"]][4]
        n = a["listo"]
        self.perfil.dar(prod, n)
        a["listo"] = 0
        self._guardar()
        self._sonido("ok")
        x, y, _ = self.pos_animal(i)
        self._texto("+%d %s" % (n, catalogo.nombre_item(prod)), x, y - 100, (255, 245, 170))
        explosion(self.parts, x, y - 100, (255, 235, 120), 12, vel_max=240, vida=0.6)
        return True

    # ------------------------------------------------------------ acciones: piscicultivo
    def peces_en(self, est):
        return sum(est["peces"].values())

    def lista_peces(self, est):
        """Lista (una por pez) de las especies conocidas del estanque, en orden estable."""
        out = []
        for esp in sorted(est["peces"]):
            if esp in arte.PECES:
                out += [esp] * est["peces"][esp]
        return out

    def comprar_estanque(self):
        n = len(self.estanques)
        if n >= ESTANQUES_MAX:
            return False
        precio = PRECIO_ESTANQUE[n + 1]
        if not self.perfil.gastar(precio):
            self._aviso("Te faltan monedas")
            self._sonido("error")
            return False
        self.estanques.append({"peces": {}, "alim": False, "huevas": 0, "alga": 0})
        self._guardar()
        self._sonido("moneda")
        self._aviso("¡Nuevo estanque!")
        return True

    def balde_a_estanque(self, especie, est=None):
        """Pasa un pez vivo del balde a un estanque con espacio. Devuelve el indice o -1."""
        if self.perfil.peces_vivos.get(especie, 0) <= 0:
            return -1
        orden = ([est] if est is not None else []) + [k for k in range(len(self.estanques)) if k != est]
        for k in orden:
            if k is not None and 0 <= k < len(self.estanques):
                e = self.estanques[k]
                if self.peces_en(e) < CAPACIDAD_ESTANQUE:
                    self.perfil.peces_vivos[especie] -= 1
                    if self.perfil.peces_vivos[especie] <= 0:
                        del self.perfil.peces_vivos[especie]
                    e["peces"][especie] = e["peces"].get(especie, 0) + 1
                    self._guardar()
                    self._sonido("splash")
                    rect = self.rect_estanque(k)["agua"]
                    explosion(self.parts, rect.centerx, rect.centery, (190, 230, 255), 14, vel_max=220, vida=0.6,
                              radio=4, gravedad=300)
                    self._texto(info_pez(especie)[0], rect.centerx, rect.y + 30, (255, 255, 255))
                    return k
        self._aviso("Los estanques están llenos")
        self._sonido("error")
        return -1

    def alimentar_estanque(self, i):
        if not (0 <= i < len(self.estanques)):
            return False
        e = self.estanques[i]
        if e["alim"]:
            return False
        if self.peces_en(e) <= 0:
            self._aviso("Primero pasa peces del balde")
            return False
        if not self.perfil.quitar("alimento_peces", 1):
            self._aviso("No tienes comida de peces")
            self._sonido("error")
            return False
        e["alim"] = True
        self._guardar()
        self._sonido("pop")
        rect = self.rect_estanque(i)["agua"]
        for k in range(10):
            explosion(self.parts, rect.x + 30 + k * (rect.width - 60) / 9, rect.y + 20, (150, 200, 110), 1,
                      vel_min=10, vel_max=40, vida=0.9, radio=4, gravedad=120)
        return True

    def recoger_huevas(self, i):
        e = self.estanques[i]
        if e["huevas"] <= 0:
            return False
        n = e["huevas"]
        self.perfil.dar("huevas", n)
        e["huevas"] = 0
        self._guardar()
        self._sonido("ok")
        r = self.rect_estanque(i)["slot"]
        self._texto("+%d Huevas" % n, r.x + 70, r.y + 330, (255, 190, 130))
        return True

    def recoger_alga(self, i):
        e = self.estanques[i]
        if e["alga"] <= 0:
            return False
        n = e["alga"]
        self.perfil.dar("alga", n)
        e["alga"] = 0
        self._guardar()
        self._sonido("ok")
        r = self.rect_estanque(i)["slot"]
        self._texto("+%d Alga" % n, r.x + 150, r.y + 330, (160, 255, 190))
        return True

    def cosechar_pez(self, i, especie):
        e = self.estanques[i]
        if e["peces"].get(especie, 0) <= 0:
            return False
        e["peces"][especie] -= 1
        if e["peces"][especie] <= 0:
            del e["peces"][especie]
        self.perfil.dar("pescado", 1)
        self._guardar()
        self._sonido("premio")
        rect = self.rect_estanque(i)["agua"]
        self._texto("+1 Pescado", rect.centerx, rect.centery, (170, 220, 255))
        explosion(self.parts, rect.centerx, rect.centery, (200, 235, 255), 12, vel_max=220, vida=0.6, gravedad=300)
        return True

    # ------------------------------------------------------------ geometria
    def rect_parcela(self, i):
        col, fila = i % 4, i // 4
        return pygame.Rect(290 + col * 220, 100 + fila * 168, 200, 150)

    def rect_semilla(self, k):
        return pygame.Rect(16, 92 + k * 52, 236, 48)

    def pos_animal(self, i):
        """(x, y de los pies, direccion) del animal i, que pasea un poco."""
        col, fila = i % 5, i // 5
        ph = i * 1.9
        x = 250 + col * 195 + 16 * math.sin(self.t * 0.33 + ph)
        y = 418 + fila * 130
        return x, y, (1 if math.cos(self.t * 0.33 + ph) >= 0 else -1)

    def rect_estanque(self, i):
        x = 300 + i * 310
        slot = pygame.Rect(x, 96, 290, 484)
        return {"slot": slot, "agua": pygame.Rect(x + 14, 150, 262, 232),
                "boton": pygame.Rect(x + 10, 484, 270, 56)}

    def rect_balde(self, k):
        return pygame.Rect(26, 168 + k * 56, 252, 52)

    # ------------------------------------------------------------ zonas de cursor
    def _zona(self, clave, ctrl, dt, dentro, tiempo=DWELL_ACCION, tajo=False):
        """True cuando el cursor activa la zona: clic/golpe (o tajo si se permite) al instante, o permanencia."""
        if not dentro or self.espera > 0:
            return False
        self.tocado.add(clave)
        if self.cool.get(clave, 0) > 0:
            return False
        self.dw[clave] = self.dw.get(clave, 0.0) + dt
        if ctrl.clic or ctrl.golpe or (tajo and ctrl.cortando) or self.dw[clave] >= tiempo:
            self.dw[clave] = 0.0
            self.cool[clave] = 0.6
            return True
        return False

    def _frac(self, clave, tiempo=DWELL_ACCION):
        return min(1.0, self.dw.get(clave, 0.0) / tiempo)

    # ------------------------------------------------------------ actualizar
    def actualizar(self, dt, ctrl):
        super().actualizar(dt, ctrl)
        self.espera = max(0.0, self.espera - dt)
        self.mano = V2(ctrl.pos)
        self._sincronizar()
        self.tocado = set()
        for k in list(self.cool):
            self.cool[k] -= dt
            if self.cool[k] <= 0:
                del self.cool[k]
        self.noche = max(0.0, self.noche - dt)
        self.textos = [x for x in self.textos if x.actualizar(dt)]
        self.parts = [x for x in self.parts if x.actualizar(dt)]
        txt, seg = self.aviso
        self.aviso = (txt, max(0.0, seg - dt))
        txt, seg = self.banner
        self.banner = (txt, max(0.0, seg - dt))
        self.regando = max(0.0, self.regando - dt)

        for sec, b in self.tabs:
            if b.actualizar(dt, ctrl) and sec != self.seccion:
                self.seccion = sec
                self._sonido("click")
                self.dw.clear()
                self.textos = []
                self.espera = 0.4
        if self.b_volver.actualizar(dt, ctrl):
            self._sonido("click")
            self.app.ir_menu()
            return
        if self.b_dormir.actualizar(dt, ctrl):
            self.dormir()

        if self.seccion == "granja":
            self._act_granja(dt, ctrl)
        elif self.seccion == "huerto":
            self._act_huerto(dt, ctrl)
        else:
            self._act_pisci(dt, ctrl)

        for k in list(self.dw):
            if k not in self.tocado:
                del self.dw[k]

    # --- granja
    def _act_granja(self, dt, ctrl):
        for tipo, b in self.b_animal.items():
            if b.actualizar(dt, ctrl):
                self.comprar_animal(tipo)
        for i, a in enumerate(self.animales):
            x, y, _ = self.pos_animal(i)
            dentro = V2(ctrl.pos).distance_to((x, y - 50)) < 85 or (abs(ctrl.pos.x - x) < 55 and y - 150 < ctrl.pos.y < y)
            if a["listo"] > 0:
                if self._zona(("rec", i), ctrl, dt, dentro, 0.5, tajo=True):
                    self.recoger_animal(i)
            elif a["falta"] == 0:
                if self._zona(("com", i), ctrl, dt, dentro, 0.8):
                    self.alimentar_animal(i)

    # --- huerto
    def _act_huerto(self, dt, ctrl):
        for k, c in enumerate(ag.CULTIVOS):
            if self._zona(("sem", c), ctrl, dt, self.rect_semilla(k).collidepoint(ctrl.pos), 0.5):
                if self.perfil.cantidad("semilla_" + c) > 0:
                    self.sel = c
                    self._sonido("click")
                else:
                    self._aviso("No tienes semillas de %s" % NOMBRES_CULTIVO[c].lower())
        precio = self.precio_parcela()
        if precio is not None:
            b = self.b_parcela
            b.rect = self.rect_parcela(len(self.parcelas)).inflate(0, 0)
            b.precio = precio
            b.titulo = "Parcela"
            b.gris = self.perfil.monedas < precio
            if b.actualizar(dt, ctrl):
                if self.comprar_parcela():
                    b.espera = 1.0
                    b.dwell = 0.0
        self.mano_riega = None
        for i, c in enumerate(self.parcelas):
            r = self.rect_parcela(i)
            dentro = r.collidepoint(ctrl.pos)
            if c is None:
                if self.perfil.cantidad("semilla_" + self.sel) > 0:
                    if self._zona(("par", i), ctrl, dt, dentro, 0.7):
                        self.plantar(i)
                elif dentro and self.semillas_total() == 0 and self.aviso[1] <= 0:
                    self._aviso("No tienes semillas. Gana más jugando")
            elif self.lista_cosecha(i):
                if self._zona(("par", i), ctrl, dt, dentro, 0.5, tajo=True):
                    self.cosechar(i)
            elif not c["regada"]:
                if dentro:
                    self.mano_riega = i
                    self.regando = 0.2
                if self._zona(("par", i), ctrl, dt, dentro, 0.5, tajo=True):
                    self.regar(i)

    # --- piscicultivo
    def _act_pisci(self, dt, ctrl):
        peces = self.balde_lista()
        for k, (esp, n) in enumerate(peces[:8]):
            if self._zona(("balde", esp), ctrl, dt, self.rect_balde(k).collidepoint(ctrl.pos), 0.7):
                self.balde_a_estanque(esp)
        for i, e in enumerate(self.estanques):
            r = self.rect_estanque(i)
            b = self.b_comida[i]
            b.rect = r["boton"]
            b.gris = e["alim"] or self.peces_en(e) == 0
            b.sub = "ya comieron" if e["alim"] else "tienes %d" % self.perfil.cantidad("alimento_peces")
            if b.actualizar(dt, ctrl):
                if e["alim"]:
                    self._aviso("Ya comieron hoy")
                elif self.alimentar_estanque(i):
                    pass
            sx, sy = r["slot"].x, r["slot"].y
            if e["huevas"] > 0 and self._zona(("hue", i), ctrl, dt,
                                              V2(ctrl.pos).distance_to((sx + 60, sy + 330)) < 40, 0.5, tajo=True):
                self.recoger_huevas(i)
            if e["alga"] > 0 and self._zona(("alg", i), ctrl, dt,
                                            V2(ctrl.pos).distance_to((sx + 140, sy + 330)) < 40, 0.5, tajo=True):
                self.recoger_alga(i)
            # un pez: cursor encima (clic, golpe o permanencia larga) -> pescado
            lista = self.lista_peces(e)
            mejor, dmin = None, 50
            for k, esp in enumerate(lista):
                x, y, _ = pos_pez(r["agua"], k + i * 7, self.t)
                d = V2(ctrl.pos).distance_to((x, y))
                if d < dmin:
                    mejor, dmin = (k, esp), d
            if mejor and r["agua"].collidepoint(ctrl.pos):
                if self._zona(("pez", i, mejor[0]), ctrl, dt, True, 1.0):
                    self.cosechar_pez(i, mejor[1])
        n = len(self.estanques)
        if n < ESTANQUES_MAX:
            b = self.b_estanque[n]
            b.rect = pygame.Rect(self.rect_estanque(n)["slot"].x + 10, 240, 270, 84)
            b.precio = PRECIO_ESTANQUE[n + 1]
            b.titulo = "Nuevo estanque"
            b.gris = self.perfil.monedas < b.precio
            if b.actualizar(dt, ctrl):
                if self.comprar_estanque():
                    for bb in self.b_estanque:
                        bb.espera = 1.0
                        bb.dwell = 0.0

    def balde_lista(self):
        return [(k, v) for k, v in sorted(self.perfil.peces_vivos.items()) if k in arte.PECES and v > 0]

    # ------------------------------------------------------------ dibujar
    def dibujar(self, p):
        f = self.f
        p.blit(ag.escenario(self.seccion), (0, 0))
        ag.nubes(p, self.t, 180)
        if self.seccion == "granja":
            self._dib_granja(p)
        elif self.seccion == "huerto":
            self._dib_huerto(p)
        else:
            self._dib_pisci(p)
        for pt in self.parts:
            pt.dibujar(p)
        for tx in self.textos:
            tx.dibujar(p, f.normal)
        self._dib_barras(p)
        self._dib_avisos(p)
        if self.noche > 0:
            frac = self.noche / 1.7
            a = int(215 * math.sin(math.pi * (1 - frac)))
            s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            s.fill((10, 15, 50, max(0, a)))
            p.blit(s, (0, 0))
            if a > 60:
                ag.dibujar_luna(p, ANCHO / 2, ALTO / 2 - 70, 46)
                escribir(p, f.grande, "Dormimos...", ANCHO / 2, ALTO / 2 + 20)

    # --- barras de arriba y abajo
    def _dib_barras(self, p):
        f = self.f
        s = pygame.Surface((ANCHO, 76), pygame.SRCALPHA)
        s.fill((25, 50, 95, 175))
        p.blit(s, (0, 0))
        pygame.draw.line(p, (255, 255, 255), (0, 76), (ANCHO, 76), 3)
        s = pygame.Surface((ANCHO, ALTO - 632), pygame.SRCALPHA)
        s.fill((25, 50, 95, 175))
        p.blit(s, (0, 632))
        pygame.draw.line(p, (255, 255, 255), (0, 632), (ANCHO, 632), 3)
        for sec, b in self.tabs:
            b.color = (60, 175, 95) if sec == self.seccion else (90, 120, 175)
            b.dibujar(p, f.normal)
            if sec == self.seccion:
                pygame.draw.polygon(p, (255, 255, 255), [(b.rect.centerx - 12, 76), (b.rect.centerx + 12, 76),
                                                         (b.rect.centerx, 88)])
        # monedas y dia, y las cantidades de lo que usas
        ag.dibujar_moneda(p, 744, 38, 16)
        escribir(p, f.normal, self.perfil.monedas, 768, 38, ancla="izq")
        escribir(p, f.normal, "Día %d" % self.dia, 872, 38, color=(255, 240, 150), ancla="izq")
        for x, ident, n in ((1000, "alimento_animal", self.perfil.cantidad("alimento_animal")),
                            (1088, "alimento_peces", self.perfil.cantidad("alimento_peces")),
                            (1176, "semilla_tomate", self.semillas_total())):
            catalogo.dibujar_item(p, ident, x, 38, 38)
            escribir(p, f.normal, n, x + 24, 38, ancla="izq")
        self.b_volver.dibujar(p, f.normal)
        self.b_dormir.dibujar(p, f)
        if self.seccion == "granja":
            for tipo, b in self.b_animal.items():
                nom, precio, mx, _, prod = ANIMALES[tipo]
                cuenta = self.contar_animales(tipo)
                lleno = cuenta >= mx
                b.gris = lleno or self.perfil.monedas < precio
                b.sub = "%d de %d" % (cuenta, mx)
                b.precio = None if lleno else precio
                if lleno:
                    b.sub = "¡Completa! %d" % cuenta
                b.dibujar(p, f)
        else:
            txt = "Elige semilla, planta y riega con el cursor" if self.seccion == "huerto" \
                else ("Pasa los peces del balde al estanque" if not any(self.estanques[k]["peces"] for k in range(len(self.estanques)))
                      else "Cursor quieto sobre un pez para sacarlo del estanque")
            escribir(p, f.chica, txt, 600, 674, color=(255, 255, 255))

    def _dib_avisos(self, p):
        f = self.f
        txt, seg = self.aviso
        if seg > 0 and txt:
            w = f.normal.size(txt)[0] + 50
            panel(p, (ANCHO / 2 - w / 2, 560, w, 54), (255, 250, 225), 235, 24, (200, 140, 30))
            escribir(p, f.normal, txt, ANCHO / 2, 587, (60, 40, 20), contorno=None)
        txt, seg = self.banner
        if seg > 0 and txt:
            k = min(1.0, seg / 0.5, (2.4 - seg) / 0.3 + 0.01)
            y = 330 - 40 * (1 - min(1.0, (2.4 - seg) / 0.4))
            s = pygame.Surface((560, 100), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 235, 120, int(235 * max(0.0, min(1.0, k)))), s.get_rect(), border_radius=30)
            pygame.draw.rect(s, (200, 130, 20, int(255 * max(0.0, min(1.0, k)))), s.get_rect(), 5, border_radius=30)
            p.blit(s, (ANCHO / 2 - 280, y - 50))
            escribir(p, f.grande, txt, ANCHO / 2, y, (120, 70, 10), contorno=(255, 250, 220))

    def _anillo(self, p, clave, x, y, r, tiempo=DWELL_ACCION):
        fr = self._frac(clave, tiempo)
        if fr > 0:
            rect = pygame.Rect(0, 0, int(r * 2), int(r * 2))
            rect.center = (int(x), int(y))
            pygame.draw.arc(p, (255, 215, 60), rect, math.pi / 2, math.pi / 2 + 2 * math.pi * fr, 7)

    # --- Mi granja
    def _dib_granja(self, p):
        f = self.f
        orden = sorted(range(len(self.animales)), key=lambda i: self.pos_animal(i)[1])
        for i in orden:
            a = self.animales[i]
            x, y, m = self.pos_animal(i)
            esc = ESCALA_ANIMAL[a["t"]]
            ag.dibujar_animal(p, a["t"], x, y, esc, self.t, i * 1.3, m)
        for i, a in enumerate(self.animales):
            x, y, m = self.pos_animal(i)
            esc = ESCALA_ANIMAL[a["t"]]
            by = y - ag.ALTO_ANIMAL[a["t"]] * esc - 30
            if a["listo"] > 0:
                cx, cy = ag.dibujar_burbuja(p, x, by, 34, self.t, self._frac(("rec", i), 0.5), aviso=True)
                catalogo.dibujar_item(p, ANIMALES[a["t"]][4], cx, cy, 46)
                if a["listo"] > 1:
                    escribir(p, f.normal, "x%d" % a["listo"], cx + 30, cy + 22, (255, 245, 170))
                self._anillo(p, ("rec", i), cx, cy, 38, 0.5)
            elif a["falta"] == 0:
                cx, cy = ag.dibujar_burbuja(p, x, by, 30, self.t, self._frac(("com", i), 0.8))
                catalogo.dibujar_item(p, "alimento_animal", cx, cy, 42)
                self._anillo(p, ("com", i), cx, cy, 34, 0.8)
            else:
                txt = "¡Listo mañana!" if a["falta"] == 1 else "Listo en %d días" % a["falta"]
                escribir(p, f.chica, txt, x, y + 18, (255, 255, 255))
        escribir(p, f.chica, "Dale grano a los animales y recoge lo que producen", 640, 604, (255, 255, 255))

    # --- Mi huerto
    def _dib_huerto(self, p):
        f = self.f
        for k, c in enumerate(ag.CULTIVOS):
            r = self.rect_semilla(k)
            n = self.perfil.cantidad("semilla_" + c)
            sel = (c == self.sel)
            panel(p, r, (255, 250, 220) if sel else (255, 255, 255), 235 if n or sel else 150, 18,
                  (240, 170, 40) if sel else (70, 100, 150))
            catalogo.dibujar_item(p, "semilla_" + c, r.x + 34, r.centery, 38)
            escribir(p, f.normal, NOMBRES_CULTIVO[c], r.x + 70, r.centery - 10, (60, 50, 40), "izq", contorno=None)
            escribir(p, f.chica, "%d día%s · x%d" % (ag.DIAS_CULTIVO[c], "" if ag.DIAS_CULTIVO[c] == 1 else "s", n),
                     r.x + 70, r.centery + 12, (90, 80, 70), "izq", contorno=None)
            if self._frac(("sem", c), 0.5) > 0:
                barra(p, (r.x + 12, r.bottom - 7, r.width - 24, 5), self._frac(("sem", c), 0.5),
                      (255, 215, 60), (200, 200, 210), (120, 120, 140))
        for i, c in enumerate(self.parcelas):
            r = self.rect_parcela(i)
            dentro = r.collidepoint(self.mano)
            ag.dibujar_parcela(p, r, bool(c and c["regada"]), self.t, dentro)
            if c:
                et = self.etapa(c)
                ag.dibujar_cultivo(p, c["c"], et, r.centerx, r.centery + 32, 1.15, self.t)
                T = ag.DIAS_CULTIVO[c["c"]]
                for k in range(T):                                   # puntitos de crecimiento
                    cx = r.centerx - (T - 1) * 9 + k * 18
                    pygame.draw.circle(p, (255, 255, 255), (cx, r.bottom - 14), 6)
                    pygame.draw.circle(p, (90, 190, 235) if k < c["dias"] else (170, 170, 180), (cx, r.bottom - 14), 4)
            self._burbuja_parcela(p, i, c, r)
        if self.precio_parcela() is not None:
            self.b_parcela.dibujar(p, f)
        if self.mano_riega is not None:
            self._dib_regadera(p)

    def _burbuja_parcela(self, p, i, c, r):
        bx, by = r.right - 36, r.y + 40
        if c is None:
            if self.perfil.cantidad("semilla_" + self.sel) > 0:
                cx, cy = ag.dibujar_burbuja(p, bx, by, 27, self.t, self._frac(("par", i), 0.7))
                catalogo.dibujar_item(p, "semilla_" + self.sel, cx, cy, 36)
                self._anillo(p, ("par", i), cx, cy, 31, 0.7)
        elif self.lista_cosecha(i):
            cx, cy = ag.dibujar_burbuja(p, bx, by, 29, self.t, self._frac(("par", i), 0.5), aviso=True)
            catalogo.dibujar_item(p, c["c"], cx, cy, 40)
            self._anillo(p, ("par", i), cx, cy, 33, 0.5)
        elif not c["regada"]:
            cx, cy = ag.dibujar_burbuja(p, bx, by, 27, self.t, self._frac(("par", i), 0.5))
            ag.dibujar_gota(p, cx, cy, 15)
            self._anillo(p, ("par", i), cx, cy, 31, 0.5)

    def _dib_regadera(self, p):
        pos = self.mano
        punta = ag.dibujar_regadera(p, pos.x + 40, pos.y - 34, self.t, True)
        for k in range(4):
            fase = (self.t * 2.2 + k * 0.25) % 1.0
            ag.dibujar_gota(p, punta.x - 4 - k * 6, punta.y + 12 + fase * 52, 5)

    # --- Mi piscicultivo
    def _dib_pisci(self, p):
        f = self.f
        # balde
        r = pygame.Rect(16, 96, 272, 530)
        panel(p, r, (255, 250, 235), 225, 22, (70, 100, 150))
        ag.dibujar_cubo(p, 52, 128, 18)
        escribir(p, f.normal, "Balde", 84, 128, (60, 50, 40), "izq", contorno=None)
        peces = self.balde_lista()
        if not peces:
            self._multilinea(p, f.chica, "Pesca peces en el mar y llegarán aquí", 152, 300, 230, (90, 80, 70))
        for k, (esp, n) in enumerate(peces[:8]):
            rr = self.rect_balde(k)
            dentro = self._frac(("balde", esp), 0.7) > 0
            pygame.draw.rect(p, (255, 240, 190) if dentro else (225, 240, 252), rr, border_radius=14)
            pygame.draw.rect(p, (70, 100, 150), rr, 2, border_radius=14)
            arte.dibujar_pez(p, esp, rr.x + 44, rr.centery, 0.42 + 0.03 * info_pez(esp)[1], 1, self.t + k)
            escribir(p, f.chica, info_pez(esp)[0], rr.x + 92, rr.centery - 8, (50, 50, 70), "izq", contorno=None)
            escribir(p, f.normal, "x%d" % n, rr.right - 14, rr.centery - 4, (60, 50, 40), "der", contorno=None)
            escribir(p, f.chica, "al estanque", rr.x + 92, rr.centery + 12, (90, 110, 140), "izq", contorno=None, grosor=1)
            if dentro:
                barra(p, (rr.x + 10, rr.bottom - 8, rr.width - 20, 6), self._frac(("balde", esp), 0.7),
                      (255, 215, 60), (200, 200, 210), (120, 120, 140))
        # estanques
        for i in range(ESTANQUES_MAX):
            r = self.rect_estanque(i)
            slot = r["slot"]
            if i < len(self.estanques):
                self._dib_estanque(p, i, r)
            elif i == len(self.estanques):
                panel(p, slot, (255, 255, 255), 110, 22, (110, 140, 180))
                escribir(p, f.normal, "Más espacio", slot.centerx, slot.y + 70, (255, 255, 255))
                self.b_estanque[i].dibujar(p, f)
                escribir(p, f.chica, "Más peces, más huevas", slot.centerx, slot.y + 350, (255, 255, 255))

    def _dib_estanque(self, p, i, r):
        f = self.f
        e = self.estanques[i]
        slot, agua = r["slot"], r["agua"]
        panel(p, slot, (255, 255, 255), 125, 22, (70, 110, 160))
        n = self.peces_en(e)
        escribir(p, f.normal, "Estanque %d" % (i + 1), slot.x + 16, slot.y + 26, (255, 255, 255), "izq")
        escribir(p, f.normal, "%d/%d" % (n, CAPACIDAD_ESTANQUE), slot.right - 16, slot.y + 26,
                 (255, 240, 150) if n < CAPACIDAD_ESTANQUE else (255, 170, 140), "der")
        ag.dibujar_estanque(p, agua, self.t)
        # peces nadando
        lista = self.lista_peces(e)
        orden = []
        for k, esp in enumerate(lista):
            x, y, m = pos_pez(agua, k + i * 7, self.t)
            orden.append((y, k, esp, x, m))
        for y, k, esp, x, m in sorted(orden):
            esc = 0.5 + 0.04 * info_pez(esp)[1]
            hov = self._frac(("pez", i, k), 1.0)
            if hov > 0:
                pygame.draw.circle(p, (255, 240, 120), (int(x), int(y)), int(44 * esc + 14), 4)
                self._anillo(p, ("pez", i, k), x, y, 44 * esc + 18, 1.0)
            arte.dibujar_pez(p, esp, x, y, esc, m, self.t + k)
        if n == 0:
            escribir(p, f.chica, "Sin peces todavía", agua.centerx, agua.centery, (255, 255, 255))
        # burbujas de lo producido
        sx, sy = slot.x, slot.y
        if e["huevas"] > 0:
            cx, cy = ag.dibujar_burbuja(p, sx + 60, sy + 330, 30, self.t, self._frac(("hue", i), 0.5), aviso=True)
            catalogo.dibujar_item(p, "huevas", cx, cy, 40)
            self._anillo(p, ("hue", i), cx, cy, 34, 0.5)
            if e["huevas"] > 1:
                escribir(p, f.normal, "x%d" % e["huevas"], cx + 32, cy + 22, (255, 245, 170))
        if e["alga"] > 0:
            cx, cy = ag.dibujar_burbuja(p, sx + 140, sy + 330, 30, self.t, self._frac(("alg", i), 0.5), aviso=True)
            catalogo.dibujar_item(p, "alga", cx, cy, 40)
            self._anillo(p, ("alg", i), cx, cy, 34, 0.5)
            if e["alga"] > 1:
                escribir(p, f.normal, "x%d" % e["alga"], cx + 32, cy + 22, (255, 245, 170))
        if e["alim"]:
            escribir(p, f.chica, "¡Ya comieron!", sx + 230, sy + 330, (200, 255, 200))
        elif n > 0:
            escribir(p, f.chica, "Tienen hambre", sx + 230, sy + 330, (255, 255, 255))
        self.b_comida[i].dibujar(p, f)

    def _multilinea(self, p, fuente, texto, cx, y, ancho, color):
        palabras, linea, lineas = texto.split(), "", []
        for w in palabras:
            prueba = (linea + " " + w).strip()
            if fuente.size(prueba)[0] > ancho and linea:
                lineas.append(linea)
                linea = w
            else:
                linea = prueba
        lineas.append(linea)
        for k, l in enumerate(lineas):
            escribir(p, fuente, l, cx, y + k * 26, color, contorno=None)

    def tecla_esc(self):
        self.app.ir_menu()
