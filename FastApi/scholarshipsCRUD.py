from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import supabase, supabase_admin # Usamos admin para escribir

router = APIRouter()

# --- MODELOS DE DATOS ---

class ScholarshipCreate(BaseModel):
    title: str
    description: str
    university_center_id: str # UUID
    scholarship_type_id: str # UUID
    requirements: Optional[List[str]] = [] # JSONB: Lo manejamos como lista de textos
    application_start_date: datetime
    application_end_date: datetime
    status: str = "active"

class ScholarshipUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    university_center_id: Optional[str] = None
    scholarship_type_id: Optional[str] = None
    requirements: Optional[List[str]] = None
    application_start_date: Optional[datetime] = None
    application_end_date: Optional[datetime] = None
    status: Optional[str] = None

# --- RUTAS DEL CRUD ---

# 1. LISTAR BECAS (Read All) - Público
@router.get("/scholarships")
async def get_scholarships():
    """Obtiene todas las becas disponibles."""
    if not supabase:
        raise HTTPException(status_code=503, detail="BD no disponible")

    try:
        # Seleccionamos todo y ordenamos por fecha de creación
        response = supabase.table('scholarships').select('*').order('created_at', desc=True).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. OBTENER UNA BECA (Read One) - Público
@router.get("/scholarships/{scholarship_id}")
async def get_scholarship_by_id(scholarship_id: str):
    """Obtiene el detalle de una beca específica."""
    if not supabase:
        raise HTTPException(status_code=503, detail="BD no disponible")

    try:
        response = supabase.table('scholarships').select('*').eq('id', scholarship_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")
        return {"status": "success", "data": response.data}
    except Exception as e:
        # Supabase lanza error si .single() no encuentra nada, capturamos eso
        raise HTTPException(status_code=404, detail="Beca no encontrada")

# 3. CREAR BECA (Create) - Admin
@router.post("/scholarships")
async def create_scholarship(scholarship: ScholarshipCreate):
    """Crea una nueva beca."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Falta Service Key para escritura")

    try:
        # Convertimos el modelo a diccionario y las fechas a string ISO
        data = scholarship.dict()
        data['application_start_date'] = data['application_start_date'].isoformat()
        data['application_end_date'] = data['application_end_date'].isoformat()

        response = supabase_admin.table('scholarships').insert(data).execute()
        return {"status": "success", "message": "Beca creada", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear: {str(e)}")

# 4. ACTUALIZAR BECA (Update) - Admin
@router.put("/scholarships/{scholarship_id}")
async def update_scholarship(scholarship_id: str, scholarship: ScholarshipUpdate):
    """Actualiza una beca existente."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Falta Service Key")

    # Filtramos campos vacíos
    update_data = {k: v for k, v in scholarship.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos")

    # Serializar fechas si existen
    if 'application_start_date' in update_data:
        update_data['application_start_date'] = update_data['application_start_date'].isoformat()
    if 'application_end_date' in update_data:
        update_data['application_end_date'] = update_data['application_end_date'].isoformat()

    try:
        response = supabase_admin.table('scholarships').update(update_data).eq('id', scholarship_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")
        return {"status": "success", "message": "Beca actualizada", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 5. ELIMINAR BECA (Delete) - Admin
@router.delete("/scholarships/{scholarship_id}")
async def delete_scholarship(scholarship_id: str):
    """Elimina una beca."""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Falta Service Key")

    try:
        response = supabase_admin.table('scholarships').delete().eq('id', scholarship_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada (ya eliminada?)")
        return {"status": "success", "message": "Beca eliminada", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))