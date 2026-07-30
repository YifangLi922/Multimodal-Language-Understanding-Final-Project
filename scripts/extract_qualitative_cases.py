"""Pull ready-to-write qualitative case studies out of the final results:
  - RelSim-correct, CLIP-and-DINO-both-wrong (success cases)
  - all three models wrong (failure cases)

For each case, includes the anchor/positive/negative captions and the
LOCAL archived image path (from review/archive/image_archive_index.csv) so
you can open the actual images while writing, without depending on
possibly-dead URLs.

Output: review/qualitative_cases.csv
"""
import pandas as pd

RESULTS_PATH = "review/triplet_results.csv"
MANIFEST_PATH = "review/triplet_manifest.csv"
ARCHIVE_INDEX_PATH = "review/archive/image_archive_index.csv"
OUT_PATH = "review/qualitative_cases.csv"


def main():
    res = pd.read_csv(RESULTS_PATH)
    manifest = pd.read_csv(MANIFEST_PATH).set_index("triplet_id")
    archive = pd.read_csv(ARCHIVE_INDEX_PATH).set_index("image_hash")["local_path"].to_dict()

    pivot = res.pivot_table(index="triplet_id", columns="model", values="correct")
    pivot = pivot.join(manifest[["relation_family", "condition"]])

    conflict = pivot[pivot["condition"] == "conflict"]
    relsim_only = conflict[(conflict["relsim"] == 1) & (conflict["CLIP"] == 0) & (conflict["DINO"] == 0)]
    all_wrong = conflict[(conflict["relsim"] == 0) & (conflict["CLIP"] == 0) & (conflict["DINO"] == 0)]

    rows = []
    for case_type, subset in [("relsim_only_correct", relsim_only), ("all_models_wrong", all_wrong)]:
        for tid in subset.index:
            m = manifest.loc[tid]
            rows.append({
                "case_type": case_type,
                "triplet_id": tid,
                "relation_family": m["relation_family"],
                "anchor_caption": m["anchor_caption"],
                "anchor_local_path": archive.get(m["anchor_hash"], ""),
                "positive_caption": m["positive_caption"],
                "positive_local_path": archive.get(m["positive_hash"], ""),
                "negative_caption": m["negative_caption"],
                "negative_local_path": archive.get(m["negative_hash"], ""),
            })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_PATH, index=False)

    print(f"Wrote {OUT_PATH}: {len(out)} cases")
    print(out["case_type"].value_counts())
    print()
    print(out.groupby(["case_type", "relation_family"]).size())


if __name__ == "__main__":
    main()
