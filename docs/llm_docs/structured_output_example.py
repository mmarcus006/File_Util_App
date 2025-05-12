import json
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4o-2024-08-06",
    input=[
        {"role": "system", "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure."},
        {"role": "user", "content": "..."}
    ],
    text={
        "format": {
              "type": "json_schema",
              "name": "research_paper_extraction",
              "schema": {
                "type": "object",
                "properties": {
                    "title": { "type": "string" },
                    "authors": { 
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "abstract": { "type": "string" },
                    "keywords": { 
                        "type": "array", 
                        "items": { "type": "string" }
                    }
                },
                "required": ["title", "authors", "abstract", "keywords"],
                "additionalProperties": False
            },
            "strict": True
        },
    },
)

research_paper = json.loads(response.output_text)