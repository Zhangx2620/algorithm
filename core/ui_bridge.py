"""步骤流 → 界面回调的适配层（组内分工：算法核心 / 高新杰）

为什么需要它
------------
算法层产出的是"步骤流"（``qs.steps``），而界面同学（肖廣桂）在 ``ui_layout.py``
里留的是回调式接口：

    set_sort_state(arr, compare, swap, pivot, sorted_set, log_msg)
    add_tree_node(l, pivot, r, parent_id) -> node_id
    finish_sort()

本模块负责把两者逐条翻译过去，界面层只需要在 ``step_sort()`` 里调 ``driver.step()``，
不用自己解析步骤字段。

用法
----
    from core import StepDriver
    from ui_layout import QuickSortVisual

    driver = StepDriver(app)                     # app 是 QuickSortVisual 实例
    driver.load(data, pivot="median3", partition="lomuto")   # 点"生成数据"时调用

    def step_sort(self):                         # 界面里原本的占位方法
        driver.step()                            # 返回 False 表示全部播完

    # 自动播放循环：每帧 step() 一次，delay 由速度滑块控制；
    # 想回看就 driver.seek(i)，想重来就 driver.reset()
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from .quicksort import QuickSort, trace_sort

#: 界面给"交换"只留了一个高亮位，另一个端点借用"比较"高亮，两个柱子就都能变色
_SWAP_SIDE_AS_COMPARE = True


class StepDriver:
    """把 QuickSort 的步骤流驱动到一个 UI 对象（鸭子类型，不依赖 tkinter）。"""

    def __init__(
        self,
        ui: Any,
        data: Optional[Sequence[Any]] = None,
        pivot: str = "median3",
        partition: str = "lomuto",
        seed: Optional[int] = None,
    ) -> None:
        self.ui = ui
        self.qs: Optional[QuickSort] = None
        self.pos = -1              # 已播放到第几步（-1 表示还没开始）
        self._sorted: set[int] = set()
        self._node_map: dict[int, int] = {}   # 算法节点 id -> 界面节点 id

        if data is not None:
            self.load(data, pivot=pivot, partition=partition, seed=seed)

    # ---------------------------------------------------------------- 装载
    def load(
        self,
        data: Sequence[Any],
        pivot: str = "median3",
        partition: str = "lomuto",
        seed: Optional[int] = None,
    ) -> QuickSort:
        """用一组新数据重新生成步骤流（"生成数据/重置"按钮调它）。"""
        self.qs = trace_sort(data, pivot=pivot, partition=partition, seed=seed)
        self.pos = -1
        self._sorted = set()
        self._node_map = {}
        return self.qs

    def reset(self) -> None:
        """回到第一帧之前，清空已就位集合与递归树（配合 ui.reset_all 使用）。"""
        self.pos = -1
        self._sorted = set()
        self._node_map = {}

    # ---------------------------------------------------------------- 播放
    @property
    def total(self) -> int:
        return len(self.qs.steps) if self.qs else 0

    @property
    def finished(self) -> bool:
        return self.total > 0 and self.pos >= self.total - 1

    def step(self) -> bool:
        """前进一步并推给界面；返回 False 表示已经播完（不重复推 end）。"""
        if not self.qs or self.finished:
            return False
        self.pos += 1
        self._apply(self.qs.steps[self.pos])
        return True

    def run_to_end(self) -> None:
        """不动画、直接推到结束（用于"跳过动画，看结果"）。"""
        while self.step():
            pass

    def seek(self, index: int) -> None:
        """跳到第 index 步（拖动进度条回看）。会按顺序重放，保证已就位集合正确。"""
        index = max(-1, min(index, self.total - 1))
        if index < self.pos:
            self.reset()
        while self.pos < index:
            self.step()

    # ---------------------------------------------------------------- 翻译
    def _apply(self, step: dict[str, Any]) -> None:
        kind = step["type"]
        arr = step["array"]
        sorted_set = set(self._sorted)
        self._sync_counters(step)

        if kind == "start":
            self.ui.set_sort_state(arr, compare=-1, swap=-1, pivot=-1, sorted_set=set(), log_msg=step["message"])

        elif kind == "range":
            self.ui.set_sort_state(arr, compare=-1, swap=-1, pivot=-1, sorted_set=sorted_set, log_msg=step["message"])

        elif kind == "pivot":
            self.ui.set_sort_state(arr, compare=-1, swap=-1, pivot=step["index"], sorted_set=sorted_set, log_msg=step["message"])

        elif kind == "compare":
            self.ui.set_sort_state(
                arr,
                compare=step["i"],
                swap=-1,
                pivot=step.get("pivot", -1),
                sorted_set=sorted_set,
                log_msg=step["message"],
            )

        elif kind == "swap":
            # 界面只有一个"交换"高亮位：交换的两个柱子分别用 swap / compare 标色
            other = step["j"] if _SWAP_SIDE_AS_COMPARE else -1
            self.ui.set_sort_state(
                arr,
                compare=other,
                swap=step["i"],
                pivot=step.get("pivot", -1),
                sorted_set=sorted_set,
                log_msg=step["message"],
            )

        elif kind in ("place", "done"):
            self._sorted.add(step["index"])
            self.ui.set_sort_state(
                arr,
                compare=-1,
                swap=-1,
                pivot=-1,
                sorted_set=set(self._sorted),
                log_msg=step["message"],
            )
            if kind == "place":
                self._add_tree_node(step["node"])

        elif kind == "end":
            self.ui.set_sort_state(
                arr,
                compare=-1,
                swap=-1,
                pivot=-1,
                sorted_set=set(range(len(arr))),
                log_msg=step["message"],
            )
            self.ui.finish_sort()

    def _sync_counters(self, step: dict[str, Any]) -> None:
        """把累计比较/交换次数推给界面的统计面板（ui_layout 里是 compare_cnt / swap_cnt）。

        界面对象没有这两个属性时自动跳过，所以驱动别的界面实现也不会报错。
        """
        if not hasattr(self.ui, "compare_cnt"):
            return
        self.ui.compare_cnt = step["comparisons"]
        self.ui.swap_cnt = step["swaps"]
        update = getattr(self.ui, "update_stat", None)
        if callable(update):
            update()

    def _add_tree_node(self, node_id: int) -> None:
        """把"基准归位"这一步的区间做成递归树节点。

        单元素区间不建节点，否则递归树会变成 n 个叶子的大杂烩；
        深度优先的步骤顺序保证父节点一定先于子节点创建。
        """
        if not self.qs:
            return
        node = self.qs.nodes[node_id]
        if node["size"] <= 1:
            return
        parent_ui = None
        if node["parent"] is not None:
            parent_ui = self._node_map.get(node["parent"])
        self._node_map[node_id] = self.ui.add_tree_node(
            node["low"], node["pivot_index"], node["high"], parent_ui
        )
