from fastapi import APIRouter, HTTPException, Depends, Body
from database import supabase_admin
from auth_utils import get_current_user_profile
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter()

# --- MODELOS DE DATOS ---

class ApplicationStatusUpdate(BaseModel):
    status: str 

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str
    campus: str = None 
    full_name: str = "Administrador"
    student_code: str = "ADMIN" # Valor dummy

class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    campus: Optional[str] = None

# --- DEPENDENCIAS DE SEGURIDAD ---

def verify_super_admin(profile: dict):
    if profile.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de Super Admin")

def verify_admin_access(profile: dict, application_university_id: str = None):
    role = profile.get('role')
    campus = profile.get('campus')

    if role == 'admin': return True 
    if role == 'campus_admin':
        if not application_university_id: return False
        if campus == application_university_id: return True
    return False 

# --- RUTAS ---

# 1. GESTIÓN DE APLICACIONES (Corrección: application_id es str/UUID)
@router.patch(path= "/applications/{application_id}/status")
async def update_application_status(
    application_id: str,  # <--- ¡ESTO FUE LO QUE CORREGIMOS! (Antes decía int)
    status_data: ApplicationStatusUpdate,
    profile: dict = Depends(get_current_user_profile)
):
    if not supabase_admin: raise HTTPException(status_code=503, detail="BD no disponible")
    if status_data.status not in ['pending', 'accepted', 'rejected']:
        raise HTTPException(status_code=400, detail="Estado inválido")

    try:
        # Obtenemos la app y la beca relacionada para ver el campus
        # Nota: Ajusta la query según tu estructura real. 
        # Si university_id ya no existe en applications, lo sacamos de scholarships.
        app_res = supabase_admin.table('applications')\
            .select('*, scholarships(university_center_id)')\
            .eq('id', application_id)\
            .single().execute()
        
        if not app_res.data: raise HTTPException(status_code=404, detail="App no encontrada")
        
        # Lógica para obtener campus desde la beca relacionada
        scholarship_data = app_res.data.get('scholarships')
        app_campus = None
        if isinstance(scholarship_data, dict):
            app_campus = scholarship_data.get('university_center_id')
        elif isinstance(scholarship_data, list) and scholarship_data:
            app_campus = scholarship_data[0].get('university_center_id')

        if not verify_admin_access(profile, app_campus):
            raise HTTPException(status_code=403, detail="Sin permiso")

        response = supabase_admin.table('applications').update({"status": status_data.status}).eq('id', application_id).execute()
        return {"status": "success", "message": f"Estado actualizado a {status_data.status}", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 2. DASHBOARD
@router.get(path= "/stats")
async def get_stats(profile: dict = Depends(get_current_user_profile)):
    if profile.get('role') not in ['admin', 'campus_admin']:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        # Consulta simplificada. Si university_id no está en applications, 
        # el filtro por campus requeriría un join más complejo o filtrar en Python.
        # Por ahora traemos todo y contamos.
        query = supabase_admin.table('applications').select('status')
        
        response = query.execute()
        data = response.data
        
        total = len(data)
        accepted = len([x for x in data if x['status'] == 'accepted'])
        rejected = len([x for x in data if x['status'] == 'rejected'])
        pending = len([x for x in data if x['status'] == 'pending'])
        
        return {
            "status": "success",
            "stats": {"total": total, "accepted": accepted, "rejected": rejected, "pending": pending}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. CRUD USUARIOS
@router.post(path= "/admin/users")
async def create_user_with_role(
    user_data: AdminUserCreate,
    profile: dict = Depends(get_current_user_profile)
):
    verify_super_admin(profile) 
    if not supabase_admin: raise HTTPException(status_code=503, detail="BD no disponible")

    try:
        auth_response = supabase_admin.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True
        })
        new_user_id = auth_response.user.id

        profile_data = {
            "id": new_user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "student_code": user_data.student_code,
            "role": user_data.role,
            "campus": user_data.campus if user_data.role == 'campus_admin' else None
        }
        supabase_admin.table('profiles').upsert(profile_data).execute()

        return {"status": "success", "message": f"Usuario creado: {user_data.email}", "user_id": new_user_id}

    except Exception as e:
        print(f"User creation error: {str(e)}")  # Log internally
        raise HTTPException(status_code=400, detail="Error al crear usuario")
    
@router.get(path="/admin/users")
async def list_users(profile: dict = Depends(get_current_user_profile)):
    verify_super_admin(profile)
    try:
        response = supabase_admin.table('profiles').select('*').execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(path= "/admin/users/{user_id}")
async def delete_user(user_id: str, profile: dict = Depends(get_current_user_profile)):
    verify_super_admin(profile)
    try:
        supabase_admin.auth.admin.delete_user(user_id)
        supabase_admin.table('profiles').delete().eq('id', user_id).execute()
        return {"status": "success", "message": "Usuario eliminado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put(path= "/admin/users/{user_id}")
async def update_user_role(
    user_id: str,
    update_data: AdminUserUpdate,
    profile: dict = Depends(get_current_user_profile)
):
    verify_super_admin(profile)
    data_to_update = {k: v for k, v in update_data.dict().items() if v is not None}
    if not data_to_update: raise HTTPException(status_code=400, detail="Sin datos")

    try:
        response = supabase_admin.table('profiles').update(data_to_update).eq('id', user_id).execute()
        if not response.data: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"status": "success", "message": "Actualizado", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))