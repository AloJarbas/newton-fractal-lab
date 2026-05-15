# Slow-convergence histograms

This report asks a complementary question to the basin gallery: not just where points go, but how much of the sampled square settles fast, late, or not at all under the current iteration budget.

The figure bins exact convergence counts on the same square grid for several powers in the unity family.

## Main read

- the heaviest late tail here is `z^12 - 1`, where 34.7% of the sampled square still needs at least 20 steps or misses the cutoff entirely
- the hardest finite-budget case here is `z^12 - 1`, where 23.3% of starts are still unresolved at 40 iterations
- lower powers still have boundary tails, but the mass sits earlier in the histogram, which is why the panels look tighter and more left-loaded

## Per-power tail summary

### z^3 - 1

- fast settle (0-4 steps): 8.6%
- middle settle (5-9 steps): 74.7%
- slow settle (10-19 steps): 15.7%
- late tail (20-40 steps): 1.0%
- unresolved at cutoff: 0.0%

### z^6 - 1

- fast settle (0-4 steps): 2.7%
- middle settle (5-9 steps): 58.9%
- slow settle (10-19 steps): 21.7%
- late tail (20-40 steps): 12.5%
- unresolved at cutoff: 4.2%

### z^9 - 1

- fast settle (0-4 steps): 1.6%
- middle settle (5-9 steps): 43.7%
- slow settle (10-19 steps): 26.8%
- late tail (20-40 steps): 13.7%
- unresolved at cutoff: 14.2%

### z^12 - 1

- fast settle (0-4 steps): 1.1%
- middle settle (5-9 steps): 30.3%
- slow settle (10-19 steps): 33.8%
- late tail (20-40 steps): 11.4%
- unresolved at cutoff: 23.3%

## Reading

- exact histograms make the boundary problem more concrete: the issue is not just that some pixels look dark, but that a larger share of the square gets pushed into a long iteration tail as the power rises
- the unresolved bar is a reminder that the current cutoff matters; some starts are not truly divergent, they are just too slow for the present budget
- this is still a sampled public summary, not a theorem about every point on the basin boundary

Open `art/slow-convergence-histograms.svg`, `art/slow-convergence-histograms.png`, and `notebooks/slow_convergence_histograms.ipynb` next.
