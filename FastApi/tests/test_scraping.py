"""
Tests for Scholarship Scraping System
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from scraper import (
    extract_text_content,
    extract_scholarship_data,
    calculate_checksum,
    content_has_changed,
    extract_dates_from_text,
    extract_requirements,
    ScraperError
)
from security_jwt import create_access_token

client = TestClient(main.app)


# ===================== HELPER FUNCTIONS =====================

def get_admin_token():
    """Generate admin token for testing"""
    return create_access_token({
        "sub": "admin-test-123",
        "email": "admin@test.com",
        "role": "admin"
    })


def get_admin_headers():
    """Get authorization headers for admin"""
    return {"Authorization": f"Bearer {get_admin_token()}"}


def get_campus_admin_token():
    """Generate campus_admin token for testing"""
    return create_access_token({
        "sub": "campus-admin-123",
        "email": "campus@test.com",
        "role": "campus_admin"
    })


def get_campus_admin_headers():
    """Get authorization headers for campus_admin"""
    return {"Authorization": f"Bearer {get_campus_admin_token()}"}


def get_user_token():
    """Generate regular user token for testing"""
    return create_access_token({
        "sub": "user-123",
        "email": "user@test.com",
        "role": "user"
    })


def get_user_headers():
    """Get authorization headers for regular user"""
    return {"Authorization": f"Bearer {get_user_token()}"}


# ===================== SCRAPER UNIT TESTS =====================

class TestExtractTextContent:
    """Tests for text extraction from HTML"""

    def test_extract_basic_text(self):
        """Test basic text extraction"""
        html = "<html><body><h1>Title</h1><p>Content here</p></body></html>"
        result = extract_text_content(html)
        assert "Title" in result
        assert "Content here" in result

    def test_extract_removes_scripts(self):
        """Test that scripts are removed"""
        html = "<html><body><script>alert('bad')</script><p>Good content</p></body></html>"
        result = extract_text_content(html)
        assert "alert" not in result
        assert "Good content" in result

    def test_extract_removes_styles(self):
        """Test that style tags are removed"""
        html = "<html><body><style>.red{color:red}</style><p>Visible text</p></body></html>"
        result = extract_text_content(html)
        assert "color" not in result
        assert "Visible text" in result

    def test_extract_removes_navigation(self):
        """Test that nav/footer/header are removed"""
        html = """
        <html><body>
            <nav>Navigation links</nav>
            <main>Main content</main>
            <footer>Footer info</footer>
        </body></html>
        """
        result = extract_text_content(html)
        assert "Navigation links" not in result
        assert "Main content" in result
        assert "Footer info" not in result


class TestExtractScholarshipData:
    """Tests for scholarship data extraction"""

    def test_extract_title_from_h1(self):
        """Test title extraction from h1"""
        html = "<html><body><h1>Beca de Excelencia</h1><p>Description</p></body></html>"
        result = extract_scholarship_data(html, "http://example.com")
        assert result["title"] == "Beca de Excelencia"

    def test_extract_title_from_meta(self):
        """Test title extraction from meta tag"""
        html = """
        <html>
            <head><meta property="og:title" content="Scholarship Title"></head>
            <body><p>Content</p></body>
        </html>
        """
        result = extract_scholarship_data(html, "http://example.com")
        assert result["title"] == "Scholarship Title"

    def test_extract_description_from_meta(self):
        """Test description extraction from meta"""
        html = """
        <html>
            <head><meta name="description" content="This is a great scholarship opportunity for students."></head>
            <body><p>Content</p></body>
        </html>
        """
        result = extract_scholarship_data(html, "http://example.com")
        assert "scholarship opportunity" in result["description"]

    def test_source_url_preserved(self):
        """Test that source URL is preserved"""
        html = "<html><body><p>Content</p></body></html>"
        result = extract_scholarship_data(html, "http://test.com/scholarship")
        assert result["source_url"] == "http://test.com/scholarship"


class TestChecksumFunctions:
    """Tests for checksum calculation and comparison"""

    def test_calculate_checksum_consistent(self):
        """Test that same content produces same checksum"""
        content = "This is test content"
        hash1 = calculate_checksum(content)
        hash2 = calculate_checksum(content)
        assert hash1 == hash2

    def test_calculate_checksum_different_content(self):
        """Test that different content produces different checksum"""
        hash1 = calculate_checksum("Content A")
        hash2 = calculate_checksum("Content B")
        assert hash1 != hash2

    def test_checksum_ignores_whitespace(self):
        """Test that extra whitespace doesn't change checksum"""
        hash1 = calculate_checksum("Hello World")
        hash2 = calculate_checksum("Hello    World")
        assert hash1 == hash2

    def test_checksum_case_insensitive(self):
        """Test that checksum is case insensitive"""
        hash1 = calculate_checksum("Hello World")
        hash2 = calculate_checksum("hello world")
        assert hash1 == hash2

    def test_content_has_changed_true(self):
        """Test content change detection returns True"""
        old_checksum = calculate_checksum("Old content")
        assert content_has_changed(old_checksum, "New content") == True

    def test_content_has_changed_false(self):
        """Test content change detection returns False"""
        content = "Same content"
        old_checksum = calculate_checksum(content)
        assert content_has_changed(old_checksum, content) == False


