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

from starboard.database import Star, Starboard, goc_member, goc_message

if TYPE_CHECKING:
    from starboard.bot import Bot


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
        .where(Starboard.star_emojis.any.eq(emoji_str))
        .fetchmany()
    )


async def handle_reaction_add(event: hikari.GuildReactionAddEvent) -> None:
    bot = cast("Bot", event.app)

    emoji_str = await _get_emoji_str_from_event(event)
    starboards = await _get_starboards_for_emoji(emoji_str, event.guild_id)
    if len(starboards) == 0:
        return

    # create users & members if necessary
    message = await bot.ccache.get_message(event.channel_id, event.message_id)
    if message is None:
        return

    # data for the person who reacted
    await goc_member(
        event.guild_id,
        event.member.id,
        event.member.is_bot,
    )

    # data for the message and its author
    await goc_message(
        event.guild_id,
        event.channel_id,
        message.id,
        message.author.id,
        message.author.is_bot,
    )

    # create a "star" for each starboard
    for s in starboards:
        if not await Star.exists(
            message_id=message.id,
            starboard_id=s.channel_id.v,
            user_id=event.user_id,
        ):
            await Star(
                message_id=message.id,
                starboard_id=s.channel_id.v,
                user_id=event.user_id,
            ).create()


async def handle_reaction_remove(
    event: hikari.GuildReactionDeleteEvent,
) -> None:
    emoji_str = await _get_emoji_str_from_event(event)
    starboards = await _get_starboards_for_emoji(emoji_str, event.guild_id)
    sbids = [sb.channel_id.v for sb in starboards]

    (
        await Star.delete_query()
        .where(message_id=event.message_id)
        .where(user_id=event.user_id)
        .where(starboard_id=apgorm.sql(sbids).any)
        .execute()
    )
