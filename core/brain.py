import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

class Brain:
    def __init__(self):
        load_dotenv()
        # Apuntando a tu variable original
        api_key = os.getenv("LLM_API_KEY")
        
        # --- EL ALMA DE J.A.R.V.I.S. ---
        instruccion_sistema = (
            "Eres J.A.R.V.I.S., el asistente de inteligencia artificial avanzado y leal de Carlos. "
            "Tu comportamiento es idéntico al J.A.R.V.I.S. de las películas de Iron Man: eres altamente educado, "
            "formal, lógico, eficiente y tienes un sutil y seco sentido del humor británico. "
            "Dirígete a Carlos como 'Señor' o 'Carlos'. "
            "Tus respuestas deben ser concisas, directas al punto y profesionales. "
            "Nunca menciones que eres un 'modelo de lenguaje', una 'IA' genérica o que fuiste creado por Google. "
            "Eres un sistema informático integrado de alto rendimiento."
        )
        
        # Modelo actualizado
        self.model_id = 'gemini-2.5-flash'
        
        self.client = genai.Client(api_key=api_key)
        
        self.config = types.GenerateContentConfig(
            system_instruction=instruccion_sistema,
        )
        
        self.chat = self.client.chats.create(
            model=self.model_id, 
            config=self.config
        )

    def think(self, prompt, image=None):
        max_retries = 3      # Número máximo de intentos antes de rendirse
        base_delay = 2       # Segundos de espera para el primer reintento

        for intento in range(max_retries):
            try:
                if image:
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=[prompt, image],
                        config=self.config
                    )
                    return response.text.replace("*", "")
                else:
                    response = self.chat.send_message(prompt)
                    return response.text.replace("*", "")
                    
            except Exception as e:
                error_msg = str(e).upper()
                
                # Si el error es de sobrecarga (503) o demasiadas peticiones (429)
                if "503" in error_msg or "429" in error_msg or "UNAVAILABLE" in error_msg:
                    if intento < max_retries - 1:
                        # Calculamos el retroceso exponencial: 2s, luego 4s...
                        tiempo_espera = base_delay * (2 ** intento)
                        print(f"\n[Sistema] Enlace neuronal saturado. Reintentando conexión en {tiempo_espera}s... (Intento {intento + 1}/{max_retries})")
                        time.sleep(tiempo_espera)
                        continue # Vuelve al inicio del bucle for para intentar de nuevo
                
                # Si es un error distinto (ej. falta de internet) o se agotaron los intentos, reporta la falla
                return f"He encontrado un error de procesamiento en mis sistemas centrales, señor: {e}"