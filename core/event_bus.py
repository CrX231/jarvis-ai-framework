class EventBus:
    def __init__(self, logger):
        self.logger = logger
        # Diccionario donde la llave es el nombre del evento, y el valor es una lista de funciones a ejecutar
        self.subscribers = {}

    def subscribe(self, event_type, callback_function):
        """Permite que un módulo se suscriba a un evento específico."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(callback_function)
        self.logger.info(f"Nuevo suscriptor adherido al evento: {event_type}")

    def publish(self, event_type, data=None):
        """Dispara un evento, notificando a todos los módulos suscritos."""
        if event_type in self.subscribers:
            self.logger.info(f"Disparando evento: {event_type}")
            
            for callback in self.subscribers[event_type]:
                try:
                    # Ejecutamos la función de cada suscriptor pasándole los datos
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Fallo en suscriptor del evento {event_type}: {e}")