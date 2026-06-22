# Agentic Coding Pipeline Benchmark

This project is an experimental framework built with [LangGraph](https://python.langchain.com/docs/langgraph) to evaluate and benchmark the coding capabilities of Large Language Models (LLMs) across different agentic architectures. The pipeline tests how well different multi-agent topologies (from zero-shot single agents to complex adaptive map-reduce architectures) perform on various coding tasks.

## 🏗️ Agent Architectures

The project evaluates three distinct levels of agentic complexity:

1. **Level 1 (Single-Agent):** A zero-shot approach where a single LLM is prompted to solve the entire task in one go.
2. **Level 2 (Multi-Agent Map-Reduce):** A manager agent breaks down the task into sub-tasks. Multiple sub-agents work on these tasks in parallel/sequence, and an integrator agent merges their code into a single script.
3. **Level 3 (Adaptive Multi-Agent with Critic):** Builds upon Level 2 by adding an evaluation and critic loop. If the generated code fails automated tests, a Critic agent analyzes the traceback and provides feedback to the Manager, triggering a re-plan and rewrite (up to a maximum number of iterations).

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Docker:** Required for the secure, sandboxed evaluation of generated code. Ensure Docker Desktop or the Docker daemon is running.
- **Groq API Key:** The project is configured to use Groq's high-speed inference API (specifically `llama3-70b-8192` by default).

### Setup

1. Clone the repository and navigate to the project directory.
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables. Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```
5. Ensure the Docker image required for evaluation is available:
   ```bash
   docker pull python:3.10-alpine
   ```

## 🎮 Usage

To run the experimental matrix, simply execute the main script:

```bash
python main.py
```

This will run all configured architectures against the tasks defined in `data/tasks.json`.

### Output

- **`logs/agent_pipeline.log`**: Detailed logs of agent interactions, rate limiting, and evaluator tracebacks.
- **`data/experiment_results.csv`**: A CSV file summarizing the success/failure, runtime, and critic iterations for each run.

## 📂 Project Structure

```text
project/
├── main.py                     # Entry point for the experimental matrix
├── evaluate.py                 # Script copied into the Docker container for secure testing
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
├── data/
│   ├── tasks.json              # Benchmark tasks (Sequential/Modular, Easy/Hard)
│   └── experiment_results.csv  # Output results from main.py
├── logs/
│   └── agent_pipeline.log      # Detailed pipeline execution logs
└── src/
    ├── graph.py                # LangGraph network topologies (Level 1, 2, 3)
    ├── nodes.py                # Logic for individual agents (Manager, Sub-Agent, Integrator, Critic)
    ├── state.py                # TypedDict defining the graph's shared state
    ├── prompts.py              # System prompts for all agents
    ├── llm_client.py           # Groq API client with sliding-window rate limiting
    └── logger.py               # Centralized logging configuration
```

## 📊 Preliminary Findings

Based on initial benchmarks using this framework:
- **Zero-Shot (Level 1)** performs surprisingly well for well-defined tasks that fit comfortably within the context window.
- **Map-Reduce (Level 2/3)** struggles heavily with highly sequential, tightly-coupled code due to context isolation between sub-agents. However, it shows promise when tasks are modular and independent. API rate limiting is a significant factor in multi-agent runtime overhead.

## 🛡️ Secure Evaluation

All generated code is evaluated inside an ephemeral, network-isolated Docker container (`python:3.10-alpine`). Memory limits, CPU constraints, and timeouts are enforced to prevent malicious code execution or infinite loops from crashing the host machine.
