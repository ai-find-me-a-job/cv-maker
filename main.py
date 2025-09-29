from src.core.index_manager import VectorIndexManager
from src.cv_maker.workflow import CVWorkflow
from src.cv_maker.latex_generator import LaTeXGenerator
import asyncio


def test_vector_index():
    index_manager = VectorIndexManager()
    index = index_manager.get_index()

    print(f"Files already in index: {list(index_manager.get_added_files())}")
    index_manager.add_documents(["data/files/Resume___Ambev.pdf"])
    print(f"Files in index after adding: {list(index_manager.get_added_files())}")
    print(f"Index contains {len(index.docstore.docs)} documents.")


async def test_workflow():
    workflow = CVWorkflow()
    result = await workflow.run(job_description="Software Engineer at OpenAI")
    # print(f"Generated resume: {result.resume}")
    print(f"LaTeX content length: {len(result.latex_content)} characters")

    if result.pdf_path:
        print(f"PDF generated successfully: {result.pdf_path}")
    else:
        print("PDF generation failed, but LaTeX content is available")

    # Save LaTeX to file
    # latex_generator = LaTeXGenerator()
    # latex_generator.save_to_file(result.latex_content, "output/generated_resume.tex")
    print("LaTeX file saved to output/generated_resume.tex")


def test_latex_generator():
    # Test LaTeX generator with sample data
    from src.cv_maker.models import Resume, Experience, Skills, Education

    sample_resume = Resume(
        name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0123",
        address="San Francisco, CA",
        linkedIn="https://linkedin.com/in/johndoe",
        github="https://github.com/johndoe",
        experience=[
            Experience(
                company="Tech Corp",
                job_title="Software Engineer",
                start_date="Jan 2020",
                end_date="Present",
                bullet_points=[
                    "Developed web applications using Python and React",
                    "Improved system performance by 30%",
                    "Led a team of 3 developers",
                ],
            )
        ],
        skills=Skills(
            technical_skills=["Python", "JavaScript", "React", "SQL"],
            soft_skills=["Leadership", "Communication", "Problem Solving"],
            languages=["English (Native)", "Spanish (Conversational)"],
        ),
        education=[
            Education(
                institution="University of California",
                degree="B.S. Computer Science",
                graduation_year="2019",
            )
        ],
    )

    latex_gen = LaTeXGenerator()

    # Test LaTeX generation
    latex_content = latex_gen.generate(sample_resume)
    latex_gen.save_to_file(latex_content, "output/sample_resume.tex")
    print("Sample LaTeX file saved to output/sample_resume.tex")

    # Test PDF generation
    try:
        pdf_path = latex_gen.generate_pdf(sample_resume, "output/sample_resume")
        print(f"Sample PDF generated successfully: {pdf_path}")
    except Exception as e:
        print(f"PDF generation failed: {e}")
        print(
            "Make sure you have a LaTeX distribution (like MiKTeX or TeX Live) installed"
        )


if __name__ == "__main__":
    # Test vector index
    # print("=== Testing Vector Index ===")
    # test_vector_index()

    # Test LaTeX generator with sample data
    # print("\n=== Testing LaTeX Generator ===")
    # test_latex_generator()

    # Test LaTeX generator with sample data
    # print("\n=== Testing LaTeX Generator ===")
    # test_latex_generator()

    # Test full workflow (uncomment when ready to test)
    # print("\n=== Testing Full Workflow ===")
    asyncio.run(test_workflow())
