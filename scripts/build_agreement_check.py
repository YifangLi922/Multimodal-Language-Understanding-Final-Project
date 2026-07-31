"""Build a blind inter-annotator agreement check: stratified sample from the
frozen review/triplet_manifest.csv, packaged as a self-contained HTML page a
second annotator can label with zero knowledge of which image was originally
the positive or the negative.

Two outputs:

  review/agreement_check/answer_key.csv (SECRET -- do not send to the second
    annotator) -- maps each blind question back to its triplet_id and records
    the ground-truth answer for both questions, derived from how the triplet
    was constructed (see ground_truth() below).

  review/galleries/agreement_check_blind.html (SAFE to send) -- anchor image
    + two candidate images labeled "Candidate A" / "Candidate B" in random
    order, two forced-choice questions, export-to-CSV button. No captions, no
    hashes, no family/condition labels, no indication of which candidate was
    originally positive/negative -- all of that lives only in answer_key.csv.

Ground truth per condition (see docs/codebook_en.md and
scripts/build_triplet_manifest.py for why):
  conflict -- positive shares the anchor's relation family (round-robin
    partner, not vetted for appearance); negative was human-accepted
    specifically because it looks like the anchor AND does not share the
    relation. So: relation -> positive, appearance -> negative. This
    mismatch is the entire point of the "conflict" condition.
  aligned -- positive shares the relation family AND was human-confirmed
    visually similar; negative is a random unrelated background image. So:
    relation -> positive, appearance -> positive.
  control -- no relation-family logic is involved at all (per README/
    codebook), so the relation question has no ground truth and is omitted
    for control items. positive is the CLIP nearest-neighbor human-confirmed
    "clearly more similar in appearance"; negative is random background. So:
    appearance -> positive.

Run once. Re-running with the same RANDOM_STATE reproduces the same sample
and slot assignment (harmless if the HTML hasn't been sent out yet; DO NOT
re-run after your friend has already started labeling, since the blind_ids
would no longer line up with what she saw).
"""
import html
import os

import numpy as np
import pandas as pd

MANIFEST_PATH = "review/triplet_manifest.csv"
KEY_OUT_PATH = "review/agreement_check/answer_key.csv"
HTML_OUT_PATH = "review/galleries/agreement_check_blind.html"

SAMPLE_PLAN = {
    ("temporal_transformation", "conflict"): 6,
    ("temporal_transformation", "aligned"): 5,
    ("compositional_formation", "conflict"): 6,
    ("compositional_formation", "aligned"): 5,
    ("attribute_priority_control", "control"): 5,
}
RANDOM_STATE = 20260731

CSS = """
:root { color-scheme: light dark; }
body { font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 0; padding: 0 16px 60px; background: #fafafa; color: #111; }
@media (prefers-color-scheme: dark) { body { background: #1a1a1a; color: #eee; } }
h1 { font-size: 1.3rem; }
.instructions { background: #fff3cd; border: 1px solid #e0c36a; padding: 10px 14px; border-radius: 6px; max-width: 900px; }
@media (prefers-color-scheme: dark) { .instructions { background: #3a3316; border-color: #6b5b1f; } }
.toolbar { position: sticky; top: 0; background: inherit; padding: 10px 0; z-index: 10; display: flex; gap: 12px; align-items: center; backdrop-filter: blur(4px); }
#export-btn { font-size: 1rem; padding: 8px 16px; cursor: pointer; border-radius: 6px; border: 1px solid #888; background: #2563eb; color: white; }
#save-status { font-size: 0.85rem; color: #666; }
#progress { font-size: 0.85rem; color: #666; }
.list { display: flex; flex-direction: column; gap: 16px; margin: 10px 0 20px; }
.item { border: 2px solid #ccc; border-radius: 8px; padding: 12px; background: rgba(255,255,255,0.6); }
@media (prefers-color-scheme: dark) { .item { background: rgba(255,255,255,0.04); border-color: #444; } }
.item.mark-done { border-color: #16a34a; }
.qnum { font-weight: 700; margin-bottom: 8px; }
.images { display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 10px; }
.slot { display: flex; flex-direction: column; gap: 4px; width: 220px; }
.slot img { width: 100%; height: 170px; object-fit: cover; border-radius: 4px; background: #ddd; }
.slot .role { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #2563eb; text-align: center; }
.question { margin: 10px 0; }
.qtext { font-size: 0.9rem; margin-bottom: 6px; }
.choices { display: flex; gap: 8px; }
.choices button { flex: 1; max-width: 160px; font-size: 0.85rem; padding: 6px 10px; border-radius: 4px; border: 1px solid #999; background: transparent; cursor: pointer; color: inherit; }
.choices button.selected { background: #16a34a; color: white; border-color: #16a34a; }
.na-note { font-size: 0.8rem; color: #888; font-style: italic; }
"""

