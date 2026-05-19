import queue
import threading

class TaskQueue:
    def __init__(self, logger):
        self.task_queue = queue.Queue()
        self.logger = logger
        
        # Creamos un "trabajador" en segundo plano que nunca se detiene
        # El modo daemon=True asegura que si apagas Jarvis, este hilo también muera
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
        self.logger.info("Cola de Tareas en segundo plano inicializada y esperando trabajo.")

    def add_task(self, target_function, *args, **kwargs):
        """Añade una función pesada a la cola para que se ejecute en el fondo."""
        self.task_queue.put((target_function, args, kwargs))
        self.logger.info(f"Tarea encolada: {target_function.__name__}")

    def _process_queue(self):
        """El trabajador invisible que va resolviendo la cola una por una."""
        while True:
            func, args, kwargs = self.task_queue.get()
            try:
                self.logger.info(f"Ejecutando tarea asíncrona: {func.__name__}")
                # Ejecutamos la tarea real
                func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Fallo crítico en tarea en segundo plano ({func.__name__}): {e}")
            finally:
                # Le avisa a la cola que ya terminó, liberando espacio
                self.task_queue.task_done()
                self.logger.info(f"Tarea completada: {func.__name__}")