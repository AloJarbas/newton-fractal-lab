# Cubic budget persistence

This pass keeps the same two cubics but changes the Newton cutoff from `8` steps to `24` steps.
The narrow question is the useful one: how much of the old drama was just a tight cutoff, and how much of it survives as a real slow region once the budget rises?

## Main read

- the unity cubic center stays hot even after the budget rises: the center four tiles only cool from `93.0%` to `77.0%` late-tail share
- the asymmetric cubic cools much harder over the same jump: the center four tiles fall from `0.0%` to `0.0%`
- unresolved starts explain part of the low-budget picture, especially for the unity cubic: its unresolved share drops from `22.5%` to `0.2%`
- but the repeated center critical point still leaves a persistent slow core: the nearest-critical unity band stays at `85.6%` tail share even at `24` steps, versus `12.2%` for the asymmetric cubic

## Why this matters

The earlier asymmetric-cubic comparison showed that broken symmetry changes basin shares and critical-point geometry.
This follow-up asks the next honest question: was the hotter unity core only a low-budget artifact?

The answer is no.

At `8` steps both cubics still mix real slow geometry with plain cutoff trouble. Once the cutoff rises to `24`, most of the asymmetric-core drama cools away, but the unity cubic keeps a much fatter slow center. That is the bounded persistence effect this sidecar adds.

## Summary table

- unity cubic, 8 steps: grid late `22.5%`, center four tiles `93.0%`, unresolved `22.5%`
- unity cubic, 24 steps: grid late `16.6%`, center four tiles `77.0%`, unresolved `0.2%`
- asymmetric cubic, 8 steps: grid late `11.1%`, center four tiles `0.0%`, unresolved `11.1%`
- asymmetric cubic, 24 steps: grid late `6.2%`, center four tiles `0.0%`, unresolved `0.0%`

## Read the figure

- top row: low-budget tail-or-cutoff map at `8` steps
- bottom row: the same map after the cutoff rises to `24` steps
- right-side charts: critical-distance tail share with unresolved starts counted as part of the low-budget tail story

Open `art/cubic-budget-persistence.svg`, `art/cubic-budget-persistence.png`, `art/cubic-budget-persistence.csv`, and `notebooks/cubic_budget_persistence.ipynb` next.
