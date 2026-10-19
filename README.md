# Ninja Mundo

Juegos de movimiento para ninos de 5 anos, controlados con el mando ESP32-C3 + MPU6050 (forma de espada/cuchillo).
Todo el arte y los sonidos se generan por codigo: no hay imagenes ni audios externos.

## Como ejecutarlo

1. Instala las librerias (una sola vez):
   `python -m pip install pygame-ce pyserial`
2. Carga en el ESP32 el firmware `firmware/ninja_mando_v2.ino` (es el mismo de antes).
3. Cierra el Monitor Serie del IDE (el puerto solo lo puede usar un programa).
4. Abre esta carpeta y ejecuta: `python main.py`
5. El puerto esta en `ajustes.py` (`PUERTO = "COM3"`). Si lo pones en `None` lo busca solo.

Sin mando tambien funciona con el raton (mover = cursor, mover rapido = cortar, clic = golpe).

## Teclas

| Tecla | Funcion |
|---|---|
| H | calibrar giro (dos barridos: izquierda-derecha y arriba-abajo) |
| T | calibrar deslizamiento lateral (barridos con el mando sin inclinar) |
| M | cambiar entre mando y raton |
| [ y ] | bajar / subir sensibilidad del golpe |
| G | simular un golpe |
| ESPACIO / ENTER | clic |
| F1 | pantalla de diagnostico del sensor |
| F11 | pantalla completa |
| ESC | volver |

No hace falta boton fisico: dejar el cursor 1 segundo sobre un boton lo pulsa.

## Menu principal

AVENTURA (mapa de 13 niveles con jefe final), MINIJUEGOS (los 9 juegos sueltos, con nivel 1 a 5), CUADERNO (criaturas, peces y dinosaurios),
ITEMS (mochila, equipo de pesca y tienda), GRANJA (mi granja, mi huerto y mi piscicultivo), GACHAPON y RULETA.
Las monedas se ganan al terminar cualquier minijuego (1 por punto + 5 por estrella) y sirven para la tienda y el gachapon.
Cada minijuego terminado cuenta como un dia para la granja.

## Los 9 minijuegos

- **Ninja Frutas**: tajo rapido sobre las frutas (margen de 50%). Cada fruta cortada va a la mochila.
- **Pesca**: apuntar (o gesto de lanzamiento), tirar, esperar, clavar y enrollar con tension. Se ve solo una parte de cada pez para
  juzgar su dificultad; el equipo (caña, cuerda, largo de cuerda, anzuelo y barco) decide que peces y zonas se pueden pescar.
  Los peces capturados van vivos al piscicultivo.
- **Cocina**: recetario en forma de libro (3 recetas por hoja, 2 hojas a la vez), recetas con nivel, habilidades que suben con la practica
  y materiales que se gastan de la mochila.
- **Corta la respuesta**: numeros, colores, formas, contar, letras y patrones.
- **Captura**: niveles 1 a 3 capturan criaturas; nivel 4 es combate por turnos y nivel 5 el jefe Rey Gruñon.
- **Rompecabezas**, **Pintor**.
- **Fosiles**: cinco grados (Arenal a Capa profunda), cuatro herramientas (brocha, martillo, cincel, pincel fino) y huesos fragiles:
  moverse brusco o golpear fuerte los agrieta. Con los 6 huesos y polvo especial se revive el dinosaurio y gana su pagina.
- **Defensa Espacial**: meteoritos, cometas, satelites amigos, planetas y un asteroide gigante.

## Aventura

13 lugares que terminan en el castillo del Rey Gruñon. Cada minijuego da 1 a 3 estrellas.

## Ruleta y Gachapon

Ruleta: cada 80 puntos acumulados se gana un giro (`RULETA_CADA`): mas tiempo, fuerza, alcance, camara lenta, puntos x2, vida extra,
30 monedas o sorpresa (cada mejora dura 3 minijuegos).
Gachapon: cada capsula cuesta `GACHA_COSTO` monedas (100). Sale una figura de rango C, B, A, S, SS o SSS; pueden repetirse.

## Archivos

- `ajustes.py`: lo que se puede afinar. `nucleo.py`: base comun, perfil y mejoras. `entrada.py`: mando, filtros y calibraciones.
- `catalogo.py`: objetos y equipo de pesca. `recetas.py`: recetas y habilidades. `figuras.py`: figuras del gachapon.
- `arte.py`, `arte_dinos.py`, `arte_mar.py`, `arte_cocina.py`, `arte_granja.py`: dibujos.
- `j_*.py`: un archivo por minijuego (`j_combate.py` lo usa Captura en los niveles 4 y 5; `j_agarre.py` son ayudas compartidas).
- `escena.py`, `escena_items.py`, `escena_granja.py`, `escena_gachapon.py`, `aventura.py`: pantallas. `main.py`: arranque.
- `firmware/`: sketch del ESP32 y `diagnostico_mando.py`. `pruebas/`: pruebas automaticas (opcionales).

Se crean solos: `partida.json` (progreso), `calibracion_ejes.json` y `calibracion_deslizamiento.json`.

## Cosas por afinar con el mando real

- `UMBRAL_GOLPE`, `PX_POR_METRO` (en `ajustes.py`).
- Fosiles: la velocidad que agrieta un hueso se calibro con raton simulado.
- Dificultad, estrellas y precios (equipo en `catalogo.py`, gachapon y monedas en `ajustes.py`): estimados, no medidos con un nino real.
