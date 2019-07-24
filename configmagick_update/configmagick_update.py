# STDLIB
import errno
import json
import logging
import pathlib
import subprocess
import sys
from typing import List

# EXT
import psutil   # type: ignore
import requests

# OWN
from configmagick_bash import lib_bash
import lib_log_utils
import lib_regexp
import lib_shell

# PROJ
from config import Config
import lib_helpers


logger = logging.getLogger()
lib_bash.install_color_log()
Config.path_version_files_dir.mkdir(mode=0o775, parents=True, exist_ok=True)


def pip_update(name_or_link: str, use_sudo: bool) -> bool:  # returns updated or not
    """
    Updates (or installs) pip packages also from git links, only if there is a new master, by storing and checking the git hashes

    name_or_link: name of the pip package or link to github
    sudo : pip install as root

    Returns updated - True if the Package was Updated, or False when it was not updated


    >>> pip_update('pip', use_sudo=False)
    >>> pip_update('pip', use_sudo=False)


    """

    package_type = lib_helpers.get_package_type(name_or_link)
    if package_type == 'pypy_package':
        updated = pip_update_from_pypy(pypy_package=name_or_link, use_sudo=use_sudo)
        return updated
    elif package_type == 'git_package':
        if not is_pip_git_package_up_to_date(git_link=name_or_link):
            pip_update_from_git(git_link=name_or_link)
            return True
    elif package_type == 'weblink':
        pip_update_from_weblink(weblink=name_or_link)
        return True
    else:
        return False


# depricated
def is_pip_pypy_package_up_to_date(pypy_package: str, use_sudo: bool) -> bool:

    pip_command = lib_helpers.get_latest_pip_command().command_string
    ls_commands = lib_helpers.get_ls_commands_prepend_sudo([pip_command, 'list', '-o'], use_sudo=use_sudo)
    shell_response = lib_shell.run_shell_ls_command(ls_commands)
    result_lines = lib_regexp.reg_grep(pypy_package, shell_response.stdout)
    if not result_lines:
        return False
    # there can be more grep matches - for instance package distro, distro-info
    # would create two result lines
    for line in result_lines:
        package, version, latest, package_type = line.split()
        if package == pypy_package:
            if version != latest:
                return False
            else:
                return True

def is_pip_git_package_up_to_date(git_link: str) -> bool:

    return None


def pip_update_from_pypy(pypy_package: str, use_sudo: bool, show_output: bool = True) -> bool:
    """
    :returns updated - True if updated, False if it was already up to date


    >>> assert pip_update_from_pypy('urllib3==1.24.1', use_sudo=True, show_output=False) is not None    # first Update to old Version
    >>> assert pip_update_from_pypy('urllib3', use_sudo=True, show_output=False) == True                # second Update to new Version
    >>> assert pip_update_from_pypy('urllib3', use_sudo=True, show_output=False) == False               # third Update - is already up to date

    """
    try:
        pip_command = lib_helpers.get_latest_pip_command().command_string
        ls_commands = lib_helpers.get_ls_commands_prepend_sudo([pip_command, "install", "--upgrade", pypy_package], use_sudo=use_sudo)
        shell_response = lib_shell.run_shell_ls_command(ls_commands, pass_std_out_line_by_line=show_output)
        if "Requirement already up-to-date: {pypy_package}".format(pypy_package=pypy_package) in shell_response.stdout:
            return False
        else:
            return True
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 13:   # pip permission error
            raise PermissionError(exc.stderr)
        else:
            error = 'Package "{pypy_package}" can not be installed via pip:\n\n{stderr}'.format(pypy_package=pypy_package, stderr=exc.stderr)
            lib_bash.banner(logging.ERROR, error)
            raise ValueError(error)


def pip_update_from_weblink(weblink: str, show_output: bool = True) -> bool:
    """
    >>> import unittest
    >>> assert pip_update_from_weblink('pip', show_output=False) == True
    >>> unittest.TestCase().assertRaises(ValueError, pip_update_from_weblink, 'https://some_unknown_link/package.zip', show_output=False)
    """
    return pip_update_from_pypy(pypy_package=weblink, show_output=show_output)


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
    >>> git_repository_slug = get_git_repository_slug_from_link(git_link='https://github.com/pypa/archive/master.zip')
    >>> assert len(get_git_remote_hash(git_repository_slug=git_repository_slug)) == len('59e6ce2847bda24b3f29683251d10ae5c3cab357')


    """
    url = 'https://github.com/{git_repository_slug}.git'.format(git_repository_slug=git_repository_slug)
    git_command = lib_bash.get_bash_command('git')
    result = lib_shell.run_shell_ls_command([git_command.command_string, '--no-pager', 'ls-remote', '--quiet'])
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


def pip_update_from_git(git_link: str) -> bool:
    git_repository_slug = get_git_repository_slug_from_link(git_link=git_link)
    git_remote_hash = get_git_remote_hash(git_repository_slug=git_repository_slug)
    git_local_hash = get_git_local_hash_from_database_or_blank(key=git_link)
    if git_remote_hash != git_local_hash:
        pip_update_from_pypy(pypy_package=git_link)
    save_git_hash_to_database(key=git_link, git_hash=git_remote_hash)
    return True




def main(sys_argv: List[str] = sys.argv[1:]) -> None:
    """
    >>> main()

    :return:
    """

    lib_log_utils.setup_console_logger()

    # noinspection PyBroadException
    try:
        lib_bash.banner(logging.INFO, 'configmagick_update')
        result = subprocess.call(["sudo", "ls"])

    except FileNotFoundError:
        # see https://www.thegeekstuff.com/2010/10/linux-error-codes for error codes
        # No such file or directory
        sys.exit(errno.ENOENT)      # pragma: no cover
    except FileExistsError:
        # File exists
        sys.exit(errno.EEXIST)      # pragma: no cover
    except TypeError:
        # Invalid Argument
        sys.exit(errno.EINVAL)      # pragma: no cover
        # Invalid Argument
    except ValueError:
        sys.exit(errno.EINVAL)      # pragma: no cover
    except Exception:
        sys.exit(1)                 # pragma: no cover


if __name__ == '__main__':
    main()                          # pragma: no cover
