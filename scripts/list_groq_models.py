import os
from groq import Groq

api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key:
    print("No API key")
    exit(1)

c = Groq(api_key=api_key)
models = c.models.list()
for m in models.data:
    print(f"{m.id}  context={getattr(m, 'context_window', '?')}")
