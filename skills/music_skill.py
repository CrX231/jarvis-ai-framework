import pywhatkit
from core.skill_registry import BaseSkill

class MusicSkill(BaseSkill):
    TRIGGERS = ["reproduce", "pon"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger

    def execute(self, command, attachment_path=None):
        # Limpiamos el comando para dejar únicamente el nombre de la canción/video
        cancion = command.replace("reproduce", "").replace("pon", "").replace("en youtube", "").strip()
        
        if cancion:
            try:
                self.logger.info(f"Delegando reproducción a pywhatkit: {cancion}")
                # pywhatkit hace la magia: busca y reproduce el primer resultado automáticamente
                pywhatkit.playonyt(cancion)
                return f"Reproduciendo {cancion} en YouTube."
            except Exception as e:
                self.logger.error(f"Fallo en la skill de YouTube: {e}")
                return "Hubo un problema de red al intentar reproducir el video."
        
        return "No escuché bien qué quieres que reproduzca."