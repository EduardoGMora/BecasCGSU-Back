from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin

router = APIRouter()


class PermissionCreate(BaseModel):
    nombre: str


class PermissionUpdate(BaseModel):
    nombre: Optional[str] = None


# GET - Get all permissions
@router.get(path="/permissions")
async def get_permissions():
    """
    Obtiene todos los permisos de la tabla 'permissions'.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('permissions').select('*').execute()
        return {
            "status": "success",
            "data": response.data
        }
    except Exception as e:
        print(f"Error al obtener permisos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener permisos: {str(e)}")


# GET - Get single permission by ID
@router.get(path="/permissions/{permission_id}")
async def get_permission(permission_id: str):
    """
    Obtiene un permiso específico por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('permissions').select('*').eq('id', permission_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Permiso no encontrado")
        return {
            "status": "success",
            "data": response.data[0]
        }
    except Exception as e:
        print(f"Error al obtener permiso: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener permiso: {str(e)}")


# POST - Create permission
@router.post(path="/permissions")
async def create_permission(permission: PermissionCreate):
    """
    Crea un nuevo permiso.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible (Falta Service Key)")

    try:
        response = supabase_admin.table('permissions').insert({
            "nombre": permission.nombre
        }).execute()

        return {
            "status": "success",
            "message": "Permiso creado correctamente",
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear permiso: {str(e)}")


# PUT - Update permission
@router.put(path="/permissions/{permission_id}")
async def update_permission(permission_id: str, permission: PermissionUpdate):
    """
    Actualiza un permiso existente por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    update_data = {k: v for k, v in permission.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    try:
        response = supabase_admin.table('permissions').update(update_data).eq('id', permission_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Permiso no encontrado")

        return {
            "status": "success",
            "message": "Permiso actualizado correctamente",
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")


# DELETE - Delete permission
@router.delete(path="/permissions/{permission_id}")
async def delete_permission(permission_id: str):
    """
    Elimina un permiso por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('permissions').delete().eq('id', permission_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Permiso no encontrado")

        return {
            "status": "success",
            "message": "Permiso eliminado correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")
