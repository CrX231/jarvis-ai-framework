import os
import importlib
import inspect

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
        
    def auto_discover(self, skills_folder="skills"):
        """Escanea la carpeta skills y auto-registra cualquier habilidad válida."""
        self.context.logger.info("[Registry] Escaneando directorio de habilidades...")
        
        # Limpiamos el registro actual para evitar duplicados en la recarga
        self._registry.clear()
        
        if not os.path.exists(skills_folder):
            return

        for filename in os.listdir(skills_folder):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"{skills_folder}.{filename[:-3]}"
                try:
                    # Importamos o recargamos el módulo en caliente
                    module = importlib.import_module(module_name)
                    importlib.reload(module)
                    
                    # Buscamos clases dentro del archivo que hereden de BaseSkill
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            if hasattr(obj, "TRIGGERS") and obj.TRIGGERS:
                                self.register(module_name, name, obj.TRIGGERS)
                                
                except Exception as e:
                    self.context.logger.error(f"Fallo al cargar habilidad {module_name}: {e}")

    def register(self, module_name, class_name, triggers):
        """Registra una habilidad sin cargarla en memoria RAM."""
        for trigger in triggers:
            self._registry[trigger] = {"module": module_name, "class": class_name, "instance": None}

    def process(self, command, attachment_path=None):
        """Busca el trigger, carga la clase (lazy) y ejecuta."""
        for trigger, data in self._registry.items():
            if trigger in command:
                if data["instance"] is None:
                    self.context.logger.info(f"[Registry] Instanciando habilidad en RAM: {data['class']}")
                    module = importlib.import_module(data["module"])
                    skill_class = getattr(module, data["class"])
                    data["instance"] = skill_class(self.context)
                    
                return data["instance"].execute(command, attachment_path)
        return None