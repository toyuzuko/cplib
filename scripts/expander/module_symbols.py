"""Resolve module bindings and rewrite only references to module globals."""

from __future__ import annotations

import ast
import builtins
import copy
import io
import re
import tokenize
from pathlib import Path

from ast_utils import assignment_target_names, is_simple_name_assignment, split_initial_import_block

Symbol = tuple[str, str]


def simplify_import_aliases(source: str, generated_names: set[str]) -> str:
    """Shorten generated from-import aliases once unused code has been removed.

    Keep aliases when the short name occurs in another binding or expression,
    including local variables and string annotations. Separate import snapshots
    and aliases referenced by strings (such as module-proxy mappings) stay intact.
    Token edits preserve comments and formatting in both library and main code.
    """
    tree = ast.parse(source)
    candidates: dict[str, list[ast.alias]] = {}
    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            for alias in statement.names:
                if alias.asname in generated_names and alias.asname.startswith('_cplib_') and '.' not in alias.name:
                    candidates.setdefault(alias.name, []).append(alias)
    writes = ModuleBindingWrites()
    writes.visit(tree)
    occupied = set(writes.counts)
    docstrings = {id(node.body[0].value) for node in ast.walk(tree) if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)}
    strings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            occupied.add(node.id)
        elif isinstance(node, ast.arg):
            occupied.add(node.arg)
        elif isinstance(node, ast.alias):
            occupied.add(node.asname or node.name.split('.')[0])
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            occupied.update(node.names)
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            occupied.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            occupied.add(node.rest)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            strings.append(node.value)
            occupied.update(re.findall(r'\w+', node.value))
    aliases: list[ast.alias] = []
    for name, items in candidates.items():
        alias = items[0]
        assert alias.asname is not None
        if len(items) == 1 and name not in occupied and not any(alias.asname in value for value in strings):
            aliases.append(alias)
    if not aliases:
        return source
    replacements = {alias.asname: alias.name for alias in aliases}
    capture_check = ImportAliasCaptureChecker({name: target for name, target in replacements.items() if name is not None})
    capture_check.visit(copy.deepcopy(tree))
    aliases = [alias for alias in aliases if alias.asname not in capture_check.conflicts]
    replacements = {alias.asname: alias.name for alias in aliases}
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    def offset(line: int, byte_column: int) -> int:
        return starts[line - 1] + len(lines[line - 1].encode('utf-8')[:byte_column].decode('utf-8'))

    edits: list[tuple[int, int, str]] = []
    for alias in aliases:
        assert alias.end_lineno is not None and alias.end_col_offset is not None
        edits.append((offset(alias.lineno, alias.col_offset) + len(alias.name), offset(alias.end_lineno, alias.end_col_offset), ''))
    import_edits = edits[:]
    previous = ''
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME and token.string in replacements and previous != '.':
            start = starts[token.start[0] - 1] + token.start[1]
            end = starts[token.end[0] - 1] + token.end[1]
            if not any(left <= start < right for left, right, _ in import_edits):
                edits.append((start, end, replacements[token.string]))
        if token.type not in (tokenize.NL, tokenize.COMMENT):
            previous = token.string
    for start, end, replacement in sorted(edits, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def is_cplib_module(name: str | None) -> bool:
    return name == 'cplib' or bool(name and name.startswith('cplib.'))


class ModuleSymbols:
    """Give each definition its own identity, following imports and re-exports."""

    def __init__(self, root: Path, main: ast.Module) -> None:
        self.root = root
        self.trees: dict[str, ast.Module] = {}
        self.paths: dict[str, Path] = {}
        self.bindings: dict[str, dict[str, Symbol]] = {}
        self.names: dict[Symbol, str] = {}
        self.submodule_imports: dict[Symbol, str] = {}
        requested: dict[str, set[str]] = {}
        for node in ast.walk(main):
            if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module):
                assert node.module is not None
                requested.setdefault(node.module, set()).update(alias.name for alias in node.names if alias.name != '*')
        pending = [node.module for node in ast.walk(main) if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module)]
        pending.extend(alias.name for node in ast.walk(main) if isinstance(node, ast.Import) for alias in node.names if is_cplib_module(alias.name))
        while pending:
            module = pending.pop()
            assert module is not None
            if module in self.trees:
                continue
            path = self.resolve_path(module)
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            self.paths[module] = path
            self.trees[module] = tree
            pending.extend(node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module))
            bindings: dict[str, Symbol] = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    bindings[node.name] = (module, node.name)
                elif is_simple_name_assignment(node):
                    for name in assignment_target_names(node):
                        bindings[name] = (module, name)
                elif isinstance(node, ast.ImportFrom) and node.module != '__future__':
                    for alias in node.names:
                        if alias.name == '*':
                            continue
                        origin = node.module or ''
                        symbol = (origin if is_cplib_module(origin) else '@from:' + origin, alias.name)
                        bindings[alias.asname or alias.name] = symbol
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        root_name = alias.name if alias.asname else alias.name.split('.')[0]
                        bindings[alias.asname or root_name] = ('@import', root_name)
            self.bindings[module] = bindings
            # Python first uses an existing package attribute, then attempts to
            # import a submodule. Do not mistake a same-named export for a file.
            if path.name == '__init__.py':
                for name in requested.get(module, set()) - bindings.keys():
                    submodule = f'{module}.{name}'
                    try:
                        self.resolve_path(submodule)
                    except FileNotFoundError:
                        continue
                    self.submodule_imports[module, name] = submodule
                    pending.append(submodule)

        redirects: dict[Symbol, Symbol] = {}
        for module, bindings in self.bindings.items():
            for name, symbol in bindings.items():
                if symbol != (module, name):
                    redirects[module, name] = symbol

        # Current modules use explicit imports. Star imports are resolved from
        # __all__ when available, otherwise from public module bindings.
        for module, tree in self.trees.items():
            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module) and any(alias.name == '*' for alias in node.names):
                    assert node.module is not None
                    for name in self.exports(node.module):
                        symbol = (node.module, name)
                        self.bindings[module][name] = symbol
                        redirects[module, name] = symbol

        def resolve(symbol: Symbol) -> Symbol:
            visited: set[Symbol] = set()
            while symbol in redirects:
                if symbol in visited:
                    raise ValueError(f'Cyclic import binding: {symbol}')
                visited.add(symbol)
                symbol = redirects[symbol]
            if is_cplib_module(symbol[0]) and symbol[1] not in self.bindings[symbol[0]]:
                raise ImportError(f'Cannot import {symbol[1]!r} from {symbol[0]!r}')
            return symbol

        for bindings in self.bindings.values():
            for name, symbol in bindings.items():
                bindings[name] = resolve(symbol)

        # Definitions whose bindings never change can be shared directly.
        # In particular, T_alias = T is not a TypeVar declaration to a type
        # checker. Mutable bindings must still use from-import snapshots.
        stable = {symbol for bindings in self.bindings.values() for symbol in bindings.values() if not is_cplib_module(symbol[0])}
        writes_by_module: dict[str, dict[str, int]] = {}
        for module, tree in self.trees.items():
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    stable.add((module, node.name))
                elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name) and node.value.func.id in ('TypeVar', 'ParamSpec', 'TypeVarTuple', 'NewType'):
                        stable.update((module, name) for name in assignment_target_names(node))
        for module, tree in self.trees.items():
            writes = ModuleBindingWrites()
            writes.visit(tree)
            writes_by_module[module] = writes.counts
            for name, count in writes.counts.items():
                symbol = self.bindings[module].get(name)
                if symbol is not None and count > 1:
                    stable.discard(symbol)
        # A single assignment such as Alias = SomeClass is stable when its
        # source binding is stable too. Do not merge aliases of mutable values.
        changed = True
        while changed:
            changed = False
            for module, tree in self.trees.items():
                for node in tree.body:
                    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and self.bindings[module].get(node.value.id) in stable:
                        for name in assignment_target_names(node):
                            symbol = (module, name)
                            if writes_by_module[module].get(name) == 1 and symbol not in stable:
                                stable.add(symbol)
                                changed = True
        mutated_attributes = {node.attr for tree in [main, *self.trees.values()] for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del))}
        stable = {symbol for symbol in stable if symbol[1] not in mutated_attributes}
        # Module objects expose writable attributes, including via setattr.
        # Keep their bindings separate from imported snapshots conservatively.
        if self.submodule_imports or any(isinstance(node, ast.Import) and any(is_cplib_module(alias.name) for alias in node.names) for node in ast.walk(main)):
            stable.clear()

        # A leading function-local import of an unchanged definition can use
        # the expanded global directly when that local name is never rebound.
        self.shared_local_imports: dict[str, set[tuple[int, int]]] = {}
        for module, tree in self.trees.items():
            shared: set[tuple[int, int]] = set()
            nested_functions = {id(child) for parent in ast.walk(tree) if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)) for child in ast.walk(parent) if child is not parent and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))}
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) or id(function) in nested_functions:
                    continue
                if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('locals', 'vars', 'eval', 'exec') for node in ast.walk(function)):
                    continue
                bound: dict[str, int] = {}
                for node in ast.walk(function):
                    names: list[str] = []
                    if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                        names = [node.id]
                    elif isinstance(node, ast.alias):
                        names = [node.asname or node.name]
                    elif isinstance(node, ast.arg):
                        names = [node.arg]
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        names = [node.name]
                    elif isinstance(node, (ast.Global, ast.Nonlocal)):
                        names = node.names
                    elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
                        names = [node.name]
                    elif isinstance(node, ast.MatchMapping) and node.rest:
                        names = [node.rest]
                    for name in names:
                        bound[name] = bound.get(name, 0) + 1
                for node in function.body:
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        continue
                    if not isinstance(node, ast.ImportFrom) or not is_cplib_module(node.module):
                        break
                    assert node.module is not None
                    if all(alias.name != '*' and alias.asname in (None, alias.name) and bound.get(alias.name) == 1 and self.bindings[node.module][alias.name] in stable for alias in node.names):
                        shared.add((node.lineno, node.col_offset))
            self.shared_local_imports[module] = shared

        identities = {symbol for bindings in self.bindings.values() for symbol in bindings.values()}
        builtin_names = {name for name in vars(builtins) if not name.startswith('_')}
        identities.update(('@from:builtins', name) for name in builtin_names)
        by_name: dict[str, set[Symbol]] = {}
        for symbol in identities:
            by_name.setdefault(symbol[1].split('.')[-1], set()).add(symbol)
        reserved: set[str] = set()
        initial_imports, _ = split_initial_import_block(main.body)
        initial_import_ids = {id(node) for node in initial_imports}
        for module, tree in self.trees.items():
            top_ids = {id(node) for node in tree.body}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module) and id(node) not in top_ids and (node.lineno, node.col_offset) not in self.shared_local_imports[module]:
                    reserved.update(alias.asname or alias.name for alias in node.names)
        for node in ast.walk(main):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                reserved.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                reserved.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        if is_cplib_module(node.module):
                            assert node.module is not None
                            reserved.update(self.exports(node.module))
                        continue
                    name = alias.asname or alias.name
                    if is_cplib_module(node.module):
                        assert node.module is not None
                        if (node.module, alias.name) in self.submodule_imports:
                            continue
                        if alias.name not in self.bindings[node.module]:
                            raise ImportError(f'Cannot import {alias.name!r} from {node.module!r}')
                        symbol = self.bindings[node.module][alias.name]
                        if id(node) not in initial_import_ids or symbol not in stable:
                            reserved.add(name)
                    else:
                        symbol = ('@from:' + (node.module or ''), alias.name)
                    by_name.setdefault(name, set()).add(symbol)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    if is_cplib_module(alias.name):
                        reserved.add(name)
                    else:
                        by_name.setdefault(name, set()).add(('@import', alias.name if alias.asname else name))
        occupied = reserved | set(by_name)
        for tree in [main, *self.trees.values()]:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    occupied.add(node.id)
                elif isinstance(node, ast.arg):
                    occupied.add(node.arg)
        for symbol in sorted(identities):
            base = symbol[1].split('.')[-1]
            if base not in reserved and len(by_name[base]) == 1:
                self.names[symbol] = base
                continue
            prefix = symbol[0].removeprefix('cplib.').replace('@', '').replace(':', '_').replace('.', '_')
            candidate = f'_cplib_{prefix}_{base}'
            suffix = 0
            while candidate in occupied:
                suffix += 1
                candidate = f'_cplib_{prefix}_{base}_{suffix}'
            occupied.add(candidate)
            self.names[symbol] = candidate
        self.occupied = occupied | set(self.names.values())
        owners: dict[Symbol, int] = {}
        for bindings in self.bindings.values():
            for symbol in bindings.values():
                owners[symbol] = owners.get(symbol, 0) + 1
        self.storage: dict[str, dict[str, str]] = {}
        for module, bindings in self.bindings.items():
            storage: dict[str, str] = {}
            for name, symbol in bindings.items():
                if symbol in stable or symbol == (module, name) or (not is_cplib_module(symbol[0]) and owners[symbol] == 1):
                    storage[name] = self.names[symbol]
                else:
                    prefix = module.removeprefix('cplib.').replace('.', '_')
                    storage[name] = self.allocate_name(f'_cplib_{prefix}_{name}')
            self.storage[module] = storage

    def allocate_name(self, prefix: str) -> str:
        candidate = prefix
        suffix = 0
        while candidate in self.occupied:
            suffix += 1
            candidate = f'{prefix}_{suffix}'
        self.occupied.add(candidate)
        return candidate

    def resolve_path(self, module: str) -> Path:
        relative = module.removeprefix('cplib').lstrip('.').replace('.', '/')
        for path in (self.root / (relative + '.py'), self.root / relative / '__init__.py'):
            if path.is_file():
                return path.resolve()
        raise FileNotFoundError(f'cplib module {module!r} not found')

    def exports(self, module: str) -> list[str]:
        for node in self.trees[module].body:
            if isinstance(node, ast.Assign) and '__all__' in assignment_target_names(node):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    names: list[str] = []
                    for item in node.value.elts:
                        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                            raise ValueError(f'Nonliteral __all__ in {module}')
                        names.append(item.value)
                    return names
        return [name for name in self.bindings[module] if not name.startswith('_')]

    def mapping(self, module: str) -> dict[str, str]:
        return self.storage[module]

    def rewrite(self, module: str) -> ast.Module:
        tree = copy.deepcopy(self.trees[module])
        mapping = self.mapping(module)
        builtin_mapping = {symbol[1]: name for symbol, name in self.names.items() if symbol[0] == '@from:builtins'}
        imported_names = {name: self.mapping(name) for name in self.trees}
        rewritten = GlobalNameRewriter({**builtin_mapping, **mapping}, imported_names, self.shared_local_imports[module]).visit(tree)
        assert isinstance(rewritten, ast.Module)
        body: list[ast.stmt] = []
        for node in rewritten.body:
            if isinstance(node, ast.ImportFrom) and is_cplib_module(node.module):
                assert node.module is not None
                aliases = [ast.alias(name=name) for name in self.exports(node.module)] if node.names[0].name == '*' else node.names
                for alias in aliases:
                    target = mapping[alias.asname or alias.name]
                    value = self.mapping(node.module)[alias.name]
                    if target == value:
                        continue
                    body.append(ast.copy_location(ast.Assign(targets=[ast.Name(id=target, ctx=ast.Store())], value=ast.Name(id=value, ctx=ast.Load())), node))
                continue
            elif isinstance(node, ast.ImportFrom) and node.module != '__future__':
                for alias in node.names:
                    binding = alias.asname or alias.name
                    target = mapping.get(binding, binding)
                    alias.asname = target if target != alias.name else None
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    binding = alias.asname or alias.name.split('.')[0]
                    target = mapping.get(binding, binding)
                    if target != binding or alias.asname:
                        alias.asname = target
            body.append(node)
        rewritten.body = body
        renamed_builtins = [ast.alias(name=name, asname=target) for name, target in builtin_mapping.items() if name != target and name not in mapping]
        if renamed_builtins:
            rewritten.body.insert(0, ast.ImportFrom(module='builtins', names=renamed_builtins, level=0))
        return ast.fix_missing_locations(rewritten)


