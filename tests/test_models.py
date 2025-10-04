"""
Unit tests for CV Maker workflow models.
"""

import pytest
from pydantic import ValidationError

from src.cv_maker.workflow.models import Resume, Experience, Skills, Education


class TestExperience:
    """Test the Experience model."""

    def test_experience_creation_valid(self):
        """Test creating a valid experience entry."""
        experience = Experience(
            company="Tech Corp",
            job_title="Software Engineer",
            start_date="Jan 2020",
            end_date="Present",
            location="San Francisco, CA",
            bullet_points=["Developed applications", "Led team meetings"],
        )

        assert experience.company == "Tech Corp"
        assert experience.job_title == "Software Engineer"
        assert experience.start_date == "Jan 2020"
        assert experience.end_date == "Present"
        assert experience.location == "San Francisco, CA"
        assert len(experience.bullet_points) == 2

    def test_experience_creation_minimal(self):
        """Test creating experience with minimal required fields."""
        experience = Experience(
            company="StartupXYZ",
            job_title="Developer",
            start_date="Jun 2018",
            location="Remote",
            bullet_points=["Built APIs"],
        )

        assert experience.company == "StartupXYZ"
        assert experience.end_date is None

    def test_experience_creation_invalid(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Experience(
                company="Tech Corp",
                # Missing job_title
                start_date="Jan 2020",
                location="San Francisco, CA",
                bullet_points=["Developed applications"],
            )


class TestSkills:
    """Test the Skills model."""

    def test_skills_creation_valid(self):
        """Test creating a valid skills entry."""
        skills = Skills(
            technical_skills=["Python", "JavaScript", "React"],
            soft_skills=["Leadership", "Communication"],
            languages=["English", "Spanish"],
        )

        assert len(skills.technical_skills) == 3
        assert "Python" in skills.technical_skills
        assert len(skills.soft_skills) == 2
        assert len(skills.languages) == 2

    def test_skills_creation_empty_lists(self):
        """Test creating skills with empty lists."""
        skills = Skills(
            technical_skills=[],
            soft_skills=[],
            languages=[],
        )

        assert skills.technical_skills == []
        assert skills.soft_skills == []
        assert skills.languages == []

    def test_skills_creation_invalid(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Skills(
                technical_skills=["Python"],
                # Missing soft_skills and languages
            )


class TestEducation:
    """Test the Education model."""

    def test_education_creation_valid(self):
        """Test creating a valid education entry."""
        education = Education(
            institution="University of California",
            degree="B.S. Computer Science",
            graduation_year="2020",
            location="Berkeley, CA",
        )

        assert education.institution == "University of California"
        assert education.degree == "B.S. Computer Science"
        assert education.graduation_year == "2020"
        assert education.location == "Berkeley, CA"

    def test_education_creation_invalid(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Education(
                institution="University of California",
                # Missing degree, graduation_year, location
            )


class TestResume:
    """Test the Resume model."""

    def test_resume_creation_valid(self, sample_resume):
        """Test creating a valid resume."""
        assert sample_resume.name == "John Doe"
        assert sample_resume.email == "john.doe@example.com"
        assert sample_resume.phone == "+1-555-0123"
        assert sample_resume.address == "San Francisco, CA, USA"
        assert sample_resume.linkedIn == "linkedin.com/in/johndoe"
        assert sample_resume.github == "github.com/johndoe"
        assert len(sample_resume.experience) == 2
        assert isinstance(sample_resume.skills, Skills)
        assert len(sample_resume.education) == 1
        assert sample_resume.considerations is not None

    def test_resume_creation_minimal(self):
        """Test creating resume with minimal required fields."""
        resume = Resume(
            name="Jane Smith",
            email="jane@example.com",
            phone="555-1234",
            address="New York, NY, USA",
            linkedIn=None,
            github=None,
            experience=[],
            skills=Skills(
                technical_skills=["Python"],
                soft_skills=["Communication"],
                languages=["English"],
            ),
            education=[],
        )

        assert resume.name == "Jane Smith"
        assert resume.linkedIn is None
        assert resume.github is None
        assert len(resume.experience) == 0
        assert len(resume.education) == 0

    def test_resume_creation_invalid(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Resume(
                name="John Doe",
                # Missing required fields
            )

    def test_resume_nested_validation(self):
        """Test that nested model validation works correctly."""
        with pytest.raises(ValidationError):
            Resume(
                name="John Doe",
                email="john@example.com",
                phone="555-1234",
                address="San Francisco, CA",
                linkedIn=None,
                github=None,
                experience=[
                    # Invalid experience - missing required fields
                    {
                        "company": "Tech Corp",
                        # Missing job_title, start_date, location, bullet_points
                    }
                ],
                skills=Skills(
                    technical_skills=["Python"],
                    soft_skills=["Communication"],
                    languages=["English"],
                ),
                education=[],
            )
