import json
import time

class ReasoningEngine:
    def __init__(self, logger, brain, event_bus):
        self.logger = logger
        self.brain = brain
        self.event_bus = event_bus

    def _break_down_goal(self, goal):
        """Usa el LLM para fragmentar un objetivo en comandos ejecutables."""
        self.logger.info(f"Desglosando objetivo complejo: {goal}")
        prompt = f"""
        Actúa como el planificador táctico de un sistema informático automatizado. 
        El objetivo complejo del usuario es: "{goal}"
        
        Desglosa este objetivo en una secuencia lógica de comandos simples que el enrutador pueda procesar.
        Los comandos válidos que el sistema entiende empiezan con:
        - "busca [tema]"
        - "crea un documento de word sobre [tema]"
        - "crea un excel sobre [tema]"
        - "crea una presentación sobre [tema]"
        - "genera una imagen de [descripción]"
        - "escribe código para [tarea]"
        - "guarda una nota que diga [texto]"
        
        Responde ÚNICAMENTE con una lista JSON válida de strings (comandos), sin texto adicional ni formato markdown.
        Ejemplo: ["busca implementaciones de sistemas Kanban", "crea un documento de word sobre sistemas Kanban", "guarda una nota que diga revisar el documento de Kanban"]
        """
        try:
            # Pedimos el plan y limpiamos posibles marcas de formato markdown
            response = self.brain.think(prompt).replace("```json", "").replace("```", "").strip()
            plan = json.loads(response)
            self.logger.info(f"Plan de acción trazado: {plan}")
            return plan
        except Exception as e:
            self.logger.error(f"Error al razonar el plan: {e}. Respuesta cruda: {response}")
            return []
            
    def execute_plan(self, goal, router_callback):
        """Ejecuta los pasos del plan de forma secuencial en segundo plano."""
        self.event_bus.publish("SPEAK_REQUEST", {"text": "Analizando la solicitud y trazando un plan de acción multisecuencial."})
        plan = self._break_down_goal(goal)
        
        if not plan:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Señor, no pude fragmentar el objetivo en tareas ejecutables por el momento."})
            return
            
        self.event_bus.publish("SPEAK_REQUEST", {"text": f"Plan establecido. Ejecutando {len(plan)} fases operativas."})
        
        for index, step in enumerate(plan):
            self.logger.info(f"Ejecutando fase {index + 1}/{len(plan)}: {step}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": f"Fase {index + 1}: Ejecutando protocolo."})
            
            try:
                # Inyectamos el comando generado por la IA de vuelta al enrutador maestro
                respuesta_paso = router_callback(step)
                if respuesta_paso:
                    self.logger.info(f"Resultado de fase {index + 1}: {respuesta_paso}")
            except Exception as e:
                self.logger.error(f"Error en fase {index + 1}: {e}")
                
            # Pausa táctica entre comandos para dar respiro al sistema de archivos y memoria
            time.sleep(3)
            
        self.event_bus.publish("SPEAK_REQUEST", {"text": "Plan de acción completado en su totalidad, señor. Misión cumplida."})