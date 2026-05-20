import time


class ContextManager:
    def __init__(self, logger, episodic_memory=None):
        self.logger           = logger
        self.episodic_memory  = episodic_memory   # Inyección de dependencia opcional
        self.recent_commands  = []
        self.recent_files     = []
        self.active_topic     = None
        self.current_topic    = None              # Alias público usado por EpisodicMemory
        self.max_history      = 5

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
        self.active_topic  = topic
        self.current_topic = topic   # Mantiene ambos en sync
        self.logger.info(f"Foco de contexto cambiado a: {topic}")

    def get_system_context(self) -> str:
        """
        Genera un bloque de texto con el estado actual para que el Brain lo lea.
        Combina memoria episódica (largo plazo) + contexto de sesión (corto plazo).
        """
        context = ""

        # ── Capa 1: Memoria episódica (largo plazo) ──────────────────────────
        if self.episodic_memory:
            resumen_episodico = self.episodic_memory.get_context_summary(max_events=5)
            if resumen_episodico:
                context += resumen_episodico + "\n\n"

        # ── Capa 2: Contexto de sesión actual (corto plazo) ──────────────────
        if not self.recent_files and not self.active_topic:
            return context   # Solo retorna el episódico si no hay contexto de sesión

        context += "\n[INFO DE SISTEMA INVISIBLE PARA EL USUARIO - CONTEXTO ACTUAL]\n"

        if self.active_topic:
            context += f"- Tema actual de la sesión: {self.active_topic}\n"

        if self.recent_files:
            context += "- Últimos archivos manipulados/creados en el sistema:\n"
            for f in self.recent_files[-3:]:
                context += f"  * {f}\n"

        context += "[FIN DEL CONTEXTO]\n\n"
        return context