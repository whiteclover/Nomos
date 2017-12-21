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


import base64
import codecs


def resource(filename, binary=False, encoding="utf-8", b64=False):
    """Return file cotnent

    :param filename: file path 
    :type filename:str
    :param binary: open file mode, defaults to "rb" if is bianry else "r" 
    :type mode: Boolean
    :param encoding:  content encoding, defaults to "utf-8"
    :type encoding: str, optional
    :param b64: if True will return base64 encoding text, defaults to False
    :type b64: bool, optional
    :returns: the file content
    :rtype: str|bytes
    """

    mode = "rb" if binary else "r"
    if binary:
        encoding = None
    with codecs.open(filename, mode, encoding) as f:
        content = f.read()
        if b64:
            content = base64.b64encode(content)
        return content


class lazy_attr(object):
    """Lazy attr decorator"""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except:  # pragma: no cover
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
