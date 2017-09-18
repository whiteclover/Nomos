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


import requests.sessions

from .util import lazy_attr


class HttpSession(object):
    """Http Session

     :param url: prefix url for the new :class:`Request` object.
     :param timeout: (optional) How long to wait for the server to send
                    data before giving up, as a float, or a :ref:`(connect timeout,
                    read timeout) <timeouts>` tuple.
    :type timeout: float or tuple
    :param verify: (optional) Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
    :param cert: (optional) if String, path to ssl client cert file (.pem).
                    If Tuple, ('cert', 'key') pair.
    """

    def __init__(self, url, timeout=5, verify=True, cert=None):
        self.url = url
        self.timeout = timeout

        #: request session instance
        self.session = requests.sessions.Session()
        self.cert = cert
        self.verify = verify

    def doRequest(self, method, path, params=None, data=None, headers=None, json=None, files=None):
        """Returns :class:`HttpResponse <Response>` object.


            :param method: method for the new :class:`Request` object.
            :param path: postfix path for the new :class:`Request` object.
            :param params: (optional) Dictionary or bytes to be sent in the query
                string for the :class:`Request`.
            :param data: (optional) Dictionary, bytes, or file-like object to send
                in the body of the :class:`Request`.
            :param json: (optional) json to send in the body of the
                :class:`Request`.
            :param headers: (optional) Dictionary of HTTP Headers to send with the
                :class:`Request`.
            :param files: (optional) Dictionary of ``'filename': file-like-objects``
                for multipart encoding upload.
            :rtype: requests.Response"""

        url = self.url + path
        res = self.session.request(method, url, params=params, data=data, headers=headers, json=json, files=files,
                                   verify=self.verify, cert=self.cert, timeout=self.timeout)
        return HttpResponse(res)


class HttpResponse(object):
    """Http response wrapper"""

    def __init__(self, res):
        self.res = res

    @lazy_attr
    def json(self):
        """ Returns a json response."""
        return self.res.json()

    def getHeader(self, key):
        """Get header value"""
        key = key.replace('_', '-')
        if key in self.res.headers:
            return self.res.headers[key]

    @property
    def content(self):
        """get response content"""
        return self.res.text

    @lazy_attr
    def contentType(self):
        """Get Content type"""
        value = self.getHeader('content-type')
        c = value.split(';')
        return c[0]

    @lazy_attr
    def charset(self):
        """Get http chaset encoding"""
        value = self.getHeader('content-type')
        c = value.split(';')
        if len(c) == 2:
            return c[1].split('=')[1]
        else:
            return "utf-8"

    @property
    def status(self):
        """Http status code"""
        return self.res.status_code
