"""
Módulo Site Crawler - Recorre múltiples páginas del sitio web
"""
import asyncio
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright


class SiteCrawler:
    """
    Crawler inteligente que recorre un sitio web usando Playwright.
    Evade WAFs y extrae información de contacto de cada página.
    """

    def __init__(self, max_pages=15, delay_seconds=1.5):
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.visited_urls = set()
        self.pages_data = []
        self.all_emails = set()
        self.all_phones = set()

    async def crawl(self, start_url: str):
        """
        Inicia el crawling desde una URL.

        Returns:
            dict con todas las páginas y datos extraídos
        """
        if not start_url.startswith('http'):
            start_url = 'https://' + start_url

        self.base_domain = urlparse(start_url).netloc
        self.base_url = start_url

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.0.36",
                viewport={'width': 1280, 'height': 800},
                ignore_https_errors=True
            )

            # Páginas prioritarias a visitar primero
            priority_paths = [
                '/contacto', '/contact', '/nosotros', '/about',
                '/about-us', '/quienes-somos', '/team', '/staff',
                '/equipo', '/empresa', '/company'
            ]

            # URLs a visitar
            urls_to_visit = [start_url]

            # Agregar páginas prioritarias
            for path in priority_paths:
                priority_url = urljoin(start_url, path)
                if priority_url not in urls_to_visit:
                    urls_to_visit.append(priority_url)

            # Procesar URLs con un timeout global de 90 segundos para el crawling
            start_crawl_time = asyncio.get_event_loop().time()
            for url in urls_to_visit:
                # Si pasamos más de 90 segundos crawleando, cortamos para ir a fase 4
                if asyncio.get_event_loop().time() - start_crawl_time > 90:
                    print(f"[CRAWLER] Timeout global alcanzado (90s). Finalizando recolección prematura.")
                    break

                if len(self.visited_urls) >= self.max_pages:
                    break

                if url in self.visited_urls:
                    continue

                try:
                    await self._process_page(context, url)
                    await asyncio.sleep(self.delay_seconds)
                except Exception as e:
                    print(f"[CRAWLER] Error procesando {url}: {e}")

            await browser.close()

        return {
            "pages": self.pages_data,
            "total_pages": len(self.pages_data),
            "emails_found": list(self.all_emails),
            "phones_found": list(self.all_phones),
            "urls_visited": list(self.visited_urls)
        }

    async def _process_page(self, context, url: str):
        """Procesa una página individual."""
        page = await context.new_page()

        try:
            response = await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)  # Esperar carga JS

            html_content = await page.content()
            page_title = await page.title()

            # Extraer datos
            emails = self._extract_emails(html_content)
            phones = self._extract_phones(html_content)
            addresses = self._extract_addresses(html_content)
            social_links = self._extract_social_links(html_content, url)

            # Extraer meta información
            meta_data = await self._extract_meta_data(page)

            # Extraer enlaces internos para seguir
            internal_links = await self._extract_internal_links(page, url)

            # Guardar datos
            page_data = {
                "url": url,
                "title": page_title,
                "status": response.status if response else 0,
                "emails": emails,
                "phones": phones,
                "addresses": addresses,
                "social_links": social_links,
                "meta": meta_data,
                "has_contact_info": bool(emails or phones or addresses)
            }

            self.pages_data.append(page_data)
            self.visited_urls.add(url)
            self.all_emails.update(emails)
            self.all_phones.update(phones)

            print(f"[CRAWLER] ✓ {url} - Emails: {len(emails)}, Teléfonos: {len(phones)}")

        except Exception as e:
            print(f"[CRAWLER] ✗ Error en {url}: {e}")
        finally:
            await page.close()

    def _extract_emails(self, html: str) -> list:
        """Extrae emails del HTML."""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, html)
        # Filtrar emails inválidos comunes
        filtered = [
            e for e in emails
            if not any(x in e.lower() for x in [
                '.png', '.jpg', '.gif', '.svg', 'example.com',
                'test@', 'email@', 'user@', 'name@'
            ])
        ]
        return list(set(filtered))[:5]  # Máximo 5 únicos

    def _extract_phones(self, html: str) -> list:
        """Extrae números de teléfono argentinos/internacionales."""
        phones = []

        # Patrones para Argentina
        patterns = [
            # +54 9 351 1234567
            r'\+54\s*9?\s*\d{2,4}\s*\d{3,4}\s*\d{4,6}',
            # 351-1234567
            r'\b\d{3,4}[-.\s]\d{6,8}\b',
            # (0351) 1234567
            r'\(?0?\d{2,4}\)?\s*\d{3,4}\s*\d{4,6}',
            # Tel: / Teléfono: prefijos
            r'(?:tel[eé]fono|tel|phone|whatsapp|wp)[:\s]+([\d\s\-+()]{8,20})',
            # Internacional genérico
            r'\+\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{4,10}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                # Limpiar el número
                if isinstance(match, tuple):
                    match = match[0]
                clean = re.sub(r'[^\d+]', '', match)
                if len(clean) >= 7:
                    phones.append(clean)

        return list(set(phones))[:5]

    def _extract_addresses(self, html: str) -> list:
        """Extrae direcciones físicas del HTML."""
        addresses = []

        # Keywords de dirección en español
        address_keywords = [
            r'(?:Avda?\.?|Avenida|Calle|Callej[oó]n|Camino|Ruta|Pasaje|Boulevard|Bv\.?)\s+[A-Z][a-zA-Z\s]+(?:\s+\d+)?',
            r'(?:C[oó]rdoba|Buenos Aires|Santa Fe|Mendoza|CABA|Rosario|La Plata)\s*,?\s*(?:Argentina)?',
            r'\b\d{4,5}\s*(?:C[oó]rdoba|Bs\.?As|Buenos Aires|Argentina)?\b',
        ]

        for pattern in address_keywords:
            matches = re.findall(pattern, html, re.IGNORECASE)
            addresses.extend(matches)

        # Limpiar y deduplicar
        clean_addresses = []
        for addr in addresses:
            addr = addr.strip()
            if len(addr) > 10 and addr not in clean_addresses:
                clean_addresses.append(addr)

        return clean_addresses[:5]

    def _extract_social_links(self, html: str, base_url: str) -> dict:
        """Extrae enlaces a redes sociales."""
        social_patterns = {
            'facebook': r'facebook\.com/[^"\s<>]+',
            'instagram': r'instagram\.com/[^"\s<>]+',
            'linkedin': r'linkedin\.com/(?:company|in)/[^"\s<>]+',
            'twitter': r'(?:twitter\.com|x\.com)/[^"\s<>]+',
            'youtube': r'youtube\.com/(?:channel|c|user)/[^"\s<>]+',
            'tiktok': r'tiktok\.com/@[^"\s<>]+',
        }

        found = {}
        for network, pattern in social_patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                found[network] = matches[0]

        return found

    async def _extract_meta_data(self, page):
        """Extrae meta tags útiles."""
        return await page.evaluate("""() => {
            const getMeta = (name) => {
                const elem = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                return elem ? elem.content : null;
            };

            return {
                description: getMeta('description') || getMeta('og:description'),
                author: getMeta('author'),
                copyright: getMeta('copyright'),
                keywords: getMeta('keywords'),
                location: getMeta('geo.placename') || getMeta('business:contact_data:locality'),
                phone: getMeta('business:contact_data:phone_number'),
                email: getMeta('business:contact_data:email'),
                street: getMeta('business:contact_data:street_address'),
                city: getMeta('business:contact_data:locality'),
                country: getMeta('business:contact_data:country_name'),
                lat: getMeta('geo.position')?.split(';')[0],
                lng: getMeta('geo.position')?.split(';')[1],
            };
        }""")

    async def _extract_internal_links(self, page, current_url: str) -> list:
        """Extrae enlaces internos para seguir crawleando."""
        links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href)
                .filter(href => href.startsWith('http'));
        }""")

        internal = []
        current_domain = urlparse(current_url).netloc

        for link in links[:20]:  # Limitar a 20 enlaces
            parsed = urlparse(link)
            if parsed.netloc == current_domain:
                # Normalizar URL
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if clean_url not in internal and clean_url not in self.visited_urls:
                    internal.append(clean_url)

        return internal[:10]  # Máximo 10 nuevos enlaces


async def crawl_website(url: str, max_pages: int = 15):
    """
    Función helper para crawling rápido.

    Args:
        url: URL inicial
        max_pages: Máximo de páginas a visitar

    Returns:
        dict con resultados del crawling
    """
    crawler = SiteCrawler(max_pages=max_pages)
    return await crawler.crawl(url)


if __name__ == "__main__":
    # Prueba
    async def test():
        result = await crawl_website("https://ejemplo.com", max_pages=5)
        print("\n" + "="*60)
        print("RESULTADO DEL CRAWLING")
        print("="*60)
        print(f"Páginas visitadas: {result['total_pages']}")
        print(f"Emails encontrados: {result['emails_found']}")
        print(f"Teléfonos encontrados: {result['phones_found']}")
        print("\nDetalles por página:")
        for page in result['pages']:
            print(f"\n- {page['url']}")
            print(f"  Título: {page['title'][:50]}...")
            print(f"  Emails: {page['emails']}")
            print(f"  Teléfonos: {page['phones']}")

    asyncio.run(test())
