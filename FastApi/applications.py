from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin 

router = APIRouter()


class ApplicationCreate(BaseModel):
    student_id: str
    scholarship_id: str


class ApplicationUpdate(BaseModel):
    scholarship_id: Optional[str] = None

@router.post("/applications")
async def create_application(app_data: ApplicationCreate):
    """
    Crea una nueva aplicación.
    Requiere: student_id, scholarship_id
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible (Falta Service Key)")

    try:
        response = supabase_admin.table('applications').insert({
            "student_id": app_data.student_id,
            "scholarship_id": app_data.scholarship_id,
            "status": "pending"
        }).execute()
        
        return {
            "status": "success", 
            "message": "Aplicación creada correctamente", 
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear aplicación: {str(e)}")


# 2. MODIFICAR (Update)
@router.put("/applications/{application_id}")
async def update_application(application_id: str, app_data: ApplicationUpdate):
    """
    Modifica una aplicación existente por su ID.
    Solo actualiza los campos que se envíen .
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    update_data = {k: v for k, v in app_data.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    try:
        response = supabase_admin.table('applications')\
            .update(update_data)\
            .eq('id', application_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Aplicación no encontrada o no se pudo actualizar")

        return {
            "status": "success", 
            "message": "Aplicación actualizada correctamente", 
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")


# 3. ELIMINAR (Delete)
@router.delete("/applications/{application_id}")
async def delete_application(application_id: str):
    """
    Elimina una aplicación por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('applications').delete().eq('id', application_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Aplicación no encontrada (quizás ya fue borrada)")

        return {
            "status": "success", 
            "message": "Aplicación eliminada correctamente", 
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")


@router.get("/applications/user/{student_id}")
async def get_user_applications(student_id: str):
    """
    Obtiene todas las aplicaciones de un usuario específico.
    Incluye los datos de la beca relacionada.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:

        response = supabase_admin.table('applications')\
            .select('*, scholarships(*)')\
            .eq('student_id', student_id)\
            .execute()
            
        return {
            "status": "success",
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))