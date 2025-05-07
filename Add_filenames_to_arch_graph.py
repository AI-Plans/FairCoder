import os
import re

def extract_functions_from_file(filepath):
    """
    Extracts function names from a Python file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:  # Specify encoding as 'utf-8'
        content = f.readlines()

    # Using a regular expression to match function definitions (e.g., def func_name)
    function_names = []
    for line in content:
        match = re.match(r'^\s*def\s+(\w+)\s*\(', line)  # Matches function definitions
        if match:
            function_names.append(match.group(1))  # Extract the function name
    return function_names

def add_filenames_to_dot(dot_file_path, directory):
    """
    Add the filenames next to the functions in the DOT file.
    """
    # Dictionary to hold function names and their corresponding files
    function_to_file = {}

    # Scan all Python files in the directory to find function names
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                functions = extract_functions_from_file(file_path)
                for func in functions:
                    function_to_file[func] = file

    # Now read the DOT file and modify the labels
    with open(dot_file_path, 'r') as f:
        content = f.readlines()

    # Modify the content to add filenames where functions are defined
    for i, line in enumerate(content):
        if "label=" in line:
            # Extract the function name from the label
            function_name = line.split('label="')[1].split('"')[0]
            
            # If the function is in our dictionary, update the label with the filename
            if function_name in function_to_file:
                filename = function_to_file[function_name]
                content[i] = content[i].replace(f'label="{function_name}"', f'label="{function_name} ({filename})"')

    # Write the modified content back to the DOT file
    with open(dot_file_path, 'w') as f:
        f.writelines(content)

# Example usage
directory = './'  # Replace this with your project directory
dot_file_path = 'clean_output.dot'  # Path to your DOT file
add_filenames_to_dot(dot_file_path, directory)