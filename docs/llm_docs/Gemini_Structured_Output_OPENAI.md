"""## Structured outputs

Gemini API allows you to format the way your response you be generated via [structured outputs](https://ai.google.dev/gemini-api/docs/structured-output). You can define the structure you want to be used as a defined schema and, using the OpenAI library, you send this structure as the `response_format` parameter.

In this example you will:
- download a scientific paper
- extract its information
- define the structure you want your response in
- send your request using the `response_format` parameter

First you need to download the reference paper. You will use the [Attention is all your need](https://arxiv.org/pdf/1706.03762.pdf) Google paper that introduced the [Transformers architecture](https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)).
"""

from IPython.display import Image
from pdf2image import convert_from_path


# download the PDF file
pdf_url = "https://arxiv.org/pdf/1706.03762.pdf" # @param
pdf_filename = pdf_url.split("/")[-1]
!wget -q $pdf_url

## visualize the pdf as an image
# convert the PDF file to images
images = convert_from_path(pdf_filename, 200)
for image in images:
  image.save('cover.png', "PNG")
  break

# show the pdf first page
Image('cover.png', width=500, height=600)

"""Now you will create your reference structure. It will be a Python `Class` that will refer to the title, authors, abstract and keywords from the paper."""

from pydantic import BaseModel


class ResearchPaperExtraction(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]

"""Now you will do your request to the Gemini API sending the pdf file and the reference structure."""

import json
from pdfminer.high_level import extract_text


# extract text from the PDF
pdf_text = extract_text(pdf_filename)

prompt = """
"As a specialist in knowledge organization and data refinement, your task is to transform
raw research paper content into a clearly defined structured format. I will provide you
with the original, free-form text. Your goal is to parse this text, extract the pertinent
information, and reconstruct it according to the structure outlined below.
"""

# send your request to the Gemini API
completion = client.beta.chat.completions.parse(
  model=MODEL,
  messages=[
    {"role": "system", "content": prompt},
    {"role": "user", "content": pdf_text}
  ],
  response_format=ResearchPaperExtraction,
)

print(completion.choices[0].message.parsed.model_dump_json(indent=2))

"""Given the Gemini API ability to handle structured outputs, you can work in more complex scenarios too - like using the structured output functionality to help you generating user interfaces.

First you define the Python classes that represent the structure you want in the output.
"""

from enum import Enum


class UIType(str, Enum):
    div = "div"
    button = "button"
    header = "header"
    section = "section"
    field = "field"
    form = "form"

class Attribute(BaseModel):
    name: str
    value: str

class UI(BaseModel):
    type: UIType
    label: str
    children: list[str]
    attributes: list[Attribute]

UI.model_rebuild() # This is required to enable recursive types

class Response(BaseModel):
    ui: UI

"""Now you send your request using the `Response` class as the `response_format`."""

completion = client.beta.chat.completions.parse(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a UI generation assistant. Convert the user input into a UI."},
        {"role": "user", "content": "Make a User Profile Form including all required attributes"}
    ],
    response_format=Response,
)

print(completion.choices[0].message.content)