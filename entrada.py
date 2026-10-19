"""Entrada: lee el mando por USB, lo calibra y lo convierte en cursor, corte, clic y golpe."""

import json
import math
import threading
import time
from collections import deque, namedtuple

import pygame

try:                       # pyserial solo existe en PC; en el telefono se juega con la pantalla
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

from ajustes import *          # noqa: F401,F403  (todos los ajustes)
from nucleo import ControlBase, escribir, V2



def parsear_linea(linea):
    """'t,ax,ay,az,gx,gy,gz,boton' -> (t_ms, [ax,ay,az], [gx,gy,gz], boton). None si no vale."""
    partes = linea.strip().split(",")
    if len(partes) != 8:
        return None
    try:
        t = int(partes[0])
        valores = [float(x) for x in partes[1:7]]
        boton = int(partes[7])
    except ValueError:
        return None
    return t, valores[0:3], valores[3:6], boton


def elegir_puerto():
    if ES_ANDROID or list_ports is None:
        return None
    puertos = list(list_ports.comports())
    print("Puertos serie encontrados:")
    for p in puertos:
        print(f"  {p.device}: {p.description}")
    if PUERTO:
        print(f"Usando el puerto definido: {PUERTO}")
        return PUERTO
    if not puertos:
        return None
    if len(puertos) == 1:
        print(f"Usando {puertos[0].device}")
        return puertos[0].device
    for p in puertos:
        if "USB" in (p.description or "").upper():
            print(f"Usando {p.device}")
            return p.device
    print("Varios puertos y ninguno claro: define PUERTO arriba en el script.")
    return None


Lectura = namedtuple("Lectura", "acum giro_max desp vlin_max vpico alin_max")


