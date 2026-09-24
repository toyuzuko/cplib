"""Run public verification-helper with conservative Python dependencies."""

import functools
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp
from typing import Any
from unittest.mock import patch

from onlinejudge_verify.languages.python import PythonLanguage
import onlinejudge_verify.verify as verifier
from onlinejudge_verify.main import get_parser, main


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


class VerificationReport:
    """Collect structured oj measurements without parsing terminal output."""

    def __init__(self, arguments: list[str]) -> None:
        self.started = time.perf_counter()
        self.root = Path.cwd()
        parent = self.root / 'tmp' / 'verify'
        parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().strftime('%Y%m%d-%H%M%S-')
        self.directory = Path(mkdtemp(prefix=stamp, dir=parent))
        self.data: dict[str, Any] = {
            'schema_version': 1,
            'started_at': datetime.now().astimezone().isoformat(),
            'arguments': arguments,
            'python': f'{platform.python_implementation()} {platform.python_version()}',
            'platform': platform.platform(),
            'files': [],
        }
        self.current: dict[str, Any] | None = None
        self.original_verify_file = verifier.verify_file
        self.original_exec_command = verifier.exec_command

    def verify_file(self, path: Path, *, compilers: list[str], tle: float, jobs: int) -> bool | None:
        """Record an executed verification file, including download failures."""
        resolved = path.resolve()
        name = str(resolved.relative_to(self.root)) if resolved.is_relative_to(self.root) else str(path)
        record: dict[str, Any] = {'path': name, 'status': 'ERROR', 'cases': [], 'measurement_errors': []}
        self.data['files'].append(record)
        self.current = record
        start = time.perf_counter()
        try:
            result = self.original_verify_file(path, compilers=compilers, tle=tle, jobs=jobs)
            record['status'] = 'PASSED' if result is True else 'FAILED' if result is False else 'SKIPPED'
            return result
        except KeyboardInterrupt:
            record['status'] = 'INTERRUPTED'
            raise
        finally:
            record['wall_time_seconds'] = time.perf_counter() - start
            self.current = None

    def exec_command(self, command: list[str]) -> None:
        """Ask oj test for its per-case JSON and retain only measurements."""
        if len(command) < 2 or Path(command[0]).name != 'oj' or command[1] != 'test' or self.current is None:
            self.original_exec_command(command)
            return
        record = self.current
        raw = self.directory / 'cases.pending.json'
        try:
            self.original_exec_command([*command, '--log-file', str(raw)])
        finally:
            try:
                if not raw.exists():
                    record['measurement_errors'].append('oj test did not produce case measurements.')
                else:
                    cases = json.loads(raw.read_text())
                    for case in cases:
                        memory = case['memory']
                        record['cases'].append({
                            'name': case['testcase']['name'],
                            'status': case['status'],
                            'exit_code': case['exitcode'],
                            'time_seconds': case['elapsed'],
                            # oj stores GNU time's peak RSS (KiB) divided by 1000.
                            'memory_mib': None if memory is None else memory * 1000 / 1024,
                        })
            except (OSError, ValueError, KeyError, TypeError) as exc:
                record['measurement_errors'].append(f'Could not read case measurements: {exc}')
            finally:
                raw.unlink(missing_ok=True)

    def finish(self, exit_code: int) -> None:
        """Write machine-readable results and a per-file Markdown summary."""
        self.data.update({
            'finished_at': datetime.now().astimezone().isoformat(),
            'wall_time_seconds': time.perf_counter() - self.started,
            'exit_code': exit_code,
        })
        lines = [
            '# Verification results', '',
            f"Started: {self.data['started_at']}",
            f"Python: {self.data['python']}",
            f"Exit code: {exit_code}",
            f"Wall time (including setup): {self.data['wall_time_seconds']:.3f} s", '',
            'Case times are in seconds; memory is peak RSS in MiB.',
            'Missing measurements are shown as `—` (JSON: null).',
            'Files skipped by the verification cache are not measured or listed.', '',
            '| File | Result | Cases | Verdicts | Max time (s) | Mean time (s) | Max memory (MiB) |',
            '| --- | --- | ---: | --- | ---: | ---: | ---: |',
        ]
        warnings: list[str] = []
        for record in self.data['files']:
            cases = record['cases']
            times = [case['time_seconds'] for case in cases if case['time_seconds'] is not None]
            memories = [case['memory_mib'] for case in cases if case['memory_mib'] is not None]
            counts = dict(sorted(Counter(case['status'] for case in cases).items()))
            stats = {
                'case_count': len(cases), 'verdicts': counts,
                'max_time_seconds': max(times, default=None),
                'mean_time_seconds': sum(times) / len(times) if times else None,
                'max_memory_mib': max(memories, default=None),
            }
            record['summary'] = stats
            values = [stats['max_time_seconds'], stats['mean_time_seconds'], stats['max_memory_mib']]
            cells = ['—' if value is None else f'{value:.6f}' for value in values]
            name = record['path'].replace('|', '\\|').replace('`', '\\`').replace('\n', ' ')
            verdicts = ', '.join(f'{status}: {count}' for status, count in counts.items()) or '—'
            lines.append(f"| `{name}` | {record['status']} | {len(cases)} | {verdicts} | {' | '.join(cells)} |")
            for error in record['measurement_errors']:
                print(f"Warning: {record['path']}: {error}", file=sys.stderr)
                warnings.append(f'Warning for `{name}`: {error}')
        if not self.data['files']:
            lines += ['', 'No test files were executed (cached/skipped or none selected).']
        for warning in warnings:
            lines += ['', warning]
        (self.directory / 'results.json').write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (self.directory / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f'Verification statistics: {self.directory.relative_to(self.root)}', file=sys.stderr)


def run() -> None:
    """Run verification with conservative dependencies and saved measurements."""
    args = sys.argv[1:]
    parsed = get_parser().parse_args(args)
    if parsed.subcommand == 'all':
        args = ['--config-file', str(parsed.config_file), 'run', '--jobs', str(parsed.jobs), '--timeout', str(parsed.timeout), '--tle', str(parsed.tle)]
    if parsed.subcommand not in ('run', 'all'):
        main(args=args)
        return
    report = VerificationReport(sys.argv[1:])
    exit_code = 0
    try:
        with patch.object(PythonLanguage, 'list_dependencies', list_dependencies), patch.object(verifier, 'verify_file', report.verify_file), patch.object(verifier, 'exec_command', report.exec_command):
            main(args=args)
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 0 if exc.code is None else 1
        raise
    except KeyboardInterrupt:
        exit_code = 130
        raise
    except BaseException:
        exit_code = 1
        raise
    finally:
        report.finish(exit_code)


if __name__ == '__main__':
    run()
