import sqlite3
import datetime
from pathlib import Path
 
 
# ---------------------------------------------------------------------------
# Tipos de evento que Jarvis puede registrar
# ---------------------------------------------------------------------------
class EventType:
    COMMAND      = "COMMAND"       # Comando recibido + respuesta generada
    ERROR        = "ERROR"         # Fallo en cualquier módulo
    MILESTONE    = "MILESTONE"     # Hito importante (tarea completada, doc creado)
    SYSTEM       = "SYSTEM"        # Arranque, apagado, cambio de estado
    PROACTIVE    = "PROACTIVE"     # Alerta generada por el daemon proactivo
 
 
# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------
class EpisodicMemory:
    """
    Diario cronológico de JARVIS basado en SQLite.
 
    Integración con tu arquitectura:
        # En __init__ de Jarvis, después de crear event_bus:
        self.episodic_memory = EpisodicMemory(self.logger)
        self.episodic_memory.attach(self.event_bus)
 
        # El ContextManager la consulta automáticamente:
        self.context_manager = ContextManager(self.logger, self.episodic_memory)
    """
 
    DB_PATH = Path("jarvis_memory.db")
 
    def __init__(self, logger):
        self.logger = logger
        self._conn  = self._initialize_db()
        self.logger.info("[EpisodicMemory] Base de datos episódica lista.")
 
    # -----------------------------------------------------------------------
    # Inicialización de la base de datos
    # -----------------------------------------------------------------------
    def _initialize_db(self) -> sqlite3.Connection:
        """Crea la DB y la tabla si no existen. Idempotente."""
        conn = sqlite3.connect(
            self.DB_PATH,
            check_same_thread=False,   # Necesario para uso multihilo con TaskQueue
        )
        conn.row_factory = sqlite3.Row  # Resultados como diccionarios
 
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episodic_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                event_type  TEXT    NOT NULL,
                topic       TEXT,
                command     TEXT,
                response    TEXT,
                detail      TEXT
            )
        """)
 
        # Índice para acelerar búsquedas por fecha y tipo
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON episodic_log(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_type
            ON episodic_log(event_type)
        """)
 
        conn.commit()
        return conn
 
    # -----------------------------------------------------------------------
    # Escritura
    # -----------------------------------------------------------------------
    def log(
        self,
        event_type: str,
        command:    str  = None,
        response:   str  = None,
        topic:      str  = None,
        detail:     str  = None,
    ):
        """
        Registra un evento en el diario.
 
        Parámetros:
            event_type → usar las constantes de EventType
            command    → texto del comando del usuario
            response   → respuesta generada por Jarvis
            topic      → tema activo en ese momento
            detail     → información adicional libre
        """
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
 
        try:
            self._conn.execute(
                """
                INSERT INTO episodic_log
                    (timestamp, event_type, topic, command, response, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, event_type, topic, command, response, detail),
            )
            self._conn.commit()
        except Exception as e:
            self.logger.error(f"[EpisodicMemory] Error al escribir en diario: {e}")
 
    # -----------------------------------------------------------------------
    # Lectura
    # -----------------------------------------------------------------------
    def get_recent(self, limit: int = 10) -> list[dict]:
        """Devuelve los N eventos más recientes."""
        cursor = self._conn.execute(
            """
            SELECT * FROM episodic_log
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
 
    def get_last_session(self) -> list[dict]:
        """
        Devuelve los eventos de la última sesión de trabajo
        (desde el último SYSTEM:START hasta ahora).
        """
        cursor = self._conn.execute(
            """
            SELECT * FROM episodic_log
            WHERE timestamp >= (
                SELECT timestamp FROM episodic_log
                WHERE event_type = 'SYSTEM' AND detail = 'START'
                ORDER BY timestamp DESC
                LIMIT 1
            )
            ORDER BY timestamp ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
 
    def get_by_topic(self, topic: str, limit: int = 5) -> list[dict]:
        """Devuelve eventos relacionados con un tema específico."""
        cursor = self._conn.execute(
            """
            SELECT * FROM episodic_log
            WHERE topic LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (f"%{topic}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]
 
    def get_by_date(self, date_str: str) -> list[dict]:
        """
        Devuelve eventos de una fecha específica.
        date_str formato: 'YYYY-MM-DD'
        """
        cursor = self._conn.execute(
            """
            SELECT * FROM episodic_log
            WHERE timestamp LIKE ?
            ORDER BY timestamp ASC
            """,
            (f"{date_str}%",),
        )
        return [dict(row) for row in cursor.fetchall()]
 
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Búsqueda de texto libre en comandos y respuestas."""
        cursor = self._conn.execute(
            """
            SELECT * FROM episodic_log
            WHERE command LIKE ?
               OR response LIKE ?
               OR topic LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]
 
    # -----------------------------------------------------------------------
    # Resumen para inyectar al Brain (el más importante)
    # -----------------------------------------------------------------------
    def get_context_summary(self, max_events: int = 5) -> str:
        """
        Genera un bloque de texto con los eventos recientes, listo para
        ser inyectado en el system prompt del Brain.
 
        El ContextManager llama a este método antes de cada consulta.
        """
        eventos = self.get_recent(limit=max_events)
 
        if not eventos:
            return ""
 
        lineas = ["Registro de actividad reciente:"]
        for e in reversed(eventos):   # Cronológico: más antiguo primero
            ts    = e["timestamp"][:16].replace("T", " ")   # 'YYYY-MM-DD HH:MM'
            etype = e["event_type"]
 
            if etype == EventType.COMMAND and e["command"]:
                lineas.append(f"  [{ts}] Comando: '{e['command'][:80]}'"
                              + (f" — Tema: {e['topic']}" if e["topic"] else ""))
 
            elif etype == EventType.MILESTONE and e["detail"]:
                lineas.append(f"  [{ts}] Completado: {e['detail']}")
 
            elif etype == EventType.ERROR and e["detail"]:
                lineas.append(f"  [{ts}] Error registrado: {e['detail'][:60]}")
 
            elif etype == EventType.SYSTEM:
                lineas.append(f"  [{ts}] Sistema: {e['detail']}")
 
        return "\n".join(lineas)
 
    # -----------------------------------------------------------------------
    # Integración con EventBus
    # -----------------------------------------------------------------------
    def attach(self, event_bus):
        """
        Se suscribe a los eventos del bus para registrar automáticamente
        lo más importante sin que main.py tenga que llamar a .log() manual.
 
        Llama a este método UNA VEZ en el __init__ de Jarvis:
            self.episodic_memory.attach(self.event_bus)
        """
        event_bus.subscribe("SPEAK_REQUEST",  self._on_speak)
        event_bus.subscribe("SYSTEM_READY",   self._on_system_ready)
        event_bus.subscribe("TASK_COMPLETE",  self._on_task_complete)
        self.logger.info("[EpisodicMemory] Suscrito al EventBus.")
 
    def _on_speak(self, data: dict):
        """Registra cada vez que Jarvis habla (respuesta proactiva del daemon)."""
        texto = data.get("text", "") if isinstance(data, dict) else str(data)
        # Solo guarda alertas del daemon, no cada respuesta de comando
        # (esas se guardan en log_command directamente)
        if len(texto) < 200:   # Las respuestas largas son comandos normales
            self.log(EventType.PROACTIVE, response=texto)
 
    def _on_system_ready(self, data):
        self.log(EventType.SYSTEM, detail="START")
        self.logger.info("[EpisodicMemory] Inicio de sesión registrado.")
 
    def _on_task_complete(self, data: dict):
        if isinstance(data, dict):
            self.log(
                EventType.MILESTONE,
                topic=data.get("topic"),
                detail=data.get("description", "Tarea completada"),
            )
 
    # -----------------------------------------------------------------------
    # Método de conveniencia para main.py
    # -----------------------------------------------------------------------
    def log_command(self, command: str, response: str, topic: str = None):
        """
        Registra un ciclo comando→respuesta completo.
        Llámalo al final de process_command() en main.py:
 
            respuesta = self.process_command(comando)
            self.episodic_memory.log_command(comando, respuesta,
                                             self.context_manager.current_topic)
        """
        self.log(
            EventType.COMMAND,
            command=command[:500],
            response=response[:500] if response else None,
            topic=topic,
        )
 
    def close(self):
        """Cierra la conexión a la DB. Llamar en el shutdown de Jarvis."""
        self.log(EventType.SYSTEM, detail="SHUTDOWN")
        self._conn.close()
        self.logger.info("[EpisodicMemory] Conexión cerrada.")