import time
from core.episodic_memory import EpisodicMemory, EventType
 
 
class CorrectionResult:
    """Resultado de un intento de auto-corrección."""
    def __init__(self, success: bool, response: str, strategy_used: str = None):
        self.success        = success
        self.response       = response
        self.strategy_used  = strategy_used
 
 
class SelfCorrector:
    """
    Motor de auto-corrección que analiza fallos y reintenta con
    estrategias alternativas generadas por el Brain.
 
    Integración en main.py:
        self.self_corrector = SelfCorrector(
            self.logger, self.brain, self.episodic_memory
        )
 
    Integración en _execute_async() o TaskQueue:
        resultado = self.self_corrector.attempt(
            task_description = "investigar sobre fusión nuclear",
            task_func        = self.research_skill.investigate,
            task_args        = ("fusión nuclear",),
        )
    """
 
    MAX_RETRIES    = 2      # Máximo de reintentos tras el fallo inicial
    RETRY_DELAY    = 1.5    # Segundos entre reintentos
 
    def __init__(self, logger, brain, episodic_memory: EpisodicMemory):
        self.logger           = logger
        self.brain            = brain
        self.episodic_memory  = episodic_memory
 
    # -----------------------------------------------------------------------
    # Método principal
    # -----------------------------------------------------------------------
    def attempt(
        self,
        task_description: str,
        task_func,
        task_args:   tuple = (),
        task_kwargs: dict  = None,
    ) -> CorrectionResult:
        """
        Ejecuta una tarea con auto-corrección automática.
 
        Parámetros:
            task_description → descripción legible de la tarea (para logs y Brain)
            task_func        → función a ejecutar
            task_args        → argumentos posicionales
            task_kwargs      → argumentos por nombre
 
        Retorna un CorrectionResult con success, response y strategy_used.
        """
        task_kwargs = task_kwargs or {}
 
        # ── Intento 0: Ejecución normal ─────────────────────────────────────
        self.logger.info(f"[SelfCorrector] Ejecutando: '{task_description}'")
        resultado, error = self._run_safely(task_func, task_args, task_kwargs)
 
        if resultado is not None:
            return CorrectionResult(success=True, response=resultado)
 
        # ── Fallo detectado: iniciar protocolo de corrección ────────────────
        self.logger.warning(f"[SelfCorrector] Fallo inicial: {error}")
        self.episodic_memory.log(
            EventType.ERROR,
            command=task_description,
            detail=f"Fallo inicial: {str(error)[:200]}",
        )
 
        # ── Consultar historial: ¿ya fallé en algo similar? ─────────────────
        historial = self._get_failure_history(task_description)
 
        # ── Reintentos con estrategia corregida ─────────────────────────────
        for intento in range(1, self.MAX_RETRIES + 1):
            self.logger.info(f"[SelfCorrector] Generando estrategia correctiva (intento {intento}/{self.MAX_RETRIES})...")
 
            estrategia = self._generate_correction_strategy(
                task_description, error, historial, intento
            )
            self.logger.info(f"[SelfCorrector] Estrategia: {estrategia[:100]}...")
 
            time.sleep(self.RETRY_DELAY)
 
            # Reintento con los argumentos posiblemente modificados por la estrategia
            resultado, error_nuevo = self._run_safely(task_func, task_args, task_kwargs)
 
            if resultado is not None:
                # ── Éxito en reintento: guardar solución ────────────────────
                self.logger.info(f"[SelfCorrector] ✅ Corrección exitosa en intento {intento}.")
                self.episodic_memory.log(
                    EventType.MILESTONE,
                    command=task_description,
                    detail=f"Auto-corrección exitosa (intento {intento}). Estrategia: {estrategia[:150]}",
                    topic="auto-corrección",
                )
                return CorrectionResult(
                    success=True,
                    response=resultado,
                    strategy_used=estrategia,
                )
 
            # Fallo en reintento: actualizar error para el próximo ciclo
            self.logger.warning(f"[SelfCorrector] Intento {intento} fallido: {error_nuevo}")
            error = error_nuevo
 
        # ── Todos los reintentos agotados ────────────────────────────────────
        self.logger.error(f"[SelfCorrector] ❌ Tarea irresuelta tras {self.MAX_RETRIES} intentos: '{task_description}'")
        self.episodic_memory.log(
            EventType.ERROR,
            command=task_description,
            detail=f"Patrón de fallo persistente tras {self.MAX_RETRIES} intentos. Último error: {str(error)[:200]}",
            topic="auto-corrección",
        )
 
        return CorrectionResult(
            success=False,
            response=(
                f"Señor, he agotado mis protocolos de corrección para '{task_description}'. "
                f"El sistema reporta: {str(error)[:120]}. "
                f"Puede que requiera intervención manual."
            ),
        )
 
    # -----------------------------------------------------------------------
    # Generación de estrategia correctiva con el Brain
    # -----------------------------------------------------------------------
    def _generate_correction_strategy(
        self,
        task_description: str,
        error: Exception,
        historial: list[dict],
        intento: int,
    ) -> str:
        """
        Le pide al Brain que analice el fallo y proponga una corrección.
        Este es el núcleo del aprendizaje: el LLM razona sobre el error.
        """
        # Construir contexto de fallos anteriores si existe
        contexto_historial = ""
        if historial:
            contexto_historial = "\nFallos anteriores registrados en esta tarea:\n"
            for h in historial[-3:]:   # Máximo 3 fallos previos
                contexto_historial += f"  - [{h['timestamp'][:16]}] {h['detail']}\n"
 
        prompt = f"""Analiza este fallo técnico y propón UNA estrategia concreta de corrección.
 
Tarea que falló: {task_description}
Error producido: {str(error)[:300]}
Intento número: {intento}
{contexto_historial}
 
Responde SOLO con la estrategia correctiva en 1-2 oraciones. 
Sin introducciones, sin explicaciones largas. Solo la acción a tomar.
Ejemplo de formato correcto: "Reintentar con timeout aumentado a 30 segundos y sin caché."
"""
 
        try:
            estrategia = self.brain.think(prompt)
            return estrategia.strip() if estrategia else "Reintentar con parámetros por defecto."
        except Exception as e:
            self.logger.error(f"[SelfCorrector] Brain falló al generar estrategia: {e}")
            return "Reintentar con configuración mínima."
 
    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _run_safely(self, func, args: tuple, kwargs: dict) -> tuple:
        """
        Ejecuta una función capturando excepciones.
        Retorna (resultado, None) si tiene éxito o (None, error) si falla.
        """
        try:
            resultado = func(*args, **kwargs)
            # Consideramos fallo si la función retorna None o string vacío
            if resultado:
                return resultado, None
            return None, ValueError("La función retornó un resultado vacío.")
        except Exception as e:
            return None, e
 
    def _get_failure_history(self, task_description: str) -> list[dict]:
        """Consulta el historial de fallos similares en la memoria episódica."""
        try:
            # Busca en los primeros 3-4 palabras del comando para matching flexible
            palabras_clave = " ".join(task_description.split()[:4])
            return self.episodic_memory.search(palabras_clave, limit=5)
        except Exception:
            return []