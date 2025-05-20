import os
from openai import OpenAI
import instructor
import base64
from pydantic import BaseModel, Field

# Define output structure
class Franchise(BaseModel):
    franchise_name: str = Field(description="The brand nameof the franchise as listed on page 1 of the FDD, this is the name consumers would know the franchise as (ex. Mcdonalds Corporation should be Mcdonalds).")
    franchise_address: str = Field(description="The complete business address of the franchisor headquarters from page 1 of the FDD")
    franchise_parent_company: str = Field(description="The name of the parent company or corporation that owns the franchise, typically found on page 1")
    franchise_phone: str = Field(description="The primary contact phone number for the franchisor listed on page 1 of the FDD")
    franchise_email: str = Field(description="The primary contact email address for the franchisor found on page 1")
    franchise_website: str = Field(description="The official website URL of the franchise as mentioned on page 1 of the FDD")
    

def main():
    # Configure client
    client = instructor.from_openai(
        OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPEN_ROUTER_API_KEY")),
        mode=instructor.Mode.OPENROUTER_STRUCTURED_OUTPUTS
    )
    
    # Encode PDF
    with open("/Users/miller/Library/CloudStorage/OneDrive-Personal/FDD_PDFS/File_Util_App/output/split_pdfs/0a6a4155-b831-4d28-a7bf-f7eb1da5d2ad/intro.pdf", "rb") as f:
        pdf_data = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode()}"
    
    # Process document
    result = client.chat.completions.create(
        model="meta-llama/llama-4-maverick:free",
        messages=[{
            "role": "user",
            "content": [
                {"type": "file", "file": {"filename": "intro.pdf", "file_data": pdf_data}},
                {"type": "text", "text": 
    f"""extract the following data points from this franchise disclosure document and return the text in json format only. do not return any other text besides the json object formatted like this:
    
    here are the data points:
    franchise_name: str = Field(description="The brand name of the franchise, meaning what a consumer would call the business. (ex. Mcdonald's Corporation should be McDonalds)")
    franchise_address: str = Field(description="The complete business address of the franchisor headquarters from page 1 of the FDD")
    franchise_parent_company: str = Field(description="The name of the parent company or corporation that owns the franchise, typically found on page 1")
    franchise_phone: str = Field(description="The primary contact phone number for the franchisor listed on page 1 of the FDD")
    franchise_email: str = Field(description="The primary contact email address for the franchisor found on page 1")
    franchise_website: str = Field(description="The official website URL of the franchise as mentioned on page 1 of the FDD")
    
    Here are some examples of what the output should be:
    
    #Example 1:
    {
    "franchise_name": "Gold's Gym",
    "franchise_address": "5420 Lyndon B. Johnson Freeway, Suite 300, Dallas, Texas 75240",
    "franchise_parent_company": "Gold's Gym Franchise LLC",
    "franchise_phone": "(214) 574-4653",
    "franchise_email": "franchise@goldsgym.com",
    "franchise_website": "www.goldsgym.com"
    }
    
    #Example 2:
    {
    "franchise_name": "Lawn Doctor",
    "franchise_address": "142 State Route 34, Holmdel, New Jersey 07733",
    "franchise_parent_company": "Lawn Doctor, Inc.",
    "franchise_phone": "(732) 946-4300",
    "franchise_email": "franchiseinformation@lawndoctor.com",
    "franchise_website": "www.lawndoctor.com"
    }"""}
            ]
        }],
        response_model=Franchise,
        extra_body={"provider": {"require_parameters": True}}
    )
    
    print(result)

if __name__ == "__main__":
    main()
