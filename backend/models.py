from sqlalchemy import Column, Integer, String, Enum, DateTime, Text
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
    telefono = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    contacto_clave = Column(String(255), nullable=True)
    falla_detectada = Column(String(255), nullable=True)
    emails_hallados = Column(String(500), nullable=True)
    auditoria_texto = Column(Text, nullable=True)
    estado = Column(Enum(LeadStatus), default=LeadStatus.nuevo)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
