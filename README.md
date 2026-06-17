# lawiki

把一个法律案件的资料整合成**可控、可溯源**的案件 wiki。成果是一个**可被不同 agent 使用的 skill**（`skill/lawiki/SKILL.md`），不是 CLI 工具。

## 流水线

```
原始资料/ ──makeitdown──▶ _md/ ──lawiki skill──▶ wiki/
```

- `原始资料/`：你丢入的法律文件（不可变）。
- `_md/`：makeitdown 转换出的 markdown（不可变来源层，带 frontmatter 与 report.json）。
- `wiki/`：LLM 按 skill 构建维护的案件 wiki：案件主体 / 法律关系 / 法律事实 / 时间线 + index/log。

## 上游依赖

[makeitdown](https://gitee.com/code-lawyer/makeitdown)（独立工具）：把各式文件转成 LLM 可读的 md。lawiki 通过其稳定输出契约（frontmatter 的 `source` / `quality: suspect` 等）对接。

## 在不同 agent 下挂载

- **Claude Code / Copilot**：把 `skill/lawiki/` 放入对应的 skills 目录，agent 会按 `description` 自动触发。
- **Codex 等**：把 `skill/lawiki/SKILL.md` 内容作为系统指令喂给 agent，或放入案件目录作 `AGENTS.md`。

## 用法

把文件放进某案件的 `原始资料/`，让 agent "处理 / 整理 / 建库"。agent 会调 makeitdown 转换、再按 skill 把来源归档进 `wiki/`，无需手动跑中间步骤。

## 可控性（为何可信）

skill 内嵌五条不可违反的铁律：零来源不可写、不推断不脑补、可疑来源标未核验、矛盾只暴露不调和、要害逐字照录。每条事实挂固定格式来源锚点 `〔来源: _md/…：「逐字片段」〕`，可回溯、可机检。

## 设计

`docs/superpowers/specs/2026-06-16-lawiki-design.md`