JS = """
const STORAGE_KEY = 'relsim_agreement_check_v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch (e) { state = {}; }

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  const el = document.getElementById('save-status');
  if (el) el.textContent = 'saved ' + new Date().toLocaleTimeString();
  updateProgress();
}

function updateProgress() {
  const items = document.querySelectorAll('.item');
  let done = 0;
  items.forEach(item => {
    const k = item.dataset.itemId;
    const s = state[k] || {};
    const needsRelation = item.dataset.hasRelation === '1';
    const ok = s.appearance && (!needsRelation || s.relation);
    if (ok) done++;
    item.classList.toggle('mark-done', !!ok);
  });
  const el = document.getElementById('progress');
  if (el) el.textContent = done + ' / ' + items.length + ' answered';
}

document.querySelectorAll('.item').forEach(item => {
  const k = item.dataset.itemId;
  const s = state[k] || {};
  item.querySelectorAll('.choices').forEach(group => {
    const qkey = group.dataset.q;
    const val = s[qkey];
    group.querySelectorAll('button').forEach(b => {
      b.classList.toggle('selected', val === b.dataset.choice);
      b.addEventListener('click', () => {
        state[k] = state[k] || {};
        state[k][qkey] = b.dataset.choice;
        group.querySelectorAll('button').forEach(bb => bb.classList.toggle('selected', bb === b));
        saveState();
      });
    });
  });
});
updateProgress();

function csvEscape(v) {
  v = String(v === undefined || v === null ? '' : v);
  if (/[",\\r\\n]/.test(v)) {
    v = '"' + v.replace(/"/g, '""') + '"';
  }
  return v;
}

document.getElementById('export-btn').addEventListener('click', () => {
  const rows = [['blind_id', 'relation_choice', 'appearance_choice']];
  document.querySelectorAll('.item').forEach(item => {
    const k = item.dataset.itemId;
    const s = state[k] || {};
    rows.push([k, s.relation || '', s.appearance || '']);
  });
  const csv = rows.map(r => r.map(csvEscape).join(',')).join('\\r\\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'agreement_check_blind.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
});
"""


def slot_html(label, url):
    url = html.escape(str(url))
    return f'''<div class="slot">
  <div class="role">{html.escape(label)}</div>
  <a href="{url}" target="_blank" rel="noopener"><img loading="lazy" src="{url}"></a>
</div>'''


def choice_buttons(qkey, item_id):
    return f'''<div class="choices" data-q="{qkey}">
  <button type="button" data-choice="A">Candidate A</button>
  <button type="button" data-choice="B">Candidate B</button>
</div>'''


def item_html(blind_id, qnum, anchor_url, a_url, b_url, has_relation):
    relation_block = ""
    if has_relation:
        relation_block = f'''<div class="question">
  <div class="qtext">关系问题：候选 A 和候选 B，哪一张和 anchor 背后的道理 / 逻辑 / 过程更像？</div>
  {choice_buttons("relation", blind_id)}
</div>'''
    else:
        relation_block = '<div class="na-note">（这道题不需要回答"关系问题"，只回答下面的外观问题即可）</div>'

    return f'''<div class="item" data-item-id="{blind_id}" data-has-relation="{"1" if has_relation else "0"}">
  <div class="qnum">问题 {qnum} / {blind_id}</div>
  <div class="images">
    {slot_html("Anchor", anchor_url)}
    {slot_html("Candidate A", a_url)}
    {slot_html("Candidate B", b_url)}
  </div>
  {relation_block}
  <div class="question">
    <div class="qtext">外观问题：候选 A 和候选 B，哪一张和 anchor 在物体、颜色、形状、纹理、布局上长得更像？</div>
    {choice_buttons("appearance", blind_id)}
  </div>
</div>'''


