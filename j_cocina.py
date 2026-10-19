"""Cocina v2: libro de 30 recetas, ficha, habilidades y preparacion paso a paso (estilo Cooking Mama).

Flujo (la app hace la cuenta atras y llama a paso()):
  libro      Recetario abierto (6 recetas por doble pagina, 5 dobles). Se pasa de pagina con botones grandes
             (dwell). La receta que corresponde al nivel de juego sale marcada "¡Para ti!" (cocina_datos.recomendada),
             pero se puede abrir cualquier otra. Desde el libro tambien se abre la vista de las 22 habilidades.
  ficha      Pasos agrupados por fase (preparar / montar / cocinar / servir), ingredientes con cantidades y de
             donde salen, habilidades y niveles que pide, y el motivo si esta bloqueada.
  paso       Una secuencia de pasos: cada uno es un mini juego de cocina_base.crear_paso(ctx, spec, dif, mods).
             Cabecera con titulo, "Paso n de N" y fase; cuencos A..F con lo ya preparado; pausa breve de resultado.
  entrega    Plato terminado, estrellas, experiencia por habilidad, subidas de nivel y recetas nuevas.

Reglas:
  * NIVEL_MAX = 30: el nivel de juego elige la receta recomendada; la dificultad de los pasos sale del nivel de la
    receta que se cocina (cocina_datos.dif_nivel).
  * Puntos: calidad * puntos_por_paso por cada paso + bono final (puntos_bono * calidad media^2). Las estrellas
    usan cocina_datos.metas_receta. XP por paso con xp_paso / dar_xp (se gana siempre, aunque salga mal).
  * Los materiales (no los de recetas `basica`) se gastan al empezar a cocinar. Sin estrellas, o si se sale con Esc a
    medias, vuelven al inventario (quedan anotados como "pendientes" en perfil.extra["cocina"] por si se cierra todo).
  * Con 1+ estrellas: plato_<id> al botin (1 en las basicas, 2 con 3 estrellas; en las demas tantos como estrellas),
    perfil.recetas_hechas[id] += 1.
  * Mejoras de la ruleta -> Mods de los pasos: potencia = pot, alcance = alc, tiempo = tiempo (la vida extra suma
    30%), lento = lento; puntos x2 lo aplica sumar().
  * Todo se maneja con el cursor (botones con dwell); clic o golpe solo aceleran.
"""

import math
import random

import pygame

from ajustes import ANCHO, ALTO, DWELL_SEG
from nucleo import MEJORAS, Boton, Minijuego, aclarar, barra, escribir, estrella, explosion, oscurecer, V2
import arte_cocina as ac
import catalogo
import cocina_datos as cd
from cocina_base import Mods, crear_paso, fondo_cocina
import cocina_herramientas as ch
import cocina_ingredientes as ci
import cocina_platos as cp

# ----------------------------------------------------------------------------- constantes
POR_HOJA = 3
POR_DOBLE = 6
HOJA_W, HOJA_H = 572, 508
HOJA_IZQ = pygame.Rect(62, 124, HOJA_W, HOJA_H)
HOJA_DER = pygame.Rect(646, 124, HOJA_W, HOJA_H)
CARTA_W, CARTA_H, CARTA_SEP = 544, 146, 8
T_GIRO = 0.55
T_ESPERA = 0.6          # pausa antes de cada paso (para que el nino lea el titulo)
T_CIERRE = 0.8          # pausa de resultado tras cada paso
CABECERA_H = 100

COLOR_FASE = {"preparar": (110, 190, 105), "montar": (105, 160, 230), "cocinar": (235, 130, 70),
              "servir": (230, 130, 190)}
FUENTE_TXT = {"huerto": ("Huerto", (80, 170, 90)), "granja": ("Granja", (200, 160, 60)),
              "pesca": ("Pesca", (80, 150, 220)), "tienda": ("Tienda", (225, 135, 60)),
              "frutas": ("Frutas", (220, 90, 90)), "casa": ("De la casa", (150, 135, 120))}
HERR_ICONO = {"cortar": "cuchillo", "pelar": "pelador", "rayar": "rallador", "extraer": "tijera",
              "exprimir": "exprimidor", "aplastar": "guantes", "presionar": "rodillo", "moldear": "molde",
              "enrollar": "guantes", "untar": "espatula", "espolvorear": "cernidor", "decorar": "manga",
              "combinar": "tazon", "girar": "cuchara", "batir": "batidor", "cucharear": "cuchara",
              "verter": "jarra", "mover_sarten": "sarten", "saltear": "sarten", "hornear": "olla",
              "hervir": "olla", "servir": "plato"}
# estado con que queda un ingrediente en el cuenco segun la habilidad
ESTADO_HAB = {"cortar": "cortado", "pelar": "pelado", "rayar": "rallado", "extraer": "pelado", "aplastar": "masa",
              "presionar": "masa", "moldear": "masa", "batir": "batido", "girar": "entero",
              "mover_sarten": "cocido", "saltear": "cocido", "hornear": "cocido", "hervir": "cocido"}

_fuentes = {}
_iconos = {}


def _F(tam):
    f = _fuentes.get(tam)
    if f is None:
        f = _fuentes[tam] = pygame.font.SysFont("arial", tam, bold=True)
    return f


def _ajustar(texto, ancho, tam_max, tam_min=12):
    for t in range(tam_max, tam_min - 1, -1):
        f = _F(t)
        if f.size(texto)[0] <= ancho:
            return f
    return _F(tam_min)


