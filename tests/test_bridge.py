"""适配层（StepDriver）单元测试：确保步骤流能正确驱动 ui_layout 的回调接口。

用 FakeUI 模拟 QuickSortVisual，不依赖 tkinter。
"""

from __future__ import annotations

import unittest

from core import StepDriver, generate, trace_sort, PARTITION_SCHEMES, PIVOT_STRATEGIES


class FakeUI:
    """按 ui_layout.QuickSortVisual 的对外接口写的替身。"""

    def __init__(self) -> None:
        self.states: list[dict] = []
        self.nodes: list[tuple] = []
        self.finish_calls = 0

    def set_sort_state(self, arr, compare=-1, swap=-1, pivot=-1, sorted_set=None, log_msg="") -> None:
        self.states.append(
            {
                "arr": list(arr),
                "compare": compare,
                "swap": swap,
                "pivot": pivot,
                "sorted": set(sorted_set) if sorted_set is not None else set(),
                "log": log_msg,
            }
        )

    def add_tree_node(self, l, pivot, r, parent_id=None) -> int:
        self.nodes.append((l, pivot, r, parent_id))
        return len(self.nodes) - 1

    def finish_sort(self) -> None:
        self.finish_calls += 1


class TestStepDriver(unittest.TestCase):
    def _drive(self, pivot="median3", partition="lomuto", n=18, seed=101):
        ui = FakeUI()
        driver = StepDriver(ui)
        driver.load(generate("random", n, seed=seed), pivot=pivot, partition=partition, seed=seed)
        while driver.step():
            pass
        return ui, driver

    def test_every_step_pushed_exactly_once(self) -> None:
        for pivot in PIVOT_STRATEGIES:
            for partition in PARTITION_SCHEMES:
                with self.subTest(pivot=pivot, partition=partition):
                    ui, driver = self._drive(pivot, partition)
                    self.assertEqual(len(ui.states), len(driver.qs.steps), "每条步骤都应推一次界面状态")
                    self.assertEqual(ui.finish_calls, 1, "结束只通知一次")

    def test_final_state_all_sorted(self) -> None:
        ui, driver = self._drive()
        last = ui.states[-1]
        self.assertEqual(last["sorted"], set(range(len(last["arr"]))))
        self.assertEqual(last["arr"], sorted(last["arr"]))
        self.assertEqual(last["pivot"], -1)
        self.assertEqual(last["compare"], -1)

    def test_rows_match_step_snapshots(self) -> None:
        ui, driver = self._drive()
        for state, step in zip(ui.states, driver.qs.steps):
            self.assertEqual(state["arr"], step["array"], "界面拿到的数组应与快照一致")

    def test_highlights(self) -> None:
        ui, driver = self._drive(partition="lomuto")
        for state, step in zip(ui.states, driver.qs.steps):
            if step["type"] == "compare":
                self.assertEqual(state["compare"], step["i"])
                self.assertEqual(state["pivot"], step["pivot"])
                self.assertEqual(state["swap"], -1)
            elif step["type"] == "swap":
                self.assertEqual(state["swap"], step["i"])
                self.assertEqual(state["compare"], step["j"], "交换的另一个端点用比较高亮标出来")
            elif step["type"] == "pivot":
                self.assertEqual(state["pivot"], step["index"])

    def test_log_messages_are_non_empty(self) -> None:
        ui, _ = self._drive()
        self.assertTrue(all(state["log"] for state in ui.states))

    def test_tree_nodes(self) -> None:
        ui, driver = self._drive(n=20)
        partitions = [node for node in driver.qs.nodes if node["size"] >= 2]
        self.assertEqual(len(ui.nodes), len(partitions))
        self.assertEqual(ui.nodes[0][3], None, "根节点没有父节点")
        for item in ui.nodes:
            self.assertEqual(len(item), 4)
            # 每个节点的区间必须与算法侧某个划分区间一致
            ranges = {(node["low"], node["high"]) for node in partitions}
            self.assertIn((item[0], item[2]), ranges)
            if item[3] is not None:
                self.assertGreaterEqual(item[3], 0)
                self.assertLess(item[3], len(ui.nodes))
        # 父节点必须比子节点先创建，界面连线才不会断
        for idx, item in enumerate(ui.nodes):
            if item[3] is not None:
                self.assertLess(item[3], idx)

    def test_step_after_end_is_noop(self) -> None:
        ui, driver = self._drive()
        before = len(ui.states)
        self.assertFalse(driver.step())
        self.assertEqual(len(ui.states), before)
        self.assertEqual(ui.finish_calls, 1)

    def test_seek_and_reset(self) -> None:
        ui = FakeUI()
        driver = StepDriver(ui)
        driver.load(generate("random", 16, seed=7), pivot="random", partition="hoare", seed=7)
        driver.seek(10)
        self.assertEqual(driver.pos, 10)
        self.assertEqual(len(ui.states), 11)
        driver.seek(driver.total - 1)
        self.assertTrue(driver.finished)
        driver.seek(2)                       # 往回拖：应重放
        self.assertEqual(driver.pos, 2)
        self.assertEqual(len(ui.states[-1]["sorted"]), len(ui.states[-1]["sorted"]))
        driver.reset()
        self.assertEqual(driver.pos, -1)
        self.assertFalse(driver.finished)

    def test_run_to_end(self) -> None:
        ui = FakeUI()
        driver = StepDriver(ui)
        driver.load(generate("sorted", 12, seed=3), pivot="median3", partition="hoare")
        driver.run_to_end()
        self.assertTrue(driver.finished)
        self.assertEqual(ui.states[-1]["arr"], list(range(1, 13)))

    def test_empty_and_single(self) -> None:
        for data in ([], [7]):
            ui = FakeUI()
            driver = StepDriver(ui, data=data)
            while driver.step():
                pass
            self.assertEqual(len(ui.states), len(driver.qs.steps))
            self.assertEqual(ui.finish_calls, 1)


if __name__ == "__main__":
    unittest.main()
