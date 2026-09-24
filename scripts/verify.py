"""Run public verification-helper with conservative Python dependencies."""

import functools
import sys
from pathlib import Path

from onlinejudge_verify.languages.python import PythonLanguage
from onlinejudge_verify.main import main


@functools.lru_cache(maxsize=None)
def repository_dependencies(basedir: Path) -> tuple[Path, ...]:
    """Collect sources and tool configuration once per verification process."""
    paths = set()
    for directory in ('cplib', 'test', 'scripts'):
        root = basedir / directory
        if not root.is_dir():
            continue
        paths.add(root)
        for path in root.rglob('*.py'):
            paths.add(path)
            # Directory timestamps also invalidate results after source removal.
            paths.update(parent for parent in path.parents if root == parent or root in parent.parents)
    for name in ('pyproject.toml', 'uv.lock', '.python-version', 'verify.sh'):
        path = basedir / name
        if path.is_file():
            paths.add(path)
    return tuple(sorted(path.resolve() for path in paths if path.exists()))


def list_dependencies(self: PythonLanguage, path: Path, *, basedir: Path) -> list[Path]:
    """Invalidate verification results whenever any repository source changes."""
    return sorted(set(repository_dependencies(basedir.resolve())) | {path.resolve()})


def run() -> None:
    """Run verification without importlab analysis or documentation publishing."""
    PythonLanguage.list_dependencies = list_dependencies
    args = sys.argv[1:]
    if args and args[0] == 'all':
        args[0] = 'run'
    main(args=args)


if __name__ == '__main__':
    run()
