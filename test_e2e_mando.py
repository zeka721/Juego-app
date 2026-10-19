import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
"""Programa completo (main.py) con un mando simulado por un puerto serie virtual."""
import json, os, pty, sys, threading, time
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
import ajustes, entrada, main, aventura as av

# calibracion previa (guardada en archivos temporales)
import tempfile
tmp = tempfile.mkdtemp()
entrada.ARCHIVO_CAL = os.path.join(tmp, "cal.json")
entrada.ARCHIVO_CAL_T = os.path.join(tmp, "calt.json")
json.dump({"h": [2, 1], "v": [0, 1]}, open(entrada.ARCHIVO_CAL, "w"))
json.dump({"h": [1, 1], "v": [2, 1]}, open(entrada.ARCHIVO_CAL_T, "w"))
import nucleo
av.Perfil.__init__.__defaults__ = (os.path.join(tmp, "partida.json"),)

m, sl = pty.openpty()
entrada.PUERTO = os.ttyname(sl)
T0 = None
SIGNO_X = 1.0

def linea(t):
    gx = 100.0 if 0.5 <= t < 0.53 else 0.0
    gz = SIGNO_X * 100.0 if 0.5 <= t < 0.59 else 0.0      # giro horizontal: lleva el cursor sobre MINIJUEGOS (primer boton)
    az = 1.0
    if 5.0 <= t < 5.03:
        az = 2.6                      # golpe seco
    boton = 0 if 2.0 <= t < 2.1 else 1
    return f"{int(t*1000)},0.0,0.0,{az:.2f},{gx:.1f},0.0,{gz:.1f},{boton}\n"

def emisor():
    while T0 is None:
        time.sleep(0.01)
    while True:
        try: os.write(m, linea(time.time() - T0).encode())
        except OSError: return
        time.sleep(0.01)
threading.Thread(target=emisor, daemon=True).start()

registro = {"xmin": 1e9, "golpes": 0, "escenas": [], "clics": 0, "ymin": 1e9}
def gancho(n, app, ent, pantalla):
    global T0
    if T0 is None:
        T0 = time.time()
    t = time.time() - T0
    if ent.golpe: registro["golpes"] += 1
    if ent.clic: registro["clics"] += 1
    nombre = type(app.escena).__name__
    if not registro["escenas"] or registro["escenas"][-1][1] != nombre:
        registro["escenas"].append((round(t, 2), nombre))
    registro["ymin"] = min(registro["ymin"], ent.pos.y)
    registro["xmin"] = min(registro["xmin"], ent.pos.x)
    if 7.0 < t < 7.1:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="", scancode=0))
    if t > 9.0:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
main.main(cada_cuadro=gancho)
print(registro)
assert registro["golpes"] >= 1, "no se detecto el golpe"
assert registro["ymin"] < 342, "el cursor no subio con el giro"
nombres = [e[1] for e in registro["escenas"]]
assert "Libre" in nombres, nombres      # el primer boton (MINIJUEGOS) abre el menu de juegos
print("E2E MANDO OK")
