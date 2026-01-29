import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print("--- START MODEL LIST (google-genai SDK) ---")
try:
    client = genai.Client(api_key=api_key)
    # List models with V2 SDK
    # Note: iterating directly might differ, we check documentation pattern
    for m in client.models.list():
        # Filter for recent ones manually or print all
        name = m.name
        if "flash" in name or "pro" in name:
            print(name)
except Exception as e:
    print(f"Error: {e}")
print("--- END MODEL LIST ---")
