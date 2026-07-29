# Revised Project Proposal

## Where Does RelSim Help?  
### A Controlled Diagnostic Evaluation Across Relation Families and Relation–Appearance Conditions

*Based on Nguyen et al., “Relational Visual Similarity” (CVPR 2026; arXiv:2512.07833).*

---

## 1. Motivation

Most widely used visual-similarity models, such as CLIP and DINO, are good at recognizing **attribute or perceptual similarity**: whether two images contain similar objects, colors, shapes, textures, or layouts. RelSim introduces a complementary notion, **relational similarity**: two images may be similar because the relations or functions among their visual elements correspond, even when the images look very different.

For example, a sequence showing a match burning down and a sequence showing fruit decaying may share the abstract relation **“irreversible change over time”**, although their visible objects and colors differ. RelSim is trained to place such images closer together in its representation space.

The original RelSim paper evaluates the model mainly through aggregate retrieval results. It does not provide a controlled breakdown showing:

1. whether RelSim’s advantage differs across relation families; and
2. whether its advantage becomes larger specifically when **relational cues and appearance cues conflict**.

This project therefore conducts a **small, controlled diagnostic evaluation**. It does not attempt to create a complete taxonomy of the full RelSim dataset. Instead, it selects a small number of clearly defined relation families and constructs human-validated triplets that isolate the effect of relational versus appearance information.

### 中文说明

本项目不再试图把整个数据集强行分成若干互斥类别。核心目标变成：

> 挑选少数定义清楚的关系，构造可控测试题，观察 RelSim 在什么情况下比 CLIP/DINO 更有优势。

---

## 2. Main Design Principle

The central design separates two variables that were mixed together in the original proposal:

1. **Relation family**: what type of relation the image expresses;
2. **Relation–appearance condition**: whether appearance cues support or conflict with the relational answer.

The experiment therefore uses a small factorial design:

| Relation family | Conflict condition | Aligned condition |
|---|---|---|
| Temporal transformation | Relation points to the positive, while appearance points to the negative | Relation and appearance both point to the positive |
| Second relation family | Relation points to the positive, while appearance points to the negative | Relation and appearance both point to the positive |

This separation allows the project to distinguish two questions:

- Does RelSim behave differently across relation families?
- Within the same relation family, does RelSim gain more advantage when appearance becomes misleading?

### Condition definitions

#### Conflict condition

For a triplet `(anchor, positive, negative)`:

- the **positive** shares the target relation with the anchor but looks different;
- the **negative** looks more similar to the anchor but expresses a different relation.

Required human judgments:

- relational similarity: `positive > negative`;
- appearance similarity: `negative > positive`.

#### Aligned condition

- the **positive** shares the target relation and is also more similar in appearance;
- the **negative** differs in both relation and appearance.

Required human judgments:

- relational similarity: `positive > negative`;
- appearance similarity: `positive > negative`.

The aligned condition is mainly a **baseline/control condition**. Because it may be easy for all models, it is not expected to provide the strongest result by itself.

---

## 3. Research Questions

### RQ1 — Relation-family variation

Under the same relation–appearance conflict condition, does RelSim’s advantage over CLIP and DINO differ across relation families?

This question requires at least two relation families.

### RQ2 — Conflict sensitivity

Within the same relation family, is RelSim’s advantage larger in the conflict condition than in the aligned condition?

This is the most direct test of RelSim’s intended strength: prioritizing relational structure when appearance is misleading.

### RQ3 — Attribute-oriented performance

On an **attribute-priority control set**, how does RelSim compare with CLIP and DINO when the correct answer is determined mainly by visible appearance?

This question is descriptive. A weaker RelSim result would show that RelSim is less aligned with these attribute-oriented judgments, but it would not by itself prove that fine-tuning caused an ability to deteriorate.

### Optional RQ3b — LoRA effect

If a technically comparable baseline can be implemented, how does the RelSim model compare with the same Qwen2.5-VL-7B-Instruct backbone without the RelSim LoRA adapter?

This optional comparison is the cleanest way to discuss what changed after RelSim fine-tuning, because the backbone architecture is held constant.

