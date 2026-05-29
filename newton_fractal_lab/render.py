from __future__ import annotations

import colorsys
from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import xml.etree.ElementTree as ET

from .core import IterationHistogram, LateTailPersistenceRow, LateTailTileRow, PowerScanRow, RadiusBandRow, RadiusBudgetComparisonRow, basin_summary, sample_grid, unity_roots
from .cubic import CriticalDistanceBandRow, CubicBasinStats, CubicBudgetComparisonRow, CubicLateTailTileRow, CubicOppositionRow, CubicPolynomial, cubic_critical_points, sample_cubic_grid


def _paragraph(x: float, y: float, lines: list[str], *, fill: str, font_size: int, weight: str = "normal", line_height: int = 20) -> str:
    tspans = [f'<tspan x="{x:.1f}" dy="0">{escape(lines[0])}</tspan>']
    tspans.extend(f'<tspan x="{x:.1f}" dy="{line_height}">{escape(line)}</tspan>' for line in lines[1:])
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{font_size}" font-family="Helvetica, Arial, sans-serif" font-weight="{weight}">{"".join(tspans)}</text>'


def render_unity_svg(
    power: int,
    *,
    width: int = 240,
    height: int = 240,
    max_iter: int = 40,
    output: str | Path,
    title: str | None = None,
) -> dict[str, float | int]:
    samples = sample_grid(power, width, height, max_iter=max_iter)
    stats = basin_summary(power, width, height, samples)
    roots = unity_roots(power)

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    frame_left = 40
    frame_top = 110
    frame_size = 580
    cell_w = frame_size / width
    cell_h = frame_size / height
    svg_width = 980
    svg_height = 780
    side_x = frame_left + frame_size + 32
    side_w = svg_width - side_x - 40

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#060814"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="40" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or f"Newton fractal for z^{power} - 1")}</text>',
        '<text x="40" y="80" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">Each basin shows which root Newton iteration finds. Darker cells converged faster.</text>',
        f'<rect x="{frame_left}" y="{frame_top}" width="{frame_size}" height="{frame_size}" rx="16" fill="#020617" stroke="#2b3752" stroke-width="1.5"/>',
        f'<rect x="{side_x}" y="{frame_top}" width="{side_w}" height="{frame_size}" rx="18" fill="#0b1320" stroke="#334155" stroke-width="1.4"/>',
        f'<text x="{side_x + 20}" y="{frame_top + 34}" fill="#e5eefc" font-size="20" font-family="Helvetica, Arial, sans-serif" font-weight="700">Root legend</text>',
        _paragraph(
            side_x + 20,
            frame_top + 62,
            [
                'Same square grid over the complex plane.',
                f'{power} competing roots split the plane into basins.',
            ],
            fill='#9ec5ff',
            font_size=14,
            line_height=18,
        ),
    ]

    for row in range(height):
        start = row * width
        row_samples = samples[start : start + width]
        run_start = 0
        current_fill = _fill_for(row_samples[0], power, max_iter)
        for col in range(1, width + 1):
            next_fill = _fill_for(row_samples[col], power, max_iter) if col < width else None
            if next_fill != current_fill:
                x = frame_left + run_start * cell_w
                y = frame_top + row * cell_h
                run_width = (col - run_start) * cell_w
                lines.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{run_width:.2f}" height="{cell_h + 0.08:.2f}" fill="{current_fill}"/>'
                )
                run_start = col
                current_fill = next_fill

    lines.append('<g fill="#dbeafe" font-family="Helvetica, Arial, sans-serif">')
    for idx, root in enumerate(roots):
        hue = idx / power
        swatch_y = frame_top + 120 + idx * 30
        lines.append(f'<rect x="{side_x + 20}" y="{swatch_y - 12}" width="18" height="18" rx="4" fill="{_root_hex(hue, 0.88)}"/>')
        lines.append(
            f'<text x="{side_x + 48}" y="{swatch_y + 1}" font-size="13">root {idx}: {_fmt_complex(root)}</text>'
        )
    lines.append('</g>')

    stats_y = frame_top + frame_size - 118
    lines.append(f'<text x="{side_x + 20}" y="{stats_y}" fill="#e5eefc" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">Grid summary</text>')
    lines.append(
        _paragraph(
            side_x + 20,
            stats_y + 26,
            [
                f'grid: {width}×{height}',
                f'mean iterations: {stats.mean_iterations:.2f}',
                f'converged: {stats.converged_points}/{stats.total_points}',
            ],
            fill='#cbd5e1',
            font_size=14,
            line_height=20,
        )
    )
    lines.append(
        _paragraph(
            side_x + 20,
            frame_top + frame_size - 42,
            ['GitHub preview note: the legend now lives beside the basin map,', 'so labels stay readable without covering the fractal itself.'],
            fill='#93c5fd',
            font_size=13,
            line_height=18,
        )
    )

    lines.append('</svg>')

    output.write_text('\n'.join(lines) + '\n')
    return {
        "power": power,
        "width": width,
        "height": height,
        "mean_iterations": stats.mean_iterations,
        "converged_points": stats.converged_points,
        "stalled_points": stats.stalled_points,
    }


def render_power_scan_svg(
    rows: list[PowerScanRow],
    *,
    output: str | Path,
    title: str | None = None,
) -> None:
    if not rows:
        raise ValueError("rows must not be empty")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    width = 920
    height = 820
    left = 72
    right = 40
    top = 108
    panel_gap = 52
    panel_height = 230
    panel_width = width - left - right
    powers = [row.power for row in rows]
    min_power = min(powers)
    max_power = max(powers)
    max_mean = max(row.mean_iterations for row in rows)
    share_top = max(max(row.max_share, 1.0 / row.power) for row in rows) * 1.12

    def x_for(power: int) -> float:
        if max_power == min_power:
            return left + panel_width / 2.0
        return left + (power - min_power) / (max_power - min_power) * panel_width

    def y_for_mean(value: float) -> float:
        return top + panel_height - (value / max_mean) * panel_height

    def y_for_share(value: float) -> float:
        base = top + panel_height + panel_gap
        return base + panel_height - (value / share_top) * panel_height

    mean_points = " ".join(f"{x_for(row.power):.2f},{y_for_mean(row.mean_iterations):.2f}" for row in rows)
    ideal_points = " ".join(f"{x_for(row.power):.2f},{y_for_share(1.0 / row.power):.2f}" for row in rows)
    conv_points = " ".join(f"{x_for(row.power):.2f},{y_for_share(row.converged_fraction):.2f}" for row in rows)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="48" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Unity-family power scan")}</text>',
        '<text x="72" y="74" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">One scan across powers shows how Newton basins get slower and less evenly captured on the same square grid.</text>',
    ]

    for panel_top, label in ((top, "mean iterations across the sampled square"), (top + panel_height + panel_gap, "convergence fraction and basin-share spread")):
        lines.append(f'<rect x="{left}" y="{panel_top}" width="{panel_width}" height="{panel_height}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<text x="{left + 18}" y="{panel_top + 28}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">{label}</text>')
        for tick in range(min_power, max_power + 1):
            x = x_for(tick)
            lines.append(f'<line x1="{x:.2f}" y1="{panel_top + 40}" x2="{x:.2f}" y2="{panel_top + panel_height - 18}" stroke="#1f2937" stroke-width="1"/>')
            lines.append(f'<text x="{x:.2f}" y="{panel_top + panel_height + 18}" fill="#94a3b8" font-size="12" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{tick}</text>')

    for idx in range(5):
        frac = idx / 4
        mean_value = max_mean * frac
        y = y_for_mean(mean_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_width}" y2="{y:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 4:.2f}" fill="#94a3b8" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{mean_value:.1f}</text>')

        share_value = share_top * frac
        sy = y_for_share(share_value)
        lines.append(f'<line x1="{left}" y1="{sy:.2f}" x2="{left + panel_width}" y2="{sy:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{left - 12}" y="{sy + 4:.2f}" fill="#94a3b8" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{share_value:.2f}</text>')

    lines.append(f'<polyline fill="none" stroke="#60a5fa" stroke-width="3" points="{mean_points}"/>')
    for row in rows:
        x = x_for(row.power)
        y = y_for_mean(row.mean_iterations)
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="#dbeafe" stroke="#60a5fa" stroke-width="2"/>')

    for row in rows:
        x = x_for(row.power)
        y1 = y_for_share(row.max_share)
        y2 = y_for_share(row.min_share)
        lines.append(f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/>')
        lines.append(f'<circle cx="{x:.2f}" cy="{y_for_share(row.converged_fraction):.2f}" r="4.5" fill="#bfdbfe" stroke="#38bdf8" stroke-width="2"/>')

    lines.append(f'<polyline fill="none" stroke="#38bdf8" stroke-width="2.5" points="{conv_points}"/>')
    lines.append(f'<polyline fill="none" stroke="#f8fafc" stroke-width="1.8" stroke-dasharray="6 5" points="{ideal_points}"/>')

    legend_y = height - 116
    legend_w = panel_width
    lines.append(f'<rect x="{left}" y="{legend_y - 26}" width="{legend_w}" height="70" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append('<g font-family="Helvetica, Arial, sans-serif" font-size="13">')
    lines.append(f'<line x1="{left + 20}" y1="{legend_y}" x2="{left + 48}" y2="{legend_y}" stroke="#60a5fa" stroke-width="3"/><text x="{left + 56}" y="{legend_y + 4}" fill="#dbeafe">mean iterations</text>')
    lines.append(f'<line x1="{left + 260}" y1="{legend_y}" x2="{left + 288}" y2="{legend_y}" stroke="#38bdf8" stroke-width="2.5"/><text x="{left + 296}" y="{legend_y + 4}" fill="#dbeafe">converged fraction</text>')
    lines.append(f'<line x1="{left + 20}" y1="{legend_y + 26}" x2="{left + 48}" y2="{legend_y + 26}" stroke="#f8fafc" stroke-width="1.8" stroke-dasharray="6 5"/><text x="{left + 56}" y="{legend_y + 30}" fill="#dbeafe">ideal equal share 1/n</text>')
    lines.append(f'<line x1="{left + 260}" y1="{legend_y + 18}" x2="{left + 260}" y2="{legend_y + 34}" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/><text x="{left + 274}" y="{legend_y + 30}" fill="#dbeafe">min to max basin share</text>')
    lines.append('</g>')
    lines.append('</svg>')

    output.write_text("\n".join(lines) + "\n")


def render_radius_scan_svg(
    profiles: dict[int, list[RadiusBandRow]],
    *,
    output: str | Path,
    title: str | None = None,
) -> None:
    if not profiles:
        raise ValueError("profiles must not be empty")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    ordered_powers = sorted(profiles)
    first_profile = profiles[ordered_powers[0]]
    if not first_profile:
        raise ValueError("profiles must contain non-empty band rows")
    max_radius = max(row.radius_max for rows in profiles.values() for row in rows)
    max_mean = max(row.mean_iterations for rows in profiles.values() for row in rows)

    width = 1120
    height = 880
    left = 82
    right = 42
    top = 112
    panel_gap = 60
    panel_height = 250
    panel_width = width - left - right

    def x_for(radius: float) -> float:
        return left + (radius / max_radius) * panel_width if max_radius > 0 else left + panel_width / 2.0

    def y_for_mean(value: float) -> float:
        return top + panel_height - (value / max_mean) * panel_height if max_mean > 0 else top + panel_height / 2.0

    def y_for_frac(value: float) -> float:
        panel_top = top + panel_height + panel_gap
        return panel_top + panel_height - value * panel_height

    colors = ["#60a5fa", "#f59e0b", "#34d399", "#f472b6", "#c084fc"]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="48" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Critical-radius scan")}</text>',
        '<text x="82" y="74" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">The derivative singularity at z = 0 does not fill the whole square equally. These radial bands show where convergence slows and where it stays reliable.</text>',
    ]

    panel_labels = [
        (top, "mean iterations by start radius"),
        (top + panel_height + panel_gap, "converged fraction by start radius"),
    ]
    for panel_top, label in panel_labels:
        lines.append(f'<rect x="{left}" y="{panel_top}" width="{panel_width}" height="{panel_height}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<text x="{left + 18}" y="{panel_top + 28}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">{_escape(label)}</text>')
        for tick in range(6):
            radius = max_radius * tick / 5.0
            x = x_for(radius)
            lines.append(f'<line x1="{x:.2f}" y1="{panel_top + 40}" x2="{x:.2f}" y2="{panel_top + panel_height - 18}" stroke="#1f2937" stroke-width="1"/>')
            lines.append(f'<text x="{x:.2f}" y="{panel_top + panel_height + 18}" fill="#94a3b8" font-size="12" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{radius:.2f}</text>')

    for idx in range(5):
        frac = idx / 4
        mean_value = max_mean * frac
        y = y_for_mean(mean_value)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_width}" y2="{y:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 4:.2f}" fill="#94a3b8" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{mean_value:.1f}</text>')

        frac_y = y_for_frac(frac)
        lines.append(f'<line x1="{left}" y1="{frac_y:.2f}" x2="{left + panel_width}" y2="{frac_y:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{left - 12}" y="{frac_y + 4:.2f}" fill="#94a3b8" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{frac:.2f}</text>')

    unit_x = x_for(1.0)
    for panel_top, _ in panel_labels:
        lines.append(f'<line x1="{unit_x:.2f}" y1="{panel_top + 40}" x2="{unit_x:.2f}" y2="{panel_top + panel_height - 18}" stroke="#e2e8f0" stroke-width="1.6" stroke-dasharray="6 5" opacity="0.9"/>')
    lines.append(f'<text x="{unit_x + 8:.2f}" y="{top + 54:.2f}" fill="#dbeafe" font-size="12" font-family="Helvetica, Arial, sans-serif">unit circle radius</text>')

    for index, power in enumerate(ordered_powers):
        rows = profiles[power]
        color = colors[index % len(colors)]
        mean_points = " ".join(f"{x_for((row.radius_min + row.radius_max) / 2.0):.2f},{y_for_mean(row.mean_iterations):.2f}" for row in rows)
        frac_points = " ".join(f"{x_for((row.radius_min + row.radius_max) / 2.0):.2f},{y_for_frac(row.converged_fraction):.2f}" for row in rows)
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{mean_points}"/>')
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{frac_points}"/>')
        for row in rows:
            x = x_for((row.radius_min + row.radius_max) / 2.0)
            lines.append(f'<circle cx="{x:.2f}" cy="{y_for_mean(row.mean_iterations):.2f}" r="4" fill="#dbeafe" stroke="{color}" stroke-width="2"/>')
            lines.append(f'<circle cx="{x:.2f}" cy="{y_for_frac(row.converged_fraction):.2f}" r="4" fill="#dbeafe" stroke="{color}" stroke-width="2"/>')

    legend_y = height - 126
    lines.append(f'<rect x="{left}" y="{legend_y - 28}" width="{panel_width}" height="88" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_y - 2}" fill="#e5eefc" font-size="16" font-family="Helvetica, Arial, sans-serif" font-weight="700">Profiles</text>')
    for index, power in enumerate(ordered_powers):
        color = colors[index % len(colors)]
        x = left + 20 + index * 170
        y = legend_y + 22
        lines.append(f'<line x1="{x}" y1="{y}" x2="{x + 30}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text x="{x + 40}" y="{y + 4}" fill="#dbeafe" font-size="13" font-family="Helvetica, Arial, sans-serif">z^{power} - 1</text>')
    lines.append(_paragraph(left + 18, legend_y + 48, ['Inner bands sit closest to the derivative singularity at z = 0.', 'Higher powers stay slow for longer before the profiles flatten near the outer square.'], fill='#9ec5ff', font_size=13, line_height=18))
    lines.append('</svg>')

    output.write_text("\n".join(lines) + "\n")


