from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import supabase, supabase_admin
from security_jwt import (
    create_tokens,
    Token,
    get_current_user,
    get_current_active_user,
    TokenData,
    decode_token
)
import applications
import scholarships
import admin_routes
import scholarships_crud
import users
import permissions
import user_permissions

app = FastAPI(
    title="API de Becas CGSU",
    description="API backend para gestión de becas y autenticación.",
    openapi_tags=[
        {"name": "Health", "description": "Estado del servicio"},
        {"name": "Auth", "description": "Registro e inicio de sesión"},
        {"name": "Users", "description": "Operaciones de usuarios"},
        {"name": "Permissions", "description": "Gestión de permisos"},
        {"name": "Users Permissions", "description": "Gestión de permisos de usuarios"},
        {"name": "Scholarships", "description": "Gestión de becas"},
        {"name": "Applications", "description": "Gestión de aplicaciones a becas"},
        ],
    version="1.1.0"
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://becascgsuback.vercel.app", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(router= scholarships.router)
app.include_router(router= applications.router)
app.include_router(router= users.router)
app.include_router(router= permissions.router)
app.include_router(router= user_permissions.router)


class UserCredentials(BaseModel):
    """Modelo para recibir email y password"""
    email: str
    password: str


@app.get("/", tags=["Health"])
def read_root():
    return {
        "status": "online", 
        "message": "Bienvenido a la API de Becas CGSU. Visita /docs para ver la documentación y probar los endpoints."
    }

@app.post("/register", tags=["Auth"])
async def register_user(credentials: UserCredentials):
    """
    Registra un usuario nuevo en Supabase Auth.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Base de datos no disponible (Revisa variables de entorno)")

    try:
      
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })

        
        if response.user is None and response.session is None:
             raise HTTPException(status_code=400, detail="No se pudo registrar. Es posible que el usuario ya exista.")
        
        return {
            "status": "success", 
            "message": "Usuario registrado correctamente", 
            "user_id": response.user.id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en el registro: {str(e)}")


@app.post("/login", tags=["Auth"], response_model=Token)
async def login_user(credentials: UserCredentials):
    """
    Inicia sesión y devuelve tokens JWT (access_token y refresh_token).

    El access_token expira en 30 minutos.
    El refresh_token expira en 7 días.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response.session or not response.user:
            raise HTTPException(
                status_code=401,
                detail="Credenciales inválidas (Email o contraseña incorrectos)"
            )

        # Get user profile to include role information
        user_id = response.user.id
        try:
            profile = supabase_admin.table('users').select('role, nombre, codigo').eq('id', user_id).single().execute()
            role = profile.data.get('role', 'user') if profile.data else 'user'
        except:
            # Fallback to default role if profile not found
            role = 'user'

        # Create JWT tokens
        tokens = create_tokens(
            user_id=user_id,
            email=credentials.email,
            role=role
        )

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error al iniciar sesión: {str(e)}")


@app.get("/auth/me", tags=["Auth"])
async def get_current_user_info(current_user: TokenData = Depends(get_current_active_user)):
    """
    Obtiene la información del usuario autenticado actual.

    Requiere un token JWT válido en el header Authorization: Bearer <token>
    """
    try:
        # Get full user details from database
        user_data = supabase_admin.table('users').select('*').eq('id', current_user.user_id).single().execute()

        if not user_data.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Remove sensitive data
        user_info = user_data.data.copy()
        user_info.pop('password_hash', None)

        return {
            "status": "success",
            "user": user_info,
            "token_info": {
                "user_id": current_user.user_id,
                "email": current_user.email,
                "role": current_user.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener información del usuario: {str(e)}")


@app.post("/auth/refresh", tags=["Auth"], response_model=Token)
async def refresh_access_token(refresh_token: str):
    """
    Refresca el access token usando un refresh token válido.

    Args:
        refresh_token: El refresh token recibido al hacer login

    Returns:
        Token: Nuevos access_token y refresh_token
    """
    try:
        # Decode and validate refresh token
        token_data = decode_token(refresh_token)

        if not token_data.user_id:
            raise HTTPException(
                status_code=401,
                detail="Refresh token inválido"
            )

        # Get user info from database
        user_data = supabase_admin.table('users').select('email, role').eq('id', token_data.user_id).single().execute()

        if not user_data.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Create new tokens
        new_tokens = create_tokens(
            user_id=token_data.user_id,
            email=user_data.data['email'],
            role=user_data.data['role']
        )

        return new_tokens

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error al refrescar token: {str(e)}")