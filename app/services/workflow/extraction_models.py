from typing import List, Optional

from pydantic import BaseModel, Field


class ProfessionalSummary(BaseModel):
    """Professional summary section."""

    summary: str = Field(
        ...,
        description="A concise 4-5 line paragraph summarizing: field of work (e.g., Data Science, AI), "
        "years of experience/seniority level, main technologies, and impact/purpose.",
    )


class Certification(BaseModel):
    """Professional certification entry."""

    name: str = Field(..., description="Name of the certification")
    issuer: str = Field(..., description="Organization that issued the certification")
    date: str = Field(..., description="Date of certification (e.g., Jan 2020)")
    expiry_date: Optional[str] = Field(
        None, description="Expiration date if applicable (e.g., Dec 2025)"
    )
    credential_id: Optional[str] = Field(
        None, description="Certification credential ID if applicable"
    )
    credential_url: Optional[str] = Field(
        None, description="URL to verify the certification"
    )


class PersonalProject(BaseModel):
    """Personal project entry."""

    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Brief description of the project")
    technologies: List[str] = Field(
        ..., description="List of technologies used in the project"
    )
    url: Optional[str] = Field(
        None, description="URL to the project (e.g., GitHub repository)"
    )
    highlights: List[str] = Field(
        ..., description="Key achievements or features of the project"
    )


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
    professional_summary: Optional[ProfessionalSummary] = Field(
        None, description="Optional professional summary section"
    )
    certifications: Optional[List[Certification]] = Field(
        None, description="Optional list of professional certifications"
    )
    personal_projects: Optional[List[PersonalProject]] = Field(
        None, description="Optional list of personal projects"
    )
    considerations: Optional[str] = Field(
        None,
        description="Write here, in markdown format, any considerations or notes related to the resume that you built. As example, "
        "indicate what skills you recognized as important, but you don't have experience with. Or indicate if you "
        "have any gap in your career.",
    )


class CandidateInfo(BaseModel):
    personal_info: str
    skills: str
    experiences: str
    education: str
    certifications: str
    personal_projects: str
