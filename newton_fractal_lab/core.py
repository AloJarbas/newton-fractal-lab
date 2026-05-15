from __future__ import annotations

from dataclasses import dataclass
import cmath
import math


@dataclass(frozen=True)
class NewtonResult:
    start: complex
    end: complex
    iterations: int
    converged: bool
    stalled: bool
    root_index: int | None
    residual: float


@dataclass(frozen=True)
class BasinStats:
    power: int
    width: int
    height: int
    converged_points: int
    stalled_points: int
    mean_iterations: float
    basin_counts: tuple[int, ...]

    @property
    def total_points(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class PowerScanRow:
    power: int
    mean_iterations: float
    converged_fraction: float
    stalled_fraction: float
    min_share: float
    max_share: float


@dataclass(frozen=True)
class RadiusBandRow:
    power: int
    radius_min: float
    radius_max: float
    sample_count: int
    mean_iterations: float
    converged_fraction: float
    stalled_fraction: float


@dataclass(frozen=True)
class IterationHistogram:
    power: int
    max_iter: int
    total_points: int
    converged_counts: tuple[int, ...]
    stalled_count: int
    unresolved_count: int

    def cumulative_converged_fraction(self, iterations: int) -> float:
        clipped = max(0, min(iterations, self.max_iter))
        return sum(self.converged_counts[: clipped + 1]) / self.total_points

    def tail_fraction(self, min_iterations: int) -> float:
        clipped = max(0, min(min_iterations, self.max_iter))
        tail = sum(self.converged_counts[clipped:]) + self.stalled_count + self.unresolved_count
        return tail / self.total_points


def unity_roots(power: int) -> list[complex]:
    if power < 2:
        raise ValueError("power must be at least 2")
    return [cmath.rect(1.0, 2.0 * math.pi * k / power) for k in range(power)]


def iterate_unity(
    start: complex,
    power: int,
    *,
    max_iter: int = 40,
    tol: float = 1e-8,
    derivative_tol: float = 1e-12,
) -> NewtonResult:
    if power < 2:
        raise ValueError("power must be at least 2")
    if max_iter < 1:
        raise ValueError("max_iter must be positive")

    z = start
    roots = unity_roots(power)

    for step in range(1, max_iter + 1):
        fz = z**power - 1.0
        residual = abs(fz)
        if residual <= tol:
            root_index = _nearest_root_index(z, roots)
            return NewtonResult(start, z, step - 1, True, False, root_index, residual)

        derivative = power * z ** (power - 1)
        if abs(derivative) <= derivative_tol:
            return NewtonResult(start, z, step - 1, False, True, None, residual)

        z = z - fz / derivative

    residual = abs(z**power - 1.0)
    root_index = _nearest_root_index(z, roots) if residual <= 1e-4 else None
    return NewtonResult(start, z, max_iter, residual <= tol, False, root_index, residual)


def sample_grid(
    power: int,
    width: int,
    height: int,
    *,
    x_min: float = -1.6,
    x_max: float = 1.6,
    y_min: float = -1.6,
    y_max: float = 1.6,
    max_iter: int = 40,
) -> list[NewtonResult]:
    if width < 2 or height < 2:
        raise ValueError("width and height must both be at least 2")

    samples: list[NewtonResult] = []
    for j in range(height):
        y = y_max - (y_max - y_min) * j / (height - 1)
        for i in range(width):
            x = x_min + (x_max - x_min) * i / (width - 1)
            samples.append(iterate_unity(complex(x, y), power, max_iter=max_iter))
    return samples


def basin_summary(power: int, width: int, height: int, samples: list[NewtonResult]) -> BasinStats:
    if len(samples) != width * height:
        raise ValueError("sample count does not match width * height")

    basin_counts = [0] * power
    converged_points = 0
    stalled_points = 0
    total_iterations = 0

    for sample in samples:
        total_iterations += sample.iterations
        if sample.stalled:
            stalled_points += 1
        if sample.converged and sample.root_index is not None:
            converged_points += 1
            basin_counts[sample.root_index] += 1

    mean_iterations = total_iterations / len(samples)
    return BasinStats(
        power=power,
        width=width,
        height=height,
        converged_points=converged_points,
        stalled_points=stalled_points,
        mean_iterations=mean_iterations,
        basin_counts=tuple(basin_counts),
    )


def scan_unity_family(
    power_min: int,
    power_max: int,
    *,
    width: int = 120,
    height: int = 120,
    max_iter: int = 40,
) -> list[PowerScanRow]:
    if power_min > power_max:
        raise ValueError("power_min must be less than or equal to power_max")

    rows: list[PowerScanRow] = []
    total_points = width * height
    for power in range(power_min, power_max + 1):
        samples = sample_grid(power, width, height, max_iter=max_iter)
        stats = basin_summary(power, width, height, samples)
        shares = [count / total_points for count in stats.basin_counts]
        rows.append(
            PowerScanRow(
                power=power,
                mean_iterations=stats.mean_iterations,
                converged_fraction=stats.converged_points / total_points,
                stalled_fraction=stats.stalled_points / total_points,
                min_share=min(shares),
                max_share=max(shares),
            )
        )
    return rows


def scan_radius_bands(
    power: int,
    *,
    width: int = 120,
    height: int = 120,
    max_iter: int = 40,
    bands: int = 12,
    x_min: float = -1.6,
    x_max: float = 1.6,
    y_min: float = -1.6,
    y_max: float = 1.6,
) -> list[RadiusBandRow]:
    if bands < 1:
        raise ValueError("bands must be at least 1")

    samples = sample_grid(
        power,
        width,
        height,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        max_iter=max_iter,
    )
    max_radius = math.hypot(max(abs(x_min), abs(x_max)), max(abs(y_min), abs(y_max)))
    step = max_radius / bands

    buckets: list[list[NewtonResult]] = [[] for _ in range(bands)]
    for sample in samples:
        radius = abs(sample.start)
        index = min(bands - 1, int(radius / step)) if step > 0.0 else 0
        buckets[index].append(sample)

    rows: list[RadiusBandRow] = []
    for index, bucket in enumerate(buckets):
        radius_min = index * step
        radius_max = (index + 1) * step
        if not bucket:
            rows.append(
                RadiusBandRow(
                    power=power,
                    radius_min=radius_min,
                    radius_max=radius_max,
                    sample_count=0,
                    mean_iterations=0.0,
                    converged_fraction=0.0,
                    stalled_fraction=0.0,
                )
            )
            continue

        converged = sum(1 for sample in bucket if sample.converged)
        stalled = sum(1 for sample in bucket if sample.stalled)
        mean_iterations = sum(sample.iterations for sample in bucket) / len(bucket)
        rows.append(
            RadiusBandRow(
                power=power,
                radius_min=radius_min,
                radius_max=radius_max,
                sample_count=len(bucket),
                mean_iterations=mean_iterations,
                converged_fraction=converged / len(bucket),
                stalled_fraction=stalled / len(bucket),
            )
        )
    return rows


def iteration_histogram(
    power: int,
    *,
    width: int = 120,
    height: int = 120,
    max_iter: int = 40,
    x_min: float = -1.6,
    x_max: float = 1.6,
    y_min: float = -1.6,
    y_max: float = 1.6,
) -> IterationHistogram:
    samples = sample_grid(
        power,
        width,
        height,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        max_iter=max_iter,
    )
    counts = [0] * (max_iter + 1)
    stalled_count = 0
    unresolved_count = 0
    for sample in samples:
        if sample.converged:
            counts[min(sample.iterations, max_iter)] += 1
        elif sample.stalled:
            stalled_count += 1
        else:
            unresolved_count += 1
    return IterationHistogram(
        power=power,
        max_iter=max_iter,
        total_points=width * height,
        converged_counts=tuple(counts),
        stalled_count=stalled_count,
        unresolved_count=unresolved_count,
    )


def _nearest_root_index(z: complex, roots: list[complex]) -> int:
    return min(range(len(roots)), key=lambda idx: abs(z - roots[idx]))
