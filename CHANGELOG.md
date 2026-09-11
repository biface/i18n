# Changelog

All notable changes to this project are documented in this file.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Sections per [CONVENTIONS.md](CONVENTIONS.md) §7 (Releases).

Issue/PR references use the GitHub issue number from `biface/i18n`.

---

## v0.10.0 — Fashionably Late (2026-09-11)

*(Title provisional — confirm or replace when writing the GitHub release note; date should match the actual `v0.10.0` tag.)*

### 📦 Release
- **New `[api]` extra.** `requests`, `validators`, `email-validator`,
  and `toml` are no longer unconditional dependencies — they move to
  `pip install pyi18t-tools[api]`. Plain `pip install pyi18t-tools`
  now covers everything needed to load, format, and save an existing
  `.i18t` file (`Message`/`Book`/`Corpus`/`Encyclopaedia`,
  `formatter.publish()`), **and** the CLI's `validate`/`info`/`sync`/
  `repl` commands with a `.yaml`/`.json` settings file — confirmed
  during implementation to need no `[api]`-only functionality at all,
  correcting the sprint's own original assumption. Author/translator
  management (`Config`/`Repository`), translator API URL validation,
  and a `.toml` settings file still require `[api]`. Calling one of
  these without the extra installed raises a plain `ModuleNotFoundError`
  naming the missing package and the install command, instead of a
  bare import failure. (DD-41, #117, #118, #119, #120)
- `dependencies` shrinks from 8 packages to 4: `ndict-tools`, `babel`,
  `langcodes`, `PyYAML`.

### 🔧 Maintenance
- `api.py`/`config.py`: `requests`/`validators`/`email_validator`
  moved from module-level to function-local imports. (#118)
- `loaders/utils.py` split: the settings-file primitives
  (`_load_toml`/`_save_toml`/`_load_config_file`/`_save_config_file`)
  moved to a new `loaders/settings.py`. `toml` itself stays local to
  each function's `.toml`-specific branch — a `.yaml`/`.json` settings
  file needs no `[api]` dependency at all, only `.toml` does. (#119)
- `babel.messages` imports on the confirmed-dead
  `build_repository()`/`verify_repository()`/`create_template()` path
  (`loaders/utils.py`, `loaders/handler.py`) moved behind
  `TYPE_CHECKING` or localized — no dependency change, `babel` stays
  core; this only removes an eager-import cost. (#120)

### 🧪 Tests
- `tests/` reorganized into `tests/core/` (no `[api]` dependency at
  all — verified with none installed: 852 passed), `tests/api/`
  (mocked), and `tests/api/integration/` (real network, tag-only).
  Replaces the previous `-m "not network and not timeout"` marker
  filter with a directory boundary. Also closes a gap found along the
  way: `09_config`'s translator tests made the same real
  `add_translator() → validate_api_url()` call as `00_api`'s tests, but
  were never marked `@pytest.mark.network` — they silently ran real
  network calls inside what was meant to be `test-unit`'s network-free
  selection on `master`/`staging` pushes.
- New `tox -e test-core` environment (`pytest tests/core`, no `[api]`
  extra installed) and a matching CI job, ahead of `test-unit` in the
  pipeline (`quality → test-core → test-unit → …`).

---

## v0.9.0 — Formatting & CLI (2026-08-26)

### ✨ New Features
- `formatter/publish.py` — `publish()`: DD-27's four-step column
  fallback (`messages[plural_index][alternative]` →
  `messages[plural_index][0]` → `messages[0][alternative]` →
  `messages[0][0]`), reading `Message`'s raw attributes
  (`default`/`options`/`default_plurals`/`options_plurals`) directly.
  `Message.format()` is left untouched — existing, tested, single-cell
  API, not the DD-27 algorithm. (#112, #37)
- `formatter/plurals.py` — `PluralRule` (DD-40): a CLDR baseline (via
  Babel) for a given locale, overlaid with explicit business-defined
  thresholds that take priority over the CLDR-derived category. Always
  resolves to an integer plural row index, never a CLDR category
  string. (#110)
- `exceptions.py` — `FormatterError`, `PluralIndexError`,
  `PluralRuleError`. (#111)
- `formatter.py` restructured into a `formatter/` sub-package, mirroring
  `models/`: `__init__.py` (re-exports `publish`, `PluralRule`),
  `publish.py`, `plurals.py`. Public import path unchanged
  (`from i18n_tools import formatter`). (#109)
- `cli.py` — basic CLI on `argparse` (stdlib): `validate <path>` and
  `info <path>` parse the DD-12 `<lang>/LC_MESSAGES/<domain>.<format>.i18t`
  layout and load a `Book`; `sync <config>` loads an application
  `Config` and calls `core.synchronize()`; `repl` is a minimal
  interactive loop. Never imports `i18n_tools.loaders.*` directly —
  `core.py` is the only module outside `loaders/` allowed to do that
  (DD-28). `[project.scripts]` entry point added
  (`i18n-tools = i18n_tools.cli:main`). (#39)

### 🧪 Tests
- `tests/04_formatter/` — 28 tests, 100% statement/branch coverage on
  `formatter/__init__.py`, `plurals.py`, `publish.py`. (#113)
- `tests/05_cli/` — 39 tests, 98% coverage on `cli.py`. `sync` is
  exercised end-to-end via a subprocess: `Config` is a process-wide
  Singleton (`patterns.Singleton`), and `01_loader`/`09_config` depend
  on its state surviving unchanged across the whole suite — an
  in-process `Config(config_path)` call here would silently return
  whatever instance already exists elsewhere in the session. A
  companion in-process test covers `cmd_sync()`'s body itself via an
  `isolated_config_singleton` fixture that saves and restores the
  singleton, leaving no residual state. (#114)

### 🔧 Maintenance
- `tox.ini` removed entirely — unified into `pyproject.toml`'s
  `[tool.tox]` table (`tox>=4.21`, native support), ~20 environments,
  functionally unchanged (amends DD-36, DD-39 — see comments on #90,
  #93). Two dead-config findings along the way:
  - `[gh-actions]` (`tox.ini`) was never actually consulted —
    `python-ci.yaml`'s `test-unit` job has always resolved its own tox
    env (`tox -e py${PYVER}`) and never installed `tox-gh-actions`.
    Dropped.
  - `[tool.flake8]` (`pyproject.toml`) was already inert — flake8 does
    not read `pyproject.toml` without the `Flake8-pyproject` plugin
    (not a dependency here). The real, effective config lived in
    `tox.ini`'s `[flake8]` section (confirmed via its
    `per-file-ignores` rule); consolidated as explicit CLI flags in
    each environment's `commands` instead, alongside `bandit -c
    pyproject.toml` (`[tool.bandit]`).
  - `docs/source/conf.py`'s `release` field was found stale at `0.6.0`
    (unrelated drift since that tag) — will be corrected together with
    the version bump at tag time.

---

## v0.8.0 — Orchestration (2026-07-29)

Combined v0.7.0 + v0.8.0 work cycle, single tag at v0.8.0 (calendar
reagencement decided 2026-07-27 — v0.7.0 was originally scheduled after
v0.8.0 on the GitHub milestones, inconsistent with roadmap order). The
v0.7.0 milestone closes with a "merged into v0.8.0" note rather than
its own tag — no separate release was published for it.

### v0.7.0 — Test coverage & repository hygiene

#### ✨ New Features
- `.codecov.yml` added — 9 components (`models`, `loaders`,
  `exceptions`, `converter`, `config`, `api`, `orchestrator`,
  `translation`, `package`) covering the full `src/i18n_tools/` tree.
  `informational: true` on `master`/`staging/**` for this cycle —
  coverage stays a personal/informative target until v1.0.0, per the
  2026-07-27 clarification (no new DD issued, consistent with DD-36's
  original wording). (#96)
- GitHub issue templates + PR template added, per `CONVENTIONS.md`
  §2/§3 — was a v0.6.0 milestone deliverable that never actually
  shipped. 5 issue forms (`bug_report`, `feature_request`,
  `documentation`, `technical_task`, `design`) plus `config.yml`
  disabling blank issues. `documentation.yml` didn't exist at all
  before; `technical_task.yml` now auto-applies `type: chore` (its
  predecessor, reused from a sibling project, only applied
  `status: triage`, leaving the type unset). (#99)
- `dependabot.yml` added — `github-actions` ecosystem on a quarterly
  cadence, `pip` monthly.
- Real, tag-only release gate for coverage: `tox -e coverage-gate`
  (`coverage report --fail-under=N`), currently inert (`N=0`) until
  v1.0.0. Distinct from and unrelated to Codecov's `informational`
  status, which was never a viable release gate in the first place —
  GitHub's required-status-checks only apply to branches, never to
  tags. Documented as its own decision (DD-39) to prevent the two
  mechanisms from being conflated later.

#### 🐛 Bug Fixes
- `converter.py` — 4 leftover debug `print()` statements removed
  (`i18n_tools_to_unified_format`, `convert_i18n_tools_to_catalog`).
- Stray `.coveragerc` removed. `coverage.py`'s config discovery order
  is `.coveragerc` > `setup.cfg` > `tox.ini` > `pyproject.toml` — first
  file found with any settings wins, all others are silently ignored.
  This leftover file (predating the `pyproject.toml` consolidation) was
  the reason `pyproject.toml`'s coverage settings never took effect.
  Its `omit` list was already a no-op given
  `source = ["src/i18n_tools"]`, and its `if __name__ = "__main__"`
  exclude pattern had a typo (single `=`) and never matched anything.
  Its one genuinely useful pattern, `def __repr__`, was folded into
  `pyproject.toml`'s `exclude_also`.

#### 🔧 Maintenance
- `converter.py` — 13 functions (the intermediate "unified format"
  bridge and every Catalog/i18next conversion function built on it,
  plus `seek_translation`) confirmed to have zero callers anywhere in
  `src/` or `tests/`. DD-15 already called this code obsolete and
  DD-17 already decided it should be `@deprecated` and excluded from
  the public API, but neither had actually been implemented. Now
  marked `@_deprecated_unmaintained` (emits `DeprecationWarning` on
  call) rather than removed — not implementing v2.x/v3.x's rebuild
  early. `message_to_i18n_tools_format`/`i18n_tools_format_to_message_dict`
  (DD-16, actually used by `Book`/`Corpus`/`loader.py`) are untouched.
  Combined with the `.coveragerc` fix above, `converter.py` coverage
  went from 16% (61/381 lines, mostly this dead code) to 92%
  (56 real lines).
- CI: the `coverage` job opened up from tag-only to
  `master`/`staging/**`/`pull_request`, using its own `go-httpbin`
  service container and no longer depending on `test-integration` in
  the `needs:` chain (so it can run in contexts where
  `test-integration`, still tag-only, does not). `build` now lists
  `needs: [coverage, test-integration]` explicitly, preserving the
  release-safety guarantee that both must pass on a tag. (#98)
- GitHub Actions bumped for the Node.js 24 migration (Node20 actions
  forced onto Node24 since 2026-06-02, fully removed 2026-09-16):
  `actions/checkout` v4→v7, `actions/setup-python` v5→v6,
  `codecov/codecov-action` v5→v6, `actions/upload-artifact` v4→v6,
  `actions/download-artifact` v4→v7. `astral-sh/setup-uv` pinned by
  commit SHA (v4→v9.0.0) rather than a floating tag — as of v8.0.0
  that action no longer publishes moving major/minor tags at all.
  `softprops/action-gh-release` (already v3) and
  `pypa/gh-action-pypi-publish` (container-based, not Node) needed no
  change.
- `pyproject.toml` — `[tool.coverage.run] branch = true` added; no
  config anywhere in the repo previously enabled branch-coverage
  measurement (the branch data seen in local runs came from an
  unversioned, machine-local config).

### v0.8.0 — Orchestration

#### ✨ New Features
- `fallback.py` — `resolve(lang, repository) -> list[str]` implemented.
  Pure function, no I/O, no dependency on Message/Book/Corpus: requested
  language → IETF parent (via `langcodes`, not naive string splitting)
  → variants declared under that parent in `Repository.hierarchy` →
  the repository's global fallback language and its own variants.
  De-duplicated, first occurrence wins. (#35)
- `Repository.source`/`Repository.fallback` properties added — the
  two singular `languages` values previously had no accessor at all
  (unlike `hierarchy`, which already had a full property + CRUD API).
  Prerequisite for `fallback.py`.
- `core.py` — the high-level orchestrator is no longer a stub.
  `load_book`/`save_book`/`load_corpus`/`save_corpus`/`synchronize`
  implemented, bridging `Repository` (paths, module/domain/language
  configuration) and the content model (`Message`/`Book`/`Corpus`/
  `Encyclopaedia`). `Book.load()`/`Book.save()` already did the actual
  file I/O; `core.py` only resolves the on-disk directory and
  delegates. `save_book`/`save_corpus` take `module` explicitly rather
  than reading it off `Book`/`Corpus` — neither ever carries it; only
  `Encyclopaedia` and this orchestration layer do. (#36)
- `Corpus.get_real_book(lang)` added — returns the actual registered
  Book, no fallback resolution, as opposed to `get_book()` which always
  returns a `FallbackBook` proxy. Needed by `core.save_corpus()`.
- `Corpus.get_book(lang, repository=None)` — now accepts an optional
  `Repository` to resolve the fallback chain via `fallback.resolve()`
  instead of the inline v0.3.x heuristic. Omitting `repository` keeps
  the exact previous behavior (any loaded language sharing an IETF
  parent counts as a sibling); supplying one respects only what is
  actually declared in `repository.hierarchy`/`fallback`, filtered to
  languages loaded in that Corpus. Fully backward compatible — no
  existing callers, and the no-repository path is unchanged logic.

#### 🐛 Bug Fixes
- `sync.py` — `check_repository()` created files as `{domain}.json`,
  predating `Book`/`build_book_filename`'s actual native `.i18t`
  naming convention (`{domain}.{fmt}.i18t`) — `Book.load()` could never
  find them. `sync.py` was built against an older design, before the
  current `Repository`/`Encyclopaedia`/`Corpus`/`Book`/`Message` model
  was in place, and was never updated. Found via `core.py`'s first
  end-to-end test (`synchronize` → `load_book` → `save_book`), which is
  what actually exercised the two modules together for the first time.
- `sync.py` — `check_repository()` also excluded hierarchy *parent*
  keys from the synced language set (only variants like `fr-FR`/`fr-BE`
  were synced, never `fr` itself, even though it is a legitimate
  fallback language in its own right). Now uses `locale.get_all_languages()`
  (keys + values) — the same helper `core.load_corpus()` uses — so the
  two always agree on which languages must exist on disk.
- `tests/conftest.py` — `use_real_network_resources()` only checked
  `is_main_branch`/`is_tag_ref()`, both false on a `pull_request` event
  (`GITHUB_REF` is `refs/pull/<n>/merge` — neither a branch nor a tag
  ref). Never exercised before: the `coverage` job, which sets
  `HTTPBIN_BASE_URL` and runs its own `go-httpbin` container, was
  tag-only until the v0.7.0 CI restructuring above, so `is_tag_ref()`
  was always true there in practice and the mock path never actually
  activated for this job. Once `coverage` started running on
  `pull_request`/`master`/`staging/**`, the mock activated for the
  first time — but its simulated responses only ever covered the
  public `httpbingo.org` URLs used elsewhere, never this container's
  own `127.0.0.1:8080`, causing `TestValidateApiUrl` failures and a
  `TestConfigTranslators` cascade (`Translator3` never gets created, so
  every subsequent test depending on it in the same `Config` Singleton
  sequence fails too). Fix: `HTTPBIN_BASE_URL` being set is itself a
  reliable signal that a real container is present and should be used —
  added as a third condition. `test-unit` never sets this variable, so
  it doesn't widen real-network use there. Same class of bug as the
  `is_tag_ref()` fix in v0.6.0 — a code path that only ever ran in one
  specific CI context, breaking the first time that context actually
  changed.

#### 🔧 Maintenance
- New `tests/03_orchestration/` directory — `test_00_fallback.py`
  (11 tests), `test_01_sync.py` (moved and extended from the former
  flat `tests/test_04_sync.py`, 6 tests), `test_02_core.py` (10 tests,
  `core.py` 0% → 100% line coverage). `tests/02_models/test_02_corpus.py`
  extended with 4 tests for `get_book(repository=...)`.
- Version bumped 0.6.0 → 0.8.0.

---

## v0.6.0 — CI/CD & repository hygiene (2026-07-05)

### 🔧 Maintenance
- Single-file `python-ci.yaml` pipeline: `quality → test-unit (py310-py314
  matrix) → test-integration → coverage → build → publish-pypi/
  publish-testpypi`, chained via `needs:`. `test-integration`, `coverage`,
  `build`, and `publish-*` are tag-gated. Modelled on `oxiflow`/`clade`.
  Replaces both the old mono-job workflow and the previously-explored
  5-file `workflow_run` design (never implemented). (#90)
- `.codecov.yml` added — per-module components (`models`, `loaders`,
  `exceptions`, `converter`, `config`, `api`), 80% target on `master` and
  `staging/**`.
- `basedpyright`/`flake8` fully activated in `tox.ini`; all findings
  resolved. (#84)
- `loaders/repository.py` and its orphaned Sphinx `.rst` **physically
  deleted**. Documented as retired since #85/#70, but the file (an
  exact duplicate of functions already migrated into `loader.py`) had
  never actually been removed from disk; nothing imported it and the
  Sphinx toctree already excluded it. (#85, #70)
- `models/__init__.py` duplicate resolved — a misnamed `models/init.py`
  is gone; correct exports (`Author`/`Authors`/`Translator`/
  `Translators`) merged into the real `__init__.py`. (#87)
- `CONTRIBUTING.md`/`CONTRIBUTING.fr.md` added (#79): development
  environment (`uv`/`tox-uv`), test suite layout including the `Config`
  Singleton execution-order constraint, Conventional Commits, and the
  current (still informal) PR process. Design decisions are described as
  GitHub issues labeled `type: decision` rather than as references to
  maintainer-internal working documents.
- `README.md`/`README.fr.md` roadmap and feature tables updated to the
  current state: v0.4.x–v0.5.0 delivered, v0.6.x in progress, and the
  v0.8.0/v0.9.0 split from v1.0.0 (`core.py`/`fallback.py` and
  `formatter.py`/`PluralRule`/CLI moved out of the v1.0.0 freeze
  milestone, 2026-07-04).
- `mirror.yml` added — mirrors `biface/i18n` to `gitlab.com/open-works/
  i18n.git` on every branch/tag push and on ref deletion, following the
  `ndt`/`fsm` pattern (`--prune` with explicit branch/tag ref specs,
  unlike `oxiflow`'s variant which declares a `delete:` trigger but omits
  `--prune`).
- `docs-ghpages.yml` added (#80) — single-version Sphinx/Furo build
  deployed to GitHub Pages on final release tags only (no `rc`, no
  `sphinx-multiversion` — both deferred).
- `.readthedocs.yaml` added — parallel ReadTheDocs hosting via native
  `uv sync --group docs` support; no GitHub secret required (webhook-based
  once the project is imported on readthedocs.org).
- Network tests made CI-independent of the public httpbingo.org uptime:
  `tests/helpers.py:HTTPBIN_BASE_URL` (default `https://httpbingo.org`,
  unchanged locally) is now read by `test_00_api.py` and the `Translator3`
  fixture; `test-integration` and `coverage` (both tag-gated, both running
  `@pytest.mark.network` tests) start a `ghcr.io/mccutchen/go-httpbin`
  service container and point `HTTPBIN_BASE_URL` at it instead. Required
  adding `passenv = HTTPBIN_BASE_URL` to `[testenv:integration]`/
  `[testenv:coverage]` in `tox.ini` — tox 4 does not forward arbitrary env
  vars to the test subprocess by default.
- `release-template-semver.yml` (`.github/`) + `release-drafter-semver.yml`
  workflow added — maintains an internal draft-only preview of merged-PR
  notes, categorized by the existing `type:` labels (CONVENTIONS.md §7).
  Deliberately **not** wired into tag creation or `python-ci.yaml`: tags
  stay fully manual, `action-gh-release` (in `publish-pypi`/
  `publish-testpypi`) remains the sole mechanism that creates a real
  release.

### 🐛 Bug Fixes
- `pyproject.toml` — removed `venvPath`/`venv` from `[tool.basedpyright]`.
  These pointed at a machine-local virtualenv absent from a clean CI
  checkout, causing `basedpyright` to exit with a fatal configuration-error
  code (`3`) that the tolerant `[ $code -le 1 ]` guard in the `ci-quality`
  tox environment does not cover — CI failed even though the actual
  diagnostics were clean (0 errors, warnings only). Reproduced locally
  with the exact CI `basedpyright` version to confirm.
- `loader.py` — `tar.extractall()` now passes `filter="data"`
  conditionally (`sys.version_info >= (3, 12)`). Without an explicit
  `filter`, Python 3.12/3.13 emit a `DeprecationWarning` and Python 3.14
  will change its default behavior (PEP 706); the `filter` parameter does
  not exist at all on Python 3.10/3.11, so it is omitted there rather than
  raising a `TypeError`. (#86)
- `CONTRIBUTING.md`/`.fr.md` incorrectly stated no label taxonomy existed
  on the repository; corrected — the 8-category taxonomy is applied, only
  issue/PR templates remain pending.
- `tests/conftest.py` — network tests silently fell back to mocks on
  tag-triggered CI runs. `get_current_git_branch()` only recognized
  `refs/heads/...`; on a tag, `GITHUB_REF` is `refs/tags/...` and
  `actions/checkout` leaves a detached HEAD, so `is_main_branch` was
  always `False` there. Added `is_tag_ref()` and OR'd it into
  `use_real_network_resources`, `patch_validate_api_url`, and
  `patch_validate_email` (the latter two also used by
  `tests/09_config/` and `TestRepositoryMethods`, autouse — same bug,
  different call sites, found only once the tag pipeline actually ran
  for the first time).
- `tox.ini` — added `passenv = GITHUB_REF, CI_COMMIT_REF_NAME,
  CI_COMMIT_TAG` to `[testenv:integration]`/`[testenv:coverage]`. tox 4
  does not forward arbitrary environment variables to the test
  subprocess by default; `is_tag_ref()` (above) needs `GITHUB_REF` to
  actually reach pytest.
- `python-ci.yaml` — `HTTPBIN_BASE_URL` changed from
  `http://localhost:8080` to `http://127.0.0.1:8080`. `validators.url()`
  (used by `api.py`'s `validate_url_format()`) rejects `localhost` as an
  invalid domain (no TLD, not a valid IP) but accepts the literal IP;
  the go-httpbin container was reachable on both, this was purely a
  string-validation issue, not a networking one.
- `python-ci.yaml` — added `permissions: contents: write` to
  `publish-pypi` and `publish-testpypi`. `softprops/action-gh-release`
  needs it to create the release; `docs-ghpages.yml` already declared
  it, `python-ci.yaml` didn't.

### 📦 Release
- **PyPI distribution renamed**: `i18n-tools` → `pyi18t-tools`.
  `i18n-tools` was rejected by TestPyPI ("too similar to an existing
  project", likely `RF-i18n-tool`, one character away after
  normalization) and the `i18n-tool(s)` namespace is crowded on the real
  registry too. `pyi18t-tools` ties to the project's own `.i18t` format
  rather than a personal name. Required an explicit
  `[tool.hatch.build.targets.wheel/sdist]` in `pyproject.toml`, since
  hatchling's default src-layout auto-detection derives the expected
  folder from the project name and would otherwise look for
  `src/pyi18t_tools/` instead of the real `src/i18n_tools/`. The
  importable module is unchanged: `pip install pyi18t-tools` +
  `import i18n_tools`.
- Validated end-to-end via `v0.6.0rc1`–`rc3` on `staging/v0.6.0`: rc1 and
  rc2 surfaced the four issues above in sequence (each only visible once
  the previous one was fixed); rc3 published successfully to
  `test.pypi.org` under the new distribution name.
- Version bumped 0.5.0 → 0.6.0 (`pyproject.toml`, `__static__.py`,
  `docs/source/conf.py`).

---

## v0.5.0 — Architecture & layering hardening (2026-06-28)

### 🐛 Bug Fixes
- **KI-01** — `Repository.add_translator()` performed a real network call
  (`api.validate_api_url()`) inside a synchronous, model-internal
  validation path, causing CI to fail on `master` whenever the test
  translator's URL was unreachable. Replaced with `validate_url_format()`
  (syntax only, no network). (#70)
- A second, independent occurrence of the same symptom was found in
  `Config.add_translator()`'s own, legitimate `validate_api_url()` call —
  not a defect, but its test fixture (`Translator3`, `https://doe.com`)
  had drifted to a real `404` on the live internet since the test was
  written. Updated to a known-stable endpoint (`https://httpbingo.org/get`).
- `tests/00_api/test_00_api.py` network fixtures (`httpbin.org`) were
  intermittently returning `503`/unexpected status codes due to upstream
  flakiness, unrelated to any code change here. Switched to the
  `httpbingo.org` mirror (Go port of the same service, same endpoint
  shapes). `go-httpbin`'s `/delay` endpoint caps at 10s server-side
  (`/delay/15`, `/delay/25` replaced with `/delay/6`, `/delay/8`).

### 🔧 Maintenance
- `loader.py` is now the sole bridge between `/models/` and the rest of
  `/loaders/`: `handler.py`/`utils.py` are never imported
  directly from `/models/`. Three new pass-throughs added
  (`file_exists`, `is_absolute_path`, `normalize_module_identifier`),
  mirroring the existing `build_book_filename` pattern. (#70)
- `loaders/repository.py` retired — legacy code with no production
  callers. Its 8 functions (`create_module_archive`,
  `restore_module_from_archive`, `build_repository`, `verify_repository`,
  `aggregate_dictionaries`, `add_translation_set`, `update_translation_set`,
  `remove_translation_set`) migrated into `loader.py`. (#69, #70)
- `models/repository.py` no longer imports `..api` or `..loaders.handler`
  directly — zero I/O performed by the model itself. (#70)
- `models/author.py`, `models/translator.py` *(new)* — `Author`/`Authors`
  and `Translator`/`Translators`, subclassing `StrictNestedDictionary`
  like `Repository`. Construction, validation, and storage logic for
  authors and translators moved here from `Repository`'s private helpers
  and `Config`'s inline logic; `Repository`'s public CRUD API is
  unchanged, delegating internally. (#17, #25)
- `Config._email_index` removed entirely. Cross-config
  (`package`/`application`) email lookup now queries both `Repository`
  instances via `Authors.get_id_by_email()` — using `ndict-tools`'
  `ancestors()` (a DFS value search) rather than a manual scan — with no
  parallel index to keep in sync. `Config` holds no state of its own
  beyond `_current_config`. (#17, #25)
- `Config.add_author()`/`add_translator()`/`update_translator()`/
  `remove_author()` keep their own pre-checks before delegating storage
  mutation to `Repository`, so exception types/messages observed by
  callers of `Config` are unchanged (transparent delegation). (#17, #25)
- Version bumped to `0.5.0` (`pyproject.toml`, `__static__.py`).

### 🧪 Tests
- Five `@pytest.mark.skip(reason="ndict_tools equality has be rewieved")`
  tests, frozen since before `ndict-tools` 1.2.0, unskipped — confirmed
  passing with no rewrite needed. `==` between `StrictNestedDictionary`
  and a plain `dict` compares by content (standard `dict` semantics), not
  by the stricter `equal()` contract (exact class match).
- Baseline: 1069 passed / 4 failed (KI-01) / 41 skipped → **1114 passed /
  0 failed / 0 skipped**.

---

## v0.4.0 — Quality, coverage & documentation (2026-06-27)

### 🐛 Bug Fixes
- `Repository.add_value()`: the guard `value is not None or not value` was a
  tautology (always `True` for any input) — `add_value()` could never
  succeed on its intended use case (an empty path) and silently overwrote
  any already-set value, including with `None`/`""`. (#29)
- `loader.load_book()`: never called `_detect_format()`, always loaded via
  `_load_json()` regardless of the file's actual extension — a
  `.yaml.i18t` file was silently parsed as JSON. (#67)
- `loader.py::_save_po` (dead code, removed) carried a regression of a bug
  already fixed once in v0.1.x (#8): opened its target file in read mode
  then attempted to write to it.
- `loaders/utils.py`: 11 functions masked every failure (malformed
  JSON/YAML/TOML, permission errors, etc.) as `FileNotFoundError`. Specific,
  actionable exceptions now propagate naturally. (#26)
- `loaders/utils.py::_load_config_file`: accepted `.yml` as a valid
  extension but had no branch to handle it, silently returning `None`. (#26)
- `loaders/handler.py::_verify_target_domain`: raised `IndexError` for a
  missing domain while its own docstring promised `ValueError`; the
  module-not-registered case was re-wrapped, losing the original
  traceback. Realigned to raise `ValueError` consistently, propagating the
  module error naturally instead of masking it. (#27)
- `sync.py::check_repository`: `.pot` files were created once per
  *language* inside `LC_MESSAGES/` instead of once per *domain* in
  `templates/`. (#30)

### 🔧 Maintenance
- Resolved the circular import between `i18n_tools.__init__` and three
  internal modules (`models/corpus.py`, `loaders/handler.py`,
  `loaders/repository.py`); `__version__` now lives in `__static__.py`.
  `Config` is exposed in the public API for the first time. (#64)
- `models/corpus.py` (`Book`) no longer imports `loaders.utils` directly;
  format resolution now goes through `loader.build_book_filename()`.
  Also fixes an inconsistency where the constructor accepted invalid
  formats silently while `add_format()`/`update_format()` did not. (#66)
- `loaders/loader.py`: removed 9 dead functions (6 private + 3 public
  PO/POT/MO wrappers), fully redundant with `utils.py`/`handler.py`. (#67)
- `models/repository.py`: extracted duplicated type-dispatch logic from
  `remove_value()`/`clean_value()` into `_empty_value_for()`. (#28)
- `loaders/handler.py`: removed 12 no-value `try/except Exception as e:
  raise e` wrappers; removed the dead stub `dump_catalog()`
  (duplicate of `update_catalog()`, never called or tested). (#27, #68)
- `loaders/utils.py::_check_domains`: removed the same no-value
  `except ValueError as e: raise e` pattern. (#26)
- `pyproject.toml`: fixed `[project.urls]` pointing to `biface/ndt`
  instead of `biface/i18n`; removed duplicate unconstrained
  `ndict-tools` dependency entries in tox environments. (#63)

### 🧪 Tests
- `loaders/loader.py` coverage: 43% → 100% (`load_locale_json`,
  `aggregate_locale_json`, `save_locale_json`,
  `save_aggregated_locale_json` had no direct test before). Loaders layer
  overall: 87% → 94%. (#31)
- First tests for `sync.py` (`check_repository`) — none existed before. (#30)
- First direct tests for `Repository.add_value`/`update_value`/
  `remove_value`/`clean_value`. (#29)

### 📚 Documentation
- Corrected a prior audit: `loaders/repository.py` is live, tested code (archive
  and aggregation operations with no equivalent elsewhere) — not the dead
  legacy loader the decision assumed without inspection. (#65)
- Split the bilingual `README.md` into separate `README.md` (EN) and
  `README.fr.md` (FR), refreshed the roadmap to reflect `v0.3.x` as
  delivered and added the `v0.5.x`/`v0.6.x`/`v0.7.x` milestones.
- `LICENSE.md` described `ndict-tools` instead of `i18n-tools` (copy-paste
  leftover); corrected, then split into `license.md` (EN) / `licence.md`
  (FR), matching the README split.
- Same correction applied to `CODE_OF_CONDUCT.md` / `CODE_DE_CONDUITE.md`
  (referenced `ndict-tools`).
- Sphinx/Furo documentation initialised: theme switched to Furo,
  `Makefile`/`make.bat` added (were missing), `format.rst`/
  `repository.rst` confirmed correctly migrated. Fixed a regression where
  several `.rst` files still referenced functions removed earlier in this
  same milestone (#67/#68); fixed broken cross-references pointing at
  nonexistent or wrongly-named pages; fixed malformed RST in two
  docstrings (`Repository`, `load_locale_json`) that broke the build.
  `cd docs && make html` now succeeds with zero warnings. (#34)
- GitHub Pages deployment and `sphinx-multiversion` deliberately deferred
  to v0.6.x / v1.0.0 respectively — not part of this release.

---

## v0.3.x — Complete model hierarchy (2026-05-31)

### ✨ New Features
- `Corpus` fixed; `FallbackBook` implemented — transparent multi-language
  fallback resolution. (#18)
- `Encyclopaedia` implemented with lazy corpus loading. (#19)
- `exceptions.py` — `I18nToolsError` hierarchy. (#20)
- Complete public API exposed in `src/i18n_tools/__init__.py`. (#22)
- `Book.save()` — model-to-disk persistence. (#57)

### 🐛 Bug Fixes
- Test suite failed on `master` under an English locale (`LANG=en`);
  `api.py` error messages were locale-dependent. (#59)

### 🔧 Maintenance
- `models/__init__.py`: added missing `Book` and `Encyclopaedia` exports. (#21)
- Test infrastructure audited and reorganised (numbered directories,
  nested `conftest.py`, network/timeout markers). (#32)
- Public API surface finalised: `__init__.py` exports, `loaders/` kept
  out of the public API, `models/__init__.py` exports settled. (#48)
- Exception hierarchy and error handling policy finalised. (#49)
- `api.py` language policy and test assertion strategy recorded. (#60)

### 🧪 Tests
- `Corpus`, `Encyclopaedia`, `FallbackBook`. (#23)
- `Repository` — construction, defaults, CRUD methods. (#24)

---

## v0.2.x — Loader ↔ model bridge (2026-05-03)

### ✨ New Features
- `load_book()` implemented in `loader.py` — the central loader ↔ model
  bridge. (#16)
- `_detect_format()` added to `loaders/utils.py`. (#56)

### 🐛 Bug Fixes
- `loaders/repository.py` ignored the `.i18t` extension (2 FIXMEs). (#13)
- `update_catalog()` was commented out — `.po` files were never synced
  after JSON changes. (#14)

### 🔧 Maintenance
- `aggregate_dictionaries()`: fixed wrong output filename and metadata
  key. (#15)
- Native `.i18t` format finalised: extension, internal structure,
  repository layout. (#44)
- External dependencies scoped: Babel, langcodes, ndict-tools. (#45)
- Hub-and-spoke conversion architecture and native serialisation
  finalised. (#46)
- `Config` Singleton, `Repository` migration, and CRUD API finalised. (#47)
- `.i18t` naming convention and format detection finalised. (#55)

---

## v0.1.x — Foundational cleanup (2026-03-24)

### 🐛 Bug Fixes
- Typo `__ALL__` → `__all__` in package `__init__.py`. (#6)
- `Corpus.__init__`: `self.messages` was never initialized. (#7)
- `_save_po` opened its target file in read mode (`'r'`) instead of write
  mode (`'w'`). (#8)
- `create_template` compared the `fuzzy` flag to the string `'True'`
  instead of a boolean. (#9)
- `formatter.publish()` called a non-existent `Message.format()` — stub
  implemented with column fallback. (#12)

### 🔧 Maintenance
- Reserved field `plural_rule = None` added to `Message` and `Book`. (#10)
- Removed 10 leftover debug `print()` calls from production code. (#11)
- `messages[row][col]` matrix structure and free plurals finalised. (#40)
- Layered architecture and strict model/layer separation finalised. (#41)
- Four-level model hierarchy, `Book` as atomic persistence unit,
  finalised. (#42)

---

## Custom format (2026-03-14)

Initial exploration phase: evaluating translation file formats before
settling on the native, object-oriented `.i18t` design that the project
has used ever since.
