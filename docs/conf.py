import guzzle_sphinx_theme

project = "sqlalchemy-better-aurora-data-api"
copyright = "Andrey Kislyuk and CZI"
author = "Andrey Kislyuk and juanjodevio"
version = ""
release = ""
language = None
master_doc = "index"
extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.viewcode"]
source_suffix = [".rst", ".md"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
html_theme_path = guzzle_sphinx_theme.html_theme_path()
html_theme = "guzzle_sphinx_theme"
html_theme_options = {
    "project_nav_name": project,
    "projectlink": "https://github.com/juanjodevio/sqlalchemy-better-aurora-data-api",
}
html_sidebars = {
    "**": [
        "logo-text.html",
        # "globaltoc.html",
        "localtoc.html",
        "searchbox.html",
    ]
}
