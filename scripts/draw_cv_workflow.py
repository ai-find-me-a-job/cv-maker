"""
Script to visualize the CVWorkflow using LlamaIndex's draw_all_possible_flows.

This script imports the CVWorkflow class and generates an HTML file that visualizes
all possible flows in the workflow. It sets up the necessary paths to allow imports
from the parent directory and outputs the visualization to 'docs/cv_workflow.html'
relative to the root directory.
"""

from llama_index.utils.workflow import draw_all_possible_flows
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))  # Allow imports from parent directory

from src.services import CVWorkflow

if __name__ == "__main__":
    draw_all_possible_flows(CVWorkflow, str(ROOT_DIR / "docs/cv_workflow.html"))
