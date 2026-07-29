# RelSim 关系家族标注 Codebook（中文草稿）

本文档对应 `relsim_project_proposal_revised.md` 第 6 节要求的交付物：一份用于人工判断"某张图片是否属于目标关系家族"的标注规则手册。它的作用是保证你自己（以及以后可能帮忙复核的人）在不同批次、不同时间标注时用的是同一套标准，而不是凭当下感觉判断。

**正例和边界反例均来自 `review/confirmed_candidates.csv`（人工看图标注的结果），下面每条描述是我根据 caption 和图片文件名推断写的初稿——你最终确认时请务必点开对应链接看一眼原图，确认描述和图片实际内容一致，有出入的地方直接改。**

数据来源：Nguyen et al. "Relational Visual Similarity" 官方 anonymous-captions-114k 数据集的 **test split**（14881 条，非 train split）。

---

## 1. Temporal Transformation（时间性转变）

### 一句话定义

同一个对象、过程或系统，呈现出有顺序的状态变化；图片本身必须能看到多个状态、或清楚的 before/after 结构，不能只靠 caption 文字判断。

### Inclusion criteria（必须同时满足）

- 图片中能看到 ≥2 个状态，或清楚的 before/after 结构（多格图、时间轴排列、序列拼图等都算）；
- 这个"变化"是图片的核心内容，不是背景里的次要细节；
- 变化的主体是**同一个**对象/过程/系统的不同阶段，不是若干个不相关物体的罗列。

### Exclusion criteria（踩中任何一条都不算，判为 boundary_reject 或 discard）

- 只是很多不同物体堆放在一起，没有时间顺序；
- 多个姿势/角度但没有状态变化（比如同一个人不同角度的照片，不算"变化"）；
- 单一瞬间的动作（不是"过程"，是一个动作的一帧）；
- **caption 提到了"transform"/"progress"/"stages"等词，但图片实际只呈现了单一的最终状态，看不到过程或多个阶段**（这是最容易误判的一类，标注时要especially小心）；
- 单纯的静态象征/比喻画面（比如用一个摆拍场景"象征"某个抽象概念，但画面本身不是真实的状态变化记录）；
- **画面里出现的是同一物种/主题的不同个体，各自处于不同阶段（比如一张图里同时有一只茧和一只蝴蝶），但无法确认这是"同一个体"的连续变化——更像是把两个不同个体的照片并列放在同一画面里，而不是单一主体真实的状态演变过程。**

### 版式标注提醒

Temporal 类图片经常用固定版式（多格图、月相图、生命周期图解这类圆形/横排模板）。**同一种版式的图不要多次计入正例**，优先保留外观差异大的例子，避免模型学到的只是"认识这种排版"而不是真正理解"随时间变化"。

### 正例 1

- **image_hash**: `f37aebc58e6f499c7b3bdf740e730ca1`
- **caption**: "The life cycle of a {Insect}, showcasing its development from a {larva} through metamorphosis to a fully formed {adult}."
- **url**: https://us.123rf.com/450wm/mathisa/mathisa1606/mathisa160600092/60898309-isolated-five-bar-swordtail-butterfly-life-cycle-antiphates-pompilius-on-twig-with-clipping-path.jpg
- **为什么符合**：蝴蝶生命周期图解，明确呈现幼虫→蛹→成虫的多个阶段，同一个体的状态变化清晰可辨，是最典型的 temporal transformation。

### 正例 2

- **image_hash**: `ebb0a441f27c21308e90b6f3f9ab0d3f`
- **caption**: "The transformation of {Ingredient} into {Product} shown through stages: {Raw Material}, {Processed Form}, {Finished Item}"
- **url**: http://1tb.favim.com/preview/7/763/7632/76327/7632706.jpg
- **为什么符合**：食材加工过程分阶段展示（原料→加工中→成品），跟正例 1 的生物题材完全不同，外观差异大，适合和正例 1 搭配构造 conflict/aligned triplet 时保证视觉多样性。

