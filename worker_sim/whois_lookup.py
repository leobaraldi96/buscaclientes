"""
Módulo WHOIS Lookup - Extracción de datos del registro de dominio
"""
import whois
from datetime import datetime
import re


def extract_whois_data(domain: str):
    """
    Extrae información del registro WHOIS del dominio.

    Args:
        domain: Nombre de dominio (ej: 'ejemplo.com')

    Returns:
        dict con datos extraídos o None si falla
    """
    try:
        # Limpiar el dominio (quitar protocolo y path)
        domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

        w = whois.whois(domain)

        # Extraer emails del registrante
        emails = []
        if w.emails:
            if isinstance(w.emails, list):
                emails = [e for e in w.emails if e and '@' in str(e)]
            else:
                emails = [str(w.emails)] if '@' in str(w.emails) else []

        # Extraer datos del registrante
        registrante = None
        if w.name:
            registrante = str(w.name)
        elif w.registrant_name:
            registrante = str(w.registrant_name)
        elif w.org:
            registrante = str(w.org)

        # Extraer teléfono si existe
        telefono = None
        if w.phone:
            telefono = str(w.phone)
        elif w.registrant_phone:
            telefono = str(w.registrant_phone)

        # Extraer fechas
        creacion = None
        expiracion = None

        if w.creation_date:
            if isinstance(w.creation_date, list):
                creacion = w.creation_date[0]
            else:
                creacion = w.creation_date

        if w.expiration_date:
            if isinstance(w.expiration_date, list):
                expiracion = w.expiration_date[0]
            else:
                expiracion = w.expiration_date

        # Convertir a string ISO si es datetime
        if creacion and hasattr(creacion, 'isoformat'):
            creacion = creacion.isoformat()
        if expiracion and hasattr(expiracion, 'isoformat'):
            expiracion = expiracion.isoformat()

        # Calcular antigüedad del dominio
        antiguedad_anios = None
        if creacion and hasattr(w.creation_date, 'year'):
            try:
                if isinstance(w.creation_date, list):
                    fecha_creacion = w.creation_date[0]
                else:
                    fecha_creacion = w.creation_date
                antiguedad_anios = datetime.now().year - fecha_creacion.year
            except:
                pass

        return {
            "domain": domain,
            "registrar": str(w.registrar) if w.registrar else None,
            "registrante": registrante,
            "organizacion": str(w.org) if w.org else None,
            "emails": emails[:3],  # Máximo 3 emails
            "telefono": telefono,
            "pais": str(w.country) if w.country else None,
            "estado": str(w.state) if w.state else None,
            "ciudad": str(w.city) if w.city else None,
            "creacion": creacion,
            "expiracion": expiracion,
            "antiguedad_anios": antiguedad_anios,
            "name_servers": w.name_servers[:3] if w.name_servers else [],
            "dnssec": bool(w.dnssec) if w.dnssec else False,
            "fuente": "whois"
        }

    except Exception as e:
        print(f"[WHOIS] Error consultando {domain}: {str(e)}")
        return {
            "domain": domain,
            "error": str(e),
            "fuente": "whois"
        }


def extract_contact_hints(whois_data: dict):
    """
    Extrae pistas de contacto útiles para ventas desde datos WHOIS.

    Returns:
        dict con contacto_clave, telefono, email sugeridos
    """
    if not whois_data or whois_data.get("error"):
        return {}

    result = {}

    # Email del registrante
    if whois_data.get("emails"):
        # Filtrar emails que no sean de registros privados comunes
        emails_filtrados = [
            e for e in whois_data["emails"]
            if not any(x in e.lower() for x in [
                'privacy', 'proxy', 'whoisguard', 'cloudflare',
                'namecheap', 'godaddy', 'dominios', 'contacto@'
            ])
        ]
        if emails_filtrados:
            result["email"] = emails_filtrados[0]

    # Teléfono
    if whois_data.get("telefono"):
        tel = whois_data["telefono"]
        # Filtrar números obvios de privacidad
        if not any(x in tel.lower() for x in ['privacy', '0000', '9999']):
            result["telefono"] = tel

    # Nombre del registrante/organización
    if whois_data.get("registrante"):
        result["contacto_sugerido"] = whois_data["registrante"]
    elif whois_data.get("organizacion"):
        result["contacto_sugerido"] = whois_data["organizacion"]

    return result


if __name__ == "__main__":
    # Prueba
    import asyncio

    test_domains = [
        "google.com",
        "microsoft.com",
        "mercadolibre.com.ar"
    ]

    for domain in test_domains:
        print(f"\n{'='*50}")
        print(f"Consultando: {domain}")
        print('='*50)
        data = extract_whois_data(domain)
        if data:
            print(f"Registrante: {data.get('registrante')}")
            print(f"Organización: {data.get('organizacion')}")
            print(f"Emails: {data.get('emails')}")
            print(f"Teléfono: {data.get('telefono')}")
            print(f"País: {data.get('pais')}")
            print(f"Antigüedad: {data.get('antiguedad_anios')} años")

            hints = extract_contact_hints(data)
            print(f"\nPistas de contacto: {hints}")
