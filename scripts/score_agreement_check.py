"""Score the second annotator's blind labels against the answer key.

Run scripts/build_agreement_check.py first, send review/galleries/
agreement_check_blind.html to the second annotator, get back their exported
agreement_check_blind.csv, then run this.

Questions with no usable answer (blank cell -- e.g. a broken/unloaded image
the annotator couldn't judge) are excluded from both the numerator and the
denominator for that dimension, not scored as a disagreement.

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
    friend["relation_choice"] = friend["relation_choice"].replace("", pd.NA)
    friend["appearance_choice"] = friend["appearance_choice"].replace("", pd.NA)

    merged = key.merge(friend, on="blind_id", how="left", validate="one_to_one")

    missing_app = merged[merged["appearance_choice"].isna()]
    if len(missing_app):
        print(f"Excluding {len(missing_app)} question(s) with no appearance answer "
              f"(e.g. broken image): {missing_app['blind_id'].tolist()}")

    missing_rel = merged[merged["has_relation_question"] & merged["relation_choice"].isna()]
    if len(missing_rel):
        print(f"Excluding {len(missing_rel)} question(s) with no relation answer: "
              f"{missing_rel['blind_id'].tolist()}")

    app_scored = merged[merged["appearance_choice"].notna()].copy()
    app_scored["appearance_agree"] = app_scored["appearance_choice"] == app_scored["ground_truth_appearance"]

    rel_scored = merged[merged["has_relation_question"] & merged["relation_choice"].notna()].copy()
    rel_scored["relation_agree"] = rel_scored["relation_choice"] == rel_scored["ground_truth_relation"]

    print(f"\nLoaded {len(merged)} questions "
          f"({int(merged['has_relation_question'].sum())} have a relation question)\n")

    print("--- Overall ---")
    print(f"Appearance agreement: {app_scored['appearance_agree'].mean():.1%} "
          f"({app_scored['appearance_agree'].sum()}/{len(app_scored)})")
    print(f"Relation agreement:   {rel_scored['relation_agree'].mean():.1%} "
          f"({rel_scored['relation_agree'].sum()}/{len(rel_scored)})  "
          f"[control items excluded -- no relation ground truth]")

    print("\n--- By relation_family x condition ---")
    app_by_group = app_scored.groupby(["relation_family", "condition"])["appearance_agree"].agg(["mean", "sum", "count"])
    rel_by_group = rel_scored.groupby(["relation_family", "condition"])["relation_agree"].agg(["mean", "sum", "count"])
    summary = app_by_group.join(rel_by_group, lsuffix="_appearance", rsuffix="_relation", how="left")
    print(summary)

    summary.to_csv(OUT_SUMMARY_PATH)
    print(f"\nWrote {OUT_SUMMARY_PATH}")

    disagree_ids = set(app_scored.loc[~app_scored["appearance_agree"], "blind_id"]) | \
        set(rel_scored.loc[~rel_scored["relation_agree"], "blind_id"])
    disagreements = merged[merged["blind_id"].isin(disagree_ids)]
    if len(disagreements):
        print(f"\n--- {len(disagreements)} question(s) with at least one disagreement (for spot-checking) ---")
        print(disagreements[["blind_id", "triplet_id", "relation_family", "condition"]].to_string(index=False))


if __name__ == "__main__":
    main()
