from llama_index.core.workflow import Workflow, step
from .custom_events import (
    CVStartEvent,
    CVStopEvent,
    CVGenerateLatexEvent,
    CVGeneratePDFEvent,
)
from llama_index.llms.google_genai import GoogleGenAI
from src.config import GOOGLE_API_KEY
from src.core.index_manager import VectorIndexManager
from src.logger import default_logger
from .models import Resume
from .latex_generator import LaTeXGenerator
import datetime


class CVWorkflow(Workflow):
    llm = GoogleGenAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY)
    index_manager = VectorIndexManager()
    index = index_manager.get_index()
    latex_generator = LaTeXGenerator()
    logger = default_logger

    @step
    async def generate_resume(self, event: CVStartEvent) -> CVGenerateLatexEvent:
        self.logger.info(
            f"Starting resume generation for job: {event.job_description[:50]}..."
        )

        query_engine = self.index.as_query_engine(
            llm=self.llm, output_cls=Resume, response_mode="tree_summarize"
        )
        prompt_template = """
        Generate a tailored resume for the following job description: {job_description}
        
        Use the information from the provided documents to create a professional resume that highlights 
        relevant experience, skills, and qualifications that match the job requirements.
        """
        prompt = prompt_template.format(job_description=event.job_description)

        self.logger.info("Querying index for resume generation")
        response = await query_engine.aquery(prompt)

        self.logger.info("Resume data generated successfully")
        # Extract the Resume object from the PydanticResponse
        resume_data = response.response if hasattr(response, "response") else response
        return CVGenerateLatexEvent(resume=resume_data)

    @step
    async def generate_latex(self, event: CVGenerateLatexEvent) -> CVGeneratePDFEvent:
        self.logger.info("Starting LaTeX generation")

        latex_content = self.latex_generator.generate(event.resume)

        self.logger.info("LaTeX generation completed")
        return CVGeneratePDFEvent(resume=event.resume, latex_content=latex_content)

    @step
    async def generate_pdf(self, event: CVGeneratePDFEvent) -> CVStopEvent:
        self.logger.info("Starting PDF generation")

        # Generate timestamp for unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/resume_{timestamp}"

        try:
            pdf_path = self.latex_generator.generate_pdf(event.resume, output_path)
            self.logger.info(f"PDF generated successfully: {pdf_path}")

            return CVStopEvent(
                resume=event.resume,
                latex_content=event.latex_content,
                pdf_path=pdf_path,
            )
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            # Return without PDF path if generation fails
            return CVStopEvent(
                resume=event.resume, latex_content=event.latex_content, pdf_path=""
            )
