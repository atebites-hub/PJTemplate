"""Unit tests for scripts/helpers/check_memory_reasoning.py (compliance check C3)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_HELPER_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "helpers" / "check_memory_reasoning.py"
)
_spec = importlib.util.spec_from_file_location("check_memory_reasoning", _HELPER_PATH)
assert _spec is not None and _spec.loader is not None
cmr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmr)


_VALID_MEMORY = """\
# Task Memory

## Task (TCREI)
- **Task**: Build the thing
- **Context**: Read docs/agents/testing_guidelines.md and src/server/runtime/main.py
- **Rules**: Keep it DRY
- **Evaluation**: verifiable. Gate: ./scripts/test-suite.sh (the new unit tests pass)
- **Iteration**: refine later
- **Plan**: step one, step two

## Status
- state: in_progress

## Lessons
### Background & Motivation
Because it matters.

### Key Challenges & Analysis
- Assumptions: the gate fires only on relevant changes
- Counterpoints: [...]
- Alternatives: [...]
- Risks: [...]

### Feedback & Assistance
None.
"""


@pytest.mark.unit
def test_is_filled_accepts_real_content() -> None:
    """Real prose, including brackets mid-sentence, counts as filled."""
    assert cmr.is_filled("Read docs/agents and src/server/main.py")
    # Brackets mid-sentence are real content, not a lone placeholder.
    assert cmr.is_filled("see `[settings.py]` for defaults")


@pytest.mark.unit
def test_is_filled_rejects_empty_and_placeholders() -> None:
    """Empty/whitespace content and lone bracket placeholders are not filled."""
    assert not cmr.is_filled("")
    assert not cmr.is_filled("   ")
    assert not cmr.is_filled("[...]")
    assert not cmr.is_filled("[Reference docs/agents/ + relevant code paths]")
    assert not cmr.is_filled("  [TODO]  ")


@pytest.mark.unit
def test_valid_memory_has_no_problems() -> None:
    """A fully filled memory reports no missing sections."""
    assert cmr.check_memory_text(_VALID_MEMORY) == []


@pytest.mark.unit
def test_template_placeholders_flag_all_sections() -> None:
    """The shipped memory template (all placeholders) flags every required section."""
    template = _HELPER_PATH.parents[2] / ".agents/skills/memory-system/assets/memory_template.md"
    problems = cmr.check_memory_text(template.read_text(encoding="utf-8"))
    assert "Context" in problems
    assert "Evaluation" in problems
    assert "Key Challenges & Analysis" in problems


@pytest.mark.unit
def test_only_evaluation_empty() -> None:
    """Only the emptied Evaluation bullet is reported."""
    text = _VALID_MEMORY.replace(
        "- **Evaluation**: verifiable. Gate: ./scripts/test-suite.sh (the new unit tests pass)",
        "- **Evaluation**: [...]",
    )
    assert cmr.check_memory_text(text) == ["Evaluation"]


@pytest.mark.unit
def test_evaluation_missing_class() -> None:
    """An Evaluation with a gate but no verifiability class is flagged."""
    text = _VALID_MEMORY.replace(
        "- **Evaluation**: verifiable. Gate: ./scripts/test-suite.sh (the new unit tests pass)",
        "- **Evaluation**: Gate: ./scripts/test-suite.sh",
    )
    problems = cmr.check_memory_text(text)
    assert "Evaluation: verifiability class (verifiable/non-verifiable)" in problems
    assert "Evaluation: acceptance gate (Gate:)" not in problems


@pytest.mark.unit
def test_evaluation_missing_gate() -> None:
    """An Evaluation with a class but no Gate is flagged."""
    text = _VALID_MEMORY.replace(
        "- **Evaluation**: verifiable. Gate: ./scripts/test-suite.sh (the new unit tests pass)",
        "- **Evaluation**: verifiable; the tests should pass",
    )
    problems = cmr.check_memory_text(text)
    assert "Evaluation: acceptance gate (Gate:)" in problems
    assert "Evaluation: verifiability class (verifiable/non-verifiable)" not in problems


@pytest.mark.unit
def test_evaluation_non_verifiable_with_rubric_passes() -> None:
    """A non-verifiable task with a rubric Gate satisfies the Evaluation check."""
    text = _VALID_MEMORY.replace(
        "- **Evaluation**: verifiable. Gate: ./scripts/test-suite.sh (the new unit tests pass)",
        "- **Evaluation**: non-verifiable. Gate: human review against rubric: clarity, tone",
    )
    assert cmr.check_memory_text(text) == []


@pytest.mark.unit
def test_evaluation_multiline_gate_passes() -> None:
    """A Gate on a continuation line under Evaluation is captured and passes."""
    text = _VALID_MEMORY.replace(
        "- **Evaluation**: verifiable. Gate: ./scripts/test-suite.sh (the new unit tests pass)",
        "- **Evaluation**: verifiable.\n  Gate: ./scripts/test-suite.sh",
    )
    assert cmr.check_memory_text(text) == []


@pytest.mark.unit
def test_missing_task_heading() -> None:
    """A missing Task (TCREI) heading is reported explicitly."""
    text = _VALID_MEMORY.replace("## Task (TCREI)", "## Plan")
    problems = cmr.check_memory_text(text)
    assert "'## Task (TCREI)' heading missing" in problems


@pytest.mark.unit
def test_missing_key_challenges_heading() -> None:
    """A missing Key Challenges & Analysis heading is reported explicitly."""
    text = _VALID_MEMORY.replace("### Key Challenges & Analysis", "### Notes")
    problems = cmr.check_memory_text(text)
    assert "Key Challenges & Analysis (heading missing)" in problems


@pytest.mark.unit
def test_key_challenges_all_placeholders_flags_section() -> None:
    """A Key Challenges section with only placeholder sub-bullets is flagged."""
    text = _VALID_MEMORY.replace(
        "- Assumptions: the gate fires only on relevant changes",
        "- Assumptions: [...]",
    )
    assert "Key Challenges & Analysis" in cmr.check_memory_text(text)


@pytest.mark.unit
def test_main_no_args_is_usage_error() -> None:
    """Invoking main with no files is a usage error (exit 2)."""
    assert cmr.main([]) == 2


@pytest.mark.unit
def test_main_passing_file(tmp_path: Path) -> None:
    """main returns 0 for a compliant memory file."""
    memory = tmp_path / "good.md"
    memory.write_text(_VALID_MEMORY, encoding="utf-8")
    assert cmr.main([str(memory)]) == 0


@pytest.mark.unit
def test_main_failing_file(tmp_path: Path) -> None:
    """main returns 1 for a memory with an empty required field."""
    memory = tmp_path / "bad.md"
    text = _VALID_MEMORY.replace(
        "- **Context**: Read docs/agents/testing_guidelines.md and src/server/runtime/main.py",
        "- **Context**: [...]",
    )
    memory.write_text(text, encoding="utf-8")
    assert cmr.main([str(memory)]) == 1


@pytest.mark.unit
def test_main_unreadable_file(tmp_path: Path) -> None:
    """main returns 2 when a given file cannot be read."""
    assert cmr.main([str(tmp_path / "does_not_exist.md")]) == 2
