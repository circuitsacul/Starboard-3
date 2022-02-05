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

from typing import Callable, Union

import emoji
from apgorm.exceptions import InvalidFieldValue


def str_length(name: str, max: int) -> Callable[[Union[str, None]], bool]:
    def check(value: str | None) -> bool:
        if value and len(value) > max:
            raise InvalidFieldValue(
                f"`{name}` cannot be longer than {max} characters."
            )

        return True

    return check


def int_range(
    name: str, max: int | None = None, min: int | None = None
) -> Callable[[Union[int, None]], bool]:
    def check(value: int | None) -> bool:
        if value is not None:
            if max is not None and value > max:
                raise InvalidFieldValue(
                    f"`{name}` cannot be greater than {max}."
                )
            if min is not None and value < min:
                raise InvalidFieldValue(f"`{name}` cannot be less than {min}.")

        return True

    return check


def valid_emoji(value: str | None) -> bool:
    if value is not None and not emoji.is_emoji(value):  # type: ignore
        raise InvalidFieldValue(f"{value} is not a valid emoji.")

    return True
