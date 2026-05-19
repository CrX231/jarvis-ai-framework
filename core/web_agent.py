"""
web_agent.py — Módulo de navegación autónoma para JARVIS
=========================================================
Estrategia en capas (de menos a más agresivo):
  Capa 1 → ddgs  (API interna de DDG, casi nunca bloqueada)
  Capa 2 → httpx + headers rotatorios  (para extraer páginas)
  Capa 3 → Playwright con stealth avanzado  (último recurso)
"""

import time
import random
import httpx
import re
from bs4 import BeautifulSoup
from ddgs import DDGS

# ---------------------------------------------------------------------------
# Cabeceras que rotan para parecer un humano real
# ---------------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

def _get_headers() -> dict:
    """Genera headers que imitan un navegador real."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }


# ---------------------------------------------------------------------------
# Limpieza de HTML
# ---------------------------------------------------------------------------
def _clean_html(html_content: str, max_chars: int = 12000) -> str:
    """Extrae solo el texto útil de una página web."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Eliminar basura visual
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "aside", "iframe", "form", "button"]):
        tag.decompose()

    # Intentar extraer el artículo principal primero
    main_content = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id="content")
        or soup.find(class_="content")
        or soup.find("body")
    )

    texto = (main_content or soup).get_text(separator=" ", strip=True)

    # Limpiar espacios múltiples
    texto = re.sub(r"\s{2,}", " ", texto)

    return texto[:max_chars]


# ---------------------------------------------------------------------------
# CAPA 1: Búsqueda con ddgs (sin scraping de buscador)
# ---------------------------------------------------------------------------
def _search_ddg(query: str, max_results: int = 5) -> list[dict]:
    """
    Usa la librería ddgs para obtener resultados.
    Devuelve lista de dicts con 'title', 'url', 'snippet'.
    Esta capa NO scrapea nada; usa la API interna de DDG.
    """
    results = []
    try:
        ddgs = DDGS()
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url":   r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    except Exception as e:
        print(f"[WebAgent] Error en la API de DDGS: {e}")
        
    return results


# ---------------------------------------------------------------------------
# CAPA 2: Extracción de página con httpx (rápido, sin browser)
# ---------------------------------------------------------------------------
def _fetch_page_httpx(url: str, timeout: int = 15) -> str | None:
    """
    Descarga una página con httpx simulando un navegador real.
    Retorna el texto limpio o None si falla.
    """
    try:
        # Pausa aleatoria para no parecer un bot
        time.sleep(random.uniform(0.8, 2.2))

        with httpx.Client(
            headers=_get_headers(),
            follow_redirects=True,
            timeout=timeout,
            verify=False,          # Evita errores de SSL en algunos sitios
        ) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return _clean_html(resp.text)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# CAPA 3: Playwright con técnicas avanzadas de stealth (último recurso)
# ---------------------------------------------------------------------------
def _fetch_page_playwright(url: str) -> str | None:
    """
    Usa Playwright con inyección manual de JS para evadir detección.
    Solo se llama si httpx falla.
    """
    try:
        from playwright.sync_api import sync_playwright

        stealth_js = """
        // Eliminar la bandera de webdriver
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // Simular plugins reales de Chrome
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // Simular idiomas reales
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-ES', 'es', 'en-US', 'en'],
        });

        // Ocultar que es headless
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters)
        );
        """

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1920,1080",
                ],
            )

            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
                locale="es-ES",
                timezone_id="America/Lima",
                # Simular permisos de notificaciones para parecer real
                permissions=["notifications"],
            )

            # Inyectar el JS de stealth ANTES de cargar cualquier página
            context.add_init_script(stealth_js)
            page = context.new_page()

            # Simular movimiento de mouse para parecer humano
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.mouse.move(random.randint(100, 800), random.randint(100, 600))
            time.sleep(random.uniform(1.5, 3.0))

            html = page.content()
            browser.close()
            return _clean_html(html)

    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Clase principal WebAgent
