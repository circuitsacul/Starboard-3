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
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar, overload

import emoji
import hikari

from starboard.core.messages import get_orig_message
from starboard.exceptions import MessageNotFound, StarboardError
from starboard.undefined import UNDEF

if TYPE_CHECKING:
    from starboard.bot import Bot
    from starboard.database import Message

_T = TypeVar("_T")
_N = TypeVar("_N")


def convert(key: str, dct: dict[str, Any], func: Callable[[Any], Any]) -> None:
    if key in dct and (v := dct[key]) is not UNDEF.UNDEF:
        dct[key] = func(v)


def clean_name(text: str) -> str:
    text = text.lower().casefold().strip().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c in "-_")


def any_emoji_str(text: str) -> str:
    with suppress(ValueError):
        return str(hikari.CustomEmoji.parse(text).id)

    uc = str(hikari.UnicodeEmoji.parse(text))
    if not emoji.is_emoji(uc):
        raise StarboardError(f"'{uc}' is not a valid emoji.")

    return uc


def any_emoji_list(text: str) -> list[str]:
    unique: set[str] = set()
    ret: list[str] = list()
    for piece in text.split(" "):
        with suppress(StarboardError):
            emoji = any_emoji_str(piece)
            if emoji in unique:
                continue
            unique.add(emoji)
            ret.append(emoji)

    return ret


def hex_color(text: str) -> int:
    try:
        return int(text.replace("#", ""), base=16)
    except ValueError:
        raise StarboardError(f"'{text}' is not a valid hex color.") from None


def disid(text: Any) -> int:
    try:
        return int(text)
    except (ValueError, TypeError):
        raise StarboardError(f"'{str(text)}' is not a valid ID.") from None


@overload
def none_or(
    func: Callable[[str], _T], noneval: None = ..., nonefirst: bool = ...
) -> Callable[[str], _T | None]:
    ...


@overload
def none_or(
    func: Callable[[str], _T], noneval: _N, nonefirst: bool = ...
) -> Callable[[str], _T | _N]:
    ...


def none_or(
    func: Callable[[str], _T],
    noneval: _N | None = None,
    nonefirst: bool = True,
) -> Callable[[str], _T | _N | None]:
    def wrapper(text: str) -> _T | _N | None:
        if nonefirst and text.lower() in {"none", "default"}:
            return noneval
        try:
            return func(text)
        except Exception as e:
            if not nonefirst and text.lower() in {"none", "default"}:
                return noneval
            raise e

    return wrapper


def none_or_str(text: str) -> None | str:
    return None if text.lower() in {"none", "default"} else text


QUICK_ID = re.compile(r"(?P<message_id>[0-9]+)-(?P<channel_id>[0-9]+)$")
MSG_LINK = re.compile(
    r"^https://discord(app)?.com/channels/[0-9]+/(?P<channel_id>[0-9]+)/"
    r"(?P<message_id>[0-9]+)$"
)


def msg_ch_id(text: str) -> tuple[int, int]:
    if (m := MSG_LINK.match(text)) is not None:
        return int(m["message_id"]), int(m["channel_id"])
    if (m := QUICK_ID.match(text)) is not None:
        return int(m["message_id"]), int(m["channel_id"])

    raise StarboardError(f"`{text}` is not a valid message link.")


def message_id(text: str) -> int:
    with suppress(ValueError):
        return int(text)

    with suppress(StarboardError):
        return msg_ch_id(text)[0]

    raise StarboardError(f"`{text}` is not a valid message link or id.")


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


def validate_channels(
    channels: list[int], bot: Bot, categories: bool = False
) -> _ValidChannels:
    v: set[int] = set()
    iv: set[int] = set()
    for id in channels:
        if c := bot.cache.get_guild_channel(id):
            if isinstance(c, hikari.TextableGuildChannel):
                v.add(id)
                continue
            if categories and isinstance(c, hikari.GuildCategory):
                v.add(id)
                continue

        iv.add(id)

    return _ValidChannels(v, iv)


NUM = re.compile(r"(?P<id>[0-9]+)")


def channel_list(
    text: str, bot: Bot, categories: bool = False
) -> _ValidChannels:
    return validate_channels(
        [int(c["id"]) for c in NUM.finditer(text)], bot, categories
    )
