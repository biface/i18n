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
copyright = '2025, biface'
author = 'biface'
release = '0.10.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../..'))
sys.path.append(os.path.abspath('../../src'))

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    # contributions
    'sphinxcontrib.mermaid',
]

templates_path = ['_templates']
exclude_patterns = []



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
