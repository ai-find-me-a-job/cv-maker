from llama_index.core.workflow import StartEvent, StopEvent, Event
from .models import Resume


class CVStartEvent(StartEvent):
    job_description: str


class CVGenerateLatexEvent(Event):
    resume: Resume


class CVStopEvent(StopEvent):
    latex_content: str