However, it will only be included if the base model can be scored through a genuinely comparable pipeline using the same prompt, pooling, projection, and similarity calculation. If the official implementation does not support a clean no-LoRA comparison, this analysis will be reported as infeasible rather than approximated with an unfair setup.

---

## 4. Hypotheses

### H1 — Relation-family heterogeneity

RelSim’s advantage over CLIP and DINO will not be identical across all tested relation families.

This is a directional claim only at a broad level; the project does not assume in advance which second relation family must produce the larger gap.

### H2 — Conflict sensitivity

Within a relation family, the RelSim–baseline accuracy gap will be larger in the **conflict** condition than in the **aligned** condition.

### H3 — Attribute-oriented performance

RelSim may or may not remain competitive with CLIP and DINO on the attribute-priority control. This is treated as an open empirical question.

If the optional base-Qwen comparison is feasible, the difference between base Qwen and RelSim will be used to discuss the effect of the RelSim adaptation more directly.

---

## 5. Relation Families

### 5.1 Core family: Temporal transformation

#### Operational definition

An image expresses temporal transformation when it visibly presents an ordered change in the state of the same object, process, or system.

Examples include:

- an object progressing from intact to damaged;
- fruit progressing from unripe to ripe or rotten;
- a plant life cycle;
- a material being created, consumed, melted, burned, or transformed through visible stages.

#### Inclusion criteria

- multiple visible states or a clear before/after structure;
- a meaningful order among states;
- the transformation is central to the image;
- the relation can be recognized from the image, not only from the caption.

#### Exclusion criteria

- a collection of different objects with no time order;
- multiple poses that do not show state change;
- a single instantaneous action;
- captions that mention transformation when the image does not visibly show it.

#### Format control

Temporal images often use multi-panel, before/after, or left-to-right layouts. Models might use this visual format as a shortcut instead of understanding change.

Therefore:

- multi-panel and before/after formats will be balanced across conditions where possible;
- hard negatives should often preserve a similar layout but remove the temporal relation;
- layout type will be recorded as metadata and checked during error analysis.

---

### 5.2 Preferred second family: Compositional formation

#### Operational definition

Multiple visible parts, objects, or materials are deliberately arranged so that together they form a recognizable larger whole, shape, symbol, or figure.

Examples include:

- fruit pieces forming an animal;
- people forming a letter or symbol;
- small objects forming a face, map, or heart;
- visible components assembled into a larger recognizable structure.

#### Inclusion criteria

- both the component parts and the larger whole are visually identifiable;
- the part-to-whole formation is the image’s central relational logic;
- the positive pair shares the abstract pattern “parts form a whole,” even when the parts and whole differ.

#### Exclusion criteria

- ordinary object co-occurrence;
- double exposure;
- two objects fused into a hybrid;
- surface decoration;
- one object simply located inside another.

#### Feasibility condition

Compositional formation will be used only if the feasibility scan finds enough clear examples in the authors’ test split.

Before committing to this family, the project will count usable candidates in the existing 400-caption sample and then verify candidate images. If the data are insufficient, the second family will be replaced by another relation that:

1. is clearly distinct from temporal transformation;
2. can be defined with reliable inclusion and exclusion criteria; and
3. has enough usable test-split examples.

The project will not force a relation family merely to preserve a preferred name.

---

### 5.3 Optional third family: Spatial containment

Spatial containment is an extension only, not a requirement for a complete submission.

#### Operational definition

A salient entity is visibly located inside, enclosed by, trapped within, or encased by another bounded object or space.

#### Exclusion criteria

- on top of;
- beside;
- behind;
- surrounded by;
- supported by;
- metaphorical containment.

This family will be added only if enough unambiguous examples are available after the core experiment is complete.

---

## 6. Step 0 — Feasibility Scan and Codebook Development

The previous plan to produce a complete relation taxonomy is removed.

Step 0 now has two limited purposes:

1. determine whether the selected relation families have enough usable examples;
2. produce a short annotation codebook.

For each relation family, the codebook will contain:

- a one-sentence definition;
- inclusion criteria;
- exclusion criteria;
- two clear positive examples;
- two boundary cases or negative examples;
- common caption keywords used only for candidate retrieval.

