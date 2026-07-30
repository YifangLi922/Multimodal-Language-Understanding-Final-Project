"""Generate a second review gallery for compositional_formation, to grow the
fits pool the same way temporal_transformation's was grown (batches 2/3).

The 400-caption sample only produced 30 keyword-matched compositional
candidates (9 fits, 2 boundary_reject after correction) -- enough to
confirm it as the second relation family and build a modest conflict pool,
but thin for aligned pairs and short of the proposal's 20-25 target for
compositional conflict. This scans the full 14,881-row test split for the
same compositional keywords, excludes anything already reviewed in the
400-sample, and samples a fresh batch for labeling.

Output is a separate file (does not overwrite the batch-1 gallery).
"""
import os

import pandas as pd
from datasets import load_dataset

from generate_gallery import KEYWORDS, build_html

OUT_PATH = "review/galleries/candidate_gallery_compositional_v2.html"
SAMPLE_SIZE = 150
RANDOM_STATE = 42


def main():
    dataset = load_dataset("thaoshibe/anonymous-captions-114k")
    test_df = dataset["test"].to_pandas()

    already_reviewed = set(pd.read_csv("data/caption_sample_400.csv")["image_hash"])

    cap_lower = test_df["caption"].fillna("").str.lower()
    pattern = "|".join(KEYWORDS["compositional_formation"])
    mask = cap_lower.str.contains(pattern, regex=True, na=False)
    mask &= ~test_df["image_hash"].isin(already_reviewed)

    candidates = test_df.loc[mask]
    print(f"Compositional keyword hits not yet reviewed: {len(candidates)}")

    sample = candidates.sample(
        n=min(SAMPLE_SIZE, len(candidates)), random_state=RANDOM_STATE
    ).reset_index(drop=True)

    family_rows = {"compositional_formation": sample.to_dict("records")}
    out_html = build_html(
        family_rows,
        other_rows=[],
        title="RelSim Compositional Formation Review -- Batch 2",
        storage_key="relsim_gallery_compositional_v2_state_v1",
    )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}")
    print(f"  compositional_formation: {len(sample)} candidates sampled")


if __name__ == "__main__":
    main()
