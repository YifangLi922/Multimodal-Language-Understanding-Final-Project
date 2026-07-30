"""Generate conflict-negative candidates for compositional_formation anchors
not covered by batch 1 (the original 9 compositional anchors already got a
top-5 search; the 29 new anchors from gallery_labels-compositional_formation_v2.csv
have never been searched at all).

Excludes every (anchor, candidate) pair already shown in
labels/similarity_gallery_labels.csv's conflict_negative section, so
previously-reviewed anchors are not repeated.
"""
import os

import numpy as np
import pandas as pd

from generate_similarity_gallery import CSS, JS, item_html, load, slot_html

LABELS_PATH = "labels/similarity_gallery_labels.csv"
OUT_PATH = "review/galleries/conflict_negative_compositional_v2.html"
FAMILY = "compositional_formation"
TOP_K_CONFLICT = 5


def already_shown_pairs():
    labels = pd.read_csv(LABELS_PATH)
    rows = labels[labels["section"] == "conflict_negative"]
    seen = set()
    for h in rows["hashes"]:
        h1, h2 = h.split(",")
        seen.add((h1, h2))
    return seen


def main():
    hashes, embeddings, meta_by_hash = load()
    hash_to_idx = {h: i for i, h in enumerate(hashes)}
    sim = embeddings @ embeddings.T

    already_shown = already_shown_pairs()

    anchor_hashes = [
        h for h in hashes
        if meta_by_hash[h]["group"] == "anchor" and meta_by_hash[h]["family"] == FAMILY
    ]
    background_mask = np.array([meta_by_hash[h]["group"] != "anchor" for h in hashes])
    print(f"{len(anchor_hashes)} confirmed {FAMILY} anchors in the pool")

    items = []
    for anchor_hash in anchor_hashes:
        ai = hash_to_idx[anchor_hash]
        sims = sim[ai].copy()
        sims[ai] = -1
        masked = np.where(background_mask, sims, -1)
        top_idx = np.argsort(-masked)[: TOP_K_CONFLICT + 5]  # a little slack to skip already-shown ones
        count_for_anchor = 0
        for rank, idx in enumerate(top_idx):
            if count_for_anchor >= TOP_K_CONFLICT:
                break
            if masked[idx] < 0:
                continue
            cand_hash = hashes[idx]
            if (anchor_hash, cand_hash) in already_shown:
                continue
            count_for_anchor += 1
            item_id = f"conflict2::{anchor_hash}::{cand_hash}"
            slots = [
                slot_html("anchor (confirmed fits)", meta_by_hash[anchor_hash]),
                slot_html("candidate negative", meta_by_hash[cand_hash]),
            ]
            sim_text = f"cosine similarity = {sim[ai, idx]:.3f}"
            items.append(item_html(item_id, "conflict_negative", slots, sim_text, f"{anchor_hash},{cand_hash}"))

    js = JS.replace("relsim_similarity_gallery_state_v1", "relsim_conflict_negative_compositional_v2_state_v1")

    out_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RelSim Compositional Conflict-Negative Review -- Batch 2</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">Export labels as CSV</button>
  <span id="save-status">not saved yet</span>
</div>
<h1>Compositional Formation Conflict-Negative Review -- Batch 2</h1>
<p class="instructions">
  Same rule as before: accept only if the candidate looks like the anchor
  in appearance AND does NOT also show compositional formation. Reject if
  it secretly also fits the relation, or if it doesn't actually look
  similar to a human eye.
</p>
<h2>Compositional conflict-negative candidates ({len(items)})</h2>
<div class="list">{''.join(items)}</div>
<script>{js}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}: {len(items)} new compositional conflict-negative candidates")


if __name__ == "__main__":
    main()
