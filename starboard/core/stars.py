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

import contextlib
from typing import TYPE_CHECKING

import apgorm
import asyncpg
import hikari
from pycooldown import FlexibleCooldown

from starboard.config import CONFIG
from starboard.database import Message, Star, User

from .config import StarboardConfig
from .permrole import get_permissions

if TYPE_CHECKING:
    from starboard.bot import Bot


COOLDOWN: FlexibleCooldown[tuple[int, int]] = FlexibleCooldown(
    CONFIG.max_cooldown_period
)


async def is_star_valid_for(
    bot: Bot,
    config: StarboardConfig,
    orig_message: Message,
    author: User,
    author_obj: hikari.Member | None,
    star_adder: hikari.Member,
) -> bool:
    if (not config.self_star) and star_adder.id == orig_message.author_id:
        return False

    if author.is_bot and not config.allow_bots:
        return False

    if orig_message.trashed:
        return False

    if orig_message.frozen:
        return False

    # check cooldown
    if config.cooldown_enabled and COOLDOWN.update_rate_limit(
        (star_adder.id, config.starboard.id),
        config.cooldown_period,
        config.cooldown_count,
    ):
        return False

    # check permissions
    guild = bot.cache.get_guild(orig_message.guild_id)
    assert guild

    adder_perms = await get_permissions(
        guild, set(star_adder.role_ids), config.starboard.id
    )
    if not adder_perms.give_stars:
        return False

    author_roles: set[int]
    if author_obj:
        author_roles = set(author_obj.role_ids)
    else:
        # the author left
        author_roles = {guild.id}
    author_perms = await get_permissions(
        guild, author_roles, config.starboard.id
    )
    if not author_perms.recv_stars:
        return False

    return True


async def add_stars(
    orig_message_id: int,
    user_id: int,
    starboard_ids: list[int],
    target_user_id: int,
) -> None:
    for sbid in starboard_ids:
        with contextlib.suppress(asyncpg.UniqueViolationError):
            await Star(
                message_id=orig_message_id,
                user_id=user_id,
                starboard_id=sbid,
                target_author_id=target_user_id,
            ).create()


async def remove_stars(
    orig_message_id: int, user_id: int, starboard_ids: list[int]
) -> None:
    await Star.delete_query().where(
        message_id=orig_message_id,
        user_id=user_id,
        starboard_id=apgorm.sql(starboard_ids).any,
    ).execute()
