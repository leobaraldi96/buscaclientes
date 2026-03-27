import asyncio
from playwright.async_api import async_playwright
import traceback

async def run():
    try:
        async with async_playwright() as p:
            print("Lanzando Chromium...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                ignore_https_errors=True
            )
            page = await context.new_page()
            
            url = "https://www.sanatorioallende.com/"
            print(f"Navegando a {url}...")
            response = await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            
            print(f"Status original HTTP: {response.status if response else 'Ninguno'}")
            
            title = await page.title()
            print(f"Título obtenido: {title}")
            
            await page.screenshot(path="allende_debug.png")
            print("Captura tomada exitosamente: allende_debug.png")
            
            await browser.close()
            print("Proceso finalizado OK.")
    except Exception as e:
        print("!!! OCURRIÓ UNA EXCEPCIÓN !!!")
        print(str(e))
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
