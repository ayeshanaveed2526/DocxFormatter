import os
import sys
from document_processor import process_document
from dotenv import load_dotenv

load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("=========================================")
        print("Usage: python run_format.py <path_to_docx>")
        print("Example: python run_format.py my_document.docx")
        print("=========================================")
        sys.exit(1)
        
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
        
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY").startswith("your_"):
        print("\n[WARNING] You haven't set a real GEMINI_API_KEY in the .env file!")
        print("The script needs this key to intelligently parse your document and instructions.")
        print("Please update backend/.env before running.\n")
        
    output_file = "formatted_" + os.path.basename(input_file)
    
    print("\n=========================================")
    print("Enter any specific formatting instructions.")
    print("Example: 'set font size to 14, headings to 16, make subheadings bold'")
    print("Or just press Enter to use default rules.")
    print("=========================================")
    instructions = input("Instructions: ")
    
    print(f"\nProcessing '{input_file}'... This may take a minute depending on length.")
    try:
        process_document(input_file, output_file, instructions)
        print(f"\n✅ Success! Formatted document saved as '{output_file}' in the current folder.")
    except Exception as e:
        print(f"\n❌ An error occurred while processing: {e}")

if __name__ == "__main__":
    main()
