#!/usr/bin/env python3
"""
filemap.py - Creates a markdown representation of a file/folder structure.
"""
from pathlib import Path

def should_exclude(path):
    """
    Determine if a file or directory should be excluded based on common .gitignore patterns.
    Returns True if the path should be excluded, False otherwise.
    """
    # Common patterns to exclude (similar to .gitignore for Python projects)
    exclude_patterns = [
        '__pycache__',
        '.git',
        '.DS_Store',
        '.idea', '.vscode',
        '.egg-info',
        'dist', 'build',
        '.venv', 'venv',
        '.pytest_cache',
        '.coverage',
        'htmlcov',
        '.tox',
    ]
    
    # File extensions to exclude
    exclude_extensions = ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe']
    
    path_str = str(path)
    
    # Special case: always include __init__.py files
    if path.name == '__init__.py':
        return False
    
    # Check file extension
    if path.is_file() and path.suffix in exclude_extensions:
        return True
    
    # Check if any pattern is in the path
    for pattern in exclude_patterns:
        if pattern in path_str:
            return True
    
    return False


def sort_items(item):
    """
    Sort function to sort directories before files and then alphabetically.
    """
    return (not item.is_dir(), item.name.lower())


def generate_markdown(directory_path, prefix=""):
    """
    Recursively generate markdown representation of a directory structure.
    Returns the markdown content as a string.
    """
    dir_path = Path(directory_path)
    content = ""
    
    try:
        # Get all items in the directory
        items = list(dir_path.iterdir())
        
        # Filter out excluded items
        items = [item for item in items if not should_exclude(item)]
        
        # Sort items (directories first, then files)
        items.sort(key=sort_items)
        
        # Process each item
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            
            if is_last_item:
                item_prefix = "└── "
                child_prefix = "    "
            else:
                item_prefix = "├── "
                child_prefix = "│   "
            
            if item.is_dir():
                # For directories, add a folder indicator and recurse
                content += f"{prefix}{item_prefix}📁 **{item.name}/**\n"
                content += generate_markdown(item, prefix + child_prefix)
            else:
                # For files, just add the filename
                content += f"{prefix}{item_prefix}📄 {item.name}\n"
    
    except PermissionError:
        content += f"{prefix}└── ⚠️ *Permission denied*\n"
    except Exception as e:
        content += f"{prefix}└── ⚠️ *Error: {str(e)}*\n"
    
    return content


def create_filemap(directory_path, output_dir='.'):
    """
    Generate a markdown file map for the given directory.
    """
    # Convert to Path objects
    directory_path = Path(directory_path)
    output_dir = Path(output_dir)
    
    # Ensure the directory exists
    if not directory_path.exists() or not directory_path.is_dir():
        print(f"Error: {directory_path} is not a valid directory")
        return False
    
    # Ensure the output directory exists
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    # Generate the header with the base directory included
    markdown_content = f"# File Structure: {directory_path}\n\n"
    markdown_content += f"📁 **{directory_path.name}/**\n"
    
    # Generate the rest of the content
    markdown_content += generate_markdown(directory_path)
    
    # Create the output file name
    output_file = output_dir / f"{directory_path.name}_filemap.md"
    
    # Write the markdown content to the file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"File structure markdown generated: {output_file}")
    return True


if __name__ == "__main__":
    # Set your variables here
    directory_path = r"C:\projects\File_Util_App\fdd_pipeline"
    output_directory = r"."  # Current directory
    
    # Generate the file map
    create_filemap(directory_path, output_directory)