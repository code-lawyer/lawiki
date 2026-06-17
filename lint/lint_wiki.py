#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lawiki lint —— EXTRACTED 硬底线的确定性闸门（Tier-1：锚点存在校验）。

对一个案件目录（含 wiki/ 与 _md/）：扫描 wiki 下每个 .md 里的来源锚点
    〔来源: <相对路径>：「<逐字片段>」〕
逐一确认 <逐字片段> 确实**逐字**出现在所指的源文件里。片段中的省略号
（… 或 ...）当作"略去若干字"的通配，按顺序分段匹配。

输出违规清单：① 所指文件不存在；② 片段（或其某一段）在文件中找不到。
这把"事实必须来自原文"的铁律从人工承诺变成机器可查。退出码非 0 表示有违规。

用法：python lint_wiki.py <案件根目录>
（案件根目录下应有 wiki/ 与 _md/）
"""
import re
import sys
from pathlib import Path

ANCHOR_RE = re.compile(r"〔来源:\s*(.+?)：「(.+?)」〕")
SPLIT_RE = re.compile(r"…+|\.\.\.+")

# 归一化"格式噪声"：源文档与手写片段在空格/换行/全半角标点/千分位逗号/直弯引号
# 上常有无害差异。归一后比较——保留数字与文字精确，故"数字写错"仍会被抓出。
_PUNCT = str.maketrans({
    "，": ",", "（": "(", "）": ")", "：": ":", "；": ";",
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "－": "-", "—": "-", "–": "-", "　": "",
})
# 去空白、千分位逗号、以及 markdown/表格格式符（| * # > ` ~ _）——
# 这些绝不会是法律数字或人名的一部分，去掉只消除格式噪声、不放过真错。
_DROP = re.compile(r"[\s,|*#>`~_]")


_TAG = re.compile(r"<[^>]+>")  # 源 md 里的 HTML 表格标签等


def _norm(s: str) -> str:
    return _DROP.sub("", _TAG.sub("", s.translate(_PUNCT)))


def _fragments(snippet: str) -> list[str]:
    """按省略号切成必须按序出现的片段，去掉空白段。"""
    return [s.strip() for s in SPLIT_RE.split(snippet) if s.strip()]


def scan_case(root: Path) -> tuple[int, list[str]]:
    """扫描一个案件目录，返回 (锚点总数, 违规说明列表)。纯函数，便于测试。"""
    wiki = root / "wiki"
    if not wiki.is_dir():
        raise FileNotFoundError(f"找不到 {wiki}")

    cache: dict[Path, str] = {}
    total = 0
    violations: list[str] = []

    for md in sorted(wiki.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for m in ANCHOR_RE.finditer(text):
            total += 1
            rel, snippet = m.group(1).strip(), m.group(2)
            src = root / rel
            where = f"{md.relative_to(root).as_posix()}"
            if not src.is_file():
                violations.append(f"[缺文件] {where}\n          所指来源不存在: {rel}")
                continue
            if src not in cache:
                cache[src] = _norm(src.read_text(encoding="utf-8"))
            body = cache[src]
            # 按序匹配各片段（归一化后）：每段都要在上一段之后出现
            pos = 0
            missing = None
            for frag in _fragments(snippet):
                idx = body.find(_norm(frag), pos)
                if idx < 0:
                    missing = frag
                    break
                pos = idx + len(_norm(frag))
            if missing is not None:
                violations.append(
                    f"[片段不符] {where}\n          来源: {rel}\n          找不到片段: 「{missing}」"
                )

    return total, violations


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 重定向默认 GBK，会糊掉中文
    except Exception:
        pass
    if len(argv) != 2:
        print("用法：python lint_wiki.py <案件根目录>", file=sys.stderr)
        return 2
    try:
        total, violations = scan_case(Path(argv[1]))
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2
    print(f"扫描锚点 {total} 个；违规 {len(violations)} 处。")
    for v in violations:
        print("  - " + v)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
