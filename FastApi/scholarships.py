from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import supabase  

router = APIRouter()

@router.get(path= "/scholarships")
async def get_scholarships(
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'Abierta', 'Cerrada')"),
    university_center_id: Optional[str] = Query(None, description="Filter by university center ID"),
    scholarship_type_id: Optional[str] = Query(None, description="Filter by scholarship type ID"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results (1-1000)"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip for pagination")
):
    """
    Obtiene becas con filtros opcionales del lado del servidor para mejor rendimiento.
    
    Parámetros de consulta:
    - status: Filtrar por estado (ej. 'Abierta', 'Cerrada')
    - university_center_id: Filtrar por ID de centro universitario
    - scholarship_type_id: Filtrar por ID de tipo de beca
    - search: Buscar en título y descripción
    - limit: Número máximo de resultados (1-1000, default: 100)
    - offset: Número de resultados a omitir para paginación (default: 0)
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")

    try:
        # Start building the query
        query = supabase.table('scholarships').select('*', count='exact')
        
        # Apply server-side filters
        if status:
            query = query.eq('status', status)
        
        if university_center_id:
            query = query.eq('university_center_id', university_center_id)
        
        if scholarship_type_id:
            query = query.eq('scholarship_type_id', scholarship_type_id)
        
        # Search in title and description using OR condition
        if search:
            query = query.or_(f'title.ilike.%{search}%,description.ilike.%{search}%')
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        return {
            "status": "success",
            "data": response.data,
            "count": len(response.data),
            "total": response.count,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        print(f"Error al obtener becas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al obtener becas: {str(e)}")

@router.get(path="/scholarship-types")
async def get_scholarship_types():
    """Get all scholarship types for filter dropdown"""
    try:
        response = supabase.table('scholarship_types').select('id, name').execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(path="/university-centers")
async def get_university_centers():
    """Get all university centers for filter dropdown"""
    try:
        response = supabase.table('university_centers').select('id, name').execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))