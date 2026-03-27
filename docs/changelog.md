# Changelog (Registro de Evolución) 🗒️

Todas las evoluciones y parches críticos del proyecto **Busca Clientes** se registran aquí.

## [1.2.0] - 2026-03-27
### Agregado
- **Acceso Red Local (LAN):** Configuración de servidores en `0.0.0.0` y autodetección de IP en el frontend para acceso desde iPad/Mac.
- **Docs & README:** Creación de estructura de documentación técnica y manual de arquitectura.
- **Playwright Binaries:** Instalación de binarios de Chromium en el entorno virtual.

### Corregido
- **CORS Lock:** Se liberó la política CORS en el Backend para permitir solicitudes desde IPs de red local.
- **Windows Async Patch:** Se implementó `WindowsProactorEventLoopPolicy` en el bloque `__main__` del worker para solucionar el error `NotImplementedError` al lanzar procesos hijos en Windows.

## [1.1.0] - 2026-03-27
### Agregado
- **Motor Playwright:** Migración de BeautifulSoup a un navegador real invisible para saltar firewalls (ej. Sanatorio Allende).
- **Persistencia de Insights:** Nuevas columnas en MySQL (`falla_detectada`, `emails_hallados`, `auditoria_texto`).

## [1.0.0] - 2026-03-26
### Inicial
- Estructura básica Orquestador/Worker.
- Dashboard inicial funcional.
- Conexión base a Base de Datos.
