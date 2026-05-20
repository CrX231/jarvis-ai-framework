import os
import requests
import re
from urllib.parse import quote
from core.skill_registry import BaseSkill

class ImageSkill(BaseSkill):
    TRIGGERS = ["genera una imagen", "crea una imagen", "dibuja"]

    def __init__(self, context):
        super().__init__(context)
        self.brain = context.brain
        self.task_queue = context.task_queue
        self.event_bus = context.event_bus
        self.logger = context.logger
        
        self.output_folder = "assets_generados"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def execute(self, command, attachment_path=None):
        raw_prompt = command.replace("genera una imagen de", "").replace("crea una imagen de", "").replace("dibuja", "").strip()
        
        if not raw_prompt:
            return "No especificaste qué quieres que dibuje."
            
        self.logger.info("Encolando generación visual...")
        # Encolamos la tarea para que no bloquee a Jarvis
        self.task_queue.add_task(self._generate_image_async, raw_prompt)
        return "Procesando generación visual en segundo plano. Esto tomará unos segundos."

    def _refine_prompt(self, raw_prompt):
        """Usa Gemini para convertir un prompt simple en uno técnico, fotorealista y SIN texto."""
        self.logger.info(f"[Visuales] Refinando prompt con IA...")
        
        # Consideramos las correcciones que has hecho anteriormente respecto a imágenes
        # Añadiendo la moto específica, sujetos musculosos, evitando el texto, usando las zapatillas específicas...
        refinement_instruction = (
            f"Actúa como un Ingeniero de Prompts experto para generadores de imágenes como Midjourney o DALL-E 3. "
            f"Tu tarea es reescribir el siguiente prompt simple en uno altamente detallado, fotorealista y profesional. "
            f"Prompt Simple: '{raw_prompt}'. "
            f"Reglas CRÍTICAS de reescritura: "
            f"1. Estilo: Fotorealista, 8k, Smart HDR, altamente detallado. "
            f"2. Fotografía: Incluye términos como perspectiva 24mm, iluminación de estudio, profundidad de campo nítida. "
            f"3. Restricción Absoluta (NEGATIVA): Asegura que la imagen NO TENGA TEXTO, tipografía, logotipos, marcas de agua ni firmas. El resultado debe ser una imagen limpia. "
            f"4. Consideraciones Especiales del Usuario: Asegura que si se pide una moto Yamaha R15, sea NEGRA. Si se pide modificar un sujeto, que sea 'un poco más musculoso' sin perder rasgos faciales. Usa 'Air Force One blancas' o 'black New York Yankees cap' si encaja con el contexto."
            f"5. Salida: Devuelve ÚNICAMENTE el prompt refinado en inglés (ya que los generadores de imágenes funcionan mejor en inglés), sin explicaciones adicionales."
        )

        try:
            response = self.brain.client.models.generate_content(
                model=self.brain.model_id,
                contents=refinement_instruction
            )
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Fallo al refinar prompt: {e}")
            return raw_prompt 

    def _generate_image_async(self, raw_prompt):
        """Descarga y guarda la imagen en un hilo secundario."""
        refined_prompt = self._refine_prompt(raw_prompt)
        self.logger.info(f"[Visuales] Prompt Final Refinado: '{refined_prompt[:100]}...'")
        
        try:
            safe_prompt = quote(refined_prompt)
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"
            
            response = requests.get(url)
            
            if response.status_code == 200:
                clean_filename = re.sub(r'[^\w\s-]', '', raw_prompt).strip().replace(' ', '_')
                filename = f"Asset_{clean_filename[:30]}.jpg"
                path = os.path.join(self.output_folder, filename)
                
                with open(path, 'wb') as f:
                    f.write(response.content)
                    
                os.startfile(path)
                self.event_bus.publish("SPEAK_REQUEST", {"text": "Asset visual generado con éxito, señor. He aplicado un filtro de refinamiento técnico para mejorar el realismo."})
            else:
                self.event_bus.publish("SPEAK_REQUEST", {"text": "Hubo un problema de conexión con el servidor de imágenes."})
                
        except Exception as e:
            self.logger.error(f"Fallo crítico al generar la imagen: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Ocurrió un error al intentar generar la imagen."})