# STDLIB
from typing import List

# OWN
import lib_bash


def get_package_type(name_or_link: str) -> str:
    """
    :returns the package type ["pypy_package"|"git_package"|"weblink"]

    >>> assert get_package_type('pip') == 'pypy_package'
    >>> assert get_package_type('https://github.com/pypa/pip.git') == 'git_package'
    >>> assert get_package_type('git+https://github.com/pypa/pip.git') == 'git_package'
    >>> assert get_package_type('https://github.com/pypa/archive/master.zip') == 'git_package'
    >>> assert get_package_type('https://github.com/pypa/archive/master.zip') == 'weblink'
    """
    if 'https://github.com/' in name_or_link:
        return 'git_package'
    elif '/' not in name_or_link:
        return 'pypy_package'
    else:
        return 'weblink'


def get_latest_pip_command() -> lib_bash.BashCommand:
    """
    >>> assert get_latest_pip_command() is not None
    >>> assert 'pip' in get_latest_pip_command().command_string

    """
    try:
        pip_command = lib_bash.get_bash_command('pip3')
        return pip_command
    except ValueError:
        pass

    try:
        pip_command = lib_bash.get_bash_command('pip')
        return pip_command
    except ValueError:
        raise ValueError('no pip command found - please install pip')


def get_sudo_command_str() -> str:
    """
    :returns the command string for sudo, if the sudo command exists, otherwise ''
    """
    try:
        sudo_command = lib_bash.get_bash_command('sudo')
        return sudo_command.command_string
    except ValueError:
        # the sudo_command does not exist
        return ''


def get_ls_commands_prepend_sudo(ls_commands: List[str], use_sudo: bool) -> List[str]:
    """
    >>> get_ls_commands_prepend_sudo(['test','test2'], use_sudo=False)
    ['test', 'test2']
    >>> get_ls_commands_prepend_sudo(['test','test2'], use_sudo=True)
    ['/usr/bin/sudo', 'test', 'test2']

    """
    if not use_sudo:
        return ls_commands
    else:
        sudo_command_str = get_sudo_command_str()
        if sudo_command_str:
            ls_commands = [sudo_command_str] + ls_commands
            return ls_commands
        else:
            return ls_commands


def get_pypy_package_name_without_version(pypy_package: str) -> str:
    """
    >>> get_pypy_package_name_without_version('wheel==0.32.3')
    'wheel'
    >>> get_pypy_package_name_without_version('wheel>=0.32.3')
    'wheel'
    >>> get_pypy_package_name_without_version('wheel<0.32.3')
    'wheel'
    >>> get_pypy_package_name_without_version('wheel>0.32.3')
    'wheel'

    """

    pypy_package = pypy_package.split('=')[0]
    pypy_package = pypy_package.split('>')[0]
    pypy_package = pypy_package.split('<')[0]
    return pypy_package