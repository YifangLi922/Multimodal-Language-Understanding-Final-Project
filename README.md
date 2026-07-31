# Where Does RelSim Help?

### A Controlled Diagnostic Evaluation Across Relation Families and Relation–Appearance Conditions

This project is a small-scale diagnostic evaluation of **RelSim** (Nguyen et al., *Relational Visual Similarity*, CVPR 2026; arXiv:2512.07833), a vision-language model fine-tuned (Qwen2.5-VL-7B-Instruct + LoRA) to judge **relational similarity** between images — whether two images are similar because of a shared underlying relation or process, even when they look completely different on the surface.

Widely used visual-similarity models such as CLIP and DINO are strong at **attribute similarity**: recognizing that two images contain similar objects, colors, shapes, or layouts. RelSim is trained to additionally capture **relational similarity** — for example, recognizing that a video of a match burning down and a video of fruit decaying share the abstract relation "irreversible change over time," despite having nothing in common visually.

The original RelSim paper evaluates the model mainly through aggregate retrieval metrics. This project instead asks a narrower, controlled question:

> **Does RelSim's advantage over CLIP/DINO differ across relation types, and does that advantage grow specifically when appearance cues are misleading?**

## Research Questions

- **RQ1: Relation-family variation.** Does RelSim's advantage over CLIP/DINO differ across relation families?
- **RQ2: Conflict sensitivity.** Within a relation family, is RelSim's advantage larger when appearance cues *conflict* with the correct relational answer than when they *align* with it?
- **RQ3: Attribute-oriented performance.** On a control set where the correct answer is determined by visible appearance alone, does RelSim remain competitive with CLIP/DINO?

Two relation families are tested — **temporal transformation** (an object/process visibly changing state over time) and **compositional formation** (multiple visible parts arranged into a recognizable whole) — each evaluated under two conditions:

- **Conflict**: the correct answer shares the anchor's *relation* but differs in *appearance*; the wrong answer looks more similar in appearance but does not share the relation.
- **Aligned**: the correct answer shares both relation and appearance (a control condition where appearance and relation point the same way).

A third, relation-independent **attribute-priority control** set tests pure appearance similarity (RQ3), unrelated to either relation family.

## Key Results

Triplet accuracy (`sim(anchor, positive) > sim(anchor, negative)`) across 169/175 scored triplets:

| Relation family | Condition | n | CLIP | DINO | RelSim |
|---|---|---|---|---|---|
| Temporal transformation | conflict | 35 | 0.0% | 17.1% | **48.6%** |
| Temporal transformation | aligned | 28 | 92.9% | 92.9% | 100.0% |
| Compositional formation | conflict | 54 | 0.0% | 18.5% | **22.2%** |
| Compositional formation | aligned | 22 | 81.8% | 86.4% | 90.9% |
| Attribute-priority control | control | 30 | 100.0% | 96.7% | 90.0% |

**Summary of findings:**
- In the **aligned** (control) condition, all three models perform comparably and near ceiling for both relation families — this condition is easy by design.
- In the **conflict** condition, CLIP fails completely (0% on both families across 89 triplets combined) and DINO performs near or below chance, while RelSim is clearly better than both baselines. This shows the conflict triplets are doing their job: appearance is genuinely misleading for appearance-only models.
- RelSim's advantage over the baselines is **much larger for temporal transformation** (+31–49 percentage points) **than for compositional formation** (+4–22 points) — evidence that RelSim's relational advantage is heterogeneous across relation types (RQ1), and that conflict sensitivity (RQ2) is clearly demonstrated for temporal transformation but only weakly for compositional formation.
- On the attribute-priority control, RelSim (90.0%) is close to but slightly below CLIP/DINO (96.7–100%) — no strong evidence of degraded appearance sensitivity from fine-tuning (RQ3).
- The full per-triplet results and bootstrap confidence intervals are in `review/triplet_results.csv` and `review/triplet_accuracy_summary.csv`.

## Inter-Annotator Agreement Check

