"""
Test fixtures and utilities for CV Maker workflow tests.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile

from src.cv_maker.workflow.models import Resume, Experience, Skills, Education
from src.cv_maker.workflow.custom_events import (
    CVStartEvent,
    CVStopEvent,
    GenerateResumeEvent,
    GeneratePDFEvent,
    ExtractJobDescriptionEvent,
)


@pytest.fixture
def sample_resume():
    """Create a sample resume for testing."""
    return Resume(
        name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0123",
        address="San Francisco, CA, USA",
        linkedIn="linkedin.com/in/johndoe",
        github="github.com/johndoe",
        experience=[
            Experience(
                company="Tech Corp",
                job_title="Senior Software Engineer",
                start_date="Jan 2020",
                end_date="Present",
                location="San Francisco, CA",
                bullet_points=[
                    "Developed web applications using Python and React",
                    "Improved system performance by 30%",
                    "Led a team of 3 developers",
                ],
            ),
            Experience(
                company="StartupXYZ",
                job_title="Software Developer",
                start_date="Jun 2018",
                end_date="Dec 2019",
                location="Remote",
                bullet_points=[
                    "Built REST APIs using FastAPI",
                    "Implemented automated testing",
                    "Collaborated with cross-functional teams",
                ],
            ),
        ],
        skills=Skills(
            technical_skills=["Python", "JavaScript", "React", "FastAPI", "SQL"],
            soft_skills=["Leadership", "Communication", "Problem Solving"],
            languages=["English (Native)", "Spanish (Conversational)"],
        ),
        education=[
            Education(
                institution="University of California",
                degree="B.S. Computer Science",
                graduation_year="2018",
                location="Berkeley, CA",
            )
        ],
        considerations="Strong technical background with leadership experience.",
    )


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    We are looking for a Senior Python Developer with 5+ years of experience.
    
    Requirements:
    - Strong Python skills
    - Experience with FastAPI or Django
    - Knowledge of databases (PostgreSQL, MongoDB)
    - Experience with cloud platforms (AWS, GCP)
    - Git version control
    - Agile development experience
    
    Responsibilities:
    - Develop and maintain web applications
    - Design and implement APIs
    - Collaborate with cross-functional teams
    - Code reviews and mentoring
    """


@pytest.fixture
def sample_job_url():
    """Sample job URL for testing."""
    return "https://example.com/job-posting/senior-python-developer"


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    mock = AsyncMock()
    mock.acomplete.return_value = Mock(text="Mocked LLM response")
    return mock


@pytest.fixture
def mock_web_scraper():
    """Mock web scraper response."""
    return {
        "url": "https://example.com/job-posting",
        "status": "success",
        "html": "<html><body><h1>Job Title</h1><p>Job description content</p></body></html>",
        "text": "Job Title\nJob description content\nRequirements:\n- Python\n- FastAPI\n- 5+ years experience",
        "page_title": "Senior Python Developer - Example Company",
        "final_url": "https://example.com/job-posting/senior-python-developer",
    }


@pytest.fixture
def mock_index_manager():
    """Mock vector index manager."""
    mock = Mock()
    mock.get_index.return_value = Mock()
    mock.get_added_files.return_value = ["resume1.pdf", "resume2.pdf"]
    return mock


@pytest.fixture
def mock_latex_generator():
    """Mock LaTeX generator."""
    mock = Mock()
    mock.generate_pdf.return_value = "/tmp/test_resume.pdf"
    mock.generate.return_value = (
        "\\documentclass{article}\\begin{document}Test\\end{document}"
    )
    return mock


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def mock_environment_variables(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")
    monkeypatch.setenv("LLAMA_PARSE_API_KEY", "test_parse_key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("GEMINI_TEMPERATURE", "0.1")


@pytest.fixture
def cv_start_event_with_url(sample_job_url):
    """CV start event with job URL."""
    return CVStartEvent(job_url=sample_job_url)


@pytest.fixture
def cv_start_event_with_description(sample_job_description):
    """CV start event with job description."""
    return CVStartEvent(job_description=sample_job_description)


@pytest.fixture
def extract_job_description_event(sample_job_url):
    """Extract job description event."""
    return ExtractJobDescriptionEvent(job_url=sample_job_url)


@pytest.fixture
def generate_resume_event(sample_job_description):
    """Generate resume event."""
    return GenerateResumeEvent(job_description=sample_job_description)


@pytest.fixture
def generate_pdf_event(sample_resume):
    """Generate PDF event."""
    return GeneratePDFEvent(resume=sample_resume)


@pytest.fixture
def cv_stop_event(sample_resume):
    """CV stop event."""
    return CVStopEvent(
        resume=sample_resume,
        latex_content="\\documentclass{article}\\begin{document}Test\\end{document}",
        pdf_path="/tmp/test_resume.pdf",
    )
