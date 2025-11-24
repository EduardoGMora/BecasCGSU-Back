from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from database import supabase_admin
from auth_utils import get_current_user_profile 

router = APIRouter()


class ApplicationCreate(BaseModel):
    user_id: str
    scholarship_id: str 
    university_id: str 

class ApplicationUpdate(BaseModel):
    scholarship_id: Optional[str] = None
    university_id: Optional[str] = None


@router.post("/applications")
async def create_application(app_data: ApplicationCreate):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('applications').insert({
            "user_id": app_data.user_id,
            "scholarship_id": app_data.scholarship_id,
            "university_id": app_data.university_id,
            "status": "pending"
        }).execute()
        
        return {"status": "success", "message": "Aplicación creada", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear: {str(e)}")


# 2. MODIFICAR (Update)
@router.put("/applications/{application_id}")
async def update_application(application_id: int, app_data: ApplicationUpdate):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    update_data = {k: v for k, v in app_data.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="Sin datos para actualizar")

    try:
        response = supabase_admin.table('applications').update(update_data).eq('id', application_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Aplicación no encontrada")
        return {"status": "success", "message": "Actualizado", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 3. ELIMINAR (Delete)
@router.delete("/applications/{application_id}")
async def delete_application(application_id: int):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('applications').delete().eq('id', application_id).execute()
        if not response.data:
             raise HTTPException(status_code=404, detail="Aplicación no encontrada")
        return {"status": "success", "message": "Eliminado", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/applications") 
async def get_applications(profile: dict = Depends(get_current_user_profile)):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="BD no disponible")

    
    role = profile.get('role', 'user')     
    campus = profile.get('campus')         
    user_id = profile.get('id')           

    print(f"DEBUG: Usuario {user_id} solicitando datos. Rol: {role}. Campus: {campus}")

    try:
        query = supabase_admin.table('applications').select('*, scholarships(*)')
        if role == 'admin':
            pass 

        elif role == 'campus_admin':
            if not campus:
                raise HTTPException(status_code=403, detail="Tu usuario es Admin de Sede pero no tiene campus asignado en su perfil.")
        
            query = query.eq('university_id', campus)

        else:
            query = query.eq('user_id', user_id)

        response = query.execute()
        
        return {
            "status": "success",
            "role_detected": role,
            "campus_filter": campus if role == 'campus_admin' else "N/A",
            "count": len(response.data),
            "data": response.data
        }

    except Exception as e:
        print(f"Error al obtener aplicaciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al obtener aplicaciones")