All codebook-review and retrieval-review accept/reject decisions that produced the 175 final triplets were made by a single annotator (see Known Limitations). To check that these decisions are not idiosyncratic to that one person, a second, independent annotator blind-labeled a stratified random sample of **27/175 triplets (~15%)** — 6 temporal-transformation conflict, 5 temporal-transformation aligned, 6 compositional-formation conflict, 5 compositional-formation aligned, 5 attribute-priority control.

**Procedure.** For each sampled triplet, the second annotator saw only the anchor image plus the positive/negative images relabeled "Candidate A" / "Candidate B" in randomized order — no captions, no hash IDs, no relation-family or condition labels, and no indication of which candidate was originally the positive or negative. Working from `docs/codebook_zh.md` alone, they answered two forced-choice questions per triplet: which candidate shares more of the anchor's underlying *relation*, and which candidate looks more similar in *appearance*. Their answers were then compared against the original labeling decision.

**Results** (one triplet excluded from both dimensions — a broken anchor image URL — leaving n=26 for appearance, n=21 for relation; the 5 control triplets are excluded from the relation dimension since the control condition has no relation-family ground truth to compare against):

| Relation family | Condition | Appearance agreement | Relation agreement |
|---|---|---|---|
| Attribute-priority control | control | 80.0% (4/5) | — |
| Compositional formation | aligned | 100.0% (5/5) | 100.0% (5/5) |
| Compositional formation | conflict | 100.0% (5/5) | 100.0% (5/5) |
| Temporal transformation | aligned | 100.0% (5/5) | 60.0% (3/5) |
| Temporal transformation | conflict | 83.3% (5/6) | 100.0% (6/6) |
| **Overall** | | **92.3% (24/26)** | **90.5% (19/21)** |

Overall agreement is high on both dimensions, supporting that the triplet construction reflects the written codebook rather than one annotator's idiosyncratic judgment. The one weak cell — temporal-transformation aligned, 60% relation agreement (2/5 disagreements) — is a small sample but worth flagging: it suggests the temporal-transformation boundary is harder to apply consistently than compositional-formation, consistent with the codebook's own note (`docs/codebook_en.md`, Section 1) that captions claiming "transform/progress/stages" often do not match what the image actually shows.

Tooling: `scripts/build_agreement_check.py` draws the stratified sample and generates the blind-labeling gallery plus a private answer key (`review/agreement_check/answer_key.csv`, intentionally **not** committed — the repo is public, and publishing the answer key would let the second annotator or anyone else discover it, invalidating the blind design). `scripts/score_agreement_check.py` compares the returned labels (`labels/agreement_check_friend.csv`) against that key and writes `review/agreement_check/agreement_summary.csv`.

## Repository Structure

