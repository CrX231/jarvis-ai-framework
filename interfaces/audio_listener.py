import time
import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
 
 
# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SAMPLE_RATE     = 16000   # Whisper siempre trabaja a 16 kHz
SILENCE_THRESH  = 0.015   # Umbral de volumen para detectar silencio
SILENCE_SECONDS = 1.8     # Segundos de silencio para cortar la grabación
MAX_SECONDS     = 30      # Corte de seguridad: grabación máxima
CHANNELS        = 1
 
 
class AudioListener:
    """
    Escucha el micrófono, detecta cuando hablas, graba hasta que te callas,
    y transcribe con faster-whisper localmente.
    """
 
    def __init__(self, logger, model_name: str = "tiny"):
        self.logger     = logger
        self.model_name = model_name
        self.model      = None
        self._ready     = False
 
    # -----------------------------------------------------------------------
    # Carga del modelo
    # -----------------------------------------------------------------------
    def initialize(self):
        """
        Descarga y carga el modelo en memoria.
        
        Parámetros clave para hardware limitado:
          device="cpu"       → sin GPU
          compute_type="int8" → cuantización: usa ~150 MB RAM con tiny
                                (en vez de ~500 MB con float32)
        """
        self.logger.info(f"[STT] Cargando faster-whisper '{self.model_name}' en CPU con int8...")
        self.logger.info("[STT] (Primera vez descarga el modelo, luego es instantáneo)")
 
        self.model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type="int8",   # Clave para PCs con poca RAM
        )
 
        self._ready = True
        self.logger.info(f"[STT] ✅ Modelo '{self.model_name}' listo. RAM: ~150 MB")
 
    # -----------------------------------------------------------------------
    # Grabación con detección de silencio
    # -----------------------------------------------------------------------
    def _record_until_silence(self) -> np.ndarray | None:
        """
        Graba audio del micrófono.
        Espera a que empieces a hablar y para cuando te callas.
        """
        self.logger.info("[STT] 🎙️  Escuchando...")
 
        frames        = []
        silent_chunks = 0
        speaking      = False
        max_chunks    = int(MAX_SECONDS * SAMPLE_RATE / 1024)
        silence_limit = int(SILENCE_SECONDS * SAMPLE_RATE / 1024)
 
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype="float32", blocksize=1024) as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(1024)
                volume   = np.abs(chunk).mean()
 
                if volume > SILENCE_THRESH:
                    speaking      = True
                    silent_chunks = 0
                    frames.append(chunk.copy())
                elif speaking:
                    frames.append(chunk.copy())
                    silent_chunks += 1
                    if silent_chunks >= silence_limit:
                        break
 
        if not frames or not speaking:
            return None
 
        return np.concatenate(frames, axis=0).flatten()
 
    # -----------------------------------------------------------------------
    # Transcripción — API diferente a openai-whisper
    # -----------------------------------------------------------------------
    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe un array numpy con faster-whisper.
        
        Diferencia importante vs openai-whisper:
          faster-whisper devuelve (segments, info) donde segments es un
          iterador — hay que recorrerlo para armar el texto completo.
        """
        audio_float = audio.astype(np.float32)
 
        # faster-whisper devuelve un generador de segmentos + metadata
        segments, info = self.model.transcribe(
            audio_float,
            language="es",           # Forzar español
            beam_size=1,             # Beam size 1 = más rápido en CPU
            vad_filter=True,         # Filtra silencio automáticamente
            vad_parameters=dict(
                min_silence_duration_ms=500
            ),
        )
 
        # Unir todos los segmentos en un solo string
        texto = " ".join(seg.text.strip() for seg in segments)
        return texto.strip()
 
    # -----------------------------------------------------------------------
    # Método principal
    # -----------------------------------------------------------------------
    def listen(self, activo: bool = True) -> str | None:
        """
        Escucha UNA vez y devuelve el texto transcrito.
        Retorna None si no detectó voz o si activo=False.
        """
        if not activo:
            return None
        if not self._ready:
            self.logger.error("[STT] Modelo no inicializado. Llama a initialize() primero.")
            return None
 
        audio = self._record_until_silence()
        if audio is None:
            return None
 
        self.logger.info("[STT] 🔄 Transcribiendo...")
        inicio = time.time()
        texto  = self.transcribe(audio)
        duracion = time.time() - inicio
 
        if texto:
            self.logger.info(f"[STT] ✅ '{texto}' ({duracion:.1f}s)")
        return texto or None
 
    # -----------------------------------------------------------------------
    # Modo continuo
    # -----------------------------------------------------------------------
    def listen_loop(self, callback, stop_event: threading.Event | None = None):
        """
        Escucha indefinidamente. Cada vez que detecta voz llama a callback(texto).
 
        Uso:
            stop = threading.Event()
            t = threading.Thread(target=stt.listen_loop,
                                 args=(jarvis.process, stop), daemon=True)
            t.start()
            ...
            stop.set()
        """
        self.logger.info("[STT] 🔁 Modo escucha continua activado.")
        while not (stop_event and stop_event.is_set()):
            texto = self.listen()
            if texto:
                callback(texto)
        self.logger.info("[STT] Escucha continua detenida.")
 
 
# ---------------------------------------------------------------------------
# Wake word con tiny (muy bajo consumo)
# ---------------------------------------------------------------------------
class WakeWordListener:
    """
    Escucha continuamente con tiny + int8 (consume muy poca RAM y CPU)
    y activa el STT completo solo cuando detecta "jarvis".
    
    Esto evita que el modelo esté transcribiendo audio todo el tiempo.
    """
 
    WAKE_WORDS = ["jarvis", "oye jarvis", "hey jarvis", "hola jarvis"]
 
    def __init__(self, logger, on_wake_callback, wake_words: list[str] | None = None):
        self.logger      = logger
        self.on_wake     = on_wake_callback
        self.wake_words  = wake_words or self.WAKE_WORDS
        self._model      = None
        self._stop_event = threading.Event()
 
    def initialize(self):
        self.logger.info("[WakeWord] Cargando tiny int8 para detección de activación...")
        # tiny + int8 = ~80 MB RAM, corre en tiempo real en cualquier CPU
        self._model = WhisperModel("tiny", device="cpu", compute_type="int8")
        self.logger.info("[WakeWord] ✅ Listo (~80 MB RAM).")
 
    def _contains_wake_word(self, texto: str) -> bool:
        return any(w in texto.lower() for w in self.wake_words)
 
    def _quick_transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self._model.transcribe(
            audio.astype(np.float32),
            language="es",
            beam_size=1,
            vad_filter=True,
        )
        return " ".join(seg.text.strip() for seg in segments).lower()
 
    def start(self) -> threading.Thread:
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        return t
 
    def stop(self):
        self._stop_event.set()
 
    def _run(self):
        self.logger.info(f"[WakeWord] 👂 Esperando: {self.wake_words}")
 
        while not self._stop_event.is_set():
            frames = []
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                                dtype="float32", blocksize=1024) as stream:
                for _ in range(int(2.5 * SAMPLE_RATE / 1024)):
                    chunk, _ = stream.read(1024)
                    frames.append(chunk.copy())
 
            audio = np.concatenate(frames, axis=0).flatten()
 
            # Ignorar si no hay volumen real (evita procesar silencio)
            if np.abs(audio).mean() < 0.008:
                continue
 
            texto = self._quick_transcribe(audio)
            if self._contains_wake_word(texto):
                self.logger.info(f"[WakeWord] 🟢 Activado: '{texto}'")
                self.on_wake()
 
 
# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logger = logging.getLogger("JARVIS")
 
    stt = AudioListener(logger, model_name="tiny")
    stt.initialize()
 
    print("\n[DEMO] Habla algo. Ctrl+C para salir.\n")
    try:
        while True:
            texto = stt.listen()
            if texto:
                print(f"Tú: {texto}\n")
    except KeyboardInterrupt:
        print("\nDemo finalizado.")