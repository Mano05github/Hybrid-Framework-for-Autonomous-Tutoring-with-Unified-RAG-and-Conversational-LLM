import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {bool(api_key)}")

genai.configure(api_key=api_key)

# Try the specific model we chose
model_name = 'gemini-2.0-flash-exp'
print(f"Testing generation with {model_name}...")

try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello, can you hear me?")
    print("SUCCESS!")
    print(response.text)
except Exception as e:
    print(f"FAILED with {model_name}: {e}")
    
    # Fallback test
    print("\nAttempting fallback to 'gemini-pro'...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello?")
        print("SUCCESS with gemini-pro!")
        print(response.text)
    except Exception as e2:
        print(f"FAILED with gemini-pro: {e2}")

