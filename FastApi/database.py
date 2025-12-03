import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = None
supabase_admin: Client = None

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("ERROR CRÍTICO: Faltan variables de entorno URL o ANON KEY.")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("✅ Cliente Público conectado.")
        
        # Initialize admin client with service key (for admin operations)
        if SUPABASE_SERVICE_KEY:
            supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            print(" Cliente Admin conectado (Service Key aceptada).")
        else:
            print("ADVERTENCIA: No se encontró SERVICE_KEY. Las funciones de escritura fallarán.")
            
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        supabase = None
        supabase_admin = None
