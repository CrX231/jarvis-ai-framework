import webbrowser

class BrowserSkill:
    def __init__(self):
        # Un diccionario básico con las páginas más comunes
        self.sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "whatsapp": "https://web.whatsapp.com",
            "facebook": "https://www.facebook.com"
        }

    def open_site(self, command):
        # Primero revisamos si quieres abrir una página específica de nuestra lista
        for site_name, url in self.sites.items():
            if site_name in command:
                webbrowser.open(url)
                return f"Abriendo {site_name}."
        
        # Si no es una página de la lista, asumimos que es una búsqueda general en Google
        busqueda = command.replace("abre", "").replace("busca", "").replace("en internet", "").strip()
        
        if busqueda:
            # Formateamos la URL para hacer una búsqueda directa
            url = f"https://www.google.com/search?q={busqueda}"
            webbrowser.open(url)
            return f"Buscando {busqueda} en la web."
            
        return "No entendí qué página o búsqueda quieres hacer."