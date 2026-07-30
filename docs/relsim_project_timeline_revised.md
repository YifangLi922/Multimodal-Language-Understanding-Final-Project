# Relsim Project Timeline（Updated）

## 先想清楚：你现在要完成的是什么

你的项目不再是“给整个数据集建立完整的关系 taxonomy”，而是一项小规模、受控的诊断实验：

> 给 RelSim、CLIP 和 DINO 同一批三元组，看它们能否优先识别关系相似，而不是被表面外观误导；再按关系家族和 conflict / aligned 条件分别统计结果。

整套项目由四个零件组成：

1. **一套定义清楚的评测数据**：少量关系家族，每类区分 conflict 和 aligned。
2. **三个必做打分器**：RelSim、CLIP、DINO；base Qwen 只作为可行时增加的对照。
3. **一套统一评估逻辑**：三元组准确率、paired model gap、bootstrap 95% CI。
4. **一套人工验证机制**：确认每个 triplet 中谁的关系更像、谁的外观更像。

你的核心发现不再只是“哪个模型准确率最高”，而是：

- 同一种关系中，外观线索从帮助变成误导时，RelSim 的优势是否增大；
- 在相同 conflict 条件下，RelSim 的优势是否随关系家族改变。

---

## 当前最重要的时间限制

你将在 **8 月 3 日回家**。离开德国后，可能无法继续稳定使用学校网络和 GPU。

因此，在离开德国前，最重要的目标不是把 report 写完，而是：

> **把完整 pipeline 跑通，拿到至少一版真实结果，并把之后可能需要的 GPU 产物全部保存下来。**

离开前应尽量保存：

- test split 图片或可复现的图片清单；
- 所有最终图片及候选图片的 RelSim / CLIP / DINO embeddings；
- 原始 similarity scores；
- 第一版 accuracy 结果；
- 模型 checkpoint、环境版本和运行命令；
- 能在没有 GPU 的情况下重新统计和画图的 CSV / NPZ 文件。

RelSim 官方接口可以批量提取图像 embedding。因此，即使最终 triplet 还没有全部确定，也可以先对较大的候选池，条件允许时甚至整个 14k test set，预计算并保存 embedding。回家后只需选择图片 ID 和读取 embedding，不必重新运行大模型。

---

## 一个关键策略

仍然遵循原 timeline 的原则：

> **先用最小规模把整条链路从头到尾跑通，再扩大规模。**

但是现在要再加一条：

> **在离开学校 GPU 前，优先做所有“回家后无法轻易补做”的工作。**

关系分类、人工验证、统计和写作可以回家继续；模型安装、图片下载、RelSim embedding 和大批量推理应尽量在德国完成。

---

# 阶段 A：把环境和模型跑通——已完成

这一阶段已经完成。

已完成内容：

- [x] RelSim 环境安装并能正常加载模型；
- [x] RelSim 能对两张图片输出 similarity score；
- [x] CLIP 能提取 embedding 并计算 cosine similarity；
- [x] DINO 能提取 embedding 并计算 cosine similarity；
- [x] 三个模型均能对任意两张图片输出一个可比较的模型内分数。

这一阶段解决了项目最大的技术风险：三个模型都能够运行。

---

# 阶段 B：串出“评估一个三元组”的最小流程——已完成

这一阶段已经完成。

一个 triplet 包含：

- `anchor`
- `positive`
- `negative`

对每个模型计算：

```text
sim(anchor, positive)
sim(anchor, negative)
```

如果：

```text
sim(anchor, positive) > sim(anchor, negative)
```

则该模型在这个 triplet 上记为正确。

已完成内容：

- [x] 一个 triplet 可以输入 pipeline；
- [x] RelSim、CLIP、DINO 都能完成同一判断；
- [x] 每个模型能够输出 similarity、margin 和 correct / incorrect；
- [x] 整条“图片 → embedding → similarity → triplet 判断”链路已跑通。

后续阶段不需要重新设计模型流程，只需要构造更可靠的数据，并批量运行同一 pipeline。

---

# 阶段 C：冻结评测设计并构造最小可用数据集

这一阶段从现在开始。

## C1. 停止完整 taxonomy，改做 feasibility scan + codebook

不再把 400 条 caption 全部分进 temporal、structural、containment 和 other。

已有 400 条 caption 只用于：

1. 判断目标关系是否有足够候选；
2. 找到适合检索候选的关键词；
3. 写清楚每类关系的定义和排除标准。

每个关系家族只需要一份短 codebook：

- 一句话定义；
- inclusion criteria；
- exclusion criteria；
- 2 个清楚正例；
- 2 个边界反例。

