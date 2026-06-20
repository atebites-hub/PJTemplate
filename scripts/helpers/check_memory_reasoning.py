#!/usr/bin/env python3
"""Verify that a task memory records the reasoning artifacts check C3 requires.

This helper implements check **C3** of ``scripts/check-task-compliance.sh``: for a
task memory under ``docs/memories/``, it confirms that the reasoning pass output
was actually persisted into the memory fields the ``reasoning-system`` skill maps
it onto. Concretely it requires, per memory file:

* a non-placeholder ``- **Context**:`` bullet under ``## Task (TCREI)`` (the
  retrieval plan), and
* a non-placeholder ``- **Evaluation**:`` bullet under ``## Task (TCREI)`` (the
  test/regression plan) that also declares a **verifiability class**
  (``verifiable`` / ``non-verifiable``) and one **acceptance gate** (a ``Gate:``
  label naming a command/check or a rubric), and
* a ``### Key Challenges & Analysis`` section with at least one non-placeholder
  sub-bullet (assumptions / counterpoints / alternatives / risks).

The Evaluation checks are deterministic and lenient — presence/structure only.
They never judge the gate's *quality*; that is the decorrelated review's job.

The structure and placeholder conventions come from
``.agents/skills/memory-system/assets/memory_template.md``. ``Context`` and
``Evaluation`` are *bullet lines* under the ``## Task (TCREI)`` heading, not
sub-headings, so the parser matches bullets rather than headings.

A field counts as **filled** when its content, after the label, is non-empty and
is not a lone bracketed placeholder (e.g. ``[...]`` or the template's
``[Reference docs/agents/ + relevant code paths]``). Because every shipped
placeholder is a single ``[...]`` bracket, the lone-bracket test subsumes an exact
placeholder-string comparison and stays robust if the placeholder wording changes.

Usage::

    check_memory_reasoning.py <memory.md> [<memory.md> ...]

Exit codes: ``0`` all given files pass C3; ``1`` at least one fails (one line per
failing file is printed to stdout as ``<path>: <comma-separated empty sections>``);
``2`` usage or file-read error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Heading that opens the Task (TCREI) block; the block runs until the next H2.
_TASK_HEADING_RE = re.compile(r"^##\s+Task\s+\(TCREI\)\s*$")
_H2_RE = re.compile(r"^##\s")
# Heading that opens the Key Challenges & Analysis block; runs until the next H2/H3.
_KCA_HEADING_RE = re.compile(r"^###\s+Key Challenges & Analysis\s*$")
_H2_OR_H3_RE = re.compile(r"^#{2,3}\s")
# A labelled bullet inside the Key Challenges & Analysis block, e.g. "- Risks: ...".
_KCA_BULLET_RE = re.compile(r"^-\s+[A-Za-z][\w &/-]*:\s*(.*)$")
# A lone bracketed placeholder occupying the whole field, e.g. "[...]".
_LONE_BRACKET_RE = re.compile(r"\[[^\]]*\]")
# Verifiability class declared inside the Evaluation field.
_CLASS_RE = re.compile(r"(?i)\b(?:non-verifiable|verifiable)\b")
# Acceptance-gate declaration inside the Evaluation field: a `Gate:` label naming
# a command/check or a rubric.
_GATE_RE = re.compile(r"(?i)\bgate:")


def is_filled(content: str) -> bool:
    """Return whether a memory field's content is real prose, not a placeholder.

    Args:
        content: The text following a field label (e.g. everything after
            ``- **Context**:``).

    Returns:
        ``True`` when ``content`` has non-whitespace text that is not a single
        bracketed placeholder; ``False`` for empty/whitespace content or a lone
        ``[...]`` bracket (the template's unfilled state).

    """
    stripped = content.strip()
    if not stripped:
        return False
    if _LONE_BRACKET_RE.fullmatch(stripped):
        return False
    return True


def _extract_block(
    lines: list[str], heading_re: re.Pattern[str], stop_re: re.Pattern[str]
) -> list[str] | None:
    """Return the lines under ``heading_re`` up to the next ``stop_re`` heading.

    Args:
        lines: The memory file split into lines (without trailing newlines).
        heading_re: Pattern matching the heading that opens the block.
        stop_re: Pattern matching the heading that closes the block; the matching
            line is excluded from the result.

    Returns:
        The block's lines (excluding the heading itself), or ``None`` when the
        opening heading is absent.

    """
    start: int | None = None
    for index, line in enumerate(lines):
        if heading_re.match(line):
            start = index + 1
            break
    if start is None:
        return None
    block: list[str] = []
    for line in lines[start:]:
        if stop_re.match(line):
            break
        block.append(line)
    return block


def _find_bullet(block: list[str], label: str) -> str | None:
    """Return the content of a ``- **<label>**:`` bullet within ``block``.

    Args:
        block: Lines of the block to search (typically the Task (TCREI) block).
        label: The bold bullet label to find, e.g. ``"Context"``.

    Returns:
        The text after the bullet label, or ``None`` when the bullet is absent.

    """
    pattern = re.compile(rf"^-\s+\*\*{re.escape(label)}\*\*:\s*(.*)$")
    for line in block:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def _find_bullet_block(block: list[str], label: str) -> str | None:
    """Return a ``- **<label>**:`` bullet's content including continuation lines.

    Unlike :func:`_find_bullet` (which returns only the label's own line), this
    captures the bullet body: the text after the label plus every following line
    until the next ``- **<name>**:`` bullet or a Markdown heading. A multi-line
    field (e.g. an Evaluation whose ``Gate:`` sits on its own line) is then
    validated as one unit.

    Args:
        block: Lines of the Task (TCREI) block to search.
        label: The bold bullet label to find, e.g. ``"Evaluation"``.

    Returns:
        The joined bullet body, or ``None`` when the bullet is absent.

    """
    pattern = re.compile(rf"^-\s+\*\*{re.escape(label)}\*\*:\s*(.*)$")
    next_bullet = re.compile(r"^-\s+\*\*[^*]+\*\*:")
    collected: list[str] | None = None
    for line in block:
        if collected is None:
            match = pattern.match(line)
            if match:
                collected = [match.group(1)]
            continue
        if next_bullet.match(line) or line.startswith("#"):
            break
        collected.append(line)
    return "\n".join(collected) if collected is not None else None


def _check_evaluation(block: list[str]) -> list[str]:
    """Validate the Evaluation field: filled, with a verifiability class and a gate.

    The Evaluation bullet must declare a verifiability class (``verifiable`` or
    ``non-verifiable``) and exactly one acceptance gate (a ``Gate:`` label naming a
    command/check or a rubric). This is a presence/structure check only — it never
    judges the gate's quality (that is the decorrelated review's job).

    Args:
        block: Lines of the Task (TCREI) block.

    Returns:
        Problem labels for each missing requirement (empty if all present).

    """
    body = _find_bullet_block(block, "Evaluation")
    if body is None or not is_filled(body):
        return ["Evaluation"]
    problems: list[str] = []
    if not _CLASS_RE.search(body):
        problems.append("Evaluation: verifiability class (verifiable/non-verifiable)")
    if not _GATE_RE.search(body):
        problems.append("Evaluation: acceptance gate (Gate:)")
    return problems


def check_memory_text(text: str) -> list[str]:
    """Return the names of required reasoning sections that are missing or empty.

    Args:
        text: The full text of a task memory file.

    Returns:
        A list of human-readable section names that fail C3. An empty list means
        the memory satisfies C3.

    """
    problems: list[str] = []
    lines = text.splitlines()

    task_block = _extract_block(lines, _TASK_HEADING_RE, _H2_RE)
    if task_block is None:
        problems.append("'## Task (TCREI)' heading missing")
    else:
        context = _find_bullet(task_block, "Context")
        if context is None or not is_filled(context):
            problems.append("Context")
        problems.extend(_check_evaluation(task_block))

    kca_block = _extract_block(lines, _KCA_HEADING_RE, _H2_OR_H3_RE)
    if kca_block is None:
        problems.append("Key Challenges & Analysis (heading missing)")
    else:
        sub_bullets = [
            match.group(1) for line in kca_block if (match := _KCA_BULLET_RE.match(line))
        ]
        if not any(is_filled(content) for content in sub_bullets):
            problems.append("Key Challenges & Analysis")

    return problems


def main(argv: list[str] | None = None) -> int:
    """Check each memory file given on the command line against C3.

    Args:
        argv: Argument list (excluding the program name). Defaults to
            ``sys.argv[1:]``.

    Returns:
        Process exit code: ``0`` all pass, ``1`` at least one fails, ``2`` on a
        usage or file-read error.

    """
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(
            "usage: check_memory_reasoning.py <memory.md> [<memory.md> ...]",
            file=sys.stderr,
        )
        return 2

    failed = False
    for arg in args:
        try:
            text = Path(arg).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"{arg}: cannot read file ({exc})", file=sys.stderr)
            return 2
        problems = check_memory_text(text)
        if problems:
            failed = True
            print(f"{arg}: {', '.join(problems)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
