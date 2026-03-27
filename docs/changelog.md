# Changelog (Registro de Evolución) 🗒️

Todas las evoluciones y parches críticos del proyecto **Busca Clientes** se registran aquí.

## [2.4.0] - 2026-03-27
### Agregado
- **Robustez Industrial:** Timeouts extendidos a 180s en el orquestador para soportar sitios lentos.
- **Corte por Timeout en Crawler:** Límite global de 90s para evitar bloqueos infinitos en sitios complejos.
- **Dashboard Sincronizado:** Polling activo y ordenamiento persistente durante la auditoría.
- **Habilitación de Re-Auditoría:** Botón disponible para leads con estado 'PERDIDO'.

## [2.3.0] - 2026-03-27
### Agregado
- **Auditoría Profunda (Deep Audit):** Motor de 4 fases (WHOIS -> Crawler -> Business Extractor -> UX/UI).
- **Business Extractor:** Extracción inteligente de WhatsApp, Google Maps, Responsables y Redes Sociales.
- **Informe Detallado de UX:** Detección de botones pequeños y menús laberínticos con muestras reales del DOM.
- **Database Expansion:** Migración de 20 campos nuevos para persistencia enriquecida.

## [1.2.0] - 2026-03-27
### Agregado
- **Acceso Red Local (LAN):** Configuración de servidores en `0.0.0.0` y autodetección de IP en el frontend para acceso desde iPad/Mac.
- **Docs & README:** Creación de estructura de documentación técnica y manual de arquitectura.

## [1.0.0] - 2026-03-26
### Inicial
- Estructura básica Orquestador/Worker.
- Dashboard inicial funcional.
- Conexión base a Base de Datos.
