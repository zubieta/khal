# coding: utf-8
# vim: set ts=4 sw=4 expandtab sts=4:
# Copyright (c) 2013-2014 Christian Geier & contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os

from configobj import ConfigObj, flatten_errors
from validate import Validator
import xdg.BaseDirectory

from khal import __productname__
from khal.log import logger

DEFAULTSPATH = os.path.join(os.path.dirname(__file__), 'default.khal')
SPECPATH = os.path.join(os.path.dirname(__file__), 'khal.spec')


def _find_configuration_file():
    """Return the configuration filename.

    This function builds the list of paths known by khal and
    then return the first one which exists. The first paths
    searched are the ones described in the XDG Base Directory
    Standard. Each one of this path ends with
    DEFAULT_PATH/DEFAULT_FILE.

    On failure, the path DEFAULT_PATH/DEFAULT_FILE, prefixed with
    a dot, is searched in the home user directory. Ultimately,
    DEFAULT_FILE is searched in the current directory.
    """
    DEFAULT_FILE = __productname__ + '.conf'
    DEFAULT_PATH = __productname__
    resource = os.path.join(DEFAULT_PATH, DEFAULT_FILE)

    paths = []
    paths.extend([os.path.join(path, resource)
                  for path in xdg.BaseDirectory.xdg_config_dirs])
    paths.append(os.path.expanduser(os.path.join('~', '.' + resource)))
    paths.append(os.path.expanduser(DEFAULT_FILE))

    for path in paths:
        if os.path.exists(path):
            return path

    return None


def _test_default_calendar(config):
    """test if config['default']['default_calendar'] is set to a sensible
    value
    """
    if config['default']['default_calendar'] is None:
        config['default']['default_calendar'] = config['calendars'].keys()[0]
    elif config['default']['default_calendar'] not in config['calendars']:
        print("in section [default] {} is not valid for 'default_calendar', "
              "must be one of {}".format(config['default']['default_calendar'],
                                         config['calendars'].keys())
              )
        raise ValueError  # TODO own error class


def get_config(config_path=None):
    """reads the config file, validates it and return a config dict

    :param config_path: path to a custom config file, if none is given the
                        default locations will be searched
    :type config_path: str
    :returns: configuration
    :rtype: dict
    """
    if config_path is None:
        config_path = _find_configuration_file()

    logger.debug('using the config file at {}'.format(config_path))
    config = ConfigObj(DEFAULTSPATH)

    user_config = ConfigObj(config_path,
                            configspec=SPECPATH,
                            interpolation=False,
                            file_error=True,
                            )

    validator = Validator()
    results = user_config.validate(validator, preserve_errors=True)
    if not results:
        for entry in flatten_errors(config, results):
            # each entry is a tuple
            section_list, key, error = entry
            if key is not None:
                section_list.append(key)
            else:
                section_list.append('[missing section]')
            section_string = ', '.join(section_list)
            if error is False:
                error = 'Missing value or section.'
            print(section_string, ' = ', error)
        raise ValueError  # TODO own error class

    config.merge(user_config)
    _test_default_calendar(config)

    return config
