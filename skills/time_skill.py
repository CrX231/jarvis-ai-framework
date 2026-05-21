import datetime

class TimeSkill:
    def get_time(self):
        ahora = datetime.datetime.now()
        
        # Obtenemos la hora en formato de 12 horas sin el cero a la izquierda
        hora = ahora.strftime("%I:%M").lstrip('0')
        
        # Determinamos si es mañana, tarde o noche para que suene natural
        if ahora.hour < 12:
            periodo = "de la mañana"
        elif ahora.hour < 19:
            periodo = "de la tarde"
        else:
            periodo = "de la noche"
            
        return f"Son las {hora} {periodo}."

if __name__ == "__main__":
    # Prueba aislada
    skill = TimeSkill()
    print(skill.get_time())