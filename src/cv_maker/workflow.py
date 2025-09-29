from llama_index.core.workflow import Workflow, step
from .custom_events import CVStartEvent, CVStopEvent, CVGenerateLatexEvent
from llama_index.llms.google_genai import GoogleGenAI
from src.config import GOOGLE_API_KEY
from src.core.index_manager import VectorIndexManager
from src.logger import default_logger
from .models import Resume
from .latex_generator import LaTeXGenerator


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
        # The structured output should be directly in the response
        # When using output_cls=Resume, the response should be a Resume object
        return CVGenerateLatexEvent(resume=response.response)

    @step
    async def generate_latex(self, event: CVGenerateLatexEvent) -> CVStopEvent:
        self.logger.info("Starting LaTeX generation")

        latex_content = self.latex_generator.generate(event.resume)

        self.logger.info("LaTeX generation completed")
        return CVStopEvent(latex_content=latex_content)
