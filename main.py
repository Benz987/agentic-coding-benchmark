"""Automated Experiment Runner for Agentic Architecture Research."""

import json
import csv
import os
import time
from src.graph import build_level_1_graph, build_level_2_graph, build_level_3_graph
from src.logger import logger

def run_experiments():

    # 1. Ensure setup is correct
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY is not set. Exiting.")
        return

    os.makedirs("data", exist_ok=True)
    results_file = "data/experiment_results.csv"
    
    with open("data/tasks.json", "r", encoding="utf-8") as f:
        all_tasks = json.load(f)

    tasks = []
    # Uncomment the tasks you want to run:
    # tasks.extend([t for t in all_tasks if t["domain"] == "Domain 1: Sequential" and t["difficulty"] == "Easy"])
    # tasks.extend([t for t in all_tasks if t["domain"] == "Domain 1: Sequential" and t["difficulty"] == "Hard"])
    tasks.extend([t for t in all_tasks if t["domain"] == "Domain 1: Sequential" and t["difficulty"] == "Extreme"])
    
    # tasks.extend([t for t in all_tasks if t["domain"] == "Domain 2: Modular" and t["difficulty"] == "Easy"])
    # tasks.extend([t for t in all_tasks if t["domain"] == "Domain 2: Modular" and t["difficulty"] == "Hard"])
    tasks.extend([t for t in all_tasks if t["domain"] == "Domain 2: Modular" and t["difficulty"] == "Extreme"])

    # 2. Define the architectures to test
    architectures = [
        ("Level 1 (Single-Agent)", build_level_1_graph()),
        ("Level 2 (Multi-Agent)", build_level_2_graph()),
        ("Level 3 (Adaptive Multi-Agent)", build_level_3_graph())
    ]
    
    runs_per_condition = 3
    
    # 3. Prepare CSV File
    file_exists = os.path.isfile(results_file)
    with open(results_file, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Architecture", "Domain", "Difficulty", "Run_ID", "Passed", "Runtime_Seconds", "Critic_Iterations", "SubTasks_Generated"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        # 4. Execute the Matrix
        logger.info("=== STARTING EXPERIMENTAL MATRIX ===")
        
        for arch_name, graph_app in architectures:
            for task in tasks:
                for run_id in range(1, runs_per_condition + 1):
                    
                    logger.info(f"\n--- Testing: {arch_name} | {task['domain']} ({task['difficulty']}) | Run {run_id}/3 ---")
                    
                    # Reset the state for each run
                    initial_state = {
                        "task_description": task["task_description"],
                        "difficulty": task["difficulty"],
                        "test_cases": task["test_cases"],
                        "sub_tasks": [],
                        "current_subtask_index": 0,
                        "code_snippets": [],
                        "current_code": "",
                        "feedback": "",
                        "passed": False,
                        "iterations": 0
                    }
                    
                    # Measure runtime
                    start_time = time.time()
                    final_state = graph_app.invoke(initial_state)
                    end_time = time.time()
                    
                    runtime = round(end_time - start_time, 2)
                    
                    # Log the metrics
                    writer.writerow({
                        "Architecture": arch_name,
                        "Domain": task["domain"],
                        "Difficulty": task["difficulty"],
                        "Run_ID": run_id,
                        "Passed": final_state["passed"],
                        "Runtime_Seconds": runtime,
                        "Critic_Iterations": final_state["iterations"],
                        "SubTasks_Generated": len(final_state["sub_tasks"])
                    })
                    
                    # Flush to CSV immediately so data isn't lost if the script crashes
                    csvfile.flush() 

    logger.info("\n=== EXPERIMENTS COMPLETE ===")
    logger.info(f"Results saved to {results_file}. You can now analyze the data!")

if __name__ == "__main__":
    run_experiments()