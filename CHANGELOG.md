# Changelog

All notable changes to this project are documented in this file.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Sections per [CONVENTIONS.md](CONVENTIONS.md) §7 (Releases).

Issue/PR references use the GitHub issue number from `biface/i18n`.

---

## v0.6.0 — CI/CD & repository hygiene (2026-07-05)

### 🔧 Maintenance
- Single-file `python-ci.yaml` pipeline: `quality → test-unit (py310-py314
  matrix) → test-integration → coverage → build → publish-pypi/
  publish-testpypi`, chained via `needs:`. `test-integration`, `coverage`,
  `build`, and `publish-*` are tag-gated. Modelled on `oxiflow`/`clade`.
  Replaces both the old mono-job workflow and the previously-explored
  5-file `workflow_run` design (never implemented). (DD-36 amendment, #90)
- `.codecov.yml` added — per-module components (`models`, `loaders`,
  `exceptions`, `converter`, `config`, `api`), 80% target on `master` and
  `staging/**`.
- `basedpyright`/`flake8` fully activated in `tox.ini`; all findings
  resolved. (#84)
- `loaders/repository.py` and its orphaned Sphinx `.rst` **physically
  deleted**. Documented as retired since DD-37/#85/#70, but the file (an
  exact duplicate of functions already migrated into `loader.py`) had
  never actually been removed from disk; nothing imported it and the
  Sphinx toctree already excluded it. (#85, #70)
- `models/__init__.py` duplicate resolved — a misnamed `models/init.py`
  is gone; correct DD-37 exports (`Author`/`Authors`/`Translator`/
  `Translators`) merged into the real `__init__.py`. (#87)
- `CONTRIBUTING.md`/`CONTRIBUTING.fr.md` added (#79): development
  environment (`uv`/`tox-uv`), test suite layout including the `Config`
  Singleton execution-order constraint, Conventional Commits, and the
  current (still informal) PR process. Design decisions are described as
  GitHub issues labeled `type: decision` rather than as references to
  `DESIGN_DECISIONS.md`/`PROJECT_STATUS.md`, which are maintainer-internal
  working documents, not contributor-facing artifacts.
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
  `sphinx-multiversion` — both deferred, DD-33).
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
  (DD-10) rather than a personal name. Required an explicit
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
  `/loaders/` (DD-06, DD-37): `handler.py`/`utils.py` are never imported
  directly from `/models/`. Three new pass-throughs added
  (`file_exists`, `is_absolute_path`, `normalize_module_identifier`),
  mirroring the existing `build_book_filename` pattern. (#70)
- `loaders/repository.py` retired — pre-DD-06 legacy with no production
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

### 📐 Design Decisions Recorded
- DD-37 — Sealing `handler.py`/`utils.py` below `loader.py`; retiring
  `loaders/repository.py`; removing I/O from `Repository`; introducing
  `Author`/`Authors` and `Translator`/`Translators`. (#69, #70, #17, #25)

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
  `templates/` (DD-12). (#30)

### 🔧 Maintenance
- Resolved the circular import between `i18n_tools.__init__` and three
  internal modules (`models/corpus.py`, `loaders/handler.py`,
  `loaders/repository.py`); `__version__` now lives in `__static__.py`.
  `Config` is exposed in the public API for the first time. (#64)
- `models/corpus.py` (`Book`) no longer imports `loaders.utils` directly
  (DD-06); format resolution now goes through `loader.build_book_filename()`.
  Also fixes an inconsistency where the constructor accepted invalid
  formats silently while `add_format()`/`update_format()` did not. (#66)
- `loaders/loader.py`: removed 9 dead functions (6 private + 3 public
  PO/POT/MO wrappers), fully redundant with `utils.py`/`handler.py`. (#67)
- `models/repository.py`: extracted duplicated type-dispatch logic from
  `remove_value()`/`clean_value()` into `_empty_value_for()`. (#28)
- `loaders/handler.py`: removed 12 no-value `try/except Exception as e:
  raise e` wrappers (DD-26); removed the dead stub `dump_catalog()`
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
- Corrected DD-19: `loaders/repository.py` is live, tested code (archive
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
- Sphinx/Furo documentation initialised (DD-33): theme switched to Furo,
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
  fallback resolution (DD-09, DD-09b). (#18)
- `Encyclopaedia` implemented with lazy corpus loading. (#19)
- `exceptions.py` — `I18nToolsError` hierarchy (DD-24). (#20)
- Complete public API exposed in `src/i18n_tools/__init__.py` (DD-21). (#22)
- `Book.save()` — model-to-disk persistence (DD-06, DD-15). (#57)

### 🐛 Bug Fixes
- Test suite failed on `master` under an English locale (`LANG=en`);
  `api.py` error messages were locale-dependent. (#59)

### 🔧 Maintenance
- `models/__init__.py`: added missing `Book` and `Encyclopaedia` exports. (#21)
- Test infrastructure audited and reorganised (numbered directories,
  nested `conftest.py`, network/timeout markers). (#32)

### 🧪 Tests
- `Corpus`, `Encyclopaedia`, `FallbackBook`. (#23)
- `Repository` — construction, defaults, CRUD methods. (#24)

### 📐 Design Decisions Recorded
- DD-09/DD-09b — `FallbackBook` proxy for multi-language resolution. (#43)
- DD-21/DD-22/DD-23 — Public API: `__init__.py`, loaders boundary, models
  exports. (#48)
- DD-24/DD-25/DD-26 — Exception hierarchy and error handling policy. (#49)
- DD-35 — `api.py` language policy and test assertion strategy. (#60)

---

## v0.2.x — Loader ↔ model bridge (2026-05-03)

### ✨ New Features
- `load_book()` implemented in `loader.py` — the central loader ↔ model
  bridge. (#16)
- `_detect_format()` added to `loaders/utils.py` (DD-34). (#56)

### 🐛 Bug Fixes
- `loaders/repository.py` ignored the `.i18t` extension (2 FIXMEs). (#13)
- `update_catalog()` was commented out — `.po` files were never synced
  after JSON changes. (#14)

### 🔧 Maintenance
- `aggregate_dictionaries()`: fixed wrong output filename and metadata
  key. (#15)

### 📐 Design Decisions Recorded
- DD-10/DD-11/DD-12 — `.i18t` format: extension, internal structure,
  repository layout. (#44)
- DD-13/DD-14/DD-14b — External dependencies: Babel, langcodes,
  ndict-tools. (#45)
- DD-15/DD-16 — Hub-and-spoke conversion architecture, native
  serialisation. (#46)
- DD-18/DD-19/DD-20 — `Config` Singleton, `Repository` migration, CRUD
  API. (#47)
- DD-34 — `.i18t` naming convention and format detection. (#55)

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

### 📐 Design Decisions Recorded
- DD-02/DD-03 — `messages[row][col]` matrix structure, free plurals. (#40)
- DD-05/DD-06 — Layered architecture, strict model/layer separation. (#41)
- DD-07/DD-08 — Four-level model hierarchy, `Book` as atomic persistence
  unit. (#42)

---

## Custom format (2026-03-14)

Initial exploration phase: evaluating translation file formats before
settling on the native, object-oriented `.i18t` design that the project
has used ever since.
