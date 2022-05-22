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
from typing import TYPE_CHECKING, cast

import apgorm
import hikari
from pycooldown import FixedCooldown

from starboard.config import CONFIG
from starboard.core.leaderboard import refresh_xp
from starboard.core.posrole import update_posroles
from starboard.core.xprole import refresh_xpr
from starboard.database import Guild, Starboard, goc_member, goc_message
from starboard.database.models.user import User

from .config import get_config
from .messages import get_orig_message
from .starboards import refresh_message
from .stars import add_stars, is_star_valid_for, remove_stars

if TYPE_CHECKING:
    from starboard.bot import Bot


COOLDOWN: FixedCooldown[int] = FixedCooldown(
    CONFIG.guild_star_cooldown_period, CONFIG.guild_star_cooldown_cap
)


async def handle_reaction_add(event: hikari.GuildReactionAddEvent) -> None:
    if event.member.is_bot:
        return
    bot = cast("Bot", event.app)

    emoji_str = _get_emoji_str_from_event(event)
    if not emoji_str:
        return
    if emoji_str not in await bot.cache.guild_star_emojis(event.guild_id):
        return

    if COOLDOWN.update_rate_limit(event.guild_id):
        return

    starboards = await _get_starboards_for_emoji(emoji_str, event.guild_id)
    if len(starboards) == 0:
        return

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

    # data for the person who reacted
    await goc_member(event.guild_id, event.member.id, event.member.is_bot)

    author = await User.fetch(id=orig_msg.author_id)
    author_obj = await bot.cache.gof_member(event.guild_id, author.id)
    valid_starboard_ids: list[int] = []
    remove_invalid: bool = True
    for s in starboards:
        c = await get_config(s, orig_msg.channel_id)
        if not c.remove_invalid:
            remove_invalid = False
        if not c.enabled:
            remove_invalid = False
            continue
        if await is_star_valid_for(
            bot, c, orig_msg, author, author_obj, event.member
        ):
            valid_starboard_ids.append(s.id)

    if len(valid_starboard_ids) == 0 and remove_invalid:
        actual_msg = await bot.cache.gof_message(
            event.channel_id, event.message_id
        )
        if actual_msg:
            try:
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
            except (hikari.NotFoundError, hikari.ForbiddenError):
                pass
        return

    # create a "star" for each starboard
    await add_stars(orig_msg.id, event.user_id, valid_starboard_ids)

    guild = await Guild.fetch(id=event.guild_id)
    ip = guild.premium_end is not None

    await refresh_message(
        cast("Bot", event.app), orig_msg, valid_starboard_ids, premium=ip
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
    if not emoji_str:
        return
    if emoji_str not in await bot.cache.guild_star_emojis(event.guild_id):
        return

    orig_msg = await get_orig_message(event.message_id)
    if not orig_msg:
        return
    if orig_msg.frozen:
        return

    starboards = await _get_starboards_for_emoji(emoji_str, event.guild_id)

    valid_sbids: list[int] = []
    for s in starboards:
        c = await get_config(s, orig_msg.channel_id)
        if not c.enabled:
            continue
        valid_sbids.append(s.id)

    if not valid_sbids:
        return

    await remove_stars(orig_msg.id, event.user_id, valid_sbids)

    guild = await Guild.fetch(id=event.guild_id)
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


async def _get_starboards_for_emoji(
    emoji_str: str, guild_id: int
) -> apgorm.LazyList[dict, Starboard]:
    return (
        await Starboard.fetch_query()
        .where(guild_id=guild_id)
        .where(
            apgorm.sql(
                Starboard.star_emojis,
                apgorm.raw("&& array["),
                emoji_str,
                apgorm.raw("]"),
            )
        )
        .fetchmany()
    )
