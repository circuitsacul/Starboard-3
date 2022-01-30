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

from typing import Any, Callable

import emoji
import hikari
import tanjun


def any_emoji(text: str) -> hikari.CustomEmoji | hikari.UnicodeEmoji:
    try:
        return hikari.CustomEmoji.parse(text)
    except ValueError:
        pass

    e = hikari.UnicodeEmoji.parse(text)
    if emoji.is_emoji(e):  # type: ignore
        return e

    raise tanjun.CommandError(f"'{e}' is not a valid emoji.")


def any_emoji_str(text: str) -> str:
    e = any_emoji(text)
    if isinstance(e, hikari.CustomEmoji):
        return str(e.id)
    return str(e)


def hex_color(text: str) -> int:
    try:
        return int(text.replace("#", ""), base=16)
    except ValueError:
        raise tanjun.CommandError(f"'{text}' is not a valid hex color.")


def none_or(
    func: Callable[[str], Any], nonefirst: bool = False
) -> Callable[[str], Any]:
    def wrapper(text: str) -> Any:
        if nonefirst and text.lower() in ["none", "default"]:
            return text
        try:
            return func(text)
        except Exception as e:
            if not nonefirst and text.lower() in ["none", "default"]:
                return None
            raise e

    return wrapper


def none_or_str(text: str) -> None | str:
    if text.lower() in ["none", "default"]:
        return None
    return text
