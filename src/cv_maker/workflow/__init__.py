from llama_index.core.workflow import Workflow, step
from .custom_events import (
    CVStartEvent,
    CVStopEvent,
    CVGenerateResumeEvent,
    CVGenerateLatexEvent,
    CVGeneratePDFEvent,
    CVExtractJobDescriptionEvent,
)
from llama_index.llms.google_genai import GoogleGenAI
from src.config import (
    GOOGLE_API_KEY,
    SCRAPPING_PAGE_CONTENT_LIMIT,
    GEMINI_TEMPERATURE,
    GEMINI_MODEL,
)
from src.core.index_manager import VectorIndexManager
from src.logger import default_logger
from .models import Resume
from src.cv_maker.latex_generator import LaTeXGenerator
from src.core.web_scraper import scrape_job_url
from .prompts import RESUME_CREATION_PROMPT_TEMPLATE


class CVWorkflow(Workflow):
    llm = GoogleGenAI(
        model=GEMINI_MODEL, api_key=GOOGLE_API_KEY, temperature=GEMINI_TEMPERATURE
    )
    index_manager = VectorIndexManager()
    index = index_manager.get_index()
    latex_generator = LaTeXGenerator()
    logger = default_logger

    @step
    async def start(
        self, event: CVStartEvent
    ) -> CVExtractJobDescriptionEvent | CVGenerateResumeEvent:
        if event.job_url:
            return CVExtractJobDescriptionEvent(job_url=event.job_url)
        elif event.job_description:
            return CVGenerateResumeEvent(job_description=event.job_description)
        else:
            raise ValueError("Either job_url or job_description must be provided.")

    @step
    async def extract_job_description(
        self, event: CVExtractJobDescriptionEvent
    ) -> CVGenerateResumeEvent:
        self.logger.info(f"Extracting job description from URL: {event.job_url}")

        # Use Playwright scraper for better compatibility
        scraped_data = await scrape_job_url(event.job_url)

        # Get the page text content directly
        page_text = scraped_data.get("text", "")
        page_title = scraped_data.get("page_title", "")

        self.logger.info(
            f"Successfully extracted content from {scraped_data.get('final_url', event.job_url)}"
        )
        self.logger.debug(f"Extracted text length: {len(page_text)} characters")

        if len(page_text) > SCRAPPING_PAGE_CONTENT_LIMIT:
            self.logger.warning(
                f"Extracted page text length ({len(page_text)}) exceeds limit of {SCRAPPING_PAGE_CONTENT_LIMIT} characters. Truncating."
            )
            page_text = page_text[:SCRAPPING_PAGE_CONTENT_LIMIT]
        # Use LLM to extract job description from the page content
        job_description = await self.llm.acomplete(
            f"Extract the job description, requirements, responsibilities, and key information "
            f"from the following web page content. Focus on the actual job posting details and ignore "
            f"navigation, footer, and advertisement content.\n\n"
            f"Page Title: {page_title}\n\n"
            f"Page Content:\n{page_text}"
        )

        job_description_text = job_description.text

        return CVGenerateResumeEvent(job_description=job_description_text)

    @step
    async def generate_resume(
        self, event: CVGenerateResumeEvent
    ) -> CVGenerateLatexEvent:
        self.logger.info(
            f"Starting resume generation for job: {event.job_description[:50]}..."
        )

        query_engine = self.index.as_query_engine(
            llm=self.llm, output_cls=Resume, response_mode="tree_summarize"
        )

        prompt = RESUME_CREATION_PROMPT_TEMPLATE.format(
            job_description=event.job_description
        )

        self.logger.info("Querying index for resume generation")
        response = await query_engine.aquery(prompt)

        self.logger.info("Resume data generated successfully")
        # Extract the Resume object from the PydanticResponse
        resume_data = response.response
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
        resume_output_path = "output/resume"
        considerations_output_path = "output/considerations.md"
        with open(considerations_output_path, "w", encoding="utf-8") as f:
            f.write(event.resume.considerations or "")

        try:
            pdf_path = self.latex_generator.generate_pdf(
                event.resume, resume_output_path
            )
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
