from __future__ import annotations

import unittest

from newton_fractal_lab.cubic import (
    asymmetric_cubic,
    compare_cubic_budget_persistence,
    counterweight_asymmetric_cubic,
    cubic_basin_summary,
    cubic_critical_points,
    evaluate_cubic,
    iterate_cubic,
    sample_cubic_grid,
    scan_critical_distance,
    scan_cubic_late_tail_tiles,
    split_critical_asymmetric_cubic,
    summarize_cubic_opposition,
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

    def test_cubic_late_tail_tiles_keep_expected_shape(self) -> None:
        rows = scan_cubic_late_tail_tiles(unity_cubic(), width=48, height=48, max_iter=8, late_threshold=10, tile_cols=6, tile_rows=6)
        self.assertEqual(len(rows), 36)
        for row in rows:
            self.assertGreater(row.sample_count, 0)
            self.assertGreaterEqual(row.late_fraction, 0.0)
            self.assertLessEqual(row.late_fraction, 1.0)
            self.assertGreaterEqual(row.unresolved_fraction, 0.0)
            self.assertLessEqual(row.unresolved_fraction, 1.0)

    def test_unity_core_stays_hotter_after_budget_rises(self) -> None:
        unity_rows = scan_critical_distance(unity_cubic(), width=72, height=72, max_iter=24, bands=6, late_threshold=10, include_unresolved_in_late=True)
        asym_rows = scan_critical_distance(asymmetric_cubic(), width=72, height=72, max_iter=24, bands=6, late_threshold=10, include_unresolved_in_late=True)
        self.assertGreater(unity_rows[0].late_fraction, 0.55)
        self.assertLess(asym_rows[0].late_fraction, 0.2)

    def test_split_critical_roots_are_actual_roots(self) -> None:
        polynomial = split_critical_asymmetric_cubic()
        for root in polynomial.roots:
            self.assertLess(abs(evaluate_cubic(polynomial, root)), 1e-9)

    def test_split_critical_cubic_keeps_balanced_basin_shares(self) -> None:
        polynomial = split_critical_asymmetric_cubic()
        samples = sample_cubic_grid(polynomial, 72, 72, max_iter=30)
        stats = cubic_basin_summary(polynomial, 72, 72, samples)
        self.assertLess(max(stats.basin_shares) - min(stats.basin_shares), 0.12)
        self.assertGreater(min(stats.basin_shares), 0.25)

    def test_split_critical_cubic_keeps_hotter_near_critical_lane(self) -> None:
        split_rows = scan_critical_distance(split_critical_asymmetric_cubic(), width=72, height=72, max_iter=30, bands=6, late_threshold=10, include_unresolved_in_late=True)
        asym_rows = scan_critical_distance(asymmetric_cubic(), width=72, height=72, max_iter=30, bands=6, late_threshold=10, include_unresolved_in_late=True)
        self.assertGreater(split_rows[0].late_fraction, asym_rows[0].late_fraction + 0.12)
        self.assertLess(split_rows[-1].dominant_share, 0.65)

    def test_counterweight_cubic_roots_are_actual_roots(self) -> None:
        polynomial = counterweight_asymmetric_cubic()
        for root in polynomial.roots:
            self.assertLess(abs(evaluate_cubic(polynomial, root)), 1e-9)

    def test_counterweight_cubic_flips_late_tail_opposite_root_cluster(self) -> None:
        row = summarize_cubic_opposition(
            [counterweight_asymmetric_cubic()],
            width=72,
            height=72,
            max_iter=24,
            late_threshold=10,
            tile_cols=8,
            tile_rows=8,
        )[0]
        self.assertGreater(row.root_centroid_x, 0.5)
        self.assertGreater(row.critical_centroid_x, 0.4)
        self.assertLess(row.late_tail_centroid_x, -0.05)
        self.assertGreater(row.left_late_share, 0.55)
        self.assertLess(row.center_late_share, 0.05)

    def test_counterweight_cubic_is_most_left_leaning_of_the_asymmetric_lane(self) -> None:
        rows = summarize_cubic_opposition(
            [asymmetric_cubic(), split_critical_asymmetric_cubic(), counterweight_asymmetric_cubic()],
            width=72,
            height=72,
            max_iter=24,
            late_threshold=10,
            tile_cols=8,
            tile_rows=8,
        )
        by_slug = {row.polynomial_slug: row for row in rows}
        self.assertLess(by_slug["counterweight-asymmetric-cubic"].late_tail_centroid_x, by_slug["split-critical-asymmetric-cubic"].late_tail_centroid_x)
        self.assertLess(by_slug["counterweight-asymmetric-cubic"].late_tail_centroid_x, by_slug["asymmetric-cubic"].late_tail_centroid_x)
        self.assertGreater(by_slug["split-critical-asymmetric-cubic"].center_late_share, by_slug["counterweight-asymmetric-cubic"].center_late_share)

    def test_cubic_budget_comparison_puts_split_critical_in_the_middle(self) -> None:
        rows = compare_cubic_budget_persistence(
            [unity_cubic(), asymmetric_cubic(), split_critical_asymmetric_cubic()],
            width=72,
            height=72,
            low_budget=8,
            high_budget=24,
            late_threshold=10,
            tile_cols=8,
            tile_rows=8,
            bands=6,
        )
        by_slug = {row.polynomial_slug: row for row in rows}
        unity = by_slug["unity-cubic"]
        asym = by_slug["asymmetric-cubic"]
        split = by_slug["split-critical-asymmetric-cubic"]
        self.assertGreater(unity.high_center_late, split.high_center_late)
        self.assertGreater(split.high_center_late, asym.high_center_late)
        self.assertGreater(unity.high_inner_band_late, split.high_inner_band_late)
        self.assertGreater(split.high_inner_band_late, asym.high_inner_band_late)


if __name__ == "__main__":
    unittest.main()
