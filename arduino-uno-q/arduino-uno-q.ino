  // ---------------- CONFIGURACIÓN ----------------
const int PIN_LED_ABRIR = 7;   // LED "abierto"
const int PIN_LED_CERRAR = 6;  // LED "cerrado"

const int PIN_TRIG = 9;   // al pin "Trig" del sensor (directo)
const int PIN_ECHO = 10;  // al punto medio del divisor de voltaje del "Echo"

const float DISTANCIA_UMBRAL_CM = 30.0;  // por debajo de esto = "detectado"
const unsigned long INTERVALO_MEDICION_MS = 100;
// ------------------------------------------------

char dato;
unsigned long ultimaMedicion = 0;
bool ultimoEstadoUltrasonido = false;

void Abrir() {
  digitalWrite(PIN_LED_CERRAR, LOW);
  digitalWrite(PIN_LED_ABRIR, HIGH);
}

void Cerrar() {
  digitalWrite(PIN_LED_CERRAR, HIGH);
  digitalWrite(PIN_LED_ABRIR, LOW);
}

float medirDistanciaCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duracion = pulseIn(PIN_ECHO, HIGH, 30000UL);  // timeout de 30ms
  if (duracion == 0) {
    return -1.0;  // no hubo lectura válida
  }
  return duracion * 0.0343 / 2.0;
}

void setup() {
  pinMode(PIN_LED_ABRIR, OUTPUT);
  pinMode(PIN_LED_CERRAR, OUTPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  Serial.begin(9600);
  Cerrar();  // estado inicial
}

void loop() {
  // 1) Escucha comandos que vengan de Python ('a' / 'c')
  if (Serial.available() > 0) {
    dato = Serial.read();
    if (dato == 'a') {
      Abrir();
    } else if (dato == 'c') {
      Cerrar();
    }
  }

  // 2) Mide el sensor ultrasónico y avisa por serial cuando cambia el estado
  unsigned long ahora = millis();
  if (ahora - ultimaMedicion >= INTERVALO_MEDICION_MS) {
    ultimaMedicion = ahora;

    float distancia = medirDistanciaCm();
    bool detectado = (distancia > 0 && distancia < DISTANCIA_UMBRAL_CM);

    if (detectado != ultimoEstadoUltrasonido) {
      Serial.println(detectado ? "1" : "0");
      ultimoEstadoUltrasonido = detectado;
    }
  }
}
