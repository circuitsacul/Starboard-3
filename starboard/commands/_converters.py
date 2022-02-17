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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import emoji
import hikari

from starboard.core.messages import get_orig_message
from starboard.exceptions import MessageNotFound, StarboardErr
from starboard.undefined import UNDEF

if TYPE_CHECKING:
    from starboard.bot import Bot
    from starboard.database import Message

_T = TypeVar("_T")


def convert(key: str, dct: dict[str, Any], func: Callable[[Any], Any]) -> None:
    if key in dct and (v := dct[key]) is not UNDEF.UNDEF:
        dct[key] = func(v)


def any_emoji_str(text: str) -> str:
    try:
        return str(hikari.CustomEmoji.parse(text).id)
    except ValueError:
        pass

    uc = str(hikari.UnicodeEmoji.parse(text))
    if not emoji.is_emoji(uc):  # type: ignore
        raise StarboardErr(f"'{uc}' is not a valid emoji.")

    return uc


def any_emoji_list(text: str) -> set[str]:
    ret: set[str] = set()
    for piece in text.split(" "):
        try:
            ret.add(any_emoji_str(piece))
        except StarboardErr:
            pass

    return ret


def hex_color(text: str) -> int:
    try:
        return int(text.replace("#", ""), base=16)
    except ValueError:
        raise StarboardErr(f"'{text}' is not a valid hex color.")


def disid(text: Any) -> int:
    try:
        return int(text)
    except (ValueError, TypeError):
        raise StarboardErr(f"'{str(text)}' is not a valid ID.")


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


def msg_ch_id(text: str) -> tuple[int, int]:
    if (m := MSG_LINK.match(text)) is not None:
        return int(m["message_id"]), int(m["channel_id"])
    if (m := QUICK_ID.match(text)) is not None:
        return int(m["message_id"]), int(m["channel_id"])

    raise StarboardErr(f"`{text}` is not a valid message link.")


def message_id(text: str) -> int:
    try:
        return int(text)
    except ValueError:
        pass

    try:
        return msg_ch_id(text)[0]
    except StarboardErr:
        pass

    raise StarboardErr(f"`{text}` is not a valid message link or id.")


async def orig_msg_from_link(text: str) -> Message:
    mid = message_id(text)
    msg = await get_orig_message(mid)
    if not msg:
        raise MessageNotFound(mid)

    return msg


@dataclass
class _ValidChannels:
    valid: set[int]
    invalid: set[int]


def validate_channels(channels: list[int], bot: Bot) -> _ValidChannels:
    v: set[int] = set()
    iv: set[int] = set()
    for id in channels:
        if c := bot.cache.get_guild_channel(id):
            if isinstance(c, hikari.TextableGuildChannel):
                v.add(id)
                continue

        iv.add(id)

    return _ValidChannels(v, iv)


NUM = re.compile(r"(?P<id>[0-9]+)")


def channel_list(text: str, bot: Bot) -> _ValidChannels:
    return validate_channels(
        list(int(c["id"]) for c in NUM.finditer(text)), bot
    )
