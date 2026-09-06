# 新教育人格测量试验：执行记录

日期：2026-09-05。研究目标仍是完成经得起检验的教育人格论文；以下是测量开发进展，尚未完成正式确认和新论文。

## 已完成并核验

1. **实际接口可用性及版本核查。** MiniMax官方的M3、M2.7，以及Gateway的DeepSeek-V4-Pro、Doubao-Seed-2.0-Lite和GLM请求配置，均能完成真实短请求。请求`glm-5.2`实际返回`glm-5.3`；本批GLM数据全部按实际返回部署单独处理，不合并历史GLM-5.2。Gateway仅绑定本机回环地址，保留认证，统计文件写入本研究的忽略目录。
2. **160/160条新回答。** 四个原创模板、16个情境、五模型各两次生成全部正常结束；无空回答、截断、重复请求ID、输入/输出哈希不符或同配置内版本混合。每模型32条；在各自32条中没有完全相同的可见回答。这不证明随机数独立，也不证明行为稳定。审计见`prospective_pilot/generation_audit.json`。
3. **第一版测量诊断48/48次。** 引用和结构全部有效；384个二元事件编码中有5个与agent编写的预期不一致，涉及间接行动邀请和解释步骤的定义边界。原结果与原标签完整保留。
4. **澄清版测量诊断96/96次。** 保留/修订16个旧锚点，并新增16个措辞锚点。全部请求及引用结构有效；768个事件编码中有1个与预期不一致：GLM实际5.3没有把“缺少宽度，因此无法确定面积”编码为知识断言限定。保留分歧，未继续修改规则以追求零分歧。锚点是agent编写的规则诊断，不是人工金标；767/768不能宣称是自然回答编码准确率。
5. **程序验证。** `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests` 完成，98项通过。新增检查包括截断/提供方错误不能计成功、请求与返回模型不能混同、正例必须有原文证据、重复JSON键拒绝、全负例一致性不能冒充正例可靠性，以及此前的来源分组约束。

## 后续状态：旧自然回答评分已停止

后续发现自然回答的大规模引用定位失败和DeepSeek输出预算不足。旧评分进程已由研究者终止，不能按480次完成来报告。保留全部生成回答和失败评分，后续采用原文行号定位证据并先做自然回答格式预检，详见 [测量修订记录](48_natural_measurement_failure_and_line_evidence_revision.md)。以下路径和计划是本文件最初记录的旧阶段。

澄清版量表对160条新回答的三评审编码，共480个请求，输出位于：

`artifacts/educational_personality_v2/prospective_pilot/judge/v2_1/run/`

该阶段必须同时检查真实进程句柄、逐条响应和最终`summary.json`。仅看到响应文件增长或部分成功不能声称完成。第一版自然回答评审清单没有调用；两版评分不会混合。

编码完成后的下一步：

- 检查480条的请求、版本、JSON结构和原文引用覆盖，单独记录错误与缺失；只对三评审均有效的样本计算共识，明确缺失比例。
- 按事件报告自然回答中的正/负一致性、三评审共识、生成重复一致性和表达机会，避免把近乎全0的高一致性当成稳定人格。
- 按实际部署显示画像，检查去掉同模型或同家族评审的敏感性；本轮四模板结果仅用于测量和正式设计。
- 冻结独立来源/模板的确认实验，交错模型调用，分开默认预测增益与情境交互的增量预测增益；随后完成正式实验和英文/中文论文重写。

## 复现入口

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_personality_generation_v2.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/analyze_personality_coding_v2.py \
  --base artifacts/educational_personality_v2/prospective_pilot/judge/v2_1 \
  --run artifacts/educational_personality_v2/prospective_pilot/judge/v2_1/run \
  --output artifacts/educational_personality_v2/prospective_pilot/natural_diagnostics_v2_1 \
  --rubric data/educational_personality_measurement_v2_1.json
```

分析器可以报告未完成覆盖，执行它不等于完成验证。原始生成和评审回答留在Git忽略目录；生成审计和锚点诊断仅输出派生计数、ID、哈希或标签。
