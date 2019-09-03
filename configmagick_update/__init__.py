import pathlib
from .lib_main import pip_install
from .lib_main import pip_update


def get_version() -> str:
    with open(str(pathlib.Path(__file__).parent / 'version.txt'), mode='r') as version_file:
        version = version_file.readline()
    return version


__title__ = 'configmagick_update'
__version__ = get_version()
__name__ = 'configmagick_update'
