import requests
import json

class OfflineBrain:
    def __init__(self, model="phi3"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def think(self, prompt):
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json().get("response", "")
            return "El motor local está ocupado."
        except Exception:
            return "No pude conectar con el motor local."