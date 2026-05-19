import time
import datetime
import threading
import requests
import psutil
from dataclasses import dataclass
 
 
# ===========================================================================
# MONITORES — cada uno solo sabe dos cosas:
#   1. Cuándo verificar (interval)
#   2. Qué publicar si algo falla (publica SPEAK_REQUEST al bus)
# ===========================================================================
 
class BaseMonitor:
    """
    Clase base. Todos los monitores heredan de aquí.
    El daemon llama a .tick(event_bus) en el intervalo configurado.
    """
    def __init__(self, name: str, interval_seconds: int):
        self.name      = name
        self.interval  = interval_seconds
        self._last_run = 0.0
 
    def is_due(self) -> bool:
        """¿Ya pasó suficiente tiempo desde la última ejecución?"""
        return (time.time() - self._last_run) >= self.interval
 
    def mark_ran(self):
        self._last_run = time.time()
 
    def check(self) -> str | None:
        """
        Lógica de comprobación.
        Retorna un mensaje si hay algo que reportar, None si todo OK.
        """
        raise NotImplementedError
 
    def tick(self, event_bus):
        """
        Llamado por el scheduler. Si hay algo que reportar,
        lo inyecta directamente al EventBus como SPEAK_REQUEST.
        """
        if not self.is_due():
            return
        self.mark_ran()
        try:
            mensaje = self.check()
            if mensaje:
                event_bus.publish("SPEAK_REQUEST", {"text": mensaje})
        except Exception as e:
            event_bus.logger.warning(f"[Monitor:{self.name}] Error en check: {e}")
 
 
# ---------------------------------------------------------------------------
# Monitor: CPU y RAM
# ---------------------------------------------------------------------------
class SystemResourceMonitor(BaseMonitor):
    def __init__(self, cpu_threshold=85, ram_threshold=90, interval=30):
        super().__init__("Sistema", interval)
        self.cpu_thresh = cpu_threshold
        self.ram_thresh = ram_threshold
 
    def check(self) -> str | None:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
 
        alertas = []
        if cpu > self.cpu_thresh:
            alertas.append(f"CPU al {cpu:.0f} por ciento")
        if ram > self.ram_thresh:
            alertas.append(f"RAM al {ram:.0f} por ciento")
 
        if alertas:
            return "Alerta de sistema: " + " y ".join(alertas) + ". Considera cerrar aplicaciones."
        return None
 
 
# ---------------------------------------------------------------------------
# Monitor: Conectividad a internet
# ---------------------------------------------------------------------------
class InternetMonitor(BaseMonitor):
    def __init__(self, interval=20):
        super().__init__("Internet", interval)
        self._last_state = True
 
    def _ping(self) -> bool:
        try:
            requests.get("https://www.google.com", timeout=4)
            return True
        except Exception:
            return False
 
    def check(self) -> str | None:
        online = self._ping()
        if not online and self._last_state:
            self._last_state = False
            return "Se perdió la conexión a internet."
        if online and not self._last_state:
            self._last_state = True
            return "La conexión a internet se restableció."
        return None
 
 
# ---------------------------------------------------------------------------
# Monitor: Batería
# ---------------------------------------------------------------------------
class BatteryMonitor(BaseMonitor):
    def __init__(self, low_threshold=20, interval=60):
        super().__init__("Batería", interval)
        self.threshold = low_threshold
        self._alerted  = False
 
    def check(self) -> str | None:
        bat = psutil.sensors_battery()
        if not bat:
            return None
        if bat.percent <= self.threshold and not bat.power_plugged and not self._alerted:
            self._alerted = True
            return f"Batería al {bat.percent:.0f} por ciento. Por favor conecta el cargador."
        if bat.power_plugged:
            self._alerted = False
        return None
 
 
# ---------------------------------------------------------------------------
# Monitor: Sitio web caído
# ---------------------------------------------------------------------------
class WebsiteMonitor(BaseMonitor):
    def __init__(self, url: str, interval=120):
        super().__init__(f"Web({url})", interval)
        self.url     = url
        self._was_up = True
 
    def check(self) -> str | None:
        try:
            resp  = requests.get(self.url, timeout=8)
            is_up = resp.status_code < 500
        except Exception:
            is_up = False
        if not is_up and self._was_up:
            self._was_up = False
            return f"El sitio {self.url} parece estar caído."
        if is_up and not self._was_up:
            self._was_up = True
            return f"El sitio {self.url} volvió a estar en línea."
        return None
 
 
# ===========================================================================
# RECORDATORIOS
# ===========================================================================
 
@dataclass
class Reminder:
    hour:    int
    minute:  int
    message: str
    repeat:  bool = True
    fired:   bool = False
 
 
class ReminderMonitor(BaseMonitor):
    """
    Gestiona todos los recordatorios del día.
    Se comporta como un monitor más: el scheduler lo llama cada 30s.
    """
    def __init__(self):
        super().__init__("Recordatorios", interval=30)
        self._reminders: list[Reminder] = []
 
    def add(self, hour: int, minute: int, message: str, repeat: bool = True):
        self._reminders.append(Reminder(hour, minute, message, repeat))
 
    def add_in(self, minutes: int, message: str):
        """Recordatorio relativo: en N minutos desde ahora, sin repetición."""
        target = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        self._reminders.append(
            Reminder(target.hour, target.minute, message, repeat=False)
        )
 
    def check(self) -> str | None:
        ahora = datetime.datetime.now()
        for r in self._reminders:
            if r.fired and not r.repeat:
                continue
            es_la_hora = (ahora.hour == r.hour and ahora.minute == r.minute)
            if es_la_hora and not r.fired:
                r.fired = True
                return r.message
            if not es_la_hora and r.fired and r.repeat:
                r.fired = False
        return None
 
 
