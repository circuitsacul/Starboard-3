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

import datetime
import re
from typing import TYPE_CHECKING, Callable, Iterable, cast

import humanize
from hikari import UNDEFINED, Message, MessageType

from .exceptions import StarboardErr

if TYPE_CHECKING:
    from starboard.bot import Bot


def jump(guild: int, channel: int, message: int) -> str:
    return f"https://discord.com/channels/{guild}/{channel}/{message}"


def rendered_content(msg: Message) -> str | None:
    bot = cast("Bot", msg.app)
    if msg.type in {
        MessageType.DEFAULT,
        MessageType.REPLY,
        MessageType.CHAT_INPUT,
        MessageType.CONTEXT_MENU_COMMAND,
    }:
        return msg.content

    if msg.type is MessageType.RECIPIENT_ADD:
        # NOTE: fails to handle DM Groups
        assert msg.mentions.users is not UNDEFINED
        target = next(iter(msg.mentions.users.values()))
        return f"{msg.author.username} added {target.username} to the thread."

    if msg.type is MessageType.RECIPIENT_REMOVE:
        # NOTE: fails to handle DM Groups
        assert msg.mentions.users is not UNDEFINED
        target = next(iter(msg.mentions.users.values()))
        return (
            f"{msg.author.username} removed {target.username} from the thread."
        )

    if msg.type is MessageType.CHANNEL_NAME_CHANGE:
        return (
            f"{msg.author.username} changed the channel name: "
            f"**{msg.content}**"
        )

    if msg.type is MessageType.CHANNEL_ICON_CHANGE:
        return f"{msg.author.username} changed the channel icon."

    if msg.type is MessageType.CHANNEL_PINNED_MESSAGE:
        return f"{msg.author.username} pinned a message to this channel."

    if msg.type is MessageType.GUILD_MEMBER_JOIN:
        formats = [
            "{0} joined the party.",
            "{0} is here.",
            "Welcome, {0}. We hope you brought pizza.",
            "A wild {0} appeared.",
            "{0} just landed.",
            "{0} just slid into the server.",
            "{0} just showed up!",
            "Welcome {0}. Say hi!",
            "{0} hopped into the server.",
            "Everyone welcome {0}!",
            "Glad you're here, {0}.",
            "Good to see you, {0}.",
            "Yay you made it, {0}!",
        ]

        created_at_ms = int(msg.created_at.timestamp() * 1000)
        return formats[created_at_ms % len(formats)].format(
            msg.author.username
        )

    if msg.type is MessageType.USER_PREMIUM_GUILD_SUBSCRIPTION:
        if msg.content:
            return (
                f"{msg.author.username} just boosted the server "
                f"**{msg.content}** times!"
            )
        return f"{msg.author.username} just boosted the server!"

    if msg.type is MessageType.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1:
        assert msg.guild_id
        guild = bot.cache.get_guild(msg.guild_id)
        assert guild
        if msg.content:
            return (
                f"{msg.author.username} just boosted the server "
                f"**{msg.content}** times! {guild} has achieved **Level 1!**"
            )
        return (
            f"{msg.author.username} just boosted the server! {guild} has "
            "achieved **Level 1!**"
        )

    if msg.type is MessageType.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2:
        assert msg.guild_id
        guild = bot.cache.get_guild(msg.guild_id)
        assert guild
        if msg.content:
            return (
                f"{msg.author.username} just boosted the server "
                f"**{msg.content}** times! {guild} has achieved **Level 2!**"
            )
        return (
            f"{msg.author.username} just boosted the server! {guild} has "
            "achieved **Level 2!**"
        )

    if msg.type is MessageType.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3:
        assert msg.guild_id
        guild = bot.cache.get_guild(msg.guild_id)
        assert guild
        if msg.content:
            return (
                f"{msg.author.username} just boosted the server "
                f"**{msg.content}** times! {guild} has achieved **Level 3!**"
            )
        return (
            f"{msg.author.username} just boosted the server! {guild} has "
            "achieved **Level 3!**"
        )

    if msg.type is MessageType.CHANNEL_FOLLOW_ADD:
        return f"{msg.author.username} has added {msg.content} to this channel"

    # if msg.type is MessageType.guild_stream:
    #     # the author will be a Member
    #     return f'{msg.author.name} is live! Now streaming
    # {msg.author.activity.name}'  # type: ignore

    if msg.type is MessageType.GUILD_DISCOVERY_DISQUALIFIED:
        return (
            "This server has been removed from Server Discovery because it no "
            "longer passes all the requirements. Check Server Settings for "
            "more details."
        )

    if msg.type is MessageType.GUILD_DISCOVERY_REQUALIFIED:
        return (
            "This server is eligible for Server Discovery again and has been "
            "automatically relisted!"
        )

    if msg.type is MessageType.GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING:
        return (
            "This server has failed Discovery activity requirements for 1 "
            "week. If this server fails for 4 weeks in a row, it will be "
            "automatically removed from Discovery."
        )

    if msg.type is MessageType.GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING:
        return (
            "This server has failed Discovery activity requirements for 3 "
            "weeks in a row. If this server fails for 1 more week, it will be "
            "removed from Discovery."
        )

    # if msg.type is MessageType.thread_created:
    #     return f'{msg.author.name} started a thread: **{msg.content}**. See
    # all **threads**.'

    # if msg.type is MessageType.thread_starter_message:
    #     if msg.reference is None or msg.reference.resolved is None:
    #         return 'Sorry, we couldn\'t load the first message in this
    # thread'

    #     # the resolved message for the reference will be a Message
    #     return msg.reference.resolved.content  # type: ignore

    if msg.type is MessageType.GUILD_INVITE_REMINDER:
        return (
            "Wondering who to invite?\nStart by inviting anyone who can help "
            "you build the server!"
        )

    print(f"WARNING: Uncaught type {msg.type}")
    return msg.content


