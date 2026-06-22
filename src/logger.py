"""Logging configuration for the Agentic Research Project."""

import logging
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create a custom logger
logger = logging.getLogger("AgenticPipeline")
logger.setLevel(logging.DEBUG) # Set to DEBUG to capture detailed inputs/outputs

# Create handlers
file_handler = logging.FileHandler("logs/agent_pipeline.log", mode="a", encoding="utf-8")
console_handler = logging.StreamHandler()

# Set levels for handlers
file_handler.setLevel(logging.DEBUG) # File gets everything (exact prompts, raw responses)
console_handler.setLevel(logging.INFO) # Console gets clean pipeline flow (hides massive prompts)

# Create formatters and add them to handlers
file_format = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')
console_format = logging.Formatter('[%(levelname)s] %(message)s')

file_handler.setFormatter(file_format)
console_handler.setFormatter(console_format)

# Add handlers to the logger
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def log_agent_interaction(agent_name: str, input_prompt: str, output_response: str):
    """Helper to consistently log exact inputs and outputs to the file."""
    logger.debug(f"=== {agent_name} INPUT ===\n{input_prompt}\n======================")
    logger.debug(f"=== {agent_name} OUTPUT ===\n{output_response}\n======================\n")