```
├── data/
│   └── caption_sample_400.csv          # 400-row random sample of the official test split's captions
│
├── labels/                             # Raw human-annotation exports (browser-exported CSVs)
│   ├── codebook_review_*.csv           # fits / boundary_reject / discard decisions -> relation-family membership
│   ├── retrieval_review_*.csv          # accept / reject decisions on CLIP-proposed triplet candidates
│   └── agreement_check_friend.csv      # second annotator's blind labels (see "Inter-Annotator Agreement Check")
│
├── review/
│   ├── galleries/                      # Self-contained HTML review tools (open directly in a browser)
│   │   ├── codebook_review_*.html      # paired 1:1 with labels/codebook_review_*.csv
│   │   ├── retrieval_review_*.html     # paired 1:1 with labels/retrieval_review_*.csv
│   │   └── agreement_check_blind.html  # blind-labeling tool for the second annotator (no answer leakage)
│   ├── pool/
│   │   ├── confirmed_candidates.csv    # consolidated fits/boundary_reject candidates (both families)
│   │   ├── similarity_embeddings.npz   # CLIP embeddings for the full candidate + background pool
│   │   ├── similarity_pool_metadata.csv
│   │   └── similarity_download_failures.csv
│   ├── archive/
│   │   ├── images/                     # permanent local copies of every image used in the final triplets
│   │   └── image_archive_index.csv     # hash -> local path -> source URL -> caption
│   ├── agreement_check/
│   │   ├── answer_key.csv              # NOT committed (gitignored on purpose) -- private ground truth for the blind check
│   │   └── agreement_summary.csv       # agreement rate by relation_family x condition (committed, no answer leakage)
│   ├── triplet_manifest.csv            # the 175 final triplets (anchor/positive/negative + metadata)
│   ├── triplet_results.csv             # per-triplet, per-model similarity scores and correctness
│   ├── triplet_accuracy_summary.csv    # accuracy by relation_family x condition x model
│   ├── statistics_accuracy_with_ci.csv # accuracy + triplet-level bootstrap 95% CI per cell
│   ├── statistics_paired_gaps.csv      # RelSim-CLIP / RelSim-DINO accuracy gaps per cell
│   ├── statistics_key_comparisons.csv  # conflict-vs-aligned gap, family-vs-family gap (RQ1/RQ2)
│   ├── validation_record.csv           # traces every final triplet back to its human accept decision
│   └── qualitative_cases.csv           # RelSim-only-correct and all-models-wrong case studies
│
├── docs/
│   ├── codebook_zh.md                  # annotation codebook (Chinese draft, for internal use only)
│   └── codebook_en.md                  # annotation codebook (English, formal version)
│
└── scripts/                            # see "Pipeline" below for what each stage does
```

## Pipeline

The benchmark was built in two review stages, followed by triplet assembly and model scoring. Every stage's HTML tool and CSV output share the same name (e.g. `codebook_review_temporal_batch2.html` ↔ `labels/codebook_review_temporal_batch2.csv`).

**1. Codebook review** — decides whether an image belongs to a relation family (`fits` / `boundary_reject` / `discard`), against the criteria in `docs/codebook_en.md`.
- `scripts/generate_codebook_review_batch1.py`, `..._temporal_batch2.py`, `..._temporal_batch3.py`, `..._compositional_batch2.py` each scan the official test split (14,881 rows) for family-specific caption keywords and render a labeling gallery.
- `scripts/consolidate_candidates.py` merges every `labels/codebook_review_*.csv` into `review/pool/confirmed_candidates.csv`.

**2. Retrieval review** — proposes conflict-negative, aligned-pair, and attribute-control candidates via CLIP similarity search over the confirmed candidates, for a human to accept/reject (CLIP never auto-decides a label; see Section 7.3 of the original design notes for why).
- `scripts/build_similarity_pool.py` downloads images and computes CLIP embeddings for every confirmed candidate plus a random background sample (`review/pool/`).
- `scripts/generate_retrieval_review_batch1.py` and the family/condition-specific follow-up batches (`..._attribute_control_batch2.py`, `..._aligned_pair_temporal_batch3.py`, `..._conflict_negative_compositional_batch2.py`, `..._aligned_pair_compositional_batch2.py`) render the accept/reject galleries.

**3. Triplet assembly** — `scripts/build_triplet_manifest.py` combines every accepted retrieval-review decision with the confirmed candidates into `review/triplet_manifest.csv`. Conflict positives are assigned via round-robin over each family's fits list; aligned negatives are random unrelated background images. Re-running this script never reassigns an already-existing triplet_id, so previously GPU-scored results stay valid.

**4. Model scoring** — `scripts/eval_triplet.py` (requires the `relsim` package, its LoRA checkpoint, and a GPU) downloads every image referenced in the manifest, scores every triplet with RelSim, CLIP (`openai/clip-vit-base-patch32`), and DINO (`facebook/dinov2-base`), and writes `review/triplet_results.csv` + `review/triplet_accuracy_summary.csv`. It resumes from existing results, so re-running after adding new triplets only scores what's new.

**5. Inter-annotator agreement check** (GPU-free) — `scripts/build_agreement_check.py` draws a stratified sample from the frozen `review/triplet_manifest.csv` and renders `review/galleries/agreement_check_blind.html`, a self-contained blind-labeling tool with no leaked positive/negative labels, sent to a second annotator. `scripts/score_agreement_check.py` compares their returned labels against the private answer key and writes `review/agreement_check/agreement_summary.csv`. See "Inter-Annotator Agreement Check" above for the results and methodology.

