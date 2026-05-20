import os
import re
from core.skill_registry import BaseSkill

class CoderSkill(BaseSkill):
    # Añadimos los triggers para expansión autónoma
    TRIGGERS = ["programa", "crea un script", "escribe código", "aprende a", "crea una habilidad"]

    def __init__(self, context):
        super().__init__(context)
        self.brain = context.brain
        self.task_queue = context.task_queue
        self.event_bus = context.event_bus
        self.logger = context.logger
        
        self.output_folder = "scripts_creados"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def execute(self, command, attachment_path=None):
        # 1. Modo Expansión Autónoma (Crear Skills)
        if "aprende a" in command or "crea una habilidad" in command:
            tema = command.replace("aprende a", "").replace("crea una habilidad para", "").replace("que", "").strip()
            if not tema:
                return "No me especificaste qué nueva habilidad deseas que aprenda."
                
            self.logger.info(f"Modo Expansión activado. Diseñando habilidad: {tema}")
            self.task_queue.add_task(self._learn_skill_async, tema)
            return f"Iniciando rediseño neuronal. Aprenderé a {tema} en segundo plano."
            
        # 2. Modo Scripts Normales
        else:
            tema = command.replace("programa", "").replace("crea un script", "").replace("escribe código", "").replace("que", "").strip()
            if not tema:
                return "No me dijiste qué necesitas que programe."

            self.logger.info(f"Encolando programación: {tema}")
            self.task_queue.add_task(self._write_code_async, tema)
            return "Iniciando la escritura de código en segundo plano, señor."

    def _learn_skill_async(self, tema):
        """Genera una nueva habilidad, la guarda en /skills y recarga el sistema."""
        prompt_skill = (
            f"Actúa como un Arquitecto de Software experto en IA. Crea una nueva habilidad en Python para un asistente virtual que haga lo siguiente: {tema}.\n"
            "REGLAS CRÍTICAS ESTRICTAS:\n"
            "1. La primera línea de tu respuesta DEBE ser obligatoriamente el nombre del archivo así: '# FILENAME: nombre_del_skill.py' (usa un nombre descriptivo terminado en _skill.py).\n"
            "2. La clase debe heredar de BaseSkill haciendo: from core.skill_registry import BaseSkill\n"
            "3. Define la variable de clase TRIGGERS = ['palabra_clave1', 'palabra_clave2']\n"
            "4. Debes implementar el método: def execute(self, command, attachment_path=None):\n"
            "5. Dentro de execute(), realiza la acción solicitada y retorna un string con la respuesta que Jarvis dirá por voz.\n"
            "6. Puedes importar librerías estándar de Python si las necesitas.\n"
            "7. Devuelve ÚNICAMENTE el código fuente, sin bloques markdown (no uses ```python), sin explicaciones."
        )

        try:
            response = self.brain.client.models.generate_content(
                model=self.brain.model_id,
                contents=prompt_skill
            )
            
            codigo_bruto = response.text.strip()
            
            # Limpieza en caso de que la IA insista con markdown
            if codigo_bruto.startswith("```"):
                codigo_bruto = re.sub(r"^```\w*\n", "", codigo_bruto)
                codigo_bruto = re.sub(r"```$", "", codigo_bruto).strip()

            # Extraemos el nombre del archivo de la primera línea
            lineas = codigo_bruto.split('\n')
            filename = "auto_generado_skill.py"
            if lineas[0].startswith("# FILENAME:"):
                filename = lineas[0].replace("# FILENAME:", "").strip()
                codigo_limpio = "\n".join(lineas[1:]).strip()
            else:
                codigo_limpio = codigo_bruto
                
            # Guardamos el archivo DIRECTO en la carpeta central de habilidades
            ruta_final = os.path.join("skills", filename)
            with open(ruta_final, 'w', encoding='utf-8') as f:
                f.write(codigo_limpio)
                
            # ¡LA MAGIA! Disparamos el evento para que Jarvis recargue sus habilidades en vivo
            self.event_bus.publish("RELOAD_SKILLS")
            self.event_bus.publish("SPEAK_REQUEST", {"text": f"He evolucionado exitosamente, señor. La habilidad para {tema} ha sido integrada a mis sistemas de forma permanente."})
            
        except Exception as e:
            self.logger.error(f"Fallo en motor de auto-expansión: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Hubo un fallo crítico al intentar escribir y asimilar la nueva habilidad."})

    def _write_code_async(self, tema):
        """Tarea pesada ejecutada en hilo secundario (Scripts genéricos)."""
        prompt_codigo = (
            f"Actúa como un Desarrollador Senior de Python. Crea un script funcional para lo siguiente: {tema}. "
            "Reglas CRÍTICAS: "
            "1. Devuelve ÚNICAMENTE el código fuente. "
            "2. NO uses bloques de formato markdown (no pongas ```python al inicio ni ``` al final). "
            "3. NO incluyas saludos, explicaciones, ni texto fuera del código. Todo debe estar documentado."
        )

        try:
            response = self.brain.client.models.generate_content(model=self.brain.model_id, contents=prompt_codigo)
            codigo_limpio = response.text.strip()
            if codigo_limpio.startswith("```"):
                codigo_limpio = re.sub(r"^```python\n|^```\w*\n", "", codigo_limpio)
                codigo_limpio = re.sub(r"```$", "", codigo_limpio).strip()

            ruta_final = os.path.join(self.output_folder, "script_automatico.py")
            with open(ruta_final, 'w', encoding='utf-8') as f:
                f.write(codigo_limpio)
                
            self.event_bus.publish("SPEAK_REQUEST", {"text": "He terminado de programar. El archivo ha sido guardado en su carpeta de scripts creados."})
        except Exception as e:
            self.logger.error(f"Fallo en motor de programación: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Hubo un fallo crítico al intentar escribir el código."})