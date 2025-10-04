"""
Unit tests for CV Maker workflow steps.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.cv_maker.workflow import CVWorkflow
from src.cv_maker.workflow.custom_events import (
    CVStartEvent,
    CVStopEvent,
    GenerateResumeEvent,
    GeneratePDFEvent,
    ExtractJobDescriptionEvent,
)


class TestCVWorkflowStart:
    """Test the CVWorkflow start step."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing."""
        return CVWorkflow()

    async def test_start_with_job_url(self, workflow, sample_job_url):
        """Test start step with job URL."""
        event = CVStartEvent(job_url=sample_job_url)

        result = await workflow.start(event)

        assert isinstance(result, ExtractJobDescriptionEvent)
        assert result.job_url == sample_job_url

    async def test_start_with_job_description(self, workflow, sample_job_description):
        """Test start step with job description."""
        event = CVStartEvent(job_description=sample_job_description)

        result = await workflow.start(event)

        assert isinstance(result, GenerateResumeEvent)
        assert result.job_description == sample_job_description

    async def test_start_with_both_url_and_description(
        self, workflow, sample_job_url, sample_job_description
    ):
        """Test start step prioritizes URL when both are provided."""
        event = CVStartEvent(
            job_url=sample_job_url, job_description=sample_job_description
        )

        result = await workflow.start(event)

        # Should prioritize URL over description
        assert isinstance(result, ExtractJobDescriptionEvent)
        assert result.job_url == sample_job_url

    async def test_start_with_neither_url_nor_description(self, workflow):
        """Test start step raises error when neither URL nor description provided."""
        event = CVStartEvent()

        with pytest.raises(
            ValueError, match="Either job_url or job_description must be provided"
        ):
            await workflow.start(event)


class TestCVWorkflowExtractJobDescription:
    """Test the CVWorkflow extract_job_description step."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing."""
        return CVWorkflow()

    @patch("src.cv_maker.workflow.scrape_job_url")
    async def test_extract_job_description_success(
        self, mock_scrape, workflow, sample_job_url, mock_web_scraper
    ):
        """Test successful job description extraction."""
        # Setup mocks
        mock_scrape.return_value = mock_web_scraper
        workflow.llm = AsyncMock()
        workflow.llm.acomplete.return_value = Mock(text="Extracted job description")

        event = ExtractJobDescriptionEvent(job_url=sample_job_url)

        result = await workflow.extract_job_description(event)

        assert isinstance(result, GenerateResumeEvent)
        assert result.job_description == "Extracted job description"
        mock_scrape.assert_called_once_with(sample_job_url)
        workflow.llm.acomplete.assert_called_once()

    @patch("src.cv_maker.workflow.scrape_job_url")
    async def test_extract_job_description_long_content(
        self, mock_scrape, workflow, sample_job_url
    ):
        """Test job description extraction with content exceeding limit."""
        # Setup mock with long content
        long_text = "x" * 20000  # Exceeds SCRAPPING_PAGE_CONTENT_LIMIT
        mock_web_scraper = {
            "text": long_text,
            "page_title": "Test Job",
            "final_url": sample_job_url,
        }
        mock_scrape.return_value = mock_web_scraper
        workflow.llm = AsyncMock()
        workflow.llm.acomplete.return_value = Mock(text="Extracted job description")

        event = ExtractJobDescriptionEvent(job_url=sample_job_url)

        result = await workflow.extract_job_description(event)

        assert isinstance(result, GenerateResumeEvent)
        # Verify content was truncated
        call_args = workflow.llm.acomplete.call_args[0][0]
        assert len(call_args) < len(long_text) + 1000  # Account for prompt overhead

    @patch("src.cv_maker.workflow.scrape_job_url")
    async def test_extract_job_description_scraping_failure(
        self, mock_scrape, workflow, sample_job_url
    ):
        """Test handling of scraping failure."""
        # Setup mock to return error
        mock_scrape.return_value = {
            "status": "error",
            "text": "",
            "page_title": "",
            "final_url": sample_job_url,
            "error": "Failed to load page",
        }
        workflow.llm = AsyncMock()
        workflow.llm.acomplete.return_value = Mock(text="Fallback description")

        event = ExtractJobDescriptionEvent(job_url=sample_job_url)

        result = await workflow.extract_job_description(event)

        assert isinstance(result, GenerateResumeEvent)
        assert result.job_description == "Fallback description"


