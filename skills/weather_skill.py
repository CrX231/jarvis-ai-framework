import requests

class WeatherSkill:
    def get_weather(self, command):
        # Ciudad por defecto para consultas rápidas
        ciudad = "Chiclayo"
        
        # Si el usuario especifica otra ciudad (ej: "clima en Madrid")
        if " en " in command:
            partes = command.split(" en ")
            if len(partes) > 1:
                ciudad = partes[-1].strip()

        try:
            # Hacemos la consulta a wttr.in pidiendo solo temperatura (%t), condición (%C) y en español (lang=es)
            url = f"https://wttr.in/{ciudad}?format=%t+%C&lang=es"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                # Limpiamos un poco el texto que llega (a veces trae un símbolo + por defecto)
                clima_texto = response.text.strip().replace("+", "")
                return f"El clima en {ciudad} es de {clima_texto}."
            else:
                return "No pude obtener la información del clima en este momento."
                
        except requests.exceptions.RequestException:
            return "Hay un problema con la conexión de red para consultar el clima."