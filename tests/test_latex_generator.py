"""
Tests for the LaTeX generator component.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import tempfile

from src.cv_maker.workflow.latex_generator import LaTeXGenerator
from src.cv_maker.workflow.models import Resume, Experience, Skills, Education


class TestLatexGenerator:
    """Test the LaTeX document generator."""

    @pytest.fixture
    def latex_generator(self):
        """Create a LaTeX generator instance."""
        return LaTeXGenerator()

    @pytest.fixture
    def sample_experience_with_special_chars(self):
        """Create experience with special LaTeX characters."""
        return Experience(
            title="Software Engineer @ Tech & Finance Corp",
            company="R&D Solutions Ltd.",
            duration="2020-2023",
            description="Developed APIs using Python & Django. Worked with 100% test coverage. Managed budgets of $50,000+.",
        )

    def test_escape_latex_special_characters(self, latex_generator):
        """Test LaTeX special character escaping."""
        test_cases = [
            ("Simple text", "Simple text"),
            ("Text with % percent", "Text with \\% percent"),
            ("Text with & ampersand", "Text with \\& ampersand"),
            ("Text with $ dollar", "Text with \\$ dollar"),
            ("Text with # hash", "Text with \\# hash"),
            ("Text with _ underscore", "Text with \\_ underscore"),
            ("Text with { braces }", "Text with \\{ braces \\}"),
            ("Text with ^ caret", "Text with \\textasciicircum{} caret"),
            ("Text with ~ tilde", "Text with \\textasciitilde{} tilde"),
            ("Text with \\ backslash", "Text with \\textbackslash{} backslash"),
            ("Multiple % & $ chars", "Multiple \\% \\& \\$ chars"),
        ]

        for input_text, expected_output in test_cases:
            result = latex_generator._escape_latex(input_text)
            assert result == expected_output, f"Failed for input: {input_text}"

    def test_escape_latex_none_and_empty(self, latex_generator):
        """Test LaTeX escaping with None and empty values."""
        assert latex_generator._escape_latex(None) == ""
        assert latex_generator._escape_latex("") == ""
        assert latex_generator._escape_latex("   ") == "   "

    def test_generate_experience_section(
        self, latex_generator, sample_experience_with_special_chars
    ):
        """Test generation of experience section with special characters."""
        result = latex_generator._generate_experience_section(
            [sample_experience_with_special_chars]
        )

        # Check that special characters are properly escaped
        assert "Software Engineer @ Tech \\& Finance Corp" in result
        assert "R\\&D Solutions Ltd." in result
        assert "100\\% test coverage" in result
        assert "\\$50,000+" in result

    def test_generate_skills_section(self, latex_generator):
        """Test generation of skills section."""
        skills = Skills(
            technical=["Python", "C++", "JavaScript"],
            soft=["Leadership", "Communication"],
            languages=["English", "Spanish"],
        )

        result = latex_generator._generate_skills_section(skills)

        assert "Technical Skills" in result
        assert "Python, C++, JavaScript" in result
        assert "Soft Skills" in result
        assert "Leadership, Communication" in result
        assert "Languages" in result
        assert "English, Spanish" in result

    def test_generate_skills_section_with_special_chars(self, latex_generator):
        """Test skills section with special characters."""
        skills = Skills(
            technical=["C++", "C#", ".NET Framework"],
            soft=["100% Commitment"],
            languages=["English & Spanish"],
        )

        result = latex_generator._generate_skills_section(skills)

        assert "C++" in result  # Should not be escaped
        assert "C\\#" in result  # Should be escaped
        assert ".NET Framework" in result
        assert "100\\% Commitment" in result
        assert "English \\& Spanish" in result

    def test_generate_education_section(self, latex_generator):
        """Test generation of education section."""
        education = [
            Education(
                degree="Bachelor of Science in Computer Science",
                institution="University of Technology & Engineering",
                year="2020",
                gpa="3.8/4.0",
            )
        ]

        result = latex_generator._generate_education_section(education)

        assert "Bachelor of Science in Computer Science" in result
        assert "University of Technology \\& Engineering" in result
        assert "2020" in result
        assert "3.8/4.0" in result

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_pdf_success(
        self, mock_file_open, mock_subprocess, latex_generator, sample_resume
    ):
        """Test successful PDF generation."""
        # Setup mocks
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            result = latex_generator.generate_pdf(sample_resume, output_dir=temp_dir)

            # Verify LaTeX file was written
            mock_file_open.assert_called()

            # Verify subprocess was called with pdflatex
            mock_subprocess.assert_called()
            call_args = mock_subprocess.call_args[0][0]
            assert "pdflatex" in call_args

            # Verify return path
            assert result.endswith(".pdf")

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_pdf_compilation_failure(
        self, mock_file_open, mock_subprocess, latex_generator, sample_resume
    ):
        """Test PDF generation with LaTeX compilation failure."""
        # Setup mock to simulate compilation failure
        mock_subprocess.return_value = Mock(
            returncode=1, stdout="", stderr="LaTeX Error: Missing \\begin{document}"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(Exception, match="LaTeX compilation failed"):
                latex_generator.generate_pdf(sample_resume, output_dir=temp_dir)

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_pdf_file_not_found(
        self, mock_file_open, mock_subprocess, latex_generator, sample_resume
    ):
        """Test PDF generation when pdflatex is not found."""
        # Setup mock to simulate pdflatex not found
        mock_subprocess.side_effect = FileNotFoundError("pdflatex not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(Exception, match="pdflatex not found"):
                latex_generator.generate_pdf(sample_resume, output_dir=temp_dir)

    def test_generate_complete_latex_document(self, latex_generator, sample_resume):
        """Test generation of complete LaTeX document."""
        result = latex_generator._generate_latex_content(sample_resume)

        # Check document structure
        assert "\\documentclass{article}" in result
        assert "\\begin{document}" in result
        assert "\\end{document}" in result

        # Check content sections
        assert sample_resume.personal_info.full_name in result
        assert sample_resume.personal_info.email in result
        assert sample_resume.personal_info.phone in result

        # Check that content is properly escaped
        if sample_resume.experience:
            for exp in sample_resume.experience:
                if "&" in exp.company:
                    assert "\\&" in result

    def test_generate_latex_with_empty_sections(self, latex_generator):
        """Test LaTeX generation with empty sections."""
        from src.cv_maker.workflow.models import PersonalInfo

        # Create minimal resume with empty sections
        minimal_resume = Resume(
            personal_info=PersonalInfo(
                full_name="John Doe", email="john@example.com", phone="123-456-7890"
            ),
            experience=[],
            skills=Skills(technical=[], soft=[], languages=[]),
            education=[],
            summary="",
            considerations="",
        )

        result = latex_generator._generate_latex_content(minimal_resume)

        # Should still generate valid LaTeX structure
        assert "\\documentclass{article}" in result
        assert "\\begin{document}" in result
        assert "\\end{document}" in result
        assert "John Doe" in result

        # Should handle empty sections gracefully
        assert "Experience" not in result or "No experience listed" in result

    def test_latex_template_integrity(self, latex_generator, sample_resume):
        """Test that generated LaTeX follows proper template structure."""
        result = latex_generator._generate_latex_content(sample_resume)

        # Check for essential LaTeX packages
        assert "\\usepackage{geometry}" in result
        assert "\\usepackage{enumitem}" in result
        assert "\\usepackage{titlesec}" in result

        # Check for proper sectioning
        assert "\\section{" in result

        # Check for proper list environments
        if sample_resume.experience:
            assert "\\begin{itemize}" in result
            assert "\\end{itemize}" in result

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_pdf_cleanup(
        self, mock_file_open, mock_subprocess, latex_generator, sample_resume
    ):
        """Test that auxiliary files are cleaned up after PDF generation."""
        # Setup mocks
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            latex_generator.generate_pdf(sample_resume, output_dir=temp_dir)

            # Check that cleanup commands were called
            # This would involve checking that .aux, .log, .out files are removed
            # For now, just verify the main compilation happened
            mock_subprocess.assert_called()
            assert mock_subprocess.call_count >= 1
