from llama_index.core.workflow import StartEvent, StopEvent


class CVStartEvent(StartEvent):
    job_description: str


class CVStopEvent(StopEvent):
    resume: str
