import time
from core.semantic_memory import SemanticMemory
from core.skill_registry import BaseSkill

class MemorySkill(BaseSkill):
    TRIGGERS = ["recuerda que", "guarda una nota", "qué recuerdas", "lee mis notas", "qué sabes sobre", "borra", "elimina", "olvida"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        self.event_bus = context.event_bus
        self.db = SemanticMemory(self.logger)

    def execute(self, command, attachment_path=None):
        if any(word in command for word in ["borra", "elimina", "olvida"]):
            return self._delete_note_flow(command)
        elif any(word in command for word in ["qué recuerdas", "lee mis notas", "qué sabes sobre"]):
            return self._get_notes(command)
        else:
            return self._save_note(command)

    def _save_note(self, comando):
        nota = comando.replace("recuerda que", "").replace("guarda una nota", "").strip()
        if not nota:
            return "No especificaste qué debo recordar, señor."
        
        nota_id = f"mem_{int(time.time())}"
        exito = self.db.store_memory(nota_id, nota, {"fecha": time.strftime("%Y-%m-%d %H:%M:%S")})
        
        if exito:
            return "Información codificada exitosamente en mi red neuronal semántica."
        return "He detectado una falla al intentar cristalizar el recuerdo."

    def _get_notes(self, comando):
        query = comando.replace("qué recuerdas sobre", "").replace("qué sabes sobre", "").replace("lee mis notas", "").replace("qué recuerdas", "").strip()
        
        if not query:
            return "Mi memoria abarca un espectro amplio, señor. ¿Sobre qué concepto específico desea que busque?"

        resultados = self.db.search_memory(query, n_results=2)
        
        if not resultados:
            return f"No encuentro nodos semánticos relacionados con '{query}' en mi arquitectura."
        
        respuesta = "Esto es lo que recuperé de mis archivos centrales: " + "; ".join(resultados)
        return respuesta

    def _delete_note_flow(self, comando):
        """Inicia el flujo de borrado pidiendo autorización mediante el EventBus."""
        item_a_borrar = comando.replace("borra", "").replace("elimina", "").replace("olvida", "").replace("sobre", "").strip()
        
        if not item_a_borrar:
            return "Debe especificar qué segmento de memoria desea purgar, señor."
            
        ids, textos = self.db.search_and_get_id(item_a_borrar)
        
        if not ids:
            return "No encontré coincidencias suficientemente exactas para proceder con una eliminación segura."
            
        id_a_borrar = ids[0]
        texto_a_borrar = textos[0]
        
        # DIP: Solicitamos autorización delegando la validación al enrutador central
        self.event_bus.publish("AUTH_REQUEST", {
            "action": f"borrar la nota sobre {item_a_borrar}",
            "callback_success": lambda: self._execute_deletion(id_a_borrar, texto_a_borrar)
        })
        return None # La respuesta final vendrá del callback

    def _execute_deletion(self, memory_id, texto_a_borrar):
        """Este método solo se ejecuta si la capa de permisos da luz verde."""
        self.db.delete_memory(memory_id)
        self.event_bus.publish("SPEAK_REQUEST", {"text": f"He purgado exitosamente este archivo de mi sistema: '{texto_a_borrar}'."})