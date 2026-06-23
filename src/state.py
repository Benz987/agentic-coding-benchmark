from typing import TypedDict, List

class AgenticResearchState(TypedDict):
    """Shared state for the LangGraph Level 3 architecture."""
    task_description: str
    difficulty: str
    test_cases: List[str]
    
    # Dynamic Map-Reduce variables
    sub_tasks: List[str]
    current_subtask_index: int
    
    # List of generated snippets. Managed manually to allow clearing on re-plan.
    code_snippets: List[str]
    
    # NEW: Round 2 Modifications
    design_manifest: str      # Holds the global SOP and structural rules
    structural_error: bool    # True if Critic forces a Manager re-plan
    
    # Integration and Evaluation variables
    current_code: str
    feedback: str
    critic_feedback: str
    passed: bool
    iterations: int