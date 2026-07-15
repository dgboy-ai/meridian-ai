import os
from groq import Groq

api_key = os.environ.get("GROQ_API_KEY", "")
print(f"API key present: {bool(api_key)}")
print(f"API key length: {len(api_key)}")

if api_key:
    c = Groq(api_key=api_key)
    r = c.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": 'Say hello in JSON format: {"msg": "..."}'}],
    )
    print(f"Response: {repr(r.choices[0].message.content)}")
else:
    print("No API key set")