# ---------------------------------------------------------------------------
class WebAgent:
    def __init__(self, logger):
        self.logger = logger

    def search_and_extract(self, query: str) -> str:
        """
        Punto de entrada principal. Orquesta las 3 capas de búsqueda.
        """
        self.logger.info(f"[WebAgent] 🔍 Investigando: '{query}'")

        # ── CAPA 1: Obtener resultados de DDG (sin scraping) ─────────────────
        self.logger.info("[WebAgent] Capa 1 → Consultando DuckDuckGo...")
        try:
            resultados = _search_ddg(query, max_results=5)
        except Exception as e:
            self.logger.warning(f"[WebAgent] DDG falló: {e}")
            resultados = []

        if not resultados:
            return "⚠️ No encontré resultados de búsqueda. Verifica tu conexión."

        # Si el snippet de DDG ya tiene info suficiente, úsalo directamente
        snippets_combinados = "\n".join(
            f"• {r['title']}: {r['snippet']}" for r in resultados if r["snippet"]
        )
        if len(snippets_combinados) > 500:
            self.logger.info("[WebAgent] ✅ Info suficiente desde snippets de DDG.")
            fuentes = "\n".join(f"  - {r['url']}" for r in resultados[:3])
            return (
                f"📋 Resumen de búsqueda para '{query}':\n\n"
                f"{snippets_combinados}\n\n"
                f"🔗 Fuentes consultadas:\n{fuentes}"
            )

        # ── CAPA 2: Intentar extraer contenido de las páginas con httpx ──────
        self.logger.info("[WebAgent] Capa 2 → Extrayendo contenido con httpx...")
        for i, resultado in enumerate(resultados[:3]):
            url = resultado["url"]
            if not url:
                continue
            self.logger.info(f"[WebAgent] Intentando: {url}")
            texto = _fetch_page_httpx(url)
            if texto and len(texto) > 300:
                self.logger.info(f"[WebAgent] ✅ Éxito con httpx en: {url}")
                return (
                    f"📄 Información extraída de: {url}\n\n"
                    f"{texto}"
                )

        # ── CAPA 3: Playwright stealth como último recurso ───────────────────
        self.logger.info("[WebAgent] Capa 3 → Activando Playwright stealth...")
        for resultado in resultados[:2]:
            url = resultado["url"]
            if not url:
                continue
            self.logger.info(f"[WebAgent] Playwright navegando a: {url}")
            texto = _fetch_page_playwright(url)
            if texto and len(texto) > 300:
                self.logger.info(f"[WebAgent] ✅ Playwright tuvo éxito en: {url}")
                return (
                    f"📄 Información extraída (Playwright) de: {url}\n\n"
                    f"{texto}"
                )

        # ── Fallback: devolver snippets de DDG aunque sean cortos ────────────
        self.logger.warning("[WebAgent] Todas las capas fallaron. Usando snippets de DDG.")
        return (
            f"⚠️ No pude acceder al contenido completo. "
            f"Aquí lo que obtuve de los snippets:\n\n{snippets_combinados}"
        )

    def quick_search(self, query: str, max_results: int = 3) -> str:
        """
        Búsqueda rápida que solo devuelve snippets (sin navegar a páginas).
        Útil para preguntas simples donde no hace falta extraer una web completa.
        """
        self.logger.info(f"[WebAgent] ⚡ Búsqueda rápida: '{query}'")
        try:
            resultados = _search_ddg(query, max_results=max_results)
            if not resultados:
                return "No encontré resultados."
            respuesta = f"Resultados para '{query}':\n\n"
            for r in resultados:
                respuesta += f"📌 {r['title']}\n   {r['snippet']}\n   🔗 {r['url']}\n\n"
            return respuesta.strip()
        except Exception as e:
            return f"Error en búsqueda rápida: {e}"


# ---------------------------------------------------------------------------
# Test rápido (ejecutar este archivo directamente para probar)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logger = logging.getLogger("JARVIS")

    agent = WebAgent(logger)

    print("\n" + "="*60)
    print("TEST 1: Búsqueda rápida")
    print("="*60)
    print(agent.quick_search("últimas noticias tecnología IA 2025"))

    print("\n" + "="*60)
    print("TEST 2: Búsqueda completa con extracción")
    print("="*60)
    print(agent.search_and_extract("cómo funciona la fusión nuclear"))