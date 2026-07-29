# Annotation Codebook: Relation Family Definitions

This document is the annotation codebook required as a deliverable in Section 6 and Section 15 of `relsim_project_proposal_revised.md`. It defines, for each relation family used in this diagnostic evaluation, a one-sentence definition, inclusion criteria, exclusion criteria, and worked examples (both clear positive instances and boundary cases that were considered but ultimately rejected). Its purpose is to make the human judgment behind triplet construction and validation explicit and reproducible, rather than left to intuition that may vary across annotation sessions or between annotators.

**Data provenance.** All example images below are drawn from the official **test split** of the anonymous-captions-114k dataset released alongside Nguyen et al., "Relational Visual Similarity" (arXiv:2512.07833) — 14,881 rows, distinct from the 100,000-row training split. Candidates were first narrowed using keyword search over captions, then adjudicated by direct visual inspection of each image against the criteria below; the full labeling record is in `review/confirmed_candidates.csv`.

**A note on method.** Captions in this dataset are machine-generated and may hallucinate or use language loosely (e.g., "transform," "progress," and "stages" are frequently used even when an image depicts only a single static state). Caption keywords were used exclusively to retrieve candidates; family membership was determined solely by inspecting the image itself. Several of the boundary examples below exist precisely because a caption's wording suggested a match that the image did not support.

---

## 1. Temporal Transformation

### Definition

An image expresses temporal transformation when it visibly presents an ordered change in the state of the same object, process, or system. The image itself — not the caption — must show multiple states, or a clear before/after structure.

### Inclusion Criteria

An image qualifies only if all of the following hold:

- The image shows two or more distinct states of the same subject, or an unambiguous before/after structure (multi-panel layouts, timeline arrangements, and sequential composites all qualify);
- The change is the central content of the image, not an incidental background detail;
- The states shown belong to a **single, identifiable** object, process, or system — not an assortment of unrelated objects.

### Exclusion Criteria

An image is rejected if it exhibits any of the following:

- A collection of unrelated objects with no temporal ordering between them;
- Multiple poses or camera angles without an underlying state change (e.g., photographs of the same person from different angles do not constitute "change");
- A single instantaneous action captured in one frame, rather than a process;
- **The caption uses words such as "transform," "progress," or "stages," but the image itself shows only a single, final state, with no visible process or intermediate stage.** This is the most common source of false positives from keyword-based retrieval and warrants particular care during review;
- A staged or symbolic scene used to represent an abstract concept, where the image itself does not document a real state change.

### Format Note

Temporal-transformation images disproportionately rely on a small set of recurring visual formats (multi-panel grids, moon-phase diagrams, life-cycle infographics arranged in a circle or row). Repeated instances of the same format should not each be counted as separate positive examples; appearance diversity should be prioritized so that models cannot succeed merely by recognizing a familiar layout rather than reasoning about change over time. Layout type should be recorded as metadata for later use in error analysis (Section 11.5 / Section 5.1 of the proposal).

### Positive Example 1

- **image_hash**: `f37aebc58e6f499c7b3bdf740e730ca1`
- **caption**: "The life cycle of a {Insect}, showcasing its development from a {larva} through metamorphosis to a fully formed {adult}."
- **url**: https://us.123rf.com/450wm/mathisa/mathisa1606/mathisa160600092/60898309-isolated-five-bar-swordtail-butterfly-life-cycle-antiphates-pompilius-on-twig-with-clipping-path.jpg
- **Rationale**: A butterfly life-cycle infographic explicitly depicting the larval, pupal, and adult stages of a single organism. The state progression is unambiguous, making this a canonical instance of temporal transformation.

### Positive Example 2

- **image_hash**: `ebb0a441f27c21308e90b6f3f9ab0d3f`
- **caption**: "The transformation of {Ingredient} into {Product} shown through stages: {Raw Material}, {Processed Form}, {Finished Item}"
- **url**: http://1tb.favim.com/preview/7/763/7632/76327/7632706.jpg
- **Rationale**: A food/ingredient processing sequence (raw material → intermediate form → finished product). The domain and appearance differ substantially from Positive Example 1, which is useful for pairing the two into conflict/aligned triplets while preserving visual diversity.