### 边界反例 1

- **image_hash**: `f16b49b38517684a39799a2881b3b3a9`
- **caption**: "Visual representation of {Insect} transitioning from {Pupa} to {Adult} during metamorphosis."
- **url**: https://imgc.artprintimages.com/img/print/paul-harcourt-davies-common-swallowtail-butterfly_u-l-pzflw30.jpg
- **为什么不算（踩中 exclusion）**：画面里确实同时出现了两个阶段——下方是茧、上方是蝴蝶——但更像是**两只处于不同发育阶段的昆虫个体恰好出现在同一张画面里**，而不是可以确认的"同一个体"的连续变化过程，看不出两者之间明确的演变/因果关系。踩中新补充的 exclusion 标准："同一物种不同个体各处于不同阶段，但无法确认是同一个体的变化"。这一对（正例 1 vs 边界反例 1）是很好的教学案例：正例 1 是明确的单一个体多阶段生命周期图解，边界反例 1 则是"看起来像，但主体身份对不上"的典型陷阱。

### 边界反例 2

- **image_hash**: `e98f0bf7516edfd67c4645687bf394b9`
- **caption**: "Creative use of {Tiny Objects} to illustrate {Concepts} like progress, teamwork, and challenges on a {Background}."
- **url**: https://img.freepik.com/free-photo/miniature-shopping-cart-trolley-top-stack-used-gold-coins-white_105035-355.jpg
- **为什么不算（踩中 exclusion）**：画面焦点其实只是**放在一枚金币上的购物车**，caption 里暗示的"金币逐渐堆积增长"实际上只是背景里被虚化处理的一堆金币，并没有真的展示"从少到多"的多个离散阶段——增长感完全是靠景深/虚化的构图手法**暗示**出来的，不是真实拍到的状态变化过程。踩中"静态象征/比喻画面"这条排除标准。

### 常见候选检索关键词（仅用于缩小候选范围，不代表命中就一定符合）

`transform`, `stage(s)`, `decay`, `rot(ten)`, `ripen`, `melt`, `burn(ing)`, `grow(th/ing)`, `aging/aged`, `progress`, `life cycle`, `metamorphosis`, `evolve`, `wither`, `bloom`, `weather(ing)`, `rust(ing)`, `construction`, `destroy`, `damaged`, `crumble`, `fade(d/ing)`, `dissolve`, `before/after`

---

## 2. Compositional Formation（部件构成整体）

### 一句话定义

多个看得见的部件/物体/材料，被有意摆放或组合在一起，共同构成一个可以被认出来的、更大的整体（形状、图案、符号、造型）。

### Inclusion criteria（必须同时满足）

- 图片里"部件"和它们拼成的"整体"都清楚可辨认，两者都能看到；
- "部件拼成整体"是图片的核心内容，不是背景里的小装饰；
- 能用一句话说清楚"什么部件拼成了什么整体"（例如"咖啡豆拼成心形""水果块拼成动物造型"）。

**判断的关键问题：图片里能不能同时数出"好几个部件"和"一个整体"？** 如果只有一个连续物体被整体塑形（不是多个部件拼接），不算。

### Exclusion criteria（踩中任何一条都不算，判为 boundary_reject 或 discard）

- 只是很多物体随意堆放在一起，没有拼出新的、可识别的整体形状；
- 双重曝光/图像叠加效果（不是真实的物理摆放）；
- 两个物体融合成一个"杂交怪物"（长成了一个新东西，而不是"部件仍可辨认+组成整体"的结构）；
- 只是表面印花/装饰图案（不是物体本身摆出来的）；
- 一个物体单纯放在另一个物体"里面"——这属于 spatial containment，不是 composition；
- 单一物体的符号化/象征性表达（画面里其实只有一个物体或一个抽象符号，不是"多个部件拼成整体"的结构）。

### 正例 1

