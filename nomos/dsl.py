#!/usr/bin/env python
# Copyright (C) 2017 Thomas Huang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re

from . import nodes
from .errors import ParserException
from .parser import NomosTokenizer
from .parser import TokenType
from .util import resource


class DslParser(object):
    """Dsl parser"""

    FLOAT_VAR = re.compile(r'^-?\d+\.\d+$')
    """Float value regex expression"""

    INT_VAR = re.compile(r'^-?\d+$')
    """Integer value regex expression"""

    BOOL_VAR = {'true': True, 'false': False, 'on': True, 'off': False}
    """Boolean value"""

    VAR_TOKEN = r'\$'
    """Test case class  instacne variable value sign"""

    GVAR_TOKEN = '@'
    """Global module/variable/fucntion value sign"""

    CMP_TOKEN = "!"
    """Test case class compare value sign"""

    NULL_TOKEN = 'null'
    """Null token"""

    VAR_REGEX = re.compile(r'%s[a-zA-Z_][a-zA-Z0-9_]+' % (VAR_TOKEN))
    """Test case class  instacne variable value sign regex expression"""

    GVAR_REGEX = re.compile(r'%s[a-zA-Z_][a-zA-Z0-9_]+' % (GVAR_TOKEN))
    """Global module/variable/fucntion value sign regex expression"""

    CMP_REGEX = re.compile(r'%s\w+' % (CMP_TOKEN))
    """Compare data size regex expression"""

    FROM_IMPOER_REGEX = re.compile(r"from\s+([.a-zA-Z_][a-zA-Z0-9_])+\s+import\s+[a-zA-Z_][a-zA-Z0-9_]+")
    """from import regex expression"""

    IMPOER_REGEX = re.compile(r"import\s+[.a-zA-Z_][a-zA-Z0-9_]")
    """import regex expression"""

    def __init__(self, path, filename):

        filepath = os.path.join(path, filename)
        name = filename.split('.', 1)[0]
        className = self._className(name)
        self.node = nodes.HttpTestCalssNode(className, filepath)
        text = resource(filepath)
        self.reader = NomosTokenizer(text)
        self._diagnosticStack = []

    def _className(self, name):
        """Generate test class name"""
        parts = re.split(r'[_-]', name.lower())
        parts = [_.capitalize() for _ in parts]
        return ''.join(parts) + 'Test'

    def pushDiagnostics(self, message):
        """Added diagnostic message"""
        self._diagnosticStack.append(message)

    def popDiagnostics(self):
        """Pop out diagnostic message"""
        self._diagnosticStack.pop()

    def getDiagnosticsStacktrace(self):
        current_path = "".join(self._diagnosticStack)
        return str.format("Current path: {0}", current_path)

    def build(self):
        """Build test case rule from nomos dsl language"""
        methods = self.node.methods

        try:
            node = None
            paramsNode = []
            currentMethod = None
            self.pushDiagnostics("{")
            while not self.reader.eof:
                t = self.reader.pullNext()
                if t.tokenType == TokenType.MethodNameStart:
                    if currentMethod:
                        self.buildMethod(currentMethod, node, paramsNode)
                    node = []
                    paramsNode = []
                    currentMethod = nodes.ActionMethodNode()
                    methods.append(currentMethod)
                    name = self.reader.pullUtilMatch(']')
                    currentMethod.name = name
                if t.tokenType == TokenType.HttpMethodStart:
                    (httpMethod, httpPath) = self.reader.pullHttpMethodAndPath()
                    currentMethod.httpMethod = httpMethod.value
                    currentMethod.httpPath = httpPath.value
                    text = self.reader.pullRestOfLine()
                    _reader = self.reader
                    self.reader = NomosTokenizer(text)
                    self.parseObject(paramsNode)
                    self.reader = _reader

                if t.tokenType == TokenType.ImportStart:
                    imports = self.reader.pullUtilMatch("%>")
                    for line in imports.split("\n"):
                        line = line.strip()
                        if self.IMPOER_REGEX.match(line) or self.FROM_IMPOER_REGEX.match(line):
                            self.node.imports.append(line)

                if t.tokenType == TokenType.Key:
                    key = t.value
                    subnode = {
                        "key": key,
                        "keyQuoted": t.isQuoted
                    }
                    node.append(subnode)
                    self.parseKeyContent(subnode)

                elif t.tokenType == TokenType.ArrayStart:
                    if 'op' not in node:
                        node['op'] = ':'
                    node['type'] = "array"
                    node['value'] = self.parseArray()

                elif t.tokenType == TokenType.ObjectEnd:
                    return
        finally:
            self.buildMethod(currentMethod, node, paramsNode)
            self.popDiagnostics()

    def buildMethod(self, currentMethod, node, paramsNode):
        """Build method dsl tree"""
        self.appendKeyValue(currentMethod.params, paramsNode)
        for subnode in node:
            name = subnode.get("key")
            op = subnode.get("op")
            if name == 'params' and op in [':', '=']:
                self.appendKeyValue(currentMethod.params, subnode['value'])

            elif name == 'data' and op in [':', '=']:
                self.appendKeyValue(currentMethod.data, subnode['value'])

            elif name == 'head' and op == '<<':
                self.appendKeyValue(currentMethod.headers, subnode['value'])

            elif name == 'head' and op in [":", "="]:
                self.apendAssertNode(currentMethod.testAsserts, subnode['value'])

            elif name == 'json' and op == '<<':
                vnode = nodes.ValueNode(None, None)
                self.buildJsonNode(vnode, subnode['value'])
                currentMethod.json = vnode

            elif name == 'files' and op in [':', '=']:
                vnode = nodes.ValueNode(None, None)
                self.buildJsonNode(vnode, subnode['value'])
                currentMethod.files = vnode

            elif name in ['content', 'charset', 'code', 'content_type']:
                self.apendAssertNode(currentMethod.testAsserts, subnode)

            elif name == 'json' and op in [':', '=']:
                self.apendJsonAssertNode(currentMethod.testAsserts, subnode['value'])

            elif op in [':', '='] and subnode['type'] == 'text':
                self.tryApendContext(currentMethod.context, subnode)

    def tryApendContext(self, context, item):
        """Append context to method context"""
        key = self.convertToValueNode(item['key'], item['keyQuoted'])
        value = self.convertToValueNode(item['value'], item['valueQuoted'], True)
        if key.valueType == nodes.ValueType.VAR:
            context[key.value] = value

    def appendKeyValue(self, settings, nodeList):
        """Append key and value to config"""
        for item in nodeList:
            if item['op'] in [':', '=']:
                key = self.convertToValueNode(item['key'], item['keyQuoted'])
                value = self.convertToValueNode(item['value'], item['valueQuoted'], True)
                settings[key] = value
            else:
                # TODO
                pass

    def convertToValueNode(self, value, quoted, isValue=False):
        """Convet to  value node

        :param value: the node original value from dsl language
        :type value: str
        :param quoted: whether the value is quotued in dsl text
        :type quoted: boolean
        :param isValue: If False, the node is a value node, otherwise if a key node
        :type isValue: bool, optional
        :returns: the value node
        :rtype: nodes.ValueNode
        """
        if quoted:
            return nodes.ValueNode(value, nodes.ValueType.TEXT)

        if self.VAR_REGEX.match(value):
            return nodes.ValueNode(value[1:], nodes.ValueType.VAR)

        if isValue:
            if self.GVAR_REGEX.match(value):
                return nodes.ValueNode(value[1:], nodes.ValueType.GLOBAL_VAR)

            if value in self.BOOL_VAR:
                return nodes.ValueNode(self.BOOL_VAR[value], nodes.ValueType.BOOL)

            if value == self.NULL_TOKEN:
                return nodes.ValueNode(None, nodes.ValueType.NONE)

            if self.INT_VAR.match(value):
                # it will auto cast to long if too large
                return nodes.ValueNode(int(value), nodes.ValueType.NUMRIC)

            if self.FLOAT_VAR.match(value):
                return nodes.ValueNode(float(value), nodes.ValueType.NUMRIC)
        else:
            # The compare data size value node
            if self.CMP_REGEX.match(value):
                return nodes.ValueNode(value[1:], nodes.ValueType.CMP)

        return nodes.ValueNode(value, nodes.ValueType.TEXT)

    def apendAssertNode(self, asserts, nodeList):
        """Append assert node to method assert list"""

        if not isinstance(nodeList, list):
            nodeList = [nodeList]

        for item in nodeList:
            key = self.convertToValueNode(item['key'], item['keyQuoted'])
            value = self.convertToValueNode(item['value'], item['valueQuoted'], True)
            asserts.append(nodes.AssertNode(key, "head", value, item['op']))

    def apendJsonAssertNode(self, asserts, nodeList):
        """Append json assert node to method assert list"""

        for item in nodeList:
            valueType = item.get('type', 'unknow')
            if 'key' not in item:
                if valueType == 'object':
                    self.apendJsonAssertNode(asserts, item['value'])
                else:
                    node = self.convertToValueNode(item['value'], item['valueQuoted'], True)
                    asserts.append(node)
            else:
                key = self.convertToValueNode(item['key'], item['keyQuoted'])
                node = nodes.JsonAssertNode(key, 'json', None, item.get('op', ':'))

                if valueType == 'text':
                    node.value = self.convertToValueNode(item['value'], item['valueQuoted'], True)

                if valueType == 'object':
                    node.value = []
                    self.apendJsonAssertNode(node.value, item['value'])

                if valueType == 'array' and item['op'] in [':', '=', '==']:
                    node.nodeType = 'array'
                    node.value = []
                    self.apendJsonAssertNode(node.value, item['value'])

                asserts.append(node)

    def buildJsonNode(self, vnode, node, isValue=False):
        """build json node

        :param vnode: the value node
        :type vnode: JsonAssertNode
        :param node: the dls parse dict node
        :type node: dict
        :param isValue: If True is a value node, defaults to False
        :type isValue: bool, optional
        """

        if isValue:
            n = self.createValueNodeFromJson(node)
            vnode.valueType = n.valueType
            vnode.value = n.value
            return

        if isinstance(node, dict):
            if 'key' not in node and node['type'] == 'text':
                value = self.convertToValueNode(node['value'], node['valueQuoted'], True)
                vnode.valueType = value.valueType
                vnode.value = value.value
                return
            node = [node]

        for n in node:
            # check whether is a array  node
            isArrayItem = not isValue and ('key' not in n)

            if isArrayItem and vnode.valueType is None:
                vnode.valueType = nodes.ValueType.ARRAY
                vnode.value = []

            if not isArrayItem and vnode.valueType is None:
                vnode.valueType = nodes.ValueType.OBJ
                vnode.value = dict()

            if isArrayItem:
                vnode.value.append(self.createValueNodeFromJson(n))
            else:
                vnode.value[n['key']] = self.createValueNodeFromJson(n)

    def createValueNodeFromJson(self, node):
        """Creates value node from json format data"""
        if node['type'] == 'text':
            return self.convertToValueNode(node['value'], node['valueQuoted'], True)
        if node['type'] == 'object':
            subnode = nodes.ValueNode({}, nodes.ValueType.OBJ)
            self.buildJsonNode(subnode, node['value'])
            return subnode
        if node['type'] == 'array':
            subnode = nodes.ValueNode([], nodes.ValueType.ARRAY)
            for subValue in node['value']:
                it = nodes.ValueNode(None, None)
                subnode.value.append(it)
                self.buildJsonNode(it, subValue, True)
            return subnode

    def parseObject(self, node):
        """parse object"""
        try:
            self.pushDiagnostics("{")
            while not self.reader.eof:
                t = self.reader.pullNext()
                if t.tokenType == TokenType.Key:
                    key = t.value
                    subnode = {
                        "key": key,
                        "keyQuoted": t.isQuoted
                    }
                    node.append(subnode)
                    self.parseKeyContent(subnode)

                elif t.tokenType == TokenType.ObjectEnd:
                    return
        finally:
            self.popDiagnostics()

    def parseKeyContent(self, node):
        """Parse the token key content"""
        try:
            self.pushDiagnostics(str.format("{0} = ", node.get("key", ".")))
            while not self.reader.eof:
                t = self.reader.pullNext()

                if t.tokenType == TokenType.Operation:
                    node['op'] = t.value
                    self.parseValue(node)
                    return

                elif t.tokenType == TokenType.ObjectStart:
                    node['value'] = []
                    node['op'] = ":"
                    node['type'] = "object"
                    self.parseObject(node["value"])
                    return
        finally:
            self.popDiagnostics()

    def parseValue(self, node):
        """Parse the value of token"""

        if self.reader.eof:
            raise ParserException(
                "End of file reached while trying to read a value")

        self.reader.pullWhitespaceAndComments()
        start = self.reader.index

        try:
            while self.reader.isValue():
                t = self.reader.pullValue()
                if t.tokenType == TokenType.EoF:
                    pass

                elif t.tokenType == TokenType.LiteralValue:
                    node['valueQuoted'] = t.isQuoted
                    node['type'] = 'text'
                    node['value'] = t.value

                elif t.tokenType == TokenType.ObjectStart:
                    if 'op' not in node:
                        node['op'] = ':'
                    node['type'] = 'object'
                    node['value'] = []
                    self.parseObject(node['value'])

                elif t.tokenType == TokenType.ArrayStart:
                    if 'op' not in node:
                        node['op'] = ':'
                    node['type'] = 'array'
                    node['value'] = self.parseArray()

            self.ignoreComma()

        except Exception as e:
            raise ParserException(
                str.format("{0} {1}", str(e), self.getDiagnosticsStacktrace()))

        finally:
            # no value was found, tokenizer is still at the same position
            if self.reader.index == start:
                raise ParserException(
                    str.format("Hocon syntax error: {0}\r{1}",
                               self.reader.getHelpTextAtIndex(start), self.getDiagnosticsStacktrace()))

    def parseArray(self):
        """Parse array path"""
        try:
            self.pushDiagnostics("|")
            arr = []
            while (not self.reader.eof) and (not self.reader.isArrayEnd()):
                v = {}
                self.parseValue(v)
                arr.append(v)
                self.reader.pullWhitespaceAndComments()
            self.reader.pullArrayEnd()
            return arr
        finally:
            self.popDiagnostics()

    def ignoreComma(self):
        """Ignore comma"""
        if self.reader.isComma():
            self.reader.pullComma()
