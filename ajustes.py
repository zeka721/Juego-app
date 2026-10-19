"""Ajustes de Ninja Mundo. Todo lo que quieras afinar esta aqui."""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))

# En el telefono (APK) no hay mando USB y los datos se guardan en la carpeta privada de la app.
ES_ANDROID = hasattr(sys, "getandroidapilevel")
CARPETA_DATOS = os.environ.get("ANDROID_PRIVATE", CARPETA) if ES_ANDROID else CARPETA

# ---------------- Mando ----------------
PUERTO = None if ES_ANDROID else "COM3"   # el de tu mando. None = detectar automaticamente (en Android: sin mando)
BAUDIOS = 115200
ANCHO, ALTO = 1280, 720

GRADOS_ANCHO = 60.0          # grados de giro horizontal para cruzar toda la pantalla
GRADOS_ALTO = 40.0           # grados de giro vertical para cruzar toda la pantalla
INVERTIR_X = True            # invierte izquierda/derecha del giro
INVERTIR_Y = False           # invierte arriba/abajo del giro
ZONA_MUERTA = 2.0            # grados/s: ignora giros menores (ruido del sensor)

UMBRAL_CORTE = 60.0          # grados/s: sobre esto empieza el corte (menor = mas sensible)
UMBRAL_SOSTEN = 30.0         # grados/s: el corte sigue activo mientras supere esto
SOSTEN_SEG = 0.18            # el corte no se suelta de golpe: aguanta este tiempo

# Deslizamiento lateral (acelerometro)
UMBRAL_LIN = 0.15            # m/s: velocidad de deslizamiento que cuenta como corte
PX_POR_METRO = 3600.0        # pixeles que recorre el cursor por cada metro deslizado
TAU_GRAVEDAD = 0.5           # s: que tan rapido se "aprende" la direccion de la gravedad
TAU_VELOCIDAD = 0.8          # s: la velocidad estimada se va olvidando (evita la deriva)
ZONA_MUERTA_ACEL = 0.5       # m/s^2: aceleraciones menores se ignoran (error del sensor)
MIN_VEL_CAL = 0.15           # m/s: velocidad minima para dar por valido un barrido de T
INVERTIR_TX = False          # invierte izquierda/derecha del deslizamiento
INVERTIR_TY = False          # invierte arriba/abajo del deslizamiento

# Golpe (sacudida o tajo seco del mando: sirve de "clic", tambor, lanzar la red...)
UMBRAL_GOLPE = 9.0           # m/s^2 de aceleracion sin gravedad (menor = mas sensible)
ESPERA_GOLPE = 0.22          # s minimos entre dos golpes

UMBRAL_PX = 900.0            # px/s: corte en modo raton
LARGO_RASTRO = 18
SEG_CAPTURA = 2.0            # duracion de cada barrido de calibracion
MIN_ANGULO_CAL = 25.0        # grados minimos para dar por valido un barrido

ARCHIVO_CAL = os.path.join(CARPETA_DATOS, "calibracion_ejes.json")
ARCHIVO_CAL_T = os.path.join(CARPETA_DATOS, "calibracion_deslizamiento.json")
ARCHIVO_PARTIDA = os.path.join(CARPETA_DATOS, "partida.json")

# ---------------- Juego ----------------
DWELL_SEG = 1.0              # segundos con el cursor sobre un boton para pulsarlo sin boton
RULETA_CADA = 80             # puntos acumulados para ganar un giro de la ruleta
USOS_MEJORA = 3              # cuantos minijuegos dura cada mejora de la ruleta
MARGEN_CORTE = 0.5           # la fruta se corta si el tajo pasa a hasta 50% de su tamano del borde
GRAVEDAD = 430.0             # px/s^2 de las frutas (menor = mas lento, pensado para 5 anos)
VIDAS = 3
GACHA_COSTO = 100            # monedas por cada tirada del gachapon
MONEDAS_POR_PUNTO = 1.0      # monedas que se ganan por cada punto al terminar un minijuego
POLVO_REVIVIR = 5            # polvo especial necesario para revivir un esqueleto completo
MODO_PRUEBA = True    # pon False para jugar normal: abre mapa, recetas y materiales