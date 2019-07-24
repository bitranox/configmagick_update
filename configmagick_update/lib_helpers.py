# STDLIB
import json
import logging
from typing import List

# OWN
from configmagick_bash import lib_bash
import lib_regexp
import lib_shell

# PROJ
from config import Config


logger = logging.getLogger()


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


def get_git_repository_slug_from_link(git_link: str) -> str:
    """
    >>> import unittest
    >>> assert get_git_repository_slug_from_link('https://github.com/pypa/pip.git') == 'pypa/pip'
    >>> assert get_git_repository_slug_from_link('git+https://github.com/pypa/pip.git') == 'pypa/pip'
    >>> assert get_git_repository_slug_from_link('https://github.com/pypa/pip/archive/master.zip') == 'pypa/pip'
    >>> unittest.TestCase().assertRaises(ValueError, get_git_repository_slug_from_link, 'https://some_unknown_link/master.zip')
    >>> unittest.TestCase().assertRaises(ValueError, get_git_repository_slug_from_link, 'git+https:/github.com/pypa/pip.git')

    """

    # https://github.com/pypa/pip.git | git+https://github.com/pypa/pip.git | https://github.com/pypa/pip/archive/master.zip
    git_repository_slug = ''
    try:
        git_repository_slug = git_link.split('https://github.com/')[1]   # pypa/pip.git | pypa/pip.git | pypa/archive/master.zip
        git_repository_slug = git_repository_slug.rsplit('.', 1)[0]                 # pypa/pip | pypa/pip | pypa/archive/master
        git_repository_slug = '/'.join(git_repository_slug.split('/')[:2])         # bitranox/lib_path | bitranox/lib_doctest_pycharm
        elements = git_repository_slug.split('/')

        if len(elements) != 2 or len(elements[0]) == 0 or len(elements[1]) == 0:
            error = 'can not get the repository slug "{git_repository_slug}" from link "{git_link}" - wrong link ?'\
                .format(git_repository_slug=git_repository_slug, git_link=git_link)

            lib_bash.banner(logging.ERROR, error)
            raise ValueError(error)

        if '.zip' in git_link.lower():
            sanitized_git_link = get_sanitized_git_link(git_repository_slug=git_repository_slug)
            warning = 'better use "{sanitized_git_link}" than "{git_link} unless You need it for a reason"'\
                .format(sanitized_git_link=sanitized_git_link, git_link=git_link)
            lib_bash.banner(logging.WARNING, warning)

        return git_repository_slug
    except Exception:
        error = 'can not get the repository slug "{git_repository_slug}" from link "{git_link}" - wrong link ?'\
                        .format(git_repository_slug=git_repository_slug, git_link=git_link)

        lib_bash.banner(logging.ERROR, error)
        raise ValueError(error)


def get_git_remote_hash(git_repository_slug: str) -> str:
    """
    >>> # https://github.com/pypa/pip.git | git+https://github.com/pypa/pip.git | https://github.com/pypa/archive/master.zip

    >>> git_repository_slug = get_git_repository_slug_from_link(git_link='https://github.com/pypa/pip.git')
    >>> assert len(get_git_remote_hash(git_repository_slug=git_repository_slug)) == len('59e6ce2847bda24b3f29683251d10ae5c3cab357')
    >>> git_repository_slug = get_git_repository_slug_from_link(git_link='git+https://github.com/pypa/pip.git')
    >>> assert len(get_git_remote_hash(git_repository_slug=git_repository_slug)) == len('59e6ce2847bda24b3f29683251d10ae5c3cab357')
    >>> git_repository_slug = get_git_repository_slug_from_link(git_link='https://github.com/pypa/pip/archive/master.zip')
    >>> assert len(get_git_remote_hash(git_repository_slug=git_repository_slug)) == len('59e6ce2847bda24b3f29683251d10ae5c3cab357')

    """
    url = 'https://github.com/{git_repository_slug}.git'.format(git_repository_slug=git_repository_slug)
    git_command = lib_bash.get_bash_command('git')
    result = lib_shell.run_shell_ls_command([git_command.command_string, '--no-pager', 'ls-remote', '--quiet', url])
    line = lib_regexp.reg_grep('HEAD', result.stdout)[0].expandtabs()
    git_remote_hash = line.split()[0]
    return git_remote_hash


def get_git_local_hash_from_directory(path_install_directory: str) -> str:
    # bash: git_local_hash=$(cat /usr/local/lib_bash/.git/refs/heads/master)
    logger.warning('STUB get_git_local_hash_from_directory')
    return ''


def get_git_local_hash_from_database_or_blank(key: str) -> str:
    """
    >>> save_path_version_file = Config.path_version_file
    >>> Config.path_version_file = Config.path_version_files_dir / 'test_database'
    >>> if Config.path_version_file.exists(): Config.path_version_file.unlink()
    >>> data_dict=dict()
    >>> save_git_hash_to_database('a','A')
    >>> save_git_hash_to_database('b','B')
    >>> get_git_local_hash_from_database_or_blank('a')
    >>> get_git_local_hash_from_database_or_blank('b')
    >>> get_git_local_hash_from_database_or_blank('c')
    >>> # Config.path_version_file.unlink()
    >>> Config.path_version_file = save_path_version_file

    """

    if not Config.path_version_file.exists():
        return ''

    with open(str(Config.path_version_file), 'r') as f:
        local_git_hash_hashed_by_key = json.load(f)

    local_hash_from_database = local_git_hash_hashed_by_key.get(key, '')    # '' if not found
    return local_hash_from_database


def save_git_hash_to_database(key: str, git_hash: str) -> bool:

    if Config.path_version_file.exists():
        with open(str(Config.path_version_file), 'r') as f:
            local_git_hash_hashed_by_key = json.load(f)
    else:
        local_git_hash_hashed_by_key = dict()

    local_git_hash_hashed_by_key[key] = git_hash
    with open(str(Config.path_version_file), 'w') as f:
        json.dump(local_git_hash_hashed_by_key, f)
    # lib_bash.fix_ownership(user=,fileobject=)  # TODO
    # lib_bash.fix_permissions(user=, fileobject=, recursive=True) # TODO
    return True


def get_sanitized_git_link(git_repository_slug: str) -> str:
    """
    >>> assert get_sanitized_git_link(git_repository_slug='pypa/pip') == 'git+https://github.com/pypa/pip.git'
    """

    sanitized_git_link = 'git+https://github.com/{git_repository_slug}.git'.format(git_repository_slug=git_repository_slug)
    return sanitized_git_link
