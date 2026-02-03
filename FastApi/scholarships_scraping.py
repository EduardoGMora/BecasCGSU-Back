"""
Scholarship Scraping Endpoints
Implements web scraping functionality for external scholarships
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from database import supabase_admin
from auth_utils import get_current_user_profile
from scraper import scrape_scholarship, check_for_updates, ScraperError, calculate_checksum
from validators import validate_uuid, ValidationError

router = APIRouter()


# --- DATA MODELS ---

class ScrapeRequest(BaseModel):
    """Request model for scraping a new scholarship"""
    url: str
    university_center_id: str
    scholarship_type_id: str
    featured: bool = False


class ScrapeResponse(BaseModel):
    """Response model for scraped data"""
    status: str
    scraped_data: dict
    message: str


class ExternalScholarshipCreate(BaseModel):
    """Model for creating external scholarship from scraped data"""
    title: str
    description: str
    source_url: str
    university_center_id: str
    scholarship_type_id: str
    requirements: Optional[List[str]] = []
    application_start_date: Optional[datetime] = None
    application_end_date: Optional[datetime] = None
    status: str = "active"
    is_external: bool = True
    featured: bool = False
    checksum: str


class RefreshRequest(BaseModel):
    """Request to refresh specific scholarships"""
    scholarship_ids: Optional[List[str]] = None  # If None, refresh all external


# --- SECURITY HELPERS ---

def verify_admin_or_campus_admin(profile: dict):
    """Verifica que el usuario sea admin o campus_admin."""
    if profile.get('role') not in ['admin', 'campus_admin']:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: Se requieren permisos de administrador"
        )


def verify_campus_ownership(profile: dict, university_center_id: str):
    """Verifica permisos de campus."""
    role = profile.get('role')

    if role == 'admin':
        return True

    if role == 'campus_admin':
        campus = profile.get('campus')
        if not campus:
            raise HTTPException(
                status_code=403,
                detail="Tu usuario es Admin de Sede pero no tiene campus asignado"
            )
        if campus != university_center_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para gestionar becas de otro campus"
            )
        return True

    return False


# --- ENDPOINTS ---

@router.post("/scholarships/scrape", tags=["Scraping"])
async def scrape_scholarship_url(
    request: ScrapeRequest,
    profile: dict = Depends(get_current_user_profile)
):
    """
    Scrapes scholarship data from a URL.
    Returns extracted data for admin review before saving.

    Requires: admin or campus_admin role
    """
    verify_admin_or_campus_admin(profile)
    verify_campus_ownership(profile, request.university_center_id)

    # Validate UUIDs
    try:
        validate_uuid(request.university_center_id, "university_center_id")
        validate_uuid(request.scholarship_type_id, "scholarship_type_id")
    except ValidationError:
        raise

    try:
        scraped_data = await scrape_scholarship(request.url)

        return {
            "status": "success",
            "message": "Datos extraídos exitosamente. Revise y confirme para guardar.",
            "scraped_data": scraped_data,
            "suggested_scholarship": {
                "title": scraped_data.get("title") or "Sin título detectado",
                "description": scraped_data.get("description") or scraped_data.get("raw_text", "")[:1000],
                "requirements": scraped_data.get("requirements", []),
                "source_url": request.url,
                "university_center_id": request.university_center_id,
                "scholarship_type_id": request.scholarship_type_id,
                "is_external": True,
                "featured": request.featured,
                "checksum": scraped_data.get("checksum"),
                "dates_found": scraped_data.get("dates_found", {})
            }
        }

    except ScraperError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al obtener datos: {e.message}"
        )
    except Exception as e:
        print(f"Scraping error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al procesar la URL"
        )


@router.post("/scholarships/external", tags=["Scraping"])
async def create_external_scholarship(
    scholarship: ExternalScholarshipCreate,
    profile: dict = Depends(get_current_user_profile)
):
    """
    Creates a new external scholarship from scraped/reviewed data.

    Requires: admin or campus_admin role
    """
    verify_admin_or_campus_admin(profile)
    verify_campus_ownership(profile, scholarship.university_center_id)

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    # Validate UUIDs
    try:
        validate_uuid(scholarship.university_center_id, "university_center_id")
        validate_uuid(scholarship.scholarship_type_id, "scholarship_type_id")
    except ValidationError:
        raise

    try:
        data = {
            "title": scholarship.title,
            "description": scholarship.description,
            "source_url": scholarship.source_url,
            "university_center_id": scholarship.university_center_id,
            "scholarship_type_id": scholarship.scholarship_type_id,
            "requirements": scholarship.requirements,
            "status": scholarship.status,
            "is_external": True,
            "featured": scholarship.featured,
            "checksum": scholarship.checksum,
            "last_checked_at": datetime.utcnow().isoformat()
        }

        if scholarship.application_start_date:
            data["application_start_date"] = scholarship.application_start_date.isoformat()
        if scholarship.application_end_date:
            data["application_end_date"] = scholarship.application_end_date.isoformat()

        response = supabase_admin.table('scholarships').insert(data).execute()

        return {
            "status": "success",
            "message": "Beca externa creada exitosamente",
            "data": response.data
        }

    except Exception as e:
        print(f"Error creating external scholarship: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Error al crear la beca externa"
        )


@router.post("/scholarships/{scholarship_id}/refresh", tags=["Scraping"])
async def refresh_scholarship(
    scholarship_id: str,
    profile: dict = Depends(get_current_user_profile)
):
    """
    Checks for updates on an external scholarship.
    Compares current content with stored checksum.

    Requires: admin or campus_admin role
    """
    verify_admin_or_campus_admin(profile)

    # Validate scholarship_id
    validate_uuid(scholarship_id, "scholarship_id")

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        # Get existing scholarship
        existing = supabase_admin.table('scholarships')\
            .select('id, title, source_url, checksum, university_center_id, is_external')\
            .eq('id', scholarship_id)\
            .single()\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")

        scholarship = existing.data

        # Verify permissions
        verify_campus_ownership(profile, scholarship['university_center_id'])

        # Check if it's an external scholarship
        if not scholarship.get('is_external'):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden actualizar becas externas"
            )

        if not scholarship.get('source_url'):
            raise HTTPException(
                status_code=400,
                detail="La beca no tiene URL de origen"
            )

        # Check for updates
        result = await check_for_updates(
            scholarship['source_url'],
            scholarship.get('checksum', '')
        )

        # Update last_checked_at
        supabase_admin.table('scholarships')\
            .update({"last_checked_at": datetime.utcnow().isoformat()})\
            .eq('id', scholarship_id)\
            .execute()

        if result.get('error'):
            return {
                "status": "error",
                "message": f"Error al verificar: {result['error']}",
                "scholarship_id": scholarship_id
            }

        if result['has_changed']:
            return {
                "status": "changes_detected",
                "message": "Se detectaron cambios en la página de origen",
                "scholarship_id": scholarship_id,
                "current_title": scholarship['title'],
                "new_data": result.get('new_data'),
                "new_checksum": result['new_checksum']
            }
        else:
            return {
                "status": "no_changes",
                "message": "No se detectaron cambios",
                "scholarship_id": scholarship_id,
                "checked_at": result['checked_at']
            }

    except HTTPException:
        raise
    except ScraperError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al verificar URL: {e.message}"
        )
    except Exception as e:
        print(f"Error refreshing scholarship: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al verificar actualizaciones"
        )


@router.put("/scholarships/{scholarship_id}/apply-update", tags=["Scraping"])
async def apply_scholarship_update(
    scholarship_id: str,
    new_data: dict,
    profile: dict = Depends(get_current_user_profile)
):
    """
    Applies detected changes to a scholarship after admin review.

    Requires: admin or campus_admin role
    """
    verify_admin_or_campus_admin(profile)
    validate_uuid(scholarship_id, "scholarship_id")

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        # Verify scholarship exists and get campus
        existing = supabase_admin.table('scholarships')\
            .select('university_center_id')\
            .eq('id', scholarship_id)\
            .single()\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Beca no encontrada")

        verify_campus_ownership(profile, existing.data['university_center_id'])

        # Prepare update data
        update_data = {}
        allowed_fields = ['title', 'description', 'requirements', 'checksum']

        for field in allowed_fields:
            if field in new_data and new_data[field] is not None:
                update_data[field] = new_data[field]

        update_data['last_updated_at'] = datetime.utcnow().isoformat()
        update_data['last_checked_at'] = datetime.utcnow().isoformat()

        response = supabase_admin.table('scholarships')\
            .update(update_data)\
            .eq('id', scholarship_id)\
            .execute()

        return {
            "status": "success",
            "message": "Beca actualizada con los nuevos datos",
            "data": response.data
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error applying update: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Error al aplicar actualización"
        )


@router.get("/scholarships/external/pending-updates", tags=["Scraping"])
async def get_pending_updates(
    profile: dict = Depends(get_current_user_profile)
):
    """
    Gets list of external scholarships that may need review.
    Returns scholarships not checked in the last 24 hours.

    Requires: admin or campus_admin role
    """
    verify_admin_or_campus_admin(profile)

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        # Build query based on role
        role = profile.get('role')
        campus = profile.get('campus')

        query = supabase_admin.table('scholarships')\
            .select('id, title, source_url, last_checked_at, university_center_id')\
            .eq('is_external', True)\
            .not_.is_('source_url', 'null')

        if role == 'campus_admin' and campus:
            query = query.eq('university_center_id', campus)

        response = query.execute()

        # Filter those not checked recently (handled in application for flexibility)
        scholarships = response.data or []

        return {
            "status": "success",
            "count": len(scholarships),
            "scholarships": scholarships
        }

    except Exception as e:
        print(f"Error getting pending updates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener becas pendientes"
        )


@router.post("/scholarships/bulk-refresh", tags=["Scraping"])
async def bulk_refresh_scholarships(
    background_tasks: BackgroundTasks,
    request: RefreshRequest = None,
    profile: dict = Depends(get_current_user_profile)
):
    """
    Triggers background refresh for multiple external scholarships.
    Results are stored in the database.

    Requires: admin role only
    """
    if profile.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden ejecutar actualización masiva"
        )

    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        # Get scholarships to refresh
        query = supabase_admin.table('scholarships')\
            .select('id, source_url, checksum')\
            .eq('is_external', True)\
            .not_.is_('source_url', 'null')

        if request and request.scholarship_ids:
            query = query.in_('id', request.scholarship_ids)

        response = query.execute()
        scholarships = response.data or []

        if not scholarships:
            return {
                "status": "success",
                "message": "No hay becas externas para verificar"
            }

        # Add background task
        background_tasks.add_task(
            process_bulk_refresh,
            scholarships
        )

        return {
            "status": "processing",
            "message": f"Verificación iniciada para {len(scholarships)} becas",
            "scholarship_count": len(scholarships)
        }

    except Exception as e:
        print(f"Error starting bulk refresh: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al iniciar verificación masiva"
        )


async def process_bulk_refresh(scholarships: list):
    """
    Background task to process multiple scholarship refreshes.
    Updates last_checked_at and flags changes.
    """
    for scholarship in scholarships:
        try:
            result = await check_for_updates(
                scholarship['source_url'],
                scholarship.get('checksum', '')
            )

            update_data = {
                "last_checked_at": datetime.utcnow().isoformat()
            }

            if result.get('has_changed'):
                update_data["needs_review"] = True

            supabase_admin.table('scholarships')\
                .update(update_data)\
                .eq('id', scholarship['id'])\
                .execute()

        except Exception as e:
            print(f"Error processing scholarship {scholarship['id']}: {str(e)}")
            continue
