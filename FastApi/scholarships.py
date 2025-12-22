from fastapi import APIRouter, HTTPException
from database import supabase_admin 

router = APIRouter()

@router.get(path= "/scholarships")
async def get_scholarships():
    """
    Obtiene todas las becas de la tabla 'scholarships'.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")

    try:
        response = supabase_admin.table('scholarships').select("""
            *,
            university_centers (
                acronym
            ), 
            scholarship_types(
                name
            )                                                   
            """).execute()
        
        return {
            "status": "success",
            "data": response.data
        }

    except Exception as e:
        print(f"Error al obtener becas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al obtener becas: {str(e)}")