import json
import re
import os

terminal_output = """
⏰ 06:30:00  🪟   🖥️MillersComp  C:/Projects/File_Util_App  via 🐍 .venv  ❯ & & c:/Projects/File_Util_App/.venv/Scripts/python.exe c:/Projects/File_Util_App/src/db/process_pdf_layouts.py   
Processing PDF: C:/Users/mille/MinerU/Temp_Walls_Franchise_Management_LLC_FDD_2024_ID636619.pdf-ee149ddc-6288-4523-8786-6c0a3cc49f0b/554d7a03-5043-41c0-8fa5-d1efa661e975_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Temp_Walls_Franchise_Management_LLC_FDD_2024_ID636619.pdf-ee149ddc-6288-4523-8786-6c0a3cc49f0b/554d7a03-5043-41c0-8fa5-d1efa661e975_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/554d7a03-5043-41c0-8fa5-d1efa661e975_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/Citadel_Panda_Express_Inc_FDD_2024_ID636111.pdf-84eb9487-72f7-4c49-a467-850b30272de8/d2df182c-e586-437e-b750-edbebd27959f_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Citadel_Panda_Express_Inc_FDD_2024_ID636111.pdf-84eb9487-72f7-4c49-a467-850b30272de8/d2df182c-e586-437e-b750-edbebd27959f_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/d2df182c-e586-437e-b750-edbebd27959f_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/Valenta_Franchise_LLC_FDD_2024_ID635410.pdf-6b334bc0-c7b1-4641-b6f4-c290c93bb253/d577664d-e266-449a-9af5-1d74d501be49_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Valenta_Franchise_LLC_FDD_2024_ID635410.pdf-6b334bc0-c7b1-4641-b6f4-c290c93bb253/d577664d-e266-449a-9af5-1d74d501be49_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/d577664d-e266-449a-9af5-1d74d501be49_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/House_of_Colour_USA_Inc_FDD_2024_ID637177.pdf-32f886b5-522a-42f8-945e-ddf65b87bdd2/d89f3719-1d18-4c5d-bf48-dd9274e0dc60_origin.pdf
Using WSL path: C:/Users/mille/MinerU/House_of_Colour_USA_Inc_FDD_2024_ID637177.pdf-32f886b5-522a-42f8-945e-ddf65b87bdd2/d89f3719-1d18-4c5d-bf48-dd9274e0dc60_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/d89f3719-1d18-4c5d-bf48-dd9274e0dc60_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/SureStay_Inc_FDD_2024_ID635407.pdf-d1ccc2d9-8d78-4c82-ac99-eb54dd2a94f9/851f26f4-e4ab-40bc-be4e-83c5fbac14c4_origin.pdf
Using WSL path: C:/Users/mille/MinerU/SureStay_Inc_FDD_2024_ID635407.pdf-d1ccc2d9-8d78-4c82-ac99-eb54dd2a94f9/851f26f4-e4ab-40bc-be4e-83c5fbac14c4_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/851f26f4-e4ab-40bc-be4e-83c5fbac14c4_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/Little_Kitchen_Academy_USA_Inc_FDD_2024_ID636051.pdf-8a72c057-eac6-47a8-830d-c7b4177d4f8c/e208d27e-95cf-4859-9449-3e3bac0633bf_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Little_Kitchen_Academy_USA_Inc_FDD_2024_ID636051.pdf-8a72c057-eac6-47a8-830d-c7b4177d4f8c/e208d27e-95cf-4859-9449-3e3bac0633bf_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/e208d27e-95cf-4859-9449-3e3bac0633bf_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/Captain_Ds_LLC_FDD_2024_ID636454.pdf-34f79f53-047d-4485-a8da-fdc971216057/fb2b69bf-71fd-4a22-bc41-6cd7bfd3ba97_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Captain_Ds_LLC_FDD_2024_ID636454.pdf-34f79f53-047d-4485-a8da-fdc971216057/fb2b69bf-71fd-4a22-bc41-6cd7bfd3ba97_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/fb2b69bf-71fd-4a22-bc41-6cd7bfd3ba97_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/Hole_in_the_Wall_Franchising_LLC_FDD_2024_ID637417.pdf-7c8fea70-c1e8-4a42-82f7-6d61f3a85b7d/5e2ab610-d23e-4dcb-97b8-03de2b10fd1f_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Hole_in_the_Wall_Franchising_LLC_FDD_2024_ID637417.pdf-7c8fea70-c1e8-4a42-82f7-6d61f3a85b7d/5e2ab610-d23e-4dcb-97b8-03de2b10fd1f_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/5e2ab610-d23e-4dcb-97b8-03de2b10fd1f_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/Sola_Franchise_LLC_FDD_2024_ID636547.pdf-5365078e-9a00-4bb4-931c-3fbe5b9ec1fc/508b71e6-3663-4877-94bc-64f4a5fd6bff_origin.pdf
Using WSL path: C:/Users/mille/MinerU/Sola_Franchise_LLC_FDD_2024_ID636547.pdf-5365078e-9a00-4bb4-931c-3fbe5b9ec1fc/508b71e6-3663-4877-94bc-64f4a5fd6bff_origin.pdf
Analysis results saved to: c:/Projects/File_Util_App/data/huridoc_analysis_output/508b71e6-3663-4877-94bc-64f4a5fd6bff_origin_huridocs_analysis.json
Processing PDF: C:/Users/mille/MinerU/LP_Franchising_LLC_FDD_2024_ID636328.pdf-7f799eeb-2439-4699-9f52-559fb6465cb4/0a493c8e-eea4-4ff0-adba-f6bb48821426_origin.pdf
Using WSL path: C:/Users/mille/MinerU/LP_Franchising_LLC_FDD_2024_ID636328.pdf-7f799eeb-2439-4699-9f52-559fb6465cb4/0a493c8e-eea4-4ff0-adba-f6bb48821426_origin.pdf
"""

processed_files = set()
pattern = r"Analysis results saved to: (.*)"

for line in terminal_output.strip().split('/n'):
    match = re.search(pattern, line)
    if match:
        # Normalize path separators for consistency
        file_path = os.path.normpath(match.group(1).strip())
        processed_files.add(file_path)

# Define the path for the tracking file relative to the script
script_dir = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
tracking_file_path = os.path.join(script_dir, "processed_files_tracking.json")

# Save the initial set to the tracking file
with open(tracking_file_path, "w") as f:
    json.dump(list(processed_files), f, indent=2)

print(f"Created tracking file: {tracking_file_path}")
print(f"Found {len(processed_files)} completed files.")
