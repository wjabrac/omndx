# Symbolic Planner

The `SymbolicPlanner` converts high‑level goals into ordered action lists. It
currently accepts three goal shapes:

1. A string with steps separated by `->` (e.g. `"a -> b"`).
2. An iterable of precomputed steps.
3. `None`, which yields an empty plan.

Any other type raises ``ValueError`` to highlight malformed goals. Future work
will introduce a proper planning algorithm and richer goal representations.
