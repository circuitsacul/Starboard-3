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

import re
from typing import Any, Callable, TypeVar, TYPE_CHECKING

import hikari
from starboard.core.messages import get_orig_message

from starboard.exceptions import ConverterErr, MessageNotFound
from starboard.undefined import UNDEF

if TYPE_CHECKING:
    from starboard.database import Message

_T = TypeVar("_T")


def convert(key: str, dct: dict[str, Any], func: Callable[[Any], Any]) -> None:
    if key in dct and (v := dct[key]) is not UNDEF.UNDEF:
        dct[key] = func(v)


def any_emoji(text: str) -> hikari.CustomEmoji | hikari.UnicodeEmoji:
    try:
        return hikari.CustomEmoji.parse(text)
    except ValueError:
        pass

    return hikari.UnicodeEmoji.parse(text)


def any_emoji_str(text: str) -> str:
    e = any_emoji(text)
    if isinstance(e, hikari.CustomEmoji):
        return str(e.id)
    return str(e)


def hex_color(text: str) -> int:
    try:
        return int(text.replace("#", ""), base=16)
    except ValueError:
        raise ConverterErr(f"'{text}' is not a valid hex color.")


def none_or(
    func: Callable[[str], _T], nonefirst: bool = True
) -> Callable[[str], _T | None]:
    def wrapper(text: str) -> _T | None:
        if nonefirst and text.lower() in ["none", "default"]:
            return None
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


QUICK_ID = re.compile(r"(?P<message_id>[0-9]+)-(?P<channel_id>[0-9]+)$")
MSG_LINK = re.compile(
    r"^https:\/\/discord.com\/channels\/[0-9]+\/(?P<channel_id>[0-9]+)\/"
    r"(?P<message_id>[0-9]+)$"
)


def message_id(text: str) -> int:
    try:
        return int(text)
    except ValueError:
        pass
    if (m := MSG_LINK.match(text)) is not None:
        return int(m["message_id"])
    if (m := QUICK_ID.match(text)) is not None:
        return int(m["message_id"])

    raise ConverterErr(f"`{text}` is not a valid message link or id.")


async def db_orig_message(text: str) -> Message:
    mid = message_id(text)
    msg = await get_orig_message(mid)
    if not msg:
        raise MessageNotFound(mid)

    return msg
