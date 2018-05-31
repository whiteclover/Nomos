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

import re

from . import nodes


class NomasComplirer(object):
    """Test case node complier"""

    def __init__(self):
        self.code = ''
        self.indent = 0

    def puts(self, line, indent=None):
        """Puts line with indent"""
        indent = indent or self.indent
        self.write('\t' * indent + line + '\n')

    def write(self, text):
        """Append text to code section"""
        self.code += text

    def complie(self, node, indent=0):
        """Complie dls node to python code


        :param node: the test case dls node, the subclass of nodes.AbstactNode
        :type node: nodes.AbstactNode
        :param indent: the indent depth, defaults to 0
        :type indent: number, optional
        """
        if isinstance(node, nodes.HttpTestCalssNode):
            # import modules
            if node.imports:
                for importLine in node.imports:
                    self.puts(importLine)
                self.puts("")

            # writes class code
            self.puts('class %s(%s):\n' % (node.name, node.baseClass))
            indent += 1
            self.writeSetupMethod(indent)
            for subnode in node.methods:
                self.complie(subnode, indent)
        elif isinstance(node, nodes.ActionMethodNode):
            self.complieMethod(node, indent)

    def writeSetupMethod(self, indent):
        """Writes setup method"""
        self.puts("@classmethod", indent)
        self.puts('def setUpClass(cls):', indent)
        self.puts('cls.initialize()', indent + 1)
        self.puts('cls.session=_session', indent + 1)
        self.puts("cls.params = _params", indent + 1)

    def complieMethod(self, node, indent=0):
        """Write method section"""

        self.puts('')
        if node.name == 'initialize':
            self.puts("@classmethod", indent)
            self.puts('def initialize(cls):', indent)
            indent += 1
            for key, value in node.context.items():
                self.puts('cls.%s = %s' % (key, value.realValue()), indent)
            return

        name = "_" .join(re.split("\W+", node.name))
        self.puts("def {}(self):".format("test_" + name), indent)
        indent += 1

        # writes request headers
        self.puts('headers = {}', indent)
        for k, v in node.headers.items():
            k = self.formatHeaderKey(k.value)
            self.puts('headers[%r] = %s' % (k, v.realValue()), indent)

        # writes http path params
        self.puts('params = {}', indent)
        for k, v in node.params.items():
            v = v.realValue()
            self.puts('params[%r] = %s' % (k.value, v), indent)

        # writes http conttent params
        self.puts('data = {}', indent)
        for k, v in node.data.items():
            v = v.realValue()
            self.puts('data[%r] = %s' % (k.value, v), indent)

        # writes json data
        if node.json is not None:
            self.puts('jsonData =%s' % (self.jsonNodePyCode(node.json)), indent)
        else:
            self.puts('jsonData = None', indent)

        # writes files data
        if node.files is not None:
            self.puts('files =%s' % (self.jsonNodePyCode(node.files)), indent)
        else:
            self.puts('files = None', indent)

        self.puts('res = self.session.doRequest("{}", "{}", params=params, data=data, headers=headers, json=jsonData, files=files)'.format(
            node.httpMethod, node.httpPath), indent)

        self.puts("")
        self.puts("#Assert section", indent)
        for testAssert in node.testAsserts:
            self.complieAssert(testAssert, indent)

    def jsonNodePyCode(self, node):
        """Format json data to python code"""
        if node.valueType not in [nodes.ValueType.OBJ, nodes.ValueType.ARRAY]:
            return node.realValue()

        value = None
        if node.valueType == nodes.ValueType.ARRAY:
            value = "["
            for subnode in node.value:
                value += "%s," % (self.jsonNodePyCode(subnode))
            value += "]"

        if node.valueType == nodes.ValueType.OBJ:
            value = "{"
            for key, subval in node.value.items():
                value += "%r: %s," % (key, self.jsonNodePyCode(subval))
            value += "}"

        return value

    def complieAssert(self, node, indent=0):
        """Complie assert section"""
        if isinstance(node, nodes.JsonAssertNode):
            self.complieJsonAssert(node, indent)
        else:
            self.complieNormalAssert(node, indent)

    def complieJsonAssert(self, node, indent=0):
        """Complie json assert section"""
        # self.puts("#Testing json assert for {}".format(node.key.value), indent)
        self.puts('assertNode =%s' % (self.jsonAssertNodePyCode(node)), indent)
        self.puts("self.assertJson(res.json, assertNode)", indent)

    def jsonAssertNodePyCode(self, node):
        """Returns the assert data serialize python code"""

        if isinstance(node, nodes.ValueNode):
            return"_n.ValueNode(%s, _n.ValueType.RAW)" % (node.realValue())

        key = "_n.ValueNode(%r, %r)" % (node.key.value, node.key.valueType)
        value = None
        if isinstance(node.value, nodes.ValueNode):
            value = "_n.ValueNode(%s, _n.ValueType.RAW)" % (node.value.realValue())
        else:
            value = []
            for subnode in node.value:
                value.append(self.jsonAssertNodePyCode(subnode))
            value = "[" + ", \n".join(value) + "]"

        return """_n.JsonAssertNode(
        %s,
        %r,
        %s,
        %r)
""" % (key, node.nodeType, value, node.operation)

    def complieNormalAssert(self, node, indent):
        """Complie normal assert section"""
        assertKey = self._key(node.key.value)

        if assertKey in ('Status', 'Code', 'ContentType', 'Charset'):
            self._line('self.assert%s(res, %r, %s)' % (assertKey, node.operation, node.value.realValue()), indent)

        elif assertKey == 'Content':
            self._line('self.assertContent(res, %r, %s)' % (node.operation, node.value.realValue()), indent)

        elif node.operation in [':', '=']:
            key = self._key(node.key.value)
            self._line('self.assertHeader(res,%r, %r, %s)' % (key, node.operation, node.value.realValue()), indent)
        else:
            key = self._key(node.key.value)
            self._line('self.assertHeader(res,%r, %r, %s)' % (key, node.operation, node.value.realValue()), indent)

    def formatHeaderKey(self, key):
        """format headerk ey to speficial"""
        parts = re.split(r'[_-]', key.lower())
        parts = [_.capitalize() for _ in parts]
        return '-'.join(parts)

    def _line(self, line, indent):
        """Puts line"""
        self.puts(line, indent)

    def _key(self, key):
        """header key"""
        parts = re.split(r'[_-]', key.lower())
        parts = [_.capitalize() for _ in parts]
        return ''.join(parts)
