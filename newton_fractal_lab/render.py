from __future__ import annotations

import colorsys
from pathlib import Path

from .core import basin_summary, sample_grid, unity_roots


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
