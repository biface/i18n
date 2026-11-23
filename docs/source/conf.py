# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import shutil
import sys
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pyi18t-tools'
copyright = '2025-2026, biface'
author = 'biface'
release = '0.11.0rc1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.append(os.path.abspath('../../src'))

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    # contributions
    'sphinxcontrib.mermaid',
]

templates_path = ['_templates']
exclude_patterns = []

# A cross-reference that resolves to nothing is a warning, so it fails the
# build (-W).
nitpicky = True
# email-validator publishes no Sphinx inventory.
nitpick_ignore = [
    ('py:exc', 'email_validator.EmailNotValidError'),
]

# A page not yet written is a skeleton with a todo: todos are never rendered.
todo_include_todos = False

# The API pages list their members by hand, in the order of the page.
autodoc_typehints = 'signature'
autodoc_member_order = 'bysource'
# Catalog is imported for type checking only (babel.messages stays a local
# import): name its class so the signatures that use it can be evaluated.
autodoc_type_aliases = {
    'Catalog': 'babel.messages.catalog.Catalog',
}

# -- Intersphinx -------------------------------------------------------------
# Each inventory has a copy in _inventories/, read when the site cannot be
# reached: a site that is down, or sphinx-build run without network in an
# environment already built, then gives no warning. Refresh a copy from
# the site with:
#   curl -sSfL <url>/objects.inv -o docs/source/_inventories/<name>.inv

intersphinx_mapping = {
    'python': (
        'https://docs.python.org/3',
        (None, '_inventories/python.inv'),
    ),
    'babel': (
        'https://babel.pocoo.org/en/latest',
        (None, '_inventories/babel.inv'),
    ),
    'ndict-tools': (
        'https://ndict-tools.readthedocs.io/en/latest',
        (None, '_inventories/ndict-tools.inv'),
    ),
}
intersphinx_timeout = 10



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'

html_use_index = True
html_search_language = 'en'
html_static_path = ['_static']
html_logo = "_static/images/logo.svg"
html_favicon = "_static/images/logo.svg"

# -- JSON Schemas ------------------------------------------------------------
# The schemas shipped in the package are published under <html>/schemas/, the
# address their "$id" gives. html_extra_path would copy them to the root.

SCHEMAS = Path(__file__).resolve().parents[2] / 'src' / 'i18n_tools' / 'schemas'


def _publish_schemas(app, exception):
    if exception is None and app.builder.format == 'html':
        shutil.copytree(SCHEMAS, Path(app.outdir) / 'schemas', dirs_exist_ok=True)


def setup(app):
    app.connect('build-finished', _publish_schemas)
