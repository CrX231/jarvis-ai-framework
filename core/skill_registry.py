# core/skill_registry.py
import importlib

class BaseSkill:
    """Clase abstracta de la que heredarán todas las habilidades."""
    TRIGGERS = []
    
    def __init__(self, context=None):
        self.context = context
        
    def execute(self, command, attachment_path=None):
        raise NotImplementedError("Cada skill debe implementar su método execute.")

class SkillRegistry:
    def __init__(self, jarvis_context):
        self.context = jarvis_context
        self._registry = {}
        
    def register(self, module_name, class_name, triggers):
        """Registra una habilidad sin cargarla en memoria RAM."""
        for trigger in triggers:
            # Guardamos la ruta del módulo para importarlo solo si hace match
            self._registry[trigger] = {"module": module_name, "class": class_name, "instance": None}

    def process(self, command, attachment_path=None):
        """Busca el trigger, carga la clase (lazy) y ejecuta."""
        for trigger, data in self._registry.items():
            if trigger in command:
                if data["instance"] is None:
                    self.context.logger.info(f"[Registry] Cargando skill en RAM: {data['class']}")
                    # Lazy Import
                    module = importlib.import_module(data["module"])
                    skill_class = getattr(module, data["class"])
                    # Instanciamos inyectando el contexto global
                    data["instance"] = skill_class(self.context)
                    
                return data["instance"].execute(command, attachment_path)
        return None