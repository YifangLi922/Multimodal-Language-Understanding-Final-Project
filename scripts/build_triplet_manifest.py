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
"""
import random

import pandas as pd

LABELS_PATH = "labels/similarity_gallery_labels.csv"
CONFIRMED_PATH = "review/pool/confirmed_candidates.csv"
METADATA_PATH = "review/pool/similarity_pool_metadata.csv"
OUT_PATH = "review/triplet_manifest.csv"  # NOTE: kept at this path deliberately -- eval_triplet.py on the GPU machine reads it from here
RANDOM_STATE = 42


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
    labels = pd.read_csv(LABELS_PATH)
    confirmed = pd.read_csv(CONFIRMED_PATH)
    meta = pd.read_csv(METADATA_PATH).set_index("image_hash")
    rng = random.Random(RANDOM_STATE)

    rows = []

    # ---------- attribute-priority control ----------
    control_acc = labels[(labels["section"] == "attribute_control") & (labels["decision"] == "accept")]
    for _, r in control_acc.iterrows():
        anchor_h, pos_h, neg_h = r["hashes"].split(",")
        a_url, a_cap = image_info(meta, anchor_h)
        p_url, p_cap = image_info(meta, pos_h)
        n_url, n_cap = image_info(meta, neg_h)
        rows.append({
            "triplet_id": f"control_{anchor_h[:8]}",
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
        neg_h = rng.choice([h for h in bg_hashes if h not in (h1, h2)])
        a_url, a_cap = image_info(meta, h1)
        p_url, p_cap = image_info(meta, h2)
        n_url, n_cap = image_info(meta, neg_h)
        rows.append({
            "triplet_id": f"aligned_{family[:4]}_{h1[:8]}_{h2[:8]}",
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

    print(f"\nWrote {OUT_PATH}: {len(manifest)} triplets")
    print(manifest.groupby(["relation_family", "condition"]).size())

    anchor_counts = manifest[manifest["condition"] == "conflict"]["anchor_hash"].value_counts()
    print(f"\nConflict triplets use {anchor_counts.shape[0]} distinct anchors "
          f"(max {anchor_counts.max()} triplets share the same anchor+different negative)")


if __name__ == "__main__":
    main()
