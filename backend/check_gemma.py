
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from backend/.env")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="models/gemma-4-26b-a4b-it",
    contents=(
        "You are SurgiPlan Copilot, an assistant for operating room "
        "scheduling. Reply in one sentence confirming you are ready. "
        "Do not make medical decisions."
    ),
)

print("\nGemma response:")
print(response.text)
