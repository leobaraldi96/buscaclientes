# Busca Clientes App 🤖⚡

> **Motor Híbrido de Prospección Distribuida e Inteligencia de Ventas**
>
> Una solución de ingeniería diseñada para automatizar la auditoría de sitios web, extracción de leads y detección de fallas críticas. El sistema utiliza una arquitectura distribuida que permite delegar tareas pesadas de scraping a nodos dedicados (Mac Pro) mientras centraliza la gestión en un orquestador ligero.

![Status](https://img.shields.io/badge/status-active-success)
![Environment](https://img.shields.io/badge/env-distributed-blue)
![Engine](https://img.shields.io/badge/engine-playwright-orange)

---

## 📌 Visión General

Busca Clientes no es un scraper genérico. Es un **sistema de auditoría profunda** que combina:
1. **Orquestador (Backend):** Gestión de Base de Datos MySQL y lógica de negocio.
2. **Worker Node (Simualdor Mac Pro):** Motor de ejecución real (Playwright) capaz de burlar WAFs (Cloudflare) y extraer insights accionables.
3. **Dashboard Premium:** Interfaz Glassmorphism para control en tiempo real y visualización de leads.

---

## 🛠️ Arquitectura del Sistema

El proyecto sigue una topología de **Orquestador/Trabajador** para permitir escalabilidad infinita:

- **Frontend:** Vite + Vanilla JS (Puerto 5173).
- **Backend (API):** FastAPI + SQLAlchemy (Puerto 8000).
- **Worker (Scraper):** FastAPI + Playwright (Puerto 8001).

Para más detalles, consulte [Documentación de Arquitectura](./docs/architecture.md).

---

## 🚀 Inicio Rápido

Para poner en marcha el ecosistema completo en modo desarrollo:

### 1. Requisitos Previos
- Python 3.12+
- Node.js (npm)
- MySQL corriendo (XAMPP/Docker)

### 2. Levantando los Servicios
En consolas separadas (dentro de sus respectivas carpetas):

**Orquestador (Backend):**
```powershell
.\venv\Scripts\activate
python main.py
```

**Worker Node (Mac Pro):**
```powershell
..\backend\venv\Scripts\activate
python main.py
```

**Dashboard (Frontend):**
```powershell
npm run dev
```

---

## 📈 Roadmap y Estado del Proyecto

- [x] Arquitectura de comunicación asíncrona (FastAPI Background Tasks).
- [x] Motor de Scraping indetectable con Playwright.
- [x] Persistencia en Base de Datos MySQL.
- [x] Dashboard con modo Red Local (Acceso desde iPad/Mac).
- [ ] Integración de LLM (Claude/Gemini) para redacción de Pitches.
- [ ] Automatización de envío de propuestas.

---

## 📄 Documentación Adicional

- [Changelog](./docs/changelog.md) - Registro histórico de evoluciones.
- [Definiciones del Sistema](./docs/architecture.md) - Detalles técnicos de la implementación.
- **Gobernanza (Obsidian):** [Abrir en Obsidian](obsidian://open?vault=leo-obs&file=proyectos%2Fbuscaclientes%2Fhome-buscaclientes) (Requiere tener la bóveda `leo-obs` abierta).

---
*Desarrollado bajo el Framework Baraldi v2.3.2*
