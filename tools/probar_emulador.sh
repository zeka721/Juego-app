#!/usr/bin/env bash
# Instala el APK en el emulador, lo abre dos veces (como hace una persona) y recoge pruebas de que corre o por que se cae.
# Uso: probar_emulador.sh <paquete> <etiqueta>      (el APK esta en apk/*.apk)
PKG="$1"; ETQ="${2:-prueba}"
OUT=salida; mkdir -p "$OUT"
APK=$(ls apk/*.apk | head -1)
echo "APK: $APK  paquete: $PKG"
adb wait-for-device
adb shell input keyevent KEYCODE_WAKEUP
adb install -r "$APK" 2>&1 | tee "$OUT/instalar.txt"

enc() { sed ':a;N;$!ba;s/%/%25/g;s/\r//g;s/\n/%0A/g' ; }
FILTRO='python|PythonActivity|SDL|DEBUG|AndroidRuntime|FATAL|Fatal|libc|GUSANO|PASO|ERROR|Traceback|signal|SIGSEGV|SIGABRT|dlopen|UnsatisfiedLink|Error|error log|ninja'

lanzar() {  # $1 = numero de intento
  adb logcat -c
  adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
  sleep 12
  adb exec-out screencap -p > "$OUT/pantalla_$1_12s.png"
  VIVO12=$(adb shell pidof "$PKG" | tr -d '\r')
  adb shell input tap 320 160
  sleep 2
  adb shell input swipe 100 100 500 250 400
  sleep 14
  adb exec-out screencap -p > "$OUT/pantalla_$1_30s.png"
  VIVO30=$(adb shell pidof "$PKG" | tr -d '\r')
  adb logcat -d > "$OUT/logcat_$1.txt"
  adb shell "run-as $PKG cat files/error.log" > "$OUT/error_log_$1.txt" 2>&1
  adb shell "run-as $PKG cat files/fatal.log" > "$OUT/fatal_log_$1.txt" 2>&1
  ESTADO="intento $1: pid a los 12s='${VIVO12}' pid a los 30s='${VIVO30}'"
  echo "$ESTADO"
  {
    echo "### $ESTADO"
    echo '--- error.log de la app ---'; cat "$OUT/error_log_$1.txt"
    echo '--- fatal.log de la app ---'; cat "$OUT/fatal_log_$1.txt" | tail -40
    echo '--- logcat (filtrado, final) ---'; grep -E "$FILTRO" "$OUT/logcat_$1.txt" | tail -70
  } > "$OUT/resumen_$1.txt"
  if [ -z "$VIVO30" ]; then NIVEL=error; else NIVEL=notice; fi
  echo "::${NIVEL} title=${ETQ} ${ESTADO}::$(head -c 60000 "$OUT/resumen_$1.txt" | enc)"
  cat "$OUT/resumen_$1.txt" >> "$GITHUB_STEP_SUMMARY" 2>/dev/null
}

lanzar 1
adb shell am force-stop "$PKG"
sleep 2
lanzar 2
exit 0
