from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from auth_utils import get_current_user_profile 

router = APIRouter()

# --- MODELOS DE DATOS ---

class ApplicationCreate(BaseModel):
    student_id: str      # Coincide con tu tabla y script
    scholarship_id: str  # UUID de la beca
    # university_id ELIMINADO (ya no existe en la tabla)

class ApplicationUpdate(BaseModel):
    scholarship_id: Optional[str] = None
    # status: Lo maneja el admin

# --- RUTAS ---

# 1. AGREGAR (Create)
@router.post(path= "/applications")
async def create_application(app_data: ApplicationCreate):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="BD no disponible")

    try:
        # Insertamos con los nombres nuevos de columnas
        response = supabase_admin.table('applications').insert({
            "student_id": app_data.student_id,
            "scholarship_id": app_data.scholarship_id,
            "status": "pending"
        }).execute()
        
        return {"status": "success", "message": "Aplicación creada", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear: {str(e)}")


# 2. MODIFICAR (Update)
@router.put(path="/applications/{application_id}")
async def update_application(application_id: str, app_data: ApplicationUpdate):
    if not supabase_admin: raise HTTPException(status_code=503, detail="BD no disponible")

    update_data = {k: v for k, v in app_data.dict().items() if v is not None}
    if not update_data: raise HTTPException(status_code=400, detail="Sin datos")

    try:
        response = supabase_admin.table('applications').update(update_data).eq('id', application_id).execute()
        if not response.data: raise HTTPException(status_code=404, detail="No encontrada")
        return {"status": "success", "message": "Actualizado", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 3. ELIMINAR (Delete)
@router.delete(path="/applications/{application_id}")
async def delete_application(application_id: str):
    if not supabase_admin: raise HTTPException(status_code=503, detail="BD no disponible")

    try:
        response = supabase_admin.table('applications').delete().eq('id', application_id).execute()
        if not response.data: raise HTTPException(status_code=404, detail="No encontrada")
        return {"status": "success", "message": "Eliminado", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 4. LEER CON ROLES (Get Inteligente Adaptado)
@router.get(path="/applications") 
async def get_applications(profile: dict = Depends(get_current_user_profile)):
    if not supabase_admin: raise HTTPException(status_code=503, detail="BD no disponible")

    role = profile.get('role', 'user')
    campus = profile.get('campus')
    user_id = profile.get('id')

    try:
        # Hacemos JOIN con scholarships para saber de qué centro es la beca
        query = supabase_admin.table('applications').select('*, scholarships(*)')

        if role == 'admin':
            pass # Ve todo

        elif role == 'campus_admin':
            if not campus: raise HTTPException(status_code=403, detail="Admin sin campus asignado")
            # Filtrado manual en Python al final
            pass 

        else:
            # Usuario Normal: Filtramos por student_id
            query = query.eq('student_id', user_id)

        response = query.execute()
        data = response.data

        # Filtrado manual para Campus Admin
        if role == 'campus_admin':
            data = [
                app for app in data 
                if app.get('scholarships') and app['scholarships'].get('university_center_id') == campus
            ]

        return {
            "status": "success",
            "role_detected": role,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        print(f"Error fetching applications: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")