# CONTRATO TAMAGOTCHI (reemplaza a Captura como juego de crianza)  -- leer entero antes de tocar nada
Carpeta: ninja_mundo/. pygame-ce 1280x720 (ajustes.ANCHO/ALTO). Nino de 5 anos: nada duro, nada de muerte (la mascota nunca muere:
si se descuida se pone triste/enferma y se recupera), sin emojis, espanol claro, controles solo cursor (ctrl.pos) con dwell (nucleo.Boton)
y clic opcional. Pruebas headless: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 pruebas/test_xxx.py -> "TODO OK".
Capturas /tmp/shots, revisalas con Read. Calidad PROFESIONAL: arte pulido, animaciones suaves, nada de rectangulos pelados.
Arte procedural con pygame (sin archivos externos; la capa de imagenes del usuario llegara la proxima semana, deja las funciones de
dibujo centralizadas en arte_tama.py para poder reemplazarlas luego).

## Concepto
18 huevos distintos (indice 0..17) sin pista de lo que contienen. El jugador elige uno, lo calienta/frota hasta que eclosiona y recien ahi se
revela la especie. 18 especies = 6 tipos x 3. Cada especie tiene 4 etapas: 0 Bebe, 1 Nino, 2 Adulto, 3 Ultimate. El TIPO (elemento) no cambia
al evolucionar; sube la intensidad de los efectos y el tamano. Se cria (comer, jugar, banar/limpiar, dormir, curar), el alimento sale del
inventario de la granja y se entrena peleando (batalla por turnos con ataque basico, ataque cargado (gesto) y escapar).

TIPOS (ids): agua, viento, fuego, hielo, tierra, electrico. Ciclo de ventajas (cada uno es fuerte contra el siguiente, debil contra el anterior):
 fuego > hielo > viento > tierra > electrico > agua > fuego.  (x1.5 ventaja, x0.67 desventaja, x1 resto)
GESTOS del ataque cargado (se traza una GUIA visible, tenue, que se sigue con el cursor pasando por puntos de control en orden; 3 vueltas = carga completa):
 electrico: zigzag vertical (rayo)  | fuego: circulo | hielo: rombo | agua: ola (seno horizontal) | viento: ocho acostado (infinito) | tierra: triangulo (montana)

ESPECIES (id: tipo, animal, formas por etapa [Bebe, Nino, Adulto, Ultimate])
 agua:     delfin  (delfin)   Gotin, Salpin, Delfaron, Delfonte
           tortuga (tortuga)  Tortin, Marin, Caparazul, Tortamarea
           pulpo   (pulpo)    Burbi, Pulpin, Octoparla, Abisalo
 viento:   mariposa(mariposa) Alin, Mariposin, Brisaflor, Alaciclon
           ardilla (ardilla voladora) Rafi, Planin, Ventarro, Tornadero
           buho    (buho)     Plumin, Buhito, Nocturvento, Buhotempestad
 fuego:    dragon  (dragon)   Brasin, Dragulla, Pirodraco, Dracolava
           lobo    (lobo)     Ascuito, Cenizo, Lobollama, Lobo Solar
           fenix   (fenix)    Cenicin, Pollollama, Ave Brasa, Fenix Solar
 hielo:    pinguino(pinguino) Copito, Pinguin, Glacialpin, Pinguirey
           oso     (oso polar)Nevadito, Osnevado, Glaciosso, Osoboreal
           ciervo  (ciervo)   Escarchin, Cervatillo, Ciervo Glacial, Cervirey Cristal
 tierra:   armadillo(armadillo) Rocadillo, Armadin, Tierradillo, Armadura Titan
           topo    (topo)     Toposo, Topin, Excavon, Topogigante
           escarabajo(escarabajo) Terron, Escarabin, Cuernoroca, Escarabeon
 electrico:raton   (raton)    Voltin, Ratonchispa, Electrorrata, Megavoltio
           gato    (gato/tigre) Zapin, Gatochispa, Truenotigre, Tigre Relampago
           rana    (rana)     Zumbi, Ranazap, Voltirrana, Rey Trueno
 (usar estos ids y nombres EXACTOS; se pueden poner tildes en NOMBRES visibles, p.ej. "Delfarón", pero los ids van sin tildes)