class Mando:
    """Lee el puerto en un hilo aparte. Acumula:
    - los grados girados en cada eje (giroscopio),
    - el desplazamiento y la velocidad de deslizamiento (acelerometro sin gravedad)."""

    def __init__(self, puerto, baudios, iniciar_hilo=True):
        self.puerto = puerto
        self.baudios = baudios
        self.lock = threading.Lock()
        self.acum = [0.0, 0.0, 0.0]   # grados girados desde la ultima llamada a tomar()
        self.vel_max = 0.0            # giro mas rapido (grados/s) desde esa llamada
        self.giro = [0.0, 0.0, 0.0]
        self.acel = [0.0, 0.0, 1.0]
        self.grav = None              # direccion de la gravedad vista desde el sensor (en g)
        self.vel = [0.0, 0.0, 0.0]    # velocidad de deslizamiento estimada (m/s, ejes del sensor)
        self.desp = [0.0, 0.0, 0.0]   # desplazamiento acumulado desde la ultima llamada (m)
        self.vlin_max = 0.0           # velocidad de deslizamiento maxima desde esa llamada
        self.vpico = [0.0, 0.0, 0.0]  # pico con signo de la velocidad por eje
        self.alin_max = 0.0           # aceleracion lineal maxima (m/s^2): sirve para detectar golpes
        self._quieto = 0.0
        self._estable = 0.0           # tiempo con la aceleracion sobrante casi constante
        self._lin_ref = [0.0, 0.0, 0.0]
        self._t_rapido = 9.0          # tiempo desde el ultimo giro rapido
        self.boton = 1
        self.conectado = False
        self.lecturas = 0
        self.invalidas = 0            # lineas recibidas que no tienen el formato esperado
        self.ultima = ""
        self.error = ""
        self._t_prev = None
        if iniciar_hilo:
            threading.Thread(target=self._leer, daemon=True).start()

    def _procesar(self, datos):
        t, acel, giro, boton = datos
        with self.lock:
            if self._t_prev is not None:
                dt = (t - self._t_prev) / 1000.0
                if 0 < dt < 0.1:      # descarta saltos (reinicios, pausas)
                    for i in range(3):
                        self.acum[i] += giro[i] * dt
                    self._deslizamiento(acel, giro, dt)
            self._t_prev = t
            self.vel_max = max(self.vel_max, math.sqrt(sum(g * g for g in giro)))
            self.giro, self.acel, self.boton = giro, acel, boton
            self.lecturas += 1

    def _deslizamiento(self, acel, giro, dt):
        """Quita la gravedad de la aceleracion y la integra para obtener la velocidad.

        La direccion de la gravedad se sigue con el giroscopio (para que inclinar el
        mando no parezca un movimiento) y se corrige despacio con el acelerometro.
        """
        if self.grav is None:
            self.grav = list(acel)
            return
        g = self.grav
        w = [math.radians(x) for x in giro]
        cx = w[1] * g[2] - w[2] * g[1]
        cy = w[2] * g[0] - w[0] * g[2]
        cz = w[0] * g[1] - w[1] * g[0]
        g = [g[0] - cx * dt, g[1] - cy * dt, g[2] - cz * dt]
        k = dt / (TAU_GRAVEDAD + dt)
        exceso = math.sqrt(sum(((acel[i] - g[i]) * 9.81) ** 2 for i in range(3)))
        mod_giro = math.sqrt(sum(x * x for x in giro))
        if exceso > 0.5:
            k *= 0.05                     # se esta acelerando: eso no es gravedad, no lo aprendas
        g = [g[i] + k * (acel[i] - g[i]) for i in range(3)]
        lin = [(acel[i] - g[i]) * 9.81 for i in range(3)]         # m/s^2

        # Recuperacion de errores: si el mando no gira y la aceleracion "sobrante" se queda
        # casi constante 0.35 s, no es un movimiento (un tajo siempre cambia de signo): es
        # error acumulado del giroscopio. Se realinea la gravedad y la velocidad vuelve a 0.
        if mod_giro < 8.0 and math.dist(lin, self._lin_ref) < 0.3:
            self._estable += dt
        else:
            self._estable = 0.0
            self._lin_ref = list(lin)
        if self._estable > 0.35:
            g = list(acel)
            lin = [0.0, 0.0, 0.0]
            self._estable = 0.0
            self._lin_ref = [0.0, 0.0, 0.0]
            self.vel = [0.0, 0.0, 0.0]
        self.grav = g

        # Con giros rapidos (y 0.4 s despues) la estimacion no es fiable: se ignora.
        self._t_rapido = 0.0 if mod_giro > 120.0 else self._t_rapido + dt
        mod_lin = math.sqrt(sum(a * a for a in lin))
        fuga = math.exp(-dt / TAU_VELOCIDAD)
        if self._t_rapido < 0.4:
            lin_u = [0.0, 0.0, 0.0]
            self.vel = [0.0, 0.0, 0.0]
        elif mod_lin < ZONA_MUERTA_ACEL:                          # error del sensor
            lin_u = [0.0, 0.0, 0.0]
        else:
            f = 1.0 - ZONA_MUERTA_ACEL / mod_lin
            lin_u = [a * f for a in lin]
        if mod_lin < ZONA_MUERTA_ACEL and mod_giro < 8.0:         # quieto: la velocidad es cero
            self._quieto += dt
        else:
            self._quieto = 0.0
        for i in range(3):
            self.vel[i] = 0.0 if self._quieto > 0.12 else self.vel[i] * fuga + lin_u[i] * dt
            self.desp[i] += self.vel[i] * dt
            if abs(self.vel[i]) > abs(self.vpico[i]):
                self.vpico[i] = self.vel[i]
        self.vlin_max = max(self.vlin_max, math.sqrt(sum(v * v for v in self.vel)))
        self.alin_max = max(self.alin_max, mod_lin)

    def tomar(self):
        """Devuelve lo acumulado desde la llamada anterior y reinicia los contadores."""
        with self.lock:
            lec = Lectura(list(self.acum), self.vel_max, list(self.desp),
                          self.vlin_max, list(self.vpico), self.alin_max)
            self.alin_max = 0.0
            self.acum = [0.0, 0.0, 0.0]
            self.vel_max = 0.0
            self.desp = [0.0, 0.0, 0.0]
            self.vlin_max = 0.0
            self.vpico = list(self.vel)
        return lec

    def _leer(self):
        while True:
            try:
                with serial.Serial(self.puerto, self.baudios, timeout=1) as s:
                    self.conectado = True
                    self.error = ""
                    self._t_prev = None
                    while True:
                        linea = s.readline().decode("ascii", errors="ignore")
                        if linea.strip():
                            self.ultima = linea.strip()[:70]
                        datos = parsear_linea(linea)
                        if datos:
                            self._procesar(datos)
                        elif linea.strip() and not linea.startswith("#"):
                            self.invalidas += 1
            except Exception as e:
                self.conectado = False
                self.error = f"{type(e).__name__}: {e}"[:90]
                print("Error del puerto serie:", self.error)
                time.sleep(1)


