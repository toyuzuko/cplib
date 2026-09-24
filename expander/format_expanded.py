#!/usr/bin/env python3
"""
Format the extracted library block for competitive programming.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def resolve_tool(cmd: str) -> str | None:
    """Prefer formatter executables from the active interpreter's environment."""
    scripts_dir = Path(sys.executable).parent
    local_cmd = scripts_dir / cmd
    if local_cmd.exists():
        return str(local_cmd)
    if scripts_dir.parent.name == ".venv":
        return None
    return cmd


def run_command(cmd: list[str], input_file: str) -> bool:
    """Run a command and return whether it succeeded."""
    try:
        executable = resolve_tool(cmd[0])
        if executable is None:
            print(
                f"Error: {cmd[0]} is not installed in the project virtualenv. "
                f"Install dev dependencies before formatting.",
                file=sys.stderr,
            )
            return False
        result = subprocess.run([executable, *cmd[1:], input_file], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running {cmd[0]}:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        print(f"Error: {cmd[0]} not found. Please install it with: pip install {cmd[0]}", file=sys.stderr)
        return False


def format_code(input_file: str, output_file: str | None = None) -> bool:
    """Format Python code using autoflake, isort, and black."""

    # Create a temporary file for in-place operations
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp_path = tmp.name
        # Copy input to temp file
        shutil.copy2(input_file, tmp_path)

    try:
        # Definitions have already been selected by dependency analysis.
        # Keep executable assignments and dictionary entries: removing them
        # could suppress exceptions or other observable effects.
        print("Running autoflake...", file=sys.stderr)
        if not run_command([
            'autoflake',
            '--in-place',
            '--remove-all-unused-imports',
        ], tmp_path):
            return False

        # 2. Sort imports
        print("Running isort...", file=sys.stderr)
        if not run_command([
            'isort',
            '--profile', 'black',  # Compatible with black
            '--float-to-top',      # Float all imports to top
            '--line-length', '999999',  # No line length limit for imports
        ], tmp_path):
            return False

        # 3. Format with black
        print("Running black...", file=sys.stderr)
        if not run_command([
            'black',
            '--line-length', '999999',  # 行の文字数制限なし（ハードコードされた数列のため）
            '--skip-string-normalization',  # Keep original quotes
            '--skip-magic-trailing-comma',  # Keep original comma placement
        ], tmp_path):
            return False

        # Copy result to output
        if output_file:
            shutil.copy2(tmp_path, output_file)
            print(f"Formatted code written to: {output_file}", file=sys.stderr)
        else:
            # Print to stdout
            with open(tmp_path, 'r') as f:
                print(f.read(), end='')

        return True

    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


def main() -> None:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: format_expanded.py <input_file> [output_file]", file=sys.stderr)
        print("  If output_file is not specified, output will be written to stdout", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else None

    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)

    if not format_code(input_file, output_file):
        sys.exit(1)


if __name__ == "__main__":
    main()
