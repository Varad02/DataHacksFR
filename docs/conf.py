import os
import sys
sys.path.insert(0, os.path.abspath(".."))

project = "Seismic Risk Atlas"
author = "DataHacks 2026"
release = "1.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

html_theme = "sphinx_rtd_theme"
autodoc_member_order = "bysource"
napoleon_google_docstyle = True
