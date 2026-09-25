import time

import cv2
import serial

# ---------------- CONFIGURACIÓN ----------------
USAR_CAMARA = False           # cámara desactivada por ahora; queda lista para reactivarla después

PUERTO_ARDUINO = "COM7"       # el único Arduino UNO Q: LEDs + sensor ultrasónico
BAUDIOS = 9600

CAMARA = 0
AREA_MINIMA = 1500
SEGUNDOS_PARA_CERRAR = 1
FRAMES_CALENTAMIENTO = 30
SEGUNDOS_ENTRE_MENSAJES = 2   # cada cuánto imprime que sigue corriendo

ORDEN_ABIERTO = b"a"
ORDEN_CERRADO = b"c"
# ------------------------------------------------


def hay_deteccion(frame, sustractor):
    """Devuelve (detectado, frame_con_cajas) usando sustracción de fondo.
    No se usa mientras USAR_CAMARA sea False; queda lista para más adelante."""
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


def leer_ultrasonido(arduino, ultimo_estado):
    """Lee todas las líneas pendientes del Arduino.
    Se espera '1' cuando detecta movimiento y '0' cuando no.
    Devuelve el último estado leído, o el estado anterior si no llegó nada nuevo."""
    estado = ultimo_estado
    while arduino.in_waiting:
        linea = arduino.readline().decode(errors="ignore").strip()
        if linea == "1":
            estado = True
        elif linea == "0":
            estado = False
    return estado


def main():
    arduino = serial.Serial(PUERTO_ARDUINO, BAUDIOS, timeout=1)
    time.sleep(2)
    print(f"Conectado a {PUERTO_ARDUINO}. Escuchando el sensor... (Ctrl+C para salir)")

    camara = None
    sustractor = None
    if USAR_CAMARA:
        camara = cv2.VideoCapture(CAMARA)
        if not camara.isOpened():
            arduino.close()
            raise RuntimeError("No se pudo abrir la cámara. Revisa el índice CAMARA.")
        sustractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)

    abierto = False
    ultima_deteccion = 0.0
    estado_ultrasonido = False
    ultimo_mensaje = 0.0

    try:
        while True:
            estado_ultrasonido = leer_ultrasonido(arduino, estado_ultrasonido)
            detectado = estado_ultrasonido

            ahora = time.time()
            if detectado:
                ultima_deteccion = ahora
                if not abierto:
                    arduino.write(ORDEN_ABIERTO)
                    abierto = True
                    print("Ultrasonido detectó -> LED abierto ('a')")
            elif abierto and (ahora - ultima_deteccion) > SEGUNDOS_PARA_CERRAR:
                arduino.write(ORDEN_CERRADO)
                abierto = False
                print("Sin detección -> LED cerrado ('c')")

            if ahora - ultimo_mensaje >= SEGUNDOS_ENTRE_MENSAJES:
                ultimo_mensaje = ahora
                estado_txt = "detectando" if detectado else "sin detección"
                print(f"[activo] estado sensor: {estado_txt} | LEDs: {'abierto' if abierto else 'cerrado'}")

            if USAR_CAMARA and camara is not None:
                ok, frame = camara.read()
                if ok:
                    _, frame = hay_deteccion(frame, sustractor)  # solo para visualizar, sin afectar la decisión
                    estado_txt = "ABIERTO (a)" if abierto else "CERRADO (c)"
                    cv2.putText(frame, estado_txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0) if abierto else (0, 0, 255), 2)
                    cv2.imshow("Camara", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            else:
                time.sleep(0.05)  # pequeña pausa para no saturar el CPU; Ctrl+C para salir

    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    finally:
        try:
            arduino.write(ORDEN_CERRADO)
            print("Cierre enviado al salir")
        except Exception as e:
            print(f"Error al enviar cierre: {e}")
        if camara is not None:
            camara.release()
        cv2.destroyAllWindows()
        arduino.close()


if __name__ == "__main__":
    main()
