# arduino_deteccion_camara_v.0.01

Sistema de detección de movimiento que envía señales a un Arduino UNO Q por comunicación serial para abrir/cerrar los "dvd". Actualmente la detección la hace un **sensor ultrasónico** conectado al mismo Arduino; el código de detección por cámara sigue en el proyecto, desactivado, para usarlo más adelante.

## Requisitos

- Python 3.7+
- Arduino UNO Q con el sketch `arduino-uno-q/arduino-uno-q.ino` cargado

## Instalación

```bash
# Crear entorno virtual
python -m venv env

# Activar entorno virtual
# Windows:
env\Scripts\activate
# Linux/Mac:
source env/bin/activate

# Instalar dependencias
pip install opencv-python pyserial
```

## Hardware

Un solo Arduino UNO Q maneja las LEDs y el sensor ultrasónico:

| Pin | Uso |
|-----|-----|
| `6` | LED "cerrado" |
| `7` | LED "abierto" |
| `9` | Trig del sensor ultrasónico (directo) |
| `10` | Echo del sensor ultrasónico (con divisor de voltaje) |
| `5V` | Vcc del sensor |
| `GND` | Gnd del sensor |

## Configuración

Editar las constantes en `deteccion_camara.py`:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `USAR_CAMARA` | Activa/desactiva la detección por cámara | `False` |
| `PUERTO_ARDUINO` | Puerto serial del Arduino UNO Q | `COM6` |
| `BAUDIOS` | Velocidad de comunicación | `9600` |
| `CAMARA` | Índice de la cámara (solo si `USAR_CAMARA=True`) | `0` |
| `AREA_MINIMA` | Área mínima de movimiento en px (solo cámara) | `1500` |
| `SEGUNDOS_PARA_CERRAR` | Segundos sin detección para cerrar | `1` |
| `SEGUNDOS_ENTRE_MENSAJES` | Cada cuánto imprime que sigue corriendo | `2` |

## Protocolo de comunicación

| Dirección | Señal | Significado |
|-----------|-------|-------------|
| PC → Arduino | `a` | Abrir (LED "abierto") |
| PC → Arduino | `c` | Cerrar (LED "cerrado") |
| Arduino → PC | `1` | Sensor ultrasónico detectó movimiento |
| Arduino → PC | `0` | Sensor ultrasónico sin detección |

## Uso

```bash
python deteccion_camara.py
```

- Imprime un mensaje al conectar y luego un mensaje cada `SEGUNDOS_ENTRE_MENSAJES` segundos con el estado actual, para confirmar que sigue corriendo.
- Si `USAR_CAMARA=True`, presiona `q` en la ventana de video para salir; si no, usa `Ctrl+C`.
- Al cerrar la aplicación se envía automáticamente la señal de cierre (`c`).