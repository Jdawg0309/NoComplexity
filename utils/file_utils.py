import os

def scan_project_directory(path):
    """Scan a directory and return its structure, skipping hidden entries."""
    if not os.path.exists(path):
        return {}

    if os.path.isfile(path):
        return {os.path.basename(path): None}

    structure = {}
    # Use os.scandir for better performance on large trees
    with os.scandir(path) as it:
        for entry in it:
            # Skip hidden files/folders
            if entry.name.startswith('.'):
                continue

            if entry.is_dir(follow_symlinks=False):
                structure[entry.name] = scan_project_directory(entry.path)
            else:
                structure[entry.name] = None
    return structure

def format_directory_tree(tree, indent=0):
    """Format directory tree as nested HTML lists."""
    html = "<ul>\n"
    for name, contents in tree.items():
        spacer = '  ' * indent
        if contents is None:
            html += f"{spacer}<li>📄 {name}</li>\n"
        else:
            html += f"{spacer}<li>📁 <strong>{name}</strong>\n"
            html += format_directory_tree(contents, indent + 1)
            html += f"{spacer}</li>\n"
    html += "</ul>\n"
    return html

def read_file(file_path):
    """Read the content of a file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    """Write content to a file"""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