The existing sample of approximately 400 captions is sufficient for this feasibility scan. Captions that do not clearly fit a target family can simply be ignored.

No claim will be made that the scan is a complete or representative taxonomy of the full dataset.

---

## 7. Data Source and Candidate Mining

### 7.1 Data split

The final evaluation images will come from the authors’ released **test split**, not the training split.

The project will:

- record image URLs and identifiers;
- remove exact and obvious near-duplicates;
- avoid repeatedly using the same image across many triplets;
- save local copies or hashes where permitted so the benchmark is reproducible.

### 7.2 Captions are candidate-search tools, not ground truth

The released anonymous captions were generated by an anonymous-caption model, and the official repository notes that the model may hallucinate or produce incorrect captions.

Therefore:

> captions will be used to retrieve candidate images, but final labels will be decided from the images themselves.

Candidate generation may use:

- caption keywords;
- sentence-transformer caption embeddings;
- CLIP image similarity;
- DINO image similarity.

These tools only reduce a large search space to a small candidate set. They do not determine the final positive or negative.

### 7.3 Avoiding a CLIP-targeted benchmark

The project will not directly select the nearest CLIP image as the negative. Doing so would create a test set intentionally optimized to make CLIP fail.

Instead:

1. CLIP, DINO, and caption retrieval each produce candidate pools;
2. candidates are inspected without using final model performance;
3. the final triplet is chosen using the written codebook;
4. the complete benchmark is frozen before RelSim/CLIP/DINO results are examined.

---

## 8. Human Validation Gate

Every final triplet will receive independent human validation. Validation is not limited to a random subset.

For every triplet, validators answer two forced-choice questions:

1. **Relation question:** Which candidate shares the more similar underlying relation or logic with the anchor?
2. **Appearance question:** Which candidate looks more similar to the anchor in objects, colors, shapes, textures, style, and layout?

### Retention rules

#### Conflict triplet

Retain only if validators judge:

- relation: `positive > negative`;
- appearance: `negative > positive`.

#### Aligned triplet

Retain only if validators judge:

- relation: `positive > negative`;
- appearance: `positive > negative`.

#### Attribute-priority control

Retain only if validators clearly judge the designated positive as more similar in visible appearance.

At least one independent peer will validate every item. A second validator will be used for every item if feasible; otherwise, the second validator will review disagreements and a substantial subset.

Agreement and disagreement counts will be recorded. Ambiguous triplets will be removed rather than forced into the benchmark.

---

## 9. Attribute-Priority Control

The original phrase “pure appearance” is replaced by **attribute-priority control**, because real images may always support some relational interpretation.

Each control triplet is designed so that human judgment is primarily based on:

- object identity;
- color;
- shape;
- texture;
- visual style;
- layout.

This control answers:

> Does RelSim rank images in a way that remains competitive with attribute-oriented similarity models on this curated set?

Without the optional base-Qwen comparison, the result will not be described as proof that fine-tuning caused “ability degradation.”

---

## 10. Models

### Required models

1. **RelSim**  
   Qwen2.5-VL-7B-Instruct with the released RelSim LoRA checkpoint and official similarity interface.

2. **CLIP**  
   Image embeddings with cosine similarity.

3. **DINO**  
   Image embeddings with cosine similarity.

### Optional fourth model

4. **Base Qwen2.5-VL-7B-Instruct without the RelSim LoRA**

This model is included only if a clean, comparable scoring pipeline can be implemented. The implementation must keep the scoring method as constant as possible.

The feasibility of this ablation will be tested early. If it cannot be implemented cleanly within a short fixed time budget, it will be documented as future work and will not delay the required experiment.

No model will be trained from scratch. The project is inference-only.

---

## 11. Evaluation Metrics

### 11.1 Primary metric: Triplet accuracy

A model answers correctly when:

`sim(anchor, positive) > sim(anchor, negative)`

Accuracy is reported separately for:

- each model;
- each relation family;
- conflict versus aligned conditions;
- the attribute-priority control.

### 11.2 Paired model gaps

Because all models answer the same triplets, model differences will be analyzed as paired comparisons.

The main reported quantities are:

- `RelSim accuracy − CLIP accuracy`;
- `RelSim accuracy − DINO accuracy`;
- if feasible, `RelSim accuracy − base-Qwen accuracy`.

