"""Horda Elemental: reglas y numeros (sin dibujo ni pygame).

El heroe elige un elemento (6 tipos del Tamagotchi). Dispara solo al enemigo mas cercano.
Tres habilidades por elemento:
  - Basico (siempre activo): 4 mejoras, cada una una sola vez.
  - Intermedio: 1 punto para desbloquearlo (requiere 2 mejoras del basico) + 3 mejoras.
  - Ultimate: 1 punto para desbloquearlo (requiere 3 mejoras del basico y el intermedio) + 1 mejora.
Total: 4 + 4 + 2 = 10 puntos = 10 subidas de nivel. Al llegar a 2000 derrotas aparece el jefe.
"""

import random

TIPOS = ["agua", "viento", "fuego", "hielo", "tierra", "electrico"]
NOMBRE_TIPO = {"agua": "Agua", "viento": "Viento", "fuego": "Fuego", "hielo": "Hielo",
               "tierra": "Tierra", "electrico": "Eléctrico"}
COLOR_TIPO = {"agua": (70, 160, 255), "viento": (190, 245, 225), "fuego": (255, 120, 50),
              "hielo": (250, 253, 255), "tierra": (172, 124, 74), "electrico": (255, 210, 50)}
# efecto del intermedio: (nombre, verbo para la descripcion)
INTERMEDIO = {"agua": ("Mojar", "ralentiza"), "viento": ("Empujar", "aleja al enemigo"),
              "tierra": ("Aturdir", "detiene al enemigo"), "fuego": ("Quemar", "quema al enemigo"),
              "hielo": ("Congelar", "congela al enemigo"), "electrico": ("Paralizar", "paraliza al enemigo")}
ULTIMATE = {"agua": "Ola", "viento": "Tornado", "tierra": "Derrumbe", "fuego": "Explosión",
            "hielo": "Iceberg", "electrico": "Truenos"}

# mejoras: id, nombre, descripcion
BASICO = [("cadencia", "Cadencia", "Dispara más seguido"),
          ("dano", "Daño", "+1 de daño"),
          ("pen", "Penetración", "Atraviesa hasta 2 enemigos"),
          ("tam", "Tamaño", "Proyectil más grande")]
MEJORAS_INTERMEDIO = [("dano_i", "Daño fuerte", "+2 de daño"),
                      ("carga", "Carga rápida", "Carga un 30% más rápido"),
                      ("efecto", "Efecto largo", "El efecto dura 0,5 s más")]
MEJORAS_ULTIMATE = [("dano_u", "Impacto fuerte", "+2 de daño en el área"),
                    ("frec", "Frecuencia", "Aparece más seguido"),
                    ("radio", "Área grande", "Radio +35%")]

REQ_INTERMEDIO = 2          # mejoras del basico para desbloquear el intermedio
REQ_ULTIMATE = 3            # mejoras del basico para desbloquear el ultimate

# derrotas acumuladas en las que sube cada nivel (10 niveles)
UMBRALES = [20, 90, 200, 350, 540, 760, 1000, 1280, 1600, 1900]
DERROTAS_JEFE = 2000
PUNTOS_DERROTA = 10
PUNTOS_JEFE = 500

VIDA = 5
VEL_HEROE = 230.0
RADIO_HEROE = 14
INVULN = 1.0
ZONA_MUERTA = 70            # distancia del cursor al centro para empezar a andar

ALCANCE = 480               # distancia maxima de la punteria automatica
VEL_PROY = 640.0
DUR_PROY = 1.1
DUR_INTER = 1.4
VEL_INTER = 560.0

EFECTO_BASE = 2.0           # segundos de mojar / empujar / aturdir / quemar / congelar / paralizar
ULT_INTERVALO = (4.0, 6.0)  # segundos entre ultimates (al azar)
ULT_INTERVALO_FREC = (3.0, 4.5)
ULT_RADIO = (150, 110, 130, 150, 120, 140)   # radio base por tipo (agua, viento, fuego, hielo, tierra, electrico)


def nivel_de(derrotas):
    """Nivel del heroe segun derrotas (0..10)."""
    return sum(1 for u in UMBRALES if derrotas >= u)


def intervalo_ola(derrotas):
    """Segundos entre hordas: al principio cada 7 s, al final cada 4 s."""
    return max(4.0, 7.0 - 0.0015 * derrotas)


