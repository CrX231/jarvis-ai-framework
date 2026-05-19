import threading
import time

class WorkflowEngine:
    def __init__(self, logger, event_bus):
        self.logger = logger
        self.event_bus = event_bus
        self.current_workflow = None
        self.workflow_state = None  # Estados: None, "RUNNING", "WAITING_USER"
        self.pending_steps = []
        self.context_data = {}      # Memoria compartida entre los pasos del flujo

    def load_and_start(self, name, steps):
        """Carga una secuencia de pasos y la inicia en segundo plano."""
        self.current_workflow = name
        self.pending_steps = steps
        self.workflow_state = "RUNNING"
        self.context_data = {}
        
        self.logger.info(f"Iniciando flujo de trabajo: {name}")
        self.event_bus.publish("SPEAK_REQUEST", {"text": f"Iniciando flujo de trabajo estructurado: {name}."})
        
        # Arrancamos el motor en un hilo secundario para no bloquear a Jarvis
        threading.Thread(target=self._execute_next, daemon=True).start()

    def _execute_next(self):
        """Ejecuta el siguiente paso del flujo o se pausa si requiere validación."""
        if not self.pending_steps:
            self.workflow_state = None
            self.event_bus.publish("SPEAK_REQUEST", {"text": f"Flujo de trabajo '{self.current_workflow}' completado en su totalidad."})
            self.current_workflow = None
            return

        step = self.pending_steps.pop(0)
        
        if step.get("type") == "action":
            self.logger.info(f"Ejecutando paso del flujo: {step['name']}")
            try:
                # Ejecutamos la función inyectándole el contexto del flujo
                result = step["func"](self.context_data)
                self.context_data[step["name"]] = result
                
                # Pausa táctica entre acciones pesadas
                time.sleep(2)
                # Llamada recursiva para el siguiente paso
                self._execute_next()
                
            except Exception as e:
                self.logger.error(f"Falla crítica en flujo {self.current_workflow}: {e}")
                self.event_bus.publish("SPEAK_REQUEST", {"text": f"Señor, el flujo de trabajo ha colapsado en la fase de {step['name']}."})
                self.workflow_state = None
                
        elif step.get("type") == "wait_validation":
            self.logger.info(f"Flujo pausado. Esperando validación humana para: {step['name']}")
            self.workflow_state = "WAITING_USER"
            # Jarvis te habla y se queda esperando tu respuesta en el main
            self.event_bus.publish("SPEAK_REQUEST", {"text": step["prompt"]})

    def resume_workflow(self, is_approved):
        """Reanuda o cancela un flujo pausado basándose en la respuesta de Carlos."""
        if self.workflow_state != "WAITING_USER":
            return "No hay ningún flujo de trabajo esperando validación en este momento."
            
        if is_approved:
            self.workflow_state = "RUNNING"
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Validación recibida. Retomando la ejecución del flujo."})
            threading.Thread(target=self._execute_next, daemon=True).start()
            return "Flujo reanudado con éxito."
        else:
            self.workflow_state = None
            self.pending_steps = []
            self.current_workflow = None
            self.logger.info("Flujo de trabajo abortado por el usuario.")
            return "Flujo de trabajo cancelado. Sistemas en espera."