"""Generate a self-contained HTML review gallery from caption_sample_400.csv.

Groups the 400 test-split captions into keyword-matched candidate pools per
relation family (temporal_transformation / compositional_formation /
spatial_containment), plus a collapsed "unmatched" pool for everything else.
Open the generated HTML directly in a browser -- no server needed. Labels
(fits / boundary_reject / discard) and notes are auto-saved to the browser's
localStorage as you go, and can be exported to a CSV at any time.
"""
import html
import os
import re

import pandas as pd

CSV_PATH = "data/caption_sample_400.csv"
OUT_PATH = "review/galleries/codebook_review_batch1_all_families.html"

KEYWORDS = {
    "temporal_transformation": [
        r"\btransform", r"\bstage", r"\bdecay", r"\brot(?:t|e)", r"\bripen", r"\bmelt",
        r"\bburn", r"\bburning\b", r"\bgrow(?:th|ing)?\b", r"\baging\b", r"\baged\b",
        r"\bprogress", r"\blife cycle\b", r"\bmetamorphosis\b", r"\bevolv",
        r"\bwither", r"\bbloom", r"\bweather(?:ing)?\b", r"\brust(?:ing)?\b",
        r"\bconstruction\b", r"\bdestroy", r"\bdamaged?\b", r"\bcrumbl",
        r"\bfade(?:d|ing)?\b", r"\bdissolv", r"\bbefore\b", r"\bafter\b",
    ],
    "compositional_formation": [
        r"\bform(?:s|ed|ing)?\s+(?:a|an|the)\b", r"\barrange", r"\bshaped like\b",
        r"\bspell(?:s|ing)?\b", r"\bmade of\b", r"\bmade from\b", r"\bcomposed of\b",
        r"\bassembl", r"\bmosaic\b", r"\bcollage\b", r"\bpattern\b",
        r"\bletter[s]?\b", r"\bsymbol\b", r"together (?:form|create|make)",
    ],
    "spatial_containment": [
        r"\binside\b", r"\benclos", r"\bencased?\b", r"\btrapped\b",
        r"\bcontained?\b", r"\bcontainer\b", r"\bjar\b", r"\bcage\b",
        r"\bwrapped\b", r"\bencapsulat",
    ],
}

