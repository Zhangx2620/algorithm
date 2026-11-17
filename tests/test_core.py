"""算法核心单元测试（组内分工：算法核心 自测，QA 可复用）

运行：
    python -m unittest discover -s tests -t . -v
"""

from __future__ import annotations

import unittest

from core import (
    DISTRIBUTIONS,
    PARTITION_SCHEMES,
    PIVOT_STRATEGIES,
    QuickSort,
    duplicates,
    generate,
    quick_sort,
    trace_sort,
)


class TestCorrectness(unittest.TestCase):
    """排序结果必须与 Python 内置排序一致 —— 这是所有其它测试的地基。"""

    def test_all_strategy_combinations(self) -> None:
        sizes = (0, 1, 2, 3, 5, 16, 40, 100)
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                for distribution in DISTRIBUTIONS:
                    for n in sizes:
                        with self.subTest(pivot=pivot, partition=partition, dist=distribution, n=n):
                            data = generate(distribution, n, seed=n * 31 + 7)
                            result = quick_sort(data, pivot=pivot, partition=partition, seed=7)
                            self.assertEqual(result, sorted(data))
                            self.assertEqual(data, generate(distribution, n, seed=n * 31 + 7), "入参不应被修改")

    def test_duplicate_values(self) -> None:
        """大量重复值：分区写错时最容易死循环或丢元素。"""
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                for distinct in (1, 2, 3, 10):
                    for n in (5, 17, 60):
                        with self.subTest(pivot=pivot, partition=partition, distinct=distinct, n=n):
                            data = duplicates(n, distinct, seed=99)
                            self.assertEqual(quick_sort(data, pivot=pivot, partition=partition, seed=3), sorted(data))

    def test_adversarial_patterns(self) -> None:
        """两端极值、锯齿、单个逆序对等边界数据。"""
        cases = [
            [5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5],
            [9, 1, 9, 1, 9, 1],
            [2, 1],
            [1, 3, 2],
            [3, 1, 2, 4, 1, 5, 2],
            list(range(50, 0, -1)),
        ]
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                for data in cases:
                    with self.subTest(pivot=pivot, partition=partition, data=data):
                        self.assertEqual(quick_sort(data, pivot=pivot, partition=partition, seed=1), sorted(data))


class TestTrace(unittest.TestCase):
    """步骤流是界面层的输入，必须自洽、可回放。"""

    def test_counter_matches_last_step(self) -> None:
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                with self.subTest(pivot=pivot, partition=partition):
                    qs = trace_sort(generate("random", 24, seed=5), pivot=pivot, partition=partition, seed=5)
                    self.assertTrue(qs.steps)
                    last = qs.steps[-1]
                    self.assertEqual(last["type"], "end")
                    self.assertEqual(last["comparisons"], qs.comparisons)
                    self.assertEqual(last["swaps"], qs.swaps)

    def test_steps_keep_permutation(self) -> None:
        """任何一个时刻的数组都必须是原数组的一个排列，不能凭空多/少元素。"""
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                with self.subTest(pivot=pivot, partition=partition):
                    data = generate("random", 30, seed=11)
                    qs = trace_sort(data, pivot=pivot, partition=partition, seed=11)
                    for step in qs.steps:
                        self.assertEqual(sorted(step["array"]), sorted(data), f"步骤 {step['type']} 元素总数变了")

    def test_swap_replay(self) -> None:
        """按步骤里的 swap 事件重放，必须复现每一步的快照和最终结果。"""
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                with self.subTest(pivot=pivot, partition=partition):
                    data = generate("random", 26, seed=13)
                    qs = trace_sort(data, pivot=pivot, partition=partition, seed=13)
                    state = list(qs.original)
                    for step in qs.steps:
                        if step["type"] == "swap":
                            i, j = step["i"], step["j"]
                            state[i], state[j] = state[j], state[i]
                            self.assertEqual(step["array"], state, "快照与重放结果不一致")
                    self.assertEqual(state, qs.arr)

    def test_every_index_finalized(self) -> None:
        """place / done 两类事件合起来必须覆盖每个下标，界面才能把柱子全部染成"已就位"。"""
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                with self.subTest(pivot=pivot, partition=partition):
                    qs = trace_sort(generate("random", 21, seed=17), pivot=pivot, partition=partition, seed=17)
                    finalized = {s["index"] for s in qs.steps if s["type"] in ("place", "done")}
                    self.assertEqual(finalized, set(range(21)))

    def test_step_fields(self) -> None:
        qs = trace_sort(generate("random", 12, seed=19), pivot="random", partition="hoare", seed=19)
        kinds = {s["type"] for s in qs.steps}
        self.assertTrue({"start", "range", "pivot", "compare", "swap", "place", "end"} <= kinds)
        for step in qs.steps:
            self.assertIn("message", step)
            self.assertIn("comparisons", step)
            self.assertIn("swaps", step)
            self.assertIsInstance(step["message"], str)
        for step in qs.steps:
            if step["type"] == "compare":
                self.assertIn("i", step)
                self.assertIn("pv", step)
        for step in qs.steps:
            if step["type"] == "swap":
                self.assertIn("i", step)
                self.assertIn("j", step)

    def test_snapshot_off(self) -> None:
        qs = trace_sort(generate("random", 10, seed=23), snapshot=False)
        self.assertTrue(all("array" not in s for s in qs.steps))
        self.assertEqual(qs.array_at(0), qs.arr)


