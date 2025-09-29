from llama_index.core.workflow import StartEvent, StopEvent
from .models import Resume


class CVStartEvent(StartEvent):
    job_description: str


class CVStopEvent(StopEvent):
    resume: Resume
