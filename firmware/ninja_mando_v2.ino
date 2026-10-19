// Mando Ninja Fruit v2 - ESP32 Super Mini C3 + MPU6050 (espada con giroscopio)
// Envia por USB ~100 lineas por segundo:
//   tiempo_ms,ax,ay,az,gx,gy,gz,boton
//   ax,ay,az : aceleracion en g
//   gx,gy,gz : giro en grados/segundo (con el sesgo en reposo ya restado)
//   boton    : 1 = suelto, 0 = presionado (GPIO 4 a GND, opcional)
// Al encender, deja la espada QUIETA un par de segundos para calibrar el giroscopio.
// Sin librerias externas: solo Wire.h

#include <Wire.h>

#define MPU_ADDR   0x68
#define PIN_SDA    5
#define PIN_SCL    6
#define PIN_BOTON  4

const float ESCALA_ACEL = 8192.0;   // +-4 g
const float ESCALA_GIRO = 32.8;     // +-1000 grados/segundo
const uint32_t PERIODO_US = 10000;  // 100 lecturas por segundo

float sesgo[3] = {0, 0, 0};         // sesgo del giroscopio en reposo (gx, gy, gz)

void escribirRegistro(uint8_t reg, uint8_t valor) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(valor);
  Wire.endTransmission();
}

// Lee aceleracion, temperatura y giro de una sola vez (14 bytes)
bool leerCrudo(int16_t raw[7]) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, 14) < 14) return false;
  for (int i = 0; i < 7; i++) {
    int16_t alto = Wire.read();
    int16_t bajo = Wire.read();
    raw[i] = (alto << 8) | bajo;
  }
  return true;
}

int leerQuienSoy() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x75);                       // registro WHO_AM_I
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom(MPU_ADDR, 1) < 1) return -1;
  return Wire.read();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BOTON, INPUT_PULLUP);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);

  int quien = leerQuienSoy();
  if (quien < 0) {
    for (int i = 0; i < 5; i++) {
      Serial.println("# ERROR: el sensor MPU6050 no responde (revisa VCC, GND, SDA=GPIO5, SCL=GPIO6)");
      delay(300);
    }
  } else {
    Serial.printf("# sensor detectado, WHO_AM_I=0x%02X\n", quien);
  }

  escribirRegistro(0x6B, 0x01);   // despertar el sensor
  escribirRegistro(0x1A, 0x03);   // filtro pasa-bajos (~44 Hz)
  escribirRegistro(0x1B, 0x10);   // giroscopio +-1000 grados/s (tajos rapidos)
  escribirRegistro(0x1C, 0x08);   // acelerometro +-4 g
  delay(500);

  Serial.println("# calibrando giroscopio: manten la espada quieta");
  float suma[3] = {0, 0, 0};
  int n = 0;
  for (int k = 0; k < 400; k++) {
    int16_t raw[7];
    if (leerCrudo(raw)) {
      for (int i = 0; i < 3; i++) suma[i] += raw[4 + i] / ESCALA_GIRO;
      n++;
    }
    delay(3);
  }
  if (n > 0) {
    for (int i = 0; i < 3; i++) sesgo[i] = suma[i] / n;
  }
  Serial.println("# listo");
}

void loop() {
  static uint32_t proximo = micros();
  while ((int32_t)(micros() - proximo) < 0) { }
  proximo += PERIODO_US;
  if ((int32_t)(micros() - proximo) > 50000) proximo = micros();

  int16_t raw[7];
  if (!leerCrudo(raw)) {
    static uint32_t ultimoAviso = 0;
    if (millis() - ultimoAviso > 1000) {
      ultimoAviso = millis();
      Serial.println("# ERROR: fallo de lectura I2C del MPU6050");
    }
    return;
  }

  float ax = raw[0] / ESCALA_ACEL;
  float ay = raw[1] / ESCALA_ACEL;
  float az = raw[2] / ESCALA_ACEL;
  float gx = raw[4] / ESCALA_GIRO - sesgo[0];
  float gy = raw[5] / ESCALA_GIRO - sesgo[1];
  float gz = raw[6] / ESCALA_GIRO - sesgo[2];
  int boton = digitalRead(PIN_BOTON);

  Serial.printf("%lu,%.3f,%.3f,%.3f,%.1f,%.1f,%.1f,%d\n",
                (unsigned long)millis(), ax, ay, az, gx, gy, gz, boton);
}
