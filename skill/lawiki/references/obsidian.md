# Obsidian 渲染约定（产出以 Obsidian 为基准）

wiki 以 Obsidian 为查看器，用 Obsidian Flavored Markdown：

- **交叉引用用 wikilink** `[[页面名]]`（按文件名解析，跨文件夹有效，重命名自动跟踪）；需自定义显示文字用 `[[页面名|显示]]`，如 `[[北京晨山|晨山]]`。
- **分析/冲突/未核验用 callout**（彩色框）：分析 `> [!note] 分析`、冲突 `> [!warning] ⚠ 冲突`、可疑来源整页提示 `> [!caution] 含未核验来源`。
- **frontmatter 即 Obsidian properties**：每页带 `tags`（板块名，便于过滤/图谱分组）；主体页带 `aliases`（简称，wikilink 自动补全）。
- **来源锚点保持纯文本** `〔来源: …〕`——它是引证不是导航，且要保持正则可校验，**不要**改成 wikilink。
- **vault 建议**：把 `wiki/` 单独作为 vault 打开，图谱最干净（`_md/` 不入图）；若把整个案件目录作 vault，在图谱过滤框输入 `path:wiki` 即可只看 wiki。

> 产出虽以 Obsidian 为基准，但仍是合法 markdown：在非 Obsidian 查看器中 callout 退化为引用块、wikilink 显示为文本，内容不丢。