class Espada:
    """Convierte los giros del sensor en movimiento del cursor.

    Como el sensor puede ir montado en cualquier orientacion dentro del cuchillo,
    la calibracion (tecla H) descubre sola que eje del sensor corresponde a
    'izquierda-derecha' y a 'abajo-arriba', y con que signo.
    """

    def __init__(self):
        self.eje_h = (2, 1)      # (indice del eje 0=gx 1=gy 2=gz, signo) hacia la derecha
        self.eje_v = (0, 1)      # lo mismo hacia arriba
        self.calibrada = False
        self.estado = None       # None, h_esperar, h_captura, v_esperar, v_captura
        self.integ = [0.0, 0.0, 0.0]
        self.pico = [0.0, 0.0, 0.0]
        self.t_inicio = 0.0
        self.mensaje = ""
        self._h_tmp = None
        self.cargar()

    def cargar(self):
        try:
            with open(ARCHIVO_CAL) as f:
                d = json.load(f)
            self.eje_h, self.eje_v = tuple(d["h"]), tuple(d["v"])
            self.calibrada = True
        except Exception:
            self.calibrada = False

    def guardar(self):
        try:
            with open(ARCHIVO_CAL, "w") as f:
                json.dump({"h": list(self.eje_h), "v": list(self.eje_v)}, f)
        except OSError as e:
            print("No se pudo guardar la calibracion:", e)

    def capturando(self):
        return self.estado in ("h_captura", "v_captura")

    def iniciar_calibracion(self):
        self.estado = "h_esperar"
        self.mensaje = ("1/2  Pulsa ESPACIO y haz UN barrido rapido de IZQUIERDA a DERECHA, "
                        "luego deja la espada quieta")

    def pulsar(self, ahora):
        """ESPACIO o boton. Devuelve True si la calibracion usa la pulsacion."""
        if self.estado in ("h_esperar", "v_esperar"):
            self.estado = self.estado.replace("esperar", "captura")
            self.integ = [0.0, 0.0, 0.0]
            self.pico = [0.0, 0.0, 0.0]
            self.t_inicio = ahora
            return True
        return False

    def restante(self, ahora):
        return max(0.0, SEG_CAPTURA - (ahora - self.t_inicio))

    def actualizar_calibracion(self, acum, ahora):
        for i in range(3):
            self.integ[i] += acum[i]
            if abs(self.integ[i]) > abs(self.pico[i]):
                self.pico[i] = self.integ[i]     # angulo maximo alcanzado (ignora el regreso)
        if ahora - self.t_inicio >= SEG_CAPTURA:
            self._terminar()

    def _terminar(self):
        vertical = self.estado == "v_captura"
        excluir = self._h_tmp[0] if vertical else None
        candidatos = [i for i in range(3) if i != excluir]
        i = max(candidatos, key=lambda k: abs(self.pico[k]))
        if abs(self.pico[i]) < MIN_ANGULO_CAL:
            self.estado = None
            self.mensaje = (f"Barrido muy pequeno ({abs(self.pico[i]):.0f} grados). "
                            "Pulsa H y repite con un movimiento mas amplio y rapido")
            return
        signo = 1 if self.pico[i] > 0 else -1
        if not vertical:
            self._h_tmp = (i, signo)
            self.estado = "v_esperar"
            self.mensaje = ("2/2  Pulsa ESPACIO y haz UN barrido rapido de ABAJO hacia ARRIBA, "
                            "luego deja la espada quieta")
        else:
            self.eje_h, self.eje_v = self._h_tmp, (i, signo)
            self.calibrada = True
            self.estado = None
            self.guardar()
            self.mensaje = "Calibracion lista y guardada"

    def mover(self, acum, dt):
        """Grados girados en este cuadro -> desplazamiento (dx, dy) del cursor en pixeles."""
        dh = self.eje_h[1] * acum[self.eje_h[0]]    # grados hacia la derecha
        dv = self.eje_v[1] * acum[self.eje_v[0]]    # grados hacia arriba
        if dt > 0:
            if abs(dh) / dt < ZONA_MUERTA:
                dh = 0.0
            if abs(dv) / dt < ZONA_MUERTA:
                dv = 0.0
        dx = dh * ANCHO / GRADOS_ANCHO
        dy = -dv * ALTO / GRADOS_ALTO
        if INVERTIR_X:
            dx = -dx
        if INVERTIR_Y:
            dy = -dy
        return dx, dy


