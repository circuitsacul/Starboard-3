# MIT License
#
# Copyright (c) 2022 TrigonDev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations


class StarboardError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg
        super().__init__(msg)


class StarboardNotFound(StarboardError):
    def __init__(self, name: str) -> None:
        self.inp = name
        super().__init__(f"No starboard found with the name '{name}'.")


class ASCNotFound(StarboardError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No autostar channel found with name '{name}'.")


class OverrideNotFound(StarboardError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No override with the name '{name}' exists.")


class MessageNotFound(StarboardError):
    def __init__(self, mid: int) -> None:
        self.mid = mid
        super().__init__(
            f"No message with the id `{mid}` was found in the database. "
            "Either the ID is invalid, or this message just hasn't received "
            "any votes yet."
        )
