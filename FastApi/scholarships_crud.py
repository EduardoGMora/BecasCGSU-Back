from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import supabase, supabase_admin # Usamos admin para escribir
from auth_utils import get_current_user_profile
from validators import (
    validate_scholarship_title,
    validate_scholarship_description,
    validate_scholarship_dates,
    validate_scholarship_status,
    validate_scholarship_requirements,
    validate_uuid,
    ValidationError,
    VALID_SCHOLARSHIP_STATUSES
)

router = APIRouter()

# --- SECURITY HELPERS ---

def verify_admin_or_campus_admin(profile: dict):
    """Verifica que el usuario sea admin o campus_admin."""
    if profile.get('role') not in ['admin', 'campus_admin']:
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado: Se requieren permisos de administrador"
        )

def verify_super_admin(profile: dict):
    """Verifica que el usuario sea super admin (admin global)."""
    if profile.get('role') != 'admin':
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado: Se requieren permisos de Super Admin"
        )

def verify_campus_ownership(profile: dict, university_center_id: str):
    """
    Verifica que un campus_admin solo pueda gestionar becas de su campus.
    Super admin puede gestionar cualquier campus.
    """
    role = profile.get('role')
    
    if role == 'admin':
        return True  # Super admin puede todo
    
    if role == 'campus_admin':
        campus = profile.get('campus')
        if not campus:
            raise HTTPException(
                status_code=403,
                detail="Tu usuario es Admin de Sede pero no tiene campus asignado"
            )
        if campus != university_center_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para gestionar becas de otro campus"
            )
        return True
    
    return False

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
# 1. CREAR BECA (Create) - Admin
@router.post(path= "/scholarships")
async def create_scholarship(
    scholarship: ScholarshipCreate,
    profile: dict = Depends(get_current_user_profile)
):
    """Crea una nueva beca. Requiere permisos de admin o campus_admin."""
    verify_admin_or_campus_admin(profile)

    # Verificar que campus_admin solo cree becas de su campus
    verify_campus_ownership(profile, scholarship.university_center_id)

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Falta Service Key para escritura")

    # Validar inputs
    try:
        validate_scholarship_title(scholarship.title)
        validate_scholarship_description(scholarship.description)
        validate_uuid(scholarship.university_center_id, "university_center_id")
        validate_uuid(scholarship.scholarship_type_id, "scholarship_type_id")
        validate_scholarship_dates(scholarship.application_start_date, scholarship.application_end_date)
        validate_scholarship_status(scholarship.status)
        validate_scholarship_requirements(scholarship.requirements)
    except ValidationError:
        raise

    try:
        # Convertimos el modelo a diccionario y las fechas a string ISO
        data = scholarship.dict()
        data['application_start_date'] = data['application_start_date'].isoformat()
        data['application_end_date'] = data['application_end_date'].isoformat()

        response = supabase_admin.table('scholarships').insert(data).execute()
        return {"status": "success", "message": "Beca creada", "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating scholarship: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al crear beca")

# 2. ACTUALIZAR BECA (Update) - Admin
@router.put(path= "/scholarships/{scholarship_id}")
async def update_scholarship(
    scholarship_id: str,
    scholarship: ScholarshipUpdate,
    profile: dict = Depends(get_current_user_profile)
):
    """Actualiza una beca existente. Requiere permisos de admin o campus_admin."""
    verify_admin_or_campus_admin(profile)

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Falta Service Key")

    # Validar scholarship_id
    validate_uuid(scholarship_id, "scholarship_id")

    # Validar campos si se proporcionan
    if scholarship.title:
        validate_scholarship_title(scholarship.title)
    if scholarship.description:
        validate_scholarship_description(scholarship.description)
    if scholarship.university_center_id:
        validate_uuid(scholarship.university_center_id, "university_center_id")
    if scholarship.scholarship_type_id:
        validate_uuid(scholarship.scholarship_type_id, "scholarship_type_id")
    if scholarship.status:
        validate_scholarship_status(scholarship.status)
    if scholarship.requirements is not None:
        validate_scholarship_requirements(scholarship.requirements)

    try:
        # Primero verificar que la beca existe y obtener su campus
        existing = supabase_admin.table('scholarships')\
            .select('university_center_id, application_start_date, application_end_date')\
            .eq('id', scholarship_id)\
            .single()\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")

        # Verificar permisos de campus
        verify_campus_ownership(profile, existing.data['university_center_id'])

        # Si se está cambiando el campus, verificar permisos para el nuevo campus
        if scholarship.university_center_id:
            verify_campus_ownership(profile, scholarship.university_center_id)

        # Filtramos campos vacíos
        update_data = {k: v for k, v in scholarship.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No se enviaron datos")

        # Validar fechas si se proporcionan
        start_date = scholarship.application_start_date or existing.data.get('application_start_date')
        end_date = scholarship.application_end_date or existing.data.get('application_end_date')
        if scholarship.application_start_date or scholarship.application_end_date:
            # Convertir strings a datetime si es necesario para validación
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            validate_scholarship_dates(start_date, end_date)

        # Serializar fechas si existen
        if 'application_start_date' in update_data:
            update_data['application_start_date'] = update_data['application_start_date'].isoformat()
        if 'application_end_date' in update_data:
            update_data['application_end_date'] = update_data['application_end_date'].isoformat()

        response = supabase_admin.table('scholarships').update(update_data).eq('id', scholarship_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")
        return {"status": "success", "message": "Beca actualizada", "data": response.data}

    except HTTPException:
        raise
    except ValidationError:
        raise
    except Exception as e:
        print(f"Error updating scholarship: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al actualizar beca")

# 3. ELIMINAR BECA (Delete) - Admin
@router.delete(path= "/scholarships/{scholarship_id}")
async def delete_scholarship(
    scholarship_id: str,
    profile: dict = Depends(get_current_user_profile)
):
    """Elimina una beca. Requiere permisos de admin o campus_admin."""
    verify_admin_or_campus_admin(profile)

    # Validar scholarship_id
    validate_uuid(scholarship_id, "scholarship_id")

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Falta Service Key")

    try:
        # Verificar que la beca existe y obtener su campus para validar permisos
        existing = supabase_admin.table('scholarships')\
            .select('university_center_id')\
            .eq('id', scholarship_id)\
            .single()\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")

        # Verificar permisos de campus
        verify_campus_ownership(profile, existing.data['university_center_id'])

        response = supabase_admin.table('scholarships').delete().eq('id', scholarship_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada (ya eliminada?)")
        return {"status": "success", "message": "Beca eliminada", "data": response.data}

    except HTTPException:
        raise
    except ValidationError:
        raise
    except Exception as e:
        print(f"Error deleting scholarship: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al eliminar beca")