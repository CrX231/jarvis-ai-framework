import sys
from interfaces.audio_listener import AudioListener
from interfaces.voice_synth import VoiceSynthesizer
from interfaces.discord_interface import DiscordInterface
from core.brain import Brain
from core.permission_layer import PermissionLayer, PermissionLevel
from core.system_logger import SystemLogger
from core.task_queue import TaskQueue
from core.event_bus import EventBus
from core.context_manager import ContextManager
from core.reasoning_engine import ReasoningEngine
from core.workflow_engine import WorkflowEngine
from skills.time_skill import TimeSkill
from skills.browser_skill import BrowserSkill
from skills.system_skill import SystemSkill
from skills.weather_skill import WeatherSkill
from skills.music_skill import MusicSkill
from skills.spotify_skill import SpotifySkill
from skills.vision_skill import VisionSkill
from skills.document_skill import DocumentSkill
from skills.memory_skill import MemorySkill
from skills.volume_skill import VolumeSkill
from skills.coder_skill import CoderSkill
from skills.messaging_skill import MessagingSkill
from skills.creative_skill import CreativeSkill
from skills.image_skill import ImageSkill
from skills.research_skill import ResearchSkill
from skills.desktop_skill import DesktopSkill  # <-- NUEVO IMPORT FÍSICO

