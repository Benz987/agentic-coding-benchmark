import re
import tempfile
import os
import time
import docker
from typing import Dict, Any
from src.state import AgenticResearchState
from src.prompts import MANAGER_PROMPT, DEVELOPER_PROMPT, INTEGRATOR_PROMPT, CRITIC_PROMPT, SINGLE_AGENT_PROMPT
from src.llm_client import call_llm, extract_json_from_llm, clean_code
from src.logger import logger, log_agent_interaction

# --- Docker Sandbox Orchestrator ---

def evaluate_with_docker(code: str, test_cases: list, timeout: int = 5) -> Dict[str, Any]:
    """Evaluates code by spinning up an isolated, network-disabled Docker container."""
    try:
        client = docker.from_env()
    except Exception as e:
        return {"passed": False, "feedback": f"SYSTEM ERROR: Docker daemon not running: {e}"}

    # Combine the LLM's code with the assertions
    full_script = code + "\n\n# --- AUTOMATED TESTS ---\n" + "\n".join(test_cases)
    
    # Create a temporary directory on the host machine
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "evaluate.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(full_script)
            
        container = None
        try:
            # Spin up the ephemeral container
            container = client.containers.run(
                "python:3.10-alpine",
                command="python /app/evaluate.py",
                volumes={tmpdir: {'bind': '/app', 'mode': 'ro'}}, # Read-only mount
                working_dir="/app",
                mem_limit="128m",       # Prevent memory exhaustion
                network_disabled=True,  # Prevent data exfiltration or external API calls
                detach=True             # Run in background to track timeouts
            )
            
            # Timeout monitoring loop
            start_time = time.time()
            while container.status in ['created', 'running']:
                if time.time() - start_time > timeout:
                    container.kill()
                    return {"passed": False, "feedback": f"Execution timed out ({timeout}s). Possible infinite loop."}
                time.sleep(0.1)
                container.reload() # Refresh container status
            
            # Retrieve results
            result = container.wait()
            logs = container.logs().decode("utf-8").strip()
            
            if result["StatusCode"] == 0:
                return {"passed": True, "feedback": "All test cases passed successfully."}
            else:
                return {"passed": False, "feedback": f"Execution Error:\n{logs}"}
                
        except Exception as e:
            return {"passed": False, "feedback": f"Sandbox Error:\n{str(e)}"}
        finally:
            # Cleanup: Always destroy the container, even if the code crashes
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

# --- Nodes ---

def single_agent_node(state: AgenticResearchState) -> Dict[str, Any]:
    """Level 1 Baseline: A single agent attempting the whole task zero-shot."""
    logger.info("Single Agent: Attempting to solve the entire task zero-shot...")
    
    task = state["task_description"]
    user_prompt = f"### TASK DESCRIPTION ###\n{task}\n"
    
    llm_response = call_llm(SINGLE_AGENT_PROMPT, user_prompt, temperature=0.2)
    
    log_agent_interaction("SINGLE_AGENT", user_prompt, llm_response)
    clean_final_code = clean_code(llm_response)
    
    return {
        "current_code": clean_final_code
    }

def manager_node(state: AgenticResearchState) -> Dict[str, Any]:
    logger.info("Manager Agent: Analyzing task and defining Architecture Manifest...")
    
    task = state["task_description"]
    user_prompt = f"### TASK DESCRIPTION ###\n{task}\n"
    
    critic_fb = state.get("critic_feedback", "")
    if critic_fb and state.get("structural_error", False):
        logger.warning("Manager Agent: Major structural failure detected. Re-planning entirely based on Critic's feedback.")
        user_prompt += f"\n\n### CRITIC FEEDBACK ###\n{critic_fb}\n"
    
    llm_response = call_llm(MANAGER_PROMPT, user_prompt, temperature=0.1)
    log_agent_interaction("MANAGER", user_prompt, llm_response)
    
    # Extract the SOP Manifest
    manifest_match = re.search(r'### MANIFEST ###\n(.*?)(?:\n###|$|```json)', llm_response, re.DOTALL)
    manifest = manifest_match.group(1).strip() if manifest_match else "Follow standard Python conventions."
    
    # Extract the Subtasks
    tasks_list = extract_json_from_llm(llm_response)
    
    logger.info(f"Manager Agent: Created Global SOP Manifest and found {len(tasks_list)} sub-tasks.")
    return {
        "design_manifest": manifest,
        "sub_tasks": tasks_list,
        "current_subtask_index": 0,
        "code_snippets": [],
        "critic_feedback": "", # Clear feedback so it doesn't pollute next loops
        "structural_error": False
    }

