"""
Detección con cámara -> envía por serial:
    'a' cuando detecta algo (abierto)
    'c' cuando no detecta nada (cerrado)

Requisitos:
    pip install opencv-python pyserial

Uso:
    python deteccion_camara.py
    Presiona 'q' en la ventana de video para salir.
"""

import time

import cv2
import serial

# ---------------- CONFIGURACIÓN ----------------
PUERTO = "COM6"              # Windows: "COM3", Linux: "/dev/ttyACM0", Mac: "/dev/cu.usbmodem..."
BAUDIOS = 9600
CAMARA = 0                   # 0 = primera cámara del equipo
AREA_MINIMA = 1500           # tamaño mínimo (px) del movimiento para contar como detección
SEGUNDOS_PARA_CERRAR = 1     # tiempo sin detectar nada antes de enviar 'b'
FRAMES_CALENTAMIENTO = 30    # frames iniciales para que aprenda el fondo

ORDEN_ABIERTO = b"a"
ORDEN_CERRADO = b"c"
# ------------------------------------------------


def hay_deteccion(frame, sustractor):
    """Devuelve (detectado, frame_con_cajas) usando sustracción de fondo."""
    mascara = sustractor.apply(frame)
    _, mascara = cv2.threshold(mascara, 200, 255, cv2.THRESH_BINARY)  # quita sombras
    mascara = cv2.erode(mascara, None, iterations=2)
    mascara = cv2.dilate(mascara, None, iterations=3)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detectado = False
    for c in contornos:
        if cv2.contourArea(c) < AREA_MINIMA:
            continue
        detectado = True
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return detectado, frame


def main():
    arduino = serial.Serial(PUERTO, BAUDIOS, timeout=1)
    time.sleep(2) 

    camara = cv2.VideoCapture(CAMARA)
    if not camara.isOpened():
        arduino.close()
        raise RuntimeError("No se pudo abrir la cámara. Revisa el índice CAMARA.")

    sustractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)

    abierto = False
    ultima_deteccion = 0.0
    frames_vistos = 0

    try:
        while True:
            ok, frame = camara.read()
            if not ok:
                print("No se pudo leer la cámara.")
                break

            detectado, frame = hay_deteccion(frame, sustractor)
            frames_vistos += 1

            # Durante el calentamiento solo aprende el fondo
            if frames_vistos > FRAMES_CALENTAMIENTO:
                ahora = time.time()

                if detectado:
                    ultima_deteccion = ahora
                    if not abierto:
                        arduino.write(ORDEN_ABIERTO)
                        abierto = True
                        print("Detectado -> enviado 'a'")

                elif abierto and (ahora - ultima_deteccion) > SEGUNDOS_PARA_CERRAR:
                    arduino.write(ORDEN_CERRADO)
                    abierto = False
                    print("Sin detección -> enviado 'c'")

            estado = "ABIERTO (a)" if abierto else "CERRADO (c)"
            cv2.putText(frame, estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0) if abierto else (0, 0, 255), 2)
            cv2.imshow("Camara", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        try:
            arduino.write(ORDEN_CERRADO)
            print("Cierre enviado al salir")
        except Exception as e:
            print(f"Error al enviar cierre: {e}")
        camara.release()
        cv2.destroyAllWindows()
        arduino.close()


if __name__ == "__main__":
    main()