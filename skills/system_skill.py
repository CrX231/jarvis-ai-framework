import os
from core.skill_registry import BaseSkill

class SystemSkill(BaseSkill):
    TRIGGERS = ["abre", "ejecuta"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        self.programs = {
            "bloc de notas": "notepad",
            "calculadora": "calc",
            "visual studio": "code",
            "spotify": "spotify",
            "archivos": "explorer",
            "explorador": "explorer",
            "panel de control": "control",
            "cmd": "cmd"
        }

    def execute(self, command, attachment_path=None):
        for name, exe in self.programs.items():
            if name in command:
                try:
                    os.system(f"start {exe}")
                    return f"Iniciando {name}."
                except Exception as e:
                    self.logger.error(f"Fallo al abrir programa local {name}: {e}")
                    return f"Hubo un error al intentar abrir {name}."
        
        # Retornamos None explícitamente si el programa no estaba en la lista.
        # Esto permite que el SkillRegistry siga buscando otro skill que coincida
        # (por ejemplo, si dijiste "abre youtube", lo tomará BrowserSkill).
        return None