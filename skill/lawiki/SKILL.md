---
name: lawiki
description: Use when building or maintaining a Chinese legal-case knowledge wiki from a folder of case materials — drives makeitdown to convert raw documents to markdown, then files them into a controlled, source-anchored case wiki (案件主体/法律关系/法律事实/时间线). Triggers on 整理案件资料、把案件资料建成 wiki、建案件库、处理这个案子、ingest case files, build a case wiki.
---

# lawiki — 法律案件 wiki 构建

把一个案件的原始资料整合成**可控、可溯源**的 wiki。你（agent）负责全部归档与维护。法律工作不接受模糊和混乱——下面的**铁律（三类标注 + 逐字锚点硬底线）不可违反**。

细节按需读本 skill 的 `references/`（`setup.md` 首次配环境、`page-formats.md` 页面格式+Obsidian 约定、`verification.md` 校验）；不必一次全装进注意力。`<SKILL_DIR>` 指本 skill 实际所在目录。

## 何时用 / 怎么激活

用户把法律文件放进某案件目录的 `原始资料/`，并说「整理案件资料」「把案件资料建成 wiki」「建案件库」「处理这个案子」「build a case wiki」等。

## 流水线

```
原始资料/ ──makeitdown──▶ _md/ ──ingest──▶ wiki/
```

三层结构（前两层不可变，你只写第三层）：
- `原始资料/`：用户丢入的原件，真相之源，**永不修改**。
- `_md/`：makeitdown 转换产物，来源层，**永不修改**。
- `wiki/`：你拥有并维护的案件 wiki。

## 第〇步：首次配环境

第一次在某机器上用、或缺 Python/makeitdown 时，照 **`references/setup.md`** 走：检测环境 → 让用户选 OCR 方式（本地/云端，附优缺点对比与 token 申请网址）→ 安装（并明确告诉用户"正在安装环境…"）→ 告知激活语。环境就绪可跳过本步。

## 第一步：确保案件结构存在

若案件目录下没有 `wiki/`，创建固定结构（不要即兴增减，保证可复现）：

```
wiki/
  index.md   log.md   案件主体/   法律关系/   法律事实/   时间线/
```

并确保案件目录下有 `原始资料/` 与 `_md/`。`index.md`/`log.md` 的初始内容见 `references/page-formats.md`。

## 第二步：转换（调 makeitdown）

在案件目录执行 `makeitdown 原始资料 -o _md`。转换后读 `_md/report.json`，留意 `warned`/`failed`/`skipped`。失败或跳过的文件**不要凭空补内容**，按缺失处理并告知用户。

## 第三步：ingest（逐个来源归档进 wiki）

对 `_md/` 下每个 `.md`：

1. 读其正文与 frontmatter。
2. 若含 `quality: suspect` → 该来源所有引用在锚点后追加「（未核验）」。
3. 抽主体信息 → `wiki/案件主体/<主体名>.md`。
4. 提炼有法律意义的事实点及证据 → `wiki/法律事实/<事实名>.md`。
5. 判定/更新法律关系 → `wiki/法律关系/<关系名>.md`。
6. 把事实按时序并入 `wiki/时间线/总览.md`。
7. 维护交叉引用，更新 `index.md`，向 `log.md` 追加 `## [YYYY-MM-DD] ingest | <来源文件名>`。
8. **确定性校验（lint）**：`python <SKILL_DIR>/lint/lint.py check <案件根目录>`，修到 **0 违规**。
9. **蕴含校验（换实例判官）**：抽取 claim↔引文 → 派全新子代理三分判 → 有界修复 ≤3 轮 → 仍判不过的显著上报用户。

第 8、9 步细节见 **`references/verification.md`**；页面格式与 Obsidian 约定见 **`references/page-formats.md`**。

## 铁律：三类标注 + 一条硬底线（不可违反）

写进 wiki 的每一句话，必须先归入且仅归入三类之一，并按该类规矩处理。

**硬底线**：凡作为「事实」陈述的（EXTRACTED），必须挂逐字来源锚点 `〔来源: _md/…：「逐字原文」〕`；挂不上锚点的，不许当事实写出。

1. **EXTRACTED（原文直取）**：源文档白纸黑字写的。必挂逐字锚点；法律要害（日期/金额/当事人名/条款原文）逐字照录、不转述。**唯一能当事实直述的一类。**
2. **INFERRED（推断）**：你的分析/推论/归纳，非任一来源明文。必须显式标注（`> [!note] 分析`），与事实物理隔离，并写明推断依据。**绝不伪装成事实。**
3. **AMBIGUOUS（存疑）**：拿不准的——来源可疑（`quality: suspect` / OCR 乱码）、多源冲突、或数值无法确证。必须显式打标：可疑引用后缀「（未核验）」；冲突用 `> [!warning] ⚠ 冲突` callout 并列各方与锚点。**绝不静默取舍、绝不当既定事实。**

> 写每句前先自问：这是 EXTRACTED / INFERRED / AMBIGUOUS？三者必居其一、各有其标。**无法归类（无来源、无依据）→ 不写。**

## 引用锚点（机器可校验）

固定格式，**不使用页码**——指明来自哪份文件的哪一部分，带逐字上下文片段：

```
〔来源: _md/<相对路径>：「<逐字上下文片段>」〕
```

- 片段取自源 md 原文、逐字；可含 `…` 表略去（lint 按 `…` 分段、按序匹配）。
- 案件主体每条属性、每个法律事实、每条时间线，都必须挂锚点。
- **一条断言 ← 一条能完整支持它的引文**：别把多个事实塞一条锚点下。
- **别引 OCR 打乱的表头**：扫描件表头常被 OCR 打散、乱序，拼不出连续引文；改引该表里干净、连续的数据行或"总计"行。

## 跨 agent

- **Claude Code / Copilot**：本 `SKILL.md` 按 `description` 自动触发。
- **Codex 等**：把本文件内容作为系统指令喂给 agent，或放入案件目录作 `AGENTS.md`；`references/` 与 `lint/` 随本 skill 一起带上。
