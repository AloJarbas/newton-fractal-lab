# Three cubic persistence atlas

This fast pass keeps the old cubic-budget question but stops pretending there were only two asymmetric outcomes worth checking.
The cutoff still rises from `8` to `24` steps. The new question is where the split-critical cubic lands between the repeated-center unity cubic and the winner-take-most asymmetric cubic.

## Main read

- the unity cubic still keeps the hottest surviving center: `77.0%` late-tail share in the center four tiles at `24` steps
- the old asymmetric cubic still cools the hardest: its center stays at `0.0%`, and its inner-band retention falls to `59.0%` of the low-budget value
- the split-critical cubic really does land in the middle lane: its center cools from `61.0%` to `35.8%`, and its inner-band retention stays at `59.6%`
- that middle lane is real geometry, not leftover cutoff fog: the split-critical unresolved share still collapses from `21.9%` to `0.1%`

## Why this changes the repo

The earlier persistence sidecar only settled one contrast: unity cubic versus one asymmetric cubic.
That was honest, but still incomplete.

The split-critical cubic already told us that broken symmetry can stay balanced and hot near the middle of the square.
This atlas checks whether that hotter middle survives a larger cutoff or whether it collapses like the winner-take-most cubic once the budget stops choking the orbit.

It survives, but not all the way to the unity story.

At `24` steps the unity cubic keeps `85.6%` late-tail share in the nearest-critical band, the split-critical cubic keeps `36.0%`, and the old asymmetric cubic keeps only `12.2%`.

That is the bounded upgrade here: the repo no longer treats 'broken symmetry' as one persistence outcome.

## Read the figure

- top row: low-budget late-tail maps at `8` steps for all three cubics
- bottom row: the same maps at `24` steps
- summary block: grid late share, center-four late share, unresolved fraction, and near-critical retention for each cubic

Open `art/cubic-persistence-atlas.svg`, `art/cubic-persistence-atlas.png`, `art/cubic-persistence-atlas.csv`, and `notebooks/cubic_persistence_atlas.ipynb` next.
