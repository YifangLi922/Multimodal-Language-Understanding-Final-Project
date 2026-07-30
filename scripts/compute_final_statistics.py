"""Compute the final reported statistics from review/triplet_results.csv:
accuracy per (relation_family, condition, model) with triplet-level
bootstrap 95% CIs, paired model gaps (RelSim-CLIP, RelSim-DINO), and the
two key comparisons the research questions hinge on (conflict gap - aligned
gap within a family; family1 gap - family2 gap within conflict).

Pure pandas/numpy on already-scored results -- no GPU, no network, no
relsim/torch needed. Safe to run locally or in Colab.

Outputs:
  review/statistics_accuracy_with_ci.csv
  review/statistics_paired_gaps.csv
  review/statistics_key_comparisons.csv
"""
import numpy as np
import pandas as pd

RESULTS_PATH = "review/triplet_results.csv"
CI_OUT_PATH = "review/statistics_accuracy_with_ci.csv"
GAPS_OUT_PATH = "review/statistics_paired_gaps.csv"
COMPARISONS_OUT_PATH = "review/statistics_key_comparisons.csv"
N_BOOTSTRAP = 3000
RANDOM_STATE = 0


def bootstrap_ci(values, n_boot=N_BOOTSTRAP, rng=None):
    rng = rng or np.random.RandomState(RANDOM_STATE)
    values = np.asarray(values)
    n = len(values)
    means = [values[rng.randint(0, n, n)].mean() for _ in range(n_boot)]
    lo, hi = np.percentile(means, [2.5, 97.5])
    return lo, hi


def main():
    res = pd.read_csv(RESULTS_PATH)
    rng = np.random.RandomState(RANDOM_STATE)

    # ---------- accuracy + bootstrap CI per cell ----------
    ci_rows = []
    for (family, condition, model), group in res.groupby(["relation_family", "condition", "model"]):
        vals = group["correct"].values
        lo, hi = bootstrap_ci(vals, rng=rng)
        ci_rows.append({
            "relation_family": family,
            "condition": condition,
            "model": model,
            "n": len(vals),
            "accuracy": vals.mean(),
            "ci_lower_95": lo,
            "ci_upper_95": hi,
        })
    ci_df = pd.DataFrame(ci_rows).sort_values(["relation_family", "condition", "model"])
    ci_df.to_csv(CI_OUT_PATH, index=False)
    print(f"Wrote {CI_OUT_PATH}")
    print(ci_df.to_string(index=False))
    print()

    # ---------- paired gaps ----------
    acc = res.groupby(["relation_family", "condition", "model"])["correct"].mean().unstack("model")
    gaps = pd.DataFrame(index=acc.index)
    gaps["relsim_minus_clip"] = acc["relsim"] - acc["CLIP"]
    gaps["relsim_minus_dino"] = acc["relsim"] - acc["DINO"]
    gaps = gaps.reset_index()
    gaps.to_csv(GAPS_OUT_PATH, index=False)
    print(f"Wrote {GAPS_OUT_PATH}")
    print(gaps.to_string(index=False))
    print()

    # ---------- key comparisons ----------
    gaps_idx = gaps.set_index(["relation_family", "condition"])
    comparisons = []
    for family in gaps["relation_family"].unique():
        if family not in acc.index.get_level_values(0):
            continue
        try:
            conflict_gap_clip = gaps_idx.loc[(family, "conflict"), "relsim_minus_clip"]
            aligned_gap_clip = gaps_idx.loc[(family, "aligned"), "relsim_minus_clip"]
            conflict_gap_dino = gaps_idx.loc[(family, "conflict"), "relsim_minus_dino"]
            aligned_gap_dino = gaps_idx.loc[(family, "aligned"), "relsim_minus_dino"]
        except KeyError:
            continue
        comparisons.append({
            "comparison": "conflict_gap_minus_aligned_gap (RQ2: conflict sensitivity)",
            "relation_family": family, "baseline": "CLIP",
            "value": conflict_gap_clip - aligned_gap_clip,
        })
        comparisons.append({
            "comparison": "conflict_gap_minus_aligned_gap (RQ2: conflict sensitivity)",
            "relation_family": family, "baseline": "DINO",
            "value": conflict_gap_dino - aligned_gap_dino,
        })

    families_with_conflict = [f for f in gaps["relation_family"].unique()
                               if (f, "conflict") in gaps_idx.index and f != "attribute_priority_control"]
    if len(families_with_conflict) == 2:
        f1, f2 = families_with_conflict
        for baseline, col in [("CLIP", "relsim_minus_clip"), ("DINO", "relsim_minus_dino")]:
            comparisons.append({
                "comparison": f"family_gap_diff (RQ1: {f1} vs {f2}, conflict)",
                "relation_family": f"{f1}_minus_{f2}", "baseline": baseline,
                "value": gaps_idx.loc[(f1, "conflict"), col] - gaps_idx.loc[(f2, "conflict"), col],
            })

    comp_df = pd.DataFrame(comparisons)
    comp_df.to_csv(COMPARISONS_OUT_PATH, index=False)
    print(f"Wrote {COMPARISONS_OUT_PATH}")
    print(comp_df.to_string(index=False))


if __name__ == "__main__":
    main()
