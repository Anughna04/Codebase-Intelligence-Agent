import os
from typing import List, Dict, Any
import tree_sitter
import tree_sitter_python

class PythonASTParser:
    """Parses Python source code to extract semantic blocks (classes, functions) for RAG context."""
    def __init__(self):
        # Initialize the Python language from tree-sitter-python
        self.language = tree_sitter.Language(tree_sitter_python.language())
        self.parser = tree_sitter.Parser(self.language)

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parses a Python file and returns a list of semantic code chunks."""
        if not os.path.exists(file_path) or not file_path.endswith('.py'):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_text = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []

        return self.parse_code(code_text, file_path)

    def parse_code(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extracts class and function definitions from raw source code string."""
        tree = self.parser.parse(bytes(source_code, 'utf8'))
        root_node = tree.root_node

        extracted_chunks = []
        source_lines = source_code.splitlines(keepends=True)

        # Traverse AST iteratively (DFS)
        stack = [root_node]
        while stack:
            node = stack.pop()

            if node.type in ('function_definition', 'async_function_definition', 'class_definition'):
                # Extract the name identity
                name_node = node.child_by_field_name('name')
                name = name_node.text.decode('utf8') if name_node else "anonymous"

                # Get block text boundaries
                start_byte = node.start_byte
                end_byte = node.end_byte
                block_text = source_code.encode('utf8')[start_byte:end_byte].decode('utf8')

                extracted_chunks.append({
                    "file_path": file_path,
                    "entity_name": name,
                    "entity_type": node.type,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "code_content": block_text
                })

            # For nested classes/functions, we DO NOT traverse children of these entities by default
            # because we chunk the whole function/class as one semantic unit.
            # However, if we want inner methods, we should traverse them or rely on the parent class block.
            # To avoid noise, let's keep whole top-level blocks. So we skip children of these node types
            # UNLESS they are class definitions, representing methods? Actually, class is a chunk, no need to overcomplicate.
            if node.type not in ('function_definition', 'async_function_definition', 'class_definition'):
                for child in node.children:
                    stack.append(child)

        return extracted_chunks

if __name__ == "__main__":
    # Test block
    parser = PythonASTParser()
    test_code = '''
class MyTestClass:
    def __init__(self):
        self.x = 10
    
    def do_something(self):
        pass

def global_function():
    return True
'''
    chunks = parser.parse_code(test_code, "test.py")
    for ch in chunks:
        print(f"[{ch['entity_type']}] {ch['entity_name']} (Lines {ch['start_line']}-{ch['end_line']})")
        print(f"Code preview: {ch['code_content'][:30]}...")
