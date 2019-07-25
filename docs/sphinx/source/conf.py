# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

<<<<<<< HEAD
# sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("../../.."))
sys.path.insert(0, os.path.abspath("../../../matrxs"))
print("\n\n -- System Path -->")
=======
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath("../../../"))
sys.path.insert(0, os.path.abspath("../../../world_builder/"))
sys.path.insert(0, os.path.abspath("../../../environment/"))
sys.path.insert(0, os.path.abspath("../../../environment/actions/"))
sys.path.insert(0, os.path.abspath("../../../environment/objects/"))
sys.path.insert(0, os.path.abspath("../../../environment/sim_goals/"))
# sys.path.insert(0, os.path.abspath("../../../agents/"))
# sys.path.insert(0, os.path.abspath("../../../agents/capabilities/"))
# sys.path.insert(0, os.path.abspath("../../../agents/utils/"))
print("\n\n\n -- System Path --> \n")
>>>>>>> parent of a52b42d... Documentation update
for p in sys.path:
    print(f"{p}")
print("\n\n")


# -- Project information -----------------------------------------------------

# Project's name
project = 'MATRXS'

# Copyright
copyright = "2019, Jasper van der Waa, Tjalling Haije, Ioana Cocu"

# The author names of the document
author = 'Jasper van der Waa, Tjalling Haije, Ioana Cocu'

# Major project version
version = '0.1'

# The full version, including alpha/beta/rc tags
release = '0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'numpydoc',
    'sphinx_rtd_theme'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Auto generate the TOC elements for when using this autodoc flag (e.g. 'members')
autodoc_default_options = {
    'members': True,
    'member-order': 'alphabetical',
    'special-members': '__init__',
    'undoc-members': True
}
autosummary_generate = True

# Suppress certain warnings
suppress_warnings = []

# If the author names should be shown for codeautho and sectionauthor
show_authors = False

# If module names are appended
add_module_names = False

# If copyright at bottom is shown
html_show_copyright = False

# If created by Sphinx is shown at bottom
html_show_sphinx = False


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
