"""
Tests for the CV Maker services layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil

from src.cv_maker.services import run_cv_workflow, add_files_to_index
from src.cv_maker.workflow.models import Resume
from src.cv_maker.workflow.custom_events import CVStopEvent


class TestRunCVWorkflow:
    """Test the CV workflow service function."""

    @pytest.fixture
    def mock_workflow_success(self, sample_resume):
        """Mock successful workflow execution."""
        mock_workflow = AsyncMock()
        stop_event = CVStopEvent(
            resume=sample_resume,
            pdf_path="output/resume.pdf",
            latex_content="\\documentclass{article}\\begin{document}Test\\end{document}",
        )
        mock_workflow.run.return_value = stop_event
        return mock_workflow

    @pytest.fixture
    def mock_workflow_failure(self):
        """Mock failed workflow execution."""
        mock_workflow = AsyncMock()
        mock_workflow.run.side_effect = Exception("Workflow execution failed")
        return mock_workflow

    @patch("src.cv_maker.services.CVWorkflow")
    async def test_run_cv_workflow_with_job_url_success(
        self, mock_workflow_class, mock_workflow_success, sample_job_url
    ):
        """Test successful CV workflow execution with job URL."""
        # Setup mocks
        mock_workflow_class.return_value = mock_workflow_success

        # Call the service
        result = await run_cv_workflow(job_url=sample_job_url)

        # Verify the result
        assert result["success"] is True
        assert result["pdf_path"] == "output/resume.pdf"
        assert "latex_content" in result
        assert result["error"] is None
        assert isinstance(result["resume"], Resume)

        # Verify workflow was called correctly
        mock_workflow_success.run.assert_called_once()
        start_event = mock_workflow_success.run.call_args[0][0]
        assert start_event.job_url == sample_job_url

    @patch("src.cv_maker.services.CVWorkflow")
    async def test_run_cv_workflow_with_job_description_success(
        self, mock_workflow_class, mock_workflow_success, sample_job_description
    ):
        """Test successful CV workflow execution with job description."""
        # Setup mocks
        mock_workflow_class.return_value = mock_workflow_success

        # Call the service
        result = await run_cv_workflow(job_description=sample_job_description)

        # Verify the result
        assert result["success"] is True
        assert result["pdf_path"] == "output/resume.pdf"
        assert result["error"] is None

        # Verify workflow was called correctly
        start_event = mock_workflow_success.run.call_args[0][0]
        assert start_event.job_description == sample_job_description

    @patch("src.cv_maker.services.CVWorkflow")
    async def test_run_cv_workflow_with_both_parameters(
        self,
        mock_workflow_class,
        mock_workflow_success,
        sample_job_url,
        sample_job_description,
    ):
        """Test CV workflow execution with both URL and description (URL takes precedence)."""
        # Setup mocks
        mock_workflow_class.return_value = mock_workflow_success

        # Call the service
        result = await run_cv_workflow(
            job_url=sample_job_url, job_description=sample_job_description
        )

        # Verify the result
        assert result["success"] is True

        # Verify workflow was called with URL (takes precedence)
        start_event = mock_workflow_success.run.call_args[0][0]
        assert start_event.job_url == sample_job_url
        assert start_event.job_description == sample_job_description

    @patch("src.cv_maker.services.CVWorkflow")
    async def test_run_cv_workflow_with_no_parameters(self, mock_workflow_class):
        """Test CV workflow execution with no parameters."""
        # Call the service
        result = await run_cv_workflow()

        # Verify the result indicates error
        assert result["success"] is False
        assert "Either job_url or job_description must be provided" in result["error"]
        assert result["pdf_path"] == ""
        assert result["latex_content"] == ""
        assert result["resume"] is None

    @patch("src.cv_maker.services.CVWorkflow")
    async def test_run_cv_workflow_execution_failure(
        self, mock_workflow_class, mock_workflow_failure, sample_job_url
    ):
        """Test CV workflow execution failure."""
        # Setup mocks
        mock_workflow_class.return_value = mock_workflow_failure

        # Call the service
        result = await run_cv_workflow(job_url=sample_job_url)

        # Verify the result indicates error
        assert result["success"] is False
        assert "Workflow execution failed" in result["error"]
        assert result["pdf_path"] == ""
        assert result["latex_content"] == ""
        assert result["resume"] is None

    @patch("src.cv_maker.services.CVWorkflow")
    async def test_run_cv_workflow_empty_pdf_path(
        self, mock_workflow_class, sample_job_url, sample_resume
    ):
        """Test CV workflow when PDF generation fails (empty path)."""
        # Setup mock with empty PDF path
        mock_workflow = AsyncMock()
        stop_event = CVStopEvent(
            resume=sample_resume,
            pdf_path="",  # Empty indicates PDF generation failure
            latex_content="\\documentclass{article}\\begin{document}Test\\end{document}",
        )
        mock_workflow.run.return_value = stop_event
        mock_workflow_class.return_value = mock_workflow

        # Call the service
        result = await run_cv_workflow(job_url=sample_job_url)

        # Verify the result shows PDF generation failure
        assert result["success"] is True  # Workflow succeeded, PDF failed
        assert result["pdf_path"] == ""
        assert "latex_content" in result  # LaTeX content should still be available
        assert result["resume"] == sample_resume


class TestAddFilesToIndex:
    """Test the file indexing service function."""

    @pytest.fixture
    def temp_files_dir(self):
        """Create a temporary directory with test files."""
        temp_dir = tempfile.mkdtemp()

        # Create test files
        pdf_file = Path(temp_dir) / "test_resume.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nfake pdf content")

        txt_file = Path(temp_dir) / "test_resume.txt"
        txt_file.write_text("Test resume content", encoding="utf-8")

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_file_uploads(self):
        """Mock FastAPI file uploads."""
        pdf_file = Mock()
        pdf_file.filename = "resume.pdf"
        pdf_file.content_type = "application/pdf"
        pdf_file.read = AsyncMock(return_value=b"%PDF-1.4\nfake pdf content")

        return [pdf_file]

    @patch("src.cv_maker.services.IndexManager")
    async def test_add_files_to_index_success(
        self, mock_index_manager_class, mock_file_uploads
    ):
        """Test successful file addition to index."""
        # Setup mocks
        mock_index_manager = Mock()
        mock_index_manager.add_files.return_value = {
            "success": True,
            "added_files": ["resume.pdf"],
            "total_files": 1,
            "error": None,
        }
        mock_index_manager_class.return_value = mock_index_manager

        # Call the service
        result = await add_files_to_index(mock_file_uploads)

        # Verify the result
        assert result["success"] is True
        assert "resume.pdf" in result["added_files"]
        assert result["total_files"] == 1
        assert result["error"] is None

        # Verify index manager was called
        mock_index_manager.add_files.assert_called_once()

    @patch("src.cv_maker.services.IndexManager")
    async def test_add_files_to_index_failure(
        self, mock_index_manager_class, mock_file_uploads
    ):
        """Test file addition to index failure."""
        # Setup mocks
        mock_index_manager = Mock()
        mock_index_manager.add_files.return_value = {
            "success": False,
            "added_files": [],
            "total_files": 0,
            "error": "Failed to process file",
        }
        mock_index_manager_class.return_value = mock_index_manager

        # Call the service
        result = await add_files_to_index(mock_file_uploads)

        # Verify the result
        assert result["success"] is False
        assert result["added_files"] == []
        assert result["total_files"] == 0
        assert "Failed to process file" in result["error"]

    @patch("src.cv_maker.services.IndexManager")
    async def test_add_files_to_index_exception(
        self, mock_index_manager_class, mock_file_uploads
    ):
        """Test file addition to index with exception."""
        # Setup mocks
        mock_index_manager = Mock()
        mock_index_manager.add_files.side_effect = Exception("Index error")
        mock_index_manager_class.return_value = mock_index_manager

        # Call the service
        result = await add_files_to_index(mock_file_uploads)

        # Verify the result
        assert result["success"] is False
        assert result["added_files"] == []
        assert result["total_files"] == 0
        assert "Index error" in result["error"]

    async def test_add_files_to_index_empty_files(self):
        """Test file addition to index with empty file list."""
        # Call the service with empty list
        result = await add_files_to_index([])

        # Verify the result
        assert result["success"] is False
        assert result["added_files"] == []
        assert result["total_files"] == 0
        assert "No files provided" in result["error"]

    @patch("src.cv_maker.services.IndexManager")
    async def test_add_files_to_index_multiple_files(self, mock_index_manager_class):
        """Test file addition to index with multiple files."""
        # Setup multiple mock file uploads
        pdf_file = Mock()
        pdf_file.filename = "resume1.pdf"
        pdf_file.content_type = "application/pdf"
        pdf_file.read = AsyncMock(return_value=b"%PDF-1.4\nfake pdf content")

        txt_file = Mock()
        txt_file.filename = "resume2.txt"
        txt_file.content_type = "text/plain"
        txt_file.read = AsyncMock(return_value=b"Resume text content")

        files = [pdf_file, txt_file]

        # Setup mocks
        mock_index_manager = Mock()
        mock_index_manager.add_files.return_value = {
            "success": True,
            "added_files": ["resume1.pdf", "resume2.txt"],
            "total_files": 2,
            "error": None,
        }
        mock_index_manager_class.return_value = mock_index_manager

        # Call the service
        result = await add_files_to_index(files)

        # Verify the result
        assert result["success"] is True
        assert len(result["added_files"]) == 2
        assert "resume1.pdf" in result["added_files"]
        assert "resume2.txt" in result["added_files"]
        assert result["total_files"] == 2

    @patch("src.cv_maker.services.IndexManager")
    async def test_add_files_to_index_file_read_error(self, mock_index_manager_class):
        """Test file addition when file reading fails."""
        # Setup mock file that fails to read
        error_file = Mock()
        error_file.filename = "error_resume.pdf"
        error_file.content_type = "application/pdf"
        error_file.read = AsyncMock(side_effect=Exception("File read error"))

        files = [error_file]

        # Call the service
        result = await add_files_to_index(files)

        # Verify the result
        assert result["success"] is False
        assert result["added_files"] == []
        assert result["total_files"] == 0
        assert "File read error" in result["error"]
