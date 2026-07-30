"""Generate a second batch of temporal_transformation aligned-pair candidates.

Batch 1 (TOP_K_ALIGNED=3 in generate_retrieval_review_batch1.py, searched across
all confirmed families) only yielded 4 accepted temporal aligned pairs --
short of the proposal's ~20-25 target. This widens the search depth to the
top 10 same-family neighbors per anchor (still among the same 22 confirmed
temporal fits -- no new images, no GPU, no re-downloading), and excludes
every (anchor, candidate) pair already reviewed in
labels/retrieval_review_batch1_all_sections.csv's aligned_pair section so you only see
genuinely new candidates.

Judgment criterion is unchanged: relation is already guaranteed (both images
are confirmed temporal_transformation fits) -- the only question is whether
the two images ALSO happen to look similar in appearance to a human.
"""
import os

import numpy as np
import pandas as pd

from generate_retrieval_review_batch1 import CSS, JS, item_html, load, slot_html

LABELS_PATH = "labels/retrieval_review_batch1_all_sections.csv"
OUT_PATH = "review/galleries/retrieval_review_aligned_pair_temporal_batch2_UNUSED.html"
FAMILY = "temporal_transformation"
TOP_K_ALIGNED = 10


def already_reviewed_pairs():
    labels = pd.read_csv(LABELS_PATH)
    aligned_rows = labels[labels["section"] == "aligned_pair"]
    seen = set()
    for h in aligned_rows["hashes"]:
        h1, h2 = h.split(",")
        seen.add(frozenset((h1, h2)))
    return seen


def main():
    hashes, embeddings, meta_by_hash = load()
    hash_to_idx = {h: i for i, h in enumerate(hashes)}
    sim = embeddings @ embeddings.T

    already_seen = already_reviewed_pairs()

    family_anchor_hashes = [
        h for h in hashes
        if meta_by_hash[h]["group"] == "anchor" and meta_by_hash[h]["family"] == FAMILY
    ]
    print(f"{len(family_anchor_hashes)} confirmed {FAMILY} anchors in the pool")

    items = []
    seen_new_pairs = set()
    for anchor_hash in family_anchor_hashes:
        ai = hash_to_idx[anchor_hash]
        same_family_mask = np.array([
            meta_by_hash[h]["group"] == "anchor" and meta_by_hash[h]["family"] == FAMILY and h != anchor_hash
            for h in hashes
        ])
        sims = sim[ai].copy()
        masked = np.where(same_family_mask, sims, -1)
        top_idx = np.argsort(-masked)[:TOP_K_ALIGNED]
        for idx in top_idx:
            if masked[idx] < 0:
                continue
            cand_hash = hashes[idx]
            pair_key = frozenset((anchor_hash, cand_hash))
            if pair_key in already_seen or pair_key in seen_new_pairs:
                continue
            seen_new_pairs.add(pair_key)
            sorted_pair = sorted(pair_key)
            item_id = f"aligned2::{sorted_pair[0]}::{sorted_pair[1]}"
            slots = [
                slot_html(f"{FAMILY} anchor", meta_by_hash[sorted_pair[0]]),
                slot_html(f"{FAMILY} candidate positive", meta_by_hash[sorted_pair[1]]),
            ]
            sim_text = f"cosine similarity = {sim[ai, idx]:.3f}"
            items.append(item_html(item_id, "aligned_pair", slots, sim_text, f"{sorted_pair[0]},{sorted_pair[1]}"))

    js = JS.replace("relsim_similarity_gallery_state_v1", "relsim_aligned_pair_temporal_v2_state_v1")
    js = js.replace("retrieval_review_batch1_all_sections.csv", "retrieval_review_aligned_pair_temporal_batch2_UNUSED.csv")

    out_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RelSim Temporal Aligned-Pair Review -- Batch 2</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">Export labels as CSV</button>
  <span id="save-status">not saved yet</span>
</div>
<h1>Temporal Transformation Aligned-Pair Review -- Batch 2</h1>
<p class="instructions">
  Both images in every pair are already confirmed temporal_transformation
  fits -- the relation is already guaranteed, do not re-check it. The only
  question: do these two images ALSO happen to look similar in appearance
  to a human (not just to CLIP)? Accept only if yes. These are new pairs
  not shown in batch 1 (deeper search radius: top {TOP_K_ALIGNED} same-family
  neighbors per anchor instead of top 3).
</p>
<h2>Temporal aligned-pair candidates ({len(items)})</h2>
<div class="list">{''.join(items)}</div>
<script>{js}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}: {len(items)} new temporal aligned-pair candidates")


if __name__ == "__main__":
    main()
