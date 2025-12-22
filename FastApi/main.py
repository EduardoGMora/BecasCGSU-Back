from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import supabase
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


@app.get(path= "/")
def read_root():
    return {
        "status": "online", 
        "message": "Bienvenido a la API de Becas CGSU. Visita /docs para ver la documentación y probar los endpoints."
    }

@app.post(path= "/register")
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


@app.post(path= "/login")
async def login_user(credentials: UserCredentials):
    """
    Inicia sesión y devuelve el token de acceso (session).
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
       
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response.session:
            raise HTTPException(status_code=401, detail="Credenciales inválidas (Email o contraseña incorrectos)")
            
        return response.session

    except Exception as e:
       
        raise HTTPException(status_code=401, detail=f"Error al iniciar sesión: {str(e)}")