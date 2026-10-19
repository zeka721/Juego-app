[app]

# ---- Identidad de la app ----
title = Ninja Mundo
package.name = ninjamundo
package.domain = org.ninjamundo
version = 0.1

# ---- Codigo ----
source.dir = .
source.include_exts = py,png,jpg,json,txt,md
source.exclude_dirs = pruebas,firmware,dataset_defensa_espacial,.venv,.idea,__pycache__,.github,bin,build
# Los datos de partida y calibracion se crean en el telefono: no van dentro del APK
source.exclude_patterns = partida.json,calibracion_*.json,test_*.py,*.patch,*.ino

# ---- Librerias para el telefono ----
requirements = python3,pygame

# Receta de pygame propia (2.6.1) para compilar con Python moderno
p4a.local_recipes = ./p4a_recipes

# ---- Pantalla ----
orientation = landscape
fullscreen = 1

# ---- Android ----
android.permissions =
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
