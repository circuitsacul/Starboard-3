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

from typing import Any, Callable, Optional, Sequence

import emoji
from apgorm.exceptions import InvalidFieldValue


def valid_emoji(value: str) -> bool:
    if value.isalnum() or emoji.is_emoji(value):  # type: ignore
        return True

    raise InvalidFieldValue(f"{value} is not a valid emoji.")


def str_len(name: str, min: int, max: int) -> Callable[[str], bool]:
    def validator(value: str | None) -> bool:
        if len(value or "") > max:
            raise InvalidFieldValue(
                f"The length of {name} cannot be greater than {max} "
                "characters."
            )
        elif len(value or "") < min:
            raise InvalidFieldValue(
                f"The length of {name} cannot be less than {min} "
                "characters."
            )

        return True

    return validator


def num_range(
    name: str, min: int | float | None, max: int | float | None
) -> Callable[[Optional[int | float]], bool]:
    def validator(value: int | float | None) -> bool:
        if value is None:
            return True
        if max is not None and value > max:
            raise InvalidFieldValue(f"{name} must be at most {max}.")
        if min is not None and value < min:
            raise InvalidFieldValue(f"{name} must be at least {min}.")

        return True

    return validator


def array_len(
    name: str, max: int
) -> Callable[[Optional[Sequence[Any]]], bool]:
    def validator(value: Sequence[Any] | None) -> bool:
        if value and len(value) > max:
            raise InvalidFieldValue(f"You can have up to {max} {name}.")

        return True

    return validator
