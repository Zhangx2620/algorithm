"""基准策略 × 分区方案 × 数据分布 的对比实验（组内分工：算法核心 / 高新杰）

直接为技术文档里的"统计对比表"产出数据（Markdown + CSV）：

    python -m core.benchmark                          # 默认 n=200/500/1000，写到 docs/
    python -m core.benchmark --sizes 500 2000 --repeat 5

计时口径：record=False，只统计比较/交换次数与纯排序耗时，不含任何日志/绘制的开销。
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from pathlib import Path
from typing import Any

from .data_gen import DISTRIBUTIONS, DISTRIBUTION_LABELS, generate
from .quicksort import PIVOT_LABELS, PIVOT_STRATEGIES, SCHEME_LABELS, PARTITION_SCHEMES, QuickSort


def measure(n: int, distribution: str, pivot: str, partition: str, seed: int, repeat: int) -> dict[str, Any]:
    """同一组参数跑 repeat 次，取耗时的中位数，返回一行结果。"""
    times: list[float] = []
    comparisons = swaps = 0
    ok = True
    for _ in range(repeat):
        data = generate(distribution, n, seed=seed)
        qs = QuickSort(data, pivot=pivot, partition=partition, seed=seed, record=False, snapshot=False)
        t0 = time.perf_counter()
        qs.sort()
        times.append((time.perf_counter() - t0) * 1000.0)
        comparisons, swaps = qs.comparisons, qs.swaps
        ok = ok and qs.sorted_ok
    return {
        "n": n,
        "distribution": distribution,
        "pivot": pivot,
        "partition": partition,
        "comparisons": comparisons,
        "swaps": swaps,
        "elapsed_ms": statistics.median(times),
        "sorted": ok,
    }


def run(sizes: list[int], repeat: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for n in sizes:
        for partition in PARTITION_SCHEMES:
            for pivot in PIVOT_STRATEGIES:
                for distribution in DISTRIBUTIONS:
                    rows.append(measure(n, distribution, pivot, partition, seed, repeat))
    return rows


def _fmt_ms(value: float) -> str:
    return f"{value:.2f}" if value >= 0.01 else "<0.01"


def to_markdown(rows: list[dict[str, Any]], sizes: list[int]) -> str:
    """Markdown 报告：先给对比明细，再给"不同规模耗时"纵横表。"""
    lines: list[str] = []
    lines.append("# 快速排序：基准策略 / 分区方案 / 数据分布 对比数据")
    lines.append("")
    lines.append("> 由 `python -m core.benchmark` 自动生成，供技术文档的统计对比表引用。")
    lines.append("> 计时口径：关闭步骤记录，仅统计比较/交换次数与纯排序耗时；每组参数取多次运行的中位数。")
    lines.append("")

    for n in sizes:
        lines.append(f"## n = {n} 明细")
        lines.append("")
        lines.append("| 数据分布 | 基准策略 | 分区方案 | 比较次数 | 交换次数 | 耗时(ms) | 排序正确 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for row in rows:
            if row["n"] != n:
                continue
            lines.append(
                f"| {DISTRIBUTION_LABELS[row['distribution']]} | {PIVOT_LABELS[row['pivot']]} | "
                f"{SCHEME_LABELS[row['partition']]} | {row['comparisons']} | {row['swaps']} | "
                f"{_fmt_ms(row['elapsed_ms'])} | {'✔' if row['sorted'] else '✘'} |"
            )
        lines.append("")

    # 纵横表：横轴是数组规模，只取 Lomuto，便于看出"固定基准在有序数据上的退化"
    lines.append("## 耗时随规模变化（Lomuto 分区，单位 ms）")
    lines.append("")
    header = "| 数据分布 | 基准策略 | " + " | ".join(f"n={n}" for n in sizes) + " |"
    lines.append(header)
    lines.append("| --- | --- | " + " | ".join("---" for _ in sizes) + " |")
    for distribution in DISTRIBUTIONS:
        for pivot in PIVOT_STRATEGIES:
            cells = []
            for n in sizes:
                value = next(
                    (
                        r["elapsed_ms"]
                        for r in rows
                        if r["n"] == n and r["partition"] == "lomuto" and r["pivot"] == pivot and r["distribution"] == distribution
                    ),
                    None,
                )
                cells.append(_fmt_ms(value) if value is not None else "-")
            lines.append(f"| {DISTRIBUTION_LABELS[distribution]} | {PIVOT_LABELS[pivot]} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def to_csv(rows: list[dict[str, Any]]) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["n", "distribution", "pivot", "partition", "comparisons", "swaps", "elapsed_ms", "sorted"])
    for row in rows:
        writer.writerow(
            [
                row["n"],
                DISTRIBUTION_LABELS[row["distribution"]],
                PIVOT_LABELS[row["pivot"]],
                SCHEME_LABELS[row["partition"]],
                row["comparisons"],
                row["swaps"],
                f"{row['elapsed_ms']:.4f}",
                "OK" if row["sorted"] else "BAD",
            ]
        )
    return buffer.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="快速排序对比实验")
    parser.add_argument("--sizes", type=int, nargs="+", default=[200, 500, 1000], help="数组规模，可传多个")
    parser.add_argument("--repeat", type=int, default=3, help="每组参数重复次数（取中位数）")
    parser.add_argument("--seed", type=int, default=20261116, help="随机种子")
    parser.add_argument("--out-dir", default="docs", help="输出目录")
    args = parser.parse_args(argv)

    rows = run(args.sizes, max(1, args.repeat), args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "基准策略对比数据.md"
    csv_path = out_dir / "基准策略对比数据.csv"
    md_path.write_text(to_markdown(rows, args.sizes), encoding="utf-8")
    csv_path.write_text(to_csv(rows), encoding="utf-8")

    bad = [r for r in rows if not r["sorted"]]
    print(f"共 {len(rows)} 组实验，结果已写入：")
    print(f"  {md_path}")
    print(f"  {csv_path}")
    print(f"排序全部正确：{'是' if not bad else '否，存在 ' + str(len(bad)) + ' 组异常'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
