![Python](https://img.shields.io/badge/Language-python-green.svg)
![Codecov](https://img.shields.io/codecov/c/github/biface/i18n)

--------------
# i18n-tools

**[English version](#english-reader-and-row)** (for English readers and ROW)

---

## Lecteur français et francophones

### Description

Le projet **i18n-tools** vise à simplifier et moderniser la gestion des traductions dans les applications Python. Il introduit un **nouveau format de fichiers de traduction** flexible, indépendant de toute langue dominante, et conçu pour coexister avec les standards existants comme **gettext** (fichiers `.po`/`.mo`) et **i18next**.

L'objectif est d'offrir une solution **modulaire**, **adaptable** et **sans contrainte linguistique**, avec un support natif pour les **variantes de traduction**, les **pluriels multiples**, et une gestion transparente des langues et des replis.

---

### Roadmap

Le projet suit une progression par valeur livrée. Chaque version est indépendamment utilisable.

| Jalon      | Description                                                                                     | État        |
|------------|-------------------------------------------------------------------------------------------------|-------------|
| **v0.1.x** | Stabilisation — corrections des bugs bloquants (B-01 à B-05)                                    | ✅ Livré     |
| **v0.2.x** | Pont loaders ↔ modèles — `Book.load()`, extension `.i18t`, pont `Config → Repository` (partiel) | ✅ Livré     |
| **v0.3.x** | Hiérarchie modèles complète — `Corpus`, `FallbackBook`, `Encyclopaedia`, exceptions             | 🔵 Planifié |
| **v0.4.x** | Qualité et couverture — harmonisation des erreurs, couverture ≥ 80 %, documentation Sphinx      | 🔵 Planifié |
| **v1.0.0** | i18n-tools natif complet — `core.py`, `fallback.py`, `formatter.py`, CLI, format `.i18t` gelé   | 🔵 Planifié |
| **v1.x**   | Interopérabilité gettext — import/export `.po`/`.mo` via Babel                                  | 🔵 Horizon  |
| **v2.x**   | Formats tiers — i18next et autres, hub de conversion central                                    | 🔵 Horizon  |
| **v3.x**   | CLI complet, API stable, ports Rust/JavaScript                                                  | 🔵 Horizon  |

---

### Fonctionnalités

| Fonctionnalité                              | v0.2.x    | v1.0.0 | v1.x | v2.x |
|---------------------------------------------|-----------|--------|------|------|
| Format `.i18t` natif (JSON/YAML)            | ✅         | ✅      | ✅    | ✅    |
| Identifiants indépendants de la langue      | ✅         | ✅      | ✅    | ✅    |
| Variantes et pluriels multiples             | ✅         | ✅      | ✅    | ✅    |
| Chargement d'un `Book` depuis `.i18t`       | ✅         | ✅      | ✅    | ✅    |
| Sauvegarde d'un `Book` vers `.i18t`         | 🔵 v0.3.x | ✅      | ✅    | ✅    |
| Hiérarchie complète (Corpus, Encyclopaedia) | 🔵 v0.3.x | ✅      | ✅    | ✅    |
| Gestion des replis linguistiques            | 🔵 v0.3.x | ✅      | ✅    | ✅    |
| Interpolation et règles de pluriel actives  | ❌         | ✅      | ✅    | ✅    |
| Interface CLI/REPL                          | ❌         | ✅      | ✅    | ✅    |
| Import/export `.po`/`.mo` (Babel/gettext)   | ❌         | ❌      | ✅    | ✅    |
| Conversion vers i18next                     | ❌         | ❌      | ❌    | ✅    |

---

### Pourquoi ce projet ?

- **Flexibilité** : un format conçu pour s'adapter à tous les besoins de traduction, sans contrainte linguistique — aucune langue n'est dominante.
- **Expressivité** : support natif des variantes contextuelles (genre, registre, contexte) et des pluriels métier au-delà des règles CLDR.
- **Extensibilité** : architecture en couches permettant une conversion vers les standards existants (gettext, i18next) sans modifier les modèles.
- **Interopérabilité** : pont avec l'écosystème Babel pour une compatibilité progressive avec les outils existants.

---

### Licence

Voir le fichier [LICENSE.md](LICENSE.md).

---

### Contact

Pour toute question ou contribution, ouvrez une [issue GitHub](https://github.com/biface/i18n/issues).

---

---

## English reader and ROW

### Description

The **i18n-tools** project aims to simplify and modernize translation management in Python applications. It introduces a **new flexible translation file format**, independent of any dominant language, designed to coexist with existing standards such as **gettext** (`.po`/`.mo` files) and **i18next**.

The goal is to provide a **modular**, **adaptable**, and **language-agnostic** solution, with native support for **translation variants**, **multiple plurals**, and transparent language fallback management.

---

### Roadmap

The project follows a progression by deliverable value. Each version is independently usable.

| Milestone  | Description                                                                                   | Status      |
|------------|-----------------------------------------------------------------------------------------------|-------------|
| **v0.1.x** | Stabilisation — fix blocking bugs (B-01 to B-05)                                              | ✅ Delivered |
| **v0.2.x** | Loaders ↔ models bridge — `Book.load()`, `.i18t` extension, partial `Config → Repository`     | ✅ Delivered |
| **v0.3.x** | Complete model hierarchy — `Corpus`, `FallbackBook`, `Encyclopaedia`, exceptions              | 🔵 Planned  |
| **v0.4.x** | Quality and coverage — error handling, ≥ 80% coverage, Sphinx documentation                   | 🔵 Planned  |
| **v1.0.0** | Full native i18n-tools — `core.py`, `fallback.py`, `formatter.py`, CLI, `.i18t` format frozen | 🔵 Planned  |
| **v1.x**   | gettext interoperability — `.po`/`.mo` import/export via Babel                                | 🔵 Horizon  |
| **v2.x**   | Third-party formats — i18next and others, central conversion hub                              | 🔵 Horizon  |
| **v3.x**   | Complete CLI, stable API, Rust/JavaScript ports                                               | 🔵 Horizon  |

---

### Features

| Feature                                     | v0.2.x    | v1.0.0 | v1.x | v2.x |
|---------------------------------------------|-----------|--------|------|------|
| Native `.i18t` format (JSON/YAML)           | ✅         | ✅      | ✅    | ✅    |
| Language-neutral identifiers                | ✅         | ✅      | ✅    | ✅    |
| Variants and multiple plurals               | ✅         | ✅      | ✅    | ✅    |
| Load a `Book` from `.i18t`                  | ✅         | ✅      | ✅    | ✅    |
| Save a `Book` to `.i18t`                    | 🔵 v0.3.x | ✅      | ✅    | ✅    |
| Complete hierarchy (Corpus, Encyclopaedia)  | 🔵 v0.3.x | ✅      | ✅    | ✅    |
| Language fallback management                | 🔵 v0.3.x | ✅      | ✅    | ✅    |
| Interpolation and active plural rules       | ❌         | ✅      | ✅    | ✅    |
| CLI/REPL interface                          | ❌         | ✅      | ✅    | ✅    |
| `.po`/`.mo` import/export (Babel/gettext)   | ❌         | ❌      | ✅    | ✅    |
| i18next conversion                          | ❌         | ❌      | ❌    | ✅    |

---

### Why This Project?

- **Flexibility**: a format designed to adapt to all translation needs, without linguistic constraints — no language is dominant.
- **Expressiveness**: native support for contextual variants (gender, register, context) and business plurals beyond CLDR rules.
- **Extensibility**: layered architecture enabling conversion to existing standards (gettext, i18next) without modifying the models.
- **Interoperability**: bridge with the Babel ecosystem for progressive compatibility with existing tools.

---

### License

See the [LICENSE.md](LICENSE.md) file.

---

### Contact

For any questions or contributions, open a [GitHub issue](https://github.com/biface/i18n/issues).
