# Project Proposal
## Is RelSim's Relational Advantage Uniform Across Relation Types? A Diagnostic Evaluation

*Based on: Nguyen et al., "Relational Visual Similarity" (CVPR 2026, arXiv:2512.07833)*

---

## 1. Motivation

Visual similarity is one of the most fundamental visual capabilities, but the widely used similarity metrics today (LPIPS, CLIP, DINO) capture only **attribute / perceptual similarity** — whether two images *look* alike. The RelSim paper introduces a complementary notion, **relational similarity**: two images are similar when their internal relational structure corresponds, even if their surface appearance is completely different (e.g., a match burning down, a banana rotting, and a leaf decaying all share the relation *"irreversible transformation over time"*). The authors fine-tune a Vision-Language Model (Qwen2.5-VL-7B) to capture this and show it outperforms traditional metrics overall.

However, the paper reports a **single, aggregate** notion of performance, and two observations suggest its advantage may not be uniform. First, the authors themselves note in their limitations that relational similarity is **subjective** (defined by annotators) and that a single anonymous caption cannot represent the full space of possible relations. Second, in their **human A/B testing**, RelSim and CLIP-I appear roughly comparable, even though RelSim leads under other evaluation protocols. This raises a question the paper does not address: **is RelSim's advantage spread evenly across all kinds of relations, or is it concentrated in a specific subset** — namely, relations where appearance gives no useful signal? And relatedly, **did specializing for relational similarity come at the cost of the model's original attribute-similarity ability?**

This project does not try to find a brand-new relation type the authors "missed" (their LAION-sourced data is broad and that would be neither feasible nor the point). Instead, it **takes relation types that already exist in the data, separates them, and diagnoses where RelSim's advantage is real and where it disappears.**

> **中文翻译与解释：**
> 这一段是"动机/背景"，目的是让老师在 30 秒内明白：(1) 这篇论文在做什么，(2) 它留了什么没回答，(3) 你要补上哪一块。
>
> 逻辑链是这样的：视觉相似度很重要 → 但传统度量（CLIP/DINO/LPIPS）只能抓"表面像不像"（属性相似）→ RelSim 论文提出了"关系相似"这个新概念，并微调了一个 VLM 来实现它，整体上打败了传统度量 → **但是**，论文只报告了一个"笼统的、整体的"表现，而有两个线索暗示它的优势可能并不均匀：① 作者自己在 limitation 里承认关系相似度很主观、一条 anonymous caption 代表不了所有关系；② 在论文的人工 A/B 测试里，RelSim 和 CLIP-I 其实差不多。
>
> 于是你提出了论文没回答的问题：**RelSim 的优势到底是均匀分布在所有关系上，还是只集中在"外观帮不上忙"的那类关系上？以及，它为了学会关系相似，有没有牺牲掉原本的属性相似能力？**
>
> 最后一句很关键，是你前几轮纠结的总结：你**不是**去找一种"作者没测过的新关系"（这既不可行也不是重点），而是**把数据里已有的关系类型切开，诊断 RelSim 的优势在哪儿是真的、在哪儿消失了**。这句话直接堵住了老师可能问的"你这关系作者不是测过了吗"。

---

## 2. Hypotheses

**H1 (main).** RelSim's advantage over CLIP/DINO is **not globally uniform**. It is largest for **appearance-independent abstract relations** (where two relationally-matched images look nothing alike, so appearance-based metrics have no signal), and **shrinks substantially** for relations where appearance and relation are naturally correlated (where a metric can "get the right answer" just by looking at surface features).

**H2 (sub-question).** Specializing the model for relational similarity **does not significantly degrade** its attribute-similarity ability relative to CLIP/DINO — *or it does.* We treat this as an open empirical question rather than a directional bet.

> **中文翻译与解释：**
> 这部分是"假设"。注意 H1 和 H2 性质不同。
>
> **H1 是有方向的假设**（你赌一个具体结果）：RelSim 的优势不是到处都一样大，而是在"外观无关的抽象关系"上最大（因为这种关系下两张图长得完全不像，CLIP 这种靠外观的度量就抓瞎了），在"外观和关系本来就高度绑定"的关系上则明显缩小（因为这种关系下，模型光看表面就能蒙对，RelSim 和 CLIP 拉不开差距）。
>
> **H2 是开放性问题**（你不预设方向）：RelSim 为了学关系相似，到底有没有损失原本"看表面像不像"的能力？这里我**故意写成开放的**——因为无论结果是"退化了"还是"没退化"，都是有意义的发现，你不需要押一个方向。在 meeting 上这样讲会显得你很客观、想得周全，而不是先入为主。

