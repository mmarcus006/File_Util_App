from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types # Import types for configuration
import os
from PyPDF2 import PdfReader, PdfWriter

api_key = os.environ.get("GEMINI_API_KEY2") # If you are not using Colab you can set the API key directly

# Create a client
client = genai.Client(api_key=api_key)

# Define the model you are going to use
model_id =  "gemini-2.5-flash-preview-04-17"
# or "gemini-2.0-flash-lite"  , "gemini-2.5-flash-preview-04-17","gemini-2.5-pro-exp-03-25"

def combine_pdfs(pdf_path1, pdf_path2, output_path):
  """Combines two PDF files into a single PDF.

  Args:
    pdf_path1: Path to the first PDF file.
    pdf_path2: Path to the second PDF file.
    output_path: Path to save the combined PDF.
  """
  
  pdf1_reader = PdfReader(pdf_path1)
  pdf2_reader = PdfReader(pdf_path2)
  pdf_writer = PdfWriter()

  # Add pages from the first PDF
  for page in pdf1_reader.pages:
    pdf_writer.add_page(page)

  # Add pages from the second PDF
  for page in pdf2_reader.pages:
    pdf_writer.add_page(page)

  # Write the combined PDF to the output path
  with open(output_path, 'wb') as output_file:
    pdf_writer.write(output_file)

  print(f"Combined PDF saved to: {output_path}")

def extract_structured_data_api(file_path: str, model: BaseModel, system_prompt: str, user_prompt: str):
    # Upload the file to the File API
    file = client.files.upload(file=file_path, config={'display_name': file_path.split('/')[-1].split('.')[0]})
    
    # Define the generation configuration with thinking budget and system instruction
    generation_config = types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=model,
        thinking_config=types.ThinkingConfig(thinking_budget=6000),
        system_instruction=system_prompt # Add system instruction here
    )
    
    # Generate a structured response using the Gemini API
    # Use the provided user_prompt and the uploaded file as content
    response = client.models.generate_content(
        model=model_id, 
        contents=[user_prompt, file], # Use user_prompt and file
        config=generation_config # Use the updated config object with the correct parameter name
    )
    # Convert the response to the pydantic model and return it
    return response.parsed

def save_structured_data_to_json(data: BaseModel, output_dir: str, filename: str):
    """Saves structured data to a JSON file in the specified output directory.

    Args:
        data: The structured data as a Pydantic model.
        output_dir: Directory path where the JSON file will be saved.
        filename: Name of the JSON file to create.
    """
    import json
    import os
    from pathlib import Path

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the full output path
    output_path = Path(output_dir) / filename
    
    # Convert the Pydantic model to a dictionary and then to JSON
    json_data = data.model_dump(exclude_none=True)
    
    # Write the JSON data to the file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Structured data saved to: {output_path}")

