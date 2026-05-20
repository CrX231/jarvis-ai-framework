from core.web_agent import WebAgent
from core.skill_registry import BaseSkill

class ResearchSkill(BaseSkill):
    TRIGGERS = ["investiga sobre", "averigua sobre"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        self.brain = context.brain
        self.task_queue = context.task_queue
        self.event_bus = context.event_bus
        self.web_agent = WebAgent(self.logger)

    def execute(self, command, attachment_path=None):
        """Prepara el tema y lanza el agente a internet en segundo plano."""
        topic = command.replace("investiga sobre", "").replace("averigua sobre", "").strip()
        
        if not topic:
            return "Por favor, dime qué tema deseas que investigue, señor."

        self.logger.info(f"Encolando investigación profunda: {topic}")
        # Lo enviamos al hilo secundario para no congelar a Jarvis
        self.task_queue.add_task(self._investigate_async, topic)
        return f"Iniciando protocolos de rastreo web e investigación sobre {topic}, señor. Le informaré los hallazgos en breve."

    def _investigate_async(self, topic):
        """Usa el Agente Web para extraer datos y luego el Cerebro para resumirlos."""
        self.logger.info(f"Iniciando protocolo de investigación sobre: {topic}")
        
        raw_data = self.web_agent.search_and_extract(topic)
        
        if "Error al intentar" in raw_data or "No se encontraron" in raw_data:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Señor, mis protocolos de navegación encontraron un bloqueo al intentar acceder a esa información."})
            return
            
        prompt_analisis = (
            f"El usuario solicitó investigar sobre: '{topic}'. "
            f"Mi Agente Web extrajo este texto en bruto de internet:\n\n{raw_data}\n\n"
            f"Analiza la información y dame un resumen claro, profesional y directo al punto "
            f"que responda a la solicitud original. No menciones el texto en bruto, solo da la respuesta."
        )
        
        try:
            respuesta_procesada = self.brain.think(prompt_analisis)
            self.event_bus.publish("SPEAK_REQUEST", {"text": respuesta_procesada})
        except Exception as e:
            self.logger.error(f"Fallo al procesar resumen de investigación: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Hubo un fallo en mi red neuronal al intentar procesar los datos web."})