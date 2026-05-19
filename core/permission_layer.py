from enum import Enum

class PermissionLevel(Enum):
    SAFE = 1        # Operaciones de lectura (hora, clima, buscar en web)
    CONFIRM = 2     # Modificaciones menores (escribir archivos, enviar correos)
    DANGEROUS = 3   # Operaciones críticas (borrar notas, modificar sistema)

class PermissionLayer:
    def __init__(self):
        # Diccionario de palabras clave que Jarvis entenderá como un "Sí"
        self.auth_keywords = ["sí", "si", "autoriza", "autorizado", "procede", "adelante", "hazlo", "confirmo", "ok"]
        # Palabras de cancelación
        self.deny_keywords = ["no", "cancela", "aborta", "detén", "espera"]

    def requires_confirmation(self, level):
        """Devuelve True si la acción necesita que el usuario confirme en voz alta."""
        return level in [PermissionLevel.CONFIRM, PermissionLevel.DANGEROUS]

    def is_authorized(self, user_response):
        """Evalúa el texto que el usuario dijo para determinar si dio luz verde."""
        if not user_response:
            return False
            
        respuesta = user_response.lower()
        
        # Si detecta una palabra de cancelación, aborta inmediatamente
        for word in self.deny_keywords:
            if word in respuesta:
                return False
                
        # Si detecta autorización, da luz verde
        for word in self.auth_keywords:
            if word in respuesta:
                return True
                
        # Ante la duda (respuestas ambiguas), el protocolo de seguridad deniega el acceso
        return False