import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

class SpotifySkill:
    def __init__(self):
        load_dotenv()
        # Permisos necesarios para buscar y modificar la reproducción actual
        scope = "user-modify-playback-state user-read-playback-state"
        
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        except Exception as e:
            print(f"Error al conectar con Spotify: {e}")
            self.sp = None

    def play_music(self, command):
        if not self.sp:
            return "El módulo de Spotify no está configurado correctamente."
        
        # Limpiamos el comando
        cancion = command.replace("reproduce", "").replace("en spotify", "").replace("pon", "").strip()
        
        if cancion:
            try:
                # Buscamos la canción (obtiene el primer resultado)
                resultados = self.sp.search(q=cancion, limit=1, type='track')
                if resultados['tracks']['items']:
                    track_uri = resultados['tracks']['items'][0]['uri']
                    nombre = resultados['tracks']['items'][0]['name']
                    artista = resultados['tracks']['items'][0]['artists'][0]['name']
                    
                    # Le da play a la canción en tu dispositivo activo
                    self.sp.start_playback(uris=[track_uri])
                    return f"Reproduciendo {nombre} de {artista} en Spotify."
                else:
                    return f"No pude encontrar la canción {cancion} en Spotify."
                    
            except spotipy.exceptions.SpotifyException:
                # La API requiere que haya una app de Spotify abierta para recibir el audio
                return "Por favor, abre la aplicación de Spotify en tu computadora o celular para poder controlarla."
            except Exception as e:
                return "Hubo un error al intentar comunicarme con Spotify."
                
        return "No escuché qué canción querías en Spotify."