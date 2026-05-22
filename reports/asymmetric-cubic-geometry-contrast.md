# Asymmetric cubic geometry contrast

This sidecar keeps the repo honest about the next loophole.

One asymmetric cubic was enough to show that the unity-family symmetry was not universal.
It was not enough to claim that symmetry breaking always produces the same kind of Newton geometry.

This pass compares the repo's existing asymmetric cubic against one second asymmetric cubic chosen for a genuinely different critical-point layout.

## The new cubic

```text
p_s(z) = (z - 1)(z - (-0.35 + 0.92i))(z - (-0.30 - 0.88i))
```

- expanded coefficients: z^3 + (-0.350 -0.040i) z^2 + (+0.265 +0.072i) z + (-0.915 -0.032i)
- critical points: +0.155 -0.263i and +0.079 +0.289i
- basin shares on the sampled square: 38.5%, 29.7%, 31.8%

## Main read

- the existing asymmetric cubic still becomes a winner-take-most square: its largest basin share is 58.0%
- the split-critical cubic does not: its largest basin share is only 38.5%, so the sampled square stays much closer to a three-way fight
- the existing asymmetric cubic cools its nearest-critical band down to 11.7% late-tail share at this budget
- the split-critical cubic keeps that same nearest-critical band far hotter at 36.1%
- even away from the center, the split-critical cubic never lets one root own much more than 60.7% of a band, while the existing asymmetric cubic reaches 100.0%

## Why this earns a second asymmetric lane

The first asymmetric cubic taught one good lesson: broken symmetry can turn a clean one-third split into a heavily skewed contest.

The new cubic teaches a different one.

Broken symmetry does not have to collapse into one dominant basin and a cooled center. If the critical points stay split near the middle of the square, the near-critical tension can remain hot while the basin shares stay comparatively balanced.

That is the real upgrade here. The hottest near-critical band in the new cubic is 36.1%, not because the repo changed the budget or the window, but because the critical geometry itself stayed competitive.

Open `art/asymmetric-cubic-geometry-contrast.svg`, `art/asymmetric-cubic-geometry-contrast.png`, `art/asymmetric-cubic-geometry-contrast.csv`, and `notebooks/asymmetric_cubic_geometry_contrast.ipynb` next.
