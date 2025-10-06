from src.cv_maker.workflow.models import Resume, Experience, Education, Skills
from typing import List
from src.logger import default_logger
from pylatex import Document, Section
from pylatex.package import Package
from pylatex.utils import NoEscape
import subprocess
from pathlib import Path


class LaTeXGenerator:
    """Generate LaTeX code from Resume model data using PyLaTeX."""

    def __init__(self):
        self.logger = default_logger
        self.doc: Document = self._initialize_document()

    def _initialize_document(self) -> Document:
        # Create document with geometry and basic setup
        doc = Document(geometry_options={"margin": "1cm"})

        # Add packages
        doc.packages.append(Package("inputenc", options=["utf8"]))
        doc.packages.append(Package("fontenc", options=["T1"]))
        doc.packages.append(Package("babel", options=["english"]))
        doc.packages.append(Package("parskip"))
        doc.packages.append(Package("hyperref"))
        doc.packages.append(Package("titlesec"))

        # Add document setup commands
        doc.append(NoEscape(r"\pagestyle{empty}"))
        doc.append(NoEscape(r"\setcounter{secnumdepth}{0}"))

        # Configure hyperref
        doc.append(
            NoEscape(
                r"\hypersetup{colorlinks=true,linkcolor=black,urlcolor=black,citecolor=black}"
            )
        )

        # Configure section formatting
        doc.append(
            NoEscape(
                r"\titleformat{\section}{\Large\bfseries}{}{0em}{}[\titlerule\vspace{0.5ex}]"
            )
        )
        return doc

    def generate_latex_doc(self, resume: Resume) -> Document:
        """
        Generate complete LaTeX document from Resume data.

        Args:
            resume: Resume model instance with all data

        Returns:
            Complete LaTeX document as Document object
        """
        self.logger.info("Starting LaTeX generation for resume using PyLaTeX")
        doc = self.doc
        # Generate content
        self._generate_personal_info(doc, resume)
        self._generate_experience(doc, resume.experience)
        self._generate_skills(doc, resume.skills)
        self._generate_education(doc, resume.education)

        self.logger.info("LaTeX generation completed")
        self.doc = doc
        return doc

    def _generate_personal_info(self, doc: Document, resume: Resume) -> None:
        """Generate personal information header."""
        self.logger.debug(f"Generating personal info for {resume.name}")

        # Build contact information
        contact_parts = []
        contact_parts.append(
            f"Email: \\href{{mailto:{resume.email}}}{{{resume.email}}}"
        )

        if resume.phone:
            contact_parts.append(f"Phone: {self._escape_latex(resume.phone)}")

        if resume.linkedIn:
            contact_parts.append(f"\\href{{{resume.linkedIn}}}{{{resume.linkedIn}}}")

        if resume.github:
            contact_parts.append(f"\\href{{{resume.github}}}{{{resume.github}}}")

        contact_line = " {\\textbullet} ".join(contact_parts)

        # Add header using center environment
        doc.append(NoEscape(r"\begin{center}"))
        doc.append(
            NoEscape(f"{{\\LARGE \\textbf{{{self._escape_latex(resume.name)}}}}}")
        )
        doc.append(NoEscape(r"\\ [0.1cm]"))
        doc.append(NoEscape(self._escape_latex(resume.address)))
        doc.append(NoEscape(r"\\ [0.1cm]"))
        doc.append(NoEscape(contact_line))
        doc.append(NoEscape(r"\end{center}"))
        doc.append(NoEscape(r"\vspace{0.5cm}"))

    def _generate_experience(
        self, doc: Document, experiences: List[Experience]
    ) -> None:
        """Generate experience section."""
        self.logger.debug(
            f"Generating experience section with {len(experiences)} entries"
        )

        if not experiences:
            return

        with doc.create(Section("Experience")):
            for exp in experiences:
                # Format dates
                date_range = exp.start_date
                if exp.end_date:
                    date_range += f" - {exp.end_date}"

                # Create subsection with company and location
                subsection_title = NoEscape(
                    f"\\textbf{{{self._escape_latex(exp.company)}}} \\hfill {exp.location}"
                )
                doc.append(NoEscape(f"\\subsection*{{{subsection_title}}}"))

                # Add job title and dates
                job_info = NoEscape(
                    f"\\textit{{{self._escape_latex(exp.job_title)} \\hfill {self._escape_latex(date_range)}}}"
                )
                doc.append(job_info)

                # Add bullet points
                doc.append(NoEscape(r"\begin{itemize}"))
                for bullet in exp.bullet_points:
                    doc.append(NoEscape(f"\\item {self._escape_latex(bullet)}"))
                doc.append(NoEscape(r"\end{itemize}"))
                doc.append(NoEscape(r"\vspace{0.2cm}"))

    def _generate_skills(self, doc: Document, skills: Skills) -> None:
        """Generate skills section."""
        self.logger.debug("Generating skills section")

        with doc.create(Section("Skills")):
            doc.append(NoEscape(r"\begin{itemize}"))
            if skills.technical_skills:
                technical_skills_str = ", ".join(
                    [self._escape_latex(skill) for skill in skills.technical_skills]
                )
                doc.append(
                    NoEscape(f"\\item \\textbf{{Technical:}} {technical_skills_str}")
                )

            if skills.languages:
                languages_str = ", ".join(
                    [self._escape_latex(lang) for lang in skills.languages]
                )
                doc.append(NoEscape(f"\\item \\textbf{{Languages:}} {languages_str}"))

            if skills.soft_skills:
                soft_skills_str = ", ".join(
                    [self._escape_latex(skill) for skill in skills.soft_skills]
                )
                doc.append(
                    NoEscape(f"\\item \\textbf{{Soft Skills:}} {soft_skills_str}")
                )
            doc.append(NoEscape(r"\end{itemize}"))

    def _generate_education(self, doc: Document, education: List[Education]) -> None:
        """Generate education section."""
        self.logger.debug(f"Generating education section with {len(education)} entries")

        if not education:
            return

        with doc.create(Section("Education")):
            for edu in education:
                # Create subsection with institution
                subsection_title = NoEscape(
                    f"\\textbf{{{self._escape_latex(edu.institution)}}} \\hfill {edu.location}"
                )
                doc.append(NoEscape(f"\\subsection*{{{subsection_title}}}"))

                # Add degree and graduation year
                degree_info = NoEscape(
                    f"\\textit{{{self._escape_latex(edu.degree)} \\hfill {self._escape_latex(edu.graduation_year)}}}"
                )
                doc.append(degree_info)
                doc.append(NoEscape(r"\vspace{0.2cm}"))

    def generate_pdf(
        self, resume: Resume, output_path: str, clean_temp_files: bool = True
    ) -> str:
        """
        Generate PDF directly from Resume data.

        Args:
            resume: Resume model instance with all data
            output_path: Path where to save the PDF file (without extension)

        Returns:
            Path to the generated PDF file
        """
        self.logger.info(f"Starting PDF generation for resume: {output_path}")
        doc = self.generate_latex_doc(resume)
        # Generate PDF
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate PDF
            doc.generate_pdf(
                output_path,
                clean=clean_temp_files,
                compiler="pdflatex",
                clean_tex=False,
            )
            pdf_path = f"{output_path}.pdf"
            self.logger.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            raise RuntimeError(f"PDF generation failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during PDF generation: {e}")
            raise

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

        # Escape backslash first to avoid double-escaping
        escaped_text = text.replace("\\", r"\textbackslash{}")

        # Dictionary of other LaTeX special characters and their escaped versions
        latex_special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "^": r"\textasciicircum{}",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
        }

        for char, escaped in latex_special_chars.items():
            escaped_text = escaped_text.replace(char, escaped)

        return escaped_text
