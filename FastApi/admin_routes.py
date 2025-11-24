from fastapi import APIRouter, HTTPException, Depends, Body
from database import supabase_admin
from auth_utils import get_current_user_profile
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter()

class ApplicationStatusUpdate(BaseModel):
    status: str 

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str
    campus: str = None 

class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    campus: Optional[str] = None



def verify_super_admin(profile: dict):
    """Verifica que el usuario tenga el rol 'admin'."""
    if profile.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de Super Admin")

def verify_admin_access(profile: dict, application_university_id: str = None):
    """
    Verifica si el usuario tiene permiso para gestionar una aplicación específica.
    """
    role = profile.get('role')
    campus = profile.get('campus')

    if role == 'admin':
        return True 
    
    if role == 'campus_admin':
        if not application_university_id:
             return False
        if campus == application_university_id:
            return True
            
    return False 


@router.patch("/applications/{application_id}/status")
async def update_application_status(
    application_id: int, 
    status_data: ApplicationStatusUpdate,
    profile: dict = Depends(get_current_user_profile)
):
    """
    Cambia el estado de una aplicación.
    Solo permitido para admins.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="BD no disponible")

    if status_data.status not in ['pending', 'accepted', 'rejected']:
        raise HTTPException(status_code=400, detail="Estado inválido. Use: pending, accepted, rejected")

    try:
        app_response = supabase_admin.table('applications').select('university_id').eq('id', application_id).single().execute()
        
        if not app_response.data:
            raise HTTPException(status_code=404, detail="Aplicación no encontrada")
            
        app_campus = app_response.data.get('university_id')

        if not verify_admin_access(profile, app_campus):
            raise HTTPException(status_code=403, detail="No tienes permiso para gestionar esta aplicación")

        response = supabase_admin.table('applications').update({
            "status": status_data.status
        }).eq('id', application_id).execute()

        return {"status": "success", "message": f"Aplicación {status_data.status}", "data": response.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/stats")
async def get_stats(profile: dict = Depends(get_current_user_profile)):
    """
    Devuelve conteos de aplicaciones.
    """
    if profile.get('role') not in ['admin', 'campus_admin']:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    try:
        query = supabase_admin.table('applications').select('status, university_id')
        
        if profile.get('role') == 'campus_admin':
            query = query.eq('university_id', profile.get('campus'))
            
        response = query.execute()
        data = response.data
        
        total = len(data)
        accepted = len([x for x in data if x['status'] == 'accepted'])
        rejected = len([x for x in data if x['status'] == 'rejected'])
        pending = len([x for x in data if x['status'] == 'pending'])
        
        by_campus = {}
        if profile.get('role') == 'admin':
            for item in data:
                camp = item.get('university_id', 'Desconocido')
                by_campus[camp] = by_campus.get(camp, 0) + 1

        return {
            "status": "success",
            "stats": {
                "total_applications": total,
                "accepted": accepted,
                "rejected": rejected,
                "pending": pending,
                "by_campus": by_campus
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/admin/users")
async def create_user_with_role(
    user_data: AdminUserCreate,
    profile: dict = Depends(get_current_user_profile)
):
    verify_super_admin(profile) 

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="BD no disponible")

    try:
        auth_response = supabase_admin.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True
        })
        new_user_id = auth_response.user.id

        profile_data = {
            "id": new_user_id,
            "role": user_data.role,
            "campus": user_data.campus if user_data.role == 'campus_admin' else None
        }
        supabase_admin.table('profiles').upsert(profile_data).execute()

        return {"status": "success", "message": f"Usuario creado: {user_data.email}", "user_id": new_user_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear usuario: {str(e)}")

@router.get("/admin/users")
async def list_users(profile: dict = Depends(get_current_user_profile)):
    verify_super_admin(profile)
    try:
        response = supabase_admin.table('profiles').select('*').execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, profile: dict = Depends(get_current_user_profile)):
    verify_super_admin(profile)
    try:
        supabase_admin.auth.admin.delete_user(user_id)
        supabase_admin.table('profiles').delete().eq('id', user_id).execute()
        return {"status": "success", "message": "Usuario eliminado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))