# STDLIB
import errno
import json
import logging
import subprocess
import sys
from typing import List

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
        if not lib_helpers.is_pip_git_package_up_to_date(git_link=name_or_link):
            updated = pip_update_from_git(git_link=name_or_link, use_sudo=use_sudo)     # returns always true, but we do it only when update is needed
            return updated
    elif package_type == 'weblink':
        pip_update_from_weblink(weblink=name_or_link, use_sudo=use_sudo)
        return True
    else:
        return False


def pip_update_from_pypy(pypy_package: str, use_sudo: bool, show_output: bool = True) -> bool:
    """
    :returns updated - True if updated, False if it was already up to date


    >>> assert pip_update_from_pypy('urllib3==1.24.1', use_sudo=True, show_output=False) is not None    # first Update to old Version
    >>> assert pip_update_from_pypy('urllib3', use_sudo=True, show_output=False) == True                # second Update to new Version
    >>> assert pip_update_from_pypy('urllib3', use_sudo=True, show_output=False) == False               # third Update - is already up to date
    >>> assert pip_update_from_pypy('chardet', use_sudo=True, show_output=False) is not None            # third Update - is already up to date

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


def pip_update_from_git(git_link: str, use_sudo: bool, show_output: bool = True) -> bool:
    """
    :returns updated - True if updated, False if it was already up to date

    >>> assert pip_update_from_git('git+https://github.com/pypa/pip.git', use_sudo=True, show_output=False) == True        # always true here

    """

    updated = pip_update_from_pypy(pypy_package=git_link, use_sudo=use_sudo)
    git_repository_slug = lib_helpers.get_git_repository_slug_from_link(git_link=git_link)
    git_remote_hash = lib_helpers.get_git_remote_hash(git_repository_slug=git_repository_slug)
    lib_helpers.save_git_hash_to_database(key=git_link, git_hash=git_remote_hash)
    return updated


def pip_update_from_weblink(weblink: str, use_sudo: bool, show_output: bool = True) -> bool:
    return pip_update_from_pypy(pypy_package=weblink, use_sudo=use_sudo, show_output=show_output)


def is_pip_git_package_up_to_date(git_link: str) -> bool:
    """
    >>> assert pip_update_from_git('git+https://github.com/pypa/pip.git', use_sudo=True, show_output=False) == True        # always true here
    >>> assert(is_pip_git_package_up_to_date('git+https://github.com/pypa/pip.git')) == True

    """
    git_repository_slug = lib_helpers.get_git_repository_slug_from_link(git_link=git_link)
    git_remote_hash = lib_helpers.get_git_remote_hash(git_repository_slug=git_repository_slug)
    git_local_hash = lib_helpers.get_git_local_hash_from_database_or_blank(key=git_link)
    if git_remote_hash != git_local_hash:
        return False
    else:
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
