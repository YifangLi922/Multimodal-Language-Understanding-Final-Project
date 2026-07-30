"""Generate a third batch of temporal_transformation aligned-pair candidates,
now searching the EXPANDED fits pool (47 confirmed temporal fits, up from 22
after codebook_review_temporal_batch3.csv).

Batch 1 (top-3 same-family neighbors, all families) yielded 4 accepted
pairs. Batch 2 (top-10 among the same original 22 anchors) was reviewed but
not exported -- the candidates were judged too weak, which is exactly why
the fits pool itself needed to grow rather than just searching deeper among
the same small set. This batch searches top-10 same-family neighbors again,
but now among all 47 confirmed temporal anchors, and excludes every pair
already shown in batch 1 (from labels/retrieval_review_batch1_all_sections.csv) or
batch 2 (parsed directly from review/galleries/retrieval_review_aligned_pair_temporal_batch2_UNUSED.html,
since that batch was viewed but never exported).
"""
import os
import re

import numpy as np
import pandas as pd

from generate_retrieval_review_batch1 import CSS, JS, item_html, load, slot_html

LABELS_PATH = "labels/retrieval_review_batch1_all_sections.csv"
BATCH2_HTML_PATH = "review/galleries/retrieval_review_aligned_pair_temporal_batch2_UNUSED.html"
OUT_PATH = "review/galleries/retrieval_review_aligned_pair_temporal_batch3.html"
FAMILY = "temporal_transformation"
TOP_K_ALIGNED = 10


def already_reviewed_pairs():
    seen = set()

    labels = pd.read_csv(LABELS_PATH)
    aligned_rows = labels[labels["section"] == "aligned_pair"]
    for h in aligned_rows["hashes"]:
        h1, h2 = h.split(",")
        seen.add(frozenset((h1, h2)))

    batch2_html = open(BATCH2_HTML_PATH, encoding="utf-8").read()
    for h1, h2 in re.findall(r'data-item-id="aligned2::([a-f0-9]+)::([a-f0-9]+)"', batch2_html):
        seen.add(frozenset((h1, h2)))

    return seen


def main():
    hashes, embeddings, meta_by_hash = load()
    hash_to_idx = {h: i for i, h in enumerate(hashes)}
    sim = embeddings @ embeddings.T

    already_seen = already_reviewed_pairs()
    print(f"Excluding {len(already_seen)} pairs already shown in batch 1 or 2")

    family_anchor_hashes = [
        h for h in hashes
        if meta_by_hash[h]["group"] == "anchor" and meta_by_hash[h]["family"] == FAMILY
    ]
    print(f"{len(family_anchor_hashes)} confirmed {FAMILY} anchors in the rebuilt pool")

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
            item_id = f"aligned3::{sorted_pair[0]}::{sorted_pair[1]}"
            slots = [
                slot_html(f"{FAMILY} anchor", meta_by_hash[sorted_pair[0]]),
                slot_html(f"{FAMILY} candidate positive", meta_by_hash[sorted_pair[1]]),
            ]
            sim_text = f"cosine similarity = {sim[ai, idx]:.3f}"
            items.append(item_html(item_id, "aligned_pair", slots, sim_text, f"{sorted_pair[0]},{sorted_pair[1]}"))

    js = JS.replace("relsim_similarity_gallery_state_v1", "relsim_aligned_pair_temporal_v3_state_v1")
    js = js.replace("retrieval_review_batch1_all_sections.csv", "retrieval_review_aligned_pair_temporal_batch3.csv")

    out_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RelSim Temporal Aligned-Pair Review -- Batch 3</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">Export labels as CSV</button>
  <span id="save-status">not saved yet</span>
</div>
<h1>Temporal Transformation Aligned-Pair Review -- Batch 3 (expanded pool)</h1>
<p class="instructions">
  Both images in every pair are already confirmed temporal_transformation
  fits -- the relation is already guaranteed, do not re-check it. The only
  question: do these two images ALSO happen to look similar in appearance
  to a human (not just to CLIP)? Accept only if yes. Now searching among
  47 confirmed temporal fits (up from 22 in batch 1/2), so there are more
  real combinations to find a genuine appearance match in.
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
