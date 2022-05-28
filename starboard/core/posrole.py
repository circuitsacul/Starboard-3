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

from contextlib import suppress
from typing import TYPE_CHECKING

import hikari
from apgorm import sql
from pycooldown import FixedCooldown

from starboard.config import CONFIG
from starboard.database import PosRole, PosRoleMember

from .leaderboard import get_leaderboard

if TYPE_CHECKING:
    from starboard.bot import Bot


LOCK: set[int] = set()
COOLDOWN: FixedCooldown[int] = FixedCooldown(
    CONFIG.pr_cooldown_period, CONFIG.pr_cooldown_cap
)


async def update_posroles(bot: Bot, guild_id: int) -> bool:
    if guild_id in LOCK:
        return False

    if COOLDOWN.update_rate_limit(guild_id):
        return False

    LOCK.add(guild_id)
    try:
        await _update_posroles(bot, guild_id)
    finally:
        LOCK.remove(guild_id)

    return True


async def _update_posroles(bot: Bot, guild_id: int) -> None:
    ret = await _get_updates(guild_id)
    if not ret:
        return
    add, remove = ret

    for roleid, users in add.items():
        for uid in users:
            with suppress(hikari.NotFoundError, hikari.ForbiddenError):
                await bot.rest.add_role_to_member(
                    guild_id, uid, roleid, reason="Position-based Role Awards"
                )
            await PosRoleMember(user_id=uid, role_id=roleid).create()

    for roleid, users in remove.items():
        await PosRoleMember.delete_query().where(role_id=roleid).where(
            PosRoleMember.user_id.eq(sql(users).any)
        ).execute()
        for uid in users:
            with suppress(hikari.NotFoundError, hikari.ForbiddenError):
                await bot.rest.remove_role_from_member(
                    guild_id, uid, roleid, reason="Position-based Role Awards"
                )


async def _get_updates(
    guild_id: int,
) -> tuple[dict[int, set[int]], dict[int, set[int]]] | None:
    posroles = (
        await PosRole.fetch_query()
        .where(guild_id=guild_id)
        .order_by(PosRole.max_members)
        .fetchmany()
    )
    if not posroles:
        return None

    # get the description of what the posrole setup should look like
    leaderboard = list(
        (
            await get_leaderboard(
                guild_id, sum(r.max_members for r in posroles)
            )
        ).keys()
    )
    wanted: dict[int, set[int]] = {}
    for p in posroles:
        uids = leaderboard[0 : p.max_members]
        leaderboard = leaderboard[p.max_members :]
        wanted[p.id] = set(uids)

    # get the description of what the posrole setup actually looks like, and
    # generate updates from it
    removals: dict[int, set[int]] = {}
    adds: dict[int, set[int]] = {}

    for p in posroles:
        curr = {
            m.user_id
            for m in await PosRoleMember.fetch_query()
            .where(role_id=p.id)
            .fetchmany()
        }
        adds[p.id] = wanted[p.id].difference(curr)
        removals[p.id] = curr.difference(wanted[p.id])

    return adds, removals
