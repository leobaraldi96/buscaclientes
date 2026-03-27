import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

async def scrape_website(url: str):
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        async with async_playwright() as p:
            # Lanzamos Chromium (El motor real de Google Chrome) de forma invisible en la RAM
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                ignore_https_errors=True # Vital para no asustarnos si tienen el SSL vencido
            )
            page = await context.new_page()
            
            # Navegamos y le damos 20 segundos máximo para evitar bucles infinitos en sitios muy rotos
            response = await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            
            # MÁGIA: Si había un firewall de Cloudflare o un SPAN (React) cargando... Playwright ya lo ejecutó como un humano!
            html_content = await page.content()
            status_code = response.status if response else 0
            
            # Reutilizamos BS4 sólo para "limpiar" el HTML final que nos trajo el navegador real
            soup = BeautifulSoup(html_content, "lxml")
            
            for script in soup(["script", "style", "noscript", "svg"]):
                script.extract()
                
            text = soup.get_text(separator=" ", strip=True)
            text_preview = text[:2000]
            
            emails = list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))
            title = await page.title()
            
            await browser.close()
            
            falla = "Ninguna falla severa aparente"
            if status_code != 200 and status_code != 0:
                falla = f"Error HTTP {status_code}"
                
            return {
                "status": "success",
                "http_status": status_code,
                "title": title if title else "Sin etiqueta <title>",
                "text_preview": text_preview,
                "emails_encontrados": emails,
                "falla_encontrada": falla
            }
            
    except PlaywrightTimeoutError:
        print(f"[WORKER] ERROR: Tiempo de espera agotado para {url}")
        return {"status": "error", "http_status": 0, "falla_encontrada": "Timeout -> Servidor lento o WAF que traba el navegador."}
    except Exception as e:
        error_msg = str(e)
        print(f"[WORKER] ERROR CRÍTICO: {error_msg}")
        
        if "executable doesn't exist" in error_msg.lower() or "playwright install" in error_msg.lower():
             return {"status": "error", "http_status": 0, "falla_encontrada": "Error de Motor: Faltan instalar los binarios (Navegador Chrome invisible)."}
        
        if "ERR_NAME_NOT_RESOLVED" in error_msg:
             return {"status": "error", "http_status": 0, "falla_encontrada": "Sitio Caído / DNS Inaccesible -> ¡Urgencia Total!"}
             
        return {"status": "error", "http_status": 0, "falla_encontrada": f"Error General de Navegación: {error_msg[:50]}"}
