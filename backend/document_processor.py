import os
import json
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv

load_dotenv()

# Configure Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-lite')

def extract_formatting_rules(instructions):
    """
    Uses Gemini to extract a JSON configuration of the formatting rules based on the user's instructions.
    """
    default_rules = {
        "heading": {"size": 16, "bold": True},
        "subheading": {"size": 14, "bold": True},
        "paragraph": {"size": 12, "bold": False}
    }
    
    if not instructions.strip():
        return default_rules
        
    try:
        prompt = (
            "You are a rule extraction engine. The user will give you instructions on how to format a document. "
            "You must extract their requirements and output a JSON object exactly matching this structure, "
            "modifying the values based on the user's instructions:\n"
            "{\n"
            "  \"heading\": {\"size\": 16, \"bold\": true},\n"
            "  \"subheading\": {\"size\": 14, \"bold\": true},\n"
            "  \"paragraph\": {\"size\": 12, \"bold\": false}\n"
            "}\n"
            "If a size is not specified, use 16 for heading, 14 for subheading, and 12 for paragraph. "
            "If the user specifies subheading must be bold, make sure bold is true.\n\n"
            f"User instructions: {instructions}\n\n"
            "Output ONLY valid JSON. Do not include markdown code blocks like ```json."
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```json'):
            text = text.replace('```json', '', 1)
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
            
        extracted = json.loads(text)
        # Merge with defaults just in case
        for k in default_rules:
            if k in extracted:
                default_rules[k].update(extracted[k])
        return default_rules
    except Exception as e:
        print(f"Rule extraction error: {e}")
        if "429" in str(e) or "quota" in str(e).lower() or "404" in str(e):
            raise Exception(f"Gemini API Error: {e}")
        return default_rules

def process_text_batch(texts, instructions):
    """
    Sends a batch of text to Gemini to classify type and improve grammar.
    """
    if not texts:
        return []
        
    # Prepare JSON array for input
    input_json = {str(i): text for i, text in enumerate(texts)}
    
    try:
        prompt = (
            "You are an intelligent document formatter.\n"
            "You will receive a JSON dictionary mapping an index to a text snippet.\n"
            "For each text snippet:\n"
            "1. Improve the grammar and professionalism without changing meaning.\n"
            "2. Determine if it's a 'heading', 'subheading', or 'paragraph' based on its context.\n"
            "3. Return a JSON object mapping the same index to {\"type\": \"...\", \"text\": \"...\"}.\n"
            "Do not change the index keys.\n\n"
            f"Input JSON: {json.dumps(input_json)}\n\n"
            "Output ONLY valid JSON. Do not include markdown code blocks like ```json."
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```json'):
            text = text.replace('```json', '', 1)
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
            
        result_json = json.loads(text)
        
        # Reconstruct list in order
        output = []
        for i in range(len(texts)):
            item = result_json.get(str(i), {"type": "paragraph", "text": texts[i]})
            output.append(item)
        return output
    except Exception as e:
        print(f"Batch processing error: {e}")
        if "429" in str(e) or "quota" in str(e).lower() or "404" in str(e):
            raise Exception(f"Gemini API Error: {e}")
        return [{"type": "paragraph", "text": t} for t in texts]

def process_document(input_path, output_path, instructions):
    doc = Document(input_path)
    
    # 1. Extract rules from chatbot prompt
    rules = extract_formatting_rules(instructions)
    print("Applying rules:", rules)
    
    # 2. Extract non-empty paragraphs
    paragraphs_to_process = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs_to_process.append(para)
            
    if not paragraphs_to_process:
        doc.save(output_path)
        return

    # 3. Process in batches to save time (e.g., 10 at a time)
    batch_size = 10
    processed_data = []
    
    texts = [p.text for p in paragraphs_to_process]
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        processed_data.extend(process_text_batch(batch, instructions))
        
    # 4. Apply styles back to document
    for para, data in zip(paragraphs_to_process, processed_data):
        ptype = data.get("type", "paragraph")
        improved_text = data.get("text", para.text)
        
        # Clear existing text
        para.clear()
        
        # Apply style based on extracted rules
        run = para.add_run(improved_text)
        
        style_rule = rules.get(ptype, rules["paragraph"])
        
        # Set Font Size
        if "size" in style_rule and style_rule["size"]:
            run.font.size = Pt(int(style_rule["size"]))
            
        # Set Bold
        if "bold" in style_rule:
            run.bold = bool(style_rule["bold"])
            
    doc.save(output_path)