The key condition effect is:

`gap in conflict − gap in aligned`

The key family effect is:

`gap for family 1 − gap for family 2`, evaluated under the same condition.

### 11.3 Uncertainty

Triplet-level bootstrap will be used to report 95% confidence intervals for:

- each accuracy;
- each paired model gap;
- the conflict-versus-aligned difference.

With only 20–25 items per cell, confidence intervals may be wide. The project will therefore be described as a **small diagnostic study**, and statistical non-significance will not be treated as proof that models are equivalent.

### 11.4 Similarity margin

The margin is:

`sim(anchor, positive) − sim(anchor, negative)`

Margins will be used only for within-model analysis. Raw margins will not be compared directly across models because their similarity-score scales may differ.

### 11.5 Qualitative error analysis

The report will include examples where:

- RelSim succeeds and CLIP/DINO fail;
- all models fail;
- a baseline succeeds and RelSim fails;
- performance appears driven by layout or another shortcut.

---

## 12. Target Dataset Size and Scope

### Minimum complete submission

- Temporal conflict: 20–25 validated triplets;
- Temporal aligned: 20–25 validated triplets;
- Attribute-priority control: 20–25 validated triplets;
- required models: RelSim, CLIP, DINO;
- optional base-Qwen ablation if technically clean.

This version can answer the conflict-sensitivity question and provide an attribute-oriented comparison.

### Complete main story

Add:

- second relation-family conflict: 20–25 triplets;
- second relation-family aligned: 20–25 triplets.

This version can answer both relation-family variation and conflict sensitivity.

### Optional extension

Add spatial containment only after the complete main story is finished.

---

## 13. Expected Outcomes and Interpretation

| Possible outcome | Interpretation |
|---|---|
| RelSim’s gap is larger in conflict than aligned | Evidence that RelSim is especially useful when appearance cues are misleading |
| RelSim has a similar gap in conflict and aligned | RelSim’s advantage may not specifically depend on relation–appearance conflict |
| RelSim performs differently across relation families | Its relational advantage is heterogeneous rather than uniform |
| All models score near ceiling in aligned conditions | Aligned tasks mainly function as an easy appearance-supported baseline |
| RelSim is weaker on the attribute-priority control | RelSim is less aligned with the curated appearance judgments; this alone does not prove causal degradation |
| RelSim and base Qwen differ on the same scoring pipeline | Stronger evidence about the effect of the RelSim adaptation |
| RelSim fails on layout-matched temporal cases | Possible evidence that the model relied on superficial temporal formats rather than the intended relation |

The project is informative even if RelSim does not win. The contribution is a controlled profile of where the model succeeds, where it fails, and which cues affect its behavior.

---

## 14. Threats to Validity

1. **Subjective relation labels**  
   Addressed through an explicit codebook and full human validation.

2. **Small curated benchmark**  
   Results are diagnostic and exploratory, not a population-level benchmark claim.

3. **Candidate-selection bias**  
   Reduced by using multiple retrieval methods, human final selection, and freezing the test set before viewing model results.

4. **Caption errors**  
   Captions are used only for candidate search; images determine the final label.

5. **Temporal-layout shortcuts**  
   Reduced through format balancing and layout-matched negatives.

6. **Ceiling effects in aligned conditions**  
   Aligned conditions are interpreted mainly as controls.

7. **Base-Qwen comparability**  
   The no-LoRA ablation is included only if scoring can be made genuinely comparable.

---

## 15. Deliverables

1. Annotation codebook;
2. final triplet manifest with metadata;
3. human-validation responses and agreement summary;
4. model similarity scores and triplet decisions;
5. results tables with bootstrap confidence intervals;
6. qualitative success and failure cases;
7. reproducible code and README;
8. final seminar report.

---

## 16. References

- Nguyen et al. “Relational Visual Similarity.” arXiv:2512.07833.  
  https://arxiv.org/abs/2512.07833

- Official RelSim repository.  
  https://github.com/thaoshibe/relsim

- Official RelSim LoRA model card.  
  https://huggingface.co/thaoshibe/relsim-qwenvl25-lora
