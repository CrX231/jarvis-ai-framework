from core.skill_registry import BaseSkill
from core.desktop_agent import DesktopAgent

class DesktopSkill(BaseSkill):
    TRIGGERS = ["escribe ", "presiona enter", "copia esto", "pega esto", "selecciona todo", "minimiza todo", "cierra esta ventana"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        self.agent = DesktopAgent(self.logger)

    def execute(self, command, attachment_path=None):
        """Traduce lenguaje natural en acciones físicas de teclado/ratón."""
        
        # Ignoramos si es una instrucción de programación
        if "código" in command:
            return None 

        self.logger.info("Activando actuadores físicos de teclado/ratón.")

        # --- ESCRITURA FÍSICA ---
        if "escribe " in command:
            texto_a_escribir = command.split("escribe", 1)[1].strip()
            texto_a_escribir = texto_a_escribir.replace('"', '').replace("'", "")
            return self.agent.type_text(texto_a_escribir)
            
        # --- ATAJOS COMUNES ---
        elif "presiona enter" in command or "dale enter" in command:
            return self.agent.press_shortcut("enter")
            
        elif "copia esto" in command or "control c" in command:
            return self.agent.press_shortcut("ctrl+c")
            
        elif "pega esto" in command or "control v" in command:
            return self.agent.press_shortcut("ctrl+v")
        
        elif "selecciona todo" in command or "control a" in command:
            return self.agent.press_shortcut("ctrl+a")
            
        elif "minimiza todo" in command or "muestra el escritorio" in command:
            return self.agent.press_shortcut("win+d")
            
        elif "cierra esta ventana" in command or "alt f4" in command:
            return self.agent.press_shortcut("alt+f4")
            
        else:
            return "Comando físico no reconocido, señor."