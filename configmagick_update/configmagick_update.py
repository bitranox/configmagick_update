# STDLIB
import errno
import logging
import sys
from typing import List

# OWN
import lib_log_utils

# PROJ
try:
    from . import lib_args
    from . import lib_main
    from .config import Config
except ImportError:                 # for local development
    import lib_args                 # type: ignore # pragma: no cover
    import lib_main                 # type: ignore # pragma: no cover
    from config import Config       # type: ignore # pragma: no cover


logger = logging.getLogger()
lib_log_utils.add_stream_handler_color()
Config.path_version_files_dir.mkdir(mode=0o775, parents=True, exist_ok=True)


def main(sys_argv: List[str] = sys.argv[1:]) -> None:
    """
    >>> import unittest
    >>> # raises Systemexit because everything is done - so we put assertIsNotNone
    >>> unittest.TestCase().assertIsNotNone(main, ['pip_install','pip','git+https://github.com/pypa/pip.git', '--use_sudo'])
    >>> # raises Systemexit because everything is done - so we put assertIsNotNone
    >>> unittest.TestCase().assertIsNotNone(main, ['pip_install','pip','git+https://github.com/pypa/pip.git', '--use_sudo'])

    """

    # noinspection PyBroadException
    try:
        lib_log_utils.add_stream_handler()

        argparse_namespace, parser = lib_args.parse_args(sys_argv)

        if argparse_namespace.which_parser == 'pip_install':
            lib_main.pip_install(package_name=argparse_namespace.package_name,
                                 package_link=argparse_namespace.package_link,
                                 use_sudo=argparse_namespace.use_sudo
                                 )
        elif argparse_namespace.which_parser == 'pip_update':
            lib_main.pip_update(package_name=argparse_namespace.package_name,
                                package_link=argparse_namespace.package_link,
                                use_sudo=argparse_namespace.use_sudo
                                )
        else:
            parser.print_help()

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
