#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CPLIB = ROOT / 'cplib'
SIGNATURE_LIMIT = 96

PACKAGES: dict[str, str] = {
    'algorithm': '`cplib.algorithm` contains common competitive-programming algorithms.',
    'datastructure': '`cplib.datastructure` contains data structure implementations.',
    'geometry': '`cplib.geometry` contains integer, rational, and floating-point geometry algorithms.',
    'graph': '`cplib.graph` contains graph and tree algorithms.\n\nUse `cplib.graph` as the common import entry point for graph and tree APIs. Direct imports from individual modules are also supported.\n\n- `core`: graph and tree containers; `base`: shared types.\n- `walk`: DFS, cycles, and walks; `reachability`: SCC, DAG order, reachability, and dominators.\n- `lowlink`: undirected decompositions and compressed forests.\n- `tree`: static tree algorithms; `treedecomp`: decompositions and LCA; `treequery`: queries; `treedp`: rerooting and fixed-root tree DP.\n- `linkcut` and `eulertourtree`: dynamic forests; `toptree`: static and dynamic top-tree DP; `connectivity`: dynamic graph connectivity.\n\n`TopTree` supports dynamic tree DP with a commutative rake monoid, without inverses. `RerootingLinkCutTree` is an alternative when inverses are available. All top-tree variants live in `toptree`:\n\n| Payloads | Fixed topology and root | Dynamic forest |\n| --- | --- | --- |\n| Vertices | `StaticTopTree` | `TopTree` |\n| Vertices and edges | `StaticTopTreeWithEdges` | `TopTreeWithEdges` |\n\nThe vertex variants share `point_identity`, `add_vertex(point, value)`, `add_edge(path)`, `rake`, `compress`, and `set`/`get`. The edge variants instead share `vertex_cluster(point, vertex_value)`, `edge_cluster(point, edge_value)`, and `set_vertex`/`get_vertex`/`set_edge`/`get_edge`. Both static constructors take a built `Tree`; the dynamic edge constructor takes endpoint pairs in edge-ID order. Dynamic edge slots are detached with `cut_edge(edge_id)` and reused with `link_edge(edge_id, child, parent)`.\n\nStatic `tree_value()` uses the fixed root; dynamic `tree_value(vertex)` changes the represented root. Subtree results exclude the incoming parent edge. Dynamic `path_cluster_value(u, v)` includes off-path branches. Callbacks must define a consistent DP across decompositions; only the static versions permit noncommutative rake with fixed light-child order.\n\n```python\nfrom cplib.graph import EulerTourTree, HeavyLightDecomposition, LinkCutTree, StaticTopTree, TopTree\n```',
    'heuristic': '`cplib.heuristic` contains utilities for heuristic and optimization problems.',
    'mathematics': '`cplib.mathematics` contains number-theoretic and algebraic algorithms.',
    'sequence': '`cplib.sequence` contains sequence, range-query, and permutation algorithms.',
    'string': '`cplib.string` contains string algorithms and data structures.',
    'tools': '`cplib.tools` contains utility code for I/O, testing, and shared types.',
}


@dataclass(frozen=True)
class Api:
    package: str
    module: str
    name: str
    kind: str
    signature: str
    summary: str
    complexity: str
    lineno: int

    @property
    def key(self) -> str:
        return f'{self.package}/{self.module}::{self.name}'


def public_modules(package_dir: Path) -> list[Path]:
    modules = []
    for path in sorted(package_dir.glob('*.py')):
        if path.name == '__init__.py':
            continue
        modules.append(path)
    return modules


def annotation_text(node: ast.AST | None) -> str:
    if node is None:
        return ''
    return ast.unparse(node).replace('\n', ' ')


def default_text(node: ast.AST) -> str:
    return ast.unparse(node).replace('\n', ' ')


def format_arg(arg: ast.arg, default: ast.AST | None = None) -> str:
    text = arg.arg
    ann = annotation_text(arg.annotation)
    if ann:
        text += f': {ann}'
    if default is not None:
        text += f' = {default_text(default)}'
    return text


