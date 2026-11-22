"""命令行自测 / 演示前核对（组内分工：算法核心 / 高新杰）

这不是交付界面，只是给算法本体做"肉眼可查"的验收工具，方便和 UC/QA 对拍：

    python -m core.demo                                  # 默认随机数据跑一遍
    python -m core.demo --n 12 --dist nearly --pivot median3 --partition hoare
    python -m core.demo --n 20 --show-steps 30           # 逐条打印步骤日志
"""

from __future__ import annotations

import argparse
import sys

from .data_gen import DISTRIBUTIONS, DISTRIBUTION_LABELS, generate
from .quicksort import PIVOT_LABELS, PIVOT_STRATEGIES, SCHEME_LABELS, PARTITION_SCHEMES, trace_sort


def _bars(values: list[int], width: int = 60) -> str:
    """把数组画成一行 ASCII 柱状条，用于命令行快速核对。"""
    if not values:
        return "（空）"
    peak = max(abs(v) for v in values) or 1
    cells = []
    for v in values:
        h = max(1, int(round(abs(v) / peak * 6)))
        cells.append("█" * h)
    return " | ".join(cells)


def _tree_lines(qs) -> list[str]:
    """把递归树按缩进打印出来，方便核对划分是否正确。"""
    lines = []

    def visit(node_id: int, indent: int) -> None:
        node = qs.nodes[node_id]
        tag = "" if node["pivot_index"] is None else f"，基准落点 {node['pivot_index']}"
        lines.append(
            f"{'  ' * indent}#{node['id']} [{node['low']}, {node['high']}] "
            f"共{node['size']}个{tag}（比较 {node['comparisons']}，交换 {node['swaps']}）"
        )
        for child in (node["left_child"], node["right_child"]):
            if child is not None:
                visit(child, indent + 1)

    if qs.nodes:
        visit(0, 0)
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="快速排序算法核心自测")
    parser.add_argument("--n", type=int, default=16, help="数组长度（默认 16）")
    parser.add_argument("--dist", choices=DISTRIBUTIONS, default="random", help="数据分布")
    parser.add_argument("--pivot", choices=PIVOT_STRATEGIES, default="median3", help="基准策略")
    parser.add_argument("--partition", choices=PARTITION_SCHEMES, default="lomuto", help="分区方案")
    parser.add_argument("--seed", type=int, default=20261116, help="随机种子，保证可复现")
    parser.add_argument("--show-steps", type=int, default=0, help="打印前多少条步骤日志（0 表示不打印）")
    args = parser.parse_args(argv)

    if args.n < 0:
        print("n 不能为负数", file=sys.stderr)
        return 2

    data = generate(args.dist, args.n, seed=args.seed)
    qs = trace_sort(data, pivot=args.pivot, partition=args.partition, seed=args.seed)

    print(f"数据分布：{DISTRIBUTION_LABELS[args.dist]}    基准：{PIVOT_LABELS[args.pivot]}    分区：{SCHEME_LABELS[args.partition]}")
    print(f"原始数组：{data}")
    print(f"排序结果：{qs.arr}")
    print(f"是否有序：{'是' if qs.sorted_ok else '否  ← 有 bug'}")
    print(f"比较次数：{qs.comparisons}    交换次数：{qs.swaps}    耗时：{qs.elapsed_ms:.3f} ms")
    print(f"步骤条数：{len(qs.steps)}    递归节点：{len(qs.nodes)}    最大递归深度：{qs.max_depth}")
    print()
    print("柱状图（ASCII）：")
    print(_bars(qs.arr))
    print()
    print("递归树：")
    for line in _tree_lines(qs):
        print(line)

    if args.show_steps > 0:
        print()
        print(f"前 {args.show_steps} 条步骤日志：")
        for idx, step in enumerate(qs.steps[: args.show_steps]):
            print(f"[{idx:>4}] {step['type']:<8} 比较 {step['comparisons']:>4} 交换 {step['swaps']:>4} | {step['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
