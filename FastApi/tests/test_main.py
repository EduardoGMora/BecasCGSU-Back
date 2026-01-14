from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from security_jwt import create_access_token

client = TestClient(main.app)

# Helper function to create admin token for tests
def get_admin_token():
    """Create a valid admin token for testing protected endpoints"""
    return create_access_token({
        "sub": "admin-test-123",
        "email": "admin@test.com",
        "role": "admin"
    })

# Helper function to get auth headers
def get_admin_headers():
    """Get authorization headers with admin token"""
    token = get_admin_token()
    return {"Authorization": f"Bearer {token}"}


# ===================== HELPER CLASSES =====================

class FakeResponse:
    """Mock response object for Supabase operations"""
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class FakeUser:
    """Mock user object"""
    def __init__(self, user_id="test-user-id"):
        self.id = user_id


class FakeSession:
    """Mock session object"""
    def __init__(self, access_token="fake-token"):
        self.access_token = access_token


class FakeAuthResponse:
    """Mock auth response object"""
    def __init__(self, user=None, session=None):
        self.user = user
        self.session = session


# ===================== HEALTH ENDPOINT =====================

def test_health_check():
    """Test the root health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "message" in response.json()


# ===================== AUTH ENDPOINTS =====================

def test_register_success(monkeypatch):
    """Test successful user registration"""
    class FakeAuth:
        def sign_up(self, credentials):
            return FakeAuthResponse(
                user=FakeUser("new-user-123"),
                session=FakeSession()
            )

    monkeypatch.setattr(main, "supabase", type("Supabase", (), {"auth": FakeAuth()}))

    response = client.post("/register", json={
        "email": "test@example.com",
        "password": "securePassword123"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["user_id"] == "new-user-123"


def test_register_duplicate_user(monkeypatch):
    """Test registration with duplicate email"""
    class FakeAuth:
        def sign_up(self, credentials):
            return FakeAuthResponse(user=None, session=None)

    monkeypatch.setattr(main, "supabase", type("Supabase", (), {"auth": FakeAuth()}))

    response = client.post("/register", json={
        "email": "existing@example.com",
        "password": "password123"
    })

    assert response.status_code == 400


def test_register_missing_credentials():
    """Test registration with missing credentials"""
    response = client.post("/register", json={})
    assert response.status_code == 422  # Validation error


def test_login_success(monkeypatch):
    """Test successful login"""
    class FakeAuth:
        def sign_in_with_password(self, credentials):
            return FakeAuthResponse(
                user=FakeUser("user-123"),
                session=FakeSession("valid-token-abc")
            )

    monkeypatch.setattr(main, "supabase", type("Supabase", (), {"auth": FakeAuth()}))

    response = client.post("/login", json={
        "email": "user@example.com",
        "password": "correctPassword"
    })

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials(monkeypatch):
    """Test login with invalid credentials"""
    class FakeAuth:
        def sign_in_with_password(self, credentials):
            return FakeAuthResponse(user=None, session=None)

    monkeypatch.setattr(main, "supabase", type("Supabase", (), {"auth": FakeAuth()}))

    response = client.post("/login", json={
        "email": "user@example.com",
        "password": "wrongPassword"
    })

    assert response.status_code == 401


# ===================== USERS ENDPOINTS =====================

def test_get_all_users(monkeypatch):
    """Test getting all users"""
    mock_users = [
        {"id": "1", "nombre": "Juan Pérez", "email": "juan@example.com", "role": "user"},
        {"id": "2", "nombre": "María López", "email": "maria@example.com", "role": "admin"}
    ]

    class FakeTable:
        def select(self, *args):
            return self
        def execute(self):
            return FakeResponse(data=mock_users)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.get("/users/users", headers=get_admin_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 2


def test_get_user_by_id(monkeypatch):
    """Test getting a specific user by ID"""
    mock_user = {"id": "user-123", "nombre": "Test User", "email": "test@example.com"}

    class FakeTable:
        def select(self, *args):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[mock_user])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.get("/users/users/user-123")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == "user-123"


def test_get_user_not_found(monkeypatch):
    """Test getting a non-existent user"""
    class FakeTable:
        def select(self, *args):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.get("/users/users/nonexistent-id")
    # The endpoint catches HTTPException and returns 500 with the original error message
    assert response.status_code == 500
    assert "Usuario no encontrado" in response.json()["detail"]


def test_create_user(monkeypatch):
    """Test creating a new user"""
    new_user = {
        "id": "new-user-123",
        "nombre": "Nuevo Usuario",
        "email": "nuevo@example.com",
        "codigo": "2024001",
        "role": "user"
    }

    class FakeTable:
        def insert(self, data):
            return self
        def execute(self):
            return FakeResponse(data=[new_user])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.post("/users/users",
        headers=get_admin_headers(),
        json={
            "nombre": "Nuevo Usuario",
            "email": "nuevo@example.com",
            "codigo": "2024001",
            "password": "securePass123",
            "role": "user"
        })

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_update_user(monkeypatch):
    """Test updating an existing user"""
    updated_user = {"id": "user-123", "nombre": "Updated Name"}

    class FakeTable:
        def update(self, data):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[updated_user])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.put("/users/users/user-123",
        headers=get_admin_headers(),
        json={"nombre": "Updated Name"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_delete_user(monkeypatch):
    """Test deleting a user"""
    class FakeTable:
        def delete(self):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[{"id": "user-123"}])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.delete("/users/users/user-123", headers=get_admin_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_login_user_with_codigo(monkeypatch):
    """Test user login with codigo"""
    mock_user = {
        "id": "user-123",
        "codigo": "2024001",
        "password_hash": "hashedPassword",
        "role": "user"
    }

    class FakeTable:
        def select(self, *args):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[mock_user])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("users.supabase_admin", FakeSupabase())

    response = client.post("/users/users/loginUser", json={
        "codigo": "2024001",
        "password": "hashedPassword"
    })

    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["user"]["codigo"] == "2024001"


# ===================== SCHOLARSHIPS ENDPOINTS =====================

def test_get_scholarships(monkeypatch):
    """Test getting all scholarships"""
    mock_scholarships = [
        {
            "id": "sch-1",
            "title": "Beca de Excelencia",
            "description": "Beca para estudiantes destacados",
            "status": "Abierta",
            "university_centers": {"acronym": "CUCEI"},
            "scholarship_types": {"name": "Académica"}
        }
    ]

    class FakeTable:
        def select(self, query, count=None):
            return self
        def range(self, start, end):
            return self
        def execute(self):
            return FakeResponse(data=mock_scholarships, count=1)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("scholarships.supabase_admin", FakeSupabase())

    response = client.get("/scholarships/scholarships")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["count"] == 1


def test_get_scholarships_with_filters(monkeypatch):
    """Test getting scholarships with filters"""
    class FakeTable:
        def select(self, query, count=None):
            return self
        def eq(self, field, value):
            return self
        def range(self, start, end):
            return self
        def execute(self):
            return FakeResponse(data=[], count=0)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("scholarships.supabase_admin", FakeSupabase())

    response = client.get("/scholarships/scholarships?status=Abierta&limit=10&offset=0")
    assert response.status_code == 200


def test_get_scholarships_with_search(monkeypatch):
    """Test searching scholarships"""
    class FakeTable:
        def select(self, query, count=None):
            return self
        def or_(self, condition):
            return self
        def range(self, start, end):
            return self
        def execute(self):
            return FakeResponse(data=[], count=0)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("scholarships.supabase_admin", FakeSupabase())

    response = client.get("/scholarships/scholarships?search=excelencia")
    assert response.status_code == 200


def test_get_scholarship_types(monkeypatch):
    """Test getting scholarship types"""
    mock_types = [
        {"id": "1", "name": "Académica"},
        {"id": "2", "name": "Deportiva"}
    ]

    class FakeTable:
        def select(self, *args):
            return self
        def execute(self):
            return FakeResponse(data=mock_types)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("scholarships.supabase", FakeSupabase())

    response = client.get("/scholarships/scholarship-types")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 2


def test_get_university_centers(monkeypatch):
    """Test getting university centers"""
    mock_centers = [
        {"id": "1", "name": "CUCEI"},
        {"id": "2", "name": "CUCS"}
    ]

    class FakeTable:
        def select(self, *args):
            return self
        def execute(self):
            return FakeResponse(data=mock_centers)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("scholarships.supabase", FakeSupabase())

    response = client.get("/scholarships/university-centers")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


# ===================== APPLICATIONS ENDPOINTS =====================

def test_create_application(monkeypatch):
    """Test creating a new application"""
    new_application = {
        "id": "app-123",
        "student_id": "student-1",
        "scholarship_id": "sch-1",
        "status": "pending"
    }

    class FakeTable:
        def insert(self, data):
            return self
        def execute(self):
            return FakeResponse(data=[new_application])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("applications.supabase_admin", FakeSupabase())

    response = client.post("/applications/applications", json={
        "student_id": "student-1",
        "scholarship_id": "sch-1"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_update_application(monkeypatch):
    """Test updating an application"""
    updated_app = {"id": "app-123", "scholarship_id": "sch-2"}

    class FakeTable:
        def update(self, data):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[updated_app])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("applications.supabase_admin", FakeSupabase())

    response = client.put("/applications/applications/app-123", json={
        "scholarship_id": "sch-2"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_delete_application(monkeypatch):
    """Test deleting an application"""
    class FakeTable:
        def delete(self):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[{"id": "app-123"}])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("applications.supabase_admin", FakeSupabase())

    response = client.delete("/applications/applications/app-123")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


# ===================== PERMISSIONS ENDPOINTS =====================

def test_get_all_permissions(monkeypatch):
    """Test getting all permissions"""
    mock_permissions = [
        {"id": "1", "nombre": "read"},
        {"id": "2", "nombre": "write"}
    ]

    class FakeTable:
        def select(self, *args):
            return self
        def execute(self):
            return FakeResponse(data=mock_permissions)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("permissions.supabase_admin", FakeSupabase())

    response = client.get("/permissions/permissions")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_get_permission_by_id(monkeypatch):
    """Test getting a specific permission"""
    mock_permission = {"id": "perm-123", "nombre": "admin_access"}

    class FakeTable:
        def select(self, *args):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[mock_permission])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("permissions.supabase_admin", FakeSupabase())

    response = client.get("/permissions/permissions/perm-123")
    assert response.status_code == 200
    assert response.json()["data"]["nombre"] == "admin_access"


def test_create_permission(monkeypatch):
    """Test creating a new permission"""
    new_permission = {"id": "perm-new", "nombre": "new_permission"}

    class FakeTable:
        def insert(self, data):
            return self
        def execute(self):
            return FakeResponse(data=[new_permission])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("permissions.supabase_admin", FakeSupabase())

    response = client.post("/permissions/permissions",
        headers=get_admin_headers(),
        json={"nombre": "new_permission"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_update_permission(monkeypatch):
    """Test updating a permission"""
    updated_permission = {"id": "perm-123", "nombre": "updated_permission"}

    class FakeTable:
        def update(self, data):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[updated_permission])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("permissions.supabase_admin", FakeSupabase())

    response = client.put("/permissions/permissions/perm-123",
        headers=get_admin_headers(),
        json={"nombre": "updated_permission"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_delete_permission(monkeypatch):
    """Test deleting a permission"""
    class FakeTable:
        def delete(self):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[{"id": "perm-123"}])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("permissions.supabase_admin", FakeSupabase())

    response = client.delete("/permissions/permissions/perm-123", headers=get_admin_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "success"


# ===================== USER PERMISSIONS ENDPOINTS =====================

def test_get_all_user_permissions(monkeypatch):
    """Test getting all user permissions"""
    mock_user_permissions = [
        {"id": "1", "user_id": "user-1", "permission_id": "perm-1"},
        {"id": "2", "user_id": "user-2", "permission_id": "perm-2"}
    ]

    class FakeTable:
        def select(self, *args):
            return self
        def execute(self):
            return FakeResponse(data=mock_user_permissions)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("user_permissions.supabase_admin", FakeSupabase())

    response = client.get("/user-permissions/user-permissions")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_get_user_permissions_by_user_id(monkeypatch):
    """Test getting permissions for a specific user"""
    mock_permissions = [
        {"id": "1", "user_id": "user-123", "permission_id": "perm-1", "permissions": {"nombre": "read"}},
        {"id": "2", "user_id": "user-123", "permission_id": "perm-2", "permissions": {"nombre": "write"}}
    ]

    class FakeTable:
        def select(self, query):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=mock_permissions)

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("user_permissions.supabase_admin", FakeSupabase())

    response = client.get("/user-permissions/user-permissions/user/user-123")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_create_user_permission(monkeypatch):
    """Test creating a new user permission"""
    new_user_permission = {"id": "up-new", "user_id": "user-1", "permission_id": "perm-1"}

    class FakeTable:
        def insert(self, data):
            return self
        def execute(self):
            return FakeResponse(data=[new_user_permission])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("user_permissions.supabase_admin", FakeSupabase())

    response = client.post("/user-permissions/user-permissions", json={
        "user_id": "user-1",
        "permission_id": "perm-1"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_update_user_permission(monkeypatch):
    """Test updating a user permission"""
    updated_permission = {"id": "up-123", "permission_id": "perm-2"}

    class FakeTable:
        def update(self, data):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[updated_permission])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("user_permissions.supabase_admin", FakeSupabase())

    response = client.put("/user-permissions/user-permissions/up-123", json={
        "permission_id": "perm-2"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_delete_user_permission(monkeypatch):
    """Test deleting a user permission"""
    class FakeTable:
        def delete(self):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return FakeResponse(data=[{"id": "up-123"}])

    class FakeSupabase:
        def table(self, table_name):
            return FakeTable()

    monkeypatch.setattr("user_permissions.supabase_admin", FakeSupabase())

    response = client.delete("/user-permissions/user-permissions/up-123")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


# ===================== ERROR HANDLING TESTS =====================

def test_database_unavailable_error(monkeypatch):
    """Test handling when database is unavailable"""
    monkeypatch.setattr("users.supabase_admin", None)

    response = client.get("/users/users", headers=get_admin_headers())
    assert response.status_code == 503


def test_invalid_json_payload():
    """Test handling of invalid JSON payload"""
    response = client.post(
        "/users/users",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_missing_required_fields():
    """Test handling of missing required fields"""
    response = client.post("/users/users",
        headers=get_admin_headers(),
        json={
            "nombre": "Test User"
            # Missing required fields: email, codigo, password, role
        })
    assert response.status_code == 422
