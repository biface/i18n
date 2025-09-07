![Python](https://img.shields.io/badge/Language-python-green.svg)

--------------
# i18n-tools

**[English version](#english-reader-and-row)** (for English readers and ROW)

---

## Lecteur français et francophones

### Description
Le projet **i18n-tools** vise à simplifier et moderniser la gestion des traductions dans les applications Python. Il introduit un **nouveau format de fichiers de traduction** flexible, indépendant de toute langue dominante, et permet une conversion vers les standards **i18next** et **i18n** (fichiers `.po`/`.mo`).

L'objectif est d'offrir une solution **modulaire**, **adaptable** et **sans contrainte linguistique**, avec un support natif pour les **variantes de traduction**, les **pluriels multiples**, et une gestion transparente des langues.

---

### Objectifs par version

#### Version 1.0
- **Nouveau format de traduction** :
  - Support des **variantes** pour une même clé de traduction.
  - Gestion des **pluriels multiples** pour chaque traduction et variante.
  - Stockage des fichiers en **JSON** ou **YAML**.
  - Indépendance linguistique : aucune langue ne domine les autres.

#### Version 1.5
- **Convertibilité vers i18next** :
  - Export des traductions vers le format **i18next**.
  - Amélioration du code et optimisation des performances.
  - Support de nouveaux formats de fichiers (à définir).

#### Version 2.0
- **Intégration avec Babel** :
  - Conversion vers le format **i18n** (fichiers `.po`, `.mo`, `.pot`).
  - Utilisation des règles de pluralisation avancées de Babel.
  - Compatibilité avec les outils existants (gettext, etc.).

---

### Fonctionnalités

<custom-element data-json="%7B%22type%22%3A%22table-metadata%22%2C%22attributes%22%3A%7B%22title%22%3A%22Fonctionnalit%C3%A9s%20cl%C3%A9s%22%7D%7D" />

| Fonctionnalité                     | Version 1.0 | Version 1.5 | Version 2.0 |
|------------------------------------|------------|------------|------------|
| Format de traduction indépendant   | ✅          | ✅          | ✅          |
| Variantes et pluriels multiples    | ✅          | ✅          | ✅          |
| Support JSON/YAML                  | ✅          | ✅          | ✅          |
| Conversion vers i18next            | ❌          | ✅          | ✅          |
| Conversion vers i18n (Babel)        | ❌          | ❌          | ✅          |
| Gestion des fallbacks              | ✅          | ✅          | ✅          |


---

### Pourquoi ce projet ?
- **Flexibilité** : Un format conçu pour s’adapter à tous les besoins de traduction, sans contrainte linguistique.
- **Extensibilité** : Conversion vers les standards existants (i18next, i18n) pour une intégration facile.
- **Modernité** : Support natif des variables dynamiques (pluriels, genres, contextes).

---

### Licence
Voir le fichier [LICENSE.md](LICENSE.md).
---

### Contact
Pour toute question, ouvrez une issue ou contactez-nous à [email@example.com](mailto\:email@example.com).

---

---

## English reader and ROW

### Description
The **i18n-tools** project aims to simplify and modernize translation management in Python applications. It introduces a **new flexible translation file format**, independent of any dominant language, and enables conversion to **i18next** and **i18n** standards (`.po`/`.mo` files).

The goal is to provide a **modular**, **adaptable**, and **language-agnostic** solution, with native support for **translation variants**, **multiple plurals**, and **transparent language management**.

---

### Goals by Version

#### Version 1.0
- **New translation format**:
  - Support for **variants** for the same translation key.
  - Management of **multiple plurals** for each translation and variant.
  - File storage in **JSON** or **YAML**.
  - Language independence: no dominant language.

#### Version 1.5
- **Convertibility to i18next**:
  - Export translations to **i18next** format.
  - Code improvements and performance optimization.
  - Support for new file formats (to be defined).

#### Version 2.0
- **Integration with Babel**:
  - Conversion to **i18n** format (`.po`, `.mo`, `.pot` files).
  - Use of Babel's advanced pluralization rules.
  - Compatibility with existing tools (gettext, etc.).

---

### Features

<custom-element data-json="%7B%22type%22%3A%22table-metadata%22%2C%22attributes%22%3A%7B%22title%22%3A%22Key%20Features%22%7D%7D" />

| Feature                              | Version 1.0 | Version 1.5 | Version 2.0 |
|--------------------------------------|------------|------------|------------|
| Independent translation format       | ✅          | ✅          | ✅          |
| Variants and multiple plurals         | ✅          | ✅          | ✅          |
| JSON/YAML support                    | ✅          | ✅          | ✅          |
| Convert to i18next                   | ❌          | ✅          | ✅          |
| Convert to i18n (Babel)              | ❌          | ❌          | ✅          |
| Fallback management                   | ✅          | ✅          | ✅          |


---

### Why This Project?
- **Flexibility**: A format designed to adapt to all translation needs, without linguistic constraints.
- **Extensibility**: Conversion to existing standards (i18next, i18n) for easy integration.
- **Modernity**: Native support for dynamic variables (plurals, genders, contexts).

---

### License
See the [LICENSE.md](LICENSE.md) file.

---

### Contact
For any questions, open an issue or contact us at [email@example.com](mailto\:email@example.com).
