import logging
import os
from datetime import datetime

class SystemLogger:
    def __init__(self):
        self.log_dir = "logs"
        
        # Crea la carpeta de logs si no existe
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Genera un archivo nuevo por día
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"jarvis_{fecha_hoy}.log")
        
        # Configuramos el formato: [Fecha/Hora] [NIVEL] - Mensaje
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            encoding='utf-8'
        )
        
        self.logger = logging.getLogger("JarvisCore")

    def info(self, mensaje):
        """Para eventos normales (comandos recibidos, acciones completadas)."""
        self.logger.info(mensaje)

    def warning(self, mensaje):
        """Para advertencias (intentos fallidos de permisos, comandos no entendidos)."""
        self.logger.warning(mensaje)

    def error(self, mensaje):
        """Para fallos de código o excepciones del sistema."""
        self.logger.error(mensaje)
        
    def security(self, mensaje):
        """Para registrar decisiones de la Capa de Permisos."""
        self.logger.info(f"[SECURITY] {mensaje}")