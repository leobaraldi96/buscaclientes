import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

async def scrape_website(url: str):
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True
            )
            page = await context.new_page()
            
            # 1. CONECTIVIDAD Y SEGURIDAD
            try:
                response = await page.goto(url, timeout=30000, wait_until="networkidle")
            except Exception as e:
                await browser.close()
                return {"status": "error", "falla_encontrada": f"Error de conexión: {str(e)[:50]}"}

            status_code = response.status if response else 0
            security_info = response.security_details if response else None
            headers = response.headers if response else {}
            
            # 2. PERFORMANCE (Métricas básicas)
            metrics = await page.evaluate("""() => {
                const resources = performance.getEntriesByType('resource');
                const images = resources.filter(r => r.initiatorType === 'img').length;
                const scripts = resources.filter(r => r.initiatorType === 'script').length;
                const css = resources.filter(r => r.initiatorType === 'link').length;
                const totalSize = resources.reduce((prev, curr) => prev + (curr.transferSize || 0), 0);
                return { images, scripts, css, totalSize: Math.round(totalSize/1024) };
            }""")

            # 3. RESPONSIVO
            is_responsive = await page.evaluate("""() => {
                const viewport = document.querySelector('meta[name="viewport"]');
                const hasHScroll = document.documentElement.scrollWidth > document.documentElement.clientWidth;
                return { meta_viewport: !!viewport, avoids_hscroll: !hasHScroll };
            }""")

            # 4. SEO Y CONTENIDOS
            html_content = await page.content()
            soup = BeautifulSoup(html_content, "lxml")
            
            seo = {
                "title": await page.title(),
                "h1_count": len(soup.find_all('h1')),
                "description": (soup.find('meta', attrs={'name': 'description'}) or {}).get('content', 'Faltante'),
                "has_sitemap": False # Simulado o requiere check extra
            }

            # 5. UX / ACCESIBILIDAD / HEURÍSTICA
            ux = await page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const missingAlt = imgs.filter(img => !img.alt).length;
                const buttons = Array.from(document.querySelectorAll('button, a.btn'));
                const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
                const missingLabels = inputs.filter(i => !document.querySelector(`label[for="${i.id}"]`)).length;
                return { total_imgs: imgs.length, missing_alt: missingAlt, missing_labels: missingLabels };
            }""")

            # GENERACIÓN DEL INFORME DETALLADO (PILARES)
            informe = {
                "pilares": {
                    "accesibilidad": {
                        "estado": "critico" if ux['missing_alt'] > 0 else "aceptable",
                        "detalle": f"Se detectaron {ux['missing_alt']} imágenes sin descripción alt y {ux['missing_labels']} formularios sin etiquetas claras."
                    },
                    "responsivo": {
                        "estado": "critico" if not is_responsive['meta_viewport'] or not is_responsive['avoids_hscroll'] else "excelente",
                        "detalle": "Falta meta-tag viewport o el sitio desborda horizontalmente en móviles." if not is_responsive['meta_viewport'] else "Diseño preparado para móviles."
                    },
                    "rendimiento": {
                        "estado": "alerta" if metrics['totalSize'] > 3000 or metrics['scripts'] > 15 else "bueno",
                        "detalle": f"Carga pesada ({metrics['totalSize']}KB). {metrics['scripts']} scripts detectados ralentizando la experiencia."
                    },
                    "seguridad": {
                        "estado": "critico" if not url.startswith("https") else "bueno",
                        "detalle": "Sitio no seguro (HTTP). Riesgo de interceptación y penalización de Google." if not url.startswith("https") else "Conexión cifrada activa."
                    },
                    "seo": {
                        "estado": "alerta" if seo['h1_count'] != 1 else "bueno",
                        "detalle": f"Se encontraron {seo['h1_count']} encabezados H1 (lo ideal es 1). Descripción meta: {seo['description'][:100]}..."
                    }
                }
            }

            # DETERMINAR FALLA CRÍTICA PARA EL DASHBOARD (METEDOR DE MIEDO)
            falla_resumen = "Ninguna falla severa detectada"
            if not url.startswith("https"):
                falla_resumen = "⚠️ SEGURIDAD CRÍTICA: Sitio No Seguro"
            elif not is_responsive['meta_viewport']:
                falla_resumen = "📱 MUERTE MÓVIL: No escala en celulares"
            elif metrics['totalSize'] > 5000:
                falla_resumen = "🐌 LENTITUD EXTREMA: Abandono inminente"
            elif ux['missing_alt'] > 5:
                falla_resumen = "🙈 INVISIBILIDAD: Errores de Accesibilidad/SEO"
            elif seo['h1_count'] == 0:
                falla_resumen = "🔍 SEO ROTO: Sin estructura jerárquica"

            # SALES PITCH (PUNTOS DE DOLOR)
            puntos_dolor = []
            if informe['pilares']['seguridad']['estado'] == 'critico':
                puntos_dolor.append("Tu sitio ahuyenta clientes con el cartel de 'Sitio No Seguro'. Estás regalando confianza a tu competencia.")
            if informe['pilares']['responsivo']['estado'] == 'critico':
                puntos_dolor.append("Estás ignorando al 80% de tus prospectos que navegan desde el celular. Tu inversión en marketing se pierde ahí.")
            if informe['pilares']['rendimiento']['estado'] == 'alerta':
                puntos_dolor.append("Tu sitio es pesado y lento. Google te hunde en los resultados y tus clientes pierden la paciencia.")
            
            if not puntos_dolor:
                puntos_dolor.append("Tu web es aceptable, pero el diseño no comunica autoridad ni convierte visitas en ventas. Necesitas el Framework Baraldi.")

            await browser.close()
            
            return {
                "status": "success",
                "http_status": status_code,
                "title": seo['title'],
                "text_preview": text_preview if 'text_preview' in locals() else "",
                "emails_encontrados": list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html_content))),
                "falla_encontrada": falla_resumen,
                "informe_detallado": informe,
                "puntos_de_dolor": "\n".join(puntos_dolor)
            }
            
    except Exception as e:
        print(f"[WORKER] ERROR CRÍTICO: {str(e)}")
        return {"status": "error", "falla_encontrada": f"Error General: {str(e)[:50]}"}
            
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