def ground_truth(condition):
    """Returns (has_relation_question, gt_relation_role, gt_appearance_role)
    where role is 'positive' or 'negative'. See module docstring for the
    reasoning behind each condition's mapping."""
    if condition == "conflict":
        return True, "positive", "negative"
    if condition == "aligned":
        return True, "positive", "positive"
    if condition == "control":
        return False, None, "positive"
    raise ValueError(f"unknown condition {condition}")


def main():
    manifest = pd.read_csv(MANIFEST_PATH)

    sampled_parts = []
    rng_sample = np.random.RandomState(RANDOM_STATE)
    for (family, condition), n in SAMPLE_PLAN.items():
        pool = manifest[(manifest["relation_family"] == family) & (manifest["condition"] == condition)]
        if len(pool) < n:
            raise ValueError(f"only {len(pool)} triplets available for {family}/{condition}, need {n}")
        picked = pool.sample(n=n, random_state=rng_sample.randint(0, 2**31 - 1))
        sampled_parts.append(picked)
    sampled = pd.concat(sampled_parts, ignore_index=True)

    # Shuffle final display order so consecutive questions don't reveal the
    # family/condition block structure to the annotator.
    sampled = sampled.sample(frac=1.0, random_state=rng_sample.randint(0, 2**31 - 1)).reset_index(drop=True)

    rng_slot = np.random.RandomState(RANDOM_STATE + 1)

    key_rows = []
    items = []
    for i, r in sampled.iterrows():
        blind_id = f"q{i + 1:02d}"
        has_relation, gt_rel_role, gt_app_role = ground_truth(r["condition"])

        flip = rng_slot.randint(0, 2) == 1  # True -> positive is slot B
        if flip:
            slot_a_role, slot_b_role = "negative", "positive"
            slot_a_hash, slot_a_url = r["negative_hash"], r["negative_url"]
            slot_b_hash, slot_b_url = r["positive_hash"], r["positive_url"]
        else:
            slot_a_role, slot_b_role = "positive", "negative"
            slot_a_hash, slot_a_url = r["positive_hash"], r["positive_url"]
            slot_b_hash, slot_b_url = r["negative_hash"], r["negative_url"]

        role_to_slot = {slot_a_role: "A", slot_b_role: "B"}
        gt_relation = role_to_slot[gt_rel_role] if has_relation else ""
        gt_appearance = role_to_slot[gt_app_role]

        key_rows.append({
            "blind_id": blind_id,
            "triplet_id": r["triplet_id"],
            "relation_family": r["relation_family"],
            "condition": r["condition"],
            "anchor_hash": r["anchor_hash"],
            "slot_a_hash": slot_a_hash,
            "slot_a_role": slot_a_role,
            "slot_b_hash": slot_b_hash,
            "slot_b_role": slot_b_role,
            "has_relation_question": has_relation,
            "ground_truth_relation": gt_relation,
            "ground_truth_appearance": gt_appearance,
        })

        items.append(item_html(blind_id, i + 1, r["anchor_url"], slot_a_url, slot_b_url, has_relation))

    os.makedirs(os.path.dirname(KEY_OUT_PATH), exist_ok=True)
    pd.DataFrame(key_rows).to_csv(KEY_OUT_PATH, index=False)

    out_html = f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>RelSim Agreement Check (Blind)</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">导出为 CSV</button>
  <span id="save-status">尚未保存</span>
  <span id="progress"></span>
</div>
<h1>RelSim 一致性检验（盲标）</h1>
<p class="instructions">
  每道题给你三张图：最上面是 anchor，下面两张是随机顺序排列的候选图 A / B。
  请回答两个问题：<br>
  1) <b>关系问题</b>：哪一张和 anchor 背后的道理 / 逻辑 / 过程更像？<br>
  2) <b>外观问题</b>：哪一张和 anchor 在物体、颜色、形状、纹理、布局上长得更像？<br>
  凭第一直觉判断即可，不需要纠结太久。答案会自动保存在浏览器里，全部答完后点"导出为 CSV"。
</p>
<h2>{len(items)} 道题</h2>
<div class="list">{''.join(items)}</div>
<script>{JS}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(HTML_OUT_PATH), exist_ok=True)
    with open(HTML_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {KEY_OUT_PATH} (SECRET -- do not share) with {len(key_rows)} rows")
    print(f"Wrote {HTML_OUT_PATH} (safe to share) with {len(items)} questions")
    print(sampled.groupby(["relation_family", "condition"]).size())


if __name__ == "__main__":
    main()
