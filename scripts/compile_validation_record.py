"""Compile a human-validation record for every triplet in the final manifest:
which gallery it was reviewed in, the CLIP similarity score shown at review
time, and any notes -- the deliverable required by proposal Section 15
("human-validation responses and agreement summary").

This does not re-run any validation; it just traces each of the 175 final
triplets back to the specific accept decision (and underlying source label
file) that put it in the benchmark, for methodology writeups.

Output: review/validation_record.csv
"""
import glob

import pandas as pd

MANIFEST_PATH = "review/triplet_manifest.csv"
OUT_PATH = "review/validation_record.csv"


def load_all_labels():
    frames = []
    for path in sorted(glob.glob("labels/*.csv")):
        df = pd.read_csv(path)
        if "hashes" not in df.columns or "decision" not in df.columns:
            continue  # skip the codebook-review label files (different schema)
        df["source_file"] = path
        frames.append(df[["source_file", "item_id", "section", "decision", "notes", "hashes", "similarity"]])
    return pd.concat(frames, ignore_index=True)


def main():
    manifest = pd.read_csv(MANIFEST_PATH)
    labels = load_all_labels()
    accepted = labels[labels["decision"] == "accept"].copy()
    accepted["hash_set"] = accepted["hashes"].apply(lambda h: frozenset(h.split(",")))

    rows = []
    for _, r in manifest.iterrows():
        triplet_hashes = frozenset([r["anchor_hash"], r["positive_hash"], r["negative_hash"]])
        match = None
        for _, lr in accepted.iterrows():
            if lr["hash_set"] <= triplet_hashes:  # the review pair/triplet is a subset of this triplet's images
                match = lr
                break
        rows.append({
            "triplet_id": r["triplet_id"],
            "relation_family": r["relation_family"],
            "condition": r["condition"],
            "validated_in_file": match["source_file"] if match is not None else "",
            "validation_item_id": match["item_id"] if match is not None else "",
            "clip_similarity_at_review": match["similarity"] if match is not None else "",
            "reviewer_notes": match["notes"] if match is not None else "",
        })

    record = pd.DataFrame(rows)
    record.to_csv(OUT_PATH, index=False)

    n_unmatched = (record["validated_in_file"] == "").sum()
    print(f"Wrote {OUT_PATH}: {len(record)} triplets")
    print(f"  {len(record) - n_unmatched} traced back to a specific accept decision")
    if n_unmatched:
        print(f"  {n_unmatched} triplets have no traceable review row (check manually): "
              f"{record.loc[record['validated_in_file'] == '', 'triplet_id'].tolist()}")


if __name__ == "__main__":
    main()
