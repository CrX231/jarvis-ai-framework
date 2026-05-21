from core.desktop_agent import DesktopAgent

class DesktopSkill:
    def __init__(self, logger):
        self.logger = logger
        self.agent = DesktopAgent(logger)

    def process_physical_command(self, comando):
        """Traduce lenguaje natural en acciones físicas de teclado/ratón."""
        
        # --- ESCRITURA FÍSICA ---
        if "escribe " in comando and "código" not in comando:
            # Extraemos lo que quieres que escriba
            texto_a_escribir = comando.split("escribe", 1)[1].strip()
            # Quitamos comillas si las dictaste
            texto_a_escribir = texto_a_escribir.replace('"', '').replace("'", "")
            return self.agent.type_text(texto_a_escribir)
            
        # --- ATAJOS COMUNES ---
        elif "presiona enter" in comando or "dale enter" in comando:
            return self.agent.press_shortcut("enter")
            
        elif "copia esto" in comando or "control c" in comando:
            return self.agent.press_shortcut("ctrl+c")
            
        elif "pega esto" in comando or "control v" in comando:
            return self.agent.press_shortcut("ctrl+v")
            
        elif "selecciona todo" in comando or "control e" in comando:
            return self.agent.press_shortcut("ctrl+e")
            
        elif "minimiza todo" in comando or "muestra el escritorio" in comando:
            # En Windows, Win+D minimiza todo
            return self.agent.press_shortcut("win+d")
            
        elif "cierra esta ventana" in comando or "alt f4" in comando:
            return self.agent.press_shortcut("alt+f4")
            
        else:
            return "Comando físico no reconocido, señor."
        
       