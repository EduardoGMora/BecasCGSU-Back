from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from security_jwt import get_current_user, require_admin, require_admin_or_campus_admin, TokenData

router = APIRouter(prefix="/users", tags=["Users"])

class LoginRequest(BaseModel):
    codigo: str
    password: str

class UserCreate(BaseModel):
    nombre: str
    email: str
    codigo: str
    password: str
    role: str


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    codigo: Optional[str] = None
    role: Optional[str] = None


# GET - Get all users (Protected - Admin only)
@router.get(path="/users")
async def get_users(current_user: TokenData = Depends(require_admin)):
    """
    Obtiene todos los usuarios de la tabla 'users'.

    Requiere autenticación y rol de administrador.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('users').select('*').execute()
        return {
            "status": "success",
            "data": response.data
        }
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")


# GET - Get single user by ID
@router.get(path="/users/{user_id}")
async def get_user(user_id: str):
    """
    Obtiene un usuario específico por su ID.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('users').select('*').eq('id', user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {
            "status": "success",
            "data": response.data[0]
        }
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")

# POST - Login user
@router.post(path="/users/loginUser")
def login(data: LoginRequest):
    response = supabase_admin.table("users") \
        .select("id, codigo, password_hash, role") \
        .eq("codigo", data.codigo) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    user = response.data[0]

    if user["password_hash"] != data.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "codigo": user["codigo"],
            "role": user["role"]
        }
    }

# POST - Create user (Protected - Admin only)
@router.post(path="/users")
async def create_user(user: UserCreate, current_user: TokenData = Depends(require_admin)):
    """
    Crea un nuevo usuario.

    Requiere autenticación y rol de administrador.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible (Falta Service Key)")

    try:
        response = supabase_admin.table('users').insert({
            "nombre": user.nombre,
            "email": user.email,
            "codigo": user.codigo,
            "password_hash": user.password,
            "role": user.role
        }).execute()

        return {
            "status": "success",
            "message": "Usuario creado correctamente",
            "data": response.data[0]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear usuario: {str(e)}")


# PUT - Update user (Protected - Admin only)
@router.put(path="/users/{user_id}")
async def update_user(user_id: str, user: UserUpdate, current_user: TokenData = Depends(require_admin)):
    """
    Actualiza un usuario existente por su ID.

    Requiere autenticación y rol de administrador.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    update_data = {k: v for k, v in user.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    try:
        response = supabase_admin.table('users').update(update_data).eq('id', user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "status": "success",
            "message": "Usuario actualizado correctamente",
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")


# DELETE - Delete user (Protected - Admin only)
@router.delete(path="/users/{user_id}")
async def delete_user(user_id: str, current_user: TokenData = Depends(require_admin)):
    """
    Elimina un usuario por su ID.

    Requiere autenticación y rol de administrador.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        response = supabase_admin.table('users').delete().eq('id', user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "status": "success",
            "message": "Usuario eliminado correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")
