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
from typing import TYPE_CHECKING, Iterable

import apgorm
import asyncpg
import hikari
from pycooldown import FlexibleCooldown

from starboard.config import CONFIG
from starboard.database import Message, User, Vote

from .config import StarboardConfig
from .permrole import get_permissions

if TYPE_CHECKING:
    from starboard.bot import Bot


COOLDOWN: FlexibleCooldown[tuple[int, int]] = FlexibleCooldown(
    CONFIG.max_cooldown_period
)


async def is_vote_valid_for(
    bot: Bot,
    config: StarboardConfig,
    orig_message: Message,
    author: User,
    author_obj: hikari.Member | None,
    voter: hikari.Member,
) -> bool:
    if (
        (not config.self_vote and voter.id == orig_message.author_id)
        or (author.is_bot and not config.allow_bots)
        or orig_message.trashed
        or orig_message.frozen
    ):
        return False

    # check cooldown
    if config.cooldown_enabled and COOLDOWN.update_ratelimit(
        (voter.id, config.starboard.channel_id),
        config.cooldown_period,
        config.cooldown_count,
    ):
        return False

    # check age filters
    now = datetime.datetime.now(datetime.timezone.utc)
    created_at = hikari.Snowflake(orig_message.message_id).created_at
    age = (now - created_at).total_seconds()

    if config.newer_than and age > config.newer_than:
        return False

    if config.older_than and age < config.older_than:
        return False

    # check permissions
    guild = bot.cache.get_guild(orig_message.guild_id)
    assert guild

    adder_perms = await get_permissions(
        guild, set(voter.role_ids), config.starboard.channel_id
    )
    if not adder_perms.vote:
        return False

    author_roles: set[int]
    if author_obj:
        author_roles = set(author_obj.role_ids)
    else:
        # the author left
        author_roles = {guild.id}
    author_perms = await get_permissions(
        guild, author_roles, config.starboard.channel_id
    )
    return author_perms.recv_votes


async def add_votes(
    orig_message_id: int,
    user_id: int,
    starboard_ids: Iterable[int],
    target_author_id: int,
    is_downvote: bool,
) -> None:
    for sbid in starboard_ids:
        try:
            await Vote(
                message_id=orig_message_id,
                user_id=user_id,
                starboard_id=sbid,
                target_author_id=target_author_id,
                is_downvote=is_downvote,
            ).create()
        except asyncpg.UniqueViolationError:
            await Vote.update_query().where(
                message_id=orig_message_id, user_id=user_id, starboard_id=sbid
            ).set(is_downvote=is_downvote).execute()


async def remove_votes(
    orig_message_id: int, user_id: int, starboard_ids: list[int]
) -> None:
    await Vote.delete_query().where(
        message_id=orig_message_id,
        user_id=user_id,
        starboard_id=apgorm.sql(starboard_ids).any,
    ).execute()
