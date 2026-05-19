import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

class MessagingSkill:
    def __init__(self):
        load_dotenv()
        self.email_address = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASS")
        
        # Aquí configuras tu libreta de contactos (todo en minúsculas)
        self.contactos = {
            "carlos": "carloswmc005@gmail.com",
            "trabajo": "mcruzcarloswilm@uss.edu.pe"
        }

    def send_email(self, command):
        if not self.email_address or not self.email_password:
            return "Faltan las credenciales de correo en el archivo punto env."

        comando = command.lower()
        
        # Formato esperado: "Jarvis, manda un correo a Carlos que diga hola cómo estás"
        if "que diga" not in comando:
            return "Por seguridad, debes usar la frase 'que diga' para separar a quién se lo envío del mensaje real."
            
        try:
            # Partimos la orden en dos pedazos
            partes = comando.split("que diga")
            primera_parte = partes[0] # "manda un correo a carlos "
            mensaje = partes[1].strip() # "hola cómo estás"
            
            # Buscamos quién es el destinatario
            destinatario_nombre = None
            for nombre in self.contactos.keys():
                if nombre in primera_parte:
                    destinatario_nombre = nombre
                    break
                    
            if not destinatario_nombre:
                return "No encontré a esa persona en tu base de datos de contactos."
                
            correo_destino = self.contactos[destinatario_nombre]
            print(f"[Mensajería] Enviando correo a {correo_destino}...")
            
            # Armamos el paquete de correo
            msg = EmailMessage()
            msg['Subject'] = 'Mensaje de voz a través de Jarvis'
            msg['From'] = self.email_address
            msg['To'] = correo_destino
            msg.set_content(mensaje)

            # Nos conectamos a los servidores de Google y lo disparamos
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return f"Correo electrónico enviado exitosamente a {destinatario_nombre.capitalize()}."
            
        except Exception as e:
            return f"Hubo un fallo crítico al enviar el mensaje: {e}"