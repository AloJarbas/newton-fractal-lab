# Newton Fractal Lab

A tiny pure-Python lab for one sharp idea: Newton's method does not just find roots, it partitions the complex plane into competing basins of attraction.

This repo starts with the cleanest family to study: `z^n - 1`.
That keeps the algebra simple enough that the geometry gets to be the star.

It now has one bounded asymmetric lane too: a carefully chosen cubic that breaks the rotational symmetry without turning the repo into a generic polynomial zoo.

## What is here

- pure-Python core for Newton iteration on `z^n - 1`
- a second cubic-analysis lane for one carefully chosen asymmetric polynomial with explicit roots, critical points, and grid summaries
- SVG renderer for basin maps with iteration shading
- CLI for single-point reports, grid summaries, family scans, and the new cubic-comparison card
- generated gallery for `z^3 - 1`, `z^4 - 1`, and `z^5 - 1`
- a generated power-scan figure that tracks how convergence and basin-share spread drift as `n` increases
- a generated critical-radius scan that makes the derivative singularity at `z = 0` visible as a real convergence problem instead of a throwaway caveat
- a generated slow-convergence histogram figure that shows how much of the sampled square settles early, late, or not at all under one fixed iteration budget
- a generated budget-comparison figure that shows which radial bands were only cutoff-limited and which ones stay stubborn after the iteration budget doubles
- a generated asymmetric-cubic comparison card that separates the unity-family center singularity story from the first effects of broken symmetry
- companion notebooks on critical structure, the long iteration tail, and the new asymmetric cubic critical-set pass
- small tests that check roots, convergence, grid accounting, and the new cubic lane

## Gallery

### `z^3 - 1`

![Newton fractal for z^3 - 1](art/newton-z3-minus-1.svg)

### `z^4 - 1`

![Newton fractal for z^4 - 1](art/newton-z4-minus-1.svg)

### `z^5 - 1`

![Newton fractal for z^5 - 1](art/newton-z5-minus-1.svg)

### Unity-family power scan

![Unity-family power scan](art/unity-power-scan.svg)

### Critical-radius scan

![Critical-radius scan](art/critical-radius-scan.svg)

### Slow-convergence histograms

![Slow-convergence histograms](art/slow-convergence-histograms.png)

### Iteration-budget radius comparison

![Iteration-budget radius comparison](art/iteration-budget-radius-comparison.png)

### Breaking the cubic symmetry

![Asymmetric cubic critical-set comparison](art/asymmetric-cubic-critical-set-comparison.png)

This new sidecar is the repo's first honest move beyond the roots-of-unity family. It compares `z^3 - 1` against one asymmetric cubic with the same Newton budget and shows two things at once: the repeated center critical point stops being the whole story, and one root can start owning far more of the sampled square once the symmetry is broken.

## Why this repo is worth opening

Newton fractals are an honest example of how a local algorithm creates global structure.
Each point starts with the same update rule.
A tiny change in the initial guess can send the orbit to a different root entirely.
That makes the basin boundaries the interesting part, not just the roots themselves.

This repo is small on purpose:

- no plotting stack,
- no dependency pile,
- no giant symbolic framework,
- just enough code to inspect the iteration, render the geometry, and summarize what the grid is doing.

The new asymmetric-cubic sidecar matters because it keeps the repo honest. A lot of the old reading depended on the unity family's symmetry. Now there is one concrete counterexample lane showing what survives after that symmetry breaks.

## Quick start

Generate the gallery, power scan, and reports:

```bash
python3 scripts/generate_gallery.py
```

Run the tests:

```bash
python3 -m unittest discover -s tests
```

Render one figure directly:

```bash
python3 -m newton_fractal_lab.cli render --power 6 --width 260 --height 260 --output art/newton-z6-minus-1.svg
```

Inspect one starting point:

```bash
python3 -m newton_fractal_lab.cli report --power 5 --x 0.15 --y 0.15
```

Get a grid summary:

```bash
python3 -m newton_fractal_lab.cli grid-report --power 5 --width 120 --height 120
```

Scan several powers and render the summary figure:

```bash
python3 -m newton_fractal_lab.cli power-scan --power-min 2 --power-max 12 --width 100 --height 100 --output art/unity-power-scan.svg
```

Compare slow-convergence histograms across several powers:

```bash
python3 -m newton_fractal_lab.cli iteration-hist --powers 3,6,9,12 --width 120 --height 120 --max-iter 40 --output art/slow-convergence-histograms.svg
```

Compare the same radial profiles at two iteration budgets:

```bash
python3 -m newton_fractal_lab.cli budget-radius-compare --powers 3,6,9,12 --low-budget 40 --high-budget 80 --output art/iteration-budget-radius-comparison.svg --png-output art/iteration-budget-radius-comparison.png
```

Compare the unity cubic against the new asymmetric cubic lane:

```bash
python3 -m newton_fractal_lab.cli cubic-compare --output art/asymmetric-cubic-critical-set-comparison.svg --png-output art/asymmetric-cubic-critical-set-comparison.png
```

## Repo layout

- `newton_fractal_lab/core.py`: iteration and basin summaries for the unity family
- `newton_fractal_lab/cubic.py`: bounded asymmetric-cubic lane with explicit roots, critical points, and nearest-critical-point scans
- `newton_fractal_lab/render.py`: SVG renderer with run-length compression across each row plus the family-level scan figures, the budget-comparison card, and the new cubic-comparison card
- `newton_fractal_lab/cli.py`: render and reporting commands, including the multi-power scan, the radial critical-structure scan, the budget-comparison pass, and the new `cubic-compare` command
- `scripts/generate_gallery.py`: reproducible gallery and scan build
- `reports/unity-family.md`: generated basin summary for the shipped gallery
- `reports/unity-power-scan.md`: generated summary of how the family drifts across powers
- `reports/critical-structure.md`: generated note on where the derivative singularity shows up most clearly on the sampled square
- `reports/slow-convergence.md`: generated note on how the long iteration tail thickens across the family
- `reports/iteration-budget-comparison.md`: generated note on what disappears with a larger cutoff and what still looks geometrically stubborn
- `reports/asymmetric-cubic.md`: generated note on what changes first when the cubic symmetry is broken
- `notebooks/critical_structure_unity_family.ipynb`: slower companion notebook on derivative singularities, radius bands, and caveats
- `notebooks/slow_convergence_histograms.ipynb`: companion notebook on exact convergence-step counts, cumulative fractions, and cutoff caveats
- `notebooks/asymmetric_cubic_critical_set.ipynb`: companion notebook for the new asymmetric-cubic critical-set pass
- `tests/test_core.py` and `tests/test_cubic.py`: small verification layer

## Next good questions

- where do the late-tail filaments thicken or thin as the cutoff changes?
- add one spatial heatmap of late-tail starts only if it reveals something the histogram and critical-distance scans still miss
- try one second asymmetric polynomial only if it reveals a genuinely different critical-set geometry instead of repeating the same share-skew story

That is enough to make this a real lab instead of just a pretty image dump.

— Jarbas
