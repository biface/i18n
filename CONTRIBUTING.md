# Contributing to i18n-tools

**[Version française](CONTRIBUTING.fr.md)**

---

Thank you for your interest in i18n-tools. This document describes how the
project is developed today. It reflects the *current* state of the tooling
and process — some items (issue/PR templates, `labels.yml`) are part of the
v0.6.x CI/repository hygiene milestone and are not fully in place yet; this
document does not pretend otherwise.

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

## Development environment

The project uses `uv` + `tox-uv` (not plain `pip`/`virtualenv`):

```bash
uv sync --group dev             # tox, quality tools, test runners
uv sync --group dev --group docs  # + Sphinx/Furo for documentation work
```

All checks and tests run through `tox` — see `tox.ini` for the full
environment list. In particular:

```bash
uv run tox -e pre-push   # quality gate + unit tests — run this before pushing
uv run tox -e local      # full workflow: auto-fix, all quality checks, full coverage
uv run tox -e ci-quality # exactly what CI's `quality` job runs
```

Individual tools (`basedpyright`, `flake8`, `black`, `isort`, `bandit`) each
have their own `tox` environment if you want to run just one.

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
`docs`, `refactor`, `test`, `perf`, `security`. Breaking changes: append `!`
after the type or add a `BREAKING CHANGE:` footer. One logical unit per
commit — group multiple files only when they form a single indivisible
change; don't bundle unrelated concerns together.

## Pull requests

This repository does not yet have a formal issue/PR template or label
taxonomy (`labels.yml`) — that tooling is part of the v0.6.x CI/repository
hygiene milestone and not fully in place. In the meantime:

- Open an issue first for anything beyond a small, obvious fix.
- Reference the related issue in your PR description (`Closes #NN` /
  `Fixes #NN`) if one exists.
- Make sure `uv run tox -e pre-push` passes locally before opening the PR —
  CI runs the same checks (`quality` → `test-unit` matrix) and will not
  merge a red build.
- Keep the PR scoped to one concern; split unrelated changes into separate
  PRs.

## Code of Conduct

By participating in this project, you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Questions

Open a [GitHub issue](https://github.com/biface/i18n/issues).
