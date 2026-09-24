"""Run docstring examples with a separate interpreter for each module."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import doctest
import importlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RESULT_PREFIX = 'DOCTEST_RESULT='


def example_modules() -> list[str]:
    modules = []
    for path in sorted((ROOT / 'cplib').rglob('*.py')):
        # FastIO configures stdin/stdout at import; templates are user programs.
        if path.name in ('__init__.py', 'fastio.py') or 'templates' in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'))
        docs = [ast.get_docstring(node) or '' for node in ast.walk(tree) if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
        if any('>>>' in doc for doc in docs):
            modules.append('.'.join(path.relative_to(ROOT).with_suffix('').parts))
    return modules


def run_module(module: str) -> tuple[str, int, int, str]:
    try:
        result = subprocess.run(
            [sys.executable, '-B', str(Path(__file__).resolve()), '--module', module],
            cwd=ROOT,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return module, 0, 1, 'Module exceeded the 60-second limit.'
    report, separator, payload = result.stdout.rpartition(RESULT_PREFIX)
    if not separator:
        return module, 0, 1, result.stdout + result.stderr
    attempted, failed = json.loads(payload)
    if result.returncode and not failed:
        failed = 1
    return module, attempted, failed, report + (result.stderr if failed else '')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', help='Run examples from one importable cplib module.')
    args = parser.parse_args()
    if args.module:
        sys.path.insert(0, str(ROOT))
        random.seed(0)
        module = importlib.import_module(args.module)
        result = doctest.testmod(module)
        print(RESULT_PREFIX + json.dumps([result.attempted, result.failed]))
        return int(bool(result.failed))

    modules = example_modules()
    attempted = failed = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        for module, count, failures, output in pool.map(run_module, modules):
            attempted += count
            failed += failures
            if failures:
                print(f'FAIL: {module}\n{output}')
    print(f'{len(modules)} modules, {attempted} examples, {failed} failures')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
