"""This module validates Vizir files"""


import os
import yaml

from .constants import POLICIES
from .util import header, Step
from .yava.validator import validate as _validate


def validate(directory="."):
    # pylint: disable=W0703
    """
    Validate a Vizir file in the given directory
    :param directory: The directory to consider
    """
    header('Vizir Validator')
    with Step('Checking the .docs.yml file', single_line=False):
        with open(os.path.join(directory, '.docs.yml'), 'r', encoding='utf8') as file:
            conf = yaml.safe_load(file)
        _validate(conf, POLICIES)
