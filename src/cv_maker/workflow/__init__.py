from llama_index.core.workflow import Workflow, step
from .custom_events import (
    CVStartEvent,
    CVStopEvent,
    GenerateResumeEvent,
    GeneratePDFEvent,
    ExtractJobDescriptionEvent,
    AskForCandidateInfoEvent,
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
from .latex_generator import LaTeXGenerator
from src.core.web_scraper import scrape_job_url
from .prompts import RESUME_CREATION_PROMPT_TEMPLATE, JOB_EXTRACTION_PROMPT_TEMPLATE


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
    ) -> ExtractJobDescriptionEvent | AskForCandidateInfoEvent:
        if event.job_url:
            return ExtractJobDescriptionEvent(job_url=event.job_url)
        elif event.job_description:
            return AskForCandidateInfoEvent(job_description=event.job_description)
        else:
            raise ValueError("Either job_url or job_description must be provided.")

    @step
    async def extract_job_description(
        self, event: ExtractJobDescriptionEvent
    ) -> AskForCandidateInfoEvent:
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
            JOB_EXTRACTION_PROMPT_TEMPLATE.format(
                page_title=page_title, page_text=page_text
            )
        )

        job_description_text = job_description.text

        return AskForCandidateInfoEvent(job_description=job_description_text)

    @step
    async def ask_for_candidate_info(
        self, event: AskForCandidateInfoEvent
    ) -> GenerateResumeEvent:
        self.logger.info("Asking for candidate information to tailor the resume")

        query_engine = self.index.as_query_engine(
            llm=self.llm, response_mode="tree_summarize"
        )
        personal_info = await query_engine.aquery(
            """Try to find the maximum of personal information (name, phone, email, address, LinkedIn, GitHub, portfolio)"""
        )
        self.logger.debug(f"Extracted personal info: {personal_info}")

        skills = await query_engine.aquery(
            f"""List key skills that can be related to the job description below:
            {event.job_description}
            """
        )
        self.logger.debug(f"Extracted skills: {skills}")
        experiences = await query_engine.aquery(
            f"""List relevant experiences that can be related to the job description below, include the following details for each experience:
            - Job Title
            - Company Name
            - Dates of Employment (Start and End)
            - Location (City, State, Country or Remote)
            - Bullet points describing responsibilities and achievements (try to quantify achievements when possible)
            --------------
            {event.job_description}
            """
        )
        self.logger.debug(f"Extracted experiences: {experiences}")
        education = await query_engine.aquery(
            """List educational background such as degrees, certifications, and relevant coursework"""
        )
        self.logger.debug(f"Extracted education: {education}")
        return GenerateResumeEvent(
            job_description=event.job_description,
            personal_info=str(personal_info),
            skills=str(skills),
            experiences=str(experiences),
            education=str(education),
        )

    @step
    async def generate_resume(self, event: GenerateResumeEvent) -> GeneratePDFEvent:
        self.logger.info(
            f"Starting resume generation for job: {event.job_description[:50]}..."
        )

        prompt = RESUME_CREATION_PROMPT_TEMPLATE.format(
            personal_info=event.personal_info,
            skills=event.skills,
            experiences=event.experiences,
            education=event.education,
            job_description=event.job_description,
        )

        self.logger.info("Querying index for resume generation")
        response = await self.llm.as_structured_llm(output_cls=Resume).acomplete(prompt)

        self.logger.info("Resume data generated successfully")

        # Extract the Resume object from the PydanticResponse
        resume_data = response.raw
        return GeneratePDFEvent(resume=resume_data)

    @step
    async def generate_pdf(self, event: GeneratePDFEvent) -> CVStopEvent:
        self.logger.info("Starting PDF generation")

        # Generate timestamp for unique filename
        resume_output_path = "output/resume"
        considerations_output_path = "output/considerations.md"
        with open(considerations_output_path, "w", encoding="utf-8") as f:
            f.write(event.resume.considerations or "")

        try:
            pdf_path = self.latex_generator.generate_pdf(
                event.resume, resume_output_path, clean_temp_files=False
            )
            self.logger.info(f"PDF generated successfully: {pdf_path}")

            return CVStopEvent(
                resume=event.resume,
                latex_content=self.latex_generator.doc.dumps(),
                pdf_path=pdf_path,
            )
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            # Return without PDF path if generation fails
            return CVStopEvent(
                resume=event.resume,
                latex_content=self.latex_generator.doc.dumps(),
                pdf_path="",
            )
