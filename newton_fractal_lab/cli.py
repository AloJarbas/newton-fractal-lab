from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import basin_summary, compare_radius_budgets, iterate_unity, iteration_histogram, sample_grid, scan_radius_bands, scan_unity_family
from .cubic import asymmetric_cubic, cubic_basin_summary, sample_cubic_grid, scan_critical_distance, unity_cubic
from .render import export_png_from_svg, render_cubic_comparison_svg, render_iteration_histograms_svg, render_power_scan_svg, render_radius_budget_comparison_svg, render_radius_scan_svg, render_unity_svg


def main() -> None:
    parser = argparse.ArgumentParser(description="Newton fractal lab for z^n - 1")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="render a Newton fractal SVG")
    render_parser.add_argument("--power", type=int, required=True)
    render_parser.add_argument("--width", type=int, default=240)
    render_parser.add_argument("--height", type=int, default=240)
    render_parser.add_argument("--max-iter", type=int, default=40)
    render_parser.add_argument("--output", type=Path, required=True)
    render_parser.add_argument("--title", type=str, default=None)

    report_parser = subparsers.add_parser("report", help="report Newton iteration at one starting point")
    report_parser.add_argument("--power", type=int, required=True)
    report_parser.add_argument("--x", type=float, required=True)
    report_parser.add_argument("--y", type=float, required=True)
    report_parser.add_argument("--max-iter", type=int, default=40)

    grid_parser = subparsers.add_parser("grid-report", help="summarize a whole sampling grid")
    grid_parser.add_argument("--power", type=int, required=True)
    grid_parser.add_argument("--width", type=int, default=120)
    grid_parser.add_argument("--height", type=int, default=120)
    grid_parser.add_argument("--max-iter", type=int, default=40)

    scan_parser = subparsers.add_parser("power-scan", help="scan several powers and optionally render a summary SVG")
    scan_parser.add_argument("--power-min", type=int, required=True)
    scan_parser.add_argument("--power-max", type=int, required=True)
    scan_parser.add_argument("--width", type=int, default=120)
    scan_parser.add_argument("--height", type=int, default=120)
    scan_parser.add_argument("--max-iter", type=int, default=40)
    scan_parser.add_argument("--output", type=Path, default=None)
    scan_parser.add_argument("--title", type=str, default=None)

    radius_parser = subparsers.add_parser("radius-scan", help="compare convergence by start radius across several powers")
    radius_parser.add_argument("--powers", type=str, required=True, help="comma-separated powers, e.g. 3,6,9,12")
    radius_parser.add_argument("--width", type=int, default=120)
    radius_parser.add_argument("--height", type=int, default=120)
    radius_parser.add_argument("--max-iter", type=int, default=40)
    radius_parser.add_argument("--bands", type=int, default=12)
    radius_parser.add_argument("--output", type=Path, default=None)
    radius_parser.add_argument("--title", type=str, default=None)

    hist_parser = subparsers.add_parser("iteration-hist", help="compare exact convergence-step histograms across several powers")
    hist_parser.add_argument("--powers", type=str, required=True, help="comma-separated powers, e.g. 3,6,9,12")
    hist_parser.add_argument("--width", type=int, default=120)
    hist_parser.add_argument("--height", type=int, default=120)
    hist_parser.add_argument("--max-iter", type=int, default=40)
    hist_parser.add_argument("--output", type=Path, default=None)
    hist_parser.add_argument("--title", type=str, default=None)

    budget_parser = subparsers.add_parser("budget-radius-compare", help="compare radial convergence profiles at two iteration budgets")
    budget_parser.add_argument("--powers", type=str, required=True, help="comma-separated powers, e.g. 3,6,9,12")
    budget_parser.add_argument("--width", type=int, default=120)
    budget_parser.add_argument("--height", type=int, default=120)
    budget_parser.add_argument("--bands", type=int, default=12)
    budget_parser.add_argument("--low-budget", type=int, default=40)
    budget_parser.add_argument("--high-budget", type=int, default=80)
    budget_parser.add_argument("--output", type=Path, default=None)
    budget_parser.add_argument("--png-output", type=Path, default=None)
    budget_parser.add_argument("--title", type=str, default=None)

    cubic_parser = subparsers.add_parser("cubic-compare", help="compare the unity cubic against one asymmetric cubic")
    cubic_parser.add_argument("--width", type=int, default=180)
    cubic_parser.add_argument("--height", type=int, default=180)
    cubic_parser.add_argument("--max-iter", type=int, default=40)
    cubic_parser.add_argument("--bands", type=int, default=8)
    cubic_parser.add_argument("--late-threshold", type=int, default=10)
    cubic_parser.add_argument("--output", type=Path, default=None)
    cubic_parser.add_argument("--png-output", type=Path, default=None)
    cubic_parser.add_argument("--title", type=str, default=None)

    args = parser.parse_args()

    if args.command == "render":
        render_unity_svg(
            args.power,
            width=args.width,
            height=args.height,
            max_iter=args.max_iter,
            output=args.output,
            title=args.title,
        )
        print(args.output)
        return

    if args.command == "report":
        result = iterate_unity(complex(args.x, args.y), args.power, max_iter=args.max_iter)
        payload = {
            "power": args.power,
            "start": [args.x, args.y],
            "end": [round(result.end.real, 9), round(result.end.imag, 9)],
            "iterations": result.iterations,
            "converged": result.converged,
            "stalled": result.stalled,
            "root_index": result.root_index,
            "residual": result.residual,
        }
        print(json.dumps(payload, indent=2))
        return

    if args.command == "power-scan":
        rows = scan_unity_family(
            args.power_min,
            args.power_max,
            width=args.width,
            height=args.height,
            max_iter=args.max_iter,
        )
        if args.output is not None:
            render_power_scan_svg(rows, output=args.output, title=args.title)
        payload = [
            {
                "power": row.power,
                "mean_iterations": round(row.mean_iterations, 6),
                "converged_fraction": round(row.converged_fraction, 6),
                "stalled_fraction": round(row.stalled_fraction, 6),
                "min_share": round(row.min_share, 6),
                "max_share": round(row.max_share, 6),
            }
            for row in rows
        ]
        print(json.dumps(payload, indent=2))
        return

    if args.command == "radius-scan":
        powers = [int(chunk.strip()) for chunk in args.powers.split(",") if chunk.strip()]
        profiles = {
            power: scan_radius_bands(
                power,
                width=args.width,
                height=args.height,
                max_iter=args.max_iter,
                bands=args.bands,
            )
            for power in powers
        }
        if args.output is not None:
            render_radius_scan_svg(profiles, output=args.output, title=args.title)
        payload = {
            str(power): [
                {
                    "radius_min": round(row.radius_min, 6),
                    "radius_max": round(row.radius_max, 6),
                    "sample_count": row.sample_count,
                    "mean_iterations": round(row.mean_iterations, 6),
                    "converged_fraction": round(row.converged_fraction, 6),
                    "stalled_fraction": round(row.stalled_fraction, 6),
                }
                for row in rows
            ]
            for power, rows in profiles.items()
        }
        print(json.dumps(payload, indent=2))
        return

    if args.command == "iteration-hist":
        powers = [int(chunk.strip()) for chunk in args.powers.split(",") if chunk.strip()]
        histograms = [
            iteration_histogram(
                power,
                width=args.width,
                height=args.height,
                max_iter=args.max_iter,
            )
            for power in powers
        ]
        if args.output is not None:
            render_iteration_histograms_svg(histograms, output=args.output, title=args.title)
        payload = [
            {
                "power": histogram.power,
                "max_iter": histogram.max_iter,
                "total_points": histogram.total_points,
                "converged_counts": list(histogram.converged_counts),
                "stalled_count": histogram.stalled_count,
                "unresolved_count": histogram.unresolved_count,
            }
            for histogram in histograms
        ]
        print(json.dumps(payload, indent=2))
        return

    if args.command == "budget-radius-compare":
        powers = [int(chunk.strip()) for chunk in args.powers.split(",") if chunk.strip()]
        comparisons = {
            power: compare_radius_budgets(
                power,
                low_budget=args.low_budget,
                high_budget=args.high_budget,
                width=args.width,
                height=args.height,
                bands=args.bands,
            )
            for power in powers
        }
        if args.output is not None:
            render_radius_budget_comparison_svg(comparisons, output=args.output, title=args.title)
        if args.png_output is not None and args.output is not None:
            export_png_from_svg(args.output, args.png_output)
        payload = [
            {
                "power": power,
                "low_budget": args.low_budget,
                "high_budget": args.high_budget,
                "grid_recovered_fraction": round(
                    sum(row.sample_count * row.recovered_fraction for row in rows) / sum(row.sample_count for row in rows),
                    6,
                ),
                "max_recovered_fraction": round(max(row.recovered_fraction for row in rows), 6),
                "max_recovered_band": {
                    "radius_min": round(max(rows, key=lambda row: row.recovered_fraction).radius_min, 6),
                    "radius_max": round(max(rows, key=lambda row: row.recovered_fraction).radius_max, 6),
                },
                "high_budget_weakest_band": {
                    "radius_min": round(min(rows, key=lambda row: row.high_converged_fraction).radius_min, 6),
                    "radius_max": round(min(rows, key=lambda row: row.high_converged_fraction).radius_max, 6),
                    "converged_fraction": round(min(rows, key=lambda row: row.high_converged_fraction).high_converged_fraction, 6),
                },
            }
            for power, rows in comparisons.items()
        ]
        print(json.dumps(payload, indent=2))
        return

    if args.command == "cubic-compare":
        unity = unity_cubic()
        asymmetric = asymmetric_cubic()
        unity_samples = sample_cubic_grid(unity, args.width, args.height, max_iter=args.max_iter)
        asym_samples = sample_cubic_grid(asymmetric, args.width, args.height, max_iter=args.max_iter)
        unity_stats = cubic_basin_summary(unity, args.width, args.height, unity_samples)
        asym_stats = cubic_basin_summary(asymmetric, args.width, args.height, asym_samples)
        unity_rows = scan_critical_distance(
            unity,
            width=args.width,
            height=args.height,
            max_iter=args.max_iter,
            bands=args.bands,
            late_threshold=args.late_threshold,
        )
        asym_rows = scan_critical_distance(
            asymmetric,
            width=args.width,
            height=args.height,
            max_iter=args.max_iter,
            bands=args.bands,
            late_threshold=args.late_threshold,
        )
        if args.output is not None:
            render_cubic_comparison_svg(
                unity,
                unity_stats,
                unity_samples,
                unity_rows,
                asymmetric,
                asym_stats,
                asym_samples,
                asym_rows,
                output=args.output,
                title=args.title,
                max_iter=args.max_iter,
            )
        if args.png_output is not None and args.output is not None:
            export_png_from_svg(args.output, args.png_output, size=2200, dpi=300)
        payload = {
            "unity_cubic": {
                "mean_iterations": round(unity_stats.mean_iterations, 6),
                "basin_shares": [round(share, 6) for share in unity_stats.basin_shares],
                "inner_late_fraction": round(unity_rows[0].late_fraction, 6),
            },
            "asymmetric_cubic": {
                "mean_iterations": round(asym_stats.mean_iterations, 6),
                "basin_shares": [round(share, 6) for share in asym_stats.basin_shares],
                "inner_late_fraction": round(asym_rows[0].late_fraction, 6),
            },
        }
        print(json.dumps(payload, indent=2))
        return

    samples = sample_grid(args.power, args.width, args.height, max_iter=args.max_iter)
    stats = basin_summary(args.power, args.width, args.height, samples)
    payload = {
        "power": stats.power,
        "width": stats.width,
        "height": stats.height,
        "converged_points": stats.converged_points,
        "stalled_points": stats.stalled_points,
        "mean_iterations": round(stats.mean_iterations, 6),
        "basin_counts": list(stats.basin_counts),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
