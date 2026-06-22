import os
import json
import re
import time
from collections import deque
from typing import List
from groq import Groq
from dotenv import load_dotenv

from src.logger import logger

load_dotenv()

# --- Smart Rate Limiter ---

class RateLimiter:
    """A sliding-window rate limiter for API calls based on RPM and TPM limits."""
    
    def __init__(self, max_rpm: int = 30, max_tpm: int = 6000):
        self.max_rpm = max_rpm
        self.max_tpm = max_tpm
        self.requests = deque() # Stores tuples of (timestamp, total_tokens_used)
        
    def wait_if_needed(self, estimated_tokens: int = 1500):
        """Blocks execution if the next request would exceed the rolling 60-second limit."""
        current_time = time.time()
        
        # Remove requests older than 60 seconds
        while self.requests and current_time - self.requests[0][0] > 60:
            self.requests.popleft()
            
        current_rpm = len(self.requests)
        current_tpm = sum(req[1] for req in self.requests)
        
        # If adding the estimated tokens or 1 request exceeds limits, we must sleep
        if current_rpm >= self.max_rpm or (current_tpm + estimated_tokens) > self.max_tpm:
            if self.requests:
                # Calculate exactly how many seconds until the oldest request expires
                oldest_timestamp = self.requests[0][0]
                sleep_duration = 60.0 - (current_time - oldest_timestamp) + 1.0 # 1s buffer
                
                if sleep_duration > 0:
                    logger.info(f"Rate Limiter: Cooling down for {sleep_duration:.1f}s (Current TPM: {current_tpm})...")
                    time.sleep(sleep_duration)
                    
                # Recursively check again after waking up
                self.wait_if_needed(estimated_tokens)
                
    def record_usage(self, actual_tokens: int):
        """Records the exact token usage after a successful API call."""
        self.requests.append((time.time(), actual_tokens))

# Initialize a global limiter instance based on the Free Plan limits
api_limiter = RateLimiter(max_rpm=30, max_tpm=6000)

# --- LLM Client ---

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """Isolated function to handle LLM API calls with proactive rate limiting."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # 1. Proactively wait to stay within the 6000 TPM limit
    api_limiter.wait_if_needed(estimated_tokens=1500)
    
    # 2. Fallback exponential backoff for unexpected server errors (500s or network drops)
    max_retries = 3
    wait_time = 5 
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=temperature,
                max_tokens=2048,
            )
            
            # 3. Post-generation: Record the exact tokens used
            total_tokens = response.usage.total_tokens if response.usage else 1500
            api_limiter.record_usage(total_tokens)
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            error_message = str(e).lower()
            if "429" in error_message or "rate limit" in error_message:
                logger.warning(f"Unexpected API Rate Limit hit. Forcing sleep for {wait_time}s...")
                time.sleep(wait_time)
                wait_time *= 2
            else:
                logger.error(f"Critical LLM API Error: {str(e)}")
                return f"LLM_ERROR: {str(e)}"
                
    logger.error("Max retries exceeded for LLM API.")
    return "LLM_ERROR: Max Retries Exceeded"

def extract_json_from_llm(response_text: str) -> List[str]:
    """Robust helper to extract a JSON list from the LLM output."""
    try:
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            return json.loads(response_text[start_idx:end_idx])
        return [response_text] # Fallback to single-agent approach if parsing fails
    except json.JSONDecodeError:
        return [response_text]

def clean_code(llm_output: str) -> str:
    """Extracts raw Python code from markdown blocks."""
    match = re.search(r'```python\n(.*?)\n```', llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_output.strip()