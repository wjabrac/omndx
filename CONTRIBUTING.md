# Contributing

We follow semantic versioning and conventional commits (e.g. `feat:`, `fix:`). Run `ruff`, `mypy`, and `pytest` before submitting a PR.

## Resolving merge conflicts

When your branch diverges, prefer rebasing onto the latest `main` to keep history clean:

1. Fetch and rebase: `git fetch origin && git rebase origin/main`.
2. Resolve conflicted files by choosing the version that preserves current behavior and tests; avoid dropping new test coverage.
3. After edits, run `pytest` (and `ruff`/`mypy` if available) to confirm the merged code still passes.
4. Amend the commit if needed (`git commit --amend`) and continue the rebase (`git rebase --continue`).
5. Push with force-with-lease: `git push --force-with-lease` to update the PR safely.

If a rebase is too risky, coordinate with reviewers, merge `origin/main`, and document the resolution strategy in the PR description.
