"""
Integration tests for the complete CV Maker workflow.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.cv_maker.workflow import CVWorkflow
from src.cv_maker.workflow.custom_events import (
    CVStartEvent,
    CVStopEvent,
)


class TestCVWorkflowIntegration:
    """Integration tests for the complete CV workflow."""

    @pytest.fixture
    def workflow_with_mocks(self, mock_llm, mock_web_scraper, sample_resume):
        """Create a workflow with all dependencies mocked."""
        workflow = CVWorkflow()

        # Mock the LLM
        workflow.llm = mock_llm

        # Mock the index and query engine
        mock_index = Mock()
        mock_query_engine = AsyncMock()
        mock_response = Mock()
        mock_response.response = sample_resume
        mock_query_engine.aquery.return_value = mock_response
        mock_index.as_query_engine.return_value = mock_query_engine
        workflow.index = mock_index

        # Mock the LaTeX generator
        workflow.latex_generator = Mock()
        workflow.latex_generator.generate_pdf.return_value = "output/resume.pdf"

        return workflow

    @patch("src.cv_maker.workflow.scrape_job_url")
    @patch("builtins.open", create=True)
    async def test_full_workflow_with_job_url(
        self,
        mock_open,
        mock_scrape,
        workflow_with_mocks,
        sample_job_url,
        mock_web_scraper,
        sample_resume,
    ):
        """Test the complete workflow starting with a job URL."""
        # Setup mocks
        mock_scrape.return_value = mock_web_scraper
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Start the workflow
        start_event = CVStartEvent(job_url=sample_job_url)

        # Run the workflow
        result = await workflow_with_mocks.run(start_event)

        # Verify the workflow completed successfully
        assert isinstance(result, CVStopEvent)
        assert result.resume == sample_resume
        assert result.pdf_path == "output/resume.pdf"

        # Verify all steps were called
        mock_scrape.assert_called_once_with(sample_job_url)
        workflow_with_mocks.llm.acomplete.assert_called()
        workflow_with_mocks.index.as_query_engine.assert_called_once()
        workflow_with_mocks.latex_generator.generate_pdf.assert_called_once()

    @patch("builtins.open", create=True)
    async def test_full_workflow_with_job_description(
        self, mock_open, workflow_with_mocks, sample_job_description, sample_resume
    ):
        """Test the complete workflow starting with a job description."""
        # Setup mocks
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Start the workflow
        start_event = CVStartEvent(job_description=sample_job_description)

        # Run the workflow
        result = await workflow_with_mocks.run(start_event)

        # Verify the workflow completed successfully
        assert isinstance(result, CVStopEvent)
        assert result.resume == sample_resume
        assert result.pdf_path == "output/resume.pdf"

        # Verify steps were called (no web scraping for direct description)
        workflow_with_mocks.llm.acomplete.assert_not_called()  # No LLM for extraction
        workflow_with_mocks.index.as_query_engine.assert_called_once()
        workflow_with_mocks.latex_generator.generate_pdf.assert_called_once()

    @patch("src.cv_maker.workflow.scrape_job_url")
    @patch("builtins.open", create=True)
    async def test_workflow_with_web_scraping_failure(
        self, mock_open, mock_scrape, workflow_with_mocks, sample_job_url, sample_resume
    ):
        """Test workflow handles web scraping failure gracefully."""
        # Setup mocks - web scraping fails
        mock_scrape.return_value = {
            "status": "error",
            "text": "",
            "page_title": "",
            "final_url": sample_job_url,
            "error": "Failed to load page",
        }
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock LLM to provide fallback description
        workflow_with_mocks.llm.acomplete.return_value = Mock(
            text="Fallback job description"
        )

        # Start the workflow
        start_event = CVStartEvent(job_url=sample_job_url)

        # Run the workflow
        result = await workflow_with_mocks.run(start_event)

        # Verify the workflow still completes
        assert isinstance(result, CVStopEvent)
        assert result.resume == sample_resume
        assert result.pdf_path == "output/resume.pdf"

    @patch("builtins.open", create=True)
    async def test_workflow_with_pdf_generation_failure(
        self, mock_open, workflow_with_mocks, sample_job_description, sample_resume
    ):
        """Test workflow handles PDF generation failure gracefully."""
        # Setup mocks - PDF generation fails
        workflow_with_mocks.latex_generator.generate_pdf.side_effect = Exception(
            "LaTeX compilation failed"
        )
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Start the workflow
        start_event = CVStartEvent(job_description=sample_job_description)

        # Run the workflow
        result = await workflow_with_mocks.run(start_event)

        # Verify the workflow completes with empty PDF path
        assert isinstance(result, CVStopEvent)
        assert result.resume == sample_resume
        assert result.pdf_path == ""  # Empty indicates failure

    async def test_workflow_timeout_handling(
        self, workflow_with_mocks, sample_job_description
    ):
        """Test workflow handles timeout gracefully."""
        # Mock a slow operation
        workflow_with_mocks.index.as_query_engine.return_value.aquery.side_effect = (
            asyncio.TimeoutError()
        )

        # Start the workflow
        start_event = CVStartEvent(job_description=sample_job_description)

        # The workflow should handle the timeout
        with pytest.raises(asyncio.TimeoutError):
            await workflow_with_mocks.run(start_event)

    @patch("builtins.open", create=True)
    async def test_workflow_event_flow(
        self, mock_open, workflow_with_mocks, sample_job_description, sample_resume
    ):
        """Test that events flow correctly through the workflow."""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Track events by patching the workflow methods
        start_called = False
        generate_resume_called = False
        generate_pdf_called = False

        original_start = workflow_with_mocks.start
        original_generate_resume = workflow_with_mocks.generate_resume
        original_generate_pdf = workflow_with_mocks.generate_pdf

        async def mock_start(*args, **kwargs):
            nonlocal start_called
            start_called = True
            return await original_start(*args, **kwargs)

        async def mock_generate_resume(*args, **kwargs):
            nonlocal generate_resume_called
            generate_resume_called = True
            return await original_generate_resume(*args, **kwargs)

        async def mock_generate_pdf(*args, **kwargs):
            nonlocal generate_pdf_called
            generate_pdf_called = True
            return await original_generate_pdf(*args, **kwargs)

        workflow_with_mocks.start = mock_start
        workflow_with_mocks.generate_resume = mock_generate_resume
        workflow_with_mocks.generate_pdf = mock_generate_pdf

        # Start the workflow
        start_event = CVStartEvent(job_description=sample_job_description)

        # Run the workflow
        result = await workflow_with_mocks.run(start_event)

        # Verify all steps were called in order
        assert start_called, "Start step was not called"
        assert generate_resume_called, "Generate resume step was not called"
        assert generate_pdf_called, "Generate PDF step was not called"
        assert isinstance(result, CVStopEvent)
