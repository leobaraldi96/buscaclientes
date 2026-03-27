# Arquitectura y Definiciones Técnicas 🏛️

## Orquestación Distribuida
El sistema separa la **Gestión de Datos** de la **Ejecución de Tareas**.

### 1. Orquestador (Windows / Python 8000)
- **Tecnología:** FastAPI.
- **Responsabilidad:** Recibir peticiones del Dashboard, persistir prospectos en MySQL y delegar auditorías al Worker de forma asíncrona (`BackgroundTasks`).
- **Base de Datos:** MySQL gestionada vía SQLAlchemy.

### 2. Worker Node (Nodo Mac Pro / Python 8001)
- **Tecnología:** FastAPI + Playwright.
- **Responsabilidad:** Ejecutar una instancia de Chromium invisible, navegar la URL del lead, ejecutar JS, evadir protecciones perimetrales (WAF) y extraer texto plano/emails.
- **Entrega de Resultados:** Devuelve un JSON estructurado al Orquestador al finalizar la tarea.

### 3. Dashboard Interactivo (Vite 5173)
- **Tecnología:** Vanilla JS + CSS Glassmorphism.
- **Acceso Dinámico:** Detecta la IP del servidor automáticamente para permitir operación remota desde dispositivos móviles.

## Flujo de Auditoría
1. Usuario pulsa "AUDITAR" en el iPad.
2. Dashboard manda POST al Orquestador (Windows).
3. Orquestador cambia estado del lead a "investigando" y manda señal al Worker (Mac Pro).
4. Worker navega, extrae datos y devuelve reporte.
5. Orquestador actualiza SQL con emails y fallas, marcando al lead como "contactado" o "perdido".
