from __future__ import annotations

import argparse
import re
from pathlib import Path


TARGET_EXTENSIONS = {".html", ".js", ".py", ".md", ".webmanifest", ".json", ".txt"}
DEFAULT_ROOTS = [
    Path("services/core/app"),
    Path("docs"),
]

# Typical UTF-8 bytes that were decoded as CP1251 or similar.
# This includes the common "Р/С" mojibake letters plus the Cyrillic
# characters that frequently appear in the corrupted output and are not
# used in normal Russian text.
SUSPICIOUS_CHARS = set(
    "РСЂ‚„…†‡‰‹›Â"
    "ЀЁЂЃЄЅІЇЈЉЊЋЌЎЏ"
    "ѐёђѓєѕіїјљњћќўџ"
)
# The broken chunks are usually contiguous runs of these characters.
BROKEN_RUN_RE = re.compile(r"[РСЂЃЄЅІЇЈЉЊЋЌЎЏѐёђѓєѕіїјљњћќўџÂâ‚„…†‡‰‹›]{2,}")


def suspicious_score(token: str) -> int:
    return sum(1 for ch in token if ch in SUSPICIOUS_CHARS)


def convert_token(token: str) -> str:
    try:
        converted = token.encode("cp1251").decode("utf-8")
    except Exception:
        return token
    return converted


def fix_text(text: str) -> tuple[str, int]:
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        chunk = match.group(0)
        converted = convert_token(chunk)
        if converted != chunk and suspicious_score(converted) < suspicious_score(chunk):
            changed += 1
            return converted
        return chunk

    return BROKEN_RUN_RE.sub(repl, text), changed


def should_process(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TARGET_EXTENSIONS


def iter_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if should_process(root):
                files.append(root)
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if should_process(path):
                files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix common mojibake tokens in text files.")
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to process")
    args = parser.parse_args()

    roots = args.paths or DEFAULT_ROOTS
    files = iter_files(list(roots))
    total_files = 0
    total_tokens = 0

    for path in files:
        text = path.read_text(encoding="utf-8")
        fixed, changed = fix_text(text)
        if changed:
            path.write_text(fixed, encoding="utf-8", newline="\n")
            total_files += 1
            total_tokens += changed
            print(f"{path}: fixed {changed} tokens")

    print(f"done: {total_files} files, {total_tokens} token replacements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