**Supporting scripts:**
- `scripts/archive_triplet_images.py` — permanently archives every image used in the final manifest (guards against link rot).
- `scripts/compile_validation_record.py` — traces every final triplet back to its specific human accept decision.
- `scripts/extract_qualitative_cases.py` — pulls RelSim-only-correct and all-models-wrong cases for qualitative analysis.
- `scripts/compute_final_statistics.py` — computes accuracy, triplet-level bootstrap 95% CIs, and paired model gaps from `review/triplet_results.csv` (no GPU needed).

## Data and Models

- **Dataset**: [`thaoshibe/anonymous-captions-114k`](https://huggingface.co/datasets/thaoshibe/anonymous-captions-114k) (official test split, 14,881 rows — captions are machine-generated and used only for candidate retrieval, never as ground truth; family membership is always decided by looking at the image itself).
- **RelSim**: Qwen2.5-VL-7B-Instruct + [`thaoshibe/relsim-qwenvl25-lora`](https://huggingface.co/thaoshibe/relsim-qwenvl25-lora), scored via the official `relsim` package.
- **CLIP**: `openai/clip-vit-base-patch32`, cosine similarity.
- **DINO**: `facebook/dinov2-base`, cosine similarity.
- No model is trained in this project; all evaluation is inference-only.

## Reproducing the Pipeline

```bash
# 1. Codebook review (repeat per batch as needed)
python scripts/generate_codebook_review_batch1.py
# -> open review/galleries/codebook_review_batch1_all_families.html, label, export to labels/

python scripts/consolidate_candidates.py

# 2. Retrieval review
python scripts/build_similarity_pool.py
python scripts/generate_retrieval_review_batch1.py
# -> open the gallery, label, export to labels/

# 3. Assemble the triplet manifest
python scripts/build_triplet_manifest.py

# 4. Score every triplet (requires relsim + GPU)
python scripts/eval_triplet.py

# Optional: archive images, compile the validation record, pull qualitative cases,
# compute final statistics (all of these are GPU-free)
python scripts/archive_triplet_images.py
python scripts/compile_validation_record.py
python scripts/extract_qualitative_cases.py
python scripts/compute_final_statistics.py

# 5. Inter-annotator agreement check (GPU-free)
python scripts/build_agreement_check.py
# -> send review/galleries/agreement_check_blind.html to a second annotator,
#    save their exported CSV as labels/agreement_check_friend.csv
python scripts/score_agreement_check.py
```

## Known Limitations

- **Small-scale diagnostic study.** Some cells (notably compositional aligned, n=22) have wide bootstrap confidence intervals; results should be read as diagnostic evidence, not a population-level benchmark claim.
- **Single primary annotator.** All 175 final triplets' codebook-review and retrieval-review accept/reject decisions were made by one person following the written codebook. A second annotator independently blind-labeled a 27-triplet stratified sample as a reproducibility check (see "Inter-Annotator Agreement Check" above, 92.3% appearance / 90.5% relation agreement) — this supports that the judgments are not idiosyncratic, but it is a sample-based check, not full double-annotation of all 175 triplets.
- **Link rot.** A meaningful fraction of source image URLs (scraped from the open web, of varying age) are no longer reachable; `review/archive/` preserves local copies of every image used in the final 175 triplets specifically to guard against this.
- **Spatial containment** was scoped as an optional third relation family in the original design and was not pursued, since both required families (temporal transformation, compositional formation) already reached the target triplet counts needed to answer RQ1–RQ3.

## References

- Nguyen et al. "Relational Visual Similarity." arXiv:2512.07833. https://arxiv.org/abs/2512.07833
- Official RelSim repository: https://github.com/thaoshibe/relsim
- Official RelSim LoRA model card: https://huggingface.co/thaoshibe/relsim-qwenvl25-lora
