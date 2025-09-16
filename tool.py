from json import dumps
from pathlib import Path
from ast import arg, expr, literal_eval, parse, FunctionDef, unparse
from importlib.util import spec_from_file_location, module_from_spec
from inspect import getmembers, getdoc, isfunction
from pprint import pprint
from types import ModuleType
from typing import Any, Literal, get_args, get_origin


class ToolHandler:
    def __init__(self) -> None:
        self._tools = []
        self._registry = {}

    def data_ready(self) -> str:
        """Give back a string version of the tools, ready for prompting."""
        return dumps(self._tools)

    @property
    def tools(self) -> list[dict]:
        """List of loaded tools."""
        return self._tools

    def exec(self, name: str, **kwargs) -> str:
        """Execute a tool."""
        callback = self._registry.get(name)

        if callback is None:
            return f"Tool \"{name}\" not found."
        
        try:
            return str(callback(**kwargs))
        except Exception as e:
            return f"Tool \"{name}\" failed with error {e}. Arguments: {kwargs}"

    def load_directory(self, directory: Path) -> None:
        """Loads an entire directory of tools, recursively."""
        if not directory.exists():
            raise OSError(f"{directory} does not exist!")
        elif directory.is_file():
            raise OSError(f"{directory} should be a directory, not a file!")

        for script in directory.rglob("*.py"):
            if "__pycache__" in script.parents:
                continue
            self.load_python_file(script)

    def load_python_file(self, file_path: Path) -> None:
        """Loads all functions from a Python file."""
        documentation, module = self._extract_functions(file_path)
        
        with open(file_path, "r") as python_file:
            node = parse(python_file.read())

        for element in node.body:
            if not isinstance(element, FunctionDef):
                continue
            tool = {
                "type": "function",
                "function": {
                    "name": element.name,
                    "description": documentation[element.name],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }

            args = element.args
            args_list = args.args
            defaults = args.defaults
            
            num_required = len(args_list) - len(defaults)

            required_args: list[arg] = args_list[:num_required]
            optional_args: list[arg] = args_list[num_required:]

            self._add_required_arguments(tool, required_args, module)
            self._add_optional_arguments(tool, optional_args, defaults, module)
            self._tools.append(tool)

            pprint(tool, indent=2)

    @staticmethod
    def _python_to_json(py_type: str, annotation=None) -> dict:
        """Converts a python type into a json type."""
        mapping = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "list": {"type": "array"},
            "dict": {"type": "object"},
            "None": {"type": "null"},
        }
        py_type = py_type.strip()

        if annotation and get_origin(annotation) is Literal:
            return {
                "type": "string",
                "enum": list(get_args(annotation))
            }

        return mapping.get(py_type, {"type": "string"})
    
    @staticmethod
    def _json_to_python(json_type: str, val: Any) -> Any:
        """Converts a json type into a python type."""
        mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if json_type == "null":
            return None
        
        return mapping[json_type](val)

    def _add_required_arguments(self, tool: dict, required_arguments: list[arg], module: ModuleType) -> None:
        """Adds all required arguments to a tool."""
        for arg_node in required_arguments:
            arg_name = arg_node.arg
            arg_type = "string"
            if arg_node.annotation:
                arg_type = unparse(arg_node.annotation)
                try:
                    annotation_obj = eval(arg_type, module.__dict__)
                except Exception:
                    annotation_obj = None
                
                schema = self._python_to_json(arg_type, annotation_obj)
            else:
                schema = {"type": "string"}

            tool["function"]["parameters"]["properties"][arg_name] = dict(schema)
            tool["function"]["parameters"]["required"].append(arg_name)

    def _add_optional_arguments(self, tool: dict, optional_arguments: list[arg], defaults: list[expr], module: ModuleType) -> None:
        """Adds all optional arguments to a tool."""
        for arg_node, default_node in zip(optional_arguments, defaults):
            arg_name = arg_node.arg

            if arg_node.annotation: 
                annotation_src = unparse(arg_node.annotation)
                try:
                    annotation_obj = eval(annotation_src, module.__dict__)
                except Exception:
                    annotation_obj = None
                schema = self._python_to_json(annotation_src, annotation_obj)
            else:
                schema = {"type": "string"}

            try:
                default_value = literal_eval(default_node)
            except Exception:
                default_value = None

            # merge default into schema
            schema = dict(schema)
            schema["default"] = default_value
            tool["function"]["parameters"]["properties"][arg_name] = schema

    def _extract_functions(self, file_path: Path) -> tuple[dict, ModuleType]:
        """Finds all functions defined in a python file, gets their documentation."""
        module_name = file_path.stem
        spec = spec_from_file_location(module_name, file_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        docs = {}

        for name, obj in getmembers(module, isfunction):
            if obj.__module__ != module.__name__:  # Function is not defined in the module itself
                continue
            self._registry[name] = obj
            docs[name] = getdoc(obj) or ""
        return docs, module
