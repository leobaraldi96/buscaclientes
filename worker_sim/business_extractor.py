"""
Módulo Business Extractor - Extrae datos de negocio estructurados
Incluye: Schema.org markup, datos de contacto, información del dueño
"""
import re
import json
from typing import Dict, List, Optional


class BusinessExtractor:
    """
    Extrae información de negocio de HTML usando múltiples técnicas:
    - Schema.org JSON-LD
    - Meta tags Open Graph / Business
    - Análisis de texto (NLP simple)
    - Footer detection
    """

    def __init__(self):
        self.contact_data = {
            "nombre_dueno": None,
            "cargo_dueno": None,
            "email_dueno": None,
            "telefono_dueno": None,
            "telefono_empresa": None,
            "direccion": None,
            "ciudad": None,
            "provincia": None,
            "codigo_postal": None,
            "pais": None,
            "redes_sociales": {},
            "horarios": None,
            "emails_encontrados": [],
            "telefonos_encontrados": [],
            "fuente_datos": [],
            "whatsapp": None,
            "google_maps": None,
        }

    def extract_from_html(self, html: str, url: str, page_title: str = "") -> Dict:
        """
        Extrae todos los datos de negocio disponibles del HTML.

        Args:
            html: Contenido HTML de la página
            url: URL de la página
            page_title: Título de la página

        Returns:
            dict con datos estructurados del negocio
        """
        # 1. Schema.org JSON-LD
        schema_data = self._extract_schema_org(html)
        self._process_schema_data(schema_data)

        # 2. Meta tags
        meta_data = self._extract_meta_contact(html)
        self._process_meta_data(meta_data)

        # 3. Footer scraping
        footer_data = self._extract_footer_info(html)
        self._process_footer_data(footer_data)

        # 4. WhatsApp Detection (CRÍTICO para ventas)
        whatsapp = self._extract_whatsapp(html)
        if whatsapp:
            self.contact_data["whatsapp"] = whatsapp
            self.contact_data["fuente_datos"].append("whatsapp_link")

        # 5. Maps / Iframe Detection
        maps_link = self._extract_maps_link(html)
        if maps_link:
            self.contact_data["google_maps"] = maps_link
            self.contact_data["fuente_datos"].append("google_maps_iframe")

        # 6. Extracción de texto general
        text_data = self._extract_from_text(html)
        self._process_text_data(text_data)

        # 7. Redes sociales (Mejorado buscando en hrefs)
        social_data = self._extract_social_media(html)
        self.contact_data["redes_sociales"].update(social_data)

        # Limpiar y normalizar
        self._normalize_data()

        return self.contact_data

    def _extract_schema_org(self, html: str) -> List[Dict]:
        """Extrae datos estructurados Schema.org (JSON-LD)."""
        # Buscar script JSON-LD
        pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        schemas = []
        for match in matches:
            try:
                # Limpiar comentarios HTML si existen
                clean_json = re.sub(r'<![^>]*>', '', match)
                data = json.loads(clean_json)
                schemas.append(data)
            except json.JSONDecodeError:
                continue

        return schemas

    def _process_schema_data(self, schemas: List[Dict]):
        """Procesa datos Schema.org extraídos."""
        for schema in schemas:
            schema_type = schema.get("@type", "").lower()

            # Persona (dueño, fundador, etc.)
            if schema_type in ["person", "contactpoint"]:
                if not self.contact_data["nombre_dueno"]:
                    name = schema.get("name") or schema.get("givenName", "") + " " + schema.get("familyName", "")
                    if name and name.strip():
                        self.contact_data["nombre_dueno"] = name.strip()
                        self.contact_data["fuente_datos"].append("schema_person")

                job = schema.get("jobTitle") or schema.get("role")
                if job and not self.contact_data["cargo_dueno"]:
                    self.contact_data["cargo_dueno"] = job

                email = schema.get("email")
                if email and not self.contact_data["email_dueno"]:
                    self.contact_data["email_dueno"] = email

                phone = schema.get("telephone") or schema.get("phone")
                if phone:
                    self.contact_data["telefonos_encontrados"].append(phone)

            # Organización / Negocio Local
            if schema_type in ["organization", "localbusiness", "store", "professionalService", "corporation"]:
                # Teléfono de la empresa
                phone = schema.get("telephone") or schema.get("phone")
                if phone:
                    self.contact_data["telefono_empresa"] = phone
                    self.contact_data["fuente_datos"].append("schema_business")

                # Email
                email = schema.get("email")
                if email:
                    self.contact_data["emails_encontrados"].append(email)

                # Dirección
                address = schema.get("address")
                if isinstance(address, dict):
                    self._process_address_dict(address)
                elif isinstance(address, str):
                    self.contact_data["direccion"] = address

                # Horarios
                hours = schema.get("openingHours") or schema.get("openingHoursSpecification")
                if hours:
                    self.contact_data["horarios"] = hours

                # URL y redes
                same_as = schema.get("sameAs", [])
                if isinstance(same_as, str):
                    same_as = [same_as]
                for link in same_as:
                    self._categorize_social_link(link)

                # Fundador / Dueño
                founder = schema.get("founder")
                if isinstance(founder, dict):
                    if not self.contact_data["nombre_dueno"]:
                        name = founder.get("name")
                        if name:
                            self.contact_data["nombre_dueno"] = name
                            self.contact_data["fuente_datos"].append("schema_founder")

            # Página "About" / Sitio Web
            if schema_type in ["aboutpage", "profilepage", "webpage"]:
                author = schema.get("author")
                if isinstance(author, dict):
                    name = author.get("name")
                    if name and not self.contact_data["nombre_dueno"]:
                        self.contact_data["nombre_dueno"] = name
                        self.contact_data["fuente_datos"].append("schema_author")

    def _extract_meta_contact(self, html: str) -> Dict:
        """Extrae meta tags de contacto de negocio."""
        meta_data = {}

        # Open Graph / Business meta tags
        patterns = {
            "business_name": r'<meta[^>]*(?:name|property)="(?:og:site_name|business:name)"[^>]*content="([^"]*)"',
            "business_phone": r'<meta[^>]*(?:name|property)="(?:business:contact_data:phone_number|phone)"[^>]*content="([^"]*)"',
            "business_email": r'<meta[^>]*(?:name|property)="(?:business:contact_data:email|email)"[^>]*content="([^"]*)"',
            "business_street": r'<meta[^>]*name="business:contact_data:street_address"[^>]*content="([^"]*)"',
            "business_city": r'<meta[^>]*name="business:contact_data:locality"[^>]*content="([^"]*)"',
            "business_region": r'<meta[^>]*name="business:contact_data:region"[^>]*content="([^"]*)"',
            "business_country": r'<meta[^>]*name="business:contact_data:country_name"[^>]*content="([^"]*)"',
            "business_zip": r'<meta[^>]*name="business:contact_data:postal_code"[^>]*content="([^"]*)"',
            "author": r'<meta[^>]*name="author"[^>]*content="([^"]*)"',
            "geo_position": r'<meta[^>]*name="geo.position"[^>]*content="([^"]*)"',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                meta_data[key] = match.group(1).strip()

        return meta_data

    def _process_meta_data(self, meta_data: Dict):
        """Procesa meta tags extraídos."""
        if meta_data.get("business_phone"):
            self.contact_data["telefono_empresa"] = meta_data["business_phone"]

        if meta_data.get("business_email"):
            self.contact_data["emails_encontrados"].append(meta_data["business_email"])

        if meta_data.get("author") and not self.contact_data["nombre_dueno"]:
            # Verificar que no sea un nombre genérico
            author = meta_data["author"]
            if not any(x in author.lower() for x in ['team', 'equipo', 'staff', 'company', 'empresa']):
                self.contact_data["nombre_dueno"] = author
                self.contact_data["fuente_datos"].append("meta_author")

        # Dirección
        address_parts = []
        if meta_data.get("business_street"):
            address_parts.append(meta_data["business_street"])
        if meta_data.get("business_city"):
            address_parts.append(meta_data["business_city"])
            self.contact_data["ciudad"] = meta_data["business_city"]
        if meta_data.get("business_region"):
            address_parts.append(meta_data["business_region"])
            self.contact_data["provincia"] = meta_data["business_region"]
        if meta_data.get("business_zip"):
            self.contact_data["codigo_postal"] = meta_data["business_zip"]
        if meta_data.get("business_country"):
            address_parts.append(meta_data["business_country"])
            self.contact_data["pais"] = meta_data["business_country"]

        if address_parts:
            self.contact_data["direccion"] = ", ".join(address_parts)

    def _extract_footer_info(self, html: str) -> Dict:
        """Extrae información típicamente encontrada en el footer."""
        footer_data = {}

        # Buscar sección footer o bottom
        footer_patterns = [
            r'<footer[^>]*>(.*?)</footer>',
            r'<div[^>]*class="[^"]*(?:footer|bottom|pie)[^"]*"[^>]*>(.*?)</div>',
            r'<section[^>]*class="[^"]*(?:footer|contact|info)[^"]*"[^>]*>(.*?)</section>',
        ]

        footer_html = ""
        for pattern in footer_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                footer_html += match.group(1) + " "

        if footer_html:
            # Buscar teléfono en footer
            phone_patterns = [
                r'(?:Tel[eé]fono|Tel|Phone|Llamar|Contacto)[:\s]+([\d\s\-+()]{7,20})',
                r'\+54\s*\d[\d\s\-]{8,15}',
                r'\(\s*\d{3,4}\s*\)\s*\d{6,8}',
            ]
            for pattern in phone_patterns:
                matches = re.findall(pattern, footer_html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    clean = re.sub(r'[^\d\s\-+()]', '', match).strip()
                    if len(clean) >= 7:
                        footer_data.setdefault("phones", []).append(clean)

            # Buscar dirección en footer
            address_keywords = [
                r'(?:Av\.?|Avenida|Calle|Ubicaci[oó]n|Sucursal)[:\s]+([^<\n]{10,100})',
                r'(?:Direcci[oó]n|Address)[:\s]+([^<\n]{10,100})',
            ]
            for pattern in address_keywords:
                match = re.search(pattern, footer_html, re.IGNORECASE)
                if match:
                    footer_data["address"] = match.group(1).strip()
                    break

        return footer_data

    def _process_footer_data(self, footer_data: Dict):
        """Procesa datos del footer."""
        if footer_data.get("phones"):
            self.contact_data["telefonos_encontrados"].extend(footer_data["phones"])
            self.contact_data["fuente_datos"].append("footer")

        if footer_data.get("address"):
            if not self.contact_data["direccion"]:
                self.contact_data["direccion"] = footer_data["address"]

    def _extract_whatsapp(self, html: str) -> Optional[str]:
        """Extrae números de WhatsApp de enlaces wa.me o api.whatsapp."""
        patterns = [
            r'wa\.me/(\d+)',
            r'api\.whatsapp\.com/send\?phone=(\d+)',
            r'whatsapp://send\?phone=(\d+)',
            r'web\.whatsapp\.com/send\?phone=(\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def _extract_maps_link(self, html: str) -> Optional[str]:
        """Extrae enlaces de Google Maps de iframes o links directos."""
        patterns = [
            r'google\.com/maps/embed\?pb=([^"\s]*)',
            r'goo\.gl/maps/([^"\s]*)',
            r'google\.com\.ar/maps/place/([^"\s]*)',
            r'maps\.app\.goo\.gl/([^"\s]*)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(0)
        return None

    def _extract_from_text(self, html: str) -> Dict:
        """Extrae información analizando el texto de la página."""
        text_data = {}

        # Limpiar HTML para obtener texto legible
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Buscar cargos ejecutivos
        executive_patterns = [
            r'(?:Director|CEO|Gerente|Fundador|Propietario|Dueño|Owner|Founder|Manager)[\s\w]*[:\s]+([A-Z][a-zA-Z\s]{3,30})(?:\s|<|$)',
            r'([A-Z][a-zA-Z\s]{3,25})\s*-\s*(?:Director|CEO|Gerente|Fundador)',
        ]

        for pattern in executive_patterns:
            matches = re.findall(pattern, text)
            if matches:
                text_data["executive_names"] = matches[:3]
                break

        return text_data

    def _process_text_data(self, text_data: Dict):
        """Procesa datos extraídos del texto."""
        if text_data.get("executive_names") and not self.contact_data["nombre_dueno"]:
            # Tomar el primero que parezca un nombre válido (al menos 2 palabras)
            for name in text_data["executive_names"]:
                name_clean = name.strip()
                if len(name_clean.split()) >= 2 and len(name_clean) < 40:
                    self.contact_data["nombre_dueno"] = name_clean
                    self.contact_data["fuente_datos"].append("text_analysis")
                    break

    def _extract_social_media(self, html: str) -> Dict:
        """Extrae enlaces a redes sociales buscando en atributos href."""
        social = {}
        
        # Patrones más robustos buscando en el HTML completo (incluyendo tags a href)
        patterns = {
            "facebook": r'href="[^"]*facebook\.com/([^"/#?\s]+)',
            "instagram": r'href="[^"]*instagram\.com/([^"/#?\s]+)',
            "linkedin": r'href="[^"]*linkedin\.com/(?:company|in)/([^"/#?\s]+)',
            "twitter": r'href="[^"]*(?:twitter\.com|x\.com)/([^"/#?\s]+)',
            "youtube": r'href="[^"]*youtube\.com/(?:channel/|c/|user/|@)?([^"/#?\s]+)',
            "tiktok": r'href="[^"]*tiktok\.com/@([^"/#?\s]+)',
        }

        for network, pattern in patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match and match.lower() not in ['sharer', 'share', 'intent', 'p', 'pages', 'groups']:
                    # Limpiar la URL final
                    clean_id = match.split('?')[0].split('&')[0].rstrip('/')
                    if clean_id:
                        social[network] = clean_id
                        break

        return social

    def _categorize_social_link(self, link: str):
        """Categoriza un enlace de social media."""
        link_lower = link.lower()
        for network in ['facebook', 'instagram', 'linkedin', 'twitter', 'youtube', 'tiktok']:
            if network in link_lower:
                self.contact_data["redes_sociales"][network] = link
                break

    def _process_address_dict(self, address: Dict):
        """Procesa un diccionario de dirección Schema.org."""
        parts = []

        if address.get("streetAddress"):
            parts.append(address["streetAddress"])
            self.contact_data["direccion"] = address["streetAddress"]

        if address.get("addressLocality"):
            parts.append(address["addressLocality"])
            self.contact_data["ciudad"] = address["addressLocality"]

        if address.get("addressRegion"):
            parts.append(address["addressRegion"])
            self.contact_data["provincia"] = address["addressRegion"]

        if address.get("postalCode"):
            self.contact_data["codigo_postal"] = address["postalCode"]

        if address.get("addressCountry"):
            parts.append(address["addressCountry"])
            self.contact_data["pais"] = address["addressCountry"]

        if parts and not self.contact_data["direccion"]:
            self.contact_data["direccion"] = ", ".join(parts)

    def _normalize_data(self):
        """Limpia y normaliza los datos extraídos."""
        # Deduplicar emails
        self.contact_data["emails_encontrados"] = list(set(
            e for e in self.contact_data["emails_encontrados"] if '@' in e
        ))[:5]

        # Deduplicar teléfonos
        self.contact_data["telefonos_encontrados"] = list(set(
            self.contact_data["telefonos_encontrados"]
        ))[:5]

        # Limpiar nombre del dueño
        if self.contact_data["nombre_dueno"]:
            name = self.contact_data["nombre_dueno"].strip()
            # Quitar títulos comunes
            for title in ['Dr.', 'Dra.', 'Lic.', 'Ing.', 'Sr.', 'Sra.', 'Mr.', 'Mrs.']:
                name = name.replace(title, '').strip()
            self.contact_data["nombre_dueno"] = name

        # Si no hay fuentes, agregar nota
        if not self.contact_data["fuente_datos"]:
            self.contact_data["fuente_datos"].append("no_structured_data_found")


def extract_business_data(html: str, url: str = "", page_title: str = "") -> Dict:
    """
    Función helper para extraer datos de negocio de HTML.

    Args:
        html: Contenido HTML
        url: URL de la página
        page_title: Título de la página

    Returns:
        dict con todos los datos de contacto extraídos
    """
    extractor = BusinessExtractor()
    return extractor.extract_from_html(html, url, page_title)


if __name__ == "__main__":
    # Prueba con HTML de ejemplo
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="author" content="Juan Pérez">
        <meta property="business:contact_data:phone_number" content="+54 351 1234567">
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Mi Empresa",
            "telephone": "+54 351 7654321",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "Av. Siempre Viva 123",
                "addressLocality": "Córdoba",
                "addressRegion": "Córdoba",
                "addressCountry": "Argentina"
            },
            "founder": {
                "@type": "Person",
                "name": "María González",
                "jobTitle": "Directora General"
            }
        }
        </script>
    </head>
    <body>
        <footer>
            Teléfono: +54 351 9876543
            Dirección: Calle Falsa 123
        </footer>
    </body>
    </html>
    """

    result = extract_business_data(sample_html, "https://ejemplo.com", "Ejemplo")
    print("=" * 60)
    print("DATOS DE NEGOCIO EXTRAÍDOS")
    print("=" * 60)
    for key, value in result.items():
        if value:
            print(f"{key}: {value}")
