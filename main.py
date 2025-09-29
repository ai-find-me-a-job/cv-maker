from src.core.index_manager import VectorIndexManager
from src.cv_maker.workflow import CVWorkflow
import asyncio


def test_vector_index():
    index_manager = VectorIndexManager()
    index = index_manager.get_index()
    index_manager.add_documents(["data/files/Resume___Ambev.pdf"])
    print(f"Index contains {index.index_struct.nodes_dict} nodes.")


async def test_workflow():
    workflow = CVWorkflow()
    result = await workflow.run(job_description="Software Engineer at OpenAI")
    print(f"Generated resume: {result.resume}")


if __name__ == "__main__":
    asyncio.run(test_workflow())
