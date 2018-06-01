#!/usr/bin/env python
#
# Copyright 2017 Nomos
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""Parser for command-line options, arguments and sub-commands
Example:
Creating a ``Options`` instance, then add  group option  conifg. Calling the ``parse_args`` to handle the 
system comand-line options.
.. code-block:: python
    argopt = Options("Demo")
    groupopt = argopt.group("Site")
    _ = groupopt.define
    _('-H', '--server.host', default='localhost', help='The host of the http server (default %(default)r)')
    _('-p', '--server.port', default=8888, help='The port of the http server (default %(default)r)', type=int)
    _('-d', '--debug', help='Open debug mode (default %(default)r)', action='store_true', default=False)
    _('--secert_key', default="7oGwHH8NQDKn9hL12Gak9G/MEjZZYk4PsAxqKU4cJoY=",
        help='The secert key for secure cookies (default %(default)r)')
    _('-c', '--config', default='etc/demo/app.conf', help="config path (default %(default)r)", metavar="FILE")
    config = argsopt.parse_args()
"""
from argparse import ArgumentParser
import sys


class Options(object):
    """Command-line options parser
    :param help_doc: Terminal help doc description, defaults to None
    :type help_doc: string, optional
    :param args: config options , defaults to None
    :type args: list[string], optional
    """

    def __init__(self, help_doc=None, args=None):

        self.args = args or sys.argv
        if help_doc is None:
            self.argparser = ArgumentParser(add_help=False)
        else:
            self.argparser = ArgumentParser(help_doc)

    def group(self, help_doc):
        """Group options
        Creates a new with group help description doc head.
        :param string help_doc: group help decscription doc
        :returns: the group options wrapper
        :rtype: {GroupOptions}
        """
        group_parser = self.argparser.add_argument_group(help_doc)
        return GroupOptions(group_parser)

    def set_defaults(self, **c):
        """Setting default config in  ArgumentParser instance"""
        self.argparser.set_defaults(**c)

    @property
    def define(self):
        """Returns the add_argument"""
        return self.argparser.add_argument

    def parse_args(self, args=None):
        """Pareses know command options, and returns the options result
        :param list args: the comannd option list conifg.
            Defaults to handle the sytem comand options in sys.argv.
        """
        args = args if args is not None else self.args
        opt, _ = self.argparser.parse_known_args(args)
        return opt


class GroupOptions(object):
    """Command-line group config options"""

    def __init__(self, group_parser):
        self.group_parser = group_parser

    @property
    def define(self):
        """Returns the add_argument"""
        return self.group_parser.add_argument

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


#: the global default options instance
__options = None


def setup_options(doc):
    """Sets the help doc description  for module options instnace"""
    global __options
    __options = Options(doc)


def group(help_doc):
    """Creates group options instance in module options instnace"""
    return __options.group(help_doc)


def define(*args, **kw):
    """Defines a config option in module options instnace"""
    return __options.define(*args, **kw)


def set_defaults(**c):
    """Sets the default config values in module options instnace"""
    __options.set_defaults(**c)


def parse_args(args=None):
    """Pareses command options in module options instnace
    Returns the options result.
    """
    return __options.parse_args(args)
