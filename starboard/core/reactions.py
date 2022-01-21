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

from typing import TYPE_CHECKING, cast

import apgorm
import hikari

from starboard.database import Starboard, goc_member, goc_message

from .starboards import get_orig_message, refresh_message
from .stars import add_stars, remove_stars

if TYPE_CHECKING:
    from starboard.bot import Bot


async def handle_reaction_add(event: hikari.GuildReactionAddEvent) -> None:
    if event.member.is_bot:
        return
    bot = cast("Bot", event.app)

    orig_msg = await get_orig_message(event.message_id)
    if orig_msg is None:
        _m = await bot.cache.gof_message(event.channel_id, event.message_id)
        if not _m:
            return
        channel = await bot.cache.gof_guild_channel_wnsfw(event.channel_id)
        if not channel:
            return
        assert channel.is_nsfw is not None

        orig_msg = await goc_message(
            event.guild_id,
            event.channel_id,
            event.message_id,
            channel.is_nsfw,
            _m.author.id,
            _m.author.is_bot,
        )

    emoji_str = await _get_emoji_str_from_event(event)
    starboards = await _get_starboards_for_emoji(emoji_str, event.guild_id)
    if len(starboards) == 0:
        return

    # data for the person who reacted
    await goc_member(
        event.guild_id,
        event.member.id,
        event.member.is_bot,
    )

    # create a "star" for each starboard
    await add_stars(
        orig_msg.id.v,
        event.user_id,
        [s.id.v for s in starboards],
    )

    await refresh_message(cast("Bot", event.app), orig_msg)


async def handle_reaction_remove(
    event: hikari.GuildReactionDeleteEvent,
) -> None:
    orig_msg = await get_orig_message(event.message_id)
    if not orig_msg:
        return

    emoji_str = await _get_emoji_str_from_event(event)
    starboards = await _get_starboards_for_emoji(emoji_str, event.guild_id)

    if len(starboards) == 0:
        return

    await remove_stars(
        orig_msg.id.v,
        event.user_id,
        [sb.id.v for sb in starboards],
    )

    await refresh_message(cast("Bot", event.app), orig_msg)


async def _get_emoji_str_from_event(
    event: hikari.GuildReactionDeleteEvent | hikari.GuildReactionAddEvent,
) -> str:
    if event.emoji_id is not None:
        return str(
            (
                await event.app.rest.fetch_emoji(
                    event.guild_id, event.emoji_id
                )
            ).id
        )
    else:
        assert isinstance(event.emoji_name, hikari.UnicodeEmoji)
        return str(event.emoji_name)


async def _get_starboards_for_emoji(
    emoji_str: str,
    guild_id: int,
) -> apgorm.LazyList[dict, Starboard]:
    return (
        await Starboard.fetch_query()
        .where(guild_id=guild_id)
        .where(apgorm.sql(emoji_str).eq(Starboard.star_emojis.any))
        .fetchmany()
    )
