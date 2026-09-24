#!/usr/bin/env python3
"""
Expand cplib imports into raw single-file source while preserving the main-body structure.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Sequence, Set, Tuple

from module_symbols import ModuleSymbols, is_cplib_module, simplify_import_aliases
from format_expanded import format_code
from merge_expanded import merge_library_with_original_main
from tempfile import NamedTemporaryFile, TemporaryDirectory

from ast_utils import LIBRARY_END_MARKER, assignment_target_names, extract_loaded_names, is_simple_name_assignment, split_initial_import_block, type_checking_comments, unparse_with_comments

@dataclass
class ImportedModule:
    module_name: str
    binding_name: str
    access_path: tuple[str, ...]
    used_exports: Set[str] = field(default_factory=set[str])
    bare_used: bool = False


def render_import_alias(alias: ast.alias) -> str:
    """Render a single import alias as a standalone import statement."""
    if alias.asname:
        return f"import {alias.name} as {alias.asname}"
    return f"import {alias.name}"


def flatten_attribute_chain(node: ast.AST) -> Optional[tuple[str, ...]]:
    """Flatten a dotted attribute chain into a tuple of names."""
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value

    if not isinstance(current, ast.Name):
        return None

    parts.append(current.id)
    return tuple(reversed(parts))


class ModuleUseCollector(ast.NodeVisitor):
    """Collect bare module-name uses and dotted attribute chains."""

    def __init__(self) -> None:
        self.bare_names: Set[str] = set()
        self.attribute_chains: list[tuple[str, ...]] = []

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.bare_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            chain = flatten_attribute_chain(node)
            if chain:
                self.attribute_chains.append(chain)
                return
        self.generic_visit(node)


def collect_module_uses(nodes: Sequence[ast.AST]) -> tuple[Set[str], list[tuple[str, ...]]]:
    """Collect module-object uses from a list of AST nodes."""
    collector = ModuleUseCollector()
    for node in nodes:
        collector.visit(node)
    return collector.bare_names, collector.attribute_chains


class CplibExpander:
    """Expand requested cplib definitions and their dependencies."""

    def __init__(self, cplib_path: Path) -> None:
        self.cplib_path = cplib_path
        self.symbols: ModuleSymbols | None = None
        self.module_variables: dict[str, str] = {}
        self.builtins_variable = ''
        self.needed_items: Set[str] = set()  # Items explicitly requested
        self.all_definitions: Dict[str, Tuple[ast.AST, str]] = {}  # name -> (node, source_file)
        self.dependencies: Dict[str, Set[str]] = {}  # name -> set of dependencies
        self.processed_files: Set[str] = set()  # Files already processed
        self.stdlib_imports: Set[str] = set()
        self.future_imports: Set[str] = set()
        self.parsed_modules: Dict[Path, ast.Module] = {}
        self.source_comments: dict[str, dict[int, str]] = {}

    def register_definition(self, node: ast.AST, file_str: str) -> None:
        """Register a top-level definition node and its dependencies."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            self.all_definitions[node.name] = (node, file_str)
            self.dependencies[node.name] = extract_loaded_names(node)
            return

        if is_simple_name_assignment(node):
            for target_name in assignment_target_names(node):
                self.all_definitions[target_name] = (node, file_str)
                self.dependencies[target_name] = extract_loaded_names(node)

    def definition_sort_key(self, name: str) -> tuple[int, int, str]:
        """Provide a deterministic fallback order inside dependency cycles."""
        node, source_file = self.all_definitions[name]
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            priority = 0
        elif isinstance(node, ast.ClassDef):
            priority = 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            priority = 2
        else:
            priority = 3
        return (priority, self.definition_source_index(name, source_file), name)

    def definition_source_index(self, name: str, source_file: str) -> int:
        """Return the source line used to stabilize ordering."""
        node, _ = self.all_definitions[name]
        return getattr(node, 'lineno', 0)

    def parse_module(self, file_path: Path) -> ast.Module:
        """Parse a Python module."""
        resolved_path = file_path.resolve()
        if resolved_path not in self.parsed_modules:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.parsed_modules[resolved_path] = ast.parse(content, filename=str(resolved_path))
        return self.parsed_modules[resolved_path]

    def collect_definitions_from_file(self, file_path: Path) -> None:
        """Collect rewritten definitions and standard-library imports."""
        file_str = str(file_path)
        if file_str in self.processed_files:
            return
        self.processed_files.add(file_str)
        comments = type_checking_comments(file_path.read_text(encoding='utf-8'))
        self.source_comments[file_str] = comments
        for node in self.parse_module(file_path).body:
            if isinstance(node, ast.ImportFrom):
                if node.module == '__future__':
                    self.future_imports.update(alias.name for alias in node.names)
                else:
                    self.stdlib_imports.add(unparse_with_comments(node, comments))
            elif isinstance(node, ast.Import):
                self.stdlib_imports.update(unparse_with_comments(ast.copy_location(ast.Import(names=[alias]), node), comments) for alias in node.names)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign)):
                self.register_definition(node, file_str)

    def resolve_module_path(self, module_name: str) -> Optional[Path]:
        """Resolve a cplib module name to file path."""
        assert self.symbols is not None
        try:
            return self.symbols.resolve_path(module_name)
        except FileNotFoundError:
            return None

    def process_import(self, import_node: ast.ImportFrom) -> None:
        """Process a cplib import and collect requested items."""
        module_name = import_node.module
        if module_name is None:
            return
        module_file = self.resolve_module_path(module_name)
        if not module_file:
            return

        # Collect all definitions from this module and its dependencies
        self.collect_definitions_from_file(module_file)

        assert self.symbols is not None
        bindings = self.symbols.mapping(module_name)
        names = self.symbols.exports(module_name) if import_node.names[0].name == '*' else [alias.name for alias in import_node.names]
        for name in names:
            if (module_name, name) in self.symbols.submodule_imports:
                continue
            if name not in bindings:
                raise ImportError(f'Cannot import {name!r} from {module_name!r}')
            self.needed_items.add(bindings[name])

    def register_module_import(self, module_imports: Dict[tuple[str, str], ImportedModule], alias: ast.alias) -> None:
        """Register an `import cplib.xxx` style import."""
        module_name = alias.name
        binding_name = alias.asname or module_name.split('.')[0]
        access_path = (binding_name,) if alias.asname else tuple(module_name.split('.'))
        key = (module_name, '.'.join(access_path))

        if key not in module_imports:
            module_imports[key] = ImportedModule(
                module_name=module_name,
                binding_name=binding_name,
                access_path=access_path,
            )

    def apply_module_import_usage(
        self,
        module_imports: Dict[tuple[str, str], ImportedModule],
        preserved_main_nodes: Sequence[ast.AST],
    ) -> None:
        """Analyze how imported cplib modules are used from the main code."""
        assert self.symbols is not None
        bare_names, attribute_chains = collect_module_uses(preserved_main_nodes)
        imports = list(module_imports.values())

        for bare_name in bare_names:
            for module_import in imports:
                if module_import.binding_name == bare_name:
                    module_import.bare_used = True

        for chain in attribute_chains:
            matched: list[ImportedModule] = []
            matched_length = -1
            for module_import in imports:
                access_path = module_import.access_path
                if len(chain) < len(access_path) or chain[:len(access_path)] != access_path:
                    continue
                if len(access_path) > matched_length:
                    matched = [module_import]
                    matched_length = len(access_path)
                elif len(access_path) == matched_length:
                    matched.append(module_import)
            for module_import in matched:
                remaining = chain[matched_length:]
                while remaining:
                    child = f'{module_import.module_name}.{remaining[0]}'
                    if remaining[0] in self.symbols.mapping(module_import.module_name) or child not in self.symbols.trees:
                        break
                    module_import = module_imports.setdefault((child, ''), ImportedModule(child, '', ()))
                    remaining = remaining[1:]
                if remaining:
                    module_import.used_exports.add(remaining[0])
                else:
                    module_import.bare_used = True

        # Passing a package object elsewhere can also access any of its loaded
        # children, even when no child attribute appears directly in main.
        for module_import in list(module_imports.values()):
            if module_import.bare_used:
                for child in self.symbols.trees:
                    if child.startswith(module_import.module_name + '.'):
                        module_imports.setdefault((child, ''), ImportedModule(child, '', ())).bare_used = True

    def build_module_namespace_assignments(self, module_imports: Dict[tuple[str, str], ImportedModule]) -> list[str]:
        """Build shared module objects whose attributes follow their bindings."""
        if not module_imports:
            return []
        assert self.symbols is not None
        exports: dict[str, dict[str, str]] = {}
        for module_import in module_imports.values():
            available = self.symbols.mapping(module_import.module_name)
            requested = set(available) if module_import.bare_used else module_import.used_exports
            bindings = exports.setdefault(module_import.module_name, {})
            bindings.update((name, available[name]) for name in requested if name in available)
        for bindings in exports.values():
            self.needed_items.update(bindings.values())
        modules = set(exports)
        for module in list(modules):
            while '.' in module:
                module = module.rpartition('.')[0]
                modules.add(module)
        for module in sorted(modules):
            self.module_variables[module] = self.symbols.allocate_name('_cplib_module_' + module.removeprefix('cplib.').replace('.', '_'))
        builtins_name = self.symbols.allocate_name('_CPLIB_BUILTINS')
        self.builtins_variable = builtins_name
        type_name = self.symbols.allocate_name('_CPLIB_ModuleType')
        proxy_name = self.symbols.allocate_name('_CPLIB_MODULE')
        self.stdlib_imports.add(f'import builtins as {builtins_name}')
        self.stdlib_imports.add(f'from types import ModuleType as {type_name}')
        helper = f'''
class {proxy_name}({type_name}):
    __slots__ = ('_cplib_bindings', '_cplib_namespace')

    def __init__(self, name, bindings, namespace, doc):
        {type_name}.__setattr__(self, '_cplib_bindings', {{name: item[0] for name, item in bindings.items()}})
        {type_name}.__setattr__(self, '_cplib_namespace', namespace)
        {type_name}.__init__(self, name, doc)

    def __getattr__(self, name):
        bindings = {type_name}.__getattribute__(self, '_cplib_bindings')
        namespace = {type_name}.__getattribute__(self, '_cplib_namespace')
        try:
            return namespace[bindings[name]]
        except {builtins_name}.KeyError:
            raise {builtins_name}.AttributeError(f'module {{self.__name__!r}} has no attribute {{name!r}}') from None

    def __setattr__(self, name, value):
        bindings = {type_name}.__getattribute__(self, '_cplib_bindings')
        if name in bindings:
            namespace = {type_name}.__getattribute__(self, '_cplib_namespace')
            namespace[bindings[name]] = value
        else:
            {type_name}.__setattr__(self, name, value)

    def __delattr__(self, name):
        bindings = {type_name}.__getattribute__(self, '_cplib_bindings')
        if name in bindings:
            namespace = {type_name}.__getattribute__(self, '_cplib_namespace')
            try:
                del namespace[bindings[name]]
            except {builtins_name}.KeyError:
                raise {builtins_name}.AttributeError(name) from None
        else:
            {type_name}.__delattr__(self, name)

    def __dir__(self):
        bindings = {type_name}.__getattribute__(self, '_cplib_bindings')
        namespace = {type_name}.__getattribute__(self, '_cplib_namespace')
        names = {builtins_name}.set({type_name}.__getattribute__(self, '__dict__'))
        names.update(name for name, target in bindings.items() if target in namespace)
        return {builtins_name}.sorted(names)
'''
        assignments = [helper]
        for module in sorted(modules, key=lambda name: (name.count('.'), name)):
            variable = self.module_variables[module]
            doc = ast.get_docstring(self.symbols.trees[module]) if module in self.symbols.trees else None
            pairs = ', '.join(f'{name!r}: ({target!r}, {target})' for name, target in sorted(exports.get(module, {}).items()))
            assignments.append(f'{variable} = {proxy_name}({module!r}, {{{pairs}}}, {builtins_name}.globals(), {doc!r})')
            parent, _, child = module.rpartition('.')
            if parent:
                assignments.append(f'{self.module_variables[parent]}.{child} = {variable}')
            is_package = module not in self.symbols.paths or self.symbols.paths[module].name == '__init__.py'
            assignments.append(f'{variable}.__package__ = {(module if is_package else parent)!r}')
        return assignments

    def find_all_dependencies(self) -> Set[str]:
        """Find all dependencies needed for the requested items."""
        needed = set(self.needed_items)
        to_process = list(self.needed_items)

        while to_process:
            current = to_process.pop()
            if current in self.dependencies:
                for dep in self.dependencies[current]:
                    if dep in self.all_definitions and dep not in needed:
                        needed.add(dep)
                        to_process.append(dep)

        return needed

    def topologically_order_definitions(self, names: Set[str]) -> list[str]:
        """Order expanded library definitions by dependency, breaking cycles deterministically."""
        ordered_candidates = [name for name in self.all_definitions if name in names]
        name_set = set(ordered_candidates)
        dependency_graph: Dict[str, list[str]] = {}

        for name in ordered_candidates:
            deps = [
                dep
                for dep in self.dependencies.get(name, set())
                if dep != name and dep in name_set
            ]
            deps.sort(key=lambda dep: self.definition_source_index(dep, self.all_definitions[dep][1]))
            dependency_graph[name] = deps

        index = 0
        stack: list[str] = []
        indices: Dict[str, int] = {}
        lowlinks: Dict[str, int] = {}
        on_stack: Set[str] = set()
        components: list[list[str]] = []

        for start in ordered_candidates:
            if start in indices:
                continue
            indices[start] = lowlinks[start] = index
            index += 1
            stack.append(start)
            on_stack.add(start)
            frames: list[tuple[str, int]] = [(start, 0)]
            while frames:
                name, next_edge = frames[-1]
                if next_edge < len(dependency_graph[name]):
                    dep = dependency_graph[name][next_edge]
                    frames[-1] = (name, next_edge + 1)
                    if dep not in indices:
                        indices[dep] = lowlinks[dep] = index
                        index += 1
                        stack.append(dep)
                        on_stack.add(dep)
                        frames.append((dep, 0))
                    elif dep in on_stack:
                        lowlinks[name] = min(lowlinks[name], indices[dep])
                    continue
                frames.pop()
                if lowlinks[name] == indices[name]:
                    component: list[str] = []
                    while stack:
                        current = stack.pop()
                        on_stack.remove(current)
                        component.append(current)
                        if current == name:
                            break
                    components.append(component)
                if frames:
                    parent = frames[-1][0]
                    lowlinks[parent] = min(lowlinks[parent], lowlinks[name])

        component_id: Dict[str, int] = {}
        for comp_index, component in enumerate(components):
            for name in component:
                component_id[name] = comp_index

        component_edges: Dict[int, Set[int]] = {i: set() for i in range(len(components))}
        indegree: Dict[int, int] = {i: 0 for i in range(len(components))}
        for name in ordered_candidates:
            src = component_id[name]
            for dep in dependency_graph[name]:
                dst = component_id[dep]
                if src == dst or src in component_edges[dst]:
                    continue
                component_edges[dst].add(src)
                indegree[src] += 1

        component_order_key = {
            i: min(self.definition_source_index(name, self.all_definitions[name][1]) for name in component)
            for i, component in enumerate(components)
        }
        ready = sorted(
            [i for i, deg in indegree.items() if deg == 0],
            key=lambda comp: component_order_key[comp],
        )
        result: list[str] = []
        ready_index = 0

        while ready_index < len(ready):
            comp = ready[ready_index]
            ready_index += 1

            component = components[comp]
            if len(component) == 1:
                result.append(component[0])
            else:
                component.sort(key=self.definition_sort_key)
                result.extend(component)

            next_components = sorted(component_edges[comp], key=lambda nxt: component_order_key[nxt])
            for nxt in next_components:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)

        return result

    def generate_minimal_code(self, main_file: str) -> str:
        """Generate minimal expanded code."""
        # Parse main file
        with open(main_file, 'r', encoding='utf-8') as f:
            main_content = f.read()
        main_tree = ast.parse(main_content)
        main_comments = type_checking_comments(main_content)

        self.symbols = ModuleSymbols(self.cplib_path, main_tree)
        self.parsed_modules = {path: self.symbols.rewrite(module) for module, path in self.symbols.paths.items()}
        for path in self.symbols.paths.values():
            self.collect_definitions_from_file(path)
        prelude_nodes, _ = split_initial_import_block(main_tree.body)
        initial_import_ids = {id(node) for node in prelude_nodes}
        module_imports: Dict[tuple[str, str], ImportedModule] = {}
        replacements: dict[ast.stmt, str] = {}
        module_nodes: list[ast.Import | ast.ImportFrom] = []
        for node in ast.walk(main_tree):
            if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module):
                self.process_import(node)
                assert node.module is not None
                bindings = self.symbols.mapping(node.module)
                aliases = [ast.alias(name=name) for name in self.symbols.exports(node.module)] if node.names[0].name == '*' else node.names
                if any((node.module, alias.name) in self.symbols.submodule_imports for alias in aliases):
                    module_nodes.append(node)
                    for alias in aliases:
                        module = self.symbols.submodule_imports.get((node.module, alias.name))
                        if module is not None:
                            self.register_module_import(module_imports, ast.alias(name=module, asname=alias.asname or alias.name))
                    continue
                assignments = [f'{alias.asname or alias.name} = {bindings[alias.name]}' for alias in aliases if (alias.asname or alias.name) != bindings[alias.name]]
                replacements[node] = '; '.join(assignments) or 'pass'
            elif isinstance(node, ast.Import):
                cplib_aliases = [alias for alias in node.names if is_cplib_module(alias.name)]
                if cplib_aliases:
                    module_nodes.append(node)
                    for alias in cplib_aliases:
                        self.register_module_import(module_imports, alias)
                elif id(node) in initial_import_ids:
                    for alias in node.names:
                        self.stdlib_imports.add(unparse_with_comments(ast.copy_location(ast.Import(names=[alias]), node), main_comments))
                    replacements[node] = 'pass'
            elif isinstance(node, ast.ImportFrom) and id(node) in initial_import_ids:
                if node.module == '__future__':
                    self.future_imports.update(alias.name for alias in node.names)
                else:
                    self.stdlib_imports.add(unparse_with_comments(node, main_comments))
                replacements[node] = 'pass'

        self.apply_module_import_usage(module_imports, main_tree.body)
        namespace_assignments = self.build_module_namespace_assignments(module_imports)
        for node in module_nodes:
            statements: list[str] = []
            for alias in node.names:
                if isinstance(node, ast.ImportFrom):
                    assert node.module is not None
                    module = self.symbols.submodule_imports.get((node.module, alias.name))
                    if module is None:
                        target = self.symbols.mapping(node.module)[alias.name]
                    else:
                        parent = self.module_variables[node.module]
                        target = f'{self.builtins_variable}.getattr({parent}, {alias.name!r}, {self.module_variables[module]})'
                    statements.append(f'{alias.asname or alias.name} = {target}')
                elif is_cplib_module(alias.name):
                    binding = alias.asname or alias.name.split('.')[0]
                    module = alias.name if alias.asname else 'cplib'
                    statements.append(f'{binding} = {self.module_variables[module]}')
                else:
                    statements.append(render_import_alias(alias))
            replacements[node] = '; '.join(statements) or 'pass'

        source = main_content.encode('utf-8')
        starts = [0]
        for line in source.splitlines(keepends=True):
            starts.append(starts[-1] + len(line))
        edits: list[tuple[int, int, bytes]] = []
        for node, replacement in replacements.items():
            start = starts[node.lineno - 1] + node.col_offset
            end = starts[(node.end_lineno or node.lineno) - 1] + (node.end_col_offset or 0)
            if replacement == 'pass' and node.col_offset == 0:
                tail = source[end:starts[node.end_lineno or node.lineno]].lstrip()
                if not tail or tail.startswith(b'#'):
                    replacement = ''
            edits.append((start, end, replacement.encode('utf-8')))
        for start, end, replacement in sorted(edits, reverse=True):
            source = source[:start] + replacement + source[end:]
        main_code = source.decode('utf-8')

        # Find all dependencies
        all_needed = self.find_all_dependencies()

        # Generate output
        output_lines: list[str] = []

        # Future imports
        if self.future_imports:
            output_lines.append(f"from __future__ import {', '.join(sorted(self.future_imports))}")
            output_lines.append("")

        # Standard library imports
        if self.stdlib_imports:
            # Sort imports
            imports = sorted(self.stdlib_imports)

            # Group by standard library vs others
            stdlib_modules = {
                'collections', 'itertools', 'functools', 'typing', 'math',
                'sys', 'os', 're', 'heapq', 'bisect', 'operator', 'random',
                'io', 'array', 'copy', 'enum', 'dataclasses', 'abc'
            }

            std_imports: list[str] = []
            other_imports: list[str] = []

            for imp in imports:
                if imp.startswith('import '):
                    module = imp.split()[1].split('.')[0]
                elif imp.startswith('from '):
                    module = imp.split()[1].split('.')[0]
                else:
                    module = ''

                if module in stdlib_modules:
                    std_imports.append(imp)
                else:
                    other_imports.append(imp)

            if std_imports:
                output_lines.extend(std_imports)
                output_lines.append("")

            if other_imports:
                output_lines.extend(other_imports)
                output_lines.append("")

        # Add expanded library definitions in dependency order only.
        original_names = {generated: symbol[1] for symbol, generated in self.symbols.names.items()}
        for name in self.topologically_order_definitions(all_needed):
            node, source_file = self.all_definitions[name]
            output_lines.append(unparse_with_comments(node, self.source_comments[source_file]))
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                original_name = original_names.get(node.name, node.name)
                if original_name != node.name:
                    output_lines.append(f'{node.name}.__name__ = {original_name!r}')
                    output_lines.append(f'{node.name}.__qualname__ = {original_name!r}')
            output_lines.append("")

        # Module-style imports need their generated namespaces in the library
        # fragment. The original main body is restored by the merger later.
        output_lines.extend(namespace_assignments)
        output_lines.append(repr(LIBRARY_END_MARKER))

        # Preserve comments, indentation, and the original import locations.
        output_lines.append(main_code)
        result = '\n'.join(output_lines)

        return result


