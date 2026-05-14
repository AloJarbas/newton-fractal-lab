from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import basin_summary, iterate_unity, sample_grid, scan_unity_family
from .render import render_power_scan_svg, render_unity_svg


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