class LocalBindings(ast.NodeVisitor):
    """Collect one lexical scope without descending into nested scopes."""

    def __init__(self) -> None:
        self.local_names: set[str] = set()
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.local_names.add(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.local_names.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.local_names.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        pass

    def visit_Import(self, node: ast.Import) -> None:
        self.local_names.update(alias.asname or alias.name.split('.')[0] for alias in node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.local_names.update(alias.asname or alias.name for alias in node.names)

    def visit_Global(self, node: ast.Global) -> None:
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocal_names.update(node.names)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            self.local_names.add(node.name)
        self.generic_visit(node)

    def comprehension(self, node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp) -> None:
        for generator in node.generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)

    visit_ListComp = comprehension
    visit_SetComp = comprehension
    visit_DictComp = comprehension
    visit_GeneratorExp = comprehension


class ModuleBindingWrites(ast.NodeVisitor):
    """Count module writes, including explicit globals inside nested scopes."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.scopes: list[set[str]] = []

    def bind(self, name: str) -> None:
        if not self.scopes or name in self.scopes[-1]:
            self.counts[name] = self.counts.get(name, 0) + 1

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.bind(node.id)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.bind(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.bind(alias.asname or alias.name)

    def body(self, statements: list[ast.stmt]) -> None:
        bindings = LocalBindings()
        for statement in statements:
            bindings.visit(statement)
        self.scopes.append(bindings.global_names)
        for statement in statements:
            self.visit(statement)
        self.scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.bind(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.visit(node.args)
        if node.returns is not None:
            self.visit(node.returns)
        self.body(node.body)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bind(node.name)
        for expression in [*node.decorator_list, *node.bases, *node.keywords]:
            self.visit(expression)
        self.body(node.body)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.visit(node.args)
        self.scopes.append(set())
        self.visit(node.body)
        self.scopes.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            self.bind(node.name)
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs | ast.MatchStar) -> None:
        if node.name is not None:
            self.bind(node.name)
        self.generic_visit(node)

    visit_MatchStar = visit_MatchAs

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest is not None:
            self.bind(node.rest)
        self.generic_visit(node)


class GlobalNameRewriter(ast.NodeTransformer):
    """Rename module bindings without renaming local variables or attributes."""

    def __init__(self, names: dict[str, str], imported_names: dict[str, dict[str, str]], shared_imports: set[tuple[int, int]] | None = None) -> None:
        self.names = names
        self.imported_names = imported_names
        self.scopes: list[tuple[bool, set[str], set[str]]] = []
        self.shared_imports = shared_imports or set()

    def shares_import(self, node: ast.stmt) -> bool:
        return isinstance(node, ast.ImportFrom) and node.module is not None and (node.lineno, node.col_offset) in self.shared_imports and all(self.imported_names[node.module][alias.name] == (alias.asname or alias.name) for alias in node.names)

    def global_name(self, name: str) -> str:
        if self.scopes and name in self.scopes[-1][2]:
            return self.names.get(name, name)
        for index in range(len(self.scopes) - 1, -1, -1):
            is_class, local_names, _ = self.scopes[index]
            if is_class and index != len(self.scopes) - 1:
                continue
            if name in local_names:
                return name
        return self.names.get(name, name)

    def bind_name(self, name: str) -> str:
        if self.scopes and self.scopes[-1][0] and name not in self.scopes[-1][2]:
            self.scopes[-1][1].add(name)
            return name
        return self.global_name(name)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self.global_name(node.id) if isinstance(node.ctx, ast.Load) else self.bind_name(node.id)
        return node

    def visit_Global(self, node: ast.Global) -> ast.Global:
        node.names = [self.names.get(name, name) for name in node.names]
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.stmt:
        if self.shares_import(node):
            return ast.copy_location(ast.Pass(), node)
        if not self.scopes or not is_cplib_module(node.module):
            return node
        assert node.module is not None
        bindings = self.imported_names[node.module]
        targets = [ast.Name(id=self.bind_name(alias.asname or alias.name), ctx=ast.Store()) for alias in node.names]
        values = [ast.Name(id=bindings[alias.name], ctx=ast.Load()) for alias in node.names]
        target = targets[0] if len(targets) == 1 else ast.Tuple(elts=list(targets), ctx=ast.Store())
        value = values[0] if len(values) == 1 else ast.Tuple(elts=list(values), ctx=ast.Load())
        return ast.copy_location(ast.Assign(targets=[target], value=value), node)

    def annotation(self, node: ast.expr | None) -> ast.expr | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            expression = ast.parse(node.value, mode='eval')
            rewritten = self.annotation(expression.body)
            assert rewritten is not None
            node.value = ast.unparse(rewritten)
            return node
        if isinstance(node, ast.Subscript):
            literal = isinstance(node.value, ast.Name) and node.value.id == 'Literal' or isinstance(node.value, ast.Attribute) and node.value.attr == 'Literal'
            node.value = self.visit_expression(node.value)
            if not literal:
                rewritten = self.annotation(node.slice)
                assert rewritten is not None
                node.slice = rewritten
            return node
        if isinstance(node, ast.Tuple):
            elements: list[ast.expr] = []
            for element in node.elts:
                rewritten = self.annotation(element)
                assert rewritten is not None
                elements.append(rewritten)
            node.elts = elements
            return node
        if node is not None:
            result = self.visit(node)
            assert isinstance(result, ast.expr)
            return result
        return None

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.annotation = self.annotation(node.annotation)
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        type_parameter = isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in ('TypeVar', 'ParamSpec', 'TypeVarTuple', 'NewType')
        node.value = self.visit_expression(node.value)
        node.targets = [self.visit_expression(target) for target in node.targets]
        if type_parameter and isinstance(node.value, ast.Call) and node.value.args and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            node.value.args[0] = ast.Constant(value=node.targets[0].id)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        if node.value is not None:
            node.value = self.visit_expression(node.value)
        target = self.visit(node.target)
        assert isinstance(target, (ast.Name, ast.Attribute, ast.Subscript))
        node.target = target
        annotation = self.annotation(node.annotation)
        assert annotation is not None
        node.annotation = annotation
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.FunctionDef | ast.AsyncFunctionDef:
        scope = LocalBindings()
        for statement in node.body:
            scope.visit(statement)
        for statement in node.body:
            if self.shares_import(statement):
                assert isinstance(statement, ast.ImportFrom)
                scope.local_names.difference_update(alias.name for alias in statement.names)
        node.decorator_list = [self.visit_expression(item) for item in node.decorator_list]
        args = self.visit(node.args)
        assert isinstance(args, ast.arguments)
        node.args = args
        node.returns = self.annotation(node.returns)
        node.name = self.bind_name(node.name)
        scope.local_names.update(arg.arg for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs])
        if node.args.vararg is not None:
            scope.local_names.add(node.args.vararg.arg)
        if node.args.kwarg is not None:
            scope.local_names.add(node.args.kwarg.arg)
        self.scopes.append((False, scope.local_names - scope.global_names - scope.nonlocal_names, scope.global_names))
        node.body = [self.visit_statement(item) for item in node.body]
        self.scopes.pop()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node.bases = [self.visit_expression(item) for item in node.bases]
        node.decorator_list = [self.visit_expression(item) for item in node.decorator_list]
        for keyword in node.keywords:
            keyword.value = self.visit_expression(keyword.value)
        scope = LocalBindings()
        for statement in node.body:
            scope.visit(statement)
        self.scopes.append((True, set(), scope.global_names))
        node.body = [self.visit_statement(item) for item in node.body]
        self.scopes.pop()
        node.name = self.bind_name(node.name)
        return node

    def visit_Lambda(self, node: ast.Lambda) -> ast.Lambda:
        args = self.visit(node.args)
        assert isinstance(args, ast.arguments)
        node.args = args
        scope = LocalBindings()
        scope.visit(node.body)
        scope.local_names.update(arg.arg for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs])
        if node.args.vararg is not None:
            scope.local_names.add(node.args.vararg.arg)
        if node.args.kwarg is not None:
            scope.local_names.add(node.args.kwarg.arg)
        self.scopes.append((False, scope.local_names, set()))
        node.body = self.visit_expression(node.body)
        self.scopes.pop()
        return node

    def comprehension(self, node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp) -> ast.expr:
        node.generators[0].iter = self.visit_expression(node.generators[0].iter)
        local_names = {item.id for generator in node.generators for item in ast.walk(generator.target) if isinstance(item, ast.Name)}
        self.scopes.append((False, local_names, set()))
        for index, generator in enumerate(node.generators):
            generator.target = self.visit_expression(generator.target)
            if index:
                generator.iter = self.visit_expression(generator.iter)
            generator.ifs = [self.visit_expression(item) for item in generator.ifs]
        if isinstance(node, ast.DictComp):
            node.key, node.value = self.visit_expression(node.key), self.visit_expression(node.value)
        else:
            node.elt = self.visit_expression(node.elt)
        self.scopes.pop()
        return node

    def visit_ListComp(self, node: ast.ListComp) -> ast.expr:
        return self.comprehension(node)

    def visit_SetComp(self, node: ast.SetComp) -> ast.expr:
        return self.comprehension(node)

    def visit_DictComp(self, node: ast.DictComp) -> ast.expr:
        return self.comprehension(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> ast.expr:
        return self.comprehension(node)

    def visit_Call(self, node: ast.Call) -> ast.Call:
        if isinstance(node.func, ast.Name) and node.func.id == 'TypeVar':
            for keyword in node.keywords:
                if keyword.arg == 'bound':
                    value = self.annotation(keyword.value)
                    assert value is not None
                    keyword.value = value
        self.generic_visit(node)
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.Subscript:
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'globals':
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                node.slice.value = self.names.get(node.slice.value, node.slice.value)
        self.generic_visit(node)
        return node

    def visit_expression(self, node: ast.expr) -> ast.expr:
        result = self.visit(node)
        assert isinstance(result, ast.expr)
        return result

    def visit_statement(self, node: ast.stmt) -> ast.stmt:
        result = self.visit(node)
        assert isinstance(result, ast.stmt)
        return result


class ImportAliasCaptureChecker(GlobalNameRewriter):
    """Detect short import names captured by a local or class binding."""

    def __init__(self, replacements: dict[str, str]) -> None:
        super().__init__({name: '_cplib_global_probe' for name in replacements.values()}, {})
        self.replacements = replacements
        self.conflicts: set[str] = set()

    def visit_Name(self, node: ast.Name) -> ast.Name:
        target = self.replacements.get(node.id)
        if target is not None and self.global_name(target) != '_cplib_global_probe':
            self.conflicts.add(node.id)
        return super().visit_Name(node)
