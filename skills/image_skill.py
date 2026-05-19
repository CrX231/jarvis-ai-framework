import os
import requests
import re
from urllib.parse import quote

class ImageSkill:
    def __init__(self):
        self.output_folder = "assets_generados"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def _refine_prompt(self, raw_prompt, brain):
        """Usa Gemini para convertir un prompt simple en uno técnico, fotorealista y SIN texto."""
        print(f"[Visuales] Refinando prompt con IA...")
        
        # Super-prompt de ingeniería para Gemini
        refinement_instruction = (
            f"Actúa como un Ingeniero de Prompts experto para generadores de imágenes como Midjourney o DALL-E 3. "
            f"Tu tarea es reescribir el siguiente prompt simple en uno altamente detallado, fotorealista y profesional. "
            f"Prompt Simple: '{raw_prompt}'. "
            f"Reglas CRÍTICAS de reescritura: "
            f"1. Estilo: Fotorealista, 8k, Smart HDR, altamente detallado. "
            f"2. Fotografía: Incluye términos como perspectiva 24mm, iluminación de estudio, profundidad de campo nítida. "
            f"3. Restricción Absoluta (NEGATIVA): Asegura que la imagen NO TENGA TEXTO, tipografía, logotipos, marcas de agua ni firmas. El resultado debe ser una imagen limpia. "
            f"4. Salida: Devuelve ÚNICAMENTE el prompt refinado en inglés (ya que los generadores de imágenes funcionan mejor en inglés), sin explicaciones adicionales."
        )

        try:
            # Usamos generate_content directamente para una petición limpia y rápida
            response = brain.client.models.generate_content(
                model=brain.model_id,
                contents=refinement_instruction
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Error] Fallo al refinar prompt: {e}")
            return raw_prompt # Si falla, devolvemos el original para no detener el proceso

    def generate_image(self, command, brain):
        # Limpiamos la orden inicial
        raw_prompt = command.replace("genera una imagen de", "").replace("crea una imagen de", "").replace("dibuja", "").strip()
        
        if not raw_prompt:
            return "No especificaste qué quieres que dibuje."
            
        # --- MOTOR DE REFINAMIENTO ---
        # Gemini reescribe el prompt para que sea profesional y sin texto
        refined_prompt = self._refine_prompt(raw_prompt, brain)
        print(f"[Visuales] Prompt Final Refinado: '{refined_prompt[:100]}...'")
        
        try:
            # Formateamos la URL con el prompt ya refinado (y en inglés)
            safe_prompt = quote(refined_prompt)
            # Pedimos máxima resolución cuadrada
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"
            
            # Descargamos la imagen de Pollinations
            response = requests.get(url)
            
            if response.status_code == 200:
                # Nombramos el archivo (usando el prompt original en español para que entiendas qué es)
                clean_filename = re.sub(r'[^\w\s-]', '', raw_prompt).strip().replace(' ', '_')
                filename = f"Asset_{clean_filename[:30]}.jpg"
                path = os.path.join(self.output_folder, filename)
                
                with open(path, 'wb') as f:
                    f.write(response.content)
                    
                # Saltamos la imagen a pantalla automáticamente
                os.startfile(path)
                
                return f"Asset visual generado con éxito. He aplicado un filtro de refinamiento técnico para mejorar el realismo y asegurar que no haya texto no deseado."
            else:
                return "Hubo un problema de conexión con el servidor de imágenes."
                
        except Exception as e:
            return f"Fallo crítico al generar la imagen: {e}"