# Late-tail spatial map

This report keeps the earlier 20-step late-tail cutoff from the histogram pass, but stops collapsing everything onto one axis.
The question is local now: where on the sampled square do those slow starts actually live?

Each panel bins the same square into `12 × 12` tiles and marks the share of starts that either need at least `20` Newton steps or fail the 40-step cutoff.

## Main read

- `z^3 - 1` still keeps most of its slow starts on thin boundary filaments: the hottest tile reaches only 14.0%, and the center four tiles average 4.5%
- whole-grid late fraction for `z^3 - 1`: 1.0%
- `z^6 - 1` has already grown a real center halo: the hottest tile `-0.27 ≤ Re(z₀) < +0.00`, `+0.00 ≤ Im(z₀) < +0.27` is at 100.0%, and the center four tiles average 100.0%
- whole-grid late fraction for `z^6 - 1`: 16.7%
- `z^9 - 1` has already grown a real center halo: the hottest tile `-0.27 ≤ Re(z₀) < +0.00`, `+0.27 ≤ Im(z₀) < +0.53` is at 100.0%, and the center four tiles average 100.0%
- whole-grid late fraction for `z^9 - 1`: 27.9%
- `z^12 - 1` has already grown a real center halo: the hottest tile `-0.27 ≤ Re(z₀) < +0.00`, `+0.27 ≤ Im(z₀) < +0.53` is at 100.0%, and the center four tiles average 100.0%
- whole-grid late fraction for `z^12 - 1`: 34.7%

## Why the map earns its place

- the histogram pass said how much late tail existed, but not whether it sat in a center block or in thin off-axis filaments
- the radius scan said the center matters more at higher powers, but it still averaged away direction and spoke structure
- this map is the missing bridge: low powers still look boundary-dominated, while higher powers visibly turn the origin neighborhood into a full finite-budget trap instead of a mere thin band

That is the useful new fact. The slow region does not just get bigger. Its shape changes.

Open `art/late-tail-spatial-map.svg`, `art/late-tail-spatial-map.png`, and `notebooks/late_tail_spatial_map.ipynb` next.
