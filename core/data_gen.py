"""四种数据分布生成器（组内分工：算法核心 / 高新杰）

对应需求里的"四种数据分布"：
    随机分布 / 顺序分布（已升序） / 逆序分布（已降序） / 近乎有序分布

统一用 1..n 作为取值，好处是柱状图可以直接按 n 等比缩放，四种分布之间也能公平比较。
"""

from __future__ import annotations

import random
from typing import List, Optional

DISTRIBUTIONS = ("random", "sorted", "reversed", "nearly")
DISTRIBUTION_LABELS = {
    "random": "随机分布",
    "sorted": "顺序分布（已升序）",
    "reversed": "逆序分布（已降序）",
    "nearly": "近乎有序分布",
}


def generate(
    distribution: str = "random",
    n: int = 16,
    seed: Optional[int] = None,
    swap_ratio: float = 0.05,
) -> List[int]:
    """按分布类型生成数组。

    distribution : "random" | "sorted" | "reversed" | "nearly"
    n            : 元素个数
    seed         : 随机种子，给定后可复现（"生成数据"按钮可用固定种子做回归测试）
    swap_ratio   : 仅"近乎有序"用，制造多少比例的乱序（默认 5%）
    """
    if distribution not in DISTRIBUTIONS:
        raise ValueError(f"未知数据分布 {distribution!r}，可选：{DISTRIBUTIONS}")
    if n < 0:
        raise ValueError("n 不能为负数")

    base = list(range(1, n + 1))
    if n < 2:
        return base

    rng = random.Random(seed)

    if distribution == "sorted":
        return base
    if distribution == "reversed":
        return base[::-1]

    if distribution == "random":
        out = base[:]
        rng.shuffle(out)
        return out

    # 近乎有序：在有序数组上做少量相邻交换，制造"看起来基本有序"的输入
    out = base[:]
    swaps = max(1, int(round(n * swap_ratio)))
    for _ in range(swaps):
        i = rng.randrange(0, n - 1)
        out[i], out[i + 1] = out[i + 1], out[i]
    return out


def duplicates(n: int = 16, distinct: int = 3, seed: Optional[int] = None) -> List[int]:
    """大量重复值的数据（单元测试用：重复元素是分区写错时最容易死循环的场景）。"""
    if n < 0:
        raise ValueError("n 不能为负数")
    if distinct < 1:
        raise ValueError("distinct 至少为 1")
    rng = random.Random(seed)
    return [rng.randint(1, distinct) for _ in range(n)]
