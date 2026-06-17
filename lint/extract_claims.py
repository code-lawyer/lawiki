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
from lint_wiki import ANCHOR_RE, SPLIT_RE  # noqa: E402
from _normalize import norm, norm_with_map  # noqa: E402

_LEAD = re.compile(r"^\s*(?:[-*+]\s+)?")  # 列表项前导符


def _context(root: Path, src: str, quote: str, cache: dict,
             window: int = 120) -> str:
    """在源文件里定位引文，返回其前后各约 window 字的上下文窗口（折叠空白）。
    判官靠它判蕴含——既不上下文饿死，又不喂全文。定位失败返回空串。"""
    sp = root / src
    if not sp.is_file():
        return ""
    if sp not in cache:
        cache[sp] = norm_with_map(sp.read_text(encoding="utf-8"))
        cache[(sp, "raw")] = sp.read_text(encoding="utf-8")
    nsrc, idxmap = cache[sp]
    raw = cache[(sp, "raw")]
    frags = [f for f in SPLIT_RE.split(quote) if f.strip()]
    if not frags:
        return ""
    anchor_frag = max(frags, key=len)  # 用最长片段定位最稳
    nq = norm(anchor_frag)
    p = nsrc.find(nq)
    if p < 0 or not nq:
        return ""
    raw_start = idxmap[p]
    raw_end = idxmap[min(p + len(nq) - 1, len(idxmap) - 1)] + 1
    ctx = raw[max(0, raw_start - window): raw_end + window]
    return re.sub(r"\s+", " ", ctx).strip()


def get_pairs(root: Path) -> list[dict]:
    wiki = root / "wiki"
    cache: dict = {}
    pairs: list[dict] = []
    for md in sorted(wiki.rglob("*.md")):
        page = md.relative_to(root).as_posix()
        for line in md.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(">"):
                continue
            matches = list(ANCHOR_RE.finditer(line))
            if not matches:
                continue
            # 每个锚点配它**紧前**的那段文字（锚点引它前面的子断言），
            # 而非整行——一行多锚点时各管各的子断言。
            last = 0
            for m in matches:
                claim = _LEAD.sub("", line[last:m.start()]).strip(" ；;，,、")
                last = m.end()
                src, quote = m.group(1).strip(), m.group(2).strip()
                pairs.append({
                    "page": page,
                    "claim": claim,
                    "source": src,
                    "quote": quote,
                    "context": _context(root, src, quote, cache),
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
