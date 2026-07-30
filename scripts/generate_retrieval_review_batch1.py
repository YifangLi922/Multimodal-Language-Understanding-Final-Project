"""Step 2 of the retrieval pipeline: turn CLIP similarity into a reviewable
HTML gallery. Reads the embeddings produced by build_similarity_pool.py and
proposes three kinds of candidates -- nothing here is auto-accepted, every
row still needs a human "accept" click after actually looking at the images
(per proposal Section 7.3: CLIP nearest-neighbor is a candidate generator,
never the final decision).

Sections in the output gallery:
  1. Conflict-negative candidates -- for each confirmed "fits" anchor, its
     most visually similar images from the background pool (candidates for
     an image that looks like the anchor but does not share its relation).
  2. Aligned-pair candidates -- pairs of confirmed same-family anchors that
     also turn out to be visually similar (candidates for an aligned
     triplet's anchor+positive, since both already share the relation).
  3. Attribute-priority control candidates -- anchor + its nearest
     background neighbor (candidate positive) + a random background image
     (candidate negative), with no relation-family logic involved.

Run scripts/build_similarity_pool.py first.
"""
import html
import os

import numpy as np
import pandas as pd

EMBEDDINGS_PATH = "review/pool/similarity_embeddings.npz"
METADATA_PATH = "review/pool/similarity_pool_metadata.csv"
OUT_PATH = "review/galleries/retrieval_review_batch1_all_sections.html"

TOP_K_CONFLICT = 5
TOP_K_ALIGNED = 3
N_ATTRIBUTE_CONTROL_ANCHORS = 20
RANDOM_STATE = 42

CSS = """
:root { color-scheme: light dark; }
body { font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 0; padding: 0 16px 60px; background: #fafafa; color: #111; }
@media (prefers-color-scheme: dark) { body { background: #1a1a1a; color: #eee; } }
h1 { font-size: 1.4rem; }
h2 { font-size: 1.1rem; margin-top: 2rem; border-bottom: 2px solid #ccc; padding-bottom: 4px; }
.instructions { background: #fff3cd; border: 1px solid #e0c36a; padding: 10px 14px; border-radius: 6px; max-width: 900px; }
@media (prefers-color-scheme: dark) { .instructions { background: #3a3316; border-color: #6b5b1f; } }
.toolbar { position: sticky; top: 0; background: inherit; padding: 10px 0; z-index: 10; display: flex; gap: 12px; align-items: center; backdrop-filter: blur(4px); }
#export-btn { font-size: 1rem; padding: 8px 16px; cursor: pointer; border-radius: 6px; border: 1px solid #888; background: #2563eb; color: white; }
#save-status { font-size: 0.85rem; color: #666; }
.list { display: flex; flex-direction: column; gap: 14px; margin: 10px 0 20px; }
.item { border: 2px solid #ccc; border-radius: 8px; padding: 10px; background: rgba(255,255,255,0.6); display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-start; }
@media (prefers-color-scheme: dark) { .item { background: rgba(255,255,255,0.04); border-color: #444; } }
.item.mark-accept { border-color: #16a34a; }
.item.mark-reject { opacity: 0.5; border-color: #888; }
.slot { display: flex; flex-direction: column; gap: 4px; width: 190px; }
.slot img { width: 100%; height: 140px; object-fit: cover; border-radius: 4px; background: #ddd; }
.slot .role { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #2563eb; }
.slot .caption { font-size: 0.75rem; line-height: 1.2; max-height: 3.5em; overflow-y: auto; }
.slot .hash { font-family: monospace; font-size: 0.65rem; color: #888; }
.meta-col { display: flex; flex-direction: column; gap: 6px; min-width: 160px; }
.sim { font-size: 0.8rem; font-weight: 600; }
.buttons { display: flex; gap: 4px; }
.buttons button { flex: 1; font-size: 0.75rem; padding: 5px 4px; border-radius: 4px; border: 1px solid #999; background: transparent; cursor: pointer; color: inherit; }
.buttons button.selected[data-choice="accept"] { background: #16a34a; color: white; border-color: #16a34a; }
.buttons button.selected[data-choice="reject"] { background: #6b7280; color: white; border-color: #6b7280; }
.notes { font-size: 0.75rem; resize: vertical; min-height: 30px; width: 100%; }
"""