class TestCVWorkflowGenerateResume:
    """Test the CVWorkflow generate_resume step."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing."""
        workflow = CVWorkflow()
        # Mock the index and query engine
        mock_index = Mock()
        mock_query_engine = AsyncMock()
        mock_index.as_query_engine.return_value = mock_query_engine
        workflow.index = mock_index
        return workflow

    async def test_generate_resume_success(
        self, workflow, sample_job_description, sample_resume
    ):
        """Test successful resume generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.response = sample_resume
        workflow.index.as_query_engine.return_value.aquery.return_value = mock_response

        event = GenerateResumeEvent(job_description=sample_job_description)

        result = await workflow.generate_resume(event)

        assert isinstance(result, GeneratePDFEvent)
        assert result.resume == sample_resume
        workflow.index.as_query_engine.assert_called_once()

    async def test_generate_resume_with_prompt_template(
        self, workflow, sample_job_description, sample_resume
    ):
        """Test that resume generation uses the correct prompt template."""
        # Setup mock response
        mock_response = Mock()
        mock_response.response = sample_resume
        workflow.index.as_query_engine.return_value.aquery.return_value = mock_response

        event = GenerateResumeEvent(job_description=sample_job_description)

        await workflow.generate_resume(event)

        # Verify the query was called with formatted prompt
        query_call_args = workflow.index.as_query_engine.return_value.aquery.call_args[
            0
        ][0]
        assert sample_job_description in query_call_args


class TestCVWorkflowGeneratePDF:
    """Test the CVWorkflow generate_pdf step."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing."""
        workflow = CVWorkflow()
        workflow.latex_generator = Mock()
        return workflow

    @patch("builtins.open", create=True)
    async def test_generate_pdf_success(
        self, mock_open, workflow, sample_resume, temp_output_dir
    ):
        """Test successful PDF generation."""
        # Setup mocks
        pdf_path = str(temp_output_dir / "test_resume.pdf")
        workflow.latex_generator.generate_pdf.return_value = pdf_path

        # Mock the file write operation
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        event = GeneratePDFEvent(resume=sample_resume)

        result = await workflow.generate_pdf(event)

        assert isinstance(result, CVStopEvent)
        assert result.resume == sample_resume
        assert result.pdf_path == pdf_path
        workflow.latex_generator.generate_pdf.assert_called_once()

    @patch("builtins.open", create=True)
    async def test_generate_pdf_failure(self, mock_open, workflow, sample_resume):
        """Test PDF generation failure handling."""
        # Setup mocks to raise exception
        workflow.latex_generator.generate_pdf.side_effect = Exception(
            "PDF generation failed"
        )

        # Mock the file write operation
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        event = GeneratePDFEvent(resume=sample_resume)

        result = await workflow.generate_pdf(event)

        assert isinstance(result, CVStopEvent)
        assert result.resume == sample_resume
        assert result.pdf_path == ""  # Empty path indicates failure

    @patch("builtins.open", create=True)
    async def test_generate_pdf_writes_considerations(
        self, mock_open, workflow, sample_resume
    ):
        """Test that considerations are written to file."""
        # Setup mocks
        pdf_path = "/tmp/test_resume.pdf"
        workflow.latex_generator.generate_pdf.return_value = pdf_path

        # Mock the file write operation
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        event = GeneratePDFEvent(resume=sample_resume)

        await workflow.generate_pdf(event)

        # Verify considerations file was opened and written
        mock_open.assert_called_with("output/considerations.md", "w", encoding="utf-8")
        mock_file.write.assert_called_once_with(sample_resume.considerations)
