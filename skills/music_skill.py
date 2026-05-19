import pywhatkit

class MusicSkill:
    def play_youtube(self, command):
        # Limpiamos el comando para dejar únicamente el nombre de la canción/video
        cancion = command.replace("reproduce", "").replace("pon", "").replace("en youtube", "").strip()
        
        if cancion:
            try:
                # pywhatkit hace la magia: busca y reproduce el primer resultado automáticamente
                pywhatkit.playonyt(cancion)
                return f"Reproduciendo {cancion} en YouTube."
            except Exception as e:
                return "Hubo un problema de red al intentar reproducir el video."
        
        return "No escuché bien qué quieres que reproduzca."