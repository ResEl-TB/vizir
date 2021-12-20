# pylint: disable=W0603
"""This module provides text printers"""


import sys

from termcolor import colored as _colored


def colored(string, color, on=None, reverse=False):
    """Color a string"""
    args = [string, color]
    if on is not None:
        args.append(f'on_{on}')
    return _colored(*args, attrs=['reverse'] if reverse else [])

def mag(string, on=None, reverse=False):
    """Put a string in magenta"""
    return colored(string, 'magenta', on, reverse)

def blue(string, on=None, reverse=False):
    """Put a string in blue"""
    return colored(string, 'blue', on, reverse)

def cyan(string, on=None, reverse=False):
    """Put a string in cyan"""
    return colored(string, 'cyan', on, reverse)

def grey(string, on=None, reverse=False):
    """Put a string in grey"""
    return colored(string, 'grey', on, reverse)


LEVEL=0
COLORS = (blue, cyan, grey)


def _print(string=''):
    """Print a string with the right level"""
    line = ''
    for i in range(LEVEL-1):
        line += COLORS[i](' ', reverse=True)
        #line += ' '
        line += COLORS[i+1](' ', reverse=True)
    if LEVEL > 0:
        line += COLORS[LEVEL-1](' ', reverse=True)
    print(line + string)


def color_join(string, elements, color):
    """Join strings after coloring them"""
    return string.join(color(element) for element in elements)


def err(string=''):
    """Print an error"""
    _print(f'{colored(" ERROR ", "red", reverse=True)} {string}')
    sys.exit(1)

def warn(string=''):
    """Print a warning"""
    _print(f'{colored("WARNING", "yellow", reverse=True)} {string}')

def ok(string=''):
    """Print an Ok message"""
    _print(f'{colored("  OK   ", "green", reverse=True)} {string}')

def info(string=''):
    """Print an info message"""
    _print(f'{colored(" INFO  ", "magenta", reverse=True)} {string}')


def _bc(color, on=None):
    """Format a breadcrumb joiner"""
    return color(' ', reverse=True) + color('', on=on)


def header(string):
    """Print a header"""
    global LEVEL
    LEVEL = 0
    _print(f'{blue(f" {string}", reverse=True)}{_bc(blue)}')


class Section:
    """
    This class represents a section
    :param string: The section name
    """
    def __init__(self, string):
        line = ''
        for i in range(LEVEL+1):
            line += _bc(COLORS[i], COLORS[i+1].__name__)
        line += COLORS[i+1](f" {string}", reverse=True) + _bc(COLORS[i+1])
        self.line = line

    def __enter__(self):
        """Print the string and increase the level"""
        global LEVEL
        _print()
        print(self.line)
        LEVEL += 1
        return self

    def __exit__(self, e_ty, e_val, e_trace):
        """Decrease the level"""
        global LEVEL
        LEVEL -=1
        _print()


class Step:
    """
    This class represents a processing step
    :param string: The string describing the step
    :param success: The string displayed upon successful completion of the task
    :param autodetect: If False, disable verb detection; if 'en', check if the first word ends with
                       'ing' and conjugate it in the past for the success text if not set
    :param single_line: Whether the step is supposed not to print anything other than its status
    """
    def __init__(self, string, success='', autodetect='en', single_line=True):
        self.string = string
        if success:
            self.success = success
        elif autodetect == 'en':
            sentence = string.split(maxsplit=1)
            first_word = sentence[0]
            if first_word.endswith('ing'):
                if first_word.lower() in ['building']:
                    sentence[0] = f'{first_word[:-4]}t'
                elif first_word[-4] == 'y':
                    if first_word[-5] in ['a', 'e', 'i', 'o', 'u', 'y']:
                        sentence[0] = f'{first_word[:-3]}ied'
                    else:
                        sentence[0] = f'{first_word[:-4]}ied'
                else:
                    sentence[0] = f'{first_word[:-3]}ed'
                self.success = ' '.join(sentence) + ' ' * (len(first_word) - len(sentence[0]))
        self.single_line = success == '' if single_line is None else single_line

    def __enter__(self):
        """Print the string"""
        info(self.string)
        return self

    def __exit__(self, e_ty, e_val, e_trace):
        """If an exception is raised, display an error message, else display an ok message"""
        if e_ty == SystemExit:
            raise
        if e_ty is not None:
            if e_ty == BaseException:
                err(e_val)
            err(f'Exception {mag(e_ty.__name__)} raised: {e_val}')
        if self.single_line:
            print('\033[F', end='')
        ok(self.success)