def function_signature(name: str, node: ast.FunctionDef | ast.AsyncFunctionDef, *, drop_self: bool = False, include_return: bool = True) -> str:
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    if drop_self and positional and positional[0].arg in {'self', 'cls'}:
        positional = positional[1:]

    defaults: list[ast.AST | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parts = [format_arg(arg, default) for arg, default in zip(positional, defaults)]

    posonly_count = len(args.posonlyargs)
    if drop_self and node.args.posonlyargs and node.args.posonlyargs[0].arg in {'self', 'cls'}:
        posonly_count -= 1
    if posonly_count > 0:
        parts.insert(posonly_count, '/')

    if args.vararg is not None:
        parts.append('*' + format_arg(args.vararg))
    elif args.kwonlyargs:
        parts.append('*')

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        parts.append(format_arg(arg, default))

    if args.kwarg is not None:
        parts.append('**' + format_arg(args.kwarg))

    signature = f'{name}({", ".join(parts)})'
    ret = annotation_text(node.returns)
    if include_return and ret:
        signature += f' -> {ret}'
    return truncate(signature)


def class_signature(node: ast.ClassDef) -> str:
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == '__init__':
            return function_signature(node.name, item, drop_self=True, include_return=False)
    return f'{node.name}(...)'


def truncate(text: str) -> str:
    text = ' '.join(text.split())
    if len(text) <= SIGNATURE_LIMIT:
        return text
    return text[: SIGNATURE_LIMIT - 1].rstrip() + '…'


def doc_summary(doc: str | None) -> str:
    if not doc:
        return ''
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line
    return ''


def extract_complexity(doc: str | None, label: str) -> str:
    if not doc:
        return ''
    lines = doc.splitlines()
    pattern = re.compile(rf'^\s*{re.escape(label)} Complexit(?:y|ies):\s*(.*)$')
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        parts = [cleanup_complexity(match.group(1))] if match.group(1).strip() else []
        indent = len(line) - len(line.lstrip())
        for next_line in lines[i + 1:]:
            if not next_line.strip():
                continue
            if len(next_line) - len(next_line.lstrip()) <= indent:
                break
            stripped = next_line.strip()
            if parts and re.match(r'^[-*]\s', stripped):
                parts[-1] += ';'
            parts.append(cleanup_complexity(stripped))
        return ' '.join(parts)
    return ''


def cleanup_complexity(text: str) -> str:
    text = text.strip()
    if not text:
        return ''
    text = re.sub(r'^[-*]\s*', '', text)
    return text


def extract_apis(package: str, module_path: Path) -> list[Api]:
    tree = ast.parse(module_path.read_text(encoding='utf-8'), filename=str(module_path))
    apis: list[Api] = []
    for item in tree.body:
        if isinstance(item, ast.ClassDef):
            if item.name.startswith('_'):
                continue
            doc = ast.get_docstring(item, clean=True)
            apis.append(Api(
                package=package,
                module=module_path.name,
                name=item.name,
                kind='class',
                signature=class_signature(item),
                summary=doc_summary(doc),
                complexity=extract_complexity(doc, 'Space'),
                lineno=item.lineno,
            ))
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name.startswith('_'):
                continue
            doc = ast.get_docstring(item, clean=True)
            apis.append(Api(
                package=package,
                module=module_path.name,
                name=item.name,
                kind='function',
                signature=function_signature(item.name, item),
                summary=doc_summary(doc),
                complexity=extract_complexity(doc, 'Time'),
                lineno=item.lineno,
            ))
    return apis


def collect() -> dict[str, dict[str, list[Api]]]:
    packages: dict[str, dict[str, list[Api]]] = {}
    for package in PACKAGES:
        package_dir = CPLIB / package
        modules: dict[str, list[Api]] = {}
        for module_path in public_modules(package_dir):
            modules[module_path.name] = extract_apis(package, module_path)
        packages[package] = modules
    return packages


def escape_cell(text: str) -> str:
    text = text or '—'
    text = text.replace('\n', ' ')
    text = text.replace('|', '\\|')
    return text


def render_package(package: str, modules: dict[str, list[Api]]) -> str:
    lines: list[str] = [
        f'# cplib.{package}',
        '',
        PACKAGES[package],
        '',
        '## Modules',
        '',
    ]
    headers = ('API', 'Kind', 'Signature', 'Summary', 'Complexity')

    for module_name in sorted(modules):
        apis = modules[module_name]
        lines += [
            f'### `{module_name}`',
            '',
            f'| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |',
            '| --- | --- | --- | --- | --- |',
        ]
        for api in apis:
            complexity_kind = 'Space' if api.kind == 'class' else 'Time'
            complexity = f'{complexity_kind}: {api.complexity}' if api.complexity else ''
            lines.append(
                f'| `{escape_cell(api.name)}` | {api.kind} | `{escape_cell(api.signature)}` | {escape_cell(api.summary)} | {escape_cell(complexity)} |'
            )
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def all_apis(packages: dict[str, dict[str, list[Api]]]) -> Iterable[Api]:
    for package in PACKAGES:
        for module_name in sorted(packages[package]):
            yield from packages[package][module_name]


def write_readmes(packages: dict[str, dict[str, list[Api]]]) -> None:
    for package, modules in packages.items():
        package_dir = CPLIB / package
        (package_dir / 'README.md').write_text(render_package(package, modules), encoding='utf-8')


def report_missing_complexity(packages: dict[str, dict[str, list[Api]]]) -> list[str]:
    return [api.key for api in all_apis(packages) if not api.complexity]


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate concise module READMEs from cplib source docstrings.')
    parser.add_argument('--report-missing-complexity', action='store_true', help='List public APIs whose primary complexity section could not be parsed.')
    args = parser.parse_args()

    packages = collect()

    if args.report_missing_complexity:
        missing = report_missing_complexity(packages)
        for key in missing:
            print(key)
        print(f'missing primary complexities: {len(missing)}')
        return 1 if missing else 0

    write_readmes(packages)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
