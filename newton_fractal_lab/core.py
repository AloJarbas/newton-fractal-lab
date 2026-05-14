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


def _nearest_root_index(z: complex, roots: list[complex]) -> int:
    return min(range(len(roots)), key=lambda idx: abs(z - roots[idx]))
