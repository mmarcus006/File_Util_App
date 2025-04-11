import os
from pathlib import Path
from typing import List, Optional, Set

def generate_tree(root_dir: str, exclude_dirs: Optional[Set[str]] = None) -> List[str]:
    """
    Generate a tree representation of the directory structure, focusing on Python files.
    
    Args:
        root_dir: Root directory to scan
        exclude_dirs: Set of directory names to exclude from scanning
        
    Returns:
        List of strings representing the tree structure
    """
    if exclude_dirs is None:
        exclude_dirs = set(['.git', '__pycache__', '.venv', '.env'])
    
    output_lines = ["Project Structure:", "./"]
    
    # Get all directories and Python files
    dirs_and_py_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        # Get relative path for display
        rel_path = os.path.relpath(dirpath, root_dir)
        
        # Skip data/split_fdds subdirectories to avoid excessive output
        if "data\\split_fdds" in rel_path and rel_path != "data\\split_fdds":
            continue
            
        if rel_path != '.':
            dirs_and_py_files.append((rel_path, True))  # True indicates it's a directory
        
        # Add Python files
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(rel_path, filename)
                if rel_path == '.':
                    file_path = filename
                dirs_and_py_files.append((file_path, False))  # False indicates it's a file
    
    # Sort by path
    dirs_and_py_files.sort()
    
    # Generate the tree structure
    for i, (path, is_dir) in enumerate(dirs_and_py_files):
        parts = path.split(os.sep)
        depth = len(parts) - 1
        
        # Calculate prefix
        prefix = "  "
        for j in range(depth):
            prefix += "│   "
        
        # Determine if this is the last item at its level
        is_last_at_level = (i == len(dirs_and_py_files) - 1 or 
                           (i < len(dirs_and_py_files) - 1 and 
                            len(dirs_and_py_files[i+1][0].split(os.sep)) <= len(parts)))
        
        connector = "└── " if is_last_at_level else "├── "
        item_name = parts[-1]
        
        if is_dir:
            output_lines.append(f"{prefix}{connector}{item_name}/")
        else:
            output_lines.append(f"{prefix}{connector}{item_name}")
    
    return output_lines

def main():
    """Main function to generate and display the project tree."""
    # Get current directory as root
    root_dir = "."
    
    # Directories to exclude
    exclude_dirs = {
        '.git', '__pycache__', '.venv', '.env', 
        '.vscode', '.idea', 'node_modules'
    }
    
    # Generate the tree structure
    output_lines = generate_tree(root_dir, exclude_dirs)
    
    # Print to console
    print("\n".join(output_lines))
    
    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Save output to a file in the docs directory
    output_file = docs_dir / "project_structure.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    
    print(f"\nProject structure saved to {output_file}")

if __name__ == "__main__":
    main() 