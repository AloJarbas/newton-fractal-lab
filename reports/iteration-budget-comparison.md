# Iteration-budget versus geometry

This report compares the same radial profiles at `40` and `80` Newton steps.
The point is not just to say that higher powers are harder. It is to separate two different effects:

- starts that were only cutoff-limited at `40` and recover once the budget rises
- starts that are still stubborn even at `80`, which is the more geometric part of the story

The radial view keeps the origin in frame, because the derivative singularity near `z = 0` is where the family first gets violent.

## Main read

- the biggest whole-grid recovery here is `z^12 - 1`, where 10.0% of sampled starts move from unresolved at `40` to converged by `80`
- the most stubborn high-budget family here is `z^9 - 1`, whose weakest radial band still converges only 0.0% of the time even at `80` steps
- lower powers flatten much earlier, which is why `z^3 - 1` barely moves in the recovery panel while the higher-power inner bands still climb

## Per-power summary

### z^3 - 1

- recovered across the whole sampled square: effectively none at this budget pair
- strongest recovery band: none worth calling out; the `40`-step cutoff was already enough for this sampled family
- weakest band even at `80`: `0.00 ≤ |z₀| < 0.19` with convergence fraction 100.0%

### z^6 - 1

- recovered across the whole sampled square: 3.8%
- strongest recovery band: `0.00 ≤ |z₀| < 0.19` gains 87.2% more converged starts when the budget rises from `40` to `80`
- weakest band even at `80`: `0.00 ≤ |z₀| < 0.19` with convergence fraction 87.2%

### z^9 - 1

- recovered across the whole sampled square: 9.3%
- strongest recovery band: `0.19 ≤ |z₀| < 0.38` gains 59.6% more converged starts when the budget rises from `40` to `80`
- weakest band even at `80`: `0.00 ≤ |z₀| < 0.19` with convergence fraction 0.0%

### z^12 - 1

- recovered across the whole sampled square: 10.0%
- strongest recovery band: `0.38 ≤ |z₀| < 0.57` gains 52.3% more converged starts when the budget rises from `40` to `80`
- weakest band even at `80`: `0.00 ≤ |z₀| < 0.19` with convergence fraction 0.0%

## Reading

- the bottom panel is the key: it marks bands where the `40`-step cutoff was hiding genuinely recoverable starts
- if a band still looks weak at `80`, that is harder to blame on the cutoff alone and easier to treat as actual basin-boundary geometry
- the higher-power families keep both effects alive at once: some inner bands recover a lot, but some outer or mid-radius bands are still not especially clean even after the budget doubles

Open `art/iteration-budget-radius-comparison.svg`, `art/iteration-budget-radius-comparison.png`, and the older critical-structure and slow-tail notebooks next.
