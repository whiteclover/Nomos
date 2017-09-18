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


class AbstractNode(object):
    """Abstact node
    """
    pass


class ValueType(object):
    """Value node type"""

    TEXT = 1
    """ text type"""
    VAR = 2
    """variable type"""
    RULE = 3
    """rule type"""

    BOOL = 4
    """boolean type"""

    NUMRIC = 5
    """numbric type"""

    GLOBAL_VAR = 6
    """global varaible"""

    NONE = 7
    """ null type"""

    RAW = 8
    """raw data"""

    CMP = 9
    """ compare and check data size type"""

    OBJ = 10
    """Object type(dict)"""

    ARRAY = 11
    """List type"""


class ValueNode(AbstractNode):
    """Value node 

    :param value: the real value
    :type value: text
    :param valueType: the node value type
    :type valueType: ValueType
    """

    def __init__(self, value, valueType=ValueType.RAW):

        self.valueType = valueType
        self.value = value

    def realValue(self):
        valueType = self.valueType
        if valueType == ValueType.NONE:
            return None

        if valueType == ValueType.TEXT:
            return '"' + self.value + '"'

        if valueType == ValueType.VAR:
            return 'self.' + self.value

        if valueType == ValueType.GLOBAL_VAR:
            return self.value

        return self.value

    def __format__(self, formator):
        if formator == "v":
            return self.value
        return str(self)

    def __json__(self):
        return {
            "__type": "ValueNode",
            "data": {
                "value": self.value,
                "valueType": self.valueType
            }
        }

    def __str__(self):
        return """ValueNode <
        value:{}, 
        valueType :{}
        >""".format(self.value, self.valueType)

    __repr__ = __str__


class HttpTestCalssNode(AbstractNode):
    """Http test unit class node
    """

    def __init__(self, name, filePath, baseClass="WebTestCase"):
        """

        :param name: the class name
        :type name: str
        :param filePath: the soure file path
        :type filePath: str
        :param baseClass: the base test case class, defaults to "WebTestCase"
        :type baseClass: str, optional
        """
        self.filePath = filePath

        # the test case mixin classe names
        self.mixins = []
        self.baseClass = baseClass

        #: the import list
        self.imports = []
        self.name = name
        #: the test method list
        self.methods = []

    def __str__(self):
        return "HttpNode <name:{}, methods :{}>".format(self.filePath, self.methods)

    __repr__ = __str__


class ActionMethodNode(AbstractNode):

    def __init__(self, name=None, method="GET", path=None):
        """The http test action 


        :param name: the test method name, defaults to None
        :type name: str, optional
        :param method: the http method name, defaults to "GET"
        :type method: str, optional
        :param path: the http test path, defaults to None
        :type path: str, optional
        """
        self.name = name
        self.httpMethod = method
        self.httpPath = path

        #: the GET method params
        self.params = {}
        #: the POST or other PUT methods params
        self.data = {}
        #: the defult request headers to set
        self.headers = {}
        #: the request is json content type
        self.json = None

        #: the multiple files upload
        self.files = None
        #: the test assert node list
        self.testAsserts = []
        #: the http test case class variables
        self.context = {}

    def __str__(self):
        return """ActionMethodNode <
        name: {},
        httpMethod: {},
        httpPath: {},
        params: {},
        data:{}
        context:{},
        json: {},
        files:{}
        headers: {},
        testAsserts: {}
        >""".format(self.name, self.httpMethod, self.httpPath, self.params,
                    self.data, self.context, self.json, self.files, self.headers, self.testAsserts)

    __repr__ = __str__


class Node(AbstractNode):

    def __init__(self, key, nodeType, value):
        """Base node

        : param key: the node key value
        : type key: ValueNode
        : param nodeType: the node type
        : type nodeType: str
        : param value: the node  value
        : type value: ValueNode
        """
        self.key = key
        self.nodeType = nodeType
        self.value = value

    def __str__(self):
        return """Node <
        key: {},
        nodeType: {},
        value: {}
        >""".format(self.key, self.nodeType, self.value)

    __repr__ = __str__


class AssertNode(Node):

    def __init__(self, key, nodeType, value, operation):
        """Assert node

        : param key: the node key value
        : type key: ValueNode
        : param nodeType: the node type
        : type nodeType: str
        : param value: the node  value
        : type value: ValueNode
        : param operation: the node operation
        : type operation: str
        """
        super(AssertNode, self).__init__(key, nodeType, value)
        self.operation = operation

    def __str__(self):
        return """{} <
        key: {},
        operation: {}
        nodeType: {},
        value: {}
        >""".format(self.__class__.__name__, self.key, self.operation, self.nodeType, self.value)

    __repr__ = __str__


class JsonAssertNode(AssertNode):
    """Json Assert node"""

    def __json__(self):
        return {
            "__type": "JsonAssertNode",
            "data": {
                "key": self.key,
                "operation": self.operation,
                "nodeType": self.nodeType,
                "value": self.value
            }
        }
