from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import httpx
import asyncio

import models, schemas
from database import get_db

router = APIRouter(
    prefix="/api/prospectos",
    tags=["prospectos"]
)

@router.get("/", response_model=List[schemas.ProspectoOut])
def read_prospectos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    prospectos = db.query(models.Prospecto).offset(skip).limit(limit).all()
    return prospectos

@router.get("/{prospecto_id}", response_model=schemas.ProspectoOut)
def read_prospecto(prospecto_id: int, db: Session = Depends(get_db)):
    db_prospecto = db.query(models.Prospecto).filter(models.Prospecto.id == prospecto_id).first()
    if db_prospecto is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")
    return db_prospecto

@router.post("/", response_model=schemas.ProspectoOut)
def create_prospecto(prospecto: schemas.ProspectoCreate, db: Session = Depends(get_db)):
    db_prospecto = models.Prospecto(**prospecto.model_dump())
    db.add(db_prospecto)
    db.commit()
    db.refresh(db_prospecto)
    return db_prospecto

@router.put("/{prospecto_id}", response_model=schemas.ProspectoOut)
def update_prospecto(prospecto_id: int, prospecto: schemas.ProspectoUpdate, db: Session = Depends(get_db)):
    db_prospecto = db.query(models.Prospecto).filter(models.Prospecto.id == prospecto_id).first()
    if not db_prospecto:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")
    
    update_data = prospecto.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prospecto, key, value)
        
    db.commit()
    db.refresh(db_prospecto)
    return db_prospecto

@router.delete("/{prospecto_id}")
def delete_prospecto(prospecto_id: int, db: Session = Depends(get_db)):
    db_prospecto = db.query(models.Prospecto).filter(models.Prospecto.id == prospecto_id).first()
    if not db_prospecto:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")
        
    db.delete(db_prospecto)
    db.commit()
    return {"message": "Prospecto eliminado exitosamente"}

async def run_audit_in_background(prospecto_id: int, url: str):
    from database import SessionLocal
    db = SessionLocal()
    
    # Notificamos al simulador del Mac Pro (Worker)
    # Primero, obtenemos el prospecto para asegurar que tenemos la URL más reciente y para la actualización posterior
    db_prospecto = db.query(models.Prospecto).filter(models.Prospecto.id == prospecto_id).first()
    if not db_prospecto:
        # Si el prospecto no existe, no hay nada que auditar o actualizar
        db.close()
        return

    try:
        # Damos 180 segundos (3 minutos) de timeout para auditorías profundas
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post("http://localhost:8001/auditar", json={"url": db_prospecto.url})
            if response.status_code == 200:
                result = response.json()
            else:
                result = {
                    "status": "error", 
                    "falla_encontrada": f"Worker error ({response.status_code})",
                    "error": response.text
                }
    except Exception as e:
        result = {
            "error": str(e), 
            "status": "error", 
            "falla_encontrada": f"Error de conexión: {str(e)[:50]}"
        }

    # Actualizamos el prospecto en base al resultado del Worker
    if db_prospecto:
        if result.get("status") in ["success", "partial"]:
            db_prospecto.estado = models.LeadStatus.contactado
            db_prospecto.falla_detectada = result.get("falla_encontrada")

            # Nuevos Campos de Auditoría Profunda
            db_prospecto.informe_detallado = result.get("informe_detallado")
            db_prospecto.puntos_de_dolor = result.get("puntos_de_dolor")

            # Emails y Teléfonos
            emails = result.get("emails_encontrados", [])
            db_prospecto.emails_hallados = ", ".join(emails) if isinstance(emails, list) else str(emails)

            telefonos = result.get("telefonos_encontrados", [])
            db_prospecto.telefonos_hallados = ", ".join(telefonos) if isinstance(telefonos, list) else str(telefonos)

            # Datos de Contacto Enriquecidos
            db_prospecto.telefono = result.get("telefono")
            db_prospecto.email = result.get("email")
            db_prospecto.direccion = result.get("direccion")
            db_prospecto.ciudad = result.get("ciudad")
            db_prospecto.provincia = result.get("provincia")

            # Datos del Dueño
            db_prospecto.nombre_dueno = result.get("nombre_dueno")
            db_prospecto.cargo_dueno = result.get("cargo_dueno")
            db_prospecto.email_dueno = result.get("email_dueno")
            db_prospecto.telefono_dueno = result.get("telefono_dueno")

            # Redes Sociales
            db_prospecto.redes_sociales = result.get("redes_sociales")

            # Auditoría Técnica
            db_prospecto.audit_tecnico = result.get("informe_detallado")
            db_prospecto.tecnologias_detectadas = result.get("informe_detallado", {}).get("tecnologias")
            db_prospecto.paginas_auditadas = result.get("paginas_recorridas", 0)

            # WHOIS
            db_prospecto.whois_data = result.get("whois_data")
            db_prospecto.antiguedad_dominio = result.get("antiguedad_dominio")

            # Crawl Data
            crawl_data = result.get("crawl_data", {})
            db_prospecto.urls_visitadas = crawl_data.get("urls_visitadas", [])

            # Contacto clave sugerido
            if result.get("nombre_dueno"):
                db_prospecto.contacto_clave = result.get("nombre_dueno")

        else:
            db_prospecto.estado = models.LeadStatus.perdido
            db_prospecto.falla_detectada = result.get("falla_encontrada", "Error de conexión")
        
        db.commit()
    db.close()

@router.post("/{prospecto_id}/iniciar-auditoria")
async def start_audit(prospecto_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_prospecto = db.query(models.Prospecto).filter(models.Prospecto.id == prospecto_id).first()
    if not db_prospecto:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")
    
    if not db_prospecto.url:
        raise HTTPException(status_code=400, detail="El prospecto no tiene URL configurada.")

    # Cambiamos estado temporal "investigando"
    db_prospecto.estado = models.LeadStatus.investigando
    db.commit()
    db.refresh(db_prospecto)

    # Lanzamos el ping asíncrono en background simulando delegar a la Mac
    background_tasks.add_task(run_audit_in_background, prospecto_id, db_prospecto.url)

    return {"message": "Bot enviado", "prospecto": db_prospecto}
