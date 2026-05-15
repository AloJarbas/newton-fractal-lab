#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from newton_fractal_lab.core import basin_summary, iterate_unity, iteration_histogram, sample_grid, scan_radius_bands, scan_unity_family
from newton_fractal_lab.render import export_png_from_svg, render_iteration_histograms_svg, render_power_scan_svg, render_radius_scan_svg, render_unity_svg

ART = REPO / "art"
REPORTS = REPO / "reports"

CASES = [3, 4, 5]
SCAN_MIN = 2
SCAN_MAX = 12
RADIUS_POWERS = [3, 6, 9, 12]
HISTOGRAM_POWERS = [3, 6, 9, 12]
SAMPLE_POINTS = [
    complex(0.15, 0.15),
    complex(-0.72, 0.34),
    complex(0.58, -0.91),
]


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    gallery_lines = [
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

        gallery_lines.append(f"## z^{power} - 1")
        gallery_lines.append("")
        gallery_lines.append(f"- converged points: {stats.converged_points}/{stats.total_points}")
        gallery_lines.append(f"- stalled points: {stats.stalled_points}")
        gallery_lines.append(f"- mean iterations across the grid: {stats.mean_iterations:.2f}")
        basin_shares = ", ".join(
            f"root {idx}: {count / stats.total_points:.1%}" for idx, count in enumerate(stats.basin_counts)
        )
        gallery_lines.append(f"- basin shares: {basin_shares}")
        gallery_lines.append("")
        gallery_lines.append("Sample starts:")
        for point in SAMPLE_POINTS:
            result = iterate_unity(point, power)
            if result.converged and result.root_index is not None:
                outcome = f"root {result.root_index}"
            elif result.root_index is not None:
                outcome = f"closest to root {result.root_index}, but not within the current tolerance"
            else:
                outcome = "did not settle cleanly"
            gallery_lines.append(
                f"- {point.real:+.2f} {point.imag:+.2f}i -> {outcome} in {result.iterations} steps (residual {result.residual:.2e})"
            )
        gallery_lines.append("")

    (REPORTS / "unity-family.md").write_text("\n".join(gallery_lines) + "\n")

    scan_rows = scan_unity_family(SCAN_MIN, SCAN_MAX, width=100, height=100, max_iter=40)
    render_power_scan_svg(scan_rows, output=ART / "unity-power-scan.svg")

    scan_lines = [
        "# Unity-family power scan",
        "",
        f"This report tracks `z^n - 1` from `n = {SCAN_MIN}` through `n = {SCAN_MAX}` on the same square grid.",
        "",
        "## What changes as n increases",
        "",
    ]

    steepest = max(scan_rows, key=lambda row: row.mean_iterations)
    weakest = min(scan_rows, key=lambda row: row.converged_fraction)
    widest = max(scan_rows, key=lambda row: row.max_share - row.min_share)

    scan_lines.append(f"- the slowest sampled family here is `z^{steepest.power} - 1`, with mean iteration count {steepest.mean_iterations:.2f}")
    scan_lines.append(f"- the lowest convergence fraction in this scan is `z^{weakest.power} - 1`, with {weakest.converged_fraction:.1%} of points settling within the current tolerance")
    scan_lines.append(f"- the widest basin-share spread in this scan is `z^{widest.power} - 1`, with a min-to-max gap of {(widest.max_share - widest.min_share):.2%}")
    scan_lines.append("")
    scan_lines.append("## Per-power summary")
    scan_lines.append("")

    for row in scan_rows:
        scan_lines.append(f"### z^{row.power} - 1")
        scan_lines.append("")
        scan_lines.append(f"- mean iterations: {row.mean_iterations:.2f}")
        scan_lines.append(f"- converged fraction: {row.converged_fraction:.1%}")
        scan_lines.append(f"- stalled fraction: {row.stalled_fraction:.1%}")
        scan_lines.append(f"- smallest basin share on this grid: {row.min_share:.1%}")
        scan_lines.append(f"- largest basin share on this grid: {row.max_share:.1%}")
        scan_lines.append("")

    profiles = {power: scan_radius_bands(power, width=120, height=120, max_iter=40, bands=12) for power in RADIUS_POWERS}
    render_radius_scan_svg(profiles, output=ART / "critical-radius-scan.svg")

    radius_lines = [
        "# Critical structure and radius scan",
        "",
        "This report asks a narrower question than the gallery: where does the derivative singularity at `z = 0` show up most clearly on the sampled square?",
        "",
        "For `f(z) = z^n - 1`, Newton's update is",
        "",
        "```text",
        "N_n(z) = ((n - 1)/n) z + 1 / (n z^(n - 1))",
        "```",
        "",
        "So the origin is not a root at all. It is the point where the derivative vanishes, and the inverse-power term makes the map violent near the center.",
        "",
        "The radial scan bins starting points by distance from the origin and compares four powers on the same square grid.",
        "",
    ]

    for power in RADIUS_POWERS:
        rows = profiles[power]
        hardest = max(rows, key=lambda row: row.mean_iterations)
        weakest = min(rows, key=lambda row: row.converged_fraction)
        outer = rows[-1]
        radius_lines.append(f"## z^{power} - 1")
        radius_lines.append("")
        radius_lines.append(
            f"- slowest radial band: `{hardest.radius_min:.2f} ≤ |z₀| < {hardest.radius_max:.2f}` with mean iteration count {hardest.mean_iterations:.2f}"
        )
        radius_lines.append(
            f"- weakest convergence band: `{weakest.radius_min:.2f} ≤ |z₀| < {weakest.radius_max:.2f}` with convergence fraction {weakest.converged_fraction:.1%}"
        )
        radius_lines.append(
            f"- outermost band `{outer.radius_min:.2f} ≤ |z₀| < {outer.radius_max:.2f}` still converges at {outer.converged_fraction:.1%} with mean iteration count {outer.mean_iterations:.2f}"
        )
        radius_lines.append("")

    radius_lines.extend(
        [
            "## Reading",
            "",
            "- the center is the trouble spot because `f'(z) = n z^(n-1)` collapses there, so Newton's correction term can explode instead of settling down",
            "- higher powers keep a slow inner region for longer, which is why the mean-iteration profile lifts upward as `n` increases",
            "- the outer square is not uniformly easy, but it is usually much calmer than the central bands on the same iteration budget",
            "",
            "This does not replace a full critical-orbit study. It is a cleaner public bridge between the basin pictures and the algebra behind them.",
            "",
            "Open `art/critical-radius-scan.svg` and `notebooks/critical_structure_unity_family.ipynb` next.",
        ]
    )

    (REPORTS / "critical-structure.md").write_text("\n".join(radius_lines) + "\n")

    histograms = [iteration_histogram(power, width=120, height=120, max_iter=40) for power in HISTOGRAM_POWERS]
    histogram_svg = ART / "slow-convergence-histograms.svg"
    histogram_png = ART / "slow-convergence-histograms.png"
    render_iteration_histograms_svg(histograms, output=histogram_svg)
    export_png_from_svg(histogram_svg, histogram_png, size=1800, dpi=300)

    histogram_lines = [
        "# Slow-convergence histograms",
        "",
        "This report asks a complementary question to the basin gallery: not just where points go, but how much of the sampled square settles fast, late, or not at all under the current iteration budget.",
        "",
        "The figure bins exact convergence counts on the same square grid for several powers in the unity family.",
        "",
        "## Main read",
        "",
    ]

    heaviest_tail = max(histograms, key=lambda row: row.tail_fraction(20))
    weakest_cutoff = max(histograms, key=lambda row: (row.stalled_count + row.unresolved_count) / row.total_points)
    histogram_lines.append(
        f"- the heaviest late tail here is `z^{heaviest_tail.power} - 1`, where {heaviest_tail.tail_fraction(20):.1%} of the sampled square still needs at least 20 steps or misses the cutoff entirely"
    )
    histogram_lines.append(
        f"- the hardest finite-budget case here is `z^{weakest_cutoff.power} - 1`, where {(weakest_cutoff.stalled_count + weakest_cutoff.unresolved_count) / weakest_cutoff.total_points:.1%} of starts are still unresolved at 40 iterations"
    )
    histogram_lines.append(
        "- lower powers still have boundary tails, but the mass sits earlier in the histogram, which is why the panels look tighter and more left-loaded"
    )
    histogram_lines.append("")
    histogram_lines.append("## Per-power tail summary")
    histogram_lines.append("")

    def bucket_fraction(histogram, left, right):
        return sum(histogram.converged_counts[left:right]) / histogram.total_points

    for histogram in histograms:
        unresolved_fraction = (histogram.stalled_count + histogram.unresolved_count) / histogram.total_points
        histogram_lines.append(f"### z^{histogram.power} - 1")
        histogram_lines.append("")
        histogram_lines.append(f"- fast settle (0-4 steps): {bucket_fraction(histogram, 0, 5):.1%}")
        histogram_lines.append(f"- middle settle (5-9 steps): {bucket_fraction(histogram, 5, 10):.1%}")
        histogram_lines.append(f"- slow settle (10-19 steps): {bucket_fraction(histogram, 10, 20):.1%}")
        histogram_lines.append(f"- late tail (20-40 steps): {bucket_fraction(histogram, 20, histogram.max_iter + 1):.1%}")
        histogram_lines.append(f"- unresolved at cutoff: {unresolved_fraction:.1%}")
        histogram_lines.append("")

    histogram_lines.extend(
        [
            "## Reading",
            "",
            "- exact histograms make the boundary problem more concrete: the issue is not just that some pixels look dark, but that a larger share of the square gets pushed into a long iteration tail as the power rises",
            "- the unresolved bar is a reminder that the current cutoff matters; some starts are not truly divergent, they are just too slow for the present budget",
            "- this is still a sampled public summary, not a theorem about every point on the basin boundary",
            "",
            "Open `art/slow-convergence-histograms.svg`, `art/slow-convergence-histograms.png`, and `notebooks/slow_convergence_histograms.ipynb` next.",
        ]
    )

    (REPORTS / "slow-convergence.md").write_text("\n".join(histogram_lines) + "\n")

    (REPORTS / "unity-power-scan.md").write_text("\n".join(scan_lines) + "\n")
    print("generated gallery, scan figures, and reports")


if __name__ == "__main__":
    main()
