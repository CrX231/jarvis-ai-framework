import time
from core.semantic_memory import SemanticMemory

class MemorySkill:
    def __init__(self, logger):
        # Ahora inyectamos el logger desde main.py y se lo pasamos a la base de datos
        self.logger = logger
        self.db = SemanticMemory(logger)

    def save_note(self, comando):
        nota = comando.replace("recuerda que", "").replace("guarda una nota", "").strip()
        if not nota:
            return "No especificaste qué debo recordar, señor."
        
        # Generamos un ID único basado en el momento exacto de creación
        nota_id = f"mem_{int(time.time())}"
        exito = self.db.store_memory(nota_id, nota, {"fecha": time.strftime("%Y-%m-%d %H:%M:%S")})
        
        if exito:
            return "Información codificada exitosamente en mi red neuronal semántica."
        return "He detectado una falla al intentar cristalizar el recuerdo."

    def get_notes(self, comando):
        # Filtramos la frase para quedarnos con el concepto central
        query = comando.replace("qué recuerdas sobre", "").replace("qué sabes sobre", "").replace("lee mis notas", "").replace("qué recuerdas", "").strip()
        
        if not query:
            return "Mi memoria abarca un espectro amplio, señor. ¿Sobre qué concepto específico desea que busque?"

        resultados = self.db.search_memory(query, n_results=2)
        
        if not resultados:
            return f"No encuentro nodos semánticos relacionados con '{query}' en mi arquitectura."
        
        respuesta = "Esto es lo que recuperé de mis archivos centrales: " + "; ".join(resultados)
        return respuesta

    def delete_note(self, comando):
        item_a_borrar = comando.replace("borra", "").replace("elimina", "").replace("olvida", "").replace("sobre", "").strip()
        
        if not item_a_borrar:
            return "Debe especificar qué segmento de memoria desea purgar, señor."
            
        # 1. Utilizamos ChromaDB para encontrar el recuerdo que matemáticamente más se parezca a lo que quieres borrar
        ids, textos = self.db.search_and_get_id(item_a_borrar)
        
        if ids:
            id_a_borrar = ids[0]
            texto_a_borrar = textos[0]
            
            # 2. Procedemos con la destrucción del nodo
            self.db.delete_memory(id_a_borrar)
            return f"He purgado exitosamente este archivo de mi sistema: '{texto_a_borrar}'."
        else:
            return "No encontré coincidencias suficientemente exactas para proceder con una eliminación segura."