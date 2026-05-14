#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from newton_fractal_lab.core import basin_summary, iterate_unity, sample_grid
from newton_fractal_lab.render import render_unity_svg
ART = REPO / "art"
REPORTS = REPO / "reports"

CASES = [3, 4, 5]
SAMPLE_POINTS = [
    complex(0.15, 0.15),
    complex(-0.72, 0.34),
    complex(0.58, -0.91),
]


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Unity-family gallery report",
        "",
        "These summaries were generated locally from the same code that produced the SVG gallery.",
        "",
    ]

    for power in CASES:
        output = ART / f"newton-z{power}-minus-1.svg"
        render_unity_svg(power, width=240, height=240, max_iter=40, output=output)
        samples = sample_grid(power, 120, 120, max_iter=40)
        stats = basin_summary(power, 120, 120, samples)

        lines.append(f"## z^{power} - 1")
        lines.append("")
        lines.append(f"- converged points: {stats.converged_points}/{stats.total_points}")
        lines.append(f"- stalled points: {stats.stalled_points}")
        lines.append(f"- mean iterations across the grid: {stats.mean_iterations:.2f}")
        basin_shares = ", ".join(
            f"root {idx}: {count / stats.total_points:.1%}" for idx, count in enumerate(stats.basin_counts)
        )
        lines.append(f"- basin shares: {basin_shares}")
        lines.append("")
        lines.append("Sample starts:")
        for point in SAMPLE_POINTS:
            result = iterate_unity(point, power)
            if result.converged and result.root_index is not None:
                outcome = f"root {result.root_index}"
            elif result.root_index is not None:
                outcome = f"closest to root {result.root_index}, but not within the current tolerance"
            else:
                outcome = "did not settle cleanly"
            lines.append(
                f"- {point.real:+.2f} {point.imag:+.2f}i -> {outcome} in {result.iterations} steps (residual {result.residual:.2e})"
            )
        lines.append("")

    (REPORTS / "unity-family.md").write_text("\n".join(lines) + "\n")
    print("generated gallery and reports")


if __name__ == "__main__":
    main()
