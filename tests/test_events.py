"""
Unit tests for CV Maker workflow events.
"""

from src.cv_maker.workflow.custom_events import (
    CVStartEvent,
    CVStopEvent,
    GenerateResumeEvent,
    GeneratePDFEvent,
    ExtractJobDescriptionEvent,
)


class TestCVStartEvent:
    """Test the CVStartEvent class."""

    def test_cv_start_event_with_url(self, sample_job_url):
        """Test creating CVStartEvent with job URL."""
        event = CVStartEvent(job_url=sample_job_url)

        assert event.job_url == sample_job_url
        assert event.job_description is None

    def test_cv_start_event_with_description(self, sample_job_description):
        """Test creating CVStartEvent with job description."""
        event = CVStartEvent(job_description=sample_job_description)

        assert event.job_description == sample_job_description
        assert event.job_url is None

    def test_cv_start_event_with_both(self, sample_job_url, sample_job_description):
        """Test creating CVStartEvent with both URL and description."""
        event = CVStartEvent(
            job_url=sample_job_url, job_description=sample_job_description
        )

        assert event.job_url == sample_job_url
        assert event.job_description == sample_job_description

    def test_cv_start_event_empty(self):
        """Test creating CVStartEvent with no parameters."""
        event = CVStartEvent()

        assert event.job_url is None
        assert event.job_description is None


class TestExtractJobDescriptionEvent:
    """Test the ExtractJobDescriptionEvent class."""

    def test_extract_job_description_event_creation(self, sample_job_url):
        """Test creating ExtractJobDescriptionEvent."""
        event = ExtractJobDescriptionEvent(job_url=sample_job_url)

        assert event.job_url == sample_job_url


class TestGenerateResumeEvent:
    """Test the GenerateResumeEvent class."""

    def test_generate_resume_event_creation(self, sample_job_description):
        """Test creating GenerateResumeEvent."""
        event = GenerateResumeEvent(job_description=sample_job_description)

        assert event.job_description == sample_job_description


class TestGeneratePDFEvent:
    """Test the GeneratePDFEvent class."""

    def test_generate_pdf_event_creation(self, sample_resume):
        """Test creating GeneratePDFEvent."""
        event = GeneratePDFEvent(resume=sample_resume)

        assert event.resume == sample_resume
        assert event.resume.name == "John Doe"


class TestCVStopEvent:
    """Test the CVStopEvent class."""

    def test_cv_stop_event_creation(self, sample_resume):
        """Test creating CVStopEvent."""
        latex_content = "\\documentclass{article}\\begin{document}Test\\end{document}"
        pdf_path = "/tmp/test_resume.pdf"

        event = CVStopEvent(
            resume=sample_resume, latex_content=latex_content, pdf_path=pdf_path
        )

        assert event.resume == sample_resume
        assert event.latex_content == latex_content
        assert event.pdf_path == pdf_path

    def test_cv_stop_event_creation_minimal(self, sample_resume):
        """Test creating CVStopEvent with minimal fields."""
        event = CVStopEvent(resume=sample_resume, latex_content="", pdf_path="")

        assert event.resume == sample_resume
        assert event.latex_content == ""
        assert event.pdf_path == ""