### Boundary Example 1

- **image_hash**: `f16b49b38517684a39799a2881b3b3a9`
- **caption**: "Visual representation of {Insect} transitioning from {Pupa} to {Adult} during metamorphosis."
- **url**: https://imgc.artprintimages.com/img/print/paul-harcourt-davies-common-swallowtail-butterfly_u-l-pzflw30.jpg
- **Rationale for rejection**: The image shows a butterfly that has just emerged, with its now-empty chrysalis visible below it. While the empty chrysalis implies that a change has occurred, the image does not actually depict the pupa or larva itself — it captures a single terminal state ("the butterfly has emerged"), not multiple visible stages. This fails the inclusion requirement of showing ≥2 states and instead falls under the exclusion criterion for captions that claim a transformation the image does not visibly support. Paired with Positive Example 1 (same general subject — insect metamorphosis), this pair illustrates the distinction sharply: one image documents multiple developmental stages directly; the other captures only the aftermath of a single completed change.

### Boundary Example 2

- **image_hash**: `e98f0bf7516edfd67c4645687bf394b9`
- **caption**: "Creative use of {Tiny Objects} to illustrate {Concepts} like progress, teamwork, and challenges on a {Background}."
- **url**: https://img.freepik.com/free-photo/miniature-shopping-cart-trolley-top-stack-used-gold-coins-white_105035-355.jpg
- **Rationale for rejection**: The image's focal subject is a miniature shopping cart resting on a single coin; the "growing" pile of coins implied by the caption is a blurred background element, not a depicted sequence of discrete accumulation stages. The sense of growth is suggested entirely through depth-of-field composition rather than documented as an actual state change, placing this squarely under the "staged/symbolic scene" exclusion criterion.

### Candidate Retrieval Keywords

Used only to narrow the candidate pool during retrieval; a keyword match is not evidence of category membership on its own.

`transform`, `stage(s)`, `decay`, `rot(ten)`, `ripen`, `melt`, `burn(ing)`, `grow(th/ing)`, `aging/aged`, `progress`, `life cycle`, `metamorphosis`, `evolve`, `wither`, `bloom`, `weather(ing)`, `rust(ing)`, `construction`, `destroy`, `damaged`, `crumble`, `fade(d/ing)`, `dissolve`, `before/after`

---

## 2. Compositional Formation

### Definition

Multiple visible parts, objects, or materials are deliberately arranged so that together they form a recognizable larger whole, shape, symbol, or figure.

### Inclusion Criteria

An image qualifies only if all of the following hold:

- Both the individual parts and the larger whole they form are clearly identifiable in the image;
- The part-to-whole formation is the central content of the image, not an incidental background detail;
- The formation can be described in one sentence naming both the parts and the whole (e.g., "coffee beans arranged into a heart," "fruit pieces arranged into an animal figure").

**Diagnostic question**: Can you count both "several distinct parts" and "one resulting whole" in the image? If the image shows a single continuous object that has been shaped or molded (rather than discrete parts assembled together), it does not qualify.

### Exclusion Criteria

An image is rejected if it exhibits any of the following:

- Objects casually placed together with no resulting recognizable whole;
- Double exposure or digital compositing effects, rather than an actual physical arrangement;
- Two objects fused into a single hybrid creature or object, rather than a structure in which the constituent parts remain individually recognizable while also forming a whole;
- Surface decoration or printed patterns, rather than an arrangement of the object itself;
- One object simply placed inside another — this falls under spatial containment, not composition;
- A symbolic or emblematic depiction of a single object, rather than multiple countable parts forming a whole.

### Positive Example 1

