import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from document_processor import extract_formatting_rules, process_text_batch

load_dotenv()
print("Using GEMINI API KEY:", "SET" if os.getenv("GEMINI_API_KEY") else "NOT SET")

instructions = "font size 14, headings 16, subheadings bold"
print("\n--- Extracting Rules ---")
try:
    rules = extract_formatting_rules(instructions)
    print("Rules:", json.dumps(rules, indent=2))
except Exception as e:
    print("Error:", e)

texts = ["This is a test heading", "This is a normal paragraph to see what it does."]
print("\n--- Processing Batch ---")
try:
    res = process_text_batch(texts, instructions)
    print("Batch Result:", json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
