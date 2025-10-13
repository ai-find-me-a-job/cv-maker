from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Event,
    InputRequiredEvent,
    HumanResponseEvent,
)
from .extraction_models import Resume


class CVStartEvent(StartEvent):
    job_url: str | None = None
    job_description: str | None = None


class ExtractJobDescriptionEvent(Event):
    job_url: str


class GenerateResumeEvent(Event):
    ...
    # personal_info: str
    # skills: str
    # experiences: str
    # education: str


class AskForCandidateInfoEvent(Event): ...


class GeneratePDFEvent(Event):
    resume: Resume


class AskForCVReviewEvent(InputRequiredEvent):
    latex_content: str
    pdf_path: str


class CVReviewResponseEvent(HumanResponseEvent):
    approve: bool
    feedback: str | None = None


class FinishWorkFlowEvent(Event): ...


class CVStopEvent(StopEvent):
    resume: Resume
    latex_content: str
