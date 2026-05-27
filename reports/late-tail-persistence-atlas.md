# Late-tail persistence atlas

This follow-up keeps the old local late-tail map, but asks a harder question.
The earlier figure marked starts that needed at least `20` Newton steps, or never settled within `40` steps.
This atlas asks which tiles still look hard when the cutoff rises to `80` and the threshold rises with it to `40` steps.

## Main read

- `z^3 - 1` almost fully cools at the harder read: its grid late share falls to 0.0%, and the center four tiles drop to 0.0%
- `z^6 - 1` keeps a smaller but real core: its center four tiles fall from 100.0% to 55.0%, so the old halo was not pure cutoff fog, just much softer than it first looked
- `z^9 - 1` keeps the center almost completely hot even at the harder read: 100.0% of the center four tiles still need at least 40 steps
- `z^12 - 1` is the strongest persistence case in this packet: 23.6% of the whole sampled square and 100.0% of the center four tiles still survive the harder cutoff

## Why this earns a new sidecar

The earlier late-tail map answered a real first question: where did the slow region live?
It did not answer the next one: how much of that heat was truly ultra-late structure, and how much was just moderate slowness sitting below the old 40-step ceiling?

This pass finally separates those cases.

At the harder read, `z^3 - 1` is basically clean, `z^6 - 1` keeps a trimmed center, and `z^9 - 1` plus `z^12 - 1` still hold a real ultra-late core. That is the new geometric fact: higher powers are not only slower on average, they keep a center halo that survives even after the old entire iteration budget becomes the new late-threshold.

## Per-power summary

### z^3 - 1

- grid late share: 1.0% at the scouting read, 0.0% at the harder read
- center four tiles: 4.5% -> 0.0%
- retained grid share: 1.4%
- unresolved share: 0.0% -> 0.0%

### z^6 - 1

- grid late share: 16.7% at the scouting read, 4.4% at the harder read
- center four tiles: 100.0% -> 55.0%
- retained grid share: 26.6%
- unresolved share: 4.2% -> 0.4%

### z^9 - 1

- grid late share: 27.9% at the scouting read, 14.7% at the harder read
- center four tiles: 100.0% -> 100.0%
- retained grid share: 52.8%
- unresolved share: 14.2% -> 4.9%

### z^12 - 1

- grid late share: 34.7% at the scouting read, 23.6% at the harder read
- center four tiles: 100.0% -> 100.0%
- retained grid share: 68.0%
- unresolved share: 23.3% -> 13.3%

## Read the figure

- left panel in each card: the old local read, `≥ 20` steps or unresolved by `40`
- right panel in each card: the surviving ultra-late read, `≥ 40` steps or unresolved by `80`
- the retention numbers tell you how much of the original late-tail mass survives once the definition becomes much stricter

Open `art/late-tail-persistence-atlas.svg`, `art/late-tail-persistence-atlas.png`, `art/late-tail-persistence-atlas.csv`, and `notebooks/late_tail_persistence_atlas.ipynb` next.
