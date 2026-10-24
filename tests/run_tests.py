#!/usr/bin/env python3
"""Local tests for the DueCrew skill.

Each scenario in tests/scenarios/ is a student's first text. The runner gives it to Claude Code
(`claude -p`) with duecrew/SKILL.md loaded as instructions, saves the reply to tests/output/, and
checks the plan's sections. Canvas and reminders don't exist locally, so this tests the reasoning
and reply format, not Cubbie's abilities.

    python3 tests/run_tests.py                 # run every scenario, then check
    python3 tests/run_tests.py 2               # run only scenarios whose file starts with "2"
    python3 tests/run_tests.py --check-only    # re-check saved replies without calling claude
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "duecrew" / "SKILL.md"
SCENARIOS = ROOT / "tests" / "scenarios"
OUTPUT = ROOT / "tests" / "output"

HARNESS = (
    "You are Cubbie, a student's assistant in iMessage. Follow the DueCrew skill below for this request. "
    "In this test, Canvas is not connected and you have no tools: reply with the texts you would send, "
    "separated by a line containing only ---.\n\n"
)

LABELS = ["Project Rescue Plan:", "Deadline:", "Committed", "Proposed, not agreed", "Unassigned", "Blockers", "Next steps"]

# Per scenario: words that must (or must not) appear in a section, and patterns the deadline line must match.
EXPECT = {
    "1": {
        "Committed": {"has": ["maya", "lit"], "lacks": ["leo", "methods", "layout"]},
        "Proposed, not agreed": {"has": ["leo", "figure"]},
        "Unassigned": {"has": ["methods"]},
        "Deadline:": {"has": ["oct", "30"], "lacks": ["conflict"]},
    },
    "2": {
        "Deadline:": {"has": ["conflict", "6", "8"]},
        "Committed": {"has": ["jordan", "summary", "background"], "lacks": ["chris"]},
        "Proposed, not agreed": {"has": ["chris", "analysis"]},
        "Next steps": {"has": ["deadline"]},
    },
    "3": {
        "Committed": {"has": ["none"], "lacks": ["taylor", "riley", "morgan"]},
        "Unassigned": {"has": ["slide", "script", "source", "video"]},
        "Deadline:": {"has": ["not"], "lacks": ["conflict"]},
    },
    # Assignment only, no group chat: a full plan with every task unassigned (asking for the chat instead fails).
    "4": {
        "Deadline:": {"has": ["nov", "12", "instructions"], "lacks": ["conflict"]},
        "Committed": {"has": ["none"]},
        "Proposed, not agreed": {"has": ["none"]},
        "Unassigned": {"has": ["introduction", "method", "results", "discussion", "references"]},
    },
    "5": {
        "Committed": {"has": ["nina", "research", "handout"], "lacks": ["dev", "slide"]},
        "Unassigned": {"has": ["slide"]},
    },
}

FORBIDDEN = {
    "Markdown": re.compile(r"\*\*|^#|```|^\|", re.M),
    "claims it contacted someone": re.compile(r"\bI(?:'ve| have)? (?:sent|messaged|texted|contacted|told)\b(?! you)", re.I),
    "claims a reminder was set": re.compile(r"\b(?:reminder (?:is |has been )?set|I(?:'ve| have)? set (?:a|your) reminder)\b", re.I),
}


def run_claude(prompt: str) -> str:
    cmd = [
        "claude", "-p", prompt,
        "--append-system-prompt", HARNESS + SKILL.read_text(),
        "--tools", "",
        "--no-session-persistence",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        sys.exit(f"claude failed: {result.stderr.strip()}")
    return result.stdout


def sections(reply: str) -> dict[str, str]:
    """Split the plan text into its labeled sections (lowercased)."""
    plan = reply.split("Here's a message you can forward")[0]
    found = {}
    positions = [(plan.find(label), label) for label in LABELS]
    positions = sorted((pos, label) for pos, label in positions if pos >= 0)
    for i, (pos, label) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(plan)
        found[label] = plan[pos + len(label):end].lower()
    return found


def check(key: str, reply: str) -> list[str]:
    failures = []
    for what, pattern in FORBIDDEN.items():
        if pattern.search(reply):
            failures.append(f"reply {what}: {pattern.search(reply).group(0)!r}")
    found = sections(reply)
    missing = [label for label in LABELS if label not in found]
    if missing:
        failures.append(f"missing labels: {missing}")
    if list(found) != [label for label in LABELS if label in found]:
        failures.append("labels out of order")
    if "Here's a message you can forward to the group:" not in reply:
        failures.append("no forwardable message")
    if not re.search(r"remind", reply.split("Here's a message you can forward")[-1], re.I):
        failures.append("no reminder offer")
    for label, rules in EXPECT[key].items():
        text = found.get(label, "")
        for word in rules.get("has", []):
            if word not in text:
                failures.append(f"{label!r} should mention {word!r}")
        for word in rules.get("lacks", []):
            if word in text:
                failures.append(f"{label!r} should not mention {word!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("only", nargs="?", help="run scenarios whose file name starts with this")
    parser.add_argument("--check-only", action="store_true", help="check saved replies in tests/output/")
    args = parser.parse_args()

    OUTPUT.mkdir(exist_ok=True)
    failed = 0
    for scenario in sorted(SCENARIOS.glob("*.txt")):
        if args.only and not scenario.name.startswith(args.only):
            continue
        key = scenario.name.split("-")[0]
        out = OUTPUT / scenario.name
        if not args.check_only:
            out.write_text(run_claude(scenario.read_text()))
        if not out.exists():
            print(f"SKIP {scenario.stem}: no saved reply")
            continue
        failures = check(key, out.read_text())
        print(f"{'PASS' if not failures else 'FAIL'} {scenario.stem}")
        for f in failures:
            print(f"     - {f}")
        failed += bool(failures)
    print(f"\nReplies saved in {OUTPUT.relative_to(ROOT)}/")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