def tamano_ola(derrotas):
    """Criaturas por horda: 8 al principio, hasta 40."""
    return min(40, 8 + derrotas // 30)


def vida_enemigo(derrotas, rng=random):
    """Puntos de vida. La mayoria cae de un golpe; con el progreso aparecen criaturas mas duras."""
    niveles = [1]
    if derrotas >= 40:
        niveles.append(2)
    if derrotas >= 150:
        niveles.append(3)
    if derrotas >= 400:
        niveles.append(5)
    if derrotas >= 900:
        niveles.append(8)
    if len(niveles) == 1 or rng.random() < 0.6:
        return 1
    return rng.choice(niveles[1:])


def vel_enemigo(derrotas):
    return 60 + min(60, derrotas * 0.3)


class Habilidades:
    """Estado de las habilidades de una partida. Cada subida de nivel da UN punto."""

    def __init__(self, tipo):
        assert tipo in TIPOS, tipo
        self.tipo = tipo
        self.basico = set()             # ids de mejoras del basico tomadas
        self.inter_desbloqueado = False
        self.inter = set()
        self.ult_desbloqueado = False
        self.ult = None                 # id de la mejora del ultimate (una sola)
        self.puntos_gastados = 0

    # --- consultas
    def n_basico(self):
        return len(self.basico)

    def puntos_disponibles(self, derrotas):
        return max(0, nivel_de(derrotas) - self.puntos_gastados)

    def completo(self):
        return self.puntos_gastados >= len(UMBRALES)

    def _requisito_inter(self):
        if self.n_basico() < REQ_INTERMEDIO:
            return f"Necesita {REQ_INTERMEDIO} mejoras del básico"
        return None

    def _requisito_ult(self):
        if self.n_basico() < REQ_ULTIMATE:
            return f"Necesita {REQ_ULTIMATE} mejoras del básico"
        if not self.inter_desbloqueado:
            return "Necesita desbloquear el intermedio"
        return None

    def opciones(self, rng=random):
        """Tres tarjetas, una por rama (basico, intermedio, ultimate). Cada una dice si se puede elegir."""
        tarjetas = []
        # basico
        pend = [m for m in BASICO if m[0] not in self.basico]
        if pend:
            m = rng.choice(pend)
            tarjetas.append(dict(rama="basico", id=m[0], nombre=m[1], desc=m[2], ok=True, motivo=""))
        else:
            tarjetas.append(dict(rama="basico", id=None, nombre="Básico al máximo", desc="", ok=False, motivo=""))
        # intermedio
        if not self.inter_desbloqueado:
            req = self._requisito_inter()
            nombre_i = INTERMEDIO[self.tipo][0]
            tarjetas.append(dict(rama="intermedio", id="desbloquear", nombre=f"Desbloquear {nombre_i}",
                                 desc=f"Habilidad: {INTERMEDIO[self.tipo][1]}", ok=req is None, motivo=req or ""))
        else:
            pend = [m for m in MEJORAS_INTERMEDIO if m[0] not in self.inter]
            if pend:
                m = rng.choice(pend)
                tarjetas.append(dict(rama="intermedio", id=m[0], nombre=m[1], desc=m[2], ok=True, motivo=""))
            else:
                tarjetas.append(dict(rama="intermedio", id=None, nombre="Intermedio al máximo", desc="", ok=False, motivo=""))
        # ultimate
        if not self.ult_desbloqueado:
            req = self._requisito_ult()
            tarjetas.append(dict(rama="ultimate", id="desbloquear", nombre=f"Desbloquear {ULTIMATE[self.tipo]}",
                                 desc="Ataque en área que cae cada pocos segundos", ok=req is None, motivo=req or ""))
        elif self.ult is None:
            m = rng.choice(MEJORAS_ULTIMATE)
            tarjetas.append(dict(rama="ultimate", id=m[0], nombre=m[1], desc=m[2], ok=True, motivo=""))
        else:
            tarjetas.append(dict(rama="ultimate", id=None, nombre="Ultimate mejorado", desc="", ok=False, motivo=""))
        return tarjetas

    def aplicar(self, tarjeta):
        """Gasta un punto en la tarjeta elegida. Devuelve False si no se podia."""
        if not tarjeta["ok"] or tarjeta["id"] is None:
            return False
        rama, mid = tarjeta["rama"], tarjeta["id"]
        if rama == "basico":
            self.basico.add(mid)
        elif rama == "intermedio":
            if mid == "desbloquear":
                self.inter_desbloqueado = True
            else:
                self.inter.add(mid)
        else:
            if mid == "desbloquear":
                self.ult_desbloqueado = True
            else:
                self.ult = mid
        self.puntos_gastados += 1
        return True

    # --- estadisticas derivadas
    def stats(self):
        b = self.basico
        i = self.inter
        u = self.ult
        return dict(
            cadencia=0.5 * (0.7 if "cadencia" in b else 1.0),
            dano=1 + (1 if "dano" in b else 0),
            pen=2 if "pen" in b else 1,
            radio=9 * (1.45 if "tam" in b else 1.0),
            inter_on=self.inter_desbloqueado,
            carga=(0.7 if "carga" in i else 1.0),
            dano_i=2 + (2 if "dano_i" in i else 0),
            radio_i=14 * (1.45 if "tam" in b else 1.0),
            efecto=EFECTO_BASE + (0.5 if "efecto" in i else 0.0),
            ult_on=self.ult_desbloqueado,
            ult_intervalo=ULT_INTERVALO_FREC if u == "frec" else ULT_INTERVALO,
            dano_u=2 + (2 if u == "dano_u" else 0),
            radio_u=1.35 if u == "radio" else 1.0,
        )


def jefe_aparece(derrotas, ya_aparecio):
    return (not ya_aparecio) and derrotas >= DERROTAS_JEFE


VIDA_TIRADOR = 3          # los monstruos de 3 o mas disparos pueden ser tiradores


def tiradores_max(derrotas):
    """Cuantos tiradores pueden estar disparando a la vez (sube por tramos, cada vez mas rapido)."""
    for limite, cuantos in ((100, 0), (250, 1), (500, 2), (1000, 4), (2000, 6)):
        if derrotas < limite:
            return cuantos
    return 8


def puntos_partida(derrotas, jefe_vencido):
    return derrotas * PUNTOS_DERROTA + (PUNTOS_JEFE if jefe_vencido else 0)