def render_iteration_histograms_svg(
    histograms: list[IterationHistogram],
    *,
    output: str | Path,
    title: str | None = None,
) -> None:
    if not histograms:
        raise ValueError("histograms must not be empty")

    ordered = sorted(histograms, key=lambda row: row.power)
    if len(ordered) > 4:
        raise ValueError("at most four histograms fit in the current layout")

    width = 1160
    height = 980
    outer_left = 52
    outer_top = 118
    panel_gap_x = 36
    panel_gap_y = 44
    panel_w = 500
    panel_h = 290
    bar_pad = 28
    max_fraction = max(
        max(
            max(count / histogram.total_points for count in histogram.converged_counts),
            histogram.tail_fraction(20),
            (histogram.stalled_count + histogram.unresolved_count) / histogram.total_points,
        )
        for histogram in ordered
    )
    max_fraction = max(max_fraction, 0.02)

    def panel_origin(index: int) -> tuple[float, float]:
        row = index // 2
        col = index % 2
        return (
            outer_left + col * (panel_w + panel_gap_x),
            outer_top + row * (panel_h + panel_gap_y),
        )

    def x_for(panel_left: float, histogram: IterationHistogram, value: int) -> float:
        inner_w = panel_w - 2 * bar_pad - 96
        if histogram.max_iter <= 0:
            return panel_left + bar_pad + inner_w / 2.0
        return panel_left + bar_pad + value / histogram.max_iter * inner_w

    def y_for(panel_top: float, fraction: float) -> float:
        inner_h = panel_h - 86
        return panel_top + panel_h - 34 - fraction / max_fraction * inner_h

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '  <linearGradient id="fastBar" x1="0" y1="1" x2="0" y2="0">',
        '    <stop offset="0%" stop-color="#2563eb"/>',
        '    <stop offset="100%" stop-color="#93c5fd"/>',
        '  </linearGradient>',
        '  <linearGradient id="lateBar" x1="0" y1="1" x2="0" y2="0">',
        '    <stop offset="0%" stop-color="#ea580c"/>',
        '    <stop offset="100%" stop-color="#fdba74"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{outer_left}" y="50" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Slow-convergence histograms")}</text>',
        '<text x="52" y="76" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">Each panel shows exact convergence-step fractions on the same square grid. Orange and white bars summarize the late tail and cutoff misses.</text>',
    ]

    for idx, histogram in enumerate(ordered):
        left, top = panel_origin(idx)
        inner_top = top + 52
        inner_bottom = top + panel_h - 34
        late_fraction = histogram.tail_fraction(20)
        unresolved_fraction = (histogram.stalled_count + histogram.unresolved_count) / histogram.total_points
        lines.append(f'<rect x="{left}" y="{top}" width="{panel_w}" height="{panel_h}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<text x="{left + 18}" y="{top + 30}" fill="#e5eefc" font-size="20" font-family="Helvetica, Arial, sans-serif" font-weight="700">z^{histogram.power} - 1</text>')
        lines.append(f'<text x="{left + 18}" y="{top + 50}" fill="#9ec5ff" font-size="13" font-family="Helvetica, Arial, sans-serif">max iter {histogram.max_iter}, sampled square {histogram.total_points} starts</text>')

        for tick in range(5):
            frac = max_fraction * tick / 4.0
            y = y_for(top, frac)
            lines.append(f'<line x1="{left + bar_pad}" y1="{y:.2f}" x2="{left + panel_w - bar_pad}" y2="{y:.2f}" stroke="#16202f" stroke-width="1"/>')
            lines.append(f'<text x="{left + bar_pad - 10}" y="{y + 4:.2f}" fill="#94a3b8" font-size="11" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{frac:.2%}</text>')

        for tick in range(0, histogram.max_iter + 1, 10):
            x = x_for(left, histogram, tick)
            lines.append(f'<line x1="{x:.2f}" y1="{inner_top}" x2="{x:.2f}" y2="{inner_bottom}" stroke="#1f2937" stroke-width="1"/>')
            lines.append(f'<text x="{x:.2f}" y="{top + panel_h - 12}" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{tick}</text>')

        plot_width = panel_w - 2 * bar_pad - 96
        bar_width = plot_width / (histogram.max_iter + 1)
        for step, count in enumerate(histogram.converged_counts):
            fraction = count / histogram.total_points
            if fraction <= 0.0:
                continue
            x = left + bar_pad + step * bar_width
            y = y_for(top, fraction)
            fill = 'url(#lateBar)' if step >= 20 else 'url(#fastBar)'
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(bar_width - 0.5, 0.8):.2f}" height="{inner_bottom - y:.2f}" fill="{fill}" opacity="0.95"/>')

        indicator_left = left + bar_pad + plot_width + 22
        late_y = y_for(top, late_fraction)
        unresolved_y = y_for(top, unresolved_fraction)
        lines.append(f'<rect x="{indicator_left:.2f}" y="{late_y:.2f}" width="16" height="{inner_bottom - late_y:.2f}" rx="4" fill="#f59e0b" opacity="0.95"/>')
        lines.append(f'<rect x="{indicator_left + 34:.2f}" y="{unresolved_y:.2f}" width="16" height="{inner_bottom - unresolved_y:.2f}" rx="4" fill="#f8fafc" opacity="0.95"/>')
        lines.append(
            _paragraph(
                left + 18,
                top + 74,
                [
                    f'late tail: {late_fraction:.1%}',
                    f'unresolved at cutoff: {unresolved_fraction:.1%}',
                ],
                fill='#cbd5e1',
                font_size=12,
                line_height=16,
            )
        )

    legend_y = 860
    lines.append(f'<rect x="{outer_left}" y="{legend_y - 26}" width="{2 * panel_w + panel_gap_x}" height="70" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(_paragraph(outer_left + 18, legend_y, ['Blue bars: exact convergence fraction at a given iteration count.', 'Orange bars inside each histogram: late tail beginning at 20 iterations. White bar: stalled or unresolved at the current cutoff.'], fill='#dbeafe', font_size=13, line_height=18))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_radius_budget_comparison_svg(
    comparisons: dict[int, list[RadiusBudgetComparisonRow]],
    *,
    output: str | Path,
    title: str | None = None,
) -> None:
    if not comparisons:
        raise ValueError("comparisons must not be empty")

    ordered_powers = sorted(comparisons)
    first_rows = comparisons[ordered_powers[0]]
    if not first_rows:
        raise ValueError("comparisons must contain non-empty rows")

    low_budget = first_rows[0].low_budget
    high_budget = first_rows[0].high_budget
    max_radius = max(row.radius_max for rows in comparisons.values() for row in rows)
    max_recovered = max(row.recovered_fraction for rows in comparisons.values() for row in rows)
    max_recovered = max(max_recovered, 0.02)

    width = 1160
    height = 1060
    left = 76
    right = 44
    top = 112
    gap_x = 34
    gap_y = 54
    panel_w = (width - left - right - gap_x) / 2.0
    panel_h = 278
    bottom_top = top + panel_h + gap_y
    bottom_h = 300
    colors = ["#60a5fa", "#f59e0b", "#34d399", "#f472b6", "#c084fc"]

    def x_for(radius: float, panel_left: float, panel_width: float) -> float:
        return panel_left + (radius / max_radius) * panel_width if max_radius > 0 else panel_left + panel_width / 2.0

    def y_for_fraction(value: float, panel_top: float, panel_height: float) -> float:
        return panel_top + panel_height - value * panel_height

    def y_for_recovered(value: float) -> float:
        return bottom_top + bottom_h - value / max_recovered * bottom_h

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="50" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Iteration-budget radius comparison")}</text>',
        '<text x="76" y="76" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">The question here is simple: which slow radial bands are truly stubborn, and which ones were only budget-limited at the earlier cutoff?</text>',
    ]

    top_panels = [
        (left, top, panel_w, panel_h, f"converged fraction by start radius at {low_budget} iterations"),
        (left + panel_w + gap_x, top, panel_w, panel_h, f"converged fraction by start radius at {high_budget} iterations"),
    ]
    for panel_left, panel_top, panel_width, panel_height, label in top_panels:
        lines.append(f'<rect x="{panel_left}" y="{panel_top}" width="{panel_width}" height="{panel_height}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<text x="{panel_left + 18}" y="{panel_top + 28}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">{_escape(label)}</text>')
        for tick in range(6):
            radius = max_radius * tick / 5.0
            x = x_for(radius, panel_left, panel_width)
            lines.append(f'<line x1="{x:.2f}" y1="{panel_top + 40}" x2="{x:.2f}" y2="{panel_top + panel_height - 18}" stroke="#1f2937" stroke-width="1"/>')
            lines.append(f'<text x="{x:.2f}" y="{panel_top + panel_height + 18}" fill="#94a3b8" font-size="12" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{radius:.2f}</text>')
        for tick in range(5):
            frac = tick / 4.0
            y = y_for_fraction(frac, panel_top + 40, panel_height - 58)
            lines.append(f'<line x1="{panel_left}" y1="{y:.2f}" x2="{panel_left + panel_width}" y2="{y:.2f}" stroke="#16202f" stroke-width="1"/>')
            lines.append(f'<text x="{panel_left - 12}" y="{y + 4:.2f}" fill="#94a3b8" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{frac:.2f}</text>')
        unit_x = x_for(1.0, panel_left, panel_width)
        lines.append(f'<line x1="{unit_x:.2f}" y1="{panel_top + 40}" x2="{unit_x:.2f}" y2="{panel_top + panel_height - 18}" stroke="#e2e8f0" stroke-width="1.6" stroke-dasharray="6 5" opacity="0.9"/>')
        lines.append(f'<text x="{unit_x + 8:.2f}" y="{panel_top + 56:.2f}" fill="#dbeafe" font-size="12" font-family="Helvetica, Arial, sans-serif">unit circle</text>')
        lines.append(f'<text x="{panel_left + panel_width / 2:.2f}" y="{panel_top + panel_height + 36}" fill="#cbd5e1" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">start radius |z₀|</text>')
        lines.append(f'<text x="{panel_left - 56:.2f}" y="{panel_top + panel_height / 2:.2f}" fill="#cbd5e1" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" transform="rotate(-90 {panel_left - 56:.2f} {panel_top + panel_height / 2:.2f})">converged fraction</text>')

    lines.append(f'<rect x="{left}" y="{bottom_top}" width="{width - left - right}" height="{bottom_h}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="{left + 18}" y="{bottom_top + 28}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">recovered share when the budget rises from {low_budget} to {high_budget}</text>')
    for tick in range(6):
        radius = max_radius * tick / 5.0
        x = x_for(radius, left, width - left - right)
        lines.append(f'<line x1="{x:.2f}" y1="{bottom_top + 40}" x2="{x:.2f}" y2="{bottom_top + bottom_h - 18}" stroke="#1f2937" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{bottom_top + bottom_h + 18}" fill="#94a3b8" font-size="12" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{radius:.2f}</text>')
    for tick in range(5):
        frac = max_recovered * tick / 4.0
        y = y_for_recovered(frac)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 4:.2f}" fill="#94a3b8" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{frac:.2f}</text>')
    unit_x_bottom = x_for(1.0, left, width - left - right)
    lines.append(f'<line x1="{unit_x_bottom:.2f}" y1="{bottom_top + 40}" x2="{unit_x_bottom:.2f}" y2="{bottom_top + bottom_h - 18}" stroke="#e2e8f0" stroke-width="1.6" stroke-dasharray="6 5" opacity="0.9"/>')
    lines.append(f'<text x="{unit_x_bottom + 8:.2f}" y="{bottom_top + 56:.2f}" fill="#dbeafe" font-size="12" font-family="Helvetica, Arial, sans-serif">unit circle</text>')
    lines.append(f'<text x="{left + (width - left - right) / 2:.2f}" y="{bottom_top + bottom_h + 36}" fill="#cbd5e1" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">start radius |z₀|</text>')
    lines.append(f'<text x="{left - 56:.2f}" y="{bottom_top + bottom_h / 2:.2f}" fill="#cbd5e1" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" transform="rotate(-90 {left - 56:.2f} {bottom_top + bottom_h / 2:.2f})">recovered fraction</text>')

    for index, power in enumerate(ordered_powers):
        rows = comparisons[power]
        color = colors[index % len(colors)]
        low_points = " ".join(
            f"{x_for((row.radius_min + row.radius_max) / 2.0, left, panel_w):.2f},{y_for_fraction(row.low_converged_fraction, top + 40, panel_h - 58):.2f}"
            for row in rows
        )
        high_points = " ".join(
            f"{x_for((row.radius_min + row.radius_max) / 2.0, left + panel_w + gap_x, panel_w):.2f},{y_for_fraction(row.high_converged_fraction, top + 40, panel_h - 58):.2f}"
            for row in rows
        )
        recovered_points = " ".join(
            f"{x_for((row.radius_min + row.radius_max) / 2.0, left, width - left - right):.2f},{y_for_recovered(row.recovered_fraction):.2f}"
            for row in rows
        )
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3.4" points="{low_points}"/>')
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3.4" points="{high_points}"/>')
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3.4" points="{recovered_points}"/>')
        for row in rows:
            radius_mid = (row.radius_min + row.radius_max) / 2.0
            low_x = x_for(radius_mid, left, panel_w)
            high_x = x_for(radius_mid, left + panel_w + gap_x, panel_w)
            bottom_x = x_for(radius_mid, left, width - left - right)
            lines.append(f'<circle cx="{low_x:.2f}" cy="{y_for_fraction(row.low_converged_fraction, top + 40, panel_h - 58):.2f}" r="4.5" fill="#dbeafe" stroke="{color}" stroke-width="2"/>')
            lines.append(f'<circle cx="{high_x:.2f}" cy="{y_for_fraction(row.high_converged_fraction, top + 40, panel_h - 58):.2f}" r="4.5" fill="#dbeafe" stroke="{color}" stroke-width="2"/>')
            lines.append(f'<circle cx="{bottom_x:.2f}" cy="{y_for_recovered(row.recovered_fraction):.2f}" r="4.5" fill="#dbeafe" stroke="{color}" stroke-width="2"/>')

    legend_y = 852
    lines.append(f'<rect x="{left}" y="{legend_y - 26}" width="{width - left - right}" height="88" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_y - 2}" fill="#e5eefc" font-size="16" font-family="Helvetica, Arial, sans-serif" font-weight="700">Profiles</text>')
    for index, power in enumerate(ordered_powers):
        color = colors[index % len(colors)]
        x = left + 20 + index * 170
        y = legend_y + 22
        lines.append(f'<line x1="{x}" y1="{y}" x2="{x + 30}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text x="{x + 40}" y="{y + 4}" fill="#dbeafe" font-size="13" font-family="Helvetica, Arial, sans-serif">z^{power} - 1</text>')
    lines.append(_paragraph(left + 18, legend_y + 48, [f'If the bottom panel stays high, the earlier cutoff was hiding recoverable points.', f'If it falls close to zero, the remaining difficulty is geometry, not just the {low_budget}-step budget.'], fill='#9ec5ff', font_size=13, line_height=18))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_late_tail_heatmap_svg(
    profiles: dict[int, list[LateTailTileRow]],
    *,
    output: str | Path,
    title: str | None = None,
    late_threshold: int = 20,
    max_iter: int = 40,
) -> None:
    if not profiles:
        raise ValueError("profiles must not be empty")

    ordered_powers = sorted(profiles)
    first_rows = profiles[ordered_powers[0]]
    if not first_rows:
        raise ValueError("profiles must contain non-empty rows")

    x_min = min(row.x_min for row in first_rows)
    x_max = max(row.x_max for row in first_rows)
    y_min = min(row.y_min for row in first_rows)
    y_max = max(row.y_max for row in first_rows)
    cols = max(row.tile_x for row in first_rows) + 1
    rows_per_panel = max(row.tile_y for row in first_rows) + 1

    page_width = 1180
    left = 58
    right = 42
    top = 116
    gap_x = 34
    gap_y = 30
    footer_h = 160
    card_w = (page_width - left - right - gap_x) / 2.0
    card_h = 432
    card_rows = (len(ordered_powers) + 1) // 2
    page_height = int(top + card_rows * card_h + max(0, card_rows - 1) * gap_y + footer_h)

    def map_x(map_left: float, map_size: float, value: float) -> float:
        return map_left + (value - x_min) / (x_max - x_min) * map_size

    def map_y(map_top: float, map_size: float, value: float) -> float:
        return map_top + (y_max - value) / (y_max - y_min) * map_size

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {page_width} {page_height}" width="{page_width}" height="{page_height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '  <linearGradient id="lateLegend" x1="0" y1="0" x2="1" y2="0">',
        f'    <stop offset="0%" stop-color="{_late_tail_hex(0.0)}"/>',
        f'    <stop offset="100%" stop-color="{_late_tail_hex(1.0)}"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="50" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Late-tail spatial map")}</text>',
        f'<text x="{left}" y="76" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">Each tile asks the same local question: what share of starts in this block still needs at least {late_threshold} steps, or never settles within the {max_iter}-step cutoff?</text>',
    ]

    for index, power in enumerate(ordered_powers):
        panel_col = index % 2
        panel_row = index // 2
        panel_left = left + panel_col * (card_w + gap_x)
        panel_top = top + panel_row * (card_h + gap_y)
        panel_rows = profiles[power]
        hottest = max(panel_rows, key=lambda row: row.late_fraction)
        grid_late = sum(row.sample_count * row.late_fraction for row in panel_rows) / sum(row.sample_count for row in panel_rows)
        grid_unresolved = sum(row.sample_count * row.unresolved_fraction for row in panel_rows) / sum(row.sample_count for row in panel_rows)
        center_rows = sorted(panel_rows, key=lambda row: abs(row.x_mid) + abs(row.y_mid))[:4]
        center_late = sum(row.late_fraction for row in center_rows) / len(center_rows)

        lines.append(f'<rect x="{panel_left}" y="{panel_top}" width="{card_w}" height="{card_h}" rx="20" fill="#020617" stroke="#334155" stroke-width="1.4"/>')
        lines.append(f'<text x="{panel_left + 22}" y="{panel_top + 34}" fill="#e5eefc" font-size="22" font-family="Helvetica, Arial, sans-serif" font-weight="700">z^{power} - 1</text>')
        lines.append(f'<text x="{panel_left + 22}" y="{panel_top + 56}" fill="#93c5fd" font-size="13" font-family="Helvetica, Arial, sans-serif">12×12 local blocks over the same sampled square</text>')

        map_left = panel_left + 24
        map_top = panel_top + 74
        map_size = 224
        lines.append(f'<rect x="{map_left}" y="{map_top}" width="{map_size}" height="{map_size}" rx="16" fill="#0b1320" stroke="#24324a" stroke-width="1.2"/>')
        axis_x = map_x(map_left, map_size, 0.0)
        axis_y = map_y(map_top, map_size, 0.0)
        unit_r = map_size * (1.0 / (x_max - x_min))
        lines.append(f'<line x1="{axis_x:.2f}" y1="{map_top + 8:.2f}" x2="{axis_x:.2f}" y2="{map_top + map_size - 8:.2f}" stroke="#dbeafe" stroke-width="1.1" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<line x1="{map_left + 8:.2f}" y1="{axis_y:.2f}" x2="{map_left + map_size - 8:.2f}" y2="{axis_y:.2f}" stroke="#dbeafe" stroke-width="1.1" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<circle cx="{axis_x:.2f}" cy="{axis_y:.2f}" r="{unit_r:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1.1" stroke-dasharray="6 5" opacity="0.55"/>')

        for row in panel_rows:
            x = map_x(map_left, map_size, row.x_min)
            y = map_y(map_top, map_size, row.y_max)
            w = (row.x_max - row.x_min) / (x_max - x_min) * map_size
            h = (row.y_max - row.y_min) / (y_max - y_min) * map_size
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w + 0.4:.2f}" height="{h + 0.4:.2f}" fill="{_late_tail_hex(row.late_fraction)}"/>')

        lines.append(f'<text x="{map_left}" y="{map_top + map_size + 24}" fill="#cbd5e1" font-size="12" font-family="Helvetica, Arial, sans-serif">Re(z₀)</text>')
        lines.append(f'<text x="{map_left - 10}" y="{map_top + map_size / 2:.2f}" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif" transform="rotate(-90 {map_left - 10} {map_top + map_size / 2:.2f})">Im(z₀)</text>')

        summary_x = panel_left + 24
        summary_y = map_top + map_size + 58
        lines.append(f'<text x="{summary_x}" y="{summary_y}" fill="#e5eefc" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">What changed</text>')
        lines.append(
            _paragraph(
                summary_x,
                summary_y + 28,
                [
                    f'grid late: {grid_late:.1%}',
                    f'center four tiles: {center_late:.1%}',
                    f'unresolved: {grid_unresolved:.1%}',
                ],
                fill='#cbd5e1',
                font_size=14,
                line_height=20,
            )
        )
        lines.append(f'<text x="{summary_x}" y="{summary_y + 112}" fill="#e5eefc" font-size="16" font-family="Helvetica, Arial, sans-serif" font-weight="700">Hottest tile</text>')
        lines.append(
            _paragraph(
                summary_x,
                summary_y + 138,
                [
                    f'{hottest.x_min:+.2f} ≤ Re(z₀) < {hottest.x_max:+.2f}',
                    f'{hottest.y_min:+.2f} ≤ Im(z₀) < {hottest.y_max:+.2f}',
                    f'late-tail share: {hottest.late_fraction:.1%}',
                ],
                fill='#fbd38d',
                font_size=14,
                line_height=20,
            )
        )
    legend_top = page_height - 118
    lines.append(f'<rect x="{left}" y="{legend_top - 28}" width="{page_width - left - right}" height="74" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top - 2}" fill="#e5eefc" font-size="16" font-family="Helvetica, Arial, sans-serif" font-weight="700">Legend</text>')
    lines.append(f'<rect x="{left + 18}" y="{legend_top + 12}" width="220" height="18" rx="9" fill="url(#lateLegend)" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top + 48}" fill="#cbd5e1" font-size="12" font-family="Helvetica, Arial, sans-serif">0%</text>')
    lines.append(f'<text x="{left + 238}" y="{legend_top + 48}" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">100%</text>')
    lines.append(_paragraph(left + 280, legend_top + 8, [f'Orange intensity = local late-tail share (≥ {late_threshold} steps or unresolved by {max_iter}).', 'Dashed circle marks the unit circle; dashed crosshairs mark the origin.'], fill='#dbeafe', font_size=13, line_height=18))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_late_tail_persistence_svg(
    low_tiles_by_power: dict[int, list[LateTailTileRow]],
    high_tiles_by_power: dict[int, list[LateTailTileRow]],
    comparison_rows: list[LateTailPersistenceRow],
    *,
    output: str | Path,
    title: str | None = None,
    low_budget: int = 40,
    high_budget: int = 80,
    low_threshold: int = 20,
    high_threshold: int = 40,
) -> None:
    if not comparison_rows:
        raise ValueError("comparison_rows must not be empty")

    ordered_powers = [row.power for row in sorted(comparison_rows, key=lambda row: row.power)]
    first_rows = low_tiles_by_power[ordered_powers[0]]
    x_min = min(row.x_min for row in first_rows)
    x_max = max(row.x_max for row in first_rows)
    y_min = min(row.y_min for row in first_rows)
    y_max = max(row.y_max for row in first_rows)

    width = 1520
    left = 54
    right = 42
    top = 118
    card_gap_x = 36
    card_gap_y = 30
    card_w = (width - left - right - card_gap_x) / 2.0
    card_h = 470
    footer_h = 148
    rows = (len(ordered_powers) + 1) // 2
    height = int(top + rows * card_h + max(0, rows - 1) * card_gap_y + footer_h)

    comparison_by_power = {row.power: row for row in comparison_rows}

    def map_x(map_left: float, map_size: float, value: float) -> float:
        return map_left + (value - x_min) / (x_max - x_min) * map_size

    def map_y(map_top: float, map_size: float, value: float) -> float:
        return map_top + (y_max - value) / (y_max - y_min) * map_size

    def append_tile_panel(lines: list[str], rows: list[LateTailTileRow], *, map_left: float, map_top: float, map_size: float, label: str) -> LateTailTileRow:
        lines.append(f'<text x="{map_left}" y="{map_top - 12}" fill="#dbeafe" font-size="15" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(label)}</text>')
        lines.append(f'<rect x="{map_left}" y="{map_top}" width="{map_size}" height="{map_size}" rx="16" fill="#0b1320" stroke="#24324a" stroke-width="1.2"/>')
        axis_x = map_x(map_left, map_size, 0.0)
        axis_y = map_y(map_top, map_size, 0.0)
        unit_r = map_size * (1.0 / (x_max - x_min))
        lines.append(f'<line x1="{axis_x:.2f}" y1="{map_top + 8:.2f}" x2="{axis_x:.2f}" y2="{map_top + map_size - 8:.2f}" stroke="#dbeafe" stroke-width="1.1" stroke-dasharray="5 5" opacity="0.58"/>')
        lines.append(f'<line x1="{map_left + 8:.2f}" y1="{axis_y:.2f}" x2="{map_left + map_size - 8:.2f}" y2="{axis_y:.2f}" stroke="#dbeafe" stroke-width="1.1" stroke-dasharray="5 5" opacity="0.58"/>')
        lines.append(f'<circle cx="{axis_x:.2f}" cy="{axis_y:.2f}" r="{unit_r:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1.1" stroke-dasharray="6 5" opacity="0.58"/>')
        hottest = max(rows, key=lambda row: row.late_fraction)
        for row in rows:
            x = map_x(map_left, map_size, row.x_min)
            y = map_y(map_top, map_size, row.y_max)
            w = (row.x_max - row.x_min) / (x_max - x_min) * map_size
            h = (row.y_max - row.y_min) / (y_max - y_min) * map_size
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w + 0.4:.2f}" height="{h + 0.4:.2f}" fill="{_late_tail_hex(row.late_fraction)}"/>')
        return hottest

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '  <linearGradient id="lateLegend" x1="0" y1="0" x2="1" y2="0">',
        f'    <stop offset="0%" stop-color="{_late_tail_hex(0.0)}"/>',
        f'    <stop offset="100%" stop-color="{_late_tail_hex(1.0)}"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Late-tail persistence atlas")}</text>',
        f'<text x="{left}" y="80" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">Each card asks the harder follow-up: after the old 40-step scouting pass, which tiles still need at least {high_threshold} Newton steps, or still miss even the {high_budget}-step cutoff?</text>',
    ]

    map_size = 232
    map_gap = 24
    for index, power in enumerate(ordered_powers):
        panel_col = index % 2
        panel_row = index // 2
        panel_left = left + panel_col * (card_w + card_gap_x)
        panel_top = top + panel_row * (card_h + card_gap_y)
        comparison = comparison_by_power[power]
        low_rows = low_tiles_by_power[power]
        high_rows = high_tiles_by_power[power]
        low_hottest = max(low_rows, key=lambda row: row.late_fraction)
        high_hottest = max(high_rows, key=lambda row: row.late_fraction)

        lines.append(f'<rect x="{panel_left}" y="{panel_top}" width="{card_w}" height="{card_h}" rx="20" fill="#020617" stroke="#334155" stroke-width="1.4"/>')
        lines.append(f'<text x="{panel_left + 22}" y="{panel_top + 34}" fill="#e5eefc" font-size="22" font-family="Helvetica, Arial, sans-serif" font-weight="700">z^{power} - 1</text>')

        map_left = panel_left + 22
        map_top = panel_top + 78
        low_label = f'≥ {low_threshold} steps or unresolved by {low_budget}'
        high_label = f'≥ {high_threshold} steps or unresolved by {high_budget}'
        append_tile_panel(lines, low_rows, map_left=map_left, map_top=map_top, map_size=map_size, label=low_label)
        append_tile_panel(lines, high_rows, map_left=map_left + map_size + map_gap, map_top=map_top, map_size=map_size, label=high_label)

        summary_x = panel_left + 22
        summary_y = map_top + map_size + 48
        lines.append(f'<text x="{summary_x}" y="{summary_y}" fill="#e5eefc" font-size="17" font-family="Helvetica, Arial, sans-serif" font-weight="700">Persistence summary</text>')
        lines.append(
            _paragraph(
                summary_x,
                summary_y + 26,
                [
                    f'grid late: {comparison.low_grid_late:.1%} → {comparison.high_grid_late:.1%}',
                    f'center four tiles: {comparison.low_center_late:.1%} → {comparison.high_center_late:.1%}',
                    f'grid retention: {comparison.grid_retained_fraction:.1%}',
                    f'center retention: {comparison.center_retained_fraction:.1%}',
                ],
                fill='#cbd5e1',
                font_size=14,
                line_height=20,
            )
        )
        lines.append(
            _paragraph(
                summary_x + 310,
                summary_y + 26,
                [
                    f'unresolved share: {comparison.low_unresolved_fraction:.1%} → {comparison.high_unresolved_fraction:.1%}',
                    f'low hottest tile: {low_hottest.late_fraction:.1%} at ({low_hottest.x_mid:+.2f}, {low_hottest.y_mid:+.2f})',
                    f'high hottest tile: {high_hottest.late_fraction:.1%} at ({high_hottest.x_mid:+.2f}, {high_hottest.y_mid:+.2f})',
                ],
                fill='#fbd38d',
                font_size=14,
                line_height=20,
            )
        )

        if comparison.high_center_late >= 0.95:
            callout = 'The hard center survives almost intact even after the budget doubles.'
        elif comparison.high_center_late <= 0.05:
            callout = 'The old late tail was mostly scouting-budget fog; the center cools away at the harder cutoff.'
        else:
            callout = 'Part of the old halo cools away, but a real slower core still survives.'
        lines.append(_paragraph(summary_x, summary_y + 126, [callout], fill='#93c5fd', font_size=13, line_height=18))

    legend_top = height - 112
    lines.append(f'<rect x="{left}" y="{legend_top - 26}" width="{width - left - right}" height="72" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top - 2}" fill="#e5eefc" font-size="16" font-family="Helvetica, Arial, sans-serif" font-weight="700">Legend</text>')
    lines.append(f'<rect x="{left + 18}" y="{legend_top + 12}" width="220" height="18" rx="9" fill="url(#lateLegend)" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top + 48}" fill="#cbd5e1" font-size="13" font-family="Helvetica, Arial, sans-serif">0%</text>')
    lines.append(f'<text x="{left + 238}" y="{legend_top + 48}" fill="#cbd5e1" font-size="13" text-anchor="end" font-family="Helvetica, Arial, sans-serif">100%</text>')
    lines.append(_paragraph(left + 280, legend_top + 8, [f'Orange intensity = local late-tail share. Left maps keep the old scouting read (≥ {low_threshold} steps or unresolved by {low_budget}); right maps ask what still survives at the harder read (≥ {high_threshold} steps or unresolved by {high_budget}).', 'Dashed circle marks the unit circle; dashed crosshairs mark the origin.'], fill='#dbeafe', font_size=14, line_height=18))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_cubic_comparison_svg(
    unity_polynomial: CubicPolynomial,
    unity_stats: CubicBasinStats,
    unity_samples,
    unity_rows: list[CriticalDistanceBandRow],
    asymmetric_polynomial: CubicPolynomial,
    asymmetric_stats: CubicBasinStats,
    asymmetric_samples,
    asymmetric_rows: list[CriticalDistanceBandRow],
    *,
    output: str | Path,
    title: str | None = None,
    max_iter: int = 40,
) -> None:
    width = 1480
    height = 1260
    panel_gap = 44
    top = 116
    map_size = 640
    left = 58
    map_left_2 = left + map_size + panel_gap
    chart_top = top + map_size + 92
    chart_width = 660
    chart_height = 320

    dominant_gap = max(asymmetric_stats.basin_shares) - max(unity_stats.basin_shares)
    unity_inner_late = unity_rows[0].late_fraction if unity_rows else 0.0
    asym_inner_late = asymmetric_rows[0].late_fraction if asymmetric_rows else 0.0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Breaking the cubic symmetry changes the critical picture")}</text>',
        '<text x="58" y="80" fill="#9ec5ff" font-size="17" font-family="Helvetica, Arial, sans-serif">Same square window, same Newton budget. The only change is the polynomial.</text>',
    ]

    _append_cubic_basin_panel(lines, unity_polynomial, unity_stats, unity_samples, left=left, top=top, size=map_size, max_iter=max_iter)
    _append_cubic_basin_panel(lines, asymmetric_polynomial, asymmetric_stats, asymmetric_samples, left=map_left_2, top=top, size=map_size, max_iter=max_iter)

    _append_critical_distance_chart(
        lines,
        title='Late tail by critical distance',
        subtitle='The unity cubic is hottest right on top of its repeated center critical point. The asymmetric cubic spreads that tension out and cools the core.',
        y_label='late fraction (≥10 steps)',
        left=left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        rows_a=unity_rows,
        rows_b=asymmetric_rows,
        value_getter=lambda row: row.late_fraction,
        y_range=(0.0, max(0.9, _max_value(unity_rows, asymmetric_rows, lambda row: row.late_fraction) * 1.12)),
    )
    _append_critical_distance_chart(
        lines,
        title='Dominant basin share by critical distance',
        subtitle='Symmetry breaking does not just move the critical set. It also lets one root own much more of the sampled square.',
        y_label='largest basin share in band',
        left=left + chart_width + panel_gap,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        rows_a=unity_rows,
        rows_b=asymmetric_rows,
        value_getter=lambda row: row.dominant_share,
        y_range=(0.28, 1.05),
        reference=1.0 / 3.0,
        reference_label='equal share = 1/3',
    )

    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_asymmetric_cubic_contrast_svg(
    first_polynomial: CubicPolynomial,
    first_stats: CubicBasinStats,
    first_samples,
    first_rows: list[CriticalDistanceBandRow],
    second_polynomial: CubicPolynomial,
    second_stats: CubicBasinStats,
    second_samples,
    second_rows: list[CriticalDistanceBandRow],
    *,
    output: str | Path,
    title: str | None = None,
    max_iter: int = 40,
) -> None:
    width = 1480
    height = 1260
    panel_gap = 44
    top = 116
    map_size = 640
    left = 58
    map_left_2 = left + map_size + panel_gap
    chart_top = top + map_size + 92
    chart_width = 660
    chart_height = 320

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Not every asymmetric cubic tells the same Newton story")}</text>',
        '<text x="58" y="80" fill="#9ec5ff" font-size="17" font-family="Helvetica, Arial, sans-serif">Both cubics break the unity-family symmetry. One turns into a winner-take-most square. The other keeps the critical competition near the center alive.</text>',
    ]

    _append_cubic_basin_panel(lines, first_polynomial, first_stats, first_samples, left=left, top=top, size=map_size, max_iter=max_iter)
    _append_cubic_basin_panel(lines, second_polynomial, second_stats, second_samples, left=map_left_2, top=top, size=map_size, max_iter=max_iter)

    _append_critical_distance_chart(
        lines,
        title='Late tail by critical distance',
        subtitle='The existing asymmetric cubic cools the core. The split-critical cubic keeps a much hotter near-critical lane instead of washing it out.',
        y_label='late fraction (≥10 steps)',
        left=left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        rows_a=first_rows,
        rows_b=second_rows,
        label_a=first_polynomial.name,
        label_b=second_polynomial.name,
        value_getter=lambda row: row.late_fraction,
        y_range=(0.0, max(0.9, _max_value(first_rows, second_rows, lambda row: row.late_fraction) * 1.12)),
    )
    _append_critical_distance_chart(
        lines,
        title='Dominant basin share by critical distance',
        subtitle='Breaking symmetry is not one story. One cubic lets a single root dominate. The split-critical cubic stays much closer to a three-way fight.',
        y_label='largest basin share in band',
        left=left + chart_width + panel_gap,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        rows_a=first_rows,
        rows_b=second_rows,
        label_a=first_polynomial.name,
        label_b=second_polynomial.name,
        value_getter=lambda row: row.dominant_share,
        y_range=(0.28, 1.05),
        reference=1.0 / 3.0,
        reference_label='equal share = 1/3',
    )

    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_cubic_budget_persistence_svg(
    *,
    unity_low_tiles: list[CubicLateTailTileRow],
    unity_high_tiles: list[CubicLateTailTileRow],
    asymmetric_low_tiles: list[CubicLateTailTileRow],
    asymmetric_high_tiles: list[CubicLateTailTileRow],
    unity_low_rows: list[CriticalDistanceBandRow],
    unity_high_rows: list[CriticalDistanceBandRow],
    asymmetric_low_rows: list[CriticalDistanceBandRow],
    asymmetric_high_rows: list[CriticalDistanceBandRow],
    low_budget: int,
    high_budget: int,
    late_threshold: int,
    output: str | Path,
    title: str | None = None,
) -> None:
    width = 1480
    height = 1460
    left = 58
    top = 116
    map_size = 280
    panel_gap_x = 40
    panel_gap_y = 34
    chart_top = top + 2 * map_size + panel_gap_y + 92
    chart_w = 660
    chart_h = 300

    def _panel_summary(rows: list[CubicLateTailTileRow]) -> tuple[float, float, float, CubicLateTailTileRow]:
        total = sum(row.sample_count for row in rows)
        grid_late = sum(row.sample_count * row.late_fraction for row in rows) / total
        center_rows = sorted(rows, key=lambda row: abs(row.x_mid) + abs(row.y_mid))[:4]
        center_late = sum(row.late_fraction for row in center_rows) / len(center_rows)
        unresolved = sum(row.sample_count * row.unresolved_fraction for row in rows) / total
        hottest = max(rows, key=lambda row: row.late_fraction)
        return grid_late, center_late, unresolved, hottest

    def _append_tile_panel(lines: list[str], rows: list[CubicLateTailTileRow], *, panel_left: float, panel_top: float, label: str) -> None:
        x_min = min(row.x_min for row in rows)
        x_max = max(row.x_max for row in rows)
        y_min = min(row.y_min for row in rows)
        y_max = max(row.y_max for row in rows)

        def map_x(value: float) -> float:
            return panel_left + (value - x_min) / (x_max - x_min) * map_size

        def map_y(value: float) -> float:
            return panel_top + (y_max - value) / (y_max - y_min) * map_size

        grid_late, center_late, unresolved, _ = _panel_summary(rows)
        axis_x = map_x(0.0)
        axis_y = map_y(0.0)
        unit_r = map_size * (1.0 / (x_max - x_min))

        lines.append(f'<rect x="{panel_left}" y="{panel_top}" width="{map_size}" height="{map_size}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<text x="{panel_left}" y="{panel_top - 20}" fill="#e5eefc" font-size="20" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(label)}</text>')
        lines.append(f'<line x1="{axis_x:.2f}" y1="{panel_top + 10:.2f}" x2="{axis_x:.2f}" y2="{panel_top + map_size - 10:.2f}" stroke="#dbeafe" stroke-width="1.0" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<line x1="{panel_left + 10:.2f}" y1="{axis_y:.2f}" x2="{panel_left + map_size - 10:.2f}" y2="{axis_y:.2f}" stroke="#dbeafe" stroke-width="1.0" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<circle cx="{axis_x:.2f}" cy="{axis_y:.2f}" r="{unit_r:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1.0" stroke-dasharray="6 5" opacity="0.55"/>')

        for row in rows:
            x = map_x(row.x_min)
            y = map_y(row.y_max)
            w = (row.x_max - row.x_min) / (x_max - x_min) * map_size
            h = (row.y_max - row.y_min) / (y_max - y_min) * map_size
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w + 0.4:.2f}" height="{h + 0.4:.2f}" fill="{_late_tail_hex(row.late_fraction)}"/>')

        lines.append(f'<text x="{panel_left}" y="{panel_top + map_size + 24}" fill="#cbd5e1" font-size="12" font-family="Helvetica, Arial, sans-serif">Re(z₀)</text>')
        lines.append(f'<text x="{panel_left - 10}" y="{panel_top + map_size / 2:.2f}" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif" transform="rotate(-90 {panel_left - 10} {panel_top + map_size / 2:.2f})">Im(z₀)</text>')
        lines.append(_paragraph(panel_left, panel_top + map_size + 48, [f'late {grid_late:.1%}', f'center {center_late:.1%} · unresolved {unresolved:.1%}'], fill='#cbd5e1', font_size=14, line_height=18))

    unity_low_grid, unity_low_center, unity_low_unresolved, _ = _panel_summary(unity_low_tiles)
    unity_high_grid, unity_high_center, unity_high_unresolved, _ = _panel_summary(unity_high_tiles)
    asym_low_grid, asym_low_center, asym_low_unresolved, _ = _panel_summary(asymmetric_low_tiles)
    asym_high_grid, asym_high_center, asym_high_unresolved, _ = _panel_summary(asymmetric_high_tiles)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '  <linearGradient id="lateLegend" x1="0" y1="0" x2="1" y2="0">',
        f'    <stop offset="0%" stop-color="{_late_tail_hex(0.0)}"/>',
        f'    <stop offset="100%" stop-color="{_late_tail_hex(1.0)}"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Cubic late-tail persistence")}</text>',
        f'<text x="{left}" y="80" fill="#9ec5ff" font-size="16" font-family="Helvetica, Arial, sans-serif">Late tiles mark starts that still need at least {late_threshold} steps, or never settle by the cutoff. The question is what stays hot after the cutoff rises.</text>',
    ]

    _append_tile_panel(lines, unity_low_tiles, panel_left=left, panel_top=top, label=f'unity cubic · {low_budget} steps')
    _append_tile_panel(lines, asymmetric_low_tiles, panel_left=left + map_size + panel_gap_x, panel_top=top, label=f'asymmetric cubic · {low_budget} steps')
    _append_tile_panel(lines, unity_high_tiles, panel_left=left, panel_top=top + map_size + panel_gap_y + 120, label=f'unity cubic · {high_budget} steps')
    _append_tile_panel(lines, asymmetric_high_tiles, panel_left=left + map_size + panel_gap_x, panel_top=top + map_size + panel_gap_y + 120, label=f'asymmetric cubic · {high_budget} steps')

    _append_critical_distance_chart(
        lines,
        title=f'near-critical tail at {low_budget} steps',
        subtitle='Low budget mixes real slow geometry with plain cutoff trouble.',
        y_label='tail-or-cutoff fraction',
        left=760,
        top=top,
        width=660,
        height=300,
        rows_a=unity_low_rows,
        rows_b=asymmetric_low_rows,
        value_getter=lambda row: row.late_fraction,
        y_range=(0.0, max(1.0, _max_value(unity_low_rows, asymmetric_low_rows, lambda row: row.late_fraction) * 1.08)),
    )
    _append_critical_distance_chart(
        lines,
        title=f'near-critical tail at {high_budget} steps',
        subtitle='The higher budget removes most cutoff noise. What survives is the geometric part.',
        y_label='tail fraction',
        left=760,
        top=top + 338,
        width=660,
        height=300,
        rows_a=unity_high_rows,
        rows_b=asymmetric_high_rows,
        value_getter=lambda row: row.late_fraction,
        y_range=(0.0, max(1.0, _max_value(unity_high_rows, asymmetric_high_rows, lambda row: row.late_fraction) * 1.08)),
    )

    summary_top = chart_top - 20
    lines.append(f'<rect x="760" y="{summary_top}" width="660" height="244" rx="20" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="782" y="{summary_top + 30}" fill="#e5eefc" font-size="21" font-family="Helvetica, Arial, sans-serif" font-weight="700">What survives when the cutoff rises</text>')
    lines.append(_paragraph(782, summary_top + 58, [
        f'unity cubic center-four tiles: {unity_low_center:.1%} → {unity_high_center:.1%}',
        f'asymmetric cubic center-four tiles: {asym_low_center:.1%} → {asym_high_center:.1%}',
        f'unity unresolved share: {unity_low_unresolved:.1%} → {unity_high_unresolved:.1%}',
        f'asymmetric unresolved share: {asym_low_unresolved:.1%} → {asym_high_unresolved:.1%}',
    ], fill='#cbd5e1', font_size=15, line_height=22))
    lines.append(_paragraph(782, summary_top + 158, [
        f'Unity stays hotter: grid late {unity_low_grid:.1%} → {unity_high_grid:.1%}.',
        f'Asymmetric cools harder: {asym_low_grid:.1%} → {asym_high_grid:.1%}.',
        'Some low-budget drama was cutoff noise, but the repeated center critical point still leaves the more persistent slow core.',
    ], fill='#9ec5ff', font_size=13, line_height=18))

    legend_top = height - 102
    lines.append(f'<rect x="{left}" y="{legend_top - 24}" width="{width - left - 42}" height="72" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<rect x="{left + 18}" y="{legend_top + 8}" width="220" height="18" rx="9" fill="url(#lateLegend)" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top + 44}" fill="#cbd5e1" font-size="12" font-family="Helvetica, Arial, sans-serif">0%</text>')
    lines.append(f'<text x="{left + 238}" y="{legend_top + 44}" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">100%</text>')
    lines.append(_paragraph(left + 280, legend_top + 6, [f'Orange intensity = local tail-or-cutoff share (≥ {late_threshold} steps or unresolved).', 'Dashed circle marks the unit circle; dashed crosshairs mark the origin.'], fill='#dbeafe', font_size=13, line_height=18))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_cubic_persistence_atlas_svg(
    *,
    low_tiles_by_slug: dict[str, list[CubicLateTailTileRow]],
    high_tiles_by_slug: dict[str, list[CubicLateTailTileRow]],
    comparison_rows: list[CubicBudgetComparisonRow],
    low_budget: int,
    high_budget: int,
    late_threshold: int,
    output: str | Path,
    title: str | None = None,
) -> None:
    width = 1900
    height = 1220
    left = 54
    top = 118
    map_size = 260
    col_gap = 32
    row_gap = 92
    summary_top = top + 2 * map_size + row_gap + 18
    summary_height = 268

    def _append_tile_panel(lines: list[str], rows: list[CubicLateTailTileRow], *, panel_left: float, panel_top: float, label: str) -> None:
        x_min = min(row.x_min for row in rows)
        x_max = max(row.x_max for row in rows)
        y_min = min(row.y_min for row in rows)
        y_max = max(row.y_max for row in rows)

        def map_x(value: float) -> float:
            return panel_left + (value - x_min) / (x_max - x_min) * map_size

        def map_y(value: float) -> float:
            return panel_top + (y_max - value) / (y_max - y_min) * map_size

        grid_late, center_late, unresolved = _summarize_cubic_tiles(rows)
        axis_x = map_x(0.0)
        axis_y = map_y(0.0)
        unit_r = map_size * (1.0 / (x_max - x_min))

        lines.append(f'<rect x="{panel_left}" y="{panel_top}" width="{map_size}" height="{map_size}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<text x="{panel_left}" y="{panel_top - 20}" fill="#e5eefc" font-size="19" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(label)}</text>')
        lines.append(f'<line x1="{axis_x:.2f}" y1="{panel_top + 10:.2f}" x2="{axis_x:.2f}" y2="{panel_top + map_size - 10:.2f}" stroke="#dbeafe" stroke-width="1.0" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<line x1="{panel_left + 10:.2f}" y1="{axis_y:.2f}" x2="{panel_left + map_size - 10:.2f}" y2="{axis_y:.2f}" stroke="#dbeafe" stroke-width="1.0" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<circle cx="{axis_x:.2f}" cy="{axis_y:.2f}" r="{unit_r:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1.0" stroke-dasharray="6 5" opacity="0.55"/>')

        for row in rows:
            x = map_x(row.x_min)
            y = map_y(row.y_max)
            w = (row.x_max - row.x_min) / (x_max - x_min) * map_size
            h = (row.y_max - row.y_min) / (y_max - y_min) * map_size
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w + 0.4:.2f}" height="{h + 0.4:.2f}" fill="{_late_tail_hex(row.late_fraction)}"/>')

        lines.append(_paragraph(panel_left, panel_top + map_size + 24, [f'grid {grid_late:.1%}', f'center {center_late:.1%} · unresolved {unresolved:.1%}'], fill='#cbd5e1', font_size=13, line_height=17))

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '  <linearGradient id="lateLegendAtlas" x1="0" y1="0" x2="1" y2="0">',
        f'    <stop offset="0%" stop-color="{_late_tail_hex(0.0)}"/>',
        f'    <stop offset="100%" stop-color="{_late_tail_hex(1.0)}"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Three cubic persistence atlas")}</text>',
        f'<text x="{left}" y="80" fill="#9ec5ff" font-size="16" font-family="Helvetica, Arial, sans-serif">Raise the Newton cutoff from {low_budget} to {high_budget} steps and ask what kind of slow geometry actually survives. Orange tiles still need at least {late_threshold} steps, or never settle by the cutoff.</text>',
    ]

    for index, row in enumerate(comparison_rows):
        panel_left = left + index * (map_size + col_gap)
        _append_tile_panel(lines, low_tiles_by_slug[row.polynomial_slug], panel_left=panel_left, panel_top=top, label=f'{row.polynomial_name} · {low_budget} steps')
        _append_tile_panel(lines, high_tiles_by_slug[row.polynomial_slug], panel_left=panel_left, panel_top=top + map_size + row_gap, label=f'{row.polynomial_name} · {high_budget} steps')

    summary_left = left + 3 * (map_size + col_gap) + 18
    summary_width = width - summary_left - 48
    lines.append(f'<rect x="{summary_left}" y="{top - 4}" width="{summary_width}" height="{summary_top + summary_height - top + 4}" rx="24" fill="#020617" stroke="#334155" stroke-width="1.4"/>')
    lines.append(f'<text x="{summary_left + 24}" y="{top + 24}" fill="#e5eefc" font-size="23" font-family="Helvetica, Arial, sans-serif" font-weight="700">What persists, and in what order</text>')

    y = top + 62
    for row in comparison_rows:
        lines.append(_paragraph(summary_left + 24, y, [
            row.polynomial_name,
            f'grid late {row.low_grid_late:.1%} → {row.high_grid_late:.1%}',
            f'center four {row.low_center_late:.1%} → {row.high_center_late:.1%} (retain {row.center_retained_fraction:.1%})',
            f'inner critical band {row.low_inner_band_late:.1%} → {row.high_inner_band_late:.1%} (retain {row.inner_band_retained_fraction:.1%})',
            f'unresolved {row.low_unresolved_fraction:.1%} → {row.high_unresolved_fraction:.1%}',
        ], fill='#cbd5e1', font_size=15, weight='700' if row.polynomial_slug == 'unity-cubic' else 'normal', line_height=22))
        y += 120

    lines.append(f'<text x="{summary_left + 24}" y="{summary_top + 24}" fill="#e5eefc" font-size="22" font-family="Helvetica, Arial, sans-serif" font-weight="700">Compact read</text>')
    hottest_center = max(comparison_rows, key=lambda row: row.high_center_late)
    coolest_center = min(comparison_rows, key=lambda row: row.high_center_late)
    strongest_retention = max(comparison_rows, key=lambda row: row.inner_band_retained_fraction)
    weakest_retention = min(comparison_rows, key=lambda row: row.inner_band_retained_fraction)
    lines.append(_paragraph(summary_left + 24, summary_top + 56, [
        f'The hottest surviving center is still {hottest_center.polynomial_name} at {hottest_center.high_center_late:.1%}.',
        f'The cleanest cooled center is {coolest_center.polynomial_name} at {coolest_center.high_center_late:.1%}.',
        f'The strongest near-critical retention is {strongest_retention.polynomial_name} at {strongest_retention.inner_band_retained_fraction:.1%} of its old tail share.',
        f'The weakest retention is {weakest_retention.polynomial_name} at {weakest_retention.inner_band_retained_fraction:.1%}.',
        'So the split-critical cubic really does land in a middle lane: less persistent than the unity singular core, much more persistent than the winner-take-most asymmetric cubic.',
    ], fill='#9ec5ff', font_size=15, line_height=22))

    legend_top = height - 94
    lines.append(f'<rect x="{left}" y="{legend_top - 28}" width="{width - left - 42}" height="76" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<rect x="{left + 18}" y="{legend_top + 6}" width="220" height="18" rx="9" fill="url(#lateLegendAtlas)" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top + 42}" fill="#cbd5e1" font-size="12" font-family="Helvetica, Arial, sans-serif">0%</text>')
    lines.append(f'<text x="{left + 238}" y="{legend_top + 42}" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">100%</text>')
    lines.append(_paragraph(left + 284, legend_top + 4, ['Orange intensity = local tail-or-cutoff share.', 'Dashed circle marks the unit circle; dashed crosshairs mark the origin. The useful difference is not just how much heat remains, but where it remains.'], fill='#dbeafe', font_size=13, line_height=18))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def render_asymmetric_cubic_opposition_svg(
    *,
    polynomials: list[CubicPolynomial],
    stats_by_slug: dict[str, CubicBasinStats],
    samples_by_slug: dict[str, list],
    tiles_by_slug: dict[str, list[CubicLateTailTileRow]],
    opposition_rows: list[CubicOppositionRow],
    output: str | Path,
    title: str | None = None,
    max_iter: int = 24,
    late_threshold: int = 10,
) -> None:
    width = 1900
    height = 1280
    left = 54
    top = 118
    map_size = 250
    col_gap = 30
    heat_top = top + 404
    summary_left = left + 3 * (map_size + col_gap) + 24
    summary_width = width - summary_left - 46

    polynomials_by_slug = {polynomial.slug: polynomial for polynomial in polynomials}
    display_names = {
        'asymmetric-cubic': 'winner-take-most',
        'split-critical-asymmetric-cubic': 'split-critical',
        'counterweight-asymmetric-cubic': 'counterweight',
    }

    def _append_compact_basin_panel(
        lines: list[str],
        polynomial: CubicPolynomial,
        stats: CubicBasinStats,
        samples,
        *,
        panel_left: float,
        panel_top: float,
        label: str,
    ) -> None:
        frame_top = panel_top
        cell_w = map_size / stats.width
        cell_h = map_size / stats.height
        lines.append(f'<text x="{panel_left}" y="{panel_top - 20}" fill="#e5eefc" font-size="20" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(label)}</text>')
        lines.append(f'<rect x="{panel_left}" y="{frame_top}" width="{map_size}" height="{map_size}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')

        for row in range(stats.height):
            start = row * stats.width
            row_samples = samples[start : start + stats.width]
            run_start = 0
            current_fill = _fill_for_cubic(row_samples[0], max_iter)
            for col in range(1, stats.width + 1):
                next_fill = _fill_for_cubic(row_samples[col], max_iter) if col < stats.width else None
                if next_fill != current_fill:
                    x = panel_left + run_start * cell_w
                    y = frame_top + row * cell_h
                    run_width = (col - run_start) * cell_w
                    lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{run_width:.2f}" height="{cell_h + 0.08:.2f}" fill="{current_fill}"/>')
                    run_start = col
                    current_fill = next_fill

        for index, root in enumerate(polynomial.roots):
            color = _cubic_palette(index)
            x = panel_left + (root.real - polynomial.x_min) / (polynomial.x_max - polynomial.x_min) * map_size
            y = frame_top + (polynomial.y_max - root.imag) / (polynomial.y_max - polynomial.y_min) * map_size
            x = min(max(x, panel_left + 14), panel_left + map_size - 14)
            y = min(max(y, frame_top + 14), frame_top + map_size - 14)
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="#f8fafc" stroke="{color}" stroke-width="3.2"/>')

        for point in cubic_critical_points(polynomial):
            x = panel_left + (point.real - polynomial.x_min) / (polynomial.x_max - polynomial.x_min) * map_size
            y = frame_top + (polynomial.y_max - point.imag) / (polynomial.y_max - polynomial.y_min) * map_size
            x = min(max(x, panel_left + 16), panel_left + map_size - 16)
            y = min(max(y, frame_top + 16), frame_top + map_size - 16)
            lines.append(f'<line x1="{x - 9:.2f}" y1="{y - 9:.2f}" x2="{x + 9:.2f}" y2="{y + 9:.2f}" stroke="#f8fafc" stroke-width="3.2"/>')
            lines.append(f'<line x1="{x + 9:.2f}" y1="{y - 9:.2f}" x2="{x - 9:.2f}" y2="{y + 9:.2f}" stroke="#f8fafc" stroke-width="3.2"/>')

        shares = ' / '.join(f'{100.0 * share:.0f}%' for share in stats.basin_shares)
        lines.append(_paragraph(panel_left, frame_top + map_size + 26, [f'shares {shares} · mean {stats.mean_iterations:.2f}'], fill='#f8fafc', font_size=15, line_height=19))

    def _append_heat_panel(
        lines: list[str],
        rows: list[CubicLateTailTileRow],
        summary: CubicOppositionRow,
        *,
        panel_left: float,
        panel_top: float,
        label: str,
    ) -> None:
        x_min = min(row.x_min for row in rows)
        x_max = max(row.x_max for row in rows)
        y_min = min(row.y_min for row in rows)
        y_max = max(row.y_max for row in rows)

        def map_x(value: float) -> float:
            return panel_left + (value - x_min) / (x_max - x_min) * map_size

        def map_y(value: float) -> float:
            return panel_top + (y_max - value) / (y_max - y_min) * map_size

        axis_x = map_x(0.0)
        axis_y = map_y(0.0)
        lines.append(f'<text x="{panel_left}" y="{panel_top - 20}" fill="#f8fafc" font-size="22" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(label)}</text>')
        lines.append(f'<rect x="{panel_left}" y="{panel_top}" width="{map_size}" height="{map_size}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
        lines.append(f'<line x1="{axis_x:.2f}" y1="{panel_top + 10:.2f}" x2="{axis_x:.2f}" y2="{panel_top + map_size - 10:.2f}" stroke="#dbeafe" stroke-width="1.0" stroke-dasharray="5 5" opacity="0.55"/>')
        lines.append(f'<line x1="{panel_left + 10:.2f}" y1="{axis_y:.2f}" x2="{panel_left + map_size - 10:.2f}" y2="{axis_y:.2f}" stroke="#dbeafe" stroke-width="1.0" stroke-dasharray="5 5" opacity="0.55"/>')

        for row in rows:
            x = map_x(row.x_min)
            y = map_y(row.y_max)
            w = (row.x_max - row.x_min) / (x_max - x_min) * map_size
            h = (row.y_max - row.y_min) / (y_max - y_min) * map_size
            lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w + 0.4:.2f}" height="{h + 0.4:.2f}" fill="{_late_tail_hex(row.late_fraction)}"/>')

        centroid_x = map_x(summary.late_tail_centroid_x)
        centroid_y = map_y(summary.late_tail_centroid_y)
        lines.append(f'<circle cx="{centroid_x:.2f}" cy="{centroid_y:.2f}" r="10" fill="#f8fafc" stroke="#f472b6" stroke-width="3.2"/>')
        lines.append(_paragraph(panel_left, panel_top + map_size + 26, [f'left {summary.left_late_share:.1%} · center {summary.center_late_share:.1%}', f'x̄ {summary.late_tail_centroid_x:+.2f} · ȳ {summary.late_tail_centroid_y:+.2f}'], fill='#f8fafc', font_size=15, line_height=19))

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#07111c"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '  <linearGradient id="lateLegendOpposition" x1="0" y1="0" x2="1" y2="0">',
        f'    <stop offset="0%" stop-color="{_late_tail_hex(0.0)}"/>',
        f'    <stop offset="100%" stop-color="{_late_tail_hex(1.0)}"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left}" y="52" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "A third asymmetric cubic can push the slow tail the other way")}</text>',
        f'<text x="{left}" y="82" fill="#b9dcff" font-size="18" font-family="Helvetica, Arial, sans-serif">The first two asymmetric cubics bent Newton geometry without inverting it. This third lane keeps the roots and critical set on the right, but most of the late-tail mass drifts left of the origin.</text>',
        f'<text x="{left}" y="{top - 44}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">Basin maps</text>',
        f'<text x="{left}" y="{heat_top - 44}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">Late-tail heatmaps at ≥ {late_threshold} steps</text>',
        f'<text x="{left + 210}" y="{top - 44}" fill="#dbeafe" font-size="14" font-family="Helvetica, Arial, sans-serif">○ roots · × critical points · ● late-tail centroid</text>',
    ]

    for index, summary in enumerate(opposition_rows):
        panel_left = left + index * (map_size + col_gap)
        slug = summary.polynomial_slug
        _append_compact_basin_panel(
            lines,
            polynomials_by_slug[slug],
            stats_by_slug[slug],
            samples_by_slug[slug],
            panel_left=panel_left,
            panel_top=top,
            label=display_names.get(slug, polynomials_by_slug[slug].name),
        )
        _append_heat_panel(
            lines,
            tiles_by_slug[slug],
            summary,
            panel_left=panel_left,
            panel_top=heat_top,
            label=display_names.get(slug, polynomials_by_slug[slug].name),
        )

    panel_top = top - 4
    panel_height = 1036
    lines.append(f'<rect x="{summary_left}" y="{panel_top}" width="{summary_width}" height="{panel_height}" rx="24" fill="#020617" stroke="#334155" stroke-width="1.4"/>')
    lines.append(f'<text x="{summary_left + 24}" y="{top + 24}" fill="#f8fafc" font-size="24" font-family="Helvetica, Arial, sans-serif" font-weight="700">Centroid opposition summary</text>')

    marker_left = summary_left + 24
    marker_top = top + 58
    marker_width = summary_width - 48
    marker_height = 330
    min_x = min(min(row.root_centroid_x, row.critical_centroid_x, row.late_tail_centroid_x) for row in opposition_rows)
    max_x = max(max(row.root_centroid_x, row.critical_centroid_x, row.late_tail_centroid_x) for row in opposition_rows)
    x_pad = max(0.18, 0.12 * (max_x - min_x))
    x_min = min(-0.6, min_x - x_pad)
    x_max = max(0.8, max_x + x_pad)

    def marker_x(value: float) -> float:
        return marker_left + (value - x_min) / (x_max - x_min) * marker_width

    lines.append(f'<rect x="{marker_left}" y="{marker_top}" width="{marker_width}" height="{marker_height}" rx="18" fill="#07111c" stroke="#334155" stroke-width="1.2"/>')
    lines.append(f'<text x="{marker_left + 18}" y="{marker_top + 28}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">x-position of the root centroid, critical centroid, and late-tail centroid</text>')
    origin_x = marker_x(0.0)
    lines.append(f'<line x1="{origin_x:.2f}" y1="{marker_top + 44:.2f}" x2="{origin_x:.2f}" y2="{marker_top + marker_height - 22:.2f}" stroke="#dbeafe" stroke-width="1.1" stroke-dasharray="6 5" opacity="0.75"/>')
    lines.append(f'<text x="{origin_x + 8:.2f}" y="{marker_top + 58:.2f}" fill="#dbeafe" font-size="12" font-family="Helvetica, Arial, sans-serif">origin</text>')
    for tick in range(6):
        value = x_min + (x_max - x_min) * tick / 5.0
        x = marker_x(value)
        lines.append(f'<line x1="{x:.2f}" y1="{marker_top + 44:.2f}" x2="{x:.2f}" y2="{marker_top + marker_height - 22:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{marker_top + marker_height - 2:.2f}" fill="#e2e8f0" font-size="14" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{value:+.2f}</text>')

    for index, row in enumerate(opposition_rows):
        y = marker_top + 94 + index * 86
        lines.append(f'<text x="{marker_left + 18}" y="{y + 5:.2f}" fill="#f8fafc" font-size="16" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(display_names.get(row.polynomial_slug, row.polynomial_name))}</text>')
        root_x = marker_x(row.root_centroid_x)
        critical_x = marker_x(row.critical_centroid_x)
        late_x = marker_x(row.late_tail_centroid_x)
        lines.append(f'<line x1="{min(root_x, late_x):.2f}" y1="{y:.2f}" x2="{max(root_x, late_x):.2f}" y2="{y:.2f}" stroke="#64748b" stroke-width="2.2"/>')
        lines.append(f'<circle cx="{root_x:.2f}" cy="{y:.2f}" r="8.5" fill="#f8fafc" stroke="#34d399" stroke-width="3.2"/>')
        lines.append(f'<circle cx="{critical_x:.2f}" cy="{y:.2f}" r="8.5" fill="#f8fafc" stroke="#f59e0b" stroke-width="3.2"/>')
        lines.append(f'<circle cx="{late_x:.2f}" cy="{y:.2f}" r="8.5" fill="#f8fafc" stroke="#f472b6" stroke-width="3.2"/>')
        lines.append(f'<text x="{marker_left + marker_width - 18}" y="{y + 5:.2f}" fill="#f8fafc" font-size="15" text-anchor="end" font-family="Helvetica, Arial, sans-serif">late x {row.late_tail_centroid_x:+.2f}</text>')

    lines.append('<g font-family="Helvetica, Arial, sans-serif" font-size="13">')
    legend_y = marker_top + marker_height - 42
    lines.append(f'<circle cx="{marker_left + 28}" cy="{legend_y:.2f}" r="7" fill="#f8fafc" stroke="#34d399" stroke-width="3"/><text x="{marker_left + 44}" y="{legend_y + 4:.2f}" fill="#dbeafe">root centroid x</text>')
    lines.append(f'<circle cx="{marker_left + 220}" cy="{legend_y:.2f}" r="7" fill="#f8fafc" stroke="#f59e0b" stroke-width="3"/><text x="{marker_left + 236}" y="{legend_y + 4:.2f}" fill="#dbeafe">critical centroid x</text>')
    lines.append(f'<circle cx="{marker_left + 442}" cy="{legend_y:.2f}" r="7" fill="#f8fafc" stroke="#f472b6" stroke-width="3"/><text x="{marker_left + 458}" y="{legend_y + 4:.2f}" fill="#dbeafe">late-tail centroid x</text>')
    lines.append('</g>')

    bar_left = summary_left + 24
    bar_top = marker_top + marker_height + 36
    bar_width = summary_width - 48
    bar_height = 250
    bar_max = max(0.75, max(row.left_late_share for row in opposition_rows) * 1.12)
    bar_axis_left = bar_left + 180
    bar_axis_width = bar_width - 198

    def bar_x(value: float) -> float:
        return bar_axis_left + (value / bar_max) * bar_axis_width

    lines.append(f'<rect x="{bar_left}" y="{bar_top}" width="{bar_width}" height="{bar_height}" rx="18" fill="#07111c" stroke="#334155" stroke-width="1.2"/>')
    lines.append(f'<text x="{bar_left + 18}" y="{bar_top + 28}" fill="#cbd5e1" font-size="15" font-family="Helvetica, Arial, sans-serif">where the late mass actually lives</text>')
    for tick in range(5):
        value = bar_max * tick / 4.0
        x = bar_x(value)
        lines.append(f'<line x1="{x:.2f}" y1="{bar_top + 44:.2f}" x2="{x:.2f}" y2="{bar_top + bar_height - 22:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{bar_top + bar_height - 2:.2f}" fill="#e2e8f0" font-size="14" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{value:.2f}</text>')

    for index, row in enumerate(opposition_rows):
        y = bar_top + 84 + index * 56
        lines.append(f'<text x="{bar_left + 18}" y="{y - 10:.2f}" fill="#f8fafc" font-size="15" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(display_names.get(row.polynomial_slug, row.polynomial_name))}</text>')
        lines.append(f'<rect x="{bar_axis_left}" y="{y - 18:.2f}" width="{bar_x(row.left_late_share) - bar_axis_left:.2f}" height="14" rx="7" fill="#60a5fa"/>')
        lines.append(f'<rect x="{bar_axis_left}" y="{y + 4:.2f}" width="{bar_x(row.center_late_share) - bar_axis_left:.2f}" height="14" rx="7" fill="#f97316"/>')
        lines.append(f'<text x="{bar_left + 186}" y="{y - 6:.2f}" fill="#dbeafe" font-size="14" font-family="Helvetica, Arial, sans-serif">left half {row.left_late_share:.1%}</text>')
        lines.append(f'<text x="{bar_left + 186}" y="{y + 16:.2f}" fill="#fed7aa" font-size="14" font-family="Helvetica, Arial, sans-serif">center square {row.center_late_share:.1%}</text>')

    flipped = next((row for row in opposition_rows if row.root_centroid_x * row.late_tail_centroid_x < 0.0), max(opposition_rows, key=lambda row: abs(row.root_centroid_x - row.late_tail_centroid_x)))
    strongest_left = max(opposition_rows, key=lambda row: row.left_late_share)
    most_center = max(opposition_rows, key=lambda row: row.center_late_share)
    text_top = bar_top + bar_height + 36
    lines.append(f'<text x="{summary_left + 24}" y="{text_top}" fill="#e5eefc" font-size="22" font-family="Helvetica, Arial, sans-serif" font-weight="700">Compact read</text>')
    lines.append(_paragraph(summary_left + 24, text_top + 34, [
        f'{display_names.get(flipped.polynomial_slug, flipped.polynomial_name).title()}: root x {flipped.root_centroid_x:+.2f}, critical x {flipped.critical_centroid_x:+.2f}, late x {flipped.late_tail_centroid_x:+.2f}.',
        f'Late mass: {strongest_left.left_late_share:.1%} in the left half, only {flipped.center_late_share:.1%} in the center box.',
        f'This is the third asymmetric story: winner-take-most, split-critical, and now a real counterweight lane.',
    ], fill='#b9dcff', font_size=17, line_height=25))

    legend_top = height - 100
    lines.append(f'<rect x="{left}" y="{legend_top - 26}" width="{width - left - 42}" height="74" rx="16" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<rect x="{left + 18}" y="{legend_top + 6}" width="220" height="18" rx="9" fill="url(#lateLegendOpposition)" stroke="#475569" stroke-width="1"/>')
    lines.append(f'<text x="{left + 18}" y="{legend_top + 42}" fill="#cbd5e1" font-size="12" font-family="Helvetica, Arial, sans-serif">0%</text>')
    lines.append(f'<text x="{left + 238}" y="{legend_top + 42}" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">100%</text>')
    lines.append(_paragraph(left + 282, legend_top + 2, [f'Orange = local late-tail share (≥ {late_threshold} steps or unresolved by {max_iter}).', 'White circles = roots, white × = critical points, pink dot = late-tail centroid.'], fill='#dbeafe', font_size=14, line_height=19))
    lines.append('</svg>')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def _summarize_cubic_tiles(rows: list[CubicLateTailTileRow]) -> tuple[float, float, float]:
    total = sum(row.sample_count for row in rows)
    grid_late = sum(row.sample_count * row.late_fraction for row in rows) / total
    center_rows = sorted(rows, key=lambda row: abs(row.x_mid) + abs(row.y_mid))[:4]
    center_late = sum(row.late_fraction for row in center_rows) / len(center_rows)
    unresolved = sum(row.sample_count * row.unresolved_fraction for row in rows) / total
    return grid_late, center_late, unresolved


