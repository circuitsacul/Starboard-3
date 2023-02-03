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

import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING, cast

import hikari

from starboard.core.leaderboard import refresh_xp
from starboard.core.posrole import update_posroles
from starboard.core.xprole import refresh_xpr
from starboard.database import Guild, Member, Message, Starboard
from starboard.database.models.user import User

from .config import StarboardConfig, get_config
from .messages import get_orig_message
from .starboards import refresh_message
from .votes import add_votes, is_vote_valid_for, remove_votes

if TYPE_CHECKING:
    from starboard.bot import Bot


async def handle_reaction_add(event: hikari.GuildReactionAddEvent) -> None:
    if event.member.is_bot:
        return
    bot = cast("Bot", event.app)

    emoji_str = _get_emoji_str_from_event(event)
    if not emoji_str or emoji_str not in await bot.cache.guild_vote_emojis(
        event.guild_id
    ):
        return

    orig_msg = await get_orig_message(event.message_id)

    orig_chid = orig_msg.channel_id if orig_msg else event.channel_id
    up_configs, down_configs = await _get_configs_for_emoji(
        bot, emoji_str, event.guild_id, orig_chid
    )
    if not (up_configs or down_configs):
        return

    if orig_msg is None:
        _m = await bot.cache.gof_message(event.channel_id, event.message_id)
        if not _m:
            return
        channel_nsfw = await bot.cache.gof_guild_channel_nsfw(event.channel_id)
        assert channel_nsfw is not None

        orig_msg = await Message.get_or_create(
            event.guild_id,
            event.channel_id,
            event.message_id,
            channel_nsfw,
            _m.author.id,
            _m.author.is_bot,
        )

    # data for the person who reacted
    await Member.get_or_create(
        event.guild_id, event.member.id, event.member.is_bot
    )

    author = await User.fetch(user_id=orig_msg.author_id)
    author_obj = await bot.cache.gof_member(event.guild_id, author.user_id)
    valid_upvote_starboard_ids: set[int] = set()
    valid_downvote_starboard_ids: set[int] = set()
    remove_invalid: bool = True
    for sb_set, id_set in zip(
        (up_configs, down_configs),
        (valid_upvote_starboard_ids, valid_downvote_starboard_ids),
    ):
        for c in sb_set:
            if not c.remove_invalid:
                remove_invalid = False
            if not c.enabled:
                remove_invalid = False
                continue
            if await is_vote_valid_for(
                bot, c, orig_msg, author, author_obj, event.member
            ):
                id_set.add(c.starboard.id)

    if (
        not valid_upvote_starboard_ids
        and not valid_downvote_starboard_ids
        and remove_invalid
    ):
        actual_msg = await bot.cache.gof_message(
            event.channel_id, event.message_id
        )
        if actual_msg:
            with suppress(hikari.NotFoundError, hikari.ForbiddenError):
                if isinstance(event.emoji_name, hikari.UnicodeEmoji):
                    await actual_msg.remove_reaction(
                        event.emoji_name, user=event.member
                    )
                elif (
                    isinstance(event.emoji_name, str)
                    and event.emoji_id is not None
                ):
                    await actual_msg.remove_reaction(
                        event.emoji_name, event.emoji_id, user=event.member
                    )
        return

    # create a "star" for each starboard
    await add_votes(
        orig_msg.message_id,
        event.user_id,
        valid_upvote_starboard_ids,
        orig_msg.author_id,
        is_downvote=False,
    )
    await add_votes(
        orig_msg.message_id,
        event.user_id,
        valid_downvote_starboard_ids,
        orig_msg.author_id,
        is_downvote=True,
    )

    guild = await Guild.fetch(guild_id=event.guild_id)
    ip = guild.premium_end is not None

    await refresh_message(
        cast("Bot", event.app),
        orig_msg,
        valid_upvote_starboard_ids.union(valid_downvote_starboard_ids),
        premium=ip,
    )
    await refresh_xp(event.guild_id, orig_msg.author_id)

    if ip:
        asyncio.create_task(
            refresh_xpr(bot, event.guild_id, orig_msg.author_id)
        )
        asyncio.create_task(update_posroles(bot, event.guild_id))


async def handle_reaction_remove(
    event: hikari.GuildReactionDeleteEvent,
) -> None:
    bot = cast("Bot", event.app)

    emoji_str = _get_emoji_str_from_event(event)
    if not emoji_str or emoji_str not in await bot.cache.guild_vote_emojis(
        event.guild_id
    ):
        return

    orig_msg = await get_orig_message(event.message_id)
    if not orig_msg or orig_msg.frozen:
        return

    up_sb, down_sb = await _get_configs_for_emoji(
        bot, emoji_str, event.guild_id, orig_msg.channel_id
    )
    valid_sbids = [sb.starboard.id for sb in up_sb + down_sb]
    if not (up_sb or down_sb):
        return

    await remove_votes(orig_msg.message_id, event.user_id, valid_sbids)

    guild = await Guild.fetch(guild_id=event.guild_id)
    ip = guild.premium_end is not None

    await refresh_message(
        cast("Bot", event.app), orig_msg, valid_sbids, premium=ip
    )
    await refresh_xp(event.guild_id, orig_msg.author_id)

    if ip:
        await refresh_xpr(bot, event.guild_id, orig_msg.author_id)
        await update_posroles(bot, event.guild_id)


def _get_emoji_str_from_event(
    event: hikari.GuildReactionDeleteEvent | hikari.GuildReactionAddEvent,
) -> str | None:
    bot = cast("Bot", event.app)
    if event.emoji_id is not None:
        c = bot.cache.get_emoji(event.emoji_id)
        if not c:
            return None
        return str(c.id)
    else:
        assert isinstance(event.emoji_name, hikari.UnicodeEmoji)
        return str(event.emoji_name)


async def _get_configs_for_emoji(
    bot: Bot, emoji_str: str, guild_id: int, channel_id: int
) -> tuple[list[StarboardConfig], list[StarboardConfig]]:
    starboards = (
        await Starboard.fetch_query().where(guild_id=guild_id).fetchmany()
    )
    upvote_configs: list[StarboardConfig] = []
    downvote_configs: list[StarboardConfig] = []

    for sb in starboards:
        config = await get_config(bot, sb, channel_id)
        if not config.enabled:
            continue
        if emoji_str in config.upvote_emojis:
            upvote_configs.append(config)
        elif emoji_str in config.downvote_emojis:
            downvote_configs.append(config)

    return upvote_configs, downvote_configs
