# 接下来要做的事情（临时笔记，正式提交前可删除）

这份文档只是给你自己看的进度清单，不是正式交付物，不会出现在 README 的 repository structure 里。提交前记得删掉这个文件。

---

## 现状：数据收集 + 模型打分已经全部完成 ✅

- Temporal transformation：47 张正例，15 张边界反例
- Compositional formation：38 张正例，3 张边界反例
- 最终 175 个 triplet（169 个已跑出分数），五个格子全部达到或超过 20-25 的目标
- 已经用 `git tag frozen-benchmark-v1` 冻结，**从现在起不要再因为看分数就回头改 triplet**

---

## 剩下要做的事，按优先级排

### 1.（可选，看时间和人脉）人工验证交叉核对

- 现在所有 accept/reject 判断都是你一个人做的。如果身边有同学愿意帮忙，可以随机挑 20-30 个 triplet 让 ta 按 `docs/codebook_en.md` 的标准重新判断一遍，算个一致率，报告里会更扎实。
- 没有人帮忙也没关系，报告里如实写"单人标注，依据书面 codebook"就行，不算硬伤。
- 参考文件：`review/validation_record.csv`（已经生成好，每个 triplet 对应哪次人工判断都能查到）。

### 2. 把统计分析结果存成正式文件（目前只在聊天记录里，没有存文件）

我们之前在对话里算过的这些数字——按 relation_family × condition × model 的 accuracy、RelSim−CLIP/DINO 的 paired gap、bootstrap 95% 置信区间——**目前只存在于聊天记录里，没有写成脚本或者存成 csv 文件**。写报告之前建议让我帮你补一个脚本，把这些数字正式跑出来存成文件（比如 `review/final_statistics_summary.csv`），到时候直接贴进报告，也方便回头复查。

如果你想让我现在就做这件事，直接说一声。

### 3. 定性案例写作

- 素材已经准备好：`review/qualitative_cases.csv`（22 个"RelSim 独赢"+ 51 个"全部模型都错"的案例，带 caption）
- 对应的图片在：`review/archive/images/`（文件名就是 image_hash，可以用 `review/archive/image_archive_index.csv` 查对应关系）
- 挑几个典型的（建议 temporal、compositional 各挑 2-3 个成功案例，1-2 个失败案例），配图写进报告的定性分析部分。

### 4. 写最终报告

报告需要覆盖的内容和对应文件：

| 报告需要的内容 | 对应文件 |
|---|---|
| 方法论 / codebook | `docs/codebook_en.md` |
| 最终数据集 | `review/triplet_manifest.csv` |
| 人工验证记录 | `review/validation_record.csv` |
| 模型打分原始结果 | `review/triplet_results.csv` |
| 结果表 + 置信区间 | 目前只有对话记录里的数字，见上面第 2 点 |
| 定性案例 | `review/qualitative_cases.csv` + `review/archive/images/` |
| 可复现代码 + README | `scripts/` + 根目录 `README.md`（已经写好） |
| 最终报告本身 | 待写 |

### 5. 确认 README 和 proposal/timeline 要不要留在仓库里

- `README.md` 已经写好推送了，你可以先看一下内容是否满意，有问题告诉我改。
- `docs/relsim_project_proposal_revised.md` 和 `docs/relsim_project_timeline_revised.md` 这两份我按你说的先没删，也没写进 README 的目录结构里——**你自己决定要不要留在最终提交的仓库里**，决定好之后如果要删，你自己删就行（或者告诉我帮你删）。

---

## 一句话总结现在的位置

数据和模型打分这块（原本预计"离开德国前"要做的核心工作）**已经全部做完，而且做得比最低要求更扎实**。剩下的都是回家之后不需要 GPU 就能做的事：可选的交叉验证、把统计数字整理成正式文件、挑定性案例、写报告。
