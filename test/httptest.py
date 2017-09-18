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
from nomos.http import HttpSession


class HttpSessionTest(unittest.TestCase):

    def testGETDoRequest(self):
        session = HttpSession("http://httpbin.org")
        res = session.doRequest("GET", "/get", params={"ctx": "hello"})

        self.assertEqual(res.status, 200)
        self.assertEqual(res.json['args']['ctx'], "hello")

    def testPOSTDoRequest(self):
        session = HttpSession("http://httpbin.org")
        res = session.doRequest("POST", "/post", data={"ctx": "hello"})
        self.assertEqual(res.status, 200)
        self.assertEqual(res.json['form']['ctx'], "hello")

        res = session.doRequest("POST", "/post", data="Hello")

        self.assertEqual(res.status, 200)
        self.assertEqual(res.json['data'], "Hello")

        res = session.doRequest("POST", "/post", params={"param": "test"}, json={"data": "Hello"})

        self.assertEqual(res.status, 200)
        self.assertEqual(res.json['data'], '{"data": "Hello"}')
        self.assertEqual(res.json['json']['data'], "Hello")
        self.assertEqual(res.json['args']['param'], "test")

    def testFileDoRequest(self):

        files = {
            "file": [
                "report.xls",
                "data",
                "application/txt",
                {
                    "Expires": 0
                }
            ]
        }

        session = HttpSession("http://httpbin.org")
        res = session.doRequest("POST", "/post", files=files)
        self.assertEqual(res.status, 200)
        self.assertEqual(res.json['files']['file'], "data")
