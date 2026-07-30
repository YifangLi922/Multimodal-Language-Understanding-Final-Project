"""Generate a third review gallery for temporal_transformation, to grow the
fits pool enough for the aligned-pair search to have real appearance-overlap
candidates to find.

Batches so far: the 400-caption sample (19 keyword hits, 3 fits) and a
120-row sample from the full test split (labels/codebook_review_temporal_batch2.csv,
20 fits). That gave 22 confirmed temporal fits total -- enough for a decent
conflict-negative pool, but too few distinct images for the aligned-pair
search to coincidentally turn up many appearance matches (deepening the
search radius within those same 22 images, tried in retrieval_review_aligned_pair_temporal_batch2_UNUSED,
mostly surfaced weak matches).

This scans the full 14,881-row test split for the same temporal keywords
again, excludes every hash already reviewed in either prior batch, and
samples a fresh batch. More confirmed fits -> quadratically more possible
pairs -> better odds of a genuine appearance coincidence for aligned triplets
(and more material for conflict triplets too).

Output is a separate file (does not overwrite the v1/v2 galleries).
"""
import os

import pandas as pd
from datasets import load_dataset

from generate_codebook_review_batch1 import KEYWORDS, build_html

OUT_PATH = "review/galleries/codebook_review_temporal_batch3.html"
SAMPLE_SIZE = 150
RANDOM_STATE = 42


def main():
    dataset = load_dataset("thaoshibe/anonymous-captions-114k")
    test_df = dataset["test"].to_pandas()

    batch1_reviewed = set(pd.read_csv("data/caption_sample_400.csv")["image_hash"])
    batch2_reviewed = set(pd.read_csv("labels/codebook_review_temporal_batch2.csv")["image_hash"])
    already_reviewed = batch1_reviewed | batch2_reviewed

    cap_lower = test_df["caption"].fillna("").str.lower()
    pattern = "|".join(KEYWORDS["temporal_transformation"])
    mask = cap_lower.str.contains(pattern, regex=True, na=False)
    mask &= ~test_df["image_hash"].isin(already_reviewed)

    candidates = test_df.loc[mask]
    print(f"Temporal keyword hits not yet reviewed: {len(candidates)}")

    sample = candidates.sample(
        n=min(SAMPLE_SIZE, len(candidates)), random_state=RANDOM_STATE
    ).reset_index(drop=True)

    family_rows = {"temporal_transformation": sample.to_dict("records")}
    out_html = build_html(
        family_rows,
        other_rows=[],
        title="RelSim Temporal Transformation Review -- Batch 3",
        storage_key="relsim_gallery_temporal_v3_state_v1",
    )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}")
    print(f"  temporal_transformation: {len(sample)} candidates sampled")


if __name__ == "__main__":
    main()
