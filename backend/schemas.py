from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from models import LeadStatus

class ProspectoBase(BaseModel):
    empresa: str
    url: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    contacto_clave: Optional[str] = None
    falla_detectada: Optional[str] = None
    emails_hallados: Optional[str] = None
    auditoria_texto: Optional[str] = None
    estado: Optional[LeadStatus] = LeadStatus.nuevo

class ProspectoCreate(ProspectoBase):
    pass

class ProspectoUpdate(BaseModel):
    empresa: Optional[str] = None
    url: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    contacto_clave: Optional[str] = None
    falla_detectada: Optional[str] = None
    emails_hallados: Optional[str] = None
    auditoria_texto: Optional[str] = None
    estado: Optional[LeadStatus] = None

class ProspectoOut(ProspectoBase):
    id: int
    creado_en: Optional[datetime]
    actualizado_en: Optional[datetime]

    class Config:
        from_attributes = True
