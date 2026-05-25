#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from newton_fractal_lab.core import basin_summary, compare_radius_budgets, iterate_unity, iteration_histogram, sample_grid, scan_late_tail_tiles, scan_radius_bands, scan_unity_family
from newton_fractal_lab.cubic import asymmetric_cubic, compare_cubic_budget_persistence, cubic_basin_summary, cubic_critical_points, sample_cubic_grid, scan_critical_distance, scan_cubic_late_tail_tiles, split_critical_asymmetric_cubic, unity_cubic
from newton_fractal_lab.render import export_png_from_svg, render_asymmetric_cubic_contrast_svg, render_cubic_budget_persistence_svg, render_cubic_comparison_svg, render_cubic_persistence_atlas_svg, render_iteration_histograms_svg, render_late_tail_heatmap_svg, render_power_scan_svg, render_radius_budget_comparison_svg, render_radius_scan_svg, render_unity_svg

ART = REPO / "art"
REPORTS = REPO / "reports"

CASES = [3, 4, 5]
SCAN_MIN = 2
SCAN_MAX = 12
RADIUS_POWERS = [3, 6, 9, 12]
HISTOGRAM_POWERS = [3, 6, 9, 12]
BUDGET_COMPARISON_POWERS = [3, 6, 9, 12]
BUDGET_LOW = 40
BUDGET_HIGH = 80
LATE_TAIL_POWERS = [3, 6, 9, 12]
LATE_TAIL_THRESHOLD = 20
LATE_TAIL_TILES = 12
CUBIC_GRID = 180
CUBIC_BANDS = 8
CUBIC_LATE_THRESHOLD = 10
CUBIC_BUDGET_LOW = 8
CUBIC_BUDGET_HIGH = 24
CUBIC_BUDGET_TILES = 12
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

    budget_rows = {
        power: compare_radius_budgets(
            power,
            low_budget=BUDGET_LOW,
            high_budget=BUDGET_HIGH,
            width=120,
            height=120,
            bands=12,
        )
        for power in BUDGET_COMPARISON_POWERS
    }
    budget_svg = ART / "iteration-budget-radius-comparison.svg"
    budget_png = ART / "iteration-budget-radius-comparison.png"
    render_radius_budget_comparison_svg(budget_rows, output=budget_svg)
    export_png_from_svg(budget_svg, budget_png, size=2000, dpi=300)

    budget_lines = [
        "# Iteration-budget versus geometry",
        "",
        f"This report compares the same radial profiles at `{BUDGET_LOW}` and `{BUDGET_HIGH}` Newton steps.",
        "The point is not just to say that higher powers are harder. It is to separate two different effects:",
        "",
        f"- starts that were only cutoff-limited at `{BUDGET_LOW}` and recover once the budget rises",
        f"- starts that are still stubborn even at `{BUDGET_HIGH}`, which is the more geometric part of the story",
        "",
        "The radial view keeps the origin in frame, because the derivative singularity near `z = 0` is where the family first gets violent.",
        "",
        "## Main read",
        "",
    ]

    def weighted_recovered_fraction(rows):
        total = sum(row.sample_count for row in rows)
        return sum(row.sample_count * row.recovered_fraction for row in rows) / total

    most_recovered = max(budget_rows.items(), key=lambda item: weighted_recovered_fraction(item[1]))
    most_stubborn = min(
        budget_rows.items(),
        key=lambda item: min(row.high_converged_fraction for row in item[1]),
    )
    budget_lines.append(
        f"- the biggest whole-grid recovery here is `z^{most_recovered[0]} - 1`, where {weighted_recovered_fraction(most_recovered[1]):.1%} of sampled starts move from unresolved at `{BUDGET_LOW}` to converged by `{BUDGET_HIGH}`"
    )
    budget_lines.append(
        f"- the most stubborn high-budget family here is `z^{most_stubborn[0]} - 1`, whose weakest radial band still converges only {min(row.high_converged_fraction for row in most_stubborn[1]):.1%} of the time even at `{BUDGET_HIGH}` steps"
    )
    budget_lines.append(
        "- lower powers flatten much earlier, which is why `z^3 - 1` barely moves in the recovery panel while the higher-power inner bands still climb"
    )
    budget_lines.append("")
    budget_lines.append("## Per-power summary")
    budget_lines.append("")

    for power in BUDGET_COMPARISON_POWERS:
        rows = budget_rows[power]
        strongest = max(rows, key=lambda row: row.recovered_fraction)
        weakest_high = min(rows, key=lambda row: row.high_converged_fraction)
        budget_lines.append(f"### z^{power} - 1")
        budget_lines.append("")
        recovered = weighted_recovered_fraction(rows)
        if recovered > 0.0005:
            budget_lines.append(f"- recovered across the whole sampled square: {recovered:.1%}")
            budget_lines.append(
                f"- strongest recovery band: `{strongest.radius_min:.2f} ≤ |z₀| < {strongest.radius_max:.2f}` gains {strongest.recovered_fraction:.1%} more converged starts when the budget rises from `{BUDGET_LOW}` to `{BUDGET_HIGH}`"
            )
        else:
            budget_lines.append(f"- recovered across the whole sampled square: effectively none at this budget pair")
            budget_lines.append(
                f"- strongest recovery band: none worth calling out; the `{BUDGET_LOW}`-step cutoff was already enough for this sampled family"
            )
        budget_lines.append(
            f"- weakest band even at `{BUDGET_HIGH}`: `{weakest_high.radius_min:.2f} ≤ |z₀| < {weakest_high.radius_max:.2f}` with convergence fraction {weakest_high.high_converged_fraction:.1%}"
        )
        budget_lines.append("")

    budget_lines.extend(
        [
            "## Reading",
            "",
            f"- the bottom panel is the key: it marks bands where the `{BUDGET_LOW}`-step cutoff was hiding genuinely recoverable starts",
            f"- if a band still looks weak at `{BUDGET_HIGH}`, that is harder to blame on the cutoff alone and easier to treat as actual basin-boundary geometry",
            "- the higher-power families keep both effects alive at once: some inner bands recover a lot, but some outer or mid-radius bands are still not especially clean even after the budget doubles",
            "",
            "Open `art/iteration-budget-radius-comparison.svg`, `art/iteration-budget-radius-comparison.png`, and the older critical-structure and slow-tail notebooks next.",
        ]
    )

    (REPORTS / "iteration-budget-comparison.md").write_text("\n".join(budget_lines) + "\n")

    late_tail_rows = {
        power: scan_late_tail_tiles(
            power,
            width=120,
            height=120,
            max_iter=40,
            late_threshold=LATE_TAIL_THRESHOLD,
            tile_cols=LATE_TAIL_TILES,
            tile_rows=LATE_TAIL_TILES,
        )
        for power in LATE_TAIL_POWERS
    }
    late_tail_svg = ART / "late-tail-spatial-map.svg"
    late_tail_png = ART / "late-tail-spatial-map.png"
    render_late_tail_heatmap_svg(
        late_tail_rows,
        output=late_tail_svg,
        late_threshold=LATE_TAIL_THRESHOLD,
        max_iter=40,
    )
    export_png_from_svg(late_tail_svg, late_tail_png, size=2200, dpi=300)

    with (ART / "late-tail-spatial-map.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "power",
                "tile_x",
                "tile_y",
                "x_min",
                "x_max",
                "y_min",
                "y_max",
                "sample_count",
                "mean_iterations",
                "late_fraction",
                "unresolved_fraction",
            ],
        )
        writer.writeheader()
        for rows in late_tail_rows.values():
            for row in rows:
                writer.writerow(
                    {
                        "power": row.power,
                        "tile_x": row.tile_x,
                        "tile_y": row.tile_y,
                        "x_min": row.x_min,
                        "x_max": row.x_max,
                        "y_min": row.y_min,
                        "y_max": row.y_max,
                        "sample_count": row.sample_count,
                        "mean_iterations": row.mean_iterations,
                        "late_fraction": row.late_fraction,
                        "unresolved_fraction": row.unresolved_fraction,
                    }
                )

    late_tail_lines = [
        "# Late-tail spatial map",
        "",
        f"This report keeps the earlier 20-step late-tail cutoff from the histogram pass, but stops collapsing everything onto one axis.",
        "The question is local now: where on the sampled square do those slow starts actually live?",
        "",
        f"Each panel bins the same square into `{LATE_TAIL_TILES} × {LATE_TAIL_TILES}` tiles and marks the share of starts that either need at least `{LATE_TAIL_THRESHOLD}` Newton steps or fail the 40-step cutoff.",
        "",
        "## Main read",
        "",
    ]

    for power in LATE_TAIL_POWERS:
        rows = late_tail_rows[power]
        hottest = max(rows, key=lambda row: row.late_fraction)
        grid_late = sum(row.sample_count * row.late_fraction for row in rows) / sum(row.sample_count for row in rows)
        center_rows = sorted(rows, key=lambda row: abs(row.x_mid) + abs(row.y_mid))[:4]
        center_late = sum(row.late_fraction for row in center_rows) / len(center_rows)
        if power == LATE_TAIL_POWERS[0]:
            late_tail_lines.append(
                f"- `z^{power} - 1` still keeps most of its slow starts on thin boundary filaments: the hottest tile reaches only {hottest.late_fraction:.1%}, and the center four tiles average {center_late:.1%}"
            )
        else:
            late_tail_lines.append(
                f"- `z^{power} - 1` has already grown a real center halo: the hottest tile `{hottest.x_min:+.2f} ≤ Re(z₀) < {hottest.x_max:+.2f}`, `{hottest.y_min:+.2f} ≤ Im(z₀) < {hottest.y_max:+.2f}` is at {hottest.late_fraction:.1%}, and the center four tiles average {center_late:.1%}"
            )
        late_tail_lines.append(f"- whole-grid late fraction for `z^{power} - 1`: {grid_late:.1%}")
    late_tail_lines.extend(
        [
            "",
            "## Why the map earns its place",
            "",
            "- the histogram pass said how much late tail existed, but not whether it sat in a center block or in thin off-axis filaments",
            "- the radius scan said the center matters more at higher powers, but it still averaged away direction and spoke structure",
            "- this map is the missing bridge: low powers still look boundary-dominated, while higher powers visibly turn the origin neighborhood into a full finite-budget trap instead of a mere thin band",
            "",
            "That is the useful new fact. The slow region does not just get bigger. Its shape changes.",
            "",
            "Open `art/late-tail-spatial-map.svg`, `art/late-tail-spatial-map.png`, and `notebooks/late_tail_spatial_map.ipynb` next.",
        ]
    )

    (REPORTS / "late-tail-spatial-map.md").write_text("\n".join(late_tail_lines) + "\n")

    unity = unity_cubic()
    asymmetric = asymmetric_cubic()
    unity_samples = sample_cubic_grid(unity, CUBIC_GRID, CUBIC_GRID, max_iter=40)
    asymmetric_samples = sample_cubic_grid(asymmetric, CUBIC_GRID, CUBIC_GRID, max_iter=40)
    unity_stats = cubic_basin_summary(unity, CUBIC_GRID, CUBIC_GRID, unity_samples)
    asymmetric_stats = cubic_basin_summary(asymmetric, CUBIC_GRID, CUBIC_GRID, asymmetric_samples)
    unity_rows = scan_critical_distance(unity, width=CUBIC_GRID, height=CUBIC_GRID, max_iter=40, bands=CUBIC_BANDS, late_threshold=CUBIC_LATE_THRESHOLD)
    asymmetric_rows = scan_critical_distance(asymmetric, width=CUBIC_GRID, height=CUBIC_GRID, max_iter=40, bands=CUBIC_BANDS, late_threshold=CUBIC_LATE_THRESHOLD)
    cubic_svg = ART / "asymmetric-cubic-critical-set-comparison.svg"
    cubic_png = ART / "asymmetric-cubic-critical-set-comparison.png"
    render_cubic_comparison_svg(
        unity,
        unity_stats,
        unity_samples,
        unity_rows,
        asymmetric,
        asymmetric_stats,
        asymmetric_samples,
        asymmetric_rows,
        output=cubic_svg,
    )
    export_png_from_svg(cubic_svg, cubic_png, size=2200, dpi=300)

    with (ART / "asymmetric-cubic-critical-set-comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "polynomial",
                "band_index",
                "distance_min",
                "distance_max",
                "sample_count",
                "mean_iterations",
                "late_fraction",
                "dominant_share",
                "share_root_0",
                "share_root_1",
                "share_root_2",
            ],
        )
        writer.writeheader()
        for row in unity_rows + asymmetric_rows:
            writer.writerow(
                {
                    "polynomial": row.polynomial_slug,
                    "band_index": row.band_index,
                    "distance_min": row.distance_min,
                    "distance_max": row.distance_max,
                    "sample_count": row.sample_count,
                    "mean_iterations": row.mean_iterations,
                    "late_fraction": row.late_fraction,
                    "dominant_share": row.dominant_share,
                    "share_root_0": row.basin_shares[0],
                    "share_root_1": row.basin_shares[1],
                    "share_root_2": row.basin_shares[2],
                }
            )

    unity_critical = cubic_critical_points(unity)
    asymmetric_critical = cubic_critical_points(asymmetric)
    strongest_asym = max(asymmetric_rows, key=lambda row: row.dominant_share)
    hottest_unity = max(unity_rows, key=lambda row: row.late_fraction)
    cubic_lines = [
        "# Breaking the cubic symmetry",
        "",
        "This report adds one carefully chosen asymmetric cubic beside the original `z^n - 1` family.",
        "The point is not to turn the repo into a generic root-finder zoo. The point is to show what changes first when the clean rotational symmetry disappears.",
        "",
        "## The two cubics",
        "",
        "### Unity cubic",
        "",
        "```text",
        "p_u(z) = z^3 - 1",
        "```",
        "",
        f"- roots: {unity.roots[0].real:+.3f} {unity.roots[0].imag:+.3f}i, {unity.roots[1].real:+.3f} {unity.roots[1].imag:+.3f}i, {unity.roots[2].real:+.3f} {unity.roots[2].imag:+.3f}i",
        f"- critical points: {unity_critical[0].real:+.3f} {unity_critical[0].imag:+.3f}i and {unity_critical[1].real:+.3f} {unity_critical[1].imag:+.3f}i",
        f"- basin shares on the sampled square: {unity_stats.basin_shares[0]:.1%}, {unity_stats.basin_shares[1]:.1%}, {unity_stats.basin_shares[2]:.1%}",
        "",
        "### Asymmetric cubic",
        "",
        "```text",
        "p_a(z) = (z - 1)(z - (-0.9 + 1.05i))(z - (-0.15 - 0.25i))",
        "```",
        "",
        f"- expanded coefficients: z^3 + ({asymmetric.coefficients[1].real:+.3f} {asymmetric.coefficients[1].imag:+.3f}i) z^2 + ({asymmetric.coefficients[2].real:+.3f} {asymmetric.coefficients[2].imag:+.3f}i) z + ({asymmetric.coefficients[3].real:+.3f} {asymmetric.coefficients[3].imag:+.3f}i)",
        f"- critical points: {asymmetric_critical[0].real:+.3f} {asymmetric_critical[0].imag:+.3f}i and {asymmetric_critical[1].real:+.3f} {asymmetric_critical[1].imag:+.3f}i",
        f"- basin shares on the sampled square: {asymmetric_stats.basin_shares[0]:.1%}, {asymmetric_stats.basin_shares[1]:.1%}, {asymmetric_stats.basin_shares[2]:.1%}",
        "",
        "## Main read",
        "",
        f"- the unity cubic keeps the classical democratic split: its largest basin share on the sampled square is only {max(unity_stats.basin_shares):.1%}",
        f"- the asymmetric cubic breaks that immediately: one root now owns {max(asymmetric_stats.basin_shares):.1%} of the same square",
        f"- the hottest unity band is the nearest-critical band, where {hottest_unity.late_fraction:.1%} of starts still need at least {CUBIC_LATE_THRESHOLD} steps",
        f"- the asymmetric cubic no longer concentrates its whole late tail in one center halo, but its strongest band skew still reaches a dominant-share value of {strongest_asym.dominant_share:.1%}",
        "",
        "## Why the comparison matters",
        "",
        "The unity family let the origin stand in for the critical set because the cubic has one repeated critical point there.",
        "Once symmetry breaks, that shortcut stops working.",
        "The hard geometry is better organized by distance to the nearest critical point, and the basin shares stop hovering near one third each.",
        "",
        "That is the real upgrade here.",
        "The repo is no longer only a study of the roots-of-unity family. It now has one bounded asymmetric lane that shows which parts of the old reading were specific to symmetry and which ones survive after the symmetry is gone.",
        "",
        "Open `art/asymmetric-cubic-critical-set-comparison.svg`, `art/asymmetric-cubic-critical-set-comparison.png`, and `notebooks/asymmetric_cubic_critical_set.ipynb` next.",
    ]
    (REPORTS / "asymmetric-cubic.md").write_text("\n".join(cubic_lines) + "\n")

    split_critical = split_critical_asymmetric_cubic()
    split_samples = sample_cubic_grid(split_critical, CUBIC_GRID, CUBIC_GRID, max_iter=40)
    split_stats = cubic_basin_summary(split_critical, CUBIC_GRID, CUBIC_GRID, split_samples)
    split_rows = scan_critical_distance(
        split_critical,
        width=CUBIC_GRID,
        height=CUBIC_GRID,
        max_iter=40,
        bands=CUBIC_BANDS,
        late_threshold=CUBIC_LATE_THRESHOLD,
    )

    asym_contrast_svg = ART / "asymmetric-cubic-geometry-contrast.svg"
    asym_contrast_png = ART / "asymmetric-cubic-geometry-contrast.png"
    render_asymmetric_cubic_contrast_svg(
        asymmetric,
        asymmetric_stats,
        asymmetric_samples,
        asymmetric_rows,
        split_critical,
        split_stats,
        split_samples,
        split_rows,
        output=asym_contrast_svg,
    )
    export_png_from_svg(asym_contrast_svg, asym_contrast_png, size=2200, dpi=300)

    with (ART / "asymmetric-cubic-geometry-contrast.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "polynomial",
                "band_index",
                "distance_min",
                "distance_max",
                "sample_count",
                "mean_iterations",
                "late_fraction",
                "dominant_share",
                "share_root_0",
                "share_root_1",
                "share_root_2",
            ],
        )
        writer.writeheader()
        for row in asymmetric_rows + split_rows:
            writer.writerow(
                {
                    "polynomial": row.polynomial_slug,
                    "band_index": row.band_index,
                    "distance_min": row.distance_min,
                    "distance_max": row.distance_max,
                    "sample_count": row.sample_count,
                    "mean_iterations": row.mean_iterations,
                    "late_fraction": row.late_fraction,
                    "dominant_share": row.dominant_share,
                    "share_root_0": row.basin_shares[0],
                    "share_root_1": row.basin_shares[1],
                    "share_root_2": row.basin_shares[2],
                }
            )

    split_critical_points = cubic_critical_points(split_critical)
    hottest_split = max(split_rows, key=lambda row: row.late_fraction)
    strongest_split = max(split_rows, key=lambda row: row.dominant_share)
    asym_contrast_lines = [
        "# Asymmetric cubic geometry contrast",
        "",
        "This sidecar keeps the repo honest about the next loophole.",
        "",
        "One asymmetric cubic was enough to show that the unity-family symmetry was not universal.",
        "It was not enough to claim that symmetry breaking always produces the same kind of Newton geometry.",
        "",
        "This pass compares the repo's existing asymmetric cubic against one second asymmetric cubic chosen for a genuinely different critical-point layout.",
        "",
        "## The new cubic",
        "",
        "```text",
        "p_s(z) = (z - 1)(z - (-0.35 + 0.92i))(z - (-0.30 - 0.88i))",
        "```",
        "",
        f"- expanded coefficients: z^3 + ({split_critical.coefficients[1].real:+.3f} {split_critical.coefficients[1].imag:+.3f}i) z^2 + ({split_critical.coefficients[2].real:+.3f} {split_critical.coefficients[2].imag:+.3f}i) z + ({split_critical.coefficients[3].real:+.3f} {split_critical.coefficients[3].imag:+.3f}i)",
        f"- critical points: {split_critical_points[0].real:+.3f} {split_critical_points[0].imag:+.3f}i and {split_critical_points[1].real:+.3f} {split_critical_points[1].imag:+.3f}i",
        f"- basin shares on the sampled square: {split_stats.basin_shares[0]:.1%}, {split_stats.basin_shares[1]:.1%}, {split_stats.basin_shares[2]:.1%}",
        "",
        "## Main read",
        "",
        f"- the existing asymmetric cubic still becomes a winner-take-most square: its largest basin share is {max(asymmetric_stats.basin_shares):.1%}",
        f"- the split-critical cubic does not: its largest basin share is only {max(split_stats.basin_shares):.1%}, so the sampled square stays much closer to a three-way fight",
        f"- the existing asymmetric cubic cools its nearest-critical band down to {asymmetric_rows[0].late_fraction:.1%} late-tail share at this budget",
        f"- the split-critical cubic keeps that same nearest-critical band far hotter at {split_rows[0].late_fraction:.1%}",
        f"- even away from the center, the split-critical cubic never lets one root own much more than {strongest_split.dominant_share:.1%} of a band, while the existing asymmetric cubic reaches {max(row.dominant_share for row in asymmetric_rows):.1%}",
        "",
        "## Why this earns a second asymmetric lane",
        "",
        "The first asymmetric cubic taught one good lesson: broken symmetry can turn a clean one-third split into a heavily skewed contest.",
        "",
        "The new cubic teaches a different one.",
        "",
        "Broken symmetry does not have to collapse into one dominant basin and a cooled center. If the critical points stay split near the middle of the square, the near-critical tension can remain hot while the basin shares stay comparatively balanced.",
        "",
        f"That is the real upgrade here. The hottest near-critical band in the new cubic is {hottest_split.late_fraction:.1%}, not because the repo changed the budget or the window, but because the critical geometry itself stayed competitive.",
        "",
        "Open `art/asymmetric-cubic-geometry-contrast.svg`, `art/asymmetric-cubic-geometry-contrast.png`, `art/asymmetric-cubic-geometry-contrast.csv`, and `notebooks/asymmetric_cubic_geometry_contrast.ipynb` next.",
    ]
    (REPORTS / "asymmetric-cubic-geometry-contrast.md").write_text("\n".join(asym_contrast_lines) + "\n")

    unity_low_tiles = scan_cubic_late_tail_tiles(
        unity,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_LOW,
        late_threshold=CUBIC_LATE_THRESHOLD,
        tile_cols=CUBIC_BUDGET_TILES,
        tile_rows=CUBIC_BUDGET_TILES,
    )
    unity_high_tiles = scan_cubic_late_tail_tiles(
        unity,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_HIGH,
        late_threshold=CUBIC_LATE_THRESHOLD,
        tile_cols=CUBIC_BUDGET_TILES,
        tile_rows=CUBIC_BUDGET_TILES,
    )
    asymmetric_low_tiles = scan_cubic_late_tail_tiles(
        asymmetric,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_LOW,
        late_threshold=CUBIC_LATE_THRESHOLD,
        tile_cols=CUBIC_BUDGET_TILES,
        tile_rows=CUBIC_BUDGET_TILES,
    )
    asymmetric_high_tiles = scan_cubic_late_tail_tiles(
        asymmetric,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_HIGH,
        late_threshold=CUBIC_LATE_THRESHOLD,
        tile_cols=CUBIC_BUDGET_TILES,
        tile_rows=CUBIC_BUDGET_TILES,
    )
    unity_low_budget_rows = scan_critical_distance(
        unity,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_LOW,
        bands=CUBIC_BANDS,
        late_threshold=CUBIC_LATE_THRESHOLD,
        include_unresolved_in_late=True,
    )
    unity_high_budget_rows = scan_critical_distance(
        unity,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_HIGH,
        bands=CUBIC_BANDS,
        late_threshold=CUBIC_LATE_THRESHOLD,
        include_unresolved_in_late=True,
    )
    asymmetric_low_budget_rows = scan_critical_distance(
        asymmetric,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_LOW,
        bands=CUBIC_BANDS,
        late_threshold=CUBIC_LATE_THRESHOLD,
        include_unresolved_in_late=True,
    )
    asymmetric_high_budget_rows = scan_critical_distance(
        asymmetric,
        width=120,
        height=120,
        max_iter=CUBIC_BUDGET_HIGH,
        bands=CUBIC_BANDS,
        late_threshold=CUBIC_LATE_THRESHOLD,
        include_unresolved_in_late=True,
    )

    cubic_budget_svg = ART / "cubic-budget-persistence.svg"
    cubic_budget_png = ART / "cubic-budget-persistence.png"
    render_cubic_budget_persistence_svg(
        unity_low_tiles=unity_low_tiles,
        unity_high_tiles=unity_high_tiles,
        asymmetric_low_tiles=asymmetric_low_tiles,
        asymmetric_high_tiles=asymmetric_high_tiles,
        unity_low_rows=unity_low_budget_rows,
        unity_high_rows=unity_high_budget_rows,
        asymmetric_low_rows=asymmetric_low_budget_rows,
        asymmetric_high_rows=asymmetric_high_budget_rows,
        low_budget=CUBIC_BUDGET_LOW,
        high_budget=CUBIC_BUDGET_HIGH,
        late_threshold=CUBIC_LATE_THRESHOLD,
        output=cubic_budget_svg,
    )
    export_png_from_svg(cubic_budget_svg, cubic_budget_png, size=2200, dpi=300)

    with (ART / "cubic-budget-persistence.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "polynomial",
                "budget",
                "tile_x",
                "tile_y",
                "x_min",
                "x_max",
                "y_min",
                "y_max",
                "sample_count",
                "mean_iterations",
                "late_fraction",
                "unresolved_fraction",
            ],
        )
        writer.writeheader()
        for row in unity_low_tiles + unity_high_tiles + asymmetric_low_tiles + asymmetric_high_tiles:
            writer.writerow(
                {
                    "polynomial": row.polynomial_slug,
                    "budget": row.budget,
                    "tile_x": row.tile_x,
                    "tile_y": row.tile_y,
                    "x_min": row.x_min,
                    "x_max": row.x_max,
                    "y_min": row.y_min,
                    "y_max": row.y_max,
                    "sample_count": row.sample_count,
                    "mean_iterations": row.mean_iterations,
                    "late_fraction": row.late_fraction,
                    "unresolved_fraction": row.unresolved_fraction,
                }
            )

    def summarize_tiles(rows):
        total = sum(row.sample_count for row in rows)
        grid_late = sum(row.sample_count * row.late_fraction for row in rows) / total
        center_rows = sorted(rows, key=lambda row: abs(row.x_mid) + abs(row.y_mid))[:4]
        center_late = sum(row.late_fraction for row in center_rows) / len(center_rows)
        unresolved = sum(row.sample_count * row.unresolved_fraction for row in rows) / total
        return grid_late, center_late, unresolved

    unity_low_grid, unity_low_center, unity_low_unresolved = summarize_tiles(unity_low_tiles)
    unity_high_grid, unity_high_center, unity_high_unresolved = summarize_tiles(unity_high_tiles)
    asymmetric_low_grid, asymmetric_low_center, asymmetric_low_unresolved = summarize_tiles(asymmetric_low_tiles)
    asymmetric_high_grid, asymmetric_high_center, asymmetric_high_unresolved = summarize_tiles(asymmetric_high_tiles)
    unity_core_low = unity_low_budget_rows[0]
    unity_core_high = unity_high_budget_rows[0]
    asym_core_low = asymmetric_low_budget_rows[0]
    asym_core_high = asymmetric_high_budget_rows[0]
    cubic_budget_lines = [
        "# Cubic budget persistence",
        "",
        f"This pass keeps the same two cubics but changes the Newton cutoff from `{CUBIC_BUDGET_LOW}` steps to `{CUBIC_BUDGET_HIGH}` steps.",
        "The narrow question is the useful one: how much of the old drama was just a tight cutoff, and how much of it survives as a real slow region once the budget rises?",
        "",
        "## Main read",
        "",
        f"- the unity cubic center stays hot even after the budget rises: the center four tiles only cool from `{unity_low_center:.1%}` to `{unity_high_center:.1%}` late-tail share",
        f"- the asymmetric cubic cools much harder over the same jump: the center four tiles fall from `{asymmetric_low_center:.1%}` to `{asymmetric_high_center:.1%}`",
        f"- unresolved starts explain part of the low-budget picture, especially for the unity cubic: its unresolved share drops from `{unity_low_unresolved:.1%}` to `{unity_high_unresolved:.1%}`",
        f"- but the repeated center critical point still leaves a persistent slow core: the nearest-critical unity band stays at `{unity_core_high.late_fraction:.1%}` tail share even at `{CUBIC_BUDGET_HIGH}` steps, versus `{asym_core_high.late_fraction:.1%}` for the asymmetric cubic",
        "",
        "## Why this matters",
        "",
        "The earlier asymmetric-cubic comparison showed that broken symmetry changes basin shares and critical-point geometry.",
        "This follow-up asks the next honest question: was the hotter unity core only a low-budget artifact?",
        "",
        "The answer is no.",
        "",
        f"At `{CUBIC_BUDGET_LOW}` steps both cubics still mix real slow geometry with plain cutoff trouble. Once the cutoff rises to `{CUBIC_BUDGET_HIGH}`, most of the asymmetric-core drama cools away, but the unity cubic keeps a much fatter slow center. That is the bounded persistence effect this sidecar adds.",
        "",
        "## Summary table",
        "",
        f"- unity cubic, {CUBIC_BUDGET_LOW} steps: grid late `{unity_low_grid:.1%}`, center four tiles `{unity_low_center:.1%}`, unresolved `{unity_low_unresolved:.1%}`",
        f"- unity cubic, {CUBIC_BUDGET_HIGH} steps: grid late `{unity_high_grid:.1%}`, center four tiles `{unity_high_center:.1%}`, unresolved `{unity_high_unresolved:.1%}`",
        f"- asymmetric cubic, {CUBIC_BUDGET_LOW} steps: grid late `{asymmetric_low_grid:.1%}`, center four tiles `{asymmetric_low_center:.1%}`, unresolved `{asymmetric_low_unresolved:.1%}`",
        f"- asymmetric cubic, {CUBIC_BUDGET_HIGH} steps: grid late `{asymmetric_high_grid:.1%}`, center four tiles `{asymmetric_high_center:.1%}`, unresolved `{asymmetric_high_unresolved:.1%}`",
        "",
        "## Read the figure",
        "",
        f"- top row: low-budget tail-or-cutoff map at `{CUBIC_BUDGET_LOW}` steps",
        f"- bottom row: the same map after the cutoff rises to `{CUBIC_BUDGET_HIGH}` steps",
        f"- right-side charts: critical-distance tail share with unresolved starts counted as part of the low-budget tail story",
        "",
        "Open `art/cubic-budget-persistence.svg`, `art/cubic-budget-persistence.png`, `art/cubic-budget-persistence.csv`, and `notebooks/cubic_budget_persistence.ipynb` next.",
    ]
    (REPORTS / "cubic-budget-persistence.md").write_text("\n".join(cubic_budget_lines) + "\n")

    cubic_persistence_rows = compare_cubic_budget_persistence(
        [unity, asymmetric, split_critical],
        width=120,
        height=120,
        low_budget=CUBIC_BUDGET_LOW,
        high_budget=CUBIC_BUDGET_HIGH,
        late_threshold=CUBIC_LATE_THRESHOLD,
        tile_cols=CUBIC_BUDGET_TILES,
        tile_rows=CUBIC_BUDGET_TILES,
        bands=CUBIC_BANDS,
    )
    cubic_persistence_svg = ART / "cubic-persistence-atlas.svg"
    cubic_persistence_png = ART / "cubic-persistence-atlas.png"
    low_tiles_by_slug = {
        unity.slug: unity_low_tiles,
        asymmetric.slug: asymmetric_low_tiles,
        split_critical.slug: scan_cubic_late_tail_tiles(
            split_critical,
            width=120,
            height=120,
            max_iter=CUBIC_BUDGET_LOW,
            late_threshold=CUBIC_LATE_THRESHOLD,
            tile_cols=CUBIC_BUDGET_TILES,
            tile_rows=CUBIC_BUDGET_TILES,
        ),
    }
    high_tiles_by_slug = {
        unity.slug: unity_high_tiles,
        asymmetric.slug: asymmetric_high_tiles,
        split_critical.slug: scan_cubic_late_tail_tiles(
            split_critical,
            width=120,
            height=120,
            max_iter=CUBIC_BUDGET_HIGH,
            late_threshold=CUBIC_LATE_THRESHOLD,
            tile_cols=CUBIC_BUDGET_TILES,
            tile_rows=CUBIC_BUDGET_TILES,
        ),
    }
    render_cubic_persistence_atlas_svg(
        low_tiles_by_slug=low_tiles_by_slug,
        high_tiles_by_slug=high_tiles_by_slug,
        comparison_rows=cubic_persistence_rows,
        low_budget=CUBIC_BUDGET_LOW,
        high_budget=CUBIC_BUDGET_HIGH,
        late_threshold=CUBIC_LATE_THRESHOLD,
        output=cubic_persistence_svg,
    )
    export_png_from_svg(cubic_persistence_svg, cubic_persistence_png, size=2200, dpi=300)

    with (ART / "cubic-persistence-atlas.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "polynomial",
                "low_budget",
                "high_budget",
                "low_grid_late",
                "high_grid_late",
                "low_center_late",
                "high_center_late",
                "low_unresolved_fraction",
                "high_unresolved_fraction",
                "low_inner_band_late",
                "high_inner_band_late",
                "center_retained_fraction",
                "inner_band_retained_fraction",
            ],
        )
        writer.writeheader()
        for row in cubic_persistence_rows:
            writer.writerow(
                {
                    "polynomial": row.polynomial_slug,
                    "low_budget": row.low_budget,
                    "high_budget": row.high_budget,
                    "low_grid_late": row.low_grid_late,
                    "high_grid_late": row.high_grid_late,
                    "low_center_late": row.low_center_late,
                    "high_center_late": row.high_center_late,
                    "low_unresolved_fraction": row.low_unresolved_fraction,
                    "high_unresolved_fraction": row.high_unresolved_fraction,
                    "low_inner_band_late": row.low_inner_band_late,
                    "high_inner_band_late": row.high_inner_band_late,
                    "center_retained_fraction": row.center_retained_fraction,
                    "inner_band_retained_fraction": row.inner_band_retained_fraction,
                }
            )

    persistence_by_slug = {row.polynomial_slug: row for row in cubic_persistence_rows}
    unity_persistence = persistence_by_slug[unity.slug]
    asym_persistence = persistence_by_slug[asymmetric.slug]
    split_persistence = persistence_by_slug[split_critical.slug]
    cubic_persistence_lines = [
        "# Three cubic persistence atlas",
        "",
        f"This fast pass keeps the old cubic-budget question but stops pretending there were only two asymmetric outcomes worth checking.",
        f"The cutoff still rises from `{CUBIC_BUDGET_LOW}` to `{CUBIC_BUDGET_HIGH}` steps. The new question is where the split-critical cubic lands between the repeated-center unity cubic and the winner-take-most asymmetric cubic.",
        "",
        "## Main read",
        "",
        f"- the unity cubic still keeps the hottest surviving center: `{unity_persistence.high_center_late:.1%}` late-tail share in the center four tiles at `{CUBIC_BUDGET_HIGH}` steps",
        f"- the old asymmetric cubic still cools the hardest: its center stays at `{asym_persistence.high_center_late:.1%}`, and its inner-band retention falls to `{asym_persistence.inner_band_retained_fraction:.1%}` of the low-budget value",
        f"- the split-critical cubic really does land in the middle lane: its center cools from `{split_persistence.low_center_late:.1%}` to `{split_persistence.high_center_late:.1%}`, and its inner-band retention stays at `{split_persistence.inner_band_retained_fraction:.1%}`",
        f"- that middle lane is real geometry, not leftover cutoff fog: the split-critical unresolved share still collapses from `{split_persistence.low_unresolved_fraction:.1%}` to `{split_persistence.high_unresolved_fraction:.1%}`",
        "",
        "## Why this changes the repo",
        "",
        "The earlier persistence sidecar only settled one contrast: unity cubic versus one asymmetric cubic.",
        "That was honest, but still incomplete.",
        "",
        "The split-critical cubic already told us that broken symmetry can stay balanced and hot near the middle of the square.",
        "This atlas checks whether that hotter middle survives a larger cutoff or whether it collapses like the winner-take-most cubic once the budget stops choking the orbit.",
        "",
        "It survives, but not all the way to the unity story.",
        "",
        f"At `{CUBIC_BUDGET_HIGH}` steps the unity cubic keeps `{unity_persistence.high_inner_band_late:.1%}` late-tail share in the nearest-critical band, the split-critical cubic keeps `{split_persistence.high_inner_band_late:.1%}`, and the old asymmetric cubic keeps only `{asym_persistence.high_inner_band_late:.1%}`.",
        "",
        "That is the bounded upgrade here: the repo no longer treats 'broken symmetry' as one persistence outcome.",
        "",
        "## Read the figure",
        "",
        f"- top row: low-budget late-tail maps at `{CUBIC_BUDGET_LOW}` steps for all three cubics",
        f"- bottom row: the same maps at `{CUBIC_BUDGET_HIGH}` steps",
        "- summary block: grid late share, center-four late share, unresolved fraction, and near-critical retention for each cubic",
        "",
        "Open `art/cubic-persistence-atlas.svg`, `art/cubic-persistence-atlas.png`, `art/cubic-persistence-atlas.csv`, and `notebooks/cubic_persistence_atlas.ipynb` next.",
    ]
    (REPORTS / "cubic-persistence-atlas.md").write_text("\n".join(cubic_persistence_lines) + "\n")

    cubic_persistence_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Three cubic persistence atlas\n",
                    "\n",
                    "This notebook is the slower companion to `reports/cubic-persistence-atlas.md`.\n",
                    "It reads the generated CSV and checks the middle-lane claim directly.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import csv\n",
                    "from pathlib import Path\n",
                    "\n",
                    "rows = []\n",
                    "with (Path('..') / 'art' / 'cubic-persistence-atlas.csv').open() as handle:\n",
                    "    for row in csv.DictReader(handle):\n",
                    "        parsed = {key: (float(value) if key not in {'polynomial'} else value) for key, value in row.items()}\n",
                    "        rows.append(parsed)\n",
                    "rows\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Sort by surviving center heat\n",
                    "\n",
                    "The cleanest read is just to rank the three cubics by high-budget center-four late share.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "sorted([(row['polynomial'], row['high_center_late']) for row in rows], key=lambda item: item[1], reverse=True)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Check the middle-lane claim\n",
                    "\n",
                    "The split-critical cubic should sit between the unity cubic and the older asymmetric cubic on both surviving center heat and inner-band retention.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "by_name = {row['polynomial']: row for row in rows}\n",
                    "unity = by_name['unity-cubic']\n",
                    "asym = by_name['asymmetric-cubic']\n",
                    "split = by_name['split-critical-asymmetric-cubic']\n",
                    "print('high center', unity['high_center_late'], split['high_center_late'], asym['high_center_late'])\n",
                    "print('inner retention', unity['inner_band_retained_fraction'], split['inner_band_retained_fraction'], asym['inner_band_retained_fraction'])\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (REPO / "notebooks" / "cubic_persistence_atlas.ipynb").write_text(json.dumps(cubic_persistence_notebook, indent=2) + "\n")

    (REPORTS / "unity-power-scan.md").write_text("\n".join(scan_lines) + "\n")
    print("generated gallery, scan figures, late-tail map, cubic persistence atlas, asymmetric cubic contrasts, and reports")


if __name__ == "__main__":
    main()