class Jarvis:
    def __init__(self):
        # 1. Base Estructural
        self.logger = SystemLogger()
        self.logger.info("=== INICIANDO SISTEMAS JARVIS ===")
        self.event_bus = EventBus(self.logger)
        self.task_queue = TaskQueue(self.logger)
        self.context_manager = ContextManager(self.logger)
        
        # 2. Interfaces y Cerebro
        self.listener = AudioListener()
        self.voice = VoiceSynthesizer()
        self.brain = Brain()
        
        # 3. Motores Avanzados (Fase 2 y 3)
        self.reasoning_engine = ReasoningEngine(self.logger, self.brain, self.event_bus)
        self.workflow_engine = WorkflowEngine(self.logger, self.event_bus)
        
        # 4. Seguridad y Habilidades
        self.permission_layer = PermissionLayer()
        self.time_skill = TimeSkill()
        self.browser_skill = BrowserSkill()
        self.system_skill = SystemSkill()
        self.weather_skill = WeatherSkill()
        self.music_skill = MusicSkill()
        self.spotify_skill = SpotifySkill()
        self.vision_skill = VisionSkill()
        self.document_skill = DocumentSkill()
        self.memory_skill = MemorySkill(self.logger)
        self.volume_skill = VolumeSkill()
        self.coder_skill = CoderSkill()
        self.messaging_skill = MessagingSkill()
        self.creative_skill = CreativeSkill()
        self.image_skill = ImageSkill()
        self.research_skill = ResearchSkill(self.logger, self.brain)
        
        # INICIALIZACIÓN: Habilidad de Control de Escritorio
        self.desktop_skill = DesktopSkill(self.logger)

        self.discord_link = DiscordInterface(self.process_command)
        
        # --- SUSCRIPCIONES A EVENTOS ---
        self.event_bus.subscribe("SYSTEM_READY", self._on_system_ready)
        self.event_bus.subscribe("SPEAK_REQUEST", self._on_speak_request)
        
        self.logger.info("Todos los módulos y habilidades cargados correctamente.")

    def _on_system_ready(self, data):
        self.voice.speak("Sistemas integrados. Esperando órdenes.")
        
    def _on_speak_request(self, data):
        texto = data.get("text", "")
        if texto:
            print(f"\nJarvis: {texto}")
            self.voice.speak(texto)

    def _execute_async(self, func, *args, **kwargs):
        try:
            resultado = func(*args, **kwargs)
            if resultado:
                self.logger.info(f"Tarea asíncrona finalizada: {resultado}")
                self.event_bus.publish("SPEAK_REQUEST", {"text": resultado})
        except Exception as e:
            self.logger.error(f"Error en tarea asíncrona: {e}")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Señor, ocurrió un error procesando la tarea en segundo plano."})

    def process_command(self, comando, attachment_path=None):
        comando = comando.lower()
        self.logger.info(f"Procesando comando: '{comando}'")
        self.context_manager.add_command(comando)
        
        # --- INTERCEPTOR DE VALIDACIÓN DEL WORKFLOW ---
        if self.workflow_engine.workflow_state == "WAITING_USER":
            if any(word in comando for word in ["sí", "si", "procede", "continúa", "ok", "adelante", "hazlo"]):
                return self.workflow_engine.resume_workflow(True)
            elif any(word in comando for word in ["no", "cancela", "aborta", "detén", "para"]):
                return self.workflow_engine.resume_workflow(False)
        
        if attachment_path:
            self.logger.info(f"Analizando documento adjunto: {attachment_path}")
            self.context_manager.add_file(attachment_path)
            return self.document_skill.analyze(comando, self.brain, ruta=attachment_path)
            
        # --- LANZADOR DE FLUJO DE TRABAJO (TEST) ---
        elif "inicia el flujo de prueba" in comando or "inicia flujo de desarrollo" in comando:
            pasos = [
                {
                    "type": "action", 
                    "name": "Investigación Base", 
                    "func": lambda ctx: self.research_skill.investigate("Arquitectura de software para ERP agroindustrial")
                },
                {
                    "type": "wait_validation", 
                    "name": "Validar Arquitectura", 
                    "prompt": "Señor, he completado la extracción de datos técnicos. ¿Desea que proceda a redactar el documento base para AgroCore Connect?"
                },
                {
                    "type": "action", 
                    "name": "Redacción", 
                    "func": lambda ctx: self.creative_skill.create_word("Arquitectura técnica base de AgroCore Connect", self.brain)
                }
            ]
            self.workflow_engine.load_and_start("Desarrollo AgroCore Fase 1", pasos)
            return "Cargando protocolo de flujo en memoria."

        # --- ENRUTAMIENTO AUTÓNOMO (MOTOR DE RAZONAMIENTO) ---
        elif "encárgate de" in comando or "misión:" in comando or "planifica" in comando:
            objetivo = comando.replace("encárgate de", "").replace("misión:", "").replace("planifica", "").strip()
            self.logger.info("Delegando control al Motor de Razonamiento.")
            self.context_manager.set_topic(f"Misión Autónoma: {objetivo}")
            self.task_queue.add_task(self.reasoning_engine.execute_plan, objetivo, self.process_command)
            return "Iniciando protocolos de agente autónomo, señor. Evaluando variables."
        
        # --- INVESTIGACIÓN PROFUNDA AUTÓNOMA (WEB AGENT) ---
        elif "investiga sobre" in comando or "averigua sobre" in comando:
            tema = comando.replace("investiga sobre", "").replace("averigua sobre", "").strip()
            self.logger.info(f"Encolando investigación profunda: {tema}")
            self.context_manager.set_topic(f"Investigación: {tema}")
            self.task_queue.add_task(self._execute_async, self.research_skill.investigate, tema)
            return f"Iniciando protocolos de rastreo web e investigación sobre {tema}, señor. Le informaré los hallazgos en breve."
            
        # --- CONTROL FÍSICO DE ESCRITORIO (ACTUALIZADO) ---
        elif any(clave in comando for clave in ["escribe ", "presiona enter", "copia esto", "pega esto", "selecciona todo", "minimiza todo", "cierra esta ventana"]):
            if "código" not in comando:
                self.logger.info("Activando actuadores físicos de teclado/ratón.")
                return self.desktop_skill.process_physical_command(comando)

        # --- ENRUTAMIENTO ESTÁNDAR ---
        elif "hora" in comando:
            return self.time_skill.get_time()
            
        elif "clima" in comando or "temperatura" in comando:
            return self.weather_skill.get_weather(comando)
            
        elif "spotify" in comando:
            return self.spotify_skill.play_music(comando)
            
        elif "reproduce" in comando or "pon" in comando:
            return self.music_skill.play_youtube(comando)
            
        elif ("analiza" in comando or "lee" in comando or "revisa" in comando) and ("documento" in comando or "archivo" in comando):
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Claro, selecciona el archivo en la ventana que acaba de aparecer."})
            return self.document_skill.analyze(comando, self.brain)
            
        elif "recuerda que" in comando or "guarda una nota" in comando:
            return self.memory_skill.save_note(comando)
            
        elif "qué recuerdas" in comando or "lee mis notas" in comando or "qué sabes sobre" in comando:
            return self.memory_skill.get_notes(comando)

        elif "borra" in comando or "elimina" in comando or "olvida" in comando:
            item_a_borrar = comando.replace("borra", "").replace("elimina", "").replace("olvida", "").replace("sobre", "").strip()
            self.event_bus.publish("SPEAK_REQUEST", {"text": f"Señor, he recibido la orden de borrar información relacionada con: {item_a_borrar}. ¿Confirma la eliminación permanente?"})
            
            respuesta_auth = self.listener.listen(activo=True)
            if self.permission_layer.is_authorized(respuesta_auth):
                self.logger.security(f"Autorización concedida para borrar nota semántica sobre: {item_a_borrar}")
                self.event_bus.publish("SPEAK_REQUEST", {"text": "Autorización confirmada. Procediendo a alterar base vectorial."})
                return self.memory_skill.delete_note(comando)
            else:
                self.logger.security("Autorización DENEGADA para borrado de nota.")
                return "Operación abortada. La arquitectura de memoria permanece intacta."
            
        elif "busca" in comando:
            return self.browser_skill.open_site(comando)
            
        elif "abre" in comando or "ejecuta" in comando:
            respuesta = self.system_skill.open_program(comando)
            if not respuesta:
                respuesta = self.browser_skill.open_site(comando)
            return respuesta
                
        elif "volumen" in comando or "silencia" in comando or "mute" in comando:
            return self.volume_skill.change_volume(comando)
            
        elif "programa" in comando or "crea un script" in comando or "escribe código" in comando:
            self.logger.info("Encolando modo de programación autónoma.")
            self.context_manager.set_topic("Programación")
            self.task_queue.add_task(self._execute_async, self.coder_skill.write_code, comando, self.brain)
            return "Iniciando la escritura de código en segundo plano, señor."
            
        elif "crea un documento" in comando or "monografía" in comando or "word" in comando:
            tema = comando.replace("crea un documento de word sobre", "").replace("crea un documento sobre", "").replace("haz una monografía sobre", "").replace("word", "").strip()
            self.context_manager.set_topic(f"Creación de documento: {tema}")
            self.task_queue.add_task(self._execute_async, self.creative_skill.create_word, tema, self.brain)
            return "Iniciando redacción del documento en segundo plano. Le notificaré cuando esté listo."
            
        elif "crea un excel" in comando or "hoja de cálculo" in comando:
            tema = comando.replace("crea un excel sobre", "").replace("crea una hoja de cálculo sobre", "").replace("excel", "").strip()
            self.task_queue.add_task(self._execute_async, self.creative_skill.create_excel, tema, self.brain)
            return "Generando hoja de cálculo en segundo plano."
            
        elif "crea una presentación" in comando or "diapositivas" in comando or "powerpoint" in comando:
            tema = comando.replace("crea una presentación sobre", "").replace("crea unas diapositivas sobre", "").replace("powerpoint", "").strip()
            self.task_queue.add_task(self._execute_async, self.creative_skill.create_pptx, tema, self.brain)
            return "Diseñando diapositivas en segundo plano."
            
        elif "genera una imagen" in comando or "crea una imagen" in comando or "dibuja" in comando:
            self.logger.info("Encolando generación visual...")
            self.task_queue.add_task(self._execute_async, self.image_skill.generate_image, comando, self.brain)
            return "Procesando generación visual en segundo plano. Esto tomará unos segundos."
            
        elif "pantalla" in comando or "ve" in comando:
            if "código" in comando or "refactoriza" in comando:
                self.logger.info("Iniciando análisis arquitectónico en pantalla.")
                self.event_bus.publish("SPEAK_REQUEST", {"text": "Capturando pantalla y analizando arquitectura SOLID. Un momento."})
                return self.vision_skill.analyze_code_on_screen(comando, self.brain)
            else:
                self.event_bus.publish("SPEAK_REQUEST", {"text": "Revisando la pantalla."})
                pantallazo_path = self.vision_skill.capture_screen()
                if pantallazo_path:
                    from PIL import Image
                    img = Image.open(pantallazo_path)
                    return self.brain.think(comando, image=img)
                else:
                    self.logger.error("Fallo al capturar la pantalla.")
                    return "Hubo un error al intentar ver la pantalla."
            
        elif "manda un correo" in comando or "envía un correo" in comando:
            if "que diga" in comando:
                partes = comando.split("que diga")
                destinatario = partes[0].replace("manda un correo a", "").replace("envía un correo a", "").replace("manda un correo", "").replace("envía un correo", "").strip()
                mensaje = partes[1].strip()
                
                self.event_bus.publish("SPEAK_REQUEST", {"text": f"Entendí que desea enviar un correo a {destinatario}, diciendo: {mensaje}. ¿Confirma esta acción?"})
                respuesta_auth = self.listener.listen(activo=True)
                
                if self.permission_layer.is_authorized(respuesta_auth):
                    self.logger.security(f"Autorización concedida para enviar correo a {destinatario}")
                    self.event_bus.publish("SPEAK_REQUEST", {"text": "Autorización reconocida. Transmitiendo."})
                    return self.messaging_skill.send_email(comando)
                else:
                    self.logger.security("Autorización DENEGADA para envío de correo exterior.")
                    return "Envío de correo abortado por protocolo de seguridad."
            else:
                return "Por favor, indique el destinatario y el mensaje separándolos con la frase 'que diga'."
                
        else:
            self.logger.info("Delegando comando ambiguo al motor neuronal (con inyección de contexto).")
            contexto_sistema = self.context_manager.get_system_context()
            comando_enriquecido = contexto_sistema + comando
            return self.brain.think(comando_enriquecido)

    def run(self):
        self.discord_link.run_in_background()
        self.logger.info("Enlace satelital de Discord iniciado.")
        
        self.event_bus.publish("SYSTEM_READY")
        
        while True:
            texto = self.listener.listen(activo=False)
            
            if texto:
                if "salir" in texto:
                    self.logger.info("=== APAGADO DEL SISTEMA SOLICITADO ===")
                    self.event_bus.publish("SPEAK_REQUEST", {"text": "Apagando sistemas, señor. Que descanse."})
                    sys.exit()
                    
                if "jarvis" in texto:
                    comando = texto.replace("jarvis", "").strip()
                    
                    if not comando:
                        self.event_bus.publish("SPEAK_REQUEST", {"text": "Dime, Carlos."})
                        comando = self.listener.listen(activo=True)
                        
                    if comando and "salir" not in comando:
                        respuesta = self.process_command(comando, attachment_path=None)
                        
                        if respuesta:
                            self.event_bus.publish("SPEAK_REQUEST", {"text": respuesta})
                            self.logger.info(f"Comando procesado exitosamente.")

if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.run()