Tamano en pantalla (altura aprox con escala 1.0): Bebe 120 px, Nino 165, Adulto 215, Ultimate 270. Cada etapa debe verse claramente MAS evolucionada
(mas detalles, mas elementos del tipo: aura, corona, alas, cola mas larga, cuernos, cristales...) pero reconociblemente la misma linea evolutiva
(mismos colores base y rasgos). Estilo: chibi/amigable, contorno oscuro grueso, sombreado suave, brillos, ojos grandes (usar arte_tama_base.ojos),
paleta propia por especie (coherente con su tipo), nada agresivo ni aterrador (ni siquiera los Ultimate: poderosos pero simpaticos).

## API de arte (arte_tama.py es el despachador; lo escribe el agente ARTE-COMUN; arte_tama_base.py ya existe)
TIPOS, ESPECIES (ids en orden: agua x3, viento x3, fuego x3, hielo x3, tierra x3, electrico x3), TIPO_DE[id], COLOR_TIPO[tipo] (rgb), NOMBRE_TIPO[tipo].
def dibujar_mascota(p, especie, etapa, cx, cy, escala=1.0, t=0.0, estado="normal", dir=1, silueta=False)
   (cx,cy) = centro de los pies/centro del cuerpo (documentar: usar centro del cuerpo); dir=1 mira a la derecha, -1 izquierda.
   estado in: normal, feliz, triste, hambre, duerme, enfermo, come, ataca, golpeado, evoluciona (brillo) -> cambia ojos/boca/postura/animacion.
   Siempre con animacion idle suave dependiente de t (respirar, rebote, parpadeo). silueta=True: forma rellena gris oscuro (sin detalles) para "???".
def dibujar_huevo(p, k, cx, cy, escala=1.0, t=0.0, grieta=0, mecer=0.0, brillo=0.0)
   k 0..17: 18 disenos CLARAMENTE distintos (colores/patrones/manchas/rayas/estrellas/puntos...) que NO delaten el tipo; grieta 0..4 (4 = a punto de abrir);
   mecer 0..1 = intensidad del balanceo; brillo 0..1 aura calida. Tamano ~150 px de alto con escala 1.
def dibujar_cascaras(p, k, cx, cy, f, t)   animacion de cascaras saltando al eclosionar, f 0..1
def dibujar_ataque_basico(p, tipo, etapa, x0, y0, x1, y1, f, t)   proyectil/golpe del tipo viajando de (x0,y0) a (x1,y1), f 0..1; intensidad crece con etapa
def dibujar_impacto(p, tipo, etapa, x, y, f, t)                    efecto en el blanco, f 0..1
def dibujar_carga(p, tipo, etapa, cx, cy, f, t)                    energia acumulandose alrededor de la mascota, f 0..1
def dibujar_ataque_cargado(p, tipo, etapa, x0, y0, x1, y1, f, t)   ataque grande del elemento (rayo, bola de fuego, lluvia de cristales de hielo, ola, tornado,
                                                                    rocas) con intensidad por etapa (mas grande, mas particulas, pantalla con destello); f 0..1
def dibujar_guia(p, tipo, rect, progreso=None, t=0.0, ancho=...)   dibuja la forma-guia del gesto (tenue, brillante) dentro de rect
def puntos_guia(tipo, rect) -> lista de (x,y) puntos de control EN ORDEN de UNA vuelta (cerrada o no) para el gesto del tipo (>= 10 puntos, espaciados ~uniformes)
def dibujar_icono_tipo(p, tipo, cx, cy, r)
def dibujar_icono_accion(p, accion, cx, cy, tam, activo=True)   acciones: comer, jugar, limpiar, dormir, curar, entrenar, cuaderno, huevos, volver
def dibujar_fondo_hogar(p, t, noche=False)   cuarto/jardin acogedor a pantalla completa (dia/noche con luna y estrellas si noche)
def dibujar_fondo_arena(p, tipo, t)          arena de entrenamiento tematizada con el tipo del rival o neutra si tipo=None
def dibujar_caca(p, x, y, s=1.0, t=0.0)      "popo" simpatica con moscas/brillo (nada asqueroso)
def dibujar_nube_estado(p, x, y, estado, t)  burbuja de pensamiento con icono (hambre, sueno, diversion, limpieza, salud)
def dibujar_aura_evolucion(p, cx, cy, f, t)  espiral de luz al evolucionar
Las funciones mascota por especie viven en arte_tama_agua_viento.py, arte_tama_fuego_hielo.py, arte_tama_tierra_electrico.py, cada una con
  DIBUJOS = {especie_id: fn(p, etapa, cx, cy, escala, t, estado, dir, silueta)}; arte_tama.dibujar_mascota solo despacha (importando los 3 modulos
  con try/except para que funcione mientras faltan).
