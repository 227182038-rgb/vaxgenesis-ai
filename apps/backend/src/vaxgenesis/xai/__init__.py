"""Explainable AI (XAI) package — per-prediction feature attribution.

Every ML-backed prediction in VaxGenesis AI v2.0 produces an
`Explanation` alongside its score. The explanation includes:

  - **Feature attributions:** SHAP values showing how each input
    feature contributed to the prediction.
  - **Confidence explanation:** a natural-language sentence explaining
    the confidence interval in plain terms.
  - **Counterfactual:** "If feature X were 10% lower, the score would
    drop below the acceptance threshold."
  - **Similar examples:** the 3 most similar training examples
    (nearest neighbors in embedding space).

This module provides the explanation generators; the actual ML model
integration (SHAP kernel, LIME explainer) happens in adapters.
"""
