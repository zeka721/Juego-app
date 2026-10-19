"""Diagnostico del mando Ninja (firmware v2).

Uso (con el Monitor Serial de Arduino CERRADO y el juego cerrado):
    python diagnostico_mando.py            -> usa COM3
    python diagnostico_mando.py COM5

Durante 6 segundos te pide mover el mando y te dice exactamente que pasa:
 - que firmware tiene cargado la placa,
 - si el sensor responde,
 - cuanto giro y cuanta aceleracion se detecta al moverlo.
"""

import sys
import time

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "COM3"
SEGUNDOS = 6

try:
    import serial
except ImportError:
    print("Falta pyserial: python -m pip install pyserial")
    sys.exit(1)

print(f"Abriendo {PUERTO} ...")
try:
    s = serial.Serial(PUERTO, 115200, timeout=0.3)
except Exception as e:
    print(f"No se pudo abrir: {type(e).__name__}: {e}")
    print("-> Cierra el Monitor Serial de Arduino y el juego, y vuelve a probar.")
    sys.exit(1)

print(f"MUEVE EL MANDO con fuerza (tajos rapidos) durante {SEGUNDOS} segundos...\n")
validas = viejas = otras = comentarios = 0
g_min = [1e9] * 3
g_max = [-1e9] * 3
a_min = [1e9] * 3
a_max = [-1e9] * 3
vel_pico = 0.0
muestras = []
t_ms = []
fin = time.time() + SEGUNDOS
buf = b""
while time.time() < fin:
    buf += s.read(s.in_waiting or 1)
    while b"\n" in buf:
        linea, buf = buf.split(b"\n", 1)
        txt = linea.decode("ascii", errors="ignore").strip()
        if not txt:
            continue
        if txt.startswith("#"):
            comentarios += 1
            print("  mensaje de la placa:", txt)
            continue
        partes = txt.split(",")
        try:
            if len(partes) == 8:
                t = int(partes[0])
                v = [float(x) for x in partes[1:7]]
                validas += 1
                t_ms.append(t)
                for i in range(3):
                    a_min[i] = min(a_min[i], v[i])
                    a_max[i] = max(a_max[i], v[i])
                    g_min[i] = min(g_min[i], v[3 + i])
                    g_max[i] = max(g_max[i], v[3 + i])
                vel_pico = max(vel_pico, (v[3] ** 2 + v[4] ** 2 + v[5] ** 2) ** 0.5)
                if len(muestras) < 3:
                    muestras.append(txt)
            elif len(partes) == 3:
                [float(x) for x in partes]
                viejas += 1
                if viejas == 1:
                    print("  linea de formato VIEJO (3 campos):", txt)
            else:
                otras += 1
                if otras <= 2:
                    print("  linea desconocida:", repr(txt[:70]))
        except ValueError:
            otras += 1
            if otras <= 2:
                print("  linea desconocida:", repr(txt[:70]))
s.close()

print("\n=== RESULTADO ===")
print(f"lineas validas (formato v2): {validas} | formato viejo: {viejas} | otras: {otras}")

if validas == 0 and viejas > 0:
    print("\nCAUSA: la placa tiene cargado el sketch VIEJO (pitch,roll,boton).")
    print("SOLUCION: en Arduino IDE abre ninja_mando_v2.ino y pulsa Subir (flecha).")
elif validas == 0 and otras > 0:
    print("\nCAUSA: la placa envia otra cosa (por ejemplo el sketch del avion).")
    print("SOLUCION: sube ninja_mando_v2.ino con Arduino IDE.")
elif validas == 0:
    print("\nNo llego nada. Revisa: cable USB de datos, puerto correcto, nada mas usando el puerto,")
    print("y que ninja_mando_v2.ino se haya subido sin errores. Prueba pulsar RESET en la placa.")
else:
    hz = 0.0
    if len(t_ms) > 1 and t_ms[-1] > t_ms[0]:
        hz = (len(t_ms) - 1) * 1000.0 / (t_ms[-1] - t_ms[0])
    print(f"frecuencia: {hz:.0f} lecturas/s (esperado ~100)")
    print("ejemplo de lineas:", *muestras, sep="\n  ")
    rango_g = [g_max[i] - g_min[i] for i in range(3)]
    rango_a = [a_max[i] - a_min[i] for i in range(3)]
    print(f"giro  : gx {g_min[0]:.0f}..{g_max[0]:.0f}  gy {g_min[1]:.0f}..{g_max[1]:.0f}  "
          f"gz {g_min[2]:.0f}..{g_max[2]:.0f}  (grados/s)")
    print(f"acel  : ax {a_min[0]:.2f}..{a_max[0]:.2f}  ay {a_min[1]:.2f}..{a_max[1]:.2f}  "
          f"az {a_min[2]:.2f}..{a_max[2]:.2f}  (g)")
    print(f"giro maximo detectado: {vel_pico:.0f} grados/s")
    if max(rango_g) == 0 and max(rango_a) == 0:
        print("\nCAUSA: el sensor responde pero todos los valores son constantes (sensor sin despertar o")
        print("defectuoso). Revisa VCC a 3.3V (no 5V), SDA/SCL bien conectados y vuelve a subir el sketch.")
    elif max(rango_g) < 5 and max(rango_a) > 0.3:
        print("\nEl acelerometro se mueve pero el giroscopio no: sensor falso/defectuoso en el giroscopio.")
    elif vel_pico < 60:
        print("\nLlegan datos pero el giro maximo fue bajo: o no moviste el mando lo bastante rapido,")
        print("o tu movimiento es suave. En el juego usa la tecla [ para bajar el umbral de corte.")
    else:
        print(f"\nTODO BIEN: el mando detecta giros de hasta {vel_pico:.0f} grados/s.")
        print("Si el juego sigue mostrando 'quieto', baja el umbral con la tecla [ (empieza en 60).")
