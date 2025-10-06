from pydantic import BaseModel, Field
from typing import Optional


class Experience(BaseModel):
    """Professional experience entry."""

    company: str = Field(..., description="Company/Organization Name")
    job_title: str = Field(..., description="Job Title/Position")
    start_date: str = Field(..., description="Start Date (e.g., Jan 2020)")
    end_date: Optional[str] = Field(
        None, description="End Date (e.g., Dec 2021 or Present)"
    )
    bullet_points: list[str] = Field(
        ..., description="List of responsibilities and achievements"
    )
    location: str = Field(
        ...,
        description="Location of the job. Use the format 'State, Country' or 'Remote'."
        "If not clear, assume 'Remote'.",
    )


class Skills(BaseModel):
    """Skills section."""

    technical_skills: list[str] = Field(..., description="List of technical skills")
    soft_skills: list[str] = Field(..., description="List of soft skills")
    languages: list[str] = Field(..., description="List of languages known")


class Education(BaseModel):
    """Educational background entry."""

    institution: str = Field(..., description="Name of the educational institution")
    degree: str = Field(
        ..., description="Degree obtained (e.g., B.Sc. in Computer Science)"
    )
    graduation_year: str = Field(..., description="Year of graduation (e.g., 2020)")
    location: str = Field(
        ...,
        description="Location of the institution. Use the format 'State, Country' or 'Remote'."
        "If not clear, assume 'Remote'.",
    )


class Resume(BaseModel):
    """Resume structure."""

    name: str = Field(..., description="Full name of the individual")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    address: str = Field(
        ...,
        description="Physical address, use the format 'City, State Abbreviation, Country'",
    )
    linkedIn: Optional[str] = Field(
        ...,
        description="LinkedIn profile URL. If applicable, use the format 'linkedin.com/in/joe-dee-dev'",
    )
    github: Optional[str] = Field(
        ...,
        description="GitHub profile URL. If applicable, use the format 'github.com/joe-dee-dev'",
    )
    experience: list[Experience] = Field(
        ..., description="List of professional experiences"
    )
    skills: Skills = Field(..., description="Skills section")
    education: list[Education] = Field(
        ..., description="List of educational qualifications"
    )
    considerations: Optional[str] = Field(
        None,
        description="Write here, in markdown format, any considerations or notes related to the resume that you built. As example, "
        "indicate what skills you recognized as important, but you don't have experience with. Or indicate if you "
        "have any gap in your career.",
    )
