# Ninja Mundo en el telefono (APK)

El APK se genera en la nube de GitHub (Buildozer no corre en Windows).

## 1. Subir el proyecto a GitHub (una sola vez)
1. En github.com crea un repositorio nuevo, por ejemplo `ninja-mundo`, privado o publico.
2. Sube todo el contenido de esta carpeta (no la carpeta misma): arrastra los archivos a la
   pagina del repositorio o usa GitHub Desktop.
   No subas `partida.json`, `calibracion_*.json` ni `.venv`.

## 2. Generar el APK
1. Entra a la pestana **Actions** del repositorio.
2. Elige **Build APK** y pulsa **Run workflow** (tambien se ejecuta cada vez que subes cambios).
3. Espera unos 30-60 minutos la primera vez (las siguientes son mas rapidas).
4. Cuando termine, abre la ejecucion y descarga el archivo **ninja-mundo-apk** (un .zip con el .apk dentro).

## 3. Instalarlo en el telefono
1. Pasa el .apk al telefono (cable, Drive, WhatsApp a ti mismo, etc.).
2. Al abrirlo, Android pedira permitir "instalar apps desconocidas": aceptalo para ese origen.
3. Abre **Ninja Mundo**. Se juega con la pantalla: tocar = clic, deslizar rapido = cortar.
   El boton "Atras" del telefono funciona como ESC.

## Notas
- El APK no usa mando ESP32 ni internet. El progreso se guarda dentro del telefono.
- Si una tarea de GitHub Actions falla, copia el mensaje de error del paso en rojo y pegalo en el chat.
