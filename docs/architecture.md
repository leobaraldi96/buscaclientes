# Arquitectura y Definiciones Técnicas 🏛️

## Orquestación Distribuida
El sistema separa la **Gestión de Datos** de la **Ejecución de Tareas**.

### 1. Orquestador (Windows / Python 8000)
- **Tecnología:** FastAPI.
- **Responsabilidad:** Recibir peticiones del Dashboard, persistir prospectos en MySQL y delegar auditorías al Worker de forma asíncrona (`BackgroundTasks`).
- **Base de Datos:** MySQL gestionada vía SQLAlchemy.

### 2. Worker Node (Nodo Motor / Python 8001)
- **Tecnología:** FastAPI + Playwright + BeautifulSoup + python-whois.
- **Responsabilidad:** Ejecutar el motor de **Auditoría Profunda** en 4 fases:
    1. **WHOIS:** Datos legales y de registro.
    2. **Crawler:** Rastreo recursivo inteligente (timeout 90s).
    3. **Extractor:** Enriquecimiento de datos comerciales (WhatsApp, Maps, Redes).
    4. **Technical:** Análisis de UX/UI y Core Web Vitals vía Chromium.
- **Entrega de Resultados:** Devuelve un reporte consolidado con "Puntos de Dolor" para el pitch de venta.

### 3. Dashboard Ejecutivo (Vite 5173)
- **Tecnología:** Vanilla JS + CSS Glassmorphism.
- **Acceso Dinámico:** Detecta la IP del servidor automáticamente para permitir operación remota desde iPad/Mac.
- **Seguimiento Realtime:** Polling cada 3s para visualizar el progreso del bot.

## Flujo de Auditoría Profunda
1. El usuario pulsa "AUDITAR" o "RE-AUDITAR" en el lead seleccionado.
2. El Orquestador cambia el estado a **INVESTIGANDO** y dispara la tarea en segundo plano.
3. El Orquestador abre una conexión HTTP con el Worker (timeout de 180s).
4. El Worker ejecuta las 4 fases de auditoría y genera el reporte.
5. Si el Worker excede los 90s en el rastreo, corta esa fase para asegurar la entrega del reporte.
6. El Orquestador recibe el reporte, actualiza MySQL y cambia el estado a **CONTACTADO**.
7. El Dashboard detecta el cambio vía Polling y habilita el botón **INFORME**.
