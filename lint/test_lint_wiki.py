# -*- coding: utf-8 -*-
"""lint 回归测试：锁住"归一化只消除格式噪声、绝不放过真错"这条底线。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lint_wiki import scan_case  # noqa: E402


def _case(tmp_path: Path, source: str, anchor_snippet: str,
          rel: str = "_md/a.md") -> Path:
    (tmp_path / "_md").mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text(source, encoding="utf-8")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "p.md").write_text(
        f"- 事实 〔来源: {rel}：「{anchor_snippet}」〕\n", encoding="utf-8")
    return tmp_path


def test_exact_match_passes(tmp_path):
    root = _case(tmp_path, "甲向乙借款500,000元。", "甲向乙借款500,000元")
    total, viol = scan_case(root)
    assert total == 1 and viol == []


def test_wrong_number_is_flagged(tmp_path):
    # 真错：金额一位不同，必须被抓出
    root = _case(tmp_path, "甲向乙借款500,000元。", "甲向乙借款500,001元")
    total, viol = scan_case(root)
    assert len(viol) == 1


def test_formatting_noise_passes(tmp_path):
    # 空格/换行/全角逗号/markdown 粗体/表格管道/HTML 标签都是噪声，不应误报
    source = '| **甲** 向乙\n借款 500，000 元 <td>（RMB）</td> |'
    root = _case(tmp_path, source, "甲向乙借款500,000元（RMB）")
    total, viol = scan_case(root)
    assert viol == []


def test_ellipsis_bridges_gap(tmp_path):
    root = _case(tmp_path, "甲方……中间很多字……乙方签字。", "甲方…乙方签字")
    total, viol = scan_case(root)
    assert viol == []


def test_ordered_fragments_out_of_order_is_flagged(tmp_path):
    # 片段在源文里存在但顺序相反 → 视为不符（顺序是语义的一部分）
    root = _case(tmp_path, "乙方在前，甲方在后。", "甲方…乙方")
    total, viol = scan_case(root)
    assert len(viol) == 1


def test_missing_source_file_is_flagged(tmp_path):
    (tmp_path / "wiki").mkdir(parents=True)
    (tmp_path / "wiki" / "p.md").write_text(
        "- 事实 〔来源: _md/missing.md：「随便」〕\n", encoding="utf-8")
    total, viol = scan_case(tmp_path)
    assert len(viol) == 1
