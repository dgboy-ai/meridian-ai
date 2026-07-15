import os
from groq import Groq

api_key = os.environ.get("GROQ_API_KEY", "")
c = Groq(api_key=api_key)

for model in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "qwen/qwen3-32b"]:
    print(f"\n--- Testing {model} ---")
    try:
        r = c.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": 'Return JSON: {"finding": "test", "confidence": 0.9}'}],
        )
        content = r.choices[0].message.content
        print(f"Response: {repr(content[:200])}")
    except Exception as e:
        print(f"Error: {e}")
