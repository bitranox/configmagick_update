# STDLIB
import argparse
import logging
import sys
from typing import List, Tuple

logger = logging.getLogger()


def parse_args(cmd_args: List[str] = sys.argv[1:]) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    """
    >>> import unittest
    >>> # args, parser = parse_args(cmd_args = ['-h'])  # todo help not working in tests here ???
    >>> unittest.TestCase().assertIsNotNone(parse_args, ['pip-install', 'pip'])

    """
    parser = argparse.ArgumentParser(
        description='Installs or Update Packages from Github with Version Cache to avoid unnecessary updates',
        epilog='check the documentation on https://github.com/bitranox/configmagick_update',
        prog='configmagick_update',
        add_help=True)
    parser.set_defaults(which_parser='all')

    subparsers = parser.add_subparsers()

    parser_pip_install = subparsers.add_parser('pip_install', help='installs pip packages from pypy or github')
    parser_pip_install.add_argument('package_name', metavar='package', help='the pip package name e.g. "pip"')
    parser_pip_install.add_argument('package_link', metavar='link', nargs='?', default='',
                                    help='optional the package link to github e.g. "git+https://github.com/pypa/pip.git"')
    parser_pip_install.add_argument('--use_sudo', help='use sudo for pip', action="store_true")
    parser_pip_install.set_defaults(which_parser='pip_install')

    parser_pip_update = subparsers.add_parser('pip_update', help='updates pip packages from pypy or github')
    parser_pip_update.add_argument('package_name', metavar='package', help='the pip package name e.g. "pip"')
    parser_pip_update.add_argument('package_link', metavar='link', nargs='?', default='',
                                   help='optional the package link to github e.g. "git+https://github.com/pypa/pip.git"')
    parser_pip_update.add_argument('--use_sudo', help='use sudo for pip', action="store_true")
    parser_pip_update.set_defaults(which_parser='pip_update')

    args = parser.parse_args(cmd_args)

    return args, parser
