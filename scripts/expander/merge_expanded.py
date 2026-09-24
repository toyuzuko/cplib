#!/usr/bin/env python3
"""
Merge formatted library code with the main code whose imports were rewritten.

Input 1: original source file
Input 2: formatted library-only source
Input 3: raw expanded source with an explicit library/main boundary
"""

import ast
import re
import sys
from pathlib import Path

from ast_utils import LIBRARY_END_MARKER, find_initial_import_block_end_line, split_initial_import_block, type_checking_comments, unparse_with_comments
from module_symbols import is_cplib_module


def _dedupe_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _normalize_code_lines(items: list[str]) -> str:
    if not items:
        return ""
    return "".join(item if item.endswith("\n") else item + "\n" for item in items)


def _render_import_block(future_imports: list[str], regular_imports: list[str]) -> str:
    parts: list[str] = []

    if future_imports:
        parts.extend(_dedupe_preserving_order(future_imports))

    if regular_imports:
        if parts:
            parts.append("")
        parts.extend(_dedupe_preserving_order(regular_imports))

    return _normalize_code_lines(parts)


def _first_body_node(body: str) -> ast.stmt | None:
    stripped = body.lstrip("\n")
    if not stripped.strip():
        return None
    parsed = ast.parse(stripped)
    return parsed.body[0] if parsed.body else None


def _join_imports_and_body(import_block: str, body: str) -> str:
    body = body.lstrip("\n")
    if not import_block:
        return body
    if not body:
        return import_block

    first_node = _first_body_node(body)
    if isinstance(first_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        separator = "\n\n\n"
    else:
        separator = "\n\n"
    return import_block.rstrip("\n") + separator + body


def _extract_script_header(lines: list[str]) -> tuple[str, int]:
    header_lines: list[str] = []
    index = 0

    if lines and lines[0].startswith("#!"):
        header_lines.append(lines[0])
        index = 1

    coding_pattern = re.compile(r"^[ \t\f]*#.*coding[:=][ \t]*[-\w.]+")
    if index < len(lines) and coding_pattern.match(lines[index]):
        header_lines.append(lines[index])
        index += 1

    return "".join(header_lines), index


def _extract_non_cplib_imports(code: str) -> tuple[list[str], list[str]]:
    tree = ast.parse(code)
    import_block, _ = split_initial_import_block(tree.body)

    future_imports: list[str] = []
    regular_imports: list[str] = []
    comments = type_checking_comments(code)

    for node in import_block:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                future_imports.append(ast.unparse(node))
            elif not is_cplib_module(node.module):
                regular_imports.append(unparse_with_comments(node, comments))
            continue

        kept_aliases = [alias for alias in node.names if not is_cplib_module(alias.name)]
        if kept_aliases:
            regular_imports.append(unparse_with_comments(ast.copy_location(ast.Import(names=kept_aliases), node), comments))

    return future_imports, regular_imports


def merge_library_with_original_main(original_file: str, library_file: str, expanded_file: str) -> str:
    """Combine the library prefix and rewritten main, retaining the script header."""
    original_code = Path(original_file).read_text(encoding='utf-8')
    library_code = Path(library_file).read_text(encoding='utf-8')

    original_lines = original_code.splitlines(keepends=True)
    script_header, _ = _extract_script_header(original_lines)
    expanded_code = Path(expanded_file).read_text(encoding='utf-8')
    for node in ast.parse(expanded_code).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value == LIBRARY_END_MARKER:
            main_code = ''.join(expanded_code.splitlines(keepends=True)[node.end_lineno:])
            _, main_header_end = _extract_script_header(main_code.splitlines(keepends=True))
            main_code = ''.join(main_code.splitlines(keepends=True)[main_header_end:])
            break
    else:
        raise ValueError('Expanded source has no library boundary marker')

    library_lines = library_code.splitlines(keepends=True)
    library_import_block_end = find_initial_import_block_end_line(library_code)
    library_body = ''.join(library_lines[library_import_block_end:])

    original_future_imports, original_regular_imports = _extract_non_cplib_imports(original_code)
    library_future_imports, library_regular_imports = _extract_non_cplib_imports(library_code)

    merged_imports = _render_import_block(
        library_future_imports + original_future_imports,
        library_regular_imports + original_regular_imports,
    )
    library_code = _join_imports_and_body(merged_imports, library_body)

    # Removed imports can leave blank lines among the main's opening comments.
    # Normalize only that prefix; preserve spacing and string contents in code.
    main_lines = main_code.lstrip('\r\n').splitlines(keepends=True)
    prefix_end = next((i for i, line in enumerate(main_lines) if line.strip() and not line.lstrip().startswith('#')), len(main_lines))
    main_prefix = re.sub(r'(?m)(?:^[ \t]*\r?\n){3,}', '\n\n', ''.join(main_lines[:prefix_end]))
    main_code = main_prefix + ''.join(main_lines[prefix_end:])

    body = library_code.rstrip('\r\n') + '\n\n\n' + main_code if library_code and main_code else library_code + main_code
    if script_header and body and not body.startswith('\n'):
        body = '\n' + body

    return script_header + body


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: merge_expanded.py <original_file> <library_file> <expanded_file>", file=sys.stderr)
        sys.exit(1)

    original_file = Path(sys.argv[1])
    library_file = Path(sys.argv[2])

    if not original_file.exists():
        print(f"Error: Original file '{original_file}' not found", file=sys.stderr)
        sys.exit(1)

    if not library_file.exists():
        print(f"Error: Library file '{library_file}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        print(merge_library_with_original_main(str(original_file), str(library_file), sys.argv[3]), end='')
    except Exception as exc:
        import traceback

        traceback.print_exc()
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