class Traslacion:
    """Calibracion y uso del deslizamiento lateral (tecla T).

    Igual que con el giro: dos barridos guiados (izquierda->derecha y abajo->arriba)
    deslizando el cuchillo SIN inclinarlo. Descubre que eje del sensor corresponde a
    cada direccion y con que signo.
    """

    def __init__(self):
        self.eje_h = (0, 1)
        self.eje_v = (1, 1)
        self.calibrada = False
        self.estado = None       # None, h_esperar, h_captura, v_esperar, v_captura
        self.pico = [0.0, 0.0, 0.0]
        self.t_inicio = 0.0
        self.mensaje = ""
        self._h_tmp = None
        try:
            with open(ARCHIVO_CAL_T) as f:
                d = json.load(f)
            self.eje_h, self.eje_v = tuple(d["h"]), tuple(d["v"])
            self.calibrada = True
        except Exception:
            self.calibrada = False

    def guardar(self):
        try:
            with open(ARCHIVO_CAL_T, "w") as f:
                json.dump({"h": list(self.eje_h), "v": list(self.eje_v)}, f)
        except OSError as e:
            print("No se pudo guardar la calibracion del deslizamiento:", e)

    def capturando(self):
        return self.estado in ("h_captura", "v_captura")

    def iniciar(self):
        self.estado = "h_esperar"
        self.mensaje = ("T 1/2  Pulsa ESPACIO y DESLIZA el cuchillo de IZQUIERDA a DERECHA "
                        "sin inclinarlo, luego dejalo quieto")

    def pulsar(self, ahora):
        if self.estado in ("h_esperar", "v_esperar"):
            self.estado = self.estado.replace("esperar", "captura")
            self.pico = [0.0, 0.0, 0.0]
            self.t_inicio = ahora
            return True
        return False

    def restante(self, ahora):
        return max(0.0, SEG_CAPTURA - (ahora - self.t_inicio))

    def actualizar(self, vpico, ahora):
        for i in range(3):
            if abs(vpico[i]) > abs(self.pico[i]):
                self.pico[i] = vpico[i]
        if ahora - self.t_inicio >= SEG_CAPTURA:
            self._terminar()

    def _terminar(self):
        vertical = self.estado == "v_captura"
        excluir = self._h_tmp[0] if vertical else None
        candidatos = [i for i in range(3) if i != excluir]
        i = max(candidatos, key=lambda k: abs(self.pico[k]))
        if abs(self.pico[i]) < MIN_VEL_CAL:
            self.estado = None
            self.mensaje = (f"Deslizamiento muy suave ({abs(self.pico[i]):.2f} m/s). "
                            "Pulsa T y repite con un movimiento mas rapido")
            return
        signo = 1 if self.pico[i] > 0 else -1
        if not vertical:
            self._h_tmp = (i, signo)
            self.estado = "v_esperar"
            self.mensaje = ("T 2/2  Pulsa ESPACIO y DESLIZA el cuchillo de ABAJO hacia ARRIBA "
                            "sin inclinarlo, luego dejalo quieto")
        else:
            self.eje_h, self.eje_v = self._h_tmp, (i, signo)
            self.calibrada = True
            self.estado = None
            self.guardar()
            self.mensaje = "Deslizamiento calibrado y guardado"

    def mover(self, desp):
        """Desplazamiento (metros por eje del sensor) -> (dx, dy) del cursor en pixeles."""
        if not self.calibrada:
            return 0.0, 0.0
        dh = self.eje_h[1] * desp[self.eje_h[0]]
        dv = self.eje_v[1] * desp[self.eje_v[0]]
        dx = dh * PX_POR_METRO
        dy = -dv * PX_POR_METRO
        if INVERTIR_TX:
            dx = -dx
        if INVERTIR_TY:
            dy = -dy
        return dx, dy




