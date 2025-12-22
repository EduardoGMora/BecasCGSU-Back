from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin

router = APIRouter()


class UserPermissionCreate(BaseModel):
    user_id: str
    permission_id: str


class UserPermissionUpdate(BaseModel):
    user_id: Optional[str] = None
    permission_id: Optional[str] = None


# GET - Get all user permissions
@router.get(path="/user-permissions")
async def get_user_permissions():
    """
    Obtiene todos los permisos de usuarios de la tabla 'user_permissions'.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('user_permissions').select('*').execute()
        return {
            "status": "success",
            "data": response.data
        }
    except Exception as e:
        print(f"Error al obtener permisos de usuarios: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener permisos de usuarios: {str(e)}")


# GET - Get permissions for a specific user
@router.get(path="/user-permissions/user/{user_id}")
async def get_user_permissions_by_user(user_id: str):
    """
    Obtiene todos los permisos de un usuario específico.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('user_permissions').select('*').eq('user_id', user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No se encontraron permisos para este usuario")
        return {
            "status": "success",
            "data": response.data
        }
    except Exception as e:
        print(f"Error al obtener permisos del usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener permisos del usuario: {str(e)}")


# GET - Get single user permission by ID
@router.get(path="/user-permissions/{user_permission_id}")
async def get_user_permission(user_permission_id: str):
    """
    Obtiene un permiso de usuario específico por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('user_permissions').select('*').eq('id', user_permission_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Permiso de usuario no encontrado")
        return {
            "status": "success",
            "data": response.data[0]
        }
    except Exception as e:
        print(f"Error al obtener permiso de usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener permiso de usuario: {str(e)}")


# POST - Create user permission
@router.post(path="/user-permissions")
async def create_user_permission(user_permission: UserPermissionCreate):
    """
    Crea un nuevo permiso de usuario.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible (Falta Service Key)")

    try:
        response = supabase_admin.table('user_permissions').insert({
            "user_id": user_permission.user_id,
            "permission_id": user_permission.permission_id
        }).execute()

        return {
            "status": "success",
            "message": "Permiso de usuario creado correctamente",
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear permiso de usuario: {str(e)}")


# PUT - Update user permission
@router.put(path="/user-permissions/{user_permission_id}")
async def update_user_permission(user_permission_id: str, user_permission: UserPermissionUpdate):
    """
    Actualiza un permiso de usuario existente por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    update_data = {k: v for k, v in user_permission.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    try:
        response = supabase_admin.table('user_permissions').update(update_data).eq('id', user_permission_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Permiso de usuario no encontrado")

        return {
            "status": "success",
            "message": "Permiso de usuario actualizado correctamente",
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")


# DELETE - Delete user permission
@router.delete(path="/user-permissions/{user_permission_id}")
async def delete_user_permission(user_permission_id: str):
    """
    Elimina un permiso de usuario por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('user_permissions').delete().eq('id', user_permission_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Permiso de usuario no encontrado")

        return {
            "status": "success",
            "message": "Permiso de usuario eliminado correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")
