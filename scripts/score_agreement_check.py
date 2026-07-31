"""Score the second annotator's blind labels against the answer key.

Run scripts/build_agreement_check.py first, send review/galleries/
agreement_check_blind.html to the second annotator, get back their exported
agreement_check_blind.csv, then run this.

Usage:
  python scripts/score_agreement_check.py [path/to/agreement_check_blind.csv]
"""
import sys

import pandas as pd

KEY_PATH = "review/agreement_check/answer_key.csv"
DEFAULT_FRIEND_PATH = "labels/agreement_check_friend.csv"
OUT_SUMMARY_PATH = "review/agreement_check/agreement_summary.csv"


def main():
    friend_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FRIEND_PATH

    key = pd.read_csv(KEY_PATH)
    friend = pd.read_csv(friend_path)

    merged = key.merge(friend, on="blind_id", how="left", validate="one_to_one")

    missing = merged[merged["appearance_choice"].isna()]
    if len(missing):
        print(f"WARNING: {len(missing)} questions have no appearance answer: {missing['blind_id'].tolist()}")

    merged["appearance_agree"] = merged["appearance_choice"] == merged["ground_truth_appearance"]

    rel_rows = merged[merged["has_relation_question"]]
    rel_rows = rel_rows.assign(relation_agree=rel_rows["relation_choice"] == rel_rows["ground_truth_relation"])

    print(f"Loaded {len(merged)} questions ({len(rel_rows)} have a relation question)\n")

    print("--- Overall ---")
    print(f"Appearance agreement: {merged['appearance_agree'].mean():.1%} "
          f"({merged['appearance_agree'].sum()}/{len(merged)})")
    print(f"Relation agreement:   {rel_rows['relation_agree'].mean():.1%} "
          f"({rel_rows['relation_agree'].sum()}/{len(rel_rows)})  "
          f"[control items excluded -- no relation ground truth]")

    print("\n--- By relation_family x condition ---")
    app_by_group = merged.groupby(["relation_family", "condition"])["appearance_agree"].agg(["mean", "sum", "count"])
    rel_by_group = rel_rows.groupby(["relation_family", "condition"])["relation_agree"].agg(["mean", "sum", "count"])
    summary = app_by_group.join(rel_by_group, lsuffix="_appearance", rsuffix="_relation", how="left")
    print(summary)

    summary.to_csv(OUT_SUMMARY_PATH)
    print(f"\nWrote {OUT_SUMMARY_PATH}")

    disagreements = merged[~merged["appearance_agree"] | (merged["has_relation_question"] & ~merged["blind_id"].isin(
        rel_rows[rel_rows["relation_agree"]]["blind_id"]
    ))]
    if len(disagreements):
        print(f"\n--- {len(disagreements)} triplet_ids with at least one disagreement (for spot-checking) ---")
        print(disagreements[["blind_id", "triplet_id", "relation_family", "condition"]].to_string(index=False))


if __name__ == "__main__":
    main()