JS = """
const STORAGE_KEY = 'relsim_similarity_gallery_state_v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch (e) { state = {}; }

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  const el = document.getElementById('save-status');
  if (el) el.textContent = 'saved ' + new Date().toLocaleTimeString();
}

document.querySelectorAll('.item').forEach(item => {
  const k = item.dataset.itemId;
  const s = state[k];
  if (s) {
    if (s.decision) {
      item.querySelectorAll('button[data-choice]').forEach(b => b.classList.toggle('selected', b.dataset.choice === s.decision));
      item.classList.remove('mark-accept', 'mark-reject');
      item.classList.add('mark-' + s.decision);
    }
    if (s.notes) {
      const ta = item.querySelector('.notes');
      if (ta) ta.value = s.notes;
    }
  }

  item.querySelectorAll('button[data-choice]').forEach(btn => {
    btn.addEventListener('click', () => {
      state[k] = state[k] || {};
      state[k].decision = btn.dataset.choice;
      item.querySelectorAll('button[data-choice]').forEach(b => b.classList.toggle('selected', b === btn));
      item.classList.remove('mark-accept', 'mark-reject');
      item.classList.add('mark-' + btn.dataset.choice);
      saveState();
    });
  });

  const ta = item.querySelector('.notes');
  if (ta) {
    ta.addEventListener('input', () => {
      state[k] = state[k] || {};
      state[k].notes = ta.value;
      saveState();
    });
  }
});

function csvEscape(v) {
  v = String(v === undefined || v === null ? '' : v);
  if (/[",\\r\\n]/.test(v)) {
    v = '"' + v.replace(/"/g, '""') + '"';
  }
  return v;
}

document.getElementById('export-btn').addEventListener('click', () => {
  const rows = [['item_id', 'section', 'decision', 'notes', 'hashes', 'similarity']];
  document.querySelectorAll('.item').forEach(item => {
    const k = item.dataset.itemId;
    const s = state[k] || {};
    rows.push([
      k,
      item.dataset.section,
      s.decision || '',
      s.notes || '',
      item.dataset.hashes,
      item.dataset.similarity,
    ]);
  });
  const csv = rows.map(r => r.map(csvEscape).join(',')).join('\\r\\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'retrieval_review_batch1_all_sections.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
});
"""


def slot_html(role, meta_row):
    h = html.escape(str(meta_row["image_hash"]))
    url = html.escape(str(meta_row["url_link"]))
    cap = html.escape(str(meta_row["caption"]))[:160]
    return f'''<div class="slot">
  <div class="role">{html.escape(role)}</div>
  <a href="{url}" target="_blank" rel="noopener"><img loading="lazy" src="{url}"></a>
  <div class="hash">{h}</div>
  <div class="caption">{cap}</div>
</div>'''


def item_html(item_id, section, slots, sim_text, hashes_for_export):
    slots_html = "\n".join(slots)
    return f'''<div class="item" data-item-id="{html.escape(item_id)}" data-section="{html.escape(section)}"
     data-hashes="{html.escape(hashes_for_export)}" data-similarity="{html.escape(sim_text)}">
  {slots_html}
  <div class="meta-col">
    <div class="sim">{html.escape(sim_text)}</div>
    <div class="buttons">
      <button type="button" data-choice="accept">accept</button>
      <button type="button" data-choice="reject">reject</button>
    </div>
    <textarea class="notes" placeholder="notes (optional)"></textarea>
  </div>
</div>'''


def load():
    npz = np.load(EMBEDDINGS_PATH, allow_pickle=False)
    hashes = list(npz["hashes"])
    embeddings = npz["embeddings"]
    meta = pd.read_csv(METADATA_PATH)
    meta_by_hash = {row["image_hash"]: row for _, row in meta.iterrows()}
    return hashes, embeddings, meta_by_hash