def icono_hab(h, tam=40):
    """Icono redondo de una habilidad (su herramienta sobre el color de la habilidad)."""
    k = (h, tam)
    s = _iconos.get(k)
    if s is None:
        s = pygame.Surface((tam, tam), pygame.SRCALPHA)
        col = cd.HABILIDADES.get(h, {}).get("color", (200, 200, 210))
        pygame.draw.circle(s, aclarar(col, 0.55), (tam // 2, tam // 2), tam // 2)
        pygame.draw.circle(s, oscurecer(col, 0.25), (tam // 2, tam // 2), tam // 2, max(2, tam // 16))
        ch.dibujar_herr(s, HERR_ICONO.get(h, h), tam / 2, tam / 2, int(tam * 0.68))
        _iconos[k] = s
    return s


def nombre_ing(ident):
    if not ident:
        return ""
    if ident in catalogo.ITEMS:
        return catalogo.nombre_item(ident).lower()
    return str(ident).replace("_", " ")


def etiqueta_paso(spec):
    """'Cortar tomate', 'Combinar ingredientes'..."""
    nombre = cd.HABILIDADES[spec["h"]]["nombre"]
    if spec["h"] == "combinar":
        return nombre + " ingredientes"
    ing = spec.get("ing") or (spec.get("ings") or [None])[0] or spec.get("sobre")
    return (nombre + " " + nombre_ing(ing)).strip()


def n_dobles():
    return (len(cd.RECETAS) + POR_DOBLE - 1) // POR_DOBLE


def rect_carta(hoja_rect, i):
    return pygame.Rect(hoja_rect.x + 14, hoja_rect.y + 40 + i * (CARTA_H + CARTA_SEP), CARTA_W, CARTA_H)


def _mezcla(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def _estrellas_fila(p, x_der, y, n, r=10, sep=22):
    for i in range(5):
        lleno = i < n
        estrella(p, x_der - (4 - i) * sep, y, r, (255, 205, 50) if lleno else (225, 215, 195),
                 (170, 115, 20) if lleno else (190, 175, 150))


def _telon(p, alfa=150):
    s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    s.fill((40, 25, 15, alfa))
    p.blit(s, (0, 0))


def fase_de(spec):
    return cd.HABILIDADES[spec["h"]]["fase"]


# ----------------------------------------------------------------------------- el minijuego
class Cocina(Minijuego):
    """Ver el docstring del modulo."""

    id = "cocina"
    titulo = "Cocina"
    instruccion = "Elige una receta del libro y cocínala paso a paso: corta, mezcla, hornea y sirve."
    gesto = "Mueve el cursor"
    duracion = None
    NIVEL_MAX = 30
    etiquetas_nivel = {r["nivel"]: r["nombre"] for r in cd.RECETAS}
    fondo_arriba = (255, 238, 205)
    fondo_abajo = (255, 225, 185)

    def __init__(self, ctx, nivel=1):
        cd.migrar_habilidades(ctx.perfil)
        self.r = None
        super().__init__(ctx, nivel)
        self.perfil = ctx.perfil
        self.particulas = []
        self.fase = "libro"             # libro -> paso -> entrega
        self.vista = "libro"            # dentro del libro: libro | ficha | habilidades
        self.sel = None
        self.cur = None
        self.i = 0
        self.pasos = []
        self.espera = 0.0
        self.cerrado = False
        self.resumen = {}
        self.tazones = {}
        self.letras = []
        self.avisos = []
        self.ult = None
        self.calid = []
        self.xp = {}
        self.subidas = []
        self.t_ent = 0.0
        self.t_fin = 4.0
        self.giro = None
        self._cache_hojas = {}
        self._cache_platos = {}
        self._devolver_pendiente()
        self._abrir_libro()

    # ------------------------------------------------------------------ metas y datos
    def calcular_metas(self):
        r = getattr(self, "r", None)
        if r is None:
            try:
                r = cd.POR_ID[cd.recomendada(self.ctx.perfil, self.nivel)]
            except Exception:
                r = cd.RECETAS[0]
        return cd.metas_receta(r)

    def _datos_cocina(self):
        return self.perfil.extra.setdefault("cocina", {})

    def _devolver_pendiente(self):
        """Devuelve los materiales de una cocina anterior que no se termino."""
        datos = self._datos_cocina()
        pend = datos.get("pendiente") or {}
        if pend:
            for m, n in pend.items():
                self.perfil.dar(m, n)
            datos["pendiente"] = {}
            self.perfil.guardar()

    def cancelar(self):
        """Para aventura.Partida: se sale a medias (Esc). Devuelve los materiales."""
        if self.fase == "paso" and not self.terminado:
            self._devolver_pendiente()
            self.perfil.guardar()
            self.terminar("Cocina cancelada")

    def _plato_surf(self, r, tam):
        k = (r["id"], tam)
        s = self._cache_platos.get(k)
        if s is None:
            s = pygame.Surface((int(tam * 1.6) + 4, int(tam * 1.6) + 4), pygame.SRCALPHA)
            cp.dibujar_plato(s, r, s.get_width() / 2, s.get_height() / 2, tam)
            self._cache_platos[k] = s
        return s

    def _mods(self):
        m = self.mej
        tiempo = m.mult("tiempo") * (1.3 if m.vidas_extra() else 1.0)
        return Mods(pot=m.mult("potencia"), alc=m.mult("alcance"), tiempo=tiempo, lento=m.mult("lento"))

    # ------------------------------------------------------------------ libro: estado
    def _abrir_libro(self):
        self.fase = "libro"
        self.vista = "libro"
        self.sel = None
        self.recom = cd.recomendada(self.perfil, self.nivel)
        idx = next((i for i, r in enumerate(cd.RECETAS) if r["id"] == self.recom), 0)
        self.doble = idx // POR_DOBLE
        self._cache_hojas = {}
        self.cartas = [Boton(pygame.Rect(0, 0, CARTA_W, CARTA_H), "", espera=0.8) for _ in range(POR_DOBLE)]
        self._colocar_cartas()
        self.b_ant = Boton((30, 650, 230, 62), "Anterior", (230, 130, 60), espera=0.8)
        self.b_sig = Boton((1020, 650, 230, 62), "Siguiente", (230, 130, 60), espera=0.8)
        self.b_hab = Boton((270, 650, 220, 62), "Habilidades", (150, 100, 220), espera=0.8)
        self.b_salir = Boton((800, 650, 190, 62), "Salir", (130, 140, 170), espera=0.8)
        self.b_cerrar = Boton((520, 640, 240, 64), "Cerrar", (70, 160, 230), espera=0.8)
        self.b_volver = Boton((60, 634, 240, 64), "Volver", (70, 160, 230), espera=0.8)
        self.b_cocinar = Boton((980, 634, 250, 64), "¡A cocinar!", (90, 190, 110), espera=0.8)

    def _recetas_hoja(self, hoja):
        return cd.RECETAS[hoja * POR_HOJA:(hoja + 1) * POR_HOJA]

    def _colocar_cartas(self, doble=None):
        e = self.doble if doble is None else doble
        for k in range(POR_DOBLE):
            lado = HOJA_IZQ if k < POR_HOJA else HOJA_DER
            self.cartas[k].rect = rect_carta(lado, k % POR_HOJA)
            hoja = 2 * e + (k // POR_HOJA)
            self.cartas[k].activo = (k % POR_HOJA) < len(self._recetas_hoja(hoja))
            self.cartas[k].espera = max(self.cartas[k].espera, 0.7)
            self.cartas[k].dwell = 0.0

    def receta_en_carta(self, k, doble=None):
        e = self.doble if doble is None else doble
        lista = self._recetas_hoja(2 * e + (k // POR_HOJA))
        i = k % POR_HOJA
        return lista[i] if i < len(lista) else None

    def girar(self, d):
        """Gira la pagina (+1 siguiente, -1 anterior) si hay a donde."""
        if self.giro or self.vista != "libro":
            return False
        destino = self.doble + d
        if destino < 0 or destino >= n_dobles():
            return False
        self.giro = dict(dir=d, u=0.0, destino=destino)
        self.sonidos.reproducir("click")
        return True

    def _reiniciar_botones(self, *bs):
        for b in bs:
            b.espera = 0.8
            b.dwell = 0.0

    def abrir_ficha(self, ident):
        r = cd.POR_ID[ident]
        self.sel = r
        self.vista = "ficha"
        self._reiniciar_botones(self.b_volver, self.b_cocinar)
        self.b_cocinar.activo = cd.jugable(self.perfil, r)
        self.sonidos.reproducir("pop")

    def cerrar_ficha(self):
        self.vista = "libro"
        self.sel = None
        self._reiniciar_botones(*self.cartas, self.b_ant, self.b_sig, self.b_hab, self.b_salir)

    def abrir_habilidades(self):
        self.vista = "habilidades"
        self._reiniciar_botones(self.b_cerrar)
        self.sonidos.reproducir("pop")

    # ------------------------------------------------------------------ empezar a cocinar
    def _empezar(self, r):
        p = self.perfil
        if not cd.jugable(p, r):
            return False
        if not r["basica"] and r["mats"]:
            for m, n in r["mats"].items():
                p.quitar(m, n)
            self._datos_cocina()["pendiente"] = dict(r["mats"])
        p.guardar()
        self.r = r
        self.pasos = list(r["pasos"])
        self.dif = cd.dif_nivel(r["nivel"])
        self.mods = self._mods()
        self.metas = cd.metas_receta(r)
        self.pp = cd.puntos_por_paso(r)
        self.puntos = 0
        self.calid = []
        self.xp = {}
        self.subidas = []
        self.antes = {x["id"] for x in cd.RECETAS if cd.desbloqueada(p, x)}
        self.tazones = {}
        self.letras = sorted({s["tazon"] for s in self.pasos if s.get("tazon")})[:6]
        self.avisos = []
        self.ult = None
        self.i = 0
        self.fase = "paso"
        self.vista = "libro"
        self._nuevo_paso()
        self.sonidos.reproducir("premio")
        return True

    def _ings_receta(self):
        """Ingredientes reales (ids) que usa la receta: materiales y los de sus pasos, sin repetir."""
        vistos = []
        for m in self.r["mats"]:
            if m not in vistos:
                vistos.append(m)
        for st in self.r["pasos"]:
            for k in [st.get("ing")] + list(st.get("ings", ())):
                if k and k not in vistos:
                    vistos.append(k)
        return vistos

    def _nuevo_paso(self):
        spec = dict(self.pasos[self.i])
        if spec.get("h") == "servir":
            spec["receta_ings"] = self._ings_receta()      # para que los adornos sean coherentes con la receta
            spec["receta_id"] = self.r["id"]
        self.cur = crear_paso(self.ctx, spec, self.dif, self.mods)
        self.cerrado = False
        self.espera = T_ESPERA
        self.ult = None

    # ------------------------------------------------------------------ pasos
    def _poner_en_tazon(self, spec, q):
        """Actualiza los cuencos con el resultado de un paso (los que tienen 'tazon')."""
        letra = spec.get("tazon")
        if not letra:
            return
        h = spec["h"]
        ing = spec.get("ing")
        if h == "combinar":
            ings = list(spec.get("ings") or ([ing] if ing else []))
            nuevo = []
            for i in ings:
                est = "entero"
                for L, cont in self.tazones.items():
                    for it in cont:
                        if it[0] == i:
                            est = it[1]
                nuevo.append((i, est))
            for L in list(self.tazones):
                self.tazones[L] = [it for it in self.tazones[L] if it[0] not in ings]
            self.tazones[letra] = nuevo
            return
        cont = [it for it in self.tazones.get(letra, [])]
        if h == "exprimir":
            cont = [it for it in cont if it[0] != ing]
            cont.append(("jugo", "entero"))
        elif ing:
            est = ESTADO_HAB.get(h, "entero")
            cont = [it for it in cont if it[0] != ing]
            cont.append((ing, est))
        self.tazones[letra] = cont[-6:]

    def _cerrar_paso(self):
        cur, r = self.cur, self.r
        spec = self.pasos[self.i]
        q = cur.calidad
        self.calid.append(q)
        n = self.sumar(q * self.pp)
        x = cd.xp_paso(r["estrellas"], q)
        h = spec["h"]
        self.xp[h] = self.xp.get(h, 0) + x
        for hab, niv in cd.dar_xp(self.perfil, {h: x}):
            self.subidas.append((hab, niv))
            self.avisos.append(["¡Subiste de nivel! %s nivel %d" % (cd.HABILIDADES[hab]["nombre"], niv), 2.6])
            self.sonidos.reproducir("premio")
        self._poner_en_tazon(spec, q)
        txt = "¡Perfecto!" if q >= 0.85 else ("¡Muy bien!" if q >= 0.6 else "¡Bien!")
        self.ult = (txt, n)
        self.sonidos.reproducir("ok" if q >= 0.6 else "click")
        explosion(self.particulas, ANCHO / 2, 330, (255, 235, 120), n=12, gravedad=400)
        self.cerrado = True

    def _cerrar_receta(self):
        """Termina la preparacion: bono, estrellas, plato, materiales."""
        r, p = self.r, self.perfil
        avg = sum(self.calid) / max(1, len(self.calid))
        self.sumar(cd.puntos_bono(r) * avg * avg)
        self.delicioso = avg >= 0.7
        est = self.estrellas()
        nuevas = [x for x in cd.RECETAS if cd.desbloqueada(p, x) and x["id"] not in self.antes]
        cant = 0
        if est >= 1:
            cant = 1 if r["basica"] else est
            if r["basica"] and est >= 3:
                cant = 2
            self.dar(cd.plato_id(r), cant)
            p.recetas_hechas[r["id"]] = p.recetas_hechas.get(r["id"], 0) + 1
            self._datos_cocina()["pendiente"] = {}
        else:
            self._devolver_pendiente()
        p.guardar()
        self.resumen = dict(xp=dict(self.xp), subidas=list(self.subidas), nuevas=nuevas, cantidad=cant,
                            estrellas=est, devueltos=(est < 1 and not r["basica"]), avg=avg)
        self.fase = "entrega"
        self.t_ent = 0.0
        self.t_fin = 4.8 + 1.2 * min(3, len(self.subidas)) + (0.8 if nuevas else 0.0)
        self.sonidos.reproducir("premio" if est >= 1 else "fin")
        for _ in range(4):
            explosion(self.particulas, random.uniform(450, 830), random.uniform(250, 400),
                      random.choice([(255, 220, 90), (255, 130, 140), (130, 220, 255)]), n=10, gravedad=300)
        self.mensaje_final = ("¡%s listo!" % r["nombre"]) if est >= 1 else "¡Sigue practicando!"

    # ------------------------------------------------------------------ ciclo
    def paso(self, dt, ctrl):
        self.particulas = [q for q in self.particulas if q.actualizar(dt)]
        for a in self.avisos:
            a[1] -= dt
        self.avisos = [a for a in self.avisos if a[1] > 0]
        if self.fase == "libro":
            self._paso_libro(dt, ctrl)
        elif self.fase == "entrega":
            self.t_ent += dt
            if self.t_ent >= self.t_fin:
                self.terminar(self.mensaje_final)
        else:
            self._paso_cocina(dt, ctrl)

    def _paso_cocina(self, dt, ctrl):
        if self.espera > 0:
            self.espera -= dt
            return
        cur = self.cur
        cur.actualizar(dt, ctrl)
        if not cur.terminado and cur.t > cur.t_max + 8.0:      # seguridad: nada se cuelga
            cur.terminar(cur.prog)
        if cur.terminado:
            if not self.cerrado:
                self._cerrar_paso()
            elif cur.t_cierre >= T_CIERRE:
                self.i += 1
                if self.i >= len(self.pasos):
                    self._cerrar_receta()
                else:
                    self._nuevo_paso()

    def _paso_libro(self, dt, ctrl):
        if self.giro:
            g = self.giro
            g["u"] += dt / T_GIRO
            if g["u"] >= 1.0:
                self.doble = g["destino"]
                self.giro = None
                self._colocar_cartas()
                self._reiniciar_botones(self.b_ant, self.b_sig)
                self.b_ant.espera = self.b_sig.espera = 0.5
            return
        if self.vista == "libro":
            self.b_ant.activo = self.doble > 0
            self.b_sig.activo = self.doble < n_dobles() - 1
            if self.b_ant.actualizar(dt, ctrl):
                self.girar(-1)
                return
            if self.b_sig.actualizar(dt, ctrl):
                self.girar(1)
                return
            if self.b_hab.actualizar(dt, ctrl):
                self.abrir_habilidades()
                return
            if self.b_salir.actualizar(dt, ctrl):
                self.terminar("¡Hasta pronto, chef!")
                return
            for k, c in enumerate(self.cartas):
                if c.actualizar(dt, ctrl):
                    r = self.receta_en_carta(k)
                    if r:
                        self.abrir_ficha(r["id"])
                    return
        elif self.vista == "ficha":
            if self.b_volver.actualizar(dt, ctrl):
                self.cerrar_ficha()
            elif self.b_cocinar.actualizar(dt, ctrl):
                self._empezar(self.sel)
        elif self.vista == "habilidades":
            if self.b_cerrar.actualizar(dt, ctrl):
                self.vista = "libro"
                self._reiniciar_botones(*self.cartas, self.b_ant, self.b_sig, self.b_hab, self.b_salir)

    # ------------------------------------------------------------------ dibujo: libro
    def _hoja(self, idx):
        s = self._cache_hojas.get(idx)
        if s is None:
            s = self._cache_hojas[idx] = self._crear_hoja(idx)
        return s

    def _crear_hoja(self, idx):
        s = pygame.Surface((HOJA_W, HOJA_H), pygame.SRCALPHA)
        izq = idx % 2 == 0
        pygame.draw.rect(s, ac.PAPEL, (0, 0, HOJA_W, HOJA_H), border_radius=14)
        for i in range(46):
            col = _mezcla(ac.PAPEL, (200, 175, 135), (1 - i / 46) ** 2)
            x = HOJA_W - 1 - i if izq else i
            pygame.draw.line(s, col, (x, 4), (x, HOJA_H - 5))
        pygame.draw.rect(s, (214, 196, 160), (0, 0, HOJA_W, HOJA_H), 2, border_radius=14)
        lista = self._recetas_hoja(idx)
        if lista:
            txt = "Recetas %d a %d" % (lista[0]["nivel"], lista[-1]["nivel"])
            escribir(s, _F(20), txt, HOJA_W // 2, 20, (150, 120, 80), contorno=None)
        for i, r in enumerate(lista):
            self._dib_tarjeta(s, pygame.Rect(14, 40 + i * (CARTA_H + CARTA_SEP), CARTA_W, CARTA_H), r)
        return s

    def _dib_tarjeta(self, s, rect, r):
        p = self.perfil
        bloq = bool(cd.habilidades_faltantes(p, r))
        faltan = cd.materiales_faltantes(p, r)
        lista = not bloq and not faltan
        fondo = (255, 251, 238) if not bloq else (234, 230, 222)
        pygame.draw.rect(s, (222, 205, 170), rect.move(0, 3), border_radius=16)
        pygame.draw.rect(s, fondo, rect, border_radius=16)
        pygame.draw.rect(s, (205, 180, 135) if not bloq else (190, 185, 178), rect, 2, border_radius=16)
        x, y = rect.x, rect.y
        cp.dibujar_plato(s, r, x + 66, y + 74, 100)
        if bloq:
            gris = pygame.Surface((116, 116), pygame.SRCALPHA)
            pygame.draw.circle(gris, (150, 150, 160, 150), (58, 58), 54)
            s.blit(gris, (x + 8, y + 16))
            ac.candado(s, x + 66, y + 78, 44)
        x0 = x + 140
        escribir(s, _ajustar(r["nombre"], 255, 27, 16), r["nombre"], x0, y + 22, (90, 55, 30), ancla="izq",
                 contorno=None)
        _estrellas_fila(s, x + CARTA_W - 20, y + 22, r["estrellas"])
        # nivel, pasos y habilidades
        niv = cd.niveles(p)
        linea = "Nivel %d  ·  %d pasos" % (r["nivel"], len(r["pasos"]))
        escribir(s, _F(19), linea, x0, y + 55, (130, 95, 60), ancla="izq", contorno=None)
        if r["hab"]:
            nec = max(r["hab"].values())
            ok = all(niv[h] >= n for h, n in r["hab"].items())
            xx = x0 + _F(19).size(linea)[0] + 14
            escribir(s, _F(19), "Habilidades nivel %d" % nec, xx, y + 55,
                     (40, 150, 60) if ok else (210, 60, 50), ancla="izq", contorno=None)
        # materiales
        yy = y + 90
        if r["basica"] or not r["mats"]:
            ac.casita(s, x0 + 14, yy - 4, 28)
            escribir(s, _F(19), "Ingredientes de la casa", x0 + 34, yy, (110, 130, 110), ancla="izq", contorno=None)
        else:
            xx = x0
            items = list(r["mats"].items())
            for m, n in items[:6]:
                tengo = p.cantidad(m)
                ok = tengo >= n
                catalogo.dibujar_item(s, m, xx + 14, yy, 28)
                escribir(s, _F(18), "%d/%d" % (tengo, n), xx + 31, yy, (40, 150, 60) if ok else (210, 60, 50),
                         ancla="izq", contorno=None)
                xx += 64
            if len(items) > 6:
                escribir(s, _F(18), "+%d" % (len(items) - 6), xx, yy, (130, 95, 60), ancla="izq", contorno=None)
        # estado
        yy = y + 123
        motivo = cd.motivo_bloqueo(p, r)
        if motivo:
            escribir(s, _ajustar(motivo, 385, 19, 14), motivo, x0, yy, (200, 55, 45), ancla="izq", contorno=None)
        else:
            hechas = p.recetas_hechas.get(r["id"], 0)
            txt = "¡Lista para cocinar!" + ("  Hecha %d" % hechas if hechas else "")
            escribir(s, _F(19), txt, x0, yy, (40, 150, 60), ancla="izq", contorno=None)
        if lista and r["id"] == self.recom:
            tag = pygame.Rect(0, 0, 118, 26)
            tag.midright = (x + CARTA_W - 12, y + CARTA_H - 22)
            pygame.draw.rect(s, (255, 205, 60), tag, border_radius=13)
            pygame.draw.rect(s, (170, 115, 20), tag, 2, border_radius=13)
            escribir(s, _F(17), "¡Para ti!", tag.centerx, tag.centery, (110, 60, 10), contorno=None)

    def _dibujar_hojas(self, p):
        e = self.doble
        g = self.giro
        if not g:
            p.blit(self._hoja(2 * e), HOJA_IZQ.topleft)
            p.blit(self._hoja(2 * e + 1), HOJA_DER.topleft)
            return
        u, d, dest = g["u"], g["dir"], g["destino"]
        if d > 0:
            p.blit(self._hoja(2 * e), HOJA_IZQ.topleft)
            p.blit(self._hoja(2 * dest + 1), HOJA_DER.topleft)
            if u < 0.5:
                self._hoja_girando(p, self._hoja(2 * e + 1), "R", 1 - 2 * u, u)
            else:
                self._hoja_girando(p, self._hoja(2 * dest), "L", 2 * u - 1, u)
        else:
            p.blit(self._hoja(2 * dest), HOJA_IZQ.topleft)
            p.blit(self._hoja(2 * e + 1), HOJA_DER.topleft)
            if u < 0.5:
                self._hoja_girando(p, self._hoja(2 * e), "L", 1 - 2 * u, u)
            else:
                self._hoja_girando(p, self._hoja(2 * dest + 1), "R", 2 * u - 1, u)

    def _hoja_girando(self, p, surf, lado, frac, u):
        w = max(3, int(HOJA_W * frac))
        img = pygame.transform.smoothscale(surf, (w, HOJA_H))
        sombra = pygame.Surface((w, HOJA_H), pygame.SRCALPHA)
        sombra.fill((60, 40, 20, int(110 * (1 - frac))))
        img.blit(sombra, (0, 0))
        pygame.draw.line(img, (255, 255, 255), (w - 1 if lado == "L" else 0, 0), (w - 1 if lado == "L" else 0, HOJA_H), 3)
        alza = int(14 * math.sin(math.pi * u))
        x = HOJA_DER.x if lado == "R" else HOJA_IZQ.right - w
        p.blit(img, (x, HOJA_IZQ.y - alza))

    def _dibujar_libro(self, p):
        tapa = pygame.Rect(36, 106, 1208, 540)
        pygame.draw.rect(p, ac.CUERO_OSC, tapa.move(0, 6), border_radius=26)
        pygame.draw.rect(p, ac.CUERO, tapa, border_radius=26)
        pygame.draw.rect(p, (160, 105, 65), tapa, 4, border_radius=26)
        for i in range(3):
            pygame.draw.rect(p, (236, 224, 196), (HOJA_IZQ.x - 4 - i * 2, HOJA_IZQ.y + 6 + i * 3, HOJA_W + 4, HOJA_H),
                             border_radius=14)
            pygame.draw.rect(p, (236, 224, 196), (HOJA_DER.x + i * 2, HOJA_DER.y + 6 + i * 3, HOJA_W + 4, HOJA_H),
                             border_radius=14)
        self._dibujar_hojas(p)
        if not self.giro and self.vista == "libro":
            for c in self.cartas:
                if c.activo and c.encima:
                    pygame.draw.rect(p, (255, 205, 50), c.rect.inflate(6, 6), 5, border_radius=18)
                    if c.dwell > 0:
                        barra(p, (c.rect.x + 20, c.rect.bottom - 14, c.rect.w - 40, 8), min(1.0, c.dwell / DWELL_SEG),
                              color=(255, 200, 40), color_fondo=(225, 210, 180), borde=(170, 115, 20))
        pygame.draw.rect(p, ac.CUERO_OSC, (HOJA_IZQ.right - 2, HOJA_IZQ.y - 2, HOJA_DER.x - HOJA_IZQ.right + 4,
                                           HOJA_H + 4), border_radius=4)
        for y in range(HOJA_IZQ.y + 14, HOJA_IZQ.bottom - 8, 34):
            pygame.draw.line(p, (225, 190, 120), (640, y), (640, y + 14), 3)
        cinta = [(1186, 106), (1214, 106), (1214, 170), (1200, 154), (1186, 170)]
        pygame.draw.polygon(p, (205, 50, 60), cinta)
        pygame.draw.polygon(p, (130, 25, 35), cinta, 3)
        escribir(p, self.f.grande, "Mi recetario", 640, 50, (255, 245, 215), contorno=(110, 60, 30), grosor=3)
        escribir(p, self.f.chica, "Elige una receta. La de ¡Para ti! va con tu nivel.", 640, 88, (120, 70, 35),
                 contorno=None)
        for b in (self.b_ant, self.b_sig, self.b_hab, self.b_salir):
            b.dibujar(p, self.f.normal)
        self._flecha(p, self.b_ant.rect, -1, self.b_ant.activo)
        self._flecha(p, self.b_sig.rect, 1, self.b_sig.activo)
        e = self.doble if not self.giro else self.giro["destino"]
        a, b = e * POR_DOBLE + 1, min(len(cd.RECETAS), (e + 1) * POR_DOBLE)
        escribir(p, self.f.normal, "Recetas %d a %d de %d" % (a, b, len(cd.RECETAS)), 640, 668, (255, 245, 215),
                 contorno=(110, 60, 30))
        n = n_dobles()
        for i in range(n):
            x = 640 + (i - (n - 1) / 2) * 26
            pygame.draw.circle(p, (255, 255, 255), (int(x), 700), 9)
            pygame.draw.circle(p, (255, 205, 60) if i == e else (190, 150, 110), (int(x), 700), 7)

    def _flecha(self, p, rect, d, activo):
        cx = rect.x + 28 if d < 0 else rect.right - 28
        cy = rect.centery
        pts = [(cx + 12 * d, cy), (cx - 10 * d, cy - 15), (cx - 10 * d, cy + 15)]
        pygame.draw.polygon(p, (255, 255, 255) if activo else (215, 218, 228), pts)
        pygame.draw.polygon(p, (110, 60, 20), pts, 3)

    # ------------------------------------------------------------------ dibujo: ficha
    def _dibujar_ficha(self, p):
        r = self.sel
        pf = self.perfil
        _telon(p)
        marco = pygame.Rect(24, 14, 1232, 692)
        pygame.draw.rect(p, ac.CUERO_OSC, marco.inflate(12, 12), border_radius=30)
        pygame.draw.rect(p, ac.PAPEL, marco, border_radius=24)
        # cabecera
        cp.dibujar_plato(p, r, 120, 100, 124, self.t)
        escribir(p, _ajustar(r["nombre"], 800, 46, 26), r["nombre"], 210, 58, (90, 55, 30), ancla="izq", contorno=None)
        escribir(p, self.f.normal, "Nivel %d" % r["nivel"], 210, 108, (40, 120, 190), ancla="izq", contorno=None)
        _estrellas_fila(p, 210 + 135 + 4 * 28 + 10, 108, r["estrellas"], r=12, sep=28)
        escribir(p, self.f.chica, "%d pasos  ·  hasta %d puntos  ·  %s" % (
            len(r["pasos"]), cd.puntos_maximos(r), r["desc"]), 210, 146, (130, 95, 60), ancla="izq", contorno=None)
        pygame.draw.line(p, (225, 205, 165), (50, 180), (1230, 180), 3)
        # ingredientes
        escribir(p, self.f.normal, "Ingredientes", 50, 204, (90, 55, 30), ancla="izq", contorno=None)
        if r["basica"] or not r["mats"]:
            ac.casita(p, 74, 262, 40)
            escribir(p, _F(18), "Ingredientes de la casa", 104, 252, (110, 130, 110), ancla="izq", contorno=None)
            escribir(p, _F(18), "No gasta tu inventario", 104, 274, (110, 130, 110), ancla="izq", contorno=None)
        else:
            for i, (m, n) in enumerate(r["mats"].items()):
                yy = 244 + i * 36
                tengo = pf.cantidad(m)
                ok = tengo >= n
                pygame.draw.rect(p, (255, 244, 220), (50, yy - 16, 370, 33), border_radius=12)
                pygame.draw.rect(p, (95, 190, 110) if ok else (230, 100, 90), (50, yy - 16, 370, 33), 2, border_radius=12)
                catalogo.dibujar_item(p, m, 70, yy, 28)
                escribir(p, _ajustar(catalogo.nombre_item(m), 140, 19, 12), catalogo.nombre_item(m), 92, yy,
                         (90, 55, 30), ancla="izq", contorno=None)
                tx, col = FUENTE_TXT.get(cd.fuente_de(m), FUENTE_TXT["casa"])
                chip = pygame.Rect(236, yy - 11, 78, 22)
                pygame.draw.rect(p, col, chip, border_radius=11)
                escribir(p, _F(14), tx, chip.centerx, chip.centery, (255, 255, 255), contorno=None)
                escribir(p, _F(19), "%d/%d" % (tengo, n), 410, yy, (40, 150, 60) if ok else (210, 60, 50),
                         ancla="der", contorno=None)
        # pasos por fase
        escribir(p, self.f.normal, "Pasos", 450, 204, (90, 55, 30), ancla="izq", contorno=None)
        grupos = {f: [s for s in r["pasos"] if fase_de(s) == f] for f in cd.FASES}
        cols = [f for f in cd.FASES if grupos[f]]
        ancho = 188
        for c, f in enumerate(cols):
            x = 450 + c * (ancho + 8)
            cab = pygame.Rect(x, 232, ancho, 28)
            pygame.draw.rect(p, COLOR_FASE[f], cab, border_radius=14)
            escribir(p, _F(18), "%s (%d)" % (cd.NOMBRE_FASE[f], len(grupos[f])), cab.centerx, cab.centery,
                     (255, 255, 255), contorno=None)
            n = len(grupos[f])
            gap = min(28, 270 // max(1, n))
            for k, s in enumerate(grupos[f]):
                yy = 276 + k * gap
                if gap >= 22:
                    p.blit(icono_hab(s["h"], 24), (x, yy - 12))
                    tx = etiqueta_paso(s)
                    escribir(p, _ajustar(tx, ancho - 32, 17, 11), tx, x + 30, yy, (90, 55, 30), ancla="izq",
                             contorno=None)
                else:
                    p.blit(icono_hab(s["h"], 18), (x, yy - 9))
                    tx = etiqueta_paso(s)
                    escribir(p, _ajustar(tx, ancho - 26, 13, 9), tx, x + 24, yy, (90, 55, 30), ancla="izq",
                             contorno=None)
        # habilidades
        pygame.draw.line(p, (225, 205, 165), (440, 556), (1230, 556), 3)
        habs = cd.habilidades_de(r)
        niv = cd.niveles(pf)
        escribir(p, self.f.chica, "Habilidades  (tienes / pide)", 450, 572, (130, 95, 60), ancla="izq", contorno=None)
        for k, h in enumerate(habs):
            x = 450 + (k % 15) * 52
            y = 598
            need = r["hab"].get(h)
            ok = need is None or niv[h] >= need
            p.blit(icono_hab(h, 34), (x + 6, y - 17))
            txt = "%d/%d" % (niv[h], need) if need else "%d" % niv[h]
            escribir(p, _F(15), txt, x + 23, y + 27, (40, 150, 60) if ok else (210, 60, 50), contorno=None)
        motivo = cd.motivo_bloqueo(pf, r)
        if motivo:
            escribir(p, _ajustar(motivo, 620, 28, 16), motivo, 640, 666, (200, 55, 45), contorno=None)
        else:
            escribir(p, self.f.normal, "¡Todo listo para cocinar!", 640, 666, (40, 150, 60), contorno=None)
        self.b_volver.dibujar(p, self.f.normal)
        self.b_cocinar.dibujar(p, self.f.normal)

    # ------------------------------------------------------------------ dibujo: habilidades
    def _dibujar_habilidades(self, p):
        pf = self.perfil
        _telon(p, 170)
        marco = pygame.Rect(24, 14, 1232, 692)
        pygame.draw.rect(p, ac.CUERO_OSC, marco.inflate(12, 12), border_radius=30)
        pygame.draw.rect(p, ac.PAPEL, marco, border_radius=24)
        escribir(p, self.f.grande, "Mis habilidades", 640, 52, (90, 55, 30), contorno=None)
        hechas = sum(1 for r in cd.RECETAS if cd.desbloqueada(pf, r))
        escribir(p, self.f.chica, "Recetas desbloqueadas: %d de %d" % (hechas, len(cd.RECETAS)), 640, 92,
                 (110, 80, 50), contorno=None)
        for i, h in enumerate(cd.ORDEN_HAB):
            col, fil = i // 11, i % 11
            x, y = 44 + col * 600, 114 + fil * 47
            xp = pf.habilidades.get(h, 0)
            n, dentro, mide, fr = cd.progreso_habilidad(xp)
            d = cd.HABILIDADES[h]
            pygame.draw.rect(p, (255, 244, 220), (x, y, 580, 43), border_radius=14)
            p.blit(icono_hab(h, 36), (x + 8, y + 3))
            escribir(p, _F(21), d["nombre"], x + 54, y + 14, (90, 55, 30), ancla="izq", contorno=None)
            escribir(p, _F(13), d["herr"], x + 54, y + 32, (140, 110, 80), ancla="izq", contorno=None)
            escribir(p, _F(20), "Nivel %d" % n, x + 232, y + 22, (40, 120, 190), ancla="izq", contorno=None)
            barra(p, (x + 322, y + 13, 160, 18), fr, color=(110, 200, 100) if n < cd.NIVEL_MAX_HAB else (255, 205, 60),
                  color_fondo=(225, 210, 180), borde=(130, 90, 55))
            txt = "%d / %d" % (dentro, mide) if mide else "¡Maestro!"
            escribir(p, _F(14), txt, x + 402, y + 22, (60, 40, 20), contorno=None)
            escribir(p, _F(14), "%d XP" % xp, x + 570, y + 22, (140, 110, 80), ancla="der", contorno=None)
        self.b_cerrar.dibujar(p, self.f.normal)

    # ------------------------------------------------------------------ dibujo: cocinando
    def _dib_cabecera(self, p):
        cur = self.cur
        n = len(self.pasos)
        spec = self.pasos[min(self.i, n - 1)]
        f = fase_de(spec)
        s = pygame.Surface((ANCHO, CABECERA_H), pygame.SRCALPHA)
        s.fill((112, 72, 44, 240))
        pygame.draw.rect(s, (70, 42, 24), (0, CABECERA_H - 5, ANCHO, 5))
        pygame.draw.rect(s, COLOR_FASE[f], (0, CABECERA_H - 5, ANCHO, 5))
        p.blit(s, (0, 0))
        tit = cur.titulo or etiqueta_paso(spec)
        escribir(p, _ajustar(tit, 720, 42, 22), tit, 640, 30, (255, 245, 215), contorno=(70, 40, 20), grosor=3)
        linea = "%s  ·  Paso %d de %d  ·  %s" % (self.r["nombre"], self.i + 1, n, cd.NOMBRE_FASE[f])
        escribir(p, _ajustar(linea, 700, 22, 14), linea, 640, 66, (255, 225, 170), contorno=None)
        sep = min(24, 640 // max(1, n))
        for k, sp in enumerate(self.pasos):
            x = 640 + (k - (n - 1) / 2) * sep
            col = COLOR_FASE[fase_de(sp)]
            if k < self.i or (k == self.i and self.cerrado):
                pygame.draw.circle(p, col, (int(x), 88), 6)
            elif k == self.i:
                pygame.draw.circle(p, (255, 255, 255), (int(x), 88), 9)
                pygame.draw.circle(p, col, (int(x), 88), 6)
            else:
                pygame.draw.circle(p, aclarar(col, 0.55), (int(x), 88), 5)
                pygame.draw.circle(p, col, (int(x), 88), 5, 1)

    def _pos_tazon(self, k):
        n = len(self.letras)
        if k < 3:
            return 66 + k * 98, 648
        n_der = n - 3
        return ANCHO - 66 - (n_der - 1 - (k - 3)) * 98, 648

    def _dib_tazones(self, p):
        if not self.letras:
            return
        for lado in (0, 1):
            ks = [k for k in range(len(self.letras)) if (k >= 3) == bool(lado)]
            if not ks:
                continue
            xs = [self._pos_tazon(k)[0] for k in ks]
            pan = pygame.Surface((max(xs) - min(xs) + 108, 96), pygame.SRCALPHA)
            pygame.draw.rect(pan, (90, 55, 30, 120), pan.get_rect(), border_radius=24)
            p.blit(pan, (min(xs) - 54, 600))
        for k, L in enumerate(self.letras):
            x, y = self._pos_tazon(k)
            ci.dibujar_tazon(p, x, y + 4, self.tazones.get(L, []), tam=76)
            pygame.draw.circle(p, (255, 255, 255), (x - 32, y + 22), 12)
            pygame.draw.circle(p, (150, 100, 60), (x - 32, y + 22), 12, 2)
            escribir(p, _F(16), L, x - 32, y + 22, (110, 60, 30), contorno=None)

    def _dib_resultado_paso(self, p):
        if not self.ult:
            return
        txt, n = self.ult
        u = min(1.0, self.cur.t_cierre / 0.25)
        w = int(300 * (0.7 + 0.3 * u))
        r = pygame.Rect(0, 0, w, 54)
        r.center = (640, 640)
        pygame.draw.rect(p, (255, 205, 60), r, border_radius=27)
        pygame.draw.rect(p, (170, 100, 20), r, 4, border_radius=27)
        escribir(p, self.f.normal, "%s  +%d" % (txt, n), r.centerx, r.centery, (255, 255, 255), contorno=(150, 80, 20))

    def _dib_avisos(self, p):
        for k, (txt, t) in enumerate(self.avisos[:2]):
            r = pygame.Rect(0, 0, 640, 44)
            r.center = (640, 214 + k * 52)
            pygame.draw.rect(p, (150, 100, 230), r, border_radius=22)
            pygame.draw.rect(p, (255, 255, 255), r, 4, border_radius=22)
            escribir(p, self.f.normal, txt, r.centerx, r.centery, (255, 255, 255), contorno=(70, 40, 120))

    def dibujar_juego(self, p):
        if self.fase == "libro":
            fondo_cocina(p, "mesada")
            self._dibujar_libro(p)
            if self.vista == "ficha":
                self._dibujar_ficha(p)
            elif self.vista == "habilidades":
                self._dibujar_habilidades(p)
        elif self.fase == "paso":
            self.cur.dibujar(p)
            self._dib_cabecera(p)
            self._dib_tazones(p)
            self._dib_resultado_paso(p)
            self._dib_avisos(p)
        else:
            fondo_cocina(p, "mesada")
            self._dib_entrega(p)
        for q in self.particulas:
            q.dibujar(p)

    def dibujar_hud(self, p):
        if self.fase == "libro":
            activas = list(self.mej.activas)
            for i, nombre in enumerate(activas):
                escribir(p, self.f.chica, MEJORAS[nombre][1], ANCHO - 20, 14 + i * 22, color=(255, 235, 140),
                         ancla="der")
            return
        super().dibujar_hud(p)

    # ------------------------------------------------------------------ dibujo: entrega
    def _dib_entrega(self, p):
        tf = self.t_ent
        res = self.resumen
        est = res["estrellas"]
        if est >= 1:
            titulo, col = ("¡Delicioso!" if self.delicioso else "¡Casi listo!"), (255, 235, 90)
        else:
            titulo, col = "¡Casi lo logras!", (255, 235, 150)
        escribir(p, self.f.enorme, titulo, 640, 70, color=col, contorno=(180, 60, 40), grosor=4)
        escribir(p, self.f.normal, self.r["nombre"], 640, 130, (90, 55, 30), contorno=None)
        sup = self._plato_surf(self.r, 230)
        esc = min(1.0, 0.5 + tf * 1.2)
        y = 360 + math.sin(tf * 5) * 5
        img = pygame.transform.rotozoom(sup, 0, esc)
        p.blit(img, img.get_rect(center=(640, int(y))))
        for k in range(3):
            lleno = k < est and tf > 0.3 + 0.4 * k
            estrella(p, 570 + k * 70, 520, 28, (255, 205, 50) if lleno else (225, 215, 195),
                     (170, 115, 20) if lleno else (190, 175, 150))
        # experiencia
        pygame.draw.rect(p, (255, 248, 230), (40, 160, 360, 380), border_radius=22)
        pygame.draw.rect(p, (150, 105, 60), (40, 160, 360, 380), 4, border_radius=22)
        escribir(p, self.f.normal, "Experiencia", 220, 200, (90, 55, 30), contorno=None)
        filas = sorted(((h, xp) for h, xp in res["xp"].items() if xp > 0), key=lambda a: -a[1])
        for i, (h, xp) in enumerate(filas[:8]):
            yy = 245 + i * 39
            p.blit(icono_hab(h, 32), (58, yy - 16))
            escribir(p, _F(21), cd.HABILIDADES[h]["nombre"], 100, yy, (90, 55, 30), ancla="izq", contorno=None)
            escribir(p, _F(22), "+%d" % xp, 380, yy, (40, 150, 60), ancla="der", contorno=None)
        if len(filas) > 8:
            escribir(p, _F(16), "y %d habilidades más" % (len(filas) - 8), 220, 524, (130, 100, 70), contorno=None)
        if not filas:
            escribir(p, self.f.chica, "Practica un poco más", 220, 320, (130, 100, 70), contorno=None)
        # plato ganado
        pygame.draw.rect(p, (255, 248, 230), (880, 160, 360, 380), border_radius=22)
        pygame.draw.rect(p, (150, 105, 60), (880, 160, 360, 380), 4, border_radius=22)
        if res["cantidad"]:
            escribir(p, self.f.normal, "Tu plato", 1060, 200, (90, 55, 30), contorno=None)
            catalogo.dibujar_item(p, cd.plato_id(self.r), 1000, 330, 100)
            escribir(p, self.f.grande, "x%d" % res["cantidad"], 1120, 330, (90, 55, 30), contorno=None)
            escribir(p, self.f.chica, "¡Nuevo plato en tu inventario!", 1060, 420, (110, 80, 50), contorno=None)
            escribir(p, self.f.chica, "Puntos: %d" % self.puntos, 1060, 470, (110, 80, 50), contorno=None)
        else:
            escribir(p, self.f.chica, "Esta vez no hubo plato.", 1060, 300, (110, 80, 50), contorno=None)
            if res["devueltos"]:
                escribir(p, self.f.chica, "Tus ingredientes vuelven", 1060, 340, (40, 150, 60), contorno=None)
                escribir(p, self.f.chica, "a tu inventario.", 1060, 366, (40, 150, 60), contorno=None)
        # subidas de nivel y recetas nuevas
        if tf > 1.0 and (res["subidas"] or res["nuevas"]):
            lineas = ["¡Subiste de nivel! %s nivel %d" % (cd.HABILIDADES[h]["nombre"], n) for h, n in res["subidas"][:3 - bool(res["nuevas"])]]
            if res["nuevas"]:
                lineas.append("¡Receta nueva: %s!" % res["nuevas"][0]["nombre"])
            alto = 20 + 38 * len(lineas)
            ban = pygame.Rect(0, 0, 760, alto)
            ban.center = (640, 708 - alto // 2)
            pulso = 1 + 0.03 * math.sin(tf * 8)
            ban = ban.inflate(int(40 * (pulso - 1)), int(20 * (pulso - 1)))
            pygame.draw.rect(p, (255, 200, 60), ban, border_radius=24)
            pygame.draw.rect(p, (200, 90, 30), ban, 5, border_radius=24)
            for i, l in enumerate(lineas):
                escribir(p, self.f.normal, l, 640, ban.y + 30 + i * 38, (255, 255, 255), contorno=(150, 60, 20))
