from __future__ import annotations

import unittest

from newton_fractal_lab.cubic import (
    asymmetric_cubic,
    cubic_basin_summary,
    cubic_critical_points,
    evaluate_cubic,
    iterate_cubic,
    sample_cubic_grid,
    scan_critical_distance,
    unity_cubic,
)


class CubicComparisonTests(unittest.TestCase):
    def test_asymmetric_roots_are_actual_roots(self) -> None:
        polynomial = asymmetric_cubic()
        for root in polynomial.roots:
            self.assertLess(abs(evaluate_cubic(polynomial, root)), 1e-9)

    def test_unity_cubic_critical_points_collapse_to_origin(self) -> None:
        point_a, point_b = cubic_critical_points(unity_cubic())
        self.assertLess(abs(point_a), 1e-6)
        self.assertLess(abs(point_b), 1e-6)
        self.assertLess(abs(point_a - point_b), 1e-6)

    def test_asymmetric_grid_skews_one_basin(self) -> None:
        polynomial = asymmetric_cubic()
        samples = sample_cubic_grid(polynomial, 72, 72, max_iter=30)
        stats = cubic_basin_summary(polynomial, 72, 72, samples)
        self.assertGreater(max(stats.basin_shares), 0.5)
        self.assertGreater(max(stats.basin_shares) - min(stats.basin_shares), 0.25)

    def test_unity_core_has_heavier_near_critical_late_tail(self) -> None:
        unity_rows = scan_critical_distance(unity_cubic(), width=72, height=72, max_iter=30, bands=6, late_threshold=10)
        asym_rows = scan_critical_distance(asymmetric_cubic(), width=72, height=72, max_iter=30, bands=6, late_threshold=10)
        self.assertGreater(unity_rows[0].late_fraction, asym_rows[0].late_fraction)
        self.assertGreater(asym_rows[-1].dominant_share, 0.7)

    def test_asymmetric_start_near_inner_root_converges(self) -> None:
        polynomial = asymmetric_cubic()
        result = iterate_cubic(complex(-0.12, -0.18), polynomial, max_iter=30)
        self.assertTrue(result.converged)
        self.assertEqual(result.root_index, 2)


if __name__ == "__main__":
    unittest.main()
