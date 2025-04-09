from pathlib import Path
from typing import Union
from markdownify import markdownify as md


def convert_html_to_md(
    html_file_path: Union[str, Path], md_file_path: Union[str, Path]
) -> None:
    """Reads an HTML file, converts its content to Markdown, and saves it.

    Args:
        html_file_path: Path to the input HTML file.
        md_file_path: Path where the output Markdown file will be saved.
    """
    html_file = Path(html_file_path)
    md_file = Path(md_file_path)

    # Ensure the input file exists
    if not html_file.is_file():
        print(f"Error: Input HTML file not found at {html_file}")
        return

    # Read HTML content
    try:
        html_content: str = html_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading HTML file {html_file}: {e}")
        return

    # Convert HTML to Markdown
    try:
        markdown_content: str = md(html_content)
    except Exception as e:
        print(f"Error converting HTML to Markdown: {e}")
        return

    # Write Markdown content to the output file
    try:
        md_file.write_text(markdown_content, encoding="utf-8")
        print(f"Successfully converted {html_file.name} to {md_file.name}")
    except Exception as e:
        print(f"Error writing Markdown file {md_file}: {e}")


if __name__ == "__main__":
    # Define the input and output file names
    input_html_file: str = r"C:\Users\mille\Downloads\Chapter 4： Classifying Texts ｜ Python Natural Language Processing Cookbook - Second Edition (4_7_2025 10：44：58 PM).html"
    output_md_file: str = "output/html.md"

    # Get the directory of the current script
    script_dir: Path = Path(__file__).parent.resolve()

    # Construct full paths
    full_html_path: Path = script_dir / input_html_file
    full_md_path: Path = script_dir / output_md_file

    # Perform the conversion
    convert_html_to_md(full_html_path, full_md_path)
