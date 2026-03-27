import re
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

# Importar nuevos módulos de auditoría profunda
from whois_lookup import extract_whois_data, extract_contact_hints
from site_crawler import crawl_website
from business_extractor import extract_business_data


async def scrape_website(url: str):
    """
    Auditoría web profunda de 4 fases:
    1. WHOIS Lookup - Datos del dominio
    2. Site Crawling - Recorrido multi-página
    3. Business Extraction - Datos de contacto y negocio
    4. Análisis Técnico UX/UI - Métricas de performance y usabilidad
    """
    if not url.startswith("http"):
        url = "https://" + url

    print(f"\n{'='*60}")
    print(f"[AUDITORÍA PROFUNDA] Iniciando: {url}")
    print('='*60)

    # ========== FASE 1: WHOIS LOOKUP ==========
    print("\n[FASE 1/4] Consultando WHOIS...")
    try:
        whois_data = extract_whois_data(url)
        whois_hints = extract_contact_hints(whois_data)
        print(f"✓ WHOIS completado - Registrante: {whois_data.get('registrante') or 'N/A'}")
    except Exception as e:
        print(f"✗ Error WHOIS: {e}")
        whois_data = {"error": str(e)}
        whois_hints = {}

    # ========== FASE 2: SITE CRAWLING ==========
    print("\n[FASE 2/4] Crawling del sitio (hasta 15 páginas)...")
    try:
        crawl_results = await crawl_website(url, max_pages=15)
        print(f"✓ Crawling completado - {crawl_results['total_pages']} páginas recorridas")
        print(f"  Emails encontrados: {len(crawl_results['emails_found'])}")
        print(f"  Teléfonos encontrados: {len(crawl_results['phones_found'])}")
    except Exception as e:
        print(f"✗ Error Crawling: {e}")
        crawl_results = {"pages": [], "total_pages": 0, "emails_found": [], "phones_found": []}

    # ========== FASE 3: BUSINESS DATA EXTRACTION ==========
    print("\n[FASE 3/4] Extrayendo datos de negocio...")
    business_data = {
        "nombre_dueno": None,
        "cargo_dueno": None,
        "email_dueno": None,
        "telefono_dueno": None,
        "telefono_empresa": None,
        "direccion": None,
        "ciudad": None,
        "provincia": None,
        "redes_sociales": {},
        "fuente_datos": []
    }

    # Procesar cada página para extraer datos de negocio
    for page in crawl_results.get("pages", []):
        if page.get("has_contact_info") or any(x in page["url"].lower() for x in ["about", "nosotros", "contact", "team", "equipo"]):
            try:
                page_business = extract_business_data(
                    html=page.get("html", ""),
                    url=page["url"],
                    page_title=page.get("title", "")
                )

                # Merge datos de negocio (priorizar datos de páginas de contacto)
                for key in ["nombre_dueno", "cargo_dueno", "email_dueno", "telefono_dueno", "telefono_empresa"]:
                    if page_business.get(key) and not business_data.get(key):
                        business_data[key] = page_business[key]

                if page_business.get("direccion") and not business_data["direccion"]:
                    business_data["direccion"] = page_business["direccion"]
                    business_data["ciudad"] = page_business.get("ciudad")
                    business_data["provincia"] = page_business.get("provincia")

                # Merge redes sociales
                if page_business.get("redes_sociales"):
                    business_data["redes_sociales"].update(page_business["redes_sociales"])

                # Merge fuentes
                if page_business.get("fuente_datos"):
                    business_data["fuente_datos"].extend(page_business["fuente_datos"])

            except Exception as e:
                print(f"  ⚠ Error extrayendo datos de {page['url']}: {e}")
                continue

    print(f"✓ Datos de negocio extraídos")
    print(f"  Dueño: {business_data['nombre_dueno'] or 'No encontrado'}")
    print(f"  Teléfono: {business_data['telefono_empresa'] or business_data['telefono_dueno'] or 'No encontrado'}")
    print(f"  Dirección: {business_data['direccion'] or 'No encontrada'}")

    # ========== FASE 4: ANÁLISIS TÉCNICO PROFUNDO (Home Page) ==========
    print("\n[FASE 4/4] Análisis técnico profundo (Home Page)...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800},
                ignore_https_errors=True
            )
            page = await context.new_page()

            try:
                start_time = asyncio.get_event_loop().time()
                response = await page.goto(url, timeout=45000, wait_until="networkidle")
                latency = asyncio.get_event_loop().time() - start_time
                status_code = response.status if response else 0
            except Exception as e:
                await browser.close()
                # Retornar datos parciales si el sitio no carga
                return _build_partial_response(url, whois_data, crawl_results, business_data, str(e))

            html_content = await page.content()

            # Análisis de Performance (Chrome DevTools)
            performance_metrics = await page.evaluate("""() => {
                const nav = performance.getEntriesByType('navigation')[0] || {};
                const resources = performance.getEntriesByType('resource');
                const totalSize = resources.reduce((prev, curr) => prev + (curr.transferSize || 0), 0);

                // Core Web Vitals aproximados
                const lcp = performance.getEntriesByType('element').pop();

                return {
                    // Timing
                    dnsTime: Math.round(nav.domainLookupEnd - nav.domainLookupStart),
                    connectTime: Math.round(nav.connectEnd - nav.connectStart),
                    ttfb: Math.round(nav.responseStart - nav.requestStart),
                    domInteractive: Math.round(nav.domInteractive),
                    domComplete: Math.round(nav.domComplete),
                    loadTime: Math.round(nav.loadEventEnd - nav.startTime),

                    // Size
                    totalSizeKB: Math.round(totalSize / 1024),
                    resourcesCount: resources.length,

                    // Counters
                    scripts: document.querySelectorAll('script').length,
                    stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length,
                    images: document.querySelectorAll('img').length,
                    iframes: document.querySelectorAll('iframe').length,

                    // LCP aproximado
                    lcpTime: lcp ? Math.round(lcp.renderTime || lcp.loadTime) : null
                };
            }""")

            # Análisis SEO
            seo_data = await page.evaluate("""() => {
                const getMeta = (name) => {
                    const elem = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return elem ? elem.content : null;
                };

                const h1s = Array.from(document.querySelectorAll('h1')).map(el => el.innerText.trim());
                const h2s = Array.from(document.querySelectorAll('h2')).slice(0, 5).map(el => el.innerText.trim());
                const imgs = Array.from(document.querySelectorAll('img'));
                const imgsSinAlt = imgs.filter(img => !img.alt || img.alt === '').length;
                const links = Array.from(document.querySelectorAll('a[href]'));
                const externalLinks = links.filter(a => a.href.startsWith('http') && !a.href.includes(window.location.hostname)).length;

                // Detectar sitemap y robots
                const hasSitemap = !!document.querySelector('link[rel="sitemap"]');
                const hasCanonical = !!document.querySelector('link[rel="canonical"]');

                return {
                    title: document.title,
                    titleLength: document.title.length,
                    description: getMeta('description'),
                    descriptionLength: getMeta('description')?.length || 0,
                    keywords: getMeta('keywords'),
                    author: getMeta('author'),
                    robots: getMeta('robots'),
                    ogTitle: getMeta('og:title'),
                    ogDescription: getMeta('og:description'),
                    h1s: h1s,
                    h1Count: h1s.length,
                    h2Count: h2s.length,
                    imagesCount: imgs.length,
                    imagesSinAlt: imgsSinAlt,
                    linksCount: links.length,
                    externalLinks: externalLinks,
                    hasSitemap: hasSitemap,
                    hasCanonical: hasCanonical,
                    lang: document.documentElement.lang || 'no especificado'
                };
            }""")

            # Análisis UX/UI (ampliado con ejemplos)
            ux_data = await page.evaluate("""() => {
                const getLabel = (el) => {
                    return (el.innerText || el.getAttribute('aria-label') || el.title || el.name || el.value || "Elemento").trim().substring(0, 30);
                };

                // Botones pequeños
                const interactive = Array.from(document.querySelectorAll('button, a.btn, input[type="submit"], .wp-block-button__link, nav a'));
                const smallOnes = interactive.filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && (rect.width < 44 || rect.height < 44);
                });

                // Menú
                const menuItems = Array.from(document.querySelectorAll('nav li, .menu-item, .nav-item, header a')).map(el => el.innerText.trim()).filter(t => t && t.length > 1);
                
                // Desbordes
                const hasHScroll = document.documentElement.scrollWidth > document.documentElement.clientWidth;

                // Formularios
                const forms = document.querySelectorAll('form');
                const formsWithoutLabels = Array.from(forms).filter(f => {
                    const inputs = f.querySelectorAll('input:not([type="hidden"]):not([type="submit"])');
                    const labels = f.querySelectorAll('label');
                    return inputs.length > labels.length;
                });

                // Contraste (muestras)
                const textElements = Array.from(document.querySelectorAll('p, span, a, h1, h2, h3, h4'));
                const lowContrastElements = textElements.filter(el => {
                    const style = window.getComputedStyle(el);
                    const color = style.color;
                    // Detección simple de grises muy claros (ej: rgb(200, 200, 200) o más alto)
                    const rgb = color.match(/\d+/g);
                    if (rgb && rgb.length >= 3) {
                        return parseInt(rgb[0]) > 180 && parseInt(rgb[1]) > 180 && parseInt(rgb[2]) > 180;
                    }
                    return false;
                });

                return {
                    smallOnesCount: smallOnes.length,
                    smallOnesSample: smallOnes.slice(0, 10).map(el => getLabel(el)),
                    menuItemsCount: menuItems.length,
                    menuItemsSample: menuItems.slice(0, 15),
                    hasHScroll: hasHScroll,
                    formsCount: forms.length,
                    formsWithoutLabelsCount: formsWithoutLabels.length,
                    lowContrastCount: lowContrastElements.length,
                    lowContrastSample: lowContrastElements.slice(0, 5).map(el => el.innerText.trim().substring(0, 40))
                };
            }""")

            # Detectar tecnologías
            tech_stack = await page.evaluate("""() => {
                const techs = [];

                // CMS
                if (document.querySelector('meta[name="generator"]')) {
                    const gen = document.querySelector('meta[name="generator"]').content;
                    if (gen.includes('WordPress')) techs.push('WordPress');
                    if (gen.includes('Joomla')) techs.push('Joomla');
                    if (gen.includes('Drupal')) techs.push('Drupal');
                    if (gen.includes('Wix')) techs.push('Wix');
                    if (gen.includes('Squarespace')) techs.push('Squarespace');
                }
                if (document.querySelector('link[href*="wp-content"]')) techs.push('WordPress');
                if (window.jQuery) techs.push('jQuery');
                if (window.Vue) techs.push('Vue.js');
                if (window.React) techs.push('React');
                if (window.Angular) techs.push('Angular');

                // Analytics
                if (window.gtag) techs.push('Google Analytics 4');
                if (window.ga) techs.push('Google Analytics');
                if (window.fbq) techs.push('Facebook Pixel');
                if (window._mtm) techs.push('Matomo');

                // E-commerce
                if (document.querySelector('[class*="woocommerce"]')) techs.push('WooCommerce');
                if (document.querySelector('[class*="shopify"]')) techs.push('Shopify');

                // CDN
                const scripts = Array.from(document.querySelectorAll('script[src]'));
                const links = Array.from(document.querySelectorAll('link[href]'));
                const allSrcs = [...scripts.map(s => s.src), ...links.map(l => l.href)].join(' ');

                if (allSrcs.includes('cloudflare')) techs.push('Cloudflare');
                if (allSrcs.includes('googleapis')) techs.push('Google CDN');
                if (allSrcs.includes('bootstrap')) techs.push('Bootstrap');
                if (allSrcs.includes('fontawesome')) techs.push('Font Awesome');

                // Frameworks CSS
                if (document.querySelector('[class*="tailwind"]')) techs.push('Tailwind CSS');

                return techs;
            }""")

            await browser.close()

            # ========== COMPILAR RESULTADOS COMPLETOS ==========

            # Generar Pilares de Auditoría (existente + nuevo)
            is_insecure = not url.startswith("https")

            # Detalle ampliado para el informe
            btn_sample_str = f" ({', '.join(ux_data['smallOnesSample'])})" if ux_data['smallOnesSample'] else ""
            menu_sample_str = f" Algunos items: {', '.join(ux_data['menuItemsSample'][:5])}..." if ux_data['menuItemsCount'] > 5 else ""

            pilares = {
                "Seguridad": {
                    "estado": "critico" if is_insecure else "bueno",
                    "detalle": "⚠️ SIN SSL: Tu sitio es inseguro. Google penaliza y los navegadores muestran 'No Seguro'." if is_insecure else "✅ SSL Activo. Conexión cifrada detectada."
                },
                "Performance": {
                    "estado": "critico" if performance_metrics['loadTime'] > 5000 else ("alerta" if performance_metrics['loadTime'] > 3000 else "bueno"),
                    "detalle": f"{'🐌 LENTA: ' if performance_metrics['loadTime'] > 3000 else '⚡ Velocidad: '}{performance_metrics['loadTime']}ms carga total. {performance_metrics['totalSizeKB']}KB transferidos en {performance_metrics['resourcesCount']} recursos."
                },
                "SEO": {
                    "estado": "critico" if seo_data['h1Count'] == 0 or not seo_data['description'] else ("alerta" if seo_data['titleLength'] < 20 or seo_data['titleLength'] > 70 else "bueno"),
                    "detalle": f"{'❌ Sin H1' if seo_data['h1Count'] == 0 else '✅ ' + str(seo_data['h1Count']) + ' H1'} | {'' if seo_data['description'] else '❌ Sin meta description'} | {seo_data['imagesSinAlt']} imágenes sin alt text."
                },
                "Accesibilidad": {
                    "estado": "critico" if ux_data['formsWithoutLabelsCount'] > 0 or ux_data['lowContrastCount'] > 10 else ("alerta" if ux_data['smallOnesCount'] > 3 else "bueno"),
                    "detalle": f"{ux_data['smallOnesCount']} botones pequeños{btn_sample_str} | {ux_data['formsWithoutLabelsCount']} formularios sin labels | {ux_data['lowContrastCount']} elementos con bajo contraste."
                },
                "UX/UI": {
                    "estado": "critico" if ux_data['hasHScroll'] or ux_data['menuItemsCount'] > 20 else ("alerta" if ux_data['menuItemsCount'] > 10 else "bueno"),
                    "detalle": f"{'❌ Desbordes horizontales' if ux_data['hasHScroll'] else '✅ Sin desbordes'} | Menú: {ux_data['menuItemsCount']} items.{menu_sample_str} | {ux_data['formsCount']} formularios."
                }
            }

            # Puntos de Dolor para Pitch de Venta
            puntos_dolor = []

            # Performance
            if performance_metrics['loadTime'] > 4000:
                puntos_dolor.append(f"🐌 VELOCIDAD CRÍTICA: Tu web tarda {performance_metrics['loadTime']}ms en cargar. El 53% de visitantes abandonan si tarda más de 3 segundos. Estás perdiendo clientes antes de que vean tu oferta.")
            elif performance_metrics['loadTime'] > 2500:
                puntos_dolor.append(f"⚡ VELOCIDAD LENTA: {performance_metrics['loadTime']}ms de carga. Estás en el límite. Cada segundo extra reduce conversiones un 7%.")

            # SEO
            if seo_data['h1Count'] == 0:
                puntos_dolor.append("🔍 SEO INVISIBLE: No tenés título H1. Google no entiende de qué habla tu página. Estás regalando posicionamiento orgánico a tu competencia.")
            if not seo_data['description']:
                puntos_dolor.append("📝 SIN META DESCRIPCIÓN: Tu resultado en Google muestra texto aleatorio. No controlás la primera impresión de tu marca.")
            if seo_data['imagesSinAlt'] > 0:
                puntos_dolor.append(f"♿ {seo_data['imagesSinAlt']} IMÁGENES INVISIBLES: Faltan descripciones alt. Google no entiende tus imágenes y usuarios con discapacidad visual no pueden navegar.")

            # Accesibilidad
            if ux_data['smallOnesCount'] > 0:
                puntos_dolor.append(f"🖱️ BOTONES IMPOSIBLES: Detectamos {ux_data['smallOnesCount']} elementos difíciles de tocar en móviles (ej: {', '.join(ux_data['smallOnesSample'][:3])}). Frustrás a tus usuarios y bajás conversiones.")

            # UX
            if ux_data['hasHScroll']:
                puntos_dolor.append("📱 DISEÑO ROTO EN MÓVILES: El contenido se sale de la pantalla. El 60% de tráfico es móvil y ven un sitio desprolijo.")
            if ux_data['menuItemsCount'] > 15:
                puntos_dolor.append(f"🧭 MENÚ LABERÍNTICO: {ux_data['menuItemsCount']} opciones en el menú ({', '.join(ux_data['menuItemsSample'][:5])}...) saturan al usuario. La paradoja de la elección: más opciones = menos ventas.")

            # Seguridad
            if is_insecure:
                puntos_dolor.append("🔒 SIN SEGURIDAD: Tu sitio muestra 'No Seguro' en el navegador. Transmitís desconfianza y perdés clientes antes de contactarte.")

            # Datos de contacto faltantes
            if not business_data['telefono_empresa'] and not business_data['telefono_dueno']:
                puntos_dolor.append("📞 SIN TELÉFONO VISIBLE: Los clientes no pueden llamarte. Estás perdiendo leads calientes que prefieren llamar antes que escribir.")

            if not puntos_dolor:
                puntos_dolor.append("✅ Tu sitio está bien técnicamente, pero carece de estrategia de conversión. Podemos optimizarlo para captar más leads y vender más.")

            # Consolidar emails de todas las fuentes
            all_emails = set(crawl_results.get("emails_found", []))
            all_emails.update(business_data.get("emails_encontrados", []))
            if business_data.get("email_dueno"):
                all_emails.add(business_data["email_dueno"])
            if whois_hints.get("email"):
                all_emails.add(whois_hints["email"])

            # Consolidar teléfonos
            all_phones = set(crawl_results.get("phones_found", []))
            all_phones.update(business_data.get("telefonos_encontrados", []))
            if business_data.get("telefono_empresa"):
                all_phones.add(business_data["telefono_empresa"])
            if business_data.get("telefono_dueno"):
                all_phones.add(business_data["telefono_dueno"])

            # Elegir teléfono principal
            telefono_principal = business_data.get("telefono_empresa") or business_data.get("telefono_dueno") or (list(all_phones)[0] if all_phones else None)

            print(f"\n{'='*60}")
            print("[AUDITORÍA COMPLETADA] Resumen:")
            print(f"  - {crawl_results['total_pages']} páginas analizadas")
            print(f"  - {len(all_emails)} emails encontrados")
            print(f"  - {len(all_phones)} teléfonos encontrados")
            print(f"  - Dueño identificado: {'Sí' if business_data['nombre_dueno'] else 'No'}")
            print(f"  - Dirección: {'Sí' if business_data['direccion'] else 'No'}")
            print('='*60)

            return {
                "status": "success",
                "http_status": status_code,
                "url_auditada": url,
                "paginas_recorridas": crawl_results['total_pages'],

                # Datos de Contacto Enriquecidos
                "telefono": telefono_principal,
                "email": business_data.get("email_dueno") or (list(all_emails)[0] if all_emails else None),
                "emails_encontrados": list(all_emails),
                "telefonos_encontrados": list(all_phones),
                "direccion": business_data.get("direccion"),
                "ciudad": business_data.get("ciudad"),
                "provincia": business_data.get("provincia"),

                # Datos del Dueño/Contacto Clave
                "nombre_dueno": business_data.get("nombre_dueno"),
                "cargo_dueno": business_data.get("cargo_dueno"),
                "email_dueno": business_data.get("email_dueno"),
                "telefono_dueno": business_data.get("telefono_dueno"),

                # Redes Sociales
                "redes_sociales": business_data.get("redes_sociales", {}),

                # WHOIS
                "whois_data": whois_data,
                "dominio_creado": whois_data.get("creacion"),
                "dominio_expira": whois_data.get("expiracion"),
                "antiguedad_dominio": whois_data.get("antiguedad_anios"),

                # Auditoría Técnica
                "informe_detallado": {
                    "pilares": pilares,
                    "performance": performance_metrics,
                    "seo": seo_data,
                    "ux": ux_data,
                    "tecnologias": tech_stack
                },

                # Datos del Crawling
                "crawl_data": {
                    "urls_visitadas": crawl_results.get("urls_visited", []),
                    "paginas": [
                        {
                            "url": p["url"],
                            "title": p["title"],
                            "emails": p.get("emails", []),
                            "phones": p.get("phones", [])
                        }
                        for p in crawl_results.get("pages", [])
                    ]
                },

                # Pitch de Venta
                "puntos_de_dolor": "\n\n".join(puntos_dolor),
                "falla_encontrada": f"{'❌ Crítico' if len([p for p in puntos_dolor if '❌' in p or '🔴' in p or '🐌' in p]) > 2 else '⚠️ Optimizable'} - {len(puntos_dolor)} issues"
            }

    except Exception as e:
        import traceback
        print(f"\n[ERROR CRÍTICO] {e}")
        print(traceback.format_exc())
        return {
            "status": "error",
            "falla_encontrada": f"Error de auditoría: {str(e)[:50]}",
            "error_details": str(e)
        }


