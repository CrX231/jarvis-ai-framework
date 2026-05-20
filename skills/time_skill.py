import datetime
from core.skill_registry import BaseSkill

class TimeSkill(BaseSkill):
    TRIGGERS = ["hora", "qué hora", "dime la hora"]

    def __init__(self, context):
        super().__init__(context)

    def execute(self, command, attachment_path=None):
        ahora = datetime.datetime.now()
        hora_str = ahora.strftime('%I:%M')
        
        # Determinamos si es mañana, tarde o noche para que suene natural
        if ahora.hour < 12:
            periodo = "de la mañana"
        elif ahora.hour < 19:
            periodo = "de la tarde"
        else:
            periodo = "de la noche"
            
        return f"Son las {hora_str} {periodo}."