# mod_ast.DAT

import td
import re
import ast
log           = mod('utils').log            # Import log function for error handling
td_isinstance = mod('utils').td_isinstance  # Import centralized TD type checking


def extract_block_text(code_text, target_name, target_type=None):
    """
    Extracts the textual block of a top-level class or function definition from the given code_text using AST,
    with a fallback to line-based parsing if AST fails due to syntax errors.
    
    This function first attempts to parse the code with ast.parse to locate the exact ClassDef or FunctionDef
    node matching target_name, handling decorators and comments accurately. If parsing fails (e.g., syntax errors
    outside the target), it falls back to a line-based approach, scanning for the target definition based on
    indentation and leading decorators. This dual-strategy ensures robustness for both well-formed and error-prone DATs.
    
    Args:
        code_text (str): The full text content of the source code (e.g., from a Text DAT).
        target_name (str): The name of the class or function to extract.
        target_type (str, optional): Specifies 'class' or 'def' to narrow the search; if None, searches both.
    
    Returns:
        str: The extracted block as a string, ready for compilation/execution.
    
    Raises:
        ValueError: If the target_name is not found in the code or target_type is invalid, with a message
                   indicating the expected type (e.g., 'Expecting Class <name> not found in the DAT' or
                   'Expecting Function <name> not found in the DAT').
    
    Importance: Combining AST with a text fallback provides a balance between precision (for valid code) and
    tolerance (for TD's often incomplete DATs), enabling selective extraction without requiring full syntactic validity.
    """
    try:
        # Attempt AST parsing
        tree = ast.parse(code_text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == target_name:
                if target_type and target_type.lower() not in ('class', 'def'):
                    raise ValueError("target_type must be 'class' or 'def'")
                if not target_type or (target_type.lower() == 'class' and isinstance(node, ast.ClassDef)) or \
                   (target_type.lower() == 'def' and isinstance(node, ast.FunctionDef)):
                    # Extract lines from source using node positions
                    lines = code_text.splitlines()
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                    block_lines = lines[start_line:end_line]
                    return '\n'.join(block_lines)
        expected_type = 'Class' if target_type == 'class' else 'Function' if target_type == 'def' else 'Class or Function'
        raise ValueError(f"Expecting {expected_type} '{target_name}' not found in the DAT")
    except SyntaxError:
        # Fallback to line-based parsing if AST fails
        lines = code_text.splitlines()
        start = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            pattern = r'^(class|def)\s+' + re.escape(target_name) + r'\b'
            if re.match(pattern, stripped):
                if not target_type or (target_type.lower() == 'class' and 'class' in stripped) or \
                   (target_type.lower() == 'def' and 'def' in stripped):
                    start = i
                    break
        if start is None:
            expected_type = 'Class' if target_type == 'class' else 'Function' if target_type == 'def' else 'Class or Function'
            raise ValueError(f"Expecting {expected_type} '{target_name}' not found in the DAT")
        # Backtrack for decorators
        decorator_start = start
        while decorator_start > 0 and lines[decorator_start - 1].strip().startswith('@'):
            decorator_start -= 1
        # Indent level from the def/class line
        indent_level = len(lines[start]) - len(lines[start].lstrip())
        # Find end
        end = start + 1
        while end < len(lines):
            current_line = lines[end]
            stripped = current_line.strip()
            if stripped and (len(current_line) - len(current_line.lstrip())) <= indent_level:
                break
            end += 1
        block_lines = lines[decorator_start:end]
        return '\n'.join(block_lines)

def Main(cls=None, func=None, op=None):
    """
    Dynamically extracts, compiles, and executes a specific class or function from a Text DAT,
    then returns the resulting class type or function object without attaching to globals or immediate execution.
    
    Args:
        cls (str, optional): The name of the class to extract; mutually exclusive with func.
        func (str, optional): The name of the function to extract; mutually exclusive with cls.
        op (td.textDAT or str, optional): The Text DAT operator or its path string containing the source code;
                                         defaults to last arg if positional.
    
    Returns:
        The class type or function object for use in OProxy's _extend method or explicit invocation.
    
    Raises:
        ValueError: If 'op' is invalid, target not found, no cls/func specified, or extracted object is unsupported.
    
    Importance: This is the core utility function that enables selective, dynamic importing of
    classes/functions from other DATs within the OProxy framework, avoiding side effects from top-level
    code execution (like prints or errors). It supports clean, modular scripting by providing the extracted
    object for OProxy to manage attachment and initialization, ensuring persistent extensions (e.g., via _extend)
    are safely handled without global namespace pollution or recursive dependencies in TouchDesigner projects.
    """
    # Ensure either cls or func is provided, but not both
    if not (cls or func) or (cls and func):
        raise ValueError("Must specify exactly one of 'cls' or 'func' keyword arguments")
    target_name = cls or func  # Use cls or func as the target name
    target_type = 'class' if cls else 'def'

    # Type checking and handling for op using td_isinstance
    try:
        op = td_isinstance(op, 'textdat', allow_string=True)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Provided op must be a td.textDAT or a string path to one: {e}")

    # Get the code text
    code_text = op.text
    block_text = extract_block_text(code_text, target_name, target_type)
    try:
        # Compile and exec only the extracted block
        compiled = compile(block_text, '<string>', 'exec')
        exec(compiled)
        obj = locals()[target_name]
        if isinstance(obj, type) or callable(obj):
            return obj  # Return class type or function for OProxy management
        else:
            raise ValueError(f"Extracted '{target_name}' is {type(obj).__name__}, neither a class nor a function")
    except Exception as e:
        log(f"Error executing block for '{target_name}' from {op.path}: {str(e)} at line {e.lineno if hasattr(e, 'lineno') else 'unknown'}")
        raise