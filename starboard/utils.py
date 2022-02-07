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

from typing import Callable


def truncate(text: str, max: int, ddd: str = "...") -> str:
    if len(text) <= max:
        return text

    to_remove = len(text) + len(ddd) - max
    return text[:-to_remove] + ddd


def _default_ddd(count: int) -> str:
    if count == 1:
        return "\nand 1 other"
    return f"\nand {count} other"


def trunc_list(
    texts: list[str], max: int, ddd: Callable[[int], str] = _default_ddd
) -> list[str]:
    if sum(len(t) for t in texts) <= max:
        return texts

    texts = texts.copy()
    oklist: list[str] = []

    while (
        texts
        and sum(len(t) for t in oklist)
        + len(ddd(len(texts) - 1))
        + len(texts[0])
        <= max
    ):
        oklist.append(texts.pop(0))

    return oklist + [ddd(len(texts))]
