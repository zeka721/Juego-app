"""Arma una carpeta 'stage/' lista para Buildozer con UNA sola app.

Uso:  python tools/armar.py gusano|ruinas|tama [carpeta_salida]
Variable opcional NINJA_ARCH (arm64-v8a por defecto; x86_64 para probar en emulador).
"""
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = {
    # nombre: (titulo, package.name, 'propia' = carpeta apps/<nombre>, 'juego' = codigo del juego)
    "gusano": ("Gusano Prueba", "gusanoprueba", "propia"),
    "ruinas": ("Ruinas", "ninjaruinas", "juego"),
    "tama": ("Tamagotchi", "ninjatama", "juego"),
}


def main():
    nombre = sys.argv[1]
    destino = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "stage"))
    titulo, paquete, tipo = APPS[nombre]
    if os.path.exists(destino):
        shutil.rmtree(destino)
    os.makedirs(destino)

    if tipo == "propia":
        shutil.copy(os.path.join(RAIZ, "apps", nombre, "main.py"), destino)
    else:
        for f in sorted(os.listdir(RAIZ)):
            if f.endswith(".py") and not f.startswith("test_") and f != "aventura_respaldo.py":
                shutil.copy(os.path.join(RAIZ, f), destino)
        with open(os.path.join(destino, "juego.txt"), "w") as fh:
            fh.write(nombre)
    shutil.copytree(os.path.join(RAIZ, "p4a_recipes"), os.path.join(destino, "p4a_recipes"),
                    ignore=shutil.ignore_patterns("__pycache__"))

    spec = open(os.path.join(RAIZ, "buildozer.spec"), encoding="utf-8").read()
    arch = os.environ.get("NINJA_ARCH", "arm64-v8a")
    for clave, valor in (("title", titulo), ("package.name", paquete), ("android.archs", arch)):
        spec, n = re.subn(r"(?m)^%s\s*=.*$" % re.escape(clave), "%s = %s" % (clave, valor), spec)
        assert n == 1, clave
    open(os.path.join(destino, "buildozer.spec"), "w", encoding="utf-8").write(spec)
    print("stage listo:", destino, "| app:", nombre, "| paquete: org.ninjamundo." + paquete, "| arch:", arch)


main()
