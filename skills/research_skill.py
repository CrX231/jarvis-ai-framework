from core.web_agent import WebAgent

class ResearchSkill:
    def __init__(self, logger, brain):
        self.logger = logger
        self.brain = brain
        self.web_agent = WebAgent(logger)

    def investigate(self, topic):
        """Usa el Agente Web para extraer datos y luego el Cerebro para resumirlos."""
        self.logger.info(f"Iniciando protocolo de investigación sobre: {topic}")
        
        # 1. El Agente va a internet y trae el texto crudo
        raw_data = self.web_agent.search_and_extract(topic)
        
        if "Error al intentar" in raw_data or "No se encontraron" in raw_data:
            return "Señor, mis protocolos de navegación encontraron un bloqueo al intentar acceder a esa información."
            
        # 2. Le pasamos el texto crudo de la web a Gemini para que lo entienda y resuma
        prompt_analisis = (
            f"El usuario solicitó investigar sobre: '{topic}'. "
            f"Mi Agente Web extrajo este texto en bruto de internet:\n\n{raw_data}\n\n"
            f"Analiza la información y dame un resumen claro, profesional y directo al punto "
            f"que responda a la solicitud original. No menciones el texto en bruto, solo da la respuesta."
        )
        
        respuesta_procesada = self.brain.think(prompt_analisis)
        return respuesta_procesada