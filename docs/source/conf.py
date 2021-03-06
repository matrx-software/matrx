# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import sphinx_rtd_theme


sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("../.."))


# -- Project information -----------------------------------------------------
# The full version, including alpha/beta/rc tags
release = '2.0'

project = 'MATRX %s Manual' % release
copyright = '2020, The MATRX Team at matrx-software.com'
author = 'The MATRX Team at matrx-software.com'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autosummary',
    # 'sphinx.ext.autodoc',
    'autoapi.extension',
    'sphinx.ext.coverage',
    'numpydoc',
    'sphinx_rtd_theme',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.todo',
    'recommonmark'
]

# autoapi automatically creates files with documentation
# See: https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html
autoapi_dirs = ['../..']
autoapi_type = 'python'
autoapi_options = ['members', 'inherited-members', 'show-inheritance']
autoapi_add_toctree_entry = False
autoapi_python_class_content = "class"
autoclass_content = 'both'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

master_doc = 'index'

autodoc_member_order = 'bysource'

autosummary_generate = True
autosummary_imported_members = False

html_theme_options = {
    'prev_next_buttons_location': 'bottom',
    # Toc options
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': True,
}

html_logo = '_static/images/matrx_logo_light.svg'

# -- Options for HTML output -------------------------------------------------
# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# By default, highlight as Python 3.
highlight_language = 'python3'

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static', '../build/html/_static']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
def setup(app):
    app.add_stylesheet("css/theme_overrides.css")


# numpydoc_xref_aliases