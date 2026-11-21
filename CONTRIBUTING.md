# Contributing to i18n-tools

**[Version française](CONTRIBUTING.fr.md)**

---

Thank you for your interest in i18n-tools. This document describes how the
project is developed today.

## Language policy

Code, comments, docstrings, commits, issues, and pull requests are
**English-only until v1.0.0.** This is not a stylistic preference — it is a
project decision, and it stays in effect regardless of the contributor's
native language. Class, method, function and module names remain in English
permanently, even after the planned FR+EN bilingual documentation transition
(post-v1.0.0) — see [issue #93](https://github.com/biface/i18n/issues/93)
for the full rationale.

`README.md`/`README.fr.md` (and this file) are the exception: user-facing
project documents are maintained in parallel, one full document per
language, not generated or auto-translated.

## Design decisions

Architectural or API changes are not implemented ahead of a recorded
decision. Decisions are tracked as GitHub issues labeled `type: decision` —
if you're proposing a change that touches architecture, public API, or the
`.i18t` format, open one of these first so the approach can be discussed
before code is written. The maintainer has final arbitration on design
decisions; discussion on the issue is welcome, but a PR that skips the
decision step for a non-trivial change will likely be asked to add one.

Each category of decision has its own issue form: architecture
(`DA-NNN`), design (`DD-NNN`), technical (`DT-NNN`) and quality
(`DQ-NNN`). The four prefixes share one three-digit counter: check the
existing decision issues for the next free number before choosing a
title such as `[DD-041] Title`. The form applies `type: decision` and
`status: triage`; add the `scope:`, `priority:`, `effort:` and
`ecosystem:` labels that match your answers.

## Development environment

The project uses `uv` + `tox-uv` (not plain `pip`/`virtualenv`). The
project environment holds the package and its runtime dependencies only:

```bash
uv sync --extra api      # the package, with the [api] extra
```

Development tools (tox, the quality tools, the test runners, Sphinx) are
not installed there: tox installs them in its own environments, from
`.tox-config/requirements/*.txt`, where their versions are pinned. The
`[dependency-groups]` of `pyproject.toml` only list their names. tox itself
runs through `uvx`:

```bash
uvx --with tox-uv tox -e local      # apply black and isort, then every check and full coverage
uvx --with tox-uv tox -e pre-push   # last gate before pushing: checks only, stops on any finding
uvx --with tox-uv tox -e ci-quality # exactly what CI's `quality` job runs
uvx --with tox-uv tox               # every check environment (env_list)
```

`pre-push` does not modify files: when it reports a formatting issue, run
`local` (or `format`) and run `pre-push` again. See `pyproject.toml`'s
`[tool.tox]` table for the full environment list.

Individual tools (`basedpyright`, `flake8`, `black`, `isort`, `bandit`) each
have their own `tox` environment if you want to run just one.

Install the versioned Git hooks once per clone:

```bash
uvx --with tox-uv tox -e hooks   # git config core.hooksPath .githooks
```

- `commit-msg` refuses a message that does not follow Conventional
  Commits (`type(scope)!: description`, blank second line,
  `BREAKING CHANGE:` footer when the subject carries `!`, subject of at
  most 100 characters, 72 recommended);
- `pre-push` runs `tox -e pre-push` before `git push` and aborts the
  push when it fails; it refuses a push with uncommitted changes to
  tracked files or of a ref other than `HEAD`, since the gate tests the
  working tree.

`--no-verify` bypasses either hook for one commit or push.

Python versions are set in two files, and only there:

- `.tox-config/versions.txt`: one tox environment per line with its
  markers, `local` (run by `pre-push`), `ci` (the CI test matrix),
  `experimental` (allowed to fail, needs `ci`; with `local`, `pre-push` runs
  it and only warns when it fails), e.g. `py315 local ci experimental`;
- `.tox-config/coverage-version.txt`: the version that measures coverage
  (marked `local` and `ci`). Locally it is tested once, by the coverage
  run.

When a version is added or retired, update the `Programming Language`
classifiers of `pyproject.toml` too: `tox -e versions` (run first by
`ci-quality`, `pre-push` and `local`) stops on any inconsistency between
the two files and the classifiers.

The documentation builds with `tox -e docs` (`sphinx-build -E -W`, warnings
as errors, output in `docs/build/html`). It is the build the GitHub Pages
workflow runs, and `pre-push` runs it too.

## Tests

### Directory layout

```
tests/
├── 00_api/          — validate_api_url() / validate_url_format() tests
├── 00_locale/        — locale utility tests (IETF normalisation)
├── 01_loader/        — loaders/loader.py tests (initializes the Config Singleton)
├── 02_models/        — Message, Book, Corpus, Repository model tests
├── 09_config/        — Config / Repository integration tests (Singleton-dependent)
├── mock/              — static repository fixtures (package/ and application/ trees)
├── locales/           — standalone config file fixtures (.json/.yaml/.toml)
├── conftest.py        — session-level fixtures, shared across all suites
├── helpers.py         — copy_and_update_repository(), update_tmp_repository()
├── parametrize.yaml   — centralised, externalised test data
└── test_04_sync.py    — sync.py tests (directory/file scaffolding)
```

Each numbered directory mirrors a layer or concern of `src/i18n_tools/` and
has its own `conftest.py` for suite-local fixtures, inheriting session
fixtures from the root `tests/conftest.py`.

### Execution order — mandatory

`Config` (in `patterns.py`) is a **Singleton**: only one instance exists per
pytest process. The numeric directory prefixes enforce a safe execution
order:

```
00_api, 00_locale   → no Config dependency, can run in any order
01_loader           → initializes the Singleton
02_models           → no Config dependency
09_config           → inherits the Singleton state from 01_loader
```

**`09_config/` must always run after `01_loader/`.** Reversing this order
causes cascading failures in `09_config` because the Singleton would not
have been initialized the way those tests expect. Don't rename directories
in a way that changes their alphabetical/numeric ordering without
re-verifying this constraint — also documented at the top of
`tests/conftest.py`.

### `parametrize.yaml`

Test data is externalised rather than hardcoded. Current top-level
sections: `configuration` (paths to mock source trees), `repository`
(path fragments injected into temporary config files), `repository-content`
(kwargs passed to `Repository()`), `files` (config file names), `setup`
(languages/domains/modules structure). Add new fixture paths/shapes here
rather than hardcoding a path string in a test module.

### `helpers.py` and `mock/`

- `copy_and_update_repository(root_conf_test, tmp_path, conf_tests, key)` —
  copies a mock repository tree (`mock/package/...` or
  `mock/application/...`) into a pytest `tmp_path`, then rewrites its config
  file's `paths.*` entries to point at the temporary location. This is the
  standard way to get an isolated, on-disk repository fixture without
  touching the real `mock/` tree.
- `mock/` holds two source trees, copied (never mutated in place): a
  `package`-context fixture and several `application`-context fixtures,
  both following the real `locales/<lang>/LC_MESSAGES/<domain>.i18t` layout.

### Markers

Declared in `pyproject.toml` (`[tool.pytest.ini_options]`):

- `@pytest.mark.network` — requires real network access (`httpbingo.org`).
  Only run in CI on tags/schedule (`test-integration` job).
- `@pytest.mark.timeout` — makes slow HTTP calls; excluded everywhere in CI
  (`-m "not timeout"`), including the tag-triggered `coverage` job.

### Coverage

Target: **80%** project-wide (v0.7.x milestone), tracked per-module via
Codecov components (`models`, `loaders`, `exceptions`, `converter`,
`config`, `api` — see `.codecov.yml`).

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types in active use in this repository: `feat`, `fix`, `chore`, `ci`,
`docs`, `refactor`, `test`, `perf`, `security`, `build`, `revert`, `style`.
Breaking changes: append `!`
after the type or add a `BREAKING CHANGE:` footer. One logical unit per
commit — group multiple files only when they form a single indivisible
change; don't bundle unrelated concerns together.

## Pull requests

The repository uses the standard label set, in seven categories:
`type:`, `status:`, `priority:`, `scope:`, `effort:`, `ecosystem:` and
`meta:`. Issues are opened from the issue forms (bug, feature,
documentation, technical task and the four decision forms); blank issues
are disabled. The pull request template lists what a PR states.

- Open an issue first for anything beyond a small, obvious fix.
- Before merge, a PR carries a milestone and at least one `type:` label:
  Release Drafter builds the release notes from it.
- Reference the related issue in your PR description (`Closes #NN` /
  `Fixes #NN`) if one exists.
- Make sure `uvx --with tox-uv tox -e pre-push` passes locally before opening the PR —
  CI runs the same checks (`quality` → `test-unit` matrix) and will not
  merge a red build.
- Keep the PR scoped to one concern; split unrelated changes into separate
  PRs.

## Code of Conduct

By participating in this project, you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Questions

Open a [GitHub issue](https://github.com/biface/i18n/issues).
