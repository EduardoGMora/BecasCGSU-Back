"""
Tests for Input Validation Functions
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validators import (
    validate_uuid,
    validate_not_empty,
    validate_max_length,
    validate_scholarship_title,
    validate_scholarship_description,
    validate_scholarship_dates,
    validate_scholarship_status,
    validate_scholarship_requirements,
    validate_password,
    validate_user_role,
    validate_campus_for_role,
    validate_full_name,
    validate_email,
    sanitize_string,
    ValidationError,
    MultipleValidationErrors,
    VALID_SCHOLARSHIP_STATUSES,
    VALID_USER_ROLES
)


# ===================== UUID VALIDATION TESTS =====================

def test_validate_uuid_valid():
    """Test valid UUID validation"""
    valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_uuid(valid_uuid, "test_id") == True


def test_validate_uuid_invalid():
    """Test invalid UUID validation"""
    with pytest.raises(ValidationError) as exc_info:
        validate_uuid("not-a-uuid", "test_id")
    assert exc_info.value.status_code == 422
    assert "UUID válido" in exc_info.value.detail["message"]


def test_validate_uuid_empty():
    """Test empty UUID validation"""
    with pytest.raises(ValidationError) as exc_info:
        validate_uuid("", "test_id")
    assert exc_info.value.status_code == 422


def test_validate_uuid_none():
    """Test None UUID validation"""
    with pytest.raises(ValidationError) as exc_info:
        validate_uuid(None, "test_id")
    assert exc_info.value.status_code == 422


# ===================== STRING VALIDATION TESTS =====================

def test_validate_not_empty_valid():
    """Test non-empty string validation"""
    assert validate_not_empty("Hello World", "field") == True


def test_validate_not_empty_whitespace():
    """Test whitespace-only string validation"""
    with pytest.raises(ValidationError) as exc_info:
        validate_not_empty("   ", "field")
    assert "vacío" in exc_info.value.detail["message"]


def test_validate_not_empty_min_length():
    """Test minimum length validation"""
    with pytest.raises(ValidationError) as exc_info:
        validate_not_empty("ab", "field", min_length=5)
    assert "al menos 5 caracteres" in exc_info.value.detail["message"]


def test_validate_max_length_valid():
    """Test valid max length"""
    assert validate_max_length("Hello", "field", 10) == True


def test_validate_max_length_exceeded():
    """Test exceeded max length"""
    with pytest.raises(ValidationError) as exc_info:
        validate_max_length("This is a very long string", "field", 10)
    assert "exceder" in exc_info.value.detail["message"]


def test_sanitize_string():
    """Test string sanitization"""
    assert sanitize_string("  Hello World  ") == "Hello World"
    assert sanitize_string("Hello\x00World") == "HelloWorld"
    assert sanitize_string(None) == None


# ===================== SCHOLARSHIP VALIDATION TESTS =====================

def test_validate_scholarship_title_valid():
    """Test valid scholarship title"""
    result = validate_scholarship_title("Beca de Excelencia Académica")
    assert result == "Beca de Excelencia Académica"


def test_validate_scholarship_title_too_short():
    """Test scholarship title too short"""
    with pytest.raises(ValidationError) as exc_info:
        validate_scholarship_title("AB")
    assert "al menos" in exc_info.value.detail["message"]


def test_validate_scholarship_title_too_long():
    """Test scholarship title too long"""
    with pytest.raises(ValidationError) as exc_info:
        validate_scholarship_title("A" * 250)
    assert "exceder" in exc_info.value.detail["message"]


def test_validate_scholarship_description_valid():
    """Test valid scholarship description"""
    description = "Esta beca está diseñada para estudiantes destacados que demuestren excelencia académica."
    result = validate_scholarship_description(description)
    assert len(result) > 10


def test_validate_scholarship_description_too_short():
    """Test scholarship description too short"""
    with pytest.raises(ValidationError) as exc_info:
        validate_scholarship_description("Corta")
    assert "al menos" in exc_info.value.detail["message"]


def test_validate_scholarship_dates_valid():
    """Test valid scholarship dates"""
    start = datetime.now()
    end = datetime.now() + timedelta(days=30)
    assert validate_scholarship_dates(start, end) == True


def test_validate_scholarship_dates_end_before_start():
    """Test end date before start date"""
    start = datetime.now() + timedelta(days=30)
    end = datetime.now()
    with pytest.raises(ValidationError) as exc_info:
        validate_scholarship_dates(start, end)
    assert "posterior" in exc_info.value.detail["message"]


def test_validate_scholarship_dates_same():
    """Test same start and end date"""
    now = datetime.now()
    with pytest.raises(ValidationError) as exc_info:
        validate_scholarship_dates(now, now)
    assert "posterior" in exc_info.value.detail["message"]


def test_validate_scholarship_status_valid():
    """Test valid scholarship statuses"""
    for status in VALID_SCHOLARSHIP_STATUSES:
        result = validate_scholarship_status(status)
        assert result == status


def test_validate_scholarship_status_invalid():
    """Test invalid scholarship status"""
    with pytest.raises(ValidationError) as exc_info:
        validate_scholarship_status("invalid_status")
    assert "Estado inválido" in exc_info.value.detail["message"]


def test_validate_scholarship_requirements_valid():
    """Test valid requirements list"""
    requirements = ["Promedio mínimo 8.5", "Ser estudiante regular", "No tener adeudos"]
    result = validate_scholarship_requirements(requirements)
    assert len(result) == 3


def test_validate_scholarship_requirements_empty():
    """Test empty requirements list"""
    result = validate_scholarship_requirements([])
    assert result == []


def test_validate_scholarship_requirements_none():
    """Test None requirements"""
    result = validate_scholarship_requirements(None)
    assert result == []


def test_validate_scholarship_requirements_filters_empty():
    """Test that empty strings are filtered out"""
    requirements = ["Requisito 1", "", "  ", "Requisito 2"]
    result = validate_scholarship_requirements(requirements)
    assert len(result) == 2


# ===================== PASSWORD VALIDATION TESTS =====================

def test_validate_password_valid():
    """Test valid password"""
    result = validate_password("SecurePass123")
    assert result == "SecurePass123"


def test_validate_password_too_short():
    """Test password too short"""
    with pytest.raises(ValidationError) as exc_info:
        validate_password("Short1")
    assert "al menos 8 caracteres" in exc_info.value.detail["message"]


def test_validate_password_no_uppercase():
    """Test password without uppercase"""
    with pytest.raises(ValidationError) as exc_info:
        validate_password("lowercase123")
    assert "mayúscula" in exc_info.value.detail["message"]


def test_validate_password_no_lowercase():
    """Test password without lowercase"""
    with pytest.raises(ValidationError) as exc_info:
        validate_password("UPPERCASE123")
    assert "minúscula" in exc_info.value.detail["message"]


def test_validate_password_no_number():
    """Test password without number"""
    with pytest.raises(ValidationError) as exc_info:
        validate_password("NoNumbersHere")
    assert "número" in exc_info.value.detail["message"]


def test_validate_password_empty():
    """Test empty password"""
    with pytest.raises(ValidationError) as exc_info:
        validate_password("")
    assert "requerida" in exc_info.value.detail["message"]


# ===================== USER ROLE VALIDATION TESTS =====================

def test_validate_user_role_valid():
    """Test valid user roles"""
    for role in VALID_USER_ROLES:
        result = validate_user_role(role)
        assert result == role


def test_validate_user_role_invalid():
    """Test invalid user role"""
    with pytest.raises(ValidationError) as exc_info:
        validate_user_role("superuser")
    assert "Rol inválido" in exc_info.value.detail["message"]


def test_validate_user_role_empty():
    """Test empty user role"""
    with pytest.raises(ValidationError) as exc_info:
        validate_user_role("")
    assert "requerido" in exc_info.value.detail["message"]


def test_validate_user_role_case_insensitive():
    """Test role validation is case insensitive"""
    result = validate_user_role("ADMIN")
    assert result == "admin"

    result = validate_user_role("Campus_Admin")
    assert result == "campus_admin"


# ===================== CAMPUS VALIDATION TESTS =====================

def test_validate_campus_for_role_campus_admin():
    """Test campus required for campus_admin"""
    valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
    result = validate_campus_for_role("campus_admin", valid_uuid)
    assert result == valid_uuid


def test_validate_campus_for_role_campus_admin_missing():
    """Test campus required but missing for campus_admin"""
    with pytest.raises(ValidationError) as exc_info:
        validate_campus_for_role("campus_admin", None)
    assert "campus es requerido" in exc_info.value.detail["message"]


def test_validate_campus_for_role_admin():
    """Test campus not required for admin"""
    result = validate_campus_for_role("admin", None)
    assert result == None


def test_validate_campus_for_role_user():
    """Test campus not required for user"""
    result = validate_campus_for_role("user", None)
    assert result == None


# ===================== FULL NAME VALIDATION TESTS =====================

def test_validate_full_name_valid():
    """Test valid full name"""
    result = validate_full_name("Juan Carlos García López")
    assert result == "Juan Carlos García López"


def test_validate_full_name_with_accents():
    """Test full name with accents"""
    result = validate_full_name("José María Ñoño")
    assert result == "José María Ñoño"


def test_validate_full_name_empty():
    """Test empty full name"""
    with pytest.raises(ValidationError) as exc_info:
        validate_full_name("")
    assert "requerido" in exc_info.value.detail["message"]


def test_validate_full_name_invalid_chars():
    """Test full name with invalid characters"""
    with pytest.raises(ValidationError) as exc_info:
        validate_full_name("User123")
    assert "letras" in exc_info.value.detail["message"]


# ===================== EMAIL VALIDATION TESTS =====================

def test_validate_email_valid():
    """Test valid email"""
    result = validate_email("user@example.com")
    assert result == "user@example.com"


def test_validate_email_uppercase():
    """Test email is lowercased"""
    result = validate_email("User@Example.COM")
    assert result == "user@example.com"


def test_validate_email_invalid_format():
    """Test invalid email format"""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("not-an-email")
    assert "formato" in exc_info.value.detail["message"]


def test_validate_email_empty():
    """Test empty email"""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("")
    assert "requerido" in exc_info.value.detail["message"]


# ===================== MULTIPLE ERRORS TEST =====================

def test_multiple_validation_errors():
    """Test multiple validation errors are collected"""
    errors = [
        {"field": "title", "message": "Título muy corto"},
        {"field": "description", "message": "Descripción muy corta"}
    ]

    with pytest.raises(MultipleValidationErrors) as exc_info:
        raise MultipleValidationErrors(errors)

    assert exc_info.value.status_code == 422
    assert len(exc_info.value.detail["errors"]) == 2
