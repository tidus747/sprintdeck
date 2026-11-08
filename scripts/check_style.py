"""Reject U+2014 in repository text files without scanning local session data."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "node_modules", "__pycache__", ".session", "sessions", "imports", "exports", ".pytest_cache"}


def main():
    # Respect ignored files, and include newly authored files before their first commit.
    result = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=ROOT, capture_output=True)
    paths = [ROOT / path for path in result.stdout.decode("utf-8").split("\0") if path] if result.returncode == 0 else ROOT.rglob("*")
    errors = []
    for path in paths:
        if not path.is_file() or any(part in SKIP for part in path.relative_to(ROOT).parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        for number, line in enumerate(content.splitlines(), 1):
            if chr(0x2014) in line:
                errors.append(f"{path.relative_to(ROOT)}:{number}: U+2014 is forbidden; use a comma, colon, or full stop.")
    if errors:
        print("\n".join(errors))
        return 1
    print("Repository text style check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
