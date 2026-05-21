import os
import time
import pyautogui
import re
from PIL import Image

class VisionSkill:
    def __init__(self):
        self.output_folder = "capturas_pantalla"
        self.code_folder = "scripts_creados"
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        if not os.path.exists(self.code_folder):
            os.makedirs(self.code_folder)

    def capture_screen(self):
        print("[Visión] Capturando pantalla...")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"captura_{timestamp}.png"
        path = os.path.join(self.output_folder, filename)
        
        time.sleep(0.5) 
        
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return path

    def analyze_code_on_screen(self, command, brain):
        image_path = self.capture_screen()
        
        if not image_path:
            return "No pude ver la pantalla."
            
        print("[Visión] Analizando arquitectura de código en pantalla...")
        
        try:
            img = Image.open(image_path)
            
            prompt_solid = (
                "Actúa como un Arquitecto de Software Senior. Analiza el código de la imagen adjunta. "
                "1. Explica brevemente los errores (code smells) y cómo mejorar la arquitectura usando SOLID. "
                "2. Escribe la versión completamente REFACTORIZADA y limpia del código. "
                "REGLA ESTRICTA: El código refactorizado debe ir obligatoriamente dentro de un bloque de código markdown. "
                "No omitas el código, escríbelo completo."
            )
            
            respuesta = brain.think(prompt_solid, image=img)
            
            # --- SOLUCIÓN DEFINITIVA ---
            # Usamos \x60 que es el código hexadecimal para las comillas invertidas.
            # Así evitamos que la interfaz del chat o el portapapeles lo rompan.
            patron = r"\x60\x60\x60(?:python)?\n(.*?)\n\x60\x60\x60"
            codigo_match = re.search(patron, respuesta, re.DOTALL)
            
            if codigo_match:
                codigo_limpio = codigo_match.group(1).strip()
                
                ruta_final = os.path.join(self.code_folder, "codigo_refactorizado.py")
                with open(ruta_final, 'w', encoding='utf-8') as f:
                    f.write(codigo_limpio)
                
                os.startfile(ruta_final)
                
                return "He revisado el código. Te he dado mis recomendaciones y he creado el archivo 'codigo_refactorizado.py'."
            else:
                return f"Revisé el código, pero no pude generar un archivo limpio. Aquí está mi análisis:\n\n{respuesta}"
            
        except Exception as e:
            return f"Hubo un error al procesar la imagen para el análisis de código: {e}"