class Entrada(ControlBase):
    """Une el mando (o el raton) con lo que necesitan las escenas. Ver ControlBase.

    Teclas globales:  H calibrar giro | T calibrar deslizamiento | M mando/raton
                      [ ] sensibilidad del corte | G golpe manual | ESPACIO/ENTER clic
    """

    def __init__(self):
        super().__init__()
        puerto = elegir_puerto()
        self.mando = Mando(puerto, BAUDIOS) if puerto else None
        self.usar_mando = self.mando is not None
        self.espada = Espada()
        self.traslacion = Traslacion()
        self.umbral = UMBRAL_CORTE
        self.corte_activo = False
        self.t_rapido = 0.0
        self.t_golpe = 0.0
        self.boton_prev = 1
        self.t_boton = 0.0
        self.vel_giro = 0.0
        self.vlin = 0.0
        self.pico_golpe = 0.0
        self.t_congelar = 0.0         # tras un golpe se ignora el deslizamiento un instante
        self.rastro = deque(maxlen=LARGO_RASTRO)
        self.msgs = {self.espada: ("", 0.0), self.traslacion: ("", 0.0)}

    @property
    def calibrando(self):
        return self.espada.estado is not None or self.traslacion.estado is not None

    def centrar(self):
        super().centrar()
        self.rastro.clear()

    def _accion(self, ahora):
        """Boton fisico, ESPACIO o clic: avanza la calibracion o cuenta como clic."""
        if self.mando:
            self.mando.tomar()
        if self.espada.pulsar(ahora) or self.traslacion.pulsar(ahora):
            return
        self.clic = True

    def actualizar(self, dt, eventos, ahora=None):
        ahora = time.time() if ahora is None else ahora
        self.clic = False
        self.golpe = False
        mando = self.mando

        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._accion(ahora)
                elif ev.key == pygame.K_g:
                    self.golpe = True
                elif ev.key == pygame.K_LEFTBRACKET:
                    self.umbral = max(15.0, self.umbral - 10.0)
                elif ev.key == pygame.K_RIGHTBRACKET:
                    self.umbral = min(400.0, self.umbral + 10.0)
                elif ev.key == pygame.K_h and mando:
                    self.espada.iniciar_calibracion()
                elif ev.key == pygame.K_t and mando:
                    self.traslacion.iniciar()
                elif ev.key == pygame.K_m and mando:
                    self.usar_mando = not self.usar_mando
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    if not (self.usar_mando and mando is not None and mando.conectado):
                        self.pos = V2(ev.pos)          # toque: el cursor aparece justo en el dedo
                    self._accion(ahora)
                elif ev.button == 3:
                    self.golpe = True

        if mando:
            if mando.boton == 0 and self.boton_prev == 1 and ahora - self.t_boton > 0.3:
                self.t_boton = ahora
                self._accion(ahora)
            self.boton_prev = mando.boton

        inicio = V2(self.pos)
        usando = self.usar_mando and mando is not None and mando.conectado
        if usando:
            lec = mando.tomar()
            self.vel_giro, self.vlin = lec.giro_max, lec.vlin_max
            self.pico_golpe = max(lec.alin_max, self.pico_golpe * 0.95)
            if self.espada.capturando():
                self.espada.actualizar_calibracion(lec.acum, ahora)
            elif self.traslacion.capturando():
                self.traslacion.actualizar(lec.vpico, ahora)
            elif not self.calibrando:
                dx, dy = self.espada.mover(lec.acum, dt)
                tx, ty = self.traslacion.mover(lec.desp)
                self.t_congelar = max(0.0, self.t_congelar - dt)
                if self.t_congelar > 0:
                    tx = ty = 0.0
                self.pos.x = max(0, min(ANCHO, self.pos.x + dx + tx))
                self.pos.y = max(0, min(ALTO, self.pos.y + dy + ty))
                if lec.alin_max > UMBRAL_GOLPE and ahora - self.t_golpe > ESPERA_GOLPE:
                    self.t_golpe = ahora
                    self.golpe = True
                    self.t_congelar = 0.3
        else:
            objetivo = V2(pygame.mouse.get_pos())
            self.pos += (objetivo - self.pos) * 0.35
            self.vel_giro = self.vlin = 0.0

        self.p1, self.p2 = inicio, V2(self.pos)
        self.vel = inicio.distance_to(self.pos) / dt if dt > 0 else 0.0
        self.rastro.append(V2(self.pos))

        if usando:
            intensidad = max(self.vel_giro / self.umbral,
                             self.vlin / (UMBRAL_LIN * self.umbral / UMBRAL_CORTE))
            if intensidad > 1.0:
                self.corte_activo, self.t_rapido = True, ahora
            elif self.corte_activo and (intensidad < UMBRAL_SOSTEN / UMBRAL_CORTE
                                        and ahora - self.t_rapido > SOSTEN_SEG):
                self.corte_activo = False
            self.cortando = self.corte_activo and not self.calibrando
        else:
            self.cortando = self.vel > UMBRAL_PX

    # --- dibujo de apoyo ---
    def dibujar_cursor(self, pantalla):
        color = (255, 170, 60) if self.cortando else (255, 255, 255)
        for i in range(1, len(self.rastro)):
            grosor = max(1, int(i * 8 / LARGO_RASTRO))
            pygame.draw.line(pantalla, color, self.rastro[i - 1], self.rastro[i], grosor)
        pygame.draw.circle(pantalla, (30, 30, 50), (int(self.pos.x), int(self.pos.y)), 14)
        pygame.draw.circle(pantalla, color, (int(self.pos.x), int(self.pos.y)), 10)

    def lineas_diagnostico(self):
        m = self.mando
        if m is None:
            estado = "Sin puerto serie: usando el raton"
        elif not m.conectado:
            estado = f"No se pudo abrir {m.puerto}: {m.error or 'reintentando...'}"
        elif m.lecturas == 0 and m.invalidas > 0:
            estado = ("PROBLEMA: el mando envia otro formato. Sube ninja_mando_v2.ino. "
                      f"Recibido: {m.ultima!r}")
        elif m.lecturas == 0:
            estado = f"Puerto {m.puerto} abierto pero NO llegan datos"
        else:
            g = m.giro
            estado = (f"Mando OK  |  gx {g[0]:5.0f} gy {g[1]:5.0f} gz {g[2]:5.0f}  |  "
                      f"golpe: {self.pico_golpe:4.1f} (sobre {UMBRAL_GOLPE:.0f})")
        lineas = [estado,
                  f"Control: {'mando' if self.usar_mando else 'raton'}  |  "
                  f"giro {int(self.vel_giro)} (sobre {int(self.umbral)})  desliz {self.vlin:.2f} m/s  |  "
                  f"{'CORTANDO' if self.cortando else 'quieto'}"]
        if m and not self.espada.calibrada:
            lineas.append("Ejes sin calibrar: pulsa H")
        if m and not self.traslacion.calibrada:
            lineas.append("Para seguir deslizamientos laterales: pulsa T")
        lineas.append("H giro | T deslizamiento | M mando/raton | [ ] sensibilidad | "
                      "G golpe | F1 diagnostico | ESC menu")
        return lineas

    def dibujar_aviso_cal(self, pantalla, fuente, ahora=None):
        ahora = time.time() if ahora is None else ahora
        for obj in (self.espada, self.traslacion):
            if obj.mensaje != self.msgs[obj][0]:
                self.msgs[obj] = (obj.mensaje, ahora)
        if self.traslacion.estado is not None:
            cal = self.traslacion
        elif self.espada.estado is not None:
            cal = self.espada
        else:
            cal = max((self.espada, self.traslacion), key=lambda o: self.msgs[o][1])
        if cal.capturando():
            aviso = f"CAPTURANDO... haz el barrido ahora ({cal.restante(ahora):.1f} s)"
            color = (255, 170, 60)
        elif cal.estado is not None or ahora - self.msgs[cal][1] < 4:
            aviso = cal.mensaje
            color = (120, 220, 160)
        else:
            return
        if aviso:
            escribir(pantalla, fuente, aviso, ANCHO / 2, ALTO - 60, color)
