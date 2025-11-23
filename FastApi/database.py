import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


SUPABASE_URL = os.environ.get(key= "SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get(key= "SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get(key= "SUPABASE_SERVICE_KEY") 

supabase: Client = None
supabase_admin: Client = None   

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Faltan las variables de entorno en database.py")
    supabase = None
else:
    try:
        
        if SUPABASE_SERVICE_KEY:
            supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        else:
            print("Advertencia: No hay SERVICE_KEY, no se podrán hacer escrituras administrativas.")
            
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")