"""
Tests for the FastAPI endpoints in the CV Maker application.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json
from io import BytesIO

from main import app
from src.cv_maker.workflow.models import Resume, Experience, Skills


class TestCVEndpoints:
    """Test the CV generation endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def mock_workflow_response(self, sample_resume):
        """Mock successful workflow response."""
        return {
            "success": True,
            "resume": sample_resume,
            "pdf_path": "output/resume.pdf",
            "latex_content": "\\documentclass{article}\\begin{document}\\end{document}",
            "error": None,
        }

    @patch("src.api.v1.cv.run_cv_workflow")
    async def test_generate_cv_from_description_success(
        self, mock_run_workflow, client, mock_workflow_response, sample_job_description
    ):
        """Test successful CV generation from job description."""
        # Setup mock
        mock_run_workflow.return_value = mock_workflow_response

        # Make request
        response = client.post(
            "/cv/generate/from-description",
            json={"job_description": sample_job_description},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pdf_path"] == "output/resume.pdf"
        assert "latex_content" in data
        mock_run_workflow.assert_called_once()

    @patch("src.api.v1.cv.run_cv_workflow")
    async def test_generate_cv_from_description_failure(
        self, mock_run_workflow, client, sample_job_description
    ):
        """Test CV generation failure from job description."""
        # Setup mock for failure
        mock_run_workflow.return_value = {
            "success": False,
            "resume": None,
            "pdf_path": "",
            "latex_content": "",
            "error": "Workflow failed",
        }

        # Make request
        response = client.post(
            "/cv/generate/from-description",
            json={"job_description": sample_job_description},
        )

        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Workflow failed"

    async def test_generate_cv_from_description_validation_error(self, client):
        """Test validation error for missing job description."""
        # Make request with missing job_description
        response = client.post("/cv/generate/from-description", json={})

        # Verify response
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @patch("src.api.v1.cv.run_cv_workflow")
    async def test_generate_cv_from_url_success(
        self, mock_run_workflow, client, mock_workflow_response, sample_job_url
    ):
        """Test successful CV generation from job URL."""
        # Setup mock
        mock_run_workflow.return_value = mock_workflow_response

        # Make request
        response = client.post(
            "/cv/generate/from-url", json={"job_url": sample_job_url}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pdf_path"] == "output/resume.pdf"
        mock_run_workflow.assert_called_once()

    @patch("src.api.v1.cv.run_cv_workflow")
    async def test_generate_cv_from_url_failure(
        self, mock_run_workflow, client, sample_job_url
    ):
        """Test CV generation failure from job URL."""
        # Setup mock for failure
        mock_run_workflow.return_value = {
            "success": False,
            "resume": None,
            "pdf_path": "",
            "latex_content": "",
            "error": "Web scraping failed",
        }

        # Make request
        response = client.post(
            "/cv/generate/from-url", json={"job_url": sample_job_url}
        )

        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Web scraping failed"

    async def test_generate_cv_from_url_validation_error(self, client):
        """Test validation error for invalid job URL."""
        # Make request with invalid URL
        response = client.post(
            "/cv/generate/from-url", json={"job_url": "not-a-valid-url"}
        )

        # Verify response
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestIndexEndpoints:
    """Test the index management endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def sample_pdf_file(self):
        """Create a sample PDF file for testing."""
        pdf_content = b"%PDF-1.4\n%fake pdf content for testing"
        return ("test_resume.pdf", BytesIO(pdf_content), "application/pdf")

    @patch("src.api.v1.index.add_files_to_index")
    async def test_add_files_success(self, mock_add_files, client, sample_pdf_file):
        """Test successful file upload and indexing."""
        # Setup mock
        mock_add_files.return_value = {
            "success": True,
            "added_files": ["test_resume.pdf"],
            "total_files": 1,
            "error": None,
        }

        # Make request with file upload
        response = client.post("/cv/index/add-files", files={"files": sample_pdf_file})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_resume.pdf" in data["added_files"]
        assert data["total_files"] == 1
        mock_add_files.assert_called_once()

    @patch("src.api.v1.index.add_files_to_index")
    async def test_add_files_failure(self, mock_add_files, client, sample_pdf_file):
        """Test file upload and indexing failure."""
        # Setup mock for failure
        mock_add_files.return_value = {
            "success": False,
            "added_files": [],
            "total_files": 0,
            "error": "Failed to process file",
        }

        # Make request with file upload
        response = client.post("/cv/index/add-files", files={"files": sample_pdf_file})

        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to process file"

    async def test_add_files_no_files(self, client):
        """Test file upload endpoint with no files."""
        # Make request without files
        response = client.post("/cv/index/add-files")

        # Verify response
        assert response.status_code == 422


class TestMainEndpoints:
    """Test the main application endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "version" in data
        assert "documentation" in data

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_docs_endpoint(self, client):
        """Test that the docs endpoint is accessible."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_endpoint(self, client):
        """Test that the OpenAPI schema is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestErrorHandling:
    """Test error handling across all endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_404_error(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/non-existent-endpoint")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method."""
        response = client.get("/cv/generate/from-description")

        assert response.status_code == 405

    @patch("src.api.v1.cv.run_cv_workflow")
    async def test_internal_server_error_handling(
        self, mock_run_workflow, client, sample_job_description
    ):
        """Test handling of unexpected server errors."""
        # Setup mock to raise unexpected error
        mock_run_workflow.side_effect = Exception("Unexpected error")

        # Make request
        response = client.post(
            "/cv/generate/from-description",
            json={"job_description": sample_job_description},
        )

        # Verify response (should be handled gracefully)
        assert response.status_code == 500
