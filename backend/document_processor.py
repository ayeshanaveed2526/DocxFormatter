import os
from docx import Document
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client with key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_text_with_ai(text):
    """
    Sends text to the AI Layer for formatting based on rules.
    """
    if not text.strip():
        return text
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent document formatting assistant designed to improve "
                        "and standardize Microsoft Word (.docx) documents. Return ONLY the improved text. "
                        "Do NOT include explanations. Do NOT include markdown or formatting symbols. "
                        "Do NOT change technical meaning."
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        # On error, fallback to original text so document processing doesn't halt
        return text 

def process_document(input_path, output_path):
    """
    The Rule Engine layer using python-docx to read and write the document.
    """
    doc = Document(input_path)
    
    # Process each paragraph
    for para in doc.paragraphs:
        if para.text.strip():
            # Send text to AI Layer
            improved_text = format_text_with_ai(para.text)
            para.text = improved_text
            
    # Save formatted document
    doc.save(output_path)
