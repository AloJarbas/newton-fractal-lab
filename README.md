# Newton Fractal Lab

A tiny pure-Python lab for one sharp idea: Newton's method does not just find roots, it partitions the complex plane into competing basins of attraction.

This repo starts with the cleanest family to study: `z^n - 1`.
That keeps the algebra simple enough that the geometry gets to be the star.

It now has three bounded asymmetric lanes too: one winner-take-most cubic, one split-critical cubic, and now one counterweight cubic that pushes most of the late tail away from its own root cluster instead of toward it.

## What is here

- pure-Python core for Newton iteration on `z^n - 1`
- bounded cubic-analysis lanes for three carefully chosen asymmetric polynomials with explicit roots, critical points, and grid summaries
- SVG renderer for basin maps with iteration shading
- CLI for single-point reports, grid summaries, family scans, the asymmetric-cubic card, the asymmetric-contrast card, the cubic-budget persistence pass, the three-cubic persistence atlas, and the new asymmetric-cubic opposition card
- generated gallery for `z^3 - 1`, `z^4 - 1`, and `z^5 - 1`
- a generated power-scan figure that tracks how convergence and basin-share spread drift as `n` increases
- a generated critical-radius scan that makes the derivative singularity at `z = 0` visible as a real convergence problem instead of a throwaway caveat
- a generated slow-convergence histogram figure that shows how much of the sampled square settles early, late, or not at all under one fixed iteration budget
- a generated budget-comparison figure that shows which radial bands were only cutoff-limited and which ones stay stubborn after the iteration budget doubles
- a generated late-tail spatial map that shows where the slow starts actually live on the square instead of collapsing them onto one histogram or one radial axis
- a generated late-tail persistence atlas that raises both the Newton cutoff and the late-threshold, so the repo can finally distinguish ordinary slow tiles from the center halos that survive even after the old entire budget becomes the new ultra-late bar
- a generated asymmetric-cubic comparison card that separates the unity-family center singularity story from the first effects of broken symmetry
- a generated asymmetric-cubic geometry-contrast card that shows broken symmetry does not force one Newton story: one cubic becomes winner-take-most, while a second split-critical cubic keeps a much more balanced three-way fight and a hotter near-critical lane
- a generated cubic-budget persistence card that checks how much of the old cubic drama survives after the Newton cutoff rises instead of stopping at one low-budget snapshot
- a generated three-cubic persistence atlas that puts the unity cubic, the winner-take-most asymmetric cubic, and the split-critical asymmetric cubic on the same low/high budget map so the middle lane stops being a vague claim
- a generated asymmetric-cubic opposition card that closes the next loophole by showing a third asymmetric geometry: the roots and critical set can stay on the right while most of the late tail drifts left of the origin
- companion notebooks on critical structure, the long iteration tail, the late-tail spatial map, the late-tail persistence atlas, the asymmetric cubic critical-set pass, the asymmetric cubic geometry contrast, the cubic-budget persistence follow-up, the three-cubic persistence atlas, and the asymmetric cubic opposition pass
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

### Late-tail spatial map

![Late-tail spatial map](art/late-tail-spatial-map.png)

This pass closes a real gap in the earlier notes. The histogram told you how much late-tail mass existed. The radius scan told you the center got hotter as the power rose. The new map shows the missing geometric fact: for low powers the slow starts still sit mostly on thin basin filaments, while higher powers turn the origin neighborhood into a visibly thick finite-budget trap.

### Late-tail persistence atlas

![Late-tail persistence atlas](art/late-tail-persistence-atlas.png)

This follow-up asks the harder version of the same question. Once the cutoff rises from 40 to 80 steps, and the late-threshold rises with it from 20 to 40, which tiles are still genuinely ultra-late? The answer is not uniform across the family: `z^3 - 1` mostly cools away, `z^6 - 1` keeps only a trimmed core, and `z^9 - 1` plus `z^12 - 1` still hold a real center halo even after the old whole budget becomes the new late bar.

### Breaking the cubic symmetry

![Asymmetric cubic critical-set comparison](art/asymmetric-cubic-critical-set-comparison.png)

This new sidecar is the repo's first honest move beyond the roots-of-unity family. It compares `z^3 - 1` against one asymmetric cubic with the same Newton budget and shows two things at once: the repeated center critical point stops being the whole story, and one root can start owning far more of the sampled square once the symmetry is broken.