不符合目标类别、含有多个同等显著关系、或图片和 caption 不一致的样本可以直接丢弃。

## C2. 确定核心关系家族

### 必做：Temporal transformation

定义：

> 同一个对象、过程或系统呈现有顺序的状态变化。

必须从图片中看到 progression、before/after 或多个阶段。

需要特别记录图片是否采用：

- 多格图；
- before/after；
- 左到右排列；
- 重复对象序列。

因为模型可能只识别这些版式，而不是真正理解时间变化。

### 第二关系家族：先检查样本，再决定

优先考虑：

> **Compositional formation**：多个可见部分共同形成一个新的、可识别的整体。

但不能为了类别名称好看而硬凑样本。只有在 test split 中有足够清晰候选，并且能够同时构造 conflict 和 aligned triplet 时才保留。

如果 composition 样本不够，就换成另一种：

- 与 temporal 明确不同；
- 容易写清楚 inclusion / exclusion；
- test split 中数量足够；
- 人能够稳定判断的关系。

### Optional：Spatial containment

Containment 只作为第三类加分项。它不是本周拿到结果的前提，也不是完整项目的必要部分。

## C3. 构造两种条件

每个关系家族都尽量构造：

### Conflict triplet

- Positive：关系更相似，但外观不同；
- Negative：外观更相似，但关系不同。

最终人工判断应满足：

```text
关系：P > N
外观：N > P
```

### Aligned triplet

- Positive：关系和外观都更相似；
- Negative：关系和外观都不同。

最终人工判断应满足：

```text
关系：P > N
外观：P > N
```

Aligned 主要作为控制条件，所有模型接近满分也是可以解释的结果。

## C4. 最小规模先跑

不要先制作 100 个 triplet。

首先准备：

- 少量 Temporal conflict；
- 少量 Temporal aligned；
- 少量 attribute-priority control。

只要这三组能够完整进入 pipeline，并输出分组结果，就已经形成一版可运行的实验。

## C5. 候选选择规则

Caption、CLIP 和 DINO 都只用于缩小候选范围。

不能直接把 CLIP 最近邻当作 negative，因为这会变成专门针对 CLIP 的测试集。

正确流程：

```text
caption / CLIP / DINO 提供候选
→ 人工看图
→ 按 codebook 选择
→ 人工验证
→ 冻结 triplet
→ 最后查看模型结果
```

Caption 不是 ground truth。图片和 caption 不一致时，以图片为准。

---

# 阶段 D：在离开德国前跑通批量实验并拿到结果

这是目前最高优先级的阶段，目标是在 **8 月 3 日离开前完成**。

## D1. 先得到一版真实结果

最低要求是用三个模型跑完：

- Temporal conflict；
- Temporal aligned；
- Attribute-priority control。

即使每组暂时只有少量样本，也要先生成：

- 每个 triplet 的原始 similarity；
- 每个模型的 correct / incorrect；
- 每组 accuracy；
- RelSim − CLIP gap；
- RelSim − DINO gap；
- 第一批失败案例。

这版结果的作用是确认：

- 分组统计代码正确；
- 数据字段够用；
- 模型输出能够解释；
- conflict / aligned 的设计确实能运行。

如果这一版结果有问题，应当在仍能使用学校 GPU 时发现并修复。

## D2. 尽量预计算，而不是只计算最终 triplet

离开前应尽量对以下图片预计算 embedding：

1. 所有已经确定的 final triplet 图片；
2. 所有可能进入第二关系家族的候选图片；
3. 所有 temporal 候选图片；
4. 条件允许时，整个 14k test set。

至少保存：

```text
image_id
image_url
local_path 或 hash
relsim_embedding
clip_embedding
dino_embedding
```

RelSim embedding 一旦保存，回家后可以直接计算任意图片组合的 cosine similarity，不再需要加载 7B 模型。

如果整个 test set 预计算时间过长，优先顺序是：

```text
final triplets
→ 已筛选候选池
→ temporal 全部候选
→ 第二关系全部候选
→ 其余 test set
```

## D3. 保存所有 GPU 相关资产

离开学校前必须保存：

- RelSim、CLIP、DINO 的环境信息；
- `pip freeze` 或 conda environment；
- checkpoint 名称和版本；
- 运行脚本；
- embedding 文件；
- raw score CSV；
- 已下载图片；
- 下载失败清单；
- image URL 和 hash；
- 第一版结果表；
- GPU 日志和 OOM 处理参数。

所有内容至少备份到两个位置，例如：

- GitHub：代码和小型 manifest；
- 云盘或移动硬盘：图片、checkpoint、embedding 和结果文件。

