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

from .errors import TokenizerException


class TokenType(object):
    """Token Type Enum"""

    Comment = 1
    """Comment Type"""

    Key = 2
    """Key Type"""

    LiteralValue = 3
    """Literal Value"""

    Operation = 4
    """Operation Value"""

    ObjectStart = 5
    """The object start type"""

    ObjectEnd = 6
    """The object end type"""

    Dot = 7
    """Dot Type"""

    EoF = 8
    """EoF Type"""

    ArrayStart = 9
    """The start of array"""

    ArrayEnd = 10
    """The end of array"""

    Comma = 11
    """The end of array"""

    MethodNameStart = 12
    """The test case method name start type"""

    MethodNameEnd = 13
    """The test case method name end type"""

    HttpMethodStart = 14
    """The http method section start type"""

    ImportStart = 15
    """Import start type"""

    ImportEnd = 16
    """Import end type"""

    CallStart = 17
    """Call start type"""

    CallEnd = 18
    """Call end type"""


class Token(object):
    """Token object

    :param tokenType: the token type
    :type tokenType: string
    :param sourceIndex: the  begin source index
    :type sourceIndex: int
    :param length: the length of token
    :type length: the length of token
    :param value: the value of token, defaults to None
    :type value: string, optional
    """

    def __init__(self, tokenType, sourceIndex, length, value=None):
        self.sourceIndex = sourceIndex
        self.length = length
        self.value = value
        self.tokenType = tokenType

    def __str__(self):
        return """Token<value:{}, type:{}>""".format(self.value, self.tokenType)

    __unicode__ = __str__

    @staticmethod
    def Key(key, sourceIndex, sourceLength, isQuoted):
        """Create Key Token

        :param sourceIndex: the  begin source index
        :type sourceIndex: int
        :param length: the length of token
        :type length: the length of token
        """
        return KeyToken(sourceIndex, sourceLength, key, isQuoted)

    @staticmethod
    def LiteralValue(value, sourceIndex, sourceLength, isQuoted):
        """Create Literal Value Token

        :param sourceIndex: the  begin source index
        :type sourceIndex: int
        :param length: the length of token
        :type length: the length of token
        :param isQuoted:  the value is quoted if true
        :type value: boolean
        """
        return LiteralValue(sourceIndex, sourceLength, value, isQuoted)


class LiteralValue(Token):
    """LiteralValue

    :param isQuoted:  the value is quoted if true
    :type value: boolean
    """

    def __init__(self, sourceIndex, length, value=None, isQuoted=False):
        super(LiteralValue, self).__init__(TokenType.LiteralValue, sourceIndex, length, value)
        self.isQuoted = isQuoted


class KeyToken(Token):
    """key token

    :param isQuoted:  the value is quoted if true
    :type value: boolean
    """

    def __init__(self, sourceIndex, length, value=None, isQuoted=False):
        super(KeyToken, self).__init__(TokenType.Key, sourceIndex, length, value)
        self.isQuoted = isQuoted


class Tokenizer(object):
    """The Base Hocon Tokenizer"""

    def __init__(self, text, pystyle=False):
            #: the current node text
        self._text = text
        #: the begin index
        self._index = 0
        #: the index stack
        self._indexStack = []
        #: the value covert style
        self.pystyle = pystyle

    @property
    def length(self):
        return len(self._text)

    @property
    def index(self):
        return self._index

    def push(self):
        self._indexStack.append(self._index)

    def pop(self):
        self._indexStack.pop()

    @property
    def eof(self):
        """End of file"""
        return self._index >= len(self._text)

    def match(self, pattern):
        """Match the pattern returns ``True``"""
        if (len(pattern) + self._index) > len(self._text):
            return False
        end = self._index + len(pattern)
        if self._text[self._index:end] == pattern:
            return True
        return False

    def matches(self, *patterns):
        """Match all patterns returns ``True``"""
        for pattern in patterns:
            m = self.match(pattern)
            if m:
                return True
        return False

    def take(self, length):
        """Get the head  length text """
        if(self._index + length) > len(self._text):
            return None
        end = self._index + length
        s = self._text[self._index:end]
        self._index += length
        return s

    def peek(self):
        """Peek the head char if not end"""
        if self.eof:
            return chr(0)

        return self._text[self._index]

    def takeOne(self):
        """Take the head one length char string"""
        if self.eof:
            return chr(0)
        index = self._index
        self._index += 1
        return self._text[index]

    def pullWhitespace(self):
        """Pull white space"""
        while (not self.eof) and self.peek().isspace():
            self.takeOne()

    def getHelpTextAtIndex(self, index, length=0):
        """Get the help text at index"""
        if length == 0:
            length = self.length - index
        l = min(20, length)
        end = l + index
        snippet = self._text[index:end]
        if length > 1:
            return snippet + "..."
        snippet = snippet.replace("\r", "\\r").replace("\n", "\\n")
        return str.format("at index {0}: `{1}`", index, snippet)


