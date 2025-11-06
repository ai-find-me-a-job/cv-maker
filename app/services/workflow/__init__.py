import logging

from llama_index.core.workflow import Context, Workflow, step
from llama_index.llms.google_genai import GoogleGenAI

from app.core.config import config
from app.core.web_scraper import scrape_job_url
from app.services.index_manager import VectorIndexManager

from .context import CVWorkflowState
from .events import (
    AskForCandidateInfoEvent,
    AskForCVReviewEvent,
    CVReviewResponseEvent,
    CVStartEvent,
    CVStopEvent,
    ExtractJobDescriptionEvent,
    FinishWorkFlowEvent,
    GeneratePDFEvent,
    GenerateResumeEvent,
)
from .extraction_models import CandidateInfo, Resume
from .latex_generator import LaTeXGenerator
from .prompts import (
    JOB_EXTRACTION_PROMPT_TEMPLATE,
    RESUME_CREATION_PROMPT_TEMPLATE,
    RESUME_CREATION_PROMPT_TEMPLATE_WITH_FEEDBACK,
)


class CVWorkflow(Workflow):
    llm = GoogleGenAI(
        model=config.gemini_model,
        api_key=config.google_api_key,
        temperature=config.gemini_temperature,
    )
    index_manager = VectorIndexManager()
    index = index_manager.get_index()
    logger = logging.getLogger("cv_workflow")
    scraping_page_content_limit = config.scrapping_page_content_limit
    supported_languages = config.supported_languages

    @step
    async def start(
        self, ctx: Context[CVWorkflowState], event: CVStartEvent
    ) -> ExtractJobDescriptionEvent | AskForCandidateInfoEvent:
        await ctx.store.set("language", event.language)
        if event.job_url:
            return ExtractJobDescriptionEvent(job_url=event.job_url)
        elif event.job_description:
            await ctx.store.set("job_description", event.job_description)
            return AskForCandidateInfoEvent()
        else:
            raise ValueError("Either job_url or job_description must be provided.")

    @step
    async def extract_job_description(
        self, ctx: Context[CVWorkflowState], event: ExtractJobDescriptionEvent
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

        if len(page_text) > self.scraping_page_content_limit:
            self.logger.warning(
                f"Extracted page text length ({len(page_text)}) exceeds limit of {self.scraping_page_content_limit} characters. Truncating."
            )
            page_text = page_text[: self.scraping_page_content_limit]

        # Use LLM to extract job description from the page content
        job_description = await self.llm.acomplete(
            JOB_EXTRACTION_PROMPT_TEMPLATE.format(
                page_title=page_title, page_text=page_text
            )
        )

        await ctx.store.set("job_description", job_description.text)

        return AskForCandidateInfoEvent()

    @step
    async def ask_for_candidate_info(
        self, ctx: Context[CVWorkflowState], event: AskForCandidateInfoEvent
    ) -> GenerateResumeEvent:
        self.logger.info("Asking for candidate information to tailor the resume")
        state = await ctx.store.get_state()
        job_description = state.job_description

        query_engine = self.index.as_query_engine(
            llm=self.llm, response_mode="tree_summarize"
        )
        personal_info = await query_engine.aquery(
            """Try to find the maximum of personal information (name, phone, email, address, LinkedIn, GitHub, portfolio)"""
        )
        self.logger.debug(f"Extracted personal info: {personal_info}")

        skills = await query_engine.aquery(
            f"""List key skills that can be related to the job description below:
            {job_description}
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
            {job_description}
            """
        )
        self.logger.debug(f"Extracted experiences: {experiences}")
        education = await query_engine.aquery(
            """List educational background such as degrees and relevant coursework (but not certifications)"""
        )
        self.logger.debug(f"Extracted education: {education}")

        certifications = await query_engine.aquery(
            """List professional certifications with the following details for each:
            - Certification Name
            - Issuing Organization
            - Date obtained (and expiration if applicable)
            - Credential ID if available
            - URL to verify the certification if available
            Only include verified or formal certifications, not just courses or training."""
        )
        self.logger.debug(f"Extracted certifications: {certifications}")

        personal_projects = await query_engine.aquery(
            f"""List relevant personal projects that showcase skills related to the job description below.
            For each project include:
            - Project name
            - Brief description
            - Technologies/tools used
            - Key features or achievements
            - URL (GitHub, live demo, etc.) if available
            --------------
            {job_description}
            """
        )
        self.logger.debug(f"Extracted personal projects: {personal_projects}")
        candidate_info = CandidateInfo(
            personal_info=str(personal_info),
            skills=str(skills),
            experiences=str(experiences),
            education=str(education),
            certifications=str(certifications),
            personal_projects=str(personal_projects),
        )
        await ctx.store.set("candidate_info", candidate_info)
        return GenerateResumeEvent()

    @step
    async def generate_resume(
        self, ctx: Context[CVWorkflowState], event: GenerateResumeEvent
    ) -> GeneratePDFEvent:
        state = await ctx.store.get_state()
        job_description = state.job_description
        candidate_info = state.candidate_info
        if not candidate_info:
            raise ValueError("Candidate information is missing.")
        self.logger.info(
            f"Starting resume generation for job: {job_description[:50]}..."
        )
        language = state.language

        # Determine language instruction
        language_instruction = self.supported_languages.get(language, "English")
        prompt = RESUME_CREATION_PROMPT_TEMPLATE.format(
            language=language_instruction,
            personal_info=candidate_info.personal_info,
            skills=candidate_info.skills,
            experiences=candidate_info.experiences,
            education=candidate_info.education,
            certifications=candidate_info.certifications,
            personal_projects=candidate_info.personal_projects,
            job_description=job_description,
        )
        feedback = state.feedback
        if feedback:
            self.logger.info("Incorporating user feedback into resume generation")
            previous_resume = state.resume
            prompt = RESUME_CREATION_PROMPT_TEMPLATE_WITH_FEEDBACK.format(
                resume_creation_prompt=prompt,
                feedback=feedback,
                resume_text=previous_resume,
            )

        self.logger.info("Querying index for resume generation")
        response = await self.llm.as_structured_llm(output_cls=Resume).acomplete(prompt)

        self.logger.info("Resume data generated successfully")

        # Extract the Resume object from the PydanticResponse
        resume_data = response.raw
        if resume_data is None:
            raise ValueError("Failed to generate resume data from LLM response")

        # await ctx.store.set("resume", resume_data)
        return GeneratePDFEvent(resume=resume_data)

    @step
    async def generate_pdf(
        self, ctx: Context[CVWorkflowState], event: GeneratePDFEvent
    ) -> AskForCVReviewEvent:
        self.logger.info("Starting PDF generation")
        state = await ctx.store.get_state()
        language = state.language

        # Generate timestamp for unique filename
        resume_output_path = "output/resume"
        considerations_output_path = "output/considerations.md"
        with open(considerations_output_path, "w", encoding="utf-8") as f:
            f.write(event.resume.considerations or "")

        latex_generator = LaTeXGenerator(language=language)

        pdf_path = latex_generator.generate_pdf(
            event.resume, resume_output_path, clean_temp_files=True
        )
        latex_content = latex_generator.doc.dumps()
        await ctx.store.set("latex_content", latex_content)

        self.logger.info(f"PDF generated successfully: {pdf_path}")

        return AskForCVReviewEvent(latex_content=latex_content)

    @step
    async def analyze_review_answer(
        self, ctx: Context[CVWorkflowState], event: CVReviewResponseEvent
    ) -> FinishWorkFlowEvent | GenerateResumeEvent:
        if event.approve:
            self.logger.info("CV approved by the user")
            return FinishWorkFlowEvent()
        else:
            await ctx.store.set("feedback", event.feedback)
            return GenerateResumeEvent()

    @step
    async def stop(
        self, ctx: Context[CVWorkflowState], event: FinishWorkFlowEvent
    ) -> CVStopEvent:
        state = await ctx.store.get_state()
        resume = state.resume
        latex_content = state.latex_content
        if not resume or not latex_content:
            raise ValueError("Resume or LaTeX content is missing.")
        return CVStopEvent(
            resume=resume,
            latex_content=latex_content,
        )
