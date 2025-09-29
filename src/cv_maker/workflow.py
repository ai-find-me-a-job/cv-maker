from llama_index.core.workflow import Workflow, step
from .custom_events import CVStartEvent, CVStopEvent
from llama_index.llms.google_genai import GoogleGenAI
from src.config import GOOGLE_API_KEY
from src.core.index_manager import VectorIndexManager, VectorStoreIndex


class CVWorkflow(Workflow):
    llm: GoogleGenAI = GoogleGenAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY)
    index_manager: VectorIndexManager = VectorIndexManager()
    index: VectorStoreIndex = index_manager.get_index()

    @step
    async def start(self, event: CVStartEvent) -> CVStopEvent:
        query_engine = self.index.as_query_engine(llm=self.llm)
        prompt = f"Generate a short resume for the following job description: {event.job_description}"
        response = await query_engine.aquery(prompt)
        return CVStopEvent(resume=response.response)
