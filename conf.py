# -*- coding: utf-8 -*-
{{ imports }}
import sys

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

search_paths = []

{{ vars }}
{{ expr_lists }}
{{ lists }}

sys.path = search_paths + sys.path
