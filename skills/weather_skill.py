import requests
from core.skill_registry import BaseSkill

class WeatherSkill(BaseSkill):
    TRIGGERS = ["clima", "temperatura"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger

    def execute(self, command, attachment_path=None):
        ciudad = "José Leonardo Ortiz"
        
        # Si el usuario especifica otra ciudad (ej: "clima en Madrid")
        if " en " in command:
            partes = command.split(" en ")
            if len(partes) > 1:
                ciudad = partes[-1].strip()

        try:
            self.logger.info(f"Consultando clima satelital para: {ciudad}")
            # Hacemos la consulta a wttr.in pidiendo solo temperatura (%t), condición (%C) y en español (lang=es)
            url = f"https://wttr.in/{ciudad}?format=%t+%C&lang=es"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                # Limpiamos un poco el texto que llega
                clima_texto = response.text.strip().replace("+", "")
                return f"El clima en {ciudad} es de {clima_texto}."
            else:
                return "No pude obtener la información del clima en este momento."
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Fallo de red al conectar con servicios meteorológicos: {e}")
            return "Hay un problema con la conexión de red para consultar el clima."