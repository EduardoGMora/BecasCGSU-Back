import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware  # ¡Importante!

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Variables de entorno SUPABASE_URL o SUPABASE_ANON_KEY no encontradas.")


try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("Conectado a Supabase (modo público)")
except Exception as e:
    print(f"Error al conectar con Supabase: {e}")
    supabase = None


origins = [
    "http://localhost",            
    "http://localhost:3000",        
    "http://localhost:5173",        
    
]


app = FastAPI(
    title="API de Becas CGSU",
    description="API intermediaria para manejar la autenticación y lógica de negocio.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              
    allow_credentials=True,             
    allow_methods=["*"],                
    allow_headers=["*"],                
)


class UserCredentials(BaseModel):
    """Modelo para recibir email y password"""
    email: str
    password: str


@app.get("/")
def read_root():
    """Endpoint raíz de bienvenida"""
    return {"status": "success", "message": "Bienvenido a la API de Becas CGSU"}

@app.post("/register")
async def register_user(credentials: UserCredentials):
    """
    Endpoint para registrar un nuevo usuario.
    Recibe email y password, y los pasa directamente a Supabase.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Servicio de Supabase no disponible")

    try:
      
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })

        
        if response.user is None and response.session is None:
             raise HTTPException(status_code=400, detail="No se pudo registrar al usuario. ¿Quizás ya existe?")

        return {"status": "success", "message": "Usuario registrado exitosamente", "user_id": response.user.id}

    except Exception as e:
        
        raise HTTPException(status_code=400, detail=f"Error al registrar: {str(e)}")


@app.post("/login")
async def login_user(credentials: UserCredentials):
    """
    Endpoint para iniciar sesión.
    Recibe email y password, los pasa a Supabase y devuelve la sesión completa.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Servicio de Supabase no disponible")

    try:
       
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response.session:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrecta")


        return response.session

    except Exception as e:
       
        raise HTTPException(status_code=401, detail=f"Error al iniciar sesión: {str(e)}")