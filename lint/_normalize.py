# -*- coding: utf-8 -*-
"""共享的归一化：只消除格式噪声（空白/换行/全半角标点/千分位逗号/markdown/
表格管道/HTML 标签），保留数字与文字精确。lint 与抽取器共用，避免漂移。

唯一算法在 `norm_with_map`；`norm` 是它丢掉索引映射的薄封装——两者绝不会漂移。"""

_PUNCT = {
    "，": ",", "（": "(", "）": ")", "：": ":", "；": ";",
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "－": "-", "—": "-", "–": "-", "　": "",
}
_DROP_CHARS = set(" \t\r\n,|*#>`~_")


def norm_with_map(s: str) -> tuple[str, list[int]]:
    """返回 (归一化串, 索引映射)，map[i] = 归一化第 i 字符在原串 s 的下标。
    用于把归一化命中位置映射回原文，截取上下文窗口。"""
    out: list[str] = []
    idx: list[int] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "<":  # 跳过成对的 HTML 标签；孤立 '<' 当普通字符处理
            j = s.find(">", i)
            if j != -1:
                i = j + 1
                continue
        c2 = _PUNCT.get(c, c)
        if c2 == "" or c2 in _DROP_CHARS:
            i += 1
            continue
        out.append(c2)
        idx.append(i)
        i += 1
    return "".join(out), idx


def norm(s: str) -> str:
    """归一化字符串（最常用；不需要索引映射时用它）。"""
    return norm_with_map(s)[0]
