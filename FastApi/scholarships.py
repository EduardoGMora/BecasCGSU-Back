from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import supabase, supabase_admin 
import re

router = APIRouter()


def sanitize_search_term(search_term: str) -> str:
    """
    Sanitize search term to prevent SQL injection by escaping special characters.
    
    Args:
        search_term: The raw search string from user input
        
    Returns:
        Sanitized search term safe for use in ILIKE queries
    """
    if not search_term:
        return ""
    
    # Escape special characters that have meaning in ILIKE patterns
    # % = wildcard for any characters
    # _ = wildcard for single character
    # \ = escape character
    sanitized = search_term.replace('\\', '\\\\')  # Escape backslashes first
    sanitized = sanitized.replace('%', '\\%')      # Escape percent signs
    sanitized = sanitized.replace('_', '\\_')      # Escape underscores
    
    # Remove any null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Limit length to prevent DoS
    max_length = 100
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

@router.get(path= "/scholarships")
async def get_scholarships(
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'Abierta', 'Cerrada')"),
    university_center_id: Optional[str] = Query(None, description="Filter by university center ID"),
    scholarship_type_id: Optional[str] = Query(None, description="Filter by scholarship type ID"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results (1-1000)"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip for pagination")
) -> dict:
    """
    Get scholarships with optional server-side filters for better performance.
    
    Query parameters:
    - status: Filter by status (e.g., 'Abierta', 'Cerrada')
    - university_center_id: Filter by university center ID
    - scholarship_type_id: Filter by scholarship type ID
    - search: Search in title and description
    - limit: Maximum number of results (1-1000, default: 100)
    - offset: Number of results to skip for pagination (default: 0)

    Returns:
        A dictionary with the status, data, count of returned items, total items, limit, and offset.

    Raises:
        HTTPException: If there is an error fetching data from the database.
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")

    try:

        # Start building the query 
        query = supabase_admin.table("scholarships").select(
            """
            *,
            university_centers ( acronym ),
            scholarship_types ( name )
            """,
            count="exact"
        )

        # Apply server-side filters
        if status:
            query = query.eq("status", status)

        if university_center_id:
            query = query.eq("university_center_id", university_center_id)

        if scholarship_type_id:
            query = query.eq("scholarship_type_id", scholarship_type_id)

        # Search in title and description using OR condition with sanitized input
        if search:
            sanitized_search = sanitize_search_term(search)
            if sanitized_search:
                query = query.or_(
                    f"title.ilike.%{sanitized_search}%,description.ilike.%{sanitized_search}%"
                )

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
async def get_scholarship_types() -> dict:
    """
    Get all scholarship types for filter dropdown

    Returns a list of scholarship types with their IDs and names.

    Returns:
        A dictionary with the status and data containing scholarship types.

    Raises:
        HTTPException: If there is an error fetching data from the database.

    """

    if not supabase:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")

    try:
        response = supabase.table('scholarship_types').select('id, name').execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        print(f"Error al obtener tipos de beca: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(path="/university-centers")
async def get_university_centers() -> dict:
    """
    Get all university centers for filter dropdown

    Returns a list of university centers with their IDs and names.

    Returns:
        A dictionary with the status and data containing university centers.

    Raises:
        HTTPException: If there is an error fetching data from the database.
    """

    if not supabase:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")

    try:
        response = supabase.table('university_centers').select('id, name').execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        print(f"Error al obtener centros universitarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))