def _build_partial_response(url, whois_data, crawl_results, business_data, error_msg):
    """Construye respuesta parcial cuando el sitio no carga pero tenemos datos de crawling/WHOIS."""

    puntos_dolor = [f"⚠️ El sitio no respondió completamente: {error_msg}"]

    if whois_data.get("antiguedad_anios") and whois_data["antiguedad_anios"] > 5:
        puntos_dolor.append(f"💡 El dominio tiene {whois_data['antiguedad_anios']} años. Probablemente sea un negocio establecido que necesita modernización.")

    # Consolidar datos disponibles
    all_emails = set(crawl_results.get("emails_found", []))
    all_phones = set(crawl_results.get("phones_found", []))

    return {
        "status": "partial",
        "falla_encontrada": f"⚠️ Sitio inaccesible: {error_msg}",
        "url_auditada": url,
        "paginas_recorridas": crawl_results.get("total_pages", 0),
        "emails_encontrados": list(all_emails),
        "telefonos_encontrados": list(all_phones),
        "telefono": list(all_phones)[0] if all_phones else None,
        "email": list(all_emails)[0] if all_emails else None,
        "nombre_dueno": business_data.get("nombre_dueno"),
        "direccion": business_data.get("direccion"),
        "whois_data": whois_data,
        "puntos_de_dolor": "\n\n".join(puntos_dolor),
        "informe_detallado": {
            "pilares": {
                "Accesibilidad": {"estado": "desconocido", "detalle": "No se pudo analizar - sitio inaccesible"},
                "Performance": {"estado": "desconocido", "detalle": "No se pudo analizar"}
            }
        }
    }


# Mantener backward compatibility
import asyncio

if __name__ == "__main__":
    # Prueba
    async def test():
        result = await scrape_website("https://ejemplo.com")
        print("\n" + "="*60)
        print("RESULTADO COMPLETO")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Páginas: {result['paginas_recorridas']}")
        print(f"Dueño: {result.get('nombre_dueno')}")
        print(f"Teléfono: {result.get('telefono')}")
        print(f"Dirección: {result.get('direccion')}")

    asyncio.run(test())
