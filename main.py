import sys
import atexit
import time

from core.config import WAKE_WORDS, CONFIRM_WORDS, CANCEL_WORDS, CPU_WARNING_THRESHOLD, RAM_WARNING_THRESHOLD, BATTERY_WARNING_THRESHOLD
from interfaces.audio_listener import AudioListener, WakeWordListener
from interfaces.voice_synth import VoiceSynthesizer
from interfaces.discord_interface import DiscordInterface
from core.brain import Brain
from core.permission_layer import PermissionLayer
from core.system_logger import SystemLogger
from core.task_queue import TaskQueue
from core.event_bus import EventBus
from core.context_manager import ContextManager
from core.reasoning_engine import ReasoningEngine
from core.workflow_engine import WorkflowEngine
from core.proactive_daemon import ProactiveDaemon, SystemResourceMonitor, InternetMonitor, BatteryMonitor
from core.skill_registry import SkillRegistry

class JarvisContext:
    """Contenedor de dependencias (Inyección de Dependencias) para los Skills."""
    def __init__(self, logger, brain, event_bus, task_queue, permission_layer):
        self.logger = logger
        self.brain = brain
        self.event_bus = event_bus
        self.task_queue = task_queue
        self.permission_layer = permission_layer

class Jarvis:
    def __init__(self):
        self.logger = SystemLogger()
        self.logger.info("=== INICIANDO SISTEMAS JARVIS ===")
        
        # 1. Servicios de Infraestructura Central (Core)
        self.event_bus = EventBus(self.logger)
        self.task_queue = TaskQueue(self.logger)
        self.context_manager = ContextManager(self.logger)
        self.permission_layer = PermissionLayer()
        self.brain = Brain()
        self.voice = VoiceSynthesizer()
        
        # 2. Interfaces de Audio Inteligente (IA Local)
        self.listener = AudioListener(self.logger)
        self.listener.initialize()  # Inicializa el modelo Whisper en CPU
        
        self.wake_listener = WakeWordListener(self.logger, self._on_wake_word_detected, wake_words=WAKE_WORDS)
        self.wake_listener.initialize()  # Inicializa el detector ligero de Wake Word

        # 3. Empaquetado del Contexto Compartido
        self.shared_context = JarvisContext(
            self.logger, self.brain, self.event_bus, self.task_queue, self.permission_layer
        )

        # 4. Motores de Inferencia Avanzados
        self.reasoning_engine = ReasoningEngine(self.logger, self.brain, self.event_bus)
        self.workflow_engine = WorkflowEngine(self.logger, self.event_bus)
        
        # 5. Registro Centralizado de Habilidades (Lazy Loading Activo)
        self.registry = SkillRegistry(self.shared_context)
        self._register_all_skills()

        # 6. Orquestador Daemon Proactivo (Iniciativa en Segundo Plano)
        self.proactive_daemon = ProactiveDaemon(self.logger, self.event_bus, self.task_queue)
        self.proactive_daemon.add_monitor(SystemResourceMonitor(cpu_threshold=CPU_WARNING_THRESHOLD, ram_threshold=RAM_WARNING_THRESHOLD))
        self.proactive_daemon.add_monitor(InternetMonitor(interval=20))
        self.proactive_daemon.add_monitor(BatteryMonitor(low_threshold=BATTERY_WARNING_THRESHOLD))
        self.proactive_daemon.reminders.add(9, 0, "Buenos días. He iniciado los protocolos de monitoreo de sistemas.")

        # 7. Enlaces y Canales de Comunicación Externos
        self.discord_link = DiscordInterface(self.process_command)
        
        # --- SUSCRIPCIONES AL BUS DE EVENTOS ---
        self.event_bus.subscribe("SYSTEM_READY", self._on_system_ready)
        self.event_bus.subscribe("SPEAK_REQUEST", self._on_speak_request)
        self.event_bus.subscribe("AUTH_REQUEST", self._handle_auth_flow)
        
        # Registro automatizado para evitar corrupción de memoria al salir
        atexit.register(self.shutdown)
        self.logger.info("Arquitectura modular y bus de eventos acoplados correctamente.")

    def _register_all_skills(self):
        """Registra la ubicación y disparadores de cada habilidad sin instanciarla en memoria RAM."""
        self.registry.register("skills.time_skill", "TimeSkill", ["hora", "qué hora", "dime la hora"])
        self.registry.register("skills.weather_skill", "WeatherSkill", ["clima", "temperatura"])
        self.registry.register("skills.spotify_skill", "SpotifySkill", ["spotify"])
        self.registry.register("skills.music_skill", "MusicSkill", ["reproduce", "pon"])
        self.registry.register("skills.browser_skill", "BrowserSkill", ["busca"])
        self.registry.register("skills.system_skill", "SystemSkill", ["abre", "ejecuta"])
        self.registry.register("skills.desktop_skill", "DesktopSkill", ["escribe ", "presiona enter", "copia esto", "pega esto", "selecciona todo", "minimiza todo", "cierra esta ventana"])
        self.registry.register("skills.coder_skill", "CoderSkill", ["programa", "crea un script", "escribe código"])
        self.registry.register("skills.creative_skill", "CreativeSkill", ["crea un documento", "monografía", "word", "crea un excel", "hoja de cálculo", "crea una presentación", "diapositivas", "powerpoint"])
        self.registry.register("skills.image_skill", "ImageSkill", ["genera una imagen", "crea una imagen", "dibuja"])
        self.registry.register("skills.document_skill", "DocumentSkill", ["analiza", "lee", "revisa"])
        self.registry.register("skills.memory_skill", "MemorySkill", ["recuerda que", "guarda una nota", "qué recuerdas", "lee mis notas", "qué sabes sobre", "borra", "elimina", "olvida"])
        self.registry.register("skills.messaging_skill", "MessagingSkill", ["manda un correo", "envía un correo"])
        self.registry.register("skills.research_skill", "ResearchSkill", ["investiga sobre", "averigua sobre"])
        self.registry.register("skills.vision_skill", "VisionSkill", ["pantalla", "ve", "refactoriza"])
        self.registry.register("skills.volume_skill", "VolumeSkill", ["volumen", "silencia", "mute"])

    def _on_system_ready(self, data):
        self.voice.speak("Sistemas en línea. Protocolo de escucha de bajo consumo activo.")

    def _on_speak_request(self, data):
        texto = data.get("text", "")
        if texto:
            print(f"\nJarvis: {texto}")
            self.voice.speak(texto)

    def _on_wake_word_detected(self):
        """Se ejecuta de forma asíncrona desde el hilo secundario al interceptar la palabra clave."""
        self.event_bus.publish("SPEAK_REQUEST", {"text": "Dime."})
        # Despierta el micrófono de alta fidelidad para procesar la orden
        comando = self.listener.listen(activo=True)
        if comando:
            self.process_command(comando)

    def _handle_auth_flow(self, data):
        """Manejador centralizado de seguridad que desacopla la validación de los módulos de lógica."""
        accion = data.get("action")
        self.event_bus.publish("SPEAK_REQUEST", {"text": f"Se requiere autorización de voz para: {accion}. ¿Confirma la operación?"})
        respuesta_auth = self.listener.listen(activo=True)
        
        if respuesta_auth and self.permission_layer.is_authorized(respuesta_auth):
            self.logger.security("Protocolo de seguridad superado. Autorización concedida.")
            data.get("callback_success")()
        else:
            self.logger.security("Alerta de seguridad: Autorización denegada por fallo de coincidencia de voz.")
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Operación abortada por restricciones de seguridad."})

    def process_command(self, comando, attachment_path=None):
        comando = comando.lower()
        self.logger.info(f"Procesando comando: '{comando}'")
        self.context_manager.add_command(comando)
        
        if "salir" in comando or "apágate" in comando:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Desconectando núcleos de ejecución. Que descanse, señor."})
            sys.exit(0)

        # 1. Interceptor de flujos interactivos (Workflows)
        if self.workflow_engine.workflow_state == "WAITING_USER":
            if any(word in comando for word in CONFIRM_WORDS):
                return self.workflow_engine.resume_workflow(True)
            elif any(word in comando for word in CANCEL_WORDS):
                return self.workflow_engine.resume_workflow(False)

        # 2. Enrutamiento polimórfico mediante el Registro (SOLID - OCP cumplido)
        respuesta_skill = self.registry.process(comando, attachment_path)
        if respuesta_skill:
            self.event_bus.publish("SPEAK_REQUEST", {"text": respuesta_skill})
            return

        # 3. Capa de Redirección Final: Razonamiento General del LLM
        self.logger.info("Comando complejo no estructurado. Derivando al procesador neuronal.")
        contexto_sistema = self.context_manager.get_system_context()
        respuesta_llm = self.brain.think(contexto_sistema + comando)
        if respuesta_llm:
            self.event_bus.publish("SPEAK_REQUEST", {"text": respuesta_llm})

    def shutdown(self):
        """Garantiza la desconexión limpia de puertos, flujos de audio y subprocesos."""
        self.logger.info("=== INICIANDO APAGADO CONTROLADO DE RECURSOS ===")
        try:
            self.wake_listener.stop()
            self.proactive_daemon.stop()
            self.discord_link.stop()
            self.logger.info("Hilos daemon detenidos. Memoria y microfonía liberados correctamente.")
        except Exception as e:
            self.logger.error(f"Error durante la secuencia de desmantelamiento: {e}")

    def run(self):
        # Activación de demonios e hilos de monitorización
        self.discord_link.run_in_background()
        self.proactive_daemon.start()
        
        # Publicación del estado listo en el bus
        self.event_bus.publish("SYSTEM_READY")
        
        # Disparo del bucle de interrupción por palabra clave (Wake Word)
        self.wake_listener.start()
        
        try:
            # Mantenemos vivo el hilo principal sin consumo de ciclos de reloj
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.run()