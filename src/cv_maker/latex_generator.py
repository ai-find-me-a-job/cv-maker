from .models import Resume, Experience, Education, Skills
from typing import List
from src.logger import default_logger


class LaTeXGenerator:
    """Generate LaTeX code from Resume model data."""

    def __init__(self):
        self.logger = default_logger

    def generate(self, resume: Resume) -> str:
        """
        Generate complete LaTeX document from Resume data.

        Args:
            resume: Resume model instance with all data

        Returns:
            Complete LaTeX document as string
        """
        self.logger.info("Starting LaTeX generation for resume")

        latex_content = self._generate_header()
        latex_content += self._generate_personal_info(resume)
        latex_content += self._generate_experience(resume.experience)
        latex_content += self._generate_skills(resume.skills)
        latex_content += self._generate_education(resume.education)
        latex_content += self._generate_footer()

        self.logger.info("LaTeX generation completed")
        return latex_content

    def _generate_header(self) -> str:
        """Generate LaTeX document header with packages and setup."""
        return """% GitHub Repo and Documentation: https://github.com/celiobjunior/resume-template
% Copyright © 2025 Celio B Junior. All rights reserved.
% 
% Licensed under the Apache License, Version 2.0 (the "License");
% you may not use this file except in compliance with the License.
% You may obtain a copy of the License at
%
%     http://www.apache.org/licenses/LICENSE-2.0
%
% This template follows best practices from README.md

% Start of LaTeX document: defines document type and format
% a4paper = A4 page size, 10pt = base font size
\\documentclass[a4paper,10pt]{article}

% --- PACKAGES ---
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage[english]{babel}
\\usepackage{geometry}
\\usepackage{parskip}
\\usepackage{hyperref}
\\usepackage{titlesec}
% For better line breaks in long URLs (don't use \\href{}, use \\url{} for long URLs)
% \\usepackage{xurl}

% --- DOCUMENT SETUP ---
% Set page margins to maximize content space
\\geometry{top=1.0cm, bottom=1.0cm, left=1.0cm, right=1.0cm}

% Remove page numbers and headers for clean resume look
\\pagestyle{empty}

% PDF metadata - customize with your information
\\hypersetup{
    pdftitle={CV Generated Resume},
    pdfauthor={Generated Resume},
    colorlinks=true,
    linkcolor=black,
    urlcolor=black,
    citecolor=black,
    bookmarksdepth=1 
}

% Disable section numbering for cleaner appearance
\\setcounter{secnumdepth}{0}

% Format section headers with bold text and underline
\\titleformat{\\section}
{\\Large\\bfseries}
{}
{0em}
{}
[\\titlerule\\vspace{0.5ex}]

% --- BEGIN DOCUMENT ---
\\begin{document}

"""

    def _generate_personal_info(self, resume: Resume) -> str:
        """Generate personal information header."""
        self.logger.debug(f"Generating personal info for {resume.name}")

        # Build contact information line
        contact_parts = []
        contact_parts.append(
            f"Email: \\href{{mailto:{resume.email}}}{{{resume.email}}}"
        )

        if resume.phone:
            contact_parts.append(f"Phone: {resume.phone}")

        if resume.linkedIn:
            # Extract username from LinkedIn URL if it's a full URL
            linkedin_display = resume.linkedIn
            if resume.linkedIn.startswith("http"):
                linkedin_display = resume.linkedIn.split("/in/")[-1].rstrip("/")
                linkedin_display = f"linkedin.com/in/{linkedin_display}"
            contact_parts.append(f"\\href{{{resume.linkedIn}}}{{{linkedin_display}}}")

        if resume.github:
            # Extract username from GitHub URL if it's a full URL
            github_display = resume.github
            if resume.github.startswith("http"):
                github_display = resume.github.split("/")[-1].rstrip("/")
                github_display = f"github.com/{github_display}"
            contact_parts.append(f"\\href{{{resume.github}}}{{{github_display}}}")

        contact_line = " {\\textbullet} ".join(contact_parts)

        return f"""% --- HEADER ---
% Personal information
\\begin{{center}}
    {{\\LARGE \\textbf{{{self._escape_latex(resume.name)}}}}} 
    \\\\ [0.1cm]
    {self._escape_latex(resume.address)}
    \\\\ [0.1cm] 
    {contact_line}
\\end{{center}}

"""

    def _generate_experience(self, experiences: List[Experience]) -> str:
        """Generate experience section."""
        self.logger.debug(
            f"Generating experience section with {len(experiences)} entries"
        )

        if not experiences:
            return ""

        latex = "\\section{Experience}\n"

        for exp in experiences:
            # Format dates
            date_range = exp.start_date
            if exp.end_date:
                date_range += f" - {exp.end_date}"

            latex += f"""    \\subsection*{{\\texorpdfstring{{
            \\textbf{{{self._escape_latex(exp.company)}}} \\hfill {self._escape_latex("Remote")}
        }}{{
            {self._escape_latex(exp.company)} -- Remote
        }}}}
    \\textit{{{self._escape_latex(exp.job_title)} \\hfill {self._escape_latex(date_range)}}}
        \\begin{{itemize}}
"""

            # Add bullet points
            for bullet in exp.bullet_points:
                latex += f"            \\item {self._escape_latex(bullet)}\n"

            latex += "        \\end{itemize}\n\n"

        return latex

    def _generate_skills(self, skills: Skills) -> str:
        """Generate skills section."""
        self.logger.debug("Generating skills section")

        latex = "\\section{Skills}\n    \\begin{itemize}\n"

        if skills.technical_skills:
            technical_skills_str = ", ".join(skills.technical_skills)
            latex += f"        \\item \\textbf{{Technical:}} {self._escape_latex(technical_skills_str)}\n"

        if skills.languages:
            languages_str = ", ".join(skills.languages)
            latex += f"        \\item \\textbf{{Languages:}} {self._escape_latex(languages_str)}\n"

        if skills.soft_skills:
            soft_skills_str = ", ".join(skills.soft_skills)
            latex += f"        \\item \\textbf{{Soft Skills:}} {self._escape_latex(soft_skills_str)}\n"

        latex += "    \\end{itemize}\n\n"
        return latex

    def _generate_education(self, education: List[Education]) -> str:
        """Generate education section."""
        self.logger.debug(f"Generating education section with {len(education)} entries")

        if not education:
            return ""

        latex = "\\section{Education}\n"

        for edu in education:
            latex += f"""    \\subsection*{{\\texorpdfstring{{
            \\textbf{{{self._escape_latex(edu.institution)}}} \\hfill {self._escape_latex("Remote")}
        }}{{
            {self._escape_latex(edu.institution)} (Education) -- Remote
        }}}}
    \\textit{{{self._escape_latex(edu.degree)} \\hfill {self._escape_latex(edu.graduation_year)}}}

"""

        return latex

    def _generate_footer(self) -> str:
        """Generate document footer."""
        return "\\end{document}\n"

    def _escape_latex(self, text: str) -> str:
        """
        Escape special LaTeX characters in text.

        Args:
            text: Input text that may contain special characters

        Returns:
            Text with LaTeX special characters properly escaped
        """
        if not text:
            return ""

        # Dictionary of LaTeX special characters and their escaped versions
        latex_special_chars = {
            "&": "\\&",
            "%": "\\%",
            "$": "\\$",
            "#": "\\#",
            "^": "\\textasciicircum{}",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "~": "\\textasciitilde{}",
            "\\": "\\textbackslash{}",
        }

        escaped_text = text
        for char, escaped in latex_special_chars.items():
            escaped_text = escaped_text.replace(char, escaped)

        return escaped_text

    def save_to_file(self, latex_content: str, output_path: str) -> None:
        """
        Save LaTeX content to file.

        Args:
            latex_content: Generated LaTeX document content
            output_path: Path where to save the .tex file
        """
        self.logger.info(f"Saving LaTeX content to {output_path}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        self.logger.info(f"LaTeX file saved successfully to {output_path}")
