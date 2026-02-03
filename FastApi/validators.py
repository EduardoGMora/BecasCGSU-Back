"""
Input Validation Module for BecasCGSU API
Provides validation functions for scholarships and users
"""

import re
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException

# ===================== CONSTANTS =====================

# Valid status values for scholarships
VALID_SCHOLARSHIP_STATUSES = ["active", "inactive", "closed", "draft", "Abierta", "Cerrada"]

# Valid roles for users
VALID_USER_ROLES = ["admin", "campus_admin", "user"]

# Password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Text field limits
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 5000

# UUID regex pattern
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)


# ===================== VALIDATION ERRORS =====================

class ValidationError(HTTPException):
    """Custom validation error with field information"""
    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=422,
            detail={
                "error": "validation_error",
                "field": field,
                "message": message
            }
        )


class MultipleValidationErrors(HTTPException):
    """Multiple validation errors"""
    def __init__(self, errors: List[dict]):
        super().__init__(
            status_code=422,
            detail={
                "error": "validation_error",
                "errors": errors
            }
        )


# ===================== GENERIC VALIDATORS =====================

def validate_uuid(value: str, field_name: str = "id") -> bool:
    """
    Validate that a string is a valid UUID

    Args:
        value: String to validate
        field_name: Name of the field for error messages

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If invalid UUID
    """
    if not value:
        raise ValidationError(field_name, f"El campo {field_name} es requerido")

    if not UUID_PATTERN.match(value):
        raise ValidationError(field_name, f"El campo {field_name} debe ser un UUID válido")

    return True


def validate_not_empty(value: str, field_name: str, min_length: int = 1) -> bool:
    """
    Validate that a string is not empty or whitespace only

    Args:
        value: String to validate
        field_name: Name of the field
        min_length: Minimum length required

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If empty or too short
    """
    if not value or not value.strip():
        raise ValidationError(field_name, f"El campo {field_name} no puede estar vacío")

    if len(value.strip()) < min_length:
        raise ValidationError(
            field_name,
            f"El campo {field_name} debe tener al menos {min_length} caracteres"
        )

    return True


def validate_max_length(value: str, field_name: str, max_length: int) -> bool:
    """
    Validate that a string does not exceed maximum length

    Args:
        value: String to validate
        field_name: Name of the field
        max_length: Maximum length allowed

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If too long
    """
    if value and len(value) > max_length:
        raise ValidationError(
            field_name,
            f"El campo {field_name} no puede exceder {max_length} caracteres"
        )

    return True


def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing potentially dangerous characters

    Args:
        value: String to sanitize

    Returns:
        str: Sanitized string
    """
    if not value:
        return value

    # Remove null bytes
    value = value.replace('\x00', '')

    # Strip leading/trailing whitespace
    value = value.strip()

    return value


# ===================== SCHOLARSHIP VALIDATORS =====================

def validate_scholarship_title(title: str) -> str:
    """
    Validate scholarship title

    Args:
        title: Title to validate

    Returns:
        str: Sanitized title

    Raises:
        ValidationError: If validation fails
    """
    title = sanitize_string(title)

    validate_not_empty(title, "title", MIN_TITLE_LENGTH)
    validate_max_length(title, "title", MAX_TITLE_LENGTH)

    return title


def validate_scholarship_description(description: str) -> str:
    """
    Validate scholarship description

    Args:
        description: Description to validate

    Returns:
        str: Sanitized description

    Raises:
        ValidationError: If validation fails
    """
    description = sanitize_string(description)

    validate_not_empty(description, "description", MIN_DESCRIPTION_LENGTH)
    validate_max_length(description, "description", MAX_DESCRIPTION_LENGTH)

    return description


def validate_scholarship_dates(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate scholarship application dates

    Args:
        start_date: Application start date
        end_date: Application end date

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If dates are invalid
    """
    if not start_date:
        raise ValidationError("application_start_date", "La fecha de inicio es requerida")

    if not end_date:
        raise ValidationError("application_end_date", "La fecha de fin es requerida")

    if end_date <= start_date:
        raise ValidationError(
            "application_end_date",
            "La fecha de fin debe ser posterior a la fecha de inicio"
        )

    # Optional: Check that start date is not in the past (for new scholarships)
    # Uncomment if needed:
    # if start_date < datetime.now():
    #     raise ValidationError(
    #         "application_start_date",
    #         "La fecha de inicio no puede ser en el pasado"
    #     )

    return True


