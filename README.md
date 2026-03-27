# Busca Clientes App 🤖⚡

> **Motor Híbrido de Prospección Distribuida e Inteligencia de Ventas (Deep Audit Edition)**
>
> Una solución de ingeniería diseñada para automatizar la auditoría de sitios web, extracción de leads y detección de fallas críticas. El sistema utiliza una arquitectura distribuida que delega tareas pesadas de scraping a nodos dedicados (Mac Pro) mientras centraliza la gestión en un orquestador inteligente.

![Status](https://img.shields.io/badge/status-active-success)
![Environment](https://img.shields.io/badge/env-distributed-blue)
![Engine](https://img.shields.io/badge/engine-playwright-orange)
![Audit](https://img.shields.io/badge/audit-deep-red)

---

## 📌 Visión General

Busca Clientes utiliza un motor de **Auditoría Profunda** en 4 fases para generar informes de alto impacto comercial:

1.  **Fase 1: Dominio (WHOIS):** Análisis de antigüedad y registro para detectar negocios establecidos.
2.  **Fase 2: Rastreo (Site Crawler):** Exploración de hasta 15 páginas internas buscando puntos de contacto.
3.  **Fase 3: Inteligencia (Business Extractor):** Identificación de **WhatsApp**, **Google Maps**, dueños/responsables y redes sociales.
4.  **Fase 4: Técnica (Análisis UX/UI & Vitals):** Detección de fallas críticas (botones pequeños, menús laberínticos, performance).

---

## 🛠️ Arquitectura del Sistema

El proyecto sigue una topología de **Orquestador/Trabajador (Mac Pro Node)**:

- **Frontend:** Vite + Vanilla JS (Puerto 5173). Interfaz Glassmorphism con Dashboard Ejecutivo.
- **Backend (Orquestador):** FastAPI + SQLAlchemy + MySQL (Puerto 8000). Gestión de BD y timeouts de 180s.
- **Worker Node (Motor):** FastAPI + Playwright (Puerto 8001). Ejecución asíncrona real.

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos
- Python 3.12+ (con dependencias: `playwright`, `python-whois`, `phonenumbers`).
- MySQL corriendo.
- Playwright instalado (`playwright install chromium`).

### 2. Levantando los Servicios 🚀

```powershell
# Ejecuta el script unificado en la raíz
.\start-all.ps1
```

---

## 💻 Robustez y Rendimiento Industrial

El sistema ha sido optimizado para el ecosistema web argentino (.com.ar) y sitios lentos:
- **Timeout Progresivo:** El orquestador espera hasta 3 minutos para informes completos.
- **Corte Inteligente:** Si un sitio demora demasiado en el rastreo, el Worker corta a los 90s para asegurar que el análisis técnico y de negocio se entreguen.
- **Dashboard Sincronizado:** Polling activo cada 3s para reflejar el estado "INVESTIGANDO" hasta completar el informe.

## 📈 Roadmap y Estado del Proyecto

- [x] Arquitectura de comunicación asíncrona (FastAPI Background Tasks).
- [x] Motor de Scraping indetectable con Playwright.
- [x] Auditoría Profunda (WHOIS + Crawler + Extractor).
- [x] Dashboard de Auditoría con muestras de fallas (ejemplos de botones/menús).
- [x] Identificación de WhatsApp, Maps y Redes Sociales.
- [ ] Integración de LLM (Claude/Gemini) para redacción de Pitches personalizados.
- [ ] Automatización de envío de propuestas vía Email/WhatsApp.

---

## 📄 Documentación Adicional

- [Changelog](./docs/changelog.md) - Registro histórico de evoluciones.
- [Definiciones del Sistema](./docs/architecture.md) - Detalles técnicos.
- **Gobernanza (Obsidian):** [Abrir en Obsidian](obsidian://open?vault=leo-obs&file=proyectos%2Fbuscaclientes%2Fhome-buscaclientes).

---
*Desarrollado bajo el Framework Baraldi v2.4.0 (Robustness Edition)*
