"""Compares the token count of tracked prompt files (see .github/prompt-budget.yaml)
between a base ref and the current working tree, using Anthropic's token-counting
API for exact counts. Reports both per-file and aggregate growth; which one
actually fails the check is controlled by `decision_maker` in the config.

Usage:
    poe check-prompt-budget [--base-ref <sha-or-ref>]
    python .github/scripts/check_prompt_budget.py --base-ref <sha-or-ref>
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

import httpx
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / ".github" / "prompt-budget.yaml"
COUNT_TOKENS_URL = "https://api.anthropic.com/v1/messages/count_tokens"
DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_BASE_REF = "main"
DECISION_MAKERS = ("per_file", "aggregate")
# Per file does token comparison on each file
# Aggregate does comparison token comparison on the combination of all files

from dotenv import load_dotenv


load_dotenv()


def glob_to_regex(pattern: str) -> re.Pattern:
    """Translates a subset of glob syntax (*, **, **/, ?) to a regex, char by char
    to avoid the "*.*" substring collisions that a sequence of str.replace() calls
    would introduce."""
    i, n = 0, len(pattern)
    parts = []
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                if i + 2 < n and pattern[i + 2] == "/":
                    parts.append("(?:.*/)?")
                    i += 3
                else:
                    parts.append(".*")
                    i += 2
            else:
                parts.append("[^/]*")
                i += 1
        elif c == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(parts) + "$")


def head_files_for_pattern(pattern: str) -> set[str]:
    matches = glob.glob(pattern, recursive=True, root_dir=REPO_ROOT)
    return {m for m in matches if (REPO_ROOT / m).is_file()}


def base_files_for_pattern(pattern: str, base_ref: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base_ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    regex = glob_to_regex(pattern)
    return {line for line in result.stdout.splitlines() if regex.match(line)}


def read_base_content(path: str, base_ref: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{base_ref}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else ""


def read_head_content(path: str) -> str:
    full_path = REPO_ROOT / path
    return full_path.read_text() if full_path.is_file() else ""


def count_tokens(text: str, api_key: str, model: str) -> int:
    if not text.strip():
        return 0
    response = httpx.post(
        COUNT_TOKENS_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={"model": model, "messages": [{"role": "user", "content": text}]},
        timeout=30,
    )
    if response.status_code >= 400:
        print(
            f"Anthropic API error {response.status_code}: {response.text}",
            file=sys.stderr,
        )
    response.raise_for_status()
    return response.json()["input_tokens"]


def format_growth(base_tokens: int, head_tokens: int) -> str:
    if base_tokens == 0:
        return "new file" if head_tokens > 0 else "+0.0%"
    return f"{(head_tokens - base_tokens) / base_tokens * 100:+.1f}%"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default=DEFAULT_BASE_REF)
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set; cannot count tokens.", file=sys.stderr)
        return 1

    config = yaml.safe_load(CONFIG_PATH.read_text())
    threshold_percent = config["threshold_percent"]
    min_token_floor = config.get("min_token_floor", 0)
    model = config.get("model", DEFAULT_MODEL)
    decision_maker = config.get("decision_maker", "per_file")
    if decision_maker not in DECISION_MAKERS:
        print(
            f"decision_maker must be one of {DECISION_MAKERS}, got {decision_maker!r}",
            file=sys.stderr,
        )
        return 1

    tracked_paths: set[str] = set()
    for pattern in config["paths"]:
        tracked_paths |= head_files_for_pattern(pattern)
        tracked_paths |= base_files_for_pattern(pattern, args.base_ref)

    exclude_regexes = [glob_to_regex(p) for p in config.get("exclude", [])]
    tracked_paths = {
        path
        for path in tracked_paths
        if not any(r.match(path) for r in exclude_regexes)
    }

    # Read each file to be compared (base vs head)
    rows = []
    for path in sorted(tracked_paths):
        head_content = read_head_content(path)
        if not head_content:
            continue  # file deleted in this PR/branch; nothing to budget-check

        base_content = read_base_content(path, args.base_ref)
        base_tokens = count_tokens(base_content, api_key, model)
        head_tokens = count_tokens(head_content, api_key, model)
        rows.append((path, base_tokens, head_tokens))

    print(
        f"threshold={threshold_percent}%  min_token_floor={min_token_floor}  "
        f"decision_maker={decision_maker}\n"
    )
    print(f"Per-file (vs {args.base_ref}):")
    print(f"{'file':<45} {'base':>8} {'head':>8} {'change':>10}  status")
    print("-" * 85)

    per_file_failed = False
    for path, base_tokens, head_tokens in rows:
        change = format_growth(base_tokens, head_tokens)
        exceeded_pct = (
            base_tokens > 0
            and (head_tokens - base_tokens) / base_tokens * 100 > threshold_percent
        )
        below_floor = 0 < base_tokens < min_token_floor
        exceeded = exceeded_pct and not below_floor
        per_file_failed = per_file_failed or exceeded

        if base_tokens == 0:
            status = "new file"
        elif exceeded:
            status = "FAIL"
        elif exceeded_pct and below_floor:
            status = "ok (below floor)"
        else:
            status = "ok"
        print(f"{path:<45} {base_tokens:>8} {head_tokens:>8} {change:>10}  {status}")

    base_total = sum(base_tokens for _, base_tokens, _ in rows)
    head_total = sum(head_tokens for _, _, head_tokens in rows)
    aggregate_change = format_growth(base_total, head_total)
    aggregate_exceeded = (
        base_total > 0
        and (head_total - base_total) / base_total * 100 > threshold_percent
    )

    print(f"\nAggregate (vs {args.base_ref}):")
    print(
        f"{'total':<45} {base_total:>8} {head_total:>8} {aggregate_change:>10}  "
        f"{'FAIL' if aggregate_exceeded else 'ok'}"
    )

    failed = per_file_failed if decision_maker == "per_file" else aggregate_exceeded

    print(
        f"\nDecision maker: {decision_maker} "
        f"({'per-file' if decision_maker == 'per_file' else 'aggregate'} result above governs pass/fail)."
    )

    if failed:
        print(f"\nPrompt token budget exceeded ({threshold_percent}% threshold).")
        return 1

    print("\nAll tracked prompt files are within budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
