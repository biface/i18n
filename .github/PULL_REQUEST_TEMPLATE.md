<!--
Before submitting: a milestone must be assigned to this PR, and at least
one `type:` label must be set (Release Drafter uses it to build the
changelog) — CONVENTIONS.md §3. Neither can be enforced by this template;
both are on you or the reviewer to set before merge.
-->

## Summary

<!-- What does this PR do, in 1-3 sentences? -->

## Type of change

- [ ] `feat` — new feature or user-facing functionality
- [ ] `fix` — bug fix
- [ ] `perf` — performance improvement
- [ ] `security` — security fix or hardening
- [ ] `docs` — documentation only
- [ ] `refactor` — restructuring, no behaviour change
- [ ] `chore` — build, deps, config
- [ ] `ci` — CI/CD pipelines, workflows
- [ ] `test` — adding or fixing tests
- [ ] `breaking` — introduces a breaking API change (also add the `type: breaking` label)

## Related issues

<!-- Closes #123 / Fixes #123 / Refs #123 -->

## List of changes

<!--
- ...
- ...
-->

## Testing

- [ ] `tox -e ci-quality` passes locally (basedpyright, flake8, black, isort, bandit)
- [ ] `tox -e local` (or the relevant `pyXXX` env) passes locally
- [ ] New/changed behaviour is covered by tests
- [ ] Coverage impact checked (`tox -e coverage`) — informational only before v1.0.0

## Documentation

- [ ] Docstrings updated for any changed public API
- [ ] `DESIGN_DECISIONS.md` updated if this PR implements or amends a DD
- [ ] `CHANGELOG.md` entry added if user-facing

## Notes for the reviewer

<!-- Anything the reviewer should pay particular attention to. -->
