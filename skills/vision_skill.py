import os
import time
import pyautogui
import re
from PIL import Image
from core.skill_registry import BaseSkill

class VisionSkill(BaseSkill):
    TRIGGERS = ["pantalla", "ve", "refactoriza"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        self.brain = context.brain
        self.task_queue = context.task_queue
        self.event_bus = context.event_bus
        
        self.output_folder = "capturas_pantalla"
        self.code_folder = "scripts_creados"
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        if not os.path.exists(self.code_folder):
            os.makedirs(self.code_folder)

    def capture_screen(self):
        self.logger.info("[Visión] Capturando pantalla...")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"captura_{timestamp}.png"
        path = os.path.join(self.output_folder, filename)
        
        time.sleep(0.5) 
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return path

    def execute(self, command, attachment_path=None):
        """Toma la solicitud y la envía a procesar en segundo plano."""
        self.event_bus.publish("SPEAK_REQUEST", {"text": "Revisando la pantalla. Un momento."})
        self.task_queue.add_task(self._process_vision_async, command)
        return None # Evitamos que el hilo principal responda inmediatamente

    def _process_vision_async(self, command):
        """Ejecuta la captura y el análisis neuronal en el hilo secundario."""
        image_path = self.capture_screen()
        
        if not image_path:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Señor, no pude acceder a la interfaz visual de la pantalla."})
            return
            
        try:
            img = Image.open(image_path)
            
            # 1. Modo: Análisis de Arquitectura de Código
            if "código" in command or "refactoriza" in command:
                self.logger.info("[Visión] Analizando arquitectura SOLID en pantalla...")
                prompt_solid = (
                    "Actúa como un Arquitecto de Software Senior. Analiza el código de la imagen adjunta. "
                    "1. Explica brevemente los errores (code smells) y cómo mejorar la arquitectura usando SOLID. "
                    "2. Escribe la versión completamente REFACTORIZADA y limpia del código. "
                    "REGLA ESTRICTA: El código refactorizado debe ir obligatoriamente dentro de un bloque de código markdown. "
                    "No omitas el código, escríbelo completo."
                )
                
                respuesta = self.brain.think(prompt_solid, image=img)
                
                # Extracción segura usando regex
                patron = r"\x60\x60\x60(?:python|java|javascript|cpp|csharp)?\n(.*?)\n\x60\x60\x60"
                codigo_match = re.search(patron, respuesta, re.DOTALL)
                
                if codigo_match:
                    codigo_limpio = codigo_match.group(1).strip()
                    ruta_final = os.path.join(self.code_folder, "codigo_refactorizado.py")
                    
                    with open(ruta_final, 'w', encoding='utf-8') as f:
                        f.write(codigo_limpio)
                        
                    os.startfile(ruta_final)
                    self.event_bus.publish("SPEAK_REQUEST", {"text": "He revisado el código. Te he dado mis recomendaciones y he creado el archivo con la refactorización."})
                else:
                    self.logger.info(f"Análisis sin código exportable: {respuesta}")
                    self.event_bus.publish("SPEAK_REQUEST", {"text": "Revisé el código, pero no detecté una estructura clara para exportar a un archivo."})
            
            # 2. Modo: Visión General ("¿qué ves en la pantalla?")
            else:
                respuesta = self.brain.think(command, image=img)
                self.event_bus.publish("SPEAK_REQUEST", {"text": respuesta})
                
        except Exception as e:
            self.logger.error(f"Error en procesamiento de visión: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Hubo un error en mi córtex visual al intentar procesar la captura."})