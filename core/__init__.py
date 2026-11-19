"""算法核心包（组内分工：算法核心 / 高新杰）。

界面层推荐这样用（适配 ui_layout.py 的回调接口）:

    from core import StepDriver

    driver = StepDriver(app)
    driver.load(generate("random", 16, seed=7), pivot="median3", partition="hoare")
    driver.step()        # 单步 / 自动播放每帧调一次

只要步骤流、自己渲染时:

    from core import trace_sort, generate

    qs = trace_sort(generate("random", 16, seed=7), pivot="median3", partition="hoare")
    for step in qs.steps:
        ...
"""

from .quicksort import (
    PARTITION_SCHEMES,
    PIVOT_LABELS,
    PIVOT_STRATEGIES,
    SCHEME_LABELS,
    QuickSort,
    quick_sort,
    trace_sort,
)
from .data_gen import (
    DISTRIBUTIONS,
    DISTRIBUTION_LABELS,
    duplicates,
    generate,
)
from .ui_bridge import StepDriver

__all__ = [
    "QuickSort",
    "quick_sort",
    "trace_sort",
    "StepDriver",
    "PIVOT_STRATEGIES",
    "PIVOT_LABELS",
    "PARTITION_SCHEMES",
    "SCHEME_LABELS",
    "generate",
    "duplicates",
    "DISTRIBUTIONS",
    "DISTRIBUTION_LABELS",
]
