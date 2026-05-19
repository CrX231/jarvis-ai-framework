import pyautogui
import time
import os

class DesktopAgent:
    def __init__(self, logger):
        self.logger = logger
        # Medida de seguridad: Si arrastras el mouse a cualquier esquina, Jarvis se detiene de golpe
        pyautogui.FAILSAFE = True
        # Pequeña pausa automática entre cada movimiento para que el sistema operativo reaccione
        pyautogui.PAUSE = 0.5
        
        self.logger.info("Agente de Escritorio (Control Físico) inicializado con FailSafe activado.")

    def type_text(self, text):
        """Escribe texto simulando un teclado físico humano (letra por letra)."""
        self.logger.info(f"[DesktopAgent] Escribiendo texto de forma manual.")
        # interval=0.03 hace que escriba rapidísimo, pero como un humano, no como un bot pegando texto
        pyautogui.write(text, interval=0.03)
        return "Texto ingresado físicamente en la interfaz actual."

    def press_shortcut(self, combination):
        """Presiona atajos de teclado (ej: 'enter', 'ctrl', 'c', 'win', 'd')."""
        self.logger.info(f"[DesktopAgent] Ejecutando atajo: {combination}")
        keys = [k.strip() for k in combination.split('+')]
        pyautogui.hotkey(*keys)
        return f"Atajo de teclado ejecutado."

    def find_and_click(self, image_path, confidence=0.8):
        """
        Visión por computadora: Busca una imagen (ej. el icono de un botón) 
        en la pantalla actual y hace clic en el centro.
        """
        if not os.path.exists(image_path):
            self.logger.error(f"[DesktopAgent] No encuentro la imagen de referencia: {image_path}")
            return "Señor, no se ha proporcionado el archivo visual de referencia."

        self.logger.info(f"[DesktopAgent] Escaneando pantalla en busca de: {os.path.basename(image_path)}")
        try:
            # Escanea la pantalla usando OpenCV por debajo
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                # Movimiento fluido hacia el objetivo
                pyautogui.moveTo(location.x, location.y, duration=0.4, tween=pyautogui.easeInOutQuad)
                pyautogui.click()
                self.logger.info("[DesktopAgent] Clic efectuado con precisión.")
                return "Objetivo visual localizado y clic efectuado."
            else:
                self.logger.warning("[DesktopAgent] El objetivo visual no está en pantalla.")
                return "No he podido localizar ese elemento en la pantalla actual."
        except Exception as e:
            self.logger.error(f"[DesktopAgent] Fallo en el motor de visión: {e}")
            return f"Error procesando la imagen de pantalla: {e}"