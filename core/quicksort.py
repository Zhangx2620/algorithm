"""快速排序算法核心（组内分工：算法核心 / 高新杰）

模块职责
--------
只做两件事：
1. 把数组排好序；
2. 把"排序过程中发生了什么"记录成可逐步回放的步骤流。

本模块不含任何 tkinter 代码。界面层（肖廣桂）只要按 ``steps`` 一条条播放即可；
性能对比表（王义豪）用 ``benchmark.py`` 直接产出。

对外接口
--------
QuickSort(data, pivot=..., partition=..., seed=...)   排序过程对象
QuickSort.sort()                                      真正执行排序
QuickSort.steps                                       步骤流（list[dict]）
QuickSort.nodes                                       递归树节点（list[dict]）
QuickSort.comparisons / QuickSort.swaps               比较次数 / 交换次数
QuickSort.elapsed_ms                                 排序耗时（已扣除记录开销）
quick_sort(data, ...)                                 只取排序结果
trace_sort(data, ...)                                 取完整过程对象

字段含义详见 docs/算法核心接口说明.md。
"""

from __future__ import annotations

import random
import sys
import time
from typing import Any, Dict, List, Optional, Sequence

# ---------------------------------------------------------------- 常量
#: 两种分区方案
PARTITION_SCHEMES = ("lomuto", "hoare")
SCHEME_LABELS = {
    "lomuto": "Lomuto 单指针分区",
    "hoare": "Hoare 双指针分区",
}

#: 基准策略。课程要求"三种基准"，这里给出四种（last 为 first 的对称变体）
PIVOT_STRATEGIES = ("first", "last", "random", "median3")
PIVOT_LABELS = {
    "first": "首元素基准",
    "last": "尾元素基准",
    "random": "随机基准",
    "median3": "三数取中基准",
}


