from __future__ import annotations

import colorsys
from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile

from .core import IterationHistogram, PowerScanRow, RadiusBandRow, basin_summary, sample_grid, unity_roots


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


def export_png_from_svg(svg_path: str | Path, png_path: str | Path, *, size: int = 1800, dpi: int = 300) -> bool:
    svg_file = Path(svg_path).resolve()
    png_file = Path(png_path).resolve()
    qlmanage = shutil.which('qlmanage')
    if qlmanage is None:
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [qlmanage, '-t', '-s', str(size), '-o', tmpdir, str(svg_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        generated = Path(tmpdir) / f'{svg_file.name}.png'
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