def validate_scholarship_status(status: str) -> str:
    """
    Validate scholarship status

    Args:
        status: Status to validate

    Returns:
        str: Validated status

    Raises:
        ValidationError: If status is invalid
    """
    if not status:
        raise ValidationError("status", "El estado es requerido")

    status = status.strip()

    if status not in VALID_SCHOLARSHIP_STATUSES:
        raise ValidationError(
            "status",
            f"Estado inválido. Valores permitidos: {', '.join(VALID_SCHOLARSHIP_STATUSES)}"
        )

    return status


def validate_scholarship_requirements(requirements: Optional[List[str]]) -> List[str]:
    """
    Validate scholarship requirements list

    Args:
        requirements: List of requirements

    Returns:
        List[str]: Validated and sanitized requirements

    Raises:
        ValidationError: If validation fails
    """
    if requirements is None:
        return []

    if not isinstance(requirements, list):
        raise ValidationError("requirements", "Los requisitos deben ser una lista")

    # Sanitize and filter empty requirements
    validated = []
    for i, req in enumerate(requirements):
        if not isinstance(req, str):
            raise ValidationError(
                "requirements",
                f"El requisito en posición {i} debe ser texto"
            )

        req = sanitize_string(req)
        if req:  # Only add non-empty requirements
            validate_max_length(req, f"requirements[{i}]", 500)
            validated.append(req)

    return validated


def validate_scholarship_create(data: dict) -> dict:
    """
    Validate all fields for creating a scholarship

    Args:
        data: Scholarship data dictionary

    Returns:
        dict: Validated and sanitized data

    Raises:
        ValidationError: If any validation fails
    """
    errors = []

    # Validate required text fields
    try:
        data['title'] = validate_scholarship_title(data.get('title', ''))
    except ValidationError as e:
        errors.append(e.detail)

    try:
        data['description'] = validate_scholarship_description(data.get('description', ''))
    except ValidationError as e:
        errors.append(e.detail)

    # Validate UUIDs
    try:
        validate_uuid(data.get('university_center_id', ''), 'university_center_id')
    except ValidationError as e:
        errors.append(e.detail)

    try:
        validate_uuid(data.get('scholarship_type_id', ''), 'scholarship_type_id')
    except ValidationError as e:
        errors.append(e.detail)

    # Validate dates
    try:
        validate_scholarship_dates(
            data.get('application_start_date'),
            data.get('application_end_date')
        )
    except ValidationError as e:
        errors.append(e.detail)

    # Validate status
    try:
        data['status'] = validate_scholarship_status(data.get('status', 'active'))
    except ValidationError as e:
        errors.append(e.detail)

    # Validate requirements
    try:
        data['requirements'] = validate_scholarship_requirements(data.get('requirements'))
    except ValidationError as e:
        errors.append(e.detail)

    if errors:
        raise MultipleValidationErrors(errors)

    return data


# ===================== USER VALIDATORS =====================

def validate_password(password: str) -> str:
    """
    Validate password strength

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number

    Args:
        password: Password to validate

    Returns:
        str: Validated password

    Raises:
        ValidationError: If password is weak
    """
    if not password:
        raise ValidationError("password", "La contraseña es requerida")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            "password",
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError(
            "password",
            f"La contraseña no puede exceder {MAX_PASSWORD_LENGTH} caracteres"
        )

    if not re.search(r'[A-Z]', password):
        raise ValidationError(
            "password",
            "La contraseña debe contener al menos una letra mayúscula"
        )

    if not re.search(r'[a-z]', password):
        raise ValidationError(
            "password",
            "La contraseña debe contener al menos una letra minúscula"
        )

    if not re.search(r'\d', password):
        raise ValidationError(
            "password",
            "La contraseña debe contener al menos un número"
        )

    return password


