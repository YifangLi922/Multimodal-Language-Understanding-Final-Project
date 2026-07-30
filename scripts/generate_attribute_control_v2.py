"""Generate a second batch of attribute-priority-control candidates.

Batch 1 (N_ATTRIBUTE_CONTROL_ANCHORS=20 in generate_similarity_gallery.py)
yielded 15 accepted triplets -- short of the ~20-25 target in the proposal.
This reuses the already-computed CLIP embeddings (no re-downloading, no
GPU needed), excludes anchors already used in batch 1 (read from
labels/similarity_gallery_labels.csv), and proposes a fresh batch of
anchor + nearest-neighbor-positive + random-negative candidates in a
separate, non-overwriting gallery page.

Judgment criterion is unchanged from batch 1: ignore any relation entirely.
Accept only if a person would clearly agree the candidate positive looks
more similar in appearance (objects, color, shape, texture, style, layout)
to the anchor than the candidate negative does.
"""
import os

import numpy as np
import pandas as pd

from generate_similarity_gallery import CSS, JS, item_html, load, slot_html

LABELS_PATH = "labels/similarity_gallery_labels.csv"
OUT_PATH = "review/galleries/attribute_control_gallery_v2.html"
N_NEW_ANCHORS = 30
RANDOM_STATE = 43  # different draw from batch 1 (which used 42)


def already_used_anchors():
    labels = pd.read_csv(LABELS_PATH)
    control_rows = labels[labels["section"] == "attribute_control"]
    return set(h.split(",")[0] for h in control_rows["hashes"])


def main():
    hashes, embeddings, meta_by_hash = load()
    hash_to_idx = {h: i for i, h in enumerate(hashes)}
    sim = embeddings @ embeddings.T

    background_hashes = [h for h in hashes if meta_by_hash[h]["group"] != "anchor"]
    used = already_used_anchors()
    pool = [h for h in background_hashes if h not in used]
    print(f"Excluding {len(used)} anchors already used in batch 1; {len(pool)} candidates remain")

    rng = np.random.RandomState(RANDOM_STATE)
    n = min(N_NEW_ANCHORS, len(pool))
    anchor_hashes = rng.choice(pool, size=n, replace=False)

    items = []
    for anchor_hash in anchor_hashes:
        ai = hash_to_idx[anchor_hash]
        sims = sim[ai].copy()
        sims[ai] = -np.inf
        pos_idx = int(np.argmax(sims))
        positive_hash = hashes[pos_idx]
        other_choices = [h for h in background_hashes if h not in (anchor_hash, positive_hash)]
        negative_hash = rng.choice(other_choices)
        item_id = f"control2::{anchor_hash}"
        slots = [
            slot_html("anchor", meta_by_hash[anchor_hash]),
            slot_html("candidate positive (nearest neighbor)", meta_by_hash[positive_hash]),
            slot_html("candidate negative (random)", meta_by_hash[negative_hash]),
        ]
        sim_text = (
            f"sim(anchor,positive)={sim[ai, pos_idx]:.3f}  "
            f"sim(anchor,negative)={sim[ai, hash_to_idx[negative_hash]]:.3f}"
        )
        items.append(
            item_html(item_id, "attribute_control", slots, sim_text, f"{anchor_hash},{positive_hash},{negative_hash}")
        )

    js = JS.replace("relsim_similarity_gallery_state_v1", "relsim_attribute_control_v2_state_v1")

    out_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RelSim Attribute-Control Review -- Batch 2</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">Export labels as CSV</button>
  <span id="save-status">not saved yet</span>
</div>
<h1>Attribute-Priority Control Review -- Batch 2</h1>
<p class="instructions">
  Same rule as batch 1: ignore any relation entirely. Accept only if a
  person would clearly agree the candidate positive looks more similar in
  appearance (objects, color, shape, texture, style, layout) to the anchor
  than the candidate negative does. Choices auto-save to this browser
  (localStorage, separate from batch 1's) and can be exported to CSV.
</p>
<h2>Attribute-priority control candidates ({len(items)})</h2>
<div class="list">{''.join(items)}</div>
<script>{js}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}: {len(items)} new attribute-control candidates")


if __name__ == "__main__":
    main()
