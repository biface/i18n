# Changelog

All notable changes to this project are documented in this file.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Sections per [CONVENTIONS.md](CONVENTIONS.md) §7 (Releases).

Issue/PR references use the GitHub issue number from `biface/i18n`.

---

## [Unreleased] — v0.4.x — Quality, coverage & documentation

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
