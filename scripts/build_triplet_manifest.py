"""Assemble the final triplet manifest from human-reviewed similarity-gallery
decisions (labels/similarity_gallery_labels.csv) plus the confirmed relation-family
candidates and pool metadata.

Three triplet types go into one output manifest:

  control -- taken directly from accepted "control::" items in the gallery
    labels. Already a complete anchor+positive+negative triplet with no
    relation-family logic involved.

  conflict -- for each accepted "conflict::anchor::negative" item, the
    negative slot is exactly that accepted candidate (looks like the anchor,
    does not share its relation). The positive slot is picked from another
    confirmed same-family "fits" image via a simple round-robin over that
    family's fits list (sorted by hash), so different anchors get different
    partners instead of all pointing at one popular image. A candidate that
    was also accepted as this anchor's ALIGNED partner is skipped when
    picking the conflict positive, since that would blur conflict vs.
    aligned (the conflict positive is supposed to differ in appearance).

  aligned -- for each accepted "aligned::h1::h2" item (already a validated
    same-relation + same-appearance pair), the negative slot is a random
    background image unrelated to either.

Run scripts/consolidate_candidates.py and the similarity-retrieval pipeline
(build_similarity_pool.py + generate_similarity_gallery.py) first, and make
sure the reviewed labels/similarity_gallery_labels.csv has been pulled from GitHub.

Output: review/triplet_manifest.csv, columns:
  triplet_id, relation_family, condition,
  anchor_hash, anchor_url, anchor_caption,
  positive_hash, positive_url, positive_caption,
  negative_hash, negative_url, negative_caption

STABILITY NOTE: the conflict positive (round-robin over the fits list) and
the aligned negative (random background pick) both depend on pool state
that changes as the fits pool grows over time -- rerunning naively can
silently reassign a DIFFERENT image to a triplet_id that was already
scored on the GPU, desyncing review/triplet_results.csv from what the
manifest claims that triplet_id means (this happened once: 24 rows drifted
after the temporal-fits-pool expansion). To prevent that, every row for a
triplet_id already present in the existing OUT_PATH is copied verbatim
instead of recomputed; only genuinely new triplet_ids get fresh
assignments.
"""
import os
import random

import pandas as pd

LABELS_PATHS = [
    "labels/similarity_gallery_labels.csv",
    "labels/similarity_gallery_labels_attribute_control_v2.csv",
    "labels/similarity_gallery_labels_aligned-pair_temporal_v3.csv",
    "labels/similarity_gallery_labels_compositional_negative_v2.csv",
    "labels/similarity_gallery_labels_compositional_aligned_v2.csv",
]
CONFIRMED_PATH = "review/pool/confirmed_candidates.csv"
METADATA_PATH = "review/pool/similarity_pool_metadata.csv"
OUT_PATH = "review/triplet_manifest.csv"  # NOTE: kept at this path deliberately -- eval_triplet.py on the GPU machine reads it from here
RANDOM_STATE = 42


def load_labels():
    frames = [pd.read_csv(p) for p in LABELS_PATHS]
    return pd.concat(frames, ignore_index=True)


def image_info(meta, image_hash):
    row = meta.loc[image_hash]
    return row["url_link"], row["caption"]


def build_conflict_positive_map(fits, aligned_partners):
    """For each family, round-robin every fits image to the next one (by
    sorted hash) that was NOT also accepted as its aligned partner."""
    positive_for = {}
    for family, group in fits.groupby("family"):
        sorted_hashes = sorted(group["image_hash"].tolist())
        n = len(sorted_hashes)
        for i, h in enumerate(sorted_hashes):
            exclude = {h} | aligned_partners.get(h, set())
            for step in range(1, n):
                candidate = sorted_hashes[(i + step) % n]
                if candidate not in exclude:
                    positive_for[h] = (candidate, family)
                    break
    return positive_for