class NomosTokenizer(Tokenizer):
    """The  Nomas Tokenizer"""

    NotInUnquotedKey = "\"{}[]:=,#`^?*&\\"
    NotInUnquotedText = "\"{}[]:=,#`^?*&\\"

    def pullWhitespaceAndComments(self):
        """Pull whitespace and comments"""
        while True:
            self.pullWhitespace()
            while self.isStartOfComment():
                self.pullComment()
            if not self.isWhitesplace():
                break

    def pullRestOfLine(self):
        """Pull the rest of the current line"""
        sb = ""
        while not self.eof:
            c = self.takeOne()
            if c == '\n':
                break
            if c == '\r':
                continue
            sb += c
        return sb.strip()

    def pullUtilMatch(self, key):
        """Pull the rest of the current line"""
        sb = ""
        length = len(key)
        while not self.eof:
            c = self.take(length)
            if c is None:
                raise TokenizerException(str.format(
                    "Expected end for math until {0}", key))
            if c == key:
                break
            sb += c
        return sb.strip()

    def pullNext(self):
        """Pull the next token section"""
        self.pullWhitespaceAndComments()
        start = self.index

        if self.isMethodNameStart():
            return self.pullMethodNameStart()

        if self.isMethodNameEnd():
            return self.pullMethodNameEnd()

        if self.isHttpMethodStart():
            return self.pullHttpMethodStart()

        callType = self.isCallStart()
        if callType:
            return self.pullCall(callType)

        if self.isImportStart():
            return self.pullImportStart()

        length = self.isOperation()
        if length > 0:
            return self.pullOperation(length)

        if self.isObjectStart():
            return self.pullStartObject()
        if self.isObjectEnd():
            return self.pullObjectEnd()

        if self.isStartOfQuotedKey():
            return self.pullQuotedKey()

        if self.isUnquotedKeyStart():
            return self.pullUnquotedKey()

        if self.isArrayStart():
            return self.pullArrayStart()

        if self.isArrayEnd():
            return self.pullArrayEnd()

        if self.eof:
            return Token(TokenType.EoF, self.index, 0)

        raise TokenizerException(str.format(
            "Unknown token: {0}", self.getHelpTextAtIndex(start)))

    def isOperation(self):
        boolean = self.matches(">=", "=~", "<-", "~~", "==", "<=", "!=", "<<")
        if boolean:
            return 2
        boolean = self.matches("=", ":", "<", ">")
        if boolean:
            return 1
        return 0

    def isCallStart(self):
        """Check is the start of substitution"""
        if self.match("${"):
            return "$"
        if self.match("@{"):
            return "@"
        return ""

    def pullCall(self, callType):
        """Pull substitution token"""
        start = self.index
        sb = ''
        self.take(2)
        while (not self.eof) and self.peek() != "}":
            sb += self.takeOne()

        self.takeOne()
        return LiteralValue(start, self.index - start, callType + sb.strip(), False)

    def pullHttpMethodAndPath(self):
        self.takeOne()
        method = self.pullNext()
        path = self.pullNext()

        return (method, path)

    def isHttpMethodStart(self):
        return self.match(">>")

    def pullHttpMethodStart(self):
        start = self.index
        self.takeOne()
        return Token(TokenType.HttpMethodStart, self.index, self.index - start)

    def pullImportStart(self):
        start = self.index
        self.take(2)
        return Token(TokenType.ImportStart, self.index, self.index - start)

    def pullImportEnd(self):
        start = self.index
        self.take(2)
        return Token(TokenType.ImportEnd, self.index, self.index - start)

    def isMethodNameStart(self):
        return self.match("[")

    def isMethodNameEnd(self):
        return self.match("]")

    def isImportStart(self):
        return self.match("<%")

    def isImportEnd(self):
        return self.match("%>")

    def pullMethodNameEnd(self):
        start = self.index
        self.takeOne()
        return Token(TokenType.MethodNameEnd, self.index, self.index - start)

    def pullMethodNameStart(self):
        start = self.index
        self.takeOne()
        return Token(TokenType.MethodNameStart, self.index, self.index - start)

    def isStartOfQuotedKey(self):
        """Check is start of quoted key"""
        return self.match("\"")

    def isStartTripQuotedText(self):
        """Check is the start of trip quoted text"""
        return self.match("\"\"\"")

    def pullArrayEnd(self):
        """Pull the end of array"""
        start = self.index
        if not self.isArrayEnd():
            raise TokenizerException(str.format(
                "Expected end of array {0}", self.getHelpTextAtIndex(start)))
        self.takeOne()
        return Token(TokenType.ArrayEnd, start, self.index - start)

    def isArrayEnd(self):
        """Check is the end of array"""
        return self.match("]")

    def isArrayStart(self):
        """Check is the begin of array"""
        return self.match("[")

    def pullArrayStart(self):
        """Pull the begin of array"""
        start = self.index
        self.takeOne()
        return Token(TokenType.ArrayStart, self.index, self.index - start)

    def pullDot(self):
        """Pull dot"""
        start = self.index
        self.takeOne()
        return Token(TokenType.Dot, start, self.index - start)

    def pullComma(self):
        """Pull comma"""
        start = self.index
        self.takeOne()
        return Token(TokenType.Comma, start, self.index - start)

    def pullStartObject(self):
        """Pull  the start of the current object"""
        start = self.index
        self.takeOne()
        return Token(TokenType.ObjectStart, start, self.index - start)

    def pullObjectEnd(self):
        """Pull  the end of the current object"""
        start = self.index
        if not self.isObjectEnd():
            raise TokenizerException(str.format(
                "Expected end of object {0}", self.getHelpTextAtIndex(self.index)))
        self.takeOne()
        return Token(TokenType.ObjectEnd, start, self.index - start)

    def pullOperation(self, length):
        """Pull  assignment (=or : ) """
        start = self.index
        value = self.take(length)
        return Token(TokenType.Operation, start, self.index - start, value)

    def isComma(self):
        """Check is comma"""
        return self.match(",")

    def isDot(self):
        """Check is dot(.)"""
        return self.match(".")

    def isObjectStart(self):
        """Check is the start of object"""
        return self.match("{")

    def isObjectEnd(self):
        """Check is the end of object"""
        return self.match("}")

    def isStartQuotedText(self):
        """Check is the start of  quoted text"""
        return self.match("\"")

    def pullComment(self):
        """Pull the comment"""
        start = self.index
        self.pullRestOfLine()
        return Token(TokenType.Comment, start, self.index - start)

    def pullUnquotedKey(self):
        """Pull unquoted key"""
        start = self.index
        sb = ""
        while (not self.eof) and self.isUnquotedKey() and (not self.isWhitesplace()):
            sb += self.takeOne()
        return Token.Key(sb.strip(), start, self.index - start, False)

    def isUnquotedKey(self):
        """Check is the  unquoted key"""
        return (not self.eof) and (not self.isStartOfComment()) and \
            (self.peek() not in self.NotInUnquotedKey)

    def isUnquotedKeyStart(self):
        """Check is the start of unquoted key"""
        return (not self.eof) and (not self.isWhitesplace()) and \
            (not self.isStartOfComment()) and (self.peek() not in self.NotInUnquotedKey)

    def isWhitesplace(self):
        """Check is blank"""
        return self.peek().isspace()

    def isWhitesplaceOrComment(self):
        """Check is blank or comment"""
        return self.isWhitesplace() or self.isStartOfComment()

    def pullTripQuotedText(self):
        """Pull the trip quoted text"""
        start = self.index
        sb = ''
        self.take(3)
        while (not self.eof) and (not self.match("\"\"\"")):
            if self.match("\\"):
                sb += self.pullEscapeSequence()
            else:
                sb += self.takeOne()

        if self.match("\""):
            raise TokenizerException(str.format(
                "Expected end of tripple quoted string {0}", self.getHelpTextAtIndex(self.index)))

        self.take(3)
        return Token.LiteralValue(sb, start, self.index - start, True)

    def pullQuotedText(self):
        """Pull the quoted text"""
        start = self.index
        sb = ''
        self.takeOne()
        while (not self.eof) and not self.match("\""):
            if self.match("\\"):
                sb += self.pullEscapeSequence()
            else:
                sb += self.takeOne()

        self.takeOne()
        return Token.LiteralValue(sb, start, self.index - start, True)

    def pullQuotedKey(self):
        """Pull the quoted key"""
        start = self.index
        sb = ''
        self.take(3)
        while (not self.eof) and (not self.match("\"")):
            if self.match("\\"):
                sb += self.pullEscapeSequence()
            else:
                sb += self.takeOne()

        self.takeOne()
        return Token.Key(sb, start, self.index - start, True)

    def pullEscapeSequence(self):
        """Pull the escape squence"""
        start = self.index

        escaped = self.takeOne()
        if escaped == '"':
            return "\""
        if escaped == '\\':
            return "\\"
        if escaped == '/':
            return "/"
        if escaped == 'b':
            return "\b"
        if escaped == 'f':
            return "\f"
        if escaped == 'n':
            return "\n"
        if escaped == 'r':
            return "\r"
        if escaped == 't':
            return "\t"
        if escaped == 'u':
            hexStr = "0x" + self.take(4)
            j = hex(hexStr)
            return chr(j)
        raise TokenizerException(str.format(
            "Unknown escape code `{0}` {1}", escaped, self.getHelpTextAtIndex(start)))

    def isStartOfComment(self):
        """Is the start of comment(  # or //)"""
        return self.matches("#", "//")

    def isStartResource(self):
        """Is the start of comment(  # or //)"""
        return self.match("@")

    def pullValue(self):
        """Pull the value, returns the token"""

        start = self.index

        if self.isArrayStart():
            return self.pullArrayStart()
        if self.isArrayEnd():
            return self.pullArrayEnd()

        if self.isObjectStart():
            return self.pullStartObject()

        if self.isStartTripQuotedText():
            return self.pullTripQuotedText()

        if self.isStartQuotedText():
            return self.pullQuotedText()

        callType = self.isCallStart()
        if callType:
            return self.pullCall(callType)

        if self.isUnquotedText():
            return self.pullUnquotedText()

        raise TokenizerException(str.format(
            "Expected value: Null literal, Array, Quoted Text, Unquoted Text, Triple quoted Text, Object or End of array {0}",
            self.getHelpTextAtIndex(start)))

    def isSpaceOrTab(self):
        """Check is  blank context"""
        return self.matches(" ", "\t", "\v")

    def isStartSimpleValue(self):
        """Check is the begin of simaple value"""
        if self.isSpaceOrTab():
            return True

        if self.isUnquotedText():
            return True

        return False

    def pullSpaceOrTab(self):
        """Pull black text"""
        start = self.index
        sb = ''
        while self.isSpaceOrTab():
            sb += self.takeOne()

        return Token.LiteralValue(sb, start, self.index - start, False)

    def pullUnquotedText(self):
        """Pull unquotes text"""
        start = self.index
        value = ''
        while (not self.eof) and self.isUnquotedText() and (not self.isWhitesplace()):
            value += self.takeOne()

        if self.pystyle:
            value = self.convertToPyValue(value)

        return Token.LiteralValue(value, start, self.index - start, False)

    FLOAT_VAR = re.compile(r'^-?\d+\.\d+$')
    INT_VAR = re.compile(r'^-?\d+$')
    BOOL_VAR = {'true': True, 'false': False, 'on': True, 'off': False}

    def convertToPyValue(self, value):
        """Convet to python value"""
        if value in self.BOOL_VAR:
            return self.BOOL_VAR[value]

        if self.INT_VAR.match(value):
            # it will auto cast to long if too large
            return int(value)

        if self.FLOAT_VAR.match(value):
            return float(value)

        return value

    def isUnquotedText(self):
        """Check is a is unquoted text"""
        return (not self.eof) and (not self.isWhitesplace()) and \
            (not self.isStartOfComment()) and (self.peek() not in self.NotInUnquotedText)

    def pullSimpleValue(self):
        """Get the simplate string or space value"""
        start = self.index

        if self.isSpaceOrTab():
            return self.pullSpaceOrTab()
        if self.isUnquotedText():
            return self.pullUnquotedText()

        raise TokenizerException(str.format(
            "No simple value found {0}", self.getHelpTextAtIndex(start)))

    def isValue(self):
        """Check the current token is a value"""

        if self.isArrayStart():
            return True
        if self.isObjectStart():
            return True
        if self.isStartTripQuotedText():
            return True
        if self.isStartQuotedText():
            return True
        if self.isUnquotedText():
            return True

        return False
