# STDLIB
import pathlib

# OWN
import lib_bash


class Config(object):
    path_version_files_dir: pathlib.Path = lib_bash.get_path_home_dir_current_user() / '.config/configmagick/configmagick_update'
    path_version_file: pathlib.Path = path_version_files_dir / 'versions.dat'
