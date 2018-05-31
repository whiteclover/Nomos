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


from unittest import TestCase
import re

from . import nodes


class WebTestCase(TestCase):
    """Web HTTP Test class

    handle json data
    handle http header

    """

    MATCH_RE = re.compile('/(.*)/([ims]+)?')
    FLAGS = {
        'i': re.I,
        'm': re.M,
        's': re.S
    }

    @classmethod
    def initialize(cls):
        pass

    def assertHeader(self, response, key, assetType, value):
        """Check a head line value"""
        self.assertRule(response.getHeader(key), assetType, value)

    def assertContentType(self, response, assetType, value):
        """Check HTTP Response ContentType head"""
        self.assertRule(response.contentType, assetType, value)

    def assertCharset(self, response, assetType, value):
        """Check HTTP Response charset info"""
        self.assertRule(response.charset, assetType, value)

    def assertCode(self, response, assetType, value):
        """Check HTTP Response Status code"""
        self.assertRule(response.status, assetType, value)

    def assertContent(self, response, assetType, value):
        """Check HTTP Response Body"""
        self.assertRule(response.content, assetType, value)

    def assertJson(self, json, jsonAssertNode):
        self.assertIsNotNone(json)
        key = jsonAssertNode.key.value
        if isinstance(jsonAssertNode.value, nodes.ValueNode):
            data = json[key]
            if jsonAssertNode.key.valueType == nodes.ValueType.CMP:
                data = len(data)
            self.assertRule(data, jsonAssertNode.operation, jsonAssertNode.value.value)
        else:
            if jsonAssertNode.nodeType == 'array':
                subnode = json[key]
                idx = 0
                for node in jsonAssertNode.value:
                    data = subnode[idx]
                    if isinstance(node, nodes.ValueNode):
                        self.assertRule(data,  ":", node.value)
                        idx += 1
                    else:
                        self.assertJson(data, node)

            else:
                for node in jsonAssertNode.value:
                    self.assertJson(json[key], node)

    def assertRule(self, data, assetType, value):

        if assetType in [':', '=', '==']:
            # the key value equal assert
            self.assertEqual(data, value)

        elif assetType == '<-':
            # the key value in assert
            self.assertIn(value, data)

        elif assetType == '=~':
            # the key value regex match assert
            bodyRe = self._complieRegexMatch(value)
            self.assertTrue(bodyRe.search(data))

        elif assetType == '~~':
            # the key value length assert
            self.assertEqual(len(data), value)

        elif assetType == '!=':
            # the value not equal
            self.assertNotEqual(data, value)
        elif assetType == '>':
            self.assertGreater(data, value)
        elif assetType == '>=':
            self.assertGreaterEqual(data, value)
        elif assetType == '<':
            self.assertLess(data, value)
        elif assetType == '<=':
            self.assertLessEqual(data, value)

    def _complieRegexMatch(self, value):
        """Comlie regex exprression from text like "/(.*)/([ims]+)?"

        eg::
            /ok/i, /ok/ims
        """
        m = self.MATCH_RE.match(value)
        flag = None
        if m:
            bodyRe, flags = m.group(1), m.group(2)
            if flags:
                for _ in flags:
                    flag = flag | self.FLAGS[_] if flag else self.FLAGS[_]

        return re.compile(bodyRe, flag) if flag else re.compile(bodyRe)
