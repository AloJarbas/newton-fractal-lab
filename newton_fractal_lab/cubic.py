from __future__ import annotations

from dataclasses import dataclass
import cmath

from .core import NewtonResult


@dataclass(frozen=True)
class CubicPolynomial:
    name: str
    slug: str
    roots: tuple[complex, complex, complex]
    coefficients: tuple[complex, complex, complex, complex]
    x_min: float = -1.6
    x_max: float = 1.6
    y_min: float = -1.6
    y_max: float = 1.6


@dataclass(frozen=True)
class CubicBasinStats:
    polynomial: CubicPolynomial
    width: int
    height: int
    mean_iterations: float
    basin_counts: tuple[int, int, int]
    stalled_points: int
    unresolved_points: int

    @property
    def total_points(self) -> int:
        return self.width * self.height

    @property
    def basin_shares(self) -> tuple[float, float, float]:
        total = self.total_points
        return tuple(count / total for count in self.basin_counts)


@dataclass(frozen=True)
class CriticalDistanceBandRow:
    polynomial_slug: str
    polynomial_name: str
    band_index: int
    distance_min: float
    distance_max: float
    sample_count: int
    mean_iterations: float
    late_fraction: float
    dominant_share: float
    basin_shares: tuple[float, float, float]

    @property
    def distance_mid(self) -> float:
        return 0.5 * (self.distance_min + self.distance_max)


def cubic_from_roots(
    name: str,
    slug: str,
    roots: tuple[complex, complex, complex],
    *,
    x_min: float = -1.6,
    x_max: float = 1.6,
    y_min: float = -1.6,
    y_max: float = 1.6,
) -> CubicPolynomial:
    if len(roots) != 3:
        raise ValueError("cubic polynomials need exactly three roots")
    a = -(roots[0] + roots[1] + roots[2])
    b = roots[0] * roots[1] + roots[0] * roots[2] + roots[1] * roots[2]
    c = -(roots[0] * roots[1] * roots[2])
    return CubicPolynomial(
        name=name,
        slug=slug,
        roots=roots,
        coefficients=(1.0 + 0.0j, a, b, c),
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )


def unity_cubic() -> CubicPolynomial:
    root_1 = 1.0 + 0.0j
    root_2 = complex(-0.5, 0.8660254037844386)
    root_3 = complex(-0.5, -0.8660254037844386)
    return cubic_from_roots("unity cubic z^3 - 1", "unity-cubic", (root_1, root_2, root_3))


def asymmetric_cubic() -> CubicPolynomial:
    return cubic_from_roots(
        "asymmetric cubic",
        "asymmetric-cubic",
        (
            1.0 + 0.0j,
            complex(-0.9, 1.05),
            complex(-0.15, -0.25),
        ),
    )


def evaluate_cubic(polynomial: CubicPolynomial, z: complex) -> complex:
    value = 0.0 + 0.0j
    for coefficient in polynomial.coefficients:
        value = value * z + coefficient
    return value


def evaluate_cubic_derivative(polynomial: CubicPolynomial, z: complex) -> complex:
    _, a, b, _ = polynomial.coefficients
    return 3.0 * z * z + 2.0 * a * z + b


def cubic_critical_points(polynomial: CubicPolynomial) -> tuple[complex, complex]:
    _, a, b, _ = polynomial.coefficients
    discriminant = (2.0 * a) ** 2 - 12.0 * b
    if abs(discriminant) <= 1e-12:
        point = (-2.0 * a) / 6.0
        return (point, point)
    root = cmath.sqrt(discriminant)
    return (((-2.0 * a) + root) / 6.0, ((-2.0 * a) - root) / 6.0)


def iterate_cubic(
    start: complex,
    polynomial: CubicPolynomial,
    *,
    max_iter: int = 40,
    tol: float = 1e-8,
    derivative_tol: float = 1e-12,
) -> NewtonResult:
    if max_iter < 1:
        raise ValueError("max_iter must be positive")

    z = start
    roots = list(polynomial.roots)
    for step in range(1, max_iter + 1):
        fz = evaluate_cubic(polynomial, z)
        residual = abs(fz)
        if residual <= tol:
            root_index = min(range(3), key=lambda idx: abs(z - roots[idx]))
            return NewtonResult(start, z, step - 1, True, False, root_index, residual)

        derivative = evaluate_cubic_derivative(polynomial, z)
        if abs(derivative) <= derivative_tol:
            return NewtonResult(start, z, step - 1, False, True, None, residual)

        z = z - fz / derivative

    residual = abs(evaluate_cubic(polynomial, z))
    root_index = min(range(3), key=lambda idx: abs(z - roots[idx])) if residual <= 1e-4 else None
    return NewtonResult(start, z, max_iter, residual <= tol, False, root_index, residual)