# ===========================================================================
# PROACTIVE DAEMON
# ===========================================================================
 
class ProactiveDaemon:
    """
    Orquestador que delega TODO en tu EventBus y TaskQueue existentes.
 
    Uso:
        event_bus.subscribe("SPEAK_REQUEST", jarvis.speak)
 
        daemon = ProactiveDaemon(logger, event_bus, task_queue)
        daemon.add_monitor(SystemResourceMonitor())
        daemon.add_monitor(InternetMonitor())
        daemon.add_monitor(BatteryMonitor())
        daemon.reminders.add(9, 0, "Buenos días.")
        daemon.reminders.add_in(minutes=30, message="Han pasado 30 minutos.")
        daemon.start()
    """
 
    def __init__(self, logger, event_bus, task_queue):
        self.logger     = logger
        self.event_bus  = event_bus
        self.task_queue = task_queue
        self._monitors: list[BaseMonitor] = []
        self._stop      = threading.Event()
 
        # El gestor de recordatorios es un monitor más
        self.reminders  = ReminderMonitor()
        self._monitors.append(self.reminders)
 
    def add_monitor(self, monitor: BaseMonitor):
        self._monitors.append(monitor)
        self.logger.info(f"[Daemon] Monitor registrado: {monitor.name}")
 
    def start(self):
        """Delega el scheduler a la TaskQueue. No crea hilos nuevos."""
        self._stop.clear()
        self.task_queue.add_task(self._scheduler_loop)
        self.logger.info(
            f"[Daemon] ✅ Iniciado con {len(self._monitors)} monitores "
            f"(encolado en TaskQueue)."
        )
 
    def stop(self):
        self._stop.set()
        self.logger.info("[Daemon] 🛑 Detenido.")
 
    def _scheduler_loop(self):
        """
        Loop ligero dentro del worker de TaskQueue.
        Comprueba cada segundo qué monitores tienen trabajo pendiente.
        """
        self.logger.info("[Daemon] Scheduler activo.")
        while not self._stop.is_set():
            for monitor in self._monitors:
                monitor.tick(self.event_bus)
            time.sleep(1)
        self.logger.info("[Daemon] Scheduler finalizado.")
 
 
# ===========================================================================
# DEMO — ejecuta este archivo directamente para probar
# ===========================================================================
if __name__ == "__main__":
    import logging
    import queue
 
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
    logger = logging.getLogger("JARVIS")
 
    # Tus clases originales (sin modificar)
    class EventBus:
        def __init__(self, logger):
            self.logger      = logger
            self.subscribers = {}
 
        def subscribe(self, event_type, callback_function):
            self.subscribers.setdefault(event_type, []).append(callback_function)
            self.logger.info(f"Nuevo suscriptor adherido al evento: {event_type}")
 
        def publish(self, event_type, data=None):
            if event_type in self.subscribers:
                self.logger.info(f"Disparando evento: {event_type}")
                for callback in self.subscribers[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.error(f"Fallo en suscriptor de {event_type}: {e}")
 
    class TaskQueue:
        def __init__(self, logger):
            self.task_queue    = queue.Queue()
            self.logger        = logger
            self.worker_thread = threading.Thread(
                target=self._process_queue, daemon=True
            )
            self.worker_thread.start()
            self.logger.info("Cola de Tareas inicializada.")
 
        def add_task(self, target_function, *args, **kwargs):
            self.task_queue.put((target_function, args, kwargs))
            self.logger.info(f"Tarea encolada: {target_function.__name__}")
 
        def _process_queue(self):
            while True:
                func, args, kwargs = self.task_queue.get()
                try:
                    self.logger.info(f"Ejecutando: {func.__name__}")
                    func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Fallo en {func.__name__}: {e}")
                finally:
                    self.task_queue.task_done()
 
    # Setup
    event_bus  = EventBus(logger)
    task_queue = TaskQueue(logger)
 
    # ← Una sola línea conecta el daemon con tu TTS
    event_bus.subscribe("SPEAK_REQUEST", lambda msg: print(f"\n🤖 JARVIS: {msg}\n"))
 
    # Configurar monitores
    daemon = ProactiveDaemon(logger, event_bus, task_queue)
    daemon.add_monitor(SystemResourceMonitor(cpu_threshold=80, interval=15))
    daemon.add_monitor(InternetMonitor(interval=20))
    daemon.add_monitor(BatteryMonitor(low_threshold=25))
    daemon.reminders.add(9,  0,  "Buenos días. ¿Qué tienes planeado hoy?")
    daemon.reminders.add(13, 0,  "Recuerda tomar un descanso para almorzar.", repeat=True)
    daemon.reminders.add_in(minutes=1, message="Un minuto desde que arrancaste Jarvis.")
 
    daemon.start()
 
    print("\n[DEMO] Ctrl+C para salir.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()