class QuickSort:
    """一次快速排序的完整过程：排序结果 + 步骤流 + 递归树 + 统计。

    参数
    ----
    data : 可比较元素序列（演示程序里是整数）
    pivot : "first" | "last" | "random" | "median3"  基准选择策略
    partition : "lomuto" | "hoare"                   分区方案
    seed : 随机数种子。给定后"随机基准"可完全复现（便于 QA 复现问题）
    record : 是否记录步骤流。False 时只统计次数和耗时（用于性能对比）
    snapshot : 每一步是否附带当时的数组快照。界面直接拿快照重绘，最省事
    """

    def __init__(
        self,
        data: Sequence[Any],
        pivot: str = "first",
        partition: str = "lomuto",
        seed: Optional[int] = None,
        record: bool = True,
        snapshot: bool = True,
    ) -> None:
        if pivot not in PIVOT_STRATEGIES:
            raise ValueError(f"未知基准策略 {pivot!r}，可选：{PIVOT_STRATEGIES}")
        if partition not in PARTITION_SCHEMES:
            raise ValueError(f"未知分区方案 {partition!r}，可选：{PARTITION_SCHEMES}")

        self.pivot = pivot
        self.partition = partition
        self.record = record
        self.snapshot = snapshot

        self.original: List[Any] = list(data)
        self.arr: List[Any] = list(data)
        self.n = len(self.arr)

        # ---- 统计数据 ----
        self.comparisons = 0          # 与基准值的比较次数
        self.swaps = 0                # 真正的元素交换次数（同下标不算）
        self.elapsed_ms = 0.0         # 排序耗时（毫秒，已扣除"记录步骤"的开销）
        self.sorted_ok = False        # 排序后自检是否有序
        self.max_depth = 0            # 最大递归深度（递归树面板可用）

        # ---- 过程记录 ----
        self.steps: List[Dict[str, Any]] = []
        self.nodes: List[Dict[str, Any]] = []
        self._overhead = 0.0          # 记录步骤本身花掉的时间，用于从耗时里扣掉
        self._rng = random.Random(seed)

    # ================================================================ 对外入口
    def sort(self) -> List[Any]:
        """执行排序，返回排序后的数组（原地排序，self.arr 同步更新）。"""
        if self.n == 0:
            self.sorted_ok = True
            if self.record:
                self._emit("end", "数组为空，无需排序")
            return self.arr

        # 有序数据 + 固定基准会退化成 n 层递归，这里放宽递归上限
        need = self.n * 3 + 200
        if sys.getrecursionlimit() < need:
            sys.setrecursionlimit(need)

        t0 = time.perf_counter()
        if self.record:
            self._emit(
                "start",
                "开始排序：共 {n} 个元素，{pivot_label} + {scheme_label}",
                n=self.n,
                pivot_label=PIVOT_LABELS[self.pivot],
                scheme_label=SCHEME_LABELS[self.partition],
            )

        self._quick_sort(0, self.n - 1, 0, None, "root")

        self.elapsed_ms = max(0.0, (time.perf_counter() - t0) * 1000.0 - self._overhead * 1000.0)
        self.sorted_ok = self.is_sorted()

        if self.record:
            self._emit(
                "end",
                "排序完成：比较 {c} 次，交换 {s} 次，用时 {t:.2f} ms",
                c=self.comparisons,
                s=self.swaps,
                t=self.elapsed_ms,
            )
        return self.arr

    def is_sorted(self) -> bool:
        """检查当前数组是否升序。"""
        return all(self.arr[i] <= self.arr[i + 1] for i in range(self.n - 1))

    def summary(self) -> Dict[str, Any]:
        """一行汇总，界面底部状态栏/测试报告可直接用。"""
        return {
            "n": self.n,
            "pivot": self.pivot,
            "partition": self.partition,
            "comparisons": self.comparisons,
            "swaps": self.swaps,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "steps": len(self.steps),
            "depth": self.max_depth,
            "sorted": self.sorted_ok,
        }

    def array_at(self, step_index: int) -> List[Any]:
        """取第 step_index 步（含）之后的数组状态；用于界面拖动进度条回看。"""
        if not self.steps:
            return list(self.arr)
        step = self.steps[max(0, min(step_index, len(self.steps) - 1))]
        snapshot = step.get("array")
        return list(snapshot) if snapshot is not None else list(self.arr)

    # ================================================================ 递归主体
    def _quick_sort(self, low: int, high: int, depth: int, parent_id: Optional[int], side: str) -> None:
        """快速排序递归主体：对 arr[low..high] 做划分，再递归处理左右两段。

        所有递归调用都会在 self.nodes 里登记一个节点，供界面画递归树。
        """
        node_id = self._new_node(low, high, depth, parent_id, side)
        c0, s0 = self.comparisons, self.swaps

        # 空区间（防御性分支，正常调用不会进来）
        if low > high:
            self._close_node(node_id, c0, s0, None, None)
            return

        # 递归出口：区间只剩一个元素，它已经在最终位置
        if low == high:
            if self.record:
                self._emit(
                    "done",
                    "区间只剩 1 个元素，arr[{index}] = {value} 已就位",
                    index=low,
                    value=self.arr[low],
                    low=low,
                    high=high,
                    depth=depth,
                    node=node_id,
                )
            self._close_node(node_id, c0, s0, low, self.arr[low])
            return

        if self.record:
            self._emit(
                "range",
                "处理区间 [{low}, {high}]：共 {size} 个元素，递归深度 {depth}",
                low=low,
                high=high,
                size=high - low + 1,
                depth=depth,
                node=node_id,
            )

        # ---- 划分 ----
        if self.partition == "lomuto":
            k = self._partition_lomuto(low, high, depth, node_id)
        else:
            k = self._partition_hoare(low, high, depth, node_id)

        # 两种方案结束时语义一致：arr[k] 就是基准，左段均不大于它、右段均不小于它
        if self.record:
            self._emit(
                "place",
                "基准 {value} 归位到下标 {k}：左侧均不大于它，右侧均不小于它",
                k=k,
                value=self.arr[k],
                index=k,
                low=low,
                high=high,
                depth=depth,
                node=node_id,
            )

        self._close_node(node_id, c0, s0, k, self.arr[k])

        # ---- 递归左右两段（空段不递归，避免递归树里出现空节点）----
        if k - 1 >= low:
            self._quick_sort(low, k - 1, depth + 1, node_id, "left")
        if k + 1 <= high:
            self._quick_sort(k + 1, high, depth + 1, node_id, "right")

    # ================================================================ 分区方案
    def _partition_lomuto(self, low: int, high: int, depth: int, node_id: int) -> int:
        """Lomuto 单指针分区：基准先挪到区间末尾，指针 store 记录"小于区"的边界。

        返回基准元素最终所在的下标。
        """
        arr = self.arr
        p = self._choose_pivot(low, high)
        pivot_value = arr[p]
        if self.record:
            self._emit(
                "pivot",
                "选取基准：arr[{index}] = {value}（{strategy}）",
                index=p,
                value=pivot_value,
                strategy=PIVOT_LABELS[self.pivot],
                low=low,
                high=high,
                depth=depth,
                node=node_id,
            )

        if p != high:
            self._swap(p, high, "把基准元素挪到区间末尾", pivot=high, low=low, high=high, depth=depth, node=node_id)

        store = low  # store 及其左边都小于基准
        for i in range(low, high):
            if self._cmp(i, pivot_value, "<", pivot=high, low=low, high=high, depth=depth, node=node_id):
                if store != i:
                    self._swap(store, i, "该元素小于基准，换到左侧小于区", pivot=high, low=low, high=high, depth=depth, node=node_id)
                store += 1

        self._swap(store, high, "基准归位", pivot=store, low=low, high=high, depth=depth, node=node_id)
        return store

    def _partition_hoare(self, low: int, high: int, depth: int, node_id: int) -> int:
        """Hoare 双指针分区：基准挪到区间左端当哨兵，i 从左往右找"不小于基准"的，
        j 从右往左找"不大于基准"的，两者互换；扫描结束后把基准换到分界点。

        返回基准元素最终所在的下标（与 Lomuto 语义一致，递归时左右两段都跳过它）。
        """
        arr = self.arr
        p = self._choose_pivot(low, high)
        pivot_value = arr[p]
        if self.record:
            self._emit(
                "pivot",
                "选取基准：arr[{index}] = {value}（{strategy}）",
                index=p,
                value=pivot_value,
                strategy=PIVOT_LABELS[self.pivot],
                low=low,
                high=high,
                depth=depth,
                node=node_id,
            )

        if p != low:
            self._swap(p, low, "把基准元素挪到区间左端（充当哨兵）", pivot=low, low=low, high=high, depth=depth, node=node_id)

        i, j = low + 1, high
        while True:
            # i 向右扫描，直到遇到不小于基准的元素（或到达右端）
            while i <= high and self._cmp(i, pivot_value, "<", pivot=low, low=low, high=high, depth=depth, node=node_id):
                i += 1
            # j 向左扫描，直到遇到不大于基准的元素（或到达左端基准处）
            while j > low and self._cmp(j, pivot_value, ">", pivot=low, low=low, high=high, depth=depth, node=node_id):
                j -= 1

            if i > j:
                break
            self._swap(i, j, "左边比基准大的与右边比基准小的互换位置", pivot=low, low=low, high=high, depth=depth, node=node_id)
            i += 1
            j -= 1

        # 扫描结束时 arr[low..j] 都不大于基准、arr[j+1..high] 都不小于基准，
        # 把左端的基准换到 j，基准即落在最终位置（与 Lomuto 的收尾语义对齐）
        self._swap(low, j, "基准归位到分界点", pivot=j, low=low, high=high, depth=depth, node=node_id)
        return j

    # ================================================================ 基准选择
    def _choose_pivot(self, low: int, high: int) -> int:
        """三种基准策略的入口（"尾元素"是"首元素"的对称变体，一并提供）。

        基准选择时的比较不计入 comparisons，也不产生步骤
        —— 这样"比较次数"统计的是与基准值的比较，语义更干净。
        """
        if self.pivot == "first":
            return low
        if self.pivot == "last":
            return high
        if self.pivot == "random":
            return self._rng.randint(low, high)

        # 三数取中：取 low / mid / high 三者数值居中的那个下标
        mid = (low + high) // 2
        x, y, z = self.arr[low], self.arr[mid], self.arr[high]
        if (x <= y <= z) or (z <= y <= x):
            return mid
        if (y <= x <= z) or (z <= x <= y):
            return low
        return high

    # ================================================================ 内部工具
    def _cmp(self, idx: int, pivot_value: Any, op: str, **fields: Any) -> bool:
        """与基准值比较一次（计数 + 记录），op 为 '<' 或 '>'，返回比较结果。"""
        self.comparisons += 1
        value = self.arr[idx]
        result = value < pivot_value if op == "<" else value > pivot_value
        if self.record:
            if op == "<":
                relation = "小于基准" if result else "不小于基准"
            else:
                relation = "大于基准" if result else "不大于基准"
            self._emit(
                "compare",
                "比较 arr[{i}] = {vi} 与基准 {pv}：{rel}",
                i=idx,
                vi=value,
                pv=pivot_value,
                rel=relation,
                op=op,
                **fields,
            )
        return result

    def _swap(self, i: int, j: int, reason: str, **fields: Any) -> None:
        """交换两个元素（同下标视为无效交换，不计数也不记录）。"""
        if i == j:
            return
        arr = self.arr
        vi, vj = arr[i], arr[j]
        arr[i], arr[j] = vj, vi
        self.swaps += 1
        if self.record:
            self._emit(
                "swap",
                "交换 arr[{i}] = {a} 与 arr[{j}] = {b}：{reason}",
                i=i,
                j=j,
                a=vi,
                b=vj,
                reason=reason,
                **fields,
            )

    def _new_node(self, low: int, high: int, depth: int, parent_id: Optional[int], side: str) -> int:
        """登记一个递归节点，并挂到父节点对应的一侧。"""
        node = {
            "id": len(self.nodes),
            "parent": parent_id,
            "side": side,
            "low": low,
            "high": high,
            "size": high - low + 1 if high >= low else 0,
            "depth": depth,
            "pivot_index": None,
            "pivot_value": None,
            "left_child": None,
            "right_child": None,
            "scheme": self.partition,
            "comparisons": 0,
            "swaps": 0,
            "done": False,
        }
        self.nodes.append(node)
        if parent_id is not None:
            self.nodes[parent_id][f"{side}_child"] = node["id"]
        if depth > self.max_depth:
            self.max_depth = depth
        return node["id"]

    def _close_node(self, node_id: int, c0: int, s0: int, pivot_index: Optional[int], pivot_value: Any) -> None:
        """节点结算：记录本次划分用掉的比较/交换次数、基准落点。"""
        node = self.nodes[node_id]
        node["comparisons"] = self.comparisons - c0
        node["swaps"] = self.swaps - s0
        node["pivot_index"] = pivot_index
        node["pivot_value"] = pivot_value
        node["done"] = True

    def _emit(self, kind: str, tmpl: Optional[str] = None, **fields: Any) -> None:
        """追加一条步骤。tmpl 里的占位符与 fields 的键一一对应。

        这里对字符串格式化做了延迟：record=False 时连格式化都不做，
        保证性能对比实验的耗时不被"拼日志字符串"污染。
        """
        if not self.record:
            return
        t0 = time.perf_counter()
        step: Dict[str, Any] = {
            "type": kind,
            "message": tmpl.format(**fields) if tmpl else "",
            "comparisons": self.comparisons,
            "swaps": self.swaps,
        }
        step.update(fields)
        if self.snapshot:
            step["array"] = self.arr.copy()
        self.steps.append(step)
        self._overhead += time.perf_counter() - t0


# ==================================================================== 便捷函数
def quick_sort(
    data: Sequence[Any],
    pivot: str = "first",
    partition: str = "lomuto",
    seed: Optional[int] = None,
) -> List[Any]:
    """只要结果、不要过程：返回新的已排序列表（不改动入参）。"""
    return QuickSort(list(data), pivot=pivot, partition=partition, seed=seed, record=False, snapshot=False).sort()


def trace_sort(
    data: Sequence[Any],
    pivot: str = "first",
    partition: str = "lomuto",
    seed: Optional[int] = None,
    snapshot: bool = True,
) -> QuickSort:
    """要完整过程：返回排好序的 QuickSort 对象（可读 steps / nodes / 统计）。"""
    qs = QuickSort(data, pivot=pivot, partition=partition, seed=seed, record=True, snapshot=snapshot)
    qs.sort()
    return qs
