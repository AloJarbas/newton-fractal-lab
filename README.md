# Newton Fractal Lab

A tiny pure-Python lab for one sharp idea: Newton's method does not just find roots, it partitions the complex plane into competing basins of attraction.

This repo starts with the cleanest family to study: `z^n - 1`.
That keeps the algebra simple enough that the geometry gets to be the star.

## What is here

- pure-Python core for Newton iteration on `z^n - 1`
- SVG renderer for basin maps with iteration shading
- CLI for single-point reports, grid summaries, and figure generation
- generated gallery for `z^3 - 1`, `z^4 - 1`, and `z^5 - 1`
- a generated power-scan figure that tracks how convergence and basin-share spread drift as `n` increases
- a generated critical-radius scan that makes the derivative singularity at `z = 0` visible as a real convergence problem instead of a throwaway caveat
- a generated slow-convergence histogram figure that shows how much of the sampled square settles early, late, or not at all under one fixed iteration budget
- companion notebooks on critical structure and on the long iteration tail that thickens as the power rises
- small tests that check roots, convergence, grid accounting, and the scan layer

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

## Repo layout

- `newton_fractal_lab/core.py`: iteration and basin summaries
- `newton_fractal_lab/render.py`: SVG renderer with run-length compression across each row plus the family-level scan figures
- `newton_fractal_lab/cli.py`: render and reporting commands, including the multi-power scan and the new radial critical-structure scan
- `scripts/generate_gallery.py`: reproducible gallery and scan build
- `reports/unity-family.md`: generated basin summary for the shipped gallery
- `reports/unity-power-scan.md`: generated summary of how the family drifts across powers
- `reports/critical-structure.md`: generated note on where the derivative singularity shows up most clearly on the sampled square
- `reports/slow-convergence.md`: generated note on how the long iteration tail thickens across the family
- `notebooks/critical_structure_unity_family.ipynb`: slower companion notebook on derivative singularities, radius bands, and caveats
- `notebooks/slow_convergence_histograms.ipynb`: companion notebook on exact convergence-step counts, cumulative fractions, and cutoff caveats
- `tests/test_core.py`: small verification layer

## Next good questions

- what changes when the polynomial stops being `z^n - 1` and the roots stop being perfectly symmetric?
- how much of the slow tail disappears if the iteration budget doubles, and how much is true geometric stubbornness?
- where do the late-tail filaments thicken or thin as the cutoff changes?
- what changes first when the symmetry is broken by one carefully chosen asymmetric polynomial?

That is enough to make this a real lab instead of just a pretty image dump.

— Jarbas
