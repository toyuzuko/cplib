#!/usr/bin/env python3
"""
Shared AST helpers for the expander pipeline.
"""

import ast
import io
import tokenize
from typing import Sequence, Set

LIBRARY_END_MARKER = '__cplib_expander_library_end__'


def type_checking_comments(source: str) -> dict[int, str]:
    """Collect inline type-checker directives, excluding text in strings."""
    return {token.start[0]: token.string for token in tokenize.generate_tokens(io.StringIO(source).readline) if token.type == tokenize.COMMENT and ('pyright: ignore' in token.string or 'type: ignore' in token.string)}


def unparse_with_comments(node: ast.AST, comments: dict[int, str]) -> str:
    """Unparse a rewritten node while retaining its statement directives."""
    code = ast.unparse(node)
    if not comments:
        return code
    original = [item for item in ast.walk(node) if isinstance(item, ast.stmt)]
    emitted = [item for item in ast.walk(ast.parse(code)) if isinstance(item, ast.stmt)]
    lines = code.splitlines()
    for before, after in zip(original, emitted):
        first = getattr(before, 'lineno', 0)
        last = getattr(before, 'end_lineno', first)
        # Compound-statement directives apply to the header, not the body.
        compound = isinstance(before, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Try, ast.Match))
        source_line = first if compound else last
        comment = comments.get(source_line)
        if comment is not None:
            line = after.lineno if compound else (after.end_lineno or after.lineno)
            if comment not in lines[line - 1]:
                lines[line - 1] += '  ' + comment
    return '\n'.join(lines)


def extract_loaded_names(node: ast.AST) -> Set[str]:
    """Extract names referenced in load context from an AST node."""

    class NameExtractor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.names: Set[str] = set()

        def _add_identifier_string(self, node: ast.AST) -> None:
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.isidentifier()
            ):
                self.names.add(node.value)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Load):
                self.names.add(node.id)
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if isinstance(node.value, ast.Name):
                self.names.add(node.value.id)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name):
                self.names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                self.names.add(node.func.value.id)
            if isinstance(node.func, ast.Name) and node.func.id == 'TypeVar':
                for keyword in node.keywords:
                    if keyword.arg in {'bound', 'constraints'}:
                        self._add_identifier_string(keyword.value)
            self.generic_visit(node)

        def visit_Subscript(self, node: ast.Subscript) -> None:
            if isinstance(node.slice, ast.Name):
                self.names.add(node.slice.id)
            self.generic_visit(node)

    extractor = NameExtractor()
    extractor.visit(node)
    return extractor.names


def is_module_docstring(node: ast.stmt) -> bool:
    """Return whether the node is the module docstring expression."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def assignment_target_names(node: ast.AST) -> list[str]:
    """Return simple name targets from an assignment."""
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def is_simple_name_assignment(node: ast.AST) -> bool:
    """Return whether the node assigns to one or more simple module-level names."""
    if isinstance(node, ast.Assign):
        return bool(node.targets) and all(isinstance(target, ast.Name) for target in node.targets)
    if isinstance(node, ast.AnnAssign):
        return isinstance(node.target, ast.Name) and node.value is not None
    return False


def split_initial_import_block(body: Sequence[ast.stmt]) -> tuple[list[ast.stmt], list[ast.stmt]]:
    """Split a module body into the leading docstring/import block and the remaining body."""
    index = 0
    if body and is_module_docstring(body[0]):
        index = 1

    while index < len(body) and isinstance(body[index], (ast.Import, ast.ImportFrom)):
        index += 1

    return list(body[:index]), list(body[index:])


def find_initial_import_block_end_line(code: str) -> int:
    """Find the line number after the initial contiguous import block."""
    tree = ast.parse(code)
    import_block, _ = split_initial_import_block(tree.body)

    end_line = 0
    for node in import_block:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end_line = max(end_line, node.end_lineno or 0)

    return end_line