def is_cplib_package_dir(path: Path) -> bool:
    """Return whether the path looks like the cplib package directory."""
    required_dirs = (
        'algorithm',
        'datastructure',
        'geometry',
        'graph',
        'mathematics',
        'string',
        'tools',
    )
    return path.is_dir() and all((path / subdir).is_dir() for subdir in required_dirs)


def normalize_cplib_path(path: Path) -> Optional[Path]:
    """Accept either a repo root or the package directory itself."""
    expanded = path.expanduser()
    candidates = [expanded, expanded / 'cplib']

    for candidate in candidates:
        resolved = candidate.resolve()
        if is_cplib_package_dir(resolved):
            return resolved

    return None


def find_installed_cplib_path() -> Optional[Path]:
    """Try to locate cplib from the current Python import path."""
    spec = importlib.util.find_spec('cplib')
    if spec is None:
        return None

    if spec.submodule_search_locations:
        for location in spec.submodule_search_locations:
            normalized = normalize_cplib_path(Path(location))
            if normalized:
                return normalized

    if spec.origin and spec.origin != 'namespace':
        normalized = normalize_cplib_path(Path(spec.origin).parent)
        if normalized:
            return normalized

    return None


def resolve_cplib_path(script_path: Path) -> Path:
    """Resolve the cplib package directory without relying on user-specific paths."""
    env_candidates: list[Path] = []
    for env_name in ('CPLIB_DIR', 'CPLIB_ROOT'):
        value = os.environ.get(env_name)
        if value:
            env_candidates.append(Path(value))

    candidates: list[Path] = [
        *env_candidates,
        script_path.resolve().parent.parent,
    ]

    for candidate in candidates:
        normalized = normalize_cplib_path(candidate)
        if normalized:
            return normalized

    installed_path = find_installed_cplib_path()
    if installed_path:
        return installed_path

    raise FileNotFoundError(
        "Could not locate the cplib package directory. "
        "Tried CPLIB_DIR, CPLIB_ROOT, the expander script location, and the current Python import path."
    )


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print('Usage: cplib-expander.sh <input_file> [output_file]', file=sys.stderr)
        raise SystemExit(1)
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    try:
        expander = CplibExpander(resolve_cplib_path(Path(__file__)))
        raw = expander.generate_minimal_code(str(input_file))
        boundary = next(node for node in ast.parse(raw).body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value == LIBRARY_END_MARKER)
        library = ''.join(raw.splitlines(keepends=True)[:boundary.lineno - 1])
        with TemporaryDirectory(prefix='cplib-expand-') as directory:
            root = Path(directory)
            raw_file, library_file, formatted_file = root / 'raw.py', root / 'library.py', root / 'formatted.py'
            raw_file.write_text(raw, encoding='utf-8')
            library_file.write_text(library, encoding='utf-8')
            if not format_code(str(library_file), str(formatted_file)):
                print('Warning: formatting failed; using unformatted library code', file=sys.stderr)
                formatted_file.write_text(library, encoding='utf-8')
            result = merge_library_with_original_main(str(input_file), str(formatted_file), str(raw_file))
        assert expander.symbols is not None
        generated_names = set(expander.symbols.names.values())
        generated_names.update(name for bindings in expander.symbols.storage.values() for name in bindings.values())
        result = simplify_import_aliases(result, generated_names)
        # Validate the complete artifact before replacing any existing output.
        ast.parse(result)
        if output_file is None:
            print(result, end='')
        else:
            temporary: Path | None = None
            try:
                with NamedTemporaryFile(mode='w', encoding='utf-8', prefix=output_file.name + '.tmp.', dir=output_file.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(result)
                os.replace(temporary, output_file)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            print(f'Expanded and formatted code written to: {output_file}', file=sys.stderr)
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