def _append_cubic_basin_panel(lines: list[str], polynomial: CubicPolynomial, stats: CubicBasinStats, samples, *, left: float, top: float, size: float, max_iter: int) -> None:
    frame_top = top + 44
    cell_w = size / stats.width
    cell_h = size / stats.height

    lines.append(f'<text x="{left}" y="{top + 2}" fill="#e5eefc" font-size="22" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(polynomial.name)}</text>')
    lines.append(f'<text x="{left}" y="{top + 26}" fill="#9ec5ff" font-size="16" font-family="Helvetica, Arial, sans-serif">roots ○, critical points ×, same square window</text>')
    lines.append(f'<rect x="{left}" y="{frame_top}" width="{size}" height="{size}" rx="18" fill="#020617" stroke="#334155" stroke-width="1.3"/>')

    for row in range(stats.height):
        start = row * stats.width
        row_samples = samples[start : start + stats.width]
        run_start = 0
        current_fill = _fill_for_cubic(row_samples[0], max_iter)
        for col in range(1, stats.width + 1):
            next_fill = _fill_for_cubic(row_samples[col], max_iter) if col < stats.width else None
            if next_fill != current_fill:
                x = left + run_start * cell_w
                y = frame_top + row * cell_h
                run_width = (col - run_start) * cell_w
                lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{run_width:.2f}" height="{cell_h + 0.08:.2f}" fill="{current_fill}"/>')
                run_start = col
                current_fill = next_fill

    for index, root in enumerate(polynomial.roots):
        color = _cubic_palette(index)
        x = left + (root.real - polynomial.x_min) / (polynomial.x_max - polynomial.x_min) * size
        y = frame_top + (polynomial.y_max - root.imag) / (polynomial.y_max - polynomial.y_min) * size
        x = min(max(x, left + 14), left + size - 14)
        y = min(max(y, frame_top + 14), frame_top + size - 14)
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="#f8fafc" stroke="{color}" stroke-width="3.2"/>')

    for point in cubic_critical_points(polynomial):
        x = left + (point.real - polynomial.x_min) / (polynomial.x_max - polynomial.x_min) * size
        y = frame_top + (polynomial.y_max - point.imag) / (polynomial.y_max - polynomial.y_min) * size
        x = min(max(x, left + 16), left + size - 16)
        y = min(max(y, frame_top + 16), frame_top + size - 16)
        lines.append(f'<line x1="{x - 9:.2f}" y1="{y - 9:.2f}" x2="{x + 9:.2f}" y2="{y + 9:.2f}" stroke="#f8fafc" stroke-width="3"/>')
        lines.append(f'<line x1="{x + 9:.2f}" y1="{y - 9:.2f}" x2="{x - 9:.2f}" y2="{y + 9:.2f}" stroke="#f8fafc" stroke-width="3"/>')

    late_fraction = sum(1 for sample in samples if sample.iterations >= 10) / len(samples)
    shares = ' / '.join(f'{share:.1%}' for share in stats.basin_shares)
    lines.append(f'<text x="{left}" y="{frame_top + size + 32}" fill="#e2e8f0" font-size="18" font-family="Helvetica, Arial, sans-serif">mean {stats.mean_iterations:.2f} · late tail {late_fraction:.1%} · shares {shares}</text>')


