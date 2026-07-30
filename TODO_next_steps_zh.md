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

### 2. 把统计分析结果存成正式文件 —— 已完成 ✅

脚本：`scripts/compute_final_statistics.py`（纯 pandas/numpy，不需要 GPU）。输出三份文件：

- `review/statistics_accuracy_with_ci.csv` —— 每个格子的 accuracy + bootstrap 95% CI
- `review/statistics_paired_gaps.csv` —— RelSim−CLIP / RelSim−DINO 的 paired gap
- `review/statistics_key_comparisons.csv` —— RQ1（跨 family 差异）和 RQ2（conflict 敏感度）需要的关键对比数字

跑出来的实际数字，写报告可以直接用：

**Accuracy + 95% CI**

| relation_family | condition | model | n | accuracy | 95% CI |
|---|---|---|---|---|---|
| attribute_priority_control | control | CLIP | 30 | 100.0% | [1.000, 1.000] |
| attribute_priority_control | control | DINO | 30 | 96.7% | [0.900, 1.000] |
| attribute_priority_control | control | relsim | 30 | 90.0% | [0.800, 1.000] |
| compositional_formation | aligned | CLIP | 22 | 81.8% | [0.636, 0.955] |
| compositional_formation | aligned | DINO | 22 | 86.4% | [0.727, 1.000] |
| compositional_formation | aligned | relsim | 22 | 90.9% | [0.773, 1.000] |
| compositional_formation | conflict | CLIP | 54 | 0.0% | [0.000, 0.000] |
| compositional_formation | conflict | DINO | 54 | 18.5% | [0.093, 0.296] |
| compositional_formation | conflict | relsim | 54 | 22.2% | [0.111, 0.333] |
| temporal_transformation | aligned | CLIP | 28 | 92.9% | [0.821, 1.000] |
| temporal_transformation | aligned | DINO | 28 | 92.9% | [0.821, 1.000] |
| temporal_transformation | aligned | relsim | 28 | 100.0% | [1.000, 1.000] |
| temporal_transformation | conflict | CLIP | 35 | 0.0% | [0.000, 0.000] |
| temporal_transformation | conflict | DINO | 35 | 17.1% | [0.057, 0.286] |
| temporal_transformation | conflict | relsim | 35 | 48.6% | [0.314, 0.657] |

**Paired gap（RelSim − baseline）**

| relation_family | condition | RelSim−CLIP | RelSim−DINO |
|---|---|---|---|
| attribute_priority_control | control | −10.0pp | −6.7pp |
| compositional_formation | aligned | +9.1pp | +4.5pp |
| compositional_formation | conflict | +22.2pp | +3.7pp |
| temporal_transformation | aligned | +7.1pp | +7.1pp |
| temporal_transformation | conflict | +48.6pp | +31.4pp |

**关键对比（RQ1 / RQ2）**

| 对比 | family | baseline | 数值 |
|---|---|---|---|
| conflict gap − aligned gap（RQ2：conflict 敏感度） | compositional | CLIP | +13.1pp |
| conflict gap − aligned gap（RQ2：conflict 敏感度） | compositional | DINO | −0.8pp |
| conflict gap − aligned gap（RQ2：conflict 敏感度） | temporal | CLIP | +41.4pp |
| conflict gap − aligned gap（RQ2：conflict 敏感度） | temporal | DINO | +24.3pp |
| family gap 差异（RQ1：compositional − temporal，conflict 条件下） | — | CLIP | −26.3pp |
| family gap 差异（RQ1：compositional − temporal，conflict 条件下） | — | DINO | −27.7pp |

**怎么读这两组 RQ 数字**：
- RQ2 那四行，**temporal 的 conflict−aligned 差值（+41.4pp / +24.3pp）明显比 compositional（+13.1pp / −0.8pp）大**——说明"外观从帮助变误导时 RelSim 优势变大"这个假设在 temporal 上支持得很扎实，在 compositional 上证据偏弱（跟 DINO 比甚至是负的）。
- RQ1 那两行是负数，意思是 **temporal 的 gap 比 compositional 的 gap 大**（因为算的是 compositional 减 temporal），也就是"RelSim 在 temporal 上的相对优势明显强于 compositional"——这是一个跨 family 有真实差异的证据。

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
| 结果表 + 置信区间 | `review/statistics_accuracy_with_ci.csv`、`review/statistics_paired_gaps.csv`、`review/statistics_key_comparisons.csv`（见上面第 2 点表格） |
| 定性案例 | `review/qualitative_cases.csv` + `review/archive/images/` |
| 可复现代码 + README | `scripts/` + 根目录 `README.md`（已经写好） |
| 最终报告本身 | 待写 |

### 5. README 相关 —— 已确认 ✅

- README 结构（Key Results 放在 Repository Structure/Pipeline 前面）**已确认不用调整**——因为项目还要交一份 ACL 格式的正式 report，那份才是"方法→结果→讨论"的学术顺序，GitHub README 只是给人快速看代码和过程用的，按热门项目"结果先行"的写法就行，两者分工不重复。
- `docs/relsim_project_proposal_revised.md` 和 `docs/relsim_project_timeline_revised.md` 这两份还留着、也还没写进 README 目录结构——**要不要留在最终提交仓库里，还是你自己决定**，决定好之后如果要删，你自己删就行（或者告诉我帮你删）。

---

## 一句话总结现在的位置

数据收集、模型打分、统计分析这三块**全部做完了**。剩下真正需要你动手的只有两件事：**挑定性案例（素材已备好）**和**写最终报告**，外加一个可选项（找人交叉验证）和一个待你自己拍板的小决定（proposal/timeline 留不留）。
