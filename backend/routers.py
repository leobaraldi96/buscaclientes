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
        # Damos 60 segundos de timeout porque los navegadores reales consumen su tiempo cargando JS, imágenes y WAFs.
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("http://localhost:8001/auditar", json={"url": db_prospecto.url})
            result = response.json()
    except Exception as e:
        result = {"error": str(e)}

    # Actualizamos el prospecto en base al resultado del Worker
    if db_prospecto: # Re-check in case it was deleted between fetch and update
        if "status" in result and result["status"] == "success":
            db_prospecto.estado = models.LeadStatus.contactado
            db_prospecto.falla_detectada = result.get("falla_encontrada")
            emails = result.get("emails_encontrados", [])
            db_prospecto.emails_hallados = ", ".join(emails) if isinstance(emails, list) else str(emails)
            db_prospecto.auditoria_texto = result.get("text_preview")
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
