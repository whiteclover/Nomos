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


import os
import unittest


from . import nodes
from .compat import import_module_from_file
from .compiler import NomasComplirer
from .dsl import DslParser
from .http import HttpSession
from .testcase import WebTestCase
from .util import resource
from .globalvar import config


class NomosRunner(object):
    """Nomos test case runner

    :param url: prefix url for the new :class:`HttpSession` object.
    :param paths: the nomos dsl test  case directory list or file path.
    :type paths: list
    :param debug:  If  ``True`` the test will be verbosity , defaults to None
    :type debug: boolean, optional
    :param timeout: (optional) How long to wait for the server to send
                    data before giving up, as a float, or a :ref:`(connect timeout,
                    read timeout) <timeouts>` tuple.
    :type timeout: float or tuple
    :param verify: (optional) Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
    :param cert: (optional) if String, path to ssl client cert file (.pem).
                    If Tuple, ('cert', 'key') pair.
    :param minixs: (optional) if Classes list, the test case minixes to inherit.
                 other wise a list of minix path to load test case minix.


    """

    def __init__(self, url, paths, debug=None, timeout=5, verify=True, cert=None, minixs=None, **params):
        self.paths = paths
        self.url = url
        self.debug = debug
        self.timeout = timeout
        self.verify = verify
        self.cert = cert
        self.params = params
        if minixs:
            self.minixs = self.getMinixClasses(None, minixs)
        else:
            self.minixs = []

    def defaultNamespace(self):
        """Default test case name space"""
        client = HttpSession(self.url, timeout=self.timeout, verify=self.verify, cert=self.cert)
        return {
            '_session': client,
            "_params": self.params,
            'resource': resource,
            'WebTestCase': WebTestCase,
            "_n": nodes,
            "config": config
        }

    def run(self):
        """Build dsl and run the http test case."""
        testClassesToRun = []
        for path in self.paths:
            # walk the directory or file list.
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    minixs = self.getMinixClasses(path, files)
                    for f in files:
                        testClass = self.genTestClassFromFile(path, f)
                        if testClass:
                            # extends minix classess
                            if minixs or self.minixs:
                                classes = self.minixs + minixs + self.getClassBases(testClass)
                                testClass = type(testClass.__name__, tuple(classes), dict(testClass.__dict__))
                            testClassesToRun.append(testClass)
            else:
                path, filename = os.path.split(path)
                testClass = self.genTestClassFromFile(path, filename)
                if testClass:
                    if self.minixs:
                        classes = self.minixs + self.getClassBases(testClass)

                        testClass = type(testClass.__name__, tuple(classes), dict(testClass.__dict__))
                    testClassesToRun.append(testClass)

        loader = unittest.TestLoader()

        suitesList = []
        for testClass in testClassesToRun:
            suite = loader.loadTestsFromTestCase(testClass)
            suitesList.append(suite)

        bigSuite = unittest.TestSuite(suitesList)
        verbosity = 2 if self.debug else 0
        runner = unittest.TextTestRunner(verbosity=verbosity)
        results = runner.run(bigSuite)
        return results

    def getClassBases(self, klass):
        """Getting the base classes excluding the type<object>"""
        bases = klass.__bases__
        if len(bases) == 1 and bases[0] == object:
            return []
        else:
            return list(bases)

    def getMinixClasses(self, path, files):
        """Get minix classes


        :param path: the parent path
        :type path: string
        :param files: the file names list
        :type files: list[string]
        :returns: the mixin classes
        :rtype: list
        """
        minixs = []
        for f in files:
            if not isinstance(f, str):
                minixs.append(f)
            elif f.endswith(".py"):
                modpath = os.path.join(path, f) if path else f
                mod = import_module_from_file("minixs", modpath)
                minixNames = getattr(mod, "__all__")
                for name in minixNames:
                    minixs.append(getattr(mod, name))
        return minixs

    def genTestClassFromFile(self, path, filename):
        """Generate test case class from file resource"""
        if not filename.endswith(".ns"):
            return

        name, ext = filename.split('.', 1)
        if ext == 'ns':
            code, class_name = self.genTestcase(path, filename)
            ns = self.defaultNamespace()

            code = compile(code, filename, 'exec')
            exec(code, ns)
            return ns[class_name]

    def genTestcase(self, path, filename):
        """Generate test case class  code"""
        dslParser = DslParser(path, filename)
        node = dslParser.buildNomos()
        compiler = NomasComplirer()
        compiler.complie(node)
        return compiler.code, node.name
