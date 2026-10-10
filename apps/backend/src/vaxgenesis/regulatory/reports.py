"""Regulatory readiness report generator.

Produces a structured report for regulatory submission:
  - FDA Software as a Medical Device (SaMD) documentation
  - ICH M11 structured electronic submission
  - 21 CFR Part 11 electronic records compliance
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RegulatoryReportSection(BaseModel):
    """A section of the regulatory readiness report."""

    title: str
    content: str
    subsections: list["RegulatoryReportSection"] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class RegulatoryReadinessReport(BaseModel):
    """A complete regulatory readiness report for a candidate vaccine."""

    report_id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    platform_version: str = "2.0.0"
    sections: list[RegulatoryReportSection] = Field(default_factory=list)
    overall_readiness: Literal["not_ready", "conditionally_ready", "ready"] = "not_ready"
    blocking_issues: list[str] = Field(default_factory=list)


# Need Literal import
from typing import Literal  # noqa: E402


class RegulatoryReportGenerator:
    """Generates regulatory readiness reports from platform data."""

    def generate(
        self,
        candidate_id: UUID,
        candidate_data: dict[str, Any],
        predictions: list[dict[str, Any]],
        assays: list[dict[str, Any]],
        audit_trail: list[dict[str, Any]],
    ) -> RegulatoryReadinessReport:
        """Generate a full regulatory readiness report."""
        report = RegulatoryReadinessReport(candidate_id=candidate_id)

        # Section 1: Software Description
        report.sections.append(RegulatoryReportSection(
            title="1. Software Description",
            content=(
                "VaxGenesis AI is a computational vaccinology platform that "
                "predicts vaccine candidate properties using machine learning "
                "models. The software is classified as SaMD Class II under "
                "FDA guidance: it informs clinical decisions but does not "
                "directly drive them."
            ),
            subsections=[
                RegulatoryReportSection(
                    title="1.1 Software Version",
                    content=f"Version {report.platform_version}, candidate v{candidate_data.get('version', 1)}",
                ),
                RegulatoryReportSection(
                    title="1.2 Intended Use",
                    content=(
                        "The software is intended for use in pharmaceutical R&D "
                        "to prioritize vaccine candidates for wet-lab validation. "
                        "It is NOT intended for clinical diagnosis or treatment."
                    ),
                ),
            ],
        ))

        # Section 2: Model Provenance
        model_versions = set()
        for p in predictions:
            model_versions.add(f"{p.get('module', 'unknown')} v{p.get('model_version', 'unknown')}")
        report.sections.append(RegulatoryReportSection(
            title="2. Model Provenance and Lineage",
            content=(
                f"This candidate was evaluated using {len(model_versions)} "
                f"prediction models. Each model's training data, hyperparameters, "
                f"and performance metrics are tracked in the MLflow Model Registry."
            ),
            evidence_refs=list(model_versions),
        ))

        # Section 3: Validation Evidence
        completed_assays = [a for a in assays if a.get("status") == "completed"]
        report.sections.append(RegulatoryReportSection(
            title="3. Wet-Lab Validation Evidence",
            content=(
                f"This candidate has {len(completed_assays)} completed wet-lab "
                f"assay(s). Each assay result is linked to the prediction it "
                f"validated, enabling closed-loop model improvement."
            ),
            evidence_refs=[str(a.get("id", "")) for a in completed_assays],
        ))

        # Section 4: 21 CFR Part 11 Compliance
        report.sections.append(RegulatoryReportSection(
            title="4. 21 CFR Part 11 Electronic Records Compliance",
            content=(
                "All audit log entries are hash-chained (SHA-256) and stored "
                "in an append-only ledger. Records cannot be altered without "
                "detection. User identity is captured for every action. "
                "Electronic signatures are applied via JWT-authenticated API calls."
            ),
            evidence_refs=[str(a.get("entry_id", "")) for a in audit_trail[:10]],
        ))

        # Section 5: Risk Assessment
        risk_score = candidate_data.get("risk_score", 1.0)
        report.sections.append(RegulatoryReportSection(
            title="5. Risk Assessment",
            content=(
                f"Composite risk score: {risk_score:.3f} (0=no risk, 1=critical). "
                f"The risk score combines toxicity, allergenicity, autoimmunity, "
                f"and prediction uncertainty. "
                + ("Risk is within acceptable bounds." if risk_score < 0.4
                   else "Risk exceeds acceptable threshold; candidate should be rejected.")
            ),
        ))

        # Overall readiness
        blocking = []
        if risk_score > 0.4:
            blocking.append("Risk score exceeds threshold")
        if len(completed_assays) == 0:
            blocking.append("No wet-lab validation completed")
        if candidate_data.get("overall_uncertainty", 1.0) > 0.5:
            blocking.append("Prediction uncertainty too high")

        report.blocking_issues = blocking
        if not blocking:
            report.overall_readiness = "ready"
        elif len(blocking) == 1:
            report.overall_readiness = "conditionally_ready"
        else:
            report.overall_readiness = "not_ready"

        return report

    def to_markdown(self, report: RegulatoryReadinessReport) -> str:
        """Render the report as Markdown for submission."""
        lines = [
            f"# Regulatory Readiness Report",
            f"",
            f"**Report ID:** {report.report_id}  ",
            f"**Candidate ID:** {report.candidate_id}  ",
            f"**Generated:** {report.generated_at.isoformat()}  ",
            f"**Platform Version:** {report.platform_version}  ",
            f"**Overall Readiness:** {report.overall_readiness.upper()}",
            f"",
        ]
        if report.blocking_issues:
            lines.append("## Blocking Issues")
            lines.append("")
            for issue in report.blocking_issues:
                lines.append(f"- ⚠ {issue}")
            lines.append("")

        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            if section.evidence_refs:
                lines.append("**Evidence:**")
                for ref in section.evidence_refs:
                    lines.append(f"- `{ref}`")
                lines.append("")
            for sub in section.subsections:
                lines.append(f"### {sub.title}")
                lines.append("")
                lines.append(sub.content)
                lines.append("")

        lines.append("---")
        lines.append(
            f"*This report was auto-generated by VaxGenesis AI v{report.platform_version} "
            f"and is suitable for inclusion in a regulatory submission package.*"
        )
        return "\n".join(lines)
