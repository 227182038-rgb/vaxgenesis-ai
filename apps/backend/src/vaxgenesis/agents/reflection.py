"""Reflect-and-revise pattern (audit 2.4).

Implements a Reflexion-style self-critique step:
  1. After the Validator produces a candidate, the Critic reflects on
     what could go wrong.
  2. The reflection is fed back to the Hypothesis agent as additional
     context for the next iteration.
  3. Reflections accumulate across iterations, allowing the system to
     learn from its own mistakes within a single reasoning cycle.

Reference: Shinn et al. "Reflexion: Language Agents with Verbal
Reinforcement Learning" (NeurIPS 2023).
"""
from __future__ import annotations

from typing import Any

from vaxgenesis.agents.types import AgentResult


class ReflectionMemory:
    """Accumulates reflections across iterations of a reasoning cycle."""

    def __init__(self) -> None:
        self.reflections: list[dict[str, Any]] = []

    def add(self, iteration: int, issue: str, severity: str, fix: str) -> None:
        self.reflections.append({
            "iteration": iteration,
            "issue": issue,
            "severity": severity,
            "proposed_fix": fix,
        })

    def as_prompt_context(self) -> str:
        """Format the accumulated reflections as additional context for the next iteration."""
        if not self.reflections:
            return "(no prior reflections)"
        lines = ["Prior reflections on what could be improved:"]
        for r in self.reflections[-5:]:  # last 5 to keep prompt bounded
            lines.append(
                f"  - [{r['severity']}] {r['issue']} → fix: {r['proposed_fix']}"
            )
        return "\n".join(lines)


async def reflect_on_validation(
    validation_outputs: dict[str, Any],
    critic_issues: list[dict[str, Any]],
    iteration: int,
    llm_call: Any | None = None,
) -> dict[str, Any]:
    """Produce a structured reflection from the validation outputs and critic issues.

    Args:
        validation_outputs: dict of module -> outputs from the Validator agent
        critic_issues: list of issues identified by the Critic
        iteration: current iteration number (0-indexed)
        llm_call: optional async callable(prompt, system) -> str for LLM-based reflection.
                  If None, uses a heuristic reflection.

    Returns:
        dict with keys: issue, severity, proposed_fix, reflection_text
    """
    if not critic_issues:
        return {
            "iteration": iteration,
            "issue": "none",
            "severity": "info",
            "proposed_fix": "no changes needed",
            "reflection_text": "No critical issues identified; candidate is acceptable.",
        }

    # Pick the highest-severity issue
    severity_rank = {"critical": 4, "error": 3, "warning": 2, "info": 1}
    sorted_issues = sorted(
        critic_issues,
        key=lambda i: severity_rank.get(i.get("severity", "info"), 0),
        reverse=True,
    )
    top_issue = sorted_issues[0]

    proposed_fix = _propose_fix(top_issue, validation_outputs)

    reflection_text = (
        f"Iteration {iteration}: identified {len(critic_issues)} issue(s). "
        f"Top issue: [{top_issue.get('severity', 'warning')}] "
        f"{top_issue.get('issue', 'unknown')} in module "
        f"{top_issue.get('module', 'unknown')}. "
        f"Proposed fix: {proposed_fix}"
    )

    if llm_call is not None:
        try:
            llm_text = await llm_call(
                prompt=(
                    f"You are reflecting on a vaccine design candidate. "
                    f"Validation outputs: {validation_outputs}. "
                    f"Issues identified: {critic_issues}. "
                    f"Provide a single most-important reflection on what to change next."
                ),
                system="You are a careful vaccine design critic.",
            )
            reflection_text = llm_text
        except Exception:
            pass  # fall back to heuristic

    return {
        "iteration": iteration,
        "issue": top_issue.get("issue", "unknown"),
        "severity": top_issue.get("severity", "warning"),
        "module": top_issue.get("module"),
        "proposed_fix": proposed_fix,
        "reflection_text": reflection_text,
    }


def _propose_fix(issue: dict[str, Any], validation_outputs: dict[str, Any]) -> str:
    """Heuristic fix proposer based on issue type."""
    issue_type = issue.get("issue", "")
    module = issue.get("module", "")

    if issue_type == "high_uncertainty":
        return f"Request wet-lab validation for {module} before proceeding."
    if issue_type == "high_risk":
        return "Redesign construct: drop risky epitopes, add safer alternatives."
    if issue_type == "toxic_epitopes":
        toxic_count = issue.get("value", 0)
        return f"Remove {toxic_count} toxic epitope(s) and re-run toxicity screen."
    if issue_type == "allergenic_epitopes":
        return "Replace allergenic epitopes with non-allergenic variants from conservancy analysis."
    if issue_type == "low_coverage":
        return "Add epitopes binding under-represented HLA alleles (e.g. HLA-A*24:02 for Asia)."
    if issue_type == "self_reactive":
        return "Drop epitopes flagged by autoimmunity_screening module."
    return "Re-run pipeline with adjusted parameters."