- **image_hash**: `df567ccf0076cfe15dc758ce5179fc77`
- **caption**: "Creative use of {Objects} to form a {Shape}."
- **url**: https://img.freepik.com/free-photo/coffee-grains-heart-form_23-2147896434.jpg
- **为什么符合**：大量咖啡豆（可数的独立部件）摆成一个心形（可识别的整体），部件和整体都清楚可见，是最典型的 compositional formation。

### 正例 2

- **image_hash**: `f9575588fb765aac970bc1766efd47f6`
- **caption**: "Artistic arrangements of {Fruit} and {Vegetables} shaped into the forms of various {Characters}."
- **url**: https://i.pinimg.com/736x/44/d2/bd/44d2bd716582c8f399f6a0a51bce66d4.jpg
- **为什么符合**：水果和蔬菜块拼成人物角色造型，跟正例 1 的几何图形（心形）不同，属于"拼成具象角色"的变体，外观和正例 1 有明显差异，适合搭配使用。

### 边界反例 1

- **image_hash**: `ebee947c663d7c1e66065c1dc8e38f6c`
- **caption**: "A circular design showcasing alternating segments of {Color} arranged in a {Theme/Pattern}."
- **url**: https://bagcraft.uk/wp-content/uploads/2018/02/soake_rainbow_bcspprain_pagoda1.jpg
- **为什么不算（踩中 exclusion）**：图片大概率是一把彩虹配色的伞/纸伞，色块分段排列是**表面印花/装饰图案**，不是"多个独立部件拼成一个新整体"的结构——踩中"只是表面印花/装饰图案"这条排除标准。

### 边界反例 2

- **image_hash**: `ff03babbb0d4908dc16cb99716d5608e`
- **caption**: "Visual representation of {Symbol} for embodying {Concept} or {Process}, using {Object} in a creative way."
- **url**: https://us.123rf.com/450wm/dogfella/dogfella1509/dogfella150900100/45058834-wei%C3%9F-gl%C3%BChbirne-au%C3%9Ferhalb-der-zeichnung-box-gl%C3%BChend-denken-au%C3%9Ferhalb-der-box-oder-anderes-konzept-zu-sein.jpg
- **为什么不算（踩中 exclusion）**：一个"跳出框框思考"主题的灯泡概念图，画面核心是**单一物体的象征性表达**，不是"多个可数部件拼成一个新整体"——踩中"单一物体的符号化表达"这条排除标准。

### 常见候选检索关键词

`form(s/ed/ing) a/an/the`, `arrange(d/ment)`, `shaped like`, `spell(s/ing)`, `made of/from`, `composed of`, `assembl(e/ed/y)`, `mosaic`, `collage`, `pattern`, `letter(s)`, `symbol`, `together form/create/make`

---

## 3. Spatial Containment（可选加分项，暂不需要现在扩充）

按 proposal 第 5.3 节，这一类只在核心实验（temporal + compositional）跑完之后才会考虑要不要加，目前 11 条候选还没有标注，先占位，暂不需要补充正例/反例。

### 一句话定义（占位，来自 proposal）

一个显眼的物体，明显被装在/困在/包裹在/封在另一个有边界的物体或空间"里面"。

### Exclusion criteria（占位）

- on top of（在上面）、beside（在旁边）、behind（在后面）、surrounded by（被围绕但无明确边界）、supported by（被支撑）；
- 比喻意义上的"containment"（抽象表达，没有实际边界物）。

---

## 4. 已知数据质量问题（写作/复核时留意）

- 部分图片 `url_link` 已失效（链接腐烂），标注时判定为 `discard`，不影响 codebook 本身；
- caption 中大量出现未替换的模板占位符（如 `{Object}`），caption 仅用于候选检索，最终判断以图片内容为准；
- temporal 类图片存在版式集中（多格图/月相图/生命周期图解）的风险，已在标注阶段有意识地避免重复计入同一版式的图片。
