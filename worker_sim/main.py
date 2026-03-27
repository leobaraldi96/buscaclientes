import sys
import asyncio

if sys.platform == "win32":
    # Forzar el motor Proactor como primera acción absoluta del archivo
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from scraper import scrape_website

# La política se define abajo en el bloque __main__ para asegurar compatibilidad con Uvicorn en Windows


app = FastAPI(
    title="Worker Node (Mac Pro)",
    description="Motor real de scraping asíncrono",
    version="1.0"
)

@app.post("/auditar")
async def perform_audit(data: dict):
    url = data.get('url')
    print(f"\n[WORKER] Iniciando Infiltración en: {url}")
    
    reporte = await scrape_website(url)
    reporte["url_auditada"] = url
    
    print(f"[WORKER] Terminado. Estado HTTP: {reporte.get('http_status')} | Falla: {reporte.get('falla_encontrada')}")
    return reporte

if __name__ == "__main__":
    import uvicorn
    # Deshabilitamos reload para esta prueba de motor, buscando estabilidad total en el loop asíncrono
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
