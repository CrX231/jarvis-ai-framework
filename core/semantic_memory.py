import chromadb
from chromadb.config import Settings
import os

class SemanticMemory:
    def __init__(self, logger):
        self.logger = logger
        self.db_dir = "memory_vector_db"
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        try:
            # Inicializamos ChromaDB local sin telemetría para mantener los logs limpios
            self.client = chromadb.PersistentClient(
                path=self.db_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(name="jarvis_memory")
            self.logger.info("Corteza de Memoria Semántica (ChromaDB) inicializada con éxito.")
        except Exception as e:
            self.logger.error(f"Fallo crítico en la inicialización de ChromaDB: {e}")

    def store_memory(self, text_id, content, metadata=None):
        """Convierte texto en vectores y lo guarda permanentemente."""
        try:
            if metadata is None:
                metadata = {"source": "voice_command"}
                
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[text_id]
            )
            self.logger.info(f"Recuerdo semántico cristalizado: {text_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error al escribir en memoria vectorial: {e}")
            return False

    def search_memory(self, query, n_results=2):
        """Busca información por proximidad de significado."""
        try:
            if self.collection.count() == 0:
                return []
                
            resultados = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count())
            )
            
            if resultados and 'documents' in resultados and len(resultados['documents'][0]) > 0:
                return resultados['documents'][0]
            return []
        except Exception as e:
            self.logger.error(f"Error en búsqueda vectorial: {e}")
            return []
            
    def search_and_get_id(self, query, n_results=1):
        """Busca y devuelve el ID único para poder modificar o borrar la memoria."""
        try:
            if self.collection.count() == 0:
                return [], []
                
            resultados = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count())
            )
            if resultados and 'ids' in resultados and len(resultados['ids'][0]) > 0:
                return resultados['ids'][0], resultados['documents'][0]
            return [], []
        except Exception as e:
            self.logger.error(f"Error al buscar ID semántico: {e}")
            return [], []

    def delete_memory(self, text_id):
        """Destruye un nodo de memoria específico."""
        try:
            self.collection.delete(ids=[text_id])
            self.logger.info(f"Recuerdo eliminado permanentemente: {text_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error al purgar memoria vectorial: {e}")
            return False