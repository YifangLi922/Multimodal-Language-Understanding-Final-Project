"""Generate a second review gallery for temporal_transformation only.

The 400-caption sub-sample only produced 19 keyword-matched candidates, of
which just 3 turned out to genuinely fit (see labels/gallery_labels.csv). That
is too thin to build several non-repeating conflict/aligned triplets. This
script instead scans the FULL 14,881-row test split for the same temporal
keywords, excludes anything already reviewed in data/caption_sample_400.csv,
and samples a manageable batch for a second labeling pass.

Output is a separate file (does not overwrite review/galleries/candidate_gallery.html).
"""
import os

import pandas as pd
from datasets import load_dataset

from generate_gallery import KEYWORDS, build_html

OUT_PATH = "review/galleries/candidate_gallery_temporal_v2.html"
SAMPLE_SIZE = 120
RANDOM_STATE = 42


def main():
    dataset = load_dataset("thaoshibe/anonymous-captions-114k")
    test_df = dataset["test"].to_pandas()

    already_reviewed = set(pd.read_csv("data/caption_sample_400.csv")["image_hash"])

    cap_lower = test_df["caption"].fillna("").str.lower()
    pattern = "|".join(KEYWORDS["temporal_transformation"])
    mask = cap_lower.str.contains(pattern, regex=True, na=False)
    mask &= ~test_df["image_hash"].isin(already_reviewed)

    candidates = test_df.loc[mask]
    sample = candidates.sample(
        n=min(SAMPLE_SIZE, len(candidates)), random_state=RANDOM_STATE
    ).reset_index(drop=True)

    family_rows = {"temporal_transformation": sample.to_dict("records")}
    out_html = build_html(
        family_rows,
        other_rows=[],
        title="RelSim Temporal Transformation Review — Batch 2 (full test split)",
        storage_key="relsim_gallery_temporal_v2_state_v1",
    )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}")
    print(f"Total new temporal keyword hits in full test split: {mask.sum()}")
    print(f"Sampled {len(sample)} for this review batch")


if __name__ == "__main__":
    main()
