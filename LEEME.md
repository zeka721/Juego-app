COCINA v2 - copia estos archivos dentro de tu carpeta del juego (reemplaza los que ya existen).

NUEVOS (9): cocina_base.py, cocina_datos.py, cocina_recetas.py, cocina_herramientas.py,
            cocina_ingredientes.py, cocina_platos.py, cocina_pasos_cortes.py, cocina_pasos_masas.py,
            cocina_pasos_fuego.py
REEMPLAZAN (4): j_cocina.py, arte_granja.py, escena_granja.py, j_pesca.py
UN CAMBIO A MANO en aventura.py (clase Intro, en actualizar, ~linea 332):
    antes:   self.nivel = min(5, self.nivel + 1)
    despues: self.nivel = min(self.clase.NIVEL_MAX, self.nivel + 1)
PRUEBAS (carpeta pruebas/): test_cocina.py, test_pasos_cortes.py, test_pasos_masas.py,
            test_pasos_fuego.py, test_arte_cocina.py
NO borres recetas.py (lo usa escena_items). Tus partidas viejas se migran solas
(picar->cortar, mezclar->girar, sazonar->espolvorear).
