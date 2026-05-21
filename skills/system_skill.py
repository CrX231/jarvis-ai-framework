import os

class SystemSkill:
    def __init__(self):
        # Diccionario que conecta lo que dices con el comando interno de Windows
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

    def open_program(self, command):
        for name, exe in self.programs.items():
            if name in command:
                try:
                    # 'start' es el comando de Windows para abrir procesos independientes
                    os.system(f"start {exe}")
                    return f"Iniciando {name}."
                except Exception:
                    return f"Hubo un error al intentar abrir {name}."
        
        # Si no encuentra el programa en la lista, retorna None para pasar al siguiente nivel
        return None