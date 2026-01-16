from fastapi import APIRouter, HTTPException, Depends, Body
from database import supabase_admin
from auth_utils import get_current_user_profile
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter()

# --- MODELOS DE DATOS ---



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



# --- RUTAS ---



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
        print(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al listar usuarios")

@router.delete(path= "/admin/users/{user_id}")
async def delete_user(user_id: str, profile: dict = Depends(get_current_user_profile)):
    verify_super_admin(profile)
    try:
        supabase_admin.auth.admin.delete_user(user_id)
        supabase_admin.table('profiles').delete().eq('id', user_id).execute()
        return {"status": "success", "message": "Usuario eliminado"}
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al eliminar usuario")

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
        print(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al actualizar usuario")