# -*- coding: utf-8 -*-
{{ imports }}

source_suffix = '.rst'
master_doc = 'index'
project = {{ project }}
copyright = {{ copyright }}
author = {{ authors }}
version = {{ version }}
release = {{ release }}
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = "sphinx_rtd_theme"
locale_dirs = ['locale/']

{{ vars }}
{{ expr_lists }}
{{ lists }}