---

## 3. Research Questions

- **RQ1.** Is RelSim's advantage over traditional attribute-based metrics (CLIP, DINO) **uniform across relation types**, or **concentrated** in appearance-independent abstract relations?
- **RQ2.** Does RelSim **retain attribute-similarity ability** comparable to CLIP/DINO, or does its relational specialization come at a measurable cost?
- **RQ3 (descriptive).** Across the relation types tested, **which show the largest and smallest RelSim-vs-baseline gap** — i.e., can we produce a "profile" of where RelSim's relational understanding is strong vs. weak?

> **中文翻译与解释：**
> 研究问题就是把假设翻译成"可以被实验回答的问句"。RQ1 对应 H1（优势均匀还是集中），RQ2 对应 H2（属性能力有没有退化），RQ3 是一个"描述性"的问题——不赌结果，只是把"RelSim 在哪类关系强、哪类弱"画成一张图谱。RQ3 很重要，因为它保证了**无论数字往哪倒，你都有东西可写**（你产出的是一张"能力分布图"，而不是一个简单的"赢/输"结论）。

---

## 4. Selected Relation Types

I will evaluate **three relation types**, ordered by how much I expect appearance to *help* a traditional metric (and therefore, inversely, how large I expect RelSim's advantage to be):

| Relation type | Example | Appearance ↔ relation coupling | Expected RelSim advantage |
|---|---|---|---|
| **Temporal evolution** (irreversible change over time) | match burning down ≈ banana rotting ≈ leaf decaying | **Low** (matched images look unalike) | **Large** |
| **Structural nesting** (abstract part-whole / layered containment) | onion cross-section ≈ geological strata ≈ nested dolls | Medium | Medium |
| **Spatial containment / support** (X inside/on Y) | water in a cup ≈ soup in a bowl | **High** (matched images also look alike) | **Small** |

In addition, I will build one **pure-appearance triplet set** (no relational component at all) to answer RQ2 — testing only whether the model still recognizes surface similarity.

> **中文翻译与解释：**
> 这是你方案的核心设计——**三类关系按"外观能帮多大忙"从低到高排列**，对应你预期 RelSim 的优势从大到小。
>
> - **时间演变类**：两张关系相似的图（燃尽的火柴 vs 腐烂的香蕉）长得完全不像，所以 CLIP 靠外观抓瞎 → RelSim 该大赢。这是论文的招牌例子。
> - **结构嵌套类**（洋葱剖面 vs 地质分层 vs 套娃）：抽象的"层级/部分-整体"关系，外观帮一点忙但不多 → RelSim 优势中等。
> - **空间容器/支撑类**（杯里的水 vs 碗里的汤）：关系相似的图往往外观也相似，CLIP 光看表面就能蒙对 → RelSim 优势小。
>
> **三类排成一个梯度**，这样你的发现不是"一个孤立的对比"，而是"一条趋势线"（优势从大→中→小），说服力强得多，也不容易被质疑成"你是不是刚好挑了极端的两类"。
>
> 最后那一组**纯外观三元组**是专门用来回答 RQ2 的（测属性能力有没有退化），它里面**完全没有关系成分**，只测"模型还认不认得出表面像不像"。这是一个独立的小对照实验。

---

## 5. Methodology

### Step 0 — Relation-type mapping of the dataset (also a deliverable)

Sample ~300–500 anonymous captions from the released `anonymous-captions-114k` dataset, manually group them into coarse relation categories, and report the rough distribution. This (a) confirms which of my three target types have enough examples, and (b) is itself a small contribution — a "relation-type map" of an otherwise unstructured dataset.

### Step 1 — Triplet construction (semi-automatic)

Each test item is a **triplet** `(anchor, positive, negative)`:
- **anchor** — a reference image
- **positive** — relationally similar but **visually different** from the anchor
- **negative** — visually similar but **relationally different** from the anchor

Construction is **semi-automatic** (algorithm narrows candidates, I make the final selection):
1. **Find positives.** Encode all anonymous captions with a small text-embedding model (e.g., sentence-transformers, runs on CPU). For a given anchor, captions that are *semantically close* point to candidate relationally-similar images. I manually confirm the final positive.
2. **Find negatives.** Use **CLIP** to find images *visually closest* to the anchor; among those, I pick one whose relation (caption) is clearly *different*. This is exactly the case where CLIP is expected to be "fooled."
3. All images come from the **authors' released dataset** (image URLs provided); the 14k random LAION images they released can serve as extra distractors.

Target size: **~25–30 triplets per relation type × 3 types ≈ 75–90 relational triplets**, plus **~20–25 pure-appearance triplets** for RQ2. Total ≈ **95–115 triplets**.

### Step 2 — Pure-appearance sub-experiment (for RQ2)

Construct ~20–25 triplets where positive = visually very similar, negative = visually different, with **no relational logic involved**. This isolates attribute-similarity ability. If RelSim scores clearly below CLIP/DINO here, it is direct evidence of a relational-vs-attribute trade-off; if comparable, RelSim retained its attribute ability.

### Models

- **RelSim** — `pip install relsim`, Qwen2.5-VL-7B + LoRA checkpoint (`thaoshibe/relsim-qwenvl25-lora`), run on the school GPU. Scoring two images is ~3 lines of code; per-image embeddings can be precomputed once for efficiency.
- **Baselines** — CLIP and DINO (small, run anywhere): embed each image, use cosine similarity.
- **Helper** — sentence-transformers for caption embedding (Step 1, CPU).

No model is trained or fine-tuned. Everything is inference-only on released checkpoints.

### Evaluation metrics

- **Primary — triplet accuracy:** the fraction of triplets where `sim(anchor, positive) > sim(anchor, negative)`, computed **separately for each model and each relation type**.
- **Key comparison:** the **gap** in triplet accuracy between RelSim and CLIP/DINO, **across relation types**. H1 predicts this gap is large for temporal evolution and small for spatial containment.
- **Secondary — score margin:** average of `sim(anchor, positive) − sim(anchor, negative)`, to see not just *whether* but *how confidently* each model separates the pair.
- **Label validation (rigor):** have 1–2 peers independently verify a random sample of my triplet labels, to check that my relation judgments aren't idiosyncratic. (Directly addresses the subjectivity concern.)

> **中文翻译与解释：**
> 这是整个实验"怎么做"的部分，从构造三元组讲到评估指标。逐步解释：
>
> **Step 0（先给数据集画关系地图）**：先从那 11.4 万条 caption 里抽 300–500 条，人工归成几个大的关系类别，统计分布。这一步有两个作用：① 确认你的三类关系在数据里都有足够样本；② 它本身就是一个小成果（你给一个杂乱的数据集做了"关系类型地图"，作者没做过）。**注意**：这步是"测试集"层面的人工归类，不是训练，量很小，CPU 就能跑文本 embedding。
>
> **Step 1（半自动构造三元组）**：一个三元组 = 3 张图（锚点 / 关系相似但外观不同的正样本 / 外观相似但关系不同的负样本）。"半自动"的意思是**算法帮你把候选从上千张缩到十几张，你只在这十几张里点选**：找正样本用 caption 文本相似度排序，找负样本用 CLIP 视觉相似度排序。所有图都来自作者数据集，不用自己满世界找图（这正是立意一比立意二省心的地方）。
>
> **Step 2（纯外观子实验）**：单独造一组只测"表面像不像"、不含关系的三元组，用来回答"RelSim 属性能力有没有退化"。逻辑：如果 RelSim 在这上面明显输给 CLIP，就是"为了关系能力牺牲了属性能力"的直接证据；如果打平，说明它兼顾了。
>
> **模型**：RelSim 是 7B，用学校 GPU 跑；CLIP/DINO 很小，哪都能跑。**全程不训练任何模型，只做推理**——这点一定要在 meeting 上强调，因为它说明工作量可控、你没有 CS 背景也能完成。
>
> **评估指标**：
> - **主指标 = 三元组准确率**：模型把"关系匹配"判得比"外观匹配"更相似的比例，**按每个模型、每类关系分别算**。
> - **关键对比 = RelSim 和 CLIP/DINO 的准确率"落差"，跨关系类型看**。H1 预测：时间演变类落差大、空间容器类落差小。**你的发现就藏在这个"落差随关系类型变化"里**，而不是任何单独一类的胜负里——这是你前几轮反复纠结后定下来的正确立意。
> - **次指标 = 分数差**：不只看"判对没"，还看"判得多有信心"。
> - **标签验证**：找 1–2 个同学独立核对你的部分三元组标签，确保你的关系判断不是你一个人的主观偏见。**这一条专门用来回应"关系相似度很主观"这个 limitation**，会让老师觉得你很严谨。

---

## 6. Expected Outcomes (and why every outcome is informative)

A key design property: **the project's value does not depend on RelSim "winning."** Because the finding lives in the *gap across relation types*, every outcome is interpretable:

| Outcome | Interpretation |
|---|---|
| Gap large for temporal evolution, small for spatial containment (H1 holds) | RelSim's advantage is **concentrated**, not global — a refinement the paper's aggregate numbers hide. |
| Gap small even for temporal evolution | RelSim's relational ability is **less robust than the paper's framing suggests** — echoes the human-A/B-testing tie. A valid critical finding. |
| RelSim worse than CLIP on some relation type | RelSim is **misled by appearance** there, or under-exposed to that relation in training — testable via the released training data. |
| Pure-appearance set: RelSim ≈ CLIP | RelSim **retained** attribute ability (no trade-off). |
| Pure-appearance set: RelSim < CLIP | Evidence of a **relational-vs-attribute trade-off**. |

> **中文翻译与解释：**
> 这部分是"预期结果"，但它真正的作用是**向老师证明你已经预先想清楚了每一种结果各意味着什么**——这是一个设计良好的评估实验的标志。
>
> 核心信息：**你的项目不依赖 RelSim 赢**。因为发现藏在"不同关系类型之间的落差"里，所以无论数字往哪倒，你都有明确且有价值的结论：H1 成立 → 你揭示了 RelSim 的优势是"局部的"而非"全局的"；H1 不成立（哪怕在时间演变类落差也小）→ 你给出了一个批判性发现，呼应论文人工 A/B 打平的现象；RelSim 在某类输了 → 你可以去看训练数据是不是这类样本太少（可验证）；纯外观组打平/落后 → 分别对应"没有能力权衡"/"存在能力权衡"。
>
> 在 meeting 上把这张表讲一遍，老师基本就放心了——因为他最怕的就是"万一结果不显著你就没东西交"，而你已经证明了这种情况不存在。

---

## 7. Feasibility, Scope, and Compute

- **No training.** Inference-only on released checkpoints — feasible without a strong ML/CS background.
- **Compute.** RelSim (7B) runs on the school GPU; embeddings for ~150 images are precomputed once (trivial). CLIP/DINO and sentence-transformers are lightweight.
- **Built-in safety margin.** I will complete **two relation types + the pure-appearance set first** (a complete, submittable result), then add the third relation type if time allows. This guarantees a finished deliverable regardless of pace.

> **中文翻译与解释：**
> 这部分讲"可行性、范围、算力"，专门用来打消老师对"你能不能做完"的顾虑。三个要点：① 不训练任何模型，只做推理，没有 CS 背景也能做；② 算力上 7B 模型用学校 GPU 没问题，要处理的图只有约 150 张，算一次 embedding 就够，很轻；③ **先做两类关系 + 纯外观组（这就是一个完整可交付的成果），有余力再加第三类**——这种"先保底、再加码"的安排本身就是项目管理能力的体现，也保证你不会落到"什么都没做完"的境地。

---

## 8. Limitations and Future Work (brief)

- **Subjectivity of relation labels** — mitigated by peer label-validation, but acknowledged.
- **Small, curated sample** — this is a focused diagnostic study, not a large-scale benchmark.
- **Future work:** test whether RelSim relies on a shallower shortcut — e.g., matching images via *anonymous-caption-template similarity* rather than true relational structure (a concern raised in class). This is a deeper question left for later.

> **中文翻译与解释：**
> 主动写出局限和未来方向，会让老师觉得你诚实、想得远。三点：① 关系标签主观（用同学交叉验证来缓解）；② 样本小（你做的是聚焦的诊断研究，不是大型 benchmark，这是有意为之）；③ **future work 里挂上"RelSim 会不会只是学会了 anonymous caption 模板的匹配，而不是真正的关系结构"**——这正是课上有同学提出的质疑，你把它放进未来方向，既显示你听进去了、想得深，又不把这次的工作量撑爆。

---

*Paper: Thao Nguyen, Sicheng Mo, Krishna Kumar Singh, Yilin Wang, Jing Shi, Nicholas Kolkin, Eli Shechtman, Yong Jae Lee, Yuheng Li. "Relational Visual Similarity." CVPR 2026. arXiv:2512.07833. Code/data/model: github.com/thaoshibe/relsim*
