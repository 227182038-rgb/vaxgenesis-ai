"""Manufacturing extension (audit v1.1, item 1.5).

Adds:
  - Bioreactor kinetics (Monod growth model)
  - Downstream processing yield cascade
  - Supply-chain bottleneck analysis
  - Techno-economic sensitivity

This module is designed to be composed with the existing
`ManufacturingSimulationModule` (v1.0) by invoking its outputs as
inputs to this module.

It does NOT replace the v1.0 module; it extends it.
"""
from __future__ import annotations

from typing import Any

from vaxgenesis.modules.base import BaseModule, ModuleResult


DEFAULT_MONOD_PARAMS = {
    "mu_max_per_hr": 0.8,
    "ks_glc_g_per_l": 0.01,
    "yi_x_per_s": 0.5,
    "yp_x_per_x": 0.3,
    "maintenance_glc_g_per_g_per_hr": 0.04,
    "inhib_threshold_g_per_l": 50.0,
}

DEFAULT_DSP_STAGES = [
    ("harvest", 0.95),
    ("lysis", 0.92),
    ("solubilization", 0.85),
    ("chromatography_1", 0.85),
    ("chromatography_2", 0.90),
    ("formulation", 0.95),
]

DEFAULT_SUPPLY_CHAIN = {
    "raw_media": 7,
    "chromatography_resin": 30,
    "single_use_bioreactor_bags": 14,
    "fill_finish_consumables": 21,
}


class BioreactorKineticsModule(BaseModule):
    """Bioreactor kinetics + DSP + supply chain (audit 1.5)."""

    module_id = "bioreactor_kinetics"
    module_name = "Bioreactor Kinetics & Supply Chain"
    description = (
        "Monod growth model, downstream processing cascade, and "
        "supply-chain bottleneck analysis for manufacturing feasibility."
    )
    category = "action"
    inputs = ["construct", "expression_host", "manufacturing_results"]
    outputs = [
        "growth_profile",
        "dsp_yield_cascade",
        "supply_chain_bottlenecks",
        "sensitivity_analysis",
    ]
    default_model_version = "1.0.0"

    def __init__(self, candidate_id, db_session=None, config=None):
        super().__init__(candidate_id, db_session, config)
        self.monod = {**DEFAULT_MONOD_PARAMS, **(config.get("monod", {}) if config else {})}
        self.dsp = config.get("dsp_stages", DEFAULT_DSP_STAGES) if config else DEFAULT_DSP_STAGES
        self.supply = {**DEFAULT_SUPPLY_CHAIN, **(config.get("supply_chain", {}) if config else {})}

    async def run(self, inputs: dict[str, Any]) -> ModuleResult:
        host = inputs.get("expression_host", "ecoli")
        construct_len = (inputs.get("construct") or {}).get("length_aa", 200)

        if host == "cho":
            self.monod["mu_max_per_hr"] = 0.04
            self.monod["yp_x_per_x"] = 0.05
        elif host == "yeast":
            self.monod["mu_max_per_hr"] = 0.3
            self.monod["yp_x_per_x"] = 0.2

        growth = self._simulate_growth(duration_hours=24, initial_glc_g_per_l=40.0)
        cascade = self._simulate_dsp(initial_product_g=growth["final_product_g"])
        bottlenecks = self._analyze_supply_chain()
        sensitivity = self._sensitivity_analysis()

        return ModuleResult(
            outputs={
                "growth_profile": growth,
                "dsp_yield_cascade": cascade,
                "supply_chain_bottlenecks": bottlenecks,
                "sensitivity_analysis": sensitivity,
                "expression_host": host,
                "construct_length_aa": construct_len,
                "combined_dsp_yield": cascade["final_yield_fraction"],
                "estimated_titer_g_per_l": round(growth["final_product_g"] / 10.0, 3),
            },
            confidence_interval={
                "titer_low": round(growth["final_product_g"] / 10.0 * 0.7, 3),
                "titer_high": round(growth["final_product_g"] / 10.0 * 1.3, 3),
            },
            model_version=self.default_model_version,
        )

    def score_uncertainty(self, result: ModuleResult, inputs: dict[str, Any]) -> float:
        return 0.35

    def _simulate_growth(
        self, duration_hours: int = 24, initial_glc_g_per_l: float = 40.0,
        initial_biomass_g_per_l: float = 0.1, volume_l: float = 10.0,
    ) -> dict[str, Any]:
        dt = 0.1
        t = 0.0
        x = initial_biomass_g_per_l
        s = initial_glc_g_per_l
        p = 0.0

        mu_max = self.monod["mu_max_per_hr"]
        ks = self.monod["ks_glc_g_per_l"]
        yx = self.monod["yi_x_per_s"]
        yp = self.monod["yp_x_per_x"]
        m = self.monod["maintenance_glc_g_per_g_per_hr"]
        inhib = self.monod["inhib_threshold_g_per_l"]

        trajectory = []
        while t < duration_hours and s > 0:
            mu = mu_max * s / (ks + s) * (1.0 if p < inhib else 0.3)
            dx = mu * x
            ds = -dx / yx - m * x
            dp = yp * dx
            x += dx * dt
            s = max(0.0, s + ds * dt)
            p += dp * dt
            t += dt
            if int(t * 10) % 10 == 0:
                trajectory.append({
                    "t_hours": round(t, 1),
                    "biomass_g_per_l": round(x, 3),
                    "glucose_g_per_l": round(s, 3),
                    "product_g_per_l": round(p, 3),
                })

        return {
            "final_biomass_g_per_l": round(x, 3),
            "final_product_g_per_l": round(p, 3),
            "final_product_g": round(p * volume_l, 3),
            "duration_hours": duration_hours,
            "growth_trajectory": trajectory[::10],
            "monod_params": self.monod,
        }

    def _simulate_dsp(self, initial_product_g: float) -> dict[str, Any]:
        remaining = initial_product_g
        stages = []
        for name, recovery in self.dsp:
            after = remaining * recovery
            stages.append({
                "stage": name,
                "recovery_fraction": recovery,
                "input_g": round(remaining, 3),
                "output_g": round(after, 3),
                "loss_g": round(remaining - after, 3),
            })
            remaining = after

        return {
            "stages": stages,
            "initial_product_g": round(initial_product_g, 3),
            "final_product_g": round(remaining, 3),
            "final_yield_fraction": round(remaining / max(1e-9, initial_product_g), 3),
        }

    def _analyze_supply_chain(self) -> dict[str, Any]:
        sorted_items = sorted(self.supply.items(), key=lambda x: -x[1])
        return {
            "lead_times_days": self.supply,
            "bottleneck": sorted_items[0][0],
            "bottleneck_lead_time_days": sorted_items[0][1],
            "recommendation": (
                f"Pre-order {sorted_items[0][0]} at least "
                f"{sorted_items[0][1]} days before planned batch start."
            ),
        }

    def _sensitivity_analysis(self) -> dict[str, Any]:
        base = self.monod["mu_max_per_hr"]
        results = {}
        for delta in [-0.2, 0.0, +0.2]:
            self.monod["mu_max_per_hr"] = base * (1 + delta)
            growth = self._simulate_growth(duration_hours=24)
            results[f"mu_max_{int(delta*100):+d}pct"] = round(
                growth["final_product_g_per_l"], 3
            )
        self.monod["mu_max_per_hr"] = base
        return {
            "varied_parameter": "mu_max_per_hr",
            "titer_by_scenario_g_per_l": results,
            "elasticity": round(
                (results["mu_max_+20pct"] - results["mu_max_-20pct"])
                / (2 * results["mu_max_+0pct"]),
                3,
            ),
        }