def sample_cubic_grid(
    polynomial: CubicPolynomial,
    width: int,
    height: int,
    *,
    max_iter: int = 40,
) -> list[NewtonResult]:
    if width < 2 or height < 2:
        raise ValueError("width and height must both be at least 2")

    samples: list[NewtonResult] = []
    for j in range(height):
        y = polynomial.y_max - (polynomial.y_max - polynomial.y_min) * j / (height - 1)
        for i in range(width):
            x = polynomial.x_min + (polynomial.x_max - polynomial.x_min) * i / (width - 1)
            samples.append(iterate_cubic(complex(x, y), polynomial, max_iter=max_iter))
    return samples


def cubic_basin_summary(
    polynomial: CubicPolynomial,
    width: int,
    height: int,
    samples: list[NewtonResult],
) -> CubicBasinStats:
    if len(samples) != width * height:
        raise ValueError("sample count does not match width * height")

    basin_counts = [0, 0, 0]
    total_iterations = 0
    stalled = 0
    unresolved = 0
    for sample in samples:
        total_iterations += sample.iterations
        if sample.converged and sample.root_index is not None:
            basin_counts[sample.root_index] += 1
        elif sample.stalled:
            stalled += 1
        else:
            unresolved += 1

    return CubicBasinStats(
        polynomial=polynomial,
        width=width,
        height=height,
        mean_iterations=total_iterations / len(samples),
        basin_counts=tuple(basin_counts),
        stalled_points=stalled,
        unresolved_points=unresolved,
    )


def scan_critical_distance(
    polynomial: CubicPolynomial,
    *,
    width: int = 120,
    height: int = 120,
    max_iter: int = 40,
    bands: int = 8,
    late_threshold: int = 10,
) -> list[CriticalDistanceBandRow]:
    if bands < 1:
        raise ValueError("bands must be at least 1")

    critical_points = cubic_critical_points(polynomial)
    samples = sample_cubic_grid(polynomial, width, height, max_iter=max_iter)
    distance_values: list[tuple[float, NewtonResult]] = []
    max_distance = 0.0
    for sample in samples:
        distance = min(abs(sample.start - point) for point in critical_points)
        max_distance = max(max_distance, distance)
        distance_values.append((distance, sample))

    band_width = max_distance / bands if max_distance > 0.0 else 1.0
    rows: list[CriticalDistanceBandRow] = []
    for band_index in range(bands):
        distance_min = band_index * band_width
        distance_max = (band_index + 1) * band_width
        bucket = [
            sample
            for distance, sample in distance_values
            if distance_min <= distance < (distance_max if band_index < bands - 1 else distance_max + 1e-12)
        ]
        if not bucket:
            rows.append(
                CriticalDistanceBandRow(
                    polynomial_slug=polynomial.slug,
                    polynomial_name=polynomial.name,
                    band_index=band_index,
                    distance_min=distance_min,
                    distance_max=distance_max,
                    sample_count=0,
                    mean_iterations=0.0,
                    late_fraction=0.0,
                    dominant_share=0.0,
                    basin_shares=(0.0, 0.0, 0.0),
                )
            )
            continue

        counts = [sum(1 for sample in bucket if sample.root_index == idx) for idx in range(3)]
        basin_shares = tuple(count / len(bucket) for count in counts)
        rows.append(
            CriticalDistanceBandRow(
                polynomial_slug=polynomial.slug,
                polynomial_name=polynomial.name,
                band_index=band_index,
                distance_min=distance_min,
                distance_max=distance_max,
                sample_count=len(bucket),
                mean_iterations=sum(sample.iterations for sample in bucket) / len(bucket),
                late_fraction=sum(1 for sample in bucket if sample.iterations >= late_threshold) / len(bucket),
                dominant_share=max(basin_shares),
                basin_shares=basin_shares,
            )
        )
    return rows
