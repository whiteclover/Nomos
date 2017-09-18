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


import unittest

from nomos.util import lazy_attr, resource


class Dummy(object):
    pass


class TestLazyAttr(unittest.TestCase):

    def _makeOne(self, wrapped):
        return lazy_attr(wrapped)

    def test___get__withinst(self):
        def wrapped(inst):
            return 'a'
        decorator = self._makeOne(wrapped)
        inst = Dummy()
        result = decorator.__get__(inst)
        self.assertEqual(result, 'a')
        self.assertEqual(inst.__dict__['wrapped'], 'a')

    def test___get__noinst(self):
        decorator = self._makeOne(None)
        result = decorator.__get__(None)
        self.assertEqual(result, decorator)

    def test___doc__copied(self):
        def wrapped(inst):
            """My doc"""
        decorator = self._makeOne(wrapped)
        self.assertEqual(decorator.__doc__, "My doc")


class ResourceTest(unittest.TestCase):

    def tet_resource(self):

        data = resource("./resource/data.txt")
        self.assertEqual(data, "This a data file")