## Datos (tama_datos.py) -- lo escribe el agente DATOS.  Todo el estado en perfil.extra["tama"] (JSON; claves str)
TIPOS, NOMBRE_TIPO, ESPECIES (dict id-> dict(id,tipo,animal,formas=[4 nombres])), ORDEN (18 ids), ETAPAS=["Bebé","Niño","Adulto","Ultimate"]
estado(perfil) -> dict normalizado con: huevos (lista de 18 especies, mapeo huevo->especie barajado una sola vez), huevo (indice elegido o None),
  calor (0..1 progreso de eclosion), activa (None o dict mascota: especie, etapa, xp, hambre, felicidad, energia, limpieza, salud (0..100), cacas (int),
  dormida (bool), ultimo (timestamp), cuidado (puntos de cuidado), batallas, victorias, nombre), eclosionados (lista de huevos ya abiertos),
  descubiertas (dict especie-> etapa maxima alcanzada), salon (lista de dict(especie, etapa, nombre) de mascotas graduadas).
elegir_huevo(perfil,k)->bool (solo si no hay mascota/huevo activo y k no eclosionado); calentar(perfil, cantidad)->calor; calor_listo; eclosionar(perfil)->especie
tick(perfil, ahora=None): paso del tiempo real (necesidades bajan lento: ~ -1 punto cada 40-90 s segun la necesidad; offline limitado a un maximo de -50; duerme: energia sube; nunca muere);
  genera cacas con el tiempo (max 4). necesidad_baja(perfil)-> nombre de la necesidad mas urgente o None.
comidas(perfil)->lista de (item_id, cantidad) del inventario que son comida (fruta, verdura, granja/comida: usa catalogo.info(item)["cat"] o la tabla que hay);
  valor_comida(item)->dict(hambre, felicidad, xp) o None; favorita(especie)-> categoria/tipo de comida que mas le gusta (bonus x1.5);
  comer(perfil,item)->dict resultado o None (descuenta 1 del inventario)
jugar(perfil, puntos)->(felicidad ganada); limpiar(perfil)->bool(quita cacas, sube limpieza); dormir(perfil, on); curar(perfil)->bool (cuesta 1 'medicina'? NO: gratis, tarda; sube salud)
xp_necesaria(etapa)->XP para pasar a la siguiente (p.ej. 100, 300, 700); dar_xp(perfil, n); puede_evolucionar(perfil)->bool (xp suficiente y cuidado >= minimo, nunca bloqueante duro:
  cuidado se gana cuidando; si cuidado es bajo evoluciona igual pero con aviso 'se podria haber cuidado mas' no, simplemente exigir cuidado>=umbral bajo);
  evolucionar(perfil)->nueva etapa; graduar(perfil) (al llegar a Ultimate con xp lleno: pasa al salon y libera para elegir otro huevo; tambien permitir al jugador conservarla activa hasta decidir).
stats(especie, etapa)->dict(hp, ataque, estamina_max=100); (hp 60,100,150,220; ataque base 10,16,24,34, con ligera variacion por especie segun id)
ventaja(tipo_atacante, tipo_defensor)->1.5/1.0/0.67; dano(ataque_stats, etapa, tipo_a, tipo_d, cargado=False, calidad=1.0, rng=None)->int
  (basico ~ ataque*0.9..1.1; cargado = ataque*2.6*calidad(0.5..1.2); x ventaja)
ESTAMINA_BASICO=25 (4 basicos llenan 100). enemigo(perfil, rng=None)->dict(especie, etapa, tipo, hp, ataque, nombre) (rival de etapa igual o +-1 a la de la mascota, tipo al azar)
recompensa_batalla(perfil, resultado('gana'|'pierde'|'escapa'), dano_hecho, hp_restante_frac)->dict(xp, monedas, items{}) y la APLICA (da xp, monedas via perfil.monedas, items en perfil.inventario)
aviso_evolucion(perfil)->bool (hay evolucion pendiente) etc.
## Minijuego de batalla (j_tama.py) y hub (escena_tama.py) -- ver prompts de cada agente. Integracion aventura.py: minima, con .patch.