def main():
    hashes, embeddings, meta_by_hash = load()
    hash_to_idx = {h: i for i, h in enumerate(hashes)}
    sim = embeddings @ embeddings.T

    group_of = {h: meta_by_hash[h]["group"] for h in hashes if h in meta_by_hash}
    family_of = {h: meta_by_hash[h]["family"] for h in hashes if h in meta_by_hash}

    anchor_hashes = [h for h in hashes if group_of.get(h) == "anchor"]
    background_hashes = [h for h in hashes if group_of.get(h) != "anchor"]
    background_mask = np.array([group_of.get(h) != "anchor" for h in hashes])

    conflict_items = []
    for anchor_hash in anchor_hashes:
        ai = hash_to_idx[anchor_hash]
        sims = sim[ai].copy()
        sims[ai] = -1
        masked = np.where(background_mask, sims, -1)
        top_idx = np.argsort(-masked)[:TOP_K_CONFLICT]
        for rank, idx in enumerate(top_idx):
            if masked[idx] < 0:
                continue
            cand_hash = hashes[idx]
            item_id = f"conflict::{anchor_hash}::{cand_hash}"
            slots = [
                slot_html("anchor (confirmed fits)", meta_by_hash[anchor_hash]),
                slot_html("candidate negative", meta_by_hash[cand_hash]),
            ]
            sim_text = f"cosine similarity = {sim[ai, idx]:.3f} (rank {rank + 1}/{TOP_K_CONFLICT})"
            conflict_items.append(item_html(item_id, "conflict_negative", slots, sim_text, f"{anchor_hash},{cand_hash}"))

    aligned_items = []
    seen_pairs = set()
    for anchor_hash in anchor_hashes:
        ai = hash_to_idx[anchor_hash]
        family = family_of.get(anchor_hash)
        same_family_mask = np.array([
            group_of.get(h) == "anchor" and family_of.get(h) == family and h != anchor_hash
            for h in hashes
        ])
        sims = sim[ai].copy()
        masked = np.where(same_family_mask, sims, -1)
        top_idx = np.argsort(-masked)[:TOP_K_ALIGNED]
        for idx in top_idx:
            if masked[idx] < 0:
                continue
            cand_hash = hashes[idx]
            pair_key = tuple(sorted([anchor_hash, cand_hash]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            item_id = f"aligned::{pair_key[0]}::{pair_key[1]}"
            slots = [
                slot_html(f"{family} anchor", meta_by_hash[pair_key[0]]),
                slot_html(f"{family} candidate positive", meta_by_hash[pair_key[1]]),
            ]
            sim_text = f"cosine similarity = {sim[ai, idx]:.3f}"
            aligned_items.append(item_html(item_id, "aligned_pair", slots, sim_text, f"{pair_key[0]},{pair_key[1]}"))

    rng = np.random.RandomState(RANDOM_STATE)
    control_anchor_hashes = rng.choice(
        background_hashes, size=min(N_ATTRIBUTE_CONTROL_ANCHORS, len(background_hashes)), replace=False
    )
    control_items = []
    for anchor_hash in control_anchor_hashes:
        ai = hash_to_idx[anchor_hash]
        sims = sim[ai].copy()
        sims[ai] = -np.inf
        pos_idx = int(np.argmax(sims))
        positive_hash = hashes[pos_idx]
        other_choices = [h for h in background_hashes if h not in (anchor_hash, positive_hash)]
        negative_hash = rng.choice(other_choices)
        item_id = f"control::{anchor_hash}"
        slots = [
            slot_html("anchor", meta_by_hash[anchor_hash]),
            slot_html("candidate positive (nearest neighbor)", meta_by_hash[positive_hash]),
            slot_html("candidate negative (random)", meta_by_hash[negative_hash]),
        ]
        sim_text = (
            f"sim(anchor,positive)={sim[ai, pos_idx]:.3f}  "
            f"sim(anchor,negative)={sim[ai, hash_to_idx[negative_hash]]:.3f}"
        )
        control_items.append(
            item_html(item_id, "attribute_control", slots, sim_text, f"{anchor_hash},{positive_hash},{negative_hash}")
        )

    out_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RelSim Similarity Retrieval Review</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">Export labels as CSV</button>
  <span id="save-status">not saved yet</span>
</div>
<h1>RelSim Similarity Retrieval Review</h1>
<p class="instructions">
  CLIP similarity only <b>proposes</b> candidates -- look at the actual images
  before deciding. <b>Conflict-negative candidates</b>: accept only if the
  candidate genuinely does <i>not</i> show the anchor's relation despite
  looking similar. <b>Aligned-pair candidates</b>: accept only if the two
  images also look similar to a human, not just to CLIP. <b>Attribute-control
  candidates</b>: accept only if the positive is clearly more similar in
  appearance than the negative, regardless of any relation. Choices
  auto-save to this browser (localStorage); export when done.
</p>
<h2>1. Conflict-negative candidates ({len(conflict_items)})</h2>
<div class="list">{''.join(conflict_items)}</div>
<h2>2. Aligned-pair candidates ({len(aligned_items)})</h2>
<div class="list">{''.join(aligned_items)}</div>
<h2>3. Attribute-priority control candidates ({len(control_items)})</h2>
<div class="list">{''.join(control_items)}</div>
<script>{JS}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}")
    print(f"  conflict-negative candidates: {len(conflict_items)}")
    print(f"  aligned-pair candidates: {len(aligned_items)}")
    print(f"  attribute-control candidates: {len(control_items)}")


if __name__ == "__main__":
    main()
