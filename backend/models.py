from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, JSON
from sqlalchemy.sql import func
import database
import enum

class LeadStatus(str, enum.Enum):
    nuevo = "nuevo"
    investigando = "investigando"
    contactado = "contactado"
    reunion = "reunion"
    ganado = "ganado"
    perdido = "perdido"

class Prospecto(database.Base):
    __tablename__ = "prospectos"

    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String(255), index=True)
    url = Column(String(255), nullable=True)

    # Datos de Contacto Básicos
    telefono = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    contacto_clave = Column(String(255), nullable=True)

    # NUEVOS: Datos de Contacto Enriquecidos
    direccion = Column(Text, nullable=True)
    ciudad = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)
    codigo_postal = Column(String(20), nullable=True)
    pais = Column(String(50), nullable=True)

    # NUEVOS: Datos del Dueño/Responsable
    nombre_dueno = Column(String(255), nullable=True)
    cargo_dueno = Column(String(100), nullable=True)
    email_dueno = Column(String(255), nullable=True)
    telefono_dueno = Column(String(100), nullable=True)
    fuente_contacto = Column(String(100), nullable=True)  # 'schema_org', 'whois', 'about_page'

    # NUEVOS: Redes Sociales
    redes_sociales = Column(JSON, nullable=True)

    # Datos de Auditoría
    falla_detectada = Column(String(255), nullable=True)
    emails_hallados = Column(String(500), nullable=True)
    telefonos_hallados = Column(String(500), nullable=True)  # NUEVO
    auditoria_texto = Column(Text, nullable=True)
    informe_detallado = Column(JSON, nullable=True)
    puntos_de_dolor = Column(Text, nullable=True)

    # NUEVOS: Auditoría Técnica Completa
    audit_tecnico = Column(JSON, nullable=True)
    tecnologias_detectadas = Column(JSON, nullable=True)
    paginas_auditadas = Column(Integer, default=0)

    # NUEVOS: Datos WHOIS
    whois_data = Column(JSON, nullable=True)
    dominio_creado = Column(DateTime(timezone=True), nullable=True)
    dominio_expira = Column(DateTime(timezone=True), nullable=True)
    antiguedad_dominio = Column(Integer, nullable=True)  # en años

    # Crawl Data
    urls_visitadas = Column(JSON, nullable=True)

    # Estado
    estado = Column(Enum(LeadStatus), default=LeadStatus.nuevo)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
