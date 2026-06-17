#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim↔引文 蕴含校验的**确定性前半**：抽取待判清单。

扫描 wiki，把每条带来源锚点的事实陈述拆成 `(page, claim, source, quote)` 三元组，
输出 JSON 清单。后半（语义判定"引文是否支持断言"）交给一个**独立 LLM 实例**
（子代理）逐对判 支持/不支持/信息不足 —— 见 SKILL.md「蕴含校验」。

只抽 EXTRACTED 事实：跳过标题、跳过以 `>` 开头的 callout（那是已显式标注的
INFERRED 分析，不按事实校验）。一行多个锚点则拆成多对，claim 为去掉全部锚点后的该行文字。

用法：python extract_claims.py <案件根目录>   # JSON 打到 stdout
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lint_wiki import ANCHOR_RE  # noqa: E402

_LEAD = re.compile(r"^\s*(?:[-*+]\s+)?")  # 列表项前导符


def get_pairs(root: Path) -> list[dict]:
    wiki = root / "wiki"
    pairs: list[dict] = []
    for md in sorted(wiki.rglob("*.md")):
        page = md.relative_to(root).as_posix()
        for line in md.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(">"):
                continue
            anchors = ANCHOR_RE.findall(line)
            if not anchors:
                continue
            claim = _LEAD.sub("", ANCHOR_RE.sub("", line)).strip()
            for src, quote in anchors:
                pairs.append({
                    "page": page,
                    "claim": claim,
                    "source": src.strip(),
                    "quote": quote.strip(),
                })
    return pairs


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(argv) != 2:
        print("用法：python extract_claims.py <案件根目录>", file=sys.stderr)
        return 2
    pairs = get_pairs(Path(argv[1]))
    print(json.dumps(pairs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
