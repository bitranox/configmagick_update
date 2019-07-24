# STDLIB
import logging
import subprocess

# OWN
from configmagick_bash import lib_bash
import lib_shell

# PROJ
try:
    from . import lib_helpers
except ImportError:                 # for local development
    import lib_helpers              # type: ignore # pragma: no cover


def pip_install(package_name: str, package_link: str, use_sudo: bool) -> bool:  # returns updated or not
    return pip_update(package_name=package_name, package_link=package_link, use_sudo=use_sudo)


def pip_update(package_name: str, package_link: str, use_sudo: bool) -> bool:  # returns updated or not
    """
    Updates (or installs) pip packages also from git links, only if there is a new master, by storing and checking the git hashes

    name_or_link: name of the pip package or link to github
    sudo : pip install as root

    Returns updated - True if the Package was Updated, or False when it was not updated


    """

    updated = False
    package_type = lib_helpers.get_package_type(package_link)
    if package_type == 'pypy_package':
        updated = pip_update_from_pypy(package_name_or_link=package_name, use_sudo=use_sudo)
    elif package_type == 'git_package':
        if not is_pip_git_package_up_to_date(package_name=package_name, package_link=package_link):
            updated = pip_update_from_git(package_link=package_link, use_sudo=use_sudo)     # returns always true, but we do it only when update is needed
    elif package_type == 'weblink':
        pip_update_from_weblink(package_link=package_link, use_sudo=use_sudo)
        updated = True
    else:
        updated = False

    return updated


def pip_update_from_pypy(package_name_or_link: str, use_sudo: bool, show_output: bool = True) -> bool:
    """
    :returns updated - True if updated, False if it was already up to date


    >>> assert pip_update_from_pypy('urllib3==1.24.1', use_sudo=True, show_output=False) is not None    # first Update to old Version
    >>> assert pip_update_from_pypy('urllib3', use_sudo=True, show_output=False) == True                # second Update to new Version
    >>> assert pip_update_from_pypy('urllib3', use_sudo=True, show_output=False) == False               # third Update - is already up to date
    >>> assert pip_update_from_pypy('chardet', use_sudo=True, show_output=False) is not None            # third Update - is already up to date

    """
    try:
        pip_command = lib_helpers.get_latest_pip_command().command_string
        ls_commands = lib_helpers.get_ls_commands_prepend_sudo([pip_command, "install", "--upgrade", package_name_or_link], use_sudo=use_sudo)
        shell_response = lib_shell.run_shell_ls_command(ls_commands, pass_std_out_line_by_line=show_output)
        if "Requirement already up-to-date: {pypy_package}".format(pypy_package=package_name_or_link) in shell_response.stdout:
            return False
        else:
            return True
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 13:   # pip permission error
            raise PermissionError(exc.stderr)
        else:
            error = 'Package "{pypy_package}" can not be installed via pip:\n\n{stderr}'.format(pypy_package=package_name_or_link, stderr=exc.stderr)
            lib_bash.banner(logging.ERROR, error)
            raise ValueError(error)


def pip_update_from_git(package_link: str, use_sudo: bool, show_output: bool = True) -> bool:
    """
    :returns updated - True if updated, False if it was already up to date

    >>> import unittest
    >>> unittest.TestCase().assertIsNotNone(pip_update_from_git, ('git+https://github.com/pypa/pip.git', True, False))


    """

    updated = pip_update_from_pypy(package_name_or_link=package_link, use_sudo=use_sudo)
    git_repository_slug = lib_helpers.get_git_repository_slug_from_link(package_link=package_link)
    git_remote_hash = lib_helpers.get_git_remote_hash(git_repository_slug=git_repository_slug)
    lib_helpers.save_git_hash_to_database(key=package_link, git_hash=git_remote_hash)
    return updated


def pip_update_from_weblink(package_link: str, use_sudo: bool, show_output: bool = True) -> bool:
    return pip_update_from_pypy(package_name_or_link=package_link, use_sudo=use_sudo, show_output=show_output)


def is_pip_git_package_up_to_date(package_name: str, package_link: str) -> bool:
    """
    >>> import unittest
    >>> unittest.TestCase().assertIsNotNone(pip_update_from_git, ('git+https://github.com/pypa/pip.git',True, False))
    >>> assert(is_pip_git_package_up_to_date('pip', 'git+https://github.com/pypa/pip.git')) == True

    """
    if not lib_helpers.is_pip_package_installed(package_name):
        return False

    git_repository_slug = lib_helpers.get_git_repository_slug_from_link(package_link=package_link)
    git_remote_hash = lib_helpers.get_git_remote_hash(git_repository_slug=git_repository_slug)
    git_local_hash = lib_helpers.get_git_local_hash_from_database_or_blank(key=package_link)

    if git_remote_hash != git_local_hash:
        return False
    else:
        return True
