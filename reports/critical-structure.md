# Critical structure and radius scan

This report asks a narrower question than the gallery: where does the derivative singularity at `z = 0` show up most clearly on the sampled square?

For `f(z) = z^n - 1`, Newton's update is

```text
N_n(z) = ((n - 1)/n) z + 1 / (n z^(n - 1))
```

So the origin is not a root at all. It is the point where the derivative vanishes, and the inverse-power term makes the map violent near the center.

The radial scan bins starting points by distance from the origin and compares four powers on the same square grid.

## z^3 - 1

- slowest radial band: `0.00 ≤ |z₀| < 0.19` with mean iteration count 14.82
- weakest convergence band: `0.00 ≤ |z₀| < 0.19` with convergence fraction 100.0%
- outermost band `2.07 ≤ |z₀| < 2.26` still converges at 100.0% with mean iteration count 7.18

## z^6 - 1

- slowest radial band: `0.00 ≤ |z₀| < 0.19` with mean iteration count 40.00
- weakest convergence band: `0.00 ≤ |z₀| < 0.19` with convergence fraction 0.0%
- outermost band `2.07 ≤ |z₀| < 2.26` still converges at 100.0% with mean iteration count 9.25

## z^9 - 1

- slowest radial band: `0.19 ≤ |z₀| < 0.38` with mean iteration count 40.00
- weakest convergence band: `0.00 ≤ |z₀| < 0.19` with convergence fraction 0.0%
- outermost band `2.07 ≤ |z₀| < 2.26` still converges at 92.6% with mean iteration count 15.17

## z^12 - 1

- slowest radial band: `0.19 ≤ |z₀| < 0.38` with mean iteration count 40.00
- weakest convergence band: `0.00 ≤ |z₀| < 0.19` with convergence fraction 0.0%
- outermost band `2.07 ≤ |z₀| < 2.26` still converges at 55.7% with mean iteration count 30.72

## Reading

- the center is the trouble spot because `f'(z) = n z^(n-1)` collapses there, so Newton's correction term can explode instead of settling down
- higher powers keep a slow inner region for longer, which is why the mean-iteration profile lifts upward as `n` increases
- the outer square is not uniformly easy, but it is usually much calmer than the central bands on the same iteration budget

This does not replace a full critical-orbit study. It is a cleaner public bridge between the basin pictures and the algebra behind them.

Open `art/critical-radius-scan.svg` and `notebooks/critical_structure_unity_family.ipynb` next.
