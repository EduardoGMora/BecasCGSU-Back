from fastapi import HTTPException, Header
from database import supabase_admin

async def get_current_user_profile(authorization: str = Header(None)):
    """
    Recibe el Token del usuario (Bearer token), valida quién es
    y devuelve su PERFIL (incluyendo rol y campus).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta el token de autenticación")

    try:
        token = authorization.replace("Bearer ", "")

        user_response = supabase_admin.auth.get_user(token)
        user_id = user_response.user.id

        profile_response = supabase_admin.table('profiles').select('*').eq('id', user_id).single().execute()
        
        if not profile_response.data:
             raise HTTPException(status_code=404, detail="Perfil de usuario no encontrado")

        return profile_response.data

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido o expirado")