def _append_critical_distance_chart(
    lines: list[str],
    *,
    title: str,
    subtitle: str,
    y_label: str,
    left: float,
    top: float,
    width: float,
    height: float,
    rows_a: list[CriticalDistanceBandRow],
    rows_b: list[CriticalDistanceBandRow],
    value_getter,
    y_range: tuple[float, float],
    reference: float | None = None,
    reference_label: str | None = None,
    label_a: str = 'unity cubic',
    label_b: str = 'asymmetric cubic',
    color_a: str = '#60a5fa',
    color_b: str = '#f59e0b',
) -> None:
    pad_left = 84
    pad_right = 42
    subtitle_lines = _wrap_svg_lines(subtitle, width=max(44, int((width - pad_left - pad_right) / 8.6)))
    plot_top = top + 78 + max(0, len(subtitle_lines) - 1) * 18
    plot_bottom = top + height - 54
    plot_left = left + pad_left
    plot_right = left + width - pad_right
    x_max = max([row.distance_mid for row in rows_a + rows_b if row.sample_count > 0] or [1.0])
    y_min, y_max = y_range

    def x_for(value: float) -> float:
        return plot_left + (value / x_max) * (plot_right - plot_left) if x_max > 0 else (plot_left + plot_right) / 2.0

    def y_for(value: float) -> float:
        if y_max == y_min:
            return (plot_top + plot_bottom) / 2.0
        return plot_bottom - (value - y_min) / (y_max - y_min) * (plot_bottom - plot_top)

    lines.append(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" rx="20" fill="#020617" stroke="#334155" stroke-width="1.3"/>')
    lines.append(f'<text x="{left + 18}" y="{top + 30}" fill="#e5eefc" font-size="21" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title)}</text>')
    for index, line in enumerate(subtitle_lines):
        lines.append(f'<text x="{left + 18}" y="{top + 56 + index * 18}" fill="#9ec5ff" font-size="14" font-family="Helvetica, Arial, sans-serif">{_escape(line)}</text>')

    for tick in range(5):
        frac = tick / 4
        y_value = y_min + frac * (y_max - y_min)
        y = y_for(y_value)
        lines.append(f'<line x1="{plot_left:.2f}" y1="{y:.2f}" x2="{plot_right:.2f}" y2="{y:.2f}" stroke="#1f2937" stroke-width="1"/>')
        lines.append(f'<text x="{plot_left - 12:.2f}" y="{y + 4:.2f}" fill="#cbd5e1" font-size="15" font-weight="600" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{y_value:.2f}</text>')

    for tick in range(5):
        frac = tick / 4
        x_value = frac * x_max
        x = x_for(x_value)
        lines.append(f'<line x1="{x:.2f}" y1="{plot_top:.2f}" x2="{x:.2f}" y2="{plot_bottom:.2f}" stroke="#16202f" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{plot_bottom + 24:.2f}" fill="#cbd5e1" font-size="15" font-weight="600" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{x_value:.2f}</text>')

    if reference is not None:
        reference_y = y_for(reference)
        lines.append(f'<line x1="{plot_left:.2f}" y1="{reference_y:.2f}" x2="{plot_right:.2f}" y2="{reference_y:.2f}" stroke="#e2e8f0" stroke-width="1.6" stroke-dasharray="7 6"/>')
        if reference_label:
            lines.append(f'<text x="{plot_right - 18:.2f}" y="{reference_y - 7:.2f}" fill="#e2e8f0" font-size="13" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{_escape(reference_label)}</text>')

    _append_chart_series(lines, rows_a, x_for=x_for, y_for=y_for, value_getter=value_getter, color=color_a)
    _append_chart_series(lines, rows_b, x_for=x_for, y_for=y_for, value_getter=value_getter, color=color_b)

    lines.append(f'<text x="{(plot_left + plot_right) / 2:.2f}" y="{top + height - 14:.2f}" fill="#cbd5e1" font-size="15" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">distance to nearest critical point</text>')

    legend_y = top + height - 90
    lines.append(f'<line x1="{left + 20}" y1="{legend_y}" x2="{left + 48}" y2="{legend_y}" stroke="{color_a}" stroke-width="3"/>')
    lines.append(f'<text x="{left + 56}" y="{legend_y + 4}" fill="#dbeafe" font-size="16" font-family="Helvetica, Arial, sans-serif">{_escape(label_a)}</text>')
    lines.append(f'<line x1="{left + 332}" y1="{legend_y}" x2="{left + 360}" y2="{legend_y}" stroke="{color_b}" stroke-width="3"/>')
    lines.append(f'<text x="{left + 368}" y="{legend_y + 4}" fill="#dbeafe" font-size="16" font-family="Helvetica, Arial, sans-serif">{_escape(label_b)}</text>')


def _append_chart_series(lines: list[str], rows: list[CriticalDistanceBandRow], *, x_for, y_for, value_getter, color: str) -> None:
    valid_rows = [row for row in rows if row.sample_count > 0]
    if not valid_rows:
        return
    points = ' '.join(f'{x_for(row.distance_mid):.2f},{y_for(value_getter(row)):.2f}' for row in valid_rows)
    lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{points}"/>')
    for row in valid_rows:
        x = x_for(row.distance_mid)
        y = y_for(value_getter(row))
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="#dbeafe" stroke="{color}" stroke-width="2"/>')


def _wrap_svg_lines(text: str, *, width: int) -> list[str]:
    lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    return lines or [text]


def _max_value(unity_rows: list[CriticalDistanceBandRow], asymmetric_rows: list[CriticalDistanceBandRow], getter) -> float:
    return max([getter(row) for row in unity_rows + asymmetric_rows if row.sample_count > 0] or [1.0])


def _late_tail_hex(fraction: float) -> str:
    fraction = max(0.0, min(fraction, 1.0))
    start = (11, 19, 32)
    end = (249, 115, 22)
    red = int(start[0] + (end[0] - start[0]) * fraction)
    green = int(start[1] + (end[1] - start[1]) * fraction)
    blue = int(start[2] + (end[2] - start[2]) * fraction)
    return f'#{red:02x}{green:02x}{blue:02x}'


def _cubic_palette(index: int) -> str:
    return ["#60a5fa", "#f59e0b", "#c084fc"][index % 3]


def _fill_for_cubic(sample, max_iter: int) -> str:
    if sample.root_index is None:
        return '#020617'
    base = _cubic_palette(sample.root_index)
    speed = 1.0 - min(sample.iterations, max_iter) / max_iter
    return _shade_hex(base, 0.34 + 0.66 * speed)


def _shade_hex(color: str, factor: float) -> str:
    factor = max(0.0, min(factor, 1.0))
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    red = int(red * factor)
    green = int(green * factor)
    blue = int(blue * factor)
    return f'#{red:02x}{green:02x}{blue:02x}'


def export_png_from_svg(svg_path: str | Path, png_path: str | Path, *, size: int = 1800, dpi: int = 300) -> bool:
    svg_file = Path(svg_path).resolve()
    png_file = Path(png_path).resolve()
    qlmanage = shutil.which('qlmanage')
    if qlmanage is None:
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        padded_svg = _square_pad_svg_for_quicklook(svg_file, Path(tmpdir) / svg_file.name)
        subprocess.run(
            [qlmanage, '-t', '-s', str(size), '-o', tmpdir, str(padded_svg)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        generated = Path(tmpdir) / f'{padded_svg.name}.png'
        if not generated.exists():
            raise FileNotFoundError(f'Quick Look did not generate {generated}')
        png_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generated, png_file)

    sips = shutil.which('sips')
    if sips is not None:
        subprocess.run(
            [sips, '--setProperty', 'dpiWidth', str(dpi), '--setProperty', 'dpiHeight', str(dpi), str(png_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return True


def _square_pad_svg_for_quicklook(svg_file: Path, destination: Path) -> Path:
    tree = ET.parse(svg_file)
    root = tree.getroot()
    width = float(root.attrib.get('width', root.attrib['viewBox'].split()[2]))
    height = float(root.attrib.get('height', root.attrib['viewBox'].split()[3]))
    if abs(width - height) < 1.0e-9:
        tree.write(destination, encoding='utf-8', xml_declaration=False)
        return destination

    square = int(max(width, height))
    root.set('width', str(square))
    root.set('height', str(square))
    root.set('viewBox', f'0 0 {square} {square}')
    tree.write(destination, encoding='utf-8', xml_declaration=False)
    return destination


def _fill_for(sample, power: int, max_iter: int) -> str:
    if sample.root_index is None:
        return '#020617'
    hue = sample.root_index / power
    speed = 1.0 - min(sample.iterations, max_iter) / max_iter
    value = 0.28 + 0.62 * speed
    saturation = 0.55 + 0.30 * speed
    return _root_hex(hue, value, saturation)


def _root_hex(hue: float, value: float, saturation: float = 0.78) -> str:
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


def _fmt_complex(z: complex) -> str:
    return f'{z.real:+.3f} {z.imag:+.3f}i'


def _escape(text: str) -> str:
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )
