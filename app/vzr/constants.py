"""This module provides the constants for Vizir"""


from .yava.primitives import is_str, is_str_or_number


FILES_POLICY = {'_error':   {'@'},
                '_warning': {'plus', 'to'},
                'minus':    [is_str],
                'plus':     [is_str],
                'to':       is_str
               }

POLICIES = {'*': {'_error':    {'@', 'repo', 'version'},
                  '_warning':  {'copyright', 'release'},
                  'code':      {'*': {'_error':    {'@'},
                                      '_warning':  {'templates'},
                                      'files':     [FILES_POLICY],
                                      'from':      is_str,
                                      'templates': [is_str]
                                     }
                               },
                  'copyright': is_str,
                  'docs':      {'_error': {'@'},
                                'files':  [FILES_POLICY],
                                'from': is_str
                               },
                  'locales':   [is_str],
                  'release':   is_str_or_number,
                  'repo':      is_str,
                  'version':   is_str_or_number
                 }
           }

ENDPOINT = 'git.resel.fr'
REMOTE = f'ssh://{ENDPOINT}:43000/{{}}'
PRIVATE_TOKEN = 'glpat-sp9wNGeB619c4CdycGPv'
