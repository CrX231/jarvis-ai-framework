import time

class ContextManager:
    def __init__(self, logger):
        self.logger = logger
        self.recent_commands = []
        self.recent_files = []
        self.active_topic = None
        self.max_history = 5  # Cuántas acciones recuerda a corto plazo

    def add_command(self, command):
        """Registra lo último que el usuario pidió."""
        self.recent_commands.append({"time": time.time(), "command": command})
        if len(self.recent_commands) > self.max_history:
            self.recent_commands.pop(0)

    def add_file(self, filepath):
        """Registra el último archivo creado o analizado."""
        if filepath not in self.recent_files:
            self.recent_files.append(filepath)
            if len(self.recent_files) > self.max_history:
                self.recent_files.pop(0)
        self.logger.info(f"Contexto actualizado: Rastreando archivo -> {filepath}")

    def set_topic(self, topic):
        """Define de qué trata la sesión de trabajo actual."""
        self.active_topic = topic
        self.logger.info(f"Foco de contexto cambiado a: {topic}")

    def get_system_context(self):
        """Genera un bloque de texto invisible con el estado actual para que la IA lo lea."""
        if not self.recent_files and not self.active_topic:
            return "" # Si no hay contexto relevante, no inyecta nada
            
        context = "\n[INFO DE SISTEMA INVISIBLE PARA EL USUARIO - CONTEXTO ACTUAL]\n"
        if self.active_topic:
            context += f"- Tema actual de la sesión: {self.active_topic}\n"
        if self.recent_files:
            context += "- Últimos archivos manipulados/creados en el sistema:\n"
            for f in self.recent_files[-3:]:
                context += f"  * {f}\n"
        context += "[FIN DEL CONTEXTO]\n\n"
        return context