class TestRecursionTree(unittest.TestCase):
    """递归树面板直接用 nodes，链接关系必须正确。"""

    def test_links_and_counters(self) -> None:
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                with self.subTest(pivot=pivot, partition=partition):
                    qs = trace_sort(generate("nearly", 33, seed=29), pivot=pivot, partition=partition, seed=29)
                    self.assertEqual(qs.nodes[0]["parent"], None)
                    self.assertEqual(qs.nodes[0]["side"], "root")
                    self.assertEqual(qs.nodes[0]["depth"], 0)
                    for node in qs.nodes:
                        for side in ("left", "right"):
                            child = node[f"{side}_child"]
                            if child is not None:
                                self.assertEqual(qs.nodes[child]["parent"], node["id"])
                                self.assertEqual(qs.nodes[child]["side"], side)
                                self.assertEqual(qs.nodes[child]["depth"], node["depth"] + 1)
                        self.assertTrue(node["done"], "每个节点都应在划分结束后被结算")

                    # 每个分区自己的比较/交换次数加起来，必须等于总数
                    self.assertEqual(sum(n["comparisons"] for n in qs.nodes), qs.comparisons)
                    self.assertEqual(sum(n["swaps"] for n in qs.nodes), qs.swaps)
                    self.assertEqual(max(n["depth"] for n in qs.nodes), qs.max_depth)

    def test_children_ranges_partition_interval(self) -> None:
        """两种分区都遵循同一约定：左子区间 = [low, k-1]，右子区间 = [k+1, high]，k 是基准落点。"""
        for partition in PARTITION_SCHEMES:
            with self.subTest(partition=partition):
                qs = trace_sort(generate("random", 28, seed=31), pivot="median3", partition=partition, seed=31)
                for node in qs.nodes:
                    if node["size"] <= 1:
                        continue
                    k = node["pivot_index"]
                    self.assertGreaterEqual(k, node["low"])
                    self.assertLessEqual(k, node["high"])
                    left, right = node["left_child"], node["right_child"]
                    if left is not None:
                        self.assertEqual((qs.nodes[left]["low"], qs.nodes[left]["high"]), (node["low"], k - 1))
                    if right is not None:
                        self.assertEqual((qs.nodes[right]["low"], qs.nodes[right]["high"]), (k + 1, node["high"]))


class TestDataGen(unittest.TestCase):
    def test_distributions(self) -> None:
        for n in (0, 1, 2, 16, 100):
            for distribution in DISTRIBUTIONS:
                with self.subTest(dist=distribution, n=n):
                    data = generate(distribution, n, seed=41)
                    self.assertEqual(len(data), n)
                    self.assertEqual(sorted(data), list(range(1, n + 1)), "应为 1..n 的排列")

        n = 40
        self.assertEqual(generate("sorted", n), list(range(1, n + 1)))
        self.assertEqual(generate("reversed", n), list(range(n, 0, -1)))

    def test_nearly_sorted_is_mostly_ordered(self) -> None:
        n = 100
        data = generate("nearly", n, seed=43, swap_ratio=0.05)
        mismatched = sum(1 for idx, value in enumerate(data) if value != idx + 1)
        self.assertLessEqual(mismatched, 2 * max(1, int(round(n * 0.05))), "近乎有序的乱序量不应超过设定比例")
        self.assertNotEqual(data, list(range(1, n + 1)), "应确实存在少量乱序")

    def test_reproducible_with_seed(self) -> None:
        self.assertEqual(generate("random", 20, seed=7), generate("random", 20, seed=7))
        self.assertNotEqual(generate("random", 20, seed=7), generate("random", 20, seed=8))

    def test_invalid_arguments(self) -> None:
        with self.assertRaises(ValueError):
            generate("bogus", 10)
        with self.assertRaises(ValueError):
            generate("random", -1)


class TestOptions(unittest.TestCase):
    def test_unknown_options_rejected(self) -> None:
        with self.assertRaises(ValueError):
            QuickSort([1, 2, 3], pivot="bogus")
        with self.assertRaises(ValueError):
            QuickSort([1, 2, 3], partition="bogus")

    def test_summary_and_flags(self) -> None:
        qs = trace_sort(generate("random", 16, seed=47), pivot="first", partition="lomuto", seed=47)
        summary = qs.summary()
        self.assertEqual(summary["n"], 16)
        self.assertTrue(summary["sorted"])
        self.assertGreaterEqual(summary["elapsed_ms"], 0.0)

    def test_empty_and_single(self) -> None:
        qs = trace_sort([], pivot="median3", partition="hoare")
        self.assertEqual(qs.arr, [])
        self.assertTrue(qs.sorted_ok)
        self.assertEqual(qs.comparisons, 0)
        self.assertEqual(qs.swaps, 0)

        single = trace_sort([42], pivot="first", partition="lomuto")
        self.assertEqual(single.arr, [42])
        self.assertEqual(len(single.nodes), 1)
        self.assertEqual(len(single.steps), 3)  # start + done + end


if __name__ == "__main__":
    unittest.main()