def main():
    labels = load_labels()
    confirmed = pd.read_csv(CONFIRMED_PATH)
    meta = pd.read_csv(METADATA_PATH).set_index("image_hash")
    rng = random.Random(RANDOM_STATE)

    existing = {}
    if os.path.exists(OUT_PATH):
        prev = pd.read_csv(OUT_PATH)
        existing = {row["triplet_id"]: row.to_dict() for _, row in prev.iterrows()}
        print(f"Found {len(existing)} existing triplets in {OUT_PATH} -- these will be kept unchanged")

    rows = []
    n_reused = 0

    # ---------- attribute-priority control ----------
    control_acc = labels[(labels["section"] == "attribute_control") & (labels["decision"] == "accept")]
    for _, r in control_acc.iterrows():
        triplet_id = f"control_{r['hashes'].split(',')[0][:8]}"
        if triplet_id in existing:
            rows.append(existing[triplet_id])
            n_reused += 1
            continue
        anchor_h, pos_h, neg_h = r["hashes"].split(",")
        a_url, a_cap = image_info(meta, anchor_h)
        p_url, p_cap = image_info(meta, pos_h)
        n_url, n_cap = image_info(meta, neg_h)
        rows.append({
            "triplet_id": triplet_id,
            "relation_family": "attribute_priority_control",
            "condition": "control",
            "anchor_hash": anchor_h, "anchor_url": a_url, "anchor_caption": a_cap,
            "positive_hash": pos_h, "positive_url": p_url, "positive_caption": p_cap,
            "negative_hash": neg_h, "negative_url": n_url, "negative_caption": n_cap,
        })

    # ---------- aligned ----------
    aligned_acc = labels[(labels["section"] == "aligned_pair") & (labels["decision"] == "accept")]

    aligned_partners = {}
    for _, r in aligned_acc.iterrows():
        h1, h2 = r["hashes"].split(",")
        aligned_partners.setdefault(h1, set()).add(h2)
        aligned_partners.setdefault(h2, set()).add(h1)

    bg_random = meta[(meta["group"] == "background_random") & (meta["download_ok"])]
    bg_hashes = list(bg_random.index)

    for _, r in aligned_acc.iterrows():
        h1, h2 = r["hashes"].split(",")
        family = meta.loc[h1, "family"]
        triplet_id = f"aligned_{family[:4]}_{h1[:8]}_{h2[:8]}"
        if triplet_id in existing:
            rows.append(existing[triplet_id])
            n_reused += 1
            continue
        neg_h = rng.choice([h for h in bg_hashes if h not in (h1, h2)])
        a_url, a_cap = image_info(meta, h1)
        p_url, p_cap = image_info(meta, h2)
        n_url, n_cap = image_info(meta, neg_h)
        rows.append({
            "triplet_id": triplet_id,
            "relation_family": family,
            "condition": "aligned",
            "anchor_hash": h1, "anchor_url": a_url, "anchor_caption": a_cap,
            "positive_hash": h2, "positive_url": p_url, "positive_caption": p_cap,
            "negative_hash": neg_h, "negative_url": n_url, "negative_caption": n_cap,
        })

    # ---------- conflict ----------
    fits = confirmed[confirmed["decision"] == "fits"]
    positive_for = build_conflict_positive_map(fits, aligned_partners)

    conflict_acc = labels[(labels["section"] == "conflict_negative") & (labels["decision"] == "accept")]
    n_skipped = 0
    for _, r in conflict_acc.iterrows():
        anchor_h, neg_h = r["hashes"].split(",")
        # family prefix is unknown until we resolve positive_for below, but
        # triplet_id only depends on anchor+negative, so check reuse by
        # scanning existing ids sharing this (anchor, negative) pair first
        matched_existing_id = next(
            (tid for tid, row in existing.items()
             if row.get("anchor_hash") == anchor_h and row.get("negative_hash") == neg_h
             and row.get("condition") == "conflict"),
            None,
        )
        if matched_existing_id is not None:
            rows.append(existing[matched_existing_id])
            n_reused += 1
            continue
        if anchor_h not in positive_for:
            n_skipped += 1
            continue
        pos_h, family = positive_for[anchor_h]
        a_url, a_cap = image_info(meta, anchor_h)
        p_url, p_cap = image_info(meta, pos_h)
        n_url, n_cap = image_info(meta, neg_h)
        rows.append({
            "triplet_id": f"conflict_{family[:4]}_{anchor_h[:8]}_{neg_h[:8]}",
            "relation_family": family,
            "condition": "conflict",
            "anchor_hash": anchor_h, "anchor_url": a_url, "anchor_caption": a_cap,
            "positive_hash": pos_h, "positive_url": p_url, "positive_caption": p_cap,
            "negative_hash": neg_h, "negative_url": n_url, "negative_caption": n_cap,
        })
    if n_skipped:
        print(f"WARNING: skipped {n_skipped} conflict candidates with no available positive partner")

    manifest = pd.DataFrame(rows)
    manifest.to_csv(OUT_PATH, index=False)

    print(f"\nWrote {OUT_PATH}: {len(manifest)} triplets ({n_reused} reused unchanged, "
          f"{len(manifest) - n_reused} newly computed)")
    print(manifest.groupby(["relation_family", "condition"]).size())

    anchor_counts = manifest[manifest["condition"] == "conflict"]["anchor_hash"].value_counts()
    print(f"\nConflict triplets use {anchor_counts.shape[0]} distinct anchors "
          f"(max {anchor_counts.max()} triplets share the same anchor+different negative)")


if __name__ == "__main__":
    main()
