import re
from pycaw.pycaw import AudioUtilities

class VolumeSkill:
    def __init__(self):
        try:
            # Nos conectamos a los controladores de audio de Windows
            dispositivo = AudioUtilities.GetSpeakers()
            
            # En las versiones modernas de pycaw, accedemos directamente al volumen
            self.volume_control = dispositivo.EndpointVolume
        except Exception as e:
            print(f"[Error Audio] No se pudo conectar a los parlantes: {e}")
            self.volume_control = None

    def change_volume(self, command):
        if not self.volume_control:
            return "No tengo acceso a los controladores de audio de este equipo."

        command = command.lower()
        
        # 1. Modo Silencio
        if "silencia" in command or "mute" in command or "apaga el volumen" in command:
            self.volume_control.SetMute(1, None)
            return "Sistema de audio silenciado."
            
        # 2. Restaurar audio
        if "desactiva el silencio" in command or "quita el silencio" in command or "devuelve el volumen" in command:
            self.volume_control.SetMute(0, None)
            return "Volumen restaurado."

        # 3. Nivel exacto (Ej: "pon el volumen al 30 por ciento")
        numeros = re.findall(r'\d+', command)
        if numeros:
            nivel = int(numeros[0])
            if 0 <= nivel <= 100:
                self.volume_control.SetMasterVolumeLevelScalar(nivel / 100.0, None)
                self.volume_control.SetMute(0, None)
                return f"Volumen configurado al {nivel} por ciento."
        
        # 4. Ajustes rápidos (subir/bajar 15%)
        vol_actual = self.volume_control.GetMasterVolumeLevelScalar()
        if "sube" in command or "aumenta" in command:
            nuevo_vol = min(vol_actual + 0.15, 1.0)
            self.volume_control.SetMasterVolumeLevelScalar(nuevo_vol, None)
            return "Volumen aumentado."
        elif "baja" in command or "disminuye" in command:
            nuevo_vol = max(vol_actual - 0.15, 0.0)
            self.volume_control.SetMasterVolumeLevelScalar(nuevo_vol, None)
            return "Volumen disminuido."

        return "No entendí a qué nivel deseas configurar el volumen."