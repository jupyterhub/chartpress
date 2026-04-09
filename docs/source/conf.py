# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime

import chartpress

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Chartpress"
author = "Project Jupyter Contributors"
copyright = f"{datetime.date.today().year}, {author}"
release = "2.3.1.dev"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_copybutton",
    "jupyterhub_sphinx_theme",
    "myst_parser",
]
root_doc = "index"
source_suffix = [".md"]
# default_role let's use use `foo` instead of ``foo`` in rST
default_role = "literal"

templates_path = ["_templates"]
exclude_patterns = []


# -- MyST configuration ------------------------------------------------------
# ref: https://myst-parser.readthedocs.io/en/latest/configuration.html
#
myst_heading_anchors = 2

myst_enable_extensions = [
    # available extensions: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
    "attrs_inline",
    "colon_fence",
    "deflist",
    "fieldlist",
    "substitution",
]

myst_substitutions = {
    # date example: Dev 07, 2022
    "date": datetime.date.today().strftime("%b %d, %Y").title(),
    "python_min": "3.7",
    "version": chartpress.__version__,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_logo = "_static/images/logo/logo.png"
# html_favicon = "_static/images/logo/favicon.ico"
html_static_path = ["_static"]

html_theme = "jupyterhub_sphinx_theme"
html_theme_options = {
    "header_links_before_dropdown": 6,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/jupyterhub/chartpress",
            "icon": "fa-brands fa-github",
        },
    ],
    "use_edit_page_button": True,
    "navbar_align": "left",
}
html_context = {
    "github_user": "jupyterhub",
    "github_repo": "chartpress",
    "github_version": "main",
    "doc_path": "docs/source",
}
