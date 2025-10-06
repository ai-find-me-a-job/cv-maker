from llama_index.core.workflow import StartEvent, StopEvent, Event
from .extraction_models import Resume


class CVStartEvent(StartEvent):
    job_url: str | None = None
    job_description: str | None = None


class ExtractJobDescriptionEvent(Event):
    job_url: str


class GenerateResumeEvent(Event):
    job_description: str
    personal_info: str
    skills: str
    experiences: str
    education: str


class AskForCandidateInfoEvent(Event):
    job_description: str


class GeneratePDFEvent(Event):
    resume: Resume


class CVStopEvent(StopEvent):
    resume: Resume
    latex_content: str
    pdf_path: str
