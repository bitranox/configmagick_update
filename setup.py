"""Setuptools entry point."""
import codecs
import os
import subprocess
import sys


def install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", package])


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

description = 'configmagick_update'

dirname = os.path.dirname(__file__)
readme_filename = os.path.join(dirname, 'README.rst')

long_description = description
if os.path.exists(readme_filename):
    try:
        readme_content = codecs.open(readme_filename, encoding='utf-8').read()
        long_description = readme_content
    except Exception:
        pass

try:
    import configmagick_update
    # update is cheap here - so we update all modules we use
    configmagick_update.lib_main.pip_update('configmagick_bash', 'git+https://github.com/bitranox/configmagick_bash.git', use_sudo=False)
    configmagick_update.lib_main.pip_update('lib_regexp', 'git+https://github.com/bitranox/lib_regexp.git', use_sudo=False)
    configmagick_update.lib_main.pip_update('lib_log_utils', 'git+https://github.com/bitranox/lib_log_utils.git', use_sudo=False)
    configmagick_update.lib_main.pip_update('lib_shell', 'git+https://github.com/bitranox/lib_shell.git', use_sudo=False)

except (ImportError, ModuleNotFoundError):
    # update is expansive here - so we update only what we need to install
    install('git+https://github.com/bitranox/configmagick_bash.git')  # installs also lib_logutils and lib_shell
    install('git+https://github.com/bitranox/lib_regexp.git')

setup(name='configmagick_update',
      version='0.0.1',
      url='https://github.com/bitranox/configmagick_update',
      packages=['configmagick_update'],
      install_requires=['pytest', 'typing', 'chardet', 'configmagick_bash', 'lib_regexp'],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      description=description,
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='Robert Nowotny',
      author_email='rnowotny1966@gmail.com',
      classifiers=CLASSIFIERS
      )

# install_requires: what other distributions need to be installed when this one is.
# setup_requires: what other distributions need to be present in order for the setup script to run
# tests_require: If your project’s tests need one or more additional packages besides those needed to install it,
#                you can use this option to specify them
