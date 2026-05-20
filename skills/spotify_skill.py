import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from core.skill_registry import BaseSkill

class SpotifySkill(BaseSkill):
    TRIGGERS = ["spotify"]

    def __init__(self, context):
        super().__init__(context)
        self.logger = context.logger
        load_dotenv()
        
        scope = "user-modify-playback-state user-read-playback-state"
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        except Exception as e:
            self.logger.error(f"Error al conectar con Spotify: {e}")
            self.sp = None

    def execute(self, command, attachment_path=None):
        if not self.sp:
            return "El módulo de Spotify no está configurado correctamente."
        
        cancion = command.replace("reproduce", "").replace("en spotify", "").replace("pon", "").strip()
        
        if cancion:
            try:
                resultados = self.sp.search(q=cancion, limit=1, type='track')
                if resultados['tracks']['items']:
                    track_uri = resultados['tracks']['items'][0]['uri']
                    nombre = resultados['tracks']['items'][0]['name']
                    artista = resultados['tracks']['items'][0]['artists'][0]['name']
                    
                    self.sp.start_playback(uris=[track_uri])
                    return f"Reproduciendo {nombre} de {artista} en Spotify."
                else:
                    return f"No pude encontrar la canción {cancion} en Spotify."
                    
            except spotipy.exceptions.SpotifyException:
                return "Por favor, abre la aplicación de Spotify en tu computadora o celular para poder controlarla."
            except Exception as e:
                self.logger.error(f"Excepción en el control de Spotify: {e}")
                return "Hubo un error al intentar comunicarme con Spotify."
                
        return "No escuché qué canción querías en Spotify."