FAMILY_LABELS = {
    "temporal_transformation": "Temporal transformation",
    "compositional_formation": "Compositional formation",
    "spatial_containment": "Spatial containment (optional third family)",
}

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
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px; margin: 10px 0 20px; }
.card { border: 2px solid #ccc; border-radius: 8px; padding: 8px; background: rgba(255,255,255,0.6); display: flex; flex-direction: column; gap: 6px; transition: border-color .15s; }
@media (prefers-color-scheme: dark) { .card { background: rgba(255,255,255,0.04); border-color: #444; } }
.card.mark-fits { border-color: #16a34a; }
.card.mark-boundary_reject { border-color: #d97706; }
.card.mark-discard { opacity: 0.45; border-color: #888; }
.card.broken { opacity: 0.3; }
.card img { width: 100%; height: 150px; object-fit: cover; border-radius: 4px; background: #ddd; }
.card .hash { font-family: monospace; font-size: 0.7rem; color: #888; }
.card .caption { font-size: 0.82rem; line-height: 1.25; max-height: 4.5em; overflow-y: auto; }
.family-badge { font-size: 0.72rem; font-weight: 600; color: #2563eb; }
.family-select { font-size: 0.78rem; }
.buttons { display: flex; gap: 4px; flex-wrap: wrap; }
.buttons button { flex: 1; font-size: 0.72rem; padding: 4px 2px; border-radius: 4px; border: 1px solid #999; background: transparent; cursor: pointer; color: inherit; }
.buttons button.selected[data-choice="fits"] { background: #16a34a; color: white; border-color: #16a34a; }
.buttons button.selected[data-choice="boundary_reject"] { background: #d97706; color: white; border-color: #d97706; }
.buttons button.selected[data-choice="discard"] { background: #6b7280; color: white; border-color: #6b7280; }
.notes { font-size: 0.75rem; resize: vertical; min-height: 32px; }
details summary { cursor: pointer; font-weight: 600; margin-top: 2rem; }
"""

JS = """
const STORAGE_KEY = 'relsim_gallery_state_v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch (e) { state = {}; }

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  const el = document.getElementById('save-status');
  if (el) el.textContent = 'saved ' + new Date().toLocaleTimeString();
}

function keyFor(card) {
  return card.dataset.hash + '::' + card.dataset.family;
}

function applyState(card) {
  const s = state[keyFor(card)];
  if (!s) return;
  if (s.decision) {
    card.querySelectorAll('button[data-choice]').forEach(b => {
      b.classList.toggle('selected', b.dataset.choice === s.decision);
    });
    card.classList.remove('mark-fits', 'mark-boundary_reject', 'mark-discard');
    card.classList.add('mark-' + s.decision);
  }
  if (s.notes) {
    const ta = card.querySelector('.notes');
    if (ta) ta.value = s.notes;
  }
  if (s.assignedFamily !== undefined) {
    const sel = card.querySelector('.family-select');
    if (sel) sel.value = s.assignedFamily;
  }
}

document.querySelectorAll('.card').forEach(card => {
  applyState(card);

  card.querySelectorAll('button[data-choice]').forEach(btn => {
    btn.addEventListener('click', () => {
      const k = keyFor(card);
      state[k] = state[k] || {};
      state[k].decision = btn.dataset.choice;
      card.querySelectorAll('button[data-choice]').forEach(b => b.classList.toggle('selected', b === btn));
      card.classList.remove('mark-fits', 'mark-boundary_reject', 'mark-discard');
      card.classList.add('mark-' + btn.dataset.choice);
      saveState();
    });
  });

  const ta = card.querySelector('.notes');
  if (ta) {
    ta.addEventListener('input', () => {
      const k = keyFor(card);
      state[k] = state[k] || {};
      state[k].notes = ta.value;
      saveState();
    });
  }

  const sel = card.querySelector('.family-select');
  if (sel) {
    sel.addEventListener('change', () => {
      const k = keyFor(card);
      state[k] = state[k] || {};
      state[k].assignedFamily = sel.value;
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
  const rows = [['image_hash', 'family_shown', 'assigned_family', 'decision', 'notes', 'url_link', 'caption']];
  document.querySelectorAll('.card').forEach(card => {
    const k = keyFor(card);
    const s = state[k] || {};
    const hash = card.dataset.hash;
    const family = card.dataset.family;
    const img = card.querySelector('img');
    const url = img ? img.getAttribute('src') : '';
    const captionEl = card.querySelector('.caption');
    const caption = captionEl ? captionEl.textContent : '';
    rows.push([hash, family, s.assignedFamily || '', s.decision || '', s.notes || '', url, caption]);
  });
  const csv = rows.map(r => r.map(csvEscape).join(',')).join('\\r\\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'codebook_review_batch1_all_families.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
});
"""


def card_html(row, family, fixed_family=True):
    h = html.escape(str(row["image_hash"]))
    url = html.escape(str(row["url_link"]))
    cap = html.escape(str(row["caption"]))
    if fixed_family:
        control = f'<span class="family-badge">{html.escape(FAMILY_LABELS.get(family, family))}</span>'
    else:
        control = (
            '<select class="family-select">'
            '<option value="">-- assign family --</option>'
            '<option value="temporal_transformation">Temporal transformation</option>'
            '<option value="compositional_formation">Compositional formation</option>'
            '<option value="spatial_containment">Spatial containment</option>'
            '<option value="other">Other / not useful</option>'
            '</select>'
        )
    return f'''<div class="card" data-hash="{h}" data-family="{html.escape(family)}">
  <a href="{url}" target="_blank" rel="noopener"><img loading="lazy" src="{url}" onerror="this.closest('.card').classList.add('broken')"></a>
  {control}
  <div class="hash">{h}</div>
  <div class="caption">{cap}</div>
  <div class="buttons">
    <button type="button" data-choice="fits">fits</button>
    <button type="button" data-choice="boundary_reject">boundary_reject</button>
    <button type="button" data-choice="discard">discard</button>
  </div>
  <textarea class="notes" placeholder="notes (optional)"></textarea>
</div>'''


def build_html(family_rows, other_rows, title="RelSim Candidate Review Gallery",
               storage_key="relsim_gallery_state_v1"):
    sections = []
    for family, rows in family_rows.items():
        cards = "\n".join(card_html(r, family, fixed_family=True) for r in rows)
        label = html.escape(FAMILY_LABELS.get(family, family))
        sections.append(
            f'<section><h2>{label} &mdash; {len(rows)} candidates</h2><div class="grid">{cards}</div></section>'
        )

    other_section = ""
    if other_rows:
        other_cards = "\n".join(card_html(r, "unmatched", fixed_family=False) for r in other_rows)
        other_section = (
            "<details><summary>Other / unmatched captions "
            f"&mdash; {len(other_rows)} rows (expand only if you need more candidates, "
            "e.g. for the second relation family)</summary>"
            f'<div class="grid">{other_cards}</div></details>'
        )

    js = JS.replace("relsim_gallery_state_v1", storage_key)
    title_esc = html.escape(title)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title_esc}</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar">
  <button id="export-btn">Export labels as CSV</button>
  <span id="save-status">not saved yet</span>
</div>
<h1>{title_esc}</h1>
<p class="instructions">
  For each image, open the codebook criteria for that relation family and decide:
  <b>fits</b> (clearly satisfies inclusion criteria) / <b>boundary_reject</b>
  (looks related but fails inclusion or hits an exclusion criterion) / <b>discard</b>
  (not relevant, or the image link is broken). Click the original image to open the
  full-size source in a new tab. Your choices auto-save in this browser
  (localStorage) as you go, so refreshing the page will not lose progress. When
  done, click <b>Export labels as CSV</b> to download your decisions.
</p>
{''.join(sections)}
{other_section}
<script>{js}</script>
</body>
</html>"""


def main():
    df = pd.read_csv(CSV_PATH)
    cap_lower = df["caption"].fillna("").str.lower()

    matched_hashes = set()
    family_rows = {}
    for family, patterns in KEYWORDS.items():
        combined = "|".join(patterns)
        mask = cap_lower.str.contains(combined, regex=True, na=False)
        rows = df.loc[mask].to_dict("records")
        family_rows[family] = rows
        matched_hashes.update(r["image_hash"] for r in rows)

    other_rows = df.loc[~df["image_hash"].isin(matched_hashes)].to_dict("records")

    out_html = build_html(family_rows, other_rows)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"Wrote {OUT_PATH}")
    for family, rows in family_rows.items():
        print(f"  {family}: {len(rows)} candidates")
    print(f"  other/unmatched: {len(other_rows)}")


if __name__ == "__main__":
    main()
