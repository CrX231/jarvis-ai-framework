import sys
import atexit
from PyQt5.QtWidgets import QApplication

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
from core.episodic_memory import EpisodicMemory
from core.self_corrector import SelfCorrector
from core.reasoning_engine import ReasoningEngine
from core.workflow_engine import WorkflowEngine
from core.proactive_daemon import ProactiveDaemon, SystemResourceMonitor, InternetMonitor, BatteryMonitor, VisualAwarenessMonitor
from core.skill_registry import SkillRegistry

# IMPORTAMOS LA NUEVA INTERFAZ GRÁFICA
from interfaces.jarvis_ui import JarvisUI

class JarvisContext:
    def __init__(self, logger, brain, event_bus, task_queue, permission_layer):
        self.logger           = logger
        self.brain            = brain
        self.event_bus        = event_bus
        self.task_queue       = task_queue
        self.permission_layer = permission_layer

class Jarvis:
    def __init__(self, q_app):
        self.q_app = q_app
        self.logger = SystemLogger()
        self.logger.info("=== INICIANDO SISTEMAS JARVIS ===")

        # 1. Servicios Base
        self.event_bus        = EventBus(self.logger)
        self.task_queue       = TaskQueue(self.logger)
        self.permission_layer = PermissionLayer()
        self.brain            = Brain()
        self.voice            = VoiceSynthesizer()

        # 2. Memorias e Inteligencia
        self.episodic_memory = EpisodicMemory(self.logger)
        self.episodic_memory.attach(self.event_bus)
        self.context_manager = ContextManager(self.logger, self.episodic_memory)
        self.self_corrector = SelfCorrector(self.logger, self.brain, self.episodic_memory)

        # 3. Microfonía
        self.listener = AudioListener(self.logger)
        self.listener.initialize()
        self.wake_listener = WakeWordListener(self.logger, self._on_wake_word_detected, wake_words=WAKE_WORDS)
        self.wake_listener.initialize()

        # 4. Contexto y Registro Dinámico
        self.shared_context = JarvisContext(self.logger, self.brain, self.event_bus, self.task_queue, self.permission_layer)
        self.reasoning_engine = ReasoningEngine(self.logger, self.brain, self.event_bus)
        self.workflow_engine  = WorkflowEngine(self.logger, self.event_bus)
        
        self.registry = SkillRegistry(self.shared_context)
        self.registry.auto_discover()

        # 5. Daemon Proactivo
        self.proactive_daemon = ProactiveDaemon(self.logger, self.event_bus, self.task_queue)
        self.proactive_daemon.add_monitor(SystemResourceMonitor(cpu_threshold=CPU_WARNING_THRESHOLD, ram_threshold=RAM_WARNING_THRESHOLD))
        self.proactive_daemon.add_monitor(InternetMonitor(interval=20))
        self.proactive_daemon.add_monitor(BatteryMonitor(low_threshold=BATTERY_WARNING_THRESHOLD))
        self.proactive_daemon.add_monitor(VisualAwarenessMonitor(self.logger, self.brain, interval=300))
        self.proactive_daemon.reminders.add(9, 0, "Buenos días. He iniciado los protocolos de monitoreo de sistemas.")

        self.discord_link = DiscordInterface(self.process_command)

        # --- INTERFAZ GRÁFICA ---
        # Le pasamos el método shutdown para que pueda apagar todo si seleccionas "Salir"
        self.ui = JarvisUI(self.event_bus, self.shutdown)

        # --- SUSCRIPCIONES VITALES ---
        self.event_bus.subscribe("SYSTEM_READY",  self._on_system_ready)
        self.event_bus.subscribe("SPEAK_REQUEST", self._on_speak_request)
        self.event_bus.subscribe("AUTH_REQUEST",  self._handle_auth_flow)
        self.event_bus.subscribe("RELOAD_SKILLS", lambda data: self.registry.auto_discover())
        self.event_bus.subscribe("NETWORK_STATUS", self._handle_network_change)

        atexit.register(self.shutdown)
        self.logger.info("Arquitectura modular y bus de eventos acoplados correctamente.")

    def _handle_network_change(self, data):
        is_online = data.get("online")
        self.brain.use_offline = not is_online
        status = "OFFLINE (MODO SUPERVIVENCIA)" if not is_online else "ONLINE"
        self.logger.info(f"Modo de operación cambiado a: {status}")

    def _on_system_ready(self, data):
        self.voice.speak("Sistemas visuales en línea, señor.")
        self.event_bus.publish("STATE_CHANGE", {"state": "idle"})

    def _on_speak_request(self, data):
        texto = data.get("text", "")
        if texto:
            print(f"\nJarvis: {texto}")
            self.event_bus.publish("STATE_CHANGE", {"state": "speaking"})
            self.voice.speak(texto)
            self.event_bus.publish("STATE_CHANGE", {"state": "idle"})

    def _on_wake_word_detected(self):
        # Jarvis cambia de color y pulsa más rápido para mostrar que te escucha
        self.event_bus.publish("STATE_CHANGE", {"state": "listening"})
        self.event_bus.publish("SPEAK_REQUEST", {"text": "Dime."})
        
        comando = self.listener.listen(activo=True)
        if comando:
            self.process_command(comando)
        else:
            self.event_bus.publish("STATE_CHANGE", {"state": "idle"})

    def _handle_auth_flow(self, data):
        accion = data.get("action")
        self.event_bus.publish("SPEAK_REQUEST", {"text": f"Se requiere autorización de voz para: {accion}. ¿Confirma?"})
        
        self.event_bus.publish("STATE_CHANGE", {"state": "listening"})
        respuesta_auth = self.listener.listen(activo=True)
        self.event_bus.publish("STATE_CHANGE", {"state": "processing"})

        if respuesta_auth and self.permission_layer.is_authorized(respuesta_auth):
            data.get("callback_success")()
        else:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Operación abortada por seguridad."})
        self.event_bus.publish("STATE_CHANGE", {"state": "idle"})

    def process_command(self, comando, attachment_path=None):
        self.event_bus.publish("STATE_CHANGE", {"state": "processing"})
        comando = comando.lower()
        self.logger.info(f"Procesando comando: '{comando}'")
        self.context_manager.add_command(comando)

        if "salir" in comando or "apágate" in comando:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Desconectando núcleos de ejecución. Que descanse."})
            self.shutdown()
            self.q_app.quit() # Cierra la ventana y el programa
            sys.exit(0)

        # 1. Workflows
        if self.workflow_engine.workflow_state == "WAITING_USER":
            respuesta = self.workflow_engine.resume_workflow(any(w in comando for w in CONFIRM_WORDS))
            if respuesta: self._log_and_speak(comando, respuesta)
            return

        # 2. Habilidades
        respuesta_skill = self.registry.process(comando, attachment_path)
        if respuesta_skill:
            self._log_and_speak(comando, respuesta_skill)
            return

        # 3. Razonamiento + Auto-corrección
        contexto = self.context_manager.get_system_context()
        resultado = self.self_corrector.attempt(comando, self.brain.think, (contexto + comando,))
        if resultado.response:
            self._log_and_speak(comando, resultado.response)

    def _log_and_speak(self, comando, respuesta):
        self.event_bus.publish("SPEAK_REQUEST", {"text": respuesta})
        self.episodic_memory.log_command(comando, respuesta, self.context_manager.current_topic)

    def shutdown(self):
        self.logger.info("=== APAGADO CONTROLADO ===")
        try:
            self.wake_listener.stop()
            self.proactive_daemon.stop()
            self.discord_link.stop()
            self.episodic_memory.close()
        except: pass

    def run(self):
        self.discord_link.run_in_background()
        self.proactive_daemon.start()
        
        # Mostramos la UI
        self.ui.show()
        
        self.event_bus.publish("SYSTEM_READY")
        self.wake_listener.start()
        
        # Le pasamos el control a PyQt (esto mantiene vivo el programa)
        sys.exit(self.q_app.exec_())

if __name__ == "__main__":
    # PyQt requiere que el QApplication se cree antes que cualquier otra cosa gráfica
    app = QApplication(sys.argv)
    
    jarvis = Jarvis(app)
    jarvis.run()