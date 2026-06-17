# -*- coding: utf-8 -*-
"""抽取器回归测试：拆对正确、跳过分析 callout 与标题、一行多锚点拆多对。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_claims import get_pairs  # noqa: E402


def _wiki(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "wiki" / "p.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return tmp_path


def test_basic_pair(tmp_path):
    root = _wiki(tmp_path, "- 蓝驰增资 3000 万 〔来源: _md/a.md：「蓝驰以叁仟万元」〕\n")
    pairs = get_pairs(root)
    assert len(pairs) == 1
    assert pairs[0]["claim"] == "蓝驰增资 3000 万"
    assert pairs[0]["source"] == "_md/a.md"
    assert pairs[0]["quote"] == "蓝驰以叁仟万元"


def test_skips_heading_and_analysis_callout(tmp_path):
    body = (
        "# 标题 〔来源: _md/a.md：「不该抽」〕\n"
        "> [!note] 分析\n"
        "> 推断如此 〔来源: _md/a.md：「也不该抽」〕\n"
        "- 真事实 〔来源: _md/a.md：「该抽」〕\n"
    )
    pairs = get_pairs(_wiki(tmp_path, body))
    assert len(pairs) == 1 and pairs[0]["quote"] == "该抽"


def test_multiple_anchors_one_line(tmp_path):
    root = _wiki(tmp_path,
                 "- 增资前 X；增资后 Y 〔来源: _md/a.md：「X」〕；〔来源: _md/b.md：「Y」〕\n")
    pairs = get_pairs(root)
    assert len(pairs) == 2
    assert {p["quote"] for p in pairs} == {"X", "Y"}
    # 两对共享同一 claim（去掉全部锚点后的该行文字）
    assert all("增资前 X" in p["claim"] for p in pairs)
