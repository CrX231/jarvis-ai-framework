import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from core.skill_registry import BaseSkill

class MessagingSkill(BaseSkill):
    TRIGGERS = ["manda un correo", "envía un correo"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        self.event_bus = context.event_bus
        self.task_queue = context.task_queue
        
        load_dotenv()
        self.email_address = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASS")
        
        self.contactos = {
            "carlos": "carloswmc005@gmail.com",
            "trabajo": "mcruzcarloswilm@uss.edu.pe"
        }

    def execute(self, command, attachment_path=None):
        if not self.email_address or not self.email_password:
            return "Faltan las credenciales de correo en el archivo punto env."

        if "que diga" not in command:
            return "Por seguridad, debes usar la frase 'que diga' para separar a quién se lo envío del mensaje real."
            
        try:
            partes = command.split("que diga")
            primera_parte = partes[0]
            mensaje = partes[1].strip()
            
            destinatario_nombre = None
            for nombre in self.contactos.keys():
                if nombre in primera_parte:
                    destinatario_nombre = nombre
                    break
                    
            if not destinatario_nombre:
                return "No encontré a esa persona en tu base de datos de contactos."
                
            correo_destino = self.contactos[destinatario_nombre]
            
            # DIP: En lugar de interrumpir el flujo aquí, mandamos una solicitud al EventBus
            self.event_bus.publish("AUTH_REQUEST", {
                "action": f"enviar correo a {destinatario_nombre}",
                "callback_success": lambda: self.task_queue.add_task(self._send_email_async, destinatario_nombre, correo_destino, mensaje)
            })
            return None # El flujo de autenticación tomará el control
            
        except Exception as e:
            self.logger.error(f"Fallo al procesar orden de mensajería: {e}")
            return "Hubo un fallo al estructurar el mensaje."

    def _send_email_async(self, nombre, destino, mensaje):
        """Ejecuta el envío de red en segundo plano."""
        self.logger.info(f"[Mensajería] Enviando correo a {destino}...")
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Mensaje de voz a través de Jarvis'
            msg['From'] = self.email_address
            msg['To'] = destino
            msg.set_content(mensaje)

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            self.event_bus.publish("SPEAK_REQUEST", {"text": f"Correo electrónico enviado exitosamente a {nombre.capitalize()}."})
        except Exception as e:
            self.logger.error(f"Fallo crítico enviando correo: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Falló la transmisión del paquete de datos hacia los servidores de Google."})