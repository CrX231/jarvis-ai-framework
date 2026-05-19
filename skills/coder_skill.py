import os
import re

class CoderSkill:
    def __init__(self):
        # Carpeta donde Jarvis dejará el código que programe
        self.output_folder = "scripts_creados"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def write_code(self, command, brain):
        # Limpiamos el comando para extraer solo lo que quieres que programe
        tema = command.replace("programa", "").replace("crea un script", "").replace("escribe código", "").replace("que", "").strip()
        
        if not tema:
            return "No me dijiste qué necesitas que programe."

        print(f"[Programación] Escribiendo código para: {tema}...")

        # Prompt estricto para extraer solo código crudo
        prompt_codigo = (
            f"Actúa como un Desarrollador Senior de Python. Crea un script funcional para lo siguiente: {tema}. "
            "Reglas CRÍTICAS: "
            "1. Devuelve ÚNICAMENTE el código fuente. "
            "2. NO uses bloques de formato markdown (no pongas ```python al inicio ni ``` al final). "
            "3. NO incluyas saludos, explicaciones, ni texto fuera del código. Todo debe estar documentado con comentarios de Python (#)."
        )

        try:
            # Usamos models.generate_content para no ensuciar el historial de tu chat hablado
            response = brain.client.models.generate_content(
                model=brain.model_id,
                contents=prompt_codigo
            )
            
            codigo_limpio = response.text.strip()
            
            # Limpieza de seguridad por si la IA insiste en poner markdown
            if codigo_limpio.startswith("```"):
                codigo_limpio = re.sub(r"^```python\n|^```\w*\n", "", codigo_limpio)
                codigo_limpio = re.sub(r"```$", "", codigo_limpio).strip()

            # Guardamos el archivo
            nombre_archivo = f"script_automatico.py"
            ruta_final = os.path.join(self.output_folder, nombre_archivo)
            
            with open(ruta_final, 'w', encoding='utf-8') as f:
                f.write(codigo_limpio)
                
            return "He terminado de programar. El archivo ha sido guardado en tu carpeta de scripts creados."
            
        except Exception as e:
            return f"Hubo un fallo crítico en mi motor de programación: {e}"