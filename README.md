# Resume–JD Optimizer Skill

一个面向中文招聘场景的可复用 Agent Skill，用于分析岗位 JD、识别核心能力与辅助能力，并在不编造经历的前提下评估和优化简历表达。

## 主要能力

- 保留 JD 原始职责顺序，并将职责拆为可独立判断的原子要求。
- 区分面向用户的“核心能力”和“辅助能力”，内部再完成角色路由与证据排序。
- 识别硬门槛、加分项、事实缺口和需要追问的信息。
- 将简历事实与 JD 要求逐项匹配，避免将“参与”夸大为“主导”。
- 支持 AI 产品经理、产品运营、用户增长、用户运营、电商运营、金融科技、银行运营、采购等岗位配置。

## 在 ChatGPT / Codex 中使用

本仓库采用 OpenAI Agent Skills 的标准目录结构：`SKILL.md` 是入口，`references/`、`scripts/` 和 `tests/` 提供规则、校验与回归测试。可将整个 `resume-jd-optimizer` 文件夹安装到支持 Skills 的 ChatGPT、Codex 或 Agent 环境；也可将发布 ZIP 上传到支持 Agent Skills 的 OpenAI API 环境。

GitHub 仓库本身不会自动安装 Skill，需要在目标产品或 Agent 工程中显式安装/上传。官方说明：

- [Skills 概念](https://developers.openai.com/plugins/concepts/skills)
- [Agent Skills API 指南](https://developers.openai.com/api/docs/guides/tools-skills)

本地 Codex 常见安装方式：

```text
<CODEX_HOME>/skills/resume-jd-optimizer/
```

请复制完整文件夹，不要只复制 `SKILL.md`。

## 验证

在仓库根目录运行：

```bash
python scripts/validate_role_configs.py
python -m unittest discover -s tests -p "test_*.py" -v
```

## 隐私与事实安全

本公开仓库只包含通用规则、脱敏岗位配置和校验代码，不包含个人简历、真实测试材料、测试台账或 API 密钥。使用者也不应把未经授权的候选人材料提交到公开仓库。

## 许可说明

当前仓库暂未附加开源许可证。代码和规则可以公开查看，但在添加许可证前，不代表已授予复制、修改或再分发许可。
