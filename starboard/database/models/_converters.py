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

from typing import Generic, TypeVar

from decimal import Decimal
from typing import Sequence

import apgorm


class NullDecimalC(apgorm.Converter["Decimal | None", "int | None"]):
    def from_stored(self, value: Decimal | None) -> int | None:
        if value is None:
            return value
        return int(value)

    def to_stored(self, value: int | None) -> Decimal | None:
        if value is None:
            return value
        return Decimal(value)


class DecimalC(apgorm.Converter[Decimal, int]):
    def from_stored(self, value: Decimal) -> int:
        return int(value)

    def to_stored(self, value: int) -> Decimal:
        return Decimal(value)


class DecimalArrayC(
    apgorm.Converter["Sequence[Decimal | None]", "Sequence[int]"]
):
    def from_stored(self, value: Sequence[Decimal | None]) -> Sequence[int]:
        return [int(v) for v in value if v is not None]

    def to_stored(self, value: Sequence[int]) -> Sequence[Decimal | None]:
        return [Decimal(v) for v in value]


_T = TypeVar("_T")


class NonNullArray(
    apgorm.Converter["Sequence[_T | None]", "Sequence[_T]"], Generic[_T]
):
    def __init__(self, t: type[_T]) -> None:
        pass

    def from_stored(self, value: Sequence[_T | None]) -> Sequence[_T]:
        return [v for v in value if v is not None]

    def to_stored(self, value: Sequence[_T]) -> Sequence[_T]:
        return value
