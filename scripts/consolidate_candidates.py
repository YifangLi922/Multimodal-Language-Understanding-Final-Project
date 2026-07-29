"""Merge all reviewed gallery-label CSVs into one master candidate list.

Pulls every row marked fits/boundary_reject out of gallery_labels.csv
(temporal batch 1 + compositional + containment) and
gallery_labels_for_temporal_transformation.csv (temporal batch 2), and
writes a single deduplicated review/confirmed_candidates.csv used from here
on as the source of truth for codebook examples and triplet construction.
"""
import pandas as pd

SOURCES = [
    ("gallery_labels.csv", "batch1"),
    ("gallery_labels_for_temporal_transformation.csv", "batch2_temporal"),
]

KEEP_DECISIONS = {"fits", "boundary_reject"}

OUT_PATH = "review/confirmed_candidates.csv"


def main():
    frames = []
    for path, batch in SOURCES:
        df = pd.read_csv(path)
        df = df[df["decision"].isin(KEEP_DECISIONS)].copy()
        # family_shown is the family the image was reviewed against
        # (batch1's "unmatched" rows are never fits/boundary_reject so they
        # drop out naturally; assigned_family only matters for those rows)
        df["family"] = df["family_shown"]
        df["source_batch"] = batch
        frames.append(df[["image_hash", "family", "decision", "notes", "url_link", "caption", "source_batch"]])

    merged = pd.concat(frames, ignore_index=True)

    before = len(merged)
    merged = merged.drop_duplicates(subset=["image_hash", "family"], keep="first")
    if before != len(merged):
        print(f"Dropped {before - len(merged)} duplicate (image_hash, family) rows")

    merged.to_csv(OUT_PATH, index=False)

    print(f"Wrote {OUT_PATH}: {len(merged)} rows")
    print(merged.groupby(["family", "decision"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
