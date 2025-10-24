#!/usr/bin/env python3
"""
Jarvis Function Inventory Generator

Scans Python files in a directory and generates a JSON index with:
- File structure and organization
- Function definitions with metadata
- Class definitions with methods
- Import statements
- Code statistics

Output: <folder_name>_index/<folder_name>_index.json co-located with scanned folder
"""

import ast
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import argparse


class InventoryGenerator:
    """Main class for generating function inventories from Python code."""
    
    def __init__(self, target_path: Path, verbose: bool = False):
        """
        Initialize the inventory generator.
        
        Args:
            target_path: Path to the folder to scan
            verbose: Enable verbose output
        """
        self.target_path = target_path.resolve()
        self.verbose = verbose
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def extract_imports(self, tree: ast.AST) -> List[str]:
        """
        Extract import statements from AST.
        
        Args:
            tree: Parsed AST tree
            
        Returns:
            List of import strings
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return sorted(set(imports))
    
    def extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Extract information about a function.
        
        Args:
            node: AST FunctionDef node
            
        Returns:
            Dictionary with function metadata
        """
        docstring = ast.get_docstring(node)
        
        return {
            "name": node.name,
            "line": node.lineno,
            "type": "function",
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "is_private": node.name.startswith("_"),
            "docstring": docstring.split('\n')[0] if docstring else None
        }
    
    def extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """
        Extract information about a class and its methods.
        
        Args:
            node: AST ClassDef node
            
        Returns:
            Dictionary with class metadata
        """
        docstring = ast.get_docstring(node)
        methods = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self.extract_function_info(item))
        
        return {
            "name": node.name,
            "line": node.lineno,
            "docstring": docstring.split('\n')[0] if docstring else None,
            "methods": methods
        }
    
    def parse_python_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a Python file and extract structure.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with file structure or None on error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                line_count = len(content.splitlines())
            
            tree = ast.parse(content, filename=str(file_path))
            
            # Extract top-level functions and classes
            functions = []
            classes = []
            
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(self.extract_function_info(node))
                elif isinstance(node, ast.ClassDef):
                    classes.append(self.extract_class_info(node))
            
            imports = self.extract_imports(tree)
            
            relative_path = file_path.relative_to(self.target_path)
            
            return {
                "path": str(file_path),
                "relative_path": str(relative_path),
                "line_count": line_count,
                "functions": functions,
                "classes": classes,
                "imports": imports
            }
            
        except SyntaxError as e:
            error_msg = f"Syntax error in {file_path}: {e}"
            self.log(error_msg, "WARNING")
            self.errors.append(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            self.log(error_msg, "ERROR")
            self.errors.append(error_msg)
            return None
    
    def scan_directory(self) -> List[Dict[str, Any]]:
        """
        Recursively scan directory for Python files.
        
        Returns:
            List of file information dictionaries
        """
        self.log(f"Scanning directory: {self.target_path}")
        
        # Find all Python files, excluding common directories to skip
        python_files = []
        for py_file in self.target_path.rglob("*.py"):
            # Skip unwanted directories
            parts = py_file.parts
            skip_dirs = {'__pycache__', '.venv', 'venv', '.git', '.tox', 'build', 'dist'}
            
            # Check if any part of the path should be skipped
            if any(part in skip_dirs or part.startswith('.') for part in parts):
                continue
            
            python_files.append(py_file)
        
        self.log(f"Found {len(python_files)} Python files")
        
        # Parse each file
        file_data = []
        for py_file in sorted(python_files):
            self.log(f"Processing: {py_file.relative_to(self.target_path)}")
            file_info = self.parse_python_file(py_file)
            if file_info:
                file_data.append(file_info)
        
        return file_data
    
    def calculate_statistics(self, file_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate statistics from file data.
        
        Args:
            file_data: List of file information dictionaries
            
        Returns:
            Dictionary of statistics
        """
        total_lines = sum(f["line_count"] for f in file_data)
        
        # Count function types
        private_funcs = 0
        public_funcs = 0
        async_funcs = 0
        
        for file_info in file_data:
            for func in file_info["functions"]:
                if func["is_private"]:
                    private_funcs += 1
                else:
                    public_funcs += 1
                if func["is_async"]:
                    async_funcs += 1
            
            # Count methods in classes
            for cls in file_info["classes"]:
                for method in cls["methods"]:
                    if method["is_private"]:
                        private_funcs += 1
                    else:
                        public_funcs += 1
                    if method["is_async"]:
                        async_funcs += 1
        
        return {
            "total_lines_of_code": total_lines,
            "files_by_type": {".py": len(file_data)},
            "private_functions": private_funcs,
            "public_functions": public_funcs,
            "async_functions": async_funcs
        }
    
    def generate_inventory(self) -> Dict[str, Any]:
        """
        Generate complete inventory for the target directory.
        
        Returns:
            Complete inventory dictionary
        """
        # Scan directory
        file_data = self.scan_directory()
        
        if not file_data:
            raise ValueError(f"No Python files found in {self.target_path}")
        
        # Calculate statistics
        statistics = self.calculate_statistics(file_data)
        
        # Count total functions and classes
        total_functions = sum(len(f["functions"]) for f in file_data)
        total_classes = sum(len(f["classes"]) for f in file_data)
        
        # Add method counts to total functions
        for file_info in file_data:
            for cls in file_info["classes"]:
                total_functions += len(cls["methods"])
        
        # Build inventory structure
        inventory = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "folder_path": str(self.target_path),
                "folder_name": self.target_path.name,
                "total_files": len(file_data),
                "total_functions": total_functions,
                "total_classes": total_classes,
                "scan_depth": "recursive"
            },
            "files": file_data,
            "statistics": statistics
        }
        
        return inventory
    
    def write_inventory(self, inventory: Dict[str, Any]) -> Path:
        """
        Write inventory to JSON file in co-located directory.
        
        Args:
            inventory: Inventory dictionary to write
            
        Returns:
            Path to written file
        """
        folder_name = self.target_path.name
        output_dir = self.target_path / f"{folder_name}_index"
        output_file = output_dir / f"{folder_name}_index.json"
        
        self.log(f"Creating output directory: {output_dir}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file if present
        if output_file.exists():
            self.log(f"Removing existing index: {output_file}")
            output_file.unlink()
        
        # Write new inventory
        self.log(f"Writing inventory to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def run(self) -> Path:
        """
        Execute the complete inventory generation process.
        
        Returns:
            Path to generated inventory file
            
        Raises:
            ValueError: If target path is invalid or no files found
            Exception: For other unexpected errors
        """
        # Validate target path
        if not self.target_path.exists():
            raise ValueError(f"Path does not exist: {self.target_path}")
        
        if not self.target_path.is_dir():
            raise ValueError(f"Path is not a directory: {self.target_path}")
        
        # Generate inventory
        inventory = self.generate_inventory()
        
        # Write to file
        output_file = self.write_inventory(inventory)
        
        return output_file


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate function inventory for Python files in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s modules/interface
  %(prog)s agents/diagnostic -v
  %(prog)s services/orchestration --verbose

The inventory will be saved to:
  <target_folder>/<folder_name>_index/<folder_name>_index.json
        """
    )
    
    parser.add_argument(
        'path',
        type=Path,
        help='Path to directory to scan'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Create generator and run
        generator = InventoryGenerator(args.path, verbose=args.verbose)
        output_file = generator.run()
        
        # Success output
        print(f"✅ Inventory generated successfully")
        print(f"📁 Output: {output_file}")
        
        # Load and display summary
        with open(output_file, 'r') as f:
            inventory = json.load(f)
        
        metadata = inventory['metadata']
        stats = inventory['statistics']
        
        print(f"\n📊 Summary:")
        print(f"   Files scanned: {metadata['total_files']}")
        print(f"   Total functions: {metadata['total_functions']}")
        print(f"   Total classes: {metadata['total_classes']}")
        print(f"   Lines of code: {stats['total_lines_of_code']}")
        print(f"   Public functions: {stats['public_functions']}")
        print(f"   Private functions: {stats['private_functions']}")
        print(f"   Async functions: {stats['async_functions']}")
        
        if generator.errors:
            print(f"\n⚠️  Warnings: {len(generator.errors)} file(s) had errors")
            if args.verbose:
                for error in generator.errors:
                    print(f"   - {error}")
        
        return 0
        
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