- **image_hash**: `df567ccf0076cfe15dc758ce5179fc77`
- **caption**: "Creative use of {Objects} to form a {Shape}."
- **url**: https://img.freepik.com/free-photo/coffee-grains-heart-form_23-2147896434.jpg
- **Rationale**: A large number of individually countable coffee beans arranged into a heart shape. Both the parts and the resulting whole are clearly visible, making this a canonical instance of compositional formation.

### Positive Example 2

- **image_hash**: `f9575588fb765aac970bc1766efd47f6`
- **caption**: "Artistic arrangements of {Fruit} and {Vegetables} shaped into the forms of various {Characters}."
- **url**: https://i.pinimg.com/736x/44/d2/bd/44d2bd716582c8f399f6a0a51bce66d4.jpg
- **Rationale**: Fruit and vegetable pieces arranged into a figurative character, as opposed to the geometric heart shape of Positive Example 1. The visible difference between an abstract-shape formation and a figurative-character formation gives useful appearance diversity for pairing.

### Boundary Example 1

- **image_hash**: `ebee947c663d7c1e66065c1dc8e38f6c`
- **caption**: "A circular design showcasing alternating segments of {Color} arranged in a {Theme/Pattern}."
- **url**: https://bagcraft.uk/wp-content/uploads/2018/02/soake_rainbow_bcspprain_pagoda1.jpg
- **Rationale for rejection**: The image is most likely a rainbow-colored parasol/umbrella; the alternating color segments are a surface pattern printed or dyed onto a single object, not discrete parts assembled into a new whole. This falls under the "surface decoration" exclusion criterion.

### Boundary Example 2

- **image_hash**: `ff03babbb0d4908dc16cb99716d5608e`
- **caption**: "Visual representation of {Symbol} for embodying {Concept} or {Process}, using {Object} in a creative way."
- **url**: https://us.123rf.com/450wm/dogfella/dogfella1509/dogfella150900100/45058834-wei%C3%9F-gl%C3%BChbirne-au%C3%9Ferhalb-der-zeichnung-box-gl%C3%BChend-denken-au%C3%9Ferhalb-der-box-oder-anderes-konzept-zu-sein.jpg
- **Rationale for rejection**: A "thinking outside the box" conceptual image centered on a single light bulb. The image conveys a symbolic idea through one object, not through multiple countable parts assembled into a new whole. This falls under the "symbolic depiction of a single object" exclusion criterion.

### Candidate Retrieval Keywords

`form(s/ed/ing) a/an/the`, `arrange(d/ment)`, `shaped like`, `spell(s/ing)`, `made of/from`, `composed of`, `assembl(e/ed/y)`, `mosaic`, `collage`, `pattern`, `letter(s)`, `symbol`, `together form/create/make`

---

## 3. Spatial Containment (Optional Extension — Not Currently Expanded)

Per Section 5.3 of the proposal, this family is an optional extension to be considered only after the core experiment (temporal transformation + compositional formation) is complete. Eleven keyword-matched candidates have been identified but not yet labeled; this section is a placeholder and does not yet include positive or boundary examples.

### Definition (placeholder, from the proposal)

A salient entity is visibly located inside, enclosed by, trapped within, or encased by another bounded object or space.

### Exclusion Criteria (placeholder)

- On top of, beside, behind, surrounded by (without a clearly defined boundary), or supported by;
- Metaphorical or figurative uses of "containment" with no actual bounding object depicted.

---

## 4. Known Data-Quality Issues

These issues were encountered during annotation and should be noted when writing up methodology or discussing limitations:

- A meaningful fraction of `url_link` values are no longer reachable (link rot from web-scraped sources of varying age). These were labeled `discard`; this does not affect the codebook definitions themselves.
- Captions frequently contain unfilled template placeholders (e.g., `{Object}`, `{Container}`). Captions were used only for candidate retrieval; family membership was determined from the image content, not the caption text.
- Temporal-transformation candidates show a tendency to cluster around a small number of recurring visual formats (multi-panel grids, moon-phase diagrams, life-cycle infographics). Annotation deliberately avoided counting multiple near-duplicate or same-format instances as separate positive examples, to preserve appearance diversity for later triplet construction.