不要只把结果留在学校服务器上。

## D4. Base Qwen 只做快速可行性检查

Base Qwen 是可选对照，不应阻碍三模型主实验。

只有在能保持与 RelSim 可比的 prompt、pooling、projection 和 similarity 计算时才加入。

止损规则：

> 如果短时间内不能确认公平实现，就记录原因并停止。先保证 RelSim、CLIP、DINO 的完整结果落盘。

## D5. 离开德国前的完成标准

满足以下条件，就可以安心回家继续：

- [ ] 三模型 batch pipeline 可一键运行；
- [ ] 至少一版 temporal conflict / aligned / attribute-control 结果已经生成；
- [ ] final triplet 和候选池 embedding 已保存；
- [ ] 最好完成全部 test-set RelSim embedding；
- [ ] 图片、manifest、代码和环境均已备份；
- [ ] 离开 GPU 后仍可用保存的 embedding 重新计算结果。

---

# 阶段 E：回家后扩展数据、完成人工验证和最终分析

回家后主要做不依赖学校 GPU 的工作。

## E1. 扩展第二关系家族

在 temporal 主实验已经跑通后，再决定第二关系家族。

目标是让第二关系家族也包含：

- conflict；
- aligned。

只有至少两个关系家族，才能完整回答：

> RelSim 的优势是否随关系类型变化？

如果时间不足，Temporal conflict + Temporal aligned + Attribute control 仍然是一份完整的保底实验，可以重点回答 conflict sensitivity。

## E2. 全量人工验证

每个最终 triplet 让独立标注者回答：

1. 哪个候选和 anchor 的关系更像？
2. 哪个候选和 anchor 的外观更像？

验证时隐藏：

- caption；
- positive / negative 标签；
- 模型分数；
- 候选来自 CLIP、DINO 还是文本检索。

只保留满足预设条件的 triplet。模糊样本直接删除，不强行解释。

理想情况是两位标注者验证全部样本；至少应有一位独立标注者验证全部样本，并由另一位复核分歧样本。

## E3. 冻结最终 benchmark

在正式报告结果前固定：

- triplet ID；
- relation family；
- conflict / aligned；
- anchor / positive / negative；
- human validation；
- layout metadata；
- image hash；
- selection notes。

冻结后不能根据某个模型的表现换题。

## E4. 运行最终统计

主指标：

```text
triplet accuracy
```

关键比较：

```text
RelSim − CLIP
RelSim − DINO
conflict gap − aligned gap
family 1 gap − family 2 gap
```

使用 triplet-level bootstrap 计算 95% confidence interval。

每格样本较少时 CI 可能很宽。报告中将项目定位为：

> small-scale diagnostic evaluation

不要因为没有显著差异就说模型完全相同，也不要为了显著性继续人工挑题。

Margin：

```text
sim(A,P) − sim(A,N)
```

只用于同一模型内部分析，不直接跨模型比较 raw margin。

## E5. 定性分析和写作

保存并分析至少三类案例：

- RelSim 正确，CLIP/DINO 错误；
- 全部模型错误；
- baseline 正确，RelSim 错误。

Temporal 类还要专门检查：

- 模型是否依赖多格图；
- 是否依赖 before/after 布局；
- layout-matched negative 是否使结果改变。

最终报告重点回答：

1. conflict 是否放大 RelSim 优势；
2. 不同关系家族的 gap 是否不同；
3. RelSim 在 attribute-priority control 上表现如何；
4. 哪些案例显示真正关系理解，哪些案例显示 shortcut。

---

## 项目范围的优先级

### 保底可交版本

- Temporal conflict；
- Temporal aligned；
- Attribute-priority control；
- RelSim、CLIP、DINO；
- 人工验证；
- accuracy、paired gap、bootstrap CI；
- 失败案例。

### 完整主线版本

在保底版本上增加：

- 第二关系家族 conflict；
- 第二关系家族 aligned；
- 跨关系家族比较。

### 可选加分项

- Base Qwen no-LoRA；
- Spatial containment 第三类。

---

## 一句话记住整个节奏

> **A、B 已完成 → C 冻结关系定义并做最小数据 → D 在德国把批量 pipeline、embedding 和第一版结果全部跑出来并备份 → E 回家后扩展第二关系、完成人工验证、统计和写作。**

当前最重要的不是继续扩大 taxonomy，而是确保离开学校 GPU 时，你已经拥有：

> **可运行的代码、可重复使用的 embeddings、真实的初步结果，以及回家后不依赖 GPU 也能继续完成项目的全部材料。**
