from __future__ import annotations

import math
import unittest

from newton_fractal_lab.core import basin_summary, iterate_unity, sample_grid, scan_unity_family, unity_roots


class NewtonFractalTests(unittest.TestCase):
    def test_unity_roots_have_unit_magnitude(self) -> None:
        roots = unity_roots(5)
        self.assertEqual(len(roots), 5)
        for root in roots:
            self.assertAlmostEqual(abs(root), 1.0, places=9)

    def test_iteration_converges_to_real_root_for_simple_start(self) -> None:
        result = iterate_unity(complex(0.9, 0.1), 3)
        self.assertTrue(result.converged)
        self.assertEqual(result.root_index, 0)
        self.assertLess(result.residual, 1e-8)

    def test_zero_start_stalls_for_unity_family(self) -> None:
        result = iterate_unity(0j, 4)
        self.assertTrue(result.stalled)
        self.assertFalse(result.converged)
        self.assertIsNone(result.root_index)

    def test_grid_summary_counts_match(self) -> None:
        width = 18
        height = 18
        samples = sample_grid(3, width, height, max_iter=30)
        stats = basin_summary(3, width, height, samples)
        self.assertEqual(sum(stats.basin_counts) + stats.stalled_points, width * height)
        self.assertGreater(stats.converged_points, 0)
        self.assertGreater(stats.mean_iterations, 0.0)

    def test_power_scan_returns_bounded_rows(self) -> None:
        rows = scan_unity_family(2, 5, width=24, height=24, max_iter=30)
        self.assertEqual([row.power for row in rows], [2, 3, 4, 5])
        for row in rows:
            self.assertGreater(row.mean_iterations, 0.0)
            self.assertGreaterEqual(row.converged_fraction, 0.0)
            self.assertLessEqual(row.converged_fraction, 1.0)
            self.assertGreaterEqual(row.stalled_fraction, 0.0)
            self.assertLessEqual(row.stalled_fraction, 1.0)
            self.assertGreaterEqual(row.min_share, 0.0)
            self.assertLessEqual(row.max_share, 1.0)
            self.assertLessEqual(row.min_share, row.max_share)


if __name__ == "__main__":
    unittest.main()
