import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def test_groq_usage_metadata():
    """Tests if the Groq API returns token usage metadata."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    print("Sending request to Groq API...")
    
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Tell me a very short joke about programmers."}
        ],
        model="llama-3.1-8b-instant",
        max_tokens=100
    )
    
    print("\n--- Full Usage Object ---")
    print(response.usage)
    
    print("\n--- Specific Token Data ---")
    if response.usage:
        print(f"Prompt (Input) Tokens: {response.usage.prompt_tokens}")
        print(f"Completion (Output) Tokens: {response.usage.completion_tokens}")
        print(f"Total Tokens: {response.usage.total_tokens}")
        print("\nSUCCESS: The usage object exists and contains data.")
    else:
        print("\nWARNING: response.usage is None! A fallback value is required.")

if __name__ == "__main__":
    test_groq_usage_metadata()