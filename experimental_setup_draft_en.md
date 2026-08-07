# Experimental Setup — English Draft

> 说明：以下是 Experimental Setup（Section 3）的英文初稿，按 3.1–3.7 组织。方括号 [ ] 内是需要你按实际情况填入或确认的占位内容。数字均取自你的项目文档；正式定稿前请再核对一遍。

---

## 3 Experimental Setup

### 3.1 Relation families and conditions

We evaluate RelSim on two relation families, each chosen so that its defining relation can be verified directly from the image rather than inferred from a caption.

**Temporal transformation.** An image expresses temporal transformation when it visibly presents an ordered change in the state of a single object, process, or system — for example, an object progressing from intact to damaged, fruit ripening or decaying, or a material being burned, melted, or assembled through visible stages. The relation must be recognizable from the image itself, not merely asserted by the caption.

**Compositional formation.** An image expresses compositional formation when multiple visible parts, objects, or materials are deliberately arranged so that together they form a recognizable larger whole, shape, or figure — for example, fruit pieces forming an animal, or people forming a letter. Both the component parts and the emergent whole must be visually identifiable.

Full operational definitions, including inclusion and exclusion criteria and worked positive/boundary examples, are given in the annotation codebook (Appendix [A]).

Within each family, every item is a forced-choice triplet `(anchor, positive, negative)` presented under one of two conditions. In the **conflict** condition, the positive shares the anchor's relation but looks less similar to it, while the negative looks more similar in appearance but does not share the relation; the intended human judgments are relation `positive > negative` and appearance `negative > positive`. In the **aligned** control condition, the positive shares both the relation and the appearance, while the negative differs on both; here relation and appearance point to the same answer. The aligned condition functions as a baseline: because appearance and relation agree, it should be solvable without relational understanding, and near-ceiling performance is an expected and interpretable outcome. A separate, relation-independent **attribute-priority control** set is described in Section 3.6.

### 3.2 Data source

All evaluation images are drawn from the official test split of the `anonymous-captions-114k` dataset released with RelSim, comprising 14,881 rows. Each row pairs a web image with a machine-generated caption describing the relation depicted. Two properties of this data are important for our design.

First, the captions are model-generated and, as the official repository notes, may be inaccurate or hallucinated. We therefore treat captions strictly as a **candidate-retrieval tool, never as ground truth**: a caption may bring an image into consideration, but family membership and every final label are always decided by inspecting the image itself.

Second, because the source images are scraped from the open web, a meaningful fraction of the original URLs are no longer reachable. To guarantee reproducibility, we archive a permanent local copy of every image used in the final triplets, indexed by content hash (Section 3.7).

### 3.3 Benchmark construction

The benchmark was built in four stages, and its construction is described here in full because one detail directly affects how the CLIP baseline should be interpreted (Section 4).

**(1) Codebook review.** Family-specific caption keywords were used to scan the 14,881-row test split, and each retrieved image was labeled `fits`, `boundary_reject`, or `discard` against the written codebook. This stage yielded [47] temporal-transformation and [38] compositional-formation confirmed members. Images whose captions did not match what the image actually showed, or that expressed several equally salient relations, were discarded.

**(2) Retrieval review.** For each confirmed member, candidate negatives and aligned pairs were proposed by nearest-neighbour search in CLIP embedding space over the confirmed pool, and a human accepted or rejected each proposal according to the codebook. CLIP was used only to narrow a large search space to a small candidate set; it never assigned a final label.

**(3) Triplet assembly.** Accepted candidates were combined into triplets. For **conflict** triplets, the negative is the human-accepted, CLIP-retrieved appearance-similar distractor, whereas the positive is assigned by an appearance-blind round-robin over each family's confirmed members (matching on relation only, using no embedding or appearance signal). For **aligned** triplets, the negative is a random unrelated background image.

This procedure introduces a deliberate but consequential asymmetry in the conflict condition: the negative is, by construction, selected to be close to the anchor *in CLIP's own embedding space*, while the positive is selected without any appearance signal. As a result, CLIP's scores on conflict triplets cannot be read as a neutral measure of CLIP's relational ability; we return to this point, and to the independent DINO baseline that is unaffected by it, in Sections 3.5 and 4.

**(4) Model scoring.** Each assembled triplet was scored by all three models (Section 3.5). The manifest was then frozen (`frozen-benchmark-v1`) before model results were examined, so that no triplet could be revised in response to a model's performance.

### 3.4 Human validation

Every final triplet's family-membership and accept/reject decisions were made by a single primary annotator working from the written codebook, and each decision is traceable to its source in a validation record.

To test whether these single-annotator judgments are reproducible rather than idiosyncratic, a second, independent annotator blind-labeled a stratified random sample of **27 of the 175 triplets** (6 temporal-transformation conflict, 5 temporal-transformation aligned, 6 compositional-formation conflict, 5 compositional-formation aligned, 5 attribute-priority control). For each sampled triplet, the second annotator saw only the anchor and the two candidates, relabeled "Candidate A" / "Candidate B" in randomized order — with no captions, no identifiers, no condition or family labels, and no indication of which candidate was originally the positive. Working from the codebook alone, they answered two forced-choice questions per triplet: which candidate shares more of the anchor's underlying *relation*, and which looks more similar in *appearance*. Their answers were then compared against the original decisions.

One triplet was excluded from both dimensions because of a broken anchor image, leaving n=26 for the appearance judgment and n=21 for the relation judgment (the 5 control triplets have no relational ground truth and are excluded from the relation dimension). Agreement was high overall — **92.3% (24/26) on appearance and 90.5% (19/21) on relation** — supporting that triplet construction reflects the written codebook rather than one annotator's private judgment. Per-cell agreement is reported in Table [X]; the single weak cell (temporal-transformation aligned, 60% relation agreement) is examined in Section [5].

**Table [X]. Inter-annotator agreement by relation family and condition.**

| Relation family | Condition | Appearance agreement | Relation agreement |
|---|---|---|---|
| Attribute-priority control | control | 80.0% (4/5) | — |
| Compositional formation | aligned | 100.0% (5/5) | 100.0% (5/5) |
| Compositional formation | conflict | 100.0% (5/5) | 100.0% (5/5) |
| Temporal transformation | aligned | 100.0% (5/5) | 60.0% (3/5) |
| Temporal transformation | conflict | 83.3% (5/6) | 100.0% (6/6) |
| **Overall** | | **92.3% (24/26)** | **90.5% (19/21)** |

### 3.5 Models and implementation

We compare three models, all applied inference-only; no model is trained or fine-tuned in this work.

**RelSim** is the released Qwen2.5-VL-7B-Instruct backbone with the official `thaoshibe/relsim-qwenvl25-lora` adapter, scored through the official `relsim` package and its similarity interface. **CLIP** uses `openai/clip-vit-base-patch32` image embeddings with cosine similarity. **DINO** uses `facebook/dinov2-base` image embeddings with cosine similarity. For every triplet, each model produces `sim(anchor, positive)` and `sim(anchor, negative)` using its own similarity procedure.

CLIP and DINO are both appearance-oriented encoders, but they play different roles here. Because CLIP was used to retrieve conflict negatives (Section 3.3), it is not an unbiased baseline in the conflict condition. DINO, by contrast, took no part in candidate selection at any stage, so its scores are independent of how the benchmark was built. We therefore treat **DINO as the primary, selection-independent baseline** for all substantive comparisons, and report CLIP alongside it with this caveat made explicit.

Key inference details: images were [preprocessed / resized per each model's default image processor]; RelSim embeddings were obtained with [the official prompt template and pooling reported in Appendix A]; all similarity scores are cosine similarities in the respective embedding spaces. [填入其余你实际用到的实现细节：分辨率、pooling、随机种子等。RelSim 的长 prompt template 放 Appendix。]

### 3.6 Metrics

**Primary metric — triplet accuracy.** A model is correct on a triplet when `sim(anchor, positive) > sim(anchor, negative)`. Accuracy is reported separately for each model, each relation family, each condition, and the attribute-priority control.

**Paired model gaps.** Because all models answer the same triplets, we analyze model differences as paired quantities: `RelSim − CLIP` and `RelSim − DINO` accuracy gaps per cell. The key condition effect is `gap in conflict − gap in aligned` (RQ2), and the key family effect is `gap for family 1 − gap for family 2` under the same condition (RQ1). Following Section 3.5, the DINO-based gaps are the primary basis for these comparisons.

**Uncertainty.** We report 95% confidence intervals from triplet-level bootstrap resampling for each accuracy and each paired gap. With 20–35 items per cell, intervals are wide; the study is accordingly framed as a small-scale diagnostic, and statistical non-significance is not treated as evidence of model equivalence.

**Similarity margin.** The margin `sim(anchor, positive) − sim(anchor, negative)` is used only for within-model analysis; raw margins are not compared across models, whose similarity scales differ.

**Attribute-priority control.** A separate control set of [30] triplets is constructed so that the correct answer is determined by visible appearance alone (object identity, color, shape, texture, style, layout), independent of either relation family. It asks whether RelSim's relational tuning has left it competitive with appearance-based models on straightforwardly appearance-driven judgments (RQ3).

### 3.7 Final dataset

The frozen benchmark contains 175 triplets, of which 169 were successfully scored by all three models; the remaining [6] could not be scored because [填原因，例如 one or more member images became unreachable at scoring time]. The scored triplets are distributed as follows.

**Table [Y]. Scored triplets per cell.**

| Relation family | Condition | n |
|---|---|---|
| Temporal transformation | conflict | 35 |
| Temporal transformation | aligned | 28 |
| Compositional formation | conflict | 54 |
| Compositional formation | aligned | 22 |
| Attribute-priority control | control | 30 |
| **Total** | | **169** |

Every image referenced in the final manifest is archived locally by content hash to protect the benchmark against link rot, and the full manifest, per-triplet model scores, and validation record are released with the code.