### Asymmetric cubic geometry contrast

![Asymmetric cubic geometry contrast](art/asymmetric-cubic-geometry-contrast.png)

This second asymmetric lane closes the next loophole. The first asymmetric cubic showed that broken symmetry can hand most of the square to one root. The new split-critical cubic shows that broken symmetry can also do something else: keep the basin shares much closer together while the near-critical lane stays hot.

### Cubic budget persistence

![Cubic budget persistence](art/cubic-budget-persistence.png)

This follow-up keeps the same two cubics and raises the Newton cutoff. That exposes one sharper fact: part of the low-budget heat was just cutoff noise, but the unity cubic still keeps a much fatter slow center after the cutoff rises, while the asymmetric cubic cools much harder.

### Three cubic persistence atlas

![Three cubic persistence atlas](art/cubic-persistence-atlas.png)

This fast-lane follow-up closes the next loophole. The split-critical cubic does not collapse into the same persistence story as the older asymmetric cubic. After the cutoff rises, it keeps a real middle lane: cooler than the unity singular core, much hotter than the winner-take-most asymmetric case.

### Asymmetric cubic opposition

![Asymmetric cubic opposition](art/asymmetric-cubic-opposition.png)

This deeper follow-up adds the third asymmetric lane the repo was still missing. The new counterweight cubic keeps its roots and critical points on the right, but the late-tail centroid flips left of the origin, so the slow geometry no longer follows the root cluster itself.

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

The new asymmetric-cubic geometry-contrast sidecar matters because it closes the next loophole too. Broken symmetry is not one story. One cubic turns into winner-take-most basin ownership. Another keeps the competition near the center alive instead of cooling it away.

The late-tail spatial map matters for the same reason. It upgrades the old "higher powers are slower" line into something more geometric: the slow region does not just grow, it changes shape.

The new late-tail persistence atlas matters because it closes the next loophole in that story. A hot tile at the old 20-step threshold might still be ordinary moderate slowness. The harder atlas asks what survives after the threshold doubles too, and that turns out to separate the lower-power filaments from the higher-power center core much more sharply.

The new cubic-budget persistence sidecar matters because it keeps the cubic comparison honest too. A hot map at one cutoff can still be partly budget-limited. The follow-up checks what is still hot after the cutoff rises.

The new three-cubic persistence atlas matters because it closes the next loophole after that. Broken symmetry does not imply one persistence outcome. The split-critical cubic keeps a real middle lane once the cutoff rises, so the repo now has three distinct persistence stories instead of two endpoints and a guess.

The new asymmetric-cubic opposition card matters because it closes the next one too. Even after the repo had a winner-take-most cubic and a balanced split-critical cubic, it still would have been easy to assume the slow tail had to lean toward the same side as the roots and critical set. The counterweight cubic breaks that intuition: the roots and critical points stay on the right, while most of the late-tail mass drifts left.

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

Render the late-tail spatial map:

```bash
python3 -m newton_fractal_lab.cli late-tail-map --powers 3,6,9,12 --late-threshold 20 --output art/late-tail-spatial-map.svg --png-output art/late-tail-spatial-map.png
```

Render the late-tail persistence atlas:

```bash
python3 -m newton_fractal_lab.cli late-tail-persistence --powers 3,6,9,12 --low-budget 40 --high-budget 80 --low-threshold 20 --high-threshold 40 --output art/late-tail-persistence-atlas.svg --png-output art/late-tail-persistence-atlas.png
```

Compare the unity cubic against the new asymmetric cubic lane:

```bash
python3 -m newton_fractal_lab.cli cubic-compare --output art/asymmetric-cubic-critical-set-comparison.svg --png-output art/asymmetric-cubic-critical-set-comparison.png
```

Compare the two asymmetric cubic stories directly:

```bash
python3 -m newton_fractal_lab.cli asymmetric-cubic-contrast --output art/asymmetric-cubic-geometry-contrast.svg --png-output art/asymmetric-cubic-geometry-contrast.png
```

Compare low- and high-budget cubic persistence:

```bash
python3 -m newton_fractal_lab.cli cubic-budget-persistence --output art/cubic-budget-persistence.svg --png-output art/cubic-budget-persistence.png
```

Render the three-cubic persistence atlas:

```bash
python3 -m newton_fractal_lab.cli cubic-persistence-atlas --output art/cubic-persistence-atlas.svg --png-output art/cubic-persistence-atlas.png
```

Render the new asymmetric-cubic opposition card:

```bash
python3 -m newton_fractal_lab.cli asymmetric-cubic-opposition --output art/asymmetric-cubic-opposition.svg --png-output art/asymmetric-cubic-opposition.png
```

## Repo layout

- `newton_fractal_lab/core.py`: iteration and basin summaries for the unity family
- `newton_fractal_lab/cubic.py`: bounded cubic lanes with explicit roots, critical points, and nearest-critical-point scans
- `newton_fractal_lab/render.py`: SVG renderer with run-length compression across each row plus the family-level scan figures, the budget-comparison card, the late-tail persistence atlas, the cubic-comparison card, the asymmetric-contrast card, the cubic-budget persistence card, the three-cubic persistence atlas, and the asymmetric-cubic opposition card
- `newton_fractal_lab/cli.py`: render and reporting commands, including the multi-power scan, the radial critical-structure scan, the late-tail spatial map, the new late-tail persistence atlas, the budget-comparison pass, `cubic-compare`, `asymmetric-cubic-contrast`, `cubic-budget-persistence`, `cubic-persistence-atlas`, and `asymmetric-cubic-opposition`
- `scripts/generate_gallery.py`: reproducible gallery and scan build
- `reports/unity-family.md`: generated basin summary for the shipped gallery
- `reports/unity-power-scan.md`: generated summary of how the family drifts across powers
- `reports/critical-structure.md`: generated note on where the derivative singularity shows up most clearly on the sampled square
- `reports/slow-convergence.md`: generated note on how the long iteration tail thickens across the family
- `reports/iteration-budget-comparison.md`: generated note on what disappears with a larger cutoff and what still looks geometrically stubborn
- `reports/late-tail-spatial-map.md`: generated note on where slow starts stay filament-thin and where they condense into a center halo
- `reports/late-tail-persistence-atlas.md`: generated note on what survives once the old 40-step budget becomes the new ultra-late bar
- `reports/asymmetric-cubic.md`: generated note on what changes first when the cubic symmetry is broken
- `reports/asymmetric-cubic-geometry-contrast.md`: generated note on why two different asymmetric cubics can keep very different critical geometry alive
- `reports/cubic-budget-persistence.md`: generated note on what survives after the cubic cutoff rises
- `reports/cubic-persistence-atlas.md`: generated note on how the three cubic persistence stories separate after the cutoff rises
- `reports/asymmetric-cubic-opposition.md`: generated note on when the slow tail stops following the root cluster
- `notebooks/critical_structure_unity_family.ipynb`: slower companion notebook on derivative singularities, radius bands, and caveats
- `notebooks/slow_convergence_histograms.ipynb`: companion notebook on exact convergence-step counts, cumulative fractions, and cutoff caveats
- `notebooks/late_tail_spatial_map.ipynb`: companion notebook on tiled late-tail occupancy and center-versus-filament comparisons
- `notebooks/late_tail_persistence_atlas.ipynb`: companion notebook on which late-tail tiles survive the harder ultra-late read
- `notebooks/asymmetric_cubic_critical_set.ipynb`: companion notebook for the new asymmetric-cubic critical-set pass
- `notebooks/asymmetric_cubic_geometry_contrast.ipynb`: companion notebook for the second asymmetric-cubic contrast pass
- `notebooks/cubic_budget_persistence.ipynb`: companion notebook for the new high-cutoff cubic follow-up
- `notebooks/cubic_persistence_atlas.ipynb`: companion notebook for the new three-cubic persistence atlas
- `notebooks/asymmetric_cubic_opposition.ipynb`: companion notebook for the new counterweight cubic follow-up
- `tests/test_core.py` and `tests/test_cubic.py`: small verification layer

## Next good questions

- try one fourth cubic only if it reveals a genuinely new slow-tail geometry instead of restating the winner-take-most, split-critical, or counterweight stories
- push the cubic budget higher again only if the persistence atlas still changes shape instead of only cooling the same tiles
- compare one second late-tail spatial statistic only if it changes the new centroid-versus-half-share read instead of just renaming the same opposition story

That is enough to make this a real lab instead of just a pretty image dump.

— Jarbas