def sub_agent_node(state: AgenticResearchState) -> Dict[str, Any]:
    idx = state["current_subtask_index"]
    current_task = state["sub_tasks"][idx]
    
    logger.info(f"Sub-Agent [{idx + 1}/{len(state['sub_tasks'])}]: Writing code strictly following manifest...")
    
    user_prompt = f"### MANIFEST ###\n{state.get('design_manifest', '')}\n\n### SUBTASK ###\n{current_task}\n"
    llm_response = call_llm(DEVELOPER_PROMPT, user_prompt)
    
    log_agent_interaction(f"SUB_AGENT_{idx+1}", user_prompt, llm_response)
    clean_snippet = clean_code(llm_response)
    
    current_snippets = state.get("code_snippets", [])
    updated_snippets = current_snippets + [clean_snippet]
    
    return {
        "code_snippets": updated_snippets,
        "current_subtask_index": idx + 1
    }

def integrator_node(state: AgenticResearchState) -> Dict[str, Any]:
    logger.info("Integrator Agent: Merging snippets and applying SOP / Minor Fixes...")
    
    snippets_text = "\n\n--- NEXT SNIPPET ---\n\n".join(state["code_snippets"])
    user_prompt = f"### MANIFEST ###\n{state.get('design_manifest', '')}\n\n### SNIPPETS ###\n{snippets_text}\n"
    
    critic_fb = state.get("critic_feedback", "")
    if critic_fb and not state.get("structural_error", False):
        logger.info("Integrator Agent: Applying minor syntax fixes based on Critic feedback.")
        user_prompt += f"\n\n### CRITIC FEEDBACK ###\n{critic_fb}\n"
    
    llm_response = call_llm(INTEGRATOR_PROMPT, user_prompt)
    log_agent_interaction("INTEGRATOR", user_prompt, llm_response)
    
    clean_final_code = clean_code(llm_response)
    
    return {
        "current_code": clean_final_code,
        "critic_feedback": "" # Clear feedback
    }

def evaluator_node(state: AgenticResearchState) -> Dict[str, Any]:
    logger.info("Evaluator System: Running automated tests in Docker sandbox...")
    
    code = state["current_code"]
    test_cases = state["test_cases"]
    
    result = evaluate_with_docker(code, test_cases, timeout=5)
    
    if result["passed"]:
        logger.info("Evaluator System: PASS - All tests succeeded.")
    else:
        logger.warning("Evaluator System: FAIL - Errors detected in generated code.")
        # Log the exact traceback to the debug file
        logger.debug(f"=== EVALUATOR TRACEBACK ===\n{result['feedback']}\n===========================")
        
    return {
        "passed": result["passed"],
        "feedback": result["feedback"]
    }

def critic_node(state: AgenticResearchState) -> Dict[str, Any]:
    iteration = state['iterations'] + 1
    logger.info(f"Critic Agent: Analyzing failure and determining routing branch (Iteration {iteration}/3)...")
    
    task = state["task_description"]
    code = state["current_code"]
    error = state["feedback"]
    
    user_prompt = f"### ORIGINAL TASK ###\n{task}\n\n### CODE ###\n{code}\n\n### ERROR TRACE ###\n{error}\n\nPlease advise."
    llm_response = call_llm(CRITIC_PROMPT, user_prompt, temperature=0.3)
    
    log_agent_interaction(f"CRITIC_ITER_{iteration}", user_prompt, llm_response)
    
    # Analyze the Critic's tag to set the routing branch
    is_structural = "[MAJOR_STRUCTURAL_ERROR]" in llm_response
    
    if is_structural:
        logger.warning("Critic Agent: MAJOR STRUCTURAL ERROR detected. Routing back to Manager for total re-plan.")
    else:
        logger.info("Critic Agent: MINOR SYNTAX ERROR detected. Routing to Integrator for quick patch.")
    
    return {
        "critic_feedback": llm_response,
        "structural_error": is_structural,
        "iterations": state["iterations"] + 1
    }

# --- Routing Logic ---

def route_sub_tasks(state: AgenticResearchState) -> str:
    if state["current_subtask_index"] < len(state["sub_tasks"]):
        return "continue_coding"
    return "integrate"

def route_evaluation(state: AgenticResearchState) -> str:
    if state["passed"]:
        return "end_success"
    if state["iterations"] >= 3:
        return "end_failure"
    return "critic"

def route_from_critic(state: AgenticResearchState) -> str:
    """LATS-inspired Architectural Branching Logic"""
    if state.get("structural_error", False):
        return "manager"     # Drop the bad plan, generate a new one
    else:
        return "integrator"  # Quick fix without touching the Sub-Agents