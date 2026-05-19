import os
import asyncio
import edge_tts
import pygame
import threading
import time

class VoiceSynthesizer:
    def __init__(self):
        # Seleccionamos la voz neuronal profesional que ya tenías
        self.voice = "es-ES-AlvaroNeural"
        pygame.mixer.init()
        
        # Candado de seguridad para la multitarea
        self.lock = threading.Lock()

    def speak(self, text):
        """Método síncrono protegido contra choques de hilos."""
        clean_text = text.replace("*", "").replace("#", "")
        
        # El candado asegura que si Jarvis quiere decir 2 cosas, haga fila y diga una a la vez
        with self.lock:
            # Ejecutamos la tarea asíncrona dentro del entorno seguro
            asyncio.run(self._generate_and_play(clean_text))

    async def _generate_and_play(self, text):
        """Genera el audio con IA neuronal y lo reproduce con nombres únicos."""
        # Generamos un nombre único usando milisegundos para evitar bloqueos de Windows
        audio_file = f"temp_speech_{int(time.time() * 1000)}.mp3"
        
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(audio_file)
            
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            
        except Exception as e:
            print(f"\n[Error de Voz] Fallo en la síntesis neuronal: {e}")
            
        finally:
            # Limpiamos el archivo temporal específico que acabamos de crear
            try:
                # Micro-pausa para asegurarnos de que pygame y Windows soltaron el archivo
                await asyncio.sleep(0.1)
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except:
                pass