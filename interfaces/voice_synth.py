import os
import asyncio
import edge_tts
import pygame

class VoiceSynthesizer:
    def __init__(self):
        # Seleccionamos una voz neuronal profesional
        # Otras opciones masculinas: "es-MX-JorgeNeural" (México) o "es-ES-AlvaroNeural" (España)
        self.voice = "es-ES-AlvaroNeural"
        
        # Inicializamos el mezclador de audio de pygame
        pygame.mixer.init()

    def speak(self, text):
        """Método síncrono que puede ser llamado por main.py sin problemas."""
        # Limpiamos asteriscos y formato markdown que puedan entorpecer la lectura
        clean_text = text.replace("*", "").replace("#", "")
        
        # Ejecutamos la tarea asíncrona en un hilo separado
        asyncio.run(self._generate_and_play(clean_text))

    async def _generate_and_play(self, text):
        """Genera el audio con IA neuronal y lo reproduce."""
        audio_file = "temp_speech.mp3"
        
        try:
            # Conectamos con el motor de voz neuronal
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(audio_file)
            
            # Cargamos y reproducimos el audio
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # Esperamos a que termine de hablar antes de devolver el control
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Liberamos el archivo de la memoria
            pygame.mixer.music.unload()
            
        except Exception as e:
            print(f"[Error de Voz] Fallo en la síntesis neuronal: {e}")
            
        finally:
            # Limpiamos el archivo temporal (con un pequeño delay para que Windows lo suelte)
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except:
                pass