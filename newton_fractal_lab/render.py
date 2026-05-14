from __future__ import annotations

import colorsys
from pathlib import Path

from .core import PowerScanRow, basin_summary, sample_grid, unity_roots


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

    frame_left = 36
    frame_top = 90
    frame_size = 640
    cell_w = frame_size / width
    cell_h = frame_size / height
    svg_width = 720
    svg_height = 790

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#060814"/>',
        '    <stop offset="100%" stop-color="#111827"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="36" y="48" fill="#e5eefc" font-size="30" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or f"Newton fractal for z^{power} - 1")}</text>',
        '<text x="36" y="74" fill="#9ec5ff" font-size="15" font-family="Helvetica, Arial, sans-serif">Each basin shows which root Newton iteration finds. Darker cells converged faster.</text>',
        f'<rect x="{frame_left}" y="{frame_top}" width="{frame_size}" height="{frame_size}" rx="16" fill="#020617" stroke="#2b3752" stroke-width="1.5"/>',
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
        swatch_y = 748 - (power - idx - 1) * 22
        lines.append(f'<rect x="500" y="{swatch_y - 12}" width="16" height="16" rx="4" fill="{_root_hex(hue, 0.88)}"/>')
        lines.append(
            f'<text x="524" y="{swatch_y}" font-size="13">root {idx}: {_fmt_complex(root)}</text>'
        )
    lines.append('</g>')

    lines.append(
        f'<text x="36" y="754" fill="#cbd5e1" font-size="14" font-family="Helvetica, Arial, sans-serif">grid: {width}×{height} · mean iterations: {stats.mean_iterations:.2f} · converged: {stats.converged_points}/{stats.total_points}</text>'
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
    height = 760
    left = 72
    right = 34
    top = 100
    panel_gap = 46
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

    legend_y = height - 72
    lines.append('<g font-family="Helvetica, Arial, sans-serif" font-size="13">')
    lines.append(f'<line x1="{left}" y1="{legend_y}" x2="{left + 28}" y2="{legend_y}" stroke="#60a5fa" stroke-width="3"/><text x="{left + 36}" y="{legend_y + 4}" fill="#dbeafe">mean iterations</text>')
    lines.append(f'<line x1="{left + 180}" y1="{legend_y}" x2="{left + 208}" y2="{legend_y}" stroke="#38bdf8" stroke-width="2.5"/><text x="{left + 216}" y="{legend_y + 4}" fill="#dbeafe">converged fraction</text>')
    lines.append(f'<line x1="{left + 398}" y1="{legend_y}" x2="{left + 426}" y2="{legend_y}" stroke="#f8fafc" stroke-width="1.8" stroke-dasharray="6 5"/><text x="{left + 434}" y="{legend_y + 4}" fill="#dbeafe">ideal equal share 1/n</text>')
    lines.append(f'<line x1="{left + 630}" y1="{legend_y - 8}" x2="{left + 630}" y2="{legend_y + 8}" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/><text x="{left + 644}" y="{legend_y + 4}" fill="#dbeafe">min to max basin share</text>')
    lines.append('</g>')
    lines.append('</svg>')

    output.write_text("\n".join(lines) + "\n")


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