def truncate(text: str, max: int, ddd: str = "...") -> str:
    if len(text) <= max:
        return text

    to_remove = len(text) + len(ddd) - max
    return text[:-to_remove] + ddd


def _default_ddd(count: int) -> str:
    if count == 1:
        return "\nand 1 other"
    return f"\nand {count} others"


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


def paginate(text: str, max: int) -> Iterable[str]:
    while True:
        yield (yielded := truncate(text, max, ddd=""))
        if len(yielded) < len(text):
            text = text[len(yielded) :]
        else:
            break


def seconds_to_human(seconds: int) -> str:
    return cast(
        str, humanize.precisedelta(datetime.timedelta(seconds=seconds))
    )


DELTA_UNITS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
    "mo": 60 * 60 * 24 * 30,
    "y": 60 * 60 * 24 * 365,
}


UNIT_CONVERSION = {
    "second": "s",
    "minute": "m",
    "hour": "h",
    "day": "d",
    "week": "w",
    "month": "mo",
    "year": "y",
}


def _normalize_unit(unit: str) -> str:
    unit = unit.strip()
    _unit = unit.rstrip("s")
    return UNIT_CONVERSION.get(_unit, unit)


TOKEN_RE = re.compile(r"^(?P<value>\d+)(?P<unit>\w+)$")


def human_to_seconds(human: str) -> int:
    space_split_tokens = human.split(" ")
    seconds: int = 0

    carry: str | None = None
    for token in space_split_tokens:
        if carry:
            token = f"{carry}{token}"
            carry = None

        if token.isdigit():
            carry = token
            continue

        match = TOKEN_RE.match(token)
        if not match:
            raise StarboardErr(
                f"I couldn't interpret {token} as a unit of time."
            )

        value = int(match.group("value"))
        unit = _normalize_unit(match.group("unit"))
        conversion_unit = DELTA_UNITS.get(unit)
        if conversion_unit is None:
            raise StarboardErr(f"I don't know what `{unit}` is.")

        seconds += value * conversion_unit

    return seconds