def validate_user_role(role: str) -> str:
    """
    Validate user role

    Args:
        role: Role to validate

    Returns:
        str: Validated role

    Raises:
        ValidationError: If role is invalid
    """
    if not role:
        raise ValidationError("role", "El rol es requerido")

    role = role.strip().lower()

    if role not in VALID_USER_ROLES:
        raise ValidationError(
            "role",
            f"Rol inválido. Valores permitidos: {', '.join(VALID_USER_ROLES)}"
        )

    return role


def validate_campus_for_role(role: str, campus: Optional[str]) -> Optional[str]:
    """
    Validate that campus is provided when role is campus_admin

    Args:
        role: User role
        campus: Campus ID (UUID)

    Returns:
        Optional[str]: Validated campus or None

    Raises:
        ValidationError: If campus is required but missing
    """
    if role == 'campus_admin':
        if not campus:
            raise ValidationError(
                "campus",
                "El campus es requerido para el rol campus_admin"
            )
        validate_uuid(campus, "campus")
        return campus

    return None


def validate_full_name(name: str) -> str:
    """
    Validate user full name

    Args:
        name: Name to validate

    Returns:
        str: Sanitized name

    Raises:
        ValidationError: If validation fails
    """
    name = sanitize_string(name)

    if not name:
        raise ValidationError("full_name", "El nombre completo es requerido")

    validate_max_length(name, "full_name", 200)

    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-'\.]+$", name):
        raise ValidationError(
            "full_name",
            "El nombre solo puede contener letras, espacios y guiones"
        )

    return name


def validate_user_create(data: dict) -> dict:
    """
    Validate all fields for creating a user

    Args:
        data: User data dictionary

    Returns:
        dict: Validated data

    Raises:
        MultipleValidationErrors: If any validation fails
    """
    errors = []

    # Validate password
    try:
        data['password'] = validate_password(data.get('password', ''))
    except ValidationError as e:
        errors.append(e.detail)

    # Validate role
    try:
        data['role'] = validate_user_role(data.get('role', ''))
    except ValidationError as e:
        errors.append(e.detail)

    # Validate campus (only if we already validated role successfully)
    if 'role' in data and not any(e.get('field') == 'role' for e in errors):
        try:
            data['campus'] = validate_campus_for_role(
                data['role'],
                data.get('campus')
            )
        except ValidationError as e:
            errors.append(e.detail)

    # Validate full name
    try:
        data['full_name'] = validate_full_name(data.get('full_name', 'Administrador'))
    except ValidationError as e:
        errors.append(e.detail)

    if errors:
        raise MultipleValidationErrors(errors)

    return data


# ===================== EMAIL VALIDATORS =====================

def validate_email(email: str) -> str:
    """
    Validate email format

    Args:
        email: Email to validate

    Returns:
        str: Validated email (lowercase)

    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("email", "El email es requerido")

    email = email.strip().lower()

    # Basic email pattern
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    if not email_pattern.match(email):
        raise ValidationError("email", "El formato del email es inválido")

    validate_max_length(email, "email", 254)

    return email


# ===================== HELPER FUNCTIONS =====================

def collect_validation_errors(*validators) -> List[dict]:
    """
    Run multiple validators and collect all errors

    Args:
        *validators: List of (validator_func, args) tuples

    Returns:
        List[dict]: List of error details
    """
    errors = []

    for validator_func, args in validators:
        try:
            validator_func(*args)
        except ValidationError as e:
            errors.append(e.detail)

    return errors