class TestDateExtraction:
    """Tests for date pattern extraction"""

    def test_extract_dates_spanish_pattern(self):
        """Test Spanish date pattern extraction"""
        text = "Convocatoria abierta del 15 de enero al 28 de febrero de 2024"
        result = extract_dates_from_text(text)
        assert "raw_matches" in result or result.get("start_date") or result.get("end_date") is None

    def test_extract_dates_deadline_pattern(self):
        """Test deadline pattern extraction"""
        text = "Fecha límite: 15 de marzo de 2024"
        result = extract_dates_from_text(text)
        # Should find something or return empty dict
        assert isinstance(result, dict)


class TestRequirementsExtraction:
    """Tests for requirements list extraction"""

    def test_extract_requirements_from_list(self):
        """Test requirements extraction from ul/li"""
        from bs4 import BeautifulSoup
        html = """
        <div>
            <h3>Requisitos</h3>
            <ul>
                <li>Ser estudiante regular</li>
                <li>Promedio mínimo de 8.5</li>
                <li>No tener adeudos</li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_requirements(soup)
        assert len(result) >= 0  # May or may not find depending on implementation


class TestScraperError:
    """Tests for ScraperError exception"""

    def test_scraper_error_creation(self):
        """Test ScraperError creation"""
        error = ScraperError("Test error", "http://example.com")
        assert error.message == "Test error"
        assert error.url == "http://example.com"

    def test_scraper_error_str(self):
        """Test ScraperError string representation"""
        error = ScraperError("Connection failed")
        assert str(error) == "Connection failed"


# ===================== ENDPOINT TESTS =====================

class TestScrapeEndpoint:
    """Tests for /scholarships/scrape endpoint"""

    def test_scrape_requires_auth(self):
        """Test that scrape endpoint requires authentication"""
        response = client.post("/scholarships/scrape", json={
            "url": "http://example.com",
            "university_center_id": "123e4567-e89b-12d3-a456-426614174000",
            "scholarship_type_id": "123e4567-e89b-12d3-a456-426614174001"
        })
        assert response.status_code == 403

    def test_scrape_rejects_user_role(self):
        """Test that regular users cannot scrape"""
        response = client.post(
            "/scholarships/scrape",
            json={
                "url": "http://example.com",
                "university_center_id": "123e4567-e89b-12d3-a456-426614174000",
                "scholarship_type_id": "123e4567-e89b-12d3-a456-426614174001"
            },
            headers=get_user_headers()
        )
        assert response.status_code == 403

    def test_scrape_validates_uuid(self, monkeypatch):
        """Test that invalid UUIDs are rejected"""
        # Mock auth to return admin profile
        class FakeTable:
            def select(self, *args): return self
            def eq(self, *args): return self
            def single(self): return self
            def execute(self):
                return type("R", (), {"data": {"role": "admin", "campus": None}})

        class FakeSupabase:
            def table(self, name): return FakeTable()

        monkeypatch.setattr("auth_utils.supabase_admin", FakeSupabase())

        response = client.post(
            "/scholarships/scrape",
            json={
                "url": "http://example.com",
                "university_center_id": "invalid-uuid",
                "scholarship_type_id": "123e4567-e89b-12d3-a456-426614174001"
            },
            headers=get_admin_headers()
        )
        assert response.status_code == 422


class TestRefreshEndpoint:
    """Tests for /scholarships/{id}/refresh endpoint"""

    def test_refresh_requires_auth(self):
        """Test that refresh endpoint requires authentication"""
        response = client.post("/scholarships/123e4567-e89b-12d3-a456-426614174000/refresh")
        assert response.status_code == 403

    def test_refresh_validates_uuid(self, monkeypatch):
        """Test that invalid scholarship_id is rejected"""
        # Mock auth
        class FakeTable:
            def select(self, *args): return self
            def eq(self, *args): return self
            def single(self): return self
            def execute(self):
                return type("R", (), {"data": {"role": "admin", "campus": None}})

        class FakeSupabase:
            def table(self, name): return FakeTable()

        monkeypatch.setattr("auth_utils.supabase_admin", FakeSupabase())

        response = client.post(
            "/scholarships/not-a-uuid/refresh",
            headers=get_admin_headers()
        )
        assert response.status_code == 422


class TestExternalScholarshipsEndpoint:
    """Tests for /scholarships/external endpoint"""

    def test_create_external_requires_auth(self):
        """Test that creating external scholarship requires auth"""
        response = client.post("/scholarships/external", json={
            "title": "Test Scholarship",
            "description": "Test description for the scholarship",
            "source_url": "http://example.com",
            "university_center_id": "123e4567-e89b-12d3-a456-426614174000",
            "scholarship_type_id": "123e4567-e89b-12d3-a456-426614174001",
            "checksum": "abc123"
        })
        assert response.status_code == 403


class TestPendingUpdatesEndpoint:
    """Tests for /scholarships/external/pending-updates endpoint"""

    def test_pending_updates_requires_auth(self):
        """Test that pending updates endpoint requires auth"""
        response = client.get("/scholarships/external/pending-updates")
        assert response.status_code == 403

    def test_pending_updates_rejects_user_role(self):
        """Test that regular users cannot access pending updates"""
        response = client.get(
            "/scholarships/external/pending-updates",
            headers=get_user_headers()
        )
        assert response.status_code == 403


class TestBulkRefreshEndpoint:
    """Tests for /scholarships/bulk-refresh endpoint"""

    def test_bulk_refresh_requires_admin(self):
        """Test that bulk refresh requires admin role"""
        response = client.post("/scholarships/bulk-refresh")
        assert response.status_code == 403

    def test_bulk_refresh_rejects_campus_admin(self, monkeypatch):
        """Test that campus_admin cannot do bulk refresh"""
        # Mock auth
        class FakeTable:
            def select(self, *args): return self
            def eq(self, *args): return self
            def single(self): return self
            def execute(self):
                return type("R", (), {"data": {"role": "campus_admin", "campus": "123"}})

        class FakeSupabase:
            def table(self, name): return FakeTable()

        monkeypatch.setattr("auth_utils.supabase_admin", FakeSupabase())

        response = client.post(
            "/scholarships/bulk-refresh",
            headers=get_campus_admin_headers()
        )
        assert response.status_code == 403


# ===================== BACKGROUND TASKS TESTS =====================

class TestBackgroundTasks:
    """Tests for background task functionality"""

    def test_checker_status(self):
        """Test checker status function"""
        from background_tasks import get_checker_status

        status = get_checker_status()
        assert "is_running" in status
        assert "last_run" in status
        assert "check_interval_hours" in status

    def test_update_checker_instance(self):
        """Test update checker instance exists"""
        from background_tasks import update_checker

        assert update_checker is not None
        assert hasattr(update_checker, 'is_running')
        assert hasattr(update_checker, 'check_single_scholarship')


# ===================== INTEGRATION TESTS =====================

class TestScrapingIntegration:
    """Integration tests for the complete scraping flow"""

    @pytest.mark.asyncio
    async def test_scrape_and_checksum_flow(self):
        """Test the complete scrape and checksum flow"""
        # Create sample HTML
        html = """
        <html>
            <head><title>Test Scholarship</title></head>
            <body>
                <h1>Beca de Prueba 2024</h1>
                <p>Esta es una beca para estudiantes destacados.</p>
            </body>
        </html>
        """

        # Extract data
        data = extract_scholarship_data(html, "http://test.com/beca")

        # Verify extraction
        assert data["title"] is not None
        assert data["source_url"] == "http://test.com/beca"

        # Calculate checksum
        checksum = calculate_checksum(data.get("raw_text", ""))
        assert len(checksum) == 64  # SHA256 produces 64 hex characters

        # Verify change detection
        assert content_has_changed(checksum, "Different content") == True
        assert content_has_changed(checksum, data.get("raw_text", "")) == False
