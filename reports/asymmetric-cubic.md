# Breaking the cubic symmetry

This report adds one carefully chosen asymmetric cubic beside the original `z^n - 1` family.
The point is not to turn the repo into a generic root-finder zoo. The point is to show what changes first when the clean rotational symmetry disappears.

## The two cubics

### Unity cubic

```text
p_u(z) = z^3 - 1
```

- roots: +1.000 +0.000i, -0.500 +0.866i, -0.500 -0.866i
- critical points: +0.000 +0.000i and +0.000 +0.000i
- basin shares on the sampled square: 34.1%, 32.9%, 32.9%

### Asymmetric cubic

```text
p_a(z) = (z - 1)(z - (-0.9 + 1.05i))(z - (-0.15 - 0.25i))
```

- expanded coefficients: z^3 + (+0.050 -0.800i) z^2 + (-0.653 +0.868i) z + (-0.398 -0.068i)
- critical points: +0.473 -0.038i and -0.506 +0.571i
- basin shares on the sampled square: 25.6%, 16.4%, 58.0%

## Main read

- the unity cubic keeps the classical democratic split: its largest basin share on the sampled square is only 34.1%
- the asymmetric cubic breaks that immediately: one root now owns 58.0% of the same square
- the hottest unity band is the nearest-critical band, where 86.0% of starts still need at least 10 steps
- the asymmetric cubic no longer concentrates its whole late tail in one center halo, but its strongest band skew still reaches a dominant-share value of 100.0%

## Why the comparison matters

The unity family let the origin stand in for the critical set because the cubic has one repeated critical point there.
Once symmetry breaks, that shortcut stops working.
The hard geometry is better organized by distance to the nearest critical point, and the basin shares stop hovering near one third each.

That is the real upgrade here.
The repo is no longer only a study of the roots-of-unity family. It now has one bounded asymmetric lane that shows which parts of the old reading were specific to symmetry and which ones survive after the symmetry is gone.

Open `art/asymmetric-cubic-critical-set-comparison.svg`, `art/asymmetric-cubic-critical-set-comparison.png`, and `notebooks/asymmetric_cubic_critical_set.ipynb` next.
