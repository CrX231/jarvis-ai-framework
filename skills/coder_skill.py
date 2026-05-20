import os
import re
from core.skill_registry import BaseSkill

class CoderSkill(BaseSkill):
    TRIGGERS = ["programa", "crea un script", "escribe código"]

    def __init__(self, context):
        super().__init__(context)
        self.brain = context.brain
        self.task_queue = context.task_queue
        self.event_bus = context.event_bus
        self.logger = context.logger
        
        # Carpeta donde Jarvis dejará el código que programe
        self.output_folder = "scripts_creados"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def execute(self, command, attachment_path=None):
        tema = command.replace("programa", "").replace("crea un script", "").replace("escribe código", "").replace("que", "").strip()
        
        if not tema:
            return "No me dijiste qué necesitas que programe."

        self.logger.info(f"Encolando programación autónoma para: {tema}")
        # Encolamos la tarea pesada
        self.task_queue.add_task(self._write_code_async, tema)
        return "Iniciando la escritura de código en segundo plano, señor."

    def _write_code_async(self, tema):
        """Tarea pesada ejecutada en hilo secundario."""
        prompt_codigo = (
            f"Actúa como un Desarrollador Senior de Python. Crea un script funcional para lo siguiente: {tema}. "
            "Reglas CRÍTICAS: "
            "1. Devuelve ÚNICAMENTE el código fuente. "
            "2. NO uses bloques de formato markdown (no pongas ```python al inicio ni ``` al final). "
            "3. NO incluyas saludos, explicaciones, ni texto fuera del código. Todo debe estar documentado con comentarios de Python (#)."
        )

        try:
            response = self.brain.client.models.generate_content(
                model=self.brain.model_id,
                contents=prompt_codigo
            )
            
            codigo_limpio = response.text.strip()
            
            if codigo_limpio.startswith("```"):
                codigo_limpio = re.sub(r"^```python\n|^```\w*\n", "", codigo_limpio)
                codigo_limpio = re.sub(r"```$", "", codigo_limpio).strip()

            nombre_archivo = f"script_automatico.py"
            ruta_final = os.path.join(self.output_folder, nombre_archivo)
            
            with open(ruta_final, 'w', encoding='utf-8') as f:
                f.write(codigo_limpio)
                
            # Avisamos por voz cuando termina
            self.event_bus.publish("SPEAK_REQUEST", {"text": "He terminado de programar. El archivo ha sido guardado en su carpeta de scripts creados."})
            
        except Exception as e:
            self.logger.error(f"Fallo en motor de programación: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Hubo un fallo crítico al intentar escribir el código."})