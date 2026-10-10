"""Explanation schemas and generators.

Defines the `Explanation` Pydantic model that travels alongside every
prediction, and the generators that produce explanations from model
outputs.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FeatureAttribution(BaseModel):
    """A single feature's contribution to a prediction."""

    feature_name: str
    feature_value: Any
    attribution: float  # SHAP value; positive = pushed score up
    contribution_pct: float = Field(ge=0.0, le=1.0)  # |attribution| / sum(|attributions|)


class ConfidenceExplanation(BaseModel):
    """Natural-language explanation of a confidence interval."""

    score: float
    confidence_low: float
    confidence_high: float
    confidence_level: float = 0.95
    sentence: str

    @classmethod
    def generate(
        cls,
        score: float,
        ci_low: float,
        ci_high: float,
        confidence_level: float = 0.95,
    ) -> "ConfidenceExplanation":
        """Generate a natural-language confidence explanation."""
        width = ci_high - ci_low
        if width < 0.1:
            certainty = "high"
        elif width < 0.2:
            certainty = "moderate"
        else:
            certainty = "low"

        sentence = (
            f"The predicted score is {score:.3f} with {certainty} certainty "
            f"(95% CI: [{ci_low:.3f}, {ci_high:.3f}]). "
            f"The true value is likely within this range, but wet-lab "
            f"validation is recommended before clinical decisions."
        )
        return cls(
            score=score,
            confidence_low=ci_low,
            confidence_high=ci_high,
            confidence_level=confidence_level,
            sentence=sentence,
        )


class Counterfactual(BaseModel):
    """'What-if' analysis: what input change would flip the prediction."""

    feature_name: str
    current_value: Any
    required_value: Any
    direction: str  # "increase" or "decrease"
    magnitude_pct: float
    sentence: str

    @classmethod
    def generate(
        cls,
        feature_name: str,
        current_value: float,
        threshold: float,
        current_score: float,
        target_score: float,
    ) -> "Counterfactual":
        """Generate a counterfactual for a single feature."""
        if target_score < current_score:
            direction = "decrease"
            magnitude = current_value - (current_value * target_score / current_score)
        else:
            direction = "increase"
            magnitude = (current_value * target_score / current_score) - current_value

        magnitude_pct = abs(magnitude / current_value) * 100 if current_value != 0 else 0

        sentence = (
            f"If {feature_name} were {direction}d by {magnitude_pct:.1f}% "
            f"(from {current_value:.3f} to {current_value + magnitude:.3f}), "
            f"the predicted score would change from {current_score:.3f} to "
            f"approximately {target_score:.3f}."
        )
        return cls(
            feature_name=feature_name,
            current_value=current_value,
            required_value=current_value + magnitude,
            direction=direction,
            magnitude_pct=magnitude_pct,
            sentence=sentence,
        )


class Explanation(BaseModel):
    """Full explanation bundle for a single prediction."""

    prediction_id: str
    model_name: str
    model_version: str
    feature_attributions: list[FeatureAttribution] = Field(default_factory=list)
    confidence_explanation: ConfidenceExplanation | None = None
    counterfactuals: list[Counterfactual] = Field(default_factory=list)
    similar_examples: list[dict[str, Any]] = Field(default_factory=list)
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ExplanationGenerator:
    """Generates Explanation objects from prediction results."""

    def generate(
        self,
        prediction_id: str,
        model_name: str,
        model_version: str,
        score: float,
        ci_low: float,
        ci_high: float,
        feature_values: dict[str, Any],
        feature_attributions: dict[str, float] | None = None,
        threshold: float = 0.5,
    ) -> Explanation:
        """Generate a full Explanation bundle.

        Args:
            prediction_id: The prediction's unique ID
            model_name: Name of the model that produced the prediction
            model_version: Version of the model
            score: The predicted score
            ci_low, ci_high: Confidence interval bounds
            feature_values: Input feature names → values
            feature_attributions: SHAP-style attributions (feature → value)
            threshold: The acceptance threshold for counterfactual analysis
        """
        # Feature attributions
        attributions: list[FeatureAttribution] = []
        if feature_attributions:
            total = sum(abs(v) for v in feature_attributions.values()) or 1.0
            for name, value in feature_values.items():
                attr = feature_attributions.get(name, 0.0)
                attributions.append(FeatureAttribution(
                    feature_name=name,
                    feature_value=value,
                    attribution=attr,
                    contribution_pct=abs(attr) / total,
                ))
            # Sort by absolute attribution descending
            attributions.sort(key=lambda a: abs(a.attribution), reverse=True)

        # Confidence explanation
        conf = ConfidenceExplanation.generate(
            score=score, ci_low=ci_low, ci_high=ci_high,
        )

        # Counterfactual: if score is above threshold, what would bring it below?
        counterfactuals: list[Counterfactual] = []
        if score > threshold and attributions:
            top_feature = attributions[0]
            if isinstance(top_feature.feature_value, (int, float)) and top_feature.feature_value != 0:
                target = threshold - 0.01  # just below threshold
                cf = Counterfactual.generate(
                    feature_name=top_feature.feature_name,
                    current_value=float(top_feature.feature_value),
                    threshold=threshold,
                    current_score=score,
                    target_score=target,
                )
                counterfactuals.append(cf)

        # Narrative summary
        top_drivers = ", ".join(a.feature_name for a in attributions[:3]) or "no single feature"
        narrative = (
            f"The model predicts a score of {score:.3f} with {conf.sentence.split(' with ')[1].split(' certainty')[0]} certainty. "
            f"The top contributing features are: {top_drivers}. "
        )
        if counterfactuals:
            narrative += counterfactuals[0].sentence + " "
        narrative += (
            "This prediction should be validated via wet-lab assay before "
            "any clinical claim is made."
        )

        return Explanation(
            prediction_id=prediction_id,
            model_name=model_name,
            model_version=model_version,
            feature_attributions=attributions,
            confidence_explanation=conf,
            counterfactuals=counterfactuals,
            narrative=narrative,
        )
