#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lawiki lint —— 确定性校验闸门（Tier-A）。

对一个案件目录（含 wiki/ 与 _md/）做四类**确定性**检查：

  违规（hard，退出码非 0）：
    1. 锚点存在   每个 〔来源:…「片段」〕的逐字片段是否（去格式噪声后）逐字、
                  按序出现在所指源文件里 —— EXTRACTED 硬底线。
    2. 死链       每个 [[wikilink]] 是否解析到真实页面或其别名。
    3. 时间线顺序 时间线页内可解析日期是否非递减。

  警告（soft，不影响退出码）：
    4. 覆盖率     _md/ 下哪些源文件从未被任何锚点引用（可能漏 ingest，
                  也可能是有意跳过的草稿，交人判断）。

只消除格式噪声（空白/换行/全半角标点/千分位逗号/markdown/表格/HTML 标签），
数字与文字精确，故"数字写错/张冠李戴"必被抓、"换行差异"不误报。

用法：python lint_wiki.py <案件根目录>
"""
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _normalize import norm as _norm  # noqa: E402

ANCHOR_RE = re.compile(r"〔来源:\s*(.+?)：「(.+?)」〕")
WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")
SPLIT_RE = re.compile(r"…+|\.\.\.+")
DATE_RE = re.compile(r"(\d{4})\s*年(?:\s*(\d{1,2})\s*月)?(?:\s*(\d{1,2})\s*日)?")
ALIASES_RE = re.compile(r"aliases:\s*\[(.*?)\]")
CHECK_RE = re.compile(r">\s*\[!check\]\s*(.+)")
_NUM_PUNCT = str.maketrans({"，": ",", "＋": "+", "－": "-", "×": "*", "＝": "="})


def _fragments(snippet: str) -> list[str]:
    return [s.strip() for s in SPLIT_RE.split(snippet) if s.strip()]


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def _load_pages(wiki: Path, root: Path) -> list[tuple[Path, str, str]]:
    """一次性读入所有 wiki 页面：(路径, 相对根的 posix 路径, 正文)。各检查共用，
    免得每个检查各自 rglob+read 一遍。"""
    return [(md, md.relative_to(root).as_posix(), md.read_text(encoding="utf-8"))
            for md in sorted(wiki.rglob("*.md"))]


def _page_names(pages: list[tuple[Path, str, str]]) -> set[str]:
    """所有 wiki 页面的可链接名：文件名（去扩展名）+ frontmatter 声明的别名。"""
    names: set[str] = set()
    for md, _where, text in pages:
        names.add(md.stem)
        m = ALIASES_RE.search(_frontmatter(text))
        if m:
            names.update(a.strip() for a in m.group(1).split(",") if a.strip())
    return names


def _check_anchors(root: Path, pages: list[tuple[Path, str, str]]
                   ) -> tuple[list[str], set[str], int]:
    """返回 (违规列表, 被引用的源文件相对路径集合, 锚点总数)。"""
    cache: dict[Path, str] = {}
    violations: list[str] = []
    cited: set[str] = set()
    total = 0
    for _md, where, text in pages:
        for m in ANCHOR_RE.finditer(text):
            total += 1
            rel, snippet = m.group(1).strip(), m.group(2)
            cited.add(rel)
            src = root / rel
            if not src.is_file():
                violations.append(f"[缺文件] {where}\n          所指来源不存在: {rel}")
                continue
            if src not in cache:
                cache[src] = _norm(src.read_text(encoding="utf-8"))
            body = cache[src]
            pos, missing = 0, None
            for frag in _fragments(snippet):
                nf = _norm(frag)
                idx = body.find(nf, pos)
                if idx < 0:
                    missing = frag
                    break
                pos = idx + len(nf)
            if missing is not None:
                violations.append(
                    f"[片段不符] {where}\n          来源: {rel}\n          找不到片段: 「{missing}」")
    return violations, cited, total


def _check_deadlinks(pages: list[tuple[Path, str, str]], names: set[str]) -> list[str]:
    violations: list[str] = []
    for _md, where, text in pages:
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).split("|")[0].split("#")[0].strip()
            if not target:  # [[#同页标题]]
                continue
            if target not in names:
                violations.append(f"[死链] {where}\n          指向不存在的页面: [[{target}]]")
    return violations


def _check_timeline_order(pages: list[tuple[Path, str, str]]) -> list[str]:
    violations: list[str] = []
    for _md, where, text in pages:
        if "时间线" not in where.split("/"):
            continue
        prev = None
        for line in text.splitlines():
            if not line.lstrip().startswith("-"):
                continue
            m = DATE_RE.search(line)
            if not m:
                continue  # 无可解析日期（如"公司设立时""待核"）→ 跳过
            cur = (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))
            if prev is not None and cur < prev:
                violations.append(
                    f"[时间线乱序] {where}\n          {cur} 出现在 {prev} 之后")
            prev = cur
    return violations


def _check_coverage(root: Path, cited: set[str]) -> list[str]:
    warnings: list[str] = []
    md_dir = root / "_md"
    if not md_dir.is_dir():
        return warnings
    cited_norm = {c.replace("\\", "/") for c in cited}
    for f in sorted(md_dir.rglob("*.md")):
        rel = f.relative_to(root).as_posix()
        if rel not in cited_norm:
            warnings.append(f"[未引用] {rel}")
    return warnings


def _ev(n):  # 受限算术求值（只许 + - * 与数字，绝不 eval）
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult)):
        l, r = _ev(n.left), _ev(n.right)
        return l + r if isinstance(n.op, ast.Add) else (l - r if isinstance(n.op, ast.Sub) else l * r)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
        v = _ev(n.operand)
        return v if isinstance(n.op, ast.UAdd) else -v
    raise ValueError("不允许的表达式")


def _safe_eval(expr: str) -> float:
    return _ev(ast.parse(expr.replace(",", "").strip(), mode="eval").body)


def _check_closures(pages: list[tuple[Path, str, str]]) -> list[str]:
    """校验 `> [!check] a + b == c` 勾稽断言：解析数字、做加减乘、核等式。"""
    violations: list[str] = []
    for _md, where, text in pages:
        for line in text.splitlines():
            m = CHECK_RE.search(line)
            if not m:
                continue
            raw = m.group(1).strip()
            # 取算术前缀（数字/逗号/+-*()/空格/==），其后中文说明自动排除
            m2 = re.match(r"\s*([0-9,\s+\-*().]+==[0-9,\s+\-*().]+)",
                          raw.translate(_NUM_PUNCT))
            if not m2:
                violations.append(f"[勾稽无法解析] {where}\n          {raw}")
                continue
            try:
                left, right = (_safe_eval(p) for p in m2.group(1).split("=="))
            except Exception as e:
                violations.append(f"[勾稽无法解析] {where}\n          {raw}  （{e}）")
                continue
            if abs(left - right) > 1e-6:
                violations.append(
                    f"[勾稽不符] {where}\n          {raw}\n          左={left:g} ≠ 右={right:g}")
    return violations


def scan_case(root: Path) -> tuple[int, list[str], list[str]]:
    """返回 (锚点总数, 违规列表, 警告列表)。纯函数，便于测试。"""
    wiki = root / "wiki"
    if not wiki.is_dir():
        raise FileNotFoundError(f"找不到 {wiki}")
    pages = _load_pages(wiki, root)
    names = _page_names(pages)
    anchor_viol, cited, total = _check_anchors(root, pages)
    violations = anchor_viol
    violations += _check_deadlinks(pages, names)
    violations += _check_timeline_order(pages)
    violations += _check_closures(pages)
    warnings = _check_coverage(root, cited)
    return total, violations, warnings


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 重定向默认 GBK
    except Exception:
        pass
    if len(argv) != 2:
        print("用法：python lint_wiki.py <案件根目录>", file=sys.stderr)
        return 2
    try:
        total, violations, warnings = scan_case(Path(argv[1]))
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2
    print(f"扫描锚点 {total} 个；违规 {len(violations)} 处；警告 {len(warnings)} 处。")
    for v in violations:
        print("  ✗ " + v)
    for w in warnings:
        print("  ! " + w)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
