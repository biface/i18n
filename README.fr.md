![Python](https://img.shields.io/badge/Language-python-green.svg)
![Codecov](https://img.shields.io/codecov/c/github/biface/i18n)

--------------
# i18n-tools

**[English version](README.md)** (for English readers and ROW)

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
| **v0.3.x** | Hiérarchie modèles complète — `Corpus`, `FallbackBook`, `Encyclopaedia`, exceptions             | ✅ Livré     |
| **v0.4.x** | Qualité et couverture — harmonisation des erreurs, couverture ≥ 80 %, documentation Sphinx      | 🔵 En cours |
| **v0.5.x** | Renforcement architecture — frontière DD-06, finalisation `Config → Repository`                 | 🔵 Planifié |
| **v0.6.x** | CI/CD et hygiène du dépôt — `uv`/`tox-uv`, `basedpyright`, `.codecov.yml`                        | 🔵 Planifié |
| **v0.7.x** | Couverture de tests — ≥ 80 % imposé sur tout le package                                         | 🔵 Planifié |
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
| Sauvegarde d'un `Book` vers `.i18t`         | ✅        | ✅      | ✅    | ✅    |
| Hiérarchie complète (Corpus, Encyclopaedia) | ✅        | ✅      | ✅    | ✅    |
| Gestion des replis linguistiques            | ✅        | ✅      | ✅    | ✅    |
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

Voir le fichier [licence.md](LICENCE.md).

---

### Contact

Pour toute question ou contribution, ouvrez une [issue GitHub](https://github.com/biface